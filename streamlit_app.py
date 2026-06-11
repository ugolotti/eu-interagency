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
# url = 'https://docs.google.com/spreadsheets/d/1oEsp-k_-2u3uhVmK33YaN4LycjW3CzuE/edit?usp=sharing&ouid=105307248857860129530&rtpof=true&sd=true'
url = 'https://www.dropbox.com/scl/fi/17x7g3ieq4a2lq0zy2ipw/EU-interagencies-schedule.xlsx?rlkey=tiit76551gidcoe70pqsafbbl&e=1&st=5b0e29ia&dl=1'
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

                df_sorted = df.sort_values(["Score", "Points quotient"], ascending=[False, False]).drop(columns=["Tied"], errors="ignore")
                st.markdown(f"### {group_name}")
                st.dataframe(df_sorted, use_container_width=True, hide_index=True)

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

    # build unique team list from both columns
    teams = sorted(
        set(global_df["Team1"].dropna().astype(str))
        | set(global_df["Team 2"].dropna().astype(str))
    )
    team_name = st.selectbox(
        "Select a team:",
        options=teams,
        index=None,
        placeholder="Start typing a team..."
    )

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

    st.markdown(
        """
        <style>
            .block-container {
                padding: 0;
                max-width: 100%;
            }

            #clock-container {
                width: 100vw;
                height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                font-family: monospace;
                font-size: 15vw;
                font-weight: bold;
            }
        </style>

        <div id="clock-container">
            <span id="clock"></span>
        </div>

        <script>
            function updateClock() {
                const now = new Date();

                const time = now.toLocaleTimeString(
                    'it-IT',
                    {
                        timeZone: 'Europe/Rome',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit'
                    }
                );

                document.getElementById('clock').textContent = time;
            }

            updateClock();
            setInterval(updateClock, 1000);
        </script>
        """,
        unsafe_allow_html=True,
    )