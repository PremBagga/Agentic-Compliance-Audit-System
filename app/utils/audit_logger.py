from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Dict, List


class AuditLogger:
    def __init__(self) -> None:
        self._lock = Lock()
        self._logs: Dict[str, List[Dict[str, str]]] = {}

    def log_step(self, audit_id: str, step: str, message: str) -> Dict[str, str]:
        entry = {
            "audit_id": audit_id,
            "step": step,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with self._lock:
            self._logs.setdefault(audit_id, []).append(entry)
        return entry

    def get_logs(self, audit_id: str) -> List[Dict[str, str]]:
        with self._lock:
            return list(self._logs.get(audit_id, []))
