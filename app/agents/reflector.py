from __future__ import annotations

from typing import Any, Dict, List

from app.agents.llm_provider import BaseLLMAdapter


def reflect_on_findings(findings: List[Dict[str, Any]], base_llm: BaseLLMAdapter) -> List[str]:
    if not findings:
        return []

    try:
        notes = base_llm.reflect_on_findings(findings)
    except Exception:
        notes = []

    if not notes:
        high_count = sum(1 for finding in findings if str(finding.get("severity", "LOW")).upper() == "HIGH")
        notes = [
            f"Reflection summary: {len(findings)} finding(s) reviewed.",
            f"High-risk findings: {high_count}.",
        ]

    return notes[:3]
