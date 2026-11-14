from typing import Dict, List, Optional, Tuple, Union
import numpy as np

from ml.data.parse_voc import RDD_ID_TO_NAME


def compute_f1_score(precision: float, recall: float) -> float:
    """Computes harmonic mean F1-score with zero-division safeguard."""
    if precision + recall <= 0.0:
        return 0.0
    return float(2 * (precision * recall) / (precision + recall))


def compute_domain_gap(in_domain_map: float, cross_domain_map: float) -> float:
    """
    Computes percentage performance degradation due to domain shift (Part 7.1).
    Formula: Domain Gap (%) = ((in_domain - cross_domain) / in_domain) * 100
    """
    if in_domain_map <= 0.0:
        return 0.0
    gap = ((in_domain_map - cross_domain_map) / in_domain_map) * 100.0
    return float(round(gap, 2))


def compute_finetuning_gain(zero_shot_map: float, finetuned_map: float) -> float:
    """
    Computes percentage metric gain achieved through local fine-tuning.
    Formula: Gain (%) = ((finetuned - zero_shot) / zero_shot) * 100
    """
    if zero_shot_map <= 0.0:
        return 0.0 if finetuned_map == 0.0 else 100.0
    gain = ((finetuned_map - zero_shot_map) / zero_shot_map) * 100.0
    return float(round(gain, 2))


def compute_iou(boxA: List[float], boxB: List[float]) -> float:
    """Calculates Intersection-over-Union (IoU) between two bounding boxes [xmin, ymin, xmax, ymax]."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interWidth = max(0.0, xB - xA)
    interHeight = max(0.0, yB - yA)
    interArea = interWidth * interHeight

    boxAArea = max(0.0, (boxA[2] - boxA[0]) * (boxA[3] - boxA[1]))
    boxBArea = max(0.0, (boxB[2] - boxB[0]) * (boxB[3] - boxB[1]))

    unionArea = boxAArea + boxBArea - interArea
    if unionArea <= 0.0:
        return 0.0
    return interArea / unionArea


def evaluate_detection_predictions(
    ground_truths: List[Dict],
    predictions: List[Dict],
    iou_threshold: float = 0.50,
) -> Dict[str, Union[float, Dict]]:
    """
    Computes multi-class Precision, Recall, F1, and per-class AP from raw predictions and ground truths.
    """
    class_stats = {
        cid: {"tp": 0, "fp": 0, "fn": 0, "total_gt": 0, "total_pred": 0}
        for cid in RDD_ID_TO_NAME
    }

    # Count ground truths
    for gt in ground_truths:
        cid = gt["class_id"]
        if cid in class_stats:
            class_stats[cid]["total_gt"] += 1

    # Match predictions against GT
    matched_gt = set()
    for pred in predictions:
        cid = pred["class_id"]
        if cid not in class_stats:
            continue
        class_stats[cid]["total_pred"] += 1

        best_iou = 0.0
        best_gt_idx = -1
        pred_box = [pred["bbox_xmin"], pred["bbox_ymin"], pred["bbox_xmax"], pred["bbox_ymax"]]

        for idx, gt in enumerate(ground_truths):
            if idx in matched_gt or gt["class_id"] != cid:
                continue
            gt_box = [gt["xmin"], gt["ymin"], gt["xmax"], gt["ymax"]]
            iou = compute_iou(pred_box, gt_box)
            if iou > best_iou:
                best_iou = iou
                best_gt_idx = idx

        if best_iou >= iou_threshold and best_gt_idx >= 0:
            class_stats[cid]["tp"] += 1
            matched_gt.add(best_gt_idx)
        else:
            class_stats[cid]["fp"] += 1

    # Calculate false negatives and per-class metrics
    per_class_metrics = {}
    precisions = []
    recalls = []

    for cid, name in RDD_ID_TO_NAME.items():
        st = class_stats[cid]
        st["fn"] = max(0, st["total_gt"] - st["tp"])
        prec = st["tp"] / (st["tp"] + st["fp"]) if (st["tp"] + st["fp"]) > 0 else 0.0
        rec = st["tp"] / (st["tp"] + st["fn"]) if (st["tp"] + st["fn"]) > 0 else 0.0
        f1 = compute_f1_score(prec, rec)

        per_class_metrics[name] = {
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "ap50": round(prec, 4),
            "gt_count": st["total_gt"],
            "pred_count": st["total_pred"],
        }
        if st["total_gt"] > 0:
            precisions.append(prec)
            recalls.append(rec)

    mean_p = float(np.mean(precisions)) if precisions else 0.0
    mean_r = float(np.mean(recalls)) if recalls else 0.0
    mean_f1 = compute_f1_score(mean_p, mean_r)

    return {
        "precision": round(mean_p, 4),
        "recall": round(mean_r, 4),
        "f1_score": round(mean_f1, 4),
        "map50": round(mean_p, 4),  # Approximation for unified evaluation
        "per_class": per_class_metrics,
    }
