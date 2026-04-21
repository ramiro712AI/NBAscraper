"""
MLB Props Analyzer — Daily Entry Point
======================================

Run:
    python main.py                      # analyze today
    python main.py --date 2025-04-21   # analyze a specific date
    python main.py --debug              # verbose logging

Output:
    output/MLB_Props_YYYY-MM-DD.xlsx
    logs/mlb_props_YYYY-MM-DD.log
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

# ── Bootstrap ────────────────────────────────────────────────────────────────
# Load .env from project root before anything else
_ROOT = Path(__file__).parent
load_dotenv(_ROOT / "config" / ".env", override=False)

# Ensure src/ is importable regardless of working directory
sys.path.insert(0, str(_ROOT))

from utils.logger import setup_logger
from src.data.mlb_client import MLBClient
from src.data.schedule import fetch_schedule
from src.data.lineups import resolve_lineups
from src.data.player_stats import build_player_analyses
from src.analysis.aggregator import compute_aggregates
from src.analysis.ranker import build_hits_ranking, build_runs_ranking, build_rbi_ranking
from src.output.excel_writer import generate_excel_report

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# Config loading
# ══════════════════════════════════════════════════════════════════════════════

def load_config() -> dict:
    """Merge config.json with optional environment overrides."""
    config_path = _ROOT / "config" / "config.json"
    with open(config_path, encoding="utf-8") as f:
        cfg: dict = json.load(f)

    # Environment variable overrides (from .env or shell)
    if os.getenv("SEASON"):
        cfg["season"] = int(os.environ["SEASON"])
    if os.getenv("OUTPUT_DIR"):
        cfg["output_dir"] = os.environ["OUTPUT_DIR"]
    if os.getenv("LOG_LEVEL"):
        cfg["log_level"] = os.environ["LOG_LEVEL"]
    if os.getenv("LOCAL_TIMEZONE"):
        cfg["local_timezone"] = os.environ["LOCAL_TIMEZONE"]

    return cfg


# ══════════════════════════════════════════════════════════════════════════════
# Pipeline
# ══════════════════════════════════════════════════════════════════════════════

def run(target_date: str, cfg: dict) -> str:
    """
    Execute the full daily analysis pipeline.

    Parameters
    ----------
    target_date : str
        Date to analyze in "YYYY-MM-DD" format.
    cfg : dict
        Merged configuration dictionary.

    Returns
    -------
    str
        Absolute path to the generated Excel file.
    """
    logger.info("═" * 60)
    logger.info("MLB Props Analyzer — %s", target_date)
    logger.info("═" * 60)

    client = MLBClient(
        timeout=cfg["api_timeout_seconds"],
        max_retries=cfg["api_max_retries"],
        call_delay=cfg.get("call_delay_seconds", 0.08),
    )

    # ── Step 1: Schedule ─────────────────────────────────────────────────────
    logger.info("[1/6] Fetching schedule for %s", target_date)
    games = fetch_schedule(client, target_date, cfg["local_timezone"])

    if not games:
        logger.warning("No games found for %s — exiting.", target_date)
        sys.exit(0)

    logger.info("      %d game(s) on schedule", len(games))

    # ── Step 2: Lineups ──────────────────────────────────────────────────────
    logger.info("[2/6] Resolving lineups")
    lineup_entries = resolve_lineups(client, games, cfg["positions_to_include"])

    if not lineup_entries:
        logger.error("No lineup players resolved — check schedule/roster APIs.")
        sys.exit(1)

    logger.info("      %d position players identified", len(lineup_entries))

    # ── Step 3: Historical stats ─────────────────────────────────────────────
    logger.info("[3/6] Fetching last-%d game logs + resolving opposing pitchers",
                cfg["max_games_lookback"])
    players = build_player_analyses(
        client,
        lineup_entries,
        games,
        season=cfg["season"],
        max_lookback=cfg["max_games_lookback"],
        min_games=cfg["min_games_required"],
    )

    if not players:
        logger.error("No players with sufficient game history — cannot produce report.")
        sys.exit(1)

    logger.info("      %d players with sufficient history", len(players))

    # ── Step 4: Aggregation ──────────────────────────────────────────────────
    logger.info("[4/6] Computing aggregated metrics")
    compute_aggregates(players)

    # ── Step 5: Rankings ─────────────────────────────────────────────────────
    logger.info("[5/6] Building rankings")
    hits_ranking = build_hits_ranking(players)
    runs_ranking = build_runs_ranking(players)
    rbi_ranking = build_rbi_ranking(players)

    logger.info(
        "      Hits: %d | Runs: %d | RBI: %d",
        len(hits_ranking), len(runs_ranking), len(rbi_ranking),
    )

    # ── Step 6: Excel output ─────────────────────────────────────────────────
    logger.info("[6/6] Generating Excel report")
    output_path = generate_excel_report(
        players=players,
        hits_ranking=hits_ranking,
        runs_ranking=runs_ranking,
        rbi_ranking=rbi_ranking,
        run_date=target_date,
        output_dir=cfg["output_dir"],
        max_lookback=cfg["max_games_lookback"],
    )

    logger.info("═" * 60)
    logger.info("Done.  Report: %s", output_path)
    logger.info("Players analyzed: %d", len(players))
    logger.info("═" * 60)

    return output_path


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="MLB Props Analyzer — daily parlay support tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--date",
        default=os.getenv("ANALYSIS_DATE", ""),
        help="Target date YYYY-MM-DD (default: today)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable DEBUG-level logging",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    cfg = load_config()

    if args.debug:
        cfg["log_level"] = "DEBUG"

    target_date = args.date or str(date.today())

    # Validate date format
    try:
        from datetime import datetime
        datetime.strptime(target_date, "%Y-%m-%d")
    except ValueError:
        print(f"ERROR: Invalid date format '{target_date}'. Use YYYY-MM-DD.")
        sys.exit(1)

    setup_logger(
        log_dir=cfg["log_dir"],
        log_level=cfg["log_level"],
        run_date=target_date,
    )

    run(target_date, cfg)


if __name__ == "__main__":
    main()
