from typing import List, Dict, Any, Tuple
from .base_plugin import BaseDomainPlugin
from ..schemas import NodeModel, EdgeModel, ToolExecutionModel, BaselineComparisonModel

class AgriculturePlugin(BaseDomainPlugin):
    @property
    def domain_name(self) -> str:
        return "agriculture"

    @property
    def presets(self) -> List[Dict[str, str]]:
        return [
            {
                "id": "agri_tomato_chlorosis",
                "title": "30-Day Tomato Crop Failure & Leaf Chlorosis",
                "description": "Greenhouse tomato crop exhibiting severe interveinal leaf yellowing, high substrate moisture, and root stagnation.",
                "image": "https://images.unsplash.com/photo-1592417817098-8f3d69102553?auto=format&fit=crop&w=1200&q=80"
            }
        ]

    def perceive_initial_scene(self, preset_id: str) -> Tuple[List[NodeModel], List[EdgeModel]]:
        nodes = [
            NodeModel(id="leaf_chlorosis_01", label="Interveinal Leaf Chlorosis", node_type="observation", category="pathology", confidence=0.96, properties={"pattern": "yellowing between green primary veins", "affected_area": "upper foliage"}),
            NodeModel(id="soil_moisture_sensor_01", label="Root Zone Moisture Sensor (48% VWC)", node_type="property", category="measurement", confidence=0.94, properties={"vwc_percent": 48.2, "saturation_threshold": 35.0}),
            NodeModel(id="soil_ph_sensor_01", label="Substrate pH Sensor (pH 7.85)", node_type="property", category="measurement", confidence=0.92, properties={"ph": 7.85, "condition": "calcareous / alkaline"}),
            NodeModel(id="irrigation_emitter_01", label="Automated Drip Irrigation Line", node_type="object", category="infrastructure", confidence=0.98, properties={"regime": "continuous pulse", "flow_liters_hr": 2.8}),
            
            # Hypotheses
            NodeModel(id="hypo_iron_deficiency", label="Hypothesis: Bicarbonate-Induced Fe²⁺ Bioavailability Deficit", node_type="hypothesis", category="nutritional_disorder", confidence=0.45, status="hypothesis"),
            NodeModel(id="hypo_nitrogen_burn", label="Hypothesis: Root-Burn via Excessive Nitrogen Application", node_type="hypothesis", category="chemical_stress", confidence=0.35, status="hypothesis")
        ]

        edges = [
            EdgeModel(id="e_agri_1", source="irrigation_emitter_01", target="soil_moisture_sensor_01", relation_type="causes", confidence=0.95, evidence="Continuous drip emitter discharge keeps substrate constantly waterlogged (>45% VWC)."),
            EdgeModel(id="e_agri_2", source="soil_moisture_sensor_01", target="hypo_iron_deficiency", relation_type="supports", confidence=0.60, evidence="Persistent waterlogging induces root hypoxia, inactivating rhizosphere proton extrusion pumps."),
            EdgeModel(id="e_agri_3", source="soil_ph_sensor_01", target="hypo_iron_deficiency", relation_type="supports", confidence=0.65, evidence="Alkaline pH (>7.5) precipitates ferric iron into insoluble hydroxides Fe(OH)3."),
            EdgeModel(id="e_agri_4", source="hypo_iron_deficiency", target="leaf_chlorosis_01", relation_type="causes", confidence=0.75, evidence="Iron is an essential cofactor for delta-aminolevulinic acid dehydratase; deficit prevents chlorophyll synthesis.")
        ]
        return nodes, edges

    def get_available_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "tool_id": "rhizosphere_anoxia_simulator",
                "tool_name": "Root-Zone Oxygenation & ATP Pump Simulator",
                "description": "Simulates soil gas diffusion and root ATP yield under prolonged saturation (>40% moisture).",
                "target_hypothesis": "hypo_iron_deficiency"
            },
            {
                "tool_id": "rhizosphere_ph_speciation_tool",
                "tool_name": "Ferric/Ferrous Iron Chemical Equilibrium Tool",
                "description": "Calculates Fe²⁺ bioavailability and Fe(III)-chelate reductase enzymatic activity across pH gradients.",
                "target_hypothesis": "hypo_iron_deficiency"
            },
            {
                "tool_id": "foliar_spectral_reflectance",
                "tool_name": "Multispectral Foliar Reflectance & SPAD Diagnostic",
                "description": "Analyzes red-edge chlorophyll index (NDRE) and anthocyanin ratios to confirm nutrient vs pathogen etiology.",
                "target_hypothesis": "hypo_iron_deficiency"
            }
        ]

    def execute_tool(self, tool_id: str, current_nodes: List[NodeModel], current_edges: List[EdgeModel]) -> ToolExecutionModel:
        if tool_id == "rhizosphere_anoxia_simulator":
            added_nodes = [
                NodeModel(
                    id="tool_hypoxia_res",
                    label="Root Anoxia Detected: Dissolved O₂ < 0.8 mg/L",
                    node_type="tool_result",
                    category="measurement",
                    confidence=0.96,
                    properties={"dissolved_oxygen_mg_l": 0.72, "atp_inhibition_pct": 82.0}
                )
            ]
            added_edges = [
                EdgeModel(
                    id="e_tool_agri_1",
                    source="soil_moisture_sensor_01",
                    target="tool_hypoxia_res",
                    relation_type="causes",
                    confidence=0.96,
                    evidence="Waterlogging for >96 consecutive hours depleted soil pore oxygen, triggering root anaerobic distress."
                ),
                EdgeModel(
                    id="e_tool_agri_2",
                    source="tool_hypoxia_res",
                    target="hypo_iron_deficiency",
                    relation_type="supports",
                    confidence=0.91,
                    evidence="Root ATP depletion directly shuts down plasma membrane H+-ATPase required for nutrient uptake."
                )
            ]
            return ToolExecutionModel(
                tool_id=tool_id,
                tool_name="Root-Zone Oxygenation & ATP Pump Simulator",
                target_node_id="hypo_iron_deficiency",
                input_params={"substrate_porosity": 0.45, "vwc_measured": 0.482, "hours_saturated": 120},
                output_findings="Rhizosphere simulation demonstrates critical anoxia (DO = 0.72 mg/L). Root aerobic respiration impaired by 82%.",
                confidence_delta=+0.25,
                added_nodes=added_nodes,
                added_edges=added_edges
            )

        elif tool_id == "rhizosphere_ph_speciation_tool":
            added_nodes = [
                NodeModel(
                    id="fe_insolubility_detected",
                    label="Bioavailable Fe²⁺: 0.04 ppm (-91% deficit)",
                    node_type="observation",
                    category="chemical_state",
                    confidence=0.95,
                    properties={"fe2_soluble_ppm": 0.04, "chelate_reductase_activity_pct": 14.0}
                )
            ]
            added_edges = [
                EdgeModel(
                    id="e_tool_agri_3",
                    source="soil_ph_sensor_01",
                    target="fe_insolubility_detected",
                    relation_type="causes",
                    confidence=0.94,
                    evidence="Substrate pH 7.85 and high bicarbonate neutralize rhizosphere acidification, blocking Fe³⁺ reduction."
                ),
                EdgeModel(
                    id="e_tool_agri_4",
                    source="fe_insolubility_detected",
                    target="hypo_iron_deficiency",
                    relation_type="supports",
                    confidence=0.97,
                    evidence="Bioavailable ferrous iron concentration of 0.04 ppm is far below the minimum 0.5 ppm threshold for Lycopersicon esculentum."
                )
            ]
            return ToolExecutionModel(
                tool_id=tool_id,
                tool_name="Ferric/Ferrous Iron Chemical Equilibrium Tool",
                target_node_id="hypo_iron_deficiency",
                input_params={"ph": 7.85, "bicarbonate_meq_l": 4.6, "total_iron_ppm": 2.1},
                output_findings="Chemical speciation confirms that 98% of rhizosphere iron is bound as insoluble ferric precipitates. Available Fe²⁺ is only 0.04 ppm.",
                confidence_delta=+0.30,
                added_nodes=added_nodes,
                added_edges=added_edges
            )

        else: # foliar_spectral_reflectance
            added_nodes = [
                NodeModel(
                    id="ndre_chlorophyll_diagnostic",
                    label="NDRE: 0.18 (Severe Chlorosis; Anthocyanin Normal)",
                    node_type="observation",
                    category="spectral_diagnostic",
                    confidence=0.98,
                    properties={"ndre_index": 0.18, "chlorophyll_spad": 16.4, "pathogen_lesion_index": 0.02}
                )
            ]
            added_edges = [
                EdgeModel(
                    id="e_tool_agri_5",
                    source="ndre_chlorophyll_diagnostic",
                    target="hypo_nitrogen_burn",
                    relation_type="contradicts",
                    confidence=0.92,
                    evidence="Absence of leaf-margin necrosis and normal anthocyanin levels rule out chemical fertilizer burn."
                ),
                EdgeModel(
                    id="e_tool_agri_6",
                    source="ndre_chlorophyll_diagnostic",
                    target="hypo_iron_deficiency",
                    relation_type="supports",
                    confidence=0.96,
                    evidence="Sharp interveinal green-to-yellow gradient confirms classical iron deficiency chlorosis."
                )
            ]
            return ToolExecutionModel(
                tool_id=tool_id,
                tool_name="Multispectral Foliar Reflectance & SPAD Diagnostic",
                target_node_id="hypo_iron_deficiency",
                input_params={"wavelength_red_nm": 670, "wavelength_red_edge_nm": 720, "wavelength_nir_nm": 790},
                output_findings="NDRE score of 0.18 confirms 65% loss of photosynthetic chlorophyll a/b. Pathogen signatures absent. Nitrogen burn ruled out.",
                confidence_delta=+0.15,
                added_nodes=added_nodes,
                added_edges=added_edges
            )

    def generate_final_conclusion(self, nodes: List[NodeModel], edges: List[EdgeModel]) -> str:
        return (
            "Autonomous investigation completed. Root cause identified: Chronic rhizosphere waterlogging "
            "(>48% VWC) combined with substrate alkalinity (pH 7.85) triggered dual-action iron deficiency chlorosis. "
            "Prolonged moisture induced root anoxia (DO < 0.8 mg/L), halting active H+-ATPase proton pumping, "
            "while high bicarbonate precipitated 98% of available iron into insoluble Fe(OH)3. "
            "Corrective action: Reduce drip cycle frequency to restore soil aeration (target VWC 28-32%) "
            "and apply Fe-EDDHA chelate formulated for alkaline substrates."
        )

    def get_baseline_comparison(self, preset_id: str) -> BaselineComparisonModel:
        return BaselineComparisonModel(
            domain="agriculture",
            preset_id=preset_id,
            vlm_prompt="Analyze this greenhouse tomato foliage image. What is the root cause of leaf yellowing and what corrective action is needed?",
            vlm_raw_response="Tomato foliage exhibits generalized yellowing. Suspected nitrogen deficiency or early blight pathogen infection.",
            vlm_explainability_score=0.32,
            vlm_root_cause_accuracy=0.38,
            vlm_tool_call_count=0,
            saar_explainability_score=0.98,
            saar_root_cause_accuracy=0.96,
            saar_tool_call_count=3,
            key_differences=[
                "Single-pass VLM misdiagnosed foliage yellowing as generic nitrogen deficiency or fungus.",
                "Saar dynamic loop tested and eliminated nitrogen burn and fungal lesions via multispectral NDRE diagnostic.",
                "Dispatched rhizosphere anoxia and pH speciation tools, uncovering sub-surface root hypoxia and Fe²⁺ bioavailability collapse."
            ]
        )
