#!/usr/bin/env python3
"""
main.py – NCAAB Prediction Pipeline entry point.

Usage
-----
  python main.py                     # today's games (America/New_York)
  python main.py --date 2026-02-18   # specific date
  python main.py --debug             # verbose logging

Output
------
  - Terminal: full game table + FINAL RANKING (#1–#N)
  - outputs/ncaab_picks_YYYYMMDD.csv
  - outputs/ncaab_picks_YYYYMMDD.json
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

# Allow running from the project root
import os, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from src.utils    import get_logger
from src.schedule import get_todays_games
from src.stats    import get_all_team_stats
from src.model    import predict_all_games
from src.output   import run_output

log = get_logger("main")


def parse_args():
    p = argparse.ArgumentParser(description="NCAAB Prediction Pipeline")
    p.add_argument(
        "--date", "-d",
        default=None,
        help="Target date YYYY-MM-DD (default: today ET)",
    )
    p.add_argument(
        "--debug",
        action="store_true",
        help="Enable DEBUG logging",
    )
    return p.parse_args()


def main():
    args = parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        for name in ("main", "schedule", "stats", "model", "output", "utils"):
            logging.getLogger(name).setLevel(logging.DEBUG)

    # ── Target date ──────────────────────────────────────────────────────────
    ny_tz = ZoneInfo("America/New_York")
    if args.date:
        target = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=ny_tz)
    else:
        target = datetime.now(ny_tz)

    date_str = target.strftime("%Y%m%d")
    log.info(f"NCAAB Prediction Pipeline  –  {target.strftime('%A %B %d, %Y')} (ET)")

    # ── 1. Fetch schedule ────────────────────────────────────────────────────
    log.info("Step 1/3 – Fetching today's schedule …")
    games = get_todays_games(target)
    if not games:
        log.error("No games found. Exiting.")
        sys.exit(1)
    log.info(f"  {len(games)} games found")

    # ── 2. Fetch team stats ──────────────────────────────────────────────────
    log.info("Step 2/3 – Fetching team statistics …")
    all_abbrs = list({g["away_abbr"] for g in games} | {g["home_abbr"] for g in games})
    all_stats = get_all_team_stats(all_abbrs)
    log.info(f"  Stats loaded for {len(all_stats)} teams")

    # ── 3. Run prediction model ──────────────────────────────────────────────
    log.info("Step 3/3 – Running prediction model …")
    results = predict_all_games(games, all_stats)
    log.info(f"  {len(results)} predictions generated")

    if not results:
        log.error("No predictions produced. Check stats/schedule data.")
        sys.exit(1)

    # ── 4. Output ────────────────────────────────────────────────────────────
    run_output(results, date_str)
    log.info("Pipeline complete.")


if __name__ == "__main__":
    main()
