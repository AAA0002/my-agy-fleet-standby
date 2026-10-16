"""
onboard_kynex_fleet.py
=============================================================================
ONBOARDS ALL 18 FLEET ACCOUNTS TO KYNEX NETWORK (@Kynex_miningbot)
=============================================================================
1. Iterates through all 18 accounts from Upstash Redis.
2. Connects via Telethon, joins sponsor channels, and requests WebApp token.
   - Workers: /start 6727787768 (binds referral to Master Account)
   - Master: starts as root
3. Farms initial cycle via kynex_miner (starter profile, 12h energy, start mining, checkin, ads, social tasks).
4. Persists kynex_init_data into Upstash Redis miniapp_tokens and Cloudflare KV.
5. Exits cleanly (Zero Phone Load - all ongoing farming runs 100% in cloud).
"""

import asyncio
import os
import sys
import json
import time
import logging
import urllib.parse
import urllib.request
import aiohttp

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import InputBotAppShortName
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import RequestAppWebViewRequest, RequestWebViewRequest

import kynex_miner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("onboard_kynex")

API_ID = 37321306
API_HASH = "5cd9e5bbfb572a4429a0c54774153b47"
UPSTASH_URL = os.getenv("UPSTASH_URL", "https://pleasant-locust-220893.upstash.io")
UPSTASH_TOKEN = os.getenv("UPSTASH_TOKEN", "")
CF_SECRET = "agy_cf_secret_7d36994e_2026"
CF_WORKERS = [
    "https://restore-agy.aaaai2.workers.dev",
    "https://restore-agy.aaa-bot.workers.dev",
    "https://restore-agy.aaa222.workers.dev",
    "https://restore-agy.agorameet.workers.dev",
    "https://restore-agy.aaaai.workers.dev"
]

KYNEX_BOT = "Kynex_miningbot"
MASTER_UID = "6727787768"
SPONSOR_CHANNELS = ["kynex_mining", "EarnVaulte", "solanamemes001", "Web3Primeteam"]


def parse_init_data(url_str):
    if not url_str:
        return None
    try:
        p = urllib.parse.urlparse(str(url_str))
        frag = urllib.parse.parse_qs(p.fragment).get("tgWebAppData", [None])[0]
        if frag:
            if frag.startswith("user%3D") or "%257B" in frag or "%2522" in frag:
                frag = urllib.parse.unquote(frag)
            return frag
        q = urllib.parse.parse_qs(p.query).get("tgWebAppData", [None])[0]
        if q:
            if q.startswith("user%3D") or "%257B" in q or "%2522" in q:
                q = urllib.parse.unquote(q)
            return q
    except Exception:
        pass
    return None


async def sync_token_to_clouds(uid: str, token_val: str):
    """Saves kynex_init_data for an account to Upstash Redis and Cloudflare KV."""
    # 1. Upstash Redis miniapp_tokens
    try:
        up_h = {"Authorization": f"Bearer {UPSTASH_TOKEN}", "Content-Type": "application/json"}
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{UPSTASH_URL}/get/miniapp_tokens", headers=up_h) as r:
                if r.status == 200:
                    d = await r.json()
                    raw = d.get("result")
                    while isinstance(raw, str):
                        raw = json.loads(raw)
                    tokens_map = raw if isinstance(raw, dict) else {}
                else:
                    tokens_map = {}

            acc_toks = tokens_map.setdefault(str(uid), {})
            acc_toks["kynex_init_data"] = token_val
            acc_toks["updated_at"] = time.time()

            # Save back to Upstash
            await s.post(f"{UPSTASH_URL}/set/miniapp_tokens", json=json.dumps(tokens_map), headers=up_h)
            logger.info(f"[{uid}] Saved kynex_init_data to Upstash miniapp_tokens")
    except Exception as e:
        logger.warning(f"[{uid}] Upstash sync note: {e}")

    # 2. Sync to Cloudflare KV
    payload = {"account_tokens": {str(uid): {"kynex_init_data": token_val}}}
    for cf_url in CF_WORKERS:
        try:
            async with aiohttp.ClientSession() as s:
                await s.post(
                    f"{cf_url}/api/fleet/sync",
                    json=payload,
                    headers={"X-Custom-Auth": CF_SECRET, "Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=4)
                )
        except Exception:
            pass


async def onboard_account(acc: dict, http_session: aiohttp.ClientSession):
    uid = str(acc.get("user_id"))
    name = acc.get("name", uid)
    sess_str = acc.get("session_string") or acc.get("session")
    if not sess_str:
        logger.warning(f"[{name}] Skipping: No session string")
        return False

    is_master = (uid == MASTER_UID)
    start_param = None if is_master else MASTER_UID

    logger.info(f"\n=======================================================")
    logger.info(f"🚀 Onboarding {name} ({uid}) to Kynex Network...")
    logger.info(f"   Referral Binding: {'Root / Master' if is_master else f'Master {MASTER_UID}'}")
    logger.info(f"=======================================================")

    client = TelegramClient(StringSession(sess_str), API_ID, API_HASH)
    init_data = None
    try:
        await client.connect()
        if not await client.is_user_authorized():
            logger.warning(f"[{name}] Session unauthorized")
            return False

        # Auto-join mandatory sponsor channels so social tasks verify instantly
        for ch in SPONSOR_CHANNELS:
            try:
                await client(JoinChannelRequest(ch))
                await asyncio.sleep(0.3)
            except Exception:
                pass

        bot_ent = await client.get_entity(KYNEX_BOT)
        bot_in = await client.get_input_entity(bot_ent)

        # Send /start with referral for worker accounts
        if start_param:
            try:
                await client.send_message(bot_ent, f"/start {start_param}")
                await asyncio.sleep(1.0)
            except Exception as se:
                logger.debug(f"[{name}] /start note: {se}")

        # Request WebApp Token (Short Name: "App")
        try:
            req_p = {
                "peer": bot_in,
                "app": InputBotAppShortName(bot_id=bot_in, short_name="App"),
                "platform": "android"
            }
            if start_param:
                req_p["start_param"] = str(start_param)
            app_view = await client(RequestAppWebViewRequest(**req_p))
            init_data = parse_init_data(getattr(app_view, "url", None))
        except Exception as ae:
            logger.debug(f"[{name}] RequestAppWebViewRequest note: {ae}")

        # Fallback to RequestWebViewRequest
        if not init_data:
            try:
                req_w = {
                    "peer": bot_ent,
                    "bot": bot_ent,
                    "platform": "android",
                    "url": "https://kynex.top/telegram-auth.html"
                }
                if start_param:
                    req_w["start_param"] = str(start_param)
                w_view = await client(RequestWebViewRequest(**req_w))
                init_data = parse_init_data(getattr(w_view, "url", None))
            except Exception as we:
                logger.debug(f"[{name}] RequestWebViewRequest note: {we}")

    except Exception as ce:
        logger.error(f"[{name}] Connection error: {ce}")
        return False
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass

    if not init_data:
        logger.warning(f"[{name}] Failed to extract Kynex initData")
        return False

    logger.info(f"[{name}] 🔑 Extracted Kynex initData (len: {len(init_data)})")

    # Save to Upstash & Cloudflare KV
    await sync_token_to_clouds(uid, init_data)

    # Farm full cycle (starter profile, energy refill, start mining, daily checkin, ads, social tasks)
    farm_res = await kynex_miner.farm_kynex_account(http_session, init_data, acc, is_master=is_master)
    logger.info(f"[{name}] 🌾 Farm Result: {farm_res.get('status')}")
    logger.info(f"[{name}]    Balance: {farm_res.get('balance'):.1f} KNX | Mining: {farm_res.get('mining_active')}")
    logger.info(f"[{name}]    Notes: {farm_res.get('notes')}")
    return True


async def main():
    logger.info("Fetching fleet accounts from Upstash Redis...")
    up_h = {"Authorization": f"Bearer {UPSTASH_TOKEN}", "Content-Type": "application/json"}
    accounts = []
    async with aiohttp.ClientSession() as s:
        async with s.get(f"{UPSTASH_URL}/keys/account:*", headers=up_h) as r:
            if r.status == 200:
                k_data = await r.json()
                keys = k_data.get("result", [])
                pipe = [["get", k] for k in sorted(keys)]
                async with s.post(f"{UPSTASH_URL}/pipeline", json=pipe, headers=up_h) as pr:
                    if pr.status == 200:
                        p_data = await pr.json()
                        for item in p_data:
                            val = item.get("result")
                            if val:
                                obj = json.loads(val) if isinstance(val, str) else val
                                while isinstance(obj, str):
                                    obj = json.loads(obj)
                                if isinstance(obj, dict) and obj.get("user_id"):
                                    accounts.append(obj)

    logger.info(f"Loaded {len(accounts)} accounts from Upstash.")
    if not accounts:
        logger.error("No accounts loaded!")
        return

    # Put Master account first
    accounts.sort(key=lambda a: 0 if str(a.get("user_id")) == MASTER_UID else 1)

    success_cnt = 0
    fail_cnt = 0

    async with aiohttp.ClientSession() as http:
        for idx, acc in enumerate(accounts, 1):
            name = acc.get("name", "User")
            uid = acc.get("user_id")
            try:
                ok = await onboard_account(acc, http)
                if ok:
                    success_cnt += 1
                else:
                    fail_cnt += 1
            except Exception as e:
                logger.error(f"[{name}] Unhandled error: {e}")
                fail_cnt += 1
            # Graceful delay between accounts to avoid MTProto connection bursts
            await asyncio.sleep(2.0)

    logger.info("\n" + "=" * 60)
    logger.info(f"🏁 ONBOARDING COMPLETE: {success_cnt}/{len(accounts)} Succeeded, {fail_cnt} Failed")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
