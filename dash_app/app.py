"""Riverkeeper Donor Intelligence Dashboard — Dash entry point.

Run directly:
    python -m dash_app.app
Or:
    python dash_app/app.py
"""

from __future__ import annotations

import base64
import io
import sys
import traceback
from pathlib import Path

import pandas as pd
from dash import ALL, ClientsideFunction, Dash, Input, MATCH, Output, State, html, no_update

# Local package-relative imports; support running as module or script.
if __package__ in (None, ""):
    ROOT = Path(__file__).resolve().parents[1]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

from dash_app import figures
from dash_app.data_io import clean, load_and_clean, load_enriched, stats_by_state
from dash_app.layout import build_layout, build_state_breakdown, statistics_tab, overview_tab, heatmap_tab, table_tab

import dash_bootstrap_components as dbc


# -----------------------------------------------------------------------------
# Global app state (simple — one dataset per process; fine for single-user use)
# -----------------------------------------------------------------------------
_DATA: pd.DataFrame = load_and_clean()


def _current_data() -> pd.DataFrame:
    global _DATA
    return _DATA


# -----------------------------------------------------------------------------
# App factory
# -----------------------------------------------------------------------------
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Riverkeeper Donor Intelligence",
    suppress_callback_exceptions=True,
    update_title=None,
)

app.layout = build_layout(_current_data())


# -----------------------------------------------------------------------------
# Callbacks
# -----------------------------------------------------------------------------

@app.callback(
    Output("upload-status", "children"),
    Output("main-tabs", "children"),
    Input("csv-upload", "contents"),
    State("csv-upload", "filename"),
    prevent_initial_call=True,
)
def handle_upload(contents, filename):
    """Replace the current dataset with an uploaded CSV and rebuild every tab.

    For now we treat the upload as a full replacement (no geocoding pipeline
    from the browser yet — that can be added once we have a background worker).
    """
    global _DATA

    if not contents:
        return no_update, no_update

    try:
        _, b64 = contents.split(",", 1)
        decoded = base64.b64decode(b64)
        new_df = pd.read_csv(io.BytesIO(decoded), on_bad_lines="skip", engine="python")
        _DATA = clean(new_df.copy())
    except Exception as exc:
        detail = html.Pre(traceback.format_exc(), style={"fontSize": "11px", "marginTop": "8px", "whiteSpace": "pre-wrap"})
        return dbc.Alert([html.Strong("Could not parse file. "), str(exc), detail], color="danger", className="fade-up"), no_update

    data = _current_data()
    status = dbc.Alert(
        [html.Strong("✓ Loaded "), f"{filename} — {len(data):,} rows"],
        color="success",
        className="fade-up",
        dismissable=True,
    )

    tabs = [
        dbc.Tab(overview_tab(data), label="Overview", tab_id="tab-overview"),
        dbc.Tab(statistics_tab(data), label="Statistics", tab_id="tab-stats"),
        dbc.Tab(heatmap_tab(data), label="Heatmap", tab_id="tab-map"),
        dbc.Tab(table_tab(data), label="Table Preview", tab_id="tab-table"),
    ]
    return status, tabs


@app.callback(
    Output("state-breakdown", "children"),
    Input("state-select", "value"),
    prevent_initial_call=False,
)
def update_state_breakdown(state):
    df = _current_data()
    if df.empty or not state:
        return None
    return build_state_breakdown(df, state)


@app.callback(
    Output("donor-map", "figure"),
    Input("map-view", "value"),
    prevent_initial_call=False,
)
def update_map(view):
    df = _current_data()
    return figures.donor_map(df, view=view or "both")


# Clientside callback: pop out the hovered slice on every pie chart
# that uses the {type: "pie-hover", index: <anything>} id pattern.
app.clientside_callback(
    ClientsideFunction(namespace="riverkeeper", function_name="pullSlice"),
    Output({"type": "pie-hover", "index": MATCH}, "figure"),
    Input({"type": "pie-hover", "index": MATCH}, "hoverData"),
    State({"type": "pie-hover", "index": MATCH}, "figure"),
    prevent_initial_call=True,
)


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------
def main() -> None:
    print("[INFO] Starting Riverkeeper Dash app at http://127.0.0.1:8050")
    app.run(host="127.0.0.1", port=8050, debug=False)


if __name__ == "__main__":
    main()
