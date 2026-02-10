"""
Tests for nba_pro_betting.py - the professional betting analysis script.
"""
import pytest
from unittest.mock import patch, MagicMock
import os
import sys
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import nba_pro_betting


# ===========================================================================
# Color assignment
# ===========================================================================
class TestUniqueColors:
    def setup_method(self):
        """Reset color state before each test."""
        nba_pro_betting._color_index = 0
        nba_pro_betting._assigned_colors = {}

    def test_same_player_gets_same_color(self):
        c1 = nba_pro_betting.get_unique_color("LeBron James")
        c2 = nba_pro_betting.get_unique_color("LeBron James")
        assert c1 == c2

    def test_different_players_get_different_colors(self):
        c1 = nba_pro_betting.get_unique_color("LeBron James")
        c2 = nba_pro_betting.get_unique_color("Stephen Curry")
        c3 = nba_pro_betting.get_unique_color("Kevin Durant")
        assert c1 != c2
        assert c2 != c3
        assert c1 != c3

    def test_colors_are_valid_hex(self):
        color = nba_pro_betting.get_unique_color("Test Player")
        assert color.startswith('#')
        assert len(color) == 7

    def test_many_players_never_repeat(self):
        colors = set()
        for i in range(50):
            c = nba_pro_betting.get_unique_color(f"Player {i}")
            colors.add(c)
        # All 50 players should have unique colors
        assert len(colors) == 50


# ===========================================================================
# Betting metrics
# ===========================================================================
class TestFindClosestLine:
    def test_exact_match(self):
        assert nba_pro_betting.find_closest_line(24.5, [19.5, 24.5, 29.5]) == 24.5

    def test_rounds_to_nearest(self):
        # 26.0 is closer to 24.5 (1.5 away) than 29.5 (3.5 away)
        assert nba_pro_betting.find_closest_line(26.0, [19.5, 24.5, 29.5]) == 24.5

    def test_low_value(self):
        assert nba_pro_betting.find_closest_line(5.0, [9.5, 14.5, 19.5]) == 9.5

    def test_empty_lines(self):
        assert nba_pro_betting.find_closest_line(25.0, []) == 25.0


class TestHitRate:
    def test_all_over(self):
        assert nba_pro_betting.calculate_hit_rate([30, 28, 25, 32, 27], 24.5) == 100.0

    def test_all_under(self):
        assert nba_pro_betting.calculate_hit_rate([10, 12, 8, 15, 11], 24.5) == 0.0

    def test_mixed(self):
        result = nba_pro_betting.calculate_hit_rate([30, 20, 28, 15, 25], 24.5)
        assert result == 60.0  # 3 out of 5

    def test_exact_line_counts_as_under(self):
        # Equal to line = NOT over
        assert nba_pro_betting.calculate_hit_rate([25], 24.5) == 100.0
        assert nba_pro_betting.calculate_hit_rate([24], 24.5) == 0.0

    def test_empty_values(self):
        assert nba_pro_betting.calculate_hit_rate([], 24.5) == 0.0


class TestTrend:
    def test_increasing_values(self):
        trend, slope = nba_pro_betting.calculate_trend([10, 15, 20, 25, 30])
        assert trend == 'UP'
        assert slope > 0

    def test_decreasing_values(self):
        trend, slope = nba_pro_betting.calculate_trend([30, 25, 20, 15, 10])
        assert trend == 'DOWN'
        assert slope < 0

    def test_stable_values(self):
        trend, slope = nba_pro_betting.calculate_trend([20, 20, 20, 20, 20])
        assert trend == 'STABLE'

    def test_single_value(self):
        trend, slope = nba_pro_betting.calculate_trend([25])
        assert trend == 'STABLE'

    def test_slightly_varying(self):
        trend, slope = nba_pro_betting.calculate_trend([20, 21, 20, 21, 20])
        assert trend == 'STABLE'


class TestConsistency:
    def test_perfectly_consistent(self):
        result = nba_pro_betting.calculate_consistency([25, 25, 25, 25, 25])
        assert result == 100.0

    def test_highly_variable(self):
        result = nba_pro_betting.calculate_consistency([5, 40, 8, 35, 10])
        assert result < 50

    def test_moderate_consistency(self):
        result = nba_pro_betting.calculate_consistency([24, 26, 25, 23, 27])
        assert result > 80

    def test_single_value(self):
        result = nba_pro_betting.calculate_consistency([25])
        assert result == 100.0

    def test_empty(self):
        result = nba_pro_betting.calculate_consistency([])
        assert result == 100.0

    def test_all_zeros(self):
        result = nba_pro_betting.calculate_consistency([0, 0, 0])
        assert result == 100.0


class TestStdDev:
    def test_no_variation(self):
        assert nba_pro_betting.calculate_std_dev([20, 20, 20]) == 0.0

    def test_known_values(self):
        result = nba_pro_betting.calculate_std_dev([10, 20, 30])
        expected = round(math.sqrt(200 / 3), 2)
        assert result == expected

    def test_single_value(self):
        assert nba_pro_betting.calculate_std_dev([25]) == 0.0


# ===========================================================================
# extract_boxscore_totals
# ===========================================================================
class TestExtractBoxscoreTotals:
    def test_extracts_players_with_minutes(self):
        data = {
            "boxscore": {
                "players": [{
                    "team": {"id": "2"},
                    "statistics": [{
                        "labels": ["MIN", "FG", "3PT", "FT", "OREB", "DREB", "REB", "AST", "STL", "BLK", "TO", "PF", "PTS"],
                        "athletes": [
                            {
                                "starter": True,
                                "athlete": {"displayName": "Jayson Tatum"},
                                "stats": ["36", "10-20", "3-8", "5-6", "1", "7", "8", "5", "1", "0", "2", "3", "28"]
                            },
                            {
                                "athlete": {"displayName": "Bench Guy"},
                                "stats": ["0", "0-0", "0-0", "0-0", "0", "0", "0", "0", "0", "0", "0", "0", "0"]
                            }
                        ]
                    }]
                }]
            }
        }

        result = nba_pro_betting.extract_boxscore_totals(data, '2')

        assert 'Jayson Tatum' in result
        assert 'Bench Guy' not in result
        assert result['Jayson Tatum']['PTS_TOTAL'] == 28
        assert result['Jayson Tatum']['MIN'] == 36
        assert result['Jayson Tatum']['STARTER'] is True

    def test_filters_wrong_team(self):
        data = {
            "boxscore": {
                "players": [{
                    "team": {"id": "13"},
                    "statistics": [{
                        "labels": ["MIN", "PTS"],
                        "athletes": [{
                            "athlete": {"displayName": "LeBron James"},
                            "stats": ["38", "30"]
                        }]
                    }]
                }]
            }
        }

        result = nba_pro_betting.extract_boxscore_totals(data, '2')
        assert result == {}

    def test_handles_colon_minutes_format(self):
        data = {
            "boxscore": {
                "players": [{
                    "team": {"id": "2"},
                    "statistics": [{
                        "labels": ["MIN", "FG", "3PT", "FT", "OREB", "DREB", "REB", "AST", "STL", "BLK", "TO", "PF", "PTS"],
                        "athletes": [{
                            "athlete": {"displayName": "Test Player"},
                            "stats": ["36:20", "5-10", "2-5", "3-4", "1", "4", "5", "3", "1", "0", "1", "2", "15"]
                        }]
                    }]
                }]
            }
        }

        result = nba_pro_betting.extract_boxscore_totals(data, '2')
        assert result['Test Player']['MIN'] == 36


# ===========================================================================
# extract_quarter_stats - hyphenated names
# ===========================================================================
class TestExtractQuarterStats:
    def test_captures_hyphenated_names(self):
        data = {
            "boxscore": {
                "players": [{
                    "team": {"id": "25"},
                    "statistics": [{
                        "athletes": [
                            {"athlete": {"displayName": "Shai Gilgeous-Alexander"}},
                        ]
                    }]
                }]
            },
            "plays": [
                {"period": {"number": 1}, "text": "Shai Gilgeous-Alexander makes driving layup", "scoringPlay": True},
                {"period": {"number": 1}, "text": "Shai Gilgeous-Alexander defensive rebound", "scoringPlay": False},
                {"period": {"number": 2}, "text": "Shai Gilgeous-Alexander makes three point jumper (Jalen Williams assists)", "scoringPlay": True},
            ]
        }

        result = nba_pro_betting.extract_quarter_stats(data, '25')
        assert 'Shai Gilgeous-Alexander' in result
        assert result['Shai Gilgeous-Alexander']['PTS_Q1'] == 2
        assert result['Shai Gilgeous-Alexander']['REB_Q1'] == 1
        assert result['Shai Gilgeous-Alexander']['PTS_Q2'] == 3

    def test_overtime_goes_to_ot_bucket(self):
        data = {
            "boxscore": {
                "players": [{
                    "team": {"id": "2"},
                    "statistics": [{
                        "athletes": [
                            {"athlete": {"displayName": "Jayson Tatum"}},
                        ]
                    }]
                }]
            },
            "plays": [
                {"period": {"number": 5}, "text": "Jayson Tatum makes free throw", "scoringPlay": True},
                {"period": {"number": 5}, "text": "Jayson Tatum makes driving layup", "scoringPlay": True},
            ]
        }

        result = nba_pro_betting.extract_quarter_stats(data, '2')
        assert result['Jayson Tatum']['PTS_OT'] == 3  # 1 FT + 2 layup

    def test_filters_opponent_plays(self):
        data = {
            "boxscore": {
                "players": [
                    {"team": {"id": "2"}, "statistics": [{"athletes": [
                        {"athlete": {"displayName": "Jayson Tatum"}}
                    ]}]},
                    {"team": {"id": "13"}, "statistics": [{"athletes": [
                        {"athlete": {"displayName": "LeBron James"}}
                    ]}]}
                ]
            },
            "plays": [
                {"period": {"number": 1}, "text": "Jayson Tatum makes layup", "scoringPlay": True},
                {"period": {"number": 1}, "text": "LeBron James makes three point jumper", "scoringPlay": True},
            ]
        }

        result = nba_pro_betting.extract_quarter_stats(data, '2')
        assert 'Jayson Tatum' in result
        assert 'LeBron James' not in result


# ===========================================================================
# process_team integration test
# ===========================================================================
class TestProcessTeam:
    @patch('nba_pro_betting.get_game_summary')
    @patch('nba_pro_betting.get_team_schedule')
    @patch('nba_pro_betting.time.sleep')
    def test_generates_betting_csv(self, mock_sleep, mock_schedule, mock_summary, tmp_path):
        import pandas as pd

        mock_schedule.return_value = [
            {'game_id': '1', 'date': '2025-01-10', 'home_team': 'Boston Celtics', 'away_team': 'Miami Heat'},
            {'game_id': '2', 'date': '2025-01-08', 'home_team': 'Boston Celtics', 'away_team': 'New York Knicks'},
            {'game_id': '3', 'date': '2025-01-06', 'home_team': 'Chicago Bulls', 'away_team': 'Boston Celtics'},
            {'game_id': '4', 'date': '2025-01-04', 'home_team': 'Boston Celtics', 'away_team': 'Orlando Magic'},
            {'game_id': '5', 'date': '2025-01-02', 'home_team': 'Boston Celtics', 'away_team': 'Cleveland Cavaliers'},
        ]
        # Return full game summary data so extract_boxscore_totals and extract_quarter_stats work
        mock_summary.return_value = {
            "boxscore": {
                "players": [{
                    "team": {"id": "2"},
                    "statistics": [{
                        "labels": ["MIN", "FG", "3PT", "FT", "OREB", "DREB", "REB", "AST", "STL", "BLK", "TO", "PF", "PTS"],
                        "athletes": [
                            {
                                "starter": True,
                                "athlete": {"displayName": "Jayson Tatum"},
                                "stats": ["36", "10-20", "3-8", "5-6", "1", "7", "8", "5", "1", "0", "2", "3", "28"]
                            },
                            {
                                "starter": True,
                                "athlete": {"displayName": "Jaylen Brown"},
                                "stats": ["34", "8-15", "2-5", "4-4", "0", "5", "5", "3", "2", "1", "1", "2", "22"]
                            }
                        ]
                    }]
                }]
            },
            "plays": [
                {"period": {"number": 1}, "text": "Jayson Tatum makes three point jumper", "scoringPlay": True},
                {"period": {"number": 1}, "text": "Jaylen Brown makes driving layup", "scoringPlay": True},
            ]
        }

        # Reset color state
        nba_pro_betting._color_index = 0
        nba_pro_betting._assigned_colors = {}

        original_dir = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = nba_pro_betting.process_team('BOS')
            assert result is True
            assert os.path.exists('BOS_BETTING_ANALYSIS.csv')

            df = pd.read_csv('BOS_BETTING_ANALYSIS.csv')

            # Check key columns exist
            assert 'Player' in df.columns
            assert 'Color_HEX' in df.columns
            assert 'Role' in df.columns
            assert 'PTS_LINE' in df.columns
            assert 'PTS_OVER' in df.columns
            assert 'PTS_HIT%' in df.columns
            assert 'PTS_TREND' in df.columns
            assert 'PTS_CONSISTENCY' in df.columns
            assert 'PTS_STDDEV' in df.columns
            assert 'PTS_OT' in df.columns
            assert 'AVG_PTS_L5' in df.columns

            # Both players should be starters
            assert all(df['Role'] == 'STARTER')

            # Colors should be unique
            colors = df.groupby('Player')['Color_HEX'].first()
            assert colors['Jayson Tatum'] != colors['Jaylen Brown']

        finally:
            os.chdir(original_dir)

    @patch('nba_pro_betting.get_game_summary')
    @patch('nba_pro_betting.get_team_schedule')
    @patch('nba_pro_betting.time.sleep')
    def test_filters_low_minutes_players(self, mock_sleep, mock_schedule, mock_summary, tmp_path):
        mock_schedule.return_value = [
            {'game_id': '1', 'date': '2025-01-10', 'home_team': 'Boston Celtics', 'away_team': 'Miami Heat'}
        ]
        mock_summary.return_value = {
            "boxscore": {
                "players": [{
                    "team": {"id": "2"},
                    "statistics": [{
                        "labels": ["MIN", "FG", "3PT", "FT", "OREB", "DREB", "REB", "AST", "STL", "BLK", "TO", "PF", "PTS"],
                        "athletes": [
                            {
                                "starter": True,
                                "athlete": {"displayName": "Star Player"},
                                "stats": ["36", "10-20", "3-8", "5-6", "1", "7", "8", "5", "1", "0", "2", "3", "28"]
                            },
                            {
                                "starter": False,
                                "athlete": {"displayName": "Low Min Player"},
                                "stats": ["10", "1-3", "0-1", "0-0", "0", "1", "1", "0", "0", "0", "1", "1", "2"]
                            }
                        ]
                    }]
                }]
            },
            "plays": []
        }

        nba_pro_betting._color_index = 0
        nba_pro_betting._assigned_colors = {}

        original_dir = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = nba_pro_betting.process_team('BOS')
            assert result is True

            import pandas as pd
            df = pd.read_csv('BOS_BETTING_ANALYSIS.csv')
            players = df['Player'].unique()
            assert 'Star Player' in players
            assert 'Low Min Player' not in players
        finally:
            os.chdir(original_dir)

    @patch('nba_pro_betting.get_team_schedule')
    def test_returns_false_when_no_games(self, mock_schedule):
        mock_schedule.return_value = []
        result = nba_pro_betting.process_team('BOS')
        assert result is False


# ===========================================================================
# Regex patterns - hyphenated names now work
# ===========================================================================
class TestRegexPatternsFixed:
    def test_hyphenated_name_captured(self):
        import re
        pattern = rf'({nba_pro_betting.PLAYER_NAME_PATTERN}?)\s+makes'
        text = "Shai Gilgeous-Alexander makes driving layup"
        m = re.search(pattern, text)
        assert m is not None
        assert m.group(1).strip() == "Shai Gilgeous-Alexander"

    def test_karl_anthony_towns(self):
        import re
        pattern = rf'({nba_pro_betting.PLAYER_NAME_PATTERN}?)\s+makes'
        text = "Karl-Anthony Towns makes three point jumper"
        m = re.search(pattern, text)
        assert m is not None
        assert m.group(1).strip() == "Karl-Anthony Towns"

    def test_pj_washington(self):
        import re
        pattern = rf'({nba_pro_betting.PLAYER_NAME_PATTERN}?)\s+makes'
        text = "P.J. Washington makes free throw"
        m = re.search(pattern, text)
        assert m is not None
        assert m.group(1).strip() == "P.J. Washington"

    def test_oubre_jr(self):
        import re
        pattern = rf'({nba_pro_betting.PLAYER_NAME_PATTERN}?)\s+makes'
        text = "Kelly Oubre Jr. makes layup"
        m = re.search(pattern, text)
        assert m is not None
        name = m.group(1).strip()
        assert "Kelly Oubre" in name
