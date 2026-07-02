from typing import Any, Protocol


class CacheBackend(Protocol):
    async def get(self, key: str) -> Any | None: ...
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None: ...


class NullCache:
    """Redis-ready no-op cache used until a shared cache is configured."""
    async def get(self, key: str) -> None: del key; return None
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None: del key, value, ttl


cache: CacheBackend = NullCache()
