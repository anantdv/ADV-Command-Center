from datetime import timedelta
from threading import Lock
from typing import Any
from uuid import uuid4

from app.utils.datetime import utc_now


class ConfirmationStore:
    """Single-use expiring confirmation store. TODO: replace with Redis for multi-worker deployments."""
    def __init__(self):
        self._items: dict[str, dict[str, Any]] = {}
        self._lock = Lock()

    def create(self, payload: dict, expires_in_seconds: int = 900) -> str:
        confirmation_id = f"conf_{uuid4().hex[:16]}"
        now = utc_now()
        with self._lock:
            self._items[confirmation_id] = {**payload, "confirmation_id":confirmation_id, "created_at":now.isoformat(), "expires_at":(now + timedelta(seconds=expires_in_seconds)).isoformat()}
        return confirmation_id

    def get(self, confirmation_id: str) -> dict | None:
        with self._lock:
            item = self._items.get(confirmation_id)
            if not item: return None
            if utc_now().isoformat() >= item["expires_at"]:
                self._items.pop(confirmation_id, None);return None
            return dict(item)

    def consume(self, confirmation_id: str) -> dict | None:
        with self._lock:
            item = self._items.pop(confirmation_id, None)
        if not item or utc_now().isoformat() >= item["expires_at"]: return None
        return item

    def cancel(self, confirmation_id: str) -> bool:
        with self._lock: return self._items.pop(confirmation_id, None) is not None

    def clear(self) -> None:
        with self._lock: self._items.clear()


confirmation_store = ConfirmationStore()
