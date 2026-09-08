import React, { useState, useRef } from 'react';
import {
  Zap, Sprout, Construction, Orbit, ArrowRight, UploadCloud,
  FileSpreadsheet, Image as ImageIcon, Sparkles, CheckCircle2,
  ShieldAlert, Activity, GitFork, BookOpen, Layers
} from 'lucide-react';

export function LandingHero({ onStartQuery, onStartPreset, onUploadFile, onNavigateTab }) {
  const [searchQuery, setSearchQuery] = useState('');
  const fileInputRef = useRef(null);

  const scenarios = [
    {
      id: 'tomato_crop',
      domain: 'agriculture',
      title: 'Tomato Crop 30-Day Failure',
      subtitle: 'Nutrient Leaching & Chlorosis',
      description: '30-day longitudinal sensor log showing acute soil acidification, moisture saturation, and sudden leaf chlorosis onset.',
      badge: 'Dataset Ready (XLSX/CSV)',
      icon: <Sprout className="text-emerald" size={20} />,
      metrics: ['30 Observations', '14 Sensor Fields', 'High Leaching Correlation'],
      query: 'Investigate the 30-day tomato crop failure dataset and identify the root cause of leaf chlorosis and yield collapse.'
    },
    {
      id: 'infra_damaged_road',
      domain: 'infrastructure',
      title: 'Highway Pavement Void Cavity',
      subtitle: 'Surface Cracking & Sub-base Void',
      description: 'Multi-modal civil inspection combining road surface cracking imagery with Ground Penetrating Radar (GPR) void detection.',
      badge: 'VLM + GPR Tool Pipeline',
      icon: <Construction className="text-amber" size={20} />,
      metrics: ['Visual Surface Cracks', 'GPR 1.8m Void', 'Compaction Failure'],
      query: 'Run civil infrastructure investigation on highway cracking and determine if sub-surface voids threaten structural integrity.'
    },
    {
      id: 'astronomy_transit',
      domain: 'astronomy',
      title: 'Exoplanet Transit Spectroscopy',
      subtitle: 'Lightcurve Dip & Flare Noise',
      description: 'Multi-band stellar flux lightcurve with periodic transit depth dips and anomalous secondary spectroscopic peaks.',
      badge: 'Spectroscopy + Keplerian Tool',
      icon: <Orbit className="text-purple" size={20} />,
      metrics: ['0.82% Flux Dip', 'Flare Anomaly Isolated', 'Confirmed Exoplanet'],
      query: 'Analyze stellar transit lightcurve to separate stellar flare contamination from confirmed exoplanetary atmosphere absorption.'
    }
  ];

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      onStartQuery(searchQuery.trim());
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file && onUploadFile) {
      onUploadFile(file);
    }
  };

  return (
    <div className="landing-hero-container">
      {/* Background Decorative Glows */}
      <div className="hero-glow-blue" />
      <div className="hero-glow-emerald" />

      {/* Floating Badge */}
      <div className="hero-badge animate-levitate-slow">
        <span className="badge-sparkle"><Sparkles size={13} /></span>
        <span>Iterative Evidence-Driven Scientific Reasoning Engine</span>
        <span className="badge-pill">v1.0 Ready</span>
      </div>

      {/* Hero Headline */}
      <h1 className="hero-title">
        Autonomous Scientific Reasoning <br />
        <span className="gradient-text">Grounded in Empirical Evidence</span>
      </h1>

      {/* Subtitle */}
      <p className="hero-subtitle">
        Moving beyond single-pass black-box VLMs. Saar decouples visual perception,
        structured tabular telemetry, and causal graph reasoning—formulating testable hypotheses
        and updating belief states through human-in-the-loop inquiries.
      </p>

      {/* Interactive Main Search Bar & Quick Dropzone */}
      <div className="hero-search-wrapper">
        <form className="hero-search-form" onSubmit={handleSearchSubmit}>
          <div className="search-input-group">
            <Sparkles size={18} className="search-icon" />
            <input
              type="text"
              className="hero-search-input"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Ask a scientific inquiry or start an investigation (e.g., 'Why did leaf chlorosis surge on Day 18?')..."
            />
          </div>

          <div className="search-buttons-group">
            <input
              type="file"
              ref={fileInputRef}
              style={{ display: 'none' }}
              accept=".csv,.xlsx,.xls,.png,.jpg,.jpeg"
              onChange={handleFileChange}
            />
            <button
              type="button"
              className="btn-hero-attach"
              onClick={() => fileInputRef.current?.click()}
              title="Upload CSV / XLSX dataset or image"
            >
              <UploadCloud size={16} />
              <span>Attach Dataset</span>
            </button>

            <button type="submit" className="btn-hero-submit">
              <span>Investigate</span>
              <ArrowRight size={16} />
            </button>
          </div>
        </form>

        {/* Quick Suggestion Chips */}
        <div className="hero-quick-chips">
          <span className="chips-label">Quick Prompts:</span>
          <button
            className="quick-chip"
            onClick={() => onStartQuery('Analyze the causal mechanism between soil pH, moisture, and iron deficiency chlorosis.')}
          >
            🌱 Soil pH &amp; Chlorosis Causality
          </button>
          <button
            className="quick-chip"
            onClick={() => onStartQuery('Run sub-surface void detection and determine highway pavement failure risk.')}
          >
            🏗️ GPR Void Cavity Analysis
          </button>
          <button
            className="quick-chip"
            onClick={() => onStartQuery('Evaluate exoplanet transit depth against stellar flare contamination.')}
          >
            🔭 Exoplanet Transit Separation
          </button>
        </div>
      </div>

      {/* Preloaded Scenario Cards */}
      <div className="hero-scenarios-section">
        <div className="section-header-compact">
          <div className="section-eyebrow">
            <Activity size={13} /> READY-TO-RUN BENCHMARK SCENARIOS
          </div>
          <h2>Select a Guided Investigation</h2>
        </div>

        <div className="scenario-cards-grid">
          {scenarios.map((sc) => (
            <div
              key={sc.id}
              className="scenario-card"
              onClick={() => onStartPreset(sc.domain, sc.id, sc.query)}
              role="button"
              tabIndex={0}
            >
              <div className="scenario-card-top">
                <div className="scenario-icon-wrapper">
                  {sc.icon}
                </div>
                <span className="scenario-badge">{sc.badge}</span>
              </div>

              <h3 className="scenario-title">{sc.title}</h3>
              <div className="scenario-subtitle">{sc.subtitle}</div>
              <p className="scenario-desc">{sc.description}</p>

              <div className="scenario-metrics">
                {sc.metrics.map((m, idx) => (
                  <span key={idx} className="metric-pill">
                    <CheckCircle2 size={11} className="text-emerald" /> {m}
                  </span>
                ))}
              </div>

              <div className="scenario-card-footer">
                <span className="launch-text">Launch Investigation</span>
                <ArrowRight size={14} className="launch-arrow" />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 4 Architectural Pillars Grid */}
      <div className="hero-pillars-section">
        <div className="pillar-card">
          <div className="pillar-icon text-primary"><Layers size={20} /></div>
          <h4>Decoupled Multi-Agent Loop</h4>
          <p>Separates raw visual feature perception from causal graph management and specialized analytical tools (GPR, Hydrology).</p>
        </div>

        <div className="pillar-card">
          <div className="pillar-icon text-emerald"><Activity size={20} /></div>
          <h4>Iterative Belief Updating</h4>
          <p>Mathematical confidence scores ($0-100\%$) and topological graph uncertainty updated dynamically as new evidence surfaces.</p>
        </div>

        <div className="pillar-card">
          <div className="pillar-icon text-amber"><GitFork size={20} /></div>
          <h4>Human-in-the-Loop Inquiry</h4>
          <p>Formulates targeted, high-information-gain questions for human investigators to resolve critical causal ambiguities.</p>
        </div>

        <div className="pillar-card">
          <div className="pillar-icon text-purple"><BookOpen size={20} /></div>
          <h4>Empirical Literature RAG</h4>
          <p>Every hypothesis and finding is grounded in domain peer-reviewed agronomy, structural engineering, and astrophysics knowledge bases.</p>
        </div>
      </div>
    </div>
  );
}
