# SAAR Sports → Badminton Module Architecture Specification
**Document Version:** 1.0.0  
**Author:** Senior CV/Software Engineer & ML Systems Architect  
**Platform:** SAAR Visual Scientific Reasoning Engine  
**Domain:** Sports Biomechanics & Performance Intelligence (Badminton)

---

## 1. Executive Summary

The **SAAR Sports → Badminton Module** is an evidence-driven computer vision and biomechanical analysis engine designed to evaluate high-velocity badminton rallies from single-camera video. 

Following strict Google-level engineering principles:
1. **Never invent measurements**: Unobservable or uncalibrated physical phenomena (e.g. 3D shuttle height without multi-view geometry, physical speed without reliable court homography) are explicitly flagged as unavailable with structured rationale.
2. **Never present estimates as ground truth**: Energetics and caloric expenditure are grounded in peer-reviewed physiological literature and labeled as model-derived estimates.
3. **Every metric is traceable**: Each reported figure includes input data provenance, mathematical definitions, assumptions, confidence scores, and failure boundaries.
4. **Modular CV architecture**: Model adapters decouple core analytics from underlying vision models (YOLO, MediaPipe, ByteTrack, TrackNetV3), enabling isolated model updates without changing analytical schemas.

---

## 2. Current Architecture vs. Proposed Architecture

### 2.1 Current SAAR Architecture
* **Backend:** FastAPI (Python 3.11), Uvicorn server running on `http://127.0.0.1:8000`.
* **State Management:** In-memory registries (`_badminton_assessments`, `_gait_assessments`) with synchronized session models in `ReasoningService`.
* **Frontend:** React 18 SPA (Vite) on `http://localhost:3000` with Lucide icons, Plotly.js charts, and Cytoscape.js causal graph rendering.
* **Badminton State:** Existing synchronous endpoint (`POST /api/sports/badminton/analyze`) executing sequential CV pipeline over uploaded video bytes.
* **Storage / Auth:** Lightweight ephemeral storage using OS temporary files and in-memory caches; zero external database requirement for standalone deployment.

### 2.2 Proposed Production Architecture
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             CLIENT LAYER (React Vite)                       │
│  [Video Upload UI] ── [Job Polling / WebSocket] ── [Interactive Dashboard]  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTP / JSON
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                            API GATEWAY (FastAPI)                            │
│  /api/v1/videos/upload  ──►  /api/v1/analysis/start  ──►  /api/v1/analysis/* │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Job Dispatch
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                    ASYNCHRONOUS JOB & WORKER ENGINE                         │
│  Job Queue ──► State Machine ──► Stage-by-Stage Artifact Persistence         │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                  MODULAR COMPUTER VISION PIPELINE (Adapter-Based)           │
│  ┌────────────────────────┐  ┌────────────────────────┐  ┌───────────────┐ │
│  │   Court Calibration    │  │  Player Detector/Track │  │  17-Joint Pose│ │
│  │   (Homography Solver)  │  │   (YOLO / ByteTrack)   │  │   (COCO/Media)│ │
│  └───────────┬────────────┘  └───────────┬────────────┘  └───────┬───────┘ │
│              │                           │                       │         │
│  ┌───────────▼────────────┐  ┌───────────▼────────────┐  ┌───────▼───────┐ │
│  │  Shuttle Tracker       │  │  Hit/Contact Detector  │  │Shot Classifier│ │
│  │  (TrackNet / Candidate)│  │  (14-frame Window/GRU) │  │(Temporal Kin.)│ │
│  └───────────┬────────────┘  └───────────┬────────────┘  └───────┬───────┘ │
└──────────────┼───────────────────────────┼───────────────────────┼─────────┘
               │                           │                       │
┌──────────────▼───────────────────────────▼───────────────────────▼─────────┐
│                    MATHEMATICAL ANALYTICS & METRICS ENGINE                  │
│  • Footwork & Velocity (m/s)       • 9-Zone Spatial Court Coverage          │
│  • Dynamic Base Recovery           • Kinetic Chain Joint Angles & Omegas   │
│  • Rally Segmentation & Frequency  • Peer-Reviewed Metabolic Estimation    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                         EVIDENCE-BASED REASONING LAYER                      │
│  • Rule-Grounded Recommendations   • SAAR Causal Graph Node Integration     │
│  • Quality Gates & Confidence      • Formal Limitations & Uncertainties     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Canonical Data Model

To prevent coupling to individual model formats or dataset structures, all stages operate on the **Unified Badminton Data Model**:

### 3.1 FrameRecord
```json
{
  "frame_id": 105,
  "timestamp_ms": 3500,
  "fps": 30.0,
  "image_width": 1280,
  "image_height": 720,
  "player_tracks": [
    {
      "player_id": "player_near",
      "bbox": [420.0, 310.0, 580.0, 690.0],
      "bbox_confidence": 0.94,
      "ankle_midpoint_px": [500.0, 685.0],
      "court_x_m": 2.59,
      "court_y_m": 3.85,
      "court_confidence": 0.88,
      "pose_keypoints": { ... },
      "velocity_mps": 2.45,
      "acceleration_mps2": 1.10
    }
  ],
  "shuttle_position": {
    "x_px": 512.0,
    "y_px": 280.0,
    "confidence": 0.82,
    "interpolated": false,
    "court_x_m": 2.65,
    "court_y_m": 4.10
  },
  "court_confidence": 0.92
}
```

### 3.2 17-Joint COCO-Compatible Pose Model
Joint indices strictly adhere to the COCO 17-keypoint standard:
`0: nose`, `1: left_eye`, `2: right_eye`, `3: left_ear`, `4: right_ear`, `5: left_shoulder`, `6: right_shoulder`, `7: left_elbow`, `8: right_elbow`, `9: left_wrist`, `10: right_wrist`, `11: left_hip`, `12: right_hip`, `13: left_knee`, `14: right_knee`, `15: left_ankle`, `16: right_ankle`.

---

## 4. Mathematical Formulations & Quality Gates

### 4.1 Court Calibration & Metric Homography
* **Doubles Court:** $13.40\,\text{m} \times 6.10\,\text{m}$.
* **Singles Court:** $13.40\,\text{m} \times 5.18\,\text{m}$.
* **Transformation Equation:**
  $$\begin{bmatrix} x' \\ y' \\ w' \end{bmatrix} = \mathbf{H} \begin{bmatrix} x_{\text{img}} \\ y_{\text{img}} \\ 1 \end{bmatrix}, \quad x_{\text{court}} = \frac{x'}{w'}, \quad y_{\text{court}} = \frac{y'}{w'}$$
* **Reprojection Error Validation:**
  $$\epsilon_{\text{reproj}} = \frac{1}{N}\sum_{i=1}^N \|\mathbf{x}_i - \mathbf{H}^{-1}\mathbf{x}'_i\|_2$$
  * If $\epsilon_{\text{reproj}} > 8.0\,\text{px}$ or corner confidence $< 0.70$, metric speed/distance are flagged:
    `available = false, reason = "UNRELIABLE_COURT_CALIBRATION"`.

### 4.2 Kinematic Player Movement
* **Contact Point:** Bounding box center is strictly prohibited for ground tracking. Position is defined by the midpoint of `left_ankle` and `right_ankle` ($x_{\text{foot}}, y_{\text{foot}}$).
* **Euclidean Displacement:**
  $$\Delta d_i = \sqrt{(x_{i+1} - x_i)^2 + (y_{i+1} - y_i)^2}$$
* **Velocity & Acceleration:**
  $$v_i = \frac{\Delta d_i}{\Delta t_i}, \quad a_i = \frac{v_{i+1} - v_i}{\Delta t_i}, \quad \text{where } \Delta t_i = \frac{f_{i+1} - f_i}{\text{FPS}}$$

### 4.3 Spatial Court Coverage (9-Zone Model)
Rather than mathematically invalid ratios ($\frac{\text{distance}}{\text{area}}$), the court half is partitioned into 9 tactical zones:
$$\text{Front} \times \{\text{Left, Center, Right}\}, \quad \text{Mid} \times \{\text{Left, Center, Right}\}, \quad \text{Rear} \times \{\text{Left, Center, Right}\}$$
* Occupancy probability per zone:
  $$P(Z_k) = \frac{\sum_{t \in T} \mathbb{I}(\mathbf{x}_t \in Z_k)}{|T|}$$
* Minimum visited area via 2D Convex Hull:
  $$\text{Coverage Area} = \text{Area}(\text{ConvexHull}(\{\mathbf{x}_t\}_{t=1}^T)) \quad [\text{m}^2]$$

### 4.4 Kinetic Chain Joint Angles
For three connected joints $A, B, C$ with $B$ as vertex:
$$\theta = \arccos\left(\frac{(\mathbf{a} - \mathbf{b}) \cdot (\mathbf{c} - \mathbf{b})}{\|\mathbf{a} - \mathbf{b}\| \|\mathbf{c} - \mathbf{b}\|}\right) \times \frac{180^\circ}{\pi}$$
Angular velocity:
$$\omega_i = \frac{\theta_{i+1} - \theta_i}{\Delta t_i} \quad [^\circ/\text{s}]$$

### 4.5 Shuttle Trajectory & Speed Limitation
* Floor-projected shuttle speed is designated explicitly as **court-plane horizontal speed**:
  $$v_{\text{shuttle, 2D}} = \frac{\|\mathbf{x}'_{i+1} - \mathbf{x}'_i\|_2}{\Delta t}$$
* **CRITICAL LIMITATION**: Single-camera floor homography cannot reconstruct the vertical height $z(t)$ of the shuttle. True 3D velocity ($v_{3D} = \sqrt{v_x^2 + v_y^2 + v_z^2}$) is NOT reported without multi-view calibration.

### 4.6 Caloric / Energy Expenditure Modeling
Grounded in published sports physiology research (e.g. Cabello-Manrique & González-Badillo, 2003; Deka et al., 2017):
1. **MET Model (Standard Intensity):**
   $$\text{Energy (kcal)} = \text{MET} \times 3.5 \times \frac{\text{body\_mass\_kg}}{200} \times \text{duration\_minutes}$$
   * Singles competitive match play: $\text{MET} \approx 8.5 - 10.5$.
   * Moderate training / rallies: $\text{MET} \approx 6.0 - 7.5$.
2. **Net Footwork Work Model:**
   $$E_{\text{work}} \approx C_{\text{netFW}} \times \text{body\_mass\_kg} \times D_{\text{total\_m}}$$
   Where $C_{\text{netFW}}$ is the empirical energetic cost coefficient of multidirectional lunge-and-recover footwork ($\sim 2.1\,\text{J}/(\text{kg}\cdot\text{m})$).

---

## 5. Asynchronous Job Processing Pipeline

To ensure server responsiveness during CPU/GPU intensive CV processing:
```
STAGE 1: UPLOAD & VALIDATE
  ↳ Validate container (MP4, MOV), read headers, duration <= 180s.
  ↳ Create JobRecord with status="uploaded".
STAGE 2: PREPROCESSING
  ↳ Downsample high-FPS, compute quality checks (blur, illumination, jitter).
STAGE 3: COURT CALIBRATION
  ↳ Detect baseline & boundary lines, compute H, test reprojection error.
STAGE 4: PLAYER TRACKING & POSE
  ↳ Detect players, track IDs across rallies, extract 17 keypoints.
STAGE 5: SHUTTLE & HIT DETECTION
  ↳ Track trajectory, detect directional reversal & peak velocity contact frames.
STAGE 6: ANALYTICS & RECOVERY
  ↳ Compute speed, 9-zone occupancy, recovery times, joint angles, energetics.
STAGE 7: REPORT & RECOMMENDATION
  ↳ Compile canonical JSON report and register findings to SAAR knowledge graph.
```

### Job Progress States
`uploaded` $\to$ `preprocessing` $\to$ `court_detection` $\to$ `player_tracking` $\to$ `pose_analysis` $\to$ `shuttle_tracking` $\to$ `shot_analysis` $\to$ `analytics` $\to$ `report_generation` $\to$ `completed` (or `failed`).

---

## 6. API Endpoints Specification

| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/videos/upload` | Ingest video file, validate technical specs, initialize job |
| `POST` | `/api/v1/analysis/start` | Trigger asynchronous pipeline execution on uploaded video |
| `GET` | `/api/v1/analysis/{job_id}` | Retrieve overall job status, progress percentage, current stage |
| `GET` | `/api/v1/analysis/{job_id}/progress` | Lightweight polling endpoint for UI progress bars |
| `GET` | `/api/v1/analysis/{job_id}/report` | Full canonical JSON analysis report |
| `GET` | `/api/v1/analysis/{job_id}/rallies` | Segmented rallies with durations, shot counts, and outcomes |
| `GET` | `/api/v1/analysis/{job_id}/shots` | Frame-by-frame shot events and contact kinematics |
| `GET` | `/api/v1/analysis/{job_id}/movement` | Player distance, speeds, accelerations, and trajectory points |
| `GET` | `/api/v1/analysis/{job_id}/coverage` | 9-zone spatial occupancy breakdown and convex hull area |
| `GET` | `/api/v1/analysis/{job_id}/pose` | 17-joint angular time series (shoulder, elbow, knee, hip) |
| `GET` | `/api/v1/analysis/{job_id}/speed` | Validated player and court-plane shuttle speed distributions |
| `GET` | `/api/v1/analysis/{job_id}/energy` | Physiological caloric estimates with MET source citations |
| `GET` | `/api/v1/analysis/{job_id}/recommendations` | Evidence-grounded tactical and biomechanical recommendations |

---

## 7. External Datasets & Research Provenance

| Source | Target Utility in SAAR | Commercial & Video Constraints |
| :--- | :--- | :--- |
| **BFMD** | Full-match court corners, 17-keypoint COCO poses, hit events | Annotations open; source broadcast videos have copyright restrictions |
| **TemPose** | 2-player 17-joint pose sequences, homography ground-plane projection | Academic use; stroke representation benchmark |
| **Badminton-hit-detection** | 14-frame temporal window for contact detection, near/far player | Hit detection architecture baseline |
| **BaddieVision** | TrackNet + YOLO player tracking & metric court projection | Open architecture reference |
| **RallyLens** | ByteTrack + Kalman filtering, rally-level reporting | Implementation reference |
| **BadmintonDB** | Stroke annotations, tactical transition probabilities | Benchmark transition matrices |
| **ShuttleVision** | Single-camera court-plane speed methodology | Informs horizontal speed calculation |

---

## 8. Scientific Limitations & Boundaries

1. **Floor-Plane Projection:** Single-camera homography provides coordinates on the ground plane. Vertical trajectory (z-axis) cannot be resolved without stereo vision or prior flight dynamics models.
2. **Motion Blur at Low FPS:** Standard 24/30 FPS recordings suffer significant motion blur during smashes (>300 km/h). Contact frames carry an uncertainty window of $\pm 2$ frames.
3. **Caloric Approximations:** Energetic expenditure models estimate work using generalized MET tables or mechanical footwork work; they do not replace gas-exchange indirect calorimetry.
4. **Non-Medical Boundary:** Kinetic chain analysis flags biomechanical movement anomalies for athletic training; it does not diagnose injuries or provide medical advice.
