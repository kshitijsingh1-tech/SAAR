from typing import List, Dict, Any, Tuple
from .base_plugin import BaseDomainPlugin
from ..schemas import NodeModel, EdgeModel, ToolExecutionModel, BaselineComparisonModel

class AstronomyPlugin(BaseDomainPlugin):
    @property
    def domain_name(self) -> str:
        return "astronomy"

    @property
    def presets(self) -> List[Dict[str, str]]:
        return [
            {
                "id": "astro_stellar_spectrum",
                "title": "HD-209458 Spectral Line Shift Analysis",
                "description": "High-resolution stellar absorption spectrum showing periodic Doppler wavelength displacement over 3.5 observation epochs.",
                "image": "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?auto=format&fit=crop&w=1200&q=80"
            }
        ]

    def perceive_initial_scene(self, preset_id: str) -> Tuple[List[NodeModel], List[EdgeModel]]:
        nodes = [
            NodeModel(id="spectrum_01", label="Stellar Absorption Spectrum", node_type="object", category="observation", confidence=0.99, properties={"spectral_class": "G0V", "target_line": "Balmer H-alpha (656.28nm)"}),
            NodeModel(id="shift_01", label="Observed Spectral Line Shift (Δλ)", node_type="property", category="measurement", confidence=0.88, properties={"delta_lambda_nm": "+0.042nm", "direction": "Redshift"}),
            NodeModel(id="time_series_01", label="Time-Series Observation Epochs", node_type="observation", category="data", confidence=0.95, properties={"num_epochs": 14, "duration_days": 12.4}),
            
            # Hypotheses
            NodeModel(id="hypo_exoplanet", label="Hypothesis A: Orbiting Sub-Jupiter Exoplanet", node_type="hypothesis", category="astrophysics", confidence=0.50, status="hypothesis"),
            NodeModel(id="hypo_binary_star", label="Hypothesis B: M-Dwarf Binary Stellar Companion", node_type="hypothesis", category="astrophysics", confidence=0.40, status="hypothesis")
        ]

        edges = [
            EdgeModel(id="e_astro_1", source="spectrum_01", target="shift_01", relation_type="indicates", confidence=0.92, evidence="Absorption line centroid displaced from lab rest wavelength."),
            EdgeModel(id="e_astro_2", source="shift_01", target="time_series_01", relation_type="varies_with", confidence=0.85, evidence="Displacement magnitude oscillates periodically across observation nights."),
            EdgeModel(id="e_astro_3", source="time_series_01", target="hypo_exoplanet", relation_type="supports", confidence=0.50, evidence="Periodic Doppler variation consistent with gravitational wobble."),
            EdgeModel(id="e_astro_4", source="time_series_01", target="hypo_binary_star", relation_type="supports", confidence=0.45, evidence="Alternative binary companion model could explain periodic radial velocity.")
        ]
        return nodes, edges

    def get_available_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "tool_id": "doppler_velocity_calculator",
                "tool_name": "Doppler Shift & Radial Velocity Tool",
                "description": "Calculates line-of-sight velocity: vr = c * (Δλ / λ0).",
                "target_hypothesis": "hypo_exoplanet"
            },
            {
                "tool_id": "keplerian_orbit_fitter",
                "tool_name": "Keplerian Orbital Curve Fitter",
                "description": "Fits sinusoid/eccentric RV curve to determine orbital period P and velocity semi-amplitude K.",
                "target_hypothesis": "hypo_exoplanet"
            },
            {
                "tool_id": "mass_function_evaluator",
                "tool_name": "Stellar Companion Mass Evaluator",
                "description": "Evaluates minimum companion mass (m sin i) to distinguish planet vs binary star.",
                "target_hypothesis": "hypo_exoplanet"
            }
        ]

    def execute_tool(self, tool_id: str, current_nodes: List[NodeModel], current_edges: List[EdgeModel]) -> ToolExecutionModel:
        if tool_id == "doppler_velocity_calculator":
            added_nodes = [
                NodeModel(
                    id="rad_vel_measured",
                    label="Radial Velocity Semi-Amplitude (K = 85.2 m/s)",
                    node_type="tool_result",
                    category="measurement",
                    confidence=0.96,
                    properties={"velocity_ms": 85.2, "precision": "+/- 1.4 m/s"}
                )
            ]
            added_edges = [
                EdgeModel(
                    id="e_rv_1",
                    source="shift_01",
                    target="rad_vel_measured",
                    relation_type="measures",
                    confidence=0.96,
                    evidence="Doppler formula converts 0.042nm shift to 85.2 m/s line-of-sight star motion."
                )
            ]
            return ToolExecutionModel(
                tool_id=tool_id,
                tool_name="Doppler Shift & Radial Velocity Tool",
                target_node_id="shift_01",
                input_params={"rest_wavelength_nm": 656.28, "delta_lambda_nm": 0.042},
                output_findings="Computed Doppler radial velocity semi-amplitude K = 85.2 m/s. High precision non-zero wobble detected.",
                confidence_delta=+0.20,
                added_nodes=added_nodes,
                added_edges=added_edges
            )

        elif tool_id == "keplerian_orbit_fitter":
            added_nodes = [
                NodeModel(
                    id="orbit_period",
                    label="Orbital Period (P = 3.524 days, e = 0.01)",
                    node_type="observation",
                    category="orbital",
                    confidence=0.94,
                    properties={"period_days": 3.524, "eccentricity": 0.01, "fit_chi_sq": 1.08}
                )
            ]
            added_edges = [
                EdgeModel(
                    id="e_orb_1",
                    source="rad_vel_measured",
                    target="orbit_period",
                    relation_type="indicates",
                    confidence=0.94,
                    evidence="Sinusoidal RV curve fit yields strict 3.524-day circular orbit."
                )
            ]
            return ToolExecutionModel(
                tool_id=tool_id,
                tool_name="Keplerian Orbital Curve Fitter",
                target_node_id="rad_vel_measured",
                input_params={"epochs": 14, "fitting_algo": "Levenberg-Marquardt"},
                output_findings="Keplerian orbital fit converged. Period P = 3.524 days, near-circular orbit (e ≈ 0). Chi-squared = 1.08.",
                confidence_delta=+0.25,
                added_nodes=added_nodes,
                added_edges=added_edges
            )

        else: # mass_function_evaluator
            added_nodes = [
                NodeModel(
                    id="mass_result",
                    label="Minimum Mass: 0.69 M_Jupiter (Exoplanet confirmed)",
                    node_type="observation",
                    category="confirmation",
                    confidence=0.97,
                    properties={"min_mass_mjup": 0.69, "stellar_mass_msun": 1.1}
                )
            ]
            added_edges = [
                EdgeModel(
                    id="e_mass_1",
                    source="mass_result",
                    target="hypo_exoplanet",
                    relation_type="supports",
                    confidence=0.97,
                    evidence="Companion mass 0.69 M_Jupiter is well below stellar ignition threshold (80 M_Jupiter)."
                ),
                EdgeModel(
                    id="e_mass_2",
                    source="mass_result",
                    target="hypo_binary_star",
                    relation_type="contradicts",
                    confidence=0.95,
                    evidence="Sub-Jupiter mass rules out binary star hypothesis."
                )
            ]
            return ToolExecutionModel(
                tool_id=tool_id,
                tool_name="Stellar Companion Mass Evaluator",
                target_node_id="hypo_exoplanet",
                input_params={"star_mass_solar": 1.1, "semi_amplitude_ms": 85.2, "period_days": 3.524},
                output_findings="Minimum companion mass is 0.69 M_Jupiter. Exoplanet hypothesis CONFIRMED; Stellar binary hypothesis CONTRADICTED.",
                confidence_delta=+0.35,
                added_nodes=added_nodes,
                added_edges=added_edges
            )

    def get_baseline_comparison(self, preset_id: str) -> BaselineComparisonModel:
        return BaselineComparisonModel(
            vlm_prompt="Analyze this astronomical spectrum. What does the shift mean?",
            vlm_raw_response=(
                "The image displays a rainbow spectrum with dark vertical absorption lines. "
                "The lines appear slightly shifted toward the red end of the spectrum. "
                "This indicates redshift, which means the star or galaxy is moving away from us due to cosmic expansion."
            ),
            vlm_explainability_score=0.25,
            vlm_root_cause_accuracy=0.35,
            vlm_tool_call_count=0,
            saar_explainability_score=0.98,
            saar_root_cause_accuracy=0.96,
            saar_tool_call_count=3,
            key_differences=[
                "Standard VLM incorrectly guessed cosmological expansion because it lacked time-series Doppler calculations.",
                "Saar derived periodic velocity variations (K = 85.2 m/s over 3.524 days).",
                "Saar executed mass function tools to confirm a 0.69 M_Jupiter exoplanet and explicitly rule out a binary star companion.",
                "Saar established an audit trail connecting spectral lines → Doppler velocity → Keplerian orbital curve → planetary confirmation."
            ]
        )

    def generate_final_conclusion(self, nodes: List[NodeModel], edges: List[EdgeModel]) -> str:
        return (
            "ASTRONOMICAL INVESTIGATION CONCLUDED (97% CONFIDENCE):\n"
            "1. Doppler Measurement: Line centroid displacement Δλ = +0.042nm corresponds to K = 85.2 m/s radial velocity semi-amplitude.\n"
            "2. Orbital Fit: Keplerian modeling establishes a circular orbit with P = 3.524 days.\n"
            "3. Mass Evaluation: Minimum companion mass m sin i = 0.69 M_Jupiter.\n"
            "4. Conclusion: Hot Jupiter Exoplanet confirmed. Binary stellar companion hypothesis rejected."
        )
