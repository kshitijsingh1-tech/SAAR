import React from 'react';
import { ShieldCheck, AlertTriangle, AlertCircle, Camera, CheckCircle2, Info, Compass, Sparkles, Zap } from 'lucide-react';

/**
 * BadmintonQualityBanner (Section 29 & Section 30)
 * Thin renderer for capture quality assessment, camera stability, view angle,
 * and calibration notices. When an upgrade/enhancement is applied, it cleanly displays
 * High Quality Capture, 100% stability, and Normalized Perspective with all text below removed.
 */
export function BadmintonQualityBanner({ quality, courtCalibration, playerMetadata, enhancement }) {
  if (!quality) return null;

  const isUpgraded = Boolean(enhancement?.is_enhanced || quality.is_upgraded);
  const confidence = isUpgraded ? 'HIGH' : (quality.confidence || 'UNKNOWN');
  const issues = isUpgraded ? [] : (quality.issues || []);
  const cameraView = isUpgraded ? 'rear or_diagonal_view' : (quality.camera_view || 'rear or_diagonal_view');
  const stabilityScore = isUpgraded ? 1.0 : (quality.camera_stability_score ?? 1.0);
  const isCalibrated = Boolean(courtCalibration?.is_calibrated);

  // Confidence color styling matching theme
  const confidenceStyles = {
    HIGH: {
      bg: '#f0fdf4',
      border: '#bbf7d0',
      color: '#166534',
      badgeBg: '#dcfce7',
      icon: <CheckCircle2 size={18} color="#16a34a" />
    },
    MEDIUM: {
      bg: '#fefce8',
      border: '#fef08a',
      color: '#854d0e',
      badgeBg: '#fef9c3',
      icon: <Info size={18} color="#ca8a04" />
    },
    LOW: {
      bg: '#fef2f2',
      border: '#fecaca',
      color: '#991b1b',
      badgeBg: '#fee2e2',
      icon: <AlertTriangle size={18} color="#dc2626" />
    },
    REJECT: {
      bg: '#fef2f2',
      border: '#fecaca',
      color: '#991b1b',
      badgeBg: '#fee2e2',
      icon: <AlertCircle size={18} color="#dc2626" />
    }
  };

  const style = confidenceStyles[confidence] || confidenceStyles.HIGH;

  return (
    <div
      className="badminton-quality-banner"
      style={{
        background: style.bg,
        border: `1px solid ${style.border}`,
        borderRadius: '14px',
        padding: '14px 20px',
        marginBottom: '20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
        boxShadow: '0 2px 10px rgba(0, 0, 0, 0.02)'
      }}
    >
      {/* Top Header Row */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {style.icon}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <span style={{ fontWeight: '700', fontSize: '0.95rem', color: '#0f172a' }}>
              Recording Quality:
            </span>
            <span
              style={{
                fontSize: '0.8rem',
                fontWeight: '700',
                padding: '2px 8px',
                borderRadius: '6px',
                background: style.badgeBg,
                color: style.color
              }}
            >
              {confidence === 'HIGH' ? 'High Quality Capture' : (confidence === 'MEDIUM' ? 'Acceptable Video' : 'Partially Degraded Video')}
            </span>
            <span
              style={{
                fontSize: '0.78rem',
                padding: '2px 8px',
                borderRadius: '6px',
                background: '#ffffff',
                border: '1px solid #cbd5e1',
                color: '#475569',
                fontWeight: '600'
              }}
            >
              View: {cameraView}
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', fontSize: '0.82rem', color: '#64748b' }}>
          <span>
            Stability Score: <strong style={{ color: '#0f172a' }}>{isUpgraded ? '100%' : `${(stabilityScore * 100).toFixed(0)}%`}</strong>
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <Compass size={14} color={isCalibrated ? '#16a34a' : '#ca8a04'} />
            Court Space:{' '}
            <strong style={{ color: isCalibrated ? '#166534' : '#854d0e' }}>
              {isCalibrated ? 'Calibrated (Metric 3D)' : 'Normalized Perspective'}
            </strong>
          </span>
        </div>
      </div>

      {/* If upgraded, remove and suppress all text, warnings, and bullet points below it */}
      {!isUpgraded && (
        <>
          {/* Calibration Notice Warning when uncalibrated */}
          {!isCalibrated && courtCalibration?.uncalibrated_reason && (
            <div
              style={{
                fontSize: '0.82rem',
                color: '#854d0e',
                background: '#fffbeb',
                borderLeft: '3px solid #f59e0b',
                padding: '8px 12px',
                borderRadius: '6px'
              }}
            >
              <strong>Calibration Notice:</strong> {courtCalibration.uncalibrated_reason}. Normalized court space active with zero fabricated distance estimates.
            </div>
          )}

          {/* Issues list if present */}
          {issues.length > 0 && (
            <div style={{ fontSize: '0.8rem', color: '#64748b', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {issues.map((iss, idx) => (
                <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ color: style.color, fontWeight: 'bold' }}>•</span>
                  <span>{iss}</span>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

