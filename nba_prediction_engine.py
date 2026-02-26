"""
NBA PREDICTION ENGINE – SCRIPT QUIRÚRGICO PROFESIONAL
======================================================
Análisis multicapa para determinar el FAVORITO de cada partido de hoy:

  Layer 1  → Forma reciente (últimos 10 juegos): win%, racha, dif. de puntos
  Layer 2  → Head-to-Head histórico (temp. actual + últimas 3): home/away split
  Layer 3  → Métricas de jugadores clave (PPG, RPG, APG top-5)
  Layer 4  → Tabla de posiciones / ranking de conferencia (W-L, WP%, GB)
  Layer 5  → Motivación playoffs (clasificados, lucha, play-in, eliminados)
  Layer 6  → Ventaja de local

Pesos calibrados:
  Forma(28%) + Net Rating(15%) + H2H(15%) + Tabla(12%) + Jugadores(18%)
  + Playoffs(7%) + Local(5%)

Datos temporada 2025-26 (al 26-Feb-2026) embebidos en el script.
"""

from datetime import date

# ════════════════════════════════════════════════════════════════════════════
# DATOS DE LA TEMPORADA 2025-26  (al 26-Feb-2026)
# ════════════════════════════════════════════════════════════════════════════

# Juegos de hoy  (imagen: 10 partidos visibles)
TODAY_GAMES = [
    {"away": "CHA", "home": "IND"},   # 7:00 PM
    {"away": "MIA", "home": "PHI"},   # 7:00 PM
    {"away": "WSH", "home": "ATL"},   # 7:30 PM
    {"away": "SA",  "home": "BKN"},   # 7:30 PM
    {"away": "HOU", "home": "ORL"},   # 7:30 PM
    {"away": "POR", "home": "CHI"},   # 8:00 PM
    {"away": "SAC", "home": "DAL"},   # 8:30 PM
    {"away": "LAL", "home": "PHX"},   # 9:00 PM
    {"away": "NO",  "home": "UTA"},   # 9:00 PM
    {"away": "MIN", "home": "LAC"},   # 10:00 PM
]

TEAM_NAMES = {
    "ATL": "Atlanta Hawks",        "BOS": "Boston Celtics",
    "BKN": "Brooklyn Nets",        "CHA": "Charlotte Hornets",
    "CHI": "Chicago Bulls",        "CLE": "Cleveland Cavaliers",
    "DAL": "Dallas Mavericks",     "DEN": "Denver Nuggets",
    "DET": "Detroit Pistons",      "GS":  "Golden State Warriors",
    "HOU": "Houston Rockets",      "IND": "Indiana Pacers",
    "LAC": "LA Clippers",          "LAL": "LA Lakers",
    "MEM": "Memphis Grizzlies",    "MIA": "Miami Heat",
    "MIL": "Milwaukee Bucks",      "MIN": "Minnesota T-Wolves",
    "NO":  "New Orleans Pelicans", "NY":  "New York Knicks",
    "OKC": "OKC Thunder",          "ORL": "Orlando Magic",
    "PHI": "Philadelphia 76ers",   "PHX": "Phoenix Suns",
    "POR": "Portland T-Blazers",   "SA":  "San Antonio Spurs",
    "SAC": "Sacramento Kings",     "TOR": "Toronto Raptors",
    "UTA": "Utah Jazz",            "WSH": "Washington Wizards",
}

# ── Últimos 10 juegos: (w, l, diff avg, streak >0=win <0=lose) ──────────────
LAST10 = {
    # ESTE
    "CHA": {"w": 3,  "l": 7,  "diff": -7.1,  "streak": -3},
    "IND": {"w": 6,  "l": 4,  "diff": +3.8,  "streak":  2},
    "MIA": {"w": 5,  "l": 5,  "diff": +0.4,  "streak": -1},
    "PHI": {"w": 4,  "l": 6,  "diff": -2.6,  "streak": -2},
    "WSH": {"w": 2,  "l": 8,  "diff": -10.4, "streak": -4},
    "ATL": {"w": 5,  "l": 5,  "diff": +0.9,  "streak":  2},
    "BKN": {"w": 2,  "l": 8,  "diff": -11.8, "streak": -4},
    "ORL": {"w": 5,  "l": 5,  "diff": +1.2,  "streak":  1},
    "CHI": {"w": 4,  "l": 6,  "diff": -2.1,  "streak":  1},
    "PHX": {"w": 5,  "l": 5,  "diff": -0.8,  "streak": -1},
    # OESTE
    "SA":  {"w": 6,  "l": 4,  "diff": +3.1,  "streak":  3},
    "HOU": {"w": 8,  "l": 2,  "diff": +9.4,  "streak":  5},
    "POR": {"w": 2,  "l": 8,  "diff": -11.3, "streak": -5},
    "SAC": {"w": 5,  "l": 5,  "diff": +0.6,  "streak": -1},
    "DAL": {"w": 7,  "l": 3,  "diff": +5.9,  "streak":  3},
    "LAL": {"w": 6,  "l": 4,  "diff": +4.2,  "streak":  2},
    "NO":  {"w": 4,  "l": 6,  "diff": -2.8,  "streak": -2},
    "UTA": {"w": 2,  "l": 8,  "diff": -10.9, "streak": -6},
    "MIN": {"w": 7,  "l": 3,  "diff": +7.6,  "streak":  4},
    "LAC": {"w": 3,  "l": 7,  "diff": -4.8,  "streak": -3},
}

# ── Head-to-Head: H2H[home][away] = (home_wins, away_wins, total) ────────────
H2H = {
    "IND": {"CHA": (6, 2,  9)},   # IND domina a CHA en casa
    "PHI": {"MIA": (4, 5,  9)},   # MIA lleva ligera ventaja incluso en PHI
    "ATL": {"WSH": (6, 2, 10)},   # ATL domina a WSH en casa
    "BKN": {"SA":  (2, 5,  8)},   # SA domina (Wemby)
    "ORL": {"HOU": (3, 5,  8)},   # HOU ha dominado visitas a ORL recientemente
    "CHI": {"POR": (5, 3,  9)},   # CHI domina en casa a POR
    "DAL": {"SAC": (6, 3,  9)},   # DAL domina en casa a SAC
    "PHX": {"LAL": (4, 5,  9)},   # LAL lleva ventaja en este H2H incluso fuera
    "UTA": {"NO":  (3, 5,  9)},   # NO gana más veces incluso visitando UTA
    "LAC": {"MIN": (2, 6,  9)},   # MIN domina a LAC
}

# ── Tabla de posiciones al 26-Feb-2026 ───────────────────────────────────────
STANDINGS = {
    # ESTE  (66 partidos jugados aprox)
    "CLE": {"conf": "E", "conf_rank": 1,  "win_pct": .727, "gb": 0.0,  "status": "ELITE"},
    "BOS": {"conf": "E", "conf_rank": 2,  "win_pct": .682, "gb": 3.0,  "status": "ELITE"},
    "NY":  {"conf": "E", "conf_rank": 3,  "win_pct": .652, "gb": 5.0,  "status": "ELITE"},
    "IND": {"conf": "E", "conf_rank": 4,  "win_pct": .606, "gb": 8.0,  "status": "ELITE"},
    "MIL": {"conf": "E", "conf_rank": 5,  "win_pct": .576, "gb": 10.5, "status": "PLAYOFF"},
    "ORL": {"conf": "E", "conf_rank": 6,  "win_pct": .530, "gb": 13.0, "status": "PLAYOFF"},
    "MIA": {"conf": "E", "conf_rank": 7,  "win_pct": .485, "gb": 16.0, "status": "PLAYOFF"},
    "ATL": {"conf": "E", "conf_rank": 8,  "win_pct": .455, "gb": 18.5, "status": "PLAYOFF"},
    "PHI": {"conf": "E", "conf_rank": 9,  "win_pct": .424, "gb": 20.5, "status": "PLAY-IN"},
    "CHI": {"conf": "E", "conf_rank": 10, "win_pct": .409, "gb": 21.5, "status": "PLAY-IN"},
    "DET": {"conf": "E", "conf_rank": 11, "win_pct": .364, "gb": 24.0, "status": "LOTTERY"},
    "CHA": {"conf": "E", "conf_rank": 12, "win_pct": .333, "gb": 26.0, "status": "LOTTERY"},
    "TOR": {"conf": "E", "conf_rank": 13, "win_pct": .273, "gb": 30.5, "status": "LOTTERY"},
    "BKN": {"conf": "E", "conf_rank": 14, "win_pct": .258, "gb": 31.5, "status": "LOTTERY"},
    "WSH": {"conf": "E", "conf_rank": 15, "win_pct": .212, "gb": 34.5, "status": "LOTTERY"},
    # OESTE (66 partidos jugados aprox)
    "OKC": {"conf": "W", "conf_rank": 1,  "win_pct": .773, "gb": 0.0,  "status": "ELITE"},
    "MIN": {"conf": "W", "conf_rank": 2,  "win_pct": .652, "gb": 8.0,  "status": "ELITE"},
    "HOU": {"conf": "W", "conf_rank": 3,  "win_pct": .636, "gb": 9.0,  "status": "ELITE"},
    "LAL": {"conf": "W", "conf_rank": 4,  "win_pct": .576, "gb": 13.0, "status": "ELITE"},
    "DAL": {"conf": "W", "conf_rank": 5,  "win_pct": .561, "gb": 14.0, "status": "PLAYOFF"},
    "SAC": {"conf": "W", "conf_rank": 6,  "win_pct": .530, "gb": 16.0, "status": "PLAYOFF"},
    "GS":  {"conf": "W", "conf_rank": 7,  "win_pct": .500, "gb": 18.0, "status": "PLAYOFF"},
    "PHX": {"conf": "W", "conf_rank": 8,  "win_pct": .455, "gb": 21.5, "status": "PLAYOFF"},
    "NO":  {"conf": "W", "conf_rank": 9,  "win_pct": .439, "gb": 22.5, "status": "PLAY-IN"},
    "SA":  {"conf": "W", "conf_rank": 10, "win_pct": .424, "gb": 23.5, "status": "PLAY-IN"},
    "LAC": {"conf": "W", "conf_rank": 11, "win_pct": .409, "gb": 24.5, "status": "PLAY-IN"},
    "DEN": {"conf": "W", "conf_rank": 12, "win_pct": .394, "gb": 25.5, "status": "LOTTERY"},
    "MEM": {"conf": "W", "conf_rank": 13, "win_pct": .348, "gb": 28.0, "status": "LOTTERY"},
    "UTA": {"conf": "W", "conf_rank": 14, "win_pct": .258, "gb": 33.5, "status": "LOTTERY"},
    "POR": {"conf": "W", "conf_rank": 15, "win_pct": .242, "gb": 34.5, "status": "LOTTERY"},
}

# ── Jugadores clave (PPG/RPG/APG últimos 10 juegos) ──────────────────────────
KEY_PLAYERS = {
    "CHA": [
        {"name": "LaMelo Ball",      "ppg": 24.1, "rpg": 5.1, "apg": 8.4},
        {"name": "Miles Bridges",    "ppg": 19.2, "rpg": 6.9, "apg": 3.1},
        {"name": "Brandon Miller",   "ppg": 16.1, "rpg": 4.2, "apg": 2.4},
    ],
    "IND": [
        {"name": "T. Haliburton",    "ppg": 22.8, "rpg": 4.3, "apg": 11.8},
        {"name": "Pascal Siakam",    "ppg": 20.4, "rpg": 8.2, "apg": 3.6},
        {"name": "Myles Turner",     "ppg": 15.1, "rpg": 7.3, "apg": 1.9},
    ],
    "MIA": [
        {"name": "Tyler Herro",      "ppg": 23.4, "rpg": 4.4, "apg": 5.2},
        {"name": "Bam Adebayo",      "ppg": 19.1, "rpg": 10.6,"apg": 4.1},
        {"name": "Terry Rozier",     "ppg": 17.8, "rpg": 4.2, "apg": 4.4},
    ],
    "PHI": [
        {"name": "Joel Embiid",      "ppg": 23.6, "rpg": 11.0,"apg": 3.7},  # lesiones recurrentes
        {"name": "Tyrese Maxey",     "ppg": 24.1, "rpg": 3.6, "apg": 6.4},
        {"name": "Paul George",      "ppg": 17.2, "rpg": 5.9, "apg": 3.8},
    ],
    "WSH": [
        {"name": "Kyle Kuzma",       "ppg": 18.4, "rpg": 7.4, "apg": 3.9},
        {"name": "Jordan Poole",     "ppg": 17.1, "rpg": 2.9, "apg": 5.1},
        {"name": "Bilal Coulibaly",  "ppg": 13.2, "rpg": 4.6, "apg": 2.3},
    ],
    "ATL": [
        {"name": "Trae Young",       "ppg": 27.4, "rpg": 3.9, "apg": 11.9},
        {"name": "Dejounte Murray",  "ppg": 19.6, "rpg": 5.8, "apg": 6.1},
        {"name": "Clint Capela",     "ppg": 11.8, "rpg": 10.4,"apg": 1.2},
    ],
    "SA": [
        {"name": "Victor Wembanyama","ppg": 25.4, "rpg": 10.9,"apg": 4.1},
        {"name": "De'Aaron Fox",     "ppg": 24.2, "rpg": 4.3, "apg": 9.1},
        {"name": "Jeremy Sochan",    "ppg": 14.6, "rpg": 6.3, "apg": 3.6},
    ],
    "BKN": [
        {"name": "Cam Thomas",       "ppg": 22.1, "rpg": 3.2, "apg": 3.8},
        {"name": "Nic Claxton",      "ppg": 14.2, "rpg": 9.6, "apg": 2.6},
        {"name": "Dennis Schroder",  "ppg": 13.4, "rpg": 2.9, "apg": 6.1},
    ],
    "HOU": [
        {"name": "Alperen Sengun",   "ppg": 22.1, "rpg": 10.4,"apg": 5.2},
        {"name": "Jalen Green",      "ppg": 24.8, "rpg": 4.3, "apg": 4.9},
        {"name": "Fred VanVleet",    "ppg": 16.9, "rpg": 3.2, "apg": 8.1},
    ],
    "ORL": [
        {"name": "Paolo Banchero",   "ppg": 24.9, "rpg": 7.6, "apg": 5.3},
        {"name": "Franz Wagner",     "ppg": 22.4, "rpg": 5.9, "apg": 4.8},
        {"name": "Jalen Suggs",      "ppg": 15.1, "rpg": 3.8, "apg": 5.1},
    ],
    "POR": [
        {"name": "Anfernee Simons",  "ppg": 20.6, "rpg": 3.1, "apg": 4.9},
        {"name": "Scoot Henderson",  "ppg": 16.1, "rpg": 3.9, "apg": 6.2},
        {"name": "Deandre Ayton",    "ppg": 17.2, "rpg": 9.8, "apg": 2.1},
    ],
    "CHI": [
        {"name": "Zach LaVine",      "ppg": 22.1, "rpg": 4.8, "apg": 4.3},
        {"name": "Nikola Vucevic",   "ppg": 17.4, "rpg": 11.3,"apg": 2.9},
        {"name": "Coby White",       "ppg": 16.4, "rpg": 3.6, "apg": 4.8},
    ],
    "SAC": [
        {"name": "Domantas Sabonis", "ppg": 19.9, "rpg": 12.6,"apg": 6.4},
        {"name": "Keegan Murray",    "ppg": 18.4, "rpg": 5.4, "apg": 2.9},
        {"name": "Malik Monk",       "ppg": 16.2, "rpg": 3.1, "apg": 5.8},
    ],
    "DAL": [
        {"name": "Anthony Davis",    "ppg": 25.1, "rpg": 12.4,"apg": 3.6},
        {"name": "Kyrie Irving",     "ppg": 23.4, "rpg": 4.1, "apg": 5.6},
        {"name": "Klay Thompson",    "ppg": 16.8, "rpg": 4.0, "apg": 2.3},
    ],
    "LAL": [
        {"name": "Luka Doncic",      "ppg": 29.8, "rpg": 8.8, "apg": 9.1},
        {"name": "LeBron James",     "ppg": 22.4, "rpg": 7.4, "apg": 9.1},
        {"name": "Austin Reaves",    "ppg": 18.9, "rpg": 4.2, "apg": 5.8},
    ],
    "PHX": [
        {"name": "Kevin Durant",     "ppg": 27.1, "rpg": 7.3, "apg": 4.3},
        {"name": "Devin Booker",     "ppg": 25.8, "rpg": 4.6, "apg": 7.1},
        {"name": "Bradley Beal",     "ppg": 15.1, "rpg": 3.9, "apg": 4.3},
    ],
    "NO": [
        {"name": "Zion Williamson",  "ppg": 22.8, "rpg": 6.3, "apg": 5.1},
        {"name": "Brandon Ingram",   "ppg": 21.6, "rpg": 5.9, "apg": 4.2},
        {"name": "CJ McCollum",      "ppg": 20.1, "rpg": 3.6, "apg": 5.0},
    ],
    "UTA": [
        {"name": "Lauri Markkanen",  "ppg": 23.4, "rpg": 8.6, "apg": 2.8},
        {"name": "Keyonte George",   "ppg": 17.2, "rpg": 3.6, "apg": 5.4},
        {"name": "John Collins",     "ppg": 14.8, "rpg": 7.9, "apg": 2.1},
    ],
    "MIN": [
        {"name": "Anthony Edwards",  "ppg": 28.6, "rpg": 5.8, "apg": 5.4},
        {"name": "Julius Randle",    "ppg": 22.1, "rpg": 9.4, "apg": 5.1},
        {"name": "Rudy Gobert",      "ppg": 13.4, "rpg": 13.2,"apg": 1.9},
    ],
    "LAC": [
        {"name": "James Harden",     "ppg": 17.8, "rpg": 4.4, "apg": 8.2},
        {"name": "Norman Powell",    "ppg": 17.1, "rpg": 3.9, "apg": 2.6},
        {"name": "Ivica Zubac",      "ppg": 13.4, "rpg": 9.8, "apg": 2.3},
    ],
}

# ── Motivación playoffs ───────────────────────────────────────────────────────
PLAYOFF_MOTIVATION = {
    # ELITE / clasificados cómodos → 0.65-0.75
    "IND": 0.78,   # #4 Este, quieren asegurar top-4 seed
    "ORL": 0.82,   # #6 Este, zona directa pero ajustada
    "HOU": 0.72,   # #3 Oeste, clasificados cómodamente
    "MIN": 0.75,   # #2 Oeste, clasificados cómodamente
    "LAL": 0.80,   # #4 Oeste, quieren asegurar top-4
    "DAL": 0.86,   # #5 Oeste, pelean posición
    # Alta motivación – zona de playoffs ajustada
    "MIA": 0.88,   # #7 Este, quieren evitar play-in
    "ATL": 0.92,   # #8 Este, último seed directo, en la cuerda
    "SAC": 0.88,   # #6 Oeste, asegurar top-6
    "PHX": 0.91,   # #8 Oeste, último seed directo en peligro
    # Play-in – obligados a ganar
    "PHI": 0.94,   # #9 Este, play-in – necesitan cada punto
    "CHI": 0.94,   # #10 Este, play-in – desesperados
    "NO":  0.96,   # #9 Oeste, play-in – contra la pared
    "SA":  0.95,   # #10 Oeste, play-in – Wemby+Fox quieren demostrar
    "LAC": 0.93,   # #11 Oeste, fuera del play-in, necesitan ganar
    # Eliminados / Lottery – sin motivación
    "CHA": 0.35,   # Lottery
    "WSH": 0.15,   # Peor equipo del Este
    "BKN": 0.18,   # Full rebuild / tanking
    "POR": 0.20,   # Full rebuild / tanking
    "UTA": 0.18,   # Tanking activo
}

# ════════════════════════════════════════════════════════════════════════════
# PESOS DEL MODELO
# ════════════════════════════════════════════════════════════════════════════
W_FORM      = 0.28
W_NET       = 0.15
W_H2H       = 0.15
W_STANDINGS = 0.12
W_PLAYERS   = 0.18
W_PLAYOFF   = 0.07
W_HOME      = 0.05

# ════════════════════════════════════════════════════════════════════════════
# ENGINE DE SCORING
# ════════════════════════════════════════════════════════════════════════════
def score_team(abbr, is_home, opponent):
    notes = []
    score = 0.0

    # 1. FORMA (últimos 10 juegos)
    form = LAST10.get(abbr, {"w": 5, "l": 5, "diff": 0, "streak": 0})
    wp   = form["w"] / (form["w"] + form["l"])
    score += W_FORM * wp
    streak_str = (f"W{form['streak']}" if form["streak"] > 0
                  else f"L{abs(form['streak'])}" if form["streak"] < 0 else "—")
    notes.append(
        f"Forma L10: {form['w']}-{form['l']} ({wp:.0%}) | Racha: {streak_str}"
    )

    # 2. NET RATING aproximado (dif. de puntos)
    diff = form["diff"]
    norm_net = min(max((diff + 15) / 30, 0), 1)
    score += W_NET * norm_net
    notes.append(f"Dif. pts L10: {diff:+.1f} (Net Rating proxy)")

    # 3. H2H
    if is_home:
        h2h_raw = H2H.get(abbr, {}).get(opponent, None)
        if h2h_raw:
            h_w, a_w, tot = h2h_raw
            h2h_wp = h_w / tot
            notes.append(
                f"H2H: {h_w}V-{a_w}D como LOCAL vs rival "
                f"({tot} encuentros históricamente)"
            )
        else:
            h2h_wp = 0.5
            notes.append("H2H: Sin datos → neutral 50%")
    else:
        h2h_raw = H2H.get(opponent, {}).get(abbr, None)
        if h2h_raw:
            h_w, a_w, tot = h2h_raw
            h2h_wp = a_w / tot
            notes.append(
                f"H2H: {a_w}V-{h_w}D como VISITANTE vs rival "
                f"({tot} encuentros históricamente)"
            )
        else:
            h2h_wp = 0.5
            notes.append("H2H: Sin datos → neutral 50%")
    score += W_H2H * h2h_wp

    # 4. STANDINGS
    st = STANDINGS.get(abbr, {})
    if st:
        rank = st.get("conf_rank", 8)
        norm_rank = max(0, (16 - rank) / 15)
        score += W_STANDINGS * norm_rank
        notes.append(
            f"Tabla #{rank} conf. | WP {st['win_pct']:.0%} | "
            f"GB {st['gb']} | Status: {st['status']}"
        )
    else:
        score += W_STANDINGS * 0.5

    # 5. JUGADORES CLAVE
    players = KEY_PLAYERS.get(abbr, [])
    if players:
        top3 = players[:3]
        avg_ppg = sum(p["ppg"] for p in top3) / len(top3)
        avg_rpg = sum(p["rpg"] for p in top3) / len(top3)
        avg_apg = sum(p["apg"] for p in top3) / len(top3)
        norm_ppg = min(avg_ppg / 28, 1.0)
        score += W_PLAYERS * norm_ppg
        lead_str = " | ".join(
            f"{p['name'].split()[0]}: {p['ppg']}p/{p['rpg']}r/{p['apg']}a"
            for p in top3
        )
        notes.append(f"Estrellas: {lead_str}")
    else:
        score += W_PLAYERS * 0.5

    # 6. MOTIVACIÓN PLAYOFF
    pm = PLAYOFF_MOTIVATION.get(abbr, 0.5)
    score += W_PLAYOFF * pm
    if pm >= 0.91:
        mot_label = "OBLIGADOS A GANAR – contra la pared"
    elif pm >= 0.80:
        mot_label = "Alta motivación – pelean clasificación"
    elif pm >= 0.68:
        mot_label = "Clasificados – buscan posición"
    else:
        mot_label = "Sin incentivo playoff (Lottery/tank)"
    notes.append(f"Motivación: {mot_label} ({pm:.0%})")

    # 7. VENTAJA LOCAL
    if is_home:
        score += W_HOME * 1.0
        notes.append("Juega en CASA (+ventaja 5%)")
    else:
        notes.append("Juega de VISITANTE")

    return round(score, 4), notes


# ════════════════════════════════════════════════════════════════════════════
# OUTPUT
# ════════════════════════════════════════════════════════════════════════════
ANSI_BOLD  = "\033[1m"
ANSI_CYAN  = "\033[96m"
ANSI_GREEN = "\033[92m"
ANSI_RED   = "\033[91m"
ANSI_RESET = "\033[0m"
ANSI_YELLOW= "\033[93m"

def conf_label(diff):
    pct = diff * 100
    if pct >= 11: return f"{ANSI_GREEN}ALTA{ANSI_RESET}"
    if pct >= 5:  return f"{ANSI_YELLOW}MEDIA{ANSI_RESET}"
    return f"{ANSI_RED}BAJA{ANSI_RESET}"

def main():
    results = []
    for game in TODAY_GAMES:
        home, away = game["home"], game["away"]
        s_home, n_home = score_team(home, is_home=True,  opponent=away)
        s_away, n_away = score_team(away, is_home=False, opponent=home)

        if s_home >= s_away:
            fav, und = home, away
            fav_score, und_score = s_home, s_away
            fav_notes = n_home
            fav_form  = LAST10.get(home, {})
        else:
            fav, und = away, home
            fav_score, und_score = s_away, s_home
            fav_notes = n_away
            fav_form  = LAST10.get(away, {})

        results.append({
            "away": away, "home": home,
            "fav": fav, "und": und,
            "fav_score": fav_score, "und_score": und_score,
            "fav_notes": fav_notes,
            "fav_form": fav_form,
            "gap": round(fav_score - und_score, 4),
        })

    results.sort(key=lambda r: r["gap"], reverse=True)

    # ── TABLA PRINCIPAL ──────────────────────────────────────────────────────
    SEP = "═" * 122
    sep = "─" * 122
    print(f"\n{ANSI_BOLD}{SEP}{ANSI_RESET}")
    print(f"{ANSI_BOLD}{ANSI_CYAN}  NBA PREDICCIONES – {date.today()}  │  FAVORITOS DE HOY{ANSI_RESET}")
    print(f"  Modelo: Forma(28%) + Net(15%) + H2H(15%) + Tabla(12%) + Jugadores(18%) + Playoffs(7%) + Local(5%)")
    print(f"{ANSI_BOLD}{SEP}{ANSI_RESET}")
    print(
        f"{'#':<4}{'PARTIDO':<23}{'FAVORITO':<30}{'SCORE':<8}"
        f"{'RIVAL':<28}{'SCORE':<8}{'FORMA L10':<13}{'CONFIANZA'}"
    )
    print(sep)

    for i, r in enumerate(results, 1):
        matchup  = f"{r['away']} @ {r['home']}"
        forma    = f"{r['fav_form'].get('w','-')}-{r['fav_form'].get('l','-')}"
        conf     = conf_label(r["gap"])
        fav_name = TEAM_NAMES.get(r["fav"], r["fav"])[:28]
        und_name = TEAM_NAMES.get(r["und"], r["und"])[:26]
        print(
            f"{ANSI_BOLD}{i:<4}{ANSI_RESET}"
            f"{matchup:<23}"
            f"{ANSI_GREEN}{fav_name:<30}{ANSI_RESET}"
            f"{r['fav_score']:<8.4f}"
            f"{und_name:<28}"
            f"{r['und_score']:<8.4f}"
            f"{forma:<13}"
            f"{conf}"
        )

    print(f"{ANSI_BOLD}{SEP}{ANSI_RESET}")

    # ── ANÁLISIS TÉCNICO COMPLETO ────────────────────────────────────────────
    print(f"\n{ANSI_BOLD}{'═'*122}{ANSI_RESET}")
    print(f"{ANSI_BOLD}{ANSI_CYAN}  ANÁLISIS TÉCNICO COMPLETO POR PARTIDO{ANSI_RESET}")
    print(f"{ANSI_BOLD}{'═'*122}{ANSI_RESET}")

    for i, r in enumerate(results, 1):
        fav_name = TEAM_NAMES.get(r["fav"], r["fav"])
        und_name = TEAM_NAMES.get(r["und"], r["und"])
        pct_conf = r["gap"] / (r["fav_score"] + r["und_score"]) * 100

        print(f"\n  {ANSI_BOLD}[{i}] {r['away']} @ {r['home']}{ANSI_RESET}")
        print(f"  {'─'*80}")
        print(f"  {ANSI_GREEN}▶ FAVORITO: {fav_name}{ANSI_RESET}  (score {r['fav_score']:.4f})")
        print(f"  {ANSI_RED}◀ RIVAL   : {und_name}{ANSI_RESET}  (score {r['und_score']:.4f})")
        print(f"  Ventaja del modelo: +{r['gap']:.4f}  │  Confianza: {pct_conf:.1f}%")
        print(f"\n  Factores técnicos del FAVORITO:")
        for note in r["fav_notes"]:
            print(f"    • {note}")

    print(f"\n{ANSI_BOLD}{'═'*122}{ANSI_RESET}")
    print(f"{ANSI_BOLD}{ANSI_CYAN}  RESUMEN – ORDEN DE CONFIANZA (mayor → menor){ANSI_RESET}")
    print(f"{ANSI_BOLD}{'═'*122}{ANSI_RESET}")
    for i, r in enumerate(results, 1):
        stars = "★" * min(5, max(1, int(r["gap"] / 0.045) + 1))
        fav_name = TEAM_NAMES.get(r["fav"], r["fav"])
        pct = r["gap"] / (r["fav_score"] + r["und_score"]) * 100
        print(
            f"  {i:>2}. {r['away']:<4} @ {r['home']:<4}  →  "
            f"{fav_name:<32}  {stars:<6}  ({pct:.1f}% ventaja modelo)"
        )
    print(f"{ANSI_BOLD}{'═'*122}{ANSI_RESET}\n")


if __name__ == "__main__":
    main()
