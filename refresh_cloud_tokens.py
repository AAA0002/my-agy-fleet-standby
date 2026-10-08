#!/usr/bin/env python3
"""
refresh_cloud_tokens.py
=============================================================================
100% CLOUD-FIRST TELEGRAM MTPROTO TOKEN REFRESHER FOR MY AGY AI FLEET
=============================================================================
Runs on GitHub Actions, Render, Deno, or ephemeral cloud runners.
Connects briefly (3-5s per account) via MTProto to extract fresh 24h WebApp
initData session tokens for all 7 active bots:
  1. Stones Miners (@stoneswithestand_bot)
  2. MRG Miner (@mrgminerbot)
  3. AI Lab Robot (@AiLab_robot)
  4. UltraWallet (@UltrawalletTrade_Bot)
  5. ATF Miner (@ATF_AIRDROP_bot)
  6. FINVORA Web3 (@FINVORAWeb3bot)
  7. TurboGram V1 (@TurboGramV1_bot)

Pushes the extracted tokens directly to 5x Cloudflare Edge Workers & KV.
Eliminates ALL dependence on local VPS uptime!
"""

import os
import sys
import time
import json
import asyncio
import urllib.parse
import aiohttp
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import RequestWebViewRequest, RequestAppWebViewRequest
from telethon.tl.types import InputBotAppShortName

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

API_ID = int(os.getenv("TELEGRAM_API_ID") or os.getenv("API_ID", "37321306"))
API_HASH = os.getenv("TELEGRAM_API_HASH") or os.getenv("API_HASH", "5cd9e5bbfb572a4429a0c54774153b47")
REPORT_CHAT_ID = int(os.getenv("REPORT_CHAT_ID", "6727787768"))
CF_SECRET_KEY = os.getenv("CF_SECRET_KEY", "agy_cf_secret_7d36994e_2026")

CF_NODES = [
    "https://restore-agy.aaaai2.workers.dev",
    "https://restore-agy.aaa-bot.workers.dev",
    "https://restore-agy.aaa222.workers.dev",
    "https://restore-agy.agorameet.workers.dev",
    "https://restore-agy.aaaai.workers.dev"
]

# Bot Usernames & Referral Codes
STONES_BOT = "stoneswithestand_bot"
MRG_BOT = "mrgminerbot"
AILAB_BOT = "AiLab_robot"
ULTRAWALLET_BOT = "UltrawalletTrade_Bot"
ATF_BOT = "ATF_AIRDROP_bot"
FINVORA_BOT = "FINVORAWeb3bot"
TURBOGRAM_BOT = "TurboGramV1_bot"

STONES_REF = "r6727787768"
MRG_REF = "ref_IRN1G3XD"
AILAB_REF = "296852"
ULTRAWALLET_REF = "6727787768"
ATF_REF = "6727787768"
FINVORA_REF = "ref_TRX6727787768"
TURBOGRAM_REF = "r_3520c92b"


def load_accounts():
    """Loads accounts from accounts.json or environment."""
    acc_path = os.path.join(BASE_DIR, "accounts.json")
    if os.path.exists(acc_path):
        try:
            with open(acc_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading accounts.json: {e}")

    # Fallback to env var FLEET_ACCOUNTS_JSON
    raw_env = os.getenv("FLEET_ACCOUNTS_JSON")
    if raw_env:
        try:
            return json.loads(raw_env)
        except Exception as e:
            print(f"Error parsing FLEET_ACCOUNTS_JSON: {e}")

    return []


async def sync_tokens_to_edge(session: aiohttp.ClientSession, uid: str, name: str, tokens: dict):
    """Pushes extracted tokens to all 5 Cloudflare Edge Worker nodes."""
    payload = {
        "uid": str(uid),
        "account_id": str(uid),
        "name": name,
        **tokens
    }
    headers = {
        "Authorization": f"Bearer {CF_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    for cf_url in CF_NODES:
        try:
            async with session.post(f"{cf_url}/api/tokens", json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as r:
                if r.status in (200, 201):
                    print(f"  ✅ Synced to {cf_url.split('//')[1].split('.')[0]}")
        except Exception as e:
            print(f"  ⚠️ Sync note for {cf_url}: {e}")


async def extract_account_tokens(acc: dict, session: aiohttp.ClientSession):
    """Connects MTProto for a single account and extracts all 10 bot session links."""
    acc_name = acc.get("name", "Account")
    acc_uid = str(acc.get("user_id"))
    acc_sess = acc.get("session_string")
    if not acc_sess or acc.get("status") == "revoked":
        print(f"[{acc_name}] Skipping revoked or empty session.")
        return

    print(f"\n🚀 [{acc_name} (ID: {acc_uid})] Connecting MTProto to collect 24h session tokens...")
    cl = TelegramClient(StringSession(acc_sess), API_ID, API_HASH)
    try:
        await cl.connect()
        if not await cl.is_user_authorized():
            print(f"[{acc_name}] Session not authorized or revoked.")
            return

        tokens = {
            "account_id": acc_uid,
            "name": acc_name,
            "updated_at": time.time()
        }

        # 1. Stones Miners
        try:
            b_st = await cl.get_entity(STONES_BOT)
            r_st = await cl(RequestWebViewRequest(
                peer=b_st, bot=b_st, platform="android",
                url="https://app.stoneswithestand.my.id/",
                start_param=STONES_REF if acc_uid != str(REPORT_CHAT_ID) else None
            ))
            init_st = urllib.parse.parse_qs(urllib.parse.urlparse(r_st.url).fragment).get("tgWebAppData", [None])[0]
            if init_st:
                tokens["stones_init_data"] = init_st
                print(f"  💎 Stones Miners: Collected")
        except Exception as e:
            print(f"  ⚠️ Stones error: {e}")

        # 2. MRG Miner
        try:
            b_mrg = await cl.get_entity(MRG_BOT)
            r_mrg = await cl(RequestWebViewRequest(
                peer=b_mrg, bot=b_mrg, platform="android",
                url=f"https://mrg.up.railway.app/?ref={MRG_REF}",
                start_param=MRG_REF if acc_uid != str(REPORT_CHAT_ID) else None
            ))
            init_mrg = urllib.parse.parse_qs(urllib.parse.urlparse(r_mrg.url).fragment).get("tgWebAppData", [None])[0]
            if init_mrg:
                tokens["mrg_init_data"] = init_mrg
                print(f"  ⛏️ MRG Miner: Collected")
        except Exception as e:
            print(f"  ⚠️ MRG error: {e}")

        # 3. AI Lab Robot
        try:
            b_ai = await cl.get_entity(AILAB_BOT)
            r_ai = await cl(RequestWebViewRequest(
                peer=b_ai, bot=b_ai, platform="android",
                url=f"https://api.ailab-agent.online/?ref={AILAB_REF}",
                start_param=AILAB_REF if acc_uid != str(REPORT_CHAT_ID) else None
            ))
            init_ai = urllib.parse.parse_qs(urllib.parse.urlparse(r_ai.url).fragment).get("tgWebAppData", [None])[0]
            if init_ai:
                tokens["ailab_init_data"] = init_ai
                print(f"  🧪 AI Lab: Collected")
        except Exception as e:
            print(f"  ⚠️ AI Lab error: {e}")

        # 4. UltraWallet
        try:
            b_uw = await cl.get_entity(ULTRAWALLET_BOT)
            r_uw = await cl(RequestWebViewRequest(
                peer=b_uw, bot=b_uw, platform="android",
                url=f"https://wallet.trxvault.top/?ref={ULTRAWALLET_REF}",
                start_param=ULTRAWALLET_REF if acc_uid != str(REPORT_CHAT_ID) else None
            ))
            init_uw = urllib.parse.parse_qs(urllib.parse.urlparse(r_uw.url).fragment).get("tgWebAppData", [None])[0]
            if init_uw:
                tokens["ultrawallet_init_data"] = init_uw
                print(f"  💳 UltraWallet: Collected")
        except Exception as e:
            print(f"  ⚠️ UltraWallet error: {e}")

        # 5. ATF Miner
        try:
            b_atf = await cl.get_entity(ATF_BOT)
            r_atf = await cl(RequestWebViewRequest(
                peer=b_atf, bot=b_atf, platform="android",
                url=f"https://atfminers.asloni.online/miner/index.html?entry=bot_start&ref={ATF_REF}",
                start_param=ATF_REF if acc_uid != str(REPORT_CHAT_ID) else None
            ))
            init_atf = urllib.parse.parse_qs(urllib.parse.urlparse(r_atf.url).fragment).get("tgWebAppData", [None])[0]
            if init_atf:
                tokens["atf_init_data"] = init_atf
                print(f"  🪙 ATF Miner: Collected")
        except Exception as e:
            print(f"  ⚠️ ATF error: {e}")

        # 6. FINVORA Web3
        try:
            b_fin = await cl.get_entity(FINVORA_BOT)
            r_fin = await cl(RequestWebViewRequest(
                peer=b_fin, bot=b_fin, platform="android",
                url=f"https://finvora-production.up.railway.app/?ref={FINVORA_REF}",
                start_param=FINVORA_REF if acc_uid != str(REPORT_CHAT_ID) else None
            ))
            init_fin = urllib.parse.parse_qs(urllib.parse.urlparse(r_fin.url).fragment).get("tgWebAppData", [None])[0]
            if init_fin:
                tokens["finvora_init_data"] = init_fin
                print(f"  🌐 FINVORA Web3: Collected")
        except Exception as e:
            print(f"  ⚠️ FINVORA error: {e}")

        # 7. TurboGram V1
        try:
            b_tb = await cl.get_entity(TURBOGRAM_BOT)
            r_tb = await cl(RequestWebViewRequest(
                peer=b_tb, bot=b_tb, platform="android",
                url=f"https://turbo.tamimdev.dev/?ref={TURBOGRAM_REF}",
                start_param=TURBOGRAM_REF if acc_uid != str(REPORT_CHAT_ID) else None
            ))
            init_tb = urllib.parse.parse_qs(urllib.parse.urlparse(r_tb.url).fragment).get("tgWebAppData", [None])[0]
            if init_tb:
                tokens["turbogram_init_data"] = init_tb
                print(f"  🚀 TurboGram V1: Collected")
        except Exception as e:
            print(f"  ⚠️ TurboGram error: {e}")

        # Sync to Cloudflare Edge KV
        await sync_tokens_to_edge(session, acc_uid, acc_name, tokens)

    finally:
        try:
            await cl.disconnect()
        except Exception:
            pass


async def main():
    print("=" * 65)
    print("MY AGY AI — 100% CLOUD-FIRST TELEGRAM TOKEN REFRESHER")
    print("=" * 65)

    accounts = load_accounts()
    if not accounts:
        print("❌ No accounts found. Ensure accounts.json or FLEET_ACCOUNTS_JSON is set.")
        sys.exit(1)

    print(f"Found {len(accounts)} accounts in fleet.")

    async with aiohttp.ClientSession() as session:
        for idx, acc in enumerate(accounts, 1):
            try:
                await extract_account_tokens(acc, session)
                await asyncio.sleep(2.0)
            except Exception as e:
                print(f"Error processing account {acc.get('name')}: {e}")

    print("\n✅ All 24h WebApp tokens collected & pushed to 3x Cloudflare Nodes!")


if __name__ == "__main__":
    asyncio.run(main())
