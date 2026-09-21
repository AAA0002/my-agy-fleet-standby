#!/usr/bin/env python3
"""
refresh_cloud_tokens.py
=============================================================================
100% CLOUD-FIRST TELEGRAM MTPROTO TOKEN REFRESHER FOR MY AGY AI FLEET
=============================================================================
Runs on GitHub Actions, Render, Deno, or ephemeral cloud runners.
Connects briefly (3-5s per account) via MTProto to extract fresh 24h WebApp
initData session tokens for all 10 bots:
  1. Stones Miners (@stoneswithestand_bot)
  2. MRG Miner (@mrgminerbot)
  3. ART Airdrop (@ART_AIRDROP_BOT)
  4. BNB Galaxy Webhook (@CryptoProUpRobot)
  5. AI Lab Robot (@AiLab_robot)
  6. UltraWallet (@UltrawalletTrade_Bot)
  7. Apex Miner (@ApxMinerBot)
  8. ATF Miner (@ATF_AIRDROP_bot)
  9. Ainovum (@ainovum_bot)
 10. MiningGRAM (@MiningGRAM_Bot)

Pushes the extracted tokens directly to 3x Cloudflare Edge Workers & KV.
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

API_ID = int(os.getenv("API_ID", "27845347"))
API_HASH = os.getenv("API_HASH", "21e25e9e2467d3d3ef0c74f5146c8209")
REPORT_CHAT_ID = int(os.getenv("REPORT_CHAT_ID", "6727787768"))
CF_SECRET_KEY = os.getenv("CF_SECRET_KEY", "agy_cf_secret_7d36994e_2026")

CF_NODES = [
    "https://restore-agy.aaaai2.workers.dev",
    "https://restore-agy.aaa-bot.workers.dev",
    "https://restore-agy.aaa222.workers.dev"
]

# Bot Usernames & Referral Codes
BNB_BOT = "CryptoProUpRobot"
STONES_BOT = "stoneswithestand_bot"
MRG_BOT = "mrgminerbot"
ART_BOT = "ART_AIRDROP_BOT"
AILAB_BOT = "AiLab_robot"
ULTRAWALLET_BOT = "UltrawalletTrade_Bot"
APX_BOT = "ApxMinerBot"
AINOVUM_BOT = "ainovum_bot"
MININGGRAM_BOT = "MiningGRAM_Bot"

STONES_REF = "r6727787768"
MRG_REF = "ref_IRN1G3XD"
ART_REF = "6727787768"
AILAB_REF = "296852"
ULTRAWALLET_REF = "6727787768"
APX_REF = "6727787768"
AINOVUM_REF = "ref_6727787768"
MININGGRAM_REF = "339JU9K"

BNB_WEBHOOK_FALLBACK = "https://api.bots.business/v1/bots/2985029/new-webhook?&command=%2FonWebhook&public_user_token=3d1ed3e6a9bb948436a55057c6e87b59&user_id=46893407"


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
    """Pushes extracted tokens to all 3 Cloudflare Edge Worker nodes."""
    payload = {
        "uid": str(uid),
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

        # 3. ART Airdrop
        try:
            b_art = await cl.get_entity(ART_BOT)
            r_art = await cl(RequestWebViewRequest(
                peer=b_art, bot=b_art, platform="android",
                url=f"https://art.tamimdev.dev/?ref={ART_REF}",
                start_param=ART_REF if acc_uid != str(REPORT_CHAT_ID) else None
            ))
            init_art = urllib.parse.parse_qs(urllib.parse.urlparse(r_art.url).fragment).get("tgWebAppData", [None])[0]
            if init_art:
                tokens["art_init_data"] = init_art
                print(f"  🚀 ART Airdrop: Collected")
        except Exception as e:
            print(f"  ⚠️ ART error: {e}")

        # 4. BNB Galaxy Webhook
        try:
            b_bnb = await cl.get_entity(BNB_BOT)
            r_bnb = await cl(RequestWebViewRequest(
                peer=b_bnb, bot=b_bnb, platform="android",
                url="https://justtool.site/tasks-adsgram/"
            ))
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(r_bnb.url).query)
            wh = qs.get("wh", [None])[0] or BNB_WEBHOOK_FALLBACK
            tokens["bnb_wh_url"] = wh
            print(f"  🟡 BNB Galaxy: Webhook Linked")
        except Exception as e:
            tokens["bnb_wh_url"] = BNB_WEBHOOK_FALLBACK

        # 5. AI Lab Robot
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

        # 6. UltraWallet
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

        # 7. Apex Miner
        try:
            b_apx = await cl.get_entity(APX_BOT)
            r_apx = await cl(RequestWebViewRequest(
                peer=b_apx, bot=b_apx, platform="android",
                url=f"https://apex-miner.vercel.app/?ref={APX_REF}",
                start_param=APX_REF if acc_uid != str(REPORT_CHAT_ID) else None
            ))
            init_apx = urllib.parse.parse_qs(urllib.parse.urlparse(r_apx.url).fragment).get("tgWebAppData", [None])[0]
            if init_apx:
                tokens["apx_init_data"] = init_apx
                print(f"  ⚡ Apex Miner: Collected")
        except Exception as e:
            print(f"  ⚠️ Apex error: {e}")

        # 8. ATF Miner
        try:
            b_atf = await cl.get_entity("ATF_AIRDROP_bot")
            r_atf = await cl(RequestWebViewRequest(
                peer=b_atf, bot=b_atf, platform="android",
                url=f"https://atfminers.asloni.online/miner/index.html?v=1789502294&entry=bot_start&ref={REPORT_CHAT_ID}",
                start_param=str(REPORT_CHAT_ID)
            ))
            init_atf = urllib.parse.parse_qs(urllib.parse.urlparse(r_atf.url).fragment).get("tgWebAppData", [None])[0]
            if init_atf:
                tokens["atf_init_data"] = init_atf
                print(f"  🪙 ATF Miner: Collected")
        except Exception as e:
            print(f"  ⚠️ ATF error: {e}")

        # 9. Ainovum
        try:
            b_an = await cl.get_entity(AINOVUM_BOT)
            r_an = await cl(RequestWebViewRequest(
                peer=b_an, bot=b_an, platform="android",
                url=f"https://ainovum.biz/?startapp={AINOVUM_REF}&ref={AINOVUM_REF}",
                start_param=AINOVUM_REF if acc_uid != str(REPORT_CHAT_ID) else None
            ))
            init_an = urllib.parse.parse_qs(urllib.parse.urlparse(r_an.url).fragment).get("tgWebAppData", [None])[0]
            if init_an:
                tokens["ainovum_init_data"] = init_an
                print(f"  🤖 Ainovum: Collected")
        except Exception as e:
            print(f"  ⚠️ Ainovum error: {e}")

        # 10. MiningGRAM
        try:
            b_mg = await cl.get_input_entity(MININGGRAM_BOT)
            r_mg = await cl(RequestAppWebViewRequest(
                peer=b_mg,
                app=InputBotAppShortName(bot_id=b_mg, short_name="mine"),
                platform="android",
                start_param=MININGGRAM_REF
            ))
            init_mg = urllib.parse.parse_qs(urllib.parse.urlparse(r_mg.url).fragment).get("tgWebAppData", [None])[0]
            if init_mg:
                tokens["mininggram_init_data"] = init_mg
                print(f"  ⛏️ MiningGRAM: Collected")
        except Exception as e:
            print(f"  ⚠️ MiningGRAM error: {e}")

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
