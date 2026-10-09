#!/usr/bin/env python3
"""
batch_referral_onboard.py
Universal 4-Bot Referral Onboarding Runner for All Worker Accounts in accounts.json.
Guarantees:
- Skips master account 6727787768
- Connects each worker account
- Automatically executes full 4-bot referral binding pipeline via login_account.bind_referrals:
  1. MRG Miner (@mrgminerbot) -> /start ref_IRN1G3XD + WebApp verify + connect TON wallet
  2. ATF Miner (@ATF_AIRDROP_bot) -> /start 6727787768 + WebApp login + sync TON wallet + claim
  3. Victor's Company (@VictorsCompanybot) -> /start ref_A20AA96F18 + WebApp login
  4. VyroDrop (@vyrodrop_bot) -> /start ref_myFjrqqE4WN_ + WebApp bootstrap
"""

import os
import json
import time
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from login_account import bind_referrals, API_ID, API_HASH, save_accounts

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")
PRIMARY_CHAT_ID = "6727787768"

async def run_batch():
    if not os.path.exists(ACCOUNTS_FILE):
        print(f"❌ {ACCOUNTS_FILE} not found!")
        return

    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        accounts = json.load(f)

    print(f"\n============================================================")
    print(f"🚀 Universal 4-Bot Referral Onboarding across {len(accounts)} Accounts")
    print(f"============================================================\n")

    for idx, acc in enumerate(accounts):
        uid = str(acc.get("user_id"))
        name = acc.get("name", f"Account #{idx+1}")
        phone = acc.get("phone", "Unknown")
        sess = acc.get("session_string")

        if uid == PRIMARY_CHAT_ID or acc.get("is_referral_host"):
            print(f"[{idx+1}/{len(accounts)}] Skipping Primary Host Account: {name} (ID: {uid})")
            continue

        if not sess:
            print(f"[{idx+1}/{len(accounts)}] ⚠️ No session string for {name}, skipping.")
            continue

        if acc.get("all_4_referrals_bound") or acc.get("all_7_referrals_bound"):
            print(f"[{idx+1}/{len(accounts)}] ✅ {name} ({phone}) is ALREADY 4/4 BOUND. Skipping.")
            continue

        print(f"\n[{idx+1}/{len(accounts)}] Onboarding Worker: {name} ({phone}, ID: {uid})...")
        client = TelegramClient(StringSession(sess), API_ID, API_HASH)
        try:
            await client.connect()
            if not await client.is_user_authorized():
                print(f"  ❌ Unauthorized session for {name}, skipping.")
                continue

            me = await client.get_me()
            await bind_referrals(client, me, acc)
            save_accounts(accounts)

        except Exception as e:
            print(f"  ❌ Error for {name}: {e}")
        finally:
            try:
                await client.disconnect()
            except Exception:
                pass

        await asyncio.sleep(2.0)

    save_accounts(accounts)
    print("\n🎉 ALL FLEET WORKER ACCOUNTS PROCESSED & VERIFIED!")

def main():
    asyncio.run(run_batch())

if __name__ == "__main__":
    main()
