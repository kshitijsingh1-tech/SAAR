"""
End-to-end Gait Analysis Pipeline orchestrator.
"""
import uuid
from typing import Optional, List
from .schemas import (
    CanonicalGaitResult, VideoMetadata, CaptureAssessment,
    CaptureConfidence, FrameQuality, TemporalMetrics
)
from .pose.estimator import PoseEstimator
from .video_processor import VideoProcessor
from .quality.frame_quality import assess_frame
from .quality.recording_quality import assess_recording
from .events.heel_strike import detect_gait_events
from .metrics.metric_computer import MetricComputer
from .norms.toddler_norms import get_cadence_range, get_walking_milestone_context
from .observations.observation_engine import ObservationEngine


class GaitAnalysisPipeline:
    """Deterministic ToddleAI gait analysis pipeline."""

    def __init__(self, estimator: Optional[PoseEstimator] = None):
        self.estimator = estimator or PoseEstimator()
        self.video_processor = VideoProcessor(estimator=self.estimator)
        self.metric_computer = MetricComputer()
        self.observation_engine = ObservationEngine()

    def analyze_video_bytes(
        self,
        video_bytes: bytes,
        filename: str = "upload.mp4",
        child_age_months: int = 24,
        assessment_id: Optional[str] = None
    ) -> CanonicalGaitResult:
        """Processes uploaded video bytes and computes the canonical gait analysis result."""
        assessment_id = assessment_id or f"gait_{uuid.uuid4().hex[:8]}"

        metadata, pose_frames = self.video_processor.process_video_bytes(
            video_bytes=video_bytes,
            filename=filename
        )

        return self._run_analysis(
            metadata=metadata,
            pose_frames=pose_frames,
            child_age_months=child_age_months,
            assessment_id=assessment_id
        )

    def analyze_video_file(
        self,
        video_path: str,
        filename: str = "video.mp4",
        child_age_months: int = 24,
        assessment_id: Optional[str] = None
    ) -> CanonicalGaitResult:
        """Processes a local video file and computes the canonical gait analysis result."""
        assessment_id = assessment_id or f"gait_{uuid.uuid4().hex[:8]}"

        metadata, pose_frames = self.video_processor.process_video_file(
            video_path=video_path,
            filename=filename
        )

        return self._run_analysis(
            metadata=metadata,
            pose_frames=pose_frames,
            child_age_months=child_age_months,
            assessment_id=assessment_id
        )

    def _run_analysis(
        self,
        metadata: VideoMetadata,
        pose_frames: list,
        child_age_months: int,
        assessment_id: str
    ) -> CanonicalGaitResult:
        cadence_range = get_cadence_range(child_age_months)
        milestone_context = get_walking_milestone_context(child_age_months)

        if not pose_frames:
            rejection_issues = ["No frames could be extracted from the video."]
            quality = CaptureAssessment(
                confidence=CaptureConfidence.REJECT,
                issues=rejection_issues,
                best_segment_start=0,
                best_segment_end=0,
                usable_step_count=0,
                good_frame_ratio=0.0
            )
            return CanonicalGaitResult(
                assessment_id=assessment_id,
                status="rejected",
                child_age_months=child_age_months,
                video=metadata,
                quality=quality,
                metrics=self.metric_computer.no_data(),
                cadence_range=cadence_range,
                milestone_context=milestone_context,
                observations=[],
                rejection_reason="No pose frames detected in video.",
                recommendations=["Please upload a clear walking video showing the full toddler body from the side."]
            )

        # 1. Evaluate Frame Qualities
        frame_qualities: List[FrameQuality] = []
        for i, frame in enumerate(pose_frames):
            prev_frame = pose_frames[i - 1] if i > 0 else None
            fq = assess_frame(frame, prev_frame, fps=metadata.fps)
            frame_qualities.append(fq)

        # 2. Compute good_frame_ratio early (needed by MetricComputer for pipeline_confidence)
        good_frames = [fq for fq in frame_qualities if fq.status.value == "GOOD"]
        good_frame_ratio = len(good_frames) / len(frame_qualities) if frame_qualities else 0.0

        # 3. Detect Temporal Heel-Strike Events
        events = detect_gait_events(pose_frames, fps=metadata.fps)

        # 4. Calculate Deterministic Gait Metrics (with confidence weighting + outlier rejection)
        metrics = self.metric_computer.compute_metrics(events, good_frame_ratio=good_frame_ratio)

        # 5. Whole-Recording Quality Gate
        quality = assess_recording(frame_qualities, detected_steps=metrics.usable_step_count)

        # 6. Generate Structured Observation Cards
        observations = self.observation_engine.generate_observations(
            metrics=metrics,
            child_age_months=child_age_months,
            capture_confidence=quality.confidence
        )

        is_rejected = (quality.confidence == CaptureConfidence.REJECT) or (metrics.usable_step_count < 2)
        status_str = "rejected" if is_rejected else "success"
        rejection_reason = "Insufficient gait-quality data or step count." if is_rejected else None

        recommendations = list(quality.issues)
        if is_rejected and not recommendations:
            recommendations.append("Record a clear 10-15 second side-view walking clip at knee height with visible feet.")

        return CanonicalGaitResult(
            assessment_id=assessment_id,
            status=status_str,
            child_age_months=child_age_months,
            video=metadata,
            quality=quality,
            metrics=metrics,
            cadence_range=cadence_range,
            milestone_context=milestone_context,
            observations=observations,
            rejection_reason=rejection_reason,
            recommendations=recommendations,
            pipeline_confidence=metrics.pipeline_confidence
        )

