from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "app" / "data" / "donor_data_enriched.csv"
DEFAULT_OUTPUT = ROOT / "client_portal" / "data" / "kevin_heatmap_data.json"


def is_valid_coordinate(lat: object, lon: object) -> bool:
    try:
        lat_value = float(lat)
        lon_value = float(lon)
    except (TypeError, ValueError):
        return False

    if pd.isna(lat_value) or pd.isna(lon_value):
        return False

    if abs(lat_value) > 90 or abs(lon_value) > 180:
        return False

    if lat_value == 0 and lon_value == 0:
        return False

    return True


def first_non_empty(series: pd.Series) -> str:
    for value in series:
        if pd.notna(value):
            text = str(value).strip()
            if text:
                return text
    return ""


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    work_df = df.copy()

    for column in ["Account ID", "City", "County", "State", "Country", "LocalArea"]:
        if column not in work_df.columns:
            work_df[column] = ""
        work_df[column] = work_df[column].fillna("").astype(str).str.strip()

    work_df["State"] = work_df["State"].replace("", "Unknown")
    work_df["Country"] = work_df["Country"].replace("", "Unknown")

    work_df["Total Gifts (All Time)"] = pd.to_numeric(
        work_df.get("Total Gifts (All Time)"),
        errors="coerce",
    ).fillna(0.0)
    work_df["Number of Gifts Past 18 Months"] = pd.to_numeric(
        work_df.get("Number of Gifts Past 18 Months"),
        errors="coerce",
    ).fillna(0.0)
    work_df["Last Gift Date"] = pd.to_datetime(
        work_df.get("Last Gift Date"),
        errors="coerce",
    )

    valid_mask = work_df.apply(
        lambda row: is_valid_coordinate(row.get("Latitude"), row.get("Longitude")),
        axis=1,
    )
    work_df = work_df.loc[valid_mask].copy()
    work_df["Latitude"] = work_df["Latitude"].astype(float)
    work_df["Longitude"] = work_df["Longitude"].astype(float)
    work_df["lat_round"] = work_df["Latitude"].round(3)
    work_df["lon_round"] = work_df["Longitude"].round(3)
    work_df["is_active"] = work_df["Number of Gifts Past 18 Months"] > 0
    work_df["Active Account ID"] = work_df["Account ID"].where(work_df["is_active"])
    work_df["location_key"] = (
        work_df["lat_round"].astype(str)
        + ":"
        + work_df["lon_round"].astype(str)
        + ":"
        + work_df["State"]
        + ":"
        + work_df["City"]
    )
    return work_df


def compose_location_label(row: pd.Series) -> str:
    city = str(row.get("City") or "").strip()
    county = str(row.get("County") or "").strip()
    state = str(row.get("State") or "").strip()
    country = str(row.get("Country") or "").strip()

    parts = [part for part in [city or county] if part]
    if state and state != "Unknown":
        parts.append(state)
    if country and country not in {"United States", "Unknown"}:
        parts.append(country)

    return ", ".join(parts) if parts else "Unknown location"


def compose_tier(total_donations: float) -> str:
    if total_donations >= 100000:
        return "Anchor"
    if total_donations >= 25000:
        return "Core"
    if total_donations >= 5000:
        return "Growth"
    return "Local"


def build_location_payload(work_df: pd.DataFrame) -> pd.DataFrame:
    group_columns = ["lat_round", "lon_round", "City", "County", "State", "Country"]
    locations_df = (
        work_df.groupby(group_columns, dropna=False)
        .agg(
            donors=("Account ID", "nunique"),
            activeDonors=("Active Account ID", "nunique"),
            totalDonations=("Total Gifts (All Time)", "sum"),
            averageDonation=("Total Gifts (All Time)", "mean"),
            largestGift=("Total Gifts (All Time)", "max"),
            recentGiftDate=("Last Gift Date", "max"),
            sampleLocalArea=("LocalArea", first_non_empty),
        )
        .reset_index()
    )
    locations_df["inactiveDonors"] = locations_df["donors"] - locations_df["activeDonors"]
    locations_df["displayLabel"] = locations_df.apply(compose_location_label, axis=1)
    locations_df["tier"] = locations_df["totalDonations"].apply(compose_tier)
    locations_df["recentGiftDate"] = (
        pd.to_datetime(locations_df["recentGiftDate"], errors="coerce")
        .dt.strftime("%Y-%m-%d")
        .fillna("")
    )
    locations_df = locations_df.sort_values(
        by=["donors", "totalDonations", "displayLabel"],
        ascending=[False, False, True],
    ).reset_index(drop=True)
    return locations_df


def build_state_payload(work_df: pd.DataFrame, locations_df: pd.DataFrame) -> pd.DataFrame:
    states_df = (
        work_df.groupby("State", dropna=False)
        .agg(
            donors=("Account ID", "nunique"),
            activeDonors=("Active Account ID", "nunique"),
            totalDonations=("Total Gifts (All Time)", "sum"),
        )
        .reset_index()
    )
    location_counts = (
        locations_df.groupby("State", dropna=False)
        .size()
        .rename("locations")
        .reset_index()
    )
    states_df = states_df.merge(location_counts, on="State", how="left").fillna({"locations": 0})
    states_df["inactiveDonors"] = states_df["donors"] - states_df["activeDonors"]
    states_df["shareOfDonors"] = states_df["donors"] / max(states_df["donors"].sum(), 1)
    states_df = states_df.sort_values(
        by=["donors", "totalDonations", "State"],
        ascending=[False, False, True],
    ).reset_index(drop=True)
    return states_df


def to_native_number(value: object) -> object:
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def dataframe_to_records(frame: pd.DataFrame) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for row in frame.to_dict(orient="records"):
        native_row = {key: to_native_number(value) for key, value in row.items()}
        records.append(native_row)
    return records


def build_payload(input_path: Path) -> dict[str, object]:
    source_df = pd.read_csv(input_path)
    work_df = clean_dataset(source_df)
    locations_df = build_location_payload(work_df)
    states_df = build_state_payload(work_df, locations_df)

    active_mask = work_df["is_active"]
    largest_location = locations_df.iloc[0] if not locations_df.empty else None
    top_state = states_df.iloc[0] if not states_df.empty else None

    try:
        source_file = str(input_path.relative_to(ROOT))
    except ValueError:
        source_file = str(input_path)

    known_states = work_df.loc[work_df["State"] != "Unknown", "State"]
    payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "sourceFile": source_file,
        "summary": {
            "totalDonors": int(work_df["Account ID"].nunique()),
            "activeDonors": int(work_df.loc[active_mask, "Account ID"].nunique()),
            "inactiveDonors": int(work_df["Account ID"].nunique() - work_df.loc[active_mask, "Account ID"].nunique()),
            "totalDonations": round(float(work_df["Total Gifts (All Time)"].sum()), 2),
            "mappedLocations": int(len(locations_df)),
            "statesCovered": int(known_states.nunique()),
            "largestLocation": {
                "label": str(largest_location["displayLabel"]) if largest_location is not None else "",
                "donors": int(largest_location["donors"]) if largest_location is not None else 0,
                "totalDonations": round(float(largest_location["totalDonations"]), 2) if largest_location is not None else 0.0,
            },
            "topState": {
                "name": str(top_state["State"]) if top_state is not None else "",
                "donors": int(top_state["donors"]) if top_state is not None else 0,
                "totalDonations": round(float(top_state["totalDonations"]), 2) if top_state is not None else 0.0,
            },
        },
        "stateSummary": dataframe_to_records(states_df),
        "locations": dataframe_to_records(locations_df),
    }
    return payload


def export_payload(input_path: Path, output_path: Path) -> Path:
    payload = build_payload(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export the cleaned donor dataset into a client-portal heatmap payload.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Path to the cleaned donor CSV. Default: {DEFAULT_INPUT}",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Path to the generated JSON payload. Default: {DEFAULT_OUTPUT}",
    )
    args = parser.parse_args()

    output_path = export_payload(args.input.resolve(), args.output.resolve())
    print(f"Heatmap payload written to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
