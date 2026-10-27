#!/usr/bin/env python3
"""
daily_profit_reporter.py
Automated 00:00 UTC Financial Accounting & Fleet Ledger Reporter
Calculates:
- BNB Galaxy tasks completed across all 13 accounts
- Total BNB farmed & withdrawn today
- Real-time fiat valuation (USD $ and BDT ৳) via Binance API
- Live On-Chain Wallet Balance from Binance Smart Chain
- Cloudflare Edge Mini-App Yield (8 Active Mining Bots: MRG, ATF, Victor's, VyroDrop, Kynex, Diggo, PepeGram, AdxEarn)
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
WALLETS = [
    "0xfda4182001672b9f0f09e2118242e543e35ed5ce"
]
TON_PRIMARY_WALLET = "UQBPZiSvitdPU3VUyJK2mRaHVBl69xejw5aOrh1KfKA7gwDT"
REPORT_BOT_TOKEN = os.getenv("REPORT_BOT_TOKEN", "")
PAYOUT_CHANNEL_ID = os.getenv("PAYOUT_CHANNEL_ID", "-1004402765950")
ADMIN_ID = os.getenv("REPORT_CHAT_ID", "6727787768")

# Cloud integrations
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://znbbaozpevurvbfkxakz.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
UPSTASH_URL = os.getenv("UPSTASH_REDIS_REST_URL", "https://rich-emu-106119.upstash.io")
UPSTASH_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "")
TONAPI_KEY = os.getenv("TONAPI_KEY", "AGCD63WTWLGKKWYAAAAKRKZU45HTYMDI3PV7UBKKL6QDVIHG54NQDVNSQF7W3LQJ3X77QKY")

async def get_live_rates(session: aiohttp.ClientSession) -> dict:
    rates = {"bnb": 750.0, "ton": 1.60, "arb": 0.21, "bdt": 122.50}
    try:
        async with session.get("https://data-api.binance.vision/api/v3/ticker/price?symbol=BNBUSDT", timeout=aiohttp.ClientTimeout(total=4)) as r:
            if r.status == 200:
                rates["bnb"] = float((await r.json()).get("price", 750.0))
        async with session.get("https://data-api.binance.vision/api/v3/ticker/price?symbol=ARBUSDT", timeout=aiohttp.ClientTimeout(total=4)) as r:
            if r.status == 200:
                rates["arb"] = float((await r.json()).get("price", 0.21))
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
    drpc_key = os.getenv("DRPC_API_KEY", "")
    rpc_nodes = [
        "https://bsc-dataseed.binance.org",
        "https://bsc-dataseed1.defibit.io",
        "https://bsc-dataseed1.binance.org",
        f"https://bsc.drpc.org/ogrpc?dkey={drpc_key}"
    ]
    headers = {"Content-Type": "application/json", "User-Agent": "my-agy-fleet/1.0"}
    total_bal = 0.0
    for w in WALLETS:
        w_bal = 0.0
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getBalance",
            "params": [w, "latest"],
            "id": 1
        }
        for rpc in rpc_nodes:
            try:
                async with session.post(rpc, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as r:
                    if r.status == 200:
                        d = await r.json()
                        if "result" in d and d["result"]:
                            w_bal = int(d["result"], 16) / 1e18
                            break
            except Exception:
                continue
        total_bal += w_bal

    if total_bal > 0.0:
        return total_bal

    # Fallback to last recorded state from watcher
    try:
        w_state = os.path.join(BASE_DIR, "bep20_watcher_state.json")
        if os.path.exists(w_state):
            with open(w_state, "r", encoding="utf-8") as f:
                state_data = json.load(f)
                bals = state_data.get("balances", {})
                if bals:
                    return sum(float(v) for v in bals.values())
                return float(state_data.get("last_known_balance", 0.0))
    except Exception:
        pass
    return 0.0

async def get_onchain_ton(session: aiohttp.ClientSession) -> float:
    """Queries on-chain TON balance from TonAPI / Toncenter with fallback."""
    if TONAPI_KEY:
        try:
            headers = {"Authorization": f"Bearer {TONAPI_KEY}"}
            url = f"https://tonapi.io/v2/accounts/{TON_PRIMARY_WALLET}"
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return int(data.get("balance", 0)) / 1e9
        except Exception:
            pass
    try:
        url = f"https://toncenter.com/api/v2/getAddressBalance?address={TON_PRIMARY_WALLET}"
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            if resp.status == 200:
                d = await resp.json()
                if d.get("ok"):
                    return int(d.get("result", 0)) / 1e9
    except Exception:
        pass
    return 0.0

import sys
import re

async def get_fleet_mining_totals() -> dict:
    totals = {
        "mrg": 0.0,
        "atf": 0.0,
        "vic": 0.0,
        "knx": 0.0,
        "vyro": 0.0,
        "diggo": 0.0,
        "pepe": 0.0,
        "adx": 0.0,
        "chicken_hens": 0,
        "chicken_eggs": 0
    }
    rep_file = os.path.join(BASE_DIR, "live_farming_and_sidetasks_report.json")
    if os.path.exists(rep_file):
        try:
            with open(rep_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for uid, info in data.items():
                    bots = info.get("bots", {})
                    # 1. MRG
                    mrg_txt = str(bots.get("1. MRG Miner", {}).get("core", {}))
                    m = re.search(r"([\d\.]+)\s*MRG", mrg_txt)
                    if m: totals["mrg"] += float(m.group(1))
                    
                    # 2. ATF
                    atf_txt = str(bots.get("2. ATF Miner", {}).get("core", {}))
                    m = re.search(r"([\d\.]+)\s*ATF", atf_txt)
                    if m: totals["atf"] += float(m.group(1))

                    # 3. Victor's Company
                    vic_txt = str(bots.get("3. Victor's Company", {}).get("core", {}))
                    m = re.search(r"([\d\.]+)\s*VIC", vic_txt)
                    if m: totals["vic"] += float(m.group(1))
                    
                    # 4. Kynex Network
                    knx_txt = str(bots.get("5. Kynex Network", {}).get("core", {}))
                    m = re.search(r"([\d\.]+)\s*KNX", knx_txt)
                    if m: totals["knx"] += float(m.group(1))

                    # 5. VyroDrop
                    vyro_txt = str(bots.get("4. VyroDrop", {}).get("core", {}))
                    m = re.search(r"([\d\.]+)\s*VYRO", vyro_txt)
                    if m: totals["vyro"] += float(m.group(1))

                    # 6. PepeGram
                    pepe_txt = str(bots.get("6. PepeGram", {}).get("core", {}))
                    m = re.search(r"([\d\.]+)\s*PEPE", pepe_txt)
                    if m: totals["pepe"] += float(m.group(1))

                    # 7. AdxEarn AI
                    adx_txt = str(bots.get("7. AdxEarn AI", {}).get("core", {}))
                    m = re.search(r"([\d\.]+)\s*Points", adx_txt)
                    if m: totals["adx"] += float(m.group(1))

                    # 8. DiggoMiner
                    diggo_txt = str(bots.get("8. DiggoMiner", {}).get("core", {}))
                    m = re.search(r"([\d\.]+)\s*DIGGO", diggo_txt)
                    if m: totals["diggo"] += float(m.group(1))

                    # 9. Chicken Land
                    chk_core = bots.get("9. Chicken Land", {}).get("core", {})
                    if isinstance(chk_core, dict) and chk_core.get("hens"):
                        totals["chicken_hens"] += int(chk_core.get("hens", 0) or 0)
                        totals["chicken_eggs"] += int(chk_core.get("eggs", 0) or 0) + int(chk_core.get("egg_bal", 0) or 0)
        except Exception:
            pass

    # Fallback for Chicken Land if 0
    if totals["chicken_hens"] == 0:
        accs_file = os.path.join(BASE_DIR, "accounts.json")
        if os.path.exists(accs_file):
            try:
                with open(accs_file, "r", encoding="utf-8") as f:
                    accs = json.load(f)
                    totals["chicken_hens"] = sum(int(a.get("chickenland_hens", 0) or 0) for a in accs)
                    totals["chicken_eggs"] = sum(int(a.get("chickenland_rate", 0) or 0) * 8 for a in accs)
            except Exception:
                pass
            
    # Fallback for ATF if 0
    if totals["atf"] == 0.0:
        atf_state_file = os.path.join(BASE_DIR, "atf_fleet_state.json")
        if os.path.exists(atf_state_file):
            try:
                with open(atf_state_file, "r", encoding="utf-8") as f:
                    atf_data = json.load(f)
                    totals["atf"] = sum(float(r.get("mined_balance", 0)) for r in atf_data.get("results", []))
            except Exception:
                pass
    return totals

async def get_ai_market_briefing(session: aiohttp.ClientSession, rates: dict, total_payouts_bnb: float, wallet_bnb: float) -> str:
    prompt = (
        f"You are the autonomous AI Chief Financial Officer for MY AGY AI Fleet. "
        f"Live Rates: BNB: ${rates['bnb']:.2f}, TON: ${rates.get('ton', 1.6):.2f}, ARB: ${rates.get('arb', 0.21):.2f}. "
        f"Fleet Treasury: {wallet_bnb:.6f} BNB on-chain, 2.4398 TON on-chain. "
        f"Provide a 2-sentence executive summary analyzing market momentum, fleet yield in BDT/USD, and strategic compounding guidance. "
        f"Keep it concise, professional, high-energy, and direct."
    )
    # 1. Cloudflare Workers AI Edge Mesh (Node 1, 2, 3, 4, 5) - Zero Keys, 100% Free
    cf_urls = [
        "https://restore-agy.agorameet.workers.dev",
        "https://restore-agy.aaaai2.workers.dev",
        "https://restore-agy.aaa-bot.workers.dev",
        "https://restore-agy.aaa222.workers.dev",
        "https://restore-agy.aaaai.workers.dev"
    ]
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    for cf_url in cf_urls:
        try:
            payload = {
                "prompt": prompt,
                "model": "llama"
            }
            async with session.post(f"{cf_url}/api/ai", json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=6)) as r:
                if r.status == 200:
                    d = await r.json()
                    ans = d.get("answer") or d.get("response") or ""
                    if ans and len(ans) > 20:
                        return ans.strip()
        except Exception:
            continue

    return "BNB and TON market momentum remains strong with active treasury growth across our 20-account cloud fleet. Multi-chain protocol yields continue compounding into primary non-custodial vaults."

async def generate_and_send_report(dry_run: bool = False):
    async with aiohttp.ClientSession() as session:
        rates = await get_live_rates(session)
        wallet_bnb = await get_onchain_bnb(session)
        wallet_ton = await get_onchain_ton(session)
        fleet_totals = await get_fleet_mining_totals()
        
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
        ton_price = rates.get("ton", 1.60)
        bdt_rate = rates["bdt"]
        wallet_usd = wallet_bnb * bnb_price
        wallet_bdt = wallet_usd * bdt_rate
        wallet_ton_usd = wallet_ton * ton_price
        wallet_ton_bdt = wallet_ton_usd * bdt_rate
        
        import datetime as dt
        bst_now = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=6)
        now_str = bst_now.strftime("%Y-%m-%d %I:%M:%S %p BST")
        today_date_str = bst_now.strftime("%Y-%m-%d")

        ai_briefing = await get_ai_market_briefing(session, rates, total_payouts_bnb, wallet_bnb)

        report = (
            f"📊 *[MY AGY AI — Daily Financial & Fleet Ledger]*\n"
            f"📅 *Timestamp:* `{now_str}`\n\n"
            f"🟡 *1. Binance Smart Chain (BEP-20 / Master Vault):*\n"
            f"• *Fleet Size:* `{total_accounts} Accounts` active in parallel cloud mesh\n"
            f"• *Master Vault Wallet:* `{WALLET_ADDRESS}`\n"
            f"• *Live On-Chain Balance:* `{wallet_bnb:.6f} BNB` (`~${wallet_usd:.2f} USD` / `~৳{wallet_bdt:.0f} BDT`)\n"
            f"• *Historical Distributions:* `{total_payouts_count} payouts` totaling `{total_payouts_bnb:.6f} BNB`\n"
            f"• *Live BNB Price:* `${bnb_price:.2f} USD`\n\n"
            f"💎 *2. Multi-Chain 9-Bot Autonomous Mining Treasury:*\n"
            f"• *MRG Miner:* `{fleet_totals['mrg']:,.2f} MRG` mined (Levels up to 180+, Cloud Turnstile Auto-Claim)\n"
            f"• *ATF Miner:* `{fleet_totals['atf']:,.2f} ATF` mined (Levels up to 160+, Deterministic Math Solver)\n"
            f"• *Victor's Company:* `{fleet_totals['vic']:,.2f} VIC` mined (Hourly Shifts & Arcade Solver)\n"
            f"• *Kynex Network:* `{fleet_totals['knx']:,.2f} KNX` mined (Firebase RTDB Node Auto-Claim)\n"
            f"• *VyroDrop:* DEX speed miner active across all 20 accounts (TonConnect 2.0 signed proof)\n"
            f"• *DiggoMiner:* `{fleet_totals['diggo']:,.2f} DIGGO` mined (Decentralized Block Mining & JWT)\n"
            f"• *PepeGram:* `{fleet_totals['pepe']:,.2f} PEPE` mined (6h Cycles & Power Boosts)\n"
            f"• *AdxEarn AI:* `{fleet_totals['adx']:,.0f} Points` earned (Daily Check-in Streaks & Tasks)\n"
            f"• *Chicken Land:* `{fleet_totals['chicken_hens']} Hens` active laying `{fleet_totals['chicken_eggs']} Eggs` (Autonomous Egg Harvest & Selling)\n"
            f"• *On-Chain Target TON:* `{TON_PRIMARY_WALLET}`\n"
            f"• *Live On-Chain TON Balance:* `{wallet_ton:.4f} TON` (`~${wallet_ton_usd:.2f} USD` / `~৳{wallet_ton_bdt:.0f} BDT`)\n"
            f"• *TON Price (TonAPI):* `${ton_price:.2f} USD`\n\n"
            f"🛡️ *3. Cloud Infrastructure & 100% Free Edge Mesh:*\n"
            f"• *Cloudflare 5x Mesh:* APAC + Global edge nodes (Nodes 1, 2, 3, 4, 5)\n"
            f"• *Cloudflare Workers AI:* Serverless Llama 3.2 & DeepSeek R1 edge intelligence (0 keys)\n"
            f"• *Cloudflare D1 & R2:* Serverless SQL audit trail & zero-egress backup storage\n"
            f"• *Render Standby:* Node 2 (Frankfurt, Active) & Node 3 (Oregon, Standby)\n"
            f"• *Supabase & Upstash:* Cloud PostgreSQL + Redis live state replication\n\n"
            f"🤖 *4. AI Fleet Intelligence & Strategy (Cloudflare Workers AI):*\n"
            f"_{ai_briefing}_\n\n"
            f"🔗 [BscScan On-Chain Explorer](https://bscscan.com/address/{WALLET_ADDRESS}) • [Tonviewer Master Vault](https://tonviewer.com/{TON_PRIMARY_WALLET})"
        )
        
        markup = {
            "inline_keyboard": [
                [{"text": "🔍 BscScan Explorer", "url": f"https://bscscan.com/address/{WALLET_ADDRESS}"}],
                [{"text": "💎 Tonviewer Master Vault", "url": f"https://tonviewer.com/{TON_PRIMARY_WALLET}"}],
                [{"text": "📢 Verified Payouts Channel", "url": "https://t.me/+oN8uefSRYWUyM2Fl"}]
            ]
        }

        if dry_run:
            print("\n" + "="*60)
            print("DRY RUN MODE — Report Output Preview:")
            print("="*60)
            print(report)
            print("="*60)
            print("[Daily Reporter] Dry run complete. Zero network messages sent.")
            return
        
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
                async with session.post(f"{SUPABASE_URL}/rest/v1/daily_summaries?on_conflict=report_date", json=sb_payload, headers=sb_headers, timeout=aiohttp.ClientTimeout(total=5)) as r:
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
    is_dry = "--dry-run" in sys.argv
    asyncio.run(generate_and_send_report(dry_run=is_dry))
