"""
SQLAlchemy ORM models and database setup.

Tables:
- signals:    Every generated signal with full metadata
- alerts:     Triggered alerts (subset of signals that crossed threshold)
- watchlists: User-defined symbol watchlists
- scan_logs:  Each scanner run metadata
"""

from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Float, Integer, String, Text, create_engine
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from market_scanner.config import DB_URL


engine = create_engine(DB_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    asset_type = Column(String(10), nullable=False)   # "crypto" | "stock"
    timeframe = Column(String(5), nullable=False)
    strategy = Column(String(50), nullable=False)
    signal_type = Column(String(20), nullable=False)  # "buy" | "sell" | "strong_buy" | etc.
    score = Column(Float, nullable=False)
    score_label = Column(String(20))                  # "weak" | "moderate" | "strong" | "very_strong"
    price = Column(Float)
    entry_zone = Column(String(30))
    stop_loss = Column(Float)
    take_profit_1 = Column(Float)
    take_profit_2 = Column(Float)
    risk_reward = Column(Float)
    atr_value = Column(Float)
    # Signal reason (JSON string of contributing rules)
    reasons = Column(Text)
    # Crypto-specific
    exchange_list = Column(Text)  # comma-separated
    # Stock-specific
    options_bias = Column(String(20))   # "calls" | "puts" | "neutral" | "avoid"
    iv_rank = Column(Float)
    sector = Column(String(50))
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(Integer, nullable=True)
    symbol = Column(String(20), nullable=False, index=True)
    asset_type = Column(String(10), nullable=False)
    timeframe = Column(String(5))
    strategy = Column(String(50))
    alert_type = Column(String(30), nullable=False)  # "buy" | "sell" | "breakout" | "volume" | etc.
    score = Column(Float)
    price = Column(Float)
    message = Column(Text)
    delivered = Column(Boolean, default=False)
    delivery_channels = Column(String(100))  # "in_app,telegram,webhook"
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class WatchlistItem(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    asset_type = Column(String(10), nullable=False)
    list_name = Column(String(50), default="default")
    priority = Column(Integer, default=0)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class ScanLog(Base):
    __tablename__ = "scan_logs"

    id = Column(Integer, primary_key=True, index=True)
    scan_type = Column(String(20))  # "crypto" | "stock"
    timeframe = Column(String(5))
    symbols_scanned = Column(Integer, default=0)
    signals_generated = Column(Integer, default=0)
    alerts_triggered = Column(Integer, default=0)
    duration_seconds = Column(Float)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)


def init_db() -> None:
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Dependency-inject a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
