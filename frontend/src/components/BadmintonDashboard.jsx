import React, { useState, useRef } from 'react';
import {
  Activity, Video, UploadCloud, Play, Sparkles, RefreshCw, AlertCircle,
  CheckCircle2, Compass, Layers, GitFork, MessageSquare, Send, HelpCircle, FileText,
  X, Eye, ArrowRight
} from 'lucide-react';
import {
  analyzeBadmintonVideo,
  analyzeBadmintonSample,
  getBadmintonSampleVideoUrl,
  askBadmintonQuestion
} from '../api/client';

import { BadmintonQualityBanner } from './BadmintonQualityBanner';
import { BadmintonMetricsPanel } from './BadmintonMetricsPanel';
import { CourtHeatmap } from './CourtHeatmap';
import { MovementTrajectory } from './MovementTrajectory';
import { ShotTimeline } from './ShotTimeline';
import { ShotDistribution } from './ShotDistribution';
import { ShotDetailCard } from './ShotDetailCard';
import { PerformanceRadar } from './PerformanceRadar';
import { BadmintonFindings } from './BadmintonFindings';
import { BadmintonVideoPlayer } from './BadmintonVideoPlayer';
import { KnowledgeGraphCanvas } from './KnowledgeGraphCanvas';
import { MarkdownResponse } from './MarkdownResponse';

/**
 * BadmintonDashboard (Section 29)
 * Master orchestrator for Badminton Biomechanics Video Analysis.
 * Strictly adheres to Section 47: Thin renderer only — never calculates
 * scientific metrics itself, only renders what the verified backend returns.
 */
export function BadmintonDashboard({ onRegisterToChat = null, initialResult = null, initialFile = null }) {
  // Intake metadata state
  const [playerAge, setPlayerAge] = useState(23);
  const [playerWeightKg, setPlayerWeightKg] = useState(72.0);
  const [sessionDurationMin, setSessionDurationMin] = useState(45.0);
  const [skillLevel, setSkillLevel] = useState('intermediate');
  const [matchType, setMatchType] = useState('singles');

  // Video & Processing state
  const [selectedFile, setSelectedFile] = useState(initialFile);
  const [videoPreviewUrl, setVideoPreviewUrl] = useState(() => {
    if (initialFile) {
      try {
        return URL.createObjectURL(initialFile);
      } catch (e) {
        return null;
      }
    }
    return null;
  });
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStage, setProcessingStage] = useState('');
  const [analysisResult, setAnalysisResult] = useState(initialResult);
  const [error, setError] = useState(null);

  React.useEffect(() => {
    if (!isProcessing) {
      setProcessingStage('');
      return;
    }
    const stages = [
      'Decoding video stream and assessing camera stability...',
      'Running MediaPipe 33-landmark 3D pose estimation & temporal smoothing...',
      'Detecting court line intersections and computing metric homography...',
      'Fusing multimodal signals to detect strokes & contact joint angles...',
      'Synthesizing Causal Evidence Graph & retrieving RAG coaching recommendations...'
    ];
    let idx = 0;
    setProcessingStage(stages[0]);
    const timer = setInterval(() => {
      idx = (idx + 1) % stages.length;
      setProcessingStage(stages[idx]);
    }, 3500);
    return () => clearInterval(timer);
  }, [isProcessing]);

  // Active sub-views & selections (Section 53 Bidirectional Evidence Loop)
  const [activeTab, setActiveTab] = useState('overview'); // 'overview', 'shots', 'court', 'graph', 'qa'
  const [selectedShot, setSelectedShot] = useState(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const [activeFindingId, setActiveFindingId] = useState(null);
  const [evidenceFeedback, setEvidenceFeedback] = useState(null);

  // Q&A state
  const [userQuestion, setUserQuestion] = useState('');
  const [isAsking, setIsAsking] = useState(false);
  const [qaHistory, setQaHistory] = useState([]);
  const fileInputRef = useRef(null);

  // Synchronize initialResult or initialFile props
  React.useEffect(() => {
    if (initialResult) {
      setAnalysisResult(initialResult);
      if (initialResult.shots && initialResult.shots.length > 0) {
        setSelectedShot(initialResult.shots[0]);
        setSelectedNodeId(`shot_${initialResult.shots[0].shot_id}`);
      }
    }
  }, [initialResult]);

  /**
   * Section 53 / Task 1: Wire ShotTimeline clicks to:
   * 1. Seek VideoTimelineScrubber to the shot's real contact_time
   * 2. Highlight the corresponding KnowledgeGraphCanvas node
   * 3. Open ShotDetailCard with that shot's real evidence_frames
   */
  const handleSelectShot = (shot) => {
    if (!shot) return;
    setSelectedShot(shot);
    const targetTime = shot.contact_time ?? shot.start_time ?? 0;
    setCurrentTime(targetTime);

    // Resolve corresponding graph node ID
    const shotNodeId = `shot_${shot.shot_id}`;
    const matchingNode = analysisResult?.graph_data?.nodes?.find(
      (n) => n.id === shotNodeId || n.id === shot.shot_id || (n.id && n.id.includes(shot.shot_id))
    );
    const resolvedNodeId = matchingNode ? matchingNode.id : shotNodeId;
    setSelectedNodeId(resolvedNodeId);
    setActiveFindingId(shot.shot_id);

    const evidenceCount = (shot.evidence_frames || []).length || 1;
    setEvidenceFeedback({
      type: 'shot',
      title: `Stroke #${shot.shot_id} (${(shot.shot_type || 'UNKNOWN').toUpperCase()})`,
      timestamp: targetTime,
      nodeId: resolvedNodeId,
      evidenceCount,
      message: `Selected Stroke #${shot.shot_id} (${shot.shot_type}) | Contact t=${targetTime.toFixed(2)}s | Graph Node: [${resolvedNodeId}]`
    });
  };

  /**
   * Section 53 / Task 2: Bidirectional evidence loop:
   * Clicking a finding in BadmintonFindings jumps back to its source video timestamp
   * and highlights its graph node, using the source metadata already attached.
   */
  const handleSelectFinding = (recOrFinding) => {
    if (!recOrFinding) return;
    const sourceId = recOrFinding.source_finding_id || recOrFinding.id || (typeof recOrFinding === 'string' ? recOrFinding : '');
    setActiveFindingId(sourceId);

    let targetTime = 0;
    let targetNodeId = sourceId;
    let matchedShot = null;

    // A. Joint Kinematics findings (e.g. joint_contact_elbow_angle)
    if (sourceId.includes('elbow') || sourceId.includes('joint')) {
      matchedShot = (analysisResult?.shots || []).find((s) => {
        const pf = s.pose_features || s.contact_joint_angles || {};
        return pf.contact_elbow_angle_deg !== undefined || pf.elbow_angle_deg !== undefined;
      }) || analysisResult?.shots?.[0];

      if (matchedShot) {
        targetTime = matchedShot.contact_time ?? matchedShot.start_time ?? 0;
        const candidateJointId = `joint_${matchedShot.shot_id}_elbow`;
        const exists = analysisResult?.graph_data?.nodes?.some((n) => n.id === candidateJointId);
        targetNodeId = exists ? candidateJointId : `shot_${matchedShot.shot_id}`;
        setSelectedShot(matchedShot);
      }
    }
    // B. Spatial Left Space Hypothesis (Section 11)
    else if (sourceId.includes('left_space') || sourceId.includes('spatial')) {
      targetNodeId = 'hypo_left_space_underutilization';
      targetTime = 0.0;
    }
    // General Hypothesis reference
    else if (sourceId.startsWith('hypo_')) {
      targetNodeId = sourceId;
      const matchedNode = analysisResult?.graph_data?.nodes?.find((n) => n.id === sourceId || n.id.includes(sourceId));
      if (matchedNode) {
        targetNodeId = matchedNode.id;
      }
      targetTime = 0.0;
    }
    // C. Movement Dynamics (Section 20/21)
    else if (sourceId.includes('movement')) {
      targetNodeId = 'movement_dynamics';
      targetTime = 0.0;
    }
    // D. Energy Expenditure & Load Nutrition (Section 22/23)
    else if (sourceId.includes('energy') || sourceId.includes('nutrition')) {
      targetNodeId = 'energy_expenditure';
      targetTime = 0.0;
    }
    // E. Direct Shot reference
    else {
      matchedShot = (analysisResult?.shots || []).find(
        (s) => s.shot_id === sourceId || `shot_${s.shot_id}` === sourceId
      );
      if (matchedShot) {
        targetTime = matchedShot.contact_time ?? matchedShot.start_time ?? 0;
        targetNodeId = `shot_${matchedShot.shot_id}`;
        setSelectedShot(matchedShot);
      } else {
        const nodeMatch = analysisResult?.graph_data?.nodes?.find(
          (n) => n.id === sourceId || n.id.includes(sourceId)
        );
        if (nodeMatch) {
          targetNodeId = nodeMatch.id;
          if (nodeMatch.properties?.contact_time !== undefined) {
            targetTime = Number(nodeMatch.properties.contact_time);
          }
        }
      }
    }

    setCurrentTime(targetTime);
    setSelectedNodeId(targetNodeId);

    setEvidenceFeedback({
      type: 'finding',
      title: recOrFinding.title || `Finding: ${sourceId}`,
      timestamp: targetTime,
      nodeId: targetNodeId,
      message: `Corroborating evidence focused for [${recOrFinding.title || sourceId}] | t=${targetTime.toFixed(2)}s | Graph Node: [${targetNodeId}]`
    });

    setTimeout(() => {
      const playerEl = document.getElementById('badminton-video-player');
      if (playerEl) {
        playerEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }, 50);
  };

  /**
   * Bidirectional Graph Node Selection:
   * Clicking a node in KnowledgeGraphCanvas synchronizes the video player,
   * stroke timeline, and ShotDetailCard.
   */
  const handleSelectGraphNode = (nodeId) => {
    setSelectedNodeId(nodeId);
    if (!nodeId) return;

    if (nodeId.startsWith('shot_') || nodeId.startsWith('type_') || nodeId.startsWith('joint_') || nodeId.startsWith('seq_')) {
      const matchedShot = (analysisResult?.shots || []).find((s) => nodeId.includes(s.shot_id));
      if (matchedShot) {
        setSelectedShot(matchedShot);
        const targetTime = matchedShot.contact_time ?? matchedShot.start_time ?? 0;
        setCurrentTime(targetTime);
        setActiveFindingId(matchedShot.shot_id);
        setEvidenceFeedback({
          type: 'graph_node',
          title: `Graph Selection: ${nodeId}`,
          timestamp: targetTime,
          nodeId,
          message: `Graph focus [${nodeId}] synchronized video to t=${targetTime.toFixed(2)}s and opened stroke detail.`
        });
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setVideoPreviewUrl(URL.createObjectURL(file));
      setError(null);
    }
  };

  const handleRunAnalysis = async () => {
    if (!selectedFile) {
      setError('Please select a video file or load the sample video.');
      return;
    }

    setIsProcessing(true);
    setError(null);
    try {
      const metadata = {
        age: playerAge,
        body_weight_kg: playerWeightKg,
        session_duration_min: sessionDurationMin,
        skill_level: skillLevel,
        match_type: matchType
      };
      const data = await analyzeBadmintonVideo(selectedFile, metadata);
      setAnalysisResult(data);
      if (data.shots && data.shots.length > 0) {
        setSelectedShot(data.shots[0]);
        setSelectedNodeId(`shot_${data.shots[0].shot_id}`);
      }
      if (onRegisterToChat) onRegisterToChat(data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Badminton video processing failed.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleLoadSample = async () => {
    setIsProcessing(true);
    setError(null);
    setVideoPreviewUrl(getBadmintonSampleVideoUrl());
    try {
      const data = await analyzeBadmintonSample();
      setAnalysisResult(data);
      if (data.shots && data.shots.length > 0) {
        setSelectedShot(data.shots[0]);
        setSelectedNodeId(`shot_${data.shots[0].shot_id}`);
      }
      if (onRegisterToChat) onRegisterToChat(data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to analyze sample badminton clip.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleAskQuestion = async (e) => {
    e.preventDefault();
    if (!userQuestion.trim() || !analysisResult?.analysis_id) return;

    const q = userQuestion.trim();
    setUserQuestion('');
    setIsAsking(true);
    try {
      const resp = await askBadmintonQuestion(analysisResult.analysis_id, q);
      setQaHistory((prev) => [...prev, { question: q, answer: resp.answer || resp.answer_summary || 'Analysis complete.', status: resp.status }]);
    } catch (err) {
      setQaHistory((prev) => [...prev, { question: q, answer: err.response?.data?.detail || err.message || 'Query failed.', status: 'ERROR' }]);
    } finally {
      setIsAsking(false);
    }
  };

  return (
    <div
      className="badminton-dashboard-container"
      style={{
        padding: '24px',
        maxWidth: '1280px',
        margin: '0 auto',
        color: '#0f172a',
        display: 'flex',
        flexDirection: 'column',
        gap: '20px'
      }}
    >
      {/* 1. Dashboard Header Banner */}
      <div
        style={{
          background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
          border: '1px solid #e2e8f0',
          borderRadius: '16px',
          padding: '24px',
          boxShadow: '0 4px 20px -2px rgba(0,0,0,0.04)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div
                style={{
                  background: 'linear-gradient(135deg, #0284c7, #0ea5e9)',
                  color: '#ffffff',
                  padding: '10px',
                  borderRadius: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 4px 12px rgba(14,165,233,0.25)'
                }}
              >
                <Activity size={24} />
              </div>
              <div>
                <h1 style={{ fontSize: '1.45rem', fontWeight: '800', color: '#0f172a', margin: 0, letterSpacing: '-0.02em' }}>
                  Badminton Biomechanics & Kinematics Studio
                </h1>
                <p style={{ fontSize: '0.86rem', color: '#64748b', margin: '4px 0 0 0' }}>
                  Multi-modal stroke detection, 3D court calibration homography, and causal coaching action plans.
                </p>
              </div>
            </div>
          </div>

          {/* Action & Intake Controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept="video/*"
              style={{ display: 'none' }}
            />

            {/* Match Type */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: '#fff', border: '1px solid #cbd5e1', borderRadius: '10px', padding: '6px 12px' }}>
              <span style={{ fontSize: '0.82rem', fontWeight: '600', color: '#475569' }}>Format:</span>
              <select
                value={matchType}
                onChange={(e) => setMatchType(e.target.value)}
                style={{ border: 'none', background: 'transparent', fontWeight: '700', color: '#0f172a', outline: 'none', cursor: 'pointer', fontSize: '0.84rem' }}
              >
                <option value="singles">Singles</option>
                <option value="doubles">Doubles</option>
              </select>
            </div>

            {/* Skill Level */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: '#fff', border: '1px solid #cbd5e1', borderRadius: '10px', padding: '6px 12px' }}>
              <span style={{ fontSize: '0.82rem', fontWeight: '600', color: '#475569' }}>Skill:</span>
              <select
                value={skillLevel}
                onChange={(e) => setSkillLevel(e.target.value)}
                style={{ border: 'none', background: 'transparent', fontWeight: '700', color: '#0f172a', outline: 'none', cursor: 'pointer', fontSize: '0.84rem' }}
              >
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
                <option value="elite">Elite / Pro</option>
              </select>
            </div>

            {/* Upload Video Button */}
            <button
              onClick={() => fileInputRef.current?.click()}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                background: '#f1f5f9',
                color: '#334155',
                border: '1px solid #cbd5e1',
                padding: '9px 16px',
                borderRadius: '10px',
                fontWeight: '600',
                fontSize: '0.85rem',
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
              title="Upload your own badminton video file"
            >
              <UploadCloud size={16} />
              <span>{selectedFile ? `File: ${selectedFile.name.slice(0, 14)}...` : 'Upload Video'}</span>
            </button>

            {/* Run Analysis Button if file selected */}
            {selectedFile && (
              <button
                onClick={handleRunAnalysis}
                disabled={isProcessing}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  background: '#0284c7',
                  color: '#ffffff',
                  border: 'none',
                  padding: '9px 18px',
                  borderRadius: '10px',
                  fontWeight: '700',
                  fontSize: '0.85rem',
                  cursor: isProcessing ? 'not-allowed' : 'pointer',
                  boxShadow: '0 2px 10px rgba(2,132,199,0.25)',
                  transition: 'all 0.15s ease'
                }}
              >
                {isProcessing ? <RefreshCw size={15} className="spin" /> : <Sparkles size={15} />}
                <span>{isProcessing ? 'Analyzing...' : 'Run Analysis'}</span>
              </button>
            )}

            {/* Load Sample Button */}
            <button
              onClick={handleLoadSample}
              disabled={isProcessing}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                background: '#0f172a',
                color: '#ffffff',
                border: 'none',
                padding: '9px 18px',
                borderRadius: '10px',
                fontWeight: '600',
                fontSize: '0.86rem',
                cursor: isProcessing ? 'not-allowed' : 'pointer',
                boxShadow: '0 2px 10px rgba(15,23,42,0.12)',
                transition: 'all 0.15s ease'
              }}
            >
              <Play size={15} />
              <span>{isProcessing ? 'Processing...' : 'Load Sample Rally'}</span>
            </button>
          </div>
        </div>

        {/* Video Upload Drop Area (Only visible before analysis or to change video) */}
        {!analysisResult && (
          <div
            style={{
              marginTop: '20px',
              border: '2px dashed #cbd5e1',
              borderRadius: '12px',
              padding: '24px',
              textAlign: 'center',
              background: '#ffffff'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '8px' }}>
              <Video size={32} color="#0284c7" />
              <div style={{ fontSize: '0.94rem', fontWeight: '700', color: '#1e293b' }}>
                {selectedFile ? `Selected: ${selectedFile.name}` : 'Upload Badminton Rally Video'}
              </div>
              <div style={{ fontSize: '0.82rem', color: '#64748b' }}>
                Full-court view with visible lines or baseline perspective. Supports MP4, MOV, WebM.
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  style={{
                    background: '#f1f5f9',
                    border: '1px solid #cbd5e1',
                    borderRadius: '8px',
                    padding: '8px 18px',
                    fontWeight: '600',
                    fontSize: '0.85rem',
                    cursor: 'pointer',
                    color: '#334155'
                  }}
                >
                  Browse Video
                </button>

                {selectedFile && (
                  <button
                    onClick={handleRunAnalysis}
                    disabled={isProcessing}
                    style={{
                      background: '#0284c7',
                      color: '#ffffff',
                      border: 'none',
                      borderRadius: '8px',
                      padding: '8px 20px',
                      fontWeight: '700',
                      fontSize: '0.85rem',
                      cursor: isProcessing ? 'not-allowed' : 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      boxShadow: '0 2px 10px rgba(2,132,199,0.25)'
                    }}
                  >
                    {isProcessing ? <RefreshCw size={15} className="spin" /> : <Sparkles size={15} />}
                    <span>{isProcessing ? 'Analyzing...' : 'Run Kinematics Analysis'}</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Error Banner */}
      {error && (
        <div
          style={{
            background: '#fef2f2',
            border: '1px solid #fecaca',
            color: '#b91c1c',
            borderRadius: '10px',
            padding: '12px 16px',
            fontSize: '0.86rem',
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
          }}
        >
          <AlertCircle size={18} color="#dc2626" />
          <span>{error}</span>
        </div>
      )}

      {/* Dynamic Processing Progress Indicator */}
      {isProcessing && (
        <div
          style={{
            background: '#ffffff',
            border: '1px solid #e2e8f0',
            borderRadius: '16px',
            padding: '36px 24px',
            textAlign: 'center',
            boxShadow: '0 4px 20px -2px rgba(0,0,0,0.04)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '12px'
          }}
        >
          <div style={{ display: 'inline-block', animation: 'spin 1.5s linear infinite' }}>
            <RefreshCw size={36} color="#0284c7" />
          </div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: '800', color: '#0f172a', margin: 0 }}>
            Analyzing Badminton Biomechanics & Court Space...
          </h3>
          <p style={{ fontSize: '0.88rem', color: '#0284c7', fontWeight: '600', maxWidth: '580px', margin: 0 }}>
            {processingStage || 'Processing rally frames...'}
          </p>
          <p style={{ fontSize: '0.78rem', color: '#64748b', maxWidth: '520px', margin: 0 }}>
            Sequential BlazePose inference, court homography calibration, and causal evidence graph construction.
          </p>
        </div>
      )}

      {/* Quality Banner */}
      {analysisResult && !isProcessing && (
        <BadmintonQualityBanner
          quality={analysisResult.quality}
          courtCalibration={analysisResult.court_calibration}
          playerMetadata={analysisResult.player_metadata}
          enhancement={analysisResult.enhancement || analysisResult.video?.enhancement}
        />
      )}

      {/* Section 53 Evidence Jump Banner */}
      {evidenceFeedback && (
        <div
          style={{
            background: '#f0f9ff',
            border: '1px solid #bae6fd',
            borderRadius: '10px',
            padding: '10px 16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '12px',
            flexWrap: 'wrap'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <Sparkles size={17} color="#0284c7" />
            <span style={{ fontSize: '0.84rem', color: '#0369a1', fontWeight: '700' }}>
              {evidenceFeedback.message}
            </span>
            <span style={{ fontSize: '0.74rem', background: '#e0f2fe', color: '#0369a1', padding: '2px 8px', borderRadius: '6px', fontFamily: 'monospace', fontWeight: '700' }}>
              t={evidenceFeedback.timestamp.toFixed(2)}s
            </span>
            <span style={{ fontSize: '0.74rem', background: '#f3e8ff', color: '#7e22ce', padding: '2px 8px', borderRadius: '6px', fontFamily: 'monospace', fontWeight: '700' }}>
              node: {evidenceFeedback.nodeId}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {activeTab !== 'graph' && (
              <button
                onClick={() => setActiveTab('graph')}
                style={{
                  background: '#0284c7',
                  border: 'none',
                  borderRadius: '6px',
                  color: '#ffffff',
                  padding: '4px 10px',
                  fontSize: '0.74rem',
                  fontWeight: '700',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
                title="Inspect node in Causal Evidence Graph"
              >
                <span>Inspect in Graph</span>
                <ArrowRight size={13} />
              </button>
            )}
            {activeTab !== 'overview' && (
              <button
                onClick={() => setActiveTab('overview')}
                style={{
                  background: '#ffffff',
                  border: '1px solid #cbd5e1',
                  borderRadius: '6px',
                  color: '#334155',
                  padding: '4px 10px',
                  fontSize: '0.74rem',
                  fontWeight: '700',
                  cursor: 'pointer'
                }}
              >
                <span>Video Overview &rarr;</span>
              </button>
            )}
            <button
              onClick={() => setEvidenceFeedback(null)}
              style={{ background: 'transparent', border: 'none', color: '#64748b', cursor: 'pointer', padding: '2px' }}
              title="Dismiss notification"
            >
              <X size={16} />
            </button>
          </div>
        </div>
      )}

      {/* 3. Navigation View Tabs */}
      {analysisResult && (
        <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid #e2e8f0', paddingBottom: '8px', flexWrap: 'wrap' }}>
          {[
            { id: 'overview', label: 'Overview & Kinematics', icon: FileText },
            { id: 'graph', label: 'Causal Evidence Graph', icon: GitFork },
            { id: 'qa', label: 'Ask SAAR (Grounded Q&A)', icon: MessageSquare }
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '8px 16px',
                  fontSize: '0.84rem',
                  fontWeight: '700',
                  borderRadius: '8px',
                  border: 'none',
                  background: isActive ? '#0f172a' : '#f1f5f9',
                  color: isActive ? '#ffffff' : '#475569',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                <Icon size={15} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      )}

      {/* 4. Active Tab Content Views */}
      {analysisResult ? (
        <div>
          {/* TAB 1: Overview & Kinematics */}
          {activeTab === 'overview' && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1.25rem' }}>
              {/* Left Column: Video Playback & Stroke Timeline */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                <BadmintonVideoPlayer
                  videoUrl={videoPreviewUrl}
                  videoFile={selectedFile}
                  metadata={analysisResult.video}
                  poseFrames={analysisResult.pose_frames}
                  shots={analysisResult.shots}
                  activeShot={selectedShot}
                  currentTime={currentTime}
                  onSeek={(t) => setCurrentTime(t)}
                />
                <ShotTimeline
                  shots={analysisResult.shots}
                  activeShotId={selectedShot?.shot_id}
                  onSelectShot={handleSelectShot}
                  onSeek={(t) => setCurrentTime(t)}
                  duration={analysisResult.video?.duration_seconds || 10}
                  currentTime={currentTime}
                />
                {selectedShot && (
                  <ShotDetailCard
                    shot={selectedShot}
                    onClose={() => setSelectedShot(null)}
                    onSeek={(t) => setCurrentTime(t)}
                    currentTime={currentTime}
                    poseFrames={analysisResult.pose_frames}
                    fps={analysisResult.video?.fps || 30.0}
                    graphNodeId={selectedNodeId || (selectedShot ? `shot_${selectedShot.shot_id}` : null)}
                    onViewInGraph={(nodeId) => {
                      setSelectedNodeId(nodeId);
                      setActiveTab('graph');
                    }}
                  />
                )}
                <PerformanceRadar result={analysisResult} />
              </div>

              {/* Right Column: Physical Metrics, Tactical Heatmap, and Findings */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                <BadmintonMetricsPanel
                  movementMetrics={analysisResult.movement_metrics}
                  courtMetrics={analysisResult.court_metrics}
                  speedMetrics={analysisResult.speed_metrics}
                  energyMetrics={analysisResult.energy_metrics}
                  poseMetrics={analysisResult.pose_metrics}
                  shotMetrics={analysisResult.shot_metrics}
                  courtCalibration={analysisResult.court_calibration}
                />
                <ShotDistribution shotMetrics={analysisResult.shot_metrics} />
                <BadmintonFindings
                  findings={analysisResult.findings}
                  hypotheses={analysisResult.hypotheses}
                  recommendations={analysisResult.recommendations}
                  prioritizedRecommendations={analysisResult.prioritized_recommendations}
                  limitations={analysisResult.limitations}
                  onSendToChat={onRegisterToChat}
                  onSelectFinding={handleSelectFinding}
                  activeFindingId={activeFindingId}
                />
              </div>
            </div>
          )}

          {/* TAB 4: Knowledge Graph */}
          {activeTab === 'graph' && (
            <div style={{ height: '620px', background: '#ffffff', borderRadius: '16px', border: '1px solid #e2e8f0', boxShadow: '0 4px 20px -2px rgba(0,0,0,0.04)', overflow: 'hidden' }}>
              <KnowledgeGraphCanvas
                graphData={analysisResult.graph_data}
                selectedNodeId={selectedNodeId}
                onSelectNode={handleSelectGraphNode}
                theme="light"
                onSendToChat={onRegisterToChat}
              />
            </div>
          )}

          {/* TAB 5: Grounded Q&A (Ask SAAR) */}
          {activeTab === 'qa' && (
            <div style={{
              background: '#ffffff',
              border: '1px solid #e2e8f0',
              borderRadius: '16px',
              padding: '24px',
              boxShadow: '0 4px 20px -2px rgba(0,0,0,0.04)',
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem',
              maxWidth: '850px'
            }}>
              <div>
                <h4 style={{ margin: '0 0 4px 0', fontSize: '1rem', fontWeight: '800', color: '#0f172a' }}>
                  Grounded Biomechanical Q&A
                </h4>
                <div style={{ fontSize: '0.84rem', color: '#64748b' }}>
                  Ask questions grounded strictly in this rally's CV findings and missing-data protocol.
                </div>
              </div>

              {/* Q&A Query Form */}
              <form onSubmit={handleAskQuestion} style={{ display: 'flex', gap: '8px' }}>
                <input
                  type="text"
                  value={userQuestion}
                  onChange={(e) => setUserQuestion(e.target.value)}
                  placeholder="e.g. What was my average overhead elbow extension across all smashes?"
                  style={{
                    flex: 1,
                    padding: '10px 14px',
                    borderRadius: '10px',
                    border: '1px solid #cbd5e1',
                    background: '#ffffff',
                    color: '#0f172a',
                    fontSize: '0.86rem',
                    outline: 'none'
                  }}
                />
                <button
                  type="submit"
                  disabled={isAsking || !userQuestion.trim()}
                  style={{
                    padding: '10px 20px',
                    borderRadius: '10px',
                    background: '#0284c7',
                    color: '#ffffff',
                    border: 'none',
                    fontWeight: '700',
                    fontSize: '0.86rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    cursor: isAsking ? 'wait' : 'pointer',
                    boxShadow: '0 2px 8px rgba(2,132,199,0.2)'
                  }}
                >
                  {isAsking ? <RefreshCw size={15} className="spin" /> : <Send size={15} />}
                  <span>Ask</span>
                </button>
              </form>

              {/* History */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '0.5rem' }}>
                {qaHistory.map((item, idx) => (
                  <div
                    key={idx}
                    style={{
                      background: '#f8fafc',
                      border: '1px solid #e2e8f0',
                      borderRadius: '12px',
                      padding: '16px'
                    }}
                  >
                    <div style={{ fontWeight: '700', fontSize: '0.88rem', color: '#0284c7', marginBottom: '0.45rem' }}>
                      Q: {item.question}
                    </div>
                    <div style={{ fontSize: '0.84rem', color: '#334155', lineHeight: '1.5' }}>
                      <MarkdownResponse content={item.answer} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        /* Empty State Prompt */
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '48px 24px',
            background: '#ffffff',
            border: '2px dashed #cbd5e1',
            borderRadius: '16px',
            textAlign: 'center',
            gap: '1rem',
            boxShadow: '0 4px 20px -2px rgba(0,0,0,0.04)'
          }}
        >
          <div
            style={{
              width: '60px',
              height: '60px',
              borderRadius: '50%',
              background: '#f0f9ff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#0284c7'
            }}
          >
            <Activity size={32} />
          </div>
          <div>
            <h4 style={{ margin: '0 0 0.35rem 0', fontSize: '1.1rem', fontWeight: '800', color: '#0f172a' }}>
              No Active Badminton Video Analysis
            </h4>
            <p style={{ margin: 0, fontSize: '0.86rem', color: '#64748b', maxWidth: '460px' }}>
              Upload an athletic video clip above or click "Load Sample Rally" to run the verified badminton kinematics pipeline.
            </p>
          </div>
          <button
            onClick={handleLoadSample}
            disabled={isProcessing}
            style={{
              padding: '10px 22px',
              borderRadius: '10px',
              background: '#0f172a',
              color: '#ffffff',
              border: 'none',
              fontWeight: '700',
              fontSize: '0.86rem',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              cursor: 'pointer',
              boxShadow: '0 2px 10px rgba(15,23,42,0.15)'
            }}
          >
            <Play size={15} />
            <span>Load & Analyze Sample Video</span>
          </button>
        </div>
      )}
    </div>
  );
}
