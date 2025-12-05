#!/usr/bin/env python3
"""
NBA Combo Props Analyzer
Scrapes last 6 games for players and generates comprehensive betting analysis
Author: NBA Props Analysis System
Date: December 5, 2025
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import time
import re
from typing import Dict, List, Tuple, Optional
import traceback
import statistics
from collections import defaultdict

# ============================================================================
# CONFIGURATION DATA
# ============================================================================

# Prop lines by game and category - EXACT players from screenshots
PROPS_DATA = {
    'LAL_BOS': {
        'game_name': 'LAL @ BOS',
        'game_time': '7:00pm EST',
        'PTS_AST': {
            'Austin Reaves': {'team': 'LAL', 'line': 40.5},
            'Jaylen Brown': {'team': 'BOS', 'line': 34.5},
            'Derrick White': {'team': 'BOS', 'line': 22.5},
            'Payton Pritchard': {'team': 'BOS', 'line': 21.5},
            'Anfernee Simons': {'team': 'BOS', 'line': 15.5},
        },
        'PTS_REB': {
            'Austin Reaves': {'team': 'LAL', 'line': 36.5},
            'Jaylen Brown': {'team': 'BOS', 'line': 35.5},
            'Derrick White': {'team': 'BOS', 'line': 21.5},
            'Payton Pritchard': {'team': 'BOS', 'line': 20.5},
            'Neemias Queta': {'team': 'BOS', 'line': 19.5},
            'Anfernee Simons': {'team': 'BOS', 'line': 14.5},
            'Jordan Walsh': {'team': 'BOS', 'line': 12.5},
        },
        'PTS_AST_REB': {
            'Austin Reaves': {'team': 'LAL', 'line': 45.5},
            'Jaylen Brown': {'team': 'BOS', 'line': 40.5},
            'Derrick White': {'team': 'BOS', 'line': 26.5},
            'Payton Pritchard': {'team': 'BOS', 'line': 25.5},
            'Neemias Queta': {'team': 'BOS', 'line': 21.5},
            'Anfernee Simons': {'team': 'BOS', 'line': 17.5},
        },
        'AST_REB': {
            'Austin Reaves': {'team': 'LAL', 'line': 14.5},
            'Jaylen Brown': {'team': 'BOS', 'line': 11.5},
            'Neemias Queta': {'team': 'BOS', 'line': 10.5},
            'Derrick White': {'team': 'BOS', 'line': 9.5},
            'Payton Pritchard': {'team': 'BOS', 'line': 8.5},
        },
    },
    'MIA_ORL': {
        'game_name': 'MIA @ ORL',
        'game_time': '7:00pm EST',
        'PTS_AST': {
            'Franz Wagner': {'team': 'ORL', 'line': 28.5},
            'Tyler Herro': {'team': 'MIA', 'line': 25.5},
            'Bam Adebayo': {'team': 'MIA', 'line': 21.5},
            'Jalen Suggs': {'team': 'ORL', 'line': 20.5},
            'Paolo Banchero': {'team': 'ORL', 'line': 20.5},
            'Anthony Black': {'team': 'ORL', 'line': 17.5},
        },
        'PTS_REB': {
            'Franz Wagner': {'team': 'ORL', 'line': 30.5},
            'Bam Adebayo': {'team': 'MIA', 'line': 27.5},
            'Tyler Herro': {'team': 'MIA', 'line': 25.5},
            'Paolo Banchero': {'team': 'ORL', 'line': 23.5},
            'Wendell Carter Jr.': {'team': 'ORL', 'line': 19.5},
            'Jalen Suggs': {'team': 'ORL', 'line': 19.5},
        },
        'PTS_AST_REB': {
            'Franz Wagner': {'team': 'ORL', 'line': 34.5},
            'Bam Adebayo': {'team': 'MIA', 'line': 30.5},
            'Tyler Herro': {'team': 'MIA', 'line': 29.5},
            'Paolo Banchero': {'team': 'ORL', 'line': 26.5},
            'Jalen Suggs': {'team': 'ORL', 'line': 24.5},
            'Wendell Carter Jr.': {'team': 'ORL', 'line': 21.5},
            'Anthony Black': {'team': 'ORL', 'line': 20.5},
        },
        'AST_REB': {
            'Bam Adebayo': {'team': 'MIA', 'line': 11.5},
            'Franz Wagner': {'team': 'ORL', 'line': 10.5},
            'Wendell Carter Jr.': {'team': 'ORL', 'line': 9.5},
            'Paolo Banchero': {'team': 'ORL', 'line': 9.5},
            'Jalen Suggs': {'team': 'ORL', 'line': 8.5},
            'Tyler Herro': {'team': 'MIA', 'line': 7.5},
        },
    },
    'SAS_CLE': {
        'game_name': 'SAS @ CLE',
        'game_time': '7:30pm EST',
        'PTS_AST': {
            'Donovan Mitchell': {'team': 'CLE', 'line': 35.5},
            'Evan Mobley': {'team': 'CLE', 'line': 24.5},
            'Devin Vassell': {'team': 'SAS', 'line': 18.5},
            'Harrison Barnes': {'team': 'SAS', 'line': 14.5},
            'Keldon Johnson': {'team': 'SAS', 'line': 14.5},
        },
        'PTS_REB': {
            'Donovan Mitchell': {'team': 'CLE', 'line': 34.5},
            'Evan Mobley': {'team': 'CLE', 'line': 30.5},
            'Devin Vassell': {'team': 'SAS', 'line': 19.5},
            'Keldon Johnson': {'team': 'SAS', 'line': 19.5},
            'Harrison Barnes': {'team': 'SAS', 'line': 16.5},
        },
        'PTS_AST_REB': {
            'Donovan Mitchell': {'team': 'CLE', 'line': 40.5},
            'Evan Mobley': {'team': 'CLE', 'line': 34.5},
            'Devin Vassell': {'team': 'SAS', 'line': 22.5},
            'Keldon Johnson': {'team': 'SAS', 'line': 21.5},
            'Harrison Barnes': {'team': 'SAS', 'line': 18.5},
        },
        'AST_REB': {
            'Evan Mobley': {'team': 'CLE', 'line': 13.5},
            'Donovan Mitchell': {'team': 'CLE', 'line': 10.5},
            'Keldon Johnson': {'team': 'SAS', 'line': 8.5},
        },
    },
}

# Player color palette - Unique color for each player
PLAYER_COLORS = {
    # LAL @ BOS
    'Austin Reaves': 'FFC7CE',          # Light pink
    'Jaylen Brown': 'E4DFEC',           # Light purple
    'Derrick White': 'D9D9D9',          # Light gray
    'Payton Pritchard': 'FFF2CC',       # Light cream
    'Anfernee Simons': 'B4C7E7',        # Light steel blue
    'Neemias Queta': 'DDEBF7',          # Light sky blue
    'Jordan Walsh': 'E2EFDA',           # Light mint

    # MIA @ ORL
    'Franz Wagner': 'C5D9F1',           # Light blue
    'Tyler Herro': 'C6EFCE',            # Light green
    'Bam Adebayo': 'FFEB9C',            # Light yellow
    'Paolo Banchero': 'F4B084',         # Light orange
    'Jalen Suggs': 'FCE4D6',            # Light peach
    'Wendell Carter Jr.': 'D5F4E6',     # Light seafoam
    'Anthony Black': 'FDEADA',          # Light tan

    # SAS @ CLE
    'Donovan Mitchell': 'D9E1F2',       # Light periwinkle
    'Evan Mobley': 'F8CBAD',            # Light coral
    'Devin Vassell': 'C9DAF8',          # Light lavender
    'Keldon Johnson': 'D5A6BD',         # Light mauve
    'Harrison Barnes': 'CFE2F3',        # Light ice blue
}

# Category display names
CATEGORY_NAMES = {
    'PTS_AST': 'Points + Assists',
    'PTS_REB': 'Points + Rebounds',
    'PTS_AST_REB': 'Points + Assists + Rebounds',
    'AST_REB': 'Assists + Rebounds',
}

# ============================================================================
# ESPN SCRAPING FUNCTIONS
# ============================================================================

def find_player_id(player_name: str, team: str = None) -> Optional[str]:
    """
    Search ESPN for player ID using their name
    Returns the ESPN player ID or None if not found
    """
    try:
        # Clean player name for URL
        search_name = player_name.lower().replace(' ', '-').replace("'", '').replace('.', '')

        # Try direct URL first (most reliable)
        # ESPN URLs are typically: espn.com/nba/player/_/id/{ID}/{name}
        # We'll need to search and parse

        search_url = f"https://www.espn.com/nba/players"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        # Alternative: Use ESPN's search API
        api_url = f"https://site.api.espn.com/apis/common/v3/search"
        params = {
            'query': player_name,
            'limit': 5,
            'type': 'player',
            'sport': 'basketball',
            'league': 'nba'
        }

        response = requests.get(api_url, params=params, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if 'results' in data and len(data['results']) > 0:
                for result in data['results']:
                    if result.get('type') == 'Player':
                        # Extract player ID from URL
                        url = result.get('url', '')
                        match = re.search(r'/id/(\d+)/', url)
                        if match:
                            player_id = match.group(1)
                            print(f"    Found player ID: {player_id} for {player_name}")
                            return player_id

        # Fallback: Try known player IDs (hardcoded for reliability)
        KNOWN_PLAYER_IDS = {
            'Donovan Mitchell': '3934672',
            'Jaylen Brown': '3917376',
            'Tyler Herro': '4395628',
            'Bam Adebayo': '4066636',
            'Franz Wagner': '4433627',
            'Paolo Banchero': '4432811',
            'Austin Reaves': '4397020',
            'Evan Mobley': '4433991',
            'Derrick White': '2990984',
            'Jalen Suggs': '4433137',
            'Payton Pritchard': '4278129',
            'Devin Vassell': '4395725',
            'Keldon Johnson': '4066648',
            'Harrison Barnes': '6475',
            'Wendell Carter Jr.': '4066421',
            'Neemias Queta': '4397124',
            'Anthony Black': '5104753',
            'Anfernee Simons': '4066757',
            'Jordan Walsh': '5105303',
        }

        if player_name in KNOWN_PLAYER_IDS:
            return KNOWN_PLAYER_IDS[player_name]

        print(f"    ⚠️  Could not find player ID for {player_name}")
        return None

    except Exception as e:
        print(f"    Error searching for {player_name}: {str(e)}")
        return None


def get_player_game_log(player_id: str, player_name: str, num_games: int = 6) -> List[Dict]:
    """
    Scrape last N games for a player from ESPN
    Returns list of game dictionaries with stats
    """
    try:
        # ESPN game log URL
        url = f"https://www.espn.com/nba/player/gamelog/_/id/{player_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            print(f"    Failed to fetch game log (Status: {response.status_code})")
            return []

        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the game log table
        games = []

        # ESPN's table structure for game logs
        table = soup.find('table', {'class': 'Table'})

        if not table:
            # Try alternative API endpoint
            api_url = f"https://site.api.espn.com/apis/common/v3/sports/basketball/nba/athletes/{player_id}/gamelog"
            response = requests.get(api_url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                # Parse API response
                if 'events' in data:
                    for event in data['events'][:num_games]:
                        game_info = parse_espn_api_game(event)
                        if game_info:
                            games.append(game_info)

            return games[:num_games]

        # Parse HTML table
        tbody = table.find('tbody')
        if not tbody:
            return []

        rows = tbody.find_all('tr')

        for row in rows[:num_games * 2]:  # Get extra rows in case of header rows
            if len(games) >= num_games:
                break

            cols = row.find_all('td')
            if len(cols) < 10:  # Skip header rows
                continue

            try:
                # Extract game data
                date_text = cols[0].get_text(strip=True)
                opponent = cols[1].get_text(strip=True)
                result = cols[2].get_text(strip=True)
                minutes = cols[3].get_text(strip=True)

                # Stats columns (order may vary)
                # Typical: FG, 3PT, FT, REB, AST, BLK, STL, PF, TO, PTS
                points = int(cols[-1].get_text(strip=True)) if cols[-1].get_text(strip=True).isdigit() else 0

                # Find rebounds and assists columns
                rebounds = 0
                assists = 0

                # Try to parse stats
                for i, col in enumerate(cols[4:], start=4):
                    text = col.get_text(strip=True)
                    # Rebounds typically before assists
                    if i == 7:  # Typical REB position
                        rebounds = int(text) if text.isdigit() else 0
                    if i == 8:  # Typical AST position
                        assists = int(text) if text.isdigit() else 0

                game_data = {
                    'date': parse_date(date_text),
                    'opponent': opponent,
                    'result': result,
                    'minutes': minutes,
                    'points': points,
                    'rebounds': rebounds,
                    'assists': assists,
                }

                games.append(game_data)

            except Exception as e:
                continue

        return games[:num_games]

    except Exception as e:
        print(f"    Error fetching game log: {str(e)}")
        return []


def parse_espn_api_game(event: Dict) -> Optional[Dict]:
    """Parse game data from ESPN API response"""
    try:
        # Extract stats from API response
        stats = event.get('stats', {})
        competition = event.get('competition', {})

        game_data = {
            'date': event.get('gameDate', 'N/A'),
            'opponent': competition.get('opponent', {}).get('abbreviation', 'N/A'),
            'result': 'W' if competition.get('won', False) else 'L',
            'minutes': stats.get('minutes', 0),
            'points': stats.get('points', 0),
            'rebounds': stats.get('rebounds', 0),
            'assists': stats.get('assists', 0),
        }

        return game_data
    except:
        return None


def parse_date(date_str: str) -> str:
    """Parse ESPN date format to YYYY-MM-DD"""
    try:
        # ESPN uses formats like "Tue, Dec 4", "Fri, Nov 28", etc.
        # Map month names to numbers
        month_map = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }

        # Try to match "Month Day" pattern (e.g., "Dec 4", "Nov 28")
        match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})', date_str)
        if match:
            month_name = match.group(1)
            day = int(match.group(2))
            month = month_map[month_name]

            # Get current date
            now = datetime.now()
            current_year = now.year
            current_month = now.month

            # NBA season logic:
            # Season runs Oct (10) - Jun (6)
            # If we're in Oct-Dec and game month is Oct-Dec: same year
            # If we're in Oct-Dec and game month is Jan-Jun: next year
            # If we're in Jan-Jun and game month is Oct-Dec: previous year
            # If we're in Jan-Jun and game month is Jan-Jun: same year
            # If we're in Jul-Sep (off-season): use previous season

            if current_month >= 10:  # Oct, Nov, Dec
                if month >= 10:  # Game in Oct-Dec
                    year = current_year
                else:  # Game in Jan-Jun (future games in next year)
                    year = current_year + 1
            elif current_month <= 6:  # Jan-Jun
                if month >= 10:  # Game in Oct-Dec (was last year)
                    year = current_year - 1
                else:  # Game in Jan-Jun (same year)
                    year = current_year
            else:  # Jul-Sep (off-season)
                # Assume looking at previous season
                if month >= 10:
                    year = current_year - 1
                else:
                    year = current_year

            return f"{year}-{month:02d}-{day:02d}"

        return date_str
    except:
        return date_str


# ============================================================================
# ADVANCED STATISTICAL ANALYSIS FUNCTIONS
# ============================================================================

def calculate_weighted_average(values: List[float], weights: List[float] = None) -> float:
    """
    Calculate weighted average with more weight on recent games
    Default: Last 3 games get 60% weight, first 3 get 40% weight
    """
    if not values:
        return 0.0

    if weights is None:
        # Default weights: recent games weighted more heavily
        n = len(values)
        if n <= 3:
            weights = [1.0] * n  # Equal weight for 3 or fewer games
        else:
            # Last 3 games: 20% each (60% total)
            # First 3 games: 13.33% each (40% total)
            weights = [0.1333] * (n - 3) + [0.2] * min(3, n)

    weighted_sum = sum(v * w for v, w in zip(values, weights))
    total_weight = sum(weights)

    return round(weighted_sum / total_weight, 2) if total_weight > 0 else 0.0


def calculate_consistency_score(values: List[float]) -> Dict:
    """
    Calculate consistency metrics using standard deviation
    Lower std_dev = more consistent
    Returns consistency score (0-100) where 100 = most consistent
    """
    if len(values) < 2:
        return {
            'std_dev': 0.0,
            'consistency_score': 100.0,
            'consistency_rating': 'INSUFFICIENT DATA'
        }

    try:
        mean = statistics.mean(values)
        std_dev = statistics.stdev(values)

        # Calculate coefficient of variation (CV)
        cv = (std_dev / mean * 100) if mean != 0 else 0

        # Consistency score: lower CV = higher consistency
        # CV < 15% = Very Consistent (90-100)
        # CV 15-25% = Consistent (75-89)
        # CV 25-35% = Moderate (60-74)
        # CV 35-50% = Inconsistent (40-59)
        # CV > 50% = Very Inconsistent (0-39)

        if cv < 15:
            consistency_score = 100 - cv
            rating = 'VERY CONSISTENT'
        elif cv < 25:
            consistency_score = 90 - cv
            rating = 'CONSISTENT'
        elif cv < 35:
            consistency_score = 75 - cv
            rating = 'MODERATE'
        elif cv < 50:
            consistency_score = 60 - cv
            rating = 'INCONSISTENT'
        else:
            consistency_score = max(0, 50 - cv)
            rating = 'VERY INCONSISTENT'

        return {
            'std_dev': round(std_dev, 2),
            'coefficient_variation': round(cv, 2),
            'consistency_score': round(max(0, min(100, consistency_score)), 1),
            'consistency_rating': rating
        }
    except:
        return {
            'std_dev': 0.0,
            'coefficient_variation': 0.0,
            'consistency_score': 50.0,
            'consistency_rating': 'UNKNOWN'
        }


def calculate_confidence_level(avg: float, line: float, hit_rate: float,
                               consistency_score: float, trend: str) -> Dict:
    """
    Calculate professional confidence level for recommendation
    Considers: average vs line, hit rate, consistency, and trend
    """
    confidence_points = 0
    factors = []

    # Factor 1: Distance from line (max 30 points)
    diff = avg - line
    if abs(diff) >= 5:
        confidence_points += 30
        factors.append(f"Strong edge: {diff:+.1f} from line")
    elif abs(diff) >= 3:
        confidence_points += 20
        factors.append(f"Solid edge: {diff:+.1f} from line")
    elif abs(diff) >= 1.5:
        confidence_points += 10
        factors.append(f"Slight edge: {diff:+.1f} from line")

    # Factor 2: Hit rate (max 30 points)
    if hit_rate >= 83.3:  # 5/6 or better
        confidence_points += 30
        factors.append(f"Excellent hit rate: {hit_rate:.1f}%")
    elif hit_rate >= 66.7:  # 4/6
        confidence_points += 20
        factors.append(f"Good hit rate: {hit_rate:.1f}%")
    elif hit_rate >= 50:  # 3/6
        confidence_points += 10
        factors.append(f"Decent hit rate: {hit_rate:.1f}%")

    # Factor 3: Consistency (max 25 points)
    if consistency_score >= 85:
        confidence_points += 25
        factors.append("Very consistent performer")
    elif consistency_score >= 70:
        confidence_points += 18
        factors.append("Consistent performer")
    elif consistency_score >= 55:
        confidence_points += 10
        factors.append("Moderately consistent")

    # Factor 4: Trend (max 15 points)
    if trend == '↑' and diff > 0:
        confidence_points += 15
        factors.append("Trending up (favorable)")
    elif trend == '↓' and diff < 0:
        confidence_points += 15
        factors.append("Trending down (favorable)")
    elif trend == '→':
        confidence_points += 8
        factors.append("Stable trend")

    # Calculate final confidence level
    if confidence_points >= 80:
        level = 'VERY HIGH'
        stars = '⭐⭐⭐'
    elif confidence_points >= 60:
        level = 'HIGH'
        stars = '⭐⭐'
    elif confidence_points >= 40:
        level = 'MEDIUM'
        stars = '⭐'
    elif confidence_points >= 20:
        level = 'LOW'
        stars = '○'
    else:
        level = 'VERY LOW'
        stars = '○'

    return {
        'confidence_score': confidence_points,
        'confidence_level': level,
        'confidence_stars': stars,
        'factors': factors
    }


def analyze_opponent_performance(games: List[Dict], opponent_abbrev: str) -> Dict:
    """
    Analyze player's historical performance against specific opponent
    """
    opponent_games = [g for g in games if opponent_abbrev.upper() in g.get('opponent', '').upper()]

    if not opponent_games:
        return {
            'games_vs_opponent': 0,
            'avg_vs_opponent': 0.0,
            'matchup_edge': 'NO DATA'
        }

    avg_vs = statistics.mean([g.get('combo_value', 0) for g in opponent_games])

    return {
        'games_vs_opponent': len(opponent_games),
        'avg_vs_opponent': round(avg_vs, 1),
        'matchup_edge': 'FAVORABLE' if len(opponent_games) > 0 else 'NO DATA'
    }


# ============================================================================
# STATISTICS CALCULATION FUNCTIONS
# ============================================================================

def calculate_combo_stat(game: Dict, combo_type: str) -> int:
    """Calculate combo stat total for a single game"""
    pts = game.get('points', 0)
    reb = game.get('rebounds', 0)
    ast = game.get('assists', 0)

    if combo_type == 'PTS_AST':
        return pts + ast
    elif combo_type == 'PTS_REB':
        return pts + reb
    elif combo_type == 'PTS_AST_REB':
        return pts + ast + reb
    elif combo_type == 'AST_REB':
        return ast + reb
    else:
        return 0


def calculate_statistics(games: List[Dict], combo_type: str, line: float) -> Dict:
    """
    Calculate comprehensive statistics for a player's games
    Returns dict with totals, averages, trends, and analysis
    """
    if not games:
        return {
            'games': [],
            'total_minutes': 0,
            'total_points': 0,
            'total_rebounds': 0,
            'total_assists': 0,
            'total_combo': 0,
            'avg_combo': 0,
            'hit_rate': 0,
            'hit_count': 0,
            'trend': '→',
            'trend_diff': 0,
            'home_avg': 0,
            'away_avg': 0,
            'recommendation': 'N/A',
        }

    # Calculate combo totals for each game
    processed_games = []
    total_minutes = 0
    total_points = 0
    total_rebounds = 0
    total_assists = 0
    total_combo = 0
    hit_count = 0

    home_games = []
    away_games = []

    for game in games:
        combo_value = calculate_combo_stat(game, combo_type)

        # Determine if over/under
        vs_line = 'OVER' if combo_value > line else 'UNDER' if combo_value < line else 'PUSH'
        if combo_value > line:
            hit_count += 1

        # Determine home/away
        is_home = 'vs' in game.get('opponent', '')

        if is_home:
            home_games.append(combo_value)
        else:
            away_games.append(combo_value)

        processed_game = {
            **game,
            'combo_value': combo_value,
            'vs_line': vs_line,
            'is_home': is_home,
        }

        processed_games.append(processed_game)

        # Accumulate totals
        total_minutes += parse_minutes(game.get('minutes', 0))
        total_points += game.get('points', 0)
        total_rebounds += game.get('rebounds', 0)
        total_assists += game.get('assists', 0)
        total_combo += combo_value

    # Calculate averages
    num_games = len(games)
    avg_combo = round(total_combo / num_games, 1) if num_games > 0 else 0
    hit_rate = (hit_count / num_games * 100) if num_games > 0 else 0

    # Calculate trend (last 3 vs first 3)
    if num_games >= 6:
        last_3_avg = sum(g['combo_value'] for g in processed_games[:3]) / 3
        first_3_avg = sum(g['combo_value'] for g in processed_games[3:6]) / 3
        trend_diff = last_3_avg - first_3_avg

        if trend_diff >= 2.0:
            trend = '↑'
        elif trend_diff <= -2.0:
            trend = '↓'
        else:
            trend = '→'
    else:
        trend_diff = 0
        trend = '→'

    # Home/Away averages
    home_avg = round(sum(home_games) / len(home_games), 1) if home_games else 0
    away_avg = round(sum(away_games) / len(away_games), 1) if away_games else 0

    # ADVANCED STATISTICAL ANALYSIS
    # ============================================================================

    # Calculate weighted average (recent games weighted more heavily)
    combo_values = [g['combo_value'] for g in processed_games]
    weighted_avg = calculate_weighted_average(combo_values)

    # Calculate consistency metrics
    consistency_metrics = calculate_consistency_score(combo_values)

    # Generate basic recommendation
    recommendation = generate_recommendation(avg_combo, line, hit_rate)

    # Calculate professional confidence level
    confidence_analysis = calculate_confidence_level(
        weighted_avg,
        line,
        hit_rate,
        consistency_metrics['consistency_score'],
        trend
    )

    # Enhanced recommendation combining weighted average and confidence
    if confidence_analysis['confidence_level'] in ['VERY HIGH', 'HIGH']:
        if weighted_avg > line:
            enhanced_recommendation = f"OVER {confidence_analysis['confidence_stars']}"
        else:
            enhanced_recommendation = f"UNDER {confidence_analysis['confidence_stars']}"
    else:
        enhanced_recommendation = recommendation

    return {
        'games': processed_games,
        'total_minutes': total_minutes,
        'total_points': total_points,
        'total_rebounds': total_rebounds,
        'total_assists': total_assists,
        'total_combo': total_combo,
        'avg_combo': avg_combo,
        'weighted_avg': weighted_avg,
        'hit_rate': hit_rate,
        'hit_count': hit_count,
        'num_games': num_games,
        'trend': trend,
        'trend_diff': round(trend_diff, 1),
        'home_avg': home_avg,
        'away_avg': away_avg,
        'home_count': len(home_games),
        'away_count': len(away_games),
        'recommendation': recommendation,
        'enhanced_recommendation': enhanced_recommendation,
        # Advanced metrics
        'std_dev': consistency_metrics['std_dev'],
        'consistency_score': consistency_metrics['consistency_score'],
        'consistency_rating': consistency_metrics['consistency_rating'],
        'confidence_score': confidence_analysis['confidence_score'],
        'confidence_level': confidence_analysis['confidence_level'],
        'confidence_stars': confidence_analysis['confidence_stars'],
        'confidence_factors': confidence_analysis['factors'],
    }


def parse_minutes(minutes_str) -> float:
    """Parse minutes string to float"""
    try:
        if isinstance(minutes_str, (int, float)):
            return float(minutes_str)

        if ':' in str(minutes_str):
            parts = str(minutes_str).split(':')
            return float(parts[0]) + float(parts[1]) / 60

        return float(minutes_str)
    except:
        return 0.0


def generate_recommendation(avg: float, line: float, hit_rate: float) -> str:
    """
    Generate betting recommendation based on statistics
    """
    diff = avg - line

    if diff >= 2.0 and hit_rate >= 67:
        return 'OVER ⭐'
    elif diff <= -2.0 and hit_rate <= 33:
        return 'UNDER ⭐'
    elif diff >= 1.0 and hit_rate >= 50:
        return 'SLIGHT OVER'
    elif diff <= -1.0 and hit_rate <= 50:
        return 'SLIGHT UNDER'
    else:
        return 'PASS'


# ============================================================================
# EXCEL GENERATION FUNCTIONS
# ============================================================================

def create_excel_report(all_data: Dict, filename: str):
    """
    Generate comprehensive Excel report with color coding
    """
    print("\n" + "="*80)
    print("GENERATING EXCEL REPORT")
    print("="*80)

    wb = openpyxl.Workbook()
    wb.remove(wb.active)  # Remove default sheet

    # Create summary sheet first
    summary_sheet = wb.create_sheet('SUMMARY', 0)

    # Create sheets for each game/category combination
    sheet_data = {}

    for game_key, categories in PROPS_DATA.items():
        game_name = categories['game_name']
        game_time = categories['game_time']

        for category_key, players in categories.items():
            if category_key in ['game_name', 'game_time']:
                continue

            sheet_name = f"{game_key}_{category_key}"
            category_name = CATEGORY_NAMES[category_key]

            # Create sheet
            ws = wb.create_sheet(sheet_name)
            sheet_data[sheet_name] = []

            print(f"\nCreating sheet: {sheet_name}")
            print(f"  Category: {category_name}")
            print(f"  Players: {len(players)}")

            current_row = 1

            # Sheet title
            ws.merge_cells(f'A{current_row}:I{current_row}')
            title_cell = ws[f'A{current_row}']
            title_cell.value = f"{game_name} - {category_name}"
            title_cell.font = Font(size=16, bold=True)
            title_cell.alignment = Alignment(horizontal='center', vertical='center')
            current_row += 2

            # Process each player
            for player_name, player_info in players.items():
                team = player_info['team']
                line = player_info['line']

                # Get player data
                data_key = f"{game_key}_{category_key}_{player_name}"

                if data_key in all_data:
                    player_data = all_data[data_key]
                    stats = player_data['stats']

                    # Add player section to sheet
                    current_row = add_player_section(
                        ws, current_row, player_name, team, category_name,
                        category_key, line, stats
                    )

                    # Collect summary data
                    sheet_data[sheet_name].append({
                        'player': player_name,
                        'team': team,
                        'line': line,
                        'avg': stats['avg_combo'],
                        'weighted_avg': stats['weighted_avg'],
                        'hit_rate': stats['hit_rate'],
                        'trend': stats['trend'],
                        'consistency_score': stats['consistency_score'],
                        'consistency_rating': stats['consistency_rating'],
                        'confidence_level': stats['confidence_level'],
                        'confidence_stars': stats['confidence_stars'],
                        'recommendation': stats['recommendation'],
                        'enhanced_recommendation': stats['enhanced_recommendation'],
                    })
                else:
                    # Player data not available
                    current_row = add_player_section_na(
                        ws, current_row, player_name, team, category_name, line
                    )

            # Auto-adjust column widths
            for column in ws.columns:
                max_length = 0
                column_letter = get_column_letter(column[0].column)
                for cell in column:
                    try:
                        if cell.value:
                            max_length = max(max_length, len(str(cell.value)))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column_letter].width = adjusted_width

    # Create summary sheet
    create_summary_sheet(summary_sheet, sheet_data, all_data)

    # Save workbook
    wb.save(filename)
    print(f"\n{'='*80}")
    print(f"Excel file saved: {filename}")
    print(f"{'='*80}\n")


def add_player_section(ws, start_row: int, player_name: str, team: str,
                       category_name: str, category_key: str, line: float,
                       stats: Dict) -> int:
    """
    Add a player's data section to worksheet
    Returns the next available row
    """
    current_row = start_row

    # Get player color
    player_color = PLAYER_COLORS.get(player_name, 'FFFFFF')
    header_fill = PatternFill(start_color=player_color, end_color=player_color, fill_type='solid')

    # Darker shade for header
    header_font = Font(size=12, bold=True, color='000000')

    # Player header
    ws.merge_cells(f'A{current_row}:I{current_row}')
    header_cell = ws[f'A{current_row}']
    header_cell.value = f"PLAYER: {player_name} ({team})"
    header_cell.fill = header_fill
    header_cell.font = header_font
    header_cell.alignment = Alignment(horizontal='center', vertical='center')
    current_row += 1

    # Category and line info
    ws.merge_cells(f'A{current_row}:I{current_row}')
    info_cell = ws[f'A{current_row}']
    info_cell.value = f"CATEGORY: {category_name} | PROP LINE: O {line} / U {line}"
    info_cell.fill = header_fill
    info_cell.font = Font(size=10, bold=True)
    info_cell.alignment = Alignment(horizontal='center', vertical='center')
    current_row += 1

    # Separator
    ws.merge_cells(f'A{current_row}:I{current_row}')
    sep_cell = ws[f'A{current_row}']
    sep_cell.value = "=" * 80
    sep_cell.fill = header_fill
    current_row += 1

    # Column headers
    headers = ['Game #', 'Date', 'Opponent', 'Result', 'MIN', 'PTS', 'REB', 'AST']

    # Add combo column based on category
    combo_header = category_name.replace(' + ', '+')
    headers.append(combo_header)
    headers.append('vs Line')

    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=current_row, column=col_idx)
        cell.value = header
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color='D3D3D3', end_color='D3D3D3', fill_type='solid')
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

    current_row += 1

    # Game rows
    games = stats['games']
    light_fill = PatternFill(start_color=player_color, end_color=player_color, fill_type='solid')

    for game_num, game in enumerate(games, start=1):
        row_data = [
            game_num,
            game.get('date', 'N/A'),
            game.get('opponent', 'N/A'),
            game.get('result', 'N/A'),
            game.get('minutes', 0),
            game.get('points', 0),
            game.get('rebounds', 0),
            game.get('assists', 0),
            game.get('combo_value', 0),
            game.get('vs_line', 'N/A'),
        ]

        for col_idx, value in enumerate(row_data, start=1):
            cell = ws.cell(row=current_row, column=col_idx)
            cell.value = value
            cell.fill = light_fill
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )

            # Color code vs_line
            if col_idx == 10:  # vs Line column
                if value == 'OVER':
                    cell.font = Font(bold=True, color='006100')  # Green
                elif value == 'UNDER':
                    cell.font = Font(bold=True, color='9C0006')  # Red

        current_row += 1

    # Totals row
    total_row_data = [
        'TOTAL',
        '',
        '',
        f"{sum(1 for g in games if 'W' in g.get('result', ''))}W-{sum(1 for g in games if 'L' in g.get('result', ''))}L",
        round(stats['total_minutes'], 1),
        stats['total_points'],
        stats['total_rebounds'],
        stats['total_assists'],
        stats['total_combo'],
        f"{stats['hit_count']}/{stats['num_games']} OVER",
    ]

    for col_idx, value in enumerate(total_row_data, start=1):
        cell = ws.cell(row=current_row, column=col_idx)
        cell.value = value
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color='808080', end_color='808080', fill_type='solid')
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = Border(
            left=Side(style='medium'),
            right=Side(style='medium'),
            top=Side(style='medium'),
            bottom=Side(style='medium')
        )

    current_row += 1

    # Average row
    avg_row_data = [
        'AVG',
        '',
        '',
        '',
        round(stats['total_minutes'] / stats['num_games'], 1) if stats['num_games'] > 0 else 0,
        round(stats['total_points'] / stats['num_games'], 1) if stats['num_games'] > 0 else 0,
        round(stats['total_rebounds'] / stats['num_games'], 1) if stats['num_games'] > 0 else 0,
        round(stats['total_assists'] / stats['num_games'], 1) if stats['num_games'] > 0 else 0,
        stats['avg_combo'],
        f"{round(stats['hit_rate'], 1)}%",
    ]

    for col_idx, value in enumerate(avg_row_data, start=1):
        cell = ws.cell(row=current_row, column=col_idx)
        cell.value = value
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color='A9A9A9', end_color='A9A9A9', fill_type='solid')
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = Border(
            left=Side(style='medium'),
            right=Side(style='medium'),
            top=Side(style='medium'),
            bottom=Side(style='medium')
        )

    current_row += 2

    # Analysis section
    ws.merge_cells(f'A{current_row}:I{current_row}')
    analysis_cell = ws[f'A{current_row}']

    analysis_text = f"""PROFESSIONAL STATISTICAL ANALYSIS:

📊 AVERAGES:
• Simple Average: {stats['avg_combo']} vs Line ({line}): {stats['avg_combo'] - line:+.1f}
• Weighted Average (Recent Games Priority): {stats['weighted_avg']} vs Line: {stats['weighted_avg'] - line:+.1f}
• Home/Away Split: Home {stats['home_count']}G (avg {stats['home_avg']}) | Away {stats['away_count']}G (avg {stats['away_avg']})

📈 PERFORMANCE METRICS:
• Hit Rate: {stats['hit_count']}/{stats['num_games']} games OVER ({stats['hit_rate']:.1f}%)
• Trend: {stats['trend']} {"IMPROVING" if stats['trend'] == "↑" else "DECLINING" if stats['trend'] == "↓" else "STABLE"} (Last 3 vs First 3: {stats['trend_diff']:+.1f})
• Standard Deviation: {stats['std_dev']}

🎯 CONSISTENCY ANALYSIS:
• Consistency Score: {stats['consistency_score']}/100
• Rating: {stats['consistency_rating']}
• {"Very reliable performer" if stats['consistency_score'] >= 85 else "Consistent enough for props" if stats['consistency_score'] >= 70 else "Moderate consistency - use caution" if stats['consistency_score'] >= 55 else "Highly variable performance"}

💪 CONFIDENCE LEVEL: {stats['confidence_level']} {stats['confidence_stars']}
• Confidence Score: {stats['confidence_score']}/100
{chr(10).join(f"  ✓ {factor}" for factor in stats['confidence_factors'][:4])}

🎲 FINAL RECOMMENDATION: {stats['enhanced_recommendation']}
{"━" * 50}"""

    analysis_cell.value = analysis_text
    analysis_cell.fill = light_fill
    analysis_cell.font = Font(size=9)
    analysis_cell.alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
    ws.row_dimensions[current_row].height = 100

    current_row += 2

    # Separator
    ws.merge_cells(f'A{current_row}:I{current_row}')
    ws[f'A{current_row}'].value = ""
    current_row += 2

    return current_row


def add_player_section_na(ws, start_row: int, player_name: str, team: str,
                          category_name: str, line: float) -> int:
    """Add N/A section for player with no data"""
    current_row = start_row

    player_color = PLAYER_COLORS.get(player_name, 'FFFFFF')
    header_fill = PatternFill(start_color=player_color, end_color=player_color, fill_type='solid')

    ws.merge_cells(f'A{current_row}:I{current_row}')
    header_cell = ws[f'A{current_row}']
    header_cell.value = f"PLAYER: {player_name} ({team}) - DATA NOT AVAILABLE"
    header_cell.fill = header_fill
    header_cell.font = Font(size=12, bold=True, color='FF0000')
    header_cell.alignment = Alignment(horizontal='center', vertical='center')

    current_row += 3

    return current_row


def create_summary_sheet(ws, sheet_data: Dict, all_data: Dict):
    """Create summary sheet with all recommendations"""
    current_row = 1

    # Title
    ws.merge_cells(f'A{current_row}:H{current_row}')
    title_cell = ws[f'A{current_row}']
    title_cell.value = "NBA COMBO PROPS ANALYSIS - December 5, 2025"
    title_cell.font = Font(size=18, bold=True)
    title_cell.alignment = Alignment(horizontal='center', vertical='center')
    current_row += 1

    ws.merge_cells(f'A{current_row}:H{current_row}')
    timestamp_cell = ws[f'A{current_row}']
    timestamp_cell.value = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    timestamp_cell.font = Font(size=10, italic=True)
    timestamp_cell.alignment = Alignment(horizontal='center', vertical='center')
    current_row += 3

    # Process each game
    for game_key, categories in PROPS_DATA.items():
        game_name = categories['game_name']
        game_time = categories['game_time']

        # Game header
        ws.merge_cells(f'A{current_row}:H{current_row}')
        game_header = ws[f'A{current_row}']
        game_header.value = f"GAME: {game_name} ({game_time})"
        game_header.font = Font(size=14, bold=True, color='FFFFFF')
        game_header.fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
        game_header.alignment = Alignment(horizontal='center', vertical='center')
        current_row += 1

        ws.merge_cells(f'A{current_row}:H{current_row}')
        sep_cell = ws[f'A{current_row}']
        sep_cell.value = "=" * 100
        current_row += 1

        # Process each category
        for category_key, players in categories.items():
            if category_key in ['game_name', 'game_time']:
                continue

            category_name = CATEGORY_NAMES[category_key]
            sheet_name = f"{game_key}_{category_key}"

            # Category header
            ws.merge_cells(f'A{current_row}:H{current_row}')
            cat_header = ws[f'A{current_row}']
            cat_header.value = category_name.upper()
            cat_header.font = Font(size=12, bold=True)
            cat_header.fill = PatternFill(start_color='D3D3D3', end_color='D3D3D3', fill_type='solid')
            cat_header.alignment = Alignment(horizontal='center', vertical='center')
            current_row += 1

            # Table headers
            headers = ['Player', 'Team', 'Weighted Avg', 'Line', 'Diff', 'Hit Rate', 'Consistency', 'Confidence', 'Recommendation']
            for col_idx, header in enumerate(headers, start=1):
                cell = ws.cell(row=current_row, column=col_idx)
                cell.value = header
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color='B8B8B8', end_color='B8B8B8', fill_type='solid')
                cell.alignment = Alignment(horizontal='center', vertical='center')
                cell.border = Border(
                    left=Side(style='thin'),
                    right=Side(style='thin'),
                    top=Side(style='thin'),
                    bottom=Side(style='thin')
                )

            current_row += 1

            # Player data
            if sheet_name in sheet_data:
                for player_data in sheet_data[sheet_name]:
                    player_color = PLAYER_COLORS.get(player_data['player'], 'FFFFFF')
                    fill = PatternFill(start_color=player_color, end_color=player_color, fill_type='solid')

                    diff = player_data['weighted_avg'] - player_data['line']

                    row_data = [
                        player_data['player'],
                        player_data['team'],
                        player_data['weighted_avg'],
                        player_data['line'],
                        f"{diff:+.1f}",
                        f"{player_data['hit_rate']:.1f}%",
                        f"{player_data['consistency_score']:.0f} ({player_data['consistency_rating'][:8]})",
                        f"{player_data['confidence_level']} {player_data['confidence_stars']}",
                        player_data['enhanced_recommendation'],
                    ]

                    for col_idx, value in enumerate(row_data, start=1):
                        cell = ws.cell(row=current_row, column=col_idx)
                        cell.value = value
                        cell.fill = fill
                        cell.alignment = Alignment(horizontal='center', vertical='center')
                        cell.border = Border(
                            left=Side(style='thin'),
                            right=Side(style='thin'),
                            top=Side(style='thin'),
                            bottom=Side(style='thin')
                        )

                        # Color code recommendation
                        if col_idx == 8:  # Recommendation column
                            if '⭐' in str(value):
                                cell.font = Font(bold=True, size=11)

                    current_row += 1

            current_row += 1

        current_row += 1

    # Auto-adjust column widths
    for column in ws.columns:
        max_length = 0
        column_letter = get_column_letter(column[0].column)
        for cell in column:
            try:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    print("\n" + "="*80)
    print("NBA COMBO PROPS ANALYZER")
    print("="*80)
    print(f"Analysis Date: December 5, 2025")
    print(f"Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")

    all_data = {}

    # Process each game and category
    total_players = 0
    successful_players = 0
    failed_players = 0

    for game_key, categories in PROPS_DATA.items():
        game_name = categories['game_name']
        print(f"\n{'='*80}")
        print(f"PROCESSING GAME: {game_name}")
        print(f"{'='*80}")

        for category_key, players in categories.items():
            if category_key in ['game_name', 'game_time']:
                continue

            category_name = CATEGORY_NAMES[category_key]
            print(f"\n  Category: {category_name}")
            print(f"  Players: {len(players)}")
            print(f"  {'-'*76}")

            for player_name, player_info in players.items():
                total_players += 1
                team = player_info['team']
                line = player_info['line']

                print(f"\n  [{total_players}] Processing: {player_name} ({team})")
                print(f"      Category: {category_name}")
                print(f"      Prop Line: {line}")

                try:
                    # Find player ID
                    player_id = find_player_id(player_name, team)

                    if not player_id:
                        print(f"      ✗ Could not find player ID")
                        failed_players += 1
                        continue

                    # Get game log
                    print(f"      Fetching last 6 games...")
                    games = get_player_game_log(player_id, player_name, num_games=6)

                    if not games:
                        print(f"      ✗ No game data available")
                        failed_players += 1
                        continue

                    print(f"      ✓ Retrieved {len(games)} games")

                    # Calculate statistics
                    stats = calculate_statistics(games, category_key, line)

                    # Store data
                    data_key = f"{game_key}_{category_key}_{player_name}"
                    all_data[data_key] = {
                        'player': player_name,
                        'team': team,
                        'game': game_key,
                        'category': category_key,
                        'line': line,
                        'stats': stats,
                    }

                    print(f"      ✓ Avg: {stats['avg_combo']} | Line: {line} | Hit Rate: {stats['hit_rate']:.1f}%")
                    print(f"      ✓ Recommendation: {stats['recommendation']}")
                    successful_players += 1

                    # Rate limiting
                    time.sleep(1.5)

                except Exception as e:
                    print(f"      ✗ Error: {str(e)}")
                    print(f"      {traceback.format_exc()}")
                    failed_players += 1
                    continue

    # Summary
    print(f"\n{'='*80}")
    print(f"SCRAPING COMPLETE")
    print(f"{'='*80}")
    print(f"Total Players Processed: {total_players}")
    print(f"Successful: {successful_players}")
    print(f"Failed: {failed_players}")
    print(f"Success Rate: {(successful_players/total_players*100):.1f}%")
    print(f"{'='*80}\n")

    # Generate Excel report
    if all_data:
        filename = f'NBA_Combo_Props_Analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        create_excel_report(all_data, filename)

        print(f"\n{'='*80}")
        print(f"✓ ANALYSIS COMPLETE!")
        print(f"{'='*80}")
        print(f"Output File: {filename}")
        print(f"Total Players Analyzed: {successful_players}")
        print(f"Ready for betting analysis!")
        print(f"{'='*80}\n")
    else:
        print("\n⚠️  No data collected. Please check errors above.")


if __name__ == "__main__":
    main()
