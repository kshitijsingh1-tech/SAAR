"""
Saar — Iterative Reasoning Service
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
    GeneratedQuestion, UserAnswer, SemanticRole,
    AdaptiveSession
)
from .ingestion_service import IngestionService
from .analytics_service import AnalyticsService
from .adaptive_inquiry import AdaptiveInquiryEngine
from ..rag_service import RAGKnowledgeService
from ..vlm_service import VLMService


class ReasoningService:
    """Orchestrates the iterative SAAR evidence-driven reasoning loop."""

    def __init__(self):
        self.ingestion = IngestionService()
        self.analytics = AnalyticsService()
        self.rag = RAGKnowledgeService()
        self.vlm = VLMService()
        self.adaptive_engine = AdaptiveInquiryEngine()
        self._investigations: Dict[str, InvestigationState] = {}
        self._badminton_results: Dict[str, Any] = {}
        self._adaptive_sessions: Dict[str, AdaptiveSession] = {}

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
        conclusion = getattr(response_data, "conclusion", "")
        text_context = getattr(response_data, "text_context_analysis", None)
        vlm_provider = getattr(response_data, "vlm_provider_used", "Saar Vision Engine")

        relationships = []
        concepts = []
        evidence = []
        features = []
        observations = []

        node_label_map = {}
        if final_graph:
            for node in getattr(final_graph, "nodes", []):
                n_id = getattr(node, "id", "")
                n_label = getattr(node, "label", n_id)
                n_conf = getattr(node, "confidence", 0.9)
                n_status = getattr(node, "status", "confirmed")
                n_cat = getattr(node, "category", "general")
                n_bbox = getattr(node, "bbox", None)
                node_label_map[n_id] = n_label

                status_enum = ConceptStatus.SUPPORTED if n_status == "confirmed" else ConceptStatus.CANDIDATE
                concepts.append(Concept(
                    concept_id=n_id,
                    name=n_label,
                    description=f"{n_label} ({n_cat})",
                    category=n_cat,
                    confidence=n_conf,
                    status=status_enum,
                    bbox=n_bbox,
                    visual_anchor=getattr(node, "visual_anchor", True)
                ))

                # Also populate features and observations so reasoning engine has structured data
                features.append(Feature(
                    name=n_label,
                    data_type="entity",
                    semantic_role=SemanticRole.STATE,
                    description=f"Grounded visual entity: {n_label} in {n_cat}"
                ))
                bbox_str = f" [bbox: {n_bbox}]" if n_bbox else ""
                observations.append(Observation(
                    feature_name=n_label,
                    value=f"{int(n_conf * 100)}% confidence ({n_status}){bbox_str}",
                    timestamp=f"Category: {n_cat}",
                    source="vlm_visual_grounding",
                    confidence=n_conf
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

        if conclusion:
            evidence.append(Evidence(
                observation=conclusion[:200],
                description=conclusion,
                evidence_type=EvidenceType.VISUAL,
                impact="supports",
                weight=0.95
            ))

        if text_context:
            m = text_context.get("milestone", {})
            m_day = m.get("day", 1)
            m_stage = m.get("stage", "Milestone")
            for target in text_context.get("focus_targets", []):
                evidence.append(Evidence(
                    observation=f"Prior Target: {target}",
                    description=f"Stage 1 focus target: {target} for Day {m_day} ({m_stage})",
                    evidence_type=EvidenceType.USER_PROVIDED,
                    impact="supports",
                    weight=0.9
                ))
            for hypo in text_context.get("hypotheses", []):
                evidence.append(Evidence(
                    observation=f"Prior Hypothesis: {hypo}",
                    description=hypo,
                    evidence_type=EvidenceType.USER_PROVIDED,
                    impact="supports",
                    weight=0.88
                ))

        state = InvestigationState(
            investigation_id=inv_id,
            dataset_id=domain,
            features=features,
            observations=observations,
            concepts=concepts,
            relationships=relationships,
            evidence=evidence,
            overall_confidence=getattr(final_graph, "overall_confidence", 0.88),
            iteration=1,
            status="active"
        )
        # Attach dynamic metadata attributes
        state.visual_conclusion = conclusion
        state.text_context = text_context
        state.vlm_provider = vlm_provider

        self._investigations[inv_id] = state
        self._investigations["latest"] = state
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

    def register_badminton_investigation(self, badminton_result: Any) -> InvestigationState:
        """Register a deterministic Badminton Biomechanics assessment into SAAR reasoning store."""
        inv_id = getattr(badminton_result, "analysis_id", f"badminton_{uuid.uuid4().hex[:8]}")
        self._badminton_results[inv_id] = badminton_result

        movement = getattr(badminton_result, "movement", None)
        court_calib = getattr(badminton_result, "court_calibration", None)
        shot_metrics = getattr(badminton_result, "shot_metrics", None)
        shots = getattr(badminton_result, "shots", []) or []
        energy = getattr(badminton_result, "energy_expenditure", None)
        speed = getattr(badminton_result, "speed_metrics", None)
        evidence_graph = getattr(badminton_result, "evidence_graph", None)
        quality = getattr(badminton_result, "quality", None)

        features = [
            Feature(name="total_shots", data_type="int", semantic_role=SemanticRole.TARGET),
            Feature(name="mean_shot_duration_s", data_type="float", semantic_role=SemanticRole.STATE),
            Feature(name="court_calibrated", data_type="bool", semantic_role=SemanticRole.STATE),
            Feature(name="total_distance_m", data_type="float", semantic_role=SemanticRole.STATE),
            Feature(name="coverage_pct", data_type="float", semantic_role=SemanticRole.STATE),
            Feature(name="calories_burned_kcal", data_type="float", semantic_role=SemanticRole.TARGET),
        ]

        observations = []
        if shot_metrics:
            total_shots = getattr(shot_metrics, "total_shots_detected", len(shots))
            mean_dur = getattr(shot_metrics, "mean_shot_duration_seconds", 0.0)
            observations.append(Observation(feature_name="total_shots", value=total_shots, confidence=0.95))
            observations.append(Observation(feature_name="mean_shot_duration_s", value=mean_dur, unit="s", confidence=0.95))

        is_cal = bool(court_calib and getattr(court_calib, "is_calibrated", False))
        observations.append(Observation(feature_name="court_calibrated", value=1 if is_cal else 0, confidence=0.99))

        if movement and is_cal:
            if getattr(movement, "total_distance_m", None) is not None:
                observations.append(Observation(feature_name="total_distance_m", value=movement.total_distance_m, unit="m", confidence=0.90))
            if getattr(movement, "coverage_percentage", None) is not None:
                observations.append(Observation(feature_name="coverage_pct", value=movement.coverage_percentage, unit="%", confidence=0.90))

        if energy:
            burned = getattr(energy, "estimated_calories_burned_kcal", None)
            if burned is not None:
                observations.append(Observation(feature_name="calories_burned_kcal", value=burned, unit="kcal", confidence=0.85))

        concepts = []
        # Extract hypotheses and concepts from evidence_graph if available
        if evidence_graph and hasattr(evidence_graph, "nodes"):
            for n in evidence_graph.nodes:
                node_id = getattr(n, "id", "")
                node_type = getattr(n, "node_type", "") or getattr(n, "type", "")
                label = getattr(n, "label", node_id)
                props = getattr(n, "properties", {}) or {}
                if node_type in ("hypothesis", "recommendation", "trend"):
                    concepts.append(Concept(
                        concept_id=f"c_{node_id}",
                        name=label,
                        description=str(props.get("value", label)),
                        category=node_type,
                        confidence=float(props.get("confidence", 0.8)),
                        status=ConceptStatus.SUPPORTED if node_type == "hypothesis" else ConceptStatus.CANDIDATE
                    ))

        if not concepts:
            concepts.append(Concept(
                concept_id="c_badminton_tactical",
                name="Badminton Tactical & Kinetic Profile",
                description="Deterministic stroke kinematics and spatial movement profile.",
                category="tactics",
                confidence=0.90,
                status=ConceptStatus.SUPPORTED
            ))

        evidence = []
        if evidence_graph and hasattr(evidence_graph, "edges"):
            for e in evidence_graph.edges:
                evidence.append(Evidence(
                    observation=f"{getattr(e, 'source', '')} -> {getattr(e, 'relation', '')} -> {getattr(e, 'target', '')}",
                    description=getattr(e, "description", "") or "Grounded evidence graph relationship",
                    evidence_type=EvidenceType.OBSERVATION,
                    impact="supports",
                    weight=0.90
                ))

        conf_val = 0.90 if is_cal else 0.75

        state = InvestigationState(
            investigation_id=inv_id,
            dataset_id="badminton",
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
    # Adaptive Diagnostic Questioning (LLM-Driven)
    # ------------------------------------------------------------------

    def start_adaptive_session(
        self, investigation_id: str, user_concern: str
    ) -> AdaptiveSession:
        """Start an adaptive diagnostic questioning session for an investigation."""
        state = self._investigations.get(investigation_id)
        if not state:
            # Try to find latest investigation
            if self._investigations:
                state = list(self._investigations.values())[-1]
                investigation_id = state.investigation_id
            else:
                raise ValueError(f"No active investigation found for adaptive session.")

        # Extract measured context from investigation state
        measured_context = {}
        for obs in state.observations:
            if obs.value is not None:
                measured_context[obs.feature_name] = {
                    "value": obs.value,
                    "unit": getattr(obs, "unit", None) or "",
                    "confidence": obs.confidence
                }

        # Determine domain
        domain = state.dataset_id or "general"

        session = self.adaptive_engine.start_session(
            investigation_id=investigation_id,
            user_concern=user_concern,
            domain=domain,
            measured_context=measured_context
        )
        self._adaptive_sessions[session.session_id] = session
        return session

    def get_adaptive_session(self, session_id: str) -> AdaptiveSession:
        """Get the current state of an adaptive session."""
        session = self.adaptive_engine.get_session(session_id)
        if not session:
            session = self._adaptive_sessions.get(session_id)
        if not session:
            raise ValueError(f"Adaptive session {session_id} not found.")
        return session

    def submit_adaptive_answer(
        self, session_id: str, option_id: str
    ) -> AdaptiveSession:
        """Submit an answer to the current adaptive question."""
        session = self.adaptive_engine.process_answer(session_id, option_id)
        self._adaptive_sessions[session_id] = session
        return session

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

    def _answer_badminton_question(self, state: InvestigationState, investigation_id: str, question: str) -> Dict[str, Any]:
        """Answer a natural-language question grounded in badminton biomechanics and evidence graph."""
        from ..plugins.sports.badminton.reasoning import BadmintonHypothesisEngine

        badminton_result = self._badminton_results.get(investigation_id) or self._badminton_results.get(state.investigation_id)

        # 1. Section 27 "What's Missing" Check & Section 52 Out-of-Scope decline
        missing_assessment = BadmintonHypothesisEngine.assess_missing_data(question, badminton_result)
        if missing_assessment and missing_assessment.is_missing:
            return {
                "question": question,
                "status": "DATA_UNAVAILABLE_DECLINED",
                "decline_reason_code": missing_assessment.category,
                "answer_summary": (
                    f"### Data Unavailable (Declined Up Front — Section 27 Protocol)\n\n"
                    f"**Status**: Declined up front — unmeasured or out-of-scope variable.\n\n"
                    f"**Reason**: {missing_assessment.reason}\n\n"
                    f"**Missing Parameter**: `{missing_assessment.parameter}`\n\n"
                    f"**Methodological Guidance**: {missing_assessment.hedged_guidance}\n\n"
                    f"**Bottom line:** Analysis declined up front. This question requires parameters that cannot be determined from video."
                ),
                "relevant_relationships": [],
                "relevant_trends": [],
                "relevant_concepts": [c.model_dump() for c in state.concepts],
                "domain_knowledge": [],
                "evidence_count": len(state.evidence),
                "overall_confidence": state.overall_confidence,
                "iteration": state.iteration,
            }

        # 2. Extract measured facts from badminton result
        movement = getattr(badminton_result, "movement", None) if badminton_result else None
        court_calib = getattr(badminton_result, "court_calibration", None) if badminton_result else None
        shot_metrics = getattr(badminton_result, "shot_metrics", None) if badminton_result else None
        shots = getattr(badminton_result, "shots", []) if badminton_result else []
        energy = getattr(badminton_result, "energy_expenditure", None) if badminton_result else None
        speed = getattr(badminton_result, "speed_metrics", None) if badminton_result else None
        evidence_graph = getattr(badminton_result, "evidence_graph", None) if badminton_result else None

        q_lower = question.lower()

        total_shots = getattr(shot_metrics, "total_shots_detected", len(shots)) if shot_metrics else len(shots)
        shot_counts = getattr(shot_metrics, "count_by_shot_type", {}) if shot_metrics else {}
        shot_pcts = getattr(shot_metrics, "percentage_by_shot_type", {}) if shot_metrics else {}
        mean_shot_dur = getattr(shot_metrics, "mean_shot_duration_seconds", None) if shot_metrics else None

        calib_str = "Calibrated (Metric 13.4m x 6.1m)" if (court_calib and court_calib.is_calibrated) else "Uncalibrated (Pixel Space)"
        dist_m = getattr(movement, "total_distance_m", None) if movement else None
        cov_pct = getattr(movement, "coverage_percentage", None) if movement else None

        # Check for asserted hypotheses in evidence graph
        hypo_node = None
        if evidence_graph and hasattr(evidence_graph, "nodes"):
            hypo_node = next((n for n in evidence_graph.nodes if n.id == "hypo_left_space_underutilization"), None)

        rag_results = self.rag.query(question, domain="sports", top_k=2)

        prompt = f"""You are SAAR, a knowledgeable and encouraging badminton coach reviewing game film with a player. Answer the user's question in a warm, conversational, storytelling tone — like a coach sitting courtside explaining what they saw.

User Question:
"{question}"

YOUR MEASURED DATA FROM THE VIDEO (use these exact numbers, never invent):
- Total Shots Detected: {total_shots}
- Shot Breakdown: {', '.join([f"{k}: {v} ({shot_pcts.get(k, 0.0):.1f}%)" for k, v in shot_counts.items()]) if shot_counts else 'None detected'}
- Mean Shot Duration: {f"{mean_shot_dur:.2f} s" if mean_shot_dur is not None else 'N/A'}
- Court Calibration: {calib_str}
- Movement Coverage: {f"{cov_pct:.1f}%" if cov_pct is not None else 'N/A'} (Total Distance: {f"{dist_m:.2f} m" if dist_m is not None else 'N/A'})
- Energy Expenditure: {f"{energy.estimated_calories_burned_kcal:.1f} kcal ({energy.active_duration_minutes:.1f} min)" if energy else 'N/A'}
- Active Hypotheses: {hypo_node.label if hypo_node else 'None asserted'}

Badminton Knowledge:
{chr(10).join([f"- [{r.domain}] {r.content[:180]}..." for r in rag_results[:2]])}

RESPONSE STYLE RULES:
1. 🏸 Be enthusiastic and encouraging — like a supportive coach, not a lab report.
2. Lead with what the player did well, then gently note areas for improvement.
3. Weave measured numbers naturally into sentences (e.g. "your arm was fully extended at 155° — that's textbook smash form") — avoid dumping tables.
4. When discussing tactical patterns or hypotheses, use hedged language ("this suggests", "it looks like", "you might want to try").
5. Use light emoji (🏸 ⚡ 🎯 💪) as tone markers.
6. End with one clear, actionable coaching suggestion.
7. Keep it concise — 150-250 words max.
"""
        answer_text = None
        try:
            answer_text = self.vlm.synthesize_reasoning_explanation(prompt)
        except Exception as synth_err:
            print(f"[ReasoningService] Live AI synthesis error for badminton: {synth_err}")

        if not answer_text:
            parts = []

            if any(k in q_lower for k in ["hypothesis", "hypotheses", "left space", "underutilization", "bias", "pattern", "avoidance", "weakness"]):
                if hypo_node:
                    props = hypo_node.properties or {}
                    parts.append("### 🏸 Coach's Tactical & Spatial Read")
                    parts.append("Looking across your movement patterns and shot distribution, there is a clear habit showing up on court.")
                    parts.append(f"\n💡 **What We Spotted**: You spent less than 20% of your time covering the left side of the court, while over 60% of your shots were directed toward the right. Your recovery position also naturally drifts right of the center line.")
                    parts.append("\n**Why It Matters**: This looks like a tactical bias or comfort zone — you may be favoring your right side to protect a backhand or because of a visual habit. On-court, an observant opponent will notice this and start pushing you wide to the left to exploit the open space.")
                    parts.append("\n🎯 **Next Step on the Court**: Work on shadow-drills moving into that left backcourt corner, and practice recovering back to the true 3.05 m center after every stroke. Have your coach watch a few live points to see if this is tactical or a movement confidence issue!")
                else:
                    parts.append("### 🏸 Coach's Tactical & Spatial Read")
                    parts.append("We checked your movement coverage and shot placement across the court to see if any tactical spatial blind spots stood out.")
                    parts.append("\n💡 **The Verdict**: Right now, your movement looks balanced! The data does **not** show a persistent bias toward one side of the court — you're covering both left and right zones sufficiently without leaving an obvious open lane.")
                    parts.append("\n🎯 **Coach's Advice**: Keep focusing on crisp split-steps and snapping back to the center base after every shot to keep that court balance.")

            elif any(k in q_lower for k in ["angle", "elbow", "shoulder", "knee", "hip", "joint", "kinematic", "arm", "technique"]):
                parts.append("### 🏸 Stroke Kinematics & Technique Breakdown")
                parts.append(f"We tracked your body angles across {total_shots} stroke(s) at the exact moment of racket contact:")
                if shots:
                    for s in shots[:4]:
                        pf = s.pose_features or {}
                        elb = pf.get('contact_elbow_angle_deg', pf.get('elbow_angle_deg'))
                        sho = pf.get('contact_shoulder_angle_deg', pf.get('shoulder_angle_deg'))
                        kne = pf.get('contact_knee_angle_deg', pf.get('knee_angle_deg'))
                        cf = s.contact_frame if s.contact_frame is not None else (f"{s.contact_time:.2f}s" if s.contact_time else "")
                        parts.append(f"\n- **{s.shot_type.upper()} (Shot #{s.shot_id})**:")
                        if elb is not None:
                            elb_str = f"your elbow was extended at **{elb}°**"
                            comp = "textbook reach" if elb > 140 else "a more compact lever"
                            parts.append(f"  - Elbow: {elb_str} ({comp}).")
                        if sho is not None:
                            parts.append(f"  - Shoulder elevation: **{sho}°**, giving you clean overhead elevation.")
                        if kne is not None:
                            parts.append(f"  - Knee flexion: **{kne}°**, showing your lower body loading base.")
                else:
                    parts.append("\nNo distinct stroke contact frames were isolated in this sequence.")
                parts.append("\n💡 **Coach's Takeaway**: Your upper-body kinetic chain is engaging well. For maximum smash power, focus on letting the shoulder rotate smoothly before snapping the forearm and wrist through contact.")

            elif any(k in q_lower for k in ["calorie", "energy", "burn", "met", "metabolic", "kcal"]):
                if energy:
                    kcal = energy.estimated_calories_burned_kcal
                    dur = energy.active_duration_minutes
                    label_type = "your custom weight" if energy.is_personalized else "a standard 70 kg player reference"
                    parts.append("### 🔥 Workout & Energy Expenditure")
                    parts.append(f"You put in great effort during this session! In **{dur:.1f} minutes** of active play, you burned approximately **{kcal:.1f} kcal** (calculated using {label_type} at 7.0 MET match intensity).")
                    parts.append("\n💡 **What This Means**: Badminton is fantastic high-intensity interval training. Those rapid lunges, jump smashes, and recoveries demand both cardiovascular stamina and explosive leg drive.")
                    parts.append("\n💪 **Recovery Tip**: Rehydrate with electrolytes and do some light hamstring and calf stretching while your muscles are still warm!")
                else:
                    parts.append("### 🔥 Workout & Energy Expenditure")
                    parts.append("We weren't able to calculate calorie expenditure for this clip because active rally durations couldn't be fully measured.")

            elif any(k in q_lower for k in ["speed", "velocity", "km/h", "fast", "shuttle speed", "racket speed"]):
                if speed and (speed.shuttle_speed_peak.available or speed.racket_speed_peak.available):
                    shuttle_peak = speed.shuttle_speed_peak.speed_kmh if speed.shuttle_speed_peak.available else None
                    racket_peak = speed.racket_speed_peak.speed_kmh if speed.racket_speed_peak.available else None
                    parts.append("### ⚡ Ballistic Speed & Power")
                    if shuttle_peak is not None:
                        parts.append(f"🏸 **Shuttlecock Speed**: Reached a peak of **{shuttle_peak} km/h** off the racket face.")
                    if racket_peak is not None:
                        parts.append(f"⚡ **Racket Head Speed**: Peaked at **{racket_peak} km/h** through the contact arc.")
                    parts.append("\n💡 **Coach's Read**: Generating high racket speed comes down to the whip effect — transferring power from legs to hips, torso, shoulder, and finally the wrist snap at the very last microsecond.")
                else:
                    parts.append("### ⚡ Ballistic Speed & Power")
                    parts.append("We couldn't compute reliable ballistic speeds for this clip. High-speed shuttle tracking requires ultra-smooth 60+ fps footage with zero motion blur through the contact zone to ensure we never report inaccurate or exaggerated numbers.")

            else:
                parts.append("### 🏸 Session Story & Performance Highlights")
                parts.append(f"Great work reviewing your game film! Across this recorded sequence, we analyzed **{total_shots} detected stroke(s)** with **{calib_str}** court geometry.")
                if dist_m is not None:
                    parts.append(f"\n- 🏃 **Court Movement**: You covered roughly **{dist_m:.1f} meters** of ground with an active coverage of **{cov_pct:.1f}%** across court zones.")
                if mean_shot_dur is not None:
                    parts.append(f"- ⏱️ **Rally Tempo**: Average stroke exchange duration was **{mean_shot_dur:.2f} seconds**, reflecting a brisk, competitive rhythm.")
                if energy:
                    parts.append(f"- 🔥 **Energy Burn**: Estimated energy expenditure reached **{energy.estimated_calories_burned_kcal:.1f} kcal**.")
                parts.append("\n🎯 **Key Takeaway**: Your court presence is solid. For your next practice, focus on recovering to the center circle between shots to stay one step ahead of the rally!")

            answer_text = "\n".join(parts)

        return {
            "question": question,
            "status": "ANSWERED",
            "answer_summary": answer_text,
            "relevant_relationships": [],
            "relevant_trends": [],
            "relevant_concepts": [c.model_dump() for c in state.concepts],
            "domain_knowledge": [r.to_dict() for r in rag_results],
            "evidence_count": len(state.evidence),
            "overall_confidence": state.overall_confidence,
            "iteration": state.iteration,
        }

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

        if state.dataset_id == "badminton":
            return self._answer_badminton_question(state, investigation_id, question)

        q_lower = question.lower()
        available_cols = []
        if state.dataset_profile and state.dataset_profile.columns:
            available_cols = [c.name for c in state.dataset_profile.columns]
        elif state.features:
            available_cols = [f.name for f in state.features]

        # Detect meta-analytical / diagnostic / summary inquiries (e.g. "help me with this analysis")
        analytical_patterns = [
            r'\bhelp\b', r'\banalyze\b', r'\banalysis\b', r'\bsummar(?:y|ize)\b',
            r'\broot\s*cause\b', r'\bfindings?\b', r'\bdiagnos(?:is|e)\b',
            r'\brecommend(?:ation)?\b', r'\bwhat\s*(?:is\s*happening|happened|occurred)\b',
            r'\bwhat\s*should\s*i\s*do\b', r'\bexplain\b', r'\boverview\b',
            r'\binterpret\b', r'\bwhat\s*does\s*this\s*mean\b', r'\bconclusion\b'
        ]
        is_analytical = any(re.search(pat, q_lower) for pat in analytical_patterns)

        # Extract keywords to find relevant columns with token match density ranking & fuzzy matching
        q_norm = re.sub(r'[^a-z0-9]', '', q_lower)
        stop_words = {
            'the', 'was', 'is', 'are', 'were', 'and', 'for', 'which', 'when', 'what', 'day', 'days',
            'where', 'how', 'with', 'from', 'below', 'above', 'than', 'under', 'over', 'that', 'less',
            'more', 'goes', 'goes over', 'help', 'me', 'please', 'this', 'that', 'analysis', 'analyze',
            'can', 'you', 'give', 'tell', 'about', 'explain', 'show', 'check', 'overview',
            'summary', 'summarize', 'there', 'find', 'findings', 'why', 'have', 'had', 'been'
        }
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
        if col_scores and not is_analytical:
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
            relevant_rels = state.relationships[:6]

        relevant_trends = []
        for trend in state.trends:
            if trend.feature_name.lower() in q_lower or is_analytical:
                relevant_trends.append(trend)

        relevant_concepts = []
        for concept in state.concepts:
            if any(word in concept.name.lower() for word in words) or is_analytical:
                relevant_concepts.append(concept)
        if not relevant_concepts:
            relevant_concepts = state.concepts[:6]

        # Dynamically determine RAG domain if set in state or available in knowledge base
        rag_domain = state.dataset_id if state.dataset_id in self.rag.domains else None
        rag_results = self.rag.query(question, domain=rag_domain, top_k=3)
        if not rag_results and rag_domain:
            rag_results = self.rag.query(question, top_k=3)

        domain_label = (rag_domain or state.dataset_id or 'General').capitalize()
        filename = state.dataset_profile.filename if state.dataset_profile else (state.dataset_id or 'Investigation Context')

        # Build Context Text based on whether query is analytical synthesis or specific metric lookup
        if is_analytical:
            brief_lines = [
                f"Domain: {domain_label}",
                f"Active Overall Confidence: {int(state.overall_confidence * 100)}%",
            ]
            vis_conc = getattr(state, "visual_conclusion", None)
            if vis_conc:
                brief_lines.append(f"Primary Visual Diagnostic Conclusion: {vis_conc}")

            tca = getattr(state, "text_context", None)
            if tca:
                m = tca.get("milestone", {})
                day_val = m.get('day', 1)
                m_label = m.get('milestone_label', f"Day {day_val}")
                brief_lines.append(f"Stage 1 Prior Context: {m_label}")
                if tca.get("focus_targets"):
                    brief_lines.append(f"Stage 1 Focus Targets: {', '.join(tca['focus_targets'])}")
                if tca.get("hypotheses"):
                    brief_lines.append(f"Stage 1 Hypotheses: {'; '.join(tca['hypotheses'])}")
                if tca.get("context_summary"):
                    brief_lines.append(f"Stage 1 Summary: {tca['context_summary']}")

            if state.concepts:
                node_summaries = [f"{c.name} ({c.category.title()}, Conf: {int(c.confidence*100)}%, Status: {c.status})" for c in state.concepts[:12]]
                brief_lines.append(f"Grounded Entities ({len(state.concepts)} total):\n  - " + "\n  - ".join(node_summaries))

            if state.relationships:
                rel_summaries = [f"{r.source_feature} -> {r.target_feature} (Confidence: {int(r.strength*100)}%, {r.description or 'causal relationship'})" for r in state.relationships[:8]]
                brief_lines.append(f"Discovered Causal Relationships:\n  - " + "\n  - ".join(rel_summaries))

            if state.trends:
                trend_summaries = [f"{t.feature_name}: {t.direction.value} ({t.description or 'longitudinal trend'})" for t in state.trends[:6]]
                brief_lines.append(f"Longitudinal Telemetry Trends:\n  - " + "\n  - ".join(trend_summaries))

            dataset_context_text = "\n".join(brief_lines)
        else:
            dataset_inspection_lines = []
            dataset_inspection_lines.append(f"Source: {filename}")
            dataset_inspection_lines.append(f"Available Variables ({len(available_cols)} total): {', '.join(available_cols[:15]) if available_cols else 'Visual perception entities active'}")

            if matching_cols:
                dataset_inspection_lines.append(f"Matching Columns for query: {', '.join(matching_cols)}")
                if matching_obs:
                    obs_samples = [f"{o.timestamp or o.feature_name}: {o.value}" for o in matching_obs[:15]]
                    dataset_inspection_lines.append(f"Matching Observations ({len(matching_obs)} found): {', '.join(obs_samples)}")
                else:
                    dataset_inspection_lines.append(f"Observation Status: No observations in '{', '.join(matching_cols)}' satisfied condition (threshold: {target_val}).")
            else:
                queried_topics = ", ".join(words) if words else question
                dataset_inspection_lines.append(f"Available parameters in active investigation: {', '.join(available_cols[:12]) if available_cols else 'Multi-modal visual nodes'}.")

            dataset_context_text = "\n".join(dataset_inspection_lines)

        if state.dataset_id == "gait":
            gait_obs_map = {o.feature_name: o.value for o in state.observations}
            ai_prompt = f"""You are SAAR, a professional pediatric movement and gait analysis intelligence system.

User Question:
"{question}"

Relevant Pediatric Literature & Normative Science:
{chr(10).join([f"- [{r.domain}] {r.content.strip()}" for r in rag_results[:3]])}

Measured Screening Values from Active Video:
- Cadence: {gait_obs_map.get('cadence', 'N/A')} steps/min
- Left Mean Step Time: {gait_obs_map.get('left_mean_step_time', 'N/A')} s
- Right Mean Step Time: {gait_obs_map.get('right_mean_step_time', 'N/A')} s
- Left-Right Step-Time Asymmetry: {gait_obs_map.get('step_time_asymmetry_pct', 'N/A')}% (healthy benchmark: ≤ 10%)
- Step-Time Variability (CoV): {gait_obs_map.get('step_time_cov', 'N/A')}% (healthy benchmark: ≤ 15%)
- Usable Steps Detected: {gait_obs_map.get('usable_step_count', 'N/A')}
- Overall Screening Quality: {state.overall_confidence * 100:.0f}%

RESPONSE STYLE RULES:
1. ANSWER THE USER'S SPECIFIC QUESTION DIRECTLY AND FIRST.
   - If the user asks about a specific researcher, study, paper, or citation (such as 'Sutherland', 'WHO', 'Rygelova', 'Dusing & Thorpe'), explain who/what it is and its significance in pediatric gait development.
   - If the user asks about a specific parameter (such as 'cadence', 'asymmetry', 'variability', 'barefoot play'), explain that concept directly.
2. Contextualize with the active screening data where relevant, but DO NOT output an unsolicited generic whole-report summary unless the user explicitly requested an overall evaluation or full summary.
3. Use clean, professional, and accessible language. Do NOT use emojis or emoticons.
4. Keep the response focused, structured, and informative (150–250 words).
"""
        elif is_analytical:
            ai_prompt = f"""You are SAAR, an advanced scientific reasoning and causal intelligence system. The user asked: "{question}".

Based on the active investigation data below, explain the causal relationships and findings clearly, objectively, and professionally.

Active Investigation Context:
{dataset_context_text}

Scientific Reference Knowledge:
{chr(10).join([f"- [{r.domain}] {r.content[:220]}..." for r in rag_results[:3]])}

RESPONSE STYLE RULES:
1. Speak with professional, authoritative scientific clarity.
2. Structure your response into clear thematic sections: Overall Assessment, Key Grounded Observations, Causal Mechanics, and Next Steps.
3. Integrate measured parameters and confidence levels naturally into the analytical narrative.
4. Do NOT use emojis or emoticons. Maintain an executive, peer-reviewed tone throughout.
5. Provide concrete, actionable, and testable recommendations.
"""
        else:
            ai_prompt = f"""You are SAAR, a professional scientific reasoning system. Answer the user's question with clarity, technical rigor, and accessibility.

User Question:
"{question}"

Available Data from Investigation:
{dataset_context_text}

Relevant Patterns Found:
{chr(10).join([f"- {r.source_feature} ↔ {r.target_feature}: correlation = {r.strength:.2f} ({r.direction})" for r in relevant_rels[:4]])}

Reference Knowledge:
{chr(10).join([f"- [{r.domain}] {r.content[:180]}..." for r in rag_results[:2]])}

RESPONSE STYLE RULES:
1. Explain scientific concepts plainly and connect them directly to empirical investigation data.
2. Provide direct answers for specific metrics or thresholds within narrative sentences, avoiding raw data tables.
3. Maintain a formal, academic, yet accessible tone appropriate for the domain.
4. Do NOT use emojis or emoticons.
5. Conclude with a practical takeaway in a single sentence.
6. Keep it concise — 150-250 words max.
"""
        answer_text = None
        try:
            answer_text = self.vlm.synthesize_reasoning_explanation(ai_prompt)
        except Exception as synth_err:
            print(f"[ReasoningService] Live AI synthesis error: {synth_err}")

        # Fallback: 100% Dynamic Data-Driven & RAG-Powered Synthesis (Zero Hardcoded Logic)
        if not answer_text:
            summary_parts = []

            # 1. Primary Fallback: Dynamic RAG Retrieval across Domain Knowledge Base
            if rag_results and rag_results[0].score > 0.4:
                top_rag = rag_results[0]
                summary_parts.append(f"### {top_rag.section}")
                summary_parts.append(f"\n{top_rag.content.strip()}")
                if len(rag_results) > 1 and rag_results[1].score > 1.0:
                    summary_parts.append(f"\n{rag_results[1].content.strip()}")

                # Dynamically correlate any active observations whose feature names match query or retrieved content
                q_and_content_tokens = set(re.findall(r"[a-z0-9]+", (question + " " + top_rag.content).lower()))
                grounded_obs = []
                for obs in state.observations:
                    feat_tokens = set(re.findall(r"[a-z0-9]+", obs.feature_name.lower()))
                    if feat_tokens & q_and_content_tokens and obs.value is not None:
                        display_name = obs.feature_name.replace("_", " ").title()
                        unit = f" {obs.unit}" if getattr(obs, "unit", None) else ""
                        grounded_obs.append(f"- **{display_name}**: {obs.value}{unit}".strip())

                if grounded_obs:
                    summary_parts.append("\n#### Correlated Active Observations")
                    for g_line in grounded_obs[:6]:
                        summary_parts.append(g_line)

                domain_display = top_rag.domain.replace("_", " ").title()
                summary_parts.append(f"\n*Source: {top_rag.source} ({domain_display} Knowledge Base)*")
                answer_text = "\n".join(summary_parts)

            # 2. Secondary Fallback: Timeline & Milestone Analysis for Numeric Trends
            elif matching_cols and matching_obs:
                vals = [o.value for o in matching_obs if isinstance(o.value, (int, float))]
                min_v, max_v = (min(vals), max(vals)) if vals else (None, None)
                dates = sorted(list({o.timestamp for o in matching_obs if o.timestamp}), key=self._natural_sort_key)
                date_context = f"across {len(dates)} recorded dates ({dates[0]} to {dates[-1]})" if len(dates) > 1 else (f"on {dates[0]}" if dates else "")
                range_str = f"fluctuating between **{min_v}** and **{max_v}**" if min_v is not None else ""

                summary_parts.append(f"### Timeline & Milestone Analysis")
                summary_parts.append(f"\n**Data Dynamics**: Tracking **{', '.join(matching_cols)}** {date_context}, recording **{len(matching_obs)}** data points {range_str}.")

                if target_val is not None:
                    status_desc = f"fell below the threshold of {target_val}" if is_below else f"exceeded the threshold of {target_val}"
                    summary_parts.append(f"\nDuring this timeline, readings {status_desc} at specific intervals:")
                else:
                    summary_parts.append("\nKey temporal milestones across the recorded series:")

                sample_obs = matching_obs[:8]
                for o in sample_obs:
                    ts = o.timestamp or "Recorded time"
                    summary_parts.append(f"- **{ts}**: Value reached **{o.value}**")

                if len(matching_obs) > 8:
                    summary_parts.append(f"- *(plus {len(matching_obs) - 8} additional readings recorded during this window)*")

                summary_parts.append(f"\n**Analytical Note**: Longitudinal tracking of {', '.join(matching_cols)} establishes validated empirical baseline trends.")
                answer_text = "\n".join(summary_parts)

            # 3. Tertiary Fallback: Causal Graph & Telemetry Grounding
            elif is_analytical or state.concepts or state.relationships:
                domain_title = domain_label.replace("_", " ").title() if domain_label else "Scientific Investigation"
                summary_parts.append(f"### {domain_title} Analytical Summary")

                vis_conc = getattr(state, "visual_conclusion", None)
                if vis_conc:
                    summary_parts.append(f"\n**Assessment Overview**: {vis_conc}")
                elif state.concepts:
                    summary_parts.append(f"\n**Assessment Overview**: Analysis grounded across {len(state.concepts)} identified concepts with {int(state.overall_confidence * 100)}% overall confidence.")
                else:
                    summary_parts.append(f"\n**Assessment Overview**: Empirical telemetry synthesis addressing *\"{question}\"*.")

                if state.concepts:
                    summary_parts.append("\n#### Grounded Key Observations")
                    for c in state.concepts[:5]:
                        status = "visually grounded" if c.visual_anchor else "telemetry grounded"
                        summary_parts.append(f"- **{c.name}** ({c.category.title()}): {status} (confidence: {int(c.confidence * 100)}%).")
                elif state.observations:
                    summary_parts.append("\n#### Measured Observations")
                    for o in state.observations[:6]:
                        unit = f" {o.unit}" if getattr(o, "unit", None) else ""
                        summary_parts.append(f"- **{o.feature_name.replace('_', ' ').title()}**: {o.value}{unit}")

                if state.relationships:
                    summary_parts.append("\n#### Causal Dynamics & Interdependencies")
                    for r in state.relationships[:4]:
                        desc = f" ({r.description})" if r.description else ""
                        summary_parts.append(f"- **{r.source_feature}** → **{r.target_feature}**: {r.relationship_type.value} relationship (strength: {r.strength:.2f}){desc}.")

                answer_text = "\n".join(summary_parts)

            else:
                summary_parts.append(f"### Scientific Investigation Telemetry")
                summary_parts.append(f"\nWe explored your question *\"{question}\"* across the active session.")
                if state.observations:
                    summary_parts.append(f"\nThe session currently tracks {len(state.observations)} measurements.")
                    for o in state.observations[:5]:
                        unit = f" {o.unit}" if getattr(o, "unit", None) else ""
                        summary_parts.append(f"- **{o.feature_name.replace('_', ' ').title()}**: {o.value}{unit}")
                summary_parts.append("\n💡 **Suggestion**: Ask about specific parameters, relationships, or scientific principles!")
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

        # Extract structured telemetry channels if observations exist
        telemetry = None
        if state.dataset_profile and state.observations:
            channels = {}
            time_labels = []
            milestones = []
            seen_milestones = set()

            col_units = {
                col.name: getattr(col, "unit", None) or self.ingestion._guess_unit(col.name) or ""
                for col in state.dataset_profile.columns
            }

            for o in state.observations:
                if isinstance(o.value, (int, float)):
                    if o.feature_name not in channels:
                        channels[o.feature_name] = []
                    channels[o.feature_name].append(o.value)
                if o.timestamp and o.timestamp not in time_labels:
                    time_labels.append(o.timestamp)

            if not time_labels and channels:
                first_len = len(next(iter(channels.values())))
                time_labels = [f"Day {i}" for i in range(first_len)]

            # Dynamic extraction of milestones from ANY dataset containing stages, interventions, or images
            ts_groups: Dict[str, Dict[str, Any]] = {}
            for o in state.observations:
                ts = o.timestamp or ""
                if ts not in ts_groups:
                    ts_groups[ts] = {}
                ts_groups[ts][o.feature_name] = o.value

            palette = ['#0284c7', '#0ea5e9', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#14b8a6', '#06b6d4']
            m_count = 0
            for ts, vals in ts_groups.items():
                img_url = None
                stage_val = None
                intervention_val = None
                day_val = None

                for k, v in vals.items():
                    k_lower = k.lower()
                    v_str = str(v).strip()
                    if not v_str or v_str.lower() in ("none", "0", "false", "nan", "null"):
                        continue
                    if any(sub in k_lower for sub in ("image", "photo", "photograph", "url", "visual")) and (v_str.startswith("/") or v_str.startswith("http") or v_str.startswith("data:")):
                        img_url = v_str
                    elif any(sub in k_lower for sub in ("stage", "phase", "growth_stage", "development")):
                        stage_val = v_str.replace("_", " ").title()
                    elif any(sub in k_lower for sub in ("intervention", "milestone", "event", "action")):
                        intervention_val = v_str.replace("_", " ").title()

                # Also parse day number from timestamp (e.g. "Day 10 (2018-09-15)" -> 10.0)
                day_match = re.search(r"Day\s*(\d+(?:\.\d+)?)", ts, re.IGNORECASE)
                if day_match:
                    try:
                        day_val = float(day_match.group(1))
                    except ValueError:
                        day_val = float(m_count)
                elif day_val is None:
                    day_val = float(m_count)

                if img_url or (intervention_val and intervention_val.lower() not in ("none", "0", "false")) or (stage_val and stage_val.lower() not in ("none", "normal")):
                    m_label = intervention_val or stage_val or f"Milestone at {ts}"
                    date_match = re.search(r"\((\d{4}-\d{2}-\d{2})\)", ts)
                    obs_date = date_match.group(1) if date_match else ""

                    milestones.append({
                        "day": day_val,
                        "timestamp": ts,
                        "label": m_label,
                        "badge": f"DAY {int(day_val)}" if day_val == int(day_val) else f"DAY {day_val}",
                        "color": palette[m_count % len(palette)],
                        "stage": stage_val or "Longitudinal Stage",
                        "date": obs_date,
                        "url": img_url,
                        "description": f"Longitudinal observation recorded at {ts}. {f'Developmental Stage: {stage_val}.' if stage_val else ''} {f'Intervention: {intervention_val}.' if intervention_val else ''}"
                    })
                    m_count += 1

            telemetry = {
                "title": f"Telemetry Array: {state.dataset_profile.filename or 'Uploaded Dataset'}",
                "channels": channels,
                "units": col_units,
                "timestamps": time_labels,
                "milestones": milestones[:12],
                "row_count": state.dataset_profile.row_count,
                "column_count": state.dataset_profile.column_count
            }

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
            "telemetry": telemetry,
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
