import streamlit as st
import plotly.express as px
import pandas as pd
from config import train_type_lookup


def is_superfast(train_number: str) -> bool:
    """Check if a train number qualifies as superfast."""
    if len(train_number) >= 1 and train_number[0] == "2":
        return True
    if len(train_number) >= 2 and train_number[0] in "012" and train_number[1] == "2":
        return True
    return False


def generate_bar_chart(df: pd.DataFrame, group_col: str, label: str):
    """Create vertical bar chart with longest bar on the left and unique colors."""
    group = df.groupby(group_col).agg({
        "Train No": lambda x: list(x)
    }).reset_index()
    group["Count"] = group["Train No"].apply(len)
    group = group[[group_col, "Count", "Train No"]]
    group = group.sort_values("Count", ascending=False)

    fig = px.bar(
        group,
        x=group_col,
        y="Count",
        color=group_col,  # Unique color per bar
        title=f"Train Count by {label}",
        text="Count",
        height=650,
        width=600
    )

    fig.update_layout(
        xaxis=dict(
            title=label,
            categoryorder="total descending"  # Longest bar first (left)
        ),
        yaxis=dict(title="Train Count"),
        showlegend=True
    )
    fig.update_traces(textposition="outside")

    col1, dummy, col2 = st.columns([4, 0.3, 2])
    col1.plotly_chart(fig, use_container_width=True)
    col2.dataframe(
        group.rename(columns={
            "Train No": "List of Train Nos",
            group_col: label
        }),
        use_container_width=True,
        hide_index=True
    )




def home_ui_unreserved(master_train_df: pd.DataFrame, station_df: pd.DataFrame):
    st.subheader("🏠 Overview Metrics")
    
    master_train_df["Train No"] = master_train_df["Train No"].apply(lambda x: int(float(x)))
    master_train_df = master_train_df[(master_train_df["Train No"] >= 30000) & (master_train_df["Train No"] <= 59999)]
    master_train_df = master_train_df.reset_index(drop=True)

    # Basic metrics
    num_trains = master_train_df["Train No"].nunique()
    num_stations = station_df["stationCode"].nunique()
    num_zones = master_train_df["Zone"].nunique()
    num_train_types = master_train_df["Train Type"].nunique()
    num_superfast = master_train_df["Train No"].astype(str).apply(is_superfast).sum()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Trains", num_trains)
    col2.metric("Stations", num_stations)
    col3.metric("Superfast Trains", num_superfast)
    col4.metric("Zones", num_zones)
    col5.metric("Train Types", num_train_types)

    # Ensure required columns exist
    required_cols = {"Train No", "Train Type", "Zone"}
    if not required_cols.issubset(master_train_df.columns):
        st.error("Uploaded file must contain columns: 'Train No', 'Train Type', 'Zone'")
        st.stop()

    # Map full train type names using lookup
    master_train_df["Train-Type"] = master_train_df["Train Type"].map(train_type_lookup).fillna(master_train_df["Train Type"])

    st.markdown("---")
    st.subheader("🚉 Train Distribution by Train Type")
    generate_bar_chart(master_train_df, "Train-Type", "Train Type")

    st.markdown("---")
    st.subheader("🗺️ Train Distribution by Zone")
    generate_bar_chart(master_train_df, "Zone", "Zone")
