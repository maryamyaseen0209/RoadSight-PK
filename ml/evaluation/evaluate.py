import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from backend.app.core.logging_config import logger
from ml.data.parse_voc import parse_voc_xml
from ml.evaluation.metrics import evaluate_detection_predictions


def evaluate_model_on_dataset(
    model_type: str,
    weights_path: Union[str, Path],
    images_dir: Union[str, Path],
    annotations_dir: Union[str, Path],
    output_metrics_file: Optional[Union[str, Path]] = None,
    conf_threshold: float = 0.25,
    iou_threshold: float = 0.50,
) -> Dict[str, Any]:
    """
    Evaluates detector performance against ground-truth Pascal VOC annotations,
    exporting structured evaluation metrics to experiments/metrics/.
    """
    images_dir = Path(images_dir)
    annotations_dir = Path(annotations_dir)
    weights_path = Path(weights_path)

    image_files = sorted(
        list(images_dir.glob("*.jpg")) +
        list(images_dir.glob("*.png")) +
        list(images_dir.glob("*.jpeg"))
    )

    all_gts: List[Dict] = []
    all_preds: List[Dict] = []

    # If YOLO and ultralytics installed, can load model
    detector = None
    if model_type.lower() == "yolo":
        try:
            from ml.models.yolo_detector import YOLODetectorWrapper
            detector = YOLODetectorWrapper(weights_path=weights_path)
        except Exception as e:
            logger.warning(f"Could not load YOLO detector: {e}")

    for img_path in image_files:
        xml_path = annotations_dir / f"{img_path.stem}.xml"
        if xml_path.exists():
            parsed = parse_voc_xml(xml_path)
            for b in parsed["boxes"]:
                all_gts.append(b)

        if detector and detector.model is not None:
            preds = detector.predict(img_path, conf=conf_threshold, iou=iou_threshold)
            all_preds.extend(preds)

    metrics = evaluate_detection_predictions(
        ground_truths=all_gts,
        predictions=all_preds,
        iou_threshold=iou_threshold,
    )

    result_summary = {
        "model_type": model_type,
        "weights_path": str(weights_path),
        "total_test_images": len(image_files),
        "total_ground_truth_boxes": len(all_gts),
        "total_predictions": len(all_preds),
        "metrics": metrics,
    }

    if output_metrics_file:
        out_f = Path(output_metrics_file)
        out_f.parent.mkdir(parents=True, exist_ok=True)
        with open(out_f, "w", encoding="utf-8") as f:
            json.dump(result_summary, f, indent=2)
        logger.info(f"Evaluation metrics written to: {out_f}")

    return result_summary
