"""
Computes aggregated metrics for each PlayerAnalysis in-place.

All arithmetic operates on the GameEntry list already attached to each
PlayerAnalysis.  Results are written back to the dataclass fields so
downstream consumers (ranker, excel_writer) see a single coherent object.
"""
from __future__ import annotations

import logging

from src.models.player_data import PlayerAnalysis

logger = logging.getLogger(__name__)


def compute_aggregates(players: list[PlayerAnalysis]) -> None:
    """Populate aggregated fields for every player in *players* (mutates in place)."""
    for p in players:
        _aggregate_one(p)
    logger.info("Aggregated stats for %d players", len(players))


def _aggregate_one(player: PlayerAnalysis) -> None:
    games = player.last_n_games
    n = len(games)

    if n == 0:
        # All metrics stay at their zero defaults
        return

    total_h = sum(g.hits for g in games)
    total_r = sum(g.runs for g in games)
    total_rbi = sum(g.rbi for g in games)

    games_with_hit = sum(1 for g in games if g.has_hit())
    games_with_run = sum(1 for g in games if g.has_run())
    games_with_rbi = sum(1 for g in games if g.has_rbi())

    player.total_hits = total_h
    player.total_runs = total_r
    player.total_rbi = total_rbi

    player.avg_hits = round(total_h / n, 3)
    player.avg_runs = round(total_r / n, 3)
    player.avg_rbi = round(total_rbi / n, 3)

    player.games_with_hit = games_with_hit
    player.games_with_run = games_with_run
    player.games_with_rbi = games_with_rbi

    player.pct_hit = round(games_with_hit / n * 100, 1)
    player.pct_run = round(games_with_run / n * 100, 1)
    player.pct_rbi = round(games_with_rbi / n * 100, 1)

    # Placeholder trend computation — to be replaced by a proper model in v2.
    # "Hot" = avg_hits in last 5 > avg_hits in prior 5 (requires ≥10 games).
    if n >= 10:
        recent_h = sum(g.hits for g in games[-5:]) / 5
        prior_h = sum(g.hits for g in games[-10:-5]) / 5
        if recent_h > prior_h + 0.2:
            player.form_trend = "Hot"
        elif recent_h < prior_h - 0.2:
            player.form_trend = "Cold"
        else:
            player.form_trend = "Neutral"
