from __future__ import annotations

from typing import Any, Dict, List

from app.agents.llm_provider import BaseLLMAdapter


def audit_document(document_text: str, policies: List[Dict[str, Any]], audit_llm: BaseLLMAdapter) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    if not policies:
        return findings

    safe_document_text = document_text or ""
    for policy in policies:
        safe_policy = dict(policy or {})
        try:
            evaluation = audit_llm.evaluate_policy(safe_document_text, safe_policy)
        except Exception:
            evaluation = {
                "violation_found": True,
                "policy_id": str(safe_policy.get("id", "")),
                "policy_title": str(safe_policy.get("title", "Unnamed Policy")),
                "category": str(safe_policy.get("category", "unknown")),
                "severity": str(safe_policy.get("severity", "LOW")).upper(),
                "status": "OPEN",
                "evidence": "Evaluation fallback was used.",
                "matched_requirements": [],
                "missing_requirements": list(safe_policy.get("requirements", []) or []),
                "recommendation": f"Review {safe_policy.get('title', 'policy')} manually.",
                "confidence": 0.5,
            }

        if not evaluation or not evaluation.get("violation_found"):
            continue

        finding = {
            "policy_id": str(evaluation.get("policy_id", safe_policy.get("id", ""))),
            "policy_title": str(evaluation.get("policy_title", safe_policy.get("title", "Unnamed Policy"))),
            "category": str(evaluation.get("category", safe_policy.get("category", "unknown"))),
            "severity": str(evaluation.get("severity", safe_policy.get("severity", "LOW"))).upper(),
            "status": str(evaluation.get("status", "OPEN")),
            "evidence": str(evaluation.get("evidence", "")),
            "matched_requirements": list(evaluation.get("matched_requirements", []) or []),
            "missing_requirements": list(evaluation.get("missing_requirements", []) or []),
            "recommendation": str(evaluation.get("recommendation", "Review the policy gap.")),
            "confidence": float(evaluation.get("confidence", 0.5)),
        }
        findings.append(finding)

    return findings
