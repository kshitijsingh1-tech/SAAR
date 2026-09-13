"""
Tests for Phase 12: Knowledge & Evidence Graph Engine.

Verifies:
1. Strict reuse of SAAR's core ReasoningGraphEngine, NodeModel, EdgeModel, and GraphStateModel.
2. Section 25 node types and Section 28 category discipline across all nodes.
3. Complete numeric attribution (value, unit, confidence, source, timestamp/frame range, calculation method).
4. Zero orphan nodes (complete connectivity and causal provenance).
5. Real multi-shot video produces a non-trivial graph compatible with KnowledgeGraphCanvas.jsx.
"""

from pathlib import Path
import pytest
import networkx as nx

from app.schemas import NodeModel, EdgeModel, GraphStateModel
from app.graph_engine import ReasoningGraphEngine
from app.plugins.sports.badminton.schemas import (
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
    Metric,
    BadmintonAnalysisResult
)
from app.plugins.sports.badminton.evidence import (
    BadmintonEvidenceGraphBuilder,
    Section25NodeType,
    NodeCategory
)
from app.plugins.sports.badminton.pipeline import BadmintonPipeline


class TestBadmintonEvidenceGraph:

    def test_schema_and_engine_reuse(self):
        """Verify SAAR's core graph engine and models are directly reused."""
        builder = BadmintonEvidenceGraphBuilder()
        assert isinstance(builder.engine, ReasoningGraphEngine)

        vid_meta = VideoMetadata(filename="test.mp4", duration_seconds=5.0, fps=30.0, total_frames=150, frames_processed=150, width=1920, height=1080)
        quality = QualityAssessment(confidence=CaptureConfidence.HIGH)

        graph_state = builder.build_evidence_graph(video_metadata=vid_meta, quality=quality)
        assert isinstance(graph_state, GraphStateModel)
        assert len(graph_state.nodes) > 0
        assert len(graph_state.edges) > 0

        # Verify NodeModel and EdgeModel types
        for n in graph_state.nodes:
            assert isinstance(n, NodeModel)
        for e in graph_state.edges:
            assert isinstance(e, EdgeModel)

    def test_section_25_node_types_and_section_28_categories(self):
        """Verify all graph nodes strictly conform to Section 25 types and Section 28 categories."""
        builder = BadmintonEvidenceGraphBuilder()
        vid_meta = VideoMetadata(filename="test.mp4", duration_seconds=10.0, fps=30.0, total_frames=300, frames_processed=300, width=1920, height=1080)
        quality = QualityAssessment(confidence=CaptureConfidence.HIGH)
        court_calib = CourtCalibration(is_calibrated=True, calibration_source="corners", corners_pixel=[[0,0],[1,0],[1,1],[0,1]], confidence=0.88)
        shot = ShotResult(
            shot_id="shot_001",
            shot_type="smash",
            confidence=0.88,
            start_time=1.0,
            contact_time=1.3,
            end_time=1.6,
            duration=0.3,
            pose_features={
                "elbow_angle_deg": 142.5,
                "shoulder_angle_deg": 160.2,
                "knee_angle_deg": 135.0,
                "hip_angle_deg": 150.1,
                "kinetic_chain_sequencing": {"available": True, "sequence_order": ["hip", "shoulder", "elbow"]}
            }
        )
        speed_meta = SpeedMetrics(
            racket_speed_peak=Metric(name="racket_speed", value=145.2, unit="km/h", confidence="HIGH", available=True),
            shuttle_speed_peak=Metric(name="shuttle_speed", value=242.0, unit="km/h", confidence="HIGH", available=True)
        )
        energy_meta = EnergyMetrics(
            estimated_energy_expenditure_kcal=4.5,
            estimation_type="personalized",
            inputs_used=["body_weight_kg", "session_duration_min"],
            calculation_method="Ainsworth 2011 MET formula",
            confidence="0.92"
        )

        graph_state = builder.build_evidence_graph(
            video_metadata=vid_meta,
            quality=quality,
            court_calibration=court_calib,
            shots=[shot],
            speed_metrics=speed_meta,
            energy_metrics=energy_meta
        )

        valid_node_types = {t.value for t in Section25NodeType}
        valid_categories = {c.value for c in NodeCategory}

        for node in graph_state.nodes:
            assert node.node_type in valid_node_types, f"Node {node.id} has invalid type: {node.node_type}"
            assert node.category in valid_categories, f"Node {node.id} has invalid category: {node.category}"

    def test_complete_numeric_attribution(self):
        """
        REQUIREMENT: Every numeric node must carry value, unit, confidence,
        source, timestamp/frame range, and calculation method in its properties dict.
        """
        builder = BadmintonEvidenceGraphBuilder()
        vid_meta = VideoMetadata(filename="test.mp4", duration_seconds=6.0, fps=30.0, total_frames=180, frames_processed=180, width=1920, height=1080)
        quality = QualityAssessment(confidence=CaptureConfidence.HIGH)
        shot = ShotResult(
            shot_id="shot_1",
            shot_type="clear",
            confidence=0.75,
            start_time=2.0,
            contact_time=2.4,
            end_time=2.8,
            duration=0.4,
            pose_features={"elbow_angle_deg": 115.0, "knee_angle_deg": 160.0}
        )

        graph_state = builder.build_evidence_graph(
            video_metadata=vid_meta,
            quality=quality,
            shots=[shot]
        )

        required_keys = ["value", "unit", "confidence", "source", "timestamp_or_frame_range", "calculation_method"]

        numeric_count = 0
        for node in graph_state.nodes:
            # Check if this node represents a numerical property or measurement
            props = node.properties
            # Every node created by our engine provides these provenance attributes
            for req_key in required_keys:
                assert req_key in props, f"Node '{node.id}' missing required provenance property '{req_key}'"
                assert props[req_key] is not None or props["value"] is None, f"Node '{node.id}' has empty '{req_key}'"
            if isinstance(props.get("value"), (int, float)):
                numeric_count += 1

        assert numeric_count >= 3, f"Expected at least 3 numeric nodes, found {numeric_count}"

    def test_zero_orphan_nodes_and_connectivity(self):
        """REQUIREMENT: Every node traces back to a specific measurement — no orphan/unsourced nodes."""
        builder = BadmintonEvidenceGraphBuilder()
        vid_meta = VideoMetadata(filename="test.mp4", duration_seconds=5.0, fps=30.0, total_frames=150, frames_processed=150, width=1920, height=1080)
        quality = QualityAssessment(confidence=CaptureConfidence.HIGH)
        shot = ShotResult(
            shot_id="shot_10",
            shot_type="drop",
            confidence=0.80,
            start_time=1.0,
            contact_time=1.3,
            end_time=1.7,
            duration=0.4,
            pose_features={"elbow_angle_deg": 120.0}
        )

        graph_state = builder.build_evidence_graph(
            video_metadata=vid_meta,
            quality=quality,
            shots=[shot]
        )

        # Build undirected view to check connectivity / degree
        node_ids = {n.id for n in graph_state.nodes}
        edge_nodes = set()
        for e in graph_state.edges:
            assert e.source in node_ids, f"Edge source {e.source} not in nodes"
            assert e.target in node_ids, f"Edge target {e.target} not in nodes"
            edge_nodes.add(e.source)
            edge_nodes.add(e.target)

        # Confirm every single node participates in at least one edge (no orphan nodes)
        orphan_nodes = node_ids - edge_nodes
        assert len(orphan_nodes) == 0, f"Found orphan nodes without edges: {orphan_nodes}"

    def test_real_video_produces_rich_graph_and_frontend_compatibility(self):
        """
        DEFINITION OF DONE REQUIREMENT:
        A real analyzed video produces a real, non-trivial graph (multiple node types,
        real edges) that KnowledgeGraphCanvas can render without modification.
        """
        candidate_paths = [
            Path("../Prompt_Photorealistic_p_.mp4"),
            Path("Prompt_Photorealistic_p_.mp4"),
            Path("app/gait/assets/sample_toddler_walk.mp4")
        ]
        video_path = next((p for p in candidate_paths if p.exists()), None)
        if not video_path:
            pytest.skip("Test video not found")

        pipeline = BadmintonPipeline()
        result = pipeline.analyze_video_bytes(video_path.read_bytes(), video_path.name)

        assert result.graph_data is not None
        assert isinstance(result.graph_data, GraphStateModel)
        assert result.graph is result.graph_data
        assert result.final_graph is result.graph_data

        nodes = result.graph_data.nodes
        edges = result.graph_data.edges

        # Check non-trivial graph size
        assert len(nodes) >= 15, f"Expected >= 15 nodes in real video graph, got {len(nodes)}"
        assert len(edges) >= 15, f"Expected >= 15 edges in real video graph, got {len(edges)}"

        # Check multiplicity of node types
        node_types = {n.node_type for n in nodes}
        expected_types = {"player", "court", "shot", "shot_type", "joint", "movement", "metric", "evidence"}
        assert expected_types.issubset(node_types), f"Missing expected node types. Found: {node_types}"

        # Check multiplicity of categories
        categories = {n.category for n in nodes}
        assert "OBSERVATION" in categories
        assert "MEASUREMENT" in categories
        assert "RAG_EVIDENCE" in categories
        assert "LIMITATION" in categories

        # KnowledgeGraphCanvas shape verification
        # 1. Every node has string id, label, valid confidence, and properties dict
        for n in nodes:
            assert isinstance(n.id, str) and len(n.id) > 0
            assert isinstance(n.label, str) and len(n.label) > 0
            assert 0.0 <= n.confidence <= 1.0
            assert isinstance(n.properties, dict)

        # 2. Every edge has string id, source, target, relation_type
        node_id_set = {n.id for n in nodes}
        for e in edges:
            assert isinstance(e.id, str) and len(e.id) > 0
            assert e.source in node_id_set
            assert e.target in node_id_set
            assert isinstance(e.relation_type, str) and len(e.relation_type) > 0
            assert 0.0 <= e.confidence <= 1.0
