#!/usr/bin/env python3
"""
execute_ailab_ainovum_withdrawals.py
=============================================================================
Autonomous withdrawal engine for AI Lab Robot ($0.02 threshold) and Ainovum ($0.10 USDT threshold).
Enforces:
  1. Host account (6727787768) 100% protected (0 withdrawals from AI Lab).
  2. Worker accounts withdraw to Binance Web3 Master (or dedicated isolated EVMs).
  3. Sends verified Telegram alerts for every successful submission.
=============================================================================
"""

import os
import sys
import json
import time
import asyncio
import logging
import aiohttp
from dotenv import load_dotenv
from proxy_manager import get_account_user_agent

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s UTC] [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("WithdrawalExecutor")

MASTER_EVM_VAULT = "0xfda4182001672b9f0f09e2118242e543e35ed5ce"
REPORT_BOT_TOKEN = os.getenv("REPORT_BOT_TOKEN", "8858823950:AAFFkuls8hBf23taCZE1y5gVzP4AFCuqI5o")
REPORT_CHAT_ID = os.getenv("REPORT_CHAT_ID", "6727787768")
PAYOUT_CHANNEL_ID = os.getenv("PAYOUT_CHANNEL_ID", "-1004402765950")

def load_accounts():
    with open(os.path.join(BASE_DIR, "accounts.json"), "r", encoding="utf-8") as f:
        return json.load(f)

def load_tokens():
    with open(os.path.join(BASE_DIR, "fleet_miniapp_tokens.json"), "r", encoding="utf-8") as f:
        return json.load(f)

def load_isolated_evm_wallets():
    p = os.path.join(BASE_DIR, "fleet_evm_wallets.json")
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

async def send_telegram_alert(session: aiohttp.ClientSession, text: str):
    if not REPORT_BOT_TOKEN:
        return
    targets = [REPORT_CHAT_ID, PAYOUT_CHANNEL_ID]
    for tid in targets:
        try:
            url = f"https://api.telegram.org/bot{REPORT_BOT_TOKEN}/sendMessage"
            await session.post(url, json={
                "chat_id": tid,
                "text": text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }, timeout=aiohttp.ClientTimeout(total=6))
        except Exception as e:
            logger.debug(f"Telegram alert error for {tid}: {e}")

async def process_ailab_account(session: aiohttp.ClientSession, acc: dict, tokens: dict, isolated_evms: dict = None) -> dict:
    uid = str(acc.get("user_id"))
    name = acc.get("name", uid)
    is_master = (uid == "6727787768" or acc.get("phone") in ("+8801317342850", "01317342850") or acc.get("is_primary"))
    
    init_data = tokens.get(uid, {}).get("ailab_init_data")
    if not init_data:
        return {"uid": uid, "name": name, "status": "no_init_data", "balance": 0.0}

    base_url = "https://api.ailab-agent.online/api/v1"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": get_account_user_agent(uid)
    }

    try:
        # Step 1: Login
        async with session.post(f"{base_url}/users/auth/login", json={"user": init_data}, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as lr:
            if lr.status != 200:
                return {"uid": uid, "name": name, "status": f"login_http_{lr.status}", "balance": 0.0}
            ld = await lr.json()
            tok = ld.get("result", {}).get("bearer") or ld.get("user_info", {}).get("session_id")
            if not tok:
                return {"uid": uid, "name": name, "status": "no_bearer_token", "balance": 0.0}

        auth_headers = {**headers, "Authorization": f"Bearer {tok}"}

        # Step 2: Check cashout balance
        async with session.get(f"{base_url}/cashout", headers=auth_headers, timeout=aiohttp.ClientTimeout(total=8)) as cr:
            if cr.status != 200:
                return {"uid": uid, "name": name, "status": f"cashout_http_{cr.status}", "balance": 0.0}
            cd = await cr.json()
            ubal = float(cd.get("user_info", {}).get("balance", 0) or 0)

        # Host account is strictly protected
        if is_master:
            logger.info(f"[AI Lab] Host account {name} ({uid}) balance: ${ubal:.4f} USD (PROTECTED — 0 withdrawals).")
            return {"uid": uid, "name": name, "status": "master_protected", "balance": ubal}

        logger.info(f"[AI Lab] Worker {name} ({uid}) balance: ${ubal:.4f} USD (Threshold: $0.02).")
        if ubal >= 0.02:
            wd_usd = round(int(ubal * 100) / 100.0, 2)
            target_wallet = (isolated_evms or {}).get(uid, {}).get("address", MASTER_EVM_VAULT)
            pay_payload = {
                "ps_id": 5,  # USDT (BEP20)
                "amount_usd": wd_usd,
                "wallet": target_wallet,
                "dest_tag": ""
            }
            # Execute Cashout
            async with session.post(f"{base_url}/cashout-pay", json=pay_payload, headers=auth_headers, timeout=aiohttp.ClientTimeout(total=10)) as pr:
                pres = await pr.json()
                logger.info(f"[AI Lab] Worker {name} cashout response: {pres}")
                err_code = pres.get("request_info", {}).get("error_code")
                if err_code == 0 or pres.get("result"):
                    await send_telegram_alert(
                        session,
                        f"🎉 *AI Lab Auto-Cashout Submitted!*\n\n"
                        f"• **Account:** {name} (`{uid}`)\n"
                        f"• **Amount:** `${wd_usd} USD`\n"
                        f"• **Destination:** `{target_wallet}` (BEP-20)\n"
                        f"• **Status:** Approved / In Flight"
                    )
                    return {"uid": uid, "name": name, "status": "withdrawn", "balance": ubal, "amount": wd_usd, "details": pres}
                else:
                    return {"uid": uid, "name": name, "status": "cashout_rejected", "balance": ubal, "details": pres}

        return {"uid": uid, "name": name, "status": "below_threshold", "balance": ubal}

    except Exception as e:
        logger.warning(f"[AI Lab] Error for {name} ({uid}): {e}")
        return {"uid": uid, "name": name, "status": f"error_{e}", "balance": 0.0}

async def process_ainovum_account(session: aiohttp.ClientSession, acc: dict, tokens: dict, isolated_evms: dict) -> dict:
    uid = str(acc.get("user_id"))
    name = acc.get("name", uid)
    is_master = (uid == "6727787768" or acc.get("phone") in ("+8801317342850", "01317342850") or acc.get("is_primary"))

    init_data = tokens.get(uid, {}).get("ainovum_init_data")
    if not init_data:
        return {"uid": uid, "name": name, "status": "no_init_data", "available": 0.0}

    proxy = acc.get("proxy")
    base_url = "https://ainovum.biz"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": get_account_user_agent(uid)
    }

    try:
        # Step 1: Bootstrap to get session cookies
        boot_payload = {
            "initData": init_data,
            "platform": "android",
            "referrer": "349182390",
            "timezone_offset_minutes": 0,
            "language_code": "en",
            "registration_duration_ms": 1500
        }
        cookie_hdr = ""
        async with session.post(f"{base_url}/api/bootstrap", json=boot_payload, headers=headers, timeout=aiohttp.ClientTimeout(total=10), proxy=proxy) as br:
            if br.status == 200:
                raw_cookies = br.headers.getall("Set-Cookie", [])
                cookie_hdr = "; ".join([c.split(";")[0] for c in raw_cookies])

        auth_headers = dict(headers)
        if cookie_hdr:
            auth_headers["Cookie"] = cookie_hdr

        # Step 2: Check withdraw config and available balance
        async with session.get(f"{base_url}/api/withdraws/usdt/config", headers=auth_headers, timeout=aiohttp.ClientTimeout(total=8), proxy=proxy) as cr:
            if cr.status != 200:
                return {"uid": uid, "name": name, "status": f"config_http_{cr.status}", "available": 0.0}
            cd = await cr.json()
            avail = float(cd.get("freeze", {}).get("available", 0) or 0)

        # Route target wallet: master gets master vault, worker gets dedicated isolated EVM
        target_wallet = MASTER_EVM_VAULT if is_master else isolated_evms.get(uid, {}).get("address", MASTER_EVM_VAULT)

        logger.info(f"[Ainovum] {name} ({uid}) available: {avail:.4f} USDT (Threshold: 0.10 USDT).")
        if avail >= 0.10:
            wd_amt = round(avail, 4)
            wd_payload = {
                "amount": wd_amt,
                "wallet": target_wallet,
                "network": "bep20"
            }
            logger.info(f"[Ainovum] Submitting withdrawal of {wd_amt} USDT for {name} to {target_wallet}...")
            async with session.post(
                f"{base_url}/api/withdraws/usdt/create",
                json=wd_payload,
                headers=auth_headers,
                timeout=aiohttp.ClientTimeout(total=12),
                proxy=proxy
            ) as wr:
                wd = await wr.json()
                logger.info(f"[Ainovum] Withdrawal result for {name}: {wd}")
                if wr.status == 200 and not wd.get("access_denied") and not wd.get("error"):
                    await send_telegram_alert(
                        session,
                        f"🎉 *Ainovum USDT Withdrawal Submitted!*\n\n"
                        f"• **Account:** {name} (`{uid}`)\n"
                        f"• **Amount:** `{wd_amt} USDT` (BEP-20)\n"
                        f"• **Destination:** `{target_wallet}`\n"
                        f"• **Result:** `{wd}`"
                    )
                    return {"uid": uid, "name": name, "status": "withdrawn", "available": avail, "amount": wd_amt, "details": wd}
                elif wd.get("code") == "busy":
                    return {"uid": uid, "name": name, "status": "gateway_busy", "available": avail, "details": wd}
                else:
                    return {"uid": uid, "name": name, "status": "rejected", "available": avail, "details": wd}

        return {"uid": uid, "name": name, "status": "below_threshold", "available": avail}

    except Exception as e:
        logger.warning(f"[Ainovum] Error for {name} ({uid}): {e}")
        return {"uid": uid, "name": name, "status": f"error_{e}", "available": 0.0}

async def main():
    logger.info("=============================================================================")
    logger.info("  AUTONOMOUS WITHDRAWAL AUDIT & EXECUTION: AI LAB ROBOT & AINOVUM")
    logger.info("=============================================================================")
    accounts = load_accounts()
    tokens = load_tokens()
    isolated_evms = load_isolated_evm_wallets()

    logger.info(f"Loaded {len(accounts)} fleet accounts. Scanning thresholds...")

    async with aiohttp.ClientSession() as session:
        print("\n--- [1/2] Scanning AI Lab Robot Balances ($0.02 Threshold) ---")
        ailab_results = []
        for acc in accounts:
            res = await process_ailab_account(session, acc, tokens, isolated_evms)
            ailab_results.append(res)
            await asyncio.sleep(0.3)

        print("\n--- [2/2] Scanning Ainovum Available USDT (0.10 USDT Threshold) ---")
        ainovum_results = []
        for acc in accounts:
            res = await process_ainovum_account(session, acc, tokens, isolated_evms)
            ainovum_results.append(res)
            await asyncio.sleep(0.3)

        print("\n=============================================================================")
        print("                        WITHDRAWAL AUDIT SUMMARY")
        print("=============================================================================")
        print("🧪 AI LAB ROBOT:")
        for r in ailab_results:
            print(f"  • {r['name']:<18} ({r['uid']}): ${r.get('balance', 0):.4f} USD | Status: {r['status']}")

        print("\n🤖 AINOVUM:")
        for r in ainovum_results:
            print(f"  • {r['name']:<18} ({r['uid']}): {r.get('available', 0):.4f} USDT | Status: {r['status']}")
        print("=============================================================================\n")

if __name__ == "__main__":
    asyncio.run(main())
