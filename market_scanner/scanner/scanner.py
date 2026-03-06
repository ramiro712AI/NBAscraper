"""
Market Scanner.

Async batch scanner that scans a universe of symbols and returns
ranked signal opportunities.

Design:
- Processes symbols in batches (BATCH_SIZE) to avoid rate limits
- Maintains a priority queue sorted by score
- Returns results incrementally via a callback
- Supports separate crypto and stock scan modes
- Integrates SPY market regime filter
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

from market_scanner.config import (
    BATCH_SIZE,
    DEFAULT_CRYPTO_SYMBOLS,
    DEFAULT_STOCK_SYMBOLS,
    STRATEGY_PRESETS,
    STRATEGY_TIMEFRAMES,
)
from market_scanner.data import crypto_data, stock_data
from market_scanner.signals.signal_engine import generate_signals_all_strategies

logger = logging.getLogger(__name__)


# ============================================================
# CRYPTO SCANNER
# ============================================================

def scan_crypto_symbol(
    symbol: str,
    timeframe: str,
    strategies: Optional[List[str]] = None,
    regime: Optional[dict] = None,
) -> List[dict]:
    """Scan a single crypto symbol and return all valid signals."""
    try:
        df, exchange_id = crypto_data.fetch_ohlcv_multi_exchange(symbol, timeframe=timeframe)
        if df.empty:
            return []

        # Exchange availability
        exchanges = crypto_data.get_available_exchanges(symbol)

        signals = generate_signals_all_strategies(
            symbol=symbol,
            asset_type="crypto",
            df=df,
            timeframe=timeframe,
            strategies=strategies,
            regime=regime,
            exchange_list=exchanges,
        )
        return signals
    except Exception as exc:
        logger.warning("Crypto scan error for %s: %s", symbol, exc)
        return []


def scan_crypto_universe(
    symbols: Optional[List[str]] = None,
    timeframe: str = "1h",
    strategies: Optional[List[str]] = None,
    max_workers: int = 5,
    progress_callback: Optional[Callable] = None,
) -> List[dict]:
    """
    Scan the full crypto universe in batches.

    Returns ranked list of signals (sorted by score desc).
    """
    if symbols is None:
        symbols = DEFAULT_CRYPTO_SYMBOLS

    # Get market regime from SPY as baseline
    regime = stock_data.fetch_spy_regime(timeframe="1d")
    logger.info("Market regime: %s (SPY trend: %s)", regime.get("regime"), regime.get("trend"))

    all_signals = []
    total = len(symbols)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(scan_crypto_symbol, sym, timeframe, strategies, regime): sym
            for sym in symbols
        }

        completed = 0
        for future in as_completed(futures):
            sym = futures[future]
            try:
                signals = future.result()
                all_signals.extend(signals)
            except Exception as exc:
                logger.warning("Future error for %s: %s", sym, exc)
            finally:
                completed += 1
                if progress_callback:
                    progress_callback(completed, total, sym)

    # Sort by score descending
    all_signals.sort(key=lambda x: -x["score"])
    return all_signals


# ============================================================
# STOCK SCANNER
# ============================================================

def scan_stock_symbol(
    symbol: str,
    timeframe: str,
    strategies: Optional[List[str]] = None,
    regime: Optional[dict] = None,
    fetch_options: bool = True,
) -> List[dict]:
    """Scan a single stock symbol and return all valid signals."""
    try:
        df = stock_data.fetch_ohlcv(symbol, timeframe=timeframe)
        if df.empty:
            return []

        # Options context (expensive - fetch conditionally)
        options_ctx = None
        if fetch_options and timeframe in ("1d", "4h"):
            options_ctx = stock_data.fetch_options_context(symbol)

        # Stock metadata
        info = stock_data.fetch_stock_info(symbol)

        signals = generate_signals_all_strategies(
            symbol=symbol,
            asset_type="stock",
            df=df,
            timeframe=timeframe,
            strategies=strategies,
            regime=regime,
            options_context=options_ctx,
            stock_info=info,
        )

        # Attach suitability scores
        for sig in signals:
            sig["day_trading_score"]  = _day_trading_score(sig)
            sig["swing_score"]        = _swing_score(sig)
            sig["scalping_score"]     = _scalping_score(sig)

        return signals
    except Exception as exc:
        logger.warning("Stock scan error for %s: %s", symbol, exc)
        return []


def scan_stock_universe(
    symbols: Optional[List[str]] = None,
    timeframe: str = "1d",
    strategies: Optional[List[str]] = None,
    max_workers: int = 4,
    fetch_options: bool = True,
    progress_callback: Optional[Callable] = None,
) -> List[dict]:
    """
    Scan the full stock universe.

    Returns ranked signals sorted by score.
    """
    if symbols is None:
        symbols = DEFAULT_STOCK_SYMBOLS

    regime = stock_data.fetch_spy_regime(timeframe="1d")
    logger.info("Market regime: %s", regime.get("regime"))

    all_signals = []
    total = len(symbols)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                scan_stock_symbol, sym, timeframe, strategies, regime, fetch_options
            ): sym
            for sym in symbols
        }

        completed = 0
        for future in as_completed(futures):
            sym = futures[future]
            try:
                signals = future.result()
                all_signals.extend(signals)
            except Exception as exc:
                logger.warning("Future error for %s: %s", sym, exc)
            finally:
                completed += 1
                if progress_callback:
                    progress_callback(completed, total, sym)

    all_signals.sort(key=lambda x: -x["score"])
    return all_signals


# ============================================================
# COMBINED SCANNER
# ============================================================

def scan_all(
    crypto_symbols: Optional[List[str]] = None,
    stock_symbols: Optional[List[str]] = None,
    crypto_timeframe: str = "1h",
    stock_timeframe: str = "1d",
    progress_callback: Optional[Callable] = None,
) -> Dict[str, List[dict]]:
    """Run both crypto and stock scans and return combined results."""
    start = time.time()

    crypto_signals = scan_crypto_universe(
        symbols=crypto_symbols,
        timeframe=crypto_timeframe,
        progress_callback=progress_callback,
    )

    stock_signals = scan_stock_universe(
        symbols=stock_symbols,
        timeframe=stock_timeframe,
        progress_callback=progress_callback,
    )

    duration = time.time() - start
    logger.info(
        "Scan complete: %d crypto signals, %d stock signals in %.1fs",
        len(crypto_signals), len(stock_signals), duration
    )

    return {
        "crypto": crypto_signals,
        "stocks": stock_signals,
        "scan_time": duration,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================
# SUITABILITY SCORING HELPERS
# ============================================================

def _day_trading_score(signal: dict) -> float:
    """
    Score a signal 0-100 for day trading suitability.
    Favors: high volume, moderate ATR, momentum confirmation.
    """
    score = 0.0
    indicators = signal.get("indicators", {})
    vol     = indicators.get("volume")
    vol_ma  = indicators.get("volume_ma")
    rsi     = indicators.get("rsi")
    atr_pct = 0.0

    price = signal.get("price")
    atr   = indicators.get("atr")
    if price and atr and price > 0:
        atr_pct = (atr / price) * 100

    if vol and vol_ma and vol_ma > 0:
        ratio = vol / vol_ma
        score += min(30, ratio * 15)

    if rsi:
        if 40 <= rsi <= 70:
            score += 30

    if 0.3 <= atr_pct <= 3.0:
        score += 25

    # Base from signal score
    score += signal.get("score", 0) * 0.15

    return min(100, round(score, 1))


def _swing_score(signal: dict) -> float:
    """Score for swing trading suitability. Favors strong trend alignment."""
    indicators = signal.get("indicators", {})
    score = signal.get("score", 0) * 0.6  # Base from overall signal

    ema9  = indicators.get("ema_9")
    ema20 = indicators.get("ema_20")
    ema50 = indicators.get("ema_50")
    if ema9 and ema20 and ema50 and ema9 > ema20 > ema50:
        score += 25

    rsi = indicators.get("rsi")
    if rsi and 45 <= rsi <= 70:
        score += 15

    return min(100, round(score, 1))


def _scalping_score(signal: dict) -> float:
    """Score for scalping suitability. Favors tight spreads, high volume."""
    indicators = signal.get("indicators", {})
    score = 0.0
    vol     = indicators.get("volume")
    vol_ma  = indicators.get("volume_ma")
    price   = signal.get("price")
    atr     = indicators.get("atr")

    if vol and vol_ma and vol_ma > 0:
        score += min(40, (vol / vol_ma) * 20)

    atr_pct = (atr / price * 100) if atr and price and price > 0 else None
    if atr_pct and atr_pct < 1.0:
        score += 30
    elif atr_pct and atr_pct < 2.0:
        score += 15

    score += signal.get("score", 0) * 0.3
    return min(100, round(score, 1))
