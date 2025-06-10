import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import os
from search_by_train import search_by_train
from search_by_route import route_search_ui, build_timetable
from search_by_station import search_by_station_ui
from search_by_train_unreserved import search_by_train_unreserved
from search_by_route_unreserved import route_search_ui_unreserved, build_timetable_unreserved
from search_by_station_unreserved import search_by_station_ui_unreserved
from home import home_ui
from home_reserved import home_ui_reserved
from home_unreserved import home_ui_unreserved
from pnr_status import check_pnr_status

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
    master_train_df = pd.read_csv(f"{pwd}/database/master_list.csv", low_memory=False)
    train_df = pd.read_csv(f"{pwd}/database/reserved_train_schedule.csv", low_memory=False)
    unreserved_train_df = pd.read_csv(f"{pwd}/database/unreserved_train_schedule.csv", low_memory=False)
    
    station_df = pd.read_csv(f"{pwd}/database/station_index_with_coords.csv", low_memory=False)
    station_df = station_df.drop_duplicates(subset="stationCode", keep="first")    
    station_df["stationCode"] = station_df["stationCode"].str.upper()
    station_df["stationName"] = station_df["stationName"].str.upper()
    station_df["label"] = station_df["stationCode"] + " - " + station_df["stationName"]

    return master_train_df, train_df, station_df, unreserved_train_df

master_train_df, train_df, station_df, unreserved_train_df = load_data()

col1, col2 = st.columns([2, 5])

col1.title("🚂 Indian Railways")

options=["Home", "Reserved Trains", "Unreserved Trains", "PNR Status"]
icons=["house", "train-lightrail-front", "train-front", "bookmark-check"]    
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


if selected_tab == "Home":
    st.write("__________")
    st.write("")
    home_ui(master_train_df, station_df)
 
elif selected_tab == "Reserved Trains":   
    options_reserved=["Home", "Train No Search", "Trains Between Stations", "Trains At Station"]
    icons_reserved=["house", "train-lightrail-front", "map", "geo"]
    
    selected_reserved_tab = option_menu(
        menu_title=None,  # No title for the top-level menu
        options=options_reserved,
        icons=icons_reserved,
        menu_icon="cast",
        default_index=index,
        orientation="horizontal",
    )
    
    if selected_reserved_tab == "Home":
        st.write("__________")
        st.write("")
        home_ui_reserved(master_train_df, station_df)

    elif selected_reserved_tab == "Train No Search":
        search_by_train(train_df)

    elif selected_reserved_tab == "Trains Between Stations":
        route_search_ui(train_df, station_df)

    elif selected_reserved_tab == "Trains At Station":
        search_by_station_ui(train_df, station_df, build_timetable)
    
elif selected_tab == "Unreserved Trains":
    options_unreserved=["Home", "Train No Search", "Trains Between Stations", "Trains At Station"]
    icons_unreserved=["house", "train-lightrail-front", "map", "geo"]
    
    selected_unreserved_tab = option_menu(
        menu_title=None,  # No title for the top-level menu
        options=options_unreserved,
        icons=icons_unreserved,
        menu_icon="cast",
        default_index=index,
        orientation="horizontal",
    )
    
    if selected_unreserved_tab == "Home":
        st.write("__________")
        st.write("")
        home_ui_unreserved(master_train_df, station_df)

    elif selected_unreserved_tab == "Train No Search":
        search_by_train_unreserved(unreserved_train_df)

    elif selected_unreserved_tab == "Trains Between Stations":
        route_search_ui_unreserved(unreserved_train_df, station_df)

    elif selected_unreserved_tab == "Trains At Station":
        search_by_station_ui_unreserved(unreserved_train_df, station_df, build_timetable)
        
if selected_tab == "PNR Status":
    check_pnr_status()