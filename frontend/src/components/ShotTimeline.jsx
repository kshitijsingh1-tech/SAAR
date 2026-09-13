import React from 'react';
import { Clock, Zap, Target, ChevronRight } from 'lucide-react';

/**
 * ShotTimeline (Section 29)
 * Horizontal temporal ribbon of detected contact events with shot type chips,
 * timestamps, duration, and confidence scores.
 */
export function ShotTimeline({
  shots = [],
  activeShotId = null,
  onSelectShot = null,
  onSeek = null,
  duration = 10,
  currentTime = 0
}) {
  if (!shots || shots.length === 0) {
    return (
      <div
        className="shot-timeline-empty"
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
        No discrete contact events detected in this video window.
      </div>
    );
  }

  // Shot type color mapping
  const shotTypeColors = {
    smash: { bg: '#ffe4e6', border: '#f43f5e', text: '#be123c' },
    clear: { bg: '#e0f2fe', border: '#0284c7', text: '#0369a1' },
    drop: { bg: '#fef3c7', border: '#f59e0b', text: '#b45309' },
    drive: { bg: '#f3e8ff', border: '#9333ea', text: '#7e22ce' },
    lift: { bg: '#dcfce7', border: '#16a34a', text: '#15803d' },
    net_shot: { bg: '#ccfbf1', border: '#0d9488', text: '#0f766e' },
    UNKNOWN: { bg: '#f1f5f9', border: '#94a3b8', text: '#475569' }
  };

  const formatSec = (sec) => {
    if (sec === null || sec === undefined || isNaN(sec)) return '0.0s';
    return `${sec.toFixed(2)}s`;
  };

  return (
    <div
      className="shot-timeline-container"
      style={{
        background: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: '16px',
        padding: '16px 20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        boxShadow: '0 2px 10px rgba(0, 0, 0, 0.02)'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ background: '#fffbeb', padding: '6px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Zap size={16} color="#ca8a04" />
          </div>
          <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: '800', color: '#0f172a' }}>
            Detected Stroke Timeline ({shots.length} events)
          </h4>
        </div>
        <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
          Click stroke to seek video
        </span>
      </div>

      {/* Horizontal Scrolling Timeline Ribbon */}
      <div
        style={{
          display: 'flex',
          gap: '10px',
          overflowX: 'auto',
          paddingBottom: '6px'
        }}
      >
        {shots.map((shot, idx) => {
          const typeKey = (shot.shot_type || 'UNKNOWN').toLowerCase();
          const colorObj = shotTypeColors[typeKey] || shotTypeColors.UNKNOWN;
          const isSelected = activeShotId === shot.shot_id || (activeShotId === null && idx === 0);
          const contactTime = shot.contact_time ?? shot.start_time;

          return (
            <div
              key={shot.shot_id || idx}
              onClick={() => {
                if (onSelectShot) onSelectShot(shot);
                if (onSeek && contactTime !== null && contactTime !== undefined) onSeek(contactTime);
              }}
              style={{
                flexShrink: 0,
                background: isSelected ? colorObj.bg : '#f8fafc',
                border: isSelected ? `2px solid ${colorObj.border}` : '1px solid #e2e8f0',
                borderRadius: '10px',
                padding: '10px 12px',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                display: 'flex',
                flexDirection: 'column',
                gap: '4px',
                minWidth: '125px',
                boxShadow: isSelected ? '0 2px 8px rgba(0,0,0,0.06)' : 'none'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '6px' }}>
                <span
                  style={{
                    fontSize: '0.78rem',
                    fontWeight: '800',
                    color: colorObj.text,
                    textTransform: 'uppercase'
                  }}
                >
                  {shot.shot_type}
                </span>
                <span style={{ fontSize: '0.7rem', color: '#94a3b8', fontWeight: '600' }}>
                  #{idx + 1}
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.78rem', color: '#0f172a', fontWeight: '700' }}>
                <Clock size={12} color="#64748b" />
                <span>{formatSec(contactTime)}</span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#64748b' }}>
                <span>Dur: {shot.duration !== undefined ? `${shot.duration.toFixed(2)}s` : '—'}</span>
                <span>Conf: {(shot.confidence * 100).toFixed(0)}%</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
