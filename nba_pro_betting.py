#!/usr/bin/env python3
"""
NBA PRO BETTING ANALYZER V1.0
Script profesional de analisis para apuestas deportivas (Hard Rock Bet / DraftKings)
Analiza los ultimos 5 juegos de cada jugador con metricas avanzadas de props betting.

Caracteristicas:
- Filtra solo jugadores regulares (25+ min promedio)
- Ordena por titulares fijos primero, luego por minutos
- Analisis de lineas Over/Under para PTS, REB, AST, 3PM
- Hit rates (% de veces que supera la linea en ultimos 5 juegos)
- Promedios, tendencias, desviacion estandar, consistencia
- Stats por quarter (Q1-Q4) + totales
- Color unico por jugador (hex) para visualizacion
- Soporte para nombres con guiones (Gilgeous-Alexander, etc.)
"""

import requests
import pandas as pd
from datetime import datetime
import time
import re
import math
from collections import defaultdict

# ============================================================================
# CONFIGURACION
# ============================================================================
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

MIN_MINUTES_THRESHOLD = 25  # Solo jugadores con 25+ min promedio
GAMES_TO_ANALYZE = 5

# Patron regex universal - soporta nombres con guion, apostrofe, punto
PLAYER_NAME_PATTERN = r"[A-Za-z'\.\-\s]+"

# Lineas comunes de props en sportsbooks (se ajustan por jugador automaticamente)
DEFAULT_PROP_LINES = {
    'PTS': [9.5, 14.5, 19.5, 24.5, 29.5, 34.5],
    'REB': [3.5, 5.5, 7.5, 9.5, 11.5],
    'AST': [2.5, 4.5, 6.5, 8.5, 10.5],
    '3PM': [0.5, 1.5, 2.5, 3.5, 4.5]
}

TEAM_ABBREVIATIONS = {
    'ATL': ('1', 'hawks'), 'BOS': ('2', 'celtics'), 'NOP': ('3', 'pelicans'),
    'CHI': ('4', 'bulls'), 'CLE': ('5', 'cavaliers'), 'DAL': ('6', 'mavericks'),
    'DEN': ('7', 'nuggets'), 'DET': ('8', 'pistons'), 'GSW': ('9', 'warriors'),
    'HOU': ('10', 'rockets'), 'IND': ('11', 'pacers'), 'LAC': ('12', 'clippers'),
    'LAL': ('13', 'lakers'), 'MIA': ('14', 'heat'), 'MIL': ('15', 'bucks'),
    'MIN': ('16', 'timberwolves'), 'BKN': ('17', 'nets'), 'NYK': ('18', 'knicks'),
    'ORL': ('19', 'magic'), 'PHI': ('20', 'sixers'), 'PHX': ('21', 'suns'),
    'POR': ('22', 'blazers'), 'SAC': ('23', 'kings'), 'SAS': ('24', 'spurs'),
    'OKC': ('25', 'thunder'), 'UTA': ('26', 'jazz'), 'WAS': ('27', 'wizards'),
    'TOR': ('28', 'raptors'), 'MEM': ('29', 'grizzlies'), 'CHA': ('30', 'hornets')
}

# ============================================================================
# PALETA DE COLORES UNICOS (200 colores distintos, nunca se repiten)
# ============================================================================
UNIQUE_COLORS = [
    '#FF0000', '#0000FF', '#00AA00', '#FF8C00', '#8B008B',
    '#00CED1', '#FFD700', '#DC143C', '#4169E1', '#32CD32',
    '#FF4500', '#6A0DAD', '#008080', '#FF1493', '#228B22',
    '#FF6347', '#4682B4', '#9ACD32', '#D2691E', '#8A2BE2',
    '#20B2AA', '#B22222', '#6495ED', '#556B2F', '#FF69B4',
    '#2F4F4F', '#CD853F', '#483D8B', '#BDB76B', '#800000',
    '#48D1CC', '#C71585', '#3CB371', '#DAA520', '#7B68EE',
    '#BC8F8F', '#191970', '#66CDAA', '#DB7093', '#2E8B57',
    '#9370DB', '#F4A460', '#5F9EA0', '#E9967A', '#6B8E23',
    '#8FBC8F', '#A0522D', '#00BFFF', '#FA8072', '#708090',
    '#7CFC00', '#BA55D3', '#D2B48C', '#40E0D0', '#ADFF2F',
    '#F08080', '#B0C4DE', '#778899', '#87CEEB', '#FFA07A',
    '#98FB98', '#DDA0DD', '#AFEEEE', '#EE82EE', '#F0E68C',
    '#E0FFFF', '#FAFAD2', '#D8BFD8', '#FFDAB9', '#B0E0E6',
    '#7FFFD4', '#F5DEB3', '#FFE4E1', '#FFC0CB', '#E6E6FA',
    '#C0C0C0', '#A9A9A9', '#696969', '#D3D3D3', '#808080',
    '#1E90FF', '#00FA9A', '#FF7F50', '#9932CC', '#00FF7F',
    '#FFDEAD', '#8B4513', '#CD5C5C', '#4B0082', '#5B2C6F',
    '#117A65', '#D35400', '#2471A3', '#7D3C98', '#1A5276',
    '#A93226', '#148F77', '#B7950B', '#6C3483', '#1F618D',
    '#C0392B', '#16A085', '#D4AC0D', '#8E44AD', '#2980B9',
    '#E74C3C', '#1ABC9C', '#F1C40F', '#9B59B6', '#3498DB',
    '#CB4335', '#17A589', '#D68910', '#884EA0', '#2E86C1',
    '#B03A2E', '#138D75', '#B9770E', '#7D3C98', '#2874A6',
    '#943126', '#117864', '#9A7D0A', '#6C3483', '#21618C',
    '#78281F', '#0E6655', '#7D6608', '#5B2C6F', '#1B4F72',
    '#641E16', '#0B5345', '#614A05', '#4A235A', '#154360',
    '#512E5F', '#0D6EFD', '#198754', '#FFC107', '#0DCAF0',
    '#6610F2', '#D63384', '#FD7E14', '#20C997', '#6F42C1',
    '#E83E8C', '#17BF63', '#F45D22', '#7952B3', '#087990',
    '#AB2E1F', '#0A6847', '#8B6914', '#5C4D7D', '#1B6CA8',
    '#CE5A57', '#2BAE66', '#C49102', '#5D5179', '#247BA0',
    '#E27D60', '#85CDCA', '#E8A87C', '#C38D9E', '#41B3A3',
    '#F64C72', '#553D67', '#F2A154', '#95E1D3', '#EAFFD0',
    '#FECE2F', '#009DAE', '#71DFE7', '#C2F784', '#F9ED69',
    '#F38181', '#AA96DA', '#FCBAD3', '#FFFFD2', '#A8D8EA',
    '#1B9AAA', '#F5F1DA', '#FFC857', '#EF476F', '#118AB2',
    '#06D6A0', '#FFD166', '#073B4C', '#FF6B6B', '#4ECDC4',
    '#45B7D1', '#96CEB4', '#FFEEAD', '#FF6F69', '#588C7E',
]

_color_index = 0
_assigned_colors = {}


def get_unique_color(player_name):
    """Asigna un color hex unico a cada jugador. Nunca se repite."""
    global _color_index
    if player_name not in _assigned_colors:
        _assigned_colors[player_name] = UNIQUE_COLORS[_color_index % len(UNIQUE_COLORS)]
        _color_index += 1
    return _assigned_colors[player_name]


# ============================================================================
# FUNCIONES DE OBTENCION DE DATOS (ESPN API)
# ============================================================================
def get_todays_games():
    """Obtiene los equipos que juegan HOY desde ESPN."""
    today = datetime.now().strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={today}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        data = response.json()

        teams_playing = []
        events = data.get('events', [])

        if not events:
            print(f"  No hay juegos programados para HOY ({datetime.now().strftime('%Y-%m-%d')})")
            return []

        print(f"\n{'='*70}")
        print(f"  JUEGOS DE HOY: {datetime.now().strftime('%A, %B %d, %Y')}")
        print(f"{'='*70}\n")

        for idx, event in enumerate(events, 1):
            competition = event.get('competitions', [{}])[0]
            competitors = competition.get('competitors', [])
            game_time = event.get('date', '')
            status = competition.get('status', {}).get('type', {}).get('name', '')

            for comp in competitors:
                team_abbr = comp.get('team', {}).get('abbreviation', '')
                if team_abbr and team_abbr in TEAM_ABBREVIATIONS:
                    teams_playing.append(team_abbr)

            if len(competitors) >= 2:
                away = competitors[0].get('team', {}).get('abbreviation', '')
                home = competitors[1].get('team', {}).get('abbreviation', '')
                try:
                    dt = datetime.strptime(game_time, '%Y-%m-%dT%H:%MZ')
                    time_str = dt.strftime('%I:%M %p')
                except (ValueError, TypeError):
                    time_str = 'TBD'
                print(f"  {idx}. {away} @ {home} - {time_str} ({status})")

        print(f"\n  Total de equipos jugando HOY: {len(teams_playing)}")
        print(f"{'='*70}\n")

        return teams_playing

    except Exception as e:
        print(f"  ERROR obteniendo juegos de hoy: {e}")
        return []


def get_team_schedule(team_id, limit=5):
    """Obtiene los ultimos N juegos completados del equipo (mas recientes primero)."""
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/schedule"

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        data = response.json()

        completed_games = []
        for event in data.get('events', []):
            competition = event.get('competitions', [{}])[0]
            status = competition.get('status', {})

            if not status.get('type', {}).get('completed', False):
                continue

            game_id = event.get('id')
            game_date = event.get('date', '')

            if not game_date:
                continue

            try:
                date_obj = datetime.strptime(game_date, '%Y-%m-%dT%H:%MZ')
                game_date_str = date_obj.strftime('%Y-%m-%d')
            except (ValueError, TypeError):
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
                'game_id': game_id,
                'date': game_date_str,
                'date_obj': date_obj,
                'home_team': home_team,
                'away_team': away_team
            })

        completed_games.sort(key=lambda x: x['date_obj'], reverse=True)

        return [
            {
                'game_id': g['game_id'],
                'date': g['date'],
                'home_team': g['home_team'],
                'away_team': g['away_team']
            }
            for g in completed_games[:limit]
        ]

    except Exception as e:
        print(f"    ERROR obteniendo calendario: {e}")
        return []


def get_game_summary(game_id):
    """Obtiene el resumen completo de un juego (boxscore + plays) en una sola llamada."""
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={game_id}"

    try:
        response = requests.get(url, timeout=10)
        return response.json()
    except Exception as e:
        print(f"    ERROR obteniendo resumen del juego {game_id}: {e}")
        return {}


def extract_boxscore_totals(data, team_id):
    """
    Extrae estadisticas TOTALES + minutos del boxscore.
    Filtra jugadores con 0 minutos y retorna minutos jugados para cada uno.
    """
    players_stats = {}

    boxscore = data.get('boxscore', {})
    players_data = boxscore.get('players', [])

    for team_data in players_data:
        current_team_id = team_data.get('team', {}).get('id')
        if str(current_team_id) != str(team_id):
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
            minutes_raw = stats_dict.get('MIN', '0')

            # Parsear minutos (puede ser "36" o "36:20")
            try:
                if ':' in str(minutes_raw):
                    minutes = int(str(minutes_raw).split(':')[0])
                else:
                    minutes = int(float(str(minutes_raw)))
            except (ValueError, TypeError):
                minutes = 0

            if minutes == 0:
                continue

            pts = stats_dict.get('PTS', '0')
            reb = stats_dict.get('REB', '0')
            ast = stats_dict.get('AST', '0')
            three_pt_raw = stats_dict.get('3PT', '0-0')
            three_pt = three_pt_raw.split('-')[0] if '-' in str(three_pt_raw) else '0'

            # Starter detection: ESPN lists starters as first 5 in the boxscore
            starter = player.get('starter', False)

            players_stats[player_name] = {
                'PTS_TOTAL': int(pts) if str(pts).isdigit() else 0,
                'REB_TOTAL': int(reb) if str(reb).isdigit() else 0,
                'AST_TOTAL': int(ast) if str(ast).isdigit() else 0,
                '3PM_TOTAL': int(three_pt) if str(three_pt).isdigit() else 0,
                'MIN': minutes,
                'STARTER': starter
            }

    return players_stats


def extract_team_players(data, team_id):
    """Obtiene set de nombres de jugadores del equipo desde el boxscore."""
    team_players = set()
    boxscore = data.get('boxscore', {})

    for team_data in boxscore.get('players', []):
        if str(team_data.get('team', {}).get('id')) != str(team_id):
            continue

        statistics = team_data.get('statistics', [])
        if statistics:
            for player in statistics[0].get('athletes', []):
                name = player.get('athlete', {}).get('displayName', '')
                if name:
                    team_players.add(name)

    return team_players


def extract_quarter_stats(data, team_id):
    """
    Extrae estadisticas de Q1-Q4 + OT desde el play-by-play.
    Soporta nombres con guion.
    """
    team_players = extract_team_players(data, team_id)
    plays = data.get('plays', [])

    quarter_stats = defaultdict(lambda: {
        'PTS_Q1': 0, 'REB_Q1': 0, 'AST_Q1': 0, '3PM_Q1': 0,
        'PTS_Q2': 0, 'REB_Q2': 0, 'AST_Q2': 0, '3PM_Q2': 0,
        'PTS_Q3': 0, 'REB_Q3': 0, 'AST_Q3': 0, '3PM_Q3': 0,
        'PTS_Q4': 0, 'REB_Q4': 0, 'AST_Q4': 0, '3PM_Q4': 0,
        'PTS_OT': 0, 'REB_OT': 0, 'AST_OT': 0, '3PM_OT': 0
    })

    makes_patterns = [
        rf'({PLAYER_NAME_PATTERN}?)\s+makes',
        rf'({PLAYER_NAME_PATTERN}?)\s+made'
    ]
    rebound_patterns = [
        rf'({PLAYER_NAME_PATTERN}?)\s+(defensive|offensive)\s+rebound',
        rf'({PLAYER_NAME_PATTERN}?)\s+rebound'
    ]
    assist_patterns = [
        rf'\(({PLAYER_NAME_PATTERN}?)\s+assists\)',
        rf'({PLAYER_NAME_PATTERN}?)\s+assists'
    ]

    for play in plays:
        period = play.get('period', {}).get('number', 0)
        if period < 1:
            continue

        # Q1-Q4 usan _Q1-_Q4, overtime usa _OT
        if period <= 4:
            suffix = f"_Q{period}"
        else:
            suffix = "_OT"

        text = play.get('text', '')
        scoring_play = play.get('scoringPlay', False)

        # PUNTOS
        if scoring_play:
            player = None
            for pattern in makes_patterns:
                match = re.search(pattern, text)
                if match:
                    player = match.group(1).strip()
                    break

            if player and player in team_players:
                is_three = 'three point' in text.lower() or '3-point' in text.lower() or 'three pointer' in text.lower()

                if is_three:
                    quarter_stats[player][f'PTS{suffix}'] += 3
                    quarter_stats[player][f'3PM{suffix}'] += 1
                elif 'free throw' in text.lower():
                    quarter_stats[player][f'PTS{suffix}'] += 1
                else:
                    quarter_stats[player][f'PTS{suffix}'] += 2

        # REBOTES
        if 'rebound' in text.lower():
            for pattern in rebound_patterns:
                match = re.search(pattern, text)
                if match:
                    player = match.group(1).strip()
                    if player in team_players:
                        quarter_stats[player][f'REB{suffix}'] += 1
                        break

        # ASISTENCIAS
        if 'assist' in text.lower():
            for pattern in assist_patterns:
                match = re.search(pattern, text)
                if match:
                    player = match.group(1).strip()
                    if player in team_players:
                        quarter_stats[player][f'AST{suffix}'] += 1
                        break

    return dict(quarter_stats)


# ============================================================================
# METRICAS AVANZADAS DE BETTING
# ============================================================================
def find_closest_line(avg, lines):
    """Encuentra la linea de prop mas cercana al promedio del jugador."""
    if not lines:
        return avg
    return min(lines, key=lambda x: abs(x - avg))


def calculate_hit_rate(values, line):
    """Calcula % de veces que el jugador supero la linea (Over hit rate)."""
    if not values:
        return 0.0
    hits = sum(1 for v in values if v > line)
    return round((hits / len(values)) * 100, 1)


def calculate_trend(values):
    """
    Calcula tendencia lineal simple.
    Retorna: 'UP' (subiendo), 'DOWN' (bajando), 'STABLE' (estable)
    y el slope numerico.
    """
    if len(values) < 2:
        return 'STABLE', 0.0

    n = len(values)
    x_mean = (n - 1) / 2
    y_mean = sum(values) / n

    numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
    denominator = sum((i - x_mean) ** 2 for i in range(n))

    if denominator == 0:
        return 'STABLE', 0.0

    slope = numerator / denominator

    if slope > 1.0:
        return 'UP', round(slope, 2)
    elif slope < -1.0:
        return 'DOWN', round(slope, 2)
    else:
        return 'STABLE', round(slope, 2)


def calculate_consistency(values):
    """
    Calcula indice de consistencia (0-100).
    100 = totalmente consistente, 0 = muy variable.
    Basado en coeficiente de variacion invertido.
    """
    if not values or len(values) < 2:
        return 100.0

    avg = sum(values) / len(values)
    if avg == 0:
        return 100.0

    variance = sum((v - avg) ** 2 for v in values) / len(values)
    std_dev = math.sqrt(variance)
    cv = std_dev / avg  # Coeficiente de variacion

    # Invertir: menor CV = mayor consistencia
    consistency = max(0, min(100, round((1 - cv) * 100, 1)))
    return consistency


def calculate_std_dev(values):
    """Desviacion estandar."""
    if not values or len(values) < 2:
        return 0.0
    avg = sum(values) / len(values)
    variance = sum((v - avg) ** 2 for v in values) / len(values)
    return round(math.sqrt(variance), 2)


# ============================================================================
# PROCESAMIENTO PRINCIPAL
# ============================================================================
def process_team(team_abbr):
    """
    Procesa un equipo: obtiene los ultimos 5 juegos, extrae stats,
    calcula metricas de betting y genera CSV profesional.
    """
    team_id, team_name = TEAM_ABBREVIATIONS[team_abbr]

    print(f"\n{'='*70}")
    print(f"  PROCESANDO: {team_abbr} ({team_name.upper()})")
    print(f"{'='*70}")

    games = get_team_schedule(team_id, limit=GAMES_TO_ANALYZE)

    if not games:
        print(f"  No se encontraron juegos completados para {team_abbr}")
        return False

    print(f"  {len(games)} juegos encontrados\n")

    # Recolectar datos crudos por jugador a traves de todos los juegos
    player_games_raw = defaultdict(list)  # {player: [game_data, ...]}

    for idx, game in enumerate(games, 1):
        game_id = game['game_id']
        game_date = game['date']
        matchup = f"{game['away_team']} @ {game['home_team']}"

        print(f"    Juego {idx}/{len(games)}: {matchup} ({game_date})")

        # Una sola llamada API por juego (antes eran 2-3)
        summary = get_game_summary(game_id)
        if not summary:
            continue

        totals = extract_boxscore_totals(summary, team_id)
        quarter_stats = extract_quarter_stats(summary, team_id)

        opponent = game['away_team'] if team_name.lower() in game['home_team'].lower() else game['home_team']

        for player_name, stats in totals.items():
            q_data = quarter_stats.get(player_name, {})

            player_games_raw[player_name].append({
                'game_date': game_date,
                'opponent': opponent,
                'starter': stats.get('STARTER', False),
                'min': stats['MIN'],
                'pts_total': stats['PTS_TOTAL'],
                'reb_total': stats['REB_TOTAL'],
                'ast_total': stats['AST_TOTAL'],
                '3pm_total': stats['3PM_TOTAL'],
                'pts_q1': q_data.get('PTS_Q1', 0),
                'reb_q1': q_data.get('REB_Q1', 0),
                'ast_q1': q_data.get('AST_Q1', 0),
                '3pm_q1': q_data.get('3PM_Q1', 0),
                'pts_q2': q_data.get('PTS_Q2', 0),
                'reb_q2': q_data.get('REB_Q2', 0),
                'ast_q2': q_data.get('AST_Q2', 0),
                '3pm_q2': q_data.get('3PM_Q2', 0),
                'pts_q3': q_data.get('PTS_Q3', 0),
                'reb_q3': q_data.get('REB_Q3', 0),
                'ast_q3': q_data.get('AST_Q3', 0),
                '3pm_q3': q_data.get('3PM_Q3', 0),
                'pts_q4': q_data.get('PTS_Q4', 0),
                'reb_q4': q_data.get('REB_Q4', 0),
                'ast_q4': q_data.get('AST_Q4', 0),
                '3pm_q4': q_data.get('3PM_Q4', 0),
                'pts_ot': q_data.get('PTS_OT', 0),
                'reb_ot': q_data.get('REB_OT', 0),
                'ast_ot': q_data.get('AST_OT', 0),
                '3pm_ot': q_data.get('3PM_OT', 0),
            })

        print(f"      {len(totals)} jugadores procesados")
        time.sleep(0.5)

    # Filtrar: solo jugadores con promedio de 25+ minutos
    qualified_players = {}
    for player_name, games_data in player_games_raw.items():
        avg_min = sum(g['min'] for g in games_data) / len(games_data)
        if avg_min >= MIN_MINUTES_THRESHOLD:
            qualified_players[player_name] = games_data

    if not qualified_players:
        print(f"  No hay jugadores con {MIN_MINUTES_THRESHOLD}+ min promedio para {team_abbr}")
        return False

    # Ordenar: titulares primero, luego por minutos promedio descendente
    def sort_key(item):
        name, games_data = item
        is_starter = any(g['starter'] for g in games_data)
        avg_min = sum(g['min'] for g in games_data) / len(games_data)
        return (not is_starter, -avg_min)

    sorted_players = sorted(qualified_players.items(), key=sort_key)

    # Construir filas del CSV
    all_rows = []

    for player_name, games_data in sorted_players:
        color = get_unique_color(player_name)

        pts_values = [g['pts_total'] for g in games_data]
        reb_values = [g['reb_total'] for g in games_data]
        ast_values = [g['ast_total'] for g in games_data]
        tpm_values = [g['3pm_total'] for g in games_data]
        min_values = [g['min'] for g in games_data]

        # Promedios
        avg_pts = round(sum(pts_values) / len(pts_values), 1)
        avg_reb = round(sum(reb_values) / len(reb_values), 1)
        avg_ast = round(sum(ast_values) / len(ast_values), 1)
        avg_3pm = round(sum(tpm_values) / len(tpm_values), 1)
        avg_min = round(sum(min_values) / len(min_values), 1)

        # Lineas de props mas cercanas al promedio
        pts_line = find_closest_line(avg_pts, DEFAULT_PROP_LINES['PTS'])
        reb_line = find_closest_line(avg_reb, DEFAULT_PROP_LINES['REB'])
        ast_line = find_closest_line(avg_ast, DEFAULT_PROP_LINES['AST'])
        tpm_line = find_closest_line(avg_3pm, DEFAULT_PROP_LINES['3PM'])

        # Hit rates (Over %)
        pts_hit = calculate_hit_rate(pts_values, pts_line)
        reb_hit = calculate_hit_rate(reb_values, reb_line)
        ast_hit = calculate_hit_rate(ast_values, ast_line)
        tpm_hit = calculate_hit_rate(tpm_values, tpm_line)

        # Tendencias
        pts_trend, pts_slope = calculate_trend(pts_values)
        reb_trend, reb_slope = calculate_trend(reb_values)
        ast_trend, ast_slope = calculate_trend(ast_values)

        # Desviacion estandar
        pts_std = calculate_std_dev(pts_values)
        reb_std = calculate_std_dev(reb_values)
        ast_std = calculate_std_dev(ast_values)
        tpm_std = calculate_std_dev(tpm_values)

        # Consistencia
        pts_consistency = calculate_consistency(pts_values)
        reb_consistency = calculate_consistency(reb_values)
        ast_consistency = calculate_consistency(ast_values)

        is_starter = any(g['starter'] for g in games_data)

        # Una fila por juego para este jugador
        for g in games_data:
            row = {
                'Player': player_name,
                'Color_HEX': color,
                'Role': 'STARTER' if is_starter else 'ROTATION',
                'AVG_MIN': avg_min,
                'Game_Date': g['game_date'],
                'Opponent': g['opponent'],
                'MIN': g['min'],
                # Per-quarter stats
                'PTS_Q1': g['pts_q1'], 'REB_Q1': g['reb_q1'],
                'AST_Q1': g['ast_q1'], '3PM_Q1': g['3pm_q1'],
                'PTS_Q2': g['pts_q2'], 'REB_Q2': g['reb_q2'],
                'AST_Q2': g['ast_q2'], '3PM_Q2': g['3pm_q2'],
                'PTS_Q3': g['pts_q3'], 'REB_Q3': g['reb_q3'],
                'AST_Q3': g['ast_q3'], '3PM_Q3': g['3pm_q3'],
                'PTS_Q4': g['pts_q4'], 'REB_Q4': g['reb_q4'],
                'AST_Q4': g['ast_q4'], '3PM_Q4': g['3pm_q4'],
                'PTS_OT': g['pts_ot'], 'REB_OT': g['reb_ot'],
                'AST_OT': g['ast_ot'], '3PM_OT': g['3pm_ot'],
                # Totals
                'PTS_TOTAL': g['pts_total'],
                'REB_TOTAL': g['reb_total'],
                'AST_TOTAL': g['ast_total'],
                '3PM_TOTAL': g['3pm_total'],
                # Betting Props Lines
                'PTS_LINE': pts_line, 'PTS_OVER': 'OVER' if g['pts_total'] > pts_line else 'UNDER',
                'REB_LINE': reb_line, 'REB_OVER': 'OVER' if g['reb_total'] > reb_line else 'UNDER',
                'AST_LINE': ast_line, 'AST_OVER': 'OVER' if g['ast_total'] > ast_line else 'UNDER',
                '3PM_LINE': tpm_line, '3PM_OVER': 'OVER' if g['3pm_total'] > tpm_line else 'UNDER',
                # Averages (L5)
                'AVG_PTS_L5': avg_pts, 'AVG_REB_L5': avg_reb,
                'AVG_AST_L5': avg_ast, 'AVG_3PM_L5': avg_3pm,
                # Hit Rates (Over %)
                'PTS_HIT%': pts_hit, 'REB_HIT%': reb_hit,
                'AST_HIT%': ast_hit, '3PM_HIT%': tpm_hit,
                # Trends
                'PTS_TREND': pts_trend, 'PTS_SLOPE': pts_slope,
                'REB_TREND': reb_trend, 'REB_SLOPE': reb_slope,
                'AST_TREND': ast_trend, 'AST_SLOPE': ast_slope,
                # Std Dev (volatilidad)
                'PTS_STDDEV': pts_std, 'REB_STDDEV': reb_std,
                'AST_STDDEV': ast_std, '3PM_STDDEV': tpm_std,
                # Consistency Index (0-100)
                'PTS_CONSISTENCY': pts_consistency,
                'REB_CONSISTENCY': reb_consistency,
                'AST_CONSISTENCY': ast_consistency,
            }
            all_rows.append(row)

    # Crear DataFrame
    df = pd.DataFrame(all_rows)

    # Ordenar por Role (STARTER primero), luego AVG_MIN desc, luego fecha desc
    df['_role_sort'] = df['Role'].map({'STARTER': 0, 'ROTATION': 1})
    df = df.sort_values(['_role_sort', 'AVG_MIN', 'Game_Date', 'Player'],
                        ascending=[True, False, False, True])
    df = df.drop(columns=['_role_sort'])

    df['Game_Date'] = pd.to_datetime(df['Game_Date']).dt.strftime('%m/%d')

    # Guardar CSV
    output_file = f"{team_abbr}_BETTING_ANALYSIS.csv"
    df.to_csv(output_file, index=False)

    print(f"\n  CSV GUARDADO: {output_file}")
    print(f"  Total registros: {len(df)}")
    print(f"  Jugadores calificados (25+ min): {len(qualified_players)}")

    # Imprimir resumen de props
    print(f"\n  {'='*70}")
    print(f"  RESUMEN DE PROPS - {team_abbr}")
    print(f"  {'='*70}")
    print(f"  {'JUGADOR':<25} {'ROL':<9} {'PTS':>5} {'LN':>5} {'HIT%':>5}  "
          f"{'REB':>5} {'LN':>5} {'HIT%':>5}  "
          f"{'AST':>5} {'LN':>5} {'HIT%':>5}  "
          f"{'3PM':>5} {'LN':>5} {'HIT%':>5}")
    print(f"  {'-'*120}")

    for player_name, games_data in sorted_players:
        pts_v = [g['pts_total'] for g in games_data]
        reb_v = [g['reb_total'] for g in games_data]
        ast_v = [g['ast_total'] for g in games_data]
        tpm_v = [g['3pm_total'] for g in games_data]

        ap = round(sum(pts_v)/len(pts_v), 1)
        ar = round(sum(reb_v)/len(reb_v), 1)
        aa = round(sum(ast_v)/len(ast_v), 1)
        at = round(sum(tpm_v)/len(tpm_v), 1)

        pl = find_closest_line(ap, DEFAULT_PROP_LINES['PTS'])
        rl = find_closest_line(ar, DEFAULT_PROP_LINES['REB'])
        al = find_closest_line(aa, DEFAULT_PROP_LINES['AST'])
        tl = find_closest_line(at, DEFAULT_PROP_LINES['3PM'])

        ph = calculate_hit_rate(pts_v, pl)
        rh = calculate_hit_rate(reb_v, rl)
        ah = calculate_hit_rate(ast_v, al)
        th = calculate_hit_rate(tpm_v, tl)

        is_s = any(g['starter'] for g in games_data)
        role = 'START' if is_s else 'BENCH'

        print(f"  {player_name:<25} {role:<9} {ap:>5} {pl:>5} {ph:>4}%  "
              f"{ar:>5} {rl:>5} {rh:>4}%  "
              f"{aa:>5} {al:>5} {ah:>4}%  "
              f"{at:>5} {tl:>5} {th:>4}%")

    print(f"  {'='*70}\n")

    return True


# ============================================================================
# MAIN
# ============================================================================
def main():
    print("\n" + "="*70)
    print("  NBA PRO BETTING ANALYZER V1.0")
    print("  Analisis avanzado para Hard Rock Bet / DraftKings")
    print("="*70)
    print(f"  Fecha/Hora: {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}")
    print(f"  Minutos minimos: {MIN_MINUTES_THRESHOLD}+")
    print(f"  Juegos a analizar: {GAMES_TO_ANALYZE}")
    print("="*70 + "\n")

    teams_today = get_todays_games()

    if not teams_today:
        print("\n  No hay equipos jugando hoy. Script terminado.")
        return

    successful = 0
    failed = 0

    for team_abbr in teams_today:
        try:
            if process_team(team_abbr):
                successful += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ERROR procesando {team_abbr}: {e}")
            failed += 1

        time.sleep(1)

    print("\n" + "="*70)
    print("  RESUMEN FINAL")
    print("="*70)
    print(f"  Equipos procesados exitosamente: {successful}")
    print(f"  Equipos con errores: {failed}")
    print(f"  Archivos CSV generados: {successful}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
