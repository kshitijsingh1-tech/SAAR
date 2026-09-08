from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class NodeModel(BaseModel):
    id: str
    label: str
    node_type: str = Field(..., description="object, property, observation, hypothesis, tool_result")
    category: str = Field(default="general")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    properties: Dict[str, Any] = Field(default_factory=dict)
    status: str = Field(default="confirmed", description="confirmed, hypothesis, invalidated")

class EdgeModel(BaseModel):
    id: str
    source: str
    target: str
    relation_type: str = Field(..., description="obstructs, causes, affects, indicates, varies_with, supports, contradicts, measures")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence: str = ""
    status: str = Field(default="active", description="active, evaluating, rejected")

class GraphStateModel(BaseModel):
    nodes: List[NodeModel]
    edges: List[EdgeModel]
    overall_confidence: float = 0.5
    active_hypothesis: Optional[str] = None
    uncertainty_score: float = 0.5
    step_count: int = 0

class ToolExecutionModel(BaseModel):
    tool_id: str
    tool_name: str
    target_node_id: Optional[str] = None
    input_params: Dict[str, Any] = Field(default_factory=dict)
    output_findings: str = ""
    confidence_delta: float = 0.0
    added_nodes: List[NodeModel] = Field(default_factory=list)
    added_edges: List[EdgeModel] = Field(default_factory=list)

class WorkflowStepModel(BaseModel):
    step_number: int
    state: str = Field(..., description="PERCEIVE, FIND_UNKNOWNS, SELECT_ACTION, RUN_TOOL, UPDATE_GRAPH, CONCLUSION")
    title: str
    description: str
    log_message: str
    graph_snapshot: GraphStateModel
    tool_execution: Optional[ToolExecutionModel] = None

class BaselineComparisonModel(BaseModel):
    vlm_prompt: str
    vlm_raw_response: str
    vlm_explainability_score: float = 0.35
    vlm_root_cause_accuracy: float = 0.50
    vlm_tool_call_count: int = 0
    saar_explainability_score: float = 0.96
    saar_root_cause_accuracy: float = 0.94
    saar_tool_call_count: int = 3
    key_differences: List[str]

class InvestigationRequest(BaseModel):
    domain: str = "infrastructure" # infrastructure | agriculture
    preset_id: Optional[str] = "infra_damaged_road"
    image_url: Optional[str] = None
    image_data: Optional[str] = None # Base64 image payload
    vlm_provider: str = "auto" # auto | gemini | openai | ollama | synthesizer
    api_key: Optional[str] = None

class InvestigationResponse(BaseModel):
    investigation_id: str
    domain: str
    preset_id: str
    vlm_provider_used: str = "Saar Vision Engine"
    is_live_vlm: bool = False
    steps: List[WorkflowStepModel]
    final_graph: GraphStateModel
    baseline: BaselineComparisonModel
    conclusion: str

