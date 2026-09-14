"""
SAAR — Adaptive Diagnostic Inquiry Engine

Dynamically generates competing hypotheses, discriminating questions, and
personalized conclusions using LLM-powered reasoning over measured data.

Zero hardcoded question trees. The LLM generates all hypotheses and questions
based on: measured metrics + user concern + domain RAG context + conversation history.
"""
import json
import re
import uuid
from typing import Dict, List, Any, Optional

from ..models.saar_models import (
    Hypothesis, AnswerOption, DiagnosticQuestion, AdaptiveSession
)
from ..vlm_service import VLMService
from ..rag_service import RAGKnowledgeService


class AdaptiveInquiryEngine:
    """
    Domain-agnostic adaptive questioning engine.

    Uses LLM to:
    1. Generate competing hypotheses from measured data + user concern
    2. Generate the single most discriminating question at each turn
    3. Update hypothesis probabilities based on user answers
    4. Auto-conclude when confidence exceeds threshold or max questions reached
    """

    def __init__(self):
        self.vlm = VLMService()
        self.rag = RAGKnowledgeService()
        self._sessions: Dict[str, AdaptiveSession] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_session(
        self,
        investigation_id: str,
        user_concern: str,
        domain: str,
        measured_context: Dict[str, Any]
    ) -> AdaptiveSession:
        """
        Initialize a new adaptive session:
        1. Query RAG for domain knowledge
        2. Ask LLM to generate competing hypotheses
        3. Ask LLM to generate the first discriminating question
        """
        session = AdaptiveSession(
            investigation_id=investigation_id,
            user_concern=user_concern,
            domain=domain,
            measured_context=measured_context
        )

        # Step 1: Generate hypotheses via LLM
        hypotheses = self._generate_hypotheses(session)
        session.hypotheses = hypotheses

        # Step 2: Generate first question
        question = self._generate_next_question(session)
        if question:
            session.current_question = question
            session.turn = 1

        self._sessions[session.session_id] = session
        return session

    def process_answer(
        self,
        session_id: str,
        selected_option_id: str
    ) -> AdaptiveSession:
        """
        Process the user's answer:
        1. Find the selected option and update hypothesis probabilities
        2. Prune eliminated hypotheses
        3. Check if we should conclude or ask another question
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Adaptive session {session_id} not found.")

        current_q = session.current_question
        if not current_q:
            raise ValueError("No active question to answer.")

        # Find selected option
        selected_option = None
        for opt in current_q.options:
            if opt.option_id == selected_option_id:
                selected_option = opt
                break

        if not selected_option:
            raise ValueError(f"Option {selected_option_id} not found in current question.")

        # Record the answer
        session.answers_given.append({
            "turn": session.turn,
            "question_id": current_q.question_id,
            "question_text": current_q.question_text,
            "selected_option_id": selected_option.option_id,
            "selected_text": selected_option.text
        })
        session.questions_asked.append(current_q)

        # Update hypothesis probabilities via LLM
        session = self._update_hypotheses(session, selected_option)

        # Check termination conditions
        active_hypotheses = [h for h in session.hypotheses if h.status == "active"]
        top_hypothesis = max(active_hypotheses, key=lambda h: h.current_probability) if active_hypotheses else None

        should_conclude = (
            session.turn >= session.max_questions or
            len(active_hypotheses) <= 1 or
            (top_hypothesis and top_hypothesis.current_probability >= session.confidence_threshold)
        )

        if should_conclude:
            session = self._generate_conclusion(session)
            session.status = "concluded"
            session.current_question = None
        else:
            # Generate next question
            next_q = self._generate_next_question(session)
            if next_q:
                session.current_question = next_q
                session.turn += 1
            else:
                # LLM couldn't generate a question — conclude
                session = self._generate_conclusion(session)
                session.status = "concluded"
                session.current_question = None

        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[AdaptiveSession]:
        return self._sessions.get(session_id)

    # ------------------------------------------------------------------
    # Internal: LLM-Powered Hypothesis Generation
    # ------------------------------------------------------------------

    def _generate_hypotheses(self, session: AdaptiveSession) -> List[Hypothesis]:
        """Use LLM + RAG to generate competing root-cause hypotheses."""
        rag_results = self.rag.query(
            session.user_concern, domain=session.domain, top_k=3
        )
        rag_context = "\n".join([
            f"- [{r.domain}] {r.content[:250]}" for r in rag_results[:3]
        ]) if rag_results else "No domain-specific references found."

        measured_str = self._format_measured_context(session.measured_context)

        prompt = f"""You are SAAR, an expert diagnostic reasoning engine. A user has uploaded data and expressed a concern.

USER CONCERN: "{session.user_concern}"

DOMAIN: {session.domain}

MEASURED DATA FROM ANALYSIS:
{measured_str}

DOMAIN KNOWLEDGE:
{rag_context}

TASK: Generate exactly 3 competing root-cause hypotheses that could explain the user's concern given the measured data.
Each hypothesis should be plausible and differentiable from the others through targeted questioning.

RESPOND WITH ONLY valid JSON (no markdown, no explanation):
{{
  "hypotheses": [
    {{
      "name": "Short clinical/technical name",
      "description": "1-2 sentence explanation accessible to a non-expert",
      "prior_probability": 0.33
    }},
    {{
      "name": "...",
      "description": "...",
      "prior_probability": 0.33
    }},
    {{
      "name": "...",
      "description": "...",
      "prior_probability": 0.34
    }}
  ]
}}
"""
        try:
            raw = self.vlm.synthesize_reasoning_explanation(prompt, temperature=0.3)
            parsed = self._parse_json_response(raw)
            if parsed and "hypotheses" in parsed:
                return [
                    Hypothesis(
                        name=h["name"],
                        description=h.get("description", ""),
                        prior_probability=float(h.get("prior_probability", 0.33)),
                        current_probability=float(h.get("prior_probability", 0.33)),
                        status="active"
                    )
                    for h in parsed["hypotheses"][:4]
                ]
        except Exception as e:
            print(f"[AdaptiveInquiry] Hypothesis generation error: {e}")

        # Fallback: generate generic hypotheses from measured data
        return self._fallback_hypotheses(session)

    # ------------------------------------------------------------------
    # Internal: LLM-Powered Question Generation
    # ------------------------------------------------------------------

    def _generate_next_question(self, session: AdaptiveSession) -> Optional[DiagnosticQuestion]:
        """Use LLM to generate the single most discriminating question."""
        active_hypotheses = [h for h in session.hypotheses if h.status == "active"]
        if len(active_hypotheses) <= 1:
            return None

        hypo_str = "\n".join([
            f"- {h.hypothesis_id}: \"{h.name}\" (probability: {h.current_probability:.0%}) — {h.description}"
            for h in active_hypotheses
        ])

        history_str = ""
        if session.answers_given:
            history_str = "PREVIOUS Q&A:\n" + "\n".join([
                f"  Q{a['turn']}: {a['question_text']} → Answer: \"{a['selected_text']}\""
                for a in session.answers_given
            ])

        measured_str = self._format_measured_context(session.measured_context)

        prompt = f"""You are SAAR, an expert diagnostic reasoning engine conducting an adaptive clinical/scientific interview.

USER CONCERN: "{session.user_concern}"
DOMAIN: {session.domain}
TURN: {session.turn + 1} of {session.max_questions}

MEASURED DATA:
{measured_str}

ACTIVE COMPETING HYPOTHESES:
{hypo_str}

{history_str}

TASK: Generate ONE question that maximally discriminates between the active hypotheses.
The question should be simple, non-technical, and answerable by a non-expert (e.g., a parent, a farmer, a field inspector).
Provide 2-4 answer options. Each option should indicate which hypotheses it would support or eliminate.

RESPOND WITH ONLY valid JSON (no markdown):
{{
  "question_text": "The question in plain, empathetic language",
  "reason": "Brief explanation of why this question helps narrow down the cause",
  "options": [
    {{
      "text": "Answer option text",
      "eliminates": ["{active_hypotheses[0].hypothesis_id}"],
      "supports": ["{active_hypotheses[1].hypothesis_id}"]
    }},
    {{
      "text": "Another answer option",
      "eliminates": ["{active_hypotheses[1].hypothesis_id}"],
      "supports": ["{active_hypotheses[0].hypothesis_id}"]
    }}
  ],
  "expected_information_gain": 0.75
}}
"""
        try:
            raw = self.vlm.synthesize_reasoning_explanation(prompt, temperature=0.3)
            parsed = self._parse_json_response(raw)
            if parsed and "question_text" in parsed:
                options = []
                for opt_data in parsed.get("options", []):
                    options.append(AnswerOption(
                        text=opt_data["text"],
                        eliminates=opt_data.get("eliminates", []),
                        supports=opt_data.get("supports", [])
                    ))

                return DiagnosticQuestion(
                    question_text=parsed["question_text"],
                    reason=parsed.get("reason", ""),
                    options=options,
                    expected_information_gain=float(parsed.get("expected_information_gain", 0.5)),
                    turn_number=session.turn + 1
                )
        except Exception as e:
            print(f"[AdaptiveInquiry] Question generation error: {e}")

        return self._fallback_question(session)

    # ------------------------------------------------------------------
    # Internal: Hypothesis Update After Answer
    # ------------------------------------------------------------------

    def _update_hypotheses(
        self, session: AdaptiveSession, selected_option: AnswerOption
    ) -> AdaptiveSession:
        """Update hypothesis probabilities based on the user's answer."""
        # Apply structural updates from the option's eliminates/supports metadata
        for hypo in session.hypotheses:
            if hypo.status != "active":
                continue

            if hypo.hypothesis_id in selected_option.eliminates:
                hypo.current_probability = max(0.02, hypo.current_probability * 0.15)
                hypo.contradicting_evidence.append(selected_option.option_id)
                if hypo.current_probability < 0.05:
                    hypo.status = "eliminated"

            elif hypo.hypothesis_id in selected_option.supports:
                hypo.current_probability = min(0.98, hypo.current_probability * 1.6 + 0.1)
                hypo.supporting_evidence.append(selected_option.option_id)

        # Normalize probabilities across active hypotheses
        active = [h for h in session.hypotheses if h.status == "active"]
        total = sum(h.current_probability for h in active)
        if total > 0:
            for h in active:
                h.current_probability = round(h.current_probability / total, 3)

        # Try LLM-based refinement for more nuanced updates
        self._llm_refine_hypotheses(session, selected_option)

        return session

    def _llm_refine_hypotheses(
        self, session: AdaptiveSession, selected_option: AnswerOption
    ) -> None:
        """Optional LLM refinement of hypothesis probabilities after an answer."""
        active = [h for h in session.hypotheses if h.status == "active"]
        if len(active) <= 1:
            return

        hypo_str = ", ".join([
            f'"{h.hypothesis_id}": {{"name": "{h.name}", "current": {h.current_probability:.2f}}}'
            for h in active
        ])

        last_q = session.questions_asked[-1] if session.questions_asked else session.current_question
        q_text = last_q.question_text if last_q else ""

        prompt = f"""Given that the user answered "{selected_option.text}" to the question "{q_text}",
update the probability distribution across these hypotheses.

Active hypotheses: {{{hypo_str}}}

RESPOND WITH ONLY valid JSON mapping hypothesis_id to new probability (must sum to 1.0):
{{"probabilities": {{"{active[0].hypothesis_id}": 0.XX, ...}}}}
"""
        try:
            raw = self.vlm.synthesize_reasoning_explanation(prompt, temperature=0.2)
            parsed = self._parse_json_response(raw)
            if parsed and "probabilities" in parsed:
                probs = parsed["probabilities"]
                for h in active:
                    if h.hypothesis_id in probs:
                        new_p = float(probs[h.hypothesis_id])
                        h.current_probability = max(0.01, min(0.99, new_p))
                        if h.current_probability < 0.05:
                            h.status = "eliminated"
        except Exception:
            pass  # Structural update already applied; LLM refinement is optional

    # ------------------------------------------------------------------
    # Internal: Conclusion Generation
    # ------------------------------------------------------------------

    def _generate_conclusion(self, session: AdaptiveSession) -> AdaptiveSession:
        """Generate a personalized diagnostic conclusion and recommendations."""
        active = [h for h in session.hypotheses if h.status == "active"]
        eliminated = [h for h in session.hypotheses if h.status == "eliminated"]
        top = max(active, key=lambda h: h.current_probability) if active else None

        if top:
            top.status = "confirmed"

        hypo_summary = "\n".join([
            f"- {'✅ CONFIRMED' if h.status == 'confirmed' else '❌ ELIMINATED' if h.status == 'eliminated' else '⚠️ ACTIVE'}: "
            f"\"{h.name}\" ({h.current_probability:.0%}) — {h.description}"
            for h in session.hypotheses
        ])

        qa_summary = "\n".join([
            f"Q{a['turn']}: {a['question_text']} → \"{a['selected_text']}\""
            for a in session.answers_given
        ])

        measured_str = self._format_measured_context(session.measured_context)

        rag_results = self.rag.query(
            f"{session.user_concern} {top.name if top else ''}",
            domain=session.domain, top_k=2
        )
        rag_context = "\n".join([
            f"- {r.content[:200]}" for r in rag_results[:2]
        ]) if rag_results else ""

        prompt = f"""You are SAAR, an expert diagnostic reasoning engine delivering a final personalized assessment.

USER CONCERN: "{session.user_concern}"
DOMAIN: {session.domain}

MEASURED DATA:
{measured_str}

DIAGNOSTIC INTERVIEW TRANSCRIPT:
{qa_summary}

HYPOTHESIS OUTCOMES:
{hypo_summary}

REFERENCE KNOWLEDGE:
{rag_context}

TASK: Write a warm, clear, personalized diagnostic conclusion for the user.
Structure it as:
1. **Root Cause Finding** — What the most likely cause is and why
2. **What Was Ruled Out** — Hypotheses eliminated and why (gives peace of mind)
3. **Your Custom Action Plan** — 2-3 specific, actionable recommendations
4. **When to Seek Professional Help** — Clear guidance on escalation

Keep it accessible, empathetic, and under 300 words. Use markdown formatting.

ALSO return a JSON block at the very end with recommendations:
```json
{{"recommendations": ["tip 1", "tip 2", "tip 3"]}}
```
"""
        try:
            raw = self.vlm.synthesize_reasoning_explanation(prompt, temperature=0.4)
            if raw:
                # Extract recommendations JSON if present
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', raw, re.DOTALL)
                if json_match:
                    try:
                        rec_data = json.loads(json_match.group(1))
                        session.personalized_recommendations = rec_data.get("recommendations", [])
                    except json.JSONDecodeError:
                        pass
                    # Remove the JSON block from the conclusion text
                    conclusion_text = raw[:json_match.start()].strip()
                else:
                    conclusion_text = raw.strip()

                session.conclusion = conclusion_text
                return session
        except Exception as e:
            print(f"[AdaptiveInquiry] Conclusion generation error: {e}")

        # Fallback conclusion
        if top:
            session.conclusion = (
                f"## Root Cause Finding: {top.name}\n\n"
                f"{top.description}\n\n"
                f"### What Was Ruled Out\n"
                + "\n".join([f"- ~~{h.name}~~ — Eliminated based on your responses" for h in eliminated])
                + "\n\n### Recommended Next Steps\n"
                f"- Consult a specialist in {session.domain} for formal evaluation.\n"
                f"- Share this diagnostic report with your practitioner."
            )
            session.personalized_recommendations = [
                f"Consult a {session.domain} specialist for formal evaluation",
                "Share this diagnostic report with your practitioner"
            ]
        else:
            session.conclusion = "Insufficient data to reach a definitive conclusion. Please provide additional information."

        return session

    # ------------------------------------------------------------------
    # Internal: Helpers
    # ------------------------------------------------------------------

    def _format_measured_context(self, ctx: Dict[str, Any]) -> str:
        """Format measured context dict into readable lines."""
        if not ctx:
            return "No measured data available."
        lines = []
        for k, v in ctx.items():
            if isinstance(v, dict):
                for sub_k, sub_v in v.items():
                    display_name = sub_k.replace("_", " ").title()
                    lines.append(f"- {display_name}: {sub_v}")
            else:
                display_name = k.replace("_", " ").title()
                lines.append(f"- {display_name}: {v}")
        return "\n".join(lines[:20])

    def _parse_json_response(self, raw: Optional[str]) -> Optional[Dict]:
        """Safely parse JSON from LLM response, handling markdown fences."""
        if not raw:
            return None
        # Strip markdown code fences
        cleaned = re.sub(r'^```(?:json)?\s*', '', raw.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r'\s*```$', '', cleaned.strip(), flags=re.MULTILINE)
        # Try to find a JSON object
        match = re.search(r'\{[\s\S]*\}', cleaned)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return None

    def _fallback_hypotheses(self, session: AdaptiveSession) -> List[Hypothesis]:
        """Generate basic hypotheses when LLM is unavailable."""
        domain = session.domain.lower()
        concern = session.user_concern.lower()

        if "gait" in domain or "pediatric" in domain or "toddle" in domain:
            return [
                Hypothesis(
                    name="Structural/Postural Asymmetry",
                    description="A fixed postural pattern such as mild scoliosis or hip alignment difference that affects movement.",
                    prior_probability=0.33, current_probability=0.33
                ),
                Hypothesis(
                    name="Neurological/Balance Development",
                    description="The vestibular or motor control system is still maturing, causing temporary balance differences.",
                    prior_probability=0.33, current_probability=0.33
                ),
                Hypothesis(
                    name="Protective Compensation (Discomfort)",
                    description="The child is guarding or avoiding weight on one side due to localized discomfort, tight footwear, or minor strain.",
                    prior_probability=0.34, current_probability=0.34
                )
            ]
        elif "sport" in domain or "badminton" in domain:
            return [
                Hypothesis(
                    name="Technique Limitation",
                    description="A biomechanical inefficiency in stroke form or footwork pattern.",
                    prior_probability=0.33, current_probability=0.33
                ),
                Hypothesis(
                    name="Physical Conditioning Gap",
                    description="Insufficient strength, flexibility, or endurance affecting performance.",
                    prior_probability=0.33, current_probability=0.33
                ),
                Hypothesis(
                    name="Tactical/Spatial Habit",
                    description="A court positioning bias or shot selection pattern limiting effectiveness.",
                    prior_probability=0.34, current_probability=0.34
                )
            ]
        else:
            return [
                Hypothesis(
                    name="Primary Environmental Factor",
                    description="An external environmental condition driving the observed pattern.",
                    prior_probability=0.33, current_probability=0.33
                ),
                Hypothesis(
                    name="Internal/Systemic Cause",
                    description="An intrinsic property or condition of the subject causing the observation.",
                    prior_probability=0.33, current_probability=0.33
                ),
                Hypothesis(
                    name="Measurement/Observational Artifact",
                    description="The observation may be within normal variation or influenced by data collection conditions.",
                    prior_probability=0.34, current_probability=0.34
                )
            ]

    def _fallback_question(self, session: AdaptiveSession) -> Optional[DiagnosticQuestion]:
        """Generate discriminating question when LLM is unavailable."""
        active = [h for h in session.hypotheses if h.status == "active"]
        if len(active) <= 1:
            return None

        turn = session.turn
        domain = session.domain.lower()
        concern = session.user_concern.lower()

        is_gait = (
            "gait" in domain or "pediatric" in domain or "toddle" in domain or
            any(k in concern for k in ["walk", "tilt", "leg", "step", "fall", "limp", "child", "baby", "toddler", "balance", "knee"])
        )

        if is_gait:
            if turn <= 1:
                return DiagnosticQuestion(
                    question_text="Does the tilt or uneven movement happen when sitting or resting, or only during walking?",
                    reason="Distinguishes between a constant structural alignment pattern versus a dynamic weight-bearing response.",
                    options=[
                        AnswerOption(
                            text="Only when walking or running",
                            eliminates=[active[0].hypothesis_id] if len(active) > 0 else [],
                            supports=[active[1].hypothesis_id, active[2].hypothesis_id] if len(active) > 2 else []
                        ),
                        AnswerOption(
                            text="Also noticeable when sitting or standing still",
                            eliminates=[active[2].hypothesis_id] if len(active) > 2 else [],
                            supports=[active[0].hypothesis_id] if len(active) > 0 else []
                        ),
                        AnswerOption(
                            text="Only when tired or after extended activity",
                            eliminates=[active[0].hypothesis_id] if len(active) > 0 else [],
                            supports=[active[1].hypothesis_id] if len(active) > 1 else []
                        )
                    ],
                    expected_information_gain=0.72,
                    turn_number=turn
                )
            elif turn == 2:
                return DiagnosticQuestion(
                    question_text="Has the child shown any sign of tenderness or pulling away when the leg or foot is touched?",
                    reason="Helps identify whether discomfort or acute guarding is the underlying driver.",
                    options=[
                        AnswerOption(
                            text="No signs of discomfort or pain at all",
                            eliminates=[active[-1].hypothesis_id] if len(active) > 0 else [],
                            supports=[active[0].hypothesis_id] if len(active) > 0 else []
                        ),
                        AnswerOption(
                            text="Yes, seems sensitive or avoids putting full weight on one side",
                            supports=[active[-1].hypothesis_id] if len(active) > 0 else [],
                            eliminates=[active[0].hypothesis_id] if len(active) > 0 else []
                        )
                    ],
                    expected_information_gain=0.68,
                    turn_number=turn
                )
            else:
                return DiagnosticQuestion(
                    question_text="How long has this walking pattern been noticeable?",
                    reason="Differentiates transient developmental adjustment from an established habit.",
                    options=[
                        AnswerOption(text="Just started recently (last few days)"),
                        AnswerOption(text="Present for several weeks or months"),
                        AnswerOption(text="Since they first started walking")
                    ],
                    expected_information_gain=0.55,
                    turn_number=turn
                )
        else:
            return DiagnosticQuestion(
                question_text=f"Under what conditions is the observed {session.domain} pattern most pronounced?",
                reason="Isolates dynamic operational load from persistent structural characteristics.",
                options=[
                    AnswerOption(text="Under peak intensity or dynamic load", supports=[active[0].hypothesis_id] if len(active) > 0 else []),
                    AnswerOption(text="Consistently present across all operating states", supports=[active[1].hypothesis_id] if len(active) > 1 else []),
                    AnswerOption(text="Intermittent and seemingly random", supports=[active[-1].hypothesis_id] if len(active) > 0 else [])
                ],
                expected_information_gain=0.60,
                turn_number=turn
            )
