import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from support_functions.support_modules import map_plot


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
        stations = []
        for i in range(1, 100):
            code = row.get(f"station{i}_code")
            if pd.isna(code):
                break
            stations.append(str(code))


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
                    "Distance (km)": int(total_distance) if total_distance != "-" else "-",
                    "Avg Speed (km/h)": int(average_speed) if average_speed != "-" else "-",
                })

    return pd.DataFrame(matches)


def route_search_ui(train_df, station_df):
    ss = st.session_state
    label_to_code = dict(zip(station_df["label"], station_df["stationCode"]))
    # station_labels = sorted(station_df["label"].tolist())
    station_labels = sorted([
        str(label) for label in station_df["label"].tolist() if pd.notnull(label)
    ])


    st.subheader("🔍 Search by Route")
    con = st.container(border=True)
    col1, col_swap, col2 = con.columns([2, 0.5, 2])

    # Initialize session state keys only if not present
    if "from_station" not in ss:
        ss["from_station"] = None
    if "to_station" not in ss:
        ss["to_station"] = None
    if "search_triggered" not in ss:
        ss["search_triggered"] = False

    # Swap and Reset buttons centered in col_swap
    with col_swap:
        inner_left, inner_mid, inner_right = st.columns([1, 2, 1])
        with inner_mid:
            swap_clicked = st.button("🔁 Swap", key="swap_button")
            reset_clicked = st.button("🧹 Reset", key="reset_button")

            if swap_clicked:
                if ss.from_station and ss.to_station:
                    ss.from_station, ss.to_station = ss.to_station, ss.from_station
                    ss.search_triggered = True
                    st.rerun()

            if reset_clicked:
                ss.from_station = None
                ss.to_station = None
                ss.search_triggered = False
                st.rerun()

    # From Station Selectbox
    from_options = [None] + station_labels
    from_index = from_options.index(ss.from_station) if ss.from_station in from_options else 0
    col1.selectbox(
        "**From Station**",
        from_options,
        index=from_index,
        key="from_station"
    )

    # To Station Selectbox (exclude selected From Station)
    to_options = [label for label in station_labels if label != ss.from_station]
    if ss.to_station not in to_options:
        if ss.to_station is not None:
            ss.to_station = None
            st.rerun()
    to_options = [None] + to_options
    to_index = to_options.index(ss.to_station) if ss.to_station in to_options else 0
    col2.selectbox(
        "**To Station**",
        to_options,
        index=to_index,
        key="to_station"
    )

    # Auto-submit once both stations selected and search not triggered yet
    if ss.from_station and ss.to_station and not ss.search_triggered:
        ss.search_triggered = True
        st.rerun()

    # Validation before search
    if not (ss.from_station and ss.to_station and ss.search_triggered):
        con.info("Please select both From and To stations.")
        return

    from_code = label_to_code[ss.from_station]
    to_code = label_to_code[ss.to_station]

    if from_code == to_code:
        con.warning("Source and destination cannot be the same.")
        return

    # === Train Search ===
    result_df = find_matching_trains(train_df, from_code, to_code)

    # === Filters ===
    st.write("")
    col11, _, col12 = con.columns([2, 0.5, 2])

    col11.markdown("### 🗓️ Filter by Running Days")
    day_options = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Daily"]
    day_cols = col11.columns(len(day_options))
    selected_days = [day for i, day in enumerate(day_options) if day_cols[i].checkbox(day, key=f"day_{day}")]

    if selected_days:
        if "Daily" in selected_days:
            result_df = result_df[result_df["Running On"].str.count(",") == 6]
        else:
            filtered_parts = [result_df[result_df["Running On"].str.contains(day)] for day in selected_days if day != "Daily"]
            if filtered_parts:
                result_df = pd.concat(filtered_parts).drop_duplicates()
            else:
                result_df = result_df[0:0]

    col12.markdown("### 🛏️ Filter by Available Classes")
    static_classes = ["1A", "2A", "3A", "3E", "CC", "SL", "FC", "EV", "2S"]
    class_cols = col12.columns(len(static_classes))
    selected_classes = [cls for i, cls in enumerate(static_classes) if class_cols[i].checkbox(cls, key=f"class_{cls}")]

    if selected_classes:
        def has_any_selected_class(classes_str):
            train_classes = [cls.strip().upper() for cls in str(classes_str).split(",")]
            return any(cls in train_classes for cls in selected_classes)

        result_df = result_df[result_df["Classes"].apply(has_any_selected_class)]

    if result_df.empty:
        st.warning("No matching trains found.")
        return

    result_df = result_df.copy().reset_index(drop=True)
    result_df.insert(0, "Select", False)

    st.subheader("List of trains")
    edited_df = st.data_editor(
        result_df,
        use_container_width=True,
        hide_index=True,
        key="route_train_selector",
        column_config={"Select": st.column_config.CheckboxColumn("Select")},
        disabled=[col for col in result_df.columns if col != "Select"],
        num_rows="fixed"
    )

    selected_rows = edited_df[edited_df["Select"] == True]
    if len(selected_rows) > 1:
        st.warning("Please select only one train.")
    elif len(selected_rows) == 1:
        selected_train_no = selected_rows.iloc[0]["Train No"]
        row = train_df[train_df["trainNumber"].astype(str) == str(selected_train_no)].iloc[0]

        df = build_timetable(row)
        col_left, col_right = st.columns([4, 2])
        with col_left:
            st.subheader(f"Full Time Table for Train No: {row['trainNumber']} - {row['trainName']}")
            st.dataframe(df)
        with col_right:
            st.subheader("Route Map (Beta)")
            if st.button("Show Map"):
                map_plot(df)
