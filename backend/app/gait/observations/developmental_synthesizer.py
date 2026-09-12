"""
Developmental Summary Synthesizer
Synthesizes complex biomechanical and temporal gait analytics into a unified,
parent-friendly, non-diagnostic developmental mobility assessment.
"""
from typing import List, Optional
from ..schemas import (
    TemporalMetrics,
    AdvancedTemporalMetrics,
    SymmetryProfile,
    JointMotionProfile,
    PostureMetrics,
    ReferenceMetricItem,
    PillarTakeaway,
    DevelopmentalSummary,
    CadenceRange
)
from ..norms.toddler_norms import get_cadence_range


def _age_label(months: int) -> str:
    years = months // 12
    rem = months % 12
    if years < 1:
        return f"{months}-month-old"
    elif rem == 0:
        return f"{years}-year-old"
    else:
        return f"{years} yr {rem} mo old"


class DevelopmentalSynthesizer:
    """Combines all granular gait domains into 4 easy-to-understand pillars."""

    def synthesize(
        self,
        child_age_months: int,
        metrics: TemporalMetrics,
        adv_temporal: Optional[AdvancedTemporalMetrics],
        symmetry: Optional[SymmetryProfile],
        joint_motion: Optional[JointMotionProfile],
        posture: Optional[PostureMetrics],
        references: Optional[List[ReferenceMetricItem]] = None,
        is_rejected: bool = False
    ) -> DevelopmentalSummary:
        age_label = _age_label(child_age_months)
        cadence_range = get_cadence_range(child_age_months)

        if is_rejected or metrics.usable_step_count < 2:
            return DevelopmentalSummary(
                overall_score=0.0,
                status_badge="REVIEW_RECOMMENDED",
                status_title="Insufficient Clear Strides",
                status_theme="amber",
                summary_headline="Video quality or step count was insufficient for a complete developmental mobility synthesis.",
                pillars=[
                    PillarTakeaway(
                        category="rhythm",
                        title="Step Rhythm & Cadence",
                        headline="Not enough continuous steps detected",
                        explanation="Record a clear 10-15s side-angle clip of walking across an open room.",
                        score=0.0,
                        status="mild_variation",
                        badge="🟡 Re-test",
                        icon="activity"
                    )
                ],
                milestone_context=f"At {age_label}, children typically walk with steady rhythm across 8-10 consecutive strides.",
                parent_tips=[
                    "Ensure the toddler is walking naturally without holding hands.",
                    "Record at knee-level height in good room lighting."
                ],
                pediatrician_discussion_point="Re-record video with uninterrupted walking passes to enable complete automated gait screening.",
                disclaimer="Observational video screening. Not a formal clinical diagnosis."
            )

        # ------------------------------------------------------------------
        # Pillar 1: Rhythm & Cadence (25% weight)
        # ------------------------------------------------------------------
        cadence = metrics.cadence
        cov = metrics.step_time_cov
        cad_low = cadence_range.low
        cad_high = cadence_range.high

        # Score computation
        r_score = 100.0
        # Cadence deviation penalty
        if cad_low <= cadence <= cad_high:
            cad_status = "typical"
            cad_desc = f"Steps are well-paced ({cadence:.0f} steps/min), matching the expected {cad_low:.0f}–{cad_high:.0f} steps/min range."
        elif cadence < cad_low:
            diff = cad_low - cadence
            penalty = min(30.0, (diff / cad_low) * 40.0)
            r_score -= penalty
            cad_status = "mild_variation" if diff < 20 else "review_recommended"
            cad_desc = f"Takes deliberate, slightly slower steps ({cadence:.0f} steps/min) compared to the typical {cad_low:.0f}–{cad_high:.0f} range."
        else:
            diff = cadence - cad_high
            penalty = min(20.0, (diff / cad_high) * 30.0)
            r_score -= penalty
            cad_status = "mild_variation"
            cad_desc = f"Takes quick, enthusiastic steps ({cadence:.0f} steps/min), common in playful toddlers."

        # CoV variability penalty
        if cov > 25.0:
            r_score -= min(25.0, (cov - 25.0) * 1.5)
            r_status = "review_recommended"
            var_desc = "Step tempo has notable variation between steps."
        elif cov > 15.0:
            r_score -= (cov - 15.0) * 1.0
            r_status = "mild_variation"
            var_desc = "Slight natural rhythm variation, very common as balance stabilizes."
        else:
            r_status = "typical"
            var_desc = "Rhythm is consistent and smooth from step to step."

        r_score = max(30.0, min(100.0, r_score))
        r_badge = "🟢 Typical" if r_score >= 80 else ("🟡 Developing" if r_score >= 65 else "🔴 Review")
        
        pillar_rhythm = PillarTakeaway(
            category="rhythm",
            title="Step Rhythm & Tempo",
            headline="Steady walking cadence and timing" if r_score >= 80 else "Developing stride rhythm",
            explanation=f"{cad_desc} {var_desc}",
            score=round(r_score, 1),
            status=r_status,
            badge=r_badge,
            icon="activity"
        )

        # ------------------------------------------------------------------
        # Pillar 2: Balance & Bilateral Symmetry (30% weight)
        # ------------------------------------------------------------------
        asym = metrics.step_time_asymmetry_pct
        knee_asym = (symmetry.knee_rom_asymmetry_pct if symmetry and symmetry.knee_rom_asymmetry_pct is not None else 0.0)
        
        s_score = 100.0
        if asym <= 10.0:
            s_score -= asym * 0.8
            sym_desc = f"Weight and timing are shared evenly between left and right legs ({asym:.0f}% variance)."
            s_status = "typical"
        elif asym <= 18.0:
            s_score -= 10.0 + (asym - 10.0) * 2.2
            sym_desc = f"Mild timing preference on one side ({asym:.0f}% variance), typical during active growth phases."
            s_status = "mild_variation"
        else:
            s_score -= 28.0 + (asym - 18.0) * 2.5
            sym_desc = f"Noticeable timing difference ({asym:.0f}% variance) between the left and right steps."
            s_status = "review_recommended"

        if knee_asym > 15.0:
            s_score -= min(15.0, (knee_asym - 15.0) * 0.8)

        s_score = max(25.0, min(100.0, s_score))
        s_badge = "🟢 Symmetrical" if s_score >= 80 else ("🟡 Mild Asymmetry" if s_score >= 65 else "🔴 Asymmetrical")

        pillar_symmetry = PillarTakeaway(
            category="symmetry",
            title="Left & Right Balance",
            headline="Even weight distribution on both legs" if s_score >= 80 else "Mild one-sided favoring observed",
            explanation=sym_desc,
            score=round(s_score, 1),
            status=s_status,
            badge=s_badge,
            icon="scale"
        )

        # ------------------------------------------------------------------
        # Pillar 3: Leg Movement & Flexibility (25% weight)
        # ------------------------------------------------------------------
        m_score = 90.0
        m_status = "typical"
        m_desc = "Knees and hips show active flexion and push-off through each stride."

        if joint_motion:
            lk_rom = joint_motion.left_knee.rom_deg
            rk_rom = joint_motion.right_knee.rom_deg
            avg_knee_rom = None
            if lk_rom is not None and rk_rom is not None:
                avg_knee_rom = (lk_rom + rk_rom) / 2.0
            elif lk_rom is not None:
                avg_knee_rom = lk_rom
            elif rk_rom is not None:
                avg_knee_rom = rk_rom

            if avg_knee_rom is not None:
                if avg_knee_rom >= 80.0:
                    m_score = min(100.0, 90.0 + (avg_knee_rom - 80.0) * 0.3)
                    m_desc = f"Healthy knee bending motion ({avg_knee_rom:.0f}° arc) allowing smooth foot clearance."
                elif avg_knee_rom >= 60.0:
                    m_score = 75.0 + (avg_knee_rom - 60.0) * 0.7
                    m_status = "mild_variation"
                    m_desc = f"Moderate knee flexion ({avg_knee_rom:.0f}° arc), typical for cautious walkers."
                else:
                    m_score = max(40.0, avg_knee_rom)
                    m_status = "review_recommended"
                    m_desc = f"Shallow knee flexion ({avg_knee_rom:.0f}° arc); steps may be stiff-legged."

        m_score = max(30.0, min(100.0, m_score))
        m_badge = "🟢 Fluid" if m_score >= 80 else ("🟡 Moderate" if m_score >= 65 else "🔴 Restricted")

        pillar_mobility = PillarTakeaway(
            category="joint_mobility",
            title="Joint Flexibility & Motion",
            headline="Fluid leg motion & foot clearance" if m_score >= 80 else "Developing joint range",
            explanation=m_desc,
            score=round(m_score, 1),
            status=m_status,
            badge=m_badge,
            icon="layers"
        )

        # ------------------------------------------------------------------
        # Pillar 4: Postural Stability & Alignment (20% weight)
        # ------------------------------------------------------------------
        p_score = 92.0
        p_status = "typical"
        p_desc = "Upright upper body alignment with stable trunk control."

        if posture and posture.trunk_angle_deg is not None:
            t_ang = posture.trunk_angle_deg
            sway = posture.lateral_sway if posture.lateral_sway is not None else 0.0

            if t_ang <= 10.0:
                p_score = 95.0
                p_desc = f"Good upright posture ({t_ang:.1f}° inclination from vertical) with centered balance."
            elif t_ang <= 18.0:
                p_score = 80.0 - (t_ang - 10.0) * 1.5
                p_status = "mild_variation"
                p_desc = f"Slight forward lean ({t_ang:.1f}°), common when toddlers accelerate forward enthusiastically."
            else:
                p_score = max(45.0, 70.0 - (t_ang - 18.0) * 2.0)
                p_status = "review_recommended"
                p_desc = f"Noticeable forward trunk lean ({t_ang:.1f}°), suggesting compensatory balance adjustment."

            if sway > 0.15:
                p_score -= 10.0

        p_score = max(35.0, min(100.0, p_score))
        p_badge = "🟢 Upright" if p_score >= 80 else ("🟡 Mild Lean" if p_score >= 65 else "🔴 Check Alignment")

        pillar_posture = PillarTakeaway(
            category="posture",
            title="Postural Alignment",
            headline="Upright trunk balance" if p_score >= 80 else "Forward leaning balance",
            explanation=p_desc,
            score=round(p_score, 1),
            status=p_status,
            badge=p_badge,
            icon="compass"
        )

        pillars = [pillar_rhythm, pillar_symmetry, pillar_mobility, pillar_posture]

        # ------------------------------------------------------------------
        # Overall Composite Score
        # ------------------------------------------------------------------
        overall = (
            0.25 * r_score +
            0.30 * s_score +
            0.25 * m_score +
            0.20 * p_score
        )
        overall = round(overall, 1)

        # Status Profile Title
        if overall >= 84.0 and all(p.status != "review_recommended" for p in pillars):
            status_badge = "WITHIN_REFERENCE"
            status_title = "Within Selected Reference"
            status_theme = "green"
            headline = f"Observed walking pattern is consistent with published reference parameters for a {age_label}."
            ped_point = f"Screening indicates walking parameters generally align with published reference ranges for {age_label} (Screening Score: {overall:.0f}/100)."
        elif overall >= 68.0:
            status_badge = "MILD_VARIATION"
            status_title = "Mild Variation Observed"
            status_theme = "amber"
            headline = f"Observed walking displays mild timing or motion variations commonly seen during {age_label} developmental phases."
            ped_point = f"Screening observed mild stride variation or timing asymmetry (Screening Score: {overall:.0f}/100). Re-screening in 3–4 weeks suggested to track maturation."
        else:
            status_badge = "OUTSIDE_REFERENCE"
            status_title = "Outside Selected Reference"
            status_theme = "red"
            headline = f"Observed walking parameters show noticeable deviation from typical reference ranges across recorded strides."
            ped_point = f"Screening identified notable asymmetry or movement variation (Screening Score: {overall:.0f}/100). Consider discussing with a clinician during routine review."

        # Parent Tips tailored to toddler age
        parent_tips = [
            "Encourage safe barefoot walking on varied surfaces (carpet, grass, smooth foam) to stimulate foot proprioception.",
            "Choose flexible-soled shoes that bend easily at the ball of the foot when walking outdoors.",
            f"At {age_label}, active daily free play (climbing, walking over low obstacles) strengthens core and hip stabilizers."
        ]

        milestone_info = (
            f"According to published pediatric gait development literature (Sutherland et al.), children at {age_label} "
            f"typically demonstrate higher cadence (~{cad_low:.0f}–{cad_high:.0f} spm) and variable stride intervals "
            f"as dynamic postural equilibrium matures toward adult patterns by age 4–5."
        )

        return DevelopmentalSummary(
            overall_score=overall,
            status_badge=status_badge,
            status_title=status_title,
            status_theme=status_theme,
            summary_headline=headline,
            pillars=pillars,
            milestone_context=milestone_info,
            parent_tips=parent_tips,
            pediatrician_discussion_point=ped_point,
            disclaimer="Automated observational video screening tool. Prototype composite score; not clinically validated. Results describe the observed walking segment and should not be interpreted as a medical diagnosis."
        )

