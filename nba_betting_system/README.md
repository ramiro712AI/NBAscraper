# 🏀 NBA Betting System - Probabilistic EV-Based Betting

**A professional, reproducible NBA betting system based on Expected Value (EV) and probability theory.**

> ⚠️ **DISCLAIMER**: This system is for EDUCATIONAL and RESEARCH purposes only. Sports betting involves risk. Never bet more than you can afford to lose. Past performance does not guarantee future results.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Philosophy](#philosophy)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Methodology](#methodology)
- [Responsible Gambling](#responsible-gambling)

---

## 🎯 Overview

This system implements a **quantitative approach** to NBA sports betting using:
- **Probabilistic modeling** (not "99% accuracy" promises)
- **Expected Value (EV)** calculation
- **Kelly Criterion** for bet sizing
- **Walk-forward backtesting** to avoid overfitting
- **Probability calibration** for accurate confidence
- **Risk management** with configurable limits

**Goal**: Identify positive EV opportunities where model probability > market probability.

---

## 🧠 Philosophy

### What This System IS:
✅ A **probabilistic framework** for betting decisions
✅ Focused on **long-term Expected Value**
✅ **Honest about uncertainty** and variance
✅ **Risk-managed** with position sizing
✅ **Reproducible** and transparent

### What This System IS NOT:
❌ A "get rich quick" scheme
❌ A "99% accuracy" predictor
❌ A guarantee of profits
❌ Financial advice

**Key Insight**: In sports betting, you don't need to win 99% of bets. You need to win **slightly more than the market expects**, and size your bets accordingly.

---

## ✨ Features

### Data Collection
- NBA game statistics via `nba_api` with caching
- Odds data from The Odds API (with CSV stub fallback)
- Manual injury tracking (CSV-based)
- Travel/rest days calculation

### Feature Engineering
- Team rolling statistics (ORtg, DRtg, pace, eFG%, etc.)
- Home/away splits
- Rest days, back-to-back, 3-in-4 game flags
- Strength of schedule proxy
- Injury impact (optional)
- Market features

### Modeling
- **Classification**: Logistic Regression + LightGBM for moneyline/spread
- **Regression**: Ridge + Gradient Boosting for totals
- **Calibration**: Platt Scaling / Isotonic Regression
- **Evaluation**: Log loss, Brier score, AUC, calibration curves

### Betting Strategy
- EV calculation: `EV = p_model * payout - (1 - p_model)`
- Kelly Criterion for optimal bet sizing (fractional)
- Configurable filters:
  - Minimum EV threshold (e.g., 2%)
  - Probability range filters
  - Max bets per day
  - Max exposure limits

### Backtesting
- **Walk-forward** temporal validation
- No data leakage
- Performance metrics: ROI, yield, max drawdown, hit rate
- Calibration tracking

---

## 🚀 Installation

### Prerequisites
- Python 3.9+
- pip or conda

### Setup

```bash
# Clone or navigate to project
cd nba_betting_system

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your API keys (optional)
nano .env
```

### Optional: The Odds API Key

To fetch live odds, sign up at [The Odds API](https://the-odds-api.com/) and add your key to `.env`:

```
ODDS_API_KEY=your_key_here
```

Without a key, the system uses CSV stubs (manual entry).

---

## 🎬 Quick Start

### 1. Check System Info

```bash
python -m src.cli info
```

### 2. Fetch NBA Data

```bash
# Fetch all games for current season
python -m src.cli fetch-games --season 2024-25

# Fetch games for specific date range
python -m src.cli fetch-games --start-date 2024-10-01 --end-date 2024-12-31
```

### 3. Fetch Odds Data

```bash
# Fetch today's odds
python -m src.cli fetch-odds

# Fetch odds for specific date
python -m src.cli fetch-odds --date 2025-01-15
```

### 4. Generate Predictions

```bash
# Generate predictions and bet recommendations
python -m src.cli predict --date 2025-01-15 --market moneyline --bankroll 10000
```

Output: Bet card with filtered picks, EV%, recommended bet sizes.

### 5. View Disclaimer

```bash
python -m src.cli disclaimer
```

---

## 📖 Usage

### Command Reference

```bash
# Fetch NBA game data
python -m src.cli fetch-games [OPTIONS]
  --season TEXT        NBA season (default: 2024-25)
  --start-date TEXT    Start date (YYYY-MM-DD)
  --end-date TEXT      End date (YYYY-MM-DD)

# Fetch odds data
python -m src.cli fetch-odds [OPTIONS]
  --date TEXT          Date for odds (YYYY-MM-DD)

# Generate predictions
python -m src.cli predict [OPTIONS]
  --date TEXT          Prediction date (required)
  --market TEXT        Market type (moneyline, spread, totals)
  --bankroll FLOAT     Current bankroll (default: 10000)

# System information
python -m src.cli info

# Responsible gambling disclaimer
python -m src.cli disclaimer
```

---

## 📁 Project Structure

```
nba_betting_system/
├── README.md                   # This file
├── requirements.txt            # Python dependencies
├── config.yaml                 # System configuration
├── .env.example                # Environment template
│
├── data_raw/                   # Raw data (cached)
│   ├── games_*.parquet
│   ├── odds_stub.csv           # Manual odds entry
│   └── injuries.csv            # Manual injury tracking
│
├── data_processed/             # Processed features
│   └── features_*.parquet
│
├── models/                     # Trained models
│   └── *.pkl
│
├── reports/                    # Generated reports
│   ├── backtest_*.html
│   └── bet_card_*.csv
│
├── src/                        # Source code
│   ├── __init__.py
│   ├── config.py               # Configuration management
│   ├── cli.py                  # Command-line interface
│   │
│   ├── ingest/                 # Data ingestion
│   │   ├── nba_data.py         # NBA stats fetcher
│   │   ├── odds_data.py        # Odds API + stub
│   │   └── injuries_stub.py    # Injury tracking
│   │
│   ├── features/               # Feature engineering
│   │   └── engineering.py      # Rolling stats, rest, etc.
│   │
│   ├── modeling/               # ML models
│   │   ├── models.py           # Model training
│   │   └── calibration.py      # Probability calibration
│   │
│   ├── backtest/               # Backtesting
│   │   └── backtester.py       # Walk-forward validation
│   │
│   └── betting/                # Betting strategy
│       └── strategy.py         # EV, Kelly, filters
│
└── tests/                      # Unit tests
    └── test_betting.py
```

---

## ⚙️ Configuration

Edit `config.yaml` to customize:

### Betting Parameters

```yaml
betting:
  min_ev_pct: 2.0              # Minimum EV to bet
  kelly_fraction: 0.25          # Fractional Kelly (0.25 = Quarter Kelly)
  max_bet_pct: 5.0              # Never bet more than 5% of bankroll
  max_bets_per_day: 5           # Limit number of bets
```

### Modeling

```yaml
modeling:
  models:
    moneyline:
      - logistic_regression
      - lightgbm
  calibration:
    method: isotonic            # or 'platt'
```

### Data Sources

```yaml
data:
  odds_api:
    enabled: true
    use_stub_if_no_key: true
```

---

## 🔬 Methodology

### 1. **Data Collection**
- Historical NBA game data (nba_api)
- Closing odds from multiple sportsbooks
- Injury reports (manual tracking)

### 2. **Feature Engineering**
- Rolling team statistics (last N games)
- Rest days, travel, back-to-back flags
- Opponent strength metrics
- Home/away adjustments

### 3. **Model Training**
- Train on historical data with temporal splits (no leakage)
- Multiple models: Logistic Regression, LightGBM, Ridge, Gradient Boosting
- Calibrate probabilities using Platt or Isotonic methods

### 4. **Probability Calibration**
- Ensures `p(win) = 0.60` actually means 60% win rate
- Critical for accurate EV calculation

### 5. **EV Calculation**
```
EV = p_model × (decimal_odds - 1) - (1 - p_model)
EV% = EV × 100
```

Only bet if:
- `EV% > min_ev_pct` (e.g., 2%)
- `p_model` in reasonable range (e.g., 40-80%)

### 6. **Bet Sizing (Kelly Criterion)**
```
kelly% = (p × (decimal_odds - 1) - (1 - p)) / (decimal_odds - 1)
bet_size = bankroll × kelly% × kelly_fraction
```

`kelly_fraction` (e.g., 0.25) reduces variance.

### 7. **Walk-Forward Backtesting**
- Train on data up to time `t`
- Predict on `t+1`
- Roll forward, avoiding future data leakage

### 8. **Performance Metrics**
- ROI (Return on Investment)
- Yield (profit per dollar wagered)
- Hit rate (% of winning bets)
- Max drawdown
- Calibration curves

---

## 🎲 Responsible Gambling

### **Key Principles**:
1. **Never bet more than you can afford to lose**
2. **Treat this as entertainment, not income**
3. **Variance is high** - expect losing streaks
4. **EV is long-term** - need 1000+ bets to converge
5. **Set strict bankroll limits**
6. **Take breaks if gambling becomes stressful**

### **Warning Signs**:
- Chasing losses
- Betting outside the system
- Increasing bet sizes after losses
- Gambling with money needed for bills

### **Get Help**:
- **National Council on Problem Gambling**: 1-800-522-4700
- **Online**: www.ncpgambling.org

---

## 📊 Example Bet Card

```
ACTIONABLE BETS for 2025-01-15

| Team         | Market    | Line  | Odds | Model% | Market% | EV%  | Edge  | Bet$ | Kelly% |
|--------------|-----------|-------|------|--------|---------|------|-------|------|--------|
| Lakers       | Moneyline | -     | -150 | 65.0   | 60.0    | 4.2  | 5.0   | 125  | 1.25   |
| Celtics OVER | Totals    | 221.5 | -110 | 57.0   | 52.4    | 3.1  | 4.6   | 85   | 0.85   |
| Warriors +5  | Spread    | +5    | -110 | 56.0   | 52.4    | 2.5  | 3.6   | 65   | 0.65   |

Total Exposure: $275 (2.75% of $10,000 bankroll)
```

**Interpretation**:
- All bets have **positive EV** (EV% > 2%)
- Model probabilities > market probabilities (**edge**)
- Bet sizes follow **fractional Kelly**
- Total exposure within limits

---

## 🧪 Testing

Run unit tests:

```bash
pytest tests/ -v
```

Test modules:
- `test_betting.py`: EV calculation, Kelly, odds conversion
- `test_data.py`: Data fetching and caching
- `test_features.py`: Feature engineering

---

## 🤝 Contributing

This is an educational project. Contributions welcome:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

---

## 📜 License

MIT License - See LICENSE file

---

## 🙏 Acknowledgments

- **nba_api**: For NBA data access
- **The Odds API**: For odds data
- **scikit-learn, LightGBM, XGBoost**: ML frameworks
- **Kelly Criterion**: J.L. Kelly Jr. (1956)

---

## 📞 Support

For issues or questions:
- GitHub Issues
- Email: support@example.com

---

## ⚠️ Final Reminder

**This system is NOT a guarantee of profits.**

Sports betting is:
- **High variance** (random outcomes)
- **Efficient markets** (hard to beat)
- **Long-term game** (need volume)

Use responsibly. Bet for fun, not profit.

**If gambling is no longer fun, STOP.**

---

**Good luck, and bet responsibly! 🍀📊**
