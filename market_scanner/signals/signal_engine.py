"""
Signal Engine.

Orchestrates: data -> indicators -> scoring -> signal output.

For each (symbol, timeframe, strategy):
1. Fetch OHLCV from data layer
2. Compute indicators via indicator engine
3. Extract latest snapshot
4. Score each rule via scoring engine
5. Build full signal result dict

This is the primary interface for the scanner.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from market_scanner.config import STRATEGY_PRESETS, StrategyPreset
from market_scanner.indicators.engine import compute_indicators, get_latest_values
from market_scanner.signals.scoring import (
    classify_score,
    classify_signal_type,
    compute_score,
    compute_trade_levels,
)

logger = logging.getLogger(__name__)


def _determine_direction(snap: dict, rule_results: Dict[str, float]) -> str:
    """
    Infer long/short direction from leading rules and indicator context.

    For strategies that use oversold/mean-reversion rules (no explicit bull/bear
    trend rules in their rule_results), fall back to indicator context:
    - Oversold RSI or Stochastic → buy (expect bounce)
    - Overbought RSI or Stochastic → sell (expect reversal)
    - Otherwise use EMA alignment
    """
    bull_rules = [
        "ema_alignment_bullish", "price_above_vwap", "rsi_bullish_range",
        "rsi_momentum", "macd_bullish", "macd_histogram_rising",
        "weekly_trend_bullish", "price_breaks_resistance",
    ]
    bear_rules = [
        "ema_alignment_bearish",
    ]
    bull_score = sum(rule_results.get(r, 0) for r in bull_rules)
    bear_score = sum(rule_results.get(r, 0) for r in bear_rules)

    # Check if any directional rules were actually evaluated
    has_directional_rules = any(r in rule_results for r in bull_rules + bear_rules)

    if not has_directional_rules:
        # Fallback: use oversold/overbought indicators for direction
        rsi = snap.get("rsi")
        stoch_k = snap.get("stoch_k")

        oversold_score = 0
        overbought_score = 0

        if rsi is not None:
            if rsi < 35:
                oversold_score += 2
            elif rsi < 45:
                oversold_score += 1
            elif rsi > 65:
                overbought_score += 2
            elif rsi > 55:
                overbought_score += 1

        if stoch_k is not None:
            if stoch_k < 25:
                oversold_score += 1
            elif stoch_k > 75:
                overbought_score += 1

        # mean_reversion: buy oversold, sell overbought
        if oversold_score > overbought_score:
            return "buy"
        elif overbought_score > oversold_score:
            return "sell"

    # EMA alignment tiebreaker
    ema9  = snap.get("ema_9")
    ema20 = snap.get("ema_20")
    ema50 = snap.get("ema_50")
    if ema9 and ema20 and ema50:
        if ema9 > ema20 > ema50:
            bull_score += 1
        elif ema9 < ema20 < ema50:
            bear_score += 1

    return "buy" if bull_score >= bear_score else "sell"


def generate_signal(
    symbol: str,
    asset_type: str,           # "crypto" | "stock"
    df,                        # pd.DataFrame with OHLCV
    strategy_name: str,
    timeframe: str,
    regime: Optional[dict] = None,
    exchange_list: Optional[List[str]] = None,
    options_context: Optional[dict] = None,
    stock_info: Optional[dict] = None,
) -> Optional[dict]:
    """
    Generate a full signal dict for one symbol/timeframe/strategy.

    Returns None if insufficient data or score below minimum.
    """
    if df is None or df.empty or len(df) < 30:
        logger.debug("Insufficient data for %s %s", symbol, timeframe)
        return None

    preset: StrategyPreset = STRATEGY_PRESETS.get(strategy_name)
    if preset is None:
        logger.warning("Unknown strategy: %s", strategy_name)
        return None

    # --- Compute indicators ---
    df_ind = compute_indicators(df)
    snap   = get_latest_values(df_ind)

    if not snap:
        return None

    # --- Score ---
    score, rule_results = compute_score(snap, preset.rules, regime=regime)

    if score < preset.min_score:
        return None  # Below threshold - not a signal

    # --- Build signal ---
    price     = snap.get("close")
    atr       = snap.get("atr")
    direction = _determine_direction(snap, rule_results)
    levels    = compute_trade_levels(price, atr, direction)
    label     = classify_score(score)
    sig_type  = classify_signal_type(score, direction)

    # Contributing reasons (sorted by contribution)
    reasons = {
        k: v for k, v in sorted(rule_results.items(), key=lambda x: -x[1])
        if v > 0.3
    }

    # Options bias from context
    options_bias = None
    iv_rank = None
    iv_warning = False
    if options_context:
        options_bias = options_context.get("options_bias")
        iv_rank      = options_context.get("iv_rank_approx")
        iv_warning   = options_context.get("iv_warning", False)
        # Align options bias with direction
        if direction == "buy" and options_bias == "puts":
            options_bias = "neutral"  # Conflict - tone it down
        if direction == "sell" and options_bias == "calls":
            options_bias = "neutral"

    signal = {
        "symbol":         symbol,
        "asset_type":     asset_type,
        "timeframe":      timeframe,
        "strategy":       strategy_name,
        "strategy_label": preset.name,
        "signal_type":    sig_type,
        "direction":      direction,
        "score":          score,
        "score_label":    label,
        "price":          round(price, 6) if price else None,
        "entry_zone":     levels["entry_zone"],
        "stop_loss":      levels["stop_loss"],
        "take_profit_1":  levels["take_profit_1"],
        "take_profit_2":  levels["take_profit_2"],
        "risk_reward":    levels["risk_reward_1"],
        "atr_value":      round(atr, 6) if atr else None,
        "reasons":        json.dumps(reasons),
        "reasons_dict":   reasons,
        # Crypto fields
        "exchange_list":  ",".join(exchange_list) if exchange_list else "",
        "exchange_display": exchange_list or [],
        # Stock fields
        "options_bias":   options_bias,
        "iv_rank":        iv_rank,
        "iv_warning":     iv_warning,
        "sector":         (stock_info or {}).get("sector"),
        # Indicator snapshot (for UI display)
        "indicators": {
            "rsi":         snap.get("rsi"),
            "macd":        snap.get("macd"),
            "macd_signal": snap.get("macd_signal"),
            "adx":         snap.get("adx"),
            "ema_9":       snap.get("ema_9"),
            "ema_20":      snap.get("ema_20"),
            "ema_50":      snap.get("ema_50"),
            "ema_200":     snap.get("ema_200"),
            "vwap":        snap.get("vwap"),
            "bb_upper":    snap.get("bb_upper"),
            "bb_lower":    snap.get("bb_lower"),
            "volume_ma":   snap.get("volume_ma"),
            "volume":      snap.get("volume"),
            "atr":         atr,
            "squeeze":     snap.get("squeeze"),
            "supertrend_dir": snap.get("supertrend_dir"),
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    # Volume condition label
    vol   = snap.get("volume")
    vol_ma = snap.get("volume_ma")
    if vol and vol_ma and vol_ma > 0:
        ratio = vol / vol_ma
        if ratio >= 2.0:
            signal["volume_condition"] = "very_high"
        elif ratio >= 1.5:
            signal["volume_condition"] = "high"
        elif ratio >= 1.0:
            signal["volume_condition"] = "normal"
        else:
            signal["volume_condition"] = "low"
    else:
        signal["volume_condition"] = "unknown"

    # Volatility condition based on ATR relative to price
    if atr and price and price > 0:
        atr_pct = atr / price * 100
        if atr_pct >= 5:
            signal["volatility_condition"] = "extreme"
        elif atr_pct >= 2:
            signal["volatility_condition"] = "high"
        elif atr_pct >= 0.5:
            signal["volatility_condition"] = "moderate"
        else:
            signal["volatility_condition"] = "low"
    else:
        signal["volatility_condition"] = "unknown"

    # Market trend from EMA alignment
    e9  = snap.get("ema_9")
    e20 = snap.get("ema_20")
    e50 = snap.get("ema_50")
    if e9 and e20 and e50:
        if e9 > e20 > e50:
            signal["trend"] = "uptrend"
        elif e9 < e20 < e50:
            signal["trend"] = "downtrend"
        else:
            signal["trend"] = "mixed"
    else:
        signal["trend"] = "unknown"

    return signal


def generate_signals_all_strategies(
    symbol: str,
    asset_type: str,
    df,
    timeframe: str,
    strategies: Optional[List[str]] = None,
    regime: Optional[dict] = None,
    exchange_list: Optional[List[str]] = None,
    options_context: Optional[dict] = None,
    stock_info: Optional[dict] = None,
) -> List[dict]:
    """
    Run all (or selected) strategies for one symbol and return valid signals.
    Returns list sorted by score descending.
    """
    if strategies is None:
        strategies = list(STRATEGY_PRESETS.keys())

    results = []
    for strategy_name in strategies:
        preset = STRATEGY_PRESETS.get(strategy_name)
        if preset is None:
            continue
        # Skip if timeframe not appropriate for this strategy
        if timeframe not in preset.timeframes:
            continue

        signal = generate_signal(
            symbol=symbol,
            asset_type=asset_type,
            df=df,
            strategy_name=strategy_name,
            timeframe=timeframe,
            regime=regime,
            exchange_list=exchange_list,
            options_context=options_context,
            stock_info=stock_info,
        )
        if signal:
            results.append(signal)

    return sorted(results, key=lambda x: -x["score"])
