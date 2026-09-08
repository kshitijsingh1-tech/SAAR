import React from 'react';
import { Layers, Sparkles, Building2, Compass } from 'lucide-react';

export const DomainSelector = ({
  domains = [],
  selectedDomain,
  onSelectDomain,
  presets,
  selectedPreset,
  onSelectPreset
}) => {
  const activeDomainObj = domains.find((d) => d.id === selectedDomain);
  const currentPresets = presets || activeDomainObj?.presets || [];

  return (
    <div className="glass-panel" style={{ padding: '1rem', width: '100%' }}>
      <div className="panel-title" style={{ marginBottom: '0.75rem' }}>
        <Layers size={15} color="var(--primary)" />
        Select Reasoning Domain
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.6rem', marginBottom: '1rem' }}>
        {domains.map((d) => {
          const isSelected = selectedDomain === d.id;
          const Icon = d.id === 'infrastructure' ? Building2 : Compass;
          return (
            <button
              key={d.id}
              onClick={() => onSelectDomain(d.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.6rem 0.8rem',
                borderRadius: '8px',
                border: isSelected ? '1px solid var(--primary)' : '1px solid var(--border-color)',
                background: isSelected ? 'var(--primary-bg)' : 'var(--bg-card)',
                color: isSelected ? 'var(--primary)' : 'var(--text-main)',
                cursor: 'pointer',
                fontWeight: '600',
                fontSize: '0.82rem',
                transition: 'all 0.2s ease'
              }}
            >
              <Icon size={16} />
              <span>{d.name} Engine</span>
            </button>
          );
        })}
      </div>

      {currentPresets.length > 0 && (
        <>
          <div className="panel-title" style={{ fontSize: '0.78rem', marginBottom: '0.5rem' }}>
            <Sparkles size={13} color="var(--purple)" />
            Scenario Presets
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {currentPresets.map((preset) => {
              const isSel = selectedPreset === preset.id;
              return (
                <div
                  key={preset.id}
                  onClick={() => onSelectPreset(preset.id)}
                  style={{
                    padding: '0.6rem 0.8rem',
                    borderRadius: '6px',
                    border: isSel ? '1px solid var(--purple)' : '1px solid var(--border-color)',
                    background: isSel ? 'rgba(168, 85, 247, 0.1)' : 'var(--bg-card)',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                >
                  <div
                    style={{
                      fontWeight: '600',
                      fontSize: '0.82rem',
                      color: isSel ? 'var(--purple)' : 'var(--text-main)',
                      marginBottom: '0.15rem'
                    }}
                  >
                    {preset.title}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: '1.3' }}>
                    {preset.description}
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
};
