import React from 'react';
import {
  X, HelpCircle, BookOpen, UploadCloud, Sliders,
  ShieldCheck, MessageSquare, CheckCircle2, Zap
} from 'lucide-react';

export function HelpDrawer({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="help-drawer" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <div className="drawer-title-group">
            <HelpCircle size={18} className="text-primary" />
            <h2>Saar System User Guide</h2>
          </div>
          <button className="icon-btn-close" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className="drawer-body">
          {/* Quick Overview */}
          <div className="guide-section">
            <h3><Zap size={15} /> What is Saar?</h3>
            <p>
              Saar is an autonomous visual and empirical scientific reasoning engine. Unlike conventional VLMs that generate single-pass text guesses, Saar maintains an active Knowledge Graph, executes specialized domain tools, and updates its belief state iteratively.
            </p>
          </div>

          {/* Workflow Steps */}
          <div className="guide-section">
            <h3><UploadCloud size={15} /> How to Run an Investigation</h3>
            <ol className="guide-steps-list">
              <li>
                <strong>Start on Launchpad or Workspace:</strong> Choose a pre-loaded benchmark (e.g., Tomato Crop 30-Day Failure or Road Pavement Void) or upload your own CSV/XLSX dataset.
              </li>
              <li>
                <strong>Review Extracted Evidence:</strong> Saar profiles all numeric and categorical telemetry, builds statistical relationships, and generates candidate hypotheses.
              </li>
              <li>
                <strong>Answer Targeted Inquiries:</strong> When the reasoning engine detects high causal ambiguity, it presents interactive questions. Answering them immediately updates confidence scores!
              </li>
              <li>
                <strong>Inspect the Causal Knowledge Graph:</strong> Open the dynamic causal graph to visualize directed causal links, node confidences, and topological uncertainty.
              </li>
              <li>
                <strong>Roll Out Operational Scientific Tools:</strong> Access Grounded Split Graph for image-to-graph linkage, Sensor Analytics for Pearson correlations/trends, Scientific References for peer-reviewed citations, Visual Evidence Monitor for high-resolution imagery, and the Scientific Dictionary for domain terminology.
              </li>
            </ol>
          </div>

          {/* Data Formats Supported */}
          <div className="guide-section">
            <h3><BookOpen size={15} /> Supported Data Formats</h3>
            <div className="formats-grid">
              <div className="format-card">
                <strong>Structured Datasets</strong>
                <span>.csv, .xlsx, .xls, .tsv (e.g. 30-day sensor telemetry, field logs)</span>
              </div>
              <div className="format-card">
                <strong>Visual Imagery</strong>
                <span>.png, .jpg, .jpeg, .webp, or live camera stream for surface inspection</span>
              </div>
            </div>
          </div>

          {/* Tips & Shortcuts */}
          <div className="guide-section">
            <h3><Sliders size={15} /> Keyboard Shortcuts &amp; Tips</h3>
            <ul className="shortcuts-list">
              <li><kbd>Enter</kbd> : Send inquiry message or answer</li>
              <li><kbd>Shift + Enter</kbd> : Newline in composer</li>
              <li>Click any scenario card on the Launchpad to launch a complete guided investigation.</li>
            </ul>
          </div>
        </div>

        <div className="drawer-footer">
          <button className="btn btn-primary" onClick={onClose} style={{ width: '100%' }}>
            Got it, Let's Investigate
          </button>
        </div>
      </div>
    </div>
  );
}
