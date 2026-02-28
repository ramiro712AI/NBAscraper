"""
MLB SPRING TRAINING PREDICTION ENGINE – SCRIPT QUIRÚRGICO PROFESIONAL
=======================================================================
Sábado 28-Feb-2026  │  16 partidos de Spring Training

DIFERENCIAS CLAVE vs NBA:
  ★ El PITCHEO es el factor dominante en béisbol (30% del modelo)
  ★ "Motivación" = ambición contendiente 2026, no playoffs inmediatos
  ★ ST = pretemporada exhibition → resultados más volátiles
  ★ Split-squad: LAD y TOR juegan 2 equipos simultáneamente (normal en ST)
  ★ Rendimiento de jugadores = stats 2024/2025 + proyección 2026

Capas del modelo:
  Layer 1 → Matchup de abridores (ERA, K%, calidad del brazo)  30%
  Layer 2 → Fortaleza del roster / proyección 2026              25%
  Layer 3 → Forma reciente en Spring Training 2026              15%
  Layer 4 → H2H histórico (temporada regular 2024-2025)         10%
  Layer 5 → Ambición contendiente para 2026                     10%
  Layer 6 → Ventaja de local                                     5%
  Layer 7 → Profundidad del bullpen                              5%
"""

from datetime import date

# ════════════════════════════════════════════════════════════════════════════
# 16 PARTIDOS HOY – 28-Feb-2026 (Spring Training)
# ════════════════════════════════════════════════════════════════════════════
TODAY_GAMES = [
    {"away": "ATL",  "home": "BAL",  "time": "1:05 PM",
     "p_away": "Spencer Strider",      "p_home": "Kyle Bradish"},
    {"away": "MIN",  "home": "BOS",  "time": "1:05 PM",
     "p_away": "Taj Bradley",          "p_home": "Sonny Gray"},
    {"away": "PIT",  "home": "HOU",  "time": "1:05 PM",
     "p_away": "Graham Ashcraft",      "p_home": "Mike Biers"},
    {"away": "TOR",  "home": "NYY",  "time": "1:05 PM",
     "p_away": "Jose Berrios",         "p_home": "Paul Blackburn"},
    {"away": "DET",  "home": "TB",   "time": "1:05 PM",
     "p_away": "Drew Anderson",        "p_home": "Nick Martinez"},
    {"away": "PHI",  "home": "TOR2", "time": "1:07 PM",   # TOR split-squad B
     "p_away": "Cristopher Sanchez",   "p_home": "Dylan Cease"},
    {"away": "STL",  "home": "MIA",  "time": "1:10 PM",
     "p_away": "Michael McGreevy",     "p_home": "Eury Perez"},
    {"away": "WSH",  "home": "NYM",  "time": "1:10 PM",
     "p_away": "Jake Irvin",           "p_home": "Tobias Myers"},
    {"away": "SF",   "home": "ATH",  "time": "3:05 PM",
     "p_away": "Tyler Mahle",          "p_home": "Luis Morales"},
    {"away": "CHW",  "home": "CLE",  "time": "3:05 PM",
     "p_away": "Shane Smith",          "p_home": "Tanner Bibee"},
    {"away": "CHC",  "home": "LAD",  "time": "3:05 PM",
     "p_away": "Colin Rea",            "p_home": "Justin Wrobleski"},
    {"away": "LAD2", "home": "TEX",  "time": "3:05 PM",   # LAD split-squad B
     "p_away": "Jackson Ferris",       "p_home": "Jack Leiter"},
    {"away": "KC",   "home": "COL",  "time": "3:10 PM",
     "p_away": "Seth Lugo",            "p_home": "Michael Lorenzo"},
    {"away": "ARI",  "home": "LAA",  "time": "3:10 PM",
     "p_away": "Mitch Bratt",          "p_home": "Alek Manoah"},
    {"away": "CIN",  "home": "MIL",  "time": "3:10 PM",
     "p_away": "Hunter Greene",        "p_home": "Rob Zastryzny"},
    {"away": "SEA",  "home": "SD",   "time": "3:10 PM",
     "p_away": "Kade Anderson",        "p_home": "JP Sears"},
]

TEAM_NAMES = {
    "ATL": "Atlanta Braves",         "BAL": "Baltimore Orioles",
    "BOS": "Boston Red Sox",         "CHC": "Chicago Cubs",
    "CHW": "Chicago White Sox",      "CIN": "Cincinnati Reds",
    "CLE": "Cleveland Guardians",    "COL": "Colorado Rockies",
    "DET": "Detroit Tigers",         "HOU": "Houston Astros",
    "KC":  "Kansas City Royals",     "LAA": "Los Angeles Angels",
    "LAD": "LA Dodgers (A)",         "LAD2":"LA Dodgers (B)",
    "MIA": "Miami Marlins",          "MIL": "Milwaukee Brewers",
    "MIN": "Minnesota Twins",        "NYM": "New York Mets",
    "NYY": "New York Yankees",       "PHI": "Philadelphia Phillies",
    "PIT": "Pittsburgh Pirates",     "SD":  "San Diego Padres",
    "SEA": "Seattle Mariners",       "SF":  "San Francisco Giants",
    "STL": "St. Louis Cardinals",    "TB":  "Tampa Bay Rays",
    "TEX": "Texas Rangers",          "TOR": "Toronto Blue Jays (A)",
    "TOR2":"Toronto Blue Jays (B)",  "WSH": "Washington Nationals",
    "ATH": "Oakland Athletics",
}

# ════════════════════════════════════════════════════════════════════════════
# LAYER 1 – CALIDAD DEL ABRIDOR (0.0 – 1.0)
# Base: ERA, K%, porcentaje ganados 2024-2025, historial lesiones
# ════════════════════════════════════════════════════════════════════════════
PITCHER_RATING = {
    # Élite (0.85-1.0)
    "Spencer Strider":      0.88,  # 2.30 ERA pre-TJ; regresa 2026 (óxido esperable)
    "Sonny Gray":           0.87,  # 2.79 ERA 2024 STL, 14-8, firmó con BOS
    "Seth Lugo":            0.86,  # 3.59 ERA 2024 KC, ace del equipo
    "Hunter Greene":        0.85,  # 3.87 ERA 2024 CIN, 198K, ace joven de élite
    # Muy bueno (0.72-0.84)
    "Dylan Cease":          0.82,  # 2.97 ERA 2024 SD, transferido a TOR
    "Tanner Bibee":         0.80,  # 3.47 ERA 2024 CLE, 141K, joven fiable
    "Tobias Myers":         0.79,  # 3.64 ERA 2024 TB, revelación; ahora NYM
    "Kyle Bradish":         0.76,  # 2.83 ERA pre-TJ; regresa 2026
    "Jose Berrios":         0.76,  # 3.64 ERA 2024 TOR, 14-9, veterano sólido
    "Taj Bradley":          0.74,  # 3.25 ERA 2024, joven con proyección
    # Sólido (0.60-0.71)
    "Cristopher Sanchez":   0.70,  # 3.82 ERA 2024 PHI, 32 aperturas
    "Mike Biers":           0.69,  # HOU sólido, stats ~3.90 ERA
    "Eury Perez":           0.65,  # Regresa de TJ; altísimo techo, forma incierta
    "Jake Irvin":           0.65,  # 4.00 ERA 2024 WSH, fiable pero no élite
    "Jackson Ferris":       0.65,  # Prospecto élite LAD; debut esperado 2026
    "Tyler Mahle":          0.63,  # Regresa de lesiones; fue 3.18 ERA 2022
    "Nick Martinez":        0.62,  # 4.55 ERA 2024 SD; ahora TB
    "Michael McGreevy":     0.62,  # STL, 3.72 ERA parcial 2024
    "Graham Ashcraft":      0.60,  # 4.31 ERA 2024 CIN; ahora PIT
    "Justin Wrobleski":     0.59,  # LAD prospecto, debut MLB 2024
    # Por debajo del promedio (0.40-0.59)
    "Colin Rea":            0.57,  # 4.52 ERA 2024 MIL; veterano
    "JP Sears":             0.56,  # 4.62 ERA 2024 OAK; ahora SD
    "Mitch Bratt":          0.55,  # ARI prospecto, buen potencial
    "Kade Anderson":        0.54,  # SEA prospecto joven
    "Paul Blackburn":       0.52,  # 4.82 ERA 2024; journeyman NYY
    "Drew Anderson":        0.48,  # DET, datos limitados
    "Michael Lorenzo":      0.46,  # COL pitcher; datos limitados
    "Luis Morales":         0.45,  # ATH prospecto
    "Shane Smith":          0.43,  # CHW rebuild; datos limitados
    "Jack Leiter":          0.42,  # 6.08 ERA 2023 TEX debut; mejorando
    "Alek Manoah":          0.38,  # 2.24 ERA 2022, pero colapso 2023-2024; comeback
    "Rob Zastryzny":        0.38,  # Relevista/spot-starter MIL; no es abridor real
}

# ════════════════════════════════════════════════════════════════════════════
# LAYER 2 – FORTALEZA DEL ROSTER (0.0 – 1.0)
# Base: record 2025 reg season + offseason moves 2025-26
# ════════════════════════════════════════════════════════════════════════════
TEAM_STRENGTH = {
    "LAD":  0.97,  "LAD2": 0.97,  # Mejor franquicia actual
    "NYY":  0.92,
    "ATL":  0.88,
    "HOU":  0.88,
    "PHI":  0.85,
    "CLE":  0.83,
    "NYM":  0.82,
    "BOS":  0.79,
    "BAL":  0.79,
    "SD":   0.78,
    "MIL":  0.76,
    "SEA":  0.75,
    "MIN":  0.74,
    "TB":   0.73,
    "KC":   0.73,
    "ARI":  0.72,
    "TEX":  0.71,
    "CIN":  0.68,
    "TOR":  0.68,  "TOR2": 0.68,
    "STL":  0.66,
    "DET":  0.66,
    "MIA":  0.65,
    "SF":   0.63,
    "CHC":  0.62,
    "ATH":  0.58,
    "PIT":  0.57,
    "WSH":  0.55,
    "LAA":  0.52,
    "COL":  0.40,
    "CHW":  0.30,   # Peor equipo de MLB 2024, full rebuild
}

# ════════════════════════════════════════════════════════════════════════════
# LAYER 3 – FORMA EN SPRING TRAINING 2026 (al 28-Feb)
# (w, l, run_diff_avg, streak >0=win <0=lose)
# ════════════════════════════════════════════════════════════════════════════
ST_FORM = {
    "ATL":  {"w": 2, "l": 1, "diff": +1.3, "streak":  2},
    "BAL":  {"w": 1, "l": 2, "diff": -0.7, "streak": -1},
    "MIN":  {"w": 2, "l": 1, "diff": +0.7, "streak":  1},
    "BOS":  {"w": 2, "l": 1, "diff": +1.0, "streak":  1},
    "PIT":  {"w": 1, "l": 2, "diff": -1.1, "streak": -1},
    "HOU":  {"w": 2, "l": 1, "diff": +0.9, "streak":  2},
    "TOR":  {"w": 1, "l": 1, "diff": +0.0, "streak": -1},
    "TOR2": {"w": 1, "l": 1, "diff": +0.0, "streak":  1},
    "NYY":  {"w": 2, "l": 1, "diff": +1.4, "streak":  2},
    "DET":  {"w": 1, "l": 2, "diff": -0.8, "streak": -1},
    "TB":   {"w": 2, "l": 1, "diff": +0.6, "streak":  1},
    "PHI":  {"w": 2, "l": 1, "diff": +1.2, "streak":  2},
    "STL":  {"w": 1, "l": 2, "diff": -0.4, "streak": -1},
    "MIA":  {"w": 2, "l": 1, "diff": +0.5, "streak":  1},
    "WSH":  {"w": 1, "l": 2, "diff": -1.9, "streak": -2},
    "NYM":  {"w": 3, "l": 0, "diff": +2.1, "streak":  3},
    "SF":   {"w": 1, "l": 2, "diff": -0.3, "streak": -1},
    "ATH":  {"w": 1, "l": 2, "diff": -0.6, "streak": -1},
    "CHW":  {"w": 0, "l": 3, "diff": -3.4, "streak": -3},
    "CLE":  {"w": 3, "l": 0, "diff": +2.8, "streak":  3},
    "CHC":  {"w": 1, "l": 2, "diff": -0.9, "streak": -1},
    "LAD":  {"w": 3, "l": 0, "diff": +3.1, "streak":  3},
    "LAD2": {"w": 3, "l": 0, "diff": +3.1, "streak":  3},
    "TEX":  {"w": 1, "l": 2, "diff": -0.7, "streak": -1},
    "KC":   {"w": 2, "l": 1, "diff": +1.1, "streak":  2},
    "COL":  {"w": 0, "l": 3, "diff": -2.9, "streak": -3},
    "ARI":  {"w": 2, "l": 1, "diff": +0.8, "streak":  1},
    "LAA":  {"w": 1, "l": 2, "diff": -1.2, "streak": -1},
    "CIN":  {"w": 2, "l": 1, "diff": +0.9, "streak":  2},
    "MIL":  {"w": 1, "l": 2, "diff": -0.3, "streak": -1},
    "SEA":  {"w": 2, "l": 1, "diff": +0.6, "streak":  1},
    "SD":   {"w": 2, "l": 1, "diff": +0.7, "streak":  1},
}

# ════════════════════════════════════════════════════════════════════════════
# LAYER 4 – HEAD-TO-HEAD TEMPORADA REGULAR 2025
# H2H[local][visitante] = (wins_local, wins_visitor, total)
# ════════════════════════════════════════════════════════════════════════════
H2H = {
    "BAL":  {"ATL":  (4, 3, 7)},
    "BOS":  {"MIN":  (5, 3, 8)},
    "HOU":  {"PIT":  (6, 1, 7)},
    "NYY":  {"TOR":  (11, 8, 19)},
    "TB":   {"DET":  (5, 2, 7)},
    "TOR2": {"PHI":  (3, 4, 7)},  # PHI tiene ligera ventaja histórica
    "MIA":  {"STL":  (4, 3, 7)},
    "NYM":  {"WSH":  (14, 5, 19)},
    "ATH":  {"SF":   (3, 4, 7)},   # SF gana más en este H2H
    "CLE":  {"CHW":  (16, 3, 19)},
    "LAD":  {"CHC":  (5, 2, 7)},
    "TEX":  {"LAD2": (3, 4, 7)},   # LAD gana más
    "COL":  {"KC":   (2, 5, 7)},
    "LAA":  {"ARI":  (3, 4, 7)},
    "MIL":  {"CIN":  (9, 10, 19)}, # CIN ligerísima ventaja
    "SD":   {"SEA":  (4, 3, 7)},
}

# ════════════════════════════════════════════════════════════════════════════
# LAYER 5 – AMBICIÓN CONTENDIENTE 2026
# 1.0 = máx (campeón favorito), 0.2 = rebuild/tanking
# ════════════════════════════════════════════════════════════════════════════
CONTENDER_MOTIVATION = {
    "LAD":  0.97,  "LAD2": 0.97,
    "NYY":  0.93,
    "ATL":  0.91,
    "HOU":  0.90,
    "PHI":  0.89,
    "CLE":  0.87,
    "NYM":  0.88,
    "BOS":  0.84,
    "BAL":  0.85,
    "SD":   0.82,
    "MIL":  0.80,
    "SEA":  0.79,
    "KC":   0.78,
    "MIN":  0.77,
    "TB":   0.76,
    "ARI":  0.78,
    "TEX":  0.74,
    "CIN":  0.74,
    "TOR":  0.72,  "TOR2": 0.72,
    "DET":  0.70,
    "STL":  0.68,
    "MIA":  0.67,
    "SF":   0.65,
    "CHC":  0.66,
    "ATH":  0.55,
    "PIT":  0.55,
    "WSH":  0.52,
    "LAA":  0.48,
    "COL":  0.35,
    "CHW":  0.22,
}

# ════════════════════════════════════════════════════════════════════════════
# LAYER 7 – PROFUNDIDAD DEL BULLPEN (0.0-1.0)
# ════════════════════════════════════════════════════════════════════════════
BULLPEN_DEPTH = {
    "LAD":  0.96,  "LAD2": 0.96,
    "NYY":  0.90,
    "HOU":  0.89,
    "ATL":  0.87,
    "PHI":  0.85,
    "CLE":  0.85,
    "NYM":  0.83,
    "SD":   0.82,
    "BAL":  0.81,
    "BOS":  0.80,
    "MIL":  0.80,
    "TB":   0.80,
    "SEA":  0.78,
    "MIN":  0.76,
    "KC":   0.76,
    "ARI":  0.75,
    "TOR":  0.74,  "TOR2": 0.74,
    "TEX":  0.73,
    "STL":  0.72,
    "CIN":  0.70,
    "DET":  0.69,
    "MIA":  0.68,
    "SF":   0.67,
    "CHC":  0.66,
    "ATH":  0.60,
    "PIT":  0.60,
    "WSH":  0.58,
    "LAA":  0.54,
    "COL":  0.42,
    "CHW":  0.32,
}

# ════════════════════════════════════════════════════════════════════════════
# PESOS DEL MODELO MLB
# ════════════════════════════════════════════════════════════════════════════
W_PITCHER   = 0.30
W_ROSTER    = 0.25
W_ST_FORM   = 0.15
W_H2H       = 0.10
W_CONTENDER = 0.10
W_HOME      = 0.05
W_BULLPEN   = 0.05

# ════════════════════════════════════════════════════════════════════════════
# ENGINE DE SCORING
# ════════════════════════════════════════════════════════════════════════════
def score_team(abbr, pitcher_name, is_home, opponent):
    notes = []
    score = 0.0

    # 1. ABRIDOR
    p_rating = PITCHER_RATING.get(pitcher_name, 0.55)
    score += W_PITCHER * p_rating
    notes.append(
        f"Abridor: {pitcher_name} "
        f"(rating {p_rating:.2f}/1.0)"
    )

    # 2. ROSTER
    r_val = TEAM_STRENGTH.get(abbr, 0.60)
    score += W_ROSTER * r_val
    notes.append(f"Fortaleza roster: {r_val:.2f}/1.0")

    # 3. FORMA EN ST
    form = ST_FORM.get(abbr, {"w": 1, "l": 1, "diff": 0, "streak": 0})
    total_g = form["w"] + form["l"]
    wp = form["w"] / total_g if total_g else 0.5
    score += W_ST_FORM * wp
    streak_str = (f"W{form['streak']}" if form["streak"] > 0
                  else f"L{abs(form['streak'])}" if form["streak"] < 0 else "—")
    notes.append(
        f"Forma ST 2026: {form['w']}-{form['l']} ({wp:.0%}) | "
        f"Run diff: {form['diff']:+.1f} | Racha: {streak_str}"
    )

    # 4. H2H
    if is_home:
        h2h_raw = H2H.get(abbr, {}).get(opponent, None)
        if h2h_raw:
            h_w, a_w, tot = h2h_raw
            h2h_wp = h_w / tot
            notes.append(
                f"H2H LOCAL 2025: {h_w}V-{a_w}D ({tot} juegos)"
            )
        else:
            h2h_wp = 0.5
            notes.append("H2H: sin datos → neutral")
    else:
        h2h_raw = H2H.get(opponent, {}).get(abbr, None)
        if h2h_raw:
            h_w, a_w, tot = h2h_raw
            h2h_wp = a_w / tot
            notes.append(
                f"H2H VISITANTE 2025: {a_w}V-{h_w}D ({tot} juegos)"
            )
        else:
            h2h_wp = 0.5
            notes.append("H2H: sin datos → neutral")
    score += W_H2H * h2h_wp

    # 5. MOTIVACIÓN CONTENDIENTE
    cm = CONTENDER_MOTIVATION.get(abbr, 0.60)
    score += W_CONTENDER * cm
    if cm >= 0.88:
        mot = "Favorito al título / World Series"
    elif cm >= 0.75:
        mot = "Contendiente playoffs"
    elif cm >= 0.60:
        mot = "Esperanzas de playoffs"
    else:
        mot = "Rebuild / desarrollo prospectos"
    notes.append(f"Ambición 2026: {mot} ({cm:.0%})")

    # 6. VENTAJA LOCAL
    if is_home:
        score += W_HOME * 1.0
        notes.append("Juega en CASA (+5%)")
    else:
        notes.append("Juega de VISITANTE")

    # 7. BULLPEN
    bp = BULLPEN_DEPTH.get(abbr, 0.60)
    score += W_BULLPEN * bp
    notes.append(f"Bullpen depth: {bp:.2f}/1.0")

    return round(score, 4), notes


# ════════════════════════════════════════════════════════════════════════════
# OUTPUT
# ════════════════════════════════════════════════════════════════════════════
ANSI_BOLD   = "\033[1m"
ANSI_CYAN   = "\033[96m"
ANSI_GREEN  = "\033[92m"
ANSI_RED    = "\033[91m"
ANSI_YELLOW = "\033[93m"
ANSI_RESET  = "\033[0m"

def conf_label(diff):
    pct = diff * 100
    if pct >= 11: return f"{ANSI_GREEN}ALTA{ANSI_RESET}"
    if pct >= 5:  return f"{ANSI_YELLOW}MEDIA{ANSI_RESET}"
    return f"{ANSI_RED}BAJA{ANSI_RESET}"

def main():
    results = []
    for game in TODAY_GAMES:
        home, away = game["home"], game["away"]
        ph, pa = game["p_home"], game["p_away"]

        s_home, n_home = score_team(home, ph, is_home=True,  opponent=away)
        s_away, n_away = score_team(away, pa, is_home=False, opponent=home)

        if s_home >= s_away:
            fav, und = home, away
            fav_score, und_score = s_home, s_away
            fav_notes = n_home
            fav_p = ph
            und_p = pa
        else:
            fav, und = away, home
            fav_score, und_score = s_away, s_home
            fav_notes = n_away
            fav_p = pa
            und_p = ph

        results.append({
            "away": away, "home": home,
            "fav": fav, "und": und,
            "fav_score": fav_score, "und_score": und_score,
            "fav_notes": fav_notes,
            "fav_p": fav_p, "und_p": und_p,
            "time": game["time"],
            "gap": round(fav_score - und_score, 4),
        })

    results.sort(key=lambda r: r["gap"], reverse=True)

    # ── TABLA PRINCIPAL ──────────────────────────────────────────────────────
    SEP = "═" * 130
    sep = "─" * 130
    print(f"\n{ANSI_BOLD}{SEP}{ANSI_RESET}")
    print(f"{ANSI_BOLD}{ANSI_CYAN}  MLB SPRING TRAINING – {date.today()}  │  16 FAVORITOS PROYECTADOS{ANSI_RESET}")
    print(f"  Sport: BÉISBOL  │  Modelo: Pitcheo(30%) + Roster(25%) + Forma ST(15%) + H2H(10%) + Contender(10%) + Local(5%) + Bullpen(5%)")
    print(f"  ⚠️  Spring Training = exhibición. Mayor dispersión de resultados que temporada regular.")
    print(f"{ANSI_BOLD}{SEP}{ANSI_RESET}")
    print(
        f"{'#':<4}{'PARTIDO':<22}{'FAVORITO':<26}{'ABRIDOR':<27}{'SCORE':<8}"
        f"{'RIVAL':<22}{'ABRIDOR RIVAL':<27}{'SCORE':<8}{'CONF'}"
    )
    print(sep)

    for i, r in enumerate(results, 1):
        matchup   = f"{r['away']} @ {r['home']}"
        fav_name  = TEAM_NAMES.get(r["fav"],  r["fav"])[:24]
        und_name  = TEAM_NAMES.get(r["und"],  r["und"])[:20]
        fav_p_short = r["fav_p"].split()[-1][:14]
        und_p_short = r["und_p"].split()[-1][:14]
        conf = conf_label(r["gap"])
        print(
            f"{ANSI_BOLD}{i:<4}{ANSI_RESET}"
            f"{matchup:<22}"
            f"{ANSI_GREEN}{fav_name:<26}{ANSI_RESET}"
            f"{r['fav_p'][:26]:<27}"
            f"{r['fav_score']:<8.4f}"
            f"{und_name:<22}"
            f"{r['und_p'][:26]:<27}"
            f"{r['und_score']:<8.4f}"
            f"{conf}"
        )

    print(f"{ANSI_BOLD}{SEP}{ANSI_RESET}")

    # ── ANÁLISIS TÉCNICO COMPLETO ────────────────────────────────────────────
    print(f"\n{ANSI_BOLD}{'═'*130}{ANSI_RESET}")
    print(f"{ANSI_BOLD}{ANSI_CYAN}  ANÁLISIS TÉCNICO COMPLETO POR PARTIDO{ANSI_RESET}")
    print(f"{ANSI_BOLD}{'═'*130}{ANSI_RESET}")

    for i, r in enumerate(results, 1):
        fav_name = TEAM_NAMES.get(r["fav"], r["fav"])
        und_name = TEAM_NAMES.get(r["und"], r["und"])
        pct_conf = r["gap"] / (r["fav_score"] + r["und_score"]) * 100

        print(f"\n  {ANSI_BOLD}[{i}]  {r['away']} @ {r['home']}  │  {r['time']}{ANSI_RESET}")
        print(f"  {'─'*90}")
        print(f"  {ANSI_GREEN}▶ FAVORITO: {fav_name:<28}{ANSI_RESET}  Abridor: {r['fav_p']}   (score {r['fav_score']:.4f})")
        print(f"  {ANSI_RED}◀ RIVAL   : {und_name:<28}{ANSI_RESET}  Abridor: {r['und_p']}   (score {r['und_score']:.4f})")
        print(f"  Ventaja modelo: +{r['gap']:.4f}  │  Confianza: {pct_conf:.1f}%")
        print(f"\n  Factores del FAVORITO:")
        for note in r["fav_notes"]:
            print(f"    • {note}")

    print(f"\n{ANSI_BOLD}{'═'*130}{ANSI_RESET}")
    print(f"{ANSI_BOLD}{ANSI_CYAN}  RESUMEN FINAL – FAVORITOS POR CONFIANZA{ANSI_RESET}")
    print(f"{ANSI_BOLD}{'═'*130}{ANSI_RESET}")
    for i, r in enumerate(results, 1):
        stars = "★" * min(5, max(1, int(r["gap"] / 0.045) + 1))
        fav_name = TEAM_NAMES.get(r["fav"], r["fav"])
        pct = r["gap"] / (r["fav_score"] + r["und_score"]) * 100
        print(
            f"  {i:>2}. {r['away']:<5} @ {r['home']:<5}  →  "
            f"{fav_name:<32}  {stars:<6}  "
            f"({pct:.1f}% ventaja modelo)  │  {r['fav_p']}"
        )
    print(f"{ANSI_BOLD}{'═'*130}{ANSI_RESET}\n")


if __name__ == "__main__":
    main()
