"""
Observation engine producing structured non-diagnostic observation cards ported from ToddleAI.
"""
from typing import List
from ..schemas import TemporalMetrics, Observation, MetricStatus, CaptureConfidence
from ..norms.toddler_norms import get_cadence_range

ASYMMETRY_THRESHOLD_PCT = 10.0
STEP_TIME_COV_THRESHOLD_PCT = 15.0


def _age_label(months: int) -> str:
    """Parent-facing age phrase, e.g. '2-year-old' or '16-month-old'."""
    years = months // 12
    if years < 1:
        return f"{months}-month-old"
    return f"{years}-year-old"


class ObservationEngine:
    """Produces non-diagnostic structured observation cards comparing measured values to age benchmarks."""

    def generate_observations(
        self,
        metrics: TemporalMetrics,
        child_age_months: int,
        capture_confidence: CaptureConfidence = CaptureConfidence.HIGH
    ) -> List[Observation]:
        age_label = _age_label(child_age_months)
        cadence_range = get_cadence_range(child_age_months)
        observations: List[Observation] = []

        # 1. Cadence Observation
        cadence_range_text = f"{cadence_range.low:.0f}–{cadence_range.high:.0f} steps/min"
        if cadence_range.low <= metrics.cadence <= cadence_range.high:
            cadence_note = "In the typical range."
            cadence_status = MetricStatus.TYPICAL
        elif metrics.cadence < cadence_range.low:
            cadence_note = "A little below the typical range."
            cadence_status = MetricStatus.ELEVATED
        else:
            cadence_note = "A little above the typical range."
            cadence_status = MetricStatus.ELEVATED

        observations.append(Observation(
            type="cadence",
            measurement=f"Cadence: {metrics.cadence:.0f} steps/min",
            context=f"Typical for a {age_label}: {cadence_range_text}.",
            note=cadence_note,
            confidence="",
            status=cadence_status
        ))

        # 2. Left / Right Symmetry Observation
        symmetry_in_range = metrics.step_time_asymmetry_pct <= ASYMMETRY_THRESHOLD_PCT
        observations.append(Observation(
            type="symmetry",
            measurement=f"Left–right symmetry: {metrics.step_time_asymmetry_pct:.0f}% difference",
            context=(
                f"Even left/right step timing is typically within {ASYMMETRY_THRESHOLD_PCT:.0f}% "
                f"(left {metrics.left_mean_step_time:.2f} s, right {metrics.right_mean_step_time:.2f} s)."
            ),
            note="In the typical range." if symmetry_in_range else "Above the typical range.",
            confidence="",
            status=MetricStatus.TYPICAL if symmetry_in_range else MetricStatus.ELEVATED
        ))

        # 3. Step Rhythm Consistency Observation
        variability_in_range = metrics.step_time_cov <= STEP_TIME_COV_THRESHOLD_PCT
        observations.append(Observation(
            type="variability",
            measurement=f"Step rhythm: {metrics.step_time_cov:.0f}% variation",
            context=(
                f"Step timing is typically within {STEP_TIME_COV_THRESHOLD_PCT:.0f}% variation; "
                f"young children are naturally a bit higher."
            ),
            note="In the typical range." if variability_in_range else "Above the typical range.",
            confidence="",
            status=MetricStatus.TYPICAL if variability_in_range else MetricStatus.ELEVATED
        ))

        return observations
