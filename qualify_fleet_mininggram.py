#!/usr/bin/env python3
"""
MiningGRAM Referral Qualifier:
Ensures all fleet accounts bound to master referral code (339JU9K)
complete the 2 mandatory tasks (Like & Retweet + Join Channel)
so that the master account gets credited $2.00 USDT per account.
"""

import json
import asyncio
import aiohttp
import os
import logging
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.channels import JoinChannelRequest

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MG_Qualifier")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_ID = 26569109
API_HASH = "aa1e0fbab557f9554289a6ea87a718b9"
REFERRAL_CODE = "339JU9K"
BASE_URL = "https://mining-gram-worker.muhaisin0888.workers.dev"

TASK_RETWEET = "c9aa035b-7664-4a1e-a60b-56e175328949"  # Like & Retweet (timer 30s)
TASK_CHANNEL = "e6c5f7ba-552b-405e-9424-8babb20ce92d"  # Join Announcement Channel

async def qualify_account(session: aiohttp.ClientSession, acc: dict, init_data: str):
    acc_name = acc.get("name", "User")
    acc_uid = str(acc.get("user_id"))

    # 1. Join Announcement Channel via Telethon
    sess_str = acc.get("session_string")
    if sess_str:
        try:
            cl = TelegramClient(StringSession(sess_str), API_ID, API_HASH)
            await cl.connect()
            try:
                ch = await cl.get_entity("MiningGRAM_channel")
                await cl(JoinChannelRequest(ch))
                logger.info(f"[{acc_name}] Joined @MiningGRAM_channel")
            except Exception as je:
                logger.debug(f"[{acc_name}] Join note: {je}")
            finally:
                await cl.disconnect()
        except Exception as ce:
            logger.debug(f"[{acc_name}] Client connect note: {ce}")

    # 2. Auth to MiningGRAM API
    auth_payload = {
        "initData": init_data,
        "referralCode": REFERRAL_CODE,
        "deviceFingerprint": f"fp_{acc_uid}"
    }
    headers = {"Content-Type": "application/json"}
    async with session.post(f"{BASE_URL}/api/auth", json=auth_payload, timeout=aiohttp.ClientTimeout(total=10)) as ar:
        ad = await ar.json()
        token = ad.get("sessionToken") or ad.get("token")
    if not token:
        logger.warning(f"[{acc_name}] Could not get MiningGRAM session token")
        return False

    auth_headers = {**headers, "Authorization": f"Bearer {token}"}

    # 3. Check current completed tasks
    async with session.get(f"{BASE_URL}/api/social/tasks", headers=auth_headers, timeout=aiohttp.ClientTimeout(total=10)) as tr:
        if tr.status != 200:
            return False
        td = await tr.json()
        tasks = td.get("tasks", [])
        status_map = {t.get("id"): t.get("completed", False) for t in tasks}

    # Task A: Join Announcement Channel
    if not status_map.get(TASK_CHANNEL):
        try:
            async with session.post(f"{BASE_URL}/api/social/claim", json={"taskId": TASK_CHANNEL}, headers=auth_headers, timeout=aiohttp.ClientTimeout(total=10)) as c1:
                res1 = await c1.json()
                if c1.status == 200:
                    logger.info(f"[{acc_name}] ✅ Claimed Task 1 (Join Channel)!")
                else:
                    logger.info(f"[{acc_name}] Task 1 claim note: {res1}")
        except Exception as e:
            logger.debug(f"[{acc_name}] Task 1 error: {e}")

    # Task B: Like & Retweet (timer 30s)
    if not status_map.get(TASK_RETWEET):
        try:
            # Start timer
            await session.post(f"{BASE_URL}/api/social/timer/start", json={"taskId": TASK_RETWEET}, headers=auth_headers, timeout=aiohttp.ClientTimeout(total=10))
            logger.info(f"[{acc_name}] Started 30s timer for Task 2 (Like & Retweet)...")
            await asyncio.sleep(32)
            async with session.post(f"{BASE_URL}/api/social/claim", json={"taskId": TASK_RETWEET}, headers=auth_headers, timeout=aiohttp.ClientTimeout(total=10)) as c2:
                res2 = await c2.json()
                if c2.status == 200:
                    logger.info(f"[{acc_name}] ✅ Claimed Task 2 (Like & Retweet)!")
                else:
                    logger.info(f"[{acc_name}] Task 2 claim note: {res2}")
        except Exception as e:
            logger.debug(f"[{acc_name}] Task 2 error: {e}")

    return True

async def main():
    with open(os.path.join(BASE_DIR, "accounts.json"), "r") as f:
        accs = json.load(f)

    with open(os.path.join(BASE_DIR, "fleet_miniapp_tokens.json"), "r") as f:
        tokens = json.load(f)

    async with aiohttp.ClientSession() as session:
        # Check master USDT promo status before
        master_init = tokens.get("6727787768", {}).get("mininggram_init_data")
        if master_init:
            ar = await session.post(f"{BASE_URL}/api/auth", json={"initData": master_init, "referralCode": REFERRAL_CODE, "deviceFingerprint": "fp_6727787768"})
            tok = (await ar.json()).get("sessionToken")
            if tok:
                pr = await session.get(f"{BASE_URL}/api/usdt/promo", headers={"Authorization": f"Bearer {tok}"})
                pd = await pr.json()
                logger.info(f"Master Balance Before: ${pd.get('balanceCents', 0)/100:.2f} USDT | Referrals: {len(pd.get('referrals', []))}")

        # Qualify uncredited accounts
        for acc in accs:
            uid = str(acc.get("user_id"))
            if uid == "6727787768":
                continue
            init_data = tokens.get(uid, {}).get("mininggram_init_data")
            if not init_data:
                continue
            logger.info(f"--- Qualifying Account: {acc.get('name')} ({uid}) ---")
            await qualify_account(session, acc, init_data)
            await asyncio.sleep(2.0)

        # Check master USDT promo status after
        if master_init and tok:
            pr = await session.get(f"{BASE_URL}/api/usdt/promo", headers={"Authorization": f"Bearer {tok}"})
            pd = await pr.json()
            logger.info(f"Master Balance After: ${pd.get('balanceCents', 0)/100:.2f} USDT | Referrals Credited: {len([r for r in pd.get('referrals', []) if r.get('credited')])}")

if __name__ == "__main__":
    asyncio.run(main())
