"""
MLB Stats API HTTP client.

Public API (statsapi.mlb.com) — no key required.
Implements session reuse, automatic retry with exponential backoff,
and an in-process request cache to avoid redundant network calls.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

_BASE_V1 = "https://statsapi.mlb.com/api/v1"
_BASE_V1_1 = "https://statsapi.mlb.com/api/v1.1"


class MLBClient:
    """Thread-safe MLB Stats API client with in-process cache."""

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        call_delay: float = 0.08,
    ) -> None:
        self._timeout = timeout
        self._call_delay = call_delay
        self._cache: dict[str, Any] = {}
        self._session = self._build_session(max_retries)

    # ── Session setup ────────────────────────────────────────────────────────

    def _build_session(self, max_retries: int) -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=max_retries,
            backoff_factor=1.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.headers.update({"User-Agent": "MLBPropsAnalyzer/1.0"})
        return session

    # ── Internal GET with cache ──────────────────────────────────────────────

    def _get(self, url: str, params: Optional[dict[str, str]] = None) -> dict:
        params = params or {}
        cache_key = url + "|" + "&".join(f"{k}={v}" for k, v in sorted(params.items()))

        if cache_key in self._cache:
            return self._cache[cache_key]

        time.sleep(self._call_delay)

        try:
            resp = self._session.get(url, params=params, timeout=self._timeout)
            resp.raise_for_status()
            data: dict = resp.json()
            self._cache[cache_key] = data
            logger.debug("GET %s → %d bytes", url, len(resp.content))
            return data
        except requests.exceptions.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "?"
            logger.error("HTTP %s on %s", status, url)
        except requests.exceptions.ConnectionError:
            logger.error("Connection error for %s", url)
        except requests.exceptions.Timeout:
            logger.error("Timeout for %s", url)
        except requests.exceptions.RequestException as exc:
            logger.error("Request error for %s: %s", url, exc)
        except ValueError:
            logger.error("Invalid JSON from %s", url)

        return {}

    # ── Public API methods ───────────────────────────────────────────────────

    def get_schedule(self, date: str) -> dict:
        """
        Today's schedule with probable pitchers and posted lineups.

        date: "YYYY-MM-DD"
        """
        return self._get(
            f"{_BASE_V1}/schedule",
            {
                "sportId": "1",
                "date": date,
                "hydrate": "teams,probablePitcher,lineups,linescore",
            },
        )

    def get_game_feed(self, game_pk: int) -> dict:
        """
        Live game feed.
        Contains confirmed batting orders and probable pitcher info
        once the lineup card is posted.
        """
        return self._get(f"{_BASE_V1_1}/game/{game_pk}/feed/live")

    def get_boxscore(self, game_pk: int) -> dict:
        """
        Completed-game boxscore.
        Used to extract the starting pitcher for historical games.
        """
        return self._get(f"{_BASE_V1}/game/{game_pk}/boxscore")

    def get_game_log(self, player_id: int, season: int) -> dict:
        """
        Batter's game-by-game hitting stats for the regular season.
        Splits are returned in chronological order (oldest first).
        """
        return self._get(
            f"{_BASE_V1}/people/{player_id}/stats",
            {"stats": "gameLog", "season": str(season), "gameType": "R"},
        )

    def get_person(self, player_id: int) -> dict:
        """Player metadata: position, bats, throws, current team."""
        return self._get(f"{_BASE_V1}/people/{player_id}", {"hydrate": "currentTeam"})

    def get_active_roster(self, team_id: int) -> dict:
        """Active 26-man roster for a team (used as lineup fallback)."""
        return self._get(
            f"{_BASE_V1}/teams/{team_id}/roster",
            {"rosterType": "active"},
        )
