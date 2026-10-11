#!/usr/bin/env python3
"""
Dedicated Onboarding Runner for newly added accounts.
Executes the full 4-bot referral binding pipeline via login_account.bind_referrals:
1. MRG Miner (@mrgminerbot) -> /start ref_IRN1G3XD + WebApp verify + connect TON wallet
2. ATF Miner (@ATF_AIRDROP_bot) -> /start 6727787768 + WebApp login + sync TON wallet + claim
3. Victor's Company (@VictorsCompanybot) -> /start ref_A20AA96F18 + WebApp login
4. VyroDrop (@vyrodrop_bot) -> /start ref_myFjrqqE4WN_ + WebApp bootstrap
"""

import asyncio
import json
import os
import urllib.request
from telethon import TelegramClient
from telethon.sessions import StringSession
from login_account import bind_referrals, API_ID, API_HASH, save_accounts

UPSTASH_URL = os.getenv("UPSTASH_REDIS_REST_URL", "https://pleasant-locust-220893.upstash.io")
UPSTASH_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")
if not UPSTASH_TOKEN and os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if "UPSTASH_REDIS_REST_TOKEN" in line:
                UPSTASH_TOKEN = line.split("=", 1)[1].strip()

NEW_ACCOUNT_IDS = ["7749125802", "7954290138", "8841038141", "8975442879"]

def sync_account_to_upstash(acc):
    if not UPSTASH_URL or not UPSTASH_TOKEN:
        return
    uid = str(acc.get("user_id"))
    try:
        url = f"{UPSTASH_URL}/set/account:{uid}"
        req = urllib.request.Request(
            url,
            data=json.dumps(acc).encode("utf-8"),
            headers={"Authorization": f"Bearer {UPSTASH_TOKEN}", "Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            pass
        print(f"  ☁️ Synced account {uid} to Upstash Redis")
    except Exception as e:
        print(f"  ⚠️ Upstash sync error for {uid}: {e}")

async def run_onboard():
    if not os.path.exists("accounts.json"):
        print("❌ accounts.json not found!")
        return

    with open("accounts.json", "r", encoding="utf-8") as f:
        accounts = json.load(f)

    target_accs = [a for a in accounts if str(a.get("user_id")) in NEW_ACCOUNT_IDS]
    print(f"\n🚀 Starting full 7-bot referral onboarding for {len(target_accs)} target accounts...\n")

    for idx, acc in enumerate(target_accs, start=1):
        uid = str(acc.get("user_id"))
        phone = acc.get("phone")
        name = acc.get("name", "Worker")
        sess_str = acc.get("session_string")

        print(f"\n{'='*60}")
        print(f"[{idx}/{len(target_accs)}] ONBOARDING ACCOUNT: {name} ({phone}, ID: {uid})")
        print(f"{'='*60}")

        if not sess_str:
            print("  ❌ No session string found, skipping.")
            continue

        client = TelegramClient(StringSession(sess_str), API_ID, API_HASH)
        try:
            await client.connect()
            if not await client.is_user_authorized():
                print("  ❌ Session string is not authorized, skipping.")
                continue

            me = await client.get_me()
            print(f"  ✅ Connected as: {me.first_name} (@{me.username or 'None'})")

            # Execute full 15-bot binding
            await bind_referrals(client, me, acc)

            # Save progress locally and to Upstash Redis
            save_accounts(accounts)
            sync_account_to_upstash(acc)

        except Exception as e:
            print(f"  ❌ Error during onboarding {name}: {e}")
        finally:
            try:
                await client.disconnect()
            except Exception:
                pass

        await asyncio.sleep(2.0)

    print("\n🎉 ALL TARGET ACCOUNTS ONBOARDING COMPLETE!")

if __name__ == "__main__":
    asyncio.run(run_onboard())
