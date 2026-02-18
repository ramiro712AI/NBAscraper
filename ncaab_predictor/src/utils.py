"""
utils.py – Logging, caching, rate-limiting helpers.
"""

import logging
import time
import json
import os
import hashlib
from functools import wraps
from pathlib import Path

# ── Logging ─────────────────────────────────────────────────────────────────

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s – %(message)s"
DATE_FORMAT = "%H:%M:%S"

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


# ── Disk cache ───────────────────────────────────────────────────────────────

CACHE_DIR = Path(__file__).parent.parent / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600 * 6  # 6 hours


def _cache_key(key: str) -> Path:
    h = hashlib.md5(key.encode()).hexdigest()[:12]
    return CACHE_DIR / f"{h}.json"


def cache_get(key: str):
    path = _cache_key(key)
    if not path.exists():
        return None
    age = time.time() - path.stat().st_mtime
    if age > CACHE_TTL:
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def cache_set(key: str, data) -> None:
    path = _cache_key(key)
    try:
        with open(path, "w") as f:
            json.dump(data, f)
    except Exception:
        pass


# ── Rate limiter ─────────────────────────────────────────────────────────────

class RateLimiter:
    """Simple token-bucket rate limiter."""

    def __init__(self, calls_per_second: float = 1.0):
        self.min_interval = 1.0 / calls_per_second
        self._last_call = 0.0

    def wait(self):
        elapsed = time.time() - self._last_call
        sleep_for = self.min_interval - elapsed
        if sleep_for > 0:
            time.sleep(sleep_for)
        self._last_call = time.time()


DEFAULT_RATE_LIMITER = RateLimiter(calls_per_second=0.5)  # 1 req / 2 s


def rate_limited(limiter: RateLimiter = None):
    """Decorator: apply rate limiting before the function runs."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            rl = limiter or DEFAULT_RATE_LIMITER
            rl.wait()
            return fn(*args, **kwargs)
        return wrapper
    return decorator


# ── HTTP helpers ─────────────────────────────────────────────────────────────

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/json,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def safe_get(session, url: str, timeout: int = 15, retries: int = 3, **kwargs):
    """GET with retry / backoff; returns Response or None."""
    log = get_logger("utils.http")
    for attempt in range(1, retries + 1):
        try:
            resp = session.get(url, headers=DEFAULT_HEADERS, timeout=timeout, **kwargs)
            resp.raise_for_status()
            return resp
        except Exception as e:
            wait = 2 ** attempt
            log.warning(f"[attempt {attempt}/{retries}] {url} → {e}  (retry in {wait}s)")
            if attempt < retries:
                time.sleep(wait)
    return None
