import React, { useState } from 'react';
import {
  Copy, Check, FileText, BarChart2, Activity,
  HelpCircle, Sparkles, CheckCircle2, ChevronRight,
  TrendingUp, TrendingDown, ArrowRight, ShieldCheck,
  ExternalLink, Network, PieChart, RotateCcw
} from 'lucide-react';

/**
 * Parses inline formatting:
 * - **bold**
 * - *italic*
 * - `code`
 * - Correlation pills: r = +0.95 or r = -0.95
 * - Confidence percentages
 */
/**
 * Safely converts LaTeX mathematical expressions into clean, legible scientific typography.
 * Supports fractions, middle dots, products, Greek symbols, superscripts, subscripts,
 * and text environments without requiring heavy external dependencies.
 */
export function formatLatexMath(str) {
  if (!str) return '';
  let s = String(str);

  // Strip enclosing delimiters if present
  s = s.replace(/^\$\$|^\$|\$\$$|\$$/g, '').trim();

  // Normalize text wrappers
  s = s.replace(/\\(?:text|mathrm|mathbf|mathit|textbf)\{([^{}]+)\}/g, '$1');
  s = s.replace(/\\(?:text|mathrm|mathbf|mathit|textbf)\{([^{}]+)\}/g, '$1');

  // Fractions: recursively format \frac{num}{den}
  const fracRegex = /\\frac\s*\{((?:[^{}]|\{[^{}]*\})*)\}\s*\{((?:[^{}]|\{[^{}]*\})*)\}/g;
  let prev = '';
  while (prev !== s && s.includes('\\frac')) {
    prev = s;
    s = s.replace(fracRegex, (_, num, den) => {
      const cleanNum = num.trim();
      const cleanDen = den.trim();
      if (/^[a-zA-Z0-9.+−-]+$/.test(cleanNum) && /^[a-zA-Z0-9.+−-]+$/.test(cleanDen)) {
        return `(${cleanNum}/${cleanDen})`;
      }
      if (/^[a-zA-Z0-9.+−-]+$/.test(cleanDen)) {
        return `[ ${cleanNum} / ${cleanDen} ]`;
      }
      return `[ ${cleanNum} ] / [ ${cleanDen} ]`;
    });
  }

  // Common mathematical & scientific symbols
  const symbolMap = {
    '\\\\approx': '≈',
    '\\\\cdot': '×',
    '\\\\times': '×',
    '\\\\pm': '±',
    '\\\\mp': '∓',
    '\\\\le': '≤',
    '\\\\leq': '≤',
    '\\\\ge': '≥',
    '\\\\geq': '≥',
    '\\\\ne': '≠',
    '\\\\neq': '≠',
    '\\\\equiv': '≡',
    '\\\\sim': '~',
    '\\\\propto': '∝',
    '\\\\infty': '∞',
    '\\\\in': '∈',
    '\\\\notin': '∉',
    '\\\\subset': '⊂',
    '\\\\subseteq': '⊆',
    '\\\\partial': '∂',
    '\\\\nabla': '∇',
    '\\\\sum': '∑',
    '\\\\prod': '∏',
    '\\\\int': '∫',
    '\\\\sqrt\\{([^}]+)\\}': '√($1)',
    '\\\\sqrt': '√',
    '\\\\varepsilon': 'ε',
    '\\\\epsilon': 'ε',
    '\\\\Delta': 'Δ',
    '\\\\delta': 'δ',
    '\\\\rho': 'ρ',
    '\\\\sigma': 'σ',
    '\\\\mu': 'μ',
    '\\\\alpha': 'α',
    '\\\\beta': 'β',
    '\\\\gamma': 'γ',
    '\\\\theta': 'θ',
    '\\\\lambda': 'λ',
    '\\\\omega': 'ω',
    '\\\\pi': 'π',
    '\\\\tau': 'τ',
    '\\\\phi': 'φ',
    '\\\\longrightarrow': '→',
    '\\\\rightarrow': '→',
    '\\\\longleftarrow': '←',
    '\\\\leftarrow': '←',
    '\\\\longleftrightarrow': '↔',
    '\\\\leftrightarrow': '↔',
    '\\\\quad': '  ',
    '\\\\qquad': '    ',
    '\\\\,': ' ',
    '\\\\;': ' ',
    '\\\\:': ' ',
    '\\\\!': '',
    '\\\\%': '%',
    '\\\\circ': '°'
  };

  for (const [pattern, repl] of Object.entries(symbolMap)) {
    s = s.replace(new RegExp(pattern, 'g'), repl);
  }

  // Parentheses & brackets
  s = s.replace(/\\left\(/g, '(').replace(/\\right\)/g, ')');
  s = s.replace(/\\left\[/g, '[').replace(/\\right\]/g, ']');
  s = s.replace(/\\left\|/g, '|').replace(/\\right\|/g, '|');
  s = s.replace(/\\left\{/g, '{').replace(/\\right\}/g, '}');

  // Matrix environments
  s = s.replace(/\\begin\{bmatrix\}([\s\S]*?)\\end\{bmatrix\}/g, (_, inner) => {
    const rows = inner.trim().split(/\\\\/).map(r => r.trim().replace(/&/g, ', '));
    return `[ ${rows.join('; ')} ]`;
  });

  // Superscripts
  s = s.replace(/\^\{?°\}?/g, '°');
  s = s.replace(/\^\{?2\}?/g, '²');
  s = s.replace(/\^\{?3\}?/g, '³');
  s = s.replace(/\^\{?-1\}?/g, '⁻¹');
  s = s.replace(/\^\{([^}]+)\}/g, '^($1)');

  // Subscripts
  s = s.replace(/_\{([A-Za-z0-9_\s+-]+)\}/g, (_, sub) => {
    if (sub.length > 2) return `(${sub.trim()})`;
    return `_${sub.trim()}`;
  });

  // Space before % if directly trailing letters
  s = s.replace(/([A-Za-z])%/g, '$1 %');

  // Minus sign cleanup inside mathematical formulas
  s = s.replace(/(?<=\s)-(?=\s)/g, '−');

  // Clean unparsed solitary backslashes
  s = s.replace(/\\([A-Za-z]+)/g, '$1');
  s = s.replace(/\\/g, '');

  return s.replace(/[ \t]+/g, ' ').trim();
}

/**
 * Parses inline formatting:
 * - **bold**
 * - *italic*
 * - `code`
 * - Math formulas: $...$ and $$...$$
 * - Correlation pills: r = +0.95 or r = -0.95
 * - Confidence percentages
 */
function renderInlineFormatting(text, onNavigateToAnalytics = null) {
  if (!text) return null;

  let processedText = String(text);

  // Auto-bold parameter key labels e.g. "Q1: Description" or "High Apex Reach Drill: Suspend..."
  if (/^[A-Za-z0-9][A-Za-z0-9\s&/–—'-]{1,45}:\s+/.test(processedText) && !/^[#*`~[$]/.test(processedText)) {
    const colonIdx = processedText.indexOf(':');
    const label = processedText.substring(0, colonIdx).trim();
    const remainder = processedText.substring(colonIdx + 1);
    return (
      <>
        <strong className="md-bold">{label}</strong>:
        {renderInlineFormatting(remainder, onNavigateToAnalytics)}
      </>
    );
  }

  const parts = [];
  const regex = /(\$\$[^\$]+\$\$|\$[^\$\n]+\$|\*\*[^*]+\*\*|\*[^*]+\*|~~[^~]+~~|`[^`]+`|(?:\[(?:HIGH|MEDIUM|LOW|CRITICAL)\])|(?:r\s*=\s*[+‑-]?\s*\d+\.?\d*)|(?:\b\d+%\b)|(?:→|↔|↓|←→))/gi;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(processedText)) !== null) {
    if (match.index > lastIndex) {
      parts.push(processedText.substring(lastIndex, match.index));
    }
    const token = match[0];

    if (token.startsWith('$$') && token.endsWith('$$')) {
      const inner = token.slice(2, -2);
      parts.push(
        <span key={match.index} className="md-math-inline md-math-display">
          {formatLatexMath(inner)}
        </span>
      );
    } else if (token.startsWith('$') && token.endsWith('$')) {
      const inner = token.slice(1, -1);
      parts.push(
        <span key={match.index} className="md-math-inline">
          {formatLatexMath(inner)}
        </span>
      );
    } else if (token.startsWith('**') && token.endsWith('**')) {
      const inner = token.slice(2, -2);
      parts.push(<strong key={match.index} className="md-bold">{renderInlineFormatting(inner, onNavigateToAnalytics)}</strong>);
    } else if (token.startsWith('~~') && token.endsWith('~~')) {
      const inner = token.slice(2, -2);
      parts.push(
        <del key={match.index} className="md-strikethrough" style={{ opacity: 0.65, textDecoration: 'line-through' }}>
          {renderInlineFormatting(inner, onNavigateToAnalytics)}
        </del>
      );
    } else if (token.startsWith('*') && token.endsWith('*')) {
      const inner = token.slice(1, -1);
      parts.push(<em key={match.index} className="md-italic">{renderInlineFormatting(inner, onNavigateToAnalytics)}</em>);
    } else if (token.startsWith('`') && token.endsWith('`')) {
      const inner = token.slice(1, -1);
      parts.push(<code key={match.index} className="md-inline-code">{inner}</code>);
    } else if (/^\[(HIGH|MEDIUM|LOW|CRITICAL)\]$/i.test(token)) {
      const prio = token.slice(1, -1).toUpperCase();
      parts.push(
        <span key={match.index} className={`md-priority-badge ${prio.toLowerCase()}`}>
          {prio}
        </span>
      );
    } else if (token.startsWith('r =') || token.startsWith('r=') || token.includes('r =') || token.includes('r=')) {
      const isNeg = token.includes('-') || token.includes('‑');
      parts.push(
        <span key={match.index} className={`md-stat-badge ${isNeg ? 'negative' : 'positive'}`}>
          {isNeg ? <TrendingDown size={11} /> : <TrendingUp size={11} />}
          {token}
        </span>
      );
    } else if (/^\d+%$/.test(token)) {
      parts.push(
        <span key={match.index} className="md-conf-pill">
          {token}
        </span>
      );
    } else if (['→', '↔', '↓', '←→'].includes(token)) {
      parts.push(
        <span key={match.index} className="md-arrow-token">
          {token}
        </span>
      );
    } else {
      parts.push(token);
    }
    lastIndex = regex.lastIndex;
  }

  if (lastIndex < processedText.length) {
    parts.push(processedText.substring(lastIndex));
  }

  return parts.length > 0 ? parts : processedText;
}

/**
 * Parses markdown text into structured blocks
 */
function parseMarkdownBlocks(rawText) {
  if (!rawText) return [];

  // Strip internal LLM thinking tags <think>...</think> and any trailing unclosed <think>
  let cleanText = rawText.replace(/<think>[\s\S]*?<\/think>/gi, '').trim();
  cleanText = cleanText.replace(/<think>[\s\S]*/gi, '').trim();

  // Strip emojis and decorative emoticons for clean, professional clinical typography
  cleanText = cleanText.replace(/[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '');

  // Rejoin isolated bullet characters on their own line with the subsequent line of text:
  // e.g. "•\nQ1: Where does..." -> "• Q1: Where does..."
  cleanText = cleanText.replace(/(^|\n)\s*([•\-*])\s*\n\s*([^\n#•\-*])/g, '$1$2 $3');

  const lines = cleanText.split(/\r?\n/);
  const blocks = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    if (!trimmed) {
      i++;
      continue;
    }

    // 1. Code Block
    if (trimmed.startsWith('```')) {
      const lang = trimmed.slice(3).trim();
      const codeLines = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith('```')) {
        codeLines.push(lines[i]);
        i++;
      }
      i++;
      blocks.push({
        type: 'code',
        lang: lang || 'text',
        content: codeLines.join('\n')
      });
      continue;
    }

    // 2. Table Block
    if (trimmed.startsWith('|') && trimmed.endsWith('|') && trimmed.includes('|')) {
      const tableLines = [];
      while (i < lines.length && lines[i].trim().startsWith('|') && lines[i].trim().endsWith('|')) {
        tableLines.push(lines[i].trim());
        i++;
      }

      if (tableLines.length >= 2) {
        const headerRow = tableLines[0]
          .split('|')
          .slice(1, -1)
          .map((c) => c.trim());

        const hasSep = /^[\s|:-]+$/.test(tableLines[1]);
        const startDataIdx = hasSep ? 2 : 1;

        const bodyRows = tableLines.slice(startDataIdx).map((r) =>
          r
            .split('|')
            .slice(1, -1)
            .map((c) => c.trim())
        );

        blocks.push({
          type: 'table',
          headers: headerRow,
          rows: bodyRows
        });
        continue;
      }
    }

    // Strip leading markdown hashes (#) to evaluate semantic heading text
    const cleanHeading = trimmed.replace(/^#{1,6}\s*/, '').trim();

    // 1. Numbered Section Header (e.g. "1. Locomotion Kinematics & Symmetry", "### 1. Root Cause Finding", "## 2. Evidence Synthesis...")
    const isSectionHeader = /^\d+\.\s+[A-Z][A-Za-z0-9\s&,/:–—()'-]{3,80}$/.test(cleanHeading) && !cleanHeading.endsWith('.');
    if (isSectionHeader) {
      blocks.push({
        type: 'heading',
        level: 4,
        text: cleanHeading
      });
      i++;
      continue;
    }

    // 2. Unmarked or Markdown Document / Assessment Title
    // e.g. "Calibrated Pediatric Gait Diagnostic Report (95% Confidence)"
    // or "## Personalized Diagnostic Assessment: Benign Developmental Variation (62% Confidence)"
    // or "Badminton Biomechanical Assessment: Kinetic Chain Sequencing / Dropped Elbow (100% Confidence)"
    const isDocTitle = (blocks.length === 0 || (blocks.length === 1 && blocks[0].type === 'quote')) &&
      /^[A-Z][A-Za-z0-9\s&,/:–—()-]+?\((?:\d+%|CONFIDENCE|HIGH|MEDIUM|LOW|CRITICAL)[^)]*\)$/i.test(cleanHeading);
    if (isDocTitle) {
      blocks.push({
        type: 'heading',
        level: 3,
        text: cleanHeading
      });
      i++;
      continue;
    }

    // 3. Standard Headings (#, ##, ###, ####, etc.)
    if (trimmed.startsWith('#')) {
      const match = trimmed.match(/^(#{1,6})\s+(.*)$/);
      if (match) {
        const level = match[1].length;
        const text = match[2].trim();
        blocks.push({
          type: 'heading',
          level,
          text
        });
        i++;
        continue;
      }
    }

    // 4. Horizontal Rule
    if (/^(\*\*\*|---|___)$/.test(trimmed)) {
      blocks.push({ type: 'hr' });
      i++;
      continue;
    }

    // 5. Blockquote / Callout
    if (trimmed.startsWith('>')) {
      const quoteLines = [];
      while (i < lines.length && lines[i].trim().startsWith('>')) {
        quoteLines.push(lines[i].trim().replace(/^>\s?/, ''));
        i++;
      }
      blocks.push({
        type: 'quote',
        content: quoteLines.join('\n')
      });
      continue;
    }

    // 5.5. Block Math ($$ ... $$)
    if (trimmed.startsWith('$$')) {
      const mathLines = [];
      if (trimmed.endsWith('$$') && trimmed.length > 4) {
        mathLines.push(trimmed.slice(2, -2).trim());
        i++;
      } else {
        mathLines.push(trimmed.slice(2).trim());
        i++;
        while (i < lines.length && !lines[i].trim().endsWith('$$')) {
          mathLines.push(lines[i].trim());
          i++;
        }
        if (i < lines.length) {
          const lastLine = lines[i].trim();
          mathLines.push(lastLine.replace(/\$\$$/, '').trim());
          i++;
        }
      }
      const rawMath = mathLines.filter(Boolean).join(' ');
      blocks.push({
        type: 'math',
        content: formatLatexMath(rawMath)
      });
      continue;
    }

    // 6. Disclaimer block
    const isDisclaimer = /^(?:\*?[A-Za-z\s]+Disclaimer:\*?|\*Clinical Note:\*)/i.test(trimmed);
    if (isDisclaimer) {
      blocks.push({
        type: 'disclaimer',
        text: trimmed
      });
      i++;
      continue;
    }

    // 6. Lists & Prioritized Next Steps
    const isBullet = /^[-*•]\s+/.test(trimmed);
    const isNumber = /^\d+\.\s+/.test(trimmed);
    const isPriorityItem = /^\[(?:HIGH|MEDIUM|LOW|CRITICAL)\]\s+/i.test(trimmed);

    if (isBullet || isNumber || isPriorityItem) {
      const items = [];
      const listType = (isNumber || isPriorityItem) ? 'ordered' : 'unordered';

      while (i < lines.length) {
        const currentTrim = lines[i].trim();
        const bulletMatch = currentTrim.match(/^[-*•]\s+(.*)$/);
        const numberMatch = currentTrim.match(/^\d+\.\s+(.*)$/);
        const prioMatch = currentTrim.match(/^(\[(?:HIGH|MEDIUM|LOW|CRITICAL)\].*)$/i);

        let rawItemText = null;
        if (bulletMatch && listType === 'unordered') {
          rawItemText = bulletMatch[1];
          i++;
        } else if (numberMatch && listType === 'ordered') {
          rawItemText = numberMatch[1];
          i++;
        } else if (prioMatch && listType === 'ordered') {
          rawItemText = prioMatch[1];
          i++;
        } else if (currentTrim === '') {
          if (
            i + 1 < lines.length &&
            ((listType === 'unordered' && /^[-*•]\s+/.test(lines[i + 1].trim())) ||
              (listType === 'ordered' && (/^\d+\.\s+/.test(lines[i + 1].trim()) || /^\[(?:HIGH|MEDIUM|LOW|CRITICAL)\]/i.test(lines[i + 1].trim()))))
          ) {
            i++;
          } else {
            break;
          }
        } else {
          break;
        }

        if (rawItemText) {
          // Normalize unbolded priority items: "[MEDIUM] Title: Description (Derived from... | Source: ...)"
          let normalized = rawItemText;
          const unboldedPrioMatch = normalized.match(/^(\[(?:HIGH|MEDIUM|LOW|CRITICAL)\])\s*([^:*]+):\s*([\s\S]*)$/i);
          if (unboldedPrioMatch) {
            const prioTag = unboldedPrioMatch[1].toUpperCase();
            const title = unboldedPrioMatch[2].trim();
            let body = unboldedPrioMatch[3].trim();
            let sourceInfo = '';
            const srcMatch = body.match(/\((?:Derived from finding '[^']+'\s*\|\s*)?Source:\s*([^)]+)\)$/);
            if (srcMatch) {
              sourceInfo = ` *(Source: ${srcMatch[1].trim()})*`;
              body = body.replace(/\s*\((?:Derived from finding '[^']+'\s*\|\s*)?Source:\s*[^)]+\)$/, '').trim();
            } else {
              body = body.replace(/\s*\(Derived from finding '[^']+'\)$/, '').trim();
            }
            normalized = `${prioTag} **${title}**: ${body}${sourceInfo}`;
          }
          items.push(normalized);
        }
      }

      blocks.push({
        type: 'list',
        listType,
        items
      });
      continue;
    }

    // 7. Regular Paragraph
    const paraLines = [trimmed];
    i++;
    while (i < lines.length) {
      const nextTrim = lines[i].trim();
      if (
        !nextTrim ||
        nextTrim.startsWith('#') ||
        nextTrim.startsWith('```') ||
        (nextTrim.startsWith('|') && nextTrim.endsWith('|')) ||
        nextTrim.startsWith('>') ||
        /^[-*•]\s+/.test(nextTrim) ||
        /^\d+\.\s+/.test(nextTrim) ||
        /^(\*\*\*|---|___)$/.test(nextTrim)
      ) {
        break;
      }
      paraLines.push(nextTrim);
      i++;
    }

    blocks.push({
      type: 'paragraph',
      text: paraLines.join(' ')
    });
  }

  return blocks;
}

/**
 * Extracts relationship pairs from content or relationships prop
 */
function extractDiscoveredPairs(content, explicitRelationships = []) {
  const pairs = [];
  const seen = new Set();

  // 1. Explicit relationships
  if (Array.isArray(explicitRelationships) && explicitRelationships.length > 0) {
    explicitRelationships.forEach((r) => {
      const src = r.source_feature || r.source;
      const tgt = r.target_feature || r.target;
      if (src && tgt) {
        const key = `${src.toLowerCase()}__${tgt.toLowerCase()}`;
        if (!seen.has(key)) {
          seen.add(key);
          pairs.push({
            source_feature: src,
            target_feature: tgt,
            strength: r.strength ?? 0.85,
            direction: r.direction || (r.strength < 0 ? 'negative' : 'positive')
          });
        }
      }
    });
  }

  // 2. Extract from markdown text if pairs found
  if (content && pairs.length === 0) {
    const tablePairRegex = /(?:\|\s*(?:\*\*)?([a-zA-Z0-9_\s]+)(?:\*\*)?\s*(?:↔|<->|->|→)\s*(?:\*\*)?([a-zA-Z0-9_\s]+)(?:\*\*)?.*?\|\s*(?:[+‑-]?\d+\.?\d*|\*\*[+‑-]?\d+\.?\d*\*\*))/g;
    let m;
    while ((m = tablePairRegex.exec(content)) !== null) {
      const src = m[1].replace(/\*\*/g, '').trim();
      const tgt = m[2].replace(/\*\*/g, '').trim();
      if (src && tgt && src.length > 1 && tgt.length > 1) {
        const key = `${src.toLowerCase()}__${tgt.toLowerCase()}`;
        if (!seen.has(key)) {
          seen.add(key);
          pairs.push({
            source_feature: src,
            target_feature: tgt,
            strength: 0.9,
            direction: 'positive'
          });
        }
      }
    }

    // Generic fallback regex for inline mentions like "temperature ↔ soil_moisture" or "moisture ↔ growth"
    if (pairs.length === 0) {
      const inlineRegex = /\b([a-zA-Z_]{3,20})\s*(?:↔|<->|→)\s*([a-zA-Z_]{3,20})\b/g;
      let im;
      while ((im = inlineRegex.exec(content)) !== null) {
        const src = im[1].trim();
        const tgt = im[2].trim();
        const key = `${src.toLowerCase()}__${tgt.toLowerCase()}`;
        if (!seen.has(key)) {
          seen.add(key);
          pairs.push({
            source_feature: src,
            target_feature: tgt,
            strength: 0.85,
            direction: 'positive'
          });
        }
      }
    }
  }

  return pairs;
}

function MarkdownResponseComponent({
  content,
  pairedQuestion = null,
  role = 'assistant',
  isCompact = false,
  relationships = [],
  onNavigateToAnalytics = null,
  onAskSaar = null,
  onRestartTriage = null,
  onClose = null
}) {
  const [copied, setCopied] = useState(false);
  const [showRaw, setShowRaw] = useState(false);

  if (!content) return null;

  const handleCopy = () => {
    let textToCopy = content;
    if (pairedQuestion && pairedQuestion.trim()) {
      if (role === 'user') {
        textToCopy = `### Question:\n${content.trim()}\n\n### Saar Reasoning Agent Response:\n${pairedQuestion.trim()}`;
      } else {
        textToCopy = `### Question:\n${pairedQuestion.trim()}\n\n### Saar Reasoning Agent Response:\n${content.trim()}`;
      }
    }
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const blocks = parseMarkdownBlocks(content);
  const discoveredPairs = extractDiscoveredPairs(content, relationships);

  return (
    <div className={`saar-markdown-container ${isCompact ? 'compact' : ''}`}>
      {/* Content Body */}

      {showRaw ? (
        <pre className="md-raw-view">{content}</pre>
      ) : (
        <div className="saar-markdown-body">
          {blocks.map((block, idx) => {
            switch (block.type) {
              case 'heading': {
                const Tag = `h${Math.min(block.level + 1, 6)}`;
                return (
                  <div key={idx} className={`md-heading-wrapper level-${block.level}`}>
                    <Tag className={`md-heading h${block.level}`}>
                      {renderInlineFormatting(block.text, onNavigateToAnalytics)}
                    </Tag>
                  </div>
                );
              }

              case 'table':
                return (
                  <div key={idx} className="md-table-wrapper">
                    <table className="md-table">
                      <thead>
                        <tr>
                          {block.headers.map((h, hIdx) => (
                            <th key={hIdx}>{renderInlineFormatting(h, onNavigateToAnalytics)}</th>
                          ))}
                          {onNavigateToAnalytics && <th>Visual Actions</th>}
                        </tr>
                      </thead>
                      <tbody>
                        {block.rows.map((row, rIdx) => {
                          // Check if row contains a pair
                          const rowText = row.join(' ');
                          const pairMatch = rowText.match(/(?:[*_]*)([a-zA-Z0-9_\s]+)(?:[*_]*)\s*(?:↔|<->|->|→)\s*(?:[*_]*)([a-zA-Z0-9_\s]+)(?:[*_]*)/);
                          const detectedSource = pairMatch ? pairMatch[1].replace(/\*/g, '').trim() : row[0]?.replace(/\*/g, '').trim();
                          const detectedTarget = pairMatch ? pairMatch[2].replace(/\*/g, '').trim() : 'Stress / Growth';

                          return (
                            <tr key={rIdx}>
                              {row.map((cell, cIdx) => {
                                const isStrengthCol =
                                  block.headers[cIdx]?.toLowerCase().includes('correlation') ||
                                  block.headers[cIdx]?.toLowerCase().includes('(r)');
                                return (
                                  <td key={cIdx} className={isStrengthCol ? 'stat-cell' : ''}>
                                    {renderInlineFormatting(cell, onNavigateToAnalytics)}
                                  </td>
                                );
                              })}
                              {onNavigateToAnalytics && (
                                <td className="table-actions-cell">
                                  <button
                                    className="table-action-chip"
                                    title={`Redirect to Visual Analytics to inspect ${detectedSource} ↔ ${detectedTarget}`}
                                    onClick={() =>
                                      onNavigateToAnalytics(
                                        { source_feature: detectedSource, target_feature: detectedTarget },
                                        'histogram'
                                      )
                                    }
                                  >
                                    <BarChart2 size={11} /> Inspect
                                  </button>
                                </td>
                              )}
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                );

              case 'code':
                return (
                  <div key={idx} className="md-code-box">
                    <div className="md-code-header">
                      <span>{block.lang || 'Causal Mechanism Flow'}</span>
                      <button
                        onClick={() => navigator.clipboard.writeText(block.content)}
                        className="md-code-copy"
                        title="Copy code"
                      >
                        <Copy size={11} />
                      </button>
                    </div>
                    <pre className="md-code-content">
                      <code>{block.content}</code>
                    </pre>
                  </div>
                );

              case 'math':
                return (
                  <div key={idx} className="md-math-block">
                    <div className="md-math-content">{block.content}</div>
                  </div>
                );

              case 'quote': {
                const quoteParagraphs = block.content.split(/\n\s*\n/);
                return (
                  <blockquote key={idx} className="md-blockquote">
                    <div className="quote-accent" />
                    <div className="quote-text">
                      {quoteParagraphs.map((para, pIdx) => (
                        <div key={pIdx} className={pIdx > 0 ? 'quote-para-margin' : ''}>
                          {para.split('\n').map((line, lIdx, arr) => (
                            <React.Fragment key={lIdx}>
                              {renderInlineFormatting(line, onNavigateToAnalytics)}
                              {lIdx < arr.length - 1 && <br />}
                            </React.Fragment>
                          ))}
                        </div>
                      ))}
                    </div>
                  </blockquote>
                );
              }

              case 'list':
                if (block.listType === 'ordered') {
                  return (
                    <ol key={idx} className="md-ordered-list">
                      {block.items.map((item, itemIdx) => (
                        <li key={itemIdx} className="md-list-item">
                          <span className="list-number-badge">{itemIdx + 1}</span>
                          <div className="list-text">{renderInlineFormatting(item, onNavigateToAnalytics)}</div>
                        </li>
                      ))}
                    </ol>
                  );
                } else {
                  return (
                    <ul key={idx} className="md-unordered-list">
                      {block.items.map((item, itemIdx) => (
                        <li key={itemIdx} className="md-list-item">
                          <span className="list-bullet-badge">•</span>
                          <div className="list-text">{renderInlineFormatting(item, onNavigateToAnalytics)}</div>
                        </li>
                      ))}
                    </ul>
                  );
                }

              case 'hr':
                return <hr key={idx} className="md-divider" />;

              case 'paragraph': {
                if (
                  block.text.toLowerCase().startsWith('**bottom line:**') ||
                  block.text.toLowerCase().startsWith('bottom line:') ||
                  block.text.toLowerCase().startsWith('**key takeaway:**')
                ) {
                  return (
                    <div key={idx} className="md-bottom-line-card">
                      <div className="bottom-line-badge">
                        <Sparkles size={13} /> KEY TAKEAWAY
                      </div>
                      <div className="bottom-line-body">{renderInlineFormatting(block.text, onNavigateToAnalytics)}</div>
                    </div>
                  );
                }

                return (
                  <p key={idx} className="md-paragraph">
                    {renderInlineFormatting(block.text, onNavigateToAnalytics)}
                  </p>
                );
              }

              case 'disclaimer':
                return (
                  <div key={idx} className="md-disclaimer-block">
                    {renderInlineFormatting(block.text, onNavigateToAnalytics)}
                  </div>
                );

              default:
                return null;
            }
          })}

          {/* Dynamic Interactive Graph & Visual Analytics Action Cards */}
          {discoveredPairs.length > 0 && onNavigateToAnalytics && (
            <div className="md-graph-actions-section">
              <div className="graph-actions-header">
                <BarChart2 size={13} className="header-icon" />
                <span>Field Relationship Visualizers (Click to Inspect Graph &amp; Charts):</span>
              </div>

              <div className="pair-action-cards-grid">
                {discoveredPairs.slice(0, 4).map((pair, pIdx) => (
                  <div key={pIdx} className="pair-action-card">
                    <div className="pair-info">
                      <strong className="pair-name">
                        {pair.source_feature} ↔ {pair.target_feature}
                      </strong>
                      <span className={`pair-pill ${pair.direction}`}>
                        {pair.direction === 'negative' ? <TrendingDown size={10} /> : <TrendingUp size={10} />}
                        {pair.strength ? `r = ${pair.strength.toFixed(2)}` : 'Coupled'}
                      </span>
                    </div>

                    <div className="pair-btns-row">
                      <button
                        className="pair-btn histogram-btn"
                        title="Show interactive Plotly Histogram"
                        onClick={() => onNavigateToAnalytics(pair, 'histogram')}
                      >
                        <BarChart2 size={11} /> Plotly Histogram
                      </button>

                      <button
                        className="pair-btn bar-btn"
                        title="Show interactive Plotly Bar Chart"
                        onClick={() => onNavigateToAnalytics(pair, 'bar')}
                      >
                        <PieChart size={11} /> Plotly Bar
                      </button>

                      <button
                        className="pair-btn graph-btn"
                        title="Show interactive Plotly Scatter Graph"
                        onClick={() => onNavigateToAnalytics(pair, 'dot')}
                      >
                        <Network size={11} /> Plotly Scatter
                      </button>

                      <button
                        className="pair-btn graph-btn"
                        style={{ borderColor: 'var(--purple)', color: 'var(--purple)' }}
                        title="Show interactive Plotly 3D Surface Density"
                        onClick={() => onNavigateToAnalytics(pair, 'surface3d')}
                      >
                        <Activity size={11} /> Plotly 3D
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Subtle Bottom Action Bar (only on assistant responses) */}
      {role === 'assistant' && (
        <div className="md-bottom-action-bar">
          {onRestartTriage && (
            <button
              onClick={onRestartTriage}
              title="Restart diagnostic triage inquiry"
              className="md-bottom-action-btn"
              style={{ marginRight: 'auto' }}
            >
              <RotateCcw size={12} />
              <span>Restart Triage</span>
            </button>
          )}
          <button
            onClick={() => setShowRaw(!showRaw)}
            title="Toggle between formatted and raw view"
            className="md-bottom-action-btn"
          >
            <FileText size={12} />
            <span>{showRaw ? 'Formatted' : 'Raw'}</span>
          </button>
          <button
            onClick={handleCopy}
            title={pairedQuestion ? "Copy question and response to clipboard" : "Copy to clipboard"}
            className="md-bottom-action-btn"
          >
            {copied ? <Check size={12} color="var(--emerald)" /> : <Copy size={12} />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
        </div>
      )}
    </div>
  );
}

export const MarkdownResponse = React.memo(MarkdownResponseComponent);
export default MarkdownResponse;
