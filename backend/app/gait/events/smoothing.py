"""
Signal smoothing and temporal processing utilities for gait event detection.

Upgraded from simple moving average to Savitzky-Golay filter for zero phase-lag
smoothing that preserves peak shape and timing accuracy.
"""
import math
import numpy as np
from typing import List, Optional
from ..schemas import PoseFrame
from ..pose.landmarks import left_hip, right_hip

MIN_HIP_VISIBILITY = 0.3  # Lowered from 0.5 to accept more frames for direction estimation
MAX_INTERPOLATION_GAP = 14  # Increased to 14 to bridge longer toddler occlusion/cross-over gaps
MOVING_AVERAGE_WINDOW = 5

# Savitzky-Golay defaults
DEFAULT_SAVGOL_POLYORDER = 2
MIN_SAVGOL_WINDOW = 5
MAX_SAVGOL_WINDOW = 15

# Check scipy availability at import time
try:
    from scipy.signal import savgol_filter as _scipy_savgol
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


def adaptive_savgol_window(fps: float) -> int:
    """Computes an adaptive Savitzky-Golay window length based on video FPS.
    
    The window should be roughly 0.23s of video, ensuring it captures
    enough of the heel-strike cycle without over-smoothing.
    Must be odd and >= MIN_SAVGOL_WINDOW.
    """
    raw_window = max(MIN_SAVGOL_WINDOW, int(fps * 0.23))
    # Ensure odd
    if raw_window % 2 == 0:
        raw_window += 1
    return min(raw_window, MAX_SAVGOL_WINDOW)


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
    """Computes moving average over non-NaN values. Kept as fallback."""
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


def savgol_smooth(signal: List[float], fps: float = 30.0) -> List[float]:
    """Applies Savitzky-Golay smoothing with adaptive window sizing.
    
    Savitzky-Golay advantages over moving average:
    - Zero phase lag (preserves peak timing)
    - Better peak shape preservation (polynomial fit vs. box filter)
    - Adaptive to video frame rate
    
    Falls back to moving_average if scipy is not available.
    """
    n = len(signal)
    if n < MIN_SAVGOL_WINDOW:
        return list(signal)

    if not HAS_SCIPY:
        return moving_average(signal, window=MOVING_AVERAGE_WINDOW)

    window_length = adaptive_savgol_window(fps)
    # Ensure window doesn't exceed signal length
    if window_length > n:
        window_length = n if n % 2 == 1 else n - 1
    if window_length < MIN_SAVGOL_WINDOW:
        return moving_average(signal, window=MOVING_AVERAGE_WINDOW)

    # Build a numpy array, marking NaNs
    arr = np.array(signal, dtype=np.float64)
    nan_mask = np.isnan(arr)

    # If all NaN or too few valid points, return as-is
    valid_count = int(np.sum(~nan_mask))
    if valid_count < window_length:
        return moving_average(signal, window=MOVING_AVERAGE_WINDOW)

    # Fill NaNs temporarily with linear interpolation for filter continuity
    if np.any(nan_mask):
        valid_indices = np.where(~nan_mask)[0]
        valid_values = arr[valid_indices]
        all_indices = np.arange(n)
        arr_filled = np.interp(all_indices, valid_indices, valid_values)
    else:
        arr_filled = arr.copy()

    # Apply Savitzky-Golay filter
    smoothed_arr = _scipy_savgol(arr_filled, window_length, DEFAULT_SAVGOL_POLYORDER)

    # Restore original NaN positions
    result = smoothed_arr.tolist()
    for i in range(n):
        if nan_mask[i]:
            result[i] = float("nan")

    return result
