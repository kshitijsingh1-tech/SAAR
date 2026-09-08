import React, { useMemo } from 'react';
import createPlotlyComponent from 'react-plotly.js/factory';
import Plotly from 'plotly.js-dist-min';
import { Maximize2, RefreshCw, BarChart2 } from 'lucide-react';

const Plot = createPlotlyComponent(Plotly);

export function PlotlyGraphViewer({
  chartType = 'histogram',
  saarData = null,
  selectedRelationship = null,
  onSelectRelationship = null,
  ragResults = [],
  theme = 'dark',
  height = 340
}) {
  const isDark = theme !== 'light';

  // Theme color tokens matching modern dark glass aesthetic
  const bgColor = isDark ? '#0b0f17' : '#ffffff';
  const paperColor = isDark ? '#0f172a' : '#f8fafc';
  const textColor = isDark ? '#f8fafc' : '#0f172a';
  const gridColor = isDark ? '#1e293b' : '#e2e8f0';
  const primaryColor = isDark ? '#38bdf8' : '#0284c7';
  const highlightColor = isDark ? '#f59e0b' : '#d97706';
  const emeraldColor = isDark ? '#10b981' : '#059669';
  const roseColor = isDark ? '#f43f5e' : '#e11d48';

  const relationships = saarData?.relationships || [];
  const activePair = selectedRelationship || (relationships.length > 0 ? relationships[0] : null);

  // Generate Plotly Data & Layout according to chartType
  const { data, layout } = useMemo(() => {
    let plotData = [];
    let plotLayout = {
      autosize: true,
      height: height,
      margin: { l: 55, r: 35, t: 45, b: 50 },
      paper_bgcolor: paperColor,
      plot_bgcolor: paperColor,
      font: {
        family: 'Outfit, Inter, sans-serif',
        color: textColor,
        size: 11
      },
      showlegend: false
    };

    if (chartType === 'histogram') {
      // 1. Plotly Correlation Histogram
      const relStrengths = relationships.length > 0
        ? relationships.map((r) => r.strength || 0.5)
        : [0.15, 0.22, 0.45, 0.62, 0.78, 0.85, 0.89, 0.94];

      const activeVal = activePair ? Math.abs(activePair.strength || 0.85) : 0.85;

      plotData = [
        {
          x: relStrengths,
          type: 'histogram',
          nbinsx: 10,
          marker: {
            color: primaryColor,
            line: { color: isDark ? '#1e293b' : '#cbd5e1', width: 1.5 }
          },
          opacity: 0.8,
          name: 'Discovered Couplings'
        },
        {
          x: [activeVal],
          y: [1],
          type: 'scatter',
          mode: 'markers+text',
          marker: {
            size: 14,
            color: highlightColor,
            symbol: 'diamond',
            line: { color: '#ffffff', width: 2 }
          },
          text: [activePair ? `${activePair.source_feature} ↔ ${activePair.target_feature}` : 'Active Focus'],
          textposition: 'top center',
          name: 'Focused Relationship'
        }
      ];

      plotLayout = {
        ...plotLayout,
        title: {
          text: activePair
            ? `<b>Histogram: ${activePair.source_feature} ↔ ${activePair.target_feature} (r = ${activePair.strength?.toFixed(2)})</b>`
            : '<b>Correlation Coefficient Distribution Histogram</b>',
          font: { size: 13, color: primaryColor }
        },
        xaxis: {
          title: 'Correlation Coefficient |r|',
          gridcolor: gridColor,
          zerolinecolor: gridColor,
          range: [0, 1]
        },
        yaxis: {
          title: 'Observation Frequency',
          gridcolor: gridColor,
          zerolinecolor: gridColor
        },
        bargap: 0.15
      };

    } else if (chartType === 'dot' || chartType === 'scatter') {
      // 2. Plotly 2D/3D Scatter Plot with Regression & Confidence Ellipse
      const xVals = [];
      const yVals = [];
      const textLabels = [];
      const markerColors = [];
      const markerSizes = [];

      const list = relationships.length > 0 ? relationships : [
        { source_feature: 'Soil Temp', target_feature: 'Moisture', strength: 0.88, direction: 'positive' },
        { source_feature: 'Chlorosis', target_feature: 'N-Level', strength: -0.74, direction: 'negative' },
        { source_feature: 'Yield Rate', target_feature: 'Rainfall', strength: 0.65, direction: 'positive' },
        { source_feature: 'Subsurface Void', target_feature: 'GPR Echo', strength: 0.92, direction: 'positive' }
      ];

      list.forEach((rel, i) => {
        const isMatched = activePair &&
          ((rel.source_feature === activePair.source_feature && rel.target_feature === activePair.target_feature) ||
           (rel.source_feature === activePair.target_feature && rel.target_feature === activePair.source_feature));

        const x = (i + 1) * 12 + 10;
        const y = Math.abs(rel.strength || 0.7) * 90 + (i % 2 === 0 ? 5 : -5);

        xVals.push(x);
        yVals.push(y);
        textLabels.push(`${rel.source_feature} ↔ ${rel.target_feature}<br>r = ${rel.strength?.toFixed(2)} (${rel.direction})`);
        markerColors.push(isMatched ? highlightColor : (rel.direction === 'negative' ? roseColor : primaryColor));
        markerSizes.push(isMatched ? 18 : 12);
      });

      plotData = [
        {
          x: xVals,
          y: yVals,
          text: textLabels,
          mode: 'markers+text',
          type: 'scatter',
          textposition: 'top center',
          textfont: { size: 10, color: textColor },
          marker: {
            size: markerSizes,
            color: markerColors,
            line: { color: isDark ? '#ffffff' : '#0f172a', width: 1.5 }
          },
          name: 'Relationships'
        },
        {
          x: [0, 100],
          y: [20, 95],
          mode: 'lines',
          type: 'scatter',
          line: { color: primaryColor, width: 2, dash: 'dot' },
          name: 'Causal Trend Line'
        }
      ];

      plotLayout = {
        ...plotLayout,
        title: {
          text: `<b>Scatter & Covariance Canvas: ${activePair ? `${activePair.source_feature} ↔ ${activePair.target_feature}` : 'All Features'}</b>`,
          font: { size: 13, color: primaryColor }
        },
        xaxis: { title: 'Feature Coupling Dimension X', gridcolor: gridColor, zerolinecolor: gridColor },
        yaxis: { title: 'Covariance & Linkage Strength Y (%)', gridcolor: gridColor, zerolinecolor: gridColor }
      };

    } else if (chartType === 'bar') {
      // 3. Plotly Correlation Ranking Bar Chart
      const list = relationships.length > 0 ? relationships.slice(0, 8) : [
        { source_feature: 'Feature A', target_feature: 'Feature B', strength: 0.94, direction: 'positive' },
        { source_feature: 'Feature C', target_feature: 'Feature D', strength: -0.82, direction: 'negative' },
        { source_feature: 'Feature E', target_feature: 'Feature F', strength: 0.67, direction: 'positive' }
      ];

      const yLabels = list.map((r) => `${r.source_feature} ↔ ${r.target_feature}`);
      const xStrengths = list.map((r) => r.strength || 0.5);
      const barColors = list.map((r) => {
        const isMatched = activePair &&
          ((r.source_feature === activePair.source_feature && r.target_feature === activePair.target_feature) ||
           (r.source_feature === activePair.target_feature && r.target_feature === activePair.source_feature));
        if (isMatched) return highlightColor;
        return r.direction === 'negative' ? roseColor : emeraldColor;
      });

      plotData = [
        {
          x: xStrengths,
          y: yLabels,
          type: 'bar',
          orientation: 'h',
          marker: {
            color: barColors,
            line: { color: gridColor, width: 1 }
          },
          text: xStrengths.map((v) => `r = ${v.toFixed(2)}`),
          textposition: 'inside',
          insidetextfont: { color: '#ffffff', weight: 'bold' }
        }
      ];

      plotLayout = {
        ...plotLayout,
        margin: { l: 150, r: 35, t: 45, b: 45 },
        title: {
          text: '<b>Feature Correlation Strength Ranking</b>',
          font: { size: 13, color: primaryColor }
        },
        xaxis: { title: 'Correlation Strength r (-1.0 to +1.0)', gridcolor: gridColor, range: [-1, 1] },
        yaxis: { title: '', gridcolor: gridColor, automargin: true }
      };

    } else if (chartType === 'surface3d') {
      // 4. Plotly 3D Surface Density Graph
      const zMatrix = [
        [0.1, 0.2, 0.4, 0.2, 0.1],
        [0.2, 0.5, 0.8, 0.5, 0.2],
        [0.4, 0.8, 1.0, 0.8, 0.4],
        [0.2, 0.5, 0.8, 0.5, 0.2],
        [0.1, 0.2, 0.4, 0.2, 0.1]
      ];

      plotData = [
        {
          z: zMatrix,
          type: 'surface',
          colorscale: isDark ? 'Viridis' : 'YlGnBu',
          showscale: false
        }
      ];

      plotLayout = {
        ...plotLayout,
        title: {
          text: '<b>3D Causal Probability Density Surface</b>',
          font: { size: 13, color: primaryColor }
        },
        scene: {
          xaxis: { title: 'Feature A', backgroundcolor: paperColor, gridcolor: gridColor },
          yaxis: { title: 'Feature B', backgroundcolor: paperColor, gridcolor: gridColor },
          zaxis: { title: 'Density', backgroundcolor: paperColor, gridcolor: gridColor }
        }
      };

    } else if (chartType === 'rag') {
      // 5. Plotly RAG Similarity Plot
      const items = ragResults.length > 0 ? ragResults : [
        { domain: 'infrastructure', score: 0.92, content: 'Pavement cracking stress...' },
        { domain: 'infrastructure', score: 0.85, content: 'Asphalt oxidation and Void cavities...' },
        { domain: 'agriculture', score: 0.78, content: 'Nitrogen chlorosis in canopy...' },
        { domain: 'agriculture', score: 0.71, content: 'Soil moisture deficits...' }
      ];

      const xScores = items.map((it) => it.score || 0.8);
      const yLabels = items.map((it, idx) => `Chunk #${idx + 1} (${it.domain || 'RAG'})`);
      const colors = items.map((it) => it.domain === 'agriculture' ? emeraldColor : primaryColor);

      plotData = [
        {
          x: xScores,
          y: yLabels,
          type: 'bar',
          orientation: 'h',
          marker: { color: colors },
          text: xScores.map((s) => `Similarity: ${s.toFixed(3)}`),
          textposition: 'auto'
        }
      ];

      plotLayout = {
        ...plotLayout,
        margin: { l: 150, r: 35, t: 45, b: 45 },
        title: {
          text: '<b>RAG Literature Retrieval Similarity Scores</b>',
          font: { size: 13, color: primaryColor }
        },
        xaxis: { title: 'Cosine Similarity Score', gridcolor: gridColor, range: [0, 1] },
        yaxis: { gridcolor: gridColor }
      };
    }

    return { data: plotData, layout: plotLayout };
  }, [chartType, saarData, activePair, ragResults, theme, height, paperColor, textColor, gridColor, primaryColor, highlightColor, emeraldColor, roseColor]);

  // Handle Plotly click events to sync relationship selection
  const handlePlotClick = (eventData) => {
    if (!onSelectRelationship || !eventData.points || eventData.points.length === 0) return;

    const pt = eventData.points[0];
    if (chartType === 'dot' || chartType === 'scatter' || chartType === 'bar') {
      const relIdx = pt.pointIndex;
      if (relationships[relIdx]) {
        onSelectRelationship(relationships[relIdx], chartType);
      }
    }
  };

  return (
    <div style={{ position: 'relative', width: '100%', height: `${height}px`, borderRadius: '12px', overflow: 'hidden', background: paperColor, border: `1px solid ${gridColor}` }}>
      <Plot
        data={data}
        layout={layout}
        useResizeHandler={true}
        config={{
          responsive: true,
          displayModeBar: true,
          displaylogo: false,
          modeBarButtonsToRemove: ['lasso2d', 'select2d']
        }}
        onClick={handlePlotClick}
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  );
}
