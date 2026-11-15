import csv
import json
from pathlib import Path
from typing import Dict, Any

from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.logging_config import logger
from backend.app.models.detection import ModelExperiment


def sync_experiments_to_database(db: Session) -> int:
    """
    Syncs experimental evaluation records from experiments/metrics/ into SQLite model_experiments table.
    Ensures idempotency (updates existing or inserts new).
    """
    metrics_dir = settings.metrics_path
    synced_count = 0

    # 1. Sync from individual JSON files with high precision
    exp_files = [
        ("exp1_international_baseline_yolo.json", "exp1_yolo_baseline", "YOLO26n", "RDD2022_Test"),
        ("exp1_international_baseline_faster_rcnn.json", "exp1_frcnn_baseline", "Faster_RCNN", "RDD2022_Test"),
        ("exp3_pakistani_zeroshot.json", "exp3_zeroshot", "YOLO26n", "Pakistani_Test_ZeroShot"),
        ("exp4_transfer_learning.json", "exp4_transfer_learning", "YOLO26n", "Pakistani_Test_Subsets"),
        ("exp5_efficiency_comparison.json", "exp5_efficiency", "Comparative", "Speed_Benchmark"),
    ]

    for fname, exp_id, default_model, default_split in exp_files:
        fpath = metrics_dir / fname
        if fpath.exists():
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    exp_name = data.get("experiment_id", exp_id)
                    model_type = data.get("model_name", default_model)
                    
                    map50 = data.get("mAP50")
                    map50_95 = data.get("mAP50_95")
                    precision = data.get("precision")
                    recall = data.get("recall")
                    f1 = data.get("f1_score")
                    
                    # Latency & FPS from exp5 or master
                    latency = None
                    fps = None
                    if "models" in data:
                        yolo_eff = data["models"].get("YOLO26n", {})
                        latency = yolo_eff.get("gpu_latency_ms")
                        fps = yolo_eff.get("gpu_fps")

                    existing = db.query(ModelExperiment).filter_by(experiment_name=exp_name).first()
                    if existing:
                        if map50 is not None:
                            existing.map50 = map50
                        if map50_95 is not None:
                            existing.map50_95 = map50_95
                        if precision is not None:
                            existing.precision = precision
                        if recall is not None:
                            existing.recall = recall
                        if f1 is not None:
                            existing.f1_score = f1
                        if latency is not None:
                            existing.latency_ms = latency
                        if fps is not None:
                            existing.fps = fps
                        existing.config_yaml = json.dumps(data)
                    else:
                        record = ModelExperiment(
                            experiment_name=exp_name,
                            model_type=model_type,
                            dataset_split=default_split,
                            precision=precision,
                            recall=recall,
                            f1_score=f1,
                            map50=map50,
                            map50_95=map50_95,
                            latency_ms=latency,
                            fps=fps,
                            config_yaml=json.dumps(data),
                        )
                        db.add(record)
                    synced_count += 1
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to sync {fname}: {e}")

    # 2. Sync from CSV
    csv_path = metrics_dir / "model_experiments.csv"
    if csv_path.exists():
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    exp_name = row.get("experiment_id") or row.get("experiment_name", "unnamed_exp")
                    model_type = row.get("model_name") or row.get("model_type", "YOLO")
                    dataset_split = row.get("dataset") or row.get("dataset_split", "test")
                    
                    exists = db.query(ModelExperiment).filter_by(experiment_name=exp_name).first()
                    if not exists:
                        map50_val = float(row["mAP50"]) if row.get("mAP50") else None
                        lat_val = float(row["latency_ms"]) if row.get("latency_ms") else None
                        fps_val = round(1000.0 / lat_val, 2) if lat_val and lat_val > 0 else None

                        record = ModelExperiment(
                            experiment_name=exp_name,
                            model_type=model_type,
                            dataset_split=dataset_split,
                            map50=map50_val,
                            latency_ms=lat_val,
                            fps=fps_val,
                            config_yaml=json.dumps(row),
                        )
                        db.add(record)
                        synced_count += 1
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to sync experiments from CSV: {e}")

    logger.info(f"Synchronized experimental records into SQLite model_experiments table.")
    return synced_count
