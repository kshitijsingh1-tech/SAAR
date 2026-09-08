import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI, HTTPException, Query, Response
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
