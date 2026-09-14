"""
Pydantic models for the Badminton Biomechanics Video Analysis domain.
Mirrors the structure and rigor of backend/app/gait/schemas.py.
All unmeasurable and unimplemented metrics are structurally represented with
first-class availability and reason fields.
"""
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.schemas import GraphStateModel


class CaptureConfidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    REJECT = "REJECT"


class BadmintonAnalysisStatus(str, Enum):
    UPLOADING = "uploading"
    VALIDATING = "validating"
    EXTRACTING_FRAMES = "extracting_frames"
    ESTIMATING_POSE = "estimating_pose"
    ANALYZING_SHOTS = "analyzing_shots"
    COMPUTING_METRICS = "computing_metrics"
    QUALITY_ASSESSED_PIPELINE_PENDING = "quality_assessed_pipeline_pending"
    COMPLETED = "completed"
    REJECTED = "rejected"
    FAILED = "failed"
    NOT_YET_IMPLEMENTED = "not_yet_implemented"


class EnhancementMetadata(BaseModel):
    """
    Provenance and quality metadata tracking AI video super-resolution,
    temporal frame interpolation, and Gemini multimodal video reasoning.
    """
    is_enhanced: bool = False
    original_resolution: Optional[str] = None
    enhanced_resolution: Optional[str] = None
    original_fps: Optional[float] = None
    enhanced_fps: Optional[float] = None
    original_frame_count: Optional[int] = None
    enhanced_frame_count: Optional[int] = None
    enhancements_applied: List[str] = Field(default_factory=list)
    super_resolution_method: Optional[str] = None
    frame_interpolation_method: Optional[str] = None
    lighting_optimization_method: Optional[str] = None
    gemini_supervisor_applied: bool = False
    gemini_insights_summary: Optional[str] = None


class VideoMetadata(BaseModel):
    filename: str
    duration_seconds: float
    fps: float
    total_frames: int
    frame_count: Optional[int] = None
    frames_processed: int
    width: int
    height: int
    quality_score: Optional[float] = None
    camera_type: Optional[str] = "fixed_baseline"
    analysis_warnings: List[str] = Field(default_factory=list)
    preview_image_base64: Optional[str] = None
    enhancement: Optional[EnhancementMetadata] = None

    def model_post_init(self, __context: Any) -> None:
        if self.frame_count is None:
            self.frame_count = self.total_frames


class JobStage(str, Enum):
    UPLOADED = "uploaded"
    PREPROCESSING = "preprocessing"
    COURT_DETECTION = "court_detection"
    PLAYER_TRACKING = "player_tracking"
    POSE_ANALYSIS = "pose_analysis"
    SHUTTLE_TRACKING = "shuttle_tracking"
    SHOT_ANALYSIS = "shot_analysis"
    ANALYTICS = "analytics"
    REPORT_GENERATION = "report_generation"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class VideoUploadResponse(BaseModel):
    job_id: str
    status: str
    metadata: VideoMetadata
    preview_base64: Optional[str] = None
    suitable: bool
    issues: List[str] = Field(default_factory=list)


class Metric(BaseModel):
    """
    Standardized measurement representation where unavailability is a first-class property.
    Prevents silent fabrication or defaulting of unmeasurable physical properties.
    """
    name: str
    value: Optional[float] = None
    unit: str = ""
    confidence: str = "LOW"
    method: str = "NOT_YET_IMPLEMENTED"
    source: str = ""
    available: bool = False
    unavailable_reason: Optional[str] = "NOT_YET_IMPLEMENTED"
    uncertainty_range: Optional[List[float]] = None
    segments_used: Optional[int] = None


class QualityAssessment(BaseModel):
    confidence: CaptureConfidence
    issues: List[str] = Field(default_factory=list)
    camera_view: str = "unknown"
    camera_stability_score: Optional[float] = None
    unstable_frame_ratio: Optional[float] = None
    # Unmeasurable signals structurally represented as Metric without numeric defaults:
    player_visibility: Metric = Field(
        default_factory=lambda: Metric(
            name="player_visibility",
            available=False,
            unavailable_reason="Pending pose estimator integration (Phase 4)"
        )
    )
    court_visibility: Metric = Field(
        default_factory=lambda: Metric(
            name="court_visibility",
            available=False,
            unavailable_reason="Pending court detector integration (Phase 4/8)"
        )
    )
    racket_visibility: Metric = Field(
        default_factory=lambda: Metric(
            name="racket_visibility",
            available=False,
            unavailable_reason="NOT_RELIABLY_MEASURABLE: No object detector available in v1 (see BADMINTON_DECISIONS.md)"
        )
    )
    shuttle_visibility: Metric = Field(
        default_factory=lambda: Metric(
            name="shuttle_visibility",
            available=False,
            unavailable_reason="NOT_RELIABLY_MEASURABLE: No object detector available in v1 (see BADMINTON_DECISIONS.md)"
        )
    )


class Landmark(BaseModel):
    x: float
    y: float
    z: float = 0.0
    visibility: float = 1.0


class PoseFrame(BaseModel):
    """MediaPipe BlazePose 33-landmark output for a single video frame."""
    frame_index: int
    timestamp_ms: int
    landmarks: List[Landmark]
    source_width: int
    source_height: int
    is_detected: bool = True
    detection_reason: Optional[str] = None
    mean_confidence: float = 0.0


class CourtCalibration(BaseModel):
    """Real-world metric court calibration data derived from detected court corners."""
    is_calibrated: bool
    calibration_source: Optional[str] = None
    uncalibrated_reason: Optional[str] = None
    court_mode: str = "doubles"  # "singles" (13.40m x 5.18m) or "doubles" (13.40m x 6.10m)
    corners_pixel: Optional[List[List[float]]] = None
    court_dimensions_m: Optional[List[float]] = None
    homography_matrix: Optional[List[List[float]]] = None
    reprojection_error_px: Optional[float] = None
    net_keypoints_pixel: Optional[List[List[float]]] = None
    short_service_keypoints_pixel: Optional[List[List[List[float]]]] = None
    singles_boundary_corners_pixel: Optional[List[List[float]]] = None
    is_manual_override: bool = False
    confidence: float = 0.0


class ManualCourtCalibrationRequest(BaseModel):
    """User-provided 4-corner annotation for manual homography calibration fallback."""
    corners_pixel: List[List[float]] = Field(
        ...,
        description="List of 4 [x, y] coordinates in pixel space: Top-Left, Top-Right, Bottom-Right, Bottom-Left"
    )
    court_mode: Optional[str] = Field(
        default="doubles",
        description="Court mode: 'singles' (5.18m x 13.40m) or 'doubles' (6.10m x 13.40m)"
    )


class BadmintonFrame(BaseModel):
    """Extracted video frame metadata retaining provenance timestamps and indices."""
    frame_index: int
    timestamp_ms: int
    width: int
    height: int
    is_stable: bool = True


class PlayerMetadata(BaseModel):
    """Optional player and session intake metadata for downstream biomechanical context."""
    player_id: Optional[str] = None
    age: Optional[int] = None
    sex: Optional[str] = None
    body_weight_kg: Optional[float] = None
    skill_level: Optional[str] = None  # e.g., "beginner", "intermediate", "advanced", "elite"
    session_duration_min: Optional[float] = None
    match_type: Optional[str] = None  # e.g., "singles", "doubles"
    court_orientation: Optional[str] = None  # e.g., "near_court", "far_court", "side_view"
    session_date: Optional[str] = None


class ShotResult(BaseModel):
    shot_id: str
    shot_type: str = "UNKNOWN"
    confidence: float = 0.0
    start_time: float = 0.0
    contact_time: Optional[float] = None
    contact_frame: Optional[int] = None
    end_time: float = 0.0
    duration: float = 0.0
    player_position: Optional[List[float]] = None
    target_position: Optional[List[float]] = None
    racket_speed: Metric = Field(
        default_factory=lambda: Metric(
            name="racket_speed",
            unit="km/h",
            available=False,
            unavailable_reason="NOT_RELIABLY_MEASURABLE: No object detector available in v1"
        )
    )
    shuttle_speed: Metric = Field(
        default_factory=lambda: Metric(
            name="shuttle_speed",
            unit="km/h",
            available=False,
            unavailable_reason="NOT_RELIABLY_MEASURABLE: No object detector available in v1"
        )
    )
    trajectory: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_frames: List[int] = Field(default_factory=list)
    pose_features: Dict[str, Any] = Field(default_factory=dict)
    trajectory_features: Dict[str, Any] = Field(default_factory=dict)
    classification_reason: Optional[str] = None
    evidence_basis: Optional[str] = None
    available: bool = False


class RegionOccupancy(BaseModel):
    region_id: str  # e.g., "front_left", "front_center", "front_right", "mid_left", "mid_center", "mid_right", "rear_left", "rear_center", "rear_right"
    name: str       # e.g., "Front Left (Forecourt Net)"
    time_seconds: float = 0.0
    occupancy_pct: float = 0.0
    entries: int = 0
    exits: int = 0


class CourtMetrics(BaseModel):
    court_coverage_pct: Optional[float] = None
    court_coverage_reason: Optional[str] = "NOT_YET_IMPLEMENTED"
    convex_hull_area_m2: Optional[float] = None
    court_area_m2: Optional[float] = None
    base_recovery_time_sec: Optional[float] = None
    base_recovery_reason: Optional[str] = "NOT_YET_IMPLEMENTED"
    baseline_depth_m: Optional[float] = None
    baseline_depth_reason: Optional[str] = "NOT_YET_IMPLEMENTED"
    lateral_displacement_m: Optional[float] = None
    lateral_displacement_reason: Optional[str] = "NOT_YET_IMPLEMENTED"


class MovementMetrics(BaseModel):
    total_distance_m: Optional[float] = None
    total_distance_reason: Optional[str] = "NOT_YET_IMPLEMENTED"
    average_speed_m_s: Optional[float] = None
    max_speed_m_s: Optional[float] = None
    speed_reason: Optional[str] = "NOT_YET_IMPLEMENTED"
    coverage_percentage: Optional[float] = None
    region_occupancies: List[RegionOccupancy] = Field(default_factory=list)
    region_occupancy_breakdown: Optional[Dict[str, Any]] = None
    region_occupancy_reason: Optional[str] = "NOT_YET_IMPLEMENTED"
    split_step_count: Optional[int] = None
    split_step_reason: Optional[str] = "NOT_YET_IMPLEMENTED"
    lunge_count: Optional[int] = None
    lunge_reason: Optional[str] = "NOT_YET_IMPLEMENTED"
    change_of_direction_count: Optional[int] = None
    change_of_direction_reason: Optional[str] = "NOT_YET_IMPLEMENTED"
    acceleration_burst_count: Optional[int] = None
    acceleration_burst_reason: Optional[str] = "NOT_YET_IMPLEMENTED"


class SpeedMetrics(BaseModel):
    racket_speed_peak: Metric = Field(
        default_factory=lambda: Metric(
            name="racket_speed_peak",
            unit="km/h",
            available=False,
            unavailable_reason="NOT_RELIABLY_MEASURABLE: No object detector available in v1"
        )
    )
    racket_speed_mean: Metric = Field(
        default_factory=lambda: Metric(
            name="racket_speed_mean",
            unit="km/h",
            available=False,
            unavailable_reason="NOT_RELIABLY_MEASURABLE: No object detector available in v1"
        )
    )
    shuttle_speed_peak: Metric = Field(
        default_factory=lambda: Metric(
            name="shuttle_speed_peak",
            unit="km/h",
            available=False,
            unavailable_reason="NOT_RELIABLY_MEASURABLE: No object detector available in v1"
        )
    )
    shuttle_speed_mean: Metric = Field(
        default_factory=lambda: Metric(
            name="shuttle_speed_mean",
            unit="km/h",
            available=False,
            unavailable_reason="NOT_RELIABLY_MEASURABLE: No object detector available in v1"
        )
    )
    wrist_speed_peak: Metric = Field(
        default_factory=lambda: Metric(
            name="wrist_speed_peak",
            unit="km/h",
            available=False,
            unavailable_reason="Pending wrist tracking evaluation"
        )
    )
    racket_uncertainty_range_km_h: Optional[List[float]] = None
    shuttle_uncertainty_range_km_h: Optional[List[float]] = None
    racket_segments_used: int = 0
    shuttle_segments_used: int = 0


class EnergyMetrics(BaseModel):
    estimated_energy_expenditure_kcal: Optional[float] = None
    estimated_range_kcal: Optional[List[float]] = None
    estimation_type: str = "population_average_generalized"  # "personalized" or "population_average_generalized"
    inputs_used: List[str] = Field(default_factory=list)
    calculation_method: str = "Ainsworth et al. (2011) Compendium of Physical Activities MET Equation"
    met_value: Optional[float] = None
    confidence: str = "LOW"
    limitations: List[str] = Field(default_factory=list)
    intensity_score: Optional[float] = None
    energy_expenditure_reason: Optional[str] = None
    metabolic_equivalent_of_task: Optional[float] = None
    metabolic_equivalent_reason: Optional[str] = None
    intensity_reason: Optional[str] = None
    available: bool = True


class PoseMetrics(BaseModel):
    kinetic_chain_sequence_score: Optional[float] = None
    kinetic_chain_reason: Optional[str] = "NOT_YET_IMPLEMENTED"
    shoulder_internal_rotation_deg: Optional[float] = None
    shoulder_rotation_reason: Optional[str] = "NOT_YET_IMPLEMENTED"
    elbow_extension_deg: Optional[float] = None
    elbow_extension_reason: Optional[str] = "NOT_YET_IMPLEMENTED"
    wrist_pronation_deg: Optional[float] = None
    wrist_pronation_reason: Optional[str] = "NOT_YET_IMPLEMENTED"
    trunk_rotation_deg: Optional[float] = None
    trunk_rotation_reason: Optional[str] = "NOT_YET_IMPLEMENTED"


class ShotMetrics(BaseModel):
    total_shots: int = 0
    duration_definition: str = "end_timestamp - contact_timestamp per Section 17"
    shot_durations_s: List[float] = Field(default_factory=list)
    average_duration_s: Optional[float] = None
    median_duration_s: Optional[float] = None
    min_duration_s: Optional[float] = None
    max_duration_s: Optional[float] = None
    count_by_shot_type: Dict[str, int] = Field(default_factory=dict)
    percentage_by_shot_type: Dict[str, float] = Field(default_factory=dict)
    placement_metrics: Dict[str, Any] = Field(default_factory=dict)
    recovery_metrics: Dict[str, Any] = Field(default_factory=dict)
    movement_efficiency: Metric = Field(
        default_factory=lambda: Metric(
            name="movement_efficiency",
            unit="retrievals/meter",
            available=False,
            unavailable_reason="NOT_RELIABLY_MEASURABLE: Rally boundary and shot outcome (successful retrieval vs winner/error) not determinable from single-player recording."
        )
    )


class BadmintonAnalysisResult(BaseModel):
    analysis_id: str
    video_id: Optional[str] = None
    player_id: Optional[str] = None
    video: VideoMetadata
    quality: QualityAssessment
    player_metadata: Optional[PlayerMetadata] = None
    shots: List[ShotResult] = Field(default_factory=list)
    shot_metrics: Optional[ShotMetrics] = None
    court_metrics: Optional[CourtMetrics] = None
    movement_metrics: Optional[MovementMetrics] = None
    speed_metrics: Optional[SpeedMetrics] = None
    energy_metrics: Optional[EnergyMetrics] = None
    pose_metrics: Optional[PoseMetrics] = None
    court_calibration: Optional[CourtCalibration] = None
    pose_frames: Optional[List[PoseFrame]] = Field(default_factory=list)
    findings: List[str] = Field(default_factory=list)
    hypotheses: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    prioritized_recommendations: List[Any] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    rejection_reason: Optional[str] = None
    status: BadmintonAnalysisStatus = BadmintonAnalysisStatus.NOT_YET_IMPLEMENTED
    graph_data: Optional[GraphStateModel] = None
    enhancement: Optional[EnhancementMetadata] = None
    kinematic_supervision: Optional[Dict[str, Any]] = None

    @property
    def graph(self) -> Optional[GraphStateModel]:
        """Convenience alias for knowledge graph consumers."""
        return self.graph_data

    @property
    def final_graph(self) -> Optional[GraphStateModel]:
        """Convenience alias matching standard SAAR InvestigationResponse schema."""
        return self.graph_data


class MetricTrend(BaseModel):
    """
    Longitudinal progression of a single metric across sessions.
    Maintains strict availability and honest-gap tracking.
    """
    metric_name: str
    values: List[Optional[float]] = Field(default_factory=list)
    sessions: List[str] = Field(default_factory=list)
    slope: Optional[float] = None
    r_squared: Optional[float] = None
    change_percentage: Optional[float] = None
    direction: str = "STABLE"  # INCREASING, DECREASING, STABLE, FLUCTUATING, INSUFFICIENT, UNAVAILABLE
    session_deltas: List[float] = Field(default_factory=list)
    available: bool = True
    unavailable_reason: Optional[str] = None


class LongitudinalCorrelation(BaseModel):
    """
    Deterministic correlation between two metrics across longitudinal sessions.
    Strictly correlation-appropriate, non-causal descriptions.
    """
    feature_a: str
    feature_b: str
    pearson_r: Optional[float] = None
    spearman_rho: Optional[float] = None
    observation_count: int = 0
    description: str = ""


class BadmintonLongitudinalComparison(BaseModel):
    """
    Master longitudinal comparison across multiple sessions for the same player_id.
    Adheres strictly to Phase 17:
    1. Reuses AnalyticsService & SportsPlugin correlation architecture.
    2. Deterministic trend slope, correlation, change percentage, and session-to-session delta.
    3. Epistemic non-causal discipline (no causal claims from correlation).
    """
    player_id: str
    session_count: int
    session_ids: List[str] = Field(default_factory=list)
    session_dates: List[Optional[str]] = Field(default_factory=list)
    metric_trends: Dict[str, MetricTrend] = Field(default_factory=dict)
    correlations: List[LongitudinalCorrelation] = Field(default_factory=list)
    hedged_summary: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    graph_data: Optional[GraphStateModel] = None
