"""
Spatial metrics computation with strict scale calibration gating and direction-invariant foot progression.

Calibration Policy:
- Physical units (meters, m/s) are strictly NOT computed from raw 2D pixel coordinates.
- If pixels_per_meter is None or <= 0, physical metrics return None with status="unavailable"
  and explicit calibration reason.
- Foot progression angle is a geometric angular measurement relative to forward progression
  vector, computable without metric scale.
"""
import math
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from ..schemas import PoseFrame, GaitEvent, Side
from ..pose.landmarks import (
    left_hip, right_hip, left_ankle, right_ankle,
    left_heel, right_heel, left_foot_index, right_foot_index
)

MIN_FOOT_VISIBILITY = 0.30
EPSILON = 1e-7


@dataclass
class FootProgressionResult:
    mean_progression_angle_deg: Optional[float]
    left_progression_angle_deg: Optional[float]
    right_progression_angle_deg: Optional[float]
    walking_direction: str  # "left_to_right", "right_to_left", or "unknown"
    confidence: float


@dataclass
class SpatialMetricsResult:
    is_calibrated: bool
    calibration_source: Optional[str]
    uncalibrated_reason: Optional[str]
    step_length_m: Optional[float]
    stride_length_m: Optional[float]
    walking_speed_m_per_s: Optional[float]
    distance_m: Optional[float]
    step_length_asymmetry_pct: Optional[float]
    foot_progression: FootProgressionResult


def determine_walking_direction(frames: List[PoseFrame]) -> Tuple[float, float, str]:
    """
    Estimates global horizontal walking direction vector (dx, dy) and label
    from net pelvis midpoint displacement across valid frames.
    """
    valid_mid_hips: List[Tuple[float, float]] = []
    for f in frames:
        lh = left_hip(f)
        rh = right_hip(f)
        if lh.visibility >= 0.25 and rh.visibility >= 0.25:
            valid_mid_hips.append(((lh.x + rh.x) / 2.0, (lh.y + rh.y) / 2.0))

    if len(valid_mid_hips) < 2:
        return (1.0, 0.0, "unknown")

    # Sample first quarter vs last quarter for robust displacement vector
    n = len(valid_mid_hips)
    q1 = valid_mid_hips[:max(1, n // 4)]
    q4 = valid_mid_hips[max(1, (3 * n) // 4):]

    start_x = sum(p[0] for p in q1) / len(q1)
    start_y = sum(p[1] for p in q1) / len(q1)
    end_x = sum(p[0] for p in q4) / len(q4)
    end_y = sum(p[1] for p in q4) / len(q4)

    dx = end_x - start_x
    dy = end_y - start_y
    mag = math.hypot(dx, dy)

    if mag < EPSILON:
        return (1.0, 0.0, "unknown")

    norm_dx = dx / mag
    norm_dy = dy / mag
    label = "left_to_right" if norm_dx >= 0 else "right_to_left"

    return (norm_dx, norm_dy, label)


def compute_foot_progression_angle(
    frames: List[PoseFrame],
    events: List[GaitEvent]
) -> FootProgressionResult:
    """
    Computes foot progression angle relative to the estimated walking progression vector.
    Works invariantly for both left->right and right->left trajectories.
    """
    dir_x, dir_y, dir_label = determine_walking_direction(frames)
    if dir_label == "unknown" or not events:
        return FootProgressionResult(
            mean_progression_angle_deg=None,
            left_progression_angle_deg=None,
            right_progression_angle_deg=None,
            walking_direction=dir_label,
            confidence=0.0
        )

    left_angles: List[float] = []
    right_angles: List[float] = []

    for ev in events:
        if 0 <= ev.frame_index < len(frames):
            frame = frames[ev.frame_index]
            is_left = ev.side == Side.LEFT
            
            heel = left_heel(frame) if is_left else right_heel(frame)
            ankle = left_ankle(frame) if is_left else right_ankle(frame)
            toe = left_foot_index(frame) if is_left else right_foot_index(frame)

            # Use heel as origin, fallback to ankle
            origin = heel if heel.visibility >= MIN_FOOT_VISIBILITY else ankle
            if origin.visibility >= MIN_FOOT_VISIBILITY and toe.visibility >= MIN_FOOT_VISIBILITY:
                # Foot vector pointing from heel to toe
                fx = toe.x - origin.x
                fy = toe.y - origin.y
                f_mag = math.hypot(fx, fy)
                if f_mag >= EPSILON:
                    # Angle between foot vector and progression vector
                    dot = (fx * dir_x) + (fy * dir_y)
                    cos_theta = dot / f_mag
                    clamped_cos = max(-1.0, min(1.0, cos_theta))
                    ang_deg = math.degrees(math.acos(clamped_cos))

                    if is_left:
                        left_angles.append(ang_deg)
                    else:
                        right_angles.append(ang_deg)

    left_mean = (sum(left_angles) / len(left_angles)) if left_angles else None
    right_mean = (sum(right_angles) / len(right_angles)) if right_angles else None

    all_angles = left_angles + right_angles
    mean_ang = (sum(all_angles) / len(all_angles)) if all_angles else None
    conf = min(1.0, len(all_angles) / max(1.0, len(events)))

    return FootProgressionResult(
        mean_progression_angle_deg=round(mean_ang, 1) if mean_ang is not None else None,
        left_progression_angle_deg=round(left_mean, 1) if left_mean is not None else None,
        right_progression_angle_deg=round(right_mean, 1) if right_mean is not None else None,
        walking_direction=dir_label,
        confidence=round(conf, 3)
    )


def compute_spatial_metrics(
    frames: List[PoseFrame],
    events: List[GaitEvent],
    pixels_per_meter: Optional[float] = None,
    calibration_source: Optional[str] = None
) -> SpatialMetricsResult:
    """
    Computes spatial metrics with explicit calibration gating.
    If no scale calibration is provided, physical spatial metrics are returned as None
    with explicit documentation.
    """
    foot_progression = compute_foot_progression_angle(frames, events)

    # Check scale validity
    if pixels_per_meter is None or pixels_per_meter <= 0.0:
        return SpatialMetricsResult(
            is_calibrated=False,
            calibration_source=None,
            uncalibrated_reason="No scale calibration available in uncalibrated monocular 2D video.",
            step_length_m=None,
            stride_length_m=None,
            walking_speed_m_per_s=None,
            distance_m=None,
            step_length_asymmetry_pct=None,
            foot_progression=foot_progression
        )

    # Calibrated physical computation
    # (Extract consecutive heel positions in pixel units and convert via pixels_per_meter)
    step_lengths_m: List[float] = []
    left_step_lengths_m: List[float] = []
    right_step_lengths_m: List[float] = []

    sorted_events = sorted(events, key=lambda e: e.frame_index)
    for ev1, ev2 in zip(sorted_events[:-1], sorted_events[1:]):
        if 0 <= ev1.frame_index < len(frames) and 0 <= ev2.frame_index < len(frames):
            f1 = frames[ev1.frame_index]
            f2 = frames[ev2.frame_index]
            
            p1_heel = left_heel(f1) if ev1.side == Side.LEFT else right_heel(f1)
            p2_heel = left_heel(f2) if ev2.side == Side.LEFT else right_heel(f2)

            dist_px = math.hypot(p2_heel.x - p1_heel.x, p2_heel.y - p1_heel.y)
            dist_m = dist_px / pixels_per_meter

            if 0.10 <= dist_m <= 1.50:  # Physiologic step length bounds for toddler/pediatric
                step_lengths_m.append(dist_m)
                if ev2.side == Side.LEFT:
                    left_step_lengths_m.append(dist_m)
                else:
                    right_step_lengths_m.append(dist_m)

    mean_step_len = (sum(step_lengths_m) / len(step_lengths_m)) if step_lengths_m else None
    stride_len_m = (2.0 * mean_step_len) if mean_step_len else None
    
    total_dist_m = sum(step_lengths_m) if step_lengths_m else None
    
    duration_sec = 0.0
    if len(sorted_events) >= 2:
        duration_sec = sorted_events[-1].time_seconds - sorted_events[0].time_seconds

    speed_m_s = (total_dist_m / duration_sec) if (total_dist_m and duration_sec > 0.1) else None

    # Step length asymmetry
    step_len_asym: Optional[float] = None
    if left_step_lengths_m and right_step_lengths_m:
        l_mean = sum(left_step_lengths_m) / len(left_step_lengths_m)
        r_mean = sum(right_step_lengths_m) / len(right_step_lengths_m)
        denom = 0.5 * (l_mean + r_mean) + EPSILON
        step_len_asym = round((100.0 * abs(l_mean - r_mean)) / denom, 2)

    return SpatialMetricsResult(
        is_calibrated=True,
        calibration_source=calibration_source or "User Supplied Reference",
        uncalibrated_reason=None,
        step_length_m=round(mean_step_len, 3) if mean_step_len else None,
        stride_length_m=round(stride_len_m, 3) if stride_len_m else None,
        walking_speed_m_per_s=round(speed_m_s, 3) if speed_m_s else None,
        distance_m=round(total_dist_m, 3) if total_dist_m else None,
        step_length_asymmetry_pct=step_len_asym,
        foot_progression=foot_progression
    )
