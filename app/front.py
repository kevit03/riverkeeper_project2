import pandas as pd
import streamlit as st
import sys
import traceback
from pathlib import Path

# Add repo root to sys.path so 'scripts' is importable
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from functions.data_analysis import clean  # noqa: E402
from functions.frontend_helpers import (  # noqa: E402
    PERSISTENT_ENRICHED,
    load_enriched,
    load_raw,
    merge_and_enrich,
    render_stats,
)
from functions.heatmap import geocode_if_needed, render_map  # noqa: E402



def main() -> None:
    st.set_page_config(
        page_title="Riverkeeper Donor Dashboard",
        page_icon="🌊",
        layout="wide",
    )
    st.title("Riverkeeper Donor Dashboard")
    st.markdown("Upload donor CSVs, merge and enrich them, then explore updated statistics.")

    # ---- Session state ----
    if "data" not in st.session_state:
        st.session_state.data = None
    if "raw_df" not in st.session_state:
        st.session_state.raw_df = load_raw()

    # ---- File upload + merge/enrich ----
    uploaded = st.file_uploader("Upload a Riverkeeper-formatted CSV", type=["csv"])
    if uploaded is not None:
        try:
            uploaded.seek(0)
            new_df = pd.read_csv(uploaded, on_bad_lines="skip", engine="python")
            with st.spinner("Merging, cleaning, and enriching data..."):
                st.session_state.data = merge_and_enrich(new_df)
                st.session_state.raw_df = load_raw()
            st.success("Dataset merged and enriched. Enriched CSV updated.")
        except Exception as exc:
            st.error(f"Could not process file: {exc.__class__.__name__}: {exc}")
            st.code(traceback.format_exc())

    # ---- Ensure we have a working dataframe ----
    if st.session_state.data is None:
        enriched = load_enriched()
        if len(enriched) == 0:
            st.info("No data loaded yet. Upload a CSV to get started.")
            return
        st.session_state.data = clean(enriched.copy())

    data = st.session_state.data

    st.markdown(f"**Enriched CSV:** `{PERSISTENT_ENRICHED}` • Rows: {len(data)}")

    # ---- Tabs: Table / Stats / Heatmap ----
    tab_table, tab_stats, tab_heatmap = st.tabs(["Table Preview", "Statistics", "Heatmap"])

    with tab_table:
        st.subheader("Data Preview")
        st.dataframe(data.head(50), width="stretch")

    with tab_stats:
        st.subheader("Donor Statistics")
        render_stats(data)

    with tab_heatmap:
        work_df = geocode_if_needed(data, cache_path=None, geocode_limit=10_000)
        render_map(work_df)


if __name__ == "__main__":
    main()
