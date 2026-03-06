# Market Scanner Pro — Quick Start

## 1. Install dependencies

```bash
pip install -r requirements.txt
```

## 2. Configure environment

```bash
cp .env.example .env
# Edit .env and add your Crypto.com API keys (optional for public data)
```

## 3. Run the dashboard

```bash
python main.py
```

Open your browser at **http://localhost:8050**

## 4. How to use the dashboard

1. **Select Asset Type** — Crypto, Stocks+Options, or All
2. **Select Timeframe** — 1m, 5m, 15m, 1h, 4h, 1D
3. **Select Strategy** — Trend Following, Breakout, Scalping, Day Trading, Swing, Mean Reversion
4. **Click "Scan Now"** — scanner runs across all symbols
5. **Click any signal row** — chart loads with indicators + signal annotations
6. **Toggle overlays** — EMA, VWAP, Bollinger Bands, etc.
7. **Toggle panels** — RSI, MACD, Volume, ADX, Stochastic

## 5. Console-only scan (no browser)

```bash
# Scan crypto
python main.py --scan-only --asset crypto --timeframe 1h

# Scan stocks
python main.py --scan-only --asset stock --timeframe 1d
```

## 6. Auto-refresh

Click the **Auto** button in the dashboard to enable automatic scanning every 60 seconds.

## Strategy Reference

| Strategy | Best For | Timeframes |
|---|---|---|
| Trend Following | Established trends | 4h, 1D |
| Breakout | Squeeze breakouts | 15m, 1h, 4h |
| Scalping | Quick trades | 1m, 3m, 5m |
| Day Trading | Intraday setups | 5m, 15m, 30m |
| Swing | Multi-day holds | 1h, 4h, 1D |
| Mean Reversion | Oversold dips | 1h, 4h |

## Signal Score Labels

| Score | Label | Meaning |
|---|---|---|
| 80-100 | Very Strong | High confluence — top setups |
| 65-79 | Strong | Good confluence |
| 50-64 | Moderate | Some confirmation present |
| 0-49 | Weak | Below filter threshold |

## Architecture

```
market_scanner/
├── config.py          — All settings & strategy presets
├── database.py        — SQLAlchemy ORM (signals, alerts, watchlists)
├── data/
│   ├── crypto_data.py — CCXT multi-exchange OHLCV + Crypto.com private API
│   ├── stock_data.py  — yfinance OHLCV + options chains + SPY regime
│   └── cache.py       — TTL-based OHLCV cache
├── indicators/
│   └── engine.py      — pandas-ta: EMA, RSI, MACD, BB, ATR, ADX, OBV...
├── signals/
│   ├── scoring.py     — Individual rule evaluators + weighted scoring
│   └── signal_engine.py — Orchestrates data→indicators→score→signal
├── scanner/
│   └── scanner.py     — Async batch scanner (ThreadPoolExecutor)
├── alerts/
│   └── alert_engine.py— Alert generation, cooldown, delivery (webhook/Telegram)
└── ui/
    ├── app.py         — Dash app + all callbacks
    ├── charts/
    │   └── chart_builder.py — Plotly candlestick + overlays + panels
    └── layout/
        └── components.py    — Scanner table, signal panel, alert panel
```
