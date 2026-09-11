"""
Heel-strike detection and gait-event extraction ported from ToddleAI GaitEventDetector.
"""
import math
from typing import List, Tuple
from ..schemas import PoseFrame, GaitEvent, Side
from ..pose.landmarks import left_hip, right_hip, heel_for_side
from .smoothing import estimate_direction_sign, interpolate_nans, moving_average

MIN_HEEL_VISIBILITY = 0.5
MIN_PROMINENCE_RATIO = 0.15
MIN_STEP_TIME_SECONDS = 0.25
MAX_STEP_TIME_SECONDS = 1.5


def find_peaks(signal: List[float], min_distance: int, min_prominence: float) -> List[int]:
    """Finds local maxima peaks with minimum distance and prominence constraints."""
    n = len(signal)
    if n < 3:
        return []

    candidates: List[Tuple[int, float]] = []

    for i in range(1, n - 1):
        curr = signal[i]
        if math.isnan(curr):
            continue

        prev_v = signal[i - 1]
        next_v = signal[i + 1]
        if math.isnan(prev_v) or math.isnan(next_v):
            continue

        is_local_max = (curr > prev_v) and (curr >= next_v)
        if not is_local_max:
            continue

        left_slice = [v for v in signal[:i] if not math.isnan(v)]
        right_slice = [v for v in signal[i:] if not math.isnan(v)]
        if not left_slice or not right_slice:
            continue

        left_min = min(left_slice)
        right_min = min(right_slice)
        prominence = curr - max(left_min, right_min)

        if prominence >= min_prominence:
            candidates.append((i, curr))

    # Greedy non-maximum suppression by distance
    candidates.sort(key=lambda c: c[1], reverse=True)
    selected: List[int] = []

    for idx, val in candidates:
        if not any(abs(idx - s) < min_distance for s in selected):
            selected.append(idx)

    selected.sort()
    return selected


def detect_side_events(
    frames: List[PoseFrame],
    fps: float,
    side: Side,
    min_peak_distance: int,
    direction: float
) -> List[GaitEvent]:
    """Detects heel-strike gait events for one side (LEFT or RIGHT)."""
    n = len(frames)
    raw_signal: List[float] = [float("nan")] * n

    for i, frame in enumerate(frames):
        heel = heel_for_side(frame, side)
        if heel.visibility < MIN_HEEL_VISIBILITY:
            raw_signal[i] = float("nan")
        else:
            sacrum_x = (left_hip(frame).x + right_hip(frame).x) / 2.0
            raw_signal[i] = float(direction * (heel.x - sacrum_x))

    interpolated = interpolate_nans(raw_signal)
    smoothed = moving_average(interpolated)

    events: List[GaitEvent] = []
    seg_start = 0

    while seg_start < n:
        while seg_start < n and math.isnan(smoothed[seg_start]):
            seg_start += 1
        if seg_start >= n:
            break

        seg_end = seg_start
        while seg_end < n and not math.isnan(smoothed[seg_end]):
            seg_end += 1

        segment = smoothed[seg_start:seg_end]
        if len(segment) >= 3:
            amplitude = max(segment) - min(segment)
            min_prom = amplitude * MIN_PROMINENCE_RATIO
            if min_prom > 0.0:
                peaks = find_peaks(segment, min_distance=min_peak_distance, min_prominence=min_prom)
                for p in peaks:
                    f_idx = seg_start + p
                    frame = frames[f_idx]
                    heel = heel_for_side(frame, side)
                    events.append(GaitEvent(
                        frame_index=frame.frame_index,
                        time_seconds=float(frame.timestamp_ms / 1000.0),
                        side=side,
                        confidence=float(heel.visibility)
                    ))

        seg_start = seg_end

    return events


def filter_physiologic_step_times(events: List[GaitEvent]) -> List[GaitEvent]:
    """Filters out events that occur faster than 0.25s or slower than 1.5s."""
    if len(events) < 2:
        return events

    filtered = [events[0]]
    for ev in events[1:]:
        last_ev = filtered[-1]
        delta = ev.time_seconds - last_ev.time_seconds
        if MIN_STEP_TIME_SECONDS <= delta <= MAX_STEP_TIME_SECONDS:
            filtered.append(ev)

    return filtered


def detect_gait_events(frames: List[PoseFrame], fps: float) -> List[GaitEvent]:
    """Full temporal gait event detection across left and right lower extremities."""
    if not frames or fps <= 0.0:
        return []

    direction = estimate_direction_sign(frames)
    min_peak_distance = max(1, math.ceil(0.3 * fps))

    left_events = detect_side_events(frames, fps, Side.LEFT, min_peak_distance, direction)
    right_events = detect_side_events(frames, fps, Side.RIGHT, min_peak_distance, direction)

    combined = left_events + right_events
    combined.sort(key=lambda e: e.frame_index)

    return filter_physiologic_step_times(combined)
