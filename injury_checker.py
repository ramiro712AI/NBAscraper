#!/usr/bin/env python3
"""
INJURY REPORT CHECKER
Verifica el estado de lesiones de jugadores antes de generar parlays
Integración con ESPN API y otras fuentes de injury reports
"""

import requests
from datetime import datetime
from typing import List, Dict, Set
import time

# Configuración
ESPN_INJURY_API = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/injuries"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# Mapeo de equipos NBA
TEAM_IDS = {
    'ATL': '1', 'BOS': '2', 'NOP': '3', 'CHI': '4', 'CLE': '5', 'DAL': '6',
    'DEN': '7', 'DET': '8', 'GSW': '9', 'HOU': '10', 'IND': '11', 'LAC': '12',
    'LAL': '13', 'MIA': '14', 'MIL': '15', 'MIN': '16', 'BKN': '17', 'NYK': '18',
    'ORL': '19', 'PHI': '20', 'PHX': '21', 'POR': '22', 'SAC': '23', 'SAS': '24',
    'OKC': '25', 'UTA': '26', 'WAS': '27', 'TOR': '28', 'MEM': '29', 'CHA': '30'
}


class InjuryChecker:
    """Verificador de lesiones en tiempo real"""

    def __init__(self):
        """Inicializa el checker"""
        self.injured_players = set()
        self.questionable_players = set()
        self.out_players = set()
        self.last_update = None

    def fetch_team_injuries(self, team_abbr: str) -> List[Dict]:
        """
        Obtiene injuries de un equipo específico

        Args:
            team_abbr: Abreviación del equipo (ej: 'LAL')

        Returns:
            Lista de jugadores lesionados
        """
        team_id = TEAM_IDS.get(team_abbr)
        if not team_id:
            return []

        url = ESPN_INJURY_API.format(team_id=team_id)

        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            data = response.json()

            injuries = []
            for athlete in data.get('athletes', []):
                injury_data = athlete.get('injuries', [])
                if injury_data:
                    for injury in injury_data:
                        injuries.append({
                            'player': athlete.get('displayName', ''),
                            'team': team_abbr,
                            'status': injury.get('status', 'Unknown'),
                            'type': injury.get('type', {}).get('abbreviation', ''),
                            'details': injury.get('details', {}).get('detail', '')
                        })

            return injuries

        except Exception as e:
            print(f"⚠️  Error obteniendo injuries de {team_abbr}: {e}")
            return []

    def fetch_all_injuries(self) -> Dict[str, List[Dict]]:
        """
        Obtiene injuries de todos los equipos NBA

        Returns:
            Dict con injuries por equipo
        """
        print(f"\n🏥 Consultando injury reports de todos los equipos NBA...")
        print(f"{'─'*70}\n")

        all_injuries = {}

        for team_abbr in TEAM_IDS.keys():
            injuries = self.fetch_team_injuries(team_abbr)
            if injuries:
                all_injuries[team_abbr] = injuries
                time.sleep(0.2)  # Rate limiting

        self.last_update = datetime.now()
        return all_injuries

    def is_player_available(self, player_name: str, team_abbr: str) -> tuple:
        """
        Verifica si un jugador está disponible para jugar

        Args:
            player_name: Nombre del jugador
            team_abbr: Abreviación del equipo

        Returns:
            (is_available, status, details)
        """
        injuries = self.fetch_team_injuries(team_abbr)

        for injury in injuries:
            if player_name.lower() in injury['player'].lower():
                status = injury['status'].upper()

                # Categorizar por status
                if status in ['OUT', 'INACTIVE']:
                    return False, 'OUT', injury['details']
                elif status in ['DOUBTFUL']:
                    return False, 'DOUBTFUL', injury['details']
                elif status in ['QUESTIONABLE', 'DAY_TO_DAY']:
                    return True, 'QUESTIONABLE', injury['details']  # Puede jugar
                elif status in ['PROBABLE']:
                    return True, 'PROBABLE', injury['details']

        return True, 'ACTIVE', 'No injury report'

    def filter_available_players(self, player_list: List[Dict]) -> List[Dict]:
        """
        Filtra jugadores disponibles de una lista

        Args:
            player_list: Lista de jugadores con 'player' y 'team'

        Returns:
            Lista filtrada con solo jugadores disponibles
        """
        print(f"\n🔍 Verificando disponibilidad de {len(player_list)} jugadores...")
        print(f"{'─'*70}\n")

        available = []
        excluded = []

        for player_data in player_list:
            player = player_data['player']
            team = player_data['team']

            is_available, status, details = self.is_player_available(player, team)

            if is_available:
                if status == 'QUESTIONABLE':
                    print(f"⚠️  {player} ({team}): {status} - {details}")
                    print(f"   💡 Incluido pero verifica 1h antes del juego")
                else:
                    print(f"✅ {player} ({team}): {status}")
                available.append(player_data)
            else:
                print(f"❌ {player} ({team}): {status} - {details}")
                print(f"   🚫 EXCLUIDO de los parlays")
                excluded.append({
                    'player': player,
                    'team': team,
                    'status': status,
                    'details': details
                })

            time.sleep(0.3)  # Rate limiting

        print(f"\n{'─'*70}")
        print(f"✅ Jugadores disponibles: {len(available)}")
        print(f"❌ Jugadores excluidos: {len(excluded)}")
        print(f"{'─'*70}\n")

        return available, excluded

    def generate_injury_report(self) -> str:
        """
        Genera reporte completo de lesiones

        Returns:
            String con reporte formateado
        """
        print(f"\n📋 Generando injury report completo...\n")

        all_injuries = self.fetch_all_injuries()

        if not all_injuries:
            return "✅ No hay injuries reportados en la NBA actualmente."

        report = []
        report.append(f"\n{'='*70}")
        report.append(f"🏥 NBA INJURY REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append(f"{'='*70}\n")

        total_injuries = 0

        for team, injuries in sorted(all_injuries.items()):
            report.append(f"{'─'*70}")
            report.append(f"🏀 {team}")
            report.append(f"{'─'*70}")

            for injury in injuries:
                total_injuries += 1
                status = injury['status'].upper()
                emoji = '❌' if status in ['OUT', 'INACTIVE'] else '⚠️'

                report.append(f"{emoji} {injury['player']}")
                report.append(f"   Status: {status}")
                report.append(f"   Details: {injury['details']}")
                report.append("")

        report.append(f"{'='*70}")
        report.append(f"📊 Total: {total_injuries} jugadores con injuries en {len(all_injuries)} equipos")
        report.append(f"{'='*70}\n")

        return '\n'.join(report)


def check_specific_players(players: List[tuple]) -> Dict:
    """
    Verifica lista específica de jugadores

    Args:
        players: Lista de tuplas (nombre, equipo)

    Returns:
        Dict con resultados
    """
    checker = InjuryChecker()

    print(f"\n{'='*70}")
    print(f"🔍 VERIFICACIÓN RÁPIDA DE JUGADORES")
    print(f"{'='*70}\n")

    results = {
        'available': [],
        'questionable': [],
        'out': []
    }

    for player_name, team_abbr in players:
        is_available, status, details = checker.is_player_available(player_name, team_abbr)

        result = {
            'player': player_name,
            'team': team_abbr,
            'status': status,
            'details': details,
            'available': is_available
        }

        if status in ['OUT', 'DOUBTFUL']:
            results['out'].append(result)
            print(f"❌ {player_name} ({team_abbr}): {status}")
        elif status in ['QUESTIONABLE', 'PROBABLE']:
            results['questionable'].append(result)
            print(f"⚠️  {player_name} ({team_abbr}): {status}")
        else:
            results['available'].append(result)
            print(f"✅ {player_name} ({team_abbr}): {status}")

        time.sleep(0.3)

    print(f"\n{'─'*70}")
    print(f"✅ Disponibles: {len(results['available'])}")
    print(f"⚠️  Cuestionables: {len(results['questionable'])}")
    print(f"❌ OUT: {len(results['out'])}")
    print(f"{'─'*70}\n")

    return results


def main():
    """Función principal para testing"""
    print(f"\n{'='*70}")
    print(f"🏥 INJURY CHECKER - NBA")
    print(f"{'='*70}\n")

    # Jugadores clave para verificar
    key_players = [
        ('Nikola Jokic', 'DEN'),
        ('Luka Doncic', 'DAL'),
        ('Giannis Antetokounmpo', 'MIL'),
        ('Anthony Davis', 'LAL'),
        ('Jayson Tatum', 'BOS'),
        ('Tyrese Haliburton', 'IND'),
        ('Joel Embiid', 'PHI'),
        ('Shai Gilgeous-Alexander', 'OKC'),
        ('Stephen Curry', 'GSW'),
        ('Domantas Sabonis', 'SAC'),
    ]

    # Verificar jugadores
    results = check_specific_players(key_players)

    # Guardar reporte
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'injury_report_{timestamp}.txt'

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"NBA INJURY REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"{'='*70}\n\n")

        f.write(f"✅ DISPONIBLES ({len(results['available'])}):\n")
        for r in results['available']:
            f.write(f"   {r['player']} ({r['team']})\n")

        f.write(f"\n⚠️  CUESTIONABLES ({len(results['questionable'])}):\n")
        for r in results['questionable']:
            f.write(f"   {r['player']} ({r['team']}) - {r['details']}\n")

        f.write(f"\n❌ OUT ({len(results['out'])}):\n")
        for r in results['out']:
            f.write(f"   {r['player']} ({r['team']}) - {r['details']}\n")

    print(f"✅ Reporte guardado en: {output_file}\n")


if __name__ == '__main__':
    main()
