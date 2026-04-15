from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.models.schemas import AuditState


@dataclass
class DocumentRepository:
    _lock: Lock = field(default_factory=Lock, init=False)
    _documents: Dict[str, Dict[str, Any]] = field(default_factory=dict, init=False)

    def create_document(self, filename: str, text: str) -> Dict[str, Any]:
        document_id = uuid4().hex
        record = {
            "document_id": document_id,
            "filename": filename,
            "text": text,
            "text_length": len(text or ""),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with self._lock:
            self._documents[document_id] = record
        return dict(record)

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            document = self._documents.get(document_id)
        return dict(document) if document else None

    def count(self) -> int:
        with self._lock:
            return len(self._documents)


@dataclass
class AuditRepository:
    _lock: Lock = field(default_factory=Lock, init=False)
    _audits: Dict[str, Dict[str, Any]] = field(default_factory=dict, init=False)

    def save_audit(self, audit_state: AuditState | Dict[str, Any]) -> Dict[str, Any]:
        normalized = AuditState.model_validate(audit_state).model_dump()
        with self._lock:
            self._audits[normalized["audit_id"]] = normalized
        return dict(normalized)

    def get_audit(self, audit_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            audit = self._audits.get(audit_id)
        return dict(audit) if audit else None

    def update_audit(self, audit_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            current = dict(self._audits.get(audit_id, {"audit_id": audit_id}))
            current.update(updates)
            self._audits[audit_id] = current
        return dict(current)

    def count(self) -> int:
        with self._lock:
            return len(self._audits)

    def list_audits(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [dict(value) for value in self._audits.values()]
