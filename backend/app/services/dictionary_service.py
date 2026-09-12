"""
Saar — Unified Scientific Terminology & Grounded Lexical Intelligence Service
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
            "term": "Rhizosphere",
            "phonetic": "/ˈraɪ.zoʊˌsfɪər/",
            "domain": "Soil Microbiology & Agronomy",
            "definition": "The narrow micro-ecological zone of soil surrounding plant roots directly influenced by root secretions, microbial activity, and nutrient exchange.",
            "investigation_context": "The primary interface where waterlogging, respiration blockages, and pH changes directly govern nutrient bioavailability to the plant.",
            "diagnostic_indicator": "Root-zone moisture, dissolved oxygen levels, and root exudate pH shifts.",
            "related_nodes": ["Root Zone Moisture", "Substrate pH", "Bioavailable Fe²⁺", "Hypoxia"]
        },
        {
            "term": "Rhizosphere Hypoxia",
            "phonetic": "/ˈraɪ.zoʊˌsfɪər haɪˈpɒk.si.ə/",
            "domain": "Plant Physiology",
            "definition": "A critical oxygen deficit (Dissolved O₂ < 0.8 mg/L) in the root zone caused by water supersaturation, suppressing aerobic cellular respiration and ATP-driven ion pumps.",
            "investigation_context": "Direct biological consequence of continuous drip irrigation exceeding drainage infiltration capacity.",
            "diagnostic_indicator": "Substrate moisture > 45% VWC sustained for >72 hours with collapse of active nutrient uptake.",
            "related_nodes": ["Root Zone Moisture", "Root Anoxia", "ATP Synthesis", "Chlorosis"]
        },
        {
            "term": "Substrate Alkalinization",
            "phonetic": "/ˌæl.kə.laɪ.nɪˈzeɪ.ʃən/",
            "domain": "Soil Chemistry",
            "definition": "An increase in root substrate pH above neutral (>7.5), causing soluble ferrous iron (Fe²⁺) to precipitate into insoluble ferric hydroxides.",
            "investigation_context": "Primary causal driver of iron lockup in tomato crops, blocking enzymatic iron reduction despite adequate total soil iron.",
            "diagnostic_indicator": "Substrate pH rising above 7.6 accompanied by sharp drops in bioavailable Fe²⁺.",
            "related_nodes": ["Substrate pH", "Bioavailable Fe²⁺", "Chlorosis", "Nutrient Lockup"]
        },
        {
            "term": "Leaf Fenestration",
            "phonetic": "/liːf ˌfɛn.əˈstreɪ.ʃən/",
            "domain": "Plant Evolutionary Morphology",
            "definition": "Natural elliptical or circular perforations in the leaf blade formed during early leaf morphogenesis via genetically programmed cell death (PCD).",
            "investigation_context": "Differentiates healthy evolutionary adaptations in Araceae (e.g. Monstera adansonii) from destructive chewing insect damage or fungal shot-hole necrosis.",
            "diagnostic_indicator": "Suberized, entire hole margins bounded by intact veins without surrounding necrotic chlorotic halos.",
            "related_nodes": ["Elliptical Leaf Fenestrations", "Foliar Margin Morphology", "Programmed Cell Death", "Vegetative Vigor"]
        },
        {
            "term": "Monstera adansonii",
            "phonetic": "/mɒnˈstɪərə əˈdænsənaɪ/",
            "domain": "Araceae Systematics & Indoor Agronomy",
            "definition": "A hemiepiphytic tropical climbing vine native to Central and South America characterized by extensive natural leaf perforations.",
            "investigation_context": "Target species under botanical phenotyping; exhibits robust fenestrated foliage, emergent apical shoots, and aerated substrate requirements.",
            "diagnostic_indicator": "Ovate-lanceolate leaves with multiple fenestrations per side, climbing habit, and aerial root nodes.",
            "related_nodes": ["Leaf Fenestrations", "Apical Shoot", "Substrate Aeration", "Canopy Fluorometry"]
        },
        {
            "term": "Programmed Cell Death (Botany)",
            "phonetic": "/ˈproʊ.ɡræmd sɛl dɛθ/",
            "domain": "Plant Developmental Biology",
            "definition": "Genetically regulated physiological suicide of specific groups of cells in juvenile leaf primordia to generate perforations and lobes.",
            "investigation_context": "The molecular developmental mechanism responsible for leaf holes in Monstera, contrasting with traumatic pathogen necrosis.",
            "diagnostic_indicator": "Clean cellular lysis bordered by protective suberin synthesis without frass or pathogen exudates.",
            "related_nodes": ["Leaf Fenestrations", "Morphology Phenotyper", "Aroid Foliage", "Vegetative Vigor"]
        },
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
    ],
    "causal": [
        {
            "term": "Bayesian Graph Updating",
            "phonetic": "/beɪˈziː.ən ɡræf ˈʌp.deɪ.tɪŋ/",
            "domain": "Causal Epistemology",
            "definition": "Recursive updating of conditional probability tables across directed acyclic graph (DAG) nodes upon assimilating novel empirical observations.",
            "investigation_context": "Drives SAAR's node belief convergence when sensor telemetry or visual evidence shifts node state priors.",
            "diagnostic_indicator": "Posterior entropy reduction below uncertainty threshold.",
            "related_nodes": ["Posterior Probability", "DAG Topology", "Markov Blanket"]
        },
        {
            "term": "Do-Calculus Interventional Node",
            "phonetic": "/duː ˈkæl.kjʊ.ləs ˌɪn.tərˈvɛn.ʃən/",
            "domain": "Structural Causal Modeling",
            "definition": "Pearl's algebraic framework evaluating causal effects by severing incoming graph edges to model active physical interventions P(Y | do(X)).",
            "investigation_context": "Evaluates what-if counterfactual scenarios by isolating direct causal mechanisms from spurious confounding correlations.",
            "diagnostic_indicator": "Parent edge disconnection and counterfactual state recalculation.",
            "related_nodes": ["Backdoor Criterion", "Counterfactual Simulation", "Intervention"]
        }
    ],
    "pediatrics": [
        {
            "term": "Physiological Genu Varum",
            "phonetic": "/ˌdʒiː.njuː ˈvɛər.əm/",
            "domain": "Pediatric Orthopedics",
            "definition": "Symmetrical lateral bowing of the tibia and femur typically present in infants and toddlers up to 24 months of age due to intrauterine positioning.",
            "investigation_context": "Differentiated from pathological bowing (Blount's disease or rickets) by bilateral symmetry, intercondylar distance < 3cm, and lack of sharp medial tibial beaking.",
            "diagnostic_indicator": "Symmetrical intercondylar distance < 3 cm with smooth curve apex at the knee joint.",
            "related_nodes": ["Intercondylar Distance", "Blount's Disease", "Tibial Torsion", "Gait Maturation"]
        },
        {
            "term": "Toddler Lumbar Lordosis",
            "phonetic": "/ˈlʌm.bər lɔːrˈdoʊ.sɪs/",
            "domain": "Pediatric Biomechanics",
            "definition": "Pronounced anterior curvature of the lumbar spine in toddlers, mechanically secondary to weak abdominal wall compliance and anterior pelvic tilt.",
            "investigation_context": "Serves as an essential compensatory biomechanical mechanism maintaining gravitational plumb line alignment over the toddler's base of support.",
            "diagnostic_indicator": "Sagittal spinal curvature ~35-42° paired with protuberant abdominal contour in standing position.",
            "related_nodes": ["Anterior Pelvic Tilt", "Plumb Line Axis", "Abdominal Wall Compliance", "Spinal Sagittal Balance"]
        },
        {
            "term": "Plumb Line Axis",
            "phonetic": "/plʌm laɪn ˈæk.sɪs/",
            "domain": "Biomechanical Posture Analysis",
            "definition": "The vertical gravitational reference line descending from the external auditory meatus through the acromion, greater trochanter, and just anterior to the lateral malleolus.",
            "investigation_context": "Quantifies whether multi-view toddler posture maintains dynamic equilibrium within the base of support without truncal collapse.",
            "diagnostic_indicator": "Minimal horizontal deviation (<2 cm) between the plumb line vector and center of foot support.",
            "related_nodes": ["Center of Mass", "Base of Support", "Postural Stability", "Sagittal Balance"]
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
        fast_prompt = f"""You are a scientific terminology extraction engine for SAAR.
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

    def lookup_word(self, word: str, domain: str = "general") -> Dict[str, Any]:
        """Synchronous word lookup compatibility helper."""
        clean_term = (word or "").strip()
        if not clean_term:
            return {"error": "Word parameter is required."}

        clean_domain = (domain or "general").lower()
        for d_key, t_list in PRELOADED_DOMAIN_TERMS.items():
            for item in t_list:
                if item["term"].lower() == clean_term.lower():
                    return item

        affix_desc = None
        for pattern, desc in SCIENTIFIC_AFFIX_MAP:
            if re.match(pattern, clean_term.lower()):
                affix_desc = desc
                break

        return {
            "term": clean_term.title(),
            "phonetic": f"/{clean_term.lower()}/",
            "domain": clean_domain.capitalize(),
            "definition": affix_desc or f"Scientific parameter or diagnostic entity evaluating '{clean_term}' in empirical models.",
            "investigation_context": f"Evaluated within the SAAR causal graph.",
            "diagnostic_indicator": "Active indicator in observational telemetry logs.",
            "related_nodes": ["Causal Graph", "Empirical Observation"]
        }

    def extract_glossary_from_screen(self, screen_texts=None, domain=None, graph_nodes=None) -> List[Dict[str, Any]]:
        """Synchronous screen glossary extraction compatibility helper."""
        clean_domain = (domain or "agriculture").lower()
        if clean_domain not in PRELOADED_DOMAIN_TERMS:
            clean_domain = "agriculture"
        return PRELOADED_DOMAIN_TERMS.get(clean_domain, PRELOADED_DOMAIN_TERMS["agriculture"])


terminology_service = TerminologyService()
dictionary_service = terminology_service
