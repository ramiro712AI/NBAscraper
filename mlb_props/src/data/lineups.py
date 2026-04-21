"""
Lineup resolution for today's games.

Priority order:
  1. Official lineup from game feed (confirmed batting order once card is posted).
  2. Lineup IDs from schedule hydration (lineups endpoint).
  3. Active roster fallback — marks players as "Projected".

Position players only; pitchers are filtered unless DH is active.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from src.data.mlb_client import MLBClient
from src.data.schedule import ScheduledGame

logger = logging.getLogger(__name__)

# Positions considered "hittable" for props purposes.
_HITTER_POSITIONS = {
    "C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH",
    # Outfield generic codes used by the API
    "OF", "IF",
}


@dataclass
class LineupEntry:
    """A single player slot in today's resolved lineup."""

    player_id: int
    full_name: str
    team_id: int
    team_name: str
    position: str         # Primary position abbreviation
    bats: str             # "R" | "L" | "S" | "N/A"
    batting_order: Optional[int]  # 1–9 or None
    lineup_status: str    # "Confirmed" | "Projected" | "Unknown"
    game_pk: int
    is_home: bool
    opponent_team_id: int
    opponent_team_name: str
    opposing_pitcher: str
    opposing_pitcher_id: Optional[int]
    game_time_local: str


def resolve_lineups(
    client: MLBClient,
    games: list[ScheduledGame],
    positions_to_include: list[str],
) -> list[LineupEntry]:
    """
    Resolve lineup players for all games on the schedule.

    Returns a deduplicated, filtered list of LineupEntry objects covering
    only confirmed-eligible position players.
    """
    seen_player_ids: set[int] = set()
    entries: list[LineupEntry] = []

    for game in games:
        game_entries = _resolve_game_lineup(client, game, positions_to_include)
        for entry in game_entries:
            if entry.player_id not in seen_player_ids:
                seen_player_ids.add(entry.player_id)
                entries.append(entry)

    logger.info("Resolved %d unique position players across all games", len(entries))
    return entries


# ── Per-game resolution ──────────────────────────────────────────────────────

def _resolve_game_lineup(
    client: MLBClient,
    game: ScheduledGame,
    positions_to_include: list[str],
) -> list[LineupEntry]:
    """Try confirmed → schedule lineups → roster fallback for one game."""

    entries = _try_game_feed(client, game, positions_to_include)
    if entries:
        logger.info(
            "Game %d: confirmed lineup (%d players)", game.game_pk, len(entries)
        )
        return entries

    entries = _try_schedule_lineups(client, game, positions_to_include)
    if entries:
        logger.info(
            "Game %d: schedule lineup (%d players)", game.game_pk, len(entries)
        )
        return entries

    entries = _try_roster_fallback(client, game, positions_to_include)
    logger.info(
        "Game %d: roster fallback (%d players)", game.game_pk, len(entries)
    )
    return entries


# ── Strategy 1: live game feed ───────────────────────────────────────────────

def _try_game_feed(
    client: MLBClient,
    game: ScheduledGame,
    positions_to_include: list[str],
) -> list[LineupEntry]:
    feed = client.get_game_feed(game.game_pk)
    if not feed:
        return []

    live_data = feed.get("liveData", {})
    boxscore = live_data.get("boxscore", {})
    teams_data = boxscore.get("teams", {})

    game_data = feed.get("gameData", {})
    probable = game_data.get("probablePitchers", {})

    entries: list[LineupEntry] = []

    for side, is_home in (("away", False), ("home", True)):
        team_box = teams_data.get(side, {})
        batting_order_ids: list[int] = team_box.get("battingOrder", [])

        if not batting_order_ids:
            return []  # Feed available but lineup not yet posted

        players_dict: dict = team_box.get("players", {})
        team_info = team_box.get("team", {})
        team_id = team_info.get("id", 0)
        team_name = team_info.get("name", "Unknown")

        if is_home:
            opp_id = game.away_team_id
            opp_name = game.away_team_name
            opp_pitcher = game.away_probable_pitcher
            opp_pitcher_id = game.away_probable_pitcher_id
        else:
            opp_id = game.home_team_id
            opp_name = game.home_team_name
            opp_pitcher = game.home_probable_pitcher
            opp_pitcher_id = game.home_probable_pitcher_id

        for order_idx, pid in enumerate(batting_order_ids, start=1):
            pkey = f"ID{pid}"
            pdata = players_dict.get(pkey, {})

            position = (
                pdata.get("position", {}).get("abbreviation", "")
                or pdata.get("allPositions", [{}])[0].get("abbreviation", "")
            )

            if not _is_eligible_position(position, positions_to_include):
                continue

            person = pdata.get("person", {})
            bats = person.get("batSide", {}).get("code", "N/A")

            entries.append(
                LineupEntry(
                    player_id=pid,
                    full_name=person.get("fullName", f"Player {pid}"),
                    team_id=team_id,
                    team_name=team_name,
                    position=position or "N/A",
                    bats=bats,
                    batting_order=order_idx,
                    lineup_status="Confirmed",
                    game_pk=game.game_pk,
                    is_home=is_home,
                    opponent_team_id=opp_id,
                    opponent_team_name=opp_name,
                    opposing_pitcher=opp_pitcher,
                    opposing_pitcher_id=opp_pitcher_id,
                    game_time_local=game.game_time_local,
                )
            )

    return entries


# ── Strategy 2: schedule lineup hydration ────────────────────────────────────

def _try_schedule_lineups(
    client: MLBClient,
    game: ScheduledGame,
    positions_to_include: list[str],
) -> list[LineupEntry]:
    """
    Use player IDs from the schedule's lineups hydration.
    Position and bats info must be enriched from the person endpoint.
    """
    raw = client.get_schedule(game.game_time_utc[:10])  # date portion
    if not raw:
        return []

    # Find this specific game in the schedule response
    game_data_raw: Optional[dict] = None
    for date_block in raw.get("dates", []):
        for g in date_block.get("games", []):
            if g.get("gamePk") == game.game_pk:
                game_data_raw = g
                break

    if not game_data_raw:
        return []

    lineups_raw = game_data_raw.get("lineups", {})
    if not lineups_raw:
        return []

    entries: list[LineupEntry] = []

    for side_key, is_home, team_id, team_name, opp_id, opp_name, opp_pitcher, opp_pid in [
        (
            "awayPlayers", False,
            game.away_team_id, game.away_team_name,
            game.home_team_id, game.home_team_name,
            game.home_probable_pitcher, game.home_probable_pitcher_id,
        ),
        (
            "homePlayers", True,
            game.home_team_id, game.home_team_name,
            game.away_team_id, game.away_team_name,
            game.away_probable_pitcher, game.away_probable_pitcher_id,
        ),
    ]:
        side_players = lineups_raw.get(side_key, [])
        for order_idx, p in enumerate(side_players, start=1):
            pid = p.get("id", 0)
            if not pid:
                continue

            position = p.get("position", {}).get("abbreviation", "")
            full_name = p.get("fullName", "")

            # Enrich from person API if position missing
            if not position or not full_name:
                person_raw = client.get_person(pid)
                person_list = person_raw.get("people", [{}])
                person = person_list[0] if person_list else {}
                position = position or person.get("primaryPosition", {}).get("abbreviation", "N/A")
                full_name = full_name or person.get("fullName", f"Player {pid}")
                bats = person.get("batSide", {}).get("code", "N/A")
            else:
                bats = p.get("batSide", {}).get("code", "N/A")

            if not _is_eligible_position(position, positions_to_include):
                continue

            entries.append(
                LineupEntry(
                    player_id=pid,
                    full_name=full_name,
                    team_id=team_id,
                    team_name=team_name,
                    position=position,
                    bats=bats,
                    batting_order=order_idx,
                    lineup_status="Confirmed",
                    game_pk=game.game_pk,
                    is_home=is_home,
                    opponent_team_id=opp_id,
                    opponent_team_name=opp_name,
                    opposing_pitcher=opp_pitcher,
                    opposing_pitcher_id=opp_pid,
                    game_time_local=game.game_time_local,
                )
            )

    return entries


# ── Strategy 3: active roster fallback ──────────────────────────────────────

def _try_roster_fallback(
    client: MLBClient,
    game: ScheduledGame,
    positions_to_include: list[str],
) -> list[LineupEntry]:
    """
    Use the full active roster when no lineup is posted.
    All players are marked "Projected"; batting order is None.
    """
    entries: list[LineupEntry] = []

    for team_id, team_name, is_home, opp_id, opp_name, opp_pitcher, opp_pid in [
        (
            game.away_team_id, game.away_team_name, False,
            game.home_team_id, game.home_team_name,
            game.home_probable_pitcher, game.home_probable_pitcher_id,
        ),
        (
            game.home_team_id, game.home_team_name, True,
            game.away_team_id, game.away_team_name,
            game.away_probable_pitcher, game.away_probable_pitcher_id,
        ),
    ]:
        roster_raw = client.get_active_roster(team_id)
        if not roster_raw:
            logger.warning("No roster data for team %d", team_id)
            continue

        for player in roster_raw.get("roster", []):
            person = player.get("person", {})
            pid = person.get("id", 0)
            if not pid:
                continue

            position = player.get("position", {}).get("abbreviation", "N/A")
            if not _is_eligible_position(position, positions_to_include):
                continue

            # Enrich bats from person API
            person_raw = client.get_person(pid)
            person_detail = (person_raw.get("people", [{}]) or [{}])[0]
            bats = person_detail.get("batSide", {}).get("code", "N/A")

            entries.append(
                LineupEntry(
                    player_id=pid,
                    full_name=person.get("fullName", f"Player {pid}"),
                    team_id=team_id,
                    team_name=team_name,
                    position=position,
                    bats=bats,
                    batting_order=None,
                    lineup_status="Projected",
                    game_pk=game.game_pk,
                    is_home=is_home,
                    opponent_team_id=opp_id,
                    opponent_team_name=opp_name,
                    opposing_pitcher=opp_pitcher,
                    opposing_pitcher_id=opp_pid,
                    game_time_local=game.game_time_local,
                )
            )

    return entries


# ── Helpers ──────────────────────────────────────────────────────────────────

def _is_eligible_position(position: str, allowed: list[str]) -> bool:
    """Return True if position qualifies as a hittable prop position."""
    if not position:
        return False
    return position.upper() in {p.upper() for p in allowed} or position.upper() in _HITTER_POSITIONS
