import React, { useState, useRef, useEffect } from 'react';
import {
  Wrench, GitFork, BarChart2, BookOpen, Camera,
  BookA, X, Crosshair, Activity
} from 'lucide-react';

export function ToolRolloutBar({ onOpenTool, activeTool, isDrawerOpen, floating = false }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const containerRef = useRef(null);

  // Operational Scientific Tools:
  const tools = [
    {
      id: 'gait',
      label: 'Toddler Gait Analysis',
      tooltip: 'Deterministic 33-point MediaPipe Pose Kinematics & Toddler Gait Screening',
      icon: <Activity size={17} />,
      gradient: 'linear-gradient(135deg, #06b6d4, #3b82f6)',
      glow: 'rgba(6, 182, 212, 0.45)'
    },
    {
      id: 'grounded',
      label: 'Grounded Split Graph',
      tooltip: 'Bidirectional Image-to-Knowledge Graph Linkage',
      icon: <Crosshair size={17} />,
      gradient: 'linear-gradient(135deg, #0284c7, #10b981)',
      glow: 'rgba(14, 165, 233, 0.45)'
    },
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
      label: 'Sensor Analytics',
      tooltip: 'Longitudinal Sensor Trends, 30-Day Timeline & Statistical Correlations',
      icon: <BarChart2 size={17} />,
      gradient: 'linear-gradient(135deg, #38bdf8, #0ea5e9)',
      glow: 'rgba(56, 189, 248, 0.45)'
    },
    {
      id: 'rag',
      label: 'Scientific References',
      tooltip: 'Peer-Reviewed Scientific Literature & Evidence References',
      icon: <BookOpen size={17} />,
      gradient: 'linear-gradient(135deg, #6366f1, #4f46e5)',
      glow: 'rgba(99, 102, 241, 0.45)'
    },
    {
      id: 'dictionary',
      label: 'Scientific Dictionary',
      tooltip: 'Scientific Nomenclature & Diagnostic Terminology Engine',
      icon: <BookA size={17} />,
      gradient: 'linear-gradient(135deg, #f59e0b, #d97706)',
      glow: 'rgba(245, 158, 11, 0.45)'
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
