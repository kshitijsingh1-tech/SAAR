import React, { useState, useMemo, useRef, useEffect } from 'react';
import {
  Network, Sparkles, Eye, ArrowRight, ArrowLeft,
  MessageSquare, ZoomIn, ZoomOut, RotateCcw, GitFork,
  Maximize2, Minimize2, Move, HelpCircle, X
} from 'lucide-react';

export const KnowledgeGraphCanvas = ({
  graphData,
  graphState,
  activeInvestigation,
  selectedRelationship,
  selectedNodeId,
  onSelectNode,
  theme = 'light',
  onSendToChat,
  isExpanded = false,
  onToggleExpand
}) => {
  const [layoutMode, setLayoutMode] = useState('flow'); // 'flow' (Left-to-Right DAG) or 'radial'
  const [zoomLevel, setZoomLevel] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const [hoveredNodeId, setHoveredNodeId] = useState(null);
  const [hoveredEdgeId, setHoveredEdgeId] = useState(null);

  const containerRef = useRef(null);

  // 1. Resolve Active Graph Data
  let activeGraph =
    graphData ||
    graphState ||
    activeInvestigation?.graph_snapshot ||
    activeInvestigation?.steps?.[activeInvestigation.steps?.length - 1]?.graph_snapshot;

  // If CSV investigation with concepts & relationships
  if ((!activeGraph || !activeGraph.nodes || activeGraph.nodes.length === 0) && activeInvestigation?.relationships) {
    const conceptNodes = (activeInvestigation.concepts || []).map((c, i) => ({
      id: c.id || `concept_${i}`,
      label: c.name || c.description || `Concept ${i + 1}`,
      node_type: 'hypothesis',
      confidence: c.confidence || 0.9,
      category: 'diagnostic_concept'
    }));
    const featureSet = new Set();
    const relEdges = (activeInvestigation.relationships || []).map((r, i) => {
      featureSet.add(r.source_feature);
      featureSet.add(r.target_feature);
      return {
        id: `rel_${i}`,
        source: r.source_feature,
        target: r.target_feature,
        relation_type: r.relationship_type || (r.correlation < 0 ? 'obstructs' : 'causes'),
        strength: r.correlation || 0.82,
        evidence: `Statistical correlation: ${(r.correlation || 0.8).toFixed(2)}`
      };
    });
    const featureNodes = Array.from(featureSet).map((f) => ({
      id: f,
      label: f.replace(/_/g, ' '),
      node_type: 'property',
      confidence: 0.95,
      category: 'telemetry_feature'
    }));
    activeGraph = {
      nodes: [...featureNodes, ...conceptNodes],
      edges: relEdges
    };
  }

  // Fallback if empty
  if (!activeGraph || !activeGraph.nodes || activeGraph.nodes.length === 0) {
    activeGraph = {
      nodes: [
        { id: 'irrigation_line', label: 'Continuous Drip Emitter', node_type: 'object', confidence: 0.98, bbox: [100, 100, 200, 200] },
        { id: 'soil_moisture', label: 'Root Zone Moisture (48%)', node_type: 'property', confidence: 0.94, bbox: [220, 220, 320, 320] },
        { id: 'soil_ph', label: 'Substrate pH (7.85)', node_type: 'property', confidence: 0.92 },
        { id: 'root_anoxia', label: 'Root Anoxia / Hypoxia', node_type: 'tool_result', confidence: 0.96 },
        { id: 'fe_block', label: 'Insoluble Fe³⁺ Hydroxides', node_type: 'property', confidence: 0.95 },
        { id: 'chlorosis', label: 'Interveinal Leaf Chlorosis', node_type: 'observation', confidence: 0.96, bbox: [180, 240, 680, 760] },
        { id: 'hypo_iron_def', label: 'Hypothesis: Fe²⁺ Uptake Block', node_type: 'hypothesis', confidence: 0.97 }
      ],
      edges: [
        { id: 'e1', source: 'irrigation_line', target: 'soil_moisture', relation_type: 'causes', strength: 0.95 },
        { id: 'e2', source: 'soil_moisture', target: 'root_anoxia', relation_type: 'causes', strength: 0.92 },
        { id: 'e3', source: 'soil_ph', target: 'fe_block', relation_type: 'causes', strength: -0.94 },
        { id: 'e4', source: 'root_anoxia', target: 'hypo_iron_def', relation_type: 'supports', strength: 0.88 },
        { id: 'e5', source: 'fe_block', target: 'hypo_iron_def', relation_type: 'supports', strength: 0.91 },
        { id: 'e6', source: 'hypo_iron_def', target: 'chlorosis', relation_type: 'causes', strength: 0.96 }
      ]
    };
  }

  // 2. Normalized Data Structures with intelligent type & label resolution
  const nodes = useMemo(() => {
    return (activeGraph.nodes || []).map((n, i) => {
      const d = n.data || n;
      const rawId = String(d.id || `node_${i}`);
      let rawLabel = String(d.label || rawId);

      // Clean formatted label
      let formattedLabel = rawLabel;
      if (formattedLabel === rawId) {
        formattedLabel = rawId
          .replace(/^hypo_/, 'Hypothesis: ')
          .replace(/_/g, ' ')
          .replace(/\b\w/g, (c) => c.toUpperCase());
      }

      // Robust node_type deduction
      let resolvedType = d.node_type || d.type || 'property';
      const idLower = rawId.toLowerCase();
      const labelLower = formattedLabel.toLowerCase();

      if (idLower.startsWith('hypo_') || labelLower.includes('hypothesis')) {
        resolvedType = 'hypothesis';
      } else if (idLower.includes('sensor') || labelLower.includes('sensor') || labelLower.includes('vwc') || labelLower.includes('ph ') || labelLower.includes('moisture')) {
        resolvedType = 'property';
      } else if (idLower.includes('leaf') || idLower.includes('chlorosis') || idLower.includes('crack') || labelLower.includes('chlorosis') || labelLower.includes('symptom')) {
        resolvedType = 'observation';
      } else if (idLower.includes('tool_') || labelLower.includes('detected') || labelLower.includes('anoxia') || labelLower.includes('bioavailable') || labelLower.includes('ndre') || labelLower.includes('gpr')) {
        resolvedType = 'tool_result';
      } else if (idLower.includes('emitter') || idLower.includes('pipe') || idLower.includes('irrigation') || idLower.includes('road')) {
        resolvedType = 'object';
      }

      return {
        id: rawId,
        label: formattedLabel,
        node_type: resolvedType,
        confidence: d.confidence !== undefined ? d.confidence : 0.88,
        bbox: d.bbox || null,
        visual_anchor: d.visual_anchor !== undefined ? d.visual_anchor : Boolean(d.bbox),
        category: d.category || 'general'
      };
    });
  }, [activeGraph]);

  const edges = useMemo(() => {
    return (activeGraph.edges || []).map((e, i) => {
      const d = e.data || e;
      return {
        id: String(d.id || `edge_${i}`),
        source: String(d.source || ''),
        target: String(d.target || ''),
        relation_type: d.relation_type || d.relation || 'causes',
        strength: d.strength !== undefined ? d.strength : 0.85,
        evidence: d.evidence || null
      };
    });
  }, [activeGraph]);

  // Quick Map & Degree Lookup
  const nodeMap = useMemo(() => {
    const map = new Map();
    nodes.forEach((n) => map.set(n.id, n));
    return map;
  }, [nodes]);

  const inDegreeMap = useMemo(() => {
    const deg = {};
    nodes.forEach((n) => (deg[n.id] = 0));
    edges.forEach((e) => {
      if (deg[e.target] !== undefined) deg[e.target]++;
    });
    return deg;
  }, [nodes, edges]);

  const outDegreeMap = useMemo(() => {
    const deg = {};
    nodes.forEach((n) => (deg[n.id] = 0));
    edges.forEach((e) => {
      if (deg[e.source] !== undefined) deg[e.source]++;
    });
    return deg;
  }, [nodes, edges]);

  // Compact Sleek Card dimensions for generous breathing room
  const CARD_W = 162;
  const CARD_H = 54;

  // 3. Layout Positioning Calculation
  const { nodePositions, canvasBounds } = useMemo(() => {
    const positions = {};

    if (layoutMode === 'flow') {
      // 4-Column Left-to-Right Causal Architecture:
      // Col 0: Inputs & Baseline Telemetry (in-degree 0 or 'object')
      // Col 1: Mediating Measurements & Tool Findings ('tool_result' or mediated 'property')
      // Col 2: Observable Symptoms & Grounded Features ('observation')
      // Col 3: Root Cause Hypotheses & Diagnoses ('hypothesis' or out-degree 0)
      const cols = [[], [], [], []];

      nodes.forEach((node) => {
        if (node.node_type === 'hypothesis') {
          cols[3].push(node);
        } else if (node.node_type === 'observation') {
          cols[2].push(node);
        } else if (node.node_type === 'tool_result') {
          cols[1].push(node);
        } else if (inDegreeMap[node.id] === 0 || node.node_type === 'object') {
          cols[0].push(node);
        } else {
          cols[1].push(node);
        }
      });

      // Avoid completely empty middle columns by shifting if needed
      if (cols[1].length === 0 && cols[0].length > 2) {
        cols[1].push(cols[0].pop());
      }
      if (cols[2].length === 0 && cols[1].length > 2) {
        cols[2].push(cols[1].pop());
      }

      const activeColIndices = cols.map((col, idx) => ({ col, idx })).filter((c) => c.col.length > 0);
      const totalActiveCols = activeColIndices.length || 1;

      const startX = 40;
      const colGap = 290;
      const maxRows = Math.max(...cols.map((c) => c.length), 1);
      const rowGap = 106;
      const totalHeight = Math.max(480, maxRows * rowGap + 90);

      activeColIndices.forEach(({ col }, colStep) => {
        const x = startX + colStep * colGap;
        const colHeight = col.length * rowGap;
        const topOffsetY = Math.max(40, (totalHeight - colHeight) / 2);

        col.forEach((node, rowIdx) => {
          positions[node.id] = {
            x,
            y: topOffsetY + rowIdx * rowGap
          };
        });
      });

      const totalWidth = startX + totalActiveCols * colGap + 60;
      return {
        nodePositions: positions,
        canvasBounds: { width: Math.max(1050, totalWidth), height: totalHeight }
      };
    } else {
      // Radial Hub Layout
      const total = nodes.length;
      const centerX = 440;
      const centerY = 240;
      const radiusX = Math.min(320, 240 + total * 8);
      const radiusY = Math.min(180, 140 + total * 6);

      nodes.forEach((node, idx) => {
        if (node.node_type === 'hypothesis' && idx === 0) {
          positions[node.id] = { x: centerX - CARD_W / 2, y: centerY - CARD_H / 2 };
          return;
        }
        const angle = (2 * Math.PI * idx) / total - Math.PI / 2;
        const x = centerX + radiusX * Math.cos(angle) - CARD_W / 2;
        const y = centerY + radiusY * Math.sin(angle) - CARD_H / 2;
        positions[node.id] = { x: Math.round(x), y: Math.round(y) };
      });

      return {
        nodePositions: positions,
        canvasBounds: { width: 900, height: 480 }
      };
    }
  }, [nodes, inDegreeMap, layoutMode]);

  // 4. Trace Ancestors and Descendants for Interactive Causal Highlighting
  const activeFocusId = hoveredNodeId || selectedNodeId;

  const { ancestors, descendants, activeEdgeSet } = useMemo(() => {
    if (!activeFocusId) {
      return { ancestors: new Set(), descendants: new Set(), activeEdgeSet: new Set() };
    }

    const anc = new Set();
    const desc = new Set();
    const edgeSet = new Set();

    // Trace ancestors (incoming causes)
    const traceUp = (currId) => {
      edges.forEach((e) => {
        if (e.target === currId && !anc.has(e.source)) {
          anc.add(e.source);
          edgeSet.add(e.id);
          traceUp(e.source);
        }
      });
    };

    // Trace descendants (outgoing consequences)
    const traceDown = (currId) => {
      edges.forEach((e) => {
        if (e.source === currId && !desc.has(e.target)) {
          desc.add(e.target);
          edgeSet.add(e.id);
          traceDown(e.target);
        }
      });
    };

    traceUp(activeFocusId);
    traceDown(activeFocusId);

    // Also include direct edges touching activeFocusId
    edges.forEach((e) => {
      if (e.source === activeFocusId || e.target === activeFocusId) {
        edgeSet.add(e.id);
      }
    });

    return { ancestors: anc, descendants: desc, activeEdgeSet: edgeSet };
  }, [activeFocusId, edges]);

  // 5. Selected Node Details for Docked Bottom Inspector
  const activeInspectedNode = selectedNodeId ? nodeMap.get(selectedNodeId) : null;
  const directInflowNodes = activeInspectedNode
    ? edges.filter((e) => e.target === activeInspectedNode.id).map((e) => ({ edge: e, node: nodeMap.get(e.source) })).filter((x) => x.node)
    : [];
  const directOutflowNodes = activeInspectedNode
    ? edges.filter((e) => e.source === activeInspectedNode.id).map((e) => ({ edge: e, node: nodeMap.get(e.target) })).filter((x) => x.node)
    : [];

  // Mouse drag-to-pan handler
  const handleMouseDown = (e) => {
    if (e.button !== 0) return; // Only left click
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    setPan({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // Wheel zoom handler
  const handleWheel = (e) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.08 : 0.92;
    setZoomLevel((prev) => Math.max(0.4, Math.min(2.5, prev * zoomFactor)));
  };

  const handleFitToScreen = () => {
    setPan({ x: 0, y: 0 });
    if (containerRef.current) {
      const containerW = containerRef.current.clientWidth || 800;
      const targetW = canvasBounds.width || 900;
      const optimalZoom = Math.min(1.1, Math.max(0.65, (containerW - 40) / targetW));
      setZoomLevel(optimalZoom);
    } else {
      setZoomLevel(1);
    }
  };

  // Auto-fit on initial mount or layout switch
  useEffect(() => {
    handleFitToScreen();
  }, [layoutMode, isExpanded]);

  // Helper for Node Theme
  const getNodeTheme = (type) => {
    switch (type) {
      case 'object':
        return {
          headerBg: '#f0fdf4',
          headerText: '#166534',
          border: '#4ade80',
          chipBg: '#dcfce7',
          tag: 'PHYSICAL OBJECT',
          badgeColor: '#16a34a'
        };
      case 'property':
        return {
          headerBg: '#eff6ff',
          headerText: '#1e40af',
          border: '#60a5fa',
          chipBg: '#dbeafe',
          tag: 'SENSOR MEASUREMENT',
          badgeColor: '#2563eb'
        };
      case 'observation':
        return {
          headerBg: '#ecfeff',
          headerText: '#0e7490',
          border: '#22d3ee',
          chipBg: '#cffafe',
          tag: 'VISUAL SYMPTOM',
          badgeColor: '#0891b2'
        };
      case 'hypothesis':
        return {
          headerBg: '#fffbeb',
          headerText: '#92400e',
          border: '#f59e0b',
          chipBg: '#fef3c7',
          tag: 'ROOT CAUSE HYPOTHESIS',
          badgeColor: '#d97706'
        };
      case 'tool_result':
        return {
          headerBg: '#fdf4ff',
          headerText: '#86198f',
          border: '#c084fc',
          chipBg: '#fae8ff',
          tag: 'EMPIRICAL EVIDENCE',
          badgeColor: '#9333ea'
        };
      default:
        return {
          headerBg: '#f8fafc',
          headerText: '#475569',
          border: '#94a3b8',
          chipBg: '#e2e8f0',
          tag: 'ENTITY',
          badgeColor: '#64748b'
        };
    }
  };

  const getRelationColor = (relation) => {
    const rel = (relation || '').toLowerCase();
    if (rel.includes('obstruct') || rel.includes('inhibit') || rel.includes('contradict')) return '#f43f5e';
    if (rel.includes('cause') || rel.includes('trigger')) return '#f59e0b';
    if (rel.includes('support') || rel.includes('confirm')) return '#10b981';
    if (rel.includes('measure') || rel.includes('indicate')) return '#0284c7';
    return '#64748b';
  };

  return (
    <div className="causal-graph-container" style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      background: '#ffffff',
      position: 'relative',
      borderRadius: '8px',
      overflow: 'hidden',
      userSelect: 'none'
    }}>
      {/* 1. Top Header Toolbar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.55rem 1rem',
        borderBottom: '1px solid #e2e8f0',
        background: '#f8fafc',
        zIndex: 5
      }}>
        {/* Title and Stats */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <div style={{
            width: '28px',
            height: '28px',
            borderRadius: '6px',
            background: 'rgba(2, 132, 199, 0.1)',
            color: '#0284c7',
            display: 'grid',
            placeItems: 'center'
          }}>
            <GitFork size={15} />
          </div>
          <div>
            <div style={{ fontSize: '0.82rem', fontWeight: '700', color: '#0f172a', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span>Causal Reasoning Pipeline</span>
              <span style={{
                fontSize: '0.68rem',
                fontWeight: '600',
                padding: '0.1rem 0.45rem',
                borderRadius: '10px',
                background: '#e0f2fe',
                color: '#0369a1'
              }}>
                {nodes.length} nodes · {edges.length} edges
              </span>
            </div>
            <div style={{ fontSize: '0.68rem', color: '#64748b' }}>
              {layoutMode === 'flow' ? 'Left-to-Right Causal Flow (Inputs → Mediators → Symptoms → Diagnosis)' : 'Concentric Radial Graph'}
            </div>
          </div>
        </div>

        {/* Action Controls (Layout Switcher, Zoom, Pan & Fullscreen) */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {/* Layout Toggle */}
          <div style={{
            display: 'flex',
            background: '#e2e8f0',
            padding: '2px',
            borderRadius: '6px',
            gap: '2px'
          }}>
            <button
              style={{
                border: 'none',
                background: layoutMode === 'flow' ? '#ffffff' : 'transparent',
                color: layoutMode === 'flow' ? '#0f172a' : '#64748b',
                fontWeight: layoutMode === 'flow' ? '700' : '500',
                padding: '0.25rem 0.55rem',
                fontSize: '0.72rem',
                borderRadius: '4px',
                cursor: 'pointer',
                boxShadow: layoutMode === 'flow' ? '0 1px 2px rgba(0,0,0,0.06)' : 'none'
              }}
              onClick={() => setLayoutMode('flow')}
              title="Causal Flow (Left-to-Right Pipeline)"
            >
              Causal Flow
            </button>
            <button
              style={{
                border: 'none',
                background: layoutMode === 'radial' ? '#ffffff' : 'transparent',
                color: layoutMode === 'radial' ? '#0f172a' : '#64748b',
                fontWeight: layoutMode === 'radial' ? '700' : '500',
                padding: '0.25rem 0.55rem',
                fontSize: '0.72rem',
                borderRadius: '4px',
                cursor: 'pointer',
                boxShadow: layoutMode === 'radial' ? '0 1px 2px rgba(0,0,0,0.06)' : 'none'
              }}
              onClick={() => setLayoutMode('radial')}
              title="Radial Graph Layout"
            >
              Radial Hub
            </button>
          </div>

          {/* Zoom Controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '2px' }}>
            <button
              style={{
                width: '26px',
                height: '26px',
                border: '1px solid #cbd5e1',
                background: '#ffffff',
                borderRadius: '4px',
                display: 'grid',
                placeItems: 'center',
                cursor: 'pointer'
              }}
              onClick={() => setZoomLevel((z) => Math.max(0.4, z - 0.15))}
              title="Zoom Out (or scroll down)"
            >
              <ZoomOut size={13} color="#475569" />
            </button>
            <span style={{ fontSize: '0.7rem', color: '#64748b', minWidth: '34px', textAlign: 'center', fontWeight: '600' }}>
              {Math.round(zoomLevel * 100)}%
            </span>
            <button
              style={{
                width: '26px',
                height: '26px',
                border: '1px solid #cbd5e1',
                background: '#ffffff',
                borderRadius: '4px',
                display: 'grid',
                placeItems: 'center',
                cursor: 'pointer'
              }}
              onClick={() => setZoomLevel((z) => Math.min(2.5, z + 0.15))}
              title="Zoom In (or scroll up)"
            >
              <ZoomIn size={13} color="#475569" />
            </button>
            <button
              style={{
                padding: '0 0.45rem',
                height: '26px',
                border: '1px solid #cbd5e1',
                background: '#ffffff',
                borderRadius: '4px',
                display: 'flex',
                alignItems: 'center',
                gap: '3px',
                fontSize: '0.68rem',
                color: '#475569',
                cursor: 'pointer',
                fontWeight: '600'
              }}
              onClick={handleFitToScreen}
              title="Fit to Screen and Center"
            >
              <RotateCcw size={11} />
              <span>Fit</span>
            </button>
          </div>

          {/* Fullscreen Expansion Action */}
          {onToggleExpand && (
            <button
              style={{
                height: '26px',
                padding: '0 0.55rem',
                border: '1px solid #0284c7',
                background: isExpanded ? '#0284c7' : 'rgba(2, 132, 199, 0.08)',
                color: isExpanded ? '#ffffff' : '#0284c7',
                borderRadius: '4px',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '0.7rem',
                fontWeight: '700',
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
              onClick={onToggleExpand}
              title={isExpanded ? 'Restore window size' : 'Expand full-width'}
            >
              {isExpanded ? <Minimize2 size={12} /> : <Maximize2 size={12} />}
              <span>{isExpanded ? 'Exit Fullscreen' : 'Fullscreen'}</span>
            </button>
          )}
        </div>
      </div>

      {/* 2. Interactive SVG Canvas Viewport (With Pan, Drag, and Zoom) */}
      <div
        ref={containerRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
        style={{
          flex: 1,
          position: 'relative',
          overflow: 'hidden',
          background: '#fafafa',
          backgroundImage: 'radial-gradient(#e2e8f0 1px, transparent 1px)',
          backgroundSize: '24px 24px',
          cursor: isDragging ? 'grabbing' : 'grab'
        }}
      >
        <svg
          width="100%"
          height="100%"
          style={{ display: 'block', overflow: 'visible' }}
          onClick={() => {
            if (onSelectNode) onSelectNode(null);
          }}
        >
          <defs>
            {/* Arrowhead Markers */}
            <marker id="arrow-causes" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 1 L 10 5 L 0 9 z" fill="#f59e0b" />
            </marker>
            <marker id="arrow-supports" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 1 L 10 5 L 0 9 z" fill="#10b981" />
            </marker>
            <marker id="arrow-obstructs" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 1 L 10 5 L 0 9 z" fill="#f43f5e" />
            </marker>
            <marker id="arrow-default" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 1 L 10 5 L 0 9 z" fill="#0284c7" />
            </marker>

            {/* Glowing Drop Shadows */}
            <filter id="active-card-shadow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="4" stdDeviation="6" floodColor="rgba(2, 132, 199, 0.35)" />
            </filter>
            <filter id="cause-card-shadow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="4" stdDeviation="5" floodColor="rgba(245, 158, 11, 0.35)" />
            </filter>
            <filter id="effect-card-shadow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="4" stdDeviation="5" floodColor="rgba(16, 185, 129, 0.35)" />
            </filter>
            <filter id="standard-card-shadow" x="-10%" y="-10%" width="120%" height="120%">
              <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="rgba(0, 0, 0, 0.06)" />
            </filter>
          </defs>

          {/* Scaled & Panned Group */}
          <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoomLevel})`}>
            {/* Causal Edges Layer */}
            <g className="edges-layer">
              {edges.map((edge) => {
                const srcPos = nodePositions[edge.source];
                const tgtPos = nodePositions[edge.target];
                if (!srcPos || !tgtPos) return null;

                const isDirectlyActive = activeEdgeSet.has(edge.id);
                const isDimmed = activeFocusId && !isDirectlyActive;
                const isHoveredEdge = hoveredEdgeId === edge.id;

                // Smooth cubic bezier curve from right-center of source to left-center of target
                const startX = srcPos.x + CARD_W;
                const startY = srcPos.y + CARD_H / 2;
                const endX = tgtPos.x;
                const endY = tgtPos.y + CARD_H / 2;

                // Calculate smooth bezier control points
                const dx = (endX - startX) * 0.52;
                const cp1X = startX + dx;
                const cp1Y = startY;
                const cp2X = endX - dx;
                const cp2Y = endY;

                let pathD = '';
                if (layoutMode === 'flow' && endX > startX + 20) {
                  pathD = `M ${startX} ${startY} C ${cp1X} ${cp1Y}, ${cp2X} ${cp2Y}, ${endX} ${endY}`;
                } else {
                  // Curved loop if backwards or radial
                  const midX = (startX + endX) / 2;
                  const midY = (startY + endY) / 2 - 25;
                  pathD = `M ${startX} ${startY} Q ${midX} ${midY}, ${endX} ${endY}`;
                }

                const edgeColor = getRelationColor(edge.relation_type);
                let marker = 'url(#arrow-default)';
                if (edge.relation_type?.includes('cause') || edge.relation_type?.includes('trigger')) marker = 'url(#arrow-causes)';
                if (edge.relation_type?.includes('support') || edge.relation_type?.includes('confirm')) marker = 'url(#arrow-supports)';
                if (edge.relation_type?.includes('obstruct') || edge.relation_type?.includes('inhibit')) marker = 'url(#arrow-obstructs)';

                // Stagger chip position along curve to prevent labels from colliding with each other
                const edgesToSameTarget = edges.filter((e) => e.target === edge.target);
                const targetIdx = edgesToSameTarget.findIndex((e) => e.id === edge.id);
                const t = edgesToSameTarget.length > 1 ? 0.36 + Math.min(targetIdx, 2) * 0.16 : 0.46;
                const u = 1 - t;

                let chipX = (startX + endX) / 2;
                let chipY = (startY + endY) / 2;
                if (layoutMode === 'flow' && endX > startX + 20) {
                  chipX = u * u * u * startX + 3 * u * u * t * cp1X + 3 * u * t * t * cp2X + t * t * t * endX;
                  chipY = u * u * u * startY + 3 * u * u * t * cp1Y + 3 * u * t * t * cp2Y + t * t * t * endY;
                }

                return (
                  <g
                    key={edge.id}
                    style={{
                      opacity: isDimmed ? 0.15 : 1,
                      transition: 'opacity 0.2s ease'
                    }}
                    onMouseEnter={() => setHoveredEdgeId(edge.id)}
                    onMouseLeave={() => setHoveredEdgeId(null)}
                  >
                    {/* Interaction hitbox */}
                    <path
                      d={pathD}
                      fill="none"
                      stroke="transparent"
                      strokeWidth="16"
                      style={{ cursor: 'pointer' }}
                    />

                    {/* Visual Causal Line */}
                    <path
                      d={pathD}
                      fill="none"
                      stroke={edgeColor}
                      strokeWidth={isDirectlyActive ? 3.5 : isHoveredEdge ? 3 : 1.8}
                      strokeDasharray={edge.relation_type?.includes('obstruct') ? '5,4' : 'none'}
                      markerEnd={marker}
                      style={{ transition: 'stroke-width 0.2s ease, stroke 0.2s ease' }}
                    />

                    {/* Relationship Badge Chip */}
                    <g transform={`translate(${chipX}, ${chipY})`} style={{ cursor: 'pointer' }}>
                      <rect
                        x="-34"
                        y="-9"
                        width="68"
                        height="18"
                        rx="9"
                        fill="#ffffff"
                        stroke={edgeColor}
                        strokeWidth={isDirectlyActive || isHoveredEdge ? 2 : 1.5}
                        filter="url(#standard-card-shadow)"
                      />
                      <text
                        x="0"
                        y="3.5"
                        textAnchor="middle"
                        fill={edgeColor}
                        fontSize="8.5px"
                        fontFamily="JetBrains Mono, monospace"
                        fontWeight="700"
                        letterSpacing="0.2px"
                      >
                        {edge.relation_type.toUpperCase()}
                      </text>
                    </g>
                  </g>
                );
              })}
            </g>

            {/* Causal Nodes Layer */}
            <g className="nodes-layer">
              {nodes.map((node) => {
                const pos = nodePositions[node.id];
                if (!pos) return null;

                const isSelected = selectedNodeId === node.id;
                const isHovered = hoveredNodeId === node.id;
                const isAncestor = ancestors.has(node.id);
                const isDescendant = descendants.has(node.id);

                const isFocused = isSelected || isHovered;
                const isPathRelated = isAncestor || isDescendant || isFocused;
                const isDimmed = activeFocusId && !isPathRelated;

                const themeStyle = getNodeTheme(node.node_type);

                let cardShadow = 'url(#standard-card-shadow)';
                let strokeColor = themeStyle.border;
                let strokeWidth = 1.5;

                if (isFocused) {
                  cardShadow = 'url(#active-card-shadow)';
                  strokeColor = '#0284c7';
                  strokeWidth = 2.5;
                } else if (isAncestor) {
                  cardShadow = 'url(#cause-card-shadow)';
                  strokeColor = '#f59e0b';
                  strokeWidth = 2;
                } else if (isDescendant) {
                  cardShadow = 'url(#effect-card-shadow)';
                  strokeColor = '#10b981';
                  strokeWidth = 2;
                }

                // Multi-line label split
                const words = (node.label || node.id).split(' ');
                let line1 = words.slice(0, 3).join(' ');
                let line2 = words.slice(3, 7).join(' ');
                if (words.length > 7) line2 += '...';

                return (
                  <g
                    key={node.id}
                    transform={`translate(${pos.x}, ${pos.y})`}
                    style={{
                      cursor: 'pointer',
                      opacity: isDimmed ? 0.22 : 1,
                      transition: 'transform 0.2s ease, opacity 0.2s ease'
                    }}
                    onClick={(e) => {
                      e.stopPropagation();
                      if (onSelectNode) {
                        onSelectNode(isSelected ? null : node.id);
                      }
                    }}
                    onMouseEnter={() => setHoveredNodeId(node.id)}
                    onMouseLeave={() => setHoveredNodeId(null)}
                  >
                    {/* Causal Pathway Status Glow */}
                    {isAncestor && (
                      <text
                        x="0"
                        y="-5"
                        fill="#b45309"
                        fontSize="8.5px"
                        fontFamily="Outfit, sans-serif"
                        fontWeight="700"
                      >
                        ▲ UPSTREAM CAUSE
                      </text>
                    )}
                    {isDescendant && (
                      <text
                        x="0"
                        y="-5"
                        fill="#047857"
                        fontSize="8.5px"
                        fontFamily="Outfit, sans-serif"
                        fontWeight="700"
                      >
                        ▼ CONSEQUENCE
                      </text>
                    )}

                    {/* Main Node Card Body */}
                    <rect
                      width={CARD_W}
                      height={CARD_H}
                      rx="7"
                      ry="7"
                      fill="#ffffff"
                      stroke={strokeColor}
                      strokeWidth={strokeWidth}
                      filter={cardShadow}
                    />

                    {/* Card Header Strip with Type Badge */}
                    <rect
                      x="0"
                      y="0"
                      width={CARD_W}
                      height="16"
                      rx="7"
                      ry="7"
                      fill={themeStyle.headerBg}
                    />
                    <rect
                      x="0"
                      y="10"
                      width={CARD_W}
                      height="6"
                      fill={themeStyle.headerBg}
                    />

                    {/* Type Tag text */}
                    <text
                      x="6"
                      y="11.5"
                      fill={themeStyle.headerText}
                      fontSize="7.5px"
                      fontFamily="JetBrains Mono, monospace"
                      fontWeight="700"
                      letterSpacing="0.3px"
                    >
                      {themeStyle.tag}
                    </text>

                    {/* Confidence Pill in Header */}
                    <rect
                      x={CARD_W - 36}
                      y="2.5"
                      width="30"
                      height="11"
                      rx="5.5"
                      fill={themeStyle.chipBg}
                    />
                    <text
                      x={CARD_W - 21}
                      y="10.5"
                      textAnchor="middle"
                      fill={themeStyle.badgeColor}
                      fontSize="7.5px"
                      fontFamily="JetBrains Mono, monospace"
                      fontWeight="700"
                    >
                      {Math.round(node.confidence * 100)}%
                    </text>

                    {/* Node Title (Line 1 & 2) */}
                    <text
                      x="6"
                      y="29"
                      fill="#0f172a"
                      fontSize="10.5px"
                      fontFamily="Outfit, sans-serif"
                      fontWeight="600"
                    >
                      {line1}
                    </text>
                    {line2 && (
                      <text
                        x="6"
                        y="41"
                        fill="#334155"
                        fontSize="9.5px"
                        fontFamily="Outfit, sans-serif"
                        fontWeight="500"
                      >
                        {line2}
                      </text>
                    )}

                    {/* Visual Grounding Reticle Badge (if anchored in image) */}
                    {node.visual_anchor && (
                      <g transform={`translate(6, ${CARD_H - 8})`}>
                        <circle cx="3" cy="-1" r="2" fill="#0284c7" />
                        <text x="7" y="1" fill="#0369a1" fontSize="7px" fontFamily="Outfit, sans-serif" fontWeight="700">
                          GROUNDED
                        </text>
                      </g>
                    )}

                    {/* Connection Ports */}
                    {layoutMode === 'flow' && (
                      <>
                        <circle cx="0" cy={CARD_H / 2} r="3.5" fill="#ffffff" stroke={themeStyle.border} strokeWidth="1.5" />
                        <circle cx={CARD_W} cy={CARD_H / 2} r="3.5" fill="#ffffff" stroke={themeStyle.border} strokeWidth="1.5" />
                      </>
                    )}
                  </g>
                );
              })}
            </g>
          </g>
        </svg>
      </div>

      {/* 3. Dedicated Docked Bottom Inspector Panel (Zero Occlusion of Graph!) */}
      {activeInspectedNode ? (
        <div style={{
          height: '115px',
          borderTop: '1px solid #cbd5e1',
          background: '#ffffff',
          display: 'grid',
          gridTemplateColumns: 'minmax(220px, 1.2fr) minmax(200px, 1.3fr) minmax(200px, 1.3fr) auto',
          gap: '1rem',
          padding: '0.65rem 1rem',
          boxShadow: '0 -4px 15px rgba(0, 0, 0, 0.04)',
          zIndex: 10,
          alignItems: 'center'
        }}>
          {/* Column 1: Node Title, Type & Confidence */}
          <div style={{ borderRight: '1px solid #f1f5f9', paddingRight: '0.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '2px' }}>
              <span style={{
                fontSize: '0.65rem',
                fontWeight: '700',
                padding: '0.1rem 0.4rem',
                borderRadius: '4px',
                background: getNodeTheme(activeInspectedNode.node_type).chipBg,
                color: getNodeTheme(activeInspectedNode.node_type).headerText
              }}>
                {getNodeTheme(activeInspectedNode.node_type).tag}
              </span>
              {activeInspectedNode.visual_anchor && (
                <span style={{ fontSize: '0.65rem', fontWeight: '700', color: '#0284c7' }}>
                  ● GROUNDED
                </span>
              )}
            </div>
            <h4 style={{ margin: '0.15rem 0', fontSize: '0.86rem', fontWeight: '700', color: '#0f172a', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {activeInspectedNode.label}
            </h4>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
              <span style={{ fontSize: '0.7rem', color: '#64748b' }}>Confidence:</span>
              <div style={{ height: '5px', width: '90px', background: '#e2e8f0', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{
                  height: '100%',
                  width: `${Math.round(activeInspectedNode.confidence * 100)}%`,
                  background: 'linear-gradient(90deg, #38bdf8, #10b981)',
                  borderRadius: '3px'
                }} />
              </div>
              <strong style={{ fontSize: '0.72rem', color: '#0f172a' }}>{Math.round(activeInspectedNode.confidence * 100)}%</strong>
            </div>
          </div>

          {/* Column 2: Direct Causes (Inflow) */}
          <div style={{ borderRight: '1px solid #f1f5f9', paddingRight: '0.75rem', overflowY: 'auto', maxHeight: '90px' }}>
            <div style={{ fontSize: '0.68rem', fontWeight: '700', color: '#b45309', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <ArrowLeft size={11} />
              <span>Direct Causes ({directInflowNodes.length}):</span>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
              {directInflowNodes.length > 0 ? (
                directInflowNodes.map(({ node }) => (
                  <span
                    key={node.id}
                    onClick={() => onSelectNode(node.id)}
                    style={{
                      background: '#fef3c7',
                      color: '#92400e',
                      padding: '0.15rem 0.4rem',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '0.68rem',
                      fontWeight: '600',
                      border: '1px solid #fde68a'
                    }}
                    title="Click to trace this cause"
                  >
                    ← {node.label}
                  </span>
                ))
              ) : (
                <span style={{ color: '#94a3b8', fontSize: '0.68rem', fontStyle: 'italic' }}>None (Root Environmental Input)</span>
              )}
            </div>
          </div>

          {/* Column 3: Direct Consequences (Outflow) */}
          <div style={{ overflowY: 'auto', maxHeight: '90px', paddingRight: '0.5rem' }}>
            <div style={{ fontSize: '0.68rem', fontWeight: '700', color: '#047857', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span>Direct Impacts ({directOutflowNodes.length}):</span>
              <ArrowRight size={11} />
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
              {directOutflowNodes.length > 0 ? (
                directOutflowNodes.map(({ node }) => (
                  <span
                    key={node.id}
                    onClick={() => onSelectNode(node.id)}
                    style={{
                      background: '#d1fae5',
                      color: '#065f46',
                      padding: '0.15rem 0.4rem',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '0.68rem',
                      fontWeight: '600',
                      border: '1px solid #a7f3d0'
                    }}
                    title="Click to trace this impact"
                  >
                    {node.label} →
                  </span>
                ))
              ) : (
                <span style={{ color: '#94a3b8', fontSize: '0.68rem', fontStyle: 'italic' }}>None (Terminal Effect / Diagnosis)</span>
              )}
            </div>
          </div>

          {/* Column 4: Actions & Close */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', alignItems: 'flex-end', justifyContent: 'center' }}>
            <button
              style={{
                border: 'none',
                background: '#f1f5f9',
                borderRadius: '4px',
                width: '20px',
                height: '20px',
                cursor: 'pointer',
                display: 'grid',
                placeItems: 'center',
                color: '#64748b'
              }}
              onClick={() => onSelectNode(null)}
              title="Close Docked Inspector"
            >
              <X size={12} />
            </button>
            {onSendToChat && (
              <button
                style={{
                  padding: '0.35rem 0.75rem',
                  background: '#0284c7',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '6px',
                  fontSize: '0.72rem',
                  fontWeight: '600',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '5px',
                  whiteSpace: 'nowrap'
                }}
                onClick={() => {
                  onSendToChat(`Can you explain the causal mechanism and empirical evidence for "${activeInspectedNode.label}"?`);
                }}
              >
                <MessageSquare size={12} />
                <span>Inquire in Chat</span>
              </button>
            )}
          </div>
        </div>
      ) : (
        /* 4. Bottom Legend & Navigation Guide (When no node is selected) */
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0.45rem 1rem',
          borderTop: '1px solid #e2e8f0',
          background: '#ffffff',
          fontSize: '0.7rem',
          color: '#475569'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span style={{ fontWeight: '700', color: '#0f172a' }}>Legend:</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#4ade80' }} />
              <span>Object</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#60a5fa' }} />
              <span>Sensor</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#22d3ee' }} />
              <span>Symptom</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#f59e0b' }} />
              <span>Hypothesis</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#c084fc' }} />
              <span>Evidence</span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '0.68rem', color: '#64748b' }}>
            <span>💡 <strong>Tip:</strong> Drag to pan · Scroll to zoom · Click node to inspect causal chain</span>
            <span style={{ color: '#b45309' }}>▲ Amber = Upstream Cause</span>
            <span style={{ color: '#047857' }}>▼ Green = Downstream Impact</span>
          </div>
        </div>
      )}
    </div>
  );
};
