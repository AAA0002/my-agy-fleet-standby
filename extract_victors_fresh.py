#!/usr/bin/env python3
"""
extract_victors_fresh.py
Extracts 0-second fresh victors_init_data across all 18 Telethon fleet accounts.
Ensures:
  1. Master Account (6727787768) does NOT bind to itself (start_param=None).
  2. All 17 Worker sub-accounts send /start ref_A20AA96F18 and request WebApp with start_param="ref_A20AA96F18".
  3. Writes updated initData to fleet_miniapp_tokens.json.
  4. Syncs updated initData to Upstash Redis (fleet:tokens:{uid} and miniapp_tokens).
"""

import os
import sys
import json
import time
import asyncio
import urllib.parse
import urllib.request
from telethon import TelegramClient, functions
from telethon.sessions import StringSession
from telethon.tl.types import InputBotAppShortName

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")
FLEET_TOKENS_FILE = os.path.join(BASE_DIR, "fleet_miniapp_tokens.json")

API_ID = int(os.getenv("TELEGRAM_API_ID", "24726207"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "5cd9e5bbfb572a4429a0c54774153b47")
PRIMARY_ID = "6727787768"
VICTORS_REF = "ref_A20AA96F18"

UPSTASH_URL = os.getenv("UPSTASH_URL") or "https://pleasant-locust-220893.upstash.io"
UPSTASH_TOKEN = os.getenv("UPSTASH_TOKEN") or ""

if not UPSTASH_TOKEN:
    env_file = os.path.join(BASE_DIR, ".env")
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                if "UPSTASH_TOKEN" in line or "UPSTASH_REDIS_REST_TOKEN" in line:
                    UPSTASH_TOKEN = line.split("=", 1)[1].strip("\" '\n")
                if "UPSTASH_URL" in line or "UPSTASH_REDIS_REST_URL" in line:
                    UPSTASH_URL = line.split("=", 1)[1].strip("\" '\n")


def extract_web_app_data(url: str) -> str:
    """Extracts tgWebAppData from URL fragment or query parameters."""
    if not url:
        return ""
    try:
        parsed = urllib.parse.urlparse(url)
        fragment_data = urllib.parse.parse_qs(parsed.fragment)
        if "tgWebAppData" in fragment_data:
            return fragment_data["tgWebAppData"][0]
        query_data = urllib.parse.parse_qs(parsed.query)
        if "tgWebAppData" in query_data:
            return query_data["tgWebAppData"][0]
    except Exception:
        pass
    return ""


async def process_account(acc: dict, index: int, total: int) -> tuple:
    uid = str(acc.get("user_id"))
    name = acc.get("name") or f"Account #{index}"
    sess_str = acc.get("session_string")
    if not sess_str:
        return uid, name, None, "No session string"

    is_master = (uid == PRIMARY_ID)
    start_param = None if is_master else VICTORS_REF

    client = TelegramClient(StringSession(sess_str), API_ID, API_HASH)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            return uid, name, None, "Unauthorized session"

        # 1. Resolve @VictorsCompanybot
        bot_vic = await client.get_entity("VictorsCompanybot")
        bot_vic_in = await client.get_input_entity(bot_vic)

        # 2. For sub-accounts, ensure /start ref_A20AA96F18 was sent to establish chat referral binding
        if not is_master:
            try:
                await client.send_message(bot_vic_in, f"/start {VICTORS_REF}")
            except Exception:
                pass

        # 3. Request WebApp URL
        res_vic = await client(functions.messages.RequestAppWebViewRequest(
            peer=bot_vic_in,
            app=InputBotAppShortName(bot_id=bot_vic_in, short_name="app"),
            platform="android",
            start_param=start_param
        ))

        vic_init = extract_web_app_data(res_vic.url)
        if not vic_init:
            return uid, name, None, "Failed to extract tgWebAppData from URL"

        return uid, name, vic_init, "OK"
    except Exception as e:
        return uid, name, None, str(e)
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


async def main():
    print("🚀 Starting 18-Account Victor's Company Token Refresh...")
    if not os.path.exists(ACCOUNTS_FILE):
        print(f"❌ {ACCOUNTS_FILE} not found!")
        return

    with open(ACCOUNTS_FILE, "r") as f:
        accounts = json.load(f)

    # Load existing local tokens
    tokens_master = {}
    if os.path.exists(FLEET_TOKENS_FILE):
        try:
            with open(FLEET_TOKENS_FILE, "r") as f:
                tokens_master = json.load(f)
        except Exception:
            tokens_master = {}

    # Load existing miniapp_tokens from Upstash Redis
    upstash_miniapp = {}
    if UPSTASH_TOKEN:
        try:
            req = urllib.request.Request(
                f"{UPSTASH_URL}/get/miniapp_tokens",
                headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                res = json.loads(resp.read().decode()).get("result")
                if res:
                    upstash_miniapp = json.loads(res) if isinstance(res, str) else res
        except Exception as e:
            print(f"⚠️ Note fetching miniapp_tokens from Upstash: {e}")

    # Process in batches of 4 to be respectful of Telegram limits
    batch_size = 4
    success_count = 0
    results = {}

    for i in range(0, len(accounts), batch_size):
        batch = accounts[i:i+batch_size]
        tasks = [
            process_account(acc, idx + 1, len(accounts))
            for idx, acc in enumerate(batch, start=i)
        ]
        batch_res = await asyncio.gather(*tasks)
        for uid, name, vic_init, status in batch_res:
            if vic_init:
                success_count += 1
                results[uid] = vic_init
                print(f"  ✅ [{len(results)}/{len(accounts)}] UID {uid} ({name}): Fresh token extracted! (status: {status})")

                # Update local master
                if uid not in tokens_master:
                    tokens_master[uid] = {"account_id": uid, "name": name}
                tokens_master[uid]["victors_init_data"] = vic_init
                tokens_master[uid]["synced_at"] = time.time()

                # Update Upstash miniapp dictionary
                if uid not in upstash_miniapp:
                    upstash_miniapp[uid] = {"account_id": uid, "name": name}
                upstash_miniapp[uid]["victors_init_data"] = vic_init
                upstash_miniapp[uid]["synced_at"] = time.time()

                # Sync single fleet:tokens:{uid} in Upstash
                if UPSTASH_TOKEN:
                    try:
                        # Fetch existing fleet:tokens:{uid}
                        req_get = urllib.request.Request(
                            f"{UPSTASH_URL}/get/fleet:tokens:{uid}",
                            headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}
                        )
                        tok_dict = {}
                        with urllib.request.urlopen(req_get, timeout=5) as resp:
                            res_raw = json.loads(resp.read().decode()).get("result")
                            if res_raw:
                                tok_dict = json.loads(res_raw) if isinstance(res_raw, str) else res_raw
                        tok_dict["victors_init_data"] = vic_init
                        tok_dict["synced_at"] = time.time()

                        req_set = urllib.request.Request(
                            f"{UPSTASH_URL}/set/fleet:tokens:{uid}",
                            data=json.dumps(tok_dict).encode("utf-8"),
                            headers={"Authorization": f"Bearer {UPSTASH_TOKEN}", "Content-Type": "application/json"},
                            method="POST"
                        )
                        urllib.request.urlopen(req_set, timeout=5)
                    except Exception as ue:
                        print(f"    ⚠️ Upstash sync note for UID {uid}: {ue}")
            else:
                print(f"  ❌ UID {uid} ({name}): Failed -> {status}")
        await asyncio.sleep(0.5)

    # Save local fleet_miniapp_tokens.json
    with open(FLEET_TOKENS_FILE, "w", encoding="utf-8") as f:
        json.dump(tokens_master, f, indent=2)
    print(f"💾 Saved {len(tokens_master)} accounts to {FLEET_TOKENS_FILE}")

    # Save master miniapp_tokens to Upstash Redis
    if UPSTASH_TOKEN and upstash_miniapp:
        try:
            req_all = urllib.request.Request(
                f"{UPSTASH_URL}/set/miniapp_tokens",
                data=json.dumps(upstash_miniapp).encode("utf-8"),
                headers={"Authorization": f"Bearer {UPSTASH_TOKEN}", "Content-Type": "application/json"},
                method="POST"
            )
            urllib.request.urlopen(req_all, timeout=10)
            print("💾 Synced master miniapp_tokens to Upstash Redis!")
        except Exception as e:
            print(f"⚠️ Error saving miniapp_tokens to Upstash: {e}")

    print(f"\n🎉 Token Refresh Completed: {success_count}/{len(accounts)} accounts successfully refreshed!")


if __name__ == "__main__":
    asyncio.run(main())
