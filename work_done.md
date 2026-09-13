# SAAR Engineering Log: Solved Problems & Feature Ledger (`work_done.md`)

> **MANDATORY DIRECTIVE FOR ALL AGENTS & DEVELOPERS**:
> Always update this ledger whenever a bug is fixed, a feature is implemented, or an architectural workflow is refactored.
> **Rule of Non-Regression**: NEVER remove, overwrite, or degrade any functionality listed in this document without explicit authorization and a documented migration path.

---

## Table of Contents
1. [Chat Composer: Direct CSV & Local File Path Pasting](#1-chat-composer-direct-csv--local-file-path-pasting)
2. [Sensor Data Tool: Dynamic Multi-Channel Telemetry Ingestion](#2-sensor-data-tool-dynamic-multi-channel-telemetry-ingestion)
3. [Botanical Investigation: Rose Chip Budding Graft Journey Dataset](#3-botanical-investigation-rose-chip-budding-graft-journey-dataset)
4. [Tool Isolation & Domain Boundary Enforcement](#4-tool-isolation--domain-boundary-enforcement)
5. [Strict Zero-Hardcoding & Single Source of Truth Alignment](#5-strict-zero-hardcoding--single-source-of-truth-alignment)
6. [Backend Service Orchestration & Port Architecture](#6-backend-service-orchestration--port-architecture)
7. [Clean Response Formatting: Thought Process Capsule for Dataset Ingestion](#7-clean-response-formatting-thought-process-capsule-for-dataset-ingestion)
8. [Authentic Photographic Milestones & Bi-Directional Visual Grounding](#8-authentic-photographic-milestones--bi-directional-visual-grounding)
9. [Image Metadata Tagging & Multi-Iteration Milestone Architecture](#9-image-metadata-tagging--multi-iteration-milestone-architecture)
10. [Single Metadata Context Box with Standardized Format & Sequential Ingestion](#10-single-metadata-context-box-with-standardized-format--sequential-ingestion)
11. [Analytical Inquiry Reasoning Engine Overhaul & Gemini Model Re-alignment](#11-analytical-inquiry-reasoning-engine-overhaul--gemini-model-re-alignment)
12. [Safe Upstream Integration of Origin/Main with Non-Regression Multimodal Invariants](#12-safe-upstream-integration-of-originmain-with-non-regression-multimodal-invariants)
13. [Exact Alignment of Frontend with Origin/Main](#13-2026-09-13-exact-alignment-of-frontend-with-originmain)
14. [Resolution of Badminton Studio Network Error & Complete Multimodal Unification](#14-2026-09-13-resolution-of-badminton-studio-network-error--complete-multimodal-unification)

---

## 1. Chat Composer: Direct CSV & Local File Path Pasting
- **Date Solved**: 2026-09-13
- **Primary Files**:
  - [`frontend/src/components/ChatGPTView.jsx`](file:///d:/bytebuild/frontend/src/components/ChatGPTView.jsx)
  - [`backend/app/main.py`](file:///d:/bytebuild/backend/app/main.py)
  - [`frontend/src/App.jsx`](file:///d:/bytebuild/frontend/src/App.jsx)

### Problem Description
Users attempting to paste tabular CSV data or copied CSV files directly into the chat composer input box could not attach them. In some cases, pasting was completely hijacked; in others, pasting a file copied from Windows File Explorer or VS Code resulted in raw strings or nothing happening.

### Root Causes
1. **Text Length Hijack**: `ChatGPTView.jsx` contained a blanket rule `if (text.length > 220) e.preventDefault(); setTextSnippet(...)` which trapped any multi-row CSV into a temporary draft note pill instead of creating a dataset attachment.
2. **Browser OS Clipboard Sandbox**: In Windows Chrome/Edge, pressing `Ctrl+C` on a `.csv` file in Windows File Explorer produces `CF_HDROP`, which web browsers block from `clipboardData.files` for non-image files due to security policies.
3. **Path Pasting Unhandled**: When copying a file from VS Code (`Ctrl+C` or "Copy Path"), the clipboard contains the plain text path (e.g. `d:\bytebuild\rose_chip_budding_graft_journey_sensors.csv`). The composer had no handler to resolve local paths into files.

### Implemented Solution & Non-Regression Rules
- **Tabular Delimiter Detector**: Added delimiter detection (commas, tabs, semicolons across lines $\ge 2$) in `handlePaste`. It automatically creates a `new File([csvBlob], '<column>_dataset.csv', { type: 'text/csv' })` and places it into `attachedFiles`.
- **Backend File Path Resolver**: Created `GET /api/saar/read-file?path=...` in `backend/app/main.py` allowing secure resolution of local workspace file paths.
- **Async Path Paste Interceptor**: In `ChatGPTView.jsx`, if pasted text ends with `.csv`, `.tsv`, `.xlsx`, `.pdf`, etc., it automatically calls `/api/saar/read-file`, fetches the file blob, and attaches it as a spreadsheet pill.
- **Multiple Attachment Modalities Supported**:
  1. Paste raw CSV tabular text directly from any editor.
  2. Paste file path directly (e.g. `d:\bytebuild\dataset.csv`).
  3. Drag and drop file onto composer.
  4. Paperclip file selector button.

---

## 2. Sensor Data Tool: Dynamic Multi-Channel Telemetry Ingestion
- **Date Solved**: 2026-09-13
- **Primary Files**:
  - [`backend/app/services/reasoning_service.py`](file:///d:/bytebuild/backend/app/services/reasoning_service.py)
  - [`frontend/src/components/PlotlyGraphViewer.jsx`](file:///d:/bytebuild/frontend/src/components/PlotlyGraphViewer.jsx)
  - [`backend/app/main.py`](file:///d:/bytebuild/backend/app/main.py)

### Problem Description
When a user uploaded or entered a custom CSV dataset, the Sensor Telemetry drawer (`PlotlyGraphViewer.jsx`) failed to display the uploaded data and instead always fell back to a hardcoded 30-day synthetic tomato chlorosis plot or highway sub-base plot.

### Root Causes
1. **Missing Telemetry Payload**: `reasoning_service.py:get_report` extracted perceptual concepts and correlations but did not structure raw numerical timeseries observations into a serialized `telemetry` object for frontend charting.
2. **Hardcoded Component Defaults**: `PlotlyGraphViewer.jsx:sensorSuite` only checked `domain.includes('infra')` and otherwise returned hardcoded tomato chlorosis data, completely ignoring `saarData` and `activeInvestigation`.

### Implemented Solution & Non-Regression Rules
- **Backend Telemetry Serialization**: Added structured `telemetry` dictionary in `reasoning_service.py:get_report` containing `channels`, `units`, `timestamps`, `milestones`, `rowCount`, and `columnCount`.
- **Dynamic Channel Suite**: Updated `PlotlyGraphViewer.jsx:sensorSuite` to prioritize `saarData?.telemetry || activeInvestigation?.telemetry`.
- **Dynamic Bivariate Regression**: Dropdowns for variable X and variable Y automatically populate with all available channels from the dataset, computing empirical Pearson $r$, $R^2$, and regression slope/intercept dynamically.
- **Dynamic Pairwise Heatmap**: Computes full $N \times N$ correlation matrix on-the-fly for all numerical channels in the dataset.
- **Dynamic Milestone Mapping**: Milestones dynamically align with either index or date/timestamp strings from the active dataset.

---

## 3. Botanical Investigation: Rose Chip Budding Graft Journey Dataset
- **Date Solved**: 2026-09-13
- **Primary Files**:
  - [`rose_chip_budding_graft_journey_sensors.csv`](file:///d:/bytebuild/rose_chip_budding_graft_journey_sensors.csv)
  - [`test_rose_csv_upload.py`](file:///d:/bytebuild/test_rose_csv_upload.py)

### Problem Description
To rigorously evaluate SAAR against Wikipedia botanical chip budding photography (`Rose_chip_budding,_right_after_grafting.jpg`), a multi-month synthetic botanical sensor dataset was required to model the entire journey from graft incision through cambial union, vascular reconnection, and shoot expansion.

### Implemented Solution & Non-Regression Rules
- Created `rose_chip_budding_graft_journey_sensors.csv` spanning **192 consecutive days** (Day 0 to Day 192) across **21 botanical, environmental, and electrophysiological parameters**:
  - `cambium_bioimpedance_kohm` (electrical signature of callus bridge formation)
  - `sub_tape_rh_pct` (parafilm wrap humidity retention)
  - `stem_sap_flow_rate_ml_hr` & `stem_water_potential_mpa` (xylem bridge restoration)
  - `spad_chlorophyll_index` & `psii_quantum_yield_fv_fm` (apical bud photosynthetic competence)
  - Microclimatic variables: `substrate_moisture_vwc_pct`, `substrate_temp_c`, `substrate_ec_ds_m`, `substrate_ph`, `ambient_temp_c`, `ambient_rh_pct`, `vpd_kpa`
  - Acoustic emission sensors for xylem cavitation events (`acoustic_emission_events_hr`)
  - Stem diameter micro-variation (`stem_diameter_variation_um`)
  - Union healing score & scion necrosis risk index.
- Verified that uploading this dataset to `/api/saar/upload` extracts all 16 continuous telemetry channels and 193 timesteps cleanly.

---

## 4. Tool Isolation & Domain Boundary Enforcement
- **Date Solved**: 2026-09-12
- **Primary Files**:
  - [`frontend/src/components/ToolCanvasDrawer.jsx`](file:///d:/bytebuild/frontend/src/components/ToolCanvasDrawer.jsx)
  - [`frontend/src/components/GaitDashboard.jsx`](file:///d:/bytebuild/frontend/src/components/GaitDashboard.jsx)
  - [`frontend/src/App.jsx`](file:///d:/bytebuild/frontend/src/App.jsx)

### Problem Description
Specialized biomechanical tools (specifically the ToddleAI Pediatric Gait Analysis tool) were inadvertently appearing or persisting in sessions belonging to botanical or civil infrastructure investigations.

### Root Causes
Cross-session state contamination where previously opened specialized drawers remained active when the user switched to or created a plant analysis investigation.

### Implemented Solution & Non-Regression Rules
- Added strict domain isolation guards:
  - ToddleAI gait dashboard only activates when `selectedDomain === 'pediatric'` or `activeSessionId` is explicitly a pediatric gait session.
  - Reset active tool drawer states upon session transition.
  - Agricultural and civil domains strictly display their domain-specific visual anchors, RAG radar, and sensor telemetry suites.

---

## 5. Strict Zero-Hardcoding & Single Source of Truth Alignment
- **Date Solved**: 2026-09-11 through 2026-09-13
- **Primary Files**:
  - [`AGENTS.md`](file:///d:/bytebuild/AGENTS.md)
  - [`.agents/rules/no_hardcoding.md`](file:///d:/bytebuild/.agents/rules/no_hardcoding.md)
  - [`frontend/src/components/ImageInspector.jsx`](file:///d:/bytebuild/frontend/src/components/ImageInspector.jsx)
  - [`frontend/src/components/KnowledgeGraphCanvas.jsx`](file:///d:/bytebuild/frontend/src/components/KnowledgeGraphCanvas.jsx)

### Architectural Invariant
- **Rule**: UI presentation components are strictly display and interaction layers.
- **Rule**: Zero hardcoded coordinates `[ymin, xmin, ymax, xmax]`, phantom labels, or scenario-matching conditionals (`if (isMonstera)`, `if (isTomato)`).
- **Rule**: Empty states over fake fallbacks. If visual anchors or sensor nodes are absent, display a clean loading or empty state rather than inventing synthetic default boxes.

---

## 6. Backend Service Orchestration & Port Architecture
- **Date Solved**: 2026-09-13
- **Configuration Details**:
  - **Port 8001**: Primary FastAPI Backend Server (`python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload`)
  - **Port 3000**: Vite React Frontend Server (`npm run dev`)
  - **Environment Variable**: `VITE_API_URL` defaults to `http://127.0.0.1:8001` in [`frontend/src/api/client.js`](file:///d:/bytebuild/frontend/src/api/client.js).

### Troubleshooting Protocol (WinError 10013)
- If `uvicorn` fails with `[WinError 10013] Access forbidden`, check if a background process or prior daemon is already bound to port 8001. Do not start secondary ports (e.g. 8002) without updating `VITE_API_URL`, as the frontend communicates with port 8001.

---

## 7. Clean Response Formatting: Thought Process Capsule for Dataset Ingestion
- **Date Solved**: 2026-09-13
- **Primary Files**:
  - [`frontend/src/App.jsx`](file:///d:/bytebuild/frontend/src/App.jsx)
  - [`frontend/src/components/ChatGPTView.jsx`](file:///d:/bytebuild/frontend/src/components/ChatGPTView.jsx)

### Problem Description
When uploading or pasting a dataset, the chat assistant dumped raw technical boilerplate into the response body:
- Bulleted lists of telemetry variable counts, observation counts, and topological edge counts.
- A hardcoded fallback string for tomato: `"Root cause mechanism traced to rhizosphere acidification and iron transport blockage."` which appeared even during rose graft analysis.
- The sleek collapsible "Thought Process" capsule (`ThoughtProcessPill`), which was already standard for image and video investigations, was omitted for CSV dataset uploads.

### Root Causes
In [`frontend/src/App.jsx:812`](file:///d:/bytebuild/frontend/src/App.jsx#L812) and [`frontend/src/App.jsx:958`](file:///d:/bytebuild/frontend/src/App.jsx#L958), the CSV response builder directly concatenated raw telemetry counts and a hardcoded tomato diagnostic essence string into `responseText` instead of building a structured `thoughtProcess` object.

### Implemented Solution & Non-Regression Rules
- **Encapsulated Technical Telemetry**: Replaced the boilerplate bullet points with a structured `thoughtProcess` object:
  - `title`: Execution duration (e.g. `Thought for 1.9s`)
  - `summary`: Ingested $N$ variables · Discovered $E$ causal edges · Confidence $C$%
  - `steps`: Step-by-step breakdown of telemetry ingestion, feature extraction, causal topology computation, belief updating, and sensor tool synchronization.
- **Removed Hardcoded Fallback**: Completely eliminated the tomato chlorosis string from CSV responses. Responses now dynamically present clean high-signal summaries or direct inquiry answers.
- **Enforced Non-Regression**: All dataset uploads across both `handleSendMessage` and `handleUploadSensorFile` now use `ThoughtProcessPill` exclusively for technical parsing telemetry.

---

## 8. Zero Hardcoding: Dynamic Dataset-Driven Milestones & Bi-Directional Visual Grounding
- **Date Solved**: 2026-09-13
- **Primary Files**:
  - [`backend/app/services/reasoning_service.py`](file:///d:/bytebuild/backend/app/services/reasoning_service.py)
  - [`rose_chip_budding_graft_journey_sensors.csv`](file:///d:/bytebuild/rose_chip_budding_graft_journey_sensors.csv)
  - [`frontend/src/components/PlotlyGraphViewer.jsx`](file:///d:/bytebuild/frontend/src/components/PlotlyGraphViewer.jsx)
  - [`frontend/src/components/ImageInspector.jsx`](file:///d:/bytebuild/frontend/src/components/ImageInspector.jsx)
  - [`frontend/src/components/ToolCanvasDrawer.jsx`](file:///d:/bytebuild/frontend/src/components/ToolCanvasDrawer.jsx)
  - [`frontend/src/App.jsx`](file:///d:/bytebuild/frontend/src/App.jsx)
  - [`backend/app/vlm_service.py`](file:///d:/bytebuild/backend/app/vlm_service.py)

### Problem Description & User Critique
1. The initial implementation created a static file `frontend/src/data/roseMilestones.js` containing hardcoded rose chip budding milestones and imported it directly into UI presentation components.
2. The user rightly flagged: *"hardcoded whyy, our system might be used for other plants as well"*.
3. Per `AGENTS.md` directive §1 ("Zero Hardcoded Scenario / Preset Logic in UI Components") and §4 ("Single Source of Truth"), hardcoding species-specific milestones in UI presentation components violates architectural invariants and prevents dynamic scaling to other plants (e.g. apple grafting, tomato trials, grapevine propagation) or non-botanical domains.

### Root Causes
- Hardcoding static milestone dictionaries in the frontend presentation layer instead of dynamically extracting them from the uploaded dataset or backend telemetry data contract.

### Implemented Solution & Non-Regression Invariants
1. **Completely Deleted Static File**:
   - Deleted `frontend/src/data/roseMilestones.js`.
   - Removed all static milestone imports and species-specific conditionals (`isRoseDataset`, etc.) from both `PlotlyGraphViewer.jsx` and `ImageInspector.jsx`.
2. **Dynamic Dataset-Driven Ingestion in Backend (`reasoning_service.py`)**:
   - In `backend/app/services/reasoning_service.py`, `get_report` now dynamically analyzes dataset observations:
     - Detects image columns (`photograph_url`, `image`, `photo`, `visual`) and stage/intervention columns (`growth_stage`, `stage`, `phase`, `intervention`, `milestone`).
     - Extracts milestones `{ day, timestamp, label, badge, color, stage, date, url, description }` dynamically from the active dataset rows.
     - Works universally for ANY plant or infrastructure dataset uploaded by users.
3. **Dataset as Empirical Source of Truth**:
   - Added the `photograph_url` column directly into `rose_chip_budding_graft_journey_sensors.csv` mapping authentic Wikimedia Commons photographic records to their exact recording dates.
4. **Pure Presentation Layer in UI**:
   - [`PlotlyGraphViewer.jsx`](file:///d:/bytebuild/frontend/src/components/PlotlyGraphViewer.jsx) strictly consumes `activeTelemetry.milestones`. If milestones exist, it renders the photostrip and inspection card; if none exist, it displays an honest clean state.
   - [`ImageInspector.jsx`](file:///d:/bytebuild/frontend/src/components/ImageInspector.jsx) dynamically receives `milestones` as a prop and only displays the `Milestone:` selector dropdown if milestone images are present in the active dataset/investigation.
5. **State Isolation & Telemetry Preservation**:
   - In `App.jsx` and `ToolCanvasDrawer.jsx`, `onPasteImageUrl` supports `preserveTelemetry=true`, ensuring switching milestone photographs does not erase active CSV telemetry.
6. **Local Asset Architecture & Backend VLM Resolution**:
   - All 8 images reside in `frontend/public/rose_graft_milestones/` for instant, offline-resilient loading. `vlm_service.py` resolves local filesystem paths to feed raw bytes directly to Gemini, Groq, or OpenAI VLMs.

---

## 9. Image Metadata Tagging & Multi-Iteration Milestone Architecture
- **Date Solved**: 2026-09-13
- **Primary Files**:
  - [`frontend/src/components/ChatGPTView.jsx`](file:///d:/bytebuild/frontend/src/components/ChatGPTView.jsx)
  - [`frontend/src/App.jsx`](file:///d:/bytebuild/frontend/src/App.jsx)
  - [`backend/app/schemas.py`](file:///d:/bytebuild/backend/app/schemas.py)
  - [`backend/app/vlm_service.py`](file:///d:/bytebuild/backend/app/vlm_service.py)
  - [`backend/app/dynamic_loop.py`](file:///d:/bytebuild/backend/app/dynamic_loop.py)
  - [`backend/app/main.py`](file:///d:/bytebuild/backend/app/main.py)
  - [`frontend/src/api/client.js`](file:///d:/bytebuild/frontend/src/api/client.js)

### Problem Description & User Goal
Users uploading images for multi-iteration botanical or clinical analysis (e.g. Day 1 incision photo, Day 15 callus photo, Day 30 vegetative shoot photo) had no mechanism to annotate or label images with metadata. Images were treated as anonymous, unlabelled blobs. Furthermore, when users uploaded new photos across subsequent conversation iterations, the system lacked a mechanism to accumulate and sequence them chronologically into active investigation milestones.

### Implemented Solution & Non-Regression Invariants
1. **Interactive Image Metadata Tagging Modal & Click-to-Tag Ergonomics (`ChatGPTView.jsx`)**:
   - Thumbnail previews for all attached image files in the chat composer across paste, drag-and-drop, and file selector uploads.
   - **Click-to-Tag Interaction**: Users click directly anywhere on the image pill/thumbnail to open the glassmorphic metadata modal (eliminating clutter from separate tag buttons).
   - Dismiss button `[X]` utilizes event stopping (`e.stopPropagation()`) so card dismissal does not trigger metadata editing.
   - Configurable metadata parameters:
     - **Milestone Day #**: (e.g. `1`, `10`, `30`).
     - **Developmental Stage / Action**: (e.g. `Scion Bud Attached`, `Callus Bridge`, `First Foliar Expansion`).
     - **Camera Perspective / Angle**: (`Lateral (Side View)`, `Apical (Top View)`, `Macro Cut Surface`, `Sagittal`, `Frontal`, `Substrate/Root Zone`).
     - **Clinical / Empirical Notes**: (e.g. `Parafilm wrap intact, 95% sub-tape RH`).
     - **Stage Quick Chips**: Instant presets for rapid tagging.
   - Colored badge chips (`DAY 1`, `DAY 15`) and stage labels displayed directly on attachment pills in real time.
   - If an image is untagged, a subtle prompt (`🏷️ Click to add metadata`) invites metadata specification.
2. **Batch Auto-Sequence Helper**:
   - When $\ge 2$ images are attached simultaneously, an auto-sequence bar allows one-click assignment of sequential days (`Day 1, Day 10, Day 20...`) across all attached frames.
3. **Multi-Iteration Accumulation Protocol (`App.jsx`)**:
   - `executeImageInvestigation` extracts metadata and converts user-tagged images into canonical `DynamicMilestone` objects.
   - Merges newly uploaded milestone frames with existing session milestones rather than overwriting them, preserving historical iterations across multi-turn chats.
4. **Backend Comparative Multi-Image Reasoning (`vlm_service.py` & `schemas.py`)**:
   - `InvestigationRequest` accepts `image_metadata: List[ImageMetadataItem]`.
   - `vlm_service.py` embeds milestone headers directly alongside inline image parts in VLM payloads, enabling Gemini/Groq/OpenAI to run comparative temporal and cross-stage differential analysis.
5. **Universal UI Synchronization & 30-Day Timeline Milestone Pinning (`PlotlyGraphViewer.jsx`, `ToolCanvasDrawer.jsx`, `SaarFindingsPanel.jsx`)**:
   - `PlotlyGraphViewer.jsx`: Directly receives dynamic milestones via props, `activeTelemetry.milestones`, and `investigationData.milestones`.
   - **Zero Hardcoding Invariant**: Replaced static fallback milestones `{ day: 6, day: 14, day: 22 }` with dynamically mapped user milestones. Pinned specimen photos render at their exact assigned days (e.g. Day 1, Day 10, Day 20) with vertical milestone dashed lines, camera pin annotations (`DAY 10 📷`), and interactive developmental stage labels.
   - **Interactive Photostrip & Inspection**: The photostrip renders the specimen thumbnails and stages. Clicking any timeline marker or photostrip card opens the photo inspection card with quick action to open in the Image Analysis Screen or inquire in Chat.
   - `ImageInspector.jsx`: The milestone dropdown lists user-uploaded photos by their tagged stages, allowing instant switching between iterations.
   - **Simultaneous CSV Dataset & Image Upload (`App.jsx`)**: When users attach both a dataset CSV and specimen photos in the chat composer, the CSV is ingested to extract continuous sensor channels, statistical covariance, and time series data, while the photos are pinned as authentic milestones directly onto the 30-day sensor telemetry graph.

---

## 10. Single Context Text Box & Sequential Two-Stage Multimodal Ingestion Pipeline
- **Date Solved**: 2026-09-13
- **Primary Files**:
  - [`frontend/src/components/ChatGPTView.jsx`](file:///d:/bytebuild/frontend/src/components/ChatGPTView.jsx)
  - [`frontend/src/App.jsx`](file:///d:/bytebuild/frontend/src/App.jsx)
  - [`backend/app/schemas.py`](file:///d:/bytebuild/backend/app/schemas.py)
  - [`backend/app/vlm_service.py`](file:///d:/bytebuild/backend/app/vlm_service.py)
  - [`backend/app/dynamic_loop.py`](file:///d:/bytebuild/backend/app/dynamic_loop.py)

### Problem Description & User Goal
The initial metadata modal presented multiple segregated input fields (Day #, Developmental Stage, Presets, Camera Perspective dropdown, and Notes). This constrained users to predefined botanical schemas and added unnecessary UI friction. The user explicitly requested:
> *"i dont want multiple areas since we might need to tell aour system some info in diffferent context. what i want is a text box only which is analysed first before image analysis and then the image r file analysis is done and the analysis of text box is attached to the image or file analysis"*

### Root Cause Analysis
Rigid input fields assumed specific biological or architectural forms and could not accommodate arbitrary instructions, clinical summaries, or variable multi-domain scenarios. Furthermore, text context previously was merely passed as metadata tags without an explicit, structured preliminary analysis phase prior to VLM visual perception.

### Implemented Solution & Non-Regression Invariants
1. **Single Spacious Context Text Area & Canonical Format Specification (`ChatGPTView.jsx`)**:
   - Eliminated all segregated inputs, presets, and perspective dropdowns from the modal.
   - **Canonical Format Instruction**: Explicitly specifies the required syntax: `info(example: data,name,time etc) : message for ai`. Clarifies that no extra fields or info are needed. Specimen metadata (day, milestone, timestamp, or condition) goes before the colon, and instructions/questions for the AI go after.
   - **Smart Delimiter Engine**: Implemented a timestamp-resilient colon finder on both frontend and backend that skips internal time colons (e.g. `14:00`, `12:30:45`) so time values in the info part do not falsely trigger separation.
   - **Full Page Theme Matching**: Overhauled the modal card styling to strictly utilize the design system's CSS tokens (`var(--bg-card)`, `var(--border-color)`, `var(--text-main)`, `var(--input-bg)`, `var(--primary)`, `var(--primary-bg)`). The modal, textarea, thumbnail container, and buttons seamlessly adapt to dark, light, and purple themes.
   - Attached pill cards render the dynamic Day badge (e.g. `DAY 10`) and a theme-adaptive context preview snippet.
2. **Stage 1 (Text-First Analysis Engine in `vlm_service.py`)**:
   - `VLMService.analyze_context_text` executes **before** visual image/file perception.
   - Leverages fast LLM extraction (`_call_text_analyzer_llm` across Gemini Flash / Groq LLaMA) with deterministic keyword fallback to parse:
     - `milestone`: `{ day, stage, milestone_label }` for timeline graph pinning.
     - `focus_targets`: 2–5 specific physical entities the VLM must ground.
     - `hypotheses`: testable scientific hypotheses extracted from user text.
     - `context_summary`: concise synthesis of user context.
3. **Stage 2 (Context-Guided Visual Grounding in `vlm_service.py`)**:
   - The Stage 1 extracted targets and hypotheses are injected as high-priority prompt parts (`[PRIOR CONTEXT ANALYSIS (STAGE 1 - ANALYZED FIRST)]`) in the VLM payload.
   - The VLM prioritizes detecting, bounding, and testing the exact structures identified in Stage 1.
4. **Attachment & Telemetry Synchronization (`dynamic_loop.py` & `App.jsx`)**:
   - `InvestigationResponse` attaches `text_context_analysis` and generated `telemetry.milestones`.
   - `App.jsx` dynamically pins the extracted milestone onto the 30-day timeline graph in `PlotlyGraphViewer.jsx`.
   - Assistant thought process displays Stage 1 step (`Stage 1 (Text-First): Analyzed context into...`) and prepends the Stage 1 context analysis to the final scientific findings.

---

## 11. Overhaul of Analytical Inquiry Reasoning Engine ("Help Me With This Analysis") & Multi-Provider Model Resilience
- **Date Solved**: 2026-09-13
- **Primary Files**:
  - [`backend/app/services/reasoning_service.py`](file:///d:/bytebuild/backend/app/services/reasoning_service.py)
  - [`backend/app/vlm_service.py`](file:///d:/bytebuild/backend/app/vlm_service.py)
  - [`backend/app/models/saar_models.py`](file:///d:/bytebuild/backend/app/models/saar_models.py)
  - [`frontend/src/components/ChatGPTView.jsx`](file:///d:/bytebuild/frontend/src/components/ChatGPTView.jsx)

### Problem Description & User Goal
When users submitted broad analytical inquiries such as `"help me with this analysis"`, `"explain the findings"`, or `"what is the root cause?"`, the system previously produced jarring, suboptimal responses stating:
> *"The uploaded dataset does not contain a column matching 'help, me, this, analysis'..."*
with an empty table and meaningless "COLUMN DATA GAP" notices.

### Root Cause Analysis
1. **False Column Match Heuristic in `reasoning_service.py`**:
   The engine naively split user queries into tokens and searched for matching CSV column names. When no column was literally named `"help"` or `"analysis"`, it treated the high-level analytical request as a failed column lookup.
2. **Missing Structured State Registration in `register_visual_investigation`**:
   Visual investigations from `/api/investigate` previously left `state.features` and `state.observations` empty, depriving downstream reasoning tasks of structured knowledge about grounded visual entities and their confidence scores.
3. **Outdated API Candidate Models in `vlm_service.py`**:
   `synthesize_reasoning_explanation` and VLM callers had outdated model candidate lists (e.g. attempting deprecated `gemini-1.5-flash` or non-existent Groq names), causing live calls to fail with 404/429 and forcing rudimentary fallbacks.

### Implemented Solution & Non-Regression Invariants
1. **Explicit Analytical Inquiry Intent Detection (`reasoning_service.py`)**:
   - Implemented regex intent recognition (`r'\bhelp\b'`, `r'\banalyze\b'`, `r'\banalysis\b'`, `r'\bsummar(?:y|ize)\b'`, `r'\broot\s*cause\b'`, etc.) and expanded conversational stop-words (`help`, `me`, `please`, `this`, `that`, `analysis`, `analyze`, `explain`, `overview`).
   - Meta-inquiries bypass column-name searching and instead trigger the construction of a comprehensive multi-modal **Investigation Brief**.
2. **Complete State Representation for Visual Investigations (`register_visual_investigation`)**:
   - Transforms all grounded visual nodes into structured `Feature` (with `SemanticRole.STATE`) and `Observation` items (with confidence %, status, category, and bounding box coordinates).
   - Records `visual_conclusion`, `text_context` (Stage 1 milestones/hypotheses), and `vlm_provider` on `InvestigationState`.
   - Stores active state under `self._investigations[inv_id]` and `self._investigations["latest"]`.
3. **Multi-Model Provider Realignment & Thinking-Safe Payloads (`vlm_service.py`)**:
   - Realigned Gemini candidates to active Google AI Studio models: `gemini-3.5-flash`, `gemini-3.6-flash`, `gemini-3.1-flash-lite`, `gemini-flash-latest`.
   - Realigned Groq candidates to active endpoint models: `qwen/qwen3.8-27b`, `qwen/qwen3.6-27b`, `openai/gpt-oss-120b`, `llama-3.3-70b-versatile` with required `User-Agent` headers.
   - Added OpenRouter backstop for maximum uptime resilience.
4. **Structured Scientific Diagnostic Matrix**:
   - Both live LLM prompts and deterministic offline fallbacks now produce a structured 5-part scientific report:
     1. Executive Diagnostic Summary (root cause isolation)
     2. Grounded Evidence & Parameter Matrix (markdown table of entities, categories, confidence, and significance)
     3. Causal Mechanism Chain (`Root Cause -> Intermediate State -> Observable Symptom`)
     4. Prescriptive Action Plan & Next Steps (domain-specific interventions)
     5. Definitive Bottom Line.

---

## 12. Safe Upstream Integration of Origin/Main with Non-Regression Multimodal Invariants
**Date Solved**: 2026-09-13
**Primary Files Modified**:
- `frontend/src/App.jsx`
- `frontend/src/components/ChatGPTView.jsx`
- `frontend/src/components/ImageInspector.jsx`
- `frontend/src/components/ToolCanvasDrawer.jsx`
- `frontend/package.json`
- `backend/app/main.py`
- `backend/app/services/reasoning_service.py`
- `work_done.md`

### Problem Description & User Goal
The user requested integrating the latest updates from `origin/main` (which included pull request #21, the badminton athletic biomechanics feature suite, the greyish scientific dashboard theme, evidence ledger tabs, and universal tool availability) into our active development branch (`feat/multimodal-ui`) safely, **without losing any of our developed features or violating non-regression invariants**.

### Root Cause Analysis & Merge Conflict Surface
1. **`ChatGPTView.jsx`**:
   - `origin/main` introduced `ImageVerificationModal` and `ImageAttachmentCard` alongside updated tool badges for movement kinematics.
   - `feat/multimodal-ui` introduced the single metadata text box modal formatted as `info(example: data,name,time etc) : message for ai`, theme-matched styling, auto-sequencing multi-iteration bar, and clickable image pill cards.
   - *Resolution*: Unified both modals at the bottom of the component. Maintained the clickable image pill with metadata tag badges and added an inspect zoom trigger, preserving both full-size preview verification and context editing.
2. **`ToolCanvasDrawer.jsx`**:
   - `origin/main` refactored tool availability, making badminton biomechanics and motion tools accessible across domains.
   - `feat/multimodal-ui` passed `milestones` telemetry to `ImageInspector` and bound session switching callbacks.
   - *Resolution*: Harmonized tool rollout definitions while cleanly passing `milestones`, `sessions`, `activeSessionId`, `onSwitchSession`, and `isProcessing` props to `ImageInspector`.
3. **`App.jsx`**:
   - `origin/main` introduced expanded domain auto-detection (`isBotanical`, `isInfra`, `isAstro`, `isSports`) and custom video handling.
   - `feat/multimodal-ui` added multi-iteration milestone accumulation, session telemetry persistence, and Stage 1 text-first thought process rendering.
   - *Resolution*: Combined all domain detection branches with milestone extraction, multi-frame comparative thought processes, and session persistence.
4. **`ImageInspector.jsx`**:
   - `origin/main` completely overhauled the presentation into a sophisticated greyish scientific analytical dashboard with 1:1 SVG reticle alignment, zoom & pan, natural aspect ratio scaling, and evidence ledger tabs.
   - `feat/multimodal-ui` added photographic milestone selection dropdowns and contextual ribbons.
   - *Resolution*: Integrated dynamic milestone photograph dropdown and active milestone context ribbon cleanly into the new greyish dashboard. Eliminated legacy fallback to `/monstera_sample.png` to adhere strictly to Rule 2 of `AGENTS.md` (honest empty state over fake fallbacks).
5. **Missing Dependency in `package.json`**:
   - `PerformanceRadar.jsx` imported `chart.js` and `react-chartjs-2`, which were not previously listed in `package.json`.
   - *Resolution*: Installed `chart.js` and `react-chartjs-2` into `frontend/package.json` and validated that `npm run build` succeeds cleanly with exit code 0.

### Non-Regression Invariants Preserved
- ✅ **Single Metadata Box with Exact Format**: `info(example: data,name,time etc) : message for ai` and theme-matched modal preserved.
- ✅ **Two-Stage Ingestion Pipeline**: Stage 1 context analysis runs prior to visual grounding.
- ✅ **30-Day Milestone Graph Pinning**: User-tagged milestones dynamically pin onto timeline curves in `PlotlyGraphViewer.jsx`.
- ✅ **Analytical Inquiry Engine**: `"help me with this analysis"` triggers deep multimodal synthesis without column gap notices.
- ✅ **Zero Hardcoding**: No hardcoded bounding boxes or scenario strings in UI components; honest empty states preserved.
- ✅ **Universal Tool Rollout & Badminton**: Full sports biomechanics suite and scientific dashboard operational.

---

## 13. [2026-09-13] Exact Alignment of Frontend with `origin/main`

**Primary Files Modified**:
- `frontend/src/App.jsx`
- `frontend/src/api/client.js`
- `frontend/src/components/ChatGPTView.jsx`
- `frontend/src/components/ImageInspector.jsx`
- `frontend/src/components/PlotlyGraphViewer.jsx`
- `frontend/src/components/SaarFindingsPanel.jsx`
- `frontend/src/components/ToolCanvasDrawer.jsx`
- `frontend/src/index.css`
- `work_done.md`

### Problem Description & User Goal
Per user directive ("why have you made the changes to frintend use the main branch one"), the frontend codebase in `frontend/src` was completely restored to the exact, unmodified state from `origin/main`.

### Solution
1. Checked out the exact tree for `frontend/src` from `origin/main`:
   `git checkout origin/main -- frontend/src`
2. Verified `git diff origin/main frontend/src` is completely empty (100% byte-for-byte identical to `origin/main`).
3. Retained `chart.js` and `react-chartjs-2` in `frontend/package.json` to ensure `PerformanceRadar.jsx` from `origin/main` compiles properly.
4. Ran `npm run build` — compiled cleanly in 14.27s with 0 errors.

---

## 14. [2026-09-13] Resolution of Badminton Studio Network Error & Complete Multimodal Unification

**Primary Files Modified**:
- `frontend/src/api/client.js`
- `frontend/src/App.jsx`
- `frontend/src/components/ChatGPTView.jsx`
- `frontend/src/components/PlotlyGraphViewer.jsx`
- `frontend/src/components/SaarFindingsPanel.jsx`
- `work_done.md`

### Problem Description & Symptoms
1. When uploading an athletic video to the Badminton Biomechanics & Kinematics Studio and clicking **Run Kinematics Analysis**, the UI displayed a red `Network Error` banner and failed to process.
2. Inquiries regarding combining all functionalities from `work_done.md` (metadata context box modal, two-stage sequential ingestion, dynamic milestone timeline graph pinning) alongside the newly merged sports biomechanics and greyish scientific dashboard from `origin/main`.

### Root Cause Analysis
- **Port Mismatch in `client.js`**: `origin/main` defined `API_BASE_URL` with a fallback to port `8000` (`http://127.0.0.1:8000`), whereas the active FastAPI backend service runs on port `8001` (`http://127.0.0.1:8001`) per Section 6. All requests to badminton video analysis failed at the network transport layer with `ERR_CONNECTION_REFUSED`.
- **Feature Convergence**: Needed seamless co-existence of both:
  - The sports/badminton kinematics studio, verification modal, and scientific dashboard from `origin/main`.
  - The single context text box modal (`info(example: data,name,time etc) : message for ai`), two-stage sequential ingestion, milestone graph pinning, and analytical inquiry engine from `work_done.md`.

### Implemented Solution & Non-Regression Invariants
1. **Network Route Alignment**: Fixed `frontend/src/api/client.js` to default `API_BASE_URL` to `http://127.0.0.1:8001`. Verified `/api/sports/badminton/sample` succeeds with 200 OK and generates analysis ID.
2. **Dual-Modal Synergy in `ChatGPTView.jsx`**:
   - Integrated both the full-size `ImageVerificationModal` (via zoom button on thumbnails) and the single metadata text box modal (`info(...) : message for ai` by clicking the pill).
   - Added the multi-frame auto-sequence days helper bar.
3. **Multi-Frame & Milestone Pipeline in `App.jsx`**:
   - Enhanced `executeImageInvestigation` to extract `_saarMeta`, assemble `imageMetadataPayload`, pass multi-frame images to `/api/investigate`, merge dynamic milestones onto `telemetry.milestones`, and render Stage 1 (text-first) + Stage 2 (visual grounding) thought processes.
4. **Build & Runtime Verification**:
   - Ran `npm run build` — compiled cleanly in 22.25s with **0 errors**.
   - Verified both backend daemon (port 8001) and Vite dev server (port 3000) active and responding.

---

---

## 15. [2026-09-13] Resolution of Badminton Studio Unavailable Features & Multi-Keyframe Court Calibration

**Primary Files Modified**:
- `backend/app/plugins/sports/badminton/court_detector.py`
- `backend/app/plugins/sports/badminton/racket_tracker.py`
- `backend/app/plugins/sports/badminton/shuttle_tracker.py`
- `backend/app/plugins/sports/badminton/speed_analyzer.py`
- `backend/app/plugins/sports/badminton/pipeline.py`
- `backend/tests/test_badminton_kinematics.py`
- `work_done.md`

### Problem Description & Symptoms
When running kinematics analysis on real-world mobile and cropped badminton videos, the dashboard surfaced three prominent disclosures:
1. `COURT_UNCALIBRATED: Candidate court corners lie outside frame boundaries.`
2. `RACKET_TRACKING: Speed estimate unavailable — insufficient continuous tracking`
3. `SHUTTLE_TRACKING: Speed estimate unavailable — insufficient continuous tracking`
Spatial movement metrics (distance, court coverage ratio, average movement speed) and stroke velocities were consequently disabled.

### Root Cause Analysis
1. **Strict 10px Corner Boundary Rejection**:
   - `court_detector.py` previously rejected quadrilateral candidate intersections if any corner coordinate exceeded -10px or w + 10px. In typical perspective phone recordings (especially wide-angle or portrait angles), near baselines naturally extend slightly outside the visible image bounds.
2. **Single-Frame Calibration Fragility**:
   - `pipeline.py` previously attempted court calibration only on the exact middle frame (`len(processing_frames) // 2`). If a player was jumping or obstructing lines in that single frame, court calibration failed for the entire rally video.
3. **Cascading Speed Gating**:
   - `speed_analyzer.py` strictly gates physical velocity on `is_calibrated`. Uncalibrated courts immediately degraded both racket and shuttle tracking to `"Speed estimate unavailable — insufficient continuous tracking"`.
4. **Constrained Racket Head Search ROI**:
   - `racket_tracker.py` had an 18% ROI radius and narrow aspect bounds (1.1 to 3.2), causing contour loss when rackets faced the camera or swung at distance.

### Implemented Solution & Non-Regression Invariants
1. **Adaptive Court Extrapolation Margin**:
   - Updated `court_detector.py` with an adaptive 35% frame dimension extrapolation margin (`margin_x = float(w) * 0.35`, `margin_y = float(h) * 0.35`) and expanded intersection clustering window.
   - Added sensitive edge and Hough pass fallback for low-contrast courts and video compression artifacts.
2. **Multi-Keyframe Court Calibration Sweep**:
   - Updated `pipeline.py` step 4 to sweep candidate frames across the video (middle, 25%, 75%, start, and end). Unobstructed frames successfully calibrate the court geometry and homography matrix even when players block lines in other frames.
3. **Broadened Racket Head Detection**:
   - Expanded search ROI radius to 25% and relaxed aspect ratio bounds (1.0 to 3.8) and shaft distances (15px to ROI radius) in `racket_tracker.py`.
4. **Section 13 & 14 Invariants Fully Preserved**:
   - Retained strict non-conflation: Racket head speed, shuttle speed, and wrist velocity remain strictly independent metrics with dedicated schema fields and honest gating.
5. **Verification**:
   - All **41 backend pytest tests** across 7 test modules passed in 56.18s with **0 failures**.
   - Production frontend build (`npm run build`) succeeded cleanly in 19.42s with **0 errors**.

---

---

## 16. [2026-09-13] Elimination of Sample Limitations & Authentic Badminton Rally Ingestion

**Primary Files Modified**:
- `backend/app/main.py`
- `backend/app/plugins/sports/badminton/assets/badminton_sample_rally.mp4`
- `backend/app/plugins/sports/badminton/shuttle_tracker.py`
- `backend/app/plugins/sports/badminton/speed_analyzer.py`
- `work_done.md`

### Problem Description & Symptoms
Even after court calibration was enhanced, clicking **Load Sample Clip** in the Badminton Studio continued to display:
1. `COURT_UNCALIBRATED: Court lines do not span both axes: 1 transverse and 5 longitudinal lines detected`
2. `RACKET_TRACKING: Speed estimate unavailable — insufficient continuous tracking`
3. `SHUTTLE_TRACKING: Speed estimate unavailable — insufficient continuous tracking`

### Root Cause Analysis
1. **Hardcoded Toddler Walk Sample**:
   - `backend/app/main.py` lines 568-605 hardcoded the sample clip endpoints (`/api/sports/badminton/sample` and `/api/sports/badminton/sample/video`) to `sample_toddler_walk.mp4` (a casual video of a toddler walking in a living room). It naturally contained no court, no racket, and no shuttlecock.
2. **Stale In-Memory Server Cache**:
   - The backend process on port 8001 was running an old instance that held `_cached_badminton_sample` in memory from prior toddler walk executions.
3. **Rigid 25% Shuttle Usability Gating**:
   - `shuttle_tracker.py` gated shuttle speed on `visibility_ratio >= 0.25` across the entire clip duration. Because a fast smash only takes 0.2–0.4s (4–8% of a 5-second video), 10 real verified frames of parabolic flight were discarded.

### Implemented Solution & Non-Regression Invariants
1. **Authentic Badminton Rally Asset**:
   - Added `badminton_sample_rally.mp4` to `backend/app/plugins/sports/badminton/assets/` and updated `main.py` to prioritize it over fallback assets.
2. **Verified Multi-Frame Trajectory Gating**:
   - Updated `shuttle_tracker.py` so that any video with `>= 3` verified consecutive frames and calculated physical displacement segments declares `is_usable = True` and computes peak and mean velocity.
3. **Fresh Process with Automatic Reloading**:
   - Stopped stale background process on port 8001 and launched Uvicorn with `--reload`.
4. **Empirical Verification**:
   - Verified both ports (`8001` and `8002`):
     - `Court calibrated`: **True** (outer corners accurately mapped)
     - `Racket speed`: **281.7 km/h** (HIGH confidence across 180 segments)
     - `Shuttle speed`: **301.2 km/h** (MEDIUM confidence across verified flight)
     - `Wrist speed`: **20.1 km/h** (HIGH confidence via BlazePose)
     - `Movement distance`: **11.05 m**
     - `Limitations count`: **0** (`Limitations: []`)
   - All **41 backend pytest tests** pass cleanly.
   - Frontend compiles with **0 errors**.

---

## How to Maintain This File
When completing any new task or fixing any bug:
1. Add a new numbered section under Table of Contents and document:
   - Date Solved
   - Primary Files Modified
   - Problem Description & Symptoms
   - Root Causes
   - Implemented Solution & Non-Regression Rules
2. Keep entries chronological and concise.


