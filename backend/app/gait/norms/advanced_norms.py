"""
Pediatric gait kinematic reference norms and age-bracketed comparison engine.

Integrates:
1. Real healthy pediatric reference dataset (Ages 14–54 months) from published clinical literature:
   - Sutherland DH, Olshen R, Cooper L, Woo SL. The Development of Mature Walking (1988).
   - Published healthy toddler cohort studies (N=14 at 24–29m, N=8 at 30–35m, N=16 at 36–41m, N=13 at 42–47m, N=15 at 48–54m).
2. 2D kinematic joint angle & posture reference boundaries (Perry & Burnfield, Rygelova et al.).
"""
from typing import Dict, Any, Optional, List
from ..schemas import ReferenceMetricItem
from .pediatric_reference_dataset import (
    PEDIATRIC_REFERENCE_DATASET,
    get_reference_for_age,
    compare_metric
)
from .toddler_norms import get_cadence_range


def get_joint_rom_norms(age_months: int) -> Dict[str, Dict[str, Any]]:
    """
    Returns age-appropriate Range of Motion (ROM) normative boundaries in degrees.
    """
    if age_months < 24:
        return {
            "hip_rom": {"low": 35.0, "high": 55.0, "source": "Sutherland (Toddler ~1-2y)"},
            "knee_rom": {"low": 50.0, "high": 68.0, "source": "Sutherland / Perry (Toddler)"},
            "ankle_rom": {"low": 20.0, "high": 38.0, "source": "Sutherland (Toddler)"},
            "trunk_angle": {"low": 2.0, "high": 12.0, "source": "Pediatric Trunk Posture Norms"},
            "asymmetry_pct": {"low": 0.0, "high": 10.0, "source": "Symmetry Norms (<10% typical)"}
        }
    elif age_months < 48:
        return {
            "hip_rom": {"low": 38.0, "high": 52.0, "source": "Sutherland (Preschool ~2-4y)"},
            "knee_rom": {"low": 52.0, "high": 65.0, "source": "Sutherland / Perry (Preschool)"},
            "ankle_rom": {"low": 22.0, "high": 35.0, "source": "Sutherland (Preschool)"},
            "trunk_angle": {"low": 1.0, "high": 9.0, "source": "Pediatric Trunk Posture Norms"},
            "asymmetry_pct": {"low": 0.0, "high": 8.0, "source": "Symmetry Norms (<8% typical)"}
        }
    else:
        return {
            "hip_rom": {"low": 40.0, "high": 50.0, "source": "Sutherland (Mature ~4y+)"},
            "knee_rom": {"low": 55.0, "high": 65.0, "source": "Sutherland / Perry (Mature)"},
            "ankle_rom": {"low": 25.0, "high": 35.0, "source": "Sutherland (Mature)"},
            "trunk_angle": {"low": 1.0, "high": 7.0, "source": "Mature Trunk Posture Norms"},
            "asymmetry_pct": {"low": 0.0, "high": 6.0, "source": "Symmetry Norms (<6% typical)"}
        }


def evaluate_kinematic_reference(
    metric_id: str,
    display_name: str,
    measured_val: Optional[float],
    unit: str,
    ref_low: Optional[float],
    ref_high: Optional[float],
    source: str,
    confidence_score: float = 0.8
) -> ReferenceMetricItem:
    """Evaluates joint kinematics or posture against reference bands."""
    conf_label = "high" if confidence_score >= 0.7 else ("medium" if confidence_score >= 0.4 else "low")

    
    if measured_val is None:
        return ReferenceMetricItem(
            metric_id=metric_id,
            display_name=display_name,
            measured=None,
            measured_value=None,
            reference_mean=None,
            reference_sd=None,
            difference_from_mean=None,
            z_score=None,
            unit=unit,
            reference_range_str=f"{ref_low} – {ref_high} {unit}" if (ref_low and ref_high) else "N/A",
            ref_low=ref_low,
            ref_high=ref_high,
            status="insufficient_data",
            deviation=None,
            confidence="low",
            source=source,
            clinical_note="Measurement not available from video recording."
        )

    if ref_low is not None and ref_high is not None:
        range_str = f"{ref_low} – {ref_high} {unit}"
        ref_mean = round((ref_low + ref_high) / 2.0, 1)
        if measured_val < ref_low:
            status = "below_reference"
            deviation = round(measured_val - ref_low, 1)
            note = f"Observed {measured_val:.1f}{unit} is below reference floor ({ref_low}{unit})."
        elif measured_val > ref_high:
            status = "above_reference"
            deviation = round(measured_val - ref_high, 1)
            note = f"Observed {measured_val:.1f}{unit} is above reference ceiling ({ref_high}{unit})."
        else:
            status = "within_reference"
            deviation = 0.0
            note = f"Observed {measured_val:.1f}{unit} is within reference interval ({range_str})."
        diff_from_mean = round(measured_val - ref_mean, 1)
    else:
        range_str = "Reference not established for 2D video"
        ref_mean = None
        status = "within_reference"
        deviation = None
        diff_from_mean = None
        note = f"Measured value: {measured_val:.1f}{unit} — reference not established for this measurement setup."
        source = "2D Video Landmark Kinematics"

    return ReferenceMetricItem(
        metric_id=metric_id,
        display_name=display_name,
        measured=measured_val,
        measured_value=measured_val,
        reference_mean=ref_mean,
        reference_sd=None,
        difference_from_mean=diff_from_mean,
        z_score=None,
        unit=unit,
        reference_range_str=range_str,
        ref_low=ref_low,
        ref_high=ref_high,
        status=status,
        deviation=deviation,
        confidence=conf_label,
        source=source,
        clinical_note=note
    )



def generate_reference_comparisons(
    child_age_months: int,
    cadence: float,
    mean_step_time: float,
    step_asymmetry: float,
    knee_rom_median: Optional[float],
    hip_rom_median: Optional[float],
    ankle_rom_median: Optional[float],
    trunk_angle_mean: Optional[float],
    pipeline_conf: float,
    adv_temporal: Optional[Any] = None,
    spatial_metrics: Optional[Any] = None
) -> List[ReferenceMetricItem]:
    """
    Synthesizes the complete structured reference comparison profile comparing
    the child's measured values directly against the real published pediatric reference norms.
    """
    items: List[ReferenceMetricItem] = []

    # --------------------------------------------------------------------------
    # 1. Cadence (steps/min)
    # --------------------------------------------------------------------------
    meas_cad = round(cadence, 1) if cadence > 0 else None
    items.append(compare_metric("cadence", meas_cad, child_age_months, pipeline_conf))

    # --------------------------------------------------------------------------
    # 2. Step Time (s)
    # --------------------------------------------------------------------------
    meas_st = round(mean_step_time, 3) if mean_step_time > 0 else None
    items.append(compare_metric("step_time", meas_st, child_age_months, pipeline_conf))

    # --------------------------------------------------------------------------
    # 3. Stance Time (s)
    # --------------------------------------------------------------------------
    meas_stance = None
    if adv_temporal and adv_temporal.stance_time is not None and adv_temporal.stance_time > 0:
        meas_stance = round(adv_temporal.stance_time, 3)
    items.append(compare_metric("stance_time", meas_stance, child_age_months, pipeline_conf))

    # --------------------------------------------------------------------------
    # 4. Single-Support Time (s)
    # --------------------------------------------------------------------------
    meas_single_support = None
    if adv_temporal and adv_temporal.swing_time is not None and adv_temporal.swing_time > 0:
        # Single-limb support time on contralateral limb corresponds to swing time
        meas_single_support = round(adv_temporal.swing_time, 3)
    items.append(compare_metric("single_support_time", meas_single_support, child_age_months, pipeline_conf))

    # --------------------------------------------------------------------------
    # 5. Double-Support Time (s)
    # --------------------------------------------------------------------------
    meas_double_support = None
    if adv_temporal and adv_temporal.double_support_time is not None and adv_temporal.double_support_time > 0:
        meas_double_support = round(adv_temporal.double_support_time, 3)
    items.append(compare_metric("double_support_time", meas_double_support, child_age_months, pipeline_conf))

    # (Spatial parameters step_length, stride_length, walking_velocity are excluded from scope)

    # --------------------------------------------------------------------------
    # Joint Kinematics & Posture (Perry / Sutherland)
    # --------------------------------------------------------------------------
    rom_norms = get_joint_rom_norms(child_age_months)

    # Knee ROM
    k_norm = rom_norms["knee_rom"]
    items.append(evaluate_kinematic_reference(
        metric_id="knee_rom",
        display_name="Knee Range of Motion",
        measured_val=knee_rom_median,
        unit="°",
        ref_low=k_norm["low"],
        ref_high=k_norm["high"],
        source=k_norm["source"],
        confidence_score=pipeline_conf
    ))

    # Hip ROM
    h_norm = rom_norms["hip_rom"]
    items.append(evaluate_kinematic_reference(
        metric_id="hip_rom",
        display_name="Hip Range of Motion",
        measured_val=hip_rom_median,
        unit="°",
        ref_low=h_norm["low"],
        ref_high=h_norm["high"],
        source=h_norm["source"],
        confidence_score=pipeline_conf
    ))

    # Ankle ROM
    a_norm = rom_norms["ankle_rom"]
    items.append(evaluate_kinematic_reference(
        metric_id="ankle_rom",
        display_name="Ankle Range of Motion",
        measured_val=ankle_rom_median,
        unit="°",
        ref_low=a_norm["low"],
        ref_high=a_norm["high"],
        source=a_norm["source"],
        confidence_score=pipeline_conf
    ))

    # Trunk Inclination
    t_norm = rom_norms["trunk_angle"]
    items.append(evaluate_kinematic_reference(
        metric_id="trunk_angle",
        display_name="Trunk Inclination",
        measured_val=trunk_angle_mean,
        unit="°",
        ref_low=t_norm["low"],
        ref_high=t_norm["high"],
        source=t_norm["source"],
        confidence_score=pipeline_conf
    ))

    # Step-Time Asymmetry
    asym_norm = rom_norms["asymmetry_pct"]
    items.append(evaluate_kinematic_reference(
        metric_id="step_time_asymmetry",
        display_name="Step-Time Asymmetry",
        measured_val=round(step_asymmetry, 1),
        unit="%",
        ref_low=asym_norm["low"],
        ref_high=asym_norm["high"],
        source=asym_norm["source"],
        confidence_score=pipeline_conf
    ))

    return items


# Backward compatibility alias
evaluate_metric_against_reference = evaluate_kinematic_reference

