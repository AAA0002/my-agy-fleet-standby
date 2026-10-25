#!/usr/bin/env python3
"""
clean_all_accounts_channels.py
Leaves and removes all unwanted third-party promotional channels from all 13 fleet accounts.
Preserves:
- @myagyai (Disaster Recovery Vault)
- All official fleet channels (AAA*)
- Verified official farming bot channels (MRG, ATF, Victor's Company, VyroDrop)
- All personal chats, groups, and contacts
"""

import os
import json
import time
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.channels import LeaveChannelRequest
from telethon.tl.types import Channel

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")

API_ID = int(os.getenv("TELEGRAM_API_ID", "23788736"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "8098c495e2820d82935041ff91176b65")

# Channels explicitly requested to be removed
EXPLICIT_UNWANTED_USERNAMES = {
    "tech_tuber_rana",
    "earningllnews",
    "cryptoabir016",
    "banglacryptoearning",
    "shtech2",
    "abrauftips",
    "milonofficialearn",
    "vipkopchanel",
    "komdamtopup",
    "nigga1z",
    "jihad_creation",
    "extremeprimex",
    "zyntrixmining",
    "revolvedao",
    "airdropbulider",
    "rewards_lab",
    "earncraftnews",
    "airdropfindteam",
    "mininggram_channel",
    "ominiai",
    "ominiaipayout",
    # Discontinued & scam channels purged per user directive
    "stoneswithestand",
    "ailabrobotnews",
    "ultrawalletofficial",
    "ultrawallet",
    "finvoraweb3",
    "trxpowerminingofficial",
    "trx_world_work",
    "trxpowermining",
    "art_airdrop",
    "artairdrop",
    "tensorcoinnews",
    "tontraderai_official",
    "tontraderai_group",
    "tontraderai_reviews",
    "tacairdrop",
    "tacairdrop_official",
    "tac_airdrop",
    "tacairdropen",
    "novum_en",
    "apexminer_official",
    "apexminergroup",
    "usdtquad_channel",
    "usdtquad",
}

# Whitelist: Channels that must NEVER be left under any circumstance
PROTECTED_USERNAMES = {
    "myagyai",
    "mrgminer",
    "mrgfun",
    "VictorsCompany",
    "vyrodrop",
}

PROTECTED_CHANNEL_IDS = {
    -1004453515167, # @myagyai
    -1004402765950, # Agy payment verification message
}

def is_protected(channel_name: str, username: str, channel_id: int) -> bool:
    if channel_id in PROTECTED_CHANNEL_IDS:
        return True
    uname_lower = (username or "").lower()
    if uname_lower in PROTECTED_USERNAMES:
        return True
    if uname_lower.startswith("aaa"):
        return True
    name_lower = (channel_name or "").lower()
    if "aaa" in name_lower or "my agy ai" in name_lower or "backup" in name_lower:
        return True
    return False

async def clean_account(acc_index: int, acc: dict, total_count: int = 18):
    name = acc.get("name", f"Account #{acc_index+1}")
    uid = str(acc.get("user_id"))
    if acc.get("dead_bots_purged_v2"):
        print(f"[{acc_index+1}/{total_count}] Skipping {name} (Already purged dead bots & channels v2)")
        return 0

    sess_str = acc.get("session_string") or acc.get("session")
    if not sess_str:
        print(f"[{acc_index+1}/{total_count}] Skipping {name} (No session string)")
        return 0

    print(f"\n=======================================================")
    print(f"[{acc_index+1}/{total_count}] Cleaning channels for: {name} (UID: {uid})")
    print(f"=======================================================")

    client = TelegramClient(StringSession(sess_str), API_ID, API_HASH)
    left_count = 0
    try:
        await client.connect()
        if not await client.is_user_authorized():
            print(f"  ❌ Unauthorized session for {name}")
            return 0

        dialogs = await client.get_dialogs()
        for d in dialogs:
            if not d.is_channel:
                continue

            ch_entity = d.entity
            ch_name = d.name or "Untitled Channel"
            ch_uname = getattr(ch_entity, "username", None) or ""
            ch_uname_lower = ch_uname.lower()
            ch_id = d.id

            # Skip protected channels
            if is_protected(ch_name, ch_uname, ch_id):
                continue

            should_leave = False

            # On Account 1 (Admin Arif Hossain), strictly only leave explicitly unwanted promotional channels
            if acc_index == 0:
                if ch_uname_lower in EXPLICIT_UNWANTED_USERNAMES:
                    should_leave = True
            else:
                # On worker accounts 2 to 13, leave all promotional/sponsored channels
                if ch_uname_lower in EXPLICIT_UNWANTED_USERNAMES:
                    should_leave = True
                elif not ch_uname_lower.startswith("aaa") and ch_uname_lower not in PROTECTED_USERNAMES:
                    # Check if it's an unwanted promotional/ad channel from tasks
                    if any(w in ch_name.lower() for w in ["earn", "crypto", "airdrop", "payout", "topup", "tech", "miner", "mining", "creation", "prime", "news", "tips", "kop", "gang", "vip"]):
                        should_leave = True

            if should_leave:
                try:
                    await client(LeaveChannelRequest(ch_entity))
                except Exception:
                    pass
                try:
                    await client.delete_dialog(ch_entity)
                    print(f"  🗑️ Left & removed: {ch_name} (@{ch_uname})")
                    left_count += 1
                except Exception as de:
                    print(f"  ⚠️ Note on {ch_name} (@{ch_uname}): {de}")
                await asyncio.sleep(0.5)

    except Exception as e:
        print(f"  ❌ Error processing {name}: {e}")
    finally:
        await client.disconnect()

    print(f"  ✅ Finished {name}: {left_count} unwanted channels removed.")
    return left_count

async def main():
    if not os.path.exists(ACCOUNTS_FILE):
        print("accounts.json not found!")
        return

    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        accounts = json.load(f)

    total_left = 0
    total_accs = len(accounts)
    for idx, acc in enumerate(accounts):
        left = await clean_account(idx, acc, total_count=total_accs)
        total_left += left
        await asyncio.sleep(2.0)

    print("\n" + "=" * 60)
    print(f"🎉 CLEANUP COMPLETE: Successfully removed {total_left} unwanted channels across all accounts!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
