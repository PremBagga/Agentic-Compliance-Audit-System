from __future__ import annotations

import sys
from pathlib import Path
from typing import List
from uuid import uuid4

APP_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = APP_ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env", override=False)
except Exception:
    pass

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.agents.llm_provider import get_audit_llm, get_base_llm
from app.graph import create_audit_graph
from app.ingestion.pdf_parser import parse_document_bytes
from app.models.schemas import ApproveRequest, AuditState, RunAuditRequest, UploadResponse
from app.utils.audit_logger import AuditLogger
from app.utils.repositories import AuditRepository, DocumentRepository


app = FastAPI(title="Agentic Compliance & Audit Intelligence System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

document_repository = DocumentRepository()
audit_repository = AuditRepository()
audit_logger = AuditLogger()
base_llm = get_base_llm()
audit_llm = get_audit_llm()
audit_graph = create_audit_graph(document_repository, audit_repository, audit_logger, base_llm, audit_llm)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "documents": document_repository.count(),
        "audits": audit_repository.count(),
        "base_llm_provider": getattr(base_llm, "provider_name", "unknown"),
        "audit_llm_provider": getattr(audit_llm, "provider_name", "unknown"),
        "base_model": getattr(base_llm, "model_name", "unknown"),
        "audit_model": getattr(audit_llm, "model_name", "unknown"),
    }


@app.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    filename = file.filename or "uploaded-document"
    suffix = Path(filename).suffix.lower()
    if suffix not in {".pdf", ".txt", ".md", ".csv", ".log", ""}:
        raise HTTPException(status_code=400, detail="Only PDF and TXT-style documents are supported.")

    raw_bytes = await file.read()
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    document_text = parse_document_bytes(filename, raw_bytes)
    record = document_repository.create_document(filename, document_text)
    audit_logger.log_step(record["document_id"], "upload", f"Document {filename} uploaded successfully.")
    return UploadResponse(document_id=record["document_id"], filename=filename, text_length=record["text_length"])


@app.post("/run_audit")
def run_audit(request: RunAuditRequest) -> dict:
    document = document_repository.get_document(request.document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    audit_id = uuid4().hex
    initial_state = AuditState(
        audit_id=audit_id,
        document_id=request.document_id,
        document_name=str(document.get("filename", "")),
        document_text="",
        selected_policy_categories=list(request.selected_policies or []),
        status="RUNNING",
    ).model_dump()

    audit_repository.save_audit(initial_state)
    audit_logger.log_step(audit_id, "run_audit", f"Audit started for document {request.document_id}.")

    final_state = audit_graph.invoke(initial_state)
    normalized = AuditState.model_validate(final_state).model_dump()
    audit_repository.save_audit(normalized)
    return normalized


@app.post("/approve")
def approve_audit(request: ApproveRequest) -> dict:
    current = audit_repository.get_audit(request.audit_id)
    if not current:
        raise HTTPException(status_code=404, detail="Audit not found.")

    updates = {
        "approved": bool(request.approved),
        "status": "APPROVED" if request.approved else "REJECTED",
        "needs_approval": False,
    }
    updated = audit_repository.update_audit(request.audit_id, updates)
    audit_logger.log_step(request.audit_id, "approve", f"Human approval updated to {request.approved}.")
    return AuditState.model_validate(updated).model_dump()


@app.get("/audit/{audit_id}")
def get_audit(audit_id: str) -> dict:
    audit = audit_repository.get_audit(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found.")
    return AuditState.model_validate(audit).model_dump()


@app.get("/audit_log/{audit_id}")
def get_audit_log(audit_id: str) -> List[dict]:
    return audit_logger.get_logs(audit_id)


@app.get("/")
def root() -> dict:
    return {"message": "Agentic Compliance & Audit Intelligence System"}
