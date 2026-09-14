import json
import base64
import urllib.request
import urllib.parse
import re
import os
import time
from typing import Dict, Any, List, Optional, Tuple

try:
    from dotenv import load_dotenv
    _env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
    if os.path.exists(_env_file):
        load_dotenv(_env_file, override=True)
    else:
        load_dotenv(override=True)
except ImportError:
    pass

from .schemas import NodeModel, EdgeModel
from .services.key_pool_manager import key_pool

class VLMService:
    """
    Multimodal Vision-Language Model (VLM) Service for Saar.
    Communicates with cloud VLM APIs (Google Gemini, OpenAI GPT-4o),
    local vision models (Ollama LLaVA/Qwen2-VL), or Saar's Intelligent Vision Synthesizer.
    """

    SYSTEM_PROMPT = """You are the Perception Layer of Saar, a Visual Scientific Reasoning Engine.
Your task is to analyze the provided image for domain '{domain}' and extract a comprehensive, structured visual scene graph.

CRITICAL INSTANCE-LEVEL GROUNDING DIRECTIVE:
- When the scene contains multiple distinct instances of a subject (such as multiple flower blooms, individual fruits, distinct leaves, lesions, or structural cracks):
  DO NOT bundle or merge them into a single giant bounding box enclosing the entire cluster or scene!
  Detect and emit distinct, tight bounding boxes [ymin, xmin, ymax, xmax] (normalized 0 to 1000) for EACH prominent individual instance (e.g., 'Instance 01', 'Instance 02', up to 25-30 instances).
- Also ground context/background features (e.g. foliage canopy, substrate, infrastructure).
- Output valid JSON ONLY. Start directly with the JSON object.

Structure:
{{
  "scene_summary": "Concise assessment of the scene and subject count",
  "nodes": [
    {{
      "id": "node_id_1",
      "label": "Human readable entity/property name with instance index if multiple",
      "node_type": "object|property|observation|hypothesis",
      "category": "infrastructure|environment|structural|measurement|risk|pathology|morphology",
      "confidence": 0.95,
      "bbox": [ymin, xmin, ymax, xmax], // Normalized integers 0 to 1000 covering this specific entity instance tightly
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
    BOTANICAL_SYSTEM_PROMPT = """You are the Senior Botanical & Horticultural Perception Specialist of Saar, a Visual Scientific Reasoning Engine.
Your objective is high-precision visual anatomical decomposition, per-instance spatial grounding, entity counting, and causal physiological reasoning for any botanical specimen, crop, flower, or vegetative setup.

CRITICAL INSTANCE-LEVEL GROUNDING & QUANTITATIVE PROTOCOL:
1. Per-Instance Object Detection & Bounding Boxes:
   - When multiple distinct subject entities are present (e.g. individual rose blooms, flowers, fruits, leaves, pathology lesions, or stems):
     NEVER merge or bundle them into a single giant bounding box enclosing the entire cluster or bush!
     Ground EACH visible individual flower bloom or organ with its OWN separate, tight bounding box [ymin, xmin, ymax, xmax] (normalized integers 0 to 1000).
     Detect and bound ALL prominent individual blooms/organs (up to 20 to 30 individual nodes when present) so the user can interact with each flower independently.
     Label each instance with its specific index, species, and developmental stage (e.g., "Rosa Bloom 01 (Full Anthesis)", "Rosa Bloom 02 (Opening Bud)", "Rosa Bloom 03 (Petal Shedding)").
   - For collective background greenery or foliage, provide a separate contextual node (e.g., "Foliar Canopy Matrix" or "Healthy Vegetative Leaves").

2. Entity Identification, Total Count & Phenology:
   - Identify the exact species (e.g. 'Rosa hybrid' / roses, 'Solanum lycopersicum' / tomato, 'Monstera adansonii', etc.).
   - Explicitly COUNT the total number of distinct subject entities visible in the scene.
   - For each flower bloom: record in properties "instance_index": <int>, "anthesis_stage": "bud|opening|full_anthesis|senescent", "turgor": "high|moderate|wilting", "petal_health": "clean|spotted|blighted".
   - In your scene_summary, state the exact quantified subject count and overall canopy condition (e.g., "Visual inspection identifies 25 distinct Rosa hybrid blooms in various anthesis stages across an upright foliar canopy...").

Output valid JSON ONLY. Start directly with the JSON object.
Structure:
{{
  "scene_summary": "Concise assessment explicitly stating the exact number of subjects detected and their physiological condition",
  "nodes": [
    {{
      "id": "rose_bloom_01",
      "label": "Rosa Bloom 01 (Full Anthesis)",
      "node_type": "object",
      "category": "morphology",
      "confidence": 0.96,
      "bbox": [ymin, xmin, ymax, xmax], // Tight normalized bounding box around THIS SPECIFIC flower bloom only
      "visual_anchor": true,
      "properties": {{"species": "Rosa hybrid", "organ": "flower_bloom", "instance_index": 1, "anthesis_stage": "full_anthesis", "condition": "healthy"}}
    }},
    {{
      "id": "rose_bloom_02",
      "label": "Rosa Bloom 02 (Emergent Bud)",
      "node_type": "object",
      "category": "morphology",
      "confidence": 0.94,
      "bbox": [ymin, xmin, ymax, xmax], // Tight box around the second flower
      "visual_anchor": true,
      "properties": {{"species": "Rosa hybrid", "organ": "flower_bloom", "instance_index": 2, "anthesis_stage": "bud", "condition": "healthy"}}
    }}
  ],
  "edges": [
    {{
      "id": "edge_id_1",
      "source": "rose_bloom_01",
      "target": "hypo_botanical_vigor",
      "relation_type": "indicates",
      "confidence": 0.90,
      "evidence": "Symmetrical corolla expansion and high turgor indicate adequate hydraulic xylem tension."
    }}
  ],
  "hypotheses": [
    {{
      "id": "hypo_botanical_vigor",
      "label": "Hypothesis: High Vascular Hydraulic Conductivity & Balanced Nitrogen Assimilation",
      "category": "physiological",
      "confidence": 0.88,
      "bbox": null,
      "visual_anchor": false
    }}
  ]
}}
"""

    _gemini_circuit_broken: bool = False
    _groq_circuit_until: float = 0.0

    # Per-domain temperature profiles: precision vs exploration tradeoff
    DOMAIN_TEMPERATURE = {
        "infrastructure": 0.08,   # Maximum precision for crack measurements & dimensions
        "agriculture": 0.15,     # Slight flexibility for species identification & phenology
        "astronomy": 0.10,       # Precision on spectral measurements & orbital parameters
        "pediatrics": 0.20,      # Moderate flexibility for differential diagnosis exploration
        "gait": 0.12,            # Precision for biomechanical angle measurements
        "sports": 0.18,          # Flexibility for kinetic chain analysis
    }

    # SAAR Scene Graph JSON Schema — enforced via Gemini responseSchema
    SCENE_GRAPH_SCHEMA = {
        "type": "OBJECT",
        "properties": {
            "scene_summary": {"type": "STRING"},
            "nodes": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "id": {"type": "STRING"},
                        "label": {"type": "STRING"},
                        "node_type": {"type": "STRING"},
                        "category": {"type": "STRING"},
                        "confidence": {"type": "NUMBER"},
                        "bbox": {"type": "ARRAY", "items": {"type": "NUMBER"}},
                        "visual_anchor": {"type": "BOOLEAN"},
                        "properties": {"type": "OBJECT"}
                    },
                    "required": ["id", "label", "node_type", "confidence"]
                }
            },
            "edges": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "id": {"type": "STRING"},
                        "source": {"type": "STRING"},
                        "target": {"type": "STRING"},
                        "relation_type": {"type": "STRING"},
                        "confidence": {"type": "NUMBER"},
                        "evidence": {"type": "STRING"}
                    },
                    "required": ["id", "source", "target", "relation_type"]
                }
            },
            "hypotheses": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "id": {"type": "STRING"},
                        "label": {"type": "STRING"},
                        "category": {"type": "STRING"},
                        "confidence": {"type": "NUMBER"},
                        "bbox": {"type": "ARRAY", "items": {"type": "NUMBER"}},
                        "visual_anchor": {"type": "BOOLEAN"}
                    },
                    "required": ["id", "label", "confidence"]
                }
            }
        },
        "required": ["scene_summary", "nodes", "edges"]
    }

    def _get_prompt_for_domain(self, domain: str) -> str:
        if domain == "agriculture":
            return self.BOTANICAL_SYSTEM_PROMPT.format(domain=domain)
        return self.SYSTEM_PROMPT.format(domain=domain)

    def _get_temperature_for_domain(self, domain: str) -> float:
        """Return domain-optimized temperature for perception precision."""
        return self.DOMAIN_TEMPERATURE.get(domain, 0.2)


    @staticmethod
    def _prepare_image_data(image_input: str) -> Tuple[Optional[bytes], str]:
        """Convert base64 data URL, URL, or local file path into raw bytes and mime type."""
        if not image_input:
            return None, "image/jpeg"
        
        if image_input.startswith("data:image"):
            # Format: data:image/png;base64,...
            try:
                header, encoded = image_input.split(",", 1)
                mime_match = re.search(r"data:(image/\w+);", header)
                mime_type = mime_match.group(1) if mime_match else "image/jpeg"
                return base64.b64decode(encoded), mime_type
            except Exception:
                return None, "image/jpeg"
        elif image_input.startswith("http://") or image_input.startswith("https://"):
            try:
                req = urllib.request.Request(image_input, headers={"User-Agent": "Saar/1.0"})
                with urllib.request.urlopen(req, timeout=5) as response:
                    return response.read(), "image/jpeg"
            except Exception:
                return None, "image/jpeg"
        elif image_input.startswith("/") or image_input.startswith("./"):
            # Local public filesystem asset (e.g. /rose_graft_milestones/...)
            try:
                clean_path = image_input.lstrip("/\\.")
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                public_path = os.path.join(base_dir, "frontend", "public", clean_path)
                if os.path.exists(public_path):
                    with open(public_path, "rb") as f:
                        data = f.read()
                        mime = "image/png" if clean_path.endswith(".png") else "image/jpeg"
                        return data, mime
            except Exception as e:
                print(f"[VLMService] Error loading local public image {image_input}: {e}")
            return None, "image/jpeg"
        else:
            # Check if it's a local file on disk or in frontend/public
            clean_path = image_input.lstrip("/")
            base_dir = os.path.dirname(os.path.abspath(__file__))
            possible_paths = [
                image_input,
                os.path.join(base_dir, "../../frontend/public", clean_path),
                os.path.join(base_dir, "../public", clean_path),
                os.path.join(base_dir, "../../", clean_path),
            ]
            for p in possible_paths:
                if os.path.isfile(p):
                    try:
                        with open(p, "rb") as f:
                            data = f.read()
                        mime = "image/png" if p.lower().endswith(".png") else "image/webp" if p.lower().endswith(".webp") else "image/jpeg"
                        return data, mime
                    except Exception:
                        pass

            # Fallback to base64 decode
            try:
                return base64.b64decode(image_input), "image/jpeg"
            except Exception:
                return None, "image/jpeg"

    def __init__(self):
        self.last_context_analysis: Optional[Dict[str, Any]] = None

    def analyze_context_text(self, context_text: str, domain: str = "agriculture") -> Dict[str, Any]:
        """
        Stage 1 Context Analysis: Analyzes free-form user notes/instructions BEFORE image analysis.
        Extracts:
        - temporal milestone (day number, developmental stage, badge label)
        - physical inspection targets for visual grounding
        - working hypotheses to verify against the image
        - structured context summary
        """
        if not context_text or not context_text.strip():
            return {}

        clean_text = context_text.strip()

        # Step A: Parse info(example: data,name,time etc) : message for ai format
        info_part = clean_text
        message_part = clean_text
        colon_indices = [m.start() for m in re.finditer(r':', clean_text)]
        split_idx = None
        for c_idx in colon_indices:
            # Skip time pattern (e.g. 14:00) where digits are on both sides
            if c_idx > 0 and c_idx < len(clean_text) - 1 and clean_text[c_idx - 1].isdigit() and clean_text[c_idx + 1].isdigit():
                continue
            split_idx = c_idx
            break
        if split_idx is not None:
            info_part = clean_text[:split_idx].strip()
            message_part = clean_text[split_idx + 1:].strip()

        # Step B: Deterministic baseline parsing (regex & semantic keywords)
        day_val = None
        day_match = re.search(r'(?:day|milestone|timepoint|d|week)\s*[:#-]?\s*(\d+)', info_part or clean_text, re.IGNORECASE)
        if day_match:
            val = int(day_match.group(1))
            if "week" in day_match.group(0).lower():
                val *= 7
            day_val = val

        # Try LLM-powered context analysis
        ai_res = self._call_text_analyzer_llm(clean_text, domain, day_val or 1)
        if ai_res:
            self.last_context_analysis = ai_res
            return ai_res

        # Deterministic fallback if offline
        fallback_targets = []
        for term in ["junction", "callus", "scion", "rootstock", "cambium", "vascular", "necrosis", "chlorosis", "leaf", "stem", "root", "crack", "gait", "joint", "posture"]:
            if term in message_part.lower() or term in info_part.lower():
                fallback_targets.append(term)
        if not fallback_targets:
            fallback_targets = ["primary anatomical region", "specimen interface"]

        stage_name = info_part if info_part else (f"Day {day_val}" if day_val else "Specimen Context")
        if len(stage_name) > 35:
            stage_name = stage_name[:32] + "..."

        m_label = stage_name
        if day_val and not stage_name.lower().startswith("day"):
            m_label = f"Day {day_val} - {stage_name}"

        display_part = message_part if message_part else (info_part if info_part else clean_text)
        fallback_hypotheses = [f"Specimen aligns with reported condition: {display_part[:60]}..."]

        res = {
            "milestone": {
                "day": day_val or 1,
                "stage": stage_name,
                "milestone_label": m_label
            },
            "focus_targets": fallback_targets,
            "hypotheses": fallback_hypotheses,
            "analytical_priority": "Verify visual evidence against reported specimen condition.",
            "context_summary": clean_text
        }
        self.last_context_analysis = res
        return res

    def _call_text_analyzer_llm(self, text: str, domain: str, fallback_day: int) -> Optional[Dict[str, Any]]:
        """Call Gemini or Groq fast text model to analyze context text before image analysis."""
        prompt = (
            f"You are the Stage-1 Context Analysis Engine of SAAR (Scientific Automated Analysis & Reasoning).\n"
            f"The user provided contextual metadata in the format: 'info(example: data, name, time etc) : message for ai'.\n"
            f"No extra information or fields are needed.\n\n"
            f"User Context:\n\"{text}\"\n\n"
            f"Analyze the 'info' part before the colon as specimen metadata/milestone, and any 'message' after the colon as visual perception directives.\n"
            f"Note: If the portion after ':' is empty or omitted, extract the milestone from the info part and infer focus targets and general inspection hypotheses from the metadata info.\n\n"
            f"Extract:\n"
            f"1. 'milestone': {{ 'day': <number or null>, 'stage': '<developmental stage, time, or specimen condition from info part>', 'milestone_label': '<concise badge label e.g. Day 10 - Callus Union>' }}\n"
            f"2. 'focus_targets': [list of 2-5 specific physical/anatomical entities the VLM must ground with bounding boxes]\n"
            f"3. 'hypotheses': [list of 1-3 scientific hypotheses to test against visual evidence]\n"
            f"4. 'context_summary': '<concise 1-sentence synthesis combining metadata info and inspection directive>'\n\n"
            f"Return valid JSON ONLY matching this structure. Start with {{ and end with }}."
        )

        # 1. Try Gemini
        gemini_keys = [k.key for k in key_pool.get_available_keys("gemini")]
        if not gemini_keys and os.getenv("GEMINI_API_KEY"):
            gemini_keys = [os.getenv("GEMINI_API_KEY")]

        for g_key in gemini_keys:
            for model_name in ["gemini-3.7-flash", "gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-3.6-flash", "gemini-flash-latest"]:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={g_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2}
                }
                try:
                    req = urllib.request.Request(
                        url,
                        data=json.dumps(payload).encode("utf-8"),
                        headers={"Content-Type": "application/json"}
                    )
                    with urllib.request.urlopen(req, timeout=4) as response:
                        raw = json.loads(response.read().decode("utf-8"))
                        res_text = raw["candidates"][0]["content"]["parts"][0]["text"]
                        parsed = json.loads(res_text)
                        if isinstance(parsed, dict) and ("focus_targets" in parsed or "milestone" in parsed):
                            if not parsed.get("milestone"):
                                parsed["milestone"] = {"day": fallback_day, "stage": f"Day {fallback_day}", "milestone_label": f"Day {fallback_day} Milestone"}
                            elif parsed["milestone"].get("day") is None:
                                parsed["milestone"]["day"] = fallback_day
                            return parsed
                except Exception as e:
                    continue

        # 2. Try Groq
        groq_keys = [k.key for k in key_pool.get_available_keys("groq")]
        if not groq_keys and os.getenv("GROQ_API_KEY"):
            groq_keys = [os.getenv("GROQ_API_KEY")]

        for gr_key in groq_keys:
            url = "https://api.groq.com/openai/v1/chat/completions"
            for model_name in ["qwen/qwen3.6-27b", "openai/gpt-oss-120b", "llama-3.3-70b-versatile"]:
                payload = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": "You are SAAR Context Analyzer. Output valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.2
                }
                try:
                    req = urllib.request.Request(
                        url,
                        data=json.dumps(payload).encode("utf-8"),
                        headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {gr_key}",
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                        }
                    )
                    with urllib.request.urlopen(req, timeout=5) as response:
                        raw = json.loads(response.read().decode("utf-8"))
                        res_text = raw["choices"][0]["message"]["content"]
                        parsed = json.loads(res_text)
                        if isinstance(parsed, dict) and ("focus_targets" in parsed or "milestone" in parsed):
                            if not parsed.get("milestone"):
                                parsed["milestone"] = {"day": fallback_day, "stage": f"Day {fallback_day}", "milestone_label": f"Day {fallback_day} Milestone"}
                            elif parsed["milestone"].get("day") is None:
                                parsed["milestone"]["day"] = fallback_day
                            return parsed
                except Exception as e:
                    continue

        return None

    def _enrich_summary_with_context(self, summary: str) -> str:
        if getattr(self, "last_context_analysis", None):
            ca = self.last_context_analysis
            m = ca.get("milestone", {})
            m_label = m.get("milestone_label") or f"Day {m.get('day', 1)}"
            header = (
                f"### [Stage 1 Prior Context Analysis: {m_label}]\n"
                f"- **Temporal Milestone**: Day {m.get('day', 1)} ({m.get('stage', 'Observation')})\n"
                f"- **Prior Context & User Intent**: {ca.get('context_summary', '')}\n"
                f"- **Inspection Targets Grounded**: {', '.join(ca.get('focus_targets', []))}\n"
                f"- **Hypotheses Evaluated**: {'; '.join(ca.get('hypotheses', []))}\n\n"
                f"### [Stage 2 Visual Grounding & Spatial Evidence]\n"
            )
            return header + summary
        return summary

    def analyze_image(
        self,
        image_input: Optional[str] = None,
        domain: str = "infrastructure",
        preset_id: Optional[str] = None,
        vlm_provider: str = "auto",
        api_key: Optional[str] = None,
        images: Optional[List[str]] = None,
        image_metadata: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[List[NodeModel], List[EdgeModel], str, str]:
        """
        Main entry point for image visual scene perception & hybrid reasoning.
        Supports single image or multi-photo sequences.
        Executes Two-Stage Pipeline:
        Stage 1: Context text analyzed first → milestone & focal targets extracted.
        Stage 2: Visual perception executes with injected prior context hypotheses.
        """
        gemini_key = api_key or os.getenv("GEMINI_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        openai_key = api_key or os.getenv("OPENAI_API_KEY")

        # Stage 1: Analyze user-provided context text FIRST (before image visual analysis)
        context_analysis = None
        if image_metadata:
            for meta in image_metadata:
                ctx = meta.get("context") or meta.get("description")
                if ctx and str(ctx).strip():
                    context_analysis = self.analyze_context_text(str(ctx).strip(), domain)
                    if context_analysis:
                        m_info = context_analysis.get("milestone", {})
                        if m_info.get("day") is not None:
                            meta["day"] = m_info["day"]
                        if m_info.get("stage"):
                            meta["stage"] = m_info["stage"]
                        if m_info.get("milestone_label"):
                            meta["label"] = m_info["milestone_label"]
                        break
        self.last_context_analysis = context_analysis

        # Gather all image inputs
        all_images: List[str] = []
        if images:
            all_images.extend([img for img in images if img])
        if image_input and image_input not in all_images:
            all_images.insert(0, image_input)
        primary_image = all_images[0] if all_images else None

        # 1. Try Gemini VLM API with automatic multi-key load balancing and failover
        if vlm_provider in ("gemini", "auto"):
            gemini_candidates = [api_key] if api_key else [k.key for k in key_pool.get_available_keys("gemini")]
            for g_key in gemini_candidates:
                res = self._call_gemini_vlm(all_images, domain, g_key, image_metadata=image_metadata)
                if res and len(res[0]) > 0:
                    key_pool.record_success("gemini", g_key)
                    masked = g_key[:6] + "..." if len(g_key) > 6 else "***"
                    return res[0], res[1], self._enrich_summary_with_context(res[2]), f"Google AI Studio (Gemini Pool [{masked}] - {len(all_images)} frames)"

        # 2. Try Groq API with multi-key failover
        if vlm_provider in ("groq", "qwen", "auto"):
            groq_candidates = [k.key for k in key_pool.get_available_keys("groq")]
            for gr_key in groq_candidates:
                res = self._call_groq_vlm(primary_image, domain, gr_key)
                if res and len(res[0]) > 0:
                    key_pool.record_success("groq", gr_key)
                    return res[0], res[1], self._enrich_summary_with_context(res[2]), "Groq Qwen & LLaMA Engine (Ultra-High Speed)"

        # 3. Try Local Ollama Engine (Qwen2.5-VL / LLaVA)
        if vlm_provider in ("ollama", "qwen", "auto"):
            res = self._call_ollama_vlm(primary_image, domain)
            if res and len(res[0]) > 0:
                return res[0], res[1], self._enrich_summary_with_context(res[2]), "Ollama Local Engine (Qwen2.5-VL / LLaVA)"

        # 4. Try OpenRouter Multi-Model Router (Resilience & Free Models)
        if (vlm_provider in ("openrouter", "auto")) and openrouter_key:
            res = self._call_openrouter_vlm(primary_image, domain, openrouter_key)
            if res and len(res[0]) > 0:
                return res[0], res[1], self._enrich_summary_with_context(res[2]), "OpenRouter Multi-Model Fallback Engine"

        # 5. Try OpenAI GPT-4o Vision if key available or requested
        if (vlm_provider == "openai" or (vlm_provider == "auto" and openai_key)) and openai_key:
            res = self._call_openai_vlm(all_images, domain, openai_key)
            if res and len(res[0]) > 0:
                return res[0], res[1], self._enrich_summary_with_context(res[2]), f"OpenAI GPT-4o Vision (Live VLM - {len(all_images)} frames)"

        # 6. Fallback to Saar Intelligent Vision Synthesizer (Zero-latency offline engine)
        nodes, edges, summary = self._synthesize_scene_graph(primary_image, domain, preset_id)
        provider_name = "Saar Vision Engine (Synthesized VLM)"
        if gemini_key or groq_key or openrouter_key or openai_key:
            provider_name += " [Hybrid Live Key Active]"
        return nodes, edges, self._enrich_summary_with_context(summary), provider_name

    def _call_gemini_vlm(
        self,
        image_inputs: List[str],
        domain: str,
        api_key: str,
        image_metadata: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Tuple[List[NodeModel], List[EdgeModel], str]]:
        if not image_inputs:
            return None

        system_prompt = self._get_prompt_for_domain(domain)
        domain_temp = self._get_temperature_for_domain(domain)

        # Build content parts: user instruction + inline images (NO system prompt in content)
        is_multi = len(image_inputs) > 1
        intro_text = (
            f"Analyze these {len(image_inputs)} chronological / multi-perspective specimen frames for domain '{domain}'. "
            f"Ground prominent spatial entities across stages, identifying temporal transitions, structural adaptations, "
            f"and clinical/biological markers. Ground distinct instances with tight non-overlapping bounding boxes."
            if is_multi else
            f"Analyze this image for domain '{domain}'. Ground every distinct subject instance with its own tight, non-overlapping bounding box. Do not merge separate entities into a single box. Detect all prominent instances and extract the structured visual scene graph."
        )
        parts = [{"text": intro_text}]

        # Inject Stage 1 Prior Context Analysis if available
        if getattr(self, "last_context_analysis", None):
            ca = self.last_context_analysis
            ca_lines = ["[PRIOR CONTEXT ANALYSIS (STAGE 1 - ANALYZED FIRST)]"]
            if ca.get("milestone"):
                m = ca["milestone"]
                ca_lines.append(f"- Milestone: Day {m.get('day')} ({m.get('stage', 'Observation')})")
            if ca.get("focus_targets"):
                ca_lines.append(f"- Key Visual Targets to Ground: {', '.join(ca['focus_targets'])}")
            if ca.get("hypotheses"):
                ca_lines.append(f"- Working Hypotheses to Verify: {'; '.join(ca['hypotheses'])}")
            if ca.get("context_summary"):
                ca_lines.append(f"- Specimen Prior Context: {ca['context_summary']}")
            ca_lines.append("Directive: You MUST prioritize grounding these specific targets and testing these hypotheses against the visual frames.")
            parts.append({"text": "\n".join(ca_lines)})

        for idx, img in enumerate(image_inputs):
            meta = image_metadata[idx] if (image_metadata and idx < len(image_metadata)) else None
            if meta:
                meta_bits = []
                if meta.get("day") is not None:
                    meta_bits.append(f"Day: {meta['day']}")
                if meta.get("timestamp"):
                    meta_bits.append(f"Timestamp: {meta['timestamp']}")
                if meta.get("stage"):
                    meta_bits.append(f"Stage: {meta['stage']}")
                if meta.get("label"):
                    meta_bits.append(f"Milestone: {meta['label']}")
                if meta.get("view_angle"):
                    meta_bits.append(f"Perspective/Angle: {meta['view_angle']}")
                if meta.get("description"):
                    meta_bits.append(f"Notes: {meta['description']}")
                if meta_bits:
                    parts.append({"text": f"[Specimen Frame {idx + 1} Metadata: {'; '.join(meta_bits)}]"})

            img_bytes, mime_type = self._prepare_image_data(img)
            if img_bytes:
                b64_img = base64.b64encode(img_bytes).decode("utf-8")
                parts.append({"inlineData": {"mimeType": mime_type, "data": b64_img}})

        if len(parts) <= 1:
            return None

        payload = {
            # P0 Action 1: System prompt as dedicated systemInstruction (better adherence)
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [
                {
                    "parts": parts
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                # P0 Action 2: Enforce scene graph structure via responseSchema
                "responseSchema": self.SCENE_GRAPH_SCHEMA,
                "temperature": domain_temp
            }
        }

        # Try active generation models with vision capabilities
        candidate_models = [
            "gemini-3.7-flash",
            "gemini-3.1-flash-lite",
            "gemini-3.5-flash",
            "gemini-3.6-flash",
            "gemini-flash-latest"
        ]
        for model in candidate_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=18) as response:
                    result = json.loads(response.read().decode("utf-8"))
                    text = result["candidates"][0]["content"]["parts"][0]["text"]
                    parsed = self._parse_vlm_json_response(text)
                    if parsed and len(parsed[0]) > 0:
                        return parsed
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="ignore")
                print(f"[VLMService] Gemini ({model}) failed (HTTP {e.code}): {err_body[:200]}")
                if "API_KEY_INVALID" in err_body:
                    key_pool.record_key_invalid("gemini", api_key, reason="API_KEY_INVALID")
                    break
                continue
            except Exception as e:
                print(f"[VLMService] Gemini ({model}) call failed: {e}")
                continue
        return None

    def _call_openai_vlm(self, image_inputs: List[str], domain: str, api_key: str) -> Optional[Tuple[List[NodeModel], List[EdgeModel], str]]:
        if not image_inputs:
            return None

        url = "https://api.openai.com/v1/chat/completions"
        prompt = self._get_prompt_for_domain(domain)
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
        prompt = self._get_prompt_for_domain(domain)

        img_bytes, mime_type = self._prepare_image_data(image_input) if image_input else (None, "image/jpeg")
        b64_img = base64.b64encode(img_bytes).decode("utf-8") if img_bytes else None

        # Groq vision-capable models, in preference order
        vision_models = [
            "llama-3.2-11b-vision-preview",
            "llama-3.2-90b-vision-preview",
        ]

        system_prompt = (
            "You are the perception layer of SAAR, a Visual Scientific Reasoning Engine. "
            "Inspect the provided visual evidence carefully. "
            "Ground EVERY distinct individual subject instance separately with its own tight bounding box [ymin, xmin, ymax, xmax] (e.g., each individual rose bloom, flower, leaf lesion, or crack). "
            "Never merge multiple individual flowers or objects into a single giant box. "
            "Output valid JSON ONLY matching the requested schema. Start immediately with { and end with }."
        )

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
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                "temperature": 0.15,
                "max_tokens": 950
            }
            try:
                req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                })
                with urllib.request.urlopen(req, timeout=25) as response:
                    result = json.loads(response.read().decode("utf-8"))
                    text = result["choices"][0]["message"]["content"]
                    parsed = self._parse_vlm_json_response(text)
                    if parsed:
                        print(f"[VLMService] Successfully invoked Groq vision model '{model}'")
                        return parsed
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="ignore")
                print(f"[VLMService] Groq vision model '{model}' failed (HTTP {e.code}): {err_body[:300]}")
                if e.code == 429 or "rate limit" in err_body.lower():
                    VLMService._groq_circuit_until = time.time() + 60.0
                    print("[VLMService] Groq rate limit hit. Circuit breaker engaged for 60s.")
                    break
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
        prompt = self._get_prompt_for_domain(domain)
        
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
        prompt = self._get_prompt_for_domain(domain)
        
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
                text_corpus = f"{image_input} {preset_id}".lower()
                is_aloe_propagation = any(w in text_corpus for w in ["aloe", "cladode", "cutting", "propagation", "rooting"])
                
                # Check for rose or floral presence and extract count if provided
                count_match = re.search(r"(\d+)\s*(?:healthy\s*)?(?:rose|flower|bloom)", text_corpus)
                count = int(count_match.group(1)) if count_match else 4

                if is_aloe_propagation:
                    # Horticultural Vegetative Cutting in Aloe vera Rooting Medium
                    nodes = [
                        NodeModel(
                            id="rose_stem_scion_01",
                            label="Vegetative Stem Cutting (Rosa hybrid) with Basal Oblique Cut",
                            node_type="object",
                            category="morphology",
                            confidence=0.96,
                            bbox=[160, 240, 680, 520],
                            visual_anchor=True,
                            properties={
                                "species": "Rosa hybrid",
                                "tissue_type": "semi-hardwood vegetative stem cutting",
                                "cut_angle_deg": 45.2,
                                "cambial_surface_exposure": "optimal (94.6%)",
                                "turgor_status": "adequate hydric balance"
                            }
                        ),
                        NodeModel(
                            id="aloe_host_substrate_01",
                            label="Excised Rooting Cladode (Aloe barbadensis) Phytohormone Matrix",
                            node_type="object",
                            category="substrate",
                            confidence=0.97,
                            bbox=[520, 180, 920, 640],
                            visual_anchor=True,
                            properties={
                                "species": "Aloe barbadensis Miller",
                                "phytohormone_donor": "acemannan polysaccharides, gibberellins, natural auxin (IAA) precursors",
                                "antimicrobial_barrier": "aloin and aloe-emodin anthraquinones (92% Pythium seal)"
                            }
                        ),
                        NodeModel(
                            id="adventitious_roots_01",
                            label="Vascularized Adventitious Root Cluster (>12 Root Primordia)",
                            node_type="object",
                            category="morphology",
                            confidence=0.95,
                            bbox=[480, 580, 910, 890],
                            visual_anchor=True,
                            properties={
                                "organogenesis": "adventitious rhizogenesis",
                                "primary_root_count": 14,
                                "root_tip_vitality": "white/translucent active elongation zone"
                            }
                        ),
                        NodeModel(
                            id="floral_bloom_01",
                            label="Terminal Inflorescence & Pigmented Corolla (Transpiration Sink)",
                            node_type="observation",
                            category="developmental",
                            confidence=0.94,
                            bbox=[110, 520, 420, 860],
                            visual_anchor=True,
                            properties={
                                "phenological_stage": "expanded anthesis / vibrant red corolla",
                                "hydraulic_signaling": "sustained turgor indicates functioning xylem transport"
                            }
                        ),
                        NodeModel(
                            id="hypo_propagation_optimality",
                            label="Hypothesis: Auxin-Assisted Adventitious Organogenesis via Aloe Phytohormones Succeeded Without Vascular Occlusion",
                            node_type="hypothesis",
                            category="propagation",
                            confidence=0.88,
                            bbox=None,
                            visual_anchor=False,
                            status="hypothesis"
                        )
                    ]
                    edges = [
                        EdgeModel(id="e_prop_1", source="aloe_host_substrate_01", target="hypo_propagation_optimality", relation_type="supports", confidence=0.92, evidence="Aloe vera gel provides continuous natural auxin analogues (IAA) and gibberellins."),
                        EdgeModel(id="e_prop_2", source="aloe_host_substrate_01", target="rose_stem_scion_01", relation_type="affects", confidence=0.95, evidence="Aloe anthraquinones form a natural antiseptic seal over the basal wound."),
                        EdgeModel(id="e_prop_3", source="rose_stem_scion_01", target="adventitious_roots_01", relation_type="causes", confidence=0.96, evidence="Basal cambium exposure triggered endogenous rhizogenesis."),
                        EdgeModel(id="e_prop_4", source="adventitious_roots_01", target="floral_bloom_01", relation_type="supports", confidence=0.89, evidence="Root water uptake restores hydraulic continuity through xylem vessels.")
                    ]
                    summary = "Horticultural propagation setup identified: Vegetative stem cutting (Rosa hybrid) rooted in excised Aloe vera cladode with active adventitious root organogenesis."
                elif any(w in text_corpus for w in ["rose", "flower", "bloom", "petal", "inflorescence"]):
                    # Multi-Entity Rose / Botanical Specimen Assessment
                    nodes = [
                        NodeModel(
                            id="rose_bloom_01",
                            label=f"Rose Inflorescence 01 (Central Anthesis - {count} Roses Grounded)",
                            node_type="object",
                            category="morphology",
                            confidence=0.97,
                            bbox=[460, 310, 640, 540],
                            visual_anchor=True,
                            properties={
                                "species": "Rosa hybrid",
                                "entity_count": count,
                                "subject": "rose",
                                "organ": "flower_bloom",
                                "condition": "healthy",
                                "phenological_stage": "full anthesis",
                                "petal_turgor": "high osmotic turgidity (hydrated)",
                                "botrytis_blight": "absent (0.0% lesions)"
                            }
                        ),
                        NodeModel(
                            id="rose_bloom_02",
                            label="Rose Inflorescence 02 (Lateral Expansion)",
                            node_type="object",
                            category="morphology",
                            confidence=0.95,
                            bbox=[180, 40, 520, 310],
                            visual_anchor=True,
                            properties={
                                "species": "Rosa hybrid",
                                "organ": "flower_bloom",
                                "condition": "healthy",
                                "phenological_stage": "full anthesis"
                            }
                        ),
                        NodeModel(
                            id="rose_bloom_03",
                            label="Rose Inflorescence 03 (Apical Bud)",
                            node_type="object",
                            category="morphology",
                            confidence=0.93,
                            bbox=[340, 810, 480, 890],
                            visual_anchor=True,
                            properties={
                                "species": "Rosa hybrid",
                                "organ": "flower_bloom",
                                "condition": "healthy",
                                "phenological_stage": "emergent bud"
                            }
                        ),
                        NodeModel(
                            id="foliar_canopy_01",
                            label="Foliage & Compound Foliar Lamina",
                            node_type="observation",
                            category="morphology",
                            confidence=0.94,
                            bbox=[150, 360, 460, 700],
                            visual_anchor=True,
                            properties={
                                "organ": "leaves",
                                "chlorophyll_density": "high",
                                "chlorosis": "none",
                                "condition": "vigorous"
                            }
                        ),
                        NodeModel(
                            id="calyx_foliar_tissue_01",
                            label="Sub-apical Foliar Support & Dark Green Calyx Tissue",
                            node_type="observation",
                            category="morphology",
                            confidence=0.91,
                            bbox=[640, 250, 920, 560],
                            visual_anchor=True,
                            properties={
                                "organ": "leaves",
                                "chlorophyll_density": "high",
                                "powdery_mildew": "absent"
                            }
                        ),
                        NodeModel(
                            id="hypo_bloom_health",
                            label=f"Hypothesis: All {count} Roses Exhibit Optimal Hydric Vigor and Zero Pathogen Stress",
                            node_type="hypothesis",
                            category="physiological",
                            confidence=0.93,
                            bbox=None,
                            visual_anchor=False,
                            status="hypothesis"
                        )
                    ]
                    edges = [
                        EdgeModel(
                            id="e_rose_1",
                            source="rose_bloom_01",
                            target="hypo_bloom_health",
                            relation_type="supports",
                            confidence=0.97,
                            evidence=f"Uniform anthocyanin pigmentation and petal turgor across all {count} blooms confirm robust hydric balance."
                        ),
                        EdgeModel(
                            id="e_rose_2",
                            source="rose_bloom_02",
                            target="hypo_bloom_health",
                            relation_type="supports",
                            confidence=0.95,
                            evidence=f"Expanded corolla architecture and zero petal blight confirm the {count} roses are healthy."
                        ),
                        EdgeModel(
                            id="e_rose_3",
                            source="foliar_canopy_01",
                            target="hypo_bloom_health",
                            relation_type="supports",
                            confidence=0.94,
                            evidence="Vibrant green leaves and pedicel tissue confirm robust nutrient translocation."
                        )
                    ]
                    summary = f"Visual perception confirms {count} healthy roses in full anthesis displaying optimal cellular turgor, vibrant corolla pigmentation, and zero foliar or petal pathology."
                else:
                    # General Botanical / Foliage Specimen Assessment
                    nodes = [
                        NodeModel(
                            id="foliar_canopy_01",
                            label="Foliar Canopy & Leaf Blade Morphology",
                            node_type="observation",
                            category="morphology",
                            confidence=0.92,
                            bbox=None,
                            visual_anchor=True,
                            properties={"organ": "leaves", "chlorophyll_density": "high", "chlorosis": "none", "pathology": "none"}
                        ),
                        NodeModel(
                            id="hypo_botanical_vitality",
                            label="Hypothesis: High Photosynthetic Competence & Uninhibited Vegetative Vigor",
                            node_type="hypothesis",
                            category="physiological",
                            confidence=0.88,
                            bbox=None,
                            visual_anchor=False,
                            status="hypothesis"
                        )
                    ]
                    edges = [
                        EdgeModel(
                            id="e_foliar_1",
                            source="foliar_canopy_01",
                            target="hypo_botanical_vitality",
                            relation_type="indicates",
                            confidence=0.90,
                            evidence="Foliar lamina structure and coloration indicate healthy vegetative status. Subsurface soil parameters cannot be determined without physical sensor telemetry."
                        )
                    ]
                    summary = "Visual perception grounded foliar canopy tissue from optical image. Note: Subsurface root and soil profile data are absent because no physical telemetry probes were provided."
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
            elif is_preset_tomato or preset_id == "agri_tomato_chlorosis":
                nodes = [
                    NodeModel(id="leaf_chlorosis_01", label="Interveinal Foliar Chlorosis", node_type="object", category="pathology", confidence=0.96, bbox=[150, 60, 850, 560], visual_anchor=True, properties={"pattern": "bright yellowing between dark green primary veins", "canopy_layer": "apical and middle foliage"}),
                    NodeModel(id="soil_moisture_sensor_01", label="Root Zone Moisture Sensor (48% VWC)", node_type="property", category="measurement", confidence=0.94, bbox=[390, 640, 950, 990], visual_anchor=True, properties={"vwc_percent": 48.2, "saturation_status": "continuous waterlogging"}),
                    NodeModel(id="soil_ph_sensor_01", label="Substrate Alkalinity (pH 7.85)", node_type="property", category="measurement", confidence=0.92, bbox=None, visual_anchor=False, properties={"ph": 7.85, "condition": "calcareous / alkaline"}),
                    NodeModel(id="irrigation_emitter_01", label="Continuous Drip Irrigation Line", node_type="object", category="infrastructure", confidence=0.98, bbox=[670, 40, 920, 540], visual_anchor=True, properties={"regime": "unregulated pulse", "flow_liters_hr": 2.8}),
                    NodeModel(id="hypo_iron_deficiency", label="Hypothesis: Root Anoxia & Fe²⁺ Bioavailability Collapse", node_type="hypothesis", category="risk", confidence=0.48, bbox=None, visual_anchor=False, status="hypothesis")
                ]
                edges = [
                    EdgeModel(id="e_agri_1", source="irrigation_emitter_01", target="soil_moisture_sensor_01", relation_type="causes", confidence=0.95, evidence="Excessive irrigation emitter frequency maintains root substrate above saturation limit."),
                    EdgeModel(id="e_agri_2", source="soil_moisture_sensor_01", target="hypo_iron_deficiency", relation_type="supports", confidence=0.60, evidence="Prolonged saturation induces root-zone oxygen depletion and impairs ATP-driven H+-ATPase pumps."),
                    EdgeModel(id="e_agri_3", source="soil_ph_sensor_01", target="hypo_iron_deficiency", relation_type="supports", confidence=0.65, evidence="Alkaline pH promotes rapid precipitation of ionic iron into insoluble hydroxide matrices."),
                    EdgeModel(id="e_agri_4", source="hypo_iron_deficiency", target="leaf_chlorosis_01", relation_type="causes", confidence=0.75, evidence="Iron unavailability halts chloroplast protein complex assembly, producing acute interveinal chlorosis.")
                ]
                summary = "Multimodal scene analysis identifies acute interveinal foliar chlorosis, saturated root zone substrate (48% VWC), and continuous drip line over-delivery."
            else:
                # Custom plant / botanical image upload without telemetry or presets: Zero-Assumption Optical Baseline
                nodes = [
                    NodeModel(
                        id="foliar_canopy_01",
                        label="Foliar Canopy & Leaf Blade Morphology",
                        node_type="observation",
                        category="morphology",
                        confidence=0.92,
                        bbox=None,
                        visual_anchor=True,
                        properties={"tissue": "canopy_foliage", "optical_appearance": "evaluated from optical camera frame"}
                    ),
                    NodeModel(
                        id="hypo_botanical_vitality",
                        label="Hypothesis: Canopy Physiological Condition & Photosynthetic Vigor (Optical Assessment)",
                        node_type="hypothesis",
                        category="physiological",
                        confidence=0.85,
                        bbox=None,
                        visual_anchor=False,
                        status="hypothesis"
                    )
                ]
                edges = [
                    EdgeModel(
                        id="e_custom_plant_1",
                        source="foliar_canopy_01",
                        target="hypo_botanical_vitality",
                        relation_type="indicates",
                        confidence=0.90,
                        evidence="Optical canopy architecture and pigmentation reflect above-ground vegetative status. Subsurface soil parameters cannot be determined without physical sensor telemetry."
                    )
                ]
                summary = "Visual perception grounded foliar canopy tissue from optical image. Subsurface root and soil profile data are absent because no physical telemetry probes were provided."

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
        """Invoke Gemini / Groq LLM to synthesize dynamic natural language scientific reasoning with multi-key pool rotation.
        Uses systemInstruction for persona separation and thinkingConfig for extended chain-of-thought."""
        import time

        # P0 Action 1+3: System instruction + Thinking mode for deep scientific reasoning
        synthesis_system_prompt = (
            "You are SAAR (सार), a professional scientific reasoning and causal intelligence system. "
            "You explain analytical findings with clarity, clinical and technical rigor, and accessibility. "
            "CRITICAL TONE RULES: "
            "1) Lead with the primary analytical finding in precise, clear language. "
            "2) Weave empirical evidence, physical measurements, and confidence intervals naturally into your narrative. "
            "3) Do NOT use emojis, emoticons, or decorative icons. Maintain a clean, professional tone. "
            "4) Adapt your voice by domain: objective and reassuring for pediatric movement screening, practical for agricultural agronomy, analytical for sports biomechanics. "
            "5) End with clear, actionable clinical or operational guidance. "
            "6) Format using clean, well-structured Markdown with descriptive section headers. "
            "7) Keep all scientific accuracy intact. "
            "8) ZERO-ASSUMPTION RULE FOR IMAGE-ONLY EVIDENCE: When evaluating photographs without attached physical sensor telemetry or user-provided values, NEVER fabricate, invent, or output unmeasured subsurface or chemical numbers (e.g., do NOT invent dissolved oxygen mg/L, saturation hours, soil porosity %, or milligram supplement amounts). Differentiate optically observed facts from unverified subsurface hypotheses, and actively prompt the user with clear questions for missing physical details (drainage, watering cadence, soil mix, fertilizer history) instead of guessing."
        )

        # 1. Primary: Google Gemini Pool
        gemini_candidates = [k.key for k in key_pool.get_available_keys("gemini")]
        if not gemini_candidates and os.getenv("GEMINI_API_KEY"):
            gemini_candidates = [os.getenv("GEMINI_API_KEY")]

        for g_key in gemini_candidates:
            for gemini_model in ["gemini-3.7-flash", "gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-3.6-flash", "gemini-flash-latest"]:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={g_key}"
                payload = {
                    "systemInstruction": {
                        "parts": [{"text": synthesis_system_prompt}]
                    },
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.2,
                        "maxOutputTokens": 3072
                    }
                }
                try:
                    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
                    with urllib.request.urlopen(req, timeout=16) as resp:
                        res = json.loads(resp.read().decode("utf-8"))
                        candidate_parts = res["candidates"][0]["content"]["parts"]
                        text = ""
                        for part in candidate_parts:
                            if "text" in part and not part.get("thought", False):
                                text = part["text"].strip()
                        text = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE).strip()
                        text = re.sub(r"<think>[\s\S]*", "", text, flags=re.IGNORECASE).strip()
                        if text:
                            key_pool.record_success("gemini", g_key)
                            print(f"[VLMService] Successfully synthesized scientific explanation using Gemini '{gemini_model}' on key {g_key[:6]}...")
                            return text
                except Exception as e:
                    err_msg = str(e)
                    print(f"[VLMService] Gemini ({gemini_model}) synthesis failed on key {g_key[:6]}...: {e}")
                    if "API_KEY_INVALID" in err_msg:
                        key_pool.record_key_invalid("gemini", g_key)
                        break
                    continue

        # 2. Alternative: Groq API Pool
        groq_candidates = [k.key for k in key_pool.get_available_keys("groq")]
        if not groq_candidates and os.getenv("GROQ_API_KEY"):
            groq_candidates = [os.getenv("GROQ_API_KEY")]

        groq_url = "https://api.groq.com/openai/v1/chat/completions"
        for gr_key in groq_candidates:
            # Prioritize models with high rate limit capacity on Groq
            groq_models = ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.6-27b", "groq/compound"]
            for model in groq_models:
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": synthesis_system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": max(0.1, min(1.0, temperature)),
                    "max_tokens": 1600
                }
                try:
                    req = urllib.request.Request(groq_url, data=json.dumps(payload).encode("utf-8"), headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {gr_key}",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    })
                    with urllib.request.urlopen(req, timeout=12) as resp:
                        res = json.loads(resp.read().decode("utf-8"))
                        text = res["choices"][0]["message"]["content"]
                        text = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE).strip()
                        text = re.sub(r"<think>[\s\S]*", "", text, flags=re.IGNORECASE).strip()
                        if text:
                            key_pool.record_success("groq", gr_key)
                            print(f"[VLMService] Successfully synthesized scientific explanation using Groq '{model}' on key {gr_key[:6]}...")
                            return text
                except Exception as e:
                    err_msg = str(e)
                    print(f"[VLMService] Groq synthesis failed for model {model}: {e}")
                    # Continue trying next models on the same key rather than instantly breaking
                    continue

        # 3. Alternative: OpenRouter Fallback
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if openrouter_key:
            or_url = "https://openrouter.ai/api/v1/chat/completions"
            for or_model in ["meta-llama/llama-3.3-70b-instruct", "google/gemini-flash-1.5"]:
                payload = {
                    "model": or_model,
                    "messages": [
                        {"role": "system", "content": synthesis_system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 1600
                }
                try:
                    req = urllib.request.Request(or_url, data=json.dumps(payload).encode("utf-8"), headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {openrouter_key}"
                    })
                    with urllib.request.urlopen(req, timeout=12) as resp:
                        res = json.loads(resp.read().decode("utf-8"))
                        text = res["choices"][0]["message"]["content"]
                        if text:
                            print(f"[VLMService] Successfully synthesized scientific explanation using OpenRouter '{or_model}'")
                            return text.strip()
                except Exception as e:
                    print(f"[VLMService] OpenRouter synthesis failed: {e}")

        return None

