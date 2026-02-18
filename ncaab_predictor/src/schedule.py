"""
schedule.py – Fetch today's NCAAB schedule.

Tries ESPN public API first; falls back to embedded schedule derived from
the Feb 18 2026 slate visible in screenshots.
"""

from __future__ import annotations

import requests
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from typing import List, Dict

from .utils import get_logger, safe_get, cache_get, cache_set, RateLimiter

log = get_logger("schedule")
_rl = RateLimiter(calls_per_second=0.4)

ESPN_NCAAB_SCOREBOARD = (
    "https://site.api.espn.com/apis/site/v2/sports/basketball/"
    "mens-college-basketball/scoreboard"
)

# ── Game data model ──────────────────────────────────────────────────────────

def make_game(
    game_id: str,
    away_abbr: str,
    away_name: str,
    home_abbr: str,
    home_name: str,
    tip_time: str,
    neutral: bool = False,
    broadcast: str = "",
    conference_game: bool = True,
) -> Dict:
    return {
        "game_id": game_id,
        "away_abbr": away_abbr,
        "away_name": away_name,
        "home_abbr": home_abbr,
        "home_name": home_name,
        "tip_time": tip_time,
        "neutral_site": neutral,
        "broadcast": broadcast,
        "conference_game": conference_game,
    }


# ── ESPN fetch ───────────────────────────────────────────────────────────────

def _fetch_espn(date_str: str) -> List[Dict]:
    """Fetch NCAAB scoreboard for a given date (YYYYMMDD)."""
    cache_key = f"espn_ncaab_{date_str}"
    cached = cache_get(cache_key)
    if cached:
        log.info(f"Cache hit: ESPN schedule {date_str}")
        return cached

    _rl.wait()
    session = requests.Session()
    resp = safe_get(session, ESPN_NCAAB_SCOREBOARD, params={"dates": date_str})
    if resp is None:
        return []

    try:
        data = resp.json()
    except Exception:
        return []

    games = []
    for i, event in enumerate(data.get("events", []), 1):
        try:
            comp = event["competitions"][0]
            competitors = comp["competitors"]
            # ESPN: index 0 = away, index 1 = home
            away = competitors[0]
            home = competitors[1]

            games.append(make_game(
                game_id=event.get("id", str(i)),
                away_abbr=away["team"]["abbreviation"],
                away_name=away["team"]["displayName"],
                home_abbr=home["team"]["abbreviation"],
                home_name=home["team"]["displayName"],
                tip_time=event.get("date", "TBD"),
                neutral=comp.get("neutralSite", False),
                broadcast=", ".join(
                    b.get("names", [""])[0]
                    for b in comp.get("broadcasts", [])
                    if b.get("names")
                ),
            ))
        except (KeyError, IndexError):
            continue

    cache_set(cache_key, games)
    log.info(f"ESPN returned {len(games)} NCAAB games for {date_str}")
    return games


# ── Hardcoded fallback – Feb 18 2026 slate ──────────────────────────────────
# Derived from screenshots: 58 games total (ordered by tip time ET)

_FALLBACK_GAMES: List[Dict] = [
    # ── 6:00 PM ET ──────────────────────────────────────────────────────────
    make_game("g01", "RUTG", "Rutgers Scarlet Knights",
              "PSU",  "Penn State Nittany Lions",           "2026-02-18T23:00Z", broadcast="BTN"),
    make_game("g02", "LAF",  "Lafayette Leopards",
              "HC",   "Holy Cross Crusaders",               "2026-02-18T23:00Z", broadcast="ESPN+"),
    make_game("g03", "VMI",  "VMI Keydets",
              "WOF",  "Wofford Terriers",                   "2026-02-18T23:00Z", broadcast="ESPN+"),

    # ── 6:30 PM ET ──────────────────────────────────────────────────────────
    make_game("g04", "BUT",  "Butler Bulldogs",
              "GTWN", "Georgetown Hoyas",                   "2026-02-18T23:30Z", broadcast="FS1"),
    make_game("g05", "CLE",  "Cleveland State Vikings",
              "YSU",  "Youngstown State Penguins",          "2026-02-18T23:30Z", broadcast="ESPN+"),
    make_game("g06", "ETSU", "East Tennessee State Buccaneers",
              "FUR",  "Furman Paladins",                    "2026-02-18T23:30Z", broadcast="ESPN+"),

    # ── 7:00 PM ET ──────────────────────────────────────────────────────────
    make_game("g07", "CREI", "Creighton Bluejays",
              "CONN", "UConn Huskies",                      "2026-02-19T00:00Z", broadcast="TNT"),
    make_game("g08", "ARK",  "Arkansas Razorbacks",
              "ALA",  "Alabama Crimson Tide",               "2026-02-19T00:00Z", broadcast="ESPN"),
    make_game("g09", "UNI",  "Northern Iowa Panthers",
              "INST", "Indiana State Sycamores",            "2026-02-19T00:00Z", broadcast="ESPN+"),
    make_game("g10", "BRAD", "Bradley Braves",
              "VAL",  "Valparaiso Beacons",                 "2026-02-19T00:00Z", broadcast="ESPN+"),
    make_game("g11", "AMER", "American Eagles",
              "BUCK", "Bucknell Bison",                     "2026-02-19T00:00Z", broadcast="ESPN+"),
    make_game("g12", "JOES", "Saint Joseph's Hawks",
              "SBU",  "Saint Bonaventure Bonnies",          "2026-02-19T00:00Z", broadcast="ESPN+"),
    make_game("g13", "LUC",  "Loyola Chicago Ramblers",
              "FOR",  "Fordham Rams",                       "2026-02-19T00:00Z", broadcast="ESPN+"),
    make_game("g14", "LAS",  "La Salle Explorers",
              "DUQ",  "Duquesne Dukes",                     "2026-02-19T00:00Z", broadcast="ESPN+"),
    make_game("g15", "DAY",  "Dayton Flyers",
              "GMU",  "George Mason Patriots",              "2026-02-19T00:00Z", broadcast="CBSSN"),
    make_game("g16", "RICH", "Richmond Spiders",
              "DAV",  "Davidson Wildcats",                  "2026-02-19T00:00Z", broadcast="ESPN+"),
    make_game("g17", "WICH", "Wichita State Shockers",
              "ECU",  "East Carolina Pirates",              "2026-02-19T00:00Z", broadcast="ESPN+"),
    make_game("g18", "UAB",  "UAB Blazers",
              "TEM",  "Temple Owls",                        "2026-02-19T00:00Z", broadcast="ESPNU"),
    make_game("g19", "CLEM", "Clemson Tigers",
              "WAKE", "Wake Forest Demon Deacons",          "2026-02-19T00:00Z", broadcast="ACCN"),
    make_game("g20", "ARMY", "Army Black Knights",
              "LMD",  "Loyola Maryland Greyhounds",         "2026-02-19T00:00Z", broadcast="ESPN+"),
    make_game("g21", "LEH",  "Lehigh Mountain Hawks",
              "NAVY", "Navy Midshipmen",                    "2026-02-19T00:00Z", broadcast="ESPN+"),
    make_game("g22", "PFW",  "Purdue Fort Wayne Mastodons",
              "NKU",  "Northern Kentucky Norse",            "2026-02-19T00:00Z", broadcast="ESPN+"),
    make_game("g23", "UNCG", "UNC Greensboro Spartans",
              "WCU",  "Western Carolina Catamounts",        "2026-02-19T00:00Z", broadcast="ESPN+"),
    make_game("g24", "JMU",  "James Madison Dukes",
              "CCU",  "Coastal Carolina Chanticleers",      "2026-02-19T00:00Z", broadcast="ESPN+"),
    make_game("g25", "MISS", "Mississippi Rebels",
              "TAM",  "Texas A&M Aggies",                  "2026-02-19T00:00Z", broadcast="SEC Network"),
    make_game("g26", "OU",   "Oklahoma Sooners",
              "TENN", "Tennessee Volunteers",               "2026-02-19T00:00Z", broadcast="ESPN2"),
    make_game("g27", "WGA",  "West Georgia Wolves",
              "EKU",  "Eastern Kentucky Colonels",          "2026-02-19T00:00Z", broadcast="ESPN+"),
    make_game("g28", "JAX",  "Jacksonville Dolphins",
              "FGCU", "Florida Gulf Coast Eagles",          "2026-02-19T00:00Z", broadcast="ESPN+"),
    make_game("g29", "QUC",  "Queens Royals",
              "UNA",  "North Alabama Lions",                "2026-02-19T00:00Z", broadcast="ESPN+"),
    make_game("g30", "WKU",  "Western Kentucky Hilltoppers",
              "DEL",  "Delaware Fightin Blue Hens",         "2026-02-19T00:00Z", broadcast="ESPN+"),

    # ── 7:30 PM ET ──────────────────────────────────────────────────────────
    make_game("g31", "SIUE", "SIU Edwardsville Cougars",
              "DRKE", "Drake Bulldogs",                     "2026-02-19T00:30Z", broadcast="ESPN+"),
    make_game("g32", "TROY", "Troy Trojans",
              "ULM",  "Louisiana Monroe Warhawks",          "2026-02-19T00:30Z", broadcast="ESPN+"),
    make_game("g33", "LIP",  "Lipscomb Bisons",
              "BELL", "Bellarmine Knights",                 "2026-02-19T00:30Z", broadcast="ESPN+"),
    make_game("g34", "MTSU", "Middle Tennessee Blue Raiders",
              "SHSU", "Sam Houston State Bearkats",         "2026-02-19T00:30Z", broadcast="ESPN+"),
    make_game("g35", "JXST", "Jackson State Tigers",
              "LT",   "Louisiana Tech Bulldogs",            "2026-02-19T00:30Z", broadcast="ESPN+"),

    # ── 8:00 PM ET ──────────────────────────────────────────────────────────
    make_game("g36", "NCCU", "NC Central Eagles",
              "SCST", "South Carolina State Bulldogs",      "2026-02-19T01:00Z", broadcast="ESPN+"),
    make_game("g37", "UIC",  "UIC Flames",
              "EVAN", "Evansville Purple Aces",             "2026-02-19T01:00Z", broadcast="ESPN+"),
    make_game("g38", "FAU",  "Florida Atlantic Owls",
              "UTSA", "UTSA Roadrunners",                   "2026-02-19T01:00Z", broadcast="ESPN+"),
    make_game("g39", "CLT",  "Charlotte 49ers",
              "TLSA", "Tulsa Golden Hurricane",             "2026-02-19T01:00Z", broadcast="ESPN+"),
    make_game("g40", "MD",   "Maryland Terrapins",
              "NU",   "Northwestern Wildcats",              "2026-02-19T01:00Z", broadcast="BTN"),
    make_game("g41", "DEP",  "DePaul Blue Demons",
              "HALL", "Seton Hall Pirates",                 "2026-02-19T01:00Z", broadcast="truTV"),
    make_game("g42", "ORU",  "Oral Roberts Golden Eagles",
              "OMA",  "Omaha Mavericks",                   "2026-02-19T01:00Z", broadcast="ESPN+"),
    make_game("g43", "NDSU", "North Dakota State Bison",
              "SDST", "South Dakota State Jackrabbits",     "2026-02-19T01:00Z", broadcast="ESPN+"),
    make_game("g44", "KENN", "Kennesaw State Owls",
              "MOST", "Morehead State Eagles",              "2026-02-19T01:00Z", broadcast="ESPN+"),

    # ── 8:30 PM ET ──────────────────────────────────────────────────────────
    make_game("g45", "UTAH", "Utah Utes",
              "WVU",  "West Virginia Mountaineers",         "2026-02-19T01:30Z", broadcast="FS1"),

    # ── 9:00 PM ET ──────────────────────────────────────────────────────────
    make_game("g46", "BYU",  "BYU Cougars",
              "ARIZ", "Arizona Wildcats",                   "2026-02-19T02:00Z", broadcast="ESPN"),
    make_game("g47", "KU",   "Kansas Jayhawks",
              "OKST", "Oklahoma State Cowboys",             "2026-02-19T02:00Z", broadcast="Peacock"),
    make_game("g48", "UVA",  "Virginia Cavaliers",
              "GT",   "Georgia Tech Yellow Jackets",        "2026-02-19T02:00Z", broadcast="ACCN"),
    make_game("g49", "SJU",  "St. John's Red Storm",
              "MARQ", "Marquette Golden Eagles",            "2026-02-19T02:00Z", broadcast="TNT"),
    make_game("g50", "VAN",  "Vanderbilt Commodores",
              "MIZ",  "Missouri Tigers",                    "2026-02-19T02:00Z", broadcast="SEC Network"),
    make_game("g51", "MUR",  "Murray State Racers",
              "ILST", "Illinois State Redbirds",            "2026-02-19T02:00Z", broadcast="ESPNU"),
    make_game("g52", "SMC",  "Saint Mary's Gaels",
              "SEA",  "Seattle Redhawks",                   "2026-02-19T02:00Z", broadcast="CBSSN"),
    make_game("g53", "AUB",  "Auburn Tigers",
              "MSST", "Mississippi State Bulldogs",         "2026-02-19T02:00Z", broadcast="ESPN2"),

    # ── 9:30 PM ET ──────────────────────────────────────────────────────────
    make_game("g54", "PAC",  "Pacific Tigers",
              "WSU",  "Washington State Cougars",           "2026-02-19T02:30Z", broadcast="ESPN+"),

    # ── 10:00 PM ET ─────────────────────────────────────────────────────────
    make_game("g55", "ILL",  "Illinois Fighting Illini",
              "USC",  "USC Trojans",                        "2026-02-19T03:00Z", broadcast="BTN"),
    make_game("g56", "PEPP", "Pepperdine Waves",
              "PORT", "Portland Pilots",                    "2026-02-19T03:00Z", broadcast="ESPN+"),

    # ── 10:30 PM ET ─────────────────────────────────────────────────────────
    make_game("g57", "BOIS", "Boise State Broncos",
              "USU",  "Utah State Aggies",                  "2026-02-19T03:30Z", broadcast="FS1"),

    # ── 11:00 PM ET ─────────────────────────────────────────────────────────
    make_game("g58", "GONZ", "Gonzaga Bulldogs",
              "SF",   "San Francisco Dons",                 "2026-02-19T04:00Z", broadcast="ESPN2"),
    make_game("g59", "CSU",  "Colorado State Rams",
              "UNLV", "UNLV Rebels",                        "2026-02-19T04:00Z", broadcast="CBSSN"),
]


# ── Public API ───────────────────────────────────────────────────────────────

def get_todays_games(target_date: datetime | None = None) -> List[Dict]:
    """
    Return list of game dicts for today (America/New_York).

    Tries ESPN API first; falls back to embedded schedule on network failure.
    """
    ny_tz = ZoneInfo("America/New_York")
    if target_date is None:
        target_date = datetime.now(ny_tz)

    date_str = target_date.strftime("%Y%m%d")
    log.info(f"Fetching NCAAB schedule for {date_str} (ET)")

    games = _fetch_espn(date_str)

    if games:
        log.info(f"Live ESPN data: {len(games)} games")
        return games

    log.warning("ESPN fetch failed – using embedded Feb 18 2026 fallback schedule")
    return _FALLBACK_GAMES
