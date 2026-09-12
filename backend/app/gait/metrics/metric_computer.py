"""
Metric calculation engine with confidence-weighted computation and IQR-based outlier rejection.

Upgraded from the original ToddleAI port with:
- IQR-based outlier filtering on step durations
- Confidence-weighted mean/median computations
- Pipeline confidence composite score
"""
import math
from typing import List, Tuple, Optional
from ..schemas import GaitEvent, StepMeasurement, TemporalMetrics, Side

MIN_STEP_TIME_SECONDS = 0.20  # Relaxed slightly for toddler gaits
MAX_STEP_TIME_SECONDS = 1.5
EPSILON = 1e-6
IQR_MULTIPLIER = 1.5  # Standard IQR fence multiplier


def _median(values: List[float]) -> float:
    if not values:
        return 0.0
    sorted_v = sorted(values)
    mid = len(sorted_v) // 2
    if len(sorted_v) % 2 == 1:
        return float(sorted_v[mid])
    return float((sorted_v[mid - 1] + sorted_v[mid]) / 2.0)


def _mean(values: List[float]) -> float:
    if not values:
        return 0.0
    return float(sum(values) / len(values))


def _std_dev(values: List[float], mean_val: float) -> float:
    if len(values) < 2:
        return 0.0
    variance = sum((v - mean_val) ** 2 for v in values) / len(values)
    return float(math.sqrt(variance))


def _weighted_mean(values: List[float], weights: List[float]) -> float:
    """Compute weighted mean. Falls back to simple mean if weights sum to zero."""
    if not values:
        return 0.0
    weight_sum = sum(weights)
    if weight_sum <= EPSILON:
        return _mean(values)
    return float(sum(v * w for v, w in zip(values, weights)) / weight_sum)


def _iqr_filter(steps: List[StepMeasurement]) -> List[StepMeasurement]:
    """Removes step duration outliers using IQR fencing.
    
    Steps with durations outside [Q1 - 1.5*IQR, Q3 + 1.5*IQR] are excluded.
    """
    if len(steps) < 4:
        return steps  # Not enough data for meaningful IQR
    
    durations = sorted(s.duration for s in steps)
    n = len(durations)
    q1_idx = n // 4
    q3_idx = (3 * n) // 4
    
    q1 = durations[q1_idx]
    q3 = durations[q3_idx]
    iqr = q3 - q1
    
    if iqr <= EPSILON:
        return steps  # All durations are essentially equal
    
    lower_fence = q1 - IQR_MULTIPLIER * iqr
    upper_fence = q3 + IQR_MULTIPLIER * iqr
    
    return [s for s in steps if lower_fence <= s.duration <= upper_fence]


class MetricComputer:
    """Computes cadence, step timing, left-right asymmetry, step-time variability,
    and pipeline confidence with outlier rejection."""

    def compute_metrics(
        self,
        events: List[GaitEvent],
        good_frame_ratio: float = 1.0
    ) -> TemporalMetrics:
        if len(events) < 2:
            return self.no_data()

        sorted_events = sorted(events, key=lambda e: e.frame_index)
        steps: List[StepMeasurement] = []

        for first, second in zip(sorted_events[:-1], sorted_events[1:]):
            duration = second.time_seconds - first.time_seconds
            if first.side != second.side:
                if MIN_STEP_TIME_SECONDS <= duration <= MAX_STEP_TIME_SECONDS:
                    steps.append(StepMeasurement(
                        duration=float(duration),
                        ending_side=second.side,
                        confidence=float(min(first.confidence, second.confidence))
                    ))
            else:
                # Same-side stride cycle: contralateral foot contact was occluded
                # A single-side stride comprises 2 steps (stride_time = 2 * step_time)
                if (1.5 * MIN_STEP_TIME_SECONDS) <= duration <= (2.0 * MAX_STEP_TIME_SECONDS):
                    half_duration = duration / 2.0
                    opp_side = Side.LEFT if second.side == Side.RIGHT else Side.RIGHT
                    inferred_conf = float(min(first.confidence, second.confidence) * 0.75)
                    steps.append(StepMeasurement(
                        duration=float(half_duration),
                        ending_side=opp_side,
                        confidence=inferred_conf
                    ))
                    steps.append(StepMeasurement(
                        duration=float(half_duration),
                        ending_side=second.side,
                        confidence=inferred_conf
                    ))

        if not steps:
            return self.no_data()

        # Apply IQR-based outlier rejection
        clean_steps = _iqr_filter(steps)
        if not clean_steps:
            clean_steps = steps  # Fallback if IQR removed everything

        left_steps = [s for s in clean_steps if s.ending_side == Side.LEFT]
        right_steps = [s for s in clean_steps if s.ending_side == Side.RIGHT]

        durations = [s.duration for s in clean_steps]
        confidences = [s.confidence for s in clean_steps]
        left_durations = [s.duration for s in left_steps]
        right_durations = [s.duration for s in right_steps]
        left_confidences = [s.confidence for s in left_steps]
        right_confidences = [s.confidence for s in right_steps]

        # Use confidence-weighted means for better accuracy
        median_step_time = _median(durations)
        mean_step_time = _weighted_mean(durations, confidences)
        left_mean = _weighted_mean(left_durations, left_confidences) if left_durations else 0.0
        right_mean = _weighted_mean(right_durations, right_confidences) if right_durations else 0.0

        cadence = (60.0 / median_step_time) if median_step_time > 0.0 else 0.0

        timing_diff_ms = abs(left_mean - right_mean) * 1000.0 if (left_mean > 0.0 and right_mean > 0.0) else 0.0
        symmetry_ratio = (left_mean / right_mean) if (left_mean > 0.0 and right_mean > 0.0) else 0.0

        # AsymmetryPct = 100 * |L - R| / (0.5 * (L + R) + eps)
        asymmetry_pct = 0.0
        if left_mean > 0.0 and right_mean > 0.0:
            asymmetry_pct = (100.0 * abs(left_mean - right_mean)) / (0.5 * (left_mean + right_mean) + EPSILON)

        # CoV% = 100 * SD / |mean|
        step_time_cov = 0.0
        if mean_step_time > 0.0 and len(clean_steps) > 1:
            sd = _std_dev(durations, mean_step_time)
            step_time_cov = (sd / mean_step_time) * 100.0

        # Pipeline confidence: geometric mean of event confidence and frame quality
        mean_event_confidence = _mean(confidences) if confidences else 0.0
        pipeline_confidence = math.sqrt(mean_event_confidence * good_frame_ratio) if mean_event_confidence > 0 else 0.0

        return TemporalMetrics(
            step_times=clean_steps,
            mean_step_time=round(mean_step_time, 4),
            median_step_time=round(median_step_time, 4),
            cadence=round(cadence, 1),
            left_mean_step_time=round(left_mean, 4),
            right_mean_step_time=round(right_mean, 4),
            timing_difference_ms=round(timing_diff_ms, 1),
            symmetry_ratio=round(symmetry_ratio, 3),
            step_time_asymmetry_pct=round(asymmetry_pct, 1),
            step_time_cov=round(step_time_cov, 1),
            usable_step_count=len(clean_steps),
            usable_cycle_count=min(len(left_steps), len(right_steps)),
            pipeline_confidence=round(pipeline_confidence, 4)
        )

    def no_data(self) -> TemporalMetrics:
        return TemporalMetrics(
            step_times=[],
            mean_step_time=0.0,
            median_step_time=0.0,
            cadence=0.0,
            left_mean_step_time=0.0,
            right_mean_step_time=0.0,
            timing_difference_ms=0.0,
            symmetry_ratio=0.0,
            step_time_asymmetry_pct=0.0,
            step_time_cov=0.0,
            usable_step_count=0,
            usable_cycle_count=0,
            pipeline_confidence=0.0
        )
