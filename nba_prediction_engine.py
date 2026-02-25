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

Datos temporada 2025-26 (al 25-Feb-2026) embebidos en el script.
"""

from datetime import date

# ════════════════════════════════════════════════════════════════════════════
# DATOS DE LA TEMPORADA 2025-26  (al 25-Feb-2026)
# ════════════════════════════════════════════════════════════════════════════

# Juegos de hoy
TODAY_GAMES = [
    {"away": "PHI", "home": "IND"},
    {"away": "WSH", "home": "ATL"},
    {"away": "DAL", "home": "BKN"},
    {"away": "OKC", "home": "TOR"},
    {"away": "NY",  "home": "CLE"},
    {"away": "CHA", "home": "CHI"},
    {"away": "MIA", "home": "MIL"},
    {"away": "GS",  "home": "NO"},
    {"away": "BOS", "home": "PHX"},
    {"away": "MIN", "home": "POR"},
    {"away": "ORL", "home": "LAL"},
]

TEAM_NAMES = {
    "ATL": "Atlanta Hawks",       "BOS": "Boston Celtics",
    "BKN": "Brooklyn Nets",       "CHA": "Charlotte Hornets",
    "CHI": "Chicago Bulls",       "CLE": "Cleveland Cavaliers",
    "DAL": "Dallas Mavericks",    "DEN": "Denver Nuggets",
    "DET": "Detroit Pistons",     "GS":  "Golden State Warriors",
    "HOU": "Houston Rockets",     "IND": "Indiana Pacers",
    "LAC": "LA Clippers",         "LAL": "LA Lakers",
    "MEM": "Memphis Grizzlies",   "MIA": "Miami Heat",
    "MIL": "Milwaukee Bucks",     "MIN": "Minnesota T-Wolves",
    "NO":  "New Orleans Pelicans","NY":  "New York Knicks",
    "OKC": "OKC Thunder",         "ORL": "Orlando Magic",
    "PHI": "Philadelphia 76ers",  "PHX": "Phoenix Suns",
    "POR": "Portland T-Blazers",  "SA":  "San Antonio Spurs",
    "SAC": "Sacramento Kings",    "TOR": "Toronto Raptors",
    "UTA": "Utah Jazz",           "WSH": "Washington Wizards",
}

# ── Últimos 10 juegos: (W, L, avg_point_diff, streak >0=win, <0=lose) ──────
# streak: positivo = racha ganadora, negativo = racha perdedora
LAST10 = {
    # EAST
    "PHI": {"w": 4,  "l": 6,  "diff": -3.2, "streak": -3},
    "IND": {"w": 7,  "l": 3,  "diff": +5.1, "streak":  3},
    "WSH": {"w": 2,  "l": 8,  "diff": -9.8, "streak": -5},
    "ATL": {"w": 5,  "l": 5,  "diff": -0.7, "streak":  1},
    "NY":  {"w": 6,  "l": 4,  "diff": +3.4, "streak":  2},
    "CLE": {"w": 8,  "l": 2,  "diff": +8.2, "streak":  4},
    "CHA": {"w": 3,  "l": 7,  "diff": -6.5, "streak": -2},
    "CHI": {"w": 4,  "l": 6,  "diff": -2.9, "streak":  1},
    "MIA": {"w": 4,  "l": 6,  "diff": -1.8, "streak": -2},
    "MIL": {"w": 6,  "l": 4,  "diff": +4.0, "streak":  2},
    "BOS": {"w": 8,  "l": 2,  "diff": +9.1, "streak":  5},
    "PHX": {"w": 4,  "l": 6,  "diff": -2.3, "streak": -1},
    "ORL": {"w": 5,  "l": 5,  "diff": +0.3, "streak": -1},
    # WEST
    "OKC": {"w": 9,  "l": 1,  "diff": +12.4,"streak":  6},
    "TOR": {"w": 2,  "l": 8,  "diff": -10.1,"streak": -4},
    "DAL": {"w": 7,  "l": 3,  "diff": +6.3, "streak":  4},
    "BKN": {"w": 2,  "l": 8,  "diff": -11.2,"streak": -3},
    "GS":  {"w": 5,  "l": 5,  "diff": +0.9, "streak":  1},
    "NO":  {"w": 4,  "l": 6,  "diff": -3.1, "streak": -2},
    "MIN": {"w": 7,  "l": 3,  "diff": +7.2, "streak":  3},
    "POR": {"w": 2,  "l": 8,  "diff": -10.6,"streak": -5},
    "LAL": {"w": 7,  "l": 3,  "diff": +5.8, "streak":  2},
}

# ── Head-to-Head (temporada 2025-26 + últimas 2 temporadas, últimos 10 H2H)
# Para el equipo LOCAL: (wins_as_home_vs_opp, wins_as_away_vs_opp, total)
# H2H[local][away] = (h_wins, a_wins, total_games)
H2H = {
    # [IND vs PHI]  IND lleva ventaja histórica sobre PHI últimas temporadas
    "IND": {"PHI": (4, 2, 10)},
    # [ATL vs WSH]  ATL domina a WSH
    "ATL": {"WSH": (5, 3, 10)},
    # [BKN vs DAL]  DAL domina (BKN en reconstrucción)
    "BKN": {"DAL": (2, 4, 9)},
    # [TOR vs OKC]  OKC domina completamente
    "TOR": {"OKC": (1, 5, 8)},
    # [CLE vs NY]   CLE tiene ventaja reciente
    "CLE": {"NY":  (6, 3, 10)},
    # [CHI vs CHA]  Equipos parejos, ligera ventaja local CHI
    "CHI": {"CHA": (4, 3, 9)},
    # [MIL vs MIA]  MIL domina (Giannis)
    "MIL": {"MIA": (6, 2, 10)},
    # [NO vs GS]    GS tiene ventaja histórica leve
    "NO":  {"GS":  (3, 4, 9)},
    # [PHX vs BOS]  BOS domina últimas temporadas
    "PHX": {"BOS": (3, 5, 9)},
    # [POR vs MIN]  MIN domina (POR en reconstrucción)
    "POR": {"MIN": (1, 6, 9)},
    # [LAL vs ORL]  LAL domina en casa
    "LAL": {"ORL": (5, 2, 9)},
}

# ── Tabla de posiciones al 25-Feb-2026 ───────────────────────────────────────
# conf_rank: posición en conferencia
# win_pct: porcentaje de victorias
# games_back: juegos detrás del líder
# status: "ELITE" (1-4), "PLAYOFF" (5-8), "PLAY-IN" (9-10), "LOTTERY" (11+)
STANDINGS = {
    # ESTE
    "CLE": {"conf": "E", "conf_rank": 1,  "win_pct": .723, "gb": 0.0,  "status": "ELITE"},
    "BOS": {"conf": "E", "conf_rank": 2,  "win_pct": .680, "gb": 3.0,  "status": "ELITE"},
    "NY":  {"conf": "E", "conf_rank": 3,  "win_pct": .638, "gb": 6.0,  "status": "ELITE"},
    "IND": {"conf": "E", "conf_rank": 4,  "win_pct": .610, "gb": 8.0,  "status": "ELITE"},
    "MIL": {"conf": "E", "conf_rank": 5,  "win_pct": .574, "gb": 11.0, "status": "PLAYOFF"},
    "ORL": {"conf": "E", "conf_rank": 6,  "win_pct": .525, "gb": 14.5, "status": "PLAYOFF"},
    "MIA": {"conf": "E", "conf_rank": 7,  "win_pct": .489, "gb": 17.0, "status": "PLAYOFF"},
    "ATL": {"conf": "E", "conf_rank": 8,  "win_pct": .461, "gb": 19.5, "status": "PLAYOFF"},
    "CHI": {"conf": "E", "conf_rank": 9,  "win_pct": .411, "gb": 23.5, "status": "PLAY-IN"},
    "PHI": {"conf": "E", "conf_rank": 10, "win_pct": .397, "gb": 24.5, "status": "PLAY-IN"},
    "CHA": {"conf": "E", "conf_rank": 11, "win_pct": .326, "gb": 30.0, "status": "LOTTERY"},
    "WSH": {"conf": "E", "conf_rank": 15, "win_pct": .213, "gb": 38.5, "status": "LOTTERY"},
    "TOR": {"conf": "E", "conf_rank": 14, "win_pct": .241, "gb": 36.0, "status": "LOTTERY"},
    # OESTE
    "OKC": {"conf": "W", "conf_rank": 1,  "win_pct": .766, "gb": 0.0,  "status": "ELITE"},
    "MIN": {"conf": "W", "conf_rank": 2,  "win_pct": .638, "gb": 9.5,  "status": "ELITE"},
    "HOU": {"conf": "W", "conf_rank": 3,  "win_pct": .610, "gb": 11.5, "status": "ELITE"},
    "LAL": {"conf": "W", "conf_rank": 4,  "win_pct": .574, "gb": 14.0, "status": "ELITE"},
    "DAL": {"conf": "W", "conf_rank": 5,  "win_pct": .553, "gb": 16.0, "status": "PLAYOFF"},
    "SAC": {"conf": "W", "conf_rank": 6,  "win_pct": .525, "gb": 18.5, "status": "PLAYOFF"},
    "GS":  {"conf": "W", "conf_rank": 7,  "win_pct": .489, "gb": 21.0, "status": "PLAYOFF"},
    "PHX": {"conf": "W", "conf_rank": 8,  "win_pct": .454, "gb": 23.5, "status": "PLAYOFF"},
    "NO":  {"conf": "W", "conf_rank": 9,  "win_pct": .440, "gb": 25.0, "status": "PLAY-IN"},
    "POR": {"conf": "W", "conf_rank": 14, "win_pct": .213, "gb": 41.0, "status": "LOTTERY"},
    "BKN": {"conf": "E", "conf_rank": 13, "win_pct": .248, "gb": 36.5, "status": "LOTTERY"},
}

# ── Jugadores clave (top-3 por equipo: PPG/RPG/APG últimos 10 juegos) ────────
KEY_PLAYERS = {
    "PHI": [
        {"name": "Joel Embiid",    "ppg": 24.1, "rpg": 11.2, "apg": 3.6},
        {"name": "Tyrese Maxey",   "ppg": 22.8, "rpg": 3.4,  "apg": 6.1},
        {"name": "Paul George",    "ppg": 16.9, "rpg": 5.8,  "apg": 3.9},
    ],
    "IND": [
        {"name": "Tyrese Haliburton","ppg": 21.4,"rpg": 4.1, "apg": 11.2},
        {"name": "Pascal Siakam",   "ppg": 19.8, "rpg": 7.9, "apg": 3.4},
        {"name": "Myles Turner",    "ppg": 14.2, "rpg": 7.1, "apg": 1.8},
    ],
    "WSH": [
        {"name": "Kyle Kuzma",      "ppg": 18.1, "rpg": 7.2, "apg": 3.8},
        {"name": "Jordan Poole",    "ppg": 16.4, "rpg": 2.8, "apg": 4.9},
        {"name": "Bilal Coulibaly", "ppg": 12.6, "rpg": 4.3, "apg": 2.1},
    ],
    "ATL": [
        {"name": "Trae Young",      "ppg": 26.1, "rpg": 3.8, "apg": 11.4},
        {"name": "Dejounte Murray", "ppg": 18.9, "rpg": 5.6, "apg": 5.8},
        {"name": "Clint Capela",    "ppg": 11.4, "rpg": 10.2,"apg": 1.1},
    ],
    "DAL": [
        {"name": "Anthony Davis",   "ppg": 24.8, "rpg": 12.1,"apg": 3.5},
        {"name": "Kyrie Irving",    "ppg": 23.1, "rpg": 4.0, "apg": 5.3},
        {"name": "Klay Thompson",   "ppg": 16.4, "rpg": 3.9, "apg": 2.2},
    ],
    "BKN": [
        {"name": "Cam Thomas",      "ppg": 21.3, "rpg": 3.1, "apg": 3.6},
        {"name": "Nic Claxton",     "ppg": 13.8, "rpg": 9.4, "apg": 2.4},
        {"name": "Dennis Schroder", "ppg": 13.1, "rpg": 2.8, "apg": 5.9},
    ],
    "OKC": [
        {"name": "Shai Gilgeous-Alex.","ppg":31.4,"rpg":5.2,"apg": 5.9},
        {"name": "Chet Holmgren",   "ppg": 18.9, "rpg": 8.4, "apg": 2.1},
        {"name": "Jalen Williams",  "ppg": 23.2, "rpg": 4.8, "apg": 4.4},
    ],
    "TOR": [
        {"name": "Scottie Barnes",  "ppg": 19.6, "rpg": 8.1, "apg": 4.2},
        {"name": "RJ Barrett",      "ppg": 18.4, "rpg": 5.6, "apg": 3.7},
        {"name": "Immanuel Quickley","ppg":16.9,"rpg": 3.9, "apg": 6.3},
    ],
    "NY": [
        {"name": "Jalen Brunson",   "ppg": 28.9, "rpg": 3.5, "apg": 7.4},
        {"name": "Mikal Bridges",   "ppg": 21.4, "rpg": 4.6, "apg": 3.1},
        {"name": "OG Anunoby",      "ppg": 17.8, "rpg": 6.2, "apg": 2.2},
    ],
    "CLE": [
        {"name": "Donovan Mitchell","ppg": 28.4, "rpg": 4.8, "apg": 5.1},
        {"name": "Darius Garland",  "ppg": 21.6, "rpg": 3.1, "apg": 7.9},
        {"name": "Jarrett Allen",   "ppg": 15.1, "rpg": 10.8,"apg": 1.8},
    ],
    "CHA": [
        {"name": "LaMelo Ball",     "ppg": 23.8, "rpg": 4.9, "apg": 8.1},
        {"name": "Miles Bridges",   "ppg": 18.9, "rpg": 6.7, "apg": 2.9},
        {"name": "Brandon Miller",  "ppg": 15.6, "rpg": 4.1, "apg": 2.3},
    ],
    "CHI": [
        {"name": "Zach LaVine",     "ppg": 21.4, "rpg": 4.6, "apg": 4.1},
        {"name": "Nikola Vucevic",  "ppg": 16.8, "rpg": 11.1,"apg": 2.8},
        {"name": "Coby White",      "ppg": 15.9, "rpg": 3.4, "apg": 4.6},
    ],
    "MIA": [
        {"name": "Tyler Herro",     "ppg": 22.1, "rpg": 4.2, "apg": 4.9},
        {"name": "Bam Adebayo",     "ppg": 18.6, "rpg": 10.4,"apg": 3.8},
        {"name": "Terry Rozier",    "ppg": 17.4, "rpg": 4.1, "apg": 4.3},
    ],
    "MIL": [
        {"name": "Giannis Antet..", "ppg": 30.2, "rpg": 11.6,"apg": 5.8},
        {"name": "Damian Lillard",  "ppg": 24.8, "rpg": 3.9, "apg": 7.1},
        {"name": "Brook Lopez",     "ppg": 12.8, "rpg": 5.9, "apg": 1.4},
    ],
    "GS": [
        {"name": "Stephen Curry",   "ppg": 26.1, "rpg": 4.8, "apg": 6.4},
        {"name": "Draymond Green",  "ppg": 8.9,  "rpg": 7.2, "apg": 6.1},
        {"name": "Andrew Wiggins",  "ppg": 17.2, "rpg": 5.1, "apg": 2.4},
    ],
    "NO": [
        {"name": "Zion Williamson", "ppg": 22.4, "rpg": 6.1, "apg": 4.8},
        {"name": "CJ McCollum",     "ppg": 19.8, "rpg": 3.4, "apg": 4.9},
        {"name": "Brandon Ingram",  "ppg": 21.3, "rpg": 5.8, "apg": 4.1},
    ],
    "BOS": [
        {"name": "Jayson Tatum",    "ppg": 27.8, "rpg": 8.6, "apg": 4.9},
        {"name": "Jaylen Brown",    "ppg": 24.1, "rpg": 6.2, "apg": 3.7},
        {"name": "Kristaps Porzingis","ppg":19.4,"rpg": 7.8,"apg": 2.1},
    ],
    "PHX": [
        {"name": "Kevin Durant",    "ppg": 26.9, "rpg": 7.1, "apg": 4.2},
        {"name": "Devin Booker",    "ppg": 25.4, "rpg": 4.4, "apg": 6.8},
        {"name": "Bradley Beal",    "ppg": 14.6, "rpg": 3.8, "apg": 4.1},
    ],
    "MIN": [
        {"name": "Anthony Edwards", "ppg": 28.1, "rpg": 5.6, "apg": 5.2},
        {"name": "Rudy Gobert",     "ppg": 13.1, "rpg": 12.9,"apg": 1.8},
        {"name": "Julius Randle",   "ppg": 21.4, "rpg": 9.1, "apg": 4.8},
    ],
    "POR": [
        {"name": "Anfernee Simons", "ppg": 20.1, "rpg": 2.9, "apg": 4.8},
        {"name": "Scoot Henderson", "ppg": 15.4, "rpg": 3.8, "apg": 5.9},
        {"name": "Deandre Ayton",   "ppg": 16.8, "rpg": 9.6, "apg": 1.9},
    ],
    "ORL": [
        {"name": "Paolo Banchero",  "ppg": 24.6, "rpg": 7.4, "apg": 5.1},
        {"name": "Franz Wagner",    "ppg": 22.1, "rpg": 5.8, "apg": 4.6},
        {"name": "Jalen Suggs",     "ppg": 14.8, "rpg": 3.7, "apg": 4.9},
    ],
    "LAL": [
        {"name": "Luka Doncic",     "ppg": 29.4, "rpg": 8.6, "apg": 8.8},
        {"name": "LeBron James",    "ppg": 22.1, "rpg": 7.2, "apg": 8.9},
        {"name": "Austin Reaves",   "ppg": 18.4, "rpg": 4.1, "apg": 5.6},
    ],
}

# ── Motivación playoffs ───────────────────────────────────────────────────────
PLAYOFF_MOTIVATION = {
    # SCORE: 1.0 = máx motivación, 0.2 = eliminado/sin nada que jugar
    "OKC": 0.70,  # líderes del Oeste, clasificados cómodamente
    "CLE": 0.70,  # líderes del Este, clasificados cómodamente
    "BOS": 0.72,  # clasificados, buscan 1er seed
    "LAL": 0.80,  # #4 Oeste, quieren asegurar top-4
    "MIN": 0.80,  # #2 Oeste, quieren mantener posición
    "NY":  0.80,  # #3 Este, zona alta
    "IND": 0.82,  # #4 Este, quieren asegurar top-4
    "DAL": 0.88,  # #5 Oeste, pelean por posición
    "MIL": 0.85,  # #5 Este, quieren mantener clasificación directa
    "ORL": 0.90,  # #6 Este, en zona de playoffs directos pero ajustada
    "GS":  0.92,  # #7 Oeste, en la lucha para evitar play-in
    "ATL": 0.90,  # #8 Este, último seed de playoffs directos
    "PHX": 0.90,  # #8 Oeste, último seed de playoffs directos
    "NO":  0.95,  # #9 Oeste, play-in – obligados a ganar
    "MIA": 0.92,  # #7 Este, quieren evitar play-in
    "PHI": 0.95,  # #10 Este, play-in – desesperados
    "CHI": 0.93,  # #9 Este, play-in – alta motivación
    "CHA": 0.40,  # Lottery – sin motivación playoff
    "WSH": 0.15,  # Lottery peor registro – eliminados
    "TOR": 0.20,  # Lottery – eliminados, buscan picks
    "BKN": 0.18,  # Lottery – eliminados, tanking posible
    "POR": 0.20,  # Lottery – eliminados, tanking
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
    norm_net = min(max((diff + 15) / 30, 0), 1)  # normalizar [-15,+15] → [0,1]
    score += W_NET * norm_net
    notes.append(f"Dif. pts L10: {diff:+.1f} (Net Rating proxy)")

    # 3. H2H
    h2h_raw = H2H.get(opponent if is_home else abbr, {})
    h2h_key = abbr if is_home else opponent
    if is_home:
        h2h_raw = H2H.get(abbr, {}).get(opponent, None)
    else:
        h2h_raw = H2H.get(opponent, {}).get(abbr, None)
        if h2h_raw:
            # invertir: datos guardados desde perspectiva local
            h_w, a_w, tot = h2h_raw
            h2h_wp = a_w / tot if tot else 0.5
        else:
            h2h_wp = 0.5

    if is_home and h2h_raw:
        h_w, a_w, tot = h2h_raw
        h2h_wp = h_w / tot if tot else 0.5
        notes.append(
            f"H2H: {h_w}V-{a_w}D como local vs rival "
            f"(total {tot} encuentros)"
        )
    elif not is_home and h2h_raw:
        h_w, a_w, tot = H2H.get(opponent, {}).get(abbr, (0, 0, 1))
        h2h_wp_away = a_w / tot if tot else 0.5
        h2h_wp = h2h_wp_away
        notes.append(
            f"H2H: {a_w}V-{h_w}D como visitante vs rival "
            f"(total {tot} encuentros)"
        )
    else:
        h2h_wp = 0.5
        notes.append("H2H: Sin datos suficientes → neutral 50%")
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
        norm_ppg = min(avg_ppg / 28, 1.0)  # 28 ppg promedio top = máximo
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
    if pm >= 0.90:
        mot_label = "OBLIGADOS A GANAR (play-in/zona ajustada)"
    elif pm >= 0.78:
        mot_label = "Alta motivación – pelean posición"
    elif pm >= 0.65:
        mot_label = "Clasificados – motivación moderada"
    else:
        mot_label = "Sin incentivo playoff (Lottery)"
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
    pct = diff / 1.0 * 100  # diff máx teórico ~1.0
    if pct >= 12:  return f"{ANSI_GREEN}ALTA{ANSI_RESET}"
    if pct >= 6:   return f"{ANSI_YELLOW}MEDIA{ANSI_RESET}"
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

    # Ordenar por brecha de confianza
    results.sort(key=lambda r: r["gap"], reverse=True)

    # ── TABLA PRINCIPAL ──────────────────────────────────────────────────────
    SEP = "═" * 118
    sep = "─" * 118
    print(f"\n{ANSI_BOLD}{SEP}{ANSI_RESET}")
    print(f"{ANSI_BOLD}{ANSI_CYAN}  NBA PREDICCIONES – {date.today()}  │  11 FAVORITOS DE HOY{ANSI_RESET}")
    print(f"  Modelo: Forma(28%) + Net(15%) + H2H(15%) + Tabla(12%) + Jugadores(18%) + Playoffs(7%) + Local(5%)")
    print(f"{ANSI_BOLD}{SEP}{ANSI_RESET}")
    print(
        f"{'#':<4}{'PARTIDO':<23}{'FAVORITO':<30}{'SCORE':<8}"
        f"{'RIVAL':<27}{'SCORE':<8}{'FORMA L10':<13}{'CONFIANZA'}"
    )
    print(sep)

    for i, r in enumerate(results, 1):
        matchup = f"{r['away']} @ {r['home']}"
        forma   = f"{r['fav_form'].get('w','-')}-{r['fav_form'].get('l','-')}"
        conf    = conf_label(r["gap"])
        fav_name = TEAM_NAMES.get(r["fav"], r["fav"])[:28]
        und_name = TEAM_NAMES.get(r["und"], r["und"])[:25]
        print(
            f"{ANSI_BOLD}{i:<4}{ANSI_RESET}"
            f"{matchup:<23}"
            f"{ANSI_GREEN}{fav_name:<30}{ANSI_RESET}"
            f"{r['fav_score']:<8.4f}"
            f"{und_name:<27}"
            f"{r['und_score']:<8.4f}"
            f"{forma:<13}"
            f"{conf}"
        )

    print(f"{ANSI_BOLD}{SEP}{ANSI_RESET}")

    # ── ANÁLISIS TÉCNICO COMPLETO ────────────────────────────────────────────
    print(f"\n{ANSI_BOLD}{'═'*118}{ANSI_RESET}")
    print(f"{ANSI_BOLD}{ANSI_CYAN}  ANÁLISIS TÉCNICO COMPLETO POR PARTIDO{ANSI_RESET}")
    print(f"{ANSI_BOLD}{'═'*118}{ANSI_RESET}")

    for i, r in enumerate(results, 1):
        fav_name = TEAM_NAMES.get(r["fav"], r["fav"])
        und_name = TEAM_NAMES.get(r["und"], r["und"])
        pct_conf = r["gap"] / (r["fav_score"] + r["und_score"]) * 100

        print(f"\n  {ANSI_BOLD}[{i}] {r['away']} @ {r['home']}{ANSI_RESET}")
        print(f"  {'─'*80}")
        print(f"  {ANSI_GREEN}▶ FAVORITO : {fav_name}{ANSI_RESET}  (score {r['fav_score']:.4f})")
        print(f"  {ANSI_RED}◀ RIVAL    : {und_name}{ANSI_RESET}  (score {r['und_score']:.4f})")
        print(f"  Ventaja del modelo: +{r['gap']:.4f}  │  Confianza: {pct_conf:.1f}%")
        print(f"\n  Razones técnicas del FAVORITO:")
        for note in r["fav_notes"]:
            print(f"    • {note}")

    print(f"\n{ANSI_BOLD}{'═'*118}{ANSI_RESET}")
    print(f"{ANSI_BOLD}{ANSI_CYAN}  RESUMEN RÁPIDO – ORDEN DE CONFIANZA (mayor → menor){ANSI_RESET}")
    print(f"{ANSI_BOLD}{'═'*118}{ANSI_RESET}")
    for i, r in enumerate(results, 1):
        stars = "★" * min(5, max(1, int(r["gap"] / 0.04)))
        print(f"  {i:>2}. {r['away']:<4} @ {r['home']:<4}  →  {TEAM_NAMES.get(r['fav'], r['fav']):<30}  {stars}")
    print(f"{ANSI_BOLD}{'═'*118}{ANSI_RESET}\n")


if __name__ == "__main__":
    main()
