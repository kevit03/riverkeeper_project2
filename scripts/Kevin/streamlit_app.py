import streamlit as st
from streamlit_folium import st_folium

# Import your map builder function from your main script
# Change "heatmap" to whatever your file is named WITHOUT .py
from heatmap import build_map  


st.set_page_config(
    page_title="Donor Map Test",
    layout="wide"
)

st.title("Donor Map Viewer")

st.write("Below is your interactive donor map. Zoom in to inspect markers. Popups show donor counts when clicked.")


# Build your folium map
try:
    folium_map = build_map()
except Exception as e:
    st.error(f"Error creating map: {e}")
    st.stop()


# Render folium map inside Streamlit
st_folium(
    folium_map,
    width=1500,
    height=900
)
