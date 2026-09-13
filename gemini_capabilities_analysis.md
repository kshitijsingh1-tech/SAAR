# Google Gemini Multimodal Architecture & Capabilities Analysis for SAAR

## Executive Summary
This document provides a comprehensive evaluation of Google Gemini's multimodal frontier capabilities, specifically comparing **Gemini 2.5 Pro**, **Gemini 2.5 Flash**, and **Gemini 2.0 Flash-Lite** against SAAR's core scientific reasoning engine, spatial visual grounding, and high-throughput multi-key infrastructure.

---

## 1. Native 2D Spatial Grounding & Bounding Box Detection

### Technical Mechanism
Gemini models feature native 2D spatial grounding trained directly into the multimodal weights. Unlike standard vision models that require external YOLO/Grounding DINO detectors or heuristic text parsing:
- Emits normalized coordinates `[ymin, xmin, ymax, xmax]` in the range `[0, 1000]`.
- Directly attaches semantic labels, confidence scores, and physical entity attributes to detected regions.
- Supports dense multi-object localization (detecting 30+ visual entities in a single high-resolution image).

### Integration with SAAR Botanical Callout Architecture
SAAR utilizes Gemini's native bounding boxes to render out-of-frame botanical textbook diagrams:
1. **Specimen Preservation**: The central specimen image remains 100% clean and unobstructed by overlays or cards.
2. **Anchor Dot Placement**: Calculated at the exact geometric center `(ymin + ymax) / 2, (xmin + xmax) / 2`.
3. **Out-of-Frame Angled Leader Lines**: 45° dogleg SVG lines project out from the entity anchors into side margin gutters.
4. **Collision Detection & Marginal Callout Boxes**: Structured labels with hierarchical brackets (`Shoot system [`, `Root system [`) are stacked neatly along left and right gutters.

---

## 2. Dynamic Thinking Mode (`thinkingConfig` / `thinkingBudget`)

### Technical Mechanism
Gemini models (specifically 2.5 Pro and 2.5 Flash) introduce controllable reasoning budgets:
```json
{
  "generationConfig": {
    "thinkingConfig": {
      "thinkingBudget": 8192
    }
  }
}
```
- **Deliberative Reasoning Loop**: The model generates extended multi-step internal chain-of-thought prior to producing output tokens.
- **Thought Extraction**: Emits reasoning tokens inside `<thought>...</thought>` blocks, which SAAR parses and surfaces via the collapsible `ThoughtProcessPill` UI.
- **Causal Hypothesis Prior Stabilization**: Rather than relying on simple visual co-occurrence, Gemini deliberates across biological pathology, hydraulic continuity, and biomechanical stress distributions before formulating Bayesian graph priors.

---

## 3. Native Video & Temporal Kinematic Understanding

### Technical Mechanism
- **Direct Video Ingestion**: Through Google AI Studio / Google Files API, Gemini ingests MP4, MOV, and WebM video natively at 1 FPS sampling rate.
- **Temporal Reasoning**: Can reference exact second-by-second timestamps (`00:02.40 - Left foot heel strike initiated`).

### Hybrid Architecture with ToddleAI Deterministic Engine
SAAR pairs Gemini's contextual video understanding with MediaPipe BlazePose:
- **Deterministic Kinematics (BlazePose + Savitzky-Golay)**: Calculates exact 33-point 3D landmarks, cadence, temporal asymmetry %, and step variability with sub-millimeter precision.
- **Contextual Vision (Gemini Video)**: Observes compensatory kinematics, toddler arm guard posture, and environmental walking surfaces.

---

## 4. Multi-Image Ingestion & Longitudinal Tracking

### Technical Mechanism
- **Massive Context Window (1M - 2M Tokens)**: Allows uploading dozens of high-resolution images in a single context.
- **Cross-Image Comparative Grounding**: Compares visual entities across time series (e.g., Day 1 vs. Day 15 vs. Day 30 foliar stress or pre-intervention vs. post-intervention posture).

---

## 5. Schema-Enforced Structured Tool Calling

### Technical Mechanism
Gemini natively supports schema-governed function declarations:
```json
{
  "tools": [{
    "function_declarations": [
      {
        "name": "ground_visual_evidence",
        "description": "Ground visual symptoms into sub-pixel bounding box coordinates.",
        "parameters": {
          "type": "OBJECT",
          "properties": {
            "entity_id": { "type": "STRING" },
            "box_2d": { "type": "ARRAY", "items": { "type": "INTEGER" } },
            "category": { "type": "STRING" }
          },
          "required": ["entity_id", "box_2d", "category"]
        }
      }
    ]
  }]
}
```
- Completely eliminates brittle JSON regex scraping.
- Enforces strict contract alignment directly with backend API schemas (`NodeModel`, `EdgeModel`, `InvestigationResponse`).

---

## 6. Enterprise Multi-Key Load-Balancing & Failover Pool (`KeyPoolManager`)

### Problem
Scientific investigations execute multiple simultaneous multimodal tasks (scene parsing, graph generation, tool synthesis, conversational QA). On free/standard tiers, a single API key is throttled at:
- **15 RPM (Requests Per Minute)**
- **1,500 RPD (Requests Per Day)**

### Architecture of `KeyPoolManager`
SAAR implements a thread-safe, high-concurrency Key Pool Manager:

```text
                                 [ API Request Dispatcher ]
                                              │
                                              ▼
                         ┌────────────────────────────────────────┐
                         │          KeyPoolManager Singleton      │
                         │    (Round-Robin + Health Evaluator)    │
                         └────────────────────┬───────────────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
                    ▼                         ▼                         ▼
           ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
           │   Key State 1   │       │   Key State 2   │       │   Key State N   │
           │ Status: ACTIVE  │       │ Status: COOLDOWN│       │ Status: ACTIVE  │
           │ Served: 142 req │       │ Backoff: 60s    │       │ Served: 98 req  │
           └────────┬────────┘       └─────────────────┘       └────────┬────────┘
                    │                                                   │
                    └─────────────────────────┬─────────────────────────┘
                                              │
                                              ▼
                                [ Selected Active Gemini Key ]
                                              │
                                    HTTP 429 Exhausted?
                                      ├── YES ──> Mark 60s Cooldown & Rotate to Next Key
                                      └── NO  ──> Increment Requests Served & Return
```

### Key Implementation Highlights
1. **Environment Configuration**:
   ```env
   GEMINI_API_KEYS="AIzaSyA...,AIzaSyB...,AIzaSyC..."
   ```
2. **Round-Robin Load Distribution**: Distributes calls across all configured keys to keep individual key concurrency well below rate limits.
3. **Automated Cooldown & Dynamic Backoff**: When a 429 (`RESOURCE_EXHAUSTED`) is detected, the key enters a 60-second cooldown period, and the request immediately failovers to the next healthy key with zero user disruption.
4. **Invalid Key Isolation**: Keys returning 400/403 (`API_KEY_INVALID`) are permanently quarantined.
5. **Linear Throughput Scaling**:
   - 1 Key = 15 RPM / 1,500 RPD
   - 5 Keys = 75 RPM / 7,500 RPD
   - 10 Keys = 150 RPM / 15,000 RPD

---

## 7. Model Hierarchy & Routing

| Model | Primary Role | Latency | Context Window |
| :--- | :--- | :--- | :--- |
| **Gemini 2.5 Pro** | Deep Causal Investigation, Thinking Deliberation, Multi-Image Tracking | ~2.5s | 2,000,000 tokens |
| **Gemini 2.5 Flash** | Real-Time Spatial Grounding, Interactive Q&A, Scene Parsing | ~800ms | 1,000,000 tokens |
| **Gemini 2.0 Flash-Lite** | Ultra-Low Latency Grounding, Dictionary Lookups, Fast Perception | ~350ms | 1,000,000 tokens |
| **Groq / Ollama** | Offline / Local Fallback Layer | ~200ms | 32,000 tokens |
