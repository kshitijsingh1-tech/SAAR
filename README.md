# SAAR (सार) — Visual Scientific Reasoning Engine

<div align="center">

![SAAR Logo](frontend/public/saar-logo-white.png)

**Autonomous Multi-Agent Causal Reasoning, Bayesian Belief Updating & Dynamic Scientific Discovery**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.2.0-61DAFB.svg?style=flat-square&logo=react)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Vite-5.4-646CFF.svg?style=flat-square&logo=vite)](https://vitejs.dev/)
[![NetworkX](https://img.shields.io/badge/NetworkX-Graph_Engine-blue.svg?style=flat-square)](https://networkx.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)

*“Deconstruct observations into essence. Traverse causal graphs. Quantify uncertainty. Prove truth.”*

</div>

---

## 🔬 Executive Overview: What is SAAR?

In conventional artificial intelligence, multi-modal systems operate as **opaque, single-pass black boxes**:
```
Visual Input / Tabular Data  ───▶  [ Monolithic VLM / LLM ]  ───▶  Superficial Text Verdict
                                                                     ↳ High Hallucination Rate
                                                                     ↳ Zero Verifiable Evidence Chain
                                                                     ↳ Static Uncertainty
```

**SAAR** (सार — Sanskrit/Hindi for *“the distilled essence, fundamental truth, or core finding”*) replaces single-pass visual heuristics with an **iterative, multi-agent scientific reasoning loop**. 

Instead of jumping directly to an unverified conclusion, SAAR constructs a **dynamic causal knowledge graph**, identifies epistemic uncertainty, runs specialized domain simulators, queries the human investigator for high-information-gain observations, and conducts Bayesian belief updates until confidence satisfies a rigorous scientific threshold.

```
                               ┌────────────────────────────────────────────────────────┐
                               │               ORCHESTRATING REASONING AGENT             │
                               │          Hypothesis Generation & Uncertainty Scent     │
                               └───────────────────────────┬────────────────────────────┘
                                                           │
                                                           ▼
                ┌──────────────────────────────────────────────────────────────────────────────────┐
                │                           DYNAMIC CAUSAL GRAPH STORE                             │
                │                 Entities, Latent Properties, Hypotheses & Confidences            │
                └──────────────┬───────────────────────────┬───────────────────────────┬───────────┘
                               │                           │                           │
                               ▼                           ▼                           ▼
                 ┌───────────────────────────┐ ┌───────────────────────┐ ┌───────────────────────────┐
                 │     Perception Sensors    │ │  Domain Simulators    │ │  Human-in-the-Loop Cards  │
                 │ Multi-Modal Vision / Tab  │ │ GPR, Darcy, Keplerian │ │ Epistemic Uncertainty Qs  │
                 └───────────────────────────┘ └───────────────────────┘ └───────────────────────────┘
```

---

## ⚡ Key Capabilities & Architectural Pillars

### 1. Dynamic Directed Acyclic Graph (DAG) Engine
- Built on top of **NetworkX** and strict **Pydantic** validation models.
- Differentiates between:
  - **Physical Entities** (`road`, `culvert`, `tomato_foliage`, `exoplanet_host`)
  - **Measured Properties** (`soil_moisture: 42%`, `ndvi_index: 0.28`, `transit_depth: 1.4%`)
  - **Active Hypotheses** (`Pythium Root Rot`, `Subterranean Void Cavity`, `Binary Eclipse`)
  - **Evidence Links** (`supports`, `contradicts`, `causes`, `mitigates`, `measures`)

### 2. Bayesian Belief Updating & Uncertainty Minimization
- Tracks global and node-level uncertainty metrics:
  $$\text{Uncertainty}_{\text{global}} = 1.0 - \frac{1}{|V \cup E|} \sum_{x \in V \cup E} \text{Confidence}(x)$$
- Hypotheses compete dynamically. Confirmatory data shifts probability mass; disconfirmatory anomalies eliminate candidate nodes in real-time.

### 3. Multi-Domain Scientific Plugin Architecture
SAAR ships with specialized analytical plugins engineered with domain equations:
- 🌿 **Agriculture & Agronomy**:
  - Darcy’s Law soil water saturation & drainage percolation
  - Chlorophyll degradation & vegetative index tracking (NDVI/SPAD)
  - Pathogen incubation models (*Pythium*, *Fusarium*, Nitrogen deficiency)
- 🛣️ **Civil Infrastructure & Geotechnical**:
  - Ground Penetrating Radar (GPR) hyperbolic reflection void cavity detection
  - Hydraulic culvert intake flow simulations
  - AASHTO structural pavement load-bearing capacity
- 🪐 **Astrophysics & Exoplanetary Science**:
  - Keplerian orbital lightcurve transit fitting
  - Radial velocity Doppler centroid shift calculations ($K = 85.2 \text{ m/s}$)
  - Planetary mass vs. brown dwarf/stellar companion evaluation

### 4. Human-in-the-Loop Inquiry Cards (Active Learning)
- When topological graph entropy is high, SAAR formulates **Targeted Epistemic Inquiries**.
- Presents interactive, one-click confirmation chips or verified field observation inputs in the chat dialogue to maximize information gain with minimal human effort.

### 5. Multi-Format Scientific Export & Dossier Generation
- **Universal Export Engine**:
  - Clean Markdown (`.md`) with complete question-and-answer pairs, causal graphs, and passport statistics.
  - Formatted JSON (`.json`) with full structural taxonomy for machine-to-machine pipelines.
  - Interactive HTML Dossier with inline CSS styling for enterprise review.
  - Formatted Print/PDF output for lab and inspection field dispatches.
- **Copy QA Stream**: Single-click combined question-and-answer clipboard synthesis with context-aware `"Ask SAAR"` drill-down.

### 6. Zero-Latency Grounded Scientific Terminology (`asyncio.gather`)
- Employs parallel asynchronous dispatch (`asyncio.gather`) pairing deep causal reasoning ($~1,500\text{ ms}$) with rapid grounded lexical extraction ($~200\text{ ms}$).
- Effective perceived added latency is **0 ms**.
- Replaces disconnected public web scrapers with contextual domain extraction powered by the same single `GROQ_API_KEY` (or offline RAG/morphological fallbacks).
- Renders interactive badges directly beneath dialogue turns (`[ 📖 Pythium ultimum ]`) with one-click **"Ask SAAR to Deep-Dive"** exploratory analysis.

---

## 📂 Repository Layout

```
SAAR/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI REST server & WebSocket gateway
│   │   ├── schemas.py                  # Pydantic schema contracts & type validators
│   │   ├── graph_engine.py             # NetworkX causal knowledge graph manager
│   │   ├── dynamic_loop.py             # ReAct investigation loop driver
│   │   ├── vlm_service.py              # Multi-provider vision perception service
│   │   ├── rag_service.py              # Domain scientific literature retrieval (BM25)
│   │   ├── models/
│   │   │   └── saar_models.py          # Node, Edge, Evidence, Terminology & State models
│   │   ├── services/
│   │   │   ├── ingestion_service.py    # CSV/Excel parser & column profiler
│   │   │   ├── analytics_service.py    # Correlation, trend, & anomaly calculators
│   │   │   ├── reasoning_service.py    # Iterative scientific belief orchestrator
│   │   │   └── dictionary_service.py   # Grounded scientific terminology engine
│   │   └── plugins/
│   │       ├── base_plugin.py          # Scientific domain plugin contract
│   │       ├── agriculture_plugin.py   # Crop diagnostics & pathogen kinetics
│   │       ├── infrastructure_plugin.py# GPR & hydraulic flow simulation
│   │       └── astronomy_plugin.py     # Orbital mechanics & transit spectroscopy
│   └── requirements.txt                # Python backend dependencies
│
└── frontend/
    ├── src/
    │   ├── App.jsx                     # Core application orchestrator & layout
    │   ├── main.jsx                    # Root entry point with global ErrorBoundary
    │   ├── index.css                   # Refined scientific typography & light theme design system
    │   ├── api/
    │   │   └── client.js               # Axios REST client with error interceptors
    │   └── components/
    │       ├── ChatGPTView.jsx         # Conversational scientific interface
    │       ├── ChatAssistant.jsx       # Integrated sidebar chat with inquiry cards
    │       ├── KnowledgeGraphCanvas.jsx# Interactive SVG causal graph visualization
    │       ├── ToolRolloutBar.jsx      # Flowing scientific tool palette
    │       ├── ToolCanvasDrawer.jsx    # Side-drawer for interactive domain simulations
    │       ├── MarkdownResponse.jsx    # MathJax LaTeX, Markdown tables, & code formatting
    │       ├── ErrorBoundary.jsx       # Robust crash prevention & graceful degradation
    │       └── BenchmarkComparison.jsx # SAAR vs. Single-Pass VLM accuracy matrix
    └── package.json                    # Frontend dependencies & scripts
```

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** and **npm**

### 1. Clone the Repository
```bash
git clone https://github.com/kshitijsingh1-tech/SAAR.git
cd SAAR
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Start the FastAPI application:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```
API documentation will be available at: `http://127.0.0.1:8001/docs`

### 3. Frontend Setup
In a new terminal:
```bash
cd frontend
npm install
npm run dev
```
Open your browser at: `http://localhost:3000`

---

## 🧪 Scientific Verification & Workflows

| Mode | Input Type | Reasoning Strategy | Output Artifact |
| :--- | :--- | :--- | :--- |
| **Agricultural Failure Analysis** | Multi-day soil & plant sensor timeseries (CSV/Excel) | Darcy saturation curve + SPAD chlorophyll decay modeling | Pathogen diagnosis (*Pythium ultimum* vs. N-deficiency) with confidence rating |
| **Geotechnical Void Detection** | High-frequency ground inspection radar scan | Hyperbolic diffraction fitting + structural load estimation | Cavity depth profile & sinkhole collapse risk passport |
| **Exoplanetary Transit Validation** | Kepler photometer lightcurve & radial velocity timeseries | Limb-darkened transit fitting + Doppler shift centroid computation | Confirmed planetary candidate mass, radius, and orbital period |

---

## 🛡️ License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
