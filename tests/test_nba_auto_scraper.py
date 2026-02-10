"""
Tests for nba_auto_scraper.py - the Q1-only NBA scraper.

Focuses on differences from nba_nuevo.py (active flag check, Q1-only stats).
"""
import pytest
from unittest.mock import patch, MagicMock
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import nba_auto_scraper


class TestAutoScraperTeamAbbreviations:
    def test_all_30_teams_present(self):
        assert len(nba_auto_scraper.TEAM_ABBREVIATIONS) == 30

    def test_matches_nuevo_scraper_ids(self):
        """Both scrapers should have the same team ID mappings."""
        import nba_nuevo
        for abbr in nba_auto_scraper.TEAM_ABBREVIATIONS:
            assert abbr in nba_nuevo.TEAM_ABBREVIATIONS
            assert nba_auto_scraper.TEAM_ABBREVIATIONS[abbr][0] == nba_nuevo.TEAM_ABBREVIATIONS[abbr][0]


class TestAutoScraperGetBoxscoreTotals:
    @patch('nba_auto_scraper.requests.get')
    def test_includes_active_players_only(self, mock_get, boxscore_response):
        """nba_auto_scraper checks the 'active' flag on each player."""
        mock_response = MagicMock()
        mock_response.json.return_value = boxscore_response
        mock_get.return_value = mock_response

        result = nba_auto_scraper.get_boxscore_totals('123', '2')

        assert 'Jayson Tatum' in result
        assert 'Jaylen Brown' in result
        assert 'Injured Player' not in result

    @patch('nba_auto_scraper.requests.get')
    def test_filters_zero_minutes(self, mock_get, boxscore_response):
        """nba_auto_scraper now filters by both active flag AND minutes played."""
        mock_response = MagicMock()
        mock_response.json.return_value = boxscore_response
        mock_get.return_value = mock_response

        result = nba_auto_scraper.get_boxscore_totals('123', '2')
        # Bench Player is active=True but has 0 minutes - should be filtered out
        assert 'Bench Player' not in result

    @patch('nba_auto_scraper.requests.get')
    def test_handles_network_error(self, mock_get):
        mock_get.side_effect = Exception("Network error")
        result = nba_auto_scraper.get_boxscore_totals('123', '2')
        assert result == {}


class TestAutoScraperQ1Stats:
    @patch('nba_auto_scraper.requests.get')
    def test_only_extracts_q1(self, mock_get, playbyplay_response):
        mock_response = MagicMock()
        mock_response.json.return_value = playbyplay_response
        mock_get.return_value = mock_response

        result = nba_auto_scraper.get_q1_stats_from_playbyplay('123', '2')

        # Should have Q1 stats only
        if 'Jayson Tatum' in result:
            assert 'PTS_Q1' in result['Jayson Tatum']
            # Should NOT have Q2/Q3/Q4 keys
            assert 'PTS_Q2' not in result['Jayson Tatum']

    @patch('nba_auto_scraper.requests.get')
    def test_counts_q1_three_pointers(self, mock_get, playbyplay_response):
        mock_response = MagicMock()
        mock_response.json.return_value = playbyplay_response
        mock_get.return_value = mock_response

        result = nba_auto_scraper.get_q1_stats_from_playbyplay('123', '2')

        assert result['Jayson Tatum']['3PM_Q1'] == 1
        assert result['Jayson Tatum']['PTS_Q1'] == 5  # 3 + 2

    @patch('nba_auto_scraper.requests.get')
    def test_handles_network_error(self, mock_get):
        mock_get.side_effect = Exception("Timeout")
        result = nba_auto_scraper.get_q1_stats_from_playbyplay('123', '2')
        assert result == {}


class TestAutoScraperProcessTeam:
    @patch('nba_auto_scraper.get_q1_stats_from_playbyplay')
    @patch('nba_auto_scraper.get_boxscore_totals')
    @patch('nba_auto_scraper.get_team_schedule')
    @patch('nba_auto_scraper.time.sleep')
    def test_generates_csv_with_q1_columns(self, mock_sleep, mock_schedule, mock_boxscore, mock_q1, tmp_path):
        import pandas as pd

        mock_schedule.return_value = [{
            'game_id': '123', 'date': '2025-01-10',
            'home_team': 'Boston Celtics', 'away_team': 'Miami Heat'
        }]
        mock_boxscore.return_value = {
            'Jayson Tatum': {'PTS_TOTAL': 28, 'REB_TOTAL': 8, 'AST_TOTAL': 5, '3PM_TOTAL': 3}
        }
        mock_q1.return_value = {
            'Jayson Tatum': {'PTS_Q1': 10, 'REB_Q1': 2, 'AST_Q1': 1, '3PM_Q1': 2}
        }

        original_dir = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = nba_auto_scraper.process_team('BOS')
            assert result is True
            assert os.path.exists('BOS_last_5_games.csv')

            df = pd.read_csv('BOS_last_5_games.csv')
            # Should have Q1 and TOTAL columns but NOT Q2/Q3/Q4
            assert 'PTS_Q1' in df.columns
            assert 'PTS_TOTAL' in df.columns
            assert 'PTS_Q2' not in df.columns
        finally:
            os.chdir(original_dir)

    @patch('nba_auto_scraper.get_team_schedule')
    def test_returns_false_when_no_games(self, mock_schedule):
        mock_schedule.return_value = []
        result = nba_auto_scraper.process_team('BOS')
        assert result is False
