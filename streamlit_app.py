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

    st.set_page_config(page_title="EU Interagency Beach Volley Tournament Dashboard", layout="wide")
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

    st.set_page_config(page_title="EU Interagency Beach Volley Tournament Dashboard", layout="wide")
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
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Standings", "Next Matches", "Search Team", "Search Player", "Clock"]
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
            # Rankings of qualified teams
            # -----------------------------

            # 2x2 MIX -> ranking of all group winners
            if category == "2x2 MIX":
                firsts = []

                for group_name, df in standings["2x2 MIX"].items():
                    df_sorted = df.sort_values(
                        ["Score", "Points quotient"],
                        ascending=[False, False]
                    )

                    winner = df_sorted.iloc[0].copy()
                    winner["Group"] = group_name
                    winner["Team"] = winner[group_name]
                    winner = winner.drop(group_name)
                    firsts.append(winner)

                if firsts:
                    firsts_df = pd.DataFrame(firsts)
                    cols = ['Team'] + [c for c in firsts_df.columns if c != "Team"]
                    firsts_df = firsts_df[cols]

                    st.markdown("## 2x2 MIX - Ranking of Group Winners")

                    firsts_df = firsts_df.sort_values(
                        ["Score", "Points quotient"],
                        ascending=[False, False]
                    ).drop(columns=["Tied"], errors="ignore")

                    cols = ["Group"] + [c for c in firsts_df.columns if c != "Group"]
                    st.dataframe(
                        firsts_df[cols],
                        use_container_width=True,
                        hide_index=True
                    )

            # 4x4 Mix -> ranking of group winners and runners-up
            if category == "4x4 Mix":

                firsts = []
                seconds = []

                for group_name, df in standings["4x4 Mix"].items():
                    df_sorted = df.sort_values(
                        ["Score", "Points quotient"],
                        ascending=[False, False]
                    )

                    if len(df_sorted) >= 1:
                        winner = df_sorted.iloc[0].copy()
                        winner["Group"] = group_name
                        winner["Team"] = winner[group_name]
                        winner = winner.drop(group_name)
                        firsts.append(winner)

                    if len(df_sorted) >= 2:
                        second = df_sorted.iloc[1].copy()
                        second["Group"] = group_name
                        second["Team"] = second[group_name]
                        second = second.drop(group_name)
                        seconds.append(second)

                if firsts:
                    firsts_df = pd.DataFrame(firsts)
                    cols = ['Team'] + [c for c in firsts_df.columns if c != "Team"]
                    firsts_df = firsts_df[cols]

                    st.markdown("## 4x4 Mix - Ranking of Group Winners")

                    firsts_df = firsts_df.sort_values(
                        ["Score", "Points quotient"],
                        ascending=[False, False]
                    ).drop(columns=["Tied"], errors="ignore")

                    cols = ["Group"] + [c for c in firsts_df.columns if c != "Group"]
                    st.dataframe(
                        firsts_df[cols],
                        use_container_width=True,
                        hide_index=True
                    )

                if seconds:
                    seconds_df = pd.DataFrame(seconds)
                    cols = ['Team'] + [c for c in seconds_df.columns if c != "Team"]
                    seconds_df = seconds_df[cols]

                    st.markdown("## 4x4 Mix - Ranking of Group Runners-up")

                    seconds_df = seconds_df.sort_values(
                        ["Score", "Points quotient"],
                        ascending=[False, False]
                    ).drop(columns=["Tied"], errors="ignore")

                    cols = ["Group"] + [c for c in seconds_df.columns if c != "Group"]
                    st.dataframe(
                        seconds_df[cols],
                        use_container_width=True,
                        hide_index=True
                    )

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

# -----------------------------
# Tab 4 - Search by player name
# -----------------------------
with tab4:
    st.title("Find Matches by Player")

    player_cols = [
        c for c in global_df.columns
        if str(c).startswith("Giocatore ")
    ]

    players = sorted(
        {
            str(player).strip()
            for col in player_cols
            for player in global_df[col].dropna()
            if str(player).strip()
        }
    )

    player_name = st.selectbox(
        "Select a player:",
        options=players,
        index=None,
        placeholder="Start typing a player..."
    )

    if player_name:

        mask = False

        for col in player_cols:
            mask = global_df[player_cols].astype(str).apply(
                lambda row: row.str.strip().str.lower().eq(player_name.strip().lower()).any(),
                axis=1
            )

        results = global_df.loc[
            mask,
            [
                "MatchDateTime",
                "Court",
                "Team1",
                "Team 2",
                "Score 1",
                "Score 2"
            ]
        ].sort_values("MatchDateTime")

        if results.empty:
            st.warning("No matches found for that player.")
        else:
            results["Score 1"] = results["Score 1"].fillna(0).astype(int)
            results["Score 2"] = results["Score 2"].fillna(0).astype(int)

            results["Score"] = (
                results["Score 1"].astype(str)
                + "-"
                + results["Score 2"].astype(str)
            )

            results = results.drop(columns=["Score 1", "Score 2"])

            results["MatchDateTime"] = results["MatchDateTime"].dt.strftime("%d-%m %H:%M")

            results = results.rename(
                columns={"MatchDateTime": "Date & Time"}
            )

            st.dataframe(
                results,
                use_container_width=True,
                hide_index=True
            )

    else:
        st.info("Type a player name to search for matches.")

with tab5:

    now = datetime.now(ITALY_TZ)

    st.markdown(
        f"""
        <style>
            html, body, [data-testid="stAppViewContainer"] {{
                height: 100vh;
                margin: 0;
                padding: 0;
            }}

            [data-testid="stAppViewContainer"] {{
                display: flex;
                justify-content: center;
                align-items: center;
            }}
        </style>

        <div style="
            display:flex;
            flex-direction:column;
            justify-content:center;
            align-items:center;
            width:100vw;
            height:100vh;
        ">
            <h1 style="
                font-size:12vw;
                margin:0;
            ">
                {now.strftime('%H:%M')}
            </h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()
st.caption("Made with ❤️ by Ingegnerini del JRC")
