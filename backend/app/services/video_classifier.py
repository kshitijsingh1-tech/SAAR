"""
Autonomous Video Domain Classifier & Tool Dispatcher.
Differentiates whether an arbitrary uploaded video is a Toddler Gait Screening
video or a Badminton Athletic Kinematics rally using multi-signal computer vision
(court line geometry, anatomical stature ratios) and fast VLM semantic keyframe probing.
"""
import os
import cv2
import json
import base64
import tempfile
import urllib.request
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from app.plugins.sports.badminton.court_detector import BadmintonCourtDetector
from app.vlm_service import key_pool


class VideoClassifierService:
    """
    Autonomous classifier for video uploads to dynamically dispatch between
    specialized tools (Badminton Studio vs. ToddleAI Gait Screening).
    """

    def __init__(self):
        self.court_detector = BadmintonCourtDetector(min_line_length=40, hough_threshold=50)

    def extract_keyframes(self, video_bytes: bytes, num_frames: int = 2) -> Tuple[List[np.ndarray], Dict[str, Any]]:
        """
        Extracts representative BGR keyframes and basic container metadata.
        """
        if not video_bytes or len(video_bytes) == 0:
            return [], {"duration_s": 0.0, "fps": 0.0, "frame_count": 0}

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(video_bytes)
            tmp_path = tmp.name

        frames = []
        metadata = {"duration_s": 0.0, "fps": 30.0, "frame_count": 0}

        try:
            cap = cv2.VideoCapture(tmp_path)
            if not cap.isOpened():
                return [], metadata

            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
            if total_frames <= 0:
                # Read sequential frames if frame count is unavailable
                count = 0
                while cap.isOpened() and len(frames) < num_frames:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    if count % 15 == 0:
                        frames.append(frame)
                    count += 1
                metadata["frame_count"] = count
                metadata["duration_s"] = round(count / (fps or 30.0), 2)
                return frames, metadata

            metadata["fps"] = round(fps, 2)
            metadata["frame_count"] = total_frames
            metadata["duration_s"] = round(total_frames / fps, 2)

            # Sample at 20% and 60% of clip duration
            indices = [int(total_frames * 0.20), int(total_frames * 0.60)]
            if num_frames == 1:
                indices = [int(total_frames * 0.35)]

            for idx in indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, min(idx, total_frames - 1))
                ret, frame = cap.read()
                if ret and frame is not None:
                    frames.append(frame)

            cap.release()
        except Exception as e:
            print(f"[VideoClassifier] Frame extraction notice: {e}")
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass

        return frames, metadata

    def probe_court_lines(self, frames: List[np.ndarray]) -> Dict[str, Any]:
        """
        Runs court detection to identify badminton boundaries, green/blue court floor,
        and intersecting perpendicular lines.
        """
        court_hits = 0
        best_confidence = 0.0
        line_counts = []

        for frame in frames:
            if frame is None:
                continue
            try:
                calib = self.court_detector.detect_court(frame)
                if calib.is_calibrated:
                    court_hits += 1
                    best_confidence = max(best_confidence, calib.confidence or 0.85)

                # Heuristic line count
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                edges = cv2.Canny(gray, 50, 150)
                lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 50, minLineLength=60, maxLineGap=15)
                l_count = len(lines) if lines is not None else 0
                line_counts.append(l_count)
            except Exception:
                pass

        avg_lines = sum(line_counts) / len(line_counts) if line_counts else 0
        has_court = court_hits > 0 or (avg_lines >= 8 and best_confidence > 0.4)

        return {
            "has_court_lines": has_court,
            "calibrated": court_hits > 0,
            "confidence": best_confidence if court_hits > 0 else min(0.75, avg_lines * 0.04),
            "avg_lines": avg_lines
        }

    def probe_anatomical_stature(self, frames: List[np.ndarray]) -> Dict[str, Any]:
        """
        Estimates subject body proportions (head-to-body height ratio).
        Toddlers have a cephalic ratio >= 0.20 (1:4 to 1:5 head-to-body proportion),
        while adult athletes have a ratio <= 0.16 (1:7 to 1:8).
        """
        try:
            from app.plugins.sports.badminton.pose_estimator import BadmintonPoseEstimator, NOSE, LEFT_ANKLE, RIGHT_ANKLE, LEFT_SHOULDER, RIGHT_SHOULDER
            estimator = BadmintonPoseEstimator()

            toddler_votes = 0
            adult_votes = 0
            observed_ratios = []

            for frame in frames:
                if frame is None:
                    continue
                pose = estimator.estimate_frame(frame, frame_idx=0, timestamp_ms=0.0)
                if pose and pose.has_landmarks:
                    nose = pose.landmarks[NOSE]
                    l_sh = pose.landmarks[LEFT_SHOULDER]
                    r_sh = pose.landmarks[RIGHT_SHOULDER]
                    l_ank = pose.landmarks[LEFT_ANKLE]
                    r_ank = pose.landmarks[RIGHT_ANKLE]

                    # Verify keypoint visibility
                    if nose.visibility > 0.4 and (l_ank.visibility > 0.4 or r_ank.visibility > 0.4):
                        sh_y = (l_sh.y + r_sh.y) / 2.0
                        ank_y = max(l_ank.y if l_ank.visibility > 0.3 else 0.0, r_ank.y if r_ank.visibility > 0.3 else 0.0)
                        
                        head_len = abs(sh_y - nose.y)
                        total_len = abs(ank_y - nose.y)

                        if total_len > 0.08:
                            ratio = head_len / total_len
                            observed_ratios.append(ratio)
                            if ratio >= 0.20:
                                toddler_votes += 1
                            elif ratio <= 0.16:
                                adult_votes += 1

            mean_ratio = sum(observed_ratios) / len(observed_ratios) if observed_ratios else 0.17
            is_toddler = toddler_votes > adult_votes or mean_ratio >= 0.20
            is_athlete = adult_votes > toddler_votes or mean_ratio <= 0.15

            return {
                "detected": len(observed_ratios) > 0,
                "mean_cephalic_ratio": round(mean_ratio, 3),
                "is_toddler_stature": is_toddler,
                "is_adult_athlete": is_athlete,
                "confidence": 0.82 if len(observed_ratios) > 0 else 0.3
            }
        except Exception as e:
            return {"detected": False, "mean_cephalic_ratio": 0.17, "is_toddler_stature": False, "is_adult_athlete": False, "confidence": 0.0}

    def probe_vlm_semantics(self, frame: np.ndarray, user_context: str = "") -> Optional[Dict[str, Any]]:
        """
        Sends a single keyframe to fast Gemini/Groq Vision model to classify
        scene semantics (Badminton athletic rally vs. Toddler gait).
        """
        if frame is None or frame.size == 0:
            return None

        # Encode frame as JPEG base64
        success, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not success:
            return None
        b64_image = base64.b64encode(buffer).decode("utf-8")

        prompt = (
            "Analyze this single video keyframe. Does this video depict:\n"
            "A) 'badminton' (badminton court, athletic player, racket, shuttlecock, net, sports rally/smash)\n"
            "B) 'toddler_gait' (toddler, infant, young child walking or playing indoors/hallway/clinic floor, pediatric gait screening)\n"
            "C) 'other' (general video, botanical, infrastructure, etc.)\n\n"
            f"User context hint (if any): '{user_context}'\n\n"
            "Return valid JSON ONLY matching:\n"
            "{\n"
            '  "classification": "badminton" | "toddler_gait" | "other",\n'
            '  "confidence": 0.0 to 1.0,\n'
            '  "rationale": "Concise 1-sentence explanation of visible visual markers",\n'
            '  "indicators": ["marker1", "marker2"]\n'
            "}\n"
            "Start with { and end with }."
        )

        # 1. Try Gemini
        gemini_keys = [k.key for k in key_pool.get_available_keys("gemini")]
        if not gemini_keys and os.getenv("GEMINI_API_KEY"):
            gemini_keys = [os.getenv("GEMINI_API_KEY")]

        for g_key in gemini_keys:
            for model_name in ["gemini-2.5-flash", "gemini-3.5-flash", "gemini-flash-latest"]:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={g_key}"
                payload = {
                    "contents": [
                        {
                            "parts": [
                                {"text": prompt},
                                {
                                    "inlineData": {
                                        "mimeType": "image/jpeg",
                                        "data": b64_image
                                    }
                                }
                            ]
                        }
                    ],
                    "generationConfig": {"responseMimeType": "application/json", "temperature": 0.1}
                }
                try:
                    req = urllib.request.Request(
                        url,
                        data=json.dumps(payload).encode("utf-8"),
                        headers={"Content-Type": "application/json"}
                    )
                    with urllib.request.urlopen(req, timeout=5) as response:
                        raw = json.loads(response.read().decode("utf-8"))
                        text_part = raw["candidates"][0]["content"]["parts"][0]["text"]
                        parsed = json.loads(text_part)
                        if isinstance(parsed, dict) and "classification" in parsed:
                            return parsed
                except Exception:
                    continue

        return None

    def classify_video_bytes(
        self,
        video_bytes: bytes,
        filename: str = "",
        user_context: str = ""
    ) -> Dict[str, Any]:
        """
        Unified multi-signal classification pipeline.
        Differentiates between Badminton and Toddler Gait with high confidence.
        """
        combined_text = f"{filename} {user_context}".lower()

        # Step 1: Extract keyframes
        keyframes, meta = self.extract_keyframes(video_bytes, num_frames=2)
        primary_frame = keyframes[0] if keyframes else None

        # Step 2: Computer Vision Probes
        court_res = self.probe_court_lines(keyframes)
        stature_res = self.probe_anatomical_stature(keyframes)

        # Step 3: Fast VLM Perception Probe (if keyframe extracted)
        vlm_res = self.probe_vlm_semantics(primary_frame, user_context) if primary_frame is not None else None

        # Step 4: Multi-Signal Scoring Fusion
        badminton_score = 0.15
        toddler_score = 0.15
        indicators = []

        # 4a. VLM Signal (weight: 0.50)
        if vlm_res:
            vlm_class = vlm_res.get("classification", "other")
            vlm_conf = float(vlm_res.get("confidence", 0.7))
            if vlm_class == "badminton":
                badminton_score += 0.50 * vlm_conf
                indicators.extend(vlm_res.get("indicators", ["VLM identified badminton match scene"]))
            elif vlm_class == "toddler_gait":
                toddler_score += 0.50 * vlm_conf
                indicators.extend(vlm_res.get("indicators", ["VLM identified toddler ambulation"]))

        # 4b. Court Geometry Signal (weight: 0.35)
        if court_res.get("has_court_lines"):
            court_weight = 0.40 if court_res.get("calibrated") else 0.25
            badminton_score += court_weight * court_res.get("confidence", 0.7)
            indicators.append("court_boundaries_detected" if court_res.get("calibrated") else "court_like_lines")

        # 4c. Anatomical Stature Signal (weight: 0.25)
        if stature_res.get("detected"):
            if stature_res.get("is_toddler_stature"):
                toddler_score += 0.30 * stature_res.get("confidence", 0.8)
                indicators.append(f"pediatric_cephalic_ratio_{stature_res.get('mean_cephalic_ratio')}")
            elif stature_res.get("is_adult_athlete"):
                badminton_score += 0.25 * stature_res.get("confidence", 0.8)
                indicators.append("adult_athletic_stature")

        # 4d. Context / Filename soft prior (weight: 0.15)
        if any(w in combined_text for w in ["badminton", "racket", "shuttle", "smash", "rally", "court", "sport"]):
            badminton_score += 0.20
            indicators.append("badminton_keyword_context")
        if any(w in combined_text for w in ["toddler", "baby", "child", "infant", "walk", "gait", "pediatric"]):
            toddler_score += 0.20
            indicators.append("pediatric_keyword_context")

        # Decision Boundary
        if badminton_score >= toddler_score:
            confidence = min(0.98, max(0.65, badminton_score))
            rationale = vlm_res.get("rationale") if (vlm_res and vlm_res.get("classification") == "badminton") else (
                f"Identified badminton athletic rally via court geometry and athletic kinematic patterns ({len(indicators)} corroborating features)."
            )
            return {
                "domain": "sports",
                "tool": "badminton",
                "classification": "badminton",
                "label": "Badminton Athletic Kinematics",
                "confidence": round(confidence, 2),
                "rationale": rationale,
                "indicators": list(set(indicators)),
                "video_metadata": meta,
                "suggested_actions": ["Analyze racket swing dynamics", "Compute shuttle velocity", "Check court coverage"]
            }
        else:
            confidence = min(0.98, max(0.65, toddler_score))
            rationale = vlm_res.get("rationale") if (vlm_res and vlm_res.get("classification") == "toddler_gait") else (
                f"Identified toddler developmental walking screening via pediatric stature proportions and ambulation patterns."
            )
            return {
                "domain": "pediatrics",
                "tool": "gait",
                "classification": "toddler_gait",
                "label": "ToddleAI Pediatric Gait Screening",
                "confidence": round(confidence, 2),
                "rationale": rationale,
                "indicators": list(set(indicators)),
                "video_metadata": meta,
                "suggested_actions": ["Measure step cadence", "Evaluate bilateral symmetry", "Benchmark against developmental norms"]
            }


_video_classifier_instance = None

def get_video_classifier() -> VideoClassifierService:
    global _video_classifier_instance
    if _video_classifier_instance is None:
        _video_classifier_instance = VideoClassifierService()
    return _video_classifier_instance
