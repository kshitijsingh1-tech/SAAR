# SAAR — Visual Scientific Reasoning & Multi-Modal Kinematics Engine

<div align="center">

![SAAR Logo](frontend/public/saar-logo-white.png)

## Autonomous Multi-Agent Causal Reasoning, Bayesian Belief Updating, Pediatric Gait Biometrics & Badminton Kinematics

[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows%20%7C%20Linux-000000.svg?style=flat-square)](https://github.com/kshitijsingh1-tech/SAAR)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.2.0-61DAFB.svg?style=flat-square&logo=react)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Vite-5.4-646CFF.svg?style=flat-square&logo=vite)](https://vitejs.dev/)
[![NetworkX](https://img.shields.io/badge/NetworkX-Graph_Engine-blue.svg?style=flat-square)](https://networkx.org/)
[![SciPy](https://img.shields.io/badge/SciPy-DSP_Kinematics-8CAAE6.svg?style=flat-square&logo=scipy)](https://scipy.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)

> *“Deconstruct observations into essence. Traverse causal graphs. Quantify uncertainty. Prove truth.”*

</div>

---

## Key Architectural Specifications

- **[Master Architecture Specification (`architecture.md`)](architecture.md)** — Comprehensive architecture document covering system topology, VLM cascading, DSP pipelines, adaptive inquiry, and tool gating protocols.
- **[Badminton Kinematics Architecture (`BADMINTON_ARCHITECTURE.md`)](BADMINTON_ARCHITECTURE.md)** — In-depth computer vision specification for BWF court homography, 33-point BlazePose keypoints, and stroke classification.
- **[Zero-Hardcoding Directives (`AGENTS.md`)](AGENTS.md)** — Absolute engineering directives governing epistemic honesty, data contracts, and presentation layer purity.
- **[Engineering Progress & Invariants Ledger (`work_done.md`)](work_done.md)** — Auditable log of all implemented features, root cause analyses, and non-regression guarantees.

---

## Executive Overview: What is SAAR?

In conventional artificial intelligence, multi-modal systems operate as **opaque, single-pass black boxes**:

```text
Visual Input / Video / Tabular Data ---> [ Monolithic VLM / LLM ] ---> Superficial Text Verdict
                                       -> High Hallucination Rate
                                       -> Zero Verifiable Evidence Chain
                                       -> Unfalsifiable Guesses
```

**SAAR** (*Discover What Matter*) replaces single-pass visual heuristics with an **iterative, multi-agent scientific reasoning loop** combined with **deterministic physics and signal processing engines**.

Instead of jumping directly to an unverified conclusion, SAAR constructs a **dynamic causal knowledge graph**, identifies epistemic uncertainty, runs specialized domain simulators, queries the human investigator for high-information-gain observations, and executes deterministic DSP pipelines to extract verified metrics across agriculture, pediatric gait, sports biomechanics, and civil infrastructure.

```text
                               +--------------------------------------------------------+
                               |               ORCHESTRATING REASONING AGENT            |
                               |          Hypothesis Generation & Uncertainty Scent     |
                               +---------------------------+----------------------------+
                                                           |
                                                           v
                +----------------------------------------------------------------------------------+
                |                           DYNAMIC CAUSAL GRAPH STORE                             |
                |                 Entities, Latent Properties, Hypotheses & Confidences            |
                +--------------+---------------------------+---------------------------+-----------+
                               |                           |                           |
                               v                           v                           v
                 +---------------------------+ +-----------------------+ +---------------------------+
                 |     Perception Sensors    | |  Domain Simulators    | |  Human-in-the-Loop Cards  |
                 | Multi-Modal Vision / Tab  | | GPR, Darcy, Homography| | Epistemic Uncertainty Qs  |
                 +---------------------------+ +-----------------------+ +---------------------------+
```

---

## Flagship Capabilities & Domain Pillars

### 1. Badminton Biomechanics & Kinematics Studio (`backend/app/plugins/sports/badminton/`)
An evidence-driven athletic kinematics engine evaluating high-velocity overhead strokes and rallies from everyday video:
- **Planar 3 x 3 BWF Metric Court Homography** ([`court_detector.py`](backend/app/plugins/sports/badminton/court_detector.py)):
  - Computes perspective transform matrix $H$ mapping camera coordinates $[u, v, 1]^T$ to international BWF dimensions ($13.40\text{m} \times 6.10\text{m}$):
    $$\begin{bmatrix} X_w \\ Y_w \\ 1 \end{bmatrix} \sim H \begin{bmatrix} u \\ v \\ 1 \end{bmatrix}$$
- **Multi-Signal Smash Peak Velocity Fusion** ([`shot_detector.py`](backend/app/plugins/sports/badminton/shot_detector.py)):
  - Fuses three concurrent kinematic triggers to identify authentic smashes without false positives:
    1. Wrist/forearm linear velocity peak: $v_{\text{wrist}} \ge 45\text{ km/h}$.
    2. Kinetic chain elbow extension: $\theta_{\text{elbow}} \ge 140^\circ$.
    3. Trajectory reversal of the shuttlecock along the forward vector.
- **Court Distance, 9-Zone Spatial Heatmaps & Recovery Centroid** ([`movement_analyzer.py`](backend/app/plugins/sports/badminton/movement_analyzer.py)):
  - Tracks player center of mass (sacrum midpoint landmarks 23 & 24) across the calibrated court plane.
  - Evaluates recovery latency to the optimal defensive base ($x \approx 3.05\text{m}, y \approx 3.8\text{m}$).
  - Multi-scenario coaching RAG knowledge base ([`badminton_tactics_and_scenarios_kb.md`](backend/app/knowledge/badminton_tactics_and_scenarios_kb.md)) covering smash defense, backhand clears, shot deception, net tumbling, and safe lunging.

---

### 2. Adaptive Diagnostic Inquiry Engine & Strict Tool Gating
Interactive Bayesian information-gain triage system for clinical, sports, and botanical reasoning:
- **Strict Tool Gating Invariant**:
  - While diagnostic questions are active, domain studio tools remain **locked** in the floating rollout bar, drawer, and message header badges.
  - Unlocks domain studios (`badminton`, `gait`, `verdict`, `rag`) **only after all required questions are answered** and the analysis concludes.
- **Unified Elevated White Card Layout** ([`MarkdownResponse.jsx`](frontend/src/components/MarkdownResponse.jsx)):
  - Concluded triage assessments render as a single elevated white card (`#ffffff` background, `box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.05)`).
  - Numbered diagnostic headings (e.g. `### 1. Root Cause Finding`, `## 1. Locomotion Kinematics`) automatically classify as `level: 4` (`h4`), styled in signature **Purple `#4338ca`** with full-width underline dividers.
  - Priority badges (`[HIGH]`, `[MEDIUM]`, `[LOW]`, `[CRITICAL]`) automatically parse and render with semantic colors.
  - Action buttons on the card (e.g. `[Launch Badminton Biomechanics Studio]`, `[Restart Triage]`, `[Copy]`, `[Raw]`).

---

### 3. Pediatric Toddler AI / Gait Analysis Engine (`backend/app/gait/`)
A deterministic, 11-stage clinical biomechanical pipeline evaluating motor milestone acquisition from everyday 30 FPS mobile smartphone video:
- **Zero Phase-Lag DSP Smoothing** ([`smoothing.py`](backend/app/gait/events/smoothing.py)):
  - 2nd-order Savitzky-Golay polynomial filter (`scipy.signal.savgol_filter`) preserves true peak amplitude without temporal delay.
  - Adaptive filter window length: $\text{window} = \text{clamp}(FPS \times 0.23\text{s}, [5, 15])$ scales filtering to real physical time.
  - Direction-invariant median pelvis displacement estimation (+1.0 for rightwards, -1.0 for leftwards).
  - Bounded NaN occlusion interpolation bridges crossover leg losses up to 14 frames ($\sim 0.46\text{s}$) without hallucinating steps during stops.
- **Sub-Frame Parabolic Heel-Strike Peak Interpolation** ([`heel_strike.py`](backend/app/gait/events/heel_strike.py)):
  - Dual-landmark confidence fusion: $\text{foot}_x = \frac{v_{\text{heel}} \cdot x_{\text{heel}} + v_{\text{ankle}} \cdot x_{\text{ankle}}}{v_{\text{heel}} + v_{\text{ankle}}}$.
  - Subtracts sacrum midpoint $\frac{x_{\text{left\_hip}} + x_{\text{right\_hip}}}{2}$ to eliminate camera drift and walking room progression.
  - Continuous timestamp refinement down to millisecond precision via quadratic vertex interpolation:
    $$p = \frac{1}{2}\frac{y_{\text{prev}} - y_{\text{next}}}{y_{\text{prev}} - 2y_{\text{curr}} + y_{\text{next}}},\quad t_{\text{strike}} = t_{\text{frame}} + \frac{p}{\text{FPS}}$$
- **Deterministic Clinical Biometrics** ([`metric_computer.py`](backend/app/gait/metrics/metric_computer.py)):
  - **Cadence**: $\text{Cadence} = \frac{60}{\bar{t}_{\text{step}}}$ (steps/min).
  - **Robinson Step Time Asymmetry Index**: $100 \times \frac{|\bar{t}_L - \bar{t}_R|}{0.5(\bar{t}_L + \bar{t}_R)}$.
  - **Rhythm Variability**: $\text{CoV } \% = 100 \times \frac{\sigma}{\bar{t}_{\text{step}}}$.
  - **Stance & Swing Phase Decomposition**: Stance phase ($\sim 60\%$), Swing phase ($\sim 40\%$), and Double Support duration.
  - Benchmarked against **Dr. David Sutherland (1988) *"The Development of Mature Walking"*** and WHO pediatric motor milestone developmental curves across ages 6–120 months.

---

### 4. Precision Agriculture & Agronomic Pathology
- **Dynamic Causal Graph Construction**: Falsifiable hypothesis testing for crop ailments (*Pythium ultimum*, *Fusarium oxysporum*, Nitrogen/Iron chlorosis).
- **Zero-Hardcoding Telemetry Guard**: Optical canopy inspections strictly emit foliar vegetative vigor hypotheses; subterranean soil aeration, root anoxia, and pH speciation tools are dynamically gated until sensor telemetry (CSV/Excel) confirms soil probes exist.
- **Dynamic Species Taxonomy**: Resolves botanical taxonomy dynamically (*Rosa hybrid*, *Solanum lycopersicum*, *Monstera adansonii*, etc.) with zero cross-scenario template leakage.
- **Multivariate Sensor Workbench**: Time-series progression curves, bivariate scatter plots with dynamic Pearson $r$ correlation coefficients, and an interactive $N \times N$ correlation heatmap matrix.
- **Darcy’s Law Percolation**: Physical hydrological flow and soil saturation kinetics.

---

### 5. Civil Infrastructure & Geotechnical Void Detection
- **Ground Penetrating Radar (GPR)**: Hyperbolic reflection fitting to detect subterranean void cavities and assess sinkhole collapse risk.
- **Hydraulic Culvert Modeling**: Culvert intake flow and hydrostatic head-loss simulations.
- **Structural Pavement Integrity**: AASHTO load-bearing capacity and deflection modeling.

---

## Zero-Hardcoding Architecture Directive

SAAR strictly enforces a **Zero-Hardcoding Architecture** governed by [`AGENTS.md`](AGENTS.md) and [`.agents/rules/no_hardcoding.md`](.agents/rules/no_hardcoding.md):
1. **Pure Presentation Layer**: UI components (`ImageInspector.jsx`, `PlotlyGraphViewer.jsx`, `ChatGPTView.jsx`) are strictly display layers. No hardcoded mock bounding boxes, phantom labels, or preset-matching conditionals (`if (isTomato)...`).
2. **Epistemic Honesty**: If visual evidence cannot confirm subsurface features (e.g., roots, soil pH, moisture), SAAR presents an honest empty state or requests telemetry rather than synthesizing phantom nodes.
3. **Dynamic Semantic Routing**: Analytical tools are dispatched dynamically based on semantic properties (`node.category === 'pathology'`), not static ID dictionaries.
4. **Strict Session Isolation**: Every uploaded image, video, and dataset forms an independent atomic session. State from prior investigations never bleeds into new runs.

---

## Repository Layout

```text
SAAR/
├── start.sh                                 # Automated 1-click startup script for macOS/Linux
├── AGENTS.md                                # Zero-hardcoding engineering directives & rules
├── architecture.md                          # Master system architecture specification
├── BADMINTON_ARCHITECTURE.md                # Computer vision badminton kinematics architecture
├── work_done.md                             # Ledger of resolved features & non-regression invariants
│
├── backend/
│   ├── app/
│   │   ├── main.py                          # FastAPI REST server & WebSocket gateway
│   │   ├── schemas.py                       # Pydantic schema contracts & data models
│   │   ├── graph_engine.py                  # NetworkX causal knowledge graph manager
│   │   ├── dynamic_loop.py                  # ReAct scientific reasoning loop
│   │   ├── vlm_service.py                   # Multimodal vision (Gemini 3.7/3.1, Groq Vision)
│   │   ├── rag_service.py                   # Domain literature retrieval (BM25)
│   │   ├── adaptive_inquiry.py              # Bayesian information-gain interactive triage
│   │   │
│   │   ├── gait/                            # Toddler Gait Analysis Engine
│   │   │   ├── pipeline.py                  # 11-stage deterministic pipeline orchestrator
│   │   │   ├── video_processor.py           # Frame extraction & MediaPipe pose tracking
│   │   │   ├── events/
│   │   │   │   ├── heel_strike.py           # Sub-frame parabolic peak heel-strike detector
│   │   │   │   └── smoothing.py             # Savitzky-Golay zero phase-lag DSP filter
│   │   │   ├── metrics/
│   │   │   │   └── metric_computer.py       # Cadence, Robinson Asymmetry, CoV %, Stance/Swing
│   │   │   ├── angles/
│   │   │   │   └── joint_angles.py          # 2D Joint ROM (hip, knee, ankle flexion/extension)
│   │   │   ├── posture/
│   │   │   │   └── trunk_posture.py         # Trunk tilt angle & lateral sway kinematics
│   │   │   └── norms/
│   │   │       ├── toddler_norms.py         # Sutherland (1988) developmental walking curves
│   │   │       └── advanced_norms.py        # Multi-metric normative comparison engine
│   │   │
│   │   ├── plugins/                         # Domain-Specific Analytical Plugins
│   │   │   ├── base_plugin.py               # Plugin interface contract
│   │   │   ├── agriculture_plugin.py        # Plant pathology, Darcy percolation & telemetry
│   │   │   ├── infrastructure_plugin.py     # GPR hyperbolic void detection & hydraulics
│   │   │   └── sports/
│   │   │       └── badminton/
│   │   │           ├── court_detector.py    # 3x3 planar homography court calibration
│   │   │           ├── shot_detector.py     # Smash peak velocity multi-signal fusion
│   │   │           ├── shot_classifier.py   # Stroke classification (Smash, Clear, Drop, Net)
│   │   │           ├── speed_analyzer.py    # Continuous shuttle velocity estimation
│   │   │           └── movement_analyzer.py # Court coverage & player center of mass
│   │   │
│   │   ├── knowledge/                       # Scientific RAG Knowledge Bases
│   │   │   ├── sports_performance_tactics_kb.md
│   │   │   └── badminton_tactics_and_scenarios_kb.md
│   │   │
│   │   └── services/
│   │       ├── reasoning_service.py         # Dynamic belief updating & hypothesis refinement
│   │       ├── analytics_service.py         # Multi-metric timeseries & correlation matrix
│   │       └── dictionary_service.py        # Grounded scientific terminology lookup
│   └── requirements.txt                     # Python dependencies
│
└── frontend/
    ├── src/
    │   ├── App.jsx                          # Main workbench orchestrator & tool gating
    │   ├── index.css                        # Design system tokens & elevated card styling
    │   ├── components/
    │   │   ├── ChatGPTView.jsx              # Conversational reasoning interface & badge gating
    │   │   ├── AdaptiveInquiryCard.jsx      # Bayesian multi-turn triage & studio launcher
    │   │   ├── MarkdownResponse.jsx         # Dynamic section parser (purple h4, priority badges)
    │   │   ├── ToolRolloutBar.jsx           # Floating circular dynamic tool unlock bar
    │   │   ├── ToolCanvasDrawer.jsx         # Domain studio slide-out drawer
    │   │   ├── BadmintonDashboard.jsx       # Court tracking, video player, shots & speed gauge
    │   │   ├── KnowledgeGraphCanvas.jsx     # Interactive NetworkX causal graph viewer
    │   │   ├── ImageInspector.jsx           # Optical canvas with grounded bounding box anchors
    │   │   └── SensorAnalyticsWorkbench.jsx # Timelines, bivariate scatter & correlation matrix
    └── package.json                         # React 18, Vite 5 & frontend dependencies
```

---

## Quick Start Guide

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** & **npm**

---

### macOS / Linux Startup

```bash
# Clone repository
git clone https://github.com/kshitijsingh1-tech/SAAR.git
cd SAAR

# 1-Click Startup
chmod +x start.sh
./start.sh
```

Or run manually in two terminal tabs:

```bash
# Terminal 1 — Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev
```

---

### Windows Startup (PowerShell)

Open two PowerShell windows:

#### Terminal 1 — Backend (FastAPI on Port 8002)
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload
```

> [!TIP]
> If PowerShell shows an execution policy error, run:  
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process` and re-run `.\venv\Scripts\Activate.ps1`.

#### Terminal 2 — Frontend (React on Port 3000)
```powershell
cd frontend
npm install
npm run dev
```

Open **`http://localhost:3000`** in your browser.

---

## Environment Variables Configuration

SAAR functions out-of-the-box with offline simulation fallbacks. To activate live multi-modal vision perception and deep ReAct agentic reasoning, configure `backend/.env`:

```ini
# Google Gemini Vision (Multimodal Optical Inspection & ReAct Synthesis)
# Active Models: gemini-3.7-flash, gemini-3.1-flash-lite
# Obtain key: https://aistudio.google.com/
GEMINI_API_KEY=your_gemini_api_key_here

# Groq API (High-Throughput Vision & Fast ReAct Reasoning)
# Models used: llama-3.2-11b-vision-preview, llama-3.3-70b-versatile
# Obtain key: https://console.groq.com/
GROQ_API_KEY=your_groq_api_key_here
```

---

## Localhost Port Reference

| Service | Localhost URL | Purpose |
| :--- | :--- | :--- |
| **Frontend Web App** | [`http://localhost:3000`](http://localhost:3000) | Interactive React Scientific Investigation Console |
| **Backend API** | [`http://127.0.0.1:8002`](http://127.0.0.1:8002) | FastAPI Causal Inference & WebSocket Gateway |
| **Interactive API Docs** | [`http://127.0.0.1:8002/docs`](http://127.0.0.1:8002/docs) | Swagger UI for live endpoint testing |
| **ReDoc Specifications** | [`http://127.0.0.1:8002/redoc`](http://127.0.0.1:8002/redoc) | Alternate REST API reference |

---

## Scientific & Mathematical Grounding Summary

| Domain | Mathematical / Physical Foundation | Authoritative Academic Reference |
| :--- | :--- | :--- |
| **Badminton Biomechanics** | Planar 3 x 3 Homography ($H$), kinetic chain angular velocity fusion | BWF Official Court Standards; TrackNet; CoachAI / ShuttleSet Dataset |
| **Pediatric Gait** | 2nd-order Savitzky-Golay filter, quadratic sub-frame peak interpolation, Robinson Asymmetry index | Sutherland (1988) *"The Development of Mature Walking"*; WHO Motor Milestones |
| **Precision Agriculture** | Darcy's Law for saturated porous flow, SPAD/NDVI chlorophyll decay modeling | Darcy (1856); Gitelson et al. (2003) |
| **Civil Geotechnics** | Hyperbolic radar diffraction wave equation, Manning's culvert formula | Daniels (2004) *Ground Penetrating Radar*; AASHTO Pavement Design |

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
