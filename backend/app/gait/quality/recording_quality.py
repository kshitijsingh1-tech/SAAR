"""
Recording-level quality assessment ported from ToddleAI QualityGate.
"""
from typing import List, Tuple
from ..schemas import FrameQuality, FrameStatus, CaptureConfidence, CaptureAssessment

MIN_GOOD_SEGMENT_FRAMES = 15  # ~0.5s at 30fps (appropriate for fast toddler step cycle durations)


def longest_good_segment(frame_qualities: List[FrameQuality]) -> Tuple[int, int, int]:
    """Finds the (start_index, end_index, length) of the longest sequence of GOOD frames."""
    best_start = 0
    best_end = 0
    best_len = 0

    current_start = -1
    current_len = 0

    for fq in frame_qualities:
        if fq.status == FrameStatus.GOOD:
            if current_start == -1:
                current_start = fq.frame_index
            current_len += 1
            current_end = fq.frame_index
            if current_len > best_len:
                best_start = current_start
                best_end = current_end
                best_len = current_len
        else:
            current_start = -1
            current_len = 0

    return best_start, best_end, best_len


def assess_recording(frame_qualities: List[FrameQuality], detected_steps: int) -> CaptureAssessment:
    """Computes whole-recording capture confidence and feedback issues."""
    if not frame_qualities:
        return CaptureAssessment(
            confidence=CaptureConfidence.REJECT,
            issues=["No usable frames were available from this recording."],
            best_segment_start=0,
            best_segment_end=0,
            usable_step_count=0,
            good_frame_ratio=0.0
        )

    total_frames = len(frame_qualities)
    good_frames = [fq for fq in frame_qualities if fq.status == FrameStatus.GOOD]
    partial_frames = [fq for fq in frame_qualities if fq.status == FrameStatus.PARTIAL]
    good_frame_ratio = float(len(good_frames) / total_frames)
    usable_frame_ratio = float((len(good_frames) + len(partial_frames)) / total_frames)

    seg_start, seg_end, seg_len = longest_good_segment(frame_qualities)

    # Classification adapted for pediatric recording durations and side-view cross-overs
    if detected_steps >= 6 and (good_frame_ratio > 0.60 or usable_frame_ratio > 0.80) and seg_len >= MIN_GOOD_SEGMENT_FRAMES:
        confidence = CaptureConfidence.HIGH
    elif detected_steps >= 5 and (good_frame_ratio > 0.35 or usable_frame_ratio > 0.60) and seg_len >= MIN_GOOD_SEGMENT_FRAMES:
        confidence = CaptureConfidence.MEDIUM
    elif detected_steps >= 3:
        confidence = CaptureConfidence.LOW
    else:
        confidence = CaptureConfidence.REJECT

    issues: List[str] = []

    hidden_feet_count = sum(1 for fq in frame_qualities if not fq.both_feet_visible)
    hidden_feet_ratio = float(hidden_feet_count / total_frames)
    if hidden_feet_ratio > 0.65:
        issues.append(f"Feet were hidden in {hidden_feet_ratio * 100:.0f}% of frames. Record from knee height.")

    unstable_count = sum(1 for fq in frame_qualities if not fq.camera_stable)
    unstable_ratio = float(unstable_count / total_frames)
    if unstable_ratio > 0.25:
        issues.append("Camera movement detected. Hold the phone still or prop it up.")


    if detected_steps < 5:
        issues.append(f"Only {detected_steps} steps detected. Record a longer walking sequence.")

    likely_front_facing_count = sum(
        1 for fq in frame_qualities
        if fq.both_feet_visible and fq.full_body_in_frame and not fq.all_major_landmarks_visible
    )
    likely_front_facing_ratio = float(likely_front_facing_count / total_frames)
    if likely_front_facing_ratio > 0.35:
        issues.append("Child appears to be facing the camera. Record from the side.")

    valid_seg_start = seg_start if seg_len >= MIN_GOOD_SEGMENT_FRAMES else 0
    valid_seg_end = seg_end if seg_len >= MIN_GOOD_SEGMENT_FRAMES else 0

    return CaptureAssessment(
        confidence=confidence,
        issues=issues,
        best_segment_start=valid_seg_start,
        best_segment_end=valid_seg_end,
        usable_step_count=detected_steps,
        good_frame_ratio=round(good_frame_ratio, 4)
    )
