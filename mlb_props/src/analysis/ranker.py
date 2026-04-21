"""
Builds sorted ranking lists for Hits, Runs, and RBI.

Each ranking is a list of dicts ready to be written to an Excel sheet.
Sorting is: primary metric descending → consistency % descending → name ascending.
"""
from __future__ import annotations

import logging
from typing import Any

from src.models.player_data import PlayerAnalysis

logger = logging.getLogger(__name__)


def build_hits_ranking(players: list[PlayerAnalysis]) -> list[dict[str, Any]]:
    return _build_ranking(players, metric="hits")


def build_runs_ranking(players: list[PlayerAnalysis]) -> list[dict[str, Any]]:
    return _build_ranking(players, metric="runs")


def build_rbi_ranking(players: list[PlayerAnalysis]) -> list[dict[str, Any]]:
    return _build_ranking(players, metric="rbi")


# ── Internal ─────────────────────────────────────────────────────────────────

def _build_ranking(
    players: list[PlayerAnalysis],
    metric: str,  # "hits" | "runs" | "rbi"
) -> list[dict[str, Any]]:
    """Return a sorted list of ranking-row dicts for the given metric."""

    # Model field names use singular: pct_hit, pct_run, pct_rbi (not pct_hits)
    _singular = {"hits": "hit", "runs": "run", "rbi": "rbi"}
    singular = _singular[metric]

    avg_field = f"avg_{metric}"
    total_field = f"total_{metric}"
    games_field = f"games_with_{singular}"
    pct_field = f"pct_{singular}"

    sorted_players = sorted(
        players,
        key=lambda p: (
            -getattr(p, avg_field),
            -getattr(p, pct_field),
            p.name,
        ),
    )

    rows: list[dict[str, Any]] = []
    for rank, p in enumerate(sorted_players, start=1):
        rows.append(
            {
                "Rank": rank,
                "Player": p.name,
                "Team": p.team,
                "Today_Matchup": p.today_game.matchup_str,
                "Today_Pitcher": p.today_game.opposing_pitcher,
                "Lineup_Status": p.lineup_status,
                "Batting_Order": p.batting_order if p.batting_order else "N/A",
                f"Avg_{metric.capitalize()}": getattr(p, avg_field),
                f"Total_{metric.capitalize()}": getattr(p, total_field),
                f"Games_1+{metric.capitalize()}": getattr(p, games_field),
                f"Pct_1+{metric.capitalize()}_%": getattr(p, pct_field),
                "Games_Used": p.games_used,
                "Form_Trend": p.form_trend or "N/A",
                "Player_ID": p.player_id,  # used for color lookup
            }
        )

    logger.info("Built %s ranking: %d players", metric, len(rows))
    return rows
