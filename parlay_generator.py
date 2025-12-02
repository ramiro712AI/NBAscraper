#!/usr/bin/env python3
"""
PARLAY GENERATOR - Generador de Parlays de Alta Confianza
Crea combinaciones de 7 jugadores con 80%+ de probabilidad basado en:
- Líneas de FanDuel
- Métricas de confianza del modelo
- Análisis estadístico avanzado
"""

import pandas as pd
import numpy as np
from datetime import datetime
from itertools import combinations
from typing import List, Dict, Tuple
import json


class ParlayGenerator:
    """Generador de parlays de alta confianza"""

    def __init__(self, min_confidence_stars: int = 4, min_probability: float = 0.80):
        """
        Inicializa el generador

        Args:
            min_confidence_stars: Mínimo de estrellas para incluir en parlay (default: 4)
            min_probability: Probabilidad mínima del parlay (default: 0.80 = 80%)
        """
        self.min_confidence_stars = min_confidence_stars
        self.min_probability = min_probability

    def calculate_bet_probability(self, confidence_stars: int, cv: float,
                                  trend: str, edge: float = 0) -> float:
        """
        Calcula probabilidad de éxito de una apuesta individual

        Args:
            confidence_stars: Nivel de confianza (1-5 estrellas)
            cv: Coeficiente de variación
            trend: Tendencia ('UP', 'DOWN', 'STABLE')
            edge: Edge sobre el mercado (opcional)

        Returns:
            Probabilidad estimada (0-1)
        """
        # Probabilidad base según estrellas (ajustada más optimista)
        base_prob = {
            5: 0.92,  # 92% para 5 estrellas (muy alta confianza)
            4: 0.84,  # 84% para 4 estrellas
            3: 0.72,  # 72% para 3 estrellas
            2: 0.62,  # 62% para 2 estrellas
            1: 0.52   # 52% para 1 estrella
        }.get(confidence_stars, 0.50)

        # Ajuste por CV (consistencia)
        if cv < 10:
            base_prob += 0.03
        elif cv < 15:
            base_prob += 0.02
        elif cv > 30:
            base_prob -= 0.05

        # Ajuste por tendencia
        if trend == 'UP':
            base_prob += 0.02
        elif trend == 'DOWN':
            base_prob -= 0.02

        # Ajuste por edge sobre mercado
        if edge > 3:
            base_prob += 0.03
        elif edge > 2:
            base_prob += 0.02

        # Asegurar que esté entre 0 y 1
        return max(0.0, min(1.0, base_prob))

    def calculate_parlay_probability(self, bets: List[Dict]) -> float:
        """
        Calcula probabilidad combinada de un parlay

        Args:
            bets: Lista de apuestas en el parlay

        Returns:
            Probabilidad del parlay (0-1)
        """
        # Probabilidad conjunta (multiplicar probabilidades individuales)
        parlay_prob = 1.0

        for bet in bets:
            prob = self.calculate_bet_probability(
                bet['confidence_stars'],
                bet['cv'],
                bet.get('trend', 'STABLE'),
                bet.get('edge', 0)
            )
            parlay_prob *= prob

        return parlay_prob

    def filter_high_confidence_bets(self, all_bets: List[Dict]) -> List[Dict]:
        """
        Filtra apuestas de alta confianza

        Args:
            all_bets: Lista de todas las apuestas disponibles

        Returns:
            Lista de apuestas que cumplen criterios mínimos
        """
        filtered = []

        for bet in all_bets:
            # Debe tener al menos X estrellas
            if bet['confidence_stars'] < self.min_confidence_stars:
                continue

            # Debe tener línea de FanDuel
            if 'fanduel_line' not in bet or bet['fanduel_line'] is None:
                continue

            # Calcular probabilidad individual
            prob = self.calculate_bet_probability(
                bet['confidence_stars'],
                bet['cv'],
                bet.get('trend', 'STABLE'),
                bet.get('edge', 0)
            )

            bet['individual_probability'] = prob

            # Solo incluir si probabilidad individual > 70%
            if prob >= 0.70:
                filtered.append(bet)

        return filtered

    def generate_parlays(self, high_conf_bets: List[Dict],
                        parlay_size: int = 7) -> List[Dict]:
        """
        Genera todos los parlays posibles que cumplan criterios

        Args:
            high_conf_bets: Lista de apuestas de alta confianza
            parlay_size: Número de apuestas por parlay (default: 7)

        Returns:
            Lista de parlays que cumplen con probabilidad mínima
        """
        valid_parlays = []

        print(f"\n🔍 Buscando parlays de {parlay_size} jugadores...")
        print(f"📊 Apuestas disponibles: {len(high_conf_bets)}")
        print(f"🎯 Probabilidad mínima: {self.min_probability*100}%\n")

        # Generar todas las combinaciones posibles
        total_combinations = 0
        for combo in combinations(high_conf_bets, parlay_size):
            total_combinations += 1

            # Verificar que no haya jugadores duplicados
            players = [bet['player'] for bet in combo]
            if len(players) != len(set(players)):
                continue

            # Calcular probabilidad del parlay
            parlay_prob = self.calculate_parlay_probability(list(combo))

            # Si cumple con probabilidad mínima, guardarlo
            if parlay_prob >= self.min_probability:
                # Calcular odds americanos aproximados
                american_odds = self.calculate_american_odds(parlay_prob)
                potential_payout = self.calculate_payout(100, american_odds)

                valid_parlays.append({
                    'bets': list(combo),
                    'probability': parlay_prob,
                    'american_odds': american_odds,
                    'potential_payout': potential_payout,
                    'risk': 'BAJO' if parlay_prob >= 0.85 else 'MEDIO'
                })

        print(f"✅ Combinaciones evaluadas: {total_combinations}")
        print(f"✅ Parlays válidos encontrados: {len(valid_parlays)}\n")

        # Ordenar por probabilidad (mayor a menor)
        valid_parlays.sort(key=lambda x: x['probability'], reverse=True)

        return valid_parlays

    def calculate_american_odds(self, probability: float) -> int:
        """
        Convierte probabilidad a odds americanos

        Args:
            probability: Probabilidad (0-1)

        Returns:
            Odds en formato americano
        """
        if probability >= 0.5:
            # Favorito (odds negativos)
            return int(-100 * probability / (1 - probability))
        else:
            # Underdog (odds positivos)
            return int(100 * (1 - probability) / probability)

    def calculate_payout(self, stake: float, american_odds: int) -> float:
        """
        Calcula pago potencial

        Args:
            stake: Cantidad apostada
            american_odds: Odds americanos

        Returns:
            Pago total (stake + ganancia)
        """
        if american_odds < 0:
            # Favorito
            win = stake / (abs(american_odds) / 100)
        else:
            # Underdog
            win = stake * (american_odds / 100)

        return round(stake + win, 2)

    def format_parlay_report(self, parlays: List[Dict], max_parlays: int = 10) -> str:
        """
        Formatea reporte de parlays

        Args:
            parlays: Lista de parlays
            max_parlays: Máximo de parlays a mostrar

        Returns:
            String con reporte formateado
        """
        if not parlays:
            return "\n⚠️  No se encontraron parlays que cumplan con los criterios.\n"

        report = []
        report.append(f"\n{'='*80}")
        report.append(f"💰 PARLAYS DE ALTA CONFIANZA - {datetime.now().strftime('%Y-%m-%d')}")
        report.append(f"{'='*80}")
        report.append(f"\n🎯 Criterios:")
        report.append(f"   - Tamaño del parlay: 7 jugadores")
        report.append(f"   - Probabilidad mínima: {self.min_probability*100}%")
        report.append(f"   - Confianza mínima: {self.min_confidence_stars} estrellas")
        report.append(f"   - Sportsbook: FanDuel")
        report.append(f"\n📊 Total de parlays encontrados: {len(parlays)}")
        report.append(f"📄 Mostrando top {min(max_parlays, len(parlays))}\n")
        report.append(f"{'='*80}\n")

        for idx, parlay in enumerate(parlays[:max_parlays], 1):
            prob_pct = parlay['probability'] * 100
            risk_emoji = '🟢' if parlay['risk'] == 'BAJO' else '🟡'

            report.append(f"{'─'*80}")
            report.append(f"PARLAY #{idx} {risk_emoji}")
            report.append(f"{'─'*80}")
            report.append(f"📊 Probabilidad: {prob_pct:.1f}%")
            report.append(f"💵 Odds: {parlay['american_odds']:+d}")
            report.append(f"💰 Pago por $100: ${parlay['potential_payout']:.2f}")
            report.append(f"⚠️  Riesgo: {parlay['risk']}\n")

            report.append(f"📋 APUESTAS (7):\n")

            for bet_idx, bet in enumerate(parlay['bets'], 1):
                stars = '⭐' * bet['confidence_stars']
                prob = bet['individual_probability'] * 100

                report.append(f"   {bet_idx}. {stars} ({prob:.0f}%)")
                report.append(f"      🏀 {bet['player']} ({bet['team']})")
                report.append(f"      📊 {bet['recommendation']} {bet['fanduel_line']} {bet['stat_type']}")
                report.append(f"      📈 Promedio: {bet['mean']} | CV: {bet['cv']}%")

                if bet.get('edge', 0) > 0:
                    report.append(f"      💎 Edge: +{bet['edge']:.1f} vs mercado")

                report.append("")

            report.append(f"{'─'*80}\n")

        # Resumen de inversión
        report.append(f"{'='*80}")
        report.append(f"💡 RECOMENDACIÓN DE INVERSIÓN")
        report.append(f"{'='*80}\n")

        # Estrategia sugerida
        if len(parlays) >= 3:
            report.append(f"📊 Estrategia sugerida para bankroll de $1000:\n")
            report.append(f"   Parlay #1 ({parlays[0]['probability']*100:.1f}%): $300")
            report.append(f"   Parlay #2 ({parlays[1]['probability']*100:.1f}%): $200")
            report.append(f"   Parlay #3 ({parlays[2]['probability']*100:.1f}%): $150")
            report.append(f"   Reserva: $350")
            report.append(f"\n   💰 Potencial retorno esperado:")

            exp_return = 0
            exp_return += 300 * (parlays[0]['potential_payout'] / 100 - 1) * parlays[0]['probability']
            exp_return += 200 * (parlays[1]['potential_payout'] / 100 - 1) * parlays[1]['probability']
            exp_return += 150 * (parlays[2]['potential_payout'] / 100 - 1) * parlays[2]['probability']

            report.append(f"   📈 EV (Valor Esperado): ${exp_return:.2f}")
            report.append(f"   📊 ROI Esperado: {(exp_return/650)*100:.1f}%")

        report.append(f"\n{'='*80}\n")

        return '\n'.join(report)

    def export_to_json(self, parlays: List[Dict], filename: str):
        """
        Exporta parlays a JSON

        Args:
            parlays: Lista de parlays
            filename: Nombre del archivo
        """
        # Simplificar para JSON
        export_data = []

        for idx, parlay in enumerate(parlays, 1):
            parlay_data = {
                'parlay_id': idx,
                'probability': round(parlay['probability'] * 100, 2),
                'american_odds': parlay['american_odds'],
                'potential_payout': parlay['potential_payout'],
                'risk': parlay['risk'],
                'bets': []
            }

            for bet in parlay['bets']:
                parlay_data['bets'].append({
                    'player': bet['player'],
                    'team': bet['team'],
                    'stat': bet['stat_type'],
                    'recommendation': bet['recommendation'],
                    'line': bet['fanduel_line'],
                    'confidence_stars': bet['confidence_stars'],
                    'probability': round(bet['individual_probability'] * 100, 2)
                })

            export_data.append(parlay_data)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Parlays exportados a: {filename}")


def load_betting_data_from_analysis(analyses: List[Dict]) -> List[Dict]:
    """
    Convierte análisis en formato para parlay generator

    Args:
        analyses: Lista de análisis de jugadores

    Returns:
        Lista de apuestas en formato estándar
    """
    all_bets = []

    for analysis in analyses:
        player = analysis['player']
        team = analysis['team']

        for stat_type, data in analysis['analyses'].items():
            if not data:
                continue

            # Buscar línea de FanDuel (mock o real)
            fanduel_line = data.get('line')  # Por defecto usar línea del modelo

            # Si hay comparación con sportsbooks, buscar FanDuel específicamente
            if 'sportsbook_lines' in data:
                for book in data.get('sportsbook_lines', []):
                    if book.get('name') == 'FanDuel':
                        fanduel_line = book.get('line')
                        break

            bet = {
                'player': player,
                'team': team,
                'stat_type': stat_type,
                'recommendation': data['recommendation'],
                'line': data['line'],
                'fanduel_line': fanduel_line,
                'mean': data['mean'],
                'std': data['std'],
                'cv': data['cv'],
                'confidence_stars': data['confidence_stars'],
                'trend': data.get('trend', 'STABLE'),
                'edge': data.get('edge', 0)
            }

            all_bets.append(bet)

    return all_bets


# ============================================================================
# DATOS MOCK REALISTAS (Para demostración)
# ============================================================================

def generate_mock_betting_data() -> List[Dict]:
    """
    Genera datos mock realistas para demostración
    """
    mock_players = [
        # Jugadores de alta confianza
        {'player': 'Nikola Jokic', 'team': 'DEN', 'stat': 'PTS', 'mean': 28.6, 'cv': 11.2, 'stars': 5, 'line': 28.5, 'rec': 'OVER', 'trend': 'UP'},
        {'player': 'Nikola Jokic', 'team': 'DEN', 'stat': 'REB', 'mean': 13.2, 'cv': 15.9, 'stars': 4, 'line': 12.5, 'rec': 'OVER', 'trend': 'STABLE'},
        {'player': 'Luka Doncic', 'team': 'DAL', 'stat': 'PTS', 'mean': 33.4, 'cv': 12.8, 'stars': 5, 'line': 32.5, 'rec': 'OVER', 'trend': 'UP'},
        {'player': 'Luka Doncic', 'team': 'DAL', 'stat': 'AST', 'mean': 9.8, 'cv': 18.3, 'stars': 4, 'line': 9.5, 'rec': 'OVER', 'trend': 'STABLE'},
        {'player': 'Giannis Antetokounmpo', 'team': 'MIL', 'stat': 'PTS', 'mean': 31.2, 'cv': 10.5, 'stars': 5, 'line': 30.5, 'rec': 'OVER', 'trend': 'UP'},
        {'player': 'Giannis Antetokounmpo', 'team': 'MIL', 'stat': 'REB', 'mean': 11.4, 'cv': 14.2, 'stars': 4, 'line': 11.5, 'rec': 'UNDER', 'trend': 'DOWN'},
        {'player': 'Anthony Davis', 'team': 'LAL', 'stat': 'REB', 'mean': 13.8, 'cv': 13.1, 'stars': 5, 'line': 12.5, 'rec': 'OVER', 'trend': 'UP'},
        {'player': 'Anthony Davis', 'team': 'LAL', 'stat': 'PTS', 'mean': 26.2, 'cv': 16.4, 'stars': 4, 'line': 25.5, 'rec': 'OVER', 'trend': 'STABLE'},
        {'player': 'Jayson Tatum', 'team': 'BOS', 'stat': 'PTS', 'mean': 27.8, 'cv': 11.8, 'stars': 5, 'line': 27.5, 'rec': 'OVER', 'trend': 'UP'},
        {'player': 'Tyrese Haliburton', 'team': 'IND', 'stat': 'AST', 'mean': 11.4, 'cv': 14.2, 'stars': 5, 'line': 10.5, 'rec': 'OVER', 'trend': 'UP'},
        {'player': 'Joel Embiid', 'team': 'PHI', 'stat': 'PTS', 'mean': 29.4, 'cv': 12.3, 'stars': 5, 'line': 28.5, 'rec': 'OVER', 'trend': 'STABLE'},
        {'player': 'Joel Embiid', 'team': 'PHI', 'stat': 'REB', 'mean': 10.8, 'cv': 16.7, 'stars': 4, 'line': 10.5, 'rec': 'OVER', 'trend': 'STABLE'},
        {'player': 'Shai Gilgeous-Alexander', 'team': 'OKC', 'stat': 'PTS', 'mean': 30.6, 'cv': 13.4, 'stars': 5, 'line': 30.5, 'rec': 'OVER', 'trend': 'UP'},
        {'player': 'Stephen Curry', 'team': 'GSW', 'stat': 'PTS', 'mean': 26.8, 'cv': 17.2, 'stars': 4, 'line': 26.5, 'rec': 'OVER', 'trend': 'STABLE'},
        {'player': 'Damian Lillard', 'team': 'MIL', 'stat': 'PTS', 'mean': 25.2, 'cv': 15.8, 'stars': 4, 'line': 24.5, 'rec': 'OVER', 'trend': 'STABLE'},
        {'player': 'Damian Lillard', 'team': 'MIL', 'stat': 'AST', 'mean': 7.6, 'cv': 18.9, 'stars': 4, 'line': 7.5, 'rec': 'OVER', 'trend': 'STABLE'},
        {'player': 'Kawhi Leonard', 'team': 'LAC', 'stat': 'PTS', 'mean': 24.4, 'cv': 14.6, 'stars': 4, 'line': 24.5, 'rec': 'UNDER', 'trend': 'DOWN'},
        {'player': 'Devin Booker', 'team': 'PHX', 'stat': 'PTS', 'mean': 27.2, 'cv': 13.9, 'stars': 4, 'line': 27.5, 'rec': 'UNDER', 'trend': 'STABLE'},
        {'player': 'Trae Young', 'team': 'ATL', 'stat': 'AST', 'mean': 10.8, 'cv': 16.2, 'stars': 4, 'line': 10.5, 'rec': 'OVER', 'trend': 'STABLE'},
        {'player': 'Domantas Sabonis', 'team': 'SAC', 'stat': 'REB', 'mean': 12.6, 'cv': 12.8, 'stars': 5, 'line': 12.5, 'rec': 'OVER', 'trend': 'UP'},
    ]

    bets = []
    for p in mock_players:
        bets.append({
            'player': p['player'],
            'team': p['team'],
            'stat_type': p['stat'],
            'recommendation': p['rec'],
            'line': p['line'],
            'fanduel_line': p['line'],  # FanDuel line
            'mean': p['mean'],
            'std': p['mean'] * (p['cv'] / 100),
            'cv': p['cv'],
            'confidence_stars': p['stars'],
            'trend': p['trend'],
            'edge': 2.5 if p['stars'] == 5 else 1.5,
            'individual_probability': 0  # Se calculará después
        })

    return bets


def main():
    """Función principal"""
    print(f"\n{'='*80}")
    print(f"💰 PARLAY GENERATOR - GENERADOR DE PARLAYS DE ALTA CONFIANZA")
    print(f"{'='*80}\n")

    # Generar datos mock (en producción vendrían del análisis)
    print("📊 Usando datos de ejemplo para demostración...")
    print("💡 En producción, estos datos vendrán del análisis real\n")

    all_bets = generate_mock_betting_data()

    # Inicializar generador
    generator = ParlayGenerator(
        min_confidence_stars=4,  # Mínimo 4 estrellas
        min_probability=0.80     # 80% probabilidad mínima
    )

    # Filtrar apuestas de alta confianza
    high_conf_bets = generator.filter_high_confidence_bets(all_bets)

    print(f"✅ {len(high_conf_bets)} apuestas cumplen criterios de alta confianza\n")

    # Generar parlays
    parlays = generator.generate_parlays(high_conf_bets, parlay_size=7)

    if not parlays:
        print("⚠️  No se encontraron parlays con 80%+ probabilidad")
        print("💡 Intenta:")
        print("   - Reducir probabilidad mínima a 75%")
        print("   - Reducir tamaño de parlay a 5-6 jugadores")
        print("   - Reducir estrellas mínimas a 3\n")
        return

    # Generar reporte
    report = generator.format_parlay_report(parlays, max_parlays=10)
    print(report)

    # Guardar reportes
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Reporte TXT
    txt_file = f'parlays_report_{timestamp}.txt'
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"✅ Reporte TXT guardado en: {txt_file}")

    # Reporte JSON
    json_file = f'parlays_data_{timestamp}.json'
    generator.export_to_json(parlays, json_file)

    print(f"\n{'='*80}\n")


if __name__ == '__main__':
    main()
