import os
import time
import requests
from bs4 import BeautifulSoup
import discord
from discord import Intents
import smtplib
from email.mime.text import MIMEText

# ====== 安全寫法，從環境變數讀取 ======
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID"))
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")          # 你的 Gmail
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")  # Gmail App 密碼

CHECK_INTERVAL = 10  # 每隔多少秒檢查一次網站

# ====== 你要監控的網址列表 ======
URLS = [
    ("3/20 TWICE", "https://tixcraft.com/ticket/area/26_twice/21471"),
    ("3/21 TWICE", "https://tixcraft.com/ticket/area/26_twice/21441"),
    ("3/22 TWICE", "https://tixcraft.com/ticket/area/26_twice/21455")
]

intents = Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def send_email(subject, body):
    if not EMAIL_ADDRESS or not EMAIL_APP_PASSWORD:
        return
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = EMAIL_ADDRESS
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"Email 發送失敗: {e}")

def check_tickets():
    results = []
    for name, url in URLS:
        try:
            r = requests.get(url)
            soup = BeautifulSoup(r.text, 'html.parser')
            # 假設有票的區塊會有 'ticket-area' class
            areas = soup.select(".ticket-area")
            if areas:
                results.append(f"{name}: 有票 {', '.join([a.text.strip() for a in areas])}")
            else:
                results.append(f"{name}: 暫時沒有票")
        except Exception as e:
            results.append(f"{name}: 無法檢查 ({e})")
    return results

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    channel = client.get_guild(GUILD_ID).get_channel(CHANNEL_ID)
    await channel.send("💖 已啟動（Email 備援已開啟）")
    send_email("TixWatcher 已啟動", "程式已啟動並準備監控票務。")

    while True:
        ticket_status = check_tickets()
        for status in ticket_status:
            # @你通知
            await channel.send(f"<@1466727179256598569> {status}")
            send_email("票務更新", status)
        time.sleep(CHECK_INTERVAL)

client.run(TOKEN)