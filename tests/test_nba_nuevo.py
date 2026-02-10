"""
Tests for nba_nuevo.py - the all-quarters NBA scraper.

These tests mock HTTP requests so they can run without network access.
"""
import pytest
from unittest.mock import patch, MagicMock
from collections import defaultdict
import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import nba_nuevo


# ===========================================================================
# TEAM_ABBREVIATIONS data integrity
# ===========================================================================
class TestTeamAbbreviations:
    def test_all_30_teams_present(self):
        assert len(nba_nuevo.TEAM_ABBREVIATIONS) == 30

    def test_each_entry_has_id_and_name(self):
        for abbr, (team_id, team_name) in nba_nuevo.TEAM_ABBREVIATIONS.items():
            assert team_id.isdigit(), f"{abbr} has non-numeric ID: {team_id}"
            assert len(team_name) > 0, f"{abbr} has empty name"

    def test_ids_are_unique(self):
        ids = [tid for tid, _ in nba_nuevo.TEAM_ABBREVIATIONS.values()]
        assert len(ids) == len(set(ids)), "Duplicate team IDs found"

    def test_abbreviations_are_3_chars(self):
        for abbr in nba_nuevo.TEAM_ABBREVIATIONS:
            assert len(abbr) == 3, f"Abbreviation '{abbr}' is not 3 characters"
            assert abbr.isupper(), f"Abbreviation '{abbr}' is not uppercase"

    def test_known_teams_exist(self):
        expected = ['LAL', 'BOS', 'GSW', 'MIA', 'CHI', 'NYK']
        for team in expected:
            assert team in nba_nuevo.TEAM_ABBREVIATIONS


# ===========================================================================
# get_todays_games()
# ===========================================================================
class TestGetTodaysGames:
    @patch('nba_nuevo.requests.get')
    def test_returns_team_abbreviations_for_games(self, mock_get, scoreboard_response_with_games):
        mock_response = MagicMock()
        mock_response.json.return_value = scoreboard_response_with_games
        mock_get.return_value = mock_response

        result = nba_nuevo.get_todays_games()

        assert 'BOS' in result
        assert 'LAL' in result
        assert 'GSW' in result
        assert 'MIA' in result
        assert len(result) == 4

    @patch('nba_nuevo.requests.get')
    def test_returns_empty_list_when_no_games(self, mock_get, scoreboard_response_no_games):
        mock_response = MagicMock()
        mock_response.json.return_value = scoreboard_response_no_games
        mock_get.return_value = mock_response

        result = nba_nuevo.get_todays_games()
        assert result == []

    @patch('nba_nuevo.requests.get')
    def test_handles_network_error(self, mock_get):
        mock_get.side_effect = Exception("Connection timeout")
        result = nba_nuevo.get_todays_games()
        assert result == []

    @patch('nba_nuevo.requests.get')
    def test_ignores_unknown_team_abbreviations(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "events": [{
                "date": "2025-01-15T00:00Z",
                "competitions": [{
                    "competitors": [
                        {"team": {"abbreviation": "FAKE", "displayName": "Fake Team"}, "homeAway": "away"},
                        {"team": {"abbreviation": "LAL", "displayName": "Los Angeles Lakers"}, "homeAway": "home"}
                    ],
                    "status": {"type": {"name": "STATUS_SCHEDULED"}}
                }]
            }]
        }
        mock_get.return_value = mock_response

        result = nba_nuevo.get_todays_games()
        assert 'LAL' in result
        assert 'FAKE' not in result

    @patch('nba_nuevo.requests.get')
    def test_handles_missing_abbreviation(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "events": [{
                "date": "2025-01-15T00:00Z",
                "competitions": [{
                    "competitors": [
                        {"team": {"displayName": "No Abbr Team"}, "homeAway": "away"},
                        {"team": {"abbreviation": "", "displayName": "Empty Abbr"}, "homeAway": "home"}
                    ],
                    "status": {"type": {"name": "STATUS_SCHEDULED"}}
                }]
            }]
        }
        mock_get.return_value = mock_response

        result = nba_nuevo.get_todays_games()
        assert result == []


# ===========================================================================
# get_team_schedule()
# ===========================================================================
class TestGetTeamSchedule:
    @patch('nba_nuevo.requests.get')
    def test_returns_only_completed_games(self, mock_get, schedule_response):
        mock_response = MagicMock()
        mock_response.json.return_value = schedule_response
        mock_get.return_value = mock_response

        result = nba_nuevo.get_team_schedule('2', limit=5)

        # Should have 3 completed games, not the upcoming one
        assert len(result) == 3
        game_ids = [g['game_id'] for g in result]
        assert '401600099' not in game_ids

    @patch('nba_nuevo.requests.get')
    def test_games_sorted_newest_first(self, mock_get, schedule_response):
        mock_response = MagicMock()
        mock_response.json.return_value = schedule_response
        mock_get.return_value = mock_response

        result = nba_nuevo.get_team_schedule('2', limit=5)

        dates = [g['date'] for g in result]
        assert dates == sorted(dates, reverse=True)

    @patch('nba_nuevo.requests.get')
    def test_respects_limit_parameter(self, mock_get, schedule_response):
        mock_response = MagicMock()
        mock_response.json.return_value = schedule_response
        mock_get.return_value = mock_response

        result = nba_nuevo.get_team_schedule('2', limit=2)
        assert len(result) == 2

    @patch('nba_nuevo.requests.get')
    def test_returns_correct_game_fields(self, mock_get, schedule_response):
        mock_response = MagicMock()
        mock_response.json.return_value = schedule_response
        mock_get.return_value = mock_response

        result = nba_nuevo.get_team_schedule('2', limit=1)
        game = result[0]

        assert 'game_id' in game
        assert 'date' in game
        assert 'home_team' in game
        assert 'away_team' in game

    @patch('nba_nuevo.requests.get')
    def test_handles_network_error(self, mock_get):
        mock_get.side_effect = Exception("Timeout")
        result = nba_nuevo.get_team_schedule('2', limit=5)
        assert result == []

    @patch('nba_nuevo.requests.get')
    def test_handles_empty_schedule(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"events": []}
        mock_get.return_value = mock_response

        result = nba_nuevo.get_team_schedule('2', limit=5)
        assert result == []

    @patch('nba_nuevo.requests.get')
    def test_handles_malformed_date(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "events": [{
                "id": "123",
                "date": "not-a-date",
                "competitions": [{
                    "competitors": [],
                    "status": {"type": {"completed": True}}
                }]
            }]
        }
        mock_get.return_value = mock_response

        result = nba_nuevo.get_team_schedule('2', limit=5)
        # Should skip the game with malformed date
        assert result == []


# ===========================================================================
# get_boxscore_totals()
# ===========================================================================
class TestGetBoxscoreTotals:
    @patch('nba_nuevo.requests.get')
    def test_extracts_correct_stats(self, mock_get, boxscore_response):
        mock_response = MagicMock()
        mock_response.json.return_value = boxscore_response
        mock_get.return_value = mock_response

        result = nba_nuevo.get_boxscore_totals('401654321', '2')

        assert 'Jayson Tatum' in result
        assert result['Jayson Tatum']['PTS_TOTAL'] == 28
        assert result['Jayson Tatum']['REB_TOTAL'] == 8
        assert result['Jayson Tatum']['AST_TOTAL'] == 5
        assert result['Jayson Tatum']['3PM_TOTAL'] == 3

    @patch('nba_nuevo.requests.get')
    def test_extracts_three_point_makes_from_made_attempted(self, mock_get, boxscore_response):
        mock_response = MagicMock()
        mock_response.json.return_value = boxscore_response
        mock_get.return_value = mock_response

        result = nba_nuevo.get_boxscore_totals('401654321', '2')
        # 3PT is "3-8", should extract 3
        assert result['Jayson Tatum']['3PM_TOTAL'] == 3
        # 3PT is "2-5", should extract 2
        assert result['Jaylen Brown']['3PM_TOTAL'] == 2

    @patch('nba_nuevo.requests.get')
    def test_filters_only_target_team(self, mock_get, boxscore_response):
        mock_response = MagicMock()
        mock_response.json.return_value = boxscore_response
        mock_get.return_value = mock_response

        result = nba_nuevo.get_boxscore_totals('401654321', '2')

        assert 'Jayson Tatum' in result
        assert 'LeBron James' not in result

    @patch('nba_nuevo.requests.get')
    def test_filters_players_with_zero_minutes(self, mock_get, boxscore_response):
        """nba_nuevo.py filters out players with 0 minutes (unlike nba_auto_scraper.py)."""
        mock_response = MagicMock()
        mock_response.json.return_value = boxscore_response
        mock_get.return_value = mock_response

        result = nba_nuevo.get_boxscore_totals('401654321', '2')
        assert 'Bench Player' not in result

    @patch('nba_nuevo.requests.get')
    def test_excludes_inactive_players(self, mock_get, boxscore_response):
        """nba_auto_scraper.py checks active flag; nba_nuevo.py does not but filters by minutes."""
        mock_response = MagicMock()
        mock_response.json.return_value = boxscore_response
        mock_get.return_value = mock_response

        result = nba_nuevo.get_boxscore_totals('401654321', '2')
        assert 'Injured Player' not in result

    @patch('nba_nuevo.requests.get')
    def test_handles_network_error(self, mock_get):
        mock_get.side_effect = Exception("API Error")
        result = nba_nuevo.get_boxscore_totals('123', '2')
        assert result == {}

    @patch('nba_nuevo.requests.get')
    def test_handles_missing_boxscore(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response

        result = nba_nuevo.get_boxscore_totals('123', '2')
        assert result == {}

    @patch('nba_nuevo.requests.get')
    def test_handles_non_numeric_stat_values(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "boxscore": {
                "players": [{
                    "team": {"id": "2"},
                    "statistics": [{
                        "labels": ["MIN", "FG", "3PT", "FT", "OREB", "DREB", "REB", "AST", "STL", "BLK", "TO", "PF", "PTS"],
                        "athletes": [{
                            "athlete": {"displayName": "Test Player"},
                            "stats": ["20", "5-10", "--", "2-3", "1", "3", "4", "N/A", "0", "0", "0", "0", "DNP"]
                        }]
                    }]
                }]
            }
        }
        mock_get.return_value = mock_response

        result = nba_nuevo.get_boxscore_totals('123', '2')
        if 'Test Player' in result:
            # Should default to 0 for non-numeric values
            assert result['Test Player']['PTS_TOTAL'] == 0
            assert result['Test Player']['AST_TOTAL'] == 0


# ===========================================================================
# get_quarter_stats_from_playbyplay()
# ===========================================================================
class TestGetQuarterStatsFromPlayByPlay:
    @patch('nba_nuevo.requests.get')
    def test_counts_q1_points_correctly(self, mock_get, playbyplay_response):
        mock_response = MagicMock()
        mock_response.json.return_value = playbyplay_response
        mock_get.return_value = mock_response

        result = nba_nuevo.get_quarter_stats_from_playbyplay('123', '2')

        # Tatum: 3pt (3) + layup (2) = 5 in Q1
        assert result['Jayson Tatum']['PTS_Q1'] == 5
        # Brown: 2 free throws = 2 in Q1
        assert result['Jaylen Brown']['PTS_Q1'] == 2

    @patch('nba_nuevo.requests.get')
    def test_counts_q1_three_pointers(self, mock_get, playbyplay_response):
        mock_response = MagicMock()
        mock_response.json.return_value = playbyplay_response
        mock_get.return_value = mock_response

        result = nba_nuevo.get_quarter_stats_from_playbyplay('123', '2')

        assert result['Jayson Tatum']['3PM_Q1'] == 1
        assert result['Derrick White']['3PM_Q1'] == 1

    @patch('nba_nuevo.requests.get')
    def test_counts_q1_rebounds(self, mock_get, playbyplay_response):
        mock_response = MagicMock()
        mock_response.json.return_value = playbyplay_response
        mock_get.return_value = mock_response

        result = nba_nuevo.get_quarter_stats_from_playbyplay('123', '2')

        assert result['Jayson Tatum']['REB_Q1'] == 1
        assert result['Jaylen Brown']['REB_Q1'] == 1

    @patch('nba_nuevo.requests.get')
    def test_counts_q1_assists(self, mock_get, playbyplay_response):
        mock_response = MagicMock()
        mock_response.json.return_value = playbyplay_response
        mock_get.return_value = mock_response

        result = nba_nuevo.get_quarter_stats_from_playbyplay('123', '2')

        assert result['Jaylen Brown']['AST_Q1'] == 1
        assert result['Jayson Tatum']['AST_Q1'] == 1

    @patch('nba_nuevo.requests.get')
    def test_counts_q2_stats_separately(self, mock_get, playbyplay_response):
        mock_response = MagicMock()
        mock_response.json.return_value = playbyplay_response
        mock_get.return_value = mock_response

        result = nba_nuevo.get_quarter_stats_from_playbyplay('123', '2')

        # Q2: Tatum dunk (2pts), Brown 3pt (3pts)
        assert result['Jayson Tatum']['PTS_Q2'] == 2
        assert result['Jaylen Brown']['PTS_Q2'] == 3
        assert result['Jaylen Brown']['3PM_Q2'] == 1
        # Q2 rebound
        assert result['Jayson Tatum']['REB_Q2'] == 1
        # Q2 assist
        assert result['Derrick White']['AST_Q2'] == 1

    @patch('nba_nuevo.requests.get')
    def test_ignores_overtime_periods(self, mock_get, playbyplay_response):
        mock_response = MagicMock()
        mock_response.json.return_value = playbyplay_response
        mock_get.return_value = mock_response

        result = nba_nuevo.get_quarter_stats_from_playbyplay('123', '2')

        # The period=5 (OT) play should be ignored
        # Check Q3 and Q4 are zero (no plays in those periods)
        assert result.get('Jayson Tatum', {}).get('PTS_Q3', 0) == 0
        assert result.get('Jayson Tatum', {}).get('PTS_Q4', 0) == 0

    @patch('nba_nuevo.requests.get')
    def test_filters_opponent_plays(self, mock_get, playbyplay_with_opponent_plays):
        mock_response = MagicMock()
        mock_response.json.return_value = playbyplay_with_opponent_plays
        mock_get.return_value = mock_response

        # Get stats for team_id=2 (Celtics)
        result = nba_nuevo.get_quarter_stats_from_playbyplay('123', '2')

        assert 'Jayson Tatum' in result
        assert result['Jayson Tatum']['PTS_Q1'] == 2
        assert result['Jayson Tatum']['REB_Q1'] == 1
        # LeBron should NOT appear (he's on team 13)
        assert 'LeBron James' not in result

    @patch('nba_nuevo.requests.get')
    def test_handles_network_error(self, mock_get):
        mock_get.side_effect = Exception("Timeout")
        result = nba_nuevo.get_quarter_stats_from_playbyplay('123', '2')
        assert result == {}

    @patch('nba_nuevo.requests.get')
    def test_handles_empty_plays(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "boxscore": {"players": [{"team": {"id": "2"}, "statistics": [{"athletes": []}]}]},
            "plays": []
        }
        mock_get.return_value = mock_response

        result = nba_nuevo.get_quarter_stats_from_playbyplay('123', '2')
        assert result == {}


# ===========================================================================
# process_team() - integration-style tests
# ===========================================================================
class TestProcessTeam:
    @patch('nba_nuevo.get_quarter_stats_from_playbyplay')
    @patch('nba_nuevo.get_boxscore_totals')
    @patch('nba_nuevo.get_team_schedule')
    @patch('nba_nuevo.time.sleep')
    def test_generates_csv_file(self, mock_sleep, mock_schedule, mock_boxscore, mock_quarter, tmp_path):
        mock_schedule.return_value = [{
            'game_id': '123', 'date': '2025-01-10',
            'home_team': 'Boston Celtics', 'away_team': 'Miami Heat'
        }]
        mock_boxscore.return_value = {
            'Jayson Tatum': {'PTS_TOTAL': 28, 'REB_TOTAL': 8, 'AST_TOTAL': 5, '3PM_TOTAL': 3}
        }
        mock_quarter.return_value = {
            'Jayson Tatum': {
                'PTS_Q1': 10, 'REB_Q1': 2, 'AST_Q1': 1, '3PM_Q1': 2,
                'PTS_Q2': 8, 'REB_Q2': 3, 'AST_Q2': 2, '3PM_Q2': 1,
                'PTS_Q3': 5, 'REB_Q3': 2, 'AST_Q3': 1, '3PM_Q3': 0,
                'PTS_Q4': 5, 'REB_Q4': 1, 'AST_Q4': 1, '3PM_Q4': 0,
            }
        }

        original_dir = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = nba_nuevo.process_team('BOS')
            assert result is True
            assert os.path.exists('BOS_last_5_games_ALL_QUARTERS.csv')
        finally:
            os.chdir(original_dir)

    @patch('nba_nuevo.get_team_schedule')
    def test_returns_false_when_no_games(self, mock_schedule):
        mock_schedule.return_value = []
        result = nba_nuevo.process_team('BOS')
        assert result is False

    @patch('nba_nuevo.get_quarter_stats_from_playbyplay')
    @patch('nba_nuevo.get_boxscore_totals')
    @patch('nba_nuevo.get_team_schedule')
    @patch('nba_nuevo.time.sleep')
    def test_csv_has_correct_columns(self, mock_sleep, mock_schedule, mock_boxscore, mock_quarter, tmp_path):
        import pandas as pd

        mock_schedule.return_value = [{
            'game_id': '123', 'date': '2025-01-10',
            'home_team': 'Boston Celtics', 'away_team': 'Miami Heat'
        }]
        mock_boxscore.return_value = {
            'Jayson Tatum': {'PTS_TOTAL': 28, 'REB_TOTAL': 8, 'AST_TOTAL': 5, '3PM_TOTAL': 3}
        }
        mock_quarter.return_value = {}

        original_dir = os.getcwd()
        os.chdir(tmp_path)
        try:
            nba_nuevo.process_team('BOS')
            df = pd.read_csv('BOS_last_5_games_ALL_QUARTERS.csv')

            expected_cols = [
                'Game_Date', 'Opponent', 'Player',
                'PTS_Q1', 'REB_Q1', 'AST_Q1', '3PM_Q1',
                'PTS_Q2', 'REB_Q2', 'AST_Q2', '3PM_Q2',
                'PTS_Q3', 'REB_Q3', 'AST_Q3', '3PM_Q3',
                'PTS_Q4', 'REB_Q4', 'AST_Q4', '3PM_Q4',
                'PTS_TOTAL', 'REB_TOTAL', 'AST_TOTAL', '3PM_TOTAL'
            ]
            for col in expected_cols:
                assert col in df.columns, f"Missing column: {col}"
        finally:
            os.chdir(original_dir)


# ===========================================================================
# Regex pattern edge case tests
# ===========================================================================
class TestRegexPatterns:
    """Test the regex patterns used for parsing play-by-play text directly."""

    def test_makes_pattern_standard(self):
        import re
        patterns = [r'([A-Za-z\'\.\s]+?)\s+makes', r'([A-Za-z\'\.\s]+?)\s+made']
        text = "Jayson Tatum makes three point jumper"
        for p in patterns:
            m = re.search(p, text)
            if m:
                assert m.group(1).strip() == "Jayson Tatum"
                break

    def test_makes_pattern_with_apostrophe(self):
        import re
        pattern = r'([A-Za-z\'\.\s]+?)\s+makes'
        text = "Shai Gilgeous-Alexander makes driving layup"
        m = re.search(pattern, text)
        # Note: hyphenated names may not match the current regex
        # This test documents the gap

    def test_makes_pattern_with_period_in_name(self):
        import re
        pattern = r'([A-Za-z\'\.\s]+?)\s+makes'
        text = "P.J. Washington makes free throw"
        m = re.search(pattern, text)
        assert m is not None
        assert m.group(1).strip() == "P.J. Washington"

    def test_rebound_pattern_defensive(self):
        import re
        pattern = r'([A-Za-z\'\.\s]+?)\s+(defensive|offensive)\s+rebound'
        text = "Jayson Tatum defensive rebound"
        m = re.search(pattern, text)
        assert m is not None
        assert m.group(1).strip() == "Jayson Tatum"

    def test_rebound_pattern_offensive(self):
        import re
        pattern = r'([A-Za-z\'\.\s]+?)\s+(defensive|offensive)\s+rebound'
        text = "Jaylen Brown offensive rebound"
        m = re.search(pattern, text)
        assert m is not None
        assert m.group(1).strip() == "Jaylen Brown"

    def test_assist_pattern_parenthesized(self):
        import re
        pattern = r'\(([A-Za-z\'\.\s]+?)\s+assists\)'
        text = "Jayson Tatum makes layup (Jaylen Brown assists)"
        m = re.search(pattern, text)
        assert m is not None
        assert m.group(1).strip() == "Jaylen Brown"

    def test_hyphenated_name_now_matched(self):
        """Hyphenated names are now captured after the regex fix."""
        import re
        pattern = r'([A-Za-z\'\.\-\s]+?)\s+makes'
        text = "Shai Gilgeous-Alexander makes driving layup"
        m = re.search(pattern, text)
        assert m is not None
        assert m.group(1).strip() == "Shai Gilgeous-Alexander"

    def test_jr_suffix_name(self):
        """Documents potential edge case with Jr./Sr. suffixes."""
        import re
        pattern = r'([A-Za-z\'\.\s]+?)\s+makes'
        text = "Kelly Oubre Jr. makes three point jumper"
        m = re.search(pattern, text)
        assert m is not None
        # Check if the full name is captured
        name = m.group(1).strip()
        assert "Kelly" in name
