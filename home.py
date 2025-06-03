import streamlit as st

def home_ui(train_df, station_df):
    st.subheader("🏠 Overview Metrics")
    num_trains = train_df["trainNumber"].nunique()
    num_stations = station_df["stationCode"].nunique()
    
    train_numbers_str = train_df["trainNumber"].astype(str)
    
    def is_superfast(tn):
        if len(tn) >= 1 and tn[0] == "2":
            return True
        if len(tn) >= 2 and int(tn[0]) <= 2 and tn[1] == "2":
            return True
        return False
    
    num_superfast = train_numbers_str.apply(is_superfast).sum()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Number of Trains", num_trains)
    col2.metric("Number of Stations", num_stations)
    col3.metric("Number of Superfast Trains", num_superfast)
