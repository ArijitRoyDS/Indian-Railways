import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def parse_running_days(running_on: str) -> str:
    days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    return ', '.join(day for day, status in zip(days, running_on) if status == 'Y')

def search_by_station_ui(train_df, station_df, build_timetable):
    st.subheader("📍 Find Trains Passing Through a Station")
    con1 = st.container(border=True)

    stations_with_none = ["None"] + sorted(station_df["label"].tolist())
    selected_station = con1.selectbox("**Select a station**", stations_with_none, index=0)

    # Filter trains passing through selected station code
    if selected_station == "None":
        matching_trains_df = train_df.copy()
    else:
        station_code = selected_station.split(" - ")[0]
        station_code_cols = [col for col in train_df.columns if col.endswith("_code")]
        mask = train_df[station_code_cols].apply(lambda row: station_code in row.values, axis=1)
        matching_trains_df = train_df[mask].copy()

    # Filters Section
    st.write("")
    col1, _, col2 = con1.columns([2, 0.5, 2])

    # --- Day Filter UI ---
    col1.markdown("### 🗓️ Filter by Running Days")
    day_options = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Daily"]
    day_cols = col1.columns(len(day_options))
    selected_days = [day_options[i] for i, col in enumerate(day_cols) if col.checkbox(day_options[i], key=f"station_day_{i}")]

    # --- Apply Day Filter Logic ---
    day_idx = {day: i for i, day in enumerate(day_options[:-1])}  # exclude "Daily"
    if selected_days:
        if "Daily" in selected_days:
            matching_trains_df = matching_trains_df[matching_trains_df["runningOn"] == "YYYYYYY"]
        else:
            def runs_on_all_selected_days(running_on_str):
                return all(running_on_str[day_idx[day]] == 'Y' for day in selected_days)
            matching_trains_df = matching_trains_df[matching_trains_df["runningOn"].apply(runs_on_all_selected_days)]

    # --- Class Filter UI ---
    col2.markdown("### 🛏️ Filter by Available Classes")
    static_classes = ["1A", "2A", "3A", "3E", "CC", "SL", "EV", "2S"]
    class_cols = col2.columns(len(static_classes))
    selected_classes = [cls for i, cls in enumerate(static_classes) if class_cols[i].checkbox(cls, key=f"station_class_{cls}")]

    # --- Apply Class Filter Logic ---
    if selected_classes:
        def has_any_selected_class(classes_str):
            train_classes = [cls.strip().upper() for cls in str(classes_str).split(',')]
            return any(cls in train_classes for cls in selected_classes)
        matching_trains_df = matching_trains_df[matching_trains_df["journeyClasses"].apply(has_any_selected_class)]

    if matching_trains_df.empty:
        st.info("No trains found for the selected station and filters.")
        return

    # Build Display Table
    fmt = "%H:%M"
    rows = []
    for _, row in matching_trains_df.iterrows():
        try:
            number = str(row["trainNumber"]).replace(",", "")
            name = str(row["trainName"])
            stations = [
                str(row.get(f"station{i}_code", ""))
                for i in range(1, 100)
                if pd.notna(row.get(f"station{i}_code"))
            ]
            if not stations:
                continue

            from_code = stations[0]
            to_code = stations[-1]
            dep_origin = row.get("station1_dep", "")
            arr_dest = row.get(f"station{len(stations)}_arr", "")
            dep_day = int(row.get("station1_day", 0))
            arr_day = int(row.get(f"station{len(stations)}_day", 0))

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

                from_dist = row.get("station1_dist")
                to_dist = row.get(f"station{len(stations)}_dist")
                if pd.notna(from_dist) and pd.notna(to_dist):
                    total_distance = int(to_dist - from_dist)
                    if total_minutes > 0:
                        average_speed = int(total_distance / (total_minutes / 60))
            except Exception:
                pass

            rows.append({
                "Select": False,
                "train_df_index": row.name,
                "Train No": number,
                "Train Name": name,
                "Origin": f"{from_code} - {row.get('station1_name', '')}",
                "Destination": f"{to_code} - {row.get(f'station{len(stations)}_name', '')}",
                "Departure": dep_origin,
                "Arrival": arr_dest,
                "Duration": total_duration,
                "Distance (km)": int(total_distance),
                "Avg Speed (km/h)": int(average_speed),
                "Running On": parse_running_days(row["runningOn"]),
                "Train Type": row["train_type"],
                "Classes": row["journeyClasses"],
            })
        except Exception:
            continue

    display_df = pd.DataFrame(rows)
    display_df.insert(0, "Sl No", range(1, len(display_df) + 1))

    st.subheader("List of trains")
    edited_df = st.data_editor(
        display_df.drop(columns=["train_df_index"]),
        use_container_width=True,
        hide_index=True,
        key="station_train_selector",
        column_config={"Select": st.column_config.CheckboxColumn("Select")},
        disabled=[col for col in display_df.columns if col not in ["Select", "Sl No"]],
        num_rows="fixed"
    )

    selected_rows = edited_df[edited_df["Select"] == True]

    if len(selected_rows) > 1:
        st.warning("Please select only one train.")
    elif len(selected_rows) == 1:
        selected_train_no = selected_rows.iloc[0]["Train No"]
        selected_index = display_df.loc[display_df["Train No"] == selected_train_no, "train_df_index"].values[0]
        selected_train_row = train_df.loc[selected_index]

        st.subheader(f"Full Time Table for Train No: {selected_train_row['trainNumber']} - {selected_train_row['trainName']}")
        st.dataframe(build_timetable(selected_train_row))
