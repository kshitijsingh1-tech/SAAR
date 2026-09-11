import React, { useState, useRef, useEffect } from 'react';
import {
  Sparkles, ArrowUp, Paperclip, Camera, FileText,
  X, Loader2, GitFork, BarChart2, ShieldCheck, Sliders,
  BookOpen, ChevronDown, PanelLeft, AlertTriangle,
  CornerDownRight, CheckCircle2, ArrowRight, ExternalLink,
  HelpCircle, Download, Copy, Check, Globe, FileCode,
  Crosshair, BookA, Image as ImageIcon
} from 'lucide-react';
import { MarkdownResponse } from './MarkdownResponse';
import { ToolRolloutBar } from './ToolRolloutBar';

// Built-in grounded domain lexicon for automatic chat dictionary linking
const SCIENTIFIC_LEXICON = [
  {
    term: "Rhizosphere",
    domain: "Soil Microbiology",
    definition: "The narrow micro-ecological zone of soil surrounding plant roots directly influenced by root secretions, microbial activity, and nutrient exchange.",
    diagnostic_indicator: "Root-zone moisture >45% VWC with dissolved oxygen <0.8 mg/L.",
    investigation_context: "The primary interface where waterlogging and pH shifts govern nutrient uptake in crops.",
    related_nodes: ["Root Zone Moisture", "Substrate pH", "Bioavailable Fe²⁺", "Hypoxia"]
  },
  {
    term: "Substrate Alkalinization",
    domain: "Soil Chemistry",
    definition: "An increase in root substrate pH above neutral (>7.5), causing soluble ferrous iron (Fe²⁺) to precipitate into insoluble ferric hydroxides.",
    diagnostic_indicator: "Substrate pH rising above 7.6 accompanied by sharp drops in bioavailable Fe²⁺.",
    investigation_context: "Primary causal driver of iron lockup in tomato crops.",
    related_nodes: ["Substrate pH", "Bioavailable Fe²⁺", "Chlorosis"]
  },
  {
    term: "Chlorosis",
    domain: "Plant Pathology",
    definition: "Loss of normal green pigmentation in plant foliage caused by impaired chlorophyll biosynthesis or iron mobilization.",
    diagnostic_indicator: "Interveinal yellowing of leaf tissue with green vein retention.",
    investigation_context: "Direct biological symptom of iron starvation in terminal foliage.",
    related_nodes: ["Bioavailable Fe²⁺", "NDRE Index", "Photosynthesis"]
  },
  {
    term: "NDRE Index",
    domain: "Remote Sensing",
    definition: "Normalized Difference Red Edge index measuring foliar chlorophyll density in dense vegetative canopies.",
    diagnostic_indicator: "Drop from healthy 0.65 down to acute chlorosis 0.18.",
    investigation_context: "Continuous optical verification of chlorophyll degradation.",
    related_nodes: ["Foliar Chlorosis", "Vegetative Vigor"]
  },
  {
    term: "Root Anoxia",
    domain: "Plant Physiology",
    definition: "Complete or near-complete depletion of dissolved oxygen (<0.8 mg/L) in the root zone, shutting down aerobic ATP generation.",
    diagnostic_indicator: "Moisture > 45% VWC sustained for >72 hours.",
    investigation_context: "Paralyzes active H⁺-ATPase pumps, preventing nutrient uptake.",
    related_nodes: ["Soil Saturation", "ATP Synthesis", "Root Rot"]
  },
  {
    term: "GPR Hyperbolic Reflection",
    domain: "Geotechnical NDT",
    definition: "A characteristic point-source radar signature formed by radar pulse velocity contrasts between asphalt and subterranean air/water voids.",
    diagnostic_indicator: "High-amplitude radar echo loss (-82%).",
    investigation_context: "Non-destructive verification of subsurface cavity.",
    related_nodes: ["Sub-base Void", "Dielectric Permittivity"]
  },
  {
    term: "Sub-base Void",
    domain: "Structural Engineering",
    definition: "An unsupported air or water cavity formed beneath the asphalt binder layer by internal aggregate erosion.",
    diagnostic_indicator: "Void diameter > 1.2m with shear fatigue cracking.",
    investigation_context: "Direct causal driver of flexible pavement collapse.",
    related_nodes: ["GPR Reflection", "Alligator Cracking"]
  }
];

export function ChatGPTView({
  messages,
  isProcessing,
  onSendMessage,
  onSelectScenario,
  onAnswerInquiry,
  onAttachFiles,
  onOpenTool,
  activeTool,
  isToolDrawerOpen,
  selectedDomain,
  onDomainChange,
  activeInvestigation,
  cameraConnected,
  onToggleCamera,
  onToggleSidebar,
  isSidebarOpen,
  onOpenHelp,
  onExportChat,
  theme = 'light'
}) {
  const [inputText, setInputText] = useState('');
  const [attachedFiles, setAttachedFiles] = useState([]);
  const [answeringQId, setAnsweringQId] = useState(null);
  const [customAnswerText, setCustomAnswerText] = useState('');

  // Floating "Ask Saar" Selection Popover State (ChatGPT style)
  const [selectionPopover, setSelectionPopover] = useState(null);
  const [copiedSelection, setCopiedSelection] = useState(false);

  // Multi-format Export Chat Dropdown state
  const [isExportMenuOpen, setIsExportMenuOpen] = useState(false);
  const [activeTermModal, setActiveTermModal] = useState(null);
  const exportMenuRef = useRef(null);

  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  // Close export dropdown when clicking outside
  useEffect(() => {
    const handleOutsideClick = (e) => {
      if (exportMenuRef.current && !exportMenuRef.current.contains(e.target)) {
        setIsExportMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleOutsideClick);
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, []);

  const saarLogoSrc = '/saar-logo-dark.png';
  const saarWordmarkSrc = '/saar-wordmark-dark.png';

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isProcessing]);

  // Global mouseup listener to display floating "Ask Saar" over highlighted text
  useEffect(() => {
    const handleMouseUp = (e) => {
      if (e.target.closest('.floating-ask-saar-popover') || e.target.closest('.composer-input')) {
        return;
      }
      setTimeout(() => {
        const selection = window.getSelection();
        const selectedText = selection?.toString().trim();
        if (selectedText && selectedText.length > 2) {
          try {
            const range = selection.getRangeAt(0);
            const rect = range.getBoundingClientRect();
            if (rect && rect.width > 0) {
              setSelectionPopover({
                text: selectedText,
                top: Math.max(10, rect.top - 46),
                left: Math.max(12, rect.left + rect.width / 2 - 80)
              });
              return;
            }
          } catch (err) {}
        }
        setSelectionPopover(null);
      }, 10);
    };

    document.addEventListener('mouseup', handleMouseUp);
    return () => {
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, []);

  const handleAskSaarFromSelection = (e) => {
    e.stopPropagation();
    if (!selectionPopover?.text) return;
    const quote = selectionPopover.text;
    const prompt = `> "${quote}"\n\nExplain and verify this causal finding: `;
    setInputText(prompt);
    setSelectionPopover(null);
    window.getSelection()?.removeAllRanges();
    if (textareaRef.current) {
      textareaRef.current.focus();
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight + 35, 180)}px`;
    }
    scrollToBottom();
  };

  const handleCopySelection = (e) => {
    e.stopPropagation();
    if (!selectionPopover?.text) return;
    navigator.clipboard.writeText(selectionPopover.text);
    setCopiedSelection(true);
    setTimeout(() => {
      setCopiedSelection(false);
      setSelectionPopover(null);
    }, 1200);
  };

  const handleAskSaarFromAction = (content, pairedQuestion) => {
    const clean = content.replace(/^[#>*\s-]+/gm, '').trim();
    const snippet = clean.split('\n')[0].slice(0, 140);
    const prompt = `Can you elaborate on the causal mechanism for: "${snippet}"?`;
    setInputText(prompt);
    if (textareaRef.current) {
      textareaRef.current.focus();
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight + 35, 180)}px`;
    }
    scrollToBottom();
  };

  const handleSend = () => {
    if (!inputText.trim() && attachedFiles.length === 0) return;
    onSendMessage(inputText, attachedFiles);
    setInputText('');
    setAttachedFiles([]);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleTextareaChange = (e) => {
    setInputText(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 180)}px`;
  };

  const handleFileChange = (e) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      setAttachedFiles((prev) => [...prev, ...files]);
    }
  };

  const handlePaste = (e) => {
    const clipboardData = e.clipboardData;
    if (!clipboardData) return;

    // Check for clipboard files (e.g. copied screenshots, images from Snipping Tool, copied files)
    const items = Array.from(clipboardData.items || []);
    const fileItems = items.filter((item) => item.kind === 'file');

    if (fileItems.length > 0) {
      const pastedFiles = [];
      for (const item of fileItems) {
        const file = item.getAsFile();
        if (file) {
          let name = file.name;
          if (!name || name === 'image.png') {
            const ext = file.type.split('/')[1] || 'png';
            name = `pasted_evidence_${Date.now()}.${ext}`;
          }
          const namedFile = new File([file], name, { type: file.type });
          pastedFiles.push(namedFile);
        }
      }

      if (pastedFiles.length > 0) {
        e.preventDefault();
        setAttachedFiles((prev) => [...prev, ...pastedFiles]);
        return;
      }
    }

    if (clipboardData.files && clipboardData.files.length > 0) {
      e.preventDefault();
      const files = Array.from(clipboardData.files);
      setAttachedFiles((prev) => [...prev, ...files]);
      return;
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFiles = Array.from(e.dataTransfer.files);
      setAttachedFiles((prev) => [...prev, ...droppedFiles]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  return (
    <div className="chatgpt-container">
      {/* Top Navbar */}
      <header className="chatgpt-header">
        <div className="header-left">
          {!isSidebarOpen && (
            <button
              className="sidebar-toggle-btn"
              onClick={onToggleSidebar}
              title="Open sidebar"
            >
              <PanelLeft size={18} />
            </button>
          )}

          {/* Domain Dropdown Pill */}
          <div className="domain-select-dropdown">
            <select
              value={selectedDomain}
              onChange={(e) => onDomainChange(e.target.value)}
              className="domain-select"
            >
              <option value="agriculture">Crop Science &amp; Agronomy</option>
              <option value="infrastructure">Civil Infrastructure</option>
              <option value="astronomy">Astrophysics &amp; Space</option>
            </select>
          </div>

          <div className="active-session-title">
            {activeInvestigation?.verdict
              ? activeInvestigation.verdict.slice(0, 48) + '...'
              : 'Empirical Scientific Reasoning'}
          </div>
        </div>

        <div className="header-right">
          {messages.length > 0 && (
            <div className="export-chat-dropdown-wrapper" ref={exportMenuRef}>
              <button
                type="button"
                className="header-export-btn"
                onClick={() => setIsExportMenuOpen((prev) => !prev)}
                title="Export entire chat conversation"
                aria-haspopup="true"
                aria-expanded={isExportMenuOpen}
              >
                <Download size={14} className="export-btn-icon" />
                <span>Export Chat</span>
                <ChevronDown size={12} className={`export-menu-arrow ${isExportMenuOpen ? 'open' : ''}`} />
              </button>

              {isExportMenuOpen && (
                <div className="export-menu-dropdown">
                  <div className="export-menu-section-title">DOWNLOAD FILE</div>

                  <button
                    type="button"
                    className="export-menu-item"
                    onClick={() => {
                      onExportChat('html');
                      setIsExportMenuOpen(false);
                    }}
                  >
                    <div className="export-icon-box html-badge">
                      <Globe size={16} />
                    </div>
                    <div className="export-item-content">
                      <div className="export-item-header">
                        <span className="export-item-title">Web Document (.html)</span>
                        <span className="export-badge">Recommended</span>
                      </div>
                      <span className="export-item-subtitle">Opens in Edge, Chrome, or any browser</span>
                    </div>
                  </button>

                  <button
                    type="button"
                    className="export-menu-item"
                    onClick={() => {
                      onExportChat('txt');
                      setIsExportMenuOpen(false);
                    }}
                  >
                    <div className="export-icon-box txt-badge">
                      <FileText size={16} />
                    </div>
                    <div className="export-item-content">
                      <div className="export-item-header">
                        <span className="export-item-title">Text Document (.txt)</span>
                      </div>
                      <span className="export-item-subtitle">Opens in Notepad on any Windows system</span>
                    </div>
                  </button>

                  <button
                    type="button"
                    className="export-menu-item"
                    onClick={() => {
                      onExportChat('md');
                      setIsExportMenuOpen(false);
                    }}
                  >
                    <div className="export-icon-box md-badge">
                      <FileCode size={16} />
                    </div>
                    <div className="export-item-content">
                      <div className="export-item-header">
                        <span className="export-item-title">Markdown Document (.md)</span>
                      </div>
                      <span className="export-item-subtitle">For Obsidian, GitHub, or code editors</span>
                    </div>
                  </button>

                  <div className="export-menu-divider" />
                  <div className="export-menu-section-title">QUICK ACTIONS</div>

                  <button
                    type="button"
                    className="export-menu-item action-item"
                    onClick={() => {
                      onExportChat('view');
                      setIsExportMenuOpen(false);
                    }}
                  >
                    <div className="export-icon-box view-badge">
                      <ExternalLink size={16} />
                    </div>
                    <div className="export-item-content">
                      <div className="export-item-header">
                        <span className="export-item-title">Open in Browser Tab</span>
                      </div>
                      <span className="export-item-subtitle">Read, review, or print to PDF instantly</span>
                    </div>
                  </button>

                  <button
                    type="button"
                    className="export-menu-item action-item"
                    onClick={() => {
                      onExportChat('copy');
                      setIsExportMenuOpen(false);
                    }}
                  >
                    <div className="export-icon-box copy-badge">
                      <Copy size={16} />
                    </div>
                    <div className="export-item-content">
                      <div className="export-item-header">
                        <span className="export-item-title">Copy Entire Chat</span>
                      </div>
                      <span className="export-item-subtitle">Copy full conversation text to clipboard</span>
                    </div>
                  </button>
                </div>
              )}
            </div>
          )}

          <button
            className="header-guide-btn"
            onClick={onOpenHelp}
            title="Open Saar System User Guide"
          >
            <HelpCircle size={15} className="guide-btn-icon" />
            <span>Guide</span>
          </button>
        </div>
      </header>

      {/* Centered Conversation Area */}
      <div className="chatgpt-body">
        <div className="chatgpt-messages-thread">
          {messages.length === 0 ? (
            /* Welcome / Empty State */
            <div className="chatgpt-welcome-canvas">
              <div className="welcome-brand-mark">
                <img
                  src={saarLogoSrc}
                  alt="Saar Logo"
                  className="welcome-saar-logo-img"
                />
              </div>
              <div className="welcome-wordmark-row">
                <img
                  src={saarWordmarkSrc}
                  alt="SAAR"
                  className="welcome-saar-wordmark-img"
                />
              </div>
              <h1 className="welcome-heading">Visual Scientific Reasoning Engine</h1>
              <p className="welcome-subheading">
                Saar pairs multi-modal visual perception with active causal graph reasoning
                to diagnose root causes across agriculture, civil structures, and astrophysics.
              </p>

              {/* Sample Prompt Cards */}
              <div className="welcome-prompt-cards">
                <button
                  className="prompt-card"
                  onClick={() => onSelectScenario ? onSelectScenario('agriculture', 'agri_tomato_chlorosis', 'Investigate the 30-day tomato crop failure dataset and isolate the root cause of leaf chlorosis.') : onSendMessage('Investigate the 30-day tomato crop failure dataset and isolate the root cause of leaf chlorosis.')}
                >
                  <div className="prompt-title">Tomato Crop 30-Day Failure</div>
                  <div className="prompt-desc">Isolate soil moisture, alkalinity surge, and iron uptake block.</div>
                </button>

                <button
                  className="prompt-card"
                  onClick={() => onSelectScenario ? onSelectScenario('infrastructure', 'infra_damaged_road', 'Analyze highway pavement surface cracking and sub-surface GPR cavity void reflections.') : onSendMessage('Analyze highway pavement surface cracking and sub-surface GPR cavity void reflections.')}
                >
                  <div className="prompt-title">Highway Pavement Cavity Void</div>
                  <div className="prompt-desc">Correlate surface alligator cracks with 1.8m sub-base GPR radar void.</div>
                </button>

                <button
                  className="prompt-card"
                  onClick={() => onSelectScenario ? onSelectScenario('astronomy', 'astro_stellar_spectrum', 'Evaluate exoplanet transit depth lightcurve against stellar flare noise contamination.') : onSendMessage('Evaluate exoplanet transit depth lightcurve against stellar flare noise contamination.')}
                >
                  <div className="prompt-title">Exoplanet Transit Spectroscopy</div>
                  <div className="prompt-desc">Separate achromatic planetary occultation from stellar flare noise.</div>
                </button>

                <button
                  className="prompt-card"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <div className="prompt-title">Upload Telemetry Dataset</div>
                  <div className="prompt-desc">Ingest CSV or XLSX dataset for autonomous column profiling and causal modeling.</div>
                </button>
              </div>
            </div>
          ) : (
            messages.map((msg, index) => {
              // Extract paired question/response so both are copied together
              let pairedText = null;
              if (msg.role === 'assistant') {
                for (let i = index - 1; i >= 0; i--) {
                  if (messages[i].role === 'user') {
                    pairedText = messages[i].text;
                    break;
                  }
                }
              } else if (msg.role === 'user') {
                for (let i = index + 1; i < messages.length; i++) {
                  if (messages[i].role === 'assistant') {
                    pairedText = messages[i].text;
                    break;
                  }
                }
              }

              return (
                <div key={index} className={`chatgpt-message-row ${msg.role}`}>
                  <div className="message-container">
                    <div className="message-avatar-circle">
                      {msg.role === 'assistant' ? (
                        <img src={saarLogoSrc} alt="Saar" className="avatar-saar-logo" />
                      ) : (
                        <div className="user-dot">U</div>
                      )}
                    </div>

                    <div className="message-text-column">
                      <div className="message-author-row">
                        <span className="author-name">
                          {msg.role === 'assistant' ? 'Saar Reasoning Agent' : 'You'}
                        </span>
                        {msg.timestamp && <span className="message-time">{msg.timestamp}</span>}
                      </div>

                      <div className="message-content-text">
                        <MarkdownResponse
                          content={msg.text}
                          pairedQuestion={pairedText}
                          role={msg.role}
                          onAskSaar={handleAskSaarFromAction}
                        />
                      </div>

                    {/* Attached Files Pills */}
                    {msg.files && msg.files.length > 0 && (
                      <div className="message-files-list">
                        {msg.files.map((file, fIdx) => (
                          <span key={fIdx} className="file-chip">
                            <FileText size={12} />
                            <span>{typeof file === 'string' ? file : file.name}</span>
                          </span>
                        ))}
                      </div>
                    )}

                    {/* In-Chat Tool Invocation Badges */}
                    {msg.role === 'assistant' && msg.report && (
                      <div className="chat-tool-badges-row">
                        <button
                          className="tool-invoke-badge badge-graph"
                          onClick={() => onOpenTool('grounded')}
                        >
                          <Crosshair size={14} className="text-primary" />
                          <span>Grounded Split Graph</span>
                          <ArrowRight size={12} className="badge-arrow" />
                        </button>

                        <button
                          className="tool-invoke-badge badge-graph"
                          onClick={() => onOpenTool('graph')}
                        >
                          <GitFork size={14} className="text-purple" />
                          <span>Causal Knowledge Graph ({msg.report.relationships?.length || 8} Edges)</span>
                          <ArrowRight size={12} className="badge-arrow" />
                        </button>

                        <button
                          className="tool-invoke-badge badge-analytics"
                          onClick={() => onOpenTool('analytics')}
                        >
                          <BarChart2 size={14} className="text-primary" />
                          <span>Sensor Analytics</span>
                          <ArrowRight size={12} className="badge-arrow" />
                        </button>

                        <button
                          className="tool-invoke-badge badge-camera"
                          onClick={() => onOpenTool('camera')}
                        >
                          <Camera size={14} className="text-rose" />
                          <span>Visual Evidence Monitor</span>
                          <ArrowRight size={12} className="badge-arrow" />
                        </button>

                        <button
                          className="tool-invoke-badge badge-rag"
                          onClick={() => onOpenTool('rag')}
                        >
                          <BookOpen size={14} className="text-purple" />
                          <span>Scientific References</span>
                          <ArrowRight size={12} className="badge-arrow" />
                        </button>

                        <button
                          className="tool-invoke-badge badge-dictionary"
                          onClick={() => onOpenTool('dictionary')}
                        >
                          <BookA size={14} className="text-amber" />
                          <span>Scientific Dictionary</span>
                          <ArrowRight size={12} className="badge-arrow" />
                        </button>
                      </div>
                    )}

                    {/* Interactive Human-in-the-Loop Inquiry Cards */}
                    {msg.openQuestions && Array.isArray(msg.openQuestions) && msg.openQuestions.length > 0 && (
                      <div className="chat-inquiry-box">
                        <div className="inquiry-box-title">
                          <AlertTriangle size={14} className="text-amber" />
                          <span>Uncertainty Reduction Inquiries</span>
                        </div>

                        {msg.openQuestions.map((q, qIdx) => {
                          const qId = typeof q === 'object' && q ? (q.question_id || q.id || `q_${qIdx}`) : `q_${qIdx}`;
                          const qText = typeof q === 'string' ? q : (q?.question || q?.text || q?.reason || 'Field observation inquiry');
                          const rawImpact = typeof q === 'object' && q ? (q.impact || q.reason || q.targets_uncertainty || '') : '';
                          const qImpact = typeof rawImpact === 'string' ? rawImpact : '';
                          const qPriority = typeof q === 'object' && q?.priority ? q.priority : 'high';

                          return (
                            <div key={qId} className="inquiry-item">
                              <p className="inquiry-prompt">{qText}</p>
                              {qImpact && <div className="inquiry-impact">Impact: {qImpact}</div>}

                              <div className="inquiry-quick-answers">
                                <button
                                  className="quick-answer-pill"
                                  onClick={() => onAnswerInquiry(qId, 'Yes, observed telemetry anomaly confirmed in field.')}
                                >
                                  Yes, confirmed
                                </button>
                                <button
                                  className="quick-answer-pill"
                                  onClick={() => onAnswerInquiry(qId, 'No, field conditions remained within nominal thresholds.')}
                                >
                                  No, within thresholds
                                </button>
                              </div>

                              <div className="inquiry-custom-input-line">
                                <input
                                  type="text"
                                  placeholder="Or enter field observation..."
                                  value={answeringQId === qId ? customAnswerText : ''}
                                  onChange={(e) => {
                                    setAnsweringQId(qId);
                                    setCustomAnswerText(e.target.value);
                                  }}
                                  onKeyDown={(e) => {
                                    if (e.key === 'Enter' && customAnswerText.trim()) {
                                      onAnswerInquiry(qId, customAnswerText.trim());
                                      setCustomAnswerText('');
                                    }
                                  }}
                                />
                                <button
                                  className="submit-inquiry-btn"
                                  onClick={() => {
                                    if (customAnswerText.trim()) {
                                      onAnswerInquiry(qId, customAnswerText.trim());
                                      setCustomAnswerText('');
                                    }
                                  }}
                                  disabled={!customAnswerText.trim()}
                                >
                                  <span>Submit</span>
                                  <CornerDownRight size={12} />
                                </button>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}

                    {/* Scientific Terminology & Grounded Lexical Intelligence */}
                    {msg.role === 'assistant' && (() => {
                      const terms = (msg.terminology && Array.isArray(msg.terminology) && msg.terminology.length > 0)
                        ? msg.terminology
                        : (msg.text
                            ? SCIENTIFIC_LEXICON.filter((lex) => {
                                const tLower = lex.term.toLowerCase();
                                const textLower = msg.text.toLowerCase();
                                return textLower.includes(tLower) ||
                                  (lex.term === 'Chlorosis' && textLower.includes('chloros')) ||
                                  (lex.term === 'Rhizosphere' && (textLower.includes('rhizospher') || textLower.includes('rhizophere'))) ||
                                  (lex.term === 'Substrate Alkalinization' && (textLower.includes('alkalin') || textLower.includes('ph > 7') || textLower.includes('alkaline'))) ||
                                  (lex.term === 'NDRE Index' && textLower.includes('ndre')) ||
                                  (lex.term === 'Root Anoxia' && (textLower.includes('anoxia') || textLower.includes('hypoxia'))) ||
                                  (lex.term === 'Sub-base Void' && (textLower.includes('void') || textLower.includes('cavity')));
                              })
                            : []);

                      if (!terms || terms.length === 0) return null;

                      return (
                        <div className="chat-terminology-container">
                          <div className="terminology-header">
                            <BookOpen size={13} className="text-purple" />
                            <span>Scientific Concepts &amp; Terminology</span>
                          </div>
                          <div className="terminology-chips-row">
                            {terms.map((t, tIdx) => (
                              <button
                                key={tIdx}
                                type="button"
                                className="terminology-chip"
                                onClick={() => setActiveTermModal(t)}
                                title={`Inspect scientific definition for ${t.term}`}
                              >
                                <span className="term-badge-icon">📖</span>
                                <span className="term-name">{t.term}</span>
                                {t.domain && <span className="term-domain-pill">{t.domain.split(' ')[0]}</span>}
                              </button>
                            ))}
                          </div>
                        </div>
                      );
                    })()}
                  </div>
                </div>
              </div>
            );
          }))}

          {isProcessing && (
            <div className="chatgpt-message-row assistant">
              <div className="message-container">
                <div className="message-avatar-circle">
                  <Loader2 size={16} className="spin text-primary" />
                </div>
                <div className="message-text-column">
                  <div className="agent-thinking-pulse">
                    <span className="pulse-circle" />
                    <span>Evaluating causal graph &amp; formulating hypotheses...</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Floating Scientific Tools Action in Chat Area */}
      <div className="chat-floating-tools-anchor">
        <ToolRolloutBar
          onOpenTool={onOpenTool}
          activeTool={activeTool}
          isDrawerOpen={isToolDrawerOpen}
          floating={true}
        />
      </div>

      {/* Floating Bottom Composer Capsule */}
      <div className="chatgpt-composer-wrapper">
        {/* Attached files chip preview */}
        {attachedFiles.length > 0 && (
          <div className="composer-files-tray">
            {attachedFiles.map((file, idx) => (
              <span key={idx} className="file-preview-pill">
                {file.type?.startsWith('image/') || /\.(png|jpe?g|webp|gif|bmp|svg)$/i.test(file.name) ? (
                  <ImageIcon size={12} />
                ) : (
                  <FileText size={12} />
                )}
                <span>{file.name}</span>
                <button
                  className="remove-file-btn"
                  onClick={() => setAttachedFiles(attachedFiles.filter((_, i) => i !== idx))}
                >
                  <X size={12} />
                </button>
              </span>
            ))}
          </div>
        )}

        <div
          className="composer-capsule"
          onPaste={handlePaste}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
        >
          <input
            type="file"
            ref={fileInputRef}
            style={{ display: 'none' }}
            accept=".csv,.xlsx,.xls,.png,.jpg,.jpeg"
            onChange={handleFileChange}
          />

          {/* Plus Attach Button */}
          <button
            className="composer-action-btn"
            onClick={() => fileInputRef.current?.click()}
            title="Attach CSV/XLSX dataset or photo"
          >
            <Paperclip size={18} />
          </button>

          {/* Camera Button */}
          {onToggleCamera && (
            <button
              className={`composer-action-btn ${cameraConnected ? 'camera-live' : ''}`}
              onClick={onToggleCamera}
              title="Toggle live camera stream"
            >
              <Camera size={18} />
            </button>
          )}

          {/* Auto-expanding Input Area */}
          <textarea
            ref={textareaRef}
            className="composer-input"
            rows={1}
            value={inputText}
            onChange={handleTextareaChange}
            onKeyDown={handleKeyDown}
            onPaste={handlePaste}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            placeholder="Ask Saar anything about the evidence, upload datasets, paste screenshots (Ctrl+V), or simulate interventions..."
          />

          {/* Send Button */}
          <button
            className="composer-send-arrow"
            onClick={handleSend}
            disabled={isProcessing || (!inputText.trim() && attachedFiles.length === 0)}
            title="Send message"
          >
            <ArrowUp size={17} />
          </button>
        </div>

        <div className="composer-footer-note">
          Saar couples visual perception with Bayesian belief updating. Verify critical scientific findings.
        </div>
      </div>

      {/* Floating Ask Saar Selection Popover (ChatGPT style) */}
      {selectionPopover && (
        <div
          className="floating-ask-saar-popover"
          style={{ top: `${selectionPopover.top}px`, left: `${selectionPopover.left}px` }}
        >
          <button
            className="ask-saar-pill-btn"
            onClick={handleAskSaarFromSelection}
            title="Ask Saar about this selection"
          >
            <Sparkles size={13} className="text-sky" />
            <span>Ask Saar</span>
          </button>
          <button
            className="ask-saar-copy-btn"
            onClick={handleCopySelection}
            title="Copy selected text"
          >
            {copiedSelection ? <Check size={12} color="#10b981" /> : <Copy size={12} />}
            <span>{copiedSelection ? 'Copied' : 'Copy'}</span>
          </button>
        </div>
      )}

      {/* Interactive Scientific Terminology Popover Modal */}
      {activeTermModal && (
        <div className="term-modal-backdrop" onClick={() => setActiveTermModal(null)}>
          <div className="term-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="term-modal-header">
              <div className="term-modal-title-group">
                <span className="term-modal-domain-tag">{activeTermModal.domain || 'Scientific Concept'}</span>
                <h3 className="term-modal-title">{activeTermModal.term}</h3>
                {activeTermModal.phonetic && (
                  <span className="term-modal-phonetic">{activeTermModal.phonetic}</span>
                )}
              </div>
              <button
                type="button"
                className="term-modal-close-btn"
                onClick={() => setActiveTermModal(null)}
                title="Close definition modal"
              >
                <X size={16} />
              </button>
            </div>

            <div className="term-modal-body">
              <div className="term-modal-section">
                <div className="term-section-label">Academic Lexical Definition</div>
                <p className="term-modal-def">{activeTermModal.definition}</p>
              </div>

              {activeTermModal.investigation_context && (
                <div className="term-modal-section">
                  <div className="term-section-label">Context in Active Investigation</div>
                  <p className="term-modal-context">{activeTermModal.investigation_context}</p>
                </div>
              )}

              {activeTermModal.diagnostic_indicator && (
                <div className="term-modal-section">
                  <div className="term-section-label">Diagnostic Sensor Indicator</div>
                  <p className="term-modal-indicator">{activeTermModal.diagnostic_indicator}</p>
                </div>
              )}

              {activeTermModal.related_nodes && activeTermModal.related_nodes.length > 0 && (
                <div className="term-modal-section">
                  <div className="term-section-label">Related Causal Nodes</div>
                  <div className="term-related-pills">
                    {activeTermModal.related_nodes.map((n, nIdx) => (
                      <span key={nIdx} className="related-node-pill">{n}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="term-modal-footer">
              <button
                type="button"
                className="btn-deep-dive-saar"
                onClick={() => {
                  const q = `Explain the causal mechanism, underlying scientific equations, and literature consensus for "${activeTermModal.term}" in ${activeTermModal.domain || 'science'}:`;
                  setInputText(q);
                  setActiveTermModal(null);
                  if (textareaRef.current) {
                    textareaRef.current.focus();
                  }
                }}
              >
                <Sparkles size={14} className="text-purple" />
                <span>Ask SAAR to Deep-Dive on {activeTermModal.term}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
