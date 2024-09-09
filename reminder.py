import schedule
import time
from datetime import datetime
import requests
import json

LINE_CHANNEL_ACCESS_TOKEN = '8yPjgjTkeLBr3lqtcH1SRhICbGF/6V8dKeZlkzya5laBxzFqeRKDMcf587srPG3Nojf0byKyVMPMT7GtZsIKZznh3UWap+nl9uGkzs3iewqMV6m4MHC971XvvO047bf2xHzvwJRgOZz5z1/ah7nLVwdB04t89/1O/w1cDnyilFU='
LINE_USER_ID = '2006237184'

def send_reminder(remind_time, message):
    now = datetime.now()
    if remind_time <= now:
        send_message(LINE_USER_ID, message)

def send_message(to, text):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    
    data = {
        "to": to,
        "messages": [{
            "type": "text",
            "text": text
        }]
    }
    
    url = "https://api.line.me/v2/bot/message/push"
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.status_code

def check_reminders():
    # ここでリマインダーをデータベースやファイルから取得してチェック
    reminders = [("2024-08-01 13:00", "mtg")]  # 例として固定のリマインド設定
    for remind_time_str, message in reminders:
        remind_time = datetime.strptime(remind_time_str, "%Y-%m-%d %H:%M")
        send_reminder(remind_time, message)

# 1分ごとにリマインダーをチェック
schedule.every(1).minutes.do(check_reminders)

while True:
    schedule.run_pending()
    time.sleep(1)
