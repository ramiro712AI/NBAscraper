# NCAAB Prediction Pipeline

Professional college basketball prediction engine for daily game picks.
Produces win probabilities and projected margins for all NCAAB games today,
ranked by confidence from highest to lowest.

---

## Quick Start

```bash
pip install -r requirements.txt
python main.py                    # today's games (America/New_York)
python main.py --date 2026-02-18  # specific date
python main.py --debug            # verbose logging
```

---

## Output

**Terminal:**
1. Full table of all games (sorted by tip time)
2. `FINAL RANKING` section – #1 through #N, ordered strictly by win probability
   (5 key factors per pick)

**Files:**
- `outputs/ncaab_picks_YYYYMMDD.csv`
- `outputs/ncaab_picks_YYYYMMDD.json`

---

## Prediction Model

### A) Power Rating
```
Net = Adj_Off − Adj_Def   (KenPom-style net efficiency)
Base_Margin = Net_A − Net_B
```

### B) Adjustments
| Factor | Description | Cap |
|---|---|---|
| Home-court | +3.0 pts for home team; 0 neutral | — |
| Four-Factors matchup | eFG%, TOV%, ORB%, FTR vs opponent's defensive values | ±3 pts |
| Recent form | L10 record differential × 0.25 | ±2 pts |
| Scoring-margin trend | L10 margin differential × 0.10 | ±1.5 pts |

### C) Win Probability (logistic)
```
P(win) = 1 / (1 + exp(−margin / k))     k = 7.5
```
| Margin | Win prob |
|---|---|
| +3 | 66% |
| +7.5 | 73% |
| +11 | 82% |
| +15 | 87% |
| +22 | 95% |

### D) Four-Factor Weights
| Factor | Coefficient | Basketball basis |
|---|---|---|
| eFG% | 0.10 pts per 1% edge | Shooting quality (40% weight per Oliver) |
| TOV% | 0.12 pts per 1% edge | Possession preservation (25%) |
| ORB% | 0.06 pts per 1% edge | Second-chance points (20%) |
| FTR  | 1.50 pts per 0.01 edge | Free-throw opportunities (15%) |

---

## Data Sources (Live)

| Source | Data |
|---|---|
| ESPN public API | Today's schedule, game metadata |
| Sports Reference / Barttorvik | Adjusted efficiency, four factors |

Live sources are attempted first; the pipeline falls back to an embedded
2025-26 season database (KenPom-style estimates for all ~350 programs) if
network access is unavailable.

---

## Architecture

```
ncaab_predictor/
├── main.py            # Orchestrator (3-step pipeline)
├── requirements.txt
├── src/
│   ├── utils.py       # Logging, disk cache, rate limiter, HTTP helpers
│   ├── schedule.py    # ESPN schedule fetch + hardcoded Feb 18 2026 fallback
│   ├── stats.py       # Team stats fetch + comprehensive embedded DB
│   ├── model.py       # Power-rating model + logistic prediction
│   └── output.py      # Terminal display + CSV/JSON export
├── outputs/           # Generated picks (CSV + JSON)
└── cache/             # 6-hour disk cache for API responses
```

---

## Example Output (Feb 18 2026)

```
==========================================================================================
   ★  FINAL RANKING – TOP FAVORITES TODAY  ★
   Ordered strictly by win probability (highest → lowest)
==========================================================================================

  #   Favorite                       vs Opponent                    Prob    Margin  Conf
─────────────────────────────────────────────────────────────────────────────────────────
  #1  [AP#4] Arizona Wildcats  (H)   vs BYU Cougars                91.9%   +18.2  Big 12
  #2         Drake Bulldogs    (H)   vs SIU Edwardsville           91.0%   +17.4  MVC
  #3         Tennessee         (H)   vs Oklahoma                   88.2%   +15.1  SEC
  #4         Louisiana Tech    (H)   vs Jackson State              87.4%   +14.5  CUSA
  #5  [AP#11] Gonzaga Bulldogs (A)   vs San Francisco              87.2%   +14.4  WCC
  ...
  #58        Murray State      (A)   vs Illinois State             50.7%    +0.2  OVC
```

---

## Notes

- **No betting odds used** — purely statistical model
- Home-court advantage calibrated at +3.0 pts (NCAAB historical average)
- Logistic scale factor k=7.5 (wider than NBA due to higher variance)
- Four-factors adjustments are additive corrections on top of net-efficiency base
- For games with missing data, a synthetic low-major estimate is used
