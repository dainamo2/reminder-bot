import json
import requests
import hashlib
import hmac
import base64
import time
import redis
from datetime import datetime, timedelta
from flask import Flask, request, abort
import threading
import os

app = Flask(__name__)

# Redisの接続設定
REDIS_URL = os.getenv('REDIS_URL', 'redis://default:nm1Ok7WLMwEPxlWNhE5Al3EGJ1aMSLRo@redis-14909.c278.us-east-1-4.ec2.redns.redis-cloud.com:14909/0')
redis_client = redis.StrictRedis.from_url(REDIS_URL)

# LINE Developersの設定ページで取得したチャネルシークレットをここに入力
CHANNEL_SECRET = 'a1ddfdc8d553c13d65130d51f58d537e'
LINE_CHANNEL_ACCESS_TOKEN = '8yPjgjTkeLBr3lqtcH1SRhICbGF/6V8dKeZlkzya5laBxzFqeRKDMcf587srPG3Nojf0byKyVMPMT7GtZsIKZznh3UWap+nl9uGkzs3iewqMV6m4MHC971XvvO047bf2xHzvwJRgOZz5z1/ah7nLVwdB04t89/1O/w1cDnyilFU='

# 署名検証関数
def verify_signature(request):
    body = request.get_data(as_text=True)
    signature = request.headers.get('X-Line-Signature', '')

    hash = hmac.new(CHANNEL_SECRET.encode('utf-8'), body.encode('utf-8'), hashlib.sha256).digest()
    generated_signature = base64.b64encode(hash).decode('utf-8')

    return hmac.compare_digest(generated_signature, signature)

# メッセージ送信関数
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
    
    print(f"Message send status: {response.status_code}")
    print(f"Response: {response.text}")

# メッセージ送信を指定時刻に行う関数
def schedule_message(to, text, scheduled_time):
    time_diff = (scheduled_time - datetime.now()).total_seconds()

    if time_diff > 0:
        print(f"Message scheduled in {time_diff} seconds.")
        redis_client.set(f"reminder:{to}:{text}", text, ex=int(time_diff))
        threading.Timer(time_diff, send_message, args=[to, f"{text}だよ〜"]).start()
    else:
        send_message(to, "過去の時刻は指定できません。")

# 日時フォーマットのメッセージを処理する
def handle_reminder_message(user_id, text):
    try:
        now = datetime.now()

        # 日付を含むフォーマットの場合 (YYYYMMDDHHMM)
        if len(text) >= 12 and text[:12].isdigit():
            datetime_str, message = text.split("\n", 1)
            scheduled_time = datetime.strptime(datetime_str, "%Y%m%d%H%M")

        # 月日を含むフォーマットの場合 (MMDDHHMM)
        elif len(text) >= 8 and text[:8].isdigit():
            datetime_str, message = text.split("\n", 1)
            scheduled_time = datetime(now.year, int(datetime_str[:2]), int(datetime_str[2:4]), int(datetime_str[4:6]), int(datetime_str[6:8]))

        # 時間だけを指定した場合 (HHMM)
        elif len(text) >= 4 and text[:4].isdigit():
            time_str, message = text.split("\n", 1)
            scheduled_time = datetime(now.year, now.month, now.day, int(time_str[:2]), int(time_str[2:4]))

        # 過去の時間か確認
        if scheduled_time < now:
            send_message(user_id, "過去の時刻は指定できません。")
            return

        # メッセージを指定された日時に送信
        schedule_message(user_id, message, scheduled_time)

        # ユーザーにリマインダー設定が成功したことを知らせる
        send_message(user_id, f"リマインダーを {scheduled_time.strftime('%Y-%m-%d %H:%M')} に設定したよ！")
    except ValueError:
        # フォーマットが違う場合のエラーメッセージ
        send_message(user_id, "リマインダーのフォーマットが正しくありません。'YYYYMMDDHHMM\\nメッセージ' または 'HHMM\\nメッセージ' の形式で送信してください。")

@app.route("/webhook", methods=['POST'])
def webhook():
    if not verify_signature(request):
        abort(403)

    body = request.get_json()

    events = body.get('events', [])
    for event in events:
        if event['type'] == 'message':
            user_id = event['source']['userId']
            text = event['message']['text']
            print(f"Message from {user_id}: {text}")

            # 日時フォーマットかどうかを判別し、リマインダー処理
            if len(text) >= 4 and '\n' in text:
                handle_reminder_message(user_id, text)
            else:
                send_message(user_id, f"正しく入力してね。\nサンプル:\n202402031930\nAちゃんと飲み会")

    return "OK", 200

if __name__ == "__main__":
    app.run(port=8000, debug=True)
