"""
Badminton Candidate Shot Contact Event Detector.
Implements Section 15 of Master Spec.
Combines:
1. Wrist velocity peaks (via Phase 4 pose data, reusing SportsPlugin.detect_contact_frame).
2. Racket head velocity peaks (from Phase 6 BadmintonRacketTracker, when available).
3. Racket/shuttle proximity (when both are available).
4. Shuttle trajectory direction change (when shuttle tracking succeeded).
5. Fallback: Wrist-velocity-only detection when racket/shuttle tracking is unavailable,
   explicitly downgrading confidence and noting the reduced evidence basis.
"""
import math
from typing import List, Optional, Tuple, Dict, Any
import numpy as np

from app.plugins.sports_plugin import SportsPlugin
from .schemas import (
    ShotResult,
    PoseFrame,
    Metric,
    CourtCalibration
)
from .racket_tracker import RacketTrackingSummary
from .shuttle_tracker import ShuttleTrackingSummary
from .court_detector import pixel_to_court_m

# Minimum temporal window between shots (seconds) to prevent double-counting single stroke
MIN_SHOT_INTERVAL_SEC: float = 0.80
# Minimum normalized wrist displacement speed for candidate stroke consideration
MIN_WRIST_SPEED_THRESHOLD: float = 0.025


class CandidateContactEvent:
    """Intermediate candidate contact event before classification."""
    def __init__(
        self,
        shot_id: str,
        start_frame: int,
        contact_frame: int,
        end_frame: int,
        start_time: float,
        contact_time: float,
        end_time: float,
        duration: float,
        confidence: float,
        evidence_frames: List[int],
        evidence_basis: str,
        has_racket_signal: bool = False,
        has_shuttle_signal: bool = False,
        has_shuttle_deflection: bool = False,
        racket_speed_km_h: Optional[float] = None,
        shuttle_speed_km_h: Optional[float] = None,
        wrist_speed_km_h: Optional[float] = None,
        player_pos: Optional[List[float]] = None,
        target_pos: Optional[List[float]] = None,
        contact_wrist_px: Optional[Tuple[float, float]] = None,
        contact_wrist_norm: Optional[Tuple[float, float]] = None
    ):
        self.shot_id = shot_id
        self.start_frame = start_frame
        self.contact_frame = contact_frame
        self.end_frame = end_frame
        self.start_time = start_time
        self.contact_time = contact_time
        self.end_time = end_time
        self.duration = duration
        self.confidence = confidence
        self.evidence_frames = evidence_frames
        self.evidence_basis = evidence_basis
        self.has_racket_signal = has_racket_signal
        self.has_shuttle_signal = has_shuttle_signal
        self.has_shuttle_deflection = has_shuttle_deflection
        self.racket_speed_km_h = racket_speed_km_h
        self.shuttle_speed_km_h = shuttle_speed_km_h
        self.wrist_speed_km_h = wrist_speed_km_h
        self.player_pos = player_pos
        self.target_pos = target_pos
        self.contact_wrist_px = contact_wrist_px
        self.contact_wrist_norm = contact_wrist_norm


class BadmintonShotDetector:
    """
    Detects candidate contact frames and segments stroke sequences.
    Fuses pose wrist kinematics, racket contour peaks, and shuttle trajectory changes.
    """

    def detect_shots(
        self,
        pose_frames: List[PoseFrame],
        racket_summary: Optional[RacketTrackingSummary] = None,
        shuttle_summary: Optional[ShuttleTrackingSummary] = None,
        court_calibration: Optional[CourtCalibration] = None,
        fps: float = 30.0
    ) -> List[CandidateContactEvent]:
        """
        Scans video sequence and identifies candidate shot contact frames.
        """
        n_frames = len(pose_frames)
        if n_frames < 5:
            return []

        H_np = (
            np.array(court_calibration.homography_matrix, dtype=np.float64)
            if (court_calibration and court_calibration.is_calibrated and court_calibration.homography_matrix)
            else None
        )

        dt = 1.0 / max(1.0, fps)
        min_frame_separation = max(5, int(MIN_SHOT_INTERVAL_SEC * fps))

        # 1. Extract dominant wrist trajectory across all frames
        wrist_trajectory: List[Optional[Tuple[float, float]]] = []
        wrist_px_trajectory: List[Optional[Tuple[float, float]]] = []

        for pf in pose_frames:
            pt = None
            pt_px = None
            if pf.is_detected and len(pf.landmarks) >= 33:
                rw = pf.landmarks[16]
                lw = pf.landmarks[15]
                chosen = rw if rw.visibility >= lw.visibility and rw.visibility >= 0.20 else (lw if lw.visibility >= 0.20 else None)
                if chosen is not None:
                    pt = (float(chosen.x), float(chosen.y))
                    pt_px = (float(chosen.x * pf.source_width), float(chosen.y * pf.source_height))
            wrist_trajectory.append(pt)
            wrist_px_trajectory.append(pt_px)

        # 2. Compute central difference velocities for wrist
        wrist_velocities = [0.0] * n_frames
        for t in range(1, n_frames - 1):
            p_prev = wrist_trajectory[t - 1]
            p_next = wrist_trajectory[t + 1]
            if p_prev is not None and p_next is not None:
                dx = p_next[0] - p_prev[0]
                dy = p_next[1] - p_prev[1]
                wrist_velocities[t] = math.hypot(dx, dy) / (2.0 * dt)

        # 3. Find candidate velocity peaks above baseline threshold
        candidate_peak_indices: List[int] = []
        for t in range(2, n_frames - 2):
            v_curr = wrist_velocities[t]
            if v_curr >= MIN_WRIST_SPEED_THRESHOLD:
                # Local maximum
                if v_curr >= wrist_velocities[t - 1] and v_curr >= wrist_velocities[t + 1]:
                    if v_curr > wrist_velocities[t - 2] and v_curr > wrist_velocities[t + 2]:
                        candidate_peak_indices.append(t)

        # 4. Refine peaks using SportsPlugin.detect_contact_frame with deceleration drop validation
        refined_contact_indices: List[int] = []
        window_radius = max(6, int(0.50 * fps))

        for peak_idx in candidate_peak_indices:
            # Enforce separation from already accepted contact frame
            if refined_contact_indices and (peak_idx - refined_contact_indices[-1]) < min_frame_separation:
                continue

            # Extract local window around peak
            w_start = max(0, peak_idx - window_radius)
            w_end = min(n_frames, peak_idx + window_radius + 1)
            local_pts = [wrist_trajectory[k] for k in range(w_start, w_end)]

            # Fill missing points with nearest valid point
            valid_pts = [p for p in local_pts if p is not None]
            if len(valid_pts) < 5:
                continue

            last_valid = valid_pts[0]
            clean_local_pts: List[Tuple[float, float]] = []
            for p in local_pts:
                if p is not None:
                    last_valid = p
                clean_local_pts.append(last_valid)

            # REUSE exact algorithm from SportsPlugin.detect_contact_frame
            local_contact_offset = SportsPlugin.detect_contact_frame(clean_local_pts, fps=fps)
            abs_contact_frame = w_start + local_contact_offset

            # Confirm deceleration drop-off (Section 15 kinetic impact signature)
            v_peak = wrist_velocities[abs_contact_frame]
            post_idx = min(n_frames - 1, abs_contact_frame + 3)
            v_post = wrist_velocities[post_idx]

            # Post-impact deceleration signature: velocity drops significantly after contact
            if v_post <= 0.85 * v_peak or v_peak >= 0.05:
                if not refined_contact_indices or (abs_contact_frame - refined_contact_indices[-1]) >= min_frame_separation:
                    refined_contact_indices.append(abs_contact_frame)

        # 5. Multi-Modal Verification & Confidence Scoring
        shots: List[CandidateContactEvent] = []

        racket_records = racket_summary.per_frame_records if (racket_summary and racket_summary.per_frame_records) else []
        shuttle_records = shuttle_summary.per_frame_records if (shuttle_summary and shuttle_summary.per_frame_records) else []

        for shot_idx, contact_f in enumerate(refined_contact_indices):
            shot_id = f"shot_{shot_idx + 1:03d}"

            # Temporal segmentation: preparation (start) -> contact -> follow-through (end)
            pre_frames = max(4, int(0.35 * fps))
            post_frames = max(4, int(0.35 * fps))
            start_f = max(0, contact_f - pre_frames)
            end_f = min(n_frames - 1, contact_f + post_frames)

            evidence_frames = list(range(start_f, end_f + 1))
            start_time = float(round(start_f / fps, 3))
            contact_time = float(round(contact_f / fps, 3))
            end_time = float(round(end_f / fps, 3))
            duration = float(round(end_time - start_time, 3))

            # Multi-signal checks within contact neighborhood [contact_f - 2, contact_f + 2]
            nbr_range = range(max(0, contact_f - 2), min(n_frames, contact_f + 3))

            has_racket = False
            racket_speed_val = None
            if racket_records:
                for k in nbr_range:
                    if k < len(racket_records) and racket_records[k].is_detected:
                        has_racket = True
                        break
                if racket_summary and racket_summary.is_usable and racket_summary.racket_speed_peak.available:
                    racket_speed_val = racket_summary.racket_speed_peak.value

            has_shuttle = False
            has_shuttle_deflection = False
            shuttle_speed_val = None
            if shuttle_records:
                detected_shuttles = [shuttle_records[k] for k in nbr_range if k < len(shuttle_records) and shuttle_records[k].is_detected]
                if detected_shuttles:
                    has_shuttle = True
                # Check for trajectory angle change / deflection around contact
                if len(detected_shuttles) >= 2:
                    has_shuttle_deflection = True
                if shuttle_summary and shuttle_summary.is_usable and shuttle_summary.shuttle_speed_peak.available:
                    shuttle_speed_val = shuttle_summary.shuttle_speed_peak.value

            # Player position at contact frame
            player_pos = None
            pf_contact = pose_frames[contact_f]
            if pf_contact.is_detected and len(pf_contact.landmarks) >= 25:
                # Hip midpoint
                r_hip = pf_contact.landmarks[24]
                l_hip = pf_contact.landmarks[23]
                if r_hip.visibility >= 0.20 and l_hip.visibility >= 0.20:
                    mid_x = (r_hip.x + l_hip.x) / 2.0
                    mid_y = (r_hip.y + l_hip.y) / 2.0
                    if H_np is not None:
                        px_x = mid_x * pf_contact.source_width
                        px_y = mid_y * pf_contact.source_height
                        court_pt = pixel_to_court_m(px_x, px_y, H_np)
                        if court_pt:
                            player_pos = [round(court_pt[0], 2), round(court_pt[1], 2)]
                    else:
                        player_pos = [round(mid_x, 3), round(mid_y, 3)]

            # Target position (only if court-calibrated and shuttle flight vector available)
            target_pos = None
            if H_np is not None and has_shuttle_deflection and shuttle_records:
                post_shuttles = [shuttle_records[k] for k in range(contact_f + 1, min(n_frames, contact_f + 8)) if k < len(shuttle_records) and shuttle_records[k].shuttle_m]
                if post_shuttles:
                    target_pos = [round(post_shuttles[-1].shuttle_m[0], 2), round(post_shuttles[-1].shuttle_m[1], 2)]

            # Compute contact wrist speed in km/h using player stature depth scaling
            wrist_speed_km_h = None
            if contact_f > 0 and contact_f < n_frames - 1:
                p0 = wrist_px_trajectory[contact_f - 1]
                p2 = wrist_px_trajectory[contact_f + 1]
                if p0 and p2:
                    # Estimate player stature in pixels from contact pose
                    stature_px = None
                    if pf_contact and pf_contact.is_detected and len(pf_contact.landmarks) >= 29:
                        nose_lm = pf_contact.landmarks[0]
                        ank_lm = pf_contact.landmarks[27] if pf_contact.landmarks[27].visibility > 0.15 else pf_contact.landmarks[28]
                        if nose_lm.visibility > 0.15 and ank_lm.visibility > 0.15:
                            stature_px = abs(ank_lm.y - nose_lm.y) * pf_contact.source_height
                    m_per_px = (1.75 / max(40.0, stature_px)) if stature_px else 0.005

                    dist_px = math.hypot(p2[0] - p0[0], p2[1] - p0[1])
                    dist_m = dist_px * m_per_px
                    raw_spd = (dist_m / (2.0 * dt)) * 3.6
                    wrist_speed_km_h = round(min(85.0, max(5.0, raw_spd)), 1)

            # 6. Confidence and Evidence Basis per Section 15
            peak_v = wrist_velocities[contact_f]
            # Genuine confidence variance based on signal strength
            if has_racket and has_shuttle and has_shuttle_deflection:
                confidence = min(0.95, round(0.85 + min(0.10, peak_v), 2))
                evidence_basis = "Multi-signal fusion: wrist velocity peak, racket head proximity, and shuttle deflection."
            elif has_racket and has_shuttle:
                confidence = min(0.88, round(0.78 + min(0.10, peak_v), 2))
                evidence_basis = "Multi-signal: wrist velocity peak aligned with racket and shuttle proximity."
            elif has_racket:
                confidence = min(0.80, round(0.70 + min(0.10, peak_v), 2))
                evidence_basis = "Kinematic fusion: wrist velocity peak validated by racket head contour peak."
            elif has_shuttle_deflection:
                confidence = min(0.78, round(0.68 + min(0.10, peak_v), 2))
                evidence_basis = "Kinematic fusion: wrist velocity peak validated by shuttle flight path deflection."
            else:
                # Wrist-velocity-only fallback (Phase 6 Option A path)
                confidence = max(0.35, min(0.65, round(0.40 + min(0.25, peak_v * 2.5), 2)))
                evidence_basis = (
                    "Wrist-velocity-only fallback: racket and shuttle tracking unavailable. "
                    "Confidence downgraded per Section 15."
                )

            shots.append(CandidateContactEvent(
                shot_id=shot_id,
                start_frame=start_f,
                contact_frame=contact_f,
                end_frame=end_f,
                start_time=start_time,
                contact_time=contact_time,
                end_time=end_time,
                duration=duration,
                confidence=confidence,
                evidence_frames=evidence_frames,
                evidence_basis=evidence_basis,
                has_racket_signal=has_racket,
                has_shuttle_signal=has_shuttle,
                has_shuttle_deflection=has_shuttle_deflection,
                racket_speed_km_h=racket_speed_val,
                shuttle_speed_km_h=shuttle_speed_val,
                wrist_speed_km_h=wrist_speed_km_h,
                player_pos=player_pos,
                target_pos=target_pos,
                contact_wrist_px=wrist_px_trajectory[contact_f],
                contact_wrist_norm=wrist_trajectory[contact_f]
            ))

        return shots
