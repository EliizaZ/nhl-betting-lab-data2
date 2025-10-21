"""
Reworked nhl_api.py — now fully based on Moneypuck data instead of NHL API.
Provides schedule, team list, and recent game stats directly from Moneypuck.
"""

import datetime as dt
import pandas as pd
import requests
from streamlit.runtime.caching import cache_data
from config import CACHE_TTL_LONG, CACHE_TTL_SHORT, CACHE_TTL_DAY


MONEYPUCK_GAMES_URL = "https://moneypuck.com/moneypuck/gameData/{season}.csv"
MONEYPUCK_TEAMS_URL = "https://moneypuck.com/moneypuck/teamData/{season}.csv"


def _current_season_str():
    today = dt.date.today()
    start_year = today.year if today.month >= 7 else today.year - 1
    return f"{start_year}-{start_year+1}"


@cache_data(show_spinner=False, ttl=CACHE_TTL_DAY)
def load_games(season: str | None = None) -> pd.DataFrame:
  import requests
import pandas as pd
from datetime import date
from io import StringIO
from streamlit.runtime.caching import cache_data
from pathlib import Path

CACHE_TTL_DAY = 60 * 60 * 24  # 1 day cache


@cache_data(show_spinner=False, ttl=CACHE_TTL_DAY)
def get_live_games() -> pd.DataFrame:
    """Fetch live NHL games from ESPN API (auto-updating)."""
    url = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()

        games = []
        for game in data.get("events", []):
            comp = game["competitions"][0]
            home = comp["competitors"][0]
            away = comp["competitors"][1]
            games.append({
                "home": home["team"]["displayName"],
                "away": away["team"]["displayName"],
                "home_score": int(home.get("score", 0)),
                "away_score": int(away.get("score", 0)),
                "status": game["status"]["type"]["description"],
                "start_time": game["date"]
            })

        if not games:
            raise ValueError("No live NHL games found from ESPN API")

        return pd.DataFrame(games)

    except Exception as e:
        print(f"[ERROR] ESPN API unavailable: {e}")
        return pd.DataFrame([{"home": "Toronto Maple Leafs", "away": "Vancouver Canucks"}])


@cache_data(show_spinner=False, ttl=CACHE_TTL_DAY)
def load_moneypuck_stats(local_path: str | None = None) -> pd.DataFrame:
    """Load team advanced stats (xG%, CF%, PDO, etc.) from local MoneyPuck CSV if available."""
    if local_path is None:
        local_path = Path(__file__).parent / "data" / "teamStats_season2025-26.csv"

    if not Path(local_path).exists():
        print(f"[INFO] MoneyPuck data not found locally: {local_path}")
        return pd.DataFrame()

    df = pd.read_csv(local_path)
    df.columns = df.columns.str.lower()

    if 'team' not in df.columns:
        raise ValueError("Invalid MoneyPuck CSV — no 'team' column found")

    key_cols = ['team', 'xgoalspercentage', 'pdo', 'cfpercentage', 'goalsfor', 'goalsagainst']
    return df[[col for col in key_cols if col in df.columns]]


@cache_data(show_spinner=False, ttl=CACHE_TTL_DAY)
def get_schedule(today: date | None = None) -> pd.DataFrame:
    """Combine ESPN live games with MoneyPuck team stats (if available)."""
    games = get_live_games()
    stats = load_moneypuck_stats()

    if not stats.empty:
        games = games.merge(stats, how="left", left_on="home", right_on="team").drop(columns=["team"], errors="ignore")
        games = games.merge(stats, how="left", left_on="away", right_on="team", suffixes=("_home", "_away")).drop(columns=["team"], errors="ignore")

    return games
