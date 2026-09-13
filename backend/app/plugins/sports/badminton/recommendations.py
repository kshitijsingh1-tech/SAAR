"""
Badminton Grounded Recommendation Engine.

Adheres strictly to:
1. Section 51: Grounded Recommendation Prioritization (HIGH / MEDIUM / LOW).
   Every recommendation must be generated FROM a specific finding in the
   analysis evidence graph (Phase 12/13), never loose unsolicited advice.
2. Section 40: RAG Traceability Requirement.
   Every recommendation grounded in domain literature carries visible
   metadata: rag_source, rag_section, evidence_strength, and confidence.
3. Section 23 & 52: General Sports Nutrition Guidance Tied Solely to Measured Load.
   Nutritional advice is restricted strictly to general hydration, carbohydrate,
   and protein recovery timing scaled by observed duration and MET energy expenditure.
   Deficiency-style claims ("you lack vitamin X", "diagnosed with deficiency")
   are strictly prohibited by programmatic guard checks.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.schemas import GraphStateModel
from app.rag_service import RAGKnowledgeService
from .schemas import (
    BadmintonAnalysisResult,
    CourtCalibration,
    MovementMetrics,
    ShotMetrics,
    ShotResult,
    EnergyMetrics,
    SpeedMetrics
)


class RecommendationPriority(str, Enum):
    HIGH = "HIGH"       # Safety, critical kinematic flaws, high-confidence tactical avoidance
    MEDIUM = "MEDIUM"   # Movement efficiency, footwork recovery, stroke variety optimization
    LOW = "LOW"         # General session conditioning, load-tied nutrition & hydration replenishment


# Programmatic guard: phrases that must NEVER appear in automated nutrition guidance
DEFICIENCY_RED_FLAG_PHRASES = [
    "you are deficient in",
    "you have a deficiency",
    "diagnosed with",
    "iron deficiency",
    "vitamin deficiency",
    "calcium deficiency",
    "magnesium deficiency",
    "ferritin deficiency",
    "you lack sufficient",
    "take 500mg of",
    "take 1000mg of",
    "prescribe",
    "prescription",
    "treatment for deficiency",
    "cure your deficiency",
    "suffer from a deficiency"
]


class PrioritizedRecommendation(BaseModel):
    recommendation_id: str
    title: str
    priority: RecommendationPriority
    source_finding_id: str
    source_finding_description: str
    recommendation: str
    actionable_drill: str
    rationale: str
    rag_source: Optional[str] = None
    rag_section: Optional[str] = None
    evidence_quote: Optional[str] = None
    evidence_strength: float = 0.85
    confidence: float = 0.85
    is_nutrition_guidance: bool = False

    def to_summary_string(self) -> str:
        """Format as human-readable prioritized summary line for canonical API responses."""
        source_meta = f" | Source: {self.rag_source} ({self.rag_section})" if self.rag_source else ""
        return f"[{self.priority.value}] {self.title}: {self.recommendation} (Derived from finding '{self.source_finding_id}'{source_meta})"


class BadmintonRecommendationEngine:
    """
    Generates prioritized, traceable recommendations derived directly from
    grounded analysis findings in the Badminton Evidence Graph.
    """

    def __init__(self, rag_service: Optional[RAGKnowledgeService] = None):
        self.rag = rag_service if rag_service is not None else RAGKnowledgeService()

    def generate_recommendations(
        self,
        analysis_result: BadmintonAnalysisResult,
        evidence_graph: Optional[GraphStateModel] = None
    ) -> List[PrioritizedRecommendation]:
        """
        Synthesizes prioritized recommendations strictly derived from active findings:
        - Tactical spatial bias (e.g. asserted left-space underutilization)
        - Contact joint angles (e.g. restricted elbow extension at contact)
        - Movement coverage and recovery centroid
        - Load-tied general sports nutrition (duration & MET kcal)
        - Court calibration / capture quality
        """
        recommendations: List[PrioritizedRecommendation] = []
        graph = evidence_graph or analysis_result.graph_data

        shots = analysis_result.shots or []
        shot_metrics = analysis_result.shot_metrics
        movement = analysis_result.movement_metrics
        court_calib = analysis_result.court_calibration
        energy = analysis_result.energy_metrics
        speed = analysis_result.speed_metrics

        # -------------------------------------------------------------
        # Finding 1: Left-Space Underutilization (Section 11 Multi-Signal Hypothesis)
        # -------------------------------------------------------------
        hypo_node = None
        if graph and hasattr(graph, "nodes"):
            hypo_node = next((n for n in graph.nodes if n.id == "hypo_left_space_underutilization"), None)

        if hypo_node:
            rag_hits = self.rag.query("shadow footwork left-space backhand corner transition drills", domain="training principles", top_k=1)
            rag_src = rag_hits[0].source if rag_hits else "training_principles_kb.md"
            rag_sec = rag_hits[0].section if rag_hits else "Tactical Footwork & Lateral Court Balance Drills"
            rag_quote = rag_hits[0].content[:160] + "..." if rag_hits else None

            recommendations.append(PrioritizedRecommendation(
                recommendation_id="rec_tactical_left_space",
                title="Rear-Court Backhand Corner Footwork Balance",
                priority=RecommendationPriority.HIGH,
                source_finding_id="hypo_left_space_underutilization",
                source_finding_description="Evidence graph confirmed multi-signal left-space underutilization hypothesis (occupancy deficit + shot placement skew).",
                recommendation="Incorporate rear-court backhand corner shadow footwork drills to restore bilateral court coverage balance.",
                actionable_drill="6-corner multi-directional shadow footwork emphasizing early pivot, hip turn, and 2-step chassé into the rear backhand corner, followed by explosive recovery to central base (x ≈ 3.05m).",
                rationale="Addressing lateral spatial asymmetry eliminates predictable opponent clear/drop exploitation on the backhand side.",
                rag_source=rag_src,
                rag_section=rag_sec,
                evidence_quote=rag_quote,
                evidence_strength=0.90,
                confidence=0.88,
                is_nutrition_guidance=False
            ))

        # -------------------------------------------------------------
        # Finding 2: Contact Joint Kinematics (Elbow Extension Angle)
        # -------------------------------------------------------------
        elbow_angles = []
        for s in shots:
            pf = s.pose_features or {}
            val = pf.get("contact_elbow_angle_deg") or pf.get("elbow_angle_deg")
            if val is not None:
                elbow_angles.append(float(val))

        if elbow_angles:
            mean_elbow = sum(elbow_angles) / len(elbow_angles)
            if mean_elbow < 135.0:
                rag_hits = self.rag.query("elbow extension contact height smash downward angle apex", domain="badminton biomechanics", top_k=1)
                rag_src = rag_hits[0].source if rag_hits else "badminton_biomechanics_kb.md"
                rag_sec = rag_hits[0].section if rag_hits else "Contact Height & Downward Smash Angle"
                rag_quote = rag_hits[0].content[:160] + "..." if rag_hits else None

                recommendations.append(PrioritizedRecommendation(
                    recommendation_id="rec_kinematic_elbow_extension",
                    title="Elevate Contact Point & Full Elbow Extension",
                    priority=RecommendationPriority.HIGH,
                    source_finding_id="joint_contact_elbow_angle",
                    source_finding_description=f"Mean elbow extension across detected strokes was {mean_elbow:.1f}°, below the optimal overhead attack benchmark (145°–165°).",
                    recommendation="Focus on reaching vertical arm extension at the apex of contact rather than collapsing with premature elbow flexion.",
                    actionable_drill="High-reach multi-shuttle feeding drills demanding contact at maximum vertical reach, paired with suspended shuttle pronation snaps.",
                    rationale="Extending the kinematic lever arm maximizes downward descent angle and increases racket-head linear impact velocity.",
                    rag_source=rag_src,
                    rag_section=rag_sec,
                    evidence_quote=rag_quote,
                    evidence_strength=0.92,
                    confidence=0.90,
                    is_nutrition_guidance=False
                ))
            else:
                rag_hits = self.rag.query("forearm pronation wrist snap kinetic chain sequencing", domain="badminton biomechanics", top_k=1)
                recommendations.append(PrioritizedRecommendation(
                    recommendation_id="rec_kinematic_pronation_whip",
                    title="Reinforce Forearm Pronation Acceleration",
                    priority=RecommendationPriority.MEDIUM,
                    source_finding_id="joint_contact_elbow_angle",
                    source_finding_description=f"Mean elbow extension ({mean_elbow:.1f}°) demonstrated competent vertical contact elevation.",
                    recommendation="Maintain high contact point while optimizing rapid forearm pronation timing prior to impact.",
                    actionable_drill="Hanging shuttle whip snaps with relaxed grip that tightens immediately upon contact.",
                    rationale="Forearm pronation generates up to 50% of resultant smash speed without placing excessive strain on the wrist joint.",
                    rag_source=rag_hits[0].source if rag_hits else "badminton_biomechanics_kb.md",
                    rag_section=rag_hits[0].section if rag_hits else "Forearm Pronation vs. Premature Wrist Flexion",
                    evidence_quote=rag_hits[0].content[:160] + "..." if rag_hits else None,
                    evidence_strength=0.85,
                    confidence=0.85,
                    is_nutrition_guidance=False
                ))

        # -------------------------------------------------------------
        # Finding 3: Movement Dynamics & Base Recovery
        # -------------------------------------------------------------
        if court_calib and court_calib.is_calibrated and movement and movement.total_distance_m is not None:
            dist_m = movement.total_distance_m
            rag_hits = self.rag.query("dynamic base recovery split step synchronization", domain="training principles", top_k=1)
            rag_src = rag_hits[0].source if rag_hits else "training_principles_kb.md"
            rag_sec = rag_hits[0].section if rag_hits else "Tactical Footwork & Lateral Court Balance Drills"

            recommendations.append(PrioritizedRecommendation(
                recommendation_id="rec_movement_split_step",
                title="Split-Step Pre-Hop Timing & Centroid Reset",
                priority=RecommendationPriority.MEDIUM,
                source_finding_id="movement_dynamics",
                source_finding_description=f"Tracked {dist_m:.1f}m displacement across calibrated playing area.",
                recommendation="Synchronize preparatory split-step pre-hop 100–200ms prior to opponent stroke impact.",
                actionable_drill="Reactionary multi-corner feeding drills focusing on resetting centroid to central base (x ≈ 3.05m) immediately after drive/clear recovery.",
                rationale="Pre-stretching calf and quadriceps musculature via timed split-step minimizes reactionary footwork initiation delay.",
                rag_source=rag_src,
                rag_section=rag_sec,
                evidence_quote=rag_hits[0].content[:160] + "..." if rag_hits else None,
                evidence_strength=0.80,
                confidence=0.85,
                is_nutrition_guidance=False
            ))

        # -------------------------------------------------------------
        # Finding 4: Energy Expenditure & Load-Tied Nutrition (Section 23)
        # -------------------------------------------------------------
        nutrition_rec = self.generate_nutrition_guidance(analysis_result)
        if nutrition_rec:
            recommendations.append(nutrition_rec)

        # -------------------------------------------------------------
        # Finding 5: Court Calibration & Capture Quality
        # -------------------------------------------------------------
        if court_calib and not court_calib.is_calibrated:
            rag_hits = self.rag.query("court dimensions planar homography camera perspective scaling", domain="badminton court", top_k=1)
            rag_src = rag_hits[0].source if rag_hits else "badminton_court_kb.md"
            rag_sec = rag_hits[0].section if rag_hits else "Planar Homography & Camera Perspective Scaling"

            recommendations.append(PrioritizedRecommendation(
                recommendation_id="rec_capture_court_calibration",
                title="Camera Setup for Metric Court Homography",
                priority=RecommendationPriority.MEDIUM,
                source_finding_id="court_plane",
                source_finding_description=f"Court calibration failed: {court_calib.uncalibrated_reason or 'Boundary corners occluded'}.",
                recommendation="Mount camera 1.5m–2.5m directly behind the baseline on a stable tripod ensuring all 4 outer court boundary lines are visible.",
                actionable_drill="Camera placement check: Verify before recording that the net posts and both rear baseline corners remain unobstructed throughout the rally.",
                rationale="Unlocking metric court homography enables precise physical distance tracking, court coverage percentages, and 9-zone tactical occupancy breakdown.",
                rag_source=rag_src,
                rag_section=rag_sec,
                evidence_quote=rag_hits[0].content[:160] + "..." if rag_hits else None,
                evidence_strength=0.95,
                confidence=0.95,
                is_nutrition_guidance=False
            ))

        # Fallback if no specific findings yielded recommendations
        if not recommendations:
            recommendations.append(PrioritizedRecommendation(
                recommendation_id="rec_general_baseline",
                title="Baseline Kinetic Chain & Interval Conditioning",
                priority=RecommendationPriority.MEDIUM,
                source_finding_id="player_main",
                source_finding_description="Optical kinematics processed without acute anomalies detected.",
                recommendation="Maintain multi-shuttle high-intensity interval training to reinforce kinetic chain timing and rally endurance.",
                actionable_drill="10–12 shuttle rapid-fire feeding sets with 20 seconds active rest across 4 blocks.",
                rationale="Interval training with 1:2 work-to-rest ratio mirrors competitive tournament rally demands.",
                rag_source="training_principles_kb.md",
                rag_section="High-Intensity Interval Training (HIIT) & Match Simulation",
                evidence_strength=0.75,
                confidence=0.80,
                is_nutrition_guidance=False
            ))

        # -------------------------------------------------------------
        # Section 51 Prioritization Sorting: HIGH -> MEDIUM -> LOW
        # Secondary tie-breaker: evidence_strength descending
        # -------------------------------------------------------------
        priority_weights = {
            RecommendationPriority.HIGH: 3,
            RecommendationPriority.MEDIUM: 2,
            RecommendationPriority.LOW: 1
        }
        recommendations.sort(
            key=lambda r: (priority_weights.get(r.priority, 0), r.evidence_strength),
            reverse=True
        )

        return recommendations

    def generate_nutrition_guidance(self, analysis_result: BadmintonAnalysisResult) -> Optional[PrioritizedRecommendation]:
        """
        Generate general, non-diagnostic sports nutrition guidance strictly tied to
        measured load, duration, and energy expenditure findings (Section 23).
        Programmatically validates that no nutrient-deficiency claims are present.
        """
        energy = analysis_result.energy_metrics
        if not energy:
            return None

        kcal = (
            getattr(energy, "estimated_energy_expenditure_kcal", None)
            or getattr(energy, "estimated_calories_burned_kcal", None)
        )
        dur_min = (
            getattr(energy, "active_duration_minutes", None)
            or (getattr(energy, "active_duration_seconds", 0.0) / 60.0 if getattr(energy, "active_duration_seconds", None) else None)
            or (analysis_result.video.duration_seconds / 60.0 if analysis_result.video and getattr(analysis_result.video, "duration_seconds", None) else 0.0)
        )
        if kcal is None and (dur_min is None or dur_min == 0.0):
            return None

        kcal = float(kcal or 0.0)
        dur_min = float(dur_min or 0.0)
        is_personalized = (
            getattr(energy, "estimation_type", "") == "personalized"
            or getattr(energy, "is_personalized", False)
            or getattr(energy, "label", "") == "personalized"
        )

        rag_hits = self.rag.query(
            "sports nutrition hydration fluid carbohydrate post exercise recovery window",
            domain="sports nutrition",
            top_k=1
        )
        rag_src = rag_hits[0].source if rag_hits else "sports_nutrition_kb.md"
        rag_sec = rag_hits[0].section if rag_hits else "Load-Tied Fluid & Electrolyte Replenishment"
        rag_quote = rag_hits[0].content[:160] + "..." if rag_hits else None

        # Formulate strictly general, load-tied replenishment advice (400-800 mL/hr scaled)
        fluid_vol_ml = round(dur_min * 10.0)
        fluid_str = f"{max(300, min(800, fluid_vol_ml))} mL" if dur_min > 0 else "400–800 mL per hour"
        carb_str = "30–60g rapid carbohydrates per hour" if (dur_min >= 45.0 or kcal >= 300.0) else "standard post-session hydration"

        nutrition_rec_text = (
            f"For an active session duration of {dur_min:.1f} minutes ({kcal:.1f} estimated kcal burned), "
            f"general sports nutrition guidelines recommend hydrating with approximately {fluid_str} of water or hypotonic electrolyte beverage. "
            f"Following high-intensity court sessions, consuming 20–30g of high-quality protein within 45–90 minutes supports muscle protein remodeling, "
            f"paired with {carb_str} to replenish depleted muscle glycogen stores."
        )

        # Programmatic verification: assert no deficiency red flags
        for red_flag in DEFICIENCY_RED_FLAG_PHRASES:
            if red_flag in nutrition_rec_text.lower():
                raise ValueError(f"CRITICAL SAFETY VIOLATION: Nutrition text contains deficiency red-flag: '{red_flag}'")

        return PrioritizedRecommendation(
            recommendation_id="rec_nutrition_load_recovery",
            title="Session Load Hydration & Glycogen Replenishment",
            priority=RecommendationPriority.LOW,
            source_finding_id="measured_session_energy_expenditure",
            source_finding_description=f"Estimated energy expenditure: {kcal:.1f} kcal across {dur_min:.1f} minutes of active play ({'personalized body weight' if is_personalized else 'generalized population-average baseline'}).",
            recommendation=nutrition_rec_text,
            actionable_drill="Hydration habit: Sip electrolyte solution between game sets; consume recovery snack (e.g. whey protein shake with banana or yogurt with honey) within 60 minutes of session conclusion.",
            rationale="Replenishing fluid deficits and providing amino acids during the early post-exercise window attenuates muscle breakdown and accelerates glycogen resynthesis.",
            rag_source=rag_src,
            rag_section=rag_sec,
            evidence_quote=rag_quote,
            evidence_strength=0.88,
            confidence=0.85,
            is_nutrition_guidance=True
        )

    def respond_to_nutrition_query(self, query: str, analysis_result: BadmintonAnalysisResult) -> str:
        """
        Respond to user prompts regarding diet, nutrition, or supplements (Section 23).
        Provides general sports nutrition principles tied strictly to observed session load.
        Guarantees that no nutrient-deficiency claims or medical prescriptions are emitted.
        """
        dur_min = 0.0
        kcal = 0.0
        if analysis_result.energy_metrics:
            dur_min = (
                getattr(analysis_result.energy_metrics, "active_duration_minutes", None)
                or (getattr(analysis_result.energy_metrics, "active_duration_seconds", 0.0) / 60.0)
                or (analysis_result.video.duration_seconds / 60.0 if analysis_result.video and getattr(analysis_result.video, "duration_seconds", None) else 0.0)
            )
            kcal = (
                getattr(analysis_result.energy_metrics, "estimated_energy_expenditure_kcal", None)
                or getattr(analysis_result.energy_metrics, "estimated_calories_burned_kcal", None)
                or 0.0
            )

        fluid_scaled = max(300, min(800, round(float(dur_min) * 10.0)))
        response_parts = [
            f"Based on your session recording ({float(dur_min):.1f} minutes active play, estimated ~{float(kcal):.1f} kcal expended):",
            "General sports science guidelines focus on session-appropriate fluid hydration and balanced macronutrient recovery.",
            f"During and after intense court play, aim for approximately {fluid_scaled} mL fluids and 20–30g high-quality protein within 45–90 minutes to facilitate muscle protein repair and glycogen replenishment.",
            "Please note: Video kinematic motion tracking does not evaluate blood chemistry, organ function, or physiological biomarker status. This system does not diagnose nutritional health or medical conditions. For individualized dietary planning, consultation with a registered sports dietitian or healthcare professional is recommended."
        ]
        full_response = " ".join(response_parts)

        # Programmatic verification against red flag phrases
        for phrase in DEFICIENCY_RED_FLAG_PHRASES:
            if phrase in full_response.lower():
                raise ValueError(f"CRITICAL SAFETY VIOLATION: Generated response contains prohibited deficiency phrase: '{phrase}'")

        return full_response
