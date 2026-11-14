from datetime import datetime, timezone
import json
from pathlib import Path
import time
import uuid
from typing import Optional, List

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.core.config import settings
from backend.app.core.logging_config import logger
from backend.app.db.session import get_db
from backend.app.models.detection import DetectionRun, Detection, ModelExperiment
from backend.app.schemas.detection import (
    PredictResponse,
    DetectionItem,
    DetectionRunSummary,
    OverallSummaryResponse,
    ModelInfoResponse,
)

router = APIRouter()

OFFICIAL_CLASSES = {
    0: "Longitudinal Crack [D00]",
    1: "Transverse Crack [D10]",
    2: "Alligator Crack [D20]",
    3: "Pothole [D40]",
}


@router.get("/health", tags=["System"])
def get_health():
    """Health check endpoint to verify backend operational readiness."""
    return {
        "status": "ok",
        "app": settings.PROJECT_NAME,
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/model", response_model=ModelInfoResponse, tags=["Model"])
def get_model_info():
    """Returns metadata about the active defect detection model and weights status."""
    weights_path = Path(settings.BASE_DIR) / settings.MODEL_WEIGHTS_PATH
    weights_exist = weights_path.exists()

    return ModelInfoResponse(
        model_name="YOLO26n / Fallback YOLO11n",
        weights_path=str(settings.MODEL_WEIGHTS_PATH),
        weights_present=weights_exist,
        classes=OFFICIAL_CLASSES,
        confidence_threshold=settings.CONFIDENCE_THRESHOLD,
        iou_threshold=settings.IOU_THRESHOLD,
        status="ready" if weights_exist else "uninitialized (Phase 1 mode)",
    )


@router.post("/predict", response_model=PredictResponse, tags=["Inference"])
async def predict_road_defects(
    file: UploadFile = File(...),
    confidence: Optional[float] = Query(0.25, ge=0.05, le=0.95),
    iou: Optional[float] = Query(0.45, ge=0.1, le=0.9),
    db: Session = Depends(get_db),
):
    """
    Analyzes an uploaded road pavement image for structural defects.
    In Phase 1, safely handles incoming images and persists detection run metadata.
    """
    start_time = time.time()

    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type '{file.content_type}'. Please upload an image (JPG, PNG).",
        )

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    # Save original image to outputs directory
    run_id = str(uuid.uuid4())
    safe_filename = f"{run_id}_{file.filename}"
    out_dir = settings.outputs_path
    image_disk_path = out_dir / safe_filename
    with open(image_disk_path, "wb") as f:
        f.write(file_bytes)

    # Check if trained weights exist to execute actual inference
    weights_path = Path(settings.BASE_DIR) / settings.MODEL_WEIGHTS_PATH
    detections_list: List[DetectionItem] = []

    if weights_path.exists():
        try:
            from ml.inference.predict import run_single_inference  # type: ignore
            raw_detections, annotated_rel_path = run_single_inference(
                image_path=str(image_disk_path),
                weights_path=str(weights_path),
                confidence=confidence or settings.CONFIDENCE_THRESHOLD,
                iou=iou or settings.IOU_THRESHOLD,
                output_dir=str(out_dir),
            )
            for d in raw_detections:
                detections_list.append(DetectionItem(**d))
            output_image_path = annotated_rel_path
        except Exception as exc:
            logger.warning(f"Inference module execution skipped or failed: {exc}")
            output_image_path = f"/outputs/{safe_filename}"
    else:
        # Safe initial Phase 1 fallback: Weights not yet generated
        output_image_path = f"/outputs/{safe_filename}"

    elapsed_ms = round((time.time() - start_time) * 1000, 2)

    # Persist in SQLite
    run_record = DetectionRun(
        id=run_id,
        image_name=file.filename or "unknown.jpg",
        image_path=f"/outputs/{safe_filename}",
        output_image_path=output_image_path,
        total_detections=len(detections_list),
        inference_time_ms=elapsed_ms,
        model_name="YOLO26n" if weights_path.exists() else "RoadSight-Base",
    )
    db.add(run_record)

    for item in detections_list:
        det_record = Detection(
            run_id=run_id,
            class_id=item.class_id,
            class_name=item.class_name,
            confidence=item.confidence,
            bbox_xmin=item.bbox_xmin,
            bbox_ymin=item.bbox_ymin,
            bbox_xmax=item.bbox_xmax,
            bbox_ymax=item.bbox_ymax,
        )
        db.add(det_record)

    db.commit()
    db.refresh(run_record)

    return PredictResponse(
        run_id=run_record.id,
        image_name=run_record.image_name,
        image_url=run_record.image_path,
        output_image_url=run_record.output_image_path,
        total_detections=run_record.total_detections,
        inference_time_ms=run_record.inference_time_ms,
        model_name=run_record.model_name,
        created_at=run_record.created_at,
        detections=detections_list,
    )


@router.get("/history", response_model=List[DetectionRunSummary], tags=["History"])
def get_detection_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Retrieves chronological history of defect detection runs."""
    runs = (
        db.query(DetectionRun)
        .order_by(DetectionRun.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        DetectionRunSummary(
            id=r.id,
            image_name=r.image_name,
            image_url=r.image_path,
            output_image_url=r.output_image_path,
            total_detections=r.total_detections,
            inference_time_ms=r.inference_time_ms,
            model_name=r.model_name,
            created_at=r.created_at,
        )
        for r in runs
    ]


@router.get("/summary", response_model=OverallSummaryResponse, tags=["Analytics"])
def get_overall_summary(db: Session = Depends(get_db)):
    """Computes overall aggregate metrics for dashboard analytics."""
    total_runs = db.query(DetectionRun).count()
    total_detections = db.query(Detection).count()

    avg_latency = (
        db.query(func.avg(DetectionRun.inference_time_ms)).scalar() or 0.0
    )

    # Defect counts by class
    defect_counts = {name: 0 for name in OFFICIAL_CLASSES.values()}
    class_group = (
        db.query(Detection.class_name, func.count(Detection.id))
        .group_by(Detection.class_name)
        .all()
    )
    for class_name, count in class_group:
        defect_counts[class_name] = count

    # Model distribution
    model_dist = {}
    model_group = (
        db.query(DetectionRun.model_name, func.count(DetectionRun.id))
        .group_by(DetectionRun.model_name)
        .all()
    )
    for model_name, count in model_group:
        model_dist[model_name] = count

    return OverallSummaryResponse(
        total_runs=total_runs,
        total_detections=total_detections,
        average_inference_time_ms=round(float(avg_latency), 2),
        defect_counts_by_class=defect_counts,
        model_distribution=model_dist,
    )


@router.get("/metrics", tags=["Evaluation"])
def get_model_metrics():
    """
    Returns empirical evaluation metrics across trained models.
    Strictly returns status: unavailable when metric files do not exist yet.
    """
    metrics_file = settings.metrics_path / "model_evaluation_summary.json"

    if not metrics_file.exists():
        return {
            "status": "unavailable",
            "message": "Evaluation metrics are not yet available. Please execute training & evaluation phases first.",
            "metrics": None,
        }

    try:
        with open(metrics_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "status": "available",
            "metrics": data,
        }
    except Exception as e:
        logger.error(f"Error reading metrics file: {e}")
        return {
            "status": "error",
            "message": f"Failed to parse metrics file: {str(e)}",
            "metrics": None,
        }
