"""
NBA data ingestion using nba_api with caching
"""

import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import requests_cache
from loguru import logger
from nba_api.stats.endpoints import leaguegamefinder, teamgamelogs
from nba_api.stats.static import teams

from src.config import CONFIG, DATA_RAW_PATH


class NBADataFetcher:
    """Fetch NBA game data with caching"""

    def __init__(self, cache_enabled: bool = True):
        self.cache_enabled = cache_enabled
        self.config = CONFIG.get('data', {}).get('nba_api', {})
        self.rate_limit_delay = self.config.get('rate_limit_delay', 0.6)

        if cache_enabled:
            cache_path = DATA_RAW_PATH / 'nba_api_cache'
            requests_cache.install_cache(
                str(cache_path),
                backend='sqlite',
                expire_after=timedelta(hours=24)
            )
            logger.info("NBA API caching enabled")

    def get_season_games(self, season: str = "2024-25") -> pd.DataFrame:
        """
        Get all games for a season

        Args:
            season: Season string (e.g., "2024-25")

        Returns:
            DataFrame with game data
        """
        logger.info(f"Fetching games for season {season}")

        try:
            time.sleep(self.rate_limit_delay)
            gamefinder = leaguegamefinder.LeagueGameFinder(
                season_nullable=season,
                league_id_nullable='00'
            )

            games = gamefinder.get_data_frames()[0]
            logger.info(f"Retrieved {len(games)} game records")

            # Save to cache
            cache_file = DATA_RAW_PATH / f"games_{season.replace('-', '_')}.parquet"
            games.to_parquet(cache_file, index=False)

            return games

        except Exception as e:
            logger.error(f"Error fetching season games: {e}")
            # Try to load from cache
            cache_file = DATA_RAW_PATH / f"games_{season.replace('-', '_')}.parquet"
            if cache_file.exists():
                logger.info("Loading from cache")
                return pd.read_parquet(cache_file)
            raise

    def get_team_gamelogs(self, team_id: int, season: str = "2024-25") -> pd.DataFrame:
        """
        Get game logs for a specific team

        Args:
            team_id: NBA team ID
            season: Season string

        Returns:
            DataFrame with team game logs
        """
        try:
            time.sleep(self.rate_limit_delay)
            gamelogs = teamgamelogs.TeamGameLogs(
                team_id_nullable=team_id,
                season_nullable=season
            )

            logs = gamelogs.get_data_frames()[0]
            return logs

        except Exception as e:
            logger.error(f"Error fetching team gamelogs for {team_id}: {e}")
            return pd.DataFrame()

    @staticmethod
    def get_all_teams() -> List[Dict]:
        """Get list of all NBA teams"""
        return teams.get_teams()

    def get_games_by_date_range(
        self,
        start_date: str,
        end_date: str,
        season: str = "2024-25"
    ) -> pd.DataFrame:
        """
        Get games within a date range

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            season: Season string

        Returns:
            DataFrame with games in date range
        """
        games = self.get_season_games(season)

        if games.empty:
            return games

        # Convert GAME_DATE to datetime
        games['GAME_DATE'] = pd.to_datetime(games['GAME_DATE'])

        # Filter by date range
        mask = (games['GAME_DATE'] >= start_date) & (games['GAME_DATE'] <= end_date)
        filtered = games[mask].copy()

        logger.info(f"Found {len(filtered)} games between {start_date} and {end_date}")
        return filtered
