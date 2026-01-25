"""
Injury data stub - Load from manual CSV
"""

import pandas as pd
from loguru import logger

from src.config import CONFIG, DATA_RAW_PATH


class InjuryData:
    """Load and process injury data from CSV"""

    def __init__(self):
        self.config = CONFIG.get('data', {}).get('injuries', {})
        self.csv_path = DATA_RAW_PATH / self.config.get('csv_path', 'injuries.csv')

    def get_injuries(self, date: str = None) -> pd.DataFrame:
        """
        Get injury data for a specific date

        Args:
            date: Date string (YYYY-MM-DD)

        Returns:
            DataFrame with injury data
        """
        if not self.csv_path.exists():
            logger.warning(f"Injuries file not found at {self.csv_path}")
            return self._create_template()

        injuries = pd.read_csv(self.csv_path)

        if date:
            injuries = injuries[injuries['date'] == date]

        logger.info(f"Loaded {len(injuries)} injury records")
        return injuries

    def _create_template(self) -> pd.DataFrame:
        """Create template CSV for manual injury entry"""
        template = pd.DataFrame({
            'date': [],
            'player': [],
            'team': [],
            'status': [],  # out, questionable, doubtful
            'injury': []
        })

        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        template.to_csv(self.csv_path, index=False)
        logger.info(f"Created injuries template at {self.csv_path}")

        return template
