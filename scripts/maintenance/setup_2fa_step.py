#!/usr/bin/env python3
"""
setup_2fa_step.py
Two-step 2FA password & recovery email binder for Telegram accounts.
"""

import sys
import os
import json
import asyncio
from telethon import TelegramClient, functions, types, errors
from telethon.sessions import StringSession
from telethon import password as pwd_mod

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
BASE_DIR = PROJECT_ROOT
ACCOUNTS_FILE = os.path.join(PROJECT_ROOT, "accounts.json")
STATE_FILE = os.path.join(BASE_DIR, "temp_2fa_state.json")

API_ID = 37321306
API_HASH = "5cd9e5bbfb572a4429a0c54774153b47"


def get_account_session(phone: str):
    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        accounts = json.load(f)
    for a in accounts:
        if a.get("phone") == phone:
            return a.get("session_string"), a.get("name")
    return None, None


async def start_2fa(phone: str, new_password: str, email: str):
    sess, name = get_account_session(phone)
    if not sess:
        print(f"ERROR:Account {phone} not found in accounts.json")
        return

    cl = TelegramClient(StringSession(sess), API_ID, API_HASH, timeout=10)
    await cl.connect()

    try:
        if not await cl.is_user_authorized():
            print("ERROR:Account not authorized")
            return

        pwd = await cl(functions.account.GetPasswordRequest())
        if pwd.has_password:
            print("ERROR:Account already has 2FA enabled!")
            return

        pwd.new_algo.salt1 += os.urandom(32)
        new_password_hash = pwd_mod.compute_digest(pwd.new_algo, new_password)

        state = {
            "phone": phone,
            "name": name,
            "session_string": sess,
            "email": email,
            "password": new_password
        }

        try:
            await cl(functions.account.UpdatePasswordSettingsRequest(
                password=types.InputCheckPasswordEmpty(),
                new_settings=types.account.PasswordInputSettings(
                    new_algo=pwd.new_algo,
                    new_password_hash=new_password_hash,
                    hint="Arif",
                    email=email,
                    new_secure_settings=None
                )
            ))
            # If no EmailUnconfirmedError, password was set directly
            print("SUCCESS_DIRECT:2FA password set directly without email challenge!")
            if os.path.exists(STATE_FILE):
                os.remove(STATE_FILE)
        except errors.EmailUnconfirmedError as e:
            state["code_length"] = e.code_length
            with open(STATE_FILE, "w") as f:
                json.dump(state, f)
            print(f"CODE_SENT:{email}:{e.code_length}")
    except Exception as e:
        print(f"ERROR_START:{type(e).__name__}:{e}")
    finally:
        await cl.disconnect()


async def confirm_2fa(code: str):
    code = code.strip()
    if not os.path.exists(STATE_FILE):
        print("ERROR:No pending 2FA setup in progress.")
        return

    with open(STATE_FILE, "r") as f:
        state = json.load(f)

    sess = state["session_string"]
    phone = state["phone"]
    name = state["name"]

    cl = TelegramClient(StringSession(sess), API_ID, API_HASH, timeout=10)
    await cl.connect()

    try:
        await cl(functions.account.ConfirmPasswordEmailRequest(code=code))
        
        # Verify status
        pwd = await cl(functions.account.GetPasswordRequest())
        if pwd.has_password:
            print(f"SUCCESS_CONFIRMED:{phone}:{name}:has_2fa={pwd.has_password}:has_email={pwd.has_recovery}")
            if os.path.exists(STATE_FILE):
                os.remove(STATE_FILE)
        else:
            print("WARNING:Confirmation completed but password status is False.")
    except Exception as e:
        print(f"ERROR_CONFIRM:{type(e).__name__}:{e}")
    finally:
        await cl.disconnect()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python setup_2fa_step.py start <phone> <password> <email> OR python setup_2fa_step.py confirm <code>")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "start":
        if len(sys.argv) < 5:
            print("Missing arguments for start")
            sys.exit(1)
        asyncio.run(start_2fa(sys.argv[2], sys.argv[3], sys.argv[4]))
    elif cmd == "confirm":
        if len(sys.argv) < 3:
            print("Missing code for confirm")
            sys.exit(1)
        asyncio.run(confirm_2fa(sys.argv[2]))
