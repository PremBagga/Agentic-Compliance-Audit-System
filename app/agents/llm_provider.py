from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _match_requirement(document_tokens: set[str], requirement: str) -> bool:
    requirement_tokens = _tokenize(requirement)
    return bool(document_tokens.intersection(requirement_tokens))


def _policy_overlap(document_tokens: set[str], policy: Dict[str, Any]) -> int:
    tokens = _tokenize(str(policy.get("title", "")))
    tokens.update(_tokenize(str(policy.get("description", ""))))
    for requirement in list(policy.get("requirements", []) or []):
        tokens.update(_tokenize(str(requirement)))
    return len(document_tokens.intersection(tokens))


@dataclass
class BaseLLMAdapter:
    model_name: str
    provider_name: str = "deterministic"

    def evaluate_policy(self, document_text: str, policy: Dict[str, Any]) -> Dict[str, Any]:
        document_tokens = _tokenize(document_text)
        requirements = list(policy.get("requirements", []) or [])
        matched_requirements = [requirement for requirement in requirements if _match_requirement(document_tokens, requirement)]
        missing_requirements = [requirement for requirement in requirements if requirement not in matched_requirements]

        severity = str(policy.get("severity", "LOW")).upper()
        category = str(policy.get("category", "unknown"))
        policy_title = str(policy.get("title", "Unnamed Policy"))
        policy_id = str(policy.get("id", ""))

        overlap = _policy_overlap(document_tokens, policy)
        req_count = max(1, len(requirements))
        coverage = len(matched_requirements) / req_count

        base_confidence = 0.4 + 0.08 * len(matched_requirements) + min(0.2, 0.03 * overlap)
        evidence = "; ".join(matched_requirements[:2]) if matched_requirements else "No direct evidence located in the document."
        recommendation = f"Address {len(missing_requirements)} missing requirement(s) for {policy_title}."

        # If the policy is not materially represented in the document, treat it as not applicable.
        if overlap < 2 and len(matched_requirements) == 0:
            return {
                "violation_found": False,
                "severity": "LOW",
                "evidence": "Policy not materially referenced by document content.",
                "matched_requirements": matched_requirements,
                "missing_requirements": missing_requirements,
                "recommendation": "No action required for this policy context.",
                "confidence": round(min(0.95, max(0.35, base_confidence)), 2),
            }

        threshold_by_severity = {"HIGH": 0.75, "MEDIUM": 0.6, "LOW": 0.5}
        threshold = threshold_by_severity.get(severity, 0.6)
        should_raise = coverage < threshold or len(document_text.strip()) < 40

        if not should_raise:
            return {
                "violation_found": False,
                "severity": "LOW",
                "evidence": evidence,
                "matched_requirements": matched_requirements,
                "missing_requirements": missing_requirements,
                "recommendation": recommendation,
                "confidence": round(min(0.95, max(0.35, base_confidence)), 2),
            }

        finding_severity = severity if severity in {"LOW", "MEDIUM", "HIGH"} else "LOW"
        if severity == "HIGH" and coverage < 0.65:
            finding_severity = "HIGH"
        elif severity == "MEDIUM" and coverage < 0.7:
            finding_severity = "MEDIUM"
        elif coverage >= 0.7:
            finding_severity = "LOW"

        return {
            "violation_found": True,
            "policy_id": policy_id,
            "policy_title": policy_title,
            "category": category,
            "severity": finding_severity,
            "status": "OPEN",
            "evidence": evidence,
            "matched_requirements": matched_requirements,
            "missing_requirements": missing_requirements,
            "recommendation": recommendation,
            "confidence": round(min(0.95, max(0.35, base_confidence + 0.05)), 2),
        }

    def reflect_on_findings(self, findings: List[Dict[str, Any]]) -> List[str]:
        if not findings:
            return []
        high_count = sum(1 for finding in findings if str(finding.get("severity", "LOW")).upper() == "HIGH")
        medium_count = sum(1 for finding in findings if str(finding.get("severity", "LOW")).upper() == "MEDIUM")
        notes = [
            f"Review coverage for {len(findings)} finding(s) across {high_count} high-risk and {medium_count} medium-risk issues.",
            "Validate whether evidence supports the stated gaps before finalizing the audit.",
        ]
        if high_count:
            notes.append("Escalate the high-risk items for human review before closure.")
        return notes[:3]


@dataclass
class GroqLLMAdapter(BaseLLMAdapter):
    api_key: str = ""
    base_url: str = "https://api.groq.com"
    provider_name: str = "groq"

    def _extract_json(self, content: str) -> Dict[str, Any]:
        stripped = (content or "").strip()
        if not stripped:
            return {}

        try:
            return json.loads(stripped)
        except Exception:
            pass

        match = re.search(r"\{[\s\S]*\}", stripped)
        if not match:
            return {}
        try:
            return json.loads(match.group(0))
        except Exception:
            return {}

    def _chat_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        try:
            from groq import Groq

            client = Groq(api_key=self.api_key, base_url=self.base_url)
            try:
                response = client.chat.completions.create(
                    model=self.model_name,
                    temperature=0,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={"type": "json_object"},
                )
            except Exception:
                response = client.chat.completions.create(
                    model=self.model_name,
                    temperature=0,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
            content = response.choices[0].message.content if response and response.choices else ""
            return self._extract_json(content or "")
        except Exception:
            return {}

    def evaluate_policy(self, document_text: str, policy: Dict[str, Any]) -> Dict[str, Any]:
        fallback = super().evaluate_policy(document_text, policy)
        if not self.api_key:
            return fallback

        prompt_system = (
            "You are a compliance audit assistant. Return strict JSON only. "
            "Do not include markdown."
        )
        prompt_user = (
            "Audit the document against the policy and return JSON with keys: "
            "violation_found(boolean), policy_id(string), policy_title(string), category(string), "
            "severity(LOW|MEDIUM|HIGH), status(string), evidence(string), matched_requirements(array), "
            "missing_requirements(array), recommendation(string), confidence(number 0..1).\n\n"
            f"Policy:\n{json.dumps(policy, ensure_ascii=False)}\n\n"
            f"Document:\n{document_text[:12000]}"
        )

        llm_json = self._chat_json(prompt_system, prompt_user)
        if not llm_json:
            return fallback

        try:
            return {
                "violation_found": bool(llm_json.get("violation_found", fallback.get("violation_found", True))),
                "policy_id": str(llm_json.get("policy_id", policy.get("id", fallback.get("policy_id", "")))),
                "policy_title": str(llm_json.get("policy_title", policy.get("title", fallback.get("policy_title", "Unnamed Policy")))),
                "category": str(llm_json.get("category", policy.get("category", fallback.get("category", "unknown")))),
                "severity": str(llm_json.get("severity", fallback.get("severity", "LOW"))).upper(),
                "status": str(llm_json.get("status", "OPEN")),
                "evidence": str(llm_json.get("evidence", fallback.get("evidence", ""))),
                "matched_requirements": list(llm_json.get("matched_requirements", fallback.get("matched_requirements", [])) or []),
                "missing_requirements": list(llm_json.get("missing_requirements", fallback.get("missing_requirements", [])) or []),
                "recommendation": str(llm_json.get("recommendation", fallback.get("recommendation", "Review policy controls."))),
                "confidence": float(llm_json.get("confidence", fallback.get("confidence", 0.5))),
            }
        except Exception:
            return fallback

    def reflect_on_findings(self, findings: List[Dict[str, Any]]) -> List[str]:
        fallback = super().reflect_on_findings(findings)
        if not self.api_key or not findings:
            return fallback

        prompt_system = "You are a compliance reflection assistant. Return strict JSON only."
        prompt_user = (
            "Given audit findings, return JSON with key notes as an array of 2 to 3 concise strings.\n\n"
            f"Findings:\n{json.dumps(findings, ensure_ascii=False)[:12000]}"
        )

        llm_json = self._chat_json(prompt_system, prompt_user)
        notes = llm_json.get("notes", []) if isinstance(llm_json, dict) else []
        if not isinstance(notes, list) or not notes:
            return fallback
        normalized = [str(note).strip() for note in notes if str(note).strip()]
        return normalized[:3] if normalized else fallback


def _create_adapter(model_name: str) -> BaseLLMAdapter:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com").strip() or "https://api.groq.com"
    if api_key:
        return GroqLLMAdapter(model_name=model_name, api_key=api_key, base_url=base_url)
    return BaseLLMAdapter(model_name=model_name)


def get_base_llm() -> BaseLLMAdapter:
    return _create_adapter(os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile"))


def get_audit_llm() -> BaseLLMAdapter:
    return _create_adapter(os.getenv("AUDIT_MODEL_NAME", os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")))
