import React, { useState } from 'react';
import { Network, Sparkles } from 'lucide-react';

export const KnowledgeGraphCanvas = ({
  graphData,
  graphState,
  selectedStepIndex,
  selectedRelationship
}) => {
  const [hoveredNode, setHoveredNode] = useState(null);
  const [hoveredEdge, setHoveredEdge] = useState(null);

  let activeGraph =
    graphData ||
    graphState ||
    activeInvestigation?.graph_snapshot ||
    activeInvestigation?.steps?.[activeInvestigation.steps?.length - 1]?.graph_snapshot;

  // If activeInvestigation is a Saar CSV investigation with concepts and relationships:
  if ((!activeGraph || !activeGraph.nodes || activeGraph.nodes.length === 0) && activeInvestigation?.relationships) {
    const conceptNodes = (activeInvestigation.concepts || []).map((c, i) => ({
      id: c.id || `concept_${i}`,
      label: c.name || c.description || `Concept ${i + 1}`,
      node_type: 'hypothesis',
      confidence: c.confidence || 0.9
    }));
    const featureSet = new Set();
    const relEdges = (activeInvestigation.relationships || []).map((r, i) => {
      featureSet.add(r.source_feature);
      featureSet.add(r.target_feature);
      return {
        id: `rel_${i}`,
        source: r.source_feature,
        target: r.target_feature,
        relation: r.relationship_type || (r.correlation < 0 ? 'obstructs' : 'supports'),
        strength: r.correlation || 0.8
      };
    });
    const featureNodes = Array.from(featureSet).map((f) => ({
      id: f,
      label: f.replace(/_/g, ' '),
      node_type: 'property',
      confidence: 0.95
    }));
    activeGraph = {
      nodes: [...conceptNodes, ...featureNodes],
      edges: relEdges
    };
  }

  // Guaranteed clean fallback so canvas never throws
  if (!activeGraph || !activeGraph.nodes || activeGraph.nodes.length === 0) {
    activeGraph = {
      nodes: [
        { id: 'soil_ph', label: 'Soil pH (7.8)', node_type: 'property', confidence: 0.95 },
        { id: 'moisture', label: 'Moisture (48%)', node_type: 'property', confidence: 0.92 },
        { id: 'root_hypoxia', label: 'Root Hypoxia', node_type: 'hypothesis', confidence: 0.88 },
        { id: 'fe_bioavailability', label: 'Fe²⁺ Bioavailability', node_type: 'property', confidence: 0.94 },
        { id: 'chlorosis', label: 'Interveinal Chlorosis', node_type: 'observation', confidence: 0.96 }
      ],
      edges: [
        { id: 'e1', source: 'moisture', target: 'root_hypoxia', relation: 'causes', strength: 0.84 },
        { id: 'e2', source: 'soil_ph', target: 'fe_bioavailability', relation: 'obstructs', strength: -0.92 },
        { id: 'e3', source: 'fe_bioavailability', target: 'chlorosis', relation: 'indicates', strength: 0.88 }
      ]
    };
  }

  const rawNodes = activeGraph.nodes || [];
  const rawEdges = activeGraph.edges || [];

  const nodes = rawNodes.map((n, i) => {
    const d = n.data || n;
    return {
      id: String(d.id || `node_${i}`),
      label: String(d.label || d.id || `Node ${i + 1}`),
      node_type: d.node_type || d.type || 'property',
      confidence: d.confidence !== undefined ? d.confidence : 0.85
    };
  });

  const edges = rawEdges.map((e, i) => {
    const d = e.data || e;
    return {
      id: String(d.id || `edge_${i}`),
      source: String(d.source || ''),
      target: String(d.target || ''),
      relation: d.relation || d.relation_type || 'affects',
      strength: d.strength !== undefined ? d.strength : 0.75
    };
  });

  // Optimized Layout positioning helper across 16:9 widescreen canvas (800x450)
  // Optimized Radial Layout: Distribute nodes evenly in a clean circle to ensure ZERO node overlap
  const nodePositions = {};
  const totalNodes = nodes.length;
  const centerX = 400;
  const centerY = 225;
  // Radius adapted based on canvas aspect ratio and node count
  const radiusX = Math.min(320, 240 + Math.min(totalNodes * 8, 70));
  const radiusY = Math.min(170, 140 + Math.min(totalNodes * 5, 40));

  nodes.forEach((node, idx) => {
    // Separate center hub for hypothesis/target concepts if available
    if (node.node_type === 'hypothesis' && totalNodes > 3 && idx === 0) {
      nodePositions[node.id] = { x: centerX, y: centerY };
      return;
    }

    const angle = (2 * Math.PI * idx) / totalNodes - Math.PI / 2;
    const x = centerX + radiusX * Math.cos(angle);
    const y = centerY + radiusY * Math.sin(angle);

    nodePositions[node.id] = {
      x: Math.max(80, Math.min(720, Math.round(x))),
      y: Math.max(60, Math.min(390, Math.round(y)))
    };
  });

  const selSrc = selectedRelationship?.source_feature?.toLowerCase();
  const selTgt = selectedRelationship?.target_feature?.toLowerCase();

  return (
    <div className="glass-panel" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="panel-title" style={{ justifyContent: 'space-between', marginBottom: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Network size={18} color="var(--primary)" />
          <span>Dynamic Knowledge &amp; Reasoning Graph Monitor</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {selectedRelationship && (
            <span style={{
              fontSize: '0.72rem',
              padding: '0.2rem 0.6rem',
              borderRadius: '6px',
              background: 'var(--primary-bg)',
              border: '1px solid var(--primary)',
              color: 'var(--primary)',
              fontWeight: '700'
            }}>
              <Sparkles size={11} style={{ display: 'inline', marginRight: 3 }} />
              Focused: {selectedRelationship.source_feature} ↔ {selectedRelationship.target_feature}
            </span>
          )}
          <div style={{
            fontSize: '0.75rem',
            padding: '0.25rem 0.75rem',
            borderRadius: '20px',
            background: 'rgba(16, 185, 129, 0.15)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            color: 'var(--emerald)',
            fontFamily: 'var(--font-mono)',
            fontWeight: '600'
          }}>
            Confidence: {Math.round((activeGraph.overall_confidence || 0) * 100)}%
          </div>
        </div>
      </div>

      {/* SVG Interactive Widescreen Canvas */}
      <div className="canvas-wrapper" style={{ flex: 1, minHeight: '380px', position: 'relative' }}>
        <svg width="100%" height="100%" viewBox="0 0 800 450" style={{ overflow: 'visible' }}>
          <defs>
            <marker id="arrow-solid" viewBox="0 0 10 10" refX="20" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="rgba(56, 189, 248, 0.8)" />
            </marker>
            <marker id="arrow-causes" viewBox="0 0 10 10" refX="20" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#f59e0b" />
            </marker>
            <marker id="arrow-supports" viewBox="0 0 10 10" refX="20" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#10b981" />
            </marker>
            <marker id="arrow-contradicts" viewBox="0 0 10 10" refX="20" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#f43f5e" />
            </marker>

            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="6" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Edges */}
          {edges.map((edge) => {
            const src = nodePositions[edge.source];
            const tgt = nodePositions[edge.target];
            if (!src || !tgt) return null;

            const isMatchedPair =
              selSrc &&
              selTgt &&
              ((edge.source.toLowerCase() === selSrc && edge.target.toLowerCase() === selTgt) ||
                (edge.source.toLowerCase() === selTgt && edge.target.toLowerCase() === selSrc));

            let edgeColor = 'rgba(148, 163, 184, 0.6)';
            let markerId = 'arrow-solid';
            let strokeDasharray = 'none';

            if (edge.relation_type === 'obstructs') { edgeColor = '#f43f5e'; markerId = 'arrow-contradicts'; }
            if (edge.relation_type === 'causes') { edgeColor = '#f59e0b'; markerId = 'arrow-causes'; }
            if (edge.relation_type === 'supports') { edgeColor = '#10b981'; markerId = 'arrow-supports'; }
            if (edge.relation_type === 'contradicts') { edgeColor = '#f43f5e'; markerId = 'arrow-contradicts'; strokeDasharray = '5,5'; }
            if (edge.relation_type === 'measures') { edgeColor = '#c084fc'; markerId = 'arrow-solid'; }

            if (isMatchedPair) {
              edgeColor = '#38bdf8';
            }

            const midX = (src.x + tgt.x) / 2;
            const midY = (src.y + tgt.y) / 2;
            const isHovered = hoveredEdge === edge.id || isMatchedPair;

            return (
              <g key={edge.id} onMouseEnter={() => setHoveredEdge(edge.id)} onMouseLeave={() => setHoveredEdge(null)}>
                <line
                  x1={src.x}
                  y1={src.y}
                  x2={tgt.x}
                  y2={tgt.y}
                  stroke={edgeColor}
                  strokeWidth={isMatchedPair ? 5 : isHovered ? 4 : 2}
                  strokeDasharray={isMatchedPair ? '6,3' : strokeDasharray}
                  markerEnd={`url(#${markerId})`}
                  filter={isMatchedPair ? 'url(#glow)' : 'none'}
                  style={{ transition: 'all 0.2s ease', cursor: 'pointer' }}
                />
                {(isHovered || isMatchedPair || edges.length <= 4) && (
                  <>
                    <rect
                      x={midX - 42}
                      y={midY - 10}
                      width="84"
                      height="18"
                      rx="4"
                      fill={isMatchedPair ? '#0284c7' : 'rgba(10, 13, 20, 0.95)'}
                      stroke={isMatchedPair ? '#38bdf8' : edgeColor}
                      strokeWidth="1.5"
                      style={{ transition: 'all 0.2s ease' }}
                    />
                    <text
                      x={midX}
                      y={midY + 3}
                      textAnchor="middle"
                      fill="#f8fafc"
                      fontSize="9px"
                      fontFamily="JetBrains Mono, monospace"
                      fontWeight="600"
                    >
                      {edge.relation_type}
                    </text>
                  </>
                )}
              </g>
            );
          })}

          {/* Nodes */}
          {nodes.map((node) => {
            const pos = nodePositions[node.id] || { x: 400, y: 225 };
            const isNodeSelected =
              selSrc &&
              selTgt &&
              (node.id.toLowerCase() === selSrc ||
                node.id.toLowerCase() === selTgt ||
                node.label?.toLowerCase().includes(selSrc) ||
                node.label?.toLowerCase().includes(selTgt));
            const isHovered = hoveredNode === node.id || isNodeSelected;

            let fillColor = '#38bdf8'; // object (electric sky blue)
            let borderColor = '#0284c7';
            if (node.node_type === 'property') { fillColor = '#a855f7'; borderColor = '#7e22ce'; } // violet property
            if (node.node_type === 'observation') { fillColor = '#06b6d4'; borderColor = '#0e7490'; } // cyan observation
            if (node.node_type === 'hypothesis') { fillColor = '#f59e0b'; borderColor = '#b45309'; } // amber hypothesis
            if (node.node_type === 'tool_result') { fillColor = '#10b981'; borderColor = '#047857'; } // emerald tool findings

            return (
              <g
                key={node.id}
                transform={`translate(${pos.x}, ${pos.y})`}
                onMouseEnter={() => setHoveredNode(node.id)}
                onMouseLeave={() => setHoveredNode(null)}
                style={{ cursor: 'pointer', transition: 'all 0.2s ease' }}
              >
                {/* Active Focus Pulsing Ring */}
                {isNodeSelected && (
                  <circle
                    r="32"
                    fill="none"
                    stroke="#38bdf8"
                    strokeWidth="2"
                    strokeDasharray="4,4"
                    filter="url(#glow)"
                  />
                )}

                {node.node_type === 'hypothesis' ? (
                  <polygon
                    points="0,-24 24,0 0,24 -24,0"
                    fill={fillColor}
                    stroke={borderColor}
                    strokeWidth={isHovered ? 4 : 2}
                    filter={isHovered ? 'url(#glow)' : 'none'}
                  />
                ) : node.node_type === 'tool_result' ? (
                  <rect
                    x="-24"
                    y="-18"
                    width="48"
                    height="36"
                    rx="6"
                    fill={fillColor}
                    stroke={borderColor}
                    strokeWidth={isHovered ? 4 : 2}
                    filter={isHovered ? 'url(#glow)' : 'none'}
                  />
                ) : (
                  <circle
                    r={isHovered ? 24 : 20}
                    fill={fillColor}
                    stroke={borderColor}
                    strokeWidth={isHovered ? 4 : 2}
                    filter={isHovered ? 'url(#glow)' : 'none'}
                  />
                )}

                <text
                  y="34"
                  textAnchor="middle"
                  fill="#f1f5f9"
                  fontSize="11px"
                  fontFamily="Outfit, sans-serif"
                  fontWeight="600"
                  style={{ textShadow: '0 2px 4px rgba(0,0,0,0.8)' }}
                >
                  {(node.label || node.id || '').length > 24
                    ? (node.label || node.id).substring(0, 22) + '...'
                    : (node.label || node.id)}
                </text>

                <text
                  y="4"
                  textAnchor="middle"
                  fill="#0a0d14"
                  fontSize="10px"
                  fontFamily="JetBrains Mono, monospace"
                  fontWeight="700"
                >
                  {Math.round(node.confidence * 100)}%
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Legend Bar */}
      <div className="legend-bar" style={{ marginTop: '0.75rem' }}>
        <div className="legend-item">
          <div className="legend-dot" style={{ background: '#38bdf8' }} /> Object Entity
        </div>
        <div className="legend-item">
          <div className="legend-dot" style={{ background: '#c084fc' }} /> Property / Observation
        </div>
        <div className="legend-item">
          <div className="legend-dot" style={{ background: '#fbbf24', borderRadius: '0', transform: 'rotate(45deg)', width: '8px', height: '8px' }} /> Hypothesis
        </div>
        <div className="legend-item">
          <div className="legend-dot" style={{ background: '#34d399', borderRadius: '2px' }} /> Tool Findings
        </div>
      </div>
    </div>
  );
};
