#!/usr/bin/env python3
"""
DEMO del NBA PRO BETTING ANALYZER
Simula datos reales para mostrar como funciona el script sin necesidad de internet.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import patch, MagicMock
import nba_pro_betting


# ============================================================================
# DATOS SIMULADOS REALISTAS - Lakers vs Celtics
# ============================================================================
FAKE_SCOREBOARD = {
    "events": [
        {
            "id": "401654321",
            "date": "2026-02-10T00:30Z",
            "competitions": [{
                "competitors": [
                    {"team": {"abbreviation": "LAL", "displayName": "Los Angeles Lakers"}, "homeAway": "away"},
                    {"team": {"abbreviation": "BOS", "displayName": "Boston Celtics"}, "homeAway": "home"}
                ],
                "status": {"type": {"name": "STATUS_SCHEDULED"}}
            }]
        }
    ]
}

# 5 juegos completados para los Lakers
FAKE_SCHEDULE_LAL = {
    "events": [
        {"id": "4016001", "date": "2026-02-08T00:00Z", "competitions": [{"competitors": [
            {"team": {"displayName": "Los Angeles Lakers"}, "homeAway": "home"},
            {"team": {"displayName": "Golden State Warriors"}, "homeAway": "away"}
        ], "status": {"type": {"completed": True}}}]},
        {"id": "4016002", "date": "2026-02-06T00:00Z", "competitions": [{"competitors": [
            {"team": {"displayName": "Phoenix Suns"}, "homeAway": "home"},
            {"team": {"displayName": "Los Angeles Lakers"}, "homeAway": "away"}
        ], "status": {"type": {"completed": True}}}]},
        {"id": "4016003", "date": "2026-02-04T00:00Z", "competitions": [{"competitors": [
            {"team": {"displayName": "Los Angeles Lakers"}, "homeAway": "home"},
            {"team": {"displayName": "Denver Nuggets"}, "homeAway": "away"}
        ], "status": {"type": {"completed": True}}}]},
        {"id": "4016004", "date": "2026-02-02T00:00Z", "competitions": [{"competitors": [
            {"team": {"displayName": "Los Angeles Lakers"}, "homeAway": "home"},
            {"team": {"displayName": "Miami Heat"}, "homeAway": "away"}
        ], "status": {"type": {"completed": True}}}]},
        {"id": "4016005", "date": "2026-01-31T00:00Z", "competitions": [{"competitors": [
            {"team": {"displayName": "Dallas Mavericks"}, "homeAway": "home"},
            {"team": {"displayName": "Los Angeles Lakers"}, "homeAway": "away"}
        ], "status": {"type": {"completed": True}}}]},
    ]
}

# 5 juegos completados para los Celtics
FAKE_SCHEDULE_BOS = {
    "events": [
        {"id": "4017001", "date": "2026-02-08T00:00Z", "competitions": [{"competitors": [
            {"team": {"displayName": "Boston Celtics"}, "homeAway": "home"},
            {"team": {"displayName": "New York Knicks"}, "homeAway": "away"}
        ], "status": {"type": {"completed": True}}}]},
        {"id": "4017002", "date": "2026-02-06T00:00Z", "competitions": [{"competitors": [
            {"team": {"displayName": "Milwaukee Bucks"}, "homeAway": "home"},
            {"team": {"displayName": "Boston Celtics"}, "homeAway": "away"}
        ], "status": {"type": {"completed": True}}}]},
        {"id": "4017003", "date": "2026-02-04T00:00Z", "competitions": [{"competitors": [
            {"team": {"displayName": "Boston Celtics"}, "homeAway": "home"},
            {"team": {"displayName": "Philadelphia 76ers"}, "homeAway": "away"}
        ], "status": {"type": {"completed": True}}}]},
        {"id": "4017004", "date": "2026-02-02T00:00Z", "competitions": [{"competitors": [
            {"team": {"displayName": "Boston Celtics"}, "homeAway": "home"},
            {"team": {"displayName": "Cleveland Cavaliers"}, "homeAway": "away"}
        ], "status": {"type": {"completed": True}}}]},
        {"id": "4017005", "date": "2026-01-31T00:00Z", "competitions": [{"competitors": [
            {"team": {"displayName": "Toronto Raptors"}, "homeAway": "home"},
            {"team": {"displayName": "Boston Celtics"}, "homeAway": "away"}
        ], "status": {"type": {"completed": True}}}]},
    ]
}

# Datos de juego simulados para Lakers
def make_lal_game_summary(game_idx):
    """Genera datos de boxscore + plays realistas para cada juego de LAL."""
    # Estadisticas por juego para cada jugador (pts, reb, ast, 3pm, min)
    lebron_games = [
        (32, 9, 11, 3, 37), (28, 7, 8, 2, 36), (35, 10, 9, 4, 38),
        (22, 8, 12, 1, 34), (30, 11, 7, 3, 36)
    ]
    ad_games = [
        (27, 14, 3, 0, 36), (31, 12, 4, 1, 37), (24, 15, 2, 0, 35),
        (29, 11, 3, 0, 36), (26, 13, 5, 1, 34)
    ]
    austin_games = [
        (18, 4, 6, 3, 32), (22, 3, 5, 4, 33), (15, 5, 7, 2, 31),
        (20, 3, 4, 3, 30), (17, 4, 8, 3, 32)
    ]
    dlo_games = [
        (16, 3, 8, 3, 30), (20, 2, 7, 4, 31), (14, 4, 9, 2, 29),
        (18, 3, 6, 3, 28), (12, 2, 10, 2, 30)
    ]
    rui_games = [
        (14, 5, 1, 1, 28), (12, 6, 2, 0, 27), (16, 4, 1, 2, 29),
        (10, 7, 2, 1, 26), (15, 5, 1, 1, 28)
    ]
    # Bench player with low minutes
    bench_games = [
        (4, 2, 1, 0, 12), (6, 1, 0, 1, 14), (2, 3, 1, 0, 10),
        (5, 1, 2, 1, 13), (3, 2, 0, 0, 11)
    ]

    g = game_idx
    players_data = [
        ("LeBron James", lebron_games[g], True),
        ("Anthony Davis", ad_games[g], True),
        ("Austin Reaves", austin_games[g], True),
        ("D'Angelo Russell", dlo_games[g], True),
        ("Rui Hachimura", rui_games[g], True),
        ("Jaxson Hayes", bench_games[g], False),
    ]

    athletes = []
    plays = []

    for name, (pts, reb, ast, tpm, mins), starter in players_data:
        athletes.append({
            "starter": starter,
            "athlete": {"displayName": name},
            "stats": [
                str(mins), f"{pts//3}-{pts//2}", f"{tpm}-{tpm+3}",
                f"{pts%5}-{pts%5+1}", str(reb//3), str(reb - reb//3),
                str(reb), str(ast), "1", "0", "2", "3", str(pts)
            ]
        })

        # Generate play-by-play for Q1-Q4
        for q in range(1, 5):
            q_pts = pts // 4 + (1 if q <= pts % 4 else 0)
            q_reb = reb // 4 + (1 if q <= reb % 4 else 0)
            q_ast = ast // 4 + (1 if q <= ast % 4 else 0)

            # Points plays
            remaining = q_pts
            if tpm > 0 and q <= tpm:
                plays.append({"period": {"number": q}, "text": f"{name} makes three point jumper", "scoringPlay": True})
                remaining -= 3
            while remaining >= 2:
                plays.append({"period": {"number": q}, "text": f"{name} makes driving layup", "scoringPlay": True})
                remaining -= 2
            if remaining == 1:
                plays.append({"period": {"number": q}, "text": f"{name} makes free throw 1 of 2", "scoringPlay": True})

            # Rebounds
            for _ in range(q_reb):
                plays.append({"period": {"number": q}, "text": f"{name} defensive rebound", "scoringPlay": False})

            # Assists
            for _ in range(q_ast):
                plays.append({"period": {"number": q}, "text": f"Teammate makes layup ({name} assists)", "scoringPlay": False})

    return {
        "boxscore": {
            "players": [{
                "team": {"id": "13"},
                "statistics": [{
                    "labels": ["MIN", "FG", "3PT", "FT", "OREB", "DREB", "REB", "AST", "STL", "BLK", "TO", "PF", "PTS"],
                    "athletes": athletes
                }]
            }]
        },
        "plays": plays
    }


def make_bos_game_summary(game_idx):
    """Genera datos de boxscore + plays realistas para cada juego de BOS."""
    tatum_games = [
        (30, 8, 5, 3, 36), (26, 9, 6, 2, 35), (33, 7, 4, 4, 37),
        (28, 10, 7, 3, 36), (31, 6, 5, 3, 35)
    ]
    brown_games = [
        (24, 5, 3, 2, 34), (28, 6, 4, 3, 35), (22, 4, 2, 1, 33),
        (26, 7, 5, 2, 34), (20, 5, 3, 2, 32)
    ]
    white_games = [
        (18, 4, 6, 3, 32), (15, 3, 5, 2, 31), (20, 5, 7, 4, 33),
        (16, 4, 4, 2, 30), (14, 3, 6, 3, 31)
    ]
    holiday_games = [
        (14, 5, 7, 1, 30), (12, 4, 8, 0, 29), (16, 6, 6, 2, 31),
        (13, 5, 9, 1, 30), (15, 4, 5, 1, 28)
    ]
    horford_games = [
        (10, 8, 3, 1, 28), (12, 9, 2, 2, 27), (8, 7, 4, 1, 26),
        (11, 10, 3, 1, 27), (9, 8, 2, 1, 26)
    ]

    g = game_idx
    players_data = [
        ("Jayson Tatum", tatum_games[g], True),
        ("Jaylen Brown", brown_games[g], True),
        ("Derrick White", white_games[g], True),
        ("Jrue Holiday", holiday_games[g], True),
        ("Al Horford", horford_games[g], True),
    ]

    athletes = []
    plays = []

    for name, (pts, reb, ast, tpm, mins), starter in players_data:
        athletes.append({
            "starter": starter,
            "athlete": {"displayName": name},
            "stats": [
                str(mins), f"{pts//3}-{pts//2}", f"{tpm}-{tpm+3}",
                f"{pts%5}-{pts%5+1}", str(reb//3), str(reb - reb//3),
                str(reb), str(ast), "1", "0", "2", "3", str(pts)
            ]
        })

        for q in range(1, 5):
            q_pts = pts // 4 + (1 if q <= pts % 4 else 0)
            q_reb = reb // 4 + (1 if q <= reb % 4 else 0)
            q_ast = ast // 4 + (1 if q <= ast % 4 else 0)

            remaining = q_pts
            if tpm > 0 and q <= tpm:
                plays.append({"period": {"number": q}, "text": f"{name} makes three point jumper", "scoringPlay": True})
                remaining -= 3
            while remaining >= 2:
                plays.append({"period": {"number": q}, "text": f"{name} makes driving layup", "scoringPlay": True})
                remaining -= 2
            if remaining == 1:
                plays.append({"period": {"number": q}, "text": f"{name} makes free throw 1 of 2", "scoringPlay": True})

            for _ in range(q_reb):
                plays.append({"period": {"number": q}, "text": f"{name} defensive rebound", "scoringPlay": False})

            for _ in range(q_ast):
                plays.append({"period": {"number": q}, "text": f"Teammate makes layup ({name} assists)", "scoringPlay": False})

    return {
        "boxscore": {
            "players": [{
                "team": {"id": "2"},
                "statistics": [{
                    "labels": ["MIN", "FG", "3PT", "FT", "OREB", "DREB", "REB", "AST", "STL", "BLK", "TO", "PF", "PTS"],
                    "athletes": athletes
                }]
            }]
        },
        "plays": plays
    }


# Track which game we're on per team
_lal_game_counter = 0
_bos_game_counter = 0


def fake_requests_get(url, **kwargs):
    """Simula las respuestas de la API de ESPN."""
    global _lal_game_counter, _bos_game_counter

    mock_resp = MagicMock()

    if 'scoreboard' in url:
        mock_resp.json.return_value = FAKE_SCOREBOARD
    elif 'teams/13/schedule' in url:
        mock_resp.json.return_value = FAKE_SCHEDULE_LAL
    elif 'teams/2/schedule' in url:
        mock_resp.json.return_value = FAKE_SCHEDULE_BOS
    elif 'summary?event=401600' in url:
        # LAL games
        data = make_lal_game_summary(_lal_game_counter % 5)
        _lal_game_counter += 1
        mock_resp.json.return_value = data
    elif 'summary?event=401700' in url:
        # BOS games
        data = make_bos_game_summary(_bos_game_counter % 5)
        _bos_game_counter += 1
        mock_resp.json.return_value = data
    else:
        mock_resp.json.return_value = {}

    return mock_resp


# ============================================================================
# EJECUTAR DEMO
# ============================================================================
if __name__ == "__main__":
    # Reset color state
    nba_pro_betting._color_index = 0
    nba_pro_betting._assigned_colors = {}

    with patch('nba_pro_betting.requests.get', side_effect=fake_requests_get):
        with patch('nba_pro_betting.time.sleep'):
            nba_pro_betting.main()

    # Show generated CSV files
    import pandas as pd
    import glob

    csv_files = glob.glob('*_BETTING_ANALYSIS.csv')
    for csv_file in sorted(csv_files):
        print(f"\n{'='*100}")
        print(f"  CONTENIDO DEL CSV: {csv_file}")
        print(f"{'='*100}")
        df = pd.read_csv(csv_file)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 200)
        pd.set_option('display.max_colwidth', 20)

        # Show summary per player
        players = df['Player'].unique()
        for player in players:
            pdf = df[df['Player'] == player]
            color = pdf['Color_HEX'].iloc[0]
            role = pdf['Role'].iloc[0]
            avg_pts = pdf['AVG_PTS_L5'].iloc[0]
            avg_reb = pdf['AVG_REB_L5'].iloc[0]
            avg_ast = pdf['AVG_AST_L5'].iloc[0]
            pts_line = pdf['PTS_LINE'].iloc[0]
            reb_line = pdf['REB_LINE'].iloc[0]
            ast_line = pdf['AST_LINE'].iloc[0]
            pts_hit = pdf['PTS_HIT%'].iloc[0]
            reb_hit = pdf['REB_HIT%'].iloc[0]
            ast_hit = pdf['AST_HIT%'].iloc[0]
            pts_trend = pdf['PTS_TREND'].iloc[0]
            pts_con = pdf['PTS_CONSISTENCY'].iloc[0]

            print(f"\n  {player} [{color}] ({role})")
            print(f"  {'─'*80}")

            # Game-by-game
            print(f"  {'FECHA':<8} {'VS':<22} {'MIN':>4}  "
                  f"{'Q1':>4} {'Q2':>4} {'Q3':>4} {'Q4':>4} {'TOT':>4}  "
                  f"{'REB':>4} {'AST':>4} {'3PM':>4}  "
                  f"{'PTS O/U':<9} {'REB O/U':<9} {'AST O/U':<9}")
            for _, row in pdf.iterrows():
                print(f"  {row['Game_Date']:<8} {str(row['Opponent'])[:20]:<22} {row['MIN']:>4}  "
                      f"{row['PTS_Q1']:>4} {row['PTS_Q2']:>4} {row['PTS_Q3']:>4} {row['PTS_Q4']:>4} {row['PTS_TOTAL']:>4}  "
                      f"{row['REB_TOTAL']:>4} {row['AST_TOTAL']:>4} {row['3PM_TOTAL']:>4}  "
                      f"{row['PTS_OVER']:<9} {row['REB_OVER']:<9} {row['AST_OVER']:<9}")

            print(f"\n  PROMEDIOS L5:  PTS={avg_pts}  REB={avg_reb}  AST={avg_ast}")
            print(f"  LINEAS:        PTS={pts_line}  REB={reb_line}  AST={ast_line}")
            print(f"  HIT RATES:     PTS={pts_hit}%  REB={reb_hit}%  AST={ast_hit}%")
            print(f"  TENDENCIA:     PTS={pts_trend}  CONSISTENCIA={pts_con}")
