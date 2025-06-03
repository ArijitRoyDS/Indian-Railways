import streamlit as st
import plotly.express as px
import pandas as pd

def home_ui(train_df, station_df):
    st.subheader("🏠 Overview Metrics")

    num_trains = train_df["trainNumber"].nunique()
    num_stations = station_df["stationCode"].nunique()

    train_numbers_str = train_df["trainNumber"].astype(str)

    def is_superfast(tn):
        if len(tn) >= 1 and tn[0] == "2":
            return True
        if len(tn) >= 2 and tn[0] in "012" and tn[1] == "2":
            return True
        return False

    num_superfast = train_numbers_str.apply(is_superfast).sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Number of Trains", num_trains)
    col2.metric("Number of Stations", num_stations)
    col3.metric("Number of Superfast Trains", num_superfast)
    
    st.write("______")

    # Zone code logic
    zone_code_map = {
        "0": "Konkan",
        "1": "CR/WCR/NCR",
        "2": "Superfast (zone from 3rd digit)",
        "3": "ER/ECR",
        "4": "NR/NCR/NWR",
        "5": "NER/NFR",
        "6": "SR/SWR",
        "7": "SCR/SWR",
        "8": "SER/ECoR",
        "9": "WR/NWR/WCR"
    }

    def resolve_zone(tn):
        if len(tn) < 2 or tn[0] not in "012":
            return "Other / Suburban"
        if tn[1] == "2":
            if len(tn) > 2:
                return zone_code_map.get(tn[2], "Unknown (Superfast)")
            else:
                return "Unknown (Superfast)"
        return zone_code_map.get(tn[1], "Unknown")

    train_df["Zone"] = train_numbers_str.apply(resolve_zone)

    # Group data
    grouped = train_df.groupby("Zone").agg(
        Count=("trainNumber", "count"),
        TrainNumbers=("trainNumber", lambda x: ", ".join(sorted(map(str, x))))
    ).reset_index()

    # Layout: Pie chart + Data table side-by-side
    st.subheader("🧭 Zone-wise Distribution of Trains")
    col1, col2 = st.columns([1, 1.5])  # Wider column for table

    with col1:
        fig = px.pie(grouped, names="Zone", values="Count", title="Train Count per Zone")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.dataframe(grouped, use_container_width=True)
