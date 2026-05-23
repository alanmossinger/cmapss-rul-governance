"""Centralized configuration for the cmapss_rul package."""
from pathlib import Path

# Project root (resolved at import time)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Data
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Model artifacts
MODEL_DIR = PROJECT_ROOT / "models"

# Subsets
CMAPSS_SUBSETS = ("FD001", "FD002", "FD003", "FD004")

# Preprocessing
DEFAULT_WINDOW_SIZE = 30
DEFAULT_RUL_CLIP = 125

# Drift monitor thresholds
PSI_INVESTIGATE = 0.10
PSI_ROLLBACK = 0.25
