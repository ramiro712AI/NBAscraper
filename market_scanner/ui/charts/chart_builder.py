"""
Chart Builder.

Builds professional Plotly candlestick charts with:
- Candlestick / OHLC / Line chart (toggle)
- Overlay indicators: EMA, SMA, VWAP, Bollinger Bands, Keltner Channels, Supertrend, PSAR, Donchian
- Lower panels: RSI, MACD, Volume, ADX, Stochastic, OBV, CMF

All charts are returned as Plotly Figure objects ready to render in Dash.
"""

from typing import Dict, List, Optional

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from market_scanner.indicators.engine import compute_indicators

# Colour palette
COLORS = {
    "bullish":       "#26a69a",
    "bearish":       "#ef5350",
    "ema_9":         "#f59e0b",
    "ema_20":        "#3b82f6",
    "ema_50":        "#8b5cf6",
    "ema_200":       "#ec4899",
    "sma_20":        "#64748b",
    "sma_50":        "#475569",
    "vwap":          "#fbbf24",
    "bb_upper":      "#94a3b8",
    "bb_lower":      "#94a3b8",
    "bb_mid":        "#64748b",
    "kc_upper":      "#6366f1",
    "kc_lower":      "#6366f1",
    "don_upper":     "#0ea5e9",
    "don_lower":     "#0ea5e9",
    "supertrend_bull":"#10b981",
    "supertrend_bear":"#f43f5e",
    "rsi_line":      "#60a5fa",
    "rsi_ob":        "#ef4444",
    "rsi_os":        "#22c55e",
    "macd_line":     "#60a5fa",
    "macd_signal":   "#f97316",
    "macd_hist_bull":"#10b981",
    "macd_hist_bear":"#f43f5e",
    "vol_bull":      "#34d399",
    "vol_bear":      "#f87171",
    "vol_ma":        "#f59e0b",
    "adx":           "#a78bfa",
    "dmi_plus":      "#34d399",
    "dmi_minus":     "#f87171",
    "stoch_k":       "#60a5fa",
    "stoch_d":       "#f97316",
    "obv":           "#818cf8",
    "cmf":           "#2dd4bf",
    "bg":            "#0f172a",
    "grid":          "#1e293b",
    "text":          "#e2e8f0",
}

LAYOUT_TEMPLATE = dict(
    paper_bgcolor=COLORS["bg"],
    plot_bgcolor=COLORS["bg"],
    font=dict(color=COLORS["text"], family="Inter, system-ui, sans-serif", size=11),
    xaxis=dict(
        gridcolor=COLORS["grid"],
        zerolinecolor=COLORS["grid"],
        showgrid=True,
        rangeslider=dict(visible=False),
    ),
    yaxis=dict(gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"]),
    legend=dict(
        bgcolor="rgba(15,23,42,0.8)",
        bordercolor=COLORS["grid"],
        borderwidth=1,
        orientation="h",
        yanchor="bottom",
        y=1.01,
        xanchor="left",
        x=0,
        font=dict(size=10),
    ),
    margin=dict(l=60, r=20, t=40, b=40),
    hovermode="x unified",
)


# ============================================================
# OVERLAY TOGGLES (default active)
# ============================================================

DEFAULT_OVERLAYS = {
    "ema_9": True,
    "ema_20": True,
    "ema_50": True,
    "ema_200": True,
    "vwap": True,
    "bb": True,
    "kc": False,
    "donchian": False,
    "supertrend": False,
    "psar": False,
}

DEFAULT_PANELS = {
    "volume": True,
    "rsi": True,
    "macd": True,
    "adx": False,
    "stochastic": False,
    "obv": False,
    "cmf": False,
}


# ============================================================
# MAIN CHART BUILDER
# ============================================================

def build_chart(
    df: pd.DataFrame,
    symbol: str,
    timeframe: str,
    chart_type: str = "candlestick",   # "candlestick" | "ohlc" | "line" | "heikin_ashi"
    overlays: Optional[Dict] = None,
    panels: Optional[Dict] = None,
    signal: Optional[dict] = None,
    asset_type: str = "crypto",
) -> go.Figure:
    """
    Build a full professional trading chart.

    Parameters
    ----------
    df : pd.DataFrame  — OHLCV data
    symbol : str       — Symbol label
    timeframe : str    — Timeframe label
    chart_type : str   — Chart type
    overlays : dict    — Which overlays to show
    panels : dict      — Which lower panels to show
    signal : dict      — Optional signal dict to annotate on chart
    """
    if df is None or df.empty:
        return _empty_chart(symbol, timeframe)

    ovl = {**DEFAULT_OVERLAYS, **(overlays or {})}
    pnl = {**DEFAULT_PANELS, **(panels or {})}

    # Compute indicators
    df_ind = compute_indicators(df.copy())

    # Determine subplots
    active_panels = [k for k, v in pnl.items() if v]
    n_panels = len(active_panels)
    row_heights = [0.55] + [0.45 / max(n_panels, 1)] * n_panels if n_panels else [1.0]

    specs = [[{"secondary_y": False}]] * (n_panels + 1)
    fig = make_subplots(
        rows=n_panels + 1,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=row_heights,
        specs=specs,
    )

    # --- Main price panel ---
    _add_price_series(fig, df_ind, chart_type, row=1)
    _add_overlays(fig, df_ind, ovl, row=1)

    # --- Signal annotations ---
    if signal:
        _add_signal_annotations(fig, df_ind, signal, row=1)

    # --- Lower panels ---
    for i, panel_name in enumerate(active_panels):
        row = i + 2
        _add_panel(fig, df_ind, panel_name, row=row)
        fig.update_yaxes(
            title_text=panel_name.upper(),
            row=row, col=1,
            gridcolor=COLORS["grid"],
            zerolinecolor=COLORS["grid"],
            title_font=dict(size=9),
        )

    # --- Layout ---
    fig.update_layout(
        title=dict(
            text=f"{symbol} — {timeframe}",
            font=dict(size=14, color=COLORS["text"]),
            x=0.01,
        ),
        **LAYOUT_TEMPLATE,
        height=700 if n_panels >= 2 else 550,
    )

    # Shared x-axis settings
    for r in range(1, n_panels + 2):
        fig.update_xaxes(
            gridcolor=COLORS["grid"],
            zerolinecolor=COLORS["grid"],
            row=r, col=1,
            rangeslider=dict(visible=False),
        )

    return fig


# ============================================================
# PRICE SERIES
# ============================================================

def _add_price_series(fig, df, chart_type, row=1):
    """Add main price candles/line to figure."""
    if chart_type == "candlestick":
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df["open"], high=df["high"],
            low=df["low"],   close=df["close"],
            name="Price",
            increasing_line_color=COLORS["bullish"],
            decreasing_line_color=COLORS["bearish"],
            increasing_fillcolor=COLORS["bullish"],
            decreasing_fillcolor=COLORS["bearish"],
            line=dict(width=1),
            whiskerwidth=0.8,
        ), row=row, col=1)

    elif chart_type == "ohlc":
        fig.add_trace(go.Ohlc(
            x=df.index,
            open=df["open"], high=df["high"],
            low=df["low"],   close=df["close"],
            name="Price",
            increasing_line_color=COLORS["bullish"],
            decreasing_line_color=COLORS["bearish"],
        ), row=row, col=1)

    elif chart_type == "heikin_ashi":
        ha = _compute_heikin_ashi(df)
        fig.add_trace(go.Candlestick(
            x=ha.index,
            open=ha["ha_open"], high=ha["ha_high"],
            low=ha["ha_low"],   close=ha["ha_close"],
            name="HA Price",
            increasing_line_color=COLORS["bullish"],
            decreasing_line_color=COLORS["bearish"],
            increasing_fillcolor=COLORS["bullish"],
            decreasing_fillcolor=COLORS["bearish"],
            line=dict(width=1),
        ), row=row, col=1)

    else:  # line
        fig.add_trace(go.Scatter(
            x=df.index, y=df["close"],
            name="Price",
            line=dict(color=COLORS["ema_20"], width=1.5),
            mode="lines",
        ), row=row, col=1)


def _compute_heikin_ashi(df):
    ha = df.copy()
    ha["ha_close"] = (df["open"] + df["high"] + df["low"] + df["close"]) / 4
    ha["ha_open"]  = ((df["open"].shift(1) + df["close"].shift(1)) / 2).fillna(df["open"])
    ha["ha_high"]  = ha[["high", "ha_open", "ha_close"]].max(axis=1)
    ha["ha_low"]   = ha[["low", "ha_open", "ha_close"]].min(axis=1)
    return ha


# ============================================================
# OVERLAYS
# ============================================================

def _add_overlays(fig, df, ovl, row=1):
    if ovl.get("ema_9") and "ema_9" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["ema_9"], name="EMA 9",
            line=dict(color=COLORS["ema_9"], width=1.2),
            mode="lines", opacity=0.9,
        ), row=row, col=1)

    if ovl.get("ema_20") and "ema_20" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["ema_20"], name="EMA 20",
            line=dict(color=COLORS["ema_20"], width=1.2),
            mode="lines", opacity=0.9,
        ), row=row, col=1)

    if ovl.get("ema_50") and "ema_50" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["ema_50"], name="EMA 50",
            line=dict(color=COLORS["ema_50"], width=1.5),
            mode="lines", opacity=0.9,
        ), row=row, col=1)

    if ovl.get("ema_200") and "ema_200" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["ema_200"], name="EMA 200",
            line=dict(color=COLORS["ema_200"], width=1.8, dash="dash"),
            mode="lines", opacity=0.8,
        ), row=row, col=1)

    if ovl.get("vwap") and "vwap" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["vwap"], name="VWAP",
            line=dict(color=COLORS["vwap"], width=1.5, dash="dot"),
            mode="lines", opacity=0.9,
        ), row=row, col=1)

    # Bollinger Bands (with fill between upper and lower)
    if ovl.get("bb") and all(c in df.columns for c in ["bb_upper", "bb_lower", "bb_mid"]):
        fig.add_trace(go.Scatter(
            x=df.index, y=df["bb_upper"], name="BB Upper",
            line=dict(color=COLORS["bb_upper"], width=0.8, dash="dot"),
            mode="lines", opacity=0.6, showlegend=False,
        ), row=row, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["bb_lower"], name="BB Lower",
            line=dict(color=COLORS["bb_lower"], width=0.8, dash="dot"),
            fill="tonexty",
            fillcolor="rgba(148,163,184,0.05)",
            mode="lines", opacity=0.6,
        ), row=row, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["bb_mid"], name="BB Mid",
            line=dict(color=COLORS["bb_mid"], width=0.8, dash="dot"),
            mode="lines", opacity=0.5, showlegend=False,
        ), row=row, col=1)

    # Keltner Channels
    if ovl.get("kc") and all(c in df.columns for c in ["kc_upper", "kc_lower"]):
        fig.add_trace(go.Scatter(
            x=df.index, y=df["kc_upper"], name="KC Upper",
            line=dict(color=COLORS["kc_upper"], width=0.8, dash="dot"),
            mode="lines", opacity=0.6, showlegend=False,
        ), row=row, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["kc_lower"], name="KC Lower",
            line=dict(color=COLORS["kc_lower"], width=0.8, dash="dot"),
            fill="tonexty",
            fillcolor="rgba(99,102,241,0.05)",
            mode="lines", opacity=0.6,
        ), row=row, col=1)

    # Donchian Channels
    if ovl.get("donchian") and all(c in df.columns for c in ["donchian_upper", "donchian_lower"]):
        fig.add_trace(go.Scatter(
            x=df.index, y=df["donchian_upper"], name="DC Upper",
            line=dict(color=COLORS["don_upper"], width=0.8),
            mode="lines", opacity=0.7,
        ), row=row, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["donchian_lower"], name="DC Lower",
            line=dict(color=COLORS["don_lower"], width=0.8),
            fill="tonexty",
            fillcolor="rgba(14,165,233,0.05)",
            mode="lines", opacity=0.7,
        ), row=row, col=1)

    # Supertrend
    if ovl.get("supertrend") and "supertrend" in df.columns and "supertrend_dir" in df.columns:
        bull_mask = df["supertrend_dir"] == 1
        bear_mask = df["supertrend_dir"] == -1
        if bull_mask.any():
            fig.add_trace(go.Scatter(
                x=df.index[bull_mask], y=df["supertrend"][bull_mask],
                name="Supertrend ↑",
                mode="lines", line=dict(color=COLORS["supertrend_bull"], width=2),
                opacity=0.8,
            ), row=row, col=1)
        if bear_mask.any():
            fig.add_trace(go.Scatter(
                x=df.index[bear_mask], y=df["supertrend"][bear_mask],
                name="Supertrend ↓",
                mode="lines", line=dict(color=COLORS["supertrend_bear"], width=2),
                opacity=0.8,
            ), row=row, col=1)

    # Parabolic SAR
    if ovl.get("psar"):
        for col, label, marker in [
            ("psar_long",  "SAR Long",  "triangle-up"),
            ("psar_short", "SAR Short", "triangle-down"),
        ]:
            if col in df.columns:
                data = df[col].dropna()
                if not data.empty:
                    fig.add_trace(go.Scatter(
                        x=data.index, y=data.values,
                        name=label,
                        mode="markers",
                        marker=dict(symbol=marker, size=5, color=COLORS["bearish" if "short" in col else "bullish"]),
                    ), row=row, col=1)


# ============================================================
# LOWER PANELS
# ============================================================

def _add_panel(fig, df, panel_name, row):
    if panel_name == "volume":
        _add_volume_panel(fig, df, row)
    elif panel_name == "rsi":
        _add_rsi_panel(fig, df, row)
    elif panel_name == "macd":
        _add_macd_panel(fig, df, row)
    elif panel_name == "adx":
        _add_adx_panel(fig, df, row)
    elif panel_name == "stochastic":
        _add_stochastic_panel(fig, df, row)
    elif panel_name == "obv":
        _add_obv_panel(fig, df, row)
    elif panel_name == "cmf":
        _add_cmf_panel(fig, df, row)


def _add_volume_panel(fig, df, row):
    if "volume" not in df.columns:
        return
    colors = [COLORS["vol_bull"] if c >= o else COLORS["vol_bear"]
              for c, o in zip(df["close"], df["open"])]
    fig.add_trace(go.Bar(
        x=df.index, y=df["volume"],
        name="Volume",
        marker_color=colors,
        opacity=0.7,
        showlegend=False,
    ), row=row, col=1)
    if "volume_ma" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["volume_ma"],
            name="Vol MA",
            line=dict(color=COLORS["vol_ma"], width=1.2),
            mode="lines",
        ), row=row, col=1)


def _add_rsi_panel(fig, df, row):
    if "rsi" not in df.columns:
        return
    fig.add_hline(y=70, line_dash="dash", line_color=COLORS["rsi_ob"], opacity=0.5, row=row, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color=COLORS["rsi_os"], opacity=0.5, row=row, col=1)
    fig.add_hline(y=50, line_dash="dot",  line_color=COLORS["grid"],   opacity=0.5, row=row, col=1)
    fig.add_trace(go.Scatter(
        x=df.index, y=df["rsi"], name="RSI",
        line=dict(color=COLORS["rsi_line"], width=1.5),
        mode="lines",
    ), row=row, col=1)
    fig.update_yaxes(range=[0, 100], row=row, col=1)


def _add_macd_panel(fig, df, row):
    if "macd" not in df.columns:
        return
    # Histogram
    if "macd_hist" in df.columns:
        hist_colors = [COLORS["macd_hist_bull"] if v >= 0 else COLORS["macd_hist_bear"]
                       for v in df["macd_hist"].fillna(0)]
        fig.add_trace(go.Bar(
            x=df.index, y=df["macd_hist"], name="MACD Hist",
            marker_color=hist_colors, opacity=0.6,
        ), row=row, col=1)
    fig.add_trace(go.Scatter(
        x=df.index, y=df["macd"], name="MACD",
        line=dict(color=COLORS["macd_line"], width=1.3),
        mode="lines",
    ), row=row, col=1)
    if "macd_signal" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["macd_signal"], name="Signal",
            line=dict(color=COLORS["macd_signal"], width=1.3),
            mode="lines",
        ), row=row, col=1)
    fig.add_hline(y=0, line_dash="dot", line_color=COLORS["grid"], opacity=0.5, row=row, col=1)


def _add_adx_panel(fig, df, row):
    if "adx" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["adx"], name="ADX",
            line=dict(color=COLORS["adx"], width=1.5),
            mode="lines",
        ), row=row, col=1)
    if "dmi_plus" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["dmi_plus"], name="+DI",
            line=dict(color=COLORS["dmi_plus"], width=1),
            mode="lines",
        ), row=row, col=1)
    if "dmi_minus" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["dmi_minus"], name="-DI",
            line=dict(color=COLORS["dmi_minus"], width=1),
            mode="lines",
        ), row=row, col=1)
    fig.add_hline(y=25, line_dash="dash", line_color=COLORS["grid"], opacity=0.5, row=row, col=1)


def _add_stochastic_panel(fig, df, row):
    if "stoch_k" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["stoch_k"], name="Stoch %K",
            line=dict(color=COLORS["stoch_k"], width=1.3),
            mode="lines",
        ), row=row, col=1)
    if "stoch_d" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["stoch_d"], name="Stoch %D",
            line=dict(color=COLORS["stoch_d"], width=1.3),
            mode="lines",
        ), row=row, col=1)
    fig.add_hline(y=80, line_dash="dash", line_color=COLORS["rsi_ob"], opacity=0.5, row=row, col=1)
    fig.add_hline(y=20, line_dash="dash", line_color=COLORS["rsi_os"], opacity=0.5, row=row, col=1)
    fig.update_yaxes(range=[0, 100], row=row, col=1)


def _add_obv_panel(fig, df, row):
    if "obv" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["obv"], name="OBV",
            line=dict(color=COLORS["obv"], width=1.3),
            mode="lines",
        ), row=row, col=1)


def _add_cmf_panel(fig, df, row):
    if "cmf" in df.columns:
        cmf_colors = [COLORS["vol_bull"] if v >= 0 else COLORS["vol_bear"]
                      for v in df["cmf"].fillna(0)]
        fig.add_trace(go.Bar(
            x=df.index, y=df["cmf"], name="CMF",
            marker_color=cmf_colors, opacity=0.7,
        ), row=row, col=1)
        fig.add_hline(y=0, line_dash="dot", line_color=COLORS["grid"], opacity=0.5, row=row, col=1)


# ============================================================
# SIGNAL ANNOTATIONS
# ============================================================

def _add_signal_annotations(fig, df, signal, row=1):
    if not signal or "price" not in signal:
        return

    price = signal["price"]
    sig_type = signal.get("signal_type", "")
    direction = signal.get("direction", "buy")

    color = COLORS["bullish"] if direction == "buy" else COLORS["bearish"]
    symbol_marker = "triangle-up" if direction == "buy" else "triangle-down"
    last_x = df.index[-1] if not df.empty else None

    if last_x is None:
        return

    # Entry arrow
    fig.add_trace(go.Scatter(
        x=[last_x], y=[price],
        mode="markers+text",
        marker=dict(symbol=symbol_marker, size=14, color=color),
        text=[sig_type.upper().replace("_", " ")],
        textposition="top center" if direction == "buy" else "bottom center",
        textfont=dict(size=10, color=color),
        name=sig_type,
        showlegend=False,
    ), row=row, col=1)

    # Stop loss line
    if signal.get("stop_loss"):
        fig.add_hline(
            y=signal["stop_loss"],
            line_dash="dash",
            line_color=COLORS["bearish"],
            opacity=0.5,
            annotation_text=f"SL {signal['stop_loss']}",
            annotation_font_size=9,
            row=row, col=1,
        )

    # TP1
    if signal.get("take_profit_1"):
        fig.add_hline(
            y=signal["take_profit_1"],
            line_dash="dot",
            line_color=COLORS["bullish"],
            opacity=0.5,
            annotation_text=f"TP1 {signal['take_profit_1']}",
            annotation_font_size=9,
            row=row, col=1,
        )


# ============================================================
# EMPTY CHART FALLBACK
# ============================================================

def _empty_chart(symbol: str, timeframe: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        title=f"{symbol} — {timeframe} (No data)",
        **LAYOUT_TEMPLATE,
        height=400,
        annotations=[dict(
            text="No data available",
            x=0.5, y=0.5,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=16, color=COLORS["text"]),
        )],
    )
    return fig
