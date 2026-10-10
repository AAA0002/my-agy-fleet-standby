#!/usr/bin/env python3
"""
rename_bought_accounts.py
Renames bought accounts to completely natural, human names and usernames
to prevent Telegram automated bans and remove seller artifacts.
Preserves personal accounts: Arif, Abid, and Sanzida Shimu.
"""

import asyncio
import json
import os
import random
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.account import UpdateProfileRequest, UpdateUsernameRequest
from telethon.errors import (
    UsernameOccupiedError,
    UsernameInvalidError,
    UsernamePurchaseAvailableError
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")

API_ID = 37321306
API_HASH = "5cd9e5bbfb572a4429a0c54774153b47"

# Personal accounts to NEVER touch:
# - Arif Hossain (+8801317342850)
# - Arif (+8801575842094)
# - MD. ARIF HOSSAIN (+8801571089931)
# - Abid Hasan (+8801718056423)
# - Abid Hasan (+8801797795624)
# - Abid (+8801838268380)
# - Sanzida Shimu (+8801774578536)
PERSONAL_PHONES = {
    "+8801317342850",
    "+8801575842094",
    "+8801571089931",
    "+8801718056423",
    "+8801797795624",
    "+8801838268380",
    "+8801774578536",
}

# Natural, human profiles for the 11 bought accounts:
TARGET_PROFILES = {
    "+8801943805617": {
        "first": "Nancy",
        "last": "Davis",
        "username_candidates": ["nancydavis_24", "nancydavis_7", "nancyd_24", "nancydavis_88"]
    },
    "+8801790208077": {
        "first": "Kamrul",
        "last": "Hasan",
        "username_candidates": ["kamrul_hasan7", "kamrul_hsn7", "kamrulhasan_88", "kamrul_h24"]
    },
    "+14302084365": {
        "first": "Nathan",
        "last": "Miller",
        "username_candidates": ["nathan_miller7", "nathan_mllr7", "nathanmiller_24", "nathan_m24"]
    },
    "+8801867539837": {
        "first": "Kaitlyn",
        "last": "Ross",
        "username_candidates": ["kaitlyn_ross7", "kaitlyn_ross24", "kaitlynr_88", "kaitlynross_7"]
    },
    "+8801727651288": {
        "first": "Naimur",
        "last": "Rahman",
        "username_candidates": ["naimur_rhmn7", "naimur_rahman7", "naimur_r24", "naimurrahman_88"]
    },
    "+8801729892810": {
        "first": "Tanvir",
        "last": "Ahmed",
        "username_candidates": ["tanvir_ahmed7", "tanvir_ahmd7", "tanvir_a24", "tanvirahmed_88"]
    },
    "+918930504750": {
        "first": "Rohan",
        "last": "Sharma",
        "username_candidates": ["rohan_sharma7", "rohansharma_77", "rohan_sharma24", "rohansharma_88"]
    },
    "+8801906045479": {
        "first": "Tasnim",
        "last": "Farhana",
        "username_candidates": ["tasnim_farhana7", "tasnim_frh7", "tasnim_f24", "tasnimfarhana_88"]
    },
    "+8801304151082": {
        "first": "Rashedul",
        "last": "Islam",
        "username_candidates": ["rashedul_islam7", "rashed_islm7", "rashed_i24", "rashedulislam_88"]
    },
    "+8801879273559": {
        "first": "Kawsar",
        "last": "Mahmud",
        "username_candidates": ["kawsar_mahmud7", "kawsar_mhmd7", "kawsar_m24", "kawsarmahmud_88"]
    },
    "+8801839716506": {
        "first": "Mehedi",
        "last": "Hasan",
        "username_candidates": ["mehedi_hasan7", "mehedi_hsn7", "mehedi_h24", "mehedihasan_88"]
    }
}


async def process_account(acc):
    phone = acc.get("phone")
    if phone in PERSONAL_PHONES:
        print(f"🔒 [SKIPPED] Personal Account preserved: {acc.get('name')} ({phone})")
        return acc

    profile = TARGET_PROFILES.get(phone)
    if not profile:
        print(f"⚠️ [NO_PROFILE] No target profile defined for {phone}")
        return acc

    sess = acc.get("session_string")
    if not sess:
        print(f"❌ [NO_SESSION] No session string for {phone}")
        return acc

    first_name = profile["first"]
    last_name = profile["last"]
    candidates = profile["username_candidates"]

    cl = TelegramClient(StringSession(sess), API_ID, API_HASH, timeout=8)
    try:
        await cl.connect()
        if not await cl.is_user_authorized():
            print(f"❌ [UNAUTHORIZED] {phone} not authorized")
            return acc

        # 1. Update Profile Name
        try:
            up_res = await cl(UpdateProfileRequest(first_name=first_name, last_name=last_name))
            full_name = f"{up_res.first_name} {up_res.last_name or ''}".strip()
            acc["name"] = full_name
            print(f"✅ Name updated for {phone} ➔ {full_name}")
        except Exception as ne:
            print(f"⚠️ Name update error for {phone}: {ne}")

        # 2. Update Username
        new_username = acc.get("username")
        for u in candidates:
            # Add random digit fallback if standard occupied
            for u_attempt in [u, f"{u}{random.randint(10, 99)}"]:
                try:
                    u_res = await cl(UpdateUsernameRequest(username=u_attempt))
                    new_username = u_res.username
                    print(f"  🌟 Username updated for {phone} ➔ @{new_username}")
                    break
                except (UsernameOccupiedError, UsernamePurchaseAvailableError):
                    continue
                except Exception as ue:
                    # Could be flood wait or restriction
                    print(f"  ℹ️ Username @{u_attempt} not applied: {ue}")
                    break
            if new_username and new_username != acc.get("username"):
                break

        if new_username:
            acc["username"] = new_username

    except Exception as e:
        print(f"❌ Error processing {phone}: {e}")
    finally:
        try:
            await cl.disconnect()
        except Exception:
            pass

    return acc


async def main():
    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        accounts = json.load(f)

    updated_accounts = []
    for acc in accounts:
        updated = await process_account(acc)
        updated_accounts.append(updated)
        await asyncio.sleep(1.0)

    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_accounts, f, indent=2, ensure_ascii=False)

    print("\n🎉 All bought accounts successfully renamed and saved to accounts.json!")


if __name__ == "__main__":
    asyncio.run(main())
