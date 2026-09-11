import React from 'react';
import { DomainSelector } from './DomainSelector';
import { ImageInspector } from './ImageInspector';
import { KnowledgeGraphCanvas } from './KnowledgeGraphCanvas';
import { SaarFindingsPanel } from './SaarFindingsPanel';
import { Layers, Activity, Eye, BarChart2 } from 'lucide-react';

export function VisualAnalyticsPage({
  domains,
  selectedDomain,
  selectedPreset,
  onSelectDomain,
  onSelectPreset,
  investigationData,
  saarData,
  selectedRelationship,
  selectedChartType,
  onSelectRelationship,
  customImageData,
  customImageUrl,
  onUploadCustomImage,
  onPasteImageUrl,
  vlmProviderUsed,
  cameraConnected,
  onCloseCamera
}) {
  const currentStep = investigationData?.steps?.slice(-1)[0];
  const graphState = currentStep?.graph_snapshot;

  // If saarData is present from uploaded dataset, compute live graph
  const dynamicSaarGraph = React.useMemo(() => {
    if (!saarData || !saarData.relationships || saarData.relationships.length === 0) {
      return null;
    }

    const featureNames = new Set();
    saarData.relationships.forEach((r) => {
      if (r.source_feature) featureNames.add(r.source_feature);
      if (r.target_feature) featureNames.add(r.target_feature);
    });

    const nodes = [];
    Array.from(featureNames).forEach((fName) => {
      nodes.push({
        id: fName,
        label: fName,
        node_type: 'observation',
        confidence: 0.95
      });
    });

    (saarData.concepts || []).slice(0, 3).forEach((c, idx) => {
      const cId = c.concept_id || `concept_${idx}`;
      nodes.push({
        id: cId,
        label: c.name.length > 26 ? c.name.slice(0, 24) + '...' : c.name,
        node_type: 'hypothesis',
        confidence: c.confidence || 0.85
      });
    });

    const edges = [];
    saarData.relationships.slice(0, 8).forEach((r, idx) => {
      edges.push({
        id: `rel_${idx}`,
        source: r.source_feature,
        target: r.target_feature,
        relation_type: r.direction === 'positive' ? 'supports' : 'contradicts',
        confidence: Math.abs(r.strength || 0.8)
      });
    });

    (saarData.concepts || []).slice(0, 3).forEach((c, idx) => {
      const cId = c.concept_id || `concept_${idx}`;
      (c.supporting_relationships || []).forEach((relId) => {
        const rel = saarData.relationships.find((r) => r.relationship_id === relId);
        if (rel) {
          edges.push({
            id: `hypo_edge_${idx}_${rel.source_feature}`,
            source: rel.source_feature,
            target: cId,
            relation_type: 'causes',
            confidence: c.confidence || 0.85
          });
        }
      });
    });

    return {
      nodes,
      edges,
      overall_confidence: saarData.confidence || 0.92
    };
  }, [saarData]);

  const activeGraphToRender = dynamicSaarGraph || graphState;

  return (
    <div className="analytics-page-container">
      {/* Top Banner */}
      <div className="analytics-hero">
        <div>
          <h2><BarChart2 size={20} /> Visual Scientific Reasoning &amp; Analytics Monitor</h2>
          <p>Two-Division Workspace: Causal Relation Graph (Left) | Vision &amp; Statistical Analysis (Right)</p>
        </div>
      </div>

      {/* 2 DIVISIONS GRID AS DRAWN IN HANDWRITTEN SKETCH */}
      <div className="analytics-grid-2col">
        {/* DIVISION 1 (LEFT): Relation Graph Canvas & Scenario Presets */}
        <div className="analytics-col division-left">
          {/* Causal Belief Relation Graph Canvas */}
          <div className="panel relation-graph-panel" style={{ height: '520px', display: 'flex', flexDirection: 'column' }}>
            <div className="panel-title">
              <Activity size={14} />
              <span>Relation Graph &amp; Dynamic Causal Belief Canvas {saarData?.dataset?.filename ? `(${saarData.dataset.filename})` : ''}</span>
            </div>
            <div style={{ flex: 1, padding: '0.5rem', position: 'relative' }}>
              <KnowledgeGraphCanvas
                graphData={activeGraphToRender}
                graphState={activeGraphToRender}
                currentStep={currentStep}
                selectedRelationship={selectedRelationship}
              />
            </div>
          </div>

          {/* Reasoning Domain & Scenario Presets */}
          <section className="panel">
            <div className="panel-title">
              <Layers size={14} />
              <span>Reasoning Domain &amp; Scenario Presets</span>
            </div>
            <div style={{ padding: '1rem' }}>
              <DomainSelector
                domains={domains}
                selectedDomain={selectedDomain}
                selectedPreset={selectedPreset}
                onSelectDomain={onSelectDomain}
                onSelectPreset={onSelectPreset}
              />
            </div>
          </section>
        </div>

        {/* DIVISION 2 (RIGHT): Vision (Top) & Analysis (Bottom) */}
        <div className="analytics-col division-right">
          {/* VISION SECTION (Top Right) */}
          <div className="vision-section">
            <ImageInspector
              preset={domains.find((d) => d.id === selectedDomain)?.presets?.find((p) => p.id === selectedPreset)}
              activeStep={currentStep}
              customImageData={customImageData}
              customImageUrl={customImageUrl}
              onImageUploaded={(imgData, url) => {
                if (imgData) onUploadCustomImage(imgData);
                if (url) onPasteImageUrl(url);
              }}
              vlmProviderUsed={vlmProviderUsed || 'Auto Token Router (Active)'}
              cameraConnected={cameraConnected || Boolean(customImageData || customImageUrl)}
              onCloseCamera={onCloseCamera}
            />
          </div>

          {/* ANALYSIS SECTION (Bottom Right) with Histogram / Dot Plot Charts */}
          <div className="analysis-section">
            <SaarFindingsPanel
              saarData={saarData}
              selectedRelationship={selectedRelationship}
              selectedChartType={selectedChartType}
              onSelectRelationship={onSelectRelationship}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
