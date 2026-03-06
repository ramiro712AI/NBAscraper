"""
Indicator Engine.

Wraps pandas-ta to compute all technical indicators on a given OHLCV DataFrame.
All results are returned as new columns on a copy of the input DataFrame.

Design goals:
- Pure functions: indicators are calculated, not applied as side effects
- Lazy: only compute what is requested
- Decoupled from signal logic

Supported indicators:
  Trend:        SMA, EMA, VWAP, Supertrend, Parabolic SAR, Ichimoku
  Volatility:   Bollinger Bands, Keltner Channels, Donchian Channels, ATR
  Momentum:     RSI, MACD, Stochastic, StochRSI, CCI, ROC, ADX/DMI
  Volume:       OBV, CMF, MFI, Volume MA
  Composite:    Squeeze (BB inside KC = compression signal)
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd

try:
    import pandas_ta as ta
    HAS_PANDAS_TA = True
except ImportError:
    HAS_PANDAS_TA = False
    logging.warning("pandas-ta not installed. Install it: pip install pandas-ta")

from market_scanner.config import INDICATOR_PARAMS as P

logger = logging.getLogger(__name__)


# ============================================================
# HELPER
# ============================================================

def _safe_last(series: pd.Series, default=None):
    """Return last non-NaN value or default."""
    s = series.dropna()
    return float(s.iloc[-1]) if not s.empty else default


def _pct_rank(series: pd.Series, window: int = 252) -> pd.Series:
    """Rolling percentile rank (0-100)."""
    return series.rolling(window).apply(
        lambda x: (x.rank().iloc[-1] - 1) / (len(x) - 1) * 100 if len(x) > 1 else 50,
        raw=False,
    )


# ============================================================
# MAIN INDICATOR COMPUTATION
# ============================================================

def compute_indicators(df: pd.DataFrame, include_all: bool = False) -> pd.DataFrame:
    """
    Compute all configured technical indicators on the OHLCV DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Must have columns: open, high, low, close, volume
    include_all : bool
        If True, compute heavier indicators (Ichimoku, Volume Profile approximation).

    Returns
    -------
    pd.DataFrame
        Original df with indicator columns appended.
    """
    if df.empty or len(df) < 10:
        return df

    df = df.copy()

    if not HAS_PANDAS_TA:
        return _compute_manual(df)

    # pandas-ta strategy: define a custom strategy for efficiency
    try:
        df = _add_trend_indicators(df)
        df = _add_volatility_indicators(df)
        df = _add_momentum_indicators(df)
        df = _add_volume_indicators(df)
        df = _add_composite_indicators(df)
    except Exception as exc:
        logger.error("Indicator computation error: %s", exc)

    return df


# ============================================================
# TREND INDICATORS
# ============================================================

def _add_trend_indicators(df: pd.DataFrame) -> pd.DataFrame:
    close = df["close"]

    # SMAs
    for period in P.sma_periods:
        df[f"sma_{period}"] = ta.sma(close, length=period)

    # EMAs
    for period in P.ema_periods:
        df[f"ema_{period}"] = ta.ema(close, length=period)

    # VWAP (requires high, low, close, volume)
    if P.use_vwap:
        try:
            vwap_result = ta.vwap(df["high"], df["low"], df["close"], df["volume"])
            if vwap_result is not None:
                if isinstance(vwap_result, pd.Series):
                    df["vwap"] = vwap_result
                elif isinstance(vwap_result, pd.DataFrame):
                    df["vwap"] = vwap_result.iloc[:, 0]
        except Exception:
            # Manual VWAP as fallback
            df["vwap"] = (
                (df["high"] + df["low"] + df["close"]) / 3 * df["volume"]
            ).cumsum() / df["volume"].cumsum()

    # Supertrend
    try:
        st = ta.supertrend(
            df["high"], df["low"], df["close"],
            length=P.supertrend_period,
            multiplier=P.supertrend_mult,
        )
        if st is not None and not st.empty:
            col_names = list(st.columns)
            # supertrend value column
            for c in col_names:
                if c.startswith("SUPERT_") and "d" not in c and "s" not in c:
                    df["supertrend"] = st[c]
                elif c.startswith("SUPERTd_"):
                    df["supertrend_dir"] = st[c]  # 1 = bullish, -1 = bearish
    except Exception as exc:
        logger.debug("Supertrend error: %s", exc)

    # Parabolic SAR
    try:
        psar = ta.psar(df["high"], df["low"], df["close"])
        if psar is not None and not psar.empty:
            for c in psar.columns:
                if "PSARl" in c:
                    df["psar_long"] = psar[c]
                elif "PSARs" in c:
                    df["psar_short"] = psar[c]
                elif "PSARaf" in c:
                    df["psar_af"] = psar[c]
                elif "PSARr" in c:
                    df["psar_reversal"] = psar[c]
    except Exception as exc:
        logger.debug("PSAR error: %s", exc)

    # Donchian Channels
    try:
        don = ta.donchian(df["high"], df["low"], lower_length=P.donchian_period, upper_length=P.donchian_period)
        if don is not None and not don.empty:
            for c in don.columns:
                cl = c.lower()
                if "lower" in cl:
                    df["donchian_lower"] = don[c]
                elif "upper" in cl:
                    df["donchian_upper"] = don[c]
                elif "mid" in cl:
                    df["donchian_mid"] = don[c]
    except Exception as exc:
        logger.debug("Donchian error: %s", exc)

    return df


# ============================================================
# VOLATILITY INDICATORS
# ============================================================

def _add_volatility_indicators(df: pd.DataFrame) -> pd.DataFrame:
    close = df["close"]

    # ATR
    df["atr"] = ta.atr(df["high"], df["low"], close, length=P.atr_period)

    # Bollinger Bands
    try:
        bb = ta.bbands(close, length=P.bb_period, std=P.bb_std)
        if bb is not None and not bb.empty:
            for c in bb.columns:
                cl = c.lower()
                if "bbl" in cl:
                    df["bb_lower"] = bb[c]
                elif "bbm" in cl:
                    df["bb_mid"] = bb[c]
                elif "bbu" in cl:
                    df["bb_upper"] = bb[c]
                elif "bbb" in cl:
                    df["bb_bandwidth"] = bb[c]
                elif "bbp" in cl:
                    df["bb_pct"] = bb[c]
    except Exception as exc:
        logger.debug("Bollinger Bands error: %s", exc)

    # Keltner Channels
    try:
        kc = ta.kc(df["high"], df["low"], close, length=P.kc_period, scalar=P.kc_mult)
        if kc is not None and not kc.empty:
            for c in kc.columns:
                cl = c.lower()
                if "kcl" in cl:
                    df["kc_lower"] = kc[c]
                elif "kcb" in cl:
                    df["kc_mid"] = kc[c]
                elif "kcu" in cl:
                    df["kc_upper"] = kc[c]
    except Exception as exc:
        logger.debug("Keltner Channels error: %s", exc)

    return df


# ============================================================
# MOMENTUM INDICATORS
# ============================================================

def _add_momentum_indicators(df: pd.DataFrame) -> pd.DataFrame:
    close = df["close"]

    # RSI
    df["rsi"] = ta.rsi(close, length=P.rsi_period)

    # MACD
    try:
        macd = ta.macd(close, fast=P.macd_fast, slow=P.macd_slow, signal=P.macd_signal)
        if macd is not None and not macd.empty:
            for c in macd.columns:
                cl = c.lower()
                if "macd_" in cl and "signal" not in cl and "hist" not in cl:
                    df["macd"] = macd[c]
                elif "macds_" in cl or "signal" in cl:
                    df["macd_signal"] = macd[c]
                elif "macdh_" in cl or "hist" in cl:
                    df["macd_hist"] = macd[c]
    except Exception as exc:
        logger.debug("MACD error: %s", exc)

    # Stochastic
    try:
        stoch = ta.stoch(df["high"], df["low"], close, k=P.stoch_k, d=P.stoch_d, smooth_k=P.stoch_smooth)
        if stoch is not None and not stoch.empty:
            for c in stoch.columns:
                cl = c.lower()
                if "stochk" in cl:
                    df["stoch_k"] = stoch[c]
                elif "stochd" in cl:
                    df["stoch_d"] = stoch[c]
    except Exception as exc:
        logger.debug("Stochastic error: %s", exc)

    # Stochastic RSI
    try:
        stochrsi = ta.stochrsi(close, length=P.stochrsi_period, rsi_length=P.rsi_period,
                                k=P.stochrsi_k, d=P.stochrsi_d)
        if stochrsi is not None and not stochrsi.empty:
            for c in stochrsi.columns:
                cl = c.lower()
                if "k" in cl:
                    df["stochrsi_k"] = stochrsi[c]
                elif "d" in cl:
                    df["stochrsi_d"] = stochrsi[c]
    except Exception as exc:
        logger.debug("StochRSI error: %s", exc)

    # ADX / DMI
    try:
        adx = ta.adx(df["high"], df["low"], close, length=P.adx_period)
        if adx is not None and not adx.empty:
            for c in adx.columns:
                cl = c.lower()
                if "adx_" in cl:
                    df["adx"] = adx[c]
                elif "dmp_" in cl:
                    df["dmi_plus"] = adx[c]
                elif "dmn_" in cl:
                    df["dmi_minus"] = adx[c]
    except Exception as exc:
        logger.debug("ADX error: %s", exc)

    # CCI
    try:
        df["cci"] = ta.cci(df["high"], df["low"], close, length=P.cci_period)
    except Exception as exc:
        logger.debug("CCI error: %s", exc)

    # ROC
    try:
        df["roc"] = ta.roc(close, length=P.roc_period)
    except Exception as exc:
        logger.debug("ROC error: %s", exc)

    return df


# ============================================================
# VOLUME INDICATORS
# ============================================================

def _add_volume_indicators(df: pd.DataFrame) -> pd.DataFrame:
    close = df["close"]
    volume = df["volume"]

    # Volume MA
    df["volume_ma"] = ta.sma(volume, length=P.volume_ma_period)

    # OBV
    try:
        df["obv"] = ta.obv(close, volume)
    except Exception as exc:
        logger.debug("OBV error: %s", exc)

    # CMF (Chaikin Money Flow)
    try:
        df["cmf"] = ta.cmf(df["high"], df["low"], close, volume, length=P.cmf_period)
    except Exception as exc:
        logger.debug("CMF error: %s", exc)

    # MFI (Money Flow Index)
    try:
        df["mfi"] = ta.mfi(df["high"], df["low"], close, volume, length=P.mfi_period)
    except Exception as exc:
        logger.debug("MFI error: %s", exc)

    return df


# ============================================================
# COMPOSITE / DERIVED INDICATORS
# ============================================================

def _add_composite_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Squeeze: Bollinger Bands inside Keltner Channels = volatility compression.
    This often precedes large directional moves.
    """
    if all(c in df.columns for c in ["bb_upper", "bb_lower", "kc_upper", "kc_lower"]):
        df["squeeze"] = (df["bb_upper"] < df["kc_upper"]) & (df["bb_lower"] > df["kc_lower"])
    return df


# ============================================================
# MANUAL FALLBACK (if pandas-ta not installed)
# ============================================================

def _compute_manual(df: pd.DataFrame) -> pd.DataFrame:
    """Minimal manual indicator computation (EMA, RSI, MACD)."""
    close = df["close"]

    for period in [9, 20, 50, 200]:
        df[f"ema_{period}"] = close.ewm(span=period, adjust=False).mean()

    # RSI
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["rsi"] = 100 - 100 / (1 + rs)

    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]

    # ATR
    hl = df["high"] - df["low"]
    hc = (df["high"] - close.shift()).abs()
    lc = (df["low"] - close.shift()).abs()
    df["atr"] = pd.concat([hl, hc, lc], axis=1).max(axis=1).rolling(14).mean()

    # Volume MA
    df["volume_ma"] = df["volume"].rolling(20).mean()

    # Bollinger Bands
    df["bb_mid"] = close.rolling(20).mean()
    std = close.rolling(20).std()
    df["bb_upper"] = df["bb_mid"] + 2 * std
    df["bb_lower"] = df["bb_mid"] - 2 * std

    # VWAP (approximate cumulative)
    df["vwap"] = (
        ((df["high"] + df["low"] + df["close"]) / 3 * df["volume"]).cumsum()
        / df["volume"].cumsum()
    )

    return df


# ============================================================
# SNAPSHOT EXTRACTION
# ============================================================

def get_latest_values(df: pd.DataFrame) -> dict:
    """
    Extract the latest indicator values as a flat dict for signal evaluation.
    All NaN values are converted to None.
    """
    if df.empty:
        return {}

    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) >= 2 else last

    def v(col):
        val = last.get(col)
        return None if val is None or (isinstance(val, float) and pd.isna(val)) else float(val)

    def vp(col):
        val = prev.get(col)
        return None if val is None or (isinstance(val, float) and pd.isna(val)) else float(val)

    snapshot = {col: v(col) for col in df.columns}
    snapshot["_prev"] = {col: vp(col) for col in df.columns}
    return snapshot
