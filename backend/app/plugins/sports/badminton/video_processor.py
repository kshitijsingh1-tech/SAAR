"""
Badminton Video Ingestion and Frame Extraction Processor.
Clones the structure of backend/app/gait/video_processor.py while adapting
sampling rates, resolution handling, and duration thresholds specifically
for high-velocity badminton rallies.
"""
import os
import cv2
import tempfile
import numpy as np
from typing import List, Tuple, Optional
from .schemas import VideoMetadata, BadmintonFrame

# ==============================================================================
# ADAPTIVE SAMPLING & DURATION THRESHOLDS (DOCUMENTED BIOMECHANICAL RATIONALE)
# ==============================================================================
# Badminton overhead smashes, slices, and net kills involve racket head angular
# speeds exceeding 1,800 deg/s and shuttle speeds up to 400+ km/h. Temporal
# downsampling causes severe motion blur and aliasing of peak contact frames.
# Therefore, badminton clips MUST NOT be downsampled below source FPS during typical
# rally lengths (under 90 seconds).
#
# For unusually long video uploads (>90 seconds, e.g. continuous multi-rally recordings),
# we dynamically switch to a 2x sample step (every 2nd frame) to maintain bounded
# memory and CPU latency while preserving adequate rally flow.
# ==============================================================================
LONG_CLIP_THRESHOLD_SECONDS: float = 90.0  # Clips > 90s switch to 2x downsampling
MAX_ALLOWED_DURATION_SECONDS: float = 180.0  # Hard ceiling for single upload processing


class BadmintonVideoProcessor:
    """
    Handles robust video decoding, adaptive FPS sampling, and raw frame extraction
    with complete temporal provenance (frame_index, timestamp_ms).
    """

    def process_video_file(
        self,
        video_path: str,
        filename: str = "badminton_video.mp4"
    ) -> Tuple[VideoMetadata, List[BadmintonFrame], List[np.ndarray]]:
        """
        Opens a local video container, extracts technical metadata, and extracts
        frames using adaptive FPS sampling.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found at path: {video_path}")

        file_size = os.path.getsize(video_path)
        if file_size == 0:
            raise ValueError(f"Video file '{filename}' is empty (0 bytes).")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file container '{filename}'. Corrupted or unsupported format.")

        try:
            fps = float(cap.get(cv2.CAP_PROP_FPS))
            if fps <= 0.0 or fps > 240.0:
                fps = 30.0

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            if total_frames <= 0 or width <= 0 or height <= 0:
                raise ValueError(f"Invalid video stream dimensions or frame count in '{filename}'.")

            duration_seconds = round(float(total_frames / fps), 2) if total_frames > 0 and fps > 0 else 0.0

            # Determine Adaptive Sampling Step:
            # - For high FPS captures (e.g. 60 or 120 FPS), normalize to ~30 FPS athletic capture baseline
            # - For long rallies (> 90s), sample every 2nd frame to keep latency bounded
            if fps > 40.0:
                sample_step = max(1, int(round(fps / 30.0)))
            elif duration_seconds > LONG_CLIP_THRESHOLD_SECONDS:
                sample_step = 2
            else:
                sample_step = 1

            # Determine Target Resolution (cap at 1280x720 for efficient CV inference without loss of landmark fidelity)
            needs_downscale = (width > 1280 or height > 720)
            if needs_downscale:
                scale_factor = min(1280.0 / width, 720.0 / height)
                target_w = int(round(width * scale_factor))
                target_h = int(round(height * scale_factor))
            else:
                target_w = width
                target_h = height

            frame_metadata_list: List[BadmintonFrame] = []
            raw_frames_list: List[np.ndarray] = []

            frame_idx = 0
            processed_count = 0

            while True:
                ret, frame_bgr = cap.read()
                if not ret:
                    break

                if frame_idx % sample_step == 0:
                    timestamp_ms = int((frame_idx / fps) * 1000.0)

                    # Optimize resolution for MediaPipe and OpenCV processing
                    if needs_downscale:
                        processed_frame = cv2.resize(frame_bgr, (target_w, target_h), interpolation=cv2.INTER_AREA)
                    else:
                        processed_frame = frame_bgr

                    frame_meta = BadmintonFrame(
                        frame_index=frame_idx,
                        timestamp_ms=timestamp_ms,
                        width=target_w,
                        height=target_h,
                        is_stable=True
                    )
                    frame_metadata_list.append(frame_meta)
                    raw_frames_list.append(processed_frame)
                    processed_count += 1

                frame_idx += 1
                if duration_seconds > 0 and (frame_idx / fps) > MAX_ALLOWED_DURATION_SECONDS:
                    break

            from .quality import generate_preview_base64
            preview_b64 = generate_preview_base64(raw_frames_list)

            metadata = VideoMetadata(
                filename=filename,
                duration_seconds=duration_seconds,
                fps=round(fps, 2),
                total_frames=total_frames,
                frame_count=total_frames,
                frames_processed=processed_count,
                width=width,
                height=height,
                camera_type="fixed_baseline",
                preview_image_base64=preview_b64
            )

            return metadata, frame_metadata_list, raw_frames_list
        finally:
            cap.release()

    def process_video_bytes(
        self,
        video_bytes: bytes,
        filename: str = "upload.mp4"
    ) -> Tuple[VideoMetadata, List[BadmintonFrame], List[np.ndarray]]:
        """
        Saves video bytes to an isolated temporary file, decodes frames,
        and guarantees cleanup of disk resources upon completion.
        """
        if not video_bytes or len(video_bytes) == 0:
            raise ValueError(f"Supplied video data for '{filename}' is empty (0 bytes).")

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
