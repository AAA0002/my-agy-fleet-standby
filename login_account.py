#!/usr/bin/env python3
"""
Interactive Telegram Account Login & Session Generator
Allows adding multiple Telegram accounts to the 24/7 cloud worker.
"""

import os
import sys
import json
import asyncio
from datetime import datetime, timezone
import random
import string
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    PhoneNumberInvalidError
)
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.contacts import UnblockRequest
from dotenv import load_dotenv
from phone_detector import detect_and_normalize_phone


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")
load_dotenv(os.path.join(BASE_DIR, ".env"))

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")

BNB_BOT = "CryptoProUpRobot"
ATF_BOT = "AAAPREMIUMAPPSbot"
BNB_REFERRAL_CODE = "Bot46893407"
ATF_REFERRAL_CODE = "ref_6727787768"
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS", "0xfda4182001672b9f0f09e2118242e543e35ed5ce")


if not API_ID or not API_HASH:
    print("❌ Error: TELEGRAM_API_ID and TELEGRAM_API_HASH not found in .env")
    sys.exit(1)

try:
    API_ID = int(API_ID)
except ValueError:
    print("❌ Error: TELEGRAM_API_ID must be an integer")
    sys.exit(1)


def generate_random_email():
    chars = string.ascii_lowercase + string.digits
    rand_name = "".join(random.choice(chars) for _ in range(9))
    domain = random.choice(["gmail.com", "yahoo.com", "outlook.com", "proton.me", "icloud.com"])
    return f"arif.{rand_name}@{domain}"


MANDATORY_BNB_CHANNELS = [
    "Rewards_Lab",
    "TensorCoinNews",
    "AirdropFindTeam",
    "EarnCraftNews"
]


async def bind_referrals(client, me, acc_entry):
    if me.id == 6727787768 or acc_entry.get("is_referral_host"):
        print("ℹ️ Primary referral host account. Skipping self-referral.")
        acc_entry["is_referral_host"] = True
        acc_entry["bnb_referral_bound"] = True
        acc_entry["atf_referral_bound"] = True
        return

    print(f"\n🔗 Automatically binding account to referral links...")

    # 1. BNB Galaxy (@CryptoProUpRobot)
    print(f"  • Connecting to @{BNB_BOT} with referral: {BNB_REFERRAL_CODE}...")
    try:
        try:
            await client(UnblockRequest(id=BNB_BOT))
        except Exception:
            pass
        await client.send_message(BNB_BOT, f"/start {BNB_REFERRAL_CODE}")
        await asyncio.sleep(2.5)

        # Step 1: Join mandatory channels
        for ch in MANDATORY_BNB_CHANNELS:
            try:
                print(f"    - Joining mandatory channel: @{ch}...")
                await client(JoinChannelRequest(ch))
                await asyncio.sleep(1.5)
            except Exception as ce:
                pass

        # Step 2: Click [Continue]
        msgs = await client.get_messages(BNB_BOT, limit=3)
        for m in msgs:
            if m.buttons:
                for row in m.buttons:
                    for btn in row:
                        if "continue" in (btn.text or "").lower():
                            print(f"    - Clicking onboarding button: '{btn.text}'")
                            try:
                                await btn.click()
                                await asyncio.sleep(2.5)
                                break
                            except Exception:
                                pass

        # Step 3: Click [Submit Details]
        msgs = await client.get_messages(BNB_BOT, limit=3)
        for m in msgs:
            if m.buttons:
                for row in m.buttons:
                    for btn in row:
                        if "submit details" in (btn.text or "").lower() or "details" in (btn.text or "").lower():
                            print(f"    - Clicking onboarding button: '{btn.text}'")
                            try:
                                await btn.click()
                                await asyncio.sleep(2.5)
                                break
                            except Exception:
                                pass

        # Step 4: Submit email if requested
        msgs = await client.get_messages(BNB_BOT, limit=3)
        for m in msgs:
            if "email id" in (m.raw_text or "").lower():
                em = generate_random_email()
                print(f"    - Submitting onboarding email: {em}")
                await client.send_message(BNB_BOT, em)
                await asyncio.sleep(2.5)
                break

        # Step 5: Submit BEP-20 wallet if requested
        msgs = await client.get_messages(BNB_BOT, limit=3)
        for m in msgs:
            if "wallet address" in (m.raw_text or "").lower():
                print(f"    - Submitting BEP-20 wallet: {WALLET_ADDRESS}")
                await client.send_message(BNB_BOT, WALLET_ADDRESS)
                await asyncio.sleep(2.5)
                break

        acc_entry["bnb_referral_bound"] = True
        print(f"  ✅ Successfully bound to BNB Galaxy referral ({BNB_REFERRAL_CODE})!")
    except Exception as e:
        print(f"  ❌ Warning binding BNB Galaxy referral: {e}")


    # 2. AAA ATF Miner (@AAAPREMIUMAPPSbot)
    print(f"  • Connecting to @{ATF_BOT} with referral: {ATF_REFERRAL_CODE}...")
    try:
        try:
            await client(UnblockRequest(id=ATF_BOT))
        except Exception:
            pass
        await client.send_message(ATF_BOT, f"/start {ATF_REFERRAL_CODE}")
        await asyncio.sleep(2.0)
        acc_entry["atf_referral_bound"] = True
        print(f"  ✅ Successfully bound to ATF Miner referral ({ATF_REFERRAL_CODE})!")
    except Exception as e:
        print(f"  ❌ Warning binding ATF Miner referral: {e}")



def load_accounts():
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_accounts(accounts):
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(accounts, f, indent=2, ensure_ascii=False)


async def interactive_login():
    print("\n" + "=" * 55)
    print("  📱 TELEGRAM MULTI-ACCOUNT LOGIN & MTPROTO SESSION")
    print("=" * 55)
    
    existing = load_accounts()
    print(f"Current connected accounts: {len(existing)}")
    for idx, acc in enumerate(existing, 1):
        print(f"  {idx}. {acc.get('name')} (@{acc.get('username')}) [ID: {acc.get('user_id')}] - Phone: {acc.get('phone')}")
    print("=" * 55 + "\n")

    phone_input = input("Enter phone number (e.g. 019XXXXXXXX, +880..., +1...): ").strip()
    if not phone_input:
        print("❌ Phone number cannot be empty.")
        return

    phone, country_label = detect_and_normalize_phone(phone_input)
    print(f"📡 Detected Region: {country_label}")
    print(f"📱 Normalized Phone: {phone}")

    # Check if already added
    for acc in existing:
        if acc.get("phone") == phone:
            print(f"⚠️ Account with phone {phone} is already in accounts.json!")
            choice = input("Do you want to re-login and overwrite it? (y/n): ").strip().lower()
            if choice != "y":
                return

    client = TelegramClient(StringSession(), API_ID, API_HASH)
    await client.connect()

    print(f"\n📡 Requesting login verification code for {phone} ({country_label})...")
    try:
        sent_code = await client.send_code_request(phone)
        phone_code_hash = sent_code.phone_code_hash
        print(f"✅ Code sent via Telegram to your phone/app!")
    except PhoneNumberInvalidError:
        print("❌ Error: The phone number is invalid. Include the country code (+...).")
        await client.disconnect()
        return
    except Exception as e:
        print(f"❌ Error requesting code: {e}")
        await client.disconnect()
        return

    code = input("\nEnter the 5-digit verification code you received: ").strip()
    # Remove any dashes or spaces
    code = code.replace("-", "").replace(" ", "")

    try:
        await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
    except SessionPasswordNeededError:
        print("\n🔒 Two-Factor Authentication (2FA) is enabled on this account.")
        pwd = input("Enter your 2FA Cloud Password: ").strip()
        try:
            await client.sign_in(password=pwd)
        except Exception as e:
            print(f"❌ 2FA Authentication failed: {e}")
            await client.disconnect()
            return
    except PhoneCodeInvalidError:
        print("❌ Error: The verification code entered is invalid.")
        await client.disconnect()
        return
    except PhoneCodeExpiredError:
        print("❌ Error: The verification code has expired. Please try again.")
        await client.disconnect()
        return
    except Exception as e:
        print(f"❌ Login failed: {e}")
        await client.disconnect()
        return

    me = await client.get_me()
    name = f"{me.first_name or ''} {me.last_name or ''}".strip() or "User"
    username = me.username or "None"
    session_str = client.session.save()

    print("\n" + "=" * 55)
    print(" 🎉 LOGIN SUCCESSFUL!")
    print(f" Name:     {name}")
    print(f" Username: @{username}")
    print(f" User ID:  {me.id}")
    print("=" * 55)

    acc_entry = {
        "name": name,
        "username": username,
        "user_id": me.id,
        "phone": phone,
        "session_string": session_str,
        "added_at": datetime.now(timezone.utc).isoformat(),
        "status": "active"
    }

    proxy_val = input("\nEnter SOCKS5/HTTP proxy for this account (or press Enter for Cloud Direct): ").strip()
    if proxy_val:
        acc_entry["proxy"] = proxy_val
        print(f"🛡️ Configured ad proxy: {proxy_val}")
    else:
        acc_entry["proxy"] = None
        print("🌍 Using built-in Cloud Direct.")

    # Automatically bind referrals to primary user's links
    await bind_referrals(client, me, acc_entry)


    # Save to accounts.json
    accounts = load_accounts()
    # Update existing or add new
    updated = False
    for acc in accounts:
        if acc.get("phone") == phone or acc.get("user_id") == me.id:
            acc.update(acc_entry)
            acc["updated_at"] = datetime.now(timezone.utc).isoformat()
            updated = True
            break

    if not updated:
        accounts.append(acc_entry)

    save_accounts(accounts)
    print(f"\n✅ Account successfully saved to {ACCOUNTS_FILE}!")
    print(f"Total active accounts: {len(accounts)}")
    print("The 24/7 background worker will now automatically farm for this account.")
    print("=" * 55 + "\n")

    await client.disconnect()



if __name__ == "__main__":
    asyncio.run(interactive_login())
