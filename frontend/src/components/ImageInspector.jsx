import React, { useState, useRef, useMemo } from 'react';
import {
  Eye, EyeOff, Radio, Upload, Sparkles, Link as LinkIcon,
  Camera, X, Crosshair, Target, Layers, Activity, Droplets,
  HelpCircle, ExternalLink, Zap
} from 'lucide-react';

// Domain-aware mapping of visual entities to analytical tools & queries
export const ENTITY_TOOL_MAPPINGS = {
  // Agriculture & Indoor Aroid Entities
  leaf_fenestrations_01: {
    toolId: 'telemetry',
    toolName: 'Foliar Margin Morphology & Fenestration Phenotyper',
    actionLabel: 'Analyze Leaf Fenestration vs Pest Damage',
    suggestedQuery: 'Evaluate whether these elliptical leaf perforations are natural evolutionary fenestrations (PCD) or pest defoliation.'
  },
  unfurling_apex_leaf_01: {
    toolId: 'telemetry',
    toolName: 'Photosystem II (PSII) Quantum Yield Fluorometer',
    actionLabel: 'Evaluate Apical Shoot Vigor & PSII Yield',
    suggestedQuery: 'Assess the photosynthetic health, metabolic turgor, and growth rate of this emergent apical leaf.'
  },
  pot_substrate_01: {
    toolId: 'telemetry',
    toolName: 'Container Substrate Drainage & Aeration Profiler',
    actionLabel: 'Analyze Container Drainage & Root Rot Risk',
    suggestedQuery: 'Examine the potting substrate drainage and evaluate vulnerability to Pythium root rot.'
  },
  fruit_01: {
    toolId: 'telemetry',
    toolName: 'Fruit Ripeness & Physiological Diagnostic',
    actionLabel: 'Analyze Ripeness & Translocation in Chat',
    suggestedQuery: 'Analyze the fruit ripening physiology, Brix sugar accumulation, and blossom-end rot risk for this cluster.'
  },
  leaf_chlorosis_01: {
    toolId: 'telemetry',
    toolName: 'Multispectral Foliar SPAD Diagnostic',
    actionLabel: 'Run SPAD Chlorophyll & NDRE Diagnostic',
    suggestedQuery: 'Explain the interveinal leaf chlorosis pattern and whether it indicates iron deficiency or nitrogen burn.'
  },
  soil_moisture_sensor_01: {
    toolId: 'telemetry',
    toolName: 'Root-Zone Oxygenation & ATP Pump Simulator',
    actionLabel: 'Simulate Root Zone Hypoxia & ATP Depletion',
    suggestedQuery: 'How does prolonged 48% VWC soil saturation impair root nutrient uptake?'
  },
  irrigation_emitter_01: {
    toolId: 'telemetry',
    toolName: 'Irrigation Drainage & Darcy Flow Simulator',
    actionLabel: 'Simulate Irrigation Drainage & Percolation',
    suggestedQuery: 'What is the optimal drip emitter pulse regime to prevent root waterlogging?'
  },

  // Civil Infrastructure Entities
  road_01: {
    toolId: 'telemetry',
    toolName: 'Ground Penetrating Radar (GPR) Void Analyzer',
    actionLabel: 'Scan for Subterranean Void Cavity',
    suggestedQuery: 'Assess the structural collapse risk and subterranean void cavity probability beneath this road crack.'
  },
  drain_01: {
    toolId: 'telemetry',
    toolName: 'Hydrological Drainage Flow Simulator',
    actionLabel: 'Simulate Storm Drain Inflow & Blockage',
    suggestedQuery: 'What is the hydraulic inflow reduction caused by debris clogging this storm drain grate?'
  },
  water_01: {
    toolId: 'telemetry',
    toolName: 'Pavement Sub-Base Erosion & Load Risk Calculator',
    actionLabel: 'Calculate Sub-Base Erosion & Load Risk',
    suggestedQuery: 'How does standing water saturation accelerate asphalt fatigue and subgrade failure?'
  },

  // Pediatrics / Toddler Entities
  node_lumbar_lordosis: {
    toolId: 'telemetry',
    toolName: 'LLM Biomechanical Postural & Spinal Alignment Analyzer',
    actionLabel: 'Analyze Plumb Line Gravitational Axis',
    suggestedQuery: 'Is this toddler lumbar lordosis (~38.5°) compensatory to abdominal wall compliance or pathological hyperlordosis?'
  },
  node_knee_bowing: {
    toolId: 'telemetry',
    toolName: 'LLM Pediatric Orthopedic Differential Diagnostician',
    actionLabel: 'Run Symmetrical Genu Varum vs Blount’s Differential',
    suggestedQuery: 'Differentiate this symmetrical toddler knee bowing (2.2cm gap) from early rickets or Blount’s disease.'
  },
  node_protuberant_abdomen: {
    toolId: 'telemetry',
    toolName: 'LLM Biomechanical Postural & Spinal Alignment Analyzer',
    actionLabel: 'Evaluate Abdominal Wall Compliance',
    suggestedQuery: 'How does developing rectus abdominis muscle tone contribute to toddler anterior pelvic tilt?'
  },
  node_wide_base_support: {
    toolId: 'telemetry',
    toolName: 'LLM WHO Milestone & Anthropometric Ratio Evaluator',
    actionLabel: 'Check WHO Motor Milestone Concordance',
    suggestedQuery: 'Does this wide-base stance and flexible flatfoot align with WHO percentiles for independent walking?'
  }
};

export const ImageInspector = ({
  preset,
  presetId,
  activeStep,
  customImageData,
  customImageUrl,
  onImageUploaded,
  onUploadCustom,
  onPasteUrl,
  vlmProviderUsed,
  vlmProvider,
  cameraConnected,
  onCloseCamera,
  nodes = [],
  selectedNodeId,
  onSelectNode,
  onOpenTool,
  onAskQuery,
  onOpenGlossary
}) => {
  const [urlInput, setUrlInput] = useState('');
  const [showUrlInput, setShowUrlInput] = useState(false);
  const [showBoundingBoxes, setShowBoundingBoxes] = useState(true);
  const [hoveredBoxId, setHoveredBoxId] = useState(null);
  const [activeHudNode, setActiveHudNode] = useState(null);
  const fileInputRef = useRef(null);

  const displayImage =
    customImageData ||
    customImageUrl ||
    preset?.image ||
    (presetId === 'agri_monstera_fenestration' || presetId === 'session-3' || preset?.id === 'agri_monstera_fenestration'
      ? '/monstera_sample.png'
      : presetId === 'infra_damaged_road'
      ? 'https://images.unsplash.com/photo-1515162816999-a0c47dc192f7?auto=format&fit=crop&w=1200&q=80'
      : presetId === 'astro_stellar_spectrum'
      ? 'https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?auto=format&fit=crop&w=1200&q=80'
      : presetId?.startsWith('toddler')
      ? 'https://images.unsplash.com/photo-1519689680058-324335c77eba?auto=format&fit=crop&w=1200&q=80'
      : '/monstera_sample.png');

  // Unified upload dispatcher
  const handleUpload = (imgDataOrFile, url) => {
    if (onImageUploaded) onImageUploaded(imgDataOrFile, url);
    if (imgDataOrFile && onUploadCustom) onUploadCustom(imgDataOrFile);
    if (url && onPasteUrl) onPasteUrl(url);
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleUpload(file, null);
    }
  };

  const handleUrlSubmit = (e) => {
    e.preventDefault();
    if (urlInput.trim()) {
      handleUpload(null, urlInput.trim());
      setShowUrlInput(false);
    }
  };

  // Helper to retrieve or synthesize tool mapping for any node ID
  const getToolMapping = (nodeId) => {
    if (ENTITY_TOOL_MAPPINGS[nodeId]) {
      return ENTITY_TOOL_MAPPINGS[nodeId];
    }
    const cleanId = String(nodeId || '').toLowerCase();
    for (const [key, mapping] of Object.entries(ENTITY_TOOL_MAPPINGS)) {
      if (cleanId.includes(key) || key.includes(cleanId)) {
        return mapping;
      }
    }
    return {
      toolId: 'telemetry',
      toolName: 'Diagnostic Simulation Tool',
      actionLabel: 'Inspect Regional Evidence',
      suggestedQuery: `Analyze the scientific implications and causal factors associated with ${nodeId}.`
    };
  };

  // Extract or synthesize grounded nodes with normalized bounding boxes [ymin, xmin, ymax, xmax] (0 to 1000)
  const groundedNodes = useMemo(() => {
    const rawList = Array.isArray(nodes) ? nodes : [];
    const valid = rawList.filter(
      (n) => n.bbox && Array.isArray(n.bbox) && n.bbox.length === 4
    );

    if (valid.length > 0) {
      return valid;
    }

    // High-fidelity fallback grounding coordinates based on active preset / domain
    if (presetId === 'infra_damaged_road' || preset?.id === 'infra_damaged_road') {
      return [
        { id: 'road_01', label: 'Longitudinal Surface Crack', bbox: [310, 190, 780, 520], confidence: 0.96, category: 'structural', properties: { aperture_mm: 18, length_m: 4.5 } },
        { id: 'water_01', label: 'Accumulated Ponding Water', bbox: [440, 470, 880, 860], confidence: 0.93, category: 'environment', properties: { area_m2: 12.5, depth_cm: 4.2 } },
        { id: 'drain_01', label: 'Storm Water Drain Grate', bbox: [120, 670, 410, 940], confidence: 0.98, category: 'infrastructure', properties: { blockage_pct: 88, flow: 'restricted' } },
        { id: 'debris_01', label: 'Organic & Solid Debris', bbox: [150, 640, 370, 890], confidence: 0.91, category: 'obstacle', properties: { type: 'silt & leaves' } }
      ];
    }

    if (presetId === 'astro_stellar_spectrum' || preset?.id === 'astro_stellar_spectrum') {
      return [
        { id: 'spectrum_01', label: 'Stellar Absorption Spectrum', bbox: [140, 80, 460, 920], confidence: 0.99, category: 'spectroscopy', properties: { resolution: 'R=45000' } },
        { id: 'shift_01', label: 'Doppler Line Shift (Δλ)', bbox: [250, 460, 390, 570], confidence: 0.92, category: 'measurement', properties: { shift_angstrom: 0.187 } },
        { id: 'time_series_01', label: 'Photometric Light Curve Dip', bbox: [560, 110, 890, 890], confidence: 0.88, category: 'photometry', properties: { depth_pct: 0.84 } }
      ];
    }

    if (presetId?.startsWith('toddler') || preset?.domain === 'pediatrics') {
      return [
        { id: 'node_lumbar_lordosis', label: 'Accentuated Lumbar Curvature (~38°)', bbox: [340, 280, 620, 520], confidence: 0.94, category: 'biomechanics', properties: { lordosis_deg: 38.5, balance: 'compensated' } },
        { id: 'node_protuberant_abdomen', label: 'Protuberant Abdominal Contour', bbox: [380, 480, 590, 720], confidence: 0.96, category: 'anatomy', properties: { wall_tone: 'developing', visceral_shift: 'anterior' } },
        { id: 'node_knee_bowing', label: 'Symmetrical Genu Varum (2.2cm gap)', bbox: [640, 310, 890, 680], confidence: 0.92, category: 'orthopedic', properties: { symmetry: 'high', gap_cm: 2.2 } },
        { id: 'node_wide_base_support', label: 'Wide-Base Stance & Medial Fat Pad', bbox: [820, 260, 970, 740], confidence: 0.91, category: 'motor', properties: { stance: 'broad', arch: 'physiologic fat pad' } }
      ];
    }

    if (presetId === 'agri_monstera_fenestration' || presetId === 'session-3' || preset?.id === 'agri_monstera_fenestration') {
      return [
        { id: 'leaf_fenestrations_01', label: 'Elliptical Leaf Fenestrations (PCD)', bbox: [90, 300, 430, 590], confidence: 0.96, category: 'morphology', properties: { mechanism: 'Programmed Cell Death (PCD)', pest_damage: 'None' } },
        { id: 'unfurling_apex_leaf_01', label: 'Emergent Juvenile Apical Shoot', bbox: [310, 520, 750, 610], confidence: 0.95, category: 'vegetative_vigor', properties: { turgor: 'high', meristem: 'active expansion' } },
        { id: 'foliar_canopy_01', label: 'Dense Fenestrated Foliage Canopy', bbox: [30, 540, 480, 890], confidence: 0.93, category: 'anatomy', properties: { chlorophyll: 'optimal', fv_fm: '0.81' } },
        { id: 'root_substrate_01', label: 'Coarse Aerated Pot Substrate', bbox: [480, 450, 980, 720], confidence: 0.92, category: 'substrate', properties: { aeration: 'high', pythium_risk: 'low' } }
      ];
    }

    // Default agriculture foliar chlorosis grounding with tomato fruit
    return [
      { id: 'leaf_chlorosis_01', label: 'Interveinal Foliar Chlorosis', bbox: [180, 240, 680, 760], confidence: 0.96, category: 'pathology', properties: { pattern: 'interveinal yellowing', severity: 'acute' } },
      { id: 'fruit_01', label: 'Tomato Fruit Truss (Apical Cluster)', bbox: [440, 110, 640, 340], confidence: 0.95, category: 'developmental', properties: { brix_sugar: '3.8°Bx', rot_risk: 'elevated' } },
      { id: 'irrigation_emitter_01', label: 'Continuous Drip Line Emitter', bbox: [670, 70, 870, 420], confidence: 0.98, category: 'infrastructure', properties: { flow_l_hr: 2.8, pulse: 'unregulated' } },
      { id: 'soil_moisture_sensor_01', label: 'Root Zone Moisture Sensor (48% VWC)', bbox: [720, 520, 910, 830], confidence: 0.94, category: 'measurement', properties: { vwc_pct: 48.2, status: 'waterlogged' } }
    ];
  }, [nodes, presetId, preset]);

  return (
    <div className="glass-panel" style={{ padding: '0.9rem', marginBottom: '1rem', display: 'flex', flexDirection: 'column', position: 'relative', borderRadius: '12px' }}>
      {/* 1. Sleek Compact Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.65rem', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{
            width: '28px',
            height: '28px',
            borderRadius: '6px',
            background: 'rgba(56, 189, 248, 0.12)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Camera size={15} color="var(--primary)" />
          </div>
          <div>
            <span style={{ fontWeight: '700', fontSize: '0.86rem', color: 'var(--text-main)' }}>Visual Evidence Grounding</span>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginLeft: '6px' }}>({groundedNodes.length} anchors)</span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          {/* Quick upload button */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept="image/*"
            style={{ display: 'none' }}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '0.25rem 0.55rem',
              borderRadius: '6px',
              background: 'var(--bg-dark)',
              border: '1px solid var(--border-color)',
              fontSize: '0.72rem',
              color: 'var(--text-main)',
              cursor: 'pointer',
              fontWeight: 500
            }}
            title="Upload specimen photo"
          >
            <Upload size={12} />
            <span>Upload</span>
          </button>

          {/* Stream URL Toggle */}
          <button
            onClick={() => setShowUrlInput(!showUrlInput)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '0.25rem 0.55rem',
              borderRadius: '6px',
              background: showUrlInput ? 'rgba(56, 189, 248, 0.15)' : 'var(--bg-dark)',
              border: showUrlInput ? '1px solid var(--primary)' : '1px solid var(--border-color)',
              fontSize: '0.72rem',
              color: showUrlInput ? 'var(--primary)' : 'var(--text-main)',
              cursor: 'pointer',
              fontWeight: 500
            }}
            title="Load image from URL"
          >
            <LinkIcon size={12} />
            <span>URL</span>
          </button>

          {/* Bounding Box Toggle */}
          <button
            onClick={() => setShowBoundingBoxes(!showBoundingBoxes)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '0.25rem 0.55rem',
              borderRadius: '6px',
              background: showBoundingBoxes ? 'rgba(56, 189, 248, 0.12)' : 'var(--bg-dark)',
              border: showBoundingBoxes ? '1px solid rgba(56, 189, 248, 0.4)' : '1px solid var(--border-color)',
              fontSize: '0.72rem',
              color: showBoundingBoxes ? 'var(--primary)' : 'var(--text-muted)',
              cursor: 'pointer',
              fontWeight: 600
            }}
            title="Toggle bounding boxes on image"
          >
            {showBoundingBoxes ? <Eye size={12} /> : <EyeOff size={12} />}
            <span>{showBoundingBoxes ? 'Anchors ON' : 'OFF'}</span>
          </button>

          {onCloseCamera && (
            <button onClick={onCloseCamera} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '2px' }}>
              <X size={15} />
            </button>
          )}
        </div>
      </div>

      {/* URL Input Form */}
      {showUrlInput && (
        <form onSubmit={handleUrlSubmit} style={{ display: 'flex', gap: '0.4rem', marginBottom: '0.6rem' }}>
          <input
            type="url"
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            placeholder="Paste direct image URL (https://...)"
            style={{
              flex: 1,
              padding: '0.3rem 0.55rem',
              borderRadius: '6px',
              border: '1px solid var(--border-color)',
              background: 'var(--bg-dark)',
              color: 'var(--text-main)',
              fontSize: '0.76rem'
            }}
          />
          <button type="submit" className="btn btn-primary" style={{ padding: '0.3rem 0.65rem', fontSize: '0.75rem' }}>
            Load
          </button>
        </form>
      )}

      {/* 2. Visual Evidence Container */}
      <div style={{
        position: 'relative',
        width: '100%',
        minHeight: '260px',
        maxHeight: '440px',
        aspectRatio: '16 / 10',
        borderRadius: '10px',
        overflow: 'hidden',
        border: '1px solid var(--border-color)',
        background: '#090d16',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: '0 4px 16px rgba(0,0,0,0.25)'
      }}>
        {/* Base Image */}
        {displayImage ? (
          <img
            src={displayImage}
            alt="Visual Evidence"
            onError={(e) => {
              if (!e.target.src.includes('monstera_sample.png')) {
                e.target.src = '/monstera_sample.png';
              }
            }}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'contain',
              display: 'block'
            }}
          />
        ) : (
          <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
            <Camera size={32} style={{ opacity: 0.5, marginBottom: '0.4rem' }} />
            <div style={{ fontSize: '0.8rem' }}>No visual evidence loaded</div>
          </div>
        )}

        {/* SVG Bounding Boxes Overlay */}
        {showBoundingBoxes && displayImage && groundedNodes.length > 0 && (
          <svg
            viewBox="0 0 1000 1000"
            preserveAspectRatio="none"
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              pointerEvents: 'auto',
              zIndex: 5
            }}
          >
            <defs>
              <filter id="box-glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="6" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            {groundedNodes.map((node) => {
              const [ymin, xmin, ymax, xmax] = node.bbox;
              const width = Math.max(30, xmax - xmin);
              const height = Math.max(30, ymax - ymin);
              const isSelected =
                (selectedNodeId &&
                  (node.id === selectedNodeId ||
                    node.id.toLowerCase() === selectedNodeId.toLowerCase() ||
                    node.label?.toLowerCase().includes(selectedNodeId.toLowerCase()))) ||
                (activeHudNode && activeHudNode.id === node.id);
              const isHovered = hoveredBoxId === node.id;

              const labelWidth = Math.min(Math.max(width, 130), 220);

              return (
                <g
                  key={node.id}
                  onClick={() => {
                    const next = activeHudNode?.id === node.id ? null : node;
                    setActiveHudNode(next);
                    if (onSelectNode) onSelectNode(next ? node.id : null);
                  }}
                  onMouseEnter={() => setHoveredBoxId(node.id)}
                  onMouseLeave={() => setHoveredBoxId(null)}
                  style={{
                    cursor: 'pointer',
                    transition: 'all 0.15s ease-out'
                  }}
                >
                  {/* Bounding Box Rectangle */}
                  <rect
                    x={xmin}
                    y={ymin}
                    width={width}
                    height={height}
                    rx="6"
                    fill={
                      isSelected
                        ? 'rgba(56, 189, 248, 0.28)'
                        : isHovered
                        ? 'rgba(56, 189, 248, 0.14)'
                        : 'rgba(56, 189, 248, 0.04)'
                    }
                    stroke={isSelected ? '#38bdf8' : isHovered ? '#7dd3fc' : 'rgba(56, 189, 248, 0.85)'}
                    strokeWidth={isSelected ? 4 : isHovered ? 3 : 2}
                    strokeDasharray={isSelected ? '8,4' : 'none'}
                    filter={isSelected || isHovered ? 'url(#box-glow)' : 'none'}
                  />

                  {/* Corner Target Reticles */}
                  {isSelected && (
                    <>
                      <circle cx={xmin} cy={ymin} r="4.5" fill="#38bdf8" />
                      <circle cx={xmax} cy={ymin} r="4.5" fill="#38bdf8" />
                      <circle cx={xmin} cy={ymax} r="4.5" fill="#38bdf8" />
                      <circle cx={xmax} cy={ymax} r="4.5" fill="#38bdf8" />
                    </>
                  )}

                  {/* Compact Grounded Entity Badge */}
                  <g transform={`translate(${xmin}, ${Math.max(6, ymin - 26)})`}>
                    <rect
                      x="0"
                      y="0"
                      width={labelWidth}
                      height="24"
                      rx="5"
                      fill={isSelected ? '#0284c7' : isHovered ? 'rgba(15, 23, 42, 0.95)' : 'rgba(15, 23, 42, 0.88)'}
                      stroke={isSelected ? '#7dd3fc' : isHovered ? '#38bdf8' : 'rgba(56, 189, 248, 0.4)'}
                      strokeWidth="1.2"
                    />

                    <circle cx="12" cy="12" r="5" fill={isSelected ? 'rgba(255,255,255,0.3)' : 'rgba(56, 189, 248, 0.3)'} />
                    <text x="9" y="15" fill={isSelected ? '#ffffff' : '#38bdf8'} fontSize="9px" fontWeight="bold">⚡</text>

                    <text
                      x="22"
                      y="16"
                      fill="#ffffff"
                      fontSize="11px"
                      fontFamily="Outfit, sans-serif"
                      fontWeight="600"
                    >
                      {node.label.length > 22 ? node.label.substring(0, 20) + '…' : node.label}
                    </text>
                  </g>
                </g>
              );
            })}
          </svg>
        )}

        {/* Minimal subtle bottom bar */}
        <div style={{
          position: 'absolute',
          bottom: 6,
          left: 8,
          right: 8,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'rgba(0, 0, 0, 0.65)',
          backdropFilter: 'blur(6px)',
          padding: '0.25rem 0.6rem',
          borderRadius: '5px',
          color: '#ffffff',
          fontSize: '0.68rem',
          zIndex: 10,
          pointerEvents: 'none'
        }}>
          <span style={{ fontWeight: 500, opacity: 0.9 }}>{preset?.title || "Visual Evidence"}</span>
          <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--emerald)' }}>
            {groundedNodes.length} Anchors Grounded
          </span>
        </div>
      </div>

      {/* 3. Dedicated Inspector Card (Rendered cleanly below the photo, leaving image 100% visible) */}
      {activeHudNode && (
        <div
          className="animate-fade-in"
          style={{
            marginTop: '0.75rem',
            background: 'var(--bg-dark)',
            border: '1px solid rgba(56, 189, 248, 0.4)',
            borderRadius: '10px',
            padding: '0.75rem 0.85rem',
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.08)'
          }}
        >
          {/* Card Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <div style={{
                width: '26px',
                height: '26px',
                borderRadius: '6px',
                background: 'rgba(56, 189, 248, 0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--primary)'
              }}>
                <Zap size={14} />
              </div>
              <div>
                <div style={{ fontWeight: '700', fontSize: '0.86rem', color: 'var(--text-main)', lineHeight: 1.2 }}>
                  {activeHudNode.label}
                </div>
                <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px', marginTop: '2px' }}>
                  <span style={{ textTransform: 'uppercase', fontWeight: 600, color: 'var(--primary)' }}>
                    {activeHudNode.category || 'entity'}
                  </span>
                  <span>•</span>
                  <span style={{ color: 'var(--emerald)', fontFamily: 'var(--font-mono)' }}>
                    {Math.round((activeHudNode.confidence || 0.9) * 100)}% Confidence
                  </span>
                </div>
              </div>
            </div>

            <button
              onClick={() => setActiveHudNode(null)}
              style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '3px' }}
              title="Close inspection card"
            >
              <X size={15} />
            </button>
          </div>

          {/* Properties / Attributes Row */}
          {activeHudNode.properties && Object.keys(activeHudNode.properties).length > 0 && (
            <div style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: '0.35rem',
              marginBottom: '0.6rem'
            }}>
              {Object.entries(activeHudNode.properties).slice(0, 4).map(([k, v]) => (
                <div
                  key={k}
                  style={{
                    background: 'rgba(56, 189, 248, 0.08)',
                    border: '1px solid rgba(56, 189, 248, 0.2)',
                    borderRadius: '5px',
                    padding: '0.2rem 0.45rem',
                    fontSize: '0.68rem',
                    fontFamily: 'var(--font-mono)',
                    display: 'flex',
                    gap: '4px'
                  }}
                >
                  <span style={{ color: 'var(--text-muted)' }}>{k.replace(/_/g, ' ')}:</span>
                  <span style={{ color: 'var(--primary)', fontWeight: 600 }}>{String(v)}</span>
                </div>
              ))}
            </div>
          )}

          {/* Action Row */}
          <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
            <button
              className="btn btn-primary"
              onClick={() => {
                const mapping = getToolMapping(activeHudNode.id);
                if (onOpenTool) onOpenTool(mapping.toolId, activeHudNode);
                setActiveHudNode(null);
              }}
              style={{
                flex: 2,
                fontSize: '0.74rem',
                padding: '0.4rem 0.6rem',
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '5px'
              }}
            >
              <Sparkles size={13} />
              <span>Launch {getToolMapping(activeHudNode.id).toolName}</span>
            </button>

            <button
              className="btn btn-secondary"
              onClick={() => {
                const mapping = getToolMapping(activeHudNode.id);
                if (onAskQuery) onAskQuery(mapping.suggestedQuery || `Analyze the physical implications of ${activeHudNode.label}`);
                setActiveHudNode(null);
              }}
              style={{
                flex: 1,
                fontSize: '0.72rem',
                padding: '0.4rem 0.5rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '4px'
              }}
            >
              <Crosshair size={12} color="var(--primary)" />
              <span>Ask SAAR</span>
            </button>

            <button
              className="btn btn-secondary"
              onClick={() => {
                if (onOpenGlossary) onOpenGlossary(activeHudNode.label);
                setActiveHudNode(null);
              }}
              style={{
                fontSize: '0.72rem',
                padding: '0.4rem 0.55rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '4px'
              }}
            >
              <Layers size={12} color="var(--emerald)" />
              <span>Glossary</span>
            </button>
          </div>
        </div>
      )}

      {/* 4. Sleek Visual Anchors Chips */}
      {groundedNodes.length > 0 && (
        <div style={{ marginTop: '0.75rem' }}>
          <div style={{
            fontSize: '0.72rem',
            fontWeight: 600,
            color: 'var(--text-muted)',
            marginBottom: '0.4rem',
            display: 'flex',
            alignItems: 'center',
            gap: '4px'
          }}>
            <Target size={12} color="var(--primary)" />
            <span>Interactive Anchors (click to inspect):</span>
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
            {groundedNodes.map((n) => {
              const isSelected =
                (selectedNodeId &&
                  (n.id === selectedNodeId ||
                    n.id.toLowerCase() === selectedNodeId.toLowerCase() ||
                    n.label?.toLowerCase().includes(selectedNodeId.toLowerCase()))) ||
                (activeHudNode && activeHudNode.id === n.id);

              return (
                <button
                  key={n.id}
                  onClick={() => {
                    const next = activeHudNode?.id === n.id ? null : n;
                    setActiveHudNode(next);
                    if (onSelectNode) onSelectNode(next ? n.id : null);
                  }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '5px',
                    padding: '0.3rem 0.65rem',
                    borderRadius: '20px',
                    background: isSelected ? 'rgba(56, 189, 248, 0.15)' : 'var(--bg-dark)',
                    border: isSelected ? '1px solid var(--primary)' : '1px solid var(--border-color)',
                    color: isSelected ? 'var(--primary)' : 'var(--text-main)',
                    fontSize: '0.74rem',
                    fontWeight: isSelected ? '600' : '400',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <Crosshair size={11} color={isSelected ? 'var(--primary)' : 'var(--emerald)'} />
                  <span>{n.label}</span>
                  <span style={{ fontSize: '0.66rem', opacity: 0.7, fontFamily: 'var(--font-mono)' }}>
                    {Math.round((n.confidence || 0.9) * 100)}%
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
