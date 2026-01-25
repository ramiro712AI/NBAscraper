"""
Tests for betting strategy module
"""

import pytest
import pandas as pd

from src.betting.strategy import BettingStrategy
from src.ingest.odds_data import american_to_prob, prob_to_american


class TestOddsConversion:
    """Test odds conversion functions"""

    def test_american_to_prob_negative(self):
        """Test conversion of negative American odds"""
        # -110 should be ~52.4% implied prob
        prob = american_to_prob(-110)
        assert 0.52 < prob < 0.53

    def test_american_to_prob_positive(self):
        """Test conversion of positive American odds"""
        # +150 should be 40% implied prob
        prob = american_to_prob(+150)
        assert 0.39 < prob < 0.41

    def test_american_to_prob_even(self):
        """Test conversion of even odds (+100)"""
        prob = american_to_prob(+100)
        assert prob == 0.5

    def test_prob_to_american_favorite(self):
        """Test conversion of high probability to negative odds"""
        odds = prob_to_american(0.6)
        assert odds < 0  # Should be negative
        assert -200 < odds < -100

    def test_prob_to_american_underdog(self):
        """Test conversion of low probability to positive odds"""
        odds = prob_to_american(0.4)
        assert odds > 0  # Should be positive
        assert 100 < odds < 200

    def test_roundtrip_conversion(self):
        """Test that conversion is reversible"""
        original_odds = -150
        prob = american_to_prob(original_odds)
        converted_odds = prob_to_american(prob)
        assert abs(original_odds - converted_odds) < 1  # Within 1 unit


class TestEVCalculation:
    """Test Expected Value calculations"""

    def setup_method(self):
        """Setup before each test"""
        self.strategy = BettingStrategy()

    def test_positive_ev(self):
        """Test calculation of positive EV"""
        # Model thinks 60% win, market says -110 (52.4%)
        result = self.strategy.calculate_ev(prob_model=0.60, odds_american=-110)

        assert result['ev'] > 0
        assert result['ev_pct'] > 0
        assert result['edge'] > 0  # Model prob > market prob

    def test_negative_ev(self):
        """Test calculation of negative EV"""
        # Model thinks 45% win, market says -110 (52.4%)
        result = self.strategy.calculate_ev(prob_model=0.45, odds_american=-110)

        assert result['ev'] < 0
        assert result['ev_pct'] < 0
        assert result['edge'] < 0  # Model prob < market prob

    def test_break_even(self):
        """Test EV at break-even point"""
        # Model matches market
        result = self.strategy.calculate_ev(prob_model=0.524, odds_american=-110)

        assert abs(result['ev']) < 0.01  # Nearly zero
        assert abs(result['edge']) < 0.01


class TestKellyCriterion:
    """Test Kelly Criterion bet sizing"""

    def setup_method(self):
        """Setup before each test"""
        self.strategy = BettingStrategy()

    def test_kelly_positive_edge(self):
        """Test Kelly with positive edge"""
        # 60% win prob, -110 odds
        kelly = self.strategy.kelly_criterion(prob_win=0.60, decimal_odds=1.909)

        assert kelly > 0  # Should bet
        assert kelly < 0.05  # Should be small (fractional Kelly)

    def test_kelly_no_edge(self):
        """Test Kelly with no edge"""
        # Fair odds
        kelly = self.strategy.kelly_criterion(prob_win=0.5, decimal_odds=2.0)

        assert kelly == 0  # Should not bet

    def test_kelly_clamping(self):
        """Test that Kelly is clamped to max bet%"""
        # Extreme edge
        kelly = self.strategy.kelly_criterion(prob_win=0.99, decimal_odds=2.0)

        max_bet = self.strategy.max_bet_pct / 100
        assert kelly <= max_bet  # Should not exceed max

    def test_kelly_fraction(self):
        """Test that Kelly fraction is applied"""
        kelly_full = self.strategy.kelly_criterion(
            prob_win=0.60,
            decimal_odds=1.909,
            fraction=1.0
        )

        kelly_quarter = self.strategy.kelly_criterion(
            prob_win=0.60,
            decimal_odds=1.909,
            fraction=0.25
        )

        assert kelly_quarter == pytest.approx(kelly_full * 0.25, rel=0.01)


class TestBettingFilters:
    """Test bet filtering logic"""

    def setup_method(self):
        """Setup before each test"""
        self.strategy = BettingStrategy()

    def test_filter_minimum_ev(self):
        """Test that bets below min EV are filtered"""
        # Create predictions with low EV
        predictions = pd.DataFrame({
            'game_id': ['game1'],
            'team': ['Lakers'],
            'market': ['moneyline'],
            'line': ['-'],
            'odds_american': [-110],
            'prob_model': [0.53]  # Just slightly above market (52.4%)
        })

        filtered = self.strategy.filter_bets(predictions, bankroll=10000)

        # Should be filtered out (EV too low)
        assert len(filtered) == 0

    def test_filter_probability_range(self):
        """Test that extreme probabilities are filtered"""
        # Create predictions with extreme probabilities
        predictions = pd.DataFrame({
            'game_id': ['game1', 'game2'],
            'team': ['Lakers', 'Celtics'],
            'market': ['moneyline', 'moneyline'],
            'line': ['-', '-'],
            'odds_american': [+500, -1000],
            'prob_model': [0.35, 0.95]  # Longshot and heavy favorite
        })

        filtered = self.strategy.filter_bets(predictions, bankroll=10000)

        # Should filter out both (outside prob range)
        assert len(filtered) == 0

    def test_filter_accepts_good_bets(self):
        """Test that good bets pass filters"""
        # Create predictions with good EV and prob range
        predictions = pd.DataFrame({
            'game_id': ['game1'],
            'team': ['Lakers'],
            'market': ['moneyline'],
            'line': ['-'],
            'odds_american': [-110],
            'prob_model': [0.60]  # 60% vs 52.4% market
        })

        filtered = self.strategy.filter_bets(predictions, bankroll=10000)

        # Should pass filters
        assert len(filtered) == 1
        assert filtered.iloc[0]['prob_model'] == 0.60

    def test_max_bets_limit(self):
        """Test that max bets per day is enforced"""
        # Create more predictions than max_bets_per_day
        n_bets = self.strategy.max_bets_per_day + 5

        predictions = pd.DataFrame({
            'game_id': [f'game{i}' for i in range(n_bets)],
            'team': [f'Team{i}' for i in range(n_bets)],
            'market': ['moneyline'] * n_bets,
            'line': ['-'] * n_bets,
            'odds_american': [-110] * n_bets,
            'prob_model': [0.60] * n_bets  # All good bets
        })

        filtered = self.strategy.filter_bets(predictions, bankroll=10000)

        # Should be limited to max_bets_per_day
        assert len(filtered) <= self.strategy.max_bets_per_day


def test_bet_card_generation():
    """Test bet card formatting"""
    strategy = BettingStrategy()

    # Create sample filtered bets
    filtered_bets = pd.DataFrame({
        'game_id': ['game1'],
        'team': ['Lakers'],
        'market': ['moneyline'],
        'line': ['-'],
        'odds_american': [-110],
        'prob_model': [0.60],
        'prob_implied': [0.524],
        'ev_pct': [5.2],
        'edge': [0.076],
        'bet_amount': [125.0],
        'kelly_fraction': [0.0125]
    })

    bet_card = strategy.generate_bet_card(filtered_bets)

    # Check that bet card has expected columns
    assert 'model_prob' in bet_card.columns
    assert 'market_prob' in bet_card.columns
    assert 'ev_%' in bet_card.columns
    assert 'bet_amount' in bet_card.columns

    # Check that values are formatted correctly
    assert bet_card.iloc[0]['model_prob'] == 60.0  # Converted to %
    assert bet_card.iloc[0]['market_prob'] == pytest.approx(52.4, rel=0.1)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
