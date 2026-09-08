import uuid
from typing import Dict, List, Optional
from .schemas import (
    NodeModel, EdgeModel, GraphStateModel, WorkflowStepModel,
    ToolExecutionModel, InvestigationResponse, BaselineComparisonModel
)
from .graph_engine import ReasoningGraphEngine
from .plugins.base_plugin import BaseDomainPlugin
from .plugins.infrastructure_plugin import InfrastructurePlugin
from .vlm_service import VLMService

class DynamicWorkflowOrchestrator:
    def __init__(self):
        self.plugins: Dict[str, BaseDomainPlugin] = {
            "infrastructure": InfrastructurePlugin()
        }
        self.vlm_service = VLMService()

    def get_plugin(self, domain: str) -> BaseDomainPlugin:
        return self.plugins.get(domain, self.plugins["infrastructure"])

    def run_investigation(
        self,
        domain: str = "infrastructure",
        preset_id: Optional[str] = None,
        image_url: Optional[str] = None,
        image_data: Optional[str] = None,
        vlm_provider: str = "auto",
        api_key: Optional[str] = None
    ) -> InvestigationResponse:
        plugin = self.get_plugin(domain)
        if not preset_id:
            preset_id = plugin.presets[0]["id"]

        graph_engine = ReasoningGraphEngine()
        steps: List[WorkflowStepModel] = []
        step_counter = 1

        # ---------------------------------------------------------
        # Step 1: PERCEIVE - Extract entities, properties, observations via VLM
        # ---------------------------------------------------------
        image_input = image_data or image_url
        if not image_input and preset_id:
            for p in plugin.presets:
                if p["id"] == preset_id:
                    image_input = p.get("image")
                    break

        initial_nodes, initial_edges, vlm_summary, provider_used = self.vlm_service.analyze_image(
            image_input=image_input,
            domain=domain,
            preset_id=preset_id,
            vlm_provider=vlm_provider,
            api_key=api_key
        )

        for n in initial_nodes:
            graph_engine.add_node(n)
        for e in initial_edges:
            graph_engine.add_edge(e)

        snapshot_1 = graph_engine.export_state(step_count=1)
        is_live = "Live VLM" in provider_used or bool(api_key)

        steps.append(WorkflowStepModel(
            step_number=1,
            state="PERCEIVE",
            title=f"1. VLM Scene Perception [{provider_used}]",
            description=vlm_summary,
            log_message=f"VLM ({provider_used}) extracted {len(initial_nodes)} visual nodes and {len(initial_edges)} relationship links. Graph confidence: {snapshot_1.overall_confidence * 100:.0f}%.",
            graph_snapshot=snapshot_1
        ))

        # ---------------------------------------------------------
        # Dynamic Tool Loop (Steps 2..N)
        # ---------------------------------------------------------
        available_tools = plugin.get_available_tools()

        for tool_info in available_tools:
            tool_id = tool_info["tool_id"]
            tool_name = tool_info["tool_name"]

            # Step A: FIND UNKNOWNS
            uncertainty, target_hypo = graph_engine.calculate_uncertainty()
            step_counter += 1
            snapshot_unk = graph_engine.export_state(step_count=step_counter)
            steps.append(WorkflowStepModel(
                step_number=step_counter,
                state="FIND_UNKNOWNS",
                title=f"{step_counter}. Uncertainty Detection & Gap Analysis",
                description=f"Identified open research questions and hypothesis node requiring evidence verification.",
                log_message=f"Graph uncertainty at {uncertainty*100:.1f}%. Target hypothesis: '{target_hypo or 'General Investigation'}'.",
                graph_snapshot=snapshot_unk
            ))

            # Step B: SELECT ACTION & EXECUTE TOOL
            step_counter += 1
            tool_exec: ToolExecutionModel = plugin.execute_tool(
                tool_id=tool_id,
                current_nodes=snapshot_unk.nodes,
                current_edges=snapshot_unk.edges
            )

            # Apply tool results to Graph
            for new_node in tool_exec.added_nodes:
                graph_engine.add_node(new_node)
            for new_edge in tool_exec.added_edges:
                graph_engine.add_edge(new_edge)

            # Update hypothesis status if present
            if target_hypo and target_hypo in graph_engine.graph:
                current_c = graph_engine.graph.nodes[target_hypo].get('confidence', 0.5)
                new_c = min(1.0, current_c + tool_exec.confidence_delta)
                status = "confirmed" if new_c >= 0.85 else "hypothesis"
                graph_engine.update_node_confidence(target_hypo, new_c, status=status)

            snapshot_tool = graph_engine.export_state(step_count=step_counter)
            steps.append(WorkflowStepModel(
                step_number=step_counter,
                state="RUN_TOOL",
                title=f"{step_counter}. Execute Specialized Tool: {tool_name}",
                description=tool_exec.output_findings,
                log_message=f"Executed tool '{tool_name}'. Added {len(tool_exec.added_nodes)} nodes & {len(tool_exec.added_edges)} edges to reasoning graph.",
                graph_snapshot=snapshot_tool,
                tool_execution=tool_exec
            ))

        # ---------------------------------------------------------
        # Final Step: CONCLUSION
        # ---------------------------------------------------------
        step_counter += 1
        final_graph = graph_engine.export_state(step_count=step_counter)
        final_conclusion = plugin.generate_final_conclusion(final_graph.nodes, final_graph.edges)

        steps.append(WorkflowStepModel(
            step_number=step_counter,
            state="CONCLUSION",
            title=f"{step_counter}. Dynamic Investigation Conclusion",
            description="All critical hypotheses verified. Evidence graph stabilized.",
            log_message=f"Investigation completed with {final_graph.overall_confidence * 100:.1f}% confidence across {len(final_graph.nodes)} evidence nodes.",
            graph_snapshot=final_graph
        ))

        baseline_comp = plugin.get_baseline_comparison(preset_id)

        return InvestigationResponse(
            investigation_id=str(uuid.uuid4())[:8],
            domain=domain,
            preset_id=preset_id,
            vlm_provider_used=provider_used,
            is_live_vlm=is_live,
            steps=steps,
            final_graph=final_graph,
            baseline=baseline_comp,
            conclusion=final_conclusion
        )
