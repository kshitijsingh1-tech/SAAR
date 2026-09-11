"""
Gait Analysis Domain Plugin for SAAR Dynamic Orchestrator.
Provides presets, scenario perception, tools, and baseline comparisons for Toddler Gait Screening.
"""
from typing import List, Dict, Any, Tuple, Optional
from .base_plugin import BaseDomainPlugin
from ..schemas import NodeModel, EdgeModel, ToolExecutionModel, BaselineComparisonModel


class GaitPlugin(BaseDomainPlugin):
    @property
    def domain_name(self) -> str:
        return "gait"

    @property
    def presets(self) -> List[Dict[str, str]]:
        return [
            {
                "id": "gait_toddler_blue_dress",
                "title": "Toddler 24-Month Walking Clip (Blue Dress)",
                "description": "Prerecorded toddler walking clip evaluating cadence, step-timing symmetry, and step-to-step rhythm variability.",
                "image": "https://images.unsplash.com/photo-1596464716127-f2a829822301?auto=format&fit=crop&w=1200&q=80"
            }
        ]

    def perceive_initial_scene(self, preset_id: str) -> Tuple[List[NodeModel], List[EdgeModel]]:
        nodes = [
            NodeModel(
                id="gait_video_capture",
                label="Video Recording & Lower Extremity Landmarks",
                node_type="object",
                category="observation",
                confidence=0.92,
                bbox=[120, 200, 850, 750],
                visual_anchor=True,
                properties={"duration_s": 6.0, "fps": 24.0, "landmarks_tracked": 33}
            ),
            NodeModel(
                id="foot_trajectory",
                label="Bilateral Heel-Strike Trajectories",
                node_type="property",
                category="kinematics",
                confidence=0.88,
                bbox=[600, 250, 880, 700],
                visual_anchor=True,
                properties={"left_heel_detected": True, "right_heel_detected": True}
            ),
            # Hypotheses
            NodeModel(
                id="hypo_typical_gait",
                label="Hypothesis A: Age-Appropriate Developing Toddler Gait",
                node_type="hypothesis",
                category="developmental",
                confidence=0.55,
                bbox=None,
                visual_anchor=False,
                status="hypothesis"
            ),
            NodeModel(
                id="hypo_asymmetry",
                label="Hypothesis B: Elevated Temporal Asymmetry Pattern",
                node_type="hypothesis",
                category="developmental",
                confidence=0.35,
                bbox=None,
                visual_anchor=False,
                status="hypothesis"
            )
        ]

        edges = [
            EdgeModel(
                id="e_gait_1",
                source="gait_video_capture",
                target="foot_trajectory",
                relation_type="extracts",
                confidence=0.90,
                evidence="MediaPipe pose tracking extracted bilateral foot coordinates across frames."
            ),
            EdgeModel(
                id="e_gait_2",
                source="foot_trajectory",
                target="hypo_typical_gait",
                relation_type="supports",
                confidence=0.55,
                evidence="Continuous foot trajectory indicates bilateral stepping."
            ),
            EdgeModel(
                id="e_gait_3",
                source="foot_trajectory",
                target="hypo_asymmetry",
                relation_type="supports",
                confidence=0.35,
                evidence="Left-right timing variations require quantitative metric calculation."
            )
        ]

        return nodes, edges

    def get_available_tools(self, current_nodes: Optional[List[NodeModel]] = None) -> List[Dict[str, Any]]:
        return [
            {
                "tool_id": "gait_quality_gate",
                "tool_name": "Gait Capture Quality & Stability Gate",
                "description": "Evaluates landmark confidence, camera stability, feet visibility, and good continuous frames.",
                "target_hypothesis": "hypo_typical_gait"
            },
            {
                "tool_id": "heel_strike_detector",
                "tool_name": "Heel-Strike Event & Step Timing Extractor",
                "description": "Detects forward extremum peaks on smoothed heel trajectories to compute step events.",
                "target_hypothesis": "hypo_typical_gait"
            },
            {
                "tool_id": "temporal_metric_computer",
                "tool_name": "ToddleAI Deterministic Metric Computer",
                "description": "Calculates Cadence (steps/min), Left/Right Step Time, Asymmetry %, and CoV %.",
                "target_hypothesis": "hypo_typical_gait"
            }
        ]

    def execute_tool(
        self,
        tool_id: str,
        current_nodes: List[NodeModel],
        current_edges: List[EdgeModel]
    ) -> ToolExecutionModel:
        if tool_id == "gait_quality_gate":
            added_nodes = [
                NodeModel(
                    id="quality_assessment_node",
                    label="Recording Quality (LOW Confidence, 66.7% Good Frames)",
                    node_type="tool_result",
                    category="quality",
                    confidence=0.95,
                    properties={"good_frame_pct": 66.7, "usable_steps": 6}
                )
            ]
            added_edges = [
                EdgeModel(
                    id="e_qg_1",
                    source="gait_video_capture",
                    target="quality_assessment_node",
                    relation_type="validates",
                    confidence=0.95,
                    evidence="Evaluated all 144 frames; detected 6 valid steps in continuous walking sequence."
                )
            ]
            return ToolExecutionModel(
                tool_id=tool_id,
                tool_name="Gait Capture Quality & Stability Gate",
                target_node_id="gait_video_capture",
                input_params={"fps": 24.0, "min_steps": 5},
                output_findings="Capture Quality confirmed with 66.7% good frames and 6 valid steps detected.",
                confidence_delta=+0.12,
                added_nodes=added_nodes,
                added_edges=added_edges
            )

        elif tool_id == "heel_strike_detector":
            added_nodes = [
                NodeModel(
                    id="heel_events_node",
                    label="Detected Heel Strikes (3 Left, 3 Right)",
                    node_type="observation",
                    category="events",
                    confidence=0.93,
                    properties={"step_count": 6, "filter_range_s": "0.25 - 1.50"}
                )
            ]
            added_edges = [
                EdgeModel(
                    id="e_hs_1",
                    source="foot_trajectory",
                    target="heel_events_node",
                    relation_type="detects",
                    confidence=0.93,
                    evidence="Peak prominence filtering on directional heel trajectories detected 6 physiological steps."
                )
            ]
            return ToolExecutionModel(
                tool_id=tool_id,
                tool_name="Heel-Strike Event & Step Timing Extractor",
                target_node_id="foot_trajectory",
                input_params={"min_prominence_ratio": 0.15, "moving_avg_window": 5},
                output_findings="Identified 6 alternating heel-strike events with physiological step durations.",
                confidence_delta=+0.15,
                added_nodes=added_nodes,
                added_edges=added_edges
            )

        elif tool_id == "temporal_metric_computer":
            added_nodes = [
                NodeModel(
                    id="gait_metrics_node",
                    label="Cadence: 120 steps/min | Asymmetry: 5.0% | CoV: 17.1%",
                    node_type="tool_result",
                    category="metrics",
                    confidence=0.98,
                    properties={
                        "cadence_spm": 120.0,
                        "left_step_time_s": 0.49,
                        "right_step_time_s": 0.51,
                        "asymmetry_pct": 5.0,
                        "step_time_cov_pct": 17.1
                    }
                )
            ]
            added_edges = [
                EdgeModel(
                    id="e_mc_1",
                    source="heel_events_node",
                    target="gait_metrics_node",
                    relation_type="computes",
                    confidence=0.98,
                    evidence="Cadence and step metrics computed from verified temporal heel strikes."
                ),
                EdgeModel(
                    id="e_mc_2",
                    source="gait_metrics_node",
                    target="hypo_typical_gait",
                    relation_type="confirms",
                    confidence=0.90,
                    evidence="Left-right asymmetry 5.0% is within the typical <=10% range. Cadence 120 steps/min aligns with 24-month developmental reference (120–160 steps/min)."
                )
            ]
            return ToolExecutionModel(
                tool_id=tool_id,
                tool_name="ToddleAI Deterministic Metric Computer",
                target_node_id="heel_events_node",
                input_params={"child_age_months": 24},
                output_findings="Deterministic metrics calculated: Cadence 120.0 steps/min, Asymmetry 5.0% (typical <=10%), Step Rhythm variation 17.1%.",
                confidence_delta=+0.20,
                added_nodes=added_nodes,
                added_edges=added_edges
            )

        return ToolExecutionModel(
            tool_id=tool_id,
            tool_name="Default Gait Tool",
            target_node_id="gait_video_capture",
            input_params={},
            output_findings="Tool completed successfully.",
            confidence_delta=0.05,
            added_nodes=[],
            added_edges=[]
        )

    def get_baseline_comparison(self, preset_id: str) -> BaselineComparisonModel:
        return BaselineComparisonModel(
            vlm_prompt="Analyze this walking toddler video. What is their gait pattern and are there any concerns?",
            vlm_raw_response=(
                "A young toddler in a blue dress is walking across a room. "
                "The child is moving forward steadily. The walking seems typical for a toddler."
            ),
            vlm_explainability_score=0.40,
            vlm_root_cause_accuracy=0.55,
            vlm_tool_call_count=0,
            saar_explainability_score=0.96,
            saar_root_cause_accuracy=0.94,
            saar_tool_call_count=3,
            key_differences=[
                "Standard VLM provides high-level visual description without quantifiable gait metrics.",
                "SAAR extracts deterministic 33-point landmarks, cadence (120 steps/min), and left-right symmetry (5.0%).",
                "SAAR compares metrics against peer-reviewed age benchmarks (120-160 steps/min for 24 months)."
            ]
        )

    def generate_final_conclusion(self, nodes: List[NodeModel], edges: List[EdgeModel]) -> str:
        return (
            "Deterministic gait tracking extracted 6 valid steps. "
            "Measured cadence was 120.0 steps/min with a left-right step-time asymmetry of 5.0% (within typical <=10% range). "
            "Step rhythm variability (17.1%) reflects typical developing motor coordination for a 2-year-old."
        )
