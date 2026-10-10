#!/usr/bin/env python3
"""
auto_bind_login_emails.py
Fully automated Telegram Login Email binding via MTProto + IMAP listener.
Uses Google App Password to automatically fetch verification codes.
"""

import sys
import os
import json
import time
import re
import imaplib
import email
from email.header import decode_header
import asyncio
from telethon import TelegramClient, functions, types, errors
from telethon.sessions import StringSession

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")

API_ID = int(os.getenv("TELEGRAM_API_ID", 37321306))
API_HASH = os.getenv("TELEGRAM_API_HASH", "5cd9e5bbfb572a4429a0c54774153b47")

GMAIL_USER = os.getenv("GMAIL_ADDRESS", "aaa.support.a@gmail.com")
GMAIL_APP_PASS = os.getenv("GMAIL_APP_PASSWORD", "").strip()
if not GMAIL_APP_PASS:
    raise ValueError("GMAIL_APP_PASSWORD environment variable is missing in .env")


def get_latest_email_id(mail):
    status, messages = mail.search(None, "ALL")
    if status != "OK" or not messages[0]:
        return 0
    mail_ids = messages[0].split()
    return int(mail_ids[-1]) if mail_ids else 0


def fetch_verification_code(min_email_id: int, max_wait: int = 35):
    """Polls Gmail inbox via IMAP for a Telegram verification code arriving after min_email_id."""
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(GMAIL_USER, GMAIL_APP_PASS)
            mail.select("inbox")
            status, messages = mail.search(None, "ALL")
            if status == "OK" and messages[0]:
                mail_ids = [int(x) for x in messages[0].split()]
                # Check IDs greater than min_email_id
                new_ids = [x for x in mail_ids if x > min_email_id]
                for mid in reversed(new_ids):
                    status, data = mail.fetch(str(mid), "(RFC822)")
                    if status != "OK":
                        continue
                    msg = email.message_from_bytes(data[0][1])
                    subject = str(msg.get("Subject", ""))
                    from_ = str(msg.get("From", ""))

                    if "telegram" in from_.lower() or "telegram" in subject.lower():
                        # Extract 6-digit code
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                ctype = part.get_content_type()
                                cdispo = str(part.get("Content-Disposition"))
                                if ctype == "text/plain" and "attachment" not in cdispo:
                                    body = part.get_payload(decode=True).decode(errors="ignore")
                                    break
                        else:
                            body = msg.get_payload(decode=True).decode(errors="ignore")

                        match = re.search(r"\b(\d{6})\b", subject) or re.search(r"code is:\s*(\d{6})", body, re.IGNORECASE) or re.search(r"\b(\d{6})\b", body)
                        if match:
                            mail.logout()
                            return match.group(1)

            mail.logout()
        except Exception as e:
            print(f"  [IMAP Warning]: {e}")
        time.sleep(3)

    return None


async def bind_single_account(account: dict):
    phone = account.get("phone")
    name = account.get("name")
    idx = account.get("index")
    sess = account.get("session_string")

    if not sess:
        print(f"❌ Account #{idx} ({phone}) has no session.")
        return False

    target_email = f"aaa.support.a+{idx}@gmail.com"
    print(f"\n🚀 Processing Account #{idx}: {name} ({phone}) -> {target_email}")

    # Check baseline IMAP
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_APP_PASS)
        mail.select("inbox")
        latest_id = get_latest_email_id(mail)
        mail.logout()
    except Exception as e:
        print(f"❌ IMAP connection error: {e}")
        return False

    cl = TelegramClient(StringSession(sess), API_ID, API_HASH, timeout=15)
    await cl.connect()

    try:
        if not await cl.is_user_authorized():
            print(f"❌ Account #{idx} ({phone}) is not authorized.")
            return False

        # Send Verify Email Code
        print(f"  📨 Sending SendVerifyEmailCodeRequest to {target_email}...")
        res = await cl(functions.account.SendVerifyEmailCodeRequest(
            purpose=types.EmailVerifyPurposeLoginChange(),
            email=target_email
        ))
        print(f"  ✅ Code sent! Pattern: {getattr(res, 'email_pattern', target_email)}, length: {getattr(res, 'length', 6)}")

        # Poll IMAP for code
        print(f"  ⏳ Waiting for Telegram email in Gmail...")
        code = fetch_verification_code(min_email_id=latest_id, max_wait=40)
        if not code:
            print(f"  ❌ Timed out waiting for code from Gmail.")
            return False

        print(f"  🔑 Received code from Gmail: {code}")

        # Verify Code
        print(f"  🔐 Submitting VerifyEmailRequest...")
        v_res = await cl(functions.account.VerifyEmailRequest(
            purpose=types.EmailVerifyPurposeLoginChange(),
            verification=types.EmailVerificationCode(code=code)
        ))
        print(f"  🎉 SUCCESS! Verified result: {type(v_res).__name__}")

        # Update accounts.json
        account["login_email"] = target_email
        account["login_email_verified"] = True

        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            all_accounts = json.load(f)

        for a in all_accounts:
            if a.get("phone") == phone:
                a["login_email"] = target_email
                a["login_email_verified"] = True
                break

        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
            json.dump(all_accounts, f, indent=2, ensure_ascii=False)

        return True

    except errors.FloodWaitError as e:
        print(f"  ⚠️ FloodWait: Need to wait {e.seconds} seconds.")
        return False
    except Exception as e:
        print(f"  ❌ Error binding #{idx}: {type(e).__name__} ({e})")
        return False
    finally:
        await cl.disconnect()


async def run_for_accounts(indices: list):
    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        accounts = json.load(f)

    target_accs = [a for a in accounts if a.get("index") in indices]
    print(f"Targeting {len(target_accs)} accounts: {[a.get('name') for a in target_accs]}")

    success_count = 0
    for acc in target_accs:
        ok = await bind_single_account(acc)
        if ok:
            success_count += 1
        await asyncio.sleep(4)

    print(f"\n==========================================")
    print(f"✅ Successfully bound and verified {success_count}/{len(target_accs)} accounts!")
    print(f"==========================================")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python auto_bind_login_emails.py <index1> <index2> ... OR all_purchased")
        sys.exit(1)

    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        accounts = json.load(f)

    purchased_indices = [2, 5, 6, 9, 10, 14, 15, 16, 17, 18]

    if sys.argv[1].lower() == "all_purchased":
        # Filter those that aren't verified yet
        pending = [a.get("index") for a in accounts if a.get("index") in purchased_indices and not a.get("login_email_verified")]
        asyncio.run(run_for_accounts(pending))
    else:
        req_indices = [int(x) for x in sys.argv[1:]]
        asyncio.run(run_for_accounts(req_indices))
