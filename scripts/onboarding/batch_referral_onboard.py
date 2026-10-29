#!/usr/bin/env python3
"""
batch_referral_onboard.py
Universal 8-Bot Referral Onboarding Runner for All Worker Accounts in accounts.json.
Guarantees:
- Skips master account 6727787768
- Connects each worker account
- Automatically executes full 8-bot referral binding pipeline via login_account.bind_referrals:
  1. MRG Miner (@mrgtoken_bot)
  2. ATF Miner (@atfminers_bot)
  3. Victor's Company (@VictorsCompanybot)
  4. Kynex Network (@Kynex_miningbot)
  5. PepeGram (@Pepe_gram_bot)
  6. AdxEarn AI (@AdxEarnAibot)
  7. DiggoMiner (@Diggominer_bot)
  8. Chicken Land (@ChickenLandBot)
"""

import os
import json
import time
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from login_account import bind_referrals, API_ID, API_HASH, save_accounts

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
ACCOUNTS_FILE = os.getenv("ACCOUNTS_FILE") or os.path.join(PROJECT_ROOT, "accounts.json")
if not os.path.exists(ACCOUNTS_FILE):
    ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")
PRIMARY_CHAT_ID = "6727787768"

async def run_batch():
    if not os.path.exists(ACCOUNTS_FILE):
        print(f"❌ {ACCOUNTS_FILE} not found!")
        return

    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        accounts = json.load(f)

    print(f"\n============================================================")
    print(f"🚀 Universal 8-Bot Referral Onboarding across {len(accounts)} Accounts")
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

        if acc.get("all_8_referrals_bound") or acc.get("referrals_bound"):
            print(f"[{idx+1}/{len(accounts)}] ✅ {name} ({phone}) is ALREADY 8/8 BOUND. Skipping.")
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
