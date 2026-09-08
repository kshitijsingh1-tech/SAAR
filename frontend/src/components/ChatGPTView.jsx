import React, { useState, useRef, useEffect } from 'react';
import {
  Sparkles, ArrowUp, Paperclip, Camera, FileText,
  X, Loader2, GitFork, BarChart2, ShieldCheck, Sliders,
  BookOpen, ChevronDown, PanelLeft, AlertTriangle,
  CornerDownRight, CheckCircle2, ArrowRight, ExternalLink,
  HelpCircle
} from 'lucide-react';
import { MarkdownResponse } from './MarkdownResponse';
import { ToolRolloutBar } from './ToolRolloutBar';

export function ChatGPTView({
  messages,
  isProcessing,
  onSendMessage,
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
  theme = 'light'
}) {
  const [inputText, setInputText] = useState('');
  const [attachedFiles, setAttachedFiles] = useState([]);
  const [answeringQId, setAnsweringQId] = useState(null);
  const [customAnswerText, setCustomAnswerText] = useState('');

  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  const saarLogoSrc = '/saar-logo-dark.png';
  const saarWordmarkSrc = '/saar-wordmark-dark.png';

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isProcessing]);

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
                  onClick={() => onSendMessage('Investigate the 30-day tomato crop failure dataset and isolate the root cause of leaf chlorosis.')}
                >
                  <div className="prompt-title">Tomato Crop 30-Day Failure</div>
                  <div className="prompt-desc">Isolate soil moisture, alkalinity surge, and iron uptake block.</div>
                </button>

                <button
                  className="prompt-card"
                  onClick={() => onSendMessage('Analyze highway pavement surface cracking and sub-surface GPR cavity void reflections.')}
                >
                  <div className="prompt-title">Highway Pavement Cavity Void</div>
                  <div className="prompt-desc">Correlate surface alligator cracks with 1.8m sub-base GPR radar void.</div>
                </button>

                <button
                  className="prompt-card"
                  onClick={() => onSendMessage('Evaluate exoplanet transit depth lightcurve against stellar flare noise contamination.')}
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
            messages.map((msg, index) => (
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
                      <MarkdownResponse content={msg.text} />
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
                          <span>Telemetry &amp; Trend Analytics</span>
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
                          <span>Literature RAG Index</span>
                          <ArrowRight size={12} className="badge-arrow" />
                        </button>

                        <button
                          className="tool-invoke-badge badge-benchmark"
                          onClick={() => onOpenTool('benchmark')}
                        >
                          <GitCompare size={14} className="text-emerald" />
                          <span>VLM vs. Saar Benchmark</span>
                          <ArrowRight size={12} className="badge-arrow" />
                        </button>
                      </div>
                    )}

                    {/* Interactive Human-in-the-Loop Inquiry Cards */}
                    {msg.openQuestions && msg.openQuestions.length > 0 && (
                      <div className="chat-inquiry-box">
                        <div className="inquiry-box-title">
                          <AlertTriangle size={14} className="text-amber" />
                          <span>Uncertainty Reduction Inquiries</span>
                        </div>

                        {msg.openQuestions.map((q, qIdx) => (
                          <div key={q.id || qIdx} className="inquiry-item">
                            <p className="inquiry-prompt">{q.text || q}</p>
                            {q.impact && <div className="inquiry-impact">Impact: {q.impact}</div>}

                            <div className="inquiry-quick-answers">
                              <button
                                className="quick-answer-pill"
                                onClick={() => onAnswerInquiry(q.id || qIdx, 'Yes, precipitation exceeded 40mm during Days 12-16.')}
                              >
                                Yes, exceeded 40mm
                              </button>
                              <button
                                className="quick-answer-pill"
                                onClick={() => onAnswerInquiry(q.id || qIdx, 'No, drainage prevented soil saturation.')}
                              >
                                No, held below 25mm
                              </button>
                            </div>

                            <div className="inquiry-custom-input-line">
                              <input
                                type="text"
                                placeholder="Or enter field observation..."
                                value={answeringQId === (q.id || qIdx) ? customAnswerText : ''}
                                onChange={(e) => {
                                  setAnsweringQId(q.id || qIdx);
                                  setCustomAnswerText(e.target.value);
                                }}
                                onKeyDown={(e) => {
                                  if (e.key === 'Enter' && customAnswerText.trim()) {
                                    onAnswerInquiry(q.id || qIdx, customAnswerText.trim());
                                    setCustomAnswerText('');
                                  }
                                }}
                              />
                              <button
                                className="submit-inquiry-btn"
                                onClick={() => {
                                  if (customAnswerText.trim()) {
                                    onAnswerInquiry(q.id || qIdx, customAnswerText.trim());
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
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}

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
                <FileText size={12} />
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

        <div className="composer-capsule">
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
            placeholder="Ask Saar anything about the evidence, upload datasets, or simulate interventions..."
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
    </div>
  );
}
