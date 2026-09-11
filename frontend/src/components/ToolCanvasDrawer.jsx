import React, { useState, useEffect } from 'react';
import {
  X, Maximize2, Minimize2, BarChart2, BookOpen,
  Camera, GitFork, BookA, Crosshair, GripVertical, Sparkles
} from 'lucide-react';
import { KnowledgeGraphCanvas } from './KnowledgeGraphCanvas';
import { ImageInspector } from './ImageInspector';
import { PlotlyGraphViewer } from './PlotlyGraphViewer';
import { DomainRAGRadar } from './DomainRAGRadar';
import { ScientificDictionaryDrawer } from './ScientificDictionaryDrawer';

export function ToolCanvasDrawer({
  isOpen,
  onClose,
  activeTool,
  onSelectTool,
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
  onSelectNode
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [drawerWidth, setDrawerWidth] = useState(() => {
    return Math.min(Math.round(window.innerWidth * 0.8), 1150);
  });
  const [isResizing, setIsResizing] = useState(false);

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
  const toolsMeta = [
    { id: 'grounded', label: 'Grounded Split Graph', icon: <Crosshair size={15} /> },
    { id: 'graph', label: 'Causal Graph', icon: <GitFork size={15} /> },
    { id: 'camera', label: 'Evidence Monitor', icon: <Camera size={15} /> },
    { id: 'spectrometer', label: 'Tissue Spectrometer', icon: <Sparkles size={15} /> },
    { id: 'analytics', label: 'Sensor Analytics', icon: <BarChart2 size={15} /> },
    { id: 'rag', label: 'Scientific References', icon: <BookOpen size={15} /> },
    { id: 'dictionary', label: 'Scientific Dictionary', icon: <BookA size={15} /> }
  ];

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
        {/* Tool: Grounded Split View (Side-by-Side Synchronized Image + Graph) */}
        {activeTool === 'grounded' && (
          <div className="tool-body-pane" style={{
            display: 'grid',
            gridTemplateColumns: 'minmax(320px, 1.1fr) minmax(340px, 1.25fr)',
            gap: '1rem',
            height: '100%',
            overflowY: 'auto',
            padding: '0.75rem'
          }}>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <ImageInspector
                preset={investigationData?.preset}
                presetId={investigationData?.preset_id || 'infra_damaged_road'}
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
            <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: '460px' }}>
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
          <div className="tool-body-pane">
            <ImageInspector
              preset={investigationData?.preset}
              presetId={investigationData?.preset_id || 'infra_damaged_road'}
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
