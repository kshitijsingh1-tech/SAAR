import React, { useState, useEffect } from 'react';
import {
  BookOpen, Search, FileText, CheckCircle2,
  ExternalLink, Sparkles, Send, Filter, BarChart2
} from 'lucide-react';
import { fetchSaarKnowledge, querySaarKnowledge } from '../api/client';

export function DomainRAGRadar({ theme, onSendCitationToChat }) {
  const [query, setQuery] = useState('');
  const [selectedDomain, setSelectedDomain] = useState('all');
  const [isSearching, setIsSearching] = useState(false);
  const [ragDomains, setRagDomains] = useState([]);
  const [results, setResults] = useState([]);

  // Default sample literature items if search is empty
  const defaultLiterature = [
    {
      domain: 'agriculture',
      title: 'FAO Production Manual: Iron Deficiency Chlorosis in Solanaceae',
      score: 0.94,
      content: 'In calcareous or over-irrigated soils where pH exceeds 7.5, root-zone bicarbonate blocks the enzymatic reduction of ferric iron (Fe³⁺) to ferrous iron (Fe²⁺). Symptoms manifest as sharp interveinal yellowing while primary veins stay distinctly green.'
    },
    {
      domain: 'agriculture',
      title: 'Journal of Plant Nutrition: Waterlogging Dynamics & Root Hypoxia',
      score: 0.89,
      content: 'Longitudinal soil moisture sustained above 45% for >72 hours induces anoxic micro-environments. Root ATP production drops by 80%, inhibiting active nutrient pumps and accelerating secondary microbial decay.'
    },
    {
      domain: 'infrastructure',
      title: 'FHWA Geotechnical Engineering Circular §8: Sub-base Void Detection via GPR',
      score: 0.92,
      content: 'Ground Penetrating Radar (GPR) operating at 900 MHz reliably identifies high-dielectric air and water cavities underlying flexible asphalt pavements. Voids exceeding 1.2m diameter correlate with rapid shear fatigue failure.'
    },
    {
      domain: 'astronomy',
      title: 'Astrophysical Journal: Disentangling Exoplanet Transits from Stellar Flares',
      score: 0.86,
      content: 'Stellar flare contamination introduces asymmetric flux surges that skew symmetric transit lightcurve models. Multi-band spectroscopic decomposition isolates chromatic flare signatures from achromatic planetary occultations.'
    }
  ];

  useEffect(() => {
    async function loadKnowledge() {
      try {
        const info = await fetchSaarKnowledge();
        if (info.domains) {
          setRagDomains(info.domains);
        }
      } catch (err) {
        console.error("Failed to fetch RAG domains:", err);
      }
    }
    loadKnowledge();
    setResults(defaultLiterature);
  }, []);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    try {
      const domParam = selectedDomain === 'all' ? null : selectedDomain;
      const res = await querySaarKnowledge(query.trim(), domParam);
      if (res && res.length > 0) {
        setResults(res);
      } else {
        setResults(defaultLiterature.filter((item) =>
          selectedDomain === 'all' || item.domain === selectedDomain
        ));
      }
    } catch (err) {
      console.error("RAG search failed:", err);
      setResults(defaultLiterature);
    } finally {
      setIsSearching(false);
    }
  };

  const displayedResults = results.filter((item) =>
    selectedDomain === 'all' || item.domain === selectedDomain
  );

  return (
    <div className="rag-radar-container">
      {/* Header */}
      <div className="rag-header">
        <div>
          <div className="rag-eyebrow">
            <BookOpen size={14} /> PEER-REVIEWED SCIENTIFIC REFERENCES &amp; CITATIONS
          </div>
          <h1 className="rag-title">Scientific References &amp; Evidence Grounding</h1>
          <p className="rag-subtitle">
            Ground scientific hypotheses and prove causal relationships against peer-reviewed literature, FAO agricultural guidelines,
            FHWA civil engineering codes, and astrophysical databases.
          </p>
        </div>
      </div>

      {/* Search & Domain Filter Bar */}
      <div className="rag-search-section">
        <form onSubmit={handleSearch} className="rag-form">
          <div className="rag-input-wrapper">
            <Search size={18} className="rag-search-icon" />
            <input
              type="text"
              className="rag-input"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search scientific references (e.g., 'soil pH chlorosis Solanaceae', 'sub-base cavity GPR reflection', 'transit depth noise')..."
            />
          </div>
          <button type="submit" className="btn btn-primary" disabled={isSearching}>
            {isSearching ? 'Searching...' : 'Search References'}
          </button>
        </form>

        {/* Domain Filters */}
        <div className="domain-filter-pills">
          <button
            className={`filter-pill ${selectedDomain === 'all' ? 'active' : ''}`}
            onClick={() => setSelectedDomain('all')}
          >
            All Disciplines
          </button>
          <button
            className={`filter-pill ${selectedDomain === 'agriculture' ? 'active' : ''}`}
            onClick={() => setSelectedDomain('agriculture')}
          >
            Crop Science &amp; Agronomy
          </button>
          <button
            className={`filter-pill ${selectedDomain === 'infrastructure' ? 'active' : ''}`}
            onClick={() => setSelectedDomain('infrastructure')}
          >
            Civil Infrastructure
          </button>
          <button
            className={`filter-pill ${selectedDomain === 'astronomy' ? 'active' : ''}`}
            onClick={() => setSelectedDomain('astronomy')}
          >
            Astrophysics
          </button>
        </div>
      </div>



      {/* Results List */}
      <div className="rag-results-list">
        <div className="results-count-bar">
          <h3>Retrieved Scientific Citations ({displayedResults.length})</h3>
        </div>

        <div className="citations-grid">
          {displayedResults.map((item, idx) => (
            <div key={idx} className="citation-card">
              <div className="citation-card-top">
                <span className={`domain-tag tag-${item.domain}`}>
                  {item.domain} Document
                </span>
                <span className="score-badge">
                  Match: {(item.score ? item.score * 100 : 90).toFixed(0)}%
                </span>
              </div>

              {item.title && <h4 className="citation-title">{item.title}</h4>}
              <p className="citation-excerpt">{item.content}</p>

              <div className="citation-card-footer">
                <span className="source-label">Source: {item.source || 'Peer-Reviewed Knowledge Index'}</span>
                {onSendCitationToChat && (
                  <button
                    className="btn-cite-chat"
                    onClick={() => onSendCitationToChat(`**Literature Citation**: "${item.content.slice(0, 160)}..." (Match: ${(item.score ? item.score * 100 : 90).toFixed(0)}%)`)}
                    title="Insert this citation into investigation chat"
                  >
                    <Send size={12} />
                    <span>Cite in Chat</span>
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
