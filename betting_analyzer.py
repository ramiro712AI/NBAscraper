#!/usr/bin/env python3
"""
NBA BETTING ANALYZER - OVER/UNDER RECOMENDACIONES
Analiza estadísticas de jugadores y genera recomendaciones de apuestas
basadas en datos históricos y análisis estadístico.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import glob
import json
from typing import Dict, List, Tuple, Optional

# Configuración
CONFIDENCE_THRESHOLDS = {
    'VERY_HIGH': {'cv_max': 15, 'stars': 5},
    'HIGH': {'cv_max': 20, 'stars': 4},
    'MEDIUM': {'cv_max': 25, 'stars': 3},
    'LOW': {'cv_max': 30, 'stars': 2},
    'VERY_LOW': {'cv_max': 100, 'stars': 1}
}

STATS_CATEGORIES = ['PTS', 'REB', 'AST']


class PlayerStatsAnalyzer:
    """Analizador de estadísticas de jugador para apuestas"""

    def __init__(self, player_data: pd.DataFrame):
        """
        Inicializa el analizador con datos del jugador

        Args:
            player_data: DataFrame con estadísticas del jugador
        """
        self.data = player_data
        self.player_name = player_data['PLAYER'].iloc[0] if not player_data.empty else 'Unknown'
        self.team = player_data['TEAM'].iloc[0] if not player_data.empty else 'Unknown'

    def calculate_stats(self, stat_name: str) -> Dict[str, float]:
        """
        Calcula métricas estadísticas para una stat específica

        Args:
            stat_name: Nombre de la estadística (ej: 'PTS_TOTAL', 'REB_TOTAL')

        Returns:
            Dict con mean, std, cv, min, max
        """
        if stat_name not in self.data.columns:
            return None

        values = self.data[stat_name].dropna()

        if len(values) == 0:
            return None

        mean = values.mean()
        std = values.std()
        cv = (std / mean * 100) if mean != 0 else 0

        return {
            'mean': round(mean, 2),
            'std': round(std, 2),
            'cv': round(cv, 2),
            'min': round(values.min(), 2),
            'max': round(values.max(), 2),
            'values': values.tolist()
        }

    def get_consistency_level(self, cv: float) -> Tuple[str, str]:
        """
        Determina el nivel de consistencia basado en CV

        Args:
            cv: Coeficiente de variación

        Returns:
            Tuple de (nivel, emoji)
        """
        if cv < 15:
            return 'MUY CONSISTENTE', '✅'
        elif cv < 25:
            return 'MODERADAMENTE CONSISTENTE', '⚠️'
        else:
            return 'INCONSISTENTE', '❌'

    def get_confidence_level(self, cv: float, trend: str, context_score: int) -> Tuple[int, str]:
        """
        Calcula el nivel de confianza de la apuesta

        Args:
            cv: Coeficiente de variación
            trend: Tendencia ('UP', 'DOWN', 'STABLE')
            context_score: Puntuación de contexto (0-3)

        Returns:
            Tuple de (estrellas, nivel)
        """
        # Base en CV
        if cv < 15:
            stars = 5
        elif cv < 20:
            stars = 4
        elif cv < 25:
            stars = 3
        elif cv < 30:
            stars = 2
        else:
            stars = 1

        # Ajustes por tendencia
        if trend == 'UP' and stars < 5:
            stars += 1
        elif trend == 'DOWN' and stars > 1:
            stars -= 1

        # Ajustes por contexto (no implementado aún)
        # context_score puede venir de análisis de oponente, casa/visitante, etc.

        levels = {
            5: 'MUY ALTA',
            4: 'ALTA',
            3: 'MEDIA',
            2: 'BAJA',
            1: 'MUY BAJA'
        }

        return stars, levels[stars]

    def analyze_trend(self, values: List[float]) -> str:
        """
        Analiza la tendencia de los últimos valores

        Args:
            values: Lista de valores históricos

        Returns:
            'UP', 'DOWN', o 'STABLE'
        """
        if len(values) < 3:
            return 'STABLE'

        # Usar últimos 3 valores
        recent = values[-3:]

        # Simple análisis de pendiente
        if recent[-1] > recent[0] * 1.1:  # 10% de incremento
            return 'UP'
        elif recent[-1] < recent[0] * 0.9:  # 10% de decremento
            return 'DOWN'
        else:
            return 'STABLE'

    def generate_line(self, mean: float, std: float, adjustment: float = 0) -> float:
        """
        Genera línea de over/under

        Args:
            mean: Media de la estadística
            std: Desviación estándar
            adjustment: Ajuste manual (positivo o negativo)

        Returns:
            Línea redondeada a .5
        """
        line = mean + adjustment
        # Redondear a .5 más cercano
        return round(line * 2) / 2

    def should_bet_over(self, mean: float, line: float, cv: float, trend: str) -> bool:
        """
        Determina si se debe apostar OVER

        Args:
            mean: Media de la estadística
            line: Línea de la casa de apuestas
            cv: Coeficiente de variación
            trend: Tendencia

        Returns:
            True si OVER, False si UNDER
        """
        # OVER si la media está sobre la línea
        if mean > line:
            return True
        # OVER si está cerca y hay tendencia alcista
        elif mean >= line * 0.95 and trend == 'UP':
            return True
        else:
            return False

    def generate_reasons(self, stats: Dict, trend: str, consistency: str,
                        stat_type: str) -> List[str]:
        """
        Genera lista de razones para la recomendación

        Args:
            stats: Dict con estadísticas calculadas
            trend: Tendencia
            consistency: Nivel de consistencia
            stat_type: Tipo de estadística (PTS, REB, AST)

        Returns:
            Lista de strings con razones
        """
        reasons = []

        # Razón 1: Promedio
        mean = stats['mean']
        stat_name = {'PTS': 'puntos', 'REB': 'rebotes', 'AST': 'asistencias'}[stat_type]
        reasons.append(f"Promedio de {mean} {stat_name} en últimos 5 juegos")

        # Razón 2: Consistencia
        cv = stats['cv']
        if cv < 15:
            reasons.append(f"Consistencia muy alta (CV: {cv}%)")
        elif cv < 25:
            reasons.append(f"Consistencia moderada (CV: {cv}%)")
        else:
            reasons.append(f"⚠️ Baja consistencia (CV: {cv}%) - Mayor riesgo")

        # Razón 3: Tendencia
        if trend == 'UP':
            values = stats['values']
            reasons.append(f"📈 Tendencia ascendente: {', '.join(map(str, values))}")
        elif trend == 'DOWN':
            reasons.append(f"📉 Tendencia descendente reciente")
        else:
            reasons.append(f"Rendimiento estable en últimos juegos")

        # Razón 4: Rango
        reasons.append(f"Rango típico: [{stats['min']}, {stats['max']}] {stat_name}")

        return reasons

    def analyze_stat(self, stat_type: str) -> Dict:
        """
        Análisis completo de una estadística

        Args:
            stat_type: 'PTS', 'REB', o 'AST'

        Returns:
            Dict con análisis completo
        """
        stat_name = f'{stat_type}_TOTAL'
        stats = self.calculate_stats(stat_name)

        if not stats:
            return None

        mean = stats['mean']
        std = stats['std']
        cv = stats['cv']
        values = stats['values']

        # Análisis
        consistency, consistency_emoji = self.get_consistency_level(cv)
        trend = self.analyze_trend(values)
        line = self.generate_line(mean, std)
        bet_over = self.should_bet_over(mean, line, cv, trend)
        stars, confidence = self.get_confidence_level(cv, trend, context_score=0)
        reasons = self.generate_reasons(stats, trend, consistency, stat_type)

        return {
            'stat_type': stat_type,
            'mean': mean,
            'std': std,
            'cv': cv,
            'min': stats['min'],
            'max': stats['max'],
            'values': values,
            'consistency': consistency,
            'consistency_emoji': consistency_emoji,
            'trend': trend,
            'line': line,
            'recommendation': 'OVER' if bet_over else 'UNDER',
            'confidence_stars': stars,
            'confidence_level': confidence,
            'reasons': reasons
        }


class BettingReportGenerator:
    """Generador de reportes de apuestas"""

    def __init__(self):
        self.reports = []

    def format_stars(self, stars: int) -> str:
        """Formatea las estrellas de confianza"""
        return '⭐' * stars

    def generate_player_report(self, player_name: str, team: str,
                               analyses: Dict[str, Dict]) -> str:
        """
        Genera reporte completo de un jugador

        Args:
            player_name: Nombre del jugador
            team: Equipo
            analyses: Dict con análisis de PTS, REB, AST

        Returns:
            String con reporte formateado
        """
        report = []
        report.append(f"\n{'='*65}")
        report.append(f"🏀 JUGADOR: {player_name} ({team})")
        report.append(f"{'='*65}\n")

        stat_names = {
            'PTS': ('PUNTOS', 'puntos'),
            'REB': ('REBOTES', 'rebotes'),
            'AST': ('ASISTENCIAS', 'asistencias')
        }

        top_bets = []

        for stat_type in STATS_CATEGORIES:
            analysis = analyses.get(stat_type)

            if not analysis:
                continue

            title, unit = stat_names[stat_type]

            report.append(f"─────────────────────────────────────────────────────────────────\n")
            report.append(f"📊 {title}")
            report.append(f"   Promedio últimos 5: {analysis['mean']} {unit}")
            report.append(f"   Desviación estándar: {analysis['std']} {unit}")
            report.append(f"   Rango típico: [{analysis['min']}, {analysis['max']}] {unit}")
            report.append(f"   Consistencia: {analysis['cv']}% - {analysis['consistency']} {analysis['consistency_emoji']}")
            report.append(f"")
            report.append(f"   Distribución últimos 5 juegos: {', '.join(map(str, analysis['values']))}")
            report.append(f"")
            report.append(f"   🎯 LÍNEA RECOMENDADA: {analysis['line']} {unit}")
            report.append(f"")
            report.append(f"   📈 RECOMENDACIÓN: {analysis['recommendation']} {analysis['line']}")
            report.append(f"   🔥 Confianza: {self.format_stars(analysis['confidence_stars'])} ({analysis['confidence_level']})")
            report.append(f"")
            report.append(f"   💡 Razones:")
            for reason in analysis['reasons']:
                report.append(f"   - {reason}")
            report.append(f"")

            # Guardar para resumen
            if analysis['confidence_stars'] >= 3:
                top_bets.append({
                    'stat': title,
                    'rec': f"{analysis['recommendation']} {analysis['line']}",
                    'stars': analysis['confidence_stars']
                })

        # Resumen de apuestas
        if top_bets:
            report.append(f"─────────────────────────────────────────────────────────────────\n")
            report.append(f"📋 RESUMEN DE APUESTAS RECOMENDADAS:")

            # Ordenar por confianza
            top_bets.sort(key=lambda x: x['stars'], reverse=True)

            for bet in top_bets:
                report.append(f"   ✅ {bet['rec']} - Confianza: {self.format_stars(bet['stars'])}")

            # Parlay sugerido si hay 3+ apuestas de alta confianza
            high_conf_bets = [b for b in top_bets if b['stars'] >= 4]
            if len(high_conf_bets) >= 2:
                report.append(f"")
                report.append(f"💰 PARLAY SUGERIDO:")
                parlay_desc = ' / '.join([b['rec'] for b in high_conf_bets[:3]])
                report.append(f"   {parlay_desc}")
                report.append(f"   Riesgo: {'Bajo' if all(b['stars'] == 5 for b in high_conf_bets) else 'Medio'} | Potencial: Alto")

        report.append(f"\n{'='*65}\n")

        return '\n'.join(report)

    def generate_summary(self, all_analyses: List[Dict]) -> str:
        """
        Genera resumen de todas las apuestas del día

        Args:
            all_analyses: Lista de análisis de todos los jugadores

        Returns:
            String con resumen formateado
        """
        report = []
        report.append(f"\n{'='*65}")
        report.append(f"🏆 TOP APUESTAS DEL DÍA - {datetime.now().strftime('%Y-%m-%d')}")
        report.append(f"{'='*65}\n")

        # Recopilar todas las apuestas
        all_bets = []
        for analysis in all_analyses:
            player = analysis['player']
            team = analysis['team']
            for stat_type, data in analysis['analyses'].items():
                if data and data['confidence_stars'] >= 3:
                    all_bets.append({
                        'player': player,
                        'team': team,
                        'stat': stat_type,
                        'rec': f"{data['recommendation']} {data['line']}",
                        'stars': data['confidence_stars'],
                        'mean': data['mean'],
                        'cv': data['cv']
                    })

        # Ordenar por confianza
        all_bets.sort(key=lambda x: (x['stars'], -x['cv']), reverse=True)

        # Top 10
        for idx, bet in enumerate(all_bets[:10], 1):
            stars_str = self.format_stars(bet['stars'])
            report.append(f"{idx}. {stars_str} {bet['player']} {bet['rec']} {bet['stat']} ({bet['team']})")
            report.append(f"   → Promedio: {bet['mean']} | CV: {bet['cv']}%\n")

        report.append(f"{'='*65}\n")

        return '\n'.join(report)


def load_player_data(csv_path: str) -> pd.DataFrame:
    """
    Carga datos de un CSV de jugador

    Args:
        csv_path: Ruta al archivo CSV

    Returns:
        DataFrame con los datos
    """
    try:
        df = pd.read_csv(csv_path)
        return df
    except Exception as e:
        print(f"❌ Error cargando {csv_path}: {e}")
        return pd.DataFrame()


def analyze_team_csv(csv_path: str) -> List[Dict]:
    """
    Analiza un CSV de equipo completo

    Args:
        csv_path: Ruta al CSV del equipo

    Returns:
        Lista de análisis por jugador
    """
    df = load_player_data(csv_path)

    if df.empty:
        return []

    results = []

    # Agrupar por jugador
    for player_name in df['PLAYER'].unique():
        player_df = df[df['PLAYER'] == player_name]

        analyzer = PlayerStatsAnalyzer(player_df)

        analyses = {}
        for stat_type in STATS_CATEGORIES:
            analysis = analyzer.analyze_stat(stat_type)
            if analysis:
                analyses[stat_type] = analysis

        if analyses:
            results.append({
                'player': player_name,
                'team': analyzer.team,
                'analyses': analyses
            })

    return results


def main():
    """Función principal"""
    print(f"\n{'='*65}")
    print(f"🏀 NBA BETTING ANALYZER - OVER/UNDER RECOMMENDATIONS")
    print(f"{'='*65}\n")

    # Buscar todos los CSVs generados
    csv_files = glob.glob('*_last_5_games*.csv')

    if not csv_files:
        print("❌ No se encontraron archivos CSV.")
        print("💡 Ejecuta primero 'nba_nuevo.py' o 'nba_auto_scraper.py'")
        return

    print(f"📁 Archivos CSV encontrados: {len(csv_files)}\n")

    all_analyses = []
    report_gen = BettingReportGenerator()

    for csv_file in csv_files:
        print(f"⚙️  Procesando: {csv_file}")

        team_analyses = analyze_team_csv(csv_file)
        all_analyses.extend(team_analyses)

        # Generar reporte por jugador
        for analysis in team_analyses:
            report = report_gen.generate_player_report(
                analysis['player'],
                analysis['team'],
                analysis['analyses']
            )
            print(report)

    # Generar resumen general
    if all_analyses:
        summary = report_gen.generate_summary(all_analyses)
        print(summary)

        # Guardar reporte en archivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'betting_report_{timestamp}.txt'

        with open(output_file, 'w', encoding='utf-8') as f:
            for analysis in all_analyses:
                report = report_gen.generate_player_report(
                    analysis['player'],
                    analysis['team'],
                    analysis['analyses']
                )
                f.write(report)
            f.write(summary)

        print(f"✅ Reporte guardado en: {output_file}\n")
    else:
        print("⚠️  No se generaron análisis. Verifica los datos de entrada.\n")


if __name__ == '__main__':
    main()
