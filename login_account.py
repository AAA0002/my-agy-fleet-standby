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
import urllib.parse
import aiohttp
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
from telethon.tl.functions.messages import RequestWebViewRequest, RequestAppWebViewRequest
from telethon.tl.types import InputBotAppShortName
from dotenv import load_dotenv
from phone_detector import detect_and_normalize_phone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")
FLEET_TON_WALLETS_FILE = os.path.join(BASE_DIR, "fleet_ton_wallets.json")
FLEET_EVM_WALLETS_FILE = os.path.join(BASE_DIR, "fleet_evm_wallets.json")
load_dotenv(os.path.join(BASE_DIR, ".env"))

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")

# Primary User Referral Links & Codes
AILAB_BOT = "AiLab_robot"
AILAB_REFERRAL_CODE = "296852"

ART_BOT = "ART_AIRDROP_BOT"
ART_REFERRAL_CODE = "6727787768"

AINOVUM_BOT = "ainovum_bot"
AINOVUM_REFERRAL_CODE = "ref_6727787768"

STONES_BOT = "stoneswithestand_bot"
STONES_REFERRAL_CODE = "r6727787768"

ULTRAWALLET_BOT = "UltrawalletTrade_Bot"
ULTRAWALLET_REFERRAL_CODE = "6727787768"

MRG_BOT = "mrgminerbot"
MRG_REFERRAL_CODE = "ref_IRN1G3XD"

APX_BOT = "ApxMinerBot"
APX_REFERRAL_CODE = "6727787768"

PRIMARY_CHAT_ID = "6727787768"
PRIMARY_EVM_WALLET = "0xfda4182001672b9f0f09e2118242e543e35ed5ce"
PRIMARY_TON_WALLET = "UQBPZiSvitdPU3VUyJK2mRaHVBl69xejw5aOrh1KfKA7gwDT"


if not API_ID or not API_HASH:
    print("❌ Error: TELEGRAM_API_ID and TELEGRAM_API_HASH not found in .env")
    sys.exit(1)

try:
    API_ID = int(API_ID)
except ValueError:
    print("❌ Error: TELEGRAM_API_ID must be an integer")
    sys.exit(1)


OFFICIAL_EMAIL = os.getenv("FLEET_EMAIL", "aaa.support.a@gmail.com")

def generate_random_email():
    return OFFICIAL_EMAIL


def ensure_account_ton_wallet(acc: dict) -> str:
    """Ensures account has an isolated TON v4r2 wallet in fleet_ton_wallets.json."""
    uid = str(acc.get("user_id"))
    if not uid or uid == PRIMARY_CHAT_ID:
        return PRIMARY_TON_WALLET

    fwallets = {}
    if os.path.exists(FLEET_TON_WALLETS_FILE):
        try:
            with open(FLEET_TON_WALLETS_FILE, "r", encoding="utf-8") as f:
                fwallets = json.load(f)
        except Exception:
            fwallets = {}

    if uid in fwallets and fwallets[uid].get("address"):
        acc["ton_wallet"] = {"address": fwallets[uid]["address"], "mnemonic": fwallets[uid].get("mnemonic", ""), "version": "v4r2"}
        return fwallets[uid]["address"]

    try:
        from tonsdk.contract.wallet import Wallets, WalletVersionEnum
        mnemonics, pub_k, priv_k, wallet = Wallets.create(WalletVersionEnum.v4r2, workchain=0)
        addr_non_bounce = wallet.address.to_string(is_user_friendly=True, is_bounceable=False, is_url_safe=True)
        addr_bounce = wallet.address.to_string(is_user_friendly=True, is_bounceable=True, is_url_safe=True)
        addr_raw = wallet.address.to_string(is_user_friendly=False)

        worker_count = len([k for k in fwallets if not str(k).startswith("_")])
        entry = {
            "account_index": worker_count + 2,
            "name": acc.get("name", "Worker"),
            "user_id": uid,
            "address": addr_non_bounce,
            "address_bounceable": addr_bounce,
            "address_raw": addr_raw,
            "public_key_hex": pub_k.hex(),
            "private_key_hex": priv_k.hex(),
            "mnemonic": " ".join(mnemonics),
            "mnemonic_words": mnemonics,
            "wallet_version": "v4r2",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        fwallets[uid] = entry
        with open(FLEET_TON_WALLETS_FILE, "w", encoding="utf-8") as f:
            json.dump(fwallets, f, indent=2, ensure_ascii=False)

        acc["ton_wallet"] = {"address": addr_non_bounce, "mnemonic": " ".join(mnemonics), "version": "v4r2"}
        print(f"  🔑 Generated isolated TON wallet for {acc.get('name')}: {addr_non_bounce}")
        return addr_non_bounce
    except Exception as e:
        print(f"  ❌ Error auto-generating TON wallet: {e}")
        return ""


def ensure_account_evm_wallet(acc: dict) -> str:
    """Ensures account has an isolated EVM / BEP-20 / Arbitrum wallet in fleet_evm_wallets.json."""
    uid = str(acc.get("user_id"))
    if not uid or uid == PRIMARY_CHAT_ID:
        return PRIMARY_EVM_WALLET

    ewallets = {}
    if os.path.exists(FLEET_EVM_WALLETS_FILE):
        try:
            with open(FLEET_EVM_WALLETS_FILE, "r", encoding="utf-8") as f:
                ewallets = json.load(f)
        except Exception:
            ewallets = {}

    if uid in ewallets and ewallets[uid].get("address"):
        acc["evm_wallet"] = {"address": ewallets[uid]["address"], "private_key": ewallets[uid].get("private_key", ""), "is_primary": False}
        return ewallets[uid]["address"]

    try:
        from eth_account import Account
        acct = Account.create()
        worker_count = len([k for k in ewallets if not str(k).startswith("_")])
        entry = {
            "account_index": worker_count + 2,
            "name": acc.get("name", "Worker"),
            "user_id": uid,
            "address": acct.address,
            "private_key": acct.key.hex(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        ewallets[uid] = entry
        with open(FLEET_EVM_WALLETS_FILE, "w", encoding="utf-8") as f:
            json.dump(ewallets, f, indent=2, ensure_ascii=False)

        acc["evm_wallet"] = {"address": acct.address, "private_key": acct.key.hex(), "is_primary": False}
        print(f"  🔑 Generated isolated EVM wallet for {acc.get('name')}: {acct.address}")
        return acct.address
    except Exception as e:
        print(f"  ⚠️ Could not auto-generate EVM wallet (eth_account unavailable or error: {e})")
        return ""


async def bind_referrals(client, me, acc_entry):
    acc_uid = str(me.id)
    acc_name = acc_entry.get("name", "Worker")

    # Ensure isolated wallets are assigned
    ton_wallet = ensure_account_ton_wallet(acc_entry)
    evm_wallet = ensure_account_evm_wallet(acc_entry)

    if acc_uid == PRIMARY_CHAT_ID or acc_entry.get("is_referral_host"):
        print("ℹ️ Primary referral host account. Skipping self-referral.")
        acc_entry["is_referral_host"] = True
        return

    print(f"\n🔗 Automatically binding account to all 8 user referral links with wallet isolation...")

    # 1. AI Lab Robot (@AiLab_robot) - Referral: 296852
    print(f"  • [1/8] Connecting to @{AILAB_BOT} with referral: {AILAB_REFERRAL_CODE}...")
    try:
        try:
            await client(UnblockRequest(id=AILAB_BOT))
        except Exception:
            pass
        bot_ai = await client.get_entity(AILAB_BOT)
        await client.send_message(bot_ai, f"/start {AILAB_REFERRAL_CODE}")
        await asyncio.sleep(2.0)
        try:
            res_ai = await client(RequestWebViewRequest(
                peer=bot_ai,
                bot=bot_ai,
                platform="android",
                url="https://ailab-agent.online/"
            ))
            parsed_ai = urllib.parse.urlparse(res_ai.url)
            init_ai = urllib.parse.parse_qs(parsed_ai.fragment).get("tgWebAppData", [None])[0]
            if init_ai:
                async with aiohttp.ClientSession() as ai_sess:
                    await ai_sess.post(
                        "https://api.ailab-agent.online/api/v1/users/auth/login",
                        json={"user": init_ai},
                        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (Linux; Android 14)"},
                        timeout=aiohttp.ClientTimeout(total=8)
                    )
        except Exception:
            pass
        acc_entry["ailab_referral_bound"] = True
        print(f"  ✅ [1/8] Successfully bound to AI Lab Robot ({AILAB_REFERRAL_CODE})!")
    except Exception as e:
        print(f"  ❌ Warning binding AI Lab referral: {e}")

    # 2. ART Airdrop (@ART_AIRDROP_BOT) - Referral: 6727787768
    print(f"  • [2/8] Connecting to @{ART_BOT} with referral: {ART_REFERRAL_CODE}...")
    try:
        try:
            await client(UnblockRequest(id=ART_BOT))
        except Exception:
            pass
        await client.send_message(ART_BOT, f"/start {ART_REFERRAL_CODE}")
        await asyncio.sleep(2.0)
        try:
            await client(JoinChannelRequest("ART_AIRDROP"))
        except Exception:
            pass
        acc_entry["art_referral_bound"] = True
        print(f"  ✅ [2/8] Successfully bound to ART Airdrop ({ART_REFERRAL_CODE})!")
    except Exception as e:
        print(f"  ❌ Warning binding ART Airdrop referral: {e}")

    # 3. Ainovum Bot (@ainovum_bot) - Referral: ref_6727787768
    print(f"  • [3/8] Connecting to @{AINOVUM_BOT} with referral: {AINOVUM_REFERRAL_CODE}...")
    try:
        try:
            await client(UnblockRequest(id=AINOVUM_BOT))
        except Exception:
            pass
        bot_an = await client.get_entity(AINOVUM_BOT)
        await client.send_message(bot_an, f"/start {AINOVUM_REFERRAL_CODE}")
        await asyncio.sleep(2.0)
        try:
            res_an = await client(RequestWebViewRequest(
                peer=bot_an,
                bot=bot_an,
                platform="android",
                url=f"https://ainovum.biz/?startapp={AINOVUM_REFERRAL_CODE}&ref={AINOVUM_REFERRAL_CODE}"
            ))
            parsed_an = urllib.parse.urlparse(res_an.url)
            init_an = urllib.parse.parse_qs(parsed_an.fragment).get("tgWebAppData", [None])[0]
            if init_an:
                async with aiohttp.ClientSession() as an_sess:
                    await an_sess.post(
                        "https://ainovum.biz/api/bootstrap",
                        json={
                            "initData": init_an,
                            "platform": "android",
                            "referrer": AINOVUM_REFERRAL_CODE,
                            "timezone_offset_minutes": 0,
                            "language_code": "en",
                            "registration_duration_ms": 1500
                        },
                        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (Linux; Android 14)"},
                        timeout=aiohttp.ClientTimeout(total=10)
                    )
        except Exception:
            pass
        acc_entry["ainovum_referral_bound"] = True
        print(f"  ✅ [3/7] Successfully bound to Ainovum Bot ({AINOVUM_REFERRAL_CODE})!")
    except Exception as e:
        print(f"  ❌ Warning binding Ainovum referral: {e}")

    # 4. Stones Miners (@stoneswithestand_bot) - Referral: r6727787768
    print(f"  • [4/7] Connecting to @{STONES_BOT} with referral: {STONES_REFERRAL_CODE}...")
    try:
        try:
            await client(UnblockRequest(id=STONES_BOT))
        except Exception:
            pass
        await client.send_message(STONES_BOT, f"/start {STONES_REFERRAL_CODE}")
        await asyncio.sleep(1.5)
        try:
            await client(JoinChannelRequest("stoneswithestand"))
        except Exception:
            pass
        acc_entry["stones_referral_bound"] = True
        print(f"  ✅ [4/7] Successfully bound to Stones Miners ({STONES_REFERRAL_CODE})!")
    except Exception as e:
        print(f"  ❌ Warning binding Stones Miners referral: {e}")

    # 5. Ultra Wallet (@UltrawalletTrade_Bot) - Referral: 6727787768
    print(f"  • [5/7] Connecting to @{ULTRAWALLET_BOT} with referral: {ULTRAWALLET_REFERRAL_CODE}...")
    try:
        try:
            await client(UnblockRequest(id=ULTRAWALLET_BOT))
        except Exception:
            pass
        bot_uw = await client.get_input_entity(ULTRAWALLET_BOT)
        res_uw = await client(RequestAppWebViewRequest(
            peer=bot_uw,
            app=InputBotAppShortName(bot_id=bot_uw, short_name="app"),
            platform="android",
            start_param=ULTRAWALLET_REFERRAL_CODE
        ))
        parsed_uw = urllib.parse.urlparse(res_uw.url)
        init_uw = urllib.parse.parse_qs(parsed_uw.fragment).get("tgWebAppData", [None])[0]
        if init_uw:
            async with aiohttp.ClientSession() as uw_sess:
                await uw_sess.post(
                    "https://wallet.trxvault.top/api/telegramLogin",
                    json={"initData": init_uw, "refBy": ULTRAWALLET_REFERRAL_CODE},
                    headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (Linux; Android 14)"},
                    timeout=aiohttp.ClientTimeout(total=8)
                )
        acc_entry["ultrawallet_referral_bound"] = True
        print(f"  ✅ [5/7] Successfully bound to Ultra Wallet ({ULTRAWALLET_REFERRAL_CODE})!")
    except Exception as e:
        print(f"  ❌ Warning binding Ultra Wallet referral: {e}")

    # 6. MRG Miner (@mrgminerbot) - Referral: ref_IRN1G3XD (Strict Isolated TON Wallet)
    print(f"  • [6/7] Connecting to @{MRG_BOT} with referral: {MRG_REFERRAL_CODE}...")
    try:
        try:
            await client(UnblockRequest(id=MRG_BOT))
        except Exception:
            pass
        bot_mrg = await client.get_input_entity(MRG_BOT)
        res_mrg = await client(RequestAppWebViewRequest(
            peer=bot_mrg,
            app=InputBotAppShortName(bot_id=bot_mrg, short_name="app"),
            platform="android",
            start_param=MRG_REFERRAL_CODE
        ))
        parsed_mrg = urllib.parse.urlparse(res_mrg.url)
        m_init = urllib.parse.parse_qs(parsed_mrg.fragment).get("tgWebAppData", [None])[0]
        if m_init:
            async with aiohttp.ClientSession() as m_sess:
                m_headers = {"Content-Type": "application/json", "Origin": "https://app.mrgtoken.xyz", "Referer": "https://app.mrgtoken.xyz/"}
                await m_sess.post("https://mrg.up.railway.app/api/auth/verify", json={"initData": m_init, "startParam": MRG_REFERRAL_CODE}, headers=m_headers, timeout=aiohttp.ClientTimeout(total=10))
                # Connect isolated TON wallet
                if ton_wallet:
                    print(f"    - Connecting isolated TON wallet for MRG: {ton_wallet}")
                    await m_sess.post("https://mrg.up.railway.app/api/user/connect-wallet", json={"initData": m_init, "address": ton_wallet, "balance": 0}, headers=m_headers, timeout=aiohttp.ClientTimeout(total=10))
        try:
            await client(JoinChannelRequest("mrgminer"))
        except Exception:
            pass
        acc_entry["mrg_referral_bound"] = True
        print(f"  ✅ [6/7] Successfully bound to MRG Miner ({MRG_REFERRAL_CODE}) with isolated TON wallet!")
    except Exception as e:
        print(f"  ❌ Warning binding MRG Miner referral: {e}")

    # 7. Apex Miner (@ApxMinerBot) - Referral: 6727787768
    print(f"  • [7/7] Connecting to @{APX_BOT} with referral: {APX_REFERRAL_CODE}...")
    try:
        try:
            await client(UnblockRequest(id=APX_BOT))
        except Exception:
            pass
        bot_apx = await client.get_input_entity(APX_BOT)
        res_apx = await client(RequestAppWebViewRequest(
            peer=bot_apx,
            app=InputBotAppShortName(bot_id=bot_apx, short_name="app"),
            platform="android",
            start_param=APX_REFERRAL_CODE
        ))
        parsed_apx = urllib.parse.urlparse(res_apx.url)
        init_apx = urllib.parse.parse_qs(parsed_apx.fragment).get("tgWebAppData", [None])[0]
        if init_apx:
            async with aiohttp.ClientSession() as apx_sess:
                apx_h = {"Content-Type": "application/json"}
                await apx_sess.post("https://apex-miner.vercel.app/api/auth/telegram", json={"initData": init_apx}, headers=apx_h, timeout=aiohttp.ClientTimeout(total=8))
                await apx_sess.post("https://apex-miner.vercel.app/api/register", json={"initData": init_apx}, headers=apx_h, timeout=aiohttp.ClientTimeout(total=8))
        try:
            await client(JoinChannelRequest("ApexMiner_Official"))
        except Exception:
            pass
        acc_entry["apx_referral_bound"] = True
        print(f"  ✅ [7/7] Successfully bound to Apex Miner ({APX_REFERRAL_CODE})!")
    except Exception as e:
        print(f"  ❌ Warning binding Apex Miner referral: {e}")



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
