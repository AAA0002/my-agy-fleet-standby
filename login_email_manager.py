#!/usr/bin/env python3
"""
login_email_manager.py
Binds and verifies Telegram Login Email (Email for Login Codes)
across fleet accounts via MTProto SendVerifyEmailCodeRequest & VerifyEmailRequest.
"""

import sys
import os
import json
import asyncio
from telethon import TelegramClient, functions, types, errors
from telethon.sessions import StringSession

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")
STATE_FILE = os.path.join(BASE_DIR, "temp_login_email_state.json")

API_ID = 37321306
API_HASH = "5cd9e5bbfb572a4429a0c54774153b47"


def get_account_session(phone: str):
    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        accounts = json.load(f)
    for a in accounts:
        if a.get("phone") == phone:
            return a.get("session_string"), a.get("name"), a.get("index")
    return None, None, None


async def send_code(phone: str, email: str):
    sess, name, idx = get_account_session(phone)
    if not sess:
        print(f"ERROR:Account {phone} not found")
        return

    cl = TelegramClient(StringSession(sess), API_ID, API_HASH, timeout=10)
    await cl.connect()

    try:
        if not await cl.is_user_authorized():
            print("ERROR:Account not authorized")
            return

        res = await cl(functions.account.SendVerifyEmailCodeRequest(
            purpose=types.EmailVerifyPurposeLoginChange(),
            email=email
        ))

        state = {
            "phone": phone,
            "name": name,
            "session_string": sess,
            "email": email,
            "length": getattr(res, "length", 6),
            "email_pattern": getattr(res, "email_pattern", email)
        }
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)

        print(f"SUCCESS_SENT:{phone}:{name}:{email}:{state['length']}")
    except Exception as e:
        print(f"ERROR_SEND:{type(e).__name__}:{e}")
    finally:
        await cl.disconnect()


async def verify_code(code: str):
    code = code.strip()
    if not os.path.exists(STATE_FILE):
        print("ERROR:No pending email verification state.")
        return

    with open(STATE_FILE, "r") as f:
        state = json.load(f)

    sess = state["session_string"]
    phone = state["phone"]
    name = state["name"]
    email = state["email"]

    cl = TelegramClient(StringSession(sess), API_ID, API_HASH, timeout=10)
    await cl.connect()

    try:
        res = await cl(functions.account.VerifyEmailRequest(
            purpose=types.EmailVerifyPurposeLoginChange(),
            verification=types.EmailVerificationCode(code=code)
        ))

        # Update accounts.json with the bound login email
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            accounts = json.load(f)

        for a in accounts:
            if a.get("phone") == phone:
                a["login_email"] = email
                a["login_email_verified"] = True
                break

        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
            json.dump(accounts, f, indent=2, ensure_ascii=False)

        print(f"SUCCESS_VERIFIED:{phone}:{name}:{email}")
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)

    except Exception as e:
        print(f"ERROR_VERIFY:{type(e).__name__}:{e}")
    finally:
        await cl.disconnect()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python login_email_manager.py send <phone> <email> OR python login_email_manager.py verify <code>")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "send":
        if len(sys.argv) < 4:
            print("Missing phone or email")
            sys.exit(1)
        asyncio.run(send_code(sys.argv[2], sys.argv[3]))
    elif cmd == "verify":
        if len(sys.argv) < 3:
            print("Missing code")
            sys.exit(1)
        asyncio.run(verify_code(sys.argv[2]))
