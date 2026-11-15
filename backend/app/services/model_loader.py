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
    yolo_international_model: Any = None
    yolo_pakistani_model: Any = None
    yolo_weights_path: Optional[str] = None
    yolo_model_name: str = "YOLO26n (International Baseline)"

    faster_rcnn_model: Any = None
    faster_rcnn_weights_path: Optional[str] = None

    is_ready: bool = False


registry = ModelRegistry()


def load_models_on_startup():
    """Loads active model checkpoints once during FastAPI lifespan startup."""
    logger.info("Initializing defect detection models for inference...")
    checkpoints_dir = Path(settings.BASE_DIR) / settings.CHECKPOINTS_DIR

    try:
        from ultralytics import YOLO  # type: ignore

        # 1. Load International Baseline YOLO (robust multi-country weights, mAP50=0.5302)
        intl_path = checkpoints_dir / "yolo_international_best.pt"
        if intl_path.exists():
            try:
                registry.yolo_international_model = YOLO(str(intl_path))
                logger.info(f"Loaded International Baseline YOLO: {intl_path}")
            except Exception as e:
                logger.warning(f"Failed to load international YOLO: {e}")

        # 2. Load Pakistani Fine-Tuned YOLO
        pk_path = checkpoints_dir / "yolo_pakistani_finetuned_best.pt"
        if pk_path.exists():
            try:
                registry.yolo_pakistani_model = YOLO(str(pk_path))
                logger.info(f"Loaded Pakistani Fine-Tuned YOLO: {pk_path}")
            except Exception as e:
                logger.warning(f"Failed to load Pakistani YOLO: {e}")

        # Set default YOLO detector: prefer international baseline for broad generalization
        if registry.yolo_international_model is not None:
            registry.yolo_model = registry.yolo_international_model
            registry.yolo_model_name = "YOLO26n (International Baseline)"
            registry.yolo_weights_path = str(intl_path)
            registry.is_ready = True
        elif registry.yolo_pakistani_model is not None:
            registry.yolo_model = registry.yolo_pakistani_model
            registry.yolo_model_name = "YOLO26n (Pakistani Fine-Tuned)"
            registry.yolo_weights_path = str(pk_path)
            registry.is_ready = True
        else:
            # Fallback to pretrained
            fallback_path = Path("yolo11n.pt")
            registry.yolo_model = YOLO(str(fallback_path))
            registry.yolo_model_name = "YOLO11n (Pretrained)"
            registry.yolo_weights_path = str(fallback_path)
            registry.is_ready = True

        # Warm up YOLO models to eliminate cold-start latency on first user request
        try:
            dummy_img = Image.new("RGB", (64, 64), color=(128, 128, 128))
            if registry.yolo_international_model:
                registry.yolo_international_model.predict(source=dummy_img, conf=0.5, imgsz=64, verbose=False)
            if registry.yolo_pakistani_model:
                registry.yolo_pakistani_model.predict(source=dummy_img, conf=0.5, imgsz=64, verbose=False)
            logger.info("YOLO models pre-warmed in memory.")
        except Exception as e:
            logger.debug(f"Warmup notice: {e}")

    except Exception as e:
        logger.warning(f"Could not load Ultralytics YOLO models ({e}).")
        registry.yolo_model = None

    # 3. Load Faster R-CNN ResNet-50 FPN V2
    frcnn_path = checkpoints_dir / "faster_rcnn_international_best.pth"
    if frcnn_path.exists():
        try:
            import torch
            from ml.models.faster_rcnn_detector import build_faster_rcnn_model
            frcnn = build_faster_rcnn_model(num_classes=5, pretrained=False)
            state = torch.load(str(frcnn_path), map_location="cpu", weights_only=False)
            frcnn.load_state_dict(state)
            frcnn.eval()
            registry.faster_rcnn_model = frcnn
            registry.faster_rcnn_weights_path = str(frcnn_path)
            logger.info(f"Faster R-CNN detector initialized successfully from {frcnn_path}")
        except Exception as e:
            logger.warning(f"Failed to load Faster R-CNN checkpoint ({e})")

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
    choice_upper = (model_choice or "YOLO").upper()

    # 1. Faster R-CNN Branch
    if "FASTER" in choice_upper and registry.faster_rcnn_model is not None:
        try:
            import torch
            from torchvision.transforms import functional as TF

            tensor_img = TF.to_tensor(img)
            with torch.inference_mode():
                preds = registry.faster_rcnn_model([tensor_img])[0]

            boxes = preds["boxes"]
            scores = preds["scores"]
            labels = preds["labels"]

            for box, score, lbl in zip(boxes, scores, labels):
                conf_val = float(score.item())
                label_val = int(lbl.item())
                # Faster R-CNN mapping: class 0 is Background, 1: D00, 2: D10, 3: D20, 4: D40
                mapped_cid = label_val - 1
                if conf_val >= confidence_threshold and mapped_cid in OFFICIAL_CLASS_MAPPING:
                    coords = box.tolist()
                    xmin = max(0.0, min(float(w), coords[0]))
                    ymin = max(0.0, min(float(h), coords[1]))
                    xmax = max(0.0, min(float(w), coords[2]))
                    ymax = max(0.0, min(float(h), coords[3]))
                    detections.append({
                        "class_id": mapped_cid,
                        "class_name": OFFICIAL_CLASS_MAPPING[mapped_cid],
                        "confidence": round(conf_val, 4),
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
            logger.error(f"Faster R-CNN inference failed: {e}")

    # 2. YOLO Branch
    else:
        # Select active YOLO model
        active_yolo = None
        is_pakistani = "PAKISTAN" in choice_upper
        if is_pakistani and registry.yolo_pakistani_model is not None:
            active_yolo = registry.yolo_pakistani_model
            # For fine-tuned Pakistani model, align raw objectness score threshold with training distribution
            eff_conf = min(confidence_threshold, 0.15) if confidence_threshold > 0.15 else confidence_threshold
        elif registry.yolo_international_model is not None:
            active_yolo = registry.yolo_international_model
            eff_conf = confidence_threshold
        else:
            active_yolo = registry.yolo_model
            eff_conf = confidence_threshold

        if active_yolo is not None:
            try:
                results = active_yolo.predict(
                    source=img,
                    conf=eff_conf,
                    iou=0.45,
                    imgsz=640,
                    verbose=False,
                )
                for r in results:
                    boxes = r.boxes
                    for i in range(len(boxes)):
                        box = boxes[i]
                        coords = box.xyxy[0].tolist()
                        cid = int(box.cls[0].item())
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
