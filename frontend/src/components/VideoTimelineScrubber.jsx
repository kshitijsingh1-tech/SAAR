import React from 'react';
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Film,
  Zap,
  Clock
} from 'lucide-react';

/**
 * VideoTimelineScrubber
 * Interactive temporal video navigation with keyframe markers,
 * play/pause control, and timestamp scrubbing styled in clean theme matching SAAR.
 */
export const VideoTimelineScrubber = ({
  currentTime = 0,
  duration = 10,
  isPlaying = false,
  onPlayToggle,
  onSeek,
  keyframes = [],
  activeKeyframeIndex = 0,
  onSelectKeyframe,
  fps = 30.0
}) => {
  const formatTime = (seconds) => {
    if (isNaN(seconds) || seconds === null) return '00:00.0';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const millis = Math.floor((seconds % 1) * 10);
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}.${millis}`;
  };

  const progressPercent = duration > 0 ? Math.min(100, Math.max(0, (currentTime / duration) * 100)) : 0;

  const handleSliderChange = (e) => {
    const val = parseFloat(e.target.value);
    if (onSeek) onSeek(val);
  };

  const stepFrame = (direction) => {
    const delta = (1 / (fps || 30.0)) * direction;
    const newTime = Math.max(0, Math.min(duration, currentTime + delta));
    if (onSeek) onSeek(newTime);
  };

  return (
    <div
      className="video-timeline-scrubber-container"
      style={{
        background: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: '12px',
        padding: '10px 14px',
        marginTop: '0.6rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.6rem',
        boxShadow: '0 2px 10px rgba(0, 0, 0, 0.03)'
      }}
    >
      {/* 1. Header Row: Mode Badge, FPS Tracker, and Live Time Display */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.74rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              padding: '2px 8px',
              borderRadius: '6px',
              background: '#e0f2fe',
              border: '1px solid #bae6fd',
              color: '#0284c7',
              fontWeight: 800,
              fontSize: '0.70rem',
              letterSpacing: '0.03em'
            }}
          >
            <Film size={12} />
            TEMPORAL VIDEO SCRUBBER
          </span>

          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '3px',
              padding: '2px 6px',
              borderRadius: '6px',
              background: '#f1f5f9',
              border: '1px solid #e2e8f0',
              color: '#475569',
              fontSize: '0.68rem',
              fontWeight: 600,
              fontFamily: 'monospace'
            }}
          >
            <Zap size={11} color="#eab308" />
            {fps.toFixed(1)} FPS
          </span>
        </div>

        {/* Timestamp */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontFamily: 'monospace', fontWeight: 700, fontSize: '0.78rem' }}>
          <Clock size={12} color="#64748b" />
          <span style={{ color: '#0284c7' }}>{formatTime(currentTime)}</span>
          <span style={{ color: '#94a3b8' }}>/</span>
          <span style={{ color: '#64748b' }}>{formatTime(duration)}</span>
        </div>
      </div>

      {/* 2. Interactive Scrubber Track with Keyframe Markers */}
      <div style={{ position: 'relative', width: '100%', height: '20px', display: 'flex', alignItems: 'center' }}>
        {/* Progress Bar Background */}
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            height: '6px',
            background: '#e2e8f0',
            borderRadius: '3px',
            overflow: 'hidden',
            pointerEvents: 'none'
          }}
        >
          <div
            style={{
              height: '100%',
              width: `${progressPercent}%`,
              background: 'linear-gradient(90deg, #0284c7, #38bdf8)',
              transition: isPlaying ? 'none' : 'width 0.08s ease-out'
            }}
          />
        </div>

        {/* Keyframe Markers along the track */}
        {keyframes && keyframes.map((kf, idx) => {
          const kfPos = duration > 0 ? (kf.timestamp / duration) * 100 : 0;
          const isCurrent = idx === activeKeyframeIndex;
          const markerColor = kf.category === 'pathology' ? '#f43f5e' : kf.category === 'biomechanics' ? '#9333ea' : '#0284c7';

          return (
            <button
              key={idx}
              type="button"
              onClick={() => onSelectKeyframe && onSelectKeyframe(idx)}
              title={`Keyframe ${idx + 1} (${formatTime(kf.timestamp)}): ${kf.label || 'Marker'}`}
              style={{
                position: 'absolute',
                left: `${kfPos}%`,
                transform: 'translateX(-50%)',
                width: isCurrent ? '12px' : '8px',
                height: isCurrent ? '12px' : '8px',
                borderRadius: '50%',
                background: isCurrent ? '#ffffff' : markerColor,
                border: isCurrent ? `2.5px solid ${markerColor}` : '1.5px solid #ffffff',
                boxShadow: isCurrent ? `0 0 6px ${markerColor}` : '0 1px 3px rgba(0,0,0,0.2)',
                cursor: 'pointer',
                zIndex: isCurrent ? 5 : 2,
                padding: 0,
                transition: 'all 0.15s ease'
              }}
            />
          );
        })}

        {/* Real Range Input */}
        <input
          type="range"
          min={0}
          max={duration || 10}
          step={0.02}
          value={currentTime}
          onChange={handleSliderChange}
          style={{
            position: 'relative',
            width: '100%',
            height: '20px',
            opacity: 0,
            cursor: 'pointer',
            zIndex: 10
          }}
        />
      </div>

      {/* 3. Controls Row: Play/Pause, Step Back/Fwd, Keyframe Pills Carousel */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          {/* Step Back Frame */}
          <button
            type="button"
            onClick={() => stepFrame(-1)}
            style={{
              width: '28px',
              height: '28px',
              borderRadius: '6px',
              background: '#f8fafc',
              border: '1px solid #cbd5e1',
              color: '#334155',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
            title="Step Back 1 Frame"
          >
            <SkipBack size={13} />
          </button>

          {/* Play/Pause Button */}
          <button
            type="button"
            onClick={onPlayToggle}
            style={{
              padding: '4px 12px',
              borderRadius: '6px',
              background: isPlaying ? '#fee2e2' : '#e0f2fe',
              border: isPlaying ? '1px solid #fca5a5' : '1px solid #bae6fd',
              color: isPlaying ? '#dc2626' : '#0284c7',
              fontWeight: 800,
              fontSize: '0.74rem',
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
            title={isPlaying ? 'Pause Video' : 'Play Video'}
          >
            {isPlaying ? <Pause size={13} /> : <Play size={13} />}
            <span>{isPlaying ? 'PAUSE' : 'PLAY'}</span>
          </button>

          {/* Step Forward Frame */}
          <button
            type="button"
            onClick={() => stepFrame(1)}
            style={{
              width: '28px',
              height: '28px',
              borderRadius: '6px',
              background: '#f8fafc',
              border: '1px solid #cbd5e1',
              color: '#334155',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
            title="Step Forward 1 Frame"
          >
            <SkipForward size={13} />
          </button>
        </div>

        {/* Keyframe Selectors Pills */}
        {keyframes && keyframes.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', overflowX: 'auto', maxWidth: '380px' }}>
            <span style={{ fontSize: '0.64rem', color: '#64748b', textTransform: 'uppercase', marginRight: '2px', fontWeight: 600 }}>
              Keyframes:
            </span>
            {keyframes.map((kf, idx) => {
              const isSelected = idx === activeKeyframeIndex;
              return (
                <button
                  key={idx}
                  type="button"
                  onClick={() => onSelectKeyframe && onSelectKeyframe(idx)}
                  style={{
                    padding: '2px 7px',
                    borderRadius: '5px',
                    background: isSelected ? '#0284c7' : '#f8fafc',
                    border: isSelected ? '1px solid #0284c7' : '1px solid #e2e8f0',
                    color: isSelected ? '#ffffff' : '#475569',
                    fontSize: '0.66rem',
                    fontFamily: 'monospace',
                    cursor: 'pointer',
                    whiteSpace: 'nowrap',
                    fontWeight: isSelected ? 700 : 500,
                    transition: 'all 0.15s ease'
                  }}
                >
                  F{idx + 1} ({formatTime(kf.timestamp)})
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
export default VideoTimelineScrubber;
