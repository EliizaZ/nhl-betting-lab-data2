import streamlit as st
import pandas as pd
import numpy as np
import os
from models import edge

# ======= CONFIG =======
st.set_page_config("🏒 NHL Betting Lab — Local Data")
st.title("🏒 NHL Betting Lab")

DATA_PATH = "data/processed/team_level.csv"

# ======= LOAD DATA =======
if not os.path.exists(DATA_PATH):
    st.error("❌ Dati nav atrasti! Palaid `fetch_nhl_data.py`, lai apstrādātu CSV failus.")
    st.stop()

df = pd.read_csv(DATA_PATH)
st.success(f"Dati ielādēti no `{DATA_PATH}`")

# ======= TEAM SELECTION =======
teams = sorted(df["team"].unique())
col1, col2 = st.columns(2)
teamA = col1.selectbox("🏒 Away komanda", teams)
teamB = col2.selectbox("🏠 Home komanda", teams)

# ======= USER INPUT: BOOK ODDS =======
# ======= USER INPUT: BOOK ODDS =======
st.subheader("💰 Bukmeikeru koeficienti")
col1, col2 = st.columns(2)

ml_away = col1.number_input(
    f"{teamA} ML",
    min_value=1.01,
    step=0.01,
    value=2.00,
    key=f"ml_away_{teamA}"
)

ml_home = col2.number_input(
    f"{teamB} ML",
    min_value=1.01,
    step=0.01,
    value=2.00,
    key=f"ml_home_{teamB}"
)


# ======= MODEL: FAIR ODDS =======

def calc_team_strength(df, team_name):
    """Aprēķina komandas relatīvo xG bilanci"""
    team_df = df[(df["team"] == team_name) & (df["situation"] == "all")]
    if team_df.empty:
        return 0.0
    xgf = team_df["xGoalsFor"].mean()
    xga = team_df["xGoalsAgainst"].mean()
    return (xgf - xga) / (xgf + xga + 1e-6)

def win_probability(str_home, str_away, is_home=True):
    """Loģistiskā funkcija — pārveido xG starpību uz uzvaras iespēju"""
    xgf_diff = str_home - str_away
    if is_home:
        xgf_diff += 0.05  # home advantage
    return 1 / (1 + np.exp(-4 * xgf_diff))

# Aprēķini komandu spēka rādītājus
str_home = calc_team_strength(df, teamB)
str_away = calc_team_strength(df, teamA)

# Pārvērš xG starpību uz win probability
prob_home = win_probability(str_home, str_away, is_home=True)
prob_away = 1 - prob_home

# Fair odds
fair_home = 1 / prob_home
fair_away = 1 / prob_away

# Edge aprēķins
edge_home = edge(fair_home, ml_home)
edge_away = edge(fair_away, ml_away)

# ======= DISPLAY RESULTS =======
st.divider()
st.subheader("📊 Model & Fair Odds Aprēķins")

col1, col2 = st.columns(2)
col1.metric(f"{teamB} Fair Odd", f"{fair_home:.2f}", f"{edge_home*100:+.2f}%")
col2.metric(f"{teamA} Fair Odd", f"{fair_away:.2f}", f"{edge_away*100:+.2f}%")

# ======= SMART VERDICT =======
st.divider()
st.subheader("🧠 Smart Verdict — Modeļa ieteikums")

def verdict(edge_home, edge_away, prob_home, team_home, team_away):
    """Izveido saprotamu value bet analīzi"""
    threshold = 0.05  # 5% value slieksnis
    confidence = abs(edge_home - edge_away) * 100

    if edge_home > threshold:
        winner = team_home
        verdict = f"✅ Value bet: {team_home} ML"
        conf = f"Confidence: {confidence:.1f}%"
    elif edge_away > threshold:
        winner = team_away
        verdict = f"✅ Value bet: {team_away} ML"
        conf = f"Confidence: {confidence:.1f}%"
    else:
        winner = None
        verdict = "⚪ Nav skaidra value situācija"
        conf = f"Confidence: {confidence:.1f}%"

    return verdict, conf, winner

verdict_txt, conf_txt, winner = verdict(edge_home, edge_away, prob_home, teamB, teamA)

st.markdown(f"### {verdict_txt}")
st.caption(conf_txt)

# ======= OPTIONAL LOGOS =======
st.divider()
st.subheader("🏒 Komandu logotipi")
LOGO_BASE = "https://assets.nhle.com/logos/nhl/svg/"
col1, col2 = st.columns(2)

def team_logo(team_abbr):
    try:
        url = f"{LOGO_BASE}{team_abbr}_light.svg"
        return url
    except:
        return None

logo_home = team_logo(teamB)
logo_away = team_logo(teamA)

with col1:
    st.image(logo_away, width=100)
    st.text(teamA)

with col2:
    st.image(logo_home, width=100)
    st.text(teamB)


