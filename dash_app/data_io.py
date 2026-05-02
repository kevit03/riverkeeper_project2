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
GEO_COLUMNS = ["County", "Location", "OriginalLocation", "ResolvedCity", "Latitude", "Longitude", "LocalArea"]
STATE_NAMES = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "IA": "Iowa",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "MA": "Massachusetts",
    "MD": "Maryland",
    "ME": "Maine",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MO": "Missouri",
    "MS": "Mississippi",
    "MT": "Montana",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "NE": "Nebraska",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NV": "Nevada",
    "NY": "New York",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VA": "Virginia",
    "VT": "Vermont",
    "WA": "Washington",
    "WI": "Wisconsin",
    "WV": "West Virginia",
    "WY": "Wyoming",
}


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


def normalize_state(value) -> str:
    state = str(value or "").strip()
    if not state or state.lower() == "nan":
        return ""
    return STATE_NAMES.get(state.upper(), state)


def location_key(city, state) -> str:
    city_text = str(city or "").strip().lower()
    state_text = normalize_state(state).lower()
    return f"{city_text}|{state_text}" if city_text and state_text else ""


def enrich_uploaded_locations(uploaded: pd.DataFrame) -> pd.DataFrame:
    """Fill geo fields for uploads using the bundled enriched donor dataset.

    This keeps uploads fast and offline-friendly. Rows with locations already
    present are left alone; rows without coordinates borrow the known location
    metadata for the same city/state when available.
    """
    enriched = uploaded.copy()
    for col in GEO_COLUMNS:
        if col not in enriched.columns:
            enriched[col] = None

    reference = load_enriched()
    if reference.empty or not {"City", "State", "Latitude", "Longitude"}.issubset(reference.columns):
        return enriched

    ref = reference.dropna(subset=["City", "State", "Latitude", "Longitude"]).copy()
    ref["_location_key"] = ref.apply(lambda row: location_key(row.get("OriginalLocation") or row.get("City"), row.get("State")), axis=1)
    ref = ref.drop_duplicates("_location_key", keep="first").set_index("_location_key")

    for idx, row in enriched.iterrows():
        has_coords = pd.notna(row.get("Latitude")) and pd.notna(row.get("Longitude"))
        if has_coords:
            continue

        key = location_key(row.get("City"), row.get("State"))
        if not key or key not in ref.index:
            continue

        match = ref.loc[key]
        for col in GEO_COLUMNS:
            if col in match.index:
                enriched.at[idx, col] = match[col]

        enriched.at[idx, "State"] = normalize_state(enriched.at[idx, "State"])
        if not enriched.at[idx, "Location"]:
            enriched.at[idx, "Location"] = ", ".join(
                part for part in [str(enriched.at[idx, "City"] or "").strip(), normalize_state(enriched.at[idx, "State"])] if part
            )

    return enriched


__all__ = [
    "PERSISTENT_RAW",
    "PERSISTENT_ENRICHED",
    "active_donors",
    "basic_stats",
    "clean",
    "frequent_donors",
    "inactive_donors",
    "enrich_uploaded_locations",
    "load_and_clean",
    "load_enriched",
    "stats_by_month",
    "stats_by_state",
    "stats_by_year",
    "stats_no_location",
    "top_donors",
]
