"""
Shared fixtures and sample data for NBA scraper tests.
"""
import pytest


# --- Sample ESPN API Responses ---

@pytest.fixture
def scoreboard_response_with_games():
    """Simulates an ESPN scoreboard API response with 2 games scheduled."""
    return {
        "events": [
            {
                "id": "401654321",
                "date": "2025-01-15T00:00Z",
                "competitions": [{
                    "competitors": [
                        {"team": {"abbreviation": "BOS", "displayName": "Boston Celtics"}, "homeAway": "away"},
                        {"team": {"abbreviation": "LAL", "displayName": "Los Angeles Lakers"}, "homeAway": "home"}
                    ],
                    "status": {"type": {"name": "STATUS_SCHEDULED"}}
                }]
            },
            {
                "id": "401654322",
                "date": "2025-01-15T02:30Z",
                "competitions": [{
                    "competitors": [
                        {"team": {"abbreviation": "GSW", "displayName": "Golden State Warriors"}, "homeAway": "away"},
                        {"team": {"abbreviation": "MIA", "displayName": "Miami Heat"}, "homeAway": "home"}
                    ],
                    "status": {"type": {"name": "STATUS_SCHEDULED"}}
                }]
            }
        ]
    }


@pytest.fixture
def scoreboard_response_no_games():
    """Simulates an ESPN scoreboard API response with no games."""
    return {"events": []}


@pytest.fixture
def schedule_response():
    """Simulates an ESPN team schedule API response with mixed completed/upcoming games."""
    return {
        "events": [
            {
                "id": "401600001",
                "date": "2025-01-10T00:00Z",
                "competitions": [{
                    "competitors": [
                        {"team": {"displayName": "Boston Celtics"}, "homeAway": "home"},
                        {"team": {"displayName": "Miami Heat"}, "homeAway": "away"}
                    ],
                    "status": {"type": {"completed": True}}
                }]
            },
            {
                "id": "401600002",
                "date": "2025-01-08T00:00Z",
                "competitions": [{
                    "competitors": [
                        {"team": {"displayName": "Boston Celtics"}, "homeAway": "away"},
                        {"team": {"displayName": "New York Knicks"}, "homeAway": "home"}
                    ],
                    "status": {"type": {"completed": True}}
                }]
            },
            {
                "id": "401600003",
                "date": "2025-01-12T00:00Z",
                "competitions": [{
                    "competitors": [
                        {"team": {"displayName": "Boston Celtics"}, "homeAway": "home"},
                        {"team": {"displayName": "Chicago Bulls"}, "homeAway": "away"}
                    ],
                    "status": {"type": {"completed": True}}
                }]
            },
            {
                "id": "401600099",
                "date": "2025-01-20T00:00Z",
                "competitions": [{
                    "competitors": [
                        {"team": {"displayName": "Boston Celtics"}, "homeAway": "home"},
                        {"team": {"displayName": "Denver Nuggets"}, "homeAway": "away"}
                    ],
                    "status": {"type": {"completed": False}}
                }]
            }
        ]
    }


@pytest.fixture
def boxscore_response():
    """Simulates an ESPN game summary response with boxscore data."""
    return {
        "boxscore": {
            "players": [
                {
                    "team": {"id": "2"},
                    "statistics": [{
                        "labels": ["MIN", "FG", "3PT", "FT", "OREB", "DREB", "REB", "AST", "STL", "BLK", "TO", "PF", "PTS"],
                        "athletes": [
                            {
                                "active": True,
                                "athlete": {"displayName": "Jayson Tatum"},
                                "stats": ["36", "10-20", "3-8", "5-6", "1", "7", "8", "5", "1", "0", "2", "3", "28"]
                            },
                            {
                                "active": True,
                                "athlete": {"displayName": "Jaylen Brown"},
                                "stats": ["34", "8-15", "2-5", "4-4", "0", "5", "5", "3", "2", "1", "1", "2", "22"]
                            },
                            {
                                "active": True,
                                "athlete": {"displayName": "Bench Player"},
                                "stats": ["0", "0-0", "0-0", "0-0", "0", "0", "0", "0", "0", "0", "0", "0", "0"]
                            },
                            {
                                "active": False,
                                "athlete": {"displayName": "Injured Player"},
                                "stats": []
                            }
                        ]
                    }]
                },
                {
                    "team": {"id": "13"},
                    "statistics": [{
                        "labels": ["MIN", "FG", "3PT", "FT", "OREB", "DREB", "REB", "AST", "STL", "BLK", "TO", "PF", "PTS"],
                        "athletes": [
                            {
                                "active": True,
                                "athlete": {"displayName": "LeBron James"},
                                "stats": ["38", "12-22", "4-9", "2-2", "2", "8", "10", "8", "1", "2", "3", "2", "30"]
                            }
                        ]
                    }]
                }
            ]
        },
        "plays": []
    }


@pytest.fixture
def playbyplay_response():
    """Simulates an ESPN game summary response with play-by-play data for Q1 and Q2."""
    team_players_boxscore = {
        "boxscore": {
            "players": [
                {
                    "team": {"id": "2"},
                    "statistics": [{
                        "athletes": [
                            {"active": True, "athlete": {"displayName": "Jayson Tatum"}},
                            {"active": True, "athlete": {"displayName": "Jaylen Brown"}},
                            {"active": True, "athlete": {"displayName": "Derrick White"}}
                        ]
                    }]
                }
            ]
        },
        "plays": [
            # Q1 plays
            {"period": {"number": 1}, "text": "Jayson Tatum makes three point jumper", "scoringPlay": True},
            {"period": {"number": 1}, "text": "Jayson Tatum makes driving layup (Jaylen Brown assists)", "scoringPlay": True},
            {"period": {"number": 1}, "text": "Jaylen Brown makes free throw 1 of 2", "scoringPlay": True},
            {"period": {"number": 1}, "text": "Jaylen Brown makes free throw 2 of 2", "scoringPlay": True},
            {"period": {"number": 1}, "text": "Jayson Tatum defensive rebound", "scoringPlay": False},
            {"period": {"number": 1}, "text": "Jaylen Brown offensive rebound", "scoringPlay": False},
            {"period": {"number": 1}, "text": "Derrick White makes 3-point jumper (Jayson Tatum assists)", "scoringPlay": True},
            # Q2 plays
            {"period": {"number": 2}, "text": "Jayson Tatum makes driving dunk", "scoringPlay": True},
            {"period": {"number": 2}, "text": "Jaylen Brown makes three point jumper (Derrick White assists)", "scoringPlay": True},
            {"period": {"number": 2}, "text": "Jayson Tatum defensive rebound", "scoringPlay": False},
            # Q5 (overtime) - should be ignored by nba_nuevo.py
            {"period": {"number": 5}, "text": "Jayson Tatum makes free throw", "scoringPlay": True},
        ]
    }
    return team_players_boxscore


@pytest.fixture
def playbyplay_with_opponent_plays():
    """Play-by-play with plays from both teams to test team filtering."""
    return {
        "boxscore": {
            "players": [
                {
                    "team": {"id": "2"},
                    "statistics": [{
                        "athletes": [
                            {"active": True, "athlete": {"displayName": "Jayson Tatum"}},
                        ]
                    }]
                },
                {
                    "team": {"id": "13"},
                    "statistics": [{
                        "athletes": [
                            {"active": True, "athlete": {"displayName": "LeBron James"}},
                        ]
                    }]
                }
            ]
        },
        "plays": [
            {"period": {"number": 1}, "text": "Jayson Tatum makes driving layup", "scoringPlay": True},
            {"period": {"number": 1}, "text": "LeBron James makes three point jumper", "scoringPlay": True},
            {"period": {"number": 1}, "text": "LeBron James defensive rebound", "scoringPlay": False},
            {"period": {"number": 1}, "text": "Jayson Tatum offensive rebound", "scoringPlay": False},
        ]
    }
