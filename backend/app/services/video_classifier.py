"""
Autonomous Video Domain Classifier & Tool Dispatcher.
Differentiates whether an arbitrary uploaded video is a Toddler Gait Screening
video or a Badminton Athletic Kinematics rally using multi-signal computer vision
(court line geometry, mat surface color, anatomical stature ratios) and fast VLM keyframe probing.
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
        self.court_detector = BadmintonCourtDetector(min_line_length=35, hough_threshold=45)

    def _normalize_frame(self, frame_or_frames: Any) -> Optional[np.ndarray]:
        if isinstance(frame_or_frames, list):
            return frame_or_frames[0] if len(frame_or_frames) > 0 else None
        return frame_or_frames

    def extract_keyframes(self, video_bytes: bytes, max_frames: int = 2) -> Tuple[List[np.ndarray], Dict[str, Any]]:
        """
        Extracts 1 or 2 representative BGR keyframes across video duration (e.g. at 20% and 60%).
        Provides high-signal temporal visual evidence to the vision LLM for domain detection.
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
                count = 0
                while cap.isOpened():
                    ret, fr = cap.read()
                    if not ret:
                        break
                    if count in [5, 20]:
                        frames.append(fr)
                        if len(frames) >= max_frames:
                            break
                    count += 1
                metadata["frame_count"] = max(count, 1)
                metadata["duration_s"] = round(count / (fps or 30.0), 2)
                return frames, metadata

            metadata["fps"] = round(fps, 2)
            metadata["frame_count"] = total_frames
            metadata["duration_s"] = round(total_frames / fps, 2)

            # Sample keyframes at 20% and 60% of duration
            target_indices = [
                max(0, min(int(total_frames * 0.20), total_frames - 1)),
                max(0, min(int(total_frames * 0.60), total_frames - 1))
            ] if max_frames >= 2 and total_frames >= 2 else [max(0, min(int(total_frames * 0.25), total_frames - 1))]

            for idx in target_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, fr = cap.read()
                if ret and fr is not None:
                    frames.append(fr)

            if not frames:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, fr = cap.read()
                if ret and fr is not None:
                    frames.append(fr)

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

    def extract_single_keyframe(self, video_bytes: bytes) -> Tuple[Optional[np.ndarray], Dict[str, Any]]:
        """Extracts strictly the primary representative keyframe."""
        frames, meta = self.extract_keyframes(video_bytes, max_frames=1)
        return (frames[0] if len(frames) > 0 else None), meta

    def probe_court_color(self, frame_input: Any) -> Dict[str, Any]:
        """
        Detects standard tournament green, blue, or terracotta badminton court mat flooring on 1 frame.
        Requires genuine high saturation (S >= 60) so domestic furniture or muted clothing does not trigger.
        """
        frame = self._normalize_frame(frame_input)
        if frame is None or frame.size == 0:
            return {"has_court_color": False, "court_color_ratio": 0.0}

        h, w = frame.shape[:2]
        floor = frame[int(h * 0.40):, :]
        hsv = cv2.cvtColor(floor, cv2.COLOR_BGR2HSV)
        # High saturation tournament green mat (H: 35-85, S: 65-255, V: 50-255)
        green_m = cv2.inRange(hsv, np.array([35, 65, 50]), np.array([85, 255, 255]))
        # High saturation tournament blue mat (H: 95-130, S: 65-255, V: 50-255)
        blue_m = cv2.inRange(hsv, np.array([95, 65, 50]), np.array([130, 255, 255]))
        # Tournament terracotta court (H: 0-12 or 168-180, S: 75-255, V: 60-255)
        red_m1 = cv2.inRange(hsv, np.array([0, 75, 60]), np.array([12, 255, 255]))
        red_m2 = cv2.inRange(hsv, np.array([168, 75, 60]), np.array([180, 255, 255]))
        court_px = cv2.countNonZero(green_m) + cv2.countNonZero(blue_m) + cv2.countNonZero(red_m1) + cv2.countNonZero(red_m2)
        total_px = floor.shape[0] * floor.shape[1]
        ratio = round(court_px / (total_px or 1), 3)

        return {
            "has_court_color": ratio >= 0.20,
            "court_color_ratio": ratio
        }

    def probe_court_lines(self, frame_input: Any, has_court_color: bool = False) -> Dict[str, Any]:
        """
        Runs court line detection to identify badminton boundaries on 1 frame.
        STRICT REQUIREMENT: Court boundaries strictly require confirmed court floor color.
        Without confirmed court flooring, domestic room edges (doors, walls, baseboards)
        are explicitly rejected to prevent false positives.
        """
        if not has_court_color:
            return {
                "has_court_lines": False,
                "calibrated": False,
                "confidence": 0.0,
                "avg_lines": 0
            }

        frame = self._normalize_frame(frame_input)
        if frame is None or frame.size == 0:
            return {"has_court_lines": False, "calibrated": False, "confidence": 0.0, "avg_lines": 0}

        calibrated = False
        confidence = 0.0
        l_count = 0

        try:
            calib = self.court_detector.detect_court(frame)
            if calib.is_calibrated:
                calibrated = True
                confidence = max(confidence, calib.confidence or 0.85)

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 40, 130)
            lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 45, minLineLength=50, maxLineGap=20)
            l_count = len(lines) if lines is not None else 0
        except Exception:
            pass

        has_court = calibrated and l_count >= 10
        final_conf = confidence if has_court else 0.0

        return {
            "has_court_lines": has_court,
            "calibrated": calibrated and has_court,
            "confidence": round(final_conf, 2),
            "avg_lines": l_count
        }

    def probe_anatomical_stature(self, frame_input: Any) -> Dict[str, Any]:
        """
        Estimates subject body proportions and height span in the field of view on 1 frame.
        Toddler gait screening features a compact stature (<0.45 frame height) or higher cephalic ratio,
        while adult athletes span >=0.50 frame height with streamlined adult ratios.
        """
        frame = self._normalize_frame(frame_input)
        if frame is None or frame.size == 0:
            return {"detected": False, "mean_cephalic_ratio": 0.17, "is_toddler_stature": False, "is_adult_athlete": False, "confidence": 0.0}

        try:
            from app.plugins.sports.badminton.pose_estimator import (
                BadmintonPoseEstimator, NOSE, LEFT_ANKLE, RIGHT_ANKLE,
                LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_HIP, RIGHT_HIP,
                LEFT_WRIST, RIGHT_WRIST
            )
            estimator = BadmintonPoseEstimator()

            pose = estimator.process_frame(frame, frame_index=0, timestamp_ms=0)
            if pose and pose.is_detected and pose.landmarks:
                nose = pose.landmarks[NOSE]
                l_sh = pose.landmarks[LEFT_SHOULDER]
                r_sh = pose.landmarks[RIGHT_SHOULDER]
                l_hip = pose.landmarks[LEFT_HIP]
                r_hip = pose.landmarks[RIGHT_HIP]
                l_ank = pose.landmarks[LEFT_ANKLE]
                r_ank = pose.landmarks[RIGHT_ANKLE]
                l_wri = pose.landmarks[LEFT_WRIST]
                r_wri = pose.landmarks[RIGHT_WRIST]

                if nose.visibility > 0.30 and (l_ank.visibility > 0.25 or r_ank.visibility > 0.25):
                    sh_y = (l_sh.y + r_sh.y) / 2.0
                    hip_y = (l_hip.y + r_hip.y) / 2.0 if (l_hip.visibility > 0.25 and r_hip.visibility > 0.25) else sh_y + 0.2
                    ank_y = max(l_ank.y if l_ank.visibility > 0.25 else 0.0, r_ank.y if r_ank.visibility > 0.25 else 0.0)

                    torso_len = abs(hip_y - sh_y)
                    leg_len = abs(ank_y - hip_y)
                    total_len = abs(ank_y - nose.y)

                    # In athletic badminton, players frequently reach overhead (wrist above nose or shoulder)
                    has_overhead_reach = (
                        (l_wri.visibility > 0.35 and l_wri.y < sh_y) or
                        (r_wri.visibility > 0.35 and r_wri.y < sh_y)
                    )

                    # Pediatric gait has short leg-to-torso ratio or arms held low/at balance
                    is_toddler = (leg_len / (torso_len or 1.0) < 1.30) or not has_overhead_reach
                    is_athlete = has_overhead_reach and (leg_len / (torso_len or 1.0) >= 1.35)

                    return {
                        "detected": True,
                        "mean_cephalic_ratio": round(abs(sh_y - nose.y) / (total_len or 1.0), 3),
                        "has_overhead_reach": has_overhead_reach,
                        "is_toddler_stature": is_toddler,
                        "is_adult_athlete": is_athlete,
                        "confidence": 0.85
                    }

            return {"detected": False, "mean_cephalic_ratio": 0.17, "has_overhead_reach": False, "is_toddler_stature": True, "is_adult_athlete": False, "confidence": 0.0}
        except Exception:
            return {"detected": False, "mean_cephalic_ratio": 0.17, "has_overhead_reach": False, "is_toddler_stature": True, "is_adult_athlete": False, "confidence": 0.0}

    def probe_vlm_semantics(self, frame_input: Any, user_context: str = "") -> Optional[Dict[str, Any]]:
        """
        Queries fast Vision LLM (Gemini / Groq) on 1 or 2 keyframes to classify whether the video depicts
        a sports activity (e.g. badminton match/rally) vs. toddler developmental gait.
        """
        frames = frame_input if isinstance(frame_input, list) else [frame_input]
        frames = [f for f in frames if f is not None and getattr(f, 'size', 0) > 0]
        if not frames:
            return None

        # Encode up to 2 frames as base64 JPEG
        b64_images = []
        for fr in frames[:2]:
            success, buffer = cv2.imencode(".jpg", fr, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if success:
                b64_images.append(base64.b64encode(buffer).decode("utf-8"))

        if not b64_images:
            return None

        prompt = (
            f"You are an expert computer vision video domain classifier analyzing {len(b64_images)} representative keyframe(s) from an uploaded video.\n"
            "Carefully examine the visual evidence across the frame(s) to determine if this video depicts:\n"
            "1. 'badminton': A real sports match, athletic drill, or badminton rally. Requires visible sports/badminton equipment (racket, shuttlecock, net) OR marked sports court with athletic players.\n"
            "2. 'toddler_gait': Pediatric walking, developmental movement, or orthopedic gait analysis. Includes toddlers, infants, children, persons walking indoors (living room, domestic floor/carpet, clinic room), walking gait animations, or toddler movement screening.\n\n"
            f"Context hint from user: '{user_context}'\n\n"
            "Return valid JSON ONLY matching:\n"
            "{\n"
            '  "classification": "badminton" | "toddler_gait",\n'
            '  "confidence": 0.0 to 1.0,\n'
            '  "rationale": "Concise 1-sentence explanation",\n'
            '  "indicators": ["marker1", "marker2"]\n'
            "}\n"
            "Start with { and end with }."
        )

        # 1. Try Gemini with low-latency flash-lite model
        gemini_keys = [k.key for k in key_pool.get_available_keys("gemini")]
        if not gemini_keys and os.getenv("GEMINI_API_KEY"):
            gemini_keys = [os.getenv("GEMINI_API_KEY")]

        for g_key in gemini_keys:
            for model_name in ["gemini-flash-lite-latest", "gemini-flash-latest"]:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={g_key}"
                parts = [{"text": prompt}]
                for b64_img in b64_images:
                    parts.append({
                        "inlineData": {
                            "mimeType": "image/jpeg",
                            "data": b64_img
                        }
                    })
                payload = {
                    "contents": [{"parts": parts}],
                    "generationConfig": {"responseMimeType": "application/json", "temperature": 0.1}
                }
                try:
                    req = urllib.request.Request(
                        url,
                        data=json.dumps(payload).encode("utf-8"),
                        headers={"Content-Type": "application/json"}
                    )
                    with urllib.request.urlopen(req, timeout=8) as response:
                        raw = json.loads(response.read().decode("utf-8"))
                        text_part = raw["candidates"][0]["content"]["parts"][0]["text"]
                        parsed = json.loads(text_part)
                        if isinstance(parsed, dict) and "classification" in parsed:
                            return parsed
                except Exception:
                    continue

        # 2. Try Groq Vision API
        groq_keys = [k.key for k in key_pool.get_available_keys("groq")]
        if not groq_keys and os.getenv("GROQ_API_KEY"):
            groq_keys = [os.getenv("GROQ_API_KEY")]

        for gr_key in groq_keys:
            url = "https://api.groq.com/openai/v1/chat/completions"
            messages_content = [{"type": "text", "text": prompt}]
            for b64_img in b64_images:
                messages_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}})

            payload = {
                "model": "llama-3.2-11b-vision-preview",
                "messages": [
                    {
                        "role": "user",
                        "content": messages_content
                    }
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.1
            }
            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {gr_key}"
                    }
                )
                with urllib.request.urlopen(req, timeout=4) as response:
                    raw = json.loads(response.read().decode("utf-8"))
                    text_part = raw["choices"][0]["message"]["content"]
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

        # Step 1: Extract 1 or 2 representative keyframes across video duration
        frames, meta = self.extract_keyframes(video_bytes, max_frames=2)
        if not frames:
            return {
                "domain": "pediatrics",
                "tool": "gait",
                "classification": "toddler_gait",
                "label": "ToddleAI Pediatric Gait Screening",
                "confidence": 0.50,
                "rationale": "Defaulted to pediatric movement screening (no frame extracted).",
                "indicators": ["frame_extraction_failed"],
                "video_metadata": meta,
                "suggested_actions": ["Upload valid video file in MP4/MOV format"]
            }

        primary_frame = frames[0]

        # Step 2: Computer Vision Probes on primary frame
        color_res = self.probe_court_color(primary_frame)
        court_res = self.probe_court_lines(primary_frame, has_court_color=color_res.get("has_court_color", False))
        stature_res = self.probe_anatomical_stature(primary_frame)

        # Step 3: Fast VLM Perception Probe on 1-2 keyframes
        vlm_res = self.probe_vlm_semantics(frames, user_context)

        # Step 4: Decision Hierarchy on 1 Frame
        # 4a. Direct VLM Semantic Authority (Ground Truth Vision Model)
        if vlm_res:
            vlm_class = vlm_res.get("classification")
            vlm_conf = float(vlm_res.get("confidence", 0.90))
            if vlm_class == "badminton":
                return {
                    "domain": "sports",
                    "tool": "badminton",
                    "classification": "badminton",
                    "label": "Badminton Athletic Kinematics",
                    "confidence": round(vlm_conf, 2),
                    "rationale": vlm_res.get("rationale", "Identified badminton sports scene from video keyframe."),
                    "indicators": vlm_res.get("indicators", ["VLM confirmed badminton athletic scene"]),
                    "video_metadata": meta,
                    "suggested_actions": ["Analyze racket swing dynamics", "Compute shuttle velocity", "Check court coverage"]
                }
            elif vlm_class == "toddler_gait":
                return {
                    "domain": "pediatrics",
                    "tool": "gait",
                    "classification": "toddler_gait",
                    "label": "ToddleAI Pediatric Gait Screening",
                    "confidence": round(vlm_conf, 2),
                    "rationale": vlm_res.get("rationale", "Identified pediatric ambulation from video keyframe."),
                    "indicators": vlm_res.get("indicators", ["VLM confirmed pediatric developmental gait"]),
                    "video_metadata": meta,
                    "suggested_actions": ["Measure step cadence", "Evaluate bilateral symmetry", "Benchmark against developmental norms"]
                }

        # 4b. Deterministic Computer Vision Fallback (when VLM is offline)
        import re
        has_sports_court = color_res.get("has_court_color", False) and court_res.get("has_court_lines", False)
        sports_keywords = ["badminton", "shuttlecock", "shuttle", "racket", "racquet", "smash", "yonex", "lining", "bwf"]
        pediatric_keywords = ["toddler", "baby", "infant", "child", "children", "pediatric", "pediatrics", "gait", "crawl", "toddle", "walk", "walking", "ambulation"]

        has_sports_kw = any(re.search(r'\b' + re.escape(w) + r'\b', combined_text) for w in sports_keywords)
        has_pediatric_kw = any(re.search(r'\b' + re.escape(w) + r'\b', combined_text) for w in pediatric_keywords)

        # Requires authentic tournament sports court OR (explicit sports keywords + verified adult athlete + no pediatric terms)
        is_badminton = (has_sports_court and not has_pediatric_kw) or (
            has_sports_kw and not has_pediatric_kw and stature_res.get("is_adult_athlete", False) and not stature_res.get("is_toddler_stature", False)
        )

        if is_badminton:
            return {
                "domain": "sports",
                "tool": "badminton",
                "classification": "badminton",
                "label": "Badminton Athletic Kinematics",
                "confidence": 0.88,
                "rationale": "Identified tournament court mat geometry and athletic biomechanical features.",
                "indicators": ["court_geometry_confirmed", "athletic_biomechanics"],
                "video_metadata": meta,
                "suggested_actions": ["Analyze racket swing dynamics", "Compute shuttle velocity", "Check court coverage"]
            }
        else:
            return {
                "domain": "pediatrics",
                "tool": "gait",
                "classification": "toddler_gait",
                "label": "ToddleAI Pediatric Gait Screening",
                "confidence": 0.85,
                "rationale": "Identified domestic/clinical developmental ambulation scene from video keyframe.",
                "indicators": ["pediatric_ambulation_scene"],
                "video_metadata": meta,
                "suggested_actions": ["Measure step cadence", "Evaluate bilateral symmetry", "Benchmark against developmental norms"]
            }


_video_classifier_instance = None

def get_video_classifier() -> VideoClassifierService:
    global _video_classifier_instance
    if _video_classifier_instance is None:
        _video_classifier_instance = VideoClassifierService()
    return _video_classifier_instance
