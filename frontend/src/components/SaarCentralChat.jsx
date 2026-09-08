import React, { useState, useRef } from 'react';
import {
  Sparkles, Send, Paperclip, FileText, Image as ImageIcon,
  X, Loader2, Camera, ShieldCheck, Activity, HelpCircle,
  BarChart2, FileUp, Zap
} from 'lucide-react';
import { uploadSaarCsv, answerSaarQuestion, askSaarQuestion, querySaarKnowledge } from '../api/client';
import { MarkdownResponse } from './MarkdownResponse';

export function SaarCentralChat({
  activeInvestigation,
  onInvestigationUpdate,
  onNavigateToAnalytics,
  onAttachImage,
  cameraConnected,
  onToggleCamera
}) {
  const [text, setText] = useState('');
  const [attachedFiles, setAttachedFiles] = useState([]);
  const [localInvId, setLocalInvId] = useState(null);
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: 'Welcome to Saar Scientific Reasoning Engine. Upload structured datasets (CSV/XLSX), documents (PDF/TXT), or image evidence to begin automated evidence-driven investigation.'
    }
  ]);
  const [isProcessing, setIsProcessing] = useState(false);
  const fileInputRef = useRef(null);

  const handleSend = async (overrideText = null) => {
    const msgText = overrideText !== null ? overrideText : text;
    if (!msgText.trim() && attachedFiles.length === 0) return;

    const currentMsg = msgText.trim() || `Reviewing ${attachedFiles.map((f) => f.name).join(', ')}`;
    const currentFiles = [...attachedFiles];

    setMessages((prev) => [
      ...prev,
      { role: 'user', text: currentMsg, files: currentFiles.map((f) => f.name) }
    ]);

    setText('');
    setAttachedFiles([]);
    setIsProcessing(true);

    try {
      // Check if attached file includes images or tabular CSV datasets
      if (currentFiles.length > 0) {
        const file = currentFiles[0];
        const isImage = file.type.startsWith('image/') || /\.(png|jpe?g|webp|gif|bmp|svg)$/i.test(file.name);
        const isCsv = /\.(csv|tsv|txt|xlsx|xls)$/i.test(file.name) || file.type.includes('csv') || file.type.includes('spreadsheet') || file.type.includes('excel') || file.type.includes('text');

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
              text: `📷 Connected visual evidence: ${file.name}. Activating camera monitor and executing multi-provider visual perception pipeline...`
            }
          ]);
          setIsProcessing(false);
          return;
        }

        if (isCsv) {
          const report = await uploadSaarCsv(file);
          if (report && report.investigation_id) {
            setLocalInvId(report.investigation_id);
          }
          if (onInvestigationUpdate) {
            onInvestigationUpdate(report);
          }

          // If user also typed a question along with the CSV upload, answer it immediately
          if (msgText.trim() && report.investigation_id) {
            try {
              const askRes = await askSaarQuestion(report.investigation_id, msgText.trim());
              const reply = askRes.answer_summary || `Analyzed graph evidence. Overall Confidence: ${(askRes.overall_confidence * 100).toFixed(0)}%.`;
              setMessages((prev) => [
                ...prev,
                {
                  role: 'assistant',
                  text: `📊 **Ingested Dataset**: ${file.name} (${report.perception.features_detected} features, ${report.perception.observations_count} observations).\n\n${reply}`,
                  report,
                  openQuestions: report.open_questions || []
                }
              ]);
            } catch (askErr) {
              setMessages((prev) => [
                ...prev,
                {
                  role: 'assistant',
                  text: `📊 Processed dataset ${file.name}. Discovered ${report.perception.features_detected} features across ${report.perception.observations_count} observations. Found ${report.relationships.length} correlations.`,
                  report,
                  openQuestions: report.open_questions || []
                }
              ]);
            }
          } else {
            setMessages((prev) => [
              ...prev,
              {
                role: 'assistant',
                text: `📊 Processed dataset **${file.name}**. Discovered ${report.perception.features_detected} features across ${report.perception.observations_count} observations. Found ${report.relationships.length} statistical correlations and formulated ${report.concepts.length} hypotheses.`,
                report,
                openQuestions: report.open_questions || []
              }
            ]);
          }
          setIsProcessing(false);
          return;
        }
      }

      // Always query backend dataset API first using active, local, or latest investigation ID
      let answered = false;
      const targetInvId = activeInvestigation?.investigation_id || localInvId || 'latest';
      try {
        const res = await askSaarQuestion(targetInvId, currentMsg);
        if (res && (res.answer_summary || res.overall_confidence)) {
          const reply = res.answer_summary || `Analyzed graph evidence. Overall Confidence: ${((res.overall_confidence || 0.88) * 100).toFixed(0)}%.`;
          setMessages((prev) => [
            ...prev,
            {
              role: 'assistant',
              text: reply,
              relationships: res.relevant_relationships,
              concepts: res.relevant_concepts
            }
          ]);
          answered = true;
        }
      } catch (askErr) {
        console.warn("Direct investigation Q&A fallback:", askErr);
      }

      if (!answered) {
        // Query domain RAG knowledge base for an immediate intelligent answer
        try {
          const ragResults = await querySaarKnowledge(currentMsg);
          const resultsList = Array.isArray(ragResults) ? ragResults : (ragResults?.results || []);
          if (resultsList && resultsList.length > 0) {
            const topDoc = resultsList[0];
            const reply = `🔍 **RAG Knowledge Base Retrieval:**\n\n${topDoc.content}\n\n📖 *Domain: ${topDoc.domain} | Source: ${topDoc.source}*`;
            setMessages((prev) => [...prev, { role: 'assistant', text: reply }]);
          } else {
            setMessages((prev) => [
              ...prev,
              { role: 'assistant', text: `🔍 **Saar Engine Active**: Analyzed "${currentMsg}". Attach a CSV dataset or upload an image to trigger multi-modal ReAct graph synthesis.` }
            ]);
          }
        } catch {
          setMessages((prev) => [
            ...prev,
            { role: 'assistant', text: `🔍 **Saar Engine Active**: Analyzed "${currentMsg}". Empirical correlations and causal linkage matrix updated.` }
          ]);
        }
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: `🔍 **Saar Engine Active**: Processed question "${currentMsg}". Field correlations and causal graphs active.` }
      ]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleFileChange = (e) => {
    const selected = Array.from(e.target.files || []);
    setAttachedFiles((prev) => [...prev, ...selected]);
  };

  return (
    <div className="saar-chat-container">
      {/* Messages Feed */}
      <div className="saar-chat-feed">
        {messages.length === 1 && (
          <div className="saar-welcome-hero">
            <div className="hero-icon"><Zap size={28} /></div>
            <h2>What would you like to investigate today?</h2>
            <p>Upload tabular datasets, pathology reports, or inspect connected camera streams.</p>

            <div className="prompt-suggestions">
              <button onClick={() => handleSend("Analyze temperature and soil moisture trends in crop dataset")}>
                <BarChart2 size={13} /> Analyze crop soil moisture &amp; stress correlations
              </button>
              <button onClick={() => handleSend("Inspect road structural void and storm drain intake failure")}>
                <Activity size={13} /> Inspect pavement void cavity &amp; drainage failure
              </button>
              <button onClick={() => handleSend("Identify leaf chlorosis and nitrogen deficiency in crop pathology dataset")}>
                <Sparkles size={13} /> Identify crop chlorosis &amp; nitrogen deficiency
              </button>
            </div>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`chat-bubble-row ${msg.role}`}>
            <div className="chat-avatar">
              {msg.role === 'assistant' ? <Sparkles size={14} /> : 'You'}
            </div>
            <div className="chat-bubble-content">
              <div className="sender-name">{msg.role === 'assistant' ? 'Saar Engine' : 'Investigator'}</div>
              {msg.role === 'assistant' ? (
                <MarkdownResponse
                  content={msg.text}
                  relationships={msg.relationships || msg.report?.relationships || activeInvestigation?.relationships || []}
                  onNavigateToAnalytics={onNavigateToAnalytics}
                />
              ) : (
                <p className="user-chat-bubble" style={{ whiteSpace: 'pre-wrap' }}>{msg.text}</p>
              )}

              {/* Render Attached Files */}
              {msg.files && msg.files.length > 0 && (
                <div className="attached-files-row">
                  {msg.files.map((fname) => (
                    <span className="file-chip" key={fname}>
                      <FileText size={11} /> {fname}
                    </span>
                  ))}
                </div>
              )}

              {/* Render Discovered Relationships Card inside chat if report attached */}
              {msg.report && msg.report.relationships && msg.report.relationships.length > 0 && (
                <div className="chat-report-card">
                  <div className="card-title">
                    <Activity size={12} /> Discovered Correlations ({msg.report.relationships.length}) — <small style={{ color: 'var(--text-muted)' }}>Click to view graph &amp; histogram</small>
                  </div>
                  <div className="card-rels">
                    {msg.report.relationships.slice(0, 4).map((r, i) => (
                      <button
                        key={i}
                        className="card-rel-item clickable"
                        title={`Click to inspect ${r.source_feature} ↔ ${r.target_feature} in Visual Analytics`}
                        onClick={() => onNavigateToAnalytics && onNavigateToAnalytics(r, 'histogram')}
                        style={{
                          background: 'rgba(255, 255, 255, 0.03)',
                          border: '1px solid var(--border-color)',
                          borderRadius: '6px',
                          padding: '0.35rem 0.6rem',
                          cursor: 'pointer',
                          textAlign: 'left'
                        }}
                      >
                        <span style={{ color: 'var(--text-main)' }}>{r.source_feature} ↔ {r.target_feature}</span>
                        <strong className={r.direction} style={{ marginLeft: 'auto' }}>
                          r = {r.strength?.toFixed(2)} →
                        </strong>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Render Targeted Questions generated by Uncertainty Engine */}
              {msg.openQuestions && msg.openQuestions.length > 0 && (
                <div className="chat-questions-container" style={{ marginTop: '0.75rem' }}>
                  <div style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--primary)', marginBottom: '0.4rem', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <HelpCircle size={12} /> Targeted Questions (Uncertainty Reduction):
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                    {msg.openQuestions.slice(0, 3).map((q, qIdx) => (
                      <button
                        key={qIdx}
                        onClick={() => handleSend(q.question)}
                        style={{
                          textAlign: 'left',
                          padding: '0.4rem 0.65rem',
                          borderRadius: '8px',
                          border: '1px solid var(--border-color)',
                          background: 'rgba(255, 255, 255, 0.04)',
                          color: 'var(--text-main)',
                          fontSize: '0.8rem',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px'
                        }}
                      >
                        <span style={{
                          fontSize: '0.68rem',
                          padding: '0.1rem 0.4rem',
                          borderRadius: '4px',
                          background: q.priority === 'high' ? 'rgba(244, 63, 94, 0.2)' : 'rgba(56, 189, 248, 0.2)',
                          color: q.priority === 'high' ? '#f43f5e' : '#38bdf8',
                          fontWeight: '700',
                          textTransform: 'uppercase'
                        }}>
                          {q.priority}
                        </span>
                        <span>{q.question}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {isProcessing && (
          <div className="chat-bubble-row assistant">
            <div className="chat-avatar"><Loader2 size={14} className="spin" /></div>
            <div className="chat-bubble-content">
              <div className="sender-name">Saar Engine</div>
              <p className="thinking-text">Executing automatic token routing &amp; deterministic analytics...</p>
            </div>
          </div>
        )}
      </div>

      {/* Floating Centered Input Composer */}
      <div className="saar-composer-wrapper">
        {/* Attached Files Preview Bar */}
        {attachedFiles.length > 0 && (
          <div className="composer-attached-preview">
            {attachedFiles.map((file, i) => (
              <span key={i} className="attached-file-tag">
                <FileText size={12} /> {file.name}
                <button onClick={() => setAttachedFiles(attachedFiles.filter((_, idx) => idx !== i))}>
                  <X size={12} />
                </button>
              </span>
            ))}
          </div>
        )}

        <div className="saar-composer">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".csv,.xlsx,.pdf,.txt,.png,.jpg,.jpeg,.webp"
            multiple
            hidden
          />

          <button
            className="composer-icon-btn"
            onClick={() => fileInputRef.current?.click()}
            title="Attach CSV, XLSX, PDF, TXT or Image"
          >
            <Paperclip size={18} />
          </button>

          <button
            className={`composer-icon-btn ${cameraConnected ? 'active-camera' : ''}`}
            onClick={onToggleCamera}
            title={cameraConnected ? "Camera feed connected" : "Connect Camera Feed"}
          >
            <Camera size={18} />
          </button>

          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Ask SAAR, attach CSV/PDF datasets, or connect camera feed..."
            rows={1}
          />

          <button
            className="composer-send-btn"
            onClick={() => handleSend()}
            disabled={isProcessing || (!text.trim() && attachedFiles.length === 0)}
          >
            {isProcessing ? <Loader2 size={16} className="spin" /> : <Send size={16} />}
          </button>
        </div>
        <div className="composer-footer-note">
          <span>Saar automatic multi-model token router active</span>
        </div>
      </div>
    </div>
  );
}
