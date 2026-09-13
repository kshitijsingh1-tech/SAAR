import React, { useMemo } from 'react';
import { Compass, AlertTriangle, Eye, Layers } from 'lucide-react';

/**
 * MovementTrajectory (Section 29)
 * Thin renderer for player movement path across the court plane.
 * Shows explicit fallback when court calibration is missing.
 */
export function MovementTrajectory({
  movementMetrics,
  courtCalibration,
  shots = [],
  currentTime = 0,
  width = 340,
  height = 240
}) {
  const isCalibrated = Boolean(courtCalibration?.is_calibrated);

  // If uncalibrated, render clean notice per Section 31
  if (!isCalibrated) {
    return (
      <div
        className="trajectory-uncalibrated-card"
        style={{
          background: '#f8fafc',
          border: '1px solid #e2e8f0',
          borderRadius: '16px',
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          textAlign: 'center',
          minHeight: '220px',
          gap: '10px'
        }}
      >
        <Compass size={28} color="#94a3b8" />
        <div style={{ fontWeight: '800', fontSize: '0.95rem', color: '#0f172a' }}>
          Metric Court Trajectory Unavailable
        </div>
        <p style={{ fontSize: '0.82rem', color: '#64748b', margin: 0, maxWidth: '300px', lineHeight: 1.4 }}>
          Physical (X, Y) meter coordinates require verified camera-to-court homography.
        </p>
      </div>
    );
  }

  // Badminton singles court: 5.18m x 13.4m (half-court: 6.7m length)
  // Doubles court: 6.10m x 13.4m
  const courtWidthM = 6.1;
  const courtLengthM = 13.4;

  return (
    <div
      className="movement-trajectory-container"
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
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ background: '#f0f9ff', padding: '6px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Compass size={16} color="#0284c7" />
          </div>
          <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: '800', color: '#0f172a' }}>
            Court Movement Trajectory P(t)
          </h4>
        </div>
        <span style={{
          fontSize: '0.75rem',
          color: '#166534',
          background: '#dcfce7',
          padding: '2px 8px',
          borderRadius: '6px',
          fontWeight: '700'
        }}>
          Calibrated (6.1m × 13.4m)
        </span>
      </div>

      {/* SVG Court Representation */}
      <div
        style={{
          width: '100%',
          height: `${height}px`,
          background: '#0f172a',
          borderRadius: '12px',
          border: '1px solid #e2e8f0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative'
        }}
      >
        <svg
          viewBox={`0 0 ${courtWidthM * 40} ${courtLengthM * 18}`}
          style={{ width: '92%', height: '90%' }}
        >
          {/* Outer Court Boundary */}
          <rect
            x="4"
            y="4"
            width={courtWidthM * 40 - 8}
            height={courtLengthM * 18 - 8}
            fill="none"
            stroke="rgba(56, 189, 248, 0.6)"
            strokeWidth="2"
          />

          {/* Center Net Line */}
          <line
            x1="4"
            y1={(courtLengthM * 18) / 2}
            x2={courtWidthM * 40 - 4}
            y2={(courtLengthM * 18) / 2}
            stroke="#f59e0b"
            strokeWidth="2"
            strokeDasharray="4 2"
          />

          {/* Short Service Lines (1.98m from net) */}
          <line
            x1="4"
            y1={(courtLengthM * 18) / 2 - 1.98 * 18}
            x2={courtWidthM * 40 - 4}
            y2={(courtLengthM * 18) / 2 - 1.98 * 18}
            stroke="rgba(255, 255, 255, 0.25)"
            strokeWidth="1.5"
          />
          <line
            x1="4"
            y1={(courtLengthM * 18) / 2 + 1.98 * 18}
            x2={courtWidthM * 40 - 4}
            y2={(courtLengthM * 18) / 2 + 1.98 * 18}
            stroke="rgba(255, 255, 255, 0.25)"
            strokeWidth="1.5"
          />

          {/* Center Line dividing Left and Right Service Courts */}
          <line
            x1={(courtWidthM * 40) / 2}
            y1="4"
            x2={(courtWidthM * 40) / 2}
            y2={(courtLengthM * 18) / 2 - 1.98 * 18}
            stroke="rgba(255, 255, 255, 0.25)"
            strokeWidth="1.5"
          />
          <line
            x1={(courtWidthM * 40) / 2}
            y1={(courtLengthM * 18) / 2 + 1.98 * 18}
            x2={(courtWidthM * 40) / 2}
            y2={courtLengthM * 18 - 4}
            stroke="rgba(255, 255, 255, 0.25)"
            strokeWidth="1.5"
          />

          {/* Shot Contact Location Markers */}
          {shots.map((s, idx) => {
            if (!s.player_position || s.player_position.length < 2) return null;
            const px = Math.max(8, Math.min(courtWidthM * 40 - 8, s.player_position[0] * 40));
            const py = Math.max(8, Math.min(courtLengthM * 18 - 8, s.player_position[1] * 18));
            return (
              <circle
                key={idx}
                cx={px}
                cy={py}
                r="4.5"
                fill={s.shot_type === 'smash' ? '#f43f5e' : '#10b981'}
                stroke="#ffffff"
                strokeWidth="1.5"
              />
            );
          })}
        </svg>

        {/* Legend Overlay */}
        <div
          style={{
            position: 'absolute',
            bottom: '6px',
            right: '8px',
            fontSize: '0.72rem',
            color: '#94a3b8',
            background: 'rgba(15, 23, 42, 0.85)',
            padding: '2px 8px',
            borderRadius: '4px',
            fontWeight: '600'
          }}
        >
          Net Line (center)
        </div>
      </div>
    </div>
  );
}
