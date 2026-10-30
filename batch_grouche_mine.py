#!/usr/bin/env python3
"""
batch_grouche_mine.py
=============================================================================
Autonomous 100% Cloud Farming & Referral Pipeline for Grouche Mine 🍐 ($GRC)
Bot: @GRC_AirdrooBot | MiniApp: https://grouchemine.world/
=============================================================================
1. Resolves @GRC_AirdrooBot and binds worker accounts to Master (6727787768).
2. Extracts WebApp initData via MTProto RequestWebViewRequest.
3. Authenticates (/api/auth/login).
4. Links dedicated account TON wallet (/api/users/wallet/connect).
5. Claims daily reward (/api/users/daily-claim).
6. Executes all social tasks (/api/tasks/open -> wait -> /api/tasks/complete).
7. Auto-compounds LNX balance into mining rigs (/api/users/buy-package).
8. Claims accumulated mining yield (/api/mining/claim).
=============================================================================
"""

import os
import sys
import json
import time
import asyncio
import urllib.parse
import urllib.request
import logging
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import RequestWebViewRequest
from telethon.tl.functions.channels import JoinChannelRequest
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

API_ID = int(os.getenv("TELEGRAM_API_ID", "24726207"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "5cd9e5bbfb572a4429a0c54774153b47")
MASTER_UID = "6727787768"
BOT_USERNAME = "GRC_AirdrooBot"
BASE_URL = "https://grouchemine.world/api"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("grouche_mine")

def api_call(endpoint: str, method: str = "GET", data: dict = None, init_data: str = None) -> dict:
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36"
    }
    if init_data:
        headers["X-Telegram-Init-Data"] = init_data

    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="ignore")
        try:
            return json.loads(err_msg)
        except Exception:
            return {"success": False, "error": f"HTTP {e.code}: {err_msg}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def process_account(account: dict, index: int, total: int):
    uid = str(account.get("user_id") or "")
    name = account.get("name") or account.get("first_name") or f"Account_{uid}"
    is_master = (uid == MASTER_UID)
    session_str = account.get("session_string")
    if not session_str:
        logger.warning(f"[{index}/{total}] {name} (UID: {uid}): Missing session_string, skipping.")
        return

    logger.info(f"[{index}/{total}] Processing {'👑 Master' if is_master else '👷 Worker'}: {name} (UID: {uid})...")
    client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
    await client.connect()
    if not await client.is_user_authorized():
        logger.warning(f"  ❌ Client {uid} not authorized in Telegram.")
        await client.disconnect()
        return

    try:
        bot_entity = await client.get_entity(BOT_USERNAME)

        # 1. Referral binding for workers
        if not is_master and not account.get("grc_referral_bound"):
            logger.info(f"  🔗 Binding referral under Master ({MASTER_UID})...")
            try:
                await client.send_message(bot_entity, f"/start {MASTER_UID}")
                account["grc_referral_bound"] = True
                await asyncio.sleep(2)
            except Exception as e:
                logger.warning(f"  ⚠️ Referral send error: {e}")

        # 2. Extract WebApp initData
        res = await client(RequestWebViewRequest(
            peer=bot_entity,
            bot=bot_entity,
            url="https://grouchemine.world/",
            platform="android"
        ))
        frag = urllib.parse.urlparse(res.url).fragment
        init_data = urllib.parse.parse_qs(frag).get("tgWebAppData", [""])[0]
        if not init_data:
            logger.error(f"  ❌ Failed to extract initData for {name}.")
            await client.disconnect()
            return

        account["grouchemine_init_data"] = init_data

        # Sync to Upstash Redis if available
        upstash_url = os.getenv("UPSTASH_URL") or os.getenv("UPSTASH_REDIS_REST_URL")
        upstash_token = os.getenv("UPSTASH_TOKEN") or os.getenv("UPSTASH_REDIS_REST_TOKEN")
        if upstash_url and upstash_token:
            try:
                # Merge into existing fleet:tokens:{uid}
                get_req = urllib.request.Request(
                    f"{upstash_url}/get/fleet:tokens:{uid}",
                    headers={"Authorization": f"Bearer {upstash_token}"}
                )
                with urllib.request.urlopen(get_req, timeout=4) as u_resp:
                    raw = json.loads(u_resp.read().decode("utf-8")).get("result")
                    curr_toks = json.loads(raw) if raw and isinstance(raw, str) else (raw or {})
                curr_toks["grouchemine_init_data"] = init_data
                set_req = urllib.request.Request(
                    f"{upstash_url}/set/fleet:tokens:{uid}",
                    data=json.dumps(curr_toks).encode("utf-8"),
                    headers={"Authorization": f"Bearer {upstash_token}"}
                )
                urllib.request.urlopen(set_req, timeout=4)
            except Exception:
                pass

        # 3. Authenticate
        login_res = api_call("/auth/login", method="POST", data={"initData": init_data}, init_data=init_data)
        user_info = login_res.get("data", {}).get("user", {})
        lnx_bal = float(user_info.get("lnxBalance", 0) or 0)
        curr_bal = lnx_bal
        logger.info(f"  ✅ Authenticated: {user_info.get('username') or name} | Balance: {lnx_bal} LNX")

        # 4. Connect TON Wallet
        ton_wallet = account.get("ton_wallet", {})
        ton_addr = ton_wallet.get("address")
        if ton_addr and not user_info.get("tonAddress"):
            w_res = api_call("/users/wallet/connect", method="POST", data={"address": ton_addr}, init_data=init_data)
            if w_res.get("success"):
                logger.info(f"  💼 Linked TON Wallet: {ton_addr[:10]}...{ton_addr[-6:]}")
            else:
                logger.warning(f"  ⚠️ Wallet link note: {w_res.get('error')}")

        # 5. Claim Daily Reward
        daily_res = api_call("/users/daily-claim", method="POST", data={}, init_data=init_data)
        if daily_res.get("success"):
            reward = float(daily_res.get("data", {}).get("rewardLnx", 5) or 5)
            curr_bal += reward
            logger.info(f"  🎁 Daily Reward Claimed: +{reward} LNX")
        else:
            logger.info(f"  ⏳ Daily claim: {daily_res.get('error', 'Already claimed')}")

        # 6. Complete available tasks
        # Join sponsor channels for Telegram task verification
        for ch in ["grouchemine", "GroucheCoinEn"]:
            try:
                ch_ent = await client.get_entity(ch)
                await client(JoinChannelRequest(ch_ent))
            except Exception:
                pass

        tasks_res = api_call("/tasks", method="GET", init_data=init_data)
        tasks = tasks_res.get("data", [])
        if isinstance(tasks, list):
            for t in tasks:
                if t.get("completed"):
                    continue
                tid = t.get("id")
                ttitle = t.get("title", "")
                r_lnx = t.get("rewardLnx", 0)
                # Open task
                api_call(f"/tasks/{tid}/open", method="POST", data={}, init_data=init_data)
                # Wait 11s (server enforces 10s countdown HF=10)
                await asyncio.sleep(11)
                # Complete task
                c_res = api_call(f"/tasks/{tid}/complete", method="POST", data={}, init_data=init_data)
                if c_res.get("success"):
                    logger.info(f"  🎯 Completed Task: '{ttitle}' (+{r_lnx} LNX)")
                    curr_bal += r_lnx
                else:
                    logger.info(f"  ℹ️ Task '{ttitle}': {c_res.get('error')}")

        # 7. Check current status & claim mining yield
        mining_res = api_call("/mining/status", method="GET", init_data=init_data)
        m_data = mining_res.get("data", {})
        sess_mined = m_data.get("sessionMinedLnx", 0)
        curr_bal = float(m_data.get("lnxBalance", curr_bal) or curr_bal)
        if sess_mined > 0:
            claim_res = api_call("/mining/claim", method="POST", data={}, init_data=init_data)
            if claim_res.get("success"):
                logger.info(f"  ⛏️ Claimed Mined Yield: +{sess_mined} LNX")

        # 8. Auto-compound / Buy highest available miner package
        # Available: pkg-3 (800 LNX), pkg-2 (300 LNX), pkg-1 (100 LNX)
        packages_to_check = [("pkg-3", 800), ("pkg-2", 300), ("pkg-1", 100)]
        for pkg_id, cost in packages_to_check:
            if curr_bal >= cost:
                buy_res = api_call("/users/buy-package", method="POST", data={"packageId": pkg_id}, init_data=init_data)
                if buy_res.get("success"):
                    logger.info(f"  🚀 Auto-Purchased Miner {pkg_id} for {cost} LNX!")
                    curr_bal -= cost
                    # Toggle mining
                    api_call("/mining/toggle", method="POST", data={}, init_data=init_data)
                    break

        # 9. Final status check
        final_status = api_call("/mining/status", method="GET", init_data=init_data)
        f_data = final_status.get("data", {})
        logger.info(f"  📊 Status: Mining={f_data.get('isMining')} | Packages={f_data.get('packageCount')} | Balance={f_data.get('lnxBalance')} LNX\n")

    except Exception as e:
        logger.error(f"  ❌ Error processing {name}: {e}")
    finally:
        await client.disconnect()

async def run_fleet():
    accounts_file = os.path.join(BASE_DIR, "accounts.json")
    with open(accounts_file, "r") as f:
        accounts = json.load(f)

    logger.info("=" * 75)
    logger.info("🚀 GROUCHE MINE 🍐 ($GRC) FLEET-WIDE 21-ACCOUNT FARMING CYCLE")
    logger.info(f"Target Bot: @{BOT_USERNAME} | Master UID: {MASTER_UID}")
    logger.info("=" * 75)

    # First run Workers to generate massive referral rewards for Master
    workers = [a for a in accounts if str(a.get("user_id")) != MASTER_UID]
    masters = [a for a in accounts if str(a.get("user_id")) == MASTER_UID]

    # Process workers
    for idx, acc in enumerate(workers, 1):
        await process_account(acc, idx, len(accounts))
        await asyncio.sleep(2)

    # Process master last so it receives all accumulated referral bonuses and buys highest tier rigs
    for idx, acc in enumerate(masters, len(workers) + 1):
        await process_account(acc, idx, len(accounts))

    # Save updated referral binding state
    with open(accounts_file, "w") as f:
        json.dump(accounts, f, indent=2)

    logger.info("=" * 75)
    logger.info("🎉 Fleet-Wide Grouche Mine 🍐 Cycle Complete!")
    logger.info("=" * 75)

if __name__ == "__main__":
    asyncio.run(run_fleet())
