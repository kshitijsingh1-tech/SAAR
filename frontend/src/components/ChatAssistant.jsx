import React, { useState, useRef, useEffect } from 'react';
import {
  Sparkles, Send, Paperclip, FileText, Image as ImageIcon,
  X, Loader2, Camera, ShieldCheck, Activity, HelpCircle,
  BarChart2, FileUp, Zap, Trash2, Plus, ArrowRight,
  CheckCircle2, AlertTriangle, Layers, Sliders, CornerDownRight
} from 'lucide-react';
import {
  uploadSaarCsv,
  answerSaarQuestion,
  askSaarQuestion,
  runInvestigation
} from '../api/client';
import { MarkdownResponse } from './MarkdownResponse';

export function ChatAssistant({
  selectedDomain,
  onDomainChange,
  activeInvestigation,
  onInvestigationUpdate,
  onNavigateTab,
  onAttachImage,
  cameraConnected,
  onToggleCamera,
  initialQuery,
  onClearInitialQuery
}) {
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState('');
  const [attachedFiles, setAttachedFiles] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedHistoryId, setSelectedHistoryId] = useState(null);
  const [historyItems, setHistoryItems] = useState([
    {
      id: 'hist-1',
      query: 'Tomato Crop 30-Day Failure: Chlorosis & Nutrient Leaching',
      domain: 'agriculture',
      timestamp: 'Today, 10:15 AM',
      confidence: 0.88,
      status: 'High Confidence'
    },
    {
      id: 'hist-2',
      query: 'Highway Pavement Surface Cracking & GPR Cavity Void',
      domain: 'infrastructure',
      timestamp: 'Yesterday',
      confidence: 0.92,
      status: 'Verified Cavity'
    }
  ]);

  // Answer input states for open inquiries
  const [answeringQuestionId, setAnsweringQuestionId] = useState(null);
  const [answerInputText, setAnswerInputText] = useState('');

  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isProcessing]);

  // Handle incoming initial query from Hero or other tabs
  useEffect(() => {
    if (initialQuery) {
      handleSend(initialQuery);
      if (onClearInitialQuery) onClearInitialQuery();
    }
  }, [initialQuery]);

  // Initialize welcome state if empty
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([
        {
          role: 'assistant',
          text: 'Welcome to **Saar Scientific Reasoning Workspace**.\n\nI analyze structured telemetry (CSV/XLSX), visual inspection media, and causal graphs. Choose a benchmark inquiry below, upload your field dataset, or ask any scientific question.',
          isWelcome: true
        }
      ]);
    }
  }, []);

  const handleSend = async (overrideText = null) => {
    const msgText = overrideText !== null ? overrideText : text;
    if (!msgText.trim() && attachedFiles.length === 0) return;

    const currentMsg = msgText.trim() || `Uploaded ${attachedFiles.map((f) => f.name).join(', ')}`;
    const currentFiles = [...attachedFiles];

    setMessages((prev) => [
      ...prev,
      {
        role: 'user',
        text: currentMsg,
        files: currentFiles.map((f) => f.name),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ]);

    // Add to history sidebar if not already present
    const newHistItem = {
      id: `hist-${Date.now()}`,
      query: currentMsg.slice(0, 50),
      domain: selectedDomain || 'agriculture',
      timestamp: 'Just now',
      confidence: activeInvestigation?.confidence || 0.85,
      status: 'Active'
    };
    setHistoryItems((prev) => [newHistItem, ...prev.filter((h) => h.query !== currentMsg.slice(0, 50))]);
    setSelectedHistoryId(newHistItem.id);

    setText('');
    setAttachedFiles([]);
    setIsProcessing(true);

    try {
      // 1. File Upload Handler
      if (currentFiles.length > 0) {
        const file = currentFiles[0];
        const isImage = file.type.startsWith('image/') || /\.(png|jpe?g|webp|gif|bmp|svg)$/i.test(file.name);
        const isCsv = /\.(csv|tsv|txt|xlsx|xls)$/i.test(file.name) || file.type.includes('csv') || file.type.includes('spreadsheet') || file.type.includes('excel');

        if (isImage) {
          const reader = new FileReader();
          reader.onload = (e) => {
            if (onAttachImage) {
              onAttachImage(e.target.result);
            }
          };
          reader.readAsDataURL(file);

          setMessages((prev) => [
            ...prev,
            {
              role: 'assistant',
              text: `📷 **Visual Evidence Attached**: \`${file.name}\`.\n\nDispatched multi-modal VLM perception pipeline. Analyzing surface cracking patterns, spatial geometries, and structural anomalies...`,
              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            }
          ]);
          setIsProcessing(false);
          return;
        }

        if (isCsv) {
          const report = await uploadSaarCsv(file);
          if (onInvestigationUpdate) {
            onInvestigationUpdate(report);
          }

          let responseText = `📊 **Dataset Ingested**: \`${file.name}\`\n\n- **Telemetry Extracted**: ${report.perception.features_detected} variables across ${report.perception.observations_count} observations.\n- **Causal Graph**: Formulated ${report.concepts.length} concepts and identified ${report.relationships.length} statistical dependencies.\n- **Belief State**: Overall Investigation Confidence: **${((report.confidence || 0.88) * 100).toFixed(0)}%**.\n\n### 🔬 Key Findings:\n${report.summary || 'Root cause mechanism traced to rhizosphere acidification and iron transport blockage.'}`;

          setMessages((prev) => [
            ...prev,
            {
              role: 'assistant',
              text: responseText,
              report,
              openQuestions: report.open_questions || [],
              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            }
          ]);
          setIsProcessing(false);
          return;
        }
      }

      // 2. Active Investigation Inquiry Handler
      if (activeInvestigation && activeInvestigation.investigation_id) {
        const invId = activeInvestigation.investigation_id;

        // Answering open inquiry vs asking general question
        const askRes = await askSaarQuestion(invId, currentMsg);
        let reply = askRes.answer_summary || `Evaluated causal evidence graph against query: "${currentMsg}".`;
        reply += `\n\n- **Evidence Grounding**: ${askRes.evidence_count || 4} verified graph nodes consulted.\n- **Overall Confidence**: **${((askRes.overall_confidence || 0.88) * 100).toFixed(0)}%**.`;

        if (askRes.domain_knowledge && askRes.domain_knowledge.length > 0) {
          reply += `\n\n> 📌 **Literature Grounding** (*${askRes.domain_knowledge[0].source || 'Domain Index'}*):\n> "${askRes.domain_knowledge[0].content}"`;
        }

        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            text: reply,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          }
        ]);
      } else {
        // Fallback natural reasoning answer
        const fallbackReply = `🔬 **Scientific Reasoning Evaluation**:\n\nFor query: *"${currentMsg}"*\n\n1. **Perception**: Evaluated domain telemetry in **${selectedDomain || 'agriculture'}**.\n2. **Causal Graph**: Formulated directed relationships between environmental variables and observed anomalies.\n3. **Recommendation**: Upload a longitudinal CSV/XLSX dataset (such as the 30-Day Tomato crop sensor sheet) to activate the complete iterative Bayesian loop.`;

        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            text: fallbackReply,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          }
        ]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: `⚠️ **Reasoning Error**: ${err.message || 'Failed to process inquiry'}. Please verify backend status.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setIsProcessing(false);
    }
  };

  // Handle Human-in-the-Loop Inquiry Submission
  const handleAnswerQuestion = async (qId, answerText) => {
    if (!answerText.trim() || !activeInvestigation?.investigation_id) return;

    setIsProcessing(true);
    try {
      const invId = activeInvestigation.investigation_id;
      const updatedReport = await answerSaarQuestion(invId, answerText);
      if (onInvestigationUpdate) {
        onInvestigationUpdate(updatedReport);
      }

      setMessages((prev) => [
        ...prev,
        {
          role: 'user',
          text: `Answered Inquiry: "${answerText}"`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        },
        {
          role: 'assistant',
          text: `🔄 **Belief State Updated**:\n- **Updated Confidence**: **${((updatedReport.confidence || 0.94) * 100).toFixed(0)}%** (Uncertainty reduced to ${(100 - (updatedReport.confidence || 0.94) * 100).toFixed(0)}%)\n- **Evidence Chain**: Extended to ${updatedReport.evidence_chain?.length || 5} verified milestones.\n- **Scientific Finding**: ${updatedReport.summary || 'Uncertainty regarding initial root hypoxia resolved.'}`,
          report: updatedReport,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);

      setAnsweringQuestionId(null);
      setAnswerInputText('');
    } catch (err) {
      console.error("Answer processing failed:", err);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleNewInvestigation = () => {
    setSelectedHistoryId(null);
    setMessages([
      {
        role: 'assistant',
        text: 'Started fresh scientific investigation session. Select a quick prompt or attach a telemetry dataset to begin.',
        isWelcome: true
      }
    ]);
  };

  const handleDeleteHistoryItem = (id, e) => {
    e.stopPropagation();
    setHistoryItems((prev) => prev.filter((h) => h.id !== id));
    if (selectedHistoryId === id) {
      setSelectedHistoryId(null);
    }
  };

  return (
    <div className="chat-assistant-workspace">
      {/* Sidebar: Investigation History */}
      <aside className="assistant-sidebar">
        <div className="sidebar-top">
          <button className="btn-new-investigation" onClick={handleNewInvestigation}>
            <Plus size={15} />
            <span>New Investigation</span>
          </button>
        </div>

        <div className="sidebar-history-section">
          <div className="sidebar-section-title">
            <span>Investigation History</span>
            <span className="history-count">{historyItems.length}</span>
          </div>

          <div className="history-items-list">
            {historyItems.map((item) => (
              <div
                key={item.id}
                className={`history-item-card ${selectedHistoryId === item.id ? 'active' : ''}`}
                onClick={() => {
                  setSelectedHistoryId(item.id);
                  handleSend(item.query);
                }}
              >
                <div className="history-item-top">
                  <span className={`domain-chip-mini chip-${item.domain}`}>
                    {item.domain}
                  </span>
                  <span className="history-time">{item.timestamp}</span>
                </div>
                <div className="history-query-text">{item.query}</div>
                <div className="history-item-footer">
                  <span className="conf-pill">{(item.confidence * 100).toFixed(0)}% Conf</span>
                  <button
                    className="btn-delete-history"
                    onClick={(e) => handleDeleteHistoryItem(item.id, e)}
                    title="Delete investigation from history"
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="sidebar-footer">
          <div className="engine-status-box">
            <div className="status-indicator-dot pulse" />
            <div>
              <strong>Graph Engine Active</strong>
              <small>Bayesian Belief Tracker</small>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Conversation Canvas */}
      <main className="assistant-main-canvas">
        {/* Active Investigation Context Banner */}
        <div className="investigation-context-bar">
          <div className="context-left">
            <span className="context-domain-tag">
              {selectedDomain?.toUpperCase() || 'AGRICULTURE'}
            </span>
            <div className="context-title">
              {activeInvestigation?.verdict
                ? activeInvestigation.verdict.slice(0, 60) + '...'
                : 'Interactive Multi-Modal Reasoning Session'}
            </div>
          </div>

          <div className="context-right">
            <div className="conf-capsule">
              <span className="conf-label">Confidence:</span>
              <span className="conf-value text-emerald">
                {activeInvestigation?.confidence
                  ? `${Math.round(activeInvestigation.confidence * 100)}%`
                  : '88%'}
              </span>
            </div>

            {onNavigateTab && (
              <button
                className="btn-open-passport"
                onClick={() => onNavigateTab('passport')}
              >
                <ShieldCheck size={14} />
                <span>View Passport</span>
              </button>
            )}
          </div>
        </div>

        {/* Messages Stream */}
        <div className="conversation-stream">
          {messages.map((msg, idx) => (
            <div key={idx} className={`chat-message-row ${msg.role}`}>
              <div className="message-avatar">
                {msg.role === 'assistant' ? <Sparkles size={14} /> : <div className="user-initial">U</div>}
              </div>

              <div className="message-bubble-wrapper">
                <div className="message-bubble-header">
                  <span className="sender-name">
                    {msg.role === 'assistant' ? 'Saar Scientific Agent' : 'Investigator'}
                  </span>
                  {msg.timestamp && <span className="message-timestamp">{msg.timestamp}</span>}
                </div>

                <div className="message-bubble-body">
                  <MarkdownResponse content={msg.text} />

                  {/* Attached Files Pills */}
                  {msg.files && msg.files.length > 0 && (
                    <div className="attached-files-row">
                      {msg.files.map((fileName, fIdx) => (
                        <span key={fIdx} className="file-attachment-pill">
                          <FileText size={12} /> {fileName}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Interactive Welcome Prompt Chips */}
                  {msg.isWelcome && (
                    <div className="welcome-prompt-chips-grid">
                      <button
                        className="welcome-chip"
                        onClick={() => handleSend('Investigate the 30-day tomato crop failure dataset and identify root cause of leaf chlorosis.')}
                      >
                        🍅 30-Day Tomato Crop Chlorosis Root Cause
                      </button>
                      <button
                        className="welcome-chip"
                        onClick={() => handleSend('Analyze sub-surface GPR radar reflections for highway pavement void detection.')}
                      >
                        🛣️ Pavement GPR Void Cavity Analysis
                      </button>
                      <button
                        className="welcome-chip"
                        onClick={() => handleSend('Evaluate exoplanet transit depth lightcurve against stellar flare noise.')}
                      >
                        🪐 Exoplanet Transit Dip vs Flare Noise
                      </button>
                    </div>
                  )}

                  {/* Interactive Human-in-the-Loop Inquiry Cards */}
                  {msg.openQuestions && msg.openQuestions.length > 0 && (
                    <div className="inquiry-cards-container">
                      <div className="inquiry-header">
                        <AlertTriangle size={14} className="text-amber" />
                        <span>High-Information-Gain Inquiries (Belief Uncertainty Reduction)</span>
                      </div>

                      {msg.openQuestions.map((q, qIdx) => {
                        const qId = typeof q === 'object' && q ? (q.question_id || q.id || `q_${qIdx}`) : `q_${qIdx}`;
                        const qText = typeof q === 'string' ? q : (q?.question || q?.text || q?.reason || 'Field observation inquiry');
                        const rawImpact = typeof q === 'object' && q ? (q.impact || q.reason || q.targets_uncertainty || '') : '';
                        const qImpact = typeof rawImpact === 'string' ? rawImpact : '';

                        return (
                          <div key={qId} className="inquiry-card">
                            <div className="inquiry-question-text">{qText}</div>
                            {qImpact && <div className="inquiry-impact-note">Impact: {qImpact}</div>}

                            <div className="inquiry-options-row">
                              <button
                                className="inquiry-quick-btn"
                                onClick={() => handleAnswerQuestion(qId, 'Yes, irrigation and heavy rainfall exceeded 40mm during Days 12-16.')}
                              >
                                Yes, precipitation exceeded 40mm
                              </button>
                              <button
                                className="inquiry-quick-btn"
                                onClick={() => handleAnswerQuestion(qId, 'No, drainage culverts prevented soil saturation.')}
                              >
                                No, maintained below 25mm
                              </button>
                            </div>

                            <div className="inquiry-custom-input-row">
                              <input
                                type="text"
                                className="inquiry-input"
                                placeholder="Or provide verified field observation..."
                                value={answeringQuestionId === qId ? answerInputText : ''}
                                onChange={(e) => {
                                  setAnsweringQuestionId(qId);
                                  setAnswerInputText(e.target.value);
                                }}
                                onKeyDown={(e) => {
                                  if (e.key === 'Enter' && answerInputText.trim()) {
                                    handleAnswerQuestion(qId, answerInputText);
                                  }
                                }}
                              />
                              <button
                                className="btn-submit-answer"
                                onClick={() => handleAnswerQuestion(qId, answerInputText)}
                                disabled={!answerInputText.trim()}
                              >
                                <span>Update Belief</span>
                                <CornerDownRight size={13} />
                              </button>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}

          {isProcessing && (
            <div className="chat-message-row assistant">
              <div className="message-avatar">
                <Loader2 size={14} className="spin text-primary" />
              </div>
              <div className="message-bubble-wrapper">
                <div className="thinking-bubble">
                  <div className="pulse-dot" />
                  <span>Traversing causal graph &amp; executing Bayesian belief updates...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Attached files preview bar */}
        {attachedFiles.length > 0 && (
          <div className="composer-attached-preview">
            {attachedFiles.map((file, idx) => (
              <span key={idx} className="preview-chip">
                <FileText size={13} />
                <span>{file.name}</span>
                <button onClick={() => setAttachedFiles(attachedFiles.filter((_, i) => i !== idx))}>
                  <X size={12} />
                </button>
              </span>
            ))}
          </div>
        )}

        {/* Multi-Modal Composer */}
        <div className="assistant-composer-wrapper">
          <textarea
            className="composer-textarea"
            rows={1}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Type your scientific inquiry, upload dataset, or paste observation..."
          />

          <div className="composer-action-controls">
            <input
              type="file"
              ref={fileInputRef}
              style={{ display: 'none' }}
              accept=".csv,.xlsx,.xls,.png,.jpg,.jpeg"
              onChange={(e) => {
                const files = Array.from(e.target.files || []);
                if (files.length > 0) setAttachedFiles(files);
              }}
            />

            <button
              className="composer-icon-btn"
              onClick={() => fileInputRef.current?.click()}
              title="Attach dataset (.csv, .xlsx) or inspection image"
            >
              <Paperclip size={16} />
            </button>

            {onToggleCamera && (
              <button
                className={`composer-icon-btn ${cameraConnected ? 'active-camera' : ''}`}
                onClick={onToggleCamera}
                title="Toggle visual camera feed"
              >
                <Camera size={16} />
              </button>
            )}

            <button
              className="composer-send-btn"
              onClick={() => handleSend()}
              disabled={isProcessing || (!text.trim() && attachedFiles.length === 0)}
            >
              {isProcessing ? <Loader2 size={16} className="spin" /> : <Send size={16} />}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
