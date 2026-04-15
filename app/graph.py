from __future__ import annotations

from typing import Any, Dict

from langgraph.graph import END, StateGraph

from app.agents.auditor import audit_document
from app.agents.llm_provider import BaseLLMAdapter
from app.agents.policy_agent import retrieve_relevant_policies
from app.agents.reflector import reflect_on_findings
from app.models.schemas import AuditState
from app.utils.audit_logger import AuditLogger
from app.utils.repositories import AuditRepository, DocumentRepository


def _normalize_state(state: Dict[str, Any]) -> Dict[str, Any]:
    return AuditState.model_validate(state).model_dump()


def create_audit_graph(
    document_repository: DocumentRepository,
    audit_repository: AuditRepository,
    audit_logger: AuditLogger,
    base_llm: BaseLLMAdapter,
    audit_llm: BaseLLMAdapter,
):
    def ingest_data(state: Dict[str, Any]) -> Dict[str, Any]:
        current_state = _normalize_state(state)
        audit_id = current_state.get("audit_id", "")
        document_id = current_state.get("document_id", "")
        document = document_repository.get_document(document_id) if document_id else None

        if not document:
            updates = {
                "status": "FAILED",
                "document_text": "",
                "document_name": "",
                "risk_level": "LOW",
                "confidence_score": 0.0,
            }
            audit_logger.log_step(audit_id, "ingest_data", f"Document {document_id or '[missing]'} not found.")
            return {**current_state, **updates}

        updates = {
            "document_text": document.get("text", ""),
            "document_name": document.get("filename", ""),
            "status": "RUNNING",
        }
        audit_logger.log_step(audit_id, "ingest_data", f"Loaded document {document_id} ({document.get('filename', '')}).")
        return {**current_state, **updates}

    def policy_retrieval(state: Dict[str, Any]) -> Dict[str, Any]:
        current_state = _normalize_state(state)
        audit_id = current_state.get("audit_id", "")
        selected_categories = current_state.get("selected_policy_categories", []) or []
        policies = retrieve_relevant_policies(current_state.get("document_text", ""), selected_categories)
        audit_logger.log_step(audit_id, "policy_retrieval", f"Retrieved {len(policies)} policy(ies) for categories: {selected_categories or ['default']}.")
        return {
            **current_state,
            "retrieved_policies": policies,
            "policy_count": len(policies),
        }

    def compliance_audit(state: Dict[str, Any]) -> Dict[str, Any]:
        current_state = _normalize_state(state)
        audit_id = current_state.get("audit_id", "")
        policies = current_state.get("retrieved_policies", []) or []
        findings = audit_document(current_state.get("document_text", ""), policies, audit_llm)
        audit_logger.log_step(audit_id, "compliance_audit", f"Generated {len(findings)} finding(s) from {len(policies)} policy(ies).")
        return {**current_state, "audit_findings": findings}

    def reflection_loop(state: Dict[str, Any]) -> Dict[str, Any]:
        current_state = _normalize_state(state)
        audit_id = current_state.get("audit_id", "")
        findings = current_state.get("audit_findings", []) or []
        iterations = int(current_state.get("reflection_iterations", 0) or 0)

        if not findings:
            audit_logger.log_step(audit_id, "reflection_loop", "Skipped reflection because no findings were produced.")
            return {**current_state, "reflection_notes": [], "reflection_iterations": iterations}

        if iterations >= 2:
            audit_logger.log_step(audit_id, "reflection_loop", "Maximum reflection iterations reached.")
            return current_state

        notes = reflect_on_findings(findings, base_llm)
        merged_notes = list(current_state.get("reflection_notes", []) or []) + notes
        audit_logger.log_step(audit_id, "reflection_loop", f"Reflection pass {iterations + 1} produced {len(notes)} note(s).")
        return {
            **current_state,
            "reflection_notes": merged_notes,
            "reflection_iterations": iterations + 1,
        }

    def decision_router(state: Dict[str, Any]) -> str:
        current_state = _normalize_state(state)
        findings = current_state.get("audit_findings", []) or []
        iterations = int(current_state.get("reflection_iterations", 0) or 0)
        high_count = sum(1 for finding in findings if str(finding.get("severity", "LOW")).upper() == "HIGH")
        if not findings:
            return "action_trigger"
        if iterations == 0:
            return "reflection_loop"
        if iterations == 1 and high_count > 0 and len(findings) >= 3:
            return "reflection_loop"
        return "action_trigger"

    def action_trigger(state: Dict[str, Any]) -> Dict[str, Any]:
        current_state = _normalize_state(state)
        audit_id = current_state.get("audit_id", "")
        findings = current_state.get("audit_findings", []) or []

        has_high = any(str(finding.get("severity", "LOW")).upper() == "HIGH" for finding in findings)
        has_medium = any(str(finding.get("severity", "LOW")).upper() == "MEDIUM" for finding in findings)

        if has_high:
            risk_level = "HIGH"
            status = "WAITING_FOR_APPROVAL"
            needs_approval = True
        elif has_medium:
            risk_level = "MEDIUM"
            status = "COMPLETE"
            needs_approval = False
        else:
            risk_level = "LOW"
            status = "COMPLETE"
            needs_approval = False

        confidence = 0.5 + min(0.35, 0.08 * len(findings)) + (0.05 if current_state.get("reflection_notes") else 0.0)
        confidence = round(min(0.98, confidence), 2)

        final_state = {
            **current_state,
            "risk_level": risk_level,
            "confidence_score": confidence,
            "status": status,
            "needs_approval": needs_approval,
        }
        audit_repository.save_audit(final_state)
        audit_logger.log_step(audit_id, "action_trigger", f"Finalized audit with risk={risk_level}, confidence={confidence}, status={status}.")
        return final_state

    workflow = StateGraph(dict)
    workflow.add_node("ingest_data", ingest_data)
    workflow.add_node("policy_retrieval", policy_retrieval)
    workflow.add_node("compliance_audit", compliance_audit)
    workflow.add_node("reflection_loop", reflection_loop)
    workflow.add_node("decision_router", lambda state: state)
    workflow.add_node("action_trigger", action_trigger)

    workflow.set_entry_point("ingest_data")
    workflow.add_edge("ingest_data", "policy_retrieval")
    workflow.add_edge("policy_retrieval", "compliance_audit")
    workflow.add_edge("compliance_audit", "decision_router")
    workflow.add_conditional_edges(
        "decision_router",
        decision_router,
        {
            "reflection_loop": "reflection_loop",
            "action_trigger": "action_trigger",
        },
    )
    workflow.add_edge("reflection_loop", "decision_router")
    workflow.add_edge("action_trigger", END)

    return workflow.compile()
