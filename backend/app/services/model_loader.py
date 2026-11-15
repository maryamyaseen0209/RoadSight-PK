import os
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
os.environ["YOLO_CONFIG_DIR"] = str(_BASE_DIR / "artifacts")
os.environ["YOLO_OFFLINE"] = "True"
os.environ["YOLO_VERBOSE"] = "False"
os.environ["ULTRALYTICS_AUTOINSTALL"] = "0"
os.environ["SETTINGS_CHECK"] = "0"
import time
from typing import Any, Dict, List, Optional, Tuple, Union
from PIL import Image, ImageDraw, ImageFont

from backend.app.core.config import settings
from backend.app.core.logging_config import logger

OFFICIAL_CLASS_MAPPING = {
    0: "Longitudinal Crack",
    1: "Transverse Crack",
    2: "Alligator Crack",
    3: "Pothole",
}

CLASS_COLOR_RGB = {
    0: (59, 130, 246),   # Blue: Longitudinal Crack [D00]
    1: (16, 185, 129),  # Emerald: Transverse Crack [D10]
    2: (245, 158, 11),  # Amber: Alligator Crack [D20]
    3: (239, 68, 68),   # Red: Pothole [D40]
}


class ModelRegistry:
    """Manages loaded models and startup lifecycle."""
    yolo_model: Any = None
    yolo_weights_path: Optional[str] = None
    yolo_model_name: str = "YOLO26n"

    faster_rcnn_model: Any = None
    faster_rcnn_weights_path: Optional[str] = None

    is_ready: bool = False


registry = ModelRegistry()


def find_best_yolo_checkpoint() -> Tuple[Path, str]:
    """Finds best available YOLO checkpoint following priority rules."""
    checkpoints_dir = Path(settings.BASE_DIR) / settings.CHECKPOINTS_DIR

    candidate_files = [
        ("yolo_pakistani_finetuned_best.pt", "YOLO26n (Pakistani Fine-Tuned)"),
        ("yolo_international_best.pt", "YOLO26n (International Baseline)"),
        ("best_yolo.pt", "YOLO26n (Checkpointed)"),
        ("yolo26n.pt", "YOLO26n (Pretrained)"),
        ("yolo11n.pt", "YOLO11n (Pretrained)"),
    ]

    for filename, display_name in candidate_files:
        candidate_path = checkpoints_dir / filename
        if candidate_path.exists():
            return candidate_path, display_name

    # If not in checkpoints_dir, check default fallback
    return Path("yolo11n.pt"), "YOLO11n (Fallback)"


def load_models_on_startup():
    """Loads active model checkpoints once during FastAPI lifespan startup."""
    logger.info("Initializing defect detection models for inference...")

    # Load YOLO
    yolo_path, yolo_name = find_best_yolo_checkpoint()
    registry.yolo_model_name = yolo_name
    registry.yolo_weights_path = str(yolo_path)

    try:
        from ultralytics import YOLO  # type: ignore
        logger.info(f"Loading YOLO checkpoint: {yolo_path} ({yolo_name})")
        registry.yolo_model = YOLO(str(yolo_path))
        registry.is_ready = True
        logger.info(f"YOLO detector successfully initialized from {yolo_path}")
    except Exception as e:
        logger.warning(f"Could not load Ultralytics YOLO model ({e}). Fallback detector will be used.")
        registry.yolo_model = None

    # Check Faster R-CNN
    frcnn_path = Path(settings.BASE_DIR) / settings.CHECKPOINTS_DIR / "faster_rcnn_international_best.pth"
    if frcnn_path.exists():
        registry.faster_rcnn_weights_path = str(frcnn_path)
        logger.info(f"Found Faster R-CNN checkpoint: {frcnn_path}")

    return registry


def draw_detection_overlay(
    image: Image.Image,
    detections: List[Dict[str, Any]],
    line_width: int = 3,
) -> Image.Image:
    """Draws clear color-coded bounding boxes and confidence labels on image."""
    annotated = image.copy().convert("RGB")
    draw = ImageDraw.Draw(annotated)

    for det in detections:
        cid = det["class_id"]
        cname = det["class_name"]
        conf = det["confidence"]
        color = CLASS_COLOR_RGB.get(cid, (255, 255, 255))

        x1 = det["bbox_xmin"]
        y1 = det["bbox_ymin"]
        x2 = det["bbox_xmax"]
        y2 = det["bbox_ymax"]

        # Bounding box
        draw.rectangle([x1, y1, x2, y2], outline=color, width=line_width)

        # Label tag
        label_text = f"{cname} {conf:.2f}"
        tag_w = len(label_text) * 7 + 10
        tag_h = 18
        draw.rectangle([x1, max(0, y1 - tag_h), x1 + tag_w, y1], fill=color)
        draw.text((x1 + 4, max(0, y1 - tag_h + 2)), label_text, fill=(255, 255, 255))

    return annotated


def run_detection_pipeline(
    image_bytes: bytes,
    run_id: str,
    original_filename: str,
    confidence_threshold: float = 0.25,
    model_choice: str = "YOLO",
) -> Tuple[List[Dict[str, Any]], float, str, str]:
    """
    Executes end-to-end detection on uploaded image bytes.
    Saves:
      - Original image to artifacts/outputs/{run_id}_original.jpg
      - Annotated image to artifacts/outputs/{run_id}.jpg
    Returns:
      (detections, inference_time_ms, original_rel_url, annotated_rel_url)
    """
    start_time = time.perf_counter()

    import io
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    w, h = img.size

    # Save original image
    outputs_dir = settings.outputs_path
    orig_path = outputs_dir / f"{run_id}_original.jpg"
    img.save(orig_path, format="JPEG", quality=95)

    detections: List[Dict[str, Any]] = []

    # Run inference with YOLO if requested and loaded
    if model_choice.upper().startswith("YOLO") and registry.yolo_model is not None:
        try:
            results = registry.yolo_model.predict(
                source=img,
                conf=confidence_threshold,
                verbose=False,
            )
            for r in results:
                boxes = r.boxes
                for i in range(len(boxes)):
                    box = boxes[i]
                    coords = box.xyxy[0].tolist()
                    cid = int(box.cls[0].item())
                    # Limit to official 4 classes
                    if cid in OFFICIAL_CLASS_MAPPING:
                        conf = float(box.conf[0].item())
                        cname = OFFICIAL_CLASS_MAPPING[cid]
                        xmin = max(0.0, min(float(w), coords[0]))
                        ymin = max(0.0, min(float(h), coords[1]))
                        xmax = max(0.0, min(float(w), coords[2]))
                        ymax = max(0.0, min(float(h), coords[3]))

                        detections.append({
                            "class_id": cid,
                            "class_name": cname,
                            "confidence": round(conf, 4),
                            "bbox_xmin": round(xmin, 2),
                            "bbox_ymin": round(ymin, 2),
                            "bbox_xmax": round(xmax, 2),
                            "bbox_ymax": round(ymax, 2),
                            "x1": round(xmin, 2),
                            "y1": round(ymin, 2),
                            "x2": round(xmax, 2),
                            "y2": round(ymax, 2),
                        })
        except Exception as e:
            logger.error(f"Inference execution failed: {e}")

    # Draw color-coded overlay
    annotated_img = draw_detection_overlay(img, detections)
    annotated_path = outputs_dir / f"{run_id}.jpg"
    annotated_img.save(annotated_path, format="JPEG", quality=95)

    elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
    orig_url = f"/outputs/{run_id}_original.jpg"
    annotated_url = f"/outputs/{run_id}.jpg"

    return detections, elapsed_ms, orig_url, annotated_url
