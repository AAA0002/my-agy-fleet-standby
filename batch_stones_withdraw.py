#!/usr/bin/env python3
"""
batch_stones_withdraw.py
Automated batch withdrawal engine for all fleet accounts holding >= 500 STONES.
Binds each account's dedicated isolated EVM wallet from fleet_evm_wallets.json
and executes the withdrawal via stones_captcha_solver.
"""

import os
import json
import asyncio
import aiohttp
import logging
from stones_captcha_solver import execute_stones_withdrawal_with_captcha
from proxy_manager import get_account_user_agent

logging.basicConfig(level=logging.INFO, format="[%(asctime)s - %(levelname)s] %(message)s")
logger = logging.getLogger("BatchStonesWithdraw")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKENS_FILE = os.path.join(BASE_DIR, "fleet_miniapp_tokens.json")
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")
FLEET_EVM_FILE = os.path.join(BASE_DIR, "fleet_evm_wallets.json")

# Accounts already successfully queued in this session
ALREADY_QUEUED = set()

async def run_batch():
    if not os.path.exists(TOKENS_FILE) or not os.path.exists(FLEET_EVM_FILE):
        logger.error("Missing required config files.")
        return

    with open(TOKENS_FILE, "r", encoding="utf-8") as f:
        tokens_cache = json.load(f)
    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        accounts_map = {str(a["user_id"]): a for a in json.load(f)}
    with open(FLEET_EVM_FILE, "r", encoding="utf-8") as f:
        fleet_evm = json.load(f)

    base_url = "https://app.stoneswithestand.my.id"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 Chrome/128.0.6613.127 Mobile Safari/537.36 Telegram-Android/11.1.3"
    }

    results = []

    async with aiohttp.ClientSession() as session:
        for uid, tok_info in tokens_cache.items():
            if str(uid).startswith("_"):
                continue
            if str(uid) in ALREADY_QUEUED:
                logger.info(f"UID {uid} already queued in previous run. Skipping.")
                results.append({"uid": uid, "name": accounts_map.get(str(uid), {}).get("name", uid), "status": "already_queued"})
                continue

            init_data = tok_info.get("stones_init_data")
            if not init_data:
                continue

            acc = accounts_map.get(str(uid), {})
            name = acc.get("name", uid)
            proxy = acc.get("proxy")
            evm_wallet = fleet_evm.get(str(uid), {}).get("address", "0xfda4182001672b9f0f09e2118242e543e35ed5ce")

            logger.info(f"--- Checking {name} (UID: {uid}) ---")
            acc_headers = {
                "Content-Type": "application/json",
                "User-Agent": get_account_user_agent(uid)
            }

            # 1. Check current coins holding
            try:
                async with session.post(
                    f"{base_url}/api/state",
                    json={"initData": init_data},
                    headers=acc_headers,
                    proxy=proxy,
                    timeout=aiohttp.ClientTimeout(total=10, connect=5)
                ) as sr:
                    if sr.status != 200:
                        logger.warning(f"[{name}] /api/state returned {sr.status}. Skipping.")
                        continue
                    state_data = await sr.json()
                    user = state_data.get("user", {})
                    coins = user.get("coins", 0)
                    cur_wallet = user.get("wallet")
            except Exception as e:
                logger.error(f"[{name}] Error querying state with proxy ({proxy}): {e}. Retrying direct...")
                try:
                    async with session.post(
                        f"{base_url}/api/state",
                        json={"initData": init_data},
                        headers=acc_headers,
                        timeout=aiohttp.ClientTimeout(total=10, connect=5)
                    ) as sr:
                        if sr.status != 200:
                            continue
                        state_data = await sr.json()
                        user = state_data.get("user", {})
                        coins = user.get("coins", 0)
                        cur_wallet = user.get("wallet")
                        proxy = None  # Use direct if proxy failed
                except Exception as de:
                    logger.error(f"[{name}] Direct retry error: {de}")
                    continue

            logger.info(f"[{name}] Spendable Coins: {coins} STONES | Bound Wallet: {cur_wallet}")

            if coins < 500:
                logger.info(f"[{name}] Balance ({coins} STONES) < 500 minimum. Skipping.")
                results.append({"uid": uid, "name": name, "status": "below_threshold", "coins": coins})
                continue

            # 2. Ensure isolated EVM wallet is bound
            if cur_wallet != evm_wallet:
                logger.info(f"[{name}] Binding isolated EVM wallet: {evm_wallet}...")
                try:
                    async with session.post(
                        f"{base_url}/api/wallet",
                        json={"initData": init_data, "wallet": evm_wallet},
                        headers=acc_headers,
                        proxy=proxy,
                        timeout=aiohttp.ClientTimeout(total=8, connect=5)
                    ) as bwr:
                        b_res = await bwr.json()
                        logger.info(f"[{name}] Wallet bind response: {b_res}")
                except Exception as be:
                    logger.warning(f"[{name}] Wallet bind note: {be}")

            # 3. Execute withdrawal with captcha
            logger.info(f"[{name}] Submitting 500 STONES withdrawal to {evm_wallet}...")
            try:
                ok, res = await execute_stones_withdrawal_with_captcha(
                    session=session,
                    base_url=base_url,
                    headers=acc_headers,
                    init_data=init_data,
                    amount=500,
                    wallet=evm_wallet,
                    proxy=proxy
                )
                logger.info(f"[{name}] Withdrawal Response: ok={ok}, res={res}")
                results.append({"uid": uid, "name": name, "status": "submitted" if ok else "failed", "res": res, "wallet": evm_wallet})
            except Exception as we:
                logger.error(f"[{name}] Withdrawal exception: {we}")
                results.append({"uid": uid, "name": name, "status": "exception", "error": str(we)})

            # Natural delay between accounts to prevent rate limiting
            await asyncio.sleep(2.0)

    print("\n" + "="*60)
    print("BATCH WITHDRAWAL SUMMARY:")
    print("="*60)
    for r in results:
        status_icon = "✅" if r.get("status") in ("submitted", "already_queued") else ("⏳" if r.get("status") == "below_threshold" else "❌")
        print(f"{status_icon} {r['name']} ({r['uid']}): {r.get('status')} | {r.get('res') or r.get('coins') or r.get('error')}")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(run_batch())
