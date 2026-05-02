"""Riverkeeper Donor Intelligence Dashboard — Dash entry point.

Run directly:
    python -m dash_app.app
Or:
    python dash_app/app.py
"""

from __future__ import annotations

import base64
import io
import os
import sys
import traceback
from pathlib import Path

import pandas as pd
from dash import ALL, ClientsideFunction, Dash, Input, MATCH, Output, State, ctx, dcc, html, no_update

# Local package-relative imports; support running as module or script.
if __package__ in (None, ""):
    ROOT = Path(__file__).resolve().parents[1]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

from dash_app import figures
from dash_app.data_io import clean, enrich_uploaded_locations, load_and_clean
from dash_app.layout import build_layout, build_state_breakdown, statistics_tab, overview_tab, heatmap_tab, table_tab
from dash_app.storage import delete_csv, list_csv_uploads, upload_csv

import dash_bootstrap_components as dbc


_DATA: pd.DataFrame = load_and_clean()


def _current_data() -> pd.DataFrame:
    global _DATA
    return _DATA


app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Riverkeeper Donor Intelligence",
    suppress_callback_exceptions=True,
    update_title=None,
)

app.layout = build_layout(_current_data())
server = app.server


def _format_size(size: int | None) -> str:
    if size is None:
        return "unknown size"
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def _render_upload_manager(notice=None):
    result = list_csv_uploads()
    children = []
    if notice is not None:
        children.append(notice)

    if not result.enabled:
        children.append(html.Div(result.message, className="upload-manager-empty"))
        return children

    if not result.ok:
        children.append(dbc.Alert(result.message, color="warning", className="fade-up"))
        return children

    if not result.items:
        children.append(html.Div("No saved CSV uploads found yet.", className="upload-manager-empty"))
        return children

    rows = []
    for item in result.items:
        meta = " · ".join(part for part in [_format_size(item.size), item.created_at[:10]] if part)
        rows.append(
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(item.name, className="upload-manager-file"),
                            html.Div(meta, className="upload-manager-meta"),
                        ]
                    ),
                    dcc.ConfirmDialogProvider(
                        children=dbc.Button("Delete", color="outline-danger", size="sm"),
                        id={"type": "delete-upload", "path": item.object_path},
                        message=f"Delete {item.name} from Supabase Storage? This cannot be undone.",
                    ),
                ],
                className="upload-manager-row",
            )
        )

    children.append(html.Div(rows, className="upload-manager-list"))
    return children


def _merge_uploaded_data(current: pd.DataFrame, uploaded: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    cleaned_upload = clean(enrich_uploaded_locations(uploaded.copy()))
    before_count = len(current)
    merged = pd.concat([current, cleaned_upload], ignore_index=True, sort=False)

    if "Account ID" in merged.columns:
        known_ids = merged["Account ID"].notna() & (merged["Account ID"].astype(str).str.strip() != "")
        with_ids = merged[known_ids].drop_duplicates(subset=["Account ID"], keep="last")
        without_ids = merged[~known_ids]
        merged = pd.concat([with_ids, without_ids], ignore_index=True, sort=False)

    return merged, max(len(merged) - before_count, 0)


@app.callback(
    Output("upload-status", "children"),
    Output("main-tabs", "children"),
    Output("upload-manager", "children"),
    Input("csv-upload", "contents"),
    State("csv-upload", "filename"),
    prevent_initial_call=True,
)
def handle_upload(contents, filename):
    """Append an uploaded CSV to the active dataset and rebuild every tab."""
    global _DATA

    if not contents:
        return no_update, no_update, no_update

    try:
        _, b64 = contents.split(",", 1)
        decoded = base64.b64decode(b64)
        new_df = pd.read_csv(io.BytesIO(decoded), on_bad_lines="skip", engine="python")
        uploaded_rows = len(new_df)
        _DATA, added_rows = _merge_uploaded_data(_current_data(), new_df)
        storage_result = upload_csv(decoded, filename)
    except Exception as exc:
        detail = html.Pre(traceback.format_exc(), style={"fontSize": "11px", "marginTop": "8px", "whiteSpace": "pre-wrap"})
        return dbc.Alert([html.Strong("Could not parse file. "), str(exc), detail], color="danger", className="fade-up"), no_update, no_update

    data = _current_data()
    storage_badge = html.Div(storage_result.message, className="upload-status-note")
    status = dbc.Alert(
        [
            html.Strong("✓ Merged "),
            f"{filename} — {uploaded_rows:,} uploaded rows, {added_rows:,} new rows added, {len(data):,} total rows now",
            storage_badge,
        ],
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
    manager = _render_upload_manager() if storage_result.ok else no_update
    return status, tabs, manager


@app.callback(
    Output("upload-manager", "children", allow_duplicate=True),
    Input("refresh-uploads", "n_clicks"),
    Input({"type": "delete-upload", "path": ALL}, "submit_n_clicks"),
    prevent_initial_call=True,
)
def manage_saved_uploads(_refresh_clicks, _delete_clicks):
    notice = None
    triggered = ctx.triggered_id
    if isinstance(triggered, dict) and triggered.get("type") == "delete-upload":
        result = delete_csv(str(triggered.get("path", "")))
        notice = dbc.Alert(result.message, color="success" if result.ok else "danger", className="fade-up", dismissable=True)
    return _render_upload_manager(notice)


@app.callback(
    Output("upload-status", "children", allow_duplicate=True),
    Output("main-tabs", "children", allow_duplicate=True),
    Input("reset-dashboard", "n_clicks"),
    prevent_initial_call=True,
)
def reset_dashboard(_n_clicks):
    global _DATA
    _DATA = load_and_clean()
    data = _current_data()
    status = dbc.Alert("Dashboard reset to the original bundled donor dataset.", color="info", className="fade-up", dismissable=True)
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


def main() -> None:
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8050"))
    print(f"[INFO] Starting Riverkeeper Dash app at http://127.0.0.1:{port}")
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
