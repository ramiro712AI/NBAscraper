"""
Market Scanner Pro — Entry Point

Usage:
    # Run the dashboard (opens browser at http://localhost:8050)
    python main.py

    # Custom port / host
    python main.py --host 0.0.0.0 --port 8080

    # Quick scan to console (no UI)
    python main.py --scan-only --asset crypto --timeframe 1h

    # Initialise DB only
    python main.py --init-db
"""

import argparse
import logging
import sys

import colorlog

from market_scanner.database import init_db


def setup_logging(debug: bool = False) -> None:
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(name)s%(reset)s: %(message)s",
        log_colors={
            "DEBUG":    "cyan",
            "INFO":     "green",
            "WARNING":  "yellow",
            "ERROR":    "red",
            "CRITICAL": "red,bg_white",
        },
    ))
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, handlers=[handler])

    # Silence noisy third-party loggers
    for noisy in ["urllib3", "ccxt", "yfinance", "peewee", "apscheduler"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)


def run_dashboard(host: str = "127.0.0.1", port: int = 8050, debug: bool = False) -> None:
    from market_scanner.ui.app import app
    print()
    print("=" * 60)
    print("  Market Scanner Pro")
    print(f"  Dashboard: http://{host}:{port}")
    print("  Press Ctrl+C to stop")
    print("=" * 60)
    print()
    app.run(host=host, port=port, debug=debug)


def run_scan_console(asset_type: str, timeframe: str) -> None:
    """Quick scan with rich console output."""
    from rich.console import Console
    from rich.table import Table

    console = Console()

    if asset_type == "crypto":
        from market_scanner.scanner.scanner import scan_crypto_universe
        console.print(f"\n[yellow]Scanning crypto universe on [bold]{timeframe}[/bold]...[/yellow]")
        signals = scan_crypto_universe(timeframe=timeframe, max_workers=4)
    else:
        from market_scanner.scanner.scanner import scan_stock_universe
        console.print(f"\n[yellow]Scanning stocks universe on [bold]{timeframe}[/bold]...[/yellow]")
        signals = scan_stock_universe(timeframe=timeframe, max_workers=3)

    if not signals:
        console.print("[red]No signals found.[/red]")
        return

    table = Table(title=f"Signals — {asset_type.upper()} / {timeframe}", style="bold")
    table.add_column("Symbol",    style="yellow")
    table.add_column("Score",     justify="right")
    table.add_column("Signal",    style="cyan")
    table.add_column("Strategy",  style="blue")
    table.add_column("Price",     justify="right")
    table.add_column("Trend")
    table.add_column("Volume")

    for sig in signals[:30]:
        score = sig["score"]
        score_style = "red bold" if score >= 80 else "yellow" if score >= 65 else "green"
        table.add_row(
            sig["symbol"],
            f"[{score_style}]{score:.0f}[/{score_style}]",
            sig.get("signal_type", "–"),
            sig.get("strategy_label", "–"),
            str(sig.get("price", "–")),
            sig.get("trend", "–"),
            sig.get("volume_condition", "–"),
        )

    console.print(table)
    console.print(f"\n[green]Total signals: {len(signals)}[/green]")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Market Scanner Pro — Professional Trading Analytics Platform"
    )
    parser.add_argument("--host",      default="127.0.0.1",     help="Dashboard host (default: 127.0.0.1)")
    parser.add_argument("--port",      type=int, default=8050,  help="Dashboard port (default: 8050)")
    parser.add_argument("--debug",     action="store_true",     help="Enable debug mode")
    parser.add_argument("--init-db",   action="store_true",     help="Initialise database and exit")
    parser.add_argument("--scan-only", action="store_true",     help="Run scan and print to console (no UI)")
    parser.add_argument("--asset",     default="crypto",        choices=["crypto", "stock"], help="Asset type for --scan-only")
    parser.add_argument("--timeframe", default="1h",            help="Timeframe for --scan-only")

    args = parser.parse_args()
    setup_logging(args.debug)

    # Init database
    init_db()

    if args.init_db:
        print("Database initialised.")
        sys.exit(0)

    if args.scan_only:
        run_scan_console(args.asset, args.timeframe)
        sys.exit(0)

    run_dashboard(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
