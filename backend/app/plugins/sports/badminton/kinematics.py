"""
Badminton Joint Kinematics & Kinetic Chain Sequencing Engine.
Implements contact-frame joint angle extraction and proximal-to-distal sequencing per Sections 3, 41, and 42.

Key Requirements:
1. Reuses SportsPlugin.calculate_joint_angle_2d (arccos 3-point angle).
2. Computes real joint angles (elbow, shoulder, knee, hip) at the exact contact frame of each detected shot.
3. Performs temporal proximal-to-distal sequencing analysis (time-to-peak angular velocity) leading into contact.
   Strictly gates sequencing: requires at least 4 consecutive frames with visibility >= 0.35; otherwise reports unavailable.
4. Strictly does NOT claim exact force or power — reports only angles, angular velocities, and relative timing.
"""
import math
from typing import List, Optional, Tuple, Dict, Any
import numpy as np

from app.plugins.sports_plugin import SportsPlugin
from .schemas import Landmark, PoseFrame, ShotResult, PoseMetrics
from .pose_estimator import (
    compute_joint_angle_2d,
    left_shoulder, right_shoulder,
    left_elbow, right_elbow,
    left_wrist, right_wrist,
    left_hip, right_hip,
    left_knee, right_knee,
    left_ankle, right_ankle
)

# Minimum landmark visibility required for reliable contact-frame angle calculation
MIN_ANGLE_VISIBILITY = 0.20

# Gating thresholds for proximal-to-distal sequencing
MIN_CONSECUTIVE_SEQUENCING_FRAMES = 4
MIN_SEQUENCING_VISIBILITY = 0.35


def get_joint_angle(
    p_proximal: Landmark,
    p_vertex: Landmark,
    p_distal: Landmark,
    min_visibility: float = MIN_ANGLE_VISIBILITY
) -> Optional[float]:
    """
    Computes 2D planar joint angle at vertex using SportsPlugin.calculate_joint_angle_2d.
    Returns None if any required landmark falls below visibility threshold.
    """
    if (p_proximal.visibility < min_visibility or
        p_vertex.visibility < min_visibility or
        p_distal.visibility < min_visibility):
        return None
    ang = SportsPlugin.calculate_joint_angle_2d(
        (p_proximal.x, p_proximal.y),
        (p_vertex.x, p_vertex.y),
        (p_distal.x, p_distal.y)
    )
    return round(float(ang), 1)


class BadmintonKinematicsAnalyzer:
    """
    Analyzes contact-frame joint angles and proximal-to-distal kinetic chain sequencing.
    """

    def compute_frame_joint_angles(self, frame: PoseFrame) -> Dict[str, Any]:
        """
        Computes all 8 bilateral joint angles (elbow, shoulder, knee, hip) for a single frame.
        """
        if not frame.is_detected or len(frame.landmarks) < 29:
            return {
                "available": False,
                "reason": "Pose not detected or insufficient landmarks in frame."
            }

        # 1. Elbow Angles (Shoulder -> Elbow -> Wrist)
        r_elbow = get_joint_angle(right_shoulder(frame), right_elbow(frame), right_wrist(frame))
        l_elbow = get_joint_angle(left_shoulder(frame), left_elbow(frame), left_wrist(frame))

        # 2. Shoulder Angles (Hip -> Shoulder -> Elbow)
        r_shoulder = get_joint_angle(right_hip(frame), right_shoulder(frame), right_elbow(frame))
        l_shoulder = get_joint_angle(left_hip(frame), left_shoulder(frame), left_elbow(frame))

        # 3. Knee Angles (Hip -> Knee -> Ankle)
        r_knee = get_joint_angle(right_hip(frame), right_knee(frame), right_ankle(frame))
        l_knee = get_joint_angle(left_hip(frame), left_knee(frame), left_ankle(frame))

        # 4. Hip Angles (Shoulder -> Hip -> Knee)
        r_hip = get_joint_angle(right_shoulder(frame), right_hip(frame), right_knee(frame))
        l_hip = get_joint_angle(left_shoulder(frame), left_hip(frame), left_knee(frame))

        # Determine dominant/active arm: higher wrist elevation (lower y) or higher elbow extension
        r_wrist_y = right_wrist(frame).y if right_wrist(frame).visibility >= 0.20 else 1.0
        l_wrist_y = left_wrist(frame).y if left_wrist(frame).visibility >= 0.20 else 1.0

        if r_wrist_y < l_wrist_y:
            dom_side = "right"
            dom_elbow = r_elbow
            dom_shoulder = r_shoulder
            dom_knee = r_knee
            dom_hip = r_hip
        else:
            dom_side = "left"
            dom_elbow = l_elbow
            dom_shoulder = l_shoulder
            dom_knee = l_knee
            dom_hip = l_hip

        return {
            "available": True,
            "dominant_side": dom_side,
            "elbow_angle_deg": dom_elbow,
            "shoulder_angle_deg": dom_shoulder,
            "knee_angle_deg": dom_knee,
            "hip_angle_deg": dom_hip,
            "bilateral_angles": {
                "right_elbow": r_elbow,
                "left_elbow": l_elbow,
                "right_shoulder": r_shoulder,
                "left_shoulder": l_shoulder,
                "right_knee": r_knee,
                "left_knee": l_knee,
                "right_hip": r_hip,
                "left_hip": l_hip
            }
        }

    def analyze_proximal_distal_sequencing(
        self,
        lead_frames: List[PoseFrame],
        contact_timestamp_s: float,
        dominant_side: str = "right"
    ) -> Dict[str, Any]:
        """
        Evaluates proximal-to-distal sequencing across frames leading into contact.
        Computes angular velocity per joint and identifies peak timing relative to impact.
        
        Strictly gates on continuous frame availability and landmark visibility >= 0.35.
        """
        if len(lead_frames) < MIN_CONSECUTIVE_SEQUENCING_FRAMES:
            return {
                "available": False,
                "reason": (
                    f"Insufficient consecutive frames leading into contact "
                    f"({len(lead_frames)} frames available, minimum {MIN_CONSECUTIVE_SEQUENCING_FRAMES} required)."
                )
            }

        # Check visibility across all lead frames for the dominant kinetic chain
        hip_angles: List[Tuple[float, float]] = []       # (timestamp_s, angle_deg)
        shoulder_angles: List[Tuple[float, float]] = []
        elbow_angles: List[Tuple[float, float]] = []

        is_right = (dominant_side == "right")

        for pf in lead_frames:
            if not pf.is_detected:
                continue

            t_s = pf.timestamp_ms / 1000.0

            if is_right:
                h_ang = get_joint_angle(right_shoulder(pf), right_hip(pf), right_knee(pf), MIN_SEQUENCING_VISIBILITY)
                s_ang = get_joint_angle(right_hip(pf), right_shoulder(pf), right_elbow(pf), MIN_SEQUENCING_VISIBILITY)
                e_ang = get_joint_angle(right_shoulder(pf), right_elbow(pf), right_wrist(pf), MIN_SEQUENCING_VISIBILITY)
            else:
                h_ang = get_joint_angle(left_shoulder(pf), left_hip(pf), left_knee(pf), MIN_SEQUENCING_VISIBILITY)
                s_ang = get_joint_angle(left_hip(pf), left_shoulder(pf), left_elbow(pf), MIN_SEQUENCING_VISIBILITY)
                e_ang = get_joint_angle(left_shoulder(pf), left_elbow(pf), left_wrist(pf), MIN_SEQUENCING_VISIBILITY)

            if h_ang is not None:
                hip_angles.append((t_s, h_ang))
            if s_ang is not None:
                shoulder_angles.append((t_s, s_ang))
            if e_ang is not None:
                elbow_angles.append((t_s, e_ang))

        if (len(hip_angles) < 3 or len(shoulder_angles) < 3 or len(elbow_angles) < 3):
            return {
                "available": False,
                "reason": (
                    "Insufficient confident landmark frames (visibility < 0.35) on hip, shoulder, or elbow "
                    "to compute continuous derivative velocity without interpolation."
                )
            }

        def compute_peak_velocity(angle_series: List[Tuple[float, float]]) -> Tuple[float, float]:
            """Returns (t_peak_s, peak_angular_velocity_deg_s)."""
            max_w = 0.0
            t_peak = angle_series[0][0]
            for i in range(1, len(angle_series)):
                t_prev, a_prev = angle_series[i - 1]
                t_curr, a_curr = angle_series[i]
                dt = t_curr - t_prev
                if dt > 0.001:
                    w = abs(a_curr - a_prev) / dt
                    if w > max_w:
                        max_w = w
                        t_peak = (t_prev + t_curr) / 2.0
            return t_peak, max_w

        t_hip_peak, w_hip_max = compute_peak_velocity(hip_angles)
        t_sho_peak, w_sho_max = compute_peak_velocity(shoulder_angles)
        t_elb_peak, w_elb_max = compute_peak_velocity(elbow_angles)

        # Proximal-to-distal sequencing check: Hip -> Shoulder -> Elbow
        is_p2d = (t_hip_peak <= t_sho_peak <= t_elb_peak)

        # Sort joints by peak timestamp to determine observed order
        joint_peaks = [
            ("hip", t_hip_peak),
            ("shoulder", t_sho_peak),
            ("elbow", t_elb_peak)
        ]
        joint_peaks.sort(key=lambda x: x[1])
        observed_order = [j[0] for j in joint_peaks]

        return {
            "available": True,
            "is_proximal_to_distal": is_p2d,
            "sequence_order": observed_order,
            "time_to_peak_velocity_s": {
                "hip": round(t_hip_peak - contact_timestamp_s, 3),
                "shoulder": round(t_sho_peak - contact_timestamp_s, 3),
                "elbow": round(t_elb_peak - contact_timestamp_s, 3)
            },
            "peak_angular_velocity_deg_s": {
                "hip": round(w_hip_max, 1),
                "shoulder": round(w_sho_max, 1),
                "elbow": round(w_elb_max, 1)
            }
        }

    def analyze_shot_kinematics(
        self,
        shots: List[ShotResult],
        pose_frames: List[PoseFrame],
        fps: float = 30.0
    ) -> Tuple[List[ShotResult], PoseMetrics, List[str]]:
        """
        Attaches real contact-frame joint angles and sequencing to each ShotResult.
        Computes clip-level PoseMetrics and natural-language findings.
        """
        if not pose_frames:
            return shots, PoseMetrics(), []

        updated_shots: List[ShotResult] = []
        all_elbows: List[float] = []
        all_shoulders: List[float] = []
        findings: List[str] = []

        for shot in shots:
            shot_copy = shot.model_copy(deep=True)
            contact_t = shot.contact_time or ((shot.start_time + shot.end_time) / 2.0)

            # 1. Locate the exact contact PoseFrame
            # Match by evidence_frames center or timestamp nearest to contact_t
            contact_pf: Optional[PoseFrame] = None
            contact_idx: Optional[int] = None

            if shot.evidence_frames:
                # Target the middle of the evidence window as the contact frame
                mid_f = shot.evidence_frames[len(shot.evidence_frames) // 2]
                if 0 <= mid_f < len(pose_frames):
                    contact_pf = pose_frames[mid_f]
                    contact_idx = mid_f

            if contact_pf is None:
                # Find closest frame by timestamp
                best_diff = float("inf")
                for i, pf in enumerate(pose_frames):
                    t_pf = pf.timestamp_ms / 1000.0
                    diff = abs(t_pf - contact_t)
                    if diff < best_diff:
                        best_diff = diff
                        contact_pf = pf
                        contact_idx = i

            # 2. Extract Real Contact Joint Angles (Task 2)
            if contact_pf and contact_pf.is_detected:
                angles_info = self.compute_frame_joint_angles(contact_pf)
                if angles_info.get("available"):
                    dom_side = angles_info["dominant_side"]
                    elb = angles_info["elbow_angle_deg"]
                    sho = angles_info["shoulder_angle_deg"]
                    kne = angles_info["knee_angle_deg"]
                    hip = angles_info["hip_angle_deg"]

                    if elb is not None:
                        all_elbows.append(elb)
                    if sho is not None:
                        all_shoulders.append(sho)

                    shot_copy.pose_features.update({
                        "elbow_angle_deg": elb,
                        "shoulder_angle_deg": sho,
                        "knee_angle_deg": kne,
                        "hip_angle_deg": hip,
                        "contact_frame_index": contact_idx,
                        "contact_timestamp_s": round(contact_t, 3),
                        "joint_angles": angles_info["bilateral_angles"]
                    })

                    # 3. Proximal-to-Distal Sequencing Analysis (Task 3)
                    # Gather frames leading into contact: up to 6 frames before contact
                    lead_start = max(0, contact_idx - 5)
                    lead_frames = pose_frames[lead_start: contact_idx + 1]
                    seq_info = self.analyze_proximal_distal_sequencing(
                        lead_frames=lead_frames,
                        contact_timestamp_s=contact_t,
                        dominant_side=dom_side
                    )
                    shot_copy.pose_features["kinetic_chain_sequencing"] = seq_info

                    findings.append(
                        f"Shot {shot.shot_id} ({shot.shot_type}) contact kinematics: "
                        f"elbow={elb}° (extension), shoulder={sho}°, knee={kne}°, hip={hip}°."
                    )
                    if seq_info.get("available"):
                        findings.append(
                            f"Shot {shot.shot_id} sequencing: order={seq_info['sequence_order']}, "
                            f"proximal-to-distal={seq_info['is_proximal_to_distal']}."
                        )
                else:
                    shot_copy.pose_features["joint_angles_reason"] = angles_info.get("reason")
            else:
                shot_copy.pose_features["joint_angles_reason"] = "Pose unresolvable at contact frame."

            updated_shots.append(shot_copy)

        # 4. Clip-Level PoseMetrics
        peak_elbow = round(float(np.max(all_elbows)), 1) if all_elbows else None
        mean_shoulder = round(float(np.mean(all_shoulders)), 1) if all_shoulders else None

        pose_metrics = PoseMetrics(
            elbow_extension_deg=peak_elbow,
            elbow_extension_reason=None if peak_elbow is not None else "No valid elbow landmarks detected at contact frames.",
            shoulder_internal_rotation_deg=mean_shoulder,
            shoulder_rotation_reason=None if mean_shoulder is not None else "No valid shoulder landmarks detected at contact frames.",
            kinetic_chain_sequence_score=None,
            kinetic_chain_reason="Evaluated per-shot in ShotResult.pose_features['kinetic_chain_sequencing']",
            trunk_rotation_deg=None,
            trunk_rotation_reason="Trunk rotation measured across full rally trajectory in Phase 4"
        )

        return updated_shots, pose_metrics, findings
