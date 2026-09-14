import React, { useState, useEffect } from 'react';
import {
  HelpCircle, Brain, CheckCircle2, XCircle, ArrowRight,
  Sparkles, ShieldCheck, AlertTriangle, Lightbulb, ChevronRight, Loader2
} from 'lucide-react';
import { startAdaptiveSession, submitAdaptiveAnswer } from '../api/client';
import { MarkdownResponse } from './MarkdownResponse';

/**
 * AdaptiveInquiryCard — Interactive diagnostic questioning interface.
 *
 * Shows LLM-generated hypotheses, asks discriminating questions with
 * one-tap answer chips, updates hypothesis confidence bars in real-time,
 * and delivers a personalized conclusion when the engine concludes.
 */
const AdaptiveInquiryCard = ({
  investigationId,
  userConcern,
  onSessionComplete,
  onClose
}) => {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedOption, setSelectedOption] = useState(null);
  const [animatingOut, setAnimatingOut] = useState(false);

  // Start the adaptive session on mount
  useEffect(() => {
    if (!userConcern) return;
    let cancelled = false;

    const init = async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await startAdaptiveSession(investigationId, userConcern);
        if (!cancelled) setSession(result);
      } catch (err) {
        if (!cancelled) {
          console.error('[AdaptiveInquiry] Failed to start session:', err);
          setError('Could not start adaptive analysis. Please try again.');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    init();

    return () => { cancelled = true; };
  }, [investigationId, userConcern]);

  const handleAnswerClick = async (optionId) => {
    if (!session || loading) return;
    setSelectedOption(optionId);
    setAnimatingOut(true);

    // Brief animation delay before submitting
    await new Promise(r => setTimeout(r, 400));

    setLoading(true);
    setAnimatingOut(false);
    try {
      const updated = await submitAdaptiveAnswer(session.session_id, optionId);
      setSession(updated);
      setSelectedOption(null);
    } catch (err) {
      console.error('[AdaptiveInquiry] Answer submission failed:', err);
      setError('Failed to process your answer. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Loading state
  if (loading && !session) {
    return (
      <div className="adaptive-inquiry-card adaptive-loading">
        <div className="adaptive-header">
          <Brain size={18} className="adaptive-icon pulse" />
          <span>SAAR is analyzing your concern...</span>
        </div>
        <div className="adaptive-loading-body">
          <Loader2 size={28} className="spin" />
          <p>Generating diagnostic hypotheses from measured data</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="adaptive-inquiry-card adaptive-error">
        <div className="adaptive-header">
          <AlertTriangle size={18} />
          <span>Diagnostic Analysis</span>
        </div>
        <p className="adaptive-error-text">{error}</p>
      </div>
    );
  }

  if (!session) return null;

  const { hypotheses = [], current_question, status, conclusion, turn, max_questions, personalized_recommendations = [] } = session;
  const activeHypotheses = hypotheses.filter(h => h.status === 'active');
  const eliminatedHypotheses = hypotheses.filter(h => h.status === 'eliminated');
  const confirmedHypothesis = hypotheses.find(h => h.status === 'confirmed');

  // Concluded state — show personalized verdict
  if (status === 'concluded') {
    return (
      <div className="adaptive-inquiry-card adaptive-concluded">
        <div className="adaptive-header concluded-header">
          <ShieldCheck size={18} className="adaptive-icon-success" />
          <span>Personalized Diagnostic Assessment</span>
        </div>

        {/* Hypothesis outcome badges */}
        <div className="adaptive-hypothesis-outcomes">
          {hypotheses.map(h => (
            <div
              key={h.hypothesis_id}
              className={`hypo-outcome-badge ${h.status}`}
            >
              {h.status === 'confirmed' && <CheckCircle2 size={14} />}
              {h.status === 'eliminated' && <XCircle size={14} />}
              <span className="hypo-outcome-name">{h.name}</span>
              <span className="hypo-outcome-pct">{Math.round(h.current_probability * 100)}%</span>
            </div>
          ))}
        </div>

        {/* Conclusion markdown */}
        {conclusion && (
          <div className="adaptive-conclusion-body">
            <MarkdownResponse content={conclusion} />
          </div>
        )}

        {/* Recommendations */}
        {personalized_recommendations.length > 0 && (
          <div className="adaptive-recommendations">
            <div className="rec-header">
              <Lightbulb size={14} />
              <span>Your Personalized Action Plan</span>
            </div>
            <ul>
              {personalized_recommendations.map((rec, i) => (
                <li key={i}>{rec}</li>
              ))}
            </ul>
          </div>
        )}

        {onClose && (
          <button className="adaptive-close-btn" onClick={onClose}>
            Close Assessment
          </button>
        )}
      </div>
    );
  }

  // Active questioning state
  return (
    <div className="adaptive-inquiry-card adaptive-active">
      {/* Header */}
      <div className="adaptive-header">
        <HelpCircle size={18} className="adaptive-icon" />
        <span>Adaptive Diagnostic Analysis</span>
        <span className="adaptive-turn-badge">
          Question {turn} of ~{max_questions}
        </span>
      </div>

      {/* Hypothesis confidence bars */}
      <div className="adaptive-hypotheses">
        <div className="hypo-section-label">
          <Brain size={13} />
          <span>Competing Hypotheses</span>
        </div>
        {hypotheses.map(h => (
          <div
            key={h.hypothesis_id}
            className={`hypo-bar-row ${h.status}`}
          >
            <div className="hypo-bar-label">
              {h.status === 'eliminated' && <XCircle size={12} className="hypo-eliminated-icon" />}
              <span className={h.status === 'eliminated' ? 'hypo-name-eliminated' : 'hypo-name'}>
                {h.name}
              </span>
            </div>
            <div className="hypo-bar-track">
              <div
                className={`hypo-bar-fill ${h.status}`}
                style={{ width: `${Math.round(h.current_probability * 100)}%` }}
              />
            </div>
            <span className="hypo-bar-pct">
              {Math.round(h.current_probability * 100)}%
            </span>
          </div>
        ))}
      </div>

      {/* Current question */}
      {current_question && (
        <div className={`adaptive-question-block ${animatingOut ? 'fade-out' : 'fade-in'}`}>
          <div className="adaptive-question-text">
            <Sparkles size={14} className="question-sparkle" />
            {current_question.question_text}
          </div>

          {current_question.reason && (
            <div className="adaptive-question-reason">
              <em>Why we're asking:</em> {current_question.reason}
            </div>
          )}

          {/* Answer option chips */}
          <div className="adaptive-options">
            {(current_question.options || []).map(opt => (
              <button
                key={opt.option_id}
                className={`adaptive-option-chip ${selectedOption === opt.option_id ? 'selected' : ''}`}
                onClick={() => handleAnswerClick(opt.option_id)}
                disabled={loading}
              >
                <span className="option-text">{opt.text}</span>
                <ChevronRight size={14} className="option-arrow" />
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Loading indicator during answer processing */}
      {loading && (
        <div className="adaptive-processing">
          <Loader2 size={16} className="spin" />
          <span>Updating diagnostic assessment...</span>
        </div>
      )}
    </div>
  );
};

export default AdaptiveInquiryCard;
