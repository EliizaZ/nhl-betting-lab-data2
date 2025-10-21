import pandas as pd, requests, datetime as dt
from streamlit.runtime.caching import cache_data
from io import StringIO
from config import CACHE_TTL_DAY

@cache_data(ttl=CACHE_TTL_DAY)
def load_team_xg():
    y = dt.date.today().year
    if dt.date.today().month < 7:
        y -= 1
    url = f"https://moneypuck.com/moneypuck/gameData/{y}-{y+1}.csv"
    df = pd.read_csv(StringIO(requests.get(url).text))
    df.columns = df.columns.str.lower()
    home = df[['hometeam','homexgoals','awayxgoals']]
    away = df[['awayteam','awayxgoals','homexgoals']]
    home.columns, away.columns = ['team','xgf','xga'], ['team','xgf','xga']
    t = pd.concat([home, away])
    g = t.groupby('team',as_index=False).mean()
    g['xg_diff'] = g['xgf'] - g['xga']
    return g

