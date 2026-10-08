#!/usr/bin/env python3
"""
execute_ailab_withdrawals.py
=============================================================================
Autonomous withdrawal engine for AI Lab Robot ($0.02 threshold).
Enforces:
  1. Host account (6727787768) 100% protected.
  2. Worker accounts withdraw to Binance Web3 Master (or dedicated isolated EVMs).
  3. Muted alerts (only verified on-chain transactions).
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
BINANCE_WALLET_2_EVM = "0x017841f26d5b79cc8c5eb20c65367bb645cc2610"
REPORT_BOT_TOKEN = os.getenv("REPORT_BOT_TOKEN", "8858823950:AAEdX47g7as1xLYEudfRUHaVGUdNIaU_ku8")
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
    # Strictly muted: only real on-chain transaction hashes trigger Telegram alerts
    return

async def process_ailab_account(session: aiohttp.ClientSession, acc: dict, tokens: dict, isolated_evms: dict = None) -> dict:
    uid = str(acc.get("user_id"))
    name = acc.get("name", uid)
    is_master = (uid == "6727787768" or acc.get("phone") in ("+8801317342850", "01317342850") or acc.get("is_primary"))
    proxy = acc.get("proxy")
    
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
        async with session.post(f"{base_url}/users/auth/login", json={"user": init_data}, headers=headers, timeout=aiohttp.ClientTimeout(total=8), proxy=proxy) as lr:
            if lr.status != 200:
                return {"uid": uid, "name": name, "status": f"login_http_{lr.status}", "balance": 0.0}
            try:
                ld = await lr.json()
            except Exception:
                return {"uid": uid, "name": name, "status": "invalid_login_json", "balance": 0.0}
            tok = ld.get("result", {}).get("bearer") or ld.get("user_info", {}).get("session_id")
            if not tok:
                return {"uid": uid, "name": name, "status": "no_bearer_token", "balance": 0.0}

        auth_headers = {**headers, "Authorization": f"Bearer {tok}"}

        # Step 2: Check cashout balance
        async with session.get(f"{base_url}/cashout", headers=auth_headers, timeout=aiohttp.ClientTimeout(total=8), proxy=proxy) as cr:
            if cr.status != 200:
                return {"uid": uid, "name": name, "status": f"cashout_http_{cr.status}", "balance": 0.0}
            try:
                cd = await cr.json()
            except Exception:
                return {"uid": uid, "name": name, "status": "invalid_cashout_json", "balance": 0.0}
            ubal = float(cd.get("user_info", {}).get("balance", 0) or 0)

        ailab_thresh = 0.02 if is_master else 1.00
        logger.info(f"[AI Lab] {name} ({uid}) balance: ${ubal:.4f} USD (Threshold: ${ailab_thresh:.2f}).")
        if ubal >= ailab_thresh:
            wd_usd = round(int(ubal * 100) / 100.0, 2)
            if uid == "6727787768":
                target_wallet = MASTER_EVM_VAULT
            elif uid == "8203342513":
                target_wallet = BINANCE_WALLET_2_EVM
            else:
                target_wallet = (acc.get("evm_wallet") or {}).get("address") or (isolated_evms.get(uid, {}).get("address") if isolated_evms else None) or MASTER_EVM_VAULT
            pay_payload = {
                "ps_id": 5,  # USDT (BEP20)
                "amount_usd": wd_usd,
                "wallet": target_wallet,
                "dest_tag": ""
            }
            # Execute Cashout
            async with session.post(f"{base_url}/cashout-pay", json=pay_payload, headers=auth_headers, timeout=aiohttp.ClientTimeout(total=10), proxy=proxy) as pr:
                try:
                    pres = await pr.json()
                except Exception:
                    pres = {"error": "non_json_cashout_response"}
                logger.info(f"[AI Lab] {name} cashout response: {pres}")
                err_code = pres.get("request_info", {}).get("error_code")
                if err_code == 0 or pres.get("result"):
                    role_str = "Main Host" if is_master else "Worker"
                    await send_telegram_alert(
                        session,
                        f"🎉 *AI Lab Auto-Cashout Submitted!*\n\n"
                        f"• *Account:* {name} ({role_str} - `{uid}`)\n"
                        f"• *Amount:* `${wd_usd} USD`\n"
                        f"• *Destination:* `{target_wallet}` (BEP-20)\n"
                        f"• *Status:* Approved / In Flight"
                    )
                    return {"uid": uid, "name": name, "status": "withdrawn", "balance": ubal, "amount": wd_usd, "details": pres}
                else:
                    return {"uid": uid, "name": name, "status": "cashout_rejected", "balance": ubal, "details": pres}

        return {"uid": uid, "name": name, "status": "below_threshold", "balance": ubal}

    except Exception as e:
        logger.warning(f"[AI Lab] Error for {name} ({uid}): {e}")
        return {"uid": uid, "name": name, "status": f"error_{e}", "balance": 0.0}

async def main():
    logger.info("Auto-withdrawals permanently disabled by user directive to prevent wrong-address routing. Fleet in 100% accumulation mode.")
    return

if __name__ == "__main__":
    asyncio.run(main())
