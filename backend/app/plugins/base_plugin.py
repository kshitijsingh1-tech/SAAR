from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
from ..schemas import NodeModel, EdgeModel, ToolExecutionModel, BaselineComparisonModel

class BaseDomainPlugin(ABC):
    @property
    @abstractmethod
    def domain_name(self) -> str:
        pass

    @property
    @abstractmethod
    def presets(self) -> List[Dict[str, str]]:
        pass

    @abstractmethod
    def perceive_initial_scene(self, preset_id: str) -> Tuple[List[NodeModel], List[EdgeModel]]:
        """Extract initial entities, properties, and direct observations from scene."""
        pass

    @abstractmethod
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Return list of specialized analytical tools provided by domain plugin."""
        pass

    @abstractmethod
    def execute_tool(self, tool_id: str, current_nodes: List[NodeModel], current_edges: List[EdgeModel]) -> ToolExecutionModel:
        """Execute domain-specific tool to test hypotheses and gather evidence."""
        pass

    @abstractmethod
    def get_baseline_comparison(self, preset_id: str) -> BaselineComparisonModel:
        """Provide single-pass VLM baseline response for benchmarking."""
        pass

    @abstractmethod
    def generate_final_conclusion(self, nodes: List[NodeModel], edges: List[EdgeModel]) -> str:
        """Generate cohesive evidence-backed scientific summary."""
        pass
