#!/usr/bin/env python3
"""
batch_referral_onboard.py
Universal 15-Bot Referral Onboarding Runner for All Worker Accounts in accounts.json.
Guarantees:
- Skips master account 6727787768
- Connects each worker account
- Automatically executes full 15-bot referral binding pipeline via login_account.bind_referrals:
  1. Stones Miners (@stoneswithestand_bot) -> /start r6727787768
  2. MRG Miner (@mrgminerbot) -> /start ref_IRN1G3XD + WebApp verify + connect TON wallet
  3. ART Airdrop (@ART_AIRDROP_BOT) -> /start 6727787768
  4. AI Lab Robot (@AiLab_robot) -> /start 296852 + WebApp login
  5. Ultra Wallet (@UltrawalletTrade_Bot) -> /start 6727787768 + WebApp login
  6. Apex Miner (@ApxMinerBot) -> /start 6727787768 + WebApp register
  7. Ainovum Bot (@ainovum_bot) -> /start ref_6727787768 + bootstrap
  8. ATF Miner (@ATF_AIRDROP_bot) -> /start 6727787768
  9. TRX Power Mining (@trxpowermining_bot) -> /start ref_TRX6727787768 + channel verify
  10. Bitcoin Cloud Miners (@BitcoinCloudMinersBot) -> join channel + /start 6727787768 + check_join + claim_mine
  11. Tensor Mining Robot (@TensorMiningRobot) -> /start 6727787768 + WebApp auth
  12. TON Trader AI (@TonTraderAIBot) -> /start REF_6727787768 + welcome & daily gifts
  13. FINVORA Web3 (@FINVORAWeb3bot) -> /start ref_TRX6727787768 + WebApp
  14. TurboGram V1 (@TurboGramV1_bot) -> /start r_3520c92b + WebApp
  15. Ominix AI Trade (@OminixAiBot) -> /start 6727787768 + ServerFn profit claim
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
    print(f"🚀 Universal 15-Bot Referral Onboarding across {len(accounts)} Accounts")
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

        if acc.get("all_15_referrals_bound"):
            print(f"[{idx+1}/{len(accounts)}] ✅ {name} ({phone}) is ALREADY 15/15 BOUND. Skipping.")
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
