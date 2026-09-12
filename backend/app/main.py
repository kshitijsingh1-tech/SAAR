import os
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

from fastapi import FastAPI, HTTPException, Query, Response, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional

from .schemas import InvestigationRequest, InvestigationResponse, BaselineComparisonModel
from .dynamic_loop import DynamicWorkflowOrchestrator

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

@app.options("/{full_path:path}")
def options_handler(full_path: str):
    return Response(status_code=200)

@app.get("/health")
@app.get("/api/health")
def health_check():
    return {"status": "ok", "engine": "Saar Scientific Reasoning Engine v1.0"}

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
    reasoning_task = asyncio.to_thread(saar_engine.answer_question, investigation_id, question)
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
    reasoning_task = asyncio.to_thread(saar_engine.answer_question, investigation_id, question)
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
# TODDLEAI GAIT ANALYSIS API (DEDICATED ENDPOINTS)
# ===================================================================

from .gait.pipeline import GaitAnalysisPipeline
from .gait.schemas import CanonicalGaitResult

_gait_pipeline: Optional[GaitAnalysisPipeline] = None
_gait_assessments: Dict[str, CanonicalGaitResult] = {}


def get_gait_pipeline() -> GaitAnalysisPipeline:
    global _gait_pipeline
    if _gait_pipeline is None:
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
        return result.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gait analysis failed: {str(e)}")


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
def gait_analyze_sample(child_age_months: int = Query(24, ge=6, le=120)):
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
        filename="sample_toddler_walk.mp4",
        child_age_months=child_age_months
    )
    _gait_assessments[result.assessment_id] = result
    try:
        saar_engine.register_gait_investigation(result)
    except Exception as reg_err:
        print(f"[Main] Warning: Failed to register gait sample investigation: {reg_err}")
    return result.model_dump()


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




