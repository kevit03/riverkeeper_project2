import json
import time
from collections import defaultdict
from typing import Callable, Optional, Tuple
import hashlib
from pathlib import Path

import pandas as pd
import folium
from folium.plugins import MarkerCluster, HeatMap
from geopy.geocoders import Nominatim
import streamlit as st
from streamlit import components


# ------------------ Helpers ------------------ #

def is_kansas(lat, lon) -> bool:
    try:
        lat = float(lat)
        lon = float(lon)
    except Exception:
        return False

    return (36.99 <= lat <= 40.01) and (-102.06 <= lon <= -94.58)


def is_valid_coordinate(lat, lon) -> bool:
    """Basic sanity checks for coordinates, including NaNs."""
    try:
        lat = float(lat)
        lon = float(lon)
    except Exception:
        return False

    # reject NaNs
    if pd.isna(lat) or pd.isna(lon):
        return False

    # reject extreme impossible values
    if abs(lat) > 90 or abs(lon) > 180:
        return False

    # reject (0,0)
    if lat == 0 and lon == 0:
        return False

    return True


def geocode_records(
    records,
    limit: int = 100,
    delay: float = 0.2,
    cache_path: Optional[str] = None,
    progress: Optional[Callable[[int], None]] = None,
    status: Optional[Callable[[str], None]] = None,
) -> None:
    """
    Mutates `records` (list of dicts) in place by filling Latitude / Longitude.
    Uses Nominatim + a JSON cache.
    """
    cache_file = cache_path or str(Path(__file__).resolve().parents[1] / "data" / "geocode_cache.json")
    try:
        with open(cache_file, "r") as f:
            cache = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        cache = {}

    geolocator = Nominatim(user_agent="heatmap_script", timeout=10)
    total = min(limit, len(records))

    for idx, entry in enumerate(records[:limit], start=1):
        query = f"{entry['City']}, {entry['State']}, {entry['Country']}"

        if query in cache:
            cached = cache[query]
            if isinstance(cached, (list, tuple)) and len(cached) >= 2:
                entry["Latitude"], entry["Longitude"] = cached[0], cached[1]
                if len(cached) >= 3:
                    entry["ResolvedCity"] = cached[2]
            continue

        resolved_city = None
        try:
            loc = geolocator.geocode(query, addressdetails=True)
            if loc:
                lat, lon = loc.latitude, loc.longitude
                addr = loc.raw.get("address", {})
                resolved_city = (
                    addr.get("city")
                    or addr.get("town")
                    or addr.get("village")
                    or addr.get("hamlet")
                    or addr.get("municipality")
                )
            else:
                lat, lon = None, None
        except Exception:
            lat, lon = None, None

        cache[query] = (lat, lon, resolved_city)
        entry["Latitude"], entry["Longitude"] = lat, lon
        entry["ResolvedCity"] = resolved_city
        time.sleep(delay)

        if progress:
            progress(int(idx / total * 100))
        if status and idx % 10 == 0:
            status(f"Geocoded {idx}/{total} locations...")

    with open(cache_file, "w") as f:
        json.dump(cache, f, indent=2)


# ------------------ Map building ------------------ #

def build_map_from_df(df: pd.DataFrame) -> Tuple[folium.Map, int, int]:
    """
    Given a DataFrame with Latitude / Longitude, build the Folium map and
    return (map, invalid_count, kansas_count).
    """
    counts = defaultdict(lambda: {"count": 0, "labels": set(), "total": 0.0})
    invalid_count = 0
    kansas_count = 0

    for _, row in df.iterrows():
        lat = row.get("Latitude")
        lon = row.get("Longitude")

        if not is_valid_coordinate(lat, lon):
            invalid_count += 1
            continue

        if is_kansas(lat, lon):
            kansas_count += 1
            continue

        # round coordinates to reduce tiny diffs (aggregate to ~100m)
        rounded_lat = round(float(lat), 3)
        rounded_lon = round(float(lon), 3)
        key = (rounded_lat, rounded_lon)
        counts[key]["count"] += 1
        # sum donation amount if available
        try:
            amt = float(row.get("Total Gifts (All Time)", 0) or 0)
        except Exception:
            amt = 0.0
        counts[key]["total"] += amt
        # capture a human-friendly label (prefer original location if present)
        orig = str(row.get("OriginalLocation") or "").strip()
        city = str(row.get("City") or "").strip()
        borough = str(row.get("Borough") or "").strip()
        county = str(row.get("County") or "").strip()
        state = str(row.get("State") or "").strip()
        country = str(row.get("Country") or "").strip()

        parts = [p for p in [city, borough, county, state, country] if p]
        label = orig or ", ".join(parts)
        if not label:
            label = "Unknown location"
        counts[key]["labels"].add(label)

    # Base map
    m = folium.Map(
        location=[40.7128, -74.0060],
        zoom_start=5,
        max_bounds=True,
        world_copy_jump=False,
    )

    # Cluster markers but reduce movement (no zoom-to-bounds/spiderfy)
    cluster_group = MarkerCluster(
        options={
            "zoomToBoundsOnClick": False,
            "showCoverageOnHover": False,
            "spiderfyOnMaxZoom": False,
        }
    ).add_to(m)

    # Add real markers
    for (lat, lon), info in counts.items():
        num = info["count"]
        total_amt = info["total"]
        label_list = sorted(info["labels"])
        label_text = label_list[0] if label_list else "Unknown location"
        if len(label_list) > 1:
            label_text += f" (+{len(label_list)-1} nearby)"
        popup_html = (
            f"<div style='font-size:14px; padding:6px 8px;'>"
            f"<b>{num} donor(s)</b><br>"
            f"Total donated: ${total_amt:,.2f}<br>"
            f"{label_text}"
            f"</div>"
        )
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(
                color="blue",
                class_name=f"donor-{num}",
                icon_size=(28, 28),
                icon_anchor=(14, 28),  # center the icon over the point
                popup_anchor=(0, -14),
                shadow_url=None,
                shadow_size=None,
            ),
        ).add_to(cluster_group)

    # Heatmap
    heat_points = [[lat, lon, info["count"]] for (lat, lon), info in counts.items()]
    if heat_points:
        HeatMap(heat_points, radius=20, blur=15).add_to(m)

    return m, invalid_count, kansas_count


# ------------------ Streamlit helpers ------------------ #

def geocode_if_needed(
    df: pd.DataFrame,
    cache_path: Optional[str],
    geocode_limit: int,
) -> pd.DataFrame:
    """Geocode unique cities; rows without a city are excluded."""
    # keep only rows with a city
    df_city = df.copy()
    df_city["City"] = df_city["City"].fillna("").astype(str).str.strip()
    df_city["State"] = df_city.get("State", "").fillna("").astype(str).str.strip()
    df_city["Country"] = df_city.get("Country", "").fillna("").astype(str).str.strip()
    df_city = df_city[df_city["City"] != ""]
    if df_city.empty:
        return df_city

    # build unique city-state-country keys
    unique_keys = {}
    for _, row in df_city.iterrows():
        key = (row["City"].title(), row["State"].upper(), row["Country"].title())
        if key not in unique_keys:
            unique_keys[key] = {
                "City": row["City"],
                "State": row["State"],
                "Country": row["Country"],
                "Latitude": None,
                "Longitude": None,
                "ResolvedCity": None,
            }

    records = list(unique_keys.values())

    progress_container = st.empty()
    progress_bar = progress_container.progress(0, text="Geocoding donor cities (with cache)...")
    status = st.empty()

    def update_progress(pct: int) -> None:
        progress_bar.progress(pct, text=f"Geocoding donor cities (with cache)... {pct}%")

    def update_status(msg: str) -> None:
        status.write(msg)

    geocode_records(
        records,
        limit=min(geocode_limit, len(records)),
        delay=0.2,
        cache_path=cache_path,
        progress=update_progress,
        status=update_status,
    )

    progress_bar.progress(100, text="Geocoding complete.")
    status.empty()
    progress_container.empty()

    # map back to dataframe
    coord_map = {
        (r["City"].title(), r["State"].upper(), r["Country"].title()): (
            r.get("Latitude"),
            r.get("Longitude"),
            r.get("ResolvedCity"),
        )
        for r in records
    }

    def lookup(row):
        return coord_map.get(
            (row["City"].title(), row["State"].upper(), row["Country"].title()),
            (None, None, None),
        )

    resolved = df_city.apply(lookup, axis=1, result_type="expand")
    df_city["Latitude"] = resolved[0]
    df_city["Longitude"] = resolved[1]
    df_city["ResolvedCity"] = resolved[2]

    # If Photon resolved a city, use it; otherwise leave City empty and store original in Location
    df_city["OriginalLocation"] = df_city["City"]
    df_city["City"] = df_city.apply(
        lambda r: r["ResolvedCity"] if pd.notna(r["ResolvedCity"]) and str(r["ResolvedCity"]).strip() else "",
        axis=1,
    )

    # drop rows still missing coords
    df_city = df_city.dropna(subset=["Latitude", "Longitude"])
    return df_city


def render_map(work_df: pd.DataFrame) -> None:
    """Build and render the map; no progress UI here."""
    m, invalid_count, kansas_count = build_map_from_df(work_df)
    # Render as static HTML to avoid interaction events/reruns
    components.v1.html(m._repr_html_(), height=650, scrolling=False)
    st.caption(
        f"Excluded {invalid_count} invalid locations and "
        f"{kansas_count} Kansas fallback locations."
    )


# ------------------ Streamlit entrypoint ------------------ #

def render_heatmap(
    df: pd.DataFrame,
    cache_path: Optional[str] = None,
    geocode_limit: int = 10_000,
) -> None:
    """
    Streamlit-friendly function:
    - Requires either Latitude/Longitude OR City/State/Country in df.
    - Geocodes missing Lat/Lon using cache.
    - Renders the Folium map inside Streamlit.
    """
    st.subheader("Donor Heatmap")

    if df.empty:
        st.info("No data available for heatmap.")
        return

    has_address = all(col in df.columns for col in ["City", "State", "Country"])
    has_latlon = "Latitude" in df.columns and "Longitude" in df.columns
    if not has_latlon and not has_address:
        st.error(
            "Heatmap requires either Latitude/Longitude columns "
            "or City/State/Country columns."
        )
        return
    work_df = geocode_if_needed(df, cache_path, geocode_limit)
    render_map(work_df)


# Optional: keep a CLI entrypoint if you still want to generate the HTML file directly.
if __name__ == "__main__":
    import csv

    filename = Path(__file__).resolve().parents[1] / "data" / "Riverkeeper_Donors.csv"
    records = []

    with open(filename, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entry = {
                "City": row.get("City", ""),
                "State": row.get("State", ""),
                "Country": row.get("Country", ""),
                "Latitude": None,
                "Longitude": None,
            }
            records.append(entry)

    geocode_records(records, limit=len(records), delay=0.2)
    df_cli = pd.DataFrame(records)
    m_cli, _, _ = build_map_from_df(df_cli)
    out_path = Path(__file__).resolve().parents[1] / "data" / "donor_map.html"
    m_cli.save(out_path)
    print(f"Saved map to {out_path}")
