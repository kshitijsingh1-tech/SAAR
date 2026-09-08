import React from 'react';
import { Play, RotateCcw, CheckCircle2, AlertCircle, Wrench, ShieldCheck } from 'lucide-react';

export const WorkflowStepper = ({ steps, activeStepIndex, onStepClick, onRunFull, isRunning }) => {
  return (
    <div className="glass-panel" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column' }}>
      <div className="panel-title" style={{ justifyContent: 'space-between', marginBottom: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <RotateCcw size={18} color="var(--primary)" />
          <span>Dynamic Loop Execution Stepper & Workflow Audit</span>
        </div>
        <button
          className="btn-primary"
          onClick={onRunFull}
          disabled={isRunning}
          style={{ padding: '0.45rem 1rem', fontSize: '0.85rem' }}
        >
          <Play size={15} />
          {isRunning ? 'Running Loop...' : 'Run Dynamic Investigation'}
        </button>
      </div>

      {/* Horizontal Step Chips Bar */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${Math.max(1, steps.length)}, 1fr)`,
        gap: '0.5rem',
        marginBottom: '0.85rem'
      }}>
        {steps.map((step, idx) => {
          const isActive = idx === activeStepIndex;
          let color = '#38bdf8';
          if (step.state === 'FIND_UNKNOWNS') color = '#f59e0b';
          if (step.state === 'RUN_TOOL') color = '#c084fc';
          if (step.state === 'CONCLUSION') color = '#34d399';

          return (
            <button
              key={idx}
              onClick={() => onStepClick(idx)}
              style={{
                padding: '0.5rem 0.4rem',
                borderRadius: '8px',
                border: isActive ? `1px solid ${color}` : '1px solid var(--border-color)',
                background: isActive ? `${color}22` : 'rgba(255, 255, 255, 0.02)',
                color: isActive ? color : 'var(--text-muted)',
                cursor: 'pointer',
                textAlign: 'center',
                transition: 'all 0.2s ease',
                fontSize: '0.75rem',
                fontWeight: '600',
                fontFamily: 'var(--font-mono)'
              }}
            >
              Step #{step.step_number}
            </button>
          );
        })}
      </div>

      {/* Active Selected Step Log Card */}
      {steps[activeStepIndex] && (
        <div style={{
          padding: '0.85rem 1rem',
          borderRadius: '10px',
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid var(--primary)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.3rem' }}>
              <span className={`state-badge state-${steps[activeStepIndex].state}`}>
                {steps[activeStepIndex].state}
              </span>
              <span style={{ fontWeight: '700', fontSize: '0.9rem', color: 'var(--text-main)' }}>
                {steps[activeStepIndex].title}
              </span>
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              {steps[activeStepIndex].log_message}
            </div>
          </div>

          <div style={{ fontSize: '0.8rem', color: 'var(--primary)', fontFamily: 'var(--font-mono)', fontWeight: '600' }}>
            Active Step ({activeStepIndex + 1}/{steps.length})
          </div>
        </div>
      )}
    </div>
  );
};
