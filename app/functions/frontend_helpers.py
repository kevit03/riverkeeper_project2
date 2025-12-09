from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
import traceback

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
from functions.heatmap import geocode_if_needed


BASE_DIR = Path(__file__).resolve().parents[1]
PERSISTENT_RAW = BASE_DIR / "data" / "donor_data.csv"
PERSISTENT_ENRICHED = BASE_DIR / "data" / "donor_data_enriched.csv"
LOCATION_CACHE = BASE_DIR / "data" / "RiverKeeper_Donors_Unique_Locations.csv"
GEO_CACHE_JSON = BASE_DIR / "data" / "geocode_cache.json"
BASE_COLUMNS = [
    "Account ID",
    "City",
    "State",
    "BFPO No",
    "Postcode",
    "Country",
    "Total Gifts (All Time)",
    "Last Gift Date",
    "Number of Gifts Past 18 Months",
]
ENRICHED_COLUMNS = [
    "Account ID",
    "City",
    "County",
    "State",
    "Country",
    "Total Gifts (All Time)",
    "Last Gift Date",
    "Number of Gifts Past 18 Months",
    "Location",
    "OriginalLocation",
    "ResolvedCity",
    "Latitude",
    "Longitude",
    "LocalArea",
]


def _load_csv(path: Path) -> pd.DataFrame:
    if path.exists():
        try:
            return pd.read_csv(path, on_bad_lines="skip", engine="python")
        except Exception:
            try:
                return pd.read_csv(path, on_bad_lines="skip")
            except Exception:
                return pd.DataFrame()
    return pd.DataFrame()


def load_raw() -> pd.DataFrame:
    return _load_csv(PERSISTENT_RAW)


def load_enriched() -> pd.DataFrame:
    return _load_csv(PERSISTENT_ENRICHED)


def _save_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def _group_top(names, values, top_n=9, other_label="Other"):
    pairs = list(zip(names, values))
    pairs = sorted(pairs, key=lambda x: x[1], reverse=True)
    total = sum(v for _, v in pairs)
    keep = []
    other = []
    for n, v in pairs[:top_n]:
        if total > 0 and v / total < 0.01:
            other.append((n, v))
        else:
            keep.append((n, v))
    other.extend(pairs[top_n:])
    if other:
        keep.append((other_label, sum(v for _, v in other)))
    grouped_names = [str(n) for n, _ in keep]
    grouped_values = [v for _, v in keep]
    return grouped_names, grouped_values



def merge_and_enrich(new_df: pd.DataFrame) -> pd.DataFrame:
    current_full = st.session_state.get("raw_df", load_raw())
    current = current_full[BASE_COLUMNS] if not current_full.empty else current_full

    merged, _ = merge_csv(current, new_df[BASE_COLUMNS], save=False)
    _save_csv(merged, PERSISTENT_RAW)  # interim save without enrichment

    progress_bar = st.progress(0, text="Geocoding donor locations (with cache)...")
    status = st.empty()

    def update_progress(done: int, total: int) -> None:
        pct = int(done / total * 100) if total else 100
        progress_bar.progress(pct, text=f"Geocoding donor locations (with cache)... {pct}%")

    def update_status(msg: str) -> None:
        status.write(msg)

    try:
        enriched = enrich_locations(
            str(PERSISTENT_RAW),
            progress=update_progress,
            status=update_status,
            stored_file=str(LOCATION_CACHE),
        )
    except Exception as e:
        raise RuntimeError(f"merge_and_enrich -> enrich_locations failed: {e}") from e
    progress_bar.progress(100, text="Geocoding complete.")
    status.empty()

    if enriched is None:
        return clean(merged.copy())

    enriched_clean = clean(enriched.copy())
    # limit borough to NYC boroughs only
    nyc_boroughs = {"Manhattan", "Queens", "Brooklyn", "The Bronx", "Staten Island"}
    if "Borough" in enriched_clean.columns:
        enriched_clean["Borough"] = enriched_clean["Borough"].apply(
            lambda b: b if isinstance(b, str) and b.strip() in nyc_boroughs else ""
        )

    # Resolve city names via Photon and enrich with lat/lon and original location strings
    with st.spinner("Resolving cities and caching coordinates..."):
        try:
            enriched_clean = geocode_if_needed(
                enriched_clean,
                cache_path=str(GEO_CACHE_JSON),
                geocode_limit=5000,
            )
        except Exception as e:
            raise RuntimeError(f"merge_and_enrich -> geocode_if_needed failed: {e}") from e

    # Normalize NYC entries: if we have a borough, set City to "New York City"; handle "City of New York"
    def normalize_nyc(row):
        borough = str(row.get("Borough") or "").strip() if "Borough" in row else ""
        city = str(row.get("City") or "").strip()
        if borough:
            row["City"] = "New York City"
            row["State"] = "New York"
            row["County"] = borough
        elif city.lower() == "city of new york":
            row["City"] = "New York City"
            row["State"] = "New York"
        return row
    enriched_clean = enriched_clean.apply(normalize_nyc, axis=1)

    # drop Borough column entirely
    if "Borough" in enriched_clean.columns:
        enriched_clean = enriched_clean.drop(columns=["Borough"])

    # Add a more specific local area field for NYC rows (use original location string)
    nyc_cities = {"NEW YORK", "NEW YORK CITY", "NYC", "CITY OF NEW YORK"}
    enriched_clean["LocalArea"] = enriched_clean.apply(
        lambda r: (
            r["OriginalLocation"]
            if (
                str(r.get("State") or "").upper() == "NY"
                and (
                    str(r.get("County") or "").strip() in nyc_boroughs
                    or str(r.get("City") or "").strip().upper() in nyc_cities
                )
                and str(r.get("OriginalLocation") or "").strip()
            )
            else ""
        ),
        axis=1,
    )
    # Ensure Location exists for downstream selection
    if "Location" not in enriched_clean.columns:
        enriched_clean["Location"] = enriched_clean.apply(
            lambda r: ", ".join(
                [part for part in [str(r.get("City") or "").strip(), str(r.get("State") or "").strip()] if part]
            ),
            axis=1,
        )
    # keep only columns relevant to stats / geo
    for col in ENRICHED_COLUMNS:
        if col not in enriched_clean.columns:
            enriched_clean[col] = None
    enriched_clean = enriched_clean[ENRICHED_COLUMNS]

    _save_csv(enriched_clean, PERSISTENT_ENRICHED)
    return enriched_clean


def render_stats(df: pd.DataFrame) -> None:
    st.subheader("Basic Statistics")
    st.table(basic_stats(df))

    st.subheader("Active vs Inactive Donors")
    col1, col2 = st.columns(2)
    with col1:
        st.caption("Active donors (donated in past 18 months)")
        st.table(active_donors(df))
    with col2:
        st.caption("Inactive donors")
        st.table(inactive_donors(df))

    st.subheader("Top Donors")
    col1, col2 = st.columns(2)
    top_amt = top_donors(df, 20)
    top_freq = frequent_donors(df, 20)
    with col1:
        st.caption("Top 20 by total amount")
        st.dataframe(top_amt)
    with col2:
        st.caption("Top 20 by frequency (past 18 months)")
        st.dataframe(top_freq)

    # pies for donor activity across all donors (from Izzy's analytics)
    if not df.empty:
        df_status = df.copy()
        df_status["Status"] = df_status["Number of Gifts Past 18 Months"].apply(lambda x: "Active" if pd.to_numeric(x, errors="coerce") > 0 else "Inactive")
        activity_counts = df_status["Status"].value_counts()
        fig = px.pie(
            names=activity_counts.index,
            values=activity_counts.values,
            title="Status of All Donors",
            color_discrete_sequence=px.colors.qualitative.Safe,
        )
        fig.update_traces(hovertemplate='%{label}: %{value} (%{percent})', textinfo="label+percent")
        st.plotly_chart(fig, width="stretch")

    st.subheader("Geography Breakdown")
    states_df = stats_by_state(df)
    st.dataframe(states_df)

    # state pies: donors and total gifts
    if not states_df.empty and "Donors" in states_df.columns:
        col_a, col_b = st.columns(2)
        g_names, g_vals = _group_top(states_df.index, states_df["Donors"], top_n=9)
        fig = px.pie(
            names=g_names,
            values=g_vals,
            title="Donors by State",
            color_discrete_sequence=px.colors.qualitative.Safe,
        )
        fig.update_traces(hovertemplate='%{label}: %{value} (%{percent})', textinfo="label+percent")
        col_a.plotly_chart(fig, width="stretch")

        # convert totals back to numeric for amount pie
        amt_series = states_df["Total Gifts (All Time)"].apply(lambda x: float(str(x).replace("$", "").replace(",", "")))
        g_names_amt, g_vals_amt = _group_top(states_df.index, amt_series, top_n=9)
        fig_amt = px.pie(
            names=g_names_amt,
            values=g_vals_amt,
            title="Donation Amount by State",
            color_discrete_sequence=px.colors.qualitative.Safe,
        )
        fig_amt.update_traces(hovertemplate='%{label}: $%{value:,.0f} (%{percent})', textinfo="label+percent")
        col_b.plotly_chart(fig_amt, width="stretch")

    st.caption("Donors without usable location")
    st.dataframe(stats_no_location(df))

    # city breakdown per state with "Other" grouping (Izzy's approach)
    states_list = [s for s in df["State"].dropna().unique().tolist() if str(s) != ""]
    states_list.sort()
    if states_list:
        default_state = "New York" if "New York" in states_list else states_list[0]
        selected_state = st.selectbox("Select a state to view city breakdown:", options=states_list, index=states_list.index(default_state) if default_state in states_list else 0)
        state_data = df[df["State"] == selected_state].copy()
        # drop numeric or blank city labels that can sneak in from malformed rows
        state_data["City"] = state_data["City"].astype(str).str.strip()
        state_data.loc[state_data["City"].isin(["", "nan", "NaN", "None", "none"]), "City"] = None
        state_data.loc[state_data["City"].str.contains(r"\d", na=False), "City"] = None
        state_data = state_data.dropna(subset=["City"])
        city_counts = state_data["City"].value_counts().reset_index()
        city_counts.columns = ["City", "Donor Count"]
        g_names, g_vals = _group_top(city_counts["City"], city_counts["Donor Count"], top_n=9)
        col_a, col_b = st.columns(2)
        fig = px.pie(
            names=g_names,
            values=g_vals,
            title=f"Donors by City in {selected_state}",
            color_discrete_sequence=px.colors.qualitative.Safe,
        )
        fig.update_traces(hovertemplate='%{label}: %{value} (%{percent})', textinfo="label+percent")
        col_a.plotly_chart(fig, width="stretch")

        # amount pie for cities
        city_amt = state_data.groupby("City")["Total Gifts (All Time)"].apply(
            lambda s: pd.to_numeric(s.replace({"\$": "", ",": ""}, regex=True), errors="coerce").sum()
        )
        g_names_amt, g_vals_amt = _group_top(city_amt.index, city_amt.values, top_n=9)
        fig_amt = px.pie(
            names=g_names_amt,
            values=g_vals_amt,
            title=f"Donation Amount by City in {selected_state}",
            color_discrete_sequence=px.colors.qualitative.Safe,
        )
        fig_amt.update_traces(hovertemplate='%{label}: $%{value:,.0f} (%{percent})', textinfo="label+percent")
        col_b.plotly_chart(fig_amt, width="stretch")

        if selected_state == "New York":
            boroughs = ["Manhattan", "Queens", "Brooklyn", "The Bronx", "Staten Island"]
            nyc = state_data[state_data["County"].isin(boroughs)]
            if not nyc.empty:
                borough_counts = nyc["County"].value_counts().reset_index()
                borough_counts.columns = ["Borough", "Donor Count"]
                col_a, col_b = st.columns(2)
                g_names, g_vals = _group_top(borough_counts["Borough"], borough_counts["Donor Count"], top_n=9)
                fig = px.pie(
                    names=g_names,
                    values=g_vals,
                    title="Donors by Borough in New York City",
                    color_discrete_sequence=px.colors.qualitative.Safe,
                )
                fig.update_traces(hovertemplate='%{label}: %{value} (%{percent})', textinfo="label+percent")
                col_a.plotly_chart(fig, width="stretch")

                borough_amt = nyc.groupby("County")["Total Gifts (All Time)"].apply(
                    lambda s: pd.to_numeric(s.replace({"\$": "", ",": ""}, regex=True), errors="coerce").sum()
                )
                g_names_amt, g_vals_amt = _group_top(borough_amt.index, borough_amt.values, top_n=9)
                fig_amt = px.pie(
                    names=g_names_amt,
                    values=g_vals_amt,
                    title="Donation Amount by Borough in New York City",
                    color_discrete_sequence=px.colors.qualitative.Safe,
                )
                fig_amt.update_traces(hovertemplate='%{label}: $%{value:,.0f} (%{percent})', textinfo="label+percent")
                col_b.plotly_chart(fig_amt, width="stretch")

    st.subheader("Gifts Over Time")
    col1, col2 = st.columns(2)
    with col1:
        st.bar_chart(stats_by_year(df), x_label="Year", y_label="Donors", color="#007633")
    with col2:
        months = stats_by_month(df)
        # ensure correct order Jan..Dec
        ordered_months = list(months["Month"])
        # enforce categorical ordering to prevent alphabetical sort in Streamlit
        months["Month"] = pd.Categorical(
            months["Month"],
            categories=["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
            ordered=True,
        )
        months = months.sort_values("Month")
        st.bar_chart(months, x="Month", y="Donors", x_label="Month", y_label="Donors", color="#007633", width="stretch")
