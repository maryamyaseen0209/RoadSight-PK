from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DetectionRun(Base):
    """Stores metadata and summary metrics for each single-image defect detection execution."""
    __tablename__ = "detection_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    image_name = Column(String(255), nullable=False)
    image_path = Column(String(1024), nullable=False)
    output_image_path = Column(String(1024), nullable=True)
    total_detections = Column(Integer, default=0, nullable=False)
    inference_time_ms = Column(Float, default=0.0, nullable=False)
    model_name = Column(String(100), default="YOLO26n", nullable=False)
    confidence_threshold = Column(Float, default=0.25, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    detections = relationship("Detection", back_populates="run", cascade="all, delete-orphan")


class Detection(Base):
    """Stores individual bounding box detections linked to a specific DetectionRun."""
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    run_id = Column(String(36), ForeignKey("detection_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    class_id = Column(Integer, nullable=False)
    class_name = Column(String(100), nullable=False)
    confidence = Column(Float, nullable=False)
    bbox_xmin = Column(Float, nullable=False)
    bbox_ymin = Column(Float, nullable=False)
    bbox_xmax = Column(Float, nullable=False)
    bbox_ymax = Column(Float, nullable=False)

    run = relationship("DetectionRun", back_populates="detections")


class ModelExperiment(Base):
    """Tracks training, validation, and benchmarking metrics across Phase 3-5 experiments."""
    __tablename__ = "model_experiments"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    experiment_name = Column(String(150), nullable=False, index=True)
    model_type = Column(String(100), nullable=False)  # e.g., YOLO26n, FasterRCNN_ResNet50
    dataset_split = Column(String(100), nullable=False)  # e.g., rdd2022_train, pk_10pct, pk_100pct
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    map50 = Column(Float, nullable=True)
    map50_95 = Column(Float, nullable=True)
    latency_ms = Column(Float, nullable=True)
    fps = Column(Float, nullable=True)
    config_yaml = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
