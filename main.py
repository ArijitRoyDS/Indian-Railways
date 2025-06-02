import streamlit as st
import pandas as pd
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
    train_df = pd.read_csv("database/train_schedule.csv")
    station_df = pd.read_csv("database/station_index.csv")
    station_df["label"] = station_df["stationCode"] + " - " + station_df["stationName"]
    return train_df, station_df


train_df, station_df = load_data()

st.title("🚂 Indian Railways")
st.write("_________")

tab_home, tab1, tab2, tab3 = st.tabs([
    "🏠 Home",
    "🔢 **Search by Train Number/Name**", 
    "🗺️ **Search by Source & Destination**",
    "📍 **Search by Station**"
])

with tab_home:
    home_ui(train_df, station_df)

with tab1:
    search_by_train(train_df)

with tab2:
    route_search_ui(train_df, station_df)

with tab3:
    search_by_station_ui(train_df, station_df, build_timetable)