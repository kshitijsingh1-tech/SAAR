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

## How to Maintain This File
When completing any new task or fixing any bug:
1. Add a new numbered section under Table of Contents and document:
   - Date Solved
   - Primary Files Modified
   - Problem Description & Symptoms
   - Root Causes
   - Implemented Solution & Non-Regression Rules
2. Keep entries chronological and concise.
