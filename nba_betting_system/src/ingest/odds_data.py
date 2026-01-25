"""
Odds data fetching from The Odds API with CSV stub fallback
"""

import time
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
import requests
from loguru import logger

from src.config import CONFIG, DATA_RAW_PATH, ODDS_API_KEY


class OddsFetcher:
    """Fetch odds data from The Odds API or CSV stub"""

    def __init__(self):
        self.api_key = ODDS_API_KEY
        self.config = CONFIG.get('data', {}).get('odds_api', {})
        self.base_url = "https://api.the-odds-api.com/v4"
        self.use_stub = self.config.get('use_stub_if_no_key', True) and not self.api_key

        if self.use_stub:
            logger.warning("No Odds API key found, using CSV stub")

    def get_nba_odds(self, date: Optional[str] = None) -> pd.DataFrame:
        """
        Get NBA odds for a specific date

        Args:
            date: Date string (YYYY-MM-DD), defaults to today

        Returns:
            DataFrame with odds data
        """
        if self.use_stub:
            return self._load_from_stub(date)

        return self._fetch_from_api(date)

    def _fetch_from_api(self, date: Optional[str] = None) -> pd.DataFrame:
        """Fetch odds from The Odds API"""
        try:
            endpoint = f"{self.base_url}/sports/basketball_nba/odds"
            params = {
                'apiKey': self.api_key,
                'regions': 'us',
                'markets': 'h2h,spreads,totals',
                'oddsFormat': 'american'
            }

            if date:
                params['commenceTimeFrom'] = f"{date}T00:00:00Z"
                params['commenceTimeTo'] = f"{date}T23:59:59Z"

            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            odds_df = self._parse_odds_response(data)

            # Cache to file
            cache_file = DATA_RAW_PATH / f"odds_{date or 'today'}.parquet"
            odds_df.to_parquet(cache_file, index=False)

            logger.info(f"Fetched odds for {len(odds_df)} games")
            return odds_df

        except Exception as e:
            logger.error(f"Error fetching odds from API: {e}")
            return self._load_from_stub(date)

    def _parse_odds_response(self, data: List[Dict]) -> pd.DataFrame:
        """Parse API response into DataFrame"""
        records = []

        for game in data:
            game_id = game.get('id')
            commence_time = game.get('commence_time')
            home_team = game.get('home_team')
            away_team = game.get('away_team')

            for bookmaker in game.get('bookmakers', []):
                bookmaker_name = bookmaker.get('key')

                for market in bookmaker.get('markets', []):
                    market_type = market.get('key')

                    for outcome in market.get('outcomes', []):
                        record = {
                            'game_id': game_id,
                            'commence_time': commence_time,
                            'home_team': home_team,
                            'away_team': away_team,
                            'bookmaker': bookmaker_name,
                            'market': market_type,
                            'name': outcome.get('name'),
                            'price': outcome.get('price'),
                            'point': outcome.get('point')
                        }
                        records.append(record)

        return pd.DataFrame(records)

    def _load_from_stub(self, date: Optional[str] = None) -> pd.DataFrame:
        """Load odds from CSV stub"""
        stub_file = DATA_RAW_PATH / "odds_stub.csv"

        if not stub_file.exists():
            logger.warning(f"Odds stub file not found at {stub_file}")
            return self._create_stub_template()

        odds = pd.read_csv(stub_file)

        if date:
            odds = odds[odds['date'] == date]

        logger.info(f"Loaded {len(odds)} odds from stub")
        return odds

    def _create_stub_template(self) -> pd.DataFrame:
        """Create template CSV for manual odds entry"""
        template = pd.DataFrame({
            'date': [],
            'home_team': [],
            'away_team': [],
            'bookmaker': [],
            'market': [],  # h2h, spreads, totals
            'name': [],  # team name or over/under
            'price': [],  # American odds
            'point': []  # spread/total line
        })

        stub_file = DATA_RAW_PATH / "odds_stub.csv"
        template.to_csv(stub_file, index=False)
        logger.info(f"Created odds stub template at {stub_file}")

        return template


def american_to_prob(odds: float, remove_vig: bool = False) -> float:
    """
    Convert American odds to implied probability

    Args:
        odds: American odds (e.g., -110, +150)
        remove_vig: If True, adjust for vig (not implemented yet)

    Returns:
        Implied probability (0 to 1)
    """
    if odds < 0:
        prob = abs(odds) / (abs(odds) + 100)
    else:
        prob = 100 / (odds + 100)

    return prob


def prob_to_american(prob: float) -> float:
    """
    Convert probability to American odds

    Args:
        prob: Probability (0 to 1)

    Returns:
        American odds
    """
    if prob >= 0.5:
        return -100 * prob / (1 - prob)
    else:
        return 100 * (1 - prob) / prob
