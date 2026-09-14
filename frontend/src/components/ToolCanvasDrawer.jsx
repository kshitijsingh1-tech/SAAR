import React, { useState, useEffect, useRef } from 'react';
import {
  X, Maximize2, Minimize2, BarChart2, BookOpen,
  Camera, GitFork, BookA, Crosshair, GripVertical, Sparkles, Activity, Zap, Award
} from 'lucide-react';
import { KnowledgeGraphCanvas } from './KnowledgeGraphCanvas';
import { ImageInspector } from './ImageInspector';
import { PlotlyGraphViewer } from './PlotlyGraphViewer';
import { DomainRAGRadar } from './DomainRAGRadar';
import { ScientificDictionaryDrawer } from './ScientificDictionaryDrawer';
import { GaitDashboard } from './GaitDashboard';
import { BadmintonDashboard } from './BadmintonDashboard';
import { DynamicOneStopVerdict } from './DynamicOneStopVerdict';

export function ToolCanvasDrawer({
  isOpen,
  onClose,
  activeTool,
  onSelectTool,
  unlockedTools = ['dictionary'],
  activeSessionId,
  activeInvestigation,
  investigationData,
  saarData,
  baselineData,
  theme,
  onSendToChat,
  selectedRelationship,
  selectedChartType,
  onSelectRelationship,
  customImageData,
  customImageUrl,
  onUploadCustomImage,
  onPasteImageUrl,
  cameraConnected,
  onCloseCamera,
  messages = [],
  selectedDomain = 'agriculture',
  selectedNodeId,
  onSelectNode,
  hasSensorData = true,
  onUploadSensorData = null,
  onLoadSampleDataset = null,
  customVideoFile = null,
  sessions = [],
  onSwitchSession = null,
  isProcessing = false,
  onExportDossier = null
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [drawerWidth, setDrawerWidth] = useState(() => {
    return Math.min(Math.round(window.innerWidth * 0.88), 1300);
  });
  const [isResizing, setIsResizing] = useState(false);

  const activePresetId = investigationData?.preset_id || activeInvestigation?.preset_id || null;

  // IDE-style split pane ratio (% width for left pane)
  const [splitRatio, setSplitRatio] = useState(48);
  const [isSplitResizing, setIsSplitResizing] = useState(false);
  const splitContainerRef = useRef(null);

  // Dragging handler for the internal junction between Image evidence and Knowledge graph
  useEffect(() => {
    const handleSplitMouseMove = (e) => {
      if (!isSplitResizing || !splitContainerRef.current) return;
      const rect = splitContainerRef.current.getBoundingClientRect();
      if (rect.width <= 0) return;
      const offsetX = e.clientX - rect.left;
      const newRatio = (offsetX / rect.width) * 100;
      // Clamp between 20% and 80% to ensure both panes stay comfortable and usable
      const clamped = Math.max(20, Math.min(80, newRatio));
      setSplitRatio(clamped);
    };

    const handleSplitMouseUp = () => {
      if (isSplitResizing) {
        setIsSplitResizing(false);
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
      }
    };

    if (isSplitResizing) {
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
      window.addEventListener('mousemove', handleSplitMouseMove);
      window.addEventListener('mouseup', handleSplitMouseUp);
    }

    return () => {
      window.removeEventListener('mousemove', handleSplitMouseMove);
      window.removeEventListener('mouseup', handleSplitMouseUp);
    };
  }, [isSplitResizing]);

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isResizing) return;
      const newWidth = window.innerWidth - e.clientX;
      const clamped = Math.max(450, Math.min(window.innerWidth - 60, newWidth));
      setDrawerWidth(clamped);
    };

    const handleMouseUp = () => {
      if (isResizing) {
        setIsResizing(false);
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
      }
    };

    if (isResizing) {
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing]);

  if (!isOpen) return null;

  const domainLower = String(selectedDomain || '').toLowerCase();
  const isPediatricsDomain = domainLower.includes('pediat') || domainLower.includes('gait') || domainLower.includes('toddle');
  const isSportsDomain = domainLower.includes('sport') || domainLower.includes('athlet') || domainLower.includes('badminton');
  const isAgriDomain = domainLower.includes('agri') || domainLower.includes('crop') || domainLower.includes('plant') || domainLower.includes('botan');
  const isInfraDomain = domainLower.includes('infra') || domainLower.includes('road') || domainLower.includes('gpr') || domainLower.includes('pave');
  const isAstroDomain = domainLower.includes('astro') || domainLower.includes('orbit') || domainLower.includes('transit');

  // Input detection:
  // Strictly honor activeTool first, then fall back to domain context
  const isGaitActive = activeTool === 'gait' || (isPediatricsDomain && activeTool !== 'badminton');
  const isBadmintonActive = (activeTool === 'badminton' || isSportsDomain) && !isGaitActive;

  // Configure tools uniquely for each domain, always preserving accessibility:
  let toolsMeta = [
    { id: 'verdict', label: 'One-Stop Verdict', icon: <Award size={15} className="text-amber" /> },
    { id: 'grounded', label: 'Image Analysis (Query & Graph)', icon: <Crosshair size={15} /> },
    { id: 'badminton', label: 'Badminton Biomechanics', icon: <Zap size={15} /> },
    { id: 'gait', label: 'Toddler Walking Screening', icon: <Activity size={15} /> },
    { id: 'graph', label: 'Causal Knowledge Graph', icon: <GitFork size={15} /> },
    { id: 'analytics', label: 'Sensor Analytics', icon: <BarChart2 size={15} />, badge: !hasSensorData ? 'Upload' : null },
    { id: 'rag', label: 'References', icon: <BookOpen size={15} /> },
    { id: 'dictionary', label: 'Scientific Dictionary', icon: <BookA size={15} /> }
  ];

  // Robust tool alias normalization
  const TOOL_ALIASES = {
    verdict: 'verdict',
    solution: 'verdict',
    solutions: 'verdict',
    executive: 'verdict',
    onestop: 'verdict',
    badminton: 'badminton',
    sports: 'badminton',
    biomechanics: 'badminton',
    telemetry: 'analytics',
    sensor: 'analytics',
    sensors: 'analytics',
    spectrometry: 'analytics',
    posture: 'gait',
    gait: 'gait',
    pediatrics: 'gait',
    morphology: 'grounded',
    camera: 'grounded',
    inspector: 'grounded',
    image: 'grounded',
    dict: 'dictionary',
    terms: 'dictionary',
    lexicon: 'dictionary'
  };

  // Filter tools strictly by the session's unlocked tools list (starts with only dictionary)
  const activeToolIds = Array.isArray(unlockedTools) && unlockedTools.length > 0 ? unlockedTools : ['dictionary'];
  const filteredToolsMeta = toolsMeta.filter((t) => activeToolIds.includes(t.id));
  const activeList = filteredToolsMeta.length > 0 ? filteredToolsMeta : toolsMeta.filter((t) => t.id === 'dictionary');

  const availableIds = activeList.map((t) => t.id);
  const defaultTool = availableIds[0] || 'dictionary';
  const aliased = TOOL_ALIASES[activeTool] || activeTool;
  const effectiveTool = availableIds.includes(aliased) ? aliased : defaultTool;

  const currentToolMeta = activeList.find((t) => t.id === effectiveTool) || activeList[0] || { id: 'dictionary', label: 'Scientific Dictionary', icon: <BookA size={15} /> };

  return (
    <aside
      className={`rollout-tool-canvas ${isExpanded ? 'fullscreen-expanded' : ''} ${isResizing ? 'is-resizing' : ''}`}
      style={!isExpanded ? { width: `${drawerWidth}px`, maxWidth: '96vw', transition: isResizing ? 'none' : 'width 0.2s cubic-bezier(0.16, 1, 0.3, 1)' } : {}}
    >
      {/* Draggable Resize Handle on Left Border */}
      {!isExpanded && (
        <div
          className="drawer-resize-handle"
          onMouseDown={(e) => {
            e.preventDefault();
            setIsResizing(true);
          }}
          title="Drag left/right to resize tool area"
        >
          <div className="resize-handle-pill">
            <GripVertical size={12} />
          </div>
        </div>
      )}

      {/* Tool Canvas Header Bar */}
      <div className="canvas-header">
        <div className="canvas-header-left">
          <div className="tool-active-icon">
            {currentToolMeta.icon}
          </div>

          {/* Tool Switcher Tabs */}
          <div className="tool-switcher-pills">
            {activeList.map((t) => (
              <button
                key={t.id}
                className={`tool-pill-btn ${effectiveTool === t.id ? 'active' : ''}`}
                onClick={() => onSelectTool(t.id)}
                title={t.label}
              >
                {t.icon}
                <span>{t.label}</span>
                {t.badge && (
                  <span style={{
                    fontSize: '0.62rem',
                    padding: '1px 5px',
                    borderRadius: '4px',
                    background: effectiveTool === t.id ? '#ffffff35' : '#e0f2fe',
                    color: effectiveTool === t.id ? '#ffffff' : '#0369a1',
                    fontWeight: '700',
                    marginLeft: '3px'
                  }}>
                    {t.badge}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Canvas Controls: Expand & Roll-In (Hide) */}
        <div className="canvas-header-actions">
          <button
            className="canvas-action-btn"
            onClick={() => setIsExpanded(!isExpanded)}
            title={isExpanded ? 'Exit Fullscreen (Restore window size)' : 'Fullscreen (Expand full-width)'}
          >
            {isExpanded ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
          </button>

          <button
            className="canvas-action-btn btn-close-tool"
            onClick={onClose}
            title="Roll In (Hide Tool Canvas)"
          >
            <X size={17} />
          </button>
        </div>
      </div>

      {/* Tool Content Body */}
      <div className="canvas-body">
        {/* Tool: Image Analysis Dashboard (Full-width, scrollable) */}
        {effectiveTool === 'grounded' && (
          <div
            className="tool-body-pane custom-pane-scrollbar"
            style={{
              flex: '1 1 0',
              height: '100%',
              minHeight: 0,
              maxHeight: '100%',
              overflow: 'auto',
              padding: '0',
              boxSizing: 'border-box',
              background: 'var(--bg-card)'
            }}
          >
            <ImageInspector
              theme={theme}
              preset={investigationData?.preset}
              presetId={activePresetId}
              customImageData={customImageData}
              customImageUrl={customImageUrl}
              onUploadCustom={onUploadCustomImage}
              onPasteUrl={onPasteImageUrl}
              vlmProvider="auto"
              cameraConnected={true}
              onCloseCamera={null}
              nodes={investigationData?.final_graph?.nodes || saarData?.graph_data?.nodes || []}
              selectedNodeId={selectedNodeId}
              onSelectNode={onSelectNode}
              onOpenTool={(toolId, node) => {
                if (node?.id && onSelectNode) onSelectNode(node.id);
                onSelectTool(toolId);
              }}
              onAskQuery={(q) => {
                if (onSendToChat) onSendToChat(q);
                if (onClose) onClose();
              }}
              onCloseDrawer={onClose}
              onOpenGlossary={() => onSelectTool('dictionary')}
              domain={selectedDomain}
              investigationData={investigationData}
              edges={investigationData?.final_graph?.edges || saarData?.graph_data?.edges || []}
              steps={investigationData?.steps || []}
              conclusion={investigationData?.conclusion || ''}
              baseline={investigationData?.baseline || null}
              saarData={saarData}
              sessions={sessions}
              activeSessionId={activeSessionId}
              onSwitchSession={onSwitchSession}
              isProcessing={isProcessing}
              overallConfidence={investigationData?.final_graph?.overall_confidence ?? saarData?.graph_data?.overall_confidence ?? null}
              activeHypothesis={investigationData?.final_graph?.active_hypothesis || null}
              uncertaintyScore={investigationData?.final_graph?.uncertainty_score ?? null}
            />
          </div>
        )}

        {/* Tool: One-Stop Verdict & Actionable Solution */}
        {effectiveTool === 'verdict' && (
          <div className="tool-body-pane custom-pane-scrollbar" style={{ overflowY: 'auto', height: '100%', padding: '1rem' }}>
            <DynamicOneStopVerdict
              investigationData={investigationData}
              saarData={saarData}
              activeInvestigation={activeInvestigation}
              selectedDomain={selectedDomain}
              onOpenTool={onSelectTool}
              theme={theme}
              onExportDossier={onExportDossier}
              onSendToChat={onSendToChat}
            />
          </div>
        )}

        {/* Tool 2: Knowledge Graph Canvas (KnowledgeGraphCanvas.jsx / GraphEngine) */}
        {effectiveTool === 'graph' && (
          <div className="tool-body-pane">
            <KnowledgeGraphCanvas
              activeInvestigation={saarData || investigationData}
              graphData={saarData?.graph_data || investigationData?.final_graph || null}
              theme={theme}
              selectedRelationship={selectedRelationship}
              selectedNodeId={selectedNodeId}
              onSelectNode={onSelectNode}
              onSendToChat={onSendToChat}
              isExpanded={isExpanded}
              onToggleExpand={() => setIsExpanded(!isExpanded)}
            />
          </div>
        )}



        {/* Tool 3: Telemetry & Trend Analytics (PlotlyGraphViewer.jsx / AnalyticsService) */}
        {effectiveTool === 'analytics' && (
          <div className="tool-body-pane">
            <div style={{ padding: '1rem' }}>
              <PlotlyGraphViewer
                saarData={saarData || investigationData}
                activeInvestigation={saarData || investigationData}
                selectedRelationship={selectedRelationship}
                chartType={selectedChartType || 'histogram'}
                theme={theme}
                height={520}
                onSelectTool={onSelectTool}
                onSendToChat={onSendToChat}
                hasSensorData={hasSensorData}
                onUploadSensorData={onUploadSensorData}
                onLoadSampleDataset={onLoadSampleDataset}
              />
            </div>
          </div>
        )}

        {/* Tool 4: Domain Literature RAG (DomainRAGRadar.jsx / RAGKnowledgeService) */}
        {effectiveTool === 'rag' && (
          <div className="tool-body-pane">
            <DomainRAGRadar
              theme={theme}
              selectedDomain={selectedDomain}
              onSendCitationToChat={(citeText) => {
                if (onSendToChat) onSendToChat(citeText);
              }}
            />
          </div>
        )}

        {/* Tool: Video Motion & Biomechanics Analysis (GaitDashboard.jsx) */}
        {effectiveTool === 'gait' && (
          <div className="tool-body-pane custom-pane-scrollbar" style={{ overflowY: 'auto', height: '100%' }}>
            <GaitDashboard
              onRegisterToChat={onSendToChat}
              initialResult={saarData}
              initialFile={customVideoFile}
              selectedDomain={selectedDomain}
            />
          </div>
        )}

        {/* Tool: Badminton Athletic Biomechanics (BadmintonDashboard.jsx) */}
        {effectiveTool === 'badminton' && (
          <div className="tool-body-pane custom-pane-scrollbar" style={{ overflowY: 'auto', height: '100%' }}>
            <BadmintonDashboard
              onRegisterToChat={onSendToChat}
              initialResult={saarData?.domain === 'sports' || saarData?.analysis_id ? saarData : null}
              initialFile={customVideoFile}
            />
          </div>
        )}

        {/* Tool: Scientific Dictionary (ScientificDictionaryDrawer.jsx) */}
        {effectiveTool === 'dictionary' && (
          <div className="tool-body-pane">
            <ScientificDictionaryDrawer
              activeInvestigation={activeInvestigation}
              saarData={saarData}
              investigationData={investigationData}
              selectedDomain={selectedDomain}
              onSendToChat={onSendToChat}
              theme={theme}
            />
          </div>
        )}
      </div>
    </aside>
  );
}
