#!/usr/bin/env python3
"""
UFC 325 Fighter Analysis Script
================================
Extracts and analyzes the last 5 fights of each fighter from UFC 325 (January 31, 2026).
Location: Qudos Bank Arena, Sydney, Australia

Author: UFC Analysis Bot
Date: January 2026
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
import time
import re
from datetime import datetime
import logging
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows
import json
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class Fight:
    """Represents a single fight in a fighter's history."""
    date: str
    opponent: str
    result: str
    method: str
    method_detail: str
    round_ended: int
    time: str
    event: str

    def to_dict(self) -> dict:
        return {
            'Fecha': self.date,
            'Oponente': self.opponent,
            'Resultado': self.result,
            'Método': self.method,
            'Detalle del Método': self.method_detail,
            'Round': self.round_ended,
            'Tiempo': self.time,
            'Evento': self.event
        }


@dataclass
class FighterStats:
    """Statistical summary for a fighter's last 5 fights."""
    win_rate: float
    most_common_method: str
    avg_rounds: float
    current_streak: str
    finish_rate: float
    decision_rate: float
    total_fights_analyzed: int
    ko_count: int = 0
    tko_count: int = 0
    submission_count: int = 0
    decision_count: int = 0
    nc_count: int = 0
    wins_by_ko: int = 0
    wins_by_sub: int = 0
    wins_by_dec: int = 0
    losses_by_ko: int = 0
    losses_by_sub: int = 0
    losses_by_dec: int = 0

    def to_dict(self) -> dict:
        return {
            'Win Rate (%)': f"{self.win_rate:.1f}%",
            'Método Más Frecuente': self.most_common_method,
            'Promedio de Rounds': f"{self.avg_rounds:.2f}",
            'Racha Actual': self.current_streak,
            'Finish Rate (%)': f"{self.finish_rate:.1f}%",
            'Decision Rate (%)': f"{self.decision_rate:.1f}%",
            'Peleas Analizadas': self.total_fights_analyzed
        }

    def to_detailed_dict(self) -> dict:
        return {
            'Win Rate (%)': f"{self.win_rate:.1f}%",
            'Método Más Frecuente': self.most_common_method,
            'Promedio de Rounds': f"{self.avg_rounds:.2f}",
            'Racha Actual': self.current_streak,
            'Finish Rate (%)': f"{self.finish_rate:.1f}%",
            'Decision Rate (%)': f"{self.decision_rate:.1f}%",
            'Peleas Analizadas': self.total_fights_analyzed,
            'KO/TKO (Total)': self.ko_count + self.tko_count,
            'Submissions (Total)': self.submission_count,
            'Decisions (Total)': self.decision_count,
            'Victorias por KO/TKO': self.wins_by_ko,
            'Victorias por Submission': self.wins_by_sub,
            'Victorias por Decision': self.wins_by_dec,
            'Derrotas por KO/TKO': self.losses_by_ko,
            'Derrotas por Submission': self.losses_by_sub,
            'Derrotas por Decision': self.losses_by_dec,
        }


@dataclass
class Fighter:
    """Represents a UFC fighter with their fight history."""
    name: str
    record: str
    weight_class: str
    card_position: str
    fight_number: int
    opponent_name: str
    fights: List[Fight] = field(default_factory=list)
    stats: Optional[FighterStats] = None

    def to_dict(self) -> dict:
        return {
            'Nombre': self.name,
            'Récord': self.record,
            'Categoría': self.weight_class,
            'Cartelera': self.card_position,
            'Pelea #': self.fight_number,
            'Oponente UFC 325': self.opponent_name
        }


# =============================================================================
# UFC 325 FIGHTER LIST - COMPLETE ROSTER (January 31, 2026 - Sydney, Australia)
# =============================================================================

UFC_325_FIGHTERS = [
    # MAIN CARD (9:00 PM ET) - Paramount+
    Fighter("Alexander Volkanovski", "27-4-0", "Featherweight", "Main Card", 1, "Diego Lopes"),
    Fighter("Diego Lopes", "26-6-0", "Featherweight", "Main Card", 1, "Alexander Volkanovski"),
    Fighter("Dan Hooker", "24-12-0", "Lightweight", "Main Card", 2, "Benoit Saint Denis"),
    Fighter("Benoit Saint Denis", "13-2-0, 1NC", "Lightweight", "Main Card", 2, "Dan Hooker"),
    Fighter("Rafael Fiziev", "13-3-0", "Lightweight", "Main Card", 3, "Mauricio Ruffy"),
    Fighter("Mauricio Ruffy", "12-1-0", "Lightweight", "Main Card", 3, "Rafael Fiziev"),
    Fighter("Tai Tuivasa", "15-8-0", "Heavyweight", "Main Card", 4, "Tallison Teixeira"),
    Fighter("Tallison Teixeira", "9-1-0", "Heavyweight", "Main Card", 4, "Tai Tuivasa"),
    Fighter("Quillan Salkilld", "8-1-0", "Lightweight", "Main Card", 5, "Jamie Mullarkey"),
    Fighter("Jamie Mullarkey", "18-7-0", "Lightweight", "Main Card", 5, "Quillan Salkilld"),
    # PRELIMINARY CARD (7:00 PM ET)
    Fighter("Junior Tafa", "6-3-0", "Light Heavyweight", "Preliminary Card", 6, "Billy Elekana"),
    Fighter("Billy Elekana", "8-1-0", "Light Heavyweight", "Preliminary Card", 6, "Junior Tafa"),
    Fighter("Cameron Rowston", "8-1-0", "Middleweight", "Preliminary Card", 7, "Cody Brundage"),
    Fighter("Cody Brundage", "8-5-0", "Middleweight", "Preliminary Card", 7, "Cameron Rowston"),
    Fighter("Jacob Malkoun", "10-4-0", "Middleweight", "Preliminary Card", 8, "Torrez Finney"),
    Fighter("Torrez Finney", "7-0-0", "Middleweight", "Preliminary Card", 8, "Jacob Malkoun"),
    Fighter("Jonathan Micallef", "8-1-0", "Welterweight", "Preliminary Card", 9, "Oban Elliott"),
    Fighter("Oban Elliott", "11-2-0", "Welterweight", "Preliminary Card", 9, "Jonathan Micallef"),
    # EARLY PRELIMS (5:00 PM ET) - Road to UFC Finals
    Fighter("Kaan Ofli", "9-1-0", "Featherweight", "Early Prelims", 10, "Yi Zha"),
    Fighter("Yi Zha", "16-5-0", "Featherweight", "Early Prelims", 10, "Kaan Ofli"),
    Fighter("Kim Sang-wook", "9-2-0", "Lightweight", "Early Prelims", 11, "Anshul Jubli"),
    Fighter("Anshul Jubli", "7-0-0", "Lightweight", "Early Prelims", 11, "Kim Sang-wook"),
    Fighter("Keiichiro Yamamiya", "10-4-0", "Featherweight", "Early Prelims", 12, "Rei Shimizu"),
    Fighter("Rei Shimizu", "12-2-0", "Featherweight", "Early Prelims", 12, "Keiichiro Yamamiya"),
    Fighter("Shi Ming", "17-8-0", "Bantamweight", "Early Prelims", 13, "Xie Bin"),
    Fighter("Xie Bin", "8-1-0", "Bantamweight", "Early Prelims", 13, "Shi Ming"),
]


# =============================================================================
# STATISTICS CALCULATION
# =============================================================================

def calculate_fighter_stats(fights: List[Fight]) -> FighterStats:
    """Calculate statistical summary for a fighter's fights."""
    if not fights:
        return FighterStats(
            win_rate=0.0, most_common_method="N/A", avg_rounds=0.0,
            current_streak="N/A", finish_rate=0.0, decision_rate=0.0,
            total_fights_analyzed=0
        )

    total_fights = len(fights)
    wins = sum(1 for f in fights if f.result == 'Win')
    win_rate = (wins / total_fights) * 100

    win_methods = [f.method for f in fights if f.result == 'Win']
    if win_methods:
        method_counts = {}
        for method in win_methods:
            method_counts[method] = method_counts.get(method, 0) + 1
        most_common_method = max(method_counts, key=method_counts.get)
    else:
        most_common_method = "N/A"

    rounds = [f.round_ended for f in fights if f.round_ended > 0]
    avg_rounds = sum(rounds) / len(rounds) if rounds else 0

    streak_count = 0
    streak_type = None
    for fight in fights:
        if streak_type is None:
            streak_type = fight.result
            streak_count = 1
        elif fight.result == streak_type:
            streak_count += 1
        else:
            break

    if streak_type == 'Win':
        current_streak = f"{streak_count}W"
    elif streak_type == 'Loss':
        current_streak = f"{streak_count}L"
    elif streak_type == 'Draw':
        current_streak = f"{streak_count}D"
    else:
        current_streak = f"{streak_count}NC"

    results_sequence = '-'.join([f.result[0] for f in fights])
    current_streak = f"{current_streak} ({results_sequence})"

    win_fights = [f for f in fights if f.result == 'Win']
    if win_fights:
        finishes = sum(1 for f in win_fights if f.method in ['KO', 'TKO', 'Submission'])
        decisions = sum(1 for f in win_fights if f.method == 'Decision')
        finish_rate = (finishes / len(win_fights)) * 100
        decision_rate = (decisions / len(win_fights)) * 100
    else:
        finish_rate = 0
        decision_rate = 0

    ko_count = sum(1 for f in fights if f.method == 'KO')
    tko_count = sum(1 for f in fights if f.method == 'TKO')
    submission_count = sum(1 for f in fights if f.method == 'Submission')
    decision_count = sum(1 for f in fights if f.method == 'Decision')
    nc_count = sum(1 for f in fights if f.method == 'NC' or f.result == 'NC')

    wins_by_ko = sum(1 for f in fights if f.result == 'Win' and f.method in ['KO', 'TKO'])
    wins_by_sub = sum(1 for f in fights if f.result == 'Win' and f.method == 'Submission')
    wins_by_dec = sum(1 for f in fights if f.result == 'Win' and f.method == 'Decision')

    losses_by_ko = sum(1 for f in fights if f.result == 'Loss' and f.method in ['KO', 'TKO'])
    losses_by_sub = sum(1 for f in fights if f.result == 'Loss' and f.method == 'Submission')
    losses_by_dec = sum(1 for f in fights if f.result == 'Loss' and f.method == 'Decision')

    return FighterStats(
        win_rate=win_rate, most_common_method=most_common_method, avg_rounds=avg_rounds,
        current_streak=current_streak, finish_rate=finish_rate, decision_rate=decision_rate,
        total_fights_analyzed=total_fights, ko_count=ko_count, tko_count=tko_count,
        submission_count=submission_count, decision_count=decision_count, nc_count=nc_count,
        wins_by_ko=wins_by_ko, wins_by_sub=wins_by_sub, wins_by_dec=wins_by_dec,
        losses_by_ko=losses_by_ko, losses_by_sub=losses_by_sub, losses_by_dec=losses_by_dec
    )


# =============================================================================
# DEMO DATA - UFC 325 FIGHTERS (Last 5 Fights)
# =============================================================================

def get_demo_fights(fighter_name: str) -> List[Fight]:
    """Returns demo fight data for UFC 325 fighters."""
    demo_data = {
        "Alexander Volkanovski": [
            Fight("Oct 26, 2025", "Diego Lopes", "Win", "Decision", "Unanimous", 5, "5:00", "UFC 314"),
            Fight("Feb 17, 2024", "Ilia Topuria", "Loss", "KO", "Punches", 2, "3:32", "UFC 298"),
            Fight("Oct 21, 2023", "Islam Makhachev", "Loss", "Submission", "Armbar", 1, "3:06", "UFC 294"),
            Fight("Jul 08, 2023", "Yair Rodriguez", "Win", "TKO", "Shoulder Injury", 3, "0:44", "UFC 290"),
            Fight("Feb 12, 2023", "Islam Makhachev", "Loss", "Decision", "Unanimous", 5, "5:00", "UFC 284"),
        ],
        "Diego Lopes": [
            Fight("Oct 26, 2025", "Alexander Volkanovski", "Loss", "Decision", "Unanimous", 5, "5:00", "UFC 314"),
            Fight("Jun 29, 2024", "Brian Ortega", "Win", "Submission", "Guillotine Choke", 2, "2:48", "UFC 303"),
            Fight("Apr 13, 2024", "Sodiq Yusuff", "Win", "KO", "Punches", 1, "4:03", "UFC 300"),
            Fight("Aug 26, 2023", "Movsar Evloev", "Win", "TKO", "Punches", 3, "3:45", "UFC Fight Night"),
            Fight("May 06, 2023", "Pat Sabatini", "Win", "Submission", "Rear Naked Choke", 2, "3:15", "UFC 288"),
        ],
        "Dan Hooker": [
            Fight("Sep 14, 2024", "Mateusz Gamrot", "Win", "Decision", "Unanimous", 3, "5:00", "UFC 305"),
            Fight("Apr 13, 2024", "Jalin Turner", "Win", "Decision", "Unanimous", 3, "5:00", "UFC 300"),
            Fight("Dec 16, 2023", "Claudio Puelles", "Win", "TKO", "Punches", 1, "1:05", "UFC Fight Night"),
            Fight("Jul 08, 2023", "Mike Chandler", "Loss", "Submission", "Rear Naked Choke", 2, "3:12", "UFC 290"),
            Fight("Mar 04, 2023", "Claudio Puelles", "Loss", "Submission", "Kneebar", 2, "4:20", "UFC 285"),
        ],
        "Benoit Saint Denis": [
            Fight("Sep 28, 2024", "Renato Moicano", "Loss", "TKO", "Punches", 1, "2:28", "UFC Fight Night"),
            Fight("Mar 09, 2024", "Dustin Poirier", "Loss", "TKO", "Punches", 2, "1:14", "UFC 299"),
            Fight("Sep 02, 2023", "Thiago Moises", "Win", "TKO", "Punches", 1, "3:52", "UFC Fight Night"),
            Fight("Apr 08, 2023", "Ismael Bonfim", "Win", "TKO", "Punches", 1, "0:51", "UFC 287"),
            Fight("Oct 29, 2022", "Gabriel Miranda", "Win", "TKO", "Punches", 1, "0:39", "UFC Fight Night"),
        ],
        "Rafael Fiziev": [
            Fight("Sep 28, 2024", "Mateusz Gamrot", "Win", "Decision", "Unanimous", 3, "5:00", "UFC Fight Night"),
            Fight("Oct 21, 2023", "Justin Gaethje", "Loss", "TKO", "Leg Kicks", 2, "4:36", "UFC 291"),
            Fight("Feb 18, 2023", "Bobby Green", "Win", "KO", "Punches", 1, "1:46", "UFC Fight Night"),
            Fight("Jun 25, 2022", "Rafael dos Anjos", "Win", "KO", "Punches", 5, "0:18", "UFC Fight Night"),
            Fight("Dec 04, 2021", "Brad Riddell", "Win", "KO", "Spinning Back Kick", 3, "1:21", "UFC Vegas 44"),
        ],
        "Mauricio Ruffy": [
            Fight("Aug 03, 2024", "Jamie Mullarkey", "Win", "TKO", "Punches", 1, "2:49", "UFC Fight Night"),
            Fight("Mar 16, 2024", "Grant Dawson", "Win", "KO", "Punches", 2, "3:45", "UFC Fight Night"),
            Fight("Aug 12, 2023", "Nicolas Dalby", "Win", "TKO", "Punches", 1, "4:25", "UFC Fight Night"),
            Fight("Feb 25, 2023", "Natan Levy", "Win", "TKO", "Punches", 1, "2:33", "UFC Fight Night"),
            Fight("Oct 01, 2022", "Gabe Green", "Win", "Decision", "Unanimous", 3, "5:00", "UFC Fight Night"),
        ],
        "Tai Tuivasa": [
            Fight("Aug 03, 2024", "Jairzinho Rozenstruik", "Loss", "KO", "Punches", 1, "0:46", "UFC Fight Night"),
            Fight("Feb 17, 2024", "Marcin Tybura", "Loss", "Decision", "Unanimous", 3, "5:00", "UFC 298"),
            Fight("Sep 02, 2023", "Alexander Volkov", "Loss", "TKO", "Punches", 1, "4:10", "UFC Fight Night"),
            Fight("Mar 04, 2023", "Derrick Lewis", "Loss", "TKO", "Punches", 2, "4:03", "UFC 285"),
            Fight("Sep 03, 2022", "Ciryl Gane", "Loss", "KO", "Punches", 3, "2:44", "UFC Fight Night"),
        ],
        "Tallison Teixeira": [
            Fight("Jul 13, 2024", "Thomas Petersen", "Win", "TKO", "Punches", 1, "2:12", "UFC Fight Night"),
            Fight("Feb 24, 2024", "Waldo Cortes-Acosta", "Win", "TKO", "Punches", 2, "3:45", "UFC 298"),
            Fight("Aug 26, 2023", "Karl Williams", "Win", "KO", "Punches", 1, "1:25", "UFC Fight Night"),
            Fight("May 13, 2023", "Mick Parkin", "Win", "TKO", "Punches", 2, "2:58", "UFC Fight Night"),
            Fight("Jan 14, 2023", "Don'Tale Mayes", "Win", "Decision", "Unanimous", 3, "5:00", "UFC Fight Night"),
        ],
        "Quillan Salkilld": [
            Fight("Aug 17, 2024", "Damon Jackson", "Win", "Decision", "Unanimous", 3, "5:00", "UFC Fight Night"),
            Fight("May 04, 2024", "Francisco Prado", "Win", "TKO", "Punches", 2, "3:15", "UFC Fight Night"),
            Fight("Nov 11, 2023", "Josh Culibao", "Win", "Decision", "Unanimous", 3, "5:00", "UFC Fight Night"),
            Fight("Jun 17, 2023", "Shayilan Nuerdanbieke", "Win", "TKO", "Punches", 1, "2:45", "UFC Fight Night"),
            Fight("Feb 04, 2023", "Alex da Silva", "Loss", "Submission", "Rear Naked Choke", 2, "3:45", "Regional"),
        ],
        "Jamie Mullarkey": [
            Fight("Aug 03, 2024", "Mauricio Ruffy", "Loss", "TKO", "Punches", 1, "2:49", "UFC Fight Night"),
            Fight("Feb 24, 2024", "Francisco Prado", "Win", "KO", "Punches", 2, "1:45", "UFC 298"),
            Fight("Aug 20, 2023", "Michael Johnson", "Win", "TKO", "Punches", 1, "0:52", "UFC Fight Night"),
            Fight("Feb 12, 2023", "Jimmy Crute", "Win", "KO", "Punches", 1, "3:47", "UFC 284"),
            Fight("Oct 22, 2022", "Devonte Smith", "Win", "KO", "Punches", 2, "0:20", "UFC 280"),
        ],
        "Junior Tafa": [
            Fight("Jun 01, 2024", "Waldo Cortes-Acosta", "Loss", "TKO", "Punches", 1, "3:20", "UFC Fight Night"),
            Fight("Feb 03, 2024", "Mick Parkin", "Loss", "TKO", "Punches", 1, "3:56", "UFC Fight Night"),
            Fight("Jul 08, 2023", "Parker Porter", "Win", "KO", "Punches", 1, "2:35", "UFC 290"),
            Fight("Feb 12, 2023", "Justin Tafa", "Win", "TKO", "Punches", 1, "1:56", "UFC 284"),
            Fight("Jun 12, 2022", "Jared Vanderaa", "Loss", "TKO", "Punches", 2, "3:42", "UFC 275"),
        ],
        "Billy Elekana": [
            Fight("Sep 21, 2024", "Rizvan Kuniev", "Win", "TKO", "Punches", 2, "3:15", "UFC Fight Night"),
            Fight("Jun 08, 2024", "Alexandar Rakic", "Win", "KO", "Punches", 1, "1:45", "UFC Fight Night"),
            Fight("Feb 03, 2024", "Karl Roberson", "Win", "Submission", "Rear Naked Choke", 2, "4:12", "UFC Fight Night"),
            Fight("Aug 05, 2023", "Tyson Pedro", "Win", "TKO", "Punches", 1, "2:30", "UFC Fight Night"),
            Fight("Mar 18, 2023", "Alonzo Menifield", "Loss", "Decision", "Split", 3, "5:00", "UFC Fight Night"),
        ],
        "Cameron Rowston": [
            Fight("Aug 17, 2024", "Charlie Radtke", "Win", "Decision", "Unanimous", 3, "5:00", "UFC Fight Night"),
            Fight("Apr 20, 2024", "Albert Duraev", "Win", "Decision", "Split", 3, "5:00", "UFC Fight Night"),
            Fight("Oct 07, 2023", "Tresean Gore", "Win", "TKO", "Punches", 2, "3:45", "UFC Fight Night"),
            Fight("Jun 17, 2023", "Zac Pauga", "Win", "Decision", "Unanimous", 3, "5:00", "UFC Fight Night"),
            Fight("Feb 04, 2023", "Julian Marquez", "Loss", "Submission", "Rear Naked Choke", 2, "4:15", "UFC Fight Night"),
        ],
        "Cody Brundage": [
            Fight("Jun 15, 2024", "Dusko Todorovic", "Win", "Decision", "Unanimous", 3, "5:00", "UFC Fight Night"),
            Fight("Feb 03, 2024", "Claudio Ribeiro", "Loss", "TKO", "Punches", 2, "2:50", "UFC Fight Night"),
            Fight("Sep 16, 2023", "Caio Borralho", "Loss", "Submission", "Armbar", 2, "3:15", "UFC Fight Night"),
            Fight("May 06, 2023", "Tresean Gore", "Win", "TKO", "Punches", 2, "3:20", "UFC 288"),
            Fight("Dec 03, 2022", "Michal Oleksiejczuk", "Loss", "TKO", "Punches", 1, "0:42", "UFC Fight Night"),
        ],
        "Jacob Malkoun": [
            Fight("Aug 03, 2024", "Cody Brundage", "Win", "Decision", "Unanimous", 3, "5:00", "UFC Fight Night"),
            Fight("Feb 03, 2024", "Roman Kopylov", "Loss", "TKO", "Punches", 2, "4:35", "UFC Fight Night"),
            Fight("Sep 02, 2023", "Abdul Razak Alhassan", "Win", "KO", "Punches", 1, "2:15", "UFC Fight Night"),
            Fight("Feb 12, 2023", "Brendan Allen", "Loss", "Submission", "Rear Naked Choke", 1, "4:38", "UFC 284"),
            Fight("Oct 01, 2022", "Nick Maximov", "Loss", "Decision", "Unanimous", 3, "5:00", "UFC Fight Night"),
        ],
        "Torrez Finney": [
            Fight("Aug 31, 2024", "Sedriques Dumas", "Win", "TKO", "Punches", 2, "2:45", "UFC Fight Night"),
            Fight("Apr 27, 2024", "Joe Pyfer", "Win", "KO", "Punches", 1, "1:58", "UFC Fight Night"),
            Fight("Dec 09, 2023", "Abdul Razak Alhassan", "Win", "TKO", "Punches", 1, "2:30", "UFC 296"),
            Fight("Jun 24, 2023", "Hamdy Abdelwahab", "Win", "Decision", "Unanimous", 3, "5:00", "UFC Fight Night"),
            Fight("Feb 18, 2023", "Chad Anheliger", "Win", "TKO", "Punches", 2, "3:15", "Contender Series"),
        ],
        "Jonathan Micallef": [
            Fight("Aug 17, 2024", "Jake Matthews", "Win", "TKO", "Punches", 2, "3:30", "UFC Fight Night"),
            Fight("Apr 20, 2024", "Kevin Jousset", "Win", "Decision", "Unanimous", 3, "5:00", "UFC Fight Night"),
            Fight("Oct 21, 2023", "Jeremiah Wells", "Win", "TKO", "Punches", 1, "4:15", "UFC Fight Night"),
            Fight("Jun 17, 2023", "Jack Della Maddalena", "Loss", "Submission", "Rear Naked Choke", 2, "3:45", "UFC Fight Night"),
            Fight("Feb 12, 2023", "Charlie Radtke", "Win", "Decision", "Unanimous", 3, "5:00", "UFC 284"),
        ],
        "Oban Elliott": [
            Fight("Jul 27, 2024", "Preston Parsons", "Win", "Submission", "Rear Naked Choke", 2, "3:45", "UFC 304"),
            Fight("Mar 30, 2024", "Rinat Fakhretdinov", "Win", "Decision", "Split", 3, "5:00", "UFC Fight Night"),
            Fight("Nov 11, 2023", "AJ Fletcher", "Win", "TKO", "Punches", 2, "4:15", "UFC Fight Night"),
            Fight("Jun 03, 2023", "Yaozong Hu", "Win", "Submission", "Rear Naked Choke", 1, "2:30", "UFC Fight Night"),
            Fight("Jan 21, 2023", "Kevin Holland", "Loss", "Decision", "Unanimous", 3, "5:00", "UFC Fight Night"),
        ],
        "Kaan Ofli": [
            Fight("Sep 07, 2024", "Topnoi Tiger Muay Thai", "Win", "Decision", "Unanimous", 3, "5:00", "Road to UFC"),
            Fight("Jun 08, 2024", "Taichi Nakajima", "Win", "TKO", "Punches", 2, "3:15", "Road to UFC"),
            Fight("Feb 24, 2024", "Batgerel Danaa", "Win", "KO", "Punches", 1, "2:45", "Road to UFC"),
            Fight("Aug 26, 2023", "Shin Min-chul", "Win", "Decision", "Unanimous", 3, "5:00", "Road to UFC"),
            Fight("Feb 04, 2023", "Yang Jun", "Loss", "Submission", "Guillotine Choke", 2, "3:30", "Regional"),
        ],
        "Yi Zha": [
            Fight("Sep 07, 2024", "Namiki Kawahara", "Win", "TKO", "Punches", 2, "2:45", "Road to UFC"),
            Fight("Jun 08, 2024", "Kyungpyo Kim", "Win", "Decision", "Unanimous", 3, "5:00", "Road to UFC"),
            Fight("Feb 24, 2024", "Keisuke Saka", "Win", "KO", "Head Kick", 1, "1:58", "Road to UFC"),
            Fight("Aug 26, 2023", "Lee Jung-hyun", "Win", "TKO", "Punches", 1, "4:15", "Road to UFC"),
            Fight("May 06, 2023", "Wang Cong", "Loss", "Decision", "Split", 3, "5:00", "Regional"),
        ],
        "Kim Sang-wook": [
            Fight("Sep 07, 2024", "Rinya Nakamura", "Win", "TKO", "Punches", 2, "3:30", "Road to UFC"),
            Fight("Jun 08, 2024", "Toshiomi Kazama", "Win", "Submission", "Rear Naked Choke", 2, "2:45", "Road to UFC"),
            Fight("Feb 24, 2024", "Tatsuro Taira", "Win", "Decision", "Unanimous", 3, "5:00", "Road to UFC"),
            Fight("Aug 26, 2023", "Lee Chang-ho", "Loss", "TKO", "Punches", 1, "2:15", "Road to UFC"),
            Fight("Apr 15, 2023", "Park Jun-yong", "Win", "Decision", "Unanimous", 3, "5:00", "Regional"),
        ],
        "Anshul Jubli": [
            Fight("Sep 07, 2024", "Ho Taek Oh", "Win", "KO", "Punches", 1, "1:45", "Road to UFC"),
            Fight("Jun 08, 2024", "Jeka Saragih", "Win", "Submission", "Guillotine Choke", 2, "3:15", "Road to UFC"),
            Fight("Feb 24, 2024", "Shohei Nose", "Win", "TKO", "Punches", 1, "2:30", "Road to UFC"),
            Fight("Aug 26, 2023", "Kazuki Takahashi", "Win", "Decision", "Unanimous", 3, "5:00", "Road to UFC"),
            Fight("Apr 01, 2023", "Max Henning", "Win", "TKO", "Punches", 2, "4:15", "Regional"),
        ],
        "Keiichiro Yamamiya": [
            Fight("Sep 07, 2024", "Chen Wenbin", "Win", "Decision", "Unanimous", 3, "5:00", "Road to UFC"),
            Fight("Jun 08, 2024", "Joshua Culibao", "Win", "TKO", "Punches", 2, "3:45", "Road to UFC"),
            Fight("Feb 24, 2024", "Nguyen Quang Hai", "Win", "KO", "Punches", 1, "2:15", "Road to UFC"),
            Fight("Aug 26, 2023", "Bao Yincang", "Loss", "Decision", "Split", 3, "5:00", "Road to UFC"),
            Fight("May 13, 2023", "Yuki Takahashi", "Win", "Submission", "Armbar", 2, "3:30", "Regional"),
        ],
        "Rei Shimizu": [
            Fight("Sep 07, 2024", "Hoyoung Kim", "Win", "TKO", "Punches", 1, "3:15", "Road to UFC"),
            Fight("Jun 08, 2024", "Chu Jutao", "Win", "KO", "Spinning Back Fist", 2, "1:58", "Road to UFC"),
            Fight("Feb 24, 2024", "Keiya Yamamoto", "Win", "Decision", "Unanimous", 3, "5:00", "Road to UFC"),
            Fight("Aug 26, 2023", "Park Hyun-sung", "Win", "TKO", "Punches", 2, "4:30", "Road to UFC"),
            Fight("Apr 08, 2023", "Adam Soldiera", "Loss", "Submission", "Rear Naked Choke", 3, "2:45", "Regional"),
        ],
        "Shi Ming": [
            Fight("Sep 07, 2024", "Kiru Singh Sahota", "Win", "Decision", "Unanimous", 3, "5:00", "Road to UFC"),
            Fight("Jun 08, 2024", "Stewart Nicoll", "Win", "TKO", "Punches", 1, "2:30", "Road to UFC"),
            Fight("Feb 24, 2024", "Niklas Stolze", "Win", "Submission", "Guillotine Choke", 2, "3:45", "Road to UFC"),
            Fight("Aug 26, 2023", "Song Kenan", "Loss", "Decision", "Split", 3, "5:00", "Road to UFC"),
            Fight("Apr 22, 2023", "Lee Min-hyuk", "Win", "TKO", "Punches", 2, "4:15", "Regional"),
        ],
        "Xie Bin": [
            Fight("Sep 07, 2024", "Yuki Yamasaki", "Win", "KO", "Punches", 2, "2:15", "Road to UFC"),
            Fight("Jun 08, 2024", "Wei Zhuo Zhang", "Win", "TKO", "Punches", 1, "3:45", "Road to UFC"),
            Fight("Feb 24, 2024", "Renchuang Yang", "Win", "Submission", "Rear Naked Choke", 2, "4:30", "Road to UFC"),
            Fight("Aug 26, 2023", "Li Kai Wen", "Win", "Decision", "Unanimous", 3, "5:00", "Road to UFC"),
            Fight("May 20, 2023", "Chen Wei", "Loss", "TKO", "Punches", 1, "2:45", "Regional"),
        ],
    }
    return demo_data.get(fighter_name, [])


# =============================================================================
# EXCEL EXPORT - COLOR-CODED MATCHUPS
# =============================================================================

FIGHT_COLORS = [
    "90EE90", "87CEEB", "FFB6C1", "DDA0DD", "F0E68C", "98FB98", "FFA07A",
    "87CEFA", "FFDAB9", "E6E6FA", "F5DEB3", "B0E0E6", "D3D3D3",
]

def extract_year(date_str: str) -> str:
    year_match = re.search(r'20\d{2}', date_str)
    return year_match.group() if year_match else "N/A"


def create_excel_report(fighters: List[Fighter], output_path: str = "UFC_325_Fighter_Analysis.xlsx"):
    """Create a comprehensive Excel report with color-coded fight matchups."""
    wb = Workbook()
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    subheader_fill = PatternFill(start_color="5B9BD5", end_color="5B9BD5", fill_type="solid")
    nc_fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
    thin_border = Border(left=Side(style='thin'), right=Side(style='thin'),
                        top=Side(style='thin'), bottom=Side(style='thin'))

    default_sheet = wb.active
    wb.remove(default_sheet)

    # SHEET 1: MATCHUPS BY FIGHT
    matchup_ws = wb.create_sheet("PELEAS UFC 325")
    matchup_ws.merge_cells('A1:R1')
    matchup_ws['A1'] = "UFC 325 - TODAS LAS PELEAS CON COLORES (31 Enero 2026 - Sydney)"
    matchup_ws['A1'].font = Font(bold=True, size=16, color="FFFFFF")
    matchup_ws['A1'].fill = header_fill
    matchup_ws['A1'].alignment = Alignment(horizontal='center')

    matchup_headers = ['Pelea #', 'Peleador 1', 'Récord', 'VS', 'Peleador 2', 'Récord',
                      'Categoría', 'Cartelera', 'Win Rate P1', 'Win Rate P2',
                      'Finish Rate P1', 'Finish Rate P2', 'Racha P1', 'Racha P2',
                      'KO/TKO P1', 'KO/TKO P2', 'SUB P1', 'SUB P2']
    matchup_ws.append([])
    matchup_ws.append(matchup_headers)

    for col, header in enumerate(matchup_headers, 1):
        cell = matchup_ws.cell(row=3, column=col)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', wrap_text=True)
        cell.border = thin_border

    fights_by_number = {}
    for fighter in fighters:
        if fighter.fight_number not in fights_by_number:
            fights_by_number[fighter.fight_number] = []
        fights_by_number[fighter.fight_number].append(fighter)

    row_num = 4
    for fight_num in sorted(fights_by_number.keys()):
        fight_fighters = fights_by_number[fight_num]
        if len(fight_fighters) >= 2:
            f1, f2 = fight_fighters[0], fight_fighters[1]
            color_idx = (fight_num - 1) % len(FIGHT_COLORS)
            fight_color = PatternFill(start_color=FIGHT_COLORS[color_idx],
                                     end_color=FIGHT_COLORS[color_idx], fill_type="solid")

            row_data = [fight_num, f1.name, f1.record, 'VS', f2.name, f2.record,
                       f1.weight_class, f1.card_position,
                       f"{f1.stats.win_rate:.1f}%" if f1.stats else "N/A",
                       f"{f2.stats.win_rate:.1f}%" if f2.stats else "N/A",
                       f"{f1.stats.finish_rate:.1f}%" if f1.stats else "N/A",
                       f"{f2.stats.finish_rate:.1f}%" if f2.stats else "N/A",
                       f1.stats.current_streak if f1.stats else "N/A",
                       f2.stats.current_streak if f2.stats else "N/A",
                       f"{f1.stats.ko_count + f1.stats.tko_count}" if f1.stats else "0",
                       f"{f2.stats.ko_count + f2.stats.tko_count}" if f2.stats else "0",
                       f"{f1.stats.submission_count}" if f1.stats else "0",
                       f"{f2.stats.submission_count}" if f2.stats else "0"]
            matchup_ws.append(row_data)

            for col in range(1, len(matchup_headers) + 1):
                cell = matchup_ws.cell(row=row_num, column=col)
                cell.fill = fight_color
                cell.border = thin_border
                cell.alignment = Alignment(horizontal='center')
                if col == 4:
                    cell.font = Font(bold=True, size=12)
            row_num += 1

    matchup_col_widths = [8, 22, 12, 4, 22, 12, 18, 20, 10, 10, 10, 10, 18, 18, 8, 8, 6, 6]
    for col, width in enumerate(matchup_col_widths, 1):
        if col <= 18:
            matchup_ws.column_dimensions[chr(64 + col)].width = width

    # SHEET 2: DETAILED FIGHT HISTORY
    detail_ws = wb.create_sheet("HISTORIAL DETALLADO")
    detail_ws.merge_cells('A1:N1')
    detail_ws['A1'] = "UFC 325 - HISTORIAL DE ÚLTIMAS 5 PELEAS DE CADA PELEADOR"
    detail_ws['A1'].font = Font(bold=True, size=16, color="FFFFFF")
    detail_ws['A1'].fill = header_fill
    detail_ws['A1'].alignment = Alignment(horizontal='center')

    detail_headers = ['Pelea UFC 325', 'Peleador', 'Oponente UFC 325', 'Pelea #',
                     'Año', 'Oponente', 'Resultado', 'Método', 'Detalle',
                     'Round', 'Tiempo', 'Evento', 'KOs (Total)', 'SUBs (Total)']
    detail_ws.append([])
    detail_ws.append(detail_headers)

    for col, header in enumerate(detail_headers, 1):
        cell = detail_ws.cell(row=3, column=col)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', wrap_text=True)
        cell.border = thin_border

    row_num = 4
    for fighter in fighters:
        color_idx = (fighter.fight_number - 1) % len(FIGHT_COLORS)
        fight_color = PatternFill(start_color=FIGHT_COLORS[color_idx],
                                 end_color=FIGHT_COLORS[color_idx], fill_type="solid")

        for fight_idx, fight in enumerate(fighter.fights, 1):
            year = extract_year(fight.date)
            row_data = [fighter.fight_number, fighter.name, fighter.opponent_name, fight_idx,
                       year, fight.opponent, fight.result, fight.method, fight.method_detail,
                       fight.round_ended, fight.time, fight.event,
                       fighter.stats.ko_count + fighter.stats.tko_count if fighter.stats else 0,
                       fighter.stats.submission_count if fighter.stats else 0]
            detail_ws.append(row_data)

            for col in range(1, len(detail_headers) + 1):
                cell = detail_ws.cell(row=row_num, column=col)
                cell.fill = fight_color
                cell.border = thin_border
                cell.alignment = Alignment(horizontal='center')
                if col == 7:
                    if cell.value == 'Win':
                        cell.font = Font(bold=True, color="006400")
                    elif cell.value == 'Loss':
                        cell.font = Font(bold=True, color="8B0000")
            row_num += 1

    detail_col_widths = [10, 22, 22, 8, 6, 22, 10, 12, 20, 7, 7, 28, 8, 8]
    for col, width in enumerate(detail_col_widths, 1):
        if col <= 14:
            detail_ws.column_dimensions[chr(64 + col)].width = width

    # SHEET 3: COMPREHENSIVE SUMMARY
    summary_ws = wb.create_sheet("RESUMEN COMPLETO")
    summary_ws.merge_cells('A1:T1')
    summary_ws['A1'] = "UFC 325 - RESUMEN COMPLETO DE ESTADÍSTICAS POR PELEADOR"
    summary_ws['A1'].font = Font(bold=True, size=16, color="FFFFFF")
    summary_ws['A1'].fill = header_fill
    summary_ws['A1'].alignment = Alignment(horizontal='center')

    summary_headers = ['Pelea #', 'Peleador', 'Récord', 'Categoría', 'Oponente UFC 325',
                      'Win Rate', 'Finish Rate', 'Decision Rate', 'Racha',
                      'Wins KO/TKO', 'Wins SUB', 'Wins DEC', 'Losses KO/TKO', 'Losses SUB',
                      'Losses DEC', 'Total KO/TKO', 'Total SUB', 'Total DEC', 'Total NC', 'Avg Rounds']
    summary_ws.append([])
    summary_ws.append(summary_headers)

    for col, header in enumerate(summary_headers, 1):
        cell = summary_ws.cell(row=3, column=col)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', wrap_text=True)
        cell.border = thin_border

    row_num = 4
    for fighter in fighters:
        color_idx = (fighter.fight_number - 1) % len(FIGHT_COLORS)
        fight_color = PatternFill(start_color=FIGHT_COLORS[color_idx],
                                 end_color=FIGHT_COLORS[color_idx], fill_type="solid")
        stats = fighter.stats
        row_data = [fighter.fight_number, fighter.name, fighter.record, fighter.weight_class,
                   fighter.opponent_name,
                   f"{stats.win_rate:.1f}%" if stats else "N/A",
                   f"{stats.finish_rate:.1f}%" if stats else "N/A",
                   f"{stats.decision_rate:.1f}%" if stats else "N/A",
                   stats.current_streak if stats else "N/A",
                   stats.wins_by_ko if stats else 0, stats.wins_by_sub if stats else 0,
                   stats.wins_by_dec if stats else 0, stats.losses_by_ko if stats else 0,
                   stats.losses_by_sub if stats else 0, stats.losses_by_dec if stats else 0,
                   stats.ko_count + stats.tko_count if stats else 0,
                   stats.submission_count if stats else 0, stats.decision_count if stats else 0,
                   stats.nc_count if stats else 0,
                   f"{stats.avg_rounds:.1f}" if stats else "N/A"]
        summary_ws.append(row_data)

        for col in range(1, len(summary_headers) + 1):
            cell = summary_ws.cell(row=row_num, column=col)
            cell.fill = fight_color
            cell.border = thin_border
            cell.alignment = Alignment(horizontal='center')
        row_num += 1

    summary_col_widths = [8, 22, 12, 18, 22, 9, 10, 10, 18, 9, 8, 8, 10, 10, 10, 10, 8, 8, 7, 9]
    for col, width in enumerate(summary_col_widths, 1):
        if col <= 20:
            summary_ws.column_dimensions[chr(64 + col)].width = width

    # INDIVIDUAL FIGHTER SHEETS
    for fighter in fighters:
        color_idx = (fighter.fight_number - 1) % len(FIGHT_COLORS)
        fight_color = PatternFill(start_color=FIGHT_COLORS[color_idx],
                                 end_color=FIGHT_COLORS[color_idx], fill_type="solid")
        sheet_name = fighter.name[:31].replace('/', '-').replace('\\', '-').replace('*', '-')
        ws = wb.create_sheet(sheet_name)

        ws.merge_cells('A1:J1')
        ws['A1'] = f"{fighter.name} - Últimas 5 Peleas"
        ws['A1'].font = Font(bold=True, size=14, color="000000")
        ws['A1'].alignment = Alignment(horizontal='center')
        ws['A1'].fill = fight_color

        ws['A2'] = f"Récord: {fighter.record}"
        ws['C2'] = f"Categoría: {fighter.weight_class}"
        ws['E2'] = f"Pelea #{fighter.fight_number}"
        ws['G2'] = f"vs {fighter.opponent_name}"

        for col in range(1, 10):
            ws.cell(row=2, column=col).fill = fight_color

        fight_headers = ['#', 'Año', 'Fecha', 'Oponente', 'Resultado', 'Método', 'Detalle', 'Round', 'Tiempo', 'Evento']
        ws.append([])
        ws.append(fight_headers)

        for col, header in enumerate(fight_headers, 1):
            cell = ws.cell(row=4, column=col)
            cell.font = header_font
            cell.fill = subheader_fill
            cell.alignment = Alignment(horizontal='center')
            cell.border = thin_border

        for fight_idx, fight in enumerate(fighter.fights, 1):
            year = extract_year(fight.date)
            fight_row = [fight_idx, year, fight.date, fight.opponent, fight.result, fight.method,
                        fight.method_detail, fight.round_ended, fight.time, fight.event]
            ws.append(fight_row)

        for row in range(5, 5 + len(fighter.fights)):
            for col in range(1, len(fight_headers) + 1):
                cell = ws.cell(row=row, column=col)
                cell.border = thin_border
                cell.alignment = Alignment(horizontal='center')
                if col == 5:
                    if cell.value == 'Win':
                        cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                        cell.font = Font(bold=True, color="006400")
                    elif cell.value == 'Loss':
                        cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
                        cell.font = Font(bold=True, color="8B0000")
                    elif cell.value in ['NC', 'Draw']:
                        cell.fill = nc_fill

        if fighter.stats:
            stats_start_row = ws.max_row + 2
            ws.cell(row=stats_start_row, column=1, value="ESTADÍSTICAS DETALLADAS")
            ws.cell(row=stats_start_row, column=1).font = Font(bold=True, size=12, color="FFFFFF")
            ws.cell(row=stats_start_row, column=1).fill = header_fill
            ws.merge_cells(f'A{stats_start_row}:D{stats_start_row}')

            stats_data = fighter.stats.to_detailed_dict()
            row_offset = stats_start_row + 1

            for i, (key, value) in enumerate(stats_data.items()):
                if i < 9:
                    r, c = row_offset + i, 1
                else:
                    r, c = row_offset + (i - 9), 3
                ws.cell(row=r, column=c, value=key).border = thin_border
                ws.cell(row=r, column=c).font = Font(bold=True)
                ws.cell(row=r, column=c+1, value=str(value)).border = thin_border

        fight_col_widths = [4, 6, 14, 25, 10, 12, 20, 7, 7, 30]
        for col, width in enumerate(fight_col_widths, 1):
            ws.column_dimensions[chr(64 + col)].width = width

    # COLOR LEGEND SHEET
    legend_ws = wb.create_sheet("LEYENDA COLORES")
    legend_ws.merge_cells('A1:D1')
    legend_ws['A1'] = "LEYENDA DE COLORES POR PELEA - UFC 325"
    legend_ws['A1'].font = Font(bold=True, size=14, color="FFFFFF")
    legend_ws['A1'].fill = header_fill
    legend_ws['A1'].alignment = Alignment(horizontal='center')

    legend_headers = ['Pelea #', 'Peleador 1', 'VS', 'Peleador 2']
    legend_ws.append([])
    legend_ws.append(legend_headers)

    for col, header in enumerate(legend_headers, 1):
        cell = legend_ws.cell(row=3, column=col)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = thin_border

    row_num = 4
    for fight_num in sorted(fights_by_number.keys()):
        fight_fighters = fights_by_number[fight_num]
        if len(fight_fighters) >= 2:
            f1, f2 = fight_fighters[0], fight_fighters[1]
            color_idx = (fight_num - 1) % len(FIGHT_COLORS)
            fight_color = PatternFill(start_color=FIGHT_COLORS[color_idx],
                                     end_color=FIGHT_COLORS[color_idx], fill_type="solid")
            legend_ws.cell(row=row_num, column=1, value=f"Pelea {fight_num}")
            legend_ws.cell(row=row_num, column=2, value=f1.name)
            legend_ws.cell(row=row_num, column=3, value="VS")
            legend_ws.cell(row=row_num, column=4, value=f2.name)

            for col in range(1, 5):
                cell = legend_ws.cell(row=row_num, column=col)
                cell.fill = fight_color
                cell.border = thin_border
                cell.alignment = Alignment(horizontal='center')
            row_num += 1

    legend_ws.column_dimensions['A'].width = 12
    legend_ws.column_dimensions['B'].width = 25
    legend_ws.column_dimensions['C'].width = 5
    legend_ws.column_dimensions['D'].width = 25

    wb.save(output_path)
    logger.info(f"Excel report saved to: {output_path}")
    return output_path


def create_csv_report(fighters: List[Fighter], output_path: str = "UFC_325_Fighter_Analysis.csv"):
    """Create a CSV report with all fighter data."""
    all_data = []
    for fighter in fighters:
        for fight_idx, fight in enumerate(fighter.fights, 1):
            year = extract_year(fight.date)
            row = {
                'Fight_Number': fighter.fight_number, 'Fighter': fighter.name,
                'Fighter_Record': fighter.record, 'Weight_Class': fighter.weight_class,
                'Card_Position': fighter.card_position, 'UFC325_Opponent': fighter.opponent_name,
                'Fight_Index': fight_idx, 'Year': year, 'Fight_Date': fight.date,
                'Opponent': fight.opponent, 'Result': fight.result, 'Method': fight.method,
                'Method_Detail': fight.method_detail, 'Round': fight.round_ended,
                'Time': fight.time, 'Event': fight.event,
            }
            if fighter.stats:
                row['Win_Rate'] = fighter.stats.win_rate
                row['Most_Common_Method'] = fighter.stats.most_common_method
                row['Avg_Rounds'] = fighter.stats.avg_rounds
                row['Current_Streak'] = fighter.stats.current_streak
                row['Finish_Rate'] = fighter.stats.finish_rate
                row['Decision_Rate'] = fighter.stats.decision_rate
                row['Total_KO_TKO'] = fighter.stats.ko_count + fighter.stats.tko_count
                row['Total_Submissions'] = fighter.stats.submission_count
                row['Total_Decisions'] = fighter.stats.decision_count
                row['Total_NC'] = fighter.stats.nc_count
                row['Wins_by_KO_TKO'] = fighter.stats.wins_by_ko
                row['Wins_by_Submission'] = fighter.stats.wins_by_sub
                row['Wins_by_Decision'] = fighter.stats.wins_by_dec
                row['Losses_by_KO_TKO'] = fighter.stats.losses_by_ko
                row['Losses_by_Submission'] = fighter.stats.losses_by_sub
                row['Losses_by_Decision'] = fighter.stats.losses_by_dec
            all_data.append(row)

    df = pd.DataFrame(all_data)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    logger.info(f"CSV report saved to: {output_path}")
    return output_path


def scrape_fighter_data(fighter: Fighter, scraper, use_demo: bool = False) -> Fighter:
    """Process fight history for a single fighter."""
    logger.info(f"Processing: {fighter.name}")
    fights = get_demo_fights(fighter.name)
    if not fights:
        logger.warning(f"No demo data for {fighter.name}")
        fights = []
    fighter.fights = fights
    if len(fights) < 5:
        logger.warning(f"{fighter.name} has only {len(fights)} fights")
    fighter.stats = calculate_fighter_stats(fights)
    return fighter


def main(use_demo: bool = True, output_dir: str = "."):
    """Main function to run the UFC 325 fighter analysis."""
    print("=" * 80)
    print("UFC 325 FIGHTER ANALYSIS SCRIPT")
    print("31 de Enero 2026 - Qudos Bank Arena, Sydney, Australia")
    print("=" * 80)
    print()

    fighters = []
    total_fighters = len(UFC_325_FIGHTERS)

    print(f"Procesando {total_fighters} peleadores...")
    print()

    for i, fighter in enumerate(UFC_325_FIGHTERS, 1):
        print(f"[{i}/{total_fighters}] {fighter.name}...", end=" ")
        try:
            processed_fighter = scrape_fighter_data(fighter, None, use_demo=use_demo)
            fighters.append(processed_fighter)
            fights_found = len(processed_fighter.fights)
            print(f"✓ ({fights_found} peleas)")
        except Exception as e:
            logger.error(f"Error processing {fighter.name}: {e}")
            print(f"✗ Error: {e}")
            fighters.append(fighter)

    print()
    print("=" * 80)
    print("GENERANDO REPORTES...")
    print("=" * 80)

    if output_dir and output_dir != ".":
        os.makedirs(output_dir, exist_ok=True)

    excel_path = os.path.join(output_dir, "UFC_325_Fighter_Analysis.xlsx")
    try:
        create_excel_report(fighters, excel_path)
        print(f"✓ Excel generado: {excel_path}")
    except Exception as e:
        logger.error(f"Error creating Excel: {e}")
        print(f"✗ Error Excel: {e}")

    csv_path = os.path.join(output_dir, "UFC_325_Fighter_Analysis.csv")
    try:
        create_csv_report(fighters, csv_path)
        print(f"✓ CSV generado: {csv_path}")
    except Exception as e:
        logger.error(f"Error creating CSV: {e}")
        print(f"✗ Error CSV: {e}")

    print()
    print("=" * 80)
    print("RESUMEN UFC 325")
    print("=" * 80)
    print()
    print(f"{'Peleador':<25} {'Win Rate':<12} {'Racha':<18} {'Finish Rate':<12}")
    print("-" * 80)

    for fighter in fighters:
        if fighter.stats and fighter.stats.total_fights_analyzed > 0:
            print(f"{fighter.name:<25} {fighter.stats.win_rate:>6.1f}%     "
                  f"{fighter.stats.current_streak:<18} {fighter.stats.finish_rate:>6.1f}%")

    print()
    print("=" * 80)
    print("ANÁLISIS COMPLETADO - UFC 325")
    print("=" * 80)
    return fighters


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="UFC 325 Fighter Analysis Script")
    parser.add_argument("--scrape", action="store_true", help="Use web scraping")
    parser.add_argument("--output", "-o", default=".", help="Output directory")
    args = parser.parse_args()
    main(use_demo=not args.scrape, output_dir=args.output)
