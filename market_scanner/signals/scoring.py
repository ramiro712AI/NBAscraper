"""
Signal Scoring Engine.

Evaluates individual signal rules and returns a weighted confluence score (0-100).

Each rule returns a float 0.0-1.0 (confidence).
The score = sum(weight_i * confidence_i) / sum(weight_i) * 100.

Score classification:
  0-49    → weak
  50-64   → moderate
  65-79   → strong
  80-100  → very_strong
"""

from typing import Dict, Optional, Tuple

from market_scanner.config import SCORE_LABELS


def classify_score(score: float) -> str:
    for label, (lo, hi) in SCORE_LABELS.items():
        if lo <= score <= hi:
            return label
    return "weak"


def classify_signal_type(score: float, direction: str) -> str:
    """Map score + direction to a signal label."""
    label = classify_score(score)
    if direction == "buy":
        if label in ("very_strong", "strong"):
            return "strong_buy"
        return "buy"
    elif direction == "sell":
        if label in ("very_strong", "strong"):
            return "strong_sell"
        return "sell"
    return "neutral"


# ============================================================
# INDIVIDUAL RULE EVALUATORS
# ============================================================

def rule_ema_alignment_bullish(snap: dict) -> float:
    """EMA9 > EMA20 > EMA50 (optionally > EMA200). Full alignment = 1.0."""
    ema9   = snap.get("ema_9")
    ema20  = snap.get("ema_20")
    ema50  = snap.get("ema_50")
    ema200 = snap.get("ema_200")

    if ema9 is None or ema20 is None or ema50 is None:
        return 0.0

    score = 0.0
    if ema9 > ema20:   score += 0.4
    if ema20 > ema50:  score += 0.4
    if ema200 and ema50 > ema200: score += 0.2

    return score


def rule_ema_alignment_bearish(snap: dict) -> float:
    """EMA9 < EMA20 < EMA50 (optionally < EMA200)."""
    ema9   = snap.get("ema_9")
    ema20  = snap.get("ema_20")
    ema50  = snap.get("ema_50")
    ema200 = snap.get("ema_200")

    if ema9 is None or ema20 is None or ema50 is None:
        return 0.0

    score = 0.0
    if ema9 < ema20:   score += 0.4
    if ema20 < ema50:  score += 0.4
    if ema200 and ema50 < ema200: score += 0.2

    return score


def rule_ema9_above_ema20(snap: dict) -> float:
    ema9 = snap.get("ema_9")
    ema20 = snap.get("ema_20")
    if ema9 is None or ema20 is None:
        return 0.0
    if ema9 > ema20:
        margin = (ema9 - ema20) / ema20
        return min(1.0, 0.5 + margin * 10)
    return 0.0


def rule_price_above_vwap(snap: dict) -> float:
    price = snap.get("close")
    vwap  = snap.get("vwap")
    if price is None or vwap is None:
        return 0.3  # neutral if VWAP not available
    if price > vwap:
        margin = (price - vwap) / vwap
        return min(1.0, 0.5 + margin * 5)
    return 0.0


def rule_rsi_bullish_range(snap: dict) -> float:
    """RSI in healthy bull range: 45-70."""
    rsi = snap.get("rsi")
    if rsi is None:
        return 0.0
    if 45 <= rsi <= 70:
        # Peak confidence at RSI ~55
        deviation = abs(rsi - 57.5) / 12.5
        return max(0.3, 1.0 - deviation * 0.5)
    return 0.0


def rule_rsi_momentum(snap: dict) -> float:
    """RSI in 50-65 range (scalping)."""
    rsi = snap.get("rsi")
    if rsi is None:
        return 0.0
    if 50 <= rsi <= 65:
        return 1.0
    if 45 <= rsi < 50:
        return 0.5
    return 0.0


def rule_rsi_oversold(snap: dict) -> float:
    """RSI < 35 (mean reversion buy trigger)."""
    rsi = snap.get("rsi")
    if rsi is None:
        return 0.0
    if rsi < 25:
        return 1.0
    if rsi < 35:
        return 0.7
    if rsi < 42:
        return 0.3
    return 0.0


def rule_macd_bullish(snap: dict) -> float:
    """MACD > Signal line."""
    macd   = snap.get("macd")
    signal = snap.get("macd_signal")
    hist   = snap.get("macd_hist")
    if macd is None or signal is None:
        return 0.0
    if macd > signal:
        # Extra confidence if histogram is also rising
        prev_hist = snap.get("_prev", {}).get("macd_hist")
        bonus = 0.2 if (hist and prev_hist and hist > prev_hist) else 0.0
        return min(1.0, 0.7 + bonus)
    return 0.0


def rule_macd_histogram_rising(snap: dict) -> float:
    hist      = snap.get("macd_hist")
    prev_hist = snap.get("_prev", {}).get("macd_hist")
    if hist is None or prev_hist is None:
        return 0.0
    if hist > 0 and hist > prev_hist:
        return 1.0
    if hist > prev_hist:
        return 0.5
    return 0.0


def rule_adx_strong(snap: dict) -> float:
    """ADX > 25 = trending market."""
    adx = snap.get("adx")
    if adx is None:
        return 0.3
    if adx >= 40:
        return 1.0
    if adx >= 25:
        return 0.7
    if adx >= 20:
        return 0.4
    return 0.0


def rule_adx_rising(snap: dict) -> float:
    adx      = snap.get("adx")
    prev_adx = snap.get("_prev", {}).get("adx")
    if adx is None:
        return 0.0
    base = rule_adx_strong(snap)
    if prev_adx and adx > prev_adx:
        return min(1.0, base + 0.2)
    return base


def rule_volume_above_avg(snap: dict) -> float:
    """Current volume > volume MA * 1.2."""
    vol    = snap.get("volume")
    vol_ma = snap.get("volume_ma")
    if vol is None or vol_ma is None or vol_ma == 0:
        return 0.3
    ratio = vol / vol_ma
    if ratio >= 2.0:
        return 1.0
    if ratio >= 1.5:
        return 0.8
    if ratio >= 1.2:
        return 0.6
    if ratio >= 1.0:
        return 0.4
    return 0.0


def rule_volume_surge(snap: dict) -> float:
    """Volume >= 1.5x average (breakout confirmation)."""
    vol    = snap.get("volume")
    vol_ma = snap.get("volume_ma")
    if vol is None or vol_ma is None or vol_ma == 0:
        return 0.0
    ratio = vol / vol_ma
    if ratio >= 3.0:
        return 1.0
    if ratio >= 2.0:
        return 0.8
    if ratio >= 1.5:
        return 0.5
    return 0.0


def rule_bb_not_overbought(snap: dict) -> float:
    """Price not above BB upper band (not extended)."""
    close    = snap.get("close")
    bb_upper = snap.get("bb_upper")
    bb_mid   = snap.get("bb_mid")
    if close is None or bb_upper is None or bb_mid is None:
        return 0.5
    bb_pct = (close - bb_mid) / (bb_upper - bb_mid) if bb_upper != bb_mid else 0
    if bb_pct <= 0.5:
        return 1.0
    if bb_pct <= 0.8:
        return 0.7
    if bb_pct <= 1.0:
        return 0.3
    return 0.0  # Above upper band


def rule_bb_lower_band_touch(snap: dict) -> float:
    """Price near or below BB lower band (oversold / mean reversion)."""
    close    = snap.get("close")
    bb_lower = snap.get("bb_lower")
    bb_mid   = snap.get("bb_mid")
    if close is None or bb_lower is None or bb_mid is None:
        return 0.0
    if close <= bb_lower:
        return 1.0
    pct_from_lower = (close - bb_lower) / (bb_mid - bb_lower) if bb_mid != bb_lower else 1.0
    if pct_from_lower <= 0.2:
        return 0.7
    return 0.0


def rule_bb_keltner_squeeze(snap: dict) -> float:
    """BB inside KC = volatility squeeze (breakout imminent)."""
    squeeze = snap.get("squeeze")
    if squeeze is None:
        # Try manual check
        bb_upper = snap.get("bb_upper")
        bb_lower = snap.get("bb_lower")
        kc_upper = snap.get("kc_upper")
        kc_lower = snap.get("kc_lower")
        if all(v is not None for v in [bb_upper, bb_lower, kc_upper, kc_lower]):
            squeeze = bb_upper < kc_upper and bb_lower > kc_lower
        else:
            return 0.0
    return 1.0 if squeeze else 0.0


def rule_stoch_not_overbought(snap: dict) -> float:
    """Stoch K < 80 (not in overbought zone)."""
    k = snap.get("stoch_k")
    if k is None:
        return 0.5
    if k < 50:
        return 1.0
    if k < 70:
        return 0.7
    if k < 80:
        return 0.4
    return 0.0


def rule_stoch_oversold(snap: dict) -> float:
    """Stoch K < 20 (oversold)."""
    k = snap.get("stoch_k")
    if k is None:
        return 0.0
    if k < 15:
        return 1.0
    if k < 20:
        return 0.7
    if k < 30:
        return 0.3
    return 0.0


def rule_price_breaks_resistance(snap: dict) -> float:
    """Price above Donchian upper (channel breakout)."""
    close        = snap.get("close")
    don_upper    = snap.get("donchian_upper")
    prev_close   = snap.get("_prev", {}).get("close")
    prev_upper   = snap.get("_prev", {}).get("donchian_upper")

    if close is None or don_upper is None:
        return 0.0

    # Price just broke above donchian upper
    if prev_close and prev_upper:
        if prev_close <= prev_upper and close > don_upper:
            return 1.0  # Fresh breakout
    if close > don_upper:
        return 0.5  # Already above

    return 0.0


def rule_price_near_support(snap: dict) -> float:
    """Price near Donchian lower (support zone)."""
    close     = snap.get("close")
    don_lower = snap.get("donchian_lower")
    if close is None or don_lower is None:
        return 0.0
    pct_above = (close - don_lower) / don_lower if don_lower > 0 else 1.0
    if pct_above <= 0.01:
        return 1.0
    if pct_above <= 0.03:
        return 0.7
    if pct_above <= 0.05:
        return 0.3
    return 0.0


def rule_market_regime_bullish(snap: dict, regime: dict = None) -> float:
    """SPY/market regime is supportive for long positions."""
    if regime is None:
        return 0.5  # neutral if no regime data
    r = regime.get("regime", "neutral")
    if r == "bullish":
        return 1.0
    if r == "neutral":
        return 0.5
    return 0.0  # bearish


def rule_market_regime_neutral(snap: dict, regime: dict = None) -> float:
    """Regime is not strongly trending (ok for mean reversion)."""
    if regime is None:
        return 0.5
    r = regime.get("regime", "neutral")
    if r == "neutral":
        return 1.0
    return 0.3


def rule_weekly_trend_bullish(snap: dict) -> float:
    """Price above SMA 200 (long-term trend proxy)."""
    close  = snap.get("close")
    sma200 = snap.get("sma_200")
    if close is None or sma200 is None:
        return 0.3
    if close > sma200:
        margin = (close - sma200) / sma200
        return min(1.0, 0.6 + margin * 3)
    return 0.0


# ============================================================
# RULE REGISTRY
# ============================================================

RULE_FUNCTIONS = {
    "ema_alignment_bullish":  rule_ema_alignment_bullish,
    "ema_alignment_bearish":  rule_ema_alignment_bearish,
    "ema9_above_ema20":       rule_ema9_above_ema20,
    "price_above_vwap":       rule_price_above_vwap,
    "rsi_bullish_range":      rule_rsi_bullish_range,
    "rsi_momentum":           rule_rsi_momentum,
    "rsi_oversold":           rule_rsi_oversold,
    "macd_bullish":           rule_macd_bullish,
    "macd_histogram_rising":  rule_macd_histogram_rising,
    "adx_strong":             rule_adx_strong,
    "adx_rising":             rule_adx_rising,
    "volume_above_avg":       rule_volume_above_avg,
    "volume_surge":           rule_volume_surge,
    "bb_not_overbought":      rule_bb_not_overbought,
    "bb_lower_band_touch":    rule_bb_lower_band_touch,
    "bb_keltner_squeeze":     rule_bb_keltner_squeeze,
    "stoch_not_overbought":   rule_stoch_not_overbought,
    "stoch_oversold":         rule_stoch_oversold,
    "price_breaks_resistance":rule_price_breaks_resistance,
    "price_near_support":     rule_price_near_support,
    "market_regime_bullish":  rule_market_regime_bullish,
    "market_regime_neutral":  rule_market_regime_neutral,
    "weekly_trend_bullish":   rule_weekly_trend_bullish,
}


# ============================================================
# SCORE COMPUTATION
# ============================================================

def compute_score(
    snap: dict,
    rule_weights: Dict[str, float],
    regime: Optional[dict] = None,
) -> Tuple[float, Dict[str, float]]:
    """
    Compute weighted confluence score.

    Parameters
    ----------
    snap : dict
        Latest indicator snapshot (from engine.get_latest_values)
    rule_weights : Dict[str, float]
        Rule name -> weight (from strategy preset)
    regime : dict, optional
        Market regime context from SPY analysis

    Returns
    -------
    score : float   (0-100)
    rule_results : dict   {rule_name: confidence (0-1)}
    """
    total_weight = 0.0
    weighted_sum = 0.0
    rule_results: Dict[str, float] = {}

    for rule_name, weight in rule_weights.items():
        func = RULE_FUNCTIONS.get(rule_name)
        if func is None:
            continue

        try:
            if rule_name in ("market_regime_bullish", "market_regime_neutral"):
                confidence = func(snap, regime=regime)
            else:
                confidence = func(snap)
        except Exception:
            confidence = 0.0

        rule_results[rule_name] = round(confidence, 3)
        weighted_sum += weight * confidence
        total_weight += weight

    score = (weighted_sum / total_weight * 100) if total_weight > 0 else 0.0
    return round(score, 1), rule_results


# ============================================================
# TRADE MANAGEMENT OUTPUT
# ============================================================

def compute_trade_levels(
    price: float,
    atr: Optional[float],
    direction: str = "buy",
    risk_reward: float = 2.0,
) -> Dict:
    """
    Compute entry zone, stop loss, and take profit levels.

    Uses ATR-based stop as default. If ATR is unavailable, uses
    a percentage-based fallback (1% stop).
    """
    if atr is None or atr == 0:
        atr = price * 0.01  # 1% fallback

    if direction == "buy":
        entry_low  = round(price * 0.999, 6)
        entry_high = round(price * 1.002, 6)
        stop       = round(price - 1.5 * atr, 6)
        tp1        = round(price + 2.0 * atr, 6)
        tp2        = round(price + 3.5 * atr, 6)
    else:  # sell / short
        entry_low  = round(price * 0.998, 6)
        entry_high = round(price * 1.001, 6)
        stop       = round(price + 1.5 * atr, 6)
        tp1        = round(price - 2.0 * atr, 6)
        tp2        = round(price - 3.5 * atr, 6)

    rr_1 = round(abs(tp1 - price) / abs(price - stop), 2) if price != stop else 0
    rr_2 = round(abs(tp2 - price) / abs(price - stop), 2) if price != stop else 0

    return {
        "entry_zone": f"{entry_low} - {entry_high}",
        "stop_loss":   stop,
        "take_profit_1": tp1,
        "take_profit_2": tp2,
        "risk_reward_1": rr_1,
        "risk_reward_2": rr_2,
        "atr_stop": round(1.5 * atr, 6),
    }
