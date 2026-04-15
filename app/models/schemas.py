from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field


class PolicyItem(BaseModel):
    id: str
    title: str
    description: str
    category: str
    severity: str
    requirements: List[str] = Field(default_factory=list)


class FindingItem(BaseModel):
    policy_id: str = ""
    policy_title: str = ""
    category: str = ""
    severity: str = "LOW"
    status: str = "OPEN"
    evidence: str = ""
    matched_requirements: List[str] = Field(default_factory=list)
    missing_requirements: List[str] = Field(default_factory=list)
    recommendation: str = ""
    confidence: float = 0.5


class AuditState(BaseModel):
    model_config = ConfigDict(extra="allow")

    audit_id: str = ""
    document_id: str = ""
    document_name: str = ""
    document_text: str = ""
    selected_policy_categories: List[str] = Field(default_factory=list)
    retrieved_policies: List[Dict[str, Any]] = Field(default_factory=list)
    audit_findings: List[Dict[str, Any]] = Field(default_factory=list)
    reflection_notes: List[str] = Field(default_factory=list)
    risk_level: str = "LOW"
    confidence_score: float = 0.5
    status: str = "PENDING"
    approved: bool = False
    needs_approval: bool = False
    reflection_iterations: int = 0
    policy_count: int = 0


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    text_length: int


class RunAuditRequest(BaseModel):
    document_id: str
    selected_policies: List[str] = Field(default_factory=list)


class ApproveRequest(BaseModel):
    audit_id: str
    approved: bool = True


class AuditLogEntry(BaseModel):
    audit_id: str
    step: str
    message: str
    timestamp: str
