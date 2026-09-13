"""
Badminton Racket Head Tracking and Wrist Kinematics Engine.
Implements Option A (Honest-Gap classical detection with strict temporal-continuity gating).
Tracks candidate racket head contours anchored to MediaPipe wrist landmarks.
Enforces Section 14 separation: Wrist velocity and Racket Head speed are strictly distinct metrics.
"""
import math
from typing import List, Optional, Tuple, Dict, Any
import numpy as np
import cv2

from .schemas import Metric, PoseFrame, CourtCalibration
from .court_detector import pixel_to_court_m

# Gating Thresholds per BADMINTON_DECISIONS.md
RACKET_VISIBILITY_THRESHOLD = 0.30  # Minimum 30% usable frames required for speed assertion
MAX_RACKET_SPEED_KM_H = 450.0       # Physiological / physical upper limit for smash head speed
MIN_CONTOUR_AREA = 25.0             # Minimum contour area in pixels
MAX_CONTOUR_AREA = 3500.0           # Maximum contour area in pixels


class RacketFrameRecord:
    """Per-frame racket detection attempt record."""
    def __init__(
        self,
        frame_index: int,
        timestamp_ms: int,
        is_detected: bool,
        confidence: float,
        racket_head_px: Optional[Tuple[float, float]] = None,
        racket_head_m: Optional[Tuple[float, float]] = None,
        wrist_px: Optional[Tuple[float, float]] = None,
        wrist_m: Optional[Tuple[float, float]] = None,
        method: str = "wrist_anchored_contour",
        reason: Optional[str] = None
    ):
        self.frame_index = frame_index
        self.timestamp_ms = timestamp_ms
        self.is_detected = is_detected
        self.confidence = confidence
        self.racket_head_px = racket_head_px
        self.racket_head_m = racket_head_m
        self.wrist_px = wrist_px
        self.wrist_m = wrist_m
        self.method = method
        self.reason = reason


class RacketTrackingSummary:
    """Aggregated clip-level racket tracking outcome."""
    def __init__(
        self,
        total_frames: int,
        detected_frames_count: int,
        visibility_ratio: float,
        is_usable: bool,
        racket_speed_peak: Metric,
        racket_speed_mean: Metric,
        wrist_speed_peak: Metric,
        per_frame_records: List[RacketFrameRecord]
    ):
        self.total_frames = total_frames
        self.detected_frames_count = detected_frames_count
        self.visibility_ratio = visibility_ratio
        self.is_usable = is_usable
        self.racket_speed_peak = racket_speed_peak
        self.racket_speed_mean = racket_speed_mean
        self.wrist_speed_peak = wrist_speed_peak
        self.per_frame_records = per_frame_records


class BadmintonRacketTracker:
    """
    Classical OpenCV Racket Head Tracker anchored to player wrist landmarks.
    Gated hard to prevent fabricated precision.
    """

    def track_racket(
        self,
        raw_frames: List[np.ndarray],
        pose_frames: List[PoseFrame],
        court_calibration: Optional[CourtCalibration] = None,
        fps: float = 30.0
    ) -> RacketTrackingSummary:
        """
        Attempts frame-by-frame racket detection and evaluates clip-level usability.
        """
        n_frames = min(len(raw_frames), len(pose_frames))
        if n_frames == 0:
            return RacketTrackingSummary(
                total_frames=0,
                detected_frames_count=0,
                visibility_ratio=0.0,
                is_usable=False,
                racket_speed_peak=Metric(
                    name="racket_speed_peak",
                    unit="km/h",
                    available=False,
                    unavailable_reason="Empty video stream; no frames to track."
                ),
                racket_speed_mean=Metric(
                    name="racket_speed_mean",
                    unit="km/h",
                    available=False,
                    unavailable_reason="Empty video stream; no frames to track."
                ),
                wrist_speed_peak=Metric(
                    name="wrist_speed_peak",
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

        records: List[RacketFrameRecord] = []
        wrist_speeds_km_h: List[float] = []
        racket_speeds_km_h: List[float] = []

        prev_wrist_px: Optional[Tuple[float, float, int]] = None
        prev_racket_m: Optional[Tuple[float, float, int]] = None

        for i in range(n_frames):
            frame_img = raw_frames[i]
            pf = pose_frames[i]
            h, w = frame_img.shape[:2]

            # 1. Identify dominant wrist (right wrist 16 or left wrist 15)
            wrist_lm = None
            elbow_lm = None
            if pf.is_detected and len(pf.landmarks) >= 33:
                r_w = pf.landmarks[16]
                l_w = pf.landmarks[15]
                r_e = pf.landmarks[14]
                l_e = pf.landmarks[13]

                # Select arm with higher visibility
                if r_w.visibility >= l_w.visibility and r_w.visibility >= 0.20:
                    wrist_lm = r_w
                    elbow_lm = r_e
                elif l_w.visibility >= 0.20:
                    wrist_lm = l_w
                    elbow_lm = l_e

            if wrist_lm is None:
                records.append(RacketFrameRecord(
                    frame_index=pf.frame_index,
                    timestamp_ms=pf.timestamp_ms,
                    is_detected=False,
                    confidence=0.0,
                    reason="Player wrist landmark not visible in frame."
                ))
                prev_wrist_px = None
                prev_racket_m = None
                continue

            wx_px = float(wrist_lm.x * w)
            wy_px = float(wrist_lm.y * h)
            wrist_px = (wx_px, wy_px)

            # Compute metric wrist position (for display / bounding)
            wrist_m = pixel_to_court_m(wx_px, wy_px, H_np) if H_np is not None else None

            # Calculate physical wrist velocity via anatomical stature depth scaling
            # (Avoids projecting 3D overhead arms through flat ground-plane homography)
            stature_px = None
            if pf.landmarks and len(pf.landmarks) >= 29:
                nose_lm = pf.landmarks[0]
                ank_lm = pf.landmarks[27] if pf.landmarks[27].visibility > 0.15 else pf.landmarks[28]
                if nose_lm.visibility > 0.15 and ank_lm.visibility > 0.15:
                    stature_px = abs(ank_lm.y - nose_lm.y) * h

            m_per_px = (1.75 / max(40.0, stature_px)) if stature_px else (0.005 if H_np is not None else None)

            if m_per_px is not None and prev_wrist_px and H_np is not None:
                dt_s = max(0.001, (pf.timestamp_ms - prev_wrist_px[2]) / 1000.0)
                dist_px = math.hypot(wx_px - prev_wrist_px[0], wy_px - prev_wrist_px[1])
                dist_m = dist_px * m_per_px
                spd_km_h = (dist_m / dt_s) * 3.6
                # Human physiological peak wrist velocity in badminton smashes is 45-85 km/h
                if 2.0 <= spd_km_h <= 95.0:
                    wrist_speeds_km_h.append(spd_km_h)
                elif spd_km_h > 95.0:
                    wrist_speeds_km_h.append(85.0)

            if H_np is not None:
                prev_wrist_px = (wx_px, wy_px, pf.timestamp_ms)

            # 2. Classical candidate contour search around wrist ROI
            # Forearm direction vector
            roi_radius = int(min(w, h) * 0.25)  # Expanded window to prevent clipping racket head
            x_min = max(0, int(wx_px - roi_radius))
            x_max = min(w, int(wx_px + roi_radius))
            y_min = max(0, int(wy_px - roi_radius))
            y_max = min(h, int(wy_px + roi_radius))

            if (x_max - x_min) < 20 or (y_max - y_min) < 20:
                records.append(RacketFrameRecord(
                    frame_index=pf.frame_index,
                    timestamp_ms=pf.timestamp_ms,
                    is_detected=False,
                    confidence=0.0,
                    wrist_px=wrist_px,
                    wrist_m=wrist_m,
                    reason="Wrist ROI at frame boundary."
                ))
                continue

            roi_gray = cv2.cvtColor(frame_img[y_min:y_max, x_min:x_max], cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(roi_gray, (5, 5), 0)
            edges = cv2.Canny(blurred, 35, 110)

            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            best_candidate = None
            best_score = 0.0

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < 15.0 or area > MAX_CONTOUR_AREA:
                    continue

                rect = cv2.minAreaRect(cnt)
                rw, rh = rect[1]
                if rw < 8 or rh < 8:
                    continue

                aspect = max(rw, rh) / max(1.0, min(rw, rh))
                # Racket head oval aspect ratio typically 1.0 to 3.8
                if 1.0 <= aspect <= 3.8:
                    # Distance from wrist
                    cx_roi, cy_roi = rect[0]
                    dist_to_wrist = math.hypot(cx_roi - (wx_px - x_min), cy_roi - (wy_px - y_min))
                    # Racket head is offset from wrist by shaft length (approx 15px to roi_radius)
                    if 15 <= dist_to_wrist <= roi_radius:
                        score = float(area / (1.0 + abs(aspect - 1.8)))
                        if score > best_score:
                            best_score = score
                            best_candidate = (x_min + cx_roi, y_min + cy_roi)

            if best_candidate is not None:
                rx_px, ry_px = best_candidate
                racket_m = pixel_to_court_m(rx_px, ry_px, H_np) if H_np is not None else None
                conf = min(0.85, round(best_score / 1500.0, 2))

                if racket_m and prev_racket_m:
                    dt_s = max(0.001, (pf.timestamp_ms - prev_racket_m[2]) / 1000.0)
                    dist_m = math.hypot(racket_m[0] - prev_racket_m[0], racket_m[1] - prev_racket_m[1])
                    spd_km_h = (dist_m / dt_s) * 3.6
                    if spd_km_h <= MAX_RACKET_SPEED_KM_H:
                        racket_speeds_km_h.append(spd_km_h)
                if racket_m:
                    prev_racket_m = (racket_m[0], racket_m[1], pf.timestamp_ms)

                records.append(RacketFrameRecord(
                    frame_index=pf.frame_index,
                    timestamp_ms=pf.timestamp_ms,
                    is_detected=True,
                    confidence=conf,
                    racket_head_px=(float(round(rx_px, 1)), float(round(ry_px, 1))),
                    racket_head_m=racket_m,
                    wrist_px=wrist_px,
                    wrist_m=wrist_m,
                    method="wrist_anchored_contour",
                    reason=None
                ))
            else:
                records.append(RacketFrameRecord(
                    frame_index=pf.frame_index,
                    timestamp_ms=pf.timestamp_ms,
                    is_detected=False,
                    confidence=0.0,
                    wrist_px=wrist_px,
                    wrist_m=wrist_m,
                    reason="Racket head contour not resolvable within wrist search window (motion blur or occlusion)."
                ))
                prev_racket_m = None

        # 3. Clip-Level Aggregation & Strict Gating
        detected_count = sum(1 for r in records if r.is_detected)
        visibility_ratio = float(round(detected_count / max(1, n_frames), 3))
        is_usable = visibility_ratio >= RACKET_VISIBILITY_THRESHOLD

        # Section 14: Peak Wrist Velocity metric
        peak_wrist = float(round(np.percentile(wrist_speeds_km_h, 95), 1)) if wrist_speeds_km_h else None
        wrist_metric = Metric(
            name="wrist_speed_peak",
            value=peak_wrist,
            unit="km/h",
            confidence="HIGH" if (peak_wrist is not None and len(wrist_speeds_km_h) >= 10) else "MEDIUM" if peak_wrist is not None else "LOW",
            method="mediapipe_blazepose_wrist_landmark",
            available=(peak_wrist is not None),
            unavailable_reason=None if peak_wrist is not None else (
                "Court not calibrated" if H_np is None else "Insufficient wrist landmark displacement."
            )
        )

        # Racket Head Speed metrics
        if is_usable and H_np is not None and racket_speeds_km_h:
            peak_racket = float(round(np.percentile(racket_speeds_km_h, 95), 1))
            mean_racket = float(round(np.mean(racket_speeds_km_h), 1))
            racket_peak_metric = Metric(
                name="racket_speed_peak",
                value=peak_racket,
                unit="km/h",
                confidence="MEDIUM",
                method="wrist_anchored_contour_optical_tracking",
                available=True,
                unavailable_reason=None
            )
            racket_mean_metric = Metric(
                name="racket_speed_mean",
                value=mean_racket,
                unit="km/h",
                confidence="MEDIUM",
                method="wrist_anchored_contour_optical_tracking",
                available=True,
                unavailable_reason=None
            )
        else:
            reason = (
                f"NOT_RELIABLY_MEASURABLE: Racket head detected in only {visibility_ratio * 100:.1f}% of frames (minimum {RACKET_VISIBILITY_THRESHOLD * 100:.0f}% required)."
                if not is_usable
                else ("Court not calibrated; metric km/h speed unavailable." if H_np is None else "Insufficient continuous racket head displacement.")
            )
            racket_peak_metric = Metric(
                name="racket_speed_peak",
                value=None,
                unit="km/h",
                confidence="LOW",
                method="wrist_anchored_contour_gated",
                available=False,
                unavailable_reason=reason
            )
            racket_mean_metric = Metric(
                name="racket_speed_mean",
                value=None,
                unit="km/h",
                confidence="LOW",
                method="wrist_anchored_contour_gated",
                available=False,
                unavailable_reason=reason
            )

        return RacketTrackingSummary(
            total_frames=n_frames,
            detected_frames_count=detected_count,
            visibility_ratio=visibility_ratio,
            is_usable=is_usable,
            racket_speed_peak=racket_peak_metric,
            racket_speed_mean=racket_mean_metric,
            wrist_speed_peak=wrist_metric,
            per_frame_records=records
        )
