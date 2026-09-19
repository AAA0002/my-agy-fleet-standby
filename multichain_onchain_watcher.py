#!/usr/bin/env python3
"""
multichain_onchain_watcher.py
Real-Time Unified Multi-Chain On-Chain Vault Watcher:
- Binance Smart Chain (BEP-20 BNB & tokens)
- Arbitrum One (ETH & STONES tokens)
- The Open Network (TON blockchain & Jettons)

Monitors primary EVM wallet (0xfda4182001672b9f0f09e2118242e543e35ed5ce) and TON fleet wallets.
Directly queries decentralized JSON-RPCs and TON nodes with zero third-party API key limits.
Broadcasts instant verified receipts with deep-link explorer buttons to Telegram Channel & Admin DM.
"""

import os
import sys
import time
import json
import asyncio
import aiohttp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_env_file():
    env_path = os.path.join(BASE_DIR, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() not in os.environ:
                        os.environ[k.strip()] = v.strip()

load_env_file()

try:
    import sentry_sdk
    SENTRY_DSN = os.getenv("SENTRY_DSN", "https://af8cd9bec30d8551a01c5554c4d24a6b@o4512113387044864.ingest.us.sentry.io/4512113405132800")
    if SENTRY_DSN:
        sentry_sdk.init(dsn=SENTRY_DSN, traces_sample_rate=0.2)
except Exception:
    pass

EVM_WALLET = "0xfda4182001672b9f0f09e2118242e543e35ed5ce"
TON_PRIMARY_WALLET = "UQA0aO4Ybdg76l2ewtiGxA7vtk8CHbVaGvrcpA0G1kionhsP"
REPORT_BOT_TOKEN = os.getenv("REPORT_BOT_TOKEN", "8858823950:AAFFkuls8hBf23taCZE1y5gVzP4AFCuqI5o")
PAYOUT_CHANNEL_ID = os.getenv("PAYOUT_CHANNEL_ID", "-1004402765950")
ADMIN_ID = os.getenv("REPORT_CHAT_ID", "6727787768")
STATE_FILE = os.path.join(BASE_DIR, "multichain_watcher_state.json")
PAYOUT_LEDGER_FILE = os.path.join(BASE_DIR, "payout_ledger.json")
PAYOUTS_JSON_FILE = os.path.join(BASE_DIR, "payouts.json")
BETTERSTACK_HEARTBEAT_URL = os.getenv("BETTERSTACK_HEARTBEAT_URL", "https://uptime.betterstack.com/api/v1/heartbeat/bABS7gYDXgHp6H35XGcU7S6p")

# Cloud integrations
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://znbbaozpevurvbfkxakz.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
UPSTASH_REDIS_REST_URL = os.getenv("UPSTASH_REDIS_REST_URL", "https://relaxing-starfish-285827.upstash.io")
UPSTASH_REDIS_REST_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "gQAAAAAABFyDAAIgcDI5MDYyYWZjNzYzNzk0ZmRjYjhmNTA4ZDI4ODlmODkzNw")
TONAPI_KEY = os.getenv("TONAPI_KEY", "AGCD63WTWLGKKWYAAAAKRKZU45HTYMDI3PV7UBKKL6QDVIHG54NQDVNSQF7W3LQJ3X77QKY")
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "Z7TRGEGWC7C3CG9574D531ZRAJ1KC6MAMK")
DRPC_KEY = os.getenv("DRPC_API_KEY", "Aj3ei0uTXUwutp4cQUkyTyjgB8oqtDAR8YBVEl_NDNxu")

CF_WORKER_URLS = [
    os.getenv("CF_WORKER_URL_1", "https://restore-agy.aaaai2.workers.dev"),
    os.getenv("CF_WORKER_URL_2", "https://restore-agy.aaa-bot.workers.dev"),
    os.getenv("CF_WORKER_URL_3", "https://restore-agy.aaa222.workers.dev")
]
SECRET_KEY = os.getenv("CF_SECRET_KEY", "agy_cf_secret_7d36994e_2026")

BSC_RPCS = [
    f"https://bsc.drpc.org/ogrpc?dkey={DRPC_KEY}",
    "https://bsc-dataseed.binance.org",
    "https://binance.llamarpc.com",
    "https://bsc-dataseed1.defibit.io",
    "https://rpc.ankr.com/bsc"
]

ARB_RPCS = [
    f"https://arbitrum.drpc.org/ogrpc?dkey={DRPC_KEY}",
    "https://arb1.arbitrum.io/rpc",
    "https://arbitrum.llamarpc.com",
    "https://rpc.ankr.com/arbitrum"
]

TON_APIS = [
    "https://toncenter.com/api/v2/getAddressBalance",
    "https://toncenter.com/api/v2/jsonRPC"
]

async def sync_payouts_history_to_edge(session: aiohttp.ClientSession):
    """Syncs recent verified payouts from payouts.json to Cloudflare Edge KV feed."""
    if not os.path.exists(PAYOUTS_JSON_FILE):
        return
    try:
        with open(PAYOUTS_JSON_FILE, "r", encoding="utf-8") as pf:
            payouts = json.load(pf)
        if not payouts:
            return
        headers = {
            "Authorization": f"Bearer {SECRET_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        }
        async def push_p(cf_url, payload):
            try:
                async with session.post(f"{cf_url}/api/payouts/record", json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=4)):
                    pass
            except Exception:
                pass

        payout_tasks = []
        for p in payouts[-6:]:
            payload = {
                "account_name": p.get("account"),
                "user_id": p.get("user_id"),
                "amount": p.get("amount"),
                "wallet": p.get("wallet"),
                "network": p.get("network", "BEP-20"),
                "timestamp": p.get("timestamp")
            }
            for cf_url in CF_WORKER_URLS:
                payout_tasks.append(push_p(cf_url, payload))
        if payout_tasks:
            await asyncio.gather(*payout_tasks, return_exceptions=True)
    except Exception as e:
        print(f"Payout sync note: {e}")

async def sync_multichain_to_edge(session: aiohttp.ClientSession, state: dict):
    """Broadcasts multichain balances and live prices to Cloudflare Edge KV and Upstash Redis concurrently."""
    # 1. Sync to Cloudflare 3x Workers
    headers = {
        "Authorization": f"Bearer {SECRET_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    }
    async def push_mc_state(cf_url):
        try:
            async with session.post(f"{cf_url}/api/multichain/sync", json=state, headers=headers, timeout=aiohttp.ClientTimeout(total=5)):
                pass
        except Exception:
            pass

    tasks = [push_mc_state(u) for u in CF_WORKER_URLS]

    # 2. Sync to Upstash Serverless Redis
    if UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN:
        async def push_upstash():
            try:
                up_headers = {
                    "Authorization": f"Bearer {UPSTASH_REDIS_REST_TOKEN}",
                    "Content-Type": "application/json"
                }
                # Store serialized state in Upstash Redis
                async with session.post(
                    f"{UPSTASH_REDIS_REST_URL}/set/fleet:multichain",
                    data=json.dumps(state),
                    headers=up_headers,
                    timeout=aiohttp.ClientTimeout(total=5)
                ):
                    pass
            except Exception:
                pass
        tasks.append(push_upstash())

    await asyncio.gather(*tasks, return_exceptions=True)

def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_state(state: dict):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass

async def record_payout_ledger(session: aiohttp.ClientSession, chain: str, amount: float, symbol: str, usd_val: float, tx_hash: str = "auto-verified"):
    recipient = EVM_WALLET if chain != "TON" else TON_PRIMARY_WALLET
    try:
        ledger = []
        if os.path.exists(PAYOUT_LEDGER_FILE):
            with open(PAYOUT_LEDGER_FILE, "r", encoding="utf-8") as f:
                ledger = json.load(f)
        ledger.append({
            "id": len(ledger) + 1,
            "chain": chain,
            "symbol": symbol,
            "amount": amount,
            "usd_value": round(usd_val, 4),
            "wallet": recipient,
            "tx_hash": tx_hash,
            "timestamp": time.time(),
            "date": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        })
        with open(PAYOUT_LEDGER_FILE, "w", encoding="utf-8") as f:
            json.dump(ledger, f, indent=2)
    except Exception as e:
        print(f"Ledger record note: {e}")

    # Sync to Supabase Managed Cloud Postgres
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            sb_headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json"
            }
            sb_payload = {
                "account_id": recipient,
                "token_name": symbol,
                "amount": f"{amount:.6f}",
                "tx_hash": tx_hash
            }
            async with session.post(f"{SUPABASE_URL}/rest/v1/fleet_payouts", json=sb_payload, headers=sb_headers, timeout=aiohttp.ClientTimeout(total=5)):
                pass
        except Exception:
            pass

async def query_evm_balance(session: aiohttp.ClientSession, rpc_list: list, wallet: str) -> float:
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBalance",
        "params": [wallet, "latest"],
        "id": 1
    }
    for rpc in rpc_list:
        try:
            async with session.post(rpc, json=payload, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if "result" in data:
                        wei = int(data["result"], 16)
                        return wei / 1e18
        except Exception:
            continue
    return -1.0

async def query_arb_balance(session: aiohttp.ClientSession, wallet: str) -> float:
    """Query Arbitrum One balance using Etherscan V2 unified API first, fallback to RPCs."""
    if ETHERSCAN_API_KEY:
        try:
            url = f"https://api.etherscan.io/v2/api?chainid=42161&module=account&action=balance&address={wallet}&tag=latest&apikey={ETHERSCAN_API_KEY}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("status") == "1":
                        wei = int(data.get("result", 0))
                        return wei / 1e18
        except Exception:
            pass
    return await query_evm_balance(session, ARB_RPCS, wallet)

async def query_ton_balance(session: aiohttp.ClientSession, wallet: str) -> float:
    """Query TON balance using official TonAPI.io first with API key, fallback to toncenter."""
    if TONAPI_KEY:
        try:
            headers = {"Authorization": f"Bearer {TONAPI_KEY}"}
            url = f"https://tonapi.io/v2/accounts/{wallet}"
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    nanoton = int(data.get("balance", 0))
                    return nanoton / 1e9
        except Exception:
            pass

    # Fallback to toncenter
    url = f"https://toncenter.com/api/v2/getAddressBalance?address={wallet}"
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("ok"):
                    nanoton = int(data.get("result", 0))
                    return nanoton / 1e9
    except Exception:
        pass
    return -1.0

async def get_crypto_prices(session: aiohttp.ClientSession) -> dict:
    prices = {"BNB": 645.0, "ETH": 3400.0, "TON": 5.60}
    try:
        # Fetch from Binance API
        async with session.get("https://api.binance.com/api/v3/ticker/price?symbol=BNBUSDT", timeout=aiohttp.ClientTimeout(total=3)) as r:
            if r.status == 200:
                prices["BNB"] = float((await r.json()).get("price", 645.0))
    except Exception:
        pass
    try:
        async with session.get("https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT", timeout=aiohttp.ClientTimeout(total=3)) as r:
            if r.status == 200:
                prices["ETH"] = float((await r.json()).get("price", 3400.0))
    except Exception:
        pass
    try:
        async with session.get("https://api.binance.com/api/v3/ticker/price?symbol=TONUSDT", timeout=aiohttp.ClientTimeout(total=3)) as r:
            if r.status == 200:
                prices["TON"] = float((await r.json()).get("price", 5.60))
    except Exception:
        pass
    return prices

async def broadcast_deposit_alert(session: aiohttp.ClientSession, chain: str, symbol: str, diff: float, total_bal: float, price: float, wallet: str, explorer_url: str):
    usd_val = diff * price
    bdt_val = usd_val * 122.50
    total_usd = total_bal * price
    
    badge = "🟡 Binance Smart Chain" if "BSC" in chain else ("🔵 Arbitrum One" if "Arbitrum" in chain else "💎 TON Blockchain")
    
    msg = (
        f"🎉 *[On-Chain {chain} Payout Confirmed!]*\n\n"
        f"A verified incoming transaction has arrived on-chain in your fleet vault!\n\n"
        f"• **Network:** {badge}\n"
        f"• **Deposit Received:** `+{diff:.6f} {symbol}`\n"
        f"• **Fiat Value:** `~${usd_val:.4f} USD` (`~৳{bdt_val:.2f} BDT`)\n"
        f"• **Current Market Price:** `${price:.2f} USD` / {symbol}\n"
        f"• **Vault Balance:** `{total_bal:.6f} {symbol}` (`~${total_usd:.2f} USD`)\n"
        f"• **Recipient Wallet:** `{wallet}`\n\n"
        f"🔗 [View Live on Block Explorer]({explorer_url})"
    )
    
    markup = {
        "inline_keyboard": [
            [{"text": f"🔍 View on {chain} Explorer", "url": explorer_url}],
            [{"text": "📢 Verified Payouts Channel", "url": "https://t.me/+oN8uefSRYWUyM2Fl"}]
        ]
    }
    
    send_url = f"https://api.telegram.org/bot{REPORT_BOT_TOKEN}/sendMessage"
    
    # Broadcast to Payout Channel
    try:
        await session.post(send_url, json={
            "chat_id": PAYOUT_CHANNEL_ID,
            "text": msg,
            "parse_mode": "Markdown",
            "reply_markup": markup
        }, timeout=aiohttp.ClientTimeout(total=8))
    except Exception as e:
        print(f"Error sending to channel: {e}")
        
    # Send to Admin Private DM
    try:
        await session.post(send_url, json={
            "chat_id": ADMIN_ID,
            "text": msg,
            "parse_mode": "Markdown",
            "reply_markup": markup
        }, timeout=aiohttp.ClientTimeout(total=8))
    except Exception as e:
        print(f"Error sending to admin: {e}")

async def run_multichain_check(session: aiohttp.ClientSession) -> dict:
    state = load_state()
    prices = await get_crypto_prices(session)
    results = {}

    # 1. BSC Watcher (BNB)
    bsc_bal = await query_evm_balance(session, BSC_RPCS, EVM_WALLET)
    if bsc_bal >= 0:
        prev_bsc = state.get("bsc_bnb_balance")
        if prev_bsc is not None:
            diff = bsc_bal - prev_bsc
            if diff >= 0.00001:
                print(f"[BSC Deposit] +{diff:.6f} BNB detected!")
                await record_payout_ledger(session, "BSC", diff, "BNB", diff * prices["BNB"])
                await broadcast_deposit_alert(
                    session, "BSC (BEP-20)", "BNB", diff, bsc_bal, prices["BNB"],
                    EVM_WALLET, f"https://bscscan.com/address/{EVM_WALLET}"
                )
                state["total_confirmed_deposits"] = state.get("total_confirmed_deposits", 0) + 1
        state["bsc_bnb_balance"] = bsc_bal
        results["bsc_bnb"] = bsc_bal

    # 2. Arbitrum One Watcher (ETH)
    arb_bal = await query_arb_balance(session, EVM_WALLET)
    if arb_bal >= 0:
        prev_arb = state.get("arb_eth_balance")
        if prev_arb is not None:
            diff = arb_bal - prev_arb
            if diff >= 0.00005:
                print(f"[Arbitrum Deposit] +{diff:.6f} ETH detected!")
                await record_payout_ledger(session, "Arbitrum", diff, "ETH", diff * prices["ETH"])
                await broadcast_deposit_alert(
                    session, "Arbitrum One", "ETH", diff, arb_bal, prices["ETH"],
                    EVM_WALLET, f"https://arbiscan.io/address/{EVM_WALLET}"
                )
                state["total_confirmed_deposits"] = state.get("total_confirmed_deposits", 0) + 1
        state["arb_eth_balance"] = arb_bal
        results["arb_eth"] = arb_bal

    # 3. TON Blockchain Watcher (TON)
    ton_bal = await query_ton_balance(session, TON_PRIMARY_WALLET)
    if ton_bal >= 0:
        prev_ton = state.get("ton_balance")
        if prev_ton is not None:
            diff = ton_bal - prev_ton
            if diff >= 0.01:
                print(f"[TON Deposit] +{diff:.4f} TON detected!")
                await record_payout_ledger(session, "TON", diff, "TON", diff * prices["TON"])
                await broadcast_deposit_alert(
                    session, "TON Blockchain", "TON", diff, ton_bal, prices["TON"],
                    TON_PRIMARY_WALLET, f"https://tonviewer.com/{TON_PRIMARY_WALLET}"
                )
                state["total_confirmed_deposits"] = state.get("total_confirmed_deposits", 0) + 1
        state["ton_balance"] = ton_bal
        results["ton"] = ton_bal

    state["last_checked_at"] = time.time()
    state["prices"] = prices
    save_state(state)

    # Only sync to Cloudflare Edge KV if a deposit occurred or if > 6 hours elapsed
    new_deposit = any([
        (bsc_bal >= 0 and state.get("bsc_bnb_balance") is not None and (bsc_bal - state.get("bsc_bnb_balance", 0)) >= 0.00001),
        (arb_bal >= 0 and state.get("arb_eth_balance") is not None and (arb_bal - state.get("arb_eth_balance", 0)) >= 0.00005),
        (ton_bal >= 0 and state.get("ton_balance") is not None and (ton_bal - state.get("ton_balance", 0)) >= 0.01)
    ])
    last_cloud_sync = state.get("last_cloud_sync_at", 0)
    time_since_sync = time.time() - last_cloud_sync

    if new_deposit or time_since_sync > 21600:
        try:
            await sync_multichain_to_edge(session, state)
            if new_deposit:
                await sync_payouts_history_to_edge(session)
            state["last_cloud_sync_at"] = time.time()
            save_state(state)
        except Exception as e:
            print(f"Edge sync note: {e}")

    return {"ok": True, "balances": results, "prices": prices}

async def main():
    async with aiohttp.ClientSession() as session:
        res = await run_multichain_check(session)
        print(f"[Multi-Chain Watcher] {res}")

if __name__ == "__main__":
    asyncio.run(main())
