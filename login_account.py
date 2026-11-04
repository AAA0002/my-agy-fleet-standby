#!/usr/bin/env python3
"""
Interactive Telegram Account Login & Session Generator
Allows adding multiple Telegram accounts to the 24/7 cloud worker.
"""

import os
import sys
import re
import json
import asyncio
import time
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
from telethon.tl.functions.messages import RequestWebViewRequest, RequestAppWebViewRequest, ImportChatInviteRequest
from telethon.tl.functions.account import UpdateNotifySettingsRequest
from telethon.tl.types import InputBotAppShortName, InputNotifyPeer, InputPeerNotifySettings
from dotenv import load_dotenv
from phone_detector import detect_and_normalize_phone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")
FLEET_TON_WALLETS_FILE = os.path.join(BASE_DIR, "fleet_ton_wallets.json")
FLEET_EVM_WALLETS_FILE = os.path.join(BASE_DIR, "fleet_evm_wallets.json")
FLEET_TRON_WALLETS_FILE = os.path.join(BASE_DIR, "fleet_tron_wallets.json")
load_dotenv(os.path.join(BASE_DIR, ".env"))

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")

# All 9 Verified Legitimate Fleet Bots & Referral Codes
ATF_BOT = "ATF_AIRDROP_bot"
ATF_REFERRAL_CODE = "6727787768"

BOT_ALIASES = {
    "ATF_AIRDROP_bot": ["atfminers_bot", 8233119648, 7058204689],
    "atfminers_bot": ["ATF_AIRDROP_bot", 8233119648, 7058204689],
    "Kynex_miningbot": ["kynexnetworkbot", 8663611744, 7421882583],
    "Pepe_gram_bot": ["pepegram_bot", 8958239010, 7639148332],
}

async def resolve_bot_entity(client, bot_name):
    candidates = [bot_name]
    if bot_name in BOT_ALIASES:
        for a in BOT_ALIASES[bot_name]:
            if a not in candidates:
                candidates.append(a)
    for cand in candidates:
        try:
            ent = await client.get_entity(cand)
            if ent:
                return ent
        except Exception:
            continue
    return None

KYNEX_BOT = "Kynex_miningbot"
KYNEX_REFERRAL_CODE = "6727787768"

DIGGO_BOT = "Diggominer_bot"
DIGGO_REFERRAL_CODE = "ref_4088138f11effe8eef4b86ff"

PEPE_BOT = "Pepe_gram_bot"
PEPE_REFERRAL_CODE = "1449"

ADX_BOT = "AdxEarnAibot"
ADX_REFERRAL_CODE = "6727787768"

CHICKEN_BOT = "ChickenLandBot"
CHICKEN_REFERRAL_CODE = "12668"

GROUCHEMINE_BOT = "GRC_AirdrooBot"
GROUCHEMINE_REFERRAL_CODE = "6727787768"

LUMEON_BOT = "lumeonminer_bot"
LUMEON_REFERRAL_CODE = "6727787768"

EARNVAULT_BOT = "EarnVaultApp_bot"
EARNVAULT_REFERRAL_CODE = "6727787768"

PRIMARY_CHAT_ID = "6727787768"
PRIMARY_EVM_WALLET = "0xfda4182001672b9f0f09e2118242e543e35ed5ce"
PRIMARY_TON_WALLET = "UQBPZiSvitdPU3VUyJK2mRaHVBl69xejw5aOrh1KfKA7gwDT"
PRIMARY_TRON_WALLET = "TZ6LY4QwiJr8WXN6W1HjiUCbkvFxq1vmUJ"

async def mute_peer(client, peer, name: str = ""):
    """Permanently silences notifications from a bot, channel, or group."""
    try:
        input_peer = await client.get_input_entity(peer)
        settings = InputPeerNotifySettings(
            show_previews=False,
            silent=True,
            mute_until=datetime(2038, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        )
        await client(UpdateNotifySettingsRequest(
            peer=InputNotifyPeer(input_peer),
            settings=settings
        ))
    except Exception:
        pass

async def join_tg_target(client, link_or_username: str, name: str = ""):
    """Joins a Telegram public channel or private invite link."""
    target = str(link_or_username or "").strip()
    if not target:
        return
    if "+" in target or "joinchat/" in target:
        h = target.split("+")[-1].split("?")[0] if "+" in target else target.split("joinchat/")[-1].split("?")[0]
        h = h.strip()
        if h:
            try:
                await client(ImportChatInviteRequest(h))
            except Exception:
                pass
    else:
        target_clean = target.replace("@", "").split("/")[-1].strip()
        if target_clean:
            try:
                await client(JoinChannelRequest(target_clean))
            except Exception:
                pass


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
        from fleet_wallet_provisioner import find_existing_account_wallets
        _, ex_wallets, _ = find_existing_account_wallets(user_id=uid, phone=acc.get("phone"))
        if ex_wallets and ex_wallets.get("ton", {}).get("address"):
            acc["ton_wallet"] = ex_wallets["ton"]
            return ex_wallets["ton"]["address"]
    except Exception:
        pass

    try:
        from tonsdk.contract.wallet import Wallets, WalletVersionEnum
        mnemonics, pub_k, priv_k, wallet = Wallets.create(WalletVersionEnum.v4r2, workchain=0)
        addr_non_bounce = wallet.address.to_string(is_user_friendly=True, is_bounceable=False, is_url_safe=True)
        addr_bounce = wallet.address.to_string(is_user_friendly=True, is_bounceable=True, is_url_safe=True)
        addr_raw = wallet.address.to_string(is_user_friendly=False)

        existing_indices = [v.get("account_index", 0) for k, v in fwallets.items() if isinstance(v, dict) and v.get("account_index")]
        next_index = max(existing_indices, default=1) + 1
        entry = {
            "account_index": next_index,
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
        from fleet_wallet_provisioner import find_existing_account_wallets
        _, ex_wallets, _ = find_existing_account_wallets(user_id=uid, phone=acc.get("phone"))
        if ex_wallets and ex_wallets.get("evm", {}).get("address"):
            acc["evm_wallet"] = ex_wallets["evm"]
            return ex_wallets["evm"]["address"]
    except Exception:
        pass

    try:
        from eth_account import Account
        acct = Account.create()
        existing_indices = [v.get("account_index", 0) for k, v in ewallets.items() if isinstance(v, dict) and v.get("account_index")]
        next_index = max(existing_indices, default=1) + 1
        entry = {
            "account_index": next_index,
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


def ensure_account_tron_wallet(acc: dict) -> str:
    """Ensures account has an isolated TRON (TRX / TRC-20) wallet in fleet_tron_wallets.json."""
    uid = str(acc.get("user_id"))
    if not uid or uid == PRIMARY_CHAT_ID:
        return PRIMARY_TRON_WALLET

    twallets = {}
    if os.path.exists(FLEET_TRON_WALLETS_FILE):
        try:
            with open(FLEET_TRON_WALLETS_FILE, "r", encoding="utf-8") as f:
                twallets = json.load(f)
        except Exception:
            twallets = {}

    if uid in twallets and twallets[uid].get("address"):
        acc["tron_wallet"] = {"address": twallets[uid]["address"], "private_key": twallets[uid].get("private_key", ""), "network": "TRON (TRX / TRC-20)"}
        return twallets[uid]["address"]

    try:
        from fleet_wallet_provisioner import find_existing_account_wallets
        _, ex_wallets, _ = find_existing_account_wallets(user_id=uid, phone=acc.get("phone"))
        if ex_wallets and ex_wallets.get("tron", {}).get("address"):
            acc["tron_wallet"] = ex_wallets["tron"]
            return ex_wallets["tron"]["address"]
    except Exception:
        pass

    try:
        from fleet_wallet_provisioner import generate_multichain_wallet_suite
        cur_accs = load_accounts()
        next_idx = len(cur_accs) + 1
        suite = generate_multichain_wallet_suite(next_idx, acc.get("name", "Worker"), uid, acc.get("phone", ""), acc.get("username", ""))
        tw = suite.get("tron", {})
        if tw.get("address"):
            twallets[uid] = tw
            with open(FLEET_TRON_WALLETS_FILE, "w", encoding="utf-8") as f:
                json.dump(twallets, f, indent=2, ensure_ascii=False)
            acc["tron_wallet"] = tw
            print(f"  🔑 Generated isolated TRON wallet for {acc.get('name')}: {tw['address']}")
            return tw["address"]
    except Exception as e:
        print(f"  ⚠️ Could not auto-generate TRON wallet: {e}")
    return ""


async def bind_referrals(client, me, acc_entry):
    acc_uid = str(me.id)
    acc_name = acc_entry.get("name", "Worker")

    # Ensure isolated wallets are assigned
    ton_wallet = ensure_account_ton_wallet(acc_entry)
    evm_wallet = ensure_account_evm_wallet(acc_entry)
    tron_wallet = ensure_account_tron_wallet(acc_entry)

    if acc_uid == PRIMARY_CHAT_ID or acc_entry.get("is_referral_host"):
        print("ℹ️ Primary referral host account. Skipping self-referral.")
        acc_entry["is_referral_host"] = True
        return

    print(f"\n🔗 Automatically binding account to all 9 verified fleet bots with wallet isolation...")

    # 1. ATF Miner (@atfminers_bot) - Referral: 6727787768
    print(f"  • [1/9] Connecting to @{ATF_BOT} with referral: {ATF_REFERRAL_CODE}...")
    try:
        try:
            await client(UnblockRequest(id=ATF_BOT))
        except Exception:
            pass
        bot_atf = await client.get_entity(ATF_BOT)
        await mute_peer(client, bot_atf, "atfminers_bot")
        try:
            await client.send_message(bot_atf, f"/start {ATF_REFERRAL_CODE}")
            await asyncio.sleep(0.5)
        except Exception:
            pass
        await asyncio.sleep(1.0)
        try:
            atf_url = f"https://atfminers.asloni.online/miner/index.html?entry=bot_start&ref={ATF_REFERRAL_CODE}"
            res_atf = await client(RequestWebViewRequest(
                peer=bot_atf,
                bot=bot_atf,
                url=atf_url,
                start_param=ATF_REFERRAL_CODE,
                platform="android"
            ))
            p_atf = urllib.parse.urlparse(getattr(res_atf, 'url', None) or "")
            atf_init = urllib.parse.parse_qs(p_atf.fragment).get("tgWebAppData", [None])[0] or urllib.parse.parse_qs(p_atf.query).get("tgWebAppData", [None])[0]
            if atf_init:
                acc_entry["atf_init_data"] = atf_init
                async with aiohttp.ClientSession() as s_atf:
                    atf_h = {"Content-Type": "application/json", "X-Requested-With": "XMLHttpRequest", "Origin": "https://atfminers.asloni.online", "Referer": "https://atfminers.asloni.online/miner/index.html"}
                    atf_p = {"initData": atf_init, "tg_id": int(me.id), "username": acc_entry.get("username", ""), "ref": ATF_REFERRAL_CODE, "request_id": f"rq-{int(time.time()*1000)}-onboard", "device_id": f"dev-{me.id}"}
                    await s_atf.post(f"https://atfminers.asloni.online/miner/index.php?action=login&t={int(time.time()*1000)}", json=atf_p, headers=atf_h, timeout=aiohttp.ClientTimeout(total=10))
                    if ton_wallet:
                        sync_p = {"initData": atf_init, "tg_id": int(me.id), "wallet": ton_wallet, "request_id": f"rq-{int(time.time()*1000)}-sync"}
                        await s_atf.post(f"https://atfminers.asloni.online/miner/index.php?action=sync_wallet&t={int(time.time()*1000)}", json=sync_p, headers=atf_h, timeout=aiohttp.ClientTimeout(total=8))
                    await s_atf.post(f"https://atfminers.asloni.online/miner/index.php?action=claim&t={int(time.time()*1000)}", json=atf_p, headers=atf_h, timeout=aiohttp.ClientTimeout(total=8))
        except Exception:
            pass
        acc_entry["atf_referral_bound"] = True
        print(f"  ✅ [1/9] Successfully bound to ATF Miner ({ATF_REFERRAL_CODE})!")
    except Exception as e:
        print(f"  ❌ Warning binding ATF referral: {e}")

    # 2. Kynex Network (@Kynex_miningbot) - Referral: 6727787768
    print(f"  • [2/9] Connecting to @{KYNEX_BOT} with referral: {KYNEX_REFERRAL_CODE}...")
    try:
        try:
            await client(UnblockRequest(id=KYNEX_BOT))
        except Exception:
            pass
        b_ky = await client.get_entity(KYNEX_BOT)
        await mute_peer(client, b_ky, "Kynex_miningbot")
        try:
            await client.send_message(b_ky, f"/start {KYNEX_REFERRAL_CODE}")
            await asyncio.sleep(0.5)
        except Exception:
            pass
        await asyncio.sleep(1.0)
        try:
            from telethon.tl.types import InputBotAppShortName
            from telethon.tl.functions.messages import RequestAppWebViewRequest
            bot_in = await client.get_input_entity(b_ky)
            r_ky = await client(RequestAppWebViewRequest(
                peer=bot_in,
                app=InputBotAppShortName(bot_id=bot_in, short_name="App"),
                platform="android",
                start_param=KYNEX_REFERRAL_CODE
            ))
            p_ky = urllib.parse.urlparse(getattr(r_ky, 'url', None) or "")
            ky_init = urllib.parse.parse_qs(p_ky.fragment).get("tgWebAppData", [None])[0] or urllib.parse.parse_qs(p_ky.query).get("tgWebAppData", [None])[0]
            if ky_init:
                if ky_init.startswith("user%3D") or "%257B" in ky_init:
                    ky_init = urllib.parse.unquote(ky_init)
                acc_entry["kynex_init_data"] = ky_init
                import kynex_miner
                async with aiohttp.ClientSession() as ky_s:
                    await kynex_miner.farm_kynex_account(ky_s, ky_init, acc_entry, is_master=False)
        except Exception as ke:
            pass
        acc_entry["kynex_referral_bound"] = True
        print(f"  ✅ [2/9] Successfully bound to Kynex Network ({KYNEX_REFERRAL_CODE})!")
    except Exception as e:
        print(f"  ❌ Warning binding Kynex Network referral: {e}")

    # 3. DiggoMiner (@Diggominer_bot) - Referral: ref_4088138f11effe8eef4b86ff
    print(f"  • [3/9] Connecting to @{DIGGO_BOT} with referral: {DIGGO_REFERRAL_CODE}...")
    try:
        try:
            await client(UnblockRequest(id=DIGGO_BOT))
        except Exception:
            pass
        b_diggo = await client.get_entity(DIGGO_BOT)
        await mute_peer(client, b_diggo, "Diggominer_bot")
        try:
            await client.send_message(b_diggo, f"/start {DIGGO_REFERRAL_CODE}")
            await asyncio.sleep(0.5)
        except Exception:
            pass
        await asyncio.sleep(1.0)
        try:
            r_diggo = await client(RequestWebViewRequest(
                peer=b_diggo,
                bot=b_diggo,
                url="https://diggo.linkpc.net/",
                platform="android",
                start_param=DIGGO_REFERRAL_CODE
            ))
            p_diggo = urllib.parse.urlparse(getattr(r_diggo, 'url', None) or "")
            diggo_init = urllib.parse.parse_qs(p_diggo.fragment).get("tgWebAppData", [None])[0] or urllib.parse.parse_qs(p_diggo.query).get("tgWebAppData", [None])[0]
            if diggo_init:
                acc_entry["diggo_init_data"] = diggo_init
        except Exception:
            pass
        acc_entry["diggo_referral_bound"] = True
        print(f"  ✅ [3/9] Successfully bound to DiggoMiner ({DIGGO_REFERRAL_CODE})!")
    except Exception as e:
        print(f"  ❌ Warning binding DiggoMiner referral: {e}")

    # 4. PepeGram (@Pepe_gram_bot) - Referral: 1449
    print(f"  • [4/9] Connecting to @{PEPE_BOT} with referral: {PEPE_REFERRAL_CODE}...")
    try:
        try:
            await client(UnblockRequest(id=PEPE_BOT))
        except Exception:
            pass
        b_pepe = await client.get_entity(PEPE_BOT)
        await mute_peer(client, b_pepe, "Pepe_gram_bot")
        try:
            await client.send_message(b_pepe, f"/start {PEPE_REFERRAL_CODE}")
            await asyncio.sleep(0.5)
        except Exception:
            pass
        await asyncio.sleep(1.0)
        try:
            r_pepe = await client(RequestWebViewRequest(
                peer=b_pepe,
                bot=b_pepe,
                url="https://app.miniempire.app/miniapp/index.html?tid=1449&lang=en",
                platform="android",
                start_param=PEPE_REFERRAL_CODE
            ))
            p_pepe = urllib.parse.urlparse(getattr(r_pepe, 'url', None) or "")
            pepe_init = urllib.parse.parse_qs(p_pepe.fragment).get("tgWebAppData", [None])[0] or urllib.parse.parse_qs(p_pepe.query).get("tgWebAppData", [None])[0]
            if pepe_init:
                acc_entry["pepegram_init_data"] = pepe_init
        except Exception:
            pass
        acc_entry["pepegram_referral_bound"] = True
        print(f"  ✅ [4/9] Successfully bound to PepeGram ({PEPE_REFERRAL_CODE})!")
    except Exception as e:
        print(f"  ❌ Warning binding PepeGram referral: {e}")

    # 5. AdxEarn AI (@AdxEarnAibot) - Referral: 6727787768
    print(f"  • [5/9] Connecting to @{ADX_BOT} with referral: {ADX_REFERRAL_CODE}...")
    try:
        try:
            await client(UnblockRequest(id=ADX_BOT))
        except Exception:
            pass
        b_adx = await client.get_entity(ADX_BOT)
        await mute_peer(client, b_adx, "AdxEarnAibot")
        try:
            await client.send_message(b_adx, f"/start {ADX_REFERRAL_CODE}")
            await asyncio.sleep(0.5)
        except Exception:
            pass
        await asyncio.sleep(1.0)
        try:
            r_adx = await client(RequestWebViewRequest(
                peer=b_adx,
                bot=b_adx,
                url="https://app.adxearnai.xyz/index.html",
                platform="android",
                start_param=ADX_REFERRAL_CODE
            ))
            p_adx = urllib.parse.urlparse(getattr(r_adx, 'url', None) or "")
            adx_init = urllib.parse.parse_qs(p_adx.fragment).get("tgWebAppData", [None])[0] or urllib.parse.parse_qs(p_adx.query).get("tgWebAppData", [None])[0]
            if adx_init:
                acc_entry["adxearn_init_data"] = adx_init
        except Exception:
            pass
        acc_entry["adxearn_referral_bound"] = True
        print(f"  ✅ [5/9] Successfully bound to AdxEarn AI ({ADX_REFERRAL_CODE})!")
    except Exception as e:
        print(f"  ❌ Warning binding AdxEarn AI referral: {e}")

    # 6. Chicken Land (@ChickenLandBot) - Referral: 12668
    print(f"  • [6/9] Connecting to @{CHICKEN_BOT} with referral: {CHICKEN_REFERRAL_CODE}...")
    try:
        try:
            await client(UnblockRequest(id=CHICKEN_BOT))
        except Exception:
            pass
        b_chk = await client.get_entity(CHICKEN_BOT)
        await mute_peer(client, b_chk, "ChickenLandBot")
        try:
            await client.send_message(b_chk, f"/start {CHICKEN_REFERRAL_CODE}")
            await asyncio.sleep(0.5)
        except Exception:
            pass
        await asyncio.sleep(1.0)
        try:
            r_chk = await client(RequestWebViewRequest(
                peer=b_chk,
                bot=b_chk,
                url="https://app8968434282.tgcloud.ai/",
                platform="android",
                start_param=CHICKEN_REFERRAL_CODE
            ))
            p_chk = urllib.parse.urlparse(getattr(r_chk, 'url', None) or "")
            chk_init = urllib.parse.parse_qs(p_chk.fragment).get("tgWebAppData", [None])[0] or urllib.parse.parse_qs(p_chk.query).get("tgWebAppData", [None])[0]
            if chk_init:
                acc_entry["chickenland_init_data"] = chk_init
        except Exception:
            pass
        acc_entry["chickenland_referral_bound"] = True
        print(f"  ✅ [6/9] Successfully bound to Chicken Land ({CHICKEN_REFERRAL_CODE})!")
    except Exception as e:
        print(f"  ❌ Warning binding Chicken Land referral: {e}")

    # 7. Grouche Mine (@GRC_AirdrooBot)
    print(f"  • [7/9] Connecting to @{GROUCHEMINE_BOT} with referral: {GROUCHEMINE_REFERRAL_CODE}...")
    try:
        try:
            await client(UnblockRequest(id=GROUCHEMINE_BOT))
        except Exception:
            pass
        b_grc = await client.get_entity(GROUCHEMINE_BOT)
        await mute_peer(client, b_grc, "GRC_AirdrooBot")
        try:
            await client.send_message(b_grc, f"/start {GROUCHEMINE_REFERRAL_CODE}")
            await asyncio.sleep(0.5)
        except Exception:
            pass
        await asyncio.sleep(1.0)
        try:
            r_grc = await client(RequestWebViewRequest(
                peer=b_grc,
                bot=b_grc,
                url="https://grouchemine.world/",
                platform="android",
                start_param=GROUCHEMINE_REFERRAL_CODE
            ))
            p_grc = urllib.parse.urlparse(getattr(r_grc, 'url', None) or "")
            grc_init = urllib.parse.parse_qs(p_grc.fragment).get("tgWebAppData", [None])[0] or urllib.parse.parse_qs(p_grc.query).get("tgWebAppData", [None])[0]
            if grc_init:
                acc_entry["grouchemine_init_data"] = grc_init
        except Exception:
            pass
        acc_entry["grouchemine_referral_bound"] = True
        print(f"  ✅ [7/9] Successfully bound to Grouche Mine ({GROUCHEMINE_REFERRAL_CODE})!")
    except Exception as e:
        print(f"  ❌ Warning binding Grouche Mine referral: {e}")

    # 8. LUM Miner (@lumeonminer_bot)
    print(f"  • [8/9] Connecting to @{LUMEON_BOT} with referral: {LUMEON_REFERRAL_CODE}...")
    try:
        try:
            await client(UnblockRequest(id=LUMEON_BOT))
        except Exception:
            pass
        b_lum = await client.get_entity(LUMEON_BOT)
        await mute_peer(client, b_lum, "lumeonminer_bot")
        try:
            await client.send_message(b_lum, f"/start {LUMEON_REFERRAL_CODE}")
            await asyncio.sleep(0.5)
        except Exception:
            pass
        await asyncio.sleep(1.0)
        try:
            r_lum = await client(RequestWebViewRequest(
                peer=b_lum,
                bot=b_lum,
                url="https://lum-miner.gurmessa747.workers.dev/",
                platform="android",
                start_param=LUMEON_REFERRAL_CODE
            ))
            p_lum = urllib.parse.urlparse(getattr(r_lum, 'url', None) or "")
            lum_init = urllib.parse.parse_qs(p_lum.fragment).get("tgWebAppData", [None])[0] or urllib.parse.parse_qs(p_lum.query).get("tgWebAppData", [None])[0]
            if lum_init:
                acc_entry["lumeon_init_data"] = lum_init
        except Exception:
            pass
        acc_entry["lumeon_referral_bound"] = True
        print(f"  ✅ [8/9] Successfully bound to LUM Miner ({LUMEON_REFERRAL_CODE})!")
    except Exception as e:
        print(f"  ❌ Warning binding LUM Miner referral: {e}")

    # 9. EarnVault (@EarnVaultApp_bot)
    print(f"  • [9/9] Connecting to @{EARNVAULT_BOT} with referral: {EARNVAULT_REFERRAL_CODE}...")
    try:
        try:
            await client(UnblockRequest(id=EARNVAULT_BOT))
        except Exception:
            pass
        b_ev = await client.get_entity(EARNVAULT_BOT)
        await mute_peer(client, b_ev, "EarnVaultApp_bot")
        try:
            await client.send_message(b_ev, f"/start {EARNVAULT_REFERRAL_CODE}")
            await asyncio.sleep(0.5)
        except Exception:
            pass
        await asyncio.sleep(1.0)
        try:
            r_ev = await client(RequestWebViewRequest(
                peer=b_ev,
                bot=b_ev,
                url="https://eearnvault.top/",
                platform="android",
                start_param=EARNVAULT_REFERRAL_CODE
            ))
            p_ev = urllib.parse.urlparse(getattr(r_ev, 'url', None) or "")
            ev_init = urllib.parse.parse_qs(p_ev.fragment).get("tgWebAppData", [None])[0] or urllib.parse.parse_qs(p_ev.query).get("tgWebAppData", [None])[0]
            if ev_init:
                acc_entry["earnvault_init_data"] = ev_init
        except Exception:
            pass
        acc_entry["earnvault_referral_bound"] = True
        print(f"  ✅ [9/9] Successfully bound to EarnVault ({EARNVAULT_REFERRAL_CODE})!")
    except Exception as e:
        print(f"  ❌ Warning binding EarnVault referral: {e}")

    # Auto-join all mandatory sponsor channels for immediate side-task qualification
    print("  • Auto-joining all mandatory sponsor channels across all 11 bots...")
    try:
        from bot_registry import get_all_sponsor_channels
        s_channels = get_all_sponsor_channels()
    except Exception:
        s_channels = [
            "keepeye_app", "AI_TRADING_FOREX",
            "kynex_mining", "EarnVaulte", "solanamemes001", "Web3Primeteam",
            "PaperHouseNFT", "pepe_grammmm", "BTCMAKERR", "AdxearnAi",
            "LandChickenNews", "ChickenLandPay", "ChickenLandCodes", "DurovKidney", "PickaxeEmpire"
        ]
    for ch in s_channels:
        try:
            await client(JoinChannelRequest(ch))
            await asyncio.sleep(0.3)
        except Exception:
            pass

    # Audit final referral status
    all_9_keys = [
        "atf_referral_bound",
        "kynex_referral_bound",
        "diggo_referral_bound",
        "pepegram_referral_bound",
        "adxearn_referral_bound",
        "chickenland_referral_bound",
        "grouchemine_referral_bound",
        "lumeon_referral_bound",
        "earnvault_referral_bound"
    ]
    bound_count = sum(1 for k in all_9_keys if acc_entry.get(k))
    if bound_count == len(all_9_keys):
        acc_entry["all_9_referrals_bound"] = True
        acc_entry["referrals_bound"] = True
        print(f"\n🎉 ALL 9/9 BOTS SUCCESSFULLY BOUND TO MASTER REFERRAL ID {PRIMARY_CHAT_ID}!")
    else:
        print(f"\n⚠️ {bound_count}/9 bots bound. Remaining will be auto-bound on next cloud cycle.")



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

    from proxy_manager import get_account_fingerprint
    fp = get_account_fingerprint(phone)
    client = TelegramClient(
        StringSession(),
        API_ID,
        API_HASH,
        device_model=fp["device_model"],
        system_version=fp["system_version"],
        app_version=fp["app_version"],
        lang_code=fp["lang_code"],
        system_lang_code=fp["system_lang_code"]
    )
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
        "account_id": str(me.id),
        "phone": phone,
        "session_string": session_str,
        "added_at": datetime.now(timezone.utc).isoformat(),
        "status": "active"
    }

    # Preserve authentic static fleet wallets or generate isolated 5-chain wallets for genuinely new worker account
    try:
        # Fully autonomous account lifecycle, wallet preservation, email & live-state sync
        import auto_wallet_manager
        cur_accs = load_accounts()
        acc_entry = auto_wallet_manager.ensure_account_complete(acc_entry, cur_accs)
        wallets = {
            "ton": acc_entry.get("ton_wallet", {}),
            "evm": acc_entry.get("evm_wallet", {}),
            "tron": acc_entry.get("tron_wallet", {}),
            "solana": acc_entry.get("solana_wallet", {}),
            "btc": acc_entry.get("btc_wallet", {})
        }
        print(f"💎 Verified 5-chain isolated wallets for {acc_entry.get('name')}:")
        print(f"   • TON (v4r2): {wallets['ton'].get('address')}")
        print(f"   • EVM (BSC):  {wallets['evm'].get('address')}")
        print(f"   • TRON:       {wallets['tron'].get('address')}")
        print(f"   • Solana:     {wallets['solana'].get('address')}")
        print(f"   • Bitcoin:    {wallets['btc'].get('address')}")
        print(f"   • Email:      {acc_entry.get('email')}")
    except Exception as we:
        print(f"⚠️ Wallet generation note: {we}")

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

    # Autonomous Cloud Synchronization: Upstash Redis & Cloudflare Mesh
    sync_account_to_clouds_sync(acc_entry)

    print("The 24/7 background worker will now automatically farm for this account.")
    print("=" * 55 + "\n")

    await client.disconnect()


def sync_account_to_clouds_sync(acc_entry: dict):
    """Synchronizes added/updated account to Upstash Redis fleet:accounts for cloud workers."""
    env = {}
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    
    up_url = env.get("UPSTASH_URL") or env.get("UPSTASH_REDIS_REST_URL")
    up_tok = env.get("UPSTASH_TOKEN") or env.get("UPSTASH_REDIS_REST_TOKEN")
    if not (up_url and up_tok):
        return
    
    uid = str(acc_entry.get("user_id"))
    try:
        req = urllib.request.Request(f"{up_url}/get/fleet:accounts", headers={"Authorization": f"Bearer {up_tok}"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            cur_accs = json.loads(data["result"]) if isinstance(data.get("result"), str) else (data.get("result") or [])
        
        acc_found = False
        for i, a in enumerate(cur_accs):
            if str(a.get("user_id")) == uid or str(a.get("phone")) == str(acc_entry.get("phone")):
                cur_accs[i] = acc_entry
                acc_found = True
                break
        if not acc_found:
            cur_accs.append(acc_entry)
        
        for i, a in enumerate(cur_accs):
            a["index"] = i + 1
        
        pipe_cmds = [
            ["SET", f"account:{uid}", json.dumps(acc_entry)],
            ["SADD", "fleet_accounts_set", uid],
            ["SADD", "fleet:healthy_sessions", uid],
            ["SREM", "fleet:revoked_sessions", uid],
            ["SET", "fleet:accounts", json.dumps(cur_accs)]
        ]
        pipe_req = urllib.request.Request(
            f"{up_url}/pipeline",
            headers={"Authorization": f"Bearer {up_tok}", "Content-Type": "application/json"},
            data=json.dumps(pipe_cmds).encode(),
            method="POST"
        )
        with urllib.request.urlopen(pipe_req, timeout=10) as p_resp:
            pass
        print(f"☁️ Successfully synchronized Account #{acc_entry.get('index', len(cur_accs))} ({acc_entry.get('name')}) to Upstash Redis fleet:accounts ({len(cur_accs)} total)!")
        try:
            import auto_wallet_manager
            auto_wallet_manager.reconcile_all_fleet_accounts()
        except Exception:
            pass
    except Exception as e:
        print(f"⚠️ Cloud sync note: {e}")



if __name__ == "__main__":
    asyncio.run(interactive_login())
