import pandas as pd
import streamlit as st
from datetime import datetime

# -----------------------------
# Configuration
# -----------------------------
EXCEL_FILE = "EU interagencies schedule.xlsx"

st.set_page_config(page_title="Tournament Dashboard", layout="wide")

# -----------------------------
# Load data
# -----------------------------
@st.cache_data
def load_data():
    standings = pd.read_excel(EXCEL_FILE, sheet_name="Standings")
    global_df = pd.read_excel(EXCEL_FILE, sheet_name="Global")

    # Normalize column names (remove extra spaces)
    standings.columns = standings.columns.str.strip()
    global_df.columns = global_df.columns.str.strip()

    # Build a datetime column from Date + Time
    global_df["MatchDateTime"] = pd.to_datetime(
        global_df["Date"].astype(str) + " " + global_df["Time"].astype(str),
        errors="coerce"
    )

    return standings, global_df


standings_df, global_df = load_data()

# -----------------------------
# Tabs
# -----------------------------
tab1, tab2, tab3 = st.tabs(["Standings", "Next Matches by Court", "Search by Team"])

# -----------------------------
# Tab 1 - Standings
# -----------------------------
with tab1:
    st.title("Standings")
    st.dataframe(standings_df, use_container_width=True)

# -----------------------------
# Tab 2 - Next 3 matches for each court
# -----------------------------
with tab2:
    st.title("Next Matches by Court")

    now = pd.Timestamp.now()

    # Only future matches
    upcoming = global_df[global_df["MatchDateTime"] >= now].copy()
    upcoming = upcoming.sort_values(["Court", "MatchDateTime"])

    if upcoming.empty:
        st.info("No upcoming matches found.")
    else:
        courts = upcoming["Court"].dropna().unique()

        for court in courts:
            court_matches = upcoming[upcoming["Court"] == court].head(3)

            st.subheader(f"Court {court}")
            display = court_matches[["MatchDateTime", "Team 1", "Team 2"]].copy()
            display.columns = ["Date & Time", "Team 1", "Team 2"]
            st.dataframe(display, use_container_width=True)

# -----------------------------
# Tab 3 - Search by team name
# -----------------------------
with tab3:
    st.title("Find Matches by Team")

    team_name = st.text_input("Enter a team name:")

    if team_name:
        mask = (
            global_df["Team 1"].astype(str).str.contains(team_name, case=False, na=False)
            | global_df["Team 2"].astype(str).str.contains(team_name, case=False, na=False)
        )

        results = global_df.loc[mask, [
            "MatchDateTime", "Court", "Team 1", "Team 2"
        ]].sort_values("MatchDateTime")

        if results.empty:
            st.warning("No matches found for that team.")
        else:
            results = results.rename(columns={"MatchDateTime": "Date & Time"})
            st.dataframe(results, use_container_width=True)
    else:
        st.info("Type a team name to search for matches.")