"""
Persistent audit logger.

Each interaction is appended as a JSON line to data/audit_log.jsonl so the
log survives server restarts. An in-memory deque provides fast recent-entry
lookups without re-reading the file.
"""
import json
import os
from collections import deque
from datetime import datetime, timezone
from typing import Optional


class AuditLogger:
    def __init__(self, log_path: str, max_memory: int = 500):
        self._path = log_path
        self._memory: deque = deque(maxlen=max_memory)
        self._counter = 0
        self._load_existing()

    # ── Public interface ───────────────────────────────────────────────────────

    def log(
        self,
        user_id: str,
        role: str,
        query: str,
        response: str,
        guardrail_triggered: bool,
    ) -> dict:
        """Append one interaction to the log and return the entry."""
        self._counter += 1
        entry = {
            "id":                  self._counter,
            "timestamp":           datetime.now(timezone.utc).isoformat(),
            "user_id":             user_id,
            "role":                role,
            "query":               query[:120],          # truncate for privacy
            "response_length":     len(response),
            "guardrail_triggered": guardrail_triggered,
        }
        self._memory.append(entry)
        self._write(entry)
        return entry

    def get_recent(self, n: int = 50) -> list:
        """Return the n most recent audit entries (in-memory)."""
        entries = list(self._memory)
        return entries[-n:]

    @property
    def total(self) -> int:
        return self._counter

    # ── Internal ───────────────────────────────────────────────────────────────

    def _write(self, entry: dict) -> None:
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def _load_existing(self) -> None:
        """Seed memory deque from existing log file (if any)."""
        if not os.path.exists(self._path):
            return
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    entry = json.loads(line)
                    self._memory.append(entry)
                    self._counter = max(self._counter, entry.get("id", 0))
            print(f"📋 Audit log restored: {self._counter} entries loaded.")
        except (json.JSONDecodeError, OSError) as e:
            print(f"⚠️  Could not load audit log: {e}")
