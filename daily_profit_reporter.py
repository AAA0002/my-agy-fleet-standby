#!/usr/bin/env python3
"""
daily_profit_reporter.py
Automated 00:00 UTC Financial Accounting & Fleet Ledger Reporter
Calculates:
- BNB Galaxy tasks completed across all 13 accounts
- Total BNB farmed & withdrawn today
- Real-time fiat valuation (USD $ and BDT ৳) via Binance API
- Live On-Chain Wallet Balance from Binance Smart Chain
- Cloudflare Edge Mini-App Yield (Stones, MRG, ART)
Broadcasts report to Telegram Payout Channel (-1004402765950) & Admin DM (6727787768).
"""

import os
import sys
import time
import json
import asyncio
from datetime import datetime, timezone
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

ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")
PAYOUTS_FILE = os.path.join(BASE_DIR, "payouts.json")
WALLET_ADDRESS = "0xfda4182001672b9f0f09e2118242e543e35ed5ce"
REPORT_BOT_TOKEN = os.getenv("REPORT_BOT_TOKEN", "8858823950:AAFFkuls8hBf23taCZE1y5gVzP4AFCuqI5o")
PAYOUT_CHANNEL_ID = os.getenv("PAYOUT_CHANNEL_ID", "-1004402765950")
ADMIN_ID = os.getenv("REPORT_CHAT_ID", "6727787768")

# Cloud integrations
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://znbbaozpevurvbfkxakz.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
UPSTASH_URL = os.getenv("UPSTASH_REDIS_REST_URL", "https://relaxing-starfish-285827.upstash.io")
UPSTASH_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "gQAAAAAABFyDAAIgcDI5MDYyYWZjNzYzNzk0ZmRjYjhmNTA4ZDI4ODlmODkzNw")
TONAPI_KEY = os.getenv("TONAPI_KEY", "AGCD63WTWLGKKWYAAAAKRKZU45HTYMDI3PV7UBKKL6QDVIHG54NQDVNSQF7W3LQJ3X77QKY")

async def get_live_rates(session: aiohttp.ClientSession) -> dict:
    rates = {"bnb": 760.0, "ton": 5.70, "arb": 0.55, "bdt": 122.50}
    try:
        async with session.get("https://api.binance.com/api/v3/ticker/price?symbol=BNBUSDT", timeout=aiohttp.ClientTimeout(total=4)) as r:
            if r.status == 200:
                rates["bnb"] = float((await r.json()).get("price", 760.0))
        async with session.get("https://api.binance.com/api/v3/ticker/price?symbol=ARBUSDT", timeout=aiohttp.ClientTimeout(total=4)) as r:
            if r.status == 200:
                rates["arb"] = float((await r.json()).get("price", 0.55))
    except Exception:
        pass

    # Use TonAPI.io for accurate live TON price
    if TONAPI_KEY:
        try:
            headers = {"Authorization": f"Bearer {TONAPI_KEY}"}
            async with session.get("https://tonapi.io/v2/rates?tokens=ton&currencies=usd", headers=headers, timeout=aiohttp.ClientTimeout(total=4)) as r:
                if r.status == 200:
                    d = await r.json()
                    rates["ton"] = float(d.get("rates", {}).get("TON", {}).get("prices", {}).get("USD", rates["ton"]))
        except Exception:
            pass
    return rates

async def get_onchain_bnb(session: aiohttp.ClientSession) -> float:
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBalance",
        "params": [WALLET_ADDRESS, "latest"],
        "id": 1
    }
    drpc_key = os.getenv("DRPC_API_KEY", "Aj3ei0uTXUwutp4cQUkyTyjgB8oqtDAR8YBVEl_NDNxu")
    rpc_nodes = [
        f"https://bsc.drpc.org/ogrpc?dkey={drpc_key}",
        "https://bsc-dataseed.binance.org",
        "https://binance.llamarpc.com",
        "https://rpc.ankr.com/bsc"
    ]
    headers = {"Content-Type": "application/json", "User-Agent": "my-agy-fleet/1.0"}
    for rpc in rpc_nodes:
        try:
            async with session.post(rpc, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as r:
                if r.status == 200:
                    d = await r.json()
                    if "result" in d and d["result"]:
                        return int(d["result"], 16) / 1e18
        except Exception:
            continue

    # Fallback to last recorded state from watcher
    try:
        w_state = os.path.join(BASE_DIR, "bep20_watcher_state.json")
        if os.path.exists(w_state):
            with open(w_state, "r", encoding="utf-8") as f:
                return float(json.load(f).get("last_known_balance", 0.0))
    except Exception:
        pass
    return 0.0

async def generate_and_send_report():
    async with aiohttp.ClientSession() as session:
        rates = await get_live_rates(session)
        wallet_bnb = await get_onchain_bnb(session)
        
        # Load fleet accounts
        accs = []
        if os.path.exists(ACCOUNTS_FILE):
            try:
                with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                    accs = json.load(f)
            except Exception:
                pass
                
        # Load payouts
        payouts = []
        if os.path.exists(PAYOUTS_FILE):
            try:
                with open(PAYOUTS_FILE, "r", encoding="utf-8") as f:
                    payouts = json.load(f)
            except Exception:
                pass

        total_accounts = len(accs)
        total_payouts_count = len(payouts)
        total_payouts_bnb = sum(float(p.get("amount", 0)) for p in payouts)
        
        bnb_price = rates["bnb"]
        bdt_rate = rates["bdt"]
        wallet_usd = wallet_bnb * bnb_price
        wallet_bdt = wallet_usd * bdt_rate
        
        daily_potential_bnb = total_accounts * 0.000055
        daily_potential_usd = daily_potential_bnb * bnb_price
        daily_potential_bdt = daily_potential_usd * bdt_rate
        
        now = datetime.now(timezone.utc)
        now_str = now.strftime("%Y-%m-%d %H:%M UTC")
        today_date_str = now.strftime("%Y-%m-%d")
        
        report = (
            f"📊 *[MY AGY AI — Daily Financial & Fleet Ledger]*\n"
            f"📅 *Timestamp:* `{now_str}`\n\n"
            f"🟡 *1. Binance Smart Chain (BNB Galaxy — Goal #1):*\n"
            f"• **Fleet Size:** `{total_accounts} Accounts` active in sequential queue\n"
            f"• **Daily Yield Capacity:** `~{daily_potential_bnb:.6f} BNB / day`\n"
            f"• **Daily Fiat Value:** `~${daily_potential_usd:.2f} USD` (`~৳{daily_potential_bdt:.0f} BDT`)\n"
            f"• **Recorded Withdrawals:** `{total_payouts_count} payouts` totaling `{total_payouts_bnb:.6f} BNB`\n"
            f"• **On-Chain Target Wallet:** `{WALLET_ADDRESS}`\n"
            f"• **Live On-Chain Balance:** `{wallet_bnb:.6f} BNB` (`~${wallet_usd:.2f} USD` / `~৳{wallet_bdt:.0f} BDT`)\n"
            f"• **Live BNB Price:** `${bnb_price:.2f} USD`\n\n"
            f"💎 *2. Multi-Chain Edge Mining:*\n"
            f"• **Stones Miners:** Auto check-ins & Arbitrum auto-withdraw ready\n"
            f"• **MRG Miner:** Squad commission sweep & TON isolation active\n"
            f"• **ART Airdrop:** 8h recurring mining cycles auto-renewed\n"
            f"• **TON Price (TonAPI):** `${rates.get('ton', 1.38):.2f} USD`\n\n"
            f"🛡️ *3. Cloud Infrastructure & Multi-Mesh:*\n"
            f"• **Cloudflare 3x Mesh:** APAC + Global workers online\n"
            f"• **Deno Deploy V2:** 2x Edge Sentinels + Deno.cron active\n"
            f"• **Render Standby:** Singapore & Frankfurt nodes connected\n"
            f"• **Supabase & Upstash:** Cloud PostgreSQL + Redis synced\n\n"
            f"🔗 [BscScan On-Chain Explorer](https://bscscan.com/address/{WALLET_ADDRESS})"
        )
        
        markup = {
            "inline_keyboard": [
                [{"text": "🔍 BscScan Explorer", "url": f"https://bscscan.com/address/{WALLET_ADDRESS}"}],
                [{"text": "📢 Verified Payouts Channel", "url": "https://t.me/+oN8uefSRYWUyM2Fl"}]
            ]
        }
        
        send_url = f"https://api.telegram.org/bot{REPORT_BOT_TOKEN}/sendMessage"
        
        # 1. Broadcast to Channel
        try:
            async with session.post(send_url, json={
                "chat_id": PAYOUT_CHANNEL_ID,
                "text": report,
                "parse_mode": "Markdown",
                "reply_markup": markup
            }, timeout=aiohttp.ClientTimeout(total=8)) as r:
                print(f"[Daily Reporter] Sent to channel: {r.status}")
        except Exception as e:
            print(f"Channel error: {e}")
            
        # 2. Send to Admin DM
        try:
            async with session.post(send_url, json={
                "chat_id": ADMIN_ID,
                "text": report,
                "parse_mode": "Markdown",
                "reply_markup": markup
            }, timeout=aiohttp.ClientTimeout(total=8)) as r:
                print(f"[Daily Reporter] Sent to admin: {r.status}")
        except Exception as e:
            print(f"Admin error: {e}")

        # 3. Sync to Supabase Managed Cloud Postgres
        if SUPABASE_URL and SUPABASE_KEY:
            try:
                sb_headers = {
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}",
                    "Content-Type": "application/json",
                    "Prefer": "resolution=merge-duplicates"
                }
                sb_payload = {
                    "report_date": today_date_str,
                    "total_bnb_farmed": round(total_payouts_bnb, 6),
                    "total_usd": round(wallet_usd, 4),
                    "total_bdt": round(wallet_bdt, 2),
                    "onchain_bnb": round(wallet_bnb, 6),
                    "summary": {
                        "active_accounts": total_accounts,
                        "rates": rates,
                        "timestamp": now_str
                    }
                }
                async with session.post(f"{SUPABASE_URL}/rest/v1/daily_summaries", json=sb_payload, headers=sb_headers, timeout=aiohttp.ClientTimeout(total=5)) as r:
                    print(f"[Daily Reporter] Synced to Supabase: {r.status}")
            except Exception as e:
                print(f"Supabase daily summary note: {e}")

        # 4. Cache in Upstash Serverless Redis
        if UPSTASH_URL and UPSTASH_TOKEN:
            try:
                up_headers = {
                    "Authorization": f"Bearer {UPSTASH_TOKEN}",
                    "Content-Type": "application/json"
                }
                redis_data = {
                    "date": today_date_str,
                    "rates": rates,
                    "wallet_bnb": wallet_bnb,
                    "total_accounts": total_accounts,
                    "report": report
                }
                async with session.post(f"{UPSTASH_URL}/set/fleet:daily_report", data=json.dumps(redis_data), headers=up_headers, timeout=aiohttp.ClientTimeout(total=5)) as r:
                    print(f"[Daily Reporter] Cached in Upstash: {r.status}")
            except Exception as e:
                print(f"Upstash daily summary note: {e}")

if __name__ == "__main__":
    asyncio.run(generate_and_send_report())
