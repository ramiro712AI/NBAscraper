#!/usr/bin/env python3
"""
NBA SCRAPER AUTOMÁTICO
Detecta qué equipos juegan HOY y genera archivos Excel (.xlsx) con sus últimos 5 juegos
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import re
from collections import defaultdict
import os
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows

# Configuración
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# Paleta de colores vibrantes (15 colores fuertes y distinguibles)
VIBRANT_COLORS = [
    '4A90E2',  # Azul fuerte
    '50C878',  # Verde fuerte
    'FF8C42',  # Naranja fuerte
    '9B59B6',  # Púrpura fuerte
    'F4D03F',  # Amarillo fuerte
    'FF69B4',  # Rosa fuerte
    '48D1CC',  # Turquesa fuerte
    'FF7F50',  # Coral fuerte
    '32CD32',  # Lima fuerte
    '8A2BE2',  # Violeta fuerte
    'FA8072',  # Salmón fuerte
    'FFD700',  # Dorado fuerte
    '00CED1',  # Cian fuerte
    'FF00FF',  # Magenta fuerte
    '3EB489',  # Menta fuerte
]

def generate_color_palette(num_colors):
    """
    Genera una paleta de colores expandida si hay más de 15 jugadores únicos.
    Reutiliza los colores base con ligeras variaciones.
    """
    colors = []
    base_colors_count = len(VIBRANT_COLORS)

    for i in range(num_colors):
        base_idx = i % base_colors_count
        base_color = VIBRANT_COLORS[base_idx]

        # Si necesitamos más de 15 colores, agregamos variaciones
        if i >= base_colors_count:
            # Cada "ciclo" de 15 colores usa una variación diferente
            cycle = i // base_colors_count
            # Ajustar brillo alternando entre más claro y más oscuro
            if cycle % 2 == 1:
                # Hacer más claro (agregar brillo)
                r, g, b = int(base_color[0:2], 16), int(base_color[2:4], 16), int(base_color[4:6], 16)
                r = min(255, r + 30)
                g = min(255, g + 30)
                b = min(255, b + 30)
                base_color = f'{r:02X}{g:02X}{b:02X}'
            else:
                # Hacer más oscuro (reducir brillo)
                r, g, b = int(base_color[0:2], 16), int(base_color[2:4], 16), int(base_color[4:6], 16)
                r = max(0, r - 30)
                g = max(0, g - 30)
                b = max(0, b - 30)
                base_color = f'{r:02X}{g:02X}{b:02X}'

        colors.append(base_color)

    return colors

# Diccionario de abreviaciones a IDs
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

def get_todays_games():
    """
    Obtiene los equipos que juegan HOY
    """
    today = datetime.now().strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={today}"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        data = response.json()
        
        teams_playing = []
        events = data.get('events', [])
        
        if not events:
            print(f"ℹ️  No hay juegos programados para HOY ({datetime.now().strftime('%Y-%m-%d')})")
            return []
        
        print(f"\n{'='*60}")
        print(f"JUEGOS DE HOY: {datetime.now().strftime('%A, %B %d, %Y')}")
        print(f"{'='*60}\n")
        
        for idx, event in enumerate(events, 1):
            competition = event.get('competitions', [{}])[0]
            competitors = competition.get('competitors', [])
            
            game_time = event.get('date', '')
            status = competition.get('status', {}).get('type', {}).get('name', '')
            
            for comp in competitors:
                team_abbr = comp.get('team', {}).get('abbreviation', '')
                team_name = comp.get('team', {}).get('displayName', '')
                
                if team_abbr and team_abbr in TEAM_ABBREVIATIONS:
                    teams_playing.append(team_abbr)
            
            # Mostrar info del juego
            if len(competitors) >= 2:
                away = competitors[0].get('team', {}).get('abbreviation', '')
                home = competitors[1].get('team', {}).get('abbreviation', '')
                
                try:
                    dt = datetime.strptime(game_time, '%Y-%m-%dT%H:%MZ')
                    time_str = dt.strftime('%I:%M %p')
                except:
                    time_str = 'TBD'
                
                print(f"{idx}. {away} @ {home} - {time_str} ({status})")
        
        print(f"\n{'='*60}")
        print(f"✅ Total de equipos jugando HOY: {len(teams_playing)}")
        print(f"{'='*60}\n")
        
        return teams_playing
        
    except Exception as e:
        print(f"❌ Error obteniendo juegos de hoy: {e}")
        return []

def get_team_schedule(team_id, limit=5):
    """
    Obtiene los últimos N juegos del equipo (más recientes primero)
    """
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/schedule"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        data = response.json()
        
        games = []
        events = data.get('events', [])
        
        # Filtrar solo juegos completados y agregar fecha como objeto datetime para ordenar
        completed_games = []
        for event in events:
            competition = event.get('competitions', [{}])[0]
            status = competition.get('status', {})
            
            # Solo juegos terminados
            if status.get('type', {}).get('completed', False):
                game_id = event.get('id')
                game_date = event.get('date', '')
                
                # Formatear fecha
                date_obj = None
                if game_date:
                    try:
                        date_obj = datetime.strptime(game_date, '%Y-%m-%dT%H:%MZ')
                        game_date_str = date_obj.strftime('%Y-%m-%d')
                    except:
                        continue
                
                # Obtener nombres de equipos
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
        
        # Ordenar por fecha (más reciente primero)
        completed_games.sort(key=lambda x: x['date_obj'], reverse=True)
        
        # Tomar solo los N más recientes
        for game in completed_games[:limit]:
            games.append({
                'game_id': game['game_id'],
                'date': game['date'],
                'home_team': game['home_team'],
                'away_team': game['away_team']
            })
        
        return games
        
    except Exception as e:
        print(f"  ❌ Error obteniendo calendario: {e}")
        return []

def get_boxscore_totals(game_id, team_id):
    """
    Extrae las estadísticas TOTALES del Box Score para cada jugador del equipo
    """
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={game_id}"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
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
                minutes = stats_dict.get('MIN', '0')

                if minutes == '0' or minutes == 0:
                    continue
                
                pts = stats_dict.get('PTS', '0')
                reb = stats_dict.get('REB', '0')
                ast = stats_dict.get('AST', '0')
                three_pt_raw = stats_dict.get('3PT', '0-0')
                
                three_pt = three_pt_raw.split('-')[0] if '-' in str(three_pt_raw) else '0'
                
                players_stats[player_name] = {
                    'PTS_TOTAL': int(pts) if str(pts).isdigit() else 0,
                    'REB_TOTAL': int(reb) if str(reb).isdigit() else 0,
                    'AST_TOTAL': int(ast) if str(ast).isdigit() else 0,
                    '3PM_TOTAL': int(three_pt) if str(three_pt).isdigit() else 0
                }
        
        return players_stats
        
    except Exception as e:
        print(f"  ❌ Error obteniendo estadísticas totales: {e}")
        return {}

def get_q1_stats_from_playbyplay(game_id, team_id):
    """
    Extrae estadísticas del Q1 desde el play-by-play
    """
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={game_id}"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        # Primero, obtener la lista de jugadores del equipo desde el boxscore
        team_players = set()
        boxscore = data.get('boxscore', {})
        players_data = boxscore.get('players', [])
        
        for team_data in players_data:
            current_team_id = team_data.get('team', {}).get('id')
            if str(current_team_id) != str(team_id):
                continue
                
            statistics = team_data.get('statistics', [])
            if statistics:
                athletes = statistics[0].get('athletes', [])
                for player in athletes:
                    if player.get('active', False):
                        athlete_info = player.get('athlete', {})
                        player_name = athlete_info.get('displayName', '')
                        if player_name:
                            team_players.add(player_name)
        
        # Ahora extraer stats del Q1 desde play-by-play
        plays = data.get('plays', [])
        
        q1_stats = defaultdict(lambda: {
            'PTS_Q1': 0,
            'REB_Q1': 0,
            'AST_Q1': 0,
            '3PM_Q1': 0
        })
        
        for play in plays:
            period = play.get('period', {}).get('number', 0)
            
            if period != 1:
                continue
            
            text = play.get('text', '')
            scoring_play = play.get('scoringPlay', False)
            
            # PUNTOS
            if scoring_play:
                makes_pattern = r'([A-Za-z\'\.\s]+?)\s+makes\s+'
                match = re.search(makes_pattern, text)
                
                if match:
                    player = match.group(1).strip()
                    
                    if player not in team_players:
                        continue
                    
                    is_three = 'three point' in text.lower() or '3-point' in text.lower()
                    
                    if is_three:
                        q1_stats[player]['PTS_Q1'] += 3
                        q1_stats[player]['3PM_Q1'] += 1
                    elif 'free throw' in text.lower():
                        q1_stats[player]['PTS_Q1'] += 1
                    else:
                        q1_stats[player]['PTS_Q1'] += 2
            
            # REBOTES
            if 'rebound' in text.lower():
                rebound_pattern = r'([A-Za-z\'\.\s]+?)\s+(defensive|offensive)\s+rebound'
                match = re.search(rebound_pattern, text)
                
                if match:
                    player = match.group(1).strip()
                    if player in team_players:
                        q1_stats[player]['REB_Q1'] += 1
            
            # ASISTENCIAS
            if 'assists)' in text:
                assist_pattern = r'\(([A-Za-z\'\.\s]+?)\s+assists\)'
                match = re.search(assist_pattern, text)
                
                if match:
                    player = match.group(1).strip()
                    if player in team_players:
                        q1_stats[player]['AST_Q1'] += 1
        
        return dict(q1_stats)
        
    except Exception as e:
        print(f"  ❌ Error obteniendo estadísticas de Q1: {e}")
        return {}

def collect_team_players(team_id, limit=5):
    """
    Recopila todos los nombres únicos de jugadores de los últimos N juegos de un equipo.
    Función ligera para la primera pasada de recopilación de jugadores.
    """
    players = set()

    try:
        games = get_team_schedule(team_id, limit=limit)

        for game in games:
            game_id = game['game_id']

            try:
                url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={game_id}"
                response = requests.get(url, timeout=10)
                data = response.json()

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
                        minutes = stats_dict.get('MIN', '0')

                        if minutes == '0' or minutes == 0:
                            continue

                        players.add(player_name)

                time.sleep(0.3)  # Pequeña pausa entre requests

            except Exception:
                continue

    except Exception:
        pass

    return players

def save_to_excel_with_colors(df, output_file, player_color_map):
    """
    Guarda el DataFrame en Excel con colores por jugador usando el mapeo global
    """
    # Crear workbook
    wb = Workbook()
    ws = wb.active

    # Insertar columna de Team_Name al inicio
    team_name = output_file.split('_')[0]  # Extrae "BOS" de "BOS_last_5_games.xlsx"
    df.insert(0, 'Team_Name', team_name)

    # Escribir headers
    for col_num, column_title in enumerate(df.columns, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = column_title
        # Estilo del header: gris oscuro con texto blanco en negrita
        cell.fill = PatternFill(start_color='404040', end_color='404040', fill_type='solid')
        cell.font = Font(bold=True, color='FFFFFF')
        cell.alignment = Alignment(horizontal='center', vertical='center')

    # Escribir datos con colores por jugador usando el mapeo global
    for row_num, row_data in enumerate(df.values, 2):
        player_name = row_data[3]  # Player está en la columna 4 (índice 3 después de insertar Team_Name)
        # Usar el mapeo global de colores
        player_color = player_color_map.get(player_name, 'FFFFFF')

        for col_num, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_num, column=col_num)
            cell.value = value
            # Aplicar color de fondo del jugador
            cell.fill = PatternFill(start_color=player_color, end_color=player_color, fill_type='solid')
            cell.alignment = Alignment(horizontal='center', vertical='center')

    # Ajustar ancho de columnas
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 20)
        ws.column_dimensions[column_letter].width = adjusted_width

    # Guardar archivo
    wb.save(output_file)

def process_team(team_abbr, player_color_map):
    """
    Procesa un equipo específico y genera su archivo Excel con colores por jugador
    usando el mapeo global de colores
    """
    team_id, team_name = TEAM_ABBREVIATIONS[team_abbr]
    
    print(f"\n{'='*60}")
    print(f"PROCESANDO: {team_abbr} ({team_name.upper()})")
    print(f"{'='*60}")
    
    # Obtener últimos 5 juegos
    games = get_team_schedule(team_id, limit=5)
    
    if not games:
        print(f"❌ No se encontraron juegos completados para {team_abbr}")
        return False
    
    print(f"✅ Se encontraron {len(games)} juegos\n")
    
    # Procesar cada juego
    all_data = []
    
    for idx, game in enumerate(games, 1):
        game_id = game['game_id']
        game_date = game['date']
        matchup = f"{game['away_team']} @ {game['home_team']}"
        
        print(f"  JUEGO {idx}/{len(games)}: {matchup} ({game_date})")
        
        totals = get_boxscore_totals(game_id, team_id)
        q1_stats = get_q1_stats_from_playbyplay(game_id, team_id)
        
        print(f"    ✅ {len(totals)} jugadores procesados")
        
        for player_name in totals:
            player_data = {
                'Game_Date': game_date,
                'Opponent': game['away_team'] if team_name.upper() in game['home_team'].upper() else game['home_team'],
                'Player': player_name,
                'PTS_Q1': q1_stats.get(player_name, {}).get('PTS_Q1', 0),
                'REB_Q1': q1_stats.get(player_name, {}).get('REB_Q1', 0),
                'AST_Q1': q1_stats.get(player_name, {}).get('AST_Q1', 0),
                '3PM_Q1': q1_stats.get(player_name, {}).get('3PM_Q1', 0),
                'PTS_TOTAL': totals[player_name]['PTS_TOTAL'],
                'REB_TOTAL': totals[player_name]['REB_TOTAL'],
                'AST_TOTAL': totals[player_name]['AST_TOTAL'],
                '3PM_TOTAL': totals[player_name]['3PM_TOTAL']
            }
            all_data.append(player_data)
        
        time.sleep(0.5)
    
    # Crear DataFrame
    df = pd.DataFrame(all_data)
    df = df.sort_values(['Game_Date', 'Player'], ascending=[False, True])
    df['Game_Date'] = pd.to_datetime(df['Game_Date']).dt.strftime('%m/%d')

    # Guardar Excel con colores usando el mapeo global
    output_file = f"{team_abbr}_last_5_games.xlsx"
    save_to_excel_with_colors(df.copy(), output_file, player_color_map)

    print(f"\n✅ EXCEL GUARDADO: {output_file}")
    print(f"📊 Total registros: {len(df)}")
    print(f"🎨 Colores consistentes aplicados por jugador\n")

    return True

def main():
    """
    Función principal
    """
    print("\n" + "="*60)
    print("NBA SCRAPER AUTOMÁTICO")
    print("="*60)
    print(f"Fecha/Hora: {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}")
    print("="*60 + "\n")
    
    # Obtener equipos que juegan HOY
    teams_today = get_todays_games()

    if not teams_today:
        print("\n⚠️  No hay equipos jugando hoy. Script terminado.")
        return

    # PRIMERA PASADA: Recopilar todos los jugadores únicos de todos los equipos
    print(f"\n{'='*60}")
    print("FASE 1: RECOPILANDO JUGADORES ÚNICOS")
    print(f"{'='*60}\n")

    all_unique_players = set()

    for idx, team_abbr in enumerate(teams_today, 1):
        team_id, team_name = TEAM_ABBREVIATIONS[team_abbr]
        print(f"  [{idx}/{len(teams_today)}] Recopilando jugadores de {team_abbr}...")

        try:
            team_players = collect_team_players(team_id, limit=5)
            all_unique_players.update(team_players)
            print(f"      ✅ {len(team_players)} jugadores encontrados")
        except Exception as e:
            print(f"      ⚠️  Error: {e}")

        time.sleep(0.5)

    print(f"\n{'='*60}")
    print(f"✅ TOTAL DE JUGADORES ÚNICOS: {len(all_unique_players)}")
    print(f"{'='*60}\n")

    # Crear mapeo global de jugador a color
    sorted_players = sorted(list(all_unique_players))  # Ordenar para consistencia
    color_palette = generate_color_palette(len(sorted_players))

    player_color_map = {}
    for idx, player in enumerate(sorted_players):
        player_color_map[player] = color_palette[idx]

    print(f"🎨 Paleta de colores creada: {len(color_palette)} colores asignados\n")

    # SEGUNDA PASADA: Procesar cada equipo con el mapeo global de colores
    print(f"\n{'='*60}")
    print("FASE 2: GENERANDO ARCHIVOS EXCEL")
    print(f"{'='*60}")

    successful = 0
    failed = 0

    for team_abbr in teams_today:
        try:
            if process_team(team_abbr, player_color_map):
                successful += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Error procesando {team_abbr}: {e}")
            failed += 1

        time.sleep(1)
    
    # Resumen final
    print("\n" + "="*60)
    print("RESUMEN FINAL")
    print("="*60)
    print(f"✅ Equipos procesados exitosamente: {successful}")
    print(f"❌ Equipos con errores: {failed}")
    print(f"📁 Archivos Excel (.xlsx) generados: {successful}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
