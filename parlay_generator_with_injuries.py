#!/usr/bin/env python3
"""
OPTIMIZED PARLAY GENERATOR WITH INJURY CHECKING
Genera parlays verificando automáticamente injury reports
"""

from parlay_generator import ParlayGenerator, generate_mock_betting_data
from injury_checker import InjuryChecker, check_specific_players
from datetime import datetime


def main():
    """Función principal con verificación de lesiones"""
    print(f"\n{'='*80}")
    print(f"💰 PARLAY GENERATOR CON VERIFICACIÓN DE LESIONES")
    print(f"{'='*80}\n")

    # PASO 1: Generar datos base
    print("📊 Generando lista de jugadores potenciales...")
    all_bets = generate_mock_betting_data()

    # Extraer jugadores únicos
    players_to_check = []
    seen_players = set()

    for bet in all_bets:
        player_key = (bet['player'], bet['team'])
        if player_key not in seen_players:
            players_to_check.append(player_key)
            seen_players.add(player_key)

    print(f"✅ {len(players_to_check)} jugadores únicos para verificar\n")

    # PASO 2: Verificar injury reports
    print(f"{'='*80}")
    print(f"🏥 VERIFICANDO INJURY REPORTS EN TIEMPO REAL")
    print(f"{'='*80}\n")

    results = check_specific_players(players_to_check)

    # PASO 3: Filtrar jugadores disponibles
    excluded_players = set()

    print(f"\n{'='*80}")
    print(f"🚫 JUGADORES EXCLUIDOS (OUT/DOUBTFUL)")
    print(f"{'='*80}\n")

    for player_info in results['out']:
        excluded_players.add(player_info['player'])
        print(f"❌ {player_info['player']} ({player_info['team']})")
        print(f"   Status: {player_info['status']}")
        print(f"   Details: {player_info['details']}\n")

    if not excluded_players:
        print("✅ Todos los jugadores están disponibles!\n")

    # PASO 4: Filtrar apuestas
    available_bets = [bet for bet in all_bets if bet['player'] not in excluded_players]

    print(f"{'='*80}")
    print(f"📊 RESUMEN DE FILTRADO")
    print(f"{'='*80}\n")
    print(f"Apuestas originales: {len(all_bets)}")
    print(f"Apuestas disponibles: {len(available_bets)}")
    print(f"Apuestas excluidas: {len(all_bets) - len(available_bets)}\n")

    if len(available_bets) < 7:
        print(f"⚠️  ADVERTENCIA: Solo {len(available_bets)} apuestas disponibles")
        print(f"   Se necesitan al menos 7 para parlays de 7 jugadores")
        print(f"   Considera reducir el tamaño del parlay o agregar más jugadores\n")
        return

    # PASO 5: Advertir sobre jugadores cuestionables
    if results['questionable']:
        print(f"{'='*80}")
        print(f"⚠️  JUGADORES CUESTIONABLES - VERIFICAR ANTES DE APOSTAR")
        print(f"{'='*80}\n")

        for player_info in results['questionable']:
            print(f"⚠️  {player_info['player']} ({player_info['team']})")
            print(f"   Status: {player_info['status']}")
            print(f"   Details: {player_info['details']}")
            print(f"   💡 Verifica 1 hora antes del juego\n")

    # PASO 6: Generar parlays con jugadores disponibles
    print(f"\n{'='*80}")
    print(f"🎯 GENERANDO PARLAYS CON JUGADORES DISPONIBLES")
    print(f"{'='*80}\n")

    # Estrategia 1: 7 jugadores @ 75%
    print(f"{'─'*80}")
    print(f"🎯 ESTRATEGIA 1: Parlays de 7 jugadores (75% probabilidad)")
    print(f"{'─'*80}\n")

    gen1 = ParlayGenerator(min_confidence_stars=4, min_probability=0.75)
    high_conf_1 = gen1.filter_high_confidence_bets(available_bets)
    parlays_7 = gen1.generate_parlays(high_conf_1, parlay_size=7)

    if parlays_7:
        report_7 = gen1.format_parlay_report(parlays_7, max_parlays=3)
        print(report_7)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'parlays_verified_7leg_{timestamp}.txt'

        # Agregar disclaimer sobre injuries
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"{'='*80}\n")
            f.write(f"⚠️  INJURY REPORT VERIFICADO - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"{'='*80}\n\n")

            if excluded_players:
                f.write(f"🚫 JUGADORES EXCLUIDOS:\n")
                for player in sorted(excluded_players):
                    f.write(f"   ❌ {player}\n")
                f.write("\n")

            if results['questionable']:
                f.write(f"⚠️  JUGADORES CUESTIONABLES (Verificar antes de apostar):\n")
                for p in results['questionable']:
                    f.write(f"   ⚠️  {p['player']} ({p['team']}) - {p['status']}\n")
                f.write("\n")

            f.write(f"{'='*80}\n\n")
            f.write(report_7)

        print(f"✅ Guardado: {filename}\n")
    else:
        print("❌ No se encontraron parlays de 7 jugadores con 75% probabilidad")
        print("💡 Esto puede deberse a:")
        print("   - Muchos jugadores clave están lesionados")
        print("   - Se necesitan más jugadores de alta confianza")
        print("   - Considera reducir la probabilidad mínima a 70%\n")

    # Estrategia 2: 6 jugadores @ 80% (Más seguro)
    print(f"\n{'─'*80}")
    print(f"🎯 ESTRATEGIA 2: Parlays de 6 jugadores (80% probabilidad)")
    print(f"{'─'*80}\n")

    gen2 = ParlayGenerator(min_confidence_stars=4, min_probability=0.80)
    high_conf_2 = gen2.filter_high_confidence_bets(available_bets)
    parlays_6 = gen2.generate_parlays(high_conf_2, parlay_size=6)

    if parlays_6:
        report_6 = gen2.format_parlay_report(parlays_6, max_parlays=3)
        print(report_6)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'parlays_verified_6leg_{timestamp}.txt'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_6)
        print(f"✅ Guardado: {filename}\n")

    # PASO 7: Guardar injury report
    injury_report_file = f'injury_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
    with open(injury_report_file, 'w', encoding='utf-8') as f:
        f.write(f"NBA INJURY REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"{'='*80}\n\n")

        f.write(f"✅ DISPONIBLES ({len(results['available'])}):\n")
        for r in results['available']:
            f.write(f"   {r['player']} ({r['team']})\n")

        f.write(f"\n⚠️  CUESTIONABLES ({len(results['questionable'])}):\n")
        for r in results['questionable']:
            f.write(f"   {r['player']} ({r['team']}) - {r['details']}\n")

        f.write(f"\n❌ OUT ({len(results['out'])}):\n")
        for r in results['out']:
            f.write(f"   {r['player']} ({r['team']}) - {r['details']}\n")

    print(f"\n{'='*80}")
    print(f"📄 ARCHIVOS GENERADOS")
    print(f"{'='*80}\n")
    print(f"✅ Injury report: {injury_report_file}")
    if parlays_7:
        print(f"✅ Parlays de 7: parlays_verified_7leg_*.txt")
    if parlays_6:
        print(f"✅ Parlays de 6: parlays_verified_6leg_*.txt")

    print(f"\n{'='*80}")
    print(f"🎉 PROCESO COMPLETADO")
    print(f"{'='*80}\n")

    print(f"💡 PRÓXIMOS PASOS:")
    print(f"   1. Revisa los archivos generados")
    print(f"   2. Verifica jugadores cuestionables 1h antes")
    print(f"   3. Confirma líneas en FanDuel")
    print(f"   4. Apuesta responsablemente\n")


if __name__ == '__main__':
    main()
