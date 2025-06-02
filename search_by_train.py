import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from search_by_route import build_timetable


def parse_running_days(running_on: str) -> str:
    days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    return ', '.join(day for day, status in zip(days, running_on) if status == 'Y')


def find_matching_trains_by_name(train_df, query):
    matches = []
    fmt = "%H:%M"
    query = query.lower()

    for _, row in train_df.iterrows():
        number = str(row["trainNumber"]).replace(",", "")
        name = str(row["trainName"])

        if query in number.lower() or query in name.lower():
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

            matches.append({
                "Train No": number,
                "Train Name": name,
                "Origin": f"{from_code} - {row.get('station1_name', '')}",
                "Destination": f"{to_code} - {row.get(f'station{len(stations)}_name', '')}",
                "Running On": parse_running_days(row["runningOn"]),
                "Train Type": row["train_type"],
                "Classes": row["journeyClasses"],
                "Departure": dep_origin,
                "Arrival": arr_dest,
                "Duration": total_duration,
                "Distance (km)": str(total_distance),
                "Avg Speed (km/h)": str(average_speed),
                "Index": row.name  # retain index to fetch original row later
            })

    return pd.DataFrame(matches)


def search_by_train(train_df):
    st.subheader("🔍 Search by Train Number or Name")

    train_df["label"] = train_df["trainNumber"].astype(str) + " - " + train_df["trainName"]
    train_labels = sorted(train_df["label"].tolist())
    label_to_number = dict(zip(train_df["label"], train_df["trainNumber"].astype(str)))

    def on_selectbox_change():
        st.session_state["textinput_train"] = ""

    def on_textinput_change():
        st.session_state["selectbox_train"] = None

    col1, col2 = st.columns(2)

    with col1:
        selected_train_label = st.selectbox(
            "**Select a train**",
            [None] + train_labels,
            key="selectbox_train",
            on_change=on_selectbox_change
        )

    with col2:
        query = st.text_input(
            "**Or type a part of the train number or name**",
            key="textinput_train",
            on_change=on_textinput_change
        )

    if selected_train_label:
        selected_train_number = label_to_number[selected_train_label]
        selected_row = train_df[train_df["trainNumber"].astype(str) == selected_train_number]
        if not selected_row.empty:
            row = selected_row.iloc[0]
            st.write(f"### 📍 Full Time Table for Train {row['trainNumber']} - {row['trainName']}")
            st.dataframe(build_timetable(row))
        st.markdown("---")

    elif query:
        results_df = find_matching_trains_by_name(train_df, query)

        if results_df.empty:
            st.info("No matching trains found.")
        else:
            st.write(f"### 🚆 {len(results_df)} Matching Trains")

            # Prepare display with 'Select' column first
            display_df = results_df.drop(columns=["Index"]).copy()
            display_df["Select"] = False
            display_df = display_df[["Select"] + [col for col in display_df.columns if col != "Select"]]

            # Display editor
            edited_df = st.data_editor(
                display_df,
                use_container_width=True,
                hide_index=True,
                key="search_table_editor",
                column_config={"Select": st.column_config.CheckboxColumn("Select")},
                disabled=[col for col in display_df.columns if col != "Select"],
                num_rows="fixed"
            )

            selected_rows = edited_df[edited_df["Select"] == True]

            # Handle selection
            if len(selected_rows) > 1:
                st.warning("Please select only one train.")
            elif len(selected_rows) == 1:
                selected_train_no = selected_rows.iloc[0]["Train No"]
                original_index = results_df[results_df["Train No"] == selected_train_no]["Index"].values[0]
                row = train_df.loc[original_index]
                st.write(f"### 📍 Full Time Table for Train {row['trainNumber']} - {row['trainName']}")
                st.dataframe(build_timetable(row))