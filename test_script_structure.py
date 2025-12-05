#!/usr/bin/env python3
"""
Quick test to validate the script structure and data configuration
"""

import sys

# Import the main script modules
try:
    from nba_combo_props_analyzer import (
        PROPS_DATA,
        PLAYER_COLORS,
        CATEGORY_NAMES,
        calculate_combo_stat,
        calculate_statistics,
        generate_recommendation,
        parse_minutes,
    )
    print("✓ All imports successful")
except Exception as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

# Test 1: Validate configuration data
print("\n" + "="*80)
print("TEST 1: Validating Configuration Data")
print("="*80)

total_players = 0
games_configured = 0

for game_key, categories in PROPS_DATA.items():
    games_configured += 1
    print(f"\n✓ Game: {categories['game_name']}")

    for category_key, players in categories.items():
        if category_key in ['game_name', 'game_time']:
            continue

        print(f"  • {CATEGORY_NAMES[category_key]}: {len(players)} players")
        total_players += len(players)

        for player_name, player_info in players.items():
            assert 'team' in player_info, f"Missing team for {player_name}"
            assert 'line' in player_info, f"Missing line for {player_name}"
            assert player_name in PLAYER_COLORS, f"Missing color for {player_name}"

print(f"\n✓ Total games configured: {games_configured}")
print(f"✓ Total players configured: {total_players}")
print(f"✓ All players have colors assigned")

# Test 2: Test combo stat calculations
print("\n" + "="*80)
print("TEST 2: Testing Combo Stat Calculations")
print("="*80)

test_game = {
    'points': 25,
    'rebounds': 8,
    'assists': 6,
}

pts_ast = calculate_combo_stat(test_game, 'PTS_AST')
pts_reb = calculate_combo_stat(test_game, 'PTS_REB')
pts_ast_reb = calculate_combo_stat(test_game, 'PTS_AST_REB')
ast_reb = calculate_combo_stat(test_game, 'AST_REB')

assert pts_ast == 31, f"PTS+AST calculation error: {pts_ast} != 31"
assert pts_reb == 33, f"PTS+REB calculation error: {pts_reb} != 33"
assert pts_ast_reb == 39, f"PTS+AST+REB calculation error: {pts_ast_reb} != 39"
assert ast_reb == 14, f"AST+REB calculation error: {ast_reb} != 14"

print(f"✓ PTS+AST: {pts_ast} (expected 31)")
print(f"✓ PTS+REB: {pts_reb} (expected 33)")
print(f"✓ PTS+AST+REB: {pts_ast_reb} (expected 39)")
print(f"✓ AST+REB: {ast_reb} (expected 14)")

# Test 3: Test recommendation engine
print("\n" + "="*80)
print("TEST 3: Testing Recommendation Engine")
print("="*80)

test_cases = [
    (35.0, 30.0, 80.0, 'OVER ⭐'),
    (25.0, 30.0, 20.0, 'UNDER ⭐'),
    (31.0, 30.0, 60.0, 'SLIGHT OVER'),
    (29.0, 30.0, 40.0, 'SLIGHT UNDER'),
    (30.0, 30.0, 50.0, 'PASS'),
]

for avg, line, hit_rate, expected in test_cases:
    result = generate_recommendation(avg, line, hit_rate)
    assert result == expected, f"Recommendation error: {result} != {expected}"
    print(f"✓ Avg={avg}, Line={line}, Hit={hit_rate}% → {result}")

# Test 4: Test minutes parsing
print("\n" + "="*80)
print("TEST 4: Testing Minutes Parsing")
print("="*80)

assert parse_minutes("35:30") == 35.5, "Minutes parsing error"
assert parse_minutes("40:00") == 40.0, "Minutes parsing error"
assert parse_minutes(35) == 35.0, "Minutes parsing error"
assert parse_minutes("32") == 32.0, "Minutes parsing error"

print("✓ Minutes parsing: '35:30' → 35.5")
print("✓ Minutes parsing: '40:00' → 40.0")
print("✓ Minutes parsing: 35 → 35.0")
print("✓ Minutes parsing: '32' → 32.0")

# Test 5: Test statistics calculation with mock data
print("\n" + "="*80)
print("TEST 5: Testing Statistics Calculation")
print("="*80)

mock_games = [
    {'date': '2024-12-04', 'opponent': 'vs LAL', 'result': 'W 110-105', 'minutes': 35, 'points': 28, 'rebounds': 6, 'assists': 7},
    {'date': '2024-12-02', 'opponent': '@ MEM', 'result': 'L 98-105', 'minutes': 33, 'points': 22, 'rebounds': 5, 'assists': 5},
    {'date': '2024-11-30', 'opponent': 'vs PHX', 'result': 'W 115-108', 'minutes': 36, 'points': 31, 'rebounds': 7, 'assists': 8},
    {'date': '2024-11-28', 'opponent': '@ ORL', 'result': 'L 92-98', 'minutes': 32, 'points': 19, 'rebounds': 4, 'assists': 4},
    {'date': '2024-11-26', 'opponent': 'vs BOS', 'result': 'W 108-102', 'minutes': 37, 'points': 26, 'rebounds': 6, 'assists': 6},
    {'date': '2024-11-24', 'opponent': '@ ATL', 'result': 'W 112-107', 'minutes': 34, 'points': 24, 'rebounds': 5, 'assists': 9},
]

stats = calculate_statistics(mock_games, 'PTS_AST', 25.5)

print(f"✓ Total combo: {stats['total_combo']}")
print(f"✓ Average combo: {stats['avg_combo']}")
print(f"✓ Hit rate: {stats['hit_rate']:.1f}%")
print(f"✓ Trend: {stats['trend']}")
print(f"✓ Recommendation: {stats['recommendation']}")

assert stats['num_games'] == 6, "Game count error"
assert stats['hit_count'] >= 0, "Hit count error"
assert 0 <= stats['hit_rate'] <= 100, "Hit rate error"
assert stats['trend'] in ['↑', '↓', '→'], "Trend error"

# Final summary
print("\n" + "="*80)
print("ALL TESTS PASSED ✓")
print("="*80)
print(f"\nScript is ready to run!")
print(f"Execute with: python nba_combo_props_analyzer.py")
print("="*80 + "\n")
