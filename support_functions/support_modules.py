import streamlit as st
import pandas as pd
import plotly.express as px
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from time import sleep
import os

def map_plot(df):
    @st.cache_data(show_spinner=False)
    def get_or_geocode_stations(stations):
        # Load known coordinates
        coord_file = os.path.join(os.getcwd(), "database/station_index_with_coords.csv")
        if os.path.exists(coord_file):
            coord_df = pd.read_csv(coord_file)
        else:
            coord_df = pd.DataFrame(columns=["stationCode", "stationName", "Latitude", "Longitude"])

        geolocator = Nominatim(user_agent="streamlit-train-route")
        results = []
        updated = False

        for stn in stations:
            # Try matching on name
            matched = coord_df[coord_df["stationName"].str.upper().str.strip() == stn.upper().strip()]
            if not matched.empty and pd.notna(matched.iloc[0]["Latitude"]) and pd.notna(matched.iloc[0]["Longitude"]):
                lat, lon = matched.iloc[0]["Latitude"], matched.iloc[0]["Longitude"]
                results.append((stn, lat, lon))
                continue

            # Otherwise, try to geocode
            station = stn.upper().split("JN")[0].split("JUNCTION")[0].strip()
            query = f"{station} Railway Station, India"
            try:
                location = geolocator.geocode(query, timeout=10)
                if location:
                    lat, lon = location.latitude, location.longitude
                    if 6 <= lat <= 38 and 68 <= lon <= 97:
                        results.append((stn, lat, lon))
                        # Add new to coord_df
                        new_entry = pd.DataFrame([{
                            "stationCode": None,
                            "stationName": stn,
                            "Latitude": lat,
                            "Longitude": lon
                        }])
                        coord_df = pd.concat([coord_df, new_entry], ignore_index=True)
                        updated = True
                    else:
                        st.warning(f"⚠️ {station} geocoded outside India: ({lat}, {lon})")
            except Exception:
                pass
            sleep(1)

        # Save new coordinates if added
        if updated:
            coord_df.drop_duplicates(subset="stationName", inplace=True)
            coord_df.to_csv(coord_file, index=False)
            st.success("💾 Updated station_index_with_coords.csv with new coordinates.")

        return pd.DataFrame(results, columns=["Station Name", "Latitude", "Longitude"])

    station_names = df["Station Name"].dropna().unique().tolist()
    geo_df = get_or_geocode_stations(station_names)

    if geo_df.empty:
        st.error("No valid station coordinates found.")
        return

    # Filter out jumps > 400 km
    filtered_points = [geo_df.iloc[0]]
    for i in range(1, len(geo_df)):
        prev = (filtered_points[-1]["Latitude"], filtered_points[-1]["Longitude"])
        curr = (geo_df.iloc[i]["Latitude"], geo_df.iloc[i]["Longitude"])
        distance_km = geodesic(prev, curr).km
        if distance_km <= 400:
            filtered_points.append(geo_df.iloc[i])

    geo_df = pd.DataFrame(filtered_points)

    center_lat = geo_df["Latitude"].mean()
    center_lon = geo_df["Longitude"].mean()

    fig = px.scatter_mapbox(
        geo_df,
        lat="Latitude",
        lon="Longitude",
        hover_name="Station Name",
        mapbox_style="carto-positron",
        height=400,
        width=600,
        zoom=5
    )

    fig.add_scattermapbox(
        lat=geo_df["Latitude"],
        lon=geo_df["Longitude"],
        mode="lines+markers",
        line=dict(color="blue", width=4),
        marker=dict(size=10),
        text=geo_df["Station Name"],
        hoverinfo="text",
        name="Train Route"
    )

    fig.update_layout(
        mapbox=dict(center={"lat": center_lat, "lon": center_lon}),
        margin=dict(l=0, r=0, t=0, b=0)
    )

    st.plotly_chart(fig, use_container_width=True)
