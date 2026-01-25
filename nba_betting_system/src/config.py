"""
Configuration management for NBA Betting System
"""

import os
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_PATH = PROJECT_ROOT / os.getenv("DATA_RAW_PATH", "data_raw")
DATA_PROCESSED_PATH = PROJECT_ROOT / os.getenv("DATA_PROCESSED_PATH", "data_processed")
MODELS_PATH = PROJECT_ROOT / os.getenv("MODELS_PATH", "models")
REPORTS_PATH = PROJECT_ROOT / os.getenv("REPORTS_PATH", "reports")

# Create directories if they don't exist
for path in [DATA_RAW_PATH, DATA_PROCESSED_PATH, MODELS_PATH, REPORTS_PATH]:
    path.mkdir(parents=True, exist_ok=True)

# API Keys
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")

# Environment
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file

    Args:
        config_path: Path to config.yaml (default: PROJECT_ROOT/config.yaml)

    Returns:
        Dictionary with configuration
    """
    if config_path is None:
        config_path = PROJECT_ROOT / "config.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        logger.warning(f"Config file not found at {config_path}, using defaults")
        return {}

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    logger.info(f"Configuration loaded from {config_path}")
    return config


# Load global config
CONFIG = load_config()


# Configure logging
def setup_logging():
    """Setup loguru logging"""
    log_config = CONFIG.get('logging', {})
    level = log_config.get('level', LOG_LEVEL)

    # Remove default handler
    logger.remove()

    # Add console handler
    logger.add(
        lambda msg: print(msg, end=""),
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=level,
        colorize=True
    )

    # Add file handler if specified
    log_file = log_config.get('file')
    if log_file:
        log_path = PROJECT_ROOT / log_file
        log_path.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            str(log_path),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
            level=level,
            rotation="10 MB",
            retention="30 days"
        )

    logger.info(f"Logging configured at {level} level")


# Setup logging on import
setup_logging()
