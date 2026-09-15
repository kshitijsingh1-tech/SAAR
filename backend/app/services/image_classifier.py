"""
Autonomous Image Domain Classifier & Dispatcher for SAAR.
Inspects custom uploaded or pasted images to accurately resolve scientific domain:
- 'agriculture' (botanical, plants, roses, flowers, crops, leaves, soil, pathologies)
- 'infrastructure' (roads, pavement, asphalt, culverts, cracks, concrete, bridges)
- 'astronomy' (stars, exoplanet transits, celestial bodies, light curves, spectra)
- 'sports' (human athletes, badminton, tennis, rackets, courts, kinematics)
- 'pediatrics' (toddlers, infants, pediatric gait, developmental posture)
Prevents cross-domain contamination when lingering session state or generic filenames
(e.g. pasted_evidence_*.png) are submitted.
"""
import os
import re
import json
import base64
import urllib.request
from typing import Dict, Any, Optional, Tuple

from app.vlm_service import key_pool


class ImageClassifierService:
    """Classifies visual domain for images using VLM probing with deterministic fallback."""

    DOMAINS = ["agriculture", "infrastructure", "astronomy", "sports", "pediatrics"]

    def classify_image(self, image_data_or_url: str, user_text: Optional[str] = None) -> Dict[str, Any]:
        """
        Classifies the domain of an image.
        Returns: {"domain": str, "confidence": float, "description": str, "method": str}
        """
        if not image_data_or_url:
            return {
                "domain": "agriculture",
                "confidence": 0.5,
                "description": "Default domain (no image provided)",
                "method": "default"
            }

        # 1. Text-based heuristic bypass if strong domain keywords exist in text
        if user_text:
            t = user_text.lower()
            if any(w in t for w in ["rose", "plant", "leaf", "flower", "crop", "cutting", "graft", "chlorosis", "botanical"]):
                return {"domain": "agriculture", "confidence": 0.98, "description": "Botanical keywords in user text", "method": "text_heuristic"}
            if any(w in t for w in ["road", "asphalt", "pavement", "crack", "culvert", "gpr", "bridge"]):
                return {"domain": "infrastructure", "confidence": 0.98, "description": "Infrastructure keywords in user text", "method": "text_heuristic"}
            if any(w in t for w in ["transit", "star", "exoplanet", "lightcurve", "telescope", "orbit"]):
                return {"domain": "astronomy", "confidence": 0.98, "description": "Astronomy keywords in user text", "method": "text_heuristic"}
            if any(w in t for w in ["badminton", "smash", "racket", "shuttle", "rally", "court"]):
                return {"domain": "sports", "confidence": 0.98, "description": "Sports keywords in user text", "method": "text_heuristic"}
            if any(w in t for w in ["toddler", "child", "infant", "pediatric"]):
                return {"domain": "pediatrics", "confidence": 0.98, "description": "Pediatric keywords in user text", "method": "text_heuristic"}

        # 2. Extract image bytes
        img_bytes, mime_type = self._extract_image_bytes(image_data_or_url)
        if not img_bytes:
            return {
                "domain": "agriculture",
                "confidence": 0.5,
                "description": "Unable to decode image bytes",
                "method": "fallback"
            }

        # 3. Fast Multimodal Classification via Gemini
        gemini_result = self._classify_with_gemini(img_bytes, mime_type)
        if gemini_result and gemini_result.get("domain") in self.DOMAINS:
            return gemini_result

        # 4. Fallback: Fast Multimodal Classification via Groq
        groq_result = self._classify_with_groq(img_bytes, mime_type)
        if groq_result and groq_result.get("domain") in self.DOMAINS:
            return groq_result

        # 5. Deterministic visual fallback (Color histograms / Dominant spectrum)
        return self._heuristic_color_classifier(img_bytes)

    def _extract_image_bytes(self, img_input: str) -> Tuple[Optional[bytes], str]:
        if img_input.startswith("data:image"):
            try:
                header, encoded = img_input.split(",", 1)
                mime_match = re.search(r"data:(image/\w+);", header)
                mime = mime_match.group(1) if mime_match else "image/jpeg"
                return base64.b64decode(encoded), mime
            except Exception:
                return None, "image/jpeg"
        elif img_input.startswith("http://") or img_input.startswith("https://"):
            try:
                req = urllib.request.Request(img_input, headers={"User-Agent": "SaarClassifier/1.0"})
                with urllib.request.urlopen(req, timeout=4) as resp:
                    return resp.read(), "image/jpeg"
            except Exception:
                return None, "image/jpeg"
        elif os.path.exists(img_input):
            try:
                with open(img_input, "rb") as f:
                    mime = "image/png" if img_input.endswith(".png") else "image/jpeg"
                    return f.read(), mime
            except Exception:
                return None, "image/jpeg"
        return None, "image/jpeg"

    def _classify_with_gemini(self, img_bytes: bytes, mime_type: str) -> Optional[Dict[str, Any]]:
        keys = [k.key for k in key_pool.get_available_keys("gemini")]
        if not keys and os.getenv("GEMINI_API_KEY"):
            keys = [os.getenv("GEMINI_API_KEY")]

        if not keys:
            return None

        b64 = base64.b64encode(img_bytes).decode("utf-8")
        prompt = (
            "Classify the scientific domain of this image into exactly one of: "
            "[agriculture, infrastructure, astronomy, sports, pediatrics].\n"
            "- agriculture: plants, roses, flowers, crops, leaves, cutting, graft, soil, botany, greenhouse.\n"
            "- infrastructure: roads, asphalt, pavement, cracks, culverts, bridges, concrete.\n"
            "- astronomy: stars, galaxies, planets, sky, telescopes, spectra, space.\n"
            "- sports: human athletes, badminton, tennis, athletic kinematics, rackets, gym.\n"
            "- pediatrics: toddlers, infants, children, gait development.\n\n"
            "Return valid JSON only:\n"
            "{\"domain\": \"agriculture|infrastructure|astronomy|sports|pediatrics\", \"confidence\": 0.95, \"description\": \"brief summary\"}"
        )

        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inlineData": {"mimeType": mime_type, "data": b64}}
                ]
            }],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.1}
        }

        for model_name in ["gemini-flash-lite-latest", "gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-flash-latest"]:
            for key in keys:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
                try:
                    req = urllib.request.Request(
                        url,
                        data=json.dumps(payload).encode("utf-8"),
                        headers={"Content-Type": "application/json"}
                    )
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                        parsed = json.loads(text)
                        parsed["method"] = f"gemini_{model_name}"
                        key_pool.record_success("gemini", key)
                        return parsed
                except urllib.error.HTTPError as e:
                    err_body = e.read().decode("utf-8", errors="ignore")
                    if e.code == 429 or "RESOURCE_EXHAUSTED" in err_body or "rate limit" in err_body.lower() or "quota" in err_body.lower():
                        key_pool.record_quota_exhausted("gemini", key, cooldown_sec=180.0)
                        break
                    continue
                except Exception:
                    continue
        return None

    def _classify_with_groq(self, img_bytes: bytes, mime_type: str) -> Optional[Dict[str, Any]]:
        groq_keys = [k.key for k in key_pool.get_available_keys("groq")]
        if not groq_keys and os.getenv("GROQ_API_KEY"):
            groq_keys = [os.getenv("GROQ_API_KEY")]

        if not groq_keys:
            return None

        b64 = base64.b64encode(img_bytes).decode("utf-8")
        url = "https://api.groq.com/openai/v1/chat/completions"

        prompt = (
            "Classify the scientific domain of this image into exactly one of: "
            "[agriculture, infrastructure, astronomy, sports, pediatrics]. "
            "Return JSON: {\"domain\": \"...\", \"confidence\": 0.95, \"description\": \"...\"}"
        )

        for g_key in groq_keys:
            payload = {
                "model": "llama-3.2-11b-vision-preview",
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}}
                    ]
                }],
                "response_format": {"type": "json_object"},
                "temperature": 0.1,
                "max_tokens": 150
            }
            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json", "Authorization": f"Bearer {g_key}"}
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    text = data["choices"][0]["message"]["content"].strip()
                    parsed = json.loads(text)
                    parsed["method"] = "groq_vision"
                    return parsed
            except Exception:
                continue
        return None

    def _heuristic_color_classifier(self, img_bytes: bytes) -> Dict[str, Any]:
        """Deterministic RGB distribution fallback if all remote vision calls are offline."""
        try:
            import cv2
            import numpy as np
            arr = np.frombuffer(img_bytes, dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is not None:
                hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                # Green foliage mask (agriculture)
                green_mask = cv2.inRange(hsv, (25, 40, 40), (85, 255, 255))
                # Red / rose floral mask
                red_mask1 = cv2.inRange(hsv, (0, 70, 50), (10, 255, 255))
                red_mask2 = cv2.inRange(hsv, (170, 70, 50), (180, 255, 255))
                floral_red = cv2.bitwise_or(red_mask1, red_mask2)

                green_ratio = np.sum(green_mask > 0) / (img.shape[0] * img.shape[1])
                red_ratio = np.sum(floral_red > 0) / (img.shape[0] * img.shape[1])

                if green_ratio > 0.15 or red_ratio > 0.08 or (green_ratio + red_ratio) > 0.20:
                    return {
                        "domain": "agriculture",
                        "confidence": 0.82,
                        "description": "Botanical foliar/floral chromatic spectrum detected",
                        "method": "chromatic_histogram_green_flora"
                    }

                # Dark asphalt / pavement (infrastructure)
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                std_dev = np.std(gray)
                mean_val = np.mean(gray)
                if 50 < mean_val < 160 and std_dev < 40:
                    return {
                        "domain": "infrastructure",
                        "confidence": 0.75,
                        "description": "Low-variance gray planar texture indicative of asphalt pavement",
                        "method": "chromatic_histogram_asphalt"
                    }
        except Exception:
            pass

        return {
            "domain": "agriculture",
            "confidence": 0.60,
            "description": "General scientific domain fallback",
            "method": "default_fallback"
        }


# Singleton instance
image_classifier = ImageClassifierService()
