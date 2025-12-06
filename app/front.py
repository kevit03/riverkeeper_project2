import pandas as pd
import streamlit as st

from functions.data_analysis import clean
from functions.frontend_helpers import (
    PERSISTENT_CSV,
    load_persistent,
    merge_and_enrich,
    render_stats,
)


def main() -> None:
    st.set_page_config(page_title="Riverkeeper Donor Dashboard", page_icon="🌊", layout="wide")
    st.title("Riverkeeper Donor Dashboard")
    st.markdown("Upload donor CSVs, merge and enrich them, then explore updated statistics.")

    if "data" not in st.session_state:
        st.session_state.data = None
    if "raw_df" not in st.session_state:
        st.session_state.raw_df = load_persistent()

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

    if st.session_state.data is None:
        if len(st.session_state.raw_df) == 0:
            st.info("No data loaded yet. Upload a CSV to get started.")
            return
        st.session_state.data = clean(st.session_state.raw_df.copy())

    data = st.session_state.data

    st.markdown(f"**Persistent CSV:** `{PERSISTENT_CSV}` • Rows: {len(data)}")
    st.dataframe(data.head(50), use_container_width=True)

    render_stats(data)


if __name__ == "__main__":
    main()
