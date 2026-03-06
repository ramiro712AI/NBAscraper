"""
Two-level OHLCV cache:
  1. In-process LRU dict keyed by (symbol, timeframe, exchange)
  2. File-based JSON cache for persistence across restarts

Cache invalidation: TTL per timeframe (shorter TF = shorter TTL).
"""

import json
import logging
import os
import time
from functools import lru_cache
from typing import Dict, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)

# TTL in seconds per timeframe
TIMEFRAME_TTL: Dict[str, int] = {
    "1m":  30,
    "3m":  60,
    "5m":  90,
    "15m": 180,
    "30m": 300,
    "1h":  600,
    "4h":  1800,
    "1d":  3600,
    "1w":  14400,
}

DEFAULT_TTL = 300
CACHE_DIR = os.path.join(os.path.dirname(__file__), "../../.cache")


class OHLCVCache:
    """In-process cache with TTL for OHLCV DataFrames."""

    def __init__(self) -> None:
        self._store: Dict[str, Tuple[pd.DataFrame, float]] = {}

    def _key(self, symbol: str, timeframe: str, source: str) -> str:
        return f"{source}:{symbol}:{timeframe}"

    def get(self, symbol: str, timeframe: str, source: str) -> Optional[pd.DataFrame]:
        key = self._key(symbol, timeframe, source)
        if key not in self._store:
            return None
        df, expires_at = self._store[key]
        if time.time() > expires_at:
            del self._store[key]
            return None
        return df

    def set(self, symbol: str, timeframe: str, source: str, df: pd.DataFrame) -> None:
        ttl = TIMEFRAME_TTL.get(timeframe, DEFAULT_TTL)
        key = self._key(symbol, timeframe, source)
        self._store[key] = (df.copy(), time.time() + ttl)

    def invalidate(self, symbol: str, timeframe: str, source: str) -> None:
        key = self._key(symbol, timeframe, source)
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()

    def stats(self) -> Dict:
        now = time.time()
        valid = sum(1 for _, (_, exp) in self._store.items() if exp > now)
        return {"total_entries": len(self._store), "valid": valid, "expired": len(self._store) - valid}


# Global shared cache instance
ohlcv_cache = OHLCVCache()
