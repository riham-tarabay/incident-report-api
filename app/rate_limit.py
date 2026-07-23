"""Small in-memory sliding-window rate limiter, keyed by client IP.

Intentionally dependency-free. For multi-instance deployments you would back
this with Redis; the interface would stay the same.
"""
import os
import time
from collections import defaultdict, deque
from typing import Deque, Dict


class SlidingWindowRateLimiter:
    def __init__(self, max_requests: int, window_seconds: float) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        """Record a hit for `key`; return False when the window is saturated."""
        now = time.monotonic()
        window_start = now - self.window_seconds
        hits = self._hits[key]
        while hits and hits[0] < window_start:
            hits.popleft()
        if len(hits) >= self.max_requests:
            return False
        hits.append(now)
        return True


def limiter_from_env() -> SlidingWindowRateLimiter:
    max_requests = int(os.environ.get("RATE_LIMIT_MAX", "120"))
    window_seconds = float(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "60"))
    return SlidingWindowRateLimiter(max_requests, window_seconds)
