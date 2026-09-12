import React, { useState, useEffect } from 'react';
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Film,
  Zap,
  Clock,
  Layers,
  ChevronRight,
  Sparkles
} from 'lucide-react';

/**
 * VideoTimelineScrubber
 * Interactive temporal video navigation with keyframe markers,
 * play/pause control, speed adjustment, and timestamp scrubbing.
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
  fps = 2.0
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
    const delta = (1 / fps) * direction;
    const newTime = Math.max(0, Math.min(duration, currentTime + delta));
    if (onSeek) onSeek(newTime);
  };

  return (
    <div
      className="video-timeline-scrubber-container"
      style={{
        background: 'rgba(15, 23, 42, 0.85)',
        border: '1px solid rgba(56, 189, 248, 0.25)',
        borderRadius: '10px',
        padding: '0.65rem 0.85rem',
        marginTop: '0.6rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.5rem',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.35)',
        backdropFilter: 'blur(10px)'
      }}
    >
      {/* 1. Header Row: Mode Badge, Keyframe Tracker, and Live Time Display */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.72rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              padding: '0.15rem 0.45rem',
              borderRadius: '4px',
              background: 'rgba(56, 189, 248, 0.15)',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              color: 'var(--primary)',
              fontWeight: 700,
              fontSize: '0.68rem',
              letterSpacing: '0.04em'
            }}
          >
            <Film size={11} />
            TEMPORAL VIDEO SCRUBBER
          </span>

          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '3px',
              padding: '0.15rem 0.4rem',
              borderRadius: '4px',
              background: 'rgba(56, 189, 248, 0.12)',
              color: 'var(--primary)',
              fontSize: '0.65rem',
              fontFamily: 'var(--font-mono)'
            }}
          >
            <Zap size={10} />
            {fps.toFixed(1)} FPS Sampled
          </span>
        </div>

        {/* Timestamp */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
          <Clock size={11} color="var(--text-muted)" />
          <span style={{ color: 'var(--primary)' }}>{formatTime(currentTime)}</span>
          <span style={{ color: 'var(--text-muted)' }}>/</span>
          <span style={{ color: 'var(--text-muted)' }}>{formatTime(duration)}</span>
        </div>
      </div>

      {/* 2. Interactive Scrubber Track with Keyframe Markers */}
      <div style={{ position: 'relative', width: '100%', height: '24px', display: 'flex', alignItems: 'center' }}>
        {/* Custom Progress Bar Background */}
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            height: '6px',
            background: 'rgba(255, 255, 255, 0.1)',
            borderRadius: '3px',
            overflow: 'hidden',
            pointerEvents: 'none'
          }}
        >
          <div
            style={{
              height: '100%',
              width: `${progressPercent}%`,
              background: 'linear-gradient(90deg, #38bdf8, #818cf8)',
              transition: isPlaying ? 'none' : 'width 0.1s ease-out'
            }}
          />
        </div>

        {/* Keyframe Markers along the track */}
        {keyframes && keyframes.map((kf, idx) => {
          const kfPos = duration > 0 ? (kf.timestamp / duration) * 100 : 0;
          const isCurrent = idx === activeKeyframeIndex;
          const categoryColor = kf.category === 'pathology' ? '#f43f5e' : kf.category === 'biomechanics' ? '#a855f7' : '#38bdf8';

          return (
            <button
              key={idx}
              type="button"
              onClick={() => onSelectKeyframe && onSelectKeyframe(idx)}
              title={`Frame ${idx + 1} (${formatTime(kf.timestamp)}): ${kf.label || 'Keyframe'}`}
              style={{
                position: 'absolute',
                left: `${kfPos}%`,
                transform: 'translateX(-50%)',
                width: isCurrent ? '12px' : '8px',
                height: isCurrent ? '12px' : '8px',
                borderRadius: '50%',
                background: isCurrent ? '#ffffff' : categoryColor,
                border: isCurrent ? `2px solid ${categoryColor}` : '1px solid rgba(0,0,0,0.4)',
                boxShadow: isCurrent ? `0 0 8px ${categoryColor}` : 'none',
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
          step={0.05}
          value={currentTime}
          onChange={handleSliderChange}
          style={{
            position: 'relative',
            width: '100%',
            height: '24px',
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
              width: '26px',
              height: '26px',
              borderRadius: '5px',
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-muted)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer'
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
              padding: '0.25rem 0.75rem',
              borderRadius: '6px',
              background: isPlaying ? 'rgba(239, 68, 68, 0.18)' : 'rgba(56, 189, 248, 0.18)',
              border: isPlaying ? '1px solid rgba(239, 68, 68, 0.4)' : '1px solid rgba(56, 189, 248, 0.4)',
              color: isPlaying ? '#f87171' : 'var(--primary)',
              fontWeight: 700,
              fontSize: '0.72rem',
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
              width: '26px',
              height: '26px',
              borderRadius: '5px',
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-muted)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer'
            }}
            title="Step Forward 1 Frame"
          >
            <SkipForward size={13} />
          </button>
        </div>

        {/* Keyframe Selectors Pills */}
        {keyframes && keyframes.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', overflowX: 'auto', maxWidth: '380px' }}>
            <span style={{ fontSize: '0.62rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginRight: '2px' }}>
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
                    padding: '0.15rem 0.4rem',
                    borderRadius: '4px',
                    background: isSelected ? 'rgba(56, 189, 248, 0.22)' : 'rgba(255, 255, 255, 0.04)',
                    border: isSelected ? '1px solid var(--primary)' : '1px solid var(--border-color)',
                    color: isSelected ? 'var(--primary)' : 'var(--text-muted)',
                    fontSize: '0.64rem',
                    fontFamily: 'var(--font-mono)',
                    cursor: 'pointer',
                    whiteSpace: 'nowrap',
                    fontWeight: isSelected ? 700 : 500
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
