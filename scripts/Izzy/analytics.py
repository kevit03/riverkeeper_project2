import streamlit as st
import pandas as pd
import numpy as np
from data_analysis import *
import plotly.express as px
import os
import sys
from pathlib import Path
import importlib.util

PATH = "donor_data.csv"
location_path = (Path(__file__).parent / ".." / "Vincent" / "location.py").resolve()

# loading location module
spec = importlib.util.spec_from_file_location("location", str(location_path))
location = importlib.util.module_from_spec(spec)
spec.loader.exec_module(location)
transform = location.run

st.set_page_config(
    page_title="Donor Analytics",
    page_icon="📊",
    layout="wide"
)

def run():

    # convert to biokind format, clean, and store in session state
    if "bkdf" not in st.session_state:
        with st.spinner("Analyzing Data..."):
            st.session_state.bkdf = transform(PATH)
            st.session_state.bkdf = clean(st.session_state.bkdf)
    data = st.session_state.bkdf

    # radio buttons for persistent tabs
    tabs = ["Basic Statistics", "Top Donors", "Donors by Location", "Donors by Date"]
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = tabs[0]
    st.session_state.active_tab = st.radio("", tabs, index=tabs.index(st.session_state.active_tab), horizontal=True)

    if st.session_state.active_tab == "Basic Statistics":
        st.header("Basic Statistics")

        ##### breakdown for all donors
        st.subheader("Basic Statistics for All Donors")
        stats = basic_stats(data)
        st.dataframe(stats)

        ##### breakdown for active donors
        st.subheader("Basic Statistics for Active Donors")
        stats_active = active_donors(data)
        st.dataframe(stats_active)
        st.caption("*An active donor is defined as a donor who has donated at least once within the past 18 months.")
        
        ##### breakdown for inactive donors
        st.subheader("Basic Statistics for Inactive Donors")
        stats_inactive = inactive_donors(data)
        st.dataframe(stats_inactive)
        st.caption("*An inactive donor is defined as a donor who has not donated within the past 18 months.")

    elif st.session_state.active_tab == "Top Donors":
        
        st.header("Top Donors")
        
        if "metric" not in st.session_state:
            st.session_state.metric = "Total Amount Donated"

        st.session_state.metric = st.selectbox("Select top donor metric:", ["Total Amount Donated", "Donation Frequency (Past 18 Months)"])

        if st.session_state.metric == "Total Amount Donated":

            st.subheader("Top 100 Donors by Total Amount Donated")

            top_amt = top_donors(data, 100)
            st.dataframe(top_amt)

            top_amt["Status"] = top_amt["Number of Gifts Past 18 Months"].apply(lambda x: "Active" if x>0 else "Inactive")
            activity_counts = top_amt["Status"].value_counts()
            fig = px.pie(names=activity_counts.index, 
                         values=activity_counts.values, 
                         title="Status of Top 100 Donors", 
                         color_discrete_sequence=px.colors.qualitative.Safe)
            fig.update_traces(hovertemplate='%{label}: %{value} (%{percent})')
            st.plotly_chart(fig)

            col1, empty, col2 = st.columns([3, 1, 3])
            
            with col1: 
                state_counts = top_amt["State"].value_counts()
                fig = px.pie(names=state_counts.index, 
                            values=state_counts.values, 
                            title="States of Top 100 Donors", 
                            color_discrete_sequence=px.colors.qualitative.Safe)
                fig.update_traces(hovertemplate='%{label}: %{value} (%{percent})')
                st.plotly_chart(fig)

            with col2:
                ny = top_amt[top_amt["State"] == "New York"]
                nyc = ["Brooklyn", "Queens", "The Bronx", "Bronx", "Staten Island", "Manhattan", "New York City"]
                ny["City"] = ny["City"].replace(nyc, "New York")
                city_counts = ny["City"].value_counts()
                fig = px.pie(names=city_counts.index, 
                            values=city_counts.values, 
                            title="Cities of Top Donors from New York State", 
                            color_discrete_sequence=px.colors.qualitative.Safe)
                fig.update_traces(hovertemplate='%{label}: %{value} (%{percent})')
                st.plotly_chart(fig)

        if st.session_state.metric == "Donation Frequency (Past 18 Months)":

            st.subheader("Top 100 Donors by Donation Frequency (Past 18 Months)")

            top_freq = frequent_donors(data, 100)
            st.dataframe(top_freq)

            col1, empty, col2 = st.columns([3, 1, 3])

            with col1: 
                state_counts = top_freq["State"].value_counts()
                fig = px.pie(names=state_counts.index, 
                            values=state_counts.values, 
                            title="States of Top 100 Donors", 
                            color_discrete_sequence=px.colors.qualitative.Safe,
                            )
                fig.update_traces(rotation=45)
                fig.update_traces(hovertemplate='%{label}: %{value} (%{percent})')
                st.plotly_chart(fig)

            with col2:
                ny = top_freq[top_freq["State"] == "New York"]
                nyc = ["Brooklyn", "Queens", "The Bronx", "Bronx", "Staten Island", "Manhattan", "New York City"]
                ny["City"] = ny["City"].replace(nyc, "New York")
                city_counts = ny["City"].value_counts()
                fig = px.pie(names=city_counts.index, 
                            values=city_counts.values, 
                            title="Cities of Top Donors from New York State", 
                            color_discrete_sequence=px.colors.qualitative.Safe)
                fig.update_traces(hovertemplate='%{label}: %{value} (%{percent})')
                st.plotly_chart(fig)


    elif st.session_state.active_tab == "Donors by Location":
        
        st.header("Donors by Location")

        ##### breakdown of states
        states = stats_by_state(data)

        # separating out states with 1% of donors from the rest for pie chart
        threshold = 0.01
        states_pie = states[states["Donors"] / states["Donors"].sum() >= threshold]
        other_states = states[states["Donors"] / states["Donors"].sum() < threshold]
        other_total = other_states["Donors"].sum()
        states_pie.loc["Other"] = other_total

        # pie chart of states and donors
        fig = px.pie(states_pie, 
                     names=states_pie.index, 
                     values="Donors", 
                     title="Percentage of Donors from Each State", 
                     color_discrete_sequence=px.colors.qualitative.Safe
                     )
        fig.update_traces(hovertemplate='%{label}: %{value} (%{percent})')
        st.plotly_chart(fig)
        st.caption("*States with less than 1% of the donors are grouped into 'Other'.")

        ##### breakdown of cities in each state
        st.space(size="small")

        # getting list of unique states
        states = data["State"].unique()
        states = [str(s) for s in states if s != ""]
        states = [s for s in states if s != "nan"]        
        states.sort()

        # setting default state
        if "state" not in st.session_state:
            st.session_state.state = "New York"

        # state selectbox and get data from that state
        st.selectbox("Select a state to view a breakdown of cities in that state:", options=states, key="state")
        state_data = data[data["State"] == st.session_state.state].copy()

        # fixing nyc if ny
        if st.session_state.state == "New York":
            boroughs = ["Brooklyn", "Queens", "The Bronx", "Staten Island", "Manhattan"]
            state_data.loc[state_data["Borough"].isin(boroughs), "City"] = "New York"

        # get breakdown of cities in that state
        city_counts = state_data["City"].value_counts().reset_index()
        city_counts.columns = ["City", "Donor Count"]
        
        # group cities with less than 1% of donors together as "Other"
        threshold = city_counts["Donor Count"].sum() * 0.01
        city_counts["City_filtered"] = city_counts.apply(lambda row: row["City"] if row["Donor Count"] >= threshold else "Other", axis=1)

        # plot pie chart
        fig = px.pie(city_counts,
                     names="City_filtered",
                     values="Donor Count",
                     title=f"Percentage of Donors from Each City in {st.session_state.state}", 
                     color_discrete_sequence=px.colors.qualitative.Safe
                     )
        fig.update_traces(hovertemplate='%{label}: %{value} (%{percent})')
        st.plotly_chart(fig)
        st.caption("*Cities with less than 1% of the donors in their state are grouped into 'Other'.")

        ##### breakdown of nyc boroughs
        if st.session_state.state == "New York":
            nyc = state_data[state_data["Borough"].isin(boroughs)]
            borough_counts = nyc["Borough"].value_counts().reset_index()
            borough_counts.columns = ["Borough", "Donor Count"]
            fig = px.pie(borough_counts,
                     names="Borough",
                     values="Donor Count",
                     title="Percentage of Donors from Each Borough in New York City", 
                     color_discrete_sequence=px.colors.qualitative.Safe
                     )
            fig.update_traces(hovertemplate='%{label}: %{value} (%{percent})')
            st.plotly_chart(fig)

        ##### breakdown of donors who have no location
        st.subheader("Donors Without Location")
        st.write("**Country Only:** Donors whose city _and_ state are not included  \
                \n**No Location:** Donors with _no_ location information")
        no_location = stats_no_location(data)
        st.dataframe(no_location)

    elif st.session_state.active_tab == "Donors by Date":

        st.header("Donors by Date")

        ##### breakdown of donors by year
        st.space(size="small")
        st.subheader("Donors by Year")
        yearly = stats_by_year(data)
        st.bar_chart(yearly, x_label="Year", y_label="Donors", color="#007633")
        st.caption("*Donors indicates the number of donors whose last donation was made in that year.")

        ##### breakdown of donors by month
        st.space(size="small")
        st.subheader("Donors by Month")
        monthly = stats_by_month(data)
        st.bar_chart(monthly, x_label="Month", y_label="Donors", color="#007633", sort=False)
        st.caption("*Donors indicates the number of donors whose last donation was made in that month.")