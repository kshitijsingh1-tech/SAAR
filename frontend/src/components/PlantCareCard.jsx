import React, { useState } from 'react';
import {
  Sprout,
  Droplets,
  Sun,
  ShieldAlert,
  Calendar,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Thermometer,
  Zap,
  ChevronRight,
  RefreshCw
} from 'lucide-react';

/**
 * PlantCareCard
 * Comprehensive botanical identification, foliar health/pathology diagnostic,
 * and prescriptive multi-step agronomic treatment & care plan.
 */
export const PlantCareCard = ({
  plantData = null,
  presetId = null,
  onApplyPrescription,
  onAskAgronomist
}) => {
  const [activeTab, setActiveTab] = useState('treatment'); // 'treatment' | 'irrigation' | 'nutrition' | 'environment'
  const [completedSteps, setCompletedSteps] = useState(new Set());

  // Default / fallback botanical diagnostic based on active preset
  const defaultData = presetId === 'agri_monstera_fenestration' || presetId === 'session-3'
    ? {
        commonName: 'Swiss Cheese Plant / Split-Leaf Philodendron',
        scientificName: 'Monstera deliciosa Liebm.',
        family: 'Araceae (Aroid)',
        healthScore: 94,
        healthStatus: 'Optimal Vigorous Vegetative State',
        statusColor: '#38bdf8', // Primary Blue
        pathologyDetected: 'None (Natural PCD Fenestration)',
        keyObservations: [
          'Morphological fenestrations are symmetrical Programmed Cell Death (PCD), not defoliation.',
          'Emergent juvenile apical shoot exhibits strong cellular turgor and healthy chlorophyll density.',
          'Substrate demonstrates adequate aeration porosity with low Pythium damping-off risk.'
        ],
        metrics: {
          chlorophyllSpad: '52.4 SPAD',
          psiiYield: '0.81 Fv/Fm (Optimal)',
          canopyTurgor: '96%',
          rootZoneOxygen: '18.2 mg/L'
        },
        prescription: {
          irrigation: {
            regime: 'Cycle-and-Soak Substrate Saturation',
            interval: 'Every 7–10 days when top 5cm substrate dries to <18% VWC',
            waterVolume: '750 mL room-temp filtered water (pH 6.0–6.5)',
            drainageCheck: 'Empty saucer within 20 mins to prevent anoxic root rot'
          },
          sunlight: {
            exposure: 'Bright Indirect Solar Radiation (East / Sheltered South)',
            ppfdTarget: '250 – 400 μmol/m²/s',
            dli: '12 – 16 mol/m²/day',
            warning: 'Avoid direct mid-day UV (>700 μmol) to prevent foliar photo-bleaching'
          },
          nutrition: {
            npkRatio: '3-1-2 Balanced Foliar Fertilizer',
            dilution: 'Half-strength (1.0 mS/cm EC) bi-weekly during vegetative flush',
            micronutrients: 'Chelated Magnesium (Mg) + Calcium (Ca) for fenestrated leaf margins',
            flushCycle: 'Monthly demineralized water flush to prevent salt crusting'
          },
          treatment: [
            {
              id: 'step_1',
              title: 'Substrate Aeration & Perlite Augmentation',
              priority: 'Maintenance',
              description: 'Incorporate 20% coarse chunky perlite and orchid bark to maintain macropore oxygenation.',
              timing: 'Immediate / Next repotting window'
            },
            {
              id: 'step_2',
              title: 'Foliar Dust Clearing & Stomatal Cleaning',
              priority: 'Weekly',
              description: 'Wipe adaxial leaf surfaces with damp micro-cloth to maximize photosynthetic photon capture.',
              timing: 'Every 7 days'
            },
            {
              id: 'step_3',
              title: 'Prophylactic Cold-Pressed Neem Oil Emulsion',
              priority: 'Preventative',
              description: 'Mist 0.5% neem oil with mild potassium soap emulsion to deter thrips and spider mites.',
              timing: 'Bi-weekly preventative spray'
            }
          ]
        }
      }
    : {
        commonName: 'Garden Tomato / Roma Truss',
        scientificName: 'Solanum lycopersicum L.',
        family: 'Solanaceae',
        healthScore: 58,
        healthStatus: 'Moderate Interveinal Foliar Chlorosis & Saturation',
        statusColor: '#f59e0b', // Amber
        pathologyDetected: 'Substrate Hypoxia & Secondary Iron (Fe)/Nitrogen (N) Translocation Deficit',
        keyObservations: [
          'Acute interveinal foliar chlorosis concentrated on lower canopy leaves.',
          'Continuous 2.8 L/hr drip emitter has elevated root zone moisture to 48.2% VWC (hypoxic threshold).',
          'Apical fruit truss development remains viable with 3.8°Bx brix sugar, but blossom-end rot risk is heightened.'
        ],
        metrics: {
          chlorophyllSpad: '34.2 SPAD (Depressed)',
          psiiYield: '0.64 Fv/Fm (Sub-optimal stress)',
          canopyTurgor: '81%',
          rootZoneOxygen: '4.1 mg/L (Hypoxic)'
        },
        prescription: {
          irrigation: {
            regime: 'Pulse-Pause Deficit Irrigation',
            interval: 'Suspend irrigation until substrate drops below 28% VWC',
            waterVolume: 'Reduce emitter volume to 1.2 L/hr in 3 spaced pulses',
            drainageCheck: 'Verify subsurface gravel trench discharge flow'
          },
          sunlight: {
            exposure: 'Full Sunlight with Diffuse Shade Netting during peak thermal hours',
            ppfdTarget: '600 – 900 μmol/m²/s',
            dli: '22 – 28 mol/m²/day',
            warning: 'Excessive heat (>34°C) accelerates blossom drop and reduces pollen viability'
          },
          nutrition: {
            npkRatio: '4-18-38 High-Potassium + Calcium Nitrate Regime',
            dilution: 'Chelated Iron (Fe-EDDHA) 5 ppm foliar spray to reverse chlorosis',
            micronutrients: 'Calcium Chloride (CaCl2) 0.5% foliar spray to prevent blossom-end rot',
            flushCycle: 'Leach root zone once VWC stabilizes to restore redox potential'
          },
          treatment: [
            {
              id: 'step_1',
              title: 'Immediate Irrigation Throttle & Aeration',
              priority: 'Urgent',
              description: 'Halt drip irrigation for 48 hours to restore root zone ATP phosphorylation and oxygen diffusion.',
              timing: 'Execute within 6 hours'
            },
            {
              id: 'step_2',
              title: 'Foliar Micronutrient Fe-EDDHA Application',
              priority: 'High',
              description: 'Spray 0.2% chelated iron solution directly on chlorotic leaves during early morning stomatal opening.',
              timing: 'Within 24 hours'
            },
            {
              id: 'step_3',
              title: 'Biological Inoculation with Bacillus amyloliquefaciens',
              priority: 'Protective',
              description: 'Drench root zone with bio-fungicide to prevent Pythium ultimum colonization in waterlogged soil.',
              timing: 'Day 3 after initial dry-down'
            }
          ]
        }
      };

  const data = plantData || defaultData;

  const toggleStep = (stepId) => {
    setCompletedSteps(prev => {
      const next = new Set(prev);
      if (next.has(stepId)) next.delete(stepId);
      else next.add(stepId);
      return next;
    });
  };

  return (
    <div
      className="plant-care-card animate-fade-in"
      style={{
        background: 'rgba(15, 23, 42, 0.92)',
        border: '1px solid rgba(56, 189, 248, 0.35)',
        borderRadius: '12px',
        padding: '1rem',
        marginTop: '0.85rem',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.35)',
        backdropFilter: 'blur(10px)',
        color: 'var(--text-main)'
      }}
    >
      {/* 1. Header: Botanical Species & Health Status Badge */}
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
            <Sprout size={20} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontWeight: 800, fontSize: '0.98rem', color: '#ffffff', letterSpacing: '-0.01em' }}>
                {data.commonName}
              </span>
              <span
                style={{
                  fontSize: '0.66rem',
                  fontFamily: 'var(--font-mono)',
                  padding: '0.12rem 0.45rem',
                  borderRadius: '12px',
                  background: 'rgba(56, 189, 248, 0.15)',
                  color: 'var(--primary)',
                  fontWeight: 600
                }}
              >
                {data.family}
              </span>
            </div>
            <div style={{ fontSize: '0.78rem', fontStyle: 'italic', color: '#94a3b8', marginTop: '2px' }}>
              {data.scientificName}
            </div>
          </div>
        </div>

        {/* Health Score Pill */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
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
              <span style={{ fontSize: '0.76rem', fontWeight: 700, color: data.statusColor }}>
                {data.healthStatus}
              </span>
            </div>
            <div style={{ fontSize: '0.66rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
              Vigor Score: <strong style={{ color: '#ffffff' }}>{data.healthScore}/100</strong>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Key Physiological Telemetry Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
          gap: '0.5rem',
          marginBottom: '0.85rem'
        }}
      >
        <div style={{ background: 'rgba(0, 0, 0, 0.3)', padding: '0.45rem 0.6rem', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)' }}>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Chlorophyll SPAD</div>
          <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#38bdf8', fontFamily: 'var(--font-mono)' }}>
            {data.metrics?.chlorophyllSpad}
          </div>
        </div>
        <div style={{ background: 'rgba(0, 0, 0, 0.3)', padding: '0.45rem 0.6rem', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)' }}>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>PSII Yield (Fv/Fm)</div>
          <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#38bdf8', fontFamily: 'var(--font-mono)' }}>
            {data.metrics?.psiiYield}
          </div>
        </div>
        <div style={{ background: 'rgba(0, 0, 0, 0.3)', padding: '0.45rem 0.6rem', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)' }}>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Foliar Turgor</div>
          <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#ffffff', fontFamily: 'var(--font-mono)' }}>
            {data.metrics?.canopyTurgor}
          </div>
        </div>
        <div style={{ background: 'rgba(0, 0, 0, 0.3)', padding: '0.45rem 0.6rem', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)' }}>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Root Zone Oxygen</div>
          <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#60a5fa', fontFamily: 'var(--font-mono)' }}>
            {data.metrics?.rootZoneOxygen}
          </div>
        </div>
      </div>

      {/* 3. Pathology & Foliar Symptoms Banner */}
      <div
        style={{
          background: 'rgba(245, 158, 11, 0.08)',
          border: '1px solid rgba(245, 158, 11, 0.25)',
          borderRadius: '8px',
          padding: '0.6rem 0.75rem',
          marginBottom: '0.85rem'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#fbbf24', fontWeight: 700, fontSize: '0.76rem', marginBottom: '4px' }}>
          <AlertTriangle size={14} />
          <span>Pathology / Symptom Diagnostics</span>
        </div>
        <div style={{ fontSize: '0.73rem', color: '#e2e8f0', lineHeight: 1.4 }}>
          {data.pathologyDetected}
        </div>
        <ul style={{ margin: '6px 0 0 16px', padding: 0, fontSize: '0.71rem', color: '#94a3b8', lineHeight: 1.45 }}>
          {data.keyObservations?.map((obs, idx) => (
            <li key={idx} style={{ marginBottom: '2px' }}>{obs}</li>
          ))}
        </ul>
      </div>

      {/* 4. Navigation Tabs for Prescriptive Care Plan */}
      <div style={{ display: 'flex', borderBottom: '1px solid rgba(255,255,255,0.08)', marginBottom: '0.75rem', gap: '4px' }}>
        <button
          type="button"
          onClick={() => setActiveTab('treatment')}
          style={{
            padding: '0.35rem 0.65rem',
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'treatment' ? '2px solid #38bdf8' : '2px solid transparent',
            color: activeTab === 'treatment' ? '#ffffff' : 'var(--text-muted)',
            fontWeight: activeTab === 'treatment' ? 700 : 500,
            fontSize: '0.74rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '5px'
          }}
        >
          <Sparkles size={13} color={activeTab === 'treatment' ? '#38bdf8' : 'currentColor'} />
          <span>Treatment Action Plan</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('irrigation')}
          style={{
            padding: '0.35rem 0.65rem',
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'irrigation' ? '2px solid #38bdf8' : '2px solid transparent',
            color: activeTab === 'irrigation' ? '#ffffff' : 'var(--text-muted)',
            fontWeight: activeTab === 'irrigation' ? 700 : 500,
            fontSize: '0.74rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '5px'
          }}
        >
          <Droplets size={13} color={activeTab === 'irrigation' ? '#38bdf8' : 'currentColor'} />
          <span>Irrigation Regime</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('nutrition')}
          style={{
            padding: '0.35rem 0.65rem',
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'nutrition' ? '2px solid #38bdf8' : '2px solid transparent',
            color: activeTab === 'nutrition' ? '#ffffff' : 'var(--text-muted)',
            fontWeight: activeTab === 'nutrition' ? 700 : 500,
            fontSize: '0.74rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '5px'
          }}
        >
          <Zap size={13} color={activeTab === 'nutrition' ? '#38bdf8' : 'currentColor'} />
          <span>Nutrition & Soil</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('environment')}
          style={{
            padding: '0.35rem 0.65rem',
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'environment' ? '2px solid #38bdf8' : '2px solid transparent',
            color: activeTab === 'environment' ? '#ffffff' : 'var(--text-muted)',
            fontWeight: activeTab === 'environment' ? 700 : 500,
            fontSize: '0.74rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '5px'
          }}
        >
          <Sun size={13} color={activeTab === 'environment' ? '#38bdf8' : 'currentColor'} />
          <span>Light & Solar</span>
        </button>
      </div>

      {/* 5. Tab Content Panes */}
      {activeTab === 'treatment' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {data.prescription?.treatment?.map((step) => {
            const isDone = completedSteps.has(step.id);
            return (
              <div
                key={step.id}
                onClick={() => toggleStep(step.id)}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '8px',
                  background: isDone ? 'rgba(56, 189, 248, 0.08)' : 'rgba(0, 0, 0, 0.25)',
                  border: isDone ? '1px solid rgba(56, 189, 248, 0.3)' : '1px solid rgba(255, 255, 255, 0.06)',
                  borderRadius: '8px',
                  padding: '0.55rem 0.7rem',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                <div style={{ marginTop: '2px', color: isDone ? '#38bdf8' : 'var(--text-muted)' }}>
                  <CheckCircle2 size={16} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '4px' }}>
                    <span style={{
                      fontWeight: 700,
                      fontSize: '0.78rem',
                      color: isDone ? '#94a3b8' : '#ffffff',
                      textDecoration: isDone ? 'line-through' : 'none'
                    }}>
                      {step.title}
                    </span>
                    <span style={{
                      fontSize: '0.62rem',
                      fontFamily: 'var(--font-mono)',
                      padding: '0.1rem 0.35rem',
                      borderRadius: '4px',
                      background: step.priority === 'Urgent' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(56, 189, 248, 0.15)',
                      color: step.priority === 'Urgent' ? '#f87171' : 'var(--primary)',
                      fontWeight: 600
                    }}>
                      {step.priority}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.71rem', color: '#cbd5e1', marginTop: '2px', lineHeight: 1.35 }}>
                    {step.description}
                  </div>
                  <div style={{ fontSize: '0.64rem', color: 'var(--text-muted)', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Calendar size={11} />
                    <span>Target Schedule: {step.timing}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {activeTab === 'irrigation' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.74rem' }}>
          <div style={{ background: 'rgba(0,0,0,0.25)', padding: '0.6rem 0.75rem', borderRadius: '8px', border: '1px solid rgba(56, 189, 248, 0.15)' }}>
            <div style={{ fontWeight: 700, color: '#38bdf8', marginBottom: '2px' }}>Regime Strategy:</div>
            <div style={{ color: '#e2e8f0' }}>{data.prescription?.irrigation?.regime}</div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
            <div style={{ background: 'rgba(0,0,0,0.25)', padding: '0.5rem 0.65rem', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.65rem' }}>Frequency & Dry-Down:</div>
              <div style={{ color: '#ffffff', fontWeight: 600 }}>{data.prescription?.irrigation?.interval}</div>
            </div>
            <div style={{ background: 'rgba(0,0,0,0.25)', padding: '0.5rem 0.65rem', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.65rem' }}>Hydration Volume:</div>
              <div style={{ color: '#ffffff', fontWeight: 600 }}>{data.prescription?.irrigation?.waterVolume}</div>
            </div>
          </div>
          <div style={{ fontSize: '0.7rem', color: '#94a3b8', fontStyle: 'italic', padding: '0.2rem 0.4rem' }}>
            Note: {data.prescription?.irrigation?.drainageCheck}
          </div>
        </div>
      )}

      {activeTab === 'nutrition' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.74rem' }}>
          <div style={{ background: 'rgba(0,0,0,0.25)', padding: '0.6rem 0.75rem', borderRadius: '8px', border: '1px solid rgba(56, 189, 248, 0.2)' }}>
            <div style={{ fontWeight: 700, color: '#38bdf8', marginBottom: '2px' }}>Target N-P-K Ratio:</div>
            <div style={{ color: '#ffffff', fontWeight: 700, fontSize: '0.84rem', fontFamily: 'var(--font-mono)' }}>
              {data.prescription?.nutrition?.npkRatio}
            </div>
          </div>
          <div style={{ background: 'rgba(0,0,0,0.25)', padding: '0.5rem 0.65rem', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.65rem' }}>Dilution & Application EC:</div>
            <div style={{ color: '#e2e8f0' }}>{data.prescription?.nutrition?.dilution}</div>
          </div>
          <div style={{ background: 'rgba(0,0,0,0.25)', padding: '0.5rem 0.65rem', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.65rem' }}>Micronutrient Fortification:</div>
            <div style={{ color: '#e2e8f0' }}>{data.prescription?.nutrition?.micronutrients}</div>
          </div>
        </div>
      )}

      {activeTab === 'environment' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.74rem' }}>
          <div style={{ background: 'rgba(0,0,0,0.25)', padding: '0.6rem 0.75rem', borderRadius: '8px', border: '1px solid rgba(56, 189, 248, 0.2)' }}>
            <div style={{ fontWeight: 700, color: '#38bdf8', marginBottom: '2px' }}>Solar Exposure:</div>
            <div style={{ color: '#ffffff', fontWeight: 600 }}>{data.prescription?.sunlight?.exposure}</div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
            <div style={{ background: 'rgba(0,0,0,0.25)', padding: '0.5rem 0.65rem', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.65rem' }}>Target PPFD:</div>
              <div style={{ color: '#38bdf8', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>{data.prescription?.sunlight?.ppfdTarget}</div>
            </div>
            <div style={{ background: 'rgba(0,0,0,0.25)', padding: '0.5rem 0.65rem', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.65rem' }}>Daily Light Integral (DLI):</div>
              <div style={{ color: '#38bdf8', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>{data.prescription?.sunlight?.dli}</div>
            </div>
          </div>
          <div style={{ background: 'rgba(239, 68, 68, 0.08)', padding: '0.4rem 0.6rem', borderRadius: '6px', border: '1px solid rgba(239, 68, 68, 0.2)', color: '#fca5a5', fontSize: '0.68rem' }}>
            Warning: {data.prescription?.sunlight?.warning}
          </div>
        </div>
      )}

      {/* 6. Footer Actions */}
      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.85rem', paddingTop: '0.65rem', borderTop: '1px solid rgba(255,255,255,0.08)' }}>
        <button
          type="button"
          className="btn btn-primary"
          onClick={() => {
            if (onAskAgronomist) onAskAgronomist(`Explain the agronomic treatment plan for ${data.commonName} (${data.scientificName}) and how to implement the ${data.prescription?.nutrition?.npkRatio} fertilizer regime.`);
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
          <span>Ask Agronomist in Chat</span>
        </button>

        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => {
            if (onApplyPrescription) onApplyPrescription(data.prescription);
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
          <CheckCircle2 size={13} color="#38bdf8" />
          <span>Save Care Plan</span>
        </button>
      </div>
    </div>
  );
};
export default PlantCareCard;
