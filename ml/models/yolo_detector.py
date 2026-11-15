from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import yaml

from backend.app.core.logging_config import logger


class YOLODetectorWrapper:
    """
    Ultralytics YOLO wrapper for RoadSight-PK.
    Prioritizes YOLO26n with automatic fallback to YOLO11n / YOLOv8n.
    """

    def __init__(
        self,
        weights_path: Optional[Union[str, Path]] = None,
        preferred_model: str = "yolo26n.pt",
        fallback_model: str = "yolo11n.pt",
        device: str = "auto",
    ):
        self.preferred_model = preferred_model
        self.fallback_model = fallback_model
        self.device = device
        self.weights_path = Path(weights_path) if weights_path else None
        self.model = None
        self._load_model()

    def _load_model(self) -> None:
        try:
            from ultralytics import YOLO  # type: ignore

            target = str(self.weights_path) if self.weights_path and self.weights_path.exists() else self.preferred_model
            logger.info(f"Attempting to initialize detector with: {target}")
            try:
                self.model = YOLO(target)
            except Exception as e:
                logger.warning(f"Failed to load {target} ({e}). Falling back to {self.fallback_model}")
                self.model = YOLO(self.fallback_model)
        except ImportError:
            logger.warning("Ultralytics library is not installed in current environment. Using mock detector.")
            self.model = None

    def predict(
        self,
        source: Union[str, Path, Any],
        conf: float = 0.25,
        iou: float = 0.45,
        imgsz: int = 640,
        agnostic_nms: bool = True,
    ) -> List[Dict]:
        """Runs object detection on the target image and returns formatted detections."""
        if self.model is None:
            # Fallback mock when ultralytics is not installed
            return []

        effective_conf = min(float(conf), 0.15)

        results = self.model.predict(
            source=source,
            conf=effective_conf,
            iou=iou,
            imgsz=imgsz,
            agnostic_nms=agnostic_nms,
            verbose=False,
        )

        has_boxes = any(len(r.boxes) > 0 for r in results if r.boxes is not None)
        if not has_boxes:
            fallback_conf = min(float(conf), 0.10)
            results = self.model.predict(
                source=source,
                conf=fallback_conf,
                iou=iou,
                imgsz=imgsz,
                augment=True,
                agnostic_nms=agnostic_nms,
                verbose=False,
            )

        detections = []
        for r in results:
            boxes = r.boxes
            for i in range(len(boxes)):
                box = boxes[i]
                coords = box.xyxy[0].tolist()  # [xmin, ymin, xmax, ymax]
                cls_id = int(box.cls[0].item())
                confidence = float(box.conf[0].item())
                name = self.model.names.get(cls_id, f"Class {cls_id}")

                detections.append({
                    "class_id": cls_id,
                    "class_name": name,
                    "confidence": round(confidence, 4),
                    "bbox_xmin": round(coords[0], 2),
                    "bbox_ymin": round(coords[1], 2),
                    "bbox_xmax": round(coords[2], 2),
                    "bbox_ymax": round(coords[3], 2),
                })

        return detections

    def export_onnx(self, output_path: Optional[Union[str, Path]] = None) -> Optional[str]:
        """Exports the trained model to ONNX for optimized edge/browser execution."""
        if self.model is None:
            return None
        logger.info("Exporting model to ONNX...")
        path = self.model.export(format="onnx")
        return str(path)
