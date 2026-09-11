"""
Signal smoothing and temporal processing utilities ported from ToddleAI GaitEventDetector.
"""
import math
import numpy as np
from typing import List, Optional
from ..schemas import PoseFrame
from ..pose.landmarks import left_hip, right_hip

MIN_HIP_VISIBILITY = 0.5
MAX_INTERPOLATION_GAP = 5
MOVING_AVERAGE_WINDOW = 5


def estimate_direction_sign(frames: List[PoseFrame]) -> float:
    """Estimates walking direction sign (+1.0 for rightwards, -1.0 for leftwards)
    based on the robust median displacement of the hip center."""
    deltas: List[float] = []
    prev_hip_x: Optional[float] = None

    for frame in frames:
        l_hip = left_hip(frame)
        r_hip = right_hip(frame)
        if l_hip.visibility < MIN_HIP_VISIBILITY or r_hip.visibility < MIN_HIP_VISIBILITY:
            prev_hip_x = None
            continue

        hip_center_x = (l_hip.x + r_hip.x) / 2.0
        if prev_hip_x is not None:
            deltas.append(hip_center_x - prev_hip_x)
        prev_hip_x = hip_center_x

    if not deltas:
        return 1.0

    deltas.sort()
    median_delta = deltas[len(deltas) // 2]
    return -1.0 if median_delta < 0.0 else 1.0


def interpolate_nans(signal: List[float], max_gap: int = MAX_INTERPOLATION_GAP) -> List[float]:
    """Linearly interpolates NaN gaps of length <= max_gap."""
    result = list(signal)
    n = len(result)
    idx = 0

    while idx < n:
        if not math.isnan(result[idx]):
            idx += 1
            continue

        gap_start = idx
        while idx < n and math.isnan(result[idx]):
            idx += 1
        gap_end = idx - 1
        gap_len = gap_end - gap_start + 1

        left_idx = gap_start - 1
        right_idx = idx

        can_interpolate = (
            gap_len <= max_gap
            and left_idx >= 0
            and right_idx < n
            and not math.isnan(result[left_idx])
            and not math.isnan(result[right_idx])
        )

        if can_interpolate:
            left_val = result[left_idx]
            right_val = result[right_idx]
            for g_idx in range(gap_start, gap_end + 1):
                ratio = float(g_idx - left_idx) / float(right_idx - left_idx)
                result[g_idx] = left_val + ((right_val - left_val) * ratio)

    return result


def moving_average(signal: List[float], window: int = MOVING_AVERAGE_WINDOW) -> List[float]:
    """Computes moving average over non-NaN values."""
    radius = window // 2
    n = len(signal)
    smoothed = [float("nan")] * n

    for i in range(n):
        if math.isnan(signal[i]):
            continue
        start = max(0, i - radius)
        end = min(n, i + radius + 1)
        valid_vals = [signal[j] for j in range(start, end) if not math.isnan(signal[j])]
        if valid_vals:
            smoothed[i] = sum(valid_vals) / len(valid_vals)

    return smoothed
