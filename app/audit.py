"""Append-only audit log. Only masked text is ever written."""

import json
import threading
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "storage" / "audit.jsonl"
_lock = threading.Lock()


class AuditLog:
    def __init__(self, path: Path | None = DEFAULT_PATH) -> None:
        self.path = path

    def write(self, event: dict) -> None:
        if self.path is None:
            return
        record = {"ts": datetime.now(UTC).isoformat(timespec="seconds"), **event}
        with _lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
