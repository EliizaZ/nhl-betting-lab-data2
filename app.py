# app.py — NHL Betting Lab (Clean Pro Version)
import os
import math
import pandas as pd
import streamlit as st
from datetime import datetime

st.set_page_config(page_title="🏒 NHL Betting Lab — Pro Version", layout="wide")
st.title("🏒 NHL Betting Lab (by Babixx)")

# ------------------------------------------
# Ceļš uz CSV failu
# ------------------------------------------
DATA_DIR = "data/processed"
CSV_PATH = os.path.join(DATA_DIR, "team_level.csv")

# ------------------------------------------
# Palīgfunkcijas
# ------------------------------------------
def pick_first_col(df, candidates, default=None):
    for c in candidates:
        if c in df.columns:
            return c
    return default

def normalized_cols(df: pd.DataFrame):
    return {
        "team": pick_first_col(df, ["team", "Team", "team_name"], "team"),
        "season": pick_first_col(df, ["season", "Season"], None),
        "games": pick_first_col(df, ["games", "games_played", "GamesPlayed"], None),
        "xgf": pick_first_col(df, ["xgf", "xGoalsFor", "xGF"], None),
        "xga": pick_first_col(df, ["xga", "xGoalsAgainst", "xGA"], None),
        "xgf_pct": pick_first_col(df, ["xgf_pct", "xGoalsPercentage", "xGF%"], None),
    }

TEAM_ABBR = {
    "Anaheim Ducks": "anaheim-ducks", "Arizona Coyotes": "arizona-coyotes", "Boston Bruins": "boston-bruins",
    "Buffalo Sabres": "buffalo-sabres", "Calgary Flames": "calgary-flames", "Carolina Hurricanes": "carolina-hurricanes",
    "Chicago Blackhawks": "chicago-blackhawks", "Colorado Avalanche": "colorado-avalanche",
    "Columbus Blue Jackets": "columbus-blue-jackets", "Dallas Stars": "dallas-stars", "Detroit Red Wings": "detroit-red-wings",
    "Edmonton Oilers": "edmonton-oilers", "Florida Panthers": "florida-panthers", "Los Angeles Kings": "los-angeles-kings",
    "Minnesota Wild": "minnesota-wild", "Montreal Canadiens": "montreal-canadiens", "Nashville Predators": "nashville-predators",
    "New Jersey Devils": "new-jersey-devils", "New York Islanders": "new-york-islanders", "New York Rangers": "new-york-rangers",
    "Ottawa Senators": "ottawa-senators", "Philadelphia Flyers": "philadelphia-flyers", "Pittsburgh Penguins": "pittsburgh-penguins",
    "San Jose Sharks": "san-jose-sharks", "Seattle Kraken": "seattle-kraken", "St Louis Blues": "st-louis-blues",
    "Tampa Bay Lightning": "tampa-bay-lightning", "Toronto Maple Leafs": "toronto-maple-leafs", "Vancouver Canucks": "vancouver-canucks",
    "Vegas Golden Knights": "vegas-golden-knights", "Washington Capitals": "washington-capitals", "Winnipeg Jets": "winnipeg-jets"
}

def logo_url(team_name: str) -> str | None:
    abbr = TEAM_ABBR.get(team_name)
    if not abbr:
        return None
    return f"https://loodibee.com/wp-content/uploads/nhl-{abbr}-logo.png"

def team_strength(row, cols):
    g = row.get(cols["games"], 0)
    xgf = row.get(cols["xgf"], 0)
    xga = row.get(cols["xga"], 0)
    xgf_pct = row.get(cols["xgf_pct"], 50)

    try:
        g = float(g)
        xgf = float(xgf)
        xga = float(xga)
        xgf_pct = float(xgf_pct)
    except:
        return 0

    margin_per_g = (xgf - xga) / g if g > 0 else 0
    comp_xgf_pct = (xgf_pct - 50.0) / 10.0
    return 0.7 * comp_xgf_pct + 0.3 * margin_per_g

def logistic(x, k=1.25):
    try:
        return 1 / (1 + math.exp(-k * x))
    except OverflowError:
        return 1.0 if x > 0 else 0.0

def fair_odds(p):
    return 1 / p if p > 0 else float("inf")

def edge(book_odds, fair):
    return (book_odds / fair) - 1

def verdict(edge_home, edge_away, team_home, team_away):
    if edge_home > 0.05 and edge_home > edge_away:
        return f"🔥 <b>{team_home}</b> ir value bet ar <b>+{edge_home*100:.1f}%</b> pārsvaru."
    elif edge_away > 0.05:
        return f"🔥 <b>{team_away}</b> ir value bet ar <b>+{edge_away*100:.1f}%</b> pārsvaru."
    return "⚖️ Nav skaidras value iespējas — bukmeikeru koeficienti ir līdzsvaroti."

# ------------------------------------------
# Datu ielāde (auto-reload)
# ------------------------------------------
if not os.path.exists(CSV_PATH):
    st.error("❌ Dati nav atrasti! Pārliecinies, ka fails ir: `data/processed/team_level.csv`.")
    st.stop()

last_modified = datetime.fromtimestamp(os.path.getmtime(CSV_PATH)).strftime("%Y-%m-%d %H:%M:%S")
df = pd.read_csv(CSV_PATH)
cols = normalized_cols(df)
teams = sorted(df[cols["team"]].dropna().unique())

st.caption(f"📅 Dati ielādēti: {last_modified}")

# ------------------------------------------
# Komandu izvēle
# ------------------------------------------
col1, col2 = st.columns(2)
with col1:
    team_home = st.selectbox("🏠 Home team", teams)
with col2:
    team_away = st.selectbox("🧳 Away team", [t for t in teams if t != team_home])

home_row = df[df[cols["team"]] == team_home].tail(1).to_dict("records")[0]
away_row = df[df[cols["team"]] == team_away].tail(1).to_dict("records")[0]

r_home = team_strength(home_row, cols)
r_away = team_strength(away_row, cols)
p_home = logistic(r_home - r_away)
p_away = 1 - p_home

# ------------------------------------------
# Komandu logotipi
# ------------------------------------------
c1, c2, c3 = st.columns([4, 1, 4])
home_logo, away_logo = logo_url(team_home), logo_url(team_away)

with c1:
    if home_logo:
        st.image(home_logo, width=120)
    st.markdown(f"### 🏠 {team_home}")

with c2:
    st.markdown("<div style='text-align:center;font-size:28px;'>vs</div>", unsafe_allow_html=True)

with c3:
    if away_logo:
        st.image(away_logo, width=120)
    st.markdown(f"### 🧳 {team_away}")

# ------------------------------------------
# Book odds ievade
# ------------------------------------------
st.divider()
st.subheader("💰 Book Odds (ievadi manuāli)")

col1, col2 = st.columns(2)
with col1:
    book_home = st.number_input(f"{team_home} Book Odds", min_value=1.01, max_value=10.0, step=0.01, value=2.0)
with col2:
    book_away = st.number_input(f"{team_away} Book Odds", min_value=1.01, max_value=10.0, step=0.01, value=2.0)

# ------------------------------------------
# Aprēķini
# ------------------------------------------
fair_home = fair_odds(p_home)
fair_away = fair_odds(p_away)
edge_home = edge(book_home, fair_home)
edge_away = edge(book_away, fair_away)

# ------------------------------------------
# Rezultātu tabula
# ------------------------------------------
st.divider()
st.subheader("📈 Model Analysis")

c1, c2, c3 = st.columns(3)
c1.metric(f"{team_home} Win%", f"{p_home*100:.1f}%")
c2.metric(f"{team_home} Fair Odds", f"{fair_home:.2f}")
c3.metric(f"{team_home} Value Edge", f"{edge_home*100:+.1f}%")

c1, c2, c3 = st.columns(3)
c1.metric(f"{team_away} Win%", f"{p_away*100:.1f}%")
c2.metric(f"{team_away} Fair Odds", f"{fair_away:.2f}")
c3.metric(f"{team_away} Value Edge", f"{edge_away*100:+.1f}%")

# ------------------------------------------
# Smart Verdict
# ------------------------------------------
st.divider()
st.subheader("🧠 Smart Verdict")

confidence = abs(edge_home - edge_away) * 100
verdict_text = verdict(edge_home, edge_away, team_home, team_away)
st.markdown(f"{verdict_text}<br><br>💡 <b>Confidence:</b> {confidence:.1f}%", unsafe_allow_html=True)

# ------------------------------------------
# Save Report
# ------------------------------------------
st.divider()
st.subheader("💾 Saglabāt rezultātus")

report = pd.DataFrame([{
    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "home_team": team_home,
    "away_team": team_away,
    "home_win_prob": p_home,
    "away_win_prob": p_away,
    "home_fair_odds": fair_home,
    "away_fair_odds": fair_away,
    "home_book_odds": book_home,
    "away_book_odds": book_away,
    "home_edge": edge_home,
    "away_edge": edge_away,
    "confidence": confidence
}])

if st.button("💾 Save to CSV"):
    save_path = os.path.join(DATA_DIR, "betting_reports.csv")
    report.to_csv(save_path, mode="a", header=not os.path.exists(save_path), index=False)
    st.success(f"Rezultāti saglabāti: {save_path}")

st.caption("Fair odds = 1 / WinProbability. Value Edge = (Book / Fair) - 1")


