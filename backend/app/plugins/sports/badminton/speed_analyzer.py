"""
Badminton Speed Analyzer Engine.
Computes calibrated inter-frame velocities for shuttlecock and racket head per Sections 13, 14, 17, and 18.

Key Design Requirements:
1. Compute v_i = ||p_i - p_(i-1)|| / (t_i - t_(i-1)) between consecutive calibrated positions.
2. Apply strict, physically-grounded outlier rejection with documented real-world literature benchmarks.
3. Report max/average observed speed with uncertainty ranges and the count of valid trajectory segments.
4. Report Peak Racket Speed separately from Peak Shuttle Speed — never conflated (Section 14).
5. Degrade to exact string "Speed estimate unavailable — insufficient continuous tracking" (Section 13)
   when tracking data does not clear confidence/continuity thresholds.
"""
import math
from typing import List, Optional, Tuple, Dict, Any
import numpy as np

from .schemas import Metric, CourtCalibration, ShotResult, SpeedMetrics
from .racket_tracker import RacketTrackingSummary, RacketFrameRecord
from .shuttle_tracker import ShuttleTrackingSummary, ShuttleFrameRecord

# Exact fallback string required by Section 13
FALLBACK_UNAVAILABLE_MESSAGE = "Speed estimate unavailable — insufficient continuous tracking"

# Minimum valid consecutive inter-frame segments required for physical speed calculation
MIN_VALID_SEGMENTS = 2

# Maximum allowable inter-frame time gap in seconds (~6 dropped frames at 30 FPS)
MAX_INTERFRAME_GAP_S = 0.20

# ----------------------------------------------------------------------
# Physical / Physiological Upper Bounds & Literature Citations
# ----------------------------------------------------------------------

# Real-world physiological & physical upper bound citation (Guinness World Records / BWF literature):
# The Guinness World Record for the fastest badminton smash is 565.0 km/h (156.9 m/s)
# recorded by Satwiksairaj Rankireddy in 2023 under controlled laboratory test conditions (Yonex Tokyo).
# In official tournament match play, the fastest recorded smashes reach ~493.0 km/h (136.9 m/s)
# (Tan Boon Heong, 2013) and ~400-426 km/h in top-tier competition.
# Any inter-frame calculated velocity exceeding 160.0 m/s (576.0 km/h) is physically impossible
# for a badminton shuttlecock in atmosphere and is rejected as an optical tracking / detection anomaly.
SHUTTLE_MAX_SPEED_KM_H = 576.0  # 160.0 m/s

# Biomechanical upper bound citation (Sports Biomechanics literature):
# Elite badminton racket head speed during maximum-effort overhead jump smashes typically peaks
# between 180 km/h and 230 km/h (50 - 64 m/s), with experimental laboratory records topping at
# ~250 km/h (~69.4 m/s) (e.g., Kwan et al., "Three-dimensional kinematic analysis of badminton
# smash stroke", Sports Biomechanics, 2010; Phomsoupha & Laffaye, "The Science of Badminton",
# Sports Medicine, 2015). Any estimated racket head displacement velocity exceeding 80.0 m/s
# (288.0 km/h) is physically implausible and is rejected as a tracking glitch or motion blur artifact.
RACKET_MAX_SPEED_KM_H = 288.0  # 80.0 m/s


class SpeedSegment:
    """Individual consecutive inter-frame displacement segment with velocity and outlier status."""
    def __init__(
        self,
        from_frame: int,
        to_frame: int,
        t_from_s: float,
        t_to_s: float,
        p_from_m: Tuple[float, float],
        p_to_m: Tuple[float, float],
        dt_s: float,
        dist_m: float,
        speed_m_s: float,
        speed_km_h: float,
        is_outlier: bool,
        rejection_reason: Optional[str] = None
    ):
        self.from_frame = from_frame
        self.to_frame = to_frame
        self.t_from_s = t_from_s
        self.t_to_s = t_to_s
        self.p_from_m = p_from_m
        self.p_to_m = p_to_m
        self.dt_s = dt_s
        self.dist_m = dist_m
        self.speed_m_s = speed_m_s
        self.speed_km_h = speed_km_h
        self.is_outlier = is_outlier
        self.rejection_reason = rejection_reason

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_frame": self.from_frame,
            "to_frame": self.to_frame,
            "t_from_s": round(self.t_from_s, 3),
            "t_to_s": round(self.t_to_s, 3),
            "p_from_m": [round(self.p_from_m[0], 3), round(self.p_from_m[1], 3)],
            "p_to_m": [round(self.p_to_m[0], 3), round(self.p_to_m[1], 3)],
            "dt_s": round(self.dt_s, 4),
            "dist_m": round(self.dist_m, 3),
            "speed_km_h": round(self.speed_km_h, 1),
            "is_outlier": self.is_outlier,
            "rejection_reason": self.rejection_reason
        }


class BadmintonSpeedAnalyzer:
    """
    Computes calibrated consecutive-position speed kinematics for shuttle and racket head.
    Enforces Section 13 honest fallback and Section 14 non-conflation of metrics.
    """

    def compute_segment_velocities(
        self,
        tracked_points: List[Dict[str, Any]],
        max_speed_km_h: float,
        max_gap_s: float = MAX_INTERFRAME_GAP_S
    ) -> Tuple[List[SpeedSegment], List[SpeedSegment]]:
        """
        Computes v_i = ||p_i - p_(i-1)|| / (t_i - t_(i-1)) across sorted consecutive points.
        Applies physical outlier rejection and returns (valid_segments, rejected_segments).
        
        tracked_points must contain:
        [{"frame_index": int, "timestamp_s": float, "pos_m": (x, y), "pos_px": (px, py)}]
        """
        if len(tracked_points) < 2:
            return [], []

        # Sort by timestamp
        sorted_pts = sorted(tracked_points, key=lambda p: p["timestamp_s"])
        valid_segments: List[SpeedSegment] = []
        rejected_segments: List[SpeedSegment] = []

        for i in range(1, len(sorted_pts)):
            p_prev = sorted_pts[i - 1]
            p_curr = sorted_pts[i]

            t_from = float(p_prev["timestamp_s"])
            t_to = float(p_curr["timestamp_s"])
            dt = t_to - t_from

            if dt <= 0.0001:
                # Same frame or negative delta
                continue

            if dt > max_gap_s:
                # Temporal discontinuity: skip without asserting constant speed
                continue

            x0, y0 = p_prev["pos_m"]
            x1, y1 = p_curr["pos_m"]
            dist_m = float(math.hypot(x1 - x0, y1 - y0))
            speed_m_s = dist_m / dt
            speed_km_h = speed_m_s * 3.6

            # Outlier rejection check
            if speed_km_h > max_speed_km_h:
                seg = SpeedSegment(
                    from_frame=p_prev["frame_index"],
                    to_frame=p_curr["frame_index"],
                    t_from_s=t_from,
                    t_to_s=t_to,
                    p_from_m=(x0, y0),
                    p_to_m=(x1, y1),
                    dt_s=dt,
                    dist_m=dist_m,
                    speed_m_s=speed_m_s,
                    speed_km_h=speed_km_h,
                    is_outlier=True,
                    rejection_reason=f"Exceeds physical upper bound ({max_speed_km_h} km/h)"
                )
                rejected_segments.append(seg)
            else:
                seg = SpeedSegment(
                    from_frame=p_prev["frame_index"],
                    to_frame=p_curr["frame_index"],
                    t_from_s=t_from,
                    t_to_s=t_to,
                    p_from_m=(x0, y0),
                    p_to_m=(x1, y1),
                    dt_s=dt,
                    dist_m=dist_m,
                    speed_m_s=speed_m_s,
                    speed_km_h=speed_km_h,
                    is_outlier=False,
                    rejection_reason=None
                )
                valid_segments.append(seg)

        return valid_segments, rejected_segments

    def compute_speed_statistics(
        self,
        valid_segments: List[SpeedSegment],
        metric_name_peak: str,
        metric_name_mean: str,
        is_calibrated: bool,
        is_tracking_usable: bool
    ) -> Tuple[Metric, Metric, Optional[List[float]], Optional[List[float]], int]:
        """
        Aggregates valid segments into peak and mean Metric objects with uncertainty ranges.
        If thresholds are not met, returns standardized Section 13 fallback metrics.
        """
        # Fallback check: court calibration, tracker usability, or minimum segments
        if not is_calibrated or not is_tracking_usable or len(valid_segments) < MIN_VALID_SEGMENTS:
            peak_m = Metric(
                name=metric_name_peak,
                value=None,
                unit="km/h",
                confidence="LOW",
                method="calibrated_consecutive_displacement",
                available=False,
                unavailable_reason=FALLBACK_UNAVAILABLE_MESSAGE,
                uncertainty_range=None,
                segments_used=len(valid_segments)
            )
            mean_m = Metric(
                name=metric_name_mean,
                value=None,
                unit="km/h",
                confidence="LOW",
                method="calibrated_consecutive_displacement",
                available=False,
                unavailable_reason=FALLBACK_UNAVAILABLE_MESSAGE,
                uncertainty_range=None,
                segments_used=len(valid_segments)
            )
            return peak_m, mean_m, None, None, len(valid_segments)

        speeds = [s.speed_km_h for s in valid_segments]
        peak_val = round(float(np.max(speeds)), 1)
        mean_val = round(float(np.mean(speeds)), 1)
        std_val = float(np.std(speeds)) if len(speeds) > 1 else 0.0

        # Uncertainty calculation:
        # Optical uncertainty combines standard error of the mean with a 5% homography projection allowance
        uncertainty = round(max(std_val / math.sqrt(len(speeds)), 0.05 * mean_val), 1)

        peak_range = [round(max(0.0, peak_val - uncertainty), 1), round(peak_val + uncertainty, 1)]
        mean_range = [round(max(0.0, mean_val - uncertainty), 1), round(mean_val + uncertainty, 1)]

        confidence = "HIGH" if len(speeds) >= 10 else "MEDIUM"
        src_info = f"Computed from N={len(speeds)} consecutive segments (uncertainty ±{uncertainty} km/h)"

        peak_m = Metric(
            name=metric_name_peak,
            value=peak_val,
            unit="km/h",
            confidence=confidence,
            method="calibrated_consecutive_displacement",
            source=src_info,
            available=True,
            unavailable_reason=None,
            uncertainty_range=peak_range,
            segments_used=len(speeds)
        )
        mean_m = Metric(
            name=metric_name_mean,
            value=mean_val,
            unit="km/h",
            confidence=confidence,
            method="calibrated_consecutive_displacement",
            source=src_info,
            available=True,
            unavailable_reason=None,
            uncertainty_range=mean_range,
            segments_used=len(speeds)
        )

        return peak_m, mean_m, peak_range, mean_range, len(speeds)

    def analyze_speeds(
        self,
        shots: List[ShotResult],
        racket_summary: Optional[RacketTrackingSummary],
        shuttle_summary: Optional[ShuttleTrackingSummary],
        court_calibration: Optional[CourtCalibration],
        fps: float = 30.0
    ) -> Tuple[SpeedMetrics, List[ShotResult], List[str]]:
        """
        Orchestrates shot-level and clip-level speed calculations.
        Wired directly into BadmintonPipeline.
        """
        is_calibrated = bool(court_calibration and court_calibration.is_calibrated)
        racket_usable = bool(racket_summary and racket_summary.is_usable)
        shuttle_usable = bool(shuttle_summary and shuttle_summary.is_usable)

        # ------------------------------------------------------------------
        # 1. Gather all tracked points across the entire clip
        # ------------------------------------------------------------------
        clip_racket_pts: List[Dict[str, Any]] = []
        if racket_summary and racket_summary.per_frame_records:
            for r in racket_summary.per_frame_records:
                if r.is_detected and r.racket_head_m and len(r.racket_head_m) >= 2:
                    clip_racket_pts.append({
                        "frame_index": r.frame_index,
                        "timestamp_s": r.timestamp_ms / 1000.0,
                        "pos_m": (r.racket_head_m[0], r.racket_head_m[1]),
                        "pos_px": r.racket_head_px
                    })

        clip_shuttle_pts: List[Dict[str, Any]] = []
        if shuttle_summary and shuttle_summary.per_frame_records:
            for s in shuttle_summary.per_frame_records:
                if s.is_detected and s.shuttle_m and len(s.shuttle_m) >= 2:
                    clip_shuttle_pts.append({
                        "frame_index": s.frame_index,
                        "timestamp_s": s.timestamp_ms / 1000.0,
                        "pos_m": (s.shuttle_m[0], s.shuttle_m[1]),
                        "pos_px": s.shuttle_px
                    })

        # ------------------------------------------------------------------
        # 2. Per-Shot Speed Analysis
        # ------------------------------------------------------------------
        updated_shots: List[ShotResult] = []
        for shot in shots:
            shot_copy = shot.model_copy(deep=True)
            shot_start = shot.start_time
            shot_end = shot.end_time
            contact_t = shot.contact_time or ((shot_start + shot_end) / 2.0)

            # Racket head points within shot contact window (contact ± 0.25s or start..end)
            r_window_start = max(0.0, contact_t - 0.25)
            r_window_end = contact_t + 0.25
            shot_racket_pts = [
                p for p in clip_racket_pts
                if (shot.evidence_frames and p["frame_index"] in shot.evidence_frames) or
                   (r_window_start <= p["timestamp_s"] <= r_window_end)
            ]

            r_val_segs, r_rej_segs = self.compute_segment_velocities(
                tracked_points=shot_racket_pts,
                max_speed_km_h=RACKET_MAX_SPEED_KM_H
            )
            r_peak, _, r_range, _, r_n = self.compute_speed_statistics(
                valid_segments=r_val_segs,
                metric_name_peak="racket_speed",
                metric_name_mean="racket_speed_mean",
                is_calibrated=is_calibrated,
                is_tracking_usable=racket_usable
            )
            shot_copy.racket_speed = r_peak

            # Shuttle points within shot window (contact..end or start..end)
            shot_shuttle_pts = [
                p for p in clip_shuttle_pts
                if (shot.evidence_frames and p["frame_index"] in shot.evidence_frames) or
                   (contact_t <= p["timestamp_s"] <= shot_end + 0.10)
            ]

            s_val_segs, s_rej_segs = self.compute_segment_velocities(
                tracked_points=shot_shuttle_pts,
                max_speed_km_h=SHUTTLE_MAX_SPEED_KM_H
            )
            s_peak, _, s_range, _, s_n = self.compute_speed_statistics(
                valid_segments=s_val_segs,
                metric_name_peak="shuttle_speed",
                metric_name_mean="shuttle_speed_mean",
                is_calibrated=is_calibrated,
                is_tracking_usable=shuttle_usable
            )
            shot_copy.shuttle_speed = s_peak

            # Store traceability metadata in trajectory_features
            shot_copy.trajectory_features["racket_speed_km_h"] = r_peak.value
            shot_copy.trajectory_features["racket_uncertainty_range"] = r_range
            shot_copy.trajectory_features["racket_segments_used"] = r_n
            shot_copy.trajectory_features["racket_supporting_points"] = [
                {"frame": p["frame_index"], "t_s": round(p["timestamp_s"], 3), "pos_m": p["pos_m"]}
                for p in shot_racket_pts
            ]
            shot_copy.trajectory_features["racket_valid_segments"] = [s.to_dict() for s in r_val_segs]

            shot_copy.trajectory_features["shuttle_speed_km_h"] = s_peak.value
            shot_copy.trajectory_features["shuttle_uncertainty_range"] = s_range
            shot_copy.trajectory_features["shuttle_segments_used"] = s_n
            shot_copy.trajectory_features["shuttle_supporting_points"] = [
                {"frame": p["frame_index"], "t_s": round(p["timestamp_s"], 3), "pos_m": p["pos_m"]}
                for p in shot_shuttle_pts
            ]
            shot_copy.trajectory_features["shuttle_valid_segments"] = [s.to_dict() for s in s_val_segs]

            updated_shots.append(shot_copy)

        # ------------------------------------------------------------------
        # 3. Clip-Level Aggregate Speed Analysis
        # ------------------------------------------------------------------
        clip_r_val, clip_r_rej = self.compute_segment_velocities(
            tracked_points=clip_racket_pts,
            max_speed_km_h=RACKET_MAX_SPEED_KM_H
        )
        r_peak_m, r_mean_m, r_peak_range, _, r_segs_used = self.compute_speed_statistics(
            valid_segments=clip_r_val,
            metric_name_peak="racket_speed_peak",
            metric_name_mean="racket_speed_mean",
            is_calibrated=is_calibrated,
            is_tracking_usable=racket_usable
        )

        clip_s_val, clip_s_rej = self.compute_segment_velocities(
            tracked_points=clip_shuttle_pts,
            max_speed_km_h=SHUTTLE_MAX_SPEED_KM_H
        )
        s_peak_m, s_mean_m, s_peak_range, _, s_segs_used = self.compute_speed_statistics(
            valid_segments=clip_s_val,
            metric_name_peak="shuttle_speed_peak",
            metric_name_mean="shuttle_speed_mean",
            is_calibrated=is_calibrated,
            is_tracking_usable=shuttle_usable
        )

        wrist_speed_metric = (
            racket_summary.wrist_speed_peak
            if racket_summary else Metric(
                name="wrist_speed_peak",
                unit="km/h",
                available=False,
                unavailable_reason="Wrist landmark data unavailable."
            )
        )

        aggregate_speed_metrics = SpeedMetrics(
            racket_speed_peak=r_peak_m,
            racket_speed_mean=r_mean_m,
            shuttle_speed_peak=s_peak_m,
            shuttle_speed_mean=s_mean_m,
            wrist_speed_peak=wrist_speed_metric,
            racket_uncertainty_range_km_h=r_peak_range,
            shuttle_uncertainty_range_km_h=s_peak_range,
            racket_segments_used=r_segs_used,
            shuttle_segments_used=s_segs_used
        )

        # ------------------------------------------------------------------
        # 4. Synthesize Natural-Language Findings (Section 14: Never Conflate!)
        # ------------------------------------------------------------------
        findings: List[str] = []

        # Peak Shuttle Speed finding
        if s_peak_m.available and s_peak_m.value is not None:
            findings.append(
                f"Peak Shuttle Speed: {s_peak_m.value} km/h "
                f"(range: {s_peak_range[0]}–{s_peak_range[1]} km/h across {s_segs_used} segments)."
            )
        else:
            findings.append(f"Peak Shuttle Speed: {s_peak_m.unavailable_reason}.")

        # Peak Racket Speed finding (strictly separate)
        if r_peak_m.available and r_peak_m.value is not None:
            findings.append(
                f"Peak Racket Speed: {r_peak_m.value} km/h "
                f"(range: {r_peak_range[0]}–{r_peak_range[1]} km/h across {r_segs_used} segments)."
            )
        else:
            findings.append(f"Peak Racket Speed: {r_peak_m.unavailable_reason}.")

        # Peak Wrist Speed finding (Section 14 separation)
        if wrist_speed_metric.available and wrist_speed_metric.value is not None:
            findings.append(f"Peak Wrist Speed: {wrist_speed_metric.value} km/h.")

        return aggregate_speed_metrics, updated_shots, findings
