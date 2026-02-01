# ====== 設定區 (雲端部署用，TOKEN 和 EMAIL 密碼從環境變數讀取) ======
import os

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
USER_ID = int(os.getenv("DISCORD_USER_ID"))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 60))  # 預設 60 秒

EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")

WATCH_LIST = {
    "TWICE 3/20": "https://tixcraft.com/ticket/area/26_twice/21471",
    "TWICE 3/21": "https://tixcraft.com/ticket/area/26_twice/21441",
    "CxM 4/26": "https://tixcraft.com/ticket/area/26_cxm/21672",
}
# ========================================================================

import discord
import asyncio
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText

intents = discord.Intents.default()
intents.guilds = True
bot = discord.Client(intents=intents)

notified = set()

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def send_email(subject, body):
    if not EMAIL_FROM or not EMAIL_APP_PASSWORD or not EMAIL_TO:
        print("⚠️ Email 尚未設定，跳過寄送")
        return
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = EMAIL_FROM
        msg["To"] = EMAIL_TO

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_FROM, EMAIL_APP_PASSWORD)
            server.send_message(msg)

        print("📧 Email 已寄出")
    except Exception as e:
        print("Email 發送失敗：", e)

def fetch_available_areas(url):
    r = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    areas = []
    rows = soup.find_all(["li", "tr"])
    for row in rows:
        text = row.get_text(strip=True)
        if not text or len(text) < 3:
            continue
        if "售完" not in text and ("區" in text or "座" in text):
            areas.append(text)
    return list(set(areas))

@bot.event
async def on_ready():
    print(f"✅ Bot 已登入：{bot.user}")
    channel = bot.get_channel(CHANNEL_ID)

    await channel.send("🤖 拓元監控 Bot 已啟動（Email 備援已開啟）")

    while True:
        for show, url in WATCH_LIST.items():
            try:
                areas = fetch_available_areas(url)
                for area in areas:
                    key = f"{show}-{area}"
                    if key not in notified:
                        discord_msg = (
                            f"<@{USER_ID}> 🎟️ **有票警報！**\n"
                            f"🎤 {show}\n"
                            f"📍 區域：{area}\n"
                            "👉 立刻打開拓元搶票！"
                        )
                        await channel.send(discord_msg)

                        email_subject = f"【有票通知】{show}"
                        email_body = f"{show}\n區域：{area}\n\n快去拓元搶票！"
                        send_email(email_subject, email_body)

                        notified.add(key)
            except Exception as e:
                print(f"{show} 檢查錯誤：", e)

        await asyncio.sleep(CHECK_INTERVAL)

bot.run(TOKEN)

