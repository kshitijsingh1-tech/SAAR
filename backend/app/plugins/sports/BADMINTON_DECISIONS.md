# Badminton Biomechanics Plugin Architectural & Scope Decisions

## 1. Domain Registration & Architecture

### Decision
Register badminton as its own top-level plugin with `domain_name = "badminton"` (sibling to `"sports"`, `"gait"`, `"agriculture"`, `"infrastructure"`, and `"astronomy"`), rather than literally nesting it inside the existing `sports_plugin.py`.

### Justification
- **Flat Architecture**: In the SAAR engine, domain registration is strictly flat (`orchestrator.plugins` dictionary in `backend/app/dynamic_loop.py`, iterated directly by `/domains` and `/investigate` in `backend/app/main.py`).
- **No Subdomain Hierarchy**: The registry, frontend routing, and VLM dispatch layers have zero native concept of nested subdomains or hierarchical routing.
- **Risk Avoidance**: Forcing a pseudo-nested structure into a flat registry creates unneeded routing indirection, complicates serialization, and introduces fragile coupling between canned multi-sport scenarios and dedicated video analytics.
- **Separation of Concerns**: While `sports_plugin.py` models canned, multi-session kinetic-chain hypothesis scenarios, `badminton` is designed as a full temporal video analysis domain mirroring `gait`.

---

## 3. Phase 6 Decision: Option A (Honest-Gap Detection with Strict Gating)

### Decision
Adopt **Option A: Defer trained deep neural detector, ship the honest-gap path with classical OpenCV candidate detection and strict temporal-continuity gating**.

### Rationale
1. **Architectural & Environmental Integrity**: Avoids heavyweight dependencies (e.g. PyTorch / Ultralytics YOLO) and fragile external weight downloads subject to Windows Application Control and network restrictions.
2. **Scientific Honesty Over Fabricated Precision**: Public detectors (YOLO, TrackNet) are trained on broadcast 1080p/4K TV cameras with telephoto lenses. On typical phone recordings, shuttles move at 100–300 km/h, traversing 20–50 pixels per frame and causing severe motion blur that leads to high false-positive rates with naive detectors.
3. **Strict Gatekeeping**: Detection candidates are strictly verified against physical continuity. If temporal continuity fails, metrics explicitly return `available=False` with documented reasons rather than reporting noisy or fabricated numbers.

### Documented Confidence & Gating Thresholds
- **Shuttle Candidate Filter**:
  - Size constraint: Area between 4 and 600 px² (diameter ~2 to 28 px).
  - Circularity / elongation filter: Solidity $\ge 0.45$.
  - Inter-frame continuity: Trajectory requires at least 3 consecutive frames with linear/parabolic motion vector consistency.
  - Usability Gate: A clip must achieve >= 25% valid temporal continuity frames for shuttle kinematics to be marked available. Below this, `shuttle_speed` returns `available=False` with `unavailable_reason="NOT_RELIABLY_MEASURABLE: Shuttle tracking below temporal continuity threshold"`.
- **Racket Candidate Filter**:
  - Search Region: Constrained within a radial search window (~120 px) around the Phase 4 wrist landmark.
  - Contour geometry: Aspect ratio between 1.1 and 3.0 matching racket head oval.
  - Usability Gate: >= 30% of active stroke frames must have verified racket head contour. Below this, `racket_speed` returns `available=False` with `unavailable_reason="NOT_RELIABLY_MEASURABLE: Racket head unresolvable from motion blur/resolution"`.
- **Wrist Velocity vs Racket Speed (Section 14 Master Spec)**:
  - Peak wrist velocity is derived from MediaPipe 3D wrist landmarks when calibrated, but is strictly isolated and labeled as `wrist_speed` or pose kinematic velocity.
  - `racket_speed_peak` represents the racket sweet spot / head only, and is NEVER conflated with wrist velocity.

