import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Search, BookOpen, Sparkles, Send, Copy, Check,
  ExternalLink, Layers, ArrowRight, BookA, Info,
  CheckCircle2, AlertCircle, RefreshCw, Filter, Compass,
  Eye, Volume2, Globe, FileText, CheckCheck, Lightbulb
} from 'lucide-react';
import { lookupDictionaryWord, fetchGlossary } from '../api/client';

export function ScientificDictionaryDrawer({
  messages = [],
  activeInvestigation = null,
  saarData = null,
  investigationData = null,
  selectedDomain = 'agriculture',
  onSendToChat = null,
  theme = 'light'
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState('screen'); // 'screen', 'all', 'agriculture', 'infrastructure', 'astrophysics', 'causal'
  const [glossaryList, setGlossaryList] = useState([]);
  const [selectedWordData, setSelectedWordData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isGlossaryLoading, setIsGlossaryLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [lastScannedTime, setLastScannedTime] = useState(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));

  // In-memory cache to prevent repeated API calls and eliminate loading screens
  const definitionCache = React.useRef(new Map());

  // Helper to extract all visible screen text from DOM & state
  const captureAllScreenTexts = useCallback(() => {
    const textSnippets = [];

    // 1. From Chat messages
    messages.forEach((m) => {
      if (m.text) textSnippets.push(m.text);
      if (m.role) textSnippets.push(m.role);
    });

    // 2. From Active Investigation
    const activeData = saarData || investigationData || activeInvestigation;
    if (activeData) {
      if (activeData.conclusion) textSnippets.push(activeData.conclusion);
      if (activeData.domain) textSnippets.push(activeData.domain);
      if (activeData.vlm_provider_used) textSnippets.push(activeData.vlm_provider_used);
      if (activeData.steps) {
        activeData.steps.forEach((s) => {
          if (s.name) textSnippets.push(s.name);
          if (s.observation) textSnippets.push(s.observation);
          if (s.reasoning) textSnippets.push(s.reasoning);
        });
      }
      const g = activeData.graph_data || activeData.final_graph;
      if (g?.nodes) {
        g.nodes.forEach((n) => {
          if (n.label) textSnippets.push(n.label);
          if (n.category) textSnippets.push(n.category);
          if (n.properties) {
            Object.entries(n.properties).forEach(([k, v]) => textSnippets.push(`${k} ${v}`));
          }
        });
      }
    }

    // 3. From Visible Screen DOM
    try {
      const chatContainer = document.querySelector('.chatgpt-main-view') || document.body;
      if (chatContainer) {
        const visibleText = chatContainer.innerText || '';
        if (visibleText.length > 0) {
          textSnippets.push(visibleText.substring(0, 4000));
        }
      }
    } catch (e) {}

    return textSnippets;
  }, [messages, saarData, investigationData, activeInvestigation]);

  // Extract graph nodes
  const graphNodes = useMemo(() => {
    const g = saarData?.graph_data || investigationData?.final_graph || activeInvestigation?.final_graph;
    return g?.nodes || [];
  }, [saarData, investigationData, activeInvestigation]);

  // Handle selecting a term from anywhere (guarded against undefined/null)
  const handleSelectTerm = useCallback((termWord) => {
    const safeWord = typeof termWord === 'string' ? termWord : (termWord?.word || termWord?.term || '');
    if (!safeWord) return;
    setSearchTerm(safeWord);
    handleLookup(safeWord);
  }, []); // will be bound with handleLookup below

  // Instant local lookup from Cache & LocalStorage
  const getCachedEntry = useCallback((wordKey) => {
    const key = (typeof wordKey === 'string' ? wordKey : '').toLowerCase().trim();
    if (!key) return null;
    if (definitionCache.current.has(key)) {
      const memoryEntry = definitionCache.current.get(key);
      if (!memoryEntry?.source?.includes("Synthesizer") && !memoryEntry?.source?.includes("Morphological")) {
        return memoryEntry;
      }
    }
    try {
      const stored = localStorage.getItem(`saar_dict_${key}`);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (!parsed?.source?.includes("Synthesizer") && !parsed?.source?.includes("Morphological")) {
          definitionCache.current.set(key, parsed);
          return parsed;
        } else {
          localStorage.removeItem(`saar_dict_${key}`);
        }
      }
    } catch (e) {}
    return null;
  }, []);

  const saveCachedEntry = useCallback((wordKey, entryData) => {
    const key = (typeof wordKey === 'string' ? wordKey : '').toLowerCase().trim();
    if (!key || !entryData) return;
    definitionCache.current.set(key, entryData);
    try {
      localStorage.setItem(`saar_dict_${key}`, JSON.stringify(entryData));
    } catch (e) {}
  }, []);

  // Comprehensive Word Lookup (Robust Backend First + Live APIs)
  const handleLookup = useCallback(async (wordToSearch) => {
    const target = (typeof wordToSearch === 'string' ? wordToSearch : (searchTerm || '')).trim();
    if (!target) return;
    const lowerTarget = target.toLowerCase();

    // 1. FASTEST PATH: Instant Local Cache Check (0ms)
    const cached = getCachedEntry(lowerTarget);
    if (cached) {
      const normCached = {
        ...cached,
        word: cached.word || cached.term || target,
        definition: cached.definition || (cached.definitions && cached.definitions[0]) || 'Scientific definition.',
        scientific_context: cached.scientific_context || cached.investigation_context || '',
        diagnostic_indicator: cached.diagnostic_indicator || '',
        related_terms: cached.related_terms || cached.related_nodes || []
      };
      setSelectedWordData(normCached);
      setSearchTerm(normCached.word);
      setErrorMsg(null);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setErrorMsg(null);

    // 2. QUERY BACKEND API & LIVE APIS IN PARALLEL
    try {
      const backendPromise = lookupDictionaryWord(target, selectedDomain);

      const datamusePromise = fetch(`https://api.datamuse.com/words?sp=${encodeURIComponent(lowerTarget)}&md=dpr&max=3`)
        .then(async (res) => (res.ok ? await res.json() : null))
        .catch(() => null);

      const freedictPromise = fetch(`https://api.dictionaryapi.dev/api/v2/entries/en/${encodeURIComponent(lowerTarget)}`)
        .then(async (res) => (res.ok ? await res.json() : null))
        .catch(() => null);

      let backendData = null;
      try {
        backendData = await backendPromise;
      } catch (beErr) {
        console.warn("Backend lookup notice:", beErr);
      }

      // If backend returned a valid definition
      if (backendData && !backendData.error) {
        const normBackend = {
          ...backendData,
          word: backendData.word || backendData.term || target,
          definition: backendData.definition || (backendData.definitions && backendData.definitions[0]) || 'Scientific domain definition.',
          scientific_context: backendData.scientific_context || backendData.investigation_context || '',
          diagnostic_indicator: backendData.diagnostic_indicator || '',
          related_terms: backendData.related_terms || backendData.related_nodes || []
        };
        setSelectedWordData(normBackend);
        setSearchTerm(normBackend.word);
        saveCachedEntry(lowerTarget, normBackend);
        setIsLoading(false);

        // Background check for audio
        freedictPromise.then((fdJson) => {
          if (Array.isArray(fdJson) && fdJson.length > 0) {
            const audioUrl = fdJson[0].phonetics?.find((p) => p.audio)?.audio;
            if (audioUrl) {
              const enriched = { ...normBackend, audio_url: audioUrl };
              setSelectedWordData(enriched);
              saveCachedEntry(lowerTarget, enriched);
            }
          }
        });
        return;
      }

      // Fallback: evaluate browser Datamuse live response
      const dmData = await datamusePromise;
      const fdData = await freedictPromise;

      if (Array.isArray(dmData) && dmData.length > 0 && dmData[0].defs && dmData[0].defs.length > 0) {
        const item = dmData[0];
        const rawDefs = item.defs || [];
        const cleanDefs = rawDefs.map((d) => {
          if (typeof d !== 'string') return '';
          const parts = d.split("\t");
          return (parts.length > 1 ? parts[1] : parts[0]).trim();
        }).filter(Boolean);

        const posTag = (typeof rawDefs[0] === 'string' && rawDefs[0].split("\t")[0]) || "n";
        const pos = { n: "noun", v: "verb", adj: "adjective", adv: "adverb" }[posTag] || "noun";
        const pronTag = item.tags?.find((t) => typeof t === 'string' && t.startsWith("pron:"));
        const pron = pronTag ? pronTag.replace("pron:", "").trim() : null;
        const phoneticStr = pron ? `/${pron}/` : `/${lowerTarget}/`;
        const audioUrl = Array.isArray(fdData) && fdData[0]?.phonetics?.find((p) => p.audio)?.audio;

        const liveEntry = {
          word: item.word ? (item.word.charAt(0).toUpperCase() + item.word.slice(1)) : target,
          phonetic: phoneticStr,
          audio_url: audioUrl,
          part_of_speech: pos,
          domain: "General Academic & Scientific Vocabulary",
          category: "Live Lexical Definition",
          difficulty: "Dictionary Term",
          definition: cleanDefs[0] || "Standard lexical definition.",
          definitions: cleanDefs,
          scientific_context: `Evaluated as an active observation and contextual parameter in multi-agent reasoning.`,
          diagnostic_indicator: `Active parameter in current investigation session.`,
          formula_or_metric: null,
          examples: cleanDefs.length > 1 ? [`Usage context: ${cleanDefs[1]}`] : [`Empirical research reference for '${target}'.`],
          related_terms: ["Empirical Evidence", "Observation", "Hypothesis", "Analysis"],
          source: "Live Real API (WordNet / Datamuse)"
        };

        setSelectedWordData(liveEntry);
        setSearchTerm(liveEntry.word);
        saveCachedEntry(lowerTarget, liveEntry);
        setIsLoading(false);
        return;
      }

      if (Array.isArray(fdData) && fdData.length > 0) {
        const fdItem = fdData[0];
        const meanings = fdItem.meanings || [];
        const firstM = meanings[0] || {};
        const defs = firstM.definitions || [];
        const primaryDef = defs[0]?.definition || "Definition unavailable.";
        const example = defs[0]?.example || "";
        const phonetic = fdItem.phonetic || fdItem.phonetics?.[0]?.text || `/${lowerTarget}/`;
        const audioUrl = fdItem.phonetics?.find((p) => p.audio)?.audio;

        const liveEntry = {
          word: fdItem.word ? (fdItem.word.charAt(0).toUpperCase() + fdItem.word.slice(1)) : target,
          phonetic: phonetic,
          audio_url: audioUrl,
          part_of_speech: firstM.partOfSpeech || "noun",
          domain: "General Academic & Scientific Vocabulary",
          category: "Lexical Definition",
          difficulty: "Standard Academic",
          definition: primaryDef,
          scientific_context: `Evaluated as an active observation and contextual parameter in multi-agent reasoning.`,
          diagnostic_indicator: `Contextual parameter identified in observational discourse.`,
          formula_or_metric: null,
          examples: example ? [example] : [`The term '${target}' is referenced in empirical observation logs.`],
          related_terms: ["Evidence", "Observation", "Theory"],
          source: "Live Real API (Free Dictionary)"
        };

        setSelectedWordData(liveEntry);
        setSearchTerm(liveEntry.word);
        saveCachedEntry(lowerTarget, liveEntry);
        setIsLoading(false);
        return;
      }

      setErrorMsg(`Could not fetch definition for "${target}".`);
    } catch (err) {
      console.error("Dictionary lookup error:", err);
      setErrorMsg(`Could not fetch definition for "${target}".`);
    } finally {
      setIsLoading(false);
    }
  }, [searchTerm, selectedDomain, getCachedEntry, saveCachedEntry]);

  // Scan live screen text and update glossary
  const scanLiveScreen = useCallback(async () => {
    setIsGlossaryLoading(true);
    try {
      const screenTexts = captureAllScreenTexts();
      const res = await fetchGlossary(screenTexts, selectedDomain, graphNodes);
      if (res?.glossary && res.glossary.length > 0) {
        setGlossaryList(res.glossary);
        // Pre-populate cache with glossary items for 0ms clicks
        res.glossary.forEach(item => {
          const w = item.word || item.term;
          if (w) {
            definitionCache.current.set(w.toLowerCase(), {
              ...item,
              word: w,
              definition: item.definition || (item.definitions && item.definitions[0]) || 'Scientific definition.',
              scientific_context: item.scientific_context || item.investigation_context || '',
              diagnostic_indicator: item.diagnostic_indicator || '',
              related_terms: item.related_terms || item.related_nodes || []
            });
          }
        });
        setLastScannedTime(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));

        // Auto select the first detected word on screen if none selected
        if (!selectedWordData) {
          const inChat = res.glossary.find((g) => g.is_in_chat) || res.glossary[0];
          const autoWord = inChat?.word || inChat?.term;
          if (autoWord) {
            setSearchTerm(autoWord);
            handleLookup(autoWord);
          }
        }
      }
    } catch (err) {
      console.warn("Dynamic screen glossary scan error:", err);
    } finally {
      setIsGlossaryLoading(false);
    }
  }, [captureAllScreenTexts, selectedDomain, graphNodes, selectedWordData, handleLookup]);

  // Initial scan on load and when messages or domain changes
  useEffect(() => {
    scanLiveScreen();
  }, [messages.length, selectedDomain, (saarData || investigationData)?.conclusion]);

  const playAudioPhonetic = () => {
    if (selectedWordData?.audio_url) {
      const audio = new Audio(selectedWordData.audio_url);
      audio.play().catch(e => console.warn("Audio play error:", e));
    }
  };

  const handleCopyDefinition = () => {
    if (!selectedWordData) return;
    const word = selectedWordData.word || selectedWordData.term || 'Term';
    const textToCopy = `**${word}** (${selectedWordData.phonetic || ''}) [${selectedWordData.part_of_speech || 'term'}]\n*Domain*: ${selectedWordData.domain || 'Science'}\n\n**Definition**: ${selectedWordData.definition}\n\n**Scientific Context**: ${selectedWordData.scientific_context || selectedWordData.investigation_context || ''}\n${selectedWordData.formula_or_metric ? `\n**Formula/Metric**: ${selectedWordData.formula_or_metric}` : ''}`;
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSendDefinitionToChat = () => {
    if (!selectedWordData || !onSendToChat) return;
    const word = selectedWordData.word || selectedWordData.term || 'Term';
    const chatMsg = `📖 **Scientific Dictionary Lookup: ${word}** (${selectedWordData.phonetic || ''})\n\n- **Category**: \`${selectedWordData.category || selectedWordData.domain || 'Scientific Term'}\` [${selectedWordData.difficulty || 'Specialized'}]\n- **Definition**: ${selectedWordData.definition}\n\n> 🔬 **Diagnostic Context**: ${selectedWordData.scientific_context || selectedWordData.investigation_context || 'Standard domain parameter in reasoning.'}\n${selectedWordData.formula_or_metric ? `\n📐 **Equation/Metric**: \`${selectedWordData.formula_or_metric}\`\n` : ''}`;
    onSendToChat(chatMsg);
  };

  const handleAskSaarAboutTerm = () => {
    if (!selectedWordData || !onSendToChat) return;
    const word = selectedWordData.word || selectedWordData.term || 'Term';
    const prompt = `Can you explain the detailed scientific role and diagnostic relevance of **${word}** in our current ${selectedDomain} investigation?`;
    onSendToChat(prompt);
  };

  // Filter glossary list
  const filteredGlossary = useMemo(() => {
    return glossaryList.filter(item => {
      if (activeTab === 'screen') return item.is_in_chat;
      const d = (item.domain || item.category || '').toLowerCase();
      if (activeTab === 'agriculture') return d.includes('agri') || d.includes('plant') || d.includes('soil');
      if (activeTab === 'infrastructure') return d.includes('infra') || d.includes('civil') || d.includes('radar') || d.includes('ndt');
      if (activeTab === 'astrophysics') return d.includes('astro') || d.includes('space') || d.includes('stellar');
      if (activeTab === 'sports') return d.includes('sport') || d.includes('biomechanic') || d.includes('kinematic') || d.includes('athletic');
      if (activeTab === 'causal') return d.includes('causal') || d.includes('bayes') || d.includes('ai') || d.includes('graph');
      return true; // 'all'
    });
  }, [glossaryList, activeTab]);

  const countInScreen = useMemo(() => {
    return glossaryList.filter(item => item.is_in_chat).length;
  }, [glossaryList]);

  return (
    <div className="dictionary-drawer-root">
      {/* Search Bar & Auto Query Controls */}
      <div className="dictionary-search-section">
        <form
          className="dictionary-search-box"
          onSubmit={(e) => {
            e.preventDefault();
            handleLookup(searchTerm);
          }}
        >
          <Search size={18} className="dict-search-icon" />
          <input
            type="text"
            className="dict-search-input"
            placeholder="Search any scientific term or word (e.g. Chlorosis, Piezometer, Transit, Permittivity)..."
            value={searchTerm || ''}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          {(searchTerm || '').trim().length > 0 && (
            <button
              type="button"
              className="dict-clear-btn"
              onClick={() => setSearchTerm('')}
              title="Clear search"
            >
              ×
            </button>
          )}
          <button
            type="submit"
            className="dict-submit-btn"
            disabled={isLoading || !(searchTerm || '').trim()}
          >
            {isLoading ? <RefreshCw size={15} className="spin-animate" /> : 'Define'}
          </button>
        </form>

        {/* Live Screen Scanner Bar */}
        <div className="dict-scanner-header">
          <div className="scanner-status">
            <span className="live-pulse-dot" />
            <span><strong>Live Screen Detector</strong>: {countInScreen} difficult terms identified on screen</span>
            <span className="last-scan-time">({lastScannedTime})</span>
          </div>

          <button
            className="rescan-screen-btn"
            onClick={scanLiveScreen}
            disabled={isGlossaryLoading}
            title="Rescan current screen text and chat dialogue"
          >
            <RefreshCw size={12} className={isGlossaryLoading ? 'spin-animate' : ''} />
            <span>{isGlossaryLoading ? 'Scanning...' : 'Rescan Screen'}</span>
          </button>
        </div>
      </div>

      {/* Main Split View */}
      <div className="dictionary-content-split">
        {/* Left Column: Live Screen Glossary List */}
        <div className="dictionary-glossary-panel">
          <div className="glossary-panel-header">
            <div className="glossary-title-group">
              <Eye size={15} className="text-amber-600" />
              <h4>Screen & Chat Glossary</h4>
            </div>
            {countInScreen > 0 && (
              <span className="live-chat-badge">
                <span className="live-pulse-dot" /> {countInScreen} on screen
              </span>
            )}
          </div>

          {/* Category Filter Tabs */}
          <div className="glossary-filter-tabs">
            <button
              className={`glossary-tab-btn ${activeTab === 'screen' ? 'active' : ''}`}
              onClick={() => setActiveTab('screen')}
            >
              ⚡ On Screen ({countInScreen})
            </button>
            <button
              className={`glossary-tab-btn ${activeTab === 'all' ? 'active' : ''}`}
              onClick={() => setActiveTab('all')}
            >
              All ({glossaryList.length})
            </button>
            <button
              className={`glossary-tab-btn ${activeTab === 'agriculture' ? 'active' : ''}`}
              onClick={() => setActiveTab('agriculture')}
            >
              🌿 Agri
            </button>
            <button
              className={`glossary-tab-btn ${activeTab === 'infrastructure' ? 'active' : ''}`}
              onClick={() => setActiveTab('infrastructure')}
            >
              🛣️ Infra
            </button>
            <button
              className={`glossary-tab-btn ${activeTab === 'astrophysics' ? 'active' : ''}`}
              onClick={() => setActiveTab('astrophysics')}
            >
              🪐 Astro
            </button>
            <button
              className={`glossary-tab-btn ${activeTab === 'sports' ? 'active' : ''}`}
              onClick={() => setActiveTab('sports')}
            >
              🏸 Sports
            </button>
            <button
              className={`glossary-tab-btn ${activeTab === 'causal' ? 'active' : ''}`}
              onClick={() => setActiveTab('causal')}
            >
              🧠 Causal
            </button>
          </div>

          {/* Cards List */}
          <div className="glossary-cards-scroll">
            {isGlossaryLoading ? (
              <div className="dict-loading-placeholder">
                <RefreshCw size={22} className="spin-animate text-amber-500" />
                <span>Scanning screen and extracting scientific terms...</span>
              </div>
            ) : filteredGlossary.length === 0 ? (
              <div className="dict-empty-state">
                <Info size={24} className="text-gray-400" />
                <p>No terms matching this category filter.</p>
                <button
                  className="dict-chip-btn"
                  onClick={() => setActiveTab('all')}
                >
                  View All Glossary Terms
                </button>
              </div>
            ) : (
              filteredGlossary.map((item, idx) => {
                const itemWord = item.word || item.term || `term-${idx}`;
                const currentSelectedWord = selectedWordData?.word || selectedWordData?.term || '';
                const isSelected = currentSelectedWord.toLowerCase() === itemWord.toLowerCase();
                return (
                  <div
                    key={`${itemWord}-${idx}`}
                    className={`glossary-card ${isSelected ? 'selected' : ''} ${item.is_in_chat ? 'in-chat-card' : ''}`}
                    onClick={() => {
                      setSearchTerm(itemWord);
                      handleLookup(itemWord);
                    }}
                  >
                    <div className="glossary-card-top">
                      <div className="glossary-card-title">
                        <strong>{itemWord}</strong>
                        {item.phonetic && <span className="glossary-phonetic">{item.phonetic}</span>}
                      </div>
                      <div className="glossary-badges">
                        {item.is_in_chat && (
                          <span className="chat-mention-pill" title="Present on visible screen/dialogue">
                            {item.occurrences_in_chat > 1 ? `${item.occurrences_in_chat}x on screen` : 'On Screen'}
                          </span>
                        )}
                        <span className="difficulty-pill">{item.difficulty || item.domain || 'Domain Term'}</span>
                      </div>
                    </div>

                    <p className="glossary-card-def">
                      {(item.definition || (item.definitions && item.definitions[0]) || '').length > 95
                        ? `${(item.definition || item.definitions[0]).substring(0, 95)}...`
                        : (item.definition || (item.definitions && item.definitions[0]) || 'Domain terminology parameter.')}
                    </p>

                    <div className="glossary-card-footer">
                      <span className="glossary-domain-tag">{item.domain || item.category || 'Science'}</span>
                      <span className="glossary-explore-link">
                        Define <ArrowRight size={12} />
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right Column: Word Definition Inspector */}
        <div className="dictionary-detail-panel">
          {isLoading && !selectedWordData ? (
            <div className="dict-loading-pane">
              <RefreshCw size={28} className="spin-animate text-amber-600" />
              <h4>Retrieving Definition...</h4>
              <p>Fetching lexical definitions and domain diagnostic context...</p>
            </div>
          ) : errorMsg ? (
            <div className="dict-error-pane">
              <AlertCircle size={28} className="text-red-500" />
              <h4>Term Not Found</h4>
              <p>{errorMsg}</p>
            </div>
          ) : selectedWordData ? (
            <div className={`word-detail-container ${isLoading ? 'opacity-75' : ''}`}>
              {/* Word Header */}
              <div className="word-detail-header">
                <div className="word-title-row">
                  <h3 className="word-headline">{selectedWordData.word || selectedWordData.term}</h3>
                  {selectedWordData.phonetic && (
                    <span className="word-phonetic-badge">{selectedWordData.phonetic}</span>
                  )}
                  {selectedWordData.audio_url && (
                    <button
                      className="word-audio-btn"
                      onClick={playAudioPhonetic}
                      title="Play pronunciation audio"
                    >
                      <Volume2 size={14} />
                    </button>
                  )}
                  {selectedWordData.part_of_speech && (
                    <span className="word-pos-badge">{selectedWordData.part_of_speech}</span>
                  )}
                </div>

                <div className="word-meta-row">
                  <span className="domain-pill-highlight">
                    {selectedWordData.domain || 'Scientific Terminology'}
                  </span>
                  {selectedWordData.category && (
                    <span className="category-pill-highlight">
                      {selectedWordData.category}
                    </span>
                  )}
                  {selectedWordData.source && (
                    <span className="source-pill-muted">
                      Source: {selectedWordData.source}
                    </span>
                  )}
                </div>
              </div>

              {/* Action Toolbar */}
              <div className="word-action-toolbar">
                <button
                  className="word-action-btn btn-send-chat"
                  onClick={handleSendDefinitionToChat}
                  title="Send formatted definition into active dialogue"
                >
                  <Send size={14} />
                  <span>Send to Chat</span>
                </button>

                <button
                  className="word-action-btn btn-ask-saar"
                  onClick={handleAskSaarAboutTerm}
                  title="Ask SAAR's reasoning loop to analyze this term"
                >
                  <Sparkles size={14} />
                  <span>Ask SAAR</span>
                </button>

                <button
                  className="word-action-btn btn-copy-def"
                  onClick={handleCopyDefinition}
                  title="Copy definition text"
                >
                  {copied ? <Check size={14} className="text-green-600" /> : <Copy size={14} />}
                  <span>{copied ? 'Copied!' : 'Copy'}</span>
                </button>
              </div>

              {/* Primary Definition */}
              <div className="word-section-card">
                <div className="section-label">
                  <BookA size={15} className="text-amber-600" />
                  <span>Primary Definition & Meaning</span>
                </div>
                <p className="word-main-definition">{selectedWordData.definition || (selectedWordData.definitions && selectedWordData.definitions[0]) || 'Scientific definition.'}</p>
              </div>

              {/* Scientific Context & Diagnostic Role */}
              {(selectedWordData.scientific_context || selectedWordData.investigation_context) && (
                <div className="word-section-card scientific-context-card">
                  <div className="section-label">
                    <Sparkles size={15} className="text-indigo-600" />
                    <span>Scientific Context & Diagnostic Role</span>
                  </div>
                  <p className="word-context-text">{selectedWordData.scientific_context || selectedWordData.investigation_context}</p>
                  {selectedWordData.diagnostic_indicator && (
                    <div className="diagnostic-indicator-box">
                      <strong>Observation Indicator:</strong> {selectedWordData.diagnostic_indicator}
                    </div>
                  )}
                </div>
              )}

              {/* Formula / Diagnostic Metric (if available) */}
              {selectedWordData.formula_or_metric && (
                <div className="word-section-card formula-card">
                  <div className="section-label">
                    <Layers size={15} className="text-emerald-600" />
                    <span>Equation / Diagnostic Metric</span>
                  </div>
                  <div className="formula-code-box">
                    <code>{selectedWordData.formula_or_metric}</code>
                  </div>
                </div>
              )}

              {/* Examples */}
              {selectedWordData.examples && selectedWordData.examples.length > 0 && (
                <div className="word-section-card">
                  <div className="section-label">
                    <CheckCircle2 size={15} className="text-blue-600" />
                    <span>Empirical Research Example</span>
                  </div>
                  <ul className="word-examples-list">
                    {selectedWordData.examples.map((ex, i) => (
                      <li key={i}>"{ex}"</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Related Scientific Concepts */}
              {((selectedWordData.related_terms && selectedWordData.related_terms.length > 0) ||
                (selectedWordData.related_nodes && selectedWordData.related_nodes.length > 0)) && (
                <div className="word-section-card">
                  <div className="section-label">
                    <ExternalLink size={15} className="text-purple-600" />
                    <span>Related Concepts & Causal Links</span>
                  </div>
                  <div className="related-terms-cloud">
                    {(selectedWordData.related_terms || selectedWordData.related_nodes || []).map((rt) => (
                      <button
                        key={rt}
                        className="related-term-chip"
                        onClick={() => {
                          setSearchTerm(rt);
                          handleLookup(rt);
                        }}
                      >
                        {rt}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="dict-placeholder-pane">
              <BookOpen size={48} className="text-amber-400 opacity-60" />
              <h4>Live Scientific Dictionary & Screen Scanner</h4>
              <p>Type any word into the search bar or select any detected word from the active screen to view its definition, pronunciation, equations, and diagnostic indicators.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
