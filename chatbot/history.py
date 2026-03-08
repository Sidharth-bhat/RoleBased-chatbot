"""
Per-user conversation history.

Stored in-memory as a deque capped at HISTORY_MAX_MESSAGES per user.
Sufficient for a short-lived session model; replace with Redis or a DB
for multi-process / persistent deployments.
"""
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import List, Dict


class ConversationHistory:
    def __init__(self, max_messages: int = 50):
        self._max = max_messages
        # user_id → deque of message dicts
        self._store: Dict[str, deque] = defaultdict(lambda: deque(maxlen=self._max))

    def add(self, user_id: str, role: str, query: str, response: str) -> None:
        """Append a user/assistant exchange for a given user."""
        ts = datetime.now(timezone.utc).isoformat()
        self._store[user_id].append({"role": "user",      "content": query,    "timestamp": ts})
        self._store[user_id].append({"role": "assistant", "content": response, "timestamp": ts})

    def get(self, user_id: str) -> List[Dict]:
        """Return all stored messages for a user (oldest first)."""
        return list(self._store.get(user_id, deque()))

    def clear(self, user_id: str) -> None:
        """Clear history for a specific user."""
        if user_id in self._store:
            self._store[user_id].clear()

    def user_count(self) -> int:
        return len(self._store)
