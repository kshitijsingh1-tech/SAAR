import React from 'react';
import {
  Zap, MessageSquare, BarChart2, ShieldCheck, Sliders,
  BookOpen, Layers, Sun, Moon, HelpCircle, Download,
  Sprout, Construction, Orbit
} from 'lucide-react';

export function Header({
  activeTab,
  onTabChange,
  selectedDomain,
  onDomainChange,
  theme,
  onToggleTheme,
  onOpenHelp,
  activeInvestigation,
  onExportDossier
}) {
  const domainIcons = {
    agriculture: <Sprout size={14} className="text-emerald" />,
    infrastructure: <Construction size={14} className="text-amber" />,
    astronomy: <Orbit size={14} className="text-purple" />
  };

  return (
    <header className="floating-header-capsule">
      {/* Brand Mark & Title */}
      <div className="brand-group" onClick={() => onTabChange('hero')} role="button" tabIndex={0}>
        <div className="brand-mark-capsule">
          <Zap size={16} />
        </div>
        <div className="brand-text">
          <div className="brand-title">
            <strong>SAAR</strong>
          </div>
          <span className="brand-subtitle">Scientific Reasoning Engine</span>
        </div>
      </div>

      {/* Domain Mode Switcher Pill */}
      <div className="domain-switcher-capsule">
        <button
          className={`domain-pill-btn ${selectedDomain === 'agriculture' ? 'active' : ''}`}
          onClick={() => onDomainChange('agriculture')}
          title="Crop Science & Agronomy"
        >
          <Sprout size={13} />
          <span>Crop Science</span>
        </button>
        <button
          className={`domain-pill-btn ${selectedDomain === 'infrastructure' ? 'active' : ''}`}
          onClick={() => onDomainChange('infrastructure')}
          title="Civil Infrastructure & Pavement"
        >
          <Construction size={13} />
          <span>Infrastructure</span>
        </button>
        <button
          className={`domain-pill-btn ${selectedDomain === 'astronomy' ? 'active' : ''}`}
          onClick={() => onDomainChange('astronomy')}
          title="Astrophysics & Spectroscopy"
        >
          <Orbit size={13} />
          <span>Astrophysics</span>
        </button>
      </div>

      {/* Main Navigation Tabs */}
      <nav className="header-nav-capsules">
        <button
          className={`capsule-nav-btn ${activeTab === 'hero' ? 'active' : ''}`}
          onClick={() => onTabChange('hero')}
        >
          <Zap size={14} />
          <span>Launchpad</span>
        </button>

        <button
          className={`capsule-nav-btn ${activeTab === 'assistant' ? 'active' : ''}`}
          onClick={() => onTabChange('assistant')}
        >
          <MessageSquare size={14} />
          <span>Investigation</span>
          {activeInvestigation?.open_questions?.length > 0 && (
            <span className="badge-pulse">{activeInvestigation.open_questions.length}</span>
          )}
        </button>

        <button
          className={`capsule-nav-btn ${activeTab === 'passport' ? 'active' : ''}`}
          onClick={() => onTabChange('passport')}
        >
          <ShieldCheck size={14} />
          <span>Readiness Passport</span>
        </button>

        <button
          className={`capsule-nav-btn ${activeTab === 'whatif' ? 'active' : ''}`}
          onClick={() => onTabChange('whatif')}
        >
          <Sliders size={14} />
          <span>What-If Simulator</span>
        </button>

        <button
          className={`capsule-nav-btn ${activeTab === 'analytics' ? 'active' : ''}`}
          onClick={() => onTabChange('analytics')}
        >
          <BarChart2 size={14} />
          <span>Causal Graph</span>
        </button>

        <button
          className={`capsule-nav-btn ${activeTab === 'rag' ? 'active' : ''}`}
          onClick={() => onTabChange('rag')}
        >
          <BookOpen size={14} />
          <span>Scientific References</span>
        </button>

      </nav>

      {/* Right Actions (Export, Theme, Help) */}
      <div className="header-actions-group">
        {activeInvestigation && (
          <button
            className="action-pill-btn export-btn"
            onClick={onExportDossier}
            title="Export Scientific Dossier"
          >
            <Download size={13} />
            <span>Export Dossier</span>
          </button>
        )}

        <button
          className="action-icon-btn"
          onClick={onOpenHelp}
          title="Saar Engine System Guide"
        >
          <HelpCircle size={15} />
        </button>
      </div>
    </header>
  );
}
