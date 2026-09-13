"""
MediaPipe BlazePose estimator and temporal kinematics smoothing for Badminton video analysis.
Reuses the generic 33-landmark BlazePose pipeline while providing badminton-specific
landmark indexing, confidence tracking, and Savitzky-Golay trajectory smoothing.
"""
import os
import math
from pathlib import Path
from typing import List, Optional, Tuple
import numpy as np
import cv2

try:
    import mediapipe as mp
    from mediapipe.tasks.python import vision, BaseOptions
    HAS_MEDIAPIPE = True
except ImportError:
    HAS_MEDIAPIPE = False

from .schemas import Landmark, PoseFrame
from app.gait.events.smoothing import interpolate_nans, savgol_smooth

# Standard MediaPipe 33-Landmark Indices (Section 7 Master Spec)
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

# Key Landmark Accessors
def left_wrist(frame: PoseFrame) -> Landmark: return frame.landmarks[LEFT_WRIST]
def right_wrist(frame: PoseFrame) -> Landmark: return frame.landmarks[RIGHT_WRIST]
def left_elbow(frame: PoseFrame) -> Landmark: return frame.landmarks[LEFT_ELBOW]
def right_elbow(frame: PoseFrame) -> Landmark: return frame.landmarks[RIGHT_ELBOW]
def left_shoulder(frame: PoseFrame) -> Landmark: return frame.landmarks[LEFT_SHOULDER]
def right_shoulder(frame: PoseFrame) -> Landmark: return frame.landmarks[RIGHT_SHOULDER]
def left_hip(frame: PoseFrame) -> Landmark: return frame.landmarks[LEFT_HIP]
def right_hip(frame: PoseFrame) -> Landmark: return frame.landmarks[RIGHT_HIP]
def left_knee(frame: PoseFrame) -> Landmark: return frame.landmarks[LEFT_KNEE]
def right_knee(frame: PoseFrame) -> Landmark: return frame.landmarks[RIGHT_KNEE]
def left_ankle(frame: PoseFrame) -> Landmark: return frame.landmarks[LEFT_ANKLE]
def right_ankle(frame: PoseFrame) -> Landmark: return frame.landmarks[RIGHT_ANKLE]


from app.plugins.sports_plugin import SportsPlugin


def compute_joint_angle_2d(p1: Landmark, p2: Landmark, p3: Landmark) -> Optional[float]:
    """
    Computes angle in degrees at vertex p2 formed by (p1 - p2) and (p3 - p2).
    Reuses SportsPlugin.calculate_joint_angle_2d to prevent duplication of geometric math.
    """
    if p1.visibility < 0.20 or p2.visibility < 0.20 or p3.visibility < 0.20:
        return None
    return round(float(SportsPlugin.calculate_joint_angle_2d((p1.x, p1.y), (p2.x, p2.y), (p3.x, p3.y))), 1)


class BadmintonPoseEstimator:
    """Extracts 33 BlazePose landmarks from badminton video frames."""

    def __init__(self, model_path: Optional[str] = None):
        if not HAS_MEDIAPIPE:
            raise ImportError("MediaPipe is not installed. Install mediapipe to run pose estimation.")

        if not model_path:
            current_dir = Path(__file__).resolve().parent
            candidates = [
                current_dir.parent.parent / "gait" / "models" / "pose_landmarker_full.task",
                current_dir.parent.parent.parent / "app" / "gait" / "models" / "pose_landmarker_full.task",
                current_dir / "models" / "pose_landmarker_full.task"
            ]
            for c in candidates:
                if c.exists():
                    model_path = str(c.resolve())
                    break

            if not model_path or not os.path.exists(model_path):
                # Fallback to downloading
                default_dir = current_dir.parent.parent / "gait" / "models"
                default_dir.mkdir(parents=True, exist_ok=True)
                target = default_dir / "pose_landmarker_full.task"
                try:
                    import urllib.request
                    model_url = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task"
                    urllib.request.urlretrieve(model_url, str(target))
                    if target.exists():
                        model_path = str(target.resolve())
                except Exception as dl_err:
                    raise FileNotFoundError(
                        f"MediaPipe pose landmarker model not found and download failed: {dl_err}"
                    )

        if not model_path or not os.path.exists(model_path):
            raise FileNotFoundError(f"MediaPipe pose landmarker model not found at {model_path}")

        self.model_path = str(os.path.abspath(model_path))
        options = vision.PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=self.model_path),
            running_mode=vision.RunningMode.IMAGE,
            min_pose_detection_confidence=0.35,
            min_pose_presence_confidence=0.35,
            min_tracking_confidence=0.35,
        )
        self._landmarker = vision.PoseLandmarker.create_from_options(options)

    def process_frame(
        self,
        frame_rgb_or_bgr: np.ndarray,
        frame_index: int,
        timestamp_ms: int,
        is_bgr: bool = True
    ) -> PoseFrame:
        """Processes a single video frame and returns a PoseFrame with 33 landmarks."""
        h, w = frame_rgb_or_bgr.shape[:2]
        if is_bgr:
            frame_rgb = cv2.cvtColor(frame_rgb_or_bgr, cv2.COLOR_BGR2RGB)
        else:
            frame_rgb = frame_rgb_or_bgr

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        result = self._landmarker.detect(mp_image)

        if result.pose_landmarks and len(result.pose_landmarks) > 0:
            raw_landmarks = result.pose_landmarks[0]
            landmarks: List[Landmark] = []
            vis_sum = 0.0
            for lm in raw_landmarks:
                vis = getattr(lm, "visibility", 1.0)
                if vis is None or vis < 0:
                    vis = getattr(lm, "presence", 1.0) or 0.0
                vis_float = float(vis)
                vis_sum += vis_float
                landmarks.append(Landmark(
                    x=float(lm.x),
                    y=float(lm.y),
                    z=float(getattr(lm, "z", 0.0) or 0.0),
                    visibility=vis_float
                ))
            mean_conf = vis_sum / max(1, len(landmarks))
            return PoseFrame(
                frame_index=frame_index,
                timestamp_ms=timestamp_ms,
                landmarks=landmarks,
                source_width=w,
                source_height=h,
                is_detected=True,
                detection_reason=None,
                mean_confidence=float(round(mean_conf, 3))
            )
        else:
            empty_landmarks = [Landmark(x=0.0, y=0.0, z=0.0, visibility=0.0) for _ in range(33)]
            return PoseFrame(
                frame_index=frame_index,
                timestamp_ms=timestamp_ms,
                landmarks=empty_landmarks,
                source_width=w,
                source_height=h,
                is_detected=False,
                detection_reason="No human pose detected by MediaPipe BlazePose in frame",
                mean_confidence=0.0
            )

    def close(self):
        if hasattr(self, "_landmarker") and self._landmarker:
            self._landmarker.close()


def smooth_pose_frames(frames: List[PoseFrame], fps: float = 30.0) -> List[PoseFrame]:
    """
    Applies zero-phase-lag Savitzky-Golay temporal smoothing to all landmark trajectories.
    Reuses the robust interpolate_nans and savgol_smooth utilities from gait.
    """
    if not frames or len(frames) < 5:
        return frames

    n_frames = len(frames)
    num_landmarks = 33

    # Extract coordinates per landmark across time
    # Shape: (33, n_frames) for x, y, z
    coords_x = np.full((num_landmarks, n_frames), np.nan, dtype=np.float64)
    coords_y = np.full((num_landmarks, n_frames), np.nan, dtype=np.float64)
    coords_z = np.full((num_landmarks, n_frames), np.nan, dtype=np.float64)
    visibilities = np.zeros((num_landmarks, n_frames), dtype=np.float64)

    for f_idx, pf in enumerate(frames):
        if pf.is_detected and len(pf.landmarks) == num_landmarks:
            for lm_idx, lm in enumerate(pf.landmarks):
                visibilities[lm_idx, f_idx] = lm.visibility
                if lm.visibility >= 0.15:
                    coords_x[lm_idx, f_idx] = lm.x
                    coords_y[lm_idx, f_idx] = lm.y
                    coords_z[lm_idx, f_idx] = lm.z

    # Smooth each landmark trajectory independently
    smoothed_x = np.copy(coords_x)
    smoothed_y = np.copy(coords_y)
    smoothed_z = np.copy(coords_z)

    for lm_idx in range(num_landmarks):
        # x smoothing
        sig_x = coords_x[lm_idx].tolist()
        interp_x = interpolate_nans(sig_x, max_gap=10)
        sm_x = savgol_smooth(interp_x, fps=fps)
        smoothed_x[lm_idx] = np.array(sm_x)

        # y smoothing
        sig_y = coords_y[lm_idx].tolist()
        interp_y = interpolate_nans(sig_y, max_gap=10)
        sm_y = savgol_smooth(interp_y, fps=fps)
        smoothed_y[lm_idx] = np.array(sm_y)

        # z smoothing
        sig_z = coords_z[lm_idx].tolist()
        interp_z = interpolate_nans(sig_z, max_gap=10)
        sm_z = savgol_smooth(interp_z, fps=fps)
        smoothed_z[lm_idx] = np.array(sm_z)

    # Reassemble smoothed PoseFrames
    result: List[PoseFrame] = []
    for f_idx, pf in enumerate(frames):
        if not pf.is_detected:
            result.append(pf)
            continue

        new_landmarks: List[Landmark] = []
        for lm_idx in range(num_landmarks):
            sx = smoothed_x[lm_idx, f_idx]
            sy = smoothed_y[lm_idx, f_idx]
            sz = smoothed_z[lm_idx, f_idx]
            # If smoothing produced NaN (e.g. at edges of undetected segments), fallback to original
            final_x = float(sx) if not np.isnan(sx) else pf.landmarks[lm_idx].x
            final_y = float(sy) if not np.isnan(sy) else pf.landmarks[lm_idx].y
            final_z = float(sz) if not np.isnan(sz) else pf.landmarks[lm_idx].z

            new_landmarks.append(Landmark(
                x=final_x,
                y=final_y,
                z=final_z,
                visibility=float(visibilities[lm_idx, f_idx])
            ))

        result.append(PoseFrame(
            frame_index=pf.frame_index,
            timestamp_ms=pf.timestamp_ms,
            landmarks=new_landmarks,
            source_width=pf.source_width,
            source_height=pf.source_height,
            is_detected=pf.is_detected,
            detection_reason=pf.detection_reason,
            mean_confidence=pf.mean_confidence
        ))

    return result
