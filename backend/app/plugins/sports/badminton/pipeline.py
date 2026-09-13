"""
Badminton Video Analysis Pipeline Orchestrator.
Integrates BadmintonVideoProcessor and Badminton QualityGate.
In Phase 3: decodes real video, runs per-frame camera stability and recording-level
quality checks, handles rejection early, and returns quality_assessed_pipeline_pending.
"""
import os
import uuid
import math
from typing import Optional, List, Dict, Any
import numpy as np

from .schemas import (
    BadmintonAnalysisResult,
    BadmintonAnalysisStatus,
    VideoMetadata,
    QualityAssessment,
    CaptureConfidence,
    PlayerMetadata,
    CourtMetrics,
    MovementMetrics,
    SpeedMetrics,
    EnergyMetrics,
    PoseMetrics,
    Metric,
    CourtCalibration,
    BadmintonFrame
)
from .video_processor import BadmintonVideoProcessor
from .quality import assess_badminton_recording_quality
from .court_detector import BadmintonCourtDetector
from .pose_estimator import (
    BadmintonPoseEstimator,
    smooth_pose_frames,
    compute_joint_angle_2d,
    left_shoulder, right_shoulder,
    left_elbow, right_elbow,
    left_wrist, right_wrist,
    left_hip, right_hip
)
from .movement_analyzer import BadmintonMovementAnalyzer
from .racket_tracker import BadmintonRacketTracker
from .shuttle_tracker import BadmintonShuttleTracker
from .shot_detector import BadmintonShotDetector
from .shot_classifier import BadmintonShotClassifier
from .metrics import BadmintonMetricsEngine
from .speed_analyzer import BadmintonSpeedAnalyzer
from .calorie_estimator import BadmintonCalorieEstimator
from .kinematics import BadmintonKinematicsAnalyzer
from .evidence import BadmintonEvidenceGraphBuilder
from .reasoning import BadmintonHypothesisEngine
from .recommendations import BadmintonRecommendationEngine, PrioritizedRecommendation
from .enhancement import video_enhancement_pipeline
from .gemini_service import gemini_sports_supervisor


class BadmintonPipeline:
    """
    Orchestrates ingestion, quality gating, pose tracking, and biomechanical analytics for Badminton videos.
    """

    def __init__(self):
        self.video_processor = BadmintonVideoProcessor()
        self._pose_estimator = None
        self._court_detector = None
        self._movement_analyzer = None
        self._racket_tracker = None
        self._shuttle_tracker = None
        self._shot_detector = None
        self._shot_classifier = None
        self._metrics_engine = None
        self._speed_analyzer = None
        self._calorie_estimator = None
        self._kinematics_analyzer = None
        self._evidence_builder = None
        self._recommendation_engine = None

    @property
    def pose_estimator(self) -> Optional[BadmintonPoseEstimator]:
        if self._pose_estimator is None:
            try:
                self._pose_estimator = BadmintonPoseEstimator()
            except Exception as e:
                print(f"[BadmintonPipeline] Notice: Pose estimator unavailable: {e}")
                self._pose_estimator = None
        return self._pose_estimator

    @property
    def court_detector(self) -> BadmintonCourtDetector:
        if self._court_detector is None:
            self._court_detector = BadmintonCourtDetector()
        return self._court_detector

    @property
    def movement_analyzer(self) -> BadmintonMovementAnalyzer:
        if self._movement_analyzer is None:
            self._movement_analyzer = BadmintonMovementAnalyzer()
        return self._movement_analyzer

    @property
    def racket_tracker(self) -> BadmintonRacketTracker:
        if self._racket_tracker is None:
            self._racket_tracker = BadmintonRacketTracker()
        return self._racket_tracker

    @property
    def shuttle_tracker(self) -> BadmintonShuttleTracker:
        if self._shuttle_tracker is None:
            self._shuttle_tracker = BadmintonShuttleTracker()
        return self._shuttle_tracker

    @property
    def shot_detector(self) -> BadmintonShotDetector:
        if self._shot_detector is None:
            self._shot_detector = BadmintonShotDetector()
        return self._shot_detector

    @property
    def shot_classifier(self) -> BadmintonShotClassifier:
        if self._shot_classifier is None:
            self._shot_classifier = BadmintonShotClassifier()
        return self._shot_classifier

    @property
    def metrics_engine(self) -> BadmintonMetricsEngine:
        if self._metrics_engine is None:
            self._metrics_engine = BadmintonMetricsEngine()
        return self._metrics_engine

    @property
    def speed_analyzer(self) -> BadmintonSpeedAnalyzer:
        if self._speed_analyzer is None:
            self._speed_analyzer = BadmintonSpeedAnalyzer()
        return self._speed_analyzer

    @property
    def calorie_estimator(self) -> BadmintonCalorieEstimator:
        if self._calorie_estimator is None:
            self._calorie_estimator = BadmintonCalorieEstimator()
        return self._calorie_estimator

    @property
    def kinematics_analyzer(self) -> BadmintonKinematicsAnalyzer:
        if self._kinematics_analyzer is None:
            self._kinematics_analyzer = BadmintonKinematicsAnalyzer()
        return self._kinematics_analyzer

    @property
    def evidence_builder(self) -> BadmintonEvidenceGraphBuilder:
        if self._evidence_builder is None:
            self._evidence_builder = BadmintonEvidenceGraphBuilder()
        return self._evidence_builder

    @property
    def recommendation_engine(self) -> BadmintonRecommendationEngine:
        if self._recommendation_engine is None:
            self._recommendation_engine = BadmintonRecommendationEngine()
        return self._recommendation_engine

    def analyze_video_bytes(
        self,
        video_bytes: bytes,
        filename: str = "badminton_rally.mp4",
        player_metadata: Optional[PlayerMetadata] = None,
        analysis_id: Optional[str] = None,
        court_calibration_override: Optional[CourtCalibration] = None
    ) -> BadmintonAnalysisResult:
        """
        Ingests video bytes, decodes frames via cv2, runs the quality gate,
        performs single-player pose estimation with temporal smoothing,
        and estimates metric court calibration via OpenCV homography or manual override.
        """
        analysis_id = analysis_id or f"badminton_{uuid.uuid4().hex[:8]}"

        # 1. Guard against empty or corrupted inputs
        if not video_bytes or len(video_bytes) == 0:
            rejection_quality = QualityAssessment(
                confidence=CaptureConfidence.REJECT,
                issues=["Supplied video file is empty (0 bytes)."]
            )
            return BadmintonAnalysisResult(
                analysis_id=analysis_id,
                video_id=f"vid_{uuid.uuid4().hex[:6]}",
                video=VideoMetadata(
                    filename=filename,
                    duration_seconds=0.0,
                    fps=0.0,
                    total_frames=0,
                    frames_processed=0,
                    width=0,
                    height=0
                ),
                quality=rejection_quality,
                player_metadata=player_metadata,
                shots=[],
                court_metrics=CourtMetrics(),
                movement_metrics=MovementMetrics(),
                speed_metrics=SpeedMetrics(),
                energy_metrics=EnergyMetrics(),
                pose_metrics=PoseMetrics(),
                court_calibration=None,
                pose_frames=[],
                findings=["Ingestion rejected: video payload contains 0 bytes."],
                hypotheses=[],
                recommendations=["Please upload a valid MP4 or MOV video file."],
                evidence=[],
                limitations=["No video data available."],
                rejection_reason="Supplied video file is empty (0 bytes).",
                status=BadmintonAnalysisStatus.REJECTED
            )

        try:
            metadata, frames_meta, raw_frames = self.video_processor.process_video_bytes(
                video_bytes=video_bytes,
                filename=filename
            )
        except Exception as decode_err:
            rejection_quality = QualityAssessment(
                confidence=CaptureConfidence.REJECT,
                issues=[f"Video decoding failed: {str(decode_err)}"]
            )
            return BadmintonAnalysisResult(
                analysis_id=analysis_id,
                video_id=f"vid_{uuid.uuid4().hex[:6]}",
                video=VideoMetadata(
                    filename=filename,
                    duration_seconds=0.0,
                    fps=0.0,
                    total_frames=0,
                    frames_processed=0,
                    width=0,
                    height=0
                ),
                quality=rejection_quality,
                player_metadata=player_metadata,
                shots=[],
                court_metrics=CourtMetrics(),
                movement_metrics=MovementMetrics(),
                speed_metrics=SpeedMetrics(),
                energy_metrics=EnergyMetrics(),
                pose_metrics=PoseMetrics(),
                court_calibration=None,
                pose_frames=[],
                findings=["Ingestion rejected: Video container could not be decoded."],
                hypotheses=[],
                recommendations=["Ensure the video is an uncorrupted MP4/MOV container with standard H.264/AVC encoding."],
                evidence=[],
                limitations=["Corrupted or unreadable video container."],
                rejection_reason=f"Video decoding failed: {str(decode_err)}",
                status=BadmintonAnalysisStatus.REJECTED,
                graph_data=self.evidence_builder.build_evidence_graph(
                    video_metadata=VideoMetadata(
                        filename=filename,
                        duration_seconds=0.0,
                        fps=0.0,
                        total_frames=0,
                        frames_processed=0,
                        width=0,
                        height=0
                    ),
                    quality=rejection_quality,
                    player_metadata=player_metadata,
                    limitations=["Corrupted or unreadable video container."]
                )
            )

        # 2. Evaluate Recording Quality
        quality = assess_badminton_recording_quality(metadata, raw_frames)

        # 3. Early Rejection Branch (matching gait pipeline pattern)
        if quality.confidence == CaptureConfidence.REJECT:
            rejection_msg = "; ".join(quality.issues) if quality.issues else "Video failed capture quality thresholds."
            return BadmintonAnalysisResult(
                analysis_id=analysis_id,
                video_id=f"vid_{uuid.uuid4().hex[:6]}",
                video=metadata,
                quality=quality,
                player_metadata=player_metadata,
                shots=[],
                court_metrics=CourtMetrics(),
                movement_metrics=MovementMetrics(),
                speed_metrics=SpeedMetrics(),
                energy_metrics=EnergyMetrics(),
                pose_metrics=PoseMetrics(),
                court_calibration=None,
                pose_frames=[],
                findings=["Recording quality assessment failed minimum thresholds for badminton analysis."],
                hypotheses=[],
                recommendations=[
                    "Ensure video duration is at least 3.0 seconds long to capture a full stroke or rally exchange.",
                    "Mount camera on a stable tripod positioned behind the baseline or at a 45° diagonal angle.",
                    "Record at 30+ FPS (60 FPS recommended) in 720p or 1080p resolution."
                ],
                evidence=[
                    f"Rejected video input: {metadata.width}x{metadata.height} @ {metadata.fps} FPS ({metadata.duration_seconds}s, {metadata.total_frames} frames)."
                ],
                limitations=["Video rejected by quality gate before pose or stroke analysis."],
                rejection_reason=rejection_msg,
                status=BadmintonAnalysisStatus.REJECTED,
                graph_data=self.evidence_builder.build_evidence_graph(
                    video_metadata=metadata,
                    quality=quality,
                    player_metadata=player_metadata,
                    limitations=["Video rejected by quality gate before pose or stroke analysis."]
                )
            )

        # 3.5. Automated Neural Video Enhancement (Super-Resolution, Optical Flow Frame Interpolation, Dynamic Lighting)
        enhancement_meta = None
        processing_frames = raw_frames
        if video_enhancement_pipeline.needs_enhancement(metadata):
            processing_frames, enhancement_meta, metadata = video_enhancement_pipeline.enhance_clip(
                raw_frames=raw_frames,
                metadata=metadata
            )
            # Synchronize frames_meta count if temporal frame interpolation synthesized micro-frames
            if len(processing_frames) != len(frames_meta):
                fps_val = metadata.fps if metadata.fps > 0 else 30.0
                frames_meta = [
                    BadmintonFrame(
                        frame_index=i,
                        timestamp_ms=int(round(i * 1000.0 / fps_val)),
                        is_keyframe=(i % max(1, int(fps_val // 2)) == 0),
                        width=metadata.width,
                        height=metadata.height
                    )
                    for i in range(len(processing_frames))
                ]

        # 4. Court Geometry & Metric Homography Calibration
        if court_calibration_override is not None and court_calibration_override.is_calibrated:
            court_calibration = court_calibration_override
        else:
            court_mode = "doubles"
            if player_metadata and player_metadata.match_type:
                court_mode = "singles" if "singles" in player_metadata.match_type.lower() else "doubles"
            keyframe_idx = len(processing_frames) // 2 if processing_frames else 0
            keyframe = processing_frames[keyframe_idx] if processing_frames else None
            court_calibration = self.court_detector.detect_court(keyframe, court_mode=court_mode)

        if court_calibration.is_calibrated:
            quality.court_visibility = Metric(
                name="court_visibility",
                value=court_calibration.confidence,
                unit="score",
                confidence="HIGH" if court_calibration.confidence >= 0.7 else "MEDIUM",
                method=court_calibration.calibration_source or "opencv_hough_outer_corners",
                available=True,
                unavailable_reason=None
            )
        else:
            quality.court_visibility = Metric(
                name="court_visibility",
                value=None,
                unit="score",
                confidence="LOW",
                method=court_calibration.calibration_source or "opencv_hough_outer_corners",
                available=False,
                unavailable_reason=court_calibration.uncalibrated_reason or "Insufficient court line visibility"
            )

        # 5. Single-Player Pose Estimation
        raw_pose_frames = []
        estimator = self.pose_estimator

        if estimator is not None:
            for i, f_img in enumerate(processing_frames):
                f_meta = frames_meta[i]
                pf = estimator.process_frame(
                    frame_rgb_or_bgr=f_img,
                    frame_index=f_meta.frame_index,
                    timestamp_ms=f_meta.timestamp_ms,
                    is_bgr=True
                )
                raw_pose_frames.append(pf)
        else:
            # Pose estimator unavailable (e.g. dependency missing in environment)
            for i, f_meta in enumerate(frames_meta):
                empty_lms = [Landmark(x=0.0, y=0.0, z=0.0, visibility=0.0) for _ in range(33)]
                raw_pose_frames.append(PoseFrame(
                    frame_index=f_meta.frame_index,
                    timestamp_ms=f_meta.timestamp_ms,
                    landmarks=empty_lms,
                    source_width=metadata.width,
                    source_height=metadata.height,
                    is_detected=False,
                    detection_reason="MediaPipe Pose estimator unavailable in runtime environment.",
                    mean_confidence=0.0
                ))

        # 6. Apply Temporal Smoothing (Savitzky-Golay via gait smoothing utilities)
        smoothed_pose_frames = smooth_pose_frames(raw_pose_frames, fps=metadata.fps)

        # 7. Evaluate Player Visibility Quality Metric
        detected_frames = [pf for pf in smoothed_pose_frames if pf.is_detected]
        det_ratio = len(detected_frames) / max(1, len(smoothed_pose_frames))

        if detected_frames:
            quality.player_visibility = Metric(
                name="player_visibility",
                value=float(round(det_ratio, 3)),
                unit="ratio",
                confidence="HIGH" if det_ratio >= 0.75 else "MEDIUM" if det_ratio >= 0.4 else "LOW",
                method="mediapipe_blazepose_33",
                available=True,
                unavailable_reason=None
            )
        else:
            quality.player_visibility = Metric(
                name="player_visibility",
                value=None,
                unit="ratio",
                confidence="LOW",
                method="mediapipe_blazepose_33",
                available=False,
                unavailable_reason="No human pose detected by BlazePose across any video frames."
            )

        # 8. Compute Measured Kinematics (PoseMetrics)
        elbow_angles = []
        trunk_angles = []

        for pf in detected_frames:
            # Measure elbow extension on dominant arm (or maximum visible arm)
            r_elb_ang = compute_joint_angle_2d(right_shoulder(pf), right_elbow(pf), right_wrist(pf))
            l_elb_ang = compute_joint_angle_2d(left_shoulder(pf), left_elbow(pf), left_wrist(pf))
            valid_elbs = [a for a in [r_elb_ang, l_elb_ang] if a is not None]
            if valid_elbs:
                elbow_angles.append(max(valid_elbs))

            # Measure trunk angle relative to vertical axis
            r_hip_lm = right_hip(pf)
            l_hip_lm = left_hip(pf)
            r_sh_lm = right_shoulder(pf)
            l_sh_lm = left_shoulder(pf)
            if r_hip_lm.visibility > 0.25 and l_hip_lm.visibility > 0.25 and r_sh_lm.visibility > 0.25 and l_sh_lm.visibility > 0.25:
                mid_hip = ((r_hip_lm.x + l_hip_lm.x) / 2.0, (r_hip_lm.y + l_hip_lm.y) / 2.0)
                mid_sh = ((r_sh_lm.x + l_sh_lm.x) / 2.0, (r_sh_lm.y + l_sh_lm.y) / 2.0)
                dx = mid_sh[0] - mid_hip[0]
                dy = mid_sh[1] - mid_hip[1] # Note: y increases downwards in image coordinates
                # Angle relative to vertical (upwards is dy < 0)
                trunk_ang = abs(math.degrees(math.atan2(dx, -dy)))
                trunk_angles.append(trunk_ang)

        peak_elbow = round(float(np.max(elbow_angles)), 1) if elbow_angles else None
        mean_trunk = round(float(np.mean(trunk_angles)), 1) if trunk_angles else None

        pose_metrics = PoseMetrics(
            kinetic_chain_sequence_score=None,
            kinetic_chain_reason="NOT_YET_IMPLEMENTED: Pending stroke classification & phase segmentation (Phase 5/6)",
            shoulder_internal_rotation_deg=None,
            shoulder_rotation_reason="NOT_YET_IMPLEMENTED: Pending stroke contact phase segmentation (Phase 5/6)",
            elbow_extension_deg=peak_elbow,
            elbow_extension_reason=None if peak_elbow is not None else "No valid elbow landmarks detected in video.",
            wrist_pronation_deg=None,
            wrist_pronation_reason="NOT_RELIABLY_MEASURABLE: No object detector available in v1",
            trunk_rotation_deg=mean_trunk,
            trunk_rotation_reason=None if mean_trunk is not None else "No valid trunk landmarks detected in video."
        )

        # 9. Movement & Spatial Court Analysis (Phase 5)
        movement_metrics, court_metrics, movement_findings = self.movement_analyzer.analyze_movement(
            pose_frames=smoothed_pose_frames,
            court_calibration=court_calibration,
            player_metadata=player_metadata
        )

        # 10. Racket & Wrist Kinematics Tracking (Phase 6 Option A)
        racket_summary = self.racket_tracker.track_racket(
            raw_frames=processing_frames,
            pose_frames=smoothed_pose_frames,
            court_calibration=court_calibration,
            fps=metadata.fps
        )

        # 11. Shuttlecock Trajectory Tracking (Phase 6 Option A)
        shuttle_summary = self.shuttle_tracker.track_shuttle(
            raw_frames=processing_frames,
            court_calibration=court_calibration,
            fps=metadata.fps
        )

        # 12. Update Quality Gate with REAL visibility metrics (Phase 6 replaces placeholders)
        if racket_summary.is_usable:
            quality.racket_visibility = Metric(
                name="racket_visibility",
                value=racket_summary.visibility_ratio,
                unit="ratio",
                confidence="HIGH" if racket_summary.visibility_ratio >= 0.50 else "MEDIUM",
                method="wrist_anchored_contour_optical_tracking",
                available=True,
                unavailable_reason=None
            )
        else:
            quality.racket_visibility = Metric(
                name="racket_visibility",
                value=None,
                unit="ratio",
                confidence="LOW",
                method="wrist_anchored_contour_optical_tracking",
                available=False,
                unavailable_reason=f"NOT_RELIABLY_MEASURABLE: Racket head detected in only {racket_summary.visibility_ratio * 100:.1f}% of frames (minimum 30% required)."
            )

        if shuttle_summary.is_usable:
            quality.shuttle_visibility = Metric(
                name="shuttle_visibility",
                value=shuttle_summary.visibility_ratio,
                unit="ratio",
                confidence="HIGH" if shuttle_summary.visibility_ratio >= 0.50 else "MEDIUM",
                method="frame_diff_temporal_continuity",
                available=True,
                unavailable_reason=None
            )
        else:
            quality.shuttle_visibility = Metric(
                name="shuttle_visibility",
                value=None,
                unit="ratio",
                confidence="LOW",
                method="frame_diff_temporal_continuity",
                available=False,
                unavailable_reason=f"NOT_RELIABLY_MEASURABLE: Shuttle tracked in only {shuttle_summary.visibility_ratio * 100:.1f}% of frames (minimum 25% required)."
            )

        # 14. Candidate Shot Contact Detection (Phase 7 Section 15)
        candidate_shots = self.shot_detector.detect_shots(
            pose_frames=smoothed_pose_frames,
            racket_summary=racket_summary,
            shuttle_summary=shuttle_summary,
            court_calibration=court_calibration,
            fps=metadata.fps
        )

        # 15. Biomechanical Shot Classification (Phase 7 Section 16)
        classified_shots = self.shot_classifier.classify_shots(
            candidate_shots=candidate_shots,
            pose_frames=smoothed_pose_frames,
            court_calibration=court_calibration
        )

        # 16. Calibrated Speed Analysis (Phase 9 Sections 13, 14, 17, 18)
        speed_metrics, speed_enhanced_shots, speed_findings = self.speed_analyzer.analyze_speeds(
            shots=classified_shots,
            racket_summary=racket_summary,
            shuttle_summary=shuttle_summary,
            court_calibration=court_calibration,
            fps=metadata.fps
        )

        # 17. Shot Contact Joint Kinematics & Kinetic Chain Sequencing (Phase 11)
        kinematics_enhanced_shots, contact_pose_metrics, kinematics_findings = self.kinematics_analyzer.analyze_shot_kinematics(
            shots=speed_enhanced_shots,
            pose_frames=smoothed_pose_frames,
            fps=metadata.fps
        )

        if contact_pose_metrics.elbow_extension_deg is not None:
            pose_metrics.elbow_extension_deg = contact_pose_metrics.elbow_extension_deg
            pose_metrics.elbow_extension_reason = None
        if contact_pose_metrics.shoulder_internal_rotation_deg is not None:
            pose_metrics.shoulder_internal_rotation_deg = contact_pose_metrics.shoulder_internal_rotation_deg
            pose_metrics.shoulder_rotation_reason = None

        # 18. Compute Aggregation Metrics, Placement Geometry, and Recovery (Phase 8)
        shot_metrics, metrics_findings = self.metrics_engine.compute_shot_metrics(
            shots=kinematics_enhanced_shots,
            pose_frames=smoothed_pose_frames,
            court_calibration=court_calibration,
            total_movement_distance_m=movement_metrics.total_distance_m
        )

        if court_metrics and shot_metrics.recovery_metrics.get("average_recovery_time_s") is not None:
            court_metrics.base_recovery_time_sec = shot_metrics.recovery_metrics["average_recovery_time_s"]
            court_metrics.base_recovery_reason = None

        # 19. Synthesize Findings & Evidence
        tracking_findings = []
        if kinematics_enhanced_shots:
            type_counts = {}
            for s in kinematics_enhanced_shots:
                type_counts[s.shot_type] = type_counts.get(s.shot_type, 0) + 1
            dist_str = ", ".join(f"{count} {stype}" for stype, count in sorted(type_counts.items()))
            tracking_findings.append(f"Detected and classified {len(kinematics_enhanced_shots)} shot event(s): {dist_str}.")
        else:
            tracking_findings.append("No active stroke contact events detected in video clip.")

        if racket_summary.is_usable:
            tracking_findings.append(
                f"Racket head tracked across {racket_summary.detected_frames_count}/{racket_summary.total_frames} frames "
                f"({racket_summary.visibility_ratio * 100:.1f}% visibility)."
            )
        else:
            tracking_findings.append(
                f"Racket head tracking: {racket_summary.racket_speed_peak.unavailable_reason or 'Tracking below reliability threshold'}."
            )

        if shuttle_summary.is_usable:
            tracking_findings.append(
                f"Shuttlecock trajectory verified across {shuttle_summary.verified_frames_count}/{shuttle_summary.total_frames} frames "
                f"({shuttle_summary.visibility_ratio * 100:.1f}% visibility)."
            )
        else:
            tracking_findings.append(
                f"Shuttlecock tracking: {shuttle_summary.shuttle_speed_peak.unavailable_reason or 'Tracking below temporal continuity threshold'}."
            )

        # 20. Energy Expenditure & Calorie Estimation (Phase 10)
        energy_metrics = self.calorie_estimator.estimate_energy_expenditure(
            player_metadata=player_metadata,
            video_metadata=metadata,
            movement_metrics=movement_metrics,
            shots=kinematics_enhanced_shots
        )

        energy_findings = []
        if energy_metrics.available and energy_metrics.estimated_energy_expenditure_kcal is not None:
            type_label = "Personalized" if energy_metrics.estimation_type == "personalized" else "Population-average generalized"
            energy_findings.append(
                f"Energy expenditure ({type_label}): {energy_metrics.estimated_energy_expenditure_kcal} kcal "
                f"(range: {energy_metrics.estimated_range_kcal[0]}–{energy_metrics.estimated_range_kcal[1]} kcal, "
                f"MET={energy_metrics.met_value}, inputs: {', '.join(energy_metrics.inputs_used)})."
            )

        findings = [
            f"Video capture quality verified ({quality.confidence.value}).",
            (
                f"Player tracked across {len(detected_frames)}/{len(smoothed_pose_frames)} frames "
                f"({det_ratio * 100:.1f}% visibility) with 33 BlazePose landmarks and Savitzky-Golay smoothing."
                if detected_frames
                else "No human pose detected in video frames."
            ),
            (
                f"Court metric homography successfully calibrated ({court_calibration.calibration_source}, confidence: {court_calibration.confidence})."
                if court_calibration.is_calibrated
                else f"Court uncalibrated: {court_calibration.uncalibrated_reason}"
            )
        ] + movement_findings + tracking_findings + speed_findings + metrics_findings + kinematics_findings + energy_findings


        evidence = [
            f"Verified video input: {metadata.width}x{metadata.height} @ {metadata.fps} FPS ({metadata.duration_seconds}s, {metadata.total_frames} frames).",
            f"Camera stability score: {quality.camera_stability_score}.",
            f"Processed {len(smoothed_pose_frames)} pose frames with temporal smoothing.",
            f"Racket tracking attempt: {racket_summary.detected_frames_count}/{racket_summary.total_frames} frames ({racket_summary.visibility_ratio * 100:.1f}%).",
            f"Shuttle tracking attempt: {shuttle_summary.verified_frames_count}/{shuttle_summary.total_frames} frames ({shuttle_summary.visibility_ratio * 100:.1f}%).",
            f"Detected {len(classified_shots)} stroke contact event(s)."
        ]
        if court_calibration.is_calibrated:
            evidence.append(f"Court 4 corners (px): {court_calibration.corners_pixel}")
            if movement_metrics.total_distance_m is not None:
                evidence.append(
                    f"Calibrated path: distance={movement_metrics.total_distance_m}m, "
                    f"speed={movement_metrics.average_speed_m_s}m/s, coverage={court_metrics.court_coverage_pct}%"
                )

        limitations = []
        if not speed_metrics.racket_speed_peak.available:
            limitations.append(f"RACKET_TRACKING: {speed_metrics.racket_speed_peak.unavailable_reason}")
        if not speed_metrics.shuttle_speed_peak.available:
            limitations.append(f"SHUTTLE_TRACKING: {speed_metrics.shuttle_speed_peak.unavailable_reason}")
        if not court_calibration.is_calibrated:
            limitations.append(f"COURT_UNCALIBRATED: {court_calibration.uncalibrated_reason}")

        hypotheses = [
            "H1_KINEMATICS: Landmark trajectories smoothed via Savitzky-Golay filter to isolate true athletic velocity peaks."
        ]

        # Evaluate Section 11 Multi-Signal Hypothesis Gate (Left-Space Underutilization)
        spatial_gate = BadmintonHypothesisEngine.evaluate_left_space_underutilization(
            court_calibration=court_calibration,
            movement_metrics=movement_metrics,
            shot_metrics=shot_metrics,
            shots=kinematics_enhanced_shots
        )
        if spatial_gate.is_asserted and spatial_gate.hedged_summary:
            hypotheses.append(f"H_SPATIAL_LEFT_SPACE: {spatial_gate.hedged_summary}")
        elif not court_calibration.is_calibrated:
            hypotheses.append(
                "H_TACTICAL_UNCORROBORATED: Court homography uncalibrated — spatial lateral hypothesis gating requires verified perspective geometry."
            )
        else:
            hypotheses.append(
                f"H_TACTICAL_BALANCED: Spatial distribution indicates balanced court coverage without statistically significant lateral asymmetry ({spatial_gate.gate_reason})."
            )

        # Overhead extension kinematic hypothesis if detected
        if contact_pose_metrics.elbow_extension_deg is not None:
            if contact_pose_metrics.elbow_extension_deg < 155.0:
                hypotheses.append(
                    f"H_OVERHEAD_EXTENSION: Contact elbow angle averaged {contact_pose_metrics.elbow_extension_deg:.1f}°, which is consistent with early racquet drop or incomplete overhead kinetic chain extension."
                )
            else:
                hypotheses.append(
                    f"H_OVERHEAD_EXTENSION: Contact elbow angle averaged {contact_pose_metrics.elbow_extension_deg:.1f}°, demonstrating verified full overhead reach extension."
                )

        # 21. Multimodal Cognitive Supervision (Gemini 1.5 Sports Video Supervisor)
        supervisor_insights = gemini_sports_supervisor.supervise_rally_analysis(
            video_metadata=metadata.model_dump(),
            shots=[s.model_dump() for s in kinematics_enhanced_shots],
            court_calibration=court_calibration.model_dump() if court_calibration else None,
            movement_metrics=movement_metrics.model_dump() if movement_metrics else None
        )
        if supervisor_insights and supervisor_insights.get("insights_summary"):
            hypotheses.append(f"H_GEMINI_SUPERVISION: {supervisor_insights['insights_summary']}")
            if enhancement_meta:
                enhancement_meta.gemini_supervisor_applied = True
                enhancement_meta.gemini_insights_summary = supervisor_insights['insights_summary']

        # 11. Generate Traceable, Prioritized Recommendations (Phase 14, Section 51, Section 40, Section 23)
        temp_result = BadmintonAnalysisResult(
            analysis_id=analysis_id,
            video_id=f"vid_{uuid.uuid4().hex[:6]}",
            video=metadata,
            quality=quality,
            player_metadata=player_metadata,
            shots=kinematics_enhanced_shots,
            shot_metrics=shot_metrics,
            court_metrics=court_metrics,
            movement_metrics=movement_metrics,
            speed_metrics=speed_metrics,
            energy_metrics=energy_metrics,
            pose_metrics=pose_metrics,
            court_calibration=court_calibration,
            pose_frames=smoothed_pose_frames,
            findings=findings,
            hypotheses=hypotheses,
            recommendations=[],
            evidence=evidence,
            limitations=limitations,
            rejection_reason=None,
            status=BadmintonAnalysisStatus.QUALITY_ASSESSED_PIPELINE_PENDING,
            graph_data=None,
            enhancement=enhancement_meta
        )
        prioritized_recs = self.recommendation_engine.generate_recommendations(temp_result)
        recommendations = [r.to_summary_string() for r in prioritized_recs]
        if not recommendations:
            recommendations = list(quality.issues) if quality.issues else ["Perception verified. Continue standard skill maintenance drills."]

        # 12. Build Knowledge & Evidence Graph (Phases 5-11, Section 25 & Section 28)
        graph_data = self.evidence_builder.build_evidence_graph(
            video_metadata=metadata,
            quality=quality,
            player_metadata=player_metadata,
            court_calibration=court_calibration,
            court_metrics=court_metrics,
            movement_metrics=movement_metrics,
            shots=kinematics_enhanced_shots,
            shot_metrics=shot_metrics,
            speed_metrics=speed_metrics,
            energy_metrics=energy_metrics,
            pose_metrics=pose_metrics,
            hypotheses=hypotheses,
            recommendations=recommendations,
            limitations=limitations
        )

        return BadmintonAnalysisResult(
            analysis_id=analysis_id,
            video_id=f"vid_{uuid.uuid4().hex[:6]}",
            player_id=player_metadata.player_id if player_metadata else None,
            video=metadata,
            quality=quality,
            player_metadata=player_metadata,
            shots=kinematics_enhanced_shots,
            shot_metrics=shot_metrics,
            court_metrics=court_metrics,
            movement_metrics=movement_metrics,
            speed_metrics=speed_metrics,
            energy_metrics=energy_metrics,
            pose_metrics=pose_metrics,
            court_calibration=court_calibration,
            pose_frames=smoothed_pose_frames,
            findings=findings,
            hypotheses=hypotheses,
            recommendations=recommendations,
            prioritized_recommendations=prioritized_recs,
            evidence=evidence,
            limitations=limitations,
            rejection_reason=None,
            status=BadmintonAnalysisStatus.QUALITY_ASSESSED_PIPELINE_PENDING,
            graph_data=graph_data,
            enhancement=enhancement_meta
        )

    def compare_longitudinal_sessions(
        self,
        sessions: List[BadmintonAnalysisResult],
        player_id: Optional[str] = None
    ):
        """
        Phase 17: Deterministic multi-session trend analysis for the same player_id.
        """
        from .longitudinal import BadmintonLongitudinalAnalyzer
        analyzer = BadmintonLongitudinalAnalyzer()
        return analyzer.compare_sessions(sessions, player_id)



