"""
Video processing and frame extraction utility.
"""
import os
import cv2
import tempfile
from typing import List, Tuple, Optional
from .schemas import PoseFrame, VideoMetadata
from .pose.estimator import PoseEstimator


class VideoProcessor:
    """Handles video file inspection, sequential frame extraction, and pose estimation."""

    def __init__(self, estimator: Optional[PoseEstimator] = None):
        self._estimator = estimator or PoseEstimator()

    def process_video_file(
        self,
        video_path: str,
        filename: str = "video.mp4",
        max_duration_seconds: float = 60.0,
        sample_step: int = 1
    ) -> Tuple[VideoMetadata, List[PoseFrame]]:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {filename}")

        try:
            fps = float(cap.get(cv2.CAP_PROP_FPS))
            if fps <= 0.0 or fps > 240.0:
                fps = 30.0

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration_seconds = float(total_frames / fps) if total_frames > 0 else 0.0

            pose_frames: List[PoseFrame] = []
            frame_idx = 0
            processed_count = 0

            while True:
                ret, frame_bgr = cap.read()
                if not ret:
                    break

                # Respect sample step if specified
                if frame_idx % sample_step == 0:
                    timestamp_ms = int((frame_idx / fps) * 1000.0)
                    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                    pose_frame = self._estimator.process_frame(
                        frame_rgb=frame_rgb,
                        frame_index=frame_idx,
                        timestamp_ms=timestamp_ms
                    )
                    pose_frames.append(pose_frame)
                    processed_count += 1

                frame_idx += 1
                if duration_seconds > 0 and (frame_idx / fps) > max_duration_seconds:
                    break

            metadata = VideoMetadata(
                filename=filename,
                duration_seconds=round(duration_seconds, 2),
                fps=round(fps, 2),
                total_frames=frame_idx,
                frames_processed=processed_count,
                width=width,
                height=height
            )

            return metadata, pose_frames
        finally:
            cap.release()

    def process_video_bytes(
        self,
        video_bytes: bytes,
        filename: str = "upload.mp4"
    ) -> Tuple[VideoMetadata, List[PoseFrame]]:
        """Saves video bytes to a temporary file, processes it, and cleans up afterwards."""
        suffix = os.path.splitext(filename)[1] or ".mp4"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(video_bytes)

        try:
            return self.process_video_file(tmp_path, filename=filename)
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
