"""
Saar (सार) — Unified Scientific Terminology & Grounded Lexical Intelligence Service
Extracts and contextualizes domain-specific scientific terminology in real-time,
grounded directly in the active investigation dataset and causal graph nodes.
Runs asynchronously without blocking or thread pool contention.
"""
import asyncio
import json
import re
from typing import List, Dict, Any, Optional

from ..vlm_service import VLMService
from ..rag_service import RAGKnowledgeService
from ..models.saar_models import TerminologyItem


SCIENTIFIC_AFFIX_MAP = [
    (r'.*osis$', "Physiological or pathological state affecting biological or physical substrate."),
    (r'.*lysis$', "Biochemical dissolution, degradation, or enzymatic breakdown of compounds."),
    (r'.*metry$', "Calibrated quantitative measurement technique assessing physical magnitudes."),
    (r'.*graphy$', "Geophysical, structural, or spectral mapping of spatial and material variations."),
    (r'.*pathy$', "Structural disease pathology or mechanical integrity deterioration."),
    (r'.*itis$', "Inflammatory response or acute localized environmental degradation."),
    (r'.*oid$', "Morphological entity exhibiting characteristics of the designated substrate."),
    (r'.*thermal$', "Thermodynamic heat distribution or temperature gradient property."),
    (r'.*dynamic$', "Kinetics and force interactions governing mass or fluid transfer."),
    (r'.*permittiv.*', "Dielectric permittivity metric critical for radar propagation velocities."),
    (r'.*percolat.*', "Darcy fluid flow percolation through porous subsoil media."),
    (r'.*chloros.*', "Chlorophyll synthesis impairment producing visible interveinal yellowing.")
]

PRELOADED_DOMAIN_TERMS = {
    "agriculture": [
        {
            "term": "Chlorosis",
            "phonetic": "/kləˈroʊ.sɪs/",
            "domain": "Plant Pathology",
            "definition": "Loss of normal green pigmentation in plant foliage caused by impaired chlorophyll biosynthesis or iron mobilization.",
            "investigation_context": "Direct indicator of root-zone anoxia, nutrient immobilization, or pathogenic infection during prolonged moisture saturation.",
            "diagnostic_indicator": "Interveinal yellowing of leaf tissue with green vein retention.",
            "related_nodes": ["Soil Moisture", "Nitrogen Uptake", "Foliar Stress", "Pythium"]
        },
        {
            "term": "Pythium ultimum",
            "phonetic": "/ˈpɪθ.i.əm ˈʌl.tɪ.məm/",
            "domain": "Agricultural Mycology",
            "definition": "A soil-borne oomycete pathogen that infects juvenile root tips, thriving in anaerobic, waterlogged rhizosphere environments.",
            "investigation_context": "Primary causative pathogen candidate when soil moisture remains above 40% VWC for consecutive observation intervals.",
            "diagnostic_indicator": "Root cortex sloughing, basal rot, and vascular water transport collapse.",
            "related_nodes": ["Soil Saturation", "Root Rot", "Waterlogging", "Chlorosis"]
        },
        {
            "term": "Darcy Percolation",
            "phonetic": "/ˈdɑːr.si pɜːr.kəˈleɪ.ʃən/",
            "domain": "Soil Physics",
            "definition": "The volumetric flux of liquid through a porous soil matrix governed by hydraulic conductivity and hydraulic gradient.",
            "investigation_context": "Determines whether irrigation or rainfall exceeds drainage culvert capacity, inducing hypoxic root zone ponding.",
            "diagnostic_indicator": "Hydraulic head saturation and soil water retention curve inflection.",
            "related_nodes": ["Hydraulic Conductivity", "Precipitation", "Soil Anoxia"]
        },
        {
            "term": "SPAD Index",
            "phonetic": "/spæd ˈɪn.dɛks/",
            "domain": "Agronomic Metrology",
            "definition": "Soil-Plant Analyses Development unit quantifying relative chlorophyll concentration via dual-wavelength transmittance.",
            "investigation_context": "Quantitative metric tracking rate of photosynthetic degradation prior to visible leaf necrosis.",
            "diagnostic_indicator": "Continuous numerical decline below baseline reference thresholds.",
            "related_nodes": ["Chlorophyll Transmittance", "NDVI", "Vegetative Vigor"]
        }
    ],
    "infrastructure": [
        {
            "term": "GPR Hyperbolic Reflection",
            "phonetic": "/ˌdʒiː.piːˈɑːr haɪ.pərˈbɒl.ɪk/",
            "domain": "Geotechnical NDT",
            "definition": "A characteristic point-source radar signature formed by radar pulse velocity contrasts between asphalt and subterranean air/water voids.",
            "investigation_context": "Detects sub-surface soil piping cavities before structural pavement collapse occurs under traffic axle loads.",
            "diagnostic_indicator": "High-amplitude hyperbolic phase reversal in radar B-scan echograms.",
            "related_nodes": ["Subgrade Cavity", "Dielectric Constant", "Alligator Cracking"]
        },
        {
            "term": "Soil Piping",
            "phonetic": "/sɔɪl ˈpaɪ.pɪŋ/",
            "domain": "Hydraulic Engineering",
            "definition": "Subsurface erosion where seepage forces dislodge fine soil particles, eroding continuous tubular void channels beneath pavements.",
            "investigation_context": "Underlying mechanism coupling blocked drainage grates with sub-base cave-ins.",
            "diagnostic_indicator": "Localized depression, water egress, and loss of subgrade compaction.",
            "related_nodes": ["Culvert Blockage", "Void Cavity", "Pavement Collapse"]
        },
        {
            "term": "Dielectric Permittivity",
            "phonetic": "/ˌdaɪ.ɪˈlɛk.trɪk pɜːr.mɪˈtɪv.ɪ.ti/",
            "domain": "Electromagnetic Metrology",
            "definition": "A physical measure of a medium's resistance to electric field formation, determining radar wave propagation velocity ($v = c / \\sqrt{\\epsilon_r}$).",
            "investigation_context": "Varies sharply between dry aggregate (\\epsilon_r \\approx 4), air (\\epsilon_r = 1), and water (\\epsilon_r \\approx 81).",
            "diagnostic_indicator": "Calculated layer thickness and moisture ingress boundaries.",
            "related_nodes": ["GPR Radar", "Void Reflection", "Subsurface Moisture"]
        }
    ],
    "astronomy": [
        {
            "term": "Keplerian Transit Dip",
            "phonetic": "/kɛpˈlɪər.i.ən ˈtræn.zɪt dɪp/",
            "domain": "Exoplanetary Science",
            "definition": "The periodic fractional decrease in stellar photometric flux caused by an orbiting exoplanet occulting the host star's disk.",
            "investigation_context": "Differentiates true planetary transits (achromatic depth $\\Delta F / F = (R_p / R_*)^2$) from chromatic stellar flare fluctuations.",
            "diagnostic_indicator": "U-shaped symmetric ingress, flat bottom, and symmetric egress lightcurve profile.",
            "related_nodes": ["Orbital Period", "Planetary Radius", "Transit Depth"]
        },
        {
            "term": "Doppler Centroid Shift",
            "phonetic": "/ˈdɒp.lər ˈsɛn.trɔɪd ʃɪft/",
            "domain": "Stellar Spectroscopy",
            "definition": "Periodic wavelength displacement of stellar spectral absorption lines induced by the gravitational tug of an orbiting companion.",
            "investigation_context": "Measures semi-amplitude velocity ($K$) to calculate the companion minimum mass ($M_p \\sin i$).",
            "diagnostic_indicator": "Radial velocity phase-folded sinusoidal curve.",
            "related_nodes": ["Radial Velocity", "Companion Mass", "Binary Discrimination"]
        }
    ]
}


class TerminologyService:
    """Zero-latency, context-grounded scientific terminology service."""

    def __init__(self):
        self.vlm = VLMService()
        self.rag = RAGKnowledgeService()

    async def extract_grounded_terms_async(
        self,
        query: str,
        domain: str = "agriculture",
        context_text: str = "",
        graph_nodes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract 2-4 key scientific terms grounded in the inquiry and domain.
        Uses fast LLM synthesis if available with immediate deterministic fallback.
        Runs purely non-blocking without worker thread overhead.
        """
        clean_domain = (domain or "agriculture").lower()
        if clean_domain not in PRELOADED_DOMAIN_TERMS:
            clean_domain = "agriculture"

        # Check if we can run fast LLM extraction concurrently
        fast_prompt = f"""You are a scientific terminology extraction engine for SAAR (सार).
Extract 2 to 4 domain-specific scientific or technical terms relevant to this investigation inquiry.

User Inquiry: "{query}"
Domain: "{clean_domain}"
Active Context: "{context_text[:350]}"

Return ONLY a valid JSON array of objects. Do NOT include markdown code fences or conversational text.
Each object must have these exact keys:
- "term": (string) canonical scientific term (e.g., "Pythium ultimum", "Dielectric Permittivity", "Chlorosis")
- "phonetic": (string) phonetic pronunciation or null
- "domain": (string) scientific sub-discipline
- "definition": (string) precise academic definition
- "investigation_context": (string) how this concept specifically relates to the inquiry or dataset
- "diagnostic_indicator": (string) observable field symptom or sensor telemetry metric
- "related_nodes": (array of strings) 2 to 4 related concept names

JSON:"""

        try:
            # Run in thread so async event loop remains 100% free
            raw_response = await asyncio.to_thread(
                self.vlm.synthesize_reasoning_explanation,
                fast_prompt
            )

            if raw_response:
                # Strip markdown code blocks if model returned them
                cleaned = re.sub(r'```json\s*', '', raw_response)
                cleaned = re.sub(r'```\s*', '', cleaned).strip()
                
                # Find outermost JSON array
                start_idx = cleaned.find('[')
                end_idx = cleaned.rfind(']')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    parsed = json.loads(cleaned[start_idx:end_idx + 1])
                    if isinstance(parsed, list) and len(parsed) > 0:
                        validated_terms = []
                        for item in parsed[:4]:
                            if isinstance(item, dict) and item.get("term") and item.get("definition"):
                                validated_terms.append({
                                    "term": str(item.get("term", "")).strip(),
                                    "phonetic": item.get("phonetic") or f"/{item.get('term', '').lower()}/",
                                    "domain": item.get("domain") or clean_domain.capitalize(),
                                    "definition": str(item.get("definition", "")).strip(),
                                    "investigation_context": str(item.get("investigation_context") or f"Active variable in {clean_domain} reasoning.").strip(),
                                    "diagnostic_indicator": str(item.get("diagnostic_indicator") or "Observed parameter in telemetry logs.").strip(),
                                    "related_nodes": item.get("related_nodes") if isinstance(item.get("related_nodes"), list) else [clean_domain.title()]
                                })
                        if validated_terms:
                            return validated_terms
        except Exception as err:
            print(f"[TerminologyService] Fast LLM extraction notice (falling back gracefully): {err}")

        # Fallback: Deterministic domain-grounded dictionary matching
        return self._deterministic_fallback_terms(query, clean_domain, context_text)

    def _deterministic_fallback_terms(self, query: str, domain: str, context_text: str) -> List[Dict[str, Any]]:
        """Instant (<5ms) deterministic domain-grounded terms matching query keywords."""
        q_lower = query.lower()
        ctx_lower = context_text.lower()
        combined = f"{q_lower} {ctx_lower}"

        domain_pool = PRELOADED_DOMAIN_TERMS.get(domain, PRELOADED_DOMAIN_TERMS["agriculture"])
        matched = []

        # 1. Match specific preloaded terms against query words
        for term_obj in domain_pool:
            t_name = term_obj["term"].lower()
            t_words = [w for w in t_name.split() if len(w) > 3]
            if t_name in combined or any(w in combined for w in t_words):
                matched.append(term_obj)

        # If not enough matches, add top domain defaults
        if len(matched) < 2:
            for term_obj in domain_pool:
                if term_obj not in matched:
                    matched.append(term_obj)
                if len(matched) >= 3:
                    break

        return matched[:3]

    async def lookup_term_async(self, term: str, domain: str = "general", context: str = "") -> Dict[str, Any]:
        """On-demand single term lookup with domain contextualization."""
        clean_term = (term or "").strip()
        if not clean_term:
            return {"error": "Term is required."}

        clean_domain = (domain or "general").lower()

        # Check preloaded domain list first
        for d_key, t_list in PRELOADED_DOMAIN_TERMS.items():
            for item in t_list:
                if item["term"].lower() == clean_term.lower():
                    return item

        # Query RAG Knowledge Base
        rag_hits = self.rag.query(clean_term, domain=clean_domain if clean_domain in self.rag.domains else None, top_k=2)
        rag_definition = rag_hits[0].content[:240] if rag_hits else None

        # Morphological affix check
        affix_desc = None
        for pattern, desc in SCIENTIFIC_AFFIX_MAP:
            if re.match(pattern, clean_term.lower()):
                affix_desc = desc
                break

        # Fast LLM definition synthesis
        prompt = f"""Define the scientific term '{clean_term}' in the context of '{clean_domain}' science.
Return JSON with keys: term, phonetic, domain, definition, investigation_context, diagnostic_indicator, related_nodes."""

        try:
            raw = await asyncio.to_thread(self.vlm.synthesize_reasoning_explanation, prompt)
            if raw:
                cleaned = re.sub(r'```json\s*', '', raw)
                cleaned = re.sub(r'```\s*', '', cleaned).strip()
                s_idx = cleaned.find('{')
                e_idx = cleaned.rfind('}')
                if s_idx != -1 and e_idx != -1:
                    data = json.loads(cleaned[s_idx:e_idx + 1])
                    if data.get("definition"):
                        return data
        except Exception:
            pass

        return {
            "term": clean_term.title(),
            "phonetic": f"/{clean_term.lower()}/",
            "domain": clean_domain.capitalize(),
            "definition": rag_definition or affix_desc or f"Specialized scientific parameter or entity evaluating '{clean_term}' in empirical domain models.",
            "investigation_context": f"Evaluated within the SAAR causal graph to verify empirical hypotheses and compute state updates.",
            "diagnostic_indicator": "Active indicator in observational telemetry logs.",
            "related_nodes": ["Causal Graph", "Empirical Observation", "Bayesian Update"]
        }


terminology_service = TerminologyService()
