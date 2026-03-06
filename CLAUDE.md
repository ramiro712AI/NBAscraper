# CLAUDE.md — NBAscraper

This file provides context for AI assistants working on the NBAscraper project.

---

## Project Overview

NBAscraper is a Python sports-data scraping project that automatically detects which NBA (and NHL) games are scheduled for the current day, fetches the last N completed games for each participating team, and outputs per-player quarter/period statistics as CSV files for downstream analysis (e.g., sports betting, DFS, research).

Data sources:
- **NBA**: ESPN public API (`site.api.espn.com`)
- **NHL**: NHL Stats API (`statsapi.web.nhl.com`)

No database, no web server, no authentication, no CI/CD. Pure Python scripts that produce CSV files.

---

## Repository Structure

```
NBAscraper/
├── nba_auto_scraper.py              # NBA scraper v1 — Q1 + totals only
├── nba_nuevo.py                     # NBA scraper v3 — all 4 quarters + totals
├── nhl_scraper.py.txt               # NHL scraper (rename to .py before running)
├── run_nba_scraper.bat              # Windows launcher for nba_auto_scraper.py
└── espn_api_response_401809996.json # Sample ESPN API response for debugging
```

### File Roles

| File | Purpose |
|------|---------|
| `nba_auto_scraper.py` | Original NBA scraper; extracts Q1 stats + game totals |
| `nba_nuevo.py` | Enhanced NBA scraper; extracts Q1–Q4 stats + game totals |
| `nhl_scraper.py.txt` | NHL scraper; extracts period 1 & 2 goals/assists/shots |
| `run_nba_scraper.bat` | Convenience launcher on Windows (hardcoded path) |
| `espn_api_response_401809996.json` | Fixture file used for inspecting ESPN JSON structure |

The **active/preferred NBA script is `nba_nuevo.py`** — it supersedes `nba_auto_scraper.py` with full 4-quarter breakdowns.

---

## Dependencies

No `requirements.txt` exists. Required packages:

```
requests   # HTTP calls to ESPN / NHL APIs
pandas     # DataFrame construction and CSV export
```

Standard-library modules used: `datetime`, `time`, `re`, `os`, `collections.defaultdict`.

Install with:
```bash
pip install requests pandas
```

---

## Running the Scrapers

### NBA (preferred)
```bash
python nba_nuevo.py
```

### NBA (legacy)
```bash
python nba_auto_scraper.py
```

### NHL
```bash
# rename file first
cp nhl_scraper.py.txt nhl_scraper.py
python nhl_scraper.py
```

### Windows batch launcher
Double-click `run_nba_scraper.bat` (path is hardcoded to `C:\Users\gomez\OneDrive\Desktop\NBAscraper`).

---

## API Integrations

### ESPN (NBA)

Base URL: `https://site.api.espn.com/apis/site/v2/sports/basketball/nba/`

| Endpoint | Used For |
|----------|----------|
| `scoreboard?dates={YYYYMMDD}` | Today's game schedule |
| `teams/{team_id}/schedule` | Last N completed games for a team |
| `summary?event={game_id}` | Boxscore + play-by-play for a game |

Key request config:
```python
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
timeout = 10          # seconds per request
sleep   = 0.5–1.0    # seconds between requests (rate limiting)
```

### NHL Stats API

Base URL: `https://statsapi.web.nhl.com/api/v1`

| Endpoint | Used For |
|----------|----------|
| `/schedule?date={YYYY-MM-DD}` | Today's NHL schedule |
| `/game/{gamePk}/feed/live` | Full game feed with play-by-play |
| `/people/{personId}/stats?stats=gameLog` | Player's game-by-game log |

Key config (top of `nhl_scraper.py.txt`):
```python
MAX_LAST_GAMES = 5    # how many past games to fetch per player
DATE_MANUAL    = None # set to "YYYY-MM-DD" to override today's date
SLEEP_BETWEEN  = 0.6  # seconds between API calls
```

---

## Code Conventions

### Naming
- Functions: `snake_case` — e.g., `get_todays_games()`, `get_quarter_stats_from_playbyplay()`
- Constants: `UPPER_CASE` — e.g., `TEAM_ABBREVIATIONS`, `HEADERS`, `BASE_URL`
- Variables: `snake_case`

### Error Handling
- All API calls are wrapped in `try/except` blocks.
- Errors are printed to stdout; the script continues gracefully.
- No exceptions are intentionally re-raised; missing data results in zeros or skipped rows.

### Data Flow
```
ESPN/NHL JSON API
      ↓
Python dicts / defaultdict
      ↓
List of row dicts
      ↓
pandas DataFrame
      ↓
CSV file (named with team abbreviations and date)
```

### Output Files
NBA scrapers generate one CSV per team playing today, e.g.:
```
LAL_vs_GSW_2024-01-15.csv
```
Columns follow the pattern `STAT_Qn` for per-quarter stats and `STAT_TOTAL` for game totals.

NHL scraper generates a single CSV for all players across today's games.

---

## Data Models

### NBA Player Row (`nba_nuevo.py`)

```python
{
    'Game_Date':  str,   # "YYYY-MM-DD"
    'Opponent':   str,   # opponent team abbreviation
    'Player':     str,   # player full name
    # Per-quarter
    'PTS_Q1': int, 'REB_Q1': int, 'AST_Q1': int, '3PM_Q1': int,
    'PTS_Q2': int, 'REB_Q2': int, 'AST_Q2': int, '3PM_Q2': int,
    'PTS_Q3': int, 'REB_Q3': int, 'AST_Q3': int, '3PM_Q3': int,
    'PTS_Q4': int, 'REB_Q4': int, 'AST_Q4': int, '3PM_Q4': int,
    # Game totals
    'PTS_TOTAL': int, 'REB_TOTAL': int, 'AST_TOTAL': int, '3PM_TOTAL': int,
}
```

### NHL Player Row

```python
{
    'GameDate':   str,   # "YYYY-MM-DD"
    'GamePk':     int,   # NHL game ID
    'PlayerID':   int,
    'PlayerName': str,
    'Team':       str,   # team abbreviation
    'Opponent':   str,
    'Period':     str,   # "1", "2", "TOTAL", etc.
    'G':          int,   # Goals
    'A':          int,   # Assists
    'Shots':      int,
    'Source':     str,   # "TODAY" or "LAST_N"
}
```

---

## Key Functions

### NBA (`nba_nuevo.py` — canonical version)

| Function | Description |
|----------|-------------|
| `get_todays_games()` | Calls ESPN scoreboard; returns list of `(home_abbr, away_abbr)` pairs |
| `get_team_schedule(team_id, limit=5)` | Returns last N completed game IDs for a team |
| `get_boxscore_totals(game_id, team_id)` | Extracts per-player total stats from boxscore JSON |
| `get_quarter_stats_from_playbyplay(game_id, team_id)` | Parses play-by-play text to assign events to Q1–Q4 |
| `process_team(team_abbr)` | Orchestrates all scraping for one team; returns list of row dicts |
| `main()` | Entry point; calls `process_team()` for each team playing today; writes CSVs |

### NHL (`nhl_scraper.py.txt`)

| Function | Description |
|----------|-------------|
| `get_schedule_for_date(d)` | Fetches today's NHL schedule |
| `get_game_feed(gamePk)` | Downloads full game JSON feed |
| `get_player_game_log(personId, max_games)` | Fetches player's recent game stats |
| `process_feed_for_game(gamePk)` | Parses goals/assists/shots from a game feed |
| `merge_stats(existing, newdata)` | Combines period-level stats across multiple games |
| `main()` | Entry point; outputs combined CSV |

---

## Team Reference

The NBA scrapers include a hardcoded mapping of 30 teams:

```python
TEAM_ABBREVIATIONS = {
    'ATL': team_id, 'BOS': team_id, 'BKN': team_id, ...
}
```

When adding or modifying team mappings, update both `TEAM_ABBREVIATIONS` and the corresponding ESPN `team_id` integer. ESPN team IDs can be verified via the scoreboard API response.

---

## Development Guidelines

1. **Prefer `nba_nuevo.py` over `nba_auto_scraper.py`** for any NBA enhancements — it has the full quarter breakdown and is the actively maintained version.

2. **Rate limiting is mandatory.** Always include `time.sleep(0.5)` or longer between ESPN/NHL API calls to avoid being throttled or blocked.

3. **Do not add a database layer** unless explicitly requested. The CSV-output design is intentional for simplicity and portability.

4. **Validate against the fixture file** when debugging ESPN API parsing — `espn_api_response_401809996.json` shows the exact JSON structure returned by the summary endpoint.

5. **No test suite exists.** When making structural changes, manually run the script against a known game date and inspect the output CSV.

6. **The NHL file has a `.txt` extension** intentionally (likely to avoid accidental execution). Rename to `.py` locally before running; do not commit it renamed unless that is the intent.

7. **Comments and variable names may be in Spanish** — this is intentional and should be preserved in existing code. New additions can use either English or Spanish, but be consistent within a function.

8. **Do not hardcode dates.** Use `datetime.date.today()` or the `DATE_MANUAL` override pattern already established in `nhl_scraper.py.txt`.

---

## Git Workflow

- Remote: `http://local_proxy@127.0.0.1:23576/git/ramiro712AI/NBAscraper`
- Default development branch pattern: `claude/<session-id>`
- Commit messages should be descriptive and in English.
- Push with: `git push -u origin <branch-name>`

---

## Known Limitations / TODOs

- No `requirements.txt` — add one for reproducibility.
- No `.gitignore` — generated CSVs and `__pycache__/` are not excluded.
- `run_nba_scraper.bat` has a hardcoded Windows path (`C:\Users\gomez\...`) — update if moving machines.
- `nhl_scraper.py.txt` must be manually renamed to `.py` before use.
- No handling for overtime periods in NBA or NHL.
- No deduplication guard if the same game appears in multiple API pages.
