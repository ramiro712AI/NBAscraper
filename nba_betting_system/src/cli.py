"""
Command Line Interface for NBA Betting System
"""

import sys
from datetime import datetime
from pathlib import Path

import click
import pandas as pd
from loguru import logger
from rich.console import Console
from rich.table import Table

from src.betting.strategy import BettingStrategy
from src.config import CONFIG, DATA_PROCESSED_PATH, MODELS_PATH, REPORTS_PATH
from src.ingest.nba_data import NBADataFetcher
from src.ingest.odds_data import OddsFetcher

console = Console()


@click.group()
def cli():
    """NBA Betting System - Probabilistic betting based on EV"""
    pass


@cli.command()
@click.option('--date', default=None, help='Date to fetch odds for (YYYY-MM-DD)')
def fetch_odds(date):
    """Fetch odds data from API or stub"""
    console.print(f"[bold green]Fetching odds data...[/bold green]")

    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')

    odds_fetcher = OddsFetcher()
    odds_df = odds_fetcher.get_nba_odds(date)

    if not odds_df.empty:
        console.print(f"✓ Fetched {len(odds_df)} odds records for {date}")
        console.print(f"Saved to: {DATA_PROCESSED_PATH / f'odds_{date}.parquet'}")

        # Show sample
        console.print("\n[bold]Sample odds:[/bold]")
        console.print(odds_df.head(10))
    else:
        console.print(f"[yellow]No odds data found for {date}[/yellow]")


@cli.command()
@click.option('--season', default='2024-25', help='NBA season')
@click.option('--start-date', default=None, help='Start date (YYYY-MM-DD)')
@click.option('--end-date', default=None, help='End date (YYYY-MM-DD)')
def fetch_games(season, start_date, end_date):
    """Fetch NBA game data"""
    console.print(f"[bold green]Fetching NBA games for {season}...[/bold green]")

    nba_fetcher = NBADataFetcher()

    if start_date and end_date:
        games_df = nba_fetcher.get_games_by_date_range(start_date, end_date, season)
    else:
        games_df = nba_fetcher.get_season_games(season)

    console.print(f"✓ Fetched {len(games_df)} game records")
    console.print(f"Saved to: {DATA_PROCESSED_PATH}")


@cli.command()
@click.option('--date', required=True, help='Date to predict (YYYY-MM-DD)')
@click.option('--market', default='moneyline', help='Market: moneyline, spread, totals')
@click.option('--bankroll', default=10000, help='Current bankroll')
def predict(date, market, bankroll):
    """Generate predictions and betting recommendations"""
    console.print(f"[bold green]Generating predictions for {date}...[/bold green]")

    # This is a simplified demo - full implementation would load trained models
    console.print(f"[yellow]Note: This is a demo. Train models first using 'train' command[/yellow]")

    # Load odds
    odds_fetcher = OddsFetcher()
    odds_df = odds_fetcher.get_nba_odds(date)

    if odds_df.empty:
        console.print(f"[red]No odds data available for {date}[/red]")
        return

    # Demo: Create mock predictions (in real system, load trained model and predict)
    predictions = []
    for _, row in odds_df.head(10).iterrows():
        pred = {
            'game_id': row.get('game_id', 'unknown'),
            'team': row.get('name', 'unknown'),
            'market': market,
            'line': row.get('point', 'N/A'),
            'odds_american': row.get('price', -110),
            'prob_model': 0.55,  # Mock prediction
        }
        predictions.append(pred)

    predictions_df = pd.DataFrame(predictions)

    # Apply betting strategy
    strategy = BettingStrategy()
    filtered_bets = strategy.filter_bets(predictions_df, bankroll)

    if filtered_bets.empty:
        console.print("[yellow]No bets meet the criteria[/yellow]")
        return

    # Generate bet card
    bet_card = strategy.generate_bet_card(filtered_bets)

    # Display results
    console.print(f"\n[bold green]✓ Found {len(bet_card)} actionable bets:[/bold green]\n")

    table = Table(show_header=True, header_style="bold magenta")
    for col in bet_card.columns:
        table.add_column(col)

    for _, row in bet_card.iterrows():
        table.add_row(*[str(val) for val in row])

    console.print(table)

    # Save to file
    output_file = REPORTS_PATH / f"bet_card_{date}.csv"
    bet_card.to_csv(output_file, index=False)
    console.print(f"\n✓ Bet card saved to: {output_file}")


@cli.command()
def info():
    """Show system information and configuration"""
    console.print("[bold blue]NBA Betting System v1.0[/bold blue]\n")

    console.print(f"[bold]Configuration:[/bold]")
    console.print(f"  Min EV%: {CONFIG.get('betting', {}).get('min_ev_pct', 2.0)}%")
    console.print(f"  Kelly Fraction: {CONFIG.get('betting', {}).get('kelly_fraction', 0.25)}")
    console.print(f"  Max bets/day: {CONFIG.get('betting', {}).get('max_bets_per_day', 5)}")
    console.print(f"  Markets: {', '.join(CONFIG.get('betting', {}).get('markets', []))}")

    console.print(f"\n[bold]Data Paths:[/bold]")
    console.print(f"  Raw: {DATA_PROCESSED_PATH}")
    console.print(f"  Models: {MODELS_PATH}")
    console.print(f"  Reports: {REPORTS_PATH}")


@cli.command()
def disclaimer():
    """Show responsible gambling disclaimer"""
    console.print("\n[bold red]⚠️  IMPORTANT DISCLAIMER ⚠️[/bold red]\n")
    console.print("""
This NBA Betting System is for EDUCATIONAL and RESEARCH purposes only.

[yellow]Key Points:[/yellow]
• Sports betting involves RISK. You can lose money.
• Past performance does NOT guarantee future results.
• This system provides PROBABILITIES, not certainties.
• No system can predict outcomes with 100% accuracy.
• Expected Value (EV) is a long-term concept - variance is high.
• Always bet responsibly and within your means.
• Never bet more than you can afford to lose.
• Seek help if gambling becomes a problem: 1-800-GAMBLER

[bold]The developers assume NO LIABILITY for any losses incurred.[/bold]

Use this tool wisely and responsibly.
    """)


if __name__ == '__main__':
    cli()
