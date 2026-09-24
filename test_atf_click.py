import asyncio
import os
import urllib.parse
import aiohttp
import json
import random
from telethon import TelegramClient, functions
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv()
client = TelegramClient(StringSession(os.getenv("TELEGRAM_STRING_SESSION")), int(os.getenv("TELEGRAM_API_ID")), os.getenv("TELEGRAM_API_HASH"))

async def test():
    await client.connect()
    bot = await client.get_entity("AAAPREMIUMAPPSbot")
    res = await client(functions.messages.RequestWebViewRequest(
        peer=bot,
        bot=bot,
        url="https://atf-miner-app.pages.dev/app/ad/?user_id=6727787768&mode=unlimited&chain=20",
        platform="android"
    ))
    parsed = urllib.parse.urlparse(res.url)
    fragment = urllib.parse.parse_qs(parsed.fragment)
    init_data = fragment.get("tgWebAppData", [None])[0]

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"tma {init_data}" if init_data else "",
        "X-Telegram-Init-Data": init_data or "",
        "X-User-Id": "6727787768",
        "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36 Telegram-Android/11.0.0",
        "Referer": "https://atf-miner-app.pages.dev/",
        "Origin": "https://atf-miner-app.pages.dev"
    }

    url = "https://atf-miner-worker.agorameet.workers.dev/api/user/verify-ad-chain"

    async with aiohttp.ClientSession() as session:
        for i in range(2):
            watch_sec = round(random.uniform(16.8, 19.5), 2)
            print(f"[Test] Watching Ad {i+1} ({watch_sec}s)...")
            await asyncio.sleep(watch_sec)

            click_delay = round(random.uniform(1.2, 2.5), 2)
            print(f"[Test] Simulating Ad Click interaction ({click_delay}s)...")
            await asyncio.sleep(click_delay)

            payload = {
                "user_id": 6727787768,
                "initData": init_data or "",
                "unit_id": "11753248",
                "placement_id": "11753248",
                "platform": "monetag",
                "elapsed_seconds": watch_sec,
                "chain": 20,
                "mode": "unlimited",
                "clicked": True
            }

            async with session.post(url, json=payload, headers=headers) as resp:
                data = await resp.json()
                watched_count = data.get("ads_watched_today", "N/A")
                print(f"[Test] Ad {i+1} verified! Ads watched today: {watched_count}")

            if i < 1:
                await asyncio.sleep(3.0)

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(test())
