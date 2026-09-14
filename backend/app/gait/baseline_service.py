"""
SAAR — Personalized Gait Baseline Service (ToddleAI)

Establishes and maintains a personalized walking baseline for individual children
using running empirical statistics (mean, variability/std dev, sample count n).
Detects meaningful deviations between new video observations and the child's own normal.

Zero hardcoded normality: Evaluates the child against their own historical reference.
"""
import math
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class MetricBaseline(BaseModel):
    """Running empirical baseline statistics for a single gait metric."""
    metric_id: str
    display_name: str
    unit: str = ""
    baseline_mean: float = 0.0
    baseline_variability: float = 0.0  # Standard deviation
    n: int = 0
    min_observed: float = 0.0
    max_observed: float = 0.0
    history: List[float] = Field(default_factory=list)

    def update(self, value: float):
        """Update running statistics using Welford's algorithm."""
        if value is None or math.isnan(value):
            return

        self.history.append(round(value, 3))
        if len(self.history) > 20:
            self.history = self.history[-20:]

        if self.n == 0:
            self.baseline_mean = round(value, 3)
            self.baseline_variability = 0.0
            self.min_observed = round(value, 3)
            self.max_observed = round(value, 3)
            self.n = 1
        else:
            old_n = self.n
            self.n += 1
            old_mean = self.baseline_mean
            new_mean = old_mean + (value - old_mean) / self.n

            # Approximate running variance update
            old_var = self.baseline_variability ** 2
            new_var = ((old_n - 1) * old_var + (value - old_mean) * (value - new_mean)) / max(1, self.n - 1)
            new_std = math.sqrt(max(0.001, new_var))

            self.baseline_mean = round(new_mean, 3)
            self.baseline_variability = round(new_std, 3)
            self.min_observed = round(min(self.min_observed, value), 3)
            self.max_observed = round(max(self.max_observed, value), 3)


class PersonalizedBaseline(BaseModel):
    """Complete personalized gait baseline profile for a single child."""
    subject_id: str
    child_name: str = "Toddler"
    child_age_months: int = 24
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    total_sessions: int = 0
    metrics: Dict[str, MetricBaseline] = Field(default_factory=dict)


class BaselineComparisonItem(BaseModel):
    """Comparison of a single metric between today's recording and child's personal baseline."""
    metric_id: str
    display_name: str
    current_value: float
    baseline_mean: float
    baseline_variability: float
    delta: float
    delta_pct: float
    z_score: float
    unit: str = ""
    is_meaningful_deviation: bool = False
    deviation_direction: str = "stable"  # "elevated", "reduced", "stable"
    interpretation: str = ""


class BaselineComparisonResult(BaseModel):
    """Overall comparison report against child's personal baseline."""
    subject_id: str
    child_name: str
    child_age_months: int
    has_baseline: bool = True
    baseline_session_count: int = 0
    meaningful_deviations_found: int = 0
    has_meaningful_deviation: bool = False
    primary_alert: Optional[str] = None
    comparison_items: List[BaselineComparisonItem] = Field(default_factory=list)
    clinical_summary: str = ""


class PersonalizedGaitBaselineService:
    """In-memory service maintaining longitudinal child baselines."""

    def __init__(self):
        self._profiles: Dict[str, PersonalizedBaseline] = {}
        self._seed_default_demo_profile()

    def _seed_default_demo_profile(self):
        """Pre-seed sample child 'Leo (24m)' with 3 prior sessions for hackathon demonstration."""
        leo = PersonalizedBaseline(
            subject_id="child_leo_24m",
            child_name="Leo",
            child_age_months=24,
            total_sessions=3,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            metrics={
                "step_time_asymmetry_pct": MetricBaseline(
                    metric_id="step_time_asymmetry_pct",
                    display_name="Step Time Asymmetry",
                    unit="%",
                    baseline_mean=3.4,
                    baseline_variability=1.1,
                    n=3,
                    min_observed=2.2,
                    max_observed=4.5,
                    history=[2.8, 4.2, 3.2]
                ),
                "cadence": MetricBaseline(
                    metric_id="cadence",
                    display_name="Cadence",
                    unit="steps/min",
                    baseline_mean=142.5,
                    baseline_variability=4.2,
                    n=3,
                    min_observed=138.0,
                    max_observed=147.0,
                    history=[144.0, 139.0, 144.5]
                ),
                "mean_step_time": MetricBaseline(
                    metric_id="mean_step_time",
                    display_name="Mean Step Duration",
                    unit="s",
                    baseline_mean=0.42,
                    baseline_variability=0.02,
                    n=3,
                    min_observed=0.40,
                    max_observed=0.44,
                    history=[0.42, 0.43, 0.41]
                ),
                "step_time_cov": MetricBaseline(
                    metric_id="step_time_cov",
                    display_name="Rhythm Variability (CoV)",
                    unit="%",
                    baseline_mean=8.2,
                    baseline_variability=1.5,
                    n=3,
                    min_observed=6.8,
                    max_observed=9.6,
                    history=[7.8, 9.1, 7.7]
                ),
                "trunk_angle_deg": MetricBaseline(
                    metric_id="trunk_angle_deg",
                    display_name="Lateral Trunk Tilt",
                    unit="°",
                    baseline_mean=4.1,
                    baseline_variability=1.2,
                    n=3,
                    min_observed=3.0,
                    max_observed=5.4,
                    history=[3.8, 5.0, 3.5]
                ),
                "knee_rom_deg": MetricBaseline(
                    metric_id="knee_rom_deg",
                    display_name="Bilateral Knee ROM",
                    unit="°",
                    baseline_mean=58.2,
                    baseline_variability=3.1,
                    n=3,
                    min_observed=54.5,
                    max_observed=61.0,
                    history=[57.0, 60.5, 57.1]
                )
            }
        )
        self._profiles[leo.subject_id] = leo

    def list_profiles(self) -> List[Dict[str, Any]]:
        """Return list of all registered child profiles with baseline summary."""
        return [
            {
                "subject_id": p.subject_id,
                "child_name": p.child_name,
                "child_age_months": p.child_age_months,
                "total_sessions": p.total_sessions,
                "updated_at": p.updated_at,
                "has_baseline": p.total_sessions >= 1,
                "asymmetry_mean": p.metrics.get("step_time_asymmetry_pct", {}).baseline_mean if "step_time_asymmetry_pct" in p.metrics else None
            }
            for p in self._profiles.values()
        ]

    def get_profile(self, subject_id: str) -> Optional[PersonalizedBaseline]:
        return self._profiles.get(subject_id)

    def create_or_get_profile(self, subject_id: str, child_name: str = "Toddler", child_age_months: int = 24) -> PersonalizedBaseline:
        if subject_id in self._profiles:
            return self._profiles[subject_id]
        new_profile = PersonalizedBaseline(
            subject_id=subject_id,
            child_name=child_name,
            child_age_months=child_age_months,
            total_sessions=0
        )
        self._profiles[subject_id] = new_profile
        return new_profile

    def update_from_assessment(self, subject_id: str, assessment_dict: Dict[str, Any]) -> PersonalizedBaseline:
        """Update a child's baseline with metrics from a new validated video assessment."""
        profile = self.create_or_get_profile(
            subject_id=subject_id,
            child_name=assessment_dict.get("child_name") or "Toddler",
            child_age_months=assessment_dict.get("child_age_months", 24)
        )

        metrics = self._extract_raw_metrics(assessment_dict)
        for m_id, (val, name, unit) in metrics.items():
            if val is None:
                continue
            if m_id not in profile.metrics:
                profile.metrics[m_id] = MetricBaseline(
                    metric_id=m_id,
                    display_name=name,
                    unit=unit
                )
            profile.metrics[m_id].update(val)

        profile.total_sessions += 1
        profile.updated_at = datetime.now().isoformat()
        return profile

    def compare_assessment(self, subject_id: str, assessment_dict: Dict[str, Any]) -> BaselineComparisonResult:
        """
        Compare current assessment measurements against the child's personalized baseline.
        Identifies meaningful deviations (|z| >= 2.0 or delta% >= 25%).
        """
        profile = self._profiles.get(subject_id)
        child_name = profile.child_name if profile else assessment_dict.get("child_name", "Toddler")
        age_months = profile.child_age_months if profile else assessment_dict.get("child_age_months", 24)

        if not profile or profile.total_sessions == 0:
            return BaselineComparisonResult(
                subject_id=subject_id or "new_child",
                child_name=child_name,
                child_age_months=age_months,
                has_baseline=False,
                baseline_session_count=0,
                meaningful_deviations_found=0,
                has_meaningful_deviation=False,
                clinical_summary="No previous baseline recorded for this child yet. Today's recording will establish their initial personalized reference."
            )

        current_metrics = self._extract_raw_metrics(assessment_dict)
        items: List[BaselineComparisonItem] = []
        meaningful_count = 0
        primary_alert = None

        for m_id, (curr_val, display_name, unit) in current_metrics.items():
            if curr_val is None or m_id not in profile.metrics:
                continue

            base = profile.metrics[m_id]
            if base.n == 0:
                continue

            delta = round(curr_val - base.baseline_mean, 3)
            delta_pct = round((abs(delta) / max(0.001, base.baseline_mean)) * 100, 1)

            # Z-score computation
            sd = base.baseline_variability if base.baseline_variability > 0.05 else 0.5
            z = round(delta / sd, 2)

            # Meaningful deviation criteria:
            # For asymmetry: delta > 5% or |z| >= 2.0
            # For cadence/step time: delta_pct > 20% or |z| >= 2.0
            is_deviated = False
            direction = "stable"
            interpretation = "Within typical personalized range"

            if m_id == "step_time_asymmetry_pct":
                if delta >= 5.0 or z >= 2.0:
                    is_deviated = True
                    direction = "elevated"
                    interpretation = f"Elevated asymmetry (+{delta:.1f}% higher than {child_name}'s {base.baseline_mean:.1f}% baseline)"
                    if not primary_alert:
                        primary_alert = f"{child_name} exhibits a {curr_val:.1f}% step asymmetry today, markedly higher than their normal {base.baseline_mean:.1f}% baseline."
                elif delta <= -5.0 or z <= -2.0:
                    direction = "reduced"
                    interpretation = "Improved symmetry compared to baseline"
            else:
                if abs(z) >= 2.0 or delta_pct >= 25.0:
                    is_deviated = True
                    direction = "elevated" if delta > 0 else "reduced"
                    interpretation = f"Marked deviation ({direction}) from typical {base.baseline_mean:.1f}{unit} baseline (z={z:+.1f})"

            if is_deviated:
                meaningful_count += 1

            items.append(BaselineComparisonItem(
                metric_id=m_id,
                display_name=display_name,
                current_value=round(curr_val, 2),
                baseline_mean=round(base.baseline_mean, 2),
                baseline_variability=round(base.baseline_variability, 2),
                delta=delta,
                delta_pct=delta_pct,
                z_score=z,
                unit=unit,
                is_meaningful_deviation=is_deviated,
                deviation_direction=direction,
                interpretation=interpretation
            ))

        # Overall synthesis
        if meaningful_count > 0:
            summary = (
                f"Today's walking pattern shows {meaningful_count} meaningful deviation(s) from {child_name}'s "
                f"established baseline ({profile.total_sessions} previous sessions). "
                f"This shift indicates a change from their personal normal rather than general population variance."
            )
        else:
            summary = (
                f"All measured movement metrics are well within {child_name}'s personal baseline "
                f"established across {profile.total_sessions} previous recording sessions."
            )

        return BaselineComparisonResult(
            subject_id=subject_id,
            child_name=child_name,
            child_age_months=age_months,
            has_baseline=True,
            baseline_session_count=profile.total_sessions,
            meaningful_deviations_found=meaningful_count,
            has_meaningful_deviation=meaningful_count > 0,
            primary_alert=primary_alert,
            comparison_items=items,
            clinical_summary=summary
        )

    def _extract_raw_metrics(self, data: Dict[str, Any]) -> Dict[str, tuple]:
        """Safely extract float metrics from any raw or canonical result dict."""
        temporal = data.get("temporal") or data.get("metrics") or {}
        gait_prof = data.get("gait_profile") or {}
        posture = data.get("posture") or gait_prof.get("posture") or {}
        joint_motion = data.get("joint_motion") or gait_prof.get("joint_motion") or {}

        # Asymmetry

        asym = (
            data.get("step_time_asymmetry_pct") or
            temporal.get("step_time_asymmetry_pct") or
            data.get("symmetry", {}).get("step_time_asymmetry_pct") or
            data.get("metrics", {}).get("step_time_asymmetry_pct")
        )
        cadence = (
            data.get("cadence") or
            temporal.get("cadence") or
            temporal.get("cadence_steps_per_min") or
            data.get("metrics", {}).get("cadence")
        )
        step_time = (
            data.get("mean_step_time") or
            temporal.get("mean_step_time") or
            temporal.get("mean_step_time_sec") or
            data.get("metrics", {}).get("mean_step_time")
        )
        cov = (
            data.get("step_time_cov") or
            temporal.get("step_time_cov") or
            temporal.get("step_time_variability_pct") or
            data.get("metrics", {}).get("step_time_cov")
        )
        tilt = (
            data.get("trunk_angle_deg") or
            posture.get("trunk_angle_deg") or
            data.get("metrics", {}).get("trunk_angle_deg")
        )


        # Knee ROM (average of left and right if available)
        left_knee = joint_motion.get("left_knee", {}).get("rom_deg")
        right_knee = joint_motion.get("right_knee", {}).get("rom_deg")
        knee_rom = None
        if left_knee is not None and right_knee is not None:
            knee_rom = (left_knee + right_knee) / 2.0
        elif left_knee is not None:
            knee_rom = left_knee
        elif right_knee is not None:
            knee_rom = right_knee

        return {
            "step_time_asymmetry_pct": (_safe_float(asym), "Step Time Asymmetry", "%"),
            "cadence": (_safe_float(cadence), "Cadence", "steps/min"),
            "mean_step_time": (_safe_float(step_time), "Step Duration", "s"),
            "step_time_cov": (_safe_float(cov), "Rhythm Variability (CoV)", "%"),
            "trunk_angle_deg": (_safe_float(tilt), "Lateral Trunk Tilt", "°"),
            "knee_rom_deg": (_safe_float(knee_rom), "Bilateral Knee ROM", "°")
        }


def _safe_float(val: Any) -> Optional[float]:
    """Safely convert a scalar, string, or observation dictionary into a float without raising TypeError."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, dict):
        v = val.get("value")
        if v is not None:
            return _safe_float(v)
        for k in ["mean", "val", "score", "reading"]:
            if k in val and val[k] is not None:
                return _safe_float(val[k])
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None



# Global singleton service
personalized_baseline_service = PersonalizedGaitBaselineService()
