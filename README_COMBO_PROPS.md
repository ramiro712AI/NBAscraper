# NBA COMBO PROPS ANALYZER

A comprehensive Python tool for analyzing NBA player combo prop bets by scraping historical game data from ESPN and generating detailed Excel reports with betting recommendations.

## Features

✅ **Complete Data Extraction**: Scrapes last 6 games for each player from ESPN
✅ **Multiple Combo Categories**:
- Points + Assists (PTS+AST)
- Points + Rebounds (PTS+REB)
- Points + Assists + Rebounds (PTS+AST+REB)
- Assists + Rebounds (AST+REB)

✅ **Advanced Analytics**:
- Hit rate analysis (how often player goes OVER the line)
- Trend indicators (improving/declining/stable)
- Home/Away performance splits
- Comprehensive averages and totals

✅ **Beautiful Excel Reports**:
- Color-coded by player (unique color per player)
- Professional formatting with borders and fills
- Summary sheet with all recommendations
- Individual sheets per game/category combination

✅ **Smart Recommendations**:
- OVER ⭐ - Strong over recommendation
- UNDER ⭐ - Strong under recommendation
- SLIGHT OVER/UNDER - Marginal edge
- PASS - No clear advantage

## Games Analyzed (December 5, 2024)

1. **LAL @ BOS** - 7:00pm EST
2. **MIA @ ORL** - 7:00pm EST
3. **SAS @ CLE** - 7:30pm EST

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. Clone or download this repository

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Execution

Simply run the script:
```bash
python nba_combo_props_analyzer.py
```

The script will:
1. Process all configured games and players
2. Scrape last 6 games from ESPN for each player
3. Calculate combo statistics and trends
4. Generate a timestamped Excel file with complete analysis

### Expected Runtime
- **3-7 minutes** depending on network speed and ESPN response times
- Rate limiting is built-in (1.5 seconds between players) to avoid being blocked

### Output

The script generates an Excel file named:
```
NBA_Combo_Props_Analysis_YYYYMMDD_HHMMSS.xlsx
```

## Excel Report Structure

### Summary Sheet
- Overview of all games and categories
- Quick reference table with all players
- Color-coded recommendations
- Hit rates and trends at a glance

### Individual Game/Category Sheets
Each sheet contains:
- Player-specific sections with unique color coding
- Last 6 games with detailed statistics
- Opponent information and game results
- Minutes, Points, Rebounds, Assists for each game
- Combo totals calculated per game
- OVER/UNDER vs prop line for each game
- Total sums and averages
- Comprehensive analysis with:
  - Average vs Line comparison
  - Hit rate percentage
  - Trend indicator (↑↓→)
  - Home/Away splits
  - Betting recommendation

## Understanding the Analysis

### Trend Indicators
- **↑ IMPROVING**: Last 3 games average is 2+ points higher than first 3 games
- **↓ DECLINING**: Last 3 games average is 2+ points lower than first 3 games
- **→ STABLE**: Difference is less than 2 points

### Recommendations Logic
- **OVER ⭐**: Average exceeds line by 2+ AND hit rate ≥ 67%
- **UNDER ⭐**: Average below line by 2+ AND hit rate ≤ 33%
- **SLIGHT OVER**: Average exceeds line by 1-2 AND hit rate ≥ 50%
- **SLIGHT UNDER**: Average below line by 1-2 AND hit rate ≤ 50%
- **PASS**: No clear statistical advantage

## Advanced Features

### Home/Away Analysis
Each player's performance is split by:
- Home games (vs opponent)
- Away games (@ opponent)
- Separate averages calculated for each

### Hit Rate Calculation
Shows X/6 games where player went OVER the prop line
Percentage helps identify consistent performers

### Color Coding System
Each player has a unique background color throughout the report:
- Makes it easy to scan and compare
- Professional, readable design
- Consistent across all sheets

## Customization

### Adding New Players
Edit the `PROPS_DATA` dictionary in the script:

```python
PROPS_DATA = {
    'GAME_KEY': {
        'CATEGORY': {
            'Player Name': {'team': 'TEAM', 'line': X.X},
        }
    }
}
```

### Adding Player Colors
Edit the `PLAYER_COLORS` dictionary:

```python
PLAYER_COLORS = {
    'Player Name': 'HEX_COLOR',  # Example: 'C6EFCE' for light green
}
```

### Changing Number of Games
Modify the `num_games` parameter in `get_player_game_log()`:

```python
games = get_player_game_log(player_id, player_name, num_games=6)  # Change to 5, 10, etc.
```

## Troubleshooting

### Player Not Found
- Verify player name spelling matches ESPN exactly
- Check if player is active (not injured/traded)
- Add player ID to `KNOWN_PLAYER_IDS` dictionary if needed

### No Game Data
- Player might be newly signed or have limited games
- ESPN might have changed their HTML structure
- Check ESPN website directly to verify data availability

### Rate Limiting
- Script has built-in 1.5 second delays
- If you get blocked, increase the delay in `time.sleep(1.5)`
- Consider using a VPN if persistent issues occur

### Excel Formatting Issues
- Ensure openpyxl is properly installed
- Check that output directory has write permissions
- Verify Python has sufficient memory for large reports

## Data Source

**Primary Source**: ESPN (https://www.espn.com)
- Player game logs
- Box scores and statistics
- Real-time NBA data

**API Endpoints**:
- ESPN Search API for player IDs
- ESPN Stats API for game logs
- HTML scraping as fallback

## Technical Details

### Dependencies
- **pandas**: Data manipulation and analysis
- **requests**: HTTP requests to ESPN
- **beautifulsoup4**: HTML parsing
- **openpyxl**: Excel file generation and formatting
- **lxml**: XML/HTML parsing support

### Architecture
1. **Configuration Layer**: Game/player/prop line data
2. **Scraping Layer**: ESPN data extraction
3. **Calculation Layer**: Statistics and trend analysis
4. **Presentation Layer**: Excel report generation

### Error Handling
- Graceful degradation (continues if individual players fail)
- Detailed error logging to console
- N/A sections for unavailable data
- Retry logic for network issues

## Best Practices

1. **Run Before Game Time**: Give yourself time to analyze results
2. **Cross-Reference**: Compare with your own research
3. **Check Injury Reports**: Script doesn't account for injuries
4. **Consider Matchups**: Some players perform better/worse against certain teams
5. **Use as Guide**: Recommendations are statistical, not guaranteed

## Future Enhancements

Potential improvements (add if needed):
- [ ] Injury status integration
- [ ] Opponent defense rankings
- [ ] Player usage rate trends
- [ ] Recent lineup changes
- [ ] Weather conditions (if applicable)
- [ ] Vegas sharp money indicators
- [ ] Multiple sportsbook line comparison
- [ ] Historical accuracy tracking

## Formula Improvements

The script includes several advanced statistical formulas:

### Weighted Average (Recent Games Priority)
Instead of simple average, you could weight recent games more:
```python
# Weight last 3 games 60%, first 3 games 40%
weighted_avg = (last_3_avg * 0.6) + (first_3_avg * 0.4)
```

### Standard Deviation Analysis
Identify consistent vs volatile performers:
```python
std_dev = statistics.stdev([game['combo_value'] for game in games])
# Lower std_dev = more consistent
```

### Opponent-Adjusted Stats
Compare performance vs strong/weak defenses:
```python
# Adjust based on opponent's defensive rating
adjusted_stat = raw_stat * (league_avg_defense / opponent_defense)
```

### Rest Days Factor
Account for back-to-back games vs rested:
```python
# Players typically perform worse on second night of back-to-back
if is_back_to_back:
    adjusted_projection *= 0.95
```

## Support

For issues, questions, or suggestions:
1. Check the Troubleshooting section
2. Review ESPN's website to verify data availability
3. Verify all dependencies are correctly installed

## Disclaimer

This tool is for informational and entertainment purposes only. Sports betting involves risk. Always gamble responsibly and within your means. Past performance does not guarantee future results.

## License

This script is provided as-is for personal use. Feel free to modify and customize for your needs.

---

**Happy Analyzing! 🏀📊**
