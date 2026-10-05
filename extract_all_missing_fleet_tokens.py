#!/usr/bin/env python3
"""
extract_all_missing_fleet_tokens.py
Batch-extracts missing WebApp initData tokens (TRX Power, FINVORA, TurboGram, USDT QUAD)
across all 18 fleet accounts in accounts.json and updates fleet_miniapp_tokens.json.
Synchronizes fresh tokens across all 5 Cloudflare Edge Worker nodes.
"""

import os
import sys
import json
import time
import asyncio
import urllib.parse
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import RequestWebViewRequest
from proxy_manager import get_account_fingerprint

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")
TOKENS_FILE = os.path.join(BASE_DIR, "fleet_miniapp_tokens.json")

API_ID = 37321306
API_HASH = "5cd9e5c464c1e4c76b911c750ba42cbb"

TARGET_BOTS = [
    {
        "key": "trxpower_init_data",
        "bot": "trxpowermining_bot",
        "url": "https://eb0frexrmrfl9pgywxd8ebxo.187.53.139.6.sslip.io/",
        "name": "TRX Power Mining"
    },
    {
        "key": "finvora_init_data",
        "bot": "FINVORAWeb3bot",
        "url": "https://finvora-production.up.railway.app/",
        "name": "FINVORA Web3"
    },
    {
        "key": "turbogram_init_data",
        "bot": "TurboGramV1_bot",
        "url": "https://turbo.tamimdev.dev/",
        "name": "TurboGram V1"
    },
    {
        "key": "usdtquad_init_data",
        "bot": "usdtquadbot",
        "url": "https://ustdquad.up.railway.app/",
        "name": "USDT QUAD"
    }
]

CF_WORKERS = [
    "https://restore-agy.aaaai2.workers.dev",
    "https://restore-agy.aaa-bot.workers.dev",
    "https://restore-agy.aaa222.workers.dev",
    "https://restore-agy.agorameet.workers.dev",
    "https://restore-agy.aaaai.workers.dev"
]
CF_SECRET = "agy_cf_secret_7d36994e_2026"

def parse_init_data(url_str):
    if not url_str:
        return None
    p = urllib.parse.urlparse(url_str)
    frag = urllib.parse.parse_qs(p.fragment).get("tgWebAppData", [None])[0]
    if frag:
        return frag
    query = urllib.parse.parse_qs(p.query).get("tgWebAppData", [None])[0]
    return query

async def process_account(acc, idx, total, tokens_data):
    name = acc.get("name", f"Account #{idx}")
    uid = str(acc.get("user_id"))
    sess = acc.get("session_string")

    if not sess:
        print(f"[{idx}/{total}] ⚠️ Skipping {name} ({uid}): No session string")
        return

    acc_tokens = tokens_data.setdefault(uid, {
        "name": name,
        "user_id": uid,
        "updated_at": time.time()
    })

    needed = [b for b in TARGET_BOTS if not acc_tokens.get(b["key"])]
    if not needed:
        print(f"[{idx}/{total}] ✅ {name} ({uid}) already has all target tokens.")
        return

    print(f"\n=======================================================")
    print(f"[{idx}/{total}] 🚀 Extracting for {name} ({uid}) — Missing: {[b['name'] for b in needed]}")
    print(f"=======================================================")

    acc_fp = get_account_fingerprint(int(uid) if uid.isdigit() else 0)
    cl = TelegramClient(StringSession(sess), API_ID, API_HASH, **acc_fp)
    try:
        await cl.connect()
        if not await cl.is_user_authorized():
            print(f"  ❌ Session unauthorized for {name}")
            return

        for bot_info in needed:
            b_key = bot_info["key"]
            b_username = bot_info["bot"]
            b_url = bot_info["url"]
            b_title = bot_info["name"]

            try:
                b_entity = await cl.get_entity(b_username)
                res = await cl(RequestWebViewRequest(
                    peer=b_entity,
                    bot=b_entity,
                    platform="android",
                    url=b_url
                ))
                init_data = parse_init_data(getattr(res, "url", None))
                if init_data:
                    acc_tokens[b_key] = init_data
                    acc_tokens["updated_at"] = time.time()
                    print(f"  🔑 Extracted {b_title} token: {init_data[:30]}...")
                else:
                    print(f"  ⚠️ No tgWebAppData in response for {b_title}")
            except Exception as e:
                print(f"  ⚠️ Error extracting {b_title}: {e}")

            await asyncio.sleep(0.8)

        # Save tokens progressively
        with open(TOKENS_FILE, "w", encoding="utf-8") as f:
            json.dump(tokens_data, f, indent=2, ensure_ascii=False)

    except Exception as ex:
        print(f"  ❌ Connection error on {name}: {ex}")
    finally:
        try:
            await cl.disconnect()
        except Exception:
            pass

async def sync_tokens_to_cloudflare(tokens_data):
    print("\n🌐 Synchronizing updated fleet tokens to 5 Cloudflare Worker nodes...")
    import urllib.request
    payload = json.dumps(tokens_data).encode("utf-8")

    for cf_url in CF_WORKERS:
        sync_url = f"{cf_url}/api/miniapp/tokens/sync"
        req = urllib.request.Request(
            sync_url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {CF_SECRET}",
                "User-Agent": "Mozilla/5.0"
            },
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                print(f"  ✅ Synced to {cf_url}: {data.get('message', 'OK')} ({data.get('count', len(tokens_data))} accounts)")
        except Exception as e:
            print(f"  ⚠️ Sync note for {cf_url}: {e}")

async def main():
    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        accounts = json.load(f)

    tokens_data = {}
    if os.path.exists(TOKENS_FILE):
        with open(TOKENS_FILE, "r", encoding="utf-8") as f:
            tokens_data = json.load(f)

    print("=" * 65)
    print("MY AGY AI — BATCH EXTRACTION OF MISSING WEBAPP TOKENS")
    print(f"Accounts: {len(accounts)}")
    print(f"Target Missing Bots: {[b['name'] for b in TARGET_BOTS]}")
    print("=" * 65)

    for idx, acc in enumerate(accounts, 1):
        await process_account(acc, idx, len(accounts), tokens_data)
        await asyncio.sleep(1.2)

    with open(TOKENS_FILE, "w", encoding="utf-8") as f:
        json.dump(tokens_data, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Saved all updated tokens to {TOKENS_FILE}")

    # Cloudflare synchronization
    await sync_tokens_to_cloudflare(tokens_data)

    print("\n" + "=" * 65)
    print("TOKEN AUDIT SUMMARY:")
    all_keys = [b["key"] for b in TARGET_BOTS]
    for uid, t in sorted(tokens_data.items()):
        got = [k for k in all_keys if t.get(k)]
        print(f"• UID {uid} ({t.get('name', 'User')}): {len(got)}/{len(all_keys)} target tokens active")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(main())
