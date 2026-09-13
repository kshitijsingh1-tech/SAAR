"""
Badminton Shot Classification Engine.
Implements Section 16 of Master Spec.
Classifies detected candidate strokes into:
- smash
- clear
- drop
- drive
- lift
- net_shot
- push
- block
- serve
- unknown

Enforces hard threshold gating: if classification confidence < 0.55,
the shot is classified as UNKNOWN rather than forcing a label.
"""
import math
from typing import List, Optional, Tuple, Dict, Any

from .schemas import (
    ShotResult,
    PoseFrame,
    Metric,
    CourtCalibration
)
from .shot_detector import CandidateContactEvent
from .pose_estimator import (
    compute_joint_angle_2d,
    right_shoulder, right_elbow, right_wrist,
    left_shoulder, left_elbow, left_wrist,
    right_hip, left_hip
)
from .movement_analyzer import classify_court_region

# Hard gating threshold per Section 16 of Master Spec
CLASSIFICATION_CONFIDENCE_THRESHOLD: float = 0.55


class BadmintonShotClassifier:
    """
    Classifies candidate contact events using multimodal pose geometry,
    contact height relative to athlete, court region, and trajectory dynamics.
    """

    def classify_shots(
        self,
        candidate_shots: List[CandidateContactEvent],
        pose_frames: List[PoseFrame],
        court_calibration: Optional[CourtCalibration] = None
    ) -> List[ShotResult]:
        """
        Classifies each candidate shot into a standardized ShotResult model.
        """
        classified_results: List[ShotResult] = []

        for candidate in candidate_shots:
            res = self._classify_single_shot(candidate, pose_frames, court_calibration)
            classified_results.append(res)

        return classified_results

    def _classify_single_shot(
        self,
        shot: CandidateContactEvent,
        pose_frames: List[PoseFrame],
        court_calibration: Optional[CourtCalibration]
    ) -> ShotResult:
        """
        Extracts biomechanical features and evaluates candidate stroke hypotheses.
        """
        cf = shot.contact_frame
        pf = pose_frames[cf] if (0 <= cf < len(pose_frames)) else None

        pose_features: Dict[str, Any] = {}
        trajectory_features: Dict[str, Any] = {
            "evidence_basis": shot.evidence_basis,
            "has_racket_signal": shot.has_racket_signal,
            "has_shuttle_signal": shot.has_shuttle_signal,
            "has_shuttle_deflection": shot.has_shuttle_deflection,
            "wrist_speed_km_h": shot.wrist_speed_km_h,
            "racket_speed_km_h": shot.racket_speed_km_h,
            "shuttle_speed_km_h": shot.shuttle_speed_km_h
        }

        # Guard: If no valid pose at contact frame, strictly UNKNOWN
        if pf is None or not pf.is_detected or len(pf.landmarks) < 33:
            return ShotResult(
                shot_id=shot.shot_id,
                shot_type="unknown",
                confidence=round(min(shot.confidence, 0.35), 2),
                start_time=shot.start_time,
                contact_time=shot.contact_time,
                end_time=shot.end_time,
                duration=shot.duration,
                player_position=shot.player_pos,
                target_position=shot.target_pos,
                racket_speed=Metric(
                    name="racket_speed",
                    value=shot.racket_speed_km_h,
                    unit="km/h",
                    available=shot.racket_speed_km_h is not None,
                    unavailable_reason="NOT_RELIABLY_MEASURABLE: Racket head unresolvable at contact." if shot.racket_speed_km_h is None else None
                ),
                shuttle_speed=Metric(
                    name="shuttle_speed",
                    value=shot.shuttle_speed_km_h,
                    unit="km/h",
                    available=shot.shuttle_speed_km_h is not None,
                    unavailable_reason="NOT_RELIABLY_MEASURABLE: Shuttle trajectory unresolvable at contact." if shot.shuttle_speed_km_h is None else None
                ),
                trajectory=[],
                evidence_frames=shot.evidence_frames,
                pose_features={"reason": "No valid human pose detected at contact frame."},
                trajectory_features=trajectory_features,
                classification_reason="Insufficient pose landmarks: Player pose landmarks occluded or unavailable at contact frame.",
                evidence_basis=shot.evidence_basis,
                available=True
            )

        # 1. Contact Height relative to body segments
        rw = right_wrist(pf)
        lw = left_wrist(pf)
        dominant_wrist = rw if rw.visibility >= lw.visibility and rw.visibility >= 0.20 else (lw if lw.visibility >= 0.20 else None)

        if dominant_wrist is None or dominant_wrist.visibility < 0.20:
            return ShotResult(
                shot_id=shot.shot_id,
                shot_type="unknown",
                confidence=round(min(shot.confidence, 0.35), 2),
                start_time=shot.start_time,
                contact_time=shot.contact_time,
                end_time=shot.end_time,
                duration=shot.duration,
                player_position=shot.player_pos,
                target_position=shot.target_pos,
                racket_speed=Metric(
                    name="racket_speed",
                    value=shot.racket_speed_km_h,
                    unit="km/h",
                    available=shot.racket_speed_km_h is not None,
                    unavailable_reason="NOT_RELIABLY_MEASURABLE: Racket head unresolvable at contact." if shot.racket_speed_km_h is None else None
                ),
                shuttle_speed=Metric(
                    name="shuttle_speed",
                    value=shot.shuttle_speed_km_h,
                    unit="km/h",
                    available=shot.shuttle_speed_km_h is not None,
                    unavailable_reason="NOT_RELIABLY_MEASURABLE: Shuttle flight unresolvable at contact." if shot.shuttle_speed_km_h is None else None
                ),
                evidence_frames=shot.evidence_frames,
                pose_features={"reason": "Wrist landmark visibility too low."},
                trajectory_features=trajectory_features,
                classification_reason="Insufficient wrist landmark visibility (< 0.20) at contact frame.",
                evidence_basis=shot.evidence_basis,
                available=True
            )

        r_sh = right_shoulder(pf)
        l_sh = left_shoulder(pf)
        r_h = right_hip(pf)
        l_h = left_hip(pf)

        sh_y = (r_sh.y + l_sh.y) / 2.0
        hip_y = (r_h.y + l_h.y) / 2.0
        w_y = dominant_wrist.y

        # In image coordinates, y increases downwards (smaller y = higher in physical space)
        is_overhead = (w_y < sh_y - 0.03)
        is_underarm = (w_y > hip_y + 0.02)
        is_mid_height = (not is_overhead and not is_underarm)

        pose_features["contact_plane"] = "overhead" if is_overhead else ("underarm" if is_underarm else "mid_height")
        pose_features["wrist_y_normalized"] = round(float(w_y), 3)

        # 2. Elbow extension angle
        r_elb_ang = compute_joint_angle_2d(right_shoulder(pf), right_elbow(pf), right_wrist(pf))
        l_elb_ang = compute_joint_angle_2d(left_shoulder(pf), left_elbow(pf), left_wrist(pf))
        valid_elbs = [a for a in [r_elb_ang, l_elb_ang] if a is not None]
        elbow_angle = max(valid_elbs) if valid_elbs else None
        if elbow_angle is not None:
            pose_features["elbow_extension_deg"] = round(float(elbow_angle), 1)

        # 3. Court Region at Contact
        court_region = "uncalibrated"
        if shot.player_pos and len(shot.player_pos) >= 2 and court_calibration and court_calibration.is_calibrated:
            court_region = classify_court_region(shot.player_pos[0], shot.player_pos[1], "near_court")
        pose_features["court_region"] = court_region

        is_rear = "rear" in court_region
        is_front = "front" in court_region
        is_mid = "mid" in court_region

        # 4. Multi-Hypothesis Scoring
        scores: Dict[str, float] = {
            "smash": 0.0,
            "clear": 0.0,
            "drop": 0.0,
            "drive": 0.0,
            "lift": 0.0,
            "net_shot": 0.0,
            "push": 0.0,
            "block": 0.0,
            "serve": 0.0
        }

        # A. Overhead Category
        if is_overhead:
            # Smash: high elbow extension + high speed + rear/mid court
            smash_score = 0.35  # baseline overhead
            if elbow_angle is not None:
                if elbow_angle >= 145.0:
                    smash_score += 0.25
                elif elbow_angle >= 125.0:
                    smash_score += 0.15

            if shot.wrist_speed_km_h and shot.wrist_speed_km_h >= 60.0:
                smash_score += 0.20
            elif shot.racket_speed_km_h and shot.racket_speed_km_h >= 120.0:
                smash_score += 0.25

            if is_rear or is_mid:
                smash_score += 0.15
            scores["smash"] = smash_score

            # Clear: high elbow extension + rear court + high contact
            clear_score = 0.35
            if elbow_angle is not None and elbow_angle >= 145.0:
                clear_score += 0.25
            if is_rear:
                clear_score += 0.25
            elif is_mid:
                clear_score += 0.10
            scores["clear"] = clear_score

            # Drop: moderate elbow extension + rear court + lower exit speed
            drop_score = 0.35
            if elbow_angle is not None and 105.0 <= elbow_angle <= 145.0:
                drop_score += 0.25
            if is_rear:
                drop_score += 0.20
            scores["drop"] = drop_score

        # B. Mid-Height Category
        elif is_mid_height:
            # Drive: midcourt flat high speed (requires active athletic velocity)
            drive_score = 0.20
            if (shot.wrist_speed_km_h and shot.wrist_speed_km_h >= 45.0) or (shot.racket_speed_km_h and shot.racket_speed_km_h >= 90.0):
                drive_score += 0.35
            if is_mid:
                drive_score += 0.20
            if elbow_angle is not None and elbow_angle >= 115.0:
                drive_score += 0.15
            scores["drive"] = drive_score

            # Push: mid/forecourt controlled touch
            push_score = 0.25
            if is_front or is_mid:
                push_score += 0.20
            if elbow_angle is not None and 100.0 <= elbow_angle <= 135.0:
                push_score += 0.15
            scores["push"] = push_score

            # Block: defensive midcourt reaction
            block_score = 0.25
            if is_mid and elbow_angle is not None and elbow_angle < 120.0:
                block_score += 0.20
            scores["block"] = block_score

        # C. Underarm Category
        elif is_underarm:
            # Lift: underarm upward swing
            lift_score = 0.40
            if is_front:
                lift_score += 0.30
            elif is_mid:
                lift_score += 0.20
            scores["lift"] = lift_score

            # Net shot: forecourt tight touch
            net_score = 0.40
            if is_front:
                net_score += 0.35
            scores["net_shot"] = net_score

            # Serve: underarm service line
            serve_score = 0.30
            if is_front or is_mid:
                serve_score += 0.20
            scores["serve"] = serve_score

        # 5. Evaluate winning hypothesis against hard Section 16 threshold
        best_type = max(scores, key=scores.get)
        raw_score = scores[best_type]

        # Combine stroke pattern score with contact detection confidence
        # Contact confidence weights the final classification certainty
        combined_confidence = round(0.40 * shot.confidence + 0.60 * raw_score, 2)

        # Section 16 Hard Gate: If confidence < 0.55, classify as UNKNOWN
        if combined_confidence < CLASSIFICATION_CONFIDENCE_THRESHOLD:
            final_type = "unknown"
            reason = (
                f"NOT_CONFIDENT_CLASSIFICATION: Best candidate '{best_type}' score ({combined_confidence:.2f}) "
                f"is below the {CLASSIFICATION_CONFIDENCE_THRESHOLD} threshold. Kinematic signals ambiguous."
            )
        else:
            final_type = best_type
            reason = f"Classified as {best_type} based on {pose_features['contact_plane']} contact in {court_region} region."

        trajectory_features["candidate_scores"] = {k: round(v, 2) for k, v in scores.items()}

        return ShotResult(
            shot_id=shot.shot_id,
            shot_type=final_type,
            confidence=combined_confidence,
            start_time=shot.start_time,
            contact_time=shot.contact_time,
            end_time=shot.end_time,
            duration=shot.duration,
            player_position=shot.player_pos,
            target_position=shot.target_pos,
            racket_speed=Metric(
                name="racket_speed",
                value=shot.racket_speed_km_h,
                unit="km/h",
                available=shot.racket_speed_km_h is not None,
                unavailable_reason="NOT_RELIABLY_MEASURABLE: Racket head unresolvable at contact." if shot.racket_speed_km_h is None else None
            ),
            shuttle_speed=Metric(
                name="shuttle_speed",
                value=shot.shuttle_speed_km_h,
                unit="km/h",
                available=shot.shuttle_speed_km_h is not None,
                unavailable_reason="NOT_RELIABLY_MEASURABLE: Shuttle flight unresolvable at contact." if shot.shuttle_speed_km_h is None else None
            ),
            trajectory=[],
            evidence_frames=shot.evidence_frames,
            pose_features=pose_features,
            trajectory_features=trajectory_features,
            classification_reason=reason,
            evidence_basis=shot.evidence_basis,
            available=True
        )
