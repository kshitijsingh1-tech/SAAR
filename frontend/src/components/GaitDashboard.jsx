import React, { useState, useRef, useMemo } from 'react';
import {
  Activity, Video, AlertCircle, CheckCircle2, Clock, Sparkles,
  Send, RefreshCw, ShieldCheck, ChevronRight, Play, Info, AlertTriangle,
  Layers, Compass, Scale, BarChart3, HelpCircle, FileText
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
  const [activeTab, setActiveTab] = useState('profile'); // 'profile', 'curves', 'cycles', 'qa'
  const [selectedCurveJoint, setSelectedCurveJoint] = useState('knee'); // 'knee', 'hip', 'ankle', 'trunk'
  const [hoveredTime, setHoveredTime] = useState(null);

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

  // Extract structured profiles (Section 12)
  const devSummary = assessmentResult?.developmental_summary;
  const gaitProfile = assessmentResult?.gait_profile;
  const temporal = gaitProfile?.temporal || assessmentResult?.temporal || assessmentResult?.metrics;
  const spatial = gaitProfile?.spatial || assessmentResult?.spatial;
  const symmetry = gaitProfile?.symmetry || assessmentResult?.symmetry;
  const jointMotion = gaitProfile?.joint_motion || assessmentResult?.joint_motion;
  const posture = gaitProfile?.posture || assessmentResult?.posture;
  const references = gaitProfile?.references || assessmentResult?.reference_comparisons || [];
  const curves = assessmentResult?.joint_angle_curves;

  return (

    <div className="gait-dashboard-container" style={{ padding: '24px', maxWidth: '1280px', margin: '0 auto', color: '#0f172a' }}>
      {/* Header Banner */}
      <div style={{
        background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
        border: '1px solid #e2e8f0',
        borderRadius: '16px',
        padding: '24px',
        marginBottom: '24px',
        boxShadow: '0 4px 20px -2px rgba(0,0,0,0.04)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{
                background: 'linear-gradient(135deg, #0284c7, #0ea5e9)',
                color: '#fff',
                padding: '10px',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 4px 12px rgba(14,165,233,0.25)'
              }}>
                <Activity size={24} />
              </div>
              <div>
                <h1 style={{ fontSize: '1.45rem', fontWeight: '800', color: '#0f172a', margin: 0, letterSpacing: '-0.02em' }}>
                  ToddleAI Child Walking Analysis
                </h1>
                <p style={{ fontSize: '0.86rem', color: '#64748b', margin: '4px 0 0 0' }}>
                  Video-based walking rhythm, leg movement balance, and age-matched developmental insights.
                </p>
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
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
                boxShadow: '0 2px 10px rgba(15,23,42,0.12)'
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
          padding: '18px',
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
            <Video size={30} color="#0284c7" />
            <div style={{ fontSize: '0.92rem', fontWeight: '600', color: '#1e293b' }}>
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
                    background: '#0284c7',
                    color: '#fff',
                    border: 'none',
                    borderRadius: '8px',
                    padding: '7px 18px',
                    fontWeight: '600',
                    fontSize: '0.85rem',
                    cursor: isProcessing ? 'not-allowed' : 'pointer'
                  }}
                >
                  {isProcessing ? 'Analyzing...' : 'Analyze Walking Video'}
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
                  maxHeight: '300px',
                  borderRadius: '8px',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                  background: '#000'
                }}
              />
              <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '6px' }}>
                {assessmentResult?.video?.filename ? `Video: ${assessmentResult.video.filename} (${assessmentResult.video.duration_seconds}s)` : 'Selected Video Clip'}
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
            <RefreshCw size={36} color="#0284c7" />
          </div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#0f172a', marginTop: '16px' }}>
            Analyzing Walking Pattern & Movement...
          </h3>
          <p style={{ fontSize: '0.88rem', color: '#64748b', maxWidth: '520px', margin: '8px auto 0 auto' }}>
            Tracking steps, measuring leg motion curves, and evaluating walking balance...
          </p>
        </div>
      )}

      {/* Results Dashboard */}
      {assessmentResult && !isProcessing && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          {/* Quality Assessment Banner */}
          <div style={{
            background: isRejected ? '#fef2f2' : (isHighQuality ? '#f0fdf4' : (isMediumQuality ? '#fefce8' : '#f8fafc')),
            border: `1px solid ${isRejected ? '#fecaca' : (isHighQuality ? '#bbf7d0' : (isMediumQuality ? '#fef08a' : '#e2e8f0'))}`,
            borderRadius: '14px',
            padding: '16px 20px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                {isHighQuality && <CheckCircle2 size={24} color="#16a34a" />}
                {isMediumQuality && <Info size={24} color="#ca8a04" />}
                {(isLowQuality || isRejected) && <AlertTriangle size={24} color="#dc2626" />}
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '0.95rem', fontWeight: '700', color: '#0f172a' }}>
                      Video Quality:
                    </span>
                    <span style={{
                      fontSize: '0.8rem',
                      fontWeight: '700',
                      padding: '2px 8px',
                      borderRadius: '6px',
                      background: isHighQuality ? '#dcfce7' : (isMediumQuality ? '#fef9c3' : '#fee2e2'),
                      color: isHighQuality ? '#166534' : (isMediumQuality ? '#854d0e' : '#991b1b')
                    }}>
                      {qualityConfidence === 'HIGH' ? 'Clear Video' : (qualityConfidence === 'MEDIUM' ? 'Acceptable Video' : 'Low Visibility')}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.82rem', color: '#64748b', marginTop: '2px' }}>
                    {Math.round((assessmentResult.quality?.good_frame_ratio || 0) * 100)}% clear frames • {temporal?.step_count || assessmentResult.metrics?.usable_step_count || 0} steps analyzed • Overall clarity: {Math.round((assessmentResult.pipeline_confidence || 0) * 100)}%
                  </div>
                </div>
              </div>

              <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                Report #{assessmentResult.assessment_id?.slice(-8) || '001'}
              </div>
            </div>
          </div>

          {/* Age Mismatch Update Banner */}
          {assessmentResult && childAgeMonths !== assessmentResult.child_age_months && (
            <div style={{
              background: '#f0f9ff',
              border: '1px solid #bae6fd',
              borderRadius: '12px',
              padding: '12px 18px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '12px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Info size={18} color="#0284c7" />
                <span style={{ fontSize: '0.86rem', color: '#0369a1' }}>
                  Age changed to <strong>{childAgeMonths} months</strong>. Current report is evaluated against <strong>{assessmentResult.child_age_months}mo</strong> norms.
                </span>
              </div>
              <button
                onClick={selectedFile ? handleRunAnalysis : handleRunSample}
                disabled={isProcessing}
                style={{
                  background: '#0284c7',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '6px 14px',
                  fontSize: '0.82rem',
                  fontWeight: '700',
                  cursor: isProcessing ? 'not-allowed' : 'pointer'
                }}
              >
                {isProcessing ? 'Updating...' : `Re-evaluate for ${childAgeMonths}mo`}
              </button>
            </div>
          )}

          {/* UNIFIED PARENT DEVELOPMENTAL MOBILITY SUMMARY CARD */}
          {devSummary && (
            <div style={{
              background: '#ffffff',
              border: '1px solid #e2e8f0',
              borderRadius: '16px',
              padding: '24px',
              boxShadow: '0 4px 20px -4px rgba(0,0,0,0.06)',
              display: 'flex',
              flexDirection: 'column',
              gap: '20px'
            }}>
              {/* Top Row: Overall Score & Status Badge */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '16px',
                paddingBottom: '16px',
                borderBottom: '1px solid #f1f5f9'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  {/* Score Gauge Circle */}
                  <div style={{
                    position: 'relative',
                    width: '76px',
                    height: '76px',
                    borderRadius: '50%',
                    background: devSummary.status_theme === 'green'
                      ? `conic-gradient(#16a34a 0% ${devSummary.overall_score}%, #e2e8f0 ${devSummary.overall_score}% 100%)`
                      : (devSummary.status_theme === 'amber'
                        ? `conic-gradient(#ca8a04 0% ${devSummary.overall_score}%, #e2e8f0 ${devSummary.overall_score}% 100%)`
                        : `conic-gradient(#dc2626 0% ${devSummary.overall_score}%, #e2e8f0 ${devSummary.overall_score}% 100%)`),
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '6px',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
                  }}>
                    <div style={{
                      width: '100%',
                      height: '100%',
                      borderRadius: '50%',
                      background: '#ffffff',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <span style={{ fontSize: '1.25rem', fontWeight: '800', color: '#0f172a', lineHeight: 1 }}>
                        {Math.round(devSummary.overall_score)}
                      </span>
                      <span style={{ fontSize: '0.62rem', fontWeight: '700', color: '#64748b' }}>/100</span>
                    </div>
                  </div>

                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{
                        fontSize: '0.82rem',
                        fontWeight: '700',
                        padding: '3px 10px',
                        borderRadius: '20px',
                        background: devSummary.status_theme === 'green' ? '#dcfce7' : (devSummary.status_theme === 'amber' ? '#fef9c3' : '#fee2e2'),
                        color: devSummary.status_theme === 'green' ? '#166534' : (devSummary.status_theme === 'amber' ? '#854d0e' : '#991b1b'),
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px'
                      }}>
                        {devSummary.status_theme === 'green' && <CheckCircle2 size={13} />}
                        {devSummary.status_theme === 'amber' && <Info size={13} />}
                        {devSummary.status_theme === 'red' && <AlertTriangle size={13} />}
                        {devSummary.status_title}
                      </span>
                      <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: '600' }}>
                        Evaluated for {assessmentResult.child_age_months || childAgeMonths} Months
                      </span>
                    </div>
                    <h2 style={{ fontSize: '1.18rem', fontWeight: '800', color: '#0f172a', margin: '6px 0 0 0', letterSpacing: '-0.01em' }}>
                      {devSummary.summary_headline}
                    </h2>
                  </div>
                </div>
              </div>

              {/* 4 Core Pillars Grid */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                gap: '14px'
              }}>
                {devSummary.pillars?.map((p, idx) => (
                  <div key={idx} style={{
                    background: '#f8fafc',
                    border: '1px solid #e2e8f0',
                    borderRadius: '12px',
                    padding: '16px',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    gap: '10px'
                  }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                        <span style={{ fontSize: '0.78rem', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.04em', color: '#64748b' }}>
                          {p.title}
                        </span>
                        <span style={{
                          fontSize: '0.75rem',
                          fontWeight: '700',
                          padding: '2px 8px',
                          borderRadius: '6px',
                          background: p.status === 'typical' ? '#dcfce7' : (p.status === 'mild_variation' ? '#fef9c3' : '#fee2e2'),
                          color: p.status === 'typical' ? '#166534' : (p.status === 'mild_variation' ? '#854d0e' : '#991b1b')
                        }}>
                          {p.badge}
                        </span>
                      </div>
                      <div style={{ fontSize: '0.92rem', fontWeight: '700', color: '#0f172a', marginBottom: '4px' }}>
                        {p.headline}
                      </div>
                      <div style={{ fontSize: '0.82rem', color: '#475569', lineHeight: 1.45 }}>
                        {p.explanation}
                      </div>
                    </div>
                    
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
                      <div style={{ flex: 1, height: '6px', background: '#e2e8f0', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{
                          height: '100%',
                          width: `${Math.min(100, Math.max(0, p.score))}%`,
                          background: p.score >= 80 ? '#16a34a' : (p.score >= 65 ? '#ca8a04' : '#dc2626'),
                          borderRadius: '3px'
                        }} />
                      </div>
                      <span style={{ fontSize: '0.75rem', fontWeight: '700', color: '#64748b' }}>
                        {Math.round(p.score)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Pediatrician Point & Parent Tips */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
                gap: '14px'
              }}>
                {/* Pediatrician Guidance */}
                <div style={{
                  background: '#f0f9ff',
                  border: '1px solid #bae6fd',
                  borderRadius: '12px',
                  padding: '16px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <ShieldCheck size={18} color="#0284c7" />
                    <span style={{ fontSize: '0.85rem', fontWeight: '700', color: '#0369a1' }}>
                      Pediatrician Discussion Point
                    </span>
                  </div>
                  <p style={{ fontSize: '0.84rem', color: '#0c4a6e', margin: 0, lineHeight: 1.45 }}>
                    {devSummary.pediatrician_discussion_point}
                  </p>
                </div>

                {/* Daily Play & Footwear Tips */}
                <div style={{
                  background: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  borderRadius: '12px',
                  padding: '16px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Sparkles size={18} color="#d97706" />
                    <span style={{ fontSize: '0.85rem', fontWeight: '700', color: '#475569' }}>
                      Developmental Guidance for Parents
                    </span>
                  </div>
                  <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '0.82rem', color: '#334155', lineHeight: 1.4 }}>
                    {devSummary.parent_tips?.map((tip, tIdx) => (
                      <li key={tIdx} style={{ marginBottom: '3px' }}>{tip}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Milestone Context Footer */}
              <div style={{
                background: '#f8fafc',
                borderRadius: '8px',
                padding: '10px 14px',
                fontSize: '0.78rem',
                color: '#64748b',
                borderLeft: '3px solid #0284c7'
              }}>
                <strong style={{ color: '#334155' }}>Milestone Context: </strong>
                {devSummary.milestone_context}
              </div>
            </div>
          )}

          {/* Navigation Sub-Tabs */}
          <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid #e2e8f0', paddingBottom: '8px', flexWrap: 'wrap' }}>
            <button
              onClick={() => setActiveTab('profile')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 16px',
                borderRadius: '8px',
                border: 'none',
                background: activeTab === 'profile' ? '#0f172a' : '#f1f5f9',
                color: activeTab === 'profile' ? '#fff' : '#475569',
                fontWeight: '700',
                fontSize: '0.85rem',
                cursor: 'pointer'
              }}
            >
              <FileText size={15} />
              Gait Overview
            </button>

            <button
              onClick={() => setActiveTab('curves')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 16px',
                borderRadius: '8px',
                border: 'none',
                background: activeTab === 'curves' ? '#0f172a' : '#f1f5f9',
                color: activeTab === 'curves' ? '#fff' : '#475569',
                fontWeight: '700',
                fontSize: '0.85rem',
                cursor: 'pointer'
              }}
            >
              <Activity size={15} />
              Joint Motion Curves
            </button>

            <button
              onClick={() => setActiveTab('cycles')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 16px',
                borderRadius: '8px',
                border: 'none',
                background: activeTab === 'cycles' ? '#0f172a' : '#f1f5f9',
                color: activeTab === 'cycles' ? '#fff' : '#475569',
                fontWeight: '700',
                fontSize: '0.85rem',
                cursor: 'pointer'
              }}
            >
              <BarChart3 size={15} />
              Step Balance Breakdown
            </button>

            <button
              onClick={() => setActiveTab('qa')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 16px',
                borderRadius: '8px',
                border: 'none',
                background: activeTab === 'qa' ? '#0f172a' : '#f1f5f9',
                color: activeTab === 'qa' ? '#fff' : '#475569',
                fontWeight: '700',
                fontSize: '0.85rem',
                cursor: 'pointer'
              }}
            >
              <HelpCircle size={15} />
              Ask SAAR Questions ({qaHistory.length})
            </button>
          </div>

          {/* TAB 1: GAIT PROFILE (Section 14) */}
          {activeTab === 'profile' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              
              {/* Category 1: Rhythm & Walking Pace */}
              <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '20px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                  <Clock size={18} color="#0284c7" />
                  <h3 style={{ fontSize: '1.05rem', fontWeight: '800', margin: 0, color: '#0f172a' }}>
                    1. Rhythm & Walking Pace
                  </h3>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px' }}>
                  <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: '700', color: '#64748b', textTransform: 'uppercase' }}>Cadence (Walking Steps)</div>
                    <div style={{ fontSize: '1.5rem', fontWeight: '800', color: '#0f172a', margin: '4px 0' }}>
                      {temporal?.cadence_steps_per_min || temporal?.cadence || 0} <span style={{ fontSize: '0.8rem', fontWeight: '500', color: '#64748b' }}>steps/min</span>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Expected for {assessmentResult.child_age_months || childAgeMonths}mo: {assessmentResult.cadence_range?.low}–{assessmentResult.cadence_range?.high} steps/min</div>
                  </div>

                  <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: '700', color: '#64748b', textTransform: 'uppercase' }}>Step Time</div>
                    <div style={{ fontSize: '1.5rem', fontWeight: '800', color: '#0f172a', margin: '4px 0' }}>
                      {temporal?.mean_step_time_sec || temporal?.mean_step_time || 0} <span style={{ fontSize: '0.8rem', fontWeight: '500', color: '#64748b' }}>s</span>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Average duration per step</div>
                  </div>

                  <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: '700', color: '#64748b', textTransform: 'uppercase' }}>Stride Time</div>
                    <div style={{ fontSize: '1.5rem', fontWeight: '800', color: '#0f172a', margin: '4px 0' }}>
                      {temporal?.mean_stride_time_sec ? `${temporal.mean_stride_time_sec} s` : 'N/A'}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Complete 2-step cycle time</div>
                  </div>

                  <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: '700', color: '#64748b', textTransform: 'uppercase' }}>Step Rhythm Consistency</div>
                    <div style={{ fontSize: '1.5rem', fontWeight: '800', color: (temporal?.step_time_variability_pct || temporal?.step_time_cov || 0) < 15 ? '#16a34a' : '#d97706', margin: '4px 0' }}>
                      {temporal?.step_time_variability_pct || temporal?.step_time_cov || 0}%
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Lower percentage indicates steady rhythm</div>
                  </div>
                </div>
              </div>

              {/* Category 2: Joint Motion & Flexibility */}
              <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '20px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                  <Activity size={18} color="#0284c7" />
                  <h3 style={{ fontSize: '1.05rem', fontWeight: '800', margin: 0, color: '#0f172a' }}>
                    2. Leg & Joint Motion
                  </h3>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
                  {/* Knee Joint */}
                  <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '16px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                      <span style={{ fontSize: '0.92rem', fontWeight: '800', color: '#0f172a' }}>Knee Bending & Straightening</span>
                      <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Bending Range</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-around', textAlign: 'center', marginTop: '10px' }}>
                      <div>
                        <div style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: '700' }}>LEFT KNEE</div>
                        <div style={{ fontSize: '1.4rem', fontWeight: '800', color: '#0284c7' }}>
                          {jointMotion?.left_knee?.rom_deg !== null && jointMotion?.left_knee?.rom_deg !== undefined ? `${jointMotion.left_knee.rom_deg}°` : 'N/A'}
                        </div>
                        <div style={{ fontSize: '0.72rem', color: '#64748b' }}>
                          [{jointMotion?.left_knee?.min_angle_deg || 0}° – {jointMotion?.left_knee?.max_angle_deg || 0}°]
                        </div>
                      </div>

                      <div style={{ borderRight: '1px solid #cbd5e1' }}></div>

                      <div>
                        <div style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: '700' }}>RIGHT KNEE</div>
                        <div style={{ fontSize: '1.4rem', fontWeight: '800', color: '#0ea5e9' }}>
                          {jointMotion?.right_knee?.rom_deg !== null && jointMotion?.right_knee?.rom_deg !== undefined ? `${jointMotion.right_knee.rom_deg}°` : 'N/A'}
                        </div>
                        <div style={{ fontSize: '0.72rem', color: '#64748b' }}>
                          [{jointMotion?.right_knee?.min_angle_deg || 0}° – {jointMotion?.right_knee?.max_angle_deg || 0}°]
                        </div>
                      </div>
                    </div>
                    <div style={{ marginTop: '12px', fontSize: '0.75rem', color: '#64748b', textAlign: 'center', borderTop: '1px dashed #e2e8f0', paddingTop: '8px' }}>
                      Left / Right Motion Balance: <strong>{symmetry?.knee_rom_asymmetry_pct || 0}%</strong> {(symmetry?.knee_rom_asymmetry_pct || 0) <= 10 ? '(Even)' : '(Slight variation)'}
                    </div>
                  </div>

                  {/* Hip Joint */}
                  <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '16px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                      <span style={{ fontSize: '0.92rem', fontWeight: '800', color: '#0f172a' }}>Hip Motion & Leg Swing</span>
                      <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Swing Range</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-around', textAlign: 'center', marginTop: '10px' }}>
                      <div>
                        <div style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: '700' }}>LEFT HIP</div>
                        <div style={{ fontSize: '1.4rem', fontWeight: '800', color: '#0284c7' }}>
                          {jointMotion?.left_hip?.rom_deg !== null && jointMotion?.left_hip?.rom_deg !== undefined ? `${jointMotion.left_hip.rom_deg}°` : 'N/A'}
                        </div>
                        <div style={{ fontSize: '0.72rem', color: '#64748b' }}>
                          [{jointMotion?.left_hip?.min_angle_deg || 0}° – {jointMotion?.left_hip?.max_angle_deg || 0}°]
                        </div>
                      </div>

                      <div style={{ borderRight: '1px solid #cbd5e1' }}></div>

                      <div>
                        <div style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: '700' }}>RIGHT HIP</div>
                        <div style={{ fontSize: '1.4rem', fontWeight: '800', color: '#0ea5e9' }}>
                          {jointMotion?.right_hip?.rom_deg !== null && jointMotion?.right_hip?.rom_deg !== undefined ? `${jointMotion.right_hip.rom_deg}°` : 'N/A'}
                        </div>
                        <div style={{ fontSize: '0.72rem', color: '#64748b' }}>
                          [{jointMotion?.right_hip?.min_angle_deg || 0}° – {jointMotion?.right_hip?.max_angle_deg || 0}°]
                        </div>
                      </div>
                    </div>
                    <div style={{ marginTop: '12px', fontSize: '0.75rem', color: '#64748b', textAlign: 'center', borderTop: '1px dashed #e2e8f0', paddingTop: '8px' }}>
                      Left / Right Motion Balance: <strong>{symmetry?.hip_rom_asymmetry_pct || 0}%</strong> {(symmetry?.hip_rom_asymmetry_pct || 0) <= 10 ? '(Even)' : '(Slight variation)'}
                    </div>
                  </div>

                  {/* Ankle Joint */}
                  <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '16px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                      <span style={{ fontSize: '0.92rem', fontWeight: '800', color: '#0f172a' }}>Ankle Flexibility</span>
                      <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Push-off Range</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-around', textAlign: 'center', marginTop: '10px' }}>
                      <div>
                        <div style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: '700' }}>LEFT ANKLE</div>
                        <div style={{ fontSize: '1.4rem', fontWeight: '800', color: '#0284c7' }}>
                          {jointMotion?.left_ankle?.rom_deg !== null && jointMotion?.left_ankle?.rom_deg !== undefined ? `${jointMotion.left_ankle.rom_deg}°` : 'N/A'}
                        </div>
                        <div style={{ fontSize: '0.72rem', color: '#64748b' }}>
                          [{jointMotion?.left_ankle?.min_angle_deg || 0}° – {jointMotion?.left_ankle?.max_angle_deg || 0}°]
                        </div>
                      </div>

                      <div style={{ borderRight: '1px solid #cbd5e1' }}></div>

                      <div>
                        <div style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: '700' }}>RIGHT ANKLE</div>
                        <div style={{ fontSize: '1.4rem', fontWeight: '800', color: '#0ea5e9' }}>
                          {jointMotion?.right_ankle?.rom_deg !== null && jointMotion?.right_ankle?.rom_deg !== undefined ? `${jointMotion.right_ankle.rom_deg}°` : 'N/A'}
                        </div>
                        <div style={{ fontSize: '0.72rem', color: '#64748b' }}>
                          [{jointMotion?.right_ankle?.min_angle_deg || 0}° – {jointMotion?.right_ankle?.max_angle_deg || 0}°]
                        </div>
                      </div>
                    </div>
                    <div style={{ marginTop: '12px', fontSize: '0.75rem', color: '#64748b', textAlign: 'center', borderTop: '1px dashed #e2e8f0', paddingTop: '8px' }}>
                      Left / Right Motion Balance: <strong>{symmetry?.ankle_rom_asymmetry_pct || 0}%</strong> {(symmetry?.ankle_rom_asymmetry_pct || 0) <= 10 ? '(Even)' : '(Slight variation)'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Category 3 & 4: Posture & Balance */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
                <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '20px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                    <ShieldCheck size={18} color="#0284c7" />
                    <h3 style={{ fontSize: '1.05rem', fontWeight: '800', margin: 0, color: '#0f172a' }}>
                      3. Body Posture & Alignment
                    </h3>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: '#f8fafc', borderRadius: '8px' }}>
                      <span style={{ fontSize: '0.84rem', color: '#475569' }}>Upright Posture Angle</span>
                      <strong style={{ fontSize: '0.9rem', color: '#0f172a' }}>{posture?.trunk_angle_deg !== null && posture?.trunk_angle_deg !== undefined ? `${posture.trunk_angle_deg}°` : 'N/A'}</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: '#f8fafc', borderRadius: '8px' }}>
                      <span style={{ fontSize: '0.84rem', color: '#475569' }}>Posture Stability</span>
                      <strong style={{ fontSize: '0.9rem', color: '#0f172a' }}>{posture?.trunk_variability_deg !== null && posture?.trunk_variability_deg !== undefined ? `±${posture.trunk_variability_deg}°` : 'N/A'}</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: '#f8fafc', borderRadius: '8px' }}>
                      <span style={{ fontSize: '0.84rem', color: '#475569' }}>Side-to-Side Sway</span>
                      <strong style={{ fontSize: '0.9rem', color: '#0f172a' }}>{posture?.lateral_sway !== null && posture?.lateral_sway !== undefined ? `${posture.lateral_sway}` : 'N/A'}</strong>
                    </div>
                  </div>
                </div>

                <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '20px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                    <Scale size={18} color="#0284c7" />
                    <h3 style={{ fontSize: '1.05rem', fontWeight: '800', margin: 0, color: '#0f172a' }}>
                      4. Left & Right Movement Balance
                    </h3>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: '#f8fafc', borderRadius: '8px' }}>
                      <span style={{ fontSize: '0.84rem', color: '#475569' }}>Step Timing Balance</span>
                      <strong style={{ fontSize: '0.9rem', color: (symmetry?.step_time_asymmetry_pct || 0) < 10 ? '#16a34a' : '#d97706' }}>
                        {(symmetry?.step_time_asymmetry_pct || 0) < 10 ? 'Balanced' : `${symmetry?.step_time_asymmetry_pct}% diff`}
                      </strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: '#f8fafc', borderRadius: '8px' }}>
                      <span style={{ fontSize: '0.84rem', color: '#475569' }}>Knee Motion Balance</span>
                      <strong style={{ fontSize: '0.9rem', color: (symmetry?.knee_rom_asymmetry_pct || 0) < 10 ? '#16a34a' : '#d97706' }}>
                        {(symmetry?.knee_rom_asymmetry_pct || 0) < 10 ? 'Balanced' : `${symmetry?.knee_rom_asymmetry_pct}% diff`}
                      </strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: '#f8fafc', borderRadius: '8px' }}>
                      <span style={{ fontSize: '0.84rem', color: '#475569' }}>Hip Motion Balance</span>
                      <strong style={{ fontSize: '0.9rem', color: (symmetry?.hip_rom_asymmetry_pct || 0) < 10 ? '#16a34a' : '#d97706' }}>
                        {(symmetry?.hip_rom_asymmetry_pct || 0) < 10 ? 'Balanced' : `${symmetry?.hip_rom_asymmetry_pct}% diff`}
                      </strong>
                    </div>
                  </div>
                </div>
              </div>

              {/* Note: Raw academic reference table removed to keep the dashboard clear and parent-friendly */}
            </div>
          )}

          {/* TAB 2: JOINT ANGLES OVER TIME (Section 15 Interactive Curves) */}
          {activeTab === 'curves' && curves && (
            <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '22px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', marginBottom: '18px' }}>
                <div>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: '800', margin: 0, color: '#0f172a' }}>
                    Joint Motion Curves
                  </h3>
                  <p style={{ fontSize: '0.82rem', color: '#64748b', margin: '4px 0 0 0' }}>
                    Visualizes joint angles over time. Blue curve represents left side, Orange represents right side.
                  </p>
                </div>

                <div style={{ display: 'flex', gap: '6px' }}>
                  {['knee', 'hip', 'ankle', 'trunk'].map((j) => (
                    <button
                      key={j}
                      onClick={() => setSelectedCurveJoint(j)}
                      style={{
                        padding: '6px 14px',
                        borderRadius: '6px',
                        border: selectedCurveJoint === j ? '2px solid #0284c7' : '1px solid #cbd5e1',
                        background: selectedCurveJoint === j ? '#f0f9ff' : '#fff',
                        color: selectedCurveJoint === j ? '#0284c7' : '#475569',
                        fontWeight: '700',
                        fontSize: '0.8rem',
                        cursor: 'pointer',
                        textTransform: 'capitalize'
                      }}
                    >
                      {j} Angle
                    </button>
                  ))}
                </div>
              </div>

              {/* Chart Component (Custom Interactive SVG Visualizer) */}
              <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '16px', position: 'relative' }}>
                {(() => {
                  const timestamps = curves.timestamps || [];
                  const leftSeries = selectedCurveJoint === 'trunk' ? curves.trunk : curves[`left_${selectedCurveJoint}`] || [];
                  const rightSeries = selectedCurveJoint === 'trunk' ? [] : curves[`right_${selectedCurveJoint}`] || [];
                  const events = curves.gait_events || [];

                  if (timestamps.length === 0) {
                    return <div style={{ textAlign: 'center', padding: '40px', color: '#94a3b8' }}>No continuous time series data available.</div>;
                  }

                  // Find min/max for scaling
                  const allPoints = [...leftSeries, ...rightSeries].filter((v) => v !== null && !isNaN(v));
                  const minVal = allPoints.length > 0 ? Math.max(0, Math.min(...allPoints) - 10) : 0;
                  const maxVal = allPoints.length > 0 ? Math.max(90, Math.max(...allPoints) + 10) : 120;
                  const maxTime = timestamps[timestamps.length - 1] || 1.0;

                  const width = 850;
                  const height = 260;
                  const padLeft = 45;
                  const padBottom = 30;
                  const padTop = 15;
                  const padRight = 20;

                  const plotW = width - padLeft - padRight;
                  const plotH = height - padTop - padBottom;

                  const getX = (t) => padLeft + (t / maxTime) * plotW;
                  const getY = (val) => padTop + plotH - ((val - minVal) / (maxVal - minVal || 1)) * plotH;

                  const buildPath = (series) => {
                    let path = '';
                    let inSegment = false;
                    for (let i = 0; i < series.length; i++) {
                      const v = series[i];
                      const t = timestamps[i];
                      if (v !== null && !isNaN(v)) {
                        const x = getX(t);
                        const y = getY(v);
                        if (!inSegment) {
                          path += `M ${x.toFixed(1)} ${y.toFixed(1)} `;
                          inSegment = true;
                        } else {
                          path += `L ${x.toFixed(1)} ${y.toFixed(1)} `;
                        }
                      } else {
                        inSegment = false;
                      }
                    }
                    return path;
                  };

                  return (
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', fontSize: '0.8rem' }}>
                        <div style={{ display: 'flex', gap: '16px' }}>
                          <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#0284c7', fontWeight: '700' }}>
                            <span style={{ width: '12px', height: '3px', background: '#0284c7', display: 'inline-block' }}></span>
                            {selectedCurveJoint === 'trunk' ? 'Upper Body Lean' : `Left ${selectedCurveJoint.toUpperCase()}`}
                          </span>
                          {selectedCurveJoint !== 'trunk' && (
                            <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#f97316', fontWeight: '700' }}>
                              <span style={{ width: '12px', height: '3px', background: '#f97316', display: 'inline-block' }}></span>
                              Right {selectedCurveJoint.toUpperCase()}
                            </span>
                          )}
                        </div>
                        <div style={{ color: '#64748b', fontSize: '0.75rem' }}>
                          {hoveredTime !== null ? `Time: ${hoveredTime.toFixed(2)}s` : 'Hover graph to see time points'}
                        </div>
                      </div>

                      <svg
                        viewBox={`0 0 ${width} ${height}`}
                        style={{ width: '100%', height: 'auto', overflow: 'visible' }}
                        onMouseMove={(e) => {
                          const rect = e.currentTarget.getBoundingClientRect();
                          const mouseX = e.clientX - rect.left;
                          const ratio = (mouseX / rect.width);
                          const t = Math.max(0, Math.min(maxTime, ratio * maxTime));
                          setHoveredTime(t);
                        }}
                        onMouseLeave={() => setHoveredTime(null)}
                      >
                        {/* Grid lines */}
                        {[0, 0.25, 0.5, 0.75, 1.0].map((frac, idx) => {
                          const val = minVal + frac * (maxVal - minVal);
                          const y = getY(val);
                          return (
                            <g key={idx}>
                              <line x1={padLeft} y1={y} x2={width - padRight} y2={y} stroke="#e2e8f0" strokeDasharray="3,3" />
                              <text x={padLeft - 8} y={y + 4} fontSize="10" fill="#94a3b8" textAnchor="end">{Math.round(val)}°</text>
                            </g>
                          );
                        })}

                        {/* Heel Strike Gait Event Markers */}
                        {events.map((ev, idx) => {
                          const x = getX(ev.time_seconds);
                          const isLeft = ev.side === 'LEFT';
                          return (
                            <g key={idx}>
                              <line x1={x} y1={padTop} x2={x} y2={padTop + plotH} stroke={isLeft ? '#0284c7' : '#f97316'} strokeDasharray="2,2" strokeWidth="1" opacity="0.6" />
                              <circle cx={x} cy={padTop + plotH} r="3" fill={isLeft ? '#0284c7' : '#f97316'} />
                            </g>
                          );
                        })}

                        {/* Data paths */}
                        <path d={buildPath(leftSeries)} fill="none" stroke="#0284c7" strokeWidth="2.5" strokeLinecap="round" />
                        {rightSeries.length > 0 && (
                          <path d={buildPath(rightSeries)} fill="none" stroke="#f97316" strokeWidth="2.5" strokeLinecap="round" />
                        )}

                        {/* X-axis labels */}
                        {[0, 0.25, 0.5, 0.75, 1.0].map((frac, idx) => {
                          const t = frac * maxTime;
                          const x = getX(t);
                          return (
                            <text key={idx} x={x} y={height - 8} fontSize="10" fill="#94a3b8" textAnchor="middle">{t.toFixed(1)}s</text>
                          );
                        })}
                      </svg>
                    </div>
                  );
                })()}
              </div>
            </div>
          )}

          {/* TAB 3: STEP BALANCE & CYCLES */}
          {activeTab === 'cycles' && (
            <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '22px' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: '800', margin: '0 0 14px 0', color: '#0f172a' }}>
                Step Balance & Movement Symmetry
              </h3>
              <p style={{ fontSize: '0.84rem', color: '#64748b', marginBottom: '18px' }}>
                Shows how evenly your child moves each leg across walking steps. Balanced movement helps children build steady, confident walking habits.
              </p>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
                <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: '800', color: '#0f172a', marginBottom: '8px' }}>Knee Motion Range</div>
                  <div style={{ fontSize: '0.8rem', color: '#475569' }}>Left Knee Motion: <strong>{jointMotion?.left_knee?.rom_deg || 0}°</strong></div>
                  <div style={{ fontSize: '0.8rem', color: '#475569' }}>Right Knee Motion: <strong>{jointMotion?.right_knee?.rom_deg || 0}°</strong></div>
                  <div style={{ fontSize: '0.8rem', color: '#475569', marginTop: '6px' }}>
                    Balance: <strong style={{ color: (symmetry?.knee_rom_asymmetry_pct || 0) < 8 ? '#16a34a' : '#d97706' }}>{(symmetry?.knee_rom_asymmetry_pct || 0) < 8 ? 'Even balance' : `${symmetry?.knee_rom_asymmetry_pct}% difference`}</strong>
                  </div>
                </div>

                <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: '800', color: '#0f172a', marginBottom: '8px' }}>Hip Motion Range</div>
                  <div style={{ fontSize: '0.8rem', color: '#475569' }}>Left Hip Motion: <strong>{jointMotion?.left_hip?.rom_deg || 0}°</strong></div>
                  <div style={{ fontSize: '0.8rem', color: '#475569' }}>Right Hip Motion: <strong>{jointMotion?.right_hip?.rom_deg || 0}°</strong></div>
                  <div style={{ fontSize: '0.8rem', color: '#475569', marginTop: '6px' }}>
                    Balance: <strong style={{ color: (symmetry?.hip_rom_asymmetry_pct || 0) < 10 ? '#16a34a' : '#d97706' }}>{(symmetry?.hip_rom_asymmetry_pct || 0) < 10 ? 'Even balance' : `${symmetry?.hip_rom_asymmetry_pct}% difference`}</strong>
                  </div>
                </div>

                <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: '800', color: '#0f172a', marginBottom: '8px' }}>Step Timing Balance</div>
                  <div style={{ fontSize: '0.8rem', color: '#475569' }}>Left Step Duration: <strong>{assessmentResult.metrics?.left_mean_step_time || 0}s</strong></div>
                  <div style={{ fontSize: '0.8rem', color: '#475569' }}>Right Step Duration: <strong>{assessmentResult.metrics?.right_mean_step_time || 0}s</strong></div>
                  <div style={{ fontSize: '0.8rem', color: '#475569', marginTop: '6px' }}>
                    Timing Difference: <strong>{assessmentResult.metrics?.timing_difference_ms || 0} ms</strong>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: CLINICAL REASONING Q&A */}
          {activeTab === 'qa' && (
            <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '22px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                <Sparkles size={20} color="#0284c7" />
                <h3 style={{ fontSize: '1.1rem', fontWeight: '800', margin: 0, color: '#0f172a' }}>
                  Ask Questions About Your Child's Walking
                </h3>
              </div>
              <p style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: '16px' }}>
                Have questions about your child's walking rhythm, leg bending, or step balance? Ask our assistant below for clear, easy-to-understand explanations.
              </p>

              {/* Q&A Input */}
              <form onSubmit={handleAskQuestion} style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
                <input
                  type="text"
                  value={userQuestion}
                  onChange={(e) => setUserQuestion(e.target.value)}
                  placeholder="e.g. Is my child's step pace and knee movement typical for their age?"
                  style={{
                    flex: 1,
                    padding: '10px 14px',
                    borderRadius: '8px',
                    border: '1px solid #cbd5e1',
                    fontSize: '0.88rem',
                    outline: 'none'
                  }}
                />
                <button
                  type="submit"
                  disabled={isAsking || !userQuestion.trim()}
                  style={{
                    background: '#0284c7',
                    color: '#fff',
                    border: 'none',
                    borderRadius: '8px',
                    padding: '10px 18px',
                    fontWeight: '700',
                    fontSize: '0.88rem',
                    cursor: isAsking || !userQuestion.trim() ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}
                >
                  <Send size={15} />
                  {isAsking ? 'Thinking...' : 'Ask Question'}
                </button>
              </form>

              {/* History */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {qaHistory.map((item, idx) => (
                  <div key={idx} style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '16px' }}>
                    <div style={{ fontSize: '0.9rem', fontWeight: '800', color: '#0f172a', marginBottom: '8px' }}>
                      Q: {item.question}
                    </div>
                    <div style={{ fontSize: '0.85rem', color: '#334155', lineHeight: '1.5' }}>
                      <MarkdownResponse content={item.answer} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Clinical Disclaimer Footnote */}
          <div style={{
            background: '#f8fafc',
            border: '1px solid #e2e8f0',
            borderRadius: '10px',
            padding: '12px 16px',
            fontSize: '0.75rem',
            color: '#64748b',
            lineHeight: '1.4'
          }}>
            <strong>Important Note:</strong> This automated screening tool provides developmental observations and movement insights based on published pediatric walking references. It is designed for informational guidance and does not replace an in-person assessment by a pediatrician or physical therapist.
          </div>

        </div>
      )}
    </div>
  );
}
