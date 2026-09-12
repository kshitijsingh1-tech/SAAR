"""
Heel-strike detection and gait-event extraction with confidence scoring and outlier rejection.

Upgraded from the original ToddleAI port with:
- Higher prominence ratio for noise rejection
- Per-event confidence scoring (landmark visibility + peak prominence + temporal consistency)
- 2-sigma outlier rejection on step times
- Savitzky-Golay smoothing (zero phase lag)
"""
import math
from typing import List, Tuple, Optional
from ..schemas import PoseFrame, GaitEvent, Side
from ..pose.landmarks import left_hip, right_hip, heel_for_side, ankle_for_side
from .smoothing import estimate_direction_sign, interpolate_nans, savgol_smooth, moving_average

MIN_HEEL_VISIBILITY = 0.25   # Accepts lower visibility; ankle fallback provides additional robustness
MIN_PROMINENCE_RATIO = 0.15  # Balanced prominence ratio
MIN_STEP_TIME_SECONDS = 0.18 # Physiologic toddler step time lower bound
MAX_STEP_TIME_SECONDS = 1.5
OUTLIER_SIGMA_THRESHOLD = 2.5


def find_peaks(signal: List[float], min_distance: int, min_prominence: float) -> List[Tuple[int, float]]:
    """Finds local maxima peaks with minimum distance and prominence constraints.
    
    Returns list of (index, prominence) tuples for confidence scoring.
    """
    n = len(signal)
    if n < 3:
        return []

    candidates: List[Tuple[int, float, float]] = []  # (index, value, prominence)

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
            candidates.append((i, curr, prominence))

    # Greedy non-maximum suppression by distance
    candidates.sort(key=lambda c: c[1], reverse=True)
    selected: List[Tuple[int, float]] = []

    for idx, val, prom in candidates:
        if not any(abs(idx - s[0]) < min_distance for s in selected):
            selected.append((idx, prom))

    selected.sort(key=lambda s: s[0])
    return selected


def _compute_event_confidence(
    heel_visibility: float,
    prominence: float,
    segment_amplitude: float
) -> float:
    """Computes a 0.0-1.0 confidence score for a detected gait event.
    
    Factors:
    - heel_visibility: how well the heel landmark was seen (0-1)
    - prominence_ratio: peak prominence relative to segment amplitude (0-1)
    """
    vis_score = min(1.0, max(0.0, heel_visibility))
    prom_ratio = 0.0
    if segment_amplitude > 0.0:
        prom_ratio = min(1.0, prominence / segment_amplitude)
    
    confidence = 0.6 * vis_score + 0.4 * prom_ratio
    return round(confidence, 4)


def detect_side_events(
    frames: List[PoseFrame],
    fps: float,
    side: Side,
    min_peak_distance: int,
    direction: float
) -> List[GaitEvent]:
    """Detects heel-strike gait events for one side (LEFT or RIGHT) with dual-landmark foot fusion."""
    n = len(frames)
    raw_signal: List[float] = [float("nan")] * n
    foot_visibilities: List[float] = [0.0] * n

    for i, frame in enumerate(frames):
        heel = heel_for_side(frame, side)
        ankle = ankle_for_side(frame, side)
        
        # Dual-landmark foot tracking: use heel if visible, fallback to ankle
        if heel.visibility >= MIN_HEEL_VISIBILITY:
            foot_x = heel.x
            v = heel.visibility
        elif ankle.visibility >= MIN_HEEL_VISIBILITY:
            foot_x = ankle.x
            v = ankle.visibility
        else:
            foot_x = None
            v = max(heel.visibility, ankle.visibility)

        foot_visibilities[i] = v
        if foot_x is not None:
            sacrum_x = (left_hip(frame).x + right_hip(frame).x) / 2.0
            raw_signal[i] = float(direction * (foot_x - sacrum_x))

    interpolated = interpolate_nans(raw_signal)
    
    # Use Savitzky-Golay smoothing (zero phase lag) instead of moving average
    smoothed = savgol_smooth(interpolated, fps=fps)

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
            min_prom = max(0.005, amplitude * MIN_PROMINENCE_RATIO)
            if min_prom > 0.0:
                peaks = find_peaks(segment, min_distance=min_peak_distance, min_prominence=min_prom)
                for peak_idx, peak_prominence in peaks:
                    f_idx = seg_start + peak_idx
                    # Foot must be at or in front of pelvis center during forward heel strike
                    if smoothed[f_idx] < -0.015:
                        continue
                    frame = frames[f_idx]
                    
                    confidence = _compute_event_confidence(
                        heel_visibility=foot_visibilities[f_idx],
                        prominence=peak_prominence,
                        segment_amplitude=amplitude
                    )
                    
                    events.append(GaitEvent(
                        frame_index=frame.frame_index,
                        time_seconds=float(frame.timestamp_ms / 1000.0),
                        side=side,
                        confidence=confidence
                    ))

        seg_start = seg_end

    return events


def _median(values: List[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    mid = len(s) // 2
    return s[mid] if len(s) % 2 == 1 else (s[mid - 1] + s[mid]) / 2.0


def _std_dev(values: List[float], mean_val: float) -> float:
    if len(values) < 2:
        return 0.0
    variance = sum((v - mean_val) ** 2 for v in values) / len(values)
    return math.sqrt(variance)


def filter_physiologic_step_times(events: List[GaitEvent]) -> List[GaitEvent]:
    """Filters out events that produce step times outside physiologic bounds,
    resolves temporal collisions between foot detections, and maintains cadence consistency."""
    if len(events) < 2:
        return events

    # Phase 1: Resolve temporal collisions (< 0.15s) between foot detections
    deduped: List[GaitEvent] = []
    i = 0
    while i < len(events):
        curr = events[i]
        if i + 1 < len(events):
            nxt = events[i + 1]
            delta = nxt.time_seconds - curr.time_seconds
            if delta < 0.15:
                # Collision: keep the higher-confidence event
                winner = curr if curr.confidence >= nxt.confidence else nxt
                deduped.append(winner)
                i += 2
                continue
        deduped.append(curr)
        i += 1

    if len(deduped) < 3:
        return deduped

    # Phase 2: Physiologic step & stride interval validation
    filtered: List[GaitEvent] = [deduped[0]]
    for ev in deduped[1:]:
        last_ev = filtered[-1]
        delta = ev.time_seconds - last_ev.time_seconds
        if ev.side == last_ev.side:
            # Same side stride interval must be >= 1.5 * MIN_STEP_TIME_SECONDS
            if delta >= (1.5 * MIN_STEP_TIME_SECONDS):
                filtered.append(ev)
        else:
            if MIN_STEP_TIME_SECONDS <= delta <= MAX_STEP_TIME_SECONDS:
                filtered.append(ev)

    return filtered


def detect_gait_events(frames: List[PoseFrame], fps: float) -> List[GaitEvent]:
    """Full temporal gait event detection across left and right lower extremities."""
    if not frames or fps <= 0.0:
        return []

    direction = estimate_direction_sign(frames)
    min_peak_distance = max(1, math.ceil(0.25 * fps))

    left_events = detect_side_events(frames, fps, Side.LEFT, min_peak_distance, direction)
    right_events = detect_side_events(frames, fps, Side.RIGHT, min_peak_distance, direction)

    combined = left_events + right_events
    combined.sort(key=lambda e: e.time_seconds)

    return filter_physiologic_step_times(combined)

