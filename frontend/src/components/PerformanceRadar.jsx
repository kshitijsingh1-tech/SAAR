import React, { useState } from 'react';
import { PieChart, Activity, Sparkles } from 'lucide-react';

/**
 * PerformanceRadar / PerformancePolarArea
 * Pure, high-fidelity SVG Polar Area chart rendering multi-dimensional performance
 * profiles (Coverage, Speed, Overhead Reach, Shot Variety, Quality, Kinematic Precision)
 * with zero external library dependency.
 */
export function PerformanceRadar({ result }) {
  const [hoveredIndex, setHoveredIndex] = useState(null);

  if (!result) return null;

  const quality = result.quality;
  const court = result.court_metrics;
  const movement = result.movement_metrics;
  const pose = result.pose_metrics;
  const shotMetrics = result.shot_metrics;
  const isCalibrated = Boolean(result.court_calibration?.is_calibrated);

  // Derive standardized 0-100 scores from backend metrics
  const coverageScore = isCalibrated && court?.court_coverage_pct
    ? Math.min(100, Math.round((court.court_coverage_pct / 50.0) * 100))
    : (court?.player_heat_distribution ? 70 : 50);

  const speedScore = isCalibrated && movement?.average_speed_m_s
    ? Math.min(100, Math.round((movement.average_speed_m_s / 2.5) * 100))
    : (movement?.distance_travelled_m ? 75 : 60);

  const elbowAngle = pose?.mean_contact_elbow_deg ?? pose?.elbow_extension_deg;
  const overheadExtensionScore = elbowAngle
    ? Math.min(100, Math.round((elbowAngle / 165.0) * 100))
    : 78;

  const shotTypeCount = Object.keys(shotMetrics?.count_by_shot_type || {}).length;
  const shotVarietyScore = Math.min(100, Math.max(30, shotTypeCount * 22));

  const qualityScore = quality?.confidence === 'HIGH'
    ? 95
    : (quality?.confidence === 'MEDIUM' ? 75 : 55);

  const stabilityScore = quality?.camera_stability_score !== undefined && quality?.camera_stability_score !== null
    ? Math.round(quality.camera_stability_score * 100)
    : 88;

  const slices = [
    { label: 'Court Coverage', score: coverageScore, color: '#0284c7', bg: 'rgba(2, 132, 199, 0.70)', bgHover: 'rgba(2, 132, 199, 0.90)' },
    { label: 'Movement Speed', score: speedScore, color: '#6366f1', bg: 'rgba(99, 102, 241, 0.70)', bgHover: 'rgba(99, 102, 241, 0.90)' },
    { label: 'Overhead Extension', score: overheadExtensionScore, color: '#10b981', bg: 'rgba(16, 185, 129, 0.70)', bgHover: 'rgba(16, 185, 129, 0.90)' },
    { label: 'Shot Variety', score: shotVarietyScore, color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.70)', bgHover: 'rgba(245, 158, 11, 0.90)' },
    { label: 'Capture Quality', score: qualityScore, color: '#ec4899', bg: 'rgba(236, 72, 153, 0.70)', bgHover: 'rgba(236, 72, 153, 0.90)' },
    { label: 'Camera Stability', score: stabilityScore, color: '#14b8a6', bg: 'rgba(20, 184, 166, 0.70)', bgHover: 'rgba(20, 184, 166, 0.90)' }
  ];

  const totalSlices = slices.length;
  const cx = 150;
  const cy = 135;
  const maxR = 100;
  const angleStep = (2 * Math.PI) / totalSlices;
  const startAngleOffset = -Math.PI / 2; // Start from top 12 o'clock

  const rings = [25, 50, 75, 100];

  return (
    <div
      className="performance-polar-container"
      style={{
        background: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: '16px',
        padding: '18px 20px',
        boxShadow: '0 4px 20px -2px rgba(0,0,0,0.04)',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px'
      }}
    >
      <div style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ background: '#f0f9ff', color: '#0284c7', padding: '6px', borderRadius: '8px', display: 'flex' }}>
            <PieChart size={16} />
          </div>
          <div>
            <h4 style={{ margin: 0, fontSize: '0.94rem', fontWeight: '800', color: '#0f172a' }}>
              Performance Polar Profile
            </h4>
            <div style={{ fontSize: '0.70rem', color: '#64748b' }}>
              Multi-axial biomechanical and capture dimension breakdown
            </div>
          </div>
        </div>
      </div>

      <div style={{ position: 'relative', width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        <svg
          viewBox="0 0 300 270"
          style={{ width: '100%', maxWidth: '300px', height: '230px', overflow: 'visible' }}
        >
          {/* Concentric Grid Rings */}
          {rings.map((ring) => {
            const r = (ring / 100) * maxR;
            return (
              <g key={ring}>
                <circle
                  cx={cx}
                  cy={cy}
                  r={r}
                  fill="none"
                  stroke="#e2e8f0"
                  strokeWidth="1"
                  strokeDasharray={ring === 100 ? 'none' : '3 3'}
                />
                <text
                  x={cx + 3}
                  y={cy - r + 9}
                  fill="#94a3b8"
                  fontSize="8"
                  fontFamily="monospace"
                  fontWeight="600"
                >
                  {ring}
                </text>
              </g>
            );
          })}

          {/* Radial Spokes */}
          {slices.map((_, i) => {
            const angle = startAngleOffset + i * angleStep;
            const x2 = cx + maxR * Math.cos(angle);
            const y2 = cy + maxR * Math.sin(angle);
            return (
              <line
                key={i}
                x1={cx}
                y1={cy}
                x2={x2}
                y2={y2}
                stroke="#e2e8f0"
                strokeWidth="1"
              />
            );
          })}

          {/* Polar Area Wedges */}
          {slices.map((slice, i) => {
            const r = (Math.max(8, slice.score) / 100) * maxR;
            const a1 = startAngleOffset + i * angleStep;
            const a2 = a1 + angleStep;
            const x1 = cx + r * Math.cos(a1);
            const y1 = cy + r * Math.sin(a1);
            const x2 = cx + r * Math.cos(a2);
            const y2 = cy + r * Math.sin(a2);

            const isHovered = hoveredIndex === i;
            const pathData = `M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 0 1 ${x2} ${y2} Z`;

            return (
              <path
                key={i}
                d={pathData}
                fill={isHovered ? slice.bgHover : slice.bg}
                stroke={slice.color}
                strokeWidth={isHovered ? 2.5 : 1.5}
                style={{
                  cursor: 'pointer',
                  transition: 'all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1)',
                  filter: isHovered ? 'drop-shadow(0 4px 10px rgba(0,0,0,0.18))' : 'none'
                }}
                onMouseEnter={() => setHoveredIndex(i)}
                onMouseLeave={() => setHoveredIndex(null)}
              />
            );
          })}

          {/* Center Pivot Point */}
          <circle cx={cx} cy={cy} r="3" fill="#64748b" />

          {/* Dynamic Tooltip */}
          {hoveredIndex !== null && (
            <g transform={`translate(${cx}, ${cy - maxR - 14})`}>
              <rect
                x="-65"
                y="-18"
                width="130"
                height="22"
                rx="6"
                fill="rgba(15, 23, 42, 0.94)"
                stroke="#38bdf8"
                strokeWidth="1"
              />
              <text
                x="0"
                y="-3"
                textAnchor="middle"
                fill="#ffffff"
                fontSize="10"
                fontWeight="700"
                fontFamily="system-ui, sans-serif"
              >
                {slices[hoveredIndex].label}: {slices[hoveredIndex].score}/100
              </text>
            </g>
          )}
        </svg>
      </div>

      {/* Legend Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: '6px 8px',
        paddingTop: '6px',
        borderTop: '1px solid #f1f5f9'
      }}>
        {slices.map((s, idx) => {
          const isHovered = hoveredIndex === idx;
          return (
            <div
              key={idx}
              onMouseEnter={() => setHoveredIndex(idx)}
              onMouseLeave={() => setHoveredIndex(null)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '3px 6px',
                borderRadius: '6px',
                background: isHovered ? '#f1f5f9' : 'transparent',
                cursor: 'pointer',
                transition: 'background 0.15s ease'
              }}
            >
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '2px',
                background: s.color,
                flexShrink: 0
              }} />
              <div style={{
                fontSize: '0.68rem',
                fontWeight: isHovered ? 700 : 600,
                color: isHovered ? '#0f172a' : '#475569',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis'
              }}>
                {s.label} ({s.score})
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export const PerformancePolarArea = PerformanceRadar;
