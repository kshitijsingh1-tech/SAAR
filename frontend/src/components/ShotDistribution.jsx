import React from 'react';
import { BarChart3, PieChart, Layers, Info } from 'lucide-react';

/**
 * ShotDistribution (Section 29)
 * Direct thin renderer of shot_metrics.count_by_shot_type and
 * percentage_by_shot_type. Prominently includes the UNKNOWN bucket
 * per Phase 8 specification.
 */
export function ShotDistribution({ shotMetrics }) {
  if (!shotMetrics || !shotMetrics.count_by_shot_type || Object.keys(shotMetrics.count_by_shot_type).length === 0) {
    return (
      <div
        className="shot-distribution-empty"
        style={{
          background: '#f8fafc',
          border: '1px solid #e2e8f0',
          borderRadius: '12px',
          padding: '16px',
          textAlign: 'center',
          fontSize: '0.84rem',
          color: '#64748b'
        }}
      >
        No shot classification distribution available.
      </div>
    );
  }

  const counts = shotMetrics.count_by_shot_type || {};
  const percentages = shotMetrics.percentage_by_shot_type || {};
  const totalShots = shotMetrics.total_shots || Object.values(counts).reduce((a, b) => a + b, 0);
  const avgDuration = shotMetrics.average_duration_s ?? shotMetrics.average_duration_seconds;

  // Shot color palette
  const getBarColor = (type) => {
    const t = type.toLowerCase();
    if (t === 'smash') return '#f43f5e';
    if (t === 'clear') return '#0284c7';
    if (t === 'drop') return '#f59e0b';
    if (t === 'drive') return '#9333ea';
    if (t === 'lift') return '#16a34a';
    if (t === 'net_shot') return '#0d9488';
    return '#94a3b8'; // UNKNOWN
  };

  return (
    <div
      className="shot-distribution-container"
      style={{
        background: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: '16px',
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
        boxShadow: '0 2px 10px rgba(0, 0, 0, 0.02)'
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ background: '#f0f9ff', padding: '6px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <BarChart3 size={16} color="#0284c7" />
          </div>
          <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: '800', color: '#0f172a' }}>
            Stroke Classification Distribution
          </h4>
        </div>
        <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
          Total: <strong style={{ color: '#0f172a' }}>{totalShots}</strong> shots
          {avgDuration !== undefined && avgDuration !== null && (
            <span> (Avg: <strong style={{ color: '#0284c7' }}>{avgDuration.toFixed(2)}s</strong>)</span>
          )}
        </div>
      </div>

      {/* Distribution Bars */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {Object.entries(counts).map(([shotType, count]) => {
          const pct = percentages[shotType] !== undefined
            ? percentages[shotType]
            : (totalShots > 0 ? (count / totalShots) * 100 : 0);
          const color = getBarColor(shotType);
          const isUnknown = shotType.toUpperCase() === 'UNKNOWN';

          return (
            <div key={shotType} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                <span
                  style={{
                    fontWeight: isUnknown ? '600' : '700',
                    color: isUnknown ? '#64748b' : '#0f172a',
                    textTransform: 'uppercase',
                    fontSize: '0.78rem'
                  }}
                >
                  {shotType} {isUnknown && <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>(unclassified/reduced evidence)</span>}
                </span>
                <span style={{ color: '#64748b', fontSize: '0.78rem', fontWeight: '600' }}>
                  {count} ({pct.toFixed(1)}%)
                </span>
              </div>

              {/* Progress bar */}
              <div
                style={{
                  width: '100%',
                  height: '8px',
                  background: '#f1f5f9',
                  borderRadius: '4px',
                  overflow: 'hidden'
                }}
              >
                <div
                  style={{
                    width: `${Math.min(100, Math.max(0, pct))}%`,
                    height: '100%',
                    background: color,
                    borderRadius: '4px',
                    transition: 'width 0.3s ease'
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <div style={{ fontSize: '0.72rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '5px', marginTop: '2px' }}>
        <Info size={13} />
        <span>Grounded in Section 17 contact timing and Section 16 UNKNOWN classification gating.</span>
      </div>
    </div>
  );
}
