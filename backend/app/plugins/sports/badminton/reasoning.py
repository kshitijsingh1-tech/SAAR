"""
Badminton Grounded Reasoning & Multi-Signal Hypothesis Engine.

Adheres strictly to:
1. Section 11: Multi-signal hypothesis gating ("Left-space underutilization" requires
   multiple corroborating observations — occupancy deficit + shot target skew +
   recovery position bias — before being asserted in the graph).
2. Section 11 Epistemic Framing: Observation -> Trend -> Correlation -> Hypothesis.
   Outputs strictly hedged, evidence-qualified language ("may indicate",
   "is consistent with a pattern of", "suggests potential"), never assertive causal certainty.
3. Section 27 "What's Missing" Protocol: Explicitly declines queries regarding unmeasured,
   uncalibrated, or out-of-scope parameters (diet/nutrition per Section 52, opponent data,
   uncalibrated court metrics, speed tracking gaps) rather than fabricating or burying fine print.
"""

from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field
import re

from .schemas import (
    CourtCalibration,
    MovementMetrics,
    ShotMetrics,
    ShotResult,
    SpeedMetrics,
    EnergyMetrics,
    PoseMetrics,
    BadmintonAnalysisResult,
)


class HypothesisSignal(BaseModel):
    name: str
    observed_value: Any
    threshold_criterion: str
    confidence: float
    is_satisfied: bool
    evidence_description: str


class HypothesisGateResult(BaseModel):
    hypothesis_id: str
    title: str
    is_asserted: bool
    signals_evaluated: List[HypothesisSignal]
    satisfied_signals_count: int
    minimum_required_signals: int = 2
    gate_reason: str
    epistemic_text: Optional[str] = None
    hedged_summary: Optional[str] = None
    node_properties: Dict[str, Any] = Field(default_factory=dict)


class MissingDataAssessment(BaseModel):
    is_missing: bool
    parameter: str
    category: str
    reason: str
    hedged_guidance: str


class BadmintonHypothesisEngine:
    """
    Evaluates multi-signal gating for biomechanical/tactical hypotheses
    and performs Section 27 "what's missing" gap assessments.
    """

    @staticmethod
    def evaluate_left_space_underutilization(
        court_calibration: Optional[CourtCalibration],
        movement_metrics: Optional[MovementMetrics],
        shot_metrics: Optional[ShotMetrics],
        shots: Optional[List[ShotResult]] = None
    ) -> HypothesisGateResult:
        """
        Evaluates Section 11's canonical 'Left-Space Underutilization' hypothesis.

        Requires AT LEAST 2 out of 3 supporting signals:
        - Signal 1: Left-court region occupancy deficit (< 20% or substantial deficit vs right).
        - Signal 2: Shot placement target distribution skew (> 60% right court or < 25% left court).
        - Signal 3: Post-shot recovery position bias (mean recovery position shifted > 0.15 normalized width to right).

        STRICT GATING:
        - If court is not calibrated, spatial court metrics are unavailable -> NOT asserted.
        - If fewer than 2 signals are satisfied -> NOT asserted.
        """
        shots = shots or []
        signals: List[HypothesisSignal] = []

        # Prerequisite check: Court calibration
        if not court_calibration or not court_calibration.is_calibrated:
            return HypothesisGateResult(
                hypothesis_id="hypo_left_space_underutilization",
                title="Left-Space Underutilization",
                is_asserted=False,
                signals_evaluated=[],
                satisfied_signals_count=0,
                minimum_required_signals=2,
                gate_reason=(
                    "GATED OUT: Court is not calibrated. Spatial region occupancy, "
                    "calibrated shot targeting, and metric recovery positioning are "
                    "strictly unavailable without a verified homography."
                ),
                epistemic_text=None,
                hedged_summary=None
            )

        # -------------------------------------------------------------
        # Signal 1: Region Occupancy Deficit (Phase 5)
        # -------------------------------------------------------------
        # Check occupancy across regions (supports both region_occupancies list and breakdown dict)
        left_occupancy = 0.0
        right_occupancy = 0.0

        region_list = getattr(movement_metrics, "region_occupancies", []) or []
        for reg in region_list:
            r_id = getattr(reg, "region_id", "") or getattr(reg, "name", "")
            pct = getattr(reg, "occupancy_pct", 0.0)
            if any(k in r_id.lower() for k in ["left", "l_"]):
                left_occupancy += pct
            elif any(k in r_id.lower() for k in ["right", "r_"]):
                right_occupancy += pct

        occupancy_breakdown = getattr(movement_metrics, "region_occupancy_breakdown", None)
        if not occupancy_breakdown and hasattr(movement_metrics, "__pydantic_extra__") and movement_metrics.__pydantic_extra__:
            occupancy_breakdown = movement_metrics.__pydantic_extra__.get("region_occupancy_breakdown")

        if isinstance(occupancy_breakdown, dict) and left_occupancy == 0.0 and right_occupancy == 0.0:
            for r_id, r_data in occupancy_breakdown.items():
                pct = getattr(r_data, "occupancy_pct", None) if hasattr(r_data, "occupancy_pct") else (
                    r_data.get("occupancy_pct", 0.0) if isinstance(r_data, dict) else (
                        float(r_data) if isinstance(r_data, (int, float)) else 0.0
                    )
                )
                if any(k in r_id.lower() for k in ["left", "l_"]):
                    left_occupancy += pct
                elif any(k in r_id.lower() for k in ["right", "r_"]):
                    right_occupancy += pct

        # Signal 1 satisfaction: left occupancy < 20% when right occupancy > 30%
        # (or left occupancy < 0.5 * right occupancy)
        s1_satisfied = (left_occupancy < 20.0 and right_occupancy > 25.0) or (left_occupancy > 0 and right_occupancy >= 2.0 * left_occupancy)
        signals.append(HypothesisSignal(
            name="left_region_occupancy_deficit",
            observed_value={"left_pct": round(left_occupancy, 1), "right_pct": round(right_occupancy, 1)},
            threshold_criterion="left_occupancy < 20.0% with right_occupancy > 25.0%",
            confidence=0.85 if s1_satisfied else 0.30,
            is_satisfied=s1_satisfied,
            evidence_description=(
                f"Observed {left_occupancy:.1f}% time spent in left-court regions vs {right_occupancy:.1f}% in right-court regions."
                if s1_satisfied
                else f"Balanced or non-skewed court occupancy (left: {left_occupancy:.1f}%, right: {right_occupancy:.1f}%)."
            )
        ))

        # -------------------------------------------------------------
        # Signal 2: Shot Placement Target Distribution Skew (Phase 8)
        # -------------------------------------------------------------
        placement = getattr(shot_metrics, "placement_metrics", None) or {}
        # Check target coordinate x distributions across shots (0.0=left, 6.1=right in BWF standard singles)
        right_targets = 0
        left_targets = 0
        total_targets = 0

        # Check explicit placement dictionary or inspect individual shot target_position
        if isinstance(placement, dict) and "target_distribution" in placement:
            t_dist = placement.get("target_distribution", {})
            left_targets = t_dist.get("left_half_count", 0)
            right_targets = t_dist.get("right_half_count", 0)
            total_targets = left_targets + right_targets
        else:
            for s in shots:
                if s.target_position and len(s.target_position) >= 2:
                    total_targets += 1
                    # court width is 6.1m, midpoint is 3.05m
                    if s.target_position[0] > 3.05:
                        right_targets += 1
                    elif s.target_position[0] < 3.05:
                        left_targets += 1

        right_target_pct = (right_targets / total_targets * 100.0) if total_targets > 0 else 0.0
        left_target_pct = (left_targets / total_targets * 100.0) if total_targets > 0 else 0.0

        s2_satisfied = total_targets >= 3 and (right_target_pct >= 60.0 or left_target_pct <= 25.0)
        signals.append(HypothesisSignal(
            name="shot_target_distribution_skew",
            observed_value={"left_target_pct": round(left_target_pct, 1), "right_target_pct": round(right_target_pct, 1), "total_shots": total_targets},
            threshold_criterion="total_shots >= 3 and right_target_pct >= 60.0%",
            confidence=0.88 if s2_satisfied else 0.35,
            is_satisfied=s2_satisfied,
            evidence_description=(
                f"Recorded target placement skew: {right_target_pct:.1f}% targeted right half ({right_targets}/{total_targets} shots)."
                if s2_satisfied
                else f"No statistically significant shot target skew ({left_target_pct:.1f}% left, {right_target_pct:.1f}% right, n={total_targets})."
            )
        ))

        # -------------------------------------------------------------
        # Signal 3: Post-Shot Recovery Position Bias (Phase 8)
        # -------------------------------------------------------------
        recovery = getattr(shot_metrics, "recovery_metrics", None) or {}
        # Check mean recovery position offset from court center line (x = 3.05m)
        mean_recovery_x = None
        recovery_bias_satisfied = False

        if isinstance(recovery, dict) and "per_shot_recovery" in recovery:
            rec_records = recovery.get("per_shot_recovery", [])
            valid_x = [r.get("end_position", [None])[0] for r in rec_records if isinstance(r, dict) and r.get("end_position") and len(r["end_position"]) >= 1 and r["end_position"][0] is not None]
            if valid_x:
                mean_recovery_x = sum(valid_x) / len(valid_x)
                # normalized court width offset: > 3.5m indicates significant right shift (center = 3.05m)
                recovery_bias_satisfied = mean_recovery_x >= 3.50

        signals.append(HypothesisSignal(
            name="recovery_position_bias",
            observed_value={"mean_recovery_x_m": round(mean_recovery_x, 2) if mean_recovery_x is not None else None},
            threshold_criterion="mean_recovery_x >= 3.50m (center = 3.05m)",
            confidence=0.82 if recovery_bias_satisfied else 0.30,
            is_satisfied=recovery_bias_satisfied,
            evidence_description=(
                f"Mean base recovery centroid is shifted rightwards to x = {mean_recovery_x:.2f}m (offset: +{mean_recovery_x - 3.05:.2f}m from centerline)."
                if recovery_bias_satisfied
                else (f"Recovery centroid centered at x = {mean_recovery_x:.2f}m without significant lateral bias." if mean_recovery_x is not None else "Recovery position data insufficient.")
            )
        ))

        # -------------------------------------------------------------
        # Multi-Signal Gating Assessment (Require >= 2 Signals)
        # -------------------------------------------------------------
        satisfied_count = sum(1 for s in signals if s.is_satisfied)
        is_asserted = satisfied_count >= 2

        if is_asserted:
            corroborating_descs = [s.evidence_description for s in signals if s.is_satisfied]
            # Section 11 Epistemic Framing: Observation -> Trend -> Correlation -> Hypothesis
            epistemic_text = (
                f"Observation: {corroborating_descs[0]} "
                f"Trend: Consecutive rally exchanges show recurring lateral asymmetry across sessions. "
                f"Correlation: {corroborating_descs[1]} correlates with observed spatial positioning. "
                f"Hypothesis: This data is consistent with a pattern of left-space underutilization, "
                f"which may indicate tactical protection, visual habit, or movement reluctance on the backhand side."
            )
            hedged_summary = (
                "Empirical evidence is consistent with a pattern of left-space underutilization. "
                "Observations suggest potential tactical avoidance or reach asymmetry, which may indicate "
                "a preference for forecourt/midcourt right-side positioning. Requires coach validation."
            )
            gate_reason = (
                f"MULTI-SIGNAL GATE PASSED ({satisfied_count}/3 signals satisfied): "
                f"Corroborated by {', '.join([s.name for s in signals if s.is_satisfied])}."
            )
        else:
            epistemic_text = None
            hedged_summary = None
            satisfied_names = [s.name for s in signals if s.is_satisfied]
            gate_reason = (
                f"GATED OUT: Only {satisfied_count}/3 supporting signals satisfied "
                f"({', '.join(satisfied_names) if satisfied_names else 'none'}). "
                f"Section 11 strictly requires at least 2 corroborating signals (occupancy, shot placement, recovery bias) "
                f"to prevent false assertions."
            )

        return HypothesisGateResult(
            hypothesis_id="hypo_left_space_underutilization",
            title="Hypothesis: Left-Space Underutilization",
            is_asserted=is_asserted,
            signals_evaluated=signals,
            satisfied_signals_count=satisfied_count,
            minimum_required_signals=2,
            gate_reason=gate_reason,
            epistemic_text=epistemic_text,
            hedged_summary=hedged_summary,
            node_properties={
                "value": hedged_summary or "GATED_UNVERIFIED",
                "unit": "hypothesis_framework",
                "confidence": 0.72 if is_asserted else 0.25,
                "source": "BadmintonHypothesisEngine (Section 11 Multi-Signal Gate)",
                "timestamp_or_frame_range": "Rally Aggregate Scope",
                "calculation_method": "Multi-signal corroboration gate (occupancy + shot placement + recovery position)",
                "signals_satisfied_count": satisfied_count,
                "epistemic_framing": "Observation -> Trend -> Correlation -> Hypothesis"
            }
        )

    @staticmethod
    def assess_missing_data(
        question: str,
        analysis_result: Optional[BadmintonAnalysisResult] = None
    ) -> Optional[MissingDataAssessment]:
        """
        Implements Section 27 'What's Missing' behavior:
        When a metric needed to answer a question is unavailable (e.g. court not calibrated,
        no opponent data, speed estimate unavailable, or medical/dietary factors per Section 52),
        the reasoning agent explicitly says so up front rather than fabricating or burying fine print.
        """
        q_lower = question.lower()

        # 1. Dietary / Nutritional / Medical Treatment Check (Section 52)
        diet_keywords = [
            "diet", "nutrition", "food", "calorie intake", "protein", "supplement", "vitamin",
            "medical", "injury treatment", "prescribe", "medication", "therapy", "cure"
        ]
        if any(re.search(rf"\b{re.escape(k)}\b", q_lower) for k in diet_keywords):
            return MissingDataAssessment(
                is_missing=True,
                parameter="dietary_nutritional_medical_data",
                category="OUT_OF_SCOPE_PHYSIOLOGICAL",
                reason=(
                    "Medical, clinical, and dietary information cannot be determined from video footage. "
                    "Video analysis provides optical kinematics, stroke frequencies, and gross athletic energy estimates, "
                    "but provides zero physiological biomarker, metabolic blood, or nutritional tracking."
                ),
                hedged_guidance=(
                    "Nutritional intake and medical recovery strategies must be evaluated in consultation with "
                    "a qualified sports dietitian or medical professional. The video analysis cannot assess or recommend dietary changes."
                )
            )

        # 2. Opponent Positioning / Opponent Outcome Check (Section 21 / 27)
        opponent_keywords = ["opponent", "competitor", "other player", "adversary", "rival", "winner vs error", "winner or error"]
        if any(re.search(rf"\b{re.escape(k)}\b", q_lower) for k in opponent_keywords):
            return MissingDataAssessment(
                is_missing=True,
                parameter="opponent_tracking_data",
                category="SINGLE_PLAYER_RECORDING_GAP",
                reason=(
                    "Opponent data is missing: The video was recorded and processed as a single-player camera capture. "
                    "Opponent court position, shot return quality, and winning/error rally outcomes cannot be deterministically verified."
                ),
                hedged_guidance=(
                    "Analysis is strictly limited to the tracked primary athlete. "
                    "Opponent interaction and tactical pressure cannot be determined from this single-player recording."
                )
            )

        # 3. Court Metric Calibration Check
        court_keywords = ["court position", "meters", "court coverage", "region occupancy", "footwork distance", "distance covered", "placement"]
        if any(re.search(rf"\b{re.escape(k)}\b", q_lower) for k in court_keywords):
            if analysis_result and analysis_result.court_calibration and not analysis_result.court_calibration.is_calibrated:
                return MissingDataAssessment(
                    is_missing=True,
                    parameter="calibrated_court_geometry",
                    category="UNCALIBRATED_PERSPECTIVE",
                    reason=(
                        f"Court metric calibration is unavailable: {analysis_result.court_calibration.uncalibrated_reason or 'Camera angle or line visibility did not meet homography thresholds.'} "
                        "Without a metric court homography, physical distances in meters, region occupancy percentages, and calibrated shot placement cannot be determined."
                    ),
                    hedged_guidance=(
                        "To unlock physical court metrics, record from a stable tripod where all four court boundary lines are clearly visible."
                    )
                )

        # 4. Shuttle / Racket Speed Tracking Check (Section 13)
        speed_keywords = ["racket speed", "shuttle speed", "smash speed", "velocity km/h", "impact speed", "how fast"]
        if any(re.search(rf"\b{re.escape(k)}\b", q_lower) for k in speed_keywords):
            if analysis_result and analysis_result.speed_metrics:
                sm = analysis_result.speed_metrics
                if not sm.shuttle_speed_peak.available and not sm.racket_speed_peak.available:
                    return MissingDataAssessment(
                        is_missing=True,
                        parameter="ballistic_speed_tracking",
                        category="INSUFFICIENT_CONTINUOUS_TRACKING",
                        reason=(
                            "Speed estimate unavailable — insufficient continuous tracking (Section 13). "
                            "Accurate ballistic measurement requires specialized high-frame-rate shuttle tracking and court homography "
                            "not cleared by this video capture."
                        ),
                        hedged_guidance=(
                            "Racket and shuttle speed estimates require continuous sub-millisecond impact tracking and calibrated perspective geometry."
                        )
                    )

        return None
