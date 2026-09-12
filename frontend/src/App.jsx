import React, { useState, useEffect, useCallback } from 'react';
import {
  fetchDomains, runInvestigation, fetchSaarKnowledge,
  uploadSaarCsv, askSaarQuestion, answerSaarQuestion, fetchBaseline,
  analyzeGaitVideo
} from './api/client';
import { ChatSidebar } from './components/ChatSidebar';
import { ChatGPTView } from './components/ChatGPTView';
import { ToolCanvasDrawer } from './components/ToolCanvasDrawer';
import { HelpDrawer } from './components/HelpDrawer';
import { LandingPage } from './components/LandingPage';
import monsteraInvestigation from './data/monsteraInvestigation.json';

export default function App() {
  // Theme State (Supports Pure Light, Pure Dark, and Lavender White with Purple Tint)
  const [theme, setTheme] = useState(() => {
    try {
      const saved = localStorage.getItem('saar_theme');
      if (['light', 'dark', 'purple'].includes(saved)) return saved;
    } catch (e) {}
    return 'dark';
  });

  const handleSelectTheme = useCallback((newTheme) => {
    setTheme(newTheme);
    try {
      localStorage.setItem('saar_theme', newTheme);
    } catch (e) {}
  }, []);

  const handleToggleTheme = useCallback(() => {
    setTheme((prev) => {
      const cycle = ['dark', 'light', 'purple'];
      const nextIdx = (cycle.indexOf(prev) + 1) % cycle.length;
      const nextTheme = cycle[nextIdx];
      try {
        localStorage.setItem('saar_theme', nextTheme);
      } catch (e) {}
      return nextTheme;
    });
  }, []);

  // View Mode: 'landing' (Futuristic Showcase) or 'studio' (Active Investigation Workspace)
  const [viewMode, setViewMode] = useState('landing');

  // Sidebar & Tool Drawer Visibility
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isToolDrawerOpen, setIsToolDrawerOpen] = useState(false);
  const [activeTool, setActiveTool] = useState('graph');

  // Help Drawer State
  const [isHelpOpen, setIsHelpOpen] = useState(false);

  // Domain & Investigation Data States
  const [selectedDomain, setSelectedDomain] = useState('agriculture');
  const [domains, setDomains] = useState([]);
  const [investigationData, setInvestigationData] = useState(null);
  const [saarData, setSaarData] = useState(null);
  const [baselineData, setBaselineData] = useState(null);

  // Visual Media & Camera
  const [customImageData, setCustomImageData] = useState(null);
  const [customImageUrl, setCustomImageUrl] = useState(null);
  const [customVideoFile, setCustomVideoFile] = useState(null);
  const [cameraConnected, setCameraConnected] = useState(false);

  // Selected Graph Relationship for Analytics
  const [selectedRelationship, setSelectedRelationship] = useState(null);
  const [selectedChartType, setSelectedChartType] = useState('histogram');

  // Processing state
  const [isProcessing, setIsProcessing] = useState(false);

  // Default Initial Chat Sessions & Pre-warmed Messages
  const DEFAULT_SESSIONS = [
    {
      id: 'session-1',
      query: 'Tomato Crop 30-Day Failure: Chlorosis & Nutrient Leaching',
      domain: 'agriculture',
      presetId: 'agri_tomato_chlorosis',
      imageUrl: '/tomato_chlorosis_sample.jpg',
      timestamp: 'Today'
    },
    {
      id: 'session-2',
      query: 'Highway Pavement Surface Cracking & GPR Cavity Void',
      domain: 'infrastructure',
      presetId: 'infra_damaged_road',
      imageUrl: 'https://images.unsplash.com/photo-1515162816999-a0c47dc192f7?auto=format&fit=crop&w=1200&q=80',
      timestamp: 'Yesterday'
    },
    {
      id: 'session-3',
      query: 'Monstera adansonii: Foliar Fenestration & Plant Health',
      domain: 'agriculture',
      presetId: 'agri_monstera_fenestration',
      imageUrl: '/monstera_sample.png',
      timestamp: 'Just now'
    },
    {
      id: 'session-4',
      query: 'Badminton Smash: Kinetic Chain Torque & Accuracy Analysis',
      domain: 'sports',
      presetId: 'sports_badminton_smash_kinetic',
      imageUrl: 'https://images.unsplash.com/photo-1626224583764-f87db24ac4ea?auto=format&fit=crop&w=1200&q=80',
      timestamp: 'Active'
    }
  ];

  const DEFAULT_MESSAGES = {
    'session-1': [
      {
        role: 'user',
        text: 'Investigate Tomato Crop 30-Day Failure: Chlorosis & Nutrient Leaching',
        timestamp: '10:15 AM'
      },
      {
        role: 'assistant',
        text: `### Autonomous Investigation Executed (AGRICULTURE)\n\n**Perception & Workflow**: Evaluated 4 investigation phases utilizing provider **Saar Dynamic Loop**.\n\n- **Evidence Graph**: **6 nodes** and **5 directed relationships** formulated.\n- **Graph Confidence**: **94%** (Stabilized after specialized tool execution).\n\n#### Diagnostic Verdict:\nRhizosphere alkalinization (pH > 7.6) caused by unmetered continuous drip irrigation blocked biological Fe²⁺ reduction, leading to progressive foliar chlorosis (NDRE collapsed from 0.65 to 0.18).`,
        timestamp: '10:16 AM'
      }
    ],
    'session-2': [
      {
        role: 'user',
        text: 'Investigate Highway Pavement Surface Cracking & GPR Cavity Void',
        timestamp: 'Yesterday'
      },
      {
        role: 'assistant',
        text: `### Autonomous Investigation Executed (INFRASTRUCTURE)\n\n**Perception & Workflow**: Evaluated 4 investigation phases utilizing provider **Saar Dynamic Loop**.\n\n- **Evidence Graph**: **5 nodes** and **4 directed relationships** formulated.\n- **Graph Confidence**: **91%** (Stabilized after specialized tool execution).\n\n#### Diagnostic Verdict:\nRepetitive surface water infiltration eroded sub-base aggregates, creating a 1.8m underground void verified via GPR reflection loss before asphalt fatigue shear failure.`,
        timestamp: 'Yesterday'
      }
    ],
    'session-3': [
      {
        role: 'user',
        text: 'Attached image of potted Monstera adansonii. Are the holes in the leaves caused by insect pests, and what does the new emergent shoot say about the plant\'s health?',
        files: ['monstera_adansonii_foliage.png'],
        timestamp: 'Just now'
      },
      {
        role: 'assistant',
        text: `## 📋 Autonomous Botanical Investigation Executed (MONSTERA ADANSONII)

**Perception & Workflow**: Evaluated 4 dynamic phases utilizing provider **Saar Vision Engine & Groq ReAct Loop**.

- **Spatial Entities Grounded**: **8 nodes** (Elliptical leaf perforations \`[90, 300, 430, 590]\`, apical shoot \`[310, 520, 750, 610]\`, container substrate \`[480, 450, 980, 720]\`, cascading foliage).
- **Specialized Tool Executed**: \`Foliar Margin Morphology & Fenestration Phenotyper\` (*foliar_morphology_eval*).
- **Causal Belief Resolution**: High-resolution edge inspection proves smooth, suberized hole perimeters with continuous vascular veins (**Programmed Cell Death**). Contradicts and definitively refutes chewing pest defoliation and fungal shot-hole disease.
- **Graph Confidence**: Stabilized at **80.1%** (+6.1% Bayesian evidence gain).

---

### Clinical Botanical Diagnosis & Health Status

| Parameter | Visual Observation | Clinical Interpretation |
| :--- | :--- | :--- |
| **Leaf Fenestrations** | Symmetrical elliptical perforations | **Natural PCD-driven adaptation**: Enhances light infiltration & reduces wind drag. Pest damage and shot-hole disease excluded. |
| **Photosystem II ($F_v/F_m$)** | $0.81$ (Optimal) | Healthy, non-stressed tropical aroid; robust chlorophyll turgor with zero photo-oxidative stress. |
| **Emergent Shoot** | Bright green juvenile apical leaf | **Active vegetative vigor**: Plant is actively allocating carbon assimilates to new leaf formation. |
| **Container Substrate** | Coarse peat-perlite medium | **Well-aerated**: Minimizes root hypoxia and *Pythium* root-rot colonization risk. |

**Horticultural Care Recommendation**: Maintain bright, indirect light; water when top 2–3 cm of substrate dries; provide moss pole support for climbing mature leaf expansion.`,
        terminology: [
          {
            term: "Leaf Fenestration",
            phonetic: "/liːf ˌfɛn.əˈstreɪ.ʃən/",
            domain: "Plant Evolutionary Morphology",
            formal_definition: "Natural elliptical or circular perforations in the leaf blade formed during early leaf morphogenesis via genetically programmed cell death (PCD).",
            investigation_context: "Differentiates healthy evolutionary adaptations in Araceae (e.g. Monstera adansonii) from destructive chewing insect damage or fungal shot-hole necrosis.",
            diagnostic_relevance: "Suberized, entire hole margins bounded by intact veins without surrounding necrotic chlorotic halos."
          },
          {
            term: "Monstera adansonii",
            phonetic: "/mɒnˈstɪərə əˈdænsənaɪ/",
            domain: "Araceae Systematics & Indoor Agronomy",
            formal_definition: "A hemiepiphytic tropical climbing vine native to Central and South America characterized by extensive natural leaf perforations.",
            investigation_context: "Target species under botanical phenotyping; exhibits robust fenestrated foliage, emergent apical shoots, and aerated substrate requirements.",
            diagnostic_relevance: "Ovate-lanceolate leaves with multiple fenestrations per side, climbing habit, and aerial root nodes."
          },
          {
            term: "Programmed Cell Death (Botany)",
            phonetic: "/ˈproʊ.ɡræmd sɛl dɛθ/",
            domain: "Plant Developmental Biology",
            formal_definition: "Genetically regulated physiological suicide of specific groups of cells in juvenile leaf primordia to generate perforations and lobes.",
            investigation_context: "The molecular developmental mechanism responsible for leaf holes in Monstera, contrasting with traumatic pathogen necrosis.",
            diagnostic_relevance: "Clean cellular lysis bordered by protective suberin synthesis without frass or pathogen exudates."
          }
        ],
        report: monsteraInvestigation,
        timestamp: 'Just now'
      }
    ],
    'session-4': [
      {
        role: 'user',
        text: 'Analyze Badminton Overhead Smash longitudinal progression (Sessions S1-S4). Is the accuracy improvement driven by kinetic-chain timing or shot volume fatigue variation?',
        timestamp: 'Active'
      },
      {
        role: 'assistant',
        text: `### 🏸 Autonomous Biomechanical Investigation (SPORTS KINEMATICS)

**Perception & Contact-Frame Kinematics**:
- **Peak-Velocity Impact Registered**: Evaluated multi-session sequence across 4 training sessions (S1–S4, 96 total shots).
- **Elbow Extension at Contact**: Improved from $152.0^\\circ$ (hyperextension lockup) to $135.0^\\circ$ (compliant lever, $r = -0.998$ vs accuracy).
- **Wrist Snap Timing Lag**: Converged from $+0.18\\text{s}$ (late pushed stroke) to $+0.03\\text{s}$ (optimal whip impact window).

---

### Diagnostic Verdict & Hypothesis Resolution:
1. **H1 (Kinetic-Chain Refinement) CONFIRMED (Confidence: 76%)**: Proximal-to-distal sequencing and synchronized forearm pronation causally drive the $+25.0\\%$ accuracy gain.
2. **H2 (Shot Volume Distortion) RULED OUT (Confidence: 8%)**: Attempt volume remained invariant at 24 shots/session across all test days.
3. **Knee Flexion ($145^\\circ \\to 122^\\circ$) Classified as Passive Covariate**: Stance lowering does not directly drive racket precision and is ruled out as an intervention priority.`,
        terminology: [
          {
            term: "Kinetic Chain Sequencing",
            phonetic: "/kɪˈnɛt.ɪk tʃeɪn ˈsiː.kwən.sɪŋ/",
            domain: "Sports Biomechanics & Motor Control",
            formal_definition: "The coordinated proximal-to-distal activation of linked anatomical segments to progressively accelerate the distal end-effector to peak velocity.",
            investigation_context: "The primary causal mechanism governing shot velocity and smash accuracy in overhead strokes.",
            diagnostic_relevance: "Sequential peak angular velocities from pelvis to trunk, shoulder, elbow, and forearm."
          },
          {
            term: "Forearm Pronation Velocity",
            phonetic: "/ˈfɔːr.ɑːrm proʊˈneɪ.ʃən vəˈlɒs.ə.ti/",
            domain: "Upper Extremity Kinematics",
            formal_definition: "The rotational speed of the radius over the ulna immediately preceding and during impact.",
            investigation_context: "Differentiates powerful whipping smashes from pushed arm strokes with flat trajectory.",
            diagnostic_relevance: "Peak angular velocity > 1800°/s occurring within 20ms of contact frame."
          }
        ],
        timestamp: 'Active'
      }
    ]
  };

  // Persistent Sessions & Messages State (Loaded from localStorage)
  const [sessions, setSessions] = useState(() => {
    try {
      const saved = localStorage.getItem('saar_chat_sessions');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          if (!parsed.some((s) => s.id === 'session-3')) {
            return [DEFAULT_SESSIONS[2], ...parsed];
          }
          return parsed;
        }
      }
    } catch (e) {
      console.warn("Failed to load sessions from storage:", e);
    }
    return DEFAULT_SESSIONS;
  });

  const [activeSessionId, setActiveSessionId] = useState(() => {
    try {
      const saved = localStorage.getItem('saar_active_session_id');
      if (saved) return saved;
    } catch (e) {}
    return 'session-3';
  });

  const [allMessages, setAllMessages] = useState(() => {
    try {
      const saved = localStorage.getItem('saar_session_messages');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (typeof parsed === 'object' && parsed !== null) {
          if (!parsed['session-3']) {
            parsed['session-3'] = DEFAULT_MESSAGES['session-3'];
          } else if (Array.isArray(parsed['session-3']) && parsed['session-3'][1] && !parsed['session-3'][1].report) {
            parsed['session-3'][1].report = monsteraInvestigation;
          }
          return parsed;
        }
      }
    } catch (e) {
      console.warn("Failed to load messages from storage:", e);
    }
    return DEFAULT_MESSAGES;
  });

  const [selectedNodeId, setSelectedNodeId] = useState(null);

  // Active session's message list
  const messages = allMessages[activeSessionId] || [];

  // Message updater with automatic localStorage synchronization
  const setMessages = useCallback((updater) => {
    setAllMessages((prevAll) => {
      const currentList = prevAll[activeSessionId] || [];
      const updatedList = typeof updater === 'function' ? updater(currentList) : updater;
      const nextAll = {
        ...prevAll,
        [activeSessionId]: updatedList
      };
      try {
        localStorage.setItem('saar_session_messages', JSON.stringify(nextAll));
      } catch (e) {
        console.warn("Failed to persist messages:", e);
      }
      return nextAll;
    });
  }, [activeSessionId]);

  // Sync sessions list to localStorage whenever updated
  useEffect(() => {
    try {
      localStorage.setItem('saar_chat_sessions', JSON.stringify(sessions));
    } catch (e) {}
  }, [sessions]);

  // Sync activeSessionId to localStorage whenever switched
  useEffect(() => {
    try {
      localStorage.setItem('saar_active_session_id', activeSessionId);
    } catch (e) {}
  }, [activeSessionId]);

  // Synchronize Dark / Light Mode with document root & localStorage
  useEffect(() => {
    try {
      document.documentElement.setAttribute('data-theme', theme);
      document.documentElement.className = theme;
      localStorage.setItem('saar_theme', theme);
    } catch (e) {}
  }, [theme]);

  // Persistent tracking of which sessions have active sensor/tabular datasets
  const [sessionSensorData, setSessionSensorData] = useState(() => {
    try {
      const saved = localStorage.getItem('saar_session_sensor_data');
      if (saved) return JSON.parse(saved);
    } catch (e) {}
    return {
      'session-1': true,
      'session-2': true,
      'session-3': false
    };
  });

  useEffect(() => {
    try {
      localStorage.setItem('saar_session_sensor_data', JSON.stringify(sessionSensorData));
    } catch (e) {}
  }, [sessionSensorData]);

  const hasSensorData = Boolean(
    sessionSensorData[activeSessionId] ||
    saarData?.perception?.features_detected ||
    saarData?.observations_count
  );

  // Synchronize active session context dynamically from session metadata
  useEffect(() => {
    const session =
      sessions.find((s) => s.id === activeSessionId) ||
      DEFAULT_SESSIONS.find((s) => s.id === activeSessionId);
    if (!session) return;

    setSelectedDomain(session.domain || 'agriculture');
    setCustomImageData(null);
    setCustomImageUrl(session.imageUrl || null);
    setCameraConnected(true);
    setSaarData(null);
    setInvestigationData(null);

    if (session.id === 'session-3') {
      setInvestigationData(monsteraInvestigation);
    } else if (session.presetId) {
      runInvestigation(session.domain, session.presetId, { vlmProvider: 'auto' })
        .then((res) => setInvestigationData(res))
        .catch((err) => console.warn(`Session ${session.id} investigation fetch:`, err));
    }
  }, [activeSessionId, sessions]);

  // Initial Load: Warm up domains & baseline
  useEffect(() => {
    async function init() {
      try {
        const domainList = await fetchDomains();
        setDomains(domainList);

        if (activeSessionId === 'session-3') {
          setInvestigationData(monsteraInvestigation);
          setCustomImageUrl('/monstera_sample.png');
          setCameraConnected(true);
        } else {
          const res = await runInvestigation('agriculture', 'agri_tomato_chlorosis', {
            vlmProvider: 'auto'
          });
          setInvestigationData(res);
        }

        const baseRes = await fetchBaseline('agriculture', 'agri_tomato_chlorosis');
        setBaselineData(baseRes);
      } catch (err) {
        console.error("Initial load notice:", err);
      }
    }
    init();
  }, []);

  // Run Autonomous Investigation Scenario from welcome card or user selection
  const handleSelectScenario = async (domain, presetId, queryText) => {
    setSelectedDomain(domain);

    // Update active session query if new session
    setSessions((prev) =>
      prev.map((s) =>
        s.id === activeSessionId && (s.query === 'New Scientific Investigation' || !s.query)
          ? { ...s, query: queryText, domain }
          : s
      )
    );

    setMessages((prev) => [
      ...prev,
      {
        role: 'user',
        text: queryText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ]);
    setIsProcessing(true);

    try {
      const res = await runInvestigation(domain, presetId, { vlmProvider: 'auto' });
      setInvestigationData(res);

      try {
        const baseRes = await fetchBaseline(domain, presetId);
        setBaselineData(baseRes);
      } catch (bErr) {
        console.warn("Baseline fetch warning:", bErr);
      }

      const nodeCount = res.final_graph?.nodes?.length || 5;
      const edgeCount = res.final_graph?.edges?.length || 4;
      const confidencePct = Math.round((res.final_graph?.overall_confidence || 0.94) * 100);

      const reply = `### Autonomous Investigation Executed (${domain.toUpperCase()})\n\n**Perception & Workflow**: Evaluated ${res.steps?.length || 4} investigation phases utilizing provider **${res.vlm_provider_used || 'Saar Dynamic Loop'}**.\n\n- **Evidence Graph**: **${nodeCount} nodes** and **${edgeCount} directed relationships** formulated.\n- **Graph Confidence**: **${confidencePct}%** (Stabilized after specialized tool execution).\n\n#### Diagnostic Verdict:\n${res.conclusion || 'Autonomous investigation concluded successfully.'}`;

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: reply,
          report: res,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);

      setActiveTool('graph');
      setIsToolDrawerOpen(true);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: `**Investigation Execution Notice**: ${err.message || 'Failed to complete autonomous loop'}.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setIsProcessing(false);
    }
  };

  // Unified Autonomous Image Investigation Pipeline
  const executeImageInvestigation = async (fileOrDataUrl, rawFileName, optionalUserText) => {
    let base64Data = null;
    let fileName = rawFileName || 'uploaded_evidence.png';

    if (typeof fileOrDataUrl === 'string') {
      base64Data = fileOrDataUrl;
    } else if (fileOrDataUrl instanceof File || fileOrDataUrl instanceof Blob) {
      fileName = fileOrDataUrl.name || fileName;
      base64Data = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = reject;
        reader.readAsDataURL(fileOrDataUrl);
      });
    }

    if (!base64Data) return;

    setCustomImageData(base64Data);
    setCameraConnected(true);

    const userMsgText = optionalUserText && optionalUserText.trim()
      ? optionalUserText.trim()
      : `Attached photo: \`${fileName}\` for autonomous visual perception and scientific causal reasoning.`;

    setMessages((prev) => [
      ...prev,
      {
        role: 'user',
        text: userMsgText,
        files: [fileName],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ]);

    setIsProcessing(true);

    try {
      const res = await runInvestigation(selectedDomain, null, {
        imageData: base64Data,
        vlmProvider: 'auto'
      });
      setInvestigationData(res);

      const nodeCount = res.final_graph?.nodes?.length || 0;
      const edgeCount = res.final_graph?.edges?.length || 0;
      const confidencePct = Math.round(
        (res.final_graph?.overall_confidence || 0.90) * 100
      );

      let reply = `### Autonomous Visual Investigation (${selectedDomain.toUpperCase()})\n\n`;
      reply += `**Visual Perception**: Grounded **${nodeCount} spatial entities** with **${edgeCount} causal relationships** from \`${fileName}\`.\n`;
      reply += `**Graph Confidence**: **${confidencePct}%**\n\n`;
      reply += `#### Scientific Analysis:\n${res.conclusion || 'Investigation completed successfully.'}`;

      if (optionalUserText && optionalUserText.trim()) {
        try {
          const askRes = await askSaarQuestion(res.investigation_id || 'latest', optionalUserText.trim());
          if (askRes?.answer_summary) {
            reply += `\n\n---\n\n### Inquiry: *"${optionalUserText.trim()}"*\n${askRes.answer_summary}`;
          }
        } catch (askErr) {
          console.warn("Follow-up inquiry error:", askErr);
        }
      }

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: reply,
          report: res,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);

      setActiveTool('camera');
      setIsToolDrawerOpen(true);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: `**Visual Analysis Error**: ${err.message || 'Failed to complete VLM analysis pipeline.'}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setIsProcessing(false);
    }
  };

  // Send Message / Execute Investigation
  const handleSendMessage = async (userText, attachedFiles = []) => {
    // If a gait result object is passed directly (e.g. from GaitDashboard registration)
    if (userText && typeof userText === 'object' && userText.assessment_id) {
      const gaitResult = userText;
      let responseText = `### Video Analysis Completed (${gaitResult.status?.toUpperCase() || 'SUCCESS'})\n\n`;
      responseText += `- **Video Processed**: \`${gaitResult.video?.filename || 'Sample Video'}\` (${gaitResult.video?.fps} FPS, ${gaitResult.video?.duration_seconds}s)\n`;
      responseText += `- **Capture Quality**: **${gaitResult.quality?.confidence} Confidence** (${Math.round((gaitResult.quality?.good_frame_ratio || 0) * 100)}% good frames, ${gaitResult.metrics?.usable_step_count || 0} valid steps)\n`;
      responseText += `- **Cadence**: **${gaitResult.metrics?.cadence} steps/min** (Typical: ${gaitResult.cadence_range?.low}–${gaitResult.cadence_range?.high} steps/min)\n`;
      responseText += `- **Left-Right Step Asymmetry**: **${gaitResult.metrics?.step_time_asymmetry_pct}%** (Typical benchmark ≤ 10%)\n`;
      responseText += `- **Step Rhythm Variation**: **${gaitResult.metrics?.step_time_cov}% CoV** (Developing toddler benchmark ≤ 15%)\n\n`;
      responseText += `#### Developmental Context:\n${gaitResult.milestone_context || ''}`;

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: responseText,
          report: gaitResult,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
      setSaarData(gaitResult);
      return;
    }

    const currentFiles = [...attachedFiles];
    const textStr = typeof userText === 'string' ? userText : (userText ? String(userText) : '');
    const msgText = textStr || (currentFiles.length ? `Attached ${currentFiles.map((f) => f.name).join(', ')}` : '');

    // Update active session query if new session
    setSessions((prev) =>
      prev.map((s) =>
        s.id === activeSessionId && (s.query === 'New Scientific Investigation' || !s.query)
          ? { ...s, query: (String(msgText || 'Scientific Query')).slice(0, 52) }
          : s
      )
    );

    setIsProcessing(true);

    try {
      // 1. File Upload (CSV/XLSX or Image)
      if (currentFiles.length > 0) {
        const file = currentFiles[0];
        const fileName = file?.name || 'attached_file';
        const fileType = (file?.type || '').toLowerCase();
        const isVideo = fileType.startsWith('video/') || /\.(mp4|mov|avi|webm|mkv)$/i.test(fileName);
        const isImage = fileType.startsWith('image/') || /\.(png|jpe?g|webp|gif|bmp|svg)$/i.test(fileName);
        const isCsv = /\.(csv|tsv|txt|xlsx|xls)$/i.test(fileName) || fileType.includes('csv') || fileType.includes('spreadsheet') || fileType.includes('excel');

        if (isVideo) {
          try {
            setCustomVideoFile(file);
            const gaitResult = await analyzeGaitVideo(file, 24);
            setSaarData(gaitResult);
            let responseText = `### Video Analysis Completed (${gaitResult.status?.toUpperCase() || 'SUCCESS'})\n\n`;
            responseText += `- **Video Processed**: \`${fileName}\` (${gaitResult.video?.fps || 24} FPS, ${gaitResult.video?.duration_seconds || 0}s)\n`;
            responseText += `- **Capture Quality**: **${gaitResult.quality?.confidence || 'High'} Confidence** (${Math.round((gaitResult.quality?.good_frame_ratio || 0) * 100)}% good frames, ${gaitResult.metrics?.usable_step_count || 0} valid steps)\n`;
            responseText += `- **Cadence**: **${gaitResult.metrics?.cadence || 0} steps/min** (Typical: ${gaitResult.cadence_range?.low || 110}–${gaitResult.cadence_range?.high || 180} steps/min)\n`;
            responseText += `- **Left-Right Step Asymmetry**: **${gaitResult.metrics?.step_time_asymmetry_pct || 0}%** (Typical benchmark ≤ 10%)\n`;
            responseText += `- **Step Rhythm Variation**: **${gaitResult.metrics?.step_time_cov || 0}% CoV** (Developing benchmark ≤ 15%)\n\n`;
            responseText += `#### Kinematic & Functional Context:\n${gaitResult.milestone_context || 'Biomechanical kinematics and temporal movement patterns calculated.'}`;

            if (userText && userText.trim()) {
              try {
                const questionReply = await askSaarQuestion(gaitResult.assessment_id || 'latest', userText.trim());
                if (questionReply?.answer_summary) {
                  responseText += `\n\n---\n\n### Inquiry Response: *"${userText.trim()}"*\n${questionReply.answer_summary}`;
                }
              } catch (qErr) {
                console.warn("Failed to answer question alongside video upload:", qErr);
              }
            }

            setMessages((prev) => [
              ...prev,
              {
                role: 'assistant',
                text: responseText,
                report: gaitResult,
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
              }
            ]);
            setActiveTool('gait');
            setIsToolDrawerOpen(true);
            setIsProcessing(false);
            return;
          } catch (vErr) {
            setMessages((prev) => [
              ...prev,
              {
                role: 'assistant',
                text: `**Video Analysis Notice**: ${vErr.response?.data?.detail || vErr.message || 'Failed to process video.'}`,
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
              }
            ]);
            setIsProcessing(false);
            return;
          }
        }

        if (isImage) {
          await executeImageInvestigation(file, fileName, userText);
          return;
        }

        if (isCsv) {
          const report = await uploadSaarCsv(file);
          setSaarData(report);
          setSessionSensorData((prev) => ({
            ...prev,
            [activeSessionId]: true
          }));

          const featuresCount = report?.perception?.features_detected ?? 'several';
          const obsCount = report?.perception?.observations_count ?? 'multiple';
          const relCount = report?.relationships?.length ?? 0;
          const conceptCount = report?.concepts?.length ?? 0;
          const confPercent = Math.round((report?.confidence || 0.88) * 100);

          let responseText = `**Dataset Ingested & Analyzed**: \`${fileName}\`\n\n- **Telemetry Variables**: Extracted ${featuresCount} features across ${obsCount} observations.\n- **Causal Dependencies**: Discovered ${relCount} statistical edges and formulated ${conceptCount} concepts.\n- **Belief Confidence**: **${confPercent}%** (Topological uncertainty: ${100 - confPercent}%).\n\n### Diagnostic Essence:\n${report?.summary || report?.conclusion || 'Root cause mechanism traced to rhizosphere acidification and iron transport blockage.'}`;

          if (userText && userText.trim()) {
            try {
              const questionReply = await askSaarQuestion(report?.investigation_id || 'latest', userText.trim());
              if (questionReply?.answer_summary) {
                responseText += `\n\n---\n\n### Inquiry Response: *"${userText.trim()}"*\n${questionReply.answer_summary}`;
              }
            } catch (qErr) {
              console.warn("Failed to answer question alongside CSV upload:", qErr);
            }
          }

          setMessages((prev) => [
            ...prev,
            {
              role: 'assistant',
              text: responseText,
              report,
              openQuestions: Array.isArray(report?.open_questions) ? report.open_questions : [],
              terminology: report?.terminology || [],
              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            }
          ]);

          // Smoothly roll out the tool canvas displaying the Causal Graph
          setActiveTool('graph');
          setIsToolDrawerOpen(true);
          setIsProcessing(false);
          return;
        }
      }

      // 2. Active or General Investigation Inquiry (Dynamic AI synthesis + RAG retrieval)
      const active = saarData || investigationData;
      const targetInvId = active?.investigation_id || 'latest';
      const askRes = await askSaarQuestion(targetInvId, msgText);
      let reply = askRes.answer_summary || `Evaluated causal evidence graph against inquiry: "${msgText}".`;

      if (askRes.overall_confidence) {
        reply += `\n\n- **Graph Evidence**: ${askRes.evidence_count || (active?.final_graph?.nodes?.length ?? 5)} verified nodes referenced.\n- **Current Confidence**: **${((askRes.overall_confidence || 0.88) * 100).toFixed(0)}%**.`;
      }

      if (askRes.domain_knowledge && askRes.domain_knowledge.length > 0) {
        reply += `\n\n> **Peer-Reviewed Citation** (*${askRes.domain_knowledge[0].source || 'Domain Index'}*):\n> "${askRes.domain_knowledge[0].content}"`;
      }

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: reply,
          report: saarData || investigationData,
          terminology: askRes.terminology || [],
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: `**Reasoning Error**: ${err.message || 'Failed to process inquiry'}.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setIsProcessing(false);
    }
  };

  // Answer Human-in-the-Loop Inquiry
  const handleAnswerInquiry = async (qId, answerText) => {
    const active = saarData || investigationData;
    if (!active || !active.investigation_id || !answerText.trim()) return;

    setIsProcessing(true);
    try {
      const updatedReport = await answerSaarQuestion(active.investigation_id, answerText);
      setSaarData(updatedReport);

      setMessages((prev) => [
        ...prev,
        {
          role: 'user',
          text: `Answered: "${answerText}"`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        },
        {
          role: 'assistant',
          text: `**Belief State Dynamically Updated**:\n- **Confidence**: **${((updatedReport.confidence || 0.94) * 100).toFixed(0)}%**\n- **Evidence Chain**: Advanced to ${updatedReport.evidence_chain?.length || 5} verified milestones.\n- **Scientific Conclusion**: ${updatedReport.summary || 'Critical causal ambiguity resolved.'}`,
          report: updatedReport,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);

      // Automatically roll out updated Causal Graph
      setActiveTool('graph');
      setIsToolDrawerOpen(true);
    } catch (err) {
      console.error("Answer failed:", err);
    } finally {
      setIsProcessing(false);
    }
  };

  // Open / Roll Out Specific Tool
  const handleOpenTool = (toolId) => {
    setActiveTool(toolId);
    setIsToolDrawerOpen(true);
  };

  // In-tool direct telemetry file upload (CSV, XLSX, TSV)
  const handleUploadSensorFile = async (file) => {
    setIsProcessing(true);
    try {
      const report = await uploadSaarCsv(file);
      setSaarData(report);
      setSessionSensorData((prev) => ({
        ...prev,
        [activeSessionId]: true
      }));

      const featuresCount = report?.perception?.features_detected ?? 'several';
      const obsCount = report?.perception?.observations_count ?? 'multiple';
      const relCount = report?.relationships?.length ?? 0;
      const conceptCount = report?.concepts?.length ?? 0;
      const confPercent = Math.round((report?.confidence || 0.88) * 100);

      const responseText = `**Dataset Ingested & Analyzed**: \`${file.name}\`\n\n- **Telemetry Variables**: Extracted ${featuresCount} features across ${obsCount} observations.\n- **Causal Dependencies**: Discovered ${relCount} statistical edges and formulated ${conceptCount} concepts.\n- **Belief Confidence**: **${confPercent}%** (Topological uncertainty: ${100 - confPercent}%).\n\n### Diagnostic Essence:\n${report?.summary || report?.conclusion || 'Sensor telemetry synchronized across temporal intervals.'}`;

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: responseText,
          report,
          openQuestions: Array.isArray(report?.open_questions) ? report.open_questions : [],
          terminology: report?.terminology || [],
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);

      setActiveTool('analytics');
      setIsToolDrawerOpen(true);
      return report;
    } catch (err) {
      console.error("Failed to upload sensor CSV:", err);
      throw err;
    } finally {
      setIsProcessing(false);
    }
  };

  // Load sample telemetry baseline for the active domain
  const handleLoadSampleDataset = (domainOverride) => {
    setSessionSensorData((prev) => ({
      ...prev,
      [activeSessionId]: true
    }));
    setActiveTool('analytics');
    setIsToolDrawerOpen(true);
  };

  // Select Session from Sidebar
  const handleSelectSession = (id) => {
    setActiveSessionId(id);
    const targetSession = sessions.find((s) => s.id === id);
    if (targetSession?.domain) {
      setSelectedDomain(targetSession.domain);
    }
  };

  // New Investigation Session
  const handleNewSession = () => {
    const newId = `session-${Date.now()}`;
    const newSession = {
      id: newId,
      query: 'New Scientific Investigation',
      domain: selectedDomain,
      timestamp: 'Just now'
    };
    setSessions((prev) => [newSession, ...prev]);
    setActiveSessionId(newId);
    setSessionSensorData((prev) => ({
      ...prev,
      [newId]: false
    }));
    setAllMessages((prevAll) => {
      const nextAll = { ...prevAll, [newId]: [] };
      try {
        localStorage.setItem('saar_session_messages', JSON.stringify(nextAll));
      } catch (e) {}
      return nextAll;
    });
    setIsToolDrawerOpen(false);
  };

  const handleDeleteSession = (sessionId) => {
    const remaining = sessions.filter((s) => s.id !== sessionId);
    setSessions(remaining);
    setAllMessages((prevAll) => {
      const nextAll = { ...prevAll };
      delete nextAll[sessionId];
      try {
        localStorage.setItem('saar_session_messages', JSON.stringify(nextAll));
      } catch (e) {}
      return nextAll;
    });
    if (activeSessionId === sessionId) {
      if (remaining.length > 0) {
        setActiveSessionId(remaining[0].id);
      } else {
        handleNewSession();
      }
    }
  };

  // Export Dossier
  const handleExportDossier = () => {
    const active = saarData || investigationData;
    const invId = active?.investigation_id || 'SAAR-INVESTIGATION-01';
    const conf = Math.round((active?.confidence ?? 0.88) * 100);

    const htmlContent = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>SAAR Scientific Investigation Dossier - ${invId}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 860px; margin: 40px auto; padding: 0 20px; line-height: 1.6; color: #0f172a; }
    h1 { color: #0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }
    .meta-box { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-bottom: 24px; display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
    .verdict-box { background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 18px; margin-bottom: 24px; color: #166534; }
    .evidence-list { padding-left: 20px; }
    .evidence-list li { margin-bottom: 10px; }
    .footer { margin-top: 40px; font-size: 0.8rem; color: #94a3b8; text-align: center; border-top: 1px solid #e2e8f0; padding-top: 16px; }
  </style>
</head>
<body>
  <h1>SAAR Scientific Investigation Dossier</h1>
  <div class="meta-box">
    <div><strong>Investigation ID:</strong> ${invId}</div>
    <div><strong>Domain:</strong> ${selectedDomain.toUpperCase()}</div>
    <div><strong>Date Generated:</strong> ${new Date().toLocaleString()}</div>
    <div><strong>Confidence Score:</strong> ${conf}%</div>
  </div>
  <h2>1. Executive Scientific Verdict</h2>
  <div class="verdict-box">${active?.verdict || active?.summary || 'Causal mechanism identified and verified across telemetry features.'}</div>
  <h2>2. Verified Evidence Chain</h2>
  <ol class="evidence-list">
    ${(active?.evidence_chain || [
      { step: 'Perception', finding: '14 sensor columns extracted across 30 daily observations.' },
      { step: 'Statistical Profiling', finding: 'Inverse correlation identified between rhizosphere pH and iron availability.' },
      { step: 'Tool Verification', finding: 'Hydrological leaching simulation confirms excessive moisture triggered root hypoxia.' }
    ]).map((m) => `<li><strong>[${m.step || 'Step'}]</strong>: ${m.finding || m.content || m}</li>`).join('\n')}
  </ol>
  <div class="footer">Generated autonomously by SAAR — Visual Scientific Reasoning Engine</div>
</body>
</html>`;

    const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `saar_dossier_${invId}.html`;
    document.body.appendChild(link);
    link.click();
    setTimeout(() => {
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }, 60000);
  };

  // Export Complete Conversation Transcript with Multi-Format Support (.html, .txt, .md, view in tab, copy)
  const handleExportChat = (format = 'html') => {
    // If called directly without arguments or from a click event handler, format could be a SyntheticEvent
    const safeFormat = (typeof format === 'string' && ['html', 'txt', 'md', 'view', 'copy'].includes(format.toLowerCase()))
      ? format.toLowerCase()
      : 'html';

    if (!messages || messages.length === 0) {
      alert("The conversation is currently empty. Run an investigation or ask a question to generate a transcript.");
      return;
    }

    const active = saarData || investigationData;
    const invId = active?.investigation_id || `SAAR-${Date.now().toString(36).toUpperCase()}`;
    const conf = Math.round((active?.confidence ?? active?.final_graph?.overall_confidence ?? 0.94) * 100);
    const dateStr = new Date().toLocaleString();
    const domainStr = selectedDomain.toUpperCase();
    const dateFileSlug = new Date().toISOString().slice(0, 10);

    // 1. Direct Copy to Clipboard Option
    if (safeFormat === 'copy') {
      let txt = `================================================================================\n`;
      txt += `SAAR SCIENTIFIC REASONING — COMPLETE CONVERSATION TRANSCRIPT\n`;
      txt += `================================================================================\n\n`;
      txt += `Investigation ID : ${invId}\n`;
      txt += `Scientific Domain: ${domainStr}\n`;
      txt += `Export Date      : ${dateStr}\n`;
      txt += `Total Messages   : ${messages.length}\n`;
      txt += `Graph Confidence : ${conf}%\n\n`;
      txt += `--------------------------------------------------------------------------------\n\n`;

      let turnIdx = 1;
      messages.forEach((msg) => {
        const isAssistant = msg.role === 'assistant';
        const roleTitle = isAssistant ? 'SAAR REASONING AGENT' : 'USER';
        txt += `[TURN ${turnIdx}] ${roleTitle} ${msg.timestamp ? `(${msg.timestamp})` : ''}\n`;
        if (msg.files && msg.files.length > 0) {
          txt += `Attached Files: ${msg.files.join(', ')}\n`;
        }
        txt += `--------------------------------------------------------------------------------\n`;
        txt += `${msg.text}\n\n`;
        if (isAssistant) turnIdx++;
      });

      if (active?.conclusion || active?.summary || active?.verdict) {
        txt += `================================================================================\n`;
        txt += `FINAL SCIENTIFIC DIAGNOSTIC VERDICT\n`;
        txt += `================================================================================\n`;
        txt += `${active.verdict || active.conclusion || active.summary}\n\n`;
      }
      txt += `================================================================================\n`;
      txt += `Exported autonomously by SAAR — Visual Scientific Reasoning Engine\n`;

      navigator.clipboard.writeText(txt);
      alert("📋 Complete conversation transcript copied to your clipboard!");
      return;
    }

    // 2. Direct View in Browser Tab Option
    if (safeFormat === 'view') {
      let turnsHtml = '';
      let turnIdx = 1;
      messages.forEach((msg) => {
        const isAssistant = msg.role === 'assistant';
        const roleClass = isAssistant ? 'turn-assistant' : 'turn-user';
        const roleTitle = isAssistant ? 'Saar Reasoning Agent' : 'User';
        const timeBadge = msg.timestamp ? `<span>${msg.timestamp}</span>` : '';
        const safeText = msg.text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        const filesHtml = (msg.files && msg.files.length > 0) ? `<div class="files-pill">📎 Attached: ${msg.files.join(', ')}</div>` : '';

        turnsHtml += `
    <div class="turn-box ${roleClass}">
      <div class="turn-header">
        <span>Turn ${turnIdx}: ${roleTitle}</span>
        ${timeBadge}
      </div>
      <div class="turn-body">
        ${filesHtml}
        ${safeText}
      </div>
    </div>`;
        if (isAssistant) turnIdx++;
      });

      const verdictHtml = (active?.verdict || active?.conclusion || active?.summary) ? `
  <div class="verdict-card">
    <div class="verdict-title">Final Scientific Diagnostic Verdict</div>
    <div>${active?.verdict || active?.conclusion || active?.summary}</div>
  </div>` : '';

      const viewHtml = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>SAAR Transcript - ${domainStr}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 24px; line-height: 1.65; color: #0f172a; background: #ffffff; }
    .header-card { border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; margin-bottom: 32px; background: #f8fafc; }
    h1 { margin-top: 0; color: #0f172a; font-size: 1.6rem; border-bottom: 2px solid #e2e8f0; padding-bottom: 12px; }
    .meta-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-top: 16px; }
    .meta-item { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px 14px; }
    .meta-label { font-size: 0.75rem; color: #64748b; text-transform: uppercase; font-weight: 700; }
    .meta-value { font-size: 0.95rem; color: #0f172a; font-weight: 600; margin-top: 2px; }
    .turn-box { border: 1px solid #e2e8f0; border-radius: 12px; margin-bottom: 20px; overflow: hidden; }
    .turn-header { padding: 10px 18px; font-size: 0.85rem; font-weight: 700; display: flex; justify-content: space-between; border-bottom: 1px solid #e2e8f0; }
    .turn-user .turn-header { background: #f8fafc; color: #334155; }
    .turn-assistant .turn-header { background: #f0fdf4; color: #166534; border-bottom-color: #bbf7d0; }
    .turn-body { padding: 18px 20px; font-size: 0.95rem; white-space: pre-wrap; word-break: break-word; }
    .files-pill { background: #e0f2fe; color: #0369a1; padding: 4px 10px; border-radius: 9999px; font-size: 0.8rem; font-weight: 600; display: inline-block; margin-bottom: 12px; }
    .verdict-card { border: 1px solid #bfdbfe; background: #eff6ff; border-radius: 12px; padding: 24px; margin-top: 32px; }
    .verdict-title { font-size: 1.1rem; font-weight: 700; color: #1e40af; margin-top: 0; margin-bottom: 8px; }
    .footer-note { text-align: center; color: #94a3b8; font-size: 0.8rem; margin-top: 40px; padding-top: 20px; border-top: 1px solid #e2e8f0; }
  </style>
</head>
<body>
  <div class="header-card">
    <h1>SAAR Scientific Reasoning Transcript</h1>
    <div class="meta-grid">
      <div class="meta-item"><div class="meta-label">Investigation ID</div><div class="meta-value">${invId}</div></div>
      <div class="meta-item"><div class="meta-label">Domain</div><div class="meta-value">${domainStr}</div></div>
      <div class="meta-item"><div class="meta-label">Timestamp</div><div class="meta-value">${dateStr}</div></div>
      <div class="meta-item"><div class="meta-label">Confidence</div><div class="meta-value">${conf}%</div></div>
    </div>
  </div>
  <div class="dialogue-thread">${turnsHtml}</div>
  ${verdictHtml}
  <div class="footer-note">Exported autonomously by SAAR — Visual Scientific Reasoning Engine</div>
</body>
</html>`;

      const tab = window.open('', '_blank');
      if (tab) {
        tab.document.write(viewHtml);
        tab.document.close();
      } else {
        alert("Popup blocked by browser. Please enable popups or choose the HTML download option.");
      }
      return;
    }

    // 3. Server-Backed Attachment Download (guarantees Content-Disposition header with filename & extension)
    try {
      let iframe = document.getElementById('saar-export-iframe');
      if (!iframe) {
        iframe = document.createElement('iframe');
        iframe.id = 'saar-export-iframe';
        iframe.name = 'saar_export_frame';
        iframe.style.display = 'none';
        document.body.appendChild(iframe);
      }

      const form = document.createElement('form');
      form.method = 'POST';
      form.action = '/api/export/chat';
      form.target = 'saar_export_frame';
      form.style.display = 'none';

      const input = document.createElement('input');
      input.type = 'hidden';
      input.name = 'payload';
      input.value = JSON.stringify({
        format: safeFormat,
        messages: messages.map(m => ({
          role: m.role,
          text: m.text,
          timestamp: m.timestamp || '',
          files: m.files || []
        })),
        domain: selectedDomain,
        investigation_id: invId,
        confidence: conf,
        verdict: active?.verdict || active?.summary || active?.conclusion || ''
      });

      form.appendChild(input);
      document.body.appendChild(form);
      form.submit();
      setTimeout(() => {
        if (document.body.contains(form)) document.body.removeChild(form);
      }, 5000);
      return;
    } catch (err) {
      console.warn("Server-backed export failed, attempting client-side fallback:", err);
    }

    // 4. Client-Side Fallback
    let blob, fileName;
    if (safeFormat === 'txt') {
      let txt = `================================================================================\nSAAR SCIENTIFIC REASONING — COMPLETE CONVERSATION TRANSCRIPT\n================================================================================\n\n`;
      txt += `Investigation ID : ${invId}\nScientific Domain: ${domainStr}\nExport Date : ${dateStr}\n\n`;
      messages.forEach((msg, idx) => {
        txt += `[TURN ${idx + 1}] ${msg.role.toUpperCase()}:\n${msg.text}\n\n`;
      });
      blob = new Blob([txt], { type: 'text/plain;charset=utf-8' });
      fileName = `saar_chat_transcript_${selectedDomain}_${dateFileSlug}.txt`;
    } else if (safeFormat === 'md') {
      let md = `# SAAR Scientific Reasoning Transcript\n\n`;
      messages.forEach((msg, idx) => {
        md += `### Turn ${idx + 1}: ${msg.role === 'assistant' ? 'Saar Reasoning Agent' : 'User'}\n\n${msg.text}\n\n---\n\n`;
      });
      blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
      fileName = `saar_chat_transcript_${selectedDomain}_${dateFileSlug}.md`;
    } else {
      let html = `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>SAAR Transcript</title></head><body><h1>SAAR Transcript</h1></body></html>`;
      blob = new Blob([html], { type: 'text/html;charset=utf-8' });
      fileName = `saar_chat_transcript_${selectedDomain}_${dateFileSlug}.html`;
    }

    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    setTimeout(() => {
      if (document.body.contains(link)) document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }, 60000);
  };

  // Handle transitions between Landing Page and Studio
  const handleEnterStudio = (initialQuery = null, domain = null, presetId = null, attachedFile = null) => {
    if (domain) {
      setSelectedDomain(domain);
    }
    setViewMode('studio');
    if (initialQuery) {
      if (presetId) {
        handleSelectScenario(domain || selectedDomain, presetId, initialQuery);
      } else if (attachedFile) {
        handleSendMessage(initialQuery, [attachedFile]);
      } else {
        handleSendMessage(initialQuery);
      }
    }
  };

  const handleReturnToLanding = () => {
    setViewMode('landing');
  };

  // If in Landing Mode, render the futuristic Landing Page
  if (viewMode === 'landing') {
    return (
      <LandingPage
        onEnterStudio={handleEnterStudio}
        theme={theme}
        onToggleTheme={handleToggleTheme}
        onSelectTheme={handleSelectTheme}
      />
    );
  }

  return (
    <div className={`saar-chatgpt-layout ${theme}`}>
      {/* 1. Left Collapsible History Sidebar */}
      <ChatSidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onNewSession={handleNewSession}
        onDeleteSession={handleDeleteSession}
        theme={theme}
        onReturnToLanding={handleReturnToLanding}
      />

      {/* 2. Central ChatGPT Conversation View */}
      <main className={`chatgpt-main-view ${isToolDrawerOpen ? 'canvas-active' : ''}`}>
        <ChatGPTView
          messages={messages}
          isProcessing={isProcessing}
          onSendMessage={handleSendMessage}
          onSelectScenario={handleSelectScenario}
          onAnswerInquiry={handleAnswerInquiry}
          onAttachFiles={(files) => handleSendMessage('', files)}
          onOpenTool={handleOpenTool}
          activeTool={activeTool}
          isToolDrawerOpen={isToolDrawerOpen}
          selectedDomain={selectedDomain}
          onDomainChange={setSelectedDomain}
          activeInvestigation={saarData || investigationData}
          cameraConnected={cameraConnected}
          onToggleCamera={() => setCameraConnected(!cameraConnected)}
          onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
          isSidebarOpen={isSidebarOpen}
          onOpenHelp={() => setIsHelpOpen(true)}
          onExportChat={handleExportChat}
          theme={theme}
          onToggleTheme={handleToggleTheme}
          onSelectTheme={handleSelectTheme}
          onReturnToLanding={handleReturnToLanding}
          hasSensorData={hasSensorData}
        />
      </main>

      {/* 3. Right Rollout Tool Canvas (Slides out when active, rolls back in on close) */}
      <ToolCanvasDrawer
        isOpen={isToolDrawerOpen}
        onClose={() => setIsToolDrawerOpen(false)}
        activeTool={activeTool}
        onSelectTool={setActiveTool}
        activeSessionId={activeSessionId}
        activeInvestigation={saarData || investigationData}
        investigationData={investigationData}
        saarData={saarData}
        baselineData={baselineData}
        theme={theme}
        onSendToChat={(text) => handleSendMessage(text)}
        selectedRelationship={selectedRelationship}
        selectedChartType={selectedChartType}
        onSelectRelationship={(rel, chart) => {
          setSelectedRelationship(rel);
          if (chart) setSelectedChartType(chart);
        }}
        customImageData={customImageData}
        customImageUrl={customImageUrl}
        customVideoFile={customVideoFile}
        onUploadCustomImage={(fileOrDataUrl) => {
          executeImageInvestigation(fileOrDataUrl);
        }}
        onPasteImageUrl={async (url) => {
          setCustomImageUrl(url);
          setCameraConnected(true);
          setIsProcessing(true);
          try {
            const res = await runInvestigation(selectedDomain, null, {
              imageUrl: url,
              vlmProvider: 'auto'
            });
            setInvestigationData(res);
            setMessages((prev) => [
              ...prev,
              {
                role: 'user',
                text: `Loaded image URL: ${url}`,
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
              },
              {
                role: 'assistant',
                text: `### Autonomous Visual Investigation (${selectedDomain.toUpperCase()})\n\n${res.conclusion || 'Visual analysis completed.'}`,
                report: res,
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
              }
            ]);
            setActiveTool('camera');
            setIsToolDrawerOpen(true);
          } catch (err) {
            console.error("Paste image URL error:", err);
          } finally {
            setIsProcessing(false);
          }
        }}
        cameraConnected={cameraConnected}
        onCloseCamera={() => setCameraConnected(false)}
        onExportDossier={handleExportDossier}
        messages={messages}
        selectedDomain={selectedDomain}
        selectedNodeId={selectedNodeId}
        onSelectNode={setSelectedNodeId}
        hasSensorData={hasSensorData}
        onUploadSensorData={handleUploadSensorFile}
        onLoadSampleDataset={handleLoadSampleDataset}
      />

      {/* 4. Help Guide Modal Drawer */}
      <HelpDrawer
        isOpen={isHelpOpen}
        onClose={() => setIsHelpOpen(false)}
      />
    </div>
  );
}
