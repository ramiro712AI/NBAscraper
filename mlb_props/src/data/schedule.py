"""
Fetches and parses the daily MLB schedule.

Extracts game PKs, matchup info, game times, and probable starting pitchers
for every game scheduled on the target date.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import pytz

from src.data.mlb_client import MLBClient

logger = logging.getLogger(__name__)


@dataclass
class ScheduledGame:
    """Lightweight representation of one MLB game on the schedule."""

    game_pk: int
    game_time_utc: str
    game_time_local: str
    home_team_id: int
    home_team_name: str
    away_team_id: int
    away_team_name: str
    home_probable_pitcher: str   # Name or "TBD"
    away_probable_pitcher: str
    home_probable_pitcher_id: Optional[int]
    away_probable_pitcher_id: Optional[int]
    status: str                  # e.g. "Scheduled", "In Progress", "Final"
    lineups_posted: bool         # True when official lineup card is available


def fetch_schedule(
    client: MLBClient,
    date: str,
    local_tz: str = "America/New_York",
) -> list[ScheduledGame]:
    """
    Return all MLB games scheduled for *date* ("YYYY-MM-DD").

    Only games with status Preview/Pre-Game/Scheduled/Warm Up/In Progress
    are included; postponed/cancelled games are skipped.
    """
    raw = client.get_schedule(date)
    if not raw:
        logger.warning("Empty schedule response for %s", date)
        return []

    tz = pytz.timezone(local_tz)
    games: list[ScheduledGame] = []

    for date_block in raw.get("dates", []):
        for g in date_block.get("games", []):
            status_detail = g.get("status", {}).get("detailedState", "Unknown")
            abstract_state = g.get("status", {}).get("abstractGameState", "Preview")

            # Skip abandoned/postponed games
            if abstract_state in ("Final",) and "postponed" in status_detail.lower():
                logger.info("Skipping postponed game %s", g.get("gamePk"))
                continue

            game_pk = g.get("gamePk", 0)
            game_date_utc = g.get("gameDate", "")

            # Convert UTC → local time for display
            game_time_local = _utc_to_local(game_date_utc, tz)

            teams = g.get("teams", {})
            home = teams.get("home", {})
            away = teams.get("away", {})

            home_team = home.get("team", {})
            away_team = away.get("team", {})

            home_pp = home.get("probablePitcher", {})
            away_pp = away.get("probablePitcher", {})

            lineups_posted = bool(
                g.get("lineups", {}).get("homePlayers")
                or g.get("lineups", {}).get("awayPlayers")
            )

            games.append(
                ScheduledGame(
                    game_pk=game_pk,
                    game_time_utc=game_date_utc,
                    game_time_local=game_time_local,
                    home_team_id=home_team.get("id", 0),
                    home_team_name=home_team.get("name", "Unknown"),
                    away_team_id=away_team.get("id", 0),
                    away_team_name=away_team.get("name", "Unknown"),
                    home_probable_pitcher=home_pp.get("fullName", "TBD"),
                    away_probable_pitcher=away_pp.get("fullName", "TBD"),
                    home_probable_pitcher_id=home_pp.get("id"),
                    away_probable_pitcher_id=away_pp.get("id"),
                    status=status_detail,
                    lineups_posted=lineups_posted,
                )
            )
            logger.info(
                "Game %d: %s @ %s  |  Pitcher A=%s, H=%s  |  lineups=%s",
                game_pk,
                away_team.get("name"),
                home_team.get("name"),
                away_pp.get("fullName", "TBD"),
                home_pp.get("fullName", "TBD"),
                lineups_posted,
            )

    logger.info("Found %d game(s) on %s", len(games), date)
    return games


def _utc_to_local(utc_str: str, tz: pytz.BaseTzInfo) -> str:
    """Convert ISO-8601 UTC string to a readable local time string."""
    if not utc_str:
        return "N/A"
    try:
        from datetime import datetime

        dt_utc = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
        dt_local = dt_utc.astimezone(tz)
        return dt_local.strftime("%I:%M %p %Z")
    except (ValueError, TypeError):
        return utc_str
