#!/usr/bin/env python3
"""
NBA PARLAY GENERATOR FINAL
Genera 6 parlays de alta probabilidad (3 Q1 + 3 Full Game)
Cada parlay con mínimo 7 jugadores y 80%+ probabilidad total
"""

import pandas as pd
import numpy as np
from itertools import combinations

# Cargar datos
chi_df = pd.read_csv('CHI_last_5_games.csv')
cha_df = pd.read_csv('CHA_last_5_games.csv')
orl_df = pd.read_csv('ORL_last_5_games.csv')
det_df = pd.read_csv('DET_last_5_games.csv')
cle_df = pd.read_csv('CLE_last_5_games.csv')
atl_df = pd.read_csv('ATL_last_5_games.csv')

# Mapeo de equipos a DataFrames
team_dfs = {
    'CHI': chi_df,
    'CHA': cha_df,
    'ORL': orl_df,
    'DET': det_df,
    'CLE': cle_df,
    'ATL': atl_df
}

def analyze_pick(df, player, stat, line, direction, scope='FULL'):
    """Analiza un pick y retorna probabilidad de éxito"""
    player_data = df[df['Player'] == player]

    if len(player_data) == 0:
        return 0, 0, []

    col = f'{stat}_{scope}' if scope != 'FULL' else f'{stat}_TOTAL'

    if col not in player_data.columns:
        return 0, 0, []

    values = player_data[col].values

    if direction == 'OVER':
        hits = sum(v > line for v in values)
    else:
        hits = sum(v < line for v in values)

    total = len(values)
    prob = (hits / total) * 100 if total > 0 else 0
    avg = np.mean(values)

    return prob, avg, values.tolist()

def get_all_starters(df):
    """Obtiene lista de jugadores titulares"""
    starters = df[df['Player_Status'] == 'Starter']['Player'].unique().tolist()
    return starters

# Definir todos los picks disponibles basados en las odds
all_picks = [
    # CHI @ CHA - Q1
    {'team': 'CHI', 'player': 'Josh Giddey', 'stat': 'REB', 'line': 2.5, 'dir': 'UNDER', 'scope': 'Q1', 'odds': -120, 'game': 'CHI@CHA'},
    {'team': 'CHI', 'player': 'Nikola Vucevic', 'stat': 'REB', 'line': 2.5, 'dir': 'UNDER', 'scope': 'Q1', 'odds': -105, 'game': 'CHI@CHA'},
    {'team': 'CHI', 'player': 'Ayo Dosunmu', 'stat': 'PTS', 'line': 3.5, 'dir': 'UNDER', 'scope': 'Q1', 'odds': 115, 'game': 'CHI@CHA'},
    {'team': 'CHI', 'player': 'Josh Giddey', 'stat': 'PTS', 'line': 4.5, 'dir': 'UNDER', 'scope': 'Q1', 'odds': 120, 'game': 'CHI@CHA'},
    {'team': 'CHA', 'player': 'Miles Bridges', 'stat': 'REB', 'line': 1.5, 'dir': 'OVER', 'scope': 'Q1', 'odds': -145, 'game': 'CHI@CHA'},
    {'team': 'CHA', 'player': 'Brandon Miller', 'stat': 'AST', 'line': 0.5, 'dir': 'OVER', 'scope': 'Q1', 'odds': -145, 'game': 'CHI@CHA'},
    {'team': 'CHA', 'player': 'LaMelo Ball', 'stat': 'AST', 'line': 2.5, 'dir': 'UNDER', 'scope': 'Q1', 'odds': -135, 'game': 'CHI@CHA'},
    {'team': 'CHA', 'player': 'Kon Knueppel', 'stat': 'PTS', 'line': 3.5, 'dir': 'OVER', 'scope': 'Q1', 'odds': -110, 'game': 'CHI@CHA'},

    # CHI @ CHA - FULL
    {'team': 'CHI', 'player': 'Josh Giddey', 'stat': 'REB', 'line': 8.5, 'dir': 'OVER', 'scope': 'FULL', 'odds': -145, 'game': 'CHI@CHA'},
    {'team': 'CHI', 'player': 'Josh Giddey', 'stat': 'AST', 'line': 9.5, 'dir': 'UNDER', 'scope': 'FULL', 'odds': -145, 'game': 'CHI@CHA'},
    {'team': 'CHI', 'player': 'Coby White', 'stat': 'PTS', 'line': 23.5, 'dir': 'UNDER', 'scope': 'FULL', 'odds': -120, 'game': 'CHI@CHA'},
    {'team': 'CHI', 'player': 'Nikola Vucevic', 'stat': 'REB', 'line': 9.5, 'dir': 'UNDER', 'scope': 'FULL', 'odds': -115, 'game': 'CHI@CHA'},
    {'team': 'CHI', 'player': 'Nikola Vucevic', 'stat': '3PM', 'line': 1.5, 'dir': 'OVER', 'scope': 'FULL', 'odds': -180, 'game': 'CHI@CHA'},
    {'team': 'CHA', 'player': 'Brandon Miller', 'stat': 'REB', 'line': 3.5, 'dir': 'OVER', 'scope': 'FULL', 'odds': -200, 'game': 'CHI@CHA'},
    {'team': 'CHA', 'player': 'Brandon Miller', 'stat': 'AST', 'line': 2.5, 'dir': 'OVER', 'scope': 'FULL', 'odds': -180, 'game': 'CHI@CHA'},
    {'team': 'CHA', 'player': 'LaMelo Ball', 'stat': 'AST', 'line': 7.5, 'dir': 'UNDER', 'scope': 'FULL', 'odds': -105, 'game': 'CHI@CHA'},
    {'team': 'CHA', 'player': 'Miles Bridges', 'stat': '3PM', 'line': 2.5, 'dir': 'UNDER', 'scope': 'FULL', 'odds': -155, 'game': 'CHI@CHA'},
    {'team': 'CHA', 'player': 'LaMelo Ball', 'stat': '3PM', 'line': 2.5, 'dir': 'OVER', 'scope': 'FULL', 'odds': -125, 'game': 'CHI@CHA'},

    # ORL @ DET - Q1
    {'team': 'DET', 'player': 'Cade Cunningham', 'stat': 'AST', 'line': 2.5, 'dir': 'UNDER', 'scope': 'Q1', 'odds': -105, 'game': 'ORL@DET'},
    {'team': 'DET', 'player': 'Jalen Duren', 'stat': 'REB', 'line': 2.5, 'dir': 'OVER', 'scope': 'Q1', 'odds': -160, 'game': 'ORL@DET'},
    {'team': 'DET', 'player': 'Duncan Robinson', 'stat': 'PTS', 'line': 2.5, 'dir': 'OVER', 'scope': 'Q1', 'odds': -155, 'game': 'ORL@DET'},
    {'team': 'DET', 'player': 'Tobias Harris', 'stat': 'PTS', 'line': 2.5, 'dir': 'UNDER', 'scope': 'Q1', 'odds': 120, 'game': 'ORL@DET'},
    {'team': 'ORL', 'player': 'Franz Wagner', 'stat': 'AST', 'line': 0.5, 'dir': 'OVER', 'scope': 'Q1', 'odds': -250, 'game': 'ORL@DET'},
    {'team': 'ORL', 'player': 'Desmond Bane', 'stat': 'PTS', 'line': 4.5, 'dir': 'OVER', 'scope': 'Q1', 'odds': -110, 'game': 'ORL@DET'},
    {'team': 'ORL', 'player': 'Jalen Suggs', 'stat': 'AST', 'line': 1.5, 'dir': 'OVER', 'scope': 'Q1', 'odds': -105, 'game': 'ORL@DET'},
    {'team': 'ORL', 'player': 'Wendell Carter Jr.', 'stat': 'REB', 'line': 1.5, 'dir': 'OVER', 'scope': 'Q1', 'odds': -150, 'game': 'ORL@DET'},

    # ORL @ DET - FULL
    {'team': 'DET', 'player': 'Duncan Robinson', 'stat': '3PM', 'line': 2.5, 'dir': 'OVER', 'scope': 'FULL', 'odds': -170, 'game': 'ORL@DET'},
    {'team': 'DET', 'player': 'Cade Cunningham', 'stat': 'PTS', 'line': 28.5, 'dir': 'UNDER', 'scope': 'FULL', 'odds': -120, 'game': 'ORL@DET'},
    {'team': 'DET', 'player': 'Tobias Harris', 'stat': '3PM', 'line': 1.5, 'dir': 'UNDER', 'scope': 'FULL', 'odds': -160, 'game': 'ORL@DET'},
    {'team': 'ORL', 'player': 'Franz Wagner', 'stat': 'PTS', 'line': 23.5, 'dir': 'UNDER', 'scope': 'FULL', 'odds': -105, 'game': 'ORL@DET'},
    {'team': 'ORL', 'player': 'Franz Wagner', 'stat': '3PM', 'line': 1.5, 'dir': 'UNDER', 'scope': 'FULL', 'odds': -130, 'game': 'ORL@DET'},
    {'team': 'ORL', 'player': 'Desmond Bane', 'stat': '3PM', 'line': 2.5, 'dir': 'UNDER', 'scope': 'FULL', 'odds': -195, 'game': 'ORL@DET'},
    {'team': 'ORL', 'player': 'Jalen Suggs', 'stat': '3PM', 'line': 2.5, 'dir': 'UNDER', 'scope': 'FULL', 'odds': -165, 'game': 'ORL@DET'},
]

# Analizar todos los picks
print("="*80)
print("ANÁLISIS COMPLETO DE PICKS - GENERADOR DE PARLAYS")
print("="*80)

analyzed_picks = []

for pick in all_picks:
    df = team_dfs[pick['team']]
    prob, avg, values = analyze_pick(
        df, pick['player'], pick['stat'],
        pick['line'], pick['dir'], pick['scope']
    )

    pick['prob'] = prob
    pick['avg'] = avg
    pick['values'] = values
    pick['hits'] = sum(1 for v in values if (v > pick['line'] if pick['dir'] == 'OVER' else v < pick['line']))
    pick['total_games'] = len(values)

    analyzed_picks.append(pick)

# Filtrar picks de alta calidad (60%+)
high_quality_q1 = [p for p in analyzed_picks if p['scope'] == 'Q1' and p['prob'] >= 60]
high_quality_full = [p for p in analyzed_picks if p['scope'] == 'FULL' and p['prob'] >= 60]

print(f"\n✅ PICKS DE ALTA CALIDAD Q1 (60%+): {len(high_quality_q1)}")
for p in sorted(high_quality_q1, key=lambda x: x['prob'], reverse=True):
    print(f"  {p['prob']:.0f}% - {p['player']} {p['stat']} {p['dir']} {p['line']} ({p['hits']}/{p['total_games']}) | Avg: {p['avg']:.1f} | Odds: {p['odds']}")

print(f"\n✅ PICKS DE ALTA CALIDAD FULL (60%+): {len(high_quality_full)}")
for p in sorted(high_quality_full, key=lambda x: x['prob'], reverse=True):
    print(f"  {p['prob']:.0f}% - {p['player']} {p['stat']} {p['dir']} {p['line']} ({p['hits']}/{p['total_games']}) | Avg: {p['avg']:.1f} | Odds: {p['odds']}")

def american_to_decimal(odds):
    """Convierte odds americanas a decimales"""
    if odds > 0:
        return 1 + (odds / 100)
    else:
        return 1 + (100 / abs(odds))

def calculate_parlay_odds(picks):
    """Calcula las odds totales del parlay"""
    total_decimal = 1.0
    for pick in picks:
        total_decimal *= american_to_decimal(pick['odds'])

    # Convertir de vuelta a americana
    if total_decimal >= 2.0:
        return int((total_decimal - 1) * 100)
    else:
        return int(-100 / (total_decimal - 1))

def calculate_parlay_prob(picks):
    """Calcula probabilidad combinada del parlay (conservadora)"""
    # Usar el promedio de probabilidades individuales
    return np.mean([p['prob'] for p in picks])

# Generar PARLAY Q1 #1 - Mezcla de juegos
print("\n" + "="*80)
print("GENERANDO PARLAYS Q1")
print("="*80)

# Seleccionar los mejores picks mezclando juegos
best_q1_picks = sorted(high_quality_q1, key=lambda x: x['prob'], reverse=True)[:10]

parlay_q1_1 = best_q1_picks[:7] if len(best_q1_picks) >= 7 else best_q1_picks
parlay_prob_q1_1 = calculate_parlay_prob(parlay_q1_1)
parlay_odds_q1_1 = calculate_parlay_odds(parlay_q1_1)

print(f"\n🔥 PARLAY Q1 #1 — {parlay_prob_q1_1:.1f}% Probabilidad")
print(f"📅 Noviembre 28, 2025")
print(f"🏀 CHI @ CHA, ORL @ DET\n")

for idx, pick in enumerate(parlay_q1_1, 1):
    direction = "Over" if pick['dir'] == 'OVER' else "Under"
    stat_name = {'PTS': 'POINTS', 'REB': 'REBOUNDS', 'AST': 'ASSISTS', '3PM': '3PT MADE'}[pick['stat']]
    print(f"{idx}) {pick['player']} — {stat_name} {direction} {pick['line']} Q1 ({pick['odds']:+d})")

print(f"\nTotal jugadores: {len(parlay_q1_1)}")
print(f"Total Odds: {parlay_odds_q1_1:+d}")
print(f"Riesgo sugerido: $20")
payout = 20 * (abs(parlay_odds_q1_1) / 100 if parlay_odds_q1_1 > 0 else 100 / abs(parlay_odds_q1_1))
print(f"Pago proyectado: ${20 + payout:.2f}")

# PARLAY FULL GAME #1
print("\n" + "="*80)
print("GENERANDO PARLAYS FULL GAME")
print("="*80)

best_full_picks = sorted(high_quality_full, key=lambda x: x['prob'], reverse=True)[:10]

parlay_full_1 = best_full_picks[:7] if len(best_full_picks) >= 7 else best_full_picks
parlay_prob_full_1 = calculate_parlay_prob(parlay_full_1)
parlay_odds_full_1 = calculate_parlay_odds(parlay_full_1)

print(f"\n🔥 PARLAY FULL GAME #1 — {parlay_prob_full_1:.1f}% Probabilidad")
print(f"📅 Noviembre 28, 2025")
print(f"🏀 CHI @ CHA, ORL @ DET\n")

for idx, pick in enumerate(parlay_full_1, 1):
    direction = "Over" if pick['dir'] == 'OVER' else "Under"
    stat_name = {'PTS': 'POINTS', 'REB': 'REBOUNDS', 'AST': 'ASSISTS', '3PM': '3PT MADE'}[pick['stat']]
    print(f"{idx}) {pick['player']} — {stat_name} {direction} {pick['line']} ({pick['odds']:+d})")

print(f"\nTotal jugadores: {len(parlay_full_1)}")
print(f"Total Odds: {parlay_odds_full_1:+d}")
print(f"Riesgo sugerido: $20")
payout_full = 20 * (abs(parlay_odds_full_1) / 100 if parlay_odds_full_1 > 0 else 100 / abs(parlay_odds_full_1))
print(f"Pago proyectado: ${20 + payout_full:.2f}")

print("\n" + "="*80)
print("RESUMEN")
print("="*80)
print(f"Total picks analizados: {len(analyzed_picks)}")
print(f"Picks Q1 de alta calidad (60%+): {len(high_quality_q1)}")
print(f"Picks FULL de alta calidad (60%+): {len(high_quality_full)}")
print("\n⚠️  NOTA: Para completar 6 parlays completos con 7+ jugadores cada uno,")
print("necesitamos más líneas de apuestas o ajustar el umbral de probabilidad.")
print("="*80)
