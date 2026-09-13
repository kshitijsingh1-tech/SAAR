"""
Tests for Phase 6: Badminton Racket and Shuttlecock Tracking Engine.
Validates Option A implementation (BADMINTON_DECISIONS.md):
1. Racket head tracker anchored to wrist with Section 14 separation.
2. Shuttlecock candidate detection with 3-frame temporal continuity linking.
3. Strict usability gating (< 30% racket, < 25% shuttle) preventing fabricated precision.
4. Real Quality Gate visibility metrics replacing Phase 3 placeholders.
5. Verification on both failure cases (real toddler walk video, blank video) and success cases (smooth flight trajectory).
"""
import os
import cv2
import numpy as np
import pytest

from app.plugins.sports.badminton.schemas import (
    Metric,
    PoseFrame,
    Landmark,
    CourtCalibration,
    SpeedMetrics,
    QualityAssessment
)
from app.plugins.sports.badminton.racket_tracker import (
    BadmintonRacketTracker,
    RacketTrackingSummary,
    RACKET_VISIBILITY_THRESHOLD
)
from app.plugins.sports.badminton.shuttle_tracker import (
    BadmintonShuttleTracker,
    ShuttleTrackingSummary,
    SHUTTLE_USABILITY_THRESHOLD
)
from app.plugins.sports.badminton.pipeline import BadmintonPipeline
from app.plugins.sports.badminton.court_detector import COURT_WIDTH_M, COURT_LENGTH_M


def create_blank_test_frames(n_frames: int = 30, width: int = 640, height: int = 480) -> list:
    """Generates blank frames without player, racket, or shuttle."""
    return [np.zeros((height, width, 3), dtype=np.uint8) for _ in range(n_frames)]


def create_dummy_pose_frames(n_frames: int = 30, moving_wrist: bool = False) -> list:
    """Generates synthetic PoseFrames with optional wrist displacement."""
    frames = []
    for i in range(n_frames):
        lms = [Landmark(x=0.0, y=0.0, z=0.0, visibility=0.0) for _ in range(33)]
        if moving_wrist:
            # Right shoulder (12), right elbow (14), right wrist (16)
            lms[12] = Landmark(x=0.5, y=0.4, z=0.0, visibility=0.95)
            lms[14] = Landmark(x=0.55, y=0.35, z=0.0, visibility=0.95)
            # Moving wrist
            lms[16] = Landmark(x=0.60 + (i * 0.005), y=0.30 - (i * 0.003), z=0.0, visibility=0.95)
        frames.append(PoseFrame(
            frame_index=i,
            timestamp_ms=int(round((i / 30.0) * 1000)),
            landmarks=lms,
            source_width=640,
            source_height=480,
            is_detected=moving_wrist,
            mean_confidence=0.95 if moving_wrist else 0.0
        ))
    return frames


def create_synthetic_shuttle_flight_video_bytes(
    total_frames: int = 30,
    flight_frames_count: int = 12,
    fps: int = 30,
    width: int = 1280,
    height: int = 720
) -> bytes:
    """
    Generates video with a court and a bright white circle moving in a smooth parabolic flight path.
    Flight frames: flight_frames_count / total_frames (e.g. 12/30 = 40% > 25% threshold).
    """
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_path = tmp.name

    out = cv2.VideoWriter(tmp_path, fourcc, float(fps), (width, height))

    # Court corners for calibration
    pts = np.array([[100, 100], [width - 100, 100], [width - 100, height - 100], [100, height - 100]], dtype=np.int32)

    start_x, start_y = 300.0, 200.0
    end_x, end_y = 750.0, 450.0

    for i in range(total_frames):
        frame = np.full((height, width, 3), (35, 75, 40), dtype=np.uint8)  # Green court surface
        # Draw high-contrast white court boundary
        cv2.polylines(frame, [pts], isClosed=True, color=(255, 255, 255), thickness=4)
        cv2.line(frame, (100, height // 2), (width - 100, height // 2), (255, 255, 255), thickness=3)

        # Shuttle in flight during flight window
        if 5 <= i < (5 + flight_frames_count):
            t = (i - 5) / max(1, flight_frames_count - 1)
            # Smooth trajectory
            sx = int(round(start_x + t * (end_x - start_x)))
            sy = int(round(start_y + t * (end_y - start_y) - 30.0 * math.sin(t * math.pi)))
            # Draw bright white compact shuttle candidate (radius 6px, area ~113 px²)
            cv2.circle(frame, (sx, sy), 6, (255, 255, 255), -1)

        out.write(frame)

    out.release()

    with open(tmp_path, "rb") as f:
        video_bytes = f.read()
    try:
        os.remove(tmp_path)
    except OSError:
        pass
    return video_bytes


import math


class TestBadmintonTracking:
    """Test suite verifying Option A tracking, hard gating, and Section 14 distinction."""

    def test_badminton_decisions_documents_option_a_and_thresholds(self):
        """
        Verify that BADMINTON_DECISIONS.md explicitly documents Option A,
        rationale, exact thresholds, and Section 14 wrist vs racket separation.
        """
        decisions_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "app",
            "plugins",
            "sports",
            "BADMINTON_DECISIONS.md"
        )
        assert os.path.exists(decisions_path), "BADMINTON_DECISIONS.md must exist."
        with open(decisions_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "Option A" in content
        assert "NOT_RELIABLY_MEASURABLE" in content
        assert "25%" in content or "0.25" in content
        assert "30%" in content or "0.30" in content
        assert "Section 14" in content
        assert "wrist" in content.lower()
        assert "racket" in content.lower()

    def test_racket_tracker_deliberate_failure_and_gating(self):
        """
        GIVEN blank or featureless frames with no player pose
        WHEN BadmintonRacketTracker.track_racket executes
        THEN visibility_ratio is 0.0 (< 30%), is_usable is False,
        racket_speed_peak.available is False with NOT_RELIABLY_MEASURABLE reason,
        and every frame attempt is recorded.
        """
        tracker = BadmintonRacketTracker()
        frames = create_blank_test_frames(n_frames=20)
        pose_frames = create_dummy_pose_frames(n_frames=20, moving_wrist=False)

        summary = tracker.track_racket(raw_frames=frames, pose_frames=pose_frames)

        assert summary.is_usable is False
        assert summary.visibility_ratio == 0.0
        assert summary.detected_frames_count == 0
        assert summary.total_frames == 20
        assert len(summary.per_frame_records) == 20

        # Peak racket speed must be unavailable
        assert summary.racket_speed_peak.available is False
        assert summary.racket_speed_peak.value is None
        assert "NOT_RELIABLY_MEASURABLE" in summary.racket_speed_peak.unavailable_reason
        assert "30%" in summary.racket_speed_peak.unavailable_reason
        assert summary.racket_speed_peak.confidence == "LOW"
        assert summary.racket_speed_peak.method == "wrist_anchored_contour_gated"

        # Per-frame records must preserve negative results
        for rec in summary.per_frame_records:
            assert rec.is_detected is False
            assert rec.confidence == 0.0
            assert rec.reason is not None

    def test_section_14_wrist_speed_vs_racket_speed_separation(self):
        """
        MASTER SPEC SECTION 14 REQUIREMENT:
        Peak Racket Speed vs Wrist Velocity are distinct kinematic phenomena.
        GIVEN valid wrist movement on a calibrated court without resolvable racket head
        WHEN BadmintonRacketTracker.track_racket executes
        THEN wrist_speed_peak is tracked and available,
        WHILE racket_speed_peak is strictly UNAVAILABLE (NOT_RELIABLY_MEASURABLE),
        and the two are never conflated.
        """
        tracker = BadmintonRacketTracker()
        n_frames = 25
        frames = create_blank_test_frames(n_frames=n_frames, width=1280, height=720)
        pose_frames = create_dummy_pose_frames(n_frames=n_frames, moving_wrist=True)

        pts_px = np.array([[100.0, 100.0], [1180.0, 100.0], [1180.0, 620.0], [100.0, 620.0]], dtype=np.float32)
        pts_world = np.array([[0.0, 0.0], [COURT_WIDTH_M, 0.0], [COURT_WIDTH_M, COURT_LENGTH_M], [0.0, COURT_LENGTH_M]], dtype=np.float32)
        H_px_to_m, _ = cv2.findHomography(pts_px, pts_world)

        calib = CourtCalibration(
            is_calibrated=True,
            calibration_source="test_homography",
            corners_pixel=pts_px.tolist(),
            court_dimensions_m=[COURT_WIDTH_M, COURT_LENGTH_M],
            homography_matrix=H_px_to_m.tolist(),
            confidence=0.95
        )

        summary = tracker.track_racket(raw_frames=frames, pose_frames=pose_frames, court_calibration=calib)

        # 1. Wrist speed is available and measured from pose landmarks
        assert summary.wrist_speed_peak.name == "wrist_speed_peak"
        assert summary.wrist_speed_peak.available is True
        assert summary.wrist_speed_peak.value is not None
        assert summary.wrist_speed_peak.value > 0.0
        assert summary.wrist_speed_peak.method == "mediapipe_blazepose_wrist_landmark"

        # 2. Racket head speed is NOT available because no racket head contour was detected
        assert summary.racket_speed_peak.name == "racket_speed_peak"
        assert summary.racket_speed_peak.available is False
        assert summary.racket_speed_peak.value is None
        assert "NOT_RELIABLY_MEASURABLE" in summary.racket_speed_peak.unavailable_reason
        assert summary.is_usable is False

        # 3. Verify no conflation: wrist speed != racket speed
        assert summary.wrist_speed_peak.name != summary.racket_speed_peak.name
        assert summary.wrist_speed_peak.method != summary.racket_speed_peak.method

    def test_shuttle_tracker_deliberate_failure_and_gating(self):
        """
        GIVEN static or featureless frames
        WHEN BadmintonShuttleTracker.track_shuttle executes
        THEN visibility_ratio is 0.0 (< 25%), is_usable is False,
        shuttle_speed_peak.available is False with NOT_RELIABLY_MEASURABLE reason,
        and all attempts are preserved in per_frame_records.
        """
        tracker = BadmintonShuttleTracker()
        frames = create_blank_test_frames(n_frames=20)

        summary = tracker.track_shuttle(raw_frames=frames)

        assert summary.is_usable is False
        assert summary.visibility_ratio == 0.0
        assert summary.verified_frames_count == 0
        assert summary.total_frames == 20
        assert len(summary.per_frame_records) == 20

        # Shuttle speed must be unavailable
        assert summary.shuttle_speed_peak.available is False
        assert summary.shuttle_speed_peak.value is None
        assert "NOT_RELIABLY_MEASURABLE" in summary.shuttle_speed_peak.unavailable_reason
        assert "25%" in summary.shuttle_speed_peak.unavailable_reason
        assert summary.shuttle_speed_peak.confidence == "LOW"
        assert summary.shuttle_speed_peak.method == "frame_diff_temporal_continuity_gated"

        # Initial frame recorded as baseline
        assert summary.per_frame_records[0].reason is not None
        assert "initial frame" in summary.per_frame_records[0].reason.lower()

    def test_shuttle_tracker_success_on_continuous_flight_trajectory(self):
        """
        GIVEN a calibrated video with a smooth moving bright candidate traversing 12/30 frames (40% > 25%)
        WHEN BadmintonShuttleTracker.track_shuttle executes
        THEN temporal continuity links the flight path,
        is_usable is True, visibility_ratio >= 0.25,
        and shuttle_speed_peak is available with physical km/h value and confidence.
        """
        tracker = BadmintonShuttleTracker()
        video_bytes = create_synthetic_shuttle_flight_video_bytes(
            total_frames=30,
            flight_frames_count=12,
            fps=30,
            width=1280,
            height=720
        )

        pipeline = BadmintonPipeline()
        metadata, frames_meta, raw_frames = pipeline.video_processor.process_video_bytes(video_bytes)

        # Detect court calibration
        keyframe = raw_frames[len(raw_frames) // 2]
        calib = pipeline.court_detector.detect_court(keyframe)
        assert calib.is_calibrated is True

        summary = tracker.track_shuttle(raw_frames=raw_frames, court_calibration=calib, fps=30.0)

        assert summary.is_usable is True
        assert summary.verified_frames_count >= 10
        assert summary.visibility_ratio >= 0.25
        assert summary.shuttle_speed_peak.available is True
        assert summary.shuttle_speed_peak.value is not None
        assert 10.0 <= summary.shuttle_speed_peak.value <= 500.0
        assert summary.shuttle_speed_peak.confidence == "MEDIUM"
        assert summary.shuttle_speed_peak.method == "frame_diff_temporal_continuity_tracking"

    def test_real_video_failure_case_reports_honest_gap(self):
        """
        CRITICAL REAL VIDEO TEST:
        Runs BadmintonPipeline on actual video from repository (sample_toddler_walk.mp4).
        Confirms:
        1. Both trackers run on real frames.
        2. Quality gate racket_visibility and shuttle_visibility are computed from actual attempts.
        3. Because it is a casual non-badminton recording, both tracking ratios fail gating.
        4. SpeedMetrics report available=False with NOT_RELIABLY_MEASURABLE reasons.
        5. Zero fabricated precision or false blob tracking confidence is emitted.
        """
        sample_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "app",
            "gait",
            "assets",
            "sample_toddler_walk.mp4"
        )
        assert os.path.exists(sample_path), f"Sample video not found at {sample_path}"

        with open(sample_path, "rb") as f:
            video_bytes = f.read()

        pipeline = BadmintonPipeline()
        result = pipeline.analyze_video_bytes(video_bytes, filename="sample_toddler_walk.mp4")

        # Video decoded successfully
        assert result.video.total_frames > 0
        assert result.video.duration_seconds >= 3.0

        # Quality Gate visibility metrics are real, not placeholders
        assert result.quality.racket_visibility.name == "racket_visibility"
        assert result.quality.racket_visibility.unit == "ratio"
        assert result.quality.racket_visibility.available is False
        assert "NOT_RELIABLY_MEASURABLE" in result.quality.racket_visibility.unavailable_reason
        assert "30%" in result.quality.racket_visibility.unavailable_reason

        assert result.quality.shuttle_visibility.name == "shuttle_visibility"
        assert result.quality.shuttle_visibility.unit == "ratio"
        assert result.quality.shuttle_visibility.available is False
        assert "NOT_RELIABLY_MEASURABLE" in result.quality.shuttle_visibility.unavailable_reason
        assert "25%" in result.quality.shuttle_visibility.unavailable_reason

        # Speed metrics report unavailable
        assert result.speed_metrics.racket_speed_peak.available is False
        assert result.speed_metrics.racket_speed_peak.value is None
        assert ("NOT_RELIABLY_MEASURABLE" in result.speed_metrics.racket_speed_peak.unavailable_reason or
                "Speed estimate unavailable" in result.speed_metrics.racket_speed_peak.unavailable_reason)

        assert result.speed_metrics.shuttle_speed_peak.available is False
        assert result.speed_metrics.shuttle_speed_peak.value is None
        assert ("NOT_RELIABLY_MEASURABLE" in result.speed_metrics.shuttle_speed_peak.unavailable_reason or
                "Speed estimate unavailable" in result.speed_metrics.shuttle_speed_peak.unavailable_reason)

        # Limitations list carries honest gap reasons
        assert any("RACKET_TRACKING" in lim for lim in result.limitations)
        assert any("SHUTTLE_TRACKING" in lim for lim in result.limitations)
