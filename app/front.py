import pandas as pd
import streamlit as st
import sys
from pathlib import Path

# Add repo root to sys.path so 'scripts' is importable
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))


from functions.data_analysis import clean
from functions.frontend_helpers import (
    PERSISTENT_CSV,
    load_persistent,
    merge_and_enrich,
    render_stats,
)

# 👇 import the heatmap renderer from your Kevin file
# adjust the module name/path as needed
from scripts.Kevin.heatmap import render_heatmap



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
        st.session_state.raw_df = load_persistent()

    # ---- File upload + merge/enrich ----
    uploaded = st.file_uploader("Upload a Riverkeeper-formatted CSV", type=["csv"])
    if uploaded is not None:
        try:
            new_df = pd.read_csv(uploaded)
            with st.spinner("Merging, cleaning, and enriching data..."):
                st.session_state.data = merge_and_enrich(new_df)
                st.session_state.raw_df = load_persistent()
            st.success("Dataset merged and enriched. Persistent CSV updated.")
        except Exception as exc:
            st.error(f"Could not process file: {exc}")

    # ---- Ensure we have a working dataframe ----
    if st.session_state.data is None:
        if len(st.session_state.raw_df) == 0:
            st.info("No data loaded yet. Upload a CSV to get started.")
            return
        st.session_state.data = clean(st.session_state.raw_df.copy())

    data = st.session_state.data

    st.markdown(f"**Persistent CSV:** `{PERSISTENT_CSV}` • Rows: {len(data)}")

    # ---- Tabs: Table / Stats / Heatmap ----
    tab_table, tab_stats, tab_heatmap = st.tabs(["Table Preview", "Statistics", "Heatmap"])

    with tab_table:
        st.subheader("Data Preview")
        st.dataframe(data.head(50), use_container_width=True)

    with tab_stats:
        st.subheader("Donor Statistics")
        render_stats(data)

    with tab_heatmap:
        # 🔥 Call into your heatmap file here
        render_heatmap(data)


if __name__ == "__main__":
    main()
