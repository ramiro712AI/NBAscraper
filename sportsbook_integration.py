#!/usr/bin/env python3
"""
SPORTSBOOK INTEGRATION MODULE
Integración con casas de apuestas y APIs de odds para comparar
líneas del mercado con recomendaciones del modelo.
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import time

# Configuración
CONFIG_FILE = 'sportsbook_config.json'


class SportsbookAPI:
    """Cliente para APIs de casas de apuestas"""

    def __init__(self, config_file: str = CONFIG_FILE):
        """
        Inicializa el cliente

        Args:
            config_file: Ruta al archivo de configuración
        """
        with open(config_file, 'r') as f:
            self.config = json.load(f)

        self.default_book = self.config.get('default_sportsbook', 'odds_api')
        self.mock_mode = self.config.get('mock_data', {}).get('enabled', True)

    def get_player_props(self, player_name: str, market: str = 'player_points') -> Optional[Dict]:
        """
        Obtiene props de un jugador de las casas de apuestas

        Args:
            player_name: Nombre del jugador
            market: Tipo de mercado ('player_points', 'player_rebounds', 'player_assists')

        Returns:
            Dict con odds de diferentes sportsbooks o None
        """
        if self.mock_mode:
            return self._get_mock_odds(player_name, market)

        # Implementación real con The Odds API
        book_config = self.config['sportsbooks'].get(self.default_book, {})
        api_key = book_config.get('api_key', '')

        if api_key == 'YOUR_API_KEY_HERE' or not api_key:
            print(f"⚠️  No hay API key configurada para {book_config.get('name', 'unknown')}")
            print(f"💡 Usando datos mock. Para usar API real:")
            print(f"   1. Registrate en https://the-odds-api.com/")
            print(f"   2. Obtén tu API key (500 requests gratis/mes)")
            print(f"   3. Actualiza 'sportsbook_config.json' con tu API key\n")
            return self._get_mock_odds(player_name, market)

        # Llamada real a la API
        try:
            base_url = book_config.get('api_url', '')
            sport = book_config.get('sports', {}).get('nba', 'basketball_nba')

            url = f"{base_url}sports/{sport}/events"
            params = {
                'apiKey': api_key,
                'regions': 'us',
                'markets': market
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                # Procesar y filtrar por jugador
                return self._parse_odds_response(data, player_name, market)
            else:
                print(f"❌ Error en API: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Error obteniendo odds: {e}")
            return None

    def _get_mock_odds(self, player_name: str, market: str) -> Dict:
        """
        Genera odds de ejemplo para testing

        Args:
            player_name: Nombre del jugador
            market: Tipo de mercado

        Returns:
            Dict con odds mock
        """
        # Datos de ejemplo realistas
        mock_data = {
            'player_points': {
                'line': 24.5,
                'sportsbooks': [
                    {'name': 'DraftKings', 'line': 24.5, 'over_odds': -110, 'under_odds': -110},
                    {'name': 'FanDuel', 'line': 25.0, 'over_odds': -115, 'under_odds': -105},
                    {'name': 'BetMGM', 'line': 24.5, 'over_odds': -105, 'under_odds': -115},
                    {'name': 'Caesars', 'line': 25.0, 'over_odds': -110, 'under_odds': -110}
                ]
            },
            'player_rebounds': {
                'line': 8.5,
                'sportsbooks': [
                    {'name': 'DraftKings', 'line': 8.5, 'over_odds': -115, 'under_odds': -105},
                    {'name': 'FanDuel', 'line': 9.0, 'over_odds': -110, 'under_odds': -110},
                    {'name': 'BetMGM', 'line': 8.5, 'over_odds': -110, 'under_odds': -110},
                    {'name': 'Caesars', 'line': 9.0, 'over_odds': -105, 'under_odds': -115}
                ]
            },
            'player_assists': {
                'line': 6.5,
                'sportsbooks': [
                    {'name': 'DraftKings', 'line': 6.5, 'over_odds': -110, 'under_odds': -110},
                    {'name': 'FanDuel', 'line': 7.0, 'over_odds': -120, 'under_odds': +100},
                    {'name': 'BetMGM', 'line': 6.5, 'over_odds': -105, 'under_odds': -115},
                    {'name': 'Caesars', 'line': 6.5, 'over_odds': -110, 'under_odds': -110}
                ]
            }
        }

        return mock_data.get(market, mock_data['player_points'])

    def _parse_odds_response(self, data: Dict, player_name: str, market: str) -> Optional[Dict]:
        """
        Parsea respuesta de la API de odds

        Args:
            data: Respuesta JSON de la API
            player_name: Nombre del jugador a filtrar
            market: Tipo de mercado

        Returns:
            Dict con odds procesadas
        """
        # Implementación específica para cada API
        # Este es un placeholder - cada API tiene su estructura
        pass

    def compare_with_model(self, player_name: str, stat_type: str,
                          model_line: float, model_rec: str) -> Dict:
        """
        Compara línea del modelo con líneas del mercado

        Args:
            player_name: Nombre del jugador
            stat_type: 'PTS', 'REB', o 'AST'
            model_line: Línea recomendada por el modelo
            model_rec: Recomendación del modelo ('OVER' o 'UNDER')

        Returns:
            Dict con comparación y value bets
        """
        # Mapear tipos de stats a markets
        market_map = {
            'PTS': 'player_points',
            'REB': 'player_rebounds',
            'AST': 'player_assists'
        }

        market = market_map.get(stat_type)
        if not market:
            return None

        # Obtener odds del mercado
        market_odds = self.get_player_props(player_name, market)

        if not market_odds:
            return None

        # Análisis de value
        sportsbooks = market_odds.get('sportsbooks', [])
        value_bets = []

        for book in sportsbooks:
            book_line = book['line']
            edge = model_line - book_line

            # Determinar si hay value
            has_value = False
            bet_type = None

            if model_rec == 'OVER' and edge > 0.5:
                has_value = True
                bet_type = 'OVER'
            elif model_rec == 'UNDER' and edge < -0.5:
                has_value = True
                bet_type = 'UNDER'

            if has_value:
                value_bets.append({
                    'sportsbook': book['name'],
                    'line': book_line,
                    'bet_type': bet_type,
                    'edge': abs(edge),
                    'odds': book['over_odds'] if bet_type == 'OVER' else book['under_odds']
                })

        return {
            'player': player_name,
            'stat_type': stat_type,
            'model_line': model_line,
            'model_recommendation': model_rec,
            'market_lines': sportsbooks,
            'value_bets': sorted(value_bets, key=lambda x: x['edge'], reverse=True)
        }


class ValueBetFinder:
    """Identificador de value bets"""

    def __init__(self, api: SportsbookAPI):
        """
        Inicializa el buscador

        Args:
            api: Instancia de SportsbookAPI
        """
        self.api = api
        self.min_edge = api.config.get('comparison_settings', {}).get('min_edge_percentage', 5) / 100

    def find_value_bets(self, analyses: List[Dict]) -> List[Dict]:
        """
        Busca value bets en todos los análisis

        Args:
            analyses: Lista de análisis de jugadores

        Returns:
            Lista de value bets ordenadas por edge
        """
        all_value_bets = []

        for analysis in analyses:
            player = analysis['player']

            for stat_type, data in analysis['analyses'].items():
                if not data or data['confidence_stars'] < 3:
                    continue

                comparison = self.api.compare_with_model(
                    player,
                    stat_type,
                    data['line'],
                    data['recommendation']
                )

                if comparison and comparison['value_bets']:
                    for vbet in comparison['value_bets']:
                        vbet['player'] = player
                        vbet['stat_type'] = stat_type
                        vbet['confidence_stars'] = data['confidence_stars']
                        all_value_bets.append(vbet)

        # Ordenar por edge y confianza
        all_value_bets.sort(key=lambda x: (x['edge'], x['confidence_stars']), reverse=True)

        return all_value_bets

    def format_value_bet_report(self, value_bets: List[Dict]) -> str:
        """
        Formatea reporte de value bets

        Args:
            value_bets: Lista de value bets

        Returns:
            String con reporte formateado
        """
        if not value_bets:
            return "\n⚠️  No se detectaron value bets con los criterios actuales.\n"

        report = []
        report.append(f"\n{'='*70}")
        report.append(f"💎 VALUE BETS DETECTADOS - {datetime.now().strftime('%Y-%m-%d')}")
        report.append(f"{'='*70}\n")

        for idx, vbet in enumerate(value_bets, 1):
            stars = '⭐' * vbet['confidence_stars']
            odds_str = f"{vbet['odds']:+d}" if vbet['odds'] < 0 else f"+{vbet['odds']}"

            report.append(f"{idx}. {stars}")
            report.append(f"   🏀 {vbet['player']} - {vbet['stat_type']}")
            report.append(f"   📊 {vbet['bet_type']} {vbet['line']}")
            report.append(f"   🏦 {vbet['sportsbook']} ({odds_str})")
            report.append(f"   💰 Edge: +{vbet['edge']:.1f} vs modelo")
            report.append(f"")

        report.append(f"{'='*70}\n")

        return '\n'.join(report)


def format_comparison_table(comparison: Dict) -> str:
    """
    Formatea tabla de comparación de odds

    Args:
        comparison: Dict con comparación de odds

    Returns:
        String con tabla formateada
    """
    report = []

    report.append(f"\n{'='*70}")
    report.append(f"🏦 COMPARACIÓN CON CASAS DE APUESTAS")
    report.append(f"{'='*70}\n")

    report.append(f"Jugador: {comparison['player']}")
    report.append(f"Métrica: {comparison['stat_type']}")
    report.append(f"Línea del Modelo: {comparison['model_line']}")
    report.append(f"Recomendación: {comparison['model_recommendation']}\n")

    report.append(f"┌────────────────┬──────────┬──────────┬──────────┐")
    report.append(f"│ Casa de Apuesta│  Línea   │   Over   │  Under   │")
    report.append(f"├────────────────┼──────────┼──────────┼──────────┤")

    for book in comparison['market_lines']:
        name = book['name'][:14].ljust(14)
        line = str(book['line']).center(8)
        over = f"{book['over_odds']:+d}".center(8)
        under = f"{book['under_odds']:+d}".center(8)
        report.append(f"│ {name} │ {line} │ {over} │ {under} │")

    report.append(f"└────────────────┴──────────┴──────────┴──────────┘\n")

    # Value bets
    if comparison['value_bets']:
        report.append(f"💎 VALUE BETS DETECTADOS:")
        for vbet in comparison['value_bets']:
            odds_str = f"{vbet['odds']:+d}" if vbet['odds'] < 0 else f"+{vbet['odds']}"
            report.append(f"   ✅ {vbet['bet_type']} {vbet['line']} en {vbet['sportsbook']} ({odds_str})")
            report.append(f"      Edge: +{vbet['edge']:.1f} puntos")
        report.append(f"")

    report.append(f"{'='*70}\n")

    return '\n'.join(report)


def main():
    """Función principal para testing"""
    print(f"\n{'='*70}")
    print(f"🏦 SPORTSBOOK INTEGRATION TEST")
    print(f"{'='*70}\n")

    # Inicializar API
    api = SportsbookAPI()

    # Test con jugador de ejemplo
    test_players = [
        ('Nikola Jokic', 'PTS', 28.5, 'OVER'),
        ('Nikola Jokic', 'REB', 12.5, 'OVER'),
        ('Nikola Jokic', 'AST', 10.5, 'OVER')
    ]

    for player, stat, line, rec in test_players:
        print(f"⚙️  Testing: {player} - {stat}")
        comparison = api.compare_with_model(player, stat, line, rec)

        if comparison:
            print(format_comparison_table(comparison))

    # Test de value bet finder
    print(f"\n{'='*70}")
    print(f"💎 VALUE BET FINDER TEST")
    print(f"{'='*70}\n")

    mock_analyses = [{
        'player': 'Nikola Jokic',
        'team': 'DEN',
        'analyses': {
            'PTS': {
                'line': 28.5,
                'recommendation': 'OVER',
                'confidence_stars': 5
            },
            'REB': {
                'line': 12.5,
                'recommendation': 'OVER',
                'confidence_stars': 4
            }
        }
    }]

    finder = ValueBetFinder(api)
    value_bets = finder.find_value_bets(mock_analyses)

    if value_bets:
        print(finder.format_value_bet_report(value_bets))
    else:
        print("⚠️  No value bets encontrados en el test\n")


if __name__ == '__main__':
    main()
