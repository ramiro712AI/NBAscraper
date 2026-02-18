"""
model.py – NCAAB game prediction engine.

Algorithm
─────────
A) Power Rating Base
   Net = Adj_Off − Adj_Def   (KenPom-style net efficiency)
   Base_Margin = Net_A − Net_B

B) Contextual Adjustments
   + Home-court advantage  (+3.0 pts for home team; 0 for neutral site)
   + Four-Factors matchup  (shooting, turnovers, rebounding, free-throws)
   + Recent-form weighted  (last-10 record differential × 0.25, capped ±2)

C) Projected Margin = Base + all adjustments  (from Team-A perspective)

D) Win Probability (logistic function, k = 7.5)
   P(A wins) = 1 / (1 + exp(−margin / k))

Key factors driving each pick are extracted and returned for display.
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple

from .utils import get_logger

log = get_logger("model")

# ── Constants ────────────────────────────────────────────────────────────────
HOME_COURT_ADVANTAGE = 3.0   # points
K_LOGISTIC           = 7.5   # logistic scale factor (calibrated to NCAAB)
FORM_WEIGHT          = 0.25  # pts per game of L10-record differential
FORM_CAP             = 2.0   # max form adjustment in points
FF_EFG_COEFF         = 0.10  # pts per 1% eFG matchup edge
FF_TOV_COEFF         = 0.12  # pts per 1% TOV differential
FF_ORB_COEFF         = 0.06  # pts per 1% ORB differential
FF_FTR_COEFF         = 1.50  # pts per 0.01 FTR differential


# ── Helpers ───────────────────────────────────────────────────────────────────

def _net(stats: Dict) -> float:
    return stats["adj_off"] - stats["adj_def"]


def _logistic(margin: float, k: float = K_LOGISTIC) -> float:
    """Map projected margin (pts) → win probability [0, 1]."""
    return 1.0 / (1.0 + math.exp(-margin / k))


def _form_adjustment(a: Dict, b: Dict) -> Tuple[float, str]:
    """
    L10 record-based form adjustment from A's perspective.
    Returns (adjustment_pts, description_str).
    """
    a_pct = a["l10_w"] / max(a["l10_w"] + a["l10_l"], 1)
    b_pct = b["l10_w"] / max(b["l10_w"] + b["l10_l"], 1)
    raw   = (a_pct - b_pct) * 10 * FORM_WEIGHT   # scale to pts
    adj   = max(-FORM_CAP, min(FORM_CAP, raw))

    a_rec = f"{a['l10_w']}-{a['l10_l']}"
    b_rec = f"{b['l10_w']}-{b['l10_l']}"
    note  = (
        f"Form L10: {a_rec} vs {b_rec} → "
        f"{'A' if adj >= 0 else 'B'} +{abs(adj):.1f}pts"
    )
    return adj, note


def _four_factors_adjustment(a: Dict, b: Dict) -> Tuple[float, str]:
    """
    Matchup-based four-factors adjustment from A's perspective.
    Compares A's offensive profile vs B's defensive profile and vice-versa.
    """
    # eFG: A's offensive shooting vs B's defensive shooting allowed
    efg_edge  = (a["efg_off"] - b["efg_def"]) * FF_EFG_COEFF

    # TOV: lower turnover rate is better for the offense
    tov_edge  = (b["tov_pct"] - a["tov_pct"]) * FF_TOV_COEFF

    # ORB: A's offensive rebounding vs B's defensive rebounding
    orb_edge  = (a["orb_pct"] - (100 - b["orb_pct"])) * FF_ORB_COEFF

    # FTR: free-throw rate edge
    ftr_edge  = (a["ftr"] - b["ftr"]) * FF_FTR_COEFF * 10

    total = efg_edge + tov_edge + orb_edge + ftr_edge

    parts = []
    if abs(efg_edge) >= 0.3:
        parts.append(f"eFG {'+' if efg_edge>0 else ''}{efg_edge:.1f}pts")
    if abs(tov_edge) >= 0.2:
        parts.append(f"TOV {'+' if tov_edge>0 else ''}{tov_edge:.1f}pts")
    if abs(orb_edge) >= 0.2:
        parts.append(f"ORB {'+' if orb_edge>0 else ''}{orb_edge:.1f}pts")
    if abs(ftr_edge) >= 0.1:
        parts.append(f"FTR {'+' if ftr_edge>0 else ''}{ftr_edge:.1f}pts")

    note = "4-Factors: " + (", ".join(parts) if parts else "neutral")
    return total, note


def _margin_adjustment(a_margin: float, b_margin: float) -> Tuple[float, str]:
    """Recent scoring margin adjustment."""
    diff  = (a_margin - b_margin) * 0.10          # 10 % of margin gap
    adj   = max(-1.5, min(1.5, diff))
    note  = (
        f"Scoring-margin trend: {a_margin:+.1f} vs {b_margin:+.1f} "
        f"→ {adj:+.1f}pts"
    )
    return adj, note


# ── Core prediction ────────────────────────────────────────────────────────────

def predict_game(game: Dict, stats_a: Dict, stats_b: Dict) -> Dict:
    """
    Predict a single game.  Returns a result dict with full breakdown.

    Parameters
    ----------
    game    : game dict from schedule.py  (away = A, home = B by default,
              but we label them correctly inside this function)
    stats_a : team-stats dict for away team
    stats_b : team-stats dict for home team
    """
    away_abbr = game["away_abbr"]
    home_abbr = game["home_abbr"]
    neutral   = game.get("neutral_site", False)

    net_away = _net(stats_a)
    net_home = _net(stats_b)

    # ── Base margin (from AWAY team's perspective) ──────────────────────────
    base_margin = net_away - net_home

    # ── Home-court adjustment ───────────────────────────────────────────────
    if neutral:
        hca       = 0.0
        hca_note  = "Neutral site: no HCA"
    else:
        hca       = -HOME_COURT_ADVANTAGE    # negative for away team
        hca_note  = f"{home_abbr} home-court advantage: –{HOME_COURT_ADVANTAGE:.1f}pts"

    # ── Form adjustment ─────────────────────────────────────────────────────
    form_adj, form_note = _form_adjustment(stats_a, stats_b)

    # ── Four-factors matchup ─────────────────────────────────────────────────
    ff_adj, ff_note = _four_factors_adjustment(stats_a, stats_b)

    # ── Scoring-margin trend ─────────────────────────────────────────────────
    margin_adj, margin_note = _margin_adjustment(
        stats_a["l10_margin"], stats_b["l10_margin"]
    )

    # ── Total projected margin (from AWAY perspective) ──────────────────────
    proj_margin_away = base_margin + hca + form_adj + ff_adj + margin_adj

    # ── Determine favorite ───────────────────────────────────────────────────
    if proj_margin_away >= 0:
        fav_abbr  = away_abbr
        fav_name  = stats_a["full_name"]
        fav_stats = stats_a
        dog_abbr  = home_abbr
        dog_name  = stats_b["full_name"]
        proj_win_margin = proj_margin_away
    else:
        fav_abbr  = home_abbr
        fav_name  = stats_b["full_name"]
        fav_stats = stats_b
        dog_abbr  = away_abbr
        dog_name  = stats_a["full_name"]
        proj_win_margin = -proj_margin_away

    win_prob = _logistic(proj_win_margin)

    # ── Build key-factors list (5 factors) ───────────────────────────────────
    net_diff  = abs(net_away - net_home)
    fav_net   = _net(fav_stats)

    if proj_margin_away >= 0:
        fav_form_str = f"{stats_a['l10_w']}-{stats_a['l10_l']} L10"
        dog_form_str = f"{stats_b['l10_w']}-{stats_b['l10_l']} L10"
    else:
        fav_form_str = f"{stats_b['l10_w']}-{stats_b['l10_l']} L10"
        dog_form_str = f"{stats_a['l10_w']}-{stats_a['l10_l']} L10"

    fav_ranking = fav_stats.get("ranking", 0)
    ranking_str  = f"AP Ranked #{fav_ranking}" if fav_ranking else "Unranked"

    home_fav = (fav_abbr == home_abbr and not neutral)

    key_factors = [
        f"Net Efficiency edge: {net_diff:+.1f} pts/100 poss "
        f"({fav_name.split()[0]} Net {fav_net:+.1f})",
        f"{'Home court: +3.0pts' if home_fav else 'Road win projection'} "
        f"({'neutral site' if neutral else home_abbr + ' home' if home_fav else fav_abbr + ' away'})",
        f"Recent form: {fav_form_str} vs opp {dog_form_str} "
        f"(form adj {form_adj:+.1f}pts)",
        f"Four-factors matchup: eFG {fav_stats['efg_off']:.1f}% off / "
        f"{fav_stats['efg_def']:.1f}% def-allowed ({ff_note})",
        f"Scoring-margin trend: {fav_stats['l10_margin']:+.1f} pts/game L10",
    ]

    return {
        "game_id":         game["game_id"],
        "away_abbr":       away_abbr,
        "away_name":       stats_a["full_name"],
        "home_abbr":       home_abbr,
        "home_name":       stats_b["full_name"],
        "neutral_site":    neutral,
        "tip_time":        game["tip_time"],
        "broadcast":       game.get("broadcast", ""),
        "fav_abbr":        fav_abbr,
        "fav_name":        fav_name,
        "dog_abbr":        dog_abbr,
        "dog_name":        dog_name,
        "proj_margin":     round(proj_win_margin, 2),
        "win_prob":        round(win_prob * 100, 1),
        "net_away":        round(net_away, 2),
        "net_home":        round(net_home, 2),
        "fav_net":         round(fav_net, 2),
        "adj_off_fav":     fav_stats["adj_off"],
        "adj_def_fav":     fav_stats["adj_def"],
        "efg_off_fav":     fav_stats["efg_off"],
        "efg_def_fav":     fav_stats["efg_def"],
        "fav_l10":         fav_form_str,
        "fav_ranking":     fav_ranking,
        "fav_conf":        fav_stats.get("conference", ""),
        "key_factors":     key_factors,
        # Full breakdown
        "base_margin":     round(base_margin, 2),
        "hca":             round(hca, 2),
        "form_adj":        round(form_adj, 2),
        "ff_adj":          round(ff_adj, 2),
        "margin_adj":      round(margin_adj, 2),
        "notes": {
            "hca":    hca_note,
            "form":   form_note,
            "ff":     ff_note,
            "margin": margin_note,
        },
    }


# ── Batch prediction ─────────────────────────────────────────────────────────

def predict_all_games(
    games: List[Dict],
    all_stats: Dict[str, Dict],
) -> List[Dict]:
    """
    Run predictions for every game.  Returns list of result dicts,
    sorted by win_prob descending (highest-confidence favorite first).
    """
    results = []
    for game in games:
        away = game["away_abbr"]
        home = game["home_abbr"]

        if away not in all_stats or home not in all_stats:
            log.warning(f"Missing stats for {away} or {home} – skipping")
            continue

        try:
            result = predict_game(game, all_stats[away], all_stats[home])
            results.append(result)
        except Exception as exc:
            log.error(f"Prediction failed for {away}@{home}: {exc}")

    # Sort by confidence (highest probability first)
    results.sort(key=lambda r: r["win_prob"], reverse=True)
    return results
