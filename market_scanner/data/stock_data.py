"""
Stock data ingestion layer.

Uses yfinance for:
- OHLCV data (intraday + daily)
- Options chains (calls/puts, IV, Greeks, OI)
- Basic fundamental info (sector, market cap)

Market regime data: SPY used as the index proxy.
"""

import logging
from typing import Dict, List, Optional, Tuple

import pandas as pd
import yfinance as yf

from market_scanner.config import DEFAULT_STOCK_SYMBOLS, SPY_SYMBOL
from market_scanner.data.cache import ohlcv_cache

logger = logging.getLogger(__name__)

# yfinance interval map to our timeframe keys
_YF_INTERVAL_MAP: Dict[str, str] = {
    "1m":  "1m",
    "3m":  "2m",   # yfinance has 2m not 3m
    "5m":  "5m",
    "15m": "15m",
    "30m": "30m",
    "1h":  "1h",
    "4h":  "1h",   # yfinance has no 4h; we resample
    "1d":  "1d",
    "1w":  "1wk",
}

# Max lookback days per yfinance interval (API limit)
_YF_MAX_DAYS: Dict[str, int] = {
    "1m":  7,
    "2m":  60,
    "5m":  60,
    "15m": 60,
    "30m": 60,
    "1h":  730,
    "1d":  3650,
    "1wk": 3650,
}


def _resample_to_4h(df: pd.DataFrame) -> pd.DataFrame:
    """Resample 1h OHLCV into 4h bars."""
    df_4h = df.resample("4h").agg({
        "open":   "first",
        "high":   "max",
        "low":    "min",
        "close":  "last",
        "volume": "sum",
    }).dropna()
    return df_4h


def fetch_ohlcv(
    symbol: str,
    timeframe: str = "1d",
    limit: int = 300,
) -> pd.DataFrame:
    """
    Fetch OHLCV data for a stock symbol via yfinance.

    Returns DataFrame with columns [open, high, low, close, volume]
    indexed by datetime (UTC).
    """
    cached = ohlcv_cache.get(symbol, timeframe, "yfinance")
    if cached is not None:
        return cached

    yf_interval = _YF_INTERVAL_MAP.get(timeframe, "1d")
    need_resample_4h = (timeframe == "4h")
    fetch_interval = "1h" if need_resample_4h else yf_interval

    max_days = _YF_MAX_DAYS.get(fetch_interval, 365)
    period_days = min(max_days, max(limit * 2, 30))  # rough estimate

    try:
        ticker = yf.Ticker(symbol)

        if fetch_interval in ("1d", "1wk"):
            period = f"{period_days}d"
            df = ticker.history(period=period, interval=fetch_interval)
        else:
            period = f"{min(period_days, max_days)}d"
            df = ticker.history(period=period, interval=fetch_interval)

        if df.empty:
            return pd.DataFrame()

        df.columns = [c.lower() for c in df.columns]
        df = df[["open", "high", "low", "close", "volume"]].copy()
        df = df.astype(float)

        # Ensure UTC timezone
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC")
        else:
            df.index = df.index.tz_convert("UTC")

        if need_resample_4h:
            df = _resample_to_4h(df)

        # Trim to requested limit
        df = df.tail(limit)

        ohlcv_cache.set(symbol, timeframe, "yfinance", df)
        return df

    except Exception as exc:
        logger.warning("yfinance error for %s %s: %s", symbol, timeframe, exc)
        return pd.DataFrame()


# ============================================================
# OPTIONS DATA
# ============================================================

def fetch_options_context(symbol: str) -> Dict:
    """
    Fetch options chain context for a stock symbol.

    Returns a dict with:
    - nearest_expiry: str
    - call_volume: int
    - put_volume: int
    - call_put_ratio: float
    - avg_call_iv: float (as decimal, e.g. 0.35 = 35%)
    - avg_put_iv: float
    - iv_rank_approx: float  (approximated from 52w range if available)
    - notable_strikes: list of dicts
    - options_bias: "calls" | "puts" | "neutral" | "unavailable"
    - iv_warning: bool  (True if IV is very high = expensive premiums)
    """
    result = {
        "nearest_expiry":  None,
        "call_volume":     0,
        "put_volume":      0,
        "call_put_ratio":  None,
        "avg_call_iv":     None,
        "avg_put_iv":      None,
        "iv_rank_approx":  None,
        "notable_strikes": [],
        "options_bias":    "unavailable",
        "iv_warning":      False,
    }
    try:
        ticker = yf.Ticker(symbol)
        expirations = ticker.options
        if not expirations:
            return result

        # Use nearest expiration (1-2 weeks out ideally)
        nearest = expirations[0]
        result["nearest_expiry"] = nearest

        chain = ticker.option_chain(nearest)
        calls = chain.calls
        puts = chain.puts

        if calls.empty or puts.empty:
            return result

        call_vol = int(calls["volume"].fillna(0).sum())
        put_vol = int(puts["volume"].fillna(0).sum())
        result["call_volume"] = call_vol
        result["put_volume"] = put_vol

        if put_vol > 0:
            result["call_put_ratio"] = round(call_vol / put_vol, 2)

        # Implied volatility (yfinance gives it as decimal)
        avg_call_iv = calls["impliedVolatility"].dropna().mean()
        avg_put_iv = puts["impliedVolatility"].dropna().mean()
        result["avg_call_iv"] = round(float(avg_call_iv), 4) if pd.notna(avg_call_iv) else None
        result["avg_put_iv"] = round(float(avg_put_iv), 4) if pd.notna(avg_put_iv) else None

        # IV warning: if avg IV > 80% it's expensive
        avg_iv = (avg_call_iv + avg_put_iv) / 2 if pd.notna(avg_call_iv) and pd.notna(avg_put_iv) else None
        if avg_iv and avg_iv > 0.80:
            result["iv_warning"] = True

        # Notable strikes (ATM ± 2 strikes)
        try:
            current_price = ticker.fast_info.get("lastPrice") or ticker.info.get("regularMarketPrice", 0)
            if current_price:
                calls_sorted = calls.iloc[(calls["strike"] - current_price).abs().argsort()[:5]]
                for _, row in calls_sorted.iterrows():
                    result["notable_strikes"].append({
                        "strike": row["strike"],
                        "type": "call",
                        "iv": row.get("impliedVolatility"),
                        "oi": row.get("openInterest"),
                        "volume": row.get("volume"),
                        "delta": row.get("delta"),
                    })
        except Exception:
            pass

        # Determine options bias
        cpr = result["call_put_ratio"]
        if cpr is not None:
            if cpr > 1.3:
                result["options_bias"] = "calls"
            elif cpr < 0.7:
                result["options_bias"] = "puts"
            else:
                result["options_bias"] = "neutral"

    except Exception as exc:
        logger.warning("Options fetch error for %s: %s", symbol, exc)

    return result


# ============================================================
# STOCK INFO
# ============================================================

_info_cache: Dict[str, Dict] = {}


def fetch_stock_info(symbol: str) -> Dict:
    """Fetch sector, industry, market cap, and other metadata."""
    if symbol in _info_cache:
        return _info_cache[symbol]

    result = {
        "sector": "Unknown",
        "industry": "Unknown",
        "market_cap": None,
        "country": "US",
        "beta": None,
        "avg_volume": None,
    }
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info or {}
        result["sector"] = info.get("sector", "Unknown")
        result["industry"] = info.get("industry", "Unknown")
        result["market_cap"] = info.get("marketCap")
        result["country"] = info.get("country", "US")
        result["beta"] = info.get("beta")
        result["avg_volume"] = info.get("averageVolume")
        _info_cache[symbol] = result
    except Exception as exc:
        logger.warning("Stock info error for %s: %s", symbol, exc)

    return result


# ============================================================
# MARKET REGIME (SPY)
# ============================================================

def fetch_spy_regime(timeframe: str = "1d") -> Dict:
    """
    Analyse SPY to determine the current market regime.

    Returns:
    - regime: "bullish" | "bearish" | "neutral"
    - ema20: float
    - ema50: float
    - spy_price: float
    - above_ema20: bool
    - above_ema50: bool
    - trend: "up" | "down" | "sideways"
    """
    try:
        df = fetch_ohlcv(SPY_SYMBOL, timeframe=timeframe, limit=100)
        if df.empty or len(df) < 55:
            return {"regime": "neutral", "trend": "sideways"}

        close = df["close"]
        ema20 = close.ewm(span=20, adjust=False).mean().iloc[-1]
        ema50 = close.ewm(span=50, adjust=False).mean().iloc[-1]
        price = close.iloc[-1]

        above_ema20 = price > ema20
        above_ema50 = price > ema50
        ema_aligned = ema20 > ema50

        if above_ema20 and above_ema50 and ema_aligned:
            regime = "bullish"
            trend = "up"
        elif not above_ema20 and not above_ema50 and not ema_aligned:
            regime = "bearish"
            trend = "down"
        else:
            regime = "neutral"
            trend = "sideways"

        return {
            "regime": regime,
            "trend": trend,
            "spy_price": round(price, 2),
            "ema20": round(ema20, 2),
            "ema50": round(ema50, 2),
            "above_ema20": above_ema20,
            "above_ema50": above_ema50,
            "ema_aligned_bullish": ema_aligned,
        }
    except Exception as exc:
        logger.warning("SPY regime error: %s", exc)
        return {"regime": "neutral", "trend": "sideways"}
