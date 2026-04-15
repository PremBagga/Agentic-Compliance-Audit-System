from __future__ import annotations

from copy import deepcopy
from typing import Dict, List


def _policy(
    policy_id: str,
    title: str,
    description: str,
    category: str,
    severity: str,
    requirements: List[str],
) -> Dict[str, object]:
    return {
        "id": policy_id,
        "title": title,
        "description": description,
        "category": category,
        "severity": severity,
        "requirements": requirements,
    }


POLICY_MAP: Dict[str, List[Dict[str, object]]] = {
    "security": [
        _policy(
            "SEC-001",
            "Access Control Enforcement",
            "Critical systems must enforce least-privilege access control.",
            "security",
            "HIGH",
            ["role-based access control", "least privilege", "access review"],
        ),
        _policy(
            "SEC-002",
            "Encryption At Rest",
            "Sensitive data must be encrypted at rest using approved algorithms.",
            "security",
            "HIGH",
            ["encryption at rest", "approved algorithm", "key management"],
        ),
    ],
    "privacy": [
        _policy(
            "PRI-001",
            "Data Minimization",
            "Collect and retain only the minimum personal data necessary.",
            "privacy",
            "MEDIUM",
            ["data minimization", "purpose limitation", "retention policy"],
        ),
        _policy(
            "PRI-002",
            "Consent and Notice",
            "Personal data processing must be covered by clear notice and valid consent.",
            "privacy",
            "HIGH",
            ["privacy notice", "consent", "lawful basis"],
        ),
    ],
    "compliance": [
        _policy(
            "COMP-001",
            "Audit Trail Retention",
            "Audit evidence and decisions must be retained for review.",
            "compliance",
            "MEDIUM",
            ["audit trail", "retention", "evidence"],
        ),
        _policy(
            "COMP-002",
            "Control Exception Approval",
            "Any material exception must be approved and documented.",
            "compliance",
            "HIGH",
            ["exception approval", "documented waiver", "approval record"],
        ),
    ],
    "financial": [
        _policy(
            "FIN-001",
            "Segregation of Duties",
            "Financial workflows must separate preparation, approval, and release duties.",
            "financial",
            "HIGH",
            ["segregation of duties", "approval workflow", "release control"],
        ),
        _policy(
            "FIN-002",
            "Reconciliation Evidence",
            "Periodic reconciliation must be documented with variance explanations.",
            "financial",
            "MEDIUM",
            ["reconciliation", "variance explanation", "review signoff"],
        ),
    ],
}


DEFAULT_POLICIES: List[Dict[str, object]] = [
    deepcopy(POLICY_MAP["security"][0]),
    deepcopy(POLICY_MAP["privacy"][0]),
    deepcopy(POLICY_MAP["compliance"][0]),
    deepcopy(POLICY_MAP["financial"][0]),
    deepcopy(POLICY_MAP["security"][1]),
]


def get_all_policies() -> List[Dict[str, object]]:
    policies: List[Dict[str, object]] = []
    for group in POLICY_MAP.values():
        policies.extend(deepcopy(group))
    return policies


def get_default_policies() -> List[Dict[str, object]]:
    return deepcopy(DEFAULT_POLICIES)


def get_policies_for_categories(categories: List[str]) -> List[Dict[str, object]]:
    normalized = {category.strip().lower() for category in categories if category and category.strip()}
    if not normalized or "all" in normalized:
        return get_all_policies()

    selected: List[Dict[str, object]] = []
    for category in normalized:
        selected.extend(deepcopy(POLICY_MAP.get(category, [])))
    return selected
