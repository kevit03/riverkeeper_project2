"""Thin wrappers around the existing `app/functions/*` modules so the Dash
app can reuse all the data logic without duplicating it.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

# Make `app/functions` importable (matches how `app/front.py` bootstraps itself)
ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from functions.data_analysis import (  # noqa: E402
    active_donors,
    basic_stats,
    clean,
    frequent_donors,
    inactive_donors,
    stats_by_month,
    stats_by_state,
    stats_by_year,
    stats_no_location,
    top_donors,
)

PERSISTENT_RAW = APP_DIR / "data" / "donor_data.csv"
PERSISTENT_ENRICHED = APP_DIR / "data" / "donor_data_enriched.csv"


def load_enriched() -> pd.DataFrame:
    if PERSISTENT_ENRICHED.exists():
        try:
            return pd.read_csv(PERSISTENT_ENRICHED, on_bad_lines="skip", engine="python")
        except Exception:
            pass
    return pd.DataFrame()


def load_and_clean() -> pd.DataFrame:
    df = load_enriched()
    if df.empty:
        return df
    return clean(df.copy())


__all__ = [
    "PERSISTENT_RAW",
    "PERSISTENT_ENRICHED",
    "active_donors",
    "basic_stats",
    "clean",
    "frequent_donors",
    "inactive_donors",
    "load_and_clean",
    "load_enriched",
    "stats_by_month",
    "stats_by_state",
    "stats_by_year",
    "stats_no_location",
    "top_donors",
]
