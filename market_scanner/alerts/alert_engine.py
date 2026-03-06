"""
Alert Engine.

Processes signals and generates alerts based on:
- Score crossing threshold (MIN_ALERT_SCORE)
- Signal type classification (buy/sell/breakout/volume)
- Cooldown deduplication (ALERT_COOLDOWN_SECONDS per symbol+strategy)

Alert delivery pipeline:
  in-app (always) -> webhook (if configured) -> Telegram (if configured)

Designed for extensibility: add new channels by implementing a
delivery function and registering it in DELIVERY_CHANNELS.
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

import requests

from market_scanner.config import (
    ALERT_COOLDOWN_SECONDS,
    ALERT_WEBHOOK_URL,
    MIN_ALERT_SCORE,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)

logger = logging.getLogger(__name__)


# ============================================================
# COOLDOWN TRACKING
# ============================================================

_alert_cooldowns: Dict[str, float] = {}   # key: "symbol:strategy" -> last_alert_ts


def _cooldown_key(symbol: str, strategy: str) -> str:
    return f"{symbol}:{strategy}"


def _is_on_cooldown(symbol: str, strategy: str) -> bool:
    key = _cooldown_key(symbol, strategy)
    last_ts = _alert_cooldowns.get(key, 0)
    return (time.time() - last_ts) < ALERT_COOLDOWN_SECONDS


def _set_cooldown(symbol: str, strategy: str) -> None:
    _alert_cooldowns[_cooldown_key(symbol, strategy)] = time.time()


# ============================================================
# IN-APP ALERT STORE
# ============================================================

_in_app_alerts: List[dict] = []
_MAX_IN_APP = 500


def get_in_app_alerts(limit: int = 100, asset_type: Optional[str] = None) -> List[dict]:
    """Return recent in-app alerts, newest first."""
    alerts = _in_app_alerts[-limit:][::-1]
    if asset_type:
        alerts = [a for a in alerts if a.get("asset_type") == asset_type]
    return alerts


def clear_in_app_alerts() -> None:
    _in_app_alerts.clear()


# ============================================================
# ALERT BUILDING
# ============================================================

def _build_alert(signal: dict, alert_type: str) -> dict:
    """Construct a standardised alert dict from a signal."""
    reasons = signal.get("reasons_dict", {})
    top_reasons = [k for k, v in reasons.items() if v >= 0.7][:3]

    message_parts = [
        f"[{alert_type.upper()}] {signal['symbol']}",
        f"Strategy: {signal.get('strategy_label', signal['strategy'])}",
        f"Score: {signal['score']:.0f}/100 ({signal['score_label']})",
        f"Price: {signal.get('price')}",
        f"Timeframe: {signal['timeframe']}",
    ]

    if signal.get("asset_type") == "crypto" and signal.get("exchange_display"):
        exchanges = signal.get("exchange_display", [])
        if exchanges:
            message_parts.append(f"Venues: {', '.join(exchanges[:3])}")

    if signal.get("asset_type") == "stock":
        if signal.get("options_bias") and signal["options_bias"] != "unavailable":
            message_parts.append(f"Options: {signal['options_bias'].upper()} favored")
        if signal.get("iv_warning"):
            message_parts.append("⚠ IV WARNING: premium may be expensive")

    if top_reasons:
        message_parts.append(f"Reasons: {', '.join(top_reasons)}")

    if signal.get("stop_loss"):
        message_parts.append(f"Stop: {signal['stop_loss']} | TP1: {signal['take_profit_1']}")

    return {
        "symbol":      signal["symbol"],
        "asset_type":  signal.get("asset_type"),
        "timeframe":   signal.get("timeframe"),
        "strategy":    signal.get("strategy"),
        "alert_type":  alert_type,
        "score":       signal["score"],
        "price":       signal.get("price"),
        "message":     "\n".join(message_parts),
        "signal":      signal,
        "created_at":  datetime.now(timezone.utc).isoformat(),
    }


def _classify_alert_type(signal: dict) -> str:
    """Map signal properties to an alert type label."""
    sig_type = signal.get("signal_type", "")
    vol_cond = signal.get("volume_condition", "")
    squeeze  = signal.get("indicators", {}).get("squeeze", False)

    if sig_type in ("strong_buy", "strong_sell"):
        return sig_type
    if vol_cond in ("very_high", "high") and signal["score"] >= 70:
        return "unusual_volume"
    if squeeze:
        return "breakout"
    if sig_type in ("buy", "sell"):
        return sig_type
    return "signal"


# ============================================================
# DELIVERY CHANNELS
# ============================================================

def _deliver_in_app(alert: dict) -> bool:
    """Store alert in in-app buffer."""
    _in_app_alerts.append(alert)
    if len(_in_app_alerts) > _MAX_IN_APP:
        del _in_app_alerts[0]
    return True


def _deliver_webhook(alert: dict) -> bool:
    """POST alert to configured webhook URL."""
    if not ALERT_WEBHOOK_URL:
        return False
    try:
        payload = {
            "symbol":     alert["symbol"],
            "alert_type": alert["alert_type"],
            "score":      alert["score"],
            "price":      alert["price"],
            "message":    alert["message"],
            "timestamp":  alert["created_at"],
        }
        resp = requests.post(ALERT_WEBHOOK_URL, json=payload, timeout=5)
        return resp.status_code < 300
    except Exception as exc:
        logger.warning("Webhook delivery error: %s", exc)
        return False


def _deliver_telegram(alert: dict) -> bool:
    """Send alert via Telegram bot."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        text = alert["message"]
        resp = requests.post(
            url,
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception as exc:
        logger.warning("Telegram delivery error: %s", exc)
        return False


DELIVERY_CHANNELS: Dict[str, Callable] = {
    "in_app":  _deliver_in_app,
    "webhook": _deliver_webhook,
    "telegram": _deliver_telegram,
}


# ============================================================
# MAIN ALERT PROCESSING
# ============================================================

def process_signal(
    signal: dict,
    channels: Optional[List[str]] = None,
    db_session=None,
) -> Optional[dict]:
    """
    Process a signal and fire an alert if it passes all filters.

    Returns the alert dict if fired, None otherwise.
    """
    if channels is None:
        channels = ["in_app", "webhook", "telegram"]

    # Score filter
    if signal.get("score", 0) < MIN_ALERT_SCORE:
        return None

    # Cooldown filter
    symbol   = signal["symbol"]
    strategy = signal["strategy"]
    if _is_on_cooldown(symbol, strategy):
        logger.debug("Alert on cooldown: %s / %s", symbol, strategy)
        return None

    alert_type = _classify_alert_type(signal)
    alert = _build_alert(signal, alert_type)

    # Deliver to all configured channels
    delivered = []
    for channel in channels:
        fn = DELIVERY_CHANNELS.get(channel)
        if fn:
            try:
                success = fn(alert)
                if success:
                    delivered.append(channel)
            except Exception as exc:
                logger.error("Alert delivery error (%s): %s", channel, exc)

    if delivered:
        _set_cooldown(symbol, strategy)
        alert["delivered_channels"] = delivered
        logger.info(
            "ALERT: %s | %s | score=%.0f | via %s",
            symbol, alert_type, signal["score"], delivered
        )

        # Persist to database if session provided
        if db_session is not None:
            _persist_alert(alert, signal, db_session)

        return alert

    return None


def process_signals_batch(
    signals: List[dict],
    channels: Optional[List[str]] = None,
    db_session=None,
) -> List[dict]:
    """Process a batch of signals and return all fired alerts."""
    alerts = []
    for signal in signals:
        alert = process_signal(signal, channels=channels, db_session=db_session)
        if alert:
            alerts.append(alert)
    return alerts


# ============================================================
# DATABASE PERSISTENCE
# ============================================================

def _persist_alert(alert: dict, signal: dict, db_session) -> None:
    """Save alert to database."""
    try:
        from market_scanner.database import Alert, Signal

        # Save signal first
        sig_record = Signal(
            symbol=signal["symbol"],
            asset_type=signal.get("asset_type", ""),
            timeframe=signal.get("timeframe", ""),
            strategy=signal.get("strategy", ""),
            signal_type=signal.get("signal_type", ""),
            score=signal.get("score", 0),
            score_label=signal.get("score_label", ""),
            price=signal.get("price"),
            entry_zone=signal.get("entry_zone"),
            stop_loss=signal.get("stop_loss"),
            take_profit_1=signal.get("take_profit_1"),
            take_profit_2=signal.get("take_profit_2"),
            risk_reward=signal.get("risk_reward"),
            atr_value=signal.get("atr_value"),
            reasons=signal.get("reasons", "{}"),
            exchange_list=signal.get("exchange_list", ""),
            options_bias=signal.get("options_bias"),
            iv_rank=signal.get("iv_rank"),
            sector=signal.get("sector"),
        )
        db_session.add(sig_record)
        db_session.flush()

        # Save alert
        alert_record = Alert(
            signal_id=sig_record.id,
            symbol=alert["symbol"],
            asset_type=alert.get("asset_type", ""),
            timeframe=alert.get("timeframe", ""),
            strategy=alert.get("strategy", ""),
            alert_type=alert["alert_type"],
            score=alert["score"],
            price=alert["price"],
            message=alert["message"],
            delivered=bool(alert.get("delivered_channels")),
            delivery_channels=",".join(alert.get("delivered_channels", [])),
        )
        db_session.add(alert_record)
        db_session.commit()

    except Exception as exc:
        logger.error("DB persist error: %s", exc)
        try:
            db_session.rollback()
        except Exception:
            pass
