"""
MediaPipe Pose Estimator implementation for video frames.
"""
import os
import cv2
import numpy as np
from pathlib import Path
from typing import List, Optional
import mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions

from ..schemas import Landmark, PoseFrame


class PoseEstimator:
    """Extracts 33 BlazePose landmarks from video frames."""

    def __init__(self, model_path: Optional[str] = None):
        if not model_path:
            # Look for model in standard locations or auto-download
            current_dir = Path(__file__).resolve().parent
            default_model_dir = current_dir.parent / "models"
            default_model_path = default_model_dir / "pose_landmarker_full.task"
            
            candidates = [
                default_model_path,
                current_dir / "models" / "pose_landmarker_full.task",
                current_dir.parent.parent.parent / "models" / "pose_landmarker_full.task"
            ]
            for c in candidates:
                if c.exists():
                    model_path = str(c.resolve())
                    break

            if not model_path or not os.path.exists(model_path):
                # Auto-download model from official Google MediaPipe repository
                try:
                    import urllib.request
                    default_model_dir.mkdir(parents=True, exist_ok=True)
                    model_url = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task"
                    urllib.request.urlretrieve(model_url, str(default_model_path))
                    if default_model_path.exists():
                        model_path = str(default_model_path.resolve())
                except Exception as dl_err:
                    raise FileNotFoundError(
                        f"MediaPipe pose landmarker model not found and auto-download failed: {dl_err}. "
                        f"Please ensure network access or place 'pose_landmarker_full.task' in {default_model_dir}."
                    )

        if not model_path or not os.path.exists(model_path):
            raise FileNotFoundError(f"MediaPipe pose landmarker model not found at {model_path}")

        self.model_path = str(os.path.abspath(model_path))
        options = vision.PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=self.model_path),
            running_mode=vision.RunningMode.IMAGE,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self._landmarker = vision.PoseLandmarker.create_from_options(options)

    def process_frame(self, frame_rgb: np.ndarray, frame_index: int, timestamp_ms: int) -> PoseFrame:
        """Process a single RGB numpy image and return a PoseFrame."""
        h, w = frame_rgb.shape[:2]
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        result = self._landmarker.detect(mp_image)

        landmarks: List[Landmark] = []
        if result.pose_landmarks and len(result.pose_landmarks) > 0:
            raw_landmarks = result.pose_landmarks[0]
            for lm in raw_landmarks:
                vis = getattr(lm, "visibility", 1.0)
                if vis is None or vis < 0:
                    vis = getattr(lm, "presence", 1.0) or 0.0
                landmarks.append(Landmark(
                    x=float(lm.x),
                    y=float(lm.y),
                    z=float(getattr(lm, "z", 0.0) or 0.0),
                    visibility=float(vis)
                ))
        else:
            # 33 placeholder empty landmarks
            landmarks = [Landmark(x=0.0, y=0.0, z=0.0, visibility=0.0) for _ in range(33)]

        return PoseFrame(
            frame_index=frame_index,
            timestamp_ms=timestamp_ms,
            landmarks=landmarks,
            source_width=w,
            source_height=h
        )

    def close(self):
        if hasattr(self, "_landmarker") and self._landmarker:
            self._landmarker.close()
