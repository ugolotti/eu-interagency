import pandas as pd
import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo
from streamlit_autorefresh import st_autorefresh
import gdown

st_autorefresh(
    interval=60 * 1000,  # 60 seconds
    key="schedule_refresh"
)

# -----------------------------
# Configuration
# -----------------------------
# EXCEL_FILE = "EU interagencies schedule.xlsx"
EXCEL_FILE = "file.xlsx"
url = 'https://docs.google.com/spreadsheets/d/1oEsp-k_-2u3uhVmK33YaN4LycjW3CzuE/edit?usp=sharing&ouid=105307248857860129530&rtpof=true&sd=true'
ITALY_TZ = ZoneInfo("Europe/Rome")

@st.cache_data(ttl=60)
def load_standings():
    gdown.download(url, EXCEL_FILE, quiet=False)

    st.set_page_config(page_title="Tournament Dashboard", layout="wide")
    raw = pd.read_excel(
        EXCEL_FILE,
        sheet_name="Standings",
        header=None
    )

    sections = {}

    current_category = None
    i = 0

    while i < len(raw):

        value = raw.iloc[i, 0]

        if pd.isna(value):
            i += 1
            continue

        value = str(value).strip()

        if value in ["2x2 MIX", "2x2 M", "2x2 F", "4x4 Mix"]:

            current_category = value
            sections[current_category] = {}
            i += 1
            continue

        if value.startswith("Group"):

            group_name = value

            headers = raw.iloc[i].tolist()

            teams = []
            r = i + 1

            while r < len(raw):

                first = raw.iloc[r, 0]

                if pd.isna(first):
                    break

                first = str(first).strip()

                if first.startswith("Group"):
                    break

                if first in ["2x2 MIX", "2x2 M", "2x2 F", "4x4 Mix"]:
                    break

                teams.append(raw.iloc[r].tolist())
                r += 1

            df = pd.DataFrame(teams, columns=headers)

            sections[current_category][group_name] = df

            i = r
            continue

        i += 1

    return sections

# -----------------------------
# Load data
# -----------------------------
@st.cache_data(ttl=60)
def load_data():
    gdown.download(url, EXCEL_FILE, quiet=False)

    st.set_page_config(page_title="Tournament Dashboard", layout="wide")
    st.caption(
        f"Last update: {datetime.now(ITALY_TZ).strftime('%H:%M:%S')}"
    )
    global_df = pd.read_excel(EXCEL_FILE, sheet_name="Global", header=3)

    # Normalize column names (remove extra spaces)
    global_df.columns = global_df.columns.str.strip()

    # Build a datetime column from Date + Time
    global_df["MatchDateTime"] = pd.to_datetime(
        global_df["Date"].astype(str) + " " + global_df["Time"].astype(str),
        errors="coerce"
    ).dt.tz_localize(ITALY_TZ)

    return global_df

global_df = load_data()

# -----------------------------
# Tabs
# -----------------------------
tab1, tab2, tab3, tab4 = st.tabs(
    ["Standings", "Next Matches", "Search Team", "Clock"]
)


# -----------------------------
# Tab 1 - Standings
# -----------------------------
with tab1:

    standings = load_standings()

    for category, groups in standings.items():

        with st.expander(category, expanded=False):

            for group_name, df in groups.items():

                st.markdown(f"### {group_name}")
                st.dataframe(df, use_container_width=True, hide_index=True)

# -----------------------------
# Tab 2 - Next 3 matches for each court
# -----------------------------
with tab2:
    st.title("Next Matches by Court")

    now = datetime.now(ITALY_TZ)

    # Only future matches
    upcoming = global_df[global_df["MatchDateTime"] >= now].copy()
    upcoming = upcoming.sort_values(["Court", "MatchDateTime"])

    if upcoming.empty:
        st.info("No upcoming matches found.")
    else:
        courts = upcoming["Court"].dropna().unique()

        for court in courts:
            court_matches = upcoming[upcoming["Court"] == court].head(3)

            st.subheader(f"Court {int(court)}")
            display = court_matches[["MatchDateTime", "Team1", "Team 2"]].copy()
            display["MatchDateTime"] = (display["MatchDateTime"].dt.strftime("%d-%m %H:%M"))
            display.columns = ["Date & Time", "Team 1", "Team 2"]
            st.dataframe(display, use_container_width=True, hide_index=True)

# -----------------------------
# Tab 3 - Search by team name
# -----------------------------
with tab3:
    st.title("Find Matches by Team")

    team_name = st.text_input("Enter a team name:")

    if team_name:
        mask = (
            global_df["Team1"].astype(str).str.contains(team_name, case=False, na=False)
            | global_df["Team 2"].astype(str).str.contains(team_name, case=False, na=False)
        )

        results = global_df.loc[mask, [
            "MatchDateTime", "Court", "Team1", "Team 2", "Score 1", "Score 2"
        ]].sort_values("MatchDateTime")

        if results.empty:
            st.warning("No matches found for that team.")
        else:
            # create combined score column
            results["Score 1"] = results["Score 1"].fillna(0).astype(int)
            results["Score 2"] = results["Score 2"].fillna(0).astype(int)
            results["Score"] = (
                results["Score 1"].astype(str) + "-" + results["Score 2"].astype(str)
            )
            # drop old score columns
            results = results.drop(columns=["Score 1", "Score 2"])

            results["MatchDateTime"] = results["MatchDateTime"].dt.strftime("%d-%m %H:%M")
            results = results.rename(columns={"MatchDateTime": "Date & Time"})
            st.dataframe(results, use_container_width=True, hide_index=True)
    else:
        st.info("Type a team name to search for matches.")

with tab4:

    now = datetime.now(ITALY_TZ)

    st.markdown(
        f"""
        <div style="
            display:flex;
            flex-direction:column;
            justify-content:center;
            align-items:center;
            height:70vh;
        ">
            <h1 style="
                font-size:10rem;
                margin:0;
            ">
                {now.strftime('%H:%M')}
            </h1>

        </div>
        """,
        unsafe_allow_html=True,
    )