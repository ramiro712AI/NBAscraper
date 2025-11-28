#!/usr/bin/env python3
"""
NBA PARLAY GENERATOR - ANÁLISIS DE CONSISTENCIA
Genera parlays de alta probabilidad basados en:
- Datos históricos de los últimos 5 juegos
- Líneas de apuestas de Hard Rock Bet
- Standings de la NBA
"""

import pandas as pd
import numpy as np
from collections import defaultdict

# Cargar todos los datos
chi_df = pd.read_csv('CHI_last_5_games.csv')
cha_df = pd.read_csv('CHA_last_5_games.csv')
orl_df = pd.read_csv('ORL_last_5_games.csv')
det_df = pd.read_csv('DET_last_5_games.csv')
cle_df = pd.read_csv('CLE_last_5_games.csv')
atl_df = pd.read_csv('ATL_last_5_games.csv')

# ODDS DE HARD ROCK BET - JUEGO CHI @ CHA

odds_chi_cha_full = {
    # POINTS FULL GAME
    ('Coby White', 'PTS', 'FULL'): {'line': 23.5, 'over': -110, 'under': -120},
    ('Josh Giddey', 'PTS', 'FULL'): {'line': 20.5, 'over': -115, 'under': -115},
    ('Brandon Miller', 'PTS', 'FULL'): {'line': 19.5, 'over': -110, 'under': -120},
    ('Miles Bridges', 'PTS', 'FULL'): {'line': 19.5, 'over': -105, 'under': -125},
    ('LaMelo Ball', 'PTS', 'FULL'): {'line': 18.5, 'over': -120, 'under': -110},
    ('Nikola Vucevic', 'PTS', 'FULL'): {'line': 18.5, 'over': -115, 'under': -115},
    ('Ayo Dosunmu', 'PTS', 'FULL'): {'line': 15.5, 'over': -115, 'under': -115},

    # ASSISTS FULL GAME
    ('Josh Giddey', 'AST', 'FULL'): {'line': 9.5, 'over': 105, 'under': -145},
    ('LaMelo Ball', 'AST', 'FULL'): {'line': 7.5, 'over': -135, 'under': -105},
    ('Coby White', 'AST', 'FULL'): {'line': 5.5, 'over': 110, 'under': -155},
    ('Miles Bridges', 'AST', 'FULL'): {'line': 3.5, 'over': 120, 'under': -170},
    ('Brandon Miller', 'AST', 'FULL'): {'line': 2.5, 'over': -180, 'under': 125},
    ('Nikola Vucevic', 'AST', 'FULL'): {'line': 2.5, 'over': -160, 'under': 115},

    # REBOUNDS FULL GAME
    ('Nikola Vucevic', 'REB', 'FULL'): {'line': 9.5, 'over': -120, 'under': -115},
    ('Josh Giddey', 'REB', 'FULL'): {'line': 8.5, 'over': -145, 'under': 100},
    ('Miles Bridges', 'REB', 'FULL'): {'line': 6.5, 'over': -110, 'under': -125},
    ('LaMelo Ball', 'REB', 'FULL'): {'line': 5.5, 'over': 105, 'under': -145},
    ('Brandon Miller', 'REB', 'FULL'): {'line': 3.5, 'over': -200, 'under': 140},

    # 3PM FULL GAME
    ('Coby White', '3PM', 'FULL'): {'line': 3.5, 'over': 110, 'under': -155},
    ('Brandon Miller', '3PM', 'FULL'): {'line': 3.5, 'over': 160, 'under': -240},
    ('LaMelo Ball', '3PM', 'FULL'): {'line': 2.5, 'over': -125, 'under': -110},
    ('Miles Bridges', '3PM', 'FULL'): {'line': 2.5, 'over': 110, 'under': -155},
    ('Nikola Vucevic', '3PM', 'FULL'): {'line': 1.5, 'over': -180, 'under': 125},
    ('Josh Giddey', '3PM', 'FULL'): {'line': 1.5, 'over': -120, 'under': -120},
}

odds_chi_cha_q1 = {
    # POINTS Q1
    ('Coby White', 'PTS', 'Q1'): {'line': 5.5, 'odds': 100, 'side': 'OVER'},
    ('Brandon Miller', 'PTS', 'Q1'): {'line': 4.5, 'odds': -125, 'side': 'OVER'},
    ('Josh Giddey', 'PTS', 'Q1'): {'line': 4.5, 'odds': -120, 'side': 'OVER'},
    ('Miles Bridges', 'PTS', 'Q1'): {'line': 4.5, 'odds': -120, 'side': 'OVER'},
    ('LaMelo Ball', 'PTS', 'Q1'): {'line': 4.5, 'odds': -115, 'side': 'OVER'},
    ('Nikola Vucevic', 'PTS', 'Q1'): {'line': 4.5, 'odds': -110, 'side': 'OVER'},

    # ASSISTS Q1
    ('Josh Giddey', 'AST', 'Q1'): {'line': 2.5, 'odds': 105, 'side': 'OVER'},
    ('LaMelo Ball', 'AST', 'Q1'): {'line': 2.5, 'odds': 135, 'side': 'OVER'},
    ('Coby White', 'AST', 'Q1'): {'line': 1.5, 'odds': 125, 'side': 'OVER'},
    ('Brandon Miller', 'AST', 'Q1'): {'line': 0.5, 'odds': -145, 'side': 'OVER'},

    # REBOUNDS Q1
    ('Nikola Vucevic', 'REB', 'Q1'): {'line': 2.5, 'odds': 105, 'side': 'OVER'},
    ('Josh Giddey', 'REB', 'Q1'): {'line': 2.5, 'odds': 120, 'side': 'OVER'},
    ('Miles Bridges', 'REB', 'Q1'): {'line': 1.5, 'odds': -145, 'side': 'OVER'},
    ('LaMelo Ball', 'REB', 'Q1'): {'line': 1.5, 'odds': 105, 'side': 'OVER'},
}

# ODDS ORL @ DET
odds_orl_det_full = {
    # POINTS FULL GAME
    ('Cade Cunningham', 'PTS', 'FULL'): {'line': 28.5, 'over': -110, 'under': -120},
    ('Franz Wagner', 'PTS', 'FULL'): {'line': 23.5, 'over': -125, 'under': -105},
    ('Desmond Bane', 'PTS', 'FULL'): {'line': 19.5, 'over': -110, 'under': -120},
    ('Jalen Duren', 'PTS', 'FULL'): {'line': 18.5, 'over': -120, 'under': -110},
    ('Jalen Suggs', 'PTS', 'FULL'): {'line': 15.5, 'over': -105, 'under': -125},

    # 3PM FULL GAME
    ('Jalen Suggs', '3PM', 'FULL'): {'line': 2.5, 'over': 115, 'under': -165},
    ('Duncan Robinson', '3PM', 'FULL'): {'line': 2.5, 'over': 120, 'under': -170},
    ('Cade Cunningham', '3PM', 'FULL'): {'line': 2.5, 'over': 130, 'under': -185},
    ('Desmond Bane', '3PM', 'FULL'): {'line': 2.5, 'over': 135, 'under': -195},
    ('Franz Wagner', '3PM', 'FULL'): {'line': 1.5, 'over': -110, 'under': -130},
    ('Tobias Harris', '3PM', 'FULL'): {'line': 1.5, 'over': 115, 'under': -160},
}

odds_orl_det_q1 = {
    # POINTS Q1
    ('Franz Wagner', 'PTS', 'Q1'): {'line': 5.5, 'odds': -135, 'side': 'OVER'},
    ('Cade Cunningham', 'PTS', 'Q1'): {'line': 5.5, 'odds': -120, 'side': 'OVER'},
    ('Jalen Duren', 'PTS', 'Q1'): {'line': 4.5, 'odds': -130, 'side': 'OVER'},
    ('Desmond Bane', 'PTS', 'Q1'): {'line': 4.5, 'odds': -110, 'side': 'OVER'},
    ('Jalen Suggs', 'PTS', 'Q1'): {'line': 3.5, 'odds': -115, 'side': 'OVER'},

    # REBOUNDS Q1
    ('Jalen Duren', 'REB', 'Q1'): {'line': 2.5, 'odds': -160, 'side': 'OVER'},
    ('Wendell Carter Jr.', 'REB', 'Q1'): {'line': 1.5, 'odds': -150, 'side': 'OVER'},
    ('Franz Wagner', 'REB', 'Q1'): {'line': 1.5, 'odds': 110, 'side': 'OVER'},
    ('Cade Cunningham', 'REB', 'Q1'): {'line': 1.5, 'odds': 115, 'side': 'OVER'},

    # ASSISTS Q1
    ('Cade Cunningham', 'AST', 'Q1'): {'line': 2.5, 'odds': 105, 'side': 'OVER'},
    ('Jalen Suggs', 'AST', 'Q1'): {'line': 1.5, 'odds': -105, 'side': 'OVER'},
    ('Franz Wagner', 'AST', 'Q1'): {'line': 0.5, 'odds': -250, 'side': 'OVER'},
    ('Desmond Bane', 'AST', 'Q1'): {'line': 0.5, 'odds': -230, 'side': 'OVER'},
}

def calculate_consistency(df, player_name, stat, line, scope='FULL'):
    """
    Calcula la consistencia de un jugador en una métrica específica
    Retorna: (porcentaje de veces que cumple, promedio)
    """
    player_data = df[df['Player'] == player_name]

    if len(player_data) == 0:
        return 0, 0

    # Obtener la columna correcta según el scope
    if scope == 'FULL':
        col = f'{stat}_TOTAL'
    else:  # Q1
        col = f'{stat}_Q1'

    if col not in player_data.columns:
        return 0, 0

    values = player_data[col].values
    avg = np.mean(values)

    return avg, values

def analyze_player_pick(df, player_name, stat, line, direction, scope='FULL'):
    """
    Analiza un pick específico y retorna la probabilidad de éxito
    """
    avg, values = calculate_consistency(df, player_name, stat, line, scope)

    if len(values) == 0:
        return {'prob': 0, 'avg': 0, 'hits': 0, 'total': 0}

    if direction == 'OVER':
        hits = sum(v > line for v in values)
    else:  # UNDER
        hits = sum(v < line for v in values)

    total = len(values)
    prob = (hits / total) * 100 if total > 0 else 0

    return {
        'prob': prob,
        'avg': avg,
        'hits': hits,
        'total': total,
        'values': values.tolist()
    }

print("="*60)
print("ANÁLISIS DE JUGADORES - JUEGO CHI @ CHA")
print("="*60)

# Analizar jugadores del juego CHI @ CHA para Q1
print("\n🏀 ANÁLISIS Q1 - CHI @ CHA\n")

# Coby White - PTS Q1 Over 5.5
result = analyze_player_pick(chi_df, 'Coby White', 'PTS', 5.5, 'OVER', 'Q1')
print(f"Coby White PTS Q1 Over 5.5: {result['prob']:.1f}% ({result['hits']}/{result['total']}) | Promedio: {result['avg']:.1f} | Valores: {result['values']}")

# Josh Giddey - AST Q1 Over 2.5
result = analyze_player_pick(chi_df, 'Josh Giddey', 'AST', 2.5, 'OVER', 'Q1')
print(f"Josh Giddey AST Q1 Over 2.5: {result['prob']:.1f}% ({result['hits']}/{result['total']}) | Promedio: {result['avg']:.1f} | Valores: {result['values']}")

# Nikola Vucevic - REB Q1 Over 2.5
result = analyze_player_pick(chi_df, 'Nikola Vucevic', 'REB', 2.5, 'OVER', 'Q1')
print(f"Nikola Vucevic REB Q1 Over 2.5: {result['prob']:.1f}% ({result['hits']}/{result['total']}) | Promedio: {result['avg']:.1f} | Valores: {result['values']}")

# Brandon Miller - PTS Q1 Over 4.5
result = analyze_player_pick(cha_df, 'Brandon Miller', 'PTS', 4.5, 'OVER', 'Q1')
print(f"Brandon Miller PTS Q1 Over 4.5: {result['prob']:.1f}% ({result['hits']}/{result['total']}) | Promedio: {result['avg']:.1f} | Valores: {result['values']}")

# LaMelo Ball - REB Q1 Over 1.5
result = analyze_player_pick(cha_df, 'LaMelo Ball', 'REB', 1.5, 'OVER', 'Q1')
print(f"LaMelo Ball REB Q1 Over 1.5: {result['prob']:.1f}% ({result['hits']}/{result['total']}) | Promedio: {result['avg']:.1f} | Valores: {result['values']}")

# Miles Bridges - REB Q1 Over 1.5
result = analyze_player_pick(cha_df, 'Miles Bridges', 'REB', 1.5, 'OVER', 'Q1')
print(f"Miles Bridges REB Q1 Over 1.5: {result['prob']:.1f}% ({result['hits']}/{result['total']}) | Promedio: {result['avg']:.1f} | Valores: {result['values']}")

print("\n🏀 ANÁLISIS FULL GAME - CHI @ CHA\n")

# Coby White - PTS FULL Under 23.5
result = analyze_player_pick(chi_df, 'Coby White', 'PTS', 23.5, 'UNDER', 'FULL')
print(f"Coby White PTS FULL Under 23.5: {result['prob']:.1f}% ({result['hits']}/{result['total']}) | Promedio: {result['avg']:.1f}")

# Josh Giddey - AST FULL Under 9.5
result = analyze_player_pick(chi_df, 'Josh Giddey', 'AST', 9.5, 'UNDER', 'FULL')
print(f"Josh Giddey AST FULL Under 9.5: {result['prob']:.1f}% ({result['hits']}/{result['total']}) | Promedio: {result['avg']:.1f}")

# Josh Giddey - REB FULL Over 8.5
result = analyze_player_pick(chi_df, 'Josh Giddey', 'REB', 8.5, 'OVER', 'FULL')
print(f"Josh Giddey REB FULL Over 8.5: {result['prob']:.1f}% ({result['hits']}/{result['total']}) | Promedio: {result['avg']:.1f}")

# Brandon Miller - REB FULL Over 3.5
result = analyze_player_pick(cha_df, 'Brandon Miller', 'REB', 3.5, 'OVER', 'FULL')
print(f"Brandon Miller REB FULL Over 3.5: {result['prob']:.1f}% ({result['hits']}/{result['total']}) | Promedio: {result['avg']:.1f}")

# LaMelo Ball - AST FULL Over 7.5
result = analyze_player_pick(cha_df, 'LaMelo Ball', 'AST', 7.5, 'OVER', 'FULL')
print(f"LaMelo Ball AST FULL Over 7.5: {result['prob']:.1f}% ({result['hits']}/{result['total']}) | Promedio: {result['avg']:.1f}")

# Miles Bridges - 3PM FULL Under 2.5
result = analyze_player_pick(cha_df, 'Miles Bridges', '3PM', 2.5, 'UNDER', 'FULL')
print(f"Miles Bridges 3PM FULL Under 2.5: {result['prob']:.1f}% ({result['hits']}/{result['total']}) | Promedio: {result['avg']:.1f}")

print("\n" + "="*60)
print("ANÁLISIS DE JUGADORES - JUEGO ORL @ DET")
print("="*60)

print("\n🏀 ANÁLISIS Q1 - ORL @ DET\n")

# Cade Cunningham - PTS Q1 Over 5.5
result = analyze_player_pick(det_df, 'Cade Cunningham', 'PTS', 5.5, 'OVER', 'Q1')
print(f"Cade Cunningham PTS Q1 Over 5.5: {result['prob']:.1f}% ({result['hits']}/{result['total']}) | Promedio: {result['avg']:.1f}")

# Franz Wagner - PTS Q1 Over 5.5
result = analyze_player_pick(orl_df, 'Franz Wagner', 'PTS', 5.5, 'OVER', 'Q1')
print(f"Franz Wagner PTS Q1 Over 5.5: {result['prob']:.1f}% ({result['hits']}/{result['total']}) | Promedio: {result['avg']:.1f}")

# Jalen Duren - REB Q1 Over 2.5
result = analyze_player_pick(det_df, 'Jalen Duren', 'REB', 2.5, 'OVER', 'Q1')
print(f"Jalen Duren REB Q1 Over 2.5: {result['prob']:.1f}% ({result['hits']}/{result['total']}) | Promedio: {result['avg']:.1f}")

# Desmond Bane - PTS Q1 Over 4.5
result = analyze_player_pick(orl_df, 'Desmond Bane', 'PTS', 4.5, 'OVER', 'Q1')
print(f"Desmond Bane PTS Q1 Over 4.5: {result['prob']:.1f}% ({result['hits']}/{result['total']}) | Promedio: {result['avg']:.1f}")

print("\n🏀 ANÁLISIS FULL GAME - ORL @ DET\n")

# Cade Cunningham - PTS FULL Over 28.5
result = analyze_player_pick(det_df, 'Cade Cunningham', 'PTS', 28.5, 'OVER', 'FULL')
print(f"Cade Cunningham PTS FULL Over 28.5: {result['prob']:.1f}% ({result['hits']}/{result['total']}) | Promedio: {result['avg']:.1f}")

# Franz Wagner - PTS FULL Under 23.5
result = analyze_player_pick(orl_df, 'Franz Wagner', 'PTS', 23.5, 'UNDER', 'FULL')
print(f"Franz Wagner PTS FULL Under 23.5: {result['prob']:.1f}% ({result['hits']}/{result['total']}) | Promedio: {result['avg']:.1f}")

# Jalen Duren - PTS FULL Over 18.5
result = analyze_player_pick(det_df, 'Jalen Duren', 'PTS', 18.5, 'UNDER', 'FULL')
print(f"Jalen Duren PTS FULL Under 18.5: {result['prob']:.1f}% ({result['hits']}/{result['total']}) | Promedio: {result['avg']:.1f}")

# Duncan Robinson - 3PM FULL Over 2.5
result = analyze_player_pick(det_df, 'Duncan Robinson', '3PM', 2.5, 'OVER', 'FULL')
print(f"Duncan Robinson 3PM FULL Over 2.5: {result['prob']:.1f}% ({result['hits']}/{result['total']}) | Promedio: {result['avg']:.1f}")

print("\n" + "="*60)
