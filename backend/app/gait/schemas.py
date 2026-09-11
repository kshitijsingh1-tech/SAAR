"""
Pydantic schemas for ToddleAI gait analysis ported into SAAR.
"""
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class Side(str, Enum):
    LEFT = "LEFT"
    RIGHT = "RIGHT"


class FrameStatus(str, Enum):
    GOOD = "GOOD"
    PARTIAL = "PARTIAL"
    REJECTED = "REJECTED"


class CaptureConfidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    REJECT = "REJECT"


class MetricStatus(str, Enum):
    TYPICAL = "TYPICAL"
    ELEVATED = "ELEVATED"


class Landmark(BaseModel):
    x: float
    y: float
    z: Optional[float] = 0.0
    visibility: float = 1.0


class PoseFrame(BaseModel):
    frame_index: int
    timestamp_ms: int
    landmarks: List[Landmark]
    source_width: int = 0
    source_height: int = 0


class FrameQuality(BaseModel):
    frame_index: int
    all_major_landmarks_visible: bool
    both_feet_visible: bool
    full_body_in_frame: bool
    camera_stable: bool
    landmark_confidence_mean: float
    status: FrameStatus


class CaptureAssessment(BaseModel):
    confidence: CaptureConfidence
    issues: List[str] = Field(default_factory=list)
    best_segment_start: int = 0
    best_segment_end: int = 0
    usable_step_count: int = 0
    good_frame_ratio: float = 0.0


class GaitEvent(BaseModel):
    frame_index: int
    time_seconds: float
    side: Side
    confidence: float


class StepMeasurement(BaseModel):
    duration: float
    ending_side: Side
    confidence: float


class TemporalMetrics(BaseModel):
    step_times: List[StepMeasurement] = Field(default_factory=list)
    mean_step_time: float = 0.0
    median_step_time: float = 0.0
    cadence: float = 0.0
    left_mean_step_time: float = 0.0
    right_mean_step_time: float = 0.0
    timing_difference_ms: float = 0.0
    symmetry_ratio: float = 0.0
    step_time_asymmetry_pct: float = 0.0
    step_time_cov: float = 0.0
    usable_step_count: int = 0
    usable_cycle_count: int = 0


class CadenceRange(BaseModel):
    low: float
    high: float
    source: str


class Observation(BaseModel):
    type: str
    measurement: str
    context: str
    note: str
    confidence: str = ""
    status: MetricStatus


class VideoMetadata(BaseModel):
    filename: str
    duration_seconds: float
    fps: float
    total_frames: int
    frames_processed: int
    width: int
    height: int


class CanonicalGaitResult(BaseModel):
    assessment_id: str
    status: str  # "success" or "rejected"
    child_age_months: int = 24
    video: VideoMetadata
    quality: CaptureAssessment
    metrics: TemporalMetrics
    cadence_range: CadenceRange
    milestone_context: str
    observations: List[Observation] = Field(default_factory=list)
    rejection_reason: Optional[str] = None
    recommendations: List[str] = Field(default_factory=list)
