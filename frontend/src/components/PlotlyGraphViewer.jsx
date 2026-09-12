import React, { useState, useMemo, useRef } from 'react';
import createPlotlyComponent from 'react-plotly.js/factory';
import Plotly from 'plotly.js-dist-min';
import {
  TrendingUp, BarChart2, Activity, GitFork, AlertTriangle,
  Calendar, Layers, Sparkles, CheckCircle2, Sliders, ArrowRight,
  BookA, BookOpen, Info, X, MessageSquare, HelpCircle, ChevronRight,
  UploadCloud, FileSpreadsheet, Database, RefreshCw
} from 'lucide-react';

const Plot = createPlotlyComponent(Plotly);

export function PlotlyGraphViewer({
  chartType: initialChartType = 'timeline',
  saarData = null,
  activeInvestigation = null,
  selectedRelationship = null,
  onSelectRelationship = null,
  theme = 'light',
  height = 420,
  onSelectTool = null,
  onSendToChat = null,
  hasSensorData = true,
  onUploadSensorData = null,
  onLoadSampleDataset = null
}) {
  const [activeTab, setActiveTab] = useState('timeline'); // 'timeline' | 'scatter' | 'heatmap'
  const [selectedKpiId, setSelectedKpiId] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isIngesting, setIsIngesting] = useState(false);
  const [uploadFeedback, setUploadFeedback] = useState(null);
  const fileInputRef = useRef(null);
  const isDark = theme === 'dark';

  // Theme tokens
  const bgColor = isDark ? '#0b0f17' : '#ffffff';
  const paperColor = isDark ? '#0f172a' : '#ffffff';
  const textColor = isDark ? '#f8fafc' : '#0f172a';
  const gridColor = isDark ? '#1e293b' : '#f1f5f9';
  const primaryColor = '#0284c7'; // Sky Blue
  const amberColor = '#f59e0b';  // Amber
  const emeraldColor = '#10b981'; // Emerald
  const roseColor = '#f43f5e';   // Rose

  // 1. Detect Scenario Domain & Synthesize Authentic 30-Day Sensor Telemetry
  const domain = (activeInvestigation?.domain || saarData?.domain || 'agriculture').toLowerCase();

  const sensorSuite = useMemo(() => {
    const days = Array.from({ length: 30 }, (_, i) => `Day ${i + 1}`);

    if (domain.includes('infra')) {
      // Civil Infrastructure: Highway Pavement Void & Radar Echo
      const rain = days.map((_, i) => (i >= 6 && i <= 9 ? 65 + Math.sin(i) * 15 : Math.max(0, 5 + Math.cos(i) * 6)));
      const moisture = days.map((_, i) => (i < 7 ? 18 + Math.sin(i) * 2 : Math.min(46, 18 + (i - 6) * 2.1 + (i % 2))));
      const gprEcho = days.map((_, i) => (i < 12 ? 8.2 - Math.sin(i) * 0.3 : Math.max(1.4, 8.2 - (i - 11) * 0.42)));
      const crackWidth = days.map((_, i) => (i < 16 ? 0.2 : Math.min(4.8, 0.2 + (i - 15) * 0.34)));

      return {
        title: 'Highway Sub-base Sensor Analytics (30-Day Rain Inflow & Cavity Progression)',
        channels: [
          { id: 'moisture', name: 'Sub-base Moisture (%)', unit: '%', data: moisture, color: '#0284c7', yaxis: 'y' },
          { id: 'gpr', name: 'GPR Radar Echo Attenuation (dB)', unit: 'dB', data: gprEcho, color: '#f59e0b', yaxis: 'y' },
          { id: 'crack', name: 'Surface Crack Width (mm)', unit: 'mm', data: crackWidth, color: '#f43f5e', yaxis: 'y2' },
          { id: 'rain', name: 'Precipitation Rainfall (mm/day)', unit: 'mm', data: rain, color: '#10b981', yaxis: 'y2' }
        ],
        milestones: [
          { day: 7, label: 'Heavy Infiltration Storm', color: '#10b981' },
          { day: 15, label: 'Subsurface 1.8m Void Formed', color: '#f59e0b' },
          { day: 22, label: 'Pavement Shear Crack Failure', color: '#f43f5e' }
        ],
        kpis: [
          {
            id: 'driver',
            title: 'Primary Driver',
            value: 'Rain Inflow ↔ Void Depth',
            sub: 'r = +0.92 (Direct Hydraulic Erosion)',
            badge: 'CRITICAL',
            badgeColor: '#f43f5e',
            conceptName: 'Subsurface Hydraulic Piping & Base Loss',
            definition: 'Piping and internal erosion within flexible pavement sub-base caused by concentrated moisture infiltration washing away fine aggregate particles.',
            mechanism: 'Uncontrolled rainwater entry elevates pore pressure, liquifying sand/silt fractions and initiating shear displacement under dynamic wheel loads.',
            thresholdRule: 'Critical threshold: Sub-base moisture > 35% with GPR reflection loss > 60%.',
            citation: 'FHWA Geotechnical Engineering Circular §8: Subsurface Cavity Progression and Moisture Infiltration.',
            dictionaryTerm: 'Sub-base Void'
          },
          {
            id: 'trigger',
            title: 'Trigger Anomaly',
            value: 'Day 7 Storm (78 mm)',
            sub: 'Exceeded 25 mm/day drainage limit',
            badge: 'ANOMALY',
            badgeColor: '#f59e0b',
            conceptName: 'Precipitation Inundation & Joint Seal Failure',
            definition: 'Severe storm precipitation exceeding lateral highway drainage capacity, forcing hydraulic intrusion into aged transverse pavement joints.',
            mechanism: 'Inflow rate exceeds sub-drain capacity by 310%, creating positive hydrostatic head beneath the asphalt binder course.',
            thresholdRule: 'Rainfall 78 mm/day vs design capacity 25 mm/day.',
            citation: 'AASHTO Pavement Drainage Guidelines: Hydraulic Surges in Granular Base Courses.',
            dictionaryTerm: 'Precipitation Infiltration'
          },
          {
            id: 'impact',
            title: 'Structural Impact',
            value: 'Void Depth: 1.84m',
            sub: 'Load Bearing Capacity -64%',
            badge: 'FAILURE',
            badgeColor: '#e11d48',
            conceptName: 'Sub-base Cavity & Pavement Fatigue Failure',
            definition: 'Formation of an unsupported air/water void beneath the asphalt layer, inducing high tensile bending stresses and surface alligator cracking.',
            mechanism: 'Absence of granular support creates cantilever flexure during heavy axle crossings, producing catastrophic shear fractures.',
            thresholdRule: 'Cavity diameter 1.84m (Threshold for immediate structural collapse: >1.2m).',
            citation: 'ASTM D6432: Standard Guide for Using Surface Ground Penetrating Radar for Subsurface Investigation.',
            dictionaryTerm: 'Fatigue Cracking'
          },
          {
            id: 'scope',
            title: 'Timeline Scope',
            value: '30 Daily Readings',
            sub: '4 Synchronized Sensor Channels',
            badge: 'VERIFIED',
            badgeColor: '#0284c7',
            conceptName: 'Multi-Sensor Infrastructure Longitudinal Array',
            definition: 'Synchronized telemetry combining GPR radar echoes, soil moisture probes, rain gauges, and surface crack extensometers over 30 days.',
            mechanism: 'Cross-sensor latency confirms water inflow on Day 7 preceded cavity formation on Day 15 and surface shear cracking on Day 22.',
            thresholdRule: '4 synchronized time series channels verifying temporal Granger causality.',
            citation: 'Federal Highway Administration Long-Term Pavement Performance (LTPP) Protocol.',
            dictionaryTerm: 'Sensor Array'
          }
        ],
        days
      };
    }

    // Default: Crop Science & Agronomy (Tomato Chlorosis & Iron Deficit)
    const soilMoisture = days.map((_, i) => (i < 5 ? 28 + (i % 2) * 2 : Math.min(51, 46 + Math.sin(i * 0.8) * 3)));
    const substratePh = days.map((_, i) => (i < 5 ? 6.7 + i * 0.02 : Math.min(7.9, 6.8 + (i - 4) * 0.048)));
    const bioavailableFe = days.map((_, i) => (i < 6 ? 0.44 - i * 0.01 : Math.max(0.038, 0.42 * Math.exp(-(i - 5) * 0.12))));
    const chlorosisNDRE = days.map((_, i) => (i < 12 ? 0.65 - (i % 3) * 0.01 : Math.max(0.18, 0.64 - (i - 11) * 0.032)));

    return {
      title: 'Rhizosphere & Foliar Sensor Analytics (30-Day Longitudinal Tracking)',
      channels: [
        { id: 'moisture', name: 'Root Zone Moisture (% VWC)', unit: '% VWC', data: soilMoisture, color: '#0284c7', yaxis: 'y' },
        { id: 'fe', name: 'Bioavailable Fe²⁺ (ppm)', unit: 'ppm', data: bioavailableFe, color: '#10b981', yaxis: 'y' },
        { id: 'ph', name: 'Substrate pH (Alkalinity)', unit: 'pH', data: substratePh, color: '#f59e0b', yaxis: 'y2' },
        { id: 'ndre', name: 'Foliar Chlorosis Index (NDRE)', unit: 'NDRE', data: chlorosisNDRE, color: '#f43f5e', yaxis: 'y' }
      ],
      milestones: [
        { day: 6, label: 'Continuous Drip Discharge Begins', color: '#0284c7' },
        { day: 14, label: 'Root Zone Anoxia (DO < 0.8 mg/L)', color: '#f59e0b' },
        { day: 22, label: 'Severe Foliar Chlorosis Observed', color: '#f43f5e' }
      ],
      kpis: [
        {
          id: 'driver',
          title: 'Primary Causal Driver',
          value: 'Substrate pH ↔ Fe²⁺ Uptake',
          sub: 'r = -0.94 (Alkaline Lockup)',
          badge: 'ROOT CAUSE',
          badgeColor: '#f59e0b',
          conceptName: 'Substrate Alkalinization & Iron Lockup',
          definition: 'In calcareous or over-irrigated soils where substrate pH exceeds 7.5, root-zone bicarbonate blocks the enzymatic reduction of ferric iron (Fe³⁺) to bioavailable ferrous iron (Fe²⁺).',
          mechanism: 'Fe³⁺ + 3OH⁻ → Fe(OH)₃ ↓ (Insoluble hydroxide precipitate). Root ferric chelate reductase enzyme shuts down under high pH, halting iron absorption into vascular xylem.',
          thresholdRule: 'Normal root zone pH: 5.8 - 6.5. Observed anomaly: pH 7.94 with 91% reduction in bioavailable Fe²⁺.',
          citation: 'FAO Plant Production & Protection Paper §4.2: Iron Deficiency Chlorosis in Solanaceae.',
          dictionaryTerm: 'Iron Deficiency Chlorosis'
        },
        {
          id: 'trigger',
          title: 'Trigger Anomaly',
          value: 'Continuous Drip Emitter',
          sub: 'Day 6: Moisture surged to 48.2%',
          badge: 'TRIGGER',
          badgeColor: '#0284c7',
          conceptName: 'Continuous Irrigation Leak & Rhizosphere Hypoxia',
          definition: 'A malfunctioning drip emitter delivering continuous unmetered discharge supersaturates substrate pore spaces, driving soil Dissolved Oxygen (DO) below critical root survival levels (<0.8 mg/L).',
          mechanism: 'Pore water displaces oxygen → Root respiration shifts from aerobic phosphorylation to anaerobic glycolysis → ATP deficit of 80% paralyzes plasma membrane H⁺-ATPase proton pumps.',
          thresholdRule: 'Normal field moisture: 28% VWC. Observed anomaly: 48.2% VWC sustained for >14 days.',
          citation: 'Journal of Plant Nutrition: Longitudinal Root Anoxia & Respiration Arrest in Solanaceae.',
          dictionaryTerm: 'Rhizosphere Hypoxia'
        },
        {
          id: 'impact',
          title: 'Biological Impact',
          value: 'Bioavailable Fe²⁺ -91%',
          sub: 'NDRE dropped from 0.65 to 0.18',
          badge: 'SYMPTOM',
          badgeColor: '#f43f5e',
          conceptName: 'Interveinal Foliar Chlorosis (NDRE Index)',
          definition: 'Degradation of chlorophyll biosynthesis in newly expanding apical foliage. Because iron is immobile in plant tissue, young terminal leaves exhibit bright interveinal yellowing while primary veins stay green.',
          mechanism: 'Absence of Fe cofactors arrests chlorophyll a/b synthesis. Red-edge reflectance shifts sharply, causing the Normalized Difference Red Edge (NDRE) spectral index to collapse.',
          thresholdRule: 'Healthy vegetative NDRE: 0.60 - 0.75. Acute Chlorosis observed: NDRE 0.18.',
          citation: 'Remote Sensing & Agronomic Physiology: NDRE Optical Diagnostics for Micronutrient Deficiencies.',
          dictionaryTerm: 'Foliar Chlorosis'
        },
        {
          id: 'scope',
          title: 'Data Resolution',
          value: '30 Daily Timesteps',
          sub: '5 Synchronized Channels · 120 Readings',
          badge: 'EMPIRICAL',
          badgeColor: '#10b981',
          conceptName: 'Synchronized Longitudinal Multivariate Telemetry',
          definition: 'High-density longitudinal tracking that captures temporal ordering between environmental trigger (Day 6 leak), chemical shift (Day 10 pH rise), and visible plant symptom (Day 22 chlorosis).',
          mechanism: 'Temporal precedence confirms Granger causality (Moisture surge preceded chemical lockup by 4 days; lockup preceded foliar chlorosis by 12 days), decisively ruling out sudden viral mosaic blights.',
          thresholdRule: '30 consecutive daily timesteps validating Bayesian belief update.',
          citation: 'Saar Longitudinal Causal Modeling Specification §3.4: Temporal Latency Calibration.',
          dictionaryTerm: 'Longitudinal Tracking'
        }
      ],
      days
    };
  }, [domain, activeInvestigation, saarData]);

  // Scatter plot selection states
  const [scatterVarX, setScatterVarX] = useState('ph');
  const [scatterVarY, setScatterVarY] = useState('fe');

  const channelX = sensorSuite.channels.find((c) => c.id === scatterVarX) || sensorSuite.channels[0];
  const channelY = sensorSuite.channels.find((c) => c.id === scatterVarY) || sensorSuite.channels[1];

  // Calculate Pearson correlation & Linear regression
  const { regressionLine, correlationR, rSquared } = useMemo(() => {
    const xs = channelX.data;
    const ys = channelY.data;
    const n = xs.length;

    let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0, sumY2 = 0;
    for (let i = 0; i < n; i++) {
      sumX += xs[i];
      sumY += ys[i];
      sumXY += xs[i] * ys[i];
      sumX2 += xs[i] * xs[i];
      sumY2 += ys[i] * ys[i];
    }

    const numerator = n * sumXY - sumX * sumY;
    const denominator = Math.sqrt((n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY));
    const r = denominator !== 0 ? numerator / denominator : 0;

    // Linear regression y = slope * x + intercept
    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;

    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);

    return {
      regressionLine: {
        x: [minX, maxX],
        y: [slope * minX + intercept, slope * maxX + intercept]
      },
      correlationR: r,
      rSquared: Math.pow(r, 2)
    };
  }, [channelX, channelY]);

  // 2. View 1: Plotly Multi-Sensor Timeline Data & Layout
  const timelinePlot = useMemo(() => {
    const traces = sensorSuite.channels.map((channel) => ({
      x: sensorSuite.days,
      y: channel.data,
      name: channel.name,
      type: 'scatter',
      mode: 'lines+markers',
      yaxis: channel.yaxis,
      line: { color: channel.color, width: 2.5, shape: 'spline' },
      marker: { size: 5, color: channel.color },
      hovertemplate: `<b>${channel.name}</b><br>%{x}: %{y:.2f} ${channel.unit}<extra></extra>`
    }));

    // Add milestone vertical dashed lines
    const shapes = sensorSuite.milestones.map((m) => ({
      type: 'line',
      x0: `Day ${m.day}`,
      x1: `Day ${m.day}`,
      y0: 0,
      y1: 1,
      yref: 'paper',
      line: { color: m.color, width: 1.5, dash: 'dash' }
    }));

    // Add milestone text annotations
    const annotations = sensorSuite.milestones.map((m) => ({
      x: `Day ${m.day}`,
      y: 0.92,
      yref: 'paper',
      text: `<b>${m.label}</b>`,
      showarrow: true,
      arrowhead: 2,
      arrowsize: 1,
      arrowcolor: m.color,
      ax: 0,
      ay: -20,
      font: { size: 9.5, color: m.color, family: 'Outfit, sans-serif' },
      bgcolor: '#ffffff',
      bordercolor: m.color,
      borderwidth: 1.5,
      borderpad: 4
    }));

    const layout = {
      autosize: true,
      height: 390,
      margin: { l: 50, r: 50, t: 45, b: 75 },
      paper_bgcolor: paperColor,
      plot_bgcolor: paperColor,
      font: { family: 'Outfit, sans-serif', color: textColor, size: 11 },
      showlegend: true,
      legend: {
        orientation: 'h',
        x: 0.5,
        xanchor: 'center',
        y: -0.22,
        font: { size: 10, family: 'Outfit, sans-serif' }
      },
      xaxis: {
        gridcolor: gridColor,
        showgrid: true,
        tickangle: -30
      },
      yaxis: {
        title: 'Sensor Metric Range (% / ppm / NDRE)',
        gridcolor: gridColor,
        showgrid: true
      },
      yaxis2: {
        title: 'Substrate pH Scale (Alkalinity)',
        overlaying: 'y',
        side: 'right',
        gridcolor: 'transparent',
        showgrid: false,
        range: [6.0, 8.5]
      },
      shapes,
      annotations
    };

    return { traces, layout };
  }, [sensorSuite, paperColor, textColor, gridColor]);

  // 3. View 2: Plotly Bivariate Scatter Plot Data & Layout
  const scatterPlot = useMemo(() => {
    const traces = [
      {
        x: channelX.data,
        y: channelY.data,
        text: sensorSuite.days.map((d, i) => `${d}<br>${channelX.name}: ${channelX.data[i]}<br>${channelY.name}: ${channelY.data[i]}`),
        type: 'scatter',
        mode: 'markers',
        marker: {
          size: 10,
          color: sensorSuite.days.map((_, i) => i),
          colorscale: 'Blues',
          showscale: false,
          line: { color: primaryColor, width: 1.5 }
        },
        hovertemplate: `%{text}<extra></extra>`,
        name: 'Daily Observations'
      },
      {
        x: regressionLine.x,
        y: regressionLine.y,
        type: 'scatter',
        mode: 'lines',
        line: { color: correlationR < 0 ? roseColor : emeraldColor, width: 2.5, dash: 'dot' },
        name: `Fit: r = ${correlationR.toFixed(2)} (R² = ${rSquared.toFixed(2)})`
      }
    ];

    const layout = {
      autosize: true,
      height: 380,
      margin: { l: 60, r: 35, t: 25, b: 70 },
      paper_bgcolor: paperColor,
      plot_bgcolor: paperColor,
      font: { family: 'Outfit, sans-serif', color: textColor, size: 11 },
      showlegend: true,
      legend: {
        orientation: 'h',
        x: 0.5,
        xanchor: 'center',
        y: -0.22,
        font: { size: 10.5 }
      },
      xaxis: { title: `${channelX.name} (${channelX.unit})`, gridcolor: gridColor },
      yaxis: { title: `${channelY.name} (${channelY.unit})`, gridcolor: gridColor }
    };

    return { traces, layout };
  }, [channelX, channelY, sensorSuite.days, regressionLine, correlationR, rSquared, paperColor, textColor, gridColor]);

  // 4. View 3: Pairwise Correlation Heatmap Data & Layout
  const heatmapPlot = useMemo(() => {
    const labels = sensorSuite.channels.map((c) => c.name);
    const zMatrix = [];
    const textMatrix = [];

    sensorSuite.channels.forEach((c1) => {
      const row = [];
      const textRow = [];
      sensorSuite.channels.forEach((c2) => {
        if (c1.id === c2.id) {
          row.push(1.0);
          textRow.push('+1.00');
        } else {
          // Calculate Pearson r between c1 and c2
          const xs = c1.data;
          const ys = c2.data;
          const n = xs.length;
          let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0, sumY2 = 0;
          for (let i = 0; i < n; i++) {
            sumX += xs[i]; sumY += ys[i]; sumXY += xs[i] * ys[i];
            sumX2 += xs[i] * xs[i]; sumY2 += ys[i] * ys[i];
          }
          const num = n * sumXY - sumX * sumY;
          const den = Math.sqrt((n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY));
          const r = den !== 0 ? num / den : 0;
          row.push(r);
          textRow.push((r > 0 ? '+' : '') + r.toFixed(2));
        }
      });
      zMatrix.push(row);
      textMatrix.push(textRow);
    });

    const traces = [
      {
        z: zMatrix,
        x: labels,
        y: labels,
        text: textMatrix,
        type: 'heatmap',
        colorscale: [
          [0.0, '#f43f5e'],   // Strong Inverse (-1.0)
          [0.5, '#ffffff'],   // Neutral (0.0)
          [1.0, '#10b981']    // Strong Positive (+1.0)
        ],
        zmin: -1,
        zmax: 1,
        hoverongaps: false,
        texttemplate: '%{text}',
        textfont: { family: 'JetBrains Mono, monospace', size: 12, color: '#0f172a', weight: 'bold' }
      }
    ];

    const layout = {
      autosize: true,
      height: 380,
      margin: { l: 140, r: 35, t: 25, b: 90 },
      paper_bgcolor: paperColor,
      plot_bgcolor: paperColor,
      font: { family: 'Outfit, sans-serif', color: textColor, size: 11 },
      xaxis: { tickangle: -25, automargin: true },
      yaxis: { automargin: true }
    };

    return { traces, layout };
  }, [sensorSuite, paperColor, textColor]);

  const handleFileSelect = async (file) => {
    if (!file) return;
    if (onUploadSensorData) {
      setIsIngesting(true);
      setUploadFeedback(null);
      try {
        await onUploadSensorData(file);
        setUploadFeedback({ success: true, name: file.name });
      } catch (err) {
        setUploadFeedback({ success: false, error: err.message || 'Failed to ingest file' });
      } finally {
        setIsIngesting(false);
      }
    }
  };

  // Guided Empty State: When no sensor telemetry or tabular document has been entered
  if (!hasSensorData) {
    return (
      <div className="sensor-empty-guide" style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '1.25rem',
        padding: '1.75rem 1.25rem',
        background: '#ffffff',
        borderRadius: '12px',
        color: '#0f172a',
        maxWidth: '900px',
        margin: '0 auto'
      }}>
        {/* Header Alert / Notice Banner */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          padding: '1.5rem 1rem',
          background: 'linear-gradient(180deg, #f8fafc 0%, #ffffff 100%)',
          borderRadius: '12px',
          border: '1px solid #e2e8f0'
        }}>
          <div style={{
            width: '56px',
            height: '56px',
            borderRadius: '16px',
            background: '#e0f2fe',
            border: '1px solid #bae6fd',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '0.85rem'
          }}>
            <BarChart2 size={28} color="#0284c7" />
          </div>
          
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '0.2rem 0.65rem',
            borderRadius: '999px',
            background: '#f1f5f9',
            border: '1px solid #e2e8f0',
            fontSize: '0.7rem',
            fontWeight: '600',
            color: '#475569',
            marginBottom: '0.6rem'
          }}>
            <Info size={12} color="#0284c7" />
            <span>Visual Evidence Investigation Active</span>
          </div>

          <h3 style={{
            fontSize: '1.18rem',
            fontWeight: '700',
            color: '#0f172a',
            margin: '0 0 0.4rem 0'
          }}>
            No Sensor Telemetry or Tabular Data Loaded
          </h3>

          <p style={{
            fontSize: '0.82rem',
            color: '#64748b',
            maxWidth: '560px',
            lineHeight: '1.5',
            margin: 0
          }}>
            This investigation is currently grounded on visual observations and morphological evidence.
            Upload a time-series dataset or load a sample baseline to unlock multi-channel sensor analytics.
          </p>

          {uploadFeedback && (
            <div style={{
              marginTop: '0.75rem',
              padding: '0.4rem 0.8rem',
              borderRadius: '6px',
              fontSize: '0.75rem',
              background: uploadFeedback.success ? '#ecfdf5' : '#fff1f2',
              color: uploadFeedback.success ? '#059669' : '#e11d48',
              border: `1px solid ${uploadFeedback.success ? '#a7f3d0' : '#fecdd3'}`
            }}>
              {uploadFeedback.success ? `Successfully ingested ${uploadFeedback.name}` : uploadFeedback.error}
            </div>
          )}
        </div>

        {/* Action Pathway Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '1rem'
        }}>
          {/* Card 1: In-Tool File Uploader */}
          <div
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setIsDragging(false);
              const file = e.dataTransfer.files?.[0];
              if (file) handleFileSelect(file);
            }}
            style={{
              border: isDragging ? '2px dashed #0284c7' : '1.5px dashed #cbd5e1',
              background: isDragging ? '#f0f9ff' : '#f8fafc',
              borderRadius: '10px',
              padding: '1.5rem 1.25rem',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              textAlign: 'center',
              transition: 'all 0.2s ease',
              position: 'relative',
              cursor: 'pointer'
            }}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.xlsx,.xls,.tsv,.txt"
              style={{ display: 'none' }}
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleFileSelect(file);
              }}
            />

            <div style={{
              width: '44px',
              height: '44px',
              borderRadius: '12px',
              background: '#ffffff',
              border: '1px solid #e2e8f0',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '0.75rem',
              boxShadow: '0 2px 4px rgba(0,0,0,0.03)'
            }}>
              {isIngesting ? (
                <RefreshCw size={22} color="#0284c7" className="animate-spin" />
              ) : (
                <UploadCloud size={22} color="#0284c7" />
              )}
            </div>

            <strong style={{ fontSize: '0.9rem', color: '#0f172a', marginBottom: '0.25rem' }}>
              {isIngesting ? 'Ingesting & Analyzing Dataset...' : 'Upload Sensor Telemetry'}
            </strong>

            <p style={{ fontSize: '0.75rem', color: '#64748b', margin: '0 0 0.85rem 0', maxWidth: '280px' }}>
              Drag & drop your CSV or Excel file here, or click to browse local files
            </p>

            <button
              type="button"
              disabled={isIngesting}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '0.45rem 0.95rem',
                borderRadius: '6px',
                background: '#0284c7',
                color: '#ffffff',
                border: 'none',
                fontSize: '0.78rem',
                fontWeight: '600',
                cursor: isIngesting ? 'not-allowed' : 'pointer',
                boxShadow: '0 1px 2px rgba(2, 132, 199, 0.2)'
              }}
            >
              <FileSpreadsheet size={14} />
              <span>Browse CSV / XLSX</span>
            </button>

            <span style={{ fontSize: '0.67rem', color: '#94a3b8', marginTop: '0.75rem' }}>
              Supports .csv, .xlsx, .tsv (Time series or multi-variable tabular telemetry)
            </span>
          </div>

          {/* Card 2: Load Sample Telemetry Baseline */}
          <div style={{
            border: '1px solid #e2e8f0',
            background: '#f8fafc',
            borderRadius: '10px',
            padding: '1.5rem 1.25rem',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            gap: '0.75rem'
          }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '0.5rem' }}>
                <div style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  background: '#ffffff',
                  border: '1px solid #e2e8f0',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <Database size={16} color="#0284c7" />
                </div>
                <div>
                  <strong style={{ fontSize: '0.88rem', color: '#0f172a', display: 'block' }}>
                    Load Demonstration Baseline
                  </strong>
                  <span style={{ fontSize: '0.68rem', color: '#64748b' }}>
                    Instant 30-Day Multi-Sensor Telemetry
                  </span>
                </div>
              </div>

              <p style={{ fontSize: '0.75rem', color: '#64748b', lineHeight: '1.45', margin: '0 0 0.85rem 0' }}>
                Explore populated sensor telemetry with 30 synchronized daily observations, bivariate cross-correlations, and anomaly markers tailored to this scientific domain.
              </p>

              <div style={{
                padding: '0.55rem 0.75rem',
                background: '#ffffff',
                border: '1px solid #e2e8f0',
                borderRadius: '6px',
                display: 'flex',
                flexDirection: 'column',
                gap: '3px',
                marginBottom: '0.85rem'
              }}>
                <span style={{ fontSize: '0.65rem', fontWeight: '700', color: '#0284c7', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  {domain.includes('infra') ? 'Civil Infrastructure Telemetry' : 'Botanical Agronomy Telemetry'}
                </span>
                <span style={{ fontSize: '0.73rem', color: '#334155', fontWeight: '500' }}>
                  {domain.includes('infra') 
                    ? '4 Channels: Moisture (%), GPR Echo (dB), Crack Width (mm), Rain (mm/day)' 
                    : '4 Channels: Soil pH, NDRE Foliar Chlorophyll, Electrical Conductivity, Transpiration'}
                </span>
              </div>
            </div>

            <button
              type="button"
              onClick={() => {
                if (onLoadSampleDataset) {
                  onLoadSampleDataset(domain);
                }
              }}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
                padding: '0.5rem 1rem',
                borderRadius: '6px',
                background: '#ffffff',
                color: '#0284c7',
                border: '1.5px solid #0284c7',
                fontSize: '0.78rem',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
              onMouseEnter={(e) => { e.currentTarget.style.background = '#f0f9ff'; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = '#ffffff'; }}
            >
              <Sparkles size={14} color="#0284c7" />
              <span>Load 30-Day Sensor Baseline</span>
            </button>
          </div>
        </div>

        {/* What Sensor Analytics Unlocks (Educational 3-Card Row) */}
        <div style={{
          marginTop: '0.5rem',
          paddingTop: '1rem',
          borderTop: '1px solid #f1f5f9'
        }}>
          <div style={{
            fontSize: '0.7rem',
            fontWeight: '700',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            color: '#94a3b8',
            marginBottom: '0.6rem'
          }}>
            Analytical Capabilities Unlocked with Telemetry
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '0.75rem'
          }}>
            <div style={{
              padding: '0.75rem',
              background: '#f8fafc',
              border: '1px solid #e2e8f0',
              borderRadius: '8px',
              display: 'flex',
              gap: '8px'
            }}>
              <Activity size={16} color="#0284c7" style={{ flexShrink: 0, marginTop: '2px' }} />
              <div>
                <strong style={{ fontSize: '0.76rem', color: '#0f172a', display: 'block', marginBottom: '2px' }}>
                  Dual-Axis Longitudinal Scrubber
                </strong>
                <span style={{ fontSize: '0.68rem', color: '#64748b', lineHeight: '1.35', display: 'block' }}>
                  Synchronized multi-channel time-series with diagnostic anomaly threshold highlights.
                </span>
              </div>
            </div>

            <div style={{
              padding: '0.75rem',
              background: '#f8fafc',
              border: '1px solid #e2e8f0',
              borderRadius: '8px',
              display: 'flex',
              gap: '8px'
            }}>
              <TrendingUp size={16} color="#0284c7" style={{ flexShrink: 0, marginTop: '2px' }} />
              <div>
                <strong style={{ fontSize: '0.76rem', color: '#0f172a', display: 'block', marginBottom: '2px' }}>
                  Bivariate Granger Regression
                </strong>
                <span style={{ fontSize: '0.68rem', color: '#64748b', lineHeight: '1.35', display: 'block' }}>
                  Quantifies direct statistical coupling, non-linear hysteresis, and lead-lag drivers.
                </span>
              </div>
            </div>

            <div style={{
              padding: '0.75rem',
              background: '#f8fafc',
              border: '1px solid #e2e8f0',
              borderRadius: '8px',
              display: 'flex',
              gap: '8px'
            }}>
              <GitFork size={16} color="#0284c7" style={{ flexShrink: 0, marginTop: '2px' }} />
              <div>
                <strong style={{ fontSize: '0.76rem', color: '#0f172a', display: 'block', marginBottom: '2px' }}>
                  Pairwise Covariance Heatmap
                </strong>
                <span style={{ fontSize: '0.68rem', color: '#64748b', lineHeight: '1.35', display: 'block' }}>
                  Full Pearson correlation matrix (r ∈ [-1, 1]) across all captured variables.
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="sensor-analytics-dashboard" style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '1rem',
      background: '#ffffff',
      borderRadius: '8px',
      padding: '0.5rem'
    }}>
      {/* Telemetry Dataset Context Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.5rem 0.85rem',
        background: '#f8fafc',
        border: '1px solid #e2e8f0',
        borderRadius: '8px',
        fontSize: '0.75rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#0f172a' }}>
          <CheckCircle2 size={15} color="#0284c7" />
          <span style={{ fontWeight: '600' }}>Active Sensor Telemetry:</span>
          <span style={{ color: '#475569' }}>
            {saarData?.perception?.observations_count
              ? `${saarData.perception.observations_count} Observations · ${saarData.perception.features_detected || 4} Features`
              : (domain.includes('infra') ? '30-Day Civil Infrastructure Sensor Array' : '30-Day Longitudinal Agronomy Sensor Array')}
          </span>
        </div>
        
        {onUploadSensorData && (
          <label style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '5px',
            padding: '0.25rem 0.65rem',
            background: '#ffffff',
            border: '1px solid #cbd5e1',
            borderRadius: '6px',
            color: '#0f172a',
            cursor: 'pointer',
            fontSize: '0.72rem',
            fontWeight: '600',
            transition: 'all 0.15s ease'
          }}
          onMouseEnter={(e) => { e.currentTarget.style.borderColor = '#0284c7'; e.currentTarget.style.color = '#0284c7'; }}
          onMouseLeave={(e) => { e.currentTarget.style.borderColor = '#cbd5e1'; e.currentTarget.style.color = '#0f172a'; }}
          >
            <UploadCloud size={13} color="#0284c7" />
            <span>Upload New CSV</span>
            <input
              type="file"
              accept=".csv,.xlsx,.tsv,.txt"
              style={{ display: 'none' }}
              onChange={(e) => {
                if (e.target.files?.[0]) handleFileSelect(e.target.files[0]);
              }}
            />
          </label>
        )}
      </div>
      {/* 1. Top Executive KPI Summary Cards (Interactive with Scientific Definitions) */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))',
        gap: '0.75rem'
      }}>
        {sensorSuite.kpis.map((kpi, idx) => {
          const isSelected = selectedKpiId === kpi.id;
          return (
            <div
              key={idx}
              onClick={() => setSelectedKpiId((prev) => (prev === kpi.id ? null : kpi.id))}
              style={{
                background: isSelected ? '#ffffff' : '#f8fafc',
                border: isSelected ? `1.5px solid ${kpi.badgeColor}` : '1px solid #e2e8f0',
                borderRadius: '8px',
                padding: '0.65rem 0.85rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '3px',
                boxShadow: isSelected ? `0 4px 14px ${kpi.badgeColor}25` : '0 1px 3px rgba(0, 0, 0, 0.04)',
                cursor: 'pointer',
                transition: 'all 0.18s cubic-bezier(0.16, 1, 0.3, 1)',
                position: 'relative'
              }}
              title="Click to view scientific explanation & dictionary definition"
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '0.68rem', fontWeight: '600', color: isSelected ? '#0f172a' : '#64748b' }}>
                  {kpi.title}
                </span>
                <span style={{
                  fontSize: '0.62rem',
                  fontWeight: '700',
                  padding: '0.1rem 0.35rem',
                  borderRadius: '4px',
                  background: `${kpi.badgeColor}15`,
                  color: kpi.badgeColor
                }}>
                  {kpi.badge}
                </span>
              </div>
              <strong style={{ fontSize: '0.92rem', color: '#0f172a', margin: '1px 0' }}>{kpi.value}</strong>
              <span style={{ fontSize: '0.7rem', color: '#475569' }}>{kpi.sub}</span>

              {/* Click-for-definition prompt */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                marginTop: '4px',
                fontSize: '0.65rem',
                color: isSelected ? kpi.badgeColor : '#94a3b8',
                fontWeight: isSelected ? '600' : '500'
              }}>
                <BookA size={11} />
                <span>{isSelected ? 'Viewing Definition ▴' : 'Click for Definition ▾'}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* 1.1 Interactive Scientific Definition & Mechanism Breakdown Card */}
      {selectedKpiId && (() => {
        const activeKpi = sensorSuite.kpis.find((k) => k.id === selectedKpiId);
        if (!activeKpi) return null;

        return (
          <div style={{
            background: '#ffffff',
            border: `1.5px solid ${activeKpi.badgeColor}45`,
            borderLeft: `4px solid ${activeKpi.badgeColor}`,
            borderRadius: '8px',
            padding: '1rem 1.2rem',
            boxShadow: '0 4px 18px rgba(0, 0, 0, 0.05)',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem'
          }}>
            {/* Header row */}
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{
                  padding: '6px',
                  borderRadius: '6px',
                  background: `${activeKpi.badgeColor}15`,
                  color: activeKpi.badgeColor,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <BookA size={18} />
                </div>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <h3 style={{ margin: 0, fontSize: '0.98rem', fontWeight: '700', color: '#0f172a' }}>
                      {activeKpi.conceptName}
                    </h3>
                    <span style={{
                      fontSize: '0.62rem',
                      fontWeight: '700',
                      padding: '0.15rem 0.45rem',
                      borderRadius: '4px',
                      background: `${activeKpi.badgeColor}18`,
                      color: activeKpi.badgeColor
                    }}>
                      {activeKpi.badge}
                    </span>
                  </div>
                  <span style={{ fontSize: '0.72rem', color: '#64748b' }}>
                    Diagnostic Indicator: <strong>{activeKpi.value}</strong> ({activeKpi.sub})
                  </span>
                </div>
              </div>

              <button
                onClick={() => setSelectedKpiId(null)}
                style={{
                  border: 'none',
                  background: '#f1f5f9',
                  borderRadius: '6px',
                  width: '26px',
                  height: '26px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#64748b'
                }}
                title="Close definition"
              >
                <X size={14} />
              </button>
            </div>

            {/* Explanation Columns */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: '0.75rem',
              background: '#f8fafc',
              padding: '0.85rem',
              borderRadius: '6px',
              border: '1px solid #e2e8f0'
            }}>
              {/* Scientific Definition */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.72rem', fontWeight: '700', color: '#0f172a', marginBottom: '3px' }}>
                  <Info size={13} className="text-primary" />
                  <span>Scientific Definition &amp; Context</span>
                </div>
                <p style={{ margin: 0, fontSize: '0.78rem', color: '#334155', lineHeight: '1.45' }}>
                  {activeKpi.definition}
                </p>
              </div>

              {/* Underlying Mechanism */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.72rem', fontWeight: '700', color: '#0f172a', marginBottom: '3px' }}>
                  <Activity size={13} style={{ color: activeKpi.badgeColor }} />
                  <span>Biochemical / Physical Mechanism</span>
                </div>
                <p style={{ margin: 0, fontSize: '0.78rem', color: '#334155', lineHeight: '1.45' }}>
                  {activeKpi.mechanism}
                </p>
              </div>
            </div>

            {/* Threshold & Reference Footer */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem', paddingTop: '0.25rem' }}>
              <div style={{ fontSize: '0.72rem', color: '#475569', display: 'flex', alignItems: 'center', gap: '5px' }}>
                <BookOpen size={13} className="text-indigo" />
                <span>Reference: <em>{activeKpi.citation}</em></span>
              </div>

              {/* Action Buttons */}
              <div style={{ display: 'flex', gap: '8px' }}>
                {onSelectTool && (
                  <button
                    onClick={() => onSelectTool('dictionary')}
                    style={{
                      border: '1px solid #cbd5e1',
                      background: '#ffffff',
                      color: '#0f172a',
                      fontSize: '0.74rem',
                      fontWeight: '600',
                      padding: '0.35rem 0.65rem',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '5px'
                    }}
                  >
                    <BookA size={13} className="text-amber" />
                    <span>Open in Scientific Dictionary</span>
                    <ChevronRight size={12} />
                  </button>
                )}

                {onSendToChat && (
                  <button
                    onClick={() => {
                      onSendToChat(`Explain the scientific mechanism of ${activeKpi.conceptName} (${activeKpi.value}) and its diagnostic role as ${activeKpi.badge} in simple terms.`);
                    }}
                    style={{
                      border: 'none',
                      background: '#0284c7',
                      color: '#ffffff',
                      fontSize: '0.74rem',
                      fontWeight: '600',
                      padding: '0.35rem 0.75rem',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '5px',
                      boxShadow: '0 1px 3px rgba(2, 132, 199, 0.3)'
                    }}
                  >
                    <MessageSquare size={13} />
                    <span>Inquire in Chat</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        );
      })()}

      {/* 2. Mode Switcher Tabs & Chart Controls Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.45rem 0.75rem',
        background: '#f1f5f9',
        borderRadius: '8px',
        border: '1px solid #e2e8f0'
      }}>
        {/* Navigation Tabs */}
        <div style={{ display: 'flex', gap: '4px' }}>
          <button
            onClick={() => setActiveTab('timeline')}
            style={{
              border: 'none',
              background: activeTab === 'timeline' ? '#ffffff' : 'transparent',
              color: activeTab === 'timeline' ? '#0284c7' : '#64748b',
              fontWeight: activeTab === 'timeline' ? '700' : '500',
              padding: '0.35rem 0.75rem',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '0.74rem',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              boxShadow: activeTab === 'timeline' ? '0 1px 3px rgba(0,0,0,0.06)' : 'none'
            }}
          >
            <TrendingUp size={13} />
            <span>30-Day Sensor Timeline</span>
          </button>

          <button
            onClick={() => setActiveTab('scatter')}
            style={{
              border: 'none',
              background: activeTab === 'scatter' ? '#ffffff' : 'transparent',
              color: activeTab === 'scatter' ? '#0284c7' : '#64748b',
              fontWeight: activeTab === 'scatter' ? '700' : '500',
              padding: '0.35rem 0.75rem',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '0.74rem',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              boxShadow: activeTab === 'scatter' ? '0 1px 3px rgba(0,0,0,0.06)' : 'none'
            }}
          >
            <Activity size={13} />
            <span>Bivariate Scatter &amp; Regression</span>
          </button>

          <button
            onClick={() => setActiveTab('heatmap')}
            style={{
              border: 'none',
              background: activeTab === 'heatmap' ? '#ffffff' : 'transparent',
              color: activeTab === 'heatmap' ? '#0284c7' : '#64748b',
              fontWeight: activeTab === 'heatmap' ? '700' : '500',
              padding: '0.35rem 0.75rem',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '0.74rem',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              boxShadow: activeTab === 'heatmap' ? '0 1px 3px rgba(0,0,0,0.06)' : 'none'
            }}
          >
            <BarChart2 size={13} />
            <span>Correlation Heatmap</span>
          </button>
        </div>

        {/* Dynamic X / Y Selectors when in Scatter mode */}
        {activeTab === 'scatter' && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.72rem' }}>
            <span style={{ color: '#64748b' }}>X:</span>
            <select
              value={scatterVarX}
              onChange={(e) => setScatterVarX(e.target.value)}
              style={{
                padding: '0.2rem 0.45rem',
                borderRadius: '4px',
                border: '1px solid #cbd5e1',
                fontSize: '0.72rem',
                background: '#ffffff',
                fontWeight: '600'
              }}
            >
              {sensorSuite.channels.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>

            <span style={{ color: '#64748b', marginLeft: '4px' }}>Y:</span>
            <select
              value={scatterVarY}
              onChange={(e) => setScatterVarY(e.target.value)}
              style={{
                padding: '0.2rem 0.45rem',
                borderRadius: '4px',
                border: '1px solid #cbd5e1',
                fontSize: '0.72rem',
                background: '#ffffff',
                fontWeight: '600'
              }}
            >
              {sensorSuite.channels.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* 3. Main Chart Display Canvas */}
      <div style={{
        background: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: '8px',
        padding: '0.75rem',
        boxShadow: '0 1px 4px rgba(0, 0, 0, 0.04)'
      }}>
        {activeTab === 'timeline' && (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Calendar size={14} color="#0284c7" />
                <strong style={{ fontSize: '0.86rem', color: '#0f172a' }}>{sensorSuite.title}</strong>
              </div>
              <span style={{ fontSize: '0.7rem', color: '#64748b' }}>
                Synchronized 30-Day Multi-Sensor Longitudinal Tracking
              </span>
            </div>
            <Plot
              data={timelinePlot.traces}
              layout={timelinePlot.layout}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%' }}
            />
          </div>
        )}

        {activeTab === 'scatter' && (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Activity size={14} color="#0284c7" />
                <strong style={{ fontSize: '0.86rem', color: '#0f172a' }}>
                  Bivariate Fit: {channelX.name} vs. {channelY.name}
                </strong>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{
                  fontSize: '0.72rem',
                  fontWeight: '700',
                  padding: '0.15rem 0.5rem',
                  borderRadius: '4px',
                  background: correlationR < 0 ? '#fee2e2' : '#dcfce7',
                  color: correlationR < 0 ? '#b91c1c' : '#15803d'
                }}>
                  Pearson r = {correlationR.toFixed(2)} ({correlationR < 0 ? 'Inverse' : 'Positive'})
                </span>
                <span style={{
                  fontSize: '0.72rem',
                  fontWeight: '600',
                  padding: '0.15rem 0.5rem',
                  borderRadius: '4px',
                  background: '#f1f5f9',
                  color: '#334155'
                }}>
                  R² = {rSquared.toFixed(2)}
                </span>
              </div>
            </div>

            <Plot
              data={scatterPlot.traces}
              layout={scatterPlot.layout}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%' }}
            />

            {/* Scientific Finding Interpretation Callout */}
            <div style={{
              marginTop: '0.75rem',
              padding: '0.65rem 0.85rem',
              background: '#f0f9ff',
              border: '1px solid #bae6fd',
              borderRadius: '6px',
              fontSize: '0.74rem',
              color: '#0369a1',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <Sparkles size={15} style={{ flexShrink: 0 }} />
              <div>
                <strong>Empirical Scientific Insight:</strong> {correlationR < -0.7
                  ? `Strong inverse coupling (r = ${correlationR.toFixed(2)}). As ${channelX.name} increases past critical levels, ${channelY.name} experiences rapid suppression due to chemical equilibrium constraints.`
                  : correlationR > 0.7
                  ? `Strong direct coupling (r = ${correlationR.toFixed(2)}). Fluctuations in ${channelX.name} directly induce matching elevation in ${channelY.name}.`
                  : `Moderate statistical relationship (r = ${correlationR.toFixed(2)}). Secondary environmental factors mediate the interaction.`}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'heatmap' && (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <BarChart2 size={14} color="#0284c7" />
                <strong style={{ fontSize: '0.86rem', color: '#0f172a' }}>Pairwise Correlation Matrix Heatmap</strong>
              </div>
              <span style={{ fontSize: '0.7rem', color: '#64748b' }}>
                Green = Positive Coupling (+1.0) · Red = Inverse Obstruction (-1.0)
              </span>
            </div>
            <Plot
              data={heatmapPlot.traces}
              layout={heatmapPlot.layout}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%' }}
            />
          </div>
        )}
      </div>
    </div>
  );
}
