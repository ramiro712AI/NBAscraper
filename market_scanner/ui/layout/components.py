"""
Reusable Dash layout components.

Each function returns a Dash HTML/DCC component tree.
"""

from typing import Dict, List, Optional

import dash_bootstrap_components as dbc
from dash import dcc, html

# ============================================================
# COLOUR HELPERS
# ============================================================

def _score_badge_color(score: float) -> str:
    if score >= 80: return "danger"
    if score >= 65: return "warning"
    if score >= 50: return "info"
    return "secondary"

def _signal_badge_color(sig_type: str) -> str:
    mapping = {
        "strong_buy":  "success",
        "buy":         "primary",
        "strong_sell": "danger",
        "sell":        "warning",
        "neutral":     "secondary",
        "breakout":    "info",
        "unusual_volume": "warning",
    }
    return mapping.get(sig_type, "secondary")

def _trend_icon(trend: str) -> str:
    icons = {
        "uptrend":   "↑",
        "downtrend": "↓",
        "mixed":     "↔",
        "unknown":   "–",
    }
    return icons.get(trend, "–")

def _regime_badge(regime: str) -> dbc.Badge:
    colors = {"bullish": "success", "bearish": "danger", "neutral": "secondary"}
    return dbc.Badge(regime.upper(), color=colors.get(regime, "secondary"), className="ms-1")


# ============================================================
# MARKET REGIME STRIP
# ============================================================

def market_regime_strip(regime: dict) -> dbc.Alert:
    """Top-of-page market regime indicator."""
    r = regime.get("regime", "neutral")
    trend = regime.get("trend", "sideways")
    spy = regime.get("spy_price")
    e20 = regime.get("ema20")
    e50 = regime.get("ema50")

    color = {"bullish": "success", "bearish": "danger", "neutral": "warning"}.get(r, "secondary")

    return dbc.Alert(
        [
            html.Strong("Market Regime: "),
            _regime_badge(r),
            html.Span(f"  SPY: ${spy}", className="ms-3") if spy else "",
            html.Span(f"  EMA20: {e20}", className="ms-2") if e20 else "",
            html.Span(f"  EMA50: {e50}", className="ms-2") if e50 else "",
            html.Span(f"  Trend: {trend}", className="ms-2"),
        ],
        color=color,
        className="mb-2 py-2 px-3",
        style={"fontSize": "0.85rem"},
    )


# ============================================================
# SCANNER TABLE
# ============================================================

def scanner_table(signals: List[dict], asset_type: str = "all") -> dbc.Table:
    """
    Render the main scanner table with all signal columns.
    """
    if not signals:
        return html.Div("No signals found. Run a scan.", className="text-muted text-center p-4")

    headers = [
        "Symbol", "Type", "Price", "Score", "Signal", "Trend",
        "TF", "Strategy", "Volume", "Volatility",
    ]
    if asset_type in ("crypto", "all"):
        headers.append("Venues")
    if asset_type in ("stock", "all"):
        headers += ["Options Bias", "Sector"]

    rows = []
    for sig in signals:
        if asset_type != "all" and sig.get("asset_type") != asset_type:
            continue

        score = sig.get("score", 0)
        sig_type = sig.get("signal_type", "")

        price = sig.get("price")
        price_str = f"{price:,.4f}" if price and price < 1 else (f"{price:,.2f}" if price else "–")

        row_cells = [
            html.Td(html.Strong(sig["symbol"]), className="text-warning"),
            html.Td(dbc.Badge(sig.get("asset_type", "").upper(), color="dark", className="me-1")),
            html.Td(price_str, className="text-end"),
            html.Td(
                dbc.Badge(f"{score:.0f}", color=_score_badge_color(score)),
                className="text-center",
            ),
            html.Td(
                dbc.Badge(sig_type.replace("_", " ").upper(), color=_signal_badge_color(sig_type)),
                className="text-center",
            ),
            html.Td(f"{_trend_icon(sig.get('trend', 'unknown'))} {sig.get('trend', '–')}"),
            html.Td(sig.get("timeframe", "–"), className="text-center"),
            html.Td(sig.get("strategy_label", sig.get("strategy", "–")), style={"fontSize": "0.8rem"}),
            html.Td(
                dbc.Badge(sig.get("volume_condition", "–"), color="dark"),
                className="text-center",
            ),
            html.Td(
                dbc.Badge(sig.get("volatility_condition", "–"), color="dark"),
                className="text-center",
            ),
        ]

        if asset_type in ("crypto", "all"):
            exchanges = sig.get("exchange_display", [])
            row_cells.append(html.Td(
                html.Span(", ".join(exchanges[:2]) if exchanges else "–", style={"fontSize": "0.75rem"}),
            ))

        if asset_type in ("stock", "all"):
            opt_bias = sig.get("options_bias") or "–"
            iv_warn = " ⚠" if sig.get("iv_warning") else ""
            row_cells.append(html.Td(
                dbc.Badge(opt_bias + iv_warn, color="info" if "call" in opt_bias else "warning" if "put" in opt_bias else "secondary"),
                className="text-center",
            ))
            row_cells.append(html.Td(
                sig.get("sector", "–"),
                style={"fontSize": "0.75rem"},
            ))

        rows.append(html.Tr(row_cells, id={"type": "signal-row", "index": sig["symbol"]}, className="signal-row"))

    return dbc.Table(
        [
            html.Thead(html.Tr([html.Th(h) for h in headers]), className="table-dark"),
            html.Tbody(rows),
        ],
        striped=True,
        hover=True,
        responsive=True,
        size="sm",
        className="table-dark signal-table",
        style={"fontSize": "0.82rem"},
    )


# ============================================================
# SIGNAL EXPLANATION PANEL
# ============================================================

def signal_panel(signal: Optional[dict]) -> html.Div:
    """Detailed breakdown of a single signal."""
    if not signal:
        return html.Div("Select a signal to see details.", className="text-muted p-3")

    score = signal.get("score", 0)
    reasons = signal.get("reasons_dict") or {}

    reason_bars = []
    for rule, conf in sorted(reasons.items(), key=lambda x: -x[1])[:8]:
        pct = int(conf * 100)
        color = "success" if conf >= 0.7 else "warning" if conf >= 0.4 else "danger"
        reason_bars.append(html.Div([
            html.Div([
                html.Span(rule.replace("_", " ").title(), style={"fontSize": "0.78rem"}),
                html.Span(f" {pct}%", className="float-end text-muted", style={"fontSize": "0.78rem"}),
            ]),
            dbc.Progress(value=pct, color=color, className="mb-2", style={"height": "6px"}),
        ]))

    indicators = signal.get("indicators", {})

    return html.Div([
        # Header
        dbc.Row([
            dbc.Col(html.H5(signal["symbol"], className="text-warning mb-0")),
            dbc.Col(
                dbc.Badge(f"{score:.0f}/100", color=_score_badge_color(score), className="fs-6"),
                className="text-end",
            ),
        ], className="mb-2"),

        html.Hr(className="border-secondary my-2"),

        # Key stats grid
        dbc.Row([
            dbc.Col(_kv("Strategy", signal.get("strategy_label", "–")), width=6),
            dbc.Col(_kv("Signal", signal.get("signal_type", "–").replace("_", " ").upper()), width=6),
            dbc.Col(_kv("Timeframe", signal.get("timeframe", "–")), width=6),
            dbc.Col(_kv("Trend", signal.get("trend", "–")), width=6),
            dbc.Col(_kv("Volume", signal.get("volume_condition", "–")), width=6),
            dbc.Col(_kv("Volatility", signal.get("volatility_condition", "–")), width=6),
        ], className="g-1 mb-3"),

        html.Hr(className="border-secondary my-2"),

        # Trade levels
        html.H6("Trade Levels", className="text-secondary"),
        dbc.Row([
            dbc.Col(_kv("Entry", signal.get("entry_zone", "–")), width=12),
            dbc.Col(_kv("Stop Loss", signal.get("stop_loss", "–")), width=6),
            dbc.Col(_kv("TP 1", signal.get("take_profit_1", "–")), width=6),
            dbc.Col(_kv("TP 2", signal.get("take_profit_2", "–")), width=6),
            dbc.Col(_kv("R/R", signal.get("risk_reward", "–")), width=6),
        ], className="g-1 mb-3"),

        html.Hr(className="border-secondary my-2"),

        # Indicator values
        html.H6("Indicators", className="text-secondary"),
        dbc.Row([
            dbc.Col(_kv("RSI", _fmt(indicators.get("rsi"))), width=6),
            dbc.Col(_kv("MACD", _fmt(indicators.get("macd"))), width=6),
            dbc.Col(_kv("ADX", _fmt(indicators.get("adx"))), width=6),
            dbc.Col(_kv("EMA 9", _fmt(indicators.get("ema_9"))), width=6),
            dbc.Col(_kv("EMA 20", _fmt(indicators.get("ema_20"))), width=6),
            dbc.Col(_kv("EMA 50", _fmt(indicators.get("ema_50"))), width=6),
            dbc.Col(_kv("VWAP", _fmt(indicators.get("vwap"))), width=6),
            dbc.Col(_kv("ATR", _fmt(indicators.get("atr"))), width=6),
        ], className="g-1 mb-3"),

        html.Hr(className="border-secondary my-2"),

        # Rule contribution bars
        html.H6("Rule Contributions", className="text-secondary"),
        html.Div(reason_bars),

        # Options context (stocks)
        _options_section(signal) if signal.get("asset_type") == "stock" else html.Div(),

        # Exchange availability (crypto)
        _exchange_section(signal) if signal.get("asset_type") == "crypto" else html.Div(),
    ], className="p-3")


def _kv(label: str, value) -> html.Div:
    return html.Div([
        html.Span(label + ": ", className="text-muted", style={"fontSize": "0.75rem"}),
        html.Span(str(value) if value is not None else "–", style={"fontSize": "0.82rem"}),
    ])


def _fmt(val, decimals=4) -> str:
    if val is None:
        return "–"
    try:
        return f"{float(val):.{decimals}f}"
    except Exception:
        return str(val)


def _options_section(signal: dict) -> html.Div:
    opt_bias = signal.get("options_bias")
    iv_warn  = signal.get("iv_warning", False)
    iv_rank  = signal.get("iv_rank")
    sector   = signal.get("sector")

    if not opt_bias or opt_bias == "unavailable":
        return html.Div()

    color = "success" if "call" in str(opt_bias) else "danger" if "put" in str(opt_bias) else "secondary"

    return html.Div([
        html.Hr(className="border-secondary my-2"),
        html.H6("Options Context", className="text-secondary"),
        dbc.Row([
            dbc.Col([
                html.Span("Bias: ", className="text-muted", style={"fontSize": "0.75rem"}),
                dbc.Badge(opt_bias.upper(), color=color),
            ], width=6),
            dbc.Col(_kv("IV Rank", f"{iv_rank:.0f}%" if iv_rank else "–"), width=6),
            dbc.Col(_kv("Sector", sector or "–"), width=12),
        ], className="g-1"),
        dbc.Alert(
            "⚠ IV is elevated — premium buying is expensive. Consider spreads.",
            color="warning", className="mt-2 py-1 px-2", style={"fontSize": "0.75rem"},
        ) if iv_warn else html.Div(),
    ])


def _exchange_section(signal: dict) -> html.Div:
    exchanges = signal.get("exchange_display", [])
    if not exchanges:
        return html.Div()

    return html.Div([
        html.Hr(className="border-secondary my-2"),
        html.H6("Tradable On", className="text-secondary"),
        html.Div([
            dbc.Badge(ex, color="primary", className="me-1 mb-1")
            for ex in exchanges
        ]),
    ])


# ============================================================
# ALERT PANEL
# ============================================================

def alert_panel(alerts: List[dict]) -> html.Div:
    if not alerts:
        return html.Div("No active alerts.", className="text-muted p-3")

    items = []
    for alert in alerts[:20]:
        at = alert.get("alert_type", "signal")
        score = alert.get("score", 0)
        color = _signal_badge_color(at)
        items.append(
            dbc.ListGroupItem([
                dbc.Row([
                    dbc.Col([
                        html.Strong(alert["symbol"], className="text-warning"),
                        dbc.Badge(at.replace("_", " ").upper(), color=color, className="ms-2"),
                    ], width=8),
                    dbc.Col(
                        dbc.Badge(f"{score:.0f}", color=_score_badge_color(score)),
                        width=4, className="text-end",
                    ),
                ]),
                html.Small(
                    f"{alert.get('strategy', '')} | {alert.get('timeframe', '')} | ${alert.get('price', '–')}",
                    className="text-muted",
                ),
                html.Br(),
                html.Small(alert.get("created_at", "")[:19], className="text-muted"),
            ],
            className="bg-dark text-light border-secondary py-2",
        ))

    return dbc.ListGroup(items, flush=True)


# ============================================================
# STRATEGY SELECTOR
# ============================================================

def strategy_selector(selected: str = "all") -> dcc.Dropdown:
    from market_scanner.config import STRATEGY_PRESETS
    options = [{"label": "All Strategies", "value": "all"}] + [
        {"label": preset.name, "value": key}
        for key, preset in STRATEGY_PRESETS.items()
    ]
    return dcc.Dropdown(
        id="strategy-selector",
        options=options,
        value=selected,
        clearable=False,
        style={"fontSize": "0.85rem"},
        className="dash-dropdown-dark",
    )


def timeframe_selector(selected: str = "1h") -> dcc.Dropdown:
    from market_scanner.config import TIMEFRAMES
    options = [{"label": label, "value": key} for key, label in TIMEFRAMES.items()]
    return dcc.Dropdown(
        id="timeframe-selector",
        options=options,
        value=selected,
        clearable=False,
        style={"fontSize": "0.85rem"},
        className="dash-dropdown-dark",
    )


def asset_type_tabs() -> dbc.Tabs:
    return dbc.Tabs(
        id="asset-type-tabs",
        active_tab="crypto",
        children=[
            dbc.Tab(label="Crypto", tab_id="crypto"),
            dbc.Tab(label="Stocks + Options", tab_id="stock"),
            dbc.Tab(label="All", tab_id="all"),
        ],
        className="mb-2",
    )
