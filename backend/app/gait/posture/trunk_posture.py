"""
Trunk alignment and posture kinematics analysis.

Mathematical Definitions:
- Mid-Hip Landmark:     P_hip = ( (L_HIP.x + R_HIP.x)/2, (L_HIP.y + R_HIP.y)/2 )
- Mid-Shoulder Landmark: P_shoulder = ( (L_SHOULDER.x + R_SHOULDER.x)/2, (L_SHOULDER.y + R_SHOULDER.y)/2 )
- Torso Vector:         T = P_shoulder - P_hip = (Tx, Ty)
- Upward Vertical Ref:  V = (0.0, -1.0) in standard image coordinates (Y increases downwards)
- Trunk Inclination:    angle = acos( clamp( (T . V) / (|T| * |V| + eps), -1.0, 1.0 ) ) * (180 / pi)
"""
import math
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from ..schemas import PoseFrame, Landmark
from ..pose.landmarks import left_shoulder, right_shoulder, left_hip, right_hip
from ..events.smoothing import interpolate_nans, savgol_smooth

MIN_TORSO_VISIBILITY = 0.30
EPSILON = 1e-7


@dataclass
class TrunkPostureResult:
    mean_trunk_angle_deg: Optional[float]
    median_trunk_angle_deg: Optional[float]
    trunk_variability_deg: Optional[float]
    lateral_sway_norm: Optional[float]
    raw_angles: List[Optional[float]]
    smoothed_angles: List[Optional[float]]
    valid_frames: int
    confidence: float


def analyze_trunk_posture(
    frames: List[PoseFrame],
    fps: float = 30.0
) -> TrunkPostureResult:
    """
    Computes trunk inclination relative to vertical, angular variability,
    and normalized lateral trunk sway.
    """
    if not frames:
        return TrunkPostureResult(
            mean_trunk_angle_deg=None,
            median_trunk_angle_deg=None,
            trunk_variability_deg=None,
            lateral_sway_norm=None,
            raw_angles=[],
            smoothed_angles=[],
            valid_frames=0,
            confidence=0.0
        )

    raw_angles: List[Optional[float]] = []
    lateral_displacements: List[float] = []

    for frame in frames:
        l_sh = left_shoulder(frame)
        r_sh = right_shoulder(frame)
        l_hp = left_hip(frame)
        r_hp = right_hip(frame)

        # Ensure all 4 torso boundary landmarks are sufficiently visible
        if (l_sh.visibility < MIN_TORSO_VISIBILITY or
            r_sh.visibility < MIN_TORSO_VISIBILITY or
            l_hp.visibility < MIN_TORSO_VISIBILITY or
            r_hp.visibility < MIN_TORSO_VISIBILITY):
            raw_angles.append(None)
            continue

        mid_hip_x = (l_hp.x + r_hp.x) / 2.0
        mid_hip_y = (l_hp.y + r_hp.y) / 2.0

        mid_sh_x = (l_sh.x + r_sh.x) / 2.0
        mid_sh_y = (l_sh.y + r_sh.y) / 2.0

        # Torso vector T pointing upward from hip to shoulder
        t_x = mid_sh_x - mid_hip_x
        t_y = mid_sh_y - mid_hip_y
        torso_len = math.hypot(t_x, t_y)

        if torso_len < EPSILON:
            raw_angles.append(None)
            continue

        # Vertical reference vector V = (0.0, -1.0)
        # Dot product (T . V) = (t_x * 0) + (t_y * -1.0) = -t_y
        dot_v = -t_y
        cos_theta = dot_v / torso_len
        clamped_cos = max(-1.0, min(1.0, cos_theta))
        ang_deg = math.degrees(math.acos(clamped_cos))

        raw_angles.append(float(round(ang_deg, 2)))
        # Lateral displacement of torso relative to hip center, normalized by torso length
        lateral_displacements.append(abs(t_x) / torso_len)

    # Temporal smoothing
    float_series = [v if v is not None else float("nan") for v in raw_angles]
    interpolated = interpolate_nans(float_series, max_gap=4)
    smoothed_floats = savgol_smooth(interpolated, fps=fps)

    smoothed_angles: List[Optional[float]] = []
    for s in smoothed_floats:
        if s is None or math.isnan(s):
            smoothed_angles.append(None)
        else:
            smoothed_angles.append(float(round(s, 2)))

    valid_vals = [a for a in smoothed_angles if a is not None]
    if len(valid_vals) < 5:
        return TrunkPostureResult(
            mean_trunk_angle_deg=None,
            median_trunk_angle_deg=None,
            trunk_variability_deg=None,
            lateral_sway_norm=None,
            raw_angles=raw_angles,
            smoothed_angles=smoothed_angles,
            valid_frames=len(valid_vals),
            confidence=0.0
        )

    # Statistical metrics
    mean_ang = float(sum(valid_vals) / len(valid_vals))
    sorted_vals = sorted(valid_vals)
    mid_idx = len(sorted_vals) // 2
    median_ang = float(sorted_vals[mid_idx]) if len(sorted_vals) % 2 == 1 else float((sorted_vals[mid_idx - 1] + sorted_vals[mid_idx]) / 2.0)

    # Standard deviation
    variance = sum((v - mean_ang) ** 2 for v in valid_vals) / len(valid_vals)
    std_dev = float(math.sqrt(variance))

    # Mean lateral sway ratio
    mean_sway = float(sum(lateral_displacements) / len(lateral_displacements)) if lateral_displacements else 0.0

    conf = min(1.0, len(valid_vals) / max(1.0, len(frames)))

    return TrunkPostureResult(
        mean_trunk_angle_deg=round(mean_ang, 1),
        median_trunk_angle_deg=round(median_ang, 1),
        trunk_variability_deg=round(std_dev, 2),
        lateral_sway_norm=round(mean_sway, 3),
        raw_angles=raw_angles,
        smoothed_angles=smoothed_angles,
        valid_frames=len(valid_vals),
        confidence=round(conf, 3)
    )
