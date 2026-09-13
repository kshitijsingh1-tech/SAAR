"""
Spatial kinematics and calibration gating package.
"""
from .spatial_metrics import (
    compute_spatial_metrics,
    SpatialMetricsResult,
    FootProgressionResult
)

__all__ = [
    "compute_spatial_metrics",
    "SpatialMetricsResult",
    "FootProgressionResult"
]
