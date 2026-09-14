# SAAR — Master System Architecture Specification
**Platform:** Synthetic Auditable Autonomous Reasoner (SAAR)  
**Document Version:** 2.5.0 (Production Release)  
**Author:** Core Engineering & Systems Architecture Team  
**Scope:** Multi-Modal Visual Scientific Reasoning, Deterministic Kinematics DSP, Bayesian Adaptive Triage & Zero-Hardcoding Architecture

---

## 1. System Philosophy & Foundational Directives

The **SAAR** platform is engineered to replace opaque, single-pass visual heuristics with verifiable, multi-agent scientific reasoning and deterministic signal processing.

```
Conventional Monolithic AI:
Visual Observation ──────▶ [ Black-Box LLM / VLM ] ──────▶ Hallucinated Diagnostic Heuristic

SAAR Architecture:
Visual / Video / Tabular ──▶ [ Deterministic DSP & Perception ] ──▶ [ Dynamic Causal Graph Store ]
                                                                             │
                         ┌───────────────────────────────────────────────────┴─────────────────┐
                         ▼                                                                     ▼
             [ Domain Simulators & Plugins ]                                       [ Adaptive Inquiry Engine ]
             • 3x3 BWF Planar Homography                                           • Dynamic Information Gain
             • Savitzky-Golay Zero-Lag Filter                                      • Strict Tool Gating Protocol
             • Darcy Soil Hydrology Flow                                           • Formatted Report Synthesis
             • GPR Sub-base Void Wavefront                                                     │
                         │                                                                     │
                         └─────────────────────────────────┬───────────────────────────────────┘
                                                           ▼
                                            [ Auditable Diagnostic Verdict ]
```

### 1.1 The Zero-Hardcoding Invariant ([`AGENTS.md`](AGENTS.md))
1. **Pure Presentation Layer**: UI presentation components (`ImageInspector.jsx`, `PlotlyGraphViewer.jsx`, `ChatGPTView.jsx`, `ToolCanvasDrawer.jsx`) are strictly display layers. Hardcoded mock coordinates `[ymin, xmin, ymax, xmax]`, phantom bounding boxes, and scenario-matching conditionals (`if (isMonstera)...`) are forbidden.
2. **Epistemic Honesty**: If sensors or cameras cannot observe physical phenomena (e.g. subsurface root rot without sensor telemetry, 3D shuttle trajectory without calibrated camera homography), the engine reports unobservable states honestly rather than fabricating synthetic nodes.
3. **Dynamic Semantic Dispatch**: Analytical tools, queries, and diagnostics route dynamically via semantic attributes (`category === 'pathology'`, `domain === 'sports'`), not static ID lookup tables.
4. **Strict Session Isolation**: Every uploaded image, video, and dataset forms an independent, self-contained atomic session. Stale visual coordinates or telemetry from prior investigations never bleed across sessions.

---

## 2. High-Level System Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               FRONTEND LAYER (React 18 + Vite 5)                       │
│  ┌─────────────────────────┐  ┌──────────────────────────┐  ┌───────────────────────┐  │
│  │     ChatGPTView.jsx     │  │    ToolRolloutBar.jsx    │  │ ToolCanvasDrawer.jsx  │  │
│  │  Conversational Reasoner│  │ Floating Dynamic Unlocks │  │ Interactive Studio    │  │
│  └───────────┬─────────────┘  └────────────┬─────────────┘  └───────────┬───────────┘  │
│              │                             │                            │              │
│  ┌───────────▼─────────────┐  ┌────────────▼─────────────┐  ┌───────────▼───────────┐  │
│  │ AdaptiveInquiryCard.jsx │  │  MarkdownResponse.jsx    │  │ BadmintonDashboard.jsx│  │
│  │ Information-Gain Triage │  │ Dynamic Section Parser   │  │ GaitStudio / Sensor   │  │
│  └─────────────────────────┘  └──────────────────────────┘  └───────────────────────┘  │
└────────────────────────────────────────────┬───────────────────────────────────────────┘
                                             │ HTTP REST / WebSocket / File Streaming
┌────────────────────────────────────────────▼───────────────────────────────────────────┐
│                               BACKEND API GATEWAY (FastAPI)                            │
│  /api/investigate  •  /api/sports/badminton/*  •  /api/gait/*  •  /api/adaptive/*      │
└───────────────────┬─────────────────────────────────────────────────┬──────────────────┘
                    │                                                 │
┌───────────────────▼─────────────────────┐       ┌───────────────────▼──────────────────┐
│        DETERMINISTIC DSP PIPELINES      │       │     AI & AGENTIC REASONING SUITE     │
│  ┌───────────────────────────────────┐  │       │  ┌────────────────────────────────┐  │
│  │ Badminton Biomechanics Studio     │  │       │  │ Multimodal VLM Cascade         │  │
│  │ • 3x3 BWF Court Homography Matrix │  │       │  │ • Google Gemini 3.7/3.1 Flash  │  │
│  │ • BlazePose 33 3D Keypoints       │  │       │  │ • Groq Llama-3.2-Vision        │  │
│  │ • Multi-Signal Velocity Fusion    │  │       │  │ • Groq Llama-3.3-70b ReAct     │  │
│  └───────────────────────────────────┘  │       │  └────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │       │  ┌────────────────────────────────┐  │
│  │ ToddleAI Pediatric Gait Engine    │  │       │  │ Dynamic Causal Graph Store     │  │
│  │ • Savitzky-Golay Zero-Lag Filter  │  │       │  │ • NetworkX Directed Causal DAG │  │
│  │ • Sub-Frame Parabolic Peak Strike │  │       │  │ • Dynamic Bayesian Updating    │  │
│  │ • Sutherland (1988) Clinical Norms│  │       │  └────────────────────────────────┘  │
│  └───────────────────────────────────┘  │       │  ┌────────────────────────────────┐  │
│  ┌───────────────────────────────────┐  │       │  │ Adaptive Inquiry Engine        │  │
│  │ Sensor Analytics & Telemetry      │  │       │  │ • Entropy / Information Gain   │  │
│  │ • Bivariate Pearson r Scatter     │  │       │  │ • Competing Hypotheses Triage  │  │
│  │ • NxN Correlation Heatmap Matrix  │  │       │  │ • Tool Gating Orchestration    │  │
│  └───────────────────────────────────┘  │       │  └────────────────────────────────┘  │
└─────────────────────────────────────────┘       └──────────────────────────────────────┘
```

---

## 3. Multimodal Perception & VLM Cascading

The backend vision layer ([`backend/app/vlm_service.py`](backend/app/vlm_service.py)) implements an automated multi-provider fallback hierarchy:

```
                          [ Incoming Image / Visual Frame ]
                                          │
                     ┌────────────────────▼────────────────────┐
                     │ Google Gemini Vision Cascade            │
                     │ 1. gemini-3.7-flash (Optimal Reasoning) │
                     │ 2. gemini-3.1-flash-lite (Ultra-Fast)   │
                     └────────────────────┬────────────────────┘
                                          │ Rate Limit (429) / Quota Exceeded
                     ┌────────────────────▼────────────────────┐
                     │ Groq Llama-Vision Cascade               │
                     │ 1. llama-3.2-11b-vision-preview         │
                     │ 2. llama-3.2-90b-vision-preview         │
                     └────────────────────┬────────────────────┘
                                          │ Network Timeout / Offline Mode
                     ┌────────────────────▼────────────────────┐
                     │ Grounded Deterministic Offline Fallback │
                     │ Grounded Visual Anchors & Sensor Models │
                     └─────────────────────────────────────────┘
```

### 3.1 Spatial Bounding Box Coordinate System
- All grounded physical entities use normalized coordinates $[y_{\min}, x_{\min}, y_{\max}, x_{\max}]$ on a $[0, 1000]$ integer scale.
- Coordinates represent physical bounding extents on the original frame without aspect distortion.

---

## 4. Deterministic Kinematics & Biomechanical Engines

### 4.1 Badminton Biomechanics & Performance Studio
Located in [`backend/app/plugins/sports/badminton/`](backend/app/plugins/sports/badminton/):

1. **BWF Metric Court Homography ([`court_detector.py`](backend/app/plugins/sports/badminton/court_detector.py))**:
   - Detects court line boundary intersections and computes the planar perspective transform matrix $H$:
     $$\begin{bmatrix} X_w \\ Y_w \\ 1 \end{bmatrix} \sim H \begin{bmatrix} u \\ v \\ 1 \end{bmatrix}$$
   - Maps 2D camera pixels to international BWF dimensions ($13.40\text{m} \times 6.10\text{m}$ for doubles, $5.18\text{m}$ width for singles).
2. **Kinematic Chain Angular Velocities ([`shot_detector.py`](backend/app/plugins/sports/badminton/shot_detector.py))**:
   - Computes segment angular velocities: pelvis $\to$ trunk $\to$ shoulder $\to$ elbow extension $\to$ forearm pronation.
   - Detects overhead smashes by fusing three concurrent physical thresholds:
     1. Forearm/wrist linear velocity peak: $v_{\text{wrist}} \ge 45\text{ km/h}$.
     2. Elbow extension: $\theta_{\text{elbow}} \ge 140^\circ$.
     3. Forward trajectory velocity vector acceleration.
3. **Court Heatmap & Base Recovery ([`movement_analyzer.py`](backend/app/plugins/sports/badminton/movement_analyzer.py))**:
   - Integrates the player's center-of-mass (sacrum midpoint landmarks 23 & 24) across time.
   - Divides the court into a 9-zone tactical spatial grid and computes centroid recovery latency to the optimal defensive base ($x \approx 3.05\text{m}, y \approx 3.8\text{m}$).

### 4.2 ToddleAI Pediatric Gait Screening Engine
Located in [`backend/app/gait/`](backend/app/gait/):

1. **Zero Phase-Lag DSP Smoothing ([`smoothing.py`](backend/app/gait/events/smoothing.py))**:
   - 2nd-order Savitzky-Golay polynomial filter (`scipy.signal.savgol_filter`).
   - Adaptive physical window length: $\text{window} = \text{clamp}(\text{round}(\text{FPS} \times 0.23\text{s}), [5, 15])$.
   - Eliminates temporal phase delay, preserving exact physical heel-strike inflection peaks.
2. **Sub-Frame Parabolic Peak Heel-Strike Interpolation ([`heel_strike.py`](backend/app/gait/events/heel_strike.py))**:
   - Fuses dual landmark confidence: $\text{foot}_x = \frac{v_{\text{heel}} \cdot x_{\text{heel}} + v_{\text{ankle}} \cdot x_{\text{ankle}}}{v_{\text{heel}} + v_{\text{ankle}}}$.
   - Subtracts sacrum midpoint $\frac{x_{\text{L\_hip}} + x_{\text{R\_hip}}}{2}$ to isolate cyclic pendulum locomotion from room progression.
   - Refines discrete frame indices down to millisecond timestamps via quadratic vertex interpolation:
     $$p = \frac{1}{2} \frac{y_{\text{prev}} - y_{\text{next}}}{y_{\text{prev}} - 2y_{\text{curr}} + y_{\text{next}}}, \quad t_{\text{strike}} = t_{\text{frame}} + \frac{p}{\text{FPS}}$$
3. **Clinical Normative Metrics ([`metric_computer.py`](backend/app/gait/metrics/metric_computer.py))**:
   - **Cadence**: $\frac{60}{\bar{t}_{\text{step}}}$ steps/min.
   - **Robinson Asymmetry Index**: $100 \times \frac{|\bar{t}_L - \bar{t}_R|}{0.5(\bar{t}_L + \bar{t}_R)}$.
   - **Step Time CoV**: $100 \times \frac{\sigma}{\bar{t}_{\text{step}}}$.
   - Evaluated against **Dr. David Sutherland (1988) *"The Development of Mature Walking"*** normative ranges.

---

## 5. Adaptive Inquiry Engine & Strict Tool Gating Protocol

The **Adaptive Inquiry Engine** ([`backend/app/adaptive_inquiry.py`](backend/app/adaptive_inquiry.py), [`frontend/src/components/AdaptiveInquiryCard.jsx`](frontend/src/components/AdaptiveInquiryCard.jsx)) orchestrates interactive diagnostic triage:

```
                                  [ User Inquiry Prompt ]
                                             │
                        ┌────────────────────▼────────────────────┐
                        │ Adaptive Diagnostic Session Created    │
                        │ Status: "in_progress" (Questions Active)│
                        └────────────────────┬────────────────────┘
                                             │
                       ┌─────────────────────▼─────────────────────┐
                       │ STRICT TOOL GATING INVARIANT              │
                       │ • unlockedTools = ['dictionary', 'rag']   │
                       │ • Badminton Studio: LOCKED                │
                       │ • Tool Rollout Bar: LOCKED                │
                       │ • Message Header Badges: HIDDEN           │
                       └─────────────────────┬─────────────────────┘
                                             │
                       ┌─────────────────────▼─────────────────────┐
                       │ Interactive Multi-Turn Question Loop      │
                       │ Q1 ──▶ Option Click ──▶ Entropy Reduction │
                       │ Q2 ──▶ Option Click ──▶ Hypothesis Stable │
                       └─────────────────────┬─────────────────────┘
                                             │ All Questions Concluded (Confidence >= 75%)
                       ┌─────────────────────▼─────────────────────┐
                       │ DIAGNOSTIC ASSESSMENT CONCLUDED           │
                       │ • Status: "concluded"                     │
                       │ • Render: Elevated White Card (Photo 1)   │
                       │ • Section Headers: Purple #4338ca (h4)    │
                       │ • onAdaptiveInquiryComplete() Triggered   │
                       └─────────────────────┬─────────────────────┘
                                             │
                       ┌─────────────────────▼─────────────────────┐
                       │ TOOL UNLOCK & STUDIO LAUNCH               │
                       │ • unlockedTools = ['badminton', 'verdict']│
                       │ • Rollout Bar reveals Badminton Studio    │
                       │ • Message Badge: [🏸 Badminton Studio ➔]   │
                       │ • Card Action: [Launch Badminton Studio]  │
                       └───────────────────────────────────────────┘
```

### 5.1 Tool Gating Invariant Implementation
- While `msg.adaptiveConcern` is active and `!concludedSessions[index]`, the tool state is locked:
  ```javascript
  // App.jsx
  if (!adaptiveConcern) {
    detectAndUnlockTools(msgText, currentFiles, askRes);
  } else {
    // Keep domain studio locked while questions are active!
    setSessionTools(['dictionary', 'rag'], activeSessionId);
  }
  ```
- When the final question is answered, `onSessionComplete(session)` emits from `AdaptiveInquiryCard`, setting `concludedSessions[index] = true` and invoking `handleAdaptiveInquiryComplete(completedSession)`.
- The Badminton Studio becomes accessible via:
  1. Floating `ToolRolloutBar` icon.
  2. Concluded card action button: `[Launch Badminton Biomechanics Studio ➔]`.
  3. Assistant message header badge: `[🏸 Badminton Studio ➔]`.

---

## 6. Frontend Presentation & Styling System

### 6.1 Unified Elevated White Card Layout ([`MarkdownResponse.jsx`](frontend/src/components/MarkdownResponse.jsx))
- All diagnostic reports and concluded triage summaries render as a single elevated white card (`#ffffff` background, `1px solid #e2e8f0` border, `box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.05)`).
- Replaces the legacy nested green container (`.adaptive-concluded`) with a clean `.adaptive-conclusion-wrapper`.

### 6.2 Dynamic Numbered Section Parser
- Strips leading markdown hashes (`cleanHeading = trimmed.replace(/^#{1,6}\s*/, '').trim()`) before classification.
- Any numbered diagnostic heading (e.g. `### 1. Root Cause Finding`, `## 1. Locomotion Kinematics`, `1. Primary Root Cause Finding`) is automatically classified as `level: 4` (`h4`), rendering in **Purple `#4338ca`** with a full-width underline divider.
- Top document titles parse as `level: 3` (`h3`), rendering with an underline divider.
- Unnumbered subsections parse as `level: 5` (`h5`), rendering in bold navy.
- Ordered recommendations automatically parse inline priority badges: `[HIGH]`, `[MEDIUM]`, `[LOW]`, and `[CRITICAL]`.

---

## 7. Data Flow & State Synchronization

```
State Variable            Scope               Authority Source           Consumers
────────────────────────────────────────────────────────────────────────────────────────
sessions                  Global LocalStorage App.jsx                    ChatSidebar
allMessages               Global LocalStorage App.jsx                    ChatGPTView
sessionUnlockedTools      Per-Session Cache   App.jsx (setSessionTools)  ToolRolloutBar, Drawer
activeInvestigation       Active Session      FastAPI Backend            ImageInspector, Verdict
saarData                  Active Session      Kinematics DSP Pipelines   BadmintonDashboard, Gait
concludedSessions         Ephemeral / Message ChatGPTView.jsx            Badminton Studio Badge
```

---

## 8. REST API Contracts & Core Endpoints

| Endpoint | Method | Input Payload | Output Schema | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `/api/investigate` | `POST` | `domain`, `preset_id`, `image` | `InvestigationResponse` | Multi-phase autonomous image investigation |
| `/api/sports/badminton/analyze` | `POST` | `multipart/form-data` (MP4/MOV) | `BadmintonAnalysisResponse` | 3D pose, homography, strokes & fatigue |
| `/api/sports/badminton/sample` | `GET` | None | `BadmintonAnalysisResponse` | Fast reference rally analysis |
| `/api/gait/analyze-video` | `POST` | `multipart/form-data` (MP4/MOV) | `GaitAnalysisResponse` | 11-stage pediatric gait screening |
| `/api/adaptive/start` | `POST` | `investigation_id`, `concern` | `AdaptiveSessionModel` | Initiates information-gain triage inquiry |
| `/api/adaptive/answer` | `POST` | `session_id`, `option_id` | `AdaptiveSessionModel` | Submits response and updates belief state |
| `/api/saar/csv/upload` | `POST` | `multipart/form-data` (CSV/XLSX) | `SaarCsvResponse` | Parses telemetry, correlations & timelines |

---

## 9. Verification & Quality Assurance Protocols

1. **Deterministic Unit Tests**:
   - [`test_dynamic_synthesis.py`](test_dynamic_synthesis.py): Validates multi-domain synthesis without preset contamination.
   - [`test_gait_accuracy.py`](test_gait_accuracy.py): Validates heel-strike peak interpolation and asymmetry indices.
   - [`test_image_entry_and_tools.py`](test_image_entry_and_tools.py): Validates visual anchor parsing and tool dispatch.
2. **Frontend Production Build**:
   - `npm run build` executed in Vite 5 with zero warnings and zero TypeScript/JSX errors.
3. **End-to-End Browser Subagent Testing**:
   - Headless browser automated sessions verify interactive triage, tool gating lock/unlock lifecycle, and video player playback.
