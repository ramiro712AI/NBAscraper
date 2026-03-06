"""
Central configuration for the Market Scanner platform.

All settings come from environment variables (via .env) or hardcoded defaults.
Strategy presets, indicator parameters, and scanning universes are all here.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()


# ============================================================
# API CREDENTIALS
# ============================================================

CRYPTO_API_KEY: str = os.getenv("CRYPTO_API_KEY", "")
CRYPTO_SECRET_KEY: str = os.getenv("CRYPTO_SECRET_KEY", "")

CRYPTO_COM_EXCHANGE_URL: str = "https://api.crypto.com/exchange/v1/"

TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

ALERT_WEBHOOK_URL: str = os.getenv("ALERT_WEBHOOK_URL", "")

EMAIL_SMTP_HOST: str = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
EMAIL_SMTP_PORT: int = int(os.getenv("EMAIL_SMTP_PORT", "587"))
EMAIL_USER: str = os.getenv("EMAIL_USER", "")
EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
EMAIL_TO: str = os.getenv("EMAIL_TO", "")

# ============================================================
# DATABASE
# ============================================================

DB_URL: str = os.getenv("DATABASE_URL", "sqlite:///market_scanner.db")

# ============================================================
# SCANNING INTERVALS (seconds)
# ============================================================

CRYPTO_SCAN_INTERVAL: int = int(os.getenv("CRYPTO_SCAN_INTERVAL", "60"))
STOCK_SCAN_INTERVAL: int = int(os.getenv("STOCK_SCAN_INTERVAL", "120"))
BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "20"))

# ============================================================
# DEFAULT CRYPTO UNIVERSE
# ============================================================

DEFAULT_CRYPTO_SYMBOLS: List[str] = [
    "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT",
    "ADA/USDT", "AVAX/USDT", "DOGE/USDT", "MATIC/USDT", "DOT/USDT",
    "LINK/USDT", "UNI/USDT", "LTC/USDT", "ATOM/USDT", "XLM/USDT",
    "NEAR/USDT", "APT/USDT", "ARB/USDT", "OP/USDT", "SUI/USDT",
    "FIL/USDT", "ICP/USDT", "INJ/USDT", "SEI/USDT", "TIA/USDT",
    "PEPE/USDT", "WIF/USDT", "BONK/USDT", "FLOKI/USDT", "SHIB/USDT",
]

# ============================================================
# DEFAULT STOCK UNIVERSE
# ============================================================

DEFAULT_STOCK_SYMBOLS: List[str] = [
    # Mega-cap
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "BRK-B",
    # Large-cap tech
    "AMD", "INTC", "ORCL", "CRM", "ADBE", "NOW", "SNOW", "PLTR",
    # ETFs / Index
    "SPY", "QQQ", "IWM", "DIA",
    # Financial
    "JPM", "BAC", "GS", "MS",
    # Healthcare
    "JNJ", "UNH", "MRNA", "PFE",
    # Energy
    "XOM", "CVX",
    # High-beta / momentum
    "COIN", "HOOD", "MSTR", "SQ", "ROKU", "SMCI",
]

SPY_SYMBOL: str = "SPY"  # Market regime proxy

# ============================================================
# EXCHANGE / VENUE MAPPING
# ============================================================

# Which exchanges support each base currency (checked via CCXT)
EXCHANGE_PRIORITY: List[str] = [
    "crypto_com",  # Primary (authenticated)
    "binance",
    "bybit",
    "okx",
    "kraken",
    "coinbase",
    "kucoin",
]

# Exchange display names
EXCHANGE_DISPLAY: Dict[str, str] = {
    "crypto_com": "Crypto.com",
    "binance": "Binance",
    "bybit": "Bybit",
    "okx": "OKX",
    "kraken": "Kraken",
    "coinbase": "Coinbase",
    "kucoin": "KuCoin",
    "gateio": "Gate.io",
    "huobi": "HTX",
}

# ============================================================
# TIMEFRAMES
# ============================================================

TIMEFRAMES: Dict[str, str] = {
    "1m":  "1 min",
    "3m":  "3 min",
    "5m":  "5 min",
    "15m": "15 min",
    "30m": "30 min",
    "1h":  "1 Hour",
    "4h":  "4 Hour",
    "1d":  "Daily",
    "1w":  "Weekly",
}

STRATEGY_TIMEFRAMES: Dict[str, List[str]] = {
    "scalping":       ["1m", "3m", "5m"],
    "day_trading":    ["5m", "15m", "30m"],
    "swing":          ["1h", "4h", "1d"],
    "trend_following":["4h", "1d"],
    "breakout":       ["15m", "1h", "4h"],
    "mean_reversion": ["1h", "4h"],
}

# ============================================================
# INDICATOR PARAMETERS
# ============================================================

@dataclass
class IndicatorParams:
    # SMA periods
    sma_periods: List[int] = field(default_factory=lambda: [20, 50, 100, 200])
    # EMA periods
    ema_periods: List[int] = field(default_factory=lambda: [9, 20, 21, 50, 200])
    # RSI
    rsi_period: int = 14
    rsi_overbought: float = 70.0
    rsi_oversold: float = 30.0
    # MACD
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    # Bollinger Bands
    bb_period: int = 20
    bb_std: float = 2.0
    # Keltner Channels
    kc_period: int = 20
    kc_mult: float = 1.5
    # ATR
    atr_period: int = 14
    # ADX
    adx_period: int = 14
    adx_threshold: float = 25.0
    # Stochastic
    stoch_k: int = 14
    stoch_d: int = 3
    stoch_smooth: int = 3
    # Stochastic RSI
    stochrsi_period: int = 14
    stochrsi_k: int = 3
    stochrsi_d: int = 3
    # OBV/CMF
    cmf_period: int = 20
    # MFI
    mfi_period: int = 14
    # CCI
    cci_period: int = 20
    # ROC
    roc_period: int = 12
    # Volume average
    volume_ma_period: int = 20
    volume_surge_threshold: float = 1.5   # 1.5x average = high volume
    # Supertrend
    supertrend_period: int = 10
    supertrend_mult: float = 3.0
    # Donchian
    donchian_period: int = 20
    # VWAP (calculated intraday per session reset)
    use_vwap: bool = True


INDICATOR_PARAMS = IndicatorParams()

# ============================================================
# STRATEGY PRESETS
# ============================================================

@dataclass
class StrategyPreset:
    name: str
    description: str
    timeframes: List[str]
    # Signal rule weights (sum should be ~100)
    rules: Dict[str, float]
    min_score: float = 55.0
    asset_type: str = "both"  # "crypto", "stocks", "both"


STRATEGY_PRESETS: Dict[str, StrategyPreset] = {
    "trend_following": StrategyPreset(
        name="Trend Following",
        description="Ride established trends using EMA alignment + ADX + MACD",
        timeframes=["4h", "1d"],
        rules={
            "ema_alignment_bullish":    20.0,  # EMA9>EMA20>EMA50>EMA200
            "adx_strong":              15.0,   # ADX > 25
            "macd_bullish":            15.0,   # MACD > signal
            "price_above_vwap":        10.0,
            "rsi_bullish_range":       10.0,   # 50-70
            "volume_above_avg":        10.0,
            "bb_not_overbought":       10.0,
            "market_regime_bullish":   10.0,
        },
        min_score=60.0,
    ),
    "breakout": StrategyPreset(
        name="Breakout",
        description="Capture breakouts from consolidation / squeeze",
        timeframes=["15m", "1h", "4h"],
        rules={
            "bb_keltner_squeeze":       20.0,  # BB inside Keltner = squeeze
            "volume_surge":             20.0,  # Volume spike
            "price_breaks_resistance":  20.0,
            "macd_bullish":             10.0,
            "rsi_bullish_range":        10.0,
            "adx_rising":               10.0,
            "market_regime_bullish":    10.0,
        },
        min_score=55.0,
    ),
    "scalping": StrategyPreset(
        name="Scalping",
        description="High-frequency micro setups with tight stops",
        timeframes=["1m", "3m", "5m"],
        rules={
            "price_above_vwap":        20.0,
            "ema9_above_ema20":        20.0,
            "rsi_momentum":            15.0,   # RSI 50-65
            "macd_histogram_rising":   15.0,
            "volume_above_avg":        15.0,
            "stoch_not_overbought":    15.0,
        },
        min_score=50.0,
    ),
    "day_trading": StrategyPreset(
        name="Day Trading",
        description="Intraday setups with VWAP, EMA, and volume confirmation",
        timeframes=["5m", "15m", "30m"],
        rules={
            "price_above_vwap":        20.0,
            "ema_alignment_bullish":   15.0,
            "macd_bullish":            15.0,
            "rsi_bullish_range":       10.0,
            "volume_above_avg":        15.0,
            "adx_strong":              10.0,
            "market_regime_bullish":   15.0,
        },
        min_score=55.0,
    ),
    "swing": StrategyPreset(
        name="Swing Trading",
        description="Multi-day swings using higher timeframe confluence",
        timeframes=["4h", "1d"],
        rules={
            "ema_alignment_bullish":   20.0,
            "weekly_trend_bullish":    15.0,
            "rsi_bullish_range":       15.0,
            "macd_bullish":            15.0,
            "volume_above_avg":        10.0,
            "bb_not_overbought":       10.0,
            "market_regime_bullish":   15.0,
        },
        min_score=60.0,
    ),
    "mean_reversion": StrategyPreset(
        name="Mean Reversion",
        description="Buy oversold dips into major support/MAs",
        timeframes=["1h", "4h"],
        rules={
            "rsi_oversold":            25.0,   # RSI < 42, deeper = higher score
            "bb_lower_band_touch":     20.0,   # Price at/near BB lower band
            "stoch_oversold":          20.0,   # Stochastic oversold
            "price_near_support":      15.0,   # Stable Donchian support (not declining)
            "volume_above_avg":        10.0,   # Volume confirmation
            "market_regime_neutral":   10.0,   # Market not in strong trend
        },
        min_score=58.0,
    ),
}

# ============================================================
# SCORING THRESHOLDS
# ============================================================

SCORE_LABELS: Dict[str, tuple] = {
    "very_strong": (80, 100),
    "strong":      (65, 80),
    "moderate":    (50, 65),
    "weak":        (0,  50),
}

# ============================================================
# ALERT SETTINGS
# ============================================================

MIN_ALERT_SCORE: float = 55.0
ALERT_COOLDOWN_SECONDS: int = 300  # 5 min cooldown per symbol+strategy

# ============================================================
# MARKET REGIME THRESHOLDS
# ============================================================

REGIME_EMA_FAST: int = 20
REGIME_EMA_SLOW: int = 50
REGIME_ADX_THRESHOLD: float = 20.0
