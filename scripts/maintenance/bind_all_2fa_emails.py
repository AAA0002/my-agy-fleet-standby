#!/usr/bin/env python3
"""
bind_all_2fa_emails.py
Automated script to bind aaa.support.a+<idx>@gmail.com to 2FA password settings
using IMAP automatic code fetching and fresh SRP password computation.
"""

import sys
import os
import json
import time
import re
import imaplib
import email
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient, functions, types, errors
from telethon.sessions import StringSession
from telethon import password as pwd_mod

load_dotenv()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
BASE_DIR = PROJECT_ROOT
ACCOUNTS_FILE = os.path.join(PROJECT_ROOT, "accounts.json")

API_ID = int(os.getenv("TELEGRAM_API_ID", 37321306))
API_HASH = os.getenv("TELEGRAM_API_HASH", "5cd9e5bbfb572a4429a0c54774153b47")
GMAIL_USER = os.getenv("GMAIL_ADDRESS", "aaa.support.a@gmail.com")
GMAIL_APP_PASS = os.getenv("GMAIL_APP_PASSWORD", "").strip()

PASSWORDS = [p for p in [os.getenv("FLEET_2FA_PASSWORD", ""), os.getenv("FLEET_2FA_FALLBACK", "")] if p]


def fetch_confirm_code(min_email_id: int, max_wait: int = 40):
    start = time.time()
    while time.time() - start < max_wait:
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(GMAIL_USER, GMAIL_APP_PASS)
            mail.select("inbox")
            status, messages = mail.search(None, "ALL")
            if status == "OK" and messages[0]:
                mail_ids = [int(x) for x in messages[0].split()]
                new_ids = [x for x in mail_ids if x > min_email_id]
                for mid in reversed(new_ids):
                    status, data = mail.fetch(str(mid), "(RFC822)")
                    if status != "OK":
                        continue
                    msg = email.message_from_bytes(data[0][1])
                    subject = str(msg.get("Subject", ""))
                    if "telegram" in str(msg.get("From", "")).lower() or "telegram" in subject.lower():
                        match = re.search(r"\b(\d{6})\b", subject)
                        if match:
                            mail.logout()
                            return match.group(1)
            mail.logout()
        except Exception as e:
            print(f"  [IMAP Poll Warning]: {e}")
        time.sleep(3)
    return None


async def get_fresh_input_password(cl):
    pwd = await cl(functions.account.GetPasswordRequest())
    for p in PASSWORDS:
        try:
            input_pwd = pwd_mod.compute_check(pwd, p)
            return input_pwd, p
        except Exception:
            pass
    return None, None


async def bind_email_for_account(acc: dict):
    idx = acc.get("index")
    phone = acc.get("phone")
    name = acc.get("name")
    sess = acc.get("session_string")
    target_email = f"aaa.support.a+{idx}@gmail.com"

    print(f"\n🚀 Processing Account #{idx}: {name} ({phone}) -> {target_email}")

    # Baseline IMAP email ID
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_APP_PASS)
        mail.select("inbox")
        status, messages = mail.search(None, "ALL")
        latest_id = int(messages[0].split()[-1]) if messages[0] else 0
        mail.logout()
    except Exception as e:
        print(f"❌ IMAP connection error: {e}")
        return False

    cl = TelegramClient(StringSession(sess), API_ID, API_HASH, timeout=15)
    await cl.connect()

    try:
        input_pwd, used_p = await get_fresh_input_password(cl)
        if not input_pwd:
            print(f"❌ Could not compute SRP password for #{idx}")
            return False

        print(f"  📨 Sending UpdatePasswordSettingsRequest for {target_email}...")
        try:
            await cl(functions.account.UpdatePasswordSettingsRequest(
                password=input_pwd,
                new_settings=types.account.PasswordInputSettings(email=target_email)
            ))
            print(f"  ✅ Email updated directly without challenge!")
            return True
        except errors.EmailUnconfirmedError as e:
            print(f"  📩 Challenge sent! Waiting for 6-digit code in Gmail (baseline ID: {latest_id})...")
            code = fetch_confirm_code(latest_id)
            if not code:
                print(f"  ❌ Timed out waiting for code in Gmail.")
                return False

            print(f"  🔑 Intercepted code: {code}")
            print(f"  🔐 Confirming with ConfirmPasswordEmailRequest...")
            res = await cl(functions.account.ConfirmPasswordEmailRequest(code=code))
            print(f"  🎉 Confirmation result: {res}")

            # Verify with fresh SRP
            v_pwd, _ = await get_fresh_input_password(cl)
            new_settings = await cl(functions.account.GetPasswordSettingsRequest(password=v_pwd))
            print(f"  ✅ Confirmed Email is now: {new_settings.email}")
            return True

    except Exception as e:
        print(f"  ❌ Error on #{idx}: {type(e).__name__} ({e})")
        return False
    finally:
        await cl.disconnect()


async def main():
    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        accounts = json.load(f)

    target_indices = [5, 6, 9, 10]
    target_accs = [a for a in accounts if a.get("index") in target_indices]

    for a in target_accs:
        await bind_email_for_account(a)
        await asyncio.sleep(4)

    print("\n🏁 Done processing targets!")


if __name__ == "__main__":
    asyncio.run(main())
