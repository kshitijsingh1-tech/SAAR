"""
Unit and integration test suite for Phase 10: Energy Expenditure & Calorie Estimation.
Verifies MET-based calculation formula, literature citations, personalized vs generalized labeling,
transparent inputs_used list, and non-medical claim compliance.
"""
from pathlib import Path
import pytest

from app.plugins.sports.badminton.schemas import (
    PlayerMetadata,
    VideoMetadata,
    MovementMetrics,
    EnergyMetrics
)
from app.plugins.sports.badminton.calorie_estimator import (
    BadmintonCalorieEstimator,
    STANDARD_REFERENCE_WEIGHT_KG,
    CALCULATION_METHOD_CITATION,
    MET_BADMINTON_GENERAL,
    MET_BADMINTON_COMPETITIVE,
    MET_BADMINTON_HIGH_INTENSITY
)
from app.plugins.sports.badminton.pipeline import BadmintonPipeline


def create_sample_video_meta(duration_sec: float = 60.0) -> VideoMetadata:
    return VideoMetadata(
        filename="test_match.mp4",
        duration_seconds=duration_sec,
        fps=30.0,
        total_frames=int(duration_sec * 30),
        frames_processed=int(duration_sec * 30),
        width=1280,
        height=720
    )


class TestBadmintonCalorieEstimator:
    """Test suite covering Phase 10 calorie and metabolic estimation requirements."""

    def test_formula_and_citation_documentation(self):
        """
        TASK 1 REQUIREMENT:
        Documented, cited MET-based energy expenditure equation.
        Must cite Compendium of Physical Activities and exist in badminton_kb.md.
        """
        assert "Ainsworth et al." in CALCULATION_METHOD_CITATION
        assert "Compendium of Physical Activities" in CALCULATION_METHOD_CITATION
        assert "MET * 3.5 * (mass_kg / 200) * duration_min" in CALCULATION_METHOD_CITATION

        # Verify badminton_kb.md exists in app/knowledge and contains citations
        kb_path = Path("app/knowledge/badminton_kb.md")
        assert kb_path.exists(), "badminton_kb.md must exist in app/knowledge/"
        kb_text = kb_path.read_text(encoding="utf-8")
        assert "15040" in kb_text
        assert "7.0 METs" in kb_text
        assert "Ainsworth" in kb_text

    def test_personalized_estimation_when_body_weight_supplied(self):
        """
        TASK 2 & 3 REQUIREMENT:
        When body mass is supplied by the user, the estimate MUST be labeled "personalized",
        inputs_used must include body_weight_kg, and exact formula must be applied.
        """
        estimator = BadmintonCalorieEstimator()
        player_meta = PlayerMetadata(
            body_weight_kg=65.0,
            session_duration_min=45.0
        )
        video_meta = create_sample_video_meta(duration_sec=30.0)

        res = estimator.estimate_energy_expenditure(
            player_metadata=player_meta,
            video_metadata=video_meta
        )

        assert res.estimation_type == "personalized"
        assert "body_weight_kg" in res.inputs_used
        assert "session_duration_min" in res.inputs_used
        assert "video_clip_duration_min" not in res.inputs_used

        # Formula check: kcal = MET * 3.5 * (mass / 200) * duration_min
        # Default MET = 7.0 (competitive singles)
        # kcal = 7.0 * 3.5 * (65.0 / 200) * 45.0 = 358.3125 -> 358.31
        expected_kcal = round(7.0 * 3.5 * (65.0 / 200.0) * 45.0, 2)
        assert res.estimated_energy_expenditure_kcal == expected_kcal

        # Range check: [5.5 METs, 8.5 METs]
        expected_min = round(5.5 * 3.5 * (65.0 / 200.0) * 45.0, 2)
        expected_max = round(8.5 * 3.5 * (65.0 / 200.0) * 45.0, 2)
        assert res.estimated_range_kcal == [expected_min, expected_max]

    def test_generalized_estimation_when_body_weight_omitted(self):
        """
        TASK 3 REQUIREMENT:
        If body weight is unavailable, the estimate MUST be clearly labeled
        "population_average_generalized" rather than personalized in the API response.
        inputs_used must accurately omit body_weight_kg.
        """
        estimator = BadmintonCalorieEstimator()
        # No body weight provided
        player_meta = PlayerMetadata(
            session_duration_min=30.0
        )
        video_meta = create_sample_video_meta(duration_sec=20.0)

        res = estimator.estimate_energy_expenditure(
            player_metadata=player_meta,
            video_metadata=video_meta
        )

        assert res.estimation_type == "population_average_generalized"
        assert "body_weight_kg" not in res.inputs_used
        assert "session_duration_min" in res.inputs_used

        # Check reference weight calculation (70.0 kg default)
        expected_kcal = round(7.0 * 3.5 * (STANDARD_REFERENCE_WEIGHT_KG / 200.0) * 30.0, 2)
        assert res.estimated_energy_expenditure_kcal == expected_kcal

        # Check limitation transparency
        assert any("70.0 kg reference adult mass" in lim for lim in res.limitations)
        assert any("population-average generalized rather than personalized" in lim for lim in res.limitations)

    def test_movement_intensity_modulates_met_value(self):
        """
        TASK 2 REQUIREMENT:
        Movement intensity derived from real movement metrics (Phase 5) modulates MET.
        """
        estimator = BadmintonCalorieEstimator()
        player_meta = PlayerMetadata(body_weight_kg=75.0, session_duration_min=60.0)
        video_meta = create_sample_video_meta(duration_sec=60.0)

        # High tempo (speed >= 1.4 m/s -> 8.5 METs)
        mov_high = MovementMetrics(average_speed_m_s=1.55)
        res_high = estimator.estimate_energy_expenditure(
            player_metadata=player_meta,
            video_metadata=video_meta,
            movement_metrics=mov_high
        )
        assert res_high.met_value == MET_BADMINTON_HIGH_INTENSITY
        assert "movement_average_speed" in res_high.inputs_used

        # Low tempo (speed < 0.8 m/s -> 5.5 METs)
        mov_low = MovementMetrics(average_speed_m_s=0.60)
        res_low = estimator.estimate_energy_expenditure(
            player_metadata=player_meta,
            video_metadata=video_meta,
            movement_metrics=mov_low
        )
        assert res_low.met_value == MET_BADMINTON_GENERAL

    def test_no_medical_or_nutritional_treatment_claims(self):
        """
        TASK 5 REQUIREMENT:
        No medical/nutritional treatment claims anywhere in output.
        """
        estimator = BadmintonCalorieEstimator()
        res = estimator.estimate_energy_expenditure(
            player_metadata=PlayerMetadata(),
            video_metadata=create_sample_video_meta(10.0)
        )

        all_text = " ".join(res.limitations) + " " + (res.energy_expenditure_reason or "") + " " + res.calculation_method
        forbidden_terms = [
            "prescribed", "prescription", "cure", "treatment for obesity",
            "diet plan", "nutritional requirement", "weight loss guaranteed", "clinical diagnosis"
        ]
        for term in forbidden_terms:
            assert term not in all_text.lower()

        # Non-medical notice must be explicitly affirmed in limitations
        assert any("Non-medical notice" in lim for lim in res.limitations)

    def test_pipeline_end_to_end_real_video(self):
        """
        DEFINITION OF DONE REQUIREMENT:
        Verify end-to-end integration on a real video clip.
        """
        candidate_paths = [
            Path("../Prompt_Photorealistic_p_.mp4"),
            Path("Prompt_Photorealistic_p_.mp4"),
            Path("app/gait/assets/sample_toddler_walk.mp4")
        ]
        video_path = next((p for p in candidate_paths if p.exists()), None)
        if not video_path:
            pytest.skip("Test video not found")

        pipeline = BadmintonPipeline()
        result = pipeline.analyze_video_bytes(
            video_bytes=video_path.read_bytes(),
            filename=video_path.name
        )

        assert result.energy_metrics is not None
        assert result.energy_metrics.available is True
        assert result.energy_metrics.estimated_energy_expenditure_kcal is not None
        assert result.energy_metrics.estimation_type == "population_average_generalized"
        assert len(result.energy_metrics.inputs_used) > 0

        # Finding appears in result.findings
        energy_finding = next((f for f in result.findings if "Energy expenditure" in f), None)
        assert energy_finding is not None
        assert "Population-average generalized" in energy_finding
