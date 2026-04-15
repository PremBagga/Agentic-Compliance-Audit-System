from __future__ import annotations

import re
from typing import Dict, List, Sequence

from app.agents.policy_store import get_all_policies, get_default_policies, get_policies_for_categories


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _policy_score(document_tokens: set[str], policy: Dict[str, object]) -> int:
    policy_tokens = _tokenize(str(policy.get("title", "")))
    policy_tokens.update(_tokenize(str(policy.get("description", ""))))
    for requirement in policy.get("requirements", []) or []:
        policy_tokens.update(_tokenize(str(requirement)))
    return len(document_tokens.intersection(policy_tokens))


def _deduplicate_policies(policies: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    unique: List[Dict[str, object]] = []
    seen: set[str] = set()
    for policy in policies:
        policy_id = str(policy.get("id", ""))
        if not policy_id or policy_id in seen:
            continue
        seen.add(policy_id)
        unique.append(dict(policy))
    return unique


def _top_up_policies(primary: List[Dict[str, object]], fallback: List[Dict[str, object]], top_k: int) -> List[Dict[str, object]]:
    combined = _deduplicate_policies(primary)
    min_required = 3
    if len(combined) >= top_k:
        return combined[:top_k]
    for policy in fallback:
        policy_id = str(policy.get("id", ""))
        if policy_id and all(str(item.get("id", "")) != policy_id for item in combined):
            combined.append(dict(policy))
        if len(combined) >= min_required:
            break
    if len(combined) < min_required:
        for policy in get_all_policies():
            policy_id = str(policy.get("id", ""))
            if policy_id and all(str(item.get("id", "")) != policy_id for item in combined):
                combined.append(dict(policy))
            if len(combined) >= min_required:
                break
    return combined[: max(min_required, min(top_k, len(combined)))]


def retrieve_relevant_policies(document_text: str, selected_categories: List[str] | None = None, top_k: int = 5) -> List[Dict[str, object]]:
    categories = [category for category in (selected_categories or []) if category]
    if not categories:
        candidates = get_default_policies()
    elif any(category.strip().lower() == "all" for category in categories):
        candidates = get_all_policies()
    else:
        candidates = get_policies_for_categories(categories)

    if not candidates:
        candidates = get_default_policies()

    document_tokens = _tokenize(document_text)
    ranked = sorted(candidates, key=lambda policy: _policy_score(document_tokens, policy), reverse=True)
    positively_ranked = [policy for policy in ranked if _policy_score(document_tokens, policy) > 0]
    selected = positively_ranked[:top_k] if positively_ranked else ranked[:top_k]
    selected = _top_up_policies(selected, get_default_policies(), top_k)
    return selected or get_default_policies()
