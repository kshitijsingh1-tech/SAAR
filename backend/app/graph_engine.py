import networkx as nx
from typing import List, Dict, Any, Optional, Tuple
from .schemas import NodeModel, EdgeModel, GraphStateModel

class ReasoningGraphEngine:
    """
    Manages the directed Knowledge & Reasoning Graph using NetworkX.
    Tracks entity nodes, causal/influential edges, confidence metrics, and uncertainty.
    """
    def __init__(self):
        self.graph = nx.DiGraph()

    def clear(self):
        self.graph.clear()

    def add_node(self, node: NodeModel) -> NodeModel:
        self.graph.add_node(
            node.id,
            label=node.label,
            node_type=node.node_type,
            category=node.category,
            confidence=node.confidence,
            properties=node.properties,
            status=node.status,
            bbox=node.bbox,
            visual_anchor=node.visual_anchor
        )
        return node

    def add_edge(self, edge: EdgeModel) -> EdgeModel:
        self.graph.add_edge(
            edge.source,
            edge.target,
            id=edge.id,
            relation_type=edge.relation_type,
            confidence=edge.confidence,
            evidence=edge.evidence,
            status=edge.status
        )
        return edge

    def update_node_confidence(self, node_id: str, new_confidence: float, status: Optional[str] = None):
        if node_id in self.graph:
            self.graph.nodes[node_id]['confidence'] = max(0.0, min(1.0, new_confidence))
            if status:
                self.graph.nodes[node_id]['status'] = status

    def update_edge_confidence(self, edge_id: str, new_confidence: float, status: Optional[str] = None):
        for u, v, data in self.graph.edges(data=True):
            if data.get('id') == edge_id:
                data['confidence'] = max(0.0, min(1.0, new_confidence))
                if status:
                    data['status'] = status
                break

    def get_node(self, node_id: str) -> Optional[NodeModel]:
        if node_id not in self.graph:
            return None
        data = self.graph.nodes[node_id]
        return NodeModel(
            id=node_id,
            label=data.get('label', node_id),
            node_type=data.get('node_type', 'object'),
            category=data.get('category', 'general'),
            confidence=data.get('confidence', 1.0),
            properties=data.get('properties', {}),
            status=data.get('status', 'confirmed'),
            bbox=data.get('bbox'),
            visual_anchor=data.get('visual_anchor', True)
        )

    def calculate_uncertainty(self) -> Tuple[float, Optional[str]]:
        """
        Calculates graph-wide uncertainty (0.0 = completely certain, 1.0 = highly uncertain)
        and identifies the active hypothesis node with highest uncertainty.
        """
        if not self.graph.nodes:
            return 1.0, None

        total_nodes = len(self.graph.nodes)
        node_confidences = [data.get('confidence', 1.0) for _, data in self.graph.nodes(data=True)]
        edge_confidences = [data.get('confidence', 1.0) for _, _, data in self.graph.edges(data=True)]

        all_conf = node_confidences + edge_confidences
        avg_confidence = sum(all_conf) / len(all_conf) if all_conf else 0.5
        uncertainty = 1.0 - avg_confidence

        # Find top hypothesis node with lowest confidence (highest uncertainty)
        top_hypothesis = None
        min_conf = 1.0
        for n, data in self.graph.nodes(data=True):
            if data.get('node_type') == 'hypothesis' and data.get('status') != 'invalidated':
                if data.get('confidence', 1.0) < min_conf:
                    min_conf = data.get('confidence', 1.0)
                    top_hypothesis = n

        return round(uncertainty, 3), top_hypothesis

    def export_state(self, step_count: int = 0) -> GraphStateModel:
        nodes_list = []
        for n, data in self.graph.nodes(data=True):
            nodes_list.append(NodeModel(
                id=n,
                label=data.get('label', n),
                node_type=data.get('node_type', 'object'),
                category=data.get('category', 'general'),
                confidence=round(data.get('confidence', 1.0), 3),
                properties=data.get('properties', {}),
                status=data.get('status', 'confirmed'),
                bbox=data.get('bbox'),
                visual_anchor=data.get('visual_anchor', True)
            ))

        edges_list = []
        for u, v, data in self.graph.edges(data=True):
            edges_list.append(EdgeModel(
                id=data.get('id', f"{u}_to_{v}"),
                source=u,
                target=v,
                relation_type=data.get('relation_type', 'affects'),
                confidence=round(data.get('confidence', 1.0), 3),
                evidence=data.get('evidence', ''),
                status=data.get('status', 'active')
            ))

        uncertainty, top_hypo = self.calculate_uncertainty()
        overall_conf = round(1.0 - uncertainty, 3)

        return GraphStateModel(
            nodes=nodes_list,
            edges=edges_list,
            overall_confidence=overall_conf,
            active_hypothesis=top_hypo,
            uncertainty_score=uncertainty,
            step_count=step_count
        )
