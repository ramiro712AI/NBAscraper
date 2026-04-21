"""Core data models for MLB Props Analyzer."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GameEntry:
    """Statistical record for one historical game."""

    game_pk: int
    date: str           # "YYYY-MM-DD"
    opponent: str       # Team abbreviation or name
    opposing_pitcher: str  # Starter name or "N/A"
    hits: int
    runs: int
    rbi: int

    def has_hit(self) -> bool:
        return self.hits >= 1

    def has_run(self) -> bool:
        return self.runs >= 1

    def has_rbi(self) -> bool:
        return self.rbi >= 1


@dataclass
class TodayGame:
    """Metadata for the player's scheduled game today."""

    game_pk: int
    game_time_utc: str    # ISO-8601
    game_time_local: str  # Human-readable, local TZ
    opponent: str
    opponent_id: int
    opposing_pitcher: str  # Probable pitcher or "N/A"
    is_home: bool
    pitcher_hand: str = "N/A"  # Future: "R" | "L"

    @property
    def venue_label(self) -> str:
        return "Home" if self.is_home else "Away"

    @property
    def matchup_str(self) -> str:
        prefix = "vs" if self.is_home else "@"
        return f"{prefix} {self.opponent}"


@dataclass
class PlayerAnalysis:
    """Complete daily analysis record for one MLB position player."""

    # Identity
    player_id: int
    name: str
    team: str
    team_id: int
    position: str      # Primary position abbreviation
    bats: str          # "R" | "L" | "S"
    lineup_status: str  # "Confirmed" | "Projected" | "Unknown"
    batting_order: Optional[int]  # 1–9 or None

    # Today's game context
    today_game: TodayGame

    # Historical data (up to max_games_lookback, ordered oldest → newest)
    last_n_games: list  # List[GameEntry]
    games_used: int     # Actual count; may be < 10

    # Data-quality notes collected during pipeline
    data_quality_notes: list = field(default_factory=list)

    # ── Aggregated metrics (populated by analysis.aggregator) ────────────────
    total_hits: int = 0
    total_runs: int = 0
    total_rbi: int = 0
    avg_hits: float = 0.0
    avg_runs: float = 0.0
    avg_rbi: float = 0.0
    games_with_hit: int = 0
    games_with_run: int = 0
    games_with_rbi: int = 0
    pct_hit: float = 0.0   # 0–100
    pct_run: float = 0.0
    pct_rbi: float = 0.0

    # ── Future scoring layer (v2 — not computed in v1) ───────────────────────
    confidence_score: Optional[float] = None
    form_trend: Optional[str] = None  # "Hot" | "Cold" | "Neutral"
    home_away_split_note: Optional[str] = None
    vs_hand_split_note: Optional[str] = None
    lineup_position_note: Optional[str] = None
