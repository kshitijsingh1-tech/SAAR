import React, { useState, useEffect, useRef } from 'react';
import {
  Zap, Sparkles, ArrowRight, Activity, GitFork, BookOpen,
  ShieldCheck, CheckCircle2, Sprout, Construction, Orbit, Baby,
  Play, Pause, Sun, Moon, Check, ChevronDown, Cpu, Terminal,
  Maximize2, ExternalLink, RefreshCw, Eye, Sliders, Layers,
  RotateCcw, Info, CheckCircle, XCircle, AlertCircle, HelpCircle,
  TrendingDown, TrendingUp, AlertTriangle, Crosshair, Clock, Atom
} from 'lucide-react';

export function LandingPage({
  onEnterStudio,
  theme = 'dark',
  onToggleTheme,
  onSelectTheme
}) {
  // ToddlerAI as First Domain, Agriculture as Second Domain
  const [activeScenarioId, setActiveScenarioId] = useState('gait');
  const [isThemeDropdownOpen, setIsThemeDropdownOpen] = useState(false);
  const [selectedNodeId, setSelectedNodeId] = useState('node-math');
  const [isFlowPlaying, setIsFlowPlaying] = useState(true);

  const themeDropdownRef = useRef(null);

  // Close theme dropdown when clicking outside
  useEffect(() => {
    const handleOutsideClick = (e) => {
      if (themeDropdownRef.current && !themeDropdownRef.current.contains(e.target)) {
        setIsThemeDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleOutsideClick);
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, []);

  // Scientific Scenarios for Causal Graph Topology (ToddlerAI first, Agronomy second)
  const scenarios = {
    gait: {
      id: 'gait',
      title: 'ToddlerAI Biomechanics',
      subtitle: '33-Joint Kinematics & Pose Estimation Engine',
      icon: <Baby size={16} className="text-sky" />,
      color: '#0284c7',
      equation: '\\theta_{\\text{dorsi}} = \\arccos\\left(\\frac{\\vec{u} \\cdot \\vec{v}}{\\|\\vec{u}\\| \\|\\vec{v}\\|}\\right)',
      equationName: 'Ankle Dorsiflexion Kinematics',
      stats: { nodes: 9, edges: 9, confidence: 92.7, entropy: 0.073 },
      nodes: [
        {
          id: 'node-ndre',
          title: '33 Joint Landmark Pose',
          tier: 'PERCEPTION',
          value: '60 FPS Stream',
          formula: '\\vec{P}_j(t) = (x_j, y_j, z_j)',
          status: 'GROUNDED',
          desc: 'Monocular video landmark extraction tracking ankle, knee, and hip trajectory vectors.',
          x: 120, y: 95
        },
        {
          id: 'node-vwc',
          title: 'Foot-Strike Cadence',
          tier: 'PERCEPTION',
          value: '46 Gait Cycles',
          formula: 'T_{stride} = t_{strike, i+1} - t_{strike, i}',
          status: 'GROUNDED',
          desc: 'Contact-point velocity zero-crossing detector isolates stance and swing phases.',
          x: 120, y: 265
        },
        {
          id: 'node-math',
          title: 'Temporal Cadence Calc',
          tier: 'PHYSICS',
          value: 'Asymmetry: 24%',
          formula: '\\text{Asym} = \\frac{|T_L - T_R|}{\\bar{T}} \\times 100',
          status: 'CONFIRMED',
          desc: 'Persistent 24% temporal deficit between left and right step time (typical <= 10%).',
          x: 350, y: 95
        },
        {
          id: 'node-fe',
          title: 'Ankle Dorsiflexion',
          tier: 'PHYSICS',
          value: '\\theta = 14^{\\circ} \\text{ (Low)}',
          formula: '\\theta = \\arccos\\left(\\frac{\\vec{u} \\cdot \\vec{v}}{\\|\\vec{u}\\| \\|\\vec{v}\\|}\\right)',
          status: 'CONFIRMED',
          desc: 'Limited heel-strike dorsiflexion indicates premature gastrocnemius contraction.',
          x: 350, y: 265
        },
        {
          id: 'node-h1',
          title: 'H1: Spastic Diplegia',
          tier: 'HYPOTHESIS',
          value: 'P(H1) = 0.927',
          formula: 'P(\\text{Spasticity}|\\theta, \\text{Asym})',
          status: 'CONFIRMED',
          desc: 'Gait asymmetry paired with restricted dorsiflexion points to motor tone impairment.',
          x: 580, y: 95
        },
        {
          id: 'node-h2',
          title: 'H2: Benign Toe-Walking',
          tier: 'HYPOTHESIS',
          value: 'P(H2) = 0.073',
          formula: 'P(\\text{Idiopathic}) < 0.10',
          status: 'REFUTED',
          desc: 'Idiopathic toe-walking is typically symmetrical; 24% unilateral asymmetry refutes this.',
          x: 580, y: 265
        },
        {
          id: 'node-inq',
          title: 'Catch Angle Test',
          tier: 'INQUIRY',
          value: 'Resistance at 90°',
          formula: '\\text{Catch angle } \\theta_{catch}',
          status: 'VERIFIED',
          desc: 'Velocity-dependent catch confirms spastic hypertonia rather than bone deformity.',
          x: 810, y: 95
        },
        {
          id: 'node-drain',
          title: 'Pelvic Symmetry Check',
          tier: 'INQUIRY',
          value: 'Tilt Deficit: 18°',
          formula: '\\Delta\\phi_{pelvis} = 18.2^{\\circ}',
          status: 'VERIFIED',
          desc: 'Compensatory pelvic rotation during terminal swing phase.',
          x: 810, y: 265
        },
        {
          id: 'node-verdict',
          title: 'Motor Screening Verdict',
          tier: 'POSTERIOR',
          value: 'Confidence 92.7%',
          formula: '\\text{Neuromotor Referral}',
          status: 'PROVEN',
          desc: 'Objective mathematical kinematic screening completed with zero diagnostic hallucination.',
          x: 1020, y: 180
        }
      ],
      edges: [
        { from: 'node-ndre', to: 'node-math', weight: '0.94', label: 'Trajectory' },
        { from: 'node-vwc', to: 'node-math', weight: '0.96', label: 'Stride Time' },
        { from: 'node-vwc', to: 'node-fe', weight: '0.91', label: 'Ground Contact' },
        { from: 'node-math', to: 'node-h1', weight: '0.95', label: 'Cadence Asym' },
        { from: 'node-fe', to: 'node-h2', weight: '0.10', label: 'Refuted (P<0.1)' },
        { from: 'node-h1', to: 'node-inq', weight: '0.93', label: 'Spastic Tone' },
        { from: 'node-h2', to: 'node-drain', weight: '0.19', label: 'Pelvic Rotation' },
        { from: 'node-inq', to: 'node-verdict', weight: '0.97', label: 'Clinical Sign' },
        { from: 'node-drain', to: 'node-verdict', weight: '0.92', label: 'Compensatory' }
      ],
      query: 'Run ToddleAI video pose estimation on toddler walking clip and assess gait asymmetry.',
      presetId: 'pediatric_gait_analysis',
      domain: 'pediatric'
    },
    agri: {
      id: 'agri',
      title: 'Agricultural Science',
      subtitle: 'Root Hypoxia & Soil Hydrology Engine',
      icon: <Sprout size={16} className="text-emerald" />,
      color: '#10b981',
      equation: 'Q = -K \\cdot A \\cdot \\frac{\\Delta h}{L}',
      equationName: "Darcy's Law Soil Water Flux",
      stats: { nodes: 9, edges: 9, confidence: 94.8, entropy: 0.052 },
      nodes: [
        {
          id: 'node-ndre',
          title: 'NDRE Spectral Camera',
          tier: 'PERCEPTION',
          value: '0.18 (-68.4%)',
          formula: 'NDRE = (\\rho_{NIR} - \\rho_{RE}) / (\\rho_{NIR} + \\rho_{RE})',
          status: 'GROUNDED',
          desc: 'Sharp foliar chlorophyll depletion detected in terminal canopies.',
          x: 120, y: 95
        },
        {
          id: 'node-vwc',
          title: 'Root-Zone TDT Probe',
          tier: 'PERCEPTION',
          value: '48.2% VWC',
          formula: '\\theta_v = V_{water} / V_{total}',
          status: 'GROUNDED',
          desc: 'Sustained volumetric water content above field capacity (>72 hrs).',
          x: 120, y: 265
        },
        {
          id: 'node-math',
          title: "Darcy Flux Hydrology",
          tier: 'PHYSICS',
          value: 'Q = -1.42 m/s',
          formula: 'Q = -K \\cdot A \\cdot \\frac{\\Delta h}{L}',
          status: 'CONFIRMED',
          desc: 'Hydraulic head gradient proves severe subterranean saturation & nutrient leaching.',
          x: 350, y: 95
        },
        {
          id: 'node-fe',
          title: 'Fe Bioavailability',
          tier: 'PHYSICS',
          value: '0.41 mg/kg (Crit)',
          formula: 'Fe^{2+} + 2OH^- \\to Fe(OH)_2 \\downarrow',
          status: 'CONFIRMED',
          desc: 'Root substrate alkalinization precipitates soluble iron into insoluble hydroxides.',
          x: 350, y: 265
        },
        {
          id: 'node-h1',
          title: 'H1: Pythium Root Rot',
          tier: 'HYPOTHESIS',
          value: 'P(H1) = 0.948',
          formula: 'P(H_1|E) = \\frac{P(E|H_1)P(H_1)}{P(E)}',
          status: 'CONFIRMED',
          desc: 'Warm saturated soil triggered opportunistic fungal pathogen colonization.',
          x: 580, y: 95
        },
        {
          id: 'node-h2',
          title: 'H2: Nitrogen Deficit',
          tier: 'HYPOTHESIS',
          value: 'P(H2) = 0.052',
          formula: 'P(H_2|E) < 0.10',
          status: 'REFUTED',
          desc: 'Leaf tissue nitrogen levels normal; ruled out as primary etiology.',
          x: 580, y: 265
        },
        {
          id: 'node-inq',
          title: 'PCD Margin Test',
          tier: 'INQUIRY',
          value: 'Suberized PCD',
          formula: '\\Delta H_{gain} = 0.384\\text{ nats}',
          status: 'VERIFIED',
          desc: 'Clean suberized perimeters exclude chewing herbivory and shot-hole fungus.',
          x: 810, y: 95
        },
        {
          id: 'node-drain',
          title: 'Perlite Porosity Check',
          tier: 'INQUIRY',
          value: 'K = 0.003 cm/s',
          formula: 'K = \\frac{Q \\cdot L}{A \\cdot \\Delta h}',
          status: 'VERIFIED',
          desc: 'Permeability check indicates compacted drainage medium.',
          x: 810, y: 265
        },
        {
          id: 'node-verdict',
          title: 'Pythium Root Rot Verdict',
          tier: 'POSTERIOR',
          value: 'Confidence 94.8%',
          formula: '\\text{Argmax}_H P(H|E) = \\text{Pythium}',
          status: 'PROVEN',
          desc: 'Definitive causal chain proven with zero single-pass heuristic hallucination.',
          x: 1020, y: 180
        }
      ],
      edges: [
        { from: 'node-ndre', to: 'node-math', weight: '0.94', label: 'Spectral Flux' },
        { from: 'node-vwc', to: 'node-math', weight: '0.97', label: 'Darcy Head' },
        { from: 'node-vwc', to: 'node-fe', weight: '0.89', label: 'Ion Leaching' },
        { from: 'node-math', to: 'node-h1', weight: '0.95', label: 'Hypoxia Path' },
        { from: 'node-fe', to: 'node-h2', weight: '0.12', label: 'Refuted (P<0.1)' },
        { from: 'node-h1', to: 'node-inq', weight: '0.93', label: 'Cell PCD' },
        { from: 'node-h2', to: 'node-drain', weight: '0.18', label: 'Substrate Check' },
        { from: 'node-inq', to: 'node-verdict', weight: '0.98', label: 'Argmax Posterior' },
        { from: 'node-drain', to: 'node-verdict', weight: '0.91', label: 'Grounded Proof' }
      ],
      query: 'Investigate 30-day tomato crop failure dataset and identify root cause of leaf chlorosis.',
      presetId: 'agri_tomato_chlorosis',
      domain: 'agriculture'
    }
  };

  const activeScenario = scenarios[activeScenarioId] || scenarios.gait;
  const activeNode = activeScenario.nodes.find((n) => n.id === selectedNodeId) || activeScenario.nodes[2];

  // 3 Themes Requested:
  // 1. Pure Light (Crisp White)
  // 2. Pure Dark (Deep Obsidian)
  // 3. Lavender White (Pure White with Purple Tint Only)
  const THEMES = [
    { id: 'light', label: 'Pure Light', icon: <Sun size={13} />, color: '#0284c7', desc: 'Crisp White & Dark Slate' },
    { id: 'dark', label: 'Pure Dark', icon: <Moon size={13} />, color: '#818cf8', desc: 'Obsidian OLED & Sleek Slate' },
    { id: 'purple', label: 'Lavender White', icon: <Sparkles size={13} />, color: '#7e22ce', desc: 'White with Purple Tint' }
  ];

  const isLightMode = theme === 'light' || theme === 'purple';

  return (
    <div className={`saar-landing-page ${theme}`}>
      {/* Clean Ambient Background Canvas (Zero Color Spots) */}
      <div className="landing-ambient-canvas">
        <div className="cyber-grid" />
      </div>

      {/* 1. Glassmorphic Navigation Header */}
      <nav className="landing-navbar">
        <div className="landing-nav-content">
          <div className="landing-brand-group" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
            <div className="landing-brand-emblem mini">
              <img
                src={isLightMode ? '/saar-logo-dark.png' : '/saar-logo-white.png'}
                alt="SAAR Logo"
                className="brand-logo-img"
              />
            </div>
            <div className="landing-brand-text">
              <span className="landing-brand-title">SAAR</span>
              <span className="landing-brand-sub">DISCOVER WHAT MATTERS</span>
            </div>
          </div>

          <div className="landing-nav-links">
            <a href="#causal-workbench" className="landing-nav-link">
              <GitFork size={14} />
              <span>Causal DAG Engine</span>
            </a>
            <a href="#saar-domains" className="landing-nav-link">
              <Layers size={14} />
              <span>3 Core Domains</span>
            </a>
          </div>

          <div className="landing-nav-actions">
            {/* 3-Theme Dropdown */}
            <div className="theme-dropdown-container" ref={themeDropdownRef}>
              <button
                type="button"
                className="theme-dropdown-trigger"
                onClick={() => setIsThemeDropdownOpen((prev) => !prev)}
                title="Select Website Theme"
              >
                {theme === 'light' && <Sun size={14} className="theme-icon-indicator" />}
                {theme === 'dark' && <Moon size={14} className="theme-icon-indicator" />}
                {theme === 'purple' && <Sparkles size={14} className="theme-icon-indicator text-purple" />}
                <span className="theme-trigger-label">
                  {theme === 'light' ? 'Pure Light' : theme === 'dark' ? 'Pure Dark' : 'Lavender White'}
                </span>
                <ChevronDown size={11} className={`theme-chevron ${isThemeDropdownOpen ? 'open' : ''}`} />
              </button>

              {isThemeDropdownOpen && (
                <div className="theme-dropdown-menu">
                  <div className="theme-menu-header">THEME PALETTE</div>
                  {THEMES.map((t) => (
                    <button
                      key={t.id}
                      type="button"
                      className={`theme-dropdown-item ${theme === t.id ? 'active' : ''}`}
                      onClick={() => {
                        onSelectTheme?.(t.id);
                        setIsThemeDropdownOpen(false);
                      }}
                    >
                      <span className="theme-swatch" style={{ backgroundColor: t.color }} />
                      <div className="theme-info-col">
                        <span className="theme-label-text">{t.label}</span>
                        <span className="theme-desc-text">{t.desc}</span>
                      </div>
                      {theme === t.id && <Check size={13} className="theme-item-check" />}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <button
              type="button"
              className="btn-launch-studio-nav"
              onClick={() => onEnterStudio()}
            >
              <Zap size={15} />
              <span>Launch Studio</span>
            </button>
          </div>
        </div>
      </nav>

      {/* 2. Hero Section with BIG Logo & DISCOVER WHAT MATTERS */}
      <section className="landing-hero-heroic">
        {/* Big Crisp SAAR Logo on Top */}
        <div className="hero-giant-logo-wrapper">
          <img
            src={isLightMode ? '/saar-logo-dark.png' : '/saar-logo-white.png'}
            alt="SAAR Logo"
            className="hero-giant-logo-img"
          />
          <div className="hero-giant-wordmark-row">
            <img
              src={isLightMode ? '/saar-wordmark-dark.png' : '/saar-wordmark-white.png'}
              alt="SAAR Wordmark"
              className="hero-giant-wordmark-img"
            />
          </div>
        </div>

        {/* Main Brand Tagline */}
        <h1 className="hero-heroic-title">
          <span className="gradient-text-glow">DISCOVER WHAT MATTERS</span>
        </h1>
        <p className="hero-heroic-sub">
          Visual Scientific Reasoning • Beyond Black-Box Hallucination
        </p>

        {/* Action Buttons */}
        <div className="hero-heroic-actions">
          <button
            type="button"
            className="luminous-btn-primary"
            onClick={() => onEnterStudio()}
          >
            <Zap size={16} />
            <span>Launch Studio Console</span>
            <ArrowRight size={16} />
          </button>

          <a href="#saar-domains" className="luminous-btn-secondary">
            <Layers size={15} className="text-primary" />
            <span>Explore 3 Scientific Domains</span>
          </a>
        </div>

        {/* Minimal Metric Strip */}
        <div className="hero-metric-strip-minimal">
          <div className="metric-chip">
            <span className="metric-num">94.8%</span>
            <span className="metric-lbl">Diagnostic Precision</span>
          </div>
          <div className="metric-divider" />
          <div className="metric-chip">
            <span className="metric-num">0 ms</span>
            <span className="metric-lbl">Hallucination Tolerance</span>
          </div>
          <div className="metric-divider" />
          <div className="metric-chip">
            <span className="metric-num">3</span>
            <span className="metric-lbl">Scientific Domains</span>
          </div>
          <div className="metric-divider" />
          <div className="metric-chip">
            <span className="metric-num">100%</span>
            <span className="metric-lbl">Auditable DAG Chains</span>
          </div>
        </div>
      </section>

      {/* 3. HIGH-TECH IN-FRAME DYNAMIC NETWORKX CAUSAL GRAPH WORKBENCH */}
      <section id="causal-workbench" className="landing-section-wrapper full-width">
        <div className="luminous-frost-card full-graph-workbench-card in-frame-hud">
          {/* Futuristic Sci-Fi Frame Reticles */}
          <div className="hud-corner top-left" />
          <div className="hud-corner top-right" />
          <div className="hud-corner bottom-left" />
          <div className="hud-corner bottom-right" />

          {/* Clean Header & Domain Switcher */}
          <div className="workbench-top-bar">
            <h2 className="luminous-card-title">Causal Reasoning Graph</h2>

            {/* Scenario Switcher Pills */}
            <div className="scenario-switcher-inline">
              {Object.values(scenarios).map((scen) => (
                <button
                  key={scen.id}
                  type="button"
                  className={`scen-pill-btn ${activeScenarioId === scen.id ? 'active' : ''}`}
                  onClick={() => {
                    setActiveScenarioId(scen.id);
                    setSelectedNodeId('node-math');
                  }}
                >
                  {scen.icon}
                  <span>{scen.title}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Stage Sequence Headers Bar */}
          <div className="dag-stage-headers-strip">
            <div className="stage-header-tag stage-1">
              <span className="stage-num">01</span>
              <span className="stage-txt">SENSOR PERCEPTION</span>
            </div>
            <div className="stage-header-tag stage-2">
              <span className="stage-num">02</span>
              <span className="stage-txt">PHYSICAL LAWS</span>
            </div>
            <div className="stage-header-tag stage-3">
              <span className="stage-num">03</span>
              <span className="stage-txt">BAYESIAN HYPOTHESES</span>
            </div>
            <div className="stage-header-tag stage-4">
              <span className="stage-num">04</span>
              <span className="stage-txt">EPISTEMIC INQUIRY</span>
            </div>
            <div className="stage-header-tag stage-5">
              <span className="stage-num">05</span>
              <span className="stage-txt">GROUNDED VERDICT</span>
            </div>
          </div>

          {/* Perfectly Scaled In-Frame SVG DAG Canvas */}
          <div className="full-dag-canvas-container in-frame-canvas">
            {/* SVG Linking Edges with Animated Flowing Laser Packets and Directional Arrowheads */}
            <svg className="full-dag-svg" viewBox="0 0 1140 370" preserveAspectRatio="xMidYMid meet">
              <defs>
                <filter id="laserGlow" x="-30%" y="-30%" width="160%" height="160%">
                  <feGaussianBlur stdDeviation="3" result="blur" />
                  <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
                <marker
                  id="laserArrow"
                  viewBox="0 0 10 10"
                  refX="6"
                  refY="5"
                  markerWidth="6"
                  markerHeight="6"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 1 L 10 5 L 0 9 z" fill="var(--primary)" />
                </marker>
              </defs>

              {/* Edge Connections with Weight Labels & Active Path Tracing */}
              {activeScenario.edges.map((edge, idx) => {
                const srcNode = activeScenario.nodes.find((n) => n.id === edge.from);
                const dstNode = activeScenario.nodes.find((n) => n.id === edge.to);
                if (!srcNode || !dstNode) return null;

                const isDirectlyActive = selectedNodeId === edge.from || selectedNodeId === edge.to;
                const dx = dstNode.x - srcNode.x;
                const pathD = `M ${srcNode.x + 75} ${srcNode.y} C ${srcNode.x + dx * 0.48} ${srcNode.y}, ${dstNode.x - dx * 0.48} ${dstNode.y}, ${dstNode.x - 75} ${dstNode.y}`;
                const midX = (srcNode.x + dstNode.x) / 2;
                const midY = (srcNode.y + dstNode.y) / 2;

                return (
                  <g key={idx} className={`dag-edge-group ${isDirectlyActive ? 'is-active-path' : ''}`}>
                    {/* Background edge wire */}
                    <path
                      d={pathD}
                      className={`svg-edge-wire ${isDirectlyActive ? 'highlighted' : ''}`}
                      markerEnd="url(#laserArrow)"
                    />
                    {/* Flowing Laser Packet */}
                    {isFlowPlaying && (
                      <path
                        d={pathD}
                        className={`svg-moving-laser packet-flow-${idx % 5}`}
                      />
                    )}
                    {/* Edge Weight / Confidence Badge */}
                    <g className="edge-weight-tag-group" transform={`translate(${midX}, ${midY})`}>
                      <rect x="-24" y="-9" width="48" height="18" rx="5" className="edge-weight-bg" />
                      <text x="0" y="3" textAnchor="middle" className="edge-weight-text">
                        w={edge.weight}
                      </text>
                    </g>
                  </g>
                );
              })}
            </svg>

            {/* Interactive HTML Nodes Positioned Safely Inside the Frame */}
            {activeScenario.nodes.map((node) => {
              const isSelected = selectedNodeId === node.id;
              const isVerdict = node.tier === 'POSTERIOR';

              return (
                <div
                  key={node.id}
                  className={`full-interactive-node tier-${node.tier.toLowerCase()} ${isSelected ? 'selected' : ''} ${isVerdict ? 'node-verdict-glow' : ''}`}
                  style={{
                    left: `${(node.x / 1140) * 100}%`,
                    top: `${(node.y / 370) * 100}%`
                  }}
                  onClick={() => setSelectedNodeId(node.id)}
                >
                  <div className="node-top-bar">
                    <span className="node-tier-tag">{node.tier}</span>
                    <span className={`node-led-dot ${node.status.toLowerCase()}`} />
                  </div>
                  <div className="node-body">
                    <strong className="node-name">{node.title}</strong>
                    <span className="node-metric">{node.value}</span>
                  </div>
                  <div className="node-status-badge">
                    {node.status === 'CONFIRMED' && <CheckCircle size={10} className="text-emerald" />}
                    {node.status === 'REFUTED' && <XCircle size={10} className="text-rose" />}
                    {node.status === 'GROUNDED' && <Eye size={10} className="text-primary" />}
                    {node.status === 'VERIFIED' && <Check size={10} className="text-sky" />}
                    {node.status === 'PROVEN' && <Sparkles size={10} className="text-amber" />}
                    <span>{node.status}</span>
                  </div>
                  {isSelected && <span className="selected-glow-ring" />}
                </div>
              );
            })}
          </div>

          {/* Active Node Info Strip (Clean & focused, zero unnecessary buttons or clutter) */}
          <div className="node-deep-inspector-drawer">
            <div className="inspector-simple-row">
              <span className="tier-pill">{activeNode.tier}</span>
              <span className="node-status-pill">{activeNode.status}</span>
              <strong className="inspector-simple-title">{activeNode.title}:</strong>
              <span className="inspector-simple-desc">{activeNode.desc}</span>
              {activeNode.formula && (
                <code className="inspector-simple-code">{activeNode.formula}</code>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* 4. OUR 3 DOMAINS SHOWCASE SECTION (Replaces Benchmark) */}
      <section id="saar-domains" className="landing-section-wrapper full-width">
        <div className="domains-showcase-section-card">
          <div className="domains-header-group">
            <div className="luminous-card-badge">
              <Layers size={13} />
              <span>CORE SCIENTIFIC DOMAINS</span>
            </div>
            <h2 className="domains-section-title">
              Three Specialized Reasoning Frontiers
            </h2>
            <p className="domains-section-sub">
              SAAR couples multi-modal sensor inputs with governing physical laws and Bayesian DAG inquiry across specialized scientific verticals.
            </p>
          </div>

          {/* 3 Domain Cards Grid */}
          <div className="domains-tri-grid">
            {/* Domain 1: ToddlerAI */}
            <div className="domain-card-module domain-toddler">
              <div className="domain-card-accent-wire" />
              <div className="domain-card-header">
                <div className="domain-badge-col">
                  <span className="domain-tier-pill sky">DOMAIN 01 • ACTIVE PRODUCTION</span>
                  <h3 className="domain-title">ToddlerAI Biomechanics</h3>
                </div>
                <div className="domain-icon-wrapper sky">
                  <Baby size={24} />
                </div>
              </div>

              <p className="domain-lead-text">
                Non-invasive monocular video joint kinematics and early screening for pediatric motor tone delays.
              </p>

              <div className="domain-specs-box">
                <div className="spec-row">
                  <span className="spec-lbl">Primary Equation:</span>
                  <code className="spec-code">{"θ = arccos( (u · v) / (|u| · |v|) )"}</code>
                </div>
                <div className="spec-row">
                  <span className="spec-lbl">Input Modality:</span>
                  <span className="spec-val">60 FPS 33-Joint Pose Video Stream</span>
                </div>
                <div className="spec-row">
                  <span className="spec-lbl">Causal Objective:</span>
                  <span className="spec-val">Early Spastic Diplegia vs Benign Toe-Walking</span>
                </div>
                <div className="spec-row">
                  <span className="spec-lbl">Diagnostic Precision:</span>
                  <strong className="spec-val text-emerald">92.7% Bayesian Posterior</strong>
                </div>
              </div>

              <div className="domain-card-footer">
                <button
                  type="button"
                  className="btn-launch-domain-studio sky"
                  onClick={() =>
                    onEnterStudio(
                      'Run ToddleAI video pose estimation on toddler walking clip and assess gait asymmetry.',
                      'pediatric',
                      'pediatric_gait_analysis'
                    )
                  }
                >
                  <span>Launch ToddlerAI Console</span>
                  <ArrowRight size={14} />
                </button>
              </div>
            </div>

            {/* Domain 2: Agricultural Science */}
            <div className="domain-card-module domain-agri">
              <div className="domain-card-accent-wire" />
              <div className="domain-card-header">
                <div className="domain-badge-col">
                  <span className="domain-tier-pill emerald">DOMAIN 02 • ACTIVE PRODUCTION</span>
                  <h3 className="domain-title">Agricultural Science</h3>
                </div>
                <div className="domain-icon-wrapper emerald">
                  <Sprout size={24} />
                </div>
              </div>

              <p className="domain-lead-text">
                Precision agronomy engine coupling subterranean Darcy flux soil hydrology with foliar spectral photometry.
              </p>

              <div className="domain-specs-box">
                <div className="spec-row">
                  <span className="spec-lbl">Primary Equation:</span>
                  <code className="spec-code">{"Q = -K · A · (Δh / L)"}</code>
                </div>
                <div className="spec-row">
                  <span className="spec-lbl">Input Modality:</span>
                  <span className="spec-val">NDRE Cameras + Root-Zone TDT Probes</span>
                </div>
                <div className="spec-row">
                  <span className="spec-lbl">Causal Objective:</span>
                  <span className="spec-val">Root Hypoxia & Pythium vs Nitrogen Deficit</span>
                </div>
                <div className="spec-row">
                  <span className="spec-lbl">Diagnostic Precision:</span>
                  <strong className="spec-val text-emerald">94.8% Bayesian Posterior</strong>
                </div>
              </div>

              <div className="domain-card-footer">
                <button
                  type="button"
                  className="btn-launch-domain-studio emerald"
                  onClick={() =>
                    onEnterStudio(
                      'Investigate 30-day tomato crop failure dataset and identify root cause of leaf chlorosis.',
                      'agriculture',
                      'agri_tomato_chlorosis'
                    )
                  }
                >
                  <span>Launch Agronomy Console</span>
                  <ArrowRight size={14} />
                </button>
              </div>
            </div>

            {/* Domain 3: Reserved Space (Under Active Formulation) */}
            <div className="domain-card-module domain-reserved">
              <div className="domain-card-accent-wire reserved-wire" />
              <div className="domain-card-header">
                <div className="domain-badge-col">
                  <span className="domain-tier-pill amber-glow">DOMAIN 03 • R&D FORMULATION</span>
                  <h3 className="domain-title">Frontier Expansion Slot</h3>
                </div>
                <div className="domain-icon-wrapper amber">
                  <Sparkles size={24} />
                </div>
              </div>

              <p className="domain-lead-text">
                Currently under active formulation in our scientific laboratory. Validating differential candidate datasets.
              </p>

              <div className="domain-specs-box reserved-box">
                <div className="spec-row">
                  <span className="spec-lbl">Status:</span>
                  <span className="spec-val text-amber font-bold">Candidate Benchmarks in Review</span>
                </div>
                <div className="spec-row">
                  <span className="spec-lbl">Candidate 1:</span>
                  <span className="spec-val">Geotechnical GPR Cavity Detection</span>
                </div>
                <div className="spec-row">
                  <span className="spec-lbl">Candidate 2:</span>
                  <span className="spec-val">Astrophysics Keplerian Orbit Spectroscopy</span>
                </div>
                <div className="spec-row">
                  <span className="spec-lbl">Mathematical Engine:</span>
                  <code className="spec-code">{"Tensor Decompilation Core (Candidate)"}</code>
                </div>
              </div>

              <div className="domain-card-footer">
                <button
                  type="button"
                  className="btn-launch-domain-studio reserved"
                  onClick={() => onEnterStudio()}
                >
                  <span>Explore Open Sandbox</span>
                  <ArrowRight size={14} />
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 5. Grand Finale CTA Banner */}
      <section className="landing-cta-banner-section">
        <div className="cta-banner-card">
          <div className="cta-brand-tag">
            <Zap size={14} />
            <span>SAAR SCIENTIFIC REASONING STUDIO</span>
          </div>

          <h2 className="cta-banner-title">
            Ready to Experience Autonomous Scientific Reasoning?
          </h2>

          <p className="cta-banner-desc">
            Diagnose pediatric neuromotor gait asymmetries or precision agricultural sensor series with 100% mathematical auditability.
          </p>

          <div className="cta-buttons-wrapper">
            <button
              type="button"
              className="btn-cta-portal-primary"
              onClick={() => onEnterStudio()}
            >
              <Sparkles size={16} />
              <span>Launch Studio Console</span>
              <ArrowRight size={16} />
            </button>

            <button
              type="button"
              className="btn-cta-portal-secondary"
              onClick={() =>
                onEnterStudio(
                  'Run ToddleAI video pose estimation on toddler walking clip and assess gait asymmetry.',
                  'pediatric',
                  'pediatric_gait_analysis'
                )
              }
            >
              <span>Load ToddlerAI Benchmark</span>
            </button>
          </div>
        </div>
      </section>

      {/* 6. Minimal Enterprise Footer */}
      <footer className="landing-footer">
        <div className="footer-content">
          <div className="footer-brand-side">
            <div className="footer-emblem-row">
              <div className="landing-brand-emblem mini">
                <img
                  src={isLightMode ? '/saar-logo-dark.png' : '/saar-logo-white.png'}
                  alt="SAAR Logo"
                  className="brand-logo-img"
                />
              </div>
              <span className="footer-brand-name">SAAR</span>
            </div>
            <p className="footer-tagline">
              Synthetic Auditable Autonomous Reasoner • Multi-Modal Scientific Reasoning Core.
            </p>
          </div>

          <div className="footer-links-group">
            <div className="footer-col">
              <h4>Core Domains</h4>
              <button type="button" onClick={() => onEnterStudio('', 'pediatric')}>ToddlerAI Biomechanics</button>
              <button type="button" onClick={() => onEnterStudio('', 'agriculture')}>Agricultural Science</button>
              <button type="button" onClick={() => onEnterStudio()}>Domain 03 (Expansion Lab)</button>
            </div>

            <div className="footer-col">
              <h4>Platform</h4>
              <a href="#causal-workbench">Causal DAG Engine</a>
              <a href="#saar-domains">3 Core Domains</a>
              <button type="button" onClick={() => onEnterStudio()}>Studio Console</button>
            </div>
          </div>
        </div>

        <div className="footer-bottom-bar">
          <span>© {new Date().getFullYear()} SAAR Research Team. All rights reserved.</span>
          <div className="system-status-indicator">
            <span className="status-dot-pulse" />
            <span>Epistemic Reasoning Core Online</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
