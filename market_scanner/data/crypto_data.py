"""
Crypto data ingestion layer.

Uses CCXT for public market data (OHLCV, tickers, order books) from multiple exchanges.
Uses the authenticated Crypto.com Exchange client for private data.

Exchange priority: Crypto.com -> Binance -> Bybit -> OKX -> Kraken -> Coinbase
"""

import hashlib
import hmac
import json
import logging
import time
from typing import Dict, List, Optional, Tuple

import ccxt
import pandas as pd
import requests

from market_scanner.config import (
    CRYPTO_API_KEY,
    CRYPTO_COM_EXCHANGE_URL,
    CRYPTO_SECRET_KEY,
    DEFAULT_CRYPTO_SYMBOLS,
    EXCHANGE_DISPLAY,
    EXCHANGE_PRIORITY,
)
from market_scanner.data.cache import ohlcv_cache

logger = logging.getLogger(__name__)

# ============================================================
# EXCHANGE INITIALISATION
# ============================================================

_EXCHANGE_INSTANCES: Dict[str, ccxt.Exchange] = {}


def _get_exchange(exchange_id: str) -> Optional[ccxt.Exchange]:
    """Lazily initialise and cache a CCXT exchange instance."""
    if exchange_id in _EXCHANGE_INSTANCES:
        return _EXCHANGE_INSTANCES[exchange_id]

    # Map config ids to CCXT ids
    ccxt_id_map = {
        "crypto_com": "cryptocom",
        "coinbase":   "coinbase",
        "binance":    "binance",
        "bybit":      "bybit",
        "okx":        "okx",
        "kraken":     "kraken",
        "kucoin":     "kucoin",
        "gateio":     "gateio",
    }
    ccxt_id = ccxt_id_map.get(exchange_id, exchange_id)

    try:
        exchange_class = getattr(ccxt, ccxt_id)
        ex = exchange_class({"enableRateLimit": True, "timeout": 15000})
        _EXCHANGE_INSTANCES[exchange_id] = ex
        return ex
    except AttributeError:
        logger.warning("CCXT exchange not found: %s", exchange_id)
        return None


def _primary_exchange() -> ccxt.Exchange:
    """Return the primary data exchange (Binance for broadest public OHLCV)."""
    return _get_exchange("binance")


# ============================================================
# OHLCV FETCHING
# ============================================================

def fetch_ohlcv(
    symbol: str,
    timeframe: str = "1h",
    limit: int = 300,
    exchange_id: str = "binance",
) -> pd.DataFrame:
    """
    Fetch OHLCV candles for a symbol from the given exchange.

    Returns DataFrame with columns: [open, high, low, close, volume]
    indexed by datetime (UTC).
    """
    cached = ohlcv_cache.get(symbol, timeframe, exchange_id)
    if cached is not None:
        return cached

    exchange = _get_exchange(exchange_id)
    if exchange is None:
        return pd.DataFrame()

    try:
        raw = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        if not raw:
            return pd.DataFrame()

        df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        df.set_index("timestamp", inplace=True)
        df = df.astype(float)

        ohlcv_cache.set(symbol, timeframe, exchange_id, df)
        return df

    except ccxt.BaseError as exc:
        logger.warning("CCXT error fetching %s %s on %s: %s", symbol, timeframe, exchange_id, exc)
        return pd.DataFrame()
    except Exception as exc:
        logger.error("Unexpected error fetching %s %s on %s: %s", symbol, timeframe, exchange_id, exc)
        return pd.DataFrame()


def fetch_ohlcv_multi_exchange(
    symbol: str,
    timeframe: str = "1h",
    limit: int = 300,
) -> Tuple[pd.DataFrame, str]:
    """
    Try exchanges in priority order until we get OHLCV data.
    Returns (DataFrame, exchange_id_that_worked).
    """
    for ex_id in EXCHANGE_PRIORITY:
        df = fetch_ohlcv(symbol, timeframe=timeframe, limit=limit, exchange_id=ex_id)
        if not df.empty:
            return df, ex_id
    return pd.DataFrame(), ""


# ============================================================
# TICKER / CURRENT PRICE
# ============================================================

def fetch_ticker(symbol: str, exchange_id: str = "binance") -> Optional[Dict]:
    """Fetch current ticker (price, volume, change) for a symbol."""
    exchange = _get_exchange(exchange_id)
    if exchange is None:
        return None
    try:
        ticker = exchange.fetch_ticker(symbol)
        return {
            "symbol": symbol,
            "price": ticker.get("last") or ticker.get("close"),
            "bid": ticker.get("bid"),
            "ask": ticker.get("ask"),
            "volume_24h": ticker.get("quoteVolume") or ticker.get("baseVolume"),
            "change_pct_24h": ticker.get("percentage"),
            "high_24h": ticker.get("high"),
            "low_24h": ticker.get("low"),
            "exchange": exchange_id,
        }
    except Exception as exc:
        logger.warning("Ticker fetch error %s on %s: %s", symbol, exchange_id, exc)
        return None


def fetch_tickers_batch(
    symbols: List[str],
    exchange_id: str = "binance",
) -> Dict[str, Dict]:
    """Fetch multiple tickers at once (much faster than individual calls)."""
    exchange = _get_exchange(exchange_id)
    if exchange is None:
        return {}
    try:
        # Some exchanges support fetch_tickers with filter
        tickers = exchange.fetch_tickers(symbols)
        result = {}
        for sym, t in tickers.items():
            result[sym] = {
                "symbol": sym,
                "price": t.get("last") or t.get("close"),
                "volume_24h": t.get("quoteVolume") or t.get("baseVolume"),
                "change_pct_24h": t.get("percentage"),
                "high_24h": t.get("high"),
                "low_24h": t.get("low"),
                "exchange": exchange_id,
            }
        return result
    except Exception as exc:
        logger.warning("Batch ticker error on %s: %s", exchange_id, exc)
        return {}


# ============================================================
# EXCHANGE AVAILABILITY CHECK
# ============================================================

_symbol_exchange_cache: Dict[str, List[str]] = {}


def get_available_exchanges(symbol: str) -> List[str]:
    """
    Return list of exchange ids where this symbol is listed.
    Uses a lazy per-symbol cache since markets don't change often.
    """
    if symbol in _symbol_exchange_cache:
        return _symbol_exchange_cache[symbol]

    available = []
    for ex_id in EXCHANGE_PRIORITY:
        exchange = _get_exchange(ex_id)
        if exchange is None:
            continue
        try:
            if not exchange.markets:
                exchange.load_markets()
            if symbol in exchange.markets:
                available.append(ex_id)
        except Exception:
            continue

    _symbol_exchange_cache[symbol] = available
    return available


def get_exchange_display_names(exchange_ids: List[str]) -> List[str]:
    return [EXCHANGE_DISPLAY.get(eid, eid) for eid in exchange_ids]


# ============================================================
# CRYPTO.COM PRIVATE API (authenticated)
# ============================================================

def _build_params_string(params: dict) -> str:
    if not params:
        return ""
    return "".join(f"{k}{params[k]}" for k in sorted(params.keys()))


def _sign_request(method: str, request_id: int, params: dict, nonce: int) -> str:
    params_string = _build_params_string(params)
    sig_payload = f"{method}{request_id}{CRYPTO_API_KEY}{params_string}{nonce}"
    return hmac.new(
        CRYPTO_SECRET_KEY.encode("utf-8"),
        sig_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def call_private_api(method: str, params: dict = None) -> Optional[Dict]:
    """Call an authenticated Crypto.com Exchange API endpoint."""
    if not CRYPTO_API_KEY or not CRYPTO_SECRET_KEY:
        return None
    if params is None:
        params = {}

    nonce = int(time.time() * 1000)
    request_id = 1
    sig = _sign_request(method, request_id, params, nonce)

    body = {
        "id": request_id,
        "method": method,
        "api_key": CRYPTO_API_KEY,
        "params": params,
        "nonce": nonce,
        "sig": sig,
    }
    try:
        response = requests.post(
            CRYPTO_COM_EXCHANGE_URL,
            json=body,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        data = response.json()
        if data.get("code") == 0:
            return data.get("result")
        else:
            logger.warning("Crypto.com API error %s: %s", data.get("code"), data.get("message"))
            return None
    except Exception as exc:
        logger.error("Crypto.com private API error: %s", exc)
        return None


def get_account_summary() -> Optional[Dict]:
    """Fetch account balance from Crypto.com (requires credentials)."""
    return call_private_api("private/get-account-summary")


# ============================================================
# UNIVERSE MANAGEMENT
# ============================================================

def get_top_symbols_by_volume(
    exchange_id: str = "binance",
    quote: str = "USDT",
    limit: int = 50,
) -> List[str]:
    """
    Fetch the top N symbols by 24h volume from an exchange.
    Falls back to DEFAULT_CRYPTO_SYMBOLS on error.
    """
    exchange = _get_exchange(exchange_id)
    if exchange is None:
        return DEFAULT_CRYPTO_SYMBOLS

    try:
        if not exchange.markets:
            exchange.load_markets()
        tickers = exchange.fetch_tickers()

        usdt_pairs = {
            sym: t for sym, t in tickers.items()
            if sym.endswith(f"/{quote}") and t.get("quoteVolume")
        }
        sorted_pairs = sorted(
            usdt_pairs.items(),
            key=lambda x: x[1]["quoteVolume"] or 0,
            reverse=True,
        )
        return [sym for sym, _ in sorted_pairs[:limit]]

    except Exception as exc:
        logger.warning("Could not fetch top symbols: %s", exc)
        return DEFAULT_CRYPTO_SYMBOLS
