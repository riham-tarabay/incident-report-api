"""Unit tests for the sliding-window rate limiter."""
from app.rate_limit import SlidingWindowRateLimiter


def test_allows_requests_under_the_limit():
    limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=60)
    assert limiter.allow("client-a")
    assert limiter.allow("client-a")
    assert limiter.allow("client-a")


def test_blocks_requests_over_the_limit():
    limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=60)
    for _ in range(3):
        assert limiter.allow("client-a")
    assert not limiter.allow("client-a")


def test_keys_are_isolated():
    limiter = SlidingWindowRateLimiter(max_requests=1, window_seconds=60)
    assert limiter.allow("client-a")
    assert limiter.allow("client-b")
    assert not limiter.allow("client-a")


def test_window_expires_old_hits():
    limiter = SlidingWindowRateLimiter(max_requests=1, window_seconds=0.01)
    assert limiter.allow("client-a")
    import time

    time.sleep(0.02)
    assert limiter.allow("client-a")
