import time
from typing import Any, Optional

class SimpleCache:
    def __init__(self, ttl: int = 600):
        self.ttl = ttl
        self.store: dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        value = self.store.get(key)
        if not value:
            return None
        data, expires = value
        if time.time() > expires:
            self.store.pop(key, None)
            return None
        return data

    def set(self, key: str, value: Any):
        self.store[key] = (value, time.time() + self.ttl)
