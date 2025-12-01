import streamlit as st
import pandas as pd
import numpy as np
from data_analysis import *
import plotly.express as px
import sys
from pathlib import Path

st.set_page_config(
    page_title="Donor Analytics",
    page_icon="📊",
    layout="wide"
)

sys.path.insert(0, str(Path("../Vincent").resolve()))
import location

def run():

    # clean data
    bk_data = clean(st.session_state.df)

    # convert to biokind format

    tab1, tab2, tab3, tab4 = st.tabs([
            "Basic Statistics",
            "Top Donors",
            "Donors by Location",
            "Donors by Date"
        ])

    with tab1:
        st.markdown("<h2 style='text-align: center;'>Basic Statistics</h2>", unsafe_allow_html=True)
        st.space(size="medium")
       
        st.markdown("<h4 style='text-align: center;'>Basic Statistics for All Donors</h4>", unsafe_allow_html=True)
        st.write("**Donors:** Number of unique donors  \
                \n**Total Donation Amount:** Total donated among all donors  \
                \n**Average Total Donation:** Average total donation per donor  \
                \n**Median Total Donation:** Median total donation per donor  \
                \n**Modal Total Donation:** Modal total donation per donor")
        stats = basic_stats(data)
        st.dataframe(stats)
        st.space(size="small")

        st.markdown("<h4 style='text-align: center;'>Basic Statistics for Active Donors</h4>", unsafe_allow_html=True)
        st.write("**Active Donor:** Donor who has donated at least once within the past 18 months.")
        stats_active = active_donors(data)
        st.dataframe(stats_active)
        st.space(size="small")
        
        st.markdown("<h4 style='text-align: center;'>Basic Statistics for Inactive Donors</h4>", unsafe_allow_html=True)
        st.write("**Inactive Donor:** Donor who has not donated within the past 18 months.")
        stats_inactive = inactive_donors(data)
        st.dataframe(stats_inactive)

    with tab2:
        st.markdown("<h2 style='text-align: center;'>Top Donors</h2>", unsafe_allow_html=True)
        st.space(size="medium")
        
        st.markdown("<h4 style='text-align: center;'>Top 50 Donors by Total Amount Donated</h4>", unsafe_allow_html=True)
        top_amt = top_donors(data, 50)
        st.dataframe(top_amt)
        st.space(size="small")

        col1, empty, col2 = st.columns([3, 1, 3])
        
        with col1:
            top_amt["Status"] = top_amt["Number of Gifts Past 18 Months"].apply(lambda x: "Active" if x>0 else "Inactive")
            activity_counts = top_amt["Status"].value_counts()
            fig = px.pie(names=activity_counts.index, values=activity_counts.values, title="Active/Inactive Top Donors", color_discrete_sequence=px.colors.qualitative.Prism)
            st.plotly_chart(fig)

        with col2: 
            state_counts = top_amt["State"].value_counts()
            fig = px.pie(names=state_counts.index, values=state_counts.values, title="States of Top Donors", color_discrete_sequence=px.colors.qualitative.Prism)
            st.plotly_chart(fig)

        st.markdown("<h4 style='text-align: center;'>Top 50 Donors by Donation Frequency (Past 18 Months)</h4>", unsafe_allow_html=True)
        top_freq = frequent_donors(data, 50)
        st.dataframe(top_freq)

    with tab3:

        st.markdown("<h2 style='text-align: center;'>Donors by State and City</h2>", unsafe_allow_html=True)
        st.space(size="medium")

        st.markdown("<h4 style='text-align: center;'>Donors by State</h4>", unsafe_allow_html=True)
        st.write("**Cities:** Number of unique cities donated from in the state  \
                \n**Donors:** Number of unique donors in the state  \
                \n**Total Gifts (All Time):** Total donated from the state  \
                \n**Number of Gifts Past 18 Months:** Number of donations in the past 18 months from the state")
        
        states = stats_by_state(data)
        st.dataframe(states)
        st.space(size="small")

        # separating out states with .85% of donors from the rest for pie chart
        threshold = 0.0085
        states_pie = states[states["Donors"] / states["Donors"].sum() >= threshold]
        other_states = states[states["Donors"] / states["Donors"].sum() < threshold]
        other_total = other_states["Donors"].sum()
        states_pie.loc["Other"] = other_total

        # pie chart of states and donors
        fig = px.pie(states_pie, names=states_pie.index, values="Donors",  title="Percentage of Donors from Each State", color_discrete_sequence=px.colors.qualitative.Prism)
        st.plotly_chart(fig)

        st.markdown("<h4 style='text-align: center;'>Donors by City</h4>", unsafe_allow_html=True)
        st.write("**Donors:** Number of unique donors in the city  \
                \n**Total Gifts (All Time):** Total donated from the city  \
                \n**Number of Gifts Past 18 Months:** Number of donations in the past 18 months from the city")
        cities = stats_by_city(data)
        st.dataframe(cities)
        st.space(size="small")

        st.markdown("<h4 style='text-align: center;'>Donors Without Location</h4>", unsafe_allow_html=True)
        st.write("**Country Only:** Donors whose city _and_ state are not included  \
                \n**No Location:** Donors with _no_ location information")
        no_location = stats_no_location(data)
        st.dataframe(no_location)

    with tab4:
        st.markdown("<h2 style='text-align: center;'>Donors by Month and Year</h2>", unsafe_allow_html=True)
        st.space(size="medium")

        st.markdown("<h4 style='text-align: center;'>Donors by Year</h4>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Years and the number of donors whose last donation was in that year.</p>", unsafe_allow_html=True)
        yearly = stats_by_year(data)
        st.bar_chart(yearly, x_label="Year", y_label="Donors", color="#007633")

        st.space(size="small")
        st.markdown("<h4 style='text-align: center;'>Donors by Month</h4>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Months and the number of donors whose last donation was in that month.</p>", unsafe_allow_html=True)
        monthly = stats_by_month(data)
        st.bar_chart(monthly, x_label="Month", y_label="Donors", color="#007633", sort=False)