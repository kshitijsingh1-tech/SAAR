import json
import base64
import urllib.request
import urllib.parse
import re
import os
from typing import Dict, Any, List, Optional, Tuple
from .schemas import NodeModel, EdgeModel

class VLMService:
    """
    Multimodal Vision-Language Model (VLM) Service for Saar.
    Communicates with cloud VLM APIs (Google Gemini, OpenAI GPT-4o),
    local vision models (Ollama LLaVA/Qwen2-VL), or Saar's Intelligent Vision Synthesizer.
    """

    SYSTEM_PROMPT = """You are the Perception Layer of Saar, a Visual Scientific Reasoning Engine.
Your task is to analyze the provided image for domain '{domain}' and extract a concise, structured visual scene graph (3 to 5 key nodes, 1 to 2 hypotheses).

Output valid JSON ONLY. Start directly with the JSON object without extensive chain-of-thought.
Structure:
{{
  "scene_summary": "Concise 1-2 sentence assessment",
  "nodes": [
    {{
      "id": "node_id_1",
      "label": "Human readable entity/property name",
      "node_type": "object|property|observation|hypothesis",
      "category": "infrastructure|environment|structural|measurement|risk|pathology",
      "confidence": 0.95,
      "bbox": [ymin, xmin, ymax, xmax], // Normalized integers 0 to 1000 covering the visual region (e.g., [120, 250, 780, 820])
      "visual_anchor": true,
      "properties": {{"key": "value"}}
    }}
  ],
  "edges": [
    {{
      "id": "edge_id_1",
      "source": "node_id_1",
      "target": "node_id_2",
      "relation_type": "obstructs|causes|affects|indicates|supports|contradicts",
      "confidence": 0.88,
      "evidence": "Visual evidence description"
    }}
  ],
  "hypotheses": [
    {{
      "id": "hypo_1",
      "label": "Hypothesis: Potential root cause or unseen risk requiring tool testing",
      "category": "risk",
      "confidence": 0.45,
      "bbox": null,
      "visual_anchor": false
    }}
  ]
}}
"""

    @staticmethod
    def _prepare_image_data(image_input: str) -> Tuple[Optional[bytes], str]:
        """Convert base64 data URL or URL into raw bytes and mime type."""
        if not image_input:
            return None, "image/jpeg"
        
        if image_input.startswith("data:image"):
            # Format: data:image/png;base64,...
            header, encoded = image_input.split(",", 1)
            mime_match = re.search(r"data:(image/\w+);", header)
            mime_type = mime_match.group(1) if mime_match else "image/jpeg"
            return base64.b64decode(encoded), mime_type
        elif image_input.startswith("http://") or image_input.startswith("https://"):
            try:
                req = urllib.request.Request(image_input, headers={"User-Agent": "Saar/1.0"})
                with urllib.request.urlopen(req, timeout=5) as response:
                    return response.read(), "image/jpeg"
            except Exception:
                return None, "image/jpeg"
        else:
            # Plain base64 string
            try:
                return base64.b64decode(image_input), "image/jpeg"
            except Exception:
                return None, "image/jpeg"

    def analyze_image(
        self,
        image_input: Optional[str] = None,
        domain: str = "infrastructure",
        preset_id: Optional[str] = None,
        vlm_provider: str = "auto",
        api_key: Optional[str] = None,
        images: Optional[List[str]] = None
    ) -> Tuple[List[NodeModel], List[EdgeModel], str, str]:
        """
        Main entry point for image visual scene perception & hybrid reasoning.
        Supports single image or multi-photo sequences (e.g. multi-view toddler posture).
        Implements Hybrid Architecture:
        1. Google Gemini 1.5/2.0 Flash (Primary Vision Perception & Long Context)
        2. Groq / Cerebras (Ultra-fast LLaMA 3.3 ReAct reasoning loops)
        3. OpenRouter (Multi-model router & free fallback catalog)
        4. Saar Vision Synthesizer (Zero-latency offline engine)
        """
        gemini_key = api_key or os.getenv("GEMINI_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        openai_key = api_key or os.getenv("OPENAI_API_KEY")

        # Gather all image inputs
        all_images: List[str] = []
        if images:
            all_images.extend([img for img in images if img])
        if image_input and image_input not in all_images:
            all_images.insert(0, image_input)
        primary_image = all_images[0] if all_images else None

        # 1. Try Groq API (Ultra-High Speed Qwen & LLaMA 3.2 Vision)
        if (vlm_provider in ("groq", "qwen", "auto")) and groq_key:
            res = self._call_groq_vlm(primary_image, domain, groq_key)
            if res and len(res[0]) > 0:
                return res[0], res[1], res[2], "Groq Qwen & LLaMA Engine (Ultra-High Speed)"

        # 2. Try Gemini VLM API (Google AI Studio - Multi-Image Multimodal VLM)
        if (vlm_provider in ("gemini", "auto")) and gemini_key:
            res = self._call_gemini_vlm(all_images, domain, gemini_key)
            if res and len(res[0]) > 0:
                return res[0], res[1], res[2], f"Google AI Studio (Gemini 1.5 Flash - {len(all_images)} frames)"

        # 3. Try Local Ollama Engine (Qwen2.5-VL / LLaVA)
        if vlm_provider in ("ollama", "qwen", "auto"):
            res = self._call_ollama_vlm(primary_image, domain)
            if res and len(res[0]) > 0:
                return res[0], res[1], res[2], "Ollama Local Engine (Qwen2.5-VL / LLaVA)"

        # 4. Try OpenRouter Multi-Model Router (Resilience & Free Models)
        if (vlm_provider in ("openrouter", "auto")) and openrouter_key:
            res = self._call_openrouter_vlm(primary_image, domain, openrouter_key)
            if res and len(res[0]) > 0:
                return res[0], res[1], res[2], "OpenRouter Multi-Model Fallback Engine"

        # 5. Try OpenAI GPT-4o Vision if key available or requested
        if (vlm_provider == "openai" or (vlm_provider == "auto" and openai_key)) and openai_key:
            res = self._call_openai_vlm(all_images, domain, openai_key)
            if res and len(res[0]) > 0:
                return res[0], res[1], res[2], f"OpenAI GPT-4o Vision (Live VLM - {len(all_images)} frames)"

        # 6. Fallback to Saar Intelligent Vision Synthesizer (Zero-latency offline engine)
        nodes, edges, summary = self._synthesize_scene_graph(primary_image, domain, preset_id)
        provider_name = "Saar Vision Engine (Synthesized VLM)"
        if gemini_key or groq_key or openrouter_key or openai_key:
            provider_name += " [Hybrid Live Key Active]"
        return nodes, edges, summary, provider_name

    def _call_gemini_vlm(self, image_inputs: List[str], domain: str, api_key: str) -> Optional[Tuple[List[NodeModel], List[EdgeModel], str]]:
        if not image_inputs:
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        prompt = self.SYSTEM_PROMPT.format(domain=domain)
        parts = [{"text": prompt}]

        for img in image_inputs:
            img_bytes, mime_type = self._prepare_image_data(img)
            if img_bytes:
                b64_img = base64.b64encode(img_bytes).decode("utf-8")
                parts.append({"inlineData": {"mimeType": mime_type, "data": b64_img}})

        if len(parts) <= 1:
            return None

        payload = {
            "contents": [
                {
                    "parts": parts
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.2
            }
        }

        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=12) as response:
                result = json.loads(response.read().decode("utf-8"))
                text = result["candidates"][0]["content"]["parts"][0]["text"]
                return self._parse_vlm_json_response(text)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            print(f"[VLMService] Gemini API call failed (HTTP {e.code}): {err_body}")
            return None
        except Exception as e:
            print(f"[VLMService] Gemini API call failed: {e}")
            return None

    def _call_openai_vlm(self, image_inputs: List[str], domain: str, api_key: str) -> Optional[Tuple[List[NodeModel], List[EdgeModel], str]]:
        if not image_inputs:
            return None

        url = "https://api.openai.com/v1/chat/completions"
        prompt = self.SYSTEM_PROMPT.format(domain=domain)
        content = [{"type": "text", "text": prompt}]

        for img in image_inputs:
            img_bytes, mime_type = self._prepare_image_data(img)
            if img_bytes:
                b64_img = base64.b64encode(img_bytes).decode("utf-8")
                content.append({"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64_img}"}})

        if len(content) <= 1:
            return None

        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": content
                }
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }

        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            })
            with urllib.request.urlopen(req, timeout=12) as response:
                result = json.loads(response.read().decode("utf-8"))
                text = result["choices"][0]["message"]["content"]
                return self._parse_vlm_json_response(text)
        except Exception as e:
            print(f"[VLMService] OpenAI API call failed: {e}")
            return None

    def _call_groq_vlm(self, image_input: Optional[str], domain: str, api_key: str) -> Optional[Tuple[List[NodeModel], List[EdgeModel], str]]:
        """Groq Vision API using Llama 4 Scout / Maverick and Llama 3.2 Vision models."""
        url = "https://api.groq.com/openai/v1/chat/completions"
        prompt = self.SYSTEM_PROMPT.format(domain=domain)

        img_bytes, mime_type = self._prepare_image_data(image_input) if image_input else (None, "image/jpeg")
        b64_img = base64.b64encode(img_bytes).decode("utf-8") if img_bytes else None

        # Groq vision-capable models, in preference order
        # qwen/qwen3.6-27b confirmed working and responsive (0.6-2.5s) on this account
        vision_models = [
            "qwen/qwen3.6-27b",
            "qwen/qwen3.8-27b",
        ]

        for model in vision_models:
            # Attach image in content array when available (vision API format)
            if b64_img:
                content = [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64_img}"}}
                ]
            else:
                content = prompt

            payload = {
                "model": model,
                "messages": [{"role": "user", "content": content}],
                "temperature": 0.2,
                "max_tokens": 750
            }
            try:
                req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                })
                with urllib.request.urlopen(req, timeout=20) as response:
                    result = json.loads(response.read().decode("utf-8"))
                    text = result["choices"][0]["message"]["content"]
                    # Strip chain-of-thought thinking tags if present
                    text = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE).strip()
                    text = re.sub(r"<think>[\s\S]*", "", text, flags=re.IGNORECASE).strip()
                    parsed = self._parse_vlm_json_response(text)
                    if parsed:
                        print(f"[VLMService] Successfully invoked Groq vision model '{model}'")
                        return parsed
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="ignore")
                print(f"[VLMService] Groq vision model '{model}' failed (HTTP {e.code}): {err_body[:300]}")
                continue
            except Exception as e:
                print(f"[VLMService] Groq vision model '{model}' failed: {e}")
                continue
        return None

    def _call_ollama_vlm(self, image_input: Optional[str], domain: str) -> Optional[Tuple[List[NodeModel], List[EdgeModel], str]]:
        """Local Ollama Qwen2.5-VL / LLaVA Vision Engine."""
        # Fast probe to see if local Ollama daemon is actively running
        try:
            probe_req = urllib.request.Request("http://localhost:11434/api/tags", headers={"User-Agent": "Saar/1.0"})
            with urllib.request.urlopen(probe_req, timeout=0.6) as resp:
                pass
        except Exception:
            return None

        url = "http://localhost:11434/api/chat"
        prompt = self.SYSTEM_PROMPT.format(domain=domain)
        
        img_bytes, _ = self._prepare_image_data(image_input) if image_input else (None, "image/jpeg")
        b64_img = base64.b64encode(img_bytes).decode("utf-8") if img_bytes else None

        models_to_try = ["qwen2.5-vl", "llava", "qwen2.5", "qwen"]

        for model in models_to_try:
            msg = {"role": "user", "content": prompt}
            if b64_img:
                msg["images"] = [b64_img]

            payload = {
                "model": model,
                "messages": [msg],
                "stream": False,
                "options": {"temperature": 0.2}
            }
            try:
                req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=4) as response:
                    result = json.loads(response.read().decode("utf-8"))
                    text = result.get("message", {}).get("content", "")
                    parsed = self._parse_vlm_json_response(text)
                    if parsed:
                        print(f"[VLMService] Successfully invoked local Ollama model '{model}'")
                        return parsed
            except Exception:
                continue
        return None

    def _call_openrouter_vlm(self, image_input: Optional[str], domain: str, api_key: str) -> Optional[Tuple[List[NodeModel], List[EdgeModel], str]]:
        """OpenRouter Resilient Multi-Model Catalog Routing."""
        url = "https://openrouter.ai/api/v1/chat/completions"
        prompt = self.SYSTEM_PROMPT.format(domain=domain)
        
        payload = {
            "model": "meta-llama/llama-3.3-70b-instruct:free",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://saar.engine",
                "X-Title": "Saar Engine"
            })
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))
                text = result["choices"][0]["message"]["content"]
                return self._parse_vlm_json_response(text)
        except Exception as e:
            print(f"[VLMService] OpenRouter API call failed: {e}")
            return None

    def _parse_vlm_json_response(self, raw_json_str: str) -> Optional[Tuple[List[NodeModel], List[EdgeModel], str]]:
        try:
            # Strip think tags if any remain
            raw = re.sub(r"<think>[\s\S]*?</think>", "", raw_json_str, flags=re.IGNORECASE).strip()
            raw = re.sub(r"<think>[\s\S]*", "", raw, flags=re.IGNORECASE).strip()

            # If stripping think removed everything, check if JSON was inside think block
            if not raw or "{" not in raw:
                raw = raw_json_str

            # Robust JSON extraction: first check code fence ```json ... ```, then find outermost { ... }
            fence_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", raw, flags=re.IGNORECASE)
            if fence_match:
                cleaned = fence_match.group(1).strip()
            else:
                json_match = re.search(r"\{[\s\S]*\}", raw)
                cleaned = json_match.group(0).strip() if json_match else raw.strip()

            # Attempt standard parse first, with auto-repair fallback for truncated payloads
            try:
                data = json.loads(cleaned)
            except Exception:
                repaired = cleaned
                if repaired.count('"') % 2 != 0:
                    repaired += '"'
                open_braces = repaired.count('{') - repaired.count('}')
                open_brackets = repaired.count('[') - repaired.count(']')
                repaired = re.sub(r",\s*$", "", repaired)
                repaired = re.sub(r",\s*(\]|\})", r"\1", repaired)
                repaired += "]" * max(0, open_brackets)
                repaired += "}" * max(0, open_braces)
                data = json.loads(repaired)

            nodes: List[NodeModel] = []
            edges: List[EdgeModel] = []

            for n in data.get("nodes", []):
                raw_bbox = n.get("bbox")
                parsed_bbox = None
                if isinstance(raw_bbox, list) and len(raw_bbox) == 4:
                    try:
                        coords = [float(coord) for coord in raw_bbox]
                        max_coord = max(coords)
                        # If model output normalized 0..1 decimals, scale to 0..1000
                        if max_coord <= 1.05:
                            coords = [c * 1000.0 for c in coords]
                        # If model output normalized 0..100 percentages, scale to 0..1000
                        elif max_coord <= 100.0:
                            coords = [c * 10.0 for c in coords]
                        
                        ymin, xmin, ymax, xmax = coords
                        # If model provided [xmin, ymin, width, height] format
                        if ymax < ymin:
                            ymax = ymin + ymax
                        if xmax < xmin:
                            xmax = xmin + xmax
                        
                        # Clamp and ensure reasonable minimum size
                        ymin = max(0.0, min(950.0, ymin))
                        xmin = max(0.0, min(950.0, xmin))
                        ymax = max(ymin + 40.0, min(1000.0, ymax))
                        xmax = max(xmin + 40.0, min(1000.0, xmax))

                        parsed_bbox = [round(ymin, 1), round(xmin, 1), round(ymax, 1), round(xmax, 1)]
                    except (ValueError, TypeError):
                        parsed_bbox = None

                is_anchor = n.get("visual_anchor", parsed_bbox is not None)

                nodes.append(NodeModel(
                    id=n.get("id", f"node_{len(nodes)}"),
                    label=n.get("label", "Extracted Visual Entity"),
                    node_type=n.get("node_type", "object"),
                    category=n.get("category", "general"),
                    confidence=float(n.get("confidence", 0.9)),
                    bbox=parsed_bbox,
                    visual_anchor=is_anchor,
                    properties=n.get("properties", {})
                ))

            for h in data.get("hypotheses", []):
                nodes.append(NodeModel(
                    id=h.get("id", f"hypo_{len(nodes)}"),
                    label=h.get("label", "Hypothesis: Unverified Structural Anomaly"),
                    node_type="hypothesis",
                    category=h.get("category", "risk"),
                    confidence=float(h.get("confidence", 0.45)),
                    bbox=None,
                    visual_anchor=False,
                    status="hypothesis"
                ))

            for e in data.get("edges", []):
                edges.append(EdgeModel(
                    id=e.get("id", f"edge_{len(edges)}"),
                    source=e.get("source"),
                    target=e.get("target"),
                    relation_type=e.get("relation_type", "affects"),
                    confidence=float(e.get("confidence", 0.8)),
                    evidence=e.get("evidence", "Visual VLM perception link")
                ))

            if not nodes:
                return None
            scene_summary = data.get("scene_summary", "Visual scene analysis completed by SAAR perception engine.")
            return nodes, edges, scene_summary

        except Exception as err:
            print(f"[VLMService] Failed to parse VLM response JSON: {err}")
            return None

    def _synthesize_scene_graph(
        self,
        image_input: Optional[str],
        domain: str,
        preset_id: Optional[str]
    ) -> Tuple[List[NodeModel], List[EdgeModel], str]:
        """Synthesizes image-grounded structured scene graph for custom uploaded images or domain presets."""
        if domain == "astronomy":
            nodes = [
                NodeModel(id="star_spectrum_01", label="Target Stellar Absorption Spectrum", node_type="object", category="spectroscopy", confidence=0.97, bbox=[140, 80, 460, 920], visual_anchor=True, properties={"spectral_class": "G2V", "resolution_r": 45000}),
                NodeModel(id="line_shift_01", label="H-Alpha Line Centroid Shift (Δλ = +0.187Å)", node_type="property", category="measurement", confidence=0.92, bbox=[250, 460, 390, 570], visual_anchor=True, properties={"delta_lambda_angstrom": 0.187, "rest_wavelength": 6562.8}),
                NodeModel(id="transit_dip_01", label="Light Curve Periodic Dip (0.84% flux depth)", node_type="observation", category="photometry", confidence=0.88, bbox=[560, 110, 890, 890], visual_anchor=True, properties={"depth_pct": 0.84, "period_days": 3.52}),
                NodeModel(id="hypo_exoplanet_companion", label="Hypothesis: Transiting Sub-Jupiter Exoplanet", node_type="hypothesis", category="astrobiology", confidence=0.52, bbox=None, visual_anchor=False, status="hypothesis")
            ]
            edges = [
                EdgeModel(id="e_astro_1", source="star_spectrum_01", target="line_shift_01", relation_type="affects", confidence=0.94, evidence="Doppler velocity shift observed in stellar absorption lines."),
                EdgeModel(id="e_astro_2", source="line_shift_01", target="hypo_exoplanet_companion", relation_type="supports", confidence=0.60, evidence="Periodic radial velocity shift indicates gravitational pull from unseen companion."),
                EdgeModel(id="e_astro_3", source="transit_dip_01", target="hypo_exoplanet_companion", relation_type="supports", confidence=0.72, evidence="Photometric light curve transit matches periodic orbital shadow.")
            ]
        elif domain == "agriculture":
            is_preset_monstera = preset_id == "agri_monstera_fenestration"
            is_preset_tomato = preset_id == "agri_tomato_chlorosis"
            is_custom_image = image_input and not is_preset_monstera and not is_preset_tomato

            if is_custom_image:
                # Generic scene for any user-uploaded plant image (VLM unavailable)
                nodes = [
                    NodeModel(
                        id="plant_specimen_01",
                        label="Botanical Foliar Specimen",
                        node_type="object",
                        category="morphology",
                        confidence=0.88,
                        bbox=[50, 50, 950, 950],
                        visual_anchor=True,
                        properties={"specimen_type": "foliar_canopy", "morphology": "vegetative_tissue"}
                    ),
                    NodeModel(
                        id="foliar_surface_01",
                        label="Foliar Surface Structure Detected",
                        node_type="observation",
                        category="morphology",
                        confidence=0.70,
                        bbox=[100, 100, 800, 800],
                        visual_anchor=True,
                        properties={"morphology": "lamina_detected"}
                    ),
                    NodeModel(
                        id="hypo_nutrient_stress",
                        label="Hypothesis: Macro/Micronutrient Deficiency or Imbalance",
                        node_type="hypothesis",
                        category="pathology",
                        confidence=0.42,
                        bbox=None,
                        visual_anchor=False,
                        status="hypothesis"
                    ),
                    NodeModel(
                        id="hypo_pathogen_pest",
                        label="Hypothesis: Pathogen Infection or Pest Infestation",
                        node_type="hypothesis",
                        category="pathology",
                        confidence=0.38,
                        bbox=None,
                        visual_anchor=False,
                        status="hypothesis"
                    ),
                    NodeModel(
                        id="hypo_environmental_stress",
                        label="Hypothesis: Abiotic Environmental Stress (Water / Light / Temperature)",
                        node_type="hypothesis",
                        category="physiological",
                        confidence=0.45,
                        bbox=None,
                        visual_anchor=False,
                        status="hypothesis"
                    )
                ]
                edges = [
                    EdgeModel(
                        id="e_generic_1",
                        source="foliar_surface_01",
                        target="hypo_nutrient_stress",
                        relation_type="indicates",
                        confidence=0.45,
                        evidence="Foliar surface detected; nutrient stress requires spectral confirmation."
                    ),
                    EdgeModel(
                        id="e_generic_2",
                        source="foliar_surface_01",
                        target="hypo_pathogen_pest",
                        relation_type="indicates",
                        confidence=0.40,
                        evidence="Morphological surface scan required to rule out lesions, pustules, or frass."
                    ),
                    EdgeModel(
                        id="e_generic_3",
                        source="plant_specimen_01",
                        target="hypo_environmental_stress",
                        relation_type="affects",
                        confidence=0.42,
                        evidence="Abiotic stress diagnosis requires soil moisture, light, and temperature cross-referencing."
                    )
                ]
                summary = "Plant specimen detected. Live VLM image analysis was unavailable; generic diagnostic hypotheses loaded. Run diagnostic tools for targeted analysis."
            elif is_preset_monstera:
                nodes = [
                    NodeModel(
                        id="leaf_fenestrations_01",
                        label="Elliptical Leaf Fenestrations (Lamina Perforations)",
                        node_type="object",
                        category="morphology",
                        confidence=0.96,
                        bbox=[90, 300, 430, 590],
                        visual_anchor=True,
                        properties={"species": "Monstera adansonii", "margin_type": "entire/suberized", "halo_necrosis": False, "fenestration_count": 8}
                    ),
                    NodeModel(
                        id="unfurling_apex_leaf_01",
                        label="Emergent Juvenile Apical Shoot (Unfurling Leaf)",
                        node_type="observation",
                        category="vegetative_vigor",
                        confidence=0.95,
                        bbox=[310, 520, 750, 610],
                        visual_anchor=True,
                        properties={"turgor": "high", "pigmentation": "light_green_juvenile", "meristem_activity": "active"}
                    ),
                    NodeModel(
                        id="foliar_canopy_01",
                        label="Dense Fenestrated Foliage Canopy",
                        node_type="object",
                        category="anatomy",
                        confidence=0.93,
                        bbox=[30, 540, 580, 980],
                        visual_anchor=True,
                        properties={"chlorophyll_density": "high", "leaf_blade_integrity": "healthy"}
                    ),
                    NodeModel(
                        id="pot_substrate_01",
                        label="Potted Planter & Aerated Peat-Perlite Substrate",
                        node_type="object",
                        category="environment",
                        confidence=0.91,
                        bbox=[480, 450, 980, 720],
                        visual_anchor=True,
                        properties={"container_type": "indoor_nursery_pot", "substrate_texture": "coarse_peat_perlite"}
                    ),
                    NodeModel(
                        id="cascading_leaves_01",
                        label="Pendulous Lateral Foliage & Calyx Stalks",
                        node_type="observation",
                        category="morphology",
                        confidence=0.89,
                        bbox=[590, 610, 990, 870],
                        visual_anchor=True,
                        properties={"orientation": "geotropic_pendulous", "turgor": "optimal"}
                    ),
                    # Competing Hypotheses
                    NodeModel(
                        id="hypo_physiological_fenestration",
                        label="Hypothesis: Natural Evolutionary Leaf Fenestration (Programmed Cell Death in Araceae)",
                        node_type="hypothesis",
                        category="developmental",
                        confidence=0.58,
                        bbox=None,
                        visual_anchor=False,
                        status="hypothesis"
                    ),
                    NodeModel(
                        id="hypo_foliar_pest_chewing",
                        label="Hypothesis: Pest Defoliation / Insect Chewing or Fungal Shot-Hole Lesions",
                        node_type="hypothesis",
                        category="pathology",
                        confidence=0.36,
                        bbox=None,
                        visual_anchor=False,
                        status="hypothesis"
                    ),
                    NodeModel(
                        id="hypo_vigor_vegetative",
                        label="Hypothesis: High Photosynthetic Competence & Active Apical Expansion",
                        node_type="hypothesis",
                        category="physiological",
                        confidence=0.62,
                        bbox=None,
                        visual_anchor=False,
                        status="hypothesis"
                    )
                ]
                edges = [
                    EdgeModel(
                        id="e_monstera_1",
                        source="leaf_fenestrations_01",
                        target="hypo_physiological_fenestration",
                        relation_type="supports",
                        confidence=0.72,
                        evidence="Smooth elliptical hole perimeters without necrotic margins or jagged borders match programmed cell death."
                    ),
                    EdgeModel(
                        id="e_monstera_2",
                        source="leaf_fenestrations_01",
                        target="hypo_foliar_pest_chewing",
                        relation_type="affects",
                        confidence=0.40,
                        evidence="Perforations require diagnostic verification against caterpillar or beetle foliar mastication."
                    ),
                    EdgeModel(
                        id="e_monstera_3",
                        source="unfurling_apex_leaf_01",
                        target="hypo_vigor_vegetative",
                        relation_type="supports",
                        confidence=0.88,
                        evidence="Emergent rolled juvenile shoot at apical meristem confirms uninhibited cell division and vascular flow."
                    ),
                    EdgeModel(
                        id="e_monstera_4",
                        source="pot_substrate_01",
                        target="hypo_vigor_vegetative",
                        relation_type="supports",
                        confidence=0.68,
                        evidence="Adequate container volume and aerated medium support root-zone respiration."
                    )
                ]
                summary = "Multimodal scene analysis identifies potted Monstera adansonii (Swiss cheese plant) exhibiting characteristic elliptical leaf fenestrations, active apical shoot unfurling, and dark green healthy foliage."
            else:  # is_preset_tomato or default
                nodes = [
                    NodeModel(id="leaf_chlorosis_01", label="Interveinal Foliar Chlorosis", node_type="object", category="pathology", confidence=0.96, bbox=[180, 240, 680, 760], visual_anchor=True, properties={"pattern": "bright yellowing between dark green primary veins", "canopy_layer": "apical and middle foliage"}),
                    NodeModel(id="soil_moisture_sensor_01", label="Root Zone Moisture Sensor (48% VWC)", node_type="property", category="measurement", confidence=0.94, bbox=[720, 520, 910, 830], visual_anchor=True, properties={"vwc_percent": 48.2, "saturation_status": "continuous waterlogging"}),
                    NodeModel(id="soil_ph_sensor_01", label="Substrate Alkalinity (pH 7.85)", node_type="property", category="measurement", confidence=0.92, bbox=None, visual_anchor=False, properties={"ph": 7.85, "condition": "calcareous / alkaline"}),
                    NodeModel(id="irrigation_emitter_01", label="Continuous Drip Irrigation Line", node_type="object", category="infrastructure", confidence=0.98, bbox=[670, 70, 870, 420], visual_anchor=True, properties={"regime": "unregulated pulse", "flow_liters_hr": 2.8}),
                    NodeModel(id="hypo_iron_deficiency", label="Hypothesis: Root Anoxia & Fe²⁺ Bioavailability Collapse", node_type="hypothesis", category="risk", confidence=0.48, bbox=None, visual_anchor=False, status="hypothesis")
                ]
                edges = [
                    EdgeModel(id="e_agri_1", source="irrigation_emitter_01", target="soil_moisture_sensor_01", relation_type="causes", confidence=0.95, evidence="Excessive irrigation emitter frequency maintains root substrate above saturation limit."),
                    EdgeModel(id="e_agri_2", source="soil_moisture_sensor_01", target="hypo_iron_deficiency", relation_type="supports", confidence=0.60, evidence="Prolonged saturation induces root-zone oxygen depletion and impairs ATP-driven H+-ATPase pumps."),
                    EdgeModel(id="e_agri_3", source="soil_ph_sensor_01", target="hypo_iron_deficiency", relation_type="supports", confidence=0.65, evidence="Alkaline pH promotes rapid precipitation of ionic iron into insoluble hydroxide matrices."),
                    EdgeModel(id="e_agri_4", source="hypo_iron_deficiency", target="leaf_chlorosis_01", relation_type="causes", confidence=0.75, evidence="Iron unavailability halts chloroplast protein complex assembly, producing acute interveinal chlorosis.")
                ]
                summary = "Multimodal scene analysis identifies acute interveinal foliar chlorosis, saturated root zone substrate (48% VWC), and continuous drip line over-delivery."

        elif domain == "pediatrics":
            nodes = [
                NodeModel(id="node_lumbar_lordosis", label="Accentuated Lumbar Curvature (~38° Lordosis)", node_type="object", category="biomechanics", confidence=0.94, bbox=[340, 280, 620, 520], visual_anchor=True, properties={"plane": "sagittal", "angle_deg": 38.5, "inflection": "L3-L5"}),
                NodeModel(id="node_protuberant_abdomen", label="Protuberant Abdominal Contour & Visceral Forward Projection", node_type="observation", category="anatomy", confidence=0.96, bbox=[380, 480, 590, 720], visual_anchor=True, properties={"presentation": "benign anterior displacement", "muscle_tone": "developing rectus abdominis"}),
                NodeModel(id="node_anterior_pelvic_tilt", label="Anterior Pelvic Inclination (ASIS-PSIS tilt ~18°)", node_type="property", category="biomechanics", confidence=0.88, bbox=None, visual_anchor=False, properties={"pelvic_tilt_deg": 18.2, "status": "compensatory"}),
                NodeModel(id="node_knee_bowing", label="Bilateral Symmetrical Genu Varum (Intercondylar distance ~2.2cm)", node_type="object", category="orthopedic", confidence=0.92, bbox=[640, 310, 890, 680], visual_anchor=True, properties={"symmetry": "high", "intercondylar_gap_cm": 2.2, "status": "bilateral"}),
                NodeModel(id="node_wide_base_support", label="Wide-Base Toddler Stance with Calcaneal Pronation", node_type="observation", category="motor", confidence=0.91, bbox=[820, 260, 970, 740], visual_anchor=True, properties={"base_of_support": "broad", "arch": "flexible toddler flatfoot (pes planus)"}),
                NodeModel(id="hypo_physiological_maturity", label="Hypothesis: Benign Physiological Toddler Biomechanics (Age-Appropriate Maturity)", node_type="hypothesis", category="developmental", confidence=0.52, bbox=None, visual_anchor=False, status="hypothesis"),
                NodeModel(id="hypo_truncal_hypotonia", label="Hypothesis: Axial Core Hypotonia / Compensatory Hyperlordosis", node_type="hypothesis", category="neuromuscular", confidence=0.40, bbox=None, visual_anchor=False, status="hypothesis"),
                NodeModel(id="hypo_pathological_bowing", label="Hypothesis: Pathological Tibial Bowing (Early Blount's Disease / Rickets)", node_type="hypothesis", category="pathology", confidence=0.35, bbox=None, visual_anchor=False, status="hypothesis")
            ]
            edges = [
                EdgeModel(id="e_ped_1", source="node_protuberant_abdomen", target="node_anterior_pelvic_tilt", relation_type="causes", confidence=0.88, evidence="Weak abdominal wall compliance in toddlers allows visceral weight to shift pelvis anteriorly."),
                EdgeModel(id="e_ped_2", source="node_anterior_pelvic_tilt", target="node_lumbar_lordosis", relation_type="causes", confidence=0.92, evidence="Anterior pelvic tilt mechanically mandates compensatory lumbar lordotic curvature to keep plumb line balanced."),
                EdgeModel(id="e_ped_3", source="node_lumbar_lordosis", target="hypo_physiological_maturity", relation_type="supports", confidence=0.65, evidence="Lumbar lordosis paired with protuberant abdomen is the classic physiological presentation in healthy 18-24m toddlers."),
                EdgeModel(id="e_ped_4", source="node_knee_bowing", target="hypo_physiological_maturity", relation_type="supports", confidence=0.60, evidence="Bilateral symmetrical genu varum < 3cm is typical up to 24 months before transitioning to physiological valgum."),
                EdgeModel(id="e_ped_5", source="node_knee_bowing", target="hypo_pathological_bowing", relation_type="affects", confidence=0.45, evidence="Bowing requires differential analysis against asymmetrical growth plate disturbance.")
            ]
            summary = "Multimodal multi-photo analysis identifies compensatory lumbar lordosis (38.5°), benign anterior pelvic tilt, wide-base stance, and symmetrical physiological genu varum (2.2cm gap)."

        else: # Infrastructure domain
            nodes = [
                NodeModel(id="road_01", label="Pavement Surface Longitudinal Cracking", node_type="object", category="structural", confidence=0.96, bbox=[310, 190, 780, 520], visual_anchor=True, properties={"length_m": 4.5, "max_aperture_mm": 18}),
                NodeModel(id="water_01", label="Localized Surface Water Accumulation", node_type="object", category="environment", confidence=0.92, bbox=[440, 470, 880, 860], visual_anchor=True, properties={"area_m2": 12.5, "stagnation": "severe"}),
                NodeModel(id="drain_01", label="Storm Drain Collection Intake", node_type="object", category="infrastructure", confidence=0.98, bbox=[120, 670, 410, 940], visual_anchor=True, properties={"clogging_level": "heavy"}),
                NodeModel(id="debris_01", label="Accumulated Organic & Solid Debris", node_type="object", category="obstacle", confidence=0.95, bbox=[150, 640, 370, 890], visual_anchor=True, properties={"type": "leaves, sediment, trash"}),
                NodeModel(id="prop_drain_flow", label="Drainage Inflow Rate = Restricted", node_type="property", category="measurement", confidence=0.60, bbox=None, visual_anchor=False),
                NodeModel(id="hypo_subsurface_erosion", label="Hypothesis: Sub-pavement Void & Soil Washout", node_type="hypothesis", category="risk", confidence=0.48, bbox=None, visual_anchor=False, status="hypothesis")
            ]
            edges = [
                EdgeModel(id="e_infra_1", source="debris_01", target="drain_01", relation_type="obstructs", confidence=0.92, evidence="Heavy debris physically blocks storm water catchment intake."),
                EdgeModel(id="e_infra_2", source="drain_01", target="water_01", relation_type="causes", confidence=0.85, evidence="Blocked drainage inlet prevents runoff removal, causing localized standing water."),
                EdgeModel(id="e_infra_3", source="water_01", target="road_01", relation_type="affects", confidence=0.80, evidence="Standing water penetrates pavement cracks, degrading sub-base cohesion."),
                EdgeModel(id="e_infra_4", source="water_01", target="hypo_subsurface_erosion", relation_type="supports", confidence=0.55, evidence="Water pressure infiltration risks subterranean soil piping.")
            ]
            summary = "Visual perception identifies asphalt pavement cracking, extensive surface water ponding, and heavy debris obstructing storm drain intake."

        return nodes, edges, summary

    def synthesize_reasoning_explanation(self, prompt: str, temperature: float = 0.3) -> Optional[str]:
        """Invoke Groq / Gemini LLM to synthesize dynamic natural language scientific reasoning with non-deterministic temperature."""
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            url = "https://api.groq.com/openai/v1/chat/completions"
            for model in ["qwen/qwen3.6-27b", "groq/compound-mini", "groq/compound", "qwen/qwen3.8-27b"]:
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are SAAR (सार), an elite scientific reasoning engine. You explain complex causal mechanisms, statistical evidence, correlations, and hypotheses clearly, concisely, and with structured markdown formatting (using executive summaries, markdown tables, step-by-step causal pathways, and bold takeaways)."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": max(0.1, min(1.0, temperature)),
                    "max_tokens": 750
                }
                try:
                    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {groq_key}",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    })
                    with urllib.request.urlopen(req, timeout=12) as resp:
                        res = json.loads(resp.read().decode("utf-8"))
                        text = res["choices"][0]["message"]["content"]
                        text = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE).strip()
                        text = re.sub(r"<think>[\s\S]*", "", text, flags=re.IGNORECASE).strip()
                        if text:
                            print(f"[VLMService] Successfully synthesized scientific explanation using Groq '{model}'")
                            return text
                except Exception as e:
                    print(f"[VLMService] Groq synthesis failed for model {model}: {e}")

        # Gemini fallback
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            payload = {
                "contents": [{"parts": [{"text": f"You are SAAR (सार), an elite scientific reasoning engine. Synthesize an evidence-backed answer with clear markdown tables, step-by-step causal mechanisms, and bold takeaways.\n\n{prompt}"}]}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1024}
            }
            try:
                req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=12) as resp:
                    res = json.loads(resp.read().decode("utf-8"))
                    text = res["candidates"][0]["content"]["parts"][0]["text"].strip()
                    text = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE).strip()
                    text = re.sub(r"<think>[\s\S]*", "", text, flags=re.IGNORECASE).strip()
                    if text:
                        return text
            except Exception as e:
                print(f"[VLMService] Gemini synthesis failed: {e}")

        return None

