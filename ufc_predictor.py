#!/usr/bin/env python3
"""
UFC 326 Fight Predictor
========================
Uses Claude API (claude-opus-4-6) with web search to analyze UFC 326 fights
and predict winners based on: record, ranking, momentum, age, finishing ability,
experience, injury history, and betting odds commentary.

Usage:
    python ufc_predictor.py
    ANTHROPIC_API_KEY=your_key python ufc_predictor.py
"""

import anthropic
import json
import os
import sys
from dataclasses import dataclass
from typing import Optional

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich import box
    from rich.progress import Progress, SpinnerColumn, TextColumn
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

# ─────────────────────────────────────────────────────────────────────────────
# Fighter data extracted from UFC 326 card screenshots
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Fighter:
    name: str
    record: str          # "W-L-D"
    wins: int
    losses: int
    draws: int
    nc: int              # No Contests
    age: Optional[int]
    ko_wins: Optional[int]
    sub_wins: Optional[int]
    dec_wins: Optional[int]
    ranking: Optional[str]
    recent_form: str     # last 3-5 fights summary


@dataclass
class Fight:
    card: str            # "Early Prelims" / "Prelims" / "Main Card"
    weight_class: str
    fighter_a: Fighter
    fighter_b: Fighter
    is_main_event: bool = False
    is_co_main: bool = False


UFC326_FIGHTS: list[Fight] = [
    # ── EARLY PRELIMS ─────────────────────────────────────────────────
    Fight(
        card="Early Prelims",
        weight_class="Flyweight",
        fighter_a=Fighter(
            name="Su Mudaerji",
            record="18-7-0", wins=18, losses=7, draws=0, nc=0,
            age=28, ko_wins=8, sub_wins=4, dec_wins=6,
            ranking="Unranked",
            recent_form="2W-2L last 4: beat Aori Qileng, lost to Tagir Ulanbekov, beat David Dvorak, lost to Manel Kape",
        ),
        fighter_b=Fighter(
            name="Jesus Aguilar",
            record="12-3-0", wins=12, losses=3, draws=0, nc=0,
            age=30, ko_wins=3, sub_wins=5, dec_wins=4,
            ranking="Unranked",
            recent_form="3W in a row: UFC debut wins, solid ground game",
        ),
    ),
    Fight(
        card="Early Prelims",
        weight_class="Light Heavyweight",
        fighter_a=Fighter(
            name="Rafael Tobias",
            record="14-1-0", wins=14, losses=1, draws=0, nc=0,
            age=29, ko_wins=9, sub_wins=3, dec_wins=2,
            ranking="Unranked",
            recent_form="4W streak, UFC debut, Brazilian prospect with heavy hands",
        ),
        fighter_b=Fighter(
            name="Diyar Nurgozhay",
            record="10-2-0", wins=10, losses=2, draws=0, nc=0,
            age=25, ko_wins=5, sub_wins=2, dec_wins=3,
            ranking="Unranked",
            recent_form="Mixed results in UFC, 1W-2L in last 3 UFC bouts",
        ),
    ),
    Fight(
        card="Early Prelims",
        weight_class="Light Heavyweight",
        fighter_a=Fighter(
            name="Luke Fernandez",
            record="6-0-0", wins=6, losses=0, draws=0, nc=0,
            age=26, ko_wins=3, sub_wins=2, dec_wins=1,
            ranking="Unranked",
            recent_form="Undefeated, UFC debut, Australian prospect",
        ),
        fighter_b=Fighter(
            name="Rodolfo Bellato",
            record="12-3-1, 1NC", wins=12, losses=3, draws=1, nc=1,
            age=29, ko_wins=6, sub_wins=4, dec_wins=2,
            ranking="Unranked",
            recent_form="3L in last 4 UFC fights, struggled with top competition",
        ),
    ),
    # ── PRELIMINARY CARD ──────────────────────────────────────────────
    Fight(
        card="Preliminary Card",
        weight_class="Bantamweight",
        fighter_a=Fighter(
            name="Cody Garbrandt",
            record="14-7-0", wins=14, losses=7, draws=0, nc=0,
            age=33, ko_wins=11, sub_wins=0, dec_wins=3,
            ranking="Unranked",
            recent_form="2W in a row after long layoff, former UFC BW champion, explosive striker",
        ),
        fighter_b=Fighter(
            name="Long Xiao",
            record="27-10-0", wins=27, losses=10, draws=0, nc=0,
            age=34, ko_wins=12, sub_wins=8, dec_wins=7,
            ranking="Unranked",
            recent_form="2L in a row in UFC, volume striker, durable",
        ),
    ),
    Fight(
        card="Preliminary Card",
        weight_class="Middleweight",
        fighter_a=Fighter(
            name="Donte Johnson",
            record="7-0-0", wins=7, losses=0, draws=0, nc=0,
            age=28, ko_wins=5, sub_wins=2, dec_wins=0,
            ranking="Unranked",
            recent_form="Undefeated, impressive finishes, UFC debut",
        ),
        fighter_b=Fighter(
            name="Cody Brundage",
            record="11-8-1, 1NC", wins=11, losses=8, draws=1, nc=1,
            age=30, ko_wins=7, sub_wins=3, dec_wins=1,
            ranking="Unranked",
            recent_form="1W-3L in last 4, struggling at UFC level",
        ),
    ),
    Fight(
        card="Preliminary Card",
        weight_class="Featherweight",
        fighter_a=Fighter(
            name="Ricky Turcios",
            record="13-5-0", wins=13, losses=5, draws=0, nc=0,
            age=28, ko_wins=4, sub_wins=4, dec_wins=5,
            ranking="Unranked",
            recent_form="2L in a row, needs a win badly, scrappy fighter",
        ),
        fighter_b=Fighter(
            name="Alberto Montes",
            record="11-1-0", wins=11, losses=1, draws=0, nc=0,
            age=27, ko_wins=5, sub_wins=3, dec_wins=3,
            ranking="Unranked",
            recent_form="3W in a row in UFC, rising prospect from Mexico",
        ),
    ),
    Fight(
        card="Preliminary Card",
        weight_class="Flyweight",
        fighter_a=Fighter(
            name="Cody Durden",
            record="17-9-1", wins=17, losses=9, draws=1, nc=0,
            age=30, ko_wins=7, sub_wins=5, dec_wins=5,
            ranking="Unranked",
            recent_form="2W-1L last 3, entertaining fighter, good cardio",
        ),
        fighter_b=Fighter(
            name="Nyamjargal Tumendemberel",
            record="9-1-0", wins=9, losses=1, draws=0, nc=0,
            age=25, ko_wins=2, sub_wins=3, dec_wins=4,
            ranking="Unranked",
            recent_form="UFC debut win, Mongolian prospect, active in Asian circuit",
        ),
    ),
    # ── MAIN CARD ─────────────────────────────────────────────────────
    Fight(
        card="Main Card",
        weight_class="Middleweight",
        fighter_a=Fighter(
            name="Gregory Rodrigues",
            record="18-6-0", wins=18, losses=6, draws=0, nc=0,
            age=33, ko_wins=12, sub_wins=4, dec_wins=2,
            ranking="Top 15",
            recent_form="2W in a row, explosive striker and BJJ black belt",
        ),
        fighter_b=Fighter(
            name="Brunno Ferreira",
            record="15-2-0", wins=15, losses=2, draws=0, nc=0,
            age=30, ko_wins=11, sub_wins=2, dec_wins=2,
            ranking="Unranked",
            recent_form="3W in a row in UFC, massive power, rising contender",
        ),
    ),
    Fight(
        card="Main Card",
        weight_class="Lightweight",
        fighter_a=Fighter(
            name="Drew Dober",
            record="28-15-0, 1NC", wins=28, losses=15, draws=0, nc=1,
            age=35, ko_wins=18, sub_wins=5, dec_wins=5,
            ranking="Unranked",
            recent_form="2L in a row, solid UFC veteran, heavy hands",
        ),
        fighter_b=Fighter(
            name="Michael Johnson",
            record="25-19-0", wins=25, losses=19, draws=0, nc=0,
            age=37, ko_wins=12, sub_wins=3, dec_wins=10,
            ranking="Unranked",
            recent_form="2L in a row, long UFC career, declining phase",
        ),
    ),
    Fight(
        card="Main Card",
        weight_class="Bantamweight",
        fighter_a=Fighter(
            name="Rob Font",
            record="22-9-0", wins=22, losses=9, draws=0, nc=0,
            age=36, ko_wins=10, sub_wins=3, dec_wins=9,
            ranking="Top 10",
            recent_form="2W in a row, former top contender, technical striker",
        ),
        fighter_b=Fighter(
            name="Raúl Rosas Jr.",
            record="11-1-0", wins=11, losses=1, draws=0, nc=0,
            age=20, ko_wins=2, sub_wins=7, dec_wins=2,
            ranking="Top 10",
            recent_form="3W in a row, youngest UFC champion contender, elite grappler, submission machine",
        ),
    ),
    Fight(
        card="Main Card",
        weight_class="Middleweight",
        is_co_main=True,
        fighter_a=Fighter(
            name="Caio Borralho",
            record="17-2-0, 1NC", wins=17, losses=2, draws=0, nc=1,
            age=31, ko_wins=5, sub_wins=8, dec_wins=4,
            ranking="#1 Contender",
            recent_form="5W in a row, dominant grappler, UFC MW title challenger, excellent cardio",
        ),
        fighter_b=Fighter(
            name="Reinier de Ridder",
            record="21-3-0", wins=21, losses=3, draws=0, nc=0,
            age=33, ko_wins=3, sub_wins=14, dec_wins=4,
            ranking="Top 5",
            recent_form="1W-2L last 3 UFC, former ONE champion, elite BJJ but struggled with UFC level",
        ),
    ),
    Fight(
        card="Main Card",
        weight_class="Lightweight",
        is_main_event=True,
        fighter_a=Fighter(
            name="Max Holloway",
            record="27-8-0", wins=27, losses=8, draws=0, nc=0,
            age=33, ko_wins=13, sub_wins=2, dec_wins=12,
            ranking="Former Champion / #2",
            recent_form="2W in a row including BMF title defense vs Gaethje, legendary volume striker, iron chin",
        ),
        fighter_b=Fighter(
            name="Charles Oliveira",
            record="36-11-0, 1NC", wins=36, losses=11, draws=0, nc=1,
            age=35, ko_wins=9, sub_wins=22, dec_wins=5,
            ranking="Former Champion / #1",
            recent_form="2L in a row (Islam Makhachev x2), former LW champion, most submission finishes in UFC history",
        ),
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# Claude-powered analysis
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Eres un experto analista de MMA y UFC con más de 15 años de experiencia.
Analizas peleas con datos estadísticos, conocimiento técnico de artes marciales mixtas,
tendencias de casas de apuestas, y comentarios de medios especializados como ESPN MMA,
MMA Fighting, Bloody Elbow y MMAjunkie.

Cuando analices una pelea debes:
1. Identificar al FAVORITO CLARO basándote en todos los factores disponibles.
2. Explicar con precisión técnica POR QUÉ el favorito ganará.
3. Explicar POR QUÉ el perdedor probable perderá, incluso si la pelea es pareja.
4. Dar un porcentaje de confianza en tu predicción (0-100%).
5. Indicar el método probable de victoria: KO/TKO, Submission, Decisión.
6. Siempre responder en formato JSON estrictamente válido."""


def build_fight_prompt(fight: Fight) -> str:
    fa = fight.fighter_a
    fb = fight.fighter_b

    def fmt(f: Fighter) -> str:
        return (
            f"Nombre: {f.name}\n"
            f"  Record: {f.record} (KOs: {f.ko_wins}, Subs: {f.sub_wins}, Decs: {f.dec_wins})\n"
            f"  Edad: {f.age} años\n"
            f"  Ranking: {f.ranking}\n"
            f"  Forma reciente: {f.recent_form}"
        )

    label = ""
    if fight.is_main_event:
        label = " [PELEA ESTELAR]"
    elif fight.is_co_main:
        label = " [CO-ESTELAR]"

    return f"""Analiza esta pelea de UFC 326{label}:

División: {fight.weight_class}
Cartelera: {fight.card}

PELEADOR A:
{fmt(fa)}

PELEADOR B:
{fmt(fb)}

Usa tu conocimiento de MMA, estadísticas históricas, estilo de pelea, momentum,
tendencias de apuestas y reportes de medios especializados.

Responde ÚNICAMENTE con JSON válido en este formato exacto:
{{
  "favorito": "nombre del favorito",
  "perdedor_probable": "nombre del perdedor probable",
  "confianza": 75,
  "metodo_victoria": "KO/TKO | Submission | Decisión",
  "cuota_estimada": "-150",
  "razon_favorito_gana": "Explicación detallada de 2-3 oraciones de por qué el favorito ganará",
  "razon_perdedor_pierde": "Explicación detallada de 2-3 oraciones de por qué el otro perderá",
  "pelea_apretada": true,
  "resumen_una_linea": "Una línea concisa resumiendo la predicción"
}}"""


def analyze_fight(client: anthropic.Anthropic, fight: Fight) -> dict:
    """Call Claude API with web search to analyze a single fight."""
    fa = fight.fighter_a
    fb = fight.fighter_b

    # Use web_search to get latest fighter info, then generate prediction
    messages = [
        {
            "role": "user",
            "content": (
                f"Busca información actualizada sobre {fa.name} vs {fb.name} UFC 326 "
                f"incluyendo cuotas de apuesta, historial reciente y cualquier noticia de lesiones. "
                f"Luego analiza la pelea y dame tu predicción.\n\n"
                + build_fight_prompt(fight)
            ),
        }
    ]

    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=1500,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        tools=[
            {"type": "web_search_20260209", "name": "web_search"},
        ],
        messages=messages,
    ) as stream:
        final = stream.get_final_message()

    # Extract the JSON text block
    for block in final.content:
        if hasattr(block, "type") and block.type == "text":
            text = block.text.strip()
            # Extract JSON from the response (may have surrounding text)
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
            # Fallback: return raw text
            return {"favorito": "N/A", "razon_favorito_gana": text, "confianza": 50}

    return {"favorito": "N/A", "razon_favorito_gana": "No se pudo analizar", "confianza": 50}


# ─────────────────────────────────────────────────────────────────────────────
# Output rendering
# ─────────────────────────────────────────────────────────────────────────────

def render_rich_table(fights: list[Fight], results: list[dict]) -> None:
    """Render a detailed Rich table with all predictions."""
    console = Console(width=160)

    console.print()
    console.print(Panel.fit(
        "[bold red]🥊  UFC 326 — PREDICTOR DE PELEAS  🥊[/bold red]\n"
        "[dim]Powered by Claude Opus 4.6 + Web Search • Fecha: 2026-03-07[/dim]",
        border_style="red",
    ))
    console.print()

    cards = ["Early Prelims", "Preliminary Card", "Main Card"]
    card_colors = {"Early Prelims": "cyan", "Preliminary Card": "yellow", "Main Card": "red"}

    for card in cards:
        card_fights = [(f, r) for f, r in zip(fights, results) if f.card == card]
        if not card_fights:
            continue

        color = card_colors.get(card, "white")
        console.print(Panel(f"[bold {color}]{card.upper()}[/bold {color}]", border_style=color))

        table = Table(
            box=box.ROUNDED,
            show_header=True,
            header_style="bold white on grey23",
            border_style="grey50",
            padding=(0, 1),
            expand=True,
        )

        table.add_column("División", style="cyan", width=14, no_wrap=True)
        table.add_column("Peleador A", style="white", width=18)
        table.add_column("Record A", style="dim white", width=10, justify="center")
        table.add_column("Peleador B", style="white", width=18)
        table.add_column("Record B", style="dim white", width=10, justify="center")
        table.add_column("⭐ FAVORITO", style="bold green", width=18)
        table.add_column("Confianza", width=10, justify="center")
        table.add_column("Método", style="yellow", width=12, justify="center")
        table.add_column("Cuota", style="magenta", width=8, justify="center")
        table.add_column("¿Apretada?", width=10, justify="center")
        table.add_column("Resumen", width=40)

        for fight, result in card_fights:
            fa = fight.fighter_a
            fb = fight.fighter_b
            favorito = result.get("favorito", "N/A")
            confianza = result.get("confianza", 50)
            metodo = result.get("metodo_victoria", "?")
            cuota = result.get("cuota_estimada", "?")
            apretada = "⚠️ Sí" if result.get("pelea_apretada", False) else "No"
            resumen = result.get("resumen_una_linea", "")

            # Color confidence
            if confianza >= 75:
                conf_text = f"[bold green]{confianza}%[/bold green]"
            elif confianza >= 60:
                conf_text = f"[yellow]{confianza}%[/yellow]"
            else:
                conf_text = f"[red]{confianza}%[/red]"

            # Highlight winner names
            name_a = f"[bold green]{fa.name}[/bold green]" if fa.name == favorito else fa.name
            name_b = f"[bold green]{fb.name}[/bold green]" if fb.name == favorito else fb.name

            label = ""
            if fight.is_main_event:
                label = " [bold red]★ MAIN[/bold red]"
            elif fight.is_co_main:
                label = " [bold yellow]★ CO[/bold yellow]"

            table.add_row(
                fight.weight_class + label,
                name_a,
                fa.record,
                name_b,
                fb.record,
                f"[bold green]{favorito}[/bold green]",
                conf_text,
                metodo,
                cuota,
                apretada,
                resumen,
            )

        console.print(table)
        console.print()

    # Detailed analysis panel per fight
    console.print(Panel("[bold white]ANÁLISIS DETALLADO POR PELEA[/bold white]", border_style="white"))
    console.print()

    for fight, result in zip(fights, results):
        fa = fight.fighter_a
        fb = fight.fighter_b
        favorito = result.get("favorito", "N/A")
        perdedor = result.get("perdedor_probable", "N/A")
        metodo = result.get("metodo_victoria", "?")
        confianza = result.get("confianza", 50)
        razon_gana = result.get("razon_favorito_gana", "")
        razon_pierde = result.get("razon_perdedor_pierde", "")

        label = ""
        if fight.is_main_event:
            label = " ★ PELEA ESTELAR"
        elif fight.is_co_main:
            label = " ★ CO-ESTELAR"

        title = f"[bold]{fa.name} vs {fb.name}[/bold]  |  {fight.weight_class}  |  {fight.card}{label}"
        body = (
            f"[bold green]FAVORITO:[/bold green] {favorito}  "
            f"[dim]({metodo} — {confianza}% confianza)[/dim]\n\n"
            f"[bold cyan]✅ Por qué {favorito} GANA:[/bold cyan]\n{razon_gana}\n\n"
            f"[bold red]❌ Por qué {perdedor} PIERDE:[/bold red]\n{razon_pierde}"
        )
        console.print(Panel(body, title=title, border_style="green" if confianza >= 70 else "yellow"))
        console.print()


def render_plain_table(fights: list[Fight], results: list[dict]) -> None:
    """Fallback plain-text table for environments without Rich."""
    print("\n" + "=" * 120)
    print("UFC 326 — PREDICTOR DE PELEAS | Claude Opus 4.6 + Web Search")
    print("=" * 120)

    header = f"{'División':<16} {'Pelea':<38} {'FAVORITO':<22} {'Conf':>5} {'Método':<14} {'¿Apretada?':<10}"
    print(header)
    print("-" * 120)

    for fight, result in zip(fights, results):
        fa = fight.fighter_a
        fb = fight.fighter_b
        matchup = f"{fa.name} vs {fb.name}"
        favorito = result.get("favorito", "N/A")
        conf = f"{result.get('confianza', 50)}%"
        metodo = result.get("metodo_victoria", "?")
        apretada = "Sí" if result.get("pelea_apretada", False) else "No"

        print(f"{fight.weight_class:<16} {matchup:<38} {favorito:<22} {conf:>5} {metodo:<14} {apretada:<10}")

    print("=" * 120)
    print()

    for fight, result in zip(fights, results):
        fa = fight.fighter_a
        fb = fight.fighter_b
        print(f"\n{'─'*80}")
        print(f"  {fa.name} vs {fb.name} | {fight.weight_class} | {fight.card}")
        print(f"  FAVORITO: {result.get('favorito','N/A')} ({result.get('confianza',50)}% — {result.get('metodo_victoria','?')})")
        print(f"  Por qué gana: {result.get('razon_favorito_gana','')}")
        print(f"  Por qué pierde {result.get('perdedor_probable','')}: {result.get('razon_perdedor_pierde','')}")

    print()


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set.")
        print("Usage: ANTHROPIC_API_KEY=your_key python ufc_predictor.py")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    fights = UFC326_FIGHTS
    results: list[dict] = []

    if HAS_RICH:
        console = Console()
        console.print(
            f"\n[bold yellow]Analizando {len(fights)} peleas de UFC 326 con Claude Opus 4.6...[/bold yellow]\n"
        )
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            for fight in fights:
                fa = fight.fighter_a
                fb = fight.fighter_b
                label = ""
                if fight.is_main_event:
                    label = " [ESTELAR]"
                elif fight.is_co_main:
                    label = " [CO-ESTELAR]"
                task = progress.add_task(
                    f"🥊 {fa.name} vs {fb.name}{label}...", total=None
                )
                result = analyze_fight(client, fight)
                results.append(result)
                progress.update(task, description=f"✅ {fa.name} vs {fb.name} — {result.get('favorito','?')}")
                progress.stop_task(task)
    else:
        print(f"\nAnalizando {len(fights)} peleas de UFC 326...")
        for fight in fights:
            fa = fight.fighter_a
            fb = fight.fighter_b
            print(f"  Analizando: {fa.name} vs {fb.name}...")
            result = analyze_fight(client, fight)
            results.append(result)
            print(f"  → Favorito: {result.get('favorito','?')} ({result.get('confianza',50)}%)")

    # Render output
    if HAS_RICH:
        render_rich_table(fights, results)
    else:
        render_plain_table(fights, results)

    # Save results to JSON
    output = []
    for fight, result in zip(fights, results):
        output.append({
            "card": fight.card,
            "weight_class": fight.weight_class,
            "fighter_a": fight.fighter_a.name,
            "fighter_b": fight.fighter_b.name,
            "is_main_event": fight.is_main_event,
            "is_co_main": fight.is_co_main,
            **result,
        })

    out_file = "ufc326_predictions.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    if HAS_RICH:
        Console().print(f"\n[dim]Predicciones guardadas en [bold]{out_file}[/bold][/dim]\n")
    else:
        print(f"\nPredicciones guardadas en {out_file}\n")


if __name__ == "__main__":
    main()
