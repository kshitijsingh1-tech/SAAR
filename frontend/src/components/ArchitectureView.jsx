import React from 'react';
import {
  Layers, ArrowRight, GitFork, Cpu, ShieldCheck,
  Zap, Database, Eye, Terminal, CheckCircle2, Sliders
} from 'lucide-react';

export function ArchitectureView() {
  return (
    <div className="architecture-view-container">
      {/* Top Header */}
      <div className="arch-header">
        <div className="arch-eyebrow">
          <Layers size={14} /> SAAR SYSTEM ARCHITECTURE &amp; REASONING FLOW
        </div>
        <h1 className="arch-title">Decoupled Multi-Agent Reasoning Engine</h1>
        <p className="arch-subtitle">
          How Saar thinks: Decoupling visual perception from causal graph memory,
          specialized domain tools, and iterative Bayesian belief updating.
        </p>
      </div>

      {/* Comparison: Conventional VLM vs Saar */}
      <div className="arch-comparison-card">
        <div className="comp-col conventional">
          <div className="comp-badge badge-rose">Conventional Black-Box VLM</div>
          <div className="comp-flow">
            <span className="flow-step">Media / Sensor Data</span>
            <ArrowRight size={14} className="text-rose" />
            <span className="flow-step box-dark">Single Giant VLM (LLM)</span>
            <ArrowRight size={14} className="text-rose" />
            <span className="flow-step">Unverified Text (High Hallucination)</span>
          </div>
          <p className="comp-note">
            Flaws: Single-pass text generation, no topological graph memory, no quantitative uncertainty metric, zero scientific evidence traceability.
          </p>
        </div>

        <div className="comp-col saar">
          <div className="comp-badge badge-emerald">Saar Decoupled Multi-Agent Architecture</div>
          <div className="comp-flow">
            <span className="flow-step">Multi-Modal Inputs</span>
            <ArrowRight size={14} className="text-emerald" />
            <span className="flow-step box-accent">Perception + Graph Engine</span>
            <ArrowRight size={14} className="text-emerald" />
            <span className="flow-step box-accent">Domain Tools + ReAct Loop</span>
            <ArrowRight size={14} className="text-emerald" />
            <span className="flow-step">Evidence-Backed Scientific Dossier</span>
          </div>
          <p className="comp-note">
            Advantages: Rigorous Pydantic schema validation, directed causal graph ($G = V, E$), quantitative belief updating, and human-in-the-loop inquiry.
          </p>
        </div>
      </div>

      {/* 4 Multi-Agent Core Components */}
      <div className="arch-components-grid">
        <div className="arch-comp-card">
          <div className="card-top">
            <div className="icon-wrapper text-primary"><Eye size={20} /></div>
            <span className="role-tag">Layer 1</span>
          </div>
          <h3>Perception &amp; Schema Parser</h3>
          <p>
            Extracts raw entities, observations, and sensor telemetry from visual media (Gemini / Groq Qwen / OpenRouter) and structured CSV/XLSX datasets. Enforces rigid Pydantic typing to avoid hallucinated fields.
          </p>
          <ul className="spec-list">
            <li><CheckCircle2 size={12} className="text-emerald" /> Automatic column profiling &amp; statistical moments</li>
            <li><CheckCircle2 size={12} className="text-emerald" /> Zero hallucination schema enforcement</li>
          </ul>
        </div>

        <div className="arch-comp-card">
          <div className="card-top">
            <div className="icon-wrapper text-purple"><Database size={20} /></div>
            <span className="role-tag">Layer 2</span>
          </div>
          <h3>Knowledge Graph Store (NetworkX)</h3>
          <p>
            Maintains directed graph $G = (V, E)$ storing Objects, Properties, Observations, and Hypotheses. Calculates topological graph uncertainty:
          </p>
          <div className="formula-box">
            Uncertainty = 1.0 - Average Confidence(V ∪ E)
          </div>
          <ul className="spec-list">
            <li><CheckCircle2 size={12} className="text-emerald" /> Dynamic edge weighting (strengths -1.0 to +1.0)</li>
            <li><CheckCircle2 size={12} className="text-emerald" /> Topological uncertainty tracking</li>
          </ul>
        </div>

        <div className="arch-comp-card">
          <div className="card-top">
            <div className="icon-wrapper text-amber"><Terminal size={20} /></div>
            <span className="role-tag">Layer 3</span>
          </div>
          <h3>Specialized Analytical Tools</h3>
          <p>
            Executes target domain calculations rather than guessing. Dispatches specialized sub-models for ground-penetrating radar, hydrological leaching, and orbital fitting.
          </p>
          <ul className="spec-list">
            <li><CheckCircle2 size={12} className="text-emerald" /> Civil GPR Sub-surface Void Detector</li>
            <li><CheckCircle2 size={12} className="text-emerald" /> Agronomic Rhizosphere Leaching Simulator</li>
          </ul>
        </div>

        <div className="arch-comp-card">
          <div className="card-top">
            <div className="icon-wrapper text-emerald"><GitFork size={20} /></div>
            <span className="role-tag">Layer 4</span>
          </div>
          <h3>Human-in-the-Loop ReAct Loop</h3>
          <p>
            The reasoning planner identifies nodes with highest uncertainty. Formulates targeted questions for human investigators, dynamically updating belief states upon answer submission.
          </p>
          <ul className="spec-list">
            <li><CheckCircle2 size={12} className="text-emerald" /> High-information-gain question selection</li>
            <li><CheckCircle2 size={12} className="text-emerald" /> Instant belief updating &amp; evidence chain closure</li>
          </ul>
        </div>
      </div>

      {/* Multi-Agent Dynamic Loop Stepper */}
      <div className="panel arch-stepper-panel">
        <div className="panel-title">
          <Zap size={16} />
          <span>Dynamic Reasoning Execution Loop (ReAct)</span>
        </div>

        <div className="loop-steps-container">
          <div className="loop-step-item">
            <div className="step-number">1</div>
            <h4>Perceive</h4>
            <p>Ingest visual evidence or dataset. Extract entities &amp; baseline observations.</p>
          </div>
          <ArrowRight size={16} className="loop-arrow" />

          <div className="loop-step-item">
            <div className="step-number">2</div>
            <h4>Hypothesize</h4>
            <p>Generate candidate causal mechanisms. Compute initial graph uncertainty.</p>
          </div>
          <ArrowRight size={16} className="loop-arrow" />

          <div className="loop-step-item">
            <div className="step-number">3</div>
            <h4>Tool / Verify</h4>
            <p>Execute specialized domain tool or prompt human investigator with high-value inquiry.</p>
          </div>
          <ArrowRight size={16} className="loop-arrow" />

          <div className="loop-step-item">
            <div className="step-number">4</div>
            <h4>Update Belief</h4>
            <p>Recalculate node confidences. Propagate Bayesian belief deltas across edges.</p>
          </div>
          <ArrowRight size={16} className="loop-arrow" />

          <div className="loop-step-item">
            <div className="step-number">5</div>
            <h4>Conclude</h4>
            <p>Emit verified evidence-backed scientific dossier with root-cause verdict and causal graph trail.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
