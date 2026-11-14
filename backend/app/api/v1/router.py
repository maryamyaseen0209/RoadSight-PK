from datetime import datetime, timezone
import io
import json
from pathlib import Path
import uuid
from typing import Any, Dict, List, Optional
from PIL import Image

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.logging_config import logger
from backend.app.db.session import get_db
from backend.app.models.detection import DetectionRun, Detection, ModelExperiment
from backend.app.schemas.detection import (
    PredictResponse,
    DetectionItem,
    DetectionRunDetail,
    DetectionRunSummary,
    OverallSummaryResponse,
    ModelInfoResponse,
)
from backend.app.services.model_loader import (
    registry,
    run_detection_pipeline,
    OFFICIAL_CLASS_MAPPING,
)

router = APIRouter()

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}


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
    weights_path = registry.yolo_weights_path or settings.MODEL_WEIGHTS_PATH
    weights_exist = Path(weights_path).exists() if weights_path else False

    return ModelInfoResponse(
        model_name=registry.yolo_model_name,
        weights_path=str(weights_path),
        weights_present=weights_exist,
        classes={
            0: "Longitudinal Crack [D00]",
            1: "Transverse Crack [D10]",
            2: "Alligator Crack [D20]",
            3: "Pothole [D40]",
        },
        confidence_threshold=settings.CONFIDENCE_THRESHOLD,
        iou_threshold=settings.IOU_THRESHOLD,
        status="ready" if registry.is_ready else "initialized",
    )


@router.post("/predict", response_model=PredictResponse, tags=["Inference"])
async def predict_road_defects(
    file: UploadFile = File(...),
    confidence_threshold: Optional[float] = Query(0.25, ge=0.05, le=0.95),
    model_name: Optional[str] = Query("YOLO", description="Detector architecture: 'YOLO' or 'Faster R-CNN'"),
    db: Session = Depends(get_db),
):
    """
    Analyzes an uploaded road pavement image for structural distress.
    Enforces strict size validation, format validation, and image content integrity.
    Saves original and annotated images, records run in SQLite, and returns detections.
    """
    # 1. Validate file extension
    filename = file.filename or "unknown.jpg"
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file extension '{ext}'. Only JPEG, PNG, and WebP images are supported.",
        )

    # 2. Read file bytes and validate size (max 10 MB)
    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty. Please select a valid pavement image.",
        )

    if len(file_bytes) > settings.MAX_UPLOAD_SIZE_BYTES:
        max_mb = settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds the {max_mb} MB limit. Please upload a smaller image.",
        )

    # 3. Verify actual image content with PIL
    try:
        with Image.open(io.BytesIO(file_bytes)) as test_img:
            test_img.verify()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is corrupt or not a valid image format.",
        )

    # 4. Generate unique run ID
    run_id = str(uuid.uuid4())
    conf_thresh = confidence_threshold or settings.CONFIDENCE_THRESHOLD

    # 5. Run inference and render bounding-box overlays
    try:
        detections_data, inference_time_ms, orig_url, annotated_url = run_detection_pipeline(
            image_bytes=file_bytes,
            run_id=run_id,
            original_filename=filename,
            confidence_threshold=conf_thresh,
            model_choice=model_name or "YOLO",
        )
    except Exception as e:
        logger.error(f"Inference pipeline execution error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the road pavement image.",
        )

    # 6. Persist execution metadata to SQLite
    run_record = DetectionRun(
        id=run_id,
        image_name=filename,
        image_path=orig_url,
        output_image_path=annotated_url,
        total_detections=len(detections_data),
        inference_time_ms=inference_time_ms,
        model_name=registry.yolo_model_name if (model_name or "").upper().startswith("YOLO") else model_name,
        confidence_threshold=conf_thresh,
    )
    db.add(run_record)

    detection_items: List[DetectionItem] = []
    for d in detections_data:
        det_record = Detection(
            run_id=run_id,
            class_id=d["class_id"],
            class_name=d["class_name"],
            confidence=d["confidence"],
            bbox_xmin=d["bbox_xmin"],
            bbox_ymin=d["bbox_ymin"],
            bbox_xmax=d["bbox_xmax"],
            bbox_ymax=d["bbox_ymax"],
        )
        db.add(det_record)
        detection_items.append(DetectionItem(**d))

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
        confidence_threshold=run_record.confidence_threshold or conf_thresh,
        created_at=run_record.created_at,
        detections=detection_items,
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
            output_image_url=r.output_image_path or r.image_path,
            total_detections=r.total_detections,
            inference_time_ms=r.inference_time_ms,
            model_name=r.model_name,
            confidence_threshold=r.confidence_threshold or 0.25,
            created_at=r.created_at,
        )
        for r in runs
    ]


@router.get("/history/{run_id}", response_model=DetectionRunDetail, tags=["History"])
def get_detection_run_detail(run_id: str, db: Session = Depends(get_db)):
    """Retrieves full detail and detected bounding boxes for a specific detection run."""
    run = db.query(DetectionRun).filter(DetectionRun.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Detection run '{run_id}' not found.",
        )

    detections = (
        db.query(Detection)
        .filter(Detection.run_id == run_id)
        .order_by(Detection.confidence.desc())
        .all()
    )

    items = [
        DetectionItem(
            id=d.id,
            class_id=d.class_id,
            class_name=d.class_name,
            confidence=d.confidence,
            bbox_xmin=d.bbox_xmin,
            bbox_ymin=d.bbox_ymin,
            bbox_xmax=d.bbox_xmax,
            bbox_ymax=d.bbox_ymax,
            x1=d.bbox_xmin,
            y1=d.bbox_ymin,
            x2=d.bbox_xmax,
            y2=d.bbox_ymax,
        )
        for d in detections
    ]

    return DetectionRunDetail(
        id=run.id,
        run_id=run.id,
        image_name=run.image_name,
        image_url=run.image_path,
        output_image_url=run.output_image_path or run.image_path,
        total_detections=run.total_detections,
        inference_time_ms=run.inference_time_ms,
        model_name=run.model_name,
        confidence_threshold=run.confidence_threshold or 0.25,
        created_at=run.created_at,
        detections=items,
    )


@router.delete("/history/{run_id}", tags=["History"])
def delete_detection_run(run_id: str, db: Session = Depends(get_db)):
    """
    Deletes a detection run, its associated detections, and disk artifacts.
    """
    run = db.query(DetectionRun).filter(DetectionRun.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Detection run '{run_id}' not found.",
        )

    # Delete files on disk if they exist
    out_dir = settings.outputs_path
    for filename in [f"{run_id}.jpg", f"{run_id}_original.jpg"]:
        file_path = out_dir / filename
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete disk artifact {file_path}: {e}")

    # Delete record from database (cascade deletes detections)
    db.delete(run)
    db.commit()

    return {
        "status": "deleted",
        "run_id": run_id,
        "message": "Detection run and artifacts deleted successfully.",
    }


@router.get("/summary", response_model=OverallSummaryResponse, tags=["Analytics"])
def get_overall_summary(db: Session = Depends(get_db)):
    """Computes overall aggregate metrics for dashboard analytics."""
    total_runs = db.query(DetectionRun).count()
    total_detections = db.query(Detection).count()

    avg_latency = (
        db.query(func.avg(DetectionRun.inference_time_ms)).scalar() or 0.0
    )

    # Defect counts by category
    category_counts = {
        "Longitudinal Crack": 0,
        "Transverse Crack": 0,
        "Alligator Crack": 0,
        "Pothole": 0,
    }
    class_group = (
        db.query(Detection.class_name, func.count(Detection.id))
        .group_by(Detection.class_name)
        .all()
    )
    for class_name, count in class_group:
        # Normalize class name
        clean_name = class_name.split("[")[0].strip()
        if clean_name in category_counts:
            category_counts[clean_name] += count
        else:
            category_counts[class_name] = count

    # Model distribution
    model_dist = {}
    model_group = (
        db.query(DetectionRun.model_name, func.count(DetectionRun.id))
        .group_by(DetectionRun.model_name)
        .all()
    )
    for model_name, count in model_group:
        model_dist[model_name] = count

    # Recent runs (top 5)
    recent_records = (
        db.query(DetectionRun)
        .order_by(DetectionRun.created_at.desc())
        .limit(5)
        .all()
    )
    recent_summaries = [
        DetectionRunSummary(
            id=r.id,
            image_name=r.image_name,
            image_url=r.image_path,
            output_image_url=r.output_image_path or r.image_path,
            total_detections=r.total_detections,
            inference_time_ms=r.inference_time_ms,
            model_name=r.model_name,
            confidence_threshold=r.confidence_threshold or 0.25,
            created_at=r.created_at,
        )
        for r in recent_records
    ]

    active_model_info = {
        "name": registry.yolo_model_name,
        "weights_path": registry.yolo_weights_path,
        "is_ready": registry.is_ready,
        "faster_rcnn_available": bool(registry.faster_rcnn_weights_path),
    }

    return OverallSummaryResponse(
        total_images_analyzed=total_runs,
        total_damage_detections=total_detections,
        average_inference_time_ms=round(float(avg_latency), 2),
        defect_counts_by_class=category_counts,
        model_distribution=model_dist,
        recent_runs=recent_summaries,
        active_model=active_model_info,
    )


@router.get("/metrics", tags=["Evaluation"])
def get_model_metrics(db: Session = Depends(get_db)):
    """
    Returns empirical experimental results from experiments/metrics/ and SQLite model_experiments table.
    Explicitly marks any experiment with status 'unavailable' if not yet executed.
    """
    metrics_dir = settings.metrics_path

    # Check for master summary
    master_json = metrics_dir / "master_metrics_summary.json"
    audit_json = metrics_dir / "dataset_audit.json"
    exp1_yolo_json = metrics_dir / "exp1_international_baseline_yolo.json"
    exp1_frcnn_json = metrics_dir / "exp1_international_baseline_faster_rcnn.json"
    exp2_loco_json = metrics_dir / "exp2_cross_country.json"
    exp3_zeroshot_json = metrics_dir / "exp3_pakistani_zeroshot.json"
    exp4_transfer_json = metrics_dir / "exp4_transfer_learning.json"
    exp5_efficiency_json = metrics_dir / "exp5_efficiency_comparison.json"

    def load_json_safe(path: Path) -> Optional[Dict]:
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    master_data = load_json_safe(master_json)
    audit_data = load_json_safe(audit_json)
    exp1_yolo = load_json_safe(exp1_yolo_json)
    exp1_frcnn = load_json_safe(exp1_frcnn_json)
    exp2_loco = load_json_safe(exp2_loco_json)
    exp3_zeroshot = load_json_safe(exp3_zeroshot_json)
    exp4_transfer = load_json_safe(exp4_transfer_json)
    exp5_efficiency = load_json_safe(exp5_efficiency_json)

    # Fetch recorded experiments from SQLite
    db_experiments = db.query(ModelExperiment).all()
    experiments_list = [
        {
            "id": exp.id,
            "experiment_name": exp.experiment_name,
            "model_type": exp.model_type,
            "dataset_split": exp.dataset_split,
            "map50": exp.map50,
            "latency_ms": exp.latency_ms,
            "fps": exp.fps,
            "created_at": exp.created_at.isoformat(),
        }
        for exp in db_experiments
    ]

    has_metrics = bool(master_data or len(experiments_list) > 0)

    return {
        "status": "available" if has_metrics else "unavailable",
        "dataset_audit": audit_data if audit_data else {"status": "unavailable"},
        "master_summary": master_data if master_data else {"status": "unavailable"},
        "exp1_baseline": {
            "yolo": exp1_yolo if exp1_yolo else {"status": "unavailable"},
            "faster_rcnn": exp1_frcnn if exp1_frcnn else {"status": "unavailable"},
        },
        "exp2_cross_country": exp2_loco if exp2_loco else {"status": "unavailable"},
        "exp3_zeroshot": exp3_zeroshot if exp3_zeroshot else {"status": "unavailable"},
        "exp4_transfer_learning": exp4_transfer if exp4_transfer else {"status": "unavailable"},
        "exp5_efficiency": exp5_efficiency if exp5_efficiency else {"status": "unavailable"},
        "recorded_experiments": experiments_list,
    }
