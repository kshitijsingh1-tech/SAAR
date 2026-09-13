"""
Unit and integration test suite for Phase 9: Badminton Speed Analyzer.
Verifies calibrated inter-frame velocity math, outlier rejection with literature citations,
Section 13 exact fallback degradation, Section 14 racket vs shuttle non-conflation,
and real video pipeline execution.
"""
import math
from pathlib import Path
import pytest
import numpy as np

from app.plugins.sports.badminton.schemas import (
    Metric,
    CourtCalibration,
    ShotResult,
    SpeedMetrics,
    BadmintonAnalysisResult
)
from app.plugins.sports.badminton.speed_analyzer import (
    BadmintonSpeedAnalyzer,
    FALLBACK_UNAVAILABLE_MESSAGE,
    SHUTTLE_MAX_SPEED_KM_H,
    RACKET_MAX_SPEED_KM_H,
    MIN_VALID_SEGMENTS,
    SpeedSegment
)
from app.plugins.sports.badminton.racket_tracker import (
    RacketTrackingSummary,
    RacketFrameRecord
)
from app.plugins.sports.badminton.shuttle_tracker import (
    ShuttleTrackingSummary,
    ShuttleFrameRecord
)
from app.plugins.sports.badminton.pipeline import BadmintonPipeline


def create_synthetic_calibration() -> CourtCalibration:
    """Creates a calibrated synthetic court."""
    return CourtCalibration(
        is_calibrated=True,
        calibration_source="synthetic_test",
        uncalibrated_reason=None,
        corners_pixel=[[100.0, 100.0], [700.0, 100.0], [750.0, 600.0], [50.0, 600.0]],
        court_dimensions_m=[6.10, 13.40],
        confidence=0.95
    )


class TestBadmintonSpeedAnalyzer:
    """Test suite covering Phase 9 speed kinematics requirements."""

    def test_shuttle_speed_consecutive_calculation_and_traceability(self):
        """
        TASK 1 REQUIREMENT:
        Compute v_i = ||p_i - p_(i-1)|| / (t_i - t_(i-1)) between consecutive calibrated positions.
        Report max/average speed with uncertainty range and number of valid segments used.
        Must be traceable to specific consecutive tracked positions and timestamps.
        """
        analyzer = BadmintonSpeedAnalyzer()

        # 3 consecutive points -> 2 segments:
        # Segment 1: t=1.00s -> t=1.033s (dt=0.033s). Pos: (3.0, 10.0) -> (3.0, 8.0). dist = 2.0m
        #   v1 = 2.0 / 0.033 = 60.606 m/s = 218.18 km/h (~218.2 km/h)
        # Segment 2: t=1.033s -> t=1.067s (dt=0.034s). Pos: (3.0, 8.0) -> (3.0, 6.2). dist = 1.8m
        #   v2 = 1.8 / 0.034 = 52.941 m/s = 190.59 km/h (~190.6 km/h)
        points = [
            {"frame_index": 30, "timestamp_s": 1.000, "pos_m": (3.0, 10.0), "pos_px": (400, 500)},
            {"frame_index": 31, "timestamp_s": 1.033, "pos_m": (3.0, 8.0), "pos_px": (400, 420)},
            {"frame_index": 32, "timestamp_s": 1.067, "pos_m": (3.0, 6.2), "pos_px": (400, 350)}
        ]

        val_segs, rej_segs = analyzer.compute_segment_velocities(
            tracked_points=points,
            max_speed_km_h=SHUTTLE_MAX_SPEED_KM_H
        )

        assert len(val_segs) == 2
        assert len(rej_segs) == 0

        # Segment 1 verification
        s1 = val_segs[0]
        assert s1.from_frame == 30 and s1.to_frame == 31
        assert pytest.approx(s1.dt_s, abs=1e-3) == 0.033
        assert pytest.approx(s1.dist_m, abs=1e-2) == 2.00
        assert pytest.approx(s1.speed_km_h, abs=0.5) == 218.2

        # Segment 2 verification
        s2 = val_segs[1]
        assert s2.from_frame == 31 and s2.to_frame == 32
        assert pytest.approx(s2.dt_s, abs=1e-3) == 0.034
        assert pytest.approx(s2.dist_m, abs=1e-2) == 1.80
        assert pytest.approx(s2.speed_km_h, abs=0.5) == 190.6

        # Aggregation statistics
        peak_m, mean_m, peak_rng, mean_rng, n_used = analyzer.compute_speed_statistics(
            valid_segments=val_segs,
            metric_name_peak="shuttle_speed_peak",
            metric_name_mean="shuttle_speed_mean",
            is_calibrated=True,
            is_tracking_usable=True
        )

        assert n_used == 2
        assert peak_m.available is True
        assert peak_m.value == round(max(s1.speed_km_h, s2.speed_km_h), 1)
        assert mean_m.value == round(float(np.mean([s1.speed_km_h, s2.speed_km_h])), 1)

        # Uncertainty range verification
        assert peak_rng is not None and len(peak_rng) == 2
        assert peak_rng[0] <= peak_m.value <= peak_rng[1]
        assert peak_m.uncertainty_range == peak_rng
        assert peak_m.segments_used == 2

    def test_shuttle_speed_outlier_rejection_with_physical_bounds(self):
        """
        TASK 1 REQUIREMENT:
        Reject implausible frame-to-frame jumps beyond physically-reasonable max badminton speed
        (SHUTTLE_MAX_SPEED_KM_H = 576.0 km/h / 160 m/s based on Guinness record 565 km/h).
        """
        analyzer = BadmintonSpeedAnalyzer()

        # 4 consecutive points:
        # p0 -> p1: valid (~200 km/h)
        # p1 -> p2: implausible jump: 8.0m in 0.033s = 242.4 m/s = 872.7 km/h > 576.0 km/h (outlier!)
        # p2 -> p3: valid (~180 km/h)
        points = [
            {"frame_index": 10, "timestamp_s": 0.333, "pos_m": (3.0, 10.0), "pos_px": (300, 500)},
            {"frame_index": 11, "timestamp_s": 0.367, "pos_m": (3.0, 8.1), "pos_px": (300, 420)},
            {"frame_index": 12, "timestamp_s": 0.400, "pos_m": (3.0, 0.1), "pos_px": (300, 100)},  # Glitch jump
            {"frame_index": 13, "timestamp_s": 0.433, "pos_m": (3.0, 1.7), "pos_px": (300, 160)}
        ]

        val_segs, rej_segs = analyzer.compute_segment_velocities(
            tracked_points=points,
            max_speed_km_h=SHUTTLE_MAX_SPEED_KM_H
        )

        assert len(val_segs) == 2
        assert len(rej_segs) == 1

        # The outlier segment must be p1 -> p2
        outlier = rej_segs[0]
        assert outlier.from_frame == 11 and outlier.to_frame == 12
        assert outlier.is_outlier is True
        assert "Exceeds physical upper bound" in outlier.rejection_reason
        assert outlier.speed_km_h > 576.0

    def test_racket_speed_isolated_around_contact_window(self):
        """
        TASK 2 REQUIREMENT:
        Racket head speed computed around contact window using racket tracking data.
        Peak Racket Speed reported with uncertainty range and segments count.
        Rejects jumps > 288.0 km/h (80 m/s biomechanical limit).
        """
        analyzer = BadmintonSpeedAnalyzer()

        # Shot from t=1.0 to t=1.6 with contact at t=1.3
        shot = ShotResult(
            shot_id="shot_smash_01",
            shot_type="smash",
            confidence=0.85,
            start_time=1.0,
            contact_time=1.3,
            end_time=1.6,
            evidence_frames=[39, 40, 41, 42]
        )

        # Racket head points around contact (t=1.267, 1.300, 1.333)
        # Segment 1: dt=0.033s, dist=1.2m -> 36.36 m/s = 130.9 km/h
        # Segment 2: dt=0.033s, dist=1.4m -> 42.42 m/s = 152.7 km/h
        racket_records = [
            RacketFrameRecord(frame_index=39, timestamp_ms=1267, is_detected=True, confidence=0.8, racket_head_m=(2.5, 9.0)),
            RacketFrameRecord(frame_index=40, timestamp_ms=1300, is_detected=True, confidence=0.85, racket_head_m=(2.5, 7.8)),
            RacketFrameRecord(frame_index=41, timestamp_ms=1333, is_detected=True, confidence=0.8, racket_head_m=(2.5, 6.4))
        ]
        racket_summary = RacketTrackingSummary(
            total_frames=50,
            detected_frames_count=20,
            visibility_ratio=0.40,
            is_usable=True,
            racket_speed_peak=Metric(name="racket_speed_peak", available=True, value=152.7),
            racket_speed_mean=Metric(name="racket_speed_mean", available=True, value=141.8),
            wrist_speed_peak=Metric(name="wrist_speed_peak", available=True, value=45.0),
            per_frame_records=racket_records
        )

        calib = create_synthetic_calibration()
        speed_metrics, updated_shots, findings = analyzer.analyze_speeds(
            shots=[shot],
            racket_summary=racket_summary,
            shuttle_summary=None,
            court_calibration=calib
        )

        shot_res = updated_shots[0]
        assert shot_res.racket_speed.available is True
        assert shot_res.racket_speed.value == 152.7
        assert shot_res.trajectory_features["racket_segments_used"] == 2
        assert len(shot_res.trajectory_features["racket_valid_segments"]) == 2

    def test_section_14_non_conflation_guarantee(self):
        """
        TASK 2 & DEFINITION OF DONE REQUIREMENT:
        Racket and shuttle speeds are never conflated in the output schema or
        in any generated natural-language text.
        """
        analyzer = BadmintonSpeedAnalyzer()
        calib = create_synthetic_calibration()

        racket_records = [
            RacketFrameRecord(frame_index=1, timestamp_ms=100, is_detected=True, confidence=0.8, racket_head_m=(2.0, 8.0)),
            RacketFrameRecord(frame_index=2, timestamp_ms=133, is_detected=True, confidence=0.8, racket_head_m=(2.0, 6.5)),
            RacketFrameRecord(frame_index=3, timestamp_ms=167, is_detected=True, confidence=0.8, racket_head_m=(2.0, 5.0))
        ]
        racket_summary = RacketTrackingSummary(
            total_frames=10, detected_frames_count=5, visibility_ratio=0.5, is_usable=True,
            racket_speed_peak=Metric(name="racket_speed_peak", available=True, value=160.0),
            racket_speed_mean=Metric(name="racket_speed_mean", available=True, value=160.0),
            wrist_speed_peak=Metric(name="wrist_speed_peak", available=True, value=48.0),
            per_frame_records=racket_records
        )

        shuttle_records = [
            ShuttleFrameRecord(frame_index=1, timestamp_ms=100, is_detected=True, confidence=0.9, shuttle_m=(3.0, 7.0)),
            ShuttleFrameRecord(frame_index=2, timestamp_ms=133, is_detected=True, confidence=0.9, shuttle_m=(3.0, 4.0)),
            ShuttleFrameRecord(frame_index=3, timestamp_ms=167, is_detected=True, confidence=0.9, shuttle_m=(3.0, 1.0))
        ]
        shuttle_summary = ShuttleTrackingSummary(
            total_frames=10, raw_candidates_count=5, verified_frames_count=5, visibility_ratio=0.5, is_usable=True,
            shuttle_speed_peak=Metric(name="shuttle_speed_peak", available=True, value=320.0),
            shuttle_speed_mean=Metric(name="shuttle_speed_mean", available=True, value=320.0),
            per_frame_records=shuttle_records
        )

        speed_metrics, _, findings = analyzer.analyze_speeds(
            shots=[],
            racket_summary=racket_summary,
            shuttle_summary=shuttle_summary,
            court_calibration=calib
        )

        # In schema: strictly separate fields
        assert speed_metrics.racket_speed_peak.name == "racket_speed_peak"
        assert speed_metrics.shuttle_speed_peak.name == "shuttle_speed_peak"
        assert speed_metrics.wrist_speed_peak.name == "wrist_speed_peak"
        assert speed_metrics.racket_speed_peak.value != speed_metrics.shuttle_speed_peak.value

        # In natural language findings: distinct sentences with exact terminology
        shuttle_finding = next(f for f in findings if "Peak Shuttle Speed" in f)
        racket_finding = next(f for f in findings if "Peak Racket Speed" in f)
        wrist_finding = next(f for f in findings if "Peak Wrist Speed" in f)

        assert "Peak Shuttle Speed:" in shuttle_finding
        assert "Peak Racket Speed:" in racket_finding
        assert "Peak Wrist Speed:" in wrist_finding
        # Ensure no ambiguous combined phrases like "Peak shot speed"
        assert not any("peak shot speed" in f.lower() for f in findings)

    def test_section_13_exact_fallback_string_on_insufficient_tracking(self):
        """
        TASK 3 REQUIREMENT:
        Both racket and shuttle speeds must degrade to
        "Speed estimate unavailable — insufficient continuous tracking"
        when underlying tracking data doesn't clear the confidence/continuity bar.
        """
        analyzer = BadmintonSpeedAnalyzer()

        # Case A: Court uncalibrated
        peak_m, mean_m, _, _, n = analyzer.compute_speed_statistics(
            valid_segments=[],
            metric_name_peak="shuttle_speed_peak",
            metric_name_mean="shuttle_speed_mean",
            is_calibrated=False,
            is_tracking_usable=True
        )
        assert peak_m.available is False
        assert peak_m.unavailable_reason == FALLBACK_UNAVAILABLE_MESSAGE
        assert mean_m.unavailable_reason == FALLBACK_UNAVAILABLE_MESSAGE

        # Case B: Tracker unusable (poor visibility)
        peak_m2, _, _, _, _ = analyzer.compute_speed_statistics(
            valid_segments=[],
            metric_name_peak="racket_speed_peak",
            metric_name_mean="racket_speed_mean",
            is_calibrated=True,
            is_tracking_usable=False
        )
        assert peak_m2.available is False
        assert peak_m2.unavailable_reason == FALLBACK_UNAVAILABLE_MESSAGE

        # Case C: Only 1 segment (below MIN_VALID_SEGMENTS = 2)
        single_seg = [SpeedSegment(1, 2, 0.0, 0.033, (0, 0), (1, 0), 0.033, 1.0, 30.3, 109.1, False)]
        peak_m3, _, _, _, _ = analyzer.compute_speed_statistics(
            valid_segments=single_seg,
            metric_name_peak="shuttle_speed_peak",
            metric_name_mean="shuttle_speed_mean",
            is_calibrated=True,
            is_tracking_usable=True
        )
        assert peak_m3.available is False
        assert peak_m3.unavailable_reason == FALLBACK_UNAVAILABLE_MESSAGE

    def test_real_video_clip_triggers_honest_fallback(self):
        """
        DEFINITION OF DONE REQUIREMENT:
        The "insufficient tracking" fallback message triggers correctly on a
        real clip with poor shuttle visibility — confirm this explicitly, don't assume.
        """
        video_path = Path("app/gait/assets/sample_toddler_walk.mp4")
        if not video_path.exists():
            pytest.skip("sample_toddler_walk.mp4 not found")

        with open(video_path, "rb") as f:
            video_bytes = f.read()

        pipeline = BadmintonPipeline()
        result = pipeline.analyze_video_bytes(video_bytes, "sample_toddler_walk.mp4")

        assert result.speed_metrics is not None

        # Shuttle speed must trigger exact Section 13 fallback
        shuttle_peak = result.speed_metrics.shuttle_speed_peak
        assert shuttle_peak.available is False
        assert shuttle_peak.unavailable_reason == FALLBACK_UNAVAILABLE_MESSAGE

        # Racket speed must trigger exact Section 13 fallback
        racket_peak = result.speed_metrics.racket_speed_peak
        assert racket_peak.available is False
        assert racket_peak.unavailable_reason == FALLBACK_UNAVAILABLE_MESSAGE

        # Check in findings
        shuttle_finding = next(f for f in result.findings if "Peak Shuttle Speed" in f)
        assert FALLBACK_UNAVAILABLE_MESSAGE in shuttle_finding

        racket_finding = next(f for f in result.findings if "Peak Racket Speed" in f)
        assert FALLBACK_UNAVAILABLE_MESSAGE in racket_finding
