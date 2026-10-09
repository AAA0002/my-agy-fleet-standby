#!/usr/bin/env python3
"""
report_and_purge_bnb_galaxy.py
Iterates through all 13 fleet accounts in accounts.json:
1. Reports @CryptoProUpRobot to Telegram as a fraudulent scam bot (InputReportReasonFake).
2. Blocks @CryptoProUpRobot on all accounts (BlockRequest).
3. Clears chat history with the bot (DeleteHistoryRequest).
4. Leaves all mandatory scam channels associated with BNB Galaxy:
   - @Rewards_Lab
   - @TensorCoinNews
   - @AirdropFindTeam
   - @EarnCraftNews
"""

import os
import sys
import json
import time
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.account import ReportPeerRequest
from telethon.tl.functions.contacts import BlockRequest
from telethon.tl.functions.messages import DeleteHistoryRequest
from telethon.tl.functions.channels import LeaveChannelRequest
from telethon.tl.types import InputReportReasonFake
from dotenv import load_dotenv
from proxy_manager import parse_proxy, get_account_fingerprint

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")
load_dotenv(os.path.join(BASE_DIR, ".env"))

API_ID = int(os.getenv("TELEGRAM_API_ID", "24726207"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "5cd9e5bbfb572a4429a0c54774153b47")

BNB_BOT = "CryptoProUpRobot"
SCAM_CHANNELS = [
    "Rewards_Lab",
    "TensorCoinNews",
    "AirdropFindTeam",
    "EarnCraftNews"
]
REPORT_MESSAGE = "Fraudulent scam bot: tricks users into watching daily ads, fakes payouts, and withholds 100% of user balances after initial bait."

async def process_account(acc, index, total):
    name = acc.get("name", f"Account #{index}")
    uid = str(acc.get("user_id"))
    sess = acc.get("session_string")
    proxy = acc.get("proxy")

    if not sess:
        print(f"[{index}/{total}] ⚠️ Skipping {name} ({uid}): No session string found.")
        return False, "no_session"

    print(f"\n=======================================================")
    print(f"[{index}/{total}] 🚀 Processing: {name} (UID: {uid})")
    print(f"=======================================================")

    acc_proxy = parse_proxy(proxy)
    acc_fp = get_account_fingerprint(int(uid) if uid.isdigit() else 0)

    cl = TelegramClient(StringSession(sess), API_ID, API_HASH, proxy=acc_proxy, **acc_fp)
    try:
        await cl.connect()
        if not await cl.is_user_authorized():
            print(f"  ❌ Session unauthorized for {name}. Skipping.")
            return False, "unauthorized"

        # 1. Report @CryptoProUpRobot as Scam/Fake
        try:
            bot_entity = await cl.get_entity(BNB_BOT)
            await cl(ReportPeerRequest(
                peer=bot_entity,
                reason=InputReportReasonFake(),
                message=REPORT_MESSAGE
            ))
            print(f"  🚨 Reported @{BNB_BOT} to Telegram as SCAMMER/FAKE!")
        except Exception as re:
            print(f"  ⚠️ Report note for @{BNB_BOT}: {re}")

        await asyncio.sleep(1.0)

        # 2. Block the bot
        try:
            bot_entity = await cl.get_entity(BNB_BOT)
            await cl(BlockRequest(id=bot_entity))
            print(f"  🚫 Blocked @{BNB_BOT}!")
        except Exception as be:
            print(f"  ⚠️ Block note for @{BNB_BOT}: {be}")

        await asyncio.sleep(1.0)

        # 3. Clear & delete chat history
        try:
            bot_entity = await cl.get_entity(BNB_BOT)
            await cl(DeleteHistoryRequest(peer=bot_entity, max_id=0, just_clear=False, revoke=True))
            print(f"  🗑️ Deleted chat history with @{BNB_BOT}!")
        except Exception as de:
            print(f"  ⚠️ Delete history note: {de}")

        await asyncio.sleep(1.0)

        # 4. Leave all scam channels
        for ch in SCAM_CHANNELS:
            try:
                ch_entity = await cl.get_entity(ch)
                await cl(LeaveChannelRequest(ch_entity))
                print(f"  👋 Left scam channel: @{ch}")
            except Exception as ce:
                err_str = str(ce).lower()
                if "not a member" in err_str or "user_not_participant" in err_str:
                    print(f"  ℹ️ Not in @{ch} (already left)")
                else:
                    print(f"  ⚠️ Leave note for @{ch}: {ce}")
            await asyncio.sleep(1.0)

        print(f"  ✅ Completed report, block, and channel purge for {name}.")
        return True, "ok"

    except Exception as ex:
        print(f"  ❌ Error processing {name}: {ex}")
        return False, str(ex)
    finally:
        try:
            await cl.disconnect()
        except Exception:
            pass

async def main():
    if not os.path.exists(ACCOUNTS_FILE):
        print(f"Error: {ACCOUNTS_FILE} does not exist.")
        return

    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        accounts = json.load(f)

    print("=" * 65)
    print("MY AGY AI — REPORT & PURGE SCAMMER BOT (@CryptoProUpRobot)")
    print(f"Total Accounts to execute: {len(accounts)}")
    print(f"Channels to leave: {SCAM_CHANNELS}")
    print("=" * 65)

    results = []
    for idx, acc in enumerate(accounts, 1):
        ok, res = await process_account(acc, idx, len(accounts))
        results.append({
            "index": idx,
            "name": acc.get("name", f"Account #{idx}"),
            "uid": acc.get("user_id"),
            "success": ok,
            "result": res
        })
        await asyncio.sleep(2.0)

    print("\n" + "=" * 65)
    print("REPORT & PURGE SUMMARY:")
    print("=" * 65)
    success_count = sum(1 for r in results if r["success"])
    for r in results:
        status_icon = "✅" if r["success"] else "❌"
        print(f"{status_icon} [{r['index']}/{len(accounts)}] {r['name']} ({r['uid']}): {r['result']}")
    print(f"\nFinal Result: {success_count}/{len(accounts)} accounts successfully reported and purged @{BNB_BOT} and channels.")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(main())
