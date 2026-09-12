"""
Advanced temporal gait metrics (stance time, swing time, double-support approximation)
consuming existing ToddleAI validated gait events.

Preservation Rule:
Does NOT alter or recalculate existing step count, cadence, step time, symmetry ratio,
or variability from MetricComputer.
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from ..schemas import GaitEvent, TemporalMetrics, Side


@dataclass
class AdvancedTemporalResult:
    step_count: int
    cadence_steps_per_min: float
    mean_step_time_sec: float
    median_step_time_sec: float
    step_time_variability_pct: float
    mean_stride_time_sec: Optional[float]
    estimated_stance_time_sec: Optional[float]
    estimated_swing_time_sec: Optional[float]
    estimated_double_support_sec: Optional[float]
    stance_phase_pct: Optional[float]
    swing_phase_pct: Optional[float]
    double_support_pct: Optional[float]
    confidence: float


def compute_advanced_temporal_metrics(
    events: List[GaitEvent],
    base_metrics: TemporalMetrics
) -> AdvancedTemporalResult:
    """
    Derives stance, swing, and double-support temporal parameters from validated gait events
    while strictly preserving the base MetricComputer results.
    """
    step_cnt = base_metrics.usable_step_count
    cadence = base_metrics.cadence
    mean_step = base_metrics.mean_step_time
    med_step = base_metrics.median_step_time
    cov = base_metrics.step_time_cov

    if step_cnt < 2 or med_step <= 0.0:
        return AdvancedTemporalResult(
            step_count=step_cnt,
            cadence_steps_per_min=cadence,
            mean_step_time_sec=mean_step,
            median_step_time_sec=med_step,
            step_time_variability_pct=cov,
            mean_stride_time_sec=None,
            estimated_stance_time_sec=None,
            estimated_swing_time_sec=None,
            estimated_double_support_sec=None,
            stance_phase_pct=None,
            swing_phase_pct=None,
            double_support_pct=None,
            confidence=0.0
        )

    # Stride time is standardly 2 * step_time in regular bilateral gait
    stride_time = 2.0 * med_step

    # Direct cycle estimation from consecutive ipsilateral events where available
    left_events = sorted([e for e in events if e.side == Side.LEFT], key=lambda e: e.time_seconds)
    right_events = sorted([e for e in events if e.side == Side.RIGHT], key=lambda e: e.time_seconds)

    cycle_durations: List[float] = []
    for side_list in [left_events, right_events]:
        if len(side_list) >= 2:
            for e1, e2 in zip(side_list[:-1], side_list[1:]):
                c_dur = e2.time_seconds - e1.time_seconds
                if (1.5 * 0.20) <= c_dur <= 3.0:
                    cycle_durations.append(c_dur)

    if cycle_durations:
        stride_time = float(sum(cycle_durations) / len(cycle_durations))

    # Direct kinematic phase derivation from actual video-derived step and stride intervals:
    # Swing phase duration of one limb directly equals the single-support contralateral step time:
    swing_time = float(mean_step) if mean_step > 0 else (stride_time / 2.0)
    
    # Stance duration is the total stride cycle duration minus the swing duration:
    stance_time = max(0.0, stride_time - swing_time)
    
    # Double-support interval is the overlap period when both feet are in contact:
    double_support_time = max(0.0, stance_time - swing_time) if stance_time > swing_time else 0.0

    # Dynamic percentage of stride cycle:
    stance_pct = round((stance_time / stride_time) * 100.0, 1) if stride_time > 0 else None
    swing_pct = round((swing_time / stride_time) * 100.0, 1) if stride_time > 0 else None
    ds_pct = round((double_support_time / stride_time) * 100.0, 1) if stride_time > 0 else None

    return AdvancedTemporalResult(
        step_count=step_cnt,
        cadence_steps_per_min=cadence,
        mean_step_time_sec=mean_step,
        median_step_time_sec=med_step,
        step_time_variability_pct=cov,
        mean_stride_time_sec=round(stride_time, 3),
        estimated_stance_time_sec=round(stance_time, 3) if stance_time > 0 else None,
        estimated_swing_time_sec=round(swing_time, 3) if swing_time > 0 else None,
        estimated_double_support_sec=round(double_support_time, 3) if double_support_time > 0 else None,
        stance_phase_pct=stance_pct,
        swing_phase_pct=swing_pct,
        double_support_pct=ds_pct,
        confidence=base_metrics.pipeline_confidence
    )
