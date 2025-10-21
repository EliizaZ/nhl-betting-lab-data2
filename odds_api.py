import requests
import os
import pandas as pd

ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "")  # ievadi šeit, ja nav ENV
SPORT = "icehockey_nhl"
REGION = "us"
MARKET = "h2h"

def get_latest_odds():
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds/?apiKey={ODDS_API_KEY}&regions={REGION}&markets={MARKET}&oddsFormat=decimal"
    r = requests.get(url, timeout=30)
    if r.status_code != 200:
        return None
    data = r.json()
    rows = []
    for game in data:
        home = game["home_team"]
        away = game["away_team"]
        for b in game["bookmakers"]:
            name = b["title"]
            for m in b["markets"]:
                if m["key"] != "h2h":
                    continue
                for o in m["outcomes"]:
                    rows.append({
                        "home": home,
                        "away": away,
                        "bookmaker": name,
                        "team": o["name"],
                        "price": o["price"]
                    })
    return pd.DataFrame(rows)

