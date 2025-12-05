# NBA COMBO PROPS ANALYZER - QUICK START GUIDE

## 🚀 Get Started in 3 Steps

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the Script
```bash
python nba_combo_props_analyzer.py
```

### Step 3: Open the Excel File
The script will generate: `NBA_Combo_Props_Analysis_YYYYMMDD_HHMMSS.xlsx`

---

## 📊 What You Get

### ✅ SUMMARY Sheet
- All games at a glance
- Color-coded players
- Quick recommendations (OVER ⭐, UNDER ⭐, PASS)
- Hit rates and trends

### ✅ Detailed Sheets (one per game/category)
Each player section shows:
- Last 6 games with full stats
- Totals and averages
- Trend analysis (↑↓→)
- Home/Away splits
- Betting recommendation

---

## 🎯 Today's Games (December 5, 2024)

### Game 1: LAL @ BOS (7:00pm EST)
- 23 total player props across 4 categories
- Key players: Austin Reaves, Jaylen Brown, Derrick White

### Game 2: MIA @ ORL (7:00pm EST)
- 25 total player props across 4 categories
- Key players: Franz Wagner, Tyler Herro, Bam Adebayo, Paolo Banchero

### Game 3: SAS @ CLE (7:30pm EST)
- 18 total player props across 4 categories
- Key players: Donovan Mitchell, Evan Mobley, Devin Vassell

**Total: 66 player props analyzed!**

---

## 🔍 Reading the Analysis

### Understanding Recommendations

| Recommendation | Meaning |
|---------------|---------|
| **OVER ⭐** | Strong statistical edge for OVER (avg beats line by 2+, hit rate 67%+) |
| **UNDER ⭐** | Strong statistical edge for UNDER (avg below line by 2+, hit rate 33%-) |
| **SLIGHT OVER** | Marginal edge for OVER (avg beats line by 1-2, hit rate 50%+) |
| **SLIGHT UNDER** | Marginal edge for UNDER (avg below line by 1-2, hit rate 50%-) |
| **PASS** | No clear statistical advantage |

### Understanding Trends

| Trend | Meaning |
|-------|---------|
| **↑ IMPROVING** | Last 3 games average is 2+ higher than first 3 games |
| **↓ DECLINING** | Last 3 games average is 2+ lower than first 3 games |
| **→ STABLE** | Less than 2 points difference (consistent) |

### Hit Rate
- Shows how many of last 6 games went OVER the prop line
- Example: "5/6 OVER (83.3%)" = Player went over the line in 5 out of 6 games

---

## ⚡ Expected Runtime

- **Total time**: 3-7 minutes
- **Per player**: ~3-5 seconds (includes rate limiting)
- **66 players**: ~3-6 minutes total

The script has built-in rate limiting to avoid being blocked by ESPN.

---

## 🎨 Color Coding

Each player has a unique background color throughout the entire report:
- Makes it easy to scan multiple sheets
- Quick visual identification
- Professional, readable design

Example colors:
- 🟢 Tyler Herro: Light Green
- 🟡 Bam Adebayo: Light Yellow
- 🔵 Franz Wagner: Light Blue
- 🟠 Paolo Banchero: Light Orange
- 🟣 Jaylen Brown: Light Purple
- ⚪ Derrick White: Light Gray

---

## 📈 Sample Output

```
PLAYER: Tyler Herro (MIA)
CATEGORY: Points + Assists | PROP LINE: O 25.5 / U 25.5

| Game # | Date       | Opponent  | Result    | MIN | PTS | AST | PTS+AST | vs Line |
|--------|------------|-----------|-----------|-----|-----|-----|---------|---------|
| 1      | 2024-12-04 | vs LAL    | W 110-105 | 35  | 28  | 7   | 35      | OVER    |
| 2      | 2024-12-02 | @ MEM     | L 98-105  | 33  | 22  | 5   | 27      | OVER    |
| ...

TOTAL: 189 | AVG: 31.5

ANALYSIS:
• Average (31.5) vs Line (25.5): +6.0 ADVANTAGE
• Hit Rate: 5 out of 6 games OVER (83.3%)
• Trend: ↑ IMPROVING
• RECOMMENDATION: OVER ⭐
```

---

## 🛠️ Troubleshooting

### Script runs but no data collected?
- ESPN might be blocking requests
- Try running at a different time
- Check your internet connection

### Player not found?
- Verify player name spelling
- Check if player is active (not injured)
- See README for adding custom player IDs

### Excel file not opening?
- Make sure you have Excel, Google Sheets, or LibreOffice installed
- File extension is .xlsx (standard Excel format)

---

## 💡 Pro Tips

1. **Run Early**: Give yourself time to analyze before games start
2. **Cross-Reference**: Compare with your own research and injury reports
3. **Check Minutes**: Low minutes = unreliable projections
4. **Watch Trends**: Improving players (↑) on good hit rates are gold
5. **Home/Away Matters**: Some players perform very differently by location

---

## 📝 Quick Customization

### Want to analyze different games?
Edit the `PROPS_DATA` dictionary in `nba_combo_props_analyzer.py`

### Want more games analyzed?
Change `num_games=6` to `num_games=10` in the script

### Want different categories?
The script supports:
- PTS_AST (Points + Assists)
- PTS_REB (Points + Rebounds)
- PTS_AST_REB (Points + Assists + Rebounds)
- AST_REB (Assists + Rebounds)

---

## 🎯 Success Metrics

After running, you should see:
```
================================================================================
ANALYSIS COMPLETE!
================================================================================
Output File: NBA_Combo_Props_Analysis_20241205_143022.xlsx
Total Players Analyzed: 66
Ready for betting analysis!
================================================================================
```

---

## 📚 Need More Help?

- Read `README_COMBO_PROPS.md` for full documentation
- Run `python test_script_structure.py` to validate setup
- Check console output for detailed progress and errors

---

**Happy Betting! 🏀💰**

*Remember: This is a tool for analysis, not a guarantee. Always bet responsibly!*
