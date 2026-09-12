"""
End-to-end Gait Analysis Pipeline orchestrator with Section 12 structured kinematics.

Preserves the original ToddleAI temporal gait detection pipeline as source of truth,
and layers deterministic 2D joint angle kinematics, cycle-aware ROM, trunk posture,
spatial calibration gating, and age-referenced norms.
"""
import uuid
from typing import Optional, List, Dict, Any
from .schemas import (
    CanonicalGaitResult, VideoMetadata, CaptureAssessment,
    CaptureConfidence, FrameQuality, TemporalMetrics,
    JointROMModel, JointMotionProfile, PostureMetrics,
    SpatialMetrics, SymmetryProfile, AdvancedTemporalMetrics,
    ReferenceMetricItem, GaitProfile, CycleROMItem, Side
)
from .pose.estimator import PoseEstimator
from .video_processor import VideoProcessor
from .quality.frame_quality import assess_frame
from .quality.recording_quality import assess_recording
from .events.heel_strike import detect_gait_events
from .metrics.metric_computer import MetricComputer
from .norms.toddler_norms import get_cadence_range, get_walking_milestone_context
from .norms.advanced_norms import generate_reference_comparisons
from .observations.observation_engine import ObservationEngine
from .observations.developmental_synthesizer import DevelopmentalSynthesizer

from .angles.joint_angles import (
    extract_joint_angles, compute_cycle_aware_rom,
    compute_bilateral_asymmetry
)
from .posture.trunk_posture import analyze_trunk_posture
from .spatial.spatial_metrics import compute_spatial_metrics
from .temporal.advanced_temporal import compute_advanced_temporal_metrics


class GaitAnalysisPipeline:
    """Deterministic ToddleAI gait analysis pipeline with 2D lower-body kinematics."""

    def __init__(self, estimator: Optional[PoseEstimator] = None):
        self.estimator = estimator or PoseEstimator()
        self.video_processor = VideoProcessor(estimator=self.estimator)
        self.metric_computer = MetricComputer()
        self.observation_engine = ObservationEngine()
        self.developmental_synthesizer = DevelopmentalSynthesizer()


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

        # ------------------------------------------------------------------
        # 1. Evaluate Frame Qualities
        # ------------------------------------------------------------------
        frame_qualities: List[FrameQuality] = []
        for i, frame in enumerate(pose_frames):
            prev_frame = pose_frames[i - 1] if i > 0 else None
            fq = assess_frame(frame, prev_frame, fps=metadata.fps)
            frame_qualities.append(fq)

        # ------------------------------------------------------------------
        # 2. Compute good_frame_ratio
        # ------------------------------------------------------------------
        good_frames = [fq for fq in frame_qualities if fq.status.value == "GOOD"]
        good_frame_ratio = len(good_frames) / len(frame_qualities) if frame_qualities else 0.0

        # ------------------------------------------------------------------
        # 3. Detect Temporal Heel-Strike Events (Source of Truth)
        # ------------------------------------------------------------------
        events = detect_gait_events(pose_frames, fps=metadata.fps)

        # ------------------------------------------------------------------
        # 4. Calculate Deterministic Base Gait Metrics (Source of Truth)
        # ------------------------------------------------------------------
        metrics = self.metric_computer.compute_metrics(events, good_frame_ratio=good_frame_ratio)

        # ------------------------------------------------------------------
        # 5. Whole-Recording Quality Gate
        # ------------------------------------------------------------------
        quality = assess_recording(frame_qualities, detected_steps=metrics.usable_step_count)

        # ------------------------------------------------------------------
        # 6. Advanced 2D Joint Angle Kinematics & Cycle-Aware ROM
        # ------------------------------------------------------------------
        joint_series = extract_joint_angles(pose_frames, fps=metadata.fps)

        l_hip_rom = compute_cycle_aware_rom(joint_series["left_hip"], events, Side.LEFT)
        r_hip_rom = compute_cycle_aware_rom(joint_series["right_hip"], events, Side.RIGHT)

        l_knee_rom = compute_cycle_aware_rom(joint_series["left_knee"], events, Side.LEFT)
        r_knee_rom = compute_cycle_aware_rom(joint_series["right_knee"], events, Side.RIGHT)

        l_ankle_rom = compute_cycle_aware_rom(joint_series["left_ankle"], events, Side.LEFT)
        r_ankle_rom = compute_cycle_aware_rom(joint_series["right_ankle"], events, Side.RIGHT)

        def _to_rom_model(rom_obj) -> JointROMModel:
            return JointROMModel(
                joint_name=rom_obj.joint_name,
                min_angle_deg=rom_obj.min_angle_deg,
                max_angle_deg=rom_obj.max_angle_deg,
                rom_deg=rom_obj.rom_deg,
                cycle_roms=[
                    CycleROMItem(
                        cycle_index=c.cycle_index,
                        start_time=c.start_time,
                        end_time=c.end_time,
                        min_angle_deg=c.min_angle_deg,
                        max_angle_deg=c.max_angle_deg,
                        rom_deg=c.rom_deg,
                        valid_samples=c.valid_samples
                    ) for c in rom_obj.cycle_roms
                ],
                valid_cycles=rom_obj.valid_cycles,
                valid_frames=rom_obj.valid_frames,
                confidence=rom_obj.confidence
            )

        joint_motion = JointMotionProfile(
            left_hip=_to_rom_model(l_hip_rom),
            right_hip=_to_rom_model(r_hip_rom),
            left_knee=_to_rom_model(l_knee_rom),
            right_knee=_to_rom_model(r_knee_rom),
            left_ankle=_to_rom_model(l_ankle_rom),
            right_ankle=_to_rom_model(r_ankle_rom),
        )

        # Bilateral Asymmetry Percentages
        hip_asym = compute_bilateral_asymmetry(l_hip_rom.rom_deg, r_hip_rom.rom_deg)
        knee_asym = compute_bilateral_asymmetry(l_knee_rom.rom_deg, r_knee_rom.rom_deg)
        ankle_asym = compute_bilateral_asymmetry(l_ankle_rom.rom_deg, r_ankle_rom.rom_deg)

        # ------------------------------------------------------------------
        # 7. Trunk & Posture Kinematics
        # ------------------------------------------------------------------
        posture_res = analyze_trunk_posture(pose_frames, fps=metadata.fps)
        posture_metrics = PostureMetrics(
            trunk_angle_deg=posture_res.mean_trunk_angle_deg,
            trunk_variability_deg=posture_res.trunk_variability_deg,
            lateral_sway=posture_res.lateral_sway_norm,
            confidence=posture_res.confidence
        )

        # ------------------------------------------------------------------
        # 8. Spatial Metrics & Calibration Gating
        # ------------------------------------------------------------------
        spatial_res = compute_spatial_metrics(
            pose_frames,
            events
        )
        spatial_metrics = SpatialMetrics(
            is_calibrated=spatial_res.is_calibrated,
            calibration_source=spatial_res.calibration_source,
            uncalibrated_reason=spatial_res.uncalibrated_reason,
            step_length_m=spatial_res.step_length_m,
            stride_length_m=spatial_res.stride_length_m,
            walking_speed_m_per_s=spatial_res.walking_speed_m_per_s,
            distance_m=spatial_res.distance_m,
            foot_progression_angle_deg=spatial_res.foot_progression.mean_progression_angle_deg,
            left_foot_progression_deg=spatial_res.foot_progression.left_progression_angle_deg,
            right_foot_progression_deg=spatial_res.foot_progression.right_progression_angle_deg,
            walking_direction=spatial_res.foot_progression.walking_direction
        )

        # ------------------------------------------------------------------
        # 9. Advanced Temporal Metrics (Stance, Swing, Double Support)
        # ------------------------------------------------------------------
        adv_temp_res = compute_advanced_temporal_metrics(events, metrics)
        adv_temporal = AdvancedTemporalMetrics(
            step_count=adv_temp_res.step_count,
            cadence_steps_per_min=adv_temp_res.cadence_steps_per_min,
            mean_step_time_sec=adv_temp_res.mean_step_time_sec,
            median_step_time_sec=adv_temp_res.median_step_time_sec,
            step_time_variability_pct=adv_temp_res.step_time_variability_pct,
            mean_stride_time_sec=adv_temp_res.mean_stride_time_sec,
            stance_time=adv_temp_res.estimated_stance_time_sec,
            swing_time=adv_temp_res.estimated_swing_time_sec,
            double_support_time=adv_temp_res.estimated_double_support_sec,
            stance_phase_pct=adv_temp_res.stance_phase_pct,
            swing_phase_pct=adv_temp_res.swing_phase_pct,
            double_support_pct=adv_temp_res.double_support_pct
        )

        # Symmetry Profile (Kinematic & Timing Balance)
        symmetry_profile = SymmetryProfile(
            step_time_asymmetry_pct=metrics.step_time_asymmetry_pct,
            step_length_asymmetry_pct=None,
            hip_rom_asymmetry_pct=hip_asym,
            knee_rom_asymmetry_pct=knee_asym,
            ankle_rom_asymmetry_pct=ankle_asym
        )

        # ------------------------------------------------------------------
        # 10. Age-Referenced Normative Comparisons
        # ------------------------------------------------------------------
        def _median_or_none(v1, v2):
            vals = [v for v in [v1, v2] if v is not None]
            return round(sum(vals) / len(vals), 1) if vals else None

        reference_comparisons = generate_reference_comparisons(
            child_age_months=child_age_months,
            cadence=metrics.cadence,
            mean_step_time=metrics.mean_step_time,
            step_asymmetry=metrics.step_time_asymmetry_pct,
            knee_rom_median=_median_or_none(l_knee_rom.rom_deg, r_knee_rom.rom_deg),
            hip_rom_median=_median_or_none(l_hip_rom.rom_deg, r_hip_rom.rom_deg),
            ankle_rom_median=_median_or_none(l_ankle_rom.rom_deg, r_ankle_rom.rom_deg),
            trunk_angle_mean=posture_res.mean_trunk_angle_deg,
            pipeline_conf=metrics.pipeline_confidence,
            adv_temporal=adv_temporal,
            spatial_metrics=spatial_metrics
        )


        # Assemble Full Structured Profile (Section 12)
        gait_profile = GaitProfile(
            temporal=adv_temporal,
            spatial=spatial_metrics,
            symmetry=symmetry_profile,
            joint_motion=joint_motion,
            posture=posture_metrics,
            references=reference_comparisons
        )

        # Angle Curve Time Series for Interactive Frontend Charting
        timestamps = joint_series["left_knee"].timestamps_seconds
        joint_angle_curves = {
            "timestamps": timestamps,
            "left_hip": joint_series["left_hip"].smoothed_angles,
            "right_hip": joint_series["right_hip"].smoothed_angles,
            "left_knee": joint_series["left_knee"].smoothed_angles,
            "right_knee": joint_series["right_knee"].smoothed_angles,
            "left_ankle": joint_series["left_ankle"].smoothed_angles,
            "right_ankle": joint_series["right_ankle"].smoothed_angles,
            "trunk": posture_res.smoothed_angles,
            "gait_events": [
                {
                    "frame_index": e.frame_index,
                    "time_seconds": e.time_seconds,
                    "side": e.side.value,
                    "confidence": e.confidence
                } for e in events
            ]
        }

        # ------------------------------------------------------------------
        # 11. Generate Structured Observation Cards & Developmental Summary
        # ------------------------------------------------------------------
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

        # Unified 4-pillar parent & clinician summary
        dev_summary = self.developmental_synthesizer.synthesize(
            child_age_months=child_age_months,
            metrics=metrics,
            adv_temporal=adv_temporal,
            symmetry=symmetry_profile,
            joint_motion=joint_motion,
            posture=posture_metrics,
            references=reference_comparisons,
            is_rejected=is_rejected
        )

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
            pipeline_confidence=metrics.pipeline_confidence,
            developmental_summary=dev_summary,
            gait_profile=gait_profile,
            temporal=adv_temporal,
            spatial=spatial_metrics,
            symmetry=symmetry_profile,
            joint_motion=joint_motion,
            posture=posture_metrics,
            reference_comparisons=reference_comparisons,
            joint_angle_curves=joint_angle_curves
        )

