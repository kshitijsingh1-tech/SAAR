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

export const querySaarKnowledge = async (query, domain = null) => {
  const res = await axios.post(`${API_BASE_URL}/api/saar/knowledge/query`, { query, domain });
  return res.data;
};
