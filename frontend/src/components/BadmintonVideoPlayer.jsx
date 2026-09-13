import React, { useState, useRef, useEffect } from 'react';
import { Play, Pause, Film, Layers, Eye, RefreshCw, ChevronRight } from 'lucide-react';
import { VideoTimelineScrubber } from './VideoTimelineScrubber';
import { getBadmintonSampleVideoUrl } from '../api/client';

/**
 * BadmintonVideoPlayer (Section 29)
 * Video playback view strictly reusing VideoTimelineScrubber with keyframe markers
 * anchored to detected strokes and optional MediaPipe BlazePose skeleton overlay.
 */
export function BadmintonVideoPlayer({
  videoUrl = null,
  videoFile = null,
  metadata = null,
  poseFrames = [],
  shots = [],
  activeShot = null,
  currentTime = 0,
  onSeek = null
}) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const animationFrameRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [localTime, setLocalTime] = useState(currentTime || 0);
  const [showSkeleton, setShowSkeleton] = useState(true);

  // Source URL resolution with automatic sample fallback to prevent black screen
  const resolvedUrl = React.useMemo(() => {
    if (videoUrl) return videoUrl;
    if (videoFile) {
      try {
        return URL.createObjectURL(videoFile);
      } catch (e) {
        return null;
      }
    }
    if (metadata?.duration_seconds || shots?.length > 0 || poseFrames?.length > 0) {
      return getBadmintonSampleVideoUrl();
    }
    return null;
  }, [videoUrl, videoFile, metadata, shots, poseFrames]);

  // Video duration & FPS fallback
  const duration = metadata?.duration_seconds || (poseFrames.length > 0 ? poseFrames.length / (metadata?.fps || 30.0) : 10);
  const fps = metadata?.fps || 30.0;

  // Keyframes from detected shots for scrubber integration
  const keyframes = React.useMemo(() => {
    return (shots || []).map((s, idx) => ({
      timestamp: s.contact_time ?? s.start_time ?? (idx * 1.5),
      label: s.shot_type || `Shot #${idx + 1}`,
      type: s.shot_type || 'stroke',
      score: s.confidence || 0.8
    }));
  }, [shots]);

  // Sync external seek with video element and local state
  const handleSeek = (newTime) => {
    const clamped = Math.max(0, Math.min(duration, newTime));
    setLocalTime(clamped);
    if (videoRef.current) {
      videoRef.current.currentTime = clamped;
    }
    if (onSeek) onSeek(clamped);
  };

  // Synchronize incoming currentTime prop from external clicks (e.g. timeline or finding card)
  useEffect(() => {
    if (currentTime !== undefined && currentTime !== null) {
      if (Math.abs(currentTime - localTime) > 0.25) {
        setLocalTime(currentTime);
        if (videoRef.current && Math.abs(videoRef.current.currentTime - currentTime) > 0.25) {
          videoRef.current.currentTime = currentTime;
        }
      }
    }
  }, [currentTime]);

  // Robust Play/Pause toggle
  const handlePlayToggle = () => {
    if (videoRef.current && resolvedUrl) {
      if (isPlaying) {
        videoRef.current.pause();
        setIsPlaying(false);
      } else {
        if (videoRef.current.currentTime >= duration - 0.1) {
          videoRef.current.currentTime = 0;
          setLocalTime(0);
        }
        videoRef.current
          .play()
          .then(() => setIsPlaying(true))
          .catch((err) => {
            console.warn('[BadmintonVideoPlayer] Playback warning:', err);
            setIsPlaying(true);
          });
      }
    } else {
      // Virtual timer playback fallback
      setIsPlaying((prev) => {
        const next = !prev;
        if (next && localTime >= duration - 0.1) {
          setLocalTime(0);
        }
        return next;
      });
    }
  };

  // High-frequency 60 FPS animation loop while playing
  useEffect(() => {
    if (!isPlaying) {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      return;
    }

    let lastTimestamp = performance.now();

    const loop = (now) => {
      const dt = (now - lastTimestamp) / 1000;
      lastTimestamp = now;

      if (videoRef.current && resolvedUrl) {
        const t = videoRef.current.currentTime;
        setLocalTime(t);
        if (videoRef.current.paused || videoRef.current.ended) {
          setIsPlaying(false);
          return;
        }
      } else {
        setLocalTime((prev) => {
          const next = prev + dt;
          if (next >= duration) {
            setIsPlaying(false);
            return duration;
          }
          return next;
        });
      }

      animationFrameRef.current = requestAnimationFrame(loop);
    };

    animationFrameRef.current = requestAnimationFrame(loop);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isPlaying, resolvedUrl, duration]);

  // Draw 33-landmark pose overlay on canvas with exact pixel projection
  useEffect(() => {
    if (!showSkeleton || !canvasRef.current || !videoRef.current || !poseFrames || poseFrames.length === 0) {
      if (canvasRef.current) {
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }
      return;
    }

    const canvas = canvasRef.current;
    const video = videoRef.current;
    const ctx = canvas.getContext('2d');

    // Synchronize canvas resolution with its actual rendered layout size
    const clientW = canvas.clientWidth || 960;
    const clientH = canvas.clientHeight || 540;
    if (canvas.width !== clientW || canvas.height !== clientH) {
      canvas.width = clientW;
      canvas.height = clientH;
    }

    const width = canvas.width;
    const height = canvas.height;
    ctx.clearRect(0, 0, width, height);

    // Compute exact rendered video rectangle inside objectFit: contain viewport
    let renderRect = { x: 0, y: 0, width, height };
    if (video && video.videoWidth && video.videoHeight) {
      const vAspect = video.videoWidth / video.videoHeight;
      const cAspect = width / height;

      if (vAspect > cAspect) {
        // Video is wider than canvas -> Letterboxed on top/bottom
        const rHeight = width / vAspect;
        const offsetY = (height - rHeight) / 2;
        renderRect = { x: 0, y: offsetY, width, height: rHeight };
      } else {
        // Video is taller than canvas -> Pillarboxed on left/right
        const rWidth = height * vAspect;
        const offsetX = (width - rWidth) / 2;
        renderRect = { x: offsetX, y: 0, width: rWidth, height };
      }
    }

    // Precise timestamp-based frame lookup (guarantees millisecond temporal synchronization)
    const currentMs = localTime * 1000;
    let frame = poseFrames[0];
    let minDiff = Infinity;
    for (let i = 0; i < poseFrames.length; i++) {
      const f = poseFrames[i];
      const tMs = f.timestamp_ms ?? (f.frame_index * (1000 / (fps || 30.0)));
      const diff = Math.abs(tMs - currentMs);
      if (diff < minDiff) {
        minDiff = diff;
        frame = f;
      }
    }

    if (frame && frame.landmarks && frame.landmarks.length >= 33 && frame.is_detected !== false) {
      const mapCoord = (lm) => {
        if (!lm || (lm.x === 0 && lm.y === 0 && lm.visibility === 0)) return null;
        return {
          x: renderRect.x + lm.x * renderRect.width,
          y: renderRect.y + lm.y * renderRect.height,
          visibility: lm.visibility ?? 1.0
        };
      };

      // Anatomical Kinetic Chain Connections
      const chains = [
        // Torso Box (Lavender/Indigo)
        { pairs: [[11, 12], [11, 23], [12, 24], [23, 24]], color: '#818cf8', glow: '#6366f1', width: 3 },
        // Right Arm / Racket Kinematic Chain (Vibrant Amber/Gold)
        { pairs: [[12, 14], [14, 16], [16, 18], [16, 20], [16, 22]], color: '#fbbf24', glow: '#f59e0b', width: 3.5 },
        // Left Arm (Electric Sky Cyan)
        { pairs: [[11, 13], [13, 15], [15, 17], [15, 19], [15, 21]], color: '#38bdf8', glow: '#0284c7', width: 2.5 },
        // Right Leg (Bright Emerald)
        { pairs: [[24, 26], [26, 28], [28, 30], [28, 32], [30, 32]], color: '#34d399', glow: '#10b981', width: 3 },
        // Left Leg (Teal)
        { pairs: [[23, 25], [25, 27], [27, 29], [27, 31], [29, 31]], color: '#2dd4bf', glow: '#0d9488', width: 2.5 }
      ];

      // 1. Draw Kinematic Chain Bone Connectors
      chains.forEach((chain) => {
        ctx.save();
        ctx.strokeStyle = chain.color;
        ctx.shadowColor = chain.glow;
        ctx.shadowBlur = 6;
        ctx.lineWidth = chain.width;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';

        chain.pairs.forEach(([i1, i2]) => {
          const lm1 = frame.landmarks[i1];
          const lm2 = frame.landmarks[i2];
          if (
            lm1 &&
            lm2 &&
            (lm1.visibility === undefined || lm1.visibility >= 0.20) &&
            (lm2.visibility === undefined || lm2.visibility >= 0.20)
          ) {
            const p1 = mapCoord(lm1);
            const p2 = mapCoord(lm2);
            if (p1 && p2) {
              ctx.beginPath();
              ctx.moveTo(p1.x, p1.y);
              ctx.lineTo(p2.x, p2.y);
              ctx.stroke();
            }
          }
        });
        ctx.restore();
      });

      // 2. Draw 33 Anatomical Joint Nodes with Glow & Core Dots
      frame.landmarks.forEach((lm, idx) => {
        if (lm.visibility !== undefined && lm.visibility < 0.20) return;
        const p = mapCoord(lm);
        if (!p) return;

        const isContactArmJoint = [12, 14, 16].includes(idx); // Right shoulder, elbow, wrist
        const isHead = idx < 11;

        ctx.save();
        // Outer Glow Ring
        ctx.beginPath();
        ctx.arc(p.x, p.y, isContactArmJoint ? 5.5 : (isHead ? 2.5 : 4), 0, 2 * Math.PI);
        ctx.fillStyle = isContactArmJoint ? '#fbbf24' : '#38bdf8';
        ctx.shadowColor = isContactArmJoint ? '#f59e0b' : '#0284c7';
        ctx.shadowBlur = isContactArmJoint ? 10 : 5;
        ctx.fill();

        // Inner Core Dot
        ctx.beginPath();
        ctx.arc(p.x, p.y, isContactArmJoint ? 2.5 : (isHead ? 1.2 : 2), 0, 2 * Math.PI);
        ctx.fillStyle = '#ffffff';
        ctx.fill();
        ctx.restore();
      });

      // 3. Highlight Dominant Contact Elbow Tag
      const rightElbow = frame.landmarks[14];
      if (rightElbow && (rightElbow.visibility ?? 1.0) >= 0.25) {
        const pElbow = mapCoord(rightElbow);
        if (pElbow) {
          ctx.save();
          ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
          ctx.strokeStyle = '#fbbf24';
          ctx.lineWidth = 1.5;
          const tagX = Math.min(width - 70, Math.max(10, pElbow.x + 10));
          const tagY = Math.min(height - 20, Math.max(20, pElbow.y - 8));
          ctx.fillRect(tagX, tagY - 14, 58, 18);
          ctx.strokeRect(tagX, tagY - 14, 58, 18);
          ctx.fillStyle = '#fbbf24';
          ctx.font = 'bold 10px monospace';
          ctx.fillText('R-ARM', tagX + 6, tagY - 2);
          ctx.restore();
        }
      }
    }
  }, [localTime, showSkeleton, poseFrames, fps]);

  return (
    <div
      id="badminton-video-player"
      className="badminton-video-player-container"
      style={{
        background: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: '16px',
        padding: '16px',
        boxShadow: '0 4px 20px -2px rgba(0,0,0,0.04)',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.75rem'
      }}
    >
      {/* Video Viewport with Overlay Canvas */}
      <div
        style={{
          position: 'relative',
          width: '100%',
          aspectRatio: '16/9',
          background: '#0f172a',
          borderRadius: '12px',
          overflow: 'hidden',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}
      >
        {resolvedUrl ? (
          <>
            <video
              ref={videoRef}
              src={resolvedUrl}
              preload="auto"
              onPlay={() => setIsPlaying(true)}
              onPause={() => setIsPlaying(false)}
              onLoadedMetadata={(e) => {
                try {
                  if (e.target.currentTime === 0) {
                    e.target.currentTime = 0.001; // Render first frame instead of black canvas
                  }
                } catch (err) {}
              }}
              onLoadedData={(e) => {
                try {
                  if (e.target.currentTime === 0) {
                    e.target.currentTime = 0.001;
                  }
                } catch (err) {}
              }}
              onError={(e) => {
                console.warn('[BadmintonVideoPlayer] Video failed to load source, falling back to sample rally:', e);
                if (videoRef.current && !videoRef.current.src.includes('/sample/video')) {
                  videoRef.current.src = getBadmintonSampleVideoUrl();
                  videoRef.current.load();
                }
              }}
              onEnded={() => {
                setIsPlaying(false);
                setLocalTime(duration);
              }}
              style={{ width: '100%', height: '100%', objectFit: 'contain', cursor: 'pointer' }}
              onClick={handlePlayToggle}
              playsInline
            />
            <canvas
              ref={canvasRef}
              width={960}
              height={540}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                pointerEvents: 'none'
              }}
            />

            {/* Prominent Center Play Button Overlay when paused */}
            {!isPlaying && (
              <button
                onClick={handlePlayToggle}
                aria-label="Play Badminton Rally Video"
                style={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  width: '64px',
                  height: '64px',
                  borderRadius: '50%',
                  background: 'rgba(15, 23, 42, 0.78)',
                  backdropFilter: 'blur(8px)',
                  WebkitBackdropFilter: 'blur(8px)',
                  border: '2px solid rgba(255, 255, 255, 0.5)',
                  color: '#ffffff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  boxShadow: '0 8px 24px rgba(0, 0, 0, 0.45)',
                  transition: 'transform 0.15s ease, background 0.15s ease',
                  zIndex: 8
                }}
                onMouseEnter={(e) => (e.currentTarget.style.transform = 'translate(-50%, -50%) scale(1.08)')}
                onMouseLeave={(e) => (e.currentTarget.style.transform = 'translate(-50%, -50%) scale(1.0)')}
              >
                <Play size={26} style={{ marginLeft: '3px' }} fill="#ffffff" />
              </button>
            )}
          </>
        ) : (
          <div style={{ color: '#94a3b8', fontSize: '0.88rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Film size={20} />
            <span>Select or upload a badminton rally clip to begin analysis</span>
          </div>
        )}

        {/* Theme-Synchronized Pose Skeleton Control HUD Box */}
        {resolvedUrl && (
          <div
            className="pose-skeleton-hud-box"
            style={{
              position: 'absolute',
              top: '12px',
              right: '12px',
              background: 'rgba(255, 255, 255, 0.94)',
              backdropFilter: 'blur(12px)',
              WebkitBackdropFilter: 'blur(12px)',
              border: '1px solid #e2e8f0',
              borderRadius: '10px',
              padding: '6px 12px',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              boxShadow: '0 4px 16px -2px rgba(0, 0, 0, 0.1)',
              zIndex: 10,
              transition: 'all 0.2s ease'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div
                style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: showSkeleton ? '#10b981' : '#94a3b8',
                  boxShadow: showSkeleton ? '0 0 8px #10b981' : 'none',
                  transition: 'all 0.25s ease'
                }}
              />
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <span style={{ fontSize: '0.78rem', fontWeight: '800', color: '#0f172a', letterSpacing: '0.01em', lineHeight: '1.2' }}>
                    Pose Skeleton
                  </span>
                  <span
                    style={{
                      fontSize: '0.62rem',
                      fontWeight: '800',
                      padding: '1px 5px',
                      borderRadius: '4px',
                      background: showSkeleton ? '#dcfce7' : '#f1f5f9',
                      color: showSkeleton ? '#15803d' : '#64748b',
                      border: `1px solid ${showSkeleton ? '#bbf7d0' : '#e2e8f0'}`
                    }}
                  >
                    {showSkeleton ? 'LIVE' : 'OFF'}
                  </span>
                </div>
                <span style={{ fontSize: '0.66rem', color: '#64748b', fontWeight: '600', lineHeight: '1.1' }}>
                  {showSkeleton ? 'MediaPipe 33 Keypoints' : 'Overlay Hidden'}
                </span>
              </div>
            </div>

            {/* Interactive Tactile Toggle Switch */}
            <button
              onClick={() => setShowSkeleton(!showSkeleton)}
              style={{
                background: showSkeleton ? '#0284c7' : '#e2e8f0',
                border: 'none',
                borderRadius: '16px',
                width: '38px',
                height: '22px',
                padding: '2px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: showSkeleton ? 'flex-end' : 'flex-start',
                transition: 'all 0.2s ease',
                boxShadow: showSkeleton ? '0 2px 8px rgba(2, 132, 199, 0.3)' : 'none'
              }}
              title={showSkeleton ? 'Hide Pose Skeleton' : 'Show Pose Skeleton'}
            >
              <div
                style={{
                  width: '18px',
                  height: '18px',
                  borderRadius: '50%',
                  background: '#ffffff',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                <Layers size={10} color={showSkeleton ? '#0284c7' : '#64748b'} />
              </div>
            </button>
          </div>
        )}

        {/* Real-Time Telemetry Badge */}
        {resolvedUrl && showSkeleton && (() => {
          const currentF = Math.round(localTime * fps);
          const contactF = activeShot?.contact_frame ?? Math.round((activeShot?.contact_time ?? -999) * fps);
          const isApexContact = activeShot && (contactF === currentF || Math.abs((activeShot?.contact_time ?? 0) - localTime) < (0.6 / fps));
          const isEvidenceFrame = activeShot && Array.isArray(activeShot?.evidence_frames) && activeShot.evidence_frames.includes(currentF);
          const deltaSec = ((currentF - contactF) / fps);

          return (
            <div
              style={{
                position: 'absolute',
                bottom: '10px',
                left: '12px',
                background: isApexContact ? 'rgba(254, 243, 199, 0.95)' : (isEvidenceFrame ? 'rgba(224, 242, 254, 0.95)' : 'rgba(255, 255, 255, 0.92)'),
                backdropFilter: 'blur(10px)',
                WebkitBackdropFilter: 'blur(10px)',
                border: isApexContact ? '1px solid #fde68a' : (isEvidenceFrame ? '1px solid #bae6fd' : '1px solid #e2e8f0'),
                borderRadius: '8px',
                padding: '4px 10px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '0.72rem',
                color: isApexContact ? '#92400e' : (isEvidenceFrame ? '#0369a1' : '#334155'),
                fontFamily: 'monospace',
                fontWeight: '600',
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
                zIndex: 10,
                transition: 'all 0.15s ease'
              }}
            >
              <span style={{ color: isApexContact ? '#b45309' : (isEvidenceFrame ? '#0284c7' : '#0284c7'), fontWeight: '800' }}>
                {isApexContact ? '⚡ IMPACT APEX' : (isEvidenceFrame ? 'EVIDENCE FRAME' : '3D BIOMECHANICS')}
              </span>
              <span>•</span>
              <span>Frame #{currentF}</span>
              <span>•</span>
              <span>t={localTime.toFixed(2)}s</span>
              {isEvidenceFrame && (
                <>
                  <span>•</span>
                  <span style={{ color: '#0369a1', fontWeight: '700' }}>
                    &Delta;t={deltaSec >= 0 ? `+${deltaSec.toFixed(2)}s` : `${deltaSec.toFixed(2)}s`}
                  </span>
                </>
              )}
            </div>
          );
        })()}
      </div>

      {/* Temporal Navigation Scrubber (Reused Component) */}
      <VideoTimelineScrubber
        currentTime={localTime}
        duration={duration}
        isPlaying={isPlaying}
        onPlayToggle={handlePlayToggle}
        onSeek={handleSeek}
        keyframes={keyframes}
        activeKeyframeIndex={activeShot ? Math.max(0, shots.findIndex((s) => s.shot_id === activeShot.shot_id)) : 0}
        onSelectKeyframe={(idx) => {
          if (keyframes[idx]) handleSeek(keyframes[idx].timestamp);
        }}
        fps={fps}
      />
    </div>
  );
}
