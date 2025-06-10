# import streamlit as st
# import pandas as pd
# import plotly.express as px
# from geopy.geocoders import Nominatim
# from geopy.distance import geodesic
# from time import sleep
# import os

# def map_plot(df):
#     @st.cache_data(show_spinner=False)
#     def get_or_geocode_stations(stations):
#         coord_file = os.path.join(os.getcwd(), "database/station_index_with_coords.csv")
#         if os.path.exists(coord_file):
#             coord_df = pd.read_csv(coord_file)
#         else:
#             coord_df = pd.DataFrame(columns=["stationCode", "stationName", "Latitude", "Longitude"])

#         geolocator = Nominatim(user_agent="streamlit-train-route")
#         results = []
#         updated = False

#         for stn in stations:
#             matched = coord_df[coord_df["stationName"].str.upper().str.strip() == stn.upper().strip()]
#             if not matched.empty and pd.notna(matched.iloc[0]["Latitude"]) and pd.notna(matched.iloc[0]["Longitude"]):
#                 lat, lon = matched.iloc[0]["Latitude"], matched.iloc[0]["Longitude"]
#                 results.append((stn, lat, lon))
#                 continue

#             station = (
#                 stn.upper()
#                 .replace("JN", "")
#                 .replace("JN.", "")
#                 .replace("JUNCTION", "")
#                 .replace("RAILWAY STATION", "")
#                 .replace("CANT", "")
#                 .replace("CANTT", "")
#                 .replace("CNT", "")
#                 .replace("CTRL", "")
#                 .replace("CTL", "")
#                 .replace("CITY", "")
#                 .replace("CTY", "")
#                 .replace("TOWN", "")
#                 .strip()
#             )
#             query = f"{station} Railway Station, India"
#             try:
#                 location = geolocator.geocode(query, timeout=10)
#                 if location:
#                     lat, lon = location.latitude, location.longitude
#                     if 6 <= lat <= 38 and 68 <= lon <= 97:
#                         results.append((stn, lat, lon))
#                         new_entry = pd.DataFrame([{
#                             "stationCode": None,
#                             "stationName": stn,
#                             "Latitude": lat,
#                             "Longitude": lon
#                         }])
#                         coord_df = pd.concat([coord_df, new_entry], ignore_index=True)
#                         updated = True
#                     else:
#                         st.warning(f"⚠️ {station} geocoded outside India: ({lat}, {lon})")
#             except Exception:
#                 pass
#             sleep(1)

#         if updated:
#             coord_df.drop_duplicates(subset="stationName", inplace=True)
#             coord_df.to_csv(coord_file, index=False)
#             st.success("💾 Updated station_index_with_coords.csv with new coordinates.")

#         return pd.DataFrame(results, columns=["Station Name", "Latitude", "Longitude"])

#     station_names = df["Station Name"].dropna().unique().tolist()
#     geo_df = get_or_geocode_stations(station_names)

#     if len(geo_df) < 2:
#         st.warning("Not enough stations to draw a route.")
#         return

#     # --- FIXED FILTERING LOGIC ---
#     filtered_points = [geo_df.iloc[0]]  # Always include first
#     last_valid_point = geo_df.iloc[0]

#     for i in range(1, len(geo_df) - 1):  # Only intermediate stations
#         curr_point = geo_df.iloc[i]
#         distance_km = geodesic(
#             (last_valid_point["Latitude"], last_valid_point["Longitude"]),
#             (curr_point["Latitude"], curr_point["Longitude"])
#         ).km
#         if distance_km <= 500:
#             filtered_points.append(curr_point)
#             last_valid_point = curr_point
#         else:
#             st.info(f"⛔ Skipped {curr_point['Station Name']} due to jump > 500 km ({distance_km:.1f} km)")

#     # Always include the last point, even if jump is large
#     last_point = geo_df.iloc[-1]
#     filtered_points.append(last_point)

#     geo_df = pd.DataFrame(filtered_points).reset_index(drop=True)
#     # --- END OF FILTERING LOGIC ---

#     center_lat = geo_df["Latitude"].mean()
#     center_lon = geo_df["Longitude"].mean()

#     fig = px.scatter_mapbox(
#         geo_df,
#         lat="Latitude",
#         lon="Longitude",
#         hover_name="Station Name",
#         mapbox_style="carto-positron",
#         height=400,
#         width=600,
#         zoom=5
#     )

#     fig.add_scattermapbox(
#         lat=geo_df["Latitude"],
#         lon=geo_df["Longitude"],
#         mode="lines+markers",
#         line=dict(color="blue", width=4),
#         marker=dict(size=10),
#         text=geo_df["Station Name"],
#         hoverinfo="text",
#         name="Train Route"
#     )

#     fig.update_layout(
#         mapbox=dict(center={"lat": center_lat, "lon": center_lon}),
#         margin=dict(l=0, r=0, t=0, b=0)
#     )

#     st.plotly_chart(fig, use_container_width=True)

import streamlit as st
import pandas as pd
import plotly.express as px
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from time import sleep
import os


def normalize_station_name(name: str) -> str:
    """Normalize station names to improve matching."""
    return (
        str(name)
        .upper()
        .strip()
        .replace("\u200b", "")
        .replace("\xa0", "")
        .replace("JN", "")
        .replace("JUNCTION", "")
        .replace("RAILWAY STATION", "")        
        .replace("CANTT", "")
        .replace("CANT", "")
        .replace("CNT", "")
        .replace("CTRL", "")
        .replace("CTL", "")
        .replace("CITY", "")
        .replace("CTY", "")
        .replace("TOWN", "")
        .strip()
    )


def map_plot(df):
    @st.cache_data(show_spinner=False)
    def get_or_geocode_stations(stations):
        coord_file = os.path.join(os.getcwd(), "database/station_index_with_coords.csv")

        if os.path.exists(coord_file):
            coord_df = pd.read_csv(coord_file)
        else:
            coord_df = pd.DataFrame(columns=["stationCode", "stationName", "Latitude", "Longitude"])

        geolocator = Nominatim(user_agent="streamlit-train-route")
        results = []
        updated = False

        # Normalize existing station names
        coord_df["__norm"] = coord_df["stationName"].apply(normalize_station_name)

        for stn in stations:
            normalized = normalize_station_name(stn)

            matched = coord_df[coord_df["__norm"] == normalized]
            if not matched.empty and pd.notna(matched.iloc[0]["Latitude"]) and pd.notna(matched.iloc[0]["Longitude"]):
                lat, lon = matched.iloc[0]["Latitude"], matched.iloc[0]["Longitude"]
                results.append((stn, lat, lon))
                continue

            # Try geocoding if not matched
            query = f"{normalized} Railway Station, India"
            try:
                location = geolocator.geocode(query, timeout=10)
                if location:
                    lat, lon = location.latitude, location.longitude
                    if 6 <= lat <= 38 and 68 <= lon <= 97:
                        results.append((stn, lat, lon))
                        # Add to coord_df
                        new_entry = pd.DataFrame([{
                            "stationCode": None,
                            "stationName": stn,
                            "Latitude": lat,
                            "Longitude": lon
                        }])
                        coord_df = pd.concat([coord_df, new_entry], ignore_index=True)
                        updated = True
                    else:
                        st.warning(f"⚠️ {stn} geocoded outside India: ({lat}, {lon})")
            except Exception:
                pass
            sleep(1)

        # Save if updated
        if updated:
            coord_df.drop(columns="__norm", errors="ignore", inplace=True)
            coord_df.drop_duplicates(subset="stationName", inplace=True)
            coord_df.to_csv(coord_file, index=False)
            st.success("💾 Updated station_index_with_coords.csv with new coordinates.")

        return pd.DataFrame(results, columns=["Station Name", "Latitude", "Longitude"])

    # Begin plotting logic
    station_names = df["Station Name"].dropna().unique().tolist()
    geo_df = get_or_geocode_stations(station_names)

    if len(geo_df) < 2:
        st.warning("Not enough stations to draw a route.")
        return

    # Normalize names before plotting
    geo_df["Station Name"] = geo_df["Station Name"].apply(normalize_station_name)

    # Filter out jumps > 500 km, but keep first and last always
    filtered_points = [geo_df.iloc[0]]
    for i in range(1, len(geo_df) - 1):
        prev = (filtered_points[-1]["Latitude"], filtered_points[-1]["Longitude"])
        curr = (geo_df.iloc[i]["Latitude"], geo_df.iloc[i]["Longitude"])
        distance_km = geodesic(prev, curr).km
        if distance_km <= 500:
            filtered_points.append(geo_df.iloc[i])

    if len(geo_df) > 1:
        filtered_points.append(geo_df.iloc[-1])  # Always include last station

    geo_df = pd.DataFrame(filtered_points)

    # Calculate map center
    min_lat, max_lat = geo_df["Latitude"].min(), geo_df["Latitude"].max()
    min_lon, max_lon = geo_df["Longitude"].min(), geo_df["Longitude"].max()
    center_lat = (min_lat + max_lat) / 2
    center_lon = (min_lon + max_lon) / 2

    # Estimate zoom based on bounds (empirical formula)
    lat_range = max_lat - min_lat
    lon_range = max_lon - min_lon
    max_range = max(lat_range, lon_range)

    # A rough mapping from range to zoom level (empirically tuned)
    if max_range < 0.1:
        zoom = 12
    elif max_range < 0.5:
        zoom = 9.5
    elif max_range < 1:
        zoom = 8.5
    elif max_range < 2:
        zoom = 7.5
    elif max_range < 4:
        zoom = 6.5
    elif max_range < 6:
        zoom = 5.5
    elif max_range < 10:
        zoom = 4.5
    elif max_range < 20:
        zoom = 3.5
    elif max_range < 40:
        zoom = 3
    elif max_range < 80:
        zoom = 2
    else:
        zoom = 1
        
    # st.write(zoom)

    fig = px.scatter_mapbox(
        geo_df,
        lat="Latitude",
        lon="Longitude",
        hover_name="Station Name",
        mapbox_style="carto-positron",
        height=400,
        width=600,
        zoom=zoom
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
        mapbox=dict(center={"lat": center_lat, "lon": center_lon}, zoom=zoom),
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)
