"""
Saar — Deterministic Analytics Service
Computes correlations, trends, anomalies, and intervention effects.
Pure statistics — NO LLM calls. Math only.
"""
import math
import statistics
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

from ..models.saar_models import (
    Observation, Relationship, RelationshipType, Evidence, EvidenceType,
    TrendResult, TrendDirection, Feature, SemanticRole
)


class AnalyticsService:
    """Deterministic statistical analysis engine."""

    # ------------------------------------------------------------------
    # Correlation Discovery
    # ------------------------------------------------------------------

    def discover_correlations(
        self,
        observations: List[Observation],
        features: List[Feature],
        min_observations: int = 5
    ) -> List[Relationship]:
        """Discover pairwise correlations between numeric features."""
        # Group observations by timestamp
        time_series = self._build_time_series(observations)
        numeric_features = [f.name for f in features if f.semantic_role not in (
            SemanticRole.IDENTIFIER, SemanticRole.TEMPORAL
        )]

        relationships = []
        checked = set()

        for i, feat_a in enumerate(numeric_features):
            for feat_b in numeric_features[i + 1:]:
                pair_key = tuple(sorted([feat_a, feat_b]))
                if pair_key in checked:
                    continue
                checked.add(pair_key)

                pairs = self._get_paired_values(time_series, feat_a, feat_b)
                if len(pairs) < min_observations:
                    continue

                xs = [p[0] for p in pairs]
                ys = [p[1] for p in pairs]

                r = self._pearson_r(xs, ys)
                if r is None or abs(r) < 0.3:
                    continue

                rho = self._spearman_rho(xs, ys)
                strength = abs(r)
                direction = "positive" if r > 0 else "negative"

                # Heuristic confidence based on strength and sample size
                confidence = min(0.95, strength * 0.6 + min(len(pairs) / 50, 0.35))

                rel = Relationship(
                    source_feature=feat_a,
                    target_feature=feat_b,
                    relationship_type=RelationshipType.CORRELATION,
                    direction=direction,
                    strength=round(r, 3),
                    confidence=round(confidence, 3),
                    observation_count=len(pairs),
                    causal_claim=False,
                    description=f"{'Strong' if strength > 0.7 else 'Moderate'} {direction} correlation (r={r:.2f}, n={len(pairs)}). Spearman ρ={rho:.2f}." if rho else None,
                )
                relationships.append(rel)

        # Sort by absolute strength
        relationships.sort(key=lambda r: abs(r.strength or 0), reverse=True)
        return relationships

    # ------------------------------------------------------------------
    # Trend Detection
    # ------------------------------------------------------------------

    def detect_trends(
        self,
        observations: List[Observation],
        features: List[Feature],
        min_observations: int = 4
    ) -> List[TrendResult]:
        """Detect trends (increasing/decreasing/stable) in numeric features."""
        time_series = self._build_time_series(observations)
        results = []

        numeric_features = [f.name for f in features if f.semantic_role not in (
            SemanticRole.IDENTIFIER, SemanticRole.TEMPORAL
        )]

        for feat_name in numeric_features:
            values = []
            for ts in sorted(time_series.keys()):
                v = time_series[ts].get(feat_name)
                if v is not None:
                    try:
                        values.append(float(v))
                    except (ValueError, TypeError):
                        pass

            if len(values) < min_observations:
                results.append(TrendResult(
                    feature_name=feat_name,
                    direction=TrendDirection.INSUFFICIENT,
                    observation_count=len(values),
                ))
                continue

            # Linear regression slope
            xs = list(range(len(values)))
            slope, r_sq = self._linear_regression(xs, values)

            # Classify trend
            if r_sq < 0.15:
                direction = TrendDirection.FLUCTUATING
            elif abs(slope) < 0.01 * (max(values) - min(values) + 1e-9):
                direction = TrendDirection.STABLE
            elif slope > 0:
                direction = TrendDirection.INCREASING
            else:
                direction = TrendDirection.DECREASING

            results.append(TrendResult(
                feature_name=feat_name,
                direction=direction,
                slope=round(slope, 4),
                r_squared=round(r_sq, 3),
                observation_count=len(values),
                description=f"{feat_name} is {direction.value} (slope={slope:.4f}, R²={r_sq:.3f}, n={len(values)}).",
            ))

        return results

    # ------------------------------------------------------------------
    # Anomaly Detection
    # ------------------------------------------------------------------

    def detect_anomalies(
        self,
        observations: List[Observation],
        features: List[Feature],
        z_threshold: float = 2.0
    ) -> List[Dict[str, Any]]:
        """Detect anomalous observations using z-score deviation."""
        grouped: Dict[str, List[Tuple[Optional[str], float]]] = defaultdict(list)

        for obs in observations:
            try:
                val = float(obs.value)
                grouped[obs.feature_name].append((obs.timestamp, val))
            except (ValueError, TypeError):
                pass

        anomalies = []
        for feat_name, ts_vals in grouped.items():
            if len(ts_vals) < 5:
                continue
            vals = [v for _, v in ts_vals]
            mean = statistics.mean(vals)
            std = statistics.stdev(vals)
            if std < 1e-9:
                continue

            for ts, v in ts_vals:
                z = abs(v - mean) / std
                if z >= z_threshold:
                    anomalies.append({
                        "feature": feat_name,
                        "timestamp": ts,
                        "value": v,
                        "mean": round(mean, 3),
                        "std": round(std, 3),
                        "z_score": round(z, 2),
                        "deviation": "above" if v > mean else "below",
                        "description": f"Unusual {feat_name} value ({v}) is {z:.1f}σ {'above' if v > mean else 'below'} mean ({mean:.1f}).",
                    })

        anomalies.sort(key=lambda a: a["z_score"], reverse=True)
        return anomalies

    # ------------------------------------------------------------------
    # Intervention (Before/After) Analysis
    # ------------------------------------------------------------------

    def analyze_interventions(
        self,
        observations: List[Observation],
        features: List[Feature],
        window: int = 5
    ) -> List[Dict[str, Any]]:
        """Analyze before/after effects of intervention events."""
        time_series = self._build_time_series(observations)
        sorted_timestamps = sorted(time_series.keys())

        # Find intervention columns
        intervention_features = [f.name for f in features if f.semantic_role == SemanticRole.INTERVENTION]
        state_features = [f.name for f in features if f.semantic_role == SemanticRole.STATE]

        if not intervention_features or not state_features:
            return []

        results = []
        for intv_feat in intervention_features:
            # Find timestamps where intervention occurred
            intv_times = []
            for i, ts in enumerate(sorted_timestamps):
                val = time_series[ts].get(intv_feat)
                if val is not None:
                    try:
                        fval = float(val)
                        if fval > 0:
                            intv_times.append((i, ts))
                    except (ValueError, TypeError):
                        s = str(val).strip().lower()
                        if s in ("yes", "true", "1", "applied"):
                            intv_times.append((i, ts))

            for idx, intv_ts in intv_times:
                for state_feat in state_features:
                    before_vals = []
                    after_vals = []
                    for j in range(max(0, idx - window), idx):
                        v = time_series[sorted_timestamps[j]].get(state_feat)
                        if v is not None:
                            try:
                                before_vals.append(float(v))
                            except (ValueError, TypeError):
                                pass
                    for j in range(idx + 1, min(len(sorted_timestamps), idx + window + 1)):
                        v = time_series[sorted_timestamps[j]].get(state_feat)
                        if v is not None:
                            try:
                                after_vals.append(float(v))
                            except (ValueError, TypeError):
                                pass

                    if len(before_vals) >= 2 and len(after_vals) >= 2:
                        before_mean = statistics.mean(before_vals)
                        after_mean = statistics.mean(after_vals)
                        delta = after_mean - before_mean
                        direction = "increased" if delta > 0 else "decreased" if delta < 0 else "unchanged"

                        results.append({
                            "intervention": intv_feat,
                            "intervention_timestamp": intv_ts,
                            "target_feature": state_feat,
                            "before_mean": round(before_mean, 3),
                            "after_mean": round(after_mean, 3),
                            "delta": round(delta, 3),
                            "direction": direction,
                            "before_n": len(before_vals),
                            "after_n": len(after_vals),
                            "causal_claim": False,
                            "description": f"{state_feat} {direction} after {intv_feat} (Δ={delta:+.3f}). Before: {before_mean:.2f} (n={len(before_vals)}), After: {after_mean:.2f} (n={len(after_vals)}). Causal link NOT established.",
                        })

        return results

    # ------------------------------------------------------------------
    # Statistical Primitives
    # ------------------------------------------------------------------

    def _build_time_series(self, observations: List[Observation]) -> Dict[str, Dict[str, Any]]:
        """Group observations into {timestamp: {feature: value}} map."""
        ts_map: Dict[str, Dict[str, Any]] = defaultdict(dict)
        for obs in observations:
            key = obs.timestamp or obs.observation_id
            ts_map[key][obs.feature_name] = obs.value
        return dict(ts_map)

    def _get_paired_values(self, ts_map: Dict[str, Dict[str, Any]], feat_a: str, feat_b: str) -> List[Tuple[float, float]]:
        """Get aligned (a, b) pairs where both features have values."""
        pairs = []
        for ts_data in ts_map.values():
            va, vb = ts_data.get(feat_a), ts_data.get(feat_b)
            if va is not None and vb is not None:
                try:
                    pairs.append((float(va), float(vb)))
                except (ValueError, TypeError):
                    pass
        return pairs

    def _pearson_r(self, xs: List[float], ys: List[float]) -> Optional[float]:
        """Compute Pearson correlation coefficient."""
        n = len(xs)
        if n < 3:
            return None
        mx, my = statistics.mean(xs), statistics.mean(ys)
        sx = math.sqrt(sum((x - mx) ** 2 for x in xs) / (n - 1)) if n > 1 else 0
        sy = math.sqrt(sum((y - my) ** 2 for y in ys) / (n - 1)) if n > 1 else 0
        if sx < 1e-12 or sy < 1e-12:
            return None
        cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (n - 1)
        return cov / (sx * sy)

    def _spearman_rho(self, xs: List[float], ys: List[float]) -> Optional[float]:
        """Compute Spearman rank correlation."""
        n = len(xs)
        if n < 3:
            return None
        rx = self._rank(xs)
        ry = self._rank(ys)
        return self._pearson_r(rx, ry)

    def _rank(self, vals: List[float]) -> List[float]:
        """Assign ranks to values (average for ties)."""
        indexed = sorted(enumerate(vals), key=lambda x: x[1])
        ranks = [0.0] * len(vals)
        i = 0
        while i < len(indexed):
            j = i
            while j < len(indexed) and indexed[j][1] == indexed[i][1]:
                j += 1
            avg_rank = (i + j + 1) / 2.0
            for k in range(i, j):
                ranks[indexed[k][0]] = avg_rank
            i = j
        return ranks

    def _linear_regression(self, xs: List[float], ys: List[float]) -> Tuple[float, float]:
        """Simple linear regression returning (slope, r_squared)."""
        n = len(xs)
        if n < 2:
            return 0.0, 0.0
        mx = sum(xs) / n
        my = sum(ys) / n
        ss_xy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        ss_xx = sum((x - mx) ** 2 for x in xs)
        ss_yy = sum((y - my) ** 2 for y in ys)
        if ss_xx < 1e-12:
            return 0.0, 0.0
        slope = ss_xy / ss_xx
        r_sq = (ss_xy ** 2) / (ss_xx * ss_yy) if ss_yy > 1e-12 else 0.0
        return slope, max(0, min(1, r_sq))
