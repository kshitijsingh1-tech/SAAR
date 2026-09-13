import axios from 'axios';

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8002';

export const fetchDomains = async () => {
  const res = await axios.get(`${API_BASE_URL}/domains`);
  return res.data;
};

export const runInvestigation = async (domain, presetId, options = {}) => {
  const payload = {
    domain,
    preset_id: presetId,
    image_data: options.imageData || null,
    image_url: options.imageUrl || null,
    images: options.images || null,
    image_metadata: options.imageMetadata || options.image_metadata || null,
    vlm_provider: options.vlmProvider || 'auto',
    api_key: options.apiKey || null
  };
  const res = await axios.post(`${API_BASE_URL}/investigate`, payload);
  return res.data;
};

export const fetchBaseline = async (domain, presetId) => {
  const res = await axios.get(`${API_BASE_URL}/baseline`, {
    params: { domain, preset_id: presetId }
  });
  return res.data;
};

// ------------------------------------------------------------------
// SAAR Iterative Reasoning API
// ------------------------------------------------------------------

export const uploadSaarCsv = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await axios.post(`${API_BASE_URL}/api/saar/upload`, formData);
  return res.data;
};

export const getSaarInvestigation = async (investigationId) => {
  const res = await axios.get(`${API_BASE_URL}/api/saar/investigation/${investigationId}`);
  return res.data;
};

export const answerSaarQuestion = async (investigationId, rawAnswer, structuredData = {}) => {
  const payload = {
    raw_answer: rawAnswer,
    structured_data: structuredData
  };
  const res = await axios.post(`${API_BASE_URL}/api/saar/investigation/${investigationId}/answer`, payload);
  return res.data;
};

export const askSaarQuestion = async (investigationId, question) => {
  if (!investigationId || investigationId === 'latest' || investigationId === 'general') {
    const res = await axios.post(`${API_BASE_URL}/api/saar/ask`, { question });
    return res.data;
  }
  const res = await axios.post(`${API_BASE_URL}/api/saar/investigation/${investigationId}/ask`, { question });
  return res.data;
};

export const askSaarGeneral = async (question, domain = 'agriculture') => {
  const res = await axios.post(`${API_BASE_URL}/api/saar/ask`, { question, domain });
  return res.data;
};

export const fetchSaarKnowledge = async () => {
  const res = await axios.get(`${API_BASE_URL}/api/saar/knowledge`);
  return res.data;
};

export const fetchKeyStatus = async () => {
  const res = await axios.get(`${API_BASE_URL}/api/keys/status`);
  return res.data;
};

export const querySaarKnowledge = async (query, domain = 'agriculture', topK = 4) => {
  const res = await axios.post(`${API_BASE_URL}/api/saar/knowledge/query`, {
    query,
    domain,
    top_k: topK
  });
  return res.data;
};

export const lookupScientificTerm = async (term, domain = 'general', context = '') => {
  const res = await axios.post(`${API_BASE_URL}/api/dictionary/lookup`, {
    term,
    domain,
    context
  });
  return res.data;
};

export const lookupDictionaryWord = async (term, domain = 'general') => {
  return lookupScientificTerm(term, domain);
};

export const fetchGlossary = async (screenTexts = [], domain = 'agriculture', graphNodes = []) => {
  try {
    let payload;
    if (Array.isArray(screenTexts)) {
      payload = { screen_texts: screenTexts, domain: typeof domain === 'string' ? domain : 'agriculture', graph_nodes: graphNodes };
    } else if (typeof screenTexts === 'object' && screenTexts !== null) {
      payload = screenTexts;
    } else {
      payload = { screen_texts: [String(screenTexts || '')], domain: 'agriculture' };
    }
    const res = await axios.post(`${API_BASE_URL}/api/dictionary/glossary`, payload);
    return res.data;
  } catch (e) {
    try {
      const targetDomain = (typeof domain === 'string' ? domain : screenTexts?.domain) || 'agriculture';
      const res = await axios.post(`${API_BASE_URL}/api/saar/ask`, {
        question: "Extract key scientific terminology and concepts",
        domain: targetDomain
      });
      const terms = res.data?.terminology || [];
      return { glossary: terms.map(t => ({ ...t, word: t.term || t.word, is_in_chat: true })) };
    } catch (err) {
      return { glossary: [] };
    }
  }
};


// ------------------------------------------------------------------
// Multimodal Video Processing API (Workstream 1 & 4)
// ------------------------------------------------------------------

export const analyzeVideo = async (fileOrUrl, domain = 'agriculture', options = {}) => {
  try {
    if (typeof fileOrUrl === 'string') {
      // URL input
      const res = await axios.post(`${API_BASE_URL}/api/video/analyze`, {
        video_url: fileOrUrl,
        domain,
        sample_fps: options.sampleFps || 2.0
      });
      return res.data;
    } else {
      // File upload
      const formData = new FormData();
      formData.append('file', fileOrUrl);
      formData.append('domain', domain);
      formData.append('sample_fps', String(options.sampleFps || 2.0));
      const res = await axios.post(`${API_BASE_URL}/api/video/upload`, formData);
      return res.data;
    }
  } catch (err) {
    console.warn("Video backend endpoint error:", err);
    return {
      status: 'error',
      message: err.message || 'Video analysis endpoint unavailable',
      video_duration: options.duration || 0,
      sample_fps: 2.0,
      total_frames_extracted: 0,
      keyframes: []
    };
  }
};


// ------------------------------------------------------------------
// ToddleAI Pediatric Gait Analysis API
// ------------------------------------------------------------------

export const analyzeGaitVideo = async (file, childAgeMonths = 24) => {
  const formData = new FormData();
  formData.append('video', file);
  const res = await axios.post(`${API_BASE_URL}/api/gait/analyze?child_age_months=${childAgeMonths}`, formData);
  return res.data;
};

export const analyzeGaitSample = async (childAgeMonths = 24) => {
  const res = await axios.get(`${API_BASE_URL}/api/gait/sample`, {
    params: { child_age_months: childAgeMonths }
  });
  return res.data;
};

export const getGaitSampleVideoUrl = () => {
  return `${API_BASE_URL}/api/gait/sample/video`;
};

export const getGaitAssessment = async (assessmentId) => {
  const res = await axios.get(`${API_BASE_URL}/api/gait/assessment/${assessmentId}`);
  return res.data;
};

export const askGaitQuestion = async (assessmentId, question) => {
  const res = await axios.post(`${API_BASE_URL}/api/gait/assessment/${assessmentId}/ask`, {
    question
  });
  return res.data;
};

export const classifyVideo = async (file, contextText = '') => {
  const formData = new FormData();
  formData.append('video', file);
  if (contextText) {
    formData.append('context', contextText);
  }
  const res = await axios.post(`${API_BASE_URL}/api/video/classify`, formData);
  return res.data;
};

// ------------------------------------------------------------------
// Badminton Biomechanics Video Analysis API
// ------------------------------------------------------------------

export const analyzeBadmintonVideo = async (file, metadata = {}) => {
  const formData = new FormData();
  formData.append('video', file);
  const params = new URLSearchParams();
  if (metadata.age) params.append('player_age', metadata.age);
  if (metadata.body_weight_kg) params.append('body_weight_kg', metadata.body_weight_kg);
  if (metadata.session_duration_min) params.append('session_duration_min', metadata.session_duration_min);
  if (metadata.skill_level) params.append('skill_level', metadata.skill_level);
  if (metadata.match_type) params.append('match_type', metadata.match_type);
  const paramStr = params.toString() ? `?${params.toString()}` : '';

  const res = await axios.post(`${API_BASE_URL}/api/sports/badminton/analyze${paramStr}`, formData);
  return res.data;
};

export const analyzeBadmintonSample = async () => {
  const res = await axios.get(`${API_BASE_URL}/api/sports/badminton/sample`);
  return res.data;
};

export const getBadmintonSampleVideoUrl = () => {
  return `${API_BASE_URL}/api/sports/badminton/sample/video`;
};

export const getBadmintonRecordingGuidance = async () => {
  const res = await axios.get(`${API_BASE_URL}/api/sports/badminton/recording-guidance`);
  return res.data;
};

export const getBadmintonAnalysis = async (analysisId) => {
  const res = await axios.get(`${API_BASE_URL}/api/sports/badminton/analysis/${analysisId}`);
  return res.data;
};

export const askBadmintonQuestion = async (analysisId, question) => {
  const res = await axios.post(`${API_BASE_URL}/api/sports/badminton/analysis/${analysisId}/ask`, {
    question
  });
  return res.data;
};

// ------------------------------------------------------------------
// Badminton v1 Asynchronous Processing API (Section 28)
// ------------------------------------------------------------------

export const uploadBadmintonVideoV1 = async (file, metadata = {}) => {
  const formData = new FormData();
  formData.append('video', file);
  const params = new URLSearchParams();
  if (metadata.age) params.append('player_age', metadata.age);
  if (metadata.body_weight_kg) params.append('body_weight_kg', metadata.body_weight_kg);
  if (metadata.session_duration_min) params.append('session_duration_min', metadata.session_duration_min);
  if (metadata.skill_level) params.append('skill_level', metadata.skill_level);
  if (metadata.match_type) params.append('match_type', metadata.match_type);
  const paramStr = params.toString() ? `?${params.toString()}` : '';

  const res = await axios.post(`${API_BASE_URL}/api/v1/videos/upload${paramStr}`, formData);
  return res.data;
};

export const startBadmintonAnalysisV1 = async (jobId) => {
  const res = await axios.post(`${API_BASE_URL}/api/v1/analysis/start`, { job_id: jobId });
  return res.data;
};

export const getBadmintonJobProgressV1 = async (jobId) => {
  const res = await axios.get(`${API_BASE_URL}/api/v1/analysis/${jobId}/progress`);
  return res.data;
};

export const getBadmintonJobReportV1 = async (jobId) => {
  const res = await axios.get(`${API_BASE_URL}/api/v1/analysis/${jobId}/report`);
  return res.data;
};

export const getBadmintonCourtV1 = async (jobId) => {
  const res = await axios.get(`${API_BASE_URL}/api/v1/analysis/${jobId}/court`);
  return res.data;
};

export const calibrateBadmintonCourtV1 = async (jobId, cornersPixel, courtMode = 'doubles') => {
  const res = await axios.post(`${API_BASE_URL}/api/v1/analysis/${jobId}/court/calibrate`, {
    corners_pixel: cornersPixel,
    court_mode: courtMode
  });
  return res.data;
};

export const getBadmintonRalliesV1 = async (jobId) => {
  const res = await axios.get(`${API_BASE_URL}/api/v1/analysis/${jobId}/rallies`);
  return res.data;
};

export const getBadmintonShotsV1 = async (jobId) => {
  const res = await axios.get(`${API_BASE_URL}/api/v1/analysis/${jobId}/shots`);
  return res.data;
};

export const getBadmintonMovementV1 = async (jobId) => {
  const res = await axios.get(`${API_BASE_URL}/api/v1/analysis/${jobId}/movement`);
  return res.data;
};

export const getBadmintonCoverageV1 = async (jobId) => {
  const res = await axios.get(`${API_BASE_URL}/api/v1/analysis/${jobId}/coverage`);
  return res.data;
};

export const getBadmintonPoseV1 = async (jobId) => {
  const res = await axios.get(`${API_BASE_URL}/api/v1/analysis/${jobId}/pose`);
  return res.data;
};

export const getBadmintonSpeedV1 = async (jobId) => {
  const res = await axios.get(`${API_BASE_URL}/api/v1/analysis/${jobId}/speed`);
  return res.data;
};

export const getBadmintonEnergyV1 = async (jobId) => {
  const res = await axios.get(`${API_BASE_URL}/api/v1/analysis/${jobId}/energy`);
  return res.data;
};

export const getBadmintonRecommendationsV1 = async (jobId) => {
  const res = await axios.get(`${API_BASE_URL}/api/v1/analysis/${jobId}/recommendations`);
  return res.data;
};


