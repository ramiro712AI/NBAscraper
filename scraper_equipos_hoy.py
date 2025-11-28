#!/usr/bin/env python3
"""
NBA SCRAPER - EQUIPOS ESPECÍFICOS DE HOY
Procesa SOLO los 6 equipos que juegan hoy:
CHI, CHA, ORL, DET, CLE, ATL
"""

import requests
import pandas as pd
from datetime import datetime
import time
import re
from collections import defaultdict

# Configuración
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# EQUIPOS QUE JUEGAN HOY (según odds.txt)
TEAMS_TODAY = ['CHI', 'CHA', 'ORL', 'DET', 'CLE', 'ATL']

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

def get_injury_report():
    """Obtiene el injury report actual"""
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        data = response.json()
        injuries = {}
        teams = data.get('injuries', [])
        for team in teams:
            team_injuries = team.get('injuries', [])
            for injury in team_injuries:
                athlete = injury.get('athlete', {})
                player_name = athlete.get('displayName', '')
                status = injury.get('status', 'Unknown')
                description = injury.get('description', '')
                if player_name:
                    injuries[player_name] = {
                        'status': status,
                        'description': description
                    }
        return injuries
    except Exception as e:
        print(f"  ⚠️  Error obteniendo injury report: {e}")
        return {}

def get_team_schedule(team_id, limit=5):
    """Obtiene los últimos N juegos del equipo"""
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/schedule"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        data = response.json()
        games = []
        events = data.get('events', [])
        completed_games = []
        for event in events:
            competition = event.get('competitions', [{}])[0]
            status = competition.get('status', {})
            if status.get('type', {}).get('completed', False):
                game_id = event.get('id')
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
                    'game_id': game_id,
                    'date': game_date_str,
                    'date_obj': date_obj,
                    'home_team': home_team,
                    'away_team': away_team
                })
        completed_games.sort(key=lambda x: x['date_obj'], reverse=True)
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
    """Extrae estadísticas TOTALES del Box Score"""
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
            player_index = 0
            for player in athletes:
                athlete_info = player.get('athlete', {})
                player_name = athlete_info.get('displayName', '')
                stats = player.get('stats', [])
                starter = player.get('starter', False)
                if not stats or not player_name:
                    continue
                stats_dict = {label: value for label, value in zip(labels, stats)}
                minutes = stats_dict.get('MIN', '0')
                if starter:
                    player_status = 'Starter'
                elif player_index < 5 and minutes != '0' and minutes != 0:
                    player_status = 'Starter'
                else:
                    player_status = 'Bench'
                pts = stats_dict.get('PTS', '0')
                reb = stats_dict.get('REB', '0')
                ast = stats_dict.get('AST', '0')
                three_pt_raw = stats_dict.get('3PT', '0-0')
                three_pt = three_pt_raw.split('-')[0] if '-' in str(three_pt_raw) else '0'
                players_stats[player_name] = {
                    'PTS_TOTAL': int(pts) if str(pts).isdigit() else 0,
                    'REB_TOTAL': int(reb) if str(reb).isdigit() else 0,
                    'AST_TOTAL': int(ast) if str(ast).isdigit() else 0,
                    '3PM_TOTAL': int(three_pt) if str(three_pt).isdigit() else 0,
                    'player_status': player_status,
                    'minutes': minutes
                }
                if minutes != '0' and minutes != 0:
                    player_index += 1
        return players_stats
    except Exception as e:
        print(f"  ❌ Error obteniendo estadísticas totales: {e}")
        return {}

def get_quarter_stats_from_playbyplay(game_id, team_id):
    """Extrae estadísticas por QUARTER desde el play-by-play"""
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={game_id}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
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
                    athlete_info = player.get('athlete', {})
                    player_name = athlete_info.get('displayName', '')
                    if player_name:
                        team_players.add(player_name)
        plays = data.get('plays', [])
        quarter_stats = defaultdict(lambda: {
            'PTS_Q1': 0, 'REB_Q1': 0, 'AST_Q1': 0, '3PM_Q1': 0,
            'PTS_Q2': 0, 'REB_Q2': 0, 'AST_Q2': 0, '3PM_Q2': 0,
            'PTS_Q3': 0, 'REB_Q3': 0, 'AST_Q3': 0, '3PM_Q3': 0,
            'PTS_Q4': 0, 'REB_Q4': 0, 'AST_Q4': 0, '3PM_Q4': 0
        })
        for play in plays:
            period = play.get('period', {}).get('number', 0)
            if period not in [1, 2, 3, 4]:
                continue
            quarter_suffix = f"_Q{period}"
            text = play.get('text', '')
            scoring_play = play.get('scoringPlay', False)
            if scoring_play:
                makes_patterns = [
                    r'([A-Za-z\'\.\s]+?)\s+makes',
                    r'([A-Za-z\'\.\s]+?)\s+made'
                ]
                player = None
                for pattern in makes_patterns:
                    match = re.search(pattern, text)
                    if match:
                        player = match.group(1).strip()
                        break
                if player and player in team_players:
                    is_three = 'three point' in text.lower() or '3-point' in text.lower() or 'three pointer' in text.lower()
                    if is_three:
                        quarter_stats[player][f'PTS{quarter_suffix}'] += 3
                        quarter_stats[player][f'3PM{quarter_suffix}'] += 1
                    elif 'free throw' in text.lower():
                        quarter_stats[player][f'PTS{quarter_suffix}'] += 1
                    else:
                        quarter_stats[player][f'PTS{quarter_suffix}'] += 2
            if 'rebound' in text.lower():
                rebound_patterns = [
                    r'([A-Za-z\'\.\s]+?)\s+(defensive|offensive)\s+rebound',
                    r'([A-Za-z\'\.\s]+?)\s+rebound'
                ]
                for pattern in rebound_patterns:
                    match = re.search(pattern, text)
                    if match:
                        player = match.group(1).strip()
                        if player in team_players:
                            quarter_stats[player][f'REB{quarter_suffix}'] += 1
                            break
            if 'assist' in text.lower():
                assist_patterns = [
                    r'\(([A-Za-z\'\.\s]+?)\s+assists\)',
                    r'([A-Za-z\'\.\s]+?)\s+assists'
                ]
                for pattern in assist_patterns:
                    match = re.search(pattern, text)
                    if match:
                        player = match.group(1).strip()
                        if player in team_players:
                            quarter_stats[player][f'AST{quarter_suffix}'] += 1
                            break
        return dict(quarter_stats)
    except Exception as e:
        print(f"  ❌ Error obteniendo estadísticas por quarter: {e}")
        return {}

def process_team(team_abbr, injury_report):
    """Procesa un equipo específico y genera su CSV"""
    team_id, team_name = TEAM_ABBREVIATIONS[team_abbr]
    print(f"\n{'='*60}")
    print(f"PROCESANDO: {team_abbr} ({team_name.upper()})")
    print(f"{'='*60}")
    games = get_team_schedule(team_id, limit=5)
    if not games:
        print(f"❌ No se encontraron juegos completados para {team_abbr}")
        return False
    print(f"✅ Se encontraron {len(games)} juegos\n")
    all_data = []
    for idx, game in enumerate(games, 1):
        game_id = game['game_id']
        game_date = game['date']
        matchup = f"{game['away_team']} @ {game['home_team']}"
        print(f"  JUEGO {idx}/{len(games)}: {matchup} ({game_date})")
        totals = get_boxscore_totals(game_id, team_id)
        quarter_stats = get_quarter_stats_from_playbyplay(game_id, team_id)
        print(f"    ✅ {len(totals)} jugadores procesados")
        for player_name in totals:
            player_quarter_data = quarter_stats.get(player_name, {})
            injury_info = injury_report.get(player_name, {})
            injury_status = injury_info.get('status', 'Healthy')
            player_data = {
                'Game_Date': game_date,
                'Opponent': game['away_team'] if team_name.upper() in game['home_team'].upper() else game['home_team'],
                'Player': player_name,
                'Player_Status': totals[player_name].get('player_status', 'Bench'),
                'Injury_Status': injury_status,
                'PTS_Q1': player_quarter_data.get('PTS_Q1', 0),
                'REB_Q1': player_quarter_data.get('REB_Q1', 0),
                'AST_Q1': player_quarter_data.get('AST_Q1', 0),
                '3PM_Q1': player_quarter_data.get('3PM_Q1', 0),
                'PTS_Q2': player_quarter_data.get('PTS_Q2', 0),
                'REB_Q2': player_quarter_data.get('REB_Q2', 0),
                'AST_Q2': player_quarter_data.get('AST_Q2', 0),
                '3PM_Q2': player_quarter_data.get('3PM_Q2', 0),
                'PTS_Q3': player_quarter_data.get('PTS_Q3', 0),
                'REB_Q3': player_quarter_data.get('REB_Q3', 0),
                'AST_Q3': player_quarter_data.get('AST_Q3', 0),
                '3PM_Q3': player_quarter_data.get('3PM_Q3', 0),
                'PTS_Q4': player_quarter_data.get('PTS_Q4', 0),
                'REB_Q4': player_quarter_data.get('REB_Q4', 0),
                'AST_Q4': player_quarter_data.get('AST_Q4', 0),
                '3PM_Q4': player_quarter_data.get('3PM_Q4', 0),
                'PTS_TOTAL': totals[player_name]['PTS_TOTAL'],
                'REB_TOTAL': totals[player_name]['REB_TOTAL'],
                'AST_TOTAL': totals[player_name]['AST_TOTAL'],
                '3PM_TOTAL': totals[player_name]['3PM_TOTAL']
            }
            all_data.append(player_data)
        time.sleep(0.5)
    df = pd.DataFrame(all_data)
    df['_status_order'] = df['Player_Status'].apply(lambda x: 0 if x == 'Starter' else 1)
    df = df.sort_values(['_status_order', 'Game_Date', 'Player'], ascending=[True, False, True])
    df = df.drop(columns=['_status_order'])
    df['Game_Date'] = pd.to_datetime(df['Game_Date']).dt.strftime('%m/%d')
    output_file = f"{team_abbr}_last_5_games.csv"
    df.to_csv(output_file, index=False)
    print(f"\n✅ CSV GUARDADO: {output_file}")
    print(f"📊 Total registros: {len(df)}")
    unique_players = df['Player'].unique()
    starters = df[df['Player_Status'] == 'Starter']['Player'].unique()
    injured = df[df['Injury_Status'] != 'Healthy']['Player'].unique()
    print(f"👥 Jugadores: {len(unique_players)} | 🏀 Titulares: {len(starters)} | 🚑 Lesionados: {len(injured)}\n")
    return True

def main():
    print("\n" + "="*60)
    print("NBA SCRAPER - EQUIPOS DE HOY")
    print("="*60)
    print(f"Fecha/Hora: {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}")
    print(f"Equipos a procesar: {', '.join(TEAMS_TODAY)}")
    print("="*60 + "\n")

    print("🚑 Obteniendo injury report...")
    injury_report = get_injury_report()
    print(f"✅ Injury report: {len(injury_report)} jugadores con lesiones\n")

    successful = 0
    failed = 0
    for team_abbr in TEAMS_TODAY:
        try:
            if process_team(team_abbr, injury_report):
                successful += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Error procesando {team_abbr}: {e}")
            failed += 1
        time.sleep(1)

    print("\n" + "="*60)
    print("RESUMEN FINAL")
    print("="*60)
    print(f"✅ Equipos procesados: {successful}")
    print(f"❌ Equipos con errores: {failed}")
    print(f"📁 Archivos CSV generados: {successful}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
