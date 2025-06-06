import requests
import streamlit as st
import pandas as pd
import warnings

warnings.filterwarnings("ignore")

def check_pnr_status():
    st.subheader("🔍 Check IRCTC PNR Status")

    with st.form("pnr_form"):
        pnr = st.text_input("Enter your 10-digit PNR Number", max_chars=10)
        submitted = st.form_submit_button("Check Status")

    if submitted:
        if not (pnr.isdigit() and len(pnr) == 10):
            st.error("❗ Please enter a valid 10-digit numeric PNR number.")
            return

        # === API Call ===
        url = f"https://irctc-indian-railway-pnr-status.p.rapidapi.com/getPNRStatus/{pnr}"
        headers = {
            "x-rapidapi-key": "bab0ed34damsh6e9ffde2dc9e481p11cafajsn8a09a681672b",
            "x-rapidapi-host": "irctc-indian-railway-pnr-status.p.rapidapi.com"
        }

        with st.spinner("Fetching PNR details..."):
            try:
                response = requests.get(url, headers=headers, verify=False, timeout=10)
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                st.error("❌ Failed to fetch data from the API.")
                return

        # === Check if response is successful ===
        if not data.get("success", False):
            st.error("❌ No data found for this PNR number.")
            return

        pnr_data = data.get("data", {})

        # === General Info Table ===
        general_info = {
            "PNR Number": pnr_data.get("pnrNumber"),
            "Train Number": pnr_data.get("trainNumber"),
            "Train Name": pnr_data.get("trainName"),
            "From": pnr_data.get("sourceStation"),
            "To": pnr_data.get("destinationStation"),
            "Boarding Point": pnr_data.get("boardingPoint"),
            "Reservation Upto": pnr_data.get("reservationUpto"),
            "Class": pnr_data.get("journeyClass"),
            "Quota": pnr_data.get("quota"),
            "Booking Date": pnr_data.get("bookingDate"),
            "Date of Journey": pnr_data.get("dateOfJourney"),
            "Arrival Date": pnr_data.get("arrivalDate"),
            "Chart Status": pnr_data.get("chartStatus"),
            "Distance (km)": pnr_data.get("distance"),
            "Ticket Fare": pnr_data.get("ticketFare"),
            "Vikalp": pnr_data.get("vikalpStatus"),
        }

        st.markdown("### 📄 General Journey Details")
        st.dataframe(pd.DataFrame([general_info]), use_container_width=True)

        # === Passenger Info Table ===
        passengers = pnr_data.get("passengerList", [])
        if passengers:
            passenger_df = pd.DataFrame(passengers)
            passenger_df.rename(columns={
                "passengerSerialNumber": "Passenger #",
                "passengerNationality": "Nationality",
                "passengerQuota": "Quota",
                "bookingStatus": "Booking Status",
                "bookingStatusDetails": "Booking Berth",
                "currentStatus": "Current Status",
                "currentStatusDetails": "Current Berth",
            }, inplace=True)

            cols = ["Passenger #", "Nationality", "Quota", "Booking Status", "Booking Berth", "Current Status", "Current Berth"]
            st.markdown("### 👥 Passenger Details")
            st.dataframe(passenger_df[cols], use_container_width=True)
        else:
            st.info("No passenger information available.")
