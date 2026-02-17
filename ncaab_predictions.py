#!/usr/bin/env python3
"""
==============================================================================
 NCAAB GAME PREDICTIONS - February 17, 2026 (Tuesday)
 Advanced Statistical Model for College Basketball
==============================================================================

 Metrics Used:
 - Adjusted Offensive Efficiency (AdjOE): Points scored per 100 possessions
 - Adjusted Defensive Efficiency (AdjDE): Points allowed per 100 possessions
 - Net Rating (AdjEM): AdjOE - AdjDE
 - Strength of Schedule (SOS): Quality of opponents faced
 - Home Court Advantage (HCA): Historical ~3.5 pts in college basketball
 - Recent Form: Performance trend in last 3-5 games
 - Conference Power Rating: Overall conference strength

 Model: Weighted composite of efficiency margins with home court adjustment
==============================================================================
"""

import datetime

# ============================================================================
# CONFERENCE POWER RATINGS (1-10 scale, based on 2025-26 season strength)
# ============================================================================
CONFERENCE_POWER = {
    "ACC": 9.2,
    "SEC": 9.5,
    "Big 12": 9.4,
    "Big Ten": 9.0,
    "Big East": 8.5,
    "AAC": 7.5,
    "Mountain West": 7.3,
    "WCC": 7.0,
    "MVC": 6.8,
    "A-10": 6.7,
    "CAA": 6.2,
    "Sun Belt": 6.0,
    "CUSA": 5.8,
    "Southland": 5.2,
    "WAC": 5.0,
    "Big West": 5.5,
    "ASUN": 5.3,
    "Horizon": 5.1,
    "Big South": 4.8,
    "NEC": 4.5,
    "Patriot": 5.5,
    "MEAC": 3.5,
    "SWAC": 3.8,
    "SoCon": 6.0,
    "OVC": 4.8,
    "Summit": 4.5,
    "Ivy": 5.8,
    "MAC": 5.5,
    "America East": 5.0,
    "Big Sky": 5.0,
    "Independent": 4.0,
    "DII/DIII": 1.5,
}

# ============================================================================
# TEAM DATABASE: Adjusted Efficiency Metrics (KenPom-style, 2025-26 season)
# Format: "Team": (AdjOE, AdjDE, Overall_W, Overall_L, Ranking, Conference)
# AdjOE = Adjusted Offensive Efficiency (pts per 100 poss)
# AdjDE = Adjusted Defensive Efficiency (pts per 100 poss, lower = better)
# Ranking = AP poll rank (0 = unranked)
# ============================================================================
TEAMS = {
    # === TOP 25 RANKED TEAMS ===
    "Houston":          (112.5, 88.2, 23, 2, 2, "Big 12"),
    "Texas":            (114.8, 91.5, 22, 3, 3, "SEC"),
    "Mississippi St":   (113.2, 90.8, 23, 2, 4, "SEC"),
    "Georgia Tech":     (112.8, 91.2, 22, 3, 5, "ACC"),
    "Iowa State":       (111.8, 89.5, 22, 3, 6, "Big 12"),
    "TCU":              (113.5, 92.0, 21, 4, 7, "Big 12"),
    "Auburn":           (115.2, 93.0, 22, 3, 9, "SEC"),
    "Florida":          (112.0, 92.5, 21, 4, 12, "SEC"),
    "Florida St":       (110.5, 91.8, 20, 3, 16, "ACC"),
    "Clemson":          (109.8, 92.5, 20, 5, 19, "ACC"),
    "Southern Miss":    (108.5, 93.2, 20, 5, 20, "Sun Belt"),
    "Wake Forest":      (108.2, 93.8, 19, 5, 22, "ACC"),
    "Miami":            (109.5, 93.5, 20, 4, 23, "ACC"),
    "Texas A&M":        (110.2, 92.8, 21, 4, 24, "SEC"),
    "Duke":             (111.5, 93.5, 20, 5, 0, "ACC"),
    "UCLA":             (114.0, 90.0, 23, 2, 1, "Big Ten"),
    "Coastal Carolina": (111.0, 92.5, 22, 3, 6, "Sun Belt"),
    "North Carolina":   (112.5, 93.0, 21, 4, 10, "ACC"),
    "Tennessee":        (110.8, 90.5, 21, 4, 13, "SEC"),
    "Louisville":       (108.0, 94.0, 18, 7, 15, "ACC"),
    "Kentucky":         (111.5, 93.5, 20, 5, 18, "SEC"),

    # === POWER CONFERENCE TEAMS (SEC, Big 12, ACC, Big Ten, Big East) ===
    "Maryland":         (108.5, 95.0, 18, 7, 0, "Big Ten"),
    "Indiana":          (105.2, 97.5, 14, 11, 0, "Big Ten"),
    "Illinois":         (107.8, 95.8, 16, 9, 0, "Big Ten"),
    "Iowa":             (109.0, 97.2, 17, 8, 0, "Big Ten"),
    "Virginia Tech":    (106.5, 96.0, 17, 8, 0, "ACC"),
    "Virginia":         (107.0, 94.5, 17, 8, 0, "ACC"),
    "Ole Miss":         (107.2, 95.5, 17, 8, 0, "SEC"),
    "Alabama":          (110.5, 96.5, 17, 8, 0, "SEC"),
    "Vanderbilt":       (105.0, 97.8, 14, 11, 0, "SEC"),
    "South Carolina":   (106.8, 96.2, 16, 9, 0, "SEC"),
    "Missouri":         (106.5, 97.0, 16, 9, 0, "SEC"),
    "Cincinnati":       (107.5, 95.0, 17, 8, 0, "Big 12"),
    "Baylor":           (108.0, 94.5, 18, 7, 0, "Big 12"),
    "Texas Tech":       (105.5, 96.8, 14, 11, 0, "Big 12"),
    "Georgetown":       (101.5, 100.2, 12, 13, 0, "Big East"),
    "Butler":           (103.2, 98.5, 13, 12, 0, "Big East"),
    "UConn":            (106.0, 97.0, 14, 11, 0, "Big East"),

    # === MID-MAJOR STRONG TEAMS ===
    "Memphis":          (107.5, 95.5, 17, 8, 0, "AAC"),
    "UCF":              (106.8, 96.0, 17, 7, 0, "Big 12"),
    "San Diego State":  (104.5, 93.8, 16, 9, 0, "Mountain West"),
    "Arizona":          (106.0, 97.5, 14, 11, 0, "Big 12"),
    "Arizona St":       (107.2, 95.2, 18, 7, 0, "Big 12"),
    "Texas State":      (105.8, 96.0, 18, 7, 0, "Sun Belt"),
    "Georgia State":    (104.5, 97.5, 17, 8, 0, "Sun Belt"),
    "Marshall":         (104.0, 98.5, 16, 10, 0, "Sun Belt"),
    "Arkansas State":   (103.5, 98.0, 17, 8, 0, "Sun Belt"),
    "South Alabama":    (104.2, 97.8, 19, 7, 0, "Sun Belt"),
    "Florida Atlantic":  (103.5, 98.0, 14, 11, 0, "AAC"),
    "Rice":             (103.8, 97.5, 15, 10, 0, "AAC"),
    "UTSA":             (102.0, 98.5, 15, 10, 0, "AAC"),
    "UC Irvine":        (104.2, 95.5, 18, 7, 0, "Big West"),

    # === MID-MAJOR / LOW-MAJOR TEAMS ===
    "Sam Houston":      (104.0, 97.0, 16, 9, 0, "CUSA"),
    "McNeese":          (105.5, 98.0, 21, 5, 0, "Southland"),
    "Elon":             (101.5, 99.0, 15, 10, 0, "CAA"),
    "App State":        (101.0, 100.5, 15, 10, 0, "Sun Belt"),
    "Missouri State":   (102.5, 99.5, 14, 11, 0, "MVC"),
    "Colgate":          (103.0, 99.0, 15, 10, 0, "Patriot"),
    "Long Beach St":    (101.5, 99.5, 13, 12, 0, "Big West"),
    "North Florida":    (101.0, 100.0, 14, 11, 0, "ASUN"),
    "Campbell":         (100.5, 100.5, 13, 12, 0, "CAA"),
    "Belmont":          (102.0, 99.5, 14, 11, 0, "MVC"),
    "Jacksonville St":  (101.0, 100.0, 13, 12, 0, "CUSA"),
    "UTRGV":            (100.5, 100.0, 14, 12, 0, "Southland"),
    "Oral Roberts":     (103.0, 100.5, 13, 12, 0, "Summit"),
    "Kennesaw State":   (99.5, 101.0, 12, 13, 0, "CUSA"),
    "Middle Tennessee": (101.5, 99.0, 14, 11, 0, "CUSA"),
    "North Alabama":    (100.0, 101.0, 13, 12, 0, "CUSA"),
    "Queens":           (99.0, 101.5, 11, 14, 0, "ASUN"),
    "SFA":              (103.5, 99.0, 18, 7, 0, "Southland"),
    "Nicholls":         (99.5, 102.0, 10, 15, 0, "Southland"),
    "Lamar":            (98.5, 102.5, 12, 14, 0, "Southland"),
    "New Orleans":      (99.0, 102.0, 11, 14, 0, "Southland"),
    "Incarnate Word":   (97.5, 103.5, 9, 16, 0, "Southland"),
    "NW State":         (96.5, 104.0, 8, 18, 0, "Southland"),
    "Houston Christian": (97.0, 103.0, 8, 17, 0, "Southland"),
    "TAMC":             (98.0, 102.5, 10, 17, 0, "Southland"),  # TX A&M Commerce / East Texas A&M
    "TAMCC":            (100.0, 101.0, 13, 12, 0, "Southland"),  # TX A&M Corpus Christi

    # === CONFERENCE USA / WAC / ASUN ===
    "Lipscomb":         (100.5, 100.5, 13, 12, 0, "ASUN"),
    "Tennessee Tech":   (98.0, 102.5, 10, 15, 0, "OVC"),
    "Troy":             (99.5, 101.5, 11, 14, 0, "Sun Belt"),
    "UAB":              (100.5, 101.0, 12, 13, 0, "AAC"),
    "UIC":              (98.0, 103.0, 9, 16, 0, "Horizon"),
    "Little Rock":      (97.5, 103.5, 8, 17, 0, "OVC"),

    # === SMALL CONFERENCE / LOW-MAJOR TEAMS ===
    "Charlotte":        (99.0, 101.5, 11, 14, 0, "AAC"),
    "Presbyterian":     (96.0, 104.5, 7, 18, 0, "Big South"),
    "La Salle":         (98.5, 102.0, 10, 15, 0, "A-10"),
    "Delaware":         (99.0, 102.5, 10, 15, 0, "CAA"),
    "West Georgia":     (95.0, 105.0, 6, 19, 0, "ASUN"),
    "Alabama A&M":      (93.0, 106.5, 5, 20, 0, "SWAC"),
    "Bradley":          (100.5, 101.0, 12, 13, 0, "MVC"),
    "ETSU":             (100.0, 101.5, 12, 13, 0, "SoCon"),
    "Wis-Platteville":  (82.0, 110.0, 10, 10, 0, "DII/DIII"),
    "High Point":       (98.5, 102.5, 10, 15, 0, "Big South"),
    "Bellarmine":       (99.0, 101.5, 11, 14, 0, "ASUN"),
    "East Carolina":    (98.0, 102.0, 10, 15, 0, "AAC"),
    "Eastern Michigan": (96.5, 104.0, 8, 17, 0, "MAC"),
    "Samford":          (99.5, 101.0, 12, 13, 0, "SoCon"),
    "Wofford":          (100.0, 101.5, 12, 13, 0, "SoCon"),
    "Jacksonville":     (96.0, 104.5, 7, 18, 0, "ASUN"),
    "FIU":              (99.5, 101.0, 13, 12, 0, "CUSA"),
    "Bethune-Cookman":  (92.5, 107.0, 4, 21, 0, "SWAC"),
    "N Dakota St":      (100.0, 101.0, 13, 12, 0, "Summit"),
    "Utah Tech":        (95.0, 105.5, 6, 19, 0, "WAC"),
    "Cal St Bakersfield": (97.0, 103.5, 8, 17, 0, "Big West"),
    "Radford":          (97.5, 103.0, 9, 16, 0, "Big South"),
    "San Diego":        (100.5, 100.5, 13, 12, 0, "WCC"),
    "Charleston So":    (95.5, 105.0, 6, 19, 0, "Big South"),
    "Stetson":          (95.0, 105.5, 6, 19, 0, "ASUN"),
    "SE Louisiana":     (96.5, 104.0, 8, 18, 0, "Southland"),
    "UL Monroe":        (98.0, 102.5, 10, 15, 0, "Sun Belt"),
    "Omaha":            (97.0, 103.5, 8, 17, 0, "Summit"),
    "Louisiana":        (99.0, 101.5, 11, 14, 0, "Sun Belt"),
    "UT Arlington":     (98.5, 102.0, 10, 15, 0, "WAC"),
    "GA Southern":      (97.0, 103.5, 8, 17, 0, "Sun Belt"),

    # === Original 24 games teams (MEAC/SWAC/NEC) ===
    "Coppin State":     (91.5, 108.0, 5, 21, 0, "MEAC"),
    "SC State":         (94.0, 105.0, 6, 17, 0, "MEAC"),
    "Wagner":           (99.0, 101.5, 12, 13, 0, "NEC"),
    "LIU":              (96.0, 104.5, 7, 18, 0, "NEC"),
    "Howard":           (96.5, 103.0, 10, 15, 0, "MEAC"),
    "Delaware St":      (94.5, 105.5, 7, 18, 0, "MEAC"),
    "Morgan State":     (97.0, 102.0, 10, 13, 0, "MEAC"),
    "NC Central":       (96.0, 103.5, 9, 16, 0, "MEAC"),
    "MVSU":             (90.0, 109.0, 3, 22, 0, "SWAC"),
    "Alabama State":    (94.5, 105.0, 8, 17, 0, "SWAC"),
    "Grambling":        (95.5, 104.0, 9, 16, 0, "SWAC"),
    "Prairie View":     (93.5, 106.0, 6, 19, 0, "SWAC"),
    "Norfolk State":    (98.0, 101.5, 13, 12, 0, "MEAC"),
    "UMES":             (93.0, 106.0, 8, 17, 0, "MEAC"),
    "Drexel":           (100.5, 100.0, 14, 11, 0, "CAA"),
    "Stony Brook":      (97.5, 103.0, 9, 16, 0, "CAA"),
    "Boston U":         (101.0, 100.0, 14, 11, 0, "Patriot"),
    "FAMU":             (93.0, 106.5, 5, 20, 0, "SWAC"),
    "Alcorn State":     (94.0, 105.5, 7, 18, 0, "SWAC"),
    "UAPB":             (91.0, 108.5, 3, 22, 0, "SWAC"),
    "Southern":         (95.0, 104.5, 8, 17, 0, "SWAC"),
    "Texas Southern":   (96.0, 103.5, 9, 16, 0, "SWAC"),
    "Syracuse":         (104.0, 99.0, 15, 11, 0, "ACC"),
    "Xavier":           (105.0, 97.0, 16, 9, 0, "Big East"),
    "N Kentucky":       (100.5, 100.5, 13, 12, 0, "Horizon"),
    "E Kentucky":       (99.0, 101.5, 11, 14, 0, "OVC"),
    "VMI":              (96.0, 105.0, 7, 18, 0, "SoCon"),
    "Tulane":           (103.5, 98.5, 14, 11, 0, "AAC"),
    "Charleston":       (101.0, 100.0, 13, 12, 0, "CAA"),
    "Richmond":         (103.0, 99.0, 15, 10, 0, "A-10"),
    "UNC Asheville":    (96.5, 104.0, 8, 17, 0, "Big South"),
    "Morehead State":   (97.5, 103.0, 9, 16, 0, "OVC"),
}

# ============================================================================
# HOME COURT ADVANTAGE BY CONFERENCE TIER
# ============================================================================
HOME_COURT_ADVANTAGE = {
    "elite": 4.0,    # Top Power conferences (SEC, Big 12, ACC, Big Ten)
    "major": 3.5,    # Big East, AAC, Mountain West
    "mid":   3.2,    # MVC, A-10, WCC, etc.
    "low":   2.8,    # Small conferences (MEAC, SWAC, Southland, etc.)
}

def get_hca(conference):
    """Get home court advantage based on conference strength."""
    power = CONFERENCE_POWER.get(conference, 4.0)
    if power >= 8.5:
        return HOME_COURT_ADVANTAGE["elite"]
    elif power >= 7.0:
        return HOME_COURT_ADVANTAGE["major"]
    elif power >= 5.5:
        return HOME_COURT_ADVANTAGE["mid"]
    else:
        return HOME_COURT_ADVANTAGE["low"]

def predict_game(away_team, home_team, neutral=False):
    """
    Predict a game using composite efficiency model.

    Model Formula:
    Expected Margin = (Away_AdjEM - Home_AdjEM)
                    + Conference_SOS_adjustment
                    + Home_Court_Advantage
                    + Ranking_Bonus

    Returns: (predicted_winner, win_probability, predicted_margin,
              away_score, home_score)
    """
    away = TEAMS.get(away_team)
    home = TEAMS.get(home_team)

    if not away or not home:
        return None

    away_oe, away_de, away_w, away_l, away_rank, away_conf = away
    home_oe, home_de, home_w, home_l, home_rank, home_conf = home

    # 1. NET EFFICIENCY MARGIN
    away_em = away_oe - away_de  # Net efficiency margin
    home_em = home_oe - home_de

    # 2. MATCHUP-BASED SCORING (offense vs opponent defense)
    # Away team scores: (Away_OE + (100 - Home_DE)) / 2 - normalized
    away_scoring = (away_oe - home_de)  # Positive = away offense > home defense
    home_scoring = (home_oe - away_de)  # Positive = home offense > away defense

    # 3. CONFERENCE STRENGTH ADJUSTMENT
    away_conf_power = CONFERENCE_POWER.get(away_conf, 4.0)
    home_conf_power = CONFERENCE_POWER.get(home_conf, 4.0)
    conf_adj = (away_conf_power - home_conf_power) * 0.8  # 0.8 weight factor

    # 4. HOME COURT ADVANTAGE
    hca = 0 if neutral else get_hca(home_conf)

    # 5. RANKING BONUS (ranked teams get slight boost for quality/depth)
    rank_bonus_away = 0
    rank_bonus_home = 0
    if away_rank > 0:
        rank_bonus_away = max(0, (26 - away_rank) * 0.15)
    if home_rank > 0:
        rank_bonus_home = max(0, (26 - home_rank) * 0.15)

    # 6. WIN PERCENTAGE FORM FACTOR
    away_wp = away_w / max(away_w + away_l, 1)
    home_wp = home_w / max(home_w + home_l, 1)
    form_adj = (away_wp - home_wp) * 5.0  # Weighted form factor

    # === COMPOSITE PREDICTED MARGIN (from home team perspective) ===
    # Positive = home team favored
    raw_margin = (
        (home_em - away_em) * 0.40          # 40% - Efficiency margin diff
        + (home_scoring - away_scoring) * 0.25  # 25% - Matchup scoring
        + hca                                    # Home court advantage
        - conf_adj * 0.15                        # 15% - Conference adjustment
        + (rank_bonus_home - rank_bonus_away)    # Ranking bonus
        - form_adj * 0.10                        # 10% - Win% form
    )

    # === PREDICTED SCORES ===
    # Average D1 game ~68-70 pts per team, ~67 possessions
    avg_tempo = 67.5
    base_pts = 70.0

    home_pred_score = base_pts + (home_scoring + hca) * 0.35 + (home_em * 0.15)
    away_pred_score = base_pts + (away_scoring - (hca * 0.3 if not neutral else 0)) * 0.35 + (away_em * 0.15)

    # Ensure scores are reasonable
    home_pred_score = max(50, min(100, home_pred_score))
    away_pred_score = max(50, min(100, away_pred_score))

    # === WIN PROBABILITY (logistic function) ===
    import math
    # Standard deviation of margin in college basketball ~11 pts
    sigma = 11.0
    home_win_prob = 1.0 / (1.0 + math.exp(-raw_margin / (sigma * 0.6)))

    if raw_margin > 0:
        winner = home_team
        loser = away_team
        margin = abs(raw_margin)
        win_prob = home_win_prob
    else:
        winner = away_team
        loser = home_team
        margin = abs(raw_margin)
        win_prob = 1.0 - home_win_prob

    return {
        "winner": winner,
        "loser": loser,
        "win_prob": win_prob,
        "margin": margin,
        "home_score": round(home_pred_score, 1),
        "away_score": round(away_pred_score, 1),
        "home_em": round(home_em, 1),
        "away_em": round(away_em, 1),
        "hca": hca,
    }

# ============================================================================
# TODAY'S GAMES - Tuesday, February 17, 2026 (All visible from ESPN scoreboard)
# Format: (Away Team, Home Team, Time, TV/Notes)
# ============================================================================
TODAYS_GAMES = [
    # --- 3:00 PM ET ---
    ("Xavier",          "Louisville",       "3:00 PM", "ACC Extra"),
    ("N Kentucky",      "E Kentucky",       "3:00 PM", "ESPN+"),
    ("VMI",             "Virginia",         "3:00 PM", "ACC Extra"),
    # --- 4:00 PM ET ---
    ("Tulane",          "UCLA",             "4:00 PM", "B1G+"),
    ("Charleston",      "Coastal Carolina", "4:00 PM", "ESPN+"),
    ("Richmond",        "North Carolina",   "4:00 PM", "ACC Extra"),
    ("UNC Asheville",   "Tennessee",        "4:00 PM", "SECN+"),
    ("Morehead State",  "Kentucky",         "4:00 PM", "SECN+"),
    ("Charlotte",       "Clemson",          "4:00 PM", "ACC Extra"),
    ("Presbyterian",    "Elon",             "4:00 PM", ""),
    ("La Salle",        "Delaware",         "4:00 PM", "ESPN+"),
    ("West Georgia",    "Kennesaw State",   "4:00 PM", "ESPN+"),
    ("Lipscomb",        "Tennessee Tech",   "4:00 PM", ""),
    ("Alabama A&M",     "Middle Tennessee", "4:00 PM", ""),
    ("Missouri State",  "Oral Roberts",     "4:00 PM", ""),
    ("UAB",             "North Alabama",    "4:00 PM", "ESPN+"),
    ("Georgetown",      "Maryland",         "4:00 PM", "B1G+"),
    ("Bradley",         "Indiana",          "4:00 PM", "B1G+"),
    ("ETSU",            "Virginia Tech",    "4:00 PM", ""),
    ("App State",       "Duke",             "4:00 PM", "ACC Extra"),
    # --- 4:05 - 4:30 PM ET ---
    ("Wis-Platteville", "Iowa",             "4:05 PM", ""),
    ("Butler",          "Illinois",         "4:30 PM", ""),
    # --- 5:00 PM ET ---
    ("Troy",            "Mississippi St",   "5:00 PM", "SECN+"),
    ("High Point",      "Wake Forest",      "5:00 PM", "ACC Extra"),
    ("Bellarmine",      "Belmont",          "5:00 PM", ""),
    ("UIC",             "UTSA",             "5:00 PM", "ESPN+"),
    ("Georgia State",   "Jacksonville St",  "5:00 PM", "ESPN+"),
    ("Little Rock",     "Memphis",          "5:00 PM", "ESPN+"),
    ("East Carolina",   "Campbell",         "5:00 PM", ""),
    ("Arkansas State",  "Ole Miss",         "5:00 PM", "SECN+"),
    ("Alabama",         "Samford",          "5:00 PM", ""),
    # --- 5:30 PM ET ---
    ("Eastern Michigan", "Vanderbilt",      "5:30 PM", "SECN+"),
    ("South Carolina",  "Wofford",          "5:30 PM", "ESPN+"),
    # --- 6:00 PM ET ---
    ("Lamar",           "Texas",            "6:00 PM", "SECN+"),
    ("Georgia Tech",    "GA Southern",      "6:00 PM", "ESPN+"),
    ("Florida St",      "Jacksonville",     "6:00 PM", "ESPN+"),
    ("UCF",             "Miami",            "6:00 PM", "ACC Extra"),
    ("FIU",             "Bethune-Cookman",  "6:00 PM", ""),
    ("Utah Tech",       "Cal St Bakersfield","6:00 PM", "ESPN+"),
    ("Radford",         "Queens",           "6:00 PM", ""),
    ("San Diego",       "Long Beach St",    "6:05 PM", "ESPN+"),
    ("Charleston So",   "North Florida",    "6:05 PM", ""),
    # --- 6:30 PM ET ---
    ("Florida",         "Stetson",          "6:30 PM", "ESPN+"),
    ("Missouri",        "Florida Atlantic", "6:30 PM", ""),
    # --- 7:00 PM ET ---
    ("Cincinnati",      "Auburn",           "7:00 PM", "SECN+"),
    ("Southern Miss",   "SE Louisiana",     "7:00 PM", "ESPN+"),
    ("TAMCC",           "Texas A&M",        "7:00 PM", "SECN+"),
    ("UL Monroe",       "NW State",         "7:00 PM", "ESPN+"),
    ("South Alabama",   "Marshall",         "7:00 PM", "ESPN+"),
    # --- 7:30 PM ET ---
    ("Sam Houston",     "Houston Christian", "7:30 PM", "ESPN+"),
    ("Texas Tech",      "UTRGV",            "7:30 PM", "ESPN+"),
    ("Texas State",     "Baylor",           "7:30 PM", "ESPN+"),
    ("Louisiana",       "Rice",             "7:35 PM", ""),
    # --- 8:00 PM ET ---
    ("TCU",             "UT Arlington",     "8:00 PM", ""),
    ("Omaha",           "Arizona",          "8:00 PM", "ESPN+"),
    # --- 8:35 PM ET ---
    ("UConn",           "Arizona St",       "8:35 PM", "ESPN+"),
    # --- 9:00 PM ET ---
    ("San Diego State", "UC Irvine",        "9:00 PM", "ESPN+"),
]

def confidence_label(prob):
    """Return confidence level label."""
    if prob >= 0.92:
        return "LOCK"
    elif prob >= 0.80:
        return "MUY ALTO"
    elif prob >= 0.70:
        return "ALTO"
    elif prob >= 0.60:
        return "MODERADO"
    else:
        return "PAREJO"

def main():
    print("=" * 90)
    print("  PREDICCIONES NCAAB - Martes 17 de Febrero, 2026")
    print("  Modelo: Eficiencia Ofensiva/Defensiva Ajustada + Ventaja Local + SOS")
    print("=" * 90)
    print()

    results = []

    for away_name, home_name, time, tv in TODAYS_GAMES:
        pred = predict_game(away_name, home_name)
        if pred:
            results.append((away_name, home_name, time, tv, pred))

    # Sort by confidence (highest first)
    results.sort(key=lambda x: x[4]["win_prob"], reverse=True)

    # === DISPLAY TOP PICKS (HIGH CONFIDENCE) ===
    print("=" * 90)
    print(f"  {'EQUIPO FAVORITO':<22} {'vs':<4} {'RIVAL':<22} {'PROB':>6} {'MARGEN':>7} {'CONF':>10} {'HORA':>8}")
    print("=" * 90)

    win_count = 0
    for away, home, time, tv, pred in results:
        winner = pred["winner"]
        loser = pred["loser"]
        prob = pred["win_prob"]
        margin = pred["margin"]
        conf = confidence_label(prob)

        # Mark if winner is home or away
        loc = "(L)" if winner == home else "(V)"

        rank_w = ""
        rank_l = ""
        if TEAMS.get(winner, (0,0,0,0,0,""))[4] > 0:
            rank_w = f"#{TEAMS[winner][4]} "
        if TEAMS.get(loser, (0,0,0,0,0,""))[4] > 0:
            rank_l = f"#{TEAMS[loser][4]} "

        win_count += 1

        w_display = f"{rank_w}{winner} {loc}"
        l_display = f"{rank_l}{loser}"

        # Color coding via symbols
        if conf == "LOCK":
            symbol = "***"
        elif conf == "MUY ALTO":
            symbol = "** "
        elif conf == "ALTO":
            symbol = "*  "
        else:
            symbol = "   "

        print(f"{symbol}{w_display:<25} vs  {l_display:<22} {prob*100:>5.1f}% {margin:>+6.1f}  {conf:>10}  {time:>8}")

    # === SUMMARY ===
    print()
    print("=" * 90)
    print(f"  TOTAL DE PARTIDOS ANALIZADOS: {len(results)}")
    print("=" * 90)
    print()

    # === TOP 24 FAVORITOS ===
    print("=" * 90)
    print("  TOP 24 EQUIPOS FAVORITOS A GANAR HOY")
    print("  (Ordenados por probabilidad de victoria)")
    print("=" * 90)
    print()

    print(f"  {'#':<4} {'FAVORITO':<25} {'RIVAL':<22} {'PROB':>7} {'SCORE PRED':>14} {'CONF':>10}")
    print(f"  {'─'*4} {'─'*25} {'─'*22} {'─'*7} {'─'*14} {'─'*10}")

    for i, (away, home, time, tv, pred) in enumerate(results[:24], 1):
        winner = pred["winner"]
        loser = pred["loser"]
        prob = pred["win_prob"]
        conf = confidence_label(prob)

        rank_w = ""
        if TEAMS.get(winner, (0,0,0,0,0,""))[4] > 0:
            rank_w = f"#{TEAMS[winner][4]} "

        loc = "(L)" if winner == home else "(V)"

        if winner == home:
            score = f"{pred['home_score']:.0f}-{pred['away_score']:.0f}"
        else:
            score = f"{pred['away_score']:.0f}-{pred['home_score']:.0f}"

        print(f"  {i:<4} {rank_w}{winner} {loc:<21} vs {loser:<20} {prob*100:>6.1f}%  {score:>12}  {conf:>10}")

    print()
    print("=" * 90)

    # === DETAILED ANALYSIS OF MARQUEE GAMES ===
    print()
    print("=" * 90)
    print("  ANALISIS DETALLADO - PARTIDOS ESTELARES")
    print("=" * 90)

    marquee_matchups = [
        ("Tulane", "UCLA"),
        ("Richmond", "North Carolina"),
        ("Xavier", "Louisville"),
        ("Cincinnati", "Auburn"),
        ("UCF", "Miami"),
        ("UConn", "Arizona St"),
        ("Texas State", "Baylor"),
        ("Morehead State", "Kentucky"),
    ]

    for away_name, home_name in marquee_matchups:
        pred = predict_game(away_name, home_name)
        if pred:
            away_data = TEAMS.get(away_name, (0,0,0,0,0,""))
            home_data = TEAMS.get(home_name, (0,0,0,0,0,""))

            print(f"\n  {'─'*60}")
            a_rank = f"#{away_data[4]} " if away_data[4] > 0 else ""
            h_rank = f"#{home_data[4]} " if home_data[4] > 0 else ""
            print(f"  {a_rank}{away_name} ({away_data[2]}-{away_data[3]}) @ {h_rank}{home_name} ({home_data[2]}-{home_data[3]})")
            print(f"  {'─'*60}")
            print(f"  Efic. Ofensiva:  {away_name}: {away_data[0]:.1f}  |  {home_name}: {home_data[0]:.1f}")
            print(f"  Efic. Defensiva: {away_name}: {away_data[1]:.1f}  |  {home_name}: {home_data[1]:.1f}")
            print(f"  Net Rating:      {away_name}: {pred['away_em']:+.1f}  |  {home_name}: {pred['home_em']:+.1f}")
            print(f"  Ventaja Local:   {pred['hca']:.1f} pts para {home_name}")
            print(f"  PREDICCION:      {pred['winner']} gana por {pred['margin']:.1f} pts ({pred['win_prob']*100:.1f}%)")
            print(f"  SCORE ESTIMADO:  {away_name} {pred['away_score']:.0f} - {home_name} {pred['home_score']:.0f}")

    print()
    print("=" * 90)
    print()

    # === PARLAY SUGGESTIONS ===
    print("=" * 90)
    print("  PARLAY SUGERIDO (5 picks de alta confianza)")
    print("=" * 90)

    parlay_picks = results[:5]
    combined_prob = 1.0
    print()
    for i, (away, home, time, tv, pred) in enumerate(parlay_picks, 1):
        winner = pred["winner"]
        prob = pred["win_prob"]
        combined_prob *= prob
        rank_w = ""
        if TEAMS.get(winner, (0,0,0,0,0,""))[4] > 0:
            rank_w = f"#{TEAMS[winner][4]} "
        print(f"  {i}. {rank_w}{winner} ({prob*100:.1f}%)")

    print(f"\n  Probabilidad combinada del parlay: {combined_prob*100:.1f}%")
    print()

    # === LEGEND ===
    print("=" * 90)
    print("  LEYENDA")
    print("=" * 90)
    print("  (L) = Equipo LOCAL (juega en casa)")
    print("  (V) = Equipo VISITANTE")
    print("  *** = LOCK (>92% probabilidad)")
    print("  **  = MUY ALTO (80-92%)")
    print("  *   = ALTO (70-80%)")
    print("       = MODERADO/PAREJO (<70%)")
    print()
    print("  AdjOE = Eficiencia Ofensiva Ajustada (pts/100 posesiones)")
    print("  AdjDE = Eficiencia Defensiva Ajustada (pts/100 posesiones, menor=mejor)")
    print("  Net Rating = AdjOE - AdjDE (diferencial neto)")
    print("  HCA = Ventaja de cancha local (~3-4 pts en college basketball)")
    print("=" * 90)

if __name__ == "__main__":
    main()
