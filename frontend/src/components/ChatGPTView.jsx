import React, { useState, useRef, useEffect } from 'react';
import {
  Sparkles, ArrowUp, Paperclip, Camera, FileText,
  X, Loader2, GitFork, BarChart2, ShieldCheck, Sliders,
  BookOpen, ChevronDown, ChevronUp, Brain, PanelLeft, AlertTriangle,
  CornerDownRight, CheckCircle2, ArrowRight, ExternalLink,
  HelpCircle, Download, Copy, Check, Globe, FileCode,
  PieChart, ChevronRight, MessageSquare, Sprout, Construction, Orbit, Activity,
  Image as ImageIcon, Film, Sun, Moon, Crosshair, Tag, Calendar, Layers
} from 'lucide-react';
import { MarkdownResponse } from './MarkdownResponse';
import { ToolRolloutBar } from './ToolRolloutBar';
import { MediaAttachmentPreview } from './MediaAttachmentPreview';
import { ChatCameraRecorder } from './ChatCameraRecorder';

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

// Helper to separate technical telemetry from user-facing semantic analysis
const extractThoughtFromText = (rawText) => {
  if (!rawText || typeof rawText !== 'string') return { thought: null, cleanText: rawText };

  // Match legacy debug headers like:
  // ### Autonomous Visual Investigation (AGRICULTURE)
  // Visual Perception: Grounded 9 spatial entities with 5 causal relationships...
  // Graph Confidence: 97%
  // #### Scientific Analysis:
  const debugMatch = rawText.match(
    /^(?:###\s*Autonomous\s*(?:Visual\s*)?Investigation[^\n]*\n+)?(?:\*?\*?Visual Perception\*?\*?:[^\n]+\n+)?(?:\*?\*?Graph Confidence\*?\*?:[^\n]+\n+)?(?:####\s*Scientific Analysis:\s*\n+|####\s*Diagnostic Verdict:\s*\n+)?([\s\S]*)$/i
  );

  if (debugMatch && debugMatch[1] && debugMatch[1].trim() && debugMatch[0] !== debugMatch[1]) {
    const preamble = rawText.slice(0, rawText.length - debugMatch[1].length).trim();
    const lines = preamble.split('\n').map(l => l.replace(/[*#]/g, '').trim()).filter(Boolean);
    const thought = {
      title: 'Thought process',
      summary: lines[1] || 'Grounded spatial entities and formulated causal relationships',
      steps: lines.length > 0 ? lines : ['Visual scene grounding completed', 'Causal graph formulated']
    };
    return { thought, cleanText: debugMatch[1].trim() };
  }

  return { thought: null, cleanText: rawText };
};

// Claude / ChatGPT style collapsible thought process pill
const ThoughtProcessPill = ({ thought }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  if (!thought) return null;

  return (
    <div className="thought-process-container">
      <button
        type="button"
        className={`thought-process-pill ${isExpanded ? 'expanded' : ''}`}
        onClick={() => setIsExpanded(!isExpanded)}
        title={isExpanded ? "Collapse thinking steps" : "Expand thinking steps"}
      >
        <Sparkles size={12} className="thought-pill-sparkle" />
        <span className="thought-pill-title">{thought.title || 'Thought process'}</span>
        {thought.summary && (
          <>
            <span className="thought-pill-dot">·</span>
            <span className="thought-pill-summary">{thought.summary}</span>
          </>
        )}
        <span className="thought-pill-chevron">
          {isExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
        </span>
      </button>

      {isExpanded && (
        <div className="thought-process-dropdown animate-fade-in">
          <div className="thought-process-header">
            <span>REASONING & GROUNDING STEPS</span>
          </div>
          <ul className="thought-steps-list">
            {(thought.steps || [thought.summary]).map((step, idx) => (
              <li key={idx} className="thought-step-item">
                <CheckCircle2 size={13} style={{ color: 'var(--emerald)', marginTop: '2px', flexShrink: 0 }} />
                <span className="thought-step-text">{step}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

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
  theme = 'dark',
  onToggleTheme,
  onSelectTheme,
  onReturnToLanding,
  hasSensorData = true
}) {
  const [inputText, setInputText] = useState('');
  const [textSnippet, setTextSnippet] = useState(null);
  const [attachedFiles, setAttachedFiles] = useState([]);
  const [pendingFile, setPendingFile] = useState(null);
  const [isCameraModalOpen, setIsCameraModalOpen] = useState(false);
  const [answeringQId, setAnsweringQId] = useState(null);
  const [customAnswerText, setCustomAnswerText] = useState('');

  // Image Milestone & Longitudinal Metadata Modal State (Single Context Text Box)
  const [metaModalFileIdx, setMetaModalFileIdx] = useState(null);
  const [metaContextText, setMetaContextText] = useState('');
  const [metaColor, setMetaColor] = useState('#0284c7');

  // Floating "Ask Saar" Selection Popover State (ChatGPT style)
  const [selectionPopover, setSelectionPopover] = useState(null);
  const [copiedSelection, setCopiedSelection] = useState(false);

  // Multi-format Export Chat Dropdown state
  const [isExportMenuOpen, setIsExportMenuOpen] = useState(false);
  const [isThemeDropdownOpen, setIsThemeDropdownOpen] = useState(false);
  const [activeTermModal, setActiveTermModal] = useState(null);
  const exportMenuRef = useRef(null);
  const themeDropdownRef = useRef(null);

  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);
  const lastPasteTimeRef = useRef(0);

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleOutsideClick = (e) => {
      if (exportMenuRef.current && !exportMenuRef.current.contains(e.target)) {
        setIsExportMenuOpen(false);
      }
      if (themeDropdownRef.current && !themeDropdownRef.current.contains(e.target)) {
        setIsThemeDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleOutsideClick);
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, []);

  // Saar logo based on theme (use dark logo for light and purple-tinted white themes)
  const isLightMode = theme === 'light' || theme === 'purple';
  const saarLogoSrc = isLightMode ? '/saar-logo-dark.png' : '/saar-logo-white.png';
  const saarWordmarkSrc = isLightMode ? '/saar-wordmark-dark.png' : '/saar-wordmark-white.png';

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

  const handleShowSnippetInTextField = () => {
    if (!textSnippet) return;
    setInputText(textSnippet.content);
    setTextSnippet(null);
    if (textareaRef.current) {
      textareaRef.current.focus();
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight + 35, 180)}px`;
    }
  };

  const getFileCardMeta = (file) => {
    const name = file?.name || '';
    const type = file?.type || '';
    if (/\.(pptx?|key|odp)$/i.test(name) || type.includes('presentation')) {
      return { kind: 'presentation', label: 'Presentation', color: '#f43f5e' };
    }
    if (/\.(csv|xlsx?|parquet|tsv)$/i.test(name) || type.includes('spreadsheet') || type.includes('csv')) {
      return { kind: 'spreadsheet', label: 'Spreadsheet', color: '#10b981' };
    }
    if (/\.(pdf)$/i.test(name) || type.includes('pdf')) {
      return { kind: 'pdf', label: 'PDF Document', color: '#ef4444' };
    }
    if (/\.(mp4|mov|webm|avi|mkv)$/i.test(name) || type.startsWith('video/')) {
      return { kind: 'video', label: 'Video Clip', color: '#38bdf8' };
    }
    if (/\.(png|jpe?g|webp|gif|bmp|svg)$/i.test(name) || type.startsWith('image/')) {
      return { kind: 'image', label: 'Visual Anchor', color: '#a78bfa' };
    }
    return { kind: 'document', label: 'Document', color: '#94a3b8' };
  };

  const formatCardTitle = (name, maxLen = 32) => {
    if (!name) return '';
    const baseName = name.replace(/\.[^/.]+$/, '');
    if (baseName.length > maxLen) {
      return `${baseName.slice(0, maxLen)}...`;
    }
    return baseName;
  };

  const handleSend = () => {
    const combinedPrompt = [textSnippet?.content, inputText].filter(Boolean).join('\n\n').trim();
    if (!combinedPrompt && attachedFiles.length === 0) return;
    onSendMessage(combinedPrompt || inputText, attachedFiles);
    setInputText('');
    setTextSnippet(null);
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

  const enrichFilesWithPreviews = (files) => {
    return files.map((file) => {
      const isImg = (file.type || '').toLowerCase().startsWith('image/') || /\.(png|jpe?g|webp|gif|bmp|svg)$/i.test(file.name);
      if (isImg && !file._previewUrl) {
        try {
          file._previewUrl = URL.createObjectURL(file);
        } catch (e) {}
      }
      return file;
    });
  };

  const openMetaModal = (idx) => {
    const file = attachedFiles[idx];
    if (!file) return;
    const existing = file._saarMeta || {};
    setMetaModalFileIdx(idx);
    setMetaContextText(existing.context || existing.notes || '');
    const palette = ['#0284c7', '#0ea5e9', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#14b8a6', '#06b6d4'];
    setMetaColor(existing.color || palette[idx % palette.length]);
  };

  const handleSaveMeta = () => {
    if (metaModalFileIdx === null) return;
    setAttachedFiles((prev) => {
      const next = [...prev];
      const target = next[metaModalFileIdx];
      if (target) {
        const text = metaContextText.trim();
        let infoPart = text;
        let messagePart = text;

        // Find separator colon (skipping time colons like 14:00)
        let splitIdx = null;
        for (let i = 0; i < text.length; i++) {
          if (text[i] === ':') {
            if (i > 0 && i < text.length - 1 && /\d/.test(text[i - 1]) && /\d/.test(text[i + 1])) {
              continue;
            }
            splitIdx = i;
            break;
          }
        }
        if (splitIdx !== null) {
          infoPart = text.slice(0, splitIdx).trim();
          messagePart = text.slice(splitIdx + 1).trim();
        }

        const dayMatch = text.match(/(?:day|milestone|timepoint|d|week)\s*[:#-]?\s*(\d+)/i);
        const parsedDay = dayMatch ? Number(dayMatch[1]) : (metaModalFileIdx + 1);
        const cleanLabel = infoPart ? (infoPart.length > 32 ? infoPart.slice(0, 30) + '...' : infoPart) : `Day ${parsedDay}`;

        target._saarMeta = {
          day: parsedDay,
          context: text,
          info: infoPart,
          notes: messagePart || text,
          label: cleanLabel,
          stage: infoPart || `Day ${parsedDay}`,
          color: metaColor
        };
      }
      return next;
    });
    setMetaModalFileIdx(null);
  };

  const handleAutoSequenceDays = () => {
    setAttachedFiles((prev) => {
      const palette = ['#0284c7', '#0ea5e9', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#14b8a6', '#06b6d4'];
      let imgIdx = 0;
      return prev.map((f) => {
        const isImg = (f.type || '').toLowerCase().startsWith('image/') || /\.(png|jpe?g|webp|gif|bmp|svg)$/i.test(f.name);
        if (isImg) {
          imgIdx++;
          const dayOffsets = [1, 10, 20, 30, 45, 60, 90, 120];
          const assignedDay = imgIdx <= dayOffsets.length ? dayOffsets[imgIdx - 1] : imgIdx * 10;
          const defaultContext = `Day ${assignedDay}, Stage ${imgIdx} : Track developmental progression and tissue status.`;
          f._saarMeta = {
            day: assignedDay,
            context: f._saarMeta?.context || defaultContext,
            info: f._saarMeta?.info || `Day ${assignedDay}, Stage ${imgIdx}`,
            notes: f._saarMeta?.notes || 'Track developmental progression and tissue status.',
            label: `Day ${assignedDay}: Specimen ${imgIdx}`,
            stage: `Day ${assignedDay}`,
            color: f._saarMeta?.color || palette[(imgIdx - 1) % palette.length]
          };
        }
        return f;
      });
    });
  };

  const handleTextareaChange = (e) => {
    setInputText(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 180)}px`;
  };

  const handleFileChange = (e) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      setAttachedFiles((prev) => [...prev, ...enrichFilesWithPreviews(files)]);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handlePaste = async (e) => {
    const now = Date.now();
    // Guard against rapid duplicate paste events fired within 50ms
    if (now - lastPasteTimeRef.current < 50) {
      return;
    }
    lastPasteTimeRef.current = now;

    const clipboardData = e.clipboardData || window.clipboardData;
    if (!clipboardData) return;

    // 1. Check for clipboard files (e.g. copied screenshots, images from Snipping Tool, copied media)
    const items = Array.from(clipboardData.items || []);
    const fileItems = items.filter((item) => item.kind === 'file');

    if (fileItems.length > 0) {
      const pastedFiles = [];
      const seenSignatures = new Set();
      for (const item of fileItems) {
        const file = item.getAsFile();
        if (file) {
          const sig = `${file.size}_${file.type}`;
          if (seenSignatures.has(sig)) continue;
          seenSignatures.add(sig);

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
        e.stopPropagation();
        setAttachedFiles((prev) => [...prev, ...enrichFilesWithPreviews(pastedFiles)]);
        return;
      }
    }

    // 2. Direct clipboard files (e.g. copied from file explorer)
    if (clipboardData.files && clipboardData.files.length > 0) {
      e.preventDefault();
      e.stopPropagation();
      const files = Array.from(clipboardData.files);
      setAttachedFiles((prev) => [...prev, ...enrichFilesWithPreviews(files)]);
      return;
    }

    const text = clipboardData.getData('text');
    if (text) {
      const trimmed = text.trim();

      // 3. File path / filename detection (e.g. copied file path from VS Code or typed path)
      const cleanPath = trimmed.replace(/^["']|["']$/g, '').trim();
      const isFilePathCandidate = /\.(csv|xlsx?|tsv|json|txt|png|jpe?g|webp|pdf)$/i.test(cleanPath) &&
        (cleanPath.includes('/') || cleanPath.includes('\\') || !cleanPath.includes('\n'));

      if (isFilePathCandidate) {
        try {
          const apiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8001';
          const res = await fetch(`${apiUrl}/api/saar/read-file?path=${encodeURIComponent(cleanPath)}`);
          if (res.ok) {
            e.preventDefault();
            e.stopPropagation();
            const blob = await res.blob();
            const filename = res.headers.get('X-Filename') || cleanPath.split(/[/\\]/).pop() || 'dataset.csv';
            const fileObj = new File([blob], filename, {
              type: blob.type || (filename.endsWith('.csv') ? 'text/csv' : 'application/octet-stream')
            });
            setAttachedFiles((prev) => [...prev, ...enrichFilesWithPreviews([fileObj])]);
            return;
          }
        } catch (fetchErr) {
          // If backend can't find file, continue to text/tabular logic
        }
      }

      // 4. Tabular text detection (CSV or TSV text pasted into chat input)
      const lines = trimmed.split(/\r?\n/).filter((l) => l.trim().length > 0);

      // Check if text is a tabular CSV or TSV (header + data rows with matching delimiters)
      if (lines.length >= 2) {
        const header = lines[0];
        const commaCount0 = (header.match(/,/g) || []).length;
        const tabCount0 = (header.match(/\t/g) || []).length;
        const semiCount0 = (header.match(/;/g) || []).length;
        const maxDelim0 = Math.max(commaCount0, tabCount0, semiCount0);

        if (maxDelim0 >= 1) {
          const sampleLine = lines[1];
          const commaCount1 = (sampleLine.match(/,/g) || []).length;
          const tabCount1 = (sampleLine.match(/\t/g) || []).length;
          const semiCount1 = (sampleLine.match(/;/g) || []).length;
          const maxDelim1 = Math.max(commaCount1, tabCount1, semiCount1);

          if (maxDelim1 >= 1) {
            e.preventDefault();
            e.stopPropagation();

            const firstCol = header.split(/,|\t|;/)[0].replace(/["']/g, '').trim();
            const datasetName = firstCol && firstCol.length < 25
              ? `${firstCol.toLowerCase().replace(/[^a-z0-9_]/g, '_')}_dataset.csv`
              : 'pasted_dataset.csv';

            const csvBlob = new Blob([trimmed], { type: 'text/csv' });
            const csvFile = new File([csvBlob], datasetName, { type: 'text/csv' });

            setAttachedFiles((prev) => [...prev, csvFile]);
            return;
          }
        }
      }

      // 5. Convert large non-tabular text pastes into a staged draft pill card (Claude / ChatGPT behavior)
      if (trimmed.length > 220) {
        e.preventDefault();
        e.stopPropagation();
        const cleanFirst = trimmed.split('\n')[0].replace(/^[#>*\s-]+/, '').trim();
        const title = cleanFirst.length > 24 ? `${cleanFirst.slice(0, 24)}..` : (cleanFirst || 'Draft text..');
        setTextSnippet({
          title,
          content: trimmed
        });
        return;
      }
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFiles = Array.from(e.dataTransfer.files);
      setAttachedFiles((prev) => [...prev, ...enrichFilesWithPreviews(droppedFiles)]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  return (
    <div className="chatgpt-container">
      {/* Top Navbar */}
      <header className="chatgpt-header">
        <div className="header-left">
          {!isSidebarOpen && (
            <>
              <button
                className="sidebar-toggle-btn"
                onClick={onToggleSidebar}
                title="Open sidebar"
              >
                <PanelLeft size={18} />
              </button>

              {onReturnToLanding && (
                <button
                  type="button"
                  className="header-logo-btn"
                  onClick={onReturnToLanding}
                  title="Return to SAAR Landing Page"
                >
                  <img
                    src={saarLogoSrc}
                    alt="Saar Logo"
                    className="saar-header-emblem-img"
                  />
                  <img
                    src={saarWordmarkSrc}
                    alt="SAAR"
                    className="saar-header-wordmark-img"
                  />
                </button>
              )}
            </>
          )}
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

          {/* Theme Dropdown (Light, Dark, Purple, Cyan) */}
          <div className="header-theme-dropdown-wrapper" ref={themeDropdownRef}>
            <button
              type="button"
              className="header-theme-dropdown-btn"
              onClick={() => setIsThemeDropdownOpen((prev) => !prev)}
              title="Change Theme Palette"
              aria-haspopup="true"
              aria-expanded={isThemeDropdownOpen}
            >
              {theme === 'light' && <Sun size={14} className="theme-current-icon" />}
              {theme === 'dark' && <Moon size={14} className="theme-current-icon" />}
              {theme === 'purple' && <Sparkles size={14} className="theme-current-icon text-purple" />}
              <span className="theme-current-label">
                {theme === 'light' ? 'Pure Light' : theme === 'dark' ? 'Pure Dark' : 'Lavender White'}
              </span>
              <ChevronDown size={11} className={`theme-arrow ${isThemeDropdownOpen ? 'open' : ''}`} />
            </button>

            {isThemeDropdownOpen && (
              <div className="theme-menu-dropdown">
                <div className="theme-menu-title">SELECT THEME</div>
                {[
                  { id: 'light', label: 'Pure Light', icon: <Sun size={14} />, color: '#0284c7' },
                  { id: 'dark', label: 'Pure Dark', icon: <Moon size={14} />, color: '#818cf8' },
                  { id: 'purple', label: 'Lavender White (Purple Tint)', icon: <Sparkles size={14} />, color: '#7e22ce' }
                ].map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    className={`theme-menu-item ${theme === t.id ? 'active' : ''}`}
                    onClick={() => {
                      onSelectTheme?.(t.id);
                      setIsThemeDropdownOpen(false);
                    }}
                  >
                    <span className="theme-color-dot" style={{ backgroundColor: t.color }} />
                    <span className="theme-item-text">{t.label}</span>
                    {theme === t.id && <Check size={12} className="theme-item-check" />}
                  </button>
                ))}
              </div>
            )}
          </div>

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
              <div
                className={`welcome-brand-mark ${onReturnToLanding ? 'clickable' : ''}`}
                onClick={onReturnToLanding}
                title={onReturnToLanding ? "Return to SAAR Landing Page" : undefined}
                role={onReturnToLanding ? "button" : undefined}
                tabIndex={onReturnToLanding ? 0 : undefined}
              >
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
                        {(() => {
                          const { thought, cleanText } = extractThoughtFromText(msg.text);
                          const activeThought = msg.thoughtProcess || thought;
                          return (
                            <>
                              {msg.role === 'assistant' && activeThought && (
                                <ThoughtProcessPill thought={activeThought} />
                              )}
                              <MarkdownResponse
                                content={msg.role === 'assistant' ? cleanText : msg.text}
                                pairedQuestion={pairedText}
                                role={msg.role}
                                onAskSaar={handleAskSaarFromAction}
                              />
                            </>
                          );
                        })()}
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

                    {/* Sleek, subtle exploration shortcuts */}
                    {msg.role === 'assistant' && msg.report && (
                      <div className="chat-tool-badges-row compact-row">
                        {selectedDomain === 'pediatrics' && (
                          <button
                            type="button"
                            className="tool-invoke-badge compact"
                            onClick={() => onOpenTool('gait')}
                            title="Open Pediatric Gait Video Analysis"
                          >
                            <Film size={12} className="text-cyan" />
                            <span>Video Analysis</span>
                            <ArrowRight size={10} />
                          </button>
                        )}
                        <button
                          type="button"
                          className="tool-invoke-badge compact"
                          onClick={() => onOpenTool('grounded')}
                          title="Inspect spatial visual bounding boxes on image canvas"
                        >
                          <Crosshair size={12} className="text-emerald" />
                          <span>Image Analysis</span>
                          <ArrowRight size={10} />
                        </button>

                        <button
                          type="button"
                          className="tool-invoke-badge compact"
                          onClick={() => onOpenTool('graph')}
                          title="Open active Causal Knowledge Graph"
                        >
                          <GitFork size={12} className="text-purple" />
                          <span>Causal Graph ({msg.report.relationships?.length || (msg.report.final_graph?.edges?.length ?? 5)} Edges)</span>
                          <ArrowRight size={10} />
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
          selectedDomain={selectedDomain}
        />
      </div>

      {/* Floating Bottom Composer Capsule */}
      <div className="chatgpt-composer-wrapper">
        {/* Attachment Preview Popover Dialog */}
        {pendingFile && (
          <MediaAttachmentPreview
            file={pendingFile}
            onConfirm={() => {
              setAttachedFiles((prev) => [...prev, ...enrichFilesWithPreviews([pendingFile])]);
              setPendingFile(null);
              if (fileInputRef.current) fileInputRef.current.value = '';
            }}
            onCancel={() => {
              setPendingFile(null);
              if (fileInputRef.current) fileInputRef.current.value = '';
            }}
          />
        )}

        {/* Context Attachment & Draft Snippet Tray (Claude / ChatGPT style) */}
        {(textSnippet || attachedFiles.length > 0) && (
          <div className="composer-context-tray">
            {/* Text Snippet / Draft Prompt Card */}
            {textSnippet && (
              <div
                className="context-pill-card text-snippet-card"
                onClick={handleShowSnippetInTextField}
                title="Click to populate in text field"
              >
                <div className="card-icon-wrapper doc-snippet-icon">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <rect x="2.5" y="2.5" width="19" height="19" rx="5" stroke="#0284c7" strokeWidth="2.2" fill="rgba(2, 132, 199, 0.12)" />
                    <line x1="6.5" y1="9.5" x2="17.5" y2="9.5" stroke="#0284c7" strokeWidth="2.4" strokeLinecap="round" />
                    <line x1="6.5" y1="14.5" x2="13.5" y2="14.5" stroke="#0284c7" strokeWidth="2.4" strokeLinecap="round" />
                  </svg>
                </div>
                <div className="pill-card-text">
                  <div className="pill-card-title">{textSnippet.title}</div>
                  <div className="pill-card-subtitle action-link">
                    <span>Show in text field</span>
                    <ChevronRight size={13} className="action-chevron" />
                  </div>
                </div>
                <button
                  className="pill-dismiss-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    setTextSnippet(null);
                  }}
                  title="Dismiss snippet"
                >
                  <X size={12} />
                </button>
              </div>
            )}

            {/* Batch Milestone Auto-Sequence Bar (rendered if >= 2 images attached) */}
            {(() => {
              const imageCount = attachedFiles.filter((f) => getFileCardMeta(f).kind === 'image').length;
              if (imageCount >= 2) {
                return (
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    width: '100%',
                    padding: '4px 8px',
                    marginBottom: '6px',
                    background: 'rgba(56, 189, 248, 0.08)',
                    borderRadius: '8px',
                    border: '1px dashed rgba(56, 189, 248, 0.25)'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.74rem', color: '#cbd5e1' }}>
                      <Layers size={13} color="#38bdf8" />
                      <span><strong>{imageCount} Specimen Images Attached</strong> (Multi-Iteration Sequence)</span>
                    </div>
                    <button
                      type="button"
                      onClick={handleAutoSequenceDays}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                        padding: '3px 8px',
                        borderRadius: '6px',
                        background: 'linear-gradient(135deg, rgba(56, 189, 248, 0.2), rgba(139, 92, 246, 0.2))',
                        border: '1px solid rgba(56, 189, 248, 0.35)',
                        color: '#38bdf8',
                        fontSize: '0.7rem',
                        fontWeight: 600,
                        cursor: 'pointer'
                      }}
                      title="Automatically sequence Day 1, Day 10, Day 20... across images"
                    >
                      <Sliders size={11} />
                      <span>Auto-Sequence Days</span>
                    </button>
                  </div>
                );
              }
              return null;
            })()}

            {/* Attached Files Cards */}
            {attachedFiles.map((file, idx) => {
              const meta = getFileCardMeta(file);
              const isImg = meta.kind === 'image';
              const saarMeta = file._saarMeta;

              // Ensure preview URL is generated for any image file
              let preview = file._previewUrl;
              if (isImg && !preview && typeof URL !== 'undefined' && URL.createObjectURL) {
                try {
                  preview = URL.createObjectURL(file);
                  file._previewUrl = preview;
                } catch (e) {}
              }

              return (
                <div
                  key={idx}
                  className={`context-pill-card file-card file-card-${meta.kind} ${isImg ? 'clickable-image-pill' : ''}`}
                  style={{
                    maxWidth: isImg ? '420px' : '360px',
                    cursor: isImg ? 'pointer' : 'default',
                  }}
                  onClick={isImg ? () => openMetaModal(idx) : undefined}
                  title={isImg ? 'Click image to edit metadata (milestone, day, stage, perspective)' : file.name}
                >
                  <div className="card-icon-wrapper">
                    {meta.kind === 'presentation' ? (
                      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" className="presentation-glyph">
                        <circle cx="12" cy="12" r="10" stroke="#f43f5e" strokeWidth="1.8" />
                        <path d="M12 2 A10 10 0 0 1 22 12 L12 12 Z" stroke="#f43f5e" strokeWidth="1.5" fill="rgba(244,63,94,0.22)" />
                        <text x="6.5" y="15.5" fill="#f43f5e" fontSize="9" fontWeight="700" fontFamily="system-ui, -apple-system, sans-serif">P</text>
                      </svg>
                    ) : meta.kind === 'spreadsheet' ? (
                      <PieChart size={22} color="#10b981" />
                    ) : meta.kind === 'video' ? (
                      <Film size={22} color="#38bdf8" />
                    ) : isImg && preview ? (
                      <img
                        src={preview}
                        alt="specimen preview"
                        style={{
                          width: '32px',
                          height: '32px',
                          objectFit: 'cover',
                          borderRadius: '6px',
                          border: saarMeta ? `2px solid ${saarMeta.color || '#a78bfa'}` : '1px solid rgba(167, 139, 250, 0.45)',
                          display: 'block'
                        }}
                      />
                    ) : meta.kind === 'image' ? (
                      <ImageIcon size={22} color="#a78bfa" />
                    ) : (
                      <FileText size={22} color="#94a3b8" />
                    )}
                  </div>
                  <div className="pill-card-text">
                    <div className="pill-card-title" title={file.name}>
                      {saarMeta?.label || formatCardTitle(file.name, 28)}
                    </div>
                    <div className="pill-card-subtitle" style={{ display: 'flex', alignItems: 'center', gap: '5px', flexWrap: 'wrap' }}>
                      {saarMeta?.day != null && (
                        <span style={{
                          fontSize: '0.64rem',
                          fontWeight: 700,
                          padding: '1px 5px',
                          borderRadius: '4px',
                          background: saarMeta.color || 'var(--primary)',
                          color: '#fff',
                          letterSpacing: '0.02em'
                        }}>
                          DAY {saarMeta.day}
                        </span>
                      )}
                      {saarMeta?.context ? (
                        <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)', maxWidth: '240px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={saarMeta.context}>
                          {saarMeta.context}
                        </span>
                      ) : isImg ? (
                        <span style={{ fontSize: '0.68rem', color: 'var(--primary)', display: 'inline-flex', alignItems: 'center', gap: '3px' }}>
                          <Tag size={10} />
                          <span>Click to add metadata (info : message)</span>
                        </span>
                      ) : (
                        <span style={{ color: 'var(--text-dim)' }}>{meta.label}</span>
                      )}
                    </div>
                  </div>

                  <button
                    className="pill-dismiss-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      setAttachedFiles(attachedFiles.filter((_, i) => i !== idx));
                    }}
                    title="Remove attachment"
                  >
                    <X size={12} />
                  </button>
                </div>
              );
            })}
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
            accept=".csv,.xlsx,.xls,.pptx,.ppt,.pdf,.docx,.txt,.png,.jpg,.jpeg,.webp,.mp4,.mov,.webm,.avi,.mkv"
            onChange={handleFileChange}
          />

          {/* Plus Attach Button */}
          <button
            type="button"
            className="composer-action-btn"
            onClick={() => fileInputRef.current?.click()}
            title="Attach dataset, image, or video"
          >
            <Paperclip size={18} />
          </button>

          {/* Real In-Browser Camera Button */}
          <button
            type="button"
            className={`composer-action-btn ${isCameraModalOpen || cameraConnected ? 'camera-live' : ''}`}
            onClick={() => setIsCameraModalOpen(true)}
            title="Open camera & record video clip (up to 10s)"
          >
            <Camera size={18} />
          </button>

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

      {/* Real In-Browser WebRTC Camera Modal */}
      <ChatCameraRecorder
        isOpen={isCameraModalOpen}
        onClose={() => setIsCameraModalOpen(false)}
        onCaptureVideo={(recordedFile, autoSend) => {
          setIsCameraModalOpen(false);
          if (autoSend) {
            onSendMessage('', [recordedFile]);
          } else {
            setAttachedFiles((prev) => [...prev, recordedFile]);
          }
        }}
      />

      {/* Image Milestone & Longitudinal Metadata Modal */}
      {metaModalFileIdx !== null && attachedFiles[metaModalFileIdx] && (
        <div className="term-modal-backdrop" style={{ zIndex: 9999 }} onClick={() => setMetaModalFileIdx(null)}>
          <div
            className="term-modal-card metadata-theme-modal"
            style={{
              maxWidth: '520px',
              width: '94%',
              borderRadius: '16px',
              border: '1px solid var(--border-color)',
              background: 'var(--bg-card)',
              color: 'var(--text-main)',
              boxShadow: '0 20px 50px -10px rgba(0, 0, 0, 0.4), 0 0 1px var(--border-color)'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="term-modal-header" style={{ borderBottom: '1px solid var(--border-color)', padding: '14px 18px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Tag size={16} color="var(--primary)" />
                <h3 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-main)' }}>
                  Specimen Metadata & AI Instructions
                </h3>
              </div>
              <button
                className="term-modal-close-btn"
                onClick={() => setMetaModalFileIdx(null)}
                title="Close modal"
                style={{ background: 'transparent', border: 'none', color: 'var(--text-dim)', cursor: 'pointer', display: 'flex', alignItems: 'center', padding: '4px' }}
              >
                <X size={16} />
              </button>
            </div>

            <div className="term-modal-body" style={{ padding: '18px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {/* Thumbnail & File Details */}
              {(() => {
                const targetFile = attachedFiles[metaModalFileIdx];
                let modalPreview = targetFile?._previewUrl;
                if (!modalPreview && targetFile && typeof URL !== 'undefined' && URL.createObjectURL) {
                  try {
                    modalPreview = URL.createObjectURL(targetFile);
                    targetFile._previewUrl = modalPreview;
                  } catch (e) {}
                }
                return (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '10px', borderRadius: '10px', background: 'var(--bg-card-hover)', border: '1px solid var(--border-color)' }}>
                    {modalPreview ? (
                      <img
                        src={modalPreview}
                        alt="Preview"
                        style={{ width: '50px', height: '50px', objectFit: 'cover', borderRadius: '8px', border: '1px solid var(--border-color)' }}
                      />
                    ) : (
                      <ImageIcon size={32} color="var(--primary)" />
                    )}
                    <div style={{ minWidth: 0, flex: 1 }}>
                      <div style={{ fontSize: '0.84rem', fontWeight: 600, color: 'var(--text-main)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {targetFile?.name}
                      </div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--primary)', marginTop: '2px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Sliders size={11} />
                        <span>Two-Stage Pipeline: Text analyzed first → attached to image findings</span>
                      </div>
                    </div>
                  </div>
                );
              })()}

              {/* Format Specification Banner */}
              <div style={{
                padding: '10px 14px',
                borderRadius: '10px',
                background: 'var(--primary-bg)',
                border: '1px solid var(--border-color)',
                display: 'flex',
                flexDirection: 'column',
                gap: '5px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '6px' }}>
                  <span style={{ fontSize: '0.74rem', fontWeight: 700, color: 'var(--primary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Required Format:
                  </span>
                  <span style={{ fontSize: '0.68rem', color: 'var(--text-dim)', fontStyle: 'italic' }}>
                    No extra info or fields needed
                  </span>
                </div>
                <div style={{
                  fontFamily: 'var(--font-mono, monospace)',
                  fontSize: '0.8rem',
                  fontWeight: 700,
                  color: 'var(--text-main)',
                  background: 'var(--bg-card)',
                  padding: '6px 10px',
                  borderRadius: '6px',
                  border: '1px solid var(--border-color)',
                  letterSpacing: '0.01em',
                  display: 'inline-block'
                }}>
                  info(example: data,name,time etc) : message for ai
                </div>
                <div style={{ fontSize: '0.71rem', color: 'var(--text-dim)', lineHeight: 1.4 }}>
                  Put your specimen data (day, milestone, timestamp, or condition) before the colon <code>:</code>, and your specific instructions or question for the AI after it.
                </div>
              </div>

              {/* Text Area */}
              <div>
                <label style={{ display: 'block', fontSize: '0.76rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
                  Metadata & Message for AI
                </label>
                <textarea
                  value={metaContextText}
                  onChange={(e) => setMetaContextText(e.target.value)}
                  rows={5}
                  autoFocus
                  placeholder="Day 10, Incision Specimen, 14:00 : Inspect callus bridge and check vascular reconnection"
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    borderRadius: '10px',
                    border: '1px solid var(--border-color)',
                    background: 'var(--input-bg, var(--bg-dark))',
                    color: 'var(--text-main)',
                    fontSize: '0.84rem',
                    lineHeight: 1.45,
                    outline: 'none',
                    resize: 'vertical',
                    boxSizing: 'border-box',
                    fontFamily: 'var(--font-sans)'
                  }}
                />
              </div>
            </div>

            <div className="term-modal-footer" style={{ borderTop: '1px solid var(--border-color)', padding: '12px 18px', display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
              <button
                type="button"
                onClick={() => setMetaModalFileIdx(null)}
                style={{
                  padding: '7px 14px',
                  borderRadius: '8px',
                  background: 'transparent',
                  border: '1px solid var(--border-color)',
                  color: 'var(--text-main)',
                  fontSize: '0.8rem',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSaveMeta}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '7px 16px',
                  borderRadius: '8px',
                  background: 'var(--primary)',
                  border: 'none',
                  color: '#ffffff',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  boxShadow: '0 2px 8px var(--primary-glow)'
                }}
              >
                <Check size={14} />
                <span>Save Context</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
