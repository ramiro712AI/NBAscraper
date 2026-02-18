"""
output.py – Format and save prediction results.

Produces:
  1. Terminal table of all games
  2. FINAL RANKING section  (#1 … #N, descending by confidence)
  3. CSV  →  outputs/ncaab_picks_YYYYMMDD.csv
  4. JSON →  outputs/ncaab_picks_YYYYMMDD.json
"""

from __future__ import annotations

import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from .utils import get_logger

log = get_logger("output")

OUTPUTS_DIR = Path(__file__).parent.parent / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# Column widths for terminal display
_COL = {
    "rank":     4,
    "fav":     28,
    "opp":     28,
    "prob":     8,
    "margin":   9,
}

def _hr(char="─", width=90):
    return char * width


def _rank_badge(rank: int) -> str:
    if rank:
        return f"AP#{rank}"
    return "     "


def _format_time(iso: str) -> str:
    """Convert ISO UTC → ET display string."""
    try:
        from datetime import timezone, timedelta
        dt = datetime.strptime(iso, "%Y-%m-%dT%H:%MZ")
        et = dt.replace(tzinfo=timezone.utc).astimezone(
            timezone(timedelta(hours=-5))
        )
        return et.strftime("%I:%M %p ET")
    except Exception:
        return iso


def print_games_table(results: List[Dict]) -> None:
    """Print a compact table of all games (sorted by tip time)."""
    # Sort by game tip time for table display
    sorted_by_time = sorted(results, key=lambda r: r["tip_time"])

    print()
    print(_hr("═"))
    print(f"  NCAAB GAME PREDICTIONS  –  {datetime.now().strftime('%A, %B %d, %Y')}")
    print(_hr("═"))
    header = (
        f"  {'#':>3}  {'Away':25} {'Home':25} "
        f"{'Favorite':25} {'Prob':>7} {'Margin':>8}  Broadcast"
    )
    print(header)
    print(_hr("─"))

    for i, r in enumerate(sorted_by_time, 1):
        away_str = f"{r['away_name'].split()[-1]:25}"
        home_str = f"{r['home_name'].split()[-1]:25}"

        fav_tag  = "(H)" if r["fav_abbr"] == r["home_abbr"] else "(A)"
        fav_str  = f"{r['fav_name'].split()[-1]} {fav_tag}"

        rank_str = f"#{r['fav_ranking']}" if r["fav_ranking"] else ""
        prob_str = f"{r['win_prob']:.1f}%"
        marg_str = f"+{r['proj_margin']:.1f}"
        bc       = r.get("broadcast", "")

        print(
            f"  {i:>3}. {away_str} {home_str} "
            f"  {rank_str:>5} {fav_str:22} {prob_str:>7} {marg_str:>7}  {bc}"
        )

    print(_hr("─"))
    print(f"  Total: {len(results)} games predicted")
    print(_hr("═"))


def print_final_ranking(results: List[Dict]) -> None:
    """
    Print the flagship FINAL RANKING section.
    Results must already be sorted by win_prob descending.
    """
    print()
    print()
    print("=" * 90)
    print("   ★  FINAL RANKING – TOP FAVORITES TODAY  ★")
    print("   Ordered strictly by win probability (highest → lowest)")
    print("=" * 90)
    print()
    print(
        f"  {'#':>3}  {'Favorite':28} {'vs Opponent':28} "
        f"{'Prob':>7}  {'Margin':>7}  {'Conference'}"
    )
    print(_hr("─"))

    for rank, r in enumerate(results, 1):
        badge = f"[AP#{r['fav_ranking']}]" if r["fav_ranking"] else "       "
        fav   = f"{badge} {r['fav_name']}"[:28]
        opp   = f"vs {r['dog_name']}"[:28]
        prob  = f"{r['win_prob']:.1f}%"
        marg  = f"+{r['proj_margin']:.1f}"
        conf  = r.get("fav_conf", "")

        print(f"  #{rank:<3} {fav:<28} {opp:<28} {prob:>7}  {marg:>7}  {conf}")

    print(_hr("─"))
    print()

    # Detailed entries
    print("=" * 90)
    print("   DETAILED BREAKDOWN  (top 58, with key factors)")
    print("=" * 90)

    for rank, r in enumerate(results, 1):
        badge   = f"[AP #{r['fav_ranking']}]" if r["fav_ranking"] else ""
        loc     = "(H)" if r["fav_abbr"] == r["home_abbr"] else "(A)"
        header  = (
            f"\n  #{rank:>2}  {badge} {r['fav_name']} {loc}  –  "
            f"{r['win_prob']:.1f}%  –  Proj Margin +{r['proj_margin']:.1f}"
        )
        print(header)

        opp_str = (
            f"       vs {'[AP #' + str(r['dog_ranking']) + '] ' if r.get('dog_ranking', 0) else ''}"
            f"{r['dog_name']}"
            if False  # simplify – just show
            else f"       vs {r['dog_name']}"
        )
        print(opp_str)

        game_info = (
            f"       {r.get('tip_time','')[:10]}  |  "
            f"{_format_time(r.get('tip_time',''))}  |  {r.get('broadcast','')}"
        )
        print(game_info)

        print(f"       Adj Off: {r['adj_off_fav']:.1f}  |  "
              f"Adj Def: {r['adj_def_fav']:.1f}  |  "
              f"Net: {r['fav_net']:+.1f}  |  "
              f"eFG Off/Def: {r['efg_off_fav']:.1f}% / {r['efg_def_fav']:.1f}%")

        print("       Key factors:")
        for j, factor in enumerate(r.get("key_factors", []), 1):
            print(f"         {j}. {factor}")

    print()
    print("=" * 90)
    print(f"  Pipeline run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 90)


def save_csv(results: List[Dict], date_str: str) -> Path:
    """Save results to CSV. Returns file path."""
    path = OUTPUTS_DIR / f"ncaab_picks_{date_str}.csv"

    fieldnames = [
        "rank", "fav_abbr", "fav_name", "fav_ranking", "fav_conf",
        "dog_abbr", "dog_name",
        "win_prob", "proj_margin",
        "adj_off_fav", "adj_def_fav", "fav_net",
        "efg_off_fav", "efg_def_fav",
        "fav_l10", "base_margin", "hca", "form_adj", "ff_adj",
        "away_abbr", "home_abbr", "neutral_site",
        "tip_time", "broadcast",
        "key_factor_1", "key_factor_2", "key_factor_3",
        "key_factor_4", "key_factor_5",
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for rank, r in enumerate(results, 1):
            kf = r.get("key_factors", [])
            row = {**r, "rank": rank}
            for i in range(5):
                row[f"key_factor_{i+1}"] = kf[i] if i < len(kf) else ""
            writer.writerow(row)

    log.info(f"CSV saved → {path}")
    return path


def save_json(results: List[Dict], date_str: str) -> Path:
    """Save results to JSON. Returns file path."""
    path = OUTPUTS_DIR / f"ncaab_picks_{date_str}.json"

    payload = {
        "generated_at": datetime.now().isoformat(),
        "date": date_str,
        "total_games": len(results),
        "picks": [
            {
                "rank": rank,
                **{k: v for k, v in r.items()},
            }
            for rank, r in enumerate(results, 1)
        ],
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    log.info(f"JSON saved → {path}")
    return path


def run_output(results: List[Dict], date_str: str) -> None:
    """Main entry: print all output and save files."""
    print_games_table(results)
    print_final_ranking(results)
    csv_path  = save_csv(results, date_str)
    json_path = save_json(results, date_str)
    print(f"\n  Saved: {csv_path}")
    print(f"  Saved: {json_path}\n")
