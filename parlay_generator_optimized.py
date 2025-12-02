#!/usr/bin/env python3
"""
OPTIMIZED PARLAY GENERATOR
Genera múltiples tipos de parlays basados en FanDuel con probabilidades realistas
"""

from parlay_generator import ParlayGenerator, generate_mock_betting_data
from datetime import datetime


def main():
    """Función principal con múltiples estrategias"""
    print(f"\n{'='*80}")
    print(f"💰 OPTIMIZED PARLAY GENERATOR - MÚLTIPLES ESTRATEGIAS")
    print(f"{'='*80}\n")

    # Generar datos
    print("📊 Generando datos de ejemplo (FanDuel lines)...\n")
    all_bets = generate_mock_betting_data()

    # ========================================================================
    # ESTRATEGIA 1: Parlays de 7 jugadores con 75% probabilidad
    # ========================================================================
    print(f"\n{'─'*80}")
    print(f"🎯 ESTRATEGIA 1: Parlays de 7 jugadores (75% probabilidad)")
    print(f"{'─'*80}\n")

    gen1 = ParlayGenerator(min_confidence_stars=4, min_probability=0.75)
    high_conf_1 = gen1.filter_high_confidence_bets(all_bets)
    parlays_7 = gen1.generate_parlays(high_conf_1, parlay_size=7)

    if parlays_7:
        report_7 = gen1.format_parlay_report(parlays_7, max_parlays=5)
        print(report_7)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'parlays_7leg_75pct_{timestamp}.txt'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_7)
        print(f"✅ Guardado: {filename}\n")
    else:
        print("❌ No se encontraron parlays de 7 jugadores con 75% probabilidad\n")

    # ========================================================================
    # ESTRATEGIA 2: Parlays de 6 jugadores con 80% probabilidad
    # ========================================================================
    print(f"\n{'─'*80}")
    print(f"🎯 ESTRATEGIA 2: Parlays de 6 jugadores (80% probabilidad)")
    print(f"{'─'*80}\n")

    gen2 = ParlayGenerator(min_confidence_stars=4, min_probability=0.80)
    high_conf_2 = gen2.filter_high_confidence_bets(all_bets)
    parlays_6 = gen2.generate_parlays(high_conf_2, parlay_size=6)

    if parlays_6:
        report_6 = gen2.format_parlay_report(parlays_6, max_parlays=5)
        print(report_6)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'parlays_6leg_80pct_{timestamp}.txt'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_6)
        print(f"✅ Guardado: {filename}\n")

        # JSON export
        json_filename = f'parlays_6leg_80pct_{timestamp}.json'
        gen2.export_to_json(parlays_6, json_filename)
    else:
        print("❌ No se encontraron parlays de 6 jugadores con 80% probabilidad\n")

    # ========================================================================
    # ESTRATEGIA 3: Parlays de 5 jugadores con 85% probabilidad (CONSERVADOR)
    # ========================================================================
    print(f"\n{'─'*80}")
    print(f"🎯 ESTRATEGIA 3: Parlays de 5 jugadores (85% probabilidad - CONSERVADOR)")
    print(f"{'─'*80}\n")

    gen3 = ParlayGenerator(min_confidence_stars=5, min_probability=0.85)
    high_conf_3 = gen3.filter_high_confidence_bets(all_bets)
    parlays_5 = gen3.generate_parlays(high_conf_3, parlay_size=5)

    if parlays_5:
        report_5 = gen3.format_parlay_report(parlays_5, max_parlays=5)
        print(report_5)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'parlays_5leg_85pct_SAFE_{timestamp}.txt'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_5)
        print(f"✅ Guardado: {filename}\n")
    else:
        print("❌ No se encontraron parlays de 5 jugadores con 85% probabilidad\n")

    # ========================================================================
    # ESTRATEGIA 4: Parlays de 7 jugadores con 70% probabilidad (AGRESIVO)
    # ========================================================================
    print(f"\n{'─'*80}")
    print(f"🎯 ESTRATEGIA 4: Parlays de 7 jugadores (70% probabilidad - AGRESIVO)")
    print(f"{'─'*80}\n")

    gen4 = ParlayGenerator(min_confidence_stars=4, min_probability=0.70)
    high_conf_4 = gen4.filter_high_confidence_bets(all_bets)
    parlays_7_agg = gen4.generate_parlays(high_conf_4, parlay_size=7)

    if parlays_7_agg:
        report_7_agg = gen4.format_parlay_report(parlays_7_agg, max_parlays=10)
        print(report_7_agg)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'parlays_7leg_70pct_AGGRESSIVE_{timestamp}.txt'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_7_agg)
        print(f"✅ Guardado: {filename}\n")

        # JSON export
        json_filename = f'parlays_7leg_70pct_{timestamp}.json'
        gen4.export_to_json(parlays_7_agg, json_filename)
    else:
        print("❌ No se encontraron parlays de 7 jugadores con 70% probabilidad\n")

    # ========================================================================
    # RESUMEN FINAL
    # ========================================================================
    print(f"\n{'='*80}")
    print(f"📊 RESUMEN DE ESTRATEGIAS")
    print(f"{'='*80}\n")

    results = [
        ('7 jugadores @ 75%', len(parlays_7)),
        ('6 jugadores @ 80%', len(parlays_6)),
        ('5 jugadores @ 85% (SAFE)', len(parlays_5)),
        ('7 jugadores @ 70% (AGGRESSIVE)', len(parlays_7_agg))
    ]

    for strategy, count in results:
        status = '✅' if count > 0 else '❌'
        print(f"{status} {strategy}: {count} parlays encontrados")

    print(f"\n💡 RECOMENDACIÓN:")
    if parlays_6:
        print(f"   Enfócate en parlays de 6 jugadores con 80% probabilidad")
        print(f"   Balance óptimo entre riesgo/recompensa")
    elif parlays_7_agg:
        print(f"   Parlays de 7 jugadores están disponibles con 70% probabilidad")
        print(f"   Mayor riesgo pero mejor payout")
    elif parlays_5:
        print(f"   Juega conservador con parlays de 5 jugadores @ 85%")
        print(f"   Menor payout pero mayor seguridad")

    print(f"\n{'='*80}\n")


if __name__ == '__main__':
    main()
