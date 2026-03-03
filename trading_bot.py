"""
Automated Trading Bot (Paper Trading / Signal-Only Mode)
=========================================================
This bot runs on a schedule, scans your watchlist, and:
  1. Generates buy/sell signals every N minutes
  2. Manages open positions (entry, stop-loss, take-profit)
  3. Logs all trades to a CSV file
  4. Prints a live summary to the terminal
  5. (Optional) Sends alerts — extend the notify() function
     to add Telegram, email, or Discord notifications.

⚠️  This is PAPER TRADING mode by default — no real money moves.
    To connect to a real broker API (Alpaca, Binance, Kraken, etc.)
    fill in the broker section at the bottom of this file.

Usage:
    python trading_bot.py              # start with default config
    python trading_bot.py --once       # run one scan and exit
"""

import os
import sys
import csv
import time
import argparse
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from trading_signals import fetch_data, add_indicators, generate_signals, risk_levels

# ─── Configuration ────────────────────────────────────────────────────────────

@dataclass
class BotConfig:
    # Assets to watch
    watchlist: List[str] = field(default_factory=lambda: [
        "AAPL", "TSLA", "NVDA", "MSFT",        # stocks
        "BTC-USD", "ETH-USD", "SOL-USD",        # crypto
    ])
    interval_minutes: int   = 15        # how often to scan (must match data interval)
    data_period:      str   = "5d"      # history window for indicators
    data_interval:    str   = "15m"     # candle size (1m/5m/15m/1h/1d)

    # Risk management
    capital_per_trade: float = 100.0    # USD per position (paper)
    max_open_trades:   int   = 5        # max simultaneous positions
    min_score:         float = 60.0     # minimum signal score to act

    # Logging
    log_file: str = "trades_log.csv"


# ─── Position tracker ────────────────────────────────────────────────────────

@dataclass
class Position:
    ticker:      str
    side:        str          # "BUY" or "SELL"
    entry_price: float
    quantity:    float
    stop_loss:   float
    take_profit: float
    opened_at:   str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    pnl:         float = 0.0
    status:      str = "OPEN"  # OPEN | CLOSED_TP | CLOSED_SL | CLOSED_SIGNAL

    @property
    def cost(self):
        return self.entry_price * self.quantity


class Portfolio:
    def __init__(self, config: BotConfig):
        self.config    = config
        self.positions: Dict[str, Position] = {}
        self.closed:    List[Position]      = []
        self.cash       = 10_000.0          # starting paper cash
        self.initial_cash = self.cash

    # ── Open a new position ───────────────────────────────────────────────────
    def open_position(self, ticker: str, side: str, price: float,
                      stop_loss: float, take_profit: float):
        if ticker in self.positions:
            return  # already in trade
        if len(self.positions) >= self.config.max_open_trades:
            print(f"    [BOT] Max trades reached — skipping {ticker}")
            return
        quantity = round(self.config.capital_per_trade / price, 6)
        if quantity <= 0:
            return
        pos = Position(
            ticker=ticker, side=side,
            entry_price=price, quantity=quantity,
            stop_loss=stop_loss, take_profit=take_profit,
        )
        self.positions[ticker] = pos
        self.cash -= pos.cost
        print(f"    [BOT] OPENED {side:4s} {ticker:10s}  "
              f"@ ${price:.4f}  qty={quantity:.6f}  "
              f"SL=${stop_loss:.4f}  TP=${take_profit:.4f}")
        self._log_trade(pos, "OPEN", price)

    # ── Close a position ──────────────────────────────────────────────────────
    def close_position(self, ticker: str, price: float, reason: str):
        if ticker not in self.positions:
            return
        pos = self.positions.pop(ticker)
        pos.status = reason
        if pos.side == "BUY":
            pos.pnl = (price - pos.entry_price) * pos.quantity
        else:
            pos.pnl = (pos.entry_price - price) * pos.quantity
        self.cash += price * pos.quantity
        self.closed.append(pos)
        icon = "✅" if pos.pnl >= 0 else "❌"
        print(f"    [BOT] {icon} CLOSED {ticker:10s}  "
              f"@ ${price:.4f}  PnL=${pos.pnl:+.2f}  [{reason}]")
        self._log_trade(pos, "CLOSE", price)

    # ── Check stops / targets for open positions ──────────────────────────────
    def check_exits(self, ticker: str, current_price: float):
        if ticker not in self.positions:
            return
        pos = self.positions[ticker]
        if pos.side == "BUY":
            if current_price <= pos.stop_loss:
                self.close_position(ticker, current_price, "CLOSED_SL")
            elif current_price >= pos.take_profit:
                self.close_position(ticker, current_price, "CLOSED_TP")
        else:  # SHORT
            if current_price >= pos.stop_loss:
                self.close_position(ticker, current_price, "CLOSED_SL")
            elif current_price <= pos.take_profit:
                self.close_position(ticker, current_price, "CLOSED_TP")

    # ── Update PnL display ────────────────────────────────────────────────────
    def update_unrealized(self, ticker: str, current_price: float):
        if ticker not in self.positions:
            return
        pos = self.positions[ticker]
        if pos.side == "BUY":
            pos.pnl = (current_price - pos.entry_price) * pos.quantity
        else:
            pos.pnl = (pos.entry_price - current_price) * pos.quantity

    # ── Portfolio summary ─────────────────────────────────────────────────────
    def summary(self) -> str:
        realized   = sum(p.pnl for p in self.closed)
        unrealized = sum(p.pnl for p in self.positions.values())
        total_pnl  = realized + unrealized
        equity     = self.cash + sum(p.cost for p in self.positions.values())
        lines = [
            f"\n  {'─'*58}",
            f"  PORTFOLIO SUMMARY  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"  {'─'*58}",
            f"  Cash:       ${self.cash:>12,.2f}",
            f"  Equity:     ${equity:>12,.2f}",
            f"  Realized:   ${realized:>+12,.2f}",
            f"  Unrealized: ${unrealized:>+12,.2f}",
            f"  Total PnL:  ${total_pnl:>+12,.2f}  "
            f"({'+'if total_pnl>=0 else ''}{total_pnl/self.initial_cash*100:.2f}%)",
            f"  Open trades: {len(self.positions)} / {self.config.max_open_trades}",
        ]
        if self.positions:
            lines.append(f"  {'─'*58}")
            for t, p in self.positions.items():
                lines.append(f"   {p.side:4s} {t:10s}  entry=${p.entry_price:.4f}  "
                             f"PnL=${p.pnl:+.2f}")
        lines.append(f"  {'─'*58}\n")
        return "\n".join(lines)

    # ── CSV logging ───────────────────────────────────────────────────────────
    def _log_trade(self, pos: Position, action: str, price: float):
        file_exists = os.path.exists(self.config.log_file)
        with open(self.config.log_file, "a", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow([
                    "timestamp", "action", "ticker", "side",
                    "price", "quantity", "stop_loss", "take_profit",
                    "pnl", "status",
                ])
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                action, pos.ticker, pos.side,
                round(price, 6), round(pos.quantity, 6),
                round(pos.stop_loss, 6), round(pos.take_profit, 6),
                round(pos.pnl, 4), pos.status,
            ])


# ─── Notification hook (extend as needed) ────────────────────────────────────

def notify(message: str):
    """
    Send an alert. Add your notification channel here:
      - Telegram: use python-telegram-bot
      - Discord:  use a webhook URL
      - Email:    use smtplib
    """
    # Example Telegram (fill in your token + chat_id):
    # import requests
    # TOKEN   = "YOUR_BOT_TOKEN"
    # CHAT_ID = "YOUR_CHAT_ID"
    # requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
    #               data={"chat_id": CHAT_ID, "text": message})
    print(f"  [NOTIFY] {message}")


# ─── Main scan loop ──────────────────────────────────────────────────────────

def run_scan(portfolio: Portfolio, config: BotConfig):
    print(f"\n  === SCAN {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    for ticker in config.watchlist:
        try:
            df = fetch_data(ticker, period=config.data_period,
                            interval=config.data_interval)
            df = add_indicators(df)
            df = generate_signals(df)
            df = risk_levels(df)

            last  = df.iloc[-1]
            price = float(last["Close"])
            sig   = last["Signal"]
            score = float(last["Score"])
            sl    = float(last["StopLoss"])
            tp    = float(last["TakeProfit"])

            # Update unrealized PnL and check exits
            portfolio.update_unrealized(ticker, price)
            portfolio.check_exits(ticker, price)

            icon = {"BUY": "🟢", "SELL": "🔴", "HOLD": "⚪"}.get(sig, "?")
            print(f"  {icon} {ticker:10s} ${price:<12.4f} "
                  f"Signal={sig:4s}  Score={score:>6.1f}")

            # Decide entry
            if sig == "BUY" and score >= config.min_score:
                portfolio.open_position(ticker, "BUY", price, sl, tp)
                notify(f"BUY signal: {ticker} @ ${price:.4f}  SL={sl:.4f}  TP={tp:.4f}")

            elif sig == "SELL" and score <= -config.min_score:
                # Close any existing long before going short
                if ticker in portfolio.positions:
                    portfolio.close_position(ticker, price, "CLOSED_SIGNAL")
                # Uncomment to enable short selling:
                # portfolio.open_position(ticker, "SELL", price, sl, tp)
                notify(f"SELL signal: {ticker} @ ${price:.4f}")

        except Exception as e:
            print(f"  [ERROR] {ticker}: {e}")

    print(portfolio.summary())


# ─── Entry point ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Paper Trading Bot")
    parser.add_argument("--once", action="store_true",
                        help="Run one scan and exit (no loop)")
    parser.add_argument("--interval", type=int, default=None,
                        help="Override scan interval in minutes")
    args = parser.parse_args()

    config = BotConfig()
    if args.interval:
        config.interval_minutes = args.interval

    portfolio = Portfolio(config)

    print("\n" + "="*60)
    print("  PAPER TRADING BOT  (no real money)")
    print("="*60)
    print(f"  Watchlist : {config.watchlist}")
    print(f"  Candles   : {config.data_interval}  |  Period: {config.data_period}")
    print(f"  Scan every: {config.interval_minutes} minutes")
    print(f"  Capital   : ${config.capital_per_trade:.0f} per trade")
    print(f"  Min score : {config.min_score}")
    print(f"  Log file  : {config.log_file}")
    print("="*60)

    if args.once:
        run_scan(portfolio, config)
        return

    while True:
        run_scan(portfolio, config)
        wait_seconds = config.interval_minutes * 60
        print(f"  Next scan in {config.interval_minutes} minutes …  (Ctrl+C to stop)\n")
        try:
            time.sleep(wait_seconds)
        except KeyboardInterrupt:
            print("\n  Bot stopped by user.")
            print(portfolio.summary())
            break


if __name__ == "__main__":
    main()
