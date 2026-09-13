"""
Badminton Video Quality Assessment Gate.
Performs frame-by-frame and whole-recording quality evaluation.
Evaluates camera stability, frame rate, resolution, and clip duration against
badminton rally biomechanical standards.
Ensures uncomputed signals (player/court/racket/shuttle visibility) are structurally
unavailable with no fabricated numbers.
"""
import cv2
import numpy as np
from typing import List, Tuple, Optional
from .schemas import (
    VideoMetadata,
    BadmintonFrame,
    QualityAssessment,
    CaptureConfidence,
    Metric
)

# ==============================================================================
# QUALITY THRESHOLDS & BIOMECHANICAL JUSTIFICATIONS
# ==============================================================================
# 1. MIN_DURATION_SECONDS (3.0s):
#    A single badminton overhead stroke sequence (preparation phase, jump/hop,
#    kinetic-chain backswing, contact, and recovery back to the base position)
#    takes a physiological minimum of 3.0 seconds. Video clips shorter than this
#    cannot encompass a single stroke cycle or rally exchange and are rejected.
#
# 2. MIN_ACCEPTABLE_FPS (24.0) & RECOMMENDED_FPS (30.0+):
#    Badminton shuttlecocks and racquets travel at extreme speeds. At 24 FPS or below,
#    impact frame temporal discretization is too coarse, producing severe motion blur.
#
# 3. CAMERA_STABILITY_THRESHOLD (0.08 normalized frame diff):
#    Camera shake or panning introduces false accelerations into player motion vectors.
#    Frame-to-frame global visual displacement is measured on thumbnail projections.
# ==============================================================================
MIN_DURATION_SECONDS: float = 3.0
MIN_TOTAL_FRAMES: int = 30
MIN_ACCEPTABLE_FPS: float = 24.0
import base64
RECOMMENDED_FPS: float = 29.5
MIN_HD_WIDTH: int = 1280
MIN_HD_HEIGHT: int = 720
CAMERA_DIFF_PIXEL_THRESHOLD: float = 2.5  # Mean pixel delta on normalized grayscale thumbnail indicating camera jitter


def generate_preview_base64(raw_frames: Optional[List[np.ndarray]], max_dim: int = 480) -> Optional[str]:
    """
    Extracts a representative frame from the recording, scales it to a web-optimized
    thumbnail, and encodes it as a base64 JPEG data URI.
    """
    if not raw_frames or len(raw_frames) == 0:
        return None
    idx = min(len(raw_frames) - 1, max(0, len(raw_frames) // 4))
    frame = raw_frames[idx]
    h, w = frame.shape[:2]
    if w > max_dim or h > max_dim:
        scale = max_dim / max(w, h)
        frame_resized = cv2.resize(frame, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    else:
        frame_resized = frame

    success, buffer = cv2.imencode(".jpg", frame_resized, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    if not success:
        return None
    b64_str = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/jpeg;base64,{b64_str}"


def detect_motion_blur(raw_frames: Optional[List[np.ndarray]]) -> Tuple[float, bool]:
    """
    Computes Laplacian variance across sampled frames to detect excessive motion blur.
    Low variance (< 60.0) indicates significant defocus, high motion blur, or poor sensor capture.
    """
    if not raw_frames or len(raw_frames) == 0:
        return 0.0, False
    sample_indices = np.linspace(0, len(raw_frames) - 1, min(10, len(raw_frames)), dtype=int)
    scores = []
    for idx in sample_indices:
        gray = cv2.cvtColor(raw_frames[idx], cv2.COLOR_BGR2GRAY)
        score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        scores.append(score)
    avg_score = float(np.mean(scores)) if scores else 0.0
    has_excessive_blur = avg_score < 60.0
    return round(avg_score, 2), has_excessive_blur


def detect_lighting_quality(raw_frames: Optional[List[np.ndarray]]) -> Tuple[float, float, List[str]]:
    """
    Evaluates average luminance and dynamic range across the video.
    Returns: (mean_brightness, dynamic_range, warnings)
    """
    if not raw_frames or len(raw_frames) == 0:
        return 0.0, 0.0, []
    sample_indices = np.linspace(0, len(raw_frames) - 1, min(10, len(raw_frames)), dtype=int)
    luminances = []
    for idx in sample_indices:
        gray = cv2.cvtColor(raw_frames[idx], cv2.COLOR_BGR2GRAY)
        luminances.append(float(np.mean(gray)))
    avg_luma = float(np.mean(luminances)) if luminances else 128.0
    dyn_range = float(np.ptp(luminances)) if luminances else 0.0
    warnings = []
    if avg_luma < 40.0:
        warnings.append("Underexposed / poor lighting conditions detected. Joint estimation accuracy may degrade.")
    elif avg_luma > 220.0:
        warnings.append("Overexposed / blown out lighting detected. Shuttlecock contrast will be impaired.")
    return round(avg_luma, 2), round(dyn_range, 2), warnings


def detect_court_visibility_heuristic(raw_frames: Optional[List[np.ndarray]]) -> bool:
    """
    Heuristic check for presence of straight white court line segments in the video.
    """
    if not raw_frames or len(raw_frames) == 0:
        return False
    mid_frame = raw_frames[len(raw_frames) // 2]
    gray = cv2.cvtColor(mid_frame, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=70, minLineLength=35, maxLineGap=10)
    return lines is not None and len(lines) >= 3


def detect_player_visibility_heuristic(raw_frames: Optional[List[np.ndarray]]) -> bool:
    """
    Heuristic check for player visibility using foreground motion / contours.
    """
    if not raw_frames or len(raw_frames) < 2:
        return False
    diff = cv2.absdiff(raw_frames[0], raw_frames[-1])
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 20, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    large_contours = [c for c in contours if cv2.contourArea(c) > 400]
    return len(large_contours) >= 1


def compute_overall_quality_score(
    metadata: VideoMetadata,
    stability_score: float,
    blur_score: float,
    avg_luma: float
) -> float:
    """
    Computes a normalized composite video capture quality score in [0.0, 1.0].
    Weights: Resolution (25%), FPS (25%), Stability (25%), Clarity/Blur (15%), Lighting (10%).
    """
    # Resolution score
    if metadata.width >= 1920 or metadata.height >= 1080:
        res_score = 1.0
    elif metadata.width >= 1280 or metadata.height >= 720:
        res_score = 0.85
    elif metadata.width >= 854 or metadata.height >= 480:
        res_score = 0.60
    else:
        res_score = 0.30

    # FPS score
    if metadata.fps >= 58.0:
        fps_score = 1.0
    elif metadata.fps >= 29.0:
        fps_score = 0.85
    elif metadata.fps >= 23.5:
        fps_score = 0.65
    else:
        fps_score = 0.35

    # Blur score (normalized with upper bound ~200)
    blur_norm = min(1.0, max(0.0, blur_score / 200.0))

    # Lighting score
    if 60.0 <= avg_luma <= 190.0:
        luma_score = 1.0
    elif 40.0 <= avg_luma <= 220.0:
        luma_score = 0.75
    else:
        luma_score = 0.40

    composite = (
        0.25 * res_score +
        0.25 * fps_score +
        0.25 * stability_score +
        0.15 * blur_norm +
        0.10 * luma_score
    )
    return round(float(composite), 3)


def assess_frame_camera_stability(curr_bgr: np.ndarray, prev_bgr: Optional[np.ndarray]) -> bool:
    """
    Evaluates frame-to-frame global camera stability.
    Uses robust background feature tracking and trimmed percentile filtering
    to prevent fast athletic foreground motion from being misclassified as camera jitter.
    """
    if prev_bgr is None:
        return True

    try:
        # Resize to standard 160x160 canvas for fast background displacement estimation
        curr_small = cv2.resize(curr_bgr, (160, 160), interpolation=cv2.INTER_AREA)
        prev_small = cv2.resize(prev_bgr, (160, 160), interpolation=cv2.INTER_AREA)

        curr_gray = cv2.cvtColor(curr_small, cv2.COLOR_BGR2GRAY)
        prev_gray = cv2.cvtColor(prev_small, cv2.COLOR_BGR2GRAY)

        # Track stationary background corner points using Lucas-Kanade optical flow
        pts_prev = cv2.goodFeaturesToTrack(prev_gray, maxCorners=50, qualityLevel=0.01, minDistance=10)
        if pts_prev is not None and len(pts_prev) >= 4:
            pts_curr, status, _ = cv2.calcOpticalFlowPyrLK(prev_gray, curr_gray, pts_prev, None)
            good_prev = pts_prev[status == 1]
            good_curr = pts_curr[status == 1]
            if len(good_prev) >= 2:
                # Compute median displacement of background features (robust against moving player)
                displacements = np.linalg.norm(good_curr - good_prev, axis=1)
                median_disp = float(np.median(displacements))
                return median_disp <= 4.0
            else:
                # Lost optical flow tracking on majority of points due to abrupt jitter/shake
                return False

        # Fallback: Trimmed pixel delta and mean difference
        diff = cv2.absdiff(curr_gray, prev_gray)
        mean_diff = float(np.mean(diff))
        p70 = float(np.percentile(diff, 70))
        return (p70 <= 14.0) and (mean_diff <= 3.0)
    except Exception:
        return True


def assess_badminton_recording_quality(
    metadata: VideoMetadata,
    raw_frames: Optional[List[np.ndarray]] = None
) -> QualityAssessment:
    """
    Evaluates complete badminton video recording against biomechanical capture standards.
    Returns QualityAssessment with HIGH, MEDIUM, LOW, or REJECT confidence and itemized feedback.
    """
    issues: List[str] = []

    # 1. Duration check
    if metadata.duration_seconds < MIN_DURATION_SECONDS:
        issues.append(
            f"Video duration ({metadata.duration_seconds}s) is under the 3.0s minimum. "
            "A full stroke or rally exchange requires at least 3 seconds of continuous footage."
        )

    # 2. Frame count check
    if metadata.total_frames < MIN_TOTAL_FRAMES:
        issues.append(
            f"Only {metadata.total_frames} frames recorded. At least {MIN_TOTAL_FRAMES} frames are required "
            "for reliable temporal trajectory reconstruction."
        )

    # 3. FPS checks
    if metadata.fps < MIN_ACCEPTABLE_FPS:
        issues.append(
            f"Frame rate ({metadata.fps} FPS) is too low for fast badminton motion. "
            "Record at 30+ FPS (60 FPS recommended) to capture clean racket contact."
        )
    elif metadata.fps < RECOMMENDED_FPS:
        issues.append(
            f"Recorded at {metadata.fps} FPS. 60 FPS is recommended for high-speed overhead smash analysis."
        )

    # 4. Resolution checks
    is_hd = (metadata.width >= MIN_HD_WIDTH or metadata.height >= MIN_HD_HEIGHT)
    if metadata.width < 640 or metadata.height < 480:
        issues.append(
            f"Low video resolution ({metadata.width}x{metadata.height}). "
            "720p (1280x720) or higher is recommended for accurate joint and shuttle tracking."
        )

    # 5. Camera stability evaluation
    unstable_frame_count = 0
    total_evaluated_frames = 0

    if raw_frames and len(raw_frames) > 1:
        total_evaluated_frames = len(raw_frames)
        for i in range(1, total_evaluated_frames):
            stable = assess_frame_camera_stability(raw_frames[i], raw_frames[i - 1])
            if not stable:
                unstable_frame_count += 1

    unstable_ratio = float(unstable_frame_count / total_evaluated_frames) if total_evaluated_frames > 0 else 0.0
    stability_score = round(1.0 - unstable_ratio, 3)

    if unstable_ratio > 0.25:
        issues.append(
            f"Camera movement detected in {unstable_ratio * 100:.0f}% of frames. "
            "Hold the camera still or use a tripod mount behind the baseline."
        )

    # 6. Motion blur detection
    blur_score, has_excessive_blur = detect_motion_blur(raw_frames)
    if has_excessive_blur and blur_score > 0:
        issues.append(
            f"Significant motion blur or defocus detected (Laplacian variance: {blur_score}). "
            "Fast racket movements and shuttlecock flight may suffer tracking loss."
        )

    # 7. Lighting & exposure evaluation
    avg_luma, dyn_range, lighting_warnings = detect_lighting_quality(raw_frames)
    issues.extend(lighting_warnings)

    # 8. Compute composite quality score
    composite_quality = compute_overall_quality_score(metadata, stability_score, blur_score, avg_luma)
    metadata.quality_score = composite_quality
    metadata.analysis_warnings = list(issues)

    # 9. Generate web preview thumbnail
    if not metadata.preview_image_base64 and raw_frames:
        metadata.preview_image_base64 = generate_preview_base64(raw_frames)

    # 10. Confidence classification
    # Hard rejection criteria:
    if (
        metadata.duration_seconds < MIN_DURATION_SECONDS
        or metadata.total_frames < MIN_TOTAL_FRAMES
        or metadata.width < 320
        or metadata.height < 240
        or unstable_ratio > 0.65
    ):
        confidence = CaptureConfidence.REJECT
    # Low confidence criteria:
    elif (
        metadata.fps < MIN_ACCEPTABLE_FPS
        or unstable_ratio > 0.30
        or not is_hd
        or has_excessive_blur
    ):
        confidence = CaptureConfidence.LOW
    # High confidence criteria:
    elif (
        metadata.duration_seconds >= 4.0
        and metadata.fps >= RECOMMENDED_FPS
        and is_hd
        and unstable_ratio <= 0.10
        and not has_excessive_blur
    ):
        confidence = CaptureConfidence.HIGH
    # Medium confidence fallback:
    else:
        confidence = CaptureConfidence.MEDIUM

    return QualityAssessment(
        confidence=confidence,
        issues=issues,
        camera_view="rear_or_diagonal_view",
        camera_stability_score=stability_score,
        unstable_frame_ratio=round(unstable_ratio, 3),
        # Downstream perception signals are populated dynamically by BadmintonPipeline:
        player_visibility=Metric(
            name="player_visibility",
            available=False,
            unavailable_reason="Uncomputed: Pending pose estimator execution."
        ),
        court_visibility=Metric(
            name="court_visibility",
            available=False,
            unavailable_reason="Uncomputed: Pending court calibration execution."
        ),
        racket_visibility=Metric(
            name="racket_visibility",
            available=False,
            unavailable_reason="Uncomputed: Pending racket tracker execution."
        ),
        shuttle_visibility=Metric(
            name="shuttle_visibility",
            available=False,
            unavailable_reason="Uncomputed: Pending shuttle tracker execution."
        )
    )
