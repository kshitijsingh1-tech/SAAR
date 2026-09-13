"""
Tests for Phase 8: Badminton Metrics Engine, Placement Geometry, and Movement Recovery.
Validates Sections 17, 19, 20, and 21 of the Master Spec:
1. Per-shot duration (end_timestamp - contact_timestamp) and stats.
2. Shot type counts and percentages, including UNKNOWN.
3. Shot placement gated by MIN_PLACEMENT_SAMPLE_SIZE (>= 3).
4. Player movement recovery after each shot.
5. Movement efficiency strictly reported as NOT_RELIABLY_MEASURABLE.
6. Real video end-to-end verification and 100% JSON traceability.
"""
import os
import inspect
import numpy as np
import pytest

from app.plugins.sports.badminton.schemas import (
    ShotResult,
    ShotMetrics,
    PoseFrame,
    Landmark,
    CourtCalibration,
    Metric
)
from app.plugins.sports.badminton.metrics import (
    BadmintonMetricsEngine,
    MIN_PLACEMENT_SAMPLE_SIZE
)
from app.plugins.sports.badminton.pipeline import BadmintonPipeline
from app.plugins.sports.badminton.court_detector import COURT_WIDTH_M, COURT_LENGTH_M


def create_synthetic_calibration() -> CourtCalibration:
    """Returns a valid metric court calibration."""
    import cv2
    pts_px = np.array([[100.0, 100.0], [1180.0, 100.0], [1180.0, 620.0], [100.0, 620.0]], dtype=np.float32)
    pts_world = np.array([[0.0, 0.0], [COURT_WIDTH_M, 0.0], [COURT_WIDTH_M, COURT_LENGTH_M], [0.0, COURT_LENGTH_M]], dtype=np.float32)
    H_px_to_m, _ = cv2.findHomography(pts_px, pts_world)

    return CourtCalibration(
        is_calibrated=True,
        calibration_source="test_calibration",
        corners_pixel=pts_px.tolist(),
        court_dimensions_m=[COURT_WIDTH_M, COURT_LENGTH_M],
        homography_matrix=H_px_to_m.tolist(),
        confidence=0.95
    )


class TestBadmintonMetrics:
    """Comprehensive test suite for Phase 8 metrics aggregation and gating."""

    def test_shot_duration_docstring_and_section_17_definition(self):
        """
        TASK 1 REQUIREMENT:
        per-shot duration = end_timestamp - contact_timestamp (state this definition
        in a docstring per Section 17 — do not silently mix it with rally-phase duration).
        """
        import app.plugins.sports.badminton.metrics as metrics_mod
        doc = inspect.getdoc(metrics_mod)
        assert doc is not None
        assert "Section 17" in doc
        assert "end_timestamp - contact_timestamp" in doc
        assert "strictly distinct from" in doc or "rally" in doc

        # Test mathematical calculation
        engine = BadmintonMetricsEngine()
        s1 = ShotResult(
            shot_id="shot_001",
            shot_type="smash",
            confidence=0.85,
            start_time=1.0,
            contact_time=1.3,
            end_time=1.7,  # duration = 1.7 - 1.3 = 0.4s
            duration=0.7
        )
        s2 = ShotResult(
            shot_id="shot_002",
            shot_type="clear",
            confidence=0.80,
            start_time=2.0,
            contact_time=2.4,
            end_time=3.0,  # duration = 3.0 - 2.4 = 0.6s
            duration=1.0
        )

        metrics, findings = engine.compute_shot_metrics([s1, s2])
        assert metrics.total_shots == 2
        assert metrics.shot_durations_s == [0.4, 0.6]
        assert metrics.average_duration_s == 0.5
        assert metrics.median_duration_s == 0.5
        assert metrics.min_duration_s == 0.4
        assert metrics.max_duration_s == 0.6

    def test_shot_type_counts_and_percentages_including_unknown(self):
        """
        TASK 1 REQUIREMENT:
        count_by_shot_type and percentage_by_shot_type computed from actual detected shots
        (including UNKNOWN as its own bucket — don't hide it).
        """
        engine = BadmintonMetricsEngine()
        shots = [
            ShotResult(shot_id="s1", shot_type="smash", confidence=0.8, start_time=0.0, contact_time=0.2, end_time=0.5),
            ShotResult(shot_id="s2", shot_type="smash", confidence=0.8, start_time=1.0, contact_time=1.2, end_time=1.5),
            ShotResult(shot_id="s3", shot_type="drop", confidence=0.75, start_time=2.0, contact_time=2.2, end_time=2.6),
            ShotResult(shot_id="s4", shot_type="unknown", confidence=0.40, start_time=3.0, contact_time=3.2, end_time=3.5)
        ]

        metrics, findings = engine.compute_shot_metrics(shots)
        assert metrics.total_shots == 4
        assert metrics.count_by_shot_type == {"smash": 2, "drop": 1, "unknown": 1}
        assert metrics.percentage_by_shot_type == {
            "smash": 50.0,
            "drop": 25.0,
            "unknown": 25.0
        }

        # Unknown must be prominently included
        assert "unknown" in metrics.count_by_shot_type
        assert metrics.count_by_shot_type["unknown"] == 1
        assert metrics.percentage_by_shot_type["unknown"] == 25.0

    def test_shot_placement_gated_by_sample_size(self):
        """
        TASK 2 REQUIREMENT:
        Placement geometry (cross-court, straight-line, corner frequencies) requires a minimum
        sample size (MIN_PLACEMENT_SAMPLE_SIZE = 3).
        Below threshold, claims must be gated with explicit explanation.
        Above threshold, percentages must be exact and traceable.
        """
        engine = BadmintonMetricsEngine()
        calib = create_synthetic_calibration()

        # Case A: Insufficient sample size (2 shots < 3)
        shots_under = [
            ShotResult(shot_id="s1", target_position=[1.5, 4.0], start_time=0.0, contact_time=0.2, end_time=0.5),
            ShotResult(shot_id="s2", target_position=[5.0, 2.0], start_time=1.0, contact_time=1.2, end_time=1.5)
        ]
        metrics_under, findings_under = engine.compute_shot_metrics(shots_under, court_calibration=calib)
        assert metrics_under.placement_metrics["available"] is False
        assert "Insufficient placement sample size" in metrics_under.placement_metrics["reason"]
        assert f"minimum {MIN_PLACEMENT_SAMPLE_SIZE}" in metrics_under.placement_metrics["reason"]

        # Case B: Sufficient sample size (4 shots >= 3)
        # Player at right side (x=5.0m)
        shots_valid = [
            # Cross-court to far left corner (x=1.2m, y=1.0m): |1.2 - 5.0| = 3.8m >= 2.0m -> cross-court, corner
            ShotResult(shot_id="s1", player_position=[5.0, 10.0], target_position=[1.2, 1.0], start_time=0.0, contact_time=0.2, end_time=0.5),
            # Cross-court to mid left (x=1.5m, y=3.0m): cross-court, mid depth (not corner)
            ShotResult(shot_id="s2", player_position=[5.0, 10.0], target_position=[1.5, 3.0], start_time=1.0, contact_time=1.2, end_time=1.5),
            # Straight-line to far right corner (x=5.2m, y=1.2m): |5.2 - 5.0| = 0.2m < 2.0m -> straight, corner
            ShotResult(shot_id="s3", player_position=[5.0, 10.0], target_position=[5.2, 1.2], start_time=2.0, contact_time=2.2, end_time=2.5),
            # Straight-line to mid right (x=4.8m, y=3.0m): straight, mid depth (not corner)
            ShotResult(shot_id="s4", player_position=[5.0, 10.0], target_position=[4.8, 3.0], start_time=3.0, contact_time=3.2, end_time=3.5)
        ]
        metrics_valid, findings_valid = engine.compute_shot_metrics(shots_valid, court_calibration=calib)

        assert metrics_valid.placement_metrics["available"] is True
        assert metrics_valid.placement_metrics["target_count"] == 4
        # 2 cross-court (50.0%), 2 straight-line (50.0%)
        assert metrics_valid.placement_metrics["cross_court_count"] == 2
        assert metrics_valid.placement_metrics["cross_court_pct"] == 50.0
        assert metrics_valid.placement_metrics["straight_line_count"] == 2
        assert metrics_valid.placement_metrics["straight_line_pct"] == 50.0
        # 2 corner targets (50.0%)
        assert metrics_valid.placement_metrics["corner_count"] == 2
        assert metrics_valid.placement_metrics["corner_pct"] == 50.0

        # Finding reflects exact numbers
        placement_finding = next(f for f in findings_valid if "placement" in f.lower())
        assert "50.0% cross-court" in placement_finding
        assert "50.0% straight-line" in placement_finding

    def test_player_movement_after_each_shot_recovery(self):
        """
        TASK 3 REQUIREMENT:
        For each shot with valid pre/post position data, compute recovery distance,
        recovery time, and movement direction.
        """
        engine = BadmintonMetricsEngine()
        calib = create_synthetic_calibration()

        # Shot at rear court (3.0m, 11.5m), recovers to base (3.0m, 9.5m)
        # Displacement = 2.0m forward to base in 0.4s
        shot = ShotResult(
            shot_id="shot_001",
            shot_type="clear",
            confidence=0.85,
            start_time=1.0,
            contact_time=1.3,
            end_time=1.7,
            player_position=[3.0, 11.5],
            evidence_frames=[10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
        )

        # Pose frames with recovery endpoint at frame 20 (x=3.0m, y=9.5m)
        pose_frames = []
        for i in range(25):
            lms = [Landmark(x=0.0, y=0.0, z=0.0, visibility=0.0) for _ in range(33)]
            # Map court meter (3.0m, 9.5m) to normalized coords
            lms[23] = Landmark(x=0.50, y=0.60, z=0.0, visibility=0.90)
            lms[24] = Landmark(x=0.52, y=0.60, z=0.0, visibility=0.90)
            pose_frames.append(PoseFrame(
                frame_index=i,
                timestamp_ms=int(round((i / 30.0) * 1000)),
                landmarks=lms,
                source_width=1280,
                source_height=720,
                is_detected=True,
                mean_confidence=0.90
            ))

        metrics, findings = engine.compute_shot_metrics(
            shots=[shot],
            pose_frames=pose_frames,
            court_calibration=calib
        )

        assert metrics.recovery_metrics["available"] is True
        records = metrics.recovery_metrics["per_shot_recoveries"]
        assert len(records) == 1
        rec = records[0]
        assert rec["shot_id"] == "shot_001"
        assert rec["recovery_time_s"] == 0.4
        assert rec["movement_direction"] in ["stationary_hold", "forward_to_base", "rearward_to_base", "lateral_left", "lateral_right"]

    def test_movement_efficiency_strictly_unavailable(self):
        """
        TASK 4 REQUIREMENT:
        Movement efficiency (successful_retrievals / total_movement_distance) must be reported
        as unavailable (NOT_RELIABLY_MEASURABLE) when rally outcome/boundary data cannot be determinable.
        Zero benchmark guessing.
        """
        engine = BadmintonMetricsEngine()
        shots = [ShotResult(shot_id="s1", start_time=0.0, contact_time=0.2, end_time=0.5)]

        metrics, _ = engine.compute_shot_metrics(shots, total_movement_distance_m=12.5)

        assert metrics.movement_efficiency.available is False
        assert metrics.movement_efficiency.value is None
        assert "NOT_RELIABLY_MEASURABLE" in metrics.movement_efficiency.unavailable_reason
        assert "Rally boundary" in metrics.movement_efficiency.unavailable_reason

    def test_real_video_metrics_traceability_to_shots_array(self):
        """
        DEFINITION OF DONE:
        Runs pipeline on real video (sample_toddler_walk.mp4) and confirms that:
        1. result.shot_metrics is generated from result.shots.
        2. Every count and percentage in shot_metrics is directly traceable to the shots[] array.
        3. Movement efficiency reports unavailable without fabricated numbers.
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

        # 1. Verify shot_metrics model is populated
        assert result.shot_metrics is not None
        sm = result.shot_metrics

        # 2. Verify 100% count traceability to result.shots
        assert sm.total_shots == len(result.shots)
        for stype, cnt in sm.count_by_shot_type.items():
            actual_count = sum(1 for s in result.shots if s.shot_type == stype)
            assert cnt == actual_count, f"Count mismatch for {stype}: {cnt} != {actual_count}"
            expected_pct = round((actual_count / max(1, len(result.shots))) * 100.0, 1)
            assert sm.percentage_by_shot_type[stype] == expected_pct

        # 3. Verify duration traceability
        if result.shots:
            actual_durations = [
                max(0.01, round(s.end_time - s.contact_time, 3))
                for s in result.shots if s.contact_time is not None
            ]
            assert sm.shot_durations_s == actual_durations
            if actual_durations:
                assert sm.average_duration_s == round(float(np.mean(actual_durations)), 3)

        # 4. Movement efficiency is honestly unavailable
        assert sm.movement_efficiency.available is False
        assert "NOT_RELIABLY_MEASURABLE" in sm.movement_efficiency.unavailable_reason
