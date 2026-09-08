import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI, HTTPException, Query, Response, Request
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

from fastapi import UploadFile, File
from .services.reasoning_service import ReasoningService
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
        return saar_engine.get_report(state.investigation_id)
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
def saar_answer(investigation_id: str, answer: UserAnswer):
    """Submit user answer → belief update → new questions."""
    try:
        state = saar_engine.process_answer(investigation_id, answer)
        return saar_engine.get_report(investigation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/saar/investigation/{investigation_id}/ask")
def saar_ask(investigation_id: str, payload: Dict[str, str]):
    """Ask a natural-language question about the investigation."""
    question = payload.get("question", "")
    if not question:
        raise HTTPException(status_code=400, detail="Question is required.")
    res = saar_engine.answer_question(investigation_id, question)
    if isinstance(res, dict) and "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res

@app.post("/api/saar/ask")
def saar_general_ask(payload: Dict[str, Any]):
    """Ask a freeform natural-language scientific query with autonomous RAG & dynamic AI synthesis."""
    question = payload.get("question", "")
    domain = payload.get("domain", "agriculture")
    investigation_id = payload.get("investigation_id") or "latest"
    if not question:
        raise HTTPException(status_code=400, detail="Question is required.")
    res = saar_engine.answer_question(investigation_id, question)
    return res

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

  <div class="footer-note">Exported autonomously by SAAR (सार) — Visual Scientific Reasoning Engine</div>
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
Exported autonomously by SAAR (सार) — Visual Scientific Reasoning Engine
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
        body_content += "*Exported autonomously by SAAR (सार) — Visual Scientific Reasoning Engine.*\n"

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": media_type
    }
    return Response(content=body_content.encode("utf-8"), media_type=media_type, headers=headers)

