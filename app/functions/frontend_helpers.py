from pathlib import Path

import pandas as pd
import streamlit as st

from functions.merge_csv import merge_csv
from functions.data_analysis import (
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
from functions.location import run as enrich_locations


BASE_DIR = Path(__file__).resolve().parents[1]
PERSISTENT_CSV = BASE_DIR / "data" / "donor_data.csv"


def load_persistent() -> pd.DataFrame:
    if PERSISTENT_CSV.exists():
        try:
            return pd.read_csv(PERSISTENT_CSV)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def save_persistent(df: pd.DataFrame) -> None:
    PERSISTENT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(PERSISTENT_CSV, index=False)


def merge_and_enrich(new_df: pd.DataFrame) -> pd.DataFrame:
    current = st.session_state.get("raw_df", load_persistent())
    merged, _ = merge_csv(current, new_df, save=False)
    save_persistent(merged)

    enriched = enrich_locations(str(PERSISTENT_CSV))
    if enriched is None:
        return clean(merged.copy())

    save_persistent(enriched)
    return clean(enriched.copy())


def render_stats(df: pd.DataFrame) -> None:
    st.subheader("Basic Statistics")
    st.dataframe(basic_stats(df))

    st.subheader("Active vs Inactive Donors")
    col1, col2 = st.columns(2)
    with col1:
        st.caption("Active donors (donated in past 18 months)")
        st.dataframe(active_donors(df))
    with col2:
        st.caption("Inactive donors")
        st.dataframe(inactive_donors(df))

    st.subheader("Top Donors")
    col1, col2 = st.columns(2)
    with col1:
        st.caption("Top 20 by total amount")
        st.dataframe(top_donors(df, 20))
    with col2:
        st.caption("Top 20 by frequency (past 18 months)")
        st.dataframe(frequent_donors(df, 20))

    st.subheader("Geography Breakdown")
    st.dataframe(stats_by_state(df))
    st.caption("Donors without usable location")
    st.dataframe(stats_no_location(df))

    st.subheader("Gifts Over Time")
    col1, col2 = st.columns(2)
    with col1:
        st.bar_chart(stats_by_year(df), x_label="Year", y_label="Donors", color="#007633")
    with col2:
        st.bar_chart(stats_by_month(df), x_label="Month", y_label="Donors", color="#007633", use_container_width=True)
