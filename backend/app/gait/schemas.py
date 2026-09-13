"""
Pydantic schemas for ToddleAI gait analysis ported into SAAR with Section 12 structured schemas.
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
    REDUCED = "REDUCED"


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
    pipeline_confidence: float = 0.0  # Composite confidence score (0.0-1.0)


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


# ===================================================================
# Advanced Gait Analysis & Kinematics Schemas (Section 12 Compliant)
# ===================================================================

class CycleROMItem(BaseModel):
    cycle_index: int
    start_time: float
    end_time: float
    min_angle_deg: float
    max_angle_deg: float
    rom_deg: float
    valid_samples: int


class JointROMModel(BaseModel):
    joint_name: str
    min_angle_deg: Optional[float] = None
    max_angle_deg: Optional[float] = None
    rom_deg: Optional[float] = None
    cycle_roms: List[CycleROMItem] = Field(default_factory=list)
    valid_cycles: int = 0
    valid_frames: int = 0
    confidence: float = 0.0


class JointMotionProfile(BaseModel):
    left_hip: JointROMModel
    right_hip: JointROMModel
    left_knee: JointROMModel
    right_knee: JointROMModel
    left_ankle: JointROMModel
    right_ankle: JointROMModel


class PostureMetrics(BaseModel):
    trunk_angle_deg: Optional[float] = None
    trunk_variability_deg: Optional[float] = None
    lateral_sway: Optional[float] = None
    confidence: float = 0.0


class SpatialMetrics(BaseModel):
    is_calibrated: bool = False
    calibration_source: Optional[str] = None
    uncalibrated_reason: Optional[str] = None
    step_length_m: Optional[float] = None
    stride_length_m: Optional[float] = None
    walking_speed_m_per_s: Optional[float] = None
    distance_m: Optional[float] = None
    foot_progression_angle_deg: Optional[float] = None
    left_foot_progression_deg: Optional[float] = None
    right_foot_progression_deg: Optional[float] = None
    walking_direction: str = "unknown"


class SymmetryProfile(BaseModel):
    step_time_asymmetry_pct: Optional[float] = None
    step_length_asymmetry_pct: Optional[float] = None
    hip_rom_asymmetry_pct: Optional[float] = None
    knee_rom_asymmetry_pct: Optional[float] = None
    ankle_rom_asymmetry_pct: Optional[float] = None


class AdvancedTemporalMetrics(BaseModel):
    step_count: int = 0
    cadence_steps_per_min: float = 0.0
    mean_step_time_sec: float = 0.0
    median_step_time_sec: float = 0.0
    step_time_variability_pct: float = 0.0
    mean_stride_time_sec: Optional[float] = None
    stance_time: Optional[float] = None
    swing_time: Optional[float] = None
    double_support_time: Optional[float] = None
    stance_phase_pct: Optional[float] = None
    swing_phase_pct: Optional[float] = None
    double_support_pct: Optional[float] = None


class ReferenceMetricItem(BaseModel):
    metric_id: str
    display_name: str
    measured: Optional[float] = None
    measured_value: Optional[float] = None
    reference_mean: Optional[float] = None
    reference_sd: Optional[float] = None
    difference_from_mean: Optional[float] = None
    z_score: Optional[float] = None
    unit: str = ""
    reference_range_str: str = ""
    ref_low: Optional[float] = None
    ref_high: Optional[float] = None
    status: str = "within_reference"  # "within_reference", "below_reference", "above_reference", "insufficient_data"
    deviation: Optional[float] = None
    confidence: str = "medium"
    source: str = ""
    age_group: str = ""
    is_interpolated: bool = False
    clinical_note: str = ""



class GaitProfile(BaseModel):
    temporal: AdvancedTemporalMetrics
    spatial: SpatialMetrics
    symmetry: SymmetryProfile
    joint_motion: JointMotionProfile
    posture: PostureMetrics
    references: List[ReferenceMetricItem] = Field(default_factory=list)


class PillarTakeaway(BaseModel):
    category: str  # "rhythm", "symmetry", "joint_mobility", "posture"
    title: str
    headline: str
    explanation: str
    score: float  # 0 - 100
    status: str   # "typical", "mild_variation", "review_recommended"
    badge: str    # "🟢 Typical", "🟡 Mild Variation", "🔴 Review"
    icon: str     # "activity", "scale", "layers", "compass"


class DevelopmentalSummary(BaseModel):
    overall_score: float  # 0 - 100
    status_badge: str     # "ON_TRACK", "EMERGING_VARIATION", "REVIEW_RECOMMENDED"
    status_title: str     # e.g., "On Track for Age"
    status_theme: str     # "green", "amber", "red"
    summary_headline: str
    pillars: List[PillarTakeaway] = Field(default_factory=list)
    milestone_context: str
    parent_tips: List[str] = Field(default_factory=list)
    pediatrician_discussion_point: str
    disclaimer: str = (
        "This automated video screening report provides observational motion analysis to assist parents and "
        "clinicians. It does not constitute a medical diagnosis. Consult a pediatrician or pediatric physical therapist for formal evaluation."
    )


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
    pipeline_confidence: float = 0.0  # Top-level composite accuracy indicator (0.0-1.0)
    
    # Unified Parent-Friendly Summary (Pillar synthesis)
    developmental_summary: Optional[DevelopmentalSummary] = None
    
    # Section 12 Structured Profile & Kinematics extensions
    gait_profile: Optional[GaitProfile] = None
    temporal: Optional[AdvancedTemporalMetrics] = None
    spatial: Optional[SpatialMetrics] = None
    symmetry: Optional[SymmetryProfile] = None
    joint_motion: Optional[JointMotionProfile] = None
    posture: Optional[PostureMetrics] = None
    reference_comparisons: List[ReferenceMetricItem] = Field(default_factory=list)
    joint_angle_curves: Optional[Dict[str, Any]] = None

