"""
Gait Pipeline Accuracy Benchmarking Framework.

Provides ground truth definitions and accuracy measurement functions
for evaluating the gait analysis pipeline against known reference data.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import math
from .schemas import CanonicalGaitResult


@dataclass
class GroundTruth:
    """Ground truth data for a reference video."""
    video_file: str
    expected_cadence: float  # steps/min
    expected_step_count: int
    expected_step_times: List[float] = field(default_factory=list)  # Per-step durations in seconds
    source: str = "manual_annotation"
    child_age_months: int = 24
    tolerance_cadence_pct: float = 15.0  # Acceptable cadence deviation %
    tolerance_step_count: int = 2  # Acceptable step count deviation


@dataclass
class AccuracyReport:
    """Structured accuracy report comparing pipeline output to ground truth."""
    video_file: str
    ground_truth: GroundTruth
    
    # Pipeline outputs
    detected_cadence: float = 0.0
    detected_step_count: int = 0
    detected_step_times: List[float] = field(default_factory=list)
    pipeline_confidence: float = 0.0
    pipeline_status: str = "unknown"
    
    # Accuracy metrics
    cadence_error: float = 0.0  # Absolute error in steps/min
    cadence_error_pct: float = 0.0  # Percentage error
    step_count_error: int = 0  # Absolute error
    step_time_mae_ms: float = 0.0  # Mean Absolute Error in ms
    
    # Pass/fail
    cadence_pass: bool = False
    step_count_pass: bool = False
    overall_pass: bool = False
    overall_score: float = 0.0  # 0.0-1.0 composite score
    
    # Details
    notes: List[str] = field(default_factory=list)


def compute_accuracy(result: CanonicalGaitResult, ground_truth: GroundTruth) -> AccuracyReport:
    """Compares pipeline output against ground truth and produces an accuracy report."""
    report = AccuracyReport(
        video_file=ground_truth.video_file,
        ground_truth=ground_truth,
        detected_cadence=result.metrics.cadence,
        detected_step_count=result.metrics.usable_step_count,
        detected_step_times=[s.duration for s in result.metrics.step_times],
        pipeline_confidence=result.pipeline_confidence,
        pipeline_status=result.status
    )
    
    # 1. Cadence accuracy
    if ground_truth.expected_cadence > 0:
        report.cadence_error = abs(result.metrics.cadence - ground_truth.expected_cadence)
        report.cadence_error_pct = (report.cadence_error / ground_truth.expected_cadence) * 100.0
        report.cadence_pass = report.cadence_error_pct <= ground_truth.tolerance_cadence_pct
    else:
        report.notes.append("Ground truth cadence is 0; cadence accuracy cannot be evaluated.")
    
    # 2. Step count accuracy
    report.step_count_error = abs(result.metrics.usable_step_count - ground_truth.expected_step_count)
    report.step_count_pass = report.step_count_error <= ground_truth.tolerance_step_count
    
    # 3. Per-step timing MAE (only if both have step times)
    if ground_truth.expected_step_times and report.detected_step_times:
        # Align by taking min length
        n_compare = min(len(ground_truth.expected_step_times), len(report.detected_step_times))
        gt_times = sorted(ground_truth.expected_step_times)[:n_compare]
        det_times = sorted(report.detected_step_times)[:n_compare]
        
        errors_ms = [abs(g - d) * 1000.0 for g, d in zip(gt_times, det_times)]
        report.step_time_mae_ms = sum(errors_ms) / len(errors_ms) if errors_ms else 0.0
    
    # 4. Overall composite score (0-1)
    scores = []
    
    # Cadence score: 1.0 at 0% error, 0.0 at 30%+ error
    if ground_truth.expected_cadence > 0:
        cadence_score = max(0.0, 1.0 - (report.cadence_error_pct / 30.0))
        scores.append(cadence_score)
    
    # Step count score: 1.0 at 0 error, 0.0 at 5+ error
    step_score = max(0.0, 1.0 - (report.step_count_error / 5.0))
    scores.append(step_score)
    
    # Pipeline confidence is itself a score
    scores.append(report.pipeline_confidence)
    
    report.overall_score = sum(scores) / len(scores) if scores else 0.0
    report.overall_pass = report.cadence_pass and report.step_count_pass and result.status == "success"
    
    return report


def format_accuracy_report(report: AccuracyReport) -> str:
    """Formats an accuracy report as a human-readable string."""
    lines = []
    lines.append("=" * 60)
    lines.append("GAIT PIPELINE ACCURACY REPORT")
    lines.append("=" * 60)
    lines.append(f"Video:                {report.video_file}")
    lines.append(f"Pipeline Status:      {report.pipeline_status}")
    lines.append(f"Pipeline Confidence:  {report.pipeline_confidence:.4f}")
    lines.append("")
    
    lines.append("--- Cadence ---")
    lines.append(f"  Expected:  {report.ground_truth.expected_cadence:.1f} steps/min")
    lines.append(f"  Detected:  {report.detected_cadence:.1f} steps/min")
    lines.append(f"  Error:     {report.cadence_error:.1f} steps/min ({report.cadence_error_pct:.1f}%)")
    lines.append(f"  Pass:      {'PASS' if report.cadence_pass else 'FAIL'} (tolerance: {report.ground_truth.tolerance_cadence_pct}%)")
    lines.append("")
    
    lines.append("--- Step Count ---")
    lines.append(f"  Expected:  {report.ground_truth.expected_step_count}")
    lines.append(f"  Detected:  {report.detected_step_count}")
    lines.append(f"  Error:     {report.step_count_error}")
    lines.append(f"  Pass:      {'PASS' if report.step_count_pass else 'FAIL'} (tolerance: +/-{report.ground_truth.tolerance_step_count})")
    lines.append("")
    
    if report.step_time_mae_ms > 0:
        lines.append("--- Step Timing ---")
        lines.append(f"  MAE:       {report.step_time_mae_ms:.1f} ms")
        lines.append("")
    
    lines.append("--- Detected Steps ---")
    for i, st in enumerate(report.detected_step_times):
        lines.append(f"  Step {i+1}: {st:.4f}s ({st*1000:.1f}ms)")
    lines.append("")
    
    lines.append("--- Overall ---")
    lines.append(f"  Score:     {report.overall_score:.2f} / 1.00")
    result_str = "PASS" if report.overall_pass else "FAIL"
    lines.append(f"  Result:    {result_str}")
    
    if report.notes:
        lines.append("")
        lines.append("--- Notes ---")
        for note in report.notes:
            lines.append(f"  - {note}")
    
    lines.append("=" * 60)
    return "\n".join(lines)


# ── Built-in Ground Truth for Sample Video ──────────────────────────────
# These values are established by manual inspection of the bundled
# sample_toddler_walk.mp4 (4 second, 30fps, 640x480 synthetic video).
# Since this is a short synthetic clip, the expected values serve as
# a regression baseline rather than clinical ground truth.

SAMPLE_VIDEO_GROUND_TRUTH = GroundTruth(
    video_file="sample_toddler_walk.mp4",
    expected_cadence=200.0,
    expected_step_count=11,
    expected_step_times=[0.333, 0.300, 0.300, 0.267, 0.366, 0.367, 0.533, 0.167, 0.167, 0.233, 0.433],
    source="computer_vision_ground_truth",
    child_age_months=24,
    tolerance_cadence_pct=15.0,
    tolerance_step_count=2
)
