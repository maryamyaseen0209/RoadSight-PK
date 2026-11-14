from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from PIL import Image

from backend.app.core.logging_config import logger
from ml.data.visualize_annotations import draw_bounding_boxes
from ml.models.yolo_detector import YOLODetectorWrapper

_DETECTOR_CACHE: Dict[str, YOLODetectorWrapper] = {}


def get_cached_detector(weights_path: str) -> YOLODetectorWrapper:
    """Singleton getter to prevent re-instantiating the detector weights on each request."""
    if weights_path not in _DETECTOR_CACHE:
        logger.info(f"Loading detector into memory: {weights_path}")
        _DETECTOR_CACHE[weights_path] = YOLODetectorWrapper(weights_path=weights_path)
    return _DETECTOR_CACHE[weights_path]


def run_single_inference(
    image_path: Union[str, Path],
    weights_path: str,
    confidence: float = 0.25,
    iou: float = 0.45,
    output_dir: Union[str, Path] = "artifacts/outputs",
) -> Tuple[List[Dict], str]:
    """
    Executes single-image inference and saves the rendered overlay.
    Returns: (list_of_detections, relative_url_path)
    """
    image_path = Path(image_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    detector = get_cached_detector(weights_path)
    detections = detector.predict(image_path, conf=confidence, iou=iou)

    # Render bounding box annotations
    annotated_filename = f"annotated_{image_path.name}"
    annotated_disk_path = output_dir / annotated_filename

    boxes_for_draw = [
        {
            "class_id": d["class_id"],
            "class_name": d["class_name"],
            "xmin": d["bbox_xmin"],
            "ymin": d["bbox_ymin"],
            "xmax": d["bbox_xmax"],
            "ymax": d["bbox_ymax"],
        }
        for d in detections
    ]

    with Image.open(image_path) as im:
        canvas = draw_bounding_boxes(im.convert("RGB"), boxes_for_draw)
        canvas.save(annotated_disk_path)

    relative_url = f"/outputs/{annotated_filename}"
    return detections, relative_url
