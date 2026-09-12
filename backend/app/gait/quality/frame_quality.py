"""
Frame-level quality assessment ported from ToddleAI QualityGate.
"""
import math
from typing import Optional
from ..schemas import Landmark, PoseFrame, FrameQuality, FrameStatus
from ..pose.landmarks import (
    left_shoulder, right_shoulder,
    left_hip, right_hip, left_knee, right_knee,
    left_ankle, right_ankle, left_heel, right_heel,
    left_foot_index, right_foot_index
)

MIN_BODY_MEASUREMENT = 0.015  # Normalized minimum measurement proxy
MAX_BODY_SCALE_SHIFT = 0.18   # Maximum torso/shoulder relative scaling shift between adjacent frames


def is_camera_stable(current: PoseFrame, previous: PoseFrame) -> bool:
    """Checks if camera is stable by verifying torso height and shoulder width scale continuity."""
    curr_l_sh = left_shoulder(current)
    curr_r_sh = right_shoulder(current)
    prev_l_sh = left_shoulder(previous)
    prev_r_sh = right_shoulder(previous)

    curr_shoulder_w = abs(curr_l_sh.x - curr_r_sh.x)
    prev_shoulder_w = abs(prev_l_sh.x - prev_r_sh.x)

    curr_l_hip = left_hip(current)
    curr_r_hip = right_hip(current)
    prev_l_hip = left_hip(previous)
    prev_r_hip = right_hip(previous)

    curr_torso_h = abs(((curr_l_hip.y + curr_r_hip.y) / 2.0) - ((curr_l_sh.y + curr_r_sh.y) / 2.0))
    prev_torso_h = abs(((prev_l_hip.y + prev_r_hip.y) / 2.0) - ((prev_l_sh.y + prev_r_sh.y) / 2.0))

    if (
        curr_shoulder_w <= MIN_BODY_MEASUREMENT
        or prev_shoulder_w <= MIN_BODY_MEASUREMENT
        or curr_torso_h <= MIN_BODY_MEASUREMENT
        or prev_torso_h <= MIN_BODY_MEASUREMENT
    ):
        return True

    shoulder_shift = abs(curr_shoulder_w - prev_shoulder_w) / max(prev_shoulder_w, MIN_BODY_MEASUREMENT)
    torso_shift = abs(curr_torso_h - prev_torso_h) / max(prev_torso_h, MIN_BODY_MEASUREMENT)

    return shoulder_shift <= MAX_BODY_SCALE_SHIFT and torso_shift <= MAX_BODY_SCALE_SHIFT


def assess_frame(current: PoseFrame, previous: Optional[PoseFrame] = None, fps: float = 30.0) -> FrameQuality:
    """Assesses individual frame landmark quality, visibility, and camera stability."""
    major_landmarks = [
        left_hip(current), right_hip(current),
        left_knee(current), right_knee(current),
        left_ankle(current), right_ankle(current),
        left_heel(current), right_heel(current),
        left_foot_index(current), right_foot_index(current)
    ]
    feet_landmarks = [
        left_heel(current), right_heel(current),
        left_foot_index(current), right_foot_index(current)
    ]
    full_body_landmarks = [
        left_shoulder(current), right_shoulder(current),
        left_ankle(current), right_ankle(current)
    ]

    all_major_landmarks_visible = all(lm.visibility > 0.4 for lm in major_landmarks)
    both_feet_visible = all(lm.visibility > 0.5 for lm in feet_landmarks)
    full_body_in_frame = all(lm.visibility > 0.3 for lm in full_body_landmarks)
    camera_stable = is_camera_stable(current, previous) if previous is not None else True

    visibilities = [lm.visibility for lm in current.landmarks] if current.landmarks else []
    landmark_confidence_mean = float(sum(visibilities) / len(visibilities)) if visibilities else 0.0

    if not both_feet_visible or landmark_confidence_mean < 0.4:
        status = FrameStatus.REJECTED
    elif all_major_landmarks_visible and full_body_in_frame and camera_stable and landmark_confidence_mean > 0.6:
        status = FrameStatus.GOOD
    elif both_feet_visible and landmark_confidence_mean > 0.4:
        status = FrameStatus.PARTIAL
    else:
        status = FrameStatus.REJECTED

    return FrameQuality(
        frame_index=current.frame_index,
        all_major_landmarks_visible=all_major_landmarks_visible,
        both_feet_visible=both_feet_visible,
        full_body_in_frame=full_body_in_frame,
        camera_stable=camera_stable,
        landmark_confidence_mean=landmark_confidence_mean,
        status=status
    )
