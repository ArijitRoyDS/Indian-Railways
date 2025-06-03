import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import os
from search_by_train import search_by_train
from search_by_route import route_search_ui, build_timetable
from search_by_station import search_by_station_ui
from home import home_ui

st.set_page_config(page_title="Indian Railways", layout="wide", page_icon="🚊")

def get_train_labels(train_df):
    train_df = train_df.copy()
    train_df["label"] = train_df["trainNumber"].astype(str) + " - " + train_df["trainName"]
    train_labels = sorted(train_df["label"].tolist())
    label_to_number = dict(zip(train_df["label"], train_df["trainNumber"].astype(str)))
    return train_labels, label_to_number

@st.cache_data
def load_data():
    pwd = os.getcwd()
    train_df = pd.read_csv(f"{pwd}/database/train_schedule.csv", low_memory=False)
    station_df = pd.read_csv(f"{pwd}/database/station_index.csv", low_memory=False)
    station_df["label"] = station_df["stationCode"] + " - " + station_df["stationName"]
    return train_df, station_df

train_df, station_df = load_data()

col1, col2 = st.columns([2, 5])

col1.title("🚂 Indian Railways")

options=["Home", "Train No Search", "Trains Between Stations", "Trains At Station"]
icons=["house", "train-lightrail-front", "map", "geo"]
    
index = 0

with col2:
    st.write("")
    selected_tab = option_menu(
        menu_title=None,  # No title for the top-level menu
        options=options,
        icons=icons,
        menu_icon="cast",
        default_index=index,
        orientation="horizontal",
    )
st.write("__________")
st.write("")

if selected_tab == "Home":
    home_ui(train_df, station_df)

elif selected_tab == "Train No Search":
    search_by_train(train_df)

elif selected_tab == "Trains Between Stations":
    route_search_ui(train_df, station_df)

elif selected_tab == "Trains At Station":
    search_by_station_ui(train_df, station_df, build_timetable)
