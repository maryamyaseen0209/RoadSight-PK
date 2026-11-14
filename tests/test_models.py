from pathlib import Path
import pytest

from ml.evaluation.metrics import (
    compute_f1_score,
    compute_domain_gap,
    compute_finetuning_gain,
    compute_iou,
    evaluate_detection_predictions,
)
from ml.evaluation.benchmark_speed import benchmark_model_speed
from ml.evaluation.error_analysis import categorize_detections
from ml.models.yolo_detector import YOLODetectorWrapper

FIXTURES_DIR = Path(__file__).parent / "fixtures"
IMAGES_DIR = FIXTURES_DIR / "images"


def test_metrics_formulas():
    # F1 score
    f1 = compute_f1_score(0.8, 0.8)
    assert round(f1, 4) == 0.8000
    assert compute_f1_score(0.0, 0.0) == 0.0

    # Domain gap: ((0.60 - 0.45) / 0.60) * 100 = 25.0%
    gap = compute_domain_gap(in_domain_map=0.60, cross_domain_map=0.45)
    assert gap == 25.0

    # Fine-tuning gain: ((0.60 - 0.30) / 0.30) * 100 = 100.0%
    gain = compute_finetuning_gain(zero_shot_map=0.30, finetuned_map=0.60)
    assert gain == 100.0

    # IoU
    boxA = [0, 0, 10, 10]
    boxB = [0, 0, 10, 10]
    assert compute_iou(boxA, boxB) == 1.0

    boxC = [10, 10, 20, 20]
    assert compute_iou(boxA, boxC) == 0.0


def test_evaluate_detection_predictions():
    ground_truths = [
        {"class_id": 0, "xmin": 10, "ymin": 10, "xmax": 50, "ymax": 50},
        {"class_id": 3, "xmin": 100, "ymin": 100, "xmax": 150, "ymax": 150},
    ]

    # Perfect prediction for class 0, imperfect for class 3
    predictions = [
        {"class_id": 0, "bbox_xmin": 12, "bbox_ymin": 10, "bbox_xmax": 52, "ymax": 50, "bbox_ymax": 50},
    ]

    results = evaluate_detection_predictions(ground_truths, predictions, iou_threshold=0.50)
    assert "precision" in results
    assert "recall" in results
    assert "per_class" in results
    assert "Longitudinal Crack [D00]" in results["per_class"]


def test_categorize_detections():
    gts = [{"class_id": 0, "xmin": 10, "ymin": 10, "xmax": 50, "ymax": 50}]
    preds = [
        {"class_id": 0, "bbox_xmin": 10, "bbox_ymin": 10, "bbox_xmax": 50, "bbox_ymax": 50},  # TP
        {"class_id": 1, "bbox_xmin": 70, "bbox_ymin": 70, "bbox_xmax": 90, "bbox_ymax": 90},    # FP
    ]

    categorized = categorize_detections(gts, preds, iou_threshold=0.5)
    assert len(categorized["true_positives"]) == 1
    assert len(categorized["false_positives"]) == 1
    assert len(categorized["false_negatives"]) == 0


def test_yolo_wrapper_fallback():
    detector = YOLODetectorWrapper(preferred_model="yolo26n.pt")
    # In environment without ultralytics, wrapper safely returns empty detections rather than crashing
    preds = detector.predict(IMAGES_DIR / "img_01.jpg")
    assert isinstance(preds, list)


def test_speed_benchmark():
    metrics = benchmark_model_speed(model_type="yolo", num_warmup=2, num_runs=5)
    assert "mean_latency_ms" in metrics
    assert "fps" in metrics
    assert metrics["fps"] > 0
