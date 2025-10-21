import os, requests
from config import TELEGRAM_BOT_TOKEN_ENV, TELEGRAM_CHAT_ID_ENV

def send_alert(msg:str):
    token = os.getenv(TELEGRAM_BOT_TOKEN_ENV)
    chat = os.getenv(TELEGRAM_CHAT_ID_ENV)
    if not token or not chat: return False
    url=f"https://api.telegram.org/bot{token}/sendMessage"
    r=requests.post(url,json={"chat_id":chat,"text":msg,"parse_mode":"HTML"})
    return r.ok


