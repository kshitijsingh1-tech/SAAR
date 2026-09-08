from typing import List, Dict, Any, Tuple
from .base_plugin import BaseDomainPlugin
from ..schemas import NodeModel, EdgeModel, ToolExecutionModel, BaselineComparisonModel

class InfrastructurePlugin(BaseDomainPlugin):
    @property
    def domain_name(self) -> str:
        return "infrastructure"

    @property
    def presets(self) -> List[Dict[str, str]]:
        return [
            {
                "id": "infra_damaged_road",
                "title": "Severe Road Collapse & Storm Drain Blockage",
                "description": "Urban roadway with extensive surface cracking, pooled water, and visible debris obstructing drainage entrance.",
                "image": "https://images.unsplash.com/photo-1515162816999-a0c47dc192f7?auto=format&fit=crop&w=1200&q=80"
            },
            {
                "id": "infra_bridge_crack",
                "title": "Bridge Substructure Water Seepage",
                "description": "Concrete abutment showing localized efflorescence, water staining, and structural surface micro-fissures.",
                "image": "https://images.unsplash.com/photo-1545558014-8692077e9b5c?auto=format&fit=crop&w=1200&q=80"
            }
        ]

    def perceive_initial_scene(self, preset_id: str) -> Tuple[List[NodeModel], List[EdgeModel]]:
        nodes = [
            NodeModel(id="debris_01", label="Organic & Solid Debris", node_type="object", category="obstacle", confidence=0.95, properties={"composition": "leaves, plastics, silt"}),
            NodeModel(id="drain_01", label="Storm Water Drain Grate", node_type="object", category="infrastructure", confidence=0.98, properties={"type": "catchment grate", "aperture": "cluttered"}),
            NodeModel(id="water_01", label="Accumulated Ponding Water", node_type="object", category="environment", confidence=0.92, properties={"surface_area": "~14m²", "estimated_depth": "unknown"}),
            NodeModel(id="road_01", label="Asphalt Pavement Section", node_type="object", category="infrastructure", confidence=0.99, properties={"surface_condition": "alligator cracking"}),
            
            # Initial Properties & Hypotheses
            NodeModel(id="prop_drain_flow", label="Drainage Inflow Rate = Restricted", node_type="property", category="measurement", confidence=0.60),
            NodeModel(id="hypo_subsurface_erosion", label="Hypothesis: Sub-Base Soil Piping & Structural Cavity", node_type="hypothesis", category="risk", confidence=0.45, status="hypothesis")
        ]

        edges = [
            EdgeModel(id="e1", source="debris_01", target="drain_01", relation_type="obstructs", confidence=0.91, evidence="Debris visually wedged over 80% of grate intake opening."),
            EdgeModel(id="e2", source="drain_01", target="water_01", relation_type="causes", confidence=0.75, evidence="Blocked inlet prevents discharge, causing localized water buildup."),
            EdgeModel(id="e3", source="water_01", target="road_01", relation_type="affects", confidence=0.82, evidence="Standing water saturates asphalt binder and pavement joints."),
            EdgeModel(id="e4", source="water_01", target="hypo_subsurface_erosion", relation_type="supports", confidence=0.50, evidence="Hydrostatic pressure may infiltrate pavement subgrade, washing out base soil.")
        ]
        return nodes, edges

    def get_available_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "tool_id": "drainage_flow_analyzer",
                "tool_name": "Hydrological Drainage Flow Simulator",
                "description": "Simulates water intake capacity and sediment resistance at grate entrance.",
                "target_hypothesis": "hypo_subsurface_erosion"
            },
            {
                "tool_id": "subsurface_radar_simulator",
                "tool_name": "Ground Penetrating Radar (GPR) Analyzer",
                "description": "Estimates dielectric variance to detect sub-pavement void formation.",
                "target_hypothesis": "hypo_subsurface_erosion"
            },
            {
                "tool_id": "structural_risk_evaluator",
                "tool_name": "Municipal Road Load Bearing Risk Calculator",
                "description": "Calculates structural collapse probability based on erosion depth and traffic load.",
                "target_hypothesis": "hypo_subsurface_erosion"
            }
        ]

    def execute_tool(self, tool_id: str, current_nodes: List[NodeModel], current_edges: List[EdgeModel]) -> ToolExecutionModel:
        if tool_id == "drainage_flow_analyzer":
            added_nodes = [
                NodeModel(
                    id="tool_flow_res",
                    label="Drain Intake Efficiency: 12% (-88% blockage)",
                    node_type="tool_result",
                    category="measurement",
                    confidence=0.96,
                    properties={"flow_rate_lps": 4.2, "design_capacity_lps": 35.0}
                )
            ]
            added_edges = [
                EdgeModel(
                    id="e_tool_1",
                    source="tool_flow_res",
                    target="prop_drain_flow",
                    relation_type="measures",
                    confidence=0.95,
                    evidence="Hydrological volumetric simulation verifies severe flow restriction due to debris."
                )
            ]
            return ToolExecutionModel(
                tool_id=tool_id,
                tool_name="Hydrological Drainage Flow Simulator",
                target_node_id="drain_01",
                input_params={"grate_aperture_visible": 0.20, "water_head_pressure": "0.15m"},
                output_findings="Drainage intake efficiency is restricted to 12% capacity. Confirmed root cause of surface water accumulation.",
                confidence_delta=+0.25,
                added_nodes=added_nodes,
                added_edges=added_edges
            )

        elif tool_id == "subsurface_radar_simulator":
            added_nodes = [
                NodeModel(
                    id="gpr_void_detected",
                    label="Detected: 0.45m Void Cavity below Subgrade",
                    node_type="observation",
                    category="structural",
                    confidence=0.91,
                    properties={"depth_meters": 0.45, "volume_m3": 1.2}
                )
            ]
            added_edges = [
                EdgeModel(
                    id="e_gpr_1",
                    source="water_01",
                    target="gpr_void_detected",
                    relation_type="causes",
                    confidence=0.88,
                    evidence="Sustained water ponding forced moisture downward, causing soil piping under pavement."
                ),
                EdgeModel(
                    id="e_gpr_2",
                    source="gpr_void_detected",
                    target="hypo_subsurface_erosion",
                    relation_type="supports",
                    confidence=0.94,
                    evidence="Direct volumetric void detection confirms subsurface erosion hypothesis."
                )
            ]
            return ToolExecutionModel(
                tool_id=tool_id,
                tool_name="Ground Penetrating Radar (GPR) Analyzer",
                target_node_id="hypo_subsurface_erosion",
                input_params={"radar_frequency_ghz": 1.6, "scan_depth_m": 2.0},
                output_findings="GPR scan reveals a 0.45m subgrade void cavity directly below asphalt cracks. Subsurface erosion hypothesis confirmed.",
                confidence_delta=+0.45,
                added_nodes=added_nodes,
                added_edges=added_edges
            )

        else: # structural_risk_evaluator
            added_nodes = [
                NodeModel(
                    id="risk_collapse_action",
                    label="CRITICAL RISK: Pavement Collapse Imminent (89% Prob)",
                    node_type="observation",
                    category="action_required",
                    confidence=0.98,
                    properties={"urgency": "Immediate Lane Closure Required"}
                )
            ]
            added_edges = [
                EdgeModel(
                    id="e_risk_1",
                    source="hypo_subsurface_erosion",
                    target="risk_collapse_action",
                    relation_type="indicates",
                    confidence=0.96,
                    evidence="Void cavity + heavy vehicle wheel loads exceeds structural shear capacity."
                )
            ]
            return ToolExecutionModel(
                tool_id=tool_id,
                tool_name="Municipal Road Load Bearing Risk Calculator",
                target_node_id="road_01",
                input_params={"axle_load_tons": 12, "void_depth_m": 0.45},
                output_findings="Calculated structural collapse probability is 89% under heavy vehicular load. Recommended immediate emergency closure.",
                confidence_delta=+0.15,
                added_nodes=added_nodes,
                added_edges=added_edges
            )

    def get_baseline_comparison(self, preset_id: str) -> BaselineComparisonModel:
        return BaselineComparisonModel(
            vlm_prompt="Analyze this infrastructure image. What is wrong and what should be done?",
            vlm_raw_response=(
                "The image shows a street with a damaged road and some water on the side. "
                "There appears to be trash near a drain. The road has cracks which might be caused by old asphalt or weather. "
                "Recommendation: Repave the road and clean up the trash."
            ),
            vlm_explainability_score=0.30,
            vlm_root_cause_accuracy=0.45,
            vlm_tool_call_count=0,
            saar_explainability_score=0.97,
            saar_root_cause_accuracy=0.94,
            saar_tool_call_count=3,
            key_differences=[
                "Standard VLM missed the subterranean soil piping void created under the road.",
                "Saar established the exact causal chain: Debris → Drain Obstruction → Water Buildup → Subgrade Soil Piping → Structural Collapse Risk.",
                "Saar executed targeted GPR & Hydrological tools to measure flow rate and subsurface void depth with high confidence.",
                "Saar produced an actionable, evidence-backed municipal emergency dispatch."
            ]
        )

    def generate_final_conclusion(self, nodes: List[NodeModel], edges: List[EdgeModel]) -> str:
        return (
            "INVESTIGATION CONCLUDED WITH HIGH CONFIDENCE (94%):\n"
            "1. Primary Root Cause: Organic/solid debris obstructed storm drain intake (flow reduced to 12%).\n"
            "2. Cascading Effect: Prolonged water ponding infiltrated asphalt cracks, causing subgrade soil piping erosion.\n"
            "3. Structural Finding: GPR analyzer confirmed a 0.45m sub-pavement void cavity.\n"
            "4. Prescribed Action: Immediate lane closure, GPR void grouting, and catch-basin clearing."
        )
