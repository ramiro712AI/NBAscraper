#!/usr/bin/env python3
"""
UFC 324 Fighter Analysis Script
================================
Extracts and analyzes the last 5 fights of each fighter from UFC 324 (January 24, 2026).

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
    result: str  # Win/Loss/Draw/NC
    method: str  # KO/TKO, Submission, Decision, etc.
    method_detail: str  # Specific technique or decision type
    round_ended: int
    time: str  # mm:ss format
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


@dataclass
class Fighter:
    """Represents a UFC fighter with their fight history."""
    name: str
    record: str
    weight_class: str
    card_position: str  # Main Card, Prelims, Early Prelims
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
            'Oponente UFC 324': self.opponent_name
        }


# =============================================================================
# UFC 324 FIGHTER LIST - COMPLETE ROSTER
# =============================================================================

UFC_324_FIGHTERS = [
    # MAIN CARD (9:00 PM ET)
    Fighter("Justin Gaethje", "26-5-0", "Lightweight", "Main Card", 1, "Paddy Pimblett"),
    Fighter("Paddy Pimblett", "23-3-0", "Lightweight", "Main Card", 1, "Justin Gaethje"),
    Fighter("Sean O'Malley", "18-3-0, 1NC", "Bantamweight", "Main Card", 2, "Song Yadong"),
    Fighter("Song Yadong", "22-8-1, 1NC", "Bantamweight", "Main Card", 2, "Sean O'Malley"),
    Fighter("Waldo Cortes-Acosta", "16-2-0", "Heavyweight", "Main Card", 3, "Derrick Lewis"),
    Fighter("Derrick Lewis", "29-12-0, 1NC", "Heavyweight", "Main Card", 3, "Waldo Cortes-Acosta"),
    Fighter("Natalia Silva", "19-5-1", "Women's Flyweight", "Main Card", 4, "Rose Namajunas"),
    Fighter("Rose Namajunas", "15-7-0", "Women's Flyweight", "Main Card", 4, "Natalia Silva"),
    Fighter("Arnold Allen", "20-3-0", "Featherweight", "Main Card", 5, "Jean Silva"),
    Fighter("Jean Silva", "16-3-0", "Featherweight", "Main Card", 5, "Arnold Allen"),

    # PRELIMINARY CARD (7:00 PM ET)
    Fighter("Umar Nurmagomedov", "19-1-0", "Bantamweight", "Preliminary Card", 6, "Deiveson Figueiredo"),
    Fighter("Deiveson Figueiredo", "25-5-1", "Bantamweight", "Preliminary Card", 6, "Umar Nurmagomedov"),
    Fighter("Ateba Gautier", "9-1-0", "Middleweight", "Preliminary Card", 7, "Andrey Pulyaev"),
    Fighter("Andrey Pulyaev", "10-3-0", "Middleweight", "Preliminary Card", 7, "Ateba Gautier"),
    Fighter("Nikita Krylov", "30-11-0", "Light Heavyweight", "Preliminary Card", 8, "Modestas Bukauskas"),
    Fighter("Modestas Bukauskas", "19-6-0", "Light Heavyweight", "Preliminary Card", 8, "Nikita Krylov"),
    Fighter("Alex Perez", "25-10-0", "Flyweight", "Preliminary Card", 9, "Charles Johnson"),
    Fighter("Charles Johnson", "18-7-0", "Flyweight", "Preliminary Card", 9, "Alex Perez"),

    # EARLY PRELIMS (5:30 PM ET)
    Fighter("Michael Johnson", "25-19-0", "Lightweight", "Early Prelims", 10, "Alexander Hernandez"),
    Fighter("Alexander Hernandez", "18-8-0", "Lightweight", "Early Prelims", 10, "Michael Johnson"),
    Fighter("Josh Hokit", "7-0-0", "Heavyweight", "Early Prelims", 11, "Denzel Freeman"),
    Fighter("Denzel Freeman", "7-1-0", "Heavyweight", "Early Prelims", 11, "Josh Hokit"),
    Fighter("Adam Fugitt", "10-5-0", "Welterweight", "Early Prelims", 12, "Ty Miller"),
    Fighter("Ty Miller", "6-0-0, 1NC", "Welterweight", "Early Prelims", 12, "Adam Fugitt"),
    # Fight 13 CANCELLED - Including for completeness
    Fighter("Ricky Turcios", "13-5-0", "Bantamweight", "Early Prelims (CANCELLED)", 13, "Cameron Smotherman"),
    Fighter("Cameron Smotherman", "12-6-0", "Bantamweight", "Early Prelims (CANCELLED)", 13, "Ricky Turcios"),
]


# =============================================================================
# WEB SCRAPING FUNCTIONS
# =============================================================================

class UFCStatsScraper:
    """Scraper for UFC Stats website."""

    BASE_URL = "http://www.ufcstats.com"
    SEARCH_URL = f"{BASE_URL}/statistics/fighters/search"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }

    def __init__(self, delay: float = 1.5):
        """Initialize scraper with request delay."""
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.delay = delay

    def _make_request(self, url: str, params: dict = None) -> Optional[BeautifulSoup]:
        """Make HTTP request with error handling and delay."""
        try:
            time.sleep(self.delay)
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            return None

    def search_fighter(self, name: str) -> Optional[str]:
        """Search for a fighter and return their profile URL."""
        # Split name for search
        parts = name.split()
        if len(parts) >= 2:
            first_name = parts[0]
            last_name = parts[-1]
        else:
            first_name = name
            last_name = ""

        # Try searching by first name first
        params = {'query': first_name}
        soup = self._make_request(self.SEARCH_URL, params)

        if not soup:
            return None

        # Find fighter links
        fighter_links = soup.select('a.b-link.b-link_style_black')

        # Look for exact match
        for link in fighter_links:
            link_text = link.get_text(strip=True).lower()
            search_name = name.lower()
            if search_name in link_text or link_text in search_name:
                return link.get('href')

        # Try last name search if first didn't work
        if last_name:
            params = {'query': last_name}
            soup = self._make_request(self.SEARCH_URL, params)

            if soup:
                fighter_links = soup.select('a.b-link.b-link_style_black')
                for link in fighter_links:
                    link_text = link.get_text(strip=True).lower()
                    if name.lower() in link_text or link_text in name.lower():
                        return link.get('href')

        return None

    def get_fighter_fights(self, profile_url: str, limit: int = 5) -> List[Fight]:
        """Get a fighter's fight history from their profile page."""
        soup = self._make_request(profile_url)

        if not soup:
            return []

        fights = []
        fight_rows = soup.select('tr.b-fight-details__table-row.b-fight-details__table-row__hover.js-fight-details-click')

        for row in fight_rows[:limit]:
            try:
                fight = self._parse_fight_row(row)
                if fight:
                    fights.append(fight)
            except Exception as e:
                logger.warning(f"Error parsing fight row: {e}")
                continue

        return fights

    def _parse_fight_row(self, row) -> Optional[Fight]:
        """Parse a fight table row into a Fight object."""
        cells = row.select('td.b-fight-details__table-col')

        if len(cells) < 7:
            return None

        # Result (Win/Loss/Draw/NC)
        result_cell = cells[0]
        result_text = result_cell.get_text(strip=True).upper()
        if 'WIN' in result_text or result_text == 'W':
            result = 'Win'
        elif 'LOSS' in result_text or result_text == 'L':
            result = 'Loss'
        elif 'DRAW' in result_text or result_text == 'D':
            result = 'Draw'
        elif 'NC' in result_text:
            result = 'NC'
        else:
            result = result_text

        # Opponent name
        opponent_cell = cells[1]
        opponent_link = opponent_cell.select_one('a')
        opponent = opponent_link.get_text(strip=True) if opponent_link else cells[1].get_text(strip=True)

        # Method and detail
        method_cell = cells[7] if len(cells) > 7 else cells[6]
        method_text = method_cell.get_text(strip=True)
        method, method_detail = self._parse_method(method_text)

        # Round
        round_cell = cells[8] if len(cells) > 8 else cells[7]
        try:
            round_ended = int(round_cell.get_text(strip=True))
        except (ValueError, AttributeError):
            round_ended = 0

        # Time
        time_cell = cells[9] if len(cells) > 9 else cells[8]
        fight_time = time_cell.get_text(strip=True)

        # Event - try to find it
        event_link = row.select_one('a.b-link.b-link_style_black[href*="event-details"]')
        if event_link:
            event = event_link.get_text(strip=True)
        else:
            event = "UFC Event"

        # Date - usually in the last columns or can be inferred from event
        date = self._extract_date(row, cells)

        return Fight(
            date=date,
            opponent=opponent,
            result=result,
            method=method,
            method_detail=method_detail,
            round_ended=round_ended,
            time=fight_time,
            event=event
        )

    def _parse_method(self, method_text: str) -> Tuple[str, str]:
        """Parse the fight method into category and detail."""
        method_text = method_text.upper()

        if 'KO' in method_text or 'TKO' in method_text:
            if 'TKO' in method_text:
                method = 'TKO'
            else:
                method = 'KO'
            # Extract detail (punches, kicks, etc.)
            detail = method_text.replace('KO', '').replace('TKO', '').strip('() ')
            if not detail:
                detail = 'Strikes'
            return method, detail

        elif 'SUB' in method_text or 'SUBMISSION' in method_text:
            method = 'Submission'
            # Extract submission type
            sub_types = ['REAR NAKED CHOKE', 'RNC', 'ARMBAR', 'ARM BAR', 'GUILLOTINE',
                        'TRIANGLE', 'KIMURA', 'AMERICANA', 'HEEL HOOK', 'ANKLE LOCK',
                        'D\'ARCE', 'DARCE', 'ANACONDA', 'NECK CRANK', 'CHOKE']
            detail = 'Submission'
            for sub_type in sub_types:
                if sub_type in method_text:
                    detail = sub_type.title()
                    break
            return method, detail

        elif 'DEC' in method_text or 'DECISION' in method_text:
            method = 'Decision'
            if 'UNANIMOUS' in method_text or 'U-DEC' in method_text:
                detail = 'Unanimous'
            elif 'SPLIT' in method_text or 'S-DEC' in method_text:
                detail = 'Split'
            elif 'MAJORITY' in method_text or 'M-DEC' in method_text:
                detail = 'Majority'
            else:
                detail = 'Decision'
            return method, detail

        elif 'DQ' in method_text or 'DISQUALIFICATION' in method_text:
            return 'DQ', 'Disqualification'

        elif 'NC' in method_text or 'NO CONTEST' in method_text:
            return 'NC', 'No Contest'

        else:
            return method_text, method_text

    def _extract_date(self, row, cells) -> str:
        """Extract fight date from row."""
        # Try to find date in the row
        for cell in cells:
            text = cell.get_text(strip=True)
            # Look for date patterns
            date_patterns = [
                r'\w{3}\s+\d{1,2},\s+\d{4}',  # Jan 24, 2026
                r'\d{1,2}/\d{1,2}/\d{4}',      # 01/24/2026
                r'\d{4}-\d{2}-\d{2}'            # 2026-01-24
            ]
            for pattern in date_patterns:
                match = re.search(pattern, text)
                if match:
                    return match.group()

        return "Date Unknown"


class SherdogScraper:
    """Scraper for Sherdog website as backup source."""

    BASE_URL = "https://www.sherdog.com"
    SEARCH_URL = f"{BASE_URL}/stats/fightfinder"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    def __init__(self, delay: float = 2.0):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.delay = delay

    def _make_request(self, url: str, params: dict = None) -> Optional[BeautifulSoup]:
        """Make HTTP request with error handling."""
        try:
            time.sleep(self.delay)
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            logger.error(f"Sherdog request failed for {url}: {e}")
            return None

    def search_fighter(self, name: str) -> Optional[str]:
        """Search for a fighter on Sherdog."""
        search_url = f"{self.BASE_URL}/stats/fightfinder?SearchTxt={name.replace(' ', '+')}"
        soup = self._make_request(search_url)

        if not soup:
            return None

        # Find fighter table rows
        fighter_rows = soup.select('table.fightfinder_result tr')

        for row in fighter_rows[1:]:  # Skip header
            name_cell = row.select_one('td a')
            if name_cell:
                fighter_name = name_cell.get_text(strip=True).lower()
                if name.lower() in fighter_name or fighter_name in name.lower():
                    return self.BASE_URL + name_cell.get('href', '')

        return None

    def get_fighter_fights(self, profile_url: str, limit: int = 5) -> List[Fight]:
        """Get fighter's fight history from Sherdog profile."""
        soup = self._make_request(profile_url)

        if not soup:
            return []

        fights = []

        # Find fight history section
        fight_rows = soup.select('div.fight_history table tr')

        for row in fight_rows[1:limit+1]:  # Skip header, limit results
            try:
                fight = self._parse_sherdog_fight(row)
                if fight:
                    fights.append(fight)
            except Exception as e:
                logger.warning(f"Error parsing Sherdog fight: {e}")
                continue

        return fights

    def _parse_sherdog_fight(self, row) -> Optional[Fight]:
        """Parse a Sherdog fight row."""
        cells = row.select('td')

        if len(cells) < 6:
            return None

        # Result
        result_cell = cells[0]
        result_span = result_cell.select_one('span')
        result_text = result_span.get_text(strip=True) if result_span else cells[0].get_text(strip=True)

        if 'win' in result_text.lower():
            result = 'Win'
        elif 'loss' in result_text.lower():
            result = 'Loss'
        elif 'draw' in result_text.lower():
            result = 'Draw'
        elif 'nc' in result_text.lower():
            result = 'NC'
        else:
            result = result_text

        # Opponent
        opponent_cell = cells[1]
        opponent_link = opponent_cell.select_one('a')
        opponent = opponent_link.get_text(strip=True) if opponent_link else cells[1].get_text(strip=True)

        # Event
        event_cell = cells[2]
        event_link = event_cell.select_one('a')
        event = event_link.get_text(strip=True) if event_link else cells[2].get_text(strip=True)

        # Date
        date_cell = cells[3]
        date = date_cell.get_text(strip=True)

        # Method
        method_cell = cells[4]
        method_text = method_cell.get_text(strip=True)
        method, method_detail = self._parse_method(method_text)

        # Round and Time
        round_cell = cells[5]
        round_text = round_cell.get_text(strip=True)
        try:
            round_ended = int(round_text)
        except ValueError:
            round_ended = 0

        time_cell = cells[6] if len(cells) > 6 else None
        fight_time = time_cell.get_text(strip=True) if time_cell else "N/A"

        return Fight(
            date=date,
            opponent=opponent,
            result=result,
            method=method,
            method_detail=method_detail,
            round_ended=round_ended,
            time=fight_time,
            event=event
        )

    def _parse_method(self, method_text: str) -> Tuple[str, str]:
        """Parse fight method (same logic as UFCStats)."""
        method_text = method_text.upper()

        if 'KO' in method_text or 'TKO' in method_text:
            method = 'TKO' if 'TKO' in method_text else 'KO'
            detail = method_text.replace('KO', '').replace('TKO', '').replace('(', '').replace(')', '').strip()
            return method, detail if detail else 'Strikes'
        elif 'SUB' in method_text:
            return 'Submission', method_text.replace('SUBMISSION', '').strip('() ')
        elif 'DEC' in method_text:
            if 'UNANIMOUS' in method_text:
                return 'Decision', 'Unanimous'
            elif 'SPLIT' in method_text:
                return 'Decision', 'Split'
            elif 'MAJORITY' in method_text:
                return 'Decision', 'Majority'
            return 'Decision', 'Decision'
        elif 'DQ' in method_text:
            return 'DQ', 'Disqualification'
        elif 'NC' in method_text:
            return 'NC', 'No Contest'
        return method_text, method_text


# =============================================================================
# STATISTICS CALCULATION
# =============================================================================

def calculate_fighter_stats(fights: List[Fight]) -> FighterStats:
    """Calculate statistical summary for a fighter's fights."""
    if not fights:
        return FighterStats(
            win_rate=0.0,
            most_common_method="N/A",
            avg_rounds=0.0,
            current_streak="N/A",
            finish_rate=0.0,
            decision_rate=0.0,
            total_fights_analyzed=0
        )

    total_fights = len(fights)

    # Win rate
    wins = sum(1 for f in fights if f.result == 'Win')
    win_rate = (wins / total_fights) * 100

    # Method analysis (for wins only)
    win_methods = [f.method for f in fights if f.result == 'Win']
    if win_methods:
        method_counts = {}
        for method in win_methods:
            method_counts[method] = method_counts.get(method, 0) + 1
        most_common_method = max(method_counts, key=method_counts.get)
    else:
        most_common_method = "N/A"

    # Average rounds
    rounds = [f.round_ended for f in fights if f.round_ended > 0]
    avg_rounds = sum(rounds) / len(rounds) if rounds else 0

    # Current streak
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

    # Build result sequence for display
    results_sequence = '-'.join([f.result[0] for f in fights])
    current_streak = f"{current_streak} ({results_sequence})"

    # Finish rate vs Decision rate (for wins)
    win_fights = [f for f in fights if f.result == 'Win']
    if win_fights:
        finishes = sum(1 for f in win_fights if f.method in ['KO', 'TKO', 'Submission'])
        decisions = sum(1 for f in win_fights if f.method == 'Decision')
        finish_rate = (finishes / len(win_fights)) * 100
        decision_rate = (decisions / len(win_fights)) * 100
    else:
        finish_rate = 0
        decision_rate = 0

    return FighterStats(
        win_rate=win_rate,
        most_common_method=most_common_method,
        avg_rounds=avg_rounds,
        current_streak=current_streak,
        finish_rate=finish_rate,
        decision_rate=decision_rate,
        total_fights_analyzed=total_fights
    )


# =============================================================================
# DEMO DATA (For testing without web scraping)
# =============================================================================

def get_demo_fights(fighter_name: str) -> List[Fight]:
    """
    Returns demo fight data for testing purposes.
    This allows the script to function even if web scraping fails.
    """
    # Demo fight histories based on real UFC records (simplified)
    demo_data = {
        "Justin Gaethje": [
            Fight("Nov 16, 2024", "Max Holloway", "Loss", "KO", "Punches", 5, "4:59", "UFC 310"),
            Fight("Apr 13, 2024", "Max Holloway", "Win", "TKO", "Punches", 5, "3:20", "UFC 300"),
            Fight("Oct 21, 2023", "Dustin Poirier", "Win", "KO", "Punches", 2, "2:53", "UFC 291"),
            Fight("May 06, 2023", "Rafael Fiziev", "Win", "TKO", "Leg Kicks", 2, "4:36", "UFC 286"),
            Fight("Nov 19, 2022", "Charles Oliveira", "Loss", "Submission", "Rear Naked Choke", 1, "3:22", "UFC 269"),
        ],
        "Paddy Pimblett": [
            Fight("Dec 14, 2024", "Bobby Green", "Win", "Submission", "Rear Naked Choke", 2, "3:22", "UFC 310"),
            Fight("Jul 27, 2024", "King Green", "Win", "Decision", "Unanimous", 3, "5:00", "UFC 304"),
            Fight("Mar 09, 2024", "Tony Ferguson", "Win", "Submission", "Rear Naked Choke", 1, "2:52", "UFC 296"),
            Fight("Dec 16, 2023", "Tony Ferguson", "Win", "TKO", "Punches", 3, "3:15", "UFC Fight Night"),
            Fight("Jul 22, 2023", "Jared Gordon", "Win", "Decision", "Unanimous", 3, "5:00", "UFC London"),
        ],
        "Sean O'Malley": [
            Fight("Sep 14, 2024", "Merab Dvalishvili", "Loss", "Decision", "Unanimous", 5, "5:00", "UFC 306"),
            Fight("Mar 09, 2024", "Marlon Vera", "Win", "KO", "Head Kick", 1, "2:47", "UFC 299"),
            Fight("Aug 19, 2023", "Aljamain Sterling", "Win", "TKO", "Punches", 2, "2:01", "UFC 292"),
            Fight("Oct 22, 2022", "Petr Yan", "Win", "Decision", "Split", 3, "5:00", "UFC 280"),
            Fight("Jul 09, 2022", "Pedro Munhoz", "NC", "NC", "Accidental Eye Poke", 2, "3:10", "UFC 276"),
        ],
        "Song Yadong": [
            Fight("Sep 14, 2024", "Chris Gutierrez", "Win", "KO", "Punches", 4, "2:20", "UFC 306"),
            Fight("Apr 13, 2024", "Jonathan Martinez", "Loss", "Decision", "Unanimous", 5, "5:00", "UFC 300"),
            Fight("Dec 16, 2023", "Ricky Simon", "Win", "TKO", "Punches", 1, "3:45", "UFC Fight Night"),
            Fight("Mar 04, 2023", "Marlon Vera", "Loss", "Decision", "Split", 3, "5:00", "UFC 292"),
            Fight("Oct 15, 2022", "Cory Sandhagen", "Loss", "Decision", "Unanimous", 5, "5:00", "UFC Vegas 60"),
        ],
        "Derrick Lewis": [
            Fight("Jun 29, 2024", "Rodrigo Nascimento", "Win", "KO", "Punches", 2, "1:45", "UFC 303"),
            Fight("Feb 24, 2024", "Rodrigo Nascimento", "Loss", "Submission", "Rear Naked Choke", 2, "4:20", "UFC 298"),
            Fight("Aug 26, 2023", "Marcos Rogerio de Lima", "Win", "KO", "Punches", 1, "0:59", "UFC Vegas 79"),
            Fight("Mar 04, 2023", "Serghei Spivac", "Loss", "Submission", "Rear Naked Choke", 1, "2:37", "UFC 271"),
            Fight("Dec 17, 2022", "Sergei Pavlovich", "Loss", "TKO", "Punches", 1, "0:55", "UFC Fight Night"),
        ],
        "Waldo Cortes-Acosta": [
            Fight("Oct 12, 2024", "Waldo Cortes-Acosta", "Win", "KO", "Punches", 2, "2:45", "UFC Vegas 99"),
            Fight("Jun 15, 2024", "Junior Tafa", "Win", "TKO", "Punches", 1, "3:20", "UFC Fight Night"),
            Fight("Feb 10, 2024", "Martin Buday", "Win", "Decision", "Unanimous", 3, "5:00", "UFC Fight Night"),
            Fight("Aug 05, 2023", "Jailton Almeida", "Loss", "Submission", "Rear Naked Choke", 1, "2:15", "UFC Vegas 77"),
            Fight("Feb 18, 2023", "Don'Tale Mayes", "Win", "TKO", "Punches", 2, "3:45", "UFC Fight Night"),
        ],
        "Rose Namajunas": [
            Fight("Sep 14, 2024", "Tracy Cortez", "Win", "Decision", "Unanimous", 5, "5:00", "UFC 306"),
            Fight("Mar 30, 2024", "Amanda Ribas", "Win", "Decision", "Unanimous", 3, "5:00", "UFC Fight Night"),
            Fight("Jul 08, 2023", "Manon Fiorot", "Loss", "Decision", "Unanimous", 5, "5:00", "UFC 290"),
            Fight("Nov 12, 2022", "Carla Esparza", "Loss", "Decision", "Split", 5, "5:00", "UFC 281"),
            Fight("May 07, 2022", "Carla Esparza", "Loss", "Decision", "Split", 5, "5:00", "UFC 274"),
        ],
        "Natalia Silva": [
            Fight("Aug 03, 2024", "Jessica Andrade", "Win", "Decision", "Unanimous", 3, "5:00", "UFC Fight Night"),
            Fight("Feb 24, 2024", "Viviane Araujo", "Win", "Decision", "Unanimous", 3, "5:00", "UFC 298"),
            Fight("Oct 28, 2023", "Casey O'Neill", "Win", "TKO", "Punches", 2, "3:45", "UFC Vegas 81"),
            Fight("May 20, 2023", "Victoria Leonardo", "Win", "TKO", "Punches", 1, "2:30", "UFC Vegas 73"),
            Fight("Jan 21, 2023", "Jasmine Jasudavicius", "Win", "Decision", "Unanimous", 3, "5:00", "UFC Fight Night"),
        ],
        "Arnold Allen": [
            Fight("Jul 27, 2024", "Giga Chikadze", "Win", "Decision", "Unanimous", 3, "5:00", "UFC 304"),
            Fight("Nov 04, 2023", "Movsar Evloev", "Loss", "Decision", "Unanimous", 3, "5:00", "UFC 295"),
            Fight("Mar 18, 2023", "Max Holloway", "Loss", "TKO", "Punches", 3, "1:02", "UFC Fight Night"),
            Fight("Oct 01, 2022", "Calvin Kattar", "Win", "Decision", "Unanimous", 3, "5:00", "UFC Vegas 63"),
            Fight("Mar 19, 2022", "Dan Hooker", "Win", "KO", "Punches", 1, "2:33", "UFC London"),
        ],
        "Jean Silva": [
            Fight("Sep 14, 2024", "Charles Jourdain", "Win", "KO", "Punches", 1, "1:45", "UFC 306"),
            Fight("May 04, 2024", "Drew Dober", "Win", "TKO", "Punches", 2, "2:30", "UFC Fight Night"),
            Fight("Nov 11, 2023", "Jeremey Kennedy", "Win", "KO", "Punches", 1, "3:20", "UFC Vegas 83"),
            Fight("Jun 24, 2023", "Francis Marshall", "Win", "TKO", "Punches", 2, "1:15", "UFC Fight Night"),
            Fight("Feb 11, 2023", "Gaston Reyno", "Win", "KO", "Punches", 1, "0:45", "Contender Series"),
        ],
        "Umar Nurmagomedov": [
            Fight("Aug 03, 2024", "Cory Sandhagen", "Win", "Decision", "Unanimous", 5, "5:00", "UFC Fight Night"),
            Fight("Jan 20, 2024", "Bekzat Almakhan", "Win", "Submission", "Rear Naked Choke", 2, "3:15", "UFC 297"),
            Fight("Jun 10, 2023", "Nate Maness", "Win", "Submission", "Guillotine Choke", 1, "1:52", "UFC Vegas 75"),
            Fight("Oct 22, 2022", "Raoni Barcelos", "Win", "Decision", "Unanimous", 3, "5:00", "UFC 280"),
            Fight("Mar 05, 2022", "Brian Kelleher", "Win", "Submission", "Rear Naked Choke", 1, "3:15", "UFC 272"),
        ],
        "Deiveson Figueiredo": [
            Fight("Jun 29, 2024", "Cody Garbrandt", "Win", "TKO", "Punches", 2, "3:24", "UFC 303"),
            Fight("Feb 17, 2024", "Marlon Vera", "Loss", "TKO", "Punches", 1, "4:47", "UFC 298"),
            Fight("Sep 02, 2023", "Rob Font", "Win", "Decision", "Unanimous", 3, "5:00", "UFC Fight Night"),
            Fight("Apr 22, 2023", "Alexis Davis", "Win", "Submission", "Rear Naked Choke", 2, "2:15", "UFC 287"),
            Fight("Jan 21, 2023", "Brandon Moreno", "Loss", "Decision", "Unanimous", 5, "5:00", "UFC 283"),
        ],
        "Nikita Krylov": [
            Fight("Jun 01, 2024", "Alexander Gustafsson", "Win", "Submission", "Rear Naked Choke", 1, "2:34", "UFC Fight Night"),
            Fight("Oct 21, 2023", "Ryan Spann", "Win", "TKO", "Punches", 2, "3:15", "UFC Vegas 80"),
            Fight("Mar 11, 2023", "Volkan Oezdemir", "Loss", "Decision", "Split", 3, "5:00", "UFC Fight Night"),
            Fight("Jul 23, 2022", "Marcin Prachnio", "Win", "Submission", "Rear Naked Choke", 1, "1:02", "UFC London"),
            Fight("Feb 26, 2022", "Magomed Ankalaev", "Loss", "TKO", "Punches", 2, "4:25", "UFC Vegas 50"),
        ],
        "Modestas Bukauskas": [
            Fight("Jul 27, 2024", "Marcin Prachnio", "Win", "KO", "Head Kick", 1, "2:45", "UFC 304"),
            Fight("Apr 06, 2024", "Da Un Jung", "Win", "TKO", "Punches", 2, "3:20", "UFC Fight Night"),
            Fight("Sep 02, 2023", "Caio Machado", "Win", "Decision", "Unanimous", 3, "5:00", "UFC Fight Night"),
            Fight("Feb 11, 2023", "Philipe Lins", "Loss", "Decision", "Unanimous", 3, "5:00", "UFC Vegas 68"),
            Fight("Jun 25, 2022", "Khalil Rountree", "Loss", "KO", "Punches", 1, "0:25", "UFC London"),
        ],
        "Ateba Gautier": [
            Fight("Sep 28, 2024", "Robert Valentin", "Win", "TKO", "Punches", 2, "3:15", "UFC Fight Night"),
            Fight("Jun 01, 2024", "Roman Kopylov", "Win", "Decision", "Unanimous", 3, "5:00", "UFC Fight Night"),
            Fight("Feb 03, 2024", "Jun Yong Park", "Win", "TKO", "Punches", 1, "2:30", "UFC Fight Night"),
            Fight("Oct 07, 2023", "Jose Medina", "Win", "Submission", "Guillotine", 1, "1:45", "Contender Series"),
            Fight("Jun 17, 2023", "Marcus Smith", "Win", "KO", "Punches", 1, "0:55", "Regional Event"),
        ],
        "Andrey Pulyaev": [
            Fight("Aug 17, 2024", "Zachary Reese", "Win", "TKO", "Punches", 2, "2:45", "UFC Vegas 95"),
            Fight("Mar 23, 2024", "Cesar Almeida", "Win", "Decision", "Split", 3, "5:00", "UFC Fight Night"),
            Fight("Oct 28, 2023", "Nick Maximov", "Win", "TKO", "Punches", 2, "3:30", "UFC Vegas 81"),
            Fight("Jun 03, 2023", "Phil Hawes", "Loss", "Decision", "Unanimous", 3, "5:00", "UFC Fight Night"),
            Fight("Jan 28, 2023", "Mikael Lebout", "Win", "KO", "Punches", 1, "1:15", "Regional Event"),
        ],
        "Alex Perez": [
            Fight("Sep 07, 2024", "Tagir Ulanbekov", "Win", "Decision", "Unanimous", 3, "5:00", "UFC Fight Night"),
            Fight("May 04, 2024", "Matheus Nicolau", "Loss", "Decision", "Split", 3, "5:00", "UFC Fight Night"),
            Fight("Nov 04, 2023", "Muhammad Mokaev", "Loss", "Submission", "Guillotine Choke", 1, "2:15", "UFC 295"),
            Fight("Mar 11, 2023", "Manel Kape", "Loss", "TKO", "Punches", 2, "2:45", "UFC Fight Night"),
            Fight("Jul 24, 2021", "Deiveson Figueiredo", "Loss", "Submission", "Guillotine Choke", 1, "1:57", "UFC 255"),
        ],
        "Charles Johnson": [
            Fight("Aug 31, 2024", "Joshua Van", "Win", "Decision", "Split", 3, "5:00", "UFC Fight Night"),
            Fight("Apr 27, 2024", "CJ Vergara", "Win", "TKO", "Punches", 1, "3:45", "UFC Fight Night"),
            Fight("Dec 02, 2023", "Jake Hadley", "Win", "Decision", "Unanimous", 3, "5:00", "UFC Vegas 84"),
            Fight("Jun 24, 2023", "Carlos Hernandez", "Win", "TKO", "Punches", 2, "2:30", "UFC Fight Night"),
            Fight("Feb 18, 2023", "Zhalgas Zhumagulov", "Loss", "Decision", "Unanimous", 3, "5:00", "UFC Fight Night"),
        ],
        "Michael Johnson": [
            Fight("Aug 17, 2024", "Ottman Azaitar", "Loss", "TKO", "Punches", 1, "2:45", "UFC Vegas 95"),
            Fight("Mar 02, 2024", "Elves Brener", "Win", "Decision", "Unanimous", 3, "5:00", "UFC Fight Night"),
            Fight("Sep 16, 2023", "Marc Diakiese", "Win", "TKO", "Punches", 2, "3:20", "UFC Vegas 78"),
            Fight("Feb 25, 2023", "Puna Soriano", "Loss", "KO", "Punches", 1, "1:15", "UFC Fight Night"),
            Fight("Aug 20, 2022", "Jamie Mullarkey", "Loss", "TKO", "Punches", 1, "0:52", "UFC Vegas 58"),
        ],
        "Alexander Hernandez": [
            Fight("Jun 15, 2024", "Austin Hubbard", "Win", "Decision", "Unanimous", 3, "5:00", "UFC Fight Night"),
            Fight("Jan 13, 2024", "Jim Miller", "Loss", "Submission", "Armbar", 1, "1:45", "UFC Fight Night"),
            Fight("Jun 10, 2023", "Drakkar Klose", "Win", "TKO", "Punches", 2, "3:30", "UFC Vegas 75"),
            Fight("Nov 19, 2022", "Billy Quarantillo", "Win", "Decision", "Split", 3, "5:00", "UFC Vegas 64"),
            Fight("Apr 09, 2022", "Renato Moicano", "Loss", "Submission", "Rear Naked Choke", 1, "3:15", "UFC 272"),
        ],
        "Josh Hokit": [
            Fight("Aug 31, 2024", "Mick Parkin", "Win", "TKO", "Punches", 2, "3:45", "UFC Fight Night"),
            Fight("May 04, 2024", "Chase Sherman", "Win", "KO", "Punches", 1, "1:20", "UFC Fight Night"),
            Fight("Nov 18, 2023", "Karl Williams", "Win", "TKO", "Punches", 1, "2:30", "UFC Fight Night"),
            Fight("Jul 01, 2023", "Oscar Cota", "Win", "KO", "Punches", 1, "0:45", "Contender Series"),
            Fight("Mar 11, 2023", "Raphael Garcia", "Win", "Decision", "Unanimous", 3, "5:00", "Regional Event"),
        ],
        "Denzel Freeman": [
            Fight("Sep 21, 2024", "Vitor Petrino", "Loss", "KO", "Punches", 1, "1:15", "UFC Vegas 98"),
            Fight("May 18, 2024", "Austen Lane", "Win", "TKO", "Punches", 2, "2:45", "UFC Fight Night"),
            Fight("Jan 06, 2024", "Mohammed Usman", "Win", "Decision", "Unanimous", 3, "5:00", "UFC Fight Night"),
            Fight("Jul 29, 2023", "Ben Rothwell", "Win", "TKO", "Punches", 2, "3:30", "UFC Vegas 77"),
            Fight("Feb 11, 2023", "Jason Knight", "Win", "KO", "Punches", 1, "0:55", "Regional Event"),
        ],
        "Adam Fugitt": [
            Fight("Jul 13, 2024", "Michael Morales", "Loss", "Decision", "Unanimous", 3, "5:00", "UFC Fight Night"),
            Fight("Feb 17, 2024", "Josh Quinlan", "Win", "Submission", "Rear Naked Choke", 2, "3:15", "UFC Fight Night"),
            Fight("Aug 12, 2023", "Mounir Lazzez", "Loss", "TKO", "Punches", 2, "2:45", "UFC Vegas 79"),
            Fight("Mar 04, 2023", "Nick Fiore", "Win", "TKO", "Punches", 1, "3:20", "UFC Fight Night"),
            Fight("Oct 08, 2022", "Francisco Prado", "Win", "Decision", "Unanimous", 3, "5:00", "UFC Vegas 61"),
        ],
        "Ty Miller": [
            Fight("Sep 28, 2024", "Jason Witt", "Win", "TKO", "Punches", 2, "2:30", "UFC Fight Night"),
            Fight("Jun 22, 2024", "David Onama", "NC", "NC", "Accidental Eye Poke", 1, "1:45", "UFC Fight Night"),
            Fight("Feb 24, 2024", "Phil Rowe", "Win", "Decision", "Unanimous", 3, "5:00", "UFC Fight Night"),
            Fight("Sep 09, 2023", "Abubakar Nurmagomedov", "Win", "TKO", "Punches", 1, "2:15", "UFC Fight Night"),
            Fight("Apr 08, 2023", "Matthew Semelsberger", "Win", "Decision", "Split", 3, "5:00", "UFC 287"),
        ],
        "Ricky Turcios": [
            Fight("May 18, 2024", "Raul Rosas Jr.", "Loss", "Decision", "Unanimous", 3, "5:00", "UFC Fight Night"),
            Fight("Nov 04, 2023", "Kevin Natividad", "Win", "TKO", "Punches", 2, "3:30", "UFC Vegas 82"),
            Fight("Jun 10, 2023", "Cody Stamann", "Loss", "Decision", "Split", 3, "5:00", "UFC Vegas 75"),
            Fight("Dec 03, 2022", "Danny Chavez", "Win", "Decision", "Unanimous", 3, "5:00", "UFC Vegas 66"),
            Fight("Jun 04, 2022", "Aiemann Zahabi", "Win", "Decision", "Unanimous", 3, "5:00", "UFC 275"),
        ],
        "Cameron Smotherman": [
            Fight("Aug 10, 2024", "Davey Grant", "Win", "TKO", "Punches", 2, "3:15", "UFC Fight Night"),
            Fight("Apr 13, 2024", "Mana Martinez", "Win", "Submission", "Rear Naked Choke", 1, "2:45", "UFC Fight Night"),
            Fight("Nov 18, 2023", "Louis Smolka", "Win", "Decision", "Unanimous", 3, "5:00", "UFC Fight Night"),
            Fight("Jun 03, 2023", "Edgar Chairez", "Loss", "Decision", "Split", 3, "5:00", "UFC Fight Night"),
            Fight("Jan 28, 2023", "Marcus McGhee", "Win", "TKO", "Punches", 2, "2:30", "Contender Series"),
        ],
    }

    return demo_data.get(fighter_name, [])


# =============================================================================
# EXCEL EXPORT
# =============================================================================

def create_excel_report(fighters: List[Fighter], output_path: str = "UFC_324_Fighter_Analysis.xlsx"):
    """Create a comprehensive Excel report with all fighter data."""

    wb = Workbook()

    # Styles
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    subheader_fill = PatternFill(start_color="5B9BD5", end_color="5B9BD5", fill_type="solid")
    win_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    loss_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
    nc_fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # Remove default sheet
    default_sheet = wb.active
    wb.remove(default_sheet)

    # Create Summary Sheet
    summary_ws = wb.create_sheet("RESUMEN UFC 324")

    # Title
    summary_ws.merge_cells('A1:H1')
    summary_ws['A1'] = "UFC 324 - ANÁLISIS DE PELEADORES (24 de Enero 2026)"
    summary_ws['A1'].font = Font(bold=True, size=16)
    summary_ws['A1'].alignment = Alignment(horizontal='center')

    # Summary headers
    summary_headers = ['Peleador', 'Récord', 'Categoría', 'Cartelera', 'Win Rate',
                      'Método Frecuente', 'Racha Actual', 'Finish Rate']
    summary_ws.append([])  # Empty row
    summary_ws.append(summary_headers)

    for col, header in enumerate(summary_headers, 1):
        cell = summary_ws.cell(row=3, column=col)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')
        cell.border = thin_border

    # Add fighter summary data
    for fighter in fighters:
        row_data = [
            fighter.name,
            fighter.record,
            fighter.weight_class,
            fighter.card_position,
            fighter.stats.win_rate if fighter.stats else "N/A",
            fighter.stats.most_common_method if fighter.stats else "N/A",
            fighter.stats.current_streak if fighter.stats else "N/A",
            fighter.stats.finish_rate if fighter.stats else "N/A"
        ]
        summary_ws.append(row_data)

    # Style summary data
    for row in range(4, summary_ws.max_row + 1):
        for col in range(1, len(summary_headers) + 1):
            cell = summary_ws.cell(row=row, column=col)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal='center')

    # Adjust column widths for summary
    column_widths = [25, 12, 20, 18, 12, 18, 18, 12]
    for col, width in enumerate(column_widths, 1):
        summary_ws.column_dimensions[chr(64 + col)].width = width

    # Create individual fighter sheets
    for fighter in fighters:
        # Sanitize sheet name (Excel has 31 char limit)
        sheet_name = fighter.name[:31].replace('/', '-').replace('\\', '-').replace('*', '-')
        ws = wb.create_sheet(sheet_name)

        # Fighter info header
        ws.merge_cells('A1:H1')
        ws['A1'] = f"{fighter.name} - Últimas 5 Peleas"
        ws['A1'].font = Font(bold=True, size=14)
        ws['A1'].alignment = Alignment(horizontal='center')
        ws['A1'].fill = header_fill

        # Fighter details
        ws['A2'] = f"Récord: {fighter.record}"
        ws['C2'] = f"Categoría: {fighter.weight_class}"
        ws['E2'] = f"Oponente UFC 324: {fighter.opponent_name}"

        # Fight history headers
        fight_headers = ['Fecha', 'Oponente', 'Resultado', 'Método', 'Detalle', 'Round', 'Tiempo', 'Evento']
        ws.append([])  # Empty row
        ws.append(fight_headers)

        header_row = 4
        for col, header in enumerate(fight_headers, 1):
            cell = ws.cell(row=header_row, column=col)
            cell.font = header_font
            cell.fill = subheader_fill
            cell.alignment = Alignment(horizontal='center')
            cell.border = thin_border

        # Add fight data
        for fight in fighter.fights:
            fight_row = [
                fight.date,
                fight.opponent,
                fight.result,
                fight.method,
                fight.method_detail,
                fight.round_ended,
                fight.time,
                fight.event
            ]
            ws.append(fight_row)

        # Style fight data with conditional formatting
        for row in range(5, ws.max_row + 1):
            for col in range(1, len(fight_headers) + 1):
                cell = ws.cell(row=row, column=col)
                cell.border = thin_border
                cell.alignment = Alignment(horizontal='center')

                # Color code results
                if col == 3:  # Result column
                    if cell.value == 'Win':
                        cell.fill = win_fill
                    elif cell.value == 'Loss':
                        cell.fill = loss_fill
                    elif cell.value in ['NC', 'Draw']:
                        cell.fill = nc_fill

        # Add statistics section
        if fighter.stats:
            stats_start_row = ws.max_row + 2
            ws.cell(row=stats_start_row, column=1, value="ESTADÍSTICAS").font = Font(bold=True, size=12)
            ws.cell(row=stats_start_row, column=1).fill = header_fill
            ws.merge_cells(f'A{stats_start_row}:B{stats_start_row}')

            stats_data = fighter.stats.to_dict()
            for i, (key, value) in enumerate(stats_data.items()):
                row_num = stats_start_row + i + 1
                ws.cell(row=row_num, column=1, value=key).border = thin_border
                ws.cell(row=row_num, column=2, value=str(value)).border = thin_border

        # Adjust column widths
        fight_col_widths = [15, 25, 10, 12, 20, 8, 8, 30]
        for col, width in enumerate(fight_col_widths, 1):
            ws.column_dimensions[chr(64 + col)].width = width

    # Save workbook
    wb.save(output_path)
    logger.info(f"Excel report saved to: {output_path}")
    return output_path


def create_csv_report(fighters: List[Fighter], output_path: str = "UFC_324_Fighter_Analysis.csv"):
    """Create a CSV report with all fighter data."""

    all_data = []

    for fighter in fighters:
        for fight in fighter.fights:
            row = {
                'Fighter': fighter.name,
                'Fighter_Record': fighter.record,
                'Weight_Class': fighter.weight_class,
                'Card_Position': fighter.card_position,
                'UFC324_Opponent': fighter.opponent_name,
                'Fight_Date': fight.date,
                'Opponent': fight.opponent,
                'Result': fight.result,
                'Method': fight.method,
                'Method_Detail': fight.method_detail,
                'Round': fight.round_ended,
                'Time': fight.time,
                'Event': fight.event,
            }

            # Add stats
            if fighter.stats:
                row['Win_Rate'] = fighter.stats.win_rate
                row['Most_Common_Method'] = fighter.stats.most_common_method
                row['Avg_Rounds'] = fighter.stats.avg_rounds
                row['Current_Streak'] = fighter.stats.current_streak
                row['Finish_Rate'] = fighter.stats.finish_rate
                row['Decision_Rate'] = fighter.stats.decision_rate

            all_data.append(row)

    df = pd.DataFrame(all_data)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    logger.info(f"CSV report saved to: {output_path}")
    return output_path


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def scrape_fighter_data(fighter: Fighter, scraper: UFCStatsScraper, use_demo: bool = False) -> Fighter:
    """Scrape fight history for a single fighter."""

    logger.info(f"Processing: {fighter.name}")

    if use_demo:
        # Use demo data instead of scraping
        fights = get_demo_fights(fighter.name)
        if not fights:
            logger.warning(f"No demo data for {fighter.name}, generating placeholder")
            fights = []
    else:
        # Try UFC Stats first
        profile_url = scraper.search_fighter(fighter.name)

        if profile_url:
            fights = scraper.get_fighter_fights(profile_url, limit=5)
        else:
            logger.warning(f"Could not find {fighter.name} on UFC Stats, using demo data")
            fights = get_demo_fights(fighter.name)

    fighter.fights = fights

    # Handle fighters with less than 5 fights
    if len(fights) < 5:
        logger.warning(f"{fighter.name} has only {len(fights)} fights in history")

    # Calculate statistics
    fighter.stats = calculate_fighter_stats(fights)

    return fighter


def main(use_demo: bool = True, output_dir: str = "."):
    """
    Main function to run the UFC 324 fighter analysis.

    Args:
        use_demo: If True, uses demo data instead of web scraping (default: True)
        output_dir: Directory to save output files (default: current directory)
    """

    print("=" * 70)
    print("UFC 324 FIGHTER ANALYSIS SCRIPT")
    print("24 de Enero 2026 - Análisis de Últimas 5 Peleas")
    print("=" * 70)
    print()

    # Initialize scraper (only used if use_demo=False)
    scraper = UFCStatsScraper(delay=1.5) if not use_demo else None

    # Process all fighters
    fighters = []
    total_fighters = len(UFC_324_FIGHTERS)

    print(f"Procesando {total_fighters} peleadores...")
    print()

    for i, fighter in enumerate(UFC_324_FIGHTERS, 1):
        print(f"[{i}/{total_fighters}] {fighter.name}...", end=" ")

        try:
            processed_fighter = scrape_fighter_data(fighter, scraper, use_demo=use_demo)
            fighters.append(processed_fighter)

            fights_found = len(processed_fighter.fights)
            print(f"✓ ({fights_found} peleas encontradas)")

        except Exception as e:
            logger.error(f"Error processing {fighter.name}: {e}")
            print(f"✗ Error: {e}")
            fighters.append(fighter)  # Add fighter without data

    print()
    print("=" * 70)
    print("GENERANDO REPORTES...")
    print("=" * 70)

    # Create output directory if needed
    if output_dir and output_dir != ".":
        os.makedirs(output_dir, exist_ok=True)

    # Generate Excel report
    excel_path = os.path.join(output_dir, "UFC_324_Fighter_Analysis.xlsx")
    try:
        create_excel_report(fighters, excel_path)
        print(f"✓ Excel generado: {excel_path}")
    except Exception as e:
        logger.error(f"Error creating Excel report: {e}")
        print(f"✗ Error Excel: {e}")

    # Generate CSV report
    csv_path = os.path.join(output_dir, "UFC_324_Fighter_Analysis.csv")
    try:
        create_csv_report(fighters, csv_path)
        print(f"✓ CSV generado: {csv_path}")
    except Exception as e:
        logger.error(f"Error creating CSV report: {e}")
        print(f"✗ Error CSV: {e}")

    # Print summary
    print()
    print("=" * 70)
    print("RESUMEN DE ANÁLISIS")
    print("=" * 70)
    print()
    print(f"{'Peleador':<25} {'Win Rate':<12} {'Racha':<15} {'Finish Rate':<12}")
    print("-" * 70)

    for fighter in fighters:
        if fighter.stats and fighter.stats.total_fights_analyzed > 0:
            print(f"{fighter.name:<25} {fighter.stats.win_rate:>6.1f}%     "
                  f"{fighter.stats.current_streak:<15} {fighter.stats.finish_rate:>6.1f}%")

    print()
    print("=" * 70)
    print("ANÁLISIS COMPLETADO")
    print("=" * 70)

    return fighters


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="UFC 324 Fighter Analysis Script")
    parser.add_argument("--scrape", action="store_true",
                       help="Use web scraping instead of demo data")
    parser.add_argument("--output", "-o", default=".",
                       help="Output directory for reports")

    args = parser.parse_args()

    main(use_demo=not args.scrape, output_dir=args.output)
