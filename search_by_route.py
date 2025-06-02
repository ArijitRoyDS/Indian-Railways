import streamlit as st
import pandas as pd
from datetime import datetime, timedelta


def parse_running_days(running_on: str) -> str:
    days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    return ', '.join(day for day, status in zip(days, running_on) if status == 'Y')


def build_timetable(row: pd.Series) -> pd.DataFrame:
    timetable = []
    fmt = "%H:%M"
    max_stations = 1000

    for i in range(1, max_stations):
        code = row.get(f"station{i}_code")
        if pd.isna(code):
            break
        name = row.get(f"station{i}_name")
        arr = row.get(f"station{i}_arr")
        dep = row.get(f"station{i}_dep")
        day = int(row.get(f"station{i}_day", 0)) if pd.notna(row.get(f"station{i}_day")) else 0
        cum_dist = int(row.get(f"station{i}_dist")) if pd.notna(row.get(f"station{i}_dist")) else None

        next_dist = row.get(f"station{i+1}_dist")
        dist = int(next_dist - cum_dist) if pd.notna(next_dist) and cum_dist is not None else None

        stop_time = "-"
        if pd.notna(arr) and pd.notna(dep) and arr != dep:
            try:
                arr_dt = datetime.strptime(arr, fmt)
                dep_dt = datetime.strptime(dep, fmt)
                if dep_dt < arr_dt:
                    dep_dt += timedelta(days=1)
                stop_minutes = int((dep_dt - arr_dt).total_seconds() // 60)
                stop_time = f"{stop_minutes} min"
            except Exception:
                pass

        journey_duration = "-"
        speed = "-"
        next_arr = row.get(f"station{i+1}_arr")
        if pd.notna(dep) and pd.notna(next_arr):
            try:
                dep_dt = datetime.strptime(dep, fmt) + timedelta(days=day)
                arr_day = int(row.get(f"station{i+1}_day", 0)) if pd.notna(row.get(f"station{i+1}_day")) else 0
                arr_dt = datetime.strptime(next_arr, fmt) + timedelta(days=arr_day)
                if arr_dt < dep_dt:
                    arr_dt += timedelta(days=1)
                delta_min = int((arr_dt - dep_dt).total_seconds() // 60)
                hrs, mins = divmod(delta_min, 60)
                journey_duration = f"{hrs}h {mins}m"
                if dist is not None and delta_min > 0:
                    speed = int(dist / (delta_min / 60))
            except Exception:
                pass

        timetable.append({
            "Station Code": code,
            "Station Name": name,
            "Arrival Time": arr,
            "Departure Time": dep,
            "Day": day,
            "Stoppage Duration": stop_time,
            "Distance": str(cum_dist),
            "Duration to Next Stn": journey_duration,
            "Distance to Next Stn": str(dist) if dist is not None else "-",
            "Speed (km/h)": speed,
        })

    return pd.DataFrame(timetable)


def find_matching_trains(train_df, from_code, to_code):
    matches = []
    fmt = "%H:%M"

    for _, row in train_df.iterrows():
        stations = [
            str(row.get(f"station{i}_code", ""))
            for i in range(1, 100)
            if pd.notna(row.get(f"station{i}_code"))
        ]

        if from_code in stations and to_code in stations:
            from_idx = stations.index(from_code)
            to_idx = stations.index(to_code)
            if from_idx < to_idx:
                dep_origin = row.get(f"station{from_idx + 1}_dep", "")
                arr_dest = row.get(f"station{to_idx + 1}_arr", "")
                dep_day = int(row.get(f"station{from_idx + 1}_day", 0))
                arr_day = int(row.get(f"station{to_idx + 1}_day", 0))

                total_duration = "-"
                total_distance = "-"
                average_speed = "-"

                try:
                    dep_dt = datetime.strptime(dep_origin, fmt) + timedelta(days=dep_day)
                    arr_dt = datetime.strptime(arr_dest, fmt) + timedelta(days=arr_day)
                    if arr_dt < dep_dt:
                        arr_dt += timedelta(days=1)

                    total_minutes = int((arr_dt - dep_dt).total_seconds() // 60)
                    hrs, mins = divmod(total_minutes, 60)
                    total_duration = f"{hrs}h {mins}m"

                    from_dist = row.get(f"station{from_idx + 1}_dist")
                    to_dist = row.get(f"station{to_idx + 1}_dist")
                    if pd.notna(from_dist) and pd.notna(to_dist):
                        total_distance = int(to_dist - from_dist)
                        if total_minutes > 0:
                            average_speed = int(total_distance / (total_minutes / 60))
                except Exception:
                    pass

                matches.append({
                    "Train No": str(row["trainNumber"]).replace(",", ""),
                    "Train Name": row["trainName"],
                    "Origin": f"{stations[0]} - {row.get('station1_name', '')}",
                    "Destination": f"{stations[-1]} - {row.get(f'station{len(stations)}_name', '')}",
                    "Running On": parse_running_days(row["runningOn"]),
                    "Train Type": row["train_type"],
                    "Classes": row["journeyClasses"],
                    f"Departure ({from_code})": dep_origin,
                    f"Arrival ({to_code})": arr_dest,
                    "Duration": total_duration,
                    "Distance (km)": total_distance,
                    "Avg Speed (km/h)": average_speed,
                })

    return pd.DataFrame(matches)


def route_search_ui(train_df, station_df):
    label_to_code = dict(zip(station_df["label"], station_df["stationCode"]))
    station_labels = sorted(station_df["label"].tolist())

    st.subheader("🔍 Search by Route")
    col1, col2 = st.columns(2)
    from_label = col1.selectbox("From Station", [None] + station_labels)
    to_label = col2.selectbox("To Station", [None] + station_labels)

    if from_label and to_label:
        from_code = label_to_code[from_label]
        to_code = label_to_code[to_label]

        if from_code == to_code:
            st.warning("Source and destination cannot be the same.")
            return

        result_df = find_matching_trains(train_df, from_code, to_code)

        if result_df.empty:
            st.warning("No matching trains found.")
            return

        # Reset index to avoid index conflicts and control column order
        result_df = result_df.copy().reset_index(drop=True)

        # Insert 'Select' column as the FIRST column
        result_df.insert(0, "Select", False)

        # Display editable table with Select column first
        edited_df = st.data_editor(
            result_df,
            use_container_width=True,
            hide_index=True,
            key="route_train_selector",
            column_config={"Select": st.column_config.CheckboxColumn("Select")},
            disabled=[col for col in result_df.columns if col != "Select"],
            num_rows="fixed"  # prevents adding new rows
        )

        # Detect the selected train (only one allowed)
        selected_rows = edited_df[edited_df["Select"] == True]

        if len(selected_rows) > 1:
            st.warning("Please select only one train.")
        elif len(selected_rows) == 1:
            selected_train_no = selected_rows.iloc[0]["Train No"]
            row = train_df[train_df["trainNumber"].astype(str) == str(selected_train_no)].iloc[0]
            st.write(f"### 📍 Full Time Table for Train {row['trainNumber']} - {row['trainName']}")
            timetable_df = build_timetable(row)
            st.dataframe(timetable_df)