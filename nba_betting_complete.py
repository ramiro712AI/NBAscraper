#!/usr/bin/env python3
"""
NBA BETTING ANALYZER - SISTEMA COMPLETO
Script unificado que ejecuta todo el proceso de análisis de apuestas:
1. Scraping de datos de juegos del día
2. Análisis estadístico y generación de líneas Over/Under
3. Comparación con casas de apuestas y detección de value bets
"""

import sys
import os
from datetime import datetime
import glob

# Banner del sistema
def print_banner():
    """Imprime banner de inicio"""
    print("\n" + "="*70)
    print("🏀 NBA BETTING ANALYZER - SISTEMA COMPLETO")
    print("="*70)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")


def print_step(step_num, title):
    """Imprime encabezado de paso"""
    print("\n" + "─"*70)
    print(f"📍 PASO {step_num}: {title}")
    print("─"*70 + "\n")


# ============================================================================
# PASO 1: SCRAPING DE DATOS
# ============================================================================

def step1_scraping():
    """
    Ejecuta el scraper para obtener datos de juegos del día
    """
    print_step(1, "SCRAPING DE DATOS")

    try:
        # Importar el módulo de scraping
        import nba_nuevo as scraper

        # Obtener equipos que juegan HOY
        teams_playing = scraper.get_todays_games()

        if not teams_playing:
            print("❌ No hay juegos programados para hoy.")
            print("💡 No se pueden generar análisis de apuestas sin datos.\n")
            return False

        print(f"\n⚙️  Procesando datos de {len(teams_playing)} equipos...\n")

        # Procesar cada equipo
        csv_count = 0
        for team_abbr in teams_playing:
            team_id, team_name = scraper.TEAM_ABBREVIATIONS.get(team_abbr, (None, None))

            if not team_id:
                continue

            print(f"  📊 Procesando: {team_abbr} ({team_name})...")

            # Obtener últimos 5 juegos
            games = scraper.get_team_schedule(team_id, limit=5)

            if len(games) < 3:
                print(f"     ⚠️  Solo {len(games)} juegos disponibles (mínimo 3)")
                continue

            # Recopilar estadísticas
            all_stats = []
            for game_id in games:
                stats = scraper.get_quarter_stats_from_playbyplay(game_id, team_id)
                if stats:
                    all_stats.extend(stats)

            if all_stats:
                # Guardar CSV
                import pandas as pd
                df = pd.DataFrame(all_stats)
                filename = f"{team_abbr}_last_5_games_ALL_QUARTERS.csv"
                df.to_csv(filename, index=False)
                csv_count += 1
                print(f"     ✅ CSV generado: {filename}")

        print(f"\n✅ SCRAPING COMPLETADO: {csv_count} CSVs generados\n")
        return True

    except Exception as e:
        print(f"❌ Error en scraping: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# PASO 2: ANÁLISIS Y RECOMENDACIONES
# ============================================================================

def step2_analysis():
    """
    Analiza estadísticas y genera recomendaciones de Over/Under
    """
    print_step(2, "ANÁLISIS ESTADÍSTICO Y RECOMENDACIONES")

    try:
        # Importar módulos necesarios
        import pandas as pd
        import numpy as np
        from betting_analyzer import (
            PlayerStatsAnalyzer,
            BettingReportGenerator,
            STATS_CATEGORIES
        )

        # Buscar CSVs
        csv_files = glob.glob('*_last_5_games*.csv')

        if not csv_files:
            print("❌ No se encontraron archivos CSV.")
            print("💡 Asegúrate de que el scraping se ejecutó correctamente.\n")
            return None

        print(f"📁 Archivos CSV encontrados: {len(csv_files)}")
        print(f"⚙️  Analizando jugadores...\n")

        all_analyses = []
        report_gen = BettingReportGenerator()
        player_count = 0

        for csv_file in csv_files:
            df = pd.read_csv(csv_file)

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
                    all_analyses.append({
                        'player': player_name,
                        'team': analyzer.team,
                        'analyses': analyses
                    })
                    player_count += 1

        print(f"✅ {player_count} jugadores analizados\n")

        # Generar reportes
        print("📝 Generando reporte detallado...\n")

        full_report = []

        for analysis in all_analyses:
            report = report_gen.generate_player_report(
                analysis['player'],
                analysis['team'],
                analysis['analyses']
            )
            full_report.append(report)
            print(report)  # Mostrar en consola

        # Generar resumen
        summary = report_gen.generate_summary(all_analyses)
        full_report.append(summary)
        print(summary)

        # Guardar reporte
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'betting_report_{timestamp}.txt'

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(full_report))

        print(f"✅ ANÁLISIS COMPLETADO")
        print(f"📄 Reporte guardado en: {output_file}\n")

        return all_analyses

    except Exception as e:
        print(f"❌ Error en análisis: {e}")
        import traceback
        traceback.print_exc()
        return None


# ============================================================================
# PASO 3: COMPARACIÓN CON CASAS DE APUESTAS
# ============================================================================

def step3_sportsbook_comparison(all_analyses):
    """
    Compara con líneas de casas de apuestas y detecta value bets
    """
    print_step(3, "COMPARACIÓN CON CASAS DE APUESTAS")

    if not all_analyses:
        print("⚠️  No hay análisis para comparar con el mercado.")
        return

    try:
        from sportsbook_integration import (
            SportsbookAPI,
            ValueBetFinder,
            format_comparison_table
        )

        # Inicializar API
        api = SportsbookAPI()

        print("🏦 Conectando con casas de apuestas...")
        print(f"📡 API: {api.config['sportsbooks']['odds_api']['name']}")

        if api.mock_mode:
            print("⚠️  Modo MOCK activado (usando datos de ejemplo)")
        else:
            print("✅ Modo REAL activado (obteniendo odds reales)")

        print()

        # Buscar value bets
        finder = ValueBetFinder(api)

        print("🔍 Buscando value bets...\n")

        # Comparar algunos jugadores principales
        comparison_count = 0
        for analysis in all_analyses[:10]:  # Top 10 jugadores
            player = analysis['player']

            for stat_type, data in analysis['analyses'].items():
                # Solo comparar apuestas con confianza 4+ estrellas
                if not data or data['confidence_stars'] < 4:
                    continue

                comparison = api.compare_with_model(
                    player,
                    stat_type,
                    data['line'],
                    data['recommendation']
                )

                if comparison:
                    print(format_comparison_table(comparison))
                    comparison_count += 1

        # Generar reporte de value bets
        value_bets = finder.find_value_bets(all_analyses)

        if value_bets:
            value_report = finder.format_value_bet_report(value_bets)
            print(value_report)

            # Guardar reporte de value bets
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'value_bets_{timestamp}.txt'

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(value_report)

            print(f"✅ COMPARACIÓN COMPLETADA")
            print(f"💎 {len(value_bets)} value bets detectados")
            print(f"📄 Reporte guardado en: {output_file}\n")
        else:
            print("⚠️  No se detectaron value bets significativos")
            print("💡 Esto puede significar que:")
            print("   - Las líneas del modelo están alineadas con el mercado")
            print("   - Los umbrales de edge son muy altos")
            print("   - No hay suficientes apuestas de alta confianza\n")

    except Exception as e:
        print(f"❌ Error en comparación: {e}")
        import traceback
        traceback.print_exc()


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    """
    Función principal que ejecuta todo el proceso
    """
    print_banner()

    # PASO 1: Scraping
    success = step1_scraping()

    if not success:
        print("\n❌ El proceso se detuvo debido a errores en el scraping.")
        print("💡 Verifica tu conexión a internet y vuelve a intentar.\n")
        sys.exit(1)

    # PASO 2: Análisis
    all_analyses = step2_analysis()

    if not all_analyses:
        print("\n❌ El proceso se detuvo debido a errores en el análisis.")
        print("💡 Verifica que los CSVs tengan datos válidos.\n")
        sys.exit(1)

    # PASO 3: Comparación con casas de apuestas
    step3_sportsbook_comparison(all_analyses)

    # Resumen final
    print("\n" + "="*70)
    print("🎉 PROCESO COMPLETADO EXITOSAMENTE")
    print("="*70)
    print("\n📊 Archivos generados:")
    print("   - CSVs de equipos (*_last_5_games_ALL_QUARTERS.csv)")
    print("   - Reporte de análisis (betting_report_*.txt)")
    print("   - Reporte de value bets (value_bets_*.txt)")
    print("\n💡 Recomendación:")
    print("   1. Revisa el reporte de análisis para ver todas las recomendaciones")
    print("   2. Consulta el reporte de value bets para oportunidades")
    print("   3. Verifica injury reports antes de apostar")
    print("   4. Apuesta responsablemente")
    print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido por el usuario")
        print("👋 ¡Hasta luego!\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
