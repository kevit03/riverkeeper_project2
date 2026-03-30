import streamlit as st
from dataset_merger import run as run_dataset_merger
from analytics import run as run_analytics

dataset_merger = st.Page(run_dataset_merger, title="Dataset Merger", icon="📁", url_path="dataset_merger.py", default=True)
analytics = st.Page(run_analytics, title="Donor Analytics", icon="📊", url_path="analytics.py")

current_page = st.navigation([dataset_merger, analytics], position="top")
current_page.run()