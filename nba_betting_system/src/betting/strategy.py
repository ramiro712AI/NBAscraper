"""
Betting strategy - Expected Value, Kelly Criterion, filters
"""

from typing import Dict, List, Optional

import pandas as pd
from loguru import logger

from src.config import CONFIG
from src.ingest.odds_data import american_to_prob, prob_to_american


class BettingStrategy:
    """Calculate EV, apply Kelly Criterion, and filter bets"""

    def __init__(self, config: Dict = None):
        self.config = config or CONFIG.get('betting', {})
        self.min_ev_pct = self.config.get('min_ev_pct', 2.0)
        self.max_ev_pct = self.config.get('max_ev_pct', 50.0)
        self.min_prob = self.config.get('min_prob', 0.40)
        self.max_prob = self.config.get('max_prob', 0.80)
        self.use_kelly = self.config.get('use_kelly', True)
        self.kelly_fraction = self.config.get('kelly_fraction', 0.25)
        self.max_bet_pct = self.config.get('max_bet_pct', 5.0)
        self.min_bet_pct = self.config.get('min_bet_pct', 0.5)
        self.max_bets_per_day = self.config.get('max_bets_per_day', 5)

    def calculate_ev(
        self,
        prob_model: float,
        odds_american: float
    ) -> Dict[str, float]:
        """
        Calculate Expected Value

        Args:
            prob_model: Model's predicted probability (0-1)
            odds_american: Market odds in American format

        Returns:
            Dict with EV metrics
        """
        # Convert American odds to decimal
        if odds_american < 0:
            decimal_odds = 1 + (100 / abs(odds_american))
        else:
            decimal_odds = 1 + (odds_american / 100)

        # Calculate EV
        ev = (prob_model * (decimal_odds - 1)) - (1 - prob_model)
        ev_pct = ev * 100

        # Implied probability from market
        prob_implied = american_to_prob(odds_american)

        # Edge (model prob - market prob)
        edge = prob_model - prob_implied

        return {
            'ev': ev,
            'ev_pct': ev_pct,
            'prob_model': prob_model,
            'prob_implied': prob_implied,
            'edge': edge,
            'decimal_odds': decimal_odds
        }

    def kelly_criterion(
        self,
        prob_win: float,
        decimal_odds: float,
        fraction: float = None
    ) -> float:
        """
        Calculate Kelly Criterion bet size

        Args:
            prob_win: Probability of winning (0-1)
            decimal_odds: Decimal odds
            fraction: Kelly fraction (default from config)

        Returns:
            Bet size as fraction of bankroll (0-1)
        """
        if fraction is None:
            fraction = self.kelly_fraction

        # Kelly formula: (bp - q) / b
        # where b = decimal_odds - 1, p = prob_win, q = 1 - prob_win
        b = decimal_odds - 1
        p = prob_win
        q = 1 - p

        kelly = (b * p - q) / b

        # Apply fraction and clamp
        kelly_fractional = kelly * fraction
        kelly_clamped = max(0, min(kelly_fractional, self.max_bet_pct / 100))

        return kelly_clamped

    def filter_bets(
        self,
        predictions_df: pd.DataFrame,
        bankroll: float = 10000
    ) -> pd.DataFrame:
        """
        Filter predictions to actionable bets

        Args:
            predictions_df: DataFrame with predictions and odds
            bankroll: Current bankroll

        Returns:
            DataFrame with filtered bets and bet sizes
        """
        # Calculate EV for all predictions
        predictions_df['ev_metrics'] = predictions_df.apply(
            lambda row: self.calculate_ev(
                row['prob_model'],
                row['odds_american']
            ),
            axis=1
        )

        # Expand EV metrics into columns
        ev_cols = pd.DataFrame(predictions_df['ev_metrics'].tolist())
        predictions_df = pd.concat([predictions_df, ev_cols], axis=1)

        # Apply filters
        mask = (
            (predictions_df['ev_pct'] >= self.min_ev_pct) &
            (predictions_df['ev_pct'] <= self.max_ev_pct) &
            (predictions_df['prob_model'] >= self.min_prob) &
            (predictions_df['prob_model'] <= self.max_prob)
        )

        filtered = predictions_df[mask].copy()

        if len(filtered) == 0:
            logger.info("No bets passed filters")
            return filtered

        # Calculate bet sizes using Kelly
        if self.use_kelly:
            filtered['kelly_fraction'] = filtered.apply(
                lambda row: self.kelly_criterion(
                    row['prob_model'],
                    row['decimal_odds']
                ),
                axis=1
            )
        else:
            # Fixed fractional betting
            filtered['kelly_fraction'] = self.min_bet_pct / 100

        # Convert to dollar amounts
        filtered['bet_amount'] = (filtered['kelly_fraction'] * bankroll).round(2)

        # Cap at max bet size
        max_bet = bankroll * (self.max_bet_pct / 100)
        filtered['bet_amount'] = filtered['bet_amount'].clip(upper=max_bet)

        # Limit number of bets per day
        filtered = filtered.nlargest(self.max_bets_per_day, 'ev_pct')

        # Sort by EV descending
        filtered = filtered.sort_values('ev_pct', ascending=False)

        logger.info(f"Found {len(filtered)} actionable bets")
        logger.info(f"Total exposure: ${filtered['bet_amount'].sum():.2f} ({filtered['bet_amount'].sum() / bankroll * 100:.1f}% of bankroll)")

        return filtered

    def generate_bet_card(
        self,
        filtered_bets: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Generate a bet card with recommendations

        Args:
            filtered_bets: DataFrame with filtered bets

        Returns:
            DataFrame formatted as bet card
        """
        if len(filtered_bets) == 0:
            return pd.DataFrame()

        bet_card = filtered_bets[[
            'game_id',
            'team',
            'market',
            'line',
            'odds_american',
            'prob_model',
            'prob_implied',
            'ev_pct',
            'edge',
            'bet_amount',
            'kelly_fraction'
        ]].copy()

        bet_card = bet_card.rename(columns={
            'prob_model': 'model_prob',
            'prob_implied': 'market_prob',
            'ev_pct': 'ev_%',
            'kelly_fraction': 'kelly_%'
        })

        # Round for display
        bet_card['model_prob'] = (bet_card['model_prob'] * 100).round(1)
        bet_card['market_prob'] = (bet_card['market_prob'] * 100).round(1)
        bet_card['ev_%'] = bet_card['ev_%'].round(2)
        bet_card['edge'] = (bet_card['edge'] * 100).round(2)
        bet_card['kelly_%'] = (bet_card['kelly_%'] * 100).round(2)

        return bet_card
