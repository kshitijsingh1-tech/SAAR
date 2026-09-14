"""
SAAR — Adaptive Diagnostic Inquiry Engine (Evidence-Driven Active Questioning)

Core Principles:
1. Dynamic Selection over Hardcoded Trees: Questions are selected based on
   Information Gain × Relevance × Uncertainty, dynamically adapting to each user response.
2. Structured Case State: Continuously updates observations, user answers, uncertainties, and confidence.
3. Proof-of-Adaptation: Demonstrates different next questions for different user answers
   (Case A: Acute Onset -> Injury inquiry vs Case B: Chronic Habit -> Gross motor milestone inquiry).
4. Personalized Baseline Aware: Grounded in deviations from the child's own personal baseline.
"""
import json
import re
import uuid
from typing import Dict, List, Any, Optional

from ..models.saar_models import (
    Hypothesis, AnswerOption, DiagnosticQuestion, AdaptiveSession, CaseState
)
from ..vlm_service import VLMService
from ..rag_service import RAGKnowledgeService
from ..gait.baseline_service import personalized_baseline_service, _safe_float


# ---------------------------------------------------------------------------
# Domain Question Banks with Dynamic Relevance & Target Uncertainties
# ---------------------------------------------------------------------------

GAIT_QUESTION_BANK = [
    {
        "question_id": "gait_recent_change",
        "question_text": "Is this a recent change in your child's walking?",
        "reason": "Distinguishes between an acute onset (injury or muscle strain) and a long-standing developmental pattern.",
        "target_uncertainty": "possible recent change",
        "info_gain": 0.85,
        "relevance_fn": lambda state: 0.98 if "recent_change" not in state.user_answers else 0.0,
        "options": [
            {
                "text": "Yes, noticed it recently (last few days to 2 weeks)",
                "updates": {"recent_change": True},
                "supports": ["acute_injury_or_strain"],
                "eliminates": ["developmental_variation"],
                "reasoning_tag": "acute_onset"
            },
            {
                "text": "No, they have always walked this way since early walking",
                "updates": {"recent_change": False},
                "supports": ["developmental_variation", "structural_asymmetry"],
                "eliminates": ["acute_injury_or_strain"],
                "reasoning_tag": "habitual_developmental"
            },
            {
                "text": "Unsure / Just noticed it for the first time today",
                "updates": {"recent_change": "unsure"},
                "supports": [],
                "eliminates": [],
                "reasoning_tag": "unverified_timeline"
            }
        ]
    },
    {
        "question_id": "gait_recent_injury",
        "question_text": "Has your child recently had a fall, bump, or leg injury?",
        "reason": "Identifies recent physical trauma or localized strain as the immediate cause of antalgic guarding.",
        "target_uncertainty": "possible injury",
        "info_gain": 0.88,
        "relevance_fn": lambda state: (
            0.95 if state.user_answers.get("recent_change") is True
            else (0.02 if state.user_answers.get("recent_change") is False else 0.40)
        ),
        "options": [
            {
                "text": "Yes, had a fall, jump from height, or leg bump",
                "updates": {"recent_injury": True},
                "supports": ["acute_injury_or_strain"],
                "eliminates": ["structural_asymmetry"],
                "reasoning_tag": "trauma_confirmed"
            },
            {
                "text": "No known injury, fall, or bump",
                "updates": {"recent_injury": False},
                "supports": ["developmental_variation", "structural_asymmetry"],
                "eliminates": ["acute_injury_or_strain"],
                "reasoning_tag": "trauma_denied"
            },
            {
                "text": "Unsure (e.g. at daycare or playing with siblings)",
                "updates": {"recent_injury": "possible"},
                "supports": ["acute_injury_or_strain"],
                "eliminates": [],
                "reasoning_tag": "unobserved_play"
            }
        ]
    },
    {
        "question_id": "gait_pain_or_guarding",
        "question_text": "Does your child complain of pain, limp, or avoid putting full weight on one leg?",
        "reason": "Confirms antalgic protection where the child cuts short step duration to avoid discomfort.",
        "target_uncertainty": "pain status",
        "info_gain": 0.80,
        "relevance_fn": lambda state: (
            0.90 if state.user_answers.get("recent_injury") is True
            else (0.75 if state.user_answers.get("recent_change") is True else 0.35)
        ),
        "options": [
            {
                "text": "Yes, winces, points to leg/foot, or avoids weight",
                "updates": {"pain_guarding": True},
                "supports": ["acute_injury_or_strain"],
                "eliminates": ["developmental_variation"],
                "reasoning_tag": "antalgic_confirmed"
            },
            {
                "text": "No signs of pain, tenderness, or guarding at all",
                "updates": {"pain_guarding": False},
                "supports": ["developmental_variation"],
                "eliminates": ["acute_injury_or_strain"],
                "reasoning_tag": "painless_pattern"
            }
        ]
    },
    {
        "question_id": "gait_running_or_stairs",
        "question_text": "Does your child have difficulty running, jumping, or climbing stairs compared to peers?",
        "reason": "Evaluates whether gross motor milestones are functionally limited or on-track for developmental age.",
        "target_uncertainty": "functional impact",
        "info_gain": 0.82,
        "relevance_fn": lambda state: (
            0.92 if state.user_answers.get("recent_change") is False
            else (0.25 if state.user_answers.get("recent_change") is True else 0.60)
        ),
        "options": [
            {
                "text": "Runs, jumps, and climbs stairs normally with good energy",
                "updates": {"gross_motor_delay": False},
                "supports": ["developmental_variation"],
                "eliminates": ["structural_asymmetry"],
                "reasoning_tag": "milestones_intact"
            },
            {
                "text": "Trips frequently or has noticeable difficulty with stairs/running",
                "updates": {"gross_motor_delay": True},
                "supports": ["structural_asymmetry"],
                "eliminates": [],
                "reasoning_tag": "milestone_deficit"
            }
        ]
    },
    {
        "question_id": "gait_consistent_or_fatigue",
        "question_text": "Does the asymmetry appear all the time, or mainly when your child gets tired?",
        "reason": "Distinguishes dynamic neuromuscular fatigue from persistent structural alignment asymmetry.",
        "target_uncertainty": "fatigue vs structural",
        "info_gain": 0.65,
        "relevance_fn": lambda state: 0.65 if "consistent_or_fatigue" not in state.user_answers else 0.0,
        "options": [
            {
                "text": "Present consistently in every step throughout the day",
                "updates": {"fatigue_dependent": False},
                "supports": ["structural_asymmetry"],
                "eliminates": [],
                "reasoning_tag": "continuous_asymmetry"
            },
            {
                "text": "Only noticeable when tired or late in the afternoon",
                "updates": {"fatigue_dependent": True},
                "supports": ["developmental_variation"],
                "eliminates": ["structural_asymmetry"],
                "reasoning_tag": "fatigue_phenomenon"
            }
        ]
    },
    {
        "question_id": "gait_footwear_check",
        "question_text": "Does the uneven step still occur when your child walks completely barefoot on flat flooring?",
        "reason": "Eliminates footwear artifacts such as tight shoes, uneven sole wear, or foreign objects.",
        "target_uncertainty": "footwear artifact",
        "info_gain": 0.55,
        "relevance_fn": lambda state: 0.50 if "footwear_check" not in state.user_answers else 0.0,
        "options": [
            {
                "text": "Yes, still happens when barefoot on flat carpet or floor",
                "updates": {"footwear_artifact": False},
                "supports": ["developmental_variation", "acute_injury_or_strain", "structural_asymmetry"],
                "eliminates": [],
                "reasoning_tag": "true_biomechanical"
            },
            {
                "text": "Only noticeable in specific shoes or boots",
                "updates": {"footwear_artifact": True},
                "supports": ["developmental_variation"],
                "eliminates": ["structural_asymmetry", "acute_injury_or_strain"],
                "reasoning_tag": "footwear_driven"
            }
        ]
    },
    {
        "question_id": "gait_shoe_wear_pattern",
        "question_text": "Looking at the soles of your child's favorite everyday shoes, do you notice uneven tread wear?",
        "reason": "Uneven medial vs. lateral shoe sole wear provides objective physical evidence of persistent overpronation, foot drop, or structural asymmetry.",
        "target_uncertainty": "structural alignment",
        "info_gain": 0.72,
        "relevance_fn": lambda state: (
            0.85 if (state.user_answers.get("recent_change") is False and state.user_answers.get("gross_motor_delay") is True)
            else (0.45 if state.user_answers.get("recent_change") is False else 0.02)
        ),
        "options": [
            {
                "text": "Noticeably more wear on the inside or outside edge of one shoe",
                "updates": {"uneven_shoe_wear": True},
                "supports": ["structural_asymmetry"],
                "eliminates": ["developmental_variation"],
                "reasoning_tag": "asymmetric_tread_erosion"
            },
            {
                "text": "Both shoe soles wear down evenly and symmetrically",
                "updates": {"uneven_shoe_wear": False},
                "supports": ["developmental_variation"],
                "eliminates": ["structural_asymmetry"],
                "reasoning_tag": "symmetric_tread_wear"
            },
            {
                "text": "Unworn / haven't worn shoes long enough to notice wear",
                "updates": {"uneven_shoe_wear": "inconclusive"},
                "supports": [],
                "eliminates": [],
                "reasoning_tag": "tread_wear_inconclusive"
            }
        ]
    },
    {
        "question_id": "gait_toe_walking_pattern",
        "question_text": "Does your child walk up on their tiptoes, and can they stand completely flat on their heels when asked?",
        "reason": "Differentiates habitual idiopathic toe-walking (child can stand flat on command) from gastrocnemius-soleus contracture or hypertonia (cannot achieve heel strike).",
        "target_uncertainty": "neuromuscular tone",
        "info_gain": 0.78,
        "relevance_fn": lambda state: (
            0.80 if state.user_answers.get("recent_change") is False
            else 0.05
        ),
        "options": [
            {
                "text": "Walks on tiptoes frequently, but easily stands flat on heels with feet flat on the floor",
                "updates": {"toe_walking": "habitual_flexible"},
                "supports": ["developmental_variation"],
                "eliminates": ["structural_asymmetry"],
                "reasoning_tag": "idiopathic_flexible_toe_walking"
            },
            {
                "text": "Always walks on tiptoes and struggles or resists putting heels completely flat",
                "updates": {"toe_walking": "fixed_tightness"},
                "supports": ["structural_asymmetry"],
                "eliminates": ["developmental_variation"],
                "reasoning_tag": "achilles_contracture_indicator"
            },
            {
                "text": "Never walks on toes; always steps heel-to-toe or with a flat foot",
                "updates": {"toe_walking": "absent"},
                "supports": ["developmental_variation", "acute_injury_or_strain"],
                "eliminates": [],
                "reasoning_tag": "heel_strike_preserved"
            }
        ]
    },
    {
        "question_id": "gait_family_history",
        "question_text": "Is there a family history of childhood intoeing ('pigeon toes'), hypermobile joints, flat feet, or hip dysplasia?",
        "reason": "Benign developmental variations like generalized joint laxity, femoral anteversion, and internal tibial torsion have strong hereditary patterns and self-resolve spontaneously.",
        "target_uncertainty": "genetic / familial predisposition",
        "info_gain": 0.70,
        "relevance_fn": lambda state: (
            0.75 if (state.user_answers.get("recent_change") is False and "family_history" not in state.user_answers)
            else 0.02
        ),
        "options": [
            {
                "text": "Yes, parents, siblings, or cousins walked with a similar pattern or had flexible flat feet as toddlers",
                "updates": {"family_history": True},
                "supports": ["developmental_variation"],
                "eliminates": [],
                "reasoning_tag": "hereditary_benign_variant"
            },
            {
                "text": "No known family history of walking variations, hip dysplasia, or hypermobility",
                "updates": {"family_history": False},
                "supports": [],
                "eliminates": [],
                "reasoning_tag": "negative_family_history"
            }
        ]
    },
    {
        "question_id": "gait_fever_recent_infection",
        "question_text": "Has your child had a cold, stomach bug, ear infection, or fever within the past 1 to 2 weeks?",
        "reason": "Transient toxic synovitis of the hip is the most common cause of sudden-onset, acute non-traumatic limping in young children following an upper respiratory or GI viral illness.",
        "target_uncertainty": "post-viral synovitis",
        "info_gain": 0.85,
        "relevance_fn": lambda state: (
            0.90 if (state.user_answers.get("recent_change") is True and state.user_answers.get("recent_injury") is False)
            else (0.40 if state.user_answers.get("recent_change") is True else 0.01)
        ),
        "options": [
            {
                "text": "Yes, had a recent viral cold, tummy bug, or fever in the past 1-2 weeks",
                "updates": {"recent_infection": True},
                "supports": ["acute_injury_or_strain"],
                "eliminates": ["developmental_variation"],
                "reasoning_tag": "transient_synovitis_suspected"
            },
            {
                "text": "No, has been completely healthy without any viral symptoms or fever",
                "updates": {"recent_infection": False},
                "supports": ["developmental_variation", "structural_asymmetry"],
                "eliminates": [],
                "reasoning_tag": "afebrile_uninfected"
            }
        ]
    },
    {
        "question_id": "gait_diurnal_pattern",
        "question_text": "Is the walking asymmetry worse first thing in the morning upon waking, or does it worsen as the day goes on?",
        "reason": "Morning stiffness indicates inflammatory/joint capsule involvement (gel phenomenon), whereas end-of-day worsening indicates muscular fatigue or biomechanical misalignment.",
        "target_uncertainty": "diurnal fatigue vs inflammatory",
        "info_gain": 0.74,
        "relevance_fn": lambda state: (
            0.70 if "diurnal_pattern" not in state.user_answers and state.user_answers.get("recent_change") is not None
            else 0.0
        ),
        "options": [
            {
                "text": "Noticeably stiffer or limps more right after getting out of bed in the morning",
                "updates": {"diurnal_pattern": "morning_stiff"},
                "supports": ["acute_injury_or_strain"],
                "eliminates": ["developmental_variation"],
                "reasoning_tag": "morning_stiffness_gel_phenomenon"
            },
            {
                "text": "Worse late in the afternoon or evening after active running and playground play",
                "updates": {"diurnal_pattern": "afternoon_fatigue"},
                "supports": ["developmental_variation"],
                "eliminates": ["structural_asymmetry"],
                "reasoning_tag": "end_of_day_muscular_fatigue"
            },
            {
                "text": "Steady and unchanged throughout the entire day",
                "updates": {"diurnal_pattern": "constant"},
                "supports": ["structural_asymmetry"],
                "eliminates": [],
                "reasoning_tag": "constant_mechanical_shift"
            }
        ]
    },
    {
        "question_id": "gait_joint_swelling_warmth",
        "question_text": "Do you notice any visible swelling, redness, or warmth to the touch around your child's knee, ankle, or foot?",
        "reason": "Localized effusion, erythema, or heat indicates acute inflammatory synovitis, sprain, or localized trauma requiring clinical verification.",
        "target_uncertainty": "localized joint effusion",
        "info_gain": 0.82,
        "relevance_fn": lambda state: (
            0.88 if (state.user_answers.get("recent_change") is True or state.user_answers.get("pain_guarding") is True)
            else 0.02
        ),
        "options": [
            {
                "text": "Yes, one joint appears slightly puffy, pink, or feels warmer than the opposite side",
                "updates": {"joint_effusion": True},
                "supports": ["acute_injury_or_strain"],
                "eliminates": ["developmental_variation"],
                "reasoning_tag": "effusion_erythema_present"
            },
            {
                "text": "No swelling, redness, or heat; both legs look completely symmetrical and calm",
                "updates": {"joint_effusion": False},
                "supports": ["developmental_variation", "structural_asymmetry"],
                "eliminates": [],
                "reasoning_tag": "no_effusion_detected"
            }
        ]
    },
    {
        "question_id": "gait_surface_variation",
        "question_text": "How does your child walk when transitioning from smooth flooring onto soft grass, carpet, or uneven ground?",
        "reason": "Evaluates sensorimotor balance and proprioceptive adaptation; toddlers with benign developmental variations adapt quickly, while structural tone issues lead to frequent falls on compliant surfaces.",
        "target_uncertainty": "proprioceptive terrain adaptation",
        "info_gain": 0.68,
        "relevance_fn": lambda state: (
            0.65 if state.user_answers.get("recent_change") is False
            else 0.10
        ),
        "options": [
            {
                "text": "Adjusts well and runs with confidence on grass, carpet, and pavement alike",
                "updates": {"surface_adaptation": "smooth"},
                "supports": ["developmental_variation"],
                "eliminates": ["structural_asymmetry"],
                "reasoning_tag": "adaptive_sensorimotor_balance"
            },
            {
                "text": "Stumbles, refuses to walk, or loses balance significantly on grass or uneven ground",
                "updates": {"surface_adaptation": "poor"},
                "supports": ["structural_asymmetry"],
                "eliminates": [],
                "reasoning_tag": "poor_compliant_surface_stability"
            }
        ]
    },
    {
        "question_id": "gait_night_pain",
        "question_text": "Does your child wake up crying from leg aches at night, or does discomfort occur strictly during daytime walking?",
        "reason": "Classic pediatric growing pains occur bilaterally at night with completely normal daytime gait; daytime-only antalgic limping points to mechanical strain or localized trauma.",
        "target_uncertainty": "nocturnal vs mechanical pain",
        "info_gain": 0.76,
        "relevance_fn": lambda state: (
            0.80 if state.user_answers.get("pain_guarding") is True
            else (0.50 if state.user_answers.get("recent_change") is True else 0.02)
        ),
        "options": [
            {
                "text": "Sleeps soundly through the night; discomfort only occurs during daytime weight-bearing or walking",
                "updates": {"night_pain": False},
                "supports": ["acute_injury_or_strain"],
                "eliminates": ["developmental_variation"],
                "reasoning_tag": "mechanical_weight_bearing_pain"
            },
            {
                "text": "Wakes at night crying about aching calves or shins, but runs normally during the day",
                "updates": {"night_pain": True},
                "supports": ["developmental_variation"],
                "eliminates": ["structural_asymmetry"],
                "reasoning_tag": "benign_nocturnal_growing_pains"
            },
            {
                "text": "No pain or crying reported at all (day or night)",
                "updates": {"night_pain": "none"},
                "supports": ["developmental_variation"],
                "eliminates": ["acute_injury_or_strain"],
                "reasoning_tag": "entirely_painless_presentation"
            }
        ]
    },
    {
        "question_id": "gait_unilateral_preference",
        "question_text": "Did your child demonstrate a strong preference for using one hand or foot before their first birthday?",
        "reason": "Definitive hand dominance established prior to 12 months can be an early clinical indicator of mild hemiparesis or asymmetric neuromuscular tone.",
        "target_uncertainty": "neurologic asymmetry",
        "info_gain": 0.84,
        "relevance_fn": lambda state: (
            0.85 if (state.user_answers.get("recent_change") is False and state.user_answers.get("gross_motor_delay") is True)
            else 0.02
        ),
        "options": [
            {
                "text": "Used both hands and legs equally and symmetrically for crawling, grasping, and play",
                "updates": {"early_unilateral_dominance": False},
                "supports": ["developmental_variation"],
                "eliminates": ["structural_asymmetry"],
                "reasoning_tag": "symmetric_early_motor_milestones"
            },
            {
                "text": "Always strongly favored one hand/side, rarely reaching or bearing weight with the other",
                "updates": {"early_unilateral_dominance": True},
                "supports": ["structural_asymmetry"],
                "eliminates": ["developmental_variation"],
                "reasoning_tag": "early_unilateral_motor_preference"
            },
            {
                "text": "Unsure / don't recall early infant motor habits",
                "updates": {"early_unilateral_dominance": "unknown"},
                "supports": [],
                "eliminates": [],
                "reasoning_tag": "unilateral_preference_unknown"
            }
        ]
    },
    {
        "question_id": "gait_onset_milestone_age",
        "question_text": "At what age did your child first take independent steps without holding on to furniture or hands?",
        "reason": "Independent walking onset norm is 9 to 18 months (WHO standard); delayed onset combined with persistent asymmetry suggests tone or ligamentous immaturity.",
        "target_uncertainty": "motor milestone timeline",
        "info_gain": 0.75,
        "relevance_fn": lambda state: (
            0.70 if (state.user_answers.get("recent_change") is False and "onset_age" not in state.user_answers)
            else 0.05
        ),
        "options": [
            {
                "text": "Between 9 and 15 months (on-schedule independent walking)",
                "updates": {"onset_age": "normal_window"},
                "supports": ["developmental_variation"],
                "eliminates": [],
                "reasoning_tag": "normative_walking_onset"
            },
            {
                "text": "After 16 to 18 months (later walking onset)",
                "updates": {"onset_age": "delayed"},
                "supports": ["structural_asymmetry"],
                "eliminates": [],
                "reasoning_tag": "delayed_walking_milestone"
            },
            {
                "text": "Recently started walking within the last 2-4 weeks (new walker consolidation)",
                "updates": {"onset_age": "brand_new_walker"},
                "supports": ["developmental_variation"],
                "eliminates": ["structural_asymmetry"],
                "reasoning_tag": "toddler_balance_consolidation"
            }
        ]
    }
]

AGRICULTURE_QUESTION_BANK = [
    {
        "question_id": "agri_leaf_position",
        "question_text": "Are the yellowing symptoms primarily on the upper new shoots or the lower mature leaves?",
        "reason": "Nutrient mobility: Iron deficiency chlorosis affects new leaves first; Nitrogen/Magnesium affects older leaves.",
        "target_uncertainty": "leaf position chlorosis",
        "info_gain": 0.85,
        "relevance_fn": lambda state: 0.95 if "leaf_position" not in state.user_answers else 0.0,
        "options": [
            {
                "text": "Top crown & young emerging leaves",
                "updates": {"leaf_position": "upper_new"},
                "supports": ["iron_lockup_alkalinity"],
                "eliminates": ["nitrogen_deficiency"]
            },
            {
                "text": "Lower bottom & mature leaves",
                "updates": {"leaf_position": "lower_old"},
                "supports": ["nitrogen_deficiency"],
                "eliminates": ["iron_lockup_alkalinity"]
            }
        ]
    },
    {
        "question_id": "agri_irrigation_drainage",
        "question_text": "Does the soil remain saturated or pooled with water 24 hours after irrigation?",
        "reason": "Root zone waterlogging causes hypoxia and root anoxia, blocking active nutrient uptake.",
        "target_uncertainty": "root hypoxia",
        "info_gain": 0.80,
        "relevance_fn": lambda state: 0.90 if state.user_answers.get("leaf_position") == "upper_new" else 0.50,
        "options": [
            {
                "text": "Yes, soil stays damp/muddy with slow drainage",
                "updates": {"waterlogged": True},
                "supports": ["root_anoxia_hypoxia"]
            },
            {
                "text": "No, drains rapidly and topsoil dries out quickly",
                "updates": {"waterlogged": False},
                "supports": ["iron_lockup_alkalinity"],
                "eliminates": ["root_anoxia_hypoxia"]
            }
        ]
    }
]

BADMINTON_QUESTION_BANK = [
    {
        "question_id": "badminton_trajectory_miss",
        "question_text": "Where does your smash typically fail or land when you miss or lack penetration?",
        "reason": "Trajectory geometry differentiates late elbow contact from lack of forearm pronation snap.",
        "target_uncertainty": "smash trajectory defect",
        "info_gain": 0.92,
        "relevance_fn": lambda state: 0.98 if "trajectory_miss" not in state.user_answers else 0.0,
        "options": [
            {
                "text": "Hits the net tape or drops steeply into the net",
                "updates": {"trajectory_miss": "net_tape"},
                "supports": ["kinetic_chain_sequencing"],
                "eliminates": ["grip_orientation_twist"],
                "reasoning_tag": "late_contact_dropped_elbow"
            },
            {
                "text": "Flies flat and floats past the back baseline (out long)",
                "updates": {"trajectory_miss": "out_long"},
                "supports": ["grip_orientation_twist"],
                "eliminates": ["kinetic_chain_sequencing"],
                "reasoning_tag": "incomplete_pronation_slice"
            },
            {
                "text": "Slices wide diagonally into the side tramlines",
                "updates": {"trajectory_miss": "out_wide"},
                "supports": ["grip_orientation_twist"],
                "eliminates": ["kinetic_chain_sequencing"],
                "reasoning_tag": "bevel_misalignment"
            },
            {
                "text": "Stays in court but lands short in midcourt with no speed/penetration",
                "updates": {"trajectory_miss": "short_slow"},
                "supports": ["kinetic_chain_sequencing", "footwork_deceleration_fatigue"],
                "eliminates": ["grip_orientation_twist"],
                "reasoning_tag": "attenuated_torque"
            }
        ]
    },
    {
        "question_id": "badminton_contact_point",
        "question_text": "Where is the shuttle relative to your body when racket strings make impact?",
        "reason": "Contact angle determines whether power loss is caused by hitting behind the head vs. optimal front-reach pronation.",
        "target_uncertainty": "contact point relative to body",
        "info_gain": 0.89,
        "relevance_fn": lambda state: (
            0.95 if "contact_point" not in state.user_answers and state.user_answers.get("trajectory_miss") in ["net_tape", "short_slow"]
            else (0.75 if "contact_point" not in state.user_answers else 0.0)
        ),
        "options": [
            {
                "text": "Slightly behind my head or above the non-racket shoulder",
                "updates": {"contact_point": "behind_head"},
                "supports": ["kinetic_chain_sequencing"],
                "eliminates": ["grip_orientation_twist", "footwork_deceleration_fatigue"],
                "reasoning_tag": "behind_center_of_gravity"
            },
            {
                "text": "Well in front of dominant shoulder at high reach apex",
                "updates": {"contact_point": "front_apex"},
                "supports": ["grip_orientation_twist", "footwork_deceleration_fatigue"],
                "eliminates": ["kinetic_chain_sequencing"],
                "reasoning_tag": "biomechanically_sound_reach"
            },
            {
                "text": "Dropping below head height (late pulled contact)",
                "updates": {"contact_point": "low_drop"},
                "supports": ["footwork_deceleration_fatigue", "kinetic_chain_sequencing"],
                "eliminates": ["grip_orientation_twist"],
                "reasoning_tag": "suboptimal_low_impact"
            }
        ]
    },
    {
        "question_id": "badminton_fatigue_timeline",
        "question_text": "When does this inconsistency or power drop occur during your training/match?",
        "reason": "Differentiates permanent technical habit/grip flaw from physical endurance and deceleration breakdown.",
        "target_uncertainty": "fatigue timeline",
        "info_gain": 0.86,
        "relevance_fn": lambda state: 0.90 if "fatigue_timeline" not in state.user_answers else 0.0,
        "options": [
            {
                "text": "From the very first rally / warm-up shots (consistent technical habit)",
                "updates": {"fatigue_timeline": "immediate"},
                "supports": ["grip_orientation_twist", "kinetic_chain_sequencing"],
                "eliminates": ["footwork_deceleration_fatigue"],
                "reasoning_tag": "intrinsic_motor_habit"
            },
            {
                "text": "Only in late Set 2 / Set 3 after 20+ minutes of high-speed rallies",
                "updates": {"fatigue_timeline": "late_fatigue"},
                "supports": ["footwork_deceleration_fatigue"],
                "eliminates": ["kinetic_chain_sequencing", "grip_orientation_twist"],
                "reasoning_tag": "eccentric_braking_exhaustion"
            }
        ]
    },
    {
        "question_id": "badminton_grip_feel",
        "question_text": "How tightly do you hold the racket handle during the preparatory backswing phase?",
        "reason": "Excessive grip tension prevents forearm pronation and blocks wrist whip.",
        "target_uncertainty": "grip tension mechanics",
        "info_gain": 0.84,
        "relevance_fn": lambda state: (
            0.95 if state.user_answers.get("trajectory_miss") in ["out_long", "out_wide"] and "grip_feel" not in state.user_answers
            else (0.60 if "grip_feel" not in state.user_answers else 0.0)
        ),
        "options": [
            {
                "text": "Tight palm squeeze throughout the preparation and swing",
                "updates": {"grip_feel": "tight_palm"},
                "supports": ["grip_orientation_twist"],
                "eliminates": ["kinetic_chain_sequencing", "footwork_deceleration_fatigue"],
                "reasoning_tag": "isometric_lockup"
            },
            {
                "text": "Relaxed in fingers, only snapping tight at milliseconds of impact",
                "updates": {"grip_feel": "relaxed_fingers"},
                "supports": ["kinetic_chain_sequencing"],
                "eliminates": ["grip_orientation_twist"],
                "reasoning_tag": "proper_kinetic_coupling"
            },
            {
                "text": "Panhandle (thumb resting flat on the broad bevel)",
                "updates": {"grip_feel": "panhandle"},
                "supports": ["grip_orientation_twist"],
                "eliminates": ["kinetic_chain_sequencing", "footwork_deceleration_fatigue"],
                "reasoning_tag": "frying_pan_grip_pathology"
            }
        ]
    },
    {
        "question_id": "badminton_arm_discomfort",
        "question_text": "Do you experience joint stiffness or soreness in your hitting arm after smash sessions?",
        "reason": "Medial epicondyle soreness indicates dropped elbow; shoulder pinch indicates incomplete trunk rotation.",
        "target_uncertainty": "joint strain pathology",
        "info_gain": 0.80,
        "relevance_fn": lambda state: 0.70 if "arm_discomfort" not in state.user_answers else 0.0,
        "options": [
            {
                "text": "Inner elbow soreness or forearm flexor tightness (Golfer's elbow strain)",
                "updates": {"arm_discomfort": "medial_elbow"},
                "supports": ["kinetic_chain_sequencing"],
                "eliminates": [],
                "reasoning_tag": "valgus_extension_overload"
            },
            {
                "text": "Anterior shoulder pinch during maximum racket takeback",
                "updates": {"arm_discomfort": "anterior_shoulder"},
                "supports": ["kinetic_chain_sequencing"],
                "eliminates": [],
                "reasoning_tag": "subacromial_impingement"
            },
            {
                "text": "Zero pain or soreness; purely looking to increase shot speed and consistency",
                "updates": {"arm_discomfort": "none"},
                "supports": ["footwork_deceleration_fatigue", "grip_orientation_twist"],
                "eliminates": [],
                "reasoning_tag": "asymptomatic_mechanical_optimization"
            }
        ]
    }
]


# ---------------------------------------------------------------------------
# Adaptive Inquiry Engine
# ---------------------------------------------------------------------------

class AdaptiveInquiryEngine:
    """
    Domain-agnostic adaptive questioning engine.
    Maintains structured Case State, computes Information Gain × Relevance × Uncertainty,
    and drives dynamic diagnostic branching.
    """

    def __init__(self):
        self.vlm = VLMService()
        self.rag = RAGKnowledgeService()
        self._sessions: Dict[str, AdaptiveSession] = {}

    def start_session(
        self,
        investigation_id: str,
        user_concern: str,
        domain: str = "gait",
        measured_context: Dict[str, Any] = None,
        subject_id: str = "child_leo_24m"
    ) -> AdaptiveSession:
        """
        Initialize an adaptive diagnostic session:
        1. Compare against personalized baseline if available
        2. Formulate structured Case State
        3. Formulate competing hypotheses
        4. Select first best question using Information Gain scoring
        """
        measured_context = measured_context or {}
        domain_clean = (domain or "gait").lower()

        # Step 1: Check child's personalized baseline
        baseline_comp = None
        if "gait" in domain_clean or "pediatric" in domain_clean or "toddle" in domain_clean:
            baseline_comp = personalized_baseline_service.compare_assessment(subject_id, measured_context)

        # Step 2: Formulate initial Case State
        observations = {}
        uncertainties = []

        asym = (
            measured_context.get("step_time_asymmetry_pct") or
            measured_context.get("metrics", {}).get("step_time_asymmetry_pct") or
            measured_context.get("temporal", {}).get("step_time_asymmetry_pct")
        )

        has_deviation = False
        baseline_summary = None

        if baseline_comp and baseline_comp.has_baseline:
            if baseline_comp.has_meaningful_deviation:
                has_deviation = True
                baseline_summary = baseline_comp.clinical_summary
                observations["baseline_deviation_detected"] = True
                observations["child_name"] = baseline_comp.child_name
                observations["prior_sessions"] = baseline_comp.baseline_session_count
                if baseline_comp.primary_alert:
                    observations["primary_alert"] = baseline_comp.primary_alert
            else:
                baseline_summary = f"Movement metrics align with {baseline_comp.child_name}'s typical baseline ({baseline_comp.baseline_session_count} prior sessions)."
                observations["baseline_deviation_detected"] = False

        asym_val = _safe_float(asym)
        if asym_val is not None:
            observations["step_asymmetry_pct"] = round(asym_val, 1)
            observations["step_asymmetry"] = asym_val > 8.0

        if any(k in domain_clean for k in ["badminton", "sport", "racket", "smash", "shuttle"]):
            uncertainties = [
                "smash trajectory defect",
                "contact point relative to body",
                "fatigue timeline",
                "grip tension mechanics",
                "joint strain pathology"
            ]
        elif "gait" in domain_clean or "pediatric" in domain_clean:
            uncertainties = [
                "possible recent change",
                "possible injury",
                "pain status",
                "functional impact"
            ]
        elif "agri" in domain_clean:
            uncertainties = [
                "leaf position chlorosis",
                "root hypoxia",
                "fertilizer schedule"
            ]
        else:
            uncertainties = ["onset timeline", "operational intensity"]

        case_state = CaseState(
            observations=observations,
            user_answers={},
            uncertainties=uncertainties,
            confidence=0.55,
            baseline_deviation_detected=has_deviation,
            baseline_summary=baseline_summary
        )

        # Step 3: Formulate initial competing hypotheses
        hypotheses = self._formulate_initial_hypotheses(domain_clean, case_state)

        # Create session
        session = AdaptiveSession(
            investigation_id=investigation_id,
            user_concern=user_concern,
            domain=domain_clean,
            case_state=case_state,
            hypotheses=hypotheses,
            measured_context=measured_context,
            turn=0,
            max_questions=4,
            confidence_threshold=0.85
        )

        # Step 4: Formulate conversational preamble & select first discriminating question
        if any(k in domain_clean for k in ["badminton", "sport", "racket", "smash", "shuttle"]):
            dist_num = _safe_float(measured_context.get("total_distance_m"))
            dist_str = f" across {dist_num:.1f}m court coverage" if dist_num else ""
            session.preamble = (
                f"Kinematic tracking detected overhead stroke mechanics{dist_str}. "
                f"To isolate whether power loss and shot inconsistency stem from **kinetic chain sequencing**, "
                f"**grip bevel misalignment**, or **footwork deceleration fatigue**, please answer a few quick questions."
            )
        elif has_deviation and baseline_comp:
            norm_mean = 3.4
            if baseline_comp.comparison_items and len(baseline_comp.comparison_items) > 0:
                norm_mean = baseline_comp.comparison_items[0].baseline_mean
            session.preamble = (
                f"We compared today's video with **{baseline_comp.child_name}'s personalized baseline** "
                f"({baseline_comp.baseline_session_count} previous recordings). "
                f"Today shows an elevated asymmetry of **{observations.get('step_asymmetry_pct', 15.2)}%** "
                f"(normally {norm_mean:.1f}%). "
                f"To understand the context of this change, please answer a few quick questions."
            )
        else:
            session.preamble = (
                f"Based on video analysis, we observed an uneven stepping pattern ({observations.get('step_asymmetry_pct', 15.0)}% asymmetry). "
                f"To evaluate whether this is a temporary adjustment or an established pattern, let's explore the context."
            )

        question = self._select_next_best_question(session)
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
        Process user's selected answer:
        1. Find selected option and update Case State
        2. Update hypothesis probabilities using Bayesian likelihood shifts
        3. Check stopping condition (confidence >= threshold or max questions)
        4. If not stopping, dynamically select the next best question
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Adaptive session {session_id} not found.")

        current_q = session.current_question
        if not current_q:
            raise ValueError("No active question to answer.")

        # Find selected option
        selected_option = next((opt for opt in current_q.options if opt.option_id == selected_option_id), None)
        if not selected_option:
            raise ValueError(f"Option {selected_option_id} not found in current question.")

        # 1. Update Case State
        case_state = session.case_state or CaseState()
        q_meta = self._find_question_meta(session.domain, current_q.question_id)

        # Record answer text and updates in Case State
        session.answers_given.append({
            "turn": session.turn,
            "question_id": current_q.question_id,
            "question_text": current_q.question_text,
            "selected_option_id": selected_option.option_id,
            "selected_text": selected_option.text
        })
        session.questions_asked.append(current_q)

        # Apply state updates from question bank metadata
        opt_meta = None
        if q_meta:
            target_u = q_meta.get("target_uncertainty")
            if target_u and target_u in case_state.uncertainties:
                case_state.uncertainties.remove(target_u)

            for om in q_meta.get("options", []):
                if om.get("text") == selected_option.text:
                    opt_meta = om
                    for k, v in om.get("updates", {}).items():
                        case_state.user_answers[k] = v
                    break

        # 2. Update Bayesian Hypotheses
        session = self._update_hypotheses_bayesian(session, selected_option, opt_meta)

        # Update confidence in Case State
        active_hypotheses = [h for h in session.hypotheses if h.status == "active"]
        top_hypo = max(session.hypotheses, key=lambda h: h.current_probability) if session.hypotheses else None
        if top_hypo:
            case_state.confidence = top_hypo.current_probability

        session.case_state = case_state

        # 3. Check Stopping Conditions
        # Conclude if:
        # - Top hypothesis reached or exceeded confidence threshold (85%)
        # - Only 1 active hypothesis remains
        # - Turn reached max_questions
        # - No candidate question provides meaningful information gain
        should_conclude = (
            session.turn >= session.max_questions or
            len(active_hypotheses) <= 1 or
            (top_hypo and top_hypo.current_probability >= session.confidence_threshold)
        )

        if should_conclude:
            session = self._generate_conclusion(session)
            session.status = "concluded"
            session.current_question = None
            session.preamble = "Diagnostic assessment complete."
        else:
            # 4. Dynamically Select Next Best Question
            next_q = self._select_next_best_question(session)
            if next_q:
                session.current_question = next_q
                session.turn += 1
                # Conversational bridge acknowledging previous answer
                session.preamble = self._generate_conversational_bridge(session, selected_option)
            else:
                # No remaining questions with meaningful score -> conclude
                session = self._generate_conclusion(session)
                session.status = "concluded"
                session.current_question = None

        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[AdaptiveSession]:
        return self._sessions.get(session_id)

    # ------------------------------------------------------------------
    # Dynamic Question Selection Engine (Score = InfoGain × Relevance × Uncertainty)
    # ------------------------------------------------------------------

    def _select_next_best_question(self, session: AdaptiveSession) -> Optional[DiagnosticQuestion]:
        """
        Dynamically selects the highest-scoring question from the domain bank:
        Score = Expected Info Gain × Dynamic Relevance × Uncertainty Factor
        """
        bank = self._get_question_bank(session.domain)
        case_state = session.case_state or CaseState()
        asked_ids = {q.question_id for q in session.questions_asked}
        if session.current_question:
            asked_ids.add(session.current_question.question_id)

        candidate_scores = []

        for q_entry in bank:
            q_id = q_entry["question_id"]
            if q_id in asked_ids:
                continue

            target_u = q_entry.get("target_uncertainty")
            # Uncertainty Factor U in [0, 1]
            u_factor = 1.0 if target_u in case_state.uncertainties else 0.1

            # Dynamic Relevance R in [0, 1]
            relevance_fn = q_entry.get("relevance_fn")
            relevance = relevance_fn(case_state) if relevance_fn else 0.5

            # Information Gain IG in [0, 1]
            ig = q_entry.get("info_gain", 0.70)

            # Composite Score = IG × Relevance × Uncertainty
            score = round(ig * relevance * u_factor, 3)

            if score > 0.08:  # Minimum meaningful threshold
                candidate_scores.append((score, q_entry))

        if not candidate_scores:
            return None

        # Sort descending by score
        candidate_scores.sort(key=lambda x: x[0], reverse=True)
        best_score, best_entry = candidate_scores[0]

        # Build DiagnosticQuestion
        options = []
        for opt_data in best_entry.get("options", []):
            options.append(AnswerOption(
                text=opt_data["text"],
                eliminates=opt_data.get("eliminates", []),
                supports=opt_data.get("supports", [])
            ))

        return DiagnosticQuestion(
            question_id=best_entry["question_id"],
            question_text=best_entry["question_text"],
            reason=best_entry.get("reason", ""),
            options=options,
            expected_information_gain=best_score,
            turn_number=session.turn + 1
        )

    def _get_question_bank(self, domain: str) -> List[Dict[str, Any]]:
        d = domain.lower()
        if any(k in d for k in ["badminton", "sport", "racket", "smash", "shuttle"]):
            return BADMINTON_QUESTION_BANK
        if any(k in d for k in ["gait", "pediatric", "toddle", "walking"]):
            return GAIT_QUESTION_BANK
        if any(k in d for k in ["agri", "crop", "leaf", "plant"]):
            return AGRICULTURE_QUESTION_BANK
        return GAIT_QUESTION_BANK

    def _find_question_meta(self, domain: str, question_id: str) -> Optional[Dict[str, Any]]:
        bank = self._get_question_bank(domain)
        for q in bank:
            if q["question_id"] == question_id:
                return q
        return None

    # ------------------------------------------------------------------
    # Bayesian Hypotheses Formulation & Probability Updating
    # ------------------------------------------------------------------

    def _formulate_initial_hypotheses(self, domain: str, state: CaseState) -> List[Hypothesis]:
        """Formulate domain-specific initial competing hypotheses."""
        if any(k in domain for k in ["badminton", "sport", "racket", "smash", "shuttle"]):
            return [
                Hypothesis(
                    hypothesis_id="kinetic_chain_sequencing",
                    name="Kinetic Chain Sequencing / Dropped Elbow",
                    description="Suboptimal proximal-to-distal acceleration or contact point too far behind head, leading to net tape clipping or weak downward penetration.",
                    prior_probability=0.35,
                    current_probability=0.35,
                    status="active"
                ),
                Hypothesis(
                    hypothesis_id="grip_orientation_twist",
                    name="Grip Orientation & Pronation Bevel Twist",
                    description="Excessive backswing palm tension or bevel misalignment (panhandle bias) that blocks internal forearm pronation and slices the shuttle wide or out long.",
                    prior_probability=0.35,
                    current_probability=0.35,
                    status="active"
                ),
                Hypothesis(
                    hypothesis_id="footwork_deceleration_fatigue",
                    name="Footwork Deceleration & Stance Fatigue",
                    description="Delayed split-step timing or eccentric fatigue in late sets, causing posterior centroid drift and late contact from an unbalanced base.",
                    prior_probability=0.30,
                    current_probability=0.30,
                    status="active"
                )
            ]
        elif any(k in domain for k in ["gait", "pediatric", "toddle", "walking"]):
            return [
                Hypothesis(
                    hypothesis_id="acute_injury_or_strain",
                    name="Acute Injury or Muscle Strain",
                    description="A recent fall, awkward landing, or minor foot/leg strain causing protective antalgic guarding.",
                    prior_probability=0.35,
                    current_probability=0.35,
                    status="active"
                ),
                Hypothesis(
                    hypothesis_id="developmental_variation",
                    name="Benign Developmental Variation",
                    description="Normal asymmetric motor maturation common in toddlers learning walking rhythm and balance.",
                    prior_probability=0.40,
                    current_probability=0.40,
                    status="active"
                ),
                Hypothesis(
                    hypothesis_id="structural_asymmetry",
                    name="Structural Alignment / Limb Asymmetry",
                    description="A persistent leg length difference, hip alignment variation, or joint restriction.",
                    prior_probability=0.25,
                    current_probability=0.25,
                    status="active"
                )
            ]
        elif any(k in domain for k in ["agri", "crop", "leaf"]):
            return [
                Hypothesis(
                    hypothesis_id="iron_lockup_alkalinity",
                    name="Alkaline Substrate Fe²⁺ Lockup",
                    description="Root zone pH elevation causing iron precipitation into insoluble forms.",
                    prior_probability=0.45,
                    current_probability=0.45,
                    status="active"
                ),
                Hypothesis(
                    hypothesis_id="root_anoxia_hypoxia",
                    name="Root Hypoxia / Over-Irrigation",
                    description="Excess soil water saturation preventing root aerobic ATP synthesis.",
                    prior_probability=0.35,
                    current_probability=0.35,
                    status="active"
                ),
                Hypothesis(
                    hypothesis_id="nitrogen_deficiency",
                    name="Nitrogen Leaching Deficiency",
                    description="Insufficient mobile nitrogen available for foliar chlorophyll synthesis.",
                    prior_probability=0.20,
                    current_probability=0.20,
                    status="active"
                )
            ]
        else:
            return [
                Hypothesis(
                    hypothesis_id="operational_fatigue",
                    name="Operational / Dynamic Fatigue",
                    description="Temporary load-dependent variation during active movement.",
                    prior_probability=0.50,
                    current_probability=0.50,
                    status="active"
                ),
                Hypothesis(
                    hypothesis_id="baseline_characteristic",
                    name="Intrinsic Individual Characteristic",
                    description="Persistent individual movement style within acceptable tolerance.",
                    prior_probability=0.50,
                    current_probability=0.50,
                    status="active"
                )
            ]

    def _update_hypotheses_bayesian(
        self, session: AdaptiveSession, selected_option: AnswerOption, opt_meta: Optional[Dict]
    ) -> AdaptiveSession:
        """Applies likelihood updates and normalizes hypothesis probabilities."""
        supports = selected_option.supports or (opt_meta.get("supports", []) if opt_meta else [])
        eliminates = selected_option.eliminates or (opt_meta.get("eliminates", []) if opt_meta else [])

        for h in session.hypotheses:
            if h.status != "active":
                continue

            if h.hypothesis_id in eliminates or any(e in h.name.lower() for e in eliminates):
                # Likelihood penalty
                h.current_probability = max(0.02, h.current_probability * 0.15)
                h.contradicting_evidence.append(selected_option.text)
                if h.current_probability < 0.08:
                    h.status = "eliminated"

            elif h.hypothesis_id in supports or any(s in h.name.lower() for s in supports):
                # Likelihood boost
                h.current_probability = min(0.95, h.current_probability * 1.8 + 0.12)
                h.supporting_evidence.append(selected_option.text)

        # Normalize active probabilities
        active = [h for h in session.hypotheses if h.status == "active"]
        total = sum(h.current_probability for h in active)
        if total > 0:
            for h in active:
                h.current_probability = round(h.current_probability / total, 3)

        # If highest probability >= 0.85, mark as confirmed
        for h in active:
            if h.current_probability >= session.confidence_threshold:
                h.status = "confirmed"

        return session

    def _generate_conversational_bridge(
        self, session: AdaptiveSession, selected_option: AnswerOption
    ) -> str:
        """Generates an empathetic conversational bridge acknowledging the previous answer."""
        text = selected_option.text.lower()
        # Badminton Biomechanical Bridges
        if "net tape" in text or "into the net" in text:
            return "Thank you. Missing into the net tape strongly suggests a **late contact point or dropped elbow angle**. Let's pinpoint where impact occurs relative to your body."
        elif "out long" in text or "past the back baseline" in text:
            return "Got it. Sinking past the baseline points to an **open racket face or incomplete forearm pronation snap**. Let's examine your grip tension during the preparation phase."
        elif "slices wide" in text or "tramlines" in text:
            return "Slicing wide indicates **bevel misalignment or early wrist angling**. Let's verify your grip feel and tension mechanics."
        elif "short in midcourt" in text:
            return "Midcourt landing indicates attenuated kinetic transfer. Let's look at contact geometry and physical fatigue."
        elif "behind my head" in text:
            return "Hitting behind your head severely disrupts the proximal-to-distal kinetic chain. Let's check whether you experience any shoulder or elbow soreness."
        elif "front of dominant shoulder" in text:
            return "Excellent contact apex. Since reach geometry is sound, let's explore grip orientation and late-game fatigue."
        elif "tight palm squeeze" in text:
            return "Excessive grip tension locks the wrist and prevents forearm pronation. This directly explains trajectory slice and power dissipation."
        elif "relaxed in fingers" in text:
            return "Great technique. Maintaining a relaxed finger grip until millisecond impact preserves optimal rotational whip."
        elif "only in late set" in text:
            return "This timeline points to **fatigue-induced spatial drift** rather than an intrinsic stroke habit flaw."
        elif "inner elbow soreness" in text:
            return "Inner elbow soreness is classic for valgus extension overload from a dropped elbow. Correcting your contact point apex will protect the joint."
        # Gait Bridges
        elif "yes, noticed it recently" in text:
            return "Thank you. Since this appears to be a **recent change**, I'd like to check whether there was a specific triggering event."
        elif "no, they have always walked this way" in text:
            return "Understood. Since this has been present **since early walking**, let's look into functional gross motor milestones and endurance."
        elif "had a fall" in text or "injury" in text:
            return "That is a critical clue. A recent fall often causes **protective antalgic guarding**. Let's check for pain or tenderness."
        elif "no known injury" in text:
            return "Good to know. Since there was no trauma, let's see how your child moves during higher-demand activities like running or stairs."
        elif "runs, jumps, and climbs" in text:
            return "Excellent. Intact gross motor skills strongly support a **benign developmental variation** that often resolves with maturation."
        return "Thank you. Let's look at another aspect to refine the assessment."

    # ------------------------------------------------------------------
    # Diagnostic Conclusion Generation
    # ------------------------------------------------------------------

    def _generate_conclusion(self, session: AdaptiveSession) -> AdaptiveSession:
        """Generate clinical/athletic diagnostic summary with root cause, ruled-out conditions, and recommendations."""
        active = [h for h in session.hypotheses if h.status in ["active", "confirmed"]]
        eliminated = [h for h in session.hypotheses if h.status == "eliminated"]
        top = max(session.hypotheses, key=lambda h: h.current_probability) if session.hypotheses else None

        if top and top.status != "confirmed":
            top.status = "confirmed"

        top_name = top.name if top else "Undetermined Pattern"
        top_prob = round(top.current_probability * 100) if top else 75

        # Format Q&A history
        qa_lines = [
            f"- **Q{i+1}**: *{a['question_text']}* ➔ **\"{a['selected_text']}\"**"
            for i, a in enumerate(session.answers_given)
        ]
        qa_str = "\n".join(qa_lines) if qa_lines else "No questions answered."

        # Check if domain is badminton / sports
        is_badminton = any(k in session.domain for k in ["badminton", "sport", "racket", "smash", "shuttle"])

        if is_badminton:
            conclusion_md = f"""## Calibrated Kinematic Diagnostic Report: {top_name} ({top_prob}% Confidence)

### 1. Primary Root Cause Finding
Based on computer vision kinematic tracking and your interactive diagnostic responses, your stroke mechanics and shot variance are primarily driven by **{top_name}**.

{top.description if top else ""}

### 2. Evidence Synthesis from Your Responses
{qa_str}

### 3. Biomechanical Pathologies Ruled Out
"""
            if eliminated:
                for el in eliminated:
                    conclusion_md += f"- ~~**{el.name}**~~ ({round(el.current_probability * 100)}%): Ruled out based on your responses.\n"
            else:
                conclusion_md += "- Competing biomechanical causes remain secondary to the primary driver above.\n"

            conclusion_md += f"""
### 4. Technical Correction & Action Plan
- **High Apex Reach Drill**: Suspend a shuttlecock at maximum vertical extension (110–115% standing reach). Practice shadow smashes initiating impact 20–30 cm in front of the dominant shoulder to eliminate dropped elbow contact.
- **Relaxed Grip Pronation Conditioning**: Use a thumb-and-index finger pinch on bevel #2, keeping palm tension below 20% until 5 milliseconds prior to impact to maximize internal radioulnar rotational velocity (40–50% of final racket speed).
- **Centroid Reset & Split-Step Synchronization**: Execute 10-shuttle multi-shuttle intervals focusing on recovering to the center base (y ≈ 3.5m from net) within 0.8s of smash execution to prevent fatigue-induced spatial drift.

---
*Athletic Analytics Disclaimer: This assessment provides automated kinematic and biomechanical guidance for coaching optimization. Consult a certified sports physiotherapist or badminton coach for personalized on-court biomechanics instruction.*
"""
            session.conclusion = conclusion_md
            session.personalized_recommendations = [
                "Practice high-apex contact suspension drills to ensure impact occurs 20-30cm in front of shoulder",
                "Maintain loose finger grip (relaxed bevel #2) during takeback to unlock 40-50% forearm pronation speed",
                "Train 10-shuttle anaerobic intervals with centroid recovery to prevent late-set footwork fatigue drift"
            ]
            return session

        # Default Pediatric Gait Conclusion
        child_name = session.case_state.observations.get("child_name") if session.case_state else "your child"

        conclusion_md = f"""## Personalized Diagnostic Assessment: {top_name} ({top_prob}% Confidence)

### 1. Root Cause Finding
Based on the integration of **computer vision measurements** ({session.case_state.observations.get('step_asymmetry_pct', 15.2)}% step asymmetry) and your responses during the adaptive inquiry, the most probable explanation is **{top_name}**.

{top.description if top else ""}

### 2. Evidence Synthesis from Your Responses
{qa_str}

### 3. Conditions Ruled Out
"""
        if eliminated:
            for el in eliminated:
                conclusion_md += f"- ~~**{el.name}**~~ ({round(el.current_probability * 100)}%): Ruled out based on your responses.\n"
        else:
            conclusion_md += "- No alternative conditions completely eliminated, but relative likelihood is significantly lower.\n"

        conclusion_md += f"""
### 4. Custom Action Plan for {child_name}
- **Short-Term Monitoring**: Keep a movement log over the next 5–7 days. Note whether the step difference decreases with rest.
- **Supportive Footwear & Environment**: Allow plenty of safe, barefoot walking on varied textures (carpet, grass, firm mats) to encourage natural proprioception.
- **Physical Pediatric Check**: Share this structured assessment with your pediatrician or pediatric physical therapist if asymmetry persists beyond 2 weeks or if any discomfort appears.

---
*Clinical Disclaimer: This automated screening tool provides observational insights and does not constitute a formal medical diagnosis. Consult a qualified pediatric specialist for clinical evaluation.*
"""
        session.conclusion = conclusion_md
        session.personalized_recommendations = [
            f"Monitor {child_name}'s walking over the next 5-7 days for natural improvement",
            "Encourage safe barefoot play on grass or carpet to promote bilateral foot development",
            "Consult a pediatrician or physical therapist if uneven walking persists beyond 2 weeks"
        ]
        return session


# Global singleton engine
adaptive_inquiry_engine = AdaptiveInquiryEngine()
