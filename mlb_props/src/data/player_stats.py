"""
Fetches per-player historical game logs and resolves opposing starting pitchers.

For each player in today's lineup the module:
  1. Pulls the regular-season game log (chronological, current season).
  2. Takes the last N games (configurable, default 10).
  3. For each historical game fetches the boxscore to identify the opposing
     starting pitcher (cached — many players share games).
  4. Builds a GameEntry for each game and attaches it to a PlayerAnalysis shell.

Pitchers are identified as the first pitcher listed in the team's pitchers array
(insertion order = appearance order in the game).
"""
from __future__ import annotations

import logging
from typing import Optional

from src.data.mlb_client import MLBClient
from src.data.lineups import LineupEntry
from src.data.schedule import ScheduledGame
from src.models.player_data import GameEntry, PlayerAnalysis, TodayGame

logger = logging.getLogger(__name__)


def build_player_analyses(
    client: MLBClient,
    lineup_entries: list[LineupEntry],
    games: list[ScheduledGame],
    season: int,
    max_lookback: int = 10,
    min_games: int = 3,
) -> list[PlayerAnalysis]:
    """
    Main entry point.  Returns one PlayerAnalysis per lineup entry that meets
    the minimum-games requirement.
    """
    # Map game_pk → ScheduledGame for quick lookup
    game_map = {g.game_pk: g for g in games}
    results: list[PlayerAnalysis] = []

    for entry in lineup_entries:
        analysis = _build_single(
            client, entry, game_map, season, max_lookback, min_games
        )
        if analysis is not None:
            results.append(analysis)

    logger.info(
        "Built %d player analyses (out of %d lineup entries)",
        len(results),
        len(lineup_entries),
    )
    return results


# ── Per-player builder ────────────────────────────────────────────────────────

def _build_single(
    client: MLBClient,
    entry: LineupEntry,
    game_map: dict[int, ScheduledGame],
    season: int,
    max_lookback: int,
    min_games: int,
) -> Optional[PlayerAnalysis]:

    today_game = _build_today_game(entry, game_map)
    game_entries, notes = _fetch_last_n_games(
        client, entry.player_id, season, max_lookback
    )

    if len(game_entries) < min_games:
        logger.warning(
            "Skipping %s — only %d games found (min %d)",
            entry.full_name,
            len(game_entries),
            min_games,
        )
        notes.append(
            f"Excluded: only {len(game_entries)} games found (minimum {min_games})"
        )
        # Still include but log it; caller can filter further if needed.
        # Returning None here to hard-exclude:
        return None

    return PlayerAnalysis(
        player_id=entry.player_id,
        name=entry.full_name,
        team=entry.team_name,
        team_id=entry.team_id,
        position=entry.position,
        bats=entry.bats,
        lineup_status=entry.lineup_status,
        batting_order=entry.batting_order,
        today_game=today_game,
        last_n_games=game_entries,
        games_used=len(game_entries),
        data_quality_notes=notes,
    )


def _build_today_game(
    entry: LineupEntry,
    game_map: dict[int, ScheduledGame],
) -> TodayGame:
    sg = game_map.get(entry.game_pk)
    if sg is None:
        return TodayGame(
            game_pk=entry.game_pk,
            game_time_utc="N/A",
            game_time_local=entry.game_time_local,
            opponent=entry.opponent_team_name,
            opponent_id=entry.opponent_team_id,
            opposing_pitcher=entry.opposing_pitcher,
            is_home=entry.is_home,
        )

    return TodayGame(
        game_pk=entry.game_pk,
        game_time_utc=sg.game_time_utc,
        game_time_local=sg.game_time_local,
        opponent=entry.opponent_team_name,
        opponent_id=entry.opponent_team_id,
        opposing_pitcher=entry.opposing_pitcher,
        is_home=entry.is_home,
    )


# ── Historical game log ───────────────────────────────────────────────────────

def _fetch_last_n_games(
    client: MLBClient,
    player_id: int,
    season: int,
    max_lookback: int,
) -> tuple[list[GameEntry], list[str]]:
    """
    Returns (game_entries, quality_notes).
    game_entries are sorted oldest → newest; last max_lookback taken.
    """
    notes: list[str] = []
    raw = client.get_game_log(player_id, season)

    if not raw:
        logger.warning("No game log response for player %d", player_id)
        notes.append("API returned empty game log")
        return [], notes

    # Find the hitting game-log stat block
    splits: list[dict] = []
    for stat_block in raw.get("stats", []):
        group = stat_block.get("group", {}).get("displayName", "")
        if group.lower() == "hitting":
            splits = stat_block.get("splits", [])
            break

    if not splits:
        logger.warning("No hitting splits for player %d", player_id)
        notes.append("No hitting splits found in game log")
        return [], notes

    # Take the most recent max_lookback entries (API returns oldest-first)
    recent_splits = splits[-max_lookback:]

    if len(splits) < max_lookback:
        notes.append(
            f"Only {len(splits)} games available in {season} season "
            f"(requested {max_lookback})"
        )

    game_entries: list[GameEntry] = []
    for split in recent_splits:
        entry = _parse_split(client, split)
        game_entries.append(entry)

    return game_entries, notes


def _parse_split(client: MLBClient, split: dict) -> GameEntry:
    """Parse one game-log split into a GameEntry, resolving opposing pitcher."""
    stat = split.get("stat", {})
    hits = int(stat.get("hits", 0) or 0)
    runs = int(stat.get("runs", 0) or 0)
    rbi = int(stat.get("rbi", 0) or 0)

    date_str = split.get("date", "N/A")
    opponent = split.get("opponent", {}).get("name", "N/A")
    game_pk = split.get("game", {}).get("gamePk") or split.get("gamePk", 0)

    # Determine which side the player's team was on to find the opposing pitcher
    player_is_home = split.get("isHome", False)
    # If player is home → opposing pitcher is on the away side
    opposing_side = "away" if player_is_home else "home"

    opposing_pitcher = _get_starting_pitcher(client, game_pk, opposing_side)

    return GameEntry(
        game_pk=game_pk,
        date=date_str,
        opponent=opponent,
        opposing_pitcher=opposing_pitcher,
        hits=hits,
        runs=runs,
        rbi=rbi,
    )


# ── Starting pitcher resolution ───────────────────────────────────────────────

def _get_starting_pitcher(
    client: MLBClient,
    game_pk: int,
    side: str,  # "home" | "away"
) -> str:
    """
    Extract the starting pitcher's name from a game boxscore.

    The starting pitcher is assumed to be the first element of the
    `pitchers` array (which lists pitchers in order of appearance).
    Falls back to "N/A" on any missing data.
    """
    if not game_pk:
        return "N/A"

    boxscore = client.get_boxscore(game_pk)
    if not boxscore:
        return "N/A"

    try:
        team_data = boxscore["teams"][side]
        pitchers: list[int] = team_data.get("pitchers", [])
        if not pitchers:
            return "N/A"

        starter_id = pitchers[0]
        player_key = f"ID{starter_id}"
        players: dict = team_data.get("players", {})
        player_info = players.get(player_key, {})

        name = player_info.get("person", {}).get("fullName", "")
        return name if name else "N/A"

    except (KeyError, IndexError, TypeError) as exc:
        logger.debug(
            "Could not resolve starting pitcher for game %d side=%s: %s",
            game_pk, side, exc,
        )
        return "N/A"
