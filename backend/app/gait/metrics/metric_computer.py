"""
Metric calculation engine ported from ToddleAI MetricComputer.
"""
import math
from typing import List
from ..schemas import GaitEvent, StepMeasurement, TemporalMetrics, Side

MIN_STEP_TIME_SECONDS = 0.25
MAX_STEP_TIME_SECONDS = 1.5
EPSILON = 1e-6


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


class MetricComputer:
    """Computes cadence, step timing, left-right asymmetry, and step-time variability."""

    def compute_metrics(self, events: List[GaitEvent]) -> TemporalMetrics:
        if len(events) < 2:
            return self.no_data()

        sorted_events = sorted(events, key=lambda e: e.frame_index)
        steps: List[StepMeasurement] = []

        for first, second in zip(sorted_events[:-1], sorted_events[1:]):
            if first.side == second.side:
                continue

            duration = second.time_seconds - first.time_seconds
            if MIN_STEP_TIME_SECONDS <= duration <= MAX_STEP_TIME_SECONDS:
                steps.append(StepMeasurement(
                    duration=float(duration),
                    ending_side=second.side,
                    confidence=float(min(first.confidence, second.confidence))
                ))

        if not steps:
            return self.no_data()

        left_steps = [s for s in steps if s.ending_side == Side.LEFT]
        right_steps = [s for s in steps if s.ending_side == Side.RIGHT]

        durations = [s.duration for s in steps]
        left_durations = [s.duration for s in left_steps]
        right_durations = [s.duration for s in right_steps]

        median_step_time = _median(durations)
        mean_step_time = _mean(durations)
        left_mean = _mean(left_durations)
        right_mean = _mean(right_durations)

        cadence = (60.0 / median_step_time) if median_step_time > 0.0 else 0.0

        timing_diff_ms = abs(left_mean - right_mean) * 1000.0 if (left_mean > 0.0 and right_mean > 0.0) else 0.0
        symmetry_ratio = (left_mean / right_mean) if (left_mean > 0.0 and right_mean > 0.0) else 0.0

        # AsymmetryPct = 100 * |L - R| / (0.5 * (L + R) + eps)
        asymmetry_pct = 0.0
        if left_mean > 0.0 and right_mean > 0.0:
            asymmetry_pct = (100.0 * abs(left_mean - right_mean)) / (0.5 * (left_mean + right_mean) + EPSILON)

        # CoV% = 100 * SD / |mean|
        step_time_cov = 0.0
        if mean_step_time > 0.0 and len(steps) > 1:
            sd = _std_dev(durations, mean_step_time)
            step_time_cov = (sd / mean_step_time) * 100.0

        return TemporalMetrics(
            step_times=steps,
            mean_step_time=round(mean_step_time, 4),
            median_step_time=round(median_step_time, 4),
            cadence=round(cadence, 1),
            left_mean_step_time=round(left_mean, 4),
            right_mean_step_time=round(right_mean, 4),
            timing_difference_ms=round(timing_diff_ms, 1),
            symmetry_ratio=round(symmetry_ratio, 3),
            step_time_asymmetry_pct=round(asymmetry_pct, 1),
            step_time_cov=round(step_time_cov, 1),
            usable_step_count=len(steps),
            usable_cycle_count=min(len(left_steps), len(right_steps))
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
            usable_cycle_count=0
        )
