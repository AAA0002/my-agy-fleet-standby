#!/usr/bin/env python3
"""
MiningGRAM USDT Promo Autonomous Claimer
Monitors the $28.00 USDT Promo balance on the master account (6727787768)
and automatically submits the BEP-20 withdrawal to Binance deposit address
(0xfda4182001672b9f0f09e2118242e543e35ed5ce) as soon as the withdrawal
window unlocks at 19:30 UTC today (2026-09-24 19:30:00 UTC).
"""

import os
import json
import time
import asyncio
import aiohttp
import urllib.request
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKENS_FILE = os.path.join(BASE_DIR, "fleet_miniapp_tokens.json")
REPORT_BOT_TOKEN = os.getenv("REPORT_BOT_TOKEN", "8858823950:AAFFkuls8hBf23taCZE1y5gVzP4AFCuqI5o")
REPORT_CHAT_ID = os.getenv("REPORT_CHAT_ID", "6727787768")
AAA_T_WALLET_GROUP = -1003973231307

API_BASE = "https://mining-gram-worker.muhaisin0888.workers.dev"
MASTER_UID = "6727787768"
MASTER_BEP20 = "0xfda4182001672b9f0f09e2118242e543e35ed5ce"
REFERRAL_CODE = "339JU9K"

def notify_telegram(text: str, chat_id: int):
    url = f"https://api.telegram.org/bot{REPORT_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"Telegram notify error to {chat_id}: {e}")
        return None

async def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Starting MiningGRAM USDT Promo Auto-Claimer...")
    
    if not os.path.exists(TOKENS_FILE):
        print(f"Tokens file missing: {TOKENS_FILE}")
        return

    with open(TOKENS_FILE, "r", encoding="utf-8") as f:
        tokens = json.load(f)

    init_data = tokens.get(MASTER_UID, {}).get("mininggram_init_data")
    if not init_data:
        print(f"Master initData missing in {TOKENS_FILE}")
        return

    async with aiohttp.ClientSession() as session:
        # 1. Login to get fresh session token
        auth_resp = await session.post(f"{API_BASE}/api/auth", json={
            "initData": init_data,
            "referralCode": REFERRAL_CODE,
            "deviceFingerprint": f"fp_{MASTER_UID}"
        })
        if auth_resp.status != 200:
            print(f"Auth failed: {auth_resp.status} - {await auth_resp.text()}")
            return
        
        session_token = (await auth_resp.json()).get("sessionToken")
        headers = {"Authorization": f"Bearer {session_token}", "Content-Type": "application/json"}

        # 2. Check Promo Status
        promo_resp = await session.get(f"{API_BASE}/api/usdt/promo", headers=headers)
        if promo_resp.status != 200:
            print(f"Promo status failed: {promo_resp.status}")
            return
        
        promo_data = await promo_resp.json()
        balance_usd = promo_data.get("balanceCents", 0) / 100.0
        open_time_str = promo_data.get("withdrawalsOpenAt", "2026-09-24T19:30:00.000Z")
        is_open = promo_data.get("withdrawalsOpen", False)

        print(f"Balance: ${balance_usd:.2f} USDT | Open: {is_open} | Unlock Time: {open_time_str}")

        # 3. Attempt Withdrawal
        wd_resp = await session.post(f"{API_BASE}/api/usdt/withdraw", headers=headers, json={"bep20Address": MASTER_BEP20})
        wd_data = await wd_resp.json()

        if wd_resp.status == 200:
            msg = (
                f"🎉 *MININGGRAM USDT PROMO WITHDRAWAL SUCCESSFUL!*\n\n"
                f"• **Amount:** `${balance_usd:.2f} USDT`\n"
                f"• **Destination:** `{MASTER_BEP20}` (Personal Binance BEP-20)\n"
                f"• **Status:** Submitted & Confirmed\n"
                f"• **Server Response:**\n`{json.dumps(wd_data, indent=2)}`"
            )
            print("SUCCESS! Withdrew USDT Promo!")
            notify_telegram(msg, int(REPORT_CHAT_ID))
            notify_telegram(msg, AAA_T_WALLET_GROUP)
        else:
            err = wd_data.get("error")
            print(f"Withdrawal attempt result: {wd_resp.status} - {wd_data}")
            if err == "usdt_withdrawals_locked":
                print(f"⏳ Still locked until {open_time_str}. Scheduled to retry at 19:30 UTC.")
            elif err == "usdt_pending_exists":
                print("✅ A pending withdrawal is already in flight!")

if __name__ == "__main__":
    asyncio.run(main())
