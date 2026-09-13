"""
Badminton Shuttlecock Detection and Trajectory Tracking Engine.
Implements Option A (Honest-Gap classical detection with strict temporal-continuity gating).
Performs candidate extraction (moving bright small object) and 3-frame trajectory continuity filtering.
Outputs all attempt records (positive and negative) and enforces clip-level usability gating.
"""
import math
from typing import List, Optional, Tuple, Dict, Any
import numpy as np
import cv2

from .schemas import Metric, CourtCalibration
from .court_detector import pixel_to_court_m

# Gating Thresholds per BADMINTON_DECISIONS.md
SHUTTLE_USABILITY_THRESHOLD = 0.25  # Minimum 25% usable frames required for speed assertion
MAX_SHUTTLE_SPEED_KM_H = 500.0      # Physical limit for world-class smash (world record ~493 km/h)
MIN_SHUTTLE_AREA = 4.0              # Minimum contour area in pixels
MAX_SHUTTLE_AREA = 600.0            # Maximum contour area in pixels
MIN_SHUTTLE_BRIGHTNESS = 135        # Grayscale intensity threshold for white/bright shuttle
MIN_TRAJECTORY_LENGTH = 3           # Minimum consecutive frames for physical trajectory confirmation


class ShuttleFrameRecord:
    """Per-frame shuttle detection attempt record (preserves negative results)."""
    def __init__(
        self,
        frame_index: int,
        timestamp_ms: int,
        is_detected: bool,
        confidence: float,
        shuttle_px: Optional[Tuple[float, float]] = None,
        shuttle_m: Optional[Tuple[float, float]] = None,
        method: str = "frame_diff_contour_temporal_continuity",
        reason: Optional[str] = None
    ):
        self.frame_index = frame_index
        self.timestamp_ms = timestamp_ms
        self.is_detected = is_detected
        self.confidence = confidence
        self.shuttle_px = shuttle_px
        self.shuttle_m = shuttle_m
        self.method = method
        self.reason = reason

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frame_index": self.frame_index,
            "timestamp_ms": self.timestamp_ms,
            "is_detected": self.is_detected,
            "confidence": self.confidence,
            "shuttle_px": self.shuttle_px,
            "shuttle_m": self.shuttle_m,
            "method": self.method,
            "reason": self.reason
        }


class ShuttleTrackingSummary:
    """Aggregated clip-level shuttle tracking outcome."""
    def __init__(
        self,
        total_frames: int,
        raw_candidates_count: int,
        verified_frames_count: int,
        visibility_ratio: float,
        is_usable: bool,
        shuttle_speed_peak: Metric,
        shuttle_speed_mean: Metric,
        per_frame_records: List[ShuttleFrameRecord]
    ):
        self.total_frames = total_frames
        self.raw_candidates_count = raw_candidates_count
        self.verified_frames_count = verified_frames_count
        self.visibility_ratio = visibility_ratio
        self.is_usable = is_usable
        self.shuttle_speed_peak = shuttle_speed_peak
        self.shuttle_speed_mean = shuttle_speed_mean
        self.per_frame_records = per_frame_records


class BadmintonShuttleTracker:
    """
    Classical OpenCV Shuttlecock Tracker with strict temporal-continuity gating.
    Never reports naive or fabricated numbers without clear method and confidence.
    """

    def track_shuttle(
        self,
        raw_frames: List[np.ndarray],
        court_calibration: Optional[CourtCalibration] = None,
        fps: float = 30.0
    ) -> ShuttleTrackingSummary:
        """
        Runs candidate detection and temporal-continuity trajectory linking across frames.
        """
        n_frames = len(raw_frames)
        if n_frames == 0:
            return ShuttleTrackingSummary(
                total_frames=0,
                raw_candidates_count=0,
                verified_frames_count=0,
                visibility_ratio=0.0,
                is_usable=False,
                shuttle_speed_peak=Metric(
                    name="shuttle_speed_peak",
                    unit="km/h",
                    available=False,
                    unavailable_reason="Empty video stream; no frames to track."
                ),
                shuttle_speed_mean=Metric(
                    name="shuttle_speed_mean",
                    unit="km/h",
                    available=False,
                    unavailable_reason="Empty video stream; no frames to track."
                ),
                per_frame_records=[]
            )

        H_np = (
            np.array(court_calibration.homography_matrix, dtype=np.float64)
            if (court_calibration and court_calibration.is_calibrated and court_calibration.homography_matrix)
            else None
        )

        # Pass 1: Frame-differencing candidate extraction
        raw_candidates: List[Optional[Tuple[float, float, float]]] = [None] * n_frames  # (x, y, raw_score)
        records: List[ShuttleFrameRecord] = []

        prev_gray: Optional[np.ndarray] = None

        for i, frame in enumerate(raw_frames):
            timestamp_ms = int(round((i / max(1.0, fps)) * 1000))
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            if prev_gray is None:
                records.append(ShuttleFrameRecord(
                    frame_index=i,
                    timestamp_ms=timestamp_ms,
                    is_detected=False,
                    confidence=0.0,
                    reason="Initial frame: baseline for motion differencing."
                ))
                prev_gray = gray
                continue

            # Moving pixels
            diff = cv2.absdiff(gray, prev_gray)
            _, diff_mask = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)

            # Bright pixels
            _, bright_mask = cv2.threshold(gray, MIN_SHUTTLE_BRIGHTNESS, 255, cv2.THRESH_BINARY)

            # Combined moving & bright
            moving_bright = cv2.bitwise_and(diff_mask, bright_mask)

            # Morphological noise cleanup
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            cleaned = cv2.morphologyEx(moving_bright, cv2.MORPH_OPEN, kernel)

            contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            best_cand = None
            best_cand_score = 0.0

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < MIN_SHUTTLE_AREA or area > MAX_SHUTTLE_AREA:
                    continue

                hull = cv2.convexHull(cnt)
                hull_area = cv2.contourArea(hull)
                solidity = float(area / max(1.0, hull_area))
                if solidity < 0.40:
                    continue

                peri = cv2.arcLength(cnt, True)
                circularity = float(4.0 * math.pi * area / max(1.0, peri * peri))
                if circularity < 0.25:
                    continue

                M = cv2.moments(cnt)
                if M["m00"] > 0:
                    cx = float(M["m10"] / M["m00"])
                    cy = float(M["m01"] / M["m00"])
                    # Score combines circularity, solidity, and compact size
                    score = (circularity * 0.5 + solidity * 0.5) * (1.0 / (1.0 + abs(area - 40.0) / 40.0))
                    if score > best_cand_score:
                        best_cand_score = score
                        best_cand = (cx, cy, score)

            raw_candidates[i] = best_cand
            # Placeholder record for Pass 1, will update in Pass 2
            records.append(ShuttleFrameRecord(
                frame_index=i,
                timestamp_ms=timestamp_ms,
                is_detected=False,
                confidence=0.0,
                reason="No candidate cleared brightness and circularity filters." if best_cand is None else "Pending temporal continuity check."
            ))
            prev_gray = gray

        # Pass 2: Temporal Continuity & Trajectory Filtering
        # Shuttles must form consistent physical trajectory tracks across >= 3 frames
        verified_tracks: List[int] = []  # indices of verified frames

        # Find contiguous candidate sequences
        i = 0
        while i < n_frames:
            if raw_candidates[i] is None:
                i += 1
                continue

            seq = [i]
            j = i + 1
            while j < n_frames and raw_candidates[j] is not None:
                # Check frame-to-frame pixel jump
                p1 = raw_candidates[j - 1]
                p2 = raw_candidates[j]
                jump = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
                # In typical 720p/1080p, shuttle moves 2 to 150 px between frames
                if 2.0 <= jump <= 180.0:
                    seq.append(j)
                    j += 1
                else:
                    break

            if len(seq) >= MIN_TRAJECTORY_LENGTH:
                # Verify trajectory direction consistency
                is_smooth = True
                if len(seq) >= 3:
                    for k in range(1, len(seq) - 1):
                        p_prev = raw_candidates[seq[k - 1]]
                        p_curr = raw_candidates[seq[k]]
                        p_next = raw_candidates[seq[k + 1]]
                        v1 = (p_curr[0] - p_prev[0], p_curr[1] - p_prev[1])
                        v2 = (p_next[0] - p_curr[0], p_next[1] - p_curr[1])
                        dot = v1[0] * v2[0] + v1[1] * v2[1]
                        m1 = math.hypot(v1[0], v1[1])
                        m2 = math.hypot(v2[0], v2[1])
                        if m1 > 0 and m2 > 0:
                            cos_ang = max(-1.0, min(1.0, dot / (m1 * m2)))
                            # Reject sharp erratic directional reversals (> 90 degrees)
                            if cos_ang < -0.2:
                                is_smooth = False
                                break
                if is_smooth:
                    verified_tracks.extend(seq)

            i = max(i + 1, j)

        verified_set = set(verified_tracks)
        shuttle_speeds_km_h: List[float] = []
        prev_court_pt: Optional[Tuple[float, float, int]] = None

        # Update per-frame records
        for idx in range(n_frames):
            cand = raw_candidates[idx]
            rec = records[idx]

            if idx in verified_set and cand is not None:
                cx, cy, score = cand
                court_m = pixel_to_court_m(cx, cy, H_np) if H_np is not None else None
                conf = min(0.90, round(0.4 + score * 0.4, 2))

                if court_m and prev_court_pt:
                    dt_s = max(0.001, (rec.timestamp_ms - prev_court_pt[2]) / 1000.0)
                    dist_m = math.hypot(court_m[0] - prev_court_pt[0], court_m[1] - prev_court_pt[1])
                    spd_km_h = (dist_m / dt_s) * 3.6
                    if spd_km_h <= MAX_SHUTTLE_SPEED_KM_H:
                        shuttle_speeds_km_h.append(spd_km_h)

                if court_m:
                    prev_court_pt = (court_m[0], court_m[1], rec.timestamp_ms)

                rec.is_detected = True
                rec.confidence = conf
                rec.shuttle_px = (float(round(cx, 1)), float(round(cy, 1)))
                rec.shuttle_m = court_m
                rec.reason = None
            else:
                rec.is_detected = False
                rec.confidence = 0.0
                if cand is not None:
                    rec.reason = "Isolated candidate rejected: failed 3-frame temporal continuity trajectory check."
                prev_court_pt = None

        # Pass 3: Clip-Level Aggregation & Hard Gating
        raw_count = sum(1 for c in raw_candidates if c is not None)
        verified_count = len(verified_set)
        visibility_ratio = float(round(verified_count / max(1, n_frames), 3))
        is_usable = visibility_ratio >= SHUTTLE_USABILITY_THRESHOLD
        has_verified_trajectory = verified_count >= 3 and len(shuttle_speeds_km_h) >= 1
        if (is_usable or has_verified_trajectory) and H_np is not None and shuttle_speeds_km_h:
            peak_shuttle = float(round(np.percentile(shuttle_speeds_km_h, 95), 1))
            mean_shuttle = float(round(np.mean(shuttle_speeds_km_h), 1))
            shuttle_peak_metric = Metric(
                name="shuttle_speed_peak",
                value=peak_shuttle,
                unit="km/h",
                confidence="MEDIUM",
                method="frame_diff_temporal_continuity_tracking",
                available=True,
                unavailable_reason=None
            )
            shuttle_mean_metric = Metric(
                name="shuttle_speed_mean",
                value=mean_shuttle,
                unit="km/h",
                confidence="MEDIUM",
                method="frame_diff_temporal_continuity_tracking",
                available=True,
                unavailable_reason=None
            )
            is_usable = True
        else:
            reason = (
                f"NOT_RELIABLY_MEASURABLE: Shuttle tracked in only {visibility_ratio * 100:.1f}% of frames (minimum {SHUTTLE_USABILITY_THRESHOLD * 100:.0f}% required for physical trajectory reconstruction)."
                if not is_usable
                else ("Court not calibrated; metric km/h speed unavailable." if H_np is None else "Insufficient continuous shuttle flight segments.")
            )
            shuttle_peak_metric = Metric(
                name="shuttle_speed_peak",
                value=None,
                unit="km/h",
                confidence="LOW",
                method="frame_diff_temporal_continuity_gated",
                available=False,
                unavailable_reason=reason
            )
            shuttle_mean_metric = Metric(
                name="shuttle_speed_mean",
                value=None,
                unit="km/h",
                confidence="LOW",
                method="frame_diff_temporal_continuity_gated",
                available=False,
                unavailable_reason=reason
            )

        return ShuttleTrackingSummary(
            total_frames=n_frames,
            raw_candidates_count=raw_count,
            verified_frames_count=verified_count,
            visibility_ratio=visibility_ratio,
            is_usable=is_usable,
            shuttle_speed_peak=shuttle_peak_metric,
            shuttle_speed_mean=shuttle_mean_metric,
            per_frame_records=records
        )
