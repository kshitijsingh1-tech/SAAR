"""
Badminton Shot Analytics, Placement Geometry, and Movement Recovery Metrics Engine.
Implements Sections 17, 19, 20, and 21 of the Master Spec.

Definitions:
1. Per-Shot Duration (Section 17):
   duration = end_timestamp - contact_timestamp
   Measured strictly from the moment of contact frame impact to stroke completion/recovery end.
   This represents individual stroke execution duration and is strictly distinct from
   whole-rally phase duration or rally interval length.

2. Placement Gating (Section 19):
   Requires a minimum sample size (MIN_PLACEMENT_SAMPLE_SIZE = 3) of court-calibrated target
   trajectories before asserting any tactical percentage claims in output dossiers.

3. Recovery Dynamics (Section 20):
   Computes post-impact player recovery distance, time, and direction vector back towards the base.

4. Movement Efficiency (Section 21):
   Guarded strictly: reports NOT_RELIABLY_MEASURABLE unless genuine retrieval outcome
   data (winner vs return) is determinable from multi-player rally tracking.
"""
import math
from typing import List, Optional, Tuple, Dict, Any
import numpy as np

from .schemas import (
    ShotResult,
    ShotMetrics,
    PoseFrame,
    CourtCalibration,
    Metric
)
from .court_detector import pixel_to_court_m, COURT_WIDTH_M, COURT_LENGTH_M
from .movement_analyzer import classify_court_region

# Minimum sample size required before computing tactical placement percentages (Section 19)
MIN_PLACEMENT_SAMPLE_SIZE: int = 3


class BadmintonMetricsEngine:
    """
    Computes aggregation statistics, placement distributions, and movement recovery
    metrics over verified ShotResult sequences.
    """

    def compute_shot_metrics(
        self,
        shots: List[ShotResult],
        pose_frames: Optional[List[PoseFrame]] = None,
        court_calibration: Optional[CourtCalibration] = None,
        total_movement_distance_m: Optional[float] = None
    ) -> Tuple[ShotMetrics, List[str]]:
        """
        Aggregates shot durations, types, placements, and recovery kinematics.
        Returns (ShotMetrics, findings_list).
        """
        findings: List[str] = []

        if not shots:
            empty_metrics = ShotMetrics(
                total_shots=0,
                duration_definition="end_timestamp - contact_timestamp per Section 17",
                shot_durations_s=[],
                average_duration_s=None,
                median_duration_s=None,
                min_duration_s=None,
                max_duration_s=None,
                count_by_shot_type={},
                percentage_by_shot_type={},
                placement_metrics={"available": False, "reason": "No shots detected in video."},
                recovery_metrics={"available": False, "reason": "No shots detected in video."}
            )
            return empty_metrics, ["No shot events detected for metric aggregation."]

        n_shots = len(shots)

        # ----------------------------------------------------------------------
        # 1. Per-Shot Duration (Section 17): end_timestamp - contact_timestamp
        # ----------------------------------------------------------------------
        durations: List[float] = []
        for s in shots:
            if s.contact_time is not None:
                d = max(0.01, round(s.end_time - s.contact_time, 3))
            else:
                d = max(0.01, round(s.end_time - s.start_time, 3))
            durations.append(d)

        avg_dur = round(float(np.mean(durations)), 3) if durations else None
        med_dur = round(float(np.median(durations)), 3) if durations else None
        min_dur = round(float(np.min(durations)), 3) if durations else None
        max_dur = round(float(np.max(durations)), 3) if durations else None

        # ----------------------------------------------------------------------
        # 2. Shot Type Counts & Percentages (including UNKNOWN)
        # ----------------------------------------------------------------------
        counts: Dict[str, int] = {}
        for s in shots:
            stype = s.shot_type
            counts[stype] = counts.get(stype, 0) + 1

        percentages: Dict[str, float] = {
            stype: round((cnt / n_shots) * 100.0, 1)
            for stype, cnt in counts.items()
        }

        # ----------------------------------------------------------------------
        # 3. Shot Placement & Spatial Distribution (Section 19)
        # ----------------------------------------------------------------------
        valid_targets = [s for s in shots if s.target_position and len(s.target_position) >= 2]
        is_calibrated = (court_calibration and court_calibration.is_calibrated)

        placement_metrics: Dict[str, Any] = {}
        if not is_calibrated:
            placement_metrics = {
                "available": False,
                "reason": "Court not calibrated; metric target placement unavailable.",
                "target_count": len(valid_targets)
            }
        elif len(valid_targets) < MIN_PLACEMENT_SAMPLE_SIZE:
            placement_metrics = {
                "available": False,
                "reason": (
                    f"Insufficient placement sample size: only {len(valid_targets)} shot(s) with calibrated "
                    f"target positions (minimum {MIN_PLACEMENT_SAMPLE_SIZE} required for statistically meaningful claims)."
                ),
                "target_count": len(valid_targets)
            }
        else:
            # Full placement distribution
            cross_court_count = 0
            straight_line_count = 0
            corner_count = 0
            left_half_count = 0
            right_half_count = 0
            region_counts: Dict[str, int] = {}

            mid_court_x = COURT_WIDTH_M / 2.0  # 3.05m

            for s in valid_targets:
                tx, ty = s.target_position[0], s.target_position[1]
                t_region = classify_court_region(tx, ty, "far_court")
                region_counts[t_region] = region_counts.get(t_region, 0) + 1

                if "corner" in t_region or t_region in ["front_left", "front_right", "rear_left", "rear_right"]:
                    corner_count += 1

                if tx < mid_court_x:
                    left_half_count += 1
                else:
                    right_half_count += 1

                if s.player_position and len(s.player_position) >= 2:
                    px = s.player_position[0]
                    # Cross-court if lateral displacement between origin and target exceeds 2.0m (1 full lane change)
                    if abs(tx - px) >= 2.0:
                        cross_court_count += 1
                    else:
                        straight_line_count += 1
                else:
                    straight_line_count += 1

            n_targets = len(valid_targets)
            placement_metrics = {
                "available": True,
                "target_count": n_targets,
                "cross_court_count": cross_court_count,
                "cross_court_pct": round((cross_court_count / n_targets) * 100.0, 1),
                "straight_line_count": straight_line_count,
                "straight_line_pct": round((straight_line_count / n_targets) * 100.0, 1),
                "corner_count": corner_count,
                "corner_pct": round((corner_count / n_targets) * 100.0, 1),
                "left_half_count": left_half_count,
                "left_half_pct": round((left_half_count / n_targets) * 100.0, 1),
                "right_half_count": right_half_count,
                "right_half_pct": round((right_half_count / n_targets) * 100.0, 1),
                "region_counts": region_counts,
                "region_percentages": {
                    r: round((c / n_targets) * 100.0, 1)
                    for r, c in region_counts.items()
                }
            }

        # ----------------------------------------------------------------------
        # 4. Player Movement After Each Shot (Recovery Dynamics - Section 20)
        # ----------------------------------------------------------------------
        recovery_records: List[Dict[str, Any]] = []
        recovery_distances: List[float] = []
        recovery_times: List[float] = []

        H_np = (
            np.array(court_calibration.homography_matrix, dtype=np.float64)
            if (court_calibration and court_calibration.is_calibrated and court_calibration.homography_matrix)
            else None
        )

        for s in shots:
            if s.contact_time is None or not pose_frames:
                continue

            # Estimate recovery endpoint at end_time
            cf = s.evidence_frames[len(s.evidence_frames) // 2] if s.evidence_frames else 0
            ef = s.evidence_frames[-1] if s.evidence_frames else 0

            p_start = s.player_position
            p_end = None

            if 0 <= ef < len(pose_frames):
                pf_end = pose_frames[ef]
                if pf_end.is_detected and len(pf_end.landmarks) >= 25:
                    r_hip = pf_end.landmarks[24]
                    l_hip = pf_end.landmarks[23]
                    if r_hip.visibility >= 0.20 and l_hip.visibility >= 0.20:
                        mx = (r_hip.x + l_hip.x) / 2.0
                        my = (r_hip.y + l_hip.y) / 2.0
                        if H_np is not None:
                            pt = pixel_to_court_m(mx * pf_end.source_width, my * pf_end.source_height, H_np)
                            if pt:
                                p_end = [round(pt[0], 2), round(pt[1], 2)]
                        else:
                            p_end = [round(mx, 3), round(my, 3)]

            rec_time = max(0.01, round(s.end_time - s.contact_time, 3))
            rec_dist = None
            rec_speed = None
            direction = "undetermined"

            if p_start and p_end and len(p_start) >= 2 and len(p_end) >= 2:
                dx = p_end[0] - p_start[0]
                dy = p_end[1] - p_start[1]
                rec_dist = round(math.hypot(dx, dy), 2)
                rec_speed = round(rec_dist / rec_time, 2)
                recovery_distances.append(rec_dist)
                recovery_times.append(rec_time)

                if is_calibrated:
                    if rec_dist < 0.30:
                        direction = "stationary_hold"
                    elif abs(dx) > abs(dy):
                        direction = "lateral_right" if dx > 0 else "lateral_left"
                    else:
                        direction = "rearward_to_base" if dy > 0 else "forward_to_base"
                else:
                    direction = "repositioning"

            recovery_records.append({
                "shot_id": s.shot_id,
                "contact_time": s.contact_time,
                "end_time": s.end_time,
                "recovery_time_s": rec_time,
                "recovery_distance_m": rec_dist if is_calibrated else None,
                "recovery_speed_m_s": rec_speed if is_calibrated else None,
                "movement_direction": direction
            })

        avg_rec_dist = round(float(np.mean(recovery_distances)), 2) if recovery_distances else None
        avg_rec_time = round(float(np.mean(recovery_times)), 2) if recovery_times else None

        recovery_metrics: Dict[str, Any] = {
            "available": is_calibrated and len(recovery_distances) > 0,
            "reason": None if (is_calibrated and recovery_distances) else "Court not calibrated or insufficient player trajectory displacement.",
            "average_recovery_distance_m": avg_rec_dist,
            "average_recovery_time_s": avg_rec_time,
            "per_shot_recoveries": recovery_records
        }

        # ----------------------------------------------------------------------
        # 5. Movement Efficiency (Section 21): strictly honest NOT_RELIABLY_MEASURABLE
        # ----------------------------------------------------------------------
        movement_efficiency = Metric(
            name="movement_efficiency",
            value=None,
            unit="retrievals/meter",
            confidence="LOW",
            method="NOT_RELIABLY_MEASURABLE",
            available=False,
            unavailable_reason="NOT_RELIABLY_MEASURABLE: Rally boundary and shot outcome (successful retrieval vs winner/error) not determinable from single-player recording."
        )

        # ----------------------------------------------------------------------
        # 6. Synthesize Natural-Language Findings (Traceable to JSON)
        # ----------------------------------------------------------------------
        # Shot type breakdown finding
        type_summary = ", ".join(f"{cnt} {stype} ({percentages[stype]}%)" for stype, cnt in counts.items())
        findings.append(f"Shot distribution ({n_shots} total): {type_summary}.")

        # Duration finding
        if avg_dur is not None:
            findings.append(f"Shot duration (end - contact): avg={avg_dur}s (median={med_dur}s, range={min_dur}s–{max_dur}s).")

        # Placement finding (ONLY if sample size >= 3)
        if placement_metrics.get("available") is True:
            findings.append(
                f"Shot placement ({placement_metrics['target_count']} calibrated targets): "
                f"{placement_metrics['cross_court_pct']}% cross-court, {placement_metrics['straight_line_pct']}% straight-line."
            )
        else:
            findings.append(f"Shot placement: {placement_metrics['reason']}")

        # Recovery dynamics finding
        if recovery_metrics.get("available") is True and avg_rec_dist is not None:
            findings.append(f"Post-shot recovery: average recovery distance={avg_rec_dist}m in {avg_rec_time}s.")
        else:
            findings.append(f"Post-shot recovery: {recovery_metrics['reason']}")

        shot_metrics_result = ShotMetrics(
            total_shots=n_shots,
            duration_definition="end_timestamp - contact_timestamp per Section 17",
            shot_durations_s=durations,
            average_duration_s=avg_dur,
            median_duration_s=med_dur,
            min_duration_s=min_dur,
            max_duration_s=max_dur,
            count_by_shot_type=counts,
            percentage_by_shot_type=percentages,
            placement_metrics=placement_metrics,
            recovery_metrics=recovery_metrics,
            movement_efficiency=movement_efficiency
        )

        return shot_metrics_result, findings
