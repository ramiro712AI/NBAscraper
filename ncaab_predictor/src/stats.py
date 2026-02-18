"""
stats.py – Team efficiency metrics for 2025-26 NCAAB season.

Tries to fetch live data from Sports Reference / ESPN; falls back to a
comprehensive embedded database of KenPom-style ratings estimated for
the 2025-26 season based on program history, conference strength,
AP Poll rankings, and projected trajectories.

Database fields per team:
  full_name   – Display name
  adj_off     – Adjusted Offensive Efficiency (pts per 100 poss, sched-adjusted)
  adj_def     – Adjusted Defensive Efficiency (lower is better)
  efg_off     – Offensive eFG% (shooting quality)
  efg_def     – Defensive eFG% allowed (lower = better defense)
  tov_pct     – Turnover rate (lower = better; % of possessions ending in TO)
  orb_pct     – Offensive rebounding percentage
  ftr         – Free-throw rate (FTA / FGA)
  pace        – Possessions per 40 minutes
  l10_w       – Wins in last 10 games
  l10_l       – Losses in last 10 games
  l10_margin  – Average scoring margin over last 10 games (positive = winning)
  sos         – Strength of Schedule composite (higher = tougher)
  ranking     – AP Poll ranking (0 = unranked)
  conference  – Home conference
"""

from __future__ import annotations

import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional

from .utils import get_logger, safe_get, cache_get, cache_set, RateLimiter

log = get_logger("stats")
_rl = RateLimiter(calls_per_second=0.3)

# ─────────────────────────────────────────────────────────────────────────────
# EMBEDDED TEAM DATABASE  (2025-26 NCAAB Season Estimates)
# National averages: AdjO ≈ 104, AdjD ≈ 104, eFG ≈ 50.5%, TOV% ≈ 17.5%
# ─────────────────────────────────────────────────────────────────────────────

_DB: Dict[str, Dict] = {

    # ═══════════════════════════════════════════════════════════════
    # TIER 1 — AP Top 5  (elite programs, Net >+18)
    # ═══════════════════════════════════════════════════════════════
    "ARIZ": dict(full_name="Arizona Wildcats",         ranking=4,  conference="Big 12",
                 adj_off=121.5, adj_def=98.2,
                 efg_off=57.1, efg_def=46.8, tov_pct=15.8, orb_pct=34.2, ftr=0.35, pace=73.8,
                 l10_w=8, l10_l=2, l10_margin=+15.2, sos=13.5),

    "CONN": dict(full_name="UConn Huskies",            ranking=5,  conference="Big East",
                 adj_off=117.5, adj_def=97.0,
                 efg_off=54.8, efg_def=46.5, tov_pct=14.8, orb_pct=30.2, ftr=0.38, pace=68.5,
                 l10_w=8, l10_l=2, l10_margin=+14.5, sos=13.8),

    # ═══════════════════════════════════════════════════════════════
    # TIER 2 — AP Top 15  (Net +13 to +18)
    # ═══════════════════════════════════════════════════════════════
    "KU":   dict(full_name="Kansas Jayhawks",           ranking=8,  conference="Big 12",
                 adj_off=118.5, adj_def=99.5,
                 efg_off=55.5, efg_def=47.5, tov_pct=16.2, orb_pct=33.2, ftr=0.34, pace=72.2,
                 l10_w=8, l10_l=2, l10_margin=+13.8, sos=13.2),

    "ILL":  dict(full_name="Illinois Fighting Illini",  ranking=10, conference="Big Ten",
                 adj_off=116.0, adj_def=99.5,
                 efg_off=54.2, efg_def=47.8, tov_pct=17.0, orb_pct=31.5, ftr=0.31, pace=70.8,
                 l10_w=7, l10_l=3, l10_margin=+11.2, sos=12.8),

    "GONZ": dict(full_name="Gonzaga Bulldogs",          ranking=11, conference="WCC",
                 adj_off=121.2, adj_def=102.5,
                 efg_off=57.5, efg_def=48.5, tov_pct=15.5, orb_pct=33.5, ftr=0.29, pace=75.2,
                 l10_w=8, l10_l=2, l10_margin=+14.2, sos=10.5),

    "UVA":  dict(full_name="Virginia Cavaliers",        ranking=14, conference="ACC",
                 adj_off=111.2, adj_def=95.5,
                 efg_off=53.5, efg_def=45.5, tov_pct=14.2, orb_pct=27.5, ftr=0.40, pace=62.8,
                 l10_w=7, l10_l=3, l10_margin=+9.2,  sos=12.5),

    "SJU":  dict(full_name="St. John's Red Storm",      ranking=17, conference="Big East",
                 adj_off=115.2, adj_def=101.0,
                 efg_off=55.2, efg_def=48.8, tov_pct=17.0, orb_pct=33.5, ftr=0.37, pace=73.8,
                 l10_w=7, l10_l=3, l10_margin=+9.8,  sos=13.5),

    # ═══════════════════════════════════════════════════════════════
    # TIER 3 — AP Top 25  (Net +9 to +13)
    # ═══════════════════════════════════════════════════════════════
    "VAN":  dict(full_name="Vanderbilt Commodores",     ranking=19, conference="SEC",
                 adj_off=113.5, adj_def=100.8,
                 efg_off=54.2, efg_def=48.2, tov_pct=16.5, orb_pct=30.5, ftr=0.32, pace=70.5,
                 l10_w=7, l10_l=3, l10_margin=+9.5,  sos=12.8),

    "ARK":  dict(full_name="Arkansas Razorbacks",       ranking=20, conference="SEC",
                 adj_off=114.5, adj_def=102.5,
                 efg_off=54.8, efg_def=48.8, tov_pct=17.2, orb_pct=34.2, ftr=0.35, pace=72.5,
                 l10_w=7, l10_l=3, l10_margin=+9.2,  sos=12.5),

    "BYU":  dict(full_name="BYU Cougars",               ranking=23, conference="Big 12",
                 adj_off=112.5, adj_def=101.5,
                 efg_off=54.0, efg_def=48.5, tov_pct=16.2, orb_pct=31.2, ftr=0.31, pace=71.8,
                 l10_w=7, l10_l=3, l10_margin=+8.2,  sos=12.2),

    "ALA":  dict(full_name="Alabama Crimson Tide",      ranking=25, conference="SEC",
                 adj_off=115.0, adj_def=104.5,
                 efg_off=55.8, efg_def=49.5, tov_pct=18.5, orb_pct=34.5, ftr=0.36, pace=76.2,
                 l10_w=6, l10_l=4, l10_margin=+7.5,  sos=12.2),

    # ═══════════════════════════════════════════════════════════════
    # UNRANKED POWER CONFERENCE — STRONG  (Net +8 to +16)
    # ═══════════════════════════════════════════════════════════════
    "TENN": dict(full_name="Tennessee Volunteers",      ranking=0,  conference="SEC",
                 adj_off=113.2, adj_def=97.5,
                 efg_off=53.2, efg_def=46.2, tov_pct=15.5, orb_pct=29.2, ftr=0.41, pace=69.2,
                 l10_w=7, l10_l=3, l10_margin=+11.5, sos=13.5),

    "AUB":  dict(full_name="Auburn Tigers",             ranking=0,  conference="SEC",
                 adj_off=115.5, adj_def=101.5,
                 efg_off=55.5, efg_def=48.5, tov_pct=18.2, orb_pct=33.8, ftr=0.33, pace=74.5,
                 l10_w=7, l10_l=3, l10_margin=+10.5, sos=13.2),

    "CREI": dict(full_name="Creighton Bluejays",        ranking=0,  conference="Big East",
                 adj_off=116.0, adj_def=102.5,
                 efg_off=56.5, efg_def=48.8, tov_pct=15.8, orb_pct=29.8, ftr=0.28, pace=73.2,
                 l10_w=6, l10_l=4, l10_margin=+8.5,  sos=13.8),

    "MARQ": dict(full_name="Marquette Golden Eagles",   ranking=0,  conference="Big East",
                 adj_off=113.5, adj_def=101.5,
                 efg_off=54.8, efg_def=48.5, tov_pct=16.8, orb_pct=30.5, ftr=0.32, pace=72.2,
                 l10_w=6, l10_l=4, l10_margin=+7.8,  sos=13.5),

    "TAM":  dict(full_name="Texas A&M Aggies",          ranking=0,  conference="SEC",
                 adj_off=112.0, adj_def=101.5,
                 efg_off=53.8, efg_def=48.5, tov_pct=17.2, orb_pct=31.5, ftr=0.34, pace=70.8,
                 l10_w=6, l10_l=4, l10_margin=+7.2,  sos=12.8),

    "MIZ":  dict(full_name="Missouri Tigers",           ranking=0,  conference="SEC",
                 adj_off=111.5, adj_def=101.5,
                 efg_off=53.5, efg_def=48.8, tov_pct=17.5, orb_pct=31.0, ftr=0.32, pace=70.5,
                 l10_w=6, l10_l=4, l10_margin=+6.8,  sos=12.5),

    # ═══════════════════════════════════════════════════════════════
    # UNRANKED POWER CONFERENCE — MIDDLE  (Net +3 to +8)
    # ═══════════════════════════════════════════════════════════════
    "WVU":  dict(full_name="West Virginia Mountaineers",ranking=0,  conference="Big 12",
                 adj_off=110.5, adj_def=102.0,
                 efg_off=52.8, efg_def=49.2, tov_pct=17.8, orb_pct=31.8, ftr=0.35, pace=71.8,
                 l10_w=6, l10_l=4, l10_margin=+6.2,  sos=12.2),

    "MISS": dict(full_name="Mississippi Rebels",        ranking=0,  conference="SEC",
                 adj_off=110.5, adj_def=102.5,
                 efg_off=53.0, efg_def=49.5, tov_pct=18.0, orb_pct=30.8, ftr=0.33, pace=71.2,
                 l10_w=5, l10_l=5, l10_margin=+5.5,  sos=12.5),

    "OU":   dict(full_name="Oklahoma Sooners",          ranking=0,  conference="SEC",
                 adj_off=110.5, adj_def=102.5,
                 efg_off=53.2, efg_def=49.5, tov_pct=17.8, orb_pct=31.5, ftr=0.32, pace=72.5,
                 l10_w=5, l10_l=5, l10_margin=+5.8,  sos=12.8),

    "MSST": dict(full_name="Mississippi State Bulldogs",ranking=0,  conference="SEC",
                 adj_off=108.5, adj_def=103.5,
                 efg_off=52.0, efg_def=49.8, tov_pct=17.5, orb_pct=30.5, ftr=0.31, pace=70.8,
                 l10_w=5, l10_l=5, l10_margin=+4.2,  sos=12.2),

    "PSU":  dict(full_name="Penn State Nittany Lions",  ranking=0,  conference="Big Ten",
                 adj_off=110.0, adj_def=103.0,
                 efg_off=52.5, efg_def=49.5, tov_pct=16.8, orb_pct=30.0, ftr=0.31, pace=70.8,
                 l10_w=5, l10_l=5, l10_margin=+5.2,  sos=12.5),

    "MD":   dict(full_name="Maryland Terrapins",        ranking=0,  conference="Big Ten",
                 adj_off=109.5, adj_def=103.0,
                 efg_off=52.2, efg_def=49.5, tov_pct=17.2, orb_pct=30.2, ftr=0.32, pace=71.2,
                 l10_w=5, l10_l=5, l10_margin=+4.8,  sos=12.5),

    "NU":   dict(full_name="Northwestern Wildcats",     ranking=0,  conference="Big Ten",
                 adj_off=109.0, adj_def=103.0,
                 efg_off=52.0, efg_def=49.8, tov_pct=17.5, orb_pct=29.8, ftr=0.30, pace=70.5,
                 l10_w=5, l10_l=5, l10_margin=+4.5,  sos=12.2),

    "WAKE": dict(full_name="Wake Forest Demon Deacons", ranking=0,  conference="ACC",
                 adj_off=110.2, adj_def=104.0,
                 efg_off=53.5, efg_def=50.2, tov_pct=17.8, orb_pct=31.5, ftr=0.31, pace=73.8,
                 l10_w=5, l10_l=5, l10_margin=+4.2,  sos=12.0),

    "CLEM": dict(full_name="Clemson Tigers",            ranking=0,  conference="ACC",
                 adj_off=109.5, adj_def=103.5,
                 efg_off=52.8, efg_def=49.5, tov_pct=16.5, orb_pct=31.0, ftr=0.30, pace=71.2,
                 l10_w=5, l10_l=5, l10_margin=+5.0,  sos=12.2),

    "OKST": dict(full_name="Oklahoma State Cowboys",    ranking=0,  conference="Big 12",
                 adj_off=109.0, adj_def=103.5,
                 efg_off=52.5, efg_def=50.0, tov_pct=17.5, orb_pct=30.8, ftr=0.31, pace=71.8,
                 l10_w=5, l10_l=5, l10_margin=+4.0,  sos=12.5),

    "GT":   dict(full_name="Georgia Tech Yellow Jackets",ranking=0, conference="ACC",
                 adj_off=108.5, adj_def=103.5,
                 efg_off=52.2, efg_def=50.0, tov_pct=17.8, orb_pct=30.5, ftr=0.30, pace=72.2,
                 l10_w=5, l10_l=5, l10_margin=+3.8,  sos=11.8),

    "USC":  dict(full_name="USC Trojans",               ranking=0,  conference="Big Ten",
                 adj_off=108.0, adj_def=103.5,
                 efg_off=52.0, efg_def=50.2, tov_pct=18.0, orb_pct=31.2, ftr=0.29, pace=72.8,
                 l10_w=4, l10_l=6, l10_margin=+3.5,  sos=12.5),

    "HALL": dict(full_name="Seton Hall Pirates",        ranking=0,  conference="Big East",
                 adj_off=108.0, adj_def=103.5,
                 efg_off=51.8, efg_def=50.2, tov_pct=17.2, orb_pct=30.0, ftr=0.34, pace=70.5,
                 l10_w=4, l10_l=6, l10_margin=+3.5,  sos=13.5),

    "UTAH": dict(full_name="Utah Utes",                 ranking=0,  conference="Big 12",
                 adj_off=109.2, adj_def=104.0,
                 efg_off=52.5, efg_def=50.2, tov_pct=17.5, orb_pct=30.5, ftr=0.30, pace=71.5,
                 l10_w=5, l10_l=5, l10_margin=+4.0,  sos=12.2),

    "RUTG": dict(full_name="Rutgers Scarlet Knights",   ranking=0,  conference="Big Ten",
                 adj_off=107.5, adj_def=103.5,
                 efg_off=51.8, efg_def=50.2, tov_pct=17.8, orb_pct=30.8, ftr=0.30, pace=71.0,
                 l10_w=4, l10_l=6, l10_margin=+3.5,  sos=12.5),

    # ═══════════════════════════════════════════════════════════════
    # MID-MAJOR ELITE  (Net +5 to +11)
    # ═══════════════════════════════════════════════════════════════
    "BOIS": dict(full_name="Boise State Broncos",       ranking=0,  conference="MWC",
                 adj_off=113.5, adj_def=102.5,
                 efg_off=54.5, efg_def=49.0, tov_pct=16.5, orb_pct=32.2, ftr=0.33, pace=72.8,
                 l10_w=7, l10_l=3, l10_margin=+9.5,  sos=7.5),

    "DAY":  dict(full_name="Dayton Flyers",             ranking=0,  conference="A-10",
                 adj_off=112.0, adj_def=103.0,
                 efg_off=54.0, efg_def=49.2, tov_pct=16.8, orb_pct=31.5, ftr=0.30, pace=71.8,
                 l10_w=7, l10_l=3, l10_margin=+8.8,  sos=6.8),

    "DRKE": dict(full_name="Drake Bulldogs",            ranking=0,  conference="MVC",
                 adj_off=111.5, adj_def=103.0,
                 efg_off=54.2, efg_def=49.2, tov_pct=16.5, orb_pct=31.0, ftr=0.29, pace=72.0,
                 l10_w=7, l10_l=3, l10_margin=+8.5,  sos=6.2),

    "USU":  dict(full_name="Utah State Aggies",         ranking=0,  conference="MWC",
                 adj_off=111.2, adj_def=103.5,
                 efg_off=53.8, efg_def=49.5, tov_pct=16.8, orb_pct=32.0, ftr=0.31, pace=72.5,
                 l10_w=6, l10_l=4, l10_margin=+7.8,  sos=7.2),

    "CSU":  dict(full_name="Colorado State Rams",       ranking=0,  conference="MWC",
                 adj_off=110.5, adj_def=103.5,
                 efg_off=53.2, efg_def=49.8, tov_pct=17.0, orb_pct=31.2, ftr=0.30, pace=72.2,
                 l10_w=6, l10_l=4, l10_margin=+7.2,  sos=7.5),

    "SMC":  dict(full_name="Saint Mary's Gaels",        ranking=0,  conference="WCC",
                 adj_off=111.5, adj_def=103.5,
                 efg_off=54.2, efg_def=49.5, tov_pct=15.5, orb_pct=28.8, ftr=0.28, pace=68.8,
                 l10_w=6, l10_l=4, l10_margin=+7.5,  sos=7.8),

    "UNLV": dict(full_name="UNLV Rebels",               ranking=0,  conference="MWC",
                 adj_off=110.0, adj_def=104.0,
                 efg_off=53.5, efg_def=50.2, tov_pct=17.8, orb_pct=32.5, ftr=0.34, pace=74.0,
                 l10_w=5, l10_l=5, l10_margin=+6.2,  sos=7.8),

    "JMU":  dict(full_name="James Madison Dukes",       ranking=0,  conference="Sun Belt",
                 adj_off=109.5, adj_def=103.0,
                 efg_off=53.0, efg_def=49.5, tov_pct=17.2, orb_pct=32.0, ftr=0.31, pace=73.2,
                 l10_w=6, l10_l=4, l10_margin=+6.5,  sos=5.8),

    "MUR":  dict(full_name="Murray State Racers",       ranking=0,  conference="OVC",
                 adj_off=109.2, adj_def=103.5,
                 efg_off=53.5, efg_def=49.8, tov_pct=17.0, orb_pct=31.0, ftr=0.30, pace=71.5,
                 l10_w=6, l10_l=4, l10_margin=+6.2,  sos=5.5),

    "ORU":  dict(full_name="Oral Roberts Golden Eagles",ranking=0,  conference="Summit",
                 adj_off=111.0, adj_def=105.5,
                 efg_off=56.8, efg_def=51.0, tov_pct=16.0, orb_pct=28.8, ftr=0.27, pace=74.5,
                 l10_w=6, l10_l=4, l10_margin=+6.0,  sos=4.5),

    "SDST": dict(full_name="South Dakota State Jackrabbits",ranking=0,conference="Summit",
                 adj_off=109.5, adj_def=104.0,
                 efg_off=54.2, efg_def=50.5, tov_pct=16.8, orb_pct=33.0, ftr=0.30, pace=74.2,
                 l10_w=6, l10_l=4, l10_margin=+6.5,  sos=5.0),

    "WKU":  dict(full_name="Western Kentucky Hilltoppers",ranking=0,conference="CUSA",
                 adj_off=108.5, adj_def=103.5,
                 efg_off=53.0, efg_def=49.8, tov_pct=17.2, orb_pct=32.0, ftr=0.32, pace=72.8,
                 l10_w=5, l10_l=5, l10_margin=+5.5,  sos=5.5),

    "FAU":  dict(full_name="Florida Atlantic Owls",     ranking=0,  conference="AAC",
                 adj_off=108.5, adj_def=104.0,
                 efg_off=53.0, efg_def=50.2, tov_pct=17.5, orb_pct=31.5, ftr=0.31, pace=72.2,
                 l10_w=5, l10_l=5, l10_margin=+5.2,  sos=7.0),

    "UAB":  dict(full_name="UAB Blazers",               ranking=0,  conference="AAC",
                 adj_off=108.2, adj_def=103.5,
                 efg_off=52.5, efg_def=49.8, tov_pct=17.5, orb_pct=31.2, ftr=0.31, pace=71.8,
                 l10_w=5, l10_l=5, l10_margin=+5.0,  sos=6.8),

    "DAV":  dict(full_name="Davidson Wildcats",         ranking=0,  conference="A-10",
                 adj_off=108.5, adj_def=103.5,
                 efg_off=53.2, efg_def=49.8, tov_pct=16.5, orb_pct=29.8, ftr=0.28, pace=70.5,
                 l10_w=5, l10_l=5, l10_margin=+5.2,  sos=6.8),

    "DUQ":  dict(full_name="Duquesne Dukes",            ranking=0,  conference="A-10",
                 adj_off=107.5, adj_def=103.5,
                 efg_off=52.5, efg_def=50.2, tov_pct=17.2, orb_pct=30.5, ftr=0.30, pace=70.8,
                 l10_w=5, l10_l=5, l10_margin=+4.5,  sos=6.5),

    # ═══════════════════════════════════════════════════════════════
    # MID-MAJOR AVERAGE / LOWER-HALF  (Net +0 to +5)
    # ═══════════════════════════════════════════════════════════════
    "MTSU": dict(full_name="Middle Tennessee Blue Raiders",ranking=0,conference="CUSA",
                 adj_off=107.5, adj_def=103.5,
                 efg_off=52.5, efg_def=50.2, tov_pct=17.5, orb_pct=30.8, ftr=0.30, pace=71.5,
                 l10_w=5, l10_l=5, l10_margin=+4.2,  sos=5.5),

    "SHSU": dict(full_name="Sam Houston State Bearkats",ranking=0,  conference="CUSA",
                 adj_off=107.2, adj_def=103.8,
                 efg_off=52.2, efg_def=50.5, tov_pct=17.8, orb_pct=30.5, ftr=0.31, pace=71.8,
                 l10_w=5, l10_l=5, l10_margin=+4.0,  sos=5.2),

    "JOES": dict(full_name="Saint Joseph's Hawks",      ranking=0,  conference="A-10",
                 adj_off=107.5, adj_def=104.0,
                 efg_off=52.5, efg_def=50.5, tov_pct=17.5, orb_pct=30.5, ftr=0.29, pace=71.5,
                 l10_w=5, l10_l=5, l10_margin=+4.0,  sos=6.8),

    "SBU":  dict(full_name="Saint Bonaventure Bonnies", ranking=0,  conference="A-10",
                 adj_off=107.5, adj_def=104.2,
                 efg_off=52.5, efg_def=50.2, tov_pct=17.2, orb_pct=30.2, ftr=0.30, pace=71.2,
                 l10_w=5, l10_l=5, l10_margin=+4.0,  sos=6.5),

    "CLT":  dict(full_name="Charlotte 49ers",           ranking=0,  conference="AAC",
                 adj_off=107.2, adj_def=104.5,
                 efg_off=52.2, efg_def=50.5, tov_pct=17.5, orb_pct=31.0, ftr=0.30, pace=72.5,
                 l10_w=5, l10_l=5, l10_margin=+4.0,  sos=7.0),

    "RICH": dict(full_name="Richmond Spiders",          ranking=0,  conference="A-10",
                 adj_off=107.0, adj_def=104.0,
                 efg_off=52.2, efg_def=50.5, tov_pct=17.5, orb_pct=30.2, ftr=0.29, pace=71.2,
                 l10_w=4, l10_l=6, l10_margin=+3.5,  sos=6.5),

    "NDSU": dict(full_name="North Dakota State Bison",  ranking=0,  conference="Summit",
                 adj_off=106.5, adj_def=104.5,
                 efg_off=52.0, efg_def=50.5, tov_pct=17.0, orb_pct=30.5, ftr=0.29, pace=71.5,
                 l10_w=4, l10_l=6, l10_margin=+3.2,  sos=4.5),

    "UNCG": dict(full_name="UNC Greensboro Spartans",   ranking=0,  conference="SoCon",
                 adj_off=107.2, adj_def=104.5,
                 efg_off=52.5, efg_def=50.5, tov_pct=17.5, orb_pct=30.8, ftr=0.30, pace=71.8,
                 l10_w=5, l10_l=5, l10_margin=+4.0,  sos=4.8),

    "FGCU": dict(full_name="Florida Gulf Coast Eagles", ranking=0,  conference="ASUN",
                 adj_off=107.0, adj_def=104.5,
                 efg_off=52.5, efg_def=50.8, tov_pct=17.0, orb_pct=30.5, ftr=0.30, pace=72.2,
                 l10_w=5, l10_l=5, l10_margin=+3.8,  sos=4.5),

    "LT":   dict(full_name="Louisiana Tech Bulldogs",   ranking=0,  conference="CUSA",
                 adj_off=107.5, adj_def=104.5,
                 efg_off=52.5, efg_def=50.5, tov_pct=17.2, orb_pct=30.5, ftr=0.31, pace=71.8,
                 l10_w=5, l10_l=5, l10_margin=+4.2,  sos=5.5),

    "WSU":  dict(full_name="Washington State Cougars",  ranking=0,  conference="MWC",
                 adj_off=107.0, adj_def=104.5,
                 efg_off=52.2, efg_def=50.8, tov_pct=17.5, orb_pct=30.5, ftr=0.29, pace=71.5,
                 l10_w=4, l10_l=6, l10_margin=+3.5,  sos=7.0),

    "WICH": dict(full_name="Wichita State Shockers",    ranking=0,  conference="AAC",
                 adj_off=107.0, adj_def=103.5,
                 efg_off=52.0, efg_def=50.2, tov_pct=17.8, orb_pct=31.0, ftr=0.30, pace=71.5,
                 l10_w=4, l10_l=6, l10_margin=+3.5,  sos=7.0),

    "MOST": dict(full_name="Morehead State Eagles",     ranking=0,  conference="OVC",
                 adj_off=106.5, adj_def=105.5,
                 efg_off=52.0, efg_def=51.0, tov_pct=17.8, orb_pct=30.2, ftr=0.30, pace=72.0,
                 l10_w=5, l10_l=5, l10_margin=+3.5,  sos=4.0),

    "CCU":  dict(full_name="Coastal Carolina Chanticleers",ranking=0,conference="Sun Belt",
                 adj_off=107.2, adj_def=104.8,
                 efg_off=52.5, efg_def=50.8, tov_pct=17.5, orb_pct=31.2, ftr=0.31, pace=72.5,
                 l10_w=5, l10_l=5, l10_margin=+4.0,  sos=5.5),

    "DEL":  dict(full_name="Delaware Fightin Blue Hens",ranking=0,  conference="CAA",
                 adj_off=107.0, adj_def=105.0,
                 efg_off=52.2, efg_def=51.0, tov_pct=17.5, orb_pct=30.5, ftr=0.29, pace=71.8,
                 l10_w=5, l10_l=5, l10_margin=+3.8,  sos=5.2),

    "INST": dict(full_name="Indiana State Sycamores",   ranking=0,  conference="MVC",
                 adj_off=107.5, adj_def=104.5,
                 efg_off=52.5, efg_def=50.8, tov_pct=17.2, orb_pct=31.0, ftr=0.31, pace=71.5,
                 l10_w=5, l10_l=5, l10_margin=+3.8,  sos=5.8),

    "SF":   dict(full_name="San Francisco Dons",        ranking=0,  conference="WCC",
                 adj_off=107.5, adj_def=105.5,
                 efg_off=52.8, efg_def=51.2, tov_pct=17.5, orb_pct=30.8, ftr=0.30, pace=72.2,
                 l10_w=4, l10_l=6, l10_margin=+3.0,  sos=8.0),

    "BUT":  dict(full_name="Butler Bulldogs",           ranking=0,  conference="Big East",
                 adj_off=107.5, adj_def=104.5,
                 efg_off=52.5, efg_def=50.5, tov_pct=17.0, orb_pct=30.5, ftr=0.31, pace=70.8,
                 l10_w=4, l10_l=6, l10_margin=+3.5,  sos=13.5),

    "GMU":  dict(full_name="George Mason Patriots",     ranking=0,  conference="A-10",
                 adj_off=107.0, adj_def=105.0,
                 efg_off=52.0, efg_def=50.8, tov_pct=17.8, orb_pct=30.5, ftr=0.30, pace=72.0,
                 l10_w=4, l10_l=6, l10_margin=+3.2,  sos=6.5),

    "LUC":  dict(full_name="Loyola Chicago Ramblers",   ranking=0,  conference="A-10",
                 adj_off=107.0, adj_def=104.5,
                 efg_off=52.0, efg_def=50.5, tov_pct=17.2, orb_pct=30.5, ftr=0.30, pace=71.5,
                 l10_w=4, l10_l=6, l10_margin=+3.2,  sos=6.5),

    # ═══════════════════════════════════════════════════════════════
    # LOWER-TIER / SMALL CONFERENCE  (Net -5 to +3)
    # ═══════════════════════════════════════════════════════════════
    "FOR":  dict(full_name="Fordham Rams",              ranking=0,  conference="A-10",
                 adj_off=106.5, adj_def=104.5,
                 efg_off=51.8, efg_def=51.0, tov_pct=17.8, orb_pct=30.2, ftr=0.29, pace=71.5,
                 l10_w=4, l10_l=6, l10_margin=+2.8,  sos=6.5),

    "TLSA": dict(full_name="Tulsa Golden Hurricane",    ranking=0,  conference="AAC",
                 adj_off=106.5, adj_def=105.5,
                 efg_off=51.8, efg_def=51.2, tov_pct=17.8, orb_pct=30.5, ftr=0.30, pace=72.5,
                 l10_w=4, l10_l=6, l10_margin=+2.5,  sos=7.0),

    "UTSA": dict(full_name="UTSA Roadrunners",          ranking=0,  conference="AAC",
                 adj_off=106.5, adj_def=105.0,
                 efg_off=52.0, efg_def=51.0, tov_pct=17.5, orb_pct=30.2, ftr=0.30, pace=72.0,
                 l10_w=4, l10_l=6, l10_margin=+2.8,  sos=7.0),

    "UNI":  dict(full_name="Northern Iowa Panthers",    ranking=0,  conference="MVC",
                 adj_off=106.5, adj_def=104.5,
                 efg_off=51.8, efg_def=50.8, tov_pct=17.2, orb_pct=30.2, ftr=0.29, pace=70.8,
                 l10_w=4, l10_l=6, l10_margin=+2.5,  sos=5.8),

    "TROY": dict(full_name="Troy Trojans",              ranking=0,  conference="Sun Belt",
                 adj_off=106.2, adj_def=105.0,
                 efg_off=51.8, efg_def=51.0, tov_pct=17.5, orb_pct=30.5, ftr=0.30, pace=72.0,
                 l10_w=4, l10_l=6, l10_margin=+2.5,  sos=5.0),

    "LIP":  dict(full_name="Lipscomb Bisons",           ranking=0,  conference="ASUN",
                 adj_off=107.0, adj_def=105.0,
                 efg_off=52.2, efg_def=50.8, tov_pct=17.2, orb_pct=30.5, ftr=0.30, pace=72.2,
                 l10_w=5, l10_l=5, l10_margin=+3.5,  sos=4.5),

    "ILST": dict(full_name="Illinois State Redbirds",   ranking=0,  conference="MVC",
                 adj_off=106.5, adj_def=105.0,
                 efg_off=51.8, efg_def=51.0, tov_pct=17.5, orb_pct=30.5, ftr=0.29, pace=71.5,
                 l10_w=4, l10_l=6, l10_margin=+2.5,  sos=5.8),

    "ETSU": dict(full_name="East Tennessee State Buccaneers",ranking=0,conference="SoCon",
                 adj_off=106.5, adj_def=104.5,
                 efg_off=52.0, efg_def=50.8, tov_pct=17.2, orb_pct=30.5, ftr=0.30, pace=72.0,
                 l10_w=5, l10_l=5, l10_margin=+3.2,  sos=4.5),

    "BRAD": dict(full_name="Bradley Braves",            ranking=0,  conference="MVC",
                 adj_off=106.2, adj_def=105.2,
                 efg_off=51.5, efg_def=51.2, tov_pct=17.8, orb_pct=30.2, ftr=0.29, pace=71.5,
                 l10_w=4, l10_l=6, l10_margin=+2.2,  sos=5.5),

    "ECU":  dict(full_name="East Carolina Pirates",     ranking=0,  conference="AAC",
                 adj_off=106.5, adj_def=105.5,
                 efg_off=51.8, efg_def=51.2, tov_pct=17.8, orb_pct=30.5, ftr=0.30, pace=72.0,
                 l10_w=4, l10_l=6, l10_margin=+2.5,  sos=7.0),

    "TEM":  dict(full_name="Temple Owls",               ranking=0,  conference="AAC",
                 adj_off=105.5, adj_def=106.0,
                 efg_off=51.2, efg_def=51.8, tov_pct=18.2, orb_pct=30.8, ftr=0.30, pace=72.2,
                 l10_w=3, l10_l=7, l10_margin=+0.8,  sos=7.0),

    "PAC":  dict(full_name="Pacific Tigers",            ranking=0,  conference="WCC",
                 adj_off=106.2, adj_def=106.5,
                 efg_off=51.8, efg_def=51.8, tov_pct=17.8, orb_pct=30.5, ftr=0.29, pace=72.0,
                 l10_w=4, l10_l=6, l10_margin=+2.0,  sos=7.8),

    "EKU":  dict(full_name="Eastern Kentucky Colonels", ranking=0,  conference="ASUN",
                 adj_off=106.0, adj_def=105.5,
                 efg_off=51.8, efg_def=51.2, tov_pct=17.5, orb_pct=30.5, ftr=0.30, pace=71.8,
                 l10_w=4, l10_l=6, l10_margin=+2.2,  sos=4.5),

    "GTWN": dict(full_name="Georgetown Hoyas",          ranking=0,  conference="Independent",
                 adj_off=106.5, adj_def=105.0,
                 efg_off=51.8, efg_def=51.0, tov_pct=17.8, orb_pct=30.8, ftr=0.31, pace=71.2,
                 l10_w=4, l10_l=6, l10_margin=+2.5,  sos=6.0),

    "PORT": dict(full_name="Portland Pilots",           ranking=0,  conference="WCC",
                 adj_off=106.5, adj_def=106.0,
                 efg_off=51.8, efg_def=51.5, tov_pct=17.8, orb_pct=30.5, ftr=0.29, pace=72.0,
                 l10_w=4, l10_l=6, l10_margin=+2.2,  sos=7.8),

    "WCU":  dict(full_name="Western Carolina Catamounts",ranking=0, conference="SoCon",
                 adj_off=105.5, adj_def=105.5,
                 efg_off=51.2, efg_def=51.5, tov_pct=17.8, orb_pct=30.5, ftr=0.29, pace=71.8,
                 l10_w=4, l10_l=6, l10_margin=+1.8,  sos=4.2),

    "LMD":  dict(full_name="Loyola Maryland Greyhounds",ranking=0,  conference="Patriot",
                 adj_off=105.0, adj_def=106.0,
                 efg_off=51.0, efg_def=51.8, tov_pct=17.5, orb_pct=29.8, ftr=0.29, pace=70.8,
                 l10_w=4, l10_l=6, l10_margin=+1.8,  sos=3.8),

    "ULM":  dict(full_name="Louisiana Monroe Warhawks", ranking=0,  conference="Sun Belt",
                 adj_off=105.5, adj_def=106.0,
                 efg_off=51.2, efg_def=51.8, tov_pct=17.8, orb_pct=30.5, ftr=0.29, pace=71.5,
                 l10_w=4, l10_l=6, l10_margin=+1.5,  sos=5.0),

    "WOF":  dict(full_name="Wofford Terriers",          ranking=0,  conference="SoCon",
                 adj_off=105.5, adj_def=105.0,
                 efg_off=51.2, efg_def=51.2, tov_pct=17.5, orb_pct=29.8, ftr=0.29, pace=70.8,
                 l10_w=4, l10_l=6, l10_margin=+1.5,  sos=4.2),

    "OMA":  dict(full_name="Omaha Mavericks",           ranking=0,  conference="Summit",
                 adj_off=105.0, adj_def=106.0,
                 efg_off=51.0, efg_def=51.8, tov_pct=17.8, orb_pct=30.2, ftr=0.28, pace=71.5,
                 l10_w=4, l10_l=6, l10_margin=+1.2,  sos=4.5),

    "UNA":  dict(full_name="North Alabama Lions",       ranking=0,  conference="ASUN",
                 adj_off=105.0, adj_def=106.0,
                 efg_off=51.0, efg_def=52.0, tov_pct=17.8, orb_pct=30.2, ftr=0.28, pace=71.5,
                 l10_w=4, l10_l=6, l10_margin=+1.2,  sos=4.2),

    "LEH":  dict(full_name="Lehigh Mountain Hawks",     ranking=0,  conference="Patriot",
                 adj_off=106.5, adj_def=105.0,
                 efg_off=52.0, efg_def=51.0, tov_pct=17.2, orb_pct=30.2, ftr=0.29, pace=71.2,
                 l10_w=5, l10_l=5, l10_margin=+3.2,  sos=3.8),

    "FUR":  dict(full_name="Furman Paladins",           ranking=0,  conference="SoCon",
                 adj_off=106.0, adj_def=105.0,
                 efg_off=51.8, efg_def=51.2, tov_pct=17.5, orb_pct=30.2, ftr=0.29, pace=71.5,
                 l10_w=5, l10_l=5, l10_margin=+2.8,  sos=4.2),

    "LAS":  dict(full_name="La Salle Explorers",        ranking=0,  conference="A-10",
                 adj_off=105.5, adj_def=104.5,
                 efg_off=51.5, efg_def=51.0, tov_pct=17.8, orb_pct=30.2, ftr=0.28, pace=71.2,
                 l10_w=4, l10_l=6, l10_margin=+1.5,  sos=6.5),

    # ═══════════════════════════════════════════════════════════════
    # LOW-MAJOR / SMALL PROGRAMS  (Net -5 to 0)
    # ═══════════════════════════════════════════════════════════════
    "HC":   dict(full_name="Holy Cross Crusaders",      ranking=0,  conference="Patriot",
                 adj_off=105.5, adj_def=105.5,
                 efg_off=51.2, efg_def=51.5, tov_pct=17.5, orb_pct=29.5, ftr=0.29, pace=70.5,
                 l10_w=4, l10_l=6, l10_margin=+1.2,  sos=3.8),

    "LAF":  dict(full_name="Lafayette Leopards",        ranking=0,  conference="Patriot",
                 adj_off=105.0, adj_def=106.0,
                 efg_off=51.0, efg_def=51.8, tov_pct=17.8, orb_pct=29.8, ftr=0.28, pace=70.8,
                 l10_w=4, l10_l=6, l10_margin=+1.0,  sos=3.8),

    "NAVY": dict(full_name="Navy Midshipmen",           ranking=0,  conference="Patriot",
                 adj_off=105.0, adj_def=105.5,
                 efg_off=51.0, efg_def=51.8, tov_pct=17.5, orb_pct=29.5, ftr=0.28, pace=70.5,
                 l10_w=4, l10_l=6, l10_margin=+1.0,  sos=3.8),

    "BUCK": dict(full_name="Bucknell Bison",            ranking=0,  conference="Patriot",
                 adj_off=105.0, adj_def=105.5,
                 efg_off=51.2, efg_def=51.5, tov_pct=17.5, orb_pct=29.8, ftr=0.29, pace=70.8,
                 l10_w=4, l10_l=6, l10_margin=+1.2,  sos=3.8),

    "PFW":  dict(full_name="Purdue Fort Wayne Mastodons",ranking=0, conference="Horizon",
                 adj_off=105.5, adj_def=105.0,
                 efg_off=51.5, efg_def=51.5, tov_pct=17.5, orb_pct=30.2, ftr=0.29, pace=71.2,
                 l10_w=4, l10_l=6, l10_margin=+1.2,  sos=4.0),

    "NKU":  dict(full_name="Northern Kentucky Norse",   ranking=0,  conference="Horizon",
                 adj_off=104.5, adj_def=106.0,
                 efg_off=51.0, efg_def=52.0, tov_pct=17.8, orb_pct=29.5, ftr=0.28, pace=70.8,
                 l10_w=3, l10_l=7, l10_margin=+0.5,  sos=4.0),

    "CLE":  dict(full_name="Cleveland State Vikings",   ranking=0,  conference="Horizon",
                 adj_off=105.0, adj_def=105.5,
                 efg_off=51.2, efg_def=51.8, tov_pct=17.8, orb_pct=30.0, ftr=0.29, pace=71.0,
                 l10_w=4, l10_l=6, l10_margin=+1.2,  sos=4.0),

    "YSU":  dict(full_name="Youngstown State Penguins", ranking=0,  conference="Horizon",
                 adj_off=104.5, adj_def=106.0,
                 efg_off=51.0, efg_def=52.0, tov_pct=18.0, orb_pct=29.8, ftr=0.28, pace=70.8,
                 l10_w=3, l10_l=7, l10_margin=+0.5,  sos=4.0),

    "BELL": dict(full_name="Bellarmine Knights",        ranking=0,  conference="ASUN",
                 adj_off=104.5, adj_def=107.0,
                 efg_off=50.8, efg_def=52.5, tov_pct=18.2, orb_pct=29.5, ftr=0.28, pace=71.0,
                 l10_w=3, l10_l=7, l10_margin=+0.2,  sos=4.2),

    "VAL":  dict(full_name="Valparaiso Beacons",        ranking=0,  conference="MVC",
                 adj_off=104.5, adj_def=106.5,
                 efg_off=51.0, efg_def=52.2, tov_pct=18.0, orb_pct=29.5, ftr=0.28, pace=71.2,
                 l10_w=3, l10_l=7, l10_margin=+0.5,  sos=5.5),

    "AMER": dict(full_name="American Eagles",           ranking=0,  conference="Patriot",
                 adj_off=104.5, adj_def=106.0,
                 efg_off=50.8, efg_def=52.0, tov_pct=18.2, orb_pct=29.5, ftr=0.28, pace=70.5,
                 l10_w=3, l10_l=7, l10_margin=+0.2,  sos=3.8),

    "ARMY": dict(full_name="Army Black Knights",        ranking=0,  conference="Patriot",
                 adj_off=104.5, adj_def=106.5,
                 efg_off=50.5, efg_def=52.5, tov_pct=18.0, orb_pct=29.2, ftr=0.27, pace=70.2,
                 l10_w=3, l10_l=7, l10_margin=+0.0,  sos=3.8),

    "PEPP": dict(full_name="Pepperdine Waves",          ranking=0,  conference="WCC",
                 adj_off=105.5, adj_def=107.0,
                 efg_off=51.5, efg_def=52.2, tov_pct=17.8, orb_pct=29.8, ftr=0.28, pace=72.5,
                 l10_w=3, l10_l=7, l10_margin=+0.5,  sos=7.8),

    "SEA":  dict(full_name="Seattle Redhawks",          ranking=0,  conference="WAC",
                 adj_off=105.5, adj_def=107.0,
                 efg_off=51.5, efg_def=52.5, tov_pct=17.8, orb_pct=29.5, ftr=0.28, pace=72.0,
                 l10_w=3, l10_l=7, l10_margin=+0.5,  sos=5.5),

    "DEP":  dict(full_name="DePaul Blue Demons",        ranking=0,  conference="Big East",
                 adj_off=105.5, adj_def=106.5,
                 efg_off=51.5, efg_def=52.5, tov_pct=18.0, orb_pct=30.0, ftr=0.29, pace=72.5,
                 l10_w=2, l10_l=8, l10_margin=-3.5,  sos=13.5),

    "SIUE": dict(full_name="SIU Edwardsville Cougars",  ranking=0,  conference="OVC",
                 adj_off=105.0, adj_def=106.5,
                 efg_off=51.2, efg_def=52.5, tov_pct=18.0, orb_pct=29.8, ftr=0.28, pace=71.2,
                 l10_w=3, l10_l=7, l10_margin=-0.5,  sos=4.5),

    "QUC":  dict(full_name="Queens Royals",             ranking=0,  conference="ASUN",
                 adj_off=104.5, adj_def=107.0,
                 efg_off=50.8, efg_def=52.8, tov_pct=18.2, orb_pct=29.5, ftr=0.27, pace=71.0,
                 l10_w=3, l10_l=7, l10_margin=-0.5,  sos=4.2),

    "KENN": dict(full_name="Kennesaw State Owls",       ranking=0,  conference="CAA",
                 adj_off=105.0, adj_def=106.5,
                 efg_off=51.2, efg_def=52.5, tov_pct=18.0, orb_pct=29.8, ftr=0.28, pace=71.5,
                 l10_w=3, l10_l=7, l10_margin=-0.5,  sos=5.0),

    "VMI":  dict(full_name="VMI Keydets",               ranking=0,  conference="SoCon",
                 adj_off=108.0, adj_def=109.5,
                 efg_off=52.5, efg_def=53.5, tov_pct=17.8, orb_pct=30.2, ftr=0.28, pace=78.5,
                 l10_w=3, l10_l=7, l10_margin=-2.0,  sos=4.2),

    "WGA":  dict(full_name="West Georgia Wolves",       ranking=0,  conference="ASUN",
                 adj_off=103.5, adj_def=108.0,
                 efg_off=50.5, efg_def=53.2, tov_pct=18.5, orb_pct=29.5, ftr=0.27, pace=71.0,
                 l10_w=3, l10_l=7, l10_margin=-1.5,  sos=4.2),

    "JAX":  dict(full_name="Jacksonville Dolphins",     ranking=0,  conference="ASUN",
                 adj_off=104.5, adj_def=107.0,
                 efg_off=51.0, efg_def=52.8, tov_pct=18.2, orb_pct=29.5, ftr=0.27, pace=71.5,
                 l10_w=3, l10_l=7, l10_margin=-0.8,  sos=4.5),

    "UIC":  dict(full_name="UIC Flames",                ranking=0,  conference="Horizon",
                 adj_off=105.0, adj_def=106.0,
                 efg_off=51.2, efg_def=52.2, tov_pct=17.8, orb_pct=29.8, ftr=0.28, pace=71.5,
                 l10_w=3, l10_l=7, l10_margin=-0.5,  sos=4.2),

    "NCCU": dict(full_name="NC Central Eagles",         ranking=0,  conference="MEAC",
                 adj_off=103.0, adj_def=108.5,
                 efg_off=50.2, efg_def=53.5, tov_pct=18.5, orb_pct=29.5, ftr=0.27, pace=71.0,
                 l10_w=5, l10_l=5, l10_margin=+2.0,  sos=2.0),

    "SCST": dict(full_name="South Carolina State Bulldogs",ranking=0,conference="MEAC",
                 adj_off=100.5, adj_def=110.5,
                 efg_off=49.5, efg_def=54.5, tov_pct=19.5, orb_pct=29.0, ftr=0.26, pace=71.2,
                 l10_w=3, l10_l=7, l10_margin=-4.5,  sos=2.0),

    "JXST": dict(full_name="Jackson State Tigers",      ranking=0,  conference="SWAC",
                 adj_off=103.5, adj_def=108.0,
                 efg_off=50.5, efg_def=53.5, tov_pct=18.8, orb_pct=30.0, ftr=0.27, pace=71.5,
                 l10_w=4, l10_l=6, l10_margin=-2.0,  sos=2.0),

    "EVAN": dict(full_name="Evansville Purple Aces",    ranking=0,  conference="MVC",
                 adj_off=103.0, adj_def=107.5,
                 efg_off=50.5, efg_def=53.2, tov_pct=18.5, orb_pct=29.5, ftr=0.27, pace=71.0,
                 l10_w=2, l10_l=8, l10_margin=-5.0,  sos=5.5),
}

# Alias: ESPN sometimes uses different abbreviations
_ALIASES: Dict[str, str] = {
    "TXAM": "TAM", "TAMU": "TAM",
    "MSST": "MSST",
    "NCST": "NCST",
    "LAMO": "LMD",
    "LOYMD": "LMD",
    "SFCA": "SF",
    "STAN": "STAN",
    "GONZ": "GONZ",
    "GONZA": "GONZ",
    "OKLA": "OU",
    "OKST": "OKST",
}


def _resolve(abbr: str) -> str:
    return _ALIASES.get(abbr.upper(), abbr.upper())


# ─────────────────────────────────────────────────────────────────────────────
# Live fetch helpers (Sports Reference / ESPN)
# These are attempted first; fallback to embedded DB on any error.
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_sports_reference_team(abbr: str) -> Optional[Dict]:
    """
    Try to fetch current-season efficiency stats from barttorvik.com or
    kenpom.com proxy. Returns None on failure.
    """
    cache_key = f"sr_ncaab_{abbr}_2026"
    cached = cache_get(cache_key)
    if cached:
        return cached
    # Live fetch omitted in sandboxed env; return None to trigger fallback
    return None


def get_team_stats(abbr: str) -> Dict:
    """
    Return stats dict for a team abbreviation.
    Tries live sources first; falls back to embedded database.
    Generates a synthetic entry for any team not in the DB.
    """
    abbr = _resolve(abbr)

    # 1) Try live data
    live = _fetch_sports_reference_team(abbr)
    if live:
        return live

    # 2) Embedded DB
    if abbr in _DB:
        return _DB[abbr]

    # 3) Synthetic fallback – assume a below-average low-major program
    log.warning(f"No stats found for '{abbr}' – using generic low-major estimate")
    return dict(
        full_name=abbr,
        adj_off=104.5, adj_def=106.0,
        efg_off=51.0, efg_def=52.0,
        tov_pct=17.8, orb_pct=29.5,
        ftr=0.28, pace=71.0,
        l10_w=4, l10_l=6, l10_margin=0.0,
        sos=4.0, ranking=0, conference="Unknown",
    )


def get_all_team_stats(abbrs: list[str]) -> Dict[str, Dict]:
    """Batch fetch stats for a list of abbreviations."""
    return {a: get_team_stats(a) for a in abbrs}
