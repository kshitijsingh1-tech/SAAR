import os
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

from fastapi import FastAPI, HTTPException, Query, Response, Request, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from .schemas import InvestigationRequest, InvestigationResponse, BaselineComparisonModel
from .dynamic_loop import DynamicWorkflowOrchestrator
from .services.key_pool_manager import key_pool

app = FastAPI(
    title="Saar API - Visual Scientific Reasoning Engine",
    description="Autonomous Visual Reasoning Engine constructing dynamic investigation workflows & graph relationships.",
    version="1.0.0"
)

# Enable CORS for all origins & methods
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = DynamicWorkflowOrchestrator()

from .plugins.sports.badminton.router import router as badminton_v1_router
app.include_router(badminton_v1_router)

@app.get("/")
def root_index():
    return {
        "status": "ok",
        "service": "Saar API - Visual Scientific Reasoning Engine",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "frontend": "http://localhost:3000"
    }

@app.options("/{full_path:path}")
def options_handler(full_path: str):
    return Response(status_code=200)

@app.get("/health")
@app.get("/api/health")
def health_check():
    return {"status": "ok", "engine": "Saar Scientific Reasoning Engine v1.0"}

@app.get("/api/keys/status")
def get_keys_status():
    """Return live load-balancing and quota status of all API key pools."""
    return {
        "status": "ok",
        "pools": key_pool.get_status()
    }

@app.get("/domains")
@app.get("/api/domains")
def get_domains():
    """Return available domain plugins and preset scenarios."""
    result = []
    for domain_key, plugin in orchestrator.plugins.items():
        result.append({
            "id": domain_key,
            "name": domain_key.capitalize(),
            "presets": plugin.presets,
            "tools_available": plugin.get_available_tools()
        })
    return result

@app.post("/investigate")
@app.post("/api/investigate", response_model=InvestigationResponse)
def run_investigation(req: InvestigationRequest):
    """Run full dynamic investigation loop for a domain preset or uploaded image."""
    try:
        response = orchestrator.run_investigation(
            domain=req.domain,
            preset_id=req.preset_id,
            image_url=req.image_url,
            image_data=req.image_data,
            images=req.images,
            image_metadata=[m.model_dump() if hasattr(m, 'model_dump') else dict(m) for m in req.image_metadata] if req.image_metadata else None,
            vlm_provider=req.vlm_provider,
            api_key=req.api_key
        )
        try:
            saar_engine.register_visual_investigation(response)
        except Exception as reg_err:
            print(f"[Main] Warning: Failed to register visual investigation state: {reg_err}")
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/baseline")
@app.get("/api/baseline")
def get_baseline(domain: str = Query("infrastructure"), preset_id: Optional[str] = None) -> BaselineComparisonModel:
    """Get single-pass VLM baseline response for scenario comparison."""
    plugin = orchestrator.get_plugin(domain)
    if not preset_id:
        preset_id = plugin.presets[0]["id"]
    return plugin.get_baseline_comparison(preset_id)


from .services.image_classifier import image_classifier


class ImageClassificationRequest(BaseModel):
    image_data: str
    user_text: Optional[str] = None


@app.post("/api/classify-image")
def classify_image_endpoint(req: ImageClassificationRequest):
    """Autonomous visual domain classification for uploaded or pasted images."""
    try:
        return image_classifier.classify_image(req.image_data, req.user_text)
    except Exception as e:
        return {"domain": "agriculture", "confidence": 0.5, "error": str(e)}


# ===================================================================
# SAAR — Iterative Evidence-Driven Reasoning API
# ===================================================================

import asyncio
from fastapi import UploadFile, File
from .services.reasoning_service import ReasoningService
from .services.dictionary_service import terminology_service, PRELOADED_DOMAIN_TERMS
from .models.saar_models import UserAnswer
from .rag_service import RAGKnowledgeService

saar_engine = ReasoningService()
rag_service = RAGKnowledgeService()

@app.post("/api/saar/upload")
async def saar_upload(file: UploadFile = File(...)):
    """Upload CSV → Start SAAR investigation (Perceive → Concepts → Relationships → Questions)."""
    try:
        content = await file.read()
        state = saar_engine.start_investigation(content, file.filename or "upload.csv")
        report = saar_engine.get_report(state.investigation_id)
        domain = getattr(state, "dataset_id", "agriculture") or "agriculture"
        terms = await terminology_service.extract_grounded_terms_async(
            f"Dataset {file.filename} analysis", domain, report.get("conclusion", "")
        )
        report["terminology"] = terms
        return report
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/saar/read-file")
async def saar_read_file(path: str = Query(...)):
    """Read a local dataset or document file from disk to support pasted file paths."""
    from pathlib import Path
    raw_path = path.strip().strip('"').strip("'")
    if not raw_path:
        raise HTTPException(status_code=400, detail="Path parameter is required")

    candidates = [
        Path(raw_path),
        Path(r"d:\bytebuild") / raw_path,
        Path(r"d:\bytebuild") / os.path.basename(raw_path)
    ]
    target = None
    for c in candidates:
        try:
            if c.exists() and c.is_file():
                target = c
                break
        except Exception:
            continue

    if not target:
        raise HTTPException(status_code=404, detail=f"File not found on system: {raw_path}")

    try:
        with open(target, "rb") as f:
            content = f.read()
        filename = target.name
        media_type = "text/csv" if filename.lower().endswith(".csv") else "application/octet-stream"
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Filename": filename,
                "Access-Control-Expose-Headers": "X-Filename, Content-Disposition"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/saar/sample-telemetry")
async def saar_sample_telemetry(domain: str = Query("agriculture"), topic: Optional[str] = Query(None)):
    """Load authentic empirical telemetry dataset for domain baseline."""
    from pathlib import Path
    base_dir = Path(__file__).resolve().parent.parent.parent
    test_data_dir = base_dir / "test_data"

    target_file = None
    domain_lower = (domain or "agriculture").lower()
    topic_lower = (topic or "").lower()

    if any(k in topic_lower or k in domain_lower for k in ["rose", "scion", "graft", "callus", "budding"]):
        target_file = test_data_dir / "rose_chip_budding_graft_journey_sensors.csv"
        if not target_file.exists():
            target_file = base_dir / "rose_chip_budding_graft_journey_sensors.csv"
    elif any(k in domain_lower for k in ["infra", "road", "pave", "bridge", "civil", "radar"]):
        target_file = test_data_dir / "infrastructure_cavity_sensors.csv"
    elif any(k in domain_lower for k in ["sport", "badminton", "athletic", "racket"]):
        target_file = test_data_dir / "badminton_match_kinematics.csv"
    elif any(k in domain_lower for k in ["pediatric", "gait", "toddle", "walking"]):
        target_file = test_data_dir / "toddler_gait_kinematics.csv"
    else:
        # Default agriculture / crop science
        target_file = test_data_dir / "crop_data.csv"
        if not target_file.exists():
            target_file = test_data_dir / "rose_chip_budding_graft_journey_sensors.csv"

    content = None
    filename = ""

    if target_file and target_file.exists():
        with open(target_file, "rb") as f:
            content = f.read()
        filename = target_file.name
    else:
        from app.sample_telemetry_defaults import (
            INFRASTRUCTURE_CAVITY_CSV,
            BADMINTON_KINEMATICS_CSV,
            TODDLER_GAIT_CSV,
            ROSE_BUDDING_CSV
        )
        if any(k in topic_lower or k in domain_lower for k in ["rose", "scion", "graft", "callus", "budding"]):
            content = ROSE_BUDDING_CSV
            filename = "rose_chip_budding_graft_journey_sensors.csv"
        elif any(k in domain_lower for k in ["infra", "road", "pave", "bridge", "civil", "radar"]):
            content = INFRASTRUCTURE_CAVITY_CSV
            filename = "infrastructure_cavity_sensors.csv"
        elif any(k in domain_lower for k in ["sport", "badminton", "athletic", "racket"]):
            content = BADMINTON_KINEMATICS_CSV
            filename = "badminton_match_kinematics.csv"
        elif any(k in domain_lower for k in ["pediatric", "gait", "toddle", "walking"]):
            content = TODDLER_GAIT_CSV
            filename = "toddler_gait_kinematics.csv"
        else:
            content = ROSE_BUDDING_CSV
            filename = "rose_chip_budding_graft_journey_sensors.csv"

    if not content:
        raise HTTPException(status_code=404, detail=f"Sample telemetry dataset not found for domain: {domain}")

    try:
        state = saar_engine.start_investigation(content, filename)
        report = saar_engine.get_report(state.investigation_id)
        report["terminology"] = await terminology_service.extract_grounded_terms_async(
            f"Baseline telemetry {filename}", domain_lower, report.get("conclusion", "")
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load sample telemetry: {str(e)}")

@app.get("/api/saar/investigation/{investigation_id}")
def saar_get_investigation(investigation_id: str):
    """Get the current state of an active SAAR investigation."""
    report = saar_engine.get_report(investigation_id)
    if "error" in report:
        raise HTTPException(status_code=404, detail=report["error"])
    return report

@app.post("/api/saar/investigation/{investigation_id}/answer")
async def saar_answer(investigation_id: str, answer: UserAnswer):
    """Submit user answer → belief update → new questions with contextual terminology."""
    try:
        state = saar_engine.process_answer(investigation_id, answer)
        report = saar_engine.get_report(investigation_id)
        domain = getattr(state, "dataset_id", "agriculture") or "agriculture"
        terms = await terminology_service.extract_grounded_terms_async(
            answer.raw_answer, domain, str(answer.structured_data)
        )
        report["terminology"] = terms
        return report
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/saar/investigation/{investigation_id}/ask")
async def saar_ask(investigation_id: str, payload: Dict[str, str]):
    """Ask a question with concurrent zero-latency terminology extraction."""
    question = payload.get("question", "")
    if not question:
        raise HTTPException(status_code=400, detail="Question is required.")

    state = saar_engine.get_investigation(investigation_id)
    domain = getattr(state, "dataset_id", "agriculture") or "agriculture"

    # Parallel dispatch: Deep causal reasoning + Grounded lexical extraction
    reasoning_task = asyncio.to_thread(saar_engine.answer_question, investigation_id, question, domain)
    terminology_task = terminology_service.extract_grounded_terms_async(question, domain)

    res, terms = await asyncio.gather(reasoning_task, terminology_task)
    if isinstance(res, dict) and "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    if isinstance(res, dict):
        res["terminology"] = terms
    return res

@app.post("/api/saar/ask")
async def saar_general_ask(payload: Dict[str, Any]):
    """Ask a freeform scientific query with concurrent zero-latency terminology extraction."""
    question = payload.get("question", "")
    domain = payload.get("domain", "agriculture")
    investigation_id = payload.get("investigation_id") or "latest"
    if not question:
        raise HTTPException(status_code=400, detail="Question is required.")

    # Parallel dispatch: Deep causal reasoning + Grounded lexical extraction
    reasoning_task = asyncio.to_thread(saar_engine.answer_question, investigation_id, question, domain)
    terminology_task = terminology_service.extract_grounded_terms_async(question, domain)

    res, terms = await asyncio.gather(reasoning_task, terminology_task)
    if isinstance(res, dict):
        res["terminology"] = terms
    return res

@app.post("/api/dictionary/lookup")
@app.post("/dictionary/lookup")
async def dictionary_lookup(payload: Dict[str, Any]):
    """On-demand scientific term lookup."""
    term = payload.get("term", "") or payload.get("word", "")
    domain = payload.get("domain", "general")
    context = payload.get("context", "")
    if not term:
        raise HTTPException(status_code=400, detail="Term is required.")
    return await terminology_service.lookup_term_async(term, domain, context)

@app.post("/api/dictionary/glossary")
@app.post("/dictionary/glossary")
async def dictionary_glossary_endpoint(payload: Dict[str, Any]):
    """Extract grounded terms from screen text with instantaneous domain glossary return."""
    screen_texts = payload.get("screen_texts") or payload.get("texts") or []
    domain = payload.get("domain", "agriculture")
    if not isinstance(domain, str):
        domain = "agriculture"
    clean_domain = domain.lower()
    
    combined_text = " ".join([str(t) for t in screen_texts if t]) if isinstance(screen_texts, list) else str(screen_texts or "")
    
    # 1. Fast extraction of terms present in screen
    terms = await terminology_service.extract_grounded_terms_async(combined_text, clean_domain)
    
    # 2. Gather full domain pool
    domain_key = "agriculture"
    for k in PRELOADED_DOMAIN_TERMS.keys():
        if k in clean_domain or clean_domain in k:
            domain_key = k
            break
    all_domain_terms = PRELOADED_DOMAIN_TERMS.get(domain_key, PRELOADED_DOMAIN_TERMS["agriculture"])
    
    results = []
    seen = set()
    combined_lower = combined_text.lower()
    
    for t in terms:
        word = t.get("term") or t.get("word", "")
        if word and word.lower() not in seen:
            item = dict(t)
            item["word"] = word
            item["is_in_chat"] = True
            item["occurrences_in_chat"] = combined_lower.count(word.lower()) or 1
            results.append(item)
            seen.add(word.lower())
            
    for t in all_domain_terms:
        word = t.get("term") or t.get("word", "")
        if word and word.lower() not in seen:
            item = dict(t)
            item["word"] = word
            in_screen = word.lower() in combined_lower
            item["is_in_chat"] = in_screen
            item["occurrences_in_chat"] = combined_lower.count(word.lower()) if in_screen else 0
            results.append(item)
            seen.add(word.lower())
            
    return {"glossary": results}

@app.get("/api/saar/knowledge")
def saar_knowledge_domains():
    """List available RAG knowledge base domains."""
    return rag_service.list_domains()

@app.post("/api/saar/knowledge/query")
def saar_knowledge_query(payload: Dict[str, Any]):
    """Query the RAG knowledge base."""
    query = payload.get("query", "")
    domain = payload.get("domain")
    top_k = payload.get("top_k", 5)
    results = rag_service.query(query, domain=domain, top_k=top_k)
    return [r.to_dict() for r in results]


# ===================================================================
# ADAPTIVE DIAGNOSTIC QUESTIONING API
# ===================================================================

from .gait.baseline_service import personalized_baseline_service


class AdaptiveStartRequest(BaseModel):
    investigation_id: Optional[str] = "latest"
    user_concern: str
    subject_id: Optional[str] = "child_toddler"


class AdaptiveAnswerRequest(BaseModel):
    option_id: str


@app.post("/api/adaptive/start")
async def adaptive_start(req: AdaptiveStartRequest):
    """Start an adaptive diagnostic questioning session for an active investigation."""
    try:
        session = saar_engine.start_adaptive_session(
            investigation_id=req.investigation_id or "latest",
            user_concern=req.user_concern,
            subject_id=req.subject_id or "child_toddler"
        )
        return session.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to start adaptive session: {str(e)}")


@app.get("/api/adaptive/{session_id}")
def adaptive_get_session(session_id: str):
    """Get the current state of an adaptive diagnostic session."""
    try:
        session = saar_engine.get_adaptive_session(session_id)
        return session.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/adaptive/{session_id}/answer")
async def adaptive_answer(session_id: str, req: AdaptiveAnswerRequest):
    """Submit an answer to the current adaptive question and get the next question or conclusion."""
    try:
        session = saar_engine.submit_adaptive_answer(session_id, req.option_id)
        return session.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process adaptive answer: {str(e)}")


# ===================================================================
# PERSONALIZED GAIT BASELINE API
# ===================================================================

@app.get("/api/gait/baselines")
def gait_list_baselines():
    """List registered child profiles with empirical baseline status."""
    return personalized_baseline_service.list_profiles()


@app.get("/api/gait/baselines/{subject_id}")
def gait_get_baseline(subject_id: str):
    """Retrieve child's longitudinal personalized baseline."""
    profile = personalized_baseline_service.get_profile(subject_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Child baseline '{subject_id}' not found.")
    return profile.model_dump()


@app.post("/api/gait/baselines/{subject_id}/update")
def gait_update_baseline(subject_id: str, payload: Dict[str, Any]):
    """Update child's personalized baseline using newly verified assessment metrics."""
    try:
        profile = personalized_baseline_service.update_from_assessment(subject_id, payload)
        return profile.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update baseline: {str(e)}")


@app.post("/api/gait/baselines/{subject_id}/compare")
def gait_compare_baseline(subject_id: str, payload: Dict[str, Any]):
    """Compare an assessment against child's personalized baseline to detect deviations."""
    try:
        result = personalized_baseline_service.compare_assessment(subject_id, payload)
        return result.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare baseline: {str(e)}")

# TODDLEAI GAIT ANALYSIS API (DEDICATED ENDPOINTS)
# ===================================================================

try:
    from .gait.pipeline import GaitAnalysisPipeline
    from .gait.schemas import CanonicalGaitResult
except ImportError:
    GaitAnalysisPipeline = None
    CanonicalGaitResult = None

_gait_pipeline = None
_gait_assessments: Dict[str, Any] = {}


def get_gait_pipeline():
    global _gait_pipeline
    if _gait_pipeline is None:
        if GaitAnalysisPipeline is None:
            raise HTTPException(status_code=503, detail="Gait analysis pipeline dependencies (cv2/mediapipe) not installed.")
        _gait_pipeline = GaitAnalysisPipeline()
    return _gait_pipeline


@app.post("/api/gait/analyze")
async def gait_analyze_video(
    video: UploadFile = File(...),
    child_age_months: int = Query(24, ge=6, le=120),
    subject_id: Optional[str] = Query(None)
):
    """Analyze a toddler walking video using deterministic ToddleAI gait pipeline."""
    try:
        content = await video.read()
        pipeline = get_gait_pipeline()
        result = pipeline.analyze_video_bytes(
            video_bytes=content,
            filename=video.filename or "toddler_walking.mp4",
            child_age_months=child_age_months
        )
        _gait_assessments[result.assessment_id] = result
        try:
            saar_engine.register_gait_investigation(result)
        except Exception as reg_err:
            print(f"[Main] Warning: Failed to register gait investigation: {reg_err}")
        
        output = result.model_dump()
        try:
            active_subject = subject_id or "child_toddler"
            comp = personalized_baseline_service.compare_assessment(active_subject, output)
            output["baseline_comparison"] = comp.model_dump()
        except Exception as comp_err:
            print(f"[Main] Baseline comparison error in video analyze: {comp_err}")
        return output
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gait analysis failed: {str(e)}")


@app.post("/api/video/classify")
async def classify_video_endpoint(
    video: UploadFile = File(...),
    context: Optional[str] = Form(None)
):
    """
    Autonomous Video Domain Classifier & Tool Dispatcher.
    Analyzes video keyframes, court boundary geometry, and anatomical stature
    to dynamically determine whether a video is a Badminton rally or a Toddler Gait screening.
    """
    try:
        from app.services.video_classifier import get_video_classifier
        content = await video.read()
        classifier = get_video_classifier()
        result = classifier.classify_video_bytes(
            video_bytes=content,
            filename=video.filename or "video.mp4",
            user_context=context or ""
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video classification failed: {str(e)}")



@app.get("/api/gait/sample/video")
def gait_sample_video():
    """Stream pre-bundled sample toddler walking video."""
    import os
    candidates = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "gait", "assets", "sample_toddler_walk.mp4")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend", "app", "gait", "assets", "sample_toddler_walk.mp4")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "toddle-ai", "video", "Toddler_walking_in_blue_dress_202606280214.mp4"))
    ]
    sample_path = next((c for c in candidates if os.path.exists(c)), None)
    if not sample_path:
        raise HTTPException(status_code=404, detail="Sample video file not found.")
    return FileResponse(sample_path, media_type="video/mp4")


@app.get("/api/gait/sample")
def gait_analyze_sample(child_age_months: int = Query(24, ge=6, le=120), subject_id: Optional[str] = Query("child_leo_24m")):
    """Run analysis on pre-bundled sample toddler walking video."""
    import os
    candidates = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "gait", "assets", "sample_toddler_walk.mp4")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend", "app", "gait", "assets", "sample_toddler_walk.mp4")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "toddle-ai", "video", "Toddler_walking_in_blue_dress_202606280214.mp4"))
    ]
    sample_path = next((c for c in candidates if os.path.exists(c)), None)
    if not sample_path:
        raise HTTPException(status_code=404, detail="Sample video not found.")

    pipeline = get_gait_pipeline()
    result = pipeline.analyze_video_file(
        video_path=sample_path,
        filename="Toddler_walking_in_blue_dress.mp4",
        child_age_months=child_age_months
    )
    _gait_assessments[result.assessment_id] = result
    try:
        saar_engine.register_gait_investigation(result)
    except Exception as reg_err:
        print(f"[Main] Warning: Failed to register gait sample investigation: {reg_err}")

    output = result.model_dump()
    try:
        active_subject = subject_id or "child_leo_24m"
        comp = personalized_baseline_service.compare_assessment(active_subject, output)
        output["baseline_comparison"] = comp.model_dump()
    except Exception as comp_err:
        print(f"[Main] Baseline comparison error in sample analyze: {comp_err}")
    return output



@app.get("/api/gait/assessment/{assessment_id}")
def gait_get_assessment(assessment_id: str):
    """Retrieve structured canonical result for a previous gait assessment."""
    if assessment_id in _gait_assessments:
        return _gait_assessments[assessment_id].model_dump()
    report = saar_engine.get_report(assessment_id)
    if "error" not in report:
        return report
    raise HTTPException(status_code=404, detail=f"Gait assessment '{assessment_id}' not found.")


@app.post("/api/gait/assessment/{assessment_id}/ask")
async def gait_ask_assessment(assessment_id: str, payload: Dict[str, str]):
    """Ask a question regarding a specific gait assessment with grounded reasoning."""
    question = payload.get("question", "")
    if not question:
        raise HTTPException(status_code=400, detail="Question is required.")

    reasoning_task = asyncio.to_thread(saar_engine.answer_question, assessment_id, question)
    terminology_task = terminology_service.extract_grounded_terms_async(question, "pediatrics")
    res, terms = await asyncio.gather(reasoning_task, terminology_task)
    if isinstance(res, dict) and "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    if isinstance(res, dict):
        res["terminology"] = terms
    return res


# ===================================================================
# BADMINTON BIOMECHANICS VIDEO ANALYSIS API
# ===================================================================

try:
    from .plugins.sports.badminton import (
        BadmintonPipeline, BadmintonAnalysisResult, PlayerMetadata
    )
except Exception as _badminton_err:
    BadmintonPipeline = None
    BadmintonAnalysisResult = None
    PlayerMetadata = None
    print(f"[Main] Notice: BadmintonPipeline unavailable: {_badminton_err}")

_badminton_pipeline = None
_badminton_assessments: Dict[str, Any] = {}


def get_badminton_pipeline():
    global _badminton_pipeline
    if _badminton_pipeline is None:
        if BadmintonPipeline is None:
            raise HTTPException(status_code=503, detail="Badminton analysis pipeline dependencies not available.")
        _badminton_pipeline = BadmintonPipeline()
    return _badminton_pipeline


@app.get("/api/sports/badminton/recording-guidance")
def badminton_recording_guidance():
    """Returns static UX recording guidelines and capture best practices for badminton video analysis."""
    return {
        "title": "Badminton Video Recording Best Practices",
        "camera_position": {
            "preferred_angles": [
                "Rear Baseline: Elevated 1.5m - 2.5m directly behind the baseline facing the net.",
                "Diagonal Corner: 45° angle from the rear corner for optimal depth and lateral footwork observation."
            ],
            "stability": "Stationary mount or tripod strongly recommended. Handheld tracking introduces false acceleration artifacts."
        },
        "framing": {
            "court_coverage": "Full half-court or complete 13.4m x 6.1m court boundaries clearly visible.",
            "player_framing": "Player must be visible head-to-toe across all strokes, jumps, and lunges.",
            "occlusion": "Keep net posts and umpire chair from obstructing player racket swing plane."
        },
        "technical_specifications": {
            "minimum_fps": 30,
            "recommended_fps": 60,
            "minimum_resolution": "720p (1280x720)",
            "recommended_resolution": "1080p (1920x1080)",
            "lighting": "Uniform indoor court lighting; avoid backlight glare and heavy shadows."
        },
        "clip_duration": {
            "minimum_seconds": 3.0,
            "recommended_seconds": "5s – 90s (single rally or repetitive stroke drill)",
            "maximum_seconds": 180.0
        },
        "rally_types": [
            "Overhead smash drills",
            "Clears and drop shots",
            "Full singles / doubles competitive rally exchanges"
        ]
    }


@app.post("/api/sports/badminton/analyze")
async def badminton_analyze_video(
    video: UploadFile = File(...),
    player_age: Optional[int] = Query(None, ge=5, le=100),
    player_sex: Optional[str] = Query(None),
    body_weight_kg: Optional[float] = Query(None, ge=20.0, le=250.0),
    skill_level: Optional[str] = Query(None),
    session_duration_min: Optional[float] = Query(None, ge=1.0, le=300.0),
    match_type: Optional[str] = Query(None),
    court_orientation: Optional[str] = Query(None)
):
    """
    Accepts video upload and optional player metadata, decodes video container,
    runs recording-level quality gating, and returns a structured BadmintonAnalysisResult.
    """
    player_meta = None
    if any(p is not None for p in [player_age, player_sex, body_weight_kg, skill_level, session_duration_min, match_type, court_orientation]):
        player_meta = PlayerMetadata(
            age=player_age,
            sex=player_sex,
            body_weight_kg=body_weight_kg,
            skill_level=skill_level,
            session_duration_min=session_duration_min,
            match_type=match_type,
            court_orientation=court_orientation
        ) if PlayerMetadata else None

    try:
        content = await video.read()
        pipeline = get_badminton_pipeline()
        result = pipeline.analyze_video_bytes(
            video_bytes=content,
            filename=video.filename or "badminton_video.mp4",
            player_metadata=player_meta
        )
        _badminton_assessments[result.analysis_id] = result
        try:
            saar_engine.register_badminton_investigation(result)
        except Exception as reg_err:
            print(f"[Main] Warning: Failed to register badminton investigation: {reg_err}")
        return result.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Badminton video processing failed: {str(e)}")


@app.get("/api/sports/badminton/analysis/{analysis_id}")
def badminton_get_analysis(analysis_id: str):
    """Retrieve structured analysis result for a badminton video."""
    if analysis_id in _badminton_assessments:
        return _badminton_assessments[analysis_id].model_dump()
    raise HTTPException(status_code=404, detail=f"Badminton analysis '{analysis_id}' not found.")


@app.post("/api/sports/badminton/analysis/{analysis_id}/ask")
async def badminton_ask_analysis(analysis_id: str, payload: Dict[str, str]):
    """
    Ask a question regarding a specific badminton analysis with grounded reasoning
    and Section 27 'what's missing' protocol.
    """
    question = payload.get("question", "")
    if not question:
        raise HTTPException(status_code=400, detail="Question is required.")

    if analysis_id not in _badminton_assessments and analysis_id not in saar_engine._investigations:
        raise HTTPException(status_code=404, detail=f"Badminton analysis '{analysis_id}' not found.")

    res = await asyncio.to_thread(saar_engine.answer_question, analysis_id, question)
    if isinstance(res, dict) and "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res


@app.get("/api/sports/badminton/sample/video")
def badminton_sample_video():
    """Stream bundled sample video for badminton player playback."""
    import os
    from fastapi.responses import FileResponse
    candidates = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "plugins", "sports", "badminton", "assets", "badminton_sample_rally.mp4")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "gait", "assets", "sample_toddler_walk.mp4")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend", "app", "gait", "assets", "sample_toddler_walk.mp4")),
    ]
    sample_path = next((c for c in candidates if os.path.exists(c)), None)
    if not sample_path:
        raise HTTPException(status_code=404, detail="Sample video file not found.")
    return FileResponse(sample_path, media_type="video/mp4")


_cached_badminton_sample = None

@app.get("/api/sports/badminton/sample")
def badminton_analyze_sample():
    """Run real badminton biomechanics analysis on the sample clip."""
    global _cached_badminton_sample
    # Clear cache if needed to ensure fresh analysis runs on real badminton rally
    import os
    candidates = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "plugins", "sports", "badminton", "assets", "badminton_sample_rally.mp4")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "gait", "assets", "sample_toddler_walk.mp4")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend", "app", "gait", "assets", "sample_toddler_walk.mp4")),
    ]
    sample_path = next((c for c in candidates if os.path.exists(c)), None)
    if not sample_path:
        raise HTTPException(status_code=404, detail="Sample video not found.")

    if _cached_badminton_sample is not None and _cached_badminton_sample.get("video", {}).get("filename") == "badminton_sample_rally.mp4":
        return _cached_badminton_sample

    pipeline = get_badminton_pipeline()
    with open(sample_path, "rb") as f:
        content = f.read()

    sample_player_meta = None
    if PlayerMetadata:
        sample_player_meta = PlayerMetadata(
            age=23,
            body_weight_kg=72.0,
            session_duration_min=45.0,
            skill_level="intermediate",
            match_type="singles"
        )

    result = pipeline.analyze_video_bytes(
        video_bytes=content,
        filename="badminton_sample_rally.mp4",
        player_metadata=sample_player_meta
    )
    _badminton_assessments[result.analysis_id] = result
    try:
        saar_engine.register_badminton_investigation(result)
    except Exception as reg_err:
        print(f"[Main] Warning: Failed to register badminton sample investigation: {reg_err}")
    _cached_badminton_sample = result.model_dump()
    return _cached_badminton_sample


@app.post("/api/sports/badminton/longitudinal")
def badminton_compare_longitudinal(payload: Dict[str, Any]):
    """
    Phase 17: Deterministic multi-session trend analysis for the same player_id.
    Compares shot accuracy, distribution, coverage, speeds, recovery tempo,
    and joint kinematics with non-causal epistemic discipline.
    """
    raw_sessions = payload.get("sessions", [])
    analysis_ids = payload.get("analysis_ids", [])
    player_id = payload.get("player_id")

    sessions: List[Any] = []
    if raw_sessions:
        for s in raw_sessions:
            if isinstance(s, dict):
                sessions.append(BadmintonAnalysisResult.model_validate(s))
            else:
                sessions.append(s)
    elif analysis_ids:
        for aid in analysis_ids:
            if aid in _badminton_assessments:
                sessions.append(_badminton_assessments[aid])
    elif player_id:
        for aid, assessment in _badminton_assessments.items():
            sess_player = getattr(assessment, "player_id", None) or (
                assessment.player_metadata.player_id if assessment.player_metadata else None
            )
            if sess_player == player_id:
                sessions.append(assessment)

    if len(sessions) < 2:
        raise HTTPException(
            status_code=400,
            detail=f"Longitudinal comparison requires at least 2 sessions for player '{player_id or 'unknown'}'. Found {len(sessions)}."
        )

    pipeline = get_badminton_pipeline()
    try:
        comparison = pipeline.compare_longitudinal_sessions(sessions, player_id=player_id)
        return comparison.model_dump()
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Longitudinal analysis failed: {err}")


@app.get("/api/sports/badminton/players/{player_id}/longitudinal")
def badminton_player_longitudinal(player_id: str):
    """
    Retrieve longitudinal trends and non-causal correlations for a specific athlete.
    """
    sessions = []
    for aid, assessment in _badminton_assessments.items():
        sess_player = getattr(assessment, "player_id", None) or (
            assessment.player_metadata.player_id if assessment.player_metadata else None
        )
        if sess_player == player_id:
            sessions.append(assessment)

    if len(sessions) < 2:
        raise HTTPException(
            status_code=404,
            detail=f"Insufficient sessions ({len(sessions)}) found for athlete '{player_id}'. Minimum 2 required."
        )

    pipeline = get_badminton_pipeline()
    try:
        comparison = pipeline.compare_longitudinal_sessions(sessions, player_id=player_id)
        return comparison.model_dump()
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Longitudinal analysis failed: {err}")



# ===================================================================
# MULTI-FORMAT TRANSCRIPT EXPORT WITH CONTENT-DISPOSITION
# ===================================================================

@app.post("/api/export/chat")
async def export_chat_endpoint(request: Request):
    """Generate and return a downloadable conversation transcript with Content-Disposition headers."""
    import json
    from datetime import datetime

    content_type = request.headers.get("content-type", "")
    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form = await request.form()
        raw_payload = form.get("payload", "{}")
        try:
            payload = json.loads(raw_payload)
        except Exception:
            payload = {}
    else:
        try:
            payload = await request.json()
        except Exception:
            payload = {}

    fmt = payload.get("format", "html").lower()
    if fmt not in ["html", "txt", "md"]:
        fmt = "html"

    messages = payload.get("messages", [])
    domain = payload.get("domain", "general").lower()
    inv_id = payload.get("investigation_id", f"SAAR-{int(datetime.now().timestamp())}")
    confidence = payload.get("confidence", 94)
    verdict = payload.get("verdict", "")
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_slug = datetime.now().strftime("%Y%m%d")

    if fmt == "html":
        filename = f"saar_chat_transcript_{domain}_{date_slug}.html"
        media_type = "text/html; charset=utf-8"

        turns_html = ""
        turn_idx = 1
        for msg in messages:
            is_assistant = msg.get("role") == "assistant"
            role_class = "turn-assistant" if is_assistant else "turn-user"
            role_title = "Saar Reasoning Agent" if is_assistant else "User"
            ts = msg.get("timestamp", "")
            time_badge = f"<span>{ts}</span>" if ts else ""
            raw_text = msg.get("text", "")
            safe_text = raw_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            
            files_html = ""
            files = msg.get("files", [])
            if files:
                files_html = f'<div class="files-pill">📎 Attached: {", ".join(files)}</div>'

            turns_html += f"""
    <div class="turn-box {role_class}">
      <div class="turn-header">
        <span>Turn {turn_idx}: {role_title}</span>
        {time_badge}
      </div>
      <div class="turn-body">
        {files_html}
        {safe_text}
      </div>
    </div>"""
            if is_assistant:
                turn_idx += 1

        verdict_html = ""
        if verdict:
            verdict_html = f"""
  <div class="verdict-card">
    <div class="verdict-title">Final Scientific Diagnostic Verdict</div>
    <div>{verdict}</div>
  </div>"""

        body_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SAAR Scientific Reasoning Transcript - {domain.upper()}</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      max-width: 900px;
      margin: 40px auto;
      padding: 0 24px;
      line-height: 1.65;
      color: #0f172a;
      background: #ffffff;
    }}
    .header-card {{
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 32px;
      background: #f8fafc;
    }}
    h1 {{
      margin-top: 0;
      color: #0f172a;
      font-size: 1.6rem;
      border-bottom: 2px solid #e2e8f0;
      padding-bottom: 12px;
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .meta-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 12px;
      margin-top: 16px;
    }}
    .meta-item {{
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 10px 14px;
    }}
    .meta-label {{ font-size: 0.75rem; color: #64748b; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em; }}
    .meta-value {{ font-size: 0.95rem; color: #0f172a; font-weight: 600; margin-top: 2px; }}
    .dialogue-thread {{ margin-top: 28px; }}
    .turn-box {{
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      margin-bottom: 20px;
      overflow: hidden;
    }}
    .turn-header {{
      padding: 10px 18px;
      font-size: 0.85rem;
      font-weight: 700;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid #e2e8f0;
    }}
    .turn-user .turn-header {{ background: #f8fafc; color: #334155; }}
    .turn-assistant .turn-header {{ background: #f0fdf4; color: #166534; border-bottom-color: #bbf7d0; }}
    .turn-body {{ padding: 18px 20px; font-size: 0.95rem; white-space: pre-wrap; word-break: break-word; }}
    .files-pill {{ background: #e0f2fe; color: #0369a1; padding: 4px 10px; border-radius: 9999px; font-size: 0.8rem; font-weight: 600; display: inline-block; margin-bottom: 12px; }}
    .verdict-card {{
      border: 1px solid #bfdbfe;
      background: #eff6ff;
      border-radius: 12px;
      padding: 24px;
      margin-top: 32px;
    }}
    .verdict-title {{ font-size: 1.1rem; font-weight: 700; color: #1e40af; margin-top: 0; margin-bottom: 8px; }}
    .footer-note {{ text-align: center; color: #94a3b8; font-size: 0.8rem; margin-top: 40px; padding-top: 20px; border-top: 1px solid #e2e8f0; }}
  </style>
</head>
<body>
  <div class="header-card">
    <h1>SAAR Scientific Reasoning Transcript</h1>
    <div class="meta-grid">
      <div class="meta-item"><div class="meta-label">Investigation ID</div><div class="meta-value">{inv_id}</div></div>
      <div class="meta-item"><div class="meta-label">Domain</div><div class="meta-value">{domain.upper()}</div></div>
      <div class="meta-item"><div class="meta-label">Timestamp</div><div class="meta-value">{date_str}</div></div>
      <div class="meta-item"><div class="meta-label">Confidence</div><div class="meta-value">{confidence}%</div></div>
    </div>
  </div>

  <div class="dialogue-thread">
    {turns_html}
  </div>

  {verdict_html}

  <div class="footer-note">Exported autonomously by SAAR — Visual Scientific Reasoning Engine</div>
</body>
</html>"""

    elif fmt == "txt":
        filename = f"saar_chat_transcript_{domain}_{date_slug}.txt"
        media_type = "text/plain; charset=utf-8"
        body_content = f"""================================================================================
SAAR SCIENTIFIC REASONING — COMPLETE CONVERSATION TRANSCRIPT
================================================================================

Investigation ID : {inv_id}
Scientific Domain: {domain.upper()}
Export Date      : {date_str}
Total Messages   : {len(messages)}
Graph Confidence : {confidence}%

--------------------------------------------------------------------------------

"""
        turn_idx = 1
        for msg in messages:
            is_assistant = msg.get("role") == "assistant"
            role_title = "SAAR REASONING AGENT" if is_assistant else "USER"
            ts = f"({msg.get('timestamp')})" if msg.get("timestamp") else ""
            body_content += f"[TURN {turn_idx}] {role_title} {ts}\n"
            files = msg.get("files", [])
            if files:
                body_content += f"Attached Files: {', '.join(files)}\n"
            body_content += f"--------------------------------------------------------------------------------\n"
            body_content += f"{msg.get('text', '')}\n\n"
            if is_assistant:
                turn_idx += 1

        if verdict:
            body_content += f"""================================================================================
FINAL SCIENTIFIC DIAGNOSTIC VERDICT
================================================================================
{verdict}

"""
        body_content += f"""================================================================================
Exported autonomously by SAAR — Visual Scientific Reasoning Engine
"""

    else: # md
        filename = f"saar_chat_transcript_{domain}_{date_slug}.md"
        media_type = "text/markdown; charset=utf-8"
        body_content = f"""# SAAR Scientific Reasoning — Complete Conversation Transcript

| Metadata | Details |
|---|---|
| **Investigation ID** | `{inv_id}` |
| **Domain** | **{domain.upper()}** |
| **Export Date & Time** | {date_str} |
| **Total Dialogue Turns** | {len(messages)} messages |
| **Reasoning Confidence** | **{confidence}%** |

---

## Dialogue Log

"""
        turn_idx = 1
        for msg in messages:
            is_assistant = msg.get("role") == "assistant"
            role_label = "Saar Reasoning Agent" if is_assistant else "User"
            ts = f" — {msg.get('timestamp')}" if msg.get("timestamp") else ""
            body_content += f"### Turn {turn_idx}: {role_label}{ts}\n\n"
            files = msg.get("files", [])
            if files:
                body_content += f"📎 **Attached Files**: `{', '.join(files)}`\n\n"
            body_content += f"{msg.get('text', '')}\n\n---\n\n"
            if is_assistant:
                turn_idx += 1

        if verdict:
            body_content += f"## Final Scientific Diagnostic Verdict\n\n{verdict}\n\n---\n"
        body_content += "*Exported autonomously by SAAR — Visual Scientific Reasoning Engine.*\n"

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": media_type
    }
    return Response(content=body_content.encode("utf-8"), media_type=media_type, headers=headers)


# ------------------------------------------------------------------
# Scientific Dictionary & Glossary Endpoints (GET compatibility)
# ------------------------------------------------------------------

@app.get("/api/dictionary/lookup")
@app.get("/dictionary/lookup")
def lookup_word_get(word: str = Query(..., description="Scientific term or word to look up")):
    """Look up a word or scientific term with definitions and diagnostic domain context."""
    if not word or not word.strip():
        raise HTTPException(status_code=400, detail="Word parameter is required.")
    return terminology_service.lookup_word(word.strip())




