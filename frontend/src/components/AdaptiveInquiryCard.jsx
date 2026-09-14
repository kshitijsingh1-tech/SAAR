import React, { useState, useEffect, useCallback } from 'react';
import {
  HelpCircle, Brain, CheckCircle2, XCircle, ArrowRight,
  Sparkles, ShieldCheck, AlertTriangle, Lightbulb, ChevronRight,
  Loader2, RotateCcw, Zap, Compass, Activity, Info
} from 'lucide-react';
import { startAdaptiveSession, submitAdaptiveAnswer } from '../api/client';
import { MarkdownResponse } from './MarkdownResponse';

/**
 * AdaptiveInquiryCard — Interactive diagnostic questioning interface.
 *
 * Grounded in the child's personalized baseline, maintains structured Case State,
 * scores questions using Information Gain × Relevance × Uncertainty,
 * and dynamically adapts the next question based on parent responses.
 *
 * Includes Quick Demo Switchers for hackathon judges to verify Case A vs Case B in 1 click.
 */
const AdaptiveInquiryCard = ({
  investigationId,
  userConcern,
  subjectId = 'child_leo_24m',
  baselineComparison,
  onSessionComplete,
  onClose
}) => {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedOption, setSelectedOption] = useState(null);
  const [animatingOut, setAnimatingOut] = useState(false);

  const initSession = useCallback(async () => {
    setLoading(true);
    setError(null);
    setSelectedOption(null);
    try {
      const defaultConcern = (subjectId?.includes('badminton') || (userConcern && (userConcern.toLowerCase().includes('badminton') || userConcern.toLowerCase().includes('smash') || userConcern.toLowerCase().includes('racket'))))
        ? "Badminton stroke power, smash penetration, and trajectory inquiry"
        : "Child exhibits 15% step time asymmetry and uneven weight bearing";
      const concernText = userConcern || defaultConcern;
      const result = await startAdaptiveSession(investigationId, concernText, subjectId);
      setSession(result);
    } catch (err) {
      console.error('[AdaptiveInquiry] Failed to start session:', err);
      setError('Could not start adaptive analysis. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [investigationId, userConcern, subjectId]);

  // Start session on mount or when concern changes
  useEffect(() => {
    initSession();
  }, [initSession]);

  const handleAnswerClick = async (optionId) => {
    if (!session || loading) return;
    setSelectedOption(optionId);
    setAnimatingOut(true);

    // Brief animation delay before submitting
    await new Promise(r => setTimeout(r, 350));

    setLoading(true);
    setAnimatingOut(false);
    try {
      const updated = await submitAdaptiveAnswer(session.session_id, optionId);
      setSession(updated);
      setSelectedOption(null);
      if (updated.status === 'concluded' && onSessionComplete) {
        onSessionComplete(updated);
      }
    } catch (err) {
      console.error('[AdaptiveInquiry] Answer submission failed:', err);
      setError('Failed to process your answer. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Quick Demo Shortcut for Judges: Case A (Acute Fall -> Injury OR Late Reach -> Net Tape)
  const handleDemoCaseA = async () => {
    if (!session || loading) return;
    if (session.turn > 1) {
      await initSession();
      // Wait for session update
      setTimeout(() => triggerCaseAAnswer(), 300);
    } else {
      triggerCaseAAnswer();
    }
  };

  const triggerCaseAAnswer = () => {
    const q = session?.current_question;
    if (!q) return;
    const opt = q.options.find(o => 
      o.text.toLowerCase().includes('net tape') || 
      o.text.toLowerCase().includes('recently')
    );
    if (opt) {
      handleAnswerClick(opt.option_id);
    }
  };

  // Quick Demo Shortcut for Judges: Case B (Chronic Habit -> Milestones OR Sliced Face -> Out Long)
  const handleDemoCaseB = async () => {
    if (!session || loading) return;
    if (session.turn > 1) {
      await initSession();
      setTimeout(() => triggerCaseBAnswer(), 300);
    } else {
      triggerCaseBAnswer();
    }
  };

  const triggerCaseBAnswer = () => {
    const q = session?.current_question;
    if (!q) return;
    const opt = q.options.find(o => 
      o.text.toLowerCase().includes('out long') || 
      o.text.toLowerCase().includes('always')
    );
    if (opt) {
      handleAnswerClick(opt.option_id);
    }
  };

  const isBadminton = session?.domain === 'sports' || session?.domain === 'badminton' || subjectId?.includes('badminton') || (userConcern && (userConcern.toLowerCase().includes('badminton') || userConcern.toLowerCase().includes('smash') || userConcern.toLowerCase().includes('racket')));

  // Loading state
  if (loading && !session) {
    return (
      <div className="adaptive-inquiry-card adaptive-loading" style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '16px', padding: '24px', textAlign: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', color: '#0284c7', fontWeight: '700', marginBottom: '12px' }}>
          <Brain size={22} className="pulse" />
          <span>SAAR Adaptive Reasoning Engine</span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', color: '#64748b', fontSize: '0.88rem' }}>
          <Loader2 size={28} className="spin text-cyan" />
          <p>{isBadminton ? 'Evaluating stroke kinematics against kinetic chain & formulating competing hypotheses...' : "Evaluating video observations against child's baseline & formulating competing hypotheses..."}</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="adaptive-inquiry-card adaptive-error" style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '14px', padding: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#dc2626', fontWeight: '700', marginBottom: '6px' }}>
          <AlertTriangle size={18} />
          <span>Adaptive Triage Notice</span>
        </div>
        <p style={{ color: '#b91c1c', fontSize: '0.88rem', margin: '0 0 12px 0' }}>{error}</p>
        <button
          onClick={initSession}
          style={{ background: '#dc2626', color: '#fff', border: 'none', borderRadius: '8px', padding: '6px 14px', fontSize: '0.82rem', fontWeight: '600', cursor: 'pointer' }}
        >
          Retry Adaptive Triage
        </button>
      </div>
    );
  }

  if (!session) return null;

  const { hypotheses = [], current_question, status, conclusion, turn, max_questions, preamble, case_state, personalized_recommendations = [] } = session;

  // Concluded state — show personalized verdict & action plan
  if (status === 'concluded') {
    return (
      <div className="adaptive-inquiry-card adaptive-concluded" style={{
        background: '#ffffff',
        border: '2px solid #10b981',
        borderRadius: '16px',
        padding: '24px',
        boxShadow: '0 8px 30px -4px rgba(16, 185, 129, 0.15)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              background: '#ecfdf5',
              color: '#059669',
              borderRadius: '10px',
              padding: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <ShieldCheck size={22} />
            </div>
            <div>
              <span style={{ fontSize: '1.05rem', fontWeight: '800', color: '#0f172a' }}>
                Personalized Diagnostic Assessment
              </span>
              <p style={{ fontSize: '0.8rem', color: '#64748b', margin: '2px 0 0 0' }}>
                Reasoning synthesized across video kinematics, child baseline, and parent responses
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={initSession}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                background: '#f1f5f9',
                border: '1px solid #cbd5e1',
                borderRadius: '8px',
                padding: '6px 12px',
                fontSize: '0.78rem',
                fontWeight: '600',
                color: '#475569',
                cursor: 'pointer'
              }}
              title="Test the questioning flow again"
            >
              <RotateCcw size={13} />
              <span>Restart Triage</span>
            </button>
            {onClose && (
              <button
                onClick={onClose}
                style={{
                  background: '#0f172a',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '6px 14px',
                  fontSize: '0.78rem',
                  fontWeight: '600',
                  cursor: 'pointer'
                }}
              >
                Done
              </button>
            )}
          </div>
        </div>

        {/* Hypothesis Outcome Badges */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '18px' }}>
          {hypotheses.map((h) => {
            const isConfirmed = h.status === 'confirmed' || h.current_probability >= 0.8;
            const isEliminated = h.status === 'eliminated' || h.current_probability < 0.1;
            return (
              <div
                key={h.hypothesis_id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 12px',
                  borderRadius: '8px',
                  fontSize: '0.82rem',
                  fontWeight: '700',
                  background: isConfirmed ? '#ecfdf5' : (isEliminated ? '#fef2f2' : '#f8fafc'),
                  border: `1px solid ${isConfirmed ? '#a7f3d0' : (isEliminated ? '#fecaca' : '#e2e8f0')}`,
                  color: isConfirmed ? '#065f46' : (isEliminated ? '#991b1b' : '#334155'),
                  textDecoration: isEliminated ? 'line-through' : 'none',
                  opacity: isEliminated ? 0.75 : 1
                }}
              >
                {isConfirmed && <CheckCircle2 size={14} color="#059669" />}
                {isEliminated && <XCircle size={14} color="#dc2626" />}
                <span>{h.name}</span>
                <span style={{ fontSize: '0.75rem', opacity: 0.9 }}>({Math.round(h.current_probability * 100)}%)</span>
              </div>
            );
          })}
        </div>

        {/* Conclusion Markdown */}
        {conclusion && (
          <div style={{ fontSize: '0.9rem', color: '#1e293b', lineHeight: '1.6', background: '#f8fafc', padding: '18px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
            <MarkdownResponse content={conclusion} />
          </div>
        )}

        {/* Action Plan Highlights */}
        {personalized_recommendations && personalized_recommendations.length > 0 && (
          <div style={{ marginTop: '16px', background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '12px', padding: '14px 18px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#166534', fontWeight: '800', fontSize: '0.88rem', marginBottom: '8px' }}>
              <Lightbulb size={16} />
              <span>Action Plan Highlights</span>
            </div>
            <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '0.85rem', color: '#166534', lineHeight: '1.5' }}>
              {personalized_recommendations.map((rec, i) => (
                <li key={i}>{rec}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  }

  // Active questioning state
  return (
    <div className="adaptive-inquiry-card adaptive-active" style={{
      background: '#ffffff',
      border: '2px solid #0284c7',
      borderRadius: '16px',
      padding: '22px',
      boxShadow: '0 8px 30px -4px rgba(2, 132, 199, 0.16)'
    }}>
      {/* Top Header Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            background: 'linear-gradient(135deg, #0284c7, #4f46e5)',
            color: '#fff',
            borderRadius: '10px',
            padding: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 12px rgba(2, 132, 199, 0.25)'
          }}>
            <Brain size={20} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '1rem', fontWeight: '800', color: '#0f172a' }}>
                {isBadminton ? '🏸 Badminton Biomechanical & Tactical Triage' : 'Adaptive Diagnostic Triage'}
              </span>
              <span style={{
                fontSize: '0.72rem',
                fontWeight: '800',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                padding: '2px 8px',
                borderRadius: '6px',
                background: '#e0f2fe',
                color: '#0369a1'
              }}>
                Active Reasoning Loop
              </span>
            </div>
            <p style={{ fontSize: '0.82rem', color: '#64748b', margin: '2px 0 0 0' }}>
              {isBadminton ? 'Kinetic chain sequencing, grip twist, and footwork fatigue inquiry' : 'Uncertainty reduction via dynamic Bayesian information gain'}
            </p>
          </div>
        </div>

        {/* Turn indicator & Reset */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{
            fontSize: '0.78rem',
            fontWeight: '700',
            color: '#0369a1',
            background: '#f0f9ff',
            border: '1px solid #bae6fd',
            borderRadius: '8px',
            padding: '4px 10px'
          }}>
            Question {turn} of ~{max_questions}
          </span>
          <button
            onClick={initSession}
            style={{
              background: '#f8fafc',
              border: '1px solid #cbd5e1',
              borderRadius: '8px',
              padding: '4px 10px',
              color: '#64748b',
              fontSize: '0.78rem',
              fontWeight: '600',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
            title="Reset to first question"
          >
            <RotateCcw size={12} />
            <span>Reset</span>
          </button>
        </div>
      </div>

      {/* Judge Proof-of-Adaptation Demo Bar */}
      <div style={{
        background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)',
        border: '1px dashed #94a3b8',
        borderRadius: '10px',
        padding: '10px 14px',
        marginBottom: '16px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '8px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Zap size={14} color="#f59e0b" />
          <span style={{ fontSize: '0.78rem', fontWeight: '800', color: '#334155', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Judge Demo Controls:
          </span>
          <span style={{ fontSize: '0.78rem', color: '#64748b' }}>
            Demonstrate how different answers change the next question:
          </span>
        </div>

        <div style={{ display: 'flex', gap: '6px' }}>
          <button
            type="button"
            onClick={handleDemoCaseA}
            disabled={loading}
            style={{
              background: '#e0f2fe',
              border: '1px solid #7dd3fc',
              color: '#0369a1',
              borderRadius: '6px',
              padding: '4px 10px',
              fontSize: '0.75rem',
              fontWeight: '700',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              transition: 'all 0.15s ease'
            }}
            title={isBadminton ? "Simulate Case A: Net tape miss -> leads to contact point apex inquiry" : "Simulate Case A: Recent change -> leads directly to injury inquiry"}
          >
            <span>{isBadminton ? '⚡ Case A: Late Reach (Hits Net)' : '⚡ Case A: Acute Fall Path'}</span>
          </button>

          <button
            type="button"
            onClick={handleDemoCaseB}
            disabled={loading}
            style={{
              background: '#fef3c7',
              border: '1px solid #fcd34d',
              color: '#92400e',
              borderRadius: '6px',
              padding: '4px 10px',
              fontSize: '0.75rem',
              fontWeight: '700',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              transition: 'all 0.15s ease'
            }}
            title={isBadminton ? "Simulate Case B: Out long -> leads to grip feel & tension inquiry" : "Simulate Case B: Chronic habit -> leads directly to running/stairs milestone inquiry"}
          >
            <span>{isBadminton ? '⚡ Case B: Sliced Face (Out Long)' : '⚡ Case B: Chronic Habit Path'}</span>
          </button>
        </div>
      </div>

      {/* Conversational Analyst Preamble */}
      {preamble && (
        <div style={{
          background: '#f0f9ff',
          borderLeft: '4px solid #0284c7',
          padding: '10px 14px',
          borderRadius: '0 8px 8px 0',
          fontSize: '0.85rem',
          color: '#0369a1',
          marginBottom: '16px',
          lineHeight: '1.5'
        }}>
          <MarkdownResponse content={preamble} />
        </div>
      )}

      {/* Case State Pills */}
      {case_state && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap', marginBottom: '16px' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: '700', color: '#475569' }}>Machine Evidence:</span>
          {case_state.observations?.step_asymmetry_pct !== undefined && (
            <span style={{ fontSize: '0.72rem', background: '#fee2e2', color: '#991b1b', padding: '2px 8px', borderRadius: '4px', fontWeight: '700' }}>
              {case_state.observations.step_asymmetry_pct}% Asymmetry
            </span>
          )}
          {case_state.baseline_deviation_detected && (
            <span style={{ fontSize: '0.72rem', background: '#ffedd5', color: '#9a3412', padding: '2px 8px', borderRadius: '4px', fontWeight: '700' }}>
              Baseline Deviation (Leo: 3.4%)
            </span>
          )}
          {case_state.uncertainties && case_state.uncertainties.length > 0 && (
            <span style={{ fontSize: '0.72rem', background: '#f1f5f9', color: '#475569', padding: '2px 8px', borderRadius: '4px', fontWeight: '600' }}>
              Resolving: {case_state.uncertainties.join(', ')}
            </span>
          )}
        </div>
      )}

      {/* Competing Hypotheses Bars */}
      <div style={{
        background: '#f8fafc',
        border: '1px solid #e2e8f0',
        borderRadius: '12px',
        padding: '14px',
        marginBottom: '20px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', fontWeight: '800', color: '#334155', textTransform: 'uppercase' }}>
            <Compass size={14} color="#0284c7" />
            <span>Competing Hypotheses & Live Confidence</span>
          </div>
          <span style={{ fontSize: '0.72rem', color: '#64748b' }}>
            Dynamic Bayesian probability update
          </span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {hypotheses.map(h => {
            const isEliminated = h.status === 'eliminated' || h.current_probability < 0.08;
            const isConfirmed = h.status === 'confirmed' || h.current_probability >= 0.8;
            const pct = Math.round(h.current_probability * 100);

            return (
              <div key={h.hypothesis_id} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '220px', flexShrink: 0, display: 'flex', alignItems: 'center', gap: '5px' }}>
                  {isEliminated && <XCircle size={12} color="#dc2626" />}
                  {isConfirmed && <CheckCircle2 size={12} color="#16a34a" />}
                  <span style={{
                    fontSize: '0.8rem',
                    fontWeight: isConfirmed ? '800' : '600',
                    color: isEliminated ? '#94a3b8' : (isConfirmed ? '#166534' : '#1e293b'),
                    textDecoration: isEliminated ? 'line-through' : 'none',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                  }} title={h.name}>
                    {h.name}
                  </span>
                </div>

                <div style={{ flex: 1, height: '8px', background: '#e2e8f0', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{
                    width: `${pct}%`,
                    height: '100%',
                    background: isConfirmed ? 'linear-gradient(90deg, #10b981, #059669)' : (isEliminated ? '#cbd5e1' : 'linear-gradient(90deg, #0284c7, #4f46e5)'),
                    borderRadius: '4px',
                    transition: 'width 0.4s ease'
                  }} />
                </div>

                <span style={{
                  width: '40px',
                  textAlign: 'right',
                  fontSize: '0.8rem',
                  fontWeight: '700',
                  color: isConfirmed ? '#166534' : (isEliminated ? '#94a3b8' : '#0f172a')
                }}>
                  {pct}%
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Current Question Block */}
      {current_question && (
        <div style={{
          background: '#ffffff',
          border: '1px solid #cbd5e1',
          borderRadius: '12px',
          padding: '18px',
          boxShadow: '0 2px 10px rgba(0,0,0,0.03)'
        }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', marginBottom: '10px' }}>
            <div style={{ background: '#e0f2fe', padding: '6px', borderRadius: '8px', color: '#0284c7', marginTop: '2px' }}>
              <HelpCircle size={18} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.02rem', fontWeight: '800', color: '#0f172a', margin: '0 0 4px 0' }}>
                {current_question.question_text}
              </h3>
              {current_question.reason && (
                <p style={{ fontSize: '0.82rem', color: '#64748b', margin: 0, fontStyle: 'italic' }}>
                  Why we are asking: {current_question.reason}
                </p>
              )}
            </div>
          </div>

          {/* Answer Option Chips */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '16px' }}>
            {(current_question.options || []).map(opt => (
              <button
                key={opt.option_id}
                onClick={() => handleAnswerClick(opt.option_id)}
                disabled={loading}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  background: selectedOption === opt.option_id ? '#e0f2fe' : '#ffffff',
                  border: `1.5px solid ${selectedOption === opt.option_id ? '#0284c7' : '#cbd5e1'}`,
                  borderRadius: '10px',
                  padding: '12px 16px',
                  textAlign: 'left',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  transition: 'all 0.15s ease'
                }}
                onMouseEnter={(e) => {
                  if (!loading && selectedOption !== opt.option_id) {
                    e.currentTarget.style.borderColor = '#0284c7';
                    e.currentTarget.style.background = '#f0f9ff';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!loading && selectedOption !== opt.option_id) {
                    e.currentTarget.style.borderColor = '#cbd5e1';
                    e.currentTarget.style.background = '#ffffff';
                  }
                }}
              >
                <span style={{ fontSize: '0.88rem', fontWeight: '600', color: '#0f172a' }}>
                  {opt.text}
                </span>
                <ChevronRight size={16} color="#0284c7" />
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Loading Indicator during answer submission */}
      {loading && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', marginTop: '14px', color: '#0284c7', fontSize: '0.85rem', fontWeight: '600' }}>
          <Loader2 size={16} className="spin" />
          <span>Updating diagnostic hypotheses and selecting next best inquiry...</span>
        </div>
      )}
    </div>
  );
};

export default AdaptiveInquiryCard;
