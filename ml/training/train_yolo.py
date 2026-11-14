from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union
import yaml

from backend.app.core.logging_config import logger


def run_yolo_training(
    data_yaml: Union[str, Path],
    model_name: str = "yolo26n.pt",
    epochs: int = 50,
    batch_size: int = 16,
    imgsz: int = 640,
    patience: int = 10,
    project: str = "artifacts/checkpoints",
    name: str = "exp_yolo",
    seed: int = 42,
    export_onnx: bool = True,
) -> Dict[str, Any]:
    """
    Executes Ultralytics YOLO training run with early stopping and reproducibility logging.
    """
    from ml.models.yolo_detector import YOLODetectorWrapper

    detector = YOLODetectorWrapper(preferred_model=model_name)
    if detector.model is None:
        raise RuntimeError("Ultralytics library is required for YOLO training. Install ultralytics to train.")

    logger.info(f"Starting YOLO training: model={model_name}, data={data_yaml}, epochs={epochs}")

    results = detector.model.train(
        data=str(data_yaml),
        epochs=epochs,
        batch=batch_size,
        imgsz=imgsz,
        patience=patience,
        project=project,
        name=name,
        seed=seed,
        exist_ok=True,
    )

    # Save training metadata YAML
    save_dir = Path(project) / name
    save_dir.mkdir(parents=True, exist_ok=True)
    reproducibility_meta = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_architecture": model_name,
        "dataset_yaml": str(data_yaml),
        "epochs": epochs,
        "batch_size": batch_size,
        "imgsz": imgsz,
        "seed": seed,
        "patience": patience,
    }
    with open(save_dir / "reproducibility_config.yaml", "w", encoding="utf-8") as f:
        yaml.dump(reproducibility_meta, f)

    onnx_path = None
    if export_onnx:
        try:
            onnx_path = detector.export_onnx()
        except Exception as e:
            logger.warning(f"ONNX export encountered an issue: {e}")

    return {
        "save_dir": str(save_dir),
        "reproducibility_meta": reproducibility_meta,
        "onnx_path": onnx_path,
    }
