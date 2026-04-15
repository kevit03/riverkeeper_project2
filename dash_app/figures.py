"""All chart builders for the Riverkeeper Dash app.

Every function returns a Plotly Figure already styled via the shared
'riverkeeper' template. Keep logic here so the layout files stay declarative.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .theme import CHART_COLORS, COLORS


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _group_top(names: Iterable, values: Iterable, top_n: int = 9, other_label: str = "Other"):
    """Keep the top N categories, roll the remainder into an 'Other' bucket.
    Mirrors the logic from frontend_helpers._group_top."""
    pairs = sorted(zip(names, values), key=lambda x: x[1], reverse=True)
    total = sum(v for _, v in pairs)
    keep, other = [], []
    for n, v in pairs[:top_n]:
        if total > 0 and v / total < 0.01:
            other.append((n, v))
        else:
            keep.append((n, v))
    other.extend(pairs[top_n:])
    if other:
        keep.append((other_label, sum(v for _, v in other)))
    return [str(n) for n, _ in keep], [v for _, v in keep]


def _empty_fig(message: str = "No data available") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=14, color=COLORS["text_muted"]),
    )
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(l=20, r=20, t=20, b=20),
        height=280,
    )
    return fig


def _money(x) -> float:
    try:
        return float(str(x).replace("$", "").replace(",", ""))
    except Exception:
        return 0.0


# -----------------------------------------------------------------------------
# Donut: active vs inactive donors
# -----------------------------------------------------------------------------

def donor_status_donut(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty_fig()
    status = df["Number of Gifts Past 18 Months"].apply(
        lambda x: "Active" if pd.to_numeric(x, errors="coerce") > 0 else "Inactive"
    )
    counts = status.value_counts()

    fig = go.Figure(
        data=[
            go.Pie(
                labels=counts.index.tolist(),
                values=counts.values.tolist(),
                hole=0.62,
                marker=dict(
                    colors=[COLORS["accent"], COLORS["primary"]] if "Active" in counts.index.tolist()[:1]
                    else [COLORS["primary"], COLORS["accent"]],
                    line=dict(color="#FFFFFF", width=3),
                ),
                textinfo="percent",
                textposition="inside",
                textfont=dict(size=14, color="white", family="Inter"),
                hovertemplate="<b>%{label}</b><br>%{value:,} donors<br>%{percent}<extra></extra>",
                sort=False,
                pull=[0] * len(counts),
                rotation=45,
            )
        ]
    )

    total = int(counts.sum())
    fig.add_annotation(
        text=f"<b style='font-size:26px;color:{COLORS['primary_dark']}'>{total:,}</b><br><span style='font-size:11px;color:{COLORS['text_muted']};letter-spacing:0.08em'>TOTAL DONORS</span>",
        x=0.5, y=0.5, showarrow=False,
    )

    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
        height=340,
        margin=dict(l=10, r=10, t=10, b=40),
        transition=dict(duration=300, easing="cubic-in-out"),
    )
    return fig


# -----------------------------------------------------------------------------
# State distribution (donor count + donation amount)
# -----------------------------------------------------------------------------

def donors_by_state_bar(states_df: pd.DataFrame, top_n: int = 12) -> go.Figure:
    if states_df.empty or "Donors" not in states_df.columns:
        return _empty_fig()

    top = states_df.head(top_n).reset_index()
    top = top.sort_values("Donors", ascending=True)

    fig = go.Figure(
        go.Bar(
            x=top["Donors"],
            y=top["State"],
            orientation="h",
            marker=dict(
                color=top["Donors"],
                colorscale=[[0, "#C7E7F5"], [0.5, COLORS["teal"]], [1, COLORS["primary_dark"]]],
                line=dict(width=0),
            ),
            hovertemplate="<b>%{y}</b><br>%{x:,} donors<extra></extra>",
            text=top["Donors"].apply(lambda v: f"{int(v):,}"),
            textposition="outside",
            textfont=dict(size=11, color=COLORS["text"]),
            cliponaxis=False,
            hoverlabel=dict(bgcolor=COLORS["primary_dark"]),
        )
    )
    fig.update_layout(
        height=max(360, 28 * len(top) + 80),
        margin=dict(l=80, r=40, t=10, b=40),
        xaxis=dict(title="Donors", showgrid=True),
        yaxis=dict(title="", automargin=True),
        transition=dict(duration=250, easing="cubic-in-out"),
    )
    return fig


def donations_by_state_donut(states_df: pd.DataFrame, top_n: int = 9) -> go.Figure:
    if states_df.empty or "Total Gifts (All Time)" not in states_df.columns:
        return _empty_fig()

    amounts = states_df["Total Gifts (All Time)"].apply(_money)
    names, values = _group_top(states_df.index, amounts, top_n=top_n)

    fig = go.Figure(
        go.Pie(
            labels=names,
            values=values,
            hole=0.5,
            marker=dict(colors=CHART_COLORS, line=dict(color="#FFFFFF", width=3)),
            textinfo="percent",
            textposition="inside",
            textfont=dict(size=12, color="white"),
            hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>",
            sort=True,
            direction="clockwise",
            pull=[0] * len(names),
            rotation=30,
        )
    )
    fig.update_layout(
        height=340,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5, x=1.02),
        transition=dict(duration=300, easing="cubic-in-out"),
    )
    return fig


# -----------------------------------------------------------------------------
# City / borough donut
# -----------------------------------------------------------------------------

def donors_by_city_donut(city_counts: pd.DataFrame, title_state: str) -> go.Figure:
    if city_counts.empty:
        return _empty_fig()

    names, values = _group_top(city_counts["City"], city_counts["Donor Count"], top_n=9)
    fig = go.Figure(
        go.Pie(
            labels=names,
            values=values,
            hole=0.5,
            marker=dict(colors=CHART_COLORS, line=dict(color="#FFFFFF", width=3)),
            textinfo="percent",
            textposition="inside",
            textfont=dict(size=12, color="white"),
            hovertemplate="<b>%{label}</b><br>%{value:,} donors<br>%{percent}<extra></extra>",
            pull=[0] * len(names),
            rotation=30,
        )
    )
    fig.update_layout(
        height=340,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="v", yanchor="middle", y=0.5, x=1.02),
        transition=dict(duration=300, easing="cubic-in-out"),
    )
    return fig


def donation_amount_by_city_donut(city_amt: pd.Series) -> go.Figure:
    if city_amt is None or city_amt.empty:
        return _empty_fig()
    names, values = _group_top(city_amt.index, city_amt.values, top_n=9)
    fig = go.Figure(
        go.Pie(
            labels=names,
            values=values,
            hole=0.5,
            marker=dict(colors=CHART_COLORS, line=dict(color="#FFFFFF", width=3)),
            textinfo="percent",
            textposition="inside",
            textfont=dict(size=12, color="white"),
            hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>",
            pull=[0] * len(names),
            rotation=30,
        )
    )
    fig.update_layout(
        height=340,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="v", yanchor="middle", y=0.5, x=1.02),
        transition=dict(duration=300, easing="cubic-in-out"),
    )
    return fig


# -----------------------------------------------------------------------------
# Time series
# -----------------------------------------------------------------------------

def donors_by_year_bar(year_df: pd.DataFrame) -> go.Figure:
    if year_df is None or year_df.empty:
        return _empty_fig()
    data = year_df.reset_index()
    data.columns = ["Year", "Donors"]
    data = data.dropna(subset=["Year"])
    data["Year"] = data["Year"].astype(int)

    fig = go.Figure(
        go.Bar(
            x=data["Year"],
            y=data["Donors"],
            marker=dict(
                color=data["Donors"],
                colorscale=[[0, "#C9EBCC"], [0.5, COLORS["accent_light"]], [1, COLORS["accent_dark"]]],
                line=dict(width=0),
            ),
            hovertemplate="<b>%{x}</b><br>%{y:,} donors<extra></extra>",
            text=data["Donors"].apply(lambda v: f"{int(v):,}"),
            textposition="outside",
            textfont=dict(size=11, color=COLORS["text"]),
            cliponaxis=False,
            hoverlabel=dict(bgcolor=COLORS["accent_dark"]),
        )
    )
    fig.update_layout(
        height=340,
        margin=dict(l=40, r=20, t=10, b=50),
        xaxis=dict(title="Year", tickmode="linear", dtick=1),
        yaxis=dict(title="Donors"),
        transition=dict(duration=250, easing="cubic-in-out"),
    )
    return fig


def donors_by_month_bar(month_df: pd.DataFrame) -> go.Figure:
    if month_df is None or month_df.empty:
        return _empty_fig()
    month_df = month_df.copy().sort_values("MonthNum")
    fig = go.Figure(
        go.Bar(
            x=month_df["Month"],
            y=month_df["Donors"],
            marker=dict(
                color=month_df["Donors"],
                colorscale=[[0, "#C7E7F5"], [0.5, COLORS["teal"]], [1, COLORS["primary_dark"]]],
                line=dict(width=0),
            ),
            hovertemplate="<b>%{x}</b><br>%{y:,} donors<extra></extra>",
            text=month_df["Donors"].apply(lambda v: f"{int(v):,}"),
            textposition="outside",
            textfont=dict(size=11, color=COLORS["text"]),
            cliponaxis=False,
            hoverlabel=dict(bgcolor=COLORS["primary_dark"]),
        )
    )
    fig.update_layout(
        height=340,
        margin=dict(l=40, r=20, t=10, b=50),
        xaxis=dict(title="Month"),
        yaxis=dict(title="Donors"),
        transition=dict(duration=250, easing="cubic-in-out"),
    )
    return fig


# -----------------------------------------------------------------------------
# Heatmap / scatter map
# -----------------------------------------------------------------------------

def _is_valid_coord(lat, lon) -> bool:
    try:
        lat, lon = float(lat), float(lon)
    except Exception:
        return False
    if pd.isna(lat) or pd.isna(lon):
        return False
    if abs(lat) > 90 or abs(lon) > 180:
        return False
    if lat == 0 and lon == 0:
        return False
    # Kansas fallback exclusion
    if (36.99 <= lat <= 40.01) and (-102.06 <= lon <= -94.58):
        return False
    return True


def donor_map(df: pd.DataFrame, view: str = "markers") -> go.Figure:
    """Return a scatter_map or density_map figure.

    view: 'markers' | 'density' | 'both'
    """
    fig = go.Figure()

    if df.empty or "Latitude" not in df.columns:
        fig.update_layout(
            map=dict(style="open-street-map", center=dict(lat=40.7128, lon=-74.006), zoom=4),
            margin=dict(l=0, r=0, t=0, b=0),
            height=620,
        )
        fig.add_annotation(
            text="No geocoded donors available",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color=COLORS["text_muted"]),
        )
        return fig

    # Aggregate per rounded coordinate
    buckets: dict = defaultdict(lambda: {"count": 0, "total": 0.0, "labels": set()})
    invalid = 0
    for _, row in df.iterrows():
        lat, lon = row.get("Latitude"), row.get("Longitude")
        if not _is_valid_coord(lat, lon):
            invalid += 1
            continue
        key = (round(float(lat), 3), round(float(lon), 3))
        buckets[key]["count"] += 1
        try:
            buckets[key]["total"] += float(row.get("Total Gifts (All Time)", 0) or 0)
        except Exception:
            pass
        orig = str(row.get("OriginalLocation") or "").strip()
        city = str(row.get("City") or "").strip()
        state = str(row.get("State") or "").strip()
        label = orig or ", ".join([p for p in [city, state] if p]) or "Unknown"
        buckets[key]["labels"].add(label)

    if not buckets:
        fig.update_layout(
            map=dict(style="open-street-map", center=dict(lat=40.7128, lon=-74.006), zoom=4),
            margin=dict(l=0, r=0, t=0, b=0),
            height=620,
        )
        return fig

    lats, lons, counts, totals, labels = [], [], [], [], []
    for (lat, lon), info in buckets.items():
        lats.append(lat); lons.append(lon)
        counts.append(info["count"])
        totals.append(info["total"])
        label_list = sorted(info["labels"])
        extra = f" (+{len(label_list)-1} nearby)" if len(label_list) > 1 else ""
        labels.append(f"{label_list[0]}{extra}")

    # Density layer (underneath)
    if view in ("density", "both"):
        fig.add_trace(
            go.Densitymap(
                lat=lats, lon=lons, z=counts,
                radius=28, opacity=0.75,
                colorscale=[[0, "rgba(11,83,148,0)"], [0.35, "#93C5FD"], [0.7, "#2563EB"], [1, "#083761"]],
                showscale=False,
                hoverinfo="skip",
            )
        )

    # Marker layer on top
    if view in ("markers", "both"):
        marker_sizes = np.clip(np.sqrt(counts) * 5 + 6, 8, 36)
        fig.add_trace(
            go.Scattermap(
                lat=lats, lon=lons,
                mode="markers",
                marker=dict(
                    size=marker_sizes,
                    color=counts,
                    colorscale=[[0, "#60A5FA"], [1, COLORS["primary_dark"]]],
                    cmin=1,
                    opacity=0.85,
                ),
                customdata=list(zip(counts, totals, labels)),
                hovertemplate=(
                    "<b>%{customdata[2]}</b><br>"
                    "%{customdata[0]:,} donor(s)<br>"
                    "Total donated: $%{customdata[1]:,.2f}"
                    "<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        map=dict(
            style="open-street-map",
            center=dict(lat=40.7128, lon=-74.006),
            zoom=5,
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=640,
        showlegend=False,
    )
    return fig
