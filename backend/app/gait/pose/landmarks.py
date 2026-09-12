"""
MediaPipe 33-landmark indices and landmark extraction helpers matching ToddleAI.
"""
from typing import Optional
from ..schemas import Landmark, PoseFrame, Side


class MediaPipeLandmarks:
    NOSE = 0
    LEFT_EYE_INNER = 1
    LEFT_EYE = 2
    LEFT_EYE_OUTER = 3
    RIGHT_EYE_INNER = 4
    RIGHT_EYE = 5
    RIGHT_EYE_OUTER = 6
    LEFT_EAR = 7
    RIGHT_EAR = 8
    MOUTH_LEFT = 9
    MOUTH_RIGHT = 10
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_ELBOW = 13
    RIGHT_ELBOW = 14
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_PINKY = 17
    RIGHT_PINKY = 18
    LEFT_INDEX = 19
    RIGHT_INDEX = 20
    LEFT_THUMB = 21
    RIGHT_THUMB = 22
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28
    LEFT_HEEL = 29
    RIGHT_HEEL = 30
    LEFT_FOOT_INDEX = 31
    RIGHT_FOOT_INDEX = 32


def _get_lm(frame: PoseFrame, idx: int) -> Landmark:
    if 0 <= idx < len(frame.landmarks):
        return frame.landmarks[idx]
    return Landmark(x=0.0, y=0.0, z=0.0, visibility=0.0)


def left_shoulder(frame: PoseFrame) -> Landmark:
    return _get_lm(frame, MediaPipeLandmarks.LEFT_SHOULDER)


def right_shoulder(frame: PoseFrame) -> Landmark:
    return _get_lm(frame, MediaPipeLandmarks.RIGHT_SHOULDER)


def left_hip(frame: PoseFrame) -> Landmark:
    return _get_lm(frame, MediaPipeLandmarks.LEFT_HIP)


def right_hip(frame: PoseFrame) -> Landmark:
    return _get_lm(frame, MediaPipeLandmarks.RIGHT_HIP)


def left_knee(frame: PoseFrame) -> Landmark:
    return _get_lm(frame, MediaPipeLandmarks.LEFT_KNEE)


def right_knee(frame: PoseFrame) -> Landmark:
    return _get_lm(frame, MediaPipeLandmarks.RIGHT_KNEE)


def left_ankle(frame: PoseFrame) -> Landmark:
    return _get_lm(frame, MediaPipeLandmarks.LEFT_ANKLE)


def right_ankle(frame: PoseFrame) -> Landmark:
    return _get_lm(frame, MediaPipeLandmarks.RIGHT_ANKLE)


def left_heel(frame: PoseFrame) -> Landmark:
    return _get_lm(frame, MediaPipeLandmarks.LEFT_HEEL)


def right_heel(frame: PoseFrame) -> Landmark:
    return _get_lm(frame, MediaPipeLandmarks.RIGHT_HEEL)


def left_foot_index(frame: PoseFrame) -> Landmark:
    return _get_lm(frame, MediaPipeLandmarks.LEFT_FOOT_INDEX)


def right_foot_index(frame: PoseFrame) -> Landmark:
    return _get_lm(frame, MediaPipeLandmarks.RIGHT_FOOT_INDEX)


def heel_for_side(frame: PoseFrame, side: Side) -> Landmark:
    return left_heel(frame) if side == Side.LEFT else right_heel(frame)
