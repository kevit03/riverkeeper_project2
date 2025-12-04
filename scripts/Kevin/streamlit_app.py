import streamlit as st
from streamlit_folium import st_folium
import copy

# Import your custom Folium map builder
from heatmap import build_map  


# page setup 
st.set_page_config(
    page_title="Donor Map Visualizer",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for aesthetics
st.markdown("""
<style>
    /* Main background */
    .main {
        background-color: #f9fafb;
        font-family: 'Inter', sans-serif;
    }

    /* Center title */
    h1 {
        text-align: center;
        font-weight: 700;
        margin-top: 10px;
        color: #1e3a8a;
    }

    /* Subheader */
    .subheader {
        text-align: center;
        color: #475569;
        font-size: 17px;
        margin-bottom: 20px;
    }

    /* Map container */
    .map-container {
        background-color: white;
        padding: 20px;
        border-radius: 14px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.1);
        margin-top: 20px;
        margin-bottom: 40px;
        border: 1px solid #e5e7eb;
    }

    /* Footer */
    .footer {
        text-align: center;
        margin-top: 20px;
        color: #94a3b8;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)


#header
st.markdown("<h1>Donor Map Viewer</h1>", unsafe_allow_html=True)
st.markdown("<div class='subheader'>A geographic visualization of donor locations</div>", unsafe_allow_html=True)

#map display
try:
    folium_map = build_map()
except Exception as e:
    st.error(f"Error loading map: {e}")
    st.stop()


st.markdown("<div class='map-container'>", unsafe_allow_html=True)

st_folium(
    copy.deepcopy(folium_map),
    width=1500,
    height=900
)

st.markdown("</div>", unsafe_allow_html=True)


st.markdown("<div class='footer'>Map generated automatically using geospatial data</div>", unsafe_allow_html=True)

#export PATH="$HOME/Library/Python/3.9/bin:$PATH"
