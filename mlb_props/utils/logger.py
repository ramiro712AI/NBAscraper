"""Centralised logging configuration for MLB Props Analyzer."""
from __future__ import annotations

import logging
import sys
from pathlib import Path


def setup_logger(
    log_dir: str = "logs",
    log_level: str = "INFO",
    run_date: str = "",
) -> logging.Logger:
    """
    Configure root logger to write to both stdout and a dated file.

    Returns the root logger so callers can simply use logging.getLogger(__name__).
    """
    log_dir_path = Path(log_dir)
    log_dir_path.mkdir(parents=True, exist_ok=True)

    log_filename = log_dir_path / f"mlb_props{'_' + run_date if run_date else ''}.log"

    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(numeric_level)

    # Avoid duplicate handlers on repeated calls (e.g. tests)
    if root.handlers:
        root.handlers.clear()

    file_handler = logging.FileHandler(log_filename, encoding="utf-8")
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(fmt)
    root.addHandler(stream_handler)

    return root
