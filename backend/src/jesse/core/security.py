from __future__ import annotations

import time
from dataclasses import dataclass
from flask import request
from .errors import JesseError


@dataclass
class SimpleRateLimiter:
    """
    Rate limiter sederhana in-memory (cukup untuk dev/single process).
    Untuk production multi-instance, pakai Redis (nanti).
    """
    limit_per_minute: int
    _bucket: dict[str, list[float]]

    def __init__(self, limit_per_minute: int) -> None:
        self.limit_per_minute = limit_per_minute
        self._bucket = {}

    def check(self, key: str) -> None:
        now = time.time()
        window_start = now - 60
        arr = self._bucket.get(key, [])
        arr = [t for t in arr if t >= window_start]
        if len(arr) >= self.limit_per_minute:
            raise JesseError("Rate limit exceeded. Please try again.", 429)
        arr.append(now)
        self._bucket[key] = arr


def require_api_key(global_api_key: str | None) -> None:
    """
    Auth opsional.
    - Kalau GLOBAL_API_KEY tidak di-set: publik, lewati.
    - Kalau di-set: client wajib kirim header X-API-Key.
    """
    if not global_api_key:
        return
    incoming = request.headers.get("X-API-Key", "")
    if incoming != global_api_key:
        raise JesseError("Unauthorized", 401)
