from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from PIL import Image, ImageDraw

from ml.data.parse_voc import parse_voc_xml, RDD_ID_TO_NAME
from ml.evaluation.metrics import compute_iou


def categorize_detections(
    ground_truth_boxes: List[Dict],
    predicted_boxes: List[Dict],
    iou_threshold: float = 0.50,
) -> Dict[str, List[Dict]]:
    """
    Categorizes detection outcomes into:
    - true_positives: Predicted box matching ground truth with IoU >= threshold.
    - false_positives: Predicted box with no matching ground truth.
    - false_negatives: Ground truth box that was missed by predictions.
    """
    matched_gt = set()
    true_positives = []
    false_positives = []

    for pred in predicted_boxes:
        p_box = [pred["bbox_xmin"], pred["bbox_ymin"], pred["bbox_xmax"], pred["bbox_ymax"]]
        best_iou = 0.0
        best_gt_idx = -1

        for idx, gt in enumerate(ground_truth_boxes):
            if idx in matched_gt or gt["class_id"] != pred["class_id"]:
                continue
            gt_box = [gt["xmin"], gt["ymin"], gt["xmax"], gt["ymax"]]
            iou = compute_iou(p_box, gt_box)
            if iou > best_iou:
                best_iou = iou
                best_gt_idx = idx

        if best_iou >= iou_threshold and best_gt_idx >= 0:
            matched_gt.add(best_gt_idx)
            true_positives.append(pred)
        else:
            false_positives.append(pred)

    false_negatives = [gt for idx, gt in enumerate(ground_truth_boxes) if idx not in matched_gt]

    return {
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
    }


def render_error_analysis_card(
    image_path: Union[str, Path],
    ground_truth_boxes: List[Dict],
    predicted_boxes: List[Dict],
    output_path: Optional[Union[str, Path]] = None,
) -> Image.Image:
    """
    Renders visual analysis highlighting:
    - Green boxes: True Positives (correct detections)
    - Red boxes: False Positives (spurious / misclassified detections)
    - Yellow dashed boxes: False Negatives (missed road defects)
    """
    with Image.open(image_path) as im:
        canvas = im.convert("RGB")
    draw = ImageDraw.Draw(canvas)

    categorized = categorize_detections(ground_truth_boxes, predicted_boxes)

    # True positives: Green
    for tp in categorized["true_positives"]:
        draw.rectangle(
            [tp["bbox_xmin"], tp["bbox_ymin"], tp["bbox_xmax"], tp["bbox_ymax"]],
            outline=(34, 197, 94),
            width=3,
        )

    # False positives: Red
    for fp in categorized["false_positives"]:
        draw.rectangle(
            [fp["bbox_xmin"], fp["bbox_ymin"], fp["bbox_xmax"], fp["bbox_ymax"]],
            outline=(239, 68, 68),
            width=3,
        )

    # False negatives (Missed): Yellow
    for fn in categorized["false_negatives"]:
        draw.rectangle(
            [fn["xmin"], fn["ymin"], fn["xmax"], fn["ymax"]],
            outline=(234, 179, 8),
            width=3,
        )

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(out_p)

    return canvas
