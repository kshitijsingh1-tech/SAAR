"""
Badminton athletic video analysis package.
Establishes schemas, pipeline scaffolding, and quality gating.
"""
from .schemas import (
    BadmintonAnalysisResult,
    BadmintonAnalysisStatus,
    VideoMetadata,
    QualityAssessment,
    CaptureConfidence,
    Metric,
    ShotResult,
    CourtMetrics,
    MovementMetrics,
    SpeedMetrics,
    EnergyMetrics,
    PoseMetrics,
    PlayerMetadata,
    BadmintonFrame,
    Landmark,
    PoseFrame,
    CourtCalibration,
    RegionOccupancy,
    ShotMetrics
)
from .pipeline import BadmintonPipeline
from .pose_estimator import BadmintonPoseEstimator
from .court_detector import BadmintonCourtDetector
from .movement_analyzer import BadmintonMovementAnalyzer
from .racket_tracker import BadmintonRacketTracker, RacketTrackingSummary, RacketFrameRecord
from .shuttle_tracker import BadmintonShuttleTracker, ShuttleTrackingSummary, ShuttleFrameRecord
from .shot_detector import BadmintonShotDetector, CandidateContactEvent
from .shot_classifier import BadmintonShotClassifier, CLASSIFICATION_CONFIDENCE_THRESHOLD
from .metrics import BadmintonMetricsEngine, MIN_PLACEMENT_SAMPLE_SIZE
from .speed_analyzer import (
    BadmintonSpeedAnalyzer,
    FALLBACK_UNAVAILABLE_MESSAGE,
    SHUTTLE_MAX_SPEED_KM_H,
    RACKET_MAX_SPEED_KM_H,
    SpeedSegment
)
from .calorie_estimator import (
    BadmintonCalorieEstimator,
    STANDARD_REFERENCE_WEIGHT_KG,
    CALCULATION_METHOD_CITATION
)
from .kinematics import BadmintonKinematicsAnalyzer
from .evidence import (
    BadmintonEvidenceGraphBuilder,
    Section25NodeType,
    NodeCategory
)
from .recommendations import (
    RecommendationPriority,
    PrioritizedRecommendation,
    BadmintonRecommendationEngine,
    DEFICIENCY_RED_FLAG_PHRASES
)

__all__ = [
    "BadmintonAnalysisResult",
    "BadmintonAnalysisStatus",
    "VideoMetadata",
    "QualityAssessment",
    "CaptureConfidence",
    "Metric",
    "ShotResult",
    "ShotMetrics",
    "CourtMetrics",
    "MovementMetrics",
    "SpeedMetrics",
    "EnergyMetrics",
    "PoseMetrics",
    "PlayerMetadata",
    "BadmintonFrame",
    "Landmark",
    "PoseFrame",
    "CourtCalibration",
    "RegionOccupancy",
    "BadmintonPipeline",
    "BadmintonPoseEstimator",
    "BadmintonCourtDetector",
    "BadmintonMovementAnalyzer",
    "BadmintonRacketTracker",
    "RacketTrackingSummary",
    "RacketFrameRecord",
    "BadmintonShuttleTracker",
    "ShuttleTrackingSummary",
    "ShuttleFrameRecord",
    "BadmintonShotDetector",
    "CandidateContactEvent",
    "BadmintonShotClassifier",
    "CLASSIFICATION_CONFIDENCE_THRESHOLD",
    "BadmintonMetricsEngine",
    "MIN_PLACEMENT_SAMPLE_SIZE",
    "BadmintonSpeedAnalyzer",
    "FALLBACK_UNAVAILABLE_MESSAGE",
    "SHUTTLE_MAX_SPEED_KM_H",
    "RACKET_MAX_SPEED_KM_H",
    "SpeedSegment",
    "BadmintonCalorieEstimator",
    "STANDARD_REFERENCE_WEIGHT_KG",
    "CALCULATION_METHOD_CITATION",
    "BadmintonKinematicsAnalyzer",
    "BadmintonEvidenceGraphBuilder",
    "Section25NodeType",
    "NodeCategory",
    "RecommendationPriority",
    "PrioritizedRecommendation",
    "BadmintonRecommendationEngine",
    "DEFICIENCY_RED_FLAG_PHRASES"
]
