import React, { useState } from 'react';
import {
  ShieldAlert,
  Activity,
  UserCheck,
  AlertTriangle,
  Info,
  Calendar,
  CheckCircle2,
  Sparkles,
  Layers,
  ChevronDown,
  ChevronUp,
  FileCheck,
  Scale
} from 'lucide-react';

/**
 * ToddlerPostureCard
 * Computer-vision biomechanical posture & developmental screening card.
 * STRICT CLINICAL PRINCIPLE: Strictly identifies as a visual screening tool
 * and NOT a medical diagnostic substitute.
 */
export const ToddlerPostureCard = ({
  postureData = null,
  presetId = null,
  onAskSpecialist,
  onExportReport
}) => {
  const [showDisclaimerDetails, setShowDisclaimerDetails] = useState(false);
  const [activeTab, setActiveTab] = useState('metrics'); // 'metrics' | 'milestones' | 'guidance'

  const defaultData = {
    subjectAgeMonths: '18–24 Months',
    screeningClassification: 'Typical Physiologic Toddler Alignment',
    riskLevel: 'Low (Within Normal Developmental Bounds)',
    statusColor: '#38bdf8', // Primary Blue
    plumbLineDeviation: '5.8 mm anterior shift (Compensated)',
    metrics: [
      {
        name: 'Lumbar Lordosis Angle',
        measured: '38.5°',
        referenceRange: '30.0° – 45.0°',
        status: 'Physiologic',
        description: 'Compensatory adaptation to horizontal sacrum and anterior pelvic tilt.'
      },
      {
        name: 'Bilateral Genu Varum (Knee Bowing)',
        measured: '2.2 cm intercondylar gap',
        referenceRange: '< 3.0 cm (Physiologic <24 mo)',
        status: 'Symmetrical',
        description: 'Typical infantile physiologic bowing; expected to transition to neutral by 24–30 months.'
      },
      {
        name: 'Base of Support (Stance Width)',
        measured: '22.4 cm (Wide)',
        referenceRange: '18.0 – 26.0 cm',
        status: 'Typical Stability',
        description: 'Wide base of support provides rotational stability during early walking phase.'
      },
      {
        name: 'Medial Longitudinal Arch',
        measured: 'Flattened (Fat Pad)',
        referenceRange: 'Flexible flatfoot expected',
        status: 'Normal <3 yr',
        description: 'Benign infantile plantar fat pad obscures structural arch formation.'
      }
    ],
    whoMilestones: {
      expectedMilestone: 'WHO Milestone 6: Independent Walking',
      ageConcordance: 'Optimal (Achieved within 9–18 mo standard distribution)',
      posturalVigor: 'High Guard to Mid Guard transition observed',
      gaitCharacteristics: [
        'Short stride length with rapid step cadence',
        'Absence of mature heel-strike (flat-foot initial contact)',
        'Symmetrical weight-bearing with absent antalgic limp'
      ]
    },
    redFlags: [
      { symptom: 'Unilateral or Asymmetric Bowing', present: false },
      { symptom: 'Progressive deformity worsening past 24 months', present: false },
      { symptom: 'Joint stiffness, swelling, or pain upon ambulation', present: false },
      { symptom: 'Height percentile dropping below 3rd percentile', present: false }
    ],
    followUpGuidance: 'Routine developmental surveillance at next scheduled 24-month well-child pediatric checkup.'
  };

  const data = postureData || defaultData;

  return (
    <div
      className="toddler-posture-card animate-fade-in"
      style={{
        background: 'rgba(15, 23, 42, 0.94)',
        border: '1px solid rgba(56, 189, 248, 0.35)',
        borderRadius: '12px',
        padding: '1rem',
        marginTop: '0.85rem',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.35)',
        backdropFilter: 'blur(10px)',
        color: 'var(--text-main)'
      }}
    >
      {/* 1. MANDATORY CLINICAL SCREENING DISCLAIMER BANNER */}
      <div
        style={{
          background: 'rgba(239, 68, 68, 0.12)',
          border: '1px solid rgba(239, 68, 68, 0.35)',
          borderRadius: '8px',
          padding: '0.6rem 0.75rem',
          marginBottom: '0.85rem'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
            <ShieldAlert size={18} color="#ef4444" style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <div style={{ fontWeight: 800, fontSize: '0.78rem', color: '#f87171', letterSpacing: '0.02em', textTransform: 'uppercase' }}>
                Visual Screening Only — Not a Clinical Diagnosis
              </div>
              <div style={{ fontSize: '0.71rem', color: '#cbd5e1', marginTop: '2px', lineHeight: 1.35 }}>
                Automated 2D keypoint computer-vision estimation. This analysis is an assistive screening aid and must never replace clinical assessment, radiological imaging, or evaluation by a licensed pediatrician or pediatric orthopedic specialist.
              </div>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setShowDisclaimerDetails(!showDisclaimerDetails)}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#f87171',
              cursor: 'pointer',
              padding: '2px',
              display: 'flex',
              alignItems: 'center'
            }}
          >
            {showDisclaimerDetails ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </div>

        {showDisclaimerDetails && (
          <div style={{ marginTop: '0.5rem', paddingTop: '0.5rem', borderTop: '1px solid rgba(239, 68, 68, 0.2)', fontSize: '0.68rem', color: '#94a3b8', lineHeight: 1.4 }}>
            <strong>Screening Limitations:</strong> Perspective distortion, baggy clothing, non-orthogonal camera angles, and momentary toddler movement can induce variance in 2D angular estimation. Results should only be used to facilitate clinical discussions with health practitioners.
          </div>
        )}
      </div>

      {/* 2. Header: Age, Developmental Classification, and Status Badge */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '8px',
              background: 'rgba(56, 189, 248, 0.15)',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--primary)'
            }}
          >
            <Activity size={20} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontWeight: 800, fontSize: '0.96rem', color: '#ffffff' }}>
                Toddler Postural & Biomechanical Screening
              </span>
              <span
                style={{
                  fontSize: '0.65rem',
                  fontFamily: 'var(--font-mono)',
                  padding: '0.12rem 0.45rem',
                  borderRadius: '12px',
                  background: 'rgba(56, 189, 248, 0.15)',
                  color: 'var(--primary)',
                  fontWeight: 600
                }}
              >
                {data.subjectAgeMonths}
              </span>
            </div>
            <div style={{ fontSize: '0.76rem', color: '#94a3b8', marginTop: '2px' }}>
              {data.screeningClassification}
            </div>
          </div>
        </div>

        {/* Status Pill */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'flex-end',
            background: 'rgba(0, 0, 0, 0.3)',
            padding: '0.3rem 0.65rem',
            borderRadius: '8px',
            border: `1px solid ${data.statusColor}55`
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: data.statusColor, boxShadow: `0 0 8px ${data.statusColor}` }} />
            <span style={{ fontSize: '0.74rem', fontWeight: 700, color: data.statusColor }}>
              {data.riskLevel}
            </span>
          </div>
          <div style={{ fontSize: '0.66rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
            Plumb: <strong style={{ color: '#ffffff' }}>{data.plumbLineDeviation}</strong>
          </div>
        </div>
      </div>

      {/* 3. Navigation Tabs */}
      <div style={{ display: 'flex', borderBottom: '1px solid rgba(255,255,255,0.08)', marginBottom: '0.75rem', gap: '4px' }}>
        <button
          type="button"
          onClick={() => setActiveTab('metrics')}
          style={{
            padding: '0.35rem 0.65rem',
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'metrics' ? '2px solid var(--primary)' : '2px solid transparent',
            color: activeTab === 'metrics' ? '#ffffff' : 'var(--text-muted)',
            fontWeight: activeTab === 'metrics' ? 700 : 500,
            fontSize: '0.74rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '5px'
          }}
        >
          <Scale size={13} color={activeTab === 'metrics' ? 'var(--primary)' : 'currentColor'} />
          <span>Biomechanical Angles</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('milestones')}
          style={{
            padding: '0.35rem 0.65rem',
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'milestones' ? '2px solid #38bdf8' : '2px solid transparent',
            color: activeTab === 'milestones' ? '#ffffff' : 'var(--text-muted)',
            fontWeight: activeTab === 'milestones' ? 700 : 500,
            fontSize: '0.74rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '5px'
          }}
        >
          <UserCheck size={13} color={activeTab === 'milestones' ? '#38bdf8' : 'currentColor'} />
          <span>WHO Milestones & Gait</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('guidance')}
          style={{
            padding: '0.35rem 0.65rem',
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'guidance' ? '2px solid #38bdf8' : '2px solid transparent',
            color: activeTab === 'guidance' ? '#ffffff' : 'var(--text-muted)',
            fontWeight: activeTab === 'guidance' ? 700 : 500,
            fontSize: '0.74rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '5px'
          }}
        >
          <Info size={13} color={activeTab === 'guidance' ? '#38bdf8' : 'currentColor'} />
          <span>Surveillance & Red Flags</span>
        </button>
      </div>

      {/* 4. Tab Content */}
      {activeTab === 'metrics' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.55rem' }}>
          {data.metrics?.map((m, idx) => (
            <div
              key={idx}
              style={{
                background: 'rgba(0, 0, 0, 0.25)',
                border: '1px solid rgba(255, 255, 255, 0.07)',
                borderRadius: '8px',
                padding: '0.55rem 0.65rem'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '4px' }}>
                <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#e2e8f0' }}>{m.name}</span>
                <span
                  style={{
                    fontSize: '0.62rem',
                    fontFamily: 'var(--font-mono)',
                    padding: '0.1rem 0.35rem',
                    borderRadius: '4px',
                    background: 'rgba(56, 189, 248, 0.15)',
                    color: 'var(--primary)',
                    fontWeight: 600,
                    whiteSpace: 'nowrap'
                  }}
                >
                  {m.status}
                </span>
              </div>
              <div style={{ fontSize: '0.86rem', fontWeight: 800, color: 'var(--primary)', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
                {m.measured}
              </div>
              <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                Ref: {m.referenceRange}
              </div>
              <div style={{ fontSize: '0.67rem', color: '#94a3b8', marginTop: '4px', lineHeight: 1.3 }}>
                {m.description}
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'milestones' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.55rem', fontSize: '0.74rem' }}>
          <div style={{ background: 'rgba(0,0,0,0.25)', padding: '0.6rem 0.75rem', borderRadius: '8px', border: '1px solid rgba(56, 189, 248, 0.2)' }}>
            <div style={{ fontWeight: 700, color: '#38bdf8', marginBottom: '2px' }}>
              {data.whoMilestones?.expectedMilestone}
            </div>
            <div style={{ color: '#e2e8f0', fontSize: '0.72rem' }}>
              {data.whoMilestones?.ageConcordance}
            </div>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '3px' }}>
              Upper Limb Posture: <strong style={{ color: '#ffffff' }}>{data.whoMilestones?.posturalVigor}</strong>
            </div>
          </div>

          <div style={{ background: 'rgba(0,0,0,0.25)', padding: '0.6rem 0.75rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div style={{ fontWeight: 700, color: '#38bdf8', marginBottom: '4px' }}>Gait Biomechanics Observed:</div>
            <ul style={{ margin: '0 0 0 16px', padding: 0, color: '#cbd5e1', lineHeight: 1.45, fontSize: '0.71rem' }}>
              {data.whoMilestones?.gaitCharacteristics?.map((g, idx) => (
                <li key={idx} style={{ marginBottom: '2px' }}>{g}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {activeTab === 'guidance' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.55rem', fontSize: '0.74rem' }}>
          {/* Red Flag Screeners */}
          <div style={{ background: 'rgba(0,0,0,0.25)', padding: '0.6rem 0.75rem', borderRadius: '8px', border: '1px solid rgba(245, 158, 11, 0.2)' }}>
            <div style={{ fontWeight: 700, color: '#fbbf24', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '5px' }}>
              <AlertTriangle size={13} />
              <span>Red Flag Clinical Triggers (Prompt Specialist Referral if Present):</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '4px' }}>
              {data.redFlags?.map((flag, idx) => (
                <div key={idx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.7rem' }}>
                  <span style={{ color: '#e2e8f0' }}>{flag.symptom}</span>
                  <span style={{
                    padding: '0.08rem 0.4rem',
                    borderRadius: '4px',
                    background: flag.present ? 'rgba(239, 68, 68, 0.2)' : 'rgba(56, 189, 248, 0.12)',
                    color: flag.present ? '#f87171' : 'var(--primary)',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 600,
                    fontSize: '0.64rem'
                  }}>
                    {flag.present ? 'DETECTED (Alert)' : 'None Detected'}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div style={{ background: 'rgba(56, 189, 248, 0.08)', padding: '0.5rem 0.65rem', borderRadius: '6px', border: '1px solid rgba(56, 189, 248, 0.2)', color: '#bae6fd', fontSize: '0.71rem' }}>
            <strong>Follow-Up Recommendation:</strong> {data.followUpGuidance}
          </div>
        </div>
      )}

      {/* 5. Footer Actions */}
      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.85rem', paddingTop: '0.65rem', borderTop: '1px solid rgba(255,255,255,0.08)' }}>
        <button
          type="button"
          className="btn btn-primary"
          onClick={() => {
            if (onAskSpecialist) onAskSpecialist(`Explain the biomechanical significance of toddler lumbar lordosis (~38.5°) and symmetrical genu varum (2.2 cm gap) in a ${data.subjectAgeMonths} toddler.`);
          }}
          style={{
            flex: 1,
            fontSize: '0.74rem',
            padding: '0.4rem 0.65rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '5px'
          }}
        >
          <Sparkles size={13} />
          <span>Ask Pediatric Specialist</span>
        </button>

        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => {
            if (onExportReport) onExportReport(data);
          }}
          style={{
            fontSize: '0.74rem',
            padding: '0.4rem 0.65rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '5px'
          }}
        >
          <FileCheck size={13} color="var(--primary)" />
          <span>Export Summary</span>
        </button>
      </div>
    </div>
  );
};
export default ToddlerPostureCard;
