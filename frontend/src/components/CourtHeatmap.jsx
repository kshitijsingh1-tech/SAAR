import React from 'react';
import { Compass, AlertTriangle, Info, Grid } from 'lucide-react';

/**
 * CourtHeatmap (Section 29 & Section 31)
 * Thin renderer for the BWF 9-zone tactical court grid.
 * If court_metrics is unavailable or uncalibrated, renders an explicit
 * fallback state instead of an empty or fake heatmap.
 */
export function CourtHeatmap({
  courtMetrics,
  movementMetrics,
  courtCalibration,
  selectedRegion = null,
  onSelectRegion = null
}) {
  const isCalibrated = Boolean(courtCalibration?.is_calibrated);

  // If court calibration failed, render explicit fallback state (Section 31 requirement)
  if (!isCalibrated) {
    return (
      <div
        className="court-heatmap-uncalibrated-card"
        style={{
          background: '#fefce8',
          border: '1px solid #fef08a',
          borderRadius: '14px',
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          textAlign: 'center',
          minHeight: '260px',
          gap: '12px'
        }}
      >
        <div
          style={{
            width: '48px',
            height: '48px',
            borderRadius: '50%',
            background: '#fef9c3',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#ca8a04'
          }}
        >
          <AlertTriangle size={24} />
        </div>
        <div style={{ fontWeight: '800', fontSize: '1rem', color: '#854d0e' }}>
          Court Not Calibrated for this Video
        </div>
        <p style={{ fontSize: '0.84rem', color: '#713f12', maxWidth: '420px', margin: 0, lineHeight: 1.4 }}>
          {courtCalibration?.uncalibrated_reason ||
            'Court boundaries could not be verified with 4-corner homography. Tactical spatial occupancy heatmaps are strictly disabled to prevent fabricated precision.'}
        </p>
        <div
          style={{
            fontSize: '0.74rem',
            color: '#854d0e',
            background: '#ffffff',
            border: '1px solid #fef08a',
            padding: '4px 10px',
            borderRadius: '6px',
            marginTop: '4px',
            fontWeight: '600'
          }}
        >
          Section 31: Verified Homography Required for Metric Court Spatial Analysis
        </div>
      </div>
    );
  }

  // Extract real occupancy breakdown from backend
  const occupancies = movementMetrics?.region_occupancies || [];
  const occupancyMap = {};
  occupancies.forEach((reg) => {
    if (reg && reg.region_id) {
      occupancyMap[reg.region_id] = reg.occupancy_pct || 0;
    }
  });

  // If region_occupancy dictionary exists on courtMetrics
  if (courtMetrics?.region_occupancy && Object.keys(occupancyMap).length === 0) {
    Object.entries(courtMetrics.region_occupancy).forEach(([k, v]) => {
      occupancyMap[k] = v;
    });
  }

  // 9-zone BWF standard layout grid definition (3 rows x 3 columns)
  const rows = [
    {
      rowLabel: 'Rear Court (Baseline)',
      zones: [
        { id: 'rear_left', label: 'Rear Left (Backhand)' },
        { id: 'rear_center', label: 'Rear Center (Deep)' },
        { id: 'rear_right', label: 'Rear Right (Forehand)' }
      ]
    },
    {
      rowLabel: 'Mid Court (Sides)',
      zones: [
        { id: 'mid_left', label: 'Mid Left (Tramline)' },
        { id: 'mid_center', label: 'Mid Center (T-Base)' },
        { id: 'mid_right', label: 'Mid Right (Tramline)' }
      ]
    },
    {
      rowLabel: 'Front Court (Net)',
      zones: [
        { id: 'front_left', label: 'Front Left (Net Tap)' },
        { id: 'front_center', label: 'Front Center (Net Center)' },
        { id: 'front_right', label: 'Front Right (Hairpin)' }
      ]
    }
  ];

  // Helper for heatmap background opacity based strictly on real backend percentage
  const getCellBg = (pct) => {
    if (!pct || pct <= 0) return '#f8fafc';
    if (pct < 5) return '#f0f9ff';
    if (pct < 15) return '#e0f2fe';
    if (pct < 30) return '#bae6fd';
    return '#7dd3fc';
  };

  const getCellColor = (pct) => {
    if (!pct || pct <= 0) return '#94a3b8';
    if (pct < 5) return '#0369a1';
    if (pct < 15) return '#0284c7';
    if (pct < 30) return '#075985';
    return '#0c4a6e';
  };

  return (
    <div
      className="court-heatmap-container"
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
            <Grid size={16} color="#0284c7" />
          </div>
          <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: '800', color: '#0f172a' }}>
            Tactical Court Heatmap (9-Zone BWF Grid)
          </h4>
        </div>
        <div style={{
          fontSize: '0.75rem',
          color: '#166534',
          background: '#dcfce7',
          padding: '2px 8px',
          borderRadius: '6px',
          fontWeight: '700'
        }}>
          Homography Calibrated
        </div>
      </div>

      {/* Grid Container */}
      <div
        style={{
          display: 'grid',
          gridTemplateRows: 'repeat(3, 1fr)',
          gap: '8px',
          background: '#f8fafc',
          padding: '12px',
          borderRadius: '12px',
          border: '2px solid #e2e8f0',
          position: 'relative'
        }}
      >
        {rows.map((row, rIdx) => (
          <div
            key={rIdx}
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '8px'
            }}
          >
            {row.zones.map((zone) => {
              const pct = occupancyMap[zone.id] || 0;
              const isSelected = selectedRegion === zone.id;

              return (
                <div
                  key={zone.id}
                  onClick={() => onSelectRegion && onSelectRegion(zone.id)}
                  style={{
                    background: isSelected ? '#bae6fd' : getCellBg(pct),
                    border: isSelected ? '2px solid #0284c7' : '1px solid #cbd5e1',
                    borderRadius: '8px',
                    padding: '10px 8px',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: onSelectRegion ? 'pointer' : 'default',
                    transition: 'all 0.15s ease',
                    minHeight: '72px',
                    boxShadow: isSelected ? '0 0 0 3px rgba(2, 132, 199, 0.15)' : 'none'
                  }}
                  title={`${zone.label}: ${pct.toFixed(1)}%`}
                >
                  <div
                    style={{
                      fontSize: '0.72rem',
                      color: '#475569',
                      textAlign: 'center',
                      lineHeight: '1.2',
                      marginBottom: '4px',
                      fontWeight: '600'
                    }}
                  >
                    {zone.label}
                  </div>
                  <div
                    style={{
                      fontSize: '1.15rem',
                      fontWeight: '800',
                      color: getCellColor(pct)
                    }}
                  >
                    {pct.toFixed(1)}%
                  </div>
                </div>
              );
            })}
          </div>
        ))}
      </div>

      {/* Legend */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.75rem', color: '#64748b' }}>
        <span>Low Occupancy (&lt;5%)</span>
        <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
          <div style={{ width: '16px', height: '10px', background: '#f0f9ff', border: '1px solid #cbd5e1', borderRadius: '3px' }} />
          <div style={{ width: '16px', height: '10px', background: '#e0f2fe', border: '1px solid #cbd5e1', borderRadius: '3px' }} />
          <div style={{ width: '16px', height: '10px', background: '#bae6fd', border: '1px solid #cbd5e1', borderRadius: '3px' }} />
          <div style={{ width: '16px', height: '10px', background: '#7dd3fc', border: '1px solid #cbd5e1', borderRadius: '3px' }} />
        </div>
        <span>High Occupancy (&gt;30%)</span>
      </div>
    </div>
  );
}
