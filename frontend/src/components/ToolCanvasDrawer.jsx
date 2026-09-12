import React, { useState, useEffect, useRef } from 'react';
import {
  X, Maximize2, Minimize2, BarChart2, BookOpen,
  Camera, GitFork, BookA, Crosshair, GripVertical, Sparkles, Activity
} from 'lucide-react';
import { KnowledgeGraphCanvas } from './KnowledgeGraphCanvas';
import { ImageInspector } from './ImageInspector';
import { PlotlyGraphViewer } from './PlotlyGraphViewer';
import { DomainRAGRadar } from './DomainRAGRadar';
import { ScientificDictionaryDrawer } from './ScientificDictionaryDrawer';
import { GaitDashboard } from './GaitDashboard';

export function ToolCanvasDrawer({
  isOpen,
  onClose,
  activeTool,
  onSelectTool,
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
  customVideoFile = null
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

  // Operational tools strictly for active scientific investigations
  // During movement/pediatric video analysis, hide irrelevant generic tools (sensor analytics, generic graph controls)
  const isMovementAnalysis = selectedDomain === 'pediatrics' || activeTool === 'gait';

  const allToolsMeta = [
    { id: 'grounded', label: 'Grounded Split Graph', icon: <Crosshair size={15} />, hideInMovement: true },
    { id: 'gait', label: 'Video Analysis', icon: <Activity size={15} /> },
    { id: 'graph', label: 'Causal Graph', icon: <GitFork size={15} />, hideInMovement: true },
    { id: 'camera', label: 'Evidence Monitor', icon: <Camera size={15} /> },
    { id: 'analytics', label: 'Sensor Analytics', icon: <BarChart2 size={15} />, badge: !hasSensorData ? 'Upload' : null, hideInMovement: true },
    { id: 'rag', label: isMovementAnalysis ? 'Clinical References' : 'Scientific References', icon: <BookOpen size={15} /> },
    { id: 'dictionary', label: 'Scientific Dictionary', icon: <BookA size={15} />, hideInMovement: true }
  ];

  const toolsMeta = isMovementAnalysis
    ? allToolsMeta.filter((t) => !t.hideInMovement)
    : allToolsMeta;

  const currentToolMeta = toolsMeta.find((t) => t.id === activeTool) || toolsMeta[0];

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
            {toolsMeta.map((t) => (
              <button
                key={t.id}
                className={`tool-pill-btn ${activeTool === t.id ? 'active' : ''}`}
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
                    background: activeTool === t.id ? '#ffffff35' : '#e0f2fe',
                    color: activeTool === t.id ? '#ffffff' : '#0369a1',
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
            title={isExpanded ? 'Restore window size' : 'Expand full-width'}
            style={{ width: 'auto', padding: '0.25rem 0.6rem', display: 'flex', alignItems: 'center', gap: '5px' }}
          >
            {isExpanded ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
            <span style={{ fontSize: '0.72rem', fontWeight: '600' }}>{isExpanded ? 'Exit Fullscreen' : 'Fullscreen'}</span>
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
        {/* Tool: Grounded Split View (Side-by-Side Synchronized Image + Graph with IDE-style Resizable Splitter) */}
        {activeTool === 'grounded' && (
          <div
            ref={splitContainerRef}
            className="tool-body-pane"
            style={{
              display: 'flex',
              flexDirection: 'row',
              flex: '1 1 0',
              height: '100%',
              minHeight: 0,
              maxHeight: '100%',
              overflow: 'hidden',
              padding: '0.65rem',
              gap: 0,
              position: 'relative',
              boxSizing: 'border-box'
            }}
          >
            {/* Left Pane: Image Evidence & Regional Labels */}
            <div
              className="split-left-pane custom-pane-scrollbar"
              style={{
                width: `calc(${splitRatio}% - 6px)`,
                minWidth: '280px',
                maxWidth: 'calc(100% - 280px)',
                height: '100%',
                maxHeight: '100%',
                minHeight: 0,
                overflowY: 'auto',
                overflowX: 'hidden',
                paddingRight: '0.65rem',
                display: 'block',
                flexShrink: 0,
                pointerEvents: isSplitResizing ? 'none' : 'auto',
                boxSizing: 'border-box'
              }}
            >
              <ImageInspector
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
                onOpenTool={(toolId) => onSelectTool(toolId)}
                onAskQuery={(q) => onSendToChat && onSendToChat(q)}
                onOpenGlossary={() => onSelectTool('dictionary')}
              />
            </div>

            {/* IDE-style Draggable Splitter Divider Junction */}
            <div
              className="ide-split-junction"
              onMouseDown={(e) => {
                e.preventDefault();
                setIsSplitResizing(true);
              }}
              onDoubleClick={() => setSplitRatio(48)}
              title="Drag junction to expand/shrink panels (Double-click to reset 50/50)"
              style={{
                width: '12px',
                margin: '0 -2px',
                cursor: 'col-resize',
                position: 'relative',
                zIndex: 20,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: isSplitResizing ? 'rgba(56, 189, 248, 0.12)' : 'transparent',
                transition: 'background 0.15s ease',
                userSelect: 'none',
                flexShrink: 0
              }}
            >
              {/* Vertical Rule Line */}
              <div
                style={{
                  width: '2px',
                  height: '100%',
                  background: isSplitResizing ? '#0284c7' : 'rgba(203, 213, 225, 0.75)',
                  borderRadius: '1px',
                  boxShadow: isSplitResizing ? '0 0 8px rgba(2, 132, 199, 0.6)' : 'none',
                  transition: 'all 0.15s ease'
                }}
              />

              {/* Centered Floating Grip Handle Pill */}
              <div
                style={{
                  position: 'absolute',
                  width: '16px',
                  height: '34px',
                  borderRadius: '4px',
                  background: isSplitResizing ? '#0284c7' : '#ffffff',
                  border: isSplitResizing ? '1px solid #38bdf8' : '1px solid #cbd5e1',
                  boxShadow: isSplitResizing
                    ? '0 0 10px rgba(56, 189, 248, 0.6)'
                    : '0 2px 5px rgba(0, 0, 0, 0.12)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: isSplitResizing ? '#ffffff' : '#64748b',
                  cursor: 'col-resize',
                  transition: 'all 0.15s ease'
                }}
              >
                <GripVertical size={12} />
              </div>
            </div>

            {/* Right Pane: Knowledge Graph Canvas */}
            <div
              style={{
                width: `calc(${100 - splitRatio}% - 6px)`,
                minWidth: '280px',
                height: '100%',
                maxHeight: '100%',
                minHeight: 0,
                paddingLeft: '0.65rem',
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden',
                flexShrink: 0,
                pointerEvents: isSplitResizing ? 'none' : 'auto',
                boxSizing: 'border-box'
              }}
            >
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
          </div>
        )}

        {/* Tool 1: Causal Knowledge Graph (KnowledgeGraphCanvas.jsx) */}
        {activeTool === 'graph' && (
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

        {/* Tool 2: Visual Photo Evidence Monitor (ImageInspector.jsx) */}
        {activeTool === 'camera' && (
          <div className="tool-body-pane custom-pane-scrollbar" style={{ height: '100%', maxHeight: '100%', minHeight: 0, overflowY: 'auto', padding: '0.65rem', display: 'block', boxSizing: 'border-box' }}>
            <ImageInspector
              preset={investigationData?.preset}
              presetId={activePresetId}
              customImageData={customImageData}
              customImageUrl={customImageUrl}
              onUploadCustom={onUploadCustomImage}
              onPasteUrl={onPasteImageUrl}
              vlmProvider="auto"
              cameraConnected={cameraConnected}
              onCloseCamera={onCloseCamera}
              nodes={investigationData?.final_graph?.nodes || saarData?.graph_data?.nodes || []}
              selectedNodeId={selectedNodeId}
              onSelectNode={onSelectNode}
              onOpenTool={(toolId) => onSelectTool(toolId)}
              onAskQuery={(q) => onSendToChat && onSendToChat(q)}
              onOpenGlossary={() => onSelectTool('dictionary')}
            />
          </div>
        )}



        {/* Tool 3: Telemetry & Trend Analytics (PlotlyGraphViewer.jsx / AnalyticsService) */}
        {activeTool === 'analytics' && (
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
        {activeTool === 'rag' && (
          <div className="tool-body-pane">
            <DomainRAGRadar
              theme={theme}
              onSendCitationToChat={(citeText) => {
                if (onSendToChat) onSendToChat(citeText);
              }}
            />
          </div>
        )}

        {/* Tool: Video Analysis (GaitDashboard.jsx) */}
        {activeTool === 'gait' && (
          <div className="tool-body-pane custom-pane-scrollbar" style={{ overflowY: 'auto', height: '100%' }}>
            <GaitDashboard
              onRegisterToChat={onSendToChat}
              initialResult={saarData}
              initialFile={customVideoFile}
            />
          </div>
        )}

        {/* Tool: Scientific Dictionary (ScientificDictionaryDrawer.jsx) */}
        {activeTool === 'dictionary' && (
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
