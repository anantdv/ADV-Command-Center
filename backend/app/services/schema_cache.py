from __future__ import annotations

from dataclasses import dataclass
from time import time
from typing import Any


@dataclass
class CacheEntry:
    value: Any
    expires_at: float


class SchemaCache:
    """Small TTL cache for ERP metadata.

    Invalidation hooks for migrate/custom-field/property-setter events should be
    wired to the Frappe companion app in the next server-side phase.
    """

    def __init__(self, ttl_seconds: int = 900) -> None:
        self.ttl_seconds = ttl_seconds
        self._items: dict[str, CacheEntry] = {}

    def get(self, key: str) -> Any | None:
        item = self._items.get(key)
        if not item:
            return None
        if item.expires_at <= time():
            self._items.pop(key, None)
            return None
        return item.value

    def set(self, key: str, value: Any) -> None:
        self._items[key] = CacheEntry(value=value, expires_at=time() + self.ttl_seconds)

    def invalidate(self, key: str | None = None) -> None:
        if key:
            self._items.pop(key, None)
        else:
            self._items.clear()


schema_cache = SchemaCache()

