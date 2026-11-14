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
    Ensures idempotency (no duplicates).
    """
    metrics_dir = settings.metrics_path
    csv_path = metrics_dir / "model_experiments.csv"
    master_json_path = metrics_dir / "master_metrics_summary.json"

    synced_count = 0

    # 1. Sync from CSV
    if csv_path.exists():
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    exp_name = row.get("experiment_id") or row.get("experiment_name", "unnamed_exp")
                    model_type = row.get("model_name") or row.get("model_type", "YOLO")
                    dataset_split = row.get("dataset") or row.get("dataset_split", "test")
                    
                    # Check for duplicate
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

    # 2. Sync from master_metrics_summary.json if CSV missed any
    if master_json_path.exists():
        try:
            with open(master_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for exp_key, val in data.items():
                    exists = db.query(ModelExperiment).filter_by(experiment_name=exp_key).first()
                    if not exists and isinstance(val, dict):
                        lat_val = val.get("latency_ms")
                        fps_val = round(1000.0 / lat_val, 2) if lat_val and lat_val > 0 else None
                        record = ModelExperiment(
                            experiment_name=exp_key,
                            model_type="YOLO26n" if "yolo" in exp_key.lower() else "Faster_RCNN",
                            dataset_split="Benchmark",
                            map50=val.get("mAP50"),
                            latency_ms=lat_val,
                            fps=fps_val,
                            config_yaml=json.dumps(val),
                        )
                        db.add(record)
                        synced_count += 1
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to sync experiments from JSON: {e}")

    if synced_count > 0:
        logger.info(f"Successfully synced {synced_count} experiment records into SQLite model_experiments table.")
    return synced_count
