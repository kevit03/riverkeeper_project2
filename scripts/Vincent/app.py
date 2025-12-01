### DEPRECATED FOR THE TIME BEING

import streamlit as st
import pandas as pd
import time
import location as locate

st.title("Welcome to the Location Cache.")

action_item=    """ 
    Here, you can upload your file of donors and their respective
    locations. We'll handle the rest from there: updating the
    database and interactive maps as needed. 👌
    """

def stream_data():
    for word in action_item.split(" "):
        yield word + " "
        time.sleep(0.035)

st.write_stream(stream_data)

uploaded_file = st.file_uploader("Upload data here")

if uploaded_file is not None:
    try:
        # check to make sure it's a proper csv file
        df = pd.read_csv(uploaded_file)

        # print out the csv file back to the user so they can self verify they uploaded the right file
        st.write(df)

        # DONE: validate proper Columns when they upload csv
        # TODO: when given a RK formatted csv, create a BK formatted csv and save it for ourselves, DO NOT SHOW IT TO THEM
        # TODO: make sure cached locations are updated and run photon API on uncached locations in the moment

        # begin runnign algorithm by first generating queries from the uploaded_file and then running them
        addressList = locate.generate_queries(uploaded_file, "RiverKeeper_Donors_Unique_Locations.csv")
        if addressList != None:
            locate.run_queries(addressList[0:60])
        else:
           st.markdown("All the locations in this file has been cached!")

    except:
        st.markdown("This isn't a csv file. Please upload a csv file.")
    

if st.button("Party Time! 🎈 "):
    st.balloons()
