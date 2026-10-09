#!/usr/bin/env python3
"""
refresh_cloud_tokens.py
=============================================================================
100% CLOUD-FIRST TELEGRAM MTPROTO TOKEN REFRESHER FOR MY AGY AI FLEET
=============================================================================
Runs on GitHub Actions, Render, Deno, or ephemeral cloud runners.
Connects briefly via MTProto to extract fresh 24h WebApp initData session tokens
across all 9 legitimate active bots and auto-joins required sponsor channels.

Pushes extracted tokens to both:
  1. 5x Cloudflare Edge Workers & KV
  2. Upstash Serverless Redis REST (`fleet:tokens:{uid}` & `fleet_miniapp_tokens`)

Eliminates all dependence on local VPS uptime! Zero Phone Load.
"""

import os
import sys
import time
import json
import asyncio
import urllib.parse
import aiohttp
from telethon import TelegramClient, functions
from telethon.sessions import StringSession
from telethon.tl.functions.messages import RequestWebViewRequest, RequestAppWebViewRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import InputBotAppShortName

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

API_ID = int(os.getenv("TELEGRAM_API_ID") or os.getenv("API_ID", "37321306"))
API_HASH = os.getenv("TELEGRAM_API_HASH") or os.getenv("API_HASH", "5cd9e5bbfb572a4429a0c54774153b47")
REPORT_CHAT_ID = int(os.getenv("REPORT_CHAT_ID", "6727787768"))
CF_SECRET_KEY = os.getenv("CF_SECRET_KEY", "agy_cf_secret_7d36994e_2026")

UPSTASH_URL = os.getenv("UPSTASH_URL") or "https://relaxing-starfish-285827.upstash.io"
UPSTASH_TOKEN = os.getenv("UPSTASH_TOKEN") or "gQAAAAAABFyDAAIgcDI5MDYyYWZjNzYzNzk0ZmRjYjhmNTA4ZDI4ODlmODkzNw"

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
VICTORS_BOT = "VictorsCompanybot"
VYRO_BOT = "vyrodrop_bot"

STONES_REF = "r6727787768"
MRG_REF = "ref_IRN1G3XD"
AILAB_REF = "296852"
ULTRAWALLET_REF = "6727787768"
ATF_REF = "6727787768"
FINVORA_REF = "ref_TRX6727787768"
TURBOGRAM_REF = "r_3520c92b"
VICTORS_REF = "ref_A20AA96F18"
VYRO_REF = "ref_myFjrqqE4WN_"

MANDATORY_SPONSOR_CHANNELS = [
    "finvoraweb3",
    "TurboGramAnnouncements",
    "stoneswithestand",
    "mrgminer", "mrgwithdrawal", "DurovKidney",
    "ailabrobotnews",
    "ultrawalletofficial",
    "VictorsCompany",
    "vyrodrop",
    "atfminers"
]


def load_accounts():
    """Loads accounts from accounts.json or environment."""
    acc_path = os.path.join(BASE_DIR, "accounts.json")
    if os.path.exists(acc_path):
        try:
            with open(acc_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading accounts.json: {e}")

    raw_env = os.getenv("FLEET_ACCOUNTS_JSON")
    if raw_env:
        try:
            return json.loads(raw_env)
        except Exception as e:
            print(f"Error parsing FLEET_ACCOUNTS_JSON: {e}")

    return []


async def sync_tokens_to_edge_and_upstash(session: aiohttp.ClientSession, uid: str, name: str, tokens: dict):
    """Pushes extracted tokens to both 5x Cloudflare Edge Workers and Upstash Redis."""
    payload = {
        "uid": str(uid),
        "account_id": str(uid),
        "name": name,
        "synced_at": time.time(),
        "updated_at": time.time(),
        **tokens
    }

    # 1. Cloudflare Edge Workers
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

    # 2. Upstash Redis REST
    if UPSTASH_URL and UPSTASH_TOKEN:
        try:
            ex_toks = {}
            async with session.get(
                f"{UPSTASH_URL}/get/fleet:tokens:{uid}",
                headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"},
                timeout=aiohttp.ClientTimeout(total=5)
            ) as r_ex:
                if r_ex.status == 200:
                    ex_d = await r_ex.json()
                    raw_res = ex_d.get("result")
                    if raw_res:
                        ex_toks = json.loads(raw_res) if isinstance(raw_res, str) else raw_res

            merged = {**ex_toks, **payload}
            await session.post(
                f"{UPSTASH_URL}/set/fleet:tokens:{uid}",
                data=json.dumps(merged),
                headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"},
                timeout=aiohttp.ClientTimeout(total=5)
            )
            print(f"  ✅ Synced to Upstash Redis (fleet:tokens:{uid})")

            # Also update batch fleet_miniapp_tokens dictionary
            try:
                batch_dict = {}
                async with session.get(
                    f"{UPSTASH_URL}/get/fleet_miniapp_tokens",
                    headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as r_b:
                    if r_b.status == 200:
                        bd = await r_b.json()
                        raw_b = bd.get("result")
                        if raw_b:
                            batch_dict = json.loads(raw_b) if isinstance(raw_b, str) else raw_b
                batch_dict[str(uid)] = merged
                await session.post(
                    f"{UPSTASH_URL}/set/fleet_miniapp_tokens",
                    data=json.dumps(batch_dict),
                    headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"},
                    timeout=aiohttp.ClientTimeout(total=5)
                )
            except Exception:
                pass
        except Exception as ue:
            print(f"  ⚠️ Upstash sync note: {ue}")


async def extract_bot_webapp_token(client: TelegramClient, bot_username: str, start_param: str = "", default_url: str = "", candidate_short_names: list = None) -> str:
    """Universal 4-strategy resilient token extractor."""
    if not bot_username:
        return None

    def extract_from_url(url_str):
        if not url_str:
            return None
        try:
            p = urllib.parse.urlparse(str(url_str))
            frag = urllib.parse.parse_qs(p.fragment).get("tgWebAppData", [None])[0]
            if frag:
                if frag.startswith("user%3D") or "%257B" in frag or "%2522" in frag:
                    frag = urllib.parse.unquote(frag)
                return frag
            query = urllib.parse.parse_qs(p.query).get("tgWebAppData", [None])[0]
            if query:
                if query.startswith("user%3D") or "%257B" in query or "%2522" in query:
                    query = urllib.parse.unquote(query)
                return query
        except Exception:
            pass
        return None

    bot_ent = None
    bot_in = None
    try:
        bot_ent = await client.get_entity(bot_username)
        bot_in = await client.get_input_entity(bot_ent)
    except Exception as e:
        return None

    # Strategy A: RequestAppWebViewRequest with short names
    names_to_try = candidate_short_names or ["app", "play", "myapp", "miniapp", "bot", "game"]
    for sn in names_to_try:
        try:
            req_p = {
                "peer": bot_in,
                "app": InputBotAppShortName(bot_id=bot_in, short_name=sn),
                "platform": "android"
            }
            if start_param:
                req_p["start_param"] = str(start_param)
            res = await client(RequestAppWebViewRequest(**req_p))
            tok = extract_from_url(getattr(res, "url", None))
            if tok:
                return tok
        except Exception:
            continue

    # Strategy B: Bot Menu Button
    try:
        menu = await client(functions.bots.GetBotMenuButtonRequest(user_id=bot_in))
        menu_btn = getattr(menu, "button", None)
        if menu_btn and hasattr(menu_btn, "url") and menu_btn.url:
            req_p = {
                "peer": bot_ent,
                "bot": bot_ent,
                "platform": "android",
                "url": menu_btn.url
            }
            if start_param:
                req_p["start_param"] = str(start_param)
            res = await client(RequestWebViewRequest(**req_p))
            tok = extract_from_url(getattr(res, "url", None))
            if tok:
                return tok
    except Exception:
        pass

    # Strategy C: Send /start and inspect keyboard buttons
    try:
        await client.send_message(bot_ent, f"/start {start_param}" if start_param else "/start")
        await asyncio.sleep(1.8)
        msgs = await client.get_messages(bot_ent, limit=5)
        for m in msgs:
            if not m.out and m.buttons:
                for row in m.buttons:
                    for b in row:
                        raw_b = getattr(b, "button", b)
                        w_url = getattr(getattr(raw_b, "web_app", None), "url", None) or getattr(raw_b, "url", None)
                        if w_url:
                            try:
                                req_p = {
                                    "peer": bot_ent,
                                    "bot": bot_ent,
                                    "platform": "android",
                                    "url": w_url
                                }
                                if start_param:
                                    req_p["start_param"] = str(start_param)
                                res = await client(RequestWebViewRequest(**req_p))
                                tok = extract_from_url(getattr(res, "url", None))
                                if tok:
                                    return tok
                            except Exception:
                                pass
                        if any(w in (b.text or "").lower() for w in ["play", "open", "launch", "app", "start", "mine"]):
                            try:
                                c_res = await b.click()
                                tok = extract_from_url(getattr(c_res, "url", None))
                                if tok:
                                    return tok
                            except Exception:
                                pass
    except Exception:
        pass

    # Strategy D: Direct RequestWebViewRequest with known default WebApp URL
    if default_url:
        try:
            req_p = {
                "peer": bot_ent,
                "bot": bot_ent,
                "platform": "android",
                "url": default_url
            }
            if start_param:
                req_p["start_param"] = str(start_param)
            res = await client(RequestWebViewRequest(**req_p))
            tok = extract_from_url(getattr(res, "url", None))
            if tok:
                return tok
        except Exception:
            pass

    return None


async def extract_account_tokens(acc: dict, session: aiohttp.ClientSession):
    """Connects MTProto for a single account and extracts all 9 bot session links."""
    acc_name = acc.get("name", "Account")
    acc_uid = str(acc.get("user_id"))
    acc_sess = acc.get("session_string") or acc.get("session")
    if not acc_sess or acc.get("status") == "revoked":
        print(f"[{acc_name}] Skipping revoked or empty session.")
        return

    is_master = (acc_uid == str(REPORT_CHAT_ID) or acc_uid == "6727787768")
    print(f"\n🚀 [{acc_name} (ID: {acc_uid}{' - 👑 Master' if is_master else ''})] Connecting MTProto...")
    cl = TelegramClient(StringSession(acc_sess), API_ID, API_HASH)
    try:
        await cl.connect()
        if not await cl.is_user_authorized():
            print(f"[{acc_name}] Session not authorized or revoked.")
            return

        tokens = {}

        # 1. Stones Miners
        tok = await extract_bot_webapp_token(cl, STONES_BOT, default_url="https://app.stoneswithestand.my.id/", candidate_short_names=["app", "miniapp"])
        if tok:
            tokens["stones_init_data"] = tok
            print(f"  💎 Stones Miners: Collected")

        # 2. MRG Miner
        mrg_p = None if is_master else MRG_REF
        tok = await extract_bot_webapp_token(cl, MRG_BOT, start_param=mrg_p, default_url="https://app.mrgtoken.xyz/", candidate_short_names=["app", "miniapp"])
        if tok:
            tokens["mrg_init_data"] = tok
            print(f"  ⛏️ MRG Miner: Collected")

        # 3. AI Lab Robot
        ai_p = None if is_master else AILAB_REF
        tok = await extract_bot_webapp_token(cl, AILAB_BOT, start_param=ai_p, default_url="https://ailab-agent.online/", candidate_short_names=["app", "agent"])
        if tok:
            tokens["ailab_init_data"] = tok
            print(f"  🧪 AI Lab: Collected")

        # 4. UltraWallet
        uw_p = None if is_master else ULTRAWALLET_REF
        tok = await extract_bot_webapp_token(cl, ULTRAWALLET_BOT, start_param=uw_p, default_url="https://wallet.trxvault.top/", candidate_short_names=["app", "trade", "Trade"])
        if tok:
            tokens["ultrawallet_init_data"] = tok
            print(f"  💳 UltraWallet: Collected")

        # 5. ATF Miner
        atf_p = None if is_master else str(REPORT_CHAT_ID)
        tok = await extract_bot_webapp_token(cl, ATF_BOT, start_param=atf_p, default_url="https://atfminers.asloni.online/miner/index.html?entry=bot_start", candidate_short_names=["app", "miner", "play"])
        if tok:
            tokens["atf_init_data"] = tok
            print(f"  🪙 ATF Miner: Collected")

        # 6. FINVORA Web3
        fin_p = None if is_master else FINVORA_REF
        tok = await extract_bot_webapp_token(cl, FINVORA_BOT, start_param=fin_p, default_url="https://finvora-production.up.railway.app/", candidate_short_names=["app", "finvora", "mine", "play"])
        if tok:
            tokens["finvora_init_data"] = tok
            print(f"  🌐 FINVORA Web3: Collected")

        # 7. TurboGram V1
        turb_p = None if is_master else TURBOGRAM_REF
        tok = await extract_bot_webapp_token(cl, TURBOGRAM_BOT, start_param=turb_p, default_url="https://turbo.tamimdev.dev/", candidate_short_names=["app", "miniapp", "bot", "turbo"])
        if tok:
            tokens["turbogram_init_data"] = tok
            print(f"  🚀 TurboGram V1: Collected")

        # 8. Victor's Company
        vic_p = None if is_master else VICTORS_REF
        tok = await extract_bot_webapp_token(cl, VICTORS_BOT, start_param=vic_p, default_url="https://app.victors.company/", candidate_short_names=["app", "play"])
        if tok:
            tokens["victors_init_data"] = tok
            print(f"  🏢 Victor's Company: Collected")

        # 9. VyroDrop
        vy_p = None if is_master else VYRO_REF
        tok = await extract_bot_webapp_token(cl, VYRO_BOT, start_param=vy_p, default_url="https://vyro.run.place/", candidate_short_names=["app", "vyro", "play", "mine"])
        if tok:
            tokens["vyro_init_data"] = tok
            print(f"  💎 VyroDrop: Collected")

        # Auto-join mandatory sponsor channels for side-task verification
        for s_ch in MANDATORY_SPONSOR_CHANNELS:
            try:
                await cl(JoinChannelRequest(s_ch))
                await asyncio.sleep(0.3)
            except Exception:
                pass

        # Sync to Cloudflare Edge KV & Upstash Redis
        if tokens:
            await sync_tokens_to_edge_and_upstash(session, acc_uid, acc_name, tokens)

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
                await asyncio.sleep(1.5)
            except Exception as e:
                print(f"Error processing account {acc.get('name')}: {e}")

    print("\n✅ All 24h WebApp tokens collected & pushed to 5x Cloudflare Nodes & Upstash Redis!")


if __name__ == "__main__":
    asyncio.run(main())
