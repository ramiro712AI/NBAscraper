"""
Trading Signals Engine
======================
Generates buy/sell signals using technical indicators:
  - RSI (Relative Strength Index)
  - MACD (Moving Average Convergence Divergence)
  - Bollinger Bands
  - EMA crossover (9/21/50)
  - Volume confirmation

Supports stocks (via yfinance) and crypto (via yfinance crypto tickers).
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")


# ─── Indicator calculations ──────────────────────────────────────────────────

def calc_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calc_macd(series: pd.Series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calc_bollinger(series: pd.Series, period: int = 20, std: float = 2.0):
    sma = series.rolling(period).mean()
    sd = series.rolling(period).std()
    upper = sma + std * sd
    lower = sma - std * sd
    return upper, sma, lower


def calc_ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def calc_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df["High"] - df["Low"]
    high_close = (df["High"] - df["Close"].shift()).abs()
    low_close = (df["Low"] - df["Close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean()


# ─── Main signal generator ───────────────────────────────────────────────────

def fetch_data(ticker: str, period: str = "5d", interval: str = "15m") -> pd.DataFrame:
    """Download OHLCV data from Yahoo Finance."""
    df = yf.download(ticker, period=period, interval=interval,
                     auto_adjust=True, progress=False)
    if df.empty:
        raise ValueError(f"No data returned for {ticker}")
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    return df


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add all technical indicators to the dataframe."""
    close = df["Close"].squeeze()

    df["RSI"] = calc_rsi(close)
    df["MACD"], df["MACD_Signal"], df["MACD_Hist"] = calc_macd(close)
    df["BB_Upper"], df["BB_Mid"], df["BB_Lower"] = calc_bollinger(close)
    df["EMA_9"]  = calc_ema(close, 9)
    df["EMA_21"] = calc_ema(close, 21)
    df["EMA_50"] = calc_ema(close, 50)
    df["ATR"]    = calc_atr(df)

    vol = df["Volume"].squeeze()
    df["Vol_MA20"] = vol.rolling(20).mean()
    df["Vol_Ratio"] = vol / df["Vol_MA20"]

    return df


def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Scoring system (0–100).  Each condition adds points:
      BUY  signals → positive score
      SELL signals → negative score
    Final call: score >= 60 → BUY | score <= -60 → SELL | else HOLD
    """
    df = df.copy()
    df["Score"] = 0.0

    close  = df["Close"].squeeze()
    rsi    = df["RSI"]
    macd_h = df["MACD_Hist"]

    # ── RSI (20 pts) ──────────────────────────────────────────────────────────
    df.loc[rsi < 30, "Score"] += 20          # oversold  → buy
    df.loc[rsi > 70, "Score"] -= 20          # overbought→ sell
    df.loc[(rsi >= 30) & (rsi < 50), "Score"] += 10
    df.loc[(rsi > 50) & (rsi <= 70), "Score"] -= 10

    # ── MACD histogram flip (25 pts) ─────────────────────────────────────────
    prev_h = macd_h.shift(1)
    df.loc[(prev_h < 0) & (macd_h > 0), "Score"] += 25   # bearish→bullish
    df.loc[(prev_h > 0) & (macd_h < 0), "Score"] -= 25   # bullish→bearish
    df.loc[macd_h > 0, "Score"] += 10
    df.loc[macd_h < 0, "Score"] -= 10

    # ── Bollinger Bands (20 pts) ─────────────────────────────────────────────
    df.loc[close < df["BB_Lower"], "Score"] += 20   # price below lower band
    df.loc[close > df["BB_Upper"], "Score"] -= 20   # price above upper band

    # ── EMA crossover (25 pts) ───────────────────────────────────────────────
    df.loc[df["EMA_9"] > df["EMA_21"], "Score"] += 15    # short > mid  → bullish
    df.loc[df["EMA_9"] < df["EMA_21"], "Score"] -= 15
    df.loc[close > df["EMA_50"], "Score"] += 10     # price above long term
    df.loc[close < df["EMA_50"], "Score"] -= 10

    # ── Volume confirmation (10 pts) ─────────────────────────────────────────
    high_vol = df["Vol_Ratio"] > 1.5
    df.loc[high_vol & (df["Score"] > 0), "Score"] += 10
    df.loc[high_vol & (df["Score"] < 0), "Score"] -= 10

    # ── Final signal ─────────────────────────────────────────────────────────
    df["Signal"] = "HOLD"
    df.loc[df["Score"] >= 60,  "Signal"] = "BUY"
    df.loc[df["Score"] <= -60, "Signal"] = "SELL"

    return df


def risk_levels(df: pd.DataFrame, risk_pct: float = 0.02) -> pd.DataFrame:
    """Add stop-loss and take-profit levels based on ATR."""
    df = df.copy()
    atr = df["ATR"]
    close = df["Close"].squeeze()
    df["StopLoss"]   = close - 1.5 * atr      # 1.5x ATR below entry
    df["TakeProfit"] = close + 3.0 * atr      # 3x ATR above entry (2:1 RR)
    return df


# ─── Scanner ─────────────────────────────────────────────────────────────────

def scan_tickers(tickers: list, period="5d", interval="15m") -> pd.DataFrame:
    """
    Scan a list of tickers and return a summary with the latest signal.
    """
    results = []
    for ticker in tickers:
        try:
            df = fetch_data(ticker, period=period, interval=interval)
            df = add_indicators(df)
            df = generate_signals(df)
            df = risk_levels(df)
            last = df.iloc[-1]
            results.append({
                "Ticker":     ticker,
                "Price":      round(float(last["Close"]), 4),
                "Signal":     last["Signal"],
                "Score":      round(float(last["Score"]), 1),
                "RSI":        round(float(last["RSI"]), 1),
                "MACD_Hist":  round(float(last["MACD_Hist"]), 6),
                "StopLoss":   round(float(last["StopLoss"]), 4),
                "TakeProfit": round(float(last["TakeProfit"]), 4),
                "Time":       df.index[-1].strftime("%Y-%m-%d %H:%M"),
            })
        except Exception as e:
            results.append({"Ticker": ticker, "Signal": "ERROR", "Score": 0,
                            "Error": str(e)})
    return pd.DataFrame(results)


# ─── CLI quick scan ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    STOCKS  = ["AAPL", "TSLA", "NVDA", "MSFT", "AMZN", "SPY"]
    CRYPTOS = ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD"]

    print("\n" + "="*70)
    print("  TRADING SIGNAL SCANNER  —  " + datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("="*70)

    for label, tickers in [("STOCKS", STOCKS), ("CRYPTO", CRYPTOS)]:
        print(f"\n{'─'*70}")
        print(f"  {label}")
        print(f"{'─'*70}")
        summary = scan_tickers(tickers)
        for _, row in summary.iterrows():
            sig = row.get("Signal", "ERROR")
            icon = {"BUY": "🟢 BUY ", "SELL": "🔴 SELL", "HOLD": "⚪ HOLD"}.get(sig, "❌ ERR ")
            try:
                print(f"  {icon}  {row['Ticker']:<10} "
                      f"${row['Price']:<12.4f} "
                      f"Score:{row['Score']:>6.1f}  "
                      f"RSI:{row['RSI']:>5.1f}  "
                      f"SL:{row['StopLoss']:<10.4f} "
                      f"TP:{row['TakeProfit']:<10.4f}")
            except Exception:
                print(f"  ❌ ERR   {row['Ticker']:<10} {row.get('Error','')}")

    print("\n" + "="*70 + "\n")
