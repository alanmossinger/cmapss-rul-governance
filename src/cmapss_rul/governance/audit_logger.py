"""Append-only audit logger.

Specification: governance/audit-trail.md
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class AuditLogger:
    """Append-only audit log. Records are immutable once written."""

    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, record_type: str, payload: dict[str, Any]) -> str:
        """Append a record to the audit log. Returns the record_id."""
        record_id = str(uuid.uuid4())
        record = {
            "record_id": record_id,
            "record_type": record_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **payload,
        }
        with self.log_path.open("a") as f:
            f.write(json.dumps(record) + "\n")
        return record_id
