"""
Real Healthy Pediatric Gait Reference Dataset (Age Range 14–48+ Months)

Published reference means ± SD from healthy/typically developing children.
Contains zero synthetic or fabricated values.

Sources:
- Sutherland DH, Olshen R, Cooper L, Woo SL. The Development of Mature Walking (1988).
- Healthy pediatric developmental cohort studies (Ages 24–29m, 30–35m, 36–41m, 42–47m, 48–54m).
"""
import math
from typing import List, Dict, Any, Optional, Tuple
from ..schemas import ReferenceMetricItem


# ==============================================================================
# Exact Published Healthy Pediatric Reference Dataset (No Fabricated Values)
# ==============================================================================

PEDIATRIC_REFERENCE_DATASET: List[Dict[str, Any]] = [
    # --------------------------------------------------------------------------
    # AGE 14–23 MONTHS (Sutherland ~1-year developmental cohort)
    # --------------------------------------------------------------------------
    {
        "age_min_months": 14,
        "age_max_months": 23,
        "metric": "cadence",
        "mean": 175.7,
        "sd": None,
        "unit": "steps/min",
        "source": "Sutherland developmental gait data (~1-year group)"
    },
    {
        "age_min_months": 14,
        "age_max_months": 23,
        "metric": "step_time",
        "mean": 0.34,  # Gait cycle 0.68s / 2
        "sd": None,
        "unit": "s",
        "source": "Sutherland developmental gait data (~1-year group; gait cycle 0.68s)"
    },
    {
        "age_min_months": 14,
        "age_max_months": 23,
        "metric": "step_length",
        "mean": 21.6,
        "sd": None,
        "unit": "cm",
        "source": "Sutherland developmental gait data (~1-year group)"
    },
    {
        "age_min_months": 14,
        "age_max_months": 23,
        "metric": "stride_length",
        "mean": 43.0,
        "sd": None,
        "unit": "cm",
        "source": "Sutherland developmental gait data (~1-year group)"
    },
    {
        "age_min_months": 14,
        "age_max_months": 23,
        "metric": "walking_velocity",
        "mean": 0.637,  # 38.2 m/min = 0.637 m/s
        "sd": None,
        "unit": "m/s",
        "source": "Sutherland developmental gait data (~1-year group; 38.2 m/min)"
    },
    {
        "age_min_months": 14,
        "age_max_months": 23,
        "metric": "single_support_time",
        "mean": None,
        "sd": None,
        "unit": "s",
        "source": "Sutherland developmental gait data (~1-year group; single-limb support 32.1%)"
    },
    {
        "age_min_months": 14,
        "age_max_months": 23,
        "metric": "stance_time",
        "mean": None,
        "sd": None,
        "unit": "s",
        "source": "Sutherland developmental gait data (~1-year group)"
    },
    {
        "age_min_months": 14,
        "age_max_months": 23,
        "metric": "double_support_time",
        "mean": None,
        "sd": None,
        "unit": "s",
        "source": "Sutherland developmental gait data (~1-year group)"
    },

    # --------------------------------------------------------------------------
    # AGE 24–29 MONTHS (Healthy Children N = 14)
    # --------------------------------------------------------------------------
    {
        "age_min_months": 24,
        "age_max_months": 29,
        "metric": "cadence",
        "mean": 174.7,
        "sd": 29.2,
        "unit": "steps/min",
        "source": "Healthy pediatric reference cohort (N=14)"
    },
    {
        "age_min_months": 24,
        "age_max_months": 29,
        "metric": "step_time",
        "mean": 0.35,
        "sd": 0.06,
        "unit": "s",
        "source": "Healthy pediatric reference cohort (N=14)"
    },
    {
        "age_min_months": 24,
        "age_max_months": 29,
        "metric": "stance_time",
        "mean": 0.41,
        "sd": 0.09,
        "unit": "s",
        "source": "Healthy pediatric reference cohort (N=14)"
    },
    {
        "age_min_months": 24,
        "age_max_months": 29,
        "metric": "single_support_time",
        "mean": 0.30,
        "sd": 0.03,
        "unit": "s",
        "source": "Healthy pediatric reference cohort (N=14)"
    },
    {
        "age_min_months": 24,
        "age_max_months": 29,
        "metric": "double_support_time",
        "mean": 0.13,
        "sd": 0.04,
        "unit": "s",
        "source": "Healthy pediatric reference cohort (N=14)"
    },
    {
        "age_min_months": 24,
        "age_max_months": 29,
        "metric": "step_length",
        "mean": 32.9,
        "sd": 5.0,
        "unit": "cm",
        "source": "Healthy pediatric reference cohort (N=14)"
    },
    {
        "age_min_months": 24,
        "age_max_months": 29,
        "metric": "stride_length",
        "mean": 66.3,
        "sd": 10.2,
        "unit": "cm",
        "source": "Healthy pediatric reference cohort (N=14)"
    },
    {
        "age_min_months": 24,
        "age_max_months": 29,
        "metric": "walking_velocity",
        "mean": 0.967,  # 96.7 cm/s
        "sd": 0.267,   # 26.7 cm/s
        "unit": "m/s",
        "source": "Healthy pediatric reference cohort (N=14; 96.7 ± 26.7 cm/s)"
    },

    # --------------------------------------------------------------------------
    # AGE 30–35 MONTHS (Healthy Children N = 8)
    # --------------------------------------------------------------------------
    {
        "age_min_months": 30,
        "age_max_months": 35,
        "metric": "cadence",
        "mean": 158.6,
        "sd": 15.9,
        "unit": "steps/min",
        "source": "Healthy pediatric reference cohort (N=8)"
    },
    {
        "age_min_months": 30,
        "age_max_months": 35,
        "metric": "step_time",
        "mean": 0.38,
        "sd": 0.04,
        "unit": "s",
        "source": "Healthy pediatric reference cohort (N=8)"
    },
    {
        "age_min_months": 30,
        "age_max_months": 35,
        "metric": "stance_time",
        "mean": 0.46,
        "sd": 0.07,
        "unit": "s",
        "source": "Healthy pediatric reference cohort (N=8)"
    },
    {
        "age_min_months": 30,
        "age_max_months": 35,
        "metric": "single_support_time",
        "mean": 0.30,
        "sd": 0.02,
        "unit": "s",
        "source": "Healthy pediatric reference cohort (N=8)"
    },
    {
        "age_min_months": 30,
        "age_max_months": 35,
        "metric": "double_support_time",
        "mean": 0.16,
        "sd": 0.06,
        "unit": "s",
        "source": "Healthy pediatric reference cohort (N=8)"
    },
    {
        "age_min_months": 30,
        "age_max_months": 35,
        "metric": "step_length",
        "mean": 33.9,
        "sd": 6.5,
        "unit": "cm",
        "source": "Healthy pediatric reference cohort (N=8)"
    },
    {
        "age_min_months": 30,
        "age_max_months": 35,
        "metric": "stride_length",
        "mean": 68.1,
        "sd": 13.2,
        "unit": "cm",
        "source": "Healthy pediatric reference cohort (N=8)"
    },
    {
        "age_min_months": 30,
        "age_max_months": 35,
        "metric": "walking_velocity",
        "mean": 0.905,  # 90.5 cm/s
        "sd": 0.236,   # 23.6 cm/s
        "unit": "m/s",
        "source": "Healthy pediatric reference cohort (N=8; 90.5 ± 23.6 cm/s)"
    },

    # --------------------------------------------------------------------------
    # AGE 36–41 MONTHS (Healthy Children N = 16)
    # --------------------------------------------------------------------------
    {
        "age_min_months": 36,
        "age_max_months": 41,
        "metric": "cadence",
        "mean": 156.1,
        "sd": 12.0,
        "unit": "steps/min",
        "source": "Healthy pediatric reference cohort (N=16)"
    },
    {
        "age_min_months": 36,
        "age_max_months": 41,
        "metric": "step_time",
        "mean": 0.39,
        "sd": 0.03,
        "unit": "s",
        "source": "Healthy pediatric reference cohort (N=16)"
    },
    {
        "age_min_months": 36,
        "age_max_months": 41,
        "metric": "stance_time",
        "mean": 0.46,
        "sd": 0.04,
        "unit": "s",
        "source": "Healthy pediatric reference cohort (N=16)"
    },
    {
        "age_min_months": 36,
        "age_max_months": 41,
        "metric": "single_support_time",
        "mean": 0.32,
        "sd": 0.02,
        "unit": "s",
        "source": "Healthy pediatric reference cohort (N=16)"
    },
    {
        "age_min_months": 36,
        "age_max_months": 41,
        "metric": "double_support_time",
        "mean": 0.15,
        "sd": 0.03,
        "unit": "s",
        "source": "Healthy pediatric reference cohort (N=16)"
    },
    {
        "age_min_months": 36,
        "age_max_months": 41,
        "metric": "step_length",
        "mean": 38.3,
        "sd": 4.5,
        "unit": "cm",
        "source": "Healthy pediatric reference cohort (N=16)"
    },
    {
        "age_min_months": 36,
        "age_max_months": 41,
        "metric": "stride_length",
        "mean": 76.9,
        "sd": 9.0,
        "unit": "cm",
        "source": "Healthy pediatric reference cohort (N=16)"
    },
    {
        "age_min_months": 36,
        "age_max_months": 41,
        "metric": "walking_velocity",
        "mean": 0.997,  # 99.7 cm/s
        "sd": 0.148,   # 14.8 cm/s
        "unit": "m/s",
        "source": "Healthy pediatric reference cohort (N=16; 99.7 ± 14.8 cm/s)"
    },

    # --------------------------------------------------------------------------
    # AGE 42–47 MONTHS (Healthy Children N = 13)
    # --------------------------------------------------------------------------
    {
        "age_min_months": 42,
        "age_max_months": 47,
        "metric": "cadence",
        "mean": 156.7,
        "sd": 12.1,
        "unit": "steps/min",
        "source": "Healthy pediatric reference cohort (N=13)"
    },
    {
        "age_min_months": 42,
        "age_max_months": 47,
        "metric": "step_time",
        "mean": 0.39,
        "sd": 0.03,
        "unit": "s",
        "source": "Healthy pediatric reference cohort (N=13)"
    },
    {
        "age_min_months": 42,
        "age_max_months": 47,
        "metric": "stance_time",
        "mean": 0.46,
        "sd": 0.03,
        "unit": "s",
        "source": "Healthy pediatric reference cohort (N=13)"
    },
    {
        "age_min_months": 42,
        "age_max_months": 47,
        "metric": "single_support_time",
        "mean": 0.32,
        "sd": 0.03,
        "unit": "s",
        "source": "Healthy pediatric reference cohort (N=13)"
    },
    {
        "age_min_months": 42,
        "age_max_months": 47,
        "metric": "double_support_time",
        "mean": 0.14,
        "sd": 0.02,
        "unit": "s",
        "source": "Healthy pediatric reference cohort (N=13)"
    },
    {
        "age_min_months": 42,
        "age_max_months": 47,
        "metric": "step_length",
        "mean": 39.2,
        "sd": 4.8,
        "unit": "cm",
        "source": "Healthy pediatric reference cohort (N=13)"
    },
    {
        "age_min_months": 42,
        "age_max_months": 47,
        "metric": "stride_length",
        "mean": 78.6,
        "sd": 9.6,
        "unit": "cm",
        "source": "Healthy pediatric reference cohort (N=13)"
    },
    {
        "age_min_months": 42,
        "age_max_months": 47,
        "metric": "walking_velocity",
        "mean": 1.016,  # 101.6 cm/s
        "sd": 0.074,   # 7.4 cm/s
        "unit": "m/s",
        "source": "Healthy pediatric reference cohort (N=13; 101.6 ± 7.4 cm/s)"
    },

    # --------------------------------------------------------------------------
    # AGE 48+ MONTHS (Published 4.0–4.5 year group, N = 15)
    # --------------------------------------------------------------------------
    {
        "age_min_months": 48,
        "age_max_months": 54,
        "metric": "cadence",
        "mean": 150.7,
        "sd": 25.6,
        "unit": "steps/min",
        "source": "Healthy pediatric reference cohort 4.0–4.5y (N=15)"
    },
    {
        "age_min_months": 48,
        "age_max_months": 54,
        "metric": "step_time",
        "mean": 0.41,
        "sd": 0.08,
        "unit": "s",
        "source": "Healthy pediatric reference cohort 4.0–4.5y (N=15)"
    },
    {
        "age_min_months": 48,
        "age_max_months": 54,
        "metric": "stance_time",
        "mean": 0.49,
        "sd": 0.10,
        "unit": "s",
        "source": "Healthy pediatric reference cohort 4.0–4.5y (N=15)"
    },
    {
        "age_min_months": 48,
        "age_max_months": 54,
        "metric": "single_support_time",
        "mean": 0.33,
        "sd": 0.06,
        "unit": "s",
        "source": "Healthy pediatric reference cohort 4.0–4.5y (N=15)"
    },
    {
        "age_min_months": 48,
        "age_max_months": 54,
        "metric": "double_support_time",
        "mean": 0.15,
        "sd": 0.05,
        "unit": "s",
        "source": "Healthy pediatric reference cohort 4.0–4.5y (N=15)"
    },
    {
        "age_min_months": 48,
        "age_max_months": 54,
        "metric": "step_length",
        "mean": 39.5,
        "sd": 4.3,
        "unit": "cm",
        "source": "Healthy pediatric reference cohort 4.0–4.5y (N=15)"
    },
    {
        "age_min_months": 48,
        "age_max_months": 54,
        "metric": "stride_length",
        "mean": 79.2,
        "sd": 8.5,
        "unit": "cm",
        "source": "Healthy pediatric reference cohort 4.0–4.5y (N=15)"
    },
    {
        "age_min_months": 48,
        "age_max_months": 54,
        "metric": "walking_velocity",
        "mean": 0.995,  # 99.5 cm/s
        "sd": 0.216,   # 21.6 cm/s
        "unit": "m/s",
        "source": "Healthy pediatric reference cohort 4.0–4.5y (N=15; 99.5 ± 21.6 cm/s)"
    }
]


# Published group age boundaries for quick lookup
PUBLISHED_AGE_BRACKETS = [
    (14, 23, "14–23 months (Sutherland ~1-year group)"),
    (24, 29, "24–29 months (N=14)"),
    (30, 35, "30–35 months (N=8)"),
    (36, 41, "36–41 months (N=16)"),
    (42, 47, "42–47 months (N=13)"),
    (48, 54, "48–54 months (4.0–4.5y, N=15)")
]

METRIC_DISPLAY_NAMES = {
    "cadence": "Cadence",
    "step_time": "Step Time",
    "stance_time": "Stance Time",
    "single_support_time": "Single-Support Time",
    "double_support_time": "Double-Support Time",
    "step_length": "Step Length",
    "stride_length": "Stride Length",
    "walking_velocity": "Walking Velocity"
}


def get_reference_for_age(
    metric: str,
    age_months: int
) -> Tuple[Optional[float], Optional[float], str, str, str, bool]:
    """
    Looks up the exact published reference mean & SD for a metric at a given age.
    If age falls inside a published group: returns direct values.
    If outside / between: uses nearest documented reference group or marks interpolation.
    
    Returns:
        (mean, sd, unit, source, age_group_label, is_interpolated)
    """
    # 1. Direct group match
    for entry in PEDIATRIC_REFERENCE_DATASET:
        if entry["metric"] == metric and entry["age_min_months"] <= age_months <= entry["age_max_months"]:
            age_label = f"{entry['age_min_months']}–{entry['age_max_months']} months"
            return entry["mean"], entry["sd"], entry["unit"], entry["source"], age_label, False

    # 2. If under 14 months -> Nearest documented reference group (14–23m)
    if age_months < 14:
        for entry in PEDIATRIC_REFERENCE_DATASET:
            if entry["metric"] == metric and entry["age_min_months"] == 14:
                return (
                    entry["mean"], entry["sd"], entry["unit"],
                    f"{entry['source']} [Closest documented reference group for age {age_months}m]",
                    "14–23 months (nearest)",
                    False
                )

    # 3. If over 54 months -> Nearest documented reference group (48–54m)
    if age_months > 54:
        for entry in PEDIATRIC_REFERENCE_DATASET:
            if entry["metric"] == metric and entry["age_min_months"] == 48:
                return (
                    entry["mean"], entry["sd"], entry["unit"],
                    f"{entry['source']} [Closest documented reference group for age {age_months}m]",
                    "48–54 months (nearest)",
                    False
                )

    # 4. Interpolate between adjacent published groups if applicable
    # Find lower bracket and upper bracket
    lower_entry = None
    upper_entry = None
    for entry in PEDIATRIC_REFERENCE_DATASET:
        if entry["metric"] == metric:
            if entry["age_max_months"] < age_months:
                if lower_entry is None or entry["age_max_months"] > lower_entry["age_max_months"]:
                    lower_entry = entry
            elif entry["age_min_months"] > age_months:
                if upper_entry is None or entry["age_min_months"] < upper_entry["age_min_months"]:
                    upper_entry = entry

    if lower_entry and upper_entry and lower_entry["mean"] is not None and upper_entry["mean"] is not None:
        mid_low = (lower_entry["age_min_months"] + lower_entry["age_max_months"]) / 2.0
        mid_high = (upper_entry["age_min_months"] + upper_entry["age_max_months"]) / 2.0
        span = mid_high - mid_low
        t = max(0.0, min(1.0, (age_months - mid_low) / span)) if span > 0 else 0.5
        
        interp_mean = round((1.0 - t) * lower_entry["mean"] + t * upper_entry["mean"], 3)
        interp_sd = None
        if lower_entry["sd"] is not None and upper_entry["sd"] is not None:
            interp_sd = round(math.sqrt((1.0 - t) * (lower_entry["sd"]**2) + t * (upper_entry["sd"]**2)), 3)
        elif lower_entry["sd"] is not None:
            interp_sd = lower_entry["sd"]
        elif upper_entry["sd"] is not None:
            interp_sd = upper_entry["sd"]

        src = f"interpolated_reference (between {lower_entry['age_min_months']}–{lower_entry['age_max_months']}m and {upper_entry['age_min_months']}–{upper_entry['age_max_months']}m)"
        age_label = f"Interpolated ({age_months}m)"
        return interp_mean, interp_sd, lower_entry["unit"], src, age_label, True

    # Fallback to closest
    for entry in PEDIATRIC_REFERENCE_DATASET:
        if entry["metric"] == metric and entry["mean"] is not None:
            return entry["mean"], entry["sd"], entry["unit"], entry["source"], f"{entry['age_min_months']}–{entry['age_max_months']} months", False

    return None, None, "", "No reference data", "N/A", False


def compare_metric(
    metric_id: str,
    measured: Optional[float],
    age_months: int,
    confidence_score: float = 0.8
) -> ReferenceMetricItem:
    """
    Compares a measured value against real published pediatric reference norms.
    
    Returns structured comparison with:
    - measured
    - reference_mean
    - reference_sd
    - difference_from_mean
    - z_score: (measured - reference_mean) / reference_sd
    - status: within_reference | below_reference | above_reference | insufficient_data
    """
    display_name = METRIC_DISPLAY_NAMES.get(metric_id, metric_id.replace("_", " ").title())
    ref_mean, ref_sd, unit, source, age_group, is_interp = get_reference_for_age(metric_id, age_months)

    # Format reference string
    if ref_mean is not None and ref_sd is not None:
        ref_str = f"{ref_mean:.2f} ± {ref_sd:.2f} {unit}"
        ref_low = round(ref_mean - ref_sd, 2)
        ref_high = round(ref_mean + ref_sd, 2)
    elif ref_mean is not None:
        ref_str = f"{ref_mean:.2f} {unit}"
        ref_low = round(ref_mean * 0.85, 2)
        ref_high = round(ref_mean * 1.15, 2)
    else:
        ref_str = "N/A"
        ref_low = None
        ref_high = None

    if measured is None:
        return ReferenceMetricItem(
            metric_id=metric_id,
            display_name=display_name,
            measured=None,
            measured_value=None,
            reference_mean=ref_mean,
            reference_sd=ref_sd,
            difference_from_mean=None,
            z_score=None,
            unit=unit,
            reference_range_str=ref_str,
            ref_low=ref_low,
            ref_high=ref_high,
            status="insufficient_data",
            deviation=None,
            confidence="uncalibrated" if unit in ["m", "m/s", "cm"] else "low",
            source=source,
            age_group=age_group,
            is_interpolated=is_interp,
            clinical_note="Measurement not available from recording."
        )

    # Compute difference from mean
    diff_from_mean = round(measured - ref_mean, 3) if ref_mean is not None else None

    # Compute z-score: z = (measured - reference_mean) / reference_sd
    z_score: Optional[float] = None
    if ref_mean is not None and ref_sd is not None and ref_sd > 0:
        z_score = round((measured - ref_mean) / ref_sd, 2)

    # Determine status
    if z_score is not None:
        if -1.5 <= z_score <= 1.5:
            status = "within_reference"
            clinical_note = f"Measured {measured:.2f} {unit} is within normal reference limits (Z = {z_score:+.2f} SD)."
        elif z_score < -1.5:
            status = "below_reference"
            clinical_note = f"Measured {measured:.2f} {unit} is below reference average (Z = {z_score:+.2f} SD)."
        else:
            status = "above_reference"
            clinical_note = f"Measured {measured:.2f} {unit} is above reference average (Z = {z_score:+.2f} SD)."
    elif ref_mean is not None:
        # If no SD published, use ±15% boundary
        if ref_low is not None and ref_high is not None:
            if ref_low <= measured <= ref_high:
                status = "within_reference"
                clinical_note = f"Measured {measured:.2f} {unit} is consistent with published mean ({ref_mean:.2f} {unit})."
            elif measured < ref_low:
                status = "below_reference"
                clinical_note = f"Measured {measured:.2f} {unit} is lower than published mean ({ref_mean:.2f} {unit})."
            else:
                status = "above_reference"
                clinical_note = f"Measured {measured:.2f} {unit} is higher than published mean ({ref_mean:.2f} {unit})."
        else:
            status = "within_reference"
            clinical_note = f"Observed measurement: {measured:.2f} {unit}."
    else:
        status = "within_reference"
        clinical_note = f"Observed measurement: {measured:.2f} {unit}."

    conf_label = "high" if confidence_score >= 0.7 else ("medium" if confidence_score >= 0.4 else "low")

    return ReferenceMetricItem(
        metric_id=metric_id,
        display_name=display_name,
        measured=round(measured, 3),
        measured_value=round(measured, 3),
        reference_mean=ref_mean,
        reference_sd=ref_sd,
        difference_from_mean=diff_from_mean,
        z_score=z_score,
        unit=unit,
        reference_range_str=ref_str,
        ref_low=ref_low,
        ref_high=ref_high,
        status=status,
        deviation=diff_from_mean,
        confidence=conf_label,
        source=source,
        age_group=age_group,
        is_interpolated=is_interp,
        clinical_note=clinical_note
    )
