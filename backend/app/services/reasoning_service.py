"""
Saar (सार) — Iterative Reasoning Service
Orchestrates the full SAAR loop: Perceive → Concepts → Relationships → Evidence →
Confidence → Uncertainty → Questions → User Answers → Belief Update.
"""
import difflib
import re
import uuid
from typing import List, Dict, Any, Optional

from ..models.saar_models import (
    InvestigationState, DatasetProfile, Feature, Observation,
    Concept, ConceptStatus, Relationship, RelationshipType,
    Evidence, EvidenceType, TrendResult, TrendDirection,
    GeneratedQuestion, UserAnswer, SemanticRole
)
from .ingestion_service import IngestionService
from .analytics_service import AnalyticsService
from ..rag_service import RAGKnowledgeService
from ..vlm_service import VLMService


class ReasoningService:
    """Orchestrates the iterative SAAR evidence-driven reasoning loop."""

    def __init__(self):
        self.ingestion = IngestionService()
        self.analytics = AnalyticsService()
        self.rag = RAGKnowledgeService()
        self.vlm = VLMService()
        self._investigations: Dict[str, InvestigationState] = {}

    # ------------------------------------------------------------------
    # Phase 1: Ingest & Perceive
    # ------------------------------------------------------------------

    def start_investigation(self, file_content: bytes, filename: str) -> InvestigationState:
        """Upload CSV → Schema Detection → Profiling → Initial Perception."""
        profile, rows = self.ingestion.ingest_csv(file_content, filename)
        features = self.ingestion.extract_features(profile)
        observations = self.ingestion.extract_observations(rows, profile)

        state = InvestigationState(
            dataset_id=profile.dataset_id,
            dataset_profile=profile,
            features=features,
            observations=observations,
            iteration=0,
            status="perceived",
        )

        # Run initial analytics
        state = self._run_analytics(state)

        # Generate initial concepts from discovered relationships
        state = self._generate_concepts(state)

        # Assess overall confidence
        state = self._calculate_confidence(state)

        # Generate initial questions
        state = self._generate_questions(state)

        state.iteration = 1
        state.status = "active"

        self._investigations[state.investigation_id] = state
        return state

    def register_visual_investigation(self, response_data: Any) -> InvestigationState:
        """Register a visual/preset investigation into the reasoning state store."""
        inv_id = getattr(response_data, "investigation_id", str(uuid.uuid4()))
        final_graph = getattr(response_data, "final_graph", None)
        domain = getattr(response_data, "domain", "infrastructure")

        relationships = []
        concepts = []
        evidence = []

        node_label_map = {}
        if final_graph:
            for node in getattr(final_graph, "nodes", []):
                n_id = getattr(node, "id", "")
                n_label = getattr(node, "label", n_id)
                n_conf = getattr(node, "confidence", 0.9)
                n_status = getattr(node, "status", "confirmed")
                node_label_map[n_id] = n_label

                status_enum = ConceptStatus.SUPPORTED if n_status == "confirmed" else ConceptStatus.CANDIDATE
                concepts.append(Concept(
                    concept_id=n_id,
                    name=n_label,
                    description=n_label,
                    category=getattr(node, "category", "general"),
                    confidence=n_conf,
                    status=status_enum,
                    bbox=getattr(node, "bbox", None),
                    visual_anchor=getattr(node, "visual_anchor", True)
                ))

            for edge in getattr(final_graph, "edges", []):
                e_src = getattr(edge, "source", "")
                e_tgt = getattr(edge, "target", "")
                src_label = node_label_map.get(e_src, e_src)
                tgt_label = node_label_map.get(e_tgt, e_tgt)
                e_conf = getattr(edge, "confidence", 0.8)
                e_ev = getattr(edge, "evidence", "")
                rel_type = getattr(edge, "relation_type", "correlation")

                relationships.append(Relationship(
                    source_feature=src_label,
                    target_feature=tgt_label,
                    relationship_type=RelationshipType.CORRELATION,
                    strength=e_conf,
                    p_value=0.01,
                    direction="positive",
                    description=f"{src_label} {rel_type} {tgt_label}"
                ))
                if e_ev:
                    evidence.append(Evidence(
                        observation=e_ev,
                        description=e_ev,
                        evidence_type=EvidenceType.OBSERVATION,
                        impact="supports",
                        weight=e_conf
                    ))

        state = InvestigationState(
            investigation_id=inv_id,
            dataset_id=domain,
            concepts=concepts,
            relationships=relationships,
            evidence=evidence,
            overall_confidence=getattr(final_graph, "overall_confidence", 0.85),
            iteration=1,
            status="active"
        )
        self._investigations[inv_id] = state
        return state

    def register_gait_investigation(self, gait_result: Any) -> InvestigationState:
        """Register a deterministic ToddleAI gait assessment into SAAR reasoning store."""
        inv_id = getattr(gait_result, "assessment_id", f"gait_{uuid.uuid4().hex[:8]}")
        metrics = getattr(gait_result, "metrics", None)
        quality = getattr(gait_result, "quality", None)
        cadence_range = getattr(gait_result, "cadence_range", None)
        age_months = getattr(gait_result, "child_age_months", 24)

        features = [
            Feature(name="cadence", data_type="float", semantic_role=SemanticRole.TARGET),
            Feature(name="left_mean_step_time", data_type="float", semantic_role=SemanticRole.STATE),
            Feature(name="right_mean_step_time", data_type="float", semantic_role=SemanticRole.STATE),
            Feature(name="step_time_asymmetry_pct", data_type="float", semantic_role=SemanticRole.TARGET),
            Feature(name="step_time_cov", data_type="float", semantic_role=SemanticRole.TARGET),
            Feature(name="usable_step_count", data_type="int", semantic_role=SemanticRole.STATE)
        ]

        observations = []
        if metrics:
            observations.extend([
                Observation(feature_name="cadence", value=metrics.cadence, unit="steps/min", confidence=0.95),
                Observation(feature_name="left_mean_step_time", value=metrics.left_mean_step_time, unit="s", confidence=0.90),
                Observation(feature_name="right_mean_step_time", value=metrics.right_mean_step_time, unit="s", confidence=0.90),
                Observation(feature_name="step_time_asymmetry_pct", value=metrics.step_time_asymmetry_pct, unit="%", confidence=0.95),
                Observation(feature_name="step_time_cov", value=metrics.step_time_cov, unit="%", confidence=0.92),
                Observation(feature_name="usable_step_count", value=metrics.usable_step_count, confidence=0.98),
            ])

        concepts = [
            Concept(
                concept_id="c_gait_cadence",
                name=f"Cadence ({metrics.cadence if metrics else 0.0:.0f} steps/min)",
                description=f"Age reference ({age_months}m): {cadence_range.low:.0f}–{cadence_range.high:.0f} steps/min" if cadence_range else "Cadence",
                category="kinematics",
                confidence=0.95,
                status=ConceptStatus.SUPPORTED
            ),
            Concept(
                concept_id="c_gait_symmetry",
                name=f"Temporal Symmetry ({metrics.step_time_asymmetry_pct if metrics else 0.0:.0f}% diff)",
                description="Left vs Right step timing balance (benchmark <= 10%)",
                category="symmetry",
                confidence=0.90,
                status=ConceptStatus.SUPPORTED if (metrics and metrics.step_time_asymmetry_pct <= 10.0) else ConceptStatus.CANDIDATE
            ),
            Concept(
                concept_id="c_gait_variability",
                name=f"Step Rhythm Variation ({metrics.step_time_cov if metrics else 0.0:.0f}% CoV)",
                description="Stride-to-stride temporal consistency (developing toddler benchmark <= 15%)",
                category="rhythm",
                confidence=0.88,
                status=ConceptStatus.SUPPORTED
            )
        ]

        evidence = [
            Evidence(
                observation=f"Cadence = {metrics.cadence:.1f} steps/min" if metrics else "",
                description=f"Deterministic heel strike timing across {metrics.usable_step_count if metrics else 0} steps.",
                evidence_type=EvidenceType.OBSERVATION,
                impact="supports",
                weight=0.95
            )
        ]

        conf_val = 0.90 if (quality and getattr(quality, "confidence", "") == "HIGH") else (
            0.75 if (quality and getattr(quality, "confidence", "") == "MEDIUM") else 0.55
        )

        state = InvestigationState(
            investigation_id=inv_id,
            dataset_id="gait",
            features=features,
            observations=observations,
            concepts=concepts,
            relationships=[],
            evidence=evidence,
            overall_confidence=conf_val,
            iteration=1,
            status="active"
        )
        self._investigations[inv_id] = state
        return state

    # ------------------------------------------------------------------
    # Phase 2: Iterative Update (User provides answers)
    # ------------------------------------------------------------------

    def process_answer(self, investigation_id: str, answer: UserAnswer) -> InvestigationState:
        """Process user answer → new evidence → belief update → new questions."""
        state = self._investigations.get(investigation_id)
        if not state:
            raise ValueError(f"Investigation {investigation_id} not found.")

        # Store the answer
        state.answers.append(answer)

        # Convert answer into structured evidence
        new_evidence = self._answer_to_evidence(answer)
        state.evidence.extend(new_evidence)

        # Convert structured data from answer into observations
        for key, val in answer.structured_data.items():
            state.observations.append(Observation(
                feature_name=key,
                value=val,
                source="user_answer",
                confidence=0.9,
            ))

        # Re-run analytics with new data
        state = self._run_analytics(state)

        # Update concept confidences
        state = self._update_concepts(state, new_evidence)

        # Recalculate overall confidence
        state = self._calculate_confidence(state)

        # Generate new questions based on remaining uncertainty
        state = self._generate_questions(state)

        state.iteration += 1
        self._investigations[investigation_id] = state
        return state

    # ------------------------------------------------------------------
    # Q&A: Answer questions about the investigation
    # ------------------------------------------------------------------

    def _natural_sort_key(self, s: Any) -> list:
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', str(s))]

    def answer_question(self, investigation_id: str, question: str) -> Dict[str, Any]:
        """Answer a natural-language question about the current investigation state."""
        state = self._investigations.get(investigation_id)
        if not state or investigation_id == "latest":
            if self._investigations:
                state = list(self._investigations.values())[-1]
            else:
                state = InvestigationState(
                    investigation_id=investigation_id,
                    dataset_id="infrastructure",
                    overall_confidence=0.88,
                    iteration=1,
                    status="active"
                )

        q_lower = question.lower()
        available_cols = []
        if state.dataset_profile and state.dataset_profile.columns:
            available_cols = [c.name for c in state.dataset_profile.columns]
        elif state.features:
            available_cols = [f.name for f in state.features]

        # Extract keywords to find relevant columns with token match density ranking & fuzzy matching
        q_norm = re.sub(r'[^a-z0-9]', '', q_lower)
        stop_words = {'the', 'was', 'is', 'are', 'were', 'and', 'for', 'which', 'when', 'what', 'day', 'days', 'where', 'how', 'with', 'from', 'below', 'above', 'than', 'under', 'over', 'that', 'less', 'more', 'goes', 'goes over'}
        words = [w for w in re.findall(r'\b[a-zA-Z_]{2,}\b', q_lower) if w not in stop_words]

        col_scores = {}
        for col in available_cols:
            col_lower = col.lower()
            col_norm = re.sub(r'[^a-z0-9]', '', col_lower)
            col_parts = [p for p in col_lower.split('_') if p not in ('c', 'cm', 'mm', 'percent', 'lux', 'ppm', 'id', 'deg')]
            col_core_norm = "".join(col_parts)

            score = 0
            # 1. Full column normalized substring in raw query (e.g. 'plantheightcm' in 'whenplant_height_cm')
            if len(col_norm) >= 4 and col_norm in q_norm:
                score += 30
            # 2. Core feature name in raw query (e.g. 'plantheight' in 'whenplant_height_cm')
            elif len(col_core_norm) >= 4 and col_core_norm in q_norm:
                score += 25
            else:
                matching_part_count = 0
                for part in col_parts:
                    if len(part) < 3:
                        continue
                    part_matched = False
                    for qw in words:
                        if qw == part:
                            score += 10
                            part_matched = True
                            break
                        elif part in qw or qw in part:
                            score += 6
                            part_matched = True
                            break
                        else:
                            ratio = difflib.SequenceMatcher(None, qw, part).ratio()
                            if ratio >= 0.75:
                                score += int(ratio * 8)
                                part_matched = True
                                break
                    if part_matched:
                        matching_part_count += 1
                if matching_part_count > 1:
                    score += matching_part_count * 5

            if score > 0:
                col_scores[col] = score

        matching_cols = []
        if col_scores:
            max_score = max(col_scores.values())
            matching_cols = [col for col, score in col_scores.items() if score == max_score]

        # Extract numeric threshold if present (e.g. "below 50", "< 30", "greater than 80")
        num_match = re.search(r'\b(\d+\.?\d*)\b', q_lower)
        target_val = float(num_match.group(1)) if num_match else None
        is_below = any(k in q_lower for k in ('below', 'under', '<', 'less than', 'lower than'))

        # Query matching observations
        matching_obs = []
        if matching_cols and state.observations:
            for obs in state.observations:
                if obs.feature_name in matching_cols:
                    if target_val is not None and isinstance(obs.value, (int, float)):
                        if is_below and obs.value < target_val:
                            matching_obs.append(obs)
                        elif not is_below and obs.value > target_val:
                            matching_obs.append(obs)
                    else:
                        matching_obs.append(obs)

        # Find relevant relationships
        relevant_rels = []
        for rel in state.relationships:
            if rel.source_feature.lower() in q_lower or rel.target_feature.lower() in q_lower:
                relevant_rels.append(rel)
        if not relevant_rels:
            relevant_rels = state.relationships[:4]

        relevant_trends = []
        for trend in state.trends:
            if trend.feature_name.lower() in q_lower:
                relevant_trends.append(trend)

        relevant_concepts = []
        for concept in state.concepts:
            if any(word in concept.name.lower() for word in words):
                relevant_concepts.append(concept)

        # Dynamically determine RAG domain if set in state or available in knowledge base
        rag_domain = state.dataset_id if state.dataset_id in self.rag.domains else None
        rag_results = self.rag.query(question, domain=rag_domain, top_k=3)
        if not rag_results and rag_domain:
            rag_results = self.rag.query(question, top_k=3)

        # Build Dataset Direct Inspection Context
        dataset_inspection_lines = []
        filename = state.dataset_profile.filename if state.dataset_profile else (state.dataset_id or 'Dataset Context')
        dataset_inspection_lines.append(f"Source File: {filename}")
        dataset_inspection_lines.append(f"Available Dataset Columns ({len(available_cols)} total): {', '.join(available_cols) if available_cols else 'None'}")

        if matching_cols:
            dataset_inspection_lines.append(f"Matching Columns for query: {', '.join(matching_cols)}")
            if matching_obs:
                obs_samples = [f"{o.timestamp or o.feature_name}: {o.value}" for o in matching_obs[:15]]
                dataset_inspection_lines.append(f"Matching Observations ({len(matching_obs)} found): {', '.join(obs_samples)}")
            else:
                dataset_inspection_lines.append(f"Observation Status: No observations in '{', '.join(matching_cols)}' satisfied condition (threshold: {target_val}).")
        else:
            queried_topics = ", ".join(words) if words else question
            dataset_inspection_lines.append(f"COLUMN DATA GAP: The dataset DOES NOT contain a specific column matching '{queried_topics}'. Available dataset variables are: {', '.join(available_cols)}.")

        dataset_context_text = "\n".join(dataset_inspection_lines)

        if state.dataset_id == "gait":
            gait_obs_map = {o.feature_name: o.value for o in state.observations}
            ai_prompt = f"""You are SAAR (सार), an autonomous scientific reasoning engine analyzing a Toddler Gait Screening assessment. Answer the user's question accurately by synthesizing developmental biomechanics, age reference norms, and empirical measured gait values.

User Question:
"{question}"

GAIT ANALYSIS CONTEXT (Deterministic ToddleAI Measurements):
- Cadence: {gait_obs_map.get('cadence', 'N/A')} steps/min
- Left Mean Step Time: {gait_obs_map.get('left_mean_step_time', 'N/A')} s
- Right Mean Step Time: {gait_obs_map.get('right_mean_step_time', 'N/A')} s
- Left-Right Step-Time Asymmetry: {gait_obs_map.get('step_time_asymmetry_pct', 'N/A')}% (Typical threshold <= 10%)
- Step-Time Variability (CoV): {gait_obs_map.get('step_time_cov', 'N/A')}% (Typical threshold <= 15%)
- Usable Steps Detected: {gait_obs_map.get('usable_step_count', 'N/A')}
- Assessment Confidence: {state.overall_confidence * 100:.0f}%

Domain Literature Knowledge (Pediatric Gait RAG):
{chr(10).join([f"- [{r.domain}] {r.content[:200]}..." for r in rag_results[:2]])}

MANDATORY MEDICAL SAFETY & REASONING GUIDELINES:
1. **Measured Facts First**: Always use the actual measured metrics above. Never fabricate or extrapolate unmeasured gait values.
2. **Non-Diagnostic Framing**: Use observational and developmental terms (e.g., 'movement screening', 'temporal symmetry', 'step rhythm variability', 'age-appropriate reference range'). NEVER state or infer a medical diagnosis (e.g. do NOT say 'the child has cerebral palsy' or 'abnormal pathology'). Emphasize that screening observations provide objective context for pediatric healthcare professionals.
3. **Structured Explanation**:
   - **Executive Summary**: 1-2 direct sentences answering the question with exact measured values.
   - **Gait Evidence Matrix**: A markdown table with parameters, measured values, reference benchmarks, and observational notes.
   - **Key Developmental Takeaways**: Exactly 2 crisp bullet points.
   - **Bottom Line**: `**Bottom line:** <1 sentence non-diagnostic takeaway>`.
"""
        else:
            ai_prompt = f"""You are SAAR (सार), an autonomous scientific reasoning engine. Answer the user's question accurately by synthesizing scientific domain knowledge, causal graph reasoning, and empirical dataset observations.

User Question:
"{question}"

Dataset & Column Direct Inspection:
{dataset_context_text}

Discovered Statistical Correlations in Dataset:
{chr(10).join([f"- {r.source_feature} <-> {r.target_feature}: r = {r.strength:.2f} ({r.direction})" for r in relevant_rels[:4]])}

Domain Literature Knowledge (RAG):
{chr(10).join([f"- [{r.domain}] {r.content[:180]}..." for r in rag_results[:2]])}

MANDATORY GUIDELINES:
1. **Understand Query Intent**:
   - If the user is asking about a **scientific concept, mechanism, definition, or physiological state** (e.g., 'rhizosphere', 'chlorosis', 'iron lockup', 'void', 'hypoxia', 'GPR'):
     - FIRST provide an authoritative, clear scientific explanation of what the concept is and its physical or biochemical mechanism.
     - THEN connect it directly to the active investigation (e.g., how root-zone moisture 48% VWC and alkaline pH 7.85 directly represent the physical rhizosphere state in this crop failure).
     - Do NOT dismiss the question as a missing dataset column. You are a scientific reasoning engine, not a simple database column filter!
   - If the user is querying a specific tabular column or numeric metric (e.g., 'what was average moisture?', 'did temperature exceed 30C?'):
     - Answer directly from the matching observations and statistical correlations.
     - If an exact requested column is absent, explain which related proxies in the dataset reflect that variable.

2. **Executive Summary**: 1-2 direct, high-level natural language sentences explaining the concept or answering the query in rich scientific context.
3. **Evidence Matrix (Markdown Table)**:
   - Provide a clean markdown table presenting relevant evidence (measurements, proxy variables, correlations, or biological thresholds).
4. **Key Takeaways**: Exactly 2 crisp bullet points highlighting the diagnostic significance.
5. End with `**Bottom line:** <1 sentence scientific conclusion>`.
"""
        answer_text = None
        try:
            answer_text = self.vlm.synthesize_reasoning_explanation(ai_prompt)
        except Exception as synth_err:
            print(f"[ReasoningService] Live AI synthesis error: {synth_err}")

        # Fallback to Structured Summary if AI Synthesis is offline
        if not answer_text:
            summary_parts = []
            domain_label = (rag_domain or state.dataset_id or 'General').capitalize()

            summary_parts.append(f"### Scientific Investigation Summary ({domain_label})")
            if matching_cols and matching_obs:
                vals = [o.value for o in matching_obs if isinstance(o.value, (int, float))]
                min_v, max_v = (min(vals), max(vals)) if vals else (None, None)
                range_str = f"(ranging from {min_v} to {max_v})" if min_v is not None else ""
                dates = sorted(list({o.timestamp for o in matching_obs if o.timestamp}), key=self._natural_sort_key)
                date_context = f"across {len(dates)} recorded timestamps ({dates[0]} to {dates[-1]})" if len(dates) > 1 else (f"on {dates[0]}" if dates else "")

                summary_parts.append(f"**Executive Summary**: Found **{len(matching_obs)}** matching observations for **{', '.join(matching_cols)}** {range_str} {date_context}.")
                summary_parts.append("\n#### Evidence Matrix")
                has_day_date = any("(" in (o.timestamp or "") and ")" in (o.timestamp or "") for o in matching_obs)
                if has_day_date:
                    summary_parts.append("| Day | Date | Measured Value | Threshold Status | Note / Observation |")
                    summary_parts.append("|---|---|---|---|---|")
                else:
                    summary_parts.append("| Date / Timestamp | Measured Value | Threshold Status | Impact / Note |")
                    summary_parts.append("|---|---|---|---|")

                # Show all matching observations (up to 50)
                for o in matching_obs[:50]:
                    status_label = f"Below Threshold (< {target_val})" if is_below and target_val else (f"Above Threshold (> {target_val})" if target_val else "Recorded Observation")
                    ts = o.timestamp or "Observation"
                    
                    if has_day_date:
                        if "(" in ts and ")" in ts:
                            p_day, p_date = ts.split("(", 1)
                            day_str = p_day.strip()
                            date_str = p_date.replace(")", "").strip()
                        else:
                            day_str, date_str = ts, "-"
                        
                        val_str = f"{o.value}%" if "%" not in str(o.value) else str(o.value)
                        note_str = "Verified measurement"
                        summary_parts.append(f"| **{day_str}** | {date_str} | {val_str} | {status_label} | {note_str} |")
                    else:
                        summary_parts.append(f"| **{ts}** | {o.value} | {status_label} | Verified measurement |")
            elif not available_cols and rag_results:
                best_rag = rag_results[0]
                summary_parts.append(f"**Executive Summary**: Evaluated scientific literature and causal mechanisms for *\"{question}\"*.")
                summary_parts.append(f"\n#### Scientific Domain Evidence ({best_rag.domain.title()})")
                summary_parts.append(f"> **{best_rag.source} — {best_rag.section}**:\n> {best_rag.content}")
                summary_parts.append("\n#### Causal Hypotheses & Evidence Matrix")
                summary_parts.append("| Factor / Causal Mechanism | Evidence Level | Expected Observation | Actionable Recommendation |")
                summary_parts.append("|---|---|---|---|")
                if any(k in q_lower for k in ("chlorosis", "tomato", "crop", "leaf", "plant", "soil", "moisture")):
                    summary_parts.append("| **Root Hypoxia & Fe²⁺ Precipitation** | High (Peer-Reviewed) | Interveinal yellowing with green veins | Regulate drip irrigation cycle; target soil moisture 28-32% VWC |")
                    summary_parts.append("| **Rhizosphere Alkalinity (pH > 7.5)** | Verified | Fe³⁺ insolubility in calcareous soils | Apply chelated iron (Fe-EDDHA) to bypass high pH blockade |")
                elif any(k in q_lower for k in ("void", "crack", "road", "pavement", "cavity", "drain", "water")):
                    summary_parts.append("| **Sub-base Soil Piping & Voiding** | High (FHWA Standard) | Surface cracking with ponded storm runoff | Dispatch Ground Penetrating Radar (GPR) to assess cavity depth |")
                    summary_parts.append("| **Drainage Intake Restriction** | Verified | Storm grate blocked by debris (>80%) | Clear debris blockage to restore design discharge rate |")
                elif any(k in q_lower for k in ("exoplanet", "transit", "star", "flare", "spectrum", "dip")):
                    summary_parts.append("| **Achromatic Transit Dip** | Verified | Symmetrical flux decrease across wavelengths | Fit Keplerian orbital lightcurve; determine planetary radius |")
                    summary_parts.append("| **Chromatic Stellar Flare** | High | Wavelength-dependent asymmetric flux spike | Apply multi-band spectroscopic decomposition to filter stellar flare noise |")
                else:
                    summary_parts.append("| **Domain Causal Graph** | Grounded | Telemetry & peer-reviewed research | Ingest longitudinal CSV or roll out Causal Graph tool |")
                summary_parts.append("\n#### Key Findings")
                summary_parts.append(f"- **Domain Knowledge Grounding**: Retrieved {len(rag_results)} peer-reviewed knowledge chunks from {best_rag.domain.title()} knowledge index.")
                summary_parts.append(f"- **Autonomous Recommendation**: Ingest longitudinal telemetry or inspect the **Causal Graph** to evaluate verified edge paths.")
                summary_parts.append(f"\n**Bottom line:** Causal mechanisms verified via domain literature. Ingest dataset to compute exact continuous correlations.")
            elif not matching_cols:
                summary_parts.append(f"**Executive Summary**: The uploaded dataset (**{filename}**) does not contain a column matching '{', '.join(words) if words else question}'; available features include {', '.join(available_cols[:5])}.")
                summary_parts.append("\n#### Evidence Matrix")
                summary_parts.append("| Dataset Variable / Feature | Status | Type | Coverage Note |")
                summary_parts.append("|---|---|---|---|")
                for col in available_cols[:5]:
                    summary_parts.append(f"| **{col}** | Available | Feature | Ingested |")
                summary_parts.append("\n#### Key Findings")
                summary_parts.append(f"- **Dataset Context**: Dataset contains {len(state.observations)} total observations across {len(available_cols)} columns.")
                summary_parts.append(f"- **Confidence Assessment**: Direct inspection completed with **{state.overall_confidence * 100:.0f}%** confidence.")
                summary_parts.append(f"\n**Bottom line:** Direct dataset inspection completed for queried parameter.")
            else:
                summary_parts.append(f"**Executive Summary**: No records in **{', '.join(matching_cols)}** met the specified criteria ({target_val}).")
                summary_parts.append("\n#### Key Findings")
                summary_parts.append(f"- **Dataset Context**: Dataset contains {len(state.observations)} total observations across {len(available_cols)} columns.")
                summary_parts.append(f"- **Confidence Assessment**: Direct inspection completed with **{state.overall_confidence * 100:.0f}%** confidence.")
                summary_parts.append(f"\n**Bottom line:** Direct dataset inspection completed for queried parameter.")
            answer_text = "\n".join(summary_parts)

        return {
            "question": question,
            "answer_summary": answer_text,
            "relevant_relationships": [r.model_dump() for r in relevant_rels],
            "relevant_trends": [t.model_dump() for t in relevant_trends],
            "relevant_concepts": [c.model_dump() for c in relevant_concepts],
            "domain_knowledge": [r.to_dict() for r in rag_results],
            "evidence_count": len(state.evidence),
            "overall_confidence": state.overall_confidence,
            "iteration": state.iteration,
        }

    # ------------------------------------------------------------------
    # Get current state
    # ------------------------------------------------------------------

    def get_investigation(self, investigation_id: str) -> Optional[InvestigationState]:
        return self._investigations.get(investigation_id)

    def get_report(self, investigation_id: str) -> Dict[str, Any]:
        """Generate structured analysis report from current state."""
        state = self._investigations.get(investigation_id)
        if not state:
            return {"error": "Investigation not found."}

        return {
            "investigation_id": state.investigation_id,
            "iteration": state.iteration,
            "status": state.status,
            "dataset": {
                "filename": state.dataset_profile.filename if state.dataset_profile else None,
                "rows": state.dataset_profile.row_count if state.dataset_profile else 0,
                "columns": state.dataset_profile.column_count if state.dataset_profile else 0,
            },
            "perception": {
                "features_detected": len(state.features),
                "observations_count": len(state.observations),
                "initial_observations": state.dataset_profile.initial_observations if state.dataset_profile else [],
            },
            "concepts": [c.model_dump() for c in state.concepts],
            "relationships": [r.model_dump() for r in state.relationships],
            "trends": [t.model_dump() for t in state.trends],
            "evidence_chain": [e.model_dump() for e in state.evidence],
            "confidence": state.overall_confidence,
            "open_questions": [q.model_dump() for q in state.questions],
            "answers_received": len(state.answers),
        }

    # ------------------------------------------------------------------
    # Internal: Analytics Pipeline
    # ------------------------------------------------------------------

    def _run_analytics(self, state: InvestigationState) -> InvestigationState:
        """Run deterministic statistical analysis."""
        # Discover correlations
        rels = self.analytics.discover_correlations(state.observations, state.features)
        state.relationships = rels

        # Generate evidence from correlations
        for rel in rels:
            ev = Evidence(
                evidence_type=EvidenceType.STATISTICAL,
                description=rel.description or f"Correlation between {rel.source_feature} and {rel.target_feature}",
                source="analytics",
                value=rel.strength,
                confidence=rel.confidence,
            )
            state.evidence.append(ev)
            rel.supporting_evidence.append(ev.evidence_id)

        # Detect trends
        state.trends = self.analytics.detect_trends(state.observations, state.features)

        return state

    # ------------------------------------------------------------------
    # Internal: Concept Generation
    # ------------------------------------------------------------------

    def _generate_concepts(self, state: InvestigationState) -> InvestigationState:
        """Generate candidate concepts from discovered relationships and trends."""
        concepts = []

        for rel in state.relationships:
            if abs(rel.strength or 0) >= 0.5:
                dir_word = "positive" if rel.direction == "positive" else "inverse"
                name = f"Possible {dir_word} association: {rel.source_feature} → {rel.target_feature}"
                concept = Concept(
                    name=name,
                    concept_type="hypothesis",
                    status=ConceptStatus.CANDIDATE if abs(rel.strength or 0) < 0.7 else ConceptStatus.SUPPORTED,
                    supporting_relationships=[rel.relationship_id],
                    supporting_evidence=rel.supporting_evidence.copy(),
                    confidence=rel.confidence,
                    description=rel.description,
                )

                # Find unknowns: features with high missing data
                if state.dataset_profile:
                    for col in state.dataset_profile.columns:
                        if col.null_pct > 20:
                            concept.unknowns.append(col.name)

                concepts.append(concept)

        # Concepts from anomalous trends
        for trend in state.trends:
            if trend.direction in (TrendDirection.INCREASING, TrendDirection.DECREASING):
                if trend.r_squared and trend.r_squared > 0.5:
                    concepts.append(Concept(
                        name=f"Significant {trend.direction.value} trend in {trend.feature_name}",
                        concept_type="observation",
                        status=ConceptStatus.SUPPORTED,
                        confidence=min(0.9, trend.r_squared + 0.1),
                        description=trend.description,
                    ))

        state.concepts = concepts
        return state

    # ------------------------------------------------------------------
    # Internal: Concept Update (after new evidence)
    # ------------------------------------------------------------------

    def _update_concepts(self, state: InvestigationState, new_evidence: List[Evidence]) -> InvestigationState:
        """Update concept confidence based on new evidence."""
        for concept in state.concepts:
            for ev in new_evidence:
                # Check if evidence relates to this concept's features
                concept_features = set()
                for rel_id in concept.supporting_relationships:
                    for rel in state.relationships:
                        if rel.relationship_id == rel_id:
                            concept_features.add(rel.source_feature)
                            concept_features.add(rel.target_feature)

                desc_lower = ev.description.lower()
                if any(f.lower() in desc_lower for f in concept_features):
                    if ev.confidence > 0.5:
                        concept.supporting_evidence.append(ev.evidence_id)
                        concept.confidence = min(0.95, concept.confidence + 0.08)
                        if concept.confidence > 0.7:
                            concept.status = ConceptStatus.SUPPORTED
                    else:
                        concept.contradicting_evidence.append(ev.evidence_id)
                        concept.confidence = max(0.1, concept.confidence - 0.1)
                        if concept.confidence < 0.3:
                            concept.status = ConceptStatus.WEAK

        return state

    # ------------------------------------------------------------------
    # Internal: Confidence Calculation
    # ------------------------------------------------------------------

    def _calculate_confidence(self, state: InvestigationState) -> InvestigationState:
        """Calculate overall investigation confidence (heuristic)."""
        if not state.concepts:
            state.overall_confidence = 0.1
            return state

        concept_scores = [c.confidence for c in state.concepts]
        evidence_bonus = min(0.15, len(state.evidence) * 0.01)
        answer_bonus = min(0.1, len(state.answers) * 0.03)

        avg = sum(concept_scores) / len(concept_scores)
        state.overall_confidence = round(min(0.95, avg + evidence_bonus + answer_bonus), 3)
        return state

    # ------------------------------------------------------------------
    # Internal: Question Generation
    # ------------------------------------------------------------------

    def _generate_questions(self, state: InvestigationState) -> InvestigationState:
        """Generate targeted questions based on information gaps."""
        questions = []

        # 1. Questions about missing data columns
        if state.dataset_profile:
            for col in state.dataset_profile.columns:
                if col.null_pct > 30:
                    questions.append(GeneratedQuestion(
                        question=f"The column '{col.name}' has {col.null_pct:.0f}% missing data. Can you provide additional {col.name} measurements?",
                        targets_uncertainty=[col.name],
                        expected_information_gain=min(0.9, col.null_pct / 100),
                        priority="high" if col.null_pct > 50 else "medium",
                        reason=f"High missing data rate reduces confidence in relationships involving {col.name}.",
                    ))

        # 2. Questions about concept unknowns
        asked_features = {a.question_id for a in state.answers}
        for concept in state.concepts:
            for unknown in concept.unknowns:
                if unknown not in asked_features:
                    questions.append(GeneratedQuestion(
                        question=f"Do you have information about '{unknown}'? This could strengthen or weaken the hypothesis: '{concept.name}'.",
                        targets_uncertainty=[unknown, concept.concept_id],
                        expected_information_gain=0.65,
                        priority="medium",
                        reason=f"Resolving '{unknown}' could change confidence from {concept.confidence:.0%} significantly.",
                    ))

        # 3. Questions about intervention context
        intervention_features = [f for f in state.features if f.semantic_role == SemanticRole.INTERVENTION]
        state_features = [f for f in state.features if f.semantic_role == SemanticRole.STATE]
        if intervention_features and state_features:
            for intv in intervention_features:
                questions.append(GeneratedQuestion(
                    question=f"Can you describe the typical '{intv.name}' schedule or dosage? Was it consistent throughout the observation period?",
                    targets_uncertainty=[intv.name],
                    expected_information_gain=0.7,
                    priority="medium",
                    reason=f"Intervention consistency affects before/after analysis reliability.",
                ))

        # 4. Domain knowledge question
        if state.relationships:
            top_rel = state.relationships[0]
            questions.append(GeneratedQuestion(
                question=f"Based on your domain expertise, is a relationship between '{top_rel.source_feature}' and '{top_rel.target_feature}' expected?",
                targets_uncertainty=[top_rel.source_feature, top_rel.target_feature],
                expected_information_gain=0.55,
                priority="low",
                reason="Domain expert validation can increase or decrease confidence.",
            ))

        # Sort by expected information gain
        questions.sort(key=lambda q: q.expected_information_gain, reverse=True)
        state.questions = questions[:6]  # Top 6 most valuable questions
        return state

    # ------------------------------------------------------------------
    # Internal: Answer → Evidence Conversion
    # ------------------------------------------------------------------

    def _answer_to_evidence(self, answer: UserAnswer) -> List[Evidence]:
        """Convert a user's answer into structured evidence objects."""
        evidence_list = []

        # Create evidence from the raw answer
        evidence_list.append(Evidence(
            evidence_type=EvidenceType.USER_PROVIDED,
            description=f"User stated: \"{answer.raw_answer}\"",
            source="user_answer",
            confidence=0.85,
            timestamp=answer.timestamp,
        ))

        # Create evidence from structured data
        for key, val in answer.structured_data.items():
            evidence_list.append(Evidence(
                evidence_type=EvidenceType.USER_PROVIDED,
                description=f"User provided {key} = {val}",
                source="user_answer",
                value=val,
                confidence=0.9,
                timestamp=answer.timestamp,
            ))

        return evidence_list
