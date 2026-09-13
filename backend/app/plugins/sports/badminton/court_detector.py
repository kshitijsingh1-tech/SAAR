"""
OpenCV-based Badminton Court Geometry and Metric Calibration Detector.
Computes real-world homography matrix using BWF standard court dimensions (13.40m x 6.10m).
Implements strict calibration gating with explicit rejection reasons when lines/corners are unresolvable.
"""
import math
from typing import List, Optional, Tuple, Dict, Any
import numpy as np
import cv2

from .schemas import CourtCalibration

# Official Badminton World Federation (BWF) Standard Court Dimensions (in meters)
COURT_LENGTH_M = 13.40  # Full baseline to baseline
COURT_WIDTH_M = 6.10    # Outer doubles sidelines
SINGLES_WIDTH_M = 5.18  # Inner singles sidelines
SHORT_SERVICE_DISTANCE_M = 1.98  # Distance from net to short service line


def get_court_dimensions(court_mode: str = "doubles") -> Tuple[float, float]:
    """Returns (width_m, length_m) dynamically based on singles or doubles mode."""
    if court_mode and court_mode.lower() == "singles":
        return SINGLES_WIDTH_M, COURT_LENGTH_M
    return COURT_WIDTH_M, COURT_LENGTH_M


def get_real_world_corners(court_mode: str = "doubles") -> np.ndarray:
    """Returns the 4 outer court corner metric coordinates in standard order [TL, TR, BR, BL]."""
    w, l = get_court_dimensions(court_mode)
    return np.array([
        [0.0, 0.0],
        [w, 0.0],
        [w, l],
        [0.0, l]
    ], dtype=np.float32)


# Default doubles corners reference
REAL_WORLD_COURT_CORNERS_M = get_real_world_corners("doubles")


def compute_reprojection_error(
    image_corners: np.ndarray,
    world_corners: np.ndarray,
    H_px_to_m: np.ndarray
) -> float:
    """
    Computes average reprojection error in pixels between detected image corners
    and reprojected metric court points via H^{-1} (metric to pixel).
    """
    try:
        H_m_to_px = np.linalg.inv(H_px_to_m)
        errors = []
        for i in range(len(world_corners)):
            m_pt = np.array([world_corners[i][0], world_corners[i][1], 1.0], dtype=np.float64)
            px_h = H_m_to_px @ m_pt
            if abs(px_h[2]) < 1e-7:
                return float("inf")
            reproj_px = np.array([px_h[0] / px_h[2], px_h[1] / px_h[2]])
            err = np.linalg.norm(image_corners[i] - reproj_px)
            errors.append(err)
        return float(round(np.mean(errors), 3))
    except Exception:
        return float("inf")


def project_court_lines(
    H_px_to_m: np.ndarray,
    court_mode: str = "doubles"
) -> Dict[str, Any]:
    """
    Projects standard BWF keypoint lines into image pixel space:
    - net_line: y = 6.70m across court width
    - short_service_lines: y = 4.72m and y = 8.68m
    - singles_boundary_corners: x = 0.46m and x = 5.64m (if doubles mode)
    """
    try:
        H_m_to_px = np.linalg.inv(H_px_to_m)
        w, l = get_court_dimensions(court_mode)

        def to_px(xm, ym):
            v = H_m_to_px @ np.array([xm, ym, 1.0], dtype=np.float64)
            return [round(float(v[0] / v[2]), 2), round(float(v[1] / v[2]), 2)]

        net_line = [to_px(0.0, l / 2.0), to_px(w, l / 2.0)]
        short_service_near = [to_px(0.0, (l / 2.0) - SHORT_SERVICE_DISTANCE_M), to_px(w, (l / 2.0) - SHORT_SERVICE_DISTANCE_M)]
        short_service_far = [to_px(0.0, (l / 2.0) + SHORT_SERVICE_DISTANCE_M), to_px(w, (l / 2.0) + SHORT_SERVICE_DISTANCE_M)]

        singles_boundaries = None
        if court_mode.lower() == "doubles":
            d_alley = (COURT_WIDTH_M - SINGLES_WIDTH_M) / 2.0  # 0.46m
            singles_boundaries = [
                to_px(d_alley, 0.0),
                to_px(COURT_WIDTH_M - d_alley, 0.0),
                to_px(COURT_WIDTH_M - d_alley, l),
                to_px(d_alley, l)
            ]

        return {
            "net_line": net_line,
            "short_service_lines": [short_service_near, short_service_far],
            "singles_boundary_corners": singles_boundaries
        }
    except Exception:
        return {}


def sort_quadrilateral_corners(pts: np.ndarray) -> np.ndarray:
    """
    Sorts 4 corner points into consistent order:
    [Top-Left, Top-Right, Bottom-Right, Bottom-Left].
    """
    # Sort points primarily by y-coordinate (top 2 vs bottom 2)
    sorted_by_y = pts[np.argsort(pts[:, 1])]
    top_two = sorted_by_y[:2]
    bottom_two = sorted_by_y[2:]

    # For top two: smaller x is top-left, larger x is top-right
    top_left = top_two[np.argmin(top_two[:, 0])]
    top_right = top_two[np.argmax(top_two[:, 0])]

    # For bottom two: smaller x is bottom-left, larger x is bottom-right
    bottom_left = bottom_two[np.argmin(bottom_two[:, 0])]
    bottom_right = bottom_two[np.argmax(bottom_two[:, 0])]

    return np.array([top_left, top_right, bottom_right, bottom_left], dtype=np.float32)


def line_intersection(
    p1: Tuple[float, float], p2: Tuple[float, float],
    p3: Tuple[float, float], p4: Tuple[float, float]
) -> Optional[Tuple[float, float]]:
    """Calculates the 2D intersection point of two infinite lines passing through p1-p2 and p3-p4."""
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4

    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-5:
        return None  # Parallel or coincident lines

    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denom
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denom
    return (float(px), float(py))


def cluster_points(points: List[Tuple[float, float]], dist_thresh: float = 30.0) -> List[Tuple[float, float]]:
    """Merges clustered intersection points within dist_thresh pixels of each other."""
    clusters: List[List[Tuple[float, float]]] = []
    for pt in points:
        assigned = False
        for c in clusters:
            cx = sum(p[0] for p in c) / len(c)
            cy = sum(p[1] for p in c) / len(c)
            if math.hypot(pt[0] - cx, pt[1] - cy) < dist_thresh:
                c.append(pt)
                assigned = True
                break
        if not assigned:
            clusters.append([pt])

    return [(sum(p[0] for p in c) / len(c), sum(p[1] for p in c) / len(c)) for c in clusters]


class BadmintonCourtDetector:
    """
    Detects badminton court boundary lines and estimates metric homography calibration.
    Does not assume a fixed camera view. Returns uncalibrated reason when geometry
    cannot be reliably established.
    """

    def __init__(self, min_line_length: int = 50, hough_threshold: int = 60):
        self.min_line_length = min_line_length
        self.hough_threshold = hough_threshold

    def detect_court(self, frame_bgr: np.ndarray, court_mode: str = "doubles") -> CourtCalibration:
        """
        Processes a single video frame (or keyframe) to detect court lines,
        extract the 4 outer perimeter corners, and compute the pixel-to-meter homography.
        """
        if frame_bgr is None or frame_bgr.size == 0:
            return CourtCalibration(
                is_calibrated=False,
                calibration_source=None,
                court_mode=court_mode,
                uncalibrated_reason="Empty or invalid image frame provided for court calibration.",
                confidence=0.0
            )

        h, w = frame_bgr.shape[:2]
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # 1. Canny edge detection
        edges = cv2.Canny(blurred, 50, 150, apertureSize=3)

        # 2. Probabilistic Hough Line Transform
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=self.hough_threshold,
            minLineLength=self.min_line_length,
            maxLineGap=30
        )

        if lines is None or len(lines) < 4:
            # Sensitive fallback pass for low-contrast courts or compressed mobile clips
            sensitive_edges = cv2.Canny(blurred, 30, 100, apertureSize=3)
            lines = cv2.HoughLinesP(
                sensitive_edges,
                rho=1,
                theta=np.pi / 180,
                threshold=max(35, self.hough_threshold - 20),
                minLineLength=max(30, self.min_line_length - 15),
                maxLineGap=45
            )

        if lines is None or len(lines) < 4:
            return CourtCalibration(
                is_calibrated=False,
                calibration_source=None,
                uncalibrated_reason=f"Insufficient court line visibility: only {len(lines) if lines is not None else 0} lines detected (minimum 4 required).",
                confidence=0.0
            )

        # 3. Classify lines into longitudinal (sidelines) vs transverse (baselines/net)
        transverse_lines = []
        longitudinal_lines = []

        lines_reshaped = lines.reshape(-1, 4)
        for x1, y1, x2, y2 in lines_reshaped:
            dx = float(x2 - x1)
            dy = float(y2 - y1)
            length = math.hypot(dx, dy)
            if length < self.min_line_length:
                continue

            angle_deg = abs(math.degrees(math.atan2(dy, dx)))
            # Transverse: near horizontal (0° or 180° +/- 35°)
            if angle_deg <= 35.0 or angle_deg >= 145.0:
                transverse_lines.append(((x1, y1), (x2, y2), length))
            # Longitudinal: near vertical or perspective angle (40° to 140°)
            elif 40.0 <= angle_deg <= 140.0:
                longitudinal_lines.append(((x1, y1), (x2, y2), length))

        if len(transverse_lines) < 2 or len(longitudinal_lines) < 2:
            return CourtCalibration(
                is_calibrated=False,
                calibration_source=None,
                uncalibrated_reason=(
                    f"Court lines do not span both axes: {len(transverse_lines)} transverse "
                    f"and {len(longitudinal_lines)} longitudinal lines detected (need >= 2 of each)."
                ),
                confidence=0.0
            )

        # Require at least one substantial boundary line in each direction (at least 20% of frame dimension)
        min_span = float(min(w, h)) * 0.20
        max_transverse = max(line[2] for line in transverse_lines)
        max_longitudinal = max(line[2] for line in longitudinal_lines)
        if max_transverse < min_span or max_longitudinal < min_span:
            return CourtCalibration(
                is_calibrated=False,
                calibration_source=None,
                uncalibrated_reason=(
                    f"Court lines lack sufficient span: longest transverse line is {max_transverse:.0f}px "
                    f"and longitudinal is {max_longitudinal:.0f}px (minimum {min_span:.0f}px required)."
                ),
                confidence=0.0
            )

        # 4. Compute intersections between transverse and longitudinal lines
        margin = max(80, int(0.35 * max(w, h)))
        intersections: List[Tuple[float, float]] = []
        for t_line in transverse_lines:
            for l_line in longitudinal_lines:
                pt = line_intersection(t_line[0], t_line[1], l_line[0], l_line[1])
                if pt is not None:
                    px, py = pt
                    if -margin <= px <= w + margin and -margin <= py <= h + margin:
                        intersections.append((px, py))

        unique_intersections = cluster_points(intersections, dist_thresh=30.0)

        if len(unique_intersections) < 4:
            return CourtCalibration(
                is_calibrated=False,
                calibration_source=None,
                uncalibrated_reason=(
                    f"Fewer than 4 outer corner points found: {len(unique_intersections)} "
                    "candidate line intersections formed."
                ),
                confidence=0.0
            )

        # 5. Extract the 4 extremal corners forming the largest convex quadrilateral
        pts_arr = np.array(unique_intersections, dtype=np.float32)
        hull = cv2.convexHull(pts_arr)
        hull_pts = hull.reshape(-1, 2)

        if len(hull_pts) < 4:
            return CourtCalibration(
                is_calibrated=False,
                calibration_source=None,
                uncalibrated_reason="Candidate corner points do not form a convex court quadrilateral.",
                confidence=0.0
            )

        # If convex hull has exactly 4 points, take them.
        # If > 4 points, approximate polygon or take 4 extremal corners (min/max sums and diffs)
        if len(hull_pts) == 4:
            candidate_corners = hull_pts
        else:
            # Approximate with Douglas-Peucker to find 4 dominant vertices
            epsilon = 0.05 * cv2.arcLength(hull, True)
            approx = cv2.approxPolyDP(hull, epsilon, True).reshape(-1, 2)
            if len(approx) == 4:
                candidate_corners = approx.astype(np.float32)
            else:
                # Fallback to 4 extremal points: top-left, top-right, bottom-right, bottom-left
                s = pts_arr.sum(axis=1)
                diff = np.diff(pts_arr, axis=1).flatten()
                tl = pts_arr[np.argmin(s)]
                br = pts_arr[np.argmax(s)]
                tr = pts_arr[np.argmin(diff)]
                bl = pts_arr[np.argmax(diff)]
                candidate_corners = np.array([tl, tr, br, bl], dtype=np.float32)

        sorted_corners = sort_quadrilateral_corners(candidate_corners)

        # Validate corners are inside visible or near-boundary frame bounds (up to 35% margin extrapolation)
        margin_x = float(w) * 0.35
        margin_y = float(h) * 0.35
        for pt in sorted_corners:
            if pt[0] < -margin_x or pt[0] > w + margin_x or pt[1] < -margin_y or pt[1] > h + margin_y:
                return CourtCalibration(
                    is_calibrated=False,
                    calibration_source=None,
                    uncalibrated_reason="Candidate court corners lie outside frame boundaries.",
                    confidence=0.0
                )

        # Validate convex quadrilateral
        int_corners = sorted_corners.reshape(-1, 1, 2).astype(np.int32)
        if not cv2.isContourConvex(int_corners):
            return CourtCalibration(
                is_calibrated=False,
                calibration_source=None,
                uncalibrated_reason="Candidate corner points do not form a strictly convex quadrilateral.",
                confidence=0.0
            )

        # Ensure valid area
        quad_area = cv2.contourArea(int_corners)
        image_area = float(w * h)

        if quad_area < 0.05 * image_area:
            return CourtCalibration(
                is_calibrated=False,
                calibration_source=None,
                uncalibrated_reason=(
                    f"Candidate court area ({quad_area:.0f}px) is too small relative to frame ({image_area:.0f}px); "
                    "likely detected an internal court box or background artifact."
                ),
                confidence=0.0
            )

        # 6. Compute Homography Matrix from Image Pixel Corners to Real-World Metric Court (Meters)
        world_corners = get_real_world_corners(court_mode)
        w_m, l_m = get_court_dimensions(court_mode)

        H_px_to_m, status = cv2.findHomography(
            sorted_corners,
            world_corners,
            method=cv2.RANSAC,
            ransacReprojThreshold=5.0
        )

        if H_px_to_m is None or np.isnan(H_px_to_m).any() or abs(np.linalg.det(H_px_to_m)) < 1e-12:
            return CourtCalibration(
                is_calibrated=False,
                calibration_source=None,
                court_mode=court_mode,
                uncalibrated_reason="Homography matrix computation failed or was singular/ill-conditioned.",
                confidence=0.0
            )

        reproj_err = compute_reprojection_error(sorted_corners, world_corners, H_px_to_m)
        lines_data = project_court_lines(H_px_to_m, court_mode)

        calib_confidence = min(1.0, float(round(0.4 + 0.1 * min(6, len(lines)), 2)))
        if reproj_err > 8.0:
            calib_confidence = min(calib_confidence, 0.40)

        corners_list = [[float(round(pt[0], 2)), float(round(pt[1], 2))] for pt in sorted_corners]
        h_matrix_list = [[float(round(val, 6)) for val in row] for row in H_px_to_m]

        return CourtCalibration(
            is_calibrated=True,
            calibration_source="opencv_hough_outer_corners",
            uncalibrated_reason=None if reproj_err <= 8.0 else f"High reprojection error ({reproj_err:.2f}px > 8.0px threshold).",
            court_mode=court_mode,
            corners_pixel=corners_list,
            court_dimensions_m=[w_m, l_m],
            homography_matrix=h_matrix_list,
            reprojection_error_px=reproj_err,
            net_keypoints_pixel=lines_data.get("net_line"),
            short_service_keypoints_pixel=lines_data.get("short_service_lines"),
            singles_boundary_corners_pixel=lines_data.get("singles_boundary_corners"),
            is_manual_override=False,
            confidence=calib_confidence
        )

    def calibrate_from_manual_corners(
        self,
        corners_pixel: List[List[float]],
        court_mode: str = "doubles"
    ) -> CourtCalibration:
        """
        Computes metric homography from user-provided manual court corner pixel annotations.
        Validates quadrilateral geometry, computes reprojection error, and projects internal keypoints.
        """
        if not corners_pixel or len(corners_pixel) != 4:
            return CourtCalibration(
                is_calibrated=False,
                calibration_source="manual_user_override",
                court_mode=court_mode,
                uncalibrated_reason="Manual calibration requires exactly 4 corner points [x, y].",
                confidence=0.0
            )

        pts_arr = np.array(corners_pixel, dtype=np.float32)
        sorted_corners = sort_quadrilateral_corners(pts_arr)

        int_corners = sorted_corners.reshape(-1, 1, 2).astype(np.int32)
        if not cv2.isContourConvex(int_corners):
            return CourtCalibration(
                is_calibrated=False,
                calibration_source="manual_user_override",
                court_mode=court_mode,
                uncalibrated_reason="Manual corner coordinates do not form a strictly convex quadrilateral.",
                confidence=0.0
            )

        w_m, l_m = get_court_dimensions(court_mode)
        world_corners = get_real_world_corners(court_mode)

        H_px_to_m, _ = cv2.findHomography(
            sorted_corners,
            world_corners,
            method=0  # Direct linear transformation for exact 4-point correspondence
        )

        if H_px_to_m is None or np.isnan(H_px_to_m).any() or abs(np.linalg.det(H_px_to_m)) < 1e-12:
            return CourtCalibration(
                is_calibrated=False,
                calibration_source="manual_user_override",
                court_mode=court_mode,
                uncalibrated_reason="Singular homography matrix from specified manual corners.",
                confidence=0.0
            )

        reproj_err = compute_reprojection_error(sorted_corners, world_corners, H_px_to_m)
        lines_data = project_court_lines(H_px_to_m, court_mode)

        confidence = 0.95 if reproj_err < 4.0 else (0.80 if reproj_err < 8.0 else 0.50)

        return CourtCalibration(
            is_calibrated=True,
            calibration_source="manual_user_override",
            uncalibrated_reason=None if reproj_err <= 8.0 else f"High reprojection error ({reproj_err:.2f}px).",
            court_mode=court_mode,
            corners_pixel=[[float(round(pt[0], 2)), float(round(pt[1], 2))] for pt in sorted_corners],
            court_dimensions_m=[w_m, l_m],
            homography_matrix=[[float(round(val, 6)) for val in row] for row in H_px_to_m],
            reprojection_error_px=reproj_err,
            net_keypoints_pixel=lines_data.get("net_line"),
            short_service_keypoints_pixel=lines_data.get("short_service_lines"),
            singles_boundary_corners_pixel=lines_data.get("singles_boundary_corners"),
            is_manual_override=True,
            confidence=confidence
        )


def pixel_to_court_m(
    px: float,
    py: float,
    homography_matrix: np.ndarray
) -> Optional[Tuple[float, float]]:
    """
    Projects a 2D image pixel coordinate [px, py] to real-world metric court coordinates [X_m, Y_m]
    using the calibrated 3x3 homography matrix.
    Returns None if homography is invalid or projection produces non-finite values.
    """
    if homography_matrix is None or homography_matrix.shape != (3, 3):
        return None

    pt_h = np.array([px, py, 1.0], dtype=np.float64)
    mapped_h = homography_matrix @ pt_h

    if abs(mapped_h[2]) < 1e-7:
        return None

    x_m = mapped_h[0] / mapped_h[2]
    y_m = mapped_h[1] / mapped_h[2]

    if math.isnan(x_m) or math.isnan(y_m) or math.isinf(x_m) or math.isinf(y_m):
        return None

    return (float(x_m), float(y_m))
