#!/usr/bin/env python3
"""
NBA SCRAPER PROFESIONAL
Genera archivos Excel con estadísticas TOTALES de los últimos 5 juegos
SOLO JUGADORES REGULARES (mínimo 20 minutos promedio)
"""

import requests
import pandas as pd
from datetime import datetime
import time
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# Minutos mínimos promedio para ser considerado REGULAR
MIN_MINUTES_FOR_STARTER = 20.0

# Paleta de colores vibrantes
VIBRANT_COLORS = [
    '4A90E2', '50C878', 'FF8C42', '9B59B6', 'F4D03F',
    'FF69B4', '48D1CC', 'FF7F50', '32CD32', '8A2BE2',
    'FA8072', 'FFD700', '00CED1', 'FF00FF', '3EB489'
]

# Mapeo de equipos
TEAM_ABBREVIATIONS = {
    'ATL': '1', 'BOS': '2', 'NOP': '3', 'CHI': '4', 'CLE': '5',
    'DAL': '6', 'DEN': '7', 'DET': '8', 'GSW': '9', 'HOU': '10',
    'IND': '11', 'LAC': '12', 'LAL': '13', 'MIA': '14', 'MIL': '15',
    'MIN': '16', 'BKN': '17', 'NYK': '18', 'ORL': '19', 'PHI': '20',
    'PHX': '21', 'POR': '22', 'SAC': '23', 'SAS': '24', 'OKC': '25',
    'UTA': '26', 'WAS': '27', 'TOR': '28', 'MEM': '29', 'CHA': '30'
}

# ============================================================================
# FUNCIONES DE API
# ============================================================================

def get_todays_games():
    """Obtiene equipos que juegan HOY"""
    today = datetime.now().strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={today}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        data = response.json()

        teams_playing = []
        game_info = {}
        events = data.get('events', [])

        if not events:
            print(f"ℹ️  No hay juegos HOY ({datetime.now().strftime('%Y-%m-%d')})")
            return [], {}

        print(f"\n{'='*70}")
        print(f"JUEGOS DE HOY: {datetime.now().strftime('%A, %B %d, %Y')}")
        print(f"{'='*70}\n")

        for idx, event in enumerate(events, 1):
            competition = event.get('competitions', [{}])[0]
            competitors = competition.get('competitors', [])

            if len(competitors) >= 2:
                away_comp = competitors[0]
                home_comp = competitors[1]

                away = away_comp.get('team', {}).get('abbreviation', '')
                home = home_comp.get('team', {}).get('abbreviation', '')
                away_name = away_comp.get('team', {}).get('displayName', '')
                home_name = home_comp.get('team', {}).get('displayName', '')

                if away and away in TEAM_ABBREVIATIONS:
                    teams_playing.append(away)
                    game_info[away] = {'opponent': home_name, 'is_home': False}

                if home and home in TEAM_ABBREVIATIONS:
                    teams_playing.append(home)
                    game_info[home] = {'opponent': away_name, 'is_home': True}

                status = competition.get('status', {}).get('type', {}).get('name', '')
                print(f"{idx}. {away} @ {home} ({status})")

        print(f"\n{'='*70}")
        print(f"✅ Total equipos: {len(teams_playing)}")
        print(f"{'='*70}\n")

        return teams_playing, game_info

    except Exception as e:
        print(f"❌ Error: {e}")
        return [], {}

def get_team_last_games(team_id, limit=5):
    """Obtiene IDs de los últimos N juegos completados"""
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/schedule"

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        data = response.json()

        completed_games = []
        for event in data.get('events', []):
            competition = event.get('competitions', [{}])[0]
            status = competition.get('status', {})

            if status.get('type', {}).get('completed', False):
                game_date = event.get('date', '')
                date_obj = None

                if game_date:
                    try:
                        date_obj = datetime.strptime(game_date, '%Y-%m-%dT%H:%MZ')
                        game_date_str = date_obj.strftime('%Y-%m-%d')
                    except:
                        continue

                competitors = competition.get('competitors', [])
                home_team = ''
                away_team = ''

                for comp in competitors:
                    team_name = comp.get('team', {}).get('displayName', '')
                    if comp.get('homeAway') == 'home':
                        home_team = team_name
                    else:
                        away_team = team_name

                completed_games.append({
                    'game_id': event.get('id'),
                    'date': game_date_str,
                    'date_obj': date_obj,
                    'home_team': home_team,
                    'away_team': away_team
                })

        completed_games.sort(key=lambda x: x['date_obj'], reverse=True)
        return completed_games[:limit]

    except Exception as e:
        print(f"  ❌ Error obteniendo calendario: {e}")
        return []

def get_game_stats(game_id, team_id):
    """
    Obtiene estadísticas TOTALES del juego
    Retorna: dict con stats por jugador
    """
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={game_id}"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        boxscore = data.get('boxscore', {})
        players_data = boxscore.get('players', [])

        player_stats = {}

        for team_data in players_data:
            if str(team_data.get('team', {}).get('id')) != str(team_id):
                continue

            statistics = team_data.get('statistics', [])
            if not statistics:
                continue

            stats_info = statistics[0]
            labels = stats_info.get('labels', [])
            athletes = stats_info.get('athletes', [])

            for player in athletes:
                athlete_info = player.get('athlete', {})
                player_name = athlete_info.get('displayName', '')
                stats = player.get('stats', [])

                if not stats or not player_name:
                    continue

                stats_dict = {label: value for label, value in zip(labels, stats)}

                # Obtener minutos
                minutes_raw = stats_dict.get('MIN', '0')
                min_value = 0.0

                if isinstance(minutes_raw, str) and ':' in minutes_raw:
                    parts = minutes_raw.split(':')
                    min_value = int(parts[0]) + (int(parts[1]) / 60.0) if len(parts) == 2 else 0.0
                elif str(minutes_raw).replace('.', '').isdigit():
                    min_value = float(minutes_raw)

                # FILTRO: Solo jugadores con minutos > 0
                if min_value <= 0:
                    continue

                # Obtener estadísticas
                pts = stats_dict.get('PTS', '0')
                reb = stats_dict.get('REB', '0')
                ast = stats_dict.get('AST', '0')
                three_pt_raw = stats_dict.get('3PT', '0-0')

                three_pt = three_pt_raw.split('-')[0] if '-' in str(three_pt_raw) else '0'

                player_stats[player_name] = {
                    'PTS': int(pts) if str(pts).isdigit() else 0,
                    'REB': int(reb) if str(reb).isdigit() else 0,
                    'AST': int(ast) if str(ast).isdigit() else 0,
                    '3PM': int(three_pt) if str(three_pt).isdigit() else 0,
                    'MIN': round(min_value, 1)
                }

        return player_stats

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return {}

# ============================================================================
# FUNCIONES DE PROCESAMIENTO
# ============================================================================

def calculate_predictions(player_games, next_opponent, is_home):
    """Calcula predicciones quirúrgicas"""
    if not player_games:
        return {'PRED_PTS': 0, 'PRED_REB': 0, 'PRED_AST': 0, 'PRED_3PM': 0}

    games = sorted(player_games, key=lambda x: x['Game_Date'], reverse=True)
    base_weights = [0.35, 0.25, 0.20, 0.12, 0.08]

    predictions = {}
    for stat in ['PTS', 'REB', 'AST', '3PM']:
        weighted_sum = 0
        total_weight = 0

        for idx, game in enumerate(games[:5]):
            if idx < len(base_weights):
                value = game.get(stat, 0)
                weight = base_weights[idx]

                # BONUS ubicación
                if game.get('Is_Home', False) == is_home:
                    weight *= 1.3

                # BONUS oponente
                if game.get('Opponent', '') == next_opponent:
                    weight *= 1.5

                weighted_sum += value * weight
                total_weight += weight

        prediction = round(weighted_sum / total_weight, 1) if total_weight > 0 else 0
        predictions[f'PRED_{stat}'] = prediction

    return predictions

def save_to_excel(df, output_file, player_colors):
    """Guarda Excel con colores por jugador"""
    wb = Workbook()
    ws = wb.active

    # Insertar columna Team
    team_abbr = output_file.split('_')[0]
    df.insert(0, 'Team', team_abbr)

    # Headers
    for col_num, column_title in enumerate(df.columns, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = column_title
        cell.fill = PatternFill(start_color='404040', end_color='404040', fill_type='solid')
        cell.font = Font(bold=True, color='FFFFFF')
        cell.alignment = Alignment(horizontal='center', vertical='center')

    # Datos con colores
    for row_num, row_data in enumerate(df.values, 2):
        player_name = row_data[4]  # Player column
        player_color = player_colors.get(player_name, 'FFFFFF')

        for col_num, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_num, column=col_num)
            cell.value = value
            cell.fill = PatternFill(start_color=player_color, end_color=player_color, fill_type='solid')
            cell.alignment = Alignment(horizontal='center', vertical='center')

    # Ajustar anchos
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        ws.column_dimensions[column_letter].width = min(max_length + 2, 20)

    wb.save(output_file)

def process_team(team_abbr, player_colors, next_game_info):
    """Procesa un equipo y genera Excel"""
    team_id = TEAM_ABBREVIATIONS[team_abbr]

    print(f"\n{'='*70}")
    print(f"PROCESANDO: {team_abbr}")
    print(f"{'='*70}")

    # Obtener últimos 5 juegos
    games = get_team_last_games(team_id, limit=5)

    if not games:
        print(f"❌ No hay juegos completados")
        return False

    print(f"✅ {len(games)} juegos encontrados\n")

    all_data = []

    for idx, game in enumerate(games, 1):
        game_id = game['game_id']
        game_date = game['date']
        matchup = f"{game['away_team']} @ {game['home_team']}"

        print(f"  [{idx}/{len(games)}] {matchup} ({game_date})")

        stats = get_game_stats(game_id, team_id)
        print(f"      ✅ {len(stats)} jugadores")

        # Determinar ubicación
        is_home = team_abbr.upper() in game['home_team'].upper()
        opponent = game['away_team'] if is_home else game['home_team']

        for player_name, player_stats in stats.items():
            all_data.append({
                'Game_Date': game_date,
                'Opponent': opponent,
                'Is_Home': is_home,
                'Player': player_name,
                'PTS': player_stats['PTS'],
                'REB': player_stats['REB'],
                'AST': player_stats['AST'],
                '3PM': player_stats['3PM'],
                'MIN': player_stats['MIN']
            })

        time.sleep(0.5)

    # Crear DataFrame
    df = pd.DataFrame(all_data)

    # Calcular promedio de minutos por jugador
    player_avg_min = df.groupby('Player')['MIN'].mean()

    # FILTRAR: Solo jugadores REGULARES (20+ minutos promedio)
    regular_players = player_avg_min[player_avg_min >= MIN_MINUTES_FOR_STARTER].index.tolist()
    df = df[df['Player'].isin(regular_players)]

    if df.empty:
        print(f"❌ No hay jugadores regulares")
        return False

    # Agregar promedio de minutos para ordenar
    df['AVG_MIN'] = df['Player'].map(player_avg_min)

    # ORDENAR: Por minutos (desc), fecha (desc), nombre (asc)
    df = df.sort_values(['AVG_MIN', 'Game_Date', 'Player'], ascending=[False, False, True])

    # Eliminar columna temporal
    df = df.drop(columns=['AVG_MIN'])

    # Formatear fecha
    df['Game_Date'] = pd.to_datetime(df['Game_Date']).dt.strftime('%m/%d')

    # PREDICCIONES
    if next_game_info:
        next_opponent = next_game_info.get('opponent', '')
        is_home_next = next_game_info.get('is_home', False)
        location = "CASA" if is_home_next else "VISITANTE"
        print(f"\n  🎯 Predicciones: vs {next_opponent} ({location})")
    else:
        next_opponent = ''
        is_home_next = False

    player_preds = {}
    for player_name in df['Player'].unique():
        player_games = df[df['Player'] == player_name].to_dict('records')
        preds = calculate_predictions(player_games, next_opponent, is_home_next)
        player_preds[player_name] = preds

    df['PRED_PTS'] = df['Player'].map(lambda x: player_preds.get(x, {}).get('PRED_PTS', 0))
    df['PRED_REB'] = df['Player'].map(lambda x: player_preds.get(x, {}).get('PRED_REB', 0))
    df['PRED_AST'] = df['Player'].map(lambda x: player_preds.get(x, {}).get('PRED_AST', 0))
    df['PRED_3PM'] = df['Player'].map(lambda x: player_preds.get(x, {}).get('PRED_3PM', 0))

    print(f"  ✅ Predicciones: {len(player_preds)} jugadores regulares")

    # Guardar Excel
    output_file = f"{team_abbr}_last_5_games.xlsx"
    save_to_excel(df.copy(), output_file, player_colors)

    print(f"\n✅ EXCEL: {output_file}")
    print(f"📊 Registros: {len(df)} (SOLO REGULARES)")
    print(f"🎨 Colores aplicados\n")

    return True

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("\n" + "="*70)
    print("NBA SCRAPER PROFESIONAL - SOLO JUGADORES REGULARES")
    print("="*70)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}")
    print("="*70 + "\n")

    # Obtener juegos de hoy
    teams_today, game_info = get_todays_games()

    if not teams_today:
        print("\n⚠️  No hay equipos jugando hoy")
        return

    # Recopilar jugadores únicos (solo regulares)
    print(f"\n{'='*70}")
    print("FASE 1: RECOPILANDO JUGADORES REGULARES")
    print(f"{'='*70}\n")

    all_players = set()
    for idx, team_abbr in enumerate(teams_today, 1):
        team_id = TEAM_ABBREVIATIONS[team_abbr]
        print(f"  [{idx}/{len(teams_today)}] {team_abbr}...")

        try:
            games = get_team_last_games(team_id, limit=5)
            for game in games:
                stats = get_game_stats(game['game_id'], team_id)
                all_players.update(stats.keys())
        except:
            pass

        time.sleep(0.3)

    print(f"\n✅ Total jugadores únicos: {len(all_players)}\n")

    # Asignar colores
    sorted_players = sorted(list(all_players))
    player_colors = {}
    for idx, player in enumerate(sorted_players):
        color_idx = idx % len(VIBRANT_COLORS)
        player_colors[player] = VIBRANT_COLORS[color_idx]

    print(f"🎨 Colores asignados: {len(player_colors)}\n")

    # Procesar equipos
    print(f"\n{'='*70}")
    print("FASE 2: GENERANDO ARCHIVOS EXCEL")
    print(f"{'='*70}")

    successful = 0
    failed = 0

    for team_abbr in teams_today:
        try:
            next_game = game_info.get(team_abbr, None)
            if process_team(team_abbr, player_colors, next_game):
                successful += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Error {team_abbr}: {e}")
            failed += 1

        time.sleep(1)

    # Resumen
    print("\n" + "="*70)
    print("RESUMEN FINAL")
    print("="*70)
    print(f"✅ Exitosos: {successful}")
    print(f"❌ Fallidos: {failed}")
    print(f"📁 Archivos generados: {successful}")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
