"""
Deterministic 2D joint angle kinematics, temporal smoothing, and cycle-aware ROM.

Joint Definitions & Mathematical Landmark Formulas:
- Left Hip Angle:  L_SHOULDER(11) -> L_HIP(23) -> L_KNEE(25)
- Right Hip Angle: R_SHOULDER(12) -> R_HIP(24) -> R_KNEE(26)
- Left Knee Angle:  L_HIP(23) -> L_KNEE(25) -> L_ANKLE(27)
- Right Knee Angle: R_HIP(24) -> R_KNEE(26) -> R_ANKLE(28)
- Left Ankle Angle: L_KNEE(25) -> L_ANKLE(27) -> L_FOOT_INDEX(31) [fallback L_HEEL(29)]
- Right Ankle Angle: R_KNEE(26) -> R_ANKLE(28) -> R_FOOT_INDEX(32) [fallback R_HEEL(30)]

Vector Angle Formula:
For joint B formed by points A-B-C:
  vector_BA = A - B
  vector_BC = C - B
  angle(B) = acos( clamp( (BA . BC) / (|BA| * |BC| + eps), -1.0, 1.0 ) ) * (180.0 / pi)
"""
import math
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from pydantic import BaseModel, Field

from ..schemas import PoseFrame, Landmark, GaitEvent, Side
from ..pose.landmarks import (
    left_shoulder, right_shoulder,
    left_hip, right_hip,
    left_knee, right_knee,
    left_ankle, right_ankle,
    left_heel, right_heel,
    left_foot_index, right_foot_index
)
from ..events.smoothing import interpolate_nans, savgol_smooth, moving_average

MIN_LANDMARK_VISIBILITY = 0.30
EPSILON = 1e-7


def calculate_2d_angle(
    pt_a: Landmark,
    pt_b: Landmark,
    pt_c: Landmark,
    min_visibility: float = MIN_LANDMARK_VISIBILITY
) -> Optional[float]:
    """
    Computes the 2D joint angle at vertex B formed by points A, B, and C.
    
    Returns:
        Angle in degrees [0.0, 180.0] or None if any landmark visibility is below threshold
        or vectors have near-zero magnitude.
    """
    if (pt_a.visibility < min_visibility or
        pt_b.visibility < min_visibility or
        pt_c.visibility < min_visibility):
        return None

    # Vector BA = A - B
    ba_x = pt_a.x - pt_b.x
    ba_y = pt_a.y - pt_b.y

    # Vector BC = C - B
    bc_x = pt_c.x - pt_b.x
    bc_y = pt_c.y - pt_b.y

    mag_ba = math.hypot(ba_x, ba_y)
    mag_bc = math.hypot(bc_x, bc_y)

    if mag_ba < EPSILON or mag_bc < EPSILON:
        return None

    # Dot product
    dot_prod = (ba_x * bc_x) + (ba_y * bc_y)
    cos_theta = dot_prod / (mag_ba * mag_bc)

    # Prevent numerical instability outside [-1.0, 1.0]
    clamped_cos = max(-1.0, min(1.0, cos_theta))
    angle_rad = math.acos(clamped_cos)
    angle_deg = math.degrees(angle_rad)

    return float(round(angle_deg, 2))


def smooth_angle_series(
    raw_angles: List[Optional[float]],
    fps: float = 30.0,
    max_interpolation_gap: int = 4
) -> List[Optional[float]]:
    """
    Smooths raw angle time series while preserving true kinematic peaks, timestamps,
    and handling short gaps without propagating across long missing data periods.
    """
    if not raw_angles:
        return []

    # Convert None to NaN for numeric filtering
    float_series = [val if val is not None else float("nan") for val in raw_angles]

    # Interpolate only short gaps
    interpolated = interpolate_nans(float_series, max_gap=max_interpolation_gap)

    # Apply Savitzky-Golay filtering (zero phase-lag)
    smoothed = savgol_smooth(interpolated, fps=fps)

    # Convert NaNs back to None for clean serialization
    result: List[Optional[float]] = []
    for s_val in smoothed:
        if s_val is None or math.isnan(s_val):
            result.append(None)
        else:
            result.append(float(round(s_val, 2)))

    return result


@dataclass
class JointAngleTimeSeries:
    joint_name: str
    landmarks_used: str
    raw_angles: List[Optional[float]]
    smoothed_angles: List[Optional[float]]
    timestamps_seconds: List[float]
    valid_frame_count: int


@dataclass
class CycleROM:
    cycle_index: int
    start_time: float
    end_time: float
    min_angle_deg: float
    max_angle_deg: float
    rom_deg: float
    valid_samples: int


@dataclass
class JointROM:
    joint_name: str
    min_angle_deg: Optional[float]
    max_angle_deg: Optional[float]
    rom_deg: Optional[float]
    cycle_roms: List[CycleROM] = field(default_factory=list)
    valid_cycles: int = 0
    valid_frames: int = 0
    confidence: float = 0.0


@dataclass
class BilateralJointROM:
    joint_type: str  # "hip", "knee", "ankle"
    left: JointROM
    right: JointROM
    rom_difference_deg: Optional[float]
    asymmetry_pct: Optional[float]


def compute_bilateral_asymmetry(left_val: Optional[float], right_val: Optional[float]) -> Optional[float]:
    """
    Calculates bilateral asymmetry percentage:
    Asymmetry% = 100 * |Left - Right| / (0.5 * (Left + Right) + eps)
    """
    if left_val is None or right_val is None:
        return None
    if left_val <= 0.0 and right_val <= 0.0:
        return 0.0
    denom = 0.5 * (left_val + right_val) + EPSILON
    asym = (100.0 * abs(left_val - right_val)) / denom
    return float(round(asym, 2))


def extract_joint_angles(
    frames: List[PoseFrame],
    fps: float = 30.0
) -> Dict[str, JointAngleTimeSeries]:
    """
    Calculates time-series angles for all 6 lower-body and pelvic joints:
    - left_hip, right_hip
    - left_knee, right_knee
    - left_ankle, right_ankle
    """
    timestamps = [f.timestamp_ms / 1000.0 if f.timestamp_ms > 0 else (i / max(1.0, fps)) for i, f in enumerate(frames)]
    
    raw_left_hip: List[Optional[float]] = []
    raw_right_hip: List[Optional[float]] = []
    raw_left_knee: List[Optional[float]] = []
    raw_right_knee: List[Optional[float]] = []
    raw_left_ankle: List[Optional[float]] = []
    raw_right_ankle: List[Optional[float]] = []

    for frame in frames:
        # Left Hip: L_SHOULDER(11) -> L_HIP(23) -> L_KNEE(25)
        raw_left_hip.append(calculate_2d_angle(
            left_shoulder(frame), left_hip(frame), left_knee(frame)
        ))
        # Right Hip: R_SHOULDER(12) -> R_HIP(24) -> R_KNEE(26)
        raw_right_hip.append(calculate_2d_angle(
            right_shoulder(frame), right_hip(frame), right_knee(frame)
        ))

        # Left Knee: L_HIP(23) -> L_KNEE(25) -> L_ANKLE(27)
        raw_left_knee.append(calculate_2d_angle(
            left_hip(frame), left_knee(frame), left_ankle(frame)
        ))
        # Right Knee: R_HIP(24) -> R_KNEE(26) -> R_ANKLE(28)
        raw_right_knee.append(calculate_2d_angle(
            right_hip(frame), right_knee(frame), right_ankle(frame)
        ))

        # Left Ankle: L_KNEE(25) -> L_ANKLE(27) -> L_FOOT_INDEX(31) [fallback L_HEEL(29)]
        l_foot = left_foot_index(frame) if left_foot_index(frame).visibility >= MIN_LANDMARK_VISIBILITY else left_heel(frame)
        raw_left_ankle.append(calculate_2d_angle(
            left_knee(frame), left_ankle(frame), l_foot
        ))
        
        # Right Ankle: R_KNEE(26) -> R_ANKLE(28) -> R_FOOT_INDEX(32) [fallback R_HEEL(30)]
        r_foot = right_foot_index(frame) if right_foot_index(frame).visibility >= MIN_LANDMARK_VISIBILITY else right_heel(frame)
        raw_right_ankle.append(calculate_2d_angle(
            right_knee(frame), right_ankle(frame), r_foot
        ))

    joint_configs = [
        ("left_hip", "L_SHOULDER(11) -> L_HIP(23) -> L_KNEE(25)", raw_left_hip),
        ("right_hip", "R_SHOULDER(12) -> R_HIP(24) -> R_KNEE(26)", raw_right_hip),
        ("left_knee", "L_HIP(23) -> L_KNEE(25) -> L_ANKLE(27)", raw_left_knee),
        ("right_knee", "R_HIP(24) -> R_KNEE(26) -> R_ANKLE(28)", raw_right_knee),
        ("left_ankle", "L_KNEE(25) -> L_ANKLE(27) -> L_FOOT_INDEX(31)/L_HEEL(29)", raw_left_ankle),
        ("right_ankle", "R_KNEE(26) -> R_ANKLE(28) -> R_FOOT_INDEX(32)/R_HEEL(30)", raw_right_ankle),
    ]

    results: Dict[str, JointAngleTimeSeries] = {}
    for name, lm_desc, raw_list in joint_configs:
        valid_cnt = sum(1 for v in raw_list if v is not None)
        smoothed_list = smooth_angle_series(raw_list, fps=fps)
        results[name] = JointAngleTimeSeries(
            joint_name=name,
            landmarks_used=lm_desc,
            raw_angles=raw_list,
            smoothed_angles=smoothed_list,
            timestamps_seconds=timestamps,
            valid_frame_count=valid_cnt
        )

    return results


def compute_cycle_aware_rom(
    series: JointAngleTimeSeries,
    events: List[GaitEvent],
    target_side: Side
) -> JointROM:
    """
    Computes Range of Motion (ROM) partitioned by validated gait cycles.
    Uses consecutive ipsilateral heel-strike events as cycle boundaries, calculates
    cycle-level min/max/ROM, and aggregates using the median across valid cycles.
    """
    ipsi_events = sorted([e for e in events if e.side == target_side], key=lambda e: e.time_seconds)
    timestamps = series.timestamps_seconds
    angles = series.smoothed_angles

    valid_cycle_roms: List[CycleROM] = []
    
    # If at least 2 ipsilateral events exist, segment into cycles
    if len(ipsi_events) >= 2:
        for idx, (ev_start, ev_end) in enumerate(zip(ipsi_events[:-1], ipsi_events[1:])):
            t_start = ev_start.time_seconds
            t_end = ev_end.time_seconds

            cycle_angles: List[float] = []
            for t, a in zip(timestamps, angles):
                if t_start <= t <= t_end and a is not None and not math.isnan(a):
                    cycle_angles.append(a)

            # Require at least 5 angle samples per valid gait cycle
            if len(cycle_angles) >= 5:
                c_min = min(cycle_angles)
                c_max = max(cycle_angles)
                c_rom = c_max - c_min
                valid_cycle_roms.append(CycleROM(
                    cycle_index=idx + 1,
                    start_time=round(t_start, 3),
                    end_time=round(t_end, 3),
                    min_angle_deg=round(c_min, 1),
                    max_angle_deg=round(c_max, 1),
                    rom_deg=round(c_rom, 1),
                    valid_samples=len(cycle_angles)
                ))

    # Calculate aggregate ROM
    if valid_cycle_roms:
        rom_values = sorted(c.rom_deg for c in valid_cycle_roms)
        min_values = sorted(c.min_angle_deg for c in valid_cycle_roms)
        max_values = sorted(c.max_angle_deg for c in valid_cycle_roms)

        mid = len(rom_values) // 2
        median_rom = float(rom_values[mid]) if len(rom_values) % 2 == 1 else float((rom_values[mid - 1] + rom_values[mid]) / 2.0)
        median_min = float(min_values[mid]) if len(min_values) % 2 == 1 else float((min_values[mid - 1] + min_values[mid]) / 2.0)
        median_max = float(max_values[mid]) if len(max_values) % 2 == 1 else float((max_values[mid - 1] + max_values[mid]) / 2.0)

        conf = min(1.0, 0.4 + 0.15 * len(valid_cycle_roms))
        return JointROM(
            joint_name=series.joint_name,
            min_angle_deg=round(median_min, 1),
            max_angle_deg=round(median_max, 1),
            rom_deg=round(median_rom, 1),
            cycle_roms=valid_cycle_roms,
            valid_cycles=len(valid_cycle_roms),
            valid_frames=series.valid_frame_count,
            confidence=round(conf, 3)
        )

    # Fallback if insufficient multi-cycle gait events: compute across entire valid time series
    valid_all = [a for a in angles if a is not None and not math.isnan(a)]
    if len(valid_all) >= 10:
        a_min = min(valid_all)
        a_max = max(valid_all)
        return JointROM(
            joint_name=series.joint_name,
            min_angle_deg=round(a_min, 1),
            max_angle_deg=round(a_max, 1),
            rom_deg=round(a_max - a_min, 1),
            cycle_roms=[],
            valid_cycles=0,
            valid_frames=len(valid_all),
            confidence=0.45
        )

    return JointROM(
        joint_name=series.joint_name,
        min_angle_deg=None,
        max_angle_deg=None,
        rom_deg=None,
        cycle_roms=[],
        valid_cycles=0,
        valid_frames=len(valid_all),
        confidence=0.0
    )


@dataclass
class AllJointsKinematics:
    time_series: Dict[str, JointAngleTimeSeries]
    roms: Dict[str, JointROM]
    bilateral: Dict[str, BilateralJointROM]
