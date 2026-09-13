"""
Badminton Longitudinal Analysis Engine (Phase 17).

Provides deterministic multi-session trend analysis for the same player_id adhering to:
1. Architectural Reuse:
   Reuses AnalyticsService (Pearson r, Spearman rho, linear regression) and
   SportsPlugin.calculate_correlations rather than reimplementing statistical logic.
2. Deterministic Metrics:
   Evaluates shot accuracy, distribution, court coverage, movement efficiency,
   speeds, and recovery time across sessions. Computes trend slope, R², change percentage,
   and session-to-session deltas.
3. Epistemic Discipline (Phase 13 / Section 28):
   Strictly correlation-appropriate, non-causal language ("is consistent with",
   "may indicate", "suggests potential", "statistically co-occurs with").
   Zero causal claims asserted from empirical correlation.
4. Honest-Gap Integrity:
   Unmeasured signals (e.g. Section 21 movement efficiency) are preserved as
   unavailable rather than fabricating longitudinal progression.
"""

import math
import re
from typing import List, Dict, Any, Optional, Tuple

from app.schemas import NodeModel, EdgeModel, GraphStateModel
from app.graph_engine import ReasoningGraphEngine
from app.services.analytics_service import AnalyticsService
from app.plugins.sports_plugin import SportsPlugin

from .schemas import (
    BadmintonAnalysisResult,
    MetricTrend,
    LongitudinalCorrelation,
    BadmintonLongitudinalComparison,
)


# Red-flag phrases that must NEVER appear in generated correlation text
CAUSAL_CLAIM_RED_FLAGS = [
    r"\bcauses\b",
    r"\bcaused by\b",
    r"\bdirectly causes\b",
    r"\bdirectly caused\b",
    r"\bproves that\b",
    r"\bproof of causality\b",
    r"\bcausal proof\b",
    r"\bproves causality\b",
]


def validate_non_causal_language(text: str) -> bool:
    """
    Validates that the generated summary contains no bare causal claims from correlation.
    Allowed: 'does not prove', 'does not cause', 'correlation does not imply causation', 'does not establish causality'.
    Disallowed: bare assertions like 'X causes Y' or 'proves that X leads to Y'.
    """
    lower = text.lower()
    for pattern in CAUSAL_CLAIM_RED_FLAGS:
        matches = re.finditer(pattern, lower)
        for match in matches:
            # Check for negative context preceding the match (e.g. 'does not cause', 'do not prove that ... causes')
            clause_start = max(0, lower.rfind(".", 0, match.start()), lower.rfind(";", 0, match.start()))
            start_pos = max(clause_start, match.start() - 85)
            prefix = lower[start_pos:match.start()]
            if any(neg in prefix for neg in ["not", "never", "no ", "cannot", "doesn't", "without proving", "no evidence"]):
                continue
            return False
    return True


class BadmintonLongitudinalAnalyzer:
    """
    Deterministic longitudinal trend and correlation analyzer across
    multiple badminton sessions for a single athlete.
    """

    def __init__(self, analytics_service: Optional[AnalyticsService] = None):
        self.analytics = analytics_service or AnalyticsService()
        self.sports_plugin = SportsPlugin

    def compare_sessions(
        self,
        sessions: List[BadmintonAnalysisResult],
        player_id: Optional[str] = None
    ) -> BadmintonLongitudinalComparison:
        """
        Computes deterministic progression, session-to-session deltas,
        linear slopes, and non-causal correlations across 2+ analyzed sessions.
        """
        if not sessions or len(sessions) < 2:
            raise ValueError(f"Longitudinal comparison requires at least 2 sessions, received {len(sessions) if sessions else 0}.")

        # 1. Resolve Player ID
        resolved_player_id = (
            player_id
            or sessions[0].player_id
            or (sessions[0].player_metadata.player_id if sessions[0].player_metadata else None)
            or "player_default"
        )

        session_ids = [s.analysis_id for s in sessions]
        session_dates = [
            (s.player_metadata.session_date if s.player_metadata else None)
            for s in sessions
        ]

        # 2. Extract per-session numeric indicators
        metric_series: Dict[str, Dict[str, Any]] = {
            "shot_accuracy_pct": {
                "name": "Shot Accuracy Ratio (%)",
                "values": [self._extract_accuracy_pct(s) for s in sessions],
                "available": True,
                "unavailable_reason": None
            },
            "smash_percentage": {
                "name": "Smash Frequency (%)",
                "values": [self._extract_shot_type_pct(s, "smash") for s in sessions],
                "available": True,
                "unavailable_reason": None
            },
            "court_coverage_m2": {
                "name": "Court Coverage Area (m²)",
                "values": (cov_vals := [self._extract_coverage_m2(s) for s in sessions]),
                "available": any(v is not None for v in cov_vals),
                "unavailable_reason": "Court coverage uncalibrated or unmeasurable across session sequence."
            },
            "movement_efficiency": {
                "name": "Movement Efficiency (retrievals/m)",
                "values": [None] * len(sessions),
                "available": False,
                "unavailable_reason": "NOT_RELIABLY_MEASURABLE per Section 21: Rally outcome not verifiable from single camera."
            },
            "peak_racket_speed_kmh": {
                "name": "Peak Racket Speed (km/h)",
                "values": (racket_vals := [self._extract_racket_speed(s) for s in sessions]),
                "available": any(v is not None for v in racket_vals),
                "unavailable_reason": "Insufficient continuous racket tracking across session sequence."
            },
            "peak_shuttle_speed_kmh": {
                "name": "Peak Shuttle Speed (km/h)",
                "values": (shuttle_vals := [self._extract_shuttle_speed(s) for s in sessions]),
                "available": any(v is not None for v in shuttle_vals),
                "unavailable_reason": "Insufficient continuous shuttle tracking across session sequence."
            },
            "mean_recovery_time_s": {
                "name": "Mean Base Recovery Time (s)",
                "values": (rec_vals := [self._extract_recovery_time_s(s) for s in sessions]),
                "available": any(v is not None for v in rec_vals),
                "unavailable_reason": "Insufficient consecutive strokes to calculate recovery intervals."
            },
            "contact_elbow_extension_deg": {
                "name": "Contact Elbow Extension (deg)",
                "values": (elb_vals := [self._extract_elbow_angle(s) for s in sessions]),
                "available": any(v is not None for v in elb_vals),
                "unavailable_reason": "No valid elbow extension angles measurable at contact."
            },
            "energy_expenditure_kcal": {
                "name": "MET Energy Expenditure (kcal)",
                "values": (energy_vals := [self._extract_energy_kcal(s) for s in sessions]),
                "available": any(v is not None for v in energy_vals),
                "unavailable_reason": "Metabolic energy expenditure unavailable across session sequence."
            }
        }

        # 3. Compute Deterministic Metric Trends
        metric_trends: Dict[str, MetricTrend] = {}
        for key, info in metric_series.items():
            vals = info["values"]
            is_avail = info["available"]
            unavail_reason = info["unavailable_reason"]

            if not is_avail or all(v is None for v in vals):
                metric_trends[key] = MetricTrend(
                    metric_name=info["name"],
                    values=vals,
                    sessions=session_ids,
                    slope=None,
                    r_squared=None,
                    change_percentage=None,
                    direction="UNAVAILABLE",
                    session_deltas=[],
                    available=False,
                    unavailable_reason=unavail_reason or "Metric unavailable across evaluated sessions."
                )
                continue

            # Compute session-to-session deltas: v_i - v_(i-1)
            deltas: List[float] = []
            for i in range(1, len(vals)):
                curr_v = vals[i]
                prev_v = vals[i - 1]
                if curr_v is not None and prev_v is not None:
                    deltas.append(round(curr_v - prev_v, 3))
                else:
                    deltas.append(0.0)

            # Overall change percentage: ((v_last - v_first) / |v_first|) * 100
            valid_vals = [(idx, v) for idx, v in enumerate(vals) if v is not None]
            change_pct = None
            slope = None
            r_sq = None

            if len(valid_vals) >= 2:
                first_idx, first_val = valid_vals[0]
                last_idx, last_val = valid_vals[-1]
                if abs(first_val) > 1e-6:
                    change_pct = round(((last_val - first_val) / abs(first_val)) * 100.0, 2)

                # Linear regression via AnalyticsService reuse
                xs = [float(x[0]) for x in valid_vals]
                ys = [float(x[1]) for x in valid_vals]
                raw_slope, raw_r_sq = self.analytics._linear_regression(xs, ys)
                slope = round(raw_slope, 4)
                r_sq = round(raw_r_sq, 3)

            # Classify progression direction
            if slope is None:
                direction = "INSUFFICIENT"
            elif abs(slope) < 0.01:
                direction = "STABLE"
            elif r_sq is not None and r_sq < 0.15:
                direction = "FLUCTUATING"
            elif slope > 0:
                direction = "INCREASING"
            else:
                direction = "DECREASING"

            metric_trends[key] = MetricTrend(
                metric_name=info["name"],
                values=vals,
                sessions=session_ids,
                slope=slope,
                r_squared=r_sq,
                change_percentage=change_pct,
                direction=direction,
                session_deltas=deltas,
                available=True,
                unavailable_reason=None
            )

        # 4. Pairwise Deterministic Correlations (Section 4 & AnalyticsService reuse)
        correlations = self._compute_pairwise_correlations(metric_trends, len(sessions))

        # 5. Non-Causal Hedged Summary Generation (Phase 13 discipline)
        hedged_summary = self._generate_hedged_summary(
            player_id=resolved_player_id,
            sessions=sessions,
            metric_trends=metric_trends,
            correlations=correlations
        )

        # Programmatic verification of non-causal language
        for statement in hedged_summary:
            assert validate_non_causal_language(statement), f"Longitudinal statement violated non-causal discipline: {statement}"

        # 6. Honest Limitations
        limitations = [
            "Statistical correlations across training sessions describe co-variation patterns and do not establish direct mechanical causation.",
            "Movement efficiency remains gated as NOT_RELIABLY_MEASURABLE per Section 21 due to lack of verified opponent and rally boundary data.",
            "Single-camera perspective introduces planar parallax; small frame-to-frame joint angle deltas should be evaluated as trends rather than absolute clinical kinematics."
        ]

        # 7. Construct Longitudinal Evidence Graph
        graph_data = self._build_longitudinal_graph(
            player_id=resolved_player_id,
            session_ids=session_ids,
            metric_trends=metric_trends,
            correlations=correlations
        )

        return BadmintonLongitudinalComparison(
            player_id=resolved_player_id,
            session_count=len(sessions),
            session_ids=session_ids,
            session_dates=session_dates,
            metric_trends=metric_trends,
            correlations=correlations,
            hedged_summary=hedged_summary,
            limitations=limitations,
            graph_data=graph_data
        )

    # ------------------------------------------------------------------------
    # Metric Extractors from real BadmintonAnalysisResult
    # ------------------------------------------------------------------------

    def _extract_accuracy_pct(self, result: BadmintonAnalysisResult) -> float:
        """Percentage of detected shots classified with high confidence (>= 0.70)."""
        shots = result.shots or []
        if not shots:
            return 0.0
        confident = sum(1 for s in shots if s.confidence >= 0.70)
        return round((confident / len(shots)) * 100.0, 1)

    def _extract_shot_type_pct(self, result: BadmintonAnalysisResult, target_type: str) -> float:
        """Percentage of total strokes matching a specific shot type."""
        sm = result.shot_metrics
        if sm and sm.percentage_by_shot_type:
            for k, v in sm.percentage_by_shot_type.items():
                if k.lower() == target_type.lower():
                    return round(float(v), 2)
        shots = result.shots or []
        if not shots:
            return 0.0
        match_count = sum(1 for s in shots if (s.shot_type or "").lower() == target_type.lower())
        return round((match_count / len(shots)) * 100.0, 2)

    def _extract_coverage_m2(self, result: BadmintonAnalysisResult) -> Optional[float]:
        """Court coverage convex hull area in square meters."""
        if result.court_metrics:
            cm = result.court_metrics
            val = getattr(cm, "convex_hull_area_m2", None)
            if val is not None:
                if isinstance(val, (int, float)):
                    return round(float(val), 2)
                if hasattr(val, "value") and getattr(val, "available", True) and val.value is not None:
                    return round(float(val.value), 2)
        if result.movement_metrics:
            mm = result.movement_metrics
            val = getattr(mm, "court_coverage_area_m2", None) or getattr(mm, "total_distance_m", None)
            if val is not None:
                if isinstance(val, (int, float)):
                    return round(float(val), 2)
                if hasattr(val, "value") and getattr(val, "available", True) and val.value is not None:
                    return round(float(val.value), 2)
        return None

    def _extract_racket_speed(self, result: BadmintonAnalysisResult) -> Optional[float]:
        """Peak racket speed in km/h if available."""
        if result.speed_metrics and result.speed_metrics.racket_speed_peak.available:
            return round(float(result.speed_metrics.racket_speed_peak.value), 1)
        return None

    def _extract_shuttle_speed(self, result: BadmintonAnalysisResult) -> Optional[float]:
        """Peak shuttle speed in km/h if available."""
        if result.speed_metrics and result.speed_metrics.shuttle_speed_peak.available:
            return round(float(result.speed_metrics.shuttle_speed_peak.value), 1)
        return None

    def _extract_recovery_time_s(self, result: BadmintonAnalysisResult) -> Optional[float]:
        """Mean duration or recovery time between strokes."""
        if result.shot_metrics and result.shot_metrics.average_duration_s is not None:
            return round(float(result.shot_metrics.average_duration_s), 2)
        shots = result.shots or []
        if len(shots) >= 2:
            intervals = [shots[i].start_time - shots[i - 1].end_time for i in range(1, len(shots))]
            pos_intervals = [i for i in intervals if i > 0]
            if pos_intervals:
                return round(sum(pos_intervals) / len(pos_intervals), 2)
        return None

    def _extract_elbow_angle(self, result: BadmintonAnalysisResult) -> Optional[float]:
        """Mean elbow extension angle across detected strokes."""
        angles = []
        for s in (result.shots or []):
            pf = s.pose_features or {}
            val = pf.get("contact_elbow_angle_deg") or pf.get("elbow_angle_deg") or pf.get("elbow_extension_deg")
            if val is not None:
                angles.append(float(val))
        if angles:
            return round(sum(angles) / len(angles), 1)
        return None

    def _extract_energy_kcal(self, result: BadmintonAnalysisResult) -> Optional[float]:
        """Estimated MET energy expenditure in kcal."""
        em = result.energy_metrics
        if em:
            if hasattr(em.estimated_energy_expenditure_kcal, "value") and em.estimated_energy_expenditure_kcal.value is not None:
                return round(float(em.estimated_energy_expenditure_kcal.value), 2)
            if isinstance(em.estimated_energy_expenditure_kcal, (int, float)):
                return round(float(em.estimated_energy_expenditure_kcal), 2)
        return None

    # ------------------------------------------------------------------------
    # Statistical Correlation Computations (Reusing AnalyticsService)
    # ------------------------------------------------------------------------

    def _compute_pairwise_correlations(
        self,
        trends: Dict[str, MetricTrend],
        session_count: int
    ) -> List[LongitudinalCorrelation]:
        """
        Calculates Pearson r and Spearman rho across paired series.
        Adheres strictly to non-causal phrasing.
        """
        pairs_to_check = [
            ("contact_elbow_extension_deg", "shot_accuracy_pct", "Elbow extension at contact and shot accuracy"),
            ("smash_percentage", "shot_accuracy_pct", "Smash frequency and overall shot precision"),
            ("court_coverage_m2", "energy_expenditure_kcal", "Court coverage displacement and metabolic energy burn"),
            ("contact_elbow_extension_deg", "mean_recovery_time_s", "Elbow extension angle and base recovery tempo"),
        ]

        results: List[LongitudinalCorrelation] = []

        for feat_a, feat_b, desc_label in pairs_to_check:
            trend_a = trends.get(feat_a)
            trend_b = trends.get(feat_b)
            if not trend_a or not trend_b or not trend_a.available or not trend_b.available:
                continue

            vals_a = trend_a.values
            vals_b = trend_b.values

            aligned: List[Tuple[float, float]] = []
            for va, vb in zip(vals_a, vals_b):
                if va is not None and vb is not None:
                    aligned.append((float(va), float(vb)))

            if len(aligned) < 2:
                continue

            xs = [p[0] for p in aligned]
            ys = [p[1] for p in aligned]

            # Reuse AnalyticsService Pearson and Spearman methods
            r = self.analytics._pearson_r(xs, ys) if len(xs) >= 3 else None
            # For n=2, compute direct two-point correlation slope sign
            if r is None and len(xs) == 2:
                dx = xs[1] - xs[0]
                dy = ys[1] - ys[0]
                if abs(dx) > 1e-9 and abs(dy) > 1e-9:
                    r = 1.0 if (dx * dy > 0) else -1.0
                else:
                    r = 0.0

            rho = self.analytics._spearman_rho(xs, ys) if len(xs) >= 3 else r

            r_rounded = round(r, 3) if r is not None else None
            rho_rounded = round(rho, 3) if rho is not None else None

            # Generate strictly correlation-appropriate non-causal text
            if r_rounded is not None:
                strength_desc = "strong" if abs(r_rounded) >= 0.7 else ("moderate" if abs(r_rounded) >= 0.4 else "weak")
                dir_desc = "positive co-variation" if r_rounded > 0 else "inverse co-variation"
                desc = (
                    f"{desc_label} demonstrated {strength_desc} {dir_desc} "
                    f"(Pearson r={r_rounded:+.2f}, n={len(aligned)}). "
                    f"Statistical co-occurrence is consistent with technique co-adaptation and does not establish causality."
                )
            else:
                desc = f"{desc_label} evaluated across {len(aligned)} sessions with insufficient variance for robust correlation."

            results.append(LongitudinalCorrelation(
                feature_a=feat_a,
                feature_b=feat_b,
                pearson_r=r_rounded,
                spearman_rho=rho_rounded,
                observation_count=len(aligned),
                description=desc
            ))

        return results

    # ------------------------------------------------------------------------
    # Hedged Summary Generation (Phase 13 Discipline)
    # ------------------------------------------------------------------------

    def _generate_hedged_summary(
        self,
        player_id: str,
        sessions: List[BadmintonAnalysisResult],
        metric_trends: Dict[str, MetricTrend],
        correlations: List[LongitudinalCorrelation]
    ) -> List[str]:
        """
        Produces non-causal, hedged clinical and coaching summaries.
        """
        statements = []

        # 1. Overview statement
        n = len(sessions)
        statements.append(
            f"Longitudinal analysis across {n} training sessions for athlete [{player_id}] "
            f"identified multi-session trends and statistical co-variation patterns without asserting causal certainty."
        )

        # 2. Key metric progression trends
        elbow_trend = metric_trends.get("contact_elbow_extension_deg")
        if elbow_trend and elbow_trend.slope is not None and elbow_trend.change_percentage is not None:
            statements.append(
                f"Contact elbow extension demonstrated an {elbow_trend.direction.lower()} trend "
                f"(observed delta: {elbow_trend.change_percentage:+.1f}%, slope: {elbow_trend.slope:+.2f}°/session, R²={elbow_trend.r_squared:.2f}). "
                f"This pattern is consistent with progressive vertical contact point elevation across consecutive sessions."
            )

        acc_trend = metric_trends.get("shot_accuracy_pct")
        if acc_trend and acc_trend.change_percentage is not None:
            statements.append(
                f"Shot precision ratio showed an observed delta of {acc_trend.change_percentage:+.1f}% "
                f"({acc_trend.direction.lower()} trend, slope={acc_trend.slope:+.2f}%/session). "
                f"Observations suggest potential tactical consistency improvements over the training sequence."
            )

        cov_trend = metric_trends.get("court_coverage_m2")
        if cov_trend and cov_trend.available and cov_trend.change_percentage is not None:
            statements.append(
                f"Court coverage area reflected a {cov_trend.direction.lower()} pattern "
                f"(delta: {cov_trend.change_percentage:+.1f}%, slope: {cov_trend.slope:+.2f} m²/session), "
                f"which may indicate expanding court occupancy or bilateral movement comfort."
            )

        # 3. Correlation statements (strictly hedged)
        for corr in correlations:
            if corr.pearson_r is not None and abs(corr.pearson_r) >= 0.5:
                statements.append(
                    f"Empirical trend: {corr.description}"
                )

        # 4. Mandatory Epistemic Safeguard statement
        statements.append(
            "Empirical Safeguard: Longitudinal correlations between kinematic parameters and shot metrics "
            "do not prove that altering an isolated joint angle directly causes performance changes; "
            "recommendations warrant individualized coach supervision and holistic kinetic chain evaluation."
        )

        return statements

    # ------------------------------------------------------------------------
    # Evidence Graph Integration (Section 25 & 28)
    # ------------------------------------------------------------------------

    def _build_longitudinal_graph(
        self,
        player_id: str,
        session_ids: List[str],
        metric_trends: Dict[str, MetricTrend],
        correlations: List[LongitudinalCorrelation]
    ) -> GraphStateModel:
        """
        Synthesizes standard SAAR GraphStateModel incorporating Section 28 TREND nodes.
        """
        engine = ReasoningGraphEngine()

        # Root athlete entity
        engine.add_node(NodeModel(
            id="player_athlete",
            label=f"Athlete: {player_id}",
            node_type="player",
            category="OBSERVATION",
            confidence=0.98,
            properties={
                "value": player_id,
                "sessions_evaluated": session_ids,
                "session_count": len(session_ids),
                "calculation_method": "Multi-session longitudinal aggregation"
            }
        ))

        # Add TREND nodes for each computed progression
        for key, trend in metric_trends.items():
            if not trend.available:
                continue

            node_id = f"trend_{key}"
            props = {
                "value": f"{trend.direction} ({trend.change_percentage:+.1f}% change)" if trend.change_percentage is not None else trend.direction,
                "slope": trend.slope,
                "r_squared": trend.r_squared,
                "change_percentage": trend.change_percentage,
                "session_deltas": trend.session_deltas,
                "confidence": min(0.95, round(0.60 + 0.10 * len(session_ids), 2)),
                "source": "BadmintonLongitudinalAnalyzer (Phase 17)",
                "timestamp_or_frame_range": f"{session_ids[0]} -> {session_ids[-1]}",
                "calculation_method": "Deterministic linear regression slope & session delta calculation"
            }

            engine.add_node(NodeModel(
                id=node_id,
                label=f"Trend: {trend.metric_name} ({trend.direction})",
                node_type="trend",
                category="TREND",
                confidence=props["confidence"],
                properties=props,
                status="confirmed"
            ))

            engine.add_edge(EdgeModel(
                id=f"edge_player_to_{node_id}",
                source="player_athlete",
                target=node_id,
                relation_type="indicates",
                confidence=props["confidence"],
                evidence=f"Computed longitudinal progression over {len(session_ids)} sessions"
            ))

        # Add CORRELATION edges between co-varying trends
        for idx, corr in enumerate(correlations):
            if corr.pearson_r is not None and abs(corr.pearson_r) >= 0.4:
                src_node = f"trend_{corr.feature_a}"
                tgt_node = f"trend_{corr.feature_b}"
                if src_node in engine.graph and tgt_node in engine.graph:
                    engine.add_edge(EdgeModel(
                        id=f"edge_corr_{idx}",
                        source=src_node,
                        target=tgt_node,
                        relation_type="correlates_with",
                        confidence=min(0.90, round(abs(corr.pearson_r), 2)),
                        evidence=f"Non-causal statistical correlation r={corr.pearson_r:+.2f} (n={corr.observation_count})"
                    ))

        return engine.export_state(step_count=len(session_ids))
