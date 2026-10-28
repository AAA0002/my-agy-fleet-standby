#!/usr/bin/env python3
"""
update_names_with_numbers.py
Adds account numbers to the end of names on Telegram profile, accounts.json,
and across all fleet wallet registries (TON, EVM, TRON, Solana, BTC).
"""

import asyncio
import json
import os
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.account import UpdateProfileRequest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
BASE_DIR = PROJECT_ROOT
ACCOUNTS_FILE = os.path.join(PROJECT_ROOT, "accounts.json")

API_ID = 37321306
API_HASH = "5cd9e5bbfb572a4429a0c54774153b47"

# Map of bought accounts to update on Telegram with index at the end
CHANGED_PROFILES = {
    "+8801943805617": {"first": "Nancy", "last": "Davis 2", "full": "Nancy Davis 2", "index": 2},
    "+8801790208077": {"first": "Kamrul", "last": "Hasan 3", "full": "Kamrul Hasan 3", "index": 3},
    "+14302084365": {"first": "Nathan", "last": "Miller 5", "full": "Nathan Miller 5", "index": 5},
    "+8801867539837": {"first": "Kaitlyn", "last": "Ross 6", "full": "Kaitlyn Ross 6", "index": 6},
    "+8801727651288": {"first": "Naimur", "last": "Rahman 9", "full": "Naimur Rahman 9", "index": 9},
    "+8801729892810": {"first": "Tanvir", "last": "Ahmed 10", "full": "Tanvir Ahmed 10", "index": 10},
    "+918930504750": {"first": "Rohan", "last": "Sharma 14", "full": "Rohan Sharma 14", "index": 14},
    "+8801906045479": {"first": "Tasnim", "last": "Farhana 15", "full": "Tasnim Farhana 15", "index": 15},
    "+8801304151082": {"first": "Rashedul", "last": "Islam 16", "full": "Rashedul Islam 16", "index": 16},
    "+8801879273559": {"first": "Kawsar", "last": "Mahmud 17", "full": "Kawsar Mahmud 17", "index": 17},
    "+8801839716506": {"first": "Mehedi", "last": "Hasan 18", "full": "Mehedi Hasan 18", "index": 18},
}

WALLET_FILES = [
    "fleet_ton_wallets.json",
    "fleet_evm_wallets.json",
    "fleet_tron_wallets.json",
    "fleet_solana_wallets.json",
    "fleet_btc_wallets.json"
]


async def update_tg_profiles():
    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        accounts = json.load(f)

    for acc in accounts:
        phone = acc.get("phone")
        if phone in CHANGED_PROFILES:
            info = CHANGED_PROFILES[phone]
            sess = acc.get("session_string")
            if not sess:
                continue

            cl = TelegramClient(StringSession(sess), API_ID, API_HASH, timeout=8)
            try:
                await cl.connect()
                if await cl.is_user_authorized():
                    await cl(UpdateProfileRequest(first_name=info["first"], last_name=info["last"]))
                    print(f"✅ Telegram profile updated: {phone} ➔ {info['full']}")
                    acc["name"] = info["full"]
            except Exception as e:
                print(f"⚠️ Telegram update failed for {phone}: {e}")
                acc["name"] = info["full"]
            finally:
                try:
                    await cl.disconnect()
                except Exception:
                    pass
            await asyncio.sleep(0.5)

    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(accounts, f, indent=2, ensure_ascii=False)
    print("\n✅ accounts.json updated with numbered names!")
    return accounts


def update_wallet_files(accounts):
    uid_to_name = {str(a.get("user_id")): a.get("name") for a in accounts if a.get("user_id")}
    phone_to_name = {a.get("phone"): a.get("name") for a in accounts if a.get("phone")}

    for fn in WALLET_FILES:
        path = os.path.join(BASE_DIR, fn)
        if not os.path.exists(path):
            continue

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict):
                for uid_key, val in data.items():
                    if uid_key == "_guide":
                        continue
                    if isinstance(val, dict):
                        # Look up by UID or phone
                        new_name = uid_to_name.get(str(uid_key)) or phone_to_name.get(val.get("phone"))
                        if new_name:
                            val["name"] = new_name
                        elif val.get("account_index"):
                            idx = val.get("account_index")
                            for acc in accounts:
                                if acc.get("index") == idx:
                                    val["name"] = acc.get("name")
                                    break
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        uid_val = str(item.get("user_id"))
                        new_name = uid_to_name.get(uid_val) or phone_to_name.get(item.get("phone"))
                        if new_name:
                            item["name"] = new_name

            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅ Wallet file updated: {fn}")
        except Exception as e:
            print(f"❌ Error updating {fn}: {e}")


async def main():
    accounts = await update_tg_profiles()
    update_wallet_files(accounts)
    print("\n🎉 ALL TELEGRAM PROFILES AND WALLET FILES SYNCHRONIZED WITH NUMBERED NAMES!")


if __name__ == "__main__":
    asyncio.run(main())
