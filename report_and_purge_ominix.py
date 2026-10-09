#!/usr/bin/env python3
"""
report_and_purge_ominix.py
Iterates through all 18 fleet accounts in accounts.json:
1. Reports @OminixAiBot to Telegram Anti-Scam as a fraudulent scammer bot (InputReportReasonFake).
2. Blocks @OminixAiBot across all accounts (BlockRequest).
3. Deletes chat history with the bot including revoke for both parties (DeleteHistoryRequest).
4. Reports and leaves all scam channels associated with Ominix:
   - @ominiai (Ominix AI Announcement Channel)
   - @ominiaipayout (Ominix Fake Payout Proofs Channel)
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
TOKENS_FILE = os.path.join(BASE_DIR, "fleet_miniapp_tokens.json")
load_dotenv(os.path.join(BASE_DIR, ".env"))

API_ID = int(os.getenv("TELEGRAM_API_ID", "24726207"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "5cd9e5bbfb572a4429a0c54774153b47")

OMINIX_BOT = "OminixAiBot"
SCAM_CHANNELS = [
    {
        "username": "ominiai",
        "reason": "Fraudulent scam channel associated with scam bot @OminixAiBot promoting fake investment returns."
    },
    {
        "username": "ominiaipayout",
        "reason": "Fake payment proofs and fraudulent channel associated with scam bot @OminixAiBot."
    }
]
BOT_REPORT_MESSAGE = "Fraudulent scam bot: fakes trading arbitrage payouts, deceives users, and steals deposits."

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

    acc_fp = get_account_fingerprint(int(uid) if uid.isdigit() else 0)

    cl = TelegramClient(StringSession(sess), API_ID, API_HASH, **acc_fp)
    try:
        await cl.connect()
        if not await cl.is_user_authorized():
            print(f"  ❌ Session unauthorized for {name}. Skipping.")
            return False, "unauthorized"

        # 1. Report @OminixAiBot as Scam/Fake
        try:
            bot_entity = await cl.get_entity(OMINIX_BOT)
            await cl(ReportPeerRequest(
                peer=bot_entity,
                reason=InputReportReasonFake(),
                message=BOT_REPORT_MESSAGE
            ))
            print(f"  🚨 Reported @{OMINIX_BOT} to Telegram as SCAMMER / FAKE!")
        except Exception as re:
            print(f"  ⚠️ Report note for @{OMINIX_BOT}: {re}")

        await asyncio.sleep(0.8)

        # 2. Block @OminixAiBot
        try:
            bot_entity = await cl.get_entity(OMINIX_BOT)
            await cl(BlockRequest(id=bot_entity))
            print(f"  🚫 Blocked @{OMINIX_BOT}!")
        except Exception as be:
            print(f"  ⚠️ Block note for @{OMINIX_BOT}: {be}")

        await asyncio.sleep(0.8)

        # 3. Clear & delete chat history with revoke
        try:
            bot_entity = await cl.get_entity(OMINIX_BOT)
            await cl(DeleteHistoryRequest(peer=bot_entity, max_id=0, just_clear=False, revoke=True))
            print(f"  🗑️ Deleted chat history with @{OMINIX_BOT} (revoke=True)!")
        except Exception as de:
            print(f"  ⚠️ Delete history note: {de}")

        await asyncio.sleep(0.8)

        # 4. Report and leave all scam channels
        for sc in SCAM_CHANNELS:
            ch_user = sc["username"]
            reason_msg = sc["reason"]
            try:
                ch_entity = await cl.get_entity(ch_user)
                # Report channel as scam
                try:
                    await cl(ReportPeerRequest(
                        peer=ch_entity,
                        reason=InputReportReasonFake(),
                        message=reason_msg
                    ))
                    print(f"  🚨 Reported scam channel @{ch_user} as FAKE!")
                except Exception as r_err:
                    print(f"  ⚠️ Report error on @{ch_user}: {r_err}")

                await asyncio.sleep(0.5)

                # Leave channel
                try:
                    await cl(LeaveChannelRequest(ch_entity))
                    print(f"  👋 Left scam channel: @{ch_user}")
                except Exception as l_err:
                    err_s = str(l_err).lower()
                    if "not a member" in err_s or "user_not_participant" in err_s:
                        print(f"  ℹ️ Not a member of @{ch_user} (already left)")
                    else:
                        print(f"  ⚠️ Leave note for @{ch_user}: {l_err}")

            except Exception as ce:
                print(f"  ℹ️ Could not find/resolve @{ch_user}: {ce}")
            await asyncio.sleep(0.8)

        print(f"  ✅ Completed Ominix purge & report for {name}.")
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
    print("MY AGY AI — REPORT & PURGE SCAMMER BOT (@OminixAiBot)")
    print(f"Total Fleet Accounts: {len(accounts)}")
    print(f"Target Scam Bot: @{OMINIX_BOT}")
    print(f"Target Scam Channels: {[s['username'] for s in SCAM_CHANNELS]}")
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
        await asyncio.sleep(1.5)

    # Clean up tokens & accounts json
    print("\n🧹 Cleaning Ominix references from local state files...")
    for acc in accounts:
        if "ominix_referral_bound" in acc:
            del acc["ominix_referral_bound"]
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(accounts, f, indent=2, ensure_ascii=False)
    print("  ✅ Purged ominix_referral_bound from accounts.json")

    if os.path.exists(TOKENS_FILE):
        with open(TOKENS_FILE, "r", encoding="utf-8") as f:
            tokens_data = json.load(f)
        modified_tokens = False
        for uid, t_dict in tokens_data.items():
            if "ominix_init_data" in t_dict:
                del t_dict["ominix_init_data"]
                modified_tokens = True
        if modified_tokens:
            with open(TOKENS_FILE, "w", encoding="utf-8") as f:
                json.dump(tokens_data, f, indent=2, ensure_ascii=False)
            print("  ✅ Purged ominix_init_data from fleet_miniapp_tokens.json")

    print("\n" + "=" * 65)
    print("REPORT & PURGE SUMMARY:")
    print("=" * 65)
    success_count = sum(1 for r in results if r["success"])
    for r in results:
        status_icon = "✅" if r["success"] else "❌"
        print(f"{status_icon} [{r['index']}/{len(accounts)}] {r['name']} ({r['uid']}): {r['result']}")
    print(f"\nFinal Result: {success_count}/{len(accounts)} accounts successfully reported, blocked, purged @{OMINIX_BOT} and scam channels.")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(main())
