"""Top-level layout for the Riverkeeper Dash app."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc

from . import figures
from .components import (
    chart_card,
    empty_state,
    info_alert,
    kpi_tile,
    section_heading,
)
from .data_io import (
    active_donors,
    basic_stats,
    frequent_donors,
    inactive_donors,
    stats_by_month,
    stats_by_state,
    stats_by_year,
    stats_no_location,
    top_donors,
)


# -----------------------------------------------------------------------------
# Shell
# -----------------------------------------------------------------------------

def topbar() -> html.Div:
    return html.Div(
        [
            html.Div(
                [
                    html.Img(src="/assets/RKlogo.png", className="brand-logo", alt="Riverkeeper"),
                    html.Div(
                        [
                            html.Span("RIVERKEEPER", className="brand-title"),
                            html.Span("Donor Intelligence Dashboard", className="brand-sub"),
                        ],
                        className="brand-text",
                    ),
                ],
                className="topbar-brand",
            ),
            html.Div(
                [
                    html.Span("LIVE", className="topbar-badge"),
                    html.Span(f"Updated {datetime.now().strftime('%b %d, %Y')}"),
                ],
                className="topbar-meta",
            ),
        ],
        className="topbar",
    )


def page_header() -> html.Div:
    return html.Div(
        [
            html.H1("Donor Analytics", className="page-title"),
            html.P(
                "Upload donor CSVs, merge and enrich them, and explore the full picture of Riverkeeper's supporters.",
                className="page-subtitle",
            ),
        ],
        className="page-header fade-up",
    )


def upload_card() -> dbc.Card:
    return dbc.Card(
        dbc.CardBody(
            [
                dcc.Upload(
                    id="csv-upload",
                    multiple=False,
                    children=html.Div(
                        [
                            html.Div("⬆  Drop a Riverkeeper-formatted CSV here", className="upload-zone-title"),
                            html.Div("or click to browse — new donors will be merged and geocoded automatically", className="upload-zone-sub"),
                        ]
                    ),
                    className="upload-zone",
                ),
                html.Div(id="upload-status"),
            ]
        ),
        className="fade-up",
    )


# -----------------------------------------------------------------------------
# Overview tab
# -----------------------------------------------------------------------------

def _safe_stats_row(df: pd.DataFrame) -> dict:
    try:
        return basic_stats(df).iloc[0].to_dict()
    except Exception:
        return {}


def overview_tab(df: pd.DataFrame) -> html.Div:
    if df.empty:
        return html.Div([empty_state("Upload a donor CSV to see the overview.", "🌊")])

    stats = _safe_stats_row(df)
    active_row = {}
    try:
        active_row = active_donors(df).iloc[0].to_dict()
    except Exception:
        pass

    total_donors = int(df["Account ID"].nunique())
    active_count = int(active_row.get("Active Donors", 0) or 0)
    active_pct = f"{(active_count / total_donors * 100):.0f}%" if total_donors else "0%"

    kpis = html.Div(
        [
            kpi_tile("Total Donors", f"{total_donors:,}", "All-time unique donors"),
            kpi_tile("Total Donated", stats.get("Total Donation Amount", "$0.00"), "Across all recorded gifts", variant="green"),
            kpi_tile("Active Donors", f"{active_count:,}", f"{active_pct} gave in past 18 months", variant="teal"),
            kpi_tile("Gifts (18 mo)", f"{int(stats.get('Gifts in Past 18 Months', 0) or 0):,}", "Donation events", variant="amber"),
            kpi_tile("Average Gift", stats.get("Average Total Donation", "$0.00"), "Per donor lifetime total"),
            kpi_tile("Median Gift", stats.get("Median Total Donation", "$0.00"), "Middle of the distribution"),
        ],
        className="kpi-grid",
    )

    states_df = stats_by_state(df)

    charts_row_1 = html.Div(
        [
            chart_card(
                "Donor status",
                dcc.Graph(
                    id={"type": "pie-hover", "index": "overview-status"},
                    figure=figures.donor_status_donut(df),
                    config={"displayModeBar": False},
                ),
                subtitle="Active vs inactive in the past 18 months",
            ),
            chart_card(
                "Donors by state",
                dcc.Graph(figure=figures.donors_by_state_bar(states_df), config={"displayModeBar": False}),
                subtitle="Top 12 states by donor count",
            ),
        ],
        className="grid-2",
        style={"marginBottom": "16px"},
    )

    charts_row_2 = html.Div(
        [
            chart_card(
                "Where the dollars come from",
                dcc.Graph(
                    id={"type": "pie-hover", "index": "overview-dollars"},
                    figure=figures.donations_by_state_donut(states_df),
                    config={"displayModeBar": False},
                ),
                subtitle="Share of total lifetime donations by state",
            ),
            chart_card(
                "Gifts over time — by year",
                dcc.Graph(figure=figures.donors_by_year_bar(stats_by_year(df)), config={"displayModeBar": False}),
                subtitle="Donors whose most recent gift fell in this year",
            ),
        ],
        className="grid-2",
    )

    return html.Div([kpis, charts_row_1, charts_row_2], className="fade-up")


# -----------------------------------------------------------------------------
# Statistics tab
# -----------------------------------------------------------------------------

def _df_to_table(df: pd.DataFrame, page_size: int = 10) -> dash_table.DataTable:
    """Standardised styling for data tables."""
    records = df.reset_index().to_dict("records") if df.index.name else df.to_dict("records")
    columns = [{"name": str(c), "id": str(c)} for c in (df.reset_index().columns if df.index.name else df.columns)]
    return dash_table.DataTable(
        data=records,
        columns=columns,
        page_size=page_size,
        style_as_list_view=True,
        style_header={
            "backgroundColor": "var(--surface-alt)",
            "color": "var(--text-muted)",
            "fontWeight": "600",
            "fontSize": "12px",
            "textTransform": "uppercase",
            "letterSpacing": "0.04em",
            "border": "none",
            "borderBottom": "1px solid var(--border)",
            "padding": "12px 14px",
        },
        style_cell={
            "fontFamily": '"Inter", system-ui, sans-serif',
            "fontSize": "13px",
            "textAlign": "left",
            "padding": "10px 14px",
            "border": "none",
            "borderBottom": "1px solid var(--border)",
            "color": "var(--text)",
            "backgroundColor": "var(--surface)",
        },
        style_data_conditional=[
            {"if": {"state": "active"}, "backgroundColor": "var(--primary-soft)", "border": "none"},
            {"if": {"row_index": "odd"}, "backgroundColor": "var(--surface-alt)"},
        ],
        style_table={"overflowX": "auto", "borderRadius": "12px", "border": "1px solid var(--border)"},
    )


def statistics_tab(df: pd.DataFrame) -> html.Div:
    if df.empty:
        return html.Div([empty_state("Upload a donor CSV to see statistics.", "📈")])

    states_df = stats_by_state(df)

    # State selector
    state_options = sorted([s for s in df["State"].dropna().unique().tolist() if str(s) != ""])
    default_state = "New York" if "New York" in state_options else (state_options[0] if state_options else None)

    return html.Div(
        [
            section_heading("Activity summary"),
            html.Div(
                [
                    chart_card("Active donors", _df_to_table(active_donors(df), page_size=1)),
                    chart_card("Inactive donors", _df_to_table(inactive_donors(df), page_size=1)),
                ],
                className="grid-2",
                style={"marginBottom": "12px"},
            ),

            section_heading("Top performers"),
            html.Div(
                [
                    chart_card("Top 20 by total amount", _df_to_table(top_donors(df, 20), page_size=10)),
                    chart_card("Top 20 by frequency (18 mo)", _df_to_table(frequent_donors(df, 20), page_size=10)),
                ],
                className="grid-2",
                style={"marginBottom": "12px"},
            ),

            section_heading("Geography", "Breakdown by state, city, and NYC boroughs"),
            chart_card("State summary", _df_to_table(states_df, page_size=15)),

            html.Div(style={"height": "16px"}),
            html.Div(
                [
                    html.Label("Focus on a state", style={"fontSize": "12px", "fontWeight": 600, "color": "var(--text-muted)", "textTransform": "uppercase", "letterSpacing": "0.05em", "marginRight": "12px"}),
                    dcc.Dropdown(
                        id="state-select",
                        options=[{"label": s, "value": s} for s in state_options],
                        value=default_state,
                        clearable=False,
                        style={"width": "260px", "display": "inline-block"},
                    ),
                ],
                style={"display": "flex", "alignItems": "center", "gap": "8px", "marginBottom": "16px"},
            ),
            html.Div(id="state-breakdown", className="fade-up"),

            section_heading("Gifts over time"),
            html.Div(
                [
                    chart_card("Donors by year", dcc.Graph(figure=figures.donors_by_year_bar(stats_by_year(df)), config={"displayModeBar": False})),
                    chart_card("Donors by month", dcc.Graph(figure=figures.donors_by_month_bar(stats_by_month(df)), config={"displayModeBar": False})),
                ],
                className="grid-2",
            ),

            section_heading("Data quality"),
            chart_card("Donors with missing location info", _df_to_table(stats_no_location(df), page_size=5)),
        ],
        className="fade-up",
    )


def build_state_breakdown(df: pd.DataFrame, state: str) -> html.Div:
    """Per-state city / borough breakdown."""
    state_data = df[df["State"] == state].copy()
    if state_data.empty:
        return info_alert(f"No donors found in {state}.", "warning")

    city_counts = state_data["City"].value_counts().reset_index()
    city_counts.columns = ["City", "Donor Count"]
    city_amt = state_data.groupby("City")["Total Gifts (All Time)"].apply(
        lambda s: pd.to_numeric(s.astype(str).str.replace(r"[\$,]", "", regex=True), errors="coerce").sum()
    )

    row1 = html.Div(
        [
            chart_card(
                f"Donors by city in {state}",
                dcc.Graph(
                    id={"type": "pie-hover", "index": f"city-count-{state}"},
                    figure=figures.donors_by_city_donut(city_counts, state),
                    config={"displayModeBar": False},
                ),
            ),
            chart_card(
                f"Donation amount by city in {state}",
                dcc.Graph(
                    id={"type": "pie-hover", "index": f"city-amt-{state}"},
                    figure=figures.donation_amount_by_city_donut(city_amt),
                    config={"displayModeBar": False},
                ),
            ),
        ],
        className="grid-2",
    )

    children = [row1]
    if state == "New York":
        boroughs = ["Manhattan", "Queens", "Brooklyn", "The Bronx", "Staten Island"]
        nyc = state_data[state_data["County"].isin(boroughs)] if "County" in state_data.columns else pd.DataFrame()
        if not nyc.empty:
            borough_counts = nyc["County"].value_counts().reset_index()
            borough_counts.columns = ["City", "Donor Count"]
            borough_amt = nyc.groupby("County")["Total Gifts (All Time)"].apply(
                lambda s: pd.to_numeric(s.astype(str).str.replace(r"[\$,]", "", regex=True), errors="coerce").sum()
            )
            children.append(
                html.Div(
                    [
                        chart_card(
                            "Donors by borough — NYC",
                            dcc.Graph(
                                id={"type": "pie-hover", "index": "nyc-borough-count"},
                                figure=figures.donors_by_city_donut(borough_counts, "New York City"),
                                config={"displayModeBar": False},
                            ),
                        ),
                        chart_card(
                            "Donation amount by borough — NYC",
                            dcc.Graph(
                                id={"type": "pie-hover", "index": "nyc-borough-amt"},
                                figure=figures.donation_amount_by_city_donut(borough_amt),
                                config={"displayModeBar": False},
                            ),
                        ),
                    ],
                    className="grid-2",
                    style={"marginTop": "16px"},
                )
            )

    return html.Div(children)


# -----------------------------------------------------------------------------
# Heatmap tab
# -----------------------------------------------------------------------------

def heatmap_tab(df: pd.DataFrame) -> html.Div:
    if df.empty:
        return html.Div([empty_state("Upload a donor CSV to see the map.", "🗺️")])

    controls = html.Div(
        [
            html.Div(
                [
                    html.Label("Map view", style={"fontSize": "12px", "fontWeight": 600, "color": "var(--text-muted)", "textTransform": "uppercase", "letterSpacing": "0.05em", "marginBottom": "6px", "display": "block"}),
                    dcc.RadioItems(
                        id="map-view",
                        options=[
                            {"label": " Markers", "value": "markers"},
                            {"label": " Density", "value": "density"},
                            {"label": " Both", "value": "both"},
                        ],
                        value="both",
                        inline=True,
                        inputStyle={"marginRight": "4px", "marginLeft": "12px"},
                        labelStyle={"marginRight": "8px", "color": "var(--text)", "fontSize": "13px", "cursor": "pointer"},
                    ),
                ]
            ),
        ],
        style={"padding": "14px 18px", "borderBottom": "1px solid var(--border)"},
    )

    return html.Div(
        [
            section_heading("Donor Heatmap", "Interactive map — hover for details, scroll to zoom"),
            html.Div(
                [
                    controls,
                    dcc.Loading(
                        id="map-loading",
                        type="default",
                        color="var(--primary)",
                        children=dcc.Graph(
                            id="donor-map",
                            figure=figures.donor_map(df, view="both"),
                            config={
                                "displayModeBar": True,
                                "displaylogo": False,
                                "modeBarButtonsToRemove": ["lasso2d", "select2d"],
                                "scrollZoom": True,
                            },
                            style={"height": "640px"},
                        ),
                    ),
                ],
                className="chart-card",
                style={"padding": 0, "overflow": "hidden"},
            ),
        ],
        className="fade-up",
    )


# -----------------------------------------------------------------------------
# Table tab
# -----------------------------------------------------------------------------

def table_tab(df: pd.DataFrame) -> html.Div:
    if df.empty:
        return html.Div([empty_state("Upload a donor CSV to see the data preview.", "📋")])

    preview = df.head(50).copy()
    # Format money nicely
    if "Total Gifts (All Time)" in preview.columns:
        preview["Total Gifts (All Time)"] = preview["Total Gifts (All Time)"].apply(
            lambda v: f"${float(v):,.2f}" if pd.notna(pd.to_numeric(v, errors="coerce")) else v
        )

    return html.Div(
        [
            section_heading("Data preview", f"First 50 of {len(df):,} rows"),
            chart_card("Enriched donor dataset", _df_to_table(preview, page_size=15)),
        ],
        className="fade-up",
    )


# -----------------------------------------------------------------------------
# Root layout
# -----------------------------------------------------------------------------

def build_layout(df: pd.DataFrame) -> html.Div:
    return html.Div(
        [
            dcc.Store(id="data-loaded", data=not df.empty),
            topbar(),
            html.Main(
                [
                    page_header(),
                    upload_card(),
                    dbc.Tabs(
                        id="main-tabs",
                        active_tab="tab-overview",
                        children=[
                            dbc.Tab(overview_tab(df), label="Overview", tab_id="tab-overview"),
                            dbc.Tab(statistics_tab(df), label="Statistics", tab_id="tab-stats"),
                            dbc.Tab(heatmap_tab(df), label="Heatmap", tab_id="tab-map"),
                            dbc.Tab(table_tab(df), label="Table Preview", tab_id="tab-table"),
                        ],
                    ),
                ],
                className="main",
            ),
            html.Footer(
                [
                    html.Img(src="/assets/RKlogo.png", className="footer-logo", alt=""),
                    html.Span("Built for Riverkeeper — defending the Hudson River since 1966."),
                ],
                className="footer",
            ),
        ],
        className="app-shell",
    )
