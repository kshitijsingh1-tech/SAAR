import React, { useState, useEffect } from 'react';
import {
  Check, AlertCircle, HelpCircle, Activity, TrendingUp, TrendingDown, ShieldCheck,
  BarChart2, ScatterChart, PieChart, Info, X, Sparkles, Filter
} from 'lucide-react';
import { PlotlyGraphViewer } from './PlotlyGraphViewer';

export function SaarFindingsPanel({
  saarData,
  selectedRelationship,
  selectedChartType,
  onSelectRelationship
}) {
  const [activeChart, setActiveChart] = useState(selectedChartType || 'histogram');

  // Sync activeChart whenever selectedChartType changes from external click
  useEffect(() => {
    if (selectedChartType) {
      setActiveChart(selectedChartType);
    }
  }, [selectedChartType, selectedRelationship]);

  // Fallback saarData if backend data is initializing
  const activeSaarData = saarData || {
    confidence: 0.92,
    concepts: [
      {
        name: 'Multivariate Correlation & System Analytics',
        description: 'System perception active. Interactive Plotly.js charts display field distributions, covariance, and causal linkages.'
      }
    ],
    relationships: [
      { source_feature: 'Soil Moisture', target_feature: 'Crop Chlorosis', strength: 0.88, direction: 'positive' },
      { source_feature: 'Subsurface Void', target_feature: 'GPR Anomaly', strength: 0.94, direction: 'positive' },
      { source_feature: 'Temperature', target_feature: 'Evapotranspiration', strength: -0.76, direction: 'negative' },
      { source_feature: 'Pavement Stress', target_feature: 'Deflection Index', strength: 0.82, direction: 'positive' }
    ]
  };

  const confidencePct = Math.round((activeSaarData.confidence || 0) * 100);
  const topConcept = activeSaarData.concepts && activeSaarData.concepts.length > 0 ? activeSaarData.concepts[0] : null;
  const relationships = activeSaarData.relationships || [];
  const questions = activeSaarData.open_questions || [];

  // Active focused pair if user clicked from chat or table
  const activePair = selectedRelationship || (relationships.length > 0 ? relationships[0] : null);

  // Generate dynamic sample points for Scatter/Dot plot
  const scatterPoints = relationships.length > 0
    ? relationships.slice(0, 10).map((rel, i) => {
        const isMatched =
          activePair &&
          ((rel.source_feature === activePair.source_feature && rel.target_feature === activePair.target_feature) ||
            (rel.source_feature === activePair.target_feature && rel.target_feature === activePair.source_feature));

        return {
          x: (i + 1) * 9 + 8,
          y: Math.min(92, Math.max(8, Math.abs(rel.strength || 0.5) * 85 + (i % 2 === 0 ? 4 : -4))),
          label: `${rel.source_feature} ↔ ${rel.target_feature}`,
          val: rel.strength,
          source: rel.source_feature,
          target: rel.target_feature,
          isMatched
        };
      })
    : [
        { x: 15, y: 35, label: 'Feature A ↔ B', val: 0.62, isMatched: false },
        { x: 35, y: 75, label: 'Feature C ↔ D', val: 0.88, isMatched: true },
        { x: 55, y: 45, label: 'Feature E ↔ F', val: 0.51, isMatched: false },
        { x: 75, y: 85, label: 'Feature G ↔ H', val: 0.94, isMatched: false }
      ];

  // Dynamic Histogram Bins
  const histogramBins = activePair
    ? [
        { bin: `0.0 - 0.25 (Low Baseline)`, count: 2, height: 28, label: 'Background Noise' },
        { bin: `0.25 - 0.50 (Moderate)`, count: 5, height: 50, label: 'Secondary Coupling' },
        {
          bin: `0.50 - 0.75 (Strong)`,
          count: 8,
          height: 75,
          label: 'Coupled Variables',
          isTarget: Math.abs(activePair.strength || 0) < 0.75 && Math.abs(activePair.strength || 0) >= 0.5
        },
        {
          bin: `0.75 - 1.0 (Direct Coupling)`,
          count: 12,
          height: 95,
          label: `${activePair.source_feature} ↔ ${activePair.target_feature}`,
          isTarget: Math.abs(activePair.strength || 0) >= 0.75
        }
      ]
    : [
        { bin: '0.0 - 0.3 (Weak)', count: 1, height: 25 },
        { bin: '0.3 - 0.6 (Moderate)', count: 3, height: 65 },
        { bin: '0.6 - 0.8 (Strong)', count: 4, height: 85 },
        { bin: '0.8 - 1.0 (Very High)', count: 2, height: 50 }
      ];

  return (
    <section className="panel findings">
      <div className="panel-title">
        <Check size={12} />
        <span>Analysis &amp; System Perception Findings</span>
        <span className="finding-confidence">
          <ShieldCheck size={13} style={{ display: 'inline', marginRight: 4 }} />
          {confidencePct}% Confidence
        </span>
      </div>

      <div className="finding-body">
        {/* Active Focus Spotlight Banner if a field pair was clicked */}
        {selectedRelationship && (
          <div className="selected-pair-spotlight">
            <div className="spotlight-header">
              <div className="spotlight-title">
                <Sparkles size={13} />
                <span>Active Focused Relationship:</span>
                <strong>
                  {selectedRelationship.source_feature} ↔ {selectedRelationship.target_feature}
                </strong>
              </div>
              <span className={`pair-pill ${selectedRelationship.direction}`}>
                {selectedRelationship.direction === 'negative' ? <TrendingDown size={11} /> : <TrendingUp size={11} />}
                r = {selectedRelationship.strength?.toFixed(2)} ({selectedRelationship.direction})
              </span>
            </div>
            <p className="spotlight-desc">
              Visualizing the statistical distribution, covariance, and causal linkage between{' '}
              <strong>{selectedRelationship.source_feature}</strong> and{' '}
              <strong>{selectedRelationship.target_feature}</strong>.
            </p>
          </div>
        )}

        <h2>{topConcept ? topConcept.name : 'Dataset & Question Analyzed'}</h2>
        <p>{topConcept ? topConcept.description : 'Perception complete. Statistical correlations and causal linkages discovered.'}</p>

        {/* Action Buttons to Visualize Parts of Analysis via Plotly.js */}
        <div className="chart-vis-buttons-row">
          <span className="vis-label"><BarChart2 size={12} /> Interactive Plotly.js Field Analytics:</span>
          <button
            className={`vis-btn ${activeChart === 'histogram' ? 'active' : ''}`}
            onClick={() => setActiveChart(activeChart === 'histogram' ? null : 'histogram')}
          >
            <BarChart2 size={12} /> Plotly Histogram
          </button>
          <button
            className={`vis-btn ${activeChart === 'dot' || activeChart === 'scatter' ? 'active' : ''}`}
            onClick={() => setActiveChart(activeChart === 'dot' || activeChart === 'scatter' ? null : 'dot')}
          >
            <ScatterChart size={12} /> Plotly Scatter
          </button>
          <button
            className={`vis-btn ${activeChart === 'bar' ? 'active' : ''}`}
            onClick={() => setActiveChart(activeChart === 'bar' ? null : 'bar')}
          >
            <PieChart size={12} /> Plotly Bar Graph
          </button>
          <button
            className={`vis-btn ${activeChart === 'surface3d' ? 'active' : ''}`}
            onClick={() => setActiveChart(activeChart === 'surface3d' ? null : 'surface3d')}
          >
            <Activity size={12} /> Plotly 3D Surface
          </button>
        </div>

        {/* Dynamic Plotly Chart Overlay Card */}
        {activeChart && (
          <div className="chart-visualization-card">
            <div className="card-header">
              <strong>
                {activeChart === 'histogram' && (
                  <span>
                    📊 Plotly Correlation Histogram:{' '}
                    {activePair ? `${activePair.source_feature} ↔ ${activePair.target_feature}` : 'All Variables'}
                  </span>
                )}
                {(activeChart === 'dot' || activeChart === 'scatter') && (
                  <span>
                    🔴 Plotly Scatter &amp; Covariance Canvas:{' '}
                    {activePair ? `${activePair.source_feature} ↔ ${activePair.target_feature}` : 'Discovered Couplings'}
                  </span>
                )}
                {activeChart === 'bar' && (
                  <span>
                    📈 Plotly Feature Correlation Ranking:{' '}
                    {activePair ? `Focused on ${activePair.source_feature}` : 'All Discovered Links'}
                  </span>
                )}
                {activeChart === 'surface3d' && (
                  <span>
                    🌌 Plotly 3D Causal Probability Density Surface
                  </span>
                )}
              </strong>
              <button onClick={() => setActiveChart(null)} title="Close Chart"><X size={13} /></button>
            </div>

            <PlotlyGraphViewer
              chartType={activeChart}
              saarData={activeSaarData}
              selectedRelationship={selectedRelationship}
              onSelectRelationship={onSelectRelationship}
              height={290}
            />
          </div>
        )}

        {/* Top Relationships List with interactive click filters */}
        {relationships.length > 0 && (
          <div className="saar-rel-box">
            <h4 className="saar-subtitle">
              <Activity size={12} /> Discovered Statistical Relationships (Click any pair to inspect):
            </h4>
            <div className="saar-rel-grid">
              {relationships.slice(0, 6).map((rel, idx) => {
                const isSelected =
                  activePair &&
                  rel.source_feature === activePair.source_feature &&
                  rel.target_feature === activePair.target_feature;

                return (
                  <button
                    className={`saar-rel-card clickable ${isSelected ? 'active-focus' : ''}`}
                    key={idx}
                    onClick={() => onSelectRelationship && onSelectRelationship(rel, 'histogram')}
                    style={{ textAlign: 'left', cursor: 'pointer' }}
                  >
                    <span className="rel-pair">
                      {isSelected && <Sparkles size={11} style={{ display: 'inline', marginRight: 4, color: 'var(--primary)' }} />}
                      {rel.source_feature} ↔ {rel.target_feature}
                    </span>
                    <span className={`rel-strength ${rel.direction}`}>
                      r = {rel.strength?.toFixed(2)} ({rel.direction})
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Open Questions generated by Uncertainty Engine */}
        {questions.length > 0 && (
          <div className="saar-questions-box">
            <h4 className="saar-subtitle"><HelpCircle size={12} /> Targeted Questions (Uncertainty Engine)</h4>
            <ul className="saar-question-list">
              {questions.slice(0, 3).map((q, idx) => (
                <li key={idx} className={`q-priority-${q.priority}`}>
                  <span className="q-badge">{q.priority}</span>
                  <span>{q.question}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="finding-actions">
          <button className="primary-action">
            View Evidence Chain ({activeSaarData.evidence_chain?.length || 0})
          </button>
          <button>Iteration #{activeSaarData.iteration || 1}</button>
        </div>
      </div>
    </section>
  );
}
