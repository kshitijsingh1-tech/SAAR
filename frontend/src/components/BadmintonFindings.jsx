import React from 'react';
import {
  Sparkles, AlertCircle, CheckCircle2, ShieldCheck,
  ArrowRight, MessageSquare, AlertTriangle, Eye, Info
} from 'lucide-react';

/**
 * BadmintonFindings
 * Clean, crisp, and actionable presentation of prioritized action plans,
 * coaching drills, and asserted hypotheses.
 */
export function BadmintonFindings({
  findings = [],
  hypotheses = [],
  recommendations = [],
  prioritizedRecommendations = [],
  limitations = [],
  onSendToChat = null,
  onSelectFinding = null,
  activeFindingId = null
}) {
  const priorityBadgeStyle = {
    HIGH: { bg: '#fef2f2', border: '#fecaca', text: '#b91c1c' },
    MEDIUM: { bg: '#fefce8', border: '#fef08a', text: '#854d0e' },
    LOW: { bg: '#f0f9ff', border: '#bae6fd', text: '#0369a1' }
  };

  const hasActionPlans = (prioritizedRecommendations && prioritizedRecommendations.length > 0) || (recommendations && recommendations.length > 0);
  const hasHypotheses = hypotheses && hypotheses.length > 0;
  const hasLimitations = limitations && limitations.length > 0;

  return (
    <div
      className="badminton-findings-container"
      style={{
        background: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: '16px',
        padding: '18px 20px',
        boxShadow: '0 4px 20px -2px rgba(0,0,0,0.04)',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.9rem'
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.6rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sparkles size={18} color="#0284c7" />
          <h4 style={{ margin: 0, fontSize: '0.96rem', fontWeight: '800', color: '#0f172a' }}>
            Prioritized Recommendations & Action Plans
          </h4>
        </div>
        {prioritizedRecommendations.length > 0 && (
          <span style={{ background: '#e0f2fe', color: '#0369a1', padding: '2px 8px', borderRadius: '6px', fontSize: '0.72rem', fontWeight: '700' }}>
            {prioritizedRecommendations.length} Action Plans
          </span>
        )}
      </div>

      {/* 1. Prioritized Action Plans */}
      {hasActionPlans && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {prioritizedRecommendations && prioritizedRecommendations.length > 0 ? (
            prioritizedRecommendations.map((rec, idx) => {
              const pStyle = priorityBadgeStyle[rec.priority] || priorityBadgeStyle.MEDIUM;
              const isSelected = activeFindingId === rec.source_finding_id || activeFindingId === rec.recommendation_id;

              return (
                <div
                  key={rec.recommendation_id || idx}
                  style={{
                    background: isSelected ? '#f0f9ff' : '#f8fafc',
                    border: isSelected ? '1.5px solid #0284c7' : '1px solid #e2e8f0',
                    borderLeft: `3.5px solid ${isSelected ? '#0284c7' : pStyle.border}`,
                    borderRadius: '10px',
                    padding: '10px 14px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '6px',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px', flexWrap: 'wrap' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1, minWidth: '220px' }}>
                      <span
                        style={{
                          fontSize: '0.66rem',
                          fontWeight: '800',
                          padding: '1px 6px',
                          borderRadius: '4px',
                          background: pStyle.bg,
                          color: pStyle.text,
                          border: `1px solid ${pStyle.border}`,
                          flexShrink: 0
                        }}
                      >
                        {rec.priority}
                      </span>
                      <span style={{ fontWeight: '700', fontSize: '0.86rem', color: '#0f172a' }}>
                        {rec.title}
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0 }}>
                      {onSelectFinding && (
                        <button
                          onClick={() => onSelectFinding(rec)}
                          style={{
                            background: isSelected ? '#0284c7' : '#e0f2fe',
                            border: '1px solid #bae6fd',
                            color: isSelected ? '#ffffff' : '#0369a1',
                            borderRadius: '6px',
                            padding: '3px 8px',
                            fontSize: '0.72rem',
                            fontWeight: '700',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px',
                            transition: 'all 0.15s ease'
                          }}
                          title={`Jump to video timestamp & graph node`}
                        >
                          <Eye size={12} />
                          <span>{isSelected ? 'Focused' : 'Evidence'}</span>
                        </button>
                      )}

                      {onSendToChat && (
                        <button
                          onClick={() => onSendToChat(`Explain the training drill for "${rec.title}": ${rec.actionable_drill || rec.recommendation}`)}
                          style={{
                            background: '#ffffff',
                            border: '1px solid #cbd5e1',
                            color: '#475569',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '3px',
                            fontSize: '0.72rem',
                            fontWeight: '600',
                            padding: '3px 7px',
                            borderRadius: '6px'
                          }}
                          title="Discuss in Chat"
                        >
                          <MessageSquare size={11} />
                          <span>Chat</span>
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Concise Recommendation & Actionable Drill */}
                  <div style={{ fontSize: '0.80rem', color: '#334155', lineHeight: '1.4' }}>
                    {rec.recommendation}
                  </div>
                  {rec.actionable_drill && (
                    <div style={{ fontSize: '0.76rem', color: '#15803d', background: '#f0fdf4', padding: '4px 8px', borderRadius: '6px', border: '1px solid #bbf7d0' }}>
                      <strong>Drill:</strong> {rec.actionable_drill}
                    </div>
                  )}
                </div>
              );
            })
          ) : (
            recommendations.map((r, idx) => (
              <div key={idx} style={{ fontSize: '0.82rem', color: '#334155', background: '#f8fafc', border: '1px solid #e2e8f0', padding: '8px 12px', borderRadius: '8px' }}>
                • {r}
              </div>
            ))
          )}
        </div>
      )}

      {/* 2. Hypotheses (if present) */}
      {hasHypotheses && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
          <div style={{ fontSize: '0.74rem', fontWeight: '800', color: '#7c3aed', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Asserted Multi-Signal Hypotheses
          </div>
          {hypotheses.map((hypo, idx) => {
            const rawText = typeof hypo === 'string' ? hypo : (hypo?.title || hypo?.text || '');
            let cleanText = rawText.replace(/^[A-Z0-9_]+:\s*/, '');
            const sourceId = `hypo_${idx + 1}`;
            const isSelected = activeFindingId === sourceId;

            return (
              <div
                key={idx}
                style={{
                  background: isSelected ? '#faf5ff' : '#ffffff',
                  border: isSelected ? '1.5px solid #7c3aed' : '1px solid #f1e8ff',
                  borderLeft: '3.5px solid #9333ea',
                  borderRadius: '8px',
                  padding: '6px 12px',
                  fontSize: '0.78rem',
                  color: '#4c1d95',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '8px'
                }}
              >
                <span>{cleanText}</span>
                {onSelectFinding && (
                  <button
                    onClick={() => onSelectFinding({ source_finding_id: sourceId, title: cleanText })}
                    style={{
                      background: '#f3e8ff',
                      border: '1px solid #d8b4fe',
                      color: '#7e22ce',
                      borderRadius: '5px',
                      padding: '2px 7px',
                      fontSize: '0.70rem',
                      fontWeight: '700',
                      cursor: 'pointer',
                      flexShrink: 0
                    }}
                  >
                    Inspect
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* 3. Limitations / Disclosures (if present) */}
      {hasLimitations && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
          <div style={{ fontSize: '0.74rem', fontWeight: '800', color: '#b45309', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Disclosures & Limitations
          </div>
          {limitations.map((lim, idx) => (
            <div
              key={idx}
              style={{
                background: '#fffbeb',
                border: '1px solid #fef08a',
                borderLeft: '3.5px solid #f59e0b',
                padding: '6px 10px',
                borderRadius: '6px',
                fontSize: '0.76rem',
                color: '#854d0e',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <AlertTriangle size={13} color="#d97706" style={{ flexShrink: 0 }} />
              <span>{lim}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
export default BadmintonFindings;
