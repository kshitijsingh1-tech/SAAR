"""
Badminton Movement Analysis and Court-Plane Spatial Tracking.
Computes pelvis/hip player center trajectory, transforms image coordinates
to metric court plane via calibrated homography, and evaluates spatial metrics
(distance, speed, convex-hull coverage, 9-zone dynamic region occupancy).

REASONING SAFEGUARD (Section 11 Master Spec):
This module strictly produces objective OBSERVATION-category facts.
It must NEVER emit prescriptive hypotheses (e.g. "player should utilize left space more").
Hypothesis synthesis is strictly delegated to downstream strategic analysis (Phase 13).
"""
import math
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy.spatial import ConvexHull

from .schemas import (
    PoseFrame,
    CourtCalibration,
    CourtMetrics,
    MovementMetrics,
    RegionOccupancy,
    PlayerMetadata
)
from .court_detector import (
    COURT_LENGTH_M,
    COURT_WIDTH_M,
    pixel_to_court_m
)

# Active court area constants
COURT_AREA_HALF_M2 = (COURT_WIDTH_M * COURT_LENGTH_M) / 2.0  # 40.87 m²
COURT_AREA_FULL_M2 = COURT_WIDTH_M * COURT_LENGTH_M          # 81.74 m²

# 9 Tactical Court Regions (Section 10 Master Spec)
REGION_METADATA = {
    "front_left": "Front Left (Forecourt Net)",
    "front_center": "Front Center (Forecourt T-Junction)",
    "front_right": "Front Right (Forecourt Net)",
    "mid_left": "Midcourt Left",
    "mid_center": "Midcourt Center (Base Position)",
    "mid_right": "Midcourt Right",
    "rear_left": "Rearcourt Left (Deep Corner)",
    "rear_center": "Rearcourt Center (Deep Baseline)",
    "rear_right": "Rearcourt Right (Deep Corner)",
}


class PlayerTrajectoryPoint:
    """Represents a single temporal player center observation."""
    def __init__(
        self,
        frame_index: int,
        timestamp_ms: int,
        pixel_x: float,
        pixel_y: float,
        court_x: Optional[float] = None,
        court_y: Optional[float] = None,
        left_foot_px: Optional[Tuple[float, float]] = None,
        right_foot_px: Optional[Tuple[float, float]] = None,
        confidence: float = 1.0
    ):
        self.frame_index = frame_index
        self.timestamp_ms = timestamp_ms
        self.pixel_x = pixel_x
        self.pixel_y = pixel_y
        self.court_x = court_x
        self.court_y = court_y
        self.left_foot_px = left_foot_px
        self.right_foot_px = right_foot_px
        self.confidence = confidence


def extract_player_center_trajectory(
    pose_frames: List[PoseFrame],
    court_calibration: Optional[CourtCalibration] = None
) -> List[PlayerTrajectoryPoint]:
    """
    Computes per-frame player center position (preferring pelvis/hip midpoint per Section 9
    of the master spec, retaining foot positions separately for movement analysis).
    Transforms coordinates to metric court plane if court is calibrated.
    """
    trajectory: List[PlayerTrajectoryPoint] = []
    H_np = np.array(court_calibration.homography_matrix) if (court_calibration and court_calibration.is_calibrated and court_calibration.homography_matrix) else None

    for pf in pose_frames:
        if not pf.is_detected or len(pf.landmarks) < 33:
            continue

        l_hip = pf.landmarks[23]
        r_hip = pf.landmarks[24]
        l_sh = pf.landmarks[11]
        r_sh = pf.landmarks[12]

        # Prefer hip midpoint (center of mass proxy)
        if l_hip.visibility >= 0.15 and r_hip.visibility >= 0.15:
            cx_norm = (l_hip.x + r_hip.x) / 2.0
            cy_norm = (l_hip.y + r_hip.y) / 2.0
            conf = (l_hip.visibility + r_hip.visibility) / 2.0
        elif l_sh.visibility >= 0.15 and r_sh.visibility >= 0.15:
            cx_norm = (l_sh.x + r_sh.x) / 2.0
            cy_norm = (l_sh.y + r_sh.y) / 2.0
            conf = (l_sh.visibility + r_sh.visibility) / 2.0
        else:
            continue

        px_x = float(cx_norm * pf.source_width)
        px_y = float(cy_norm * pf.source_height)

        # Floor contact point for 2D court plane homography (ankle midpoint per Section 9)
        l_ank = pf.landmarks[27]
        r_ank = pf.landmarks[28]
        l_foot = (float(l_ank.x * pf.source_width), float(l_ank.y * pf.source_height)) if l_ank.visibility >= 0.15 else None
        r_foot = (float(r_ank.x * pf.source_width), float(r_ank.y * pf.source_height)) if r_ank.visibility >= 0.15 else None

        if l_foot is not None and r_foot is not None:
            foot_px_x = (l_foot[0] + r_foot[0]) / 2.0
            foot_px_y = (l_foot[1] + r_foot[1]) / 2.0
        elif l_foot is not None:
            foot_px_x, foot_px_y = l_foot
        elif r_foot is not None:
            foot_px_x, foot_px_y = r_foot
        else:
            foot_px_x, foot_px_y = px_x, px_y

        # Project floor contact point to metric court plane if calibrated
        court_coords = None
        if H_np is not None:
            proj = pixel_to_court_m(foot_px_x, foot_px_y, H_np)
            if proj is not None:
                cx, cy = proj
                # Allowable realistic run-off zone around the court
                w_max = (court_calibration.court_dimensions_m[0] if (court_calibration and court_calibration.court_dimensions_m) else COURT_WIDTH_M) + 1.5
                l_max = (court_calibration.court_dimensions_m[1] if (court_calibration and court_calibration.court_dimensions_m) else COURT_LENGTH_M) + 2.0
                if -1.5 <= cx <= w_max and -2.0 <= cy <= l_max:
                    court_coords = (float(round(cx, 3)), float(round(cy, 3)))

        court_x = court_coords[0] if court_coords else None
        court_y = court_coords[1] if court_coords else None

        trajectory.append(PlayerTrajectoryPoint(
            frame_index=pf.frame_index,
            timestamp_ms=pf.timestamp_ms,
            pixel_x=px_x,
            pixel_y=px_y,
            court_x=court_x,
            court_y=court_y,
            left_foot_px=l_foot,
            right_foot_px=r_foot,
            confidence=conf
        ))

    return trajectory


def classify_court_region(
    x_m: float,
    y_m: float,
    court_orientation: str = "near_court"
) -> str:
    """
    Classifies a metric court position (x_m, y_m) into one of 9 dynamic regions (Section 10).
    Width (6.10m): 3 equal lateral lanes (Left, Center, Right).
    Length: 3 equal longitudinal depth zones for active player half-court.
    """
    # 1. Lateral partition (3 lanes across 6.10m width)
    lane_w = COURT_WIDTH_M / 3.0  # ~2.033m
    if x_m < lane_w:
        lat = "left"
    elif x_m < 2.0 * lane_w:
        lat = "center"
    else:
        lat = "right"

    # 2. Longitudinal partition (depth zones)
    # If playing near court: y in [6.70m (net), 13.40m (baseline)]
    # Forecourt: [6.70, 8.933m), Midcourt: [8.933, 11.167m), Rearcourt: [11.167, 13.40m]
    if court_orientation == "near_court" or y_m >= 6.70:
        half_start = 6.70
        half_len = 6.70
        zone_len = half_len / 3.0  # ~2.233m
        if y_m < half_start + zone_len:
            depth = "front"
        elif y_m < half_start + 2.0 * zone_len:
            depth = "mid"
        else:
            depth = "rear"
    elif court_orientation == "far_court" or y_m < 6.70:
        # Far court: y in [0.0m (baseline), 6.70m (net)]
        zone_len = 6.70 / 3.0
        if y_m < zone_len:
            depth = "rear"  # Near far baseline
        elif y_m < 2.0 * zone_len:
            depth = "mid"
        else:
            depth = "front"  # Near net
    else:
        # Full court 3-way split
        zone_len = COURT_LENGTH_M / 3.0
        if y_m < zone_len:
            depth = "front"
        elif y_m < 2.0 * zone_len:
            depth = "mid"
        else:
            depth = "rear"

    return f"{depth}_{lat}"


class BadmintonMovementAnalyzer:
    """
    Computes spatial kinematics, coverage, and region occupancy metrics for badminton video.
    Strictly gates physical metrics on real homography court calibration.
    """

    def analyze_movement(
        self,
        pose_frames: List[PoseFrame],
        court_calibration: Optional[CourtCalibration] = None,
        player_metadata: Optional[PlayerMetadata] = None
    ) -> Tuple[MovementMetrics, CourtMetrics, List[str]]:
        """
        Extracts player center path, computes physical kinematics if calibrated,
        and generates objective observation findings.
        """
        # 1. Extract trajectory
        trajectory = extract_player_center_trajectory(pose_frames, court_calibration)

        # 2. Uncalibrated Branch: Strict Calibration Gating
        is_calibrated = court_calibration is not None and court_calibration.is_calibrated and court_calibration.homography_matrix is not None
        if not is_calibrated:
            reason = (
                f"Court not calibrated: {court_calibration.uncalibrated_reason}"
                if (court_calibration and court_calibration.uncalibrated_reason)
                else "Court not calibrated; physical distance and coverage metrics require metric homography."
            )
            movement_metrics = MovementMetrics(
                total_distance_m=None,
                total_distance_reason=reason,
                average_speed_m_s=None,
                max_speed_m_s=None,
                speed_reason=reason,
                region_occupancies=[],
                region_occupancy_reason=reason
            )
            court_metrics = CourtMetrics(
                court_coverage_pct=None,
                court_coverage_reason=reason,
                convex_hull_area_m2=None,
                court_area_m2=COURT_AREA_HALF_M2
            )
            findings = [
                f"Movement path extracted across {len(trajectory)} frames in 2D image coordinates.",
                f"Physical spatial metrics unavailable: {reason}"
            ]
            return movement_metrics, court_metrics, findings

        # 3. Calibrated Branch: Compute Real Physical Kinematics
        valid_points = [p for p in trajectory if p.court_x is not None and p.court_y is not None]

        if len(valid_points) < 2:
            movement_metrics = MovementMetrics(
                total_distance_m=0.0,
                total_distance_reason="Insufficient calibrated positions detected to evaluate distance.",
                average_speed_m_s=0.0,
                max_speed_m_s=0.0,
                speed_reason="Insufficient calibrated positions.",
                region_occupancies=[],
                region_occupancy_reason="Insufficient positions."
            )
            court_metrics = CourtMetrics(
                court_coverage_pct=0.0,
                court_coverage_reason="Insufficient positions for convex hull.",
                convex_hull_area_m2=0.0,
                court_area_m2=COURT_AREA_HALF_M2
            )
            findings = ["Fewer than 2 calibrated player positions detected; spatial kinematics omitted."]
            return movement_metrics, court_metrics, findings

        # A. Total distance & speeds with trajectory smoothing & jitter deadband filtering
        raw_x = [p.court_x for p in valid_points]
        raw_y = [p.court_y for p in valid_points]

        # 5-tap moving window median smoothing to eliminate sub-pixel landmark jitter
        window_size = 5 if len(valid_points) >= 5 else 3 if len(valid_points) >= 3 else 1
        smoothed_x = []
        smoothed_y = []
        for i in range(len(valid_points)):
            w_start = max(0, i - window_size // 2)
            w_end = min(len(valid_points), i + window_size // 2 + 1)
            smoothed_x.append(float(np.median(raw_x[w_start:w_end])))
            smoothed_y.append(float(np.median(raw_y[w_start:w_end])))

        total_distance = 0.0
        speeds: List[float] = []
        total_dt = 0.0

        for i in range(len(valid_points) - 1):
            dt = max(0.001, (valid_points[i + 1].timestamp_ms - valid_points[i].timestamp_ms) / 1000.0)
            total_dt += dt

            # Distance computed on smoothed trajectory
            dist = math.hypot(smoothed_x[i + 1] - smoothed_x[i], smoothed_y[i + 1] - smoothed_y[i])

            # Deadband filter: micro-movements < 2.5cm between frames represent standing landmark jitter
            if dist >= 0.025:
                total_distance += dist

            # Instantaneous speed bounded by physiological court movement limit (5.5 m/s maximum badminton sprint)
            spd = dist / dt
            if spd <= 5.5:
                speeds.append(spd)
            elif spd > 5.5:
                # Clamp extreme jumps to peak sprint velocity
                speeds.append(4.8)

        total_distance = float(round(total_distance, 1))
        avg_speed = float(round(total_distance / max(0.1, total_dt), 1))
        max_speed = float(round(np.percentile(speeds, 90), 1)) if speeds else 0.0

        # B. Court Coverage Ratio via scipy.spatial.ConvexHull
        coords_2d = np.array([[p.court_x, p.court_y] for p in valid_points], dtype=np.float64)
        hull_area = 0.0
        ref_area = COURT_AREA_HALF_M2  # Standard active player half-court (40.87 m²)

        # Check for collinearity or distinct points
        unique_coords = np.unique(coords_2d, axis=0)
        if len(unique_coords) >= 3:
            try:
                hull = ConvexHull(unique_coords)
                hull_area = float(hull.volume)  # In 2D, volume is polygon area
            except Exception:
                hull_area = 0.0

        coverage_pct = float(round(min(100.0, (hull_area / ref_area) * 100.0), 1))

        # C. 9-Zone Dynamic Region Occupancy (Section 10)
        court_orientation = player_metadata.court_orientation if (player_metadata and player_metadata.court_orientation) else "near_court"

        region_times: Dict[str, float] = {r: 0.0 for r in REGION_METADATA}
        region_entries: Dict[str, int] = {r: 0 for r in REGION_METADATA}
        region_exits: Dict[str, int] = {r: 0 for r in REGION_METADATA}

        prev_region = None
        for i in range(len(valid_points)):
            p = valid_points[i]
            r_id = classify_court_region(p.court_x, p.court_y, court_orientation)

            dt = 0.033  # default fallback frame time (~30fps)
            if i < len(valid_points) - 1:
                dt = max(0.001, (valid_points[i + 1].timestamp_ms - p.timestamp_ms) / 1000.0)
            elif i > 0:
                dt = max(0.001, (p.timestamp_ms - valid_points[i - 1].timestamp_ms) / 1000.0)

            if r_id in region_times:
                region_times[r_id] += dt

            if r_id != prev_region:
                if prev_region in region_exits:
                    region_exits[prev_region] += 1
                if r_id in region_entries:
                    region_entries[r_id] += 1
                prev_region = r_id

        total_tracked_time = max(0.001, sum(region_times.values()))
        region_occupancies: List[RegionOccupancy] = []

        for r_id, r_name in REGION_METADATA.items():
            t_sec = float(round(region_times[r_id], 2))
            pct = float(round((t_sec / total_tracked_time) * 100.0, 1))
            region_occupancies.append(RegionOccupancy(
                region_id=r_id,
                name=r_name,
                time_seconds=t_sec,
                occupancy_pct=pct,
                entries=region_entries[r_id],
                exits=region_exits[r_id]
            ))

        # 4. Construct Models
        movement_metrics = MovementMetrics(
            total_distance_m=float(round(total_distance, 2)),
            total_distance_reason=None,
            average_speed_m_s=avg_speed,
            max_speed_m_s=max_speed,
            speed_reason=None,
            region_occupancies=region_occupancies,
            region_occupancy_reason=None
        )

        court_metrics = CourtMetrics(
            court_coverage_pct=coverage_pct,
            court_coverage_reason=None,
            convex_hull_area_m2=float(round(hull_area, 2)),
            court_area_m2=ref_area
        )

        # 5. REASONING SAFEGUARD (Section 11 Master Spec):
        # Emit strictly objective observation facts, without prescriptive advice or hypotheses.
        mid_c = next((r for r in region_occupancies if r.region_id == "mid_center"), None)
        mid_c_pct = mid_c.occupancy_pct if mid_c else 0.0

        left_pct = round(sum(r.occupancy_pct for r in region_occupancies if "left" in r.region_id), 1)
        right_pct = round(sum(r.occupancy_pct for r in region_occupancies if "right" in r.region_id), 1)
        center_pct = round(sum(r.occupancy_pct for r in region_occupancies if "center" in r.region_id), 1)

        findings = [
            f"Total distance covered: {total_distance:.2f}m at average speed {avg_speed:.2f} m/s (peak {max_speed:.2f} m/s).",
            f"Court coverage ratio: {coverage_pct:.1f}% ({hull_area:.2f} m² of {ref_area:.2f} m² active court area).",
            f"Occupancy distribution: Midcourt Center (Base Position) {mid_c_pct:.1f}%; Lateral: Left {left_pct}%, Center {center_pct}%, Right {right_pct}%."
        ]

        return movement_metrics, court_metrics, findings
