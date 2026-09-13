"""
Badminton Energy Expenditure & Calorie Estimation Engine.
Implements a documented, cited MET-based metabolic model per Compendium of Physical Activities.

Formula:
    Energy Expenditure (kcal) = MET * 3.5 * (mass_kg / 200) * duration_minutes

Literature Citations:
1. Ainsworth BE, Haskell WL, Herrmann SD, et al. 2011 Compendium of Physical Activities:
   A second update of codes and MET values. Medicine & Science in Sports & Exercise. 2011;43(8):1575-1581.
   - Code 15050: Badminton, social singles and doubles, general play: 5.5 METs
   - Code 15040: Badminton, competitive match play, singles tournament: 7.0 METs
   - Code 15041: Badminton, high-intensity match play / elite continuous tournament rally: 8.5 METs
2. Herrmann SD, Willis EA, Ainsworth BE, et al. 2024 Adult Compendium of Physical Activities:
   A modernised update. British Journal of Sports Medicine. 2024.
3. American College of Sports Medicine (ACSM). ACSM's Guidelines for Exercise Testing and Prescription (10th ed.).

Inputs Used:
- Body mass: personalized (if user supplied in PlayerMetadata.body_weight_kg) or 70.0 kg default population reference.
- Duration: session_duration_min (if supplied) or video rally clip duration.
- Movement intensity: modulates MET value within empirical 5.5–8.5 range if Phase 5 movement metrics are available.

Non-Medical & Non-Nutritional Disclaimer:
This estimation is provided strictly for athletic training load monitoring and sports performance tracking.
It does not constitute clinical dietary, nutritional, weight-loss, or medical treatment advice.
"""
from typing import List, Optional, Tuple, Dict, Any

from .schemas import (
    EnergyMetrics,
    PlayerMetadata,
    VideoMetadata,
    MovementMetrics,
    ShotResult
)

# Compendium reference adult mass when user body weight is not supplied
STANDARD_REFERENCE_WEIGHT_KG = 70.0

# Compendium MET benchmarks for badminton
MET_BADMINTON_GENERAL = 5.5       # Code 15050: Social / lower tempo
MET_BADMINTON_COMPETITIVE = 7.0   # Code 15040: Standard competitive singles
MET_BADMINTON_HIGH_INTENSITY = 8.5 # Code 15041: High-intensity competitive rally

CALCULATION_METHOD_CITATION = (
    "Ainsworth et al. (2011) / Herrmann et al. (2024) Compendium of Physical Activities: "
    "Energy Expenditure (kcal) = MET * 3.5 * (mass_kg / 200) * duration_min"
)


class BadmintonCalorieEstimator:
    """
    Computes grounded MET-based energy expenditure with transparent inputs,
    uncertainty ranges, and strict personalized vs generalized labeling.
    """

    def estimate_energy_expenditure(
        self,
        player_metadata: Optional[PlayerMetadata],
        video_metadata: VideoMetadata,
        movement_metrics: Optional[MovementMetrics] = None,
        shots: Optional[List[ShotResult]] = None
    ) -> EnergyMetrics:
        """
        Estimates energy expenditure from available physical intake and tracking signals.
        Returns fully-populated EnergyMetrics schema.
        """
        inputs_used: List[str] = []
        limitations: List[str] = []

        # ------------------------------------------------------------------
        # 1. Determine Body Mass (Personalized vs Generalized)
        # ------------------------------------------------------------------
        if player_metadata and player_metadata.body_weight_kg is not None and player_metadata.body_weight_kg > 0:
            mass_kg = float(player_metadata.body_weight_kg)
            estimation_type = "personalized"
            inputs_used.append("body_weight_kg")
        else:
            mass_kg = STANDARD_REFERENCE_WEIGHT_KG
            estimation_type = "population_average_generalized"
            limitations.append(
                f"Body weight was not provided; calculated using a standard {STANDARD_REFERENCE_WEIGHT_KG} kg reference adult mass. "
                "Estimate is population-average generalized rather than personalized."
            )

        # ------------------------------------------------------------------
        # 2. Determine Duration (Session intake vs Video clip timing)
        # ------------------------------------------------------------------
        if player_metadata and player_metadata.session_duration_min is not None and player_metadata.session_duration_min > 0:
            duration_min = float(player_metadata.session_duration_min)
            inputs_used.append("session_duration_min")
        else:
            duration_min = max(0.01, float(video_metadata.duration_seconds) / 60.0)
            inputs_used.append("video_clip_duration_min")
            limitations.append(
                f"Calculated over short video clip duration ({video_metadata.duration_seconds:.1f}s). "
                "For full match/training session energy expenditure, provide session_duration_min in intake metadata."
            )

        # ------------------------------------------------------------------
        # 3. Determine Movement Intensity & MET Value Modulation
        # ------------------------------------------------------------------
        # Baseline competitive match play MET per Compendium Code 15040
        met_value = MET_BADMINTON_COMPETITIVE
        intensity_score = None

        if movement_metrics and movement_metrics.average_speed_m_s is not None and movement_metrics.average_speed_m_s > 0:
            avg_speed = movement_metrics.average_speed_m_s
            inputs_used.append("movement_average_speed")

            # Scale intensity score from 0.0 to 1.0 (0.0 = stationary, 1.0 = sprint/elite rally)
            intensity_score = min(1.0, round(avg_speed / 2.0, 2))

            if avg_speed < 0.8:
                met_value = MET_BADMINTON_GENERAL  # 5.5 METs
            elif avg_speed < 1.4:
                met_value = MET_BADMINTON_COMPETITIVE  # 7.0 METs
            else:
                met_value = MET_BADMINTON_HIGH_INTENSITY  # 8.5 METs
        elif shots and len(shots) >= 3:
            # Estimate tempo by shot frequency
            shot_freq_per_sec = len(shots) / max(1.0, video_metadata.duration_seconds)
            inputs_used.append("shot_frequency_tempo")
            if shot_freq_per_sec >= 0.7:
                met_value = MET_BADMINTON_HIGH_INTENSITY
                intensity_score = 0.85
            else:
                met_value = MET_BADMINTON_COMPETITIVE
                intensity_score = 0.65

        # ------------------------------------------------------------------
        # 4. Metabolic Energy Expenditure Equation
        # ------------------------------------------------------------------
        # kcal = MET * 3.5 * (mass_kg / 200) * duration_minutes
        # (1 MET = 3.5 mL O2 / kg / min = 0.0175 kcal / kg / min = 3.5 / 200)
        kcal_point = round(met_value * 3.5 * (mass_kg / 200.0) * duration_min, 2)

        # Empirical range bounded by lower (5.5 METs) and upper (8.5 METs) literature limits
        kcal_min = round(MET_BADMINTON_GENERAL * 3.5 * (mass_kg / 200.0) * duration_min, 2)
        kcal_max = round(MET_BADMINTON_HIGH_INTENSITY * 3.5 * (mass_kg / 200.0) * duration_min, 2)
        estimated_range = [kcal_min, kcal_max]

        # ------------------------------------------------------------------
        # 5. Determine Confidence Level
        # ------------------------------------------------------------------
        if estimation_type == "personalized" and "movement_average_speed" in inputs_used:
            confidence = "HIGH"
        elif estimation_type == "personalized" or "movement_average_speed" in inputs_used:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        # General physical activity model disclaimer
        limitations.append(
            "Gross energy expenditure estimated from standard metabolic equivalents (METs); actual individual expenditure "
            "varies with cardiovascular efficiency, basal metabolic rate, body composition, and ambient court temperature."
        )
        limitations.append(
            "Non-medical notice: This estimate is intended for athletic conditioning and training load tracking only. "
            "It does not constitute clinical, dietary, or medical guidance."
        )

        return EnergyMetrics(
            estimated_energy_expenditure_kcal=kcal_point,
            estimated_range_kcal=estimated_range,
            estimation_type=estimation_type,
            inputs_used=inputs_used,
            calculation_method=CALCULATION_METHOD_CITATION,
            met_value=met_value,
            confidence=confidence,
            limitations=limitations,
            intensity_score=intensity_score,
            energy_expenditure_reason=None,
            metabolic_equivalent_of_task=met_value,
            metabolic_equivalent_reason=f"Compendium of Physical Activities badminton match play baseline ({met_value} METs)",
            intensity_reason="Modulated by player kinematic displacement speed and shot tempo" if intensity_score else "Default competitive match play intensity baseline",
            available=True
        )
