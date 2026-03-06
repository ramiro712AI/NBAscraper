"""
Main Dash Application.

Professional multi-asset market scanner dashboard.

Layout:
  - Top bar: Market regime strip + controls
  - Left: Scanner table (crypto / stock / all)
  - Right: Chart panel + Signal explanation panel
  - Bottom: Alert panel

Scanning is triggered manually or via auto-refresh interval.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback_context, dcc, html
from dash.exceptions import PreventUpdate

from market_scanner.alerts.alert_engine import get_in_app_alerts, process_signals_batch
from market_scanner.config import (
    DEFAULT_CRYPTO_SYMBOLS,
    DEFAULT_STOCK_SYMBOLS,
    STRATEGY_PRESETS,
    TIMEFRAMES,
)
from market_scanner.data import stock_data
from market_scanner.scanner.scanner import scan_crypto_universe, scan_stock_universe
from market_scanner.ui.charts.chart_builder import build_chart
from market_scanner.ui.layout.components import (
    alert_panel,
    asset_type_tabs,
    market_regime_strip,
    scanner_table,
    signal_panel,
    strategy_selector,
    timeframe_selector,
)

logger = logging.getLogger(__name__)

# ============================================================
# APP INIT
# ============================================================

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.CYBORG,
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap",
    ],
    title="Market Scanner Pro",
    suppress_callback_exceptions=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server   # For production WSGI deployment

# ============================================================
# GLOBAL STATE (simple in-process store for MVP)
# ============================================================

_signal_store: Dict = {
    "crypto": [],
    "stocks": [],
    "last_scan": None,
    "regime": {},
}


# ============================================================
# LAYOUT
# ============================================================

def build_layout():
    return dbc.Container(
        fluid=True,
        className="px-3 py-2",
        style={"backgroundColor": "#0f172a", "minHeight": "100vh"},
        children=[
            # Hidden stores
            dcc.Store(id="signal-store", data={}),
            dcc.Store(id="selected-signal-store", data=None),
            dcc.Interval(id="auto-refresh", interval=60_000, n_intervals=0, disabled=True),

            # ---- Header ----
            dbc.Row([
                dbc.Col([
                    html.H4(
                        [html.Span("📡 ", className="me-1"), "Market Scanner Pro"],
                        className="text-warning mb-0",
                        style={"fontFamily": "Inter", "fontWeight": 600},
                    ),
                    html.Small("Crypto + Stocks | Multi-strategy | Real-time", className="text-muted"),
                ], width=6),
                dbc.Col([
                    dbc.Row([
                        dbc.Col(html.Small("Last scan: ", className="text-muted"), width="auto"),
                        dbc.Col(html.Small(id="last-scan-time", children="—", className="text-secondary"), width="auto"),
                        dbc.Col(
                            dbc.Button("⟳ Scan Now", id="scan-btn", color="success", size="sm", className="ms-2"),
                            width="auto",
                        ),
                        dbc.Col(
                            dbc.Button("Auto", id="auto-btn", color="outline-secondary", size="sm", className="ms-1"),
                            width="auto",
                        ),
                    ], className="align-items-center justify-content-end"),
                ], width=6),
            ], className="mb-2 align-items-center"),

            # ---- Regime strip ----
            html.Div(id="regime-strip"),

            # ---- Controls ----
            dbc.Row([
                dbc.Col([
                    html.Label("Asset Type", className="text-muted small"),
                    asset_type_tabs(),
                ], width=3),
                dbc.Col([
                    html.Label("Timeframe", className="text-muted small"),
                    timeframe_selector("1h"),
                ], width=2),
                dbc.Col([
                    html.Label("Strategy", className="text-muted small"),
                    strategy_selector("all"),
                ], width=3),
                dbc.Col([
                    html.Label("Chart Type", className="text-muted small"),
                    dcc.Dropdown(
                        id="chart-type-selector",
                        options=[
                            {"label": "Candlestick", "value": "candlestick"},
                            {"label": "OHLC", "value": "ohlc"},
                            {"label": "Heikin Ashi", "value": "heikin_ashi"},
                            {"label": "Line", "value": "line"},
                        ],
                        value="candlestick",
                        clearable=False,
                        style={"fontSize": "0.85rem"},
                    ),
                ], width=2),
                dbc.Col([
                    html.Label("Min Score", className="text-muted small"),
                    dcc.Slider(
                        id="min-score-slider",
                        min=0, max=100, step=5,
                        value=50,
                        marks={0: "0", 50: "50", 80: "80", 100: "100"},
                        tooltip={"placement": "bottom"},
                    ),
                ], width=2),
            ], className="mb-3 g-2"),

            # ---- Overlay toggles ----
            dbc.Row([
                dbc.Col([
                    html.Small("Overlays: ", className="text-muted me-2"),
                    dbc.Checklist(
                        id="overlay-toggles",
                        options=[
                            {"label": "EMA 9", "value": "ema_9"},
                            {"label": "EMA 20", "value": "ema_20"},
                            {"label": "EMA 50", "value": "ema_50"},
                            {"label": "EMA 200", "value": "ema_200"},
                            {"label": "VWAP", "value": "vwap"},
                            {"label": "BB", "value": "bb"},
                            {"label": "KC", "value": "kc"},
                            {"label": "Donchian", "value": "donchian"},
                            {"label": "Supertrend", "value": "supertrend"},
                            {"label": "SAR", "value": "psar"},
                        ],
                        value=["ema_9", "ema_20", "ema_50", "ema_200", "vwap", "bb"],
                        inline=True,
                        style={"fontSize": "0.78rem"},
                        inputClassName="me-1",
                        labelClassName="me-3 text-light",
                    ),
                ]),
            ], className="mb-2"),
            dbc.Row([
                dbc.Col([
                    html.Small("Panels: ", className="text-muted me-2"),
                    dbc.Checklist(
                        id="panel-toggles",
                        options=[
                            {"label": "Volume", "value": "volume"},
                            {"label": "RSI", "value": "rsi"},
                            {"label": "MACD", "value": "macd"},
                            {"label": "ADX", "value": "adx"},
                            {"label": "Stochastic", "value": "stochastic"},
                            {"label": "OBV", "value": "obv"},
                            {"label": "CMF", "value": "cmf"},
                        ],
                        value=["volume", "rsi", "macd"],
                        inline=True,
                        style={"fontSize": "0.78rem"},
                        inputClassName="me-1",
                        labelClassName="me-3 text-light",
                    ),
                ]),
            ], className="mb-3"),

            # ---- Loading spinner ----
            dbc.Row([
                dbc.Col(
                    dbc.Spinner(
                        html.Div(id="scan-status", className="text-success small"),
                        color="success",
                        size="sm",
                    ),
                ),
            ], className="mb-2"),

            # ---- Main content ----
            dbc.Row([
                # LEFT: Scanner table
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(
                            dbc.Row([
                                dbc.Col(html.Strong("Scanner", className="text-warning"), width=6),
                                dbc.Col(html.Small(id="signal-count", className="text-muted"), width=6, className="text-end"),
                            ])
                        ),
                        dbc.CardBody(
                            html.Div(id="scanner-table", style={"overflowX": "auto", "overflowY": "auto", "maxHeight": "480px"}),
                            className="p-1",
                        ),
                    ], className="border-secondary"),
                ], width=7),

                # RIGHT: Signal detail panel
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.Strong("Signal Details", className="text-warning")),
                        dbc.CardBody(
                            html.Div(id="signal-detail-panel"),
                            className="p-0",
                            style={"overflowY": "auto", "maxHeight": "480px"},
                        ),
                    ], className="border-secondary"),
                ], width=5),
            ], className="mb-3"),

            # ---- Chart ----
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(
                            dbc.Row([
                                dbc.Col(html.Strong(id="chart-title", children="Select a signal to view chart", className="text-warning")),
                                dbc.Col(
                                    dbc.ButtonGroup([
                                        dbc.Button("1m", id="tf-1m",  size="sm", color="outline-secondary"),
                                        dbc.Button("5m", id="tf-5m",  size="sm", color="outline-secondary"),
                                        dbc.Button("15m",id="tf-15m", size="sm", color="outline-secondary"),
                                        dbc.Button("1h", id="tf-1h",  size="sm", color="outline-secondary"),
                                        dbc.Button("4h", id="tf-4h",  size="sm", color="outline-secondary"),
                                        dbc.Button("1D", id="tf-1d",  size="sm", color="outline-secondary"),
                                    ], size="sm"),
                                    className="text-end",
                                ),
                            ], align="center"),
                        ),
                        dbc.CardBody(
                            dcc.Graph(
                                id="main-chart",
                                config={"displayModeBar": True, "scrollZoom": True},
                                style={"height": "650px"},
                            ),
                            className="p-1",
                        ),
                    ], className="border-secondary"),
                ], width=12),
            ], className="mb-3"),

            # ---- Bottom: Alerts ----
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(
                            dbc.Row([
                                dbc.Col(html.Strong("Alerts", className="text-warning"), width=6),
                                dbc.Col(
                                    dbc.Button("Clear", id="clear-alerts-btn", size="sm", color="outline-danger"),
                                    width=6, className="text-end",
                                ),
                            ])
                        ),
                        dbc.CardBody(
                            html.Div(id="alert-panel", style={"maxHeight": "300px", "overflowY": "auto"}),
                            className="p-1",
                        ),
                    ], className="border-secondary"),
                ], width=12),
            ]),

            # Bottom padding
            html.Div(style={"height": "40px"}),
        ],
    )


app.layout = build_layout()


# ============================================================
# CALLBACKS
# ============================================================

@app.callback(
    Output("signal-store", "data"),
    Output("scan-status", "children"),
    Output("last-scan-time", "children"),
    Output("regime-strip", "children"),
    Input("scan-btn", "n_clicks"),
    Input("auto-refresh", "n_intervals"),
    State("asset-type-tabs", "active_tab"),
    State("timeframe-selector", "value"),
    State("strategy-selector", "value"),
    prevent_initial_call=True,
)
def run_scan(n_clicks, n_intervals, asset_tab, timeframe, strategy):
    """Run the market scanner and update signal store."""
    global _signal_store

    strategies = None if strategy == "all" else [strategy]

    try:
        crypto_signals = []
        stock_signals  = []

        if asset_tab in ("crypto", "all"):
            crypto_signals = scan_crypto_universe(
                timeframe=timeframe or "1h",
                strategies=strategies,
                max_workers=4,
            )

        if asset_tab in ("stock", "all"):
            stock_signals = scan_stock_universe(
                timeframe=timeframe or "1d",
                strategies=strategies,
                max_workers=3,
                fetch_options=(timeframe in ("1d", "4h") or timeframe is None),
            )

        # Fire alerts for new signals
        all_signals = crypto_signals + stock_signals
        process_signals_batch(all_signals)

        regime = stock_data.fetch_spy_regime(timeframe="1d")

        _signal_store = {
            "crypto": crypto_signals,
            "stocks": stock_signals,
            "last_scan": datetime.now(timezone.utc).isoformat(),
            "regime": regime,
        }

        total = len(crypto_signals) + len(stock_signals)
        timestamp = datetime.now().strftime("%H:%M:%S")
        status = f"✓ {total} signals found ({len(crypto_signals)} crypto, {len(stock_signals)} stocks)"
        regime_strip = market_regime_strip(regime)

        return _signal_store, status, timestamp, regime_strip

    except Exception as exc:
        logger.error("Scan error: %s", exc)
        return dash.no_update, f"Error: {exc}", dash.no_update, dash.no_update


@app.callback(
    Output("scanner-table", "children"),
    Output("signal-count", "children"),
    Input("signal-store", "data"),
    Input("asset-type-tabs", "active_tab"),
    Input("min-score-slider", "value"),
)
def update_scanner_table(store_data, asset_tab, min_score):
    """Re-render scanner table when signals or filters change."""
    if not store_data:
        return html.Div("Run a scan to see signals.", className="text-muted p-3"), ""

    crypto = store_data.get("crypto", [])
    stocks = store_data.get("stocks", [])
    all_sigs = crypto + stocks

    # Filter by asset type
    if asset_tab == "crypto":
        signals = [s for s in crypto if s.get("score", 0) >= min_score]
    elif asset_tab == "stock":
        signals = [s for s in stocks if s.get("score", 0) >= min_score]
    else:
        signals = [s for s in all_sigs if s.get("score", 0) >= min_score]

    table = scanner_table(signals, asset_type=asset_tab)
    count = f"{len(signals)} signals"
    return table, count


@app.callback(
    Output("selected-signal-store", "data"),
    Input({"type": "signal-row", "index": dash.ALL}, "n_clicks"),
    State("signal-store", "data"),
    prevent_initial_call=True,
)
def select_signal(n_clicks_list, store_data):
    """Store the selected signal when a row is clicked."""
    if not any(n_clicks_list):
        raise PreventUpdate

    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate

    triggered_id = ctx.triggered[0]["prop_id"]
    try:
        id_dict = json.loads(triggered_id.split(".")[0])
        symbol = id_dict.get("index")
    except Exception:
        raise PreventUpdate

    # Find the signal in the store
    all_sigs = store_data.get("crypto", []) + store_data.get("stocks", [])
    for sig in all_sigs:
        if sig["symbol"] == symbol:
            return sig

    raise PreventUpdate


@app.callback(
    Output("signal-detail-panel", "children"),
    Input("selected-signal-store", "data"),
)
def update_signal_panel(selected_signal):
    return signal_panel(selected_signal)


@app.callback(
    Output("main-chart", "figure"),
    Output("chart-title", "children"),
    Input("selected-signal-store", "data"),
    Input("overlay-toggles", "value"),
    Input("panel-toggles", "value"),
    Input("chart-type-selector", "value"),
    Input("tf-1m", "n_clicks"),
    Input("tf-5m", "n_clicks"),
    Input("tf-15m", "n_clicks"),
    Input("tf-1h", "n_clicks"),
    Input("tf-4h", "n_clicks"),
    Input("tf-1d", "n_clicks"),
    prevent_initial_call=True,
)
def update_chart(
    selected_signal, overlay_list, panel_list, chart_type,
    n1m, n5m, n15m, n1h, n4h, n1d,
):
    """Render the main chart for the selected signal."""
    if not selected_signal:
        raise PreventUpdate

    ctx = callback_context

    # Determine timeframe from button clicks
    tf_map = {"tf-1m": "1m", "tf-5m": "5m", "tf-15m": "15m",
               "tf-1h": "1h", "tf-4h": "4h", "tf-1d": "1d"}
    timeframe = selected_signal.get("timeframe", "1h")
    if ctx.triggered:
        btn_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if btn_id in tf_map:
            timeframe = tf_map[btn_id]

    symbol    = selected_signal["symbol"]
    asset_type = selected_signal.get("asset_type", "crypto")

    # Overlays dict
    all_overlay_keys = ["ema_9", "ema_20", "ema_50", "ema_200", "vwap", "bb", "kc", "donchian", "supertrend", "psar"]
    overlays = {k: (k in (overlay_list or [])) for k in all_overlay_keys}

    # Panels dict
    all_panel_keys = ["volume", "rsi", "macd", "adx", "stochastic", "obv", "cmf"]
    panels = {k: (k in (panel_list or [])) for k in all_panel_keys}

    try:
        if asset_type == "crypto":
            from market_scanner.data.crypto_data import fetch_ohlcv_multi_exchange
            df, _ = fetch_ohlcv_multi_exchange(symbol, timeframe=timeframe)
        else:
            from market_scanner.data.stock_data import fetch_ohlcv
            df = fetch_ohlcv(symbol, timeframe=timeframe)

        fig = build_chart(
            df=df,
            symbol=symbol,
            timeframe=timeframe,
            chart_type=chart_type or "candlestick",
            overlays=overlays,
            panels=panels,
            signal=selected_signal,
            asset_type=asset_type,
        )
        title = f"{symbol} — {timeframe} | {selected_signal.get('strategy_label', '')} | Score: {selected_signal.get('score', 0):.0f}"
        return fig, title

    except Exception as exc:
        logger.error("Chart error: %s", exc)
        from market_scanner.ui.charts.chart_builder import _empty_chart
        return _empty_chart(symbol, timeframe), symbol


@app.callback(
    Output("alert-panel", "children"),
    Input("signal-store", "data"),
    Input("clear-alerts-btn", "n_clicks"),
)
def update_alert_panel(store_data, clear_clicks):
    ctx = callback_context
    if ctx.triggered:
        triggered = ctx.triggered[0]["prop_id"]
        if "clear-alerts-btn" in triggered:
            from market_scanner.alerts.alert_engine import clear_in_app_alerts
            clear_in_app_alerts()
            return alert_panel([])

    alerts = get_in_app_alerts(limit=50)
    return alert_panel(alerts)


@app.callback(
    Output("auto-refresh", "disabled"),
    Output("auto-btn", "color"),
    Input("auto-btn", "n_clicks"),
    State("auto-refresh", "disabled"),
    prevent_initial_call=True,
)
def toggle_auto_refresh(n_clicks, currently_disabled):
    if currently_disabled:
        return False, "success"   # Enable auto-refresh
    else:
        return True, "outline-secondary"  # Disable


# ============================================================
# CUSTOM CSS
# ============================================================

app.index_string = '''
<!DOCTYPE html>
<html>
<head>
    {%metas%}
    <title>{%title%}</title>
    {%favicon%}
    {%css%}
    <style>
        body { background-color: #0f172a !important; font-family: 'Inter', system-ui, sans-serif; }
        .signal-row { cursor: pointer; }
        .signal-row:hover { background-color: rgba(255,255,255,0.05) !important; }
        .signal-table td, .signal-table th { vertical-align: middle !important; white-space: nowrap; }
        .dash-dropdown-dark .Select-control { background-color: #1e293b !important; border-color: #334155; }
        .dash-dropdown-dark .Select-value-label { color: #e2e8f0 !important; }
        .card { background-color: #1e293b !important; }
        .card-header { background-color: #0f172a !important; border-bottom: 1px solid #334155 !important; }
        .list-group-item { border-color: #334155 !important; }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #0f172a; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
        .nav-tabs .nav-link { color: #94a3b8 !important; border-color: #334155 !important; background-color: transparent !important; }
        .nav-tabs .nav-link.active { color: #f59e0b !important; border-bottom-color: #1e293b !important; background-color: #1e293b !important; }
    </style>
</head>
<body>
    {%app_entry%}
    <footer>
        {%config%}
        {%scripts%}
        {%renderer%}
    </footer>
</body>
</html>
'''
