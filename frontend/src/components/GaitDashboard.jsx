import React, { useState, useRef } from 'react';
import {
  Activity, Video, AlertCircle, CheckCircle2, Clock, Sparkles,
  Send, RefreshCw, ShieldCheck, ChevronRight, Play, Info, AlertTriangle
} from 'lucide-react';
import { analyzeGaitVideo, analyzeGaitSample, askGaitQuestion, getGaitSampleVideoUrl } from '../api/client';
import { MarkdownResponse } from './MarkdownResponse';

export function GaitDashboard({ onRegisterToChat }) {
  const [childAgeMonths, setChildAgeMonths] = useState(24);
  const [selectedFile, setSelectedFile] = useState(null);
  const [videoPreviewUrl, setVideoPreviewUrl] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [assessmentResult, setAssessmentResult] = useState(null);
  const [error, setError] = useState(null);

  // In-context Q&A state
  const [userQuestion, setUserQuestion] = useState('');
  const [isAsking, setIsAsking] = useState(false);
  const [qaHistory, setQaHistory] = useState([]);
  const fileInputRef = useRef(null);

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
      setError("Please select a video file first or use the sample video.");
      return;
    }

    setIsProcessing(true);
    setError(null);
    try {
      const data = await analyzeGaitVideo(selectedFile, childAgeMonths);
      setAssessmentResult(data);
      if (onRegisterToChat) {
        onRegisterToChat(data);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Gait analysis failed.");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleRunSample = async () => {
    setIsProcessing(true);
    setError(null);
    setVideoPreviewUrl(getGaitSampleVideoUrl());
    try {
      const data = await analyzeGaitSample(childAgeMonths);
      setAssessmentResult(data);
      if (onRegisterToChat) {
        onRegisterToChat(data);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Failed to load sample analysis.");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleAskQuestion = async (e) => {
    e.preventDefault();
    if (!userQuestion.trim() || !assessmentResult?.assessment_id) return;

    const qText = userQuestion.trim();
    setUserQuestion('');
    setIsAsking(true);

    try {
      const res = await askGaitQuestion(assessmentResult.assessment_id, qText);
      setQaHistory((prev) => [
        ...prev,
        {
          question: qText,
          answer: res.answer_summary || "No response generated.",
          terminology: res.terminology || []
        }
      ]);
    } catch (err) {
      setQaHistory((prev) => [
        ...prev,
        {
          question: qText,
          answer: `**Inquiry Notice**: ${err.response?.data?.detail || err.message || 'Unable to complete reasoning synthesis.'}`,
          terminology: []
        }
      ]);
    } finally {
      setIsAsking(false);
    }
  };

  const qualityConfidence = assessmentResult?.quality?.confidence || 'UNKNOWN';
  const isHighQuality = qualityConfidence === 'HIGH';
  const isMediumQuality = qualityConfidence === 'MEDIUM';
  const isLowQuality = qualityConfidence === 'LOW';
  const isRejected = qualityConfidence === 'REJECT' || assessmentResult?.status === 'rejected';

  return (
    <div className="gait-dashboard-container" style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Header Banner */}
      <div style={{
        background: 'linear-gradient(135deg, #f8fafc 0%, #eef2f6 100%)',
        border: '1px solid #e2e8f0',
        borderRadius: '16px',
        padding: '24px',
        marginBottom: '24px',
        boxShadow: '0 4px 20px -2px rgba(0,0,0,0.05)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{
                background: 'linear-gradient(135deg, #3b82f6, #06b6d4)',
                color: '#fff',
                padding: '10px',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <Activity size={24} />
              </div>
              <div>
                <h1 style={{ fontSize: '1.4rem', fontWeight: '700', color: '#0f172a', margin: 0 }}>
                  ToddleAI Gait Analysis Engine
                </h1>
                <p style={{ fontSize: '0.88rem', color: '#64748b', margin: '4px 0 0 0' }}>
                  Deterministic 33-point MediaPipe pose kinematics, cadence, symmetry, and age-referenced screening.
                </p>
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#fff', border: '1px solid #cbd5e1', borderRadius: '10px', padding: '6px 14px' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: '600', color: '#475569' }}>Child Age:</span>
              <select
                value={[14, 18, 24, 36, 48].includes(childAgeMonths) ? childAgeMonths : 'custom'}
                onChange={(e) => {
                  if (e.target.value !== 'custom') {
                    setChildAgeMonths(Number(e.target.value));
                  }
                }}
                style={{ border: 'none', background: 'transparent', fontWeight: '700', color: '#0f172a', outline: 'none', cursor: 'pointer' }}
              >
                <option value={14}>14 months (&lt;18m bracket)</option>
                <option value={18}>18 months (18–24m bracket)</option>
                <option value={24}>24 months (24–36m bracket)</option>
                <option value={36}>36 months (36–48m bracket)</option>
                <option value={48}>48 months (48m+ mature)</option>
                <option value="custom">Custom Age (months)...</option>
              </select>
              <input
                type="number"
                min="6"
                max="120"
                value={childAgeMonths}
                onChange={(e) => setChildAgeMonths(Math.max(6, Math.min(120, Number(e.target.value) || 6)))}
                style={{
                  width: '56px',
                  padding: '2px 6px',
                  border: '1px solid #cbd5e1',
                  borderRadius: '6px',
                  fontSize: '0.85rem',
                  fontWeight: '700',
                  color: '#0f172a'
                }}
                title="Enter exact age in months"
              />
              <span style={{ fontSize: '0.8rem', color: '#64748b' }}>mo</span>
            </div>

            <button
              onClick={handleRunSample}
              disabled={isProcessing}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                background: '#0f172a',
                color: '#fff',
                border: 'none',
                padding: '9px 18px',
                borderRadius: '10px',
                fontWeight: '600',
                fontSize: '0.88rem',
                cursor: isProcessing ? 'not-allowed' : 'pointer',
                boxShadow: '0 2px 10px rgba(15,23,42,0.15)'
              }}
            >
              <Play size={16} />
              {isProcessing ? 'Processing Video...' : 'Load Sample Walk Clip'}
            </button>
          </div>
        </div>

        {/* Video Upload Drop Area */}
        <div style={{
          marginTop: '20px',
          border: '2px dashed #cbd5e1',
          borderRadius: '12px',
          padding: '20px',
          textAlign: 'center',
          background: '#ffffff'
        }}>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept="video/*"
            style={{ display: 'none' }}
          />

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '8px' }}>
            <Video size={32} color="#3b82f6" />
            <div style={{ fontSize: '0.95rem', fontWeight: '600', color: '#1e293b' }}>
              {selectedFile ? `Selected: ${selectedFile.name}` : 'Upload Toddler Walking Video'}
            </div>
            <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
              Prerecorded 10–15s walking clip, side camera view at knee height.
            </div>

            <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
              <button
                onClick={() => fileInputRef.current?.click()}
                style={{
                  background: '#f1f5f9',
                  border: '1px solid #cbd5e1',
                  borderRadius: '8px',
                  padding: '7px 16px',
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
                    background: '#2563eb',
                    color: '#fff',
                    border: 'none',
                    borderRadius: '8px',
                    padding: '7px 18px',
                    fontWeight: '600',
                    fontSize: '0.85rem',
                    cursor: isProcessing ? 'not-allowed' : 'pointer'
                  }}
                >
                  {isProcessing ? 'Analyzing...' : 'Run Gait Analysis'}
                </button>
              )}
            </div>
          </div>

          {videoPreviewUrl && (
            <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <video
                src={videoPreviewUrl}
                controls
                playsInline
                style={{
                  maxWidth: '100%',
                  maxHeight: '320px',
                  borderRadius: '8px',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                  background: '#000'
                }}
              />
              <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '6px' }}>
                {assessmentResult?.video?.filename ? `Playback: ${assessmentResult.video.filename} (${assessmentResult.video.duration_seconds}s @ ${assessmentResult.video.fps} FPS)` : 'Active Video Stream'}
              </div>
            </div>
          )}
        </div>

        {error && (
          <div style={{
            marginTop: '16px',
            background: '#fef2f2',
            border: '1px solid #fecaca',
            color: '#b91c1c',
            borderRadius: '10px',
            padding: '12px 16px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            fontSize: '0.88rem'
          }}>
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Loading Indicator */}
      {isProcessing && (
        <div style={{
          background: '#fff',
          border: '1px solid #e2e8f0',
          borderRadius: '16px',
          padding: '40px 20px',
          textAlign: 'center',
          marginBottom: '24px'
        }}>
          <div style={{ display: 'inline-block', animation: 'spin 1.5s linear infinite' }}>
            <RefreshCw size={36} color="#3b82f6" />
          </div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#0f172a', marginTop: '16px' }}>
            Processing Toddler Gait Kinematics
          </h3>
          <p style={{ fontSize: '0.88rem', color: '#64748b', maxWidth: '500px', margin: '8px auto 0 auto' }}>
            Extracting 33-point MediaPipe landmarks, evaluating frame quality, detecting heel strikes, and computing temporal symmetry...
          </p>
        </div>
      )}

      {/* Results Dashboard */}
      {assessmentResult && !isProcessing && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Quality Assessment Banner */}
          <div style={{
            background: isRejected ? '#fef2f2' : (isHighQuality ? '#f0fdf4' : (isMediumQuality ? '#fefce8' : '#f8fafc')),
            border: `1px solid ${isRejected ? '#fecaca' : (isHighQuality ? '#bbf7d0' : (isMediumQuality ? '#fef08a' : '#e2e8f0'))}`,
            borderRadius: '14px',
            padding: '18px 22px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                {isHighQuality && <CheckCircle2 size={24} color="#16a34a" />}
                {isMediumQuality && <Info size={24} color="#ca8a04" />}
                {(isLowQuality || isRejected) && <AlertTriangle size={24} color="#dc2626" />}
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '0.95rem', fontWeight: '700', color: '#0f172a' }}>
                      Recording Quality:
                    </span>
                    <span style={{
                      fontSize: '0.8rem',
                      fontWeight: '700',
                      padding: '2px 8px',
                      borderRadius: '6px',
                      background: isHighQuality ? '#dcfce7' : (isMediumQuality ? '#fef9c3' : '#fee2e2'),
                      color: isHighQuality ? '#166534' : (isMediumQuality ? '#854d0e' : '#991b1b')
                    }}>
                      {qualityConfidence} CONFIDENCE
                    </span>
                  </div>
                  <div style={{ fontSize: '0.82rem', color: '#64748b', marginTop: '2px' }}>
                    {Math.round((assessmentResult.quality?.good_frame_ratio || 0) * 100)}% good continuous frames • {assessmentResult.metrics?.usable_step_count || 0} valid steps detected
                  </div>
                </div>
              </div>

              <div style={{ fontSize: '0.8rem', color: '#64748b', fontStyle: 'italic' }}>
                Assessment ID: <code>{assessmentResult.assessment_id}</code>
              </div>
            </div>

            {/* Quality Issues if any */}
            {assessmentResult.quality?.issues?.length > 0 && (
              <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid rgba(0,0,0,0.06)' }}>
                <div style={{ fontSize: '0.82rem', fontWeight: '600', color: '#475569', marginBottom: '6px' }}>
                  Capture Guidance & Observations:
                </div>
                <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '0.82rem', color: '#475569' }}>
                  {assessmentResult.quality.issues.map((issue, idx) => (
                    <li key={idx} style={{ marginBottom: '3px' }}>{issue}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Metric Cards Grid */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
            gap: '16px'
          }}>
            {/* Card 1: Cadence */}
            <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '20px', boxShadow: '0 2px 10px rgba(0,0,0,0.02)' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: '700', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Cadence
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginTop: '8px' }}>
                <span style={{ fontSize: '2rem', fontWeight: '800', color: '#0f172a' }}>
                  {assessmentResult.metrics?.cadence || 0}
                </span>
                <span style={{ fontSize: '0.9rem', color: '#64748b', fontWeight: '600' }}>steps/min</span>
              </div>
              <div style={{ marginTop: '10px', fontSize: '0.82rem', color: '#334155', background: '#f8fafc', padding: '8px 10px', borderRadius: '8px' }}>
                <strong>Typical (24m):</strong> {assessmentResult.cadence_range?.low}–{assessmentResult.cadence_range?.high} steps/min
              </div>
            </div>

            {/* Card 2: Step Times */}
            <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '20px', boxShadow: '0 2px 10px rgba(0,0,0,0.02)' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: '700', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Step Timing (L vs R)
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginTop: '8px' }}>
                <span style={{ fontSize: '2rem', fontWeight: '800', color: '#0f172a' }}>
                  {assessmentResult.metrics?.mean_step_time || 0}
                </span>
                <span style={{ fontSize: '0.9rem', color: '#64748b', fontWeight: '600' }}>sec (mean)</span>
              </div>
              <div style={{ marginTop: '10px', fontSize: '0.82rem', color: '#334155', background: '#f8fafc', padding: '8px 10px', borderRadius: '8px', display: 'flex', justifyContent: 'space-between' }}>
                <span><strong>Left:</strong> {assessmentResult.metrics?.left_mean_step_time}s</span>
                <span><strong>Right:</strong> {assessmentResult.metrics?.right_mean_step_time}s</span>
                <span><strong>Diff:</strong> {assessmentResult.metrics?.timing_difference_ms}ms</span>
              </div>
            </div>

            {/* Card 3: Left/Right Asymmetry */}
            <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '20px', boxShadow: '0 2px 10px rgba(0,0,0,0.02)' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: '700', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Temporal Symmetry
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginTop: '8px' }}>
                <span style={{ fontSize: '2rem', fontWeight: '800', color: '#0f172a' }}>
                  {assessmentResult.metrics?.step_time_asymmetry_pct || 0}%
                </span>
                <span style={{ fontSize: '0.9rem', color: '#64748b', fontWeight: '600' }}>asymmetry</span>
              </div>
              <div style={{ marginTop: '10px', fontSize: '0.82rem', color: '#334155', background: '#f8fafc', padding: '8px 10px', borderRadius: '8px' }}>
                <strong>Benchmark:</strong> Even step timing is typically within ≤ 10%
              </div>
            </div>

            {/* Card 4: Step-Time Variability */}
            <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '20px', boxShadow: '0 2px 10px rgba(0,0,0,0.02)' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: '700', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Step Rhythm Variability
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginTop: '8px' }}>
                <span style={{ fontSize: '2rem', fontWeight: '800', color: '#0f172a' }}>
                  {assessmentResult.metrics?.step_time_cov || 0}%
                </span>
                <span style={{ fontSize: '0.9rem', color: '#64748b', fontWeight: '600' }}>CoV</span>
              </div>
              <div style={{ marginTop: '10px', fontSize: '0.82rem', color: '#334155', background: '#f8fafc', padding: '8px 10px', borderRadius: '8px' }}>
                <strong>Developing Toddler:</strong> Rhythm variation typically ≤ 15%
              </div>
            </div>
          </div>

          {/* Structured ToddleAI Observations */}
          <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '24px' }}>
            <h3 style={{ fontSize: '1.05rem', fontWeight: '700', color: '#0f172a', margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ShieldCheck size={20} color="#3b82f6" />
              Non-Diagnostic Structured Observations
            </h3>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '14px' }}>
              {assessmentResult.observations?.map((obs, idx) => {
                const isTypical = obs.status === 'TYPICAL';
                return (
                  <div key={idx} style={{
                    border: '1px solid #e2e8f0',
                    borderRadius: '10px',
                    padding: '16px',
                    background: '#f8fafc'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <span style={{ fontSize: '0.78rem', fontWeight: '700', textTransform: 'uppercase', color: '#64748b' }}>
                        {obs.type}
                      </span>
                      <span style={{
                        fontSize: '0.75rem',
                        fontWeight: '700',
                        padding: '2px 8px',
                        borderRadius: '6px',
                        background: isTypical ? '#dcfce7' : '#fef3c7',
                        color: isTypical ? '#166534' : '#92400e'
                      }}>
                        {obs.status}
                      </span>
                    </div>

                    <div style={{ fontSize: '0.95rem', fontWeight: '700', color: '#0f172a', marginBottom: '6px' }}>
                      {obs.measurement}
                    </div>

                    <div style={{ fontSize: '0.82rem', color: '#475569', marginBottom: '6px' }}>
                      {obs.context}
                    </div>

                    <div style={{ fontSize: '0.8rem', fontWeight: '600', color: isTypical ? '#166534' : '#b45309' }}>
                      Note: {obs.note}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* WHO Milestone Text */}
            <div style={{ marginTop: '16px', padding: '12px 16px', background: '#eff6ff', borderRadius: '10px', border: '1px solid #bfdbfe', fontSize: '0.83rem', color: '#1e40af' }}>
              <strong>Developmental Context (WHO & Sutherland):</strong> {assessmentResult.milestone_context}
            </div>
          </div>

          {/* In-Assessment SAAR Q&A Assistant */}
          <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '24px' }}>
            <h3 style={{ fontSize: '1.05rem', fontWeight: '700', color: '#0f172a', margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Sparkles size={20} color="#8b5cf6" />
              Ask SAAR About This Assessment
            </h3>

            {/* Q&A Thread */}
            {qaHistory.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '20px' }}>
                {qaHistory.map((item, idx) => (
                  <div key={idx} style={{ border: '1px solid #e2e8f0', borderRadius: '12px', overflow: 'hidden' }}>
                    <div style={{ background: '#f8fafc', padding: '10px 16px', fontWeight: '700', fontSize: '0.88rem', color: '#1e293b', borderBottom: '1px solid #e2e8f0' }}>
                      Q: {item.question}
                    </div>
                    <div style={{ padding: '16px', fontSize: '0.9rem', color: '#0f172a', background: '#ffffff' }}>
                      <MarkdownResponse content={item.answer} />
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Prompt input */}
            <form onSubmit={handleAskQuestion} style={{ display: 'flex', gap: '10px' }}>
              <input
                type="text"
                value={userQuestion}
                onChange={(e) => setUserQuestion(e.target.value)}
                placeholder="Ask about cadence, asymmetry percentage, step time variation, or developmental benchmarks..."
                style={{
                  flex: 1,
                  padding: '11px 16px',
                  borderRadius: '10px',
                  border: '1px solid #cbd5e1',
                  fontSize: '0.9rem',
                  outline: 'none'
                }}
              />
              <button
                type="submit"
                disabled={isAsking || !userQuestion.trim()}
                style={{
                  background: 'linear-gradient(135deg, #4f46e5, #7c3aed)',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '10px',
                  padding: '11px 22px',
                  fontWeight: '600',
                  fontSize: '0.88rem',
                  cursor: (isAsking || !userQuestion.trim()) ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                <Send size={16} />
                {isAsking ? 'Reasoning...' : 'Ask SAAR'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
