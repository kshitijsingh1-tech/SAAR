import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8001';

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
  const res = await axios.post(`${API_BASE_URL}/api/saar/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
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

export const querySaarKnowledge = async (query, domain = null) => {
  const res = await axios.post(`${API_BASE_URL}/api/saar/knowledge/query`, { query, domain });
  return res.data;
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
      const res = await axios.post(`${API_BASE_URL}/api/video/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
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
  const res = await axios.post(`${API_BASE_URL}/api/gait/analyze?child_age_months=${childAgeMonths}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
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

