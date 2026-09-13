import React, { useState, useEffect, useMemo } from 'react';
import {
  X, Target, Zap, Clock, Activity, Gauge, AlertTriangle,
  ShieldCheck, Film, Layers, GitFork, ExternalLink, Play,
  Pause, ChevronLeft, ChevronRight, Calculator,
  TrendingUp, TrendingDown, Crosshair
} from 'lucide-react';

/**
 * Helper: Compute 3-point angle in degrees (arccos vector formula)
 * A -> B (vertex) -> C
 */
function calculateJointAngle(pA, pB, pC) {
  if (!pA || !pB || !pC) return null;
  if (pA.visibility < 0.25 || pB.visibility < 0.25 || pC.visibility < 0.25) return null;

  const v1x = pA.x - pB.x;
  const v1y = pA.y - pB.y;
  const v2x = pC.x - pB.x;
  const v2y = pC.y - pB.y;

  const dot = v1x * v2x + v1y * v2y;
  const mag1 = Math.sqrt(v1x * v1x + v1y * v1y);
  const mag2 = Math.sqrt(v2x * v2x + v2y * v2y);

  if (mag1 === 0 || mag2 === 0) return null;
  const cosTheta = Math.max(-1.0, Math.min(1.0, dot / (mag1 * mag2)));
  return (Math.acos(cosTheta) * 180.0) / Math.PI;
}

/**
 * ShotDetailCard (Section 29)
 * Deep-dive detail card for a selected shot event featuring accurate, calculative,
 * and reactive Real Evidence Frames with real-time video playhead synchronization,
 * frame-by-frame joint kinematics, micro-step controls, and biomechanical phase breakdown.
 */
export function ShotDetailCard({
  shot,
  onClose,
  onSeek = null,
  currentTime = 0,
  poseFrames = [],
  fps = 30.0,
  graphNodeId = null,
  onViewInGraph = null
}) {
  if (!shot) return null;

  const [selectedFrameOverride, setSelectedFrameOverride] = useState(null);

  // Global Shot Pose Metrics fallback
  const poseFeatures = shot.pose_features || shot.contact_joint_angles || {};
  const apexElbowAngle = poseFeatures.contact_elbow_angle_deg ?? poseFeatures.elbow_angle_deg;
  const apexShoulderAngle = poseFeatures.shoulder_angle_deg;
  const apexKneeAngle = poseFeatures.knee_angle_deg;
  const apexHipAngle = poseFeatures.hip_angle_deg;

  const racketSpeed = shot.racket_speed;
  const shuttleSpeed = shot.shuttle_speed;

  const contactFrame = shot.contact_frame ?? Math.round((shot.contact_time ?? 0) * fps);
  const startFrame = shot.start_frame ?? Math.max(0, contactFrame - 6);
  const endFrame = shot.end_frame ?? Math.min(contactFrame + 6, Math.round(((shot.end_time ?? 0) * fps) || (contactFrame + 6)));

  // Real evidence frames list from contact window
  const rawEvidenceFrames = useMemo(() => {
    if (Array.isArray(shot.evidence_frames) && shot.evidence_frames.length > 0) {
      return [...new Set(shot.evidence_frames)].sort((a, b) => a - b);
    }
    const frames = [];
    for (let f = startFrame; f <= endFrame; f++) {
      frames.push(f);
    }
    return frames.length > 0 ? frames : [contactFrame];
  }, [shot.evidence_frames, startFrame, endFrame, contactFrame]);

  // Current playing frame index
  const currentPlayingFrame = Math.round(currentTime * fps);

  // Active Frame: either explicitly clicked frame or closest playing frame within shot window
  const activeFrame = useMemo(() => {
    if (selectedFrameOverride !== null && rawEvidenceFrames.includes(selectedFrameOverride)) {
      return selectedFrameOverride;
    }
    // Check if current video playhead is inside evidence frames range
    if (rawEvidenceFrames.includes(currentPlayingFrame)) {
      return currentPlayingFrame;
    }
    // Fallback to contact frame
    return rawEvidenceFrames.includes(contactFrame) ? contactFrame : rawEvidenceFrames[0];
  }, [selectedFrameOverride, currentPlayingFrame, rawEvidenceFrames, contactFrame]);

  // Reset selected frame override when shot changes
  useEffect(() => {
    setSelectedFrameOverride(null);
  }, [shot.shot_id]);

  // Calculate precision kinematics for the active frame from poseFrames
  const frameKinematics = useMemo(() => {
    const pFrame = poseFrames?.find((f) => f.frame_index === activeFrame);
    const lms = pFrame?.landmarks;

    let elbow = null;
    let shoulder = null;
    let knee = null;
    let hip = null;
    let wristDist = null;

    if (lms && lms.length >= 33) {
      // Right arm chain: 12 (R-Shoulder), 14 (R-Elbow), 16 (R-Wrist)
      elbow = calculateJointAngle(lms[12], lms[14], lms[16]);
      // Right shoulder: 24 (R-Hip), 12 (R-Shoulder), 14 (R-Elbow)
      shoulder = calculateJointAngle(lms[24], lms[12], lms[14]);
      // Right knee: 24 (R-Hip), 26 (R-Knee), 28 (R-Ankle)
      knee = calculateJointAngle(lms[24], lms[26], lms[28]);
      // Right hip: 12 (R-Shoulder), 24 (R-Hip), 26 (R-Knee)
      hip = calculateJointAngle(lms[12], lms[24], lms[26]);

      // Calculate instantaneous wrist speed from delta if neighboring frames exist
      const prevFrame = poseFrames?.find((f) => f.frame_index === activeFrame - 1);
      const nextFrame = poseFrames?.find((f) => f.frame_index === activeFrame + 1);
      if (prevFrame?.landmarks?.[16] && nextFrame?.landmarks?.[16]) {
        const dx = nextFrame.landmarks[16].x - prevFrame.landmarks[16].x;
        const dy = nextFrame.landmarks[16].y - prevFrame.landmarks[16].y;
        wristDist = Math.sqrt(dx * dx + dy * dy);
      }
    }

    // Temporal delta from contact apex
    const deltaFrames = activeFrame - contactFrame;
    const deltaSeconds = deltaFrames / fps;

    // Biomechanical Phase derivation
    let phaseName = 'Impact Apex';
    let phaseColor = '#f59e0b';
    let phaseBadge = '⚡ APEX CONTACT';

    if (deltaFrames <= -4) {
      phaseName = 'Preparation & Backswing Load';
      phaseColor = '#64748b';
      phaseBadge = '1. PREPARATION';
    } else if (deltaFrames < 0) {
      phaseName = 'Kinematic Forward Acceleration';
      phaseColor = '#0284c7';
      phaseBadge = '2. FORWARD DRIVE';
    } else if (deltaFrames === 0) {
      phaseName = 'Kinetic Energy Transfer / Impact';
      phaseColor = '#d97706';
      phaseBadge = '3. APEX IMPACT';
    } else {
      phaseName = 'Deceleration & Follow-Through';
      phaseColor = '#16a34a';
      phaseBadge = '4. FOLLOW-THROUGH';
    }

    return {
      frame: activeFrame,
      time: activeFrame / fps,
      deltaFrames,
      deltaSeconds,
      phaseName,
      phaseColor,
      phaseBadge,
      elbowAngle: elbow ?? (activeFrame === contactFrame ? apexElbowAngle : null),
      shoulderAngle: shoulder ?? (activeFrame === contactFrame ? apexShoulderAngle : null),
      kneeAngle: knee ?? (activeFrame === contactFrame ? apexKneeAngle : null),
      hipAngle: hip ?? (activeFrame === contactFrame ? apexHipAngle : null),
      wristSpeedEstimate: wristDist ? (wristDist * fps * 3.6).toFixed(1) : (shot.wrist_speed_km_h?.toString() || null)
    };
  }, [activeFrame, poseFrames, contactFrame, fps, apexElbowAngle, apexShoulderAngle, apexKneeAngle, apexHipAngle, shot.wrist_speed_km_h]);

  const handleSeekToFrame = (frameNum) => {
    setSelectedFrameOverride(frameNum);
    const frameTime = frameNum / fps;
    if (onSeek) onSeek(frameTime);

    // Smooth scroll to video viewport
    setTimeout(() => {
      const videoEl = document.getElementById('badminton-video-player') || document.querySelector('.badminton-video-player-container');
      if (videoEl) {
        videoEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    }, 40);
  };

  const handleStepFrame = (step) => {
    const currentIndex = rawEvidenceFrames.indexOf(activeFrame);
    let nextFrame = activeFrame + step;
    if (currentIndex !== -1) {
      const targetIdx = Math.max(0, Math.min(rawEvidenceFrames.length - 1, currentIndex + step));
      nextFrame = rawEvidenceFrames[targetIdx];
    }
    handleSeekToFrame(nextFrame);
  };

  return (
    <div
      className="shot-detail-card"
      style={{
        background: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: '16px',
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
        boxShadow: '0 6px 24px rgba(0, 0, 0, 0.05)',
        position: 'relative'
      }}
    >
      {/* Close Button */}
      {onClose && (
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '16px',
            right: '16px',
            background: '#f1f5f9',
            border: 'none',
            color: '#64748b',
            cursor: 'pointer',
            padding: '6px',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'background 0.15s ease'
          }}
          title="Close Stroke Detail"
        >
          <X size={16} />
        </button>
      )}

      {/* Header with Title & Confidence Badge */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
        <div style={{ background: '#f0f9ff', padding: '6px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Target size={18} color="#0284c7" />
        </div>
        <span style={{ fontSize: '1.02rem', fontWeight: '800', color: '#0f172a' }}>
          Stroke Detail: {shot.shot_id || 'Selected Event'}
        </span>
        <span
          style={{
            fontSize: '0.75rem',
            fontWeight: '800',
            padding: '3px 10px',
            borderRadius: '6px',
            background: '#e0f2fe',
            color: '#0369a1',
            textTransform: 'uppercase',
            letterSpacing: '0.03em'
          }}
        >
          {shot.shot_type || 'UNKNOWN'}
        </span>
        <span
          style={{
            fontSize: '0.76rem',
            color: (shot.confidence || 0) >= 0.8 ? '#15803d' : '#b45309',
            background: (shot.confidence || 0) >= 0.8 ? '#dcfce7' : '#fef3c7',
            padding: '2px 8px',
            borderRadius: '6px',
            fontWeight: '700'
          }}
        >
          Conf: {((shot.confidence || 0) * 100).toFixed(0)}%
        </span>
      </div>

      {/* Timing & Duration Summary Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))',
          gap: '8px',
          background: '#f8fafc',
          padding: '12px',
          borderRadius: '12px',
          border: '1px solid #e2e8f0'
        }}
      >
        <div>
          <div style={{ fontSize: '0.70rem', color: '#64748b', fontWeight: '600' }}>Contact Apex</div>
          <div style={{ fontSize: '0.92rem', fontWeight: '800', color: '#0f172a', marginTop: '2px' }}>
            {shot.contact_time !== undefined && shot.contact_time !== null ? `${shot.contact_time.toFixed(2)}s` : '—'}
          </div>
          <div style={{ fontSize: '0.68rem', color: '#0284c7', fontFamily: 'monospace' }}>Frame #{contactFrame}</div>
        </div>
        <div>
          <div style={{ fontSize: '0.70rem', color: '#64748b', fontWeight: '600' }}>Stroke Duration</div>
          <div style={{ fontSize: '0.92rem', fontWeight: '800', color: '#0284c7', marginTop: '2px' }}>
            {shot.duration !== undefined && shot.duration !== null ? `${shot.duration.toFixed(2)}s` : '—'}
          </div>
          <div style={{ fontSize: '0.68rem', color: '#64748b' }}>{rawEvidenceFrames.length} Frames</div>
        </div>
        <div>
          <div style={{ fontSize: '0.70rem', color: '#64748b', fontWeight: '600' }}>Impact Speed</div>
          <div style={{ fontSize: '0.92rem', fontWeight: '800', color: '#9333ea', marginTop: '2px' }}>
            {shot.racket_speed?.value ? `${shot.racket_speed.value} ${shot.racket_speed.unit}` : (shot.wrist_speed_km_h ? `${shot.wrist_speed_km_h} km/h` : 'Calculated')}
          </div>
          <div style={{ fontSize: '0.68rem', color: '#64748b' }}>Kinematic Peak</div>
        </div>
      </div>

      {/* Classification Reason / Ground Truth */}
      {shot.classification_reason && (
        <div style={{ fontSize: '0.78rem', color: '#475569', background: '#f8fafc', padding: '10px 12px', borderRadius: '10px', border: '1px solid #e2e8f0', lineHeight: 1.45 }}>
          <strong style={{ color: '#0f172a' }}>Classification Ground Truth:</strong> {shot.classification_reason}
        </div>
      )}

      {/* ========================================================================= */}
      {/* SECTION: ACCURATE, CALCULATIVE & REACTIVE REAL EVIDENCE FRAMES */}
      {/* ========================================================================= */}
      <div
        style={{
          background: 'linear-gradient(145deg, #f0fdf4 0%, #f0f9ff 100%)',
          border: '1px solid #bae6fd',
          borderRadius: '14px',
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
          boxShadow: '0 2px 10px rgba(2, 132, 199, 0.04)'
        }}
      >
        {/* Header & Playback Control Ribbon */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ background: '#0284c7', color: '#ffffff', padding: '4px', borderRadius: '6px', display: 'flex' }}>
              <Layers size={15} />
            </div>
            <div>
              <div style={{ fontSize: '0.86rem', fontWeight: '800', color: '#0c4a6e' }}>
                Real Evidence Frames ({rawEvidenceFrames.length} Frames)
              </div>
              <div style={{ fontSize: '0.70rem', color: '#0369a1' }}>
                Frame-accurate multi-modal contact window & kinematics
              </div>
            </div>
          </div>

          {/* Micro-Stepping & Stroke Loop Playback Toolbar */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <button
              onClick={() => handleStepFrame(-1)}
              style={{
                background: '#ffffff',
                border: '1px solid #cbd5e1',
                borderRadius: '6px',
                padding: '4px 7px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                color: '#334155',
                fontSize: '0.72rem',
                fontWeight: '700'
              }}
              title="Step -1 Frame"
            >
              <ChevronLeft size={13} />
              <span>-1f</span>
            </button>

            <button
              onClick={() => handleSeekToFrame(contactFrame)}
              style={{
                background: activeFrame === contactFrame ? '#d97706' : '#ffffff',
                border: activeFrame === contactFrame ? '1px solid #b45309' : '1px solid #cbd5e1',
                color: activeFrame === contactFrame ? '#ffffff' : '#b45309',
                borderRadius: '6px',
                padding: '4px 8px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '3px',
                fontSize: '0.72rem',
                fontWeight: '800'
              }}
              title="Jump to Impact Apex Contact Frame"
            >
              <Zap size={12} />
              <span>Apex</span>
            </button>

            <button
              onClick={() => handleStepFrame(1)}
              style={{
                background: '#ffffff',
                border: '1px solid #cbd5e1',
                borderRadius: '6px',
                padding: '4px 7px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                color: '#334155',
                fontSize: '0.72rem',
                fontWeight: '700'
              }}
              title="Step +1 Frame"
            >
              <span>+1f</span>
              <ChevronRight size={13} />
            </button>
          </div>
        </div>

        {/* Interactive Reactive Evidence Frames Strip */}
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '6px',
            background: 'rgba(255, 255, 255, 0.75)',
            padding: '8px',
            borderRadius: '10px',
            border: '1px solid rgba(186, 230, 253, 0.8)'
          }}
        >
          {rawEvidenceFrames.map((frameNum) => {
            const isContact = frameNum === contactFrame;
            const isActive = frameNum === activeFrame;
            const frameTime = frameNum / fps;
            const deltaF = frameNum - contactFrame;

            let badgeBg = '#ffffff';
            let badgeBorder = '#cbd5e1';
            let badgeText = '#334155';

            if (isActive) {
              badgeBg = isContact ? '#fef3c7' : '#e0f2fe';
              badgeBorder = isContact ? '#d97706' : '#0284c7';
              badgeText = isContact ? '#92400e' : '#0369a1';
            } else if (isContact) {
              badgeBg = '#fffbeb';
              badgeBorder = '#f59e0b';
              badgeText = '#b45309';
            }

            return (
              <button
                key={frameNum}
                onClick={() => handleSeekToFrame(frameNum)}
                style={{
                  background: badgeBg,
                  border: `1.5px solid ${badgeBorder}`,
                  color: badgeText,
                  borderRadius: '8px',
                  padding: '5px 8px',
                  fontSize: '0.74rem',
                  cursor: 'pointer',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '2px',
                  fontWeight: isActive || isContact ? '800' : '600',
                  transition: 'all 0.15s ease',
                  boxShadow: isActive ? '0 0 0 2px rgba(2, 132, 199, 0.25)' : 'none',
                  minWidth: '46px'
                }}
                title={`Seek video to Frame #${frameNum} (t=${frameTime.toFixed(2)}s | Δt=${(deltaF / fps).toFixed(2)}s)${isContact ? ' - APEX IMPACT' : ''}`}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
                  {isContact ? <Zap size={11} color="#d97706" /> : <Film size={11} color={isActive ? '#0284c7' : '#94a3b8'} />}
                  <span>#{frameNum}</span>
                </div>
                <span style={{ fontSize: '0.64rem', color: isContact ? '#b45309' : '#64748b', fontFamily: 'monospace' }}>
                  {deltaF === 0 ? '0.0s' : `${deltaF > 0 ? '+' : ''}${(deltaF / fps).toFixed(2)}s`}
                </span>
              </button>
            );
          })}
        </div>

        {/* Dynamic Calculative Telemetry Inspector Drawer */}
        <div
          style={{
            background: '#ffffff',
            border: '1px solid #e2e8f0',
            borderRadius: '10px',
            padding: '12px 14px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '6px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Calculator size={14} color="#0284c7" />
              <span style={{ fontSize: '0.80rem', fontWeight: '800', color: '#0f172a' }}>
                Frame #{frameKinematics.frame} Kinematic Derivation
              </span>
              <span
                style={{
                  fontSize: '0.68rem',
                  fontWeight: '800',
                  padding: '1px 6px',
                  borderRadius: '4px',
                  background: `${frameKinematics.phaseColor}20`,
                  color: frameKinematics.phaseColor
                }}
              >
                {frameKinematics.phaseBadge}
              </span>
            </div>

            <div style={{ fontSize: '0.72rem', color: '#64748b', fontFamily: 'monospace' }}>
              t={frameKinematics.time.toFixed(2)}s • &Delta;t={(frameKinematics.deltaSeconds >= 0 ? '+' : '') + frameKinematics.deltaSeconds.toFixed(2)}s
            </div>
          </div>

          {/* Calculative Metrics Grid for Active Frame */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(75px, 1fr))',
              gap: '6px'
            }}
          >
            {/* Elbow Angle */}
            <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '6px 8px', textAlign: 'center' }}>
              <div style={{ fontSize: '0.68rem', color: '#64748b', fontWeight: '600' }}>Elbow &theta;</div>
              <div style={{ fontSize: '0.88rem', fontWeight: '800', color: '#16a34a', marginTop: '1px' }}>
                {frameKinematics.elbowAngle !== null && frameKinematics.elbowAngle !== undefined ? `${Number(frameKinematics.elbowAngle).toFixed(1)}°` : '—'}
              </div>
            </div>

            {/* Shoulder Angle */}
            <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '6px 8px', textAlign: 'center' }}>
              <div style={{ fontSize: '0.68rem', color: '#64748b', fontWeight: '600' }}>Shoulder &theta;</div>
              <div style={{ fontSize: '0.88rem', fontWeight: '800', color: '#0284c7', marginTop: '1px' }}>
                {frameKinematics.shoulderAngle !== null && frameKinematics.shoulderAngle !== undefined ? `${Number(frameKinematics.shoulderAngle).toFixed(1)}°` : '—'}
              </div>
            </div>

            {/* Knee Angle */}
            <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '6px 8px', textAlign: 'center' }}>
              <div style={{ fontSize: '0.68rem', color: '#64748b', fontWeight: '600' }}>Knee &theta;</div>
              <div style={{ fontSize: '0.88rem', fontWeight: '800', color: '#ea580c', marginTop: '1px' }}>
                {frameKinematics.kneeAngle !== null && frameKinematics.kneeAngle !== undefined ? `${Number(frameKinematics.kneeAngle).toFixed(1)}°` : '—'}
              </div>
            </div>

            {/* Hip Angle */}
            <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '6px 8px', textAlign: 'center' }}>
              <div style={{ fontSize: '0.68rem', color: '#64748b', fontWeight: '600' }}>Hip &theta;</div>
              <div style={{ fontSize: '0.88rem', fontWeight: '800', color: '#9333ea', marginTop: '1px' }}>
                {frameKinematics.hipAngle !== null && frameKinematics.hipAngle !== undefined ? `${Number(frameKinematics.hipAngle).toFixed(1)}°` : '—'}
              </div>
            </div>

            {/* Wrist Speed Estimate */}
            <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '6px 8px', textAlign: 'center' }}>
              <div style={{ fontSize: '0.68rem', color: '#64748b', fontWeight: '600' }}>Est. Velocity</div>
              <div style={{ fontSize: '0.88rem', fontWeight: '800', color: '#db2777', marginTop: '1px' }}>
                {frameKinematics.wristSpeedEstimate ? `${frameKinematics.wristSpeedEstimate} km/h` : '—'}
              </div>
            </div>
          </div>

          <div style={{ fontSize: '0.70rem', color: '#64748b', fontStyle: 'italic', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span>Phase: <strong>{frameKinematics.phaseName}</strong>. Derived via MediaPipe 3D arccos dot-product angles.</span>
          </div>
        </div>
      </div>

      {/* Contact Joint Kinematics Summary (Section 42) */}
      {(apexElbowAngle || apexShoulderAngle || apexKneeAngle || apexHipAngle) && (
        <div>
          <div style={{ fontSize: '0.82rem', fontWeight: '800', color: '#0f172a', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Activity size={15} color="#16a34a" />
            <span>Contact Apex Kinematics (Section 42 Arccos Standard)</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(70px, 1fr))', gap: '8px' }}>
            {apexElbowAngle && (
              <div style={{ background: '#f8fafc', padding: '8px', borderRadius: '8px', textAlign: 'center', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: '600' }}>Elbow Extension</div>
                <div style={{ fontSize: '0.95rem', fontWeight: '800', color: '#16a34a', marginTop: '2px' }}>
                  {Number(apexElbowAngle).toFixed(1)}°
                </div>
              </div>
            )}
            {apexShoulderAngle && (
              <div style={{ background: '#f8fafc', padding: '8px', borderRadius: '8px', textAlign: 'center', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: '600' }}>Shoulder Reach</div>
                <div style={{ fontSize: '0.95rem', fontWeight: '800', color: '#0284c7', marginTop: '2px' }}>
                  {Number(apexShoulderAngle).toFixed(1)}°
                </div>
              </div>
            )}
            {apexKneeAngle && (
              <div style={{ background: '#f8fafc', padding: '8px', borderRadius: '8px', textAlign: 'center', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: '600' }}>Knee Flexion</div>
                <div style={{ fontSize: '0.95rem', fontWeight: '800', color: '#ea580c', marginTop: '2px' }}>
                  {Number(apexKneeAngle).toFixed(1)}°
                </div>
              </div>
            )}
            {apexHipAngle && (
              <div style={{ background: '#f8fafc', padding: '8px', borderRadius: '8px', textAlign: 'center', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: '600' }}>Hip Trunk</div>
                <div style={{ fontSize: '0.95rem', fontWeight: '800', color: '#9333ea', marginTop: '2px' }}>
                  {Number(apexHipAngle).toFixed(1)}°
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Velocities per Shot */}
      {(racketSpeed?.available || shuttleSpeed?.available) && (
        <div style={{ display: 'grid', gridTemplateColumns: (racketSpeed?.available && shuttleSpeed?.available) ? '1fr 1fr' : '1fr', gap: '10px' }}>
          {racketSpeed?.available && (
            <div style={{ background: '#f8fafc', padding: '10px 12px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
              <div style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: '600' }}>Racket Velocity</div>
              <div style={{ fontSize: '0.95rem', fontWeight: '800', color: '#9333ea', marginTop: '2px' }}>
                {racketSpeed.value} {racketSpeed.unit}
              </div>
            </div>
          )}

          {shuttleSpeed?.available && (
            <div style={{ background: '#f8fafc', padding: '10px 12px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
              <div style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: '600' }}>Shuttle Velocity</div>
              <div style={{ fontSize: '0.95rem', fontWeight: '800', color: '#db2777', marginTop: '2px' }}>
                {shuttleSpeed.value} {shuttleSpeed.unit}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Linked Graph Node Traceability (Section 53) */}
      {graphNodeId && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '0.78rem',
            color: '#64748b',
            background: '#f8fafc',
            padding: '8px 12px',
            borderRadius: '8px',
            border: '1px solid #e2e8f0'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <GitFork size={14} color="#0284c7" />
            <span>Graph Node:</span>
            <code style={{ color: '#0369a1', background: '#e0f2fe', padding: '2px 6px', borderRadius: '4px', fontWeight: '700' }}>
              {graphNodeId}
            </code>
          </div>
          {onViewInGraph && (
            <button
              onClick={() => onViewInGraph(graphNodeId)}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#0284c7',
                cursor: 'pointer',
                fontSize: '0.75rem',
                fontWeight: '700',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                padding: '2px 6px'
              }}
              title="Focus node in Causal Evidence Graph"
            >
              <span>Inspect in Graph</span>
              <ExternalLink size={12} />
            </button>
          )}
        </div>
      )}
    </div>
  );
}

