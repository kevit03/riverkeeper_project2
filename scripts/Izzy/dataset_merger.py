import streamlit as st
import pandas as pd
import numpy as np
import os
from merge_csv import merge_csv

PATH = "donor_data.csv"

# load existing data if the file exists
# if it does not exist, create an empty dataframe
def load_data():
        if os.path.exists(PATH):
            return pd.read_csv(PATH)
        else:
            df = pd.DataFrame()
            df.to_csv(PATH, index=False)
            return df
    
# save data to csv
def save_data(df):
    df.to_csv(PATH, index=False)

def run():

    st.set_page_config(
    page_title="Dataset Merger",
    page_icon="📁",
    layout="wide"
    )

    st.header("Dataset Merger")
    st.write("Upload a new dataset below to merge with the existing dataset.")

    # load dataset into the user's session if it does not already exist
    if "df" not in st.session_state:
        st.session_state.df = load_data()

    # button to upload new csv
    uploaded_file = st.file_uploader("", type="csv")

    if uploaded_file:

        # merge datasets
        new_df = pd.read_csv(uploaded_file)
        merged_df, _ = merge_csv(st.session_state.df, new_df, save=False)

        # save the merged data and update the session state
        save_data(merged_df)
        st.session_state.df = merged_df

        st.success("Merged CSV saved and updated!")
        st.space(size="small")

        # display new data
        st.write("Merged Dataset:")
        st.dataframe(merged_df)
