import React, { useState, useRef, useEffect } from 'react';
import {
  Wrench, GitFork, BarChart2, BookOpen, Camera,
  Layers, GitCompare, BookA, X
} from 'lucide-react';

export function ToolRolloutBar({ onOpenTool, activeTool, isDrawerOpen, floating = false }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const containerRef = useRef(null);

  // Tools specified in architecture:
  // 1. Knowledge Graph (KnowledgeGraphCanvas.jsx)
  // 2. Photo Evidence Monitor (ImageInspector.jsx)
  // 3. Telemetry & Trend Analytics (PlotlyGraphViewer.jsx / AnalyticsService)
  // 4. Multi-Domain Literature RAG (DomainRAGRadar.jsx / RAGKnowledgeService)
  // 5. Scientific Dictionary & Grounded Lexical Explorer (ScientificDictionaryDrawer.jsx)
  // 6. Benchmark Comparison: Single-Pass VLM vs Saar (BenchmarkComparison.jsx)
  // 7. Decoupled ReAct Architecture (ArchitectureView.jsx)
  const tools = [
    {
      id: 'graph',
      label: 'Causal Graph',
      tooltip: 'NetworkX Causal Knowledge Graph',
      icon: <GitFork size={17} />,
      gradient: 'linear-gradient(135deg, #a855f7, #6366f1)',
      glow: 'rgba(168, 85, 247, 0.45)'
    },
    {
      id: 'camera',
      label: 'Evidence Monitor',
      tooltip: 'High-Res Photo & Visual Inspection Monitor',
      icon: <Camera size={17} />,
      gradient: 'linear-gradient(135deg, #f43f5e, #e11d48)',
      glow: 'rgba(244, 63, 94, 0.45)'
    },
    {
      id: 'analytics',
      label: 'Telemetry Analytics',
      tooltip: 'Deterministic Correlations & Trends',
      icon: <BarChart2 size={17} />,
      gradient: 'linear-gradient(135deg, #38bdf8, #0ea5e9)',
      glow: 'rgba(56, 189, 248, 0.45)'
    },
    {
      id: 'rag',
      label: 'Literature RAG',
      tooltip: 'Multi-Domain BM25 Literature Index',
      icon: <BookOpen size={17} />,
      gradient: 'linear-gradient(135deg, #6366f1, #4f46e5)',
      glow: 'rgba(99, 102, 241, 0.45)'
    },
    {
      id: 'dictionary',
      label: 'Dictionary',
      tooltip: 'Scientific Dictionary & Grounded Lexical Explorer',
      icon: <BookA size={17} />,
      gradient: 'linear-gradient(135deg, #f59e0b, #d97706)',
      glow: 'rgba(245, 158, 11, 0.45)'
    },
    {
      id: 'benchmark',
      label: 'VLM Benchmark',
      tooltip: 'Single-Pass VLM vs Saar Audit Matrix',
      icon: <GitCompare size={17} />,
      gradient: 'linear-gradient(135deg, #10b981, #059669)',
      glow: 'rgba(16, 185, 129, 0.45)'
    },
    {
      id: 'architecture',
      label: 'Architecture',
      tooltip: 'Decoupled Multi-Agent Reasoning Engine',
      icon: <Layers size={17} />,
      gradient: 'linear-gradient(135deg, #8b5cf6, #ec4899)',
      glow: 'rgba(139, 92, 246, 0.45)'
    }
  ];

  useEffect(() => {
    function handleClickOutside(event) {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsExpanded(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleToolClick = (toolId) => {
    onOpenTool(toolId);
  };

  return (
    <div
      className={`flowing-tool-rollout-wrapper ${floating ? 'floating-in-chat' : ''}`}
      ref={containerRef}
    >
      {/* Flowing Stream of Round Tool Icons */}
      <div className={`round-icons-flow-stream ${isExpanded ? 'stream-rolled-out' : 'stream-rolled-in'}`}>
        {tools.map((t, index) => {
          const isActive = activeTool === t.id && isDrawerOpen;
          const delayStyle = {
            transitionDelay: isExpanded
              ? `${index * 35}ms`
              : `${(tools.length - 1 - index) * 25}ms`,
            background: t.gradient,
            boxShadow: isActive
              ? `0 0 16px ${t.glow}, 0 0 0 2px #ffffff`
              : `0 4px 14px ${t.glow}`
          };

          return (
            <div key={t.id} className="round-tool-item-wrapper">
              <button
                className={`round-tool-btn ${isActive ? 'tool-active' : ''}`}
                style={delayStyle}
                onClick={() => handleToolClick(t.id)}
                title={t.label}
              >
                {t.icon}
              </button>

              {/* Hover Tooltip Pill */}
              <div className="round-tool-tooltip">
                <strong>{t.label}</strong>
                <small>{t.tooltip}</small>
              </div>
            </div>
          );
        })}
      </div>

      {/* Main Round Flowing Action Trigger Button */}
      <div className="floating-trigger-item-wrapper">
        <button
          className={`round-flow-trigger-btn ${isExpanded ? 'is-open' : ''} ${isDrawerOpen ? 'drawer-active' : ''}`}
          onClick={() => setIsExpanded(!isExpanded)}
          title={isExpanded ? 'Roll in scientific tools' : 'Roll out scientific tools'}
        >
          <div className="trigger-icon-spin">
            {isExpanded ? <X size={20} /> : <Wrench size={19} />}
          </div>
          <span className="trigger-pulse-aura" />
        </button>

        {/* Trigger Tooltip */}
        {!isExpanded && (
          <div className="round-tool-tooltip trigger-tooltip">
            <strong>Scientific Tools</strong>
            <small>Click to roll out</small>
          </div>
        )}
      </div>
    </div>
  );
}
