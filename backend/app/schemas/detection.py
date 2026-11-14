from datetime import datetime
from typing import List, Optional
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

    model_config = {"from_attributes": True}


class PredictResponse(BaseModel):
    run_id: str
    image_name: str
    image_url: str
    output_image_url: Optional[str]
    total_detections: int
    inference_time_ms: float
    model_name: str
    created_at: datetime
    detections: List[DetectionItem]

    model_config = {"from_attributes": True}


class DetectionRunSummary(BaseModel):
    id: str
    image_name: str
    image_url: str
    output_image_url: Optional[str]
    total_detections: int
    inference_time_ms: float
    model_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class OverallSummaryResponse(BaseModel):
    total_runs: int
    total_detections: int
    average_inference_time_ms: float
    defect_counts_by_class: dict
    model_distribution: dict


class ModelInfoResponse(BaseModel):
    model_name: str
    weights_path: str
    weights_present: bool
    classes: dict
    confidence_threshold: float
    iou_threshold: float
    status: str
