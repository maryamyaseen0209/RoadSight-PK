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


def merge_adjacent_defect_boxes(
    detections: List[Dict[str, Any]],
    iou_thresh: float = 0.20,
) -> List[Dict[str, Any]]:
    """
    Class-Agnostic / Same Priority Tier NMS Merge:
    Merges overlapping or adjacent defect bounding boxes into a unified damage region.
    """
    if len(detections) <= 1:
        return detections

    def calc_iou(b1, b2):
        xA = max(b1[0], b2[0])
        yA = max(b1[1], b2[1])
        xB = min(b1[2], b2[2])
        yB = min(b1[3], b2[3])
        inter = max(0.0, xB - xA) * max(0.0, yB - yA)
        areaA = max(1.0, (b1[2] - b1[0]) * (b1[3] - b1[1]))
        areaB = max(1.0, (b2[2] - b2[0]) * (b2[3] - b2[1]))
        return inter / (areaA + areaB - inter)

    sorted_dets = sorted(detections, key=lambda d: d.get("confidence", 0), reverse=True)
    merged: List[Dict[str, Any]] = []

    while sorted_dets:
        curr = dict(sorted_dets.pop(0))
        curr_box = [
            float(curr.get("bbox_xmin", 0)),
            float(curr.get("bbox_ymin", 0)),
            float(curr.get("bbox_xmax", 0)),
            float(curr.get("bbox_ymax", 0)),
        ]

        remaining = []
        for other in sorted_dets:
            other_box = [
                float(other.get("bbox_xmin", 0)),
                float(other.get("bbox_ymin", 0)),
                float(other.get("bbox_xmax", 0)),
                float(other.get("bbox_ymax", 0)),
            ]
            iou = calc_iou(curr_box, other_box)
            if iou >= iou_thresh:
                # Merge into cohesive unified damage region
                curr_box[0] = min(curr_box[0], other_box[0])
                curr_box[1] = min(curr_box[1], other_box[1])
                curr_box[2] = max(curr_box[2], other_box[2])
                curr_box[3] = max(curr_box[3], other_box[3])
                curr["confidence"] = max(curr["confidence"], other["confidence"])
                if other.get("class_id", 0) > curr.get("class_id", 0):
                    curr["class_id"] = other["class_id"]
                    curr["class_name"] = other["class_name"]
            else:
                remaining.append(other)

        curr["bbox_xmin"] = round(curr_box[0], 2)
        curr["bbox_ymin"] = round(curr_box[1], 2)
        curr["bbox_xmax"] = round(curr_box[2], 2)
        curr["bbox_ymax"] = round(curr_box[3], 2)
        curr["x1"] = curr["bbox_xmin"]
        curr["y1"] = curr["bbox_ymin"]
        curr["x2"] = curr["bbox_xmax"]
        curr["y2"] = curr["bbox_ymax"]

        merged.append(curr)
        sorted_dets = remaining

    return merged


def draw_detection_overlay(
    image: Image.Image,
    detections: List[Dict[str, Any]],
    line_width: int = 3,
) -> Image.Image:
    """Draws clear color-coded bounding boxes and confidence labels on image."""
    annotated = image.copy().convert("RGB")
    draw = ImageDraw.Draw(annotated)
    w, h = annotated.size

    try:
        font = ImageFont.truetype("arial.ttf", 13)
    except Exception:
        font = ImageFont.load_default()

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

        # Label tag with accurate text measurement and clipping protection
        label_text = f"{cname} {conf:.2f}"
        try:
            bbox = draw.textbbox((0, 0), label_text, font=font)
            tag_w = (bbox[2] - bbox[0]) + 10
            tag_h = (bbox[3] - bbox[1]) + 6
        except Exception:
            tag_w = len(label_text) * 7 + 10
            tag_h = 18

        # Position above box if space permits, otherwise place inside top border
        if y1 >= tag_h + 2:
            tag_y1 = y1 - tag_h
            tag_y2 = y1
        else:
            tag_y1 = y1
            tag_y2 = y1 + tag_h

        tag_x1 = max(0.0, min(float(x1), float(w - tag_w)))
        tag_x2 = tag_x1 + tag_w

        draw.rectangle([tag_x1, tag_y1, tag_x2, tag_y2], fill=color)
        draw.text((tag_x1 + 5, tag_y1 + 2), label_text, font=font, fill=(255, 255, 255))

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

                    # Discard degenerate / whole-frame false-positive bounding boxes (e.g. spanning > 82% width or > 40% total area)
                    bw = xmax - xmin
                    bh = ymax - ymin
                    if bw > 0.82 * float(w) and bh > 0.50 * float(h):
                        continue
                    if (bw * bh) > 0.40 * float(w * h):
                        continue

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
        if "PAKISTAN" in choice_upper and registry.yolo_pakistani_model is not None:
            active_yolo = registry.yolo_pakistani_model
        elif registry.yolo_international_model is not None:
            active_yolo = registry.yolo_international_model
        else:
            active_yolo = registry.yolo_model

        # Ensure thin road cracks (0.15-0.24) are not dropped when user slider is at 0.25
        effective_conf = min(float(confidence_threshold), 0.15)

        if active_yolo is not None:
            try:
                # 1. Standard 640 pass with Class-Agnostic NMS (IoU 0.20)
                results = active_yolo.predict(
                    source=img,
                    conf=effective_conf,
                    iou=0.20,  # Forces overlapping adjacent boxes of similar classes to merge
                    imgsz=640,
                    agnostic_nms=True,  # Merges disparate class boxes into a unified damage region
                    verbose=False,
                )

                # Fallback for close-up cracks or low-res web thumbnails (like 'images (1).jpg', 'images (2).jpg'):
                # Run a second pass with augment=True (multi-scale TTA) and a relaxed confidence floor (0.10)
                has_boxes = any(len(r.boxes) > 0 for r in results if r.boxes is not None)
                if not has_boxes:
                    fallback_conf = min(float(confidence_threshold), 0.10)
                    results = active_yolo.predict(
                        source=img,
                        conf=fallback_conf,
                        iou=0.20,  # Forces overlapping adjacent boxes of similar classes to merge
                        imgsz=640,
                        augment=True,  # Enables Test-Time Augmentation across scales/flips
                        agnostic_nms=True,  # Merges disparate class boxes into a unified damage region
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

                            # Discard degenerate / whole-frame false-positive bounding boxes
                            bw = xmax - xmin
                            bh = ymax - ymin
                            if bw > 0.82 * float(w) and bh > 0.50 * float(h):
                                continue
                            if (bw * bh) > 0.40 * float(w * h):
                                continue

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

    # 3. OpenCV fallback: Supplement missed water-filled potholes (D40) or close-up structural cracks
    try:
        import cv2
        import numpy as np
        from backend.opencv_fallback import supplement_missed_defects

        image_bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        detections = supplement_missed_defects(
            image_bgr,
            detections,
            conf_threshold=min(float(confidence_threshold), 0.15),
        )
    except Exception as e:
        logger.warning(f"OpenCV fallback processing notice: {e}")

    # 4. Post-Processing NMS Merge: Merge adjacent / overlapping defect boxes (IoU >= 0.20)
    detections = merge_adjacent_defect_boxes(detections, iou_thresh=0.20)

    # Draw color-coded overlay
    annotated_img = draw_detection_overlay(img, detections)
    annotated_path = outputs_dir / f"{run_id}.jpg"
    annotated_img.save(annotated_path, format="JPEG", quality=95)

    elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
    orig_url = f"/outputs/{run_id}_original.jpg"
    annotated_url = f"/outputs/{run_id}.jpg"

    return detections, elapsed_ms, orig_url, annotated_url
