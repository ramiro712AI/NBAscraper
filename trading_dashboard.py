"""
Real-Time Trading Dashboard
============================
Interactive Plotly chart with:
  - Candlestick OHLC
  - Bollinger Bands overlay
  - EMA 9 / 21 / 50 lines
  - RSI panel
  - MACD panel
  - Volume bars with color
  - BUY / SELL signal markers
  - Stop-Loss / Take-Profit annotation on last signal

Usage:
    python trading_dashboard.py             # defaults to BTC-USD, 5d, 15m
    python trading_dashboard.py TSLA 5d 15m
"""

import sys
import webbrowser
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

from trading_signals import fetch_data, add_indicators, generate_signals, risk_levels


# ─── Chart builder ───────────────────────────────────────────────────────────

def build_chart(ticker: str, period: str = "5d", interval: str = "15m") -> go.Figure:
    print(f"  Fetching {ticker}  period={period}  interval={interval} …")
    df = fetch_data(ticker, period=period, interval=interval)
    df = add_indicators(df)
    df = generate_signals(df)
    df = risk_levels(df)

    buys  = df[df["Signal"] == "BUY"]
    sells = df[df["Signal"] == "SELL"]
    last  = df.iloc[-1]
    close_last = float(last["Close"])

    # ── Layout: 4 rows (candles + BB + EMA | RSI | MACD | Volume) ────────────
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        row_heights=[0.50, 0.17, 0.17, 0.16],
        vertical_spacing=0.03,
        subplot_titles=(
            f"{ticker} — {interval} candles",
            "RSI (14)",
            "MACD (12,26,9)",
            "Volume",
        ),
    )

    # ── 1. Candlestick ────────────────────────────────────────────────────────
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        name="OHLC",
        increasing_line_color="#26a69a",
        decreasing_line_color="#ef5350",
    ), row=1, col=1)

    # Bollinger Bands
    fig.add_trace(go.Scatter(x=df.index, y=df["BB_Upper"], name="BB Upper",
                             line=dict(color="rgba(100,149,237,0.6)", width=1, dash="dot")), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["BB_Lower"], name="BB Lower",
                             fill="tonexty",
                             fillcolor="rgba(100,149,237,0.07)",
                             line=dict(color="rgba(100,149,237,0.6)", width=1, dash="dot")), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["BB_Mid"], name="BB Mid",
                             line=dict(color="rgba(100,149,237,0.4)", width=1)), row=1, col=1)

    # EMA lines
    for span, color in [(9, "#f9a825"), (21, "#e91e63"), (50, "#7e57c2")]:
        fig.add_trace(go.Scatter(x=df.index, y=df[f"EMA_{span}"],
                                 name=f"EMA {span}",
                                 line=dict(color=color, width=1.2)), row=1, col=1)

    # BUY markers
    if not buys.empty:
        fig.add_trace(go.Scatter(
            x=buys.index, y=buys["Low"] * 0.998,
            mode="markers+text",
            marker=dict(symbol="triangle-up", size=14, color="#00e676"),
            text="BUY", textposition="bottom center",
            name="BUY Signal",
        ), row=1, col=1)

    # SELL markers
    if not sells.empty:
        fig.add_trace(go.Scatter(
            x=sells.index, y=sells["High"] * 1.002,
            mode="markers+text",
            marker=dict(symbol="triangle-down", size=14, color="#ff1744"),
            text="SELL", textposition="top center",
            name="SELL Signal",
        ), row=1, col=1)

    # Stop-Loss / Take-Profit horizontal lines for the last signal
    if last["Signal"] in ("BUY", "SELL"):
        sl_color = "rgba(255,82,82,0.8)"
        tp_color = "rgba(0,200,83,0.8)"
        for y_val, label, color in [
            (float(last["StopLoss"]),   "SL", sl_color),
            (float(last["TakeProfit"]), "TP", tp_color),
        ]:
            fig.add_hline(y=y_val, line_dash="dash", line_color=color,
                          annotation_text=f" {label}: {y_val:.4f}",
                          annotation_font_color=color,
                          row=1, col=1)

    # ── 2. RSI ────────────────────────────────────────────────────────────────
    fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI",
                             line=dict(color="#ab47bc", width=1.5)), row=2, col=1)
    for level, color in [(70, "rgba(239,83,80,0.4)"), (30, "rgba(38,166,154,0.4)")]:
        fig.add_hline(y=level, line_dash="dot", line_color=color, row=2, col=1)
    fig.add_hrect(y0=30, y1=70, fillcolor="rgba(200,200,200,0.06)",
                  line_width=0, row=2, col=1)

    # ── 3. MACD ───────────────────────────────────────────────────────────────
    colors_hist = ["#26a69a" if v >= 0 else "#ef5350" for v in df["MACD_Hist"]]
    fig.add_trace(go.Bar(x=df.index, y=df["MACD_Hist"], name="MACD Hist",
                         marker_color=colors_hist, opacity=0.7), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], name="MACD",
                             line=dict(color="#42a5f5", width=1.5)), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD_Signal"], name="Signal",
                             line=dict(color="#ff7043", width=1.5, dash="dot")), row=3, col=1)

    # ── 4. Volume ─────────────────────────────────────────────────────────────
    vol_colors = [
        "#26a69a" if float(df["Close"].iloc[i]) >= float(df["Open"].iloc[i])
        else "#ef5350"
        for i in range(len(df))
    ]
    fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Volume",
                         marker_color=vol_colors, opacity=0.6), row=4, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["Vol_MA20"], name="Vol MA20",
                             line=dict(color="#ffa726", width=1)), row=4, col=1)

    # ── Layout styling ────────────────────────────────────────────────────────
    latest_signal = last["Signal"]
    score = float(last["Score"])
    rsi_val = float(last["RSI"])
    sig_color = {"BUY": "#00e676", "SELL": "#ff1744", "HOLD": "#90a4ae"}.get(latest_signal, "#fff")

    title_text = (
        f"<b>{ticker}</b>  —  ${close_last:.4f}  │  "
        f"Signal: <span style='color:{sig_color}'><b>{latest_signal}</b></span>  "
        f"│ Score: {score:.0f}  │ RSI: {rsi_val:.1f}  │  "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )

    fig.update_layout(
        title=dict(text=title_text, font=dict(size=15)),
        template="plotly_dark",
        height=900,
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1),
        margin=dict(l=60, r=60, t=80, b=40),
        paper_bgcolor="#131722",
        plot_bgcolor="#131722",
    )

    # Y-axis labels
    fig.update_yaxes(title_text="Price (USD)", row=1, col=1)
    fig.update_yaxes(title_text="RSI",         row=2, col=1, range=[0, 100])
    fig.update_yaxes(title_text="MACD",        row=3, col=1)
    fig.update_yaxes(title_text="Volume",      row=4, col=1)

    return fig


# ─── Multi-ticker grid ───────────────────────────────────────────────────────

def build_scanner_table(tickers: list, period="5d", interval="15m") -> go.Figure:
    """Simple signal summary table for multiple tickers."""
    from trading_signals import scan_tickers
    df = scan_tickers(tickers, period=period, interval=interval)

    def color_signal(sig):
        return {"BUY": "#00e676", "SELL": "#ff1744", "HOLD": "#90a4ae"}.get(sig, "#fff")

    cell_colors = [
        ["#1e1e2e"] * len(df),
        ["#1e1e2e"] * len(df),
        [[color_signal(s) for s in df["Signal"].fillna("ERROR")]],
        ["#1e1e2e"] * len(df),
        ["#1e1e2e"] * len(df),
        ["#1e1e2e"] * len(df),
        ["#1e1e2e"] * len(df),
    ]

    fig = go.Figure(data=[go.Table(
        header=dict(
            values=["<b>Ticker</b>", "<b>Price</b>", "<b>Signal</b>",
                    "<b>Score</b>", "<b>RSI</b>", "<b>Stop Loss</b>", "<b>Take Profit</b>"],
            fill_color="#1a1a2e",
            font=dict(color="white", size=13),
            align="center",
        ),
        cells=dict(
            values=[
                df.get("Ticker", []),
                df.get("Price", []).apply(lambda x: f"${x:.4f}" if pd.notna(x) else "N/A"),
                df.get("Signal", []),
                df.get("Score", []),
                df.get("RSI", []),
                df.get("StopLoss", pd.Series()).apply(lambda x: f"${x:.4f}" if pd.notna(x) else "N/A"),
                df.get("TakeProfit", pd.Series()).apply(lambda x: f"${x:.4f}" if pd.notna(x) else "N/A"),
            ],
            fill_color=cell_colors,
            font=dict(color="white", size=12),
            align="center",
            height=30,
        ),
    )])
    fig.update_layout(
        title="<b>Signal Scanner</b>",
        template="plotly_dark",
        paper_bgcolor="#131722",
        height=max(300, 60 + 35 * len(df)),
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return fig


# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ticker   = sys.argv[1] if len(sys.argv) > 1 else "BTC-USD"
    period   = sys.argv[2] if len(sys.argv) > 2 else "5d"
    interval = sys.argv[3] if len(sys.argv) > 3 else "15m"

    print("\n" + "="*60)
    print("  TRADING DASHBOARD")
    print("="*60)

    # Single ticker detailed chart
    fig = build_chart(ticker, period, interval)
    chart_path = f"/tmp/chart_{ticker.replace('-','_')}.html"
    fig.write_html(chart_path)
    print(f"\n  Chart saved → {chart_path}")
    webbrowser.open(f"file://{chart_path}")

    # Scanner table for common assets
    WATCHLIST = ["AAPL", "TSLA", "NVDA", "SPY", "BTC-USD", "ETH-USD", "SOL-USD"]
    print("\n  Building scanner table …")
    table_fig = build_scanner_table(WATCHLIST, period=period, interval=interval)
    table_path = "/tmp/scanner_table.html"
    table_fig.write_html(table_path)
    print(f"  Scanner table saved → {table_path}")
    webbrowser.open(f"file://{table_path}")

    print("\n  Done. Check your browser.\n")
