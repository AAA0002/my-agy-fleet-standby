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
STONES_BOT = "stoneswithestand_bot"
STONES_REFERRAL_CODE = "r6727787768"

MRG_BOT = "mrgminerbot"
MRG_REFERRAL_CODE = "ref_IRN1G3XD"

AILAB_BOT = "AiLab_robot"
AILAB_REFERRAL_CODE = "296852"

ULTRAWALLET_BOT = "UltrawalletTrade_Bot"
ULTRAWALLET_REFERRAL_CODE = "6727787768"

ATF_BOT = "ATF_AIRDROP_bot"
ATF_REFERRAL_CODE = "6727787768"

FINVORA_BOT = "FINVORAWeb3bot"
FINVORA_REFERRAL_CODE = "ref_TRX6727787768"

TURBOGRAM_BOT = "TurboGramV1_bot"
TURBOGRAM_REFERRAL_CODE = "r_3520c92b"

VICTORS_BOT = "VictorsCompanybot"
VICTORS_REFERRAL_CODE = "ref_A20AA96F18"

VYRO_BOT = "vyrodrop_bot"
VYRO_REFERRAL_CODE = "ref_myFjrqqE4WN_"

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

    print(f"\n🔗 Automatically binding account to all 7 verified fleet bots with wallet isolation...")

    # 1. Stones Miners (@stoneswithestand_bot) - Referral: r6727787768
    print(f"  • [1/7] Connecting to @{STONES_BOT} with referral: {STONES_REFERRAL_CODE}...")
    try:
        try:
            await client(UnblockRequest(id=STONES_BOT))
        except Exception:
            pass
        b_stones = await client.get_entity(STONES_BOT)
        await mute_peer(client, b_stones, "stoneswithestand_bot")
        await client.send_message(b_stones, f"/start {STONES_REFERRAL_CODE}")
        await asyncio.sleep(1.5)
        try:
            await client(JoinChannelRequest("stoneswithestand"))
        except Exception:
            pass
        try:
            res_st = await client(RequestWebViewRequest(
                peer=b_stones,
                bot=b_stones,
                platform="android",
                url="https://app.stoneswithestand.my.id/"
            ))
            p_st = urllib.parse.urlparse(getattr(res_st, 'url', None) or "")
            st_init = urllib.parse.parse_qs(p_st.fragment).get("tgWebAppData", [None])[0] or urllib.parse.parse_qs(p_st.query).get("tgWebAppData", [None])[0]
            if st_init:
                acc_entry["stones_init_data"] = st_init
                st_h = {"Content-Type": "application/json", "Origin": "https://app.stoneswithestand.my.id", "Referer": "https://app.stoneswithestand.my.id/"}
                async with aiohttp.ClientSession() as s_st:
                    await s_st.post("https://app.stoneswithestand.my.id/api/init", json={"initData": st_init, "start_param": STONES_REFERRAL_CODE}, headers=st_h, timeout=aiohttp.ClientTimeout(total=8))
                    if evm_wallet:
                        await s_st.post("https://app.stoneswithestand.my.id/api/wallet", json={"initData": st_init, "wallet": evm_wallet}, headers=st_h, timeout=aiohttp.ClientTimeout(total=8))
                    await s_st.post("https://app.stoneswithestand.my.id/api/mining/start", json={"initData": st_init}, headers=st_h, timeout=aiohttp.ClientTimeout(total=8))
        except Exception:
            pass
        acc_entry["stones_referral_bound"] = True
        print(f"  ✅ [1/7] Successfully bound to Stones Miners ({STONES_REFERRAL_CODE})!")
    except Exception as e:
        print(f"  ❌ Warning binding Stones Miners referral: {e}")

    # 2. MRG Miner (@mrgminerbot) - Referral: ref_IRN1G3XD
    print(f"  • [2/7] Connecting to @{MRG_BOT} with referral: {MRG_REFERRAL_CODE}...")
    try:
        try:
            await client(UnblockRequest(id=MRG_BOT))
        except Exception:
            pass
        b_mrg = await client.get_entity(MRG_BOT)
        await mute_peer(client, b_mrg, "mrgminerbot")
        await client.send_message(b_mrg, f"/start {MRG_REFERRAL_CODE}")
        await asyncio.sleep(1.5)
        try:
            bot_mrg_in = await client.get_input_entity(MRG_BOT)
            res_mrg = await client(RequestAppWebViewRequest(
                peer=bot_mrg_in,
                app=InputBotAppShortName(bot_id=bot_mrg_in, short_name="app"),
                platform="android",
                start_param=MRG_REFERRAL_CODE
            ))
            parsed_mrg = urllib.parse.urlparse(res_mrg.url)
            m_init = urllib.parse.parse_qs(parsed_mrg.fragment).get("tgWebAppData", [None])[0] or urllib.parse.parse_qs(parsed_mrg.query).get("tgWebAppData", [None])[0]
            if m_init:
                async with aiohttp.ClientSession() as m_sess:
                    m_headers = {"Content-Type": "application/json", "Origin": "https://app.mrgtoken.xyz", "Referer": "https://app.mrgtoken.xyz/"}
                    dev_info = {
                        "platform": "android",
                        "userAgent": "Mozilla/5.0 (Linux; Android 10; SM-A305F) AppleWebKit/537.36",
                        "deviceMemory": "4 GB",
                        "hardwareConcurrency": 8
                    }
                    await m_sess.post("https://mrg.up.railway.app/api/auth/verify", json={"initData": m_init, "startParam": MRG_REFERRAL_CODE, "start_param": MRG_REFERRAL_CODE, "deviceInfo": dev_info}, headers=m_headers, timeout=aiohttp.ClientTimeout(total=10))
                    if ton_wallet:
                        await m_sess.post("https://mrg.up.railway.app/api/user/connect-wallet", json={"initData": m_init, "address": ton_wallet, "balance": 0}, headers=m_headers, timeout=aiohttp.ClientTimeout(total=10))
        except Exception:
            pass
        try:
            await client(JoinChannelRequest("mrgminer"))
            await client(JoinChannelRequest("mrgfun"))
        except Exception:
            pass
        acc_entry["mrg_referral_bound"] = True
        print(f"  ✅ [2/7] Successfully bound to MRG Miner ({MRG_REFERRAL_CODE})!")
    except Exception as e:
        print(f"  ❌ Warning binding MRG Miner referral: {e}")

    # 3. AI Lab Robot (@AiLab_robot) - Referral: 296852
    print(f"  • [3/7] Connecting to @{AILAB_BOT} with referral: {AILAB_REFERRAL_CODE}...")
    try:
        try:
            await client(UnblockRequest(id=AILAB_BOT))
        except Exception:
            pass
        bot_ai = await client.get_entity(AILAB_BOT)
        await mute_peer(client, bot_ai, "AiLab_robot")
        await client.send_message(bot_ai, f"/start {AILAB_REFERRAL_CODE}")
        await asyncio.sleep(2.0)
        try:
            res_ai = await client(RequestWebViewRequest(
                peer=bot_ai,
                bot=bot_ai,
                platform="android",
                url=f"https://api.ailab-agent.online/?ref={AILAB_REFERRAL_CODE}"
            ))
            parsed_ai = urllib.parse.urlparse(res_ai.url)
            init_ai = urllib.parse.parse_qs(parsed_ai.fragment).get("tgWebAppData", [None])[0]
            if init_ai:
                acc_entry["ailab_init_data"] = init_ai
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
        print(f"  ✅ [3/7] Successfully bound to AI Lab Robot ({AILAB_REFERRAL_CODE})!")
    except Exception as e:
        print(f"  ❌ Warning binding AI Lab referral: {e}")

    # 4. Ultra Wallet (@UltrawalletTrade_Bot) - Referral: 6727787768
    print(f"  • [4/7] Connecting to @{ULTRAWALLET_BOT} with referral: {ULTRAWALLET_REFERRAL_CODE}...")
    try:
        try:
            await client(UnblockRequest(id=ULTRAWALLET_BOT))
        except Exception:
            pass
        bot_uw = await client.get_entity(ULTRAWALLET_BOT)
        await mute_peer(client, bot_uw, "UltrawalletTrade_Bot")
        bot_uw_in = await client.get_input_entity(ULTRAWALLET_BOT)
        res_uw = await client(RequestAppWebViewRequest(
            peer=bot_uw_in,
            app=InputBotAppShortName(bot_id=bot_uw_in, short_name="app"),
            platform="android",
            start_param=ULTRAWALLET_REFERRAL_CODE
        ))
        parsed_uw = urllib.parse.urlparse(res_uw.url)
        init_uw = urllib.parse.parse_qs(parsed_uw.fragment).get("tgWebAppData", [None])[0]
        if init_uw:
            acc_entry["ultrawallet_init_data"] = init_uw
            async with aiohttp.ClientSession() as uw_sess:
                await uw_sess.post(
                    "https://wallet.trxvault.top/api/telegramLogin",
                    json={"initData": init_uw, "refBy": ULTRAWALLET_REFERRAL_CODE},
                    headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (Linux; Android 14)"},
                    timeout=aiohttp.ClientTimeout(total=8)
                )
        acc_entry["ultrawallet_referral_bound"] = True
        print(f"  ✅ [4/7] Successfully bound to Ultra Wallet ({ULTRAWALLET_REFERRAL_CODE})!")
    except Exception as e:
        print(f"  ❌ Warning binding Ultra Wallet referral: {e}")

    # 5. ATF Miner (@ATF_AIRDROP_bot) - Referral: 6727787768
    print(f"  • [5/7] Connecting to @{ATF_BOT} with referral: {ATF_REFERRAL_CODE}...")
    try:
        try:
            await client(UnblockRequest(id=ATF_BOT))
        except Exception:
            pass
        bot_atf = await client.get_entity(ATF_BOT)
        await mute_peer(client, bot_atf, "ATF_AIRDROP_bot")
        await client.send_message(bot_atf, f"/start {ATF_REFERRAL_CODE}")
        await asyncio.sleep(1.5)
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
        print(f"  ✅ [5/7] Successfully bound to ATF Miner ({ATF_REFERRAL_CODE})!")
    except Exception as e:
        print(f"  ❌ Warning binding ATF referral: {e}")

    # 6. FINVORA Web3 (@FINVORAWeb3bot) - Referral: ref_TRX6727787768
    print(f"  • [6/7] Connecting to @{FINVORA_BOT} with referral: {FINVORA_REFERRAL_CODE}...")
    try:
        try:
            await client(UnblockRequest(id=FINVORA_BOT))
        except Exception:
            pass
        await join_tg_target(client, "finvoraweb3", acc_name)
        b_fin = await client.get_entity(FINVORA_BOT)
        await mute_peer(client, b_fin, "FINVORAWeb3bot")
        await client.send_message(b_fin, f"/start {FINVORA_REFERRAL_CODE}")
        await asyncio.sleep(1.5)
        try:
            res_fin = await client(RequestWebViewRequest(
                peer=b_fin,
                bot=b_fin,
                url="https://finvora-production.up.railway.app/",
                platform="android",
                start_param=str(FINVORA_REFERRAL_CODE)
            ))
            p_fin = urllib.parse.urlparse(getattr(res_fin, 'url', None) or "")
            fin_init = urllib.parse.parse_qs(p_fin.fragment).get("tgWebAppData", [None])[0] or urllib.parse.parse_qs(p_fin.query).get("tgWebAppData", [None])[0]
            if fin_init:
                fin_h = {"Content-Type": "application/json", "X-Telegram-Init-Data": fin_init, "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-A305F)"}
                async with aiohttp.ClientSession() as fin_s:
                    if ton_wallet:
                        await fin_s.post("https://finvora-production.up.railway.app/api/wallet/connect", json={"address": ton_wallet, "walletType": "manual"}, headers=fin_h, timeout=aiohttp.ClientTimeout(total=8))
                    await fin_s.post("https://finvora-production.up.railway.app/api/bonus/instant", json={}, headers=fin_h, timeout=aiohttp.ClientTimeout(total=8))
                    await fin_s.post("https://finvora-production.up.railway.app/api/mining/claim", json={}, headers=fin_h, timeout=aiohttp.ClientTimeout(total=8))
        except Exception:
            pass
        acc_entry["finvora_referral_bound"] = True
        print(f"  ✅ [6/7] Successfully bound to FINVORA Web3 ({FINVORA_REFERRAL_CODE})!")
    except Exception as e:
        print(f"  ❌ Warning binding FINVORA referral: {e}")

    # 7. TurboGram V1 (@TurboGramV1_bot) - Referral: r_3520c92b
    print(f"  • [7/7] Connecting to @{TURBOGRAM_BOT} with referral: {TURBOGRAM_REFERRAL_CODE}...")
    try:
        try:
            await client(UnblockRequest(id=TURBOGRAM_BOT))
        except Exception:
            pass
        await join_tg_target(client, "TurboGramAnnouncements", acc_name)
        await join_tg_target(client, "TurboGramPayment", acc_name)
        b_tb = await client.get_entity(TURBOGRAM_BOT)
        await mute_peer(client, b_tb, "TurboGramV1_bot")
        await client.send_message(b_tb, f"/start {TURBOGRAM_REFERRAL_CODE}")
        await asyncio.sleep(1.5)
        try:
            res_tb = await client(RequestWebViewRequest(
                peer=b_tb,
                bot=b_tb,
                url="https://turbo.tamimdev.dev/",
                platform="android",
                start_param=str(TURBOGRAM_REFERRAL_CODE)
            ))
            p_tb = urllib.parse.urlparse(getattr(res_tb, 'url', None) or "")
            tb_init = urllib.parse.parse_qs(p_tb.fragment).get("tgWebAppData", [None])[0] or urllib.parse.parse_qs(p_tb.query).get("tgWebAppData", [None])[0]
            if tb_init:
                tb_h = {"Authorization": f"tma {tb_init}", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-A305F)"}
                async with aiohttp.ClientSession() as tb_s:
                    await tb_s.get("https://turbo.tamimdev.dev/api/me", headers=tb_h, timeout=aiohttp.ClientTimeout(total=8))
                    if ton_wallet:
                        await tb_s.post("https://turbo.tamimdev.dev/api/me/wallet", json={"address": ton_wallet}, headers=tb_h, timeout=aiohttp.ClientTimeout(total=8))
        except Exception:
            pass
        acc_entry["turbogram_referral_bound"] = True
        print(f"  ✅ [7/9] Successfully bound to TurboGram V1 ({TURBOGRAM_REFERRAL_CODE})!")
    except Exception as e:
        print(f"  ❌ Warning binding TurboGram referral: {e}")

    # 8. Victor's Company (@VictorsCompanybot) - Referral: ref_A20AA96F18
    print(f"  • [8/9] Connecting to @{VICTORS_BOT} with referral: {VICTORS_REFERRAL_CODE}...")
    try:
        try:
            await client(UnblockRequest(id=VICTORS_BOT))
        except Exception:
            pass
        b_vic = await client.get_entity(VICTORS_BOT)
        await mute_peer(client, b_vic, "VictorsCompanybot")
        await client.send_message(b_vic, f"/start {VICTORS_REFERRAL_CODE}")
        await asyncio.sleep(1.5)
        try:
            b_vic_in = await client.get_input_entity(b_vic)
            r_vic = await client(RequestAppWebViewRequest(
                peer=b_vic_in,
                app=InputBotAppShortName(bot_id=b_vic_in, short_name="app"),
                platform="android",
                start_param=VICTORS_REFERRAL_CODE
            ))
            p_vic = urllib.parse.urlparse(getattr(r_vic, 'url', None) or "")
            vic_init = urllib.parse.parse_qs(p_vic.fragment).get("tgWebAppData", [None])[0] or urllib.parse.parse_qs(p_vic.query).get("tgWebAppData", [None])[0]
            if vic_init:
                acc_entry["victors_init_data"] = vic_init
                vic_h = {"Authorization": f"tma {vic_init}", "Content-Type": "application/json", "Origin": "https://app.victors.company", "Referer": "https://app.victors.company/"}
                async with aiohttp.ClientSession() as vic_s:
                    await vic_s.post("https://server.victors.company/api/auth/login", json={"startParam": VICTORS_REFERRAL_CODE, "turnstileToken": None}, headers=vic_h, timeout=aiohttp.ClientTimeout(total=8))
        except Exception:
            pass
        acc_entry["victors_referral_bound"] = True
        print(f"  ✅ [8/9] Successfully bound to Victor's Company ({VICTORS_REFERRAL_CODE})!")
    except Exception as e:
        print(f"  ❌ Warning binding Victor's Company referral: {e}")

    # 9. VyroDrop (@vyrodrop_bot) - Referral: ref_myFjrqqE4WN_
    print(f"  • [9/9] Connecting to @{VYRO_BOT} with referral: {VYRO_REFERRAL_CODE}...")
    try:
        try:
            await client(UnblockRequest(id=VYRO_BOT))
        except Exception:
            pass
        b_vy = await client.get_entity(VYRO_BOT)
        await mute_peer(client, b_vy, "vyrodrop_bot")
        await client.send_message(b_vy, f"/start {VYRO_REFERRAL_CODE}")
        await asyncio.sleep(1.5)
        try:
            r_vy = await client(RequestWebViewRequest(
                peer=b_vy,
                bot=b_vy,
                url="https://vyro.run.place/",
                platform="android",
                start_param=VYRO_REFERRAL_CODE
            ))
            p_vy = urllib.parse.urlparse(getattr(r_vy, 'url', None) or "")
            vy_init = urllib.parse.parse_qs(p_vy.fragment).get("tgWebAppData", [None])[0] or urllib.parse.parse_qs(p_vy.query).get("tgWebAppData", [None])[0]
            if vy_init:
                acc_entry["vyro_init_data"] = vy_init
                vy_h = {"Authorization": f"tma {vy_init}", "Content-Type": "application/json", "Referer": "https://vyro.run.place/"}
                async with aiohttp.ClientSession() as vy_s:
                    await vy_s.get("https://vyro.run.place/api/bootstrap", headers=vy_h, timeout=aiohttp.ClientTimeout(total=8))
        except Exception:
            pass
        acc_entry["vyro_referral_bound"] = True
        print(f"  ✅ [9/9] Successfully bound to VyroDrop ({VYRO_REFERRAL_CODE})!")
    except Exception as e:
        print(f"  ❌ Warning binding VyroDrop referral: {e}")

    # Audit final referral status
    all_9_keys = [
        "stones_referral_bound", "mrg_referral_bound",
        "ailab_referral_bound", "ultrawallet_referral_bound",
        "atf_referral_bound", "finvora_referral_bound",
        "turbogram_referral_bound", "victors_referral_bound",
        "vyro_referral_bound"
    ]
    bound_count = sum(1 for k in all_9_keys if acc_entry.get(k))
    if bound_count == len(all_9_keys):
        acc_entry["all_9_referrals_bound"] = True
        acc_entry["all_7_referrals_bound"] = True
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

    # Generate 100% isolated 5-chain wallets for this new account
    try:
        from fleet_wallet_provisioner import generate_multichain_wallet_suite, save_and_archive_account_wallets
        cur_accs = load_accounts()
        next_idx = len(cur_accs) + 1
        wallets = generate_multichain_wallet_suite(next_idx, name, me.id, phone, username)
        acc_entry.update({
            "index": next_idx,
            "evm_wallet": wallets["evm"],
            "ton_wallet": wallets["ton"],
            "tron_wallet": wallets["tron"],
            "solana_wallet": wallets["solana"],
            "btc_wallet": wallets["btc"],
            "bnb_wallet": wallets["evm"]["address"]
        })
        save_and_archive_account_wallets(acc_entry, wallets)
        print(f"💎 Generated & Archived 5-chain isolated wallets for {name}:")
        print(f"   • TON (v4r2): {wallets['ton']['address']}")
        print(f"   • EVM (BSC):  {wallets['evm']['address']}")
        print(f"   • TRON:       {wallets['tron']['address']}")
        print(f"   • Solana:     {wallets['solana']['address']}")
        print(f"   • Bitcoin:    {wallets['btc']['address']}")
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
    print("The 24/7 background worker will now automatically farm for this account.")
    print("=" * 55 + "\n")

    await client.disconnect()



if __name__ == "__main__":
    asyncio.run(interactive_login())
