#!/usr/bin/env python3
"""
login_step.py
Two-step interactive Telegram session regenerator with 2FA password fallback.
"""

import sys
import os
import json
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    PasswordHashInvalidError
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")
SESSION_FILE = os.path.join(BASE_DIR, "temp_relogin")
STATE_FILE = os.path.join(BASE_DIR, "temp_relogin_state.json")

API_ID = 37321306
API_HASH = "5cd9e5bbfb572a4429a0c54774153b47"

PASSWORDS = ["Arif216@", "Arif-Abid"]


async def request_code(phone: str):
    phone = phone.strip()
    if os.path.exists(f"{SESSION_FILE}.session"):
        try:
            os.remove(f"{SESSION_FILE}.session")
        except Exception:
            pass
    if os.path.exists(STATE_FILE):
        try:
            os.remove(STATE_FILE)
        except Exception:
            pass

    client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
    await client.connect()

    try:
        res = await client.send_code_request(phone)
        state = {
            "phone": phone,
            "phone_code_hash": res.phone_code_hash
        }
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
        print(f"SUCCESS_CODE_SENT:{phone}")
    except Exception as e:
        print(f"ERROR_SENDING_CODE:{type(e).__name__}:{e}")
    finally:
        await client.disconnect()


async def verify_code(code: str):
    code = code.strip()
    if not os.path.exists(STATE_FILE) or not os.path.exists(f"{SESSION_FILE}.session"):
        print("ERROR_NO_PENDING_STATE")
        return

    with open(STATE_FILE, "r") as f:
        state = json.load(f)

    phone = state["phone"]
    phone_code_hash = state["phone_code_hash"]

    client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
    await client.connect()

    logged_in = False
    try:
        try:
            await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
            logged_in = True
        except SessionPasswordNeededError:
            print("2FA_NEEDED:Attempting 2FA passwords...")
            for pwd in PASSWORDS:
                try:
                    await client.sign_in(password=pwd)
                    print(f"2FA_SUCCESS:Logged in using 2FA password: {pwd}")
                    logged_in = True
                    break
                except PasswordHashInvalidError:
                    print(f"2FA_INCORRECT:Password {pwd} incorrect, trying next...")
                except Exception as pe:
                    print(f"2FA_ERROR:{pe}")
            if not logged_in:
                print("ERROR_2FA_FAILED:All known 2FA passwords failed.")
                return

        if logged_in:
            me = await client.get_me()
            new_session_string = StringSession.save(client.session)
            
            # Update accounts.json
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                accounts = json.load(f)

            found = False
            for acc in accounts:
                if acc.get("phone") == phone:
                    acc["session_string"] = new_session_string
                    acc["status"] = "active"
                    acc["user_id"] = me.id
                    acc["name"] = f"{me.first_name or ''} {me.last_name or ''}".strip() or acc.get("name")
                    acc["username"] = me.username or acc.get("username")
                    found = True
                    break

            if not found:
                accounts.append({
                    "name": f"{me.first_name or ''} {me.last_name or ''}".strip() or "Telegram User",
                    "username": me.username or "",
                    "user_id": me.id,
                    "phone": phone,
                    "session_string": new_session_string,
                    "status": "active"
                })

            with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
                json.dump(accounts, f, indent=2, ensure_ascii=False)

            print(f"SUCCESS_LOGIN:{phone}:{me.id}:{me.first_name}")

            # Clean up temp files
            if os.path.exists(STATE_FILE):
                os.remove(STATE_FILE)
            if os.path.exists(f"{SESSION_FILE}.session"):
                os.remove(f"{SESSION_FILE}.session")

    except Exception as e:
        print(f"ERROR_SIGN_IN:{type(e).__name__}:{e}")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python login_step.py request <phone> OR python login_step.py verify <code>")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "request":
        if len(sys.argv) < 3:
            print("Missing phone number")
            sys.exit(1)
        asyncio.run(request_code(sys.argv[2]))
    elif cmd == "verify":
        if len(sys.argv) < 3:
            print("Missing verification code")
            sys.exit(1)
        asyncio.run(verify_code(sys.argv[2]))
