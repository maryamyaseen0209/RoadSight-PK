from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DetectionItem(BaseModel):
    id: Optional[int] = None
    class_id: int = Field(..., ge=0, le=3)
    class_name: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox_xmin: float
    bbox_ymin: float
    bbox_xmax: float
    bbox_ymax: float
    x1: Optional[float] = None
    y1: Optional[float] = None
    x2: Optional[float] = None
    y2: Optional[float] = None

    model_config = {"from_attributes": True}


class PredictResponse(BaseModel):
    run_id: str
    image_name: str
    image_url: str
    output_image_url: str
    total_detections: int
    inference_time_ms: float
    model_name: str
    confidence_threshold: float = 0.25
    created_at: datetime
    detections: List[DetectionItem]

    model_config = {"from_attributes": True}


class DetectionRunDetail(BaseModel):
    id: str
    run_id: str
    image_name: str
    image_url: str
    output_image_url: str
    total_detections: int
    inference_time_ms: float
    model_name: str
    confidence_threshold: float = 0.25
    created_at: datetime
    detections: List[DetectionItem]

    model_config = {"from_attributes": True}


class DetectionRunSummary(BaseModel):
    id: str
    image_name: str
    image_url: str
    output_image_url: str
    total_detections: int
    inference_time_ms: float
    model_name: str
    confidence_threshold: float = 0.25
    created_at: datetime

    model_config = {"from_attributes": True}


class OverallSummaryResponse(BaseModel):
    total_images_analyzed: int
    total_damage_detections: int
    average_inference_time_ms: float
    defect_counts_by_class: Dict[str, int]
    model_distribution: Dict[str, int]
    recent_runs: List[DetectionRunSummary] = []
    active_model: Dict[str, Any] = {}


class ModelInfoResponse(BaseModel):
    model_name: str
    weights_path: str
    weights_present: bool
    classes: dict
    confidence_threshold: float
    iou_threshold: float
    status: str
