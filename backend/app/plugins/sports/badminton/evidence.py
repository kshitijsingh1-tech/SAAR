"""
Badminton Knowledge & Evidence Graph Engine.

Constructs a unified, directed causal & evidence graph adhering to:
1. Core SAAR graph infrastructure (ReasoningGraphEngine, NodeModel, EdgeModel, GraphStateModel).
2. Section 25 node types: player, court, shot, shot_type, movement, joint, racket,
   shuttle, metric, observation, trend, hypothesis, recommendation, evidence.
3. Section 28 Category discipline: OBSERVATION, MEASUREMENT, TREND, CORRELATION,
   RAG_EVIDENCE, HYPOTHESIS, RECOMMENDATION, LIMITATION.
4. Complete numeric attribution: every numeric node carries value, unit, confidence,
   source, timestamp_or_frame_range, and calculation_method in its properties dict.
5. Zero orphan nodes: every node connects via typed directed edges into the evidence network.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
import networkx as nx

from app.schemas import NodeModel, EdgeModel, GraphStateModel
from app.graph_engine import ReasoningGraphEngine
from .schemas import (
    VideoMetadata,
    QualityAssessment,
    CaptureConfidence,
    PlayerMetadata,
    CourtCalibration,
    CourtMetrics,
    MovementMetrics,
    ShotResult,
    ShotMetrics,
    SpeedMetrics,
    EnergyMetrics,
    PoseMetrics,
)
from .reasoning import BadmintonHypothesisEngine


class Section25NodeType(str, Enum):
    """Explicit node types defined in Section 25 of the Biomechanics Specification."""
    PLAYER = "player"
    COURT = "court"
    SHOT = "shot"
    SHOT_TYPE = "shot_type"
    MOVEMENT = "movement"
    JOINT = "joint"
    RACKET = "racket"
    SHUTTLE = "shuttle"
    METRIC = "metric"
    OBSERVATION = "observation"
    TREND = "trend"
    HYPOTHESIS = "hypothesis"
    RECOMMENDATION = "recommendation"
    EVIDENCE = "evidence"


class NodeCategory(str, Enum):
    """
    Section 28 Category Discipline.
    Ensures epistemic integrity across observations, measurements, literature grounding, and limits.
    """
    OBSERVATION = "OBSERVATION"        # Directly observed/perceived from sensor/vision frames
    MEASUREMENT = "MEASUREMENT"        # Derived/calculated mathematical property
    TREND = "TREND"                    # Change over time across sessions (Phase 17 longitudinal)
    CORRELATION = "CORRELATION"        # Statistical co-variance between signals
    RAG_EVIDENCE = "RAG_EVIDENCE"      # Domain literature citations & external clinical/athletic standards
    HYPOTHESIS = "HYPOTHESIS"          # Exploratory biomechanical inferences requiring validation
    RECOMMENDATION = "RECOMMENDATION"  # Actionable coaching & technique cues
    LIMITATION = "LIMITATION"          # Explicit honesty boundary / unmeasured signal gate


def _normalize_confidence(conf: Any, default: float = 0.85) -> float:
    """Safely converts string, numeric, or enum confidence into a float in [0.0, 1.0]."""
    if conf is None:
        return default
    if isinstance(conf, (int, float)):
        return max(0.0, min(1.0, float(conf)))
    s = str(conf).strip().upper()
    if s == "HIGH":
        return 0.95
    if s == "MEDIUM":
        return 0.75
    if s == "LOW":
        return 0.40
    try:
        return max(0.0, min(1.0, float(s)))
    except ValueError:
        return default


class BadmintonEvidenceGraphBuilder:
    """
    Builds a grounded Knowledge & Evidence Graph from all badminton analysis phases.
    Uses ReasoningGraphEngine to ensure standard SAAR topology, confidence scoring,
    and seamless rendering in KnowledgeGraphCanvas.jsx.
    """

    def __init__(self):
        self.engine = ReasoningGraphEngine()

    def build_evidence_graph(
        self,
        video_metadata: VideoMetadata,
        quality: Optional[QualityAssessment] = None,
        player_metadata: Optional[PlayerMetadata] = None,
        court_calibration: Optional[CourtCalibration] = None,
        court_metrics: Optional[CourtMetrics] = None,
        movement_metrics: Optional[MovementMetrics] = None,
        shots: Optional[List[ShotResult]] = None,
        shot_metrics: Optional[ShotMetrics] = None,
        speed_metrics: Optional[SpeedMetrics] = None,
        energy_metrics: Optional[EnergyMetrics] = None,
        pose_metrics: Optional[PoseMetrics] = None,
        hypotheses: Optional[List[str]] = None,
        recommendations: Optional[List[str]] = None,
        limitations: Optional[List[str]] = None,
    ) -> GraphStateModel:
        """
        Constructs and exports the complete GraphStateModel.
        """
        self.engine.clear()
        shots = shots or []
        quality = quality or QualityAssessment(confidence=CaptureConfidence.HIGH)

        # 1. Root Entity: Tracked Player
        player_label = "Tracked Player"
        player_conf = 0.95
        if quality and hasattr(quality, "player_visibility") and quality.player_visibility.available and quality.player_visibility.value is not None:
            player_conf = float(quality.player_visibility.value)

        player_props: Dict[str, Any] = {
            "value": "Primary Athlete",
            "unit": "entity",
            "confidence": round(player_conf, 3),
            "source": "PoseEstimator (MediaPipe BlazePose 33-landmarks)",
            "timestamp_or_frame_range": f"0.00s - {video_metadata.duration_seconds:.2f}s (Frames 0 - {video_metadata.total_frames})",
            "calculation_method": "Single-person blaze pose detection & tracking"
        }
        if player_metadata:
            if player_metadata.skill_level:
                player_label += f" ({player_metadata.skill_level.title()})"
                player_props["skill_level"] = player_metadata.skill_level
            if player_metadata.body_weight_kg:
                player_props["body_weight_kg"] = player_metadata.body_weight_kg
            if player_metadata.age:
                player_props["age"] = player_metadata.age
            if player_metadata.match_type:
                player_props["match_type"] = player_metadata.match_type

        self.engine.add_node(NodeModel(
            id="player_main",
            label=player_label,
            node_type=Section25NodeType.PLAYER.value,
            category=NodeCategory.OBSERVATION.value,
            confidence=player_props["confidence"],
            properties=player_props,
            status="confirmed",
            visual_anchor=True
        ))

        # 2. Root/Spatial Entity: Badminton Court
        is_court_calib = bool(court_calibration and court_calibration.is_calibrated)
        court_label = "Court: Calibrated (13.4m x 6.1m)" if is_court_calib else "Court: Uncalibrated"
        court_props = {
            "value": "13.4m x 6.1m BWF Standard" if is_court_calib else "Uncalibrated",
            "unit": "meters" if is_court_calib else "status",
            "confidence": round(court_calibration.confidence if court_calibration else 0.0, 3),
            "source": "CourtDetector (Phase 4)",
            "timestamp_or_frame_range": f"0.00s - {video_metadata.duration_seconds:.2f}s",
            "calculation_method": (
                "4-corner planar homography perspective transformation"
                if is_court_calib
                else (court_calibration.uncalibrated_reason if court_calibration else "Court boundaries obscured")
            )
        }
        if is_court_calib and court_calibration and court_calibration.corners_pixel:
            court_props["corners_pixel"] = court_calibration.corners_pixel

        self.engine.add_node(NodeModel(
            id="court_plane",
            label=court_label,
            node_type=Section25NodeType.COURT.value,
            category=NodeCategory.MEASUREMENT.value if is_court_calib else NodeCategory.LIMITATION.value,
            confidence=court_props["confidence"] if is_court_calib else 0.2,
            properties=court_props,
            status="confirmed" if is_court_calib else "invalidated",
            visual_anchor=True
        ))

        # 3. Movement Path & Dynamics
        mov_avail = bool(movement_metrics and movement_metrics.total_distance_m is not None)
        dist_val = movement_metrics.total_distance_m if (movement_metrics and mov_avail) else None
        mov_conf = 0.85 if mov_avail else 0.30
        mov_props = {
            "value": dist_val,
            "unit": "meters",
            "confidence": round(mov_conf, 3),
            "source": "BadmintonMovementAnalyzer (Phase 5)",
            "timestamp_or_frame_range": f"0.00s - {video_metadata.duration_seconds:.2f}s",
            "calculation_method": (
                "Sum of consecutive calibrated Euclidean hip displacements"
                if mov_avail
                else (movement_metrics.total_distance_reason if movement_metrics else "Unavailable: court not calibrated")
            ),
            "average_speed_mps": movement_metrics.average_speed_m_s if movement_metrics else None,
            "max_speed_mps": movement_metrics.max_speed_m_s if movement_metrics else None,
            "court_coverage_pct": court_metrics.court_coverage_pct if court_metrics else None,
        }
        mov_label = f"Movement: {dist_val:.1f}m Traveled" if dist_val is not None else "Movement: Uncalibrated Trajectory"

        self.engine.add_node(NodeModel(
            id="movement_dynamics",
            label=mov_label,
            node_type=Section25NodeType.MOVEMENT.value,
            category=NodeCategory.MEASUREMENT.value if mov_avail else NodeCategory.LIMITATION.value,
            confidence=mov_props["confidence"],
            properties=mov_props,
            status="confirmed" if mov_avail else "evaluating",
            visual_anchor=True
        ))

        self.engine.add_edge(EdgeModel(
            id="edge_player_movement",
            source="player_main",
            target="movement_dynamics",
            relation_type="exhibits",
            confidence=0.95,
            evidence="Continuous hip midpoint tracking over rally duration"
        ))
        self.engine.add_edge(EdgeModel(
            id="edge_court_movement",
            source="court_plane",
            target="movement_dynamics",
            relation_type="affects",
            confidence=0.90 if is_court_calib else 0.30,
            evidence="Court spatial homography scaling to metric coordinates"
        ))

        # 4. Shots, Classifications, and Contact Joint Kinematics
        for idx, shot in enumerate(shots):
            shot_node_id = f"shot_{shot.shot_id}"
            shot_label = f"Shot #{idx+1}: {shot.shot_type.upper()}"
            c_str = f"{shot.contact_time:.3f}s" if shot.contact_time is not None else (f"frame {shot.contact_frame}" if shot.contact_frame is not None else "contact")
            s_str = f"{shot.start_time:.3f}s" if shot.start_time is not None else "0.000s"
            e_str = f"{shot.end_time:.3f}s" if shot.end_time is not None else "end"
            shot_props = {
                "value": round(shot.duration, 3) if shot.duration is not None else 0.0,
                "unit": "seconds",
                "confidence": round(shot.confidence, 3) if shot.confidence is not None else 0.8,
                "source": "ShotDetector (Phase 7)",
                "timestamp_or_frame_range": f"t={c_str} (window: {s_str} - {e_str})",
                "calculation_method": "per-shot duration = end_timestamp - contact_timestamp per Section 17",
                "shot_type": shot.shot_type,
                "evidence_frames": shot.evidence_frames or []
            }
            self.engine.add_node(NodeModel(
                id=shot_node_id,
                label=shot_label,
                node_type=Section25NodeType.SHOT.value,
                category=NodeCategory.MEASUREMENT.value,
                confidence=round(shot.confidence, 3),
                properties=shot_props,
                status="confirmed",
                visual_anchor=True
            ))
            self.engine.add_edge(EdgeModel(
                id=f"edge_player_{shot_node_id}",
                source="player_main",
                target=shot_node_id,
                relation_type="executes",
                confidence=round(shot.confidence, 3) if shot.confidence is not None else 0.8,
                evidence=f"Contact event detected at t={c_str}"
            ))

            # 4a. Shot Type Node
            type_node_id = f"type_{shot.shot_id}"
            type_props = {
                "value": shot.shot_type,
                "unit": "stroke_category",
                "confidence": round(shot.confidence, 3) if shot.confidence is not None else 0.8,
                "source": "ShotClassifier (Phase 7)",
                "timestamp_or_frame_range": f"t={c_str}",
                "calculation_method": "Biomechanical heuristics (wrist height, velocity direction, preparation duration)"
            }
            self.engine.add_node(NodeModel(
                id=type_node_id,
                label=f"Class: {shot.shot_type.title()}",
                node_type=Section25NodeType.SHOT_TYPE.value,
                category=NodeCategory.MEASUREMENT.value,
                confidence=round(shot.confidence, 3) if shot.confidence is not None else 0.8,
                properties=type_props,
                status="confirmed"
            ))
            self.engine.add_edge(EdgeModel(
                id=f"edge_shot_{shot.shot_id}_to_type",
                source=shot_node_id,
                target=type_node_id,
                relation_type="classified_as",
                confidence=round(shot.confidence, 3) if shot.confidence is not None else 0.8,
                evidence=f"Kinematic classification confidence {shot.confidence:.2f}" if shot.confidence is not None else "Classification"
            ))

            # 4b. Contact-Frame Joint Kinematics (Elbow, Shoulder, Knee, Hip)
            pf = shot.pose_features or {}
            joint_specs = [
                ("elbow", pf.get("contact_elbow_angle_deg", pf.get("elbow_angle_deg")), "Elbow Extension"),
                ("shoulder", pf.get("contact_shoulder_angle_deg", pf.get("shoulder_angle_deg")), "Shoulder Elevation"),
                ("knee", pf.get("contact_knee_angle_deg", pf.get("knee_angle_deg")), "Knee Flexion"),
                ("hip", pf.get("contact_hip_angle_deg", pf.get("hip_angle_deg")), "Hip Extension")
            ]

            for j_key, j_val, j_desc in joint_specs:
                if j_val is not None:
                    joint_node_id = f"joint_{shot.shot_id}_{j_key}"
                    joint_props = {
                        "value": round(j_val, 1),
                        "unit": "degrees",
                        "confidence": 0.90,
                        "source": "BadmintonKinematicsAnalyzer (Phase 11)",
                        "timestamp_or_frame_range": f"t={c_str} (contact frame)",
                        "calculation_method": "Arccos 3-point planar angle via SportsPlugin.calculate_joint_angle_2d"
                    }
                    self.engine.add_node(NodeModel(
                        id=joint_node_id,
                        label=f"{j_desc} ({j_val:.1f}°)",
                        node_type=Section25NodeType.JOINT.value,
                        category=NodeCategory.MEASUREMENT.value,
                        confidence=0.90,
                        properties=joint_props,
                        status="confirmed",
                        visual_anchor=True
                    ))
                    self.engine.add_edge(EdgeModel(
                        id=f"edge_{shot_node_id}_to_{joint_node_id}",
                        source=shot_node_id,
                        target=joint_node_id,
                        relation_type="measures",
                        confidence=0.90,
                        evidence=f"Contact-frame 2D landmark angle {j_val:.1f}°"
                    ))

            # 4c. Kinetic Chain Sequencing (Section 42 Gating)
            seq_info = pf.get("kinetic_chain_sequencing", {})
            seq_avail = seq_info.get("available", False)
            seq_node_id = f"seq_{shot.shot_id}"
            seq_props = {
                "value": "SEQUENCED" if seq_avail else "GATED_UNAVAILABLE",
                "unit": "timing_sequence",
                "confidence": 0.85 if seq_avail else 0.30,
                "source": "BadmintonKinematicsAnalyzer (Section 42)",
                "timestamp_or_frame_range": f"Lead-in window to t={c_str}",
                "calculation_method": (
                    "Proximal-to-distal peak angular velocity derivative timing"
                    if seq_avail
                    else seq_info.get("reason", "Insufficient consecutive frames with visibility >= 0.35")
                )
            }
            self.engine.add_node(NodeModel(
                id=seq_node_id,
                label="Kinetic Chain: Confirmed" if seq_avail else "Kinetic Chain: Gated",
                node_type=Section25NodeType.EVIDENCE.value,
                category=NodeCategory.MEASUREMENT.value if seq_avail else NodeCategory.LIMITATION.value,
                confidence=seq_props["confidence"],
                properties=seq_props,
                status="confirmed" if seq_avail else "invalidated"
            ))
            self.engine.add_edge(EdgeModel(
                id=f"edge_{shot_node_id}_to_{seq_node_id}",
                source=shot_node_id,
                target=seq_node_id,
                relation_type="supports" if seq_avail else "indicates",
                confidence=seq_props["confidence"],
                evidence="Section 42 proximal-to-distal sequencing evaluation"
            ))

        # 5. Speed Analysis Nodes (Section 14 Non-Conflated Racket vs Shuttle)
        racket_avail = bool(speed_metrics and speed_metrics.racket_speed_peak.available)
        racket_val = speed_metrics.racket_speed_peak.value if (speed_metrics and racket_avail) else None
        racket_conf = _normalize_confidence(speed_metrics.racket_speed_peak.confidence if (speed_metrics and racket_avail) else 0.20)
        racket_props = {
            "value": racket_val,
            "unit": "km/h",
            "confidence": round(racket_conf, 3),
            "source": "BadmintonSpeedAnalyzer (Phase 9)",
            "timestamp_or_frame_range": "Contact window [-0.10s, +0.10s]",
            "calculation_method": (
                "v = ||dp||/dt on calibrated racket head coordinates"
                if racket_avail
                else (speed_metrics.racket_speed_peak.unavailable_reason if speed_metrics else "Insufficient continuous tracking")
            )
        }
        self.engine.add_node(NodeModel(
            id="racket_speed_peak",
            label=f"Peak Racket Speed: {racket_val:.1f} km/h" if racket_val is not None else "Racket Speed: Unavailable",
            node_type=Section25NodeType.RACKET.value,
            category=NodeCategory.MEASUREMENT.value if racket_avail else NodeCategory.LIMITATION.value,
            confidence=racket_props["confidence"],
            properties=racket_props,
            status="confirmed" if racket_avail else "invalidated"
        ))
        self.engine.add_edge(EdgeModel(
            id="edge_movement_to_racket_speed",
            source="movement_dynamics",
            target="racket_speed_peak",
            relation_type="measures" if racket_avail else "indicates",
            confidence=racket_props["confidence"],
            evidence="Section 14 racket speed assessment"
        ))

        shuttle_avail = bool(speed_metrics and speed_metrics.shuttle_speed_peak.available)
        shuttle_val = speed_metrics.shuttle_speed_peak.value if (speed_metrics and shuttle_avail) else None
        shuttle_conf = _normalize_confidence(speed_metrics.shuttle_speed_peak.confidence if (speed_metrics and shuttle_avail) else 0.20)
        shuttle_props = {
            "value": shuttle_val,
            "unit": "km/h",
            "confidence": round(shuttle_conf, 3),
            "source": "BadmintonSpeedAnalyzer (Phase 9)",
            "timestamp_or_frame_range": "Post-contact flight trajectory",
            "calculation_method": (
                "v = ||dp||/dt on calibrated shuttle trajectory segments"
                if shuttle_avail
                else (speed_metrics.shuttle_speed_peak.unavailable_reason if speed_metrics else "Insufficient continuous tracking")
            )
        }
        self.engine.add_node(NodeModel(
            id="shuttle_speed_peak",
            label=f"Peak Shuttle Speed: {shuttle_val:.1f} km/h" if shuttle_val is not None else "Shuttle Speed: Unavailable",
            node_type=Section25NodeType.SHUTTLE.value,
            category=NodeCategory.MEASUREMENT.value if shuttle_avail else NodeCategory.LIMITATION.value,
            confidence=shuttle_props["confidence"],
            properties=shuttle_props,
            status="confirmed" if shuttle_avail else "invalidated"
        ))
        self.engine.add_edge(EdgeModel(
            id="edge_court_to_shuttle_speed",
            source="court_plane",
            target="shuttle_speed_peak",
            relation_type="measures" if shuttle_avail else "indicates",
            confidence=shuttle_props["confidence"],
            evidence="Section 14 shuttle speed calibrated trajectory"
        ))

        # 6. RAG Evidence & Metabolic Calorie Estimation (Phase 10)
        self.engine.add_node(NodeModel(
            id="rag_badminton_kb",
            label="RAG: Compendium Physical Activities (MET 7.0-8.5)",
            node_type=Section25NodeType.EVIDENCE.value,
            category=NodeCategory.RAG_EVIDENCE.value,
            confidence=0.98,
            properties={
                "value": "Compendium Codes 15040 & 15050",
                "unit": "citation",
                "confidence": 0.98,
                "source": "backend/app/knowledge/badminton_kb.md (Ainsworth et al. 2011 / Herrmann et al. 2024)",
                "timestamp_or_frame_range": "Peer-Reviewed Literature Grounding",
                "calculation_method": "Energy = MET * 3.5 * mass_kg / 200 * duration_min"
            },
            status="confirmed"
        ))

        energy_val = None
        if energy_metrics:
            if hasattr(energy_metrics.estimated_energy_expenditure_kcal, "value"):
                energy_val = energy_metrics.estimated_energy_expenditure_kcal.value
            else:
                energy_val = energy_metrics.estimated_energy_expenditure_kcal

        energy_conf = 0.85
        if energy_metrics:
            if isinstance(energy_metrics.confidence, (int, float)):
                energy_conf = float(energy_metrics.confidence)
            elif str(energy_metrics.confidence).upper() == "HIGH":
                energy_conf = 0.95
            elif str(energy_metrics.confidence).upper() == "MEDIUM":
                energy_conf = 0.75
            elif str(energy_metrics.confidence).upper() == "LOW":
                energy_conf = 0.50

        energy_props = {
            "value": round(float(energy_val), 2) if energy_val is not None else None,
            "unit": "kcal",
            "confidence": round(energy_conf, 3),
            "source": "BadmintonCalorieEstimator (Phase 10)",
            "timestamp_or_frame_range": f"Active Session: {energy_metrics.inputs_used if energy_metrics else 'N/A'}",
            "calculation_method": energy_metrics.calculation_method if energy_metrics else "MET-based metabolic equation",
            "estimation_type": energy_metrics.estimation_type if energy_metrics else "population_average_generalized",
            "inputs_used": energy_metrics.inputs_used if energy_metrics else []
        }
        self.engine.add_node(NodeModel(
            id="energy_expenditure",
            label=f"Energy: {energy_val:.2f} kcal" if energy_val is not None else "Energy Expenditure",
            node_type=Section25NodeType.METRIC.value,
            category=NodeCategory.MEASUREMENT.value,
            confidence=energy_props["confidence"],
            properties=energy_props,
            status="confirmed"
        ))
        self.engine.add_edge(EdgeModel(
            id="edge_rag_to_energy",
            source="rag_badminton_kb",
            target="energy_expenditure",
            relation_type="supports",
            confidence=0.98,
            evidence="Cited MET metabolic equivalent grounds caloric burn rate"
        ))
        self.engine.add_edge(EdgeModel(
            id="edge_player_to_energy",
            source="player_main",
            target="energy_expenditure",
            relation_type="affects",
            confidence=0.90,
            evidence="Player mass and active tempo determine metabolic energy burn"
        ))
        self.engine.add_edge(EdgeModel(
            id="edge_movement_to_energy",
            source="movement_dynamics",
            target="energy_expenditure",
            relation_type="modulates",
            confidence=0.85,
            evidence="Movement displacement velocity dynamically modulates MET intensity"
        ))

        # 7. Aggregated Shot Distribution Metric (Phase 8)
        shot_dist_props = {
            "value": len(shots),
            "unit": "shots_count",
            "confidence": 0.92,
            "source": "BadmintonMetricsCalculator (Phase 8)",
            "timestamp_or_frame_range": f"0.00s - {video_metadata.duration_seconds:.2f}s",
            "calculation_method": "count_by_shot_type and duration distributions",
            "counts": shot_metrics.count_by_shot_type if shot_metrics else {},
            "percentages": shot_metrics.percentage_by_shot_type if shot_metrics else {}
        }
        self.engine.add_node(NodeModel(
            id="metric_shot_distribution",
            label=f"Rally Metrics ({len(shots)} Strokes)",
            node_type=Section25NodeType.METRIC.value,
            category=NodeCategory.MEASUREMENT.value,
            confidence=0.92,
            properties=shot_dist_props,
            status="confirmed"
        ))
        for shot in shots:
            self.engine.add_edge(EdgeModel(
                id=f"edge_shot_{shot.shot_id}_to_dist",
                source=f"shot_{shot.shot_id}",
                target="metric_shot_distribution",
                relation_type="supports",
                confidence=0.92,
                evidence="Aggregated into rally stroke volume and duration distributions"
            ))

        # 8. Section 21 Movement Efficiency Limitation
        self.engine.add_node(NodeModel(
            id="limitation_movement_efficiency",
            label="Movement Efficiency: Gated",
            node_type=Section25NodeType.METRIC.value,
            category=NodeCategory.LIMITATION.value,
            confidence=1.0,
            properties={
                "value": "NOT_RELIABLY_MEASURABLE",
                "unit": "status",
                "confidence": 1.0,
                "source": "Section 21 Master Biomechanics Specification",
                "timestamp_or_frame_range": "Full Video Recording",
                "calculation_method": "Single-player camera recording cannot verify rally boundaries or retrieval outcomes"
            },
            status="invalidated"
        ))
        self.engine.add_edge(EdgeModel(
            id="edge_movement_to_eff_lim",
            source="movement_dynamics",
            target="limitation_movement_efficiency",
            relation_type="indicates",
            confidence=1.0,
            evidence="Section 21 integrity constraint: no fabricated efficiency ratios"
        ))

        # 9. Hypotheses & Recommendations
        # 9a. Standard Kinematic Hypotheses
        hypo_list = hypotheses or [
            "H1_KINEMATICS: Landmark trajectories smoothed via Savitzky-Golay filter to isolate true athletic velocity peaks."
        ]
        for h_idx, hypo_text in enumerate(hypo_list):
            h_id = f"hypo_{h_idx+1}"
            self.engine.add_node(NodeModel(
                id=h_id,
                label=f"Hypothesis #{h_idx+1}: {hypo_text[:32]}...",
                node_type=Section25NodeType.HYPOTHESIS.value,
                category=NodeCategory.HYPOTHESIS.value,
                confidence=0.65,
                properties={
                    "value": hypo_text,
                    "unit": "hypothesis_statement",
                    "confidence": 0.65,
                    "source": "SAAR Reasoning Engine (Section 28)",
                    "timestamp_or_frame_range": "Longitudinal / Session Scope",
                    "calculation_method": "Empirical inductive reasoning over detected kinematics and shot distribution"
                },
                status="hypothesis"
            ))
            self.engine.add_edge(EdgeModel(
                id=f"edge_dist_to_{h_id}",
                source="metric_shot_distribution",
                target=h_id,
                relation_type="supports",
                confidence=0.65,
                evidence="Stroke distribution and kinematic trends support working hypothesis"
            ))

        # 9b. Section 11 Multi-Signal Spatial Hypothesis Gate (Left-Space Underutilization)
        spatial_gate = BadmintonHypothesisEngine.evaluate_left_space_underutilization(
            court_calibration=court_calibration,
            movement_metrics=movement_metrics,
            shot_metrics=shot_metrics,
            shots=shots
        )
        if spatial_gate.is_asserted:
            self.engine.add_node(NodeModel(
                id=spatial_gate.hypothesis_id,
                label=spatial_gate.title,
                node_type=Section25NodeType.HYPOTHESIS.value,
                category=NodeCategory.HYPOTHESIS.value,
                confidence=spatial_gate.node_properties.get("confidence", 0.72),
                properties=spatial_gate.node_properties,
                status="hypothesis"
            ))
            self.engine.add_edge(EdgeModel(
                id="edge_movement_to_hypo_left_space",
                source="movement_dynamics",
                target=spatial_gate.hypothesis_id,
                relation_type="supports",
                confidence=0.85,
                evidence="Observed court occupancy and recovery bias corroborate spatial hypothesis"
            ))
            self.engine.add_edge(EdgeModel(
                id="edge_shot_dist_to_hypo_left_space",
                source="metric_shot_distribution",
                target=spatial_gate.hypothesis_id,
                relation_type="supports",
                confidence=0.88,
                evidence="Shot target placement skew corroborates spatial hypothesis"
            ))


        rec_list = recommendations or list(quality.issues if quality else [])
        if not rec_list:
            rec_list = ["Maintain active ready stance and complete follow-through on overhead strokes."]
        for r_idx, rec_text in enumerate(rec_list):
            r_id = f"rec_{r_idx+1}"
            self.engine.add_node(NodeModel(
                id=r_id,
                label=f"Rec #{r_idx+1}: {rec_text[:32]}...",
                node_type=Section25NodeType.RECOMMENDATION.value,
                category=NodeCategory.RECOMMENDATION.value,
                confidence=0.85,
                properties={
                    "value": rec_text,
                    "unit": "recommendation_cue",
                    "confidence": 0.85,
                    "source": "SAAR Biomechanical Intelligence",
                    "timestamp_or_frame_range": "Technique Intervention",
                    "calculation_method": "Expert coaching cue mapped to observed movement & stroke patterns"
                },
                status="confirmed"
            ))
            # Connect recommendation to player or first hypothesis
            rec_source = "hypo_1" if hypo_list else "metric_shot_distribution"
            self.engine.add_edge(EdgeModel(
                id=f"edge_{rec_source}_to_{r_id}",
                source=rec_source,
                target=r_id,
                relation_type="causes",
                confidence=0.80,
                evidence="Actionable cue derived from biomechanical findings"
            ))

        return self.engine.export_state(step_count=len(shots))
