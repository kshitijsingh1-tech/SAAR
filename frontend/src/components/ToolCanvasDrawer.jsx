import React, { useState } from 'react';
import {
  X, Maximize2, Minimize2, BarChart2, BookOpen,
  Layers, Camera, GitFork, GitCompare
} from 'lucide-react';
import { KnowledgeGraphCanvas } from './KnowledgeGraphCanvas';
import { ImageInspector } from './ImageInspector';
import { PlotlyGraphViewer } from './PlotlyGraphViewer';
import { DomainRAGRadar } from './DomainRAGRadar';
import { BenchmarkComparison } from './BenchmarkComparison';
import { ArchitectureView } from './ArchitectureView';

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
  onCloseCamera
}) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!isOpen) return null;

  // Tools strictly documented in architecture_explained.md
  const toolsMeta = [
    { id: 'graph', label: 'Causal Graph', icon: <GitFork size={15} /> },
    { id: 'camera', label: 'Evidence Monitor', icon: <Camera size={15} /> },
    { id: 'analytics', label: 'Telemetry Analytics', icon: <BarChart2 size={15} /> },
    { id: 'rag', label: 'Literature RAG', icon: <BookOpen size={15} /> },
    { id: 'benchmark', label: 'VLM Benchmark', icon: <GitCompare size={15} /> },
    { id: 'architecture', label: 'Architecture', icon: <Layers size={15} /> }
  ];

  const currentToolMeta = toolsMeta.find((t) => t.id === activeTool) || toolsMeta[0];

  return (
    <aside className={`rollout-tool-canvas ${isExpanded ? 'fullscreen-expanded' : ''}`}>
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
          >
            {isExpanded ? <Minimize2 size={15} /> : <Maximize2 size={15} />}
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
        {/* Tool 1: Causal Knowledge Graph (KnowledgeGraphCanvas.jsx) */}
        {activeTool === 'graph' && (
          <div className="tool-body-pane">
            <KnowledgeGraphCanvas
              activeInvestigation={saarData || investigationData}
              graphData={saarData?.graph_data || investigationData?.final_graph || null}
              theme={theme}
            />
          </div>
        )}

        {/* Tool 2: Visual Photo Evidence Monitor (ImageInspector.jsx) */}
        {activeTool === 'camera' && (
          <div className="tool-body-pane">
            <ImageInspector
              presetId={investigationData?.preset_id || 'infra_damaged_road'}
              customImageData={customImageData}
              customImageUrl={customImageUrl}
              onUploadCustom={onUploadCustomImage}
              onPasteUrl={onPasteImageUrl}
              vlmProvider="auto"
              cameraConnected={cameraConnected}
              onCloseCamera={onCloseCamera}
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

        {/* Tool 5: Benchmark Comparison (BenchmarkComparison.jsx) */}
        {activeTool === 'benchmark' && (
          <div className="tool-body-pane" style={{ padding: '1.25rem' }}>
            <BenchmarkComparison
              baseline={baselineData || {
                vlm_raw_response: 'Pavement shows superficial longitudinal and alligator distress. Possible asphalt oxidation.',
                vlm_explainability_score: 0.28,
                vlm_root_cause_accuracy: 0.35,
                vlm_tool_call_count: 0,
                saar_explainability_score: 0.97,
                saar_root_cause_accuracy: 0.95,
                saar_tool_call_count: 3,
                key_differences: [
                  'Single-pass VLM missed sub-surface void cavity completely (diagnosed only surface wear).',
                  'Saar dynamic ReAct loop detected high uncertainty and dispatched Ground Penetrating Radar tool.',
                  'GPR Scan detected 0.45m void piping cavity, increasing hypothesis confidence from 45% to 94%.'
                ]
              }}
            />
          </div>
        )}

        {/* Tool 6: System Architecture View (ArchitectureView.jsx) */}
        {activeTool === 'architecture' && (
          <div className="tool-body-pane">
            <ArchitectureView />
          </div>
        )}
      </div>
    </aside>
  );
}
