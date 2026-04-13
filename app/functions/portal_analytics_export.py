from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.functions.heatmap_portal_export import build_payload as build_geography_payload

RAW_INPUT = ROOT / "app" / "data" / "donor_data.csv"
ENRICHED_INPUT = ROOT / "app" / "data" / "donor_data_enriched.csv"
DEFAULT_OUTPUT = ROOT / "client_portal" / "data" / "portal_analytics_data.json"


def load_raw_dataset(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path).copy()

    df["State"] = (
        df.get("State", "")
        .fillna("Unknown")
        .astype(str)
        .str.strip()
        .replace("", "Unknown")
    )
    df["Country"] = (
        df.get("Country", "")
        .fillna("Unknown")
        .astype(str)
        .str.strip()
        .replace("", "Unknown")
    )
    df["City"] = df.get("City", "").fillna("").astype(str).str.strip()
    df["Total Gifts (All Time)"] = (
        df["Total Gifts (All Time)"]
        .astype(str)
        .str.replace(r"[$,]", "", regex=True)
        .str.strip()
    )
    df["Total Gifts (All Time)"] = pd.to_numeric(
        df["Total Gifts (All Time)"], errors="coerce"
    ).fillna(0.0)
    df["Last Gift Date"] = pd.to_datetime(df["Last Gift Date"], errors="coerce")
    df["Number of Gifts Past 18 Months"] = pd.to_numeric(
        df["Number of Gifts Past 18 Months"], errors="coerce"
    ).fillna(0.0)
    return df


def format_date(value: object) -> str:
    if pd.isna(value):
        return ""
    return pd.to_datetime(value).strftime("%Y-%m-%d")


def to_native(value: object) -> object:
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def dataframe_to_records(frame: pd.DataFrame) -> list[dict[str, object]]:
    return [
        {key: to_native(value) for key, value in row.items()}
        for row in frame.to_dict(orient="records")
    ]


def build_engagement_payload(df: pd.DataFrame) -> dict[str, object]:
    work_df = df.copy()
    work_df["Segment"] = work_df["Number of Gifts Past 18 Months"].apply(
        lambda value: "Active" if value > 0 else "Inactive"
    )

    segment_summary = (
        work_df.groupby("Segment")
        .agg(
            donorCount=("Account ID", "count"),
            totalRaised=("Total Gifts (All Time)", "sum"),
            avgGift=("Total Gifts (All Time)", "mean"),
            medianGift=("Total Gifts (All Time)", "median"),
            avgGiftsPast18M=("Number of Gifts Past 18 Months", "mean"),
            latestGift=("Last Gift Date", "max"),
            earliestGift=("Last Gift Date", "min"),
        )
        .reset_index()
        .round(2)
    )
    segment_summary["latestGift"] = segment_summary["latestGift"].apply(format_date)
    segment_summary["earliestGift"] = segment_summary["earliestGift"].apply(format_date)

    active_df = work_df[work_df["Segment"] == "Active"].copy()
    top_active_states = (
        active_df.groupby("State")["Account ID"]
        .count()
        .sort_values(ascending=False)
        .reset_index(name="activeDonors")
        .head(8)
    )

    gift_frequency = (
        active_df.groupby("Number of Gifts Past 18 Months")["Account ID"]
        .count()
        .sort_index()
        .reset_index(name="donorCount")
        .rename(columns={"Number of Gifts Past 18 Months": "giftCount"})
    )

    total_donors = int(len(work_df))
    active_donors = int((work_df["Segment"] == "Active").sum())
    inactive_donors = int((work_df["Segment"] == "Inactive").sum())

    return {
        "overall": {
            "totalDonors": total_donors,
            "activeDonors": active_donors,
            "inactiveDonors": inactive_donors,
            "activeRate": round(active_donors / max(total_donors, 1), 4),
            "totalRaised": round(float(work_df["Total Gifts (All Time)"].sum()), 2),
        },
        "segmentSummary": dataframe_to_records(segment_summary),
        "topActiveStates": dataframe_to_records(top_active_states),
        "giftFrequency": dataframe_to_records(gift_frequency),
    }


def build_concentration_payload(df: pd.DataFrame) -> dict[str, object]:
    donor_totals = (
        df.groupby("Account ID", as_index=False)["Total Gifts (All Time)"]
        .sum()
        .sort_values("Total Gifts (All Time)", ascending=False)
    )
    donor_totals = donor_totals.rename(columns={"Total Gifts (All Time)": "donationAmount"})

    total_donations = float(donor_totals["donationAmount"].sum())
    top_n = max(1, math.ceil(0.05 * len(donor_totals)))
    top_5 = donor_totals.head(top_n).copy()
    top_5_sum = float(top_5["donationAmount"].sum())

    state_summary = (
        df.groupby("State")
        .agg(
            donorCount=("Account ID", "nunique"),
            totalDonations=("Total Gifts (All Time)", "sum"),
        )
        .sort_values(["donorCount", "totalDonations"], ascending=[False, False])
        .reset_index()
        .head(10)
    )

    time_df = df.dropna(subset=["Last Gift Date"]).copy()
    time_df["Month"] = time_df["Last Gift Date"].dt.to_period("M").dt.to_timestamp()
    monthly_total = (
        time_df.groupby("Month", as_index=False)["Total Gifts (All Time)"]
        .sum()
        .sort_values("Month")
        .tail(12)
    )
    monthly_total["month"] = monthly_total["Month"].dt.strftime("%Y-%m")
    monthly_total = monthly_total.rename(
        columns={"Total Gifts (All Time)": "donationAmount"}
    )[["month", "donationAmount"]]

    spike_threshold = (
        float(monthly_total["donationAmount"].mean())
        + 2 * float(monthly_total["donationAmount"].std(ddof=0))
        if not monthly_total.empty
        else 0.0
    )
    monthly_spikes = monthly_total[
        monthly_total["donationAmount"] > spike_threshold
    ].copy()

    top_state = state_summary.iloc[0] if not state_summary.empty else None

    return {
        "concentration": {
            "donorCount": int(len(donor_totals)),
            "topSliceCount": int(top_n),
            "topSliceShare": round(top_5_sum / max(total_donations, 1), 4),
            "topSliceTotal": round(top_5_sum, 2),
            "overallTotal": round(total_donations, 2),
        },
        "topDonors": dataframe_to_records(top_5.head(8)),
        "topStates": dataframe_to_records(state_summary),
        "monthlyTotal": dataframe_to_records(monthly_total),
        "monthlySpikes": dataframe_to_records(monthly_spikes),
        "headline": {
            "state": str(top_state["State"]) if top_state is not None else "",
            "donorCount": int(top_state["donorCount"]) if top_state is not None else 0,
            "totalDonations": round(float(top_state["totalDonations"]), 2)
            if top_state is not None
            else 0.0,
        },
    }


def donor_size_category(amount: float) -> str:
    if pd.isna(amount):
        return "Unknown"
    if amount >= 100000:
        return "Major Donor"
    if amount >= 10000:
        return "Mid-Level Donor"
    if amount >= 1000:
        return "General Donor"
    if amount > 0:
        return "Small Donor"
    return "No Giving History"


def donor_activity_category(gifts_18m: float, last_gift_date: object) -> str:
    if gifts_18m >= 3:
        return "Highly Active"
    if gifts_18m >= 1:
        return "Active"
    if pd.notna(last_gift_date):
        return "Lapsed"
    return "No Recorded Activity"


def build_reporting_payload(df: pd.DataFrame) -> dict[str, object]:
    work_df = df.copy()
    work_df["donorSizeCategory"] = work_df["Total Gifts (All Time)"].apply(
        donor_size_category
    )
    work_df["donorActivityCategory"] = work_df.apply(
        lambda row: donor_activity_category(
            row["Number of Gifts Past 18 Months"], row["Last Gift Date"]
        ),
        axis=1,
    )
    work_df["combinedCategory"] = (
        work_df["donorSizeCategory"] + " - " + work_df["donorActivityCategory"]
    )

    donor_size_table = (
        work_df["donorSizeCategory"]
        .value_counts(dropna=False)
        .rename_axis("category")
        .reset_index(name="count")
    )
    donor_activity_table = (
        work_df["donorActivityCategory"]
        .value_counts(dropna=False)
        .rename_axis("category")
        .reset_index(name="count")
    )
    giving_by_size = (
        work_df.groupby("donorSizeCategory", dropna=False)["Total Gifts (All Time)"]
        .sum()
        .reset_index()
        .rename(
            columns={
                "donorSizeCategory": "category",
                "Total Gifts (All Time)": "totalDonations",
            }
        )
        .sort_values("totalDonations", ascending=False)
    )
    combined_category = (
        work_df["combinedCategory"]
        .value_counts(dropna=False)
        .rename_axis("category")
        .reset_index(name="count")
        .head(8)
    )
    top_states = (
        work_df.groupby("State")["Account ID"]
        .count()
        .sort_values(ascending=False)
        .reset_index(name="donorCount")
        .head(8)
    )

    crosstab = pd.crosstab(
        work_df["donorSizeCategory"], work_df["donorActivityCategory"]
    ).reset_index()
    crosstab = crosstab.rename(columns={"donorSizeCategory": "sizeCategory"})

    return {
        "donorSizeTable": dataframe_to_records(donor_size_table),
        "donorActivityTable": dataframe_to_records(donor_activity_table),
        "givingBySize": dataframe_to_records(giving_by_size),
        "combinedCategory": dataframe_to_records(combined_category),
        "topStates": dataframe_to_records(top_states),
        "crossTab": dataframe_to_records(crosstab),
    }


def build_payload(raw_input: Path, enriched_input: Path) -> dict[str, object]:
    raw_df = load_raw_dataset(raw_input)
    geography_payload = build_geography_payload(enriched_input)
    engagement_payload = build_engagement_payload(raw_df)
    concentration_payload = build_concentration_payload(raw_df)
    reporting_payload = build_reporting_payload(raw_df)

    overview = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "totalDonors": engagement_payload["overall"]["totalDonors"],
        "activeDonors": engagement_payload["overall"]["activeDonors"],
        "activeRate": engagement_payload["overall"]["activeRate"],
        "totalRaised": engagement_payload["overall"]["totalRaised"],
        "statesCovered": geography_payload["summary"]["statesCovered"],
        "mappedLocations": geography_payload["summary"]["mappedLocations"],
        "topFiveShare": concentration_payload["concentration"]["topSliceShare"],
        "largestLocation": geography_payload["summary"]["largestLocation"],
    }

    return {
        "overview": overview,
        "geography": geography_payload,
        "engagement": engagement_payload,
        "concentration": concentration_payload,
        "reporting": reporting_payload,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate the combined Riverkeeper portal analytics payload."
    )
    parser.add_argument(
        "--raw-input",
        type=Path,
        default=RAW_INPUT,
        help=f"Path to donor_data.csv (default: {RAW_INPUT})",
    )
    parser.add_argument(
        "--enriched-input",
        type=Path,
        default=ENRICHED_INPUT,
        help=f"Path to donor_data_enriched.csv (default: {ENRICHED_INPUT})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Path to output JSON file (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()

    payload = build_payload(args.raw_input, args.enriched_input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2))
    print(f"Wrote combined portal payload to {args.output}")


if __name__ == "__main__":
    main()
