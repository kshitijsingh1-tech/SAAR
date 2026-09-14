import React, { useState, useMemo, useRef, useEffect } from 'react';
import {
  Network, Sparkles, Eye, ArrowRight, ArrowLeft,
  MessageSquare, ZoomIn, ZoomOut, RotateCcw, GitFork,
  Maximize2, Minimize2, Move, HelpCircle, X, Search,
  Filter, Layers, CheckCircle, AlertTriangle, ShieldCheck
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
  const [zoomLevel, setZoomLevel] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const isDark = theme === 'dark';

  const [hoveredNodeId, setHoveredNodeId] = useState(null);
  const [hoveredEdgeId, setHoveredEdgeId] = useState(null);
  const [activeShotFilter, setActiveShotFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

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

  // Fallback empty state
  if (!activeGraph || !activeGraph.nodes) {
    activeGraph = {
      nodes: [],
      edges: []
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

      if (idLower.startsWith('player') || idLower.includes('player_main') || resolvedType === 'player') {
        resolvedType = 'player';
      } else if (idLower.startsWith('court') || idLower.includes('court_plane') || resolvedType === 'court') {
        resolvedType = 'court';
      } else if (idLower.startsWith('rag_') || labelLower.includes('rag:')) {
        resolvedType = 'rag';
      } else if (idLower.startsWith('movement') || resolvedType === 'movement') {
        resolvedType = 'movement';
      } else if (idLower.startsWith('shot_') || resolvedType === 'shot') {
        resolvedType = 'shot';
      } else if (idLower.startsWith('type_shot') || resolvedType === 'shot_type') {
        resolvedType = 'stroke_class';
      } else if (idLower.startsWith('joint_') || resolvedType === 'joint' || resolvedType === 'kinematics') {
        resolvedType = 'joint_kinematics';
      } else if (idLower.startsWith('seq_') || idLower.includes('kinetic_chain') || resolvedType === 'evidence' && labelLower.includes('kinetic')) {
        resolvedType = 'kinetic_chain';
      } else if (idLower.includes('racket_speed') || idLower.includes('shuttle_speed') || resolvedType === 'speed' || resolvedType === 'racket' || resolvedType === 'shuttle') {
        resolvedType = 'speed_metric';
      } else if (idLower.startsWith('hypo_') || labelLower.includes('hypothesis')) {
        resolvedType = 'hypothesis';
      } else if (idLower.startsWith('rec_') || labelLower.includes('rec #') || resolvedType === 'recommendation') {
        resolvedType = 'recommendation';
      } else if (idLower.includes('limitation') || resolvedType === 'limitation') {
        resolvedType = 'limitation';
      } else if (idLower.includes('energy') || idLower.includes('distribution') || resolvedType === 'metric') {
        resolvedType = 'metric';
      } else if (idLower.includes('sensor') || labelLower.includes('sensor') || labelLower.includes('vwc') || labelLower.includes('ph ') || labelLower.includes('moisture')) {
        resolvedType = 'property';
      } else if (idLower.includes('leaf') || idLower.includes('chlorosis') || idLower.includes('crack') || labelLower.includes('chlorosis') || labelLower.includes('symptom')) {
        resolvedType = 'observation';
      } else if (idLower.includes('tool_') || labelLower.includes('detected') || labelLower.includes('anoxia') || labelLower.includes('bioavailable') || labelLower.includes('ndre') || labelLower.includes('gpr')) {
        resolvedType = 'tool_result';
      } else if (idLower.includes('emitter') || idLower.includes('pipe') || idLower.includes('irrigation') || idLower.includes('road')) {
        resolvedType = 'object';
      }

      // Extract shot index if node belongs to a shot
      let shotRefId = null;
      const shotMatch = rawId.match(/shot_0*(\d+)/i) || rawId.match(/shot_(\d+)/i);
      if (shotMatch) {
        shotRefId = `shot_${shotMatch[1]}`;
      }

      return {
        id: rawId,
        label: formattedLabel,
        node_type: resolvedType,
        confidence: d.confidence !== undefined ? d.confidence : 0.88,
        bbox: d.bbox || null,
        visual_anchor: d.visual_anchor !== undefined ? d.visual_anchor : Boolean(d.bbox),
        category: d.category || 'general',
        shotRefId,
        properties: d.properties || {}
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
        strength: d.strength !== undefined ? d.strength : (d.confidence || 0.85),
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

  // Detect all distinct shots in graph
  const detectedShots = useMemo(() => {
    const shotList = [];
    nodes.forEach((n) => {
      if (n.node_type === 'shot') {
        shotList.push(n);
      }
    });
    // Sort shots by label / ID
    shotList.sort((a, b) => a.id.localeCompare(b.id, undefined, { numeric: true }));
    return shotList;
  }, [nodes]);

  // Dimensions of node cards
  const CARD_W = 184;
  const CARD_H = 58;

  // 3. Intelligent Multi-Stage Corridor DAG Layout (Structured Horizontal Pipeline)
  const { nodePositions, canvasBounds, stageColumns } = useMemo(() => {
    const positions = {};

    // Check if this graph is a Badminton Rally or Multi-Shot Sport Graph
    const isShotBasedGraph = detectedShots.length > 0;

    if (isShotBasedGraph) {
      // 6-Column Structured Biomechanical Architecture:
      // Col 0: Global Entities & Video Baseline (Player, Court, RAG)
      // Col 1: Rally Events & Macro Dynamics (Shot Events, Movement, Rally Distribution)
      // Col 2: Per-Shot Joint Kinematics & Ballistic Sensors (Class, Elbow, Shoulder, Knee, Hip, Speed)
      // Col 3: Kinetic Chain Sequences & Epistemic Gate Verifications (Kinetic Chain Confirmed, Efficiency Gate)
      // Col 4: Bayesian Causal Hypotheses (H1, H2, H3, H4)
      // Col 5: Actionable Prescriptions & Recommendations (Rec 1, Rec 2, Rec 3)

      const colX = [40, 290, 560, 940, 1220, 1500];
      const stageTitles = [
        { title: 'GLOBAL INPUTS', sub: 'Entities & Calibration', x: colX[0] },
        { title: 'RALLY EVENTS', sub: 'Strokes & Spatial Path', x: colX[1] },
        { title: 'JOINT KINEMATICS', sub: 'Per-Stroke Bio-Angles', x: colX[2] },
        { title: 'KINETIC CHAIN', sub: 'Torque & Gate Proof', x: colX[3] },
        { title: 'CAUSAL HYPOTHESES', sub: 'Bayesian Diagnoses', x: colX[4] },
        { title: 'RECOMMENDATIONS', sub: 'Coaching Interventions', x: colX[5] }
      ];

      // Calculate Per-Shot Vertical Corridors
      const SHOT_ROW_GAP = 145;
      const startShotY = 70;

      // Group kinematic and kinetic-chain nodes by their parent shot
      const shotKinematicsMap = new Map();
      const shotKineticChainMap = new Map();
      detectedShots.forEach((s) => {
        shotKinematicsMap.set(s.id, []);
        shotKineticChainMap.set(s.id, []);
      });

      // Also gather global items (non-shot-specific)
      const globalCol0 = [];
      const globalCol1 = [];
      const globalCol2 = [];
      const globalCol3 = [];
      const col4Hypotheses = [];
      const col5Recommendations = [];

      nodes.forEach((n) => {
        if (n.node_type === 'player' || n.node_type === 'court' || n.node_type === 'rag') {
          globalCol0.push(n);
        } else if (n.node_type === 'shot') {
          // Handled in shot list
        } else if (n.node_type === 'movement' || n.node_type === 'metric' && n.id.includes('distribution')) {
          globalCol1.push(n);
        } else if (n.node_type === 'hypothesis') {
          col4Hypotheses.push(n);
        } else if (n.node_type === 'recommendation') {
          col5Recommendations.push(n);
        } else if (n.node_type === 'speed_metric' || n.node_type === 'metric' && n.id.includes('energy')) {
          globalCol2.push(n);
        } else if (n.node_type === 'limitation') {
          globalCol3.push(n);
        } else if (n.node_type === 'stroke_class' || n.node_type === 'joint_kinematics') {
          // Find matching shot
          const sId = detectedShots.find((s) => n.id.includes(s.id.replace('shot_', '')) || (n.shotRefId && s.id.includes(n.shotRefId)))?.id;
          if (sId && shotKinematicsMap.has(sId)) {
            shotKinematicsMap.get(sId).push(n);
          } else {
            // Check edges to find parent shot
            const parentShotEdge = edges.find((e) => e.target === n.id && detectedShots.some((s) => s.id === e.source));
            if (parentShotEdge && shotKinematicsMap.has(parentShotEdge.source)) {
              shotKinematicsMap.get(parentShotEdge.source).push(n);
            } else {
              globalCol2.push(n);
            }
          }
        } else if (n.node_type === 'kinetic_chain') {
          const sId = detectedShots.find((s) => n.id.includes(s.id.replace('shot_', '')) || (n.shotRefId && s.id.includes(n.shotRefId)))?.id;
          if (sId && shotKineticChainMap.has(sId)) {
            shotKineticChainMap.get(sId).push(n);
          } else {
            const parentKinEdge = edges.find((e) => e.target === n.id);
            if (parentKinEdge) {
              const matchingShot = detectedShots.find((s) => parentKinEdge.source.includes(s.id.replace('shot_', '')));
              if (matchingShot && shotKineticChainMap.has(matchingShot.id)) {
                shotKineticChainMap.get(matchingShot.id).push(n);
              } else {
                globalCol3.push(n);
              }
            } else {
              globalCol3.push(n);
            }
          }
        } else {
          // Fallback based on in/out degree
          if (inDegreeMap[n.id] === 0) globalCol0.push(n);
          else if (outDegreeMap[n.id] === 0) col5Recommendations.push(n);
          else globalCol2.push(n);
        }
      });

      const totalShotsHeight = detectedShots.length * SHOT_ROW_GAP;
      const totalGlobalHeight = Math.max(globalCol0.length, globalCol1.length + 1) * 85;
      const canvasHeight = Math.max(680, Math.max(totalShotsHeight, totalGlobalHeight) + 120);

      // Place Column 0 (Global Entities: Player, Court, RAG)
      const col0StartY = 70;
      globalCol0.forEach((n, idx) => {
        positions[n.id] = {
          x: colX[0],
          y: col0StartY + idx * 85
        };
      });

      // Place Column 1 Global Items (Movement Dynamics, Rally Metrics)
      const col1GlobalStartY = Math.max(70, startShotY + detectedShots.length * SHOT_ROW_GAP + 10);
      globalCol1.forEach((n, idx) => {
        positions[n.id] = {
          x: colX[1],
          y: col1GlobalStartY + idx * 80
        };
      });

      // Place Each Shot & Its Parallel Horizontal Causal Corridor
      detectedShots.forEach((shotNode, sIdx) => {
        const shotCenterY = startShotY + sIdx * SHOT_ROW_GAP;

        // 1. Place Shot Node in Column 1
        positions[shotNode.id] = {
          x: colX[1],
          y: shotCenterY
        };

        // 2. Place Kinematic Joint Nodes in Column 2 (Structured 2-column mini-grid)
        const kinematicsList = shotKinematicsMap.get(shotNode.id) || [];
        kinematicsList.forEach((kinNode, kIdx) => {
          // Arrange in 2 sub-columns inside Column 2 (SubCol 0: x, SubCol 1: x + 160)
          const subCol = kIdx % 2;
          const subRow = Math.floor(kIdx / 2);
          const subOffsetY = (subRow - 0.5) * 62;

          positions[kinNode.id] = {
            x: colX[2] + subCol * 175,
            y: shotCenterY + subOffsetY
          };
        });

        // 3. Place Kinetic Chain Node in Column 3
        const chainList = shotKineticChainMap.get(shotNode.id) || [];
        chainList.forEach((chainNode, cIdx) => {
          positions[chainNode.id] = {
            x: colX[3],
            y: shotCenterY + (cIdx - (chainList.length - 1) / 2) * 65
          };
        });
      });

      // Place Global Ballistics & Energy in Column 2 Bottom
      globalCol2.forEach((n, idx) => {
        positions[n.id] = {
          x: colX[2],
          y: col1GlobalStartY + idx * 75
        };
      });

      // Place Global Limitations in Column 3 Bottom
      globalCol3.forEach((n, idx) => {
        positions[n.id] = {
          x: colX[3],
          y: col1GlobalStartY + idx * 75
        };
      });

      // Place Column 4: Hypotheses (Evenly distributed across canvas height)
      const hypoGap = 110;
      const hypoStartY = Math.max(60, (canvasHeight - col4Hypotheses.length * hypoGap) / 2);
      col4Hypotheses.forEach((n, idx) => {
        positions[n.id] = {
          x: colX[4],
          y: hypoStartY + idx * hypoGap
        };
      });

      // Place Column 5: Recommendations (Directly beside Hypotheses)
      const recGap = 110;
      const recStartY = Math.max(60, (canvasHeight - col5Recommendations.length * recGap) / 2);
      col5Recommendations.forEach((n, idx) => {
        positions[n.id] = {
          x: colX[5],
          y: recStartY + idx * recGap
        };
      });

      const totalWidth = colX[5] + CARD_W + 80;

      return {
        nodePositions: positions,
        canvasBounds: { width: Math.max(1600, totalWidth), height: canvasHeight },
        stageColumns: stageTitles
      };
    } else {
      // General Topological Longest-Path DAG Layout for Generic / Agriculture / Infrastructure graphs
      const depths = {};
      nodes.forEach((n) => (depths[n.id] = inDegreeMap[n.id] === 0 ? 0 : 1));

      // Iteratively compute longest path depth
      for (let iter = 0; iter < 6; iter++) {
        edges.forEach((e) => {
          const srcD = depths[e.source] || 0;
          const tgtD = depths[e.target] || 0;
          if (tgtD <= srcD) {
            depths[e.target] = srcD + 1;
          }
        });
      }

      // Pin hypotheses to second-to-last layer, and recommendations to last layer
      nodes.forEach((n) => {
        if (n.node_type === 'hypothesis') depths[n.id] = Math.max(depths[n.id], 3);
        if (n.node_type === 'recommendation' || n.node_type === 'posterior') depths[n.id] = Math.max(depths[n.id], 4);
      });

      const maxDepth = Math.min(5, Math.max(...Object.values(depths), 1));
      const cols = Array.from({ length: maxDepth + 1 }, () => []);

      nodes.forEach((node) => {
        const d = Math.min(maxDepth, depths[node.id] || 0);
        cols[d].push(node);
      });

      const startX = 40;
      const colGap = 260;
      const maxRows = Math.max(...cols.map((c) => c.length), 1);
      const rowGap = 88;
      const totalHeight = Math.max(540, maxRows * rowGap + 100);

      cols.forEach((col, colIdx) => {
        const x = startX + colIdx * colGap;
        const colHeight = col.length * rowGap;
        const topOffsetY = Math.max(60, (totalHeight - colHeight) / 2);

        col.forEach((node, rowIdx) => {
          positions[node.id] = {
            x,
            y: topOffsetY + rowIdx * rowGap
          };
        });
      });

      const stageTitles = cols.map((_, idx) => ({
        title: idx === 0 ? 'INPUTS' : idx === cols.length - 1 ? 'DIAGNOSIS' : `STAGE 0${idx}`,
        sub: idx === 0 ? 'Empirical Sensors' : idx === cols.length - 1 ? 'Grounded Proof' : 'Causal Pathways',
        x: startX + idx * colGap
      }));

      const totalWidth = startX + cols.length * colGap + CARD_W + 40;

      return {
        nodePositions: positions,
        canvasBounds: { width: Math.max(1200, totalWidth), height: totalHeight },
        stageColumns: stageTitles
      };
    }
  }, [nodes, edges, inDegreeMap, outDegreeMap, detectedShots]);

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

  // 5. Shot Filtering & Search Query Filtering
  const isNodeVisible = (node) => {
    // Search query filter
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const matchLabel = (node.label || '').toLowerCase().includes(q);
      const matchId = node.id.toLowerCase().includes(q);
      const matchType = (node.node_type || '').toLowerCase().includes(q);
      if (!matchLabel && !matchId && !matchType) return false;
    }

    // Shot filter
    if (activeShotFilter === 'ALL') return true;
    if (activeShotFilter === 'HYPO_ONLY') {
      return node.node_type === 'hypothesis' || node.node_type === 'recommendation';
    }

    // Isolate specific shot
    if (node.node_type === 'player' || node.node_type === 'court') return true;
    if (node.id === activeShotFilter || node.shotRefId === activeShotFilter) return true;
    if (node.node_type === 'hypothesis' || node.node_type === 'recommendation') {
      // Check if connected to active shot
      return true;
    }

    // Check if node is part of this shot's subgraph
    const shotNode = nodes.find((n) => n.id === activeShotFilter);
    if (!shotNode) return true;

    const isConnectedToShot = edges.some(
      (e) => (e.source === activeShotFilter && e.target === node.id) || (e.source === node.id && e.target === activeShotFilter)
    );

    return isConnectedToShot;
  };

  // 6. Selected Node Details for Docked Bottom Inspector
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
    setZoomLevel((prev) => Math.max(0.35, Math.min(2.5, prev * zoomFactor)));
  };

  const handleFitToScreen = () => {
    if (containerRef.current) {
      const containerW = containerRef.current.clientWidth || 800;
      const containerH = containerRef.current.clientHeight || 500;
      const targetW = canvasBounds.width || 1200;
      const targetH = canvasBounds.height || 600;

      const scaleX = (containerW - 60) / targetW;
      const scaleY = (containerH - 60) / targetH;
      const optimalZoom = Math.min(1.0, Math.max(0.45, Math.min(scaleX, scaleY)));

      setZoomLevel(optimalZoom);
      setPan({
        x: Math.max(20, (containerW - targetW * optimalZoom) / 2),
        y: 20
      });
    } else {
      setZoomLevel(0.85);
      setPan({ x: 20, y: 20 });
    }
  };

  // Auto-fit on initial mount or container resize
  useEffect(() => {
    handleFitToScreen();
  }, [isExpanded, detectedShots.length]);

  // Helper for Node Theme
  const getNodeTheme = (type) => {
    switch (type) {
      case 'player':
      case 'object':
        return {
          headerBg: isDark ? 'rgba(22, 101, 52, 0.35)' : '#f0fdf4',
          headerText: isDark ? '#4ade80' : '#166534',
          border: isDark ? '#22c55e' : '#86efac',
          chipBg: isDark ? 'rgba(34, 197, 94, 0.2)' : '#dcfce7',
          tag: 'ATHLETE ENTITY',
          badgeColor: isDark ? '#86efac' : '#16a34a'
        };
      case 'court':
        return {
          headerBg: isDark ? 'rgba(2, 132, 199, 0.25)' : '#f0f9ff',
          headerText: isDark ? '#38bdf8' : '#0369a1',
          border: isDark ? '#0284c7' : '#7dd3fc',
          chipBg: isDark ? 'rgba(2, 132, 199, 0.2)' : '#e0f2fe',
          tag: 'COURT GEOMETRY',
          badgeColor: isDark ? '#7dd3fc' : '#0284c7'
        };
      case 'shot':
        return {
          headerBg: isDark ? 'rgba(126, 34, 206, 0.28)' : '#faf5ff',
          headerText: isDark ? '#c084fc' : '#6b21a8',
          border: isDark ? '#a855f7' : '#d8b4fe',
          chipBg: isDark ? 'rgba(147, 51, 234, 0.2)' : '#f3e8ff',
          tag: 'RALLY STROKE',
          badgeColor: isDark ? '#e9d5ff' : '#7e22ce'
        };
      case 'joint_kinematics':
      case 'stroke_class':
        return {
          headerBg: isDark ? 'rgba(14, 116, 144, 0.25)' : '#ecfeff',
          headerText: isDark ? '#22d3ee' : '#0e7490',
          border: isDark ? '#06b6d4' : '#a5f3fc',
          chipBg: isDark ? 'rgba(6, 182, 212, 0.18)' : '#cffafe',
          tag: 'JOINT KINEMATICS',
          badgeColor: isDark ? '#67e8f9' : '#0891b2'
        };
      case 'kinetic_chain':
        return {
          headerBg: isDark ? 'rgba(22, 163, 74, 0.25)' : '#f0fdf4',
          headerText: isDark ? '#4ade80' : '#15803d',
          border: isDark ? '#16a34a' : '#86efac',
          chipBg: isDark ? 'rgba(22, 163, 74, 0.2)' : '#dcfce7',
          tag: 'KINETIC CHAIN',
          badgeColor: isDark ? '#86efac' : '#16a34a'
        };
      case 'speed_metric':
      case 'movement':
        return {
          headerBg: isDark ? 'rgba(3, 105, 161, 0.25)' : '#f0f9ff',
          headerText: isDark ? '#38bdf8' : '#0284c7',
          border: isDark ? '#0284c7' : '#93c5fd',
          chipBg: isDark ? 'rgba(2, 132, 199, 0.2)' : '#dbeafe',
          tag: 'SPATIAL TELEMETRY',
          badgeColor: isDark ? '#93c5fd' : '#1d4ed8'
        };
      case 'hypothesis':
        return {
          headerBg: isDark ? 'rgba(217, 119, 6, 0.25)' : '#fffbeb',
          headerText: isDark ? '#fbbf24' : '#92400e',
          border: isDark ? '#f59e0b' : '#fde047',
          chipBg: isDark ? 'rgba(245, 158, 11, 0.2)' : '#fef3c7',
          tag: 'CAUSAL HYPOTHESIS',
          badgeColor: isDark ? '#fde68a' : '#d97706'
        };
      case 'recommendation':
      case 'posterior':
        return {
          headerBg: isDark ? 'rgba(190, 24, 93, 0.25)' : '#fdf2f8',
          headerText: isDark ? '#f472b6' : '#9d174d',
          border: isDark ? '#db2777' : '#fbcfe8',
          chipBg: isDark ? 'rgba(219, 39, 119, 0.18)' : '#fce7f3',
          tag: 'COACHING INTERVENTION',
          badgeColor: isDark ? '#fbcfe8' : '#be185d'
        };
      default:
        return {
          headerBg: isDark ? 'rgba(51, 65, 85, 0.5)' : '#f8fafc',
          headerText: isDark ? '#cbd5e1' : '#475569',
          border: isDark ? '#64748b' : '#cbd5e1',
          chipBg: isDark ? 'rgba(100, 116, 139, 0.2)' : '#f1f5f9',
          tag: 'EMPIRICAL FEATURE',
          badgeColor: isDark ? '#e2e8f0' : '#64748b'
        };
    }
  };

  const getRelationColor = (relation) => {
    const rel = (relation || '').toLowerCase();
    if (rel.includes('obstruct') || rel.includes('inhibit') || rel.includes('contradict') || rel.includes('refute')) return '#dc2626';
    if (rel.includes('cause') || rel.includes('trigger')) return '#d97706';
    if (rel.includes('support') || rel.includes('confirm') || rel.includes('executes')) return '#16a34a';
    if (rel.includes('measure') || rel.includes('indicate')) return '#0284c7';
    return '#818cf8';
  };

  return (
    <div className="causal-graph-container" style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      background: isDark ? '#090d16' : '#faf9ff',
      position: 'relative',
      borderRadius: '12px',
      overflow: 'hidden',
      userSelect: 'none'
    }}>
      {/* 1. Top Header Toolbar - Structured Scientific Navigation */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.5rem 0.9rem',
        borderBottom: isDark ? '1px solid #1e293b' : '1px solid #e2e8f0',
        background: isDark ? '#0f172a' : '#ffffff',
        zIndex: 5,
        gap: '0.8rem',
        flexWrap: 'wrap'
      }}>
        {/* Title and Node Count Stats */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <div style={{
            width: '28px',
            height: '28px',
            borderRadius: '8px',
            background: isDark ? 'rgba(126, 34, 206, 0.25)' : 'rgba(126, 34, 206, 0.1)',
            color: '#7e22ce',
            display: 'grid',
            placeItems: 'center'
          }}>
            <GitFork size={15} />
          </div>
          <div>
            <div style={{ fontSize: '0.84rem', fontWeight: '700', color: isDark ? '#f8fafc' : '#0f172a', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>Causal Reasoning Pipeline</span>
              <span style={{
                fontSize: '0.68rem',
                fontWeight: '600',
                padding: '0.1rem 0.5rem',
                borderRadius: '9999px',
                background: isDark ? 'rgba(126, 34, 206, 0.25)' : '#f3e8ff',
                color: isDark ? '#d8b4fe' : '#7e22ce'
              }}>
                {nodes.length} nodes · {edges.length} edges
              </span>
            </div>
            <div style={{ fontSize: '0.66rem', color: isDark ? '#94a3b8' : '#64748b' }}>
              Horizontal Causal Flow: Inputs ➔ Strokes ➔ Kinematics ➔ Kinetic Chain ➔ Hypotheses ➔ Recommendations
            </div>
          </div>
        </div>

        {/* Search Box & Stroke Filter Pills */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
          {/* Quick Search */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '5px',
            background: isDark ? '#1e293b' : '#f8fafc',
            border: `1px solid ${isDark ? '#334155' : '#cbd5e1'}`,
            borderRadius: '6px',
            padding: '2px 8px'
          }}>
            <Search size={12} color={isDark ? '#94a3b8' : '#64748b'} />
            <input
              type="text"
              placeholder="Search nodes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                background: 'transparent',
                border: 'none',
                outline: 'none',
                fontSize: '0.7rem',
                color: isDark ? '#f8fafc' : '#0f172a',
                width: '100px'
              }}
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
              >
                <X size={10} color="#94a3b8" />
              </button>
            )}
          </div>

          {/* Stroke Selector Filter (for Badminton analysis) */}
          {detectedShots.length > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
              <button
                type="button"
                style={{
                  padding: '3px 8px',
                  borderRadius: '6px',
                  fontSize: '0.68rem',
                  fontWeight: '600',
                  border: `1px solid ${activeShotFilter === 'ALL' ? '#7e22ce' : (isDark ? '#334155' : '#cbd5e1')}`,
                  background: activeShotFilter === 'ALL' ? (isDark ? 'rgba(126, 34, 206, 0.3)' : '#f3e8ff') : (isDark ? '#1e293b' : '#ffffff'),
                  color: activeShotFilter === 'ALL' ? '#7e22ce' : (isDark ? '#cbd5e1' : '#475569'),
                  cursor: 'pointer'
                }}
                onClick={() => setActiveShotFilter('ALL')}
              >
                All Strokes ({detectedShots.length})
              </button>

              {detectedShots.slice(0, 4).map((shot, sIdx) => {
                const isShotActive = activeShotFilter === shot.id;
                return (
                  <button
                    key={shot.id}
                    type="button"
                    style={{
                      padding: '3px 8px',
                      borderRadius: '6px',
                      fontSize: '0.68rem',
                      fontWeight: '600',
                      border: `1px solid ${isShotActive ? '#7e22ce' : (isDark ? '#334155' : '#cbd5e1')}`,
                      background: isShotActive ? (isDark ? 'rgba(126, 34, 206, 0.3)' : '#f3e8ff') : (isDark ? '#1e293b' : '#ffffff'),
                      color: isShotActive ? '#7e22ce' : (isDark ? '#cbd5e1' : '#475569'),
                      cursor: 'pointer'
                    }}
                    onClick={() => setActiveShotFilter(isShotActive ? 'ALL' : shot.id)}
                    title={`Focus on ${shot.label}`}
                  >
                    Shot #{sIdx + 1}
                  </button>
                );
              })}
            </div>
          )}

          {/* Zoom & View Actions */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
            <button
              style={{
                width: '26px',
                height: '26px',
                border: `1px solid ${isDark ? '#334155' : '#cbd5e1'}`,
                background: isDark ? '#1e293b' : '#ffffff',
                borderRadius: '6px',
                display: 'grid',
                placeItems: 'center',
                cursor: 'pointer'
              }}
              onClick={() => setZoomLevel((z) => Math.max(0.35, z - 0.15))}
              title="Zoom Out"
            >
              <ZoomOut size={12} color={isDark ? '#cbd5e1' : '#475569'} />
            </button>
            <span style={{ fontSize: '0.68rem', color: isDark ? '#94a3b8' : '#64748b', minWidth: '32px', textAlign: 'center', fontWeight: '700' }}>
              {Math.round(zoomLevel * 100)}%
            </span>
            <button
              style={{
                width: '26px',
                height: '26px',
                border: `1px solid ${isDark ? '#334155' : '#cbd5e1'}`,
                background: isDark ? '#1e293b' : '#ffffff',
                borderRadius: '6px',
                display: 'grid',
                placeItems: 'center',
                cursor: 'pointer'
              }}
              onClick={() => setZoomLevel((z) => Math.min(2.5, z + 0.15))}
              title="Zoom In"
            >
              <ZoomIn size={12} color={isDark ? '#cbd5e1' : '#475569'} />
            </button>
            <button
              style={{
                padding: '0 0.5rem',
                height: '26px',
                border: `1px solid ${isDark ? '#334155' : '#cbd5e1'}`,
                background: isDark ? '#1e293b' : '#ffffff',
                borderRadius: '6px',
                display: 'flex',
                alignItems: 'center',
                gap: '3px',
                fontSize: '0.68rem',
                color: isDark ? '#cbd5e1' : '#475569',
                cursor: 'pointer',
                fontWeight: '600'
              }}
              onClick={handleFitToScreen}
              title="Fit to Screen"
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
                border: '1px solid #7e22ce',
                background: isExpanded ? '#7e22ce' : (isDark ? 'rgba(126, 34, 206, 0.25)' : 'rgba(126, 34, 206, 0.08)'),
                color: isExpanded ? '#ffffff' : '#7e22ce',
                borderRadius: '6px',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '0.7rem',
                fontWeight: '600',
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
          background: isDark ? '#090d16' : '#f8fafc',
          backgroundImage: isDark
            ? 'radial-gradient(#1e293b 1.5px, transparent 1.5px)'
            : 'radial-gradient(#e2e8f0 1.2px, transparent 1.2px)',
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
            <marker id="arrow-causes" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
              <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#d97706" />
            </marker>
            <marker id="arrow-supports" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
              <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#16a34a" />
            </marker>
            <marker id="arrow-obstructs" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
              <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#dc2626" />
            </marker>
            <marker id="arrow-default" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
              <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#7e22ce" />
            </marker>

            {/* Soft Scientific Elevation Filters */}
            <filter id="active-card-shadow" x="-10%" y="-10%" width="120%" height="120%">
              <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="rgba(126, 34, 206, 0.25)" />
            </filter>
            <filter id="cause-card-shadow" x="-10%" y="-10%" width="120%" height="120%">
              <feDropShadow dx="0" dy="2" stdDeviation="2.5" floodColor="rgba(217, 119, 6, 0.2)" />
            </filter>
            <filter id="effect-card-shadow" x="-10%" y="-10%" width="120%" height="120%">
              <feDropShadow dx="0" dy="2" stdDeviation="2.5" floodColor="rgba(22, 163, 74, 0.2)" />
            </filter>
            <filter id="standard-card-shadow" x="-10%" y="-10%" width="120%" height="120%">
              <feDropShadow dx="0" dy="1.5" stdDeviation="2" floodColor="rgba(15, 23, 42, 0.08)" />
            </filter>
          </defs>

          {/* Scaled & Panned Group */}
          <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoomLevel})`}>
            {/* Stage Swimlane Column Backdrops & Headers */}
            {stageColumns.map((col, idx) => (
              <g key={idx} className="stage-column-group">
                <rect
                  x={col.x - 12}
                  y={15}
                  width={idx === 2 ? 370 : 208}
                  height={canvasBounds.height - 30}
                  rx="10"
                  fill={isDark ? 'rgba(30, 41, 59, 0.3)' : 'rgba(241, 245, 249, 0.65)'}
                  stroke={isDark ? 'rgba(51, 65, 85, 0.5)' : '#e2e8f0'}
                  strokeDasharray="4 4"
                />
                <rect
                  x={col.x - 4}
                  y={22}
                  width={idx === 2 ? 354 : 192}
                  height={24}
                  rx="5"
                  fill={isDark ? '#0f172a' : '#ffffff'}
                  stroke={isDark ? '#334155' : '#cbd5e1'}
                />
                <text
                  x={col.x + 8}
                  y={38}
                  fill={isDark ? '#cbd5e1' : '#1e293b'}
                  fontSize="9px"
                  fontFamily="Inter, sans-serif"
                  fontWeight="800"
                  letterSpacing="0.4px"
                >
                  {col.title}
                </text>
                <text
                  x={col.x + (idx === 2 ? 340 : 180)}
                  y={38}
                  textAnchor="end"
                  fill={isDark ? '#64748b' : '#94a3b8'}
                  fontSize="7.5px"
                  fontFamily="Inter, sans-serif"
                  fontWeight="500"
                >
                  {col.sub}
                </text>
              </g>
            ))}

            {/* Causal Edges Layer */}
            <g className="edges-layer">
              {edges.map((edge) => {
                const srcNode = nodeMap.get(edge.source);
                const tgtNode = nodeMap.get(edge.target);
                const srcPos = nodePositions[edge.source];
                const tgtPos = nodePositions[edge.target];
                if (!srcPos || !tgtPos) return null;

                const srcVisible = srcNode ? isNodeVisible(srcNode) : true;
                const tgtVisible = tgtNode ? isNodeVisible(tgtNode) : true;
                if (!srcVisible || !tgtVisible) return null;

                const isDirectlyActive = activeEdgeSet.has(edge.id);
                const isDimmed = activeFocusId && !isDirectlyActive;
                const isHoveredEdge = hoveredEdgeId === edge.id;

                // Connect right-center of source to left-center of target
                const startX = srcPos.x + CARD_W;
                const startY = srcPos.y + CARD_H / 2;
                const endX = tgtPos.x;
                const endY = tgtPos.y + CARD_H / 2;

                // Smooth horizontal cubic bezier curve
                const dx = Math.max(40, (endX - startX) * 0.5);
                const cp1X = startX + dx;
                const cp1Y = startY;
                const cp2X = endX - dx;
                const cp2Y = endY;

                let pathD = '';
                if (endX > startX + 15) {
                  pathD = `M ${startX} ${startY} C ${cp1X} ${cp1Y}, ${cp2X} ${cp2Y}, ${endX} ${endY}`;
                } else {
                  // Loop curve if target is to the left
                  const midX = (startX + endX) / 2;
                  const midY = Math.min(startY, endY) - 30;
                  pathD = `M ${startX} ${startY} Q ${midX} ${midY}, ${endX} ${endY}`;
                }

                const relationColor = getRelationColor(edge.relation_type);
                const strokeColor = isDirectlyActive
                  ? (edge.relation_type?.includes('cause') ? '#d97706' : edge.relation_type?.includes('support') ? '#16a34a' : '#7e22ce')
                  : isHoveredEdge
                  ? relationColor
                  : (isDark ? 'rgba(148, 163, 184, 0.25)' : 'rgba(100, 80, 180, 0.25)');

                let marker = 'url(#arrow-default)';
                if (edge.relation_type?.includes('cause') || edge.relation_type?.includes('trigger')) marker = 'url(#arrow-causes)';
                if (edge.relation_type?.includes('support') || edge.relation_type?.includes('confirm') || edge.relation_type?.includes('executes')) marker = 'url(#arrow-supports)';
                if (edge.relation_type?.includes('obstruct') || edge.relation_type?.includes('inhibit')) marker = 'url(#arrow-obstructs)';

                const chipX = (startX + endX) / 2;
                const chipY = (startY + endY) / 2;

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
                    {/* Hitbox */}
                    <path
                      d={pathD}
                      fill="none"
                      stroke="transparent"
                      strokeWidth="14"
                      style={{ cursor: 'pointer' }}
                    />

                    {/* Visual Causal Line */}
                    <path
                      d={pathD}
                      fill="none"
                      stroke={strokeColor}
                      strokeWidth={isDirectlyActive ? 2.5 : isHoveredEdge ? 2 : 1.2}
                      strokeDasharray={edge.relation_type?.includes('obstruct') ? '4,3' : 'none'}
                      markerEnd={marker}
                      style={{ transition: 'stroke-width 0.2s ease, stroke 0.2s ease' }}
                    />

                    {/* Edge Label Badge */}
                    {(isDirectlyActive || isHoveredEdge) && (
                      <g transform={`translate(${chipX}, ${chipY})`} style={{ cursor: 'pointer' }}>
                        <rect
                          x="-28"
                          y="-8"
                          width="56"
                          height="16"
                          rx="4"
                          fill={isDark ? '#0f172a' : '#ffffff'}
                          stroke={strokeColor}
                          strokeWidth="1.2"
                          filter="url(#standard-card-shadow)"
                        />
                        <text
                          x="0"
                          y="3.5"
                          textAnchor="middle"
                          fill={strokeColor}
                          fontSize="7px"
                          fontFamily="JetBrains Mono, monospace"
                          fontWeight="700"
                        >
                          {edge.relation_type.toUpperCase()}
                        </text>
                      </g>
                    )}
                  </g>
                );
              })}
            </g>

            {/* Causal Nodes Layer */}
            <g className="nodes-layer">
              {nodes.map((node) => {
                const pos = nodePositions[node.id];
                if (!pos) return null;

                const isVisible = isNodeVisible(node);
                if (!isVisible) return null;

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
                let strokeWidth = 1.2;

                if (isFocused) {
                  cardShadow = 'url(#active-card-shadow)';
                  strokeColor = '#7e22ce';
                  strokeWidth = 2;
                } else if (isAncestor) {
                  cardShadow = 'url(#cause-card-shadow)';
                  strokeColor = '#d97706';
                  strokeWidth = 1.6;
                } else if (isDescendant) {
                  cardShadow = 'url(#effect-card-shadow)';
                  strokeColor = '#16a34a';
                  strokeWidth = 1.6;
                }

                // Format node label for clean multi-line display
                const labelWords = (node.label || node.id).split(' ');
                let line1 = labelWords.slice(0, 3).join(' ');
                let line2 = labelWords.slice(3, 7).join(' ');
                if (labelWords.length > 7) line2 += '...';

                return (
                  <g
                    key={node.id}
                    transform={`translate(${pos.x}, ${pos.y})`}
                    style={{
                      cursor: 'pointer',
                      opacity: isDimmed ? 0.2 : 1,
                      transition: 'transform 0.18s ease, opacity 0.18s ease'
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
                    {/* Causal Pathway Status Indicator Tag */}
                    {isAncestor && (
                      <text
                        x="0"
                        y="-5"
                        fill="#d97706"
                        fontSize="8px"
                        fontFamily="Inter, sans-serif"
                        fontWeight="700"
                      >
                        ▲ CAUSE
                      </text>
                    )}
                    {isDescendant && (
                      <text
                        x="0"
                        y="-5"
                        fill="#16a34a"
                        fontSize="8px"
                        fontFamily="Inter, sans-serif"
                        fontWeight="700"
                      >
                        ▼ IMPACT
                      </text>
                    )}

                    {/* Main Node Card Body */}
                    <rect
                      width={CARD_W}
                      height={CARD_H}
                      rx="8"
                      ry="8"
                      fill={isDark ? '#1e293b' : '#ffffff'}
                      stroke={strokeColor}
                      strokeWidth={strokeWidth}
                      filter={cardShadow}
                    />

                    {/* Card Header Strip with Tinted Category Accent */}
                    <rect
                      x="0"
                      y="0"
                      width={CARD_W}
                      height="16"
                      rx="8"
                      ry="8"
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
                      letterSpacing="0.2px"
                    >
                      {themeStyle.tag}
                    </text>

                    {/* Confidence Tag in Header */}
                    <rect
                      x={CARD_W - 32}
                      y="2.5"
                      width="26"
                      height="11"
                      rx="3"
                      fill={themeStyle.chipBg}
                    />
                    <text
                      x={CARD_W - 19}
                      y="10.5"
                      textAnchor="middle"
                      fill={themeStyle.badgeColor}
                      fontSize="7px"
                      fontFamily="JetBrains Mono, monospace"
                      fontWeight="700"
                    >
                      {Math.round(node.confidence * 100)}%
                    </text>

                    {/* Node Title (Line 1 & 2) */}
                    <text
                      x="7"
                      y="31"
                      fill={isDark ? '#f8fafc' : '#0f172a'}
                      fontSize="10px"
                      fontFamily="Inter, sans-serif"
                      fontWeight="700"
                    >
                      {line1}
                    </text>
                    {line2 && (
                      <text
                        x="7"
                        y="44"
                        fill={isDark ? '#94a3b8' : '#475569'}
                        fontSize="8.5px"
                        fontFamily="Inter, sans-serif"
                        fontWeight="500"
                      >
                        {line2}
                      </text>
                    )}

                    {/* Visual Grounding Reticle Badge */}
                    {node.visual_anchor && (
                      <g transform={`translate(7, ${CARD_H - 6})`}>
                        <circle cx="2.5" cy="-1.5" r="2" fill="#7e22ce" />
                        <text x="6" y="0.5" fill="#7e22ce" fontSize="6px" fontFamily="Inter, sans-serif" fontWeight="700">
                          GROUNDED
                        </text>
                      </g>
                    )}

                    {/* Connection Ports */}
                    <circle cx="0" cy={CARD_H / 2} r="3" fill="#ffffff" stroke={themeStyle.border} strokeWidth="1.2" />
                    <circle cx={CARD_W} cy={CARD_H / 2} r="3" fill="#ffffff" stroke={themeStyle.border} strokeWidth="1.2" />
                  </g>
                );
              })}
            </g>
          </g>
        </svg>
      </div>

      {/* 3. Dedicated Docked Bottom Evidence Inspector Panel */}
      {activeInspectedNode ? (
        <div style={{
          minHeight: '85px',
          maxHeight: '125px',
          borderTop: isDark ? '1px solid #1e293b' : '1px solid #e2e8f0',
          background: isDark ? '#0f172a' : '#ffffff',
          display: 'grid',
          gridTemplateColumns: 'minmax(180px, 1.3fr) minmax(150px, 1fr) minmax(150px, 1fr) auto',
          gap: '0.75rem',
          padding: '0.5rem 0.85rem',
          boxShadow: '0 -2px 10px rgba(15, 23, 42, 0.05)',
          zIndex: 10,
          alignItems: 'center',
          boxSizing: 'border-box',
          width: '100%',
          overflowX: 'auto',
          overflowY: 'hidden'
        }}>
          {/* Column 1: Node Title, Type & Confidence Bar */}
          <div style={{ minWidth: 0, borderRight: isDark ? '1px solid #1e293b' : '1px solid #f1f5f9', paddingRight: '0.6rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '2px' }}>
              <span style={{
                fontSize: '0.62rem',
                fontWeight: '700',
                padding: '0.1rem 0.4rem',
                borderRadius: '4px',
                background: getNodeTheme(activeInspectedNode.node_type).chipBg,
                color: getNodeTheme(activeInspectedNode.node_type).headerText,
                whiteSpace: 'nowrap'
              }}>
                {getNodeTheme(activeInspectedNode.node_type).tag}
              </span>
              {activeInspectedNode.visual_anchor && (
                <span style={{ fontSize: '0.62rem', fontWeight: '700', color: '#7e22ce', whiteSpace: 'nowrap' }}>
                  ● GROUNDED
                </span>
              )}
            </div>
            <h4 style={{
              margin: '0.15rem 0',
              fontSize: '0.84rem',
              fontWeight: '700',
              color: isDark ? '#f8fafc' : '#0f172a',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis'
            }} title={activeInspectedNode.label}>
              {activeInspectedNode.label}
            </h4>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '3px' }}>
              <span style={{ fontSize: '0.66rem', color: '#64748b', whiteSpace: 'nowrap' }}>Confidence:</span>
              <div style={{ height: '4px', width: '65px', background: isDark ? '#334155' : '#e2e8f0', borderRadius: '2px', overflow: 'hidden' }}>
                <div style={{
                  height: '100%',
                  width: `${Math.round(activeInspectedNode.confidence * 100)}%`,
                  background: '#7e22ce',
                  borderRadius: '2px'
                }} />
              </div>
              <strong style={{ fontSize: '0.7rem', color: isDark ? '#f8fafc' : '#0f172a', fontFamily: 'JetBrains Mono, monospace' }}>
                {Math.round(activeInspectedNode.confidence * 100)}%
              </strong>
            </div>
          </div>

          {/* Column 2: Direct Causes (Inflow) */}
          <div style={{ minWidth: 0, borderRight: isDark ? '1px solid #1e293b' : '1px solid #f1f5f9', paddingRight: '0.6rem', overflowY: 'auto', maxHeight: '80px' }}>
            <div style={{ fontSize: '0.66rem', fontWeight: '700', color: '#d97706', marginBottom: '3px', display: 'flex', alignItems: 'center', gap: '4px', whiteSpace: 'nowrap' }}>
              <ArrowLeft size={10} />
              <span>Direct Causes ({directInflowNodes.length}):</span>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '3px' }}>
              {directInflowNodes.length > 0 ? (
                directInflowNodes.map(({ node, edge }) => (
                  <span
                    key={node.id}
                    onClick={() => onSelectNode(node.id)}
                    style={{
                      background: isDark ? 'rgba(217, 119, 6, 0.15)' : '#fffbeb',
                      color: isDark ? '#fbbf24' : '#92400e',
                      padding: '0.1rem 0.35rem',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '0.66rem',
                      fontWeight: '600',
                      border: `1px solid ${isDark ? 'rgba(217, 119, 6, 0.3)' : '#fef08a'}`,
                      maxWidth: '100%',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis'
                    }}
                    title={`Click to trace cause: ${node.label}`}
                  >
                    ← {node.label}
                  </span>
                ))
              ) : (
                <span style={{ color: '#94a3b8', fontSize: '0.66rem', fontStyle: 'italic' }}>Baseline Entity</span>
              )}
            </div>
          </div>

          {/* Column 3: Direct Impacts (Outflow) */}
          <div style={{ minWidth: 0, paddingRight: '0.4rem', overflowY: 'auto', maxHeight: '80px' }}>
            <div style={{ fontSize: '0.66rem', fontWeight: '700', color: '#16a34a', marginBottom: '3px', display: 'flex', alignItems: 'center', gap: '4px', whiteSpace: 'nowrap' }}>
              <span>Direct Impacts ({directOutflowNodes.length}):</span>
              <ArrowRight size={10} />
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '3px' }}>
              {directOutflowNodes.length > 0 ? (
                directOutflowNodes.map(({ node, edge }) => (
                  <span
                    key={node.id}
                    onClick={() => onSelectNode(node.id)}
                    style={{
                      background: isDark ? 'rgba(22, 163, 74, 0.15)' : '#f0fdf4',
                      color: isDark ? '#4ade80' : '#166534',
                      padding: '0.1rem 0.35rem',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '0.66rem',
                      fontWeight: '600',
                      border: `1px solid ${isDark ? 'rgba(22, 163, 74, 0.3)' : '#bbf7d0'}`,
                      maxWidth: '100%',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis'
                    }}
                    title={`Click to trace impact: ${node.label}`}
                  >
                    {node.label} →
                  </span>
                ))
              ) : (
                <span style={{ color: '#94a3b8', fontSize: '0.66rem', fontStyle: 'italic' }}>Terminal Hypothesis / Rec</span>
              )}
            </div>
          </div>

          {/* Column 4: Actions & Close */}
          <div style={{
            minWidth: 'fit-content',
            flexShrink: 0,
            display: 'flex',
            flexDirection: 'column',
            gap: '4px',
            alignItems: 'flex-end',
            justifyContent: 'center',
            paddingLeft: '0.2rem'
          }}>
            <button
              style={{
                border: 'none',
                background: isDark ? '#1e293b' : '#f1f5f9',
                borderRadius: '6px',
                width: '22px',
                height: '22px',
                cursor: 'pointer',
                display: 'grid',
                placeItems: 'center',
                color: isDark ? '#cbd5e1' : '#64748b'
              }}
              onClick={() => onSelectNode(null)}
              title="Close Docked Inspector"
            >
              <X size={12} />
            </button>
            {onSendToChat && (
              <button
                style={{
                  padding: '0.28rem 0.55rem',
                  background: '#7e22ce',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '6px',
                  fontSize: '0.68rem',
                  fontWeight: '600',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  whiteSpace: 'nowrap'
                }}
                onClick={() => {
                  onSendToChat(`Can you explain the causal mechanism and empirical evidence for "${activeInspectedNode.label}"?`);
                }}
                title="Inquire in Chat"
              >
                <MessageSquare size={11} />
                <span>Ask SAAR</span>
              </button>
            )}
          </div>
        </div>
      ) : (
        /* 4. Bottom Legend & Navigation Guide */
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '0.4rem 0.8rem',
          padding: '0.35rem 0.85rem',
          borderTop: isDark ? '1px solid #1e293b' : '1px solid #e2e8f0',
          background: isDark ? '#0f172a' : '#ffffff',
          fontSize: '0.68rem',
          color: isDark ? '#94a3b8' : '#475569',
          boxSizing: 'border-box',
          width: '100%',
          overflow: 'hidden'
        }}>
          {/* Left: Node Type Legend */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
            <span style={{ fontWeight: '700', color: isDark ? '#f8fafc' : '#0f172a', whiteSpace: 'nowrap' }}>Legend:</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '3px', whiteSpace: 'nowrap' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#22c55e' }} />
              <span>Entity</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '3px', whiteSpace: 'nowrap' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#7e22ce' }} />
              <span>Stroke</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '3px', whiteSpace: 'nowrap' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#06b6d4' }} />
              <span>Joint Kinematics</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '3px', whiteSpace: 'nowrap' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#16a34a' }} />
              <span>Kinetic Chain</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '3px', whiteSpace: 'nowrap' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#f59e0b' }} />
              <span>Hypothesis</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '3px', whiteSpace: 'nowrap' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#db2777' }} />
              <span>Recommendation</span>
            </div>
          </div>

          {/* Right: Quick Interaction Guide & Causal Direction Markers */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap', fontSize: '0.66rem' }}>
            <span style={{ whiteSpace: 'nowrap', color: isDark ? '#64748b' : '#94a3b8' }}>
              Drag to pan · Scroll to zoom
            </span>
            <span style={{ whiteSpace: 'nowrap', color: '#92400e', fontWeight: '600', background: '#fffbeb', padding: '0.08rem 0.35rem', borderRadius: '4px', border: '1px solid #fef08a' }}>
              ▲ Cause
            </span>
            <span style={{ whiteSpace: 'nowrap', color: '#166534', fontWeight: '600', background: '#f0fdf4', padding: '0.08rem 0.35rem', borderRadius: '4px', border: '1px solid #bbf7d0' }}>
              ▼ Impact
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
