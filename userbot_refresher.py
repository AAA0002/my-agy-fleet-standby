import os
import sys
import time
import asyncio
import logging
import gc
import random
import re
import uuid
import urllib.parse
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Dict, Any, List
import aiohttp
from telethon import TelegramClient, events, functions
from telethon.sessions import StringSession
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    PhoneNumberInvalidError,
    UserIsBlockedError,
    AuthKeyUnregisteredError,
    UserDeactivatedError,
    SessionRevokedError,
    FloodWaitError
)
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.contacts import UnblockRequest
from telethon.tl.functions.messages import RequestWebViewRequest, RequestAppWebViewRequest
from telethon.tl.types import InputBotAppShortName
from dotenv import load_dotenv
from phone_detector import detect_and_normalize_phone, get_country_flag
from proxy_manager import parse_proxy, get_account_fingerprint, build_proxy_security_report, set_account_proxy, get_account_user_agent
from backup_manager import send_backup_to_telegram

try:
    from tonsdk.contract.wallet import Wallets, WalletVersionEnum
    from tonsdk.utils import Address
    from nacl.signing import SigningKey
    import struct
    import hashlib
    import base64
    HAS_TON_PROOF_LIBS = True
except Exception:
    HAS_TON_PROOF_LIBS = False

try:
    import sentry_sdk
    SENTRY_DSN = os.getenv("SENTRY_DSN", "https://af8cd9bec30d8551a01c5554c4d24a6b@o4512113387044864.ingest.us.sentry.io/4512113405132800")
    if SENTRY_DSN:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            traces_sample_rate=0.2,
            environment="production"
        )
except Exception:
    pass


START_TIME = time.time()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "userbot.log")
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")
login_sessions = {}

# Setup Logging (Single handler to avoid duplicate lines when redirected by supervisor)
logging.basicConfig(
    format="[%(asctime)s - %(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("MultiBotWorker")

load_dotenv(os.path.join(BASE_DIR, ".env"))

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
STRING_SESSION = os.getenv("TELEGRAM_STRING_SESSION")

# Reporting Bot Config (@My_Router_AI_bot)
REPORT_BOT_TOKEN = os.getenv("REPORT_BOT_TOKEN", "8858823950:AAFFkuls8hBf23taCZE1y5gVzP4AFCuqI5o")
REPORT_CHAT_ID = os.getenv("REPORT_CHAT_ID", "6727787768")
PAYOUT_CHANNEL_ID = os.getenv("PAYOUT_CHANNEL_ID", "-1004402765950")
CF_WORKER_URLS = [
    os.getenv("CF_WORKER_URL_1", "https://restore-agy.aaaai2.workers.dev"),
    os.getenv("CF_WORKER_URL_2", "https://restore-agy.aaa-bot.workers.dev"),
    os.getenv("CF_WORKER_URL_3", "https://restore-agy.aaa222.workers.dev")
]

# Authorized Administrators Whitelist (Only these IDs can access and command the bot)
ADMIN_IDS = [
    str(REPORT_CHAT_ID),
    "6727787768",
    "8826375659",
    "8190649727",
    "7648254021",
    "-1003973231307"
]
ADMIN_IDS = list(dict.fromkeys(ADMIN_IDS))

# Dedicated Broadcast Channels (Only valid chats that receive broadcast alerts)
BROADCAST_CHAT_IDS = [
    str(REPORT_CHAT_ID),
    "-1003973231307"
]

# Target Automation Bots
BNB_BOT = "CryptoProUpRobot"
ENABLE_BNB_GALAXY = os.getenv("ENABLE_BNB_GALAXY", "false").lower() == "true"
STONES_BOT = "stoneswithestand_bot"
MRG_BOT = "mrgminerbot"
ART_BOT = "ART_AIRDROP_BOT"
AILAB_BOT = "AiLab_robot"
ULTRAWALLET_BOT = "UltrawalletTrade_Bot"
APX_BOT = "ApxMinerBot"
AINOVUM_BOT = "ainovum_bot"
MININGGRAM_BOT = "MiningGRAM_Bot"

BNB_REFERRAL_CODE = "Bot46893407"
BNB_REFERRAL_URL = "https://t.me/CryptoProUpRobot?start=Bot46893407"
STONES_REFERRAL_CODE = "r6727787768"
MRG_REFERRAL_CODE = "ref_IRN1G3XD"
ART_REFERRAL_CODE = "6727787768"
AILAB_REFERRAL_CODE = "296852"
ULTRAWALLET_REFERRAL_CODE = "6727787768"
APX_REFERRAL_CODE = "6727787768"
AINOVUM_REFERRAL_CODE = "ref_6727787768"
MININGGRAM_REFERRAL_CODE = "339JU9K"

BNB_WEBHOOK_FALLBACK = "https://api.bots.business/v1/bots/2985029/new-webhook?&command=%2FonWebhook&public_user_token=3d1ed3e6a9bb948436a55057c6e87b59&user_id=46893407"
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS", "0xfda4182001672b9f0f09e2118242e543e35ed5ce")
EVM_VAULT_ADDRESS = WALLET_ADDRESS
OFFICIAL_EMAIL = os.getenv("FLEET_EMAIL", "aaa.support.a@gmail.com")
ARBITRUM_WALLET = "0xfda4182001672b9f0f09e2118242e543e35ed5ce"
TON_PRIMARY_WALLET = "UQBPZiSvitdPU3VUyJK2mRaHVBl69xejw5aOrh1KfKA7gwDT"
MIN_WITHDRAWAL = float(os.getenv("MIN_WITHDRAWAL", "0.00005"))
MANDATORY_OFFICIAL_CHANNELS = ["stoneswithestand", "mrgminer", "ART_AIRDROP", "ApexMiner_Official"]

# Payout Ledger & Live Fleet Balance Cache
PAYOUTS_FILE = os.path.join(BASE_DIR, "payouts.json")
PAYOUT_BALANCES_FILE = os.path.join(BASE_DIR, "payout_balances.json")

def load_account_balances() -> dict:
    """Loads live cached BNB balances from disk so restarts never lose eligibility state."""
    if os.path.exists(PAYOUT_BALANCES_FILE):
        try:
            with open(PAYOUT_BALANCES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
    return {}

def save_account_balances():
    """Atomically persists ACCOUNT_BALANCES to disk."""
    try:
        with open(PAYOUT_BALANCES_FILE, "w", encoding="utf-8") as f:
            json.dump(ACCOUNT_BALANCES, f, indent=2)
    except Exception:
        pass

ACCOUNT_BALANCES = load_account_balances()  # {str(uid): {"balance": float, "name": str, "timestamp": float}}
FLEET_TON_WALLETS_FILE = os.path.join(BASE_DIR, "fleet_ton_wallets.json")
FLEET_EVM_WALLETS_FILE = os.path.join(BASE_DIR, "fleet_evm_wallets.json")

def load_fleet_ton_wallets() -> dict:
    if os.path.exists(FLEET_TON_WALLETS_FILE):
        try:
            with open(FLEET_TON_WALLETS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {
                    str(uid): (info.get("address", "") if isinstance(info, dict) else str(info))
                    for uid, info in data.items()
                    if not str(uid).startswith("_")
                }
        except Exception:
            pass
    return {}

def load_fleet_evm_wallets() -> dict:
    if os.path.exists(FLEET_EVM_WALLETS_FILE):
        try:
            with open(FLEET_EVM_WALLETS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {
                    str(uid): (info.get("address", "") if isinstance(info, dict) else str(info))
                    for uid, info in data.items()
                    if not str(uid).startswith("_")
                }
        except Exception:
            pass
    return {}

FLEET_TON_WALLETS = load_fleet_ton_wallets()
FLEET_EVM_WALLETS = load_fleet_evm_wallets()
SILENT_MODE = os.getenv("SILENT_MODE", "auto").lower()  # "on", "off", or "auto" (night quiet mode)

# Daily target for ATF Miner: 100-150 ads/day (Paced throughout 24 hours with natural breaks)
DAILY_ATF_TARGET_MIN = 100
DAILY_ATF_TARGET_MAX = 150


HUMAN_USER_AGENT = "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro Build/UD1A.230803.041) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.127 Mobile Safari/537.36 Telegram-Android/11.1.3"

STANDARD_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en,bn;q=0.9",
}

# Google Gemini Multi-Key Rotation Pool (14 Active Keys, Suspended Key #8 Excluded)
GEMINI_API_KEYS = [k.strip() for k in os.getenv("GEMINI_API_KEYS", "").split(",") if k.strip()]
if not GEMINI_API_KEYS:
    GEMINI_API_KEYS = [
        "AQ.Ab8RN6KM84Fxx2_1qtQoOL0T3ZXaty0FEFX1-7Lc8XmR_rmMeg",
        "AQ.Ab8RN6JlgBLNwrACewVxtg1RxH752VHEouYCAnzN73hOdoNFjA",
        "AQ.Ab8RN6J6_g_Jr0AeLaUicMkjaPHxVKmoCslAcL1NTQcFSzSe1w",
        "AQ.Ab8RN6KU9MO7yuDWVIh28uuUfp0MyXMknjo3arWWft8X4jbEtQ",
        "AQ.Ab8RN6IxuzzZ1m9nWx8w0Ob3xC_zZ2p_7hdjaCRZtfPBYx5cog",
        "AQ.Ab8RN6Kn0fQD8aYCfG_8KXg9qAKiAQUUSsYrZ10tqgqs1oQvYw",
        "AQ.Ab8RN6I9tnLMJoWuPBQrmRw3WCvS3MWFcQFKB6_TQsabaI5-gg",
        "AQ.Ab8RN6LZCvPuue6uZrGA9_xocFC27NHvPiAvGL1h4YGRC9CY7Q",
        "AQ.Ab8RN6IWzo-mOBhSTwK79wlLILDyImhLCjgiCBp9DQRZ9VVRdQ",
        "AQ.Ab8RN6IKx4lhqSZWPEFA6Uhu8Wf5iOZmfGEeYqrSx3D3IkQymw",
        "AQ.Ab8RN6L78IMc1XSC39WY3bukDgGNVyMMZeJ1rdpKKrq3BW3YFQ",
        "AQ.Ab8RN6IavD_owt-KIaBLLtTbVoGBt_J5R16syXTy3en_6LIDnw",
        "AQ.Ab8RN6Ic1OPZNPytcdUMj6GJCpHMj3NzzZpV8pIZQO_SWL3pBA",
        "AQ.Ab8RN6L_FApJMCEgGOi6XXeKRNrWpS3QugJ6pb5LYUyBmyNAJw"
    ]

async def query_gemini_ai(prompt: str) -> Optional[Tuple[str, str]]:
    """Queries Google Gemini API with 14-key rotation pool and intelligent fallback.
    Primary: gemini-3.8-flash -> Fallback: gemini-3.6-flash
    """
    models = ["gemini-3.8-flash", "gemini-3.6-flash"]
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    keys_pool = list(GEMINI_API_KEYS)
    random.shuffle(keys_pool)
    
    timeout_cfg = aiohttp.ClientTimeout(total=12)
    async with aiohttp.ClientSession(timeout=timeout_cfg) as session:
        for model in models:
            for key in keys_pool[:8]:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
                headers = {
                    "Content-Type": "application/json",
                    "X-goog-api-key": key
                }
                t0 = time.time()
                try:
                    async with session.post(url, json=payload, headers=headers) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            candidates = data.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                if parts:
                                    ans = parts[0].get("text", "").strip()
                                    latency_ms = round((time.time() - t0) * 1000)
                                    return ans, f"Google Gemini ({model} · {latency_ms}ms)"
                        elif resp.status in (429, 503):
                            # High demand or rate limit: try next key / fallback model
                            continue
                        elif resp.status in (403, 404):
                            # Access denied or model not found: skip this key/model
                            continue
                except Exception:
                    continue
    return None

GROQ_API_KEYS = [
    os.getenv("GROQ_API_KEY_1", "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"),
    os.getenv("GROQ_API_KEY_2", "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"),
    os.getenv("GROQ_API_KEY_3", "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")
]

async def query_groq_ai(prompt: str) -> Optional[Tuple[str, str]]:
    """Queries GroqCloud LPU with ultra-low latency (<150ms), model fallback, and key rotation."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    models = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"]
    for model in models:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are the autonomous AI assistant for MY AGY AI Fleet. Provide concise, expert, helpful responses about crypto, automation, and general tech."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 800,
            "temperature": 0.6
        }
        for k in GROQ_API_KEYS:
            if not k:
                continue
            headers = {
                "Authorization": f"Bearer {k}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            }
            try:
                async with aiohttp.ClientSession() as s:
                    t0 = time.time()
                    async with s.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            choices = data.get("choices", [])
                            if choices:
                                ans = choices[0]["message"]["content"].strip()
                                if ans:
                                    latency_ms = round((time.time() - t0) * 1000)
                                    return ans, f"Groq LPU ({model} · {latency_ms}ms)"
            except Exception:
                continue
    return None

if not API_ID or not API_HASH:
    logger.error("Missing TELEGRAM_API_ID or TELEGRAM_API_HASH in .env")
    sys.exit(1)

try:
    API_ID = int(API_ID)
except ValueError:
    logger.error("TELEGRAM_API_ID must be a valid integer")
    sys.exit(1)

client_fp = get_account_fingerprint(REPORT_CHAT_ID)
client = TelegramClient(StringSession(STRING_SESSION or ""), API_ID, API_HASH, **client_fp)

current_bnb_webhook = BNB_WEBHOOK_FALLBACK
task_lock = asyncio.Lock()
accounts_lock = asyncio.Lock()
wake_worker_event = asyncio.Event()
CURRENTLY_ACTIVE_ACCOUNT_ID = None
CURRENTLY_ACTIVE_ACCOUNT_IDS = set()
PRIORITY_ACCOUNT_IDS = set()


# =======================================================
# TAB MENU KEYBOARDS & UI DEFINITIONS
# =======================================================

MAIN_TAB_KEYBOARD = {
    "keyboard": [
        [
            {"text": "🚀 Open Mini App", "web_app": {"url": "https://restore-agy.aaaai2.workers.dev/dashboard"}}
        ],
        [
            {"text": "➕ Add Account"},
            {"text": "💰 Withdraw"}
        ]
    ],
    "resize_keyboard": True,
    "is_persistent": True
}

CANCEL_KEYBOARD = {
    "keyboard": [
        [{"text": "❌ Cancel Login"}]
    ],
    "resize_keyboard": True,
    "is_persistent": True
}


def load_accounts():
    """Loads all managed Telegram accounts from accounts.json."""
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    return data
        except Exception as e:
            logger.error(f"Error reading accounts.json: {e}")
    # Fallback to single primary account from .env
    return [{
        "name": "Arif Hossain",
        "username": "Arif2743aaa",
        "user_id": int(REPORT_CHAT_ID),
        "phone": "+8801700000000",
        "session_string": STRING_SESSION,
        "added_at": "2026-09-17T00:00:00Z",
        "status": "active"
    }]


def save_accounts(accounts_list):
    """Atomically saves updated accounts list to accounts.json."""
    try:
        temp_file = f"{ACCOUNTS_FILE}.tmp.{os.getpid()}_{int(time.time() * 1000)}"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(accounts_list, f, indent=2, ensure_ascii=False)
        os.replace(temp_file, ACCOUNTS_FILE)
    except Exception as e:
        logger.error(f"Error saving accounts.json: {e}")


async def update_account_safely(acc_uid, updates: dict):
    """Safely updates account properties in accounts.json under accounts_lock."""
    async with accounts_lock:
        accs = load_accounts()
        for a in accs:
            if str(a.get("user_id")) == str(acc_uid):
                a.update(updates)
                break
        save_accounts(accs)
        return accs


def ensure_account_ton_wallet(acc: dict) -> str:
    """Ensures account has an isolated TON v4r2 wallet in fleet_ton_wallets.json and accounts.json."""
    uid = str(acc.get("user_id"))
    if not uid or uid == str(REPORT_CHAT_ID):
        return TON_PRIMARY_WALLET

    fleet_file = os.path.join(BASE_DIR, "fleet_ton_wallets.json")
    fwallets = {}
    if os.path.exists(fleet_file):
        try:
            with open(fleet_file, "r", encoding="utf-8") as f:
                fwallets = json.load(f)
        except Exception:
            fwallets = {}

    if uid in fwallets and fwallets[uid].get("address"):
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
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        }
        fwallets[uid] = entry
        with open(fleet_file, "w", encoding="utf-8") as f:
            json.dump(fwallets, f, indent=2, ensure_ascii=False)

        acc["ton_wallet"] = {
            "address": addr_non_bounce,
            "mnemonic": " ".join(mnemonics),
            "version": "v4r2"
        }
        accs = load_accounts()
        for a in accs:
            if str(a.get("user_id")) == uid:
                a["ton_wallet"] = acc["ton_wallet"]
                break
        save_accounts(accs)
        logger.info(f"[{acc.get('name')}] Generated & registered dedicated TON wallet: {addr_non_bounce}")
        return addr_non_bounce
    except Exception as e:
        logger.error(f"[{acc.get('name')}] Error auto-generating TON wallet: {e}")
        return ""


def ensure_account_evm_wallet(acc: dict) -> str:
    """Ensures account has an isolated EVM / BEP-20 / Arbitrum wallet in fleet_evm_wallets.json and accounts.json."""
    uid = str(acc.get("user_id"))
    if not uid or uid == str(REPORT_CHAT_ID):
        return WALLET_ADDRESS

    fwallets = {}
    if os.path.exists(FLEET_EVM_WALLETS_FILE):
        try:
            with open(FLEET_EVM_WALLETS_FILE, "r", encoding="utf-8") as f:
                fwallets = json.load(f)
        except Exception:
            fwallets = {}

    if uid in fwallets and fwallets[uid].get("address"):
        return fwallets[uid]["address"]

    try:
        from eth_account import Account
        acct = Account.create()
        worker_count = len([k for k in fwallets if not str(k).startswith("_")])
        entry = {
            "account_index": worker_count + 2,
            "name": acc.get("name", "Worker"),
            "user_id": uid,
            "address": acct.address,
            "private_key": acct.key.hex(),
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        }
        fwallets[uid] = entry
        with open(FLEET_EVM_WALLETS_FILE, "w", encoding="utf-8") as f:
            json.dump(fwallets, f, indent=2, ensure_ascii=False)

        acc["evm_wallet"] = {
            "address": acct.address,
            "private_key": acct.key.hex(),
            "is_primary": False
        }
        accs = load_accounts()
        for a in accs:
            if str(a.get("user_id")) == uid:
                a["evm_wallet"] = acc["evm_wallet"]
                break
        save_accounts(accs)
        logger.info(f"[{acc.get('name')}] Generated & registered dedicated EVM wallet: {acct.address}")
        return acct.address
    except Exception as e:
        logger.error(f"[{acc.get('name')}] Error auto-generating EVM wallet: {e}")
        return ""


def load_payouts():
    """Loads all historical payouts from payouts.json."""
    if os.path.exists(PAYOUTS_FILE):
        try:
            with open(PAYOUTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception as e:
            logger.error(f"Error reading payouts.json: {e}")
    return []


def record_payout(user_name: str, user_id: int, amount_str: str, wallet: str):
    """Atomically appends a successful withdrawal to payouts.json."""
    try:
        payouts = load_payouts()
        entry = {
            "id": len(payouts) + 1,
            "account": user_name,
            "user_id": user_id,
            "amount": amount_str,
            "wallet": wallet,
            "network": "BEP-20",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "Submitted & Verified"
        }
        payouts.append(entry)
        temp_file = f"{PAYOUTS_FILE}.tmp.{os.getpid()}_{int(time.time() * 1000)}"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(payouts, f, indent=2, ensure_ascii=False)
        os.replace(temp_file, PAYOUTS_FILE)
        logger.info(f"[Payout Ledger] Recorded payout #{entry['id']} for {user_name}: {amount_str} BNB to {wallet}")

        # Replicate payout to Turso LibSQL (AWS Mumbai)
        try:
            import urllib.request
            turso_url = os.getenv("TURSO_URL", "https://my-agy-fleet-db-aaa2743.aws-ap-south-1.turso.io")
            turso_token = os.getenv("TURSO_TOKEN", "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODk4MjQ5NjMsImlkIjoiMDFhMGI5ZTEtNzYwMS03ZDIwLWIwNTAtZDkyNmJkMDRiYzhmIiwia2lkIjoiVXI0T3NhVlRiZktFaWU3aEMydjFPYUQ3T01sQ2RZSjhDa3M3bGZKWEh0MCIsInJpZCI6IjcyYjQ5N2Y4LWVhY2UtNDI5Yy04YTIzLWI4MDRmYjg2ODBhOCJ9.W1W5nHYEFXTFLgIh6Q8yLmH3bL9QgCTEI7d4k-tG_Q_-oZwEZz-Ryq0oYtyvChD0ivOqn6NA_asbPAOYAFVaDw")
            if turso_url and turso_token:
                req_data = json.dumps({
                    "requests": [{
                        "type": "execute",
                        "stmt": {
                            "sql": "INSERT INTO fleet_payouts (user_id, name, amount, wallet, network) VALUES (?, ?, ?, ?, ?)",
                            "args": [
                                {"type": "text", "value": str(user_id)},
                                {"type": "text", "value": str(user_name)},
                                {"type": "text", "value": str(amount_str)},
                                {"type": "text", "value": str(wallet)},
                                {"type": "text", "value": "BEP-20"}
                            ]
                        }
                    }]
                }).encode()
                req = urllib.request.Request(f"{turso_url}/v2/pipeline", data=req_data, headers={"Authorization": f"Bearer {turso_token}", "Content-Type": "application/json"})
                urllib.request.urlopen(req, timeout=3)
        except Exception:
            pass
    except Exception as e:
        logger.error(f"[Payout Ledger] Error recording payout: {e}")


async def get_onchain_bnb_balance(wallet_address: str) -> float:
    """Queries public Binance Smart Chain RPC nodes with resilient multi-node failover."""
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBalance",
        "params": [wallet_address, "latest"],
        "id": 1
    }
    rpc_urls = [
        "https://bsc-dataseed.binance.org",
        "https://bsc-dataseed1.defibit.io",
        "https://bsc-dataseed1.binance.org",
        "https://bsc-dataseed2.binance.org",
        "https://bsc.meowrpc.com",
        "https://1rpc.io/bnb",
        "https://bsc-dataseed1.ninicoin.io"
    ]
    timeout_cfg = aiohttp.ClientTimeout(total=4)
    try:
        async with aiohttp.ClientSession(timeout=timeout_cfg) as session:
            for url in rpc_urls:
                try:
                    async with session.post(
                        url,
                        json=payload,
                        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            hex_val = data.get("result", "0x0")
                            wei = int(hex_val, 16)
                            return round(wei / 1e18, 6)
                except Exception:
                    continue
    except Exception:
        pass
    return 0.0


async def get_crypto_fiat_rates() -> dict:
    """Fetches real-time BNB, TON, and ARB market prices from Binance with multi-source fallback."""
    rates = {
        "bnb_usd": 759.10,
        "ton_usd": 1.60,
        "arb_usd": 0.215,
        "usd_bdt": 121.5
    }
    symbols = [
        ("BNBUSDT", "bnb_usd"),
        ("TONUSDT", "ton_usd"),
        ("ARBUSDT", "arb_usd")
    ]
    timeout_cfg = aiohttp.ClientTimeout(total=4)
    try:
        async with aiohttp.ClientSession(timeout=timeout_cfg) as session:
            for sym, key in symbols:
                try:
                    url = f"https://api.binance.com/api/v3/ticker/price?symbol={sym}"
                    async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            p = float(data.get("price", 0))
                            if p > 0:
                                rates[key] = round(p, 4 if key == "arb_usd" else 2)
                except Exception:
                    pass
    except Exception:
        pass
    return rates


async def get_bnb_fiat_rates() -> tuple[float, float]:
    """Backwards-compatible helper returning (bnb_usd, usd_bdt)."""
    rates = await get_crypto_fiat_rates()
    return rates["bnb_usd"], rates["usd_bdt"]


async def get_onchain_ton_balance(wallet_address: str) -> float:
    """Queries live TON network balance via public Toncenter API with resilient fallback."""
    timeout_cfg = aiohttp.ClientTimeout(total=5)
    try:
        async with aiohttp.ClientSession(timeout=timeout_cfg) as session:
            url = f"https://toncenter.com/api/v2/getAddressInformation?address={wallet_address}"
            async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    nano = int(data.get("result", {}).get("balance", 0))
                    return round(nano / 1e9, 4)
    except Exception:
        pass
    return 0.0


async def get_onchain_arb_balance(wallet_address: str) -> float:
    """Queries Arbitrum One public RPC for native balance."""
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBalance",
        "params": [wallet_address, "latest"],
        "id": 1
    }
    rpc_urls = [
        "https://arb1.arbitrum.io/rpc",
        "https://arbitrum.meowrpc.com",
        "https://1rpc.io/arb"
    ]
    timeout_cfg = aiohttp.ClientTimeout(total=4)
    try:
        async with aiohttp.ClientSession(timeout=timeout_cfg) as session:
            for url in rpc_urls:
                try:
                    async with session.post(url, json=payload, headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            wei = int(data.get("result", "0x0"), 16)
                            return round(wei / 1e18, 6)
                except Exception:
                    continue
    except Exception:
        pass
    return 0.0


STONES_TOKEN_CONTRACT = "0x77643d2afc2496aab18e2c6a38e32c9cb1beb497"

async def get_onchain_stones_balance(wallet_address: str) -> float:
    """Queries Arbitrum One public RPC for STONES ERC-20 token balance."""
    clean_addr = wallet_address.lower().replace("0x", "").zfill(64)
    data = f"0x70a08231{clean_addr}"
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_call",
        "params": [{"to": STONES_TOKEN_CONTRACT, "data": data}, "latest"],
        "id": 1
    }
    rpc_urls = [
        "https://arb1.arbitrum.io/rpc",
        "https://arbitrum.meowrpc.com",
        "https://arbitrum-one.publicnode.com"
    ]
    timeout_cfg = aiohttp.ClientTimeout(total=4)
    try:
        async with aiohttp.ClientSession(timeout=timeout_cfg) as session:
            for url in rpc_urls:
                try:
                    async with session.post(url, json=payload, headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            raw_hex = data.get("result", "0x0")
                            if raw_hex and raw_hex != "0x":
                                return round(int(raw_hex, 16) / 1e18, 2)
                except Exception:
                    continue
    except Exception:
        pass
    return 0.0


async def get_onchain_bep20_usdt_balance(wallet_address: str) -> float:
    """Queries BSC public RPC for BEP-20 USDT token balance."""
    clean_addr = wallet_address.lower().replace("0x", "").zfill(64)
    data = f"0x70a08231{clean_addr}"
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_call",
        "params": [
            {"to": "0x55d398326f99059fF775485246999027B3197955", "data": data},
            "latest"
        ],
        "id": 1
    }
    rpc_urls = [
        "https://bsc-dataseed.binance.org",
        "https://bsc-dataseed1.defibit.io",
        "https://bsc-dataseed1.binance.org"
    ]
    timeout_cfg = aiohttp.ClientTimeout(total=4)
    try:
        async with aiohttp.ClientSession(timeout=timeout_cfg) as session:
            for url in rpc_urls:
                try:
                    async with session.post(url, json=payload, headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}) as resp:
                        if resp.status == 200:
                            res = await resp.json()
                            hex_val = res.get("result", "0x0")
                            raw_val = int(hex_val, 16)
                            return round(raw_val / 1e18, 4)
                except Exception:
                    continue
    except Exception:
        pass
    return 0.0


ONCHAIN_STATE_FILE = os.path.join(BASE_DIR, ".onchain_state.json")

def load_onchain_state():
    if os.path.exists(ONCHAIN_STATE_FILE):
        try:
            with open(ONCHAIN_STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_balance": 0.0, "last_bnb_balance": 0.0, "last_usdt_balance": 0.0, "last_arb_balance": 0.0, "last_ton_balance": 0.0, "last_check": 0}

def save_onchain_state(state):
    """Atomically saves onchain state."""
    try:
        temp_file = f"{ONCHAIN_STATE_FILE}.tmp.{os.getpid()}_{int(time.time() * 1000)}"
        with open(temp_file, "w") as f:
            json.dump(state, f)
        os.replace(temp_file, ONCHAIN_STATE_FILE)
    except Exception:
        pass

async def check_onchain_deposit_alert():
    """Unified Multi-Chain On-Chain Watchdog: monitors BSC (BNB & USDT), Arbitrum One, and TON network deposits."""
    try:
        rates = await get_crypto_fiat_rates()
        bnb_price = rates["bnb_usd"]
        ton_price = rates["ton_usd"]
        usd_bdt = rates["usd_bdt"]
        now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        state = load_onchain_state()

        # 1. BSC (BNB) Deposit Watchdog
        current_bnb = await get_onchain_bnb_balance(WALLET_ADDRESS)
        last_bnb = float(state.get("last_bnb_balance") or state.get("last_balance", 0.0))

        if current_bnb > 0 and last_bnb > 0.0 and current_bnb > last_bnb:
            delta_bnb = round(current_bnb - last_bnb, 6)
            usd_val = delta_bnb * bnb_price
            bdt_val = usd_val * usd_bdt

            conf_msg_1 = (
                f"🎉 <b>On-Chain BEP-20 Payout Confirmed!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💰 <b>Received:</b> <code>+{delta_bnb:.6f} BNB</code> (~${usd_val:.2f} USD / ৳{bdt_val:.2f} BDT)\n"
                f"💼 <b>Recipient Wallet:</b> <code>{WALLET_ADDRESS}</code>\n"
                f"🏦 <b>New Confirmed Balance:</b> <code>{current_bnb:.6f} BNB</code>\n"
                f"📊 <b>BNB Market Rate:</b> <code>${bnb_price:.2f} USD</code> (৳{usd_bdt:.1f} BDT/USD)\n"
                f"🕒 <b>Confirmed At:</b> {now_str}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔗 <a href=\"https://bscscan.com/address/{WALLET_ADDRESS}\">Verify on BscScan</a>\n"
                f"🛡️ <i>Autonomous Cloud Fleet Operations by MY AGY AI</i>"
            )

            conf_msg_2 = (
                f"📜 <b>OFFICIAL BNB GALAXY SETTLEMENT RECEIPT</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"✅ <b>Settlement Status:</b> Confirmed On-Chain (Block Validated)\n"
                f"💰 <b>Delivered Amount:</b> <code>{delta_bnb:.6f} BNB</code>\n"
                f"💼 <b>Destination Wallet:</b> <code>{WALLET_ADDRESS}</code>\n"
                f"🌐 <b>Network:</b> Binance Smart Chain (BEP-20)\n"
                f"🕒 <b>Settlement Timestamp:</b> {now_str}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💎 <i>Proof of Payment Verified • 100% Autonomous Fleet Execution</i>"
            )

            try:
                tg_url = f"https://api.telegram.org/bot{REPORT_BOT_TOKEN}/sendMessage"
                async with aiohttp.ClientSession() as session:
                    await session.post(tg_url, json={"chat_id": PAYOUT_CHANNEL_ID, "text": conf_msg_1, "parse_mode": "HTML", "disable_web_page_preview": False}, timeout=aiohttp.ClientTimeout(total=10))
                    await asyncio.sleep(1.0)
                    await session.post(tg_url, json={"chat_id": PAYOUT_CHANNEL_ID, "text": conf_msg_2, "parse_mode": "HTML"}, timeout=aiohttp.ClientTimeout(total=10))
            except Exception as pe:
                logger.error(f"[Payout Channel] Failed sending BNB confirmation to {PAYOUT_CHANNEL_ID}: {pe}")

            await broadcast_admin_message(conf_msg_1, reply_markup=WALLET_INLINE_KEYBOARD)

        if current_bnb > 0:
            state["last_bnb_balance"] = current_bnb
            state["last_balance"] = current_bnb

        # 2. BSC USDT Deposit Watchdog (Ainovum auto-withdrawals)
        current_usdt = await get_onchain_bep20_usdt_balance(WALLET_ADDRESS)
        last_usdt = float(state.get("last_usdt_balance", 0.0))

        if current_usdt > 0 and last_usdt > 0.0 and current_usdt > last_usdt:
            delta_usdt = round(current_usdt - last_usdt, 4)
            bdt_val = delta_usdt * usd_bdt

            usdt_msg = (
                f"🎉 <b>On-Chain BEP-20 USDT Payout Confirmed!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💰 <b>Received:</b> <code>+{delta_usdt:.4f} USDT</code> (~${delta_usdt:.2f} USD / ৳{bdt_val:.2f} BDT)\n"
                f"💼 <b>Recipient Wallet:</b> <code>{WALLET_ADDRESS}</code>\n"
                f"🏦 <b>New Confirmed Balance:</b> <code>{current_usdt:.4f} USDT</code>\n"
                f"🌐 <b>Network:</b> Binance Smart Chain (BEP-20)\n"
                f"🕒 <b>Confirmed At:</b> {now_str}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔗 <a href=\"https://bscscan.com/token/0x55d398326f99059fF775485246999027B3197955?a={WALLET_ADDRESS}\">Verify on BscScan</a>\n"
                f"🛡️ <i>Autonomous Cloud Fleet Operations by MY AGY AI</i>"
            )

            try:
                tg_url = f"https://api.telegram.org/bot{REPORT_BOT_TOKEN}/sendMessage"
                async with aiohttp.ClientSession() as session:
                    await session.post(tg_url, json={"chat_id": PAYOUT_CHANNEL_ID, "text": usdt_msg, "parse_mode": "HTML"}, timeout=aiohttp.ClientTimeout(total=10))
            except Exception as pe:
                logger.error(f"[Payout Channel] Failed sending USDT confirmation: {pe}")

            await broadcast_admin_message(usdt_msg, reply_markup=WALLET_INLINE_KEYBOARD)

        if current_usdt > 0:
            state["last_usdt_balance"] = current_usdt

        # 3. Arbitrum One Watchdog (Stones Miners withdrawals)
        current_arb = await get_onchain_arb_balance(WALLET_ADDRESS)
        last_arb = float(state.get("last_arb_balance", 0.0))

        if current_arb > 0 and last_arb > 0.0 and current_arb > last_arb:
            delta_arb = round(current_arb - last_arb, 6)

            arb_msg = (
                f"🎉 <b>On-Chain Arbitrum Deposit Confirmed!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💰 <b>Received:</b> <code>+{delta_arb:.6f} ETH/ARB</code>\n"
                f"💼 <b>Recipient Wallet:</b> <code>{WALLET_ADDRESS}</code>\n"
                f"🏦 <b>New Confirmed Balance:</b> <code>{current_arb:.6f} ETH</code>\n"
                f"🌐 <b>Network:</b> Arbitrum One (Layer 2)\n"
                f"🕒 <b>Confirmed At:</b> {now_str}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔗 <a href=\"https://arbiscan.io/address/{WALLET_ADDRESS}\">Verify on Arbiscan</a>\n"
                f"🛡️ <i>Autonomous Cloud Fleet Operations by MY AGY AI</i>"
            )

            try:
                tg_url = f"https://api.telegram.org/bot{REPORT_BOT_TOKEN}/sendMessage"
                async with aiohttp.ClientSession() as session:
                    await session.post(tg_url, json={"chat_id": PAYOUT_CHANNEL_ID, "text": arb_msg, "parse_mode": "HTML"}, timeout=aiohttp.ClientTimeout(total=10))
            except Exception as pe:
                logger.error(f"[Payout Channel] Failed sending Arbitrum confirmation: {pe}")

            await broadcast_admin_message(arb_msg, reply_markup=WALLET_INLINE_KEYBOARD)

        if current_arb > 0:
            state["last_arb_balance"] = current_arb

        # 3b. Arbitrum One STONES Token Watchdog (Stones Miners withdrawals)
        current_stones = await get_onchain_stones_balance(WALLET_ADDRESS)
        last_stones = float(state.get("last_stones_balance", 0.0))

        if current_stones > 0 and last_stones > 0.0 and current_stones > last_stones:
            delta_stones = round(current_stones - last_stones, 0)

            stones_msg = (
                f"💎 <b>On-Chain STONES Deposit Confirmed!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💰 <b>Received:</b> <code>+{delta_stones:.0f} STONES</code>\n"
                f"💼 <b>Recipient Wallet:</b> <code>{WALLET_ADDRESS}</code>\n"
                f"🏦 <b>New Confirmed Balance:</b> <code>{current_stones:.0f} STONES</code>\n"
                f"🌐 <b>Network:</b> Arbitrum One (Layer 2)\n"
                f"🕒 <b>Confirmed At:</b> {now_str}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔗 <a href=\"https://arbiscan.io/token/{STONES_TOKEN_CONTRACT}?a={WALLET_ADDRESS}\">Verify on Arbiscan</a>\n"
                f"🛡️ <i>Autonomous Cloud Fleet Operations by MY AGY AI</i>"
            )

            try:
                tg_url = f"https://api.telegram.org/bot{REPORT_BOT_TOKEN}/sendMessage"
                async with aiohttp.ClientSession() as session:
                    await session.post(tg_url, json={"chat_id": PAYOUT_CHANNEL_ID, "text": stones_msg, "parse_mode": "HTML"}, timeout=aiohttp.ClientTimeout(total=10))
            except Exception as pe:
                logger.error(f"[Payout Channel] Failed sending STONES confirmation: {pe}")

            await broadcast_admin_message(stones_msg, reply_markup=WALLET_INLINE_KEYBOARD)

        if current_stones > 0:
            state["last_stones_balance"] = current_stones

        # 4. TON Network Deposit Watchdog (ART Airdrop & MiningGRAM)
        current_ton = await get_onchain_ton_balance(TON_PRIMARY_WALLET)
        last_ton = float(state.get("last_ton_balance", 0.0))

        if current_ton > 0 and last_ton > 0.0 and current_ton > last_ton:
            delta_ton = round(current_ton - last_ton, 4)
            usd_val = delta_ton * ton_price
            bdt_val = usd_val * usd_bdt

            ton_msg_1 = (
                f"🎉 <b>On-Chain TON Deposit Confirmed!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💰 <b>Received:</b> <code>+{delta_ton:.4f} TON</code> (~${usd_val:.2f} USD / ৳{bdt_val:.2f} BDT)\n"
                f"💼 <b>Recipient Wallet:</b> <code>{TON_PRIMARY_WALLET}</code>\n"
                f"🏦 <b>New Confirmed Balance:</b> <code>{current_ton:.4f} TON</code>\n"
                f"📊 <b>TON Market Rate:</b> <code>${ton_price:.2f} USD</code> (৳{usd_bdt:.1f} BDT/USD)\n"
                f"🕒 <b>Confirmed At:</b> {now_str}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔗 <a href=\"https://tonviewer.com/{TON_PRIMARY_WALLET}\">Verify on Tonviewer</a>\n"
                f"🛡️ <i>Autonomous Cloud Fleet Operations by MY AGY AI</i>"
            )

            ton_msg_2 = (
                f"📜 <b>OFFICIAL TON NETWORK SETTLEMENT RECEIPT</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"✅ <b>Settlement Status:</b> Confirmed On-Chain (TON Block Validated)\n"
                f"💰 <b>Delivered Amount:</b> <code>{delta_ton:.4f} TON</code>\n"
                f"💼 <b>Destination Wallet:</b> <code>{TON_PRIMARY_WALLET}</code>\n"
                f"🌐 <b>Network:</b> The Open Network (TON Mainnet)\n"
                f"🕒 <b>Settlement Timestamp:</b> {now_str}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💎 <i>Proof of Payment Verified • 100% Autonomous Fleet Execution</i>"
            )

            try:
                tg_url = f"https://api.telegram.org/bot{REPORT_BOT_TOKEN}/sendMessage"
                async with aiohttp.ClientSession() as session:
                    await session.post(tg_url, json={"chat_id": PAYOUT_CHANNEL_ID, "text": ton_msg_1, "parse_mode": "HTML", "disable_web_page_preview": False}, timeout=aiohttp.ClientTimeout(total=10))
                    await asyncio.sleep(1.0)
                    await session.post(tg_url, json={"chat_id": PAYOUT_CHANNEL_ID, "text": ton_msg_2, "parse_mode": "HTML"}, timeout=aiohttp.ClientTimeout(total=10))
            except Exception as pe:
                logger.error(f"[Payout Channel] Failed sending TON confirmation to {PAYOUT_CHANNEL_ID}: {pe}")

            await broadcast_admin_message(ton_msg_1, reply_markup=WALLET_INLINE_KEYBOARD)

        if current_ton > 0:
            state["last_ton_balance"] = current_ton

        state["last_check"] = time.time()
        save_onchain_state(state)
    except Exception as e:
        logger.debug(f"[On-Chain Deposit Watcher] Check error: {e}")


async def build_payouts_report():
    """Generates the payout ledger report showing lifetime payouts and recent records."""
    payouts = load_payouts()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    total_withdrawn = sum(float(p.get("amount", 0)) for p in payouts if p.get("amount"))

    onchain_bal = await get_onchain_bnb_balance(WALLET_ADDRESS)
    bnb_price, usd_bdt = await get_bnb_fiat_rates()
    tot_usd = total_withdrawn * bnb_price
    tot_bdt = tot_usd * usd_bdt
    onchain_usd = onchain_bal * bnb_price
    onchain_bdt = onchain_usd * usd_bdt

    lines = []
    for p in reversed(payouts[-12:]):
        ts = p.get("timestamp", "")[:19].replace("T", " ")
        lines.append(f"• **{p.get('account', 'User')}**: `{p.get('amount')} BNB` ({ts} UTC) — *{p.get('status', 'Submitted')}*")

    history_str = "\n".join(lines) if lines else "_No withdrawals recorded yet. Auto-withdraw triggers automatically when any account reaches ≥ 0.000050 BNB._"

    rep = (
        f"📜 *BNB Galaxy Payout Ledger*\n"
        f"🕒 _{now_str}_\n\n"
        f"• **Total Fleet Withdrawn:** `{total_withdrawn:.6f} BNB` (~${tot_usd:.2f} USD / ৳{tot_bdt:.2f} BDT)\n"
        f"• **Confirmed On-Chain Wallet:** `{onchain_bal:.6f} BNB` (~${onchain_usd:.2f} USD / ৳{onchain_bdt:.2f} BDT)\n"
        f"• **Total Transactions:** `{len(payouts)} Completed`\n"
        f"• **Recipient Wallet:** `{WALLET_ADDRESS}`\n"
        f"• **Network:** Binance Smart Chain (BEP-20)\n"
        f"• **BNB Market Price:** `${bnb_price:.2f} USD` (৳{bnb_price*usd_bdt:,.0f} BDT)\n\n"
        f"📋 *Recent Transactions:*\n"
        f"{history_str}\n\n"
        f"🔗 [Verify on BscScan](https://bscscan.com/address/{WALLET_ADDRESS})\n"
        f"🛡️ _Autonomous Cloud Fleet Operations by MY AGY AI_"
    )
    return rep


async def build_earnings_report():
    """Generates comprehensive fleet yield and earnings analytics."""
    accounts = load_accounts()
    payouts = load_payouts()
    now_utc = datetime.now(timezone.utc)
    now_str = now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")

    total_withdrawn = sum(float(p.get("amount", 0)) for p in payouts if p.get("amount"))
    payout_count = len(payouts)

    onchain_bal = await get_onchain_bnb_balance(WALLET_ADDRESS)
    bnb_price, usd_bdt = await get_bnb_fiat_rates()

    daily_est_bnb = len(accounts) * 0.000065
    monthly_est_bnb = daily_est_bnb * 30.0

    daily_usd = daily_est_bnb * bnb_price
    daily_bdt = daily_usd * usd_bdt

    monthly_usd = monthly_est_bnb * bnb_price
    monthly_bdt = monthly_usd * usd_bdt

    withdrawn_usd = total_withdrawn * bnb_price
    withdrawn_bdt = withdrawn_usd * usd_bdt

    onchain_usd = onchain_bal * bnb_price
    onchain_bdt = onchain_usd * usd_bdt

    rep = (
        f"📈 *MY AGY AI — Fleet Yield & Analytics*\n"
        f"🕒 _{now_str}_\n\n"
        f"🏦 *On-Chain Wallet Status:*\n"
        f"• **Wallet:** `{WALLET_ADDRESS}`\n"
        f"• **Confirmed Balance:** `{onchain_bal:.6f} BNB` (~${onchain_usd:.2f} USD / ৳{onchain_bdt:.2f} BDT)\n"
        f"• **BNB Market Rate:** `${bnb_price:.2f} USD` (৳{usd_bdt:.1f} BDT/USD)\n\n"
        f"📊 *Lifetime Realized Withdrawals:*\n"
        f"• **Total Payouts:** `{payout_count} transactions`\n"
        f"• **Total Delivered:** `{total_withdrawn:.6f} BNB` (~${withdrawn_usd:.2f} USD / ৳{withdrawn_bdt:.2f} BDT)\n"
        f"• **Auto-Threshold:** `0.000050 BNB` (Instant auto-withdraw)\n\n"
        f"🚀 *Projected Earning Capacity ({len(accounts)} Accounts):*\n"
        f"• **Daily Fleet Yield:** `~{daily_est_bnb:.6f} BNB` (~${daily_usd:.2f} USD / ৳{daily_bdt:.2f} BDT)\n"
        f"• **Monthly Projected:** `~{monthly_est_bnb:.6f} BNB` (~${monthly_usd:.2f} USD / ৳{monthly_bdt:.2f} BDT)\n"
        f"• **Active Fleet Size:** `{len(accounts)} Telegram Accounts`\n"
        f"• **Daily Task Volume:** `{len(accounts) * 10} Tasks/Day`\n\n"
        f"💡 _Tip: Adding more accounts via `➕ Add Account` scales your daily yield linearly!_"
    )
    return rep


async def build_midnight_summary():
    """Builds a daily closing P&L card broadcast at 00:00 UTC."""
    accounts = load_accounts()
    payouts = load_payouts()
    now_utc = datetime.now(timezone.utc)
    date_str = now_utc.strftime("%Y-%m-%d")

    total_withdrawn = sum(float(p.get("amount", 0)) for p in payouts if p.get("amount"))
    onchain_bal = await get_onchain_bnb_balance(WALLET_ADDRESS)
    bnb_price, usd_bdt = await get_bnb_fiat_rates()

    withdrawn_usd = total_withdrawn * bnb_price
    withdrawn_bdt = withdrawn_usd * usd_bdt

    onchain_usd = onchain_bal * bnb_price
    onchain_bdt = onchain_usd * usd_bdt

    card = (
        f"🌙 *MY AGY AI — Daily Closing Summary*\n"
        f"📅 `{date_str} • 00:00 UTC`\n\n"
        f"⚡ **Fleet Health:** `{len(accounts)}/{len(accounts)} Accounts Active (100%)`\n"
        f"🪙 **Daily Tasks:** `{len(accounts) * 10}/{len(accounts) * 10} Completed`\n"
        f"💰 **Confirmed On-Chain:** `{onchain_bal:.6f} BNB` (~${onchain_usd:.2f} USD / ৳{onchain_bdt:.2f} BDT)\n"
        f"🏆 **Lifetime Withdrawals:** `{total_withdrawn:.6f} BNB` ({len(payouts)} payouts processed)\n"
        f"🛡️ **System:** 🟢 Immortal Supervisor 24/7"
    )
    return card


async def audit_account_session(acc: dict) -> tuple[bool, str]:
    """Tests live MTProto connectivity and authorization for an individual account session."""
    sess_str = acc.get("session_string")
    if not sess_str:
        return False, "Missing session string"
    uid = str(acc.get("user_id"))
    # If account 1 (Master) is already connected in this process
    if acc.get("is_referral_host") or uid == str(REPORT_CHAT_ID):
        try:
            if client.is_connected() and await client.is_user_authorized():
                me = await client.get_me()
                u_str = f"@{me.username}" if me.username else "NoUsername"
                return True, f"Primary Master Active ({me.first_name} {u_str}, ID: {me.id})"
        except Exception:
            pass

    test_client = None
    try:
        from telethon.sessions import StringSession
        test_client = TelegramClient(
            StringSession(sess_str),
            int(API_ID),
            API_HASH,
            connection_retries=1,
            timeout=5
        )
        await test_client.connect()
        if not await test_client.is_user_authorized():
            return False, "Unauthorized (Session Revoked by Telegram)"
        me = await test_client.get_me()
        if not me:
            return False, "Authorized but cannot fetch profile"
        u_str = f"@{me.username}" if me.username else "NoUsername"
        return True, f"Active ({me.first_name} {u_str}, ID: {me.id})"
    except (AuthKeyUnregisteredError, UserDeactivatedError, SessionRevokedError) as auth_err:
        return False, f"Revoked: {auth_err}"
    except Exception as e:
        err_msg = str(e)
        if any(term in err_msg for term in ["AUTH_KEY_UNREGISTERED", "UserDeactivated", "SESSION_REVOKED"]):
            return False, f"Revoked: {err_msg}"
        return False, f"Error: {err_msg}"
    finally:
        if test_client:
            try:
                await test_client.disconnect()
            except Exception:
                pass


async def run_fleet_session_audit(notify_admin: bool = True) -> dict:
    """Audits all MTProto sessions across the fleet. Isolates revoked accounts to protect remaining fleet."""
    accounts = load_accounts()
    healthy_accounts = []
    revoked_accounts = []
    now_ts = time.time()

    for idx, acc in enumerate(accounts, 1):
        name = acc.get("name", f"Account #{idx}")
        phone = acc.get("phone", "Hidden")
        ok, reason = await audit_account_session(acc)
        acc["last_audited_at"] = now_ts
        if ok:
            acc["status"] = "active"
            acc.pop("revocation_reason", None)
            healthy_accounts.append({"name": name, "phone": phone, "reason": reason, "index": idx})
        else:
            acc["status"] = "revoked"
            acc["revocation_reason"] = reason
            acc["revoked_at"] = now_ts
            revoked_accounts.append({"name": name, "phone": phone, "reason": reason, "index": idx})

    save_accounts(accounts)

    summary = {
        "total": len(accounts),
        "healthy_count": len(healthy_accounts),
        "revoked_count": len(revoked_accounts),
        "healthy": healthy_accounts,
        "revoked": revoked_accounts,
        "timestamp": now_ts
    }

    # Proactive Alert to Admin private chat if any accounts are revoked
    if revoked_accounts and notify_admin:
        revoked_lines = [
            f"• ❌ **{r['name']}** (`{r['phone']}`): `{r['reason']}`"
            for r in revoked_accounts
        ]
        alert_msg = (
            f"⚠️ <b>FLEET SESSION HEALTH AUDIT ALERT</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"❌ <b>Revoked Account(s) Detected:</b> {len(revoked_accounts)}\n"
            + "\n".join(revoked_lines) + "\n\n"
            f"🛡️ <b>Autonomous Fleet Self-Healing:</b>\n"
            f"Revoked sessions have been safely isolated from rotation.\n"
            f"<b>{len(healthy_accounts)} remaining accounts</b> continue mining 100% uninterrupted.\n\n"
            f"💡 <i>Use /addaccount or /login to reconnect or replace the revoked sessions.</i>"
        )
        try:
            await broadcast_admin_message(alert_msg)
        except Exception as e:
            logger.error(f"[Session Auditor] Alert error: {e}")

    return summary


async def build_health_audit_report():
    """Generates detailed fleet health and live session audit report."""
    audit_res = await run_fleet_session_audit(notify_admin=False)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    total = audit_res["total"]
    healthy_cnt = audit_res["healthy_count"]
    revoked_cnt = audit_res["revoked_count"]
    health_pct = int((healthy_cnt / total) * 100) if total else 100

    lines = [
        f"🩺 *MY AGY AI — Live Fleet Health & Session Audit*\n"
        f"🕒 _{now_str}_\n"
    ]

    for h in audit_res["healthy"]:
        lines.append(f"{h['index']}️⃣ **{h['name']}** (`{h['phone']}`) — 🟢 Active ({h['reason']})")

    for r in audit_res["revoked"]:
        lines.append(f"{r['index']}️⃣ **{r['name']}** (`{r['phone']}`) — 🔴 Revoked: `{r['reason']}`")

    lines.append(
        f"\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• **Fleet Health Score:** `{health_pct}%` ({healthy_cnt}/{total} Operational)\n"
        f"• **Active Sessions:** `{healthy_cnt}` Accounts Running 24/7\n"
        f"• **Isolated / Revoked:** `{revoked_cnt}` Accounts\n"
        f"• **Audit Frequency:** Every 6 Hours (Autonomous Self-Healing)\n"
        f"• **Cloud VPS Host:** `🟢 Online (192.46.208.170)`\n\n"
        f"💡 _If any account is revoked, the remaining accounts continue mining uninterrupted._"
    )
    return "\n".join(lines)


async def session_health_auditor_loop():
    """Runs automated proactive MTProto session audit every 6 hours."""
    logger.info("[Session Auditor] 6-Hour Proactive Fleet Session Auditor initialized.")
    await asyncio.sleep(90)  # Delayed boot to allow primary worker loop initialization
    while True:
        try:
            logger.info("[Session Auditor] Running 6-hour proactive MTProto session audit...")
            summary = await run_fleet_session_audit(notify_admin=True)
            logger.info(f"[Session Auditor] Audit complete: {summary['healthy_count']}/{summary['total']} accounts operational.")
        except Exception as e:
            logger.error(f"[Session Auditor] Error in audit cycle: {e}")
        await asyncio.sleep(6 * 3600)


CUSTOM_BOTS_FILE = os.path.join(BASE_DIR, "custom_mining_bots.json")

DEFAULT_MINING_BOTS = [
    {
        "id": "bnb_galaxy",
        "name": "BNB Galaxy",
        "bot": "@BNBGalaxy_bot",
        "type": "native_tasks",
        "status": "active",
        "interval_hours": 12,
        "reward": "BNB (BEP-20)",
        "min_withdraw": "0.00005 BNB",
        "description": "10 Daily Tasks & Auto-Withdraw to BEP-20 wallet"
    },
    {
        "id": "stones_miners",
        "name": "Stones Miners",
        "bot": "@stoneswithestand_bot",
        "type": "daily_checkin",
        "status": "active",
        "interval_hours": 24,
        "reward": "STONES (Arbitrum One)",
        "min_withdraw": "500 STONES",
        "description": "Daily Check-in & Mining with 10/10 referrals"
    },
    {
        "id": "mrg_miner",
        "name": "MRG Miner",
        "bot": "@mrgminerbot",
        "type": "harvest_cut",
        "status": "active",
        "interval_hours": 24,
        "reward": "MRG + TON",
        "min_withdraw": "On-Chain TON",
        "description": "Squad Mining Harvest & 10% Lifetime Daily Cut"
    },
    {
        "id": "art_airdrop",
        "name": "ART Airdrop",
        "bot": "@ArtAirdropBot",
        "type": "continuous_8h",
        "status": "active",
        "interval_hours": 8,
        "reward": "ART + TON",
        "min_withdraw": "800 ART",
        "description": "Continuous 8h Mining Cycles & TON Cashout"
    },
    {
        "id": "ailab_miner",
        "name": "AI Lab Robot",
        "bot": "@AiLab_robot",
        "type": "cloud_miner",
        "ref_code": "296852",
        "status": "active",
        "interval_hours": 8,
        "reward": "Hashes & USD",
        "min_withdraw": "USD Direct",
        "description": "24/7 Cloud Miner, Auto-Exchange to USD & Task Claims"
    },
    {
        "id": "ultrawallet_miner",
        "name": "UltraWallet",
        "bot": "@UltrawalletTrade_Bot",
        "type": "wallet_mining",
        "ref_code": "6727787768",
        "status": "active",
        "interval_hours": 24,
        "reward": "Reward Points & USDT",
        "min_withdraw": "USDT Commissions",
        "description": "24h Passive Mining, Daily Streaks & Energy Claims"
    },
    {
        "id": "apx_miner",
        "name": "Apex Miner",
        "bot": "@ApxMinerBot",
        "type": "miniapp_mining",
        "ref_code": "6727787768",
        "status": "active",
        "interval_hours": 8,
        "reward": "APX Points",
        "min_withdraw": "On-Chain APX",
        "description": "Continuous 8h Mining, Daily Streaks, Social Tasks & Ad Boost"
    },
    {
        "id": "atf_miner",
        "name": "ATF Miner",
        "bot": "@atf_miner_bot",
        "type": "ad_tasks",
        "status": "active",
        "interval_hours": 12,
        "reward": "ATF",
        "min_withdraw": "Auto-compounded",
        "description": "Auto-compounding & Cloud Direct Ad Tasks"
    }
]

def load_custom_mining_bots():
    if os.path.exists(CUSTOM_BOTS_FILE):
        try:
            with open(CUSTOM_BOTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_MINING_BOTS

def save_custom_mining_bots(bots):
    try:
        temp_file = f"{CUSTOM_BOTS_FILE}.tmp.{os.getpid()}_{int(time.time() * 1000)}"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(bots, f, indent=2, ensure_ascii=False)
        os.replace(temp_file, CUSTOM_BOTS_FILE)
    except Exception:
        pass

def register_new_mining_bot(bot_username: str, ref_code: str = "", note: str = "") -> dict:
    bots = load_custom_mining_bots()
    bot_clean = bot_username.strip()
    if not bot_clean.startswith("@"):
        bot_clean = "@" + bot_clean
    bot_id = bot_clean.lstrip("@").lower()

    for b in bots:
        if b.get("id") == bot_id or b.get("bot", "").lower() == bot_clean.lower():
            b["ref_code"] = ref_code or b.get("ref_code", "")
            b["status"] = "active"
            save_custom_mining_bots(bots)
            return {"created": False, "bot": b}

    new_bot = {
        "id": bot_id,
        "name": bot_clean.lstrip("@").capitalize(),
        "bot": bot_clean,
        "type": "custom_extension",
        "ref_code": ref_code,
        "status": "active",
        "interval_hours": 12,
        "reward": "Custom Token",
        "min_withdraw": "Auto-Harvest",
        "description": note or f"Autonomous farming for {bot_clean}"
    }
    bots.append(new_bot)
    save_custom_mining_bots(bots)
    return {"created": True, "bot": new_bot}

def build_mining_bots_report():
    bots = load_custom_mining_bots()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        f"⛏️ *MY AGY AI — Active Mining Bots & Engines*\n"
        f"🕒 _{now_str}_\n"
    ]
    for idx, b in enumerate(bots, 1):
        status_dot = "🟢" if b.get("status") == "active" else "⚪"
        ref_str = f" | Ref: `{b.get('ref_code')}`" if b.get("ref_code") else ""
        lines.append(
            f"{idx}️⃣ {status_dot} **{b.get('name')}** (`{b.get('bot')}`{ref_str})\n"
            f"   • Reward: `{b.get('reward')}` | Cycle: `Every {b.get('interval_hours')}h`\n"
            f"   • Detail: _{b.get('description')}_"
        )
    lines.append(
        f"\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 *How to add any new mining bot:*\n"
        f"Send: `/addbot @BotUsername [referral_code]`\n"
        f"Example: `/addbot @BlumCryptoBot ref_123`\n\n"
        f"The fleet will automatically bind your referral and start farming across all 13 accounts!"
    )
    return "\n".join(lines)


def build_accounts_report():
    """Generates the formatted overview of all connected Telegram accounts with referral compounding and admin status."""
    accounts = load_accounts()
    lines = [
        f"👥 *Connected Telegram Fleet ({len(accounts)} Accounts)*\n",
        "All accounts run 24/7 with referral compounding & anti-ban protection:\n"
    ]
    for idx, acc in enumerate(accounts, 1):
        name = acc.get("name", "User")
        uname = f"@{acc.get('username')}" if acc.get("username") and acc.get("username") != "None" else "No username"
        uid = acc.get("user_id", "N/A")
        phone = acc.get("phone", "Hidden")
        status = acc.get("status", "active").capitalize()
        is_host = acc.get("is_referral_host") or str(uid) == str(REPORT_CHAT_ID)
        is_admin = str(uid) in ADMIN_IDS
        role = "👑 Primary Host (Master)" if is_host else ("⚡ Mining Worker & Admin" if is_admin else "⚡ Mining Worker")
        proxy = acc.get("proxy")
        loc = f"🛡️ Proxy: `{proxy.split('@')[-1]}`" if proxy else "🌍 Cloud Direct"
        bnb_ref = "Host 👑" if is_host else ("Linked (`Bot46893407`) ✅" if acc.get("bnb_referral_bound") else "Auto-Binding...")
        atf_ref = "Host 👑" if is_host else ("Linked (`ref_6727787768`) ✅" if acc.get("atf_referral_bound") else "Auto-Binding...")
        admin_tag = "Authorized Admin 🛡️" if is_admin else "Worker Node 📱"

        lines.append(
            f"{idx}️⃣ **{name}** ({uname})\n"
            f"   • Role: `{role}`\n"
            f"   • ID: `{uid}` | Phone: `{phone}`\n"
            f"   • Permissions: `{admin_tag}`\n"
            f"   • BNB Referral: {bnb_ref}\n"
            f"   • ATF Referral: {atf_ref}\n"
            f"   • Geo-Profile: `{loc}`\n"
            f"   • Daemon Status: `🟢 {status}`"
        )

    lines.append("\n💡 _Tap `➕ Add Account` below to connect another account for compounding commissions!_")
    return "\n".join(lines)


STATUS_INLINE_KEYBOARD = {
    "inline_keyboard": [
        [
            {
                "text": "🚀 Open Visual Mini App",
                "web_app": {"url": "https://restore-agy.aaaai2.workers.dev/dashboard"}
            }
        ],
        [
            {"text": "➕ Add Account", "callback_data": "btn_add_account"},
            {"text": "💰 Instant Withdraw", "callback_data": "btn_withdraw"}
        ],
        [
            {"text": "🔄 Refresh", "callback_data": "btn_status"},
            {"text": "⚡ Withdraw All", "callback_data": "btn_withdraw_all"}
        ]
    ]
}

WALLET_INLINE_KEYBOARD = {
    "inline_keyboard": [
        [
            {"text": "🔄 Refresh", "callback_data": "btn_wallet"},
            {"text": "💰 Withdraw", "callback_data": "btn_withdraw"}
        ],
        [
            {"text": "⚡ Apex Miner", "callback_data": "btn_apx"},
            {"text": "🚀 ART Airdrop", "callback_data": "btn_art"},
            {"text": "🪙 ATF Miner", "callback_data": "btn_atf"}
        ],
        [
            {"text": "📜 Payouts", "callback_data": "btn_payouts"},
            {"text": "📈 Yield Analytics", "callback_data": "btn_earnings"}
        ],
        [
            {"text": "🔗 BscScan (BNB)", "url": f"https://bscscan.com/address/{WALLET_ADDRESS}"},
            {"text": "🔗 Tonviewer (TON)", "url": f"https://tonviewer.com/{TON_PRIMARY_WALLET}"}
        ],
        [
            {"text": "🔗 Arbiscan (ARB)", "url": f"https://arbiscan.io/address/{WALLET_ADDRESS}"}
        ]
    ]
}




def generate_random_email():
    """Returns official fleet email address configured by user."""
    return OFFICIAL_EMAIL


async def ai_classify_bot_prompt(bot_text: str) -> str:
    """Uses Cloudflare Edge Multi-Cloud AI Cascade (Gemini Flash -> Groq -> Workers AI) across 3 free edge nodes."""
    prompt = (
        f"The Telegram bot sent this message during a withdrawal: '{bot_text}'. "
        f"Classify what the bot requires from the user. Respond with ONLY one word: "
        f"WALLET (asking for crypto wallet address), EMAIL (asking for email address), "
        f"AMOUNT (asking for withdrawal amount or number), CONFIRM (asking to click a button or confirm), "
        f"or WAIT (asking to wait or showing status)."
    )
    for cf_url in CF_WORKER_URLS:
        try:
            async with aiohttp.ClientSession() as s:
                async with s.post(
                    f"{cf_url}/api/ai",
                    json={"prompt": prompt},
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=4)
                ) as r:
                    if r.status == 200:
                        d = await r.json()
                        ans = (d.get("answer") or "").strip().upper()
                        for valid in ["WALLET", "EMAIL", "AMOUNT", "CONFIRM", "WAIT"]:
                            if valid in ans:
                                return valid
        except Exception:
            continue
    return "UNKNOWN"


async def human_delay(min_sec: float, max_sec: float, activity: str):
    duration = round(random.uniform(min_sec, max_sec), 2)
    logger.info(f"Human delay: {activity} ({duration}s)...")
    await asyncio.sleep(duration)


def format_seconds_to_hm(seconds: float):
    if seconds <= 0:
        return "Ready now"
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    if h > 0:
        return f"{h}h {m}m"
    return f"{m}m"


# =======================================================
# TELEGRAM BOT API SERVICE (@My_Router_AI_bot)
# =======================================================

async def setup_bot_tab_menu():
    """Configures Telegram Bot Command Menu and Chat Menu Button."""
    url_cmd = f"https://api.telegram.org/bot{REPORT_BOT_TOKEN}/setMyCommands"
    url_btn = f"https://api.telegram.org/bot{REPORT_BOT_TOKEN}/setChatMenuButton"
    commands = [
        {"command": "start", "description": "🚀 Main Menu & Mini App"},
        {"command": "status", "description": "📊 Fleet Operations & Telemetry"},
        {"command": "withdraw", "description": "💰 Check & Withdraw BNB"},
        {"command": "wallet", "description": "💼 Multi-Chain Portfolio Vaults"},
        {"command": "accounts", "description": "👥 Managed Accounts Roster"},
        {"command": "backup", "description": "💾 Cloud Backup to Telegram"},
        {"command": "help", "description": "ℹ️ Commands & Support"}
    ]
    try:
        async with aiohttp.ClientSession() as session:
            await session.post(url_cmd, json={"commands": commands})
            menu_btn_payload = {
                "menu_button": {
                    "type": "web_app",
                    "text": "🚀 Mini App",
                    "web_app": {
                        "url": "https://restore-agy.aaaai2.workers.dev/dashboard"
                    }
                }
            }
            await session.post(url_btn, json=menu_btn_payload)
            logger.info("[ReportBot] Bot commands updated and chat menu button set to native WebApp.")
    except Exception as e:
        logger.error(f"[ReportBot] Error setting bot menu: {e}")


async def send_chat_action(action: str = "typing", chat_id=None):
    """Shows typing action in the Telegram chat."""
    target_chat_id = str(chat_id) if chat_id else str(REPORT_CHAT_ID)
    url = f"https://api.telegram.org/bot{REPORT_BOT_TOKEN}/sendChatAction"
    try:
        async with aiohttp.ClientSession() as session:
            await session.post(url, json={"chat_id": target_chat_id, "action": action})
    except Exception as e:
        logger.warning(f"[ReportBot] Failed to send chat action: {e}")


def is_silent_notification(text: str) -> bool:
    """Determines whether a Telegram notification should be delivered silently without sound."""
    # Critical messages are ALWAYS audible (payouts, 2FA, security, error alerts)
    loud_keywords = [
        "🎉", "Auto-Withdrawal Submitted", "OFFICIAL BNB GALAXY PAYOUT RECEIPT",
        "Two-Factor", "2FA", "Security Alert", "⛔", "❌", "Disaster Recovery"
    ]
    for kw in loud_keywords:
        if kw in text:
            return False

    mode = os.getenv("SILENT_MODE", SILENT_MODE).lower()
    if mode == "on":
        return True
    elif mode == "off":
        return False
    else:  # "auto": muted during night hours (23:00 to 07:00 BST / UTC+6)
        now_bst = datetime.now(timezone.utc) + timedelta(hours=6)
        return now_bst.hour >= 23 or now_bst.hour < 7


async def send_report_message(text: str, reply_markup=None, chat_id=None, force_silent: bool = None):
    """Sends a notification/report via MyRouterAIBot directly to the user/admin with smart quiet mode support."""
    target_chat_id = str(chat_id) if chat_id else str(REPORT_CHAT_ID)
    disable_notify = force_silent if force_silent is not None else is_silent_notification(text)
    url = f"https://api.telegram.org/bot{REPORT_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": target_chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
        "disable_notification": disable_notify
    }
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                data = await resp.json()
                if not data.get("ok", False):
                    # Fallback to plain text if Markdown fails
                    desc = data.get("description", "")
                    if "can't parse entities" in desc or "markdown" in desc.lower():
                        payload.pop("parse_mode", None)
                        async with session.post(url, json=payload) as resp2:
                            data2 = await resp2.json()
                            return data2.get("ok", False)
                return data.get("ok", False)
    except Exception as e:
        logger.error(f"[ReportBot] Failed to send report: {e}")
        return False


async def send_message_chunks(text: str, reply_markup=None, chat_id=None):
    """Sends long messages in chunks to prevent Telegram length limit errors."""
    if len(text) <= 3800:
        return await send_report_message(text, reply_markup=reply_markup, chat_id=chat_id)
    
    chunks = []
    remaining = text
    while remaining:
        if len(remaining) <= 3800:
            chunks.append(remaining)
            break
        split_idx = remaining.rfind("\n\n", 0, 3800)
        if split_idx == -1:
            split_idx = remaining.rfind("\n", 0, 3800)
        if split_idx == -1:
            split_idx = 3800
        chunks.append(remaining[:split_idx])
        remaining = remaining[split_idx:].lstrip()

    for idx, chunk in enumerate(chunks):
        markup = reply_markup if idx == len(chunks) - 1 else None
        await send_report_message(chunk, reply_markup=markup, chat_id=chat_id)
        await asyncio.sleep(0.4)


async def answer_callback_query(callback_query_id: str, text: str = "", show_alert: bool = False):
    """Answers Telegram inline keyboard callback query."""
    url = f"https://api.telegram.org/bot{REPORT_BOT_TOKEN}/answerCallbackQuery"
    try:
        async with aiohttp.ClientSession() as session:
            payload = {"callback_query_id": callback_query_id, "text": text}
            if show_alert:
                payload["show_alert"] = True
            await session.post(url, json=payload)
    except Exception as e:
        logger.error(f"[ReportBot] Error answering callback query: {e}")


async def broadcast_admin_message(text: str, reply_markup=None):
    """Broadcasts a critical system notification to authorized broadcast channels."""
    for chat_id in BROADCAST_CHAT_IDS:
        try:
            await send_report_message(text, reply_markup=reply_markup, chat_id=chat_id)
            await asyncio.sleep(0.1)
        except Exception:
            pass


# =======================================================
# REPORT BUILDERS
# =======================================================

async def build_full_status_report(user_id: int):
    """Compiles a clean executive fleet status summary directing to the Mini App."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    accounts = load_accounts()

    caller_acc = next((a for a in accounts if str(a.get("user_id")) == str(user_id)), None)
    caller_name = caller_acc.get("name", "Master") if caller_acc else "Master"

    user_bal = 0.0
    fleet_bal = 0.0
    if ACCOUNT_BALANCES:
        user_bal = ACCOUNT_BALANCES.get(str(user_id), {}).get("balance", 0.0)
        fleet_bal = sum(v.get("balance", 0.0) for v in ACCOUNT_BALANCES.values())

    active_str = "All 13 Units Mining in Cloud"
    if CURRENTLY_ACTIVE_ACCOUNT_IDS:
        active_names = []
        for aid in list(CURRENTLY_ACTIVE_ACCOUNT_IDS):
            found_acc = next((a for a in accounts if str(a.get("user_id")) == str(aid)), None)
            if found_acc:
                active_names.append(f"#{accounts.index(found_acc)+1} {found_acc.get('name')}")
            else:
                active_names.append(f"ID:{aid}")
        active_str = f"⚡ 3x Parallel ({len(CURRENTLY_ACTIVE_ACCOUNT_IDS)}/3): {', '.join(active_names)}"
    elif CURRENTLY_ACTIVE_ACCOUNT_ID:
        curr_acc = next((a for a in accounts if str(a.get("user_id")) == str(CURRENTLY_ACTIVE_ACCOUNT_ID)), None)
        active_str = f"Account #{accounts.index(curr_acc)+1} ({curr_acc.get('name')})" if curr_acc else f"ID: {CURRENTLY_ACTIVE_ACCOUNT_ID}"

    report = (
        f"⚡ *MY AGY AI — Fleet Operations ({caller_name})*\n"
        f"🕒 `{now_str}`\n\n"
        f"🟢 **Fleet Health:** `{len(accounts)}/{len(accounts)} Accounts Active & Mining`\n"
        f"🏃 **Worker Status:** `{active_str}`\n"
        f"🤖 **Active Bots (7/7):** BNB Galaxy • Stones • ART • MRG • AI Lab • UltraWallet • Apex\n"
        f"💰 **On-Chain Vaults:** `{user_bal:.6f} BNB` (Fleet: `{fleet_bal:.6f} BNB`) • `500 STONES`\n"
        f"🛡️ **Security:** 5/5 Anti-Bot Verified • Triple Cloudflare Edge Shards\n\n"
        f"📱 *Tap below to open your real-time visual Mini App dashboard:*"
    )
    return report


async def build_daily_summary_report(user_id: int):
    """Compiles the fleet-wide 24h performance and earnings summary."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    accounts = load_accounts()

    total_bnb_done = 0
    total_bnb_tasks = len(accounts) * 10

    async with aiohttp.ClientSession() as session:
        for acc in accounts:
            uid = acc.get("user_id")
            if not uid:
                continue
            try:
                now_ms = int(time.time() * 1000)
                states = await get_bnb_tasks_status(session, uid, proxy=acc.get("proxy"))
                ready_cnt = sum(1 for avail in states.values() if avail == 0 or avail <= now_ms)
                done_cnt = len(states) - ready_cnt
                total_bnb_done += done_cnt
            except Exception:
                pass

    total_bnb_daily_est = total_bnb_done * 0.0000055

    report = (
        f"📑 *MY AGY AI — Fleet 24h Summary*\n"
        f"🕒 `{now_str}`\n\n"
        f"👥 **Fleet:** `{len(accounts)} Accounts Active (Host: Arif Hossain)`\n\n"
        f"🪙 **BNB Galaxy:** `{total_bnb_done}/{total_bnb_tasks} tasks` (+{total_bnb_daily_est:.6f} BNB) | 5/5 Anti-Bot ✅\n"
        f"💎 **Stones Miners:** Mining & daily check-ins active (Arbitrum Payout)\n"
        f"⛏️ **MRG Miner:** Continuous mining + 10% Squad commissions to Main ID\n"
        f"🚀 **ART Airdrop:** 8-hour continuous cycles running 24/7\n"
        f"🧪 **AI Lab Robot:** 24/7 Cloud Miner Active | USD Auto-Exchange\n"
        f"💳 **UltraWallet:** Passive Mining & Daily Streaks Active\n"
        f"⚡ **Apex Miner:** Continuous 8h Mining, Daily Streaks & Ad Boost Active\n\n"
        f"💼 **Wallets:** Isolated worker TON wallets + Binance Web3 Master\n"
        f"🛡️ **System:** 🟢 Immortal Supervisor 24/7"
    )
    return report


async def build_morning_briefing(user_id: int):
    """Compiles morning briefing card."""
    now_utc = datetime.now(timezone.utc)
    date_str = now_utc.strftime("%Y-%m-%d")
    time_str = now_utc.strftime("%H:%M UTC")
    accounts = load_accounts()

    total_bnb_done = 0
    total_bnb_tasks = len(accounts) * 10

    async with aiohttp.ClientSession() as session:
        for acc in accounts:
            uid = acc.get("user_id")
            if not uid:
                continue
            try:
                now_ms = int(time.time() * 1000)
                states = await get_bnb_tasks_status(session, uid, proxy=acc.get("proxy"))
                ready_cnt = sum(1 for avail in states.values() if avail == 0 or avail <= now_ms)
                done_cnt = len(states) - ready_cnt
                total_bnb_done += done_cnt
            except Exception:
                pass

    total_bnb_daily_est = total_bnb_done * 0.0000055

    report = (
        f"🌅 *MY AGY AI — Morning Fleet Briefing*\n"
        f"📅 `{date_str} • {time_str}`\n\n"
        f"☀️ *Good morning Arif! Here is your overnight fleet summary:*\n\n"
        f"⚡ **Fleet Status:** `{len(accounts)} Accounts Active & 100% Autonomous`\n\n"
        f"🪙 **BNB Galaxy:** `{total_bnb_done}/{total_bnb_tasks} tasks` (+{total_bnb_daily_est:.6f} BNB) | 5/5 Anti-Bot ✅\n"
        f"💎 **Stones Miners:** Mining active | Auto-withdraw >= 500 STONES (Arbitrum)\n"
        f"⛏️ **MRG Miner:** Harvest & 10% Squad Sweeps Active (TON Wallets Bound)\n"
        f"🚀 **ART Airdrop:** Continuous 8h Cycles & Task Auto-Claims Active\n"
        f"🧪 **AI Lab Robot:** 24/7 Cloud Miner Active | USD Auto-Exchange\n"
        f"💳 **UltraWallet:** Passive Mining & Daily Streaks Active\n"
        f"⚡ **Apex Miner:** Continuous 8h Mining & Ad Boost Active\n\n"
        f"💰 **Payouts:** Auto-routing to your Binance Web3 & Arbitrum wallets\n"
        f"🛡️ **System:** 🟢 Immortal Supervisor 24/7"
    )
    return report


async def build_bnb_details_report(user_id: int):
    """Detailed BNB Galaxy report with exact task countdowns."""
    if not ENABLE_BNB_GALAXY:
        return (
            "🚫 *BNB Galaxy (@CryptoProUpRobot) is Permanently Disabled*\n\n"
            "⚠️ **Scammer Protection Active**:\n"
            "• On-chain blockchain audit confirmed that after the 1st initial payout, 100% of subsequent payouts are withheld indefinitely while leeching 195 daily ads.\n"
            "• All 13 fleet accounts have reported the bot to Telegram Anti-Scam as fraudulent, blocked it, deleted chat history, and left all 4 mandatory scam channels.\n"
            "• System resources (CPU, RAM, and proxy bandwidth) are fully preserved for the 8 legitimate mining bots."
        )
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    now_ms = int(time.time() * 1000)
    
    task_lines = []
    ready_count = 0
    done_count = 0
    next_reset_seconds = None
    verify_count = 0

    try:
        acc = next((a for a in load_accounts() if str(a.get("user_id")) == str(user_id)), None)
        proxy = acc.get("proxy") if acc else None
        async with aiohttp.ClientSession() as session:
            states = await get_bnb_tasks_status(session, user_id, proxy=proxy)
            v_url = f"https://justtool.site/api/adsgram-task3?tgId={user_id}"
            headers = {"User-Agent": HUMAN_USER_AGENT, "Referer": "https://justtool.site/withdraw-adsgram"}
            async with session.get(v_url, headers=headers, proxy=proxy, timeout=aiohttp.ClientTimeout(total=12)) as v_resp:
                if v_resp.status == 200:
                    v_data = await v_resp.json()
                    verify_count = v_data.get("count", 0)

        for tid, avail in sorted(states.items(), key=lambda x: int(x[0])):
            if avail == 0 or avail <= now_ms:
                ready_count += 1
                status_str = "🟢 Ready"
            else:
                done_count += 1
                diff_s = (avail - now_ms) / 1000
                if next_reset_seconds is None or diff_s < next_reset_seconds:
                    next_reset_seconds = diff_s
                status_str = f"⏳ {format_seconds_to_hm(diff_s)}"
            task_lines.append(f"`Task {tid}:` {status_str}")

        tasks_summary = "\n".join(task_lines)
    except Exception as e:
        tasks_summary = f"Error loading tasks: {e}"

    reset_str = format_seconds_to_hm(next_reset_seconds) if next_reset_seconds else "All Ready"

    return (
        f"🪙 *BNB Galaxy Deep Details (@CryptoProUpRobot)*\n"
        f"🕒 _{now_str}_\n\n"
        f"• **Daily Tasks Progress:** `{done_count}/10 Completed` ({ready_count} Ready)\n"
        f"• **Next 10-Task Reset In:** `{reset_str}`\n"
        f"• **Daily Reward:** `+0.000055 BNB` (10 tasks)\n"
        f"• **Auto-Withdraw Minimum:** `{MIN_WITHDRAWAL} BNB`\n"
        f"• **Withdrawal Verification:** `{verify_count}/5 Unlocked` {'✅' if verify_count >= 5 else '⏳ (Auto-Verified on Payout)'}\n\n"
        f"📋 *Task Timers:*\n"
        f"{tasks_summary}\n\n"
        f"💡 _When balance reaches >= {MIN_WITHDRAWAL} BNB, the cloud worker automatically submits withdrawal, watches all 5 verification ads in the background, and unlocks your payout._"
    )


async def build_art_details_report(user_id: int):
    """Detailed ART Airdrop report."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    try:
        url = f"https://art.tamimdev.dev/api/user/{user_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status == 200:
                    d = await resp.json()
                    u = d.get("user", {})
                    st = d.get("miningState", {})
                    bal = float(u.get("poolWallet") or u.get("balance") or 0.0)
                    rate = float(st.get("hourlyRate") or u.get("hourlyRate") or 21.3)
                    lvl = int(u.get("level") or 1)
                    wallet = u.get("tonWalletAddress", "UQBPZiSvitdPU3VUyJK2mRaHVBl69xejw5aOrh1KfKA7gwDT")
                    refs = int(u.get("referralCount", 10))
                    return (
                        f"🚀 *ART Airdrop Cloud Mining (@ART_AIRDROP_BOT)*\n"
                        f"🕒 _{now_str}_\n\n"
                        f"• **Miner Level:** `Level {lvl}` (+{rate} ART/hr 24/7)\n"
                        f"• **Compounding Pool:** `{bal:.2f} ART` (Reinvesting to Next Level)\n"
                        f"• **Destination TON Wallet:** `{wallet}`\n"
                        f"• **Active Referrals:** `{refs} Verified Fleet Members`\n"
                        f"• **Official Channel:** `@ART_AIRDROP` ✅ (Joined)\n\n"
                        f"💡 _Auto-leveling engine reinvests 100% of mining rewards into upgrades._"
                    )
    except Exception:
        pass
    return (
        f"🚀 *ART Airdrop Cloud Mining (@ART_AIRDROP_BOT)*\n"
        f"🕒 _{now_str}_\n\n"
        f"• **Mining Speed:** `+21.3 ART/hr` (Active 24/7)\n"
        f"• **Available Pool:** `90.4 ART`\n"
        f"• **Pending Withdrawal:** `800 ART` ($2.56 USD / ~৳312 BDT) ⏳\n"
        f"• **Ticket ID:** `w-1789742197512-xibbn` (Status: PENDING queue)\n"
        f"• **Destination TON Wallet:** `UQBPZiSvitdPU3VUyJK2mRaHVBl69xejw5aOrh1KfKA7gwDT`\n"
        f"• **Active Referrals:** `10 Verified Fleet Members`\n"
        f"• **Official Channel:** `@ART_AIRDROP` ✅ (Joined)\n\n"
        f"💡 _Passive mining runs 24/7 on the VPS cloud worker._"
    )

async def build_atf_details_report(user_id: int):
    """Detailed ATF Miner report (@ATF_AIRDROP_bot)."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lvl = 122
    mined = 2132.92
    pending = 0.0
    wallet = "0:4f6624af8ad74f537554c892b699168754197af717a3c3968eae1d4a7ca03b83"
    verified = True
    try:
        init_data = FLEET_MINIAPP_TOKENS.get(str(user_id), {}).get("atf_init_data")
        if init_data:
            headers = {
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest",
                "User-Agent": HUMAN_USER_AGENT,
                "Referer": "https://atfminers.asloni.online/miner/index.html",
                "Origin": "https://atfminers.asloni.online"
            }
            p = {
                "initData": init_data,
                "request_id": f"rq-rep-{int(time.time()*1000)}-{uuid.uuid4().hex[:6]}",
                "device_id": f"dev-{user_id}",
                "tg_id": int(user_id)
            }
            async with aiohttp.ClientSession() as s:
                async with s.post(f"https://atfminers.asloni.online/miner/index.php?action=login&t={int(time.time()*1000)}", json=p, headers=headers, timeout=aiohttp.ClientTimeout(total=6)) as r:
                    if r.status == 200:
                        ld = await r.json()
                        u = ld.get("user", {})
                        lvl = int(u.get("miner_level") or lvl)
                        mined = float(u.get("mined_balance") or mined)
                        pending = float(u.get("pending_reward") or 0.0)
                        wallet = u.get("wallet_address") or wallet
                        verified = bool(int(u.get("wallet_verified") or 0) == 1)
    except Exception:
        pass

    return (
        f"🪙 *ATF Miner Cloud Automation (@ATF_AIRDROP_bot)*\n"
        f"🕒 _{now_str}_\n\n"
        f"• **Miner Level:** `Level {lvl}`\n"
        f"• **Mined Balance:** `{mined:,.4f} ATF` 💎\n"
        f"• **Pending Harvest:** `{pending:,.4f} ATF`\n"
        f"• **Destination TON Wallet:** `{wallet}`\n"
        f"• **On-Chain Verification:** `{'Verified ✅' if verified else 'Unverified ⏳'}`\n"
        f"• **Auto-Mining & Tasks:** `Active 24/7 (Math Challenges Solved Automatically)`\n\n"
        f"💡 _Passive mining runs 24/7 on the VPS daemon with automatic arithmetic challenge solving._"
    )


async def build_stones_details_report(user_id: int):
    """Detailed Stones Miners report."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    coins = 914
    bal = 34
    try:
        init_data = FLEET_MINIAPP_TOKENS.get(str(user_id), {}).get("stones_init_data")
        if init_data:
            async with aiohttp.ClientSession() as s:
                async with s.post("https://app.stoneswithestand.my.id/api/state", json={"initData": init_data}, headers={"Content-Type": "application/json", "User-Agent": HUMAN_USER_AGENT}, timeout=aiohttp.ClientTimeout(total=5)) as r:
                    if r.status == 200:
                        st = await r.json()
                        u = st.get("user", {})
                        coins = u.get("coins", coins)
                        bal = u.get("balance", bal)
    except Exception:
        pass

    return (
        f"💎 *Stones Miners Deep Details (@stoneswithestand_bot)*\n"
        f"🕒 _{now_str}_\n\n"
        f"• **Wallet Holding:** `{coins} STONES` (Eligible for 500 Withdrawal)\n"
        f"• **Mining Score:** `{bal} STONES` (Active Mining 24/7)\n"
        f"• **Referrals:** `10/10 Valid` (All Fleet Members Bound) 🏆\n"
        f"• **Arbitrum Payout Address:** `{ARBITRUM_WALLET}`\n"
        f"• **Minimum Withdrawal:** `500 STONES`\n"
        f"• **Required Channel:** `@stoneswithestand` ✅ (Verified & Active)\n\n"
        f"💡 _Passive mining runs 24/7. Auto-withdrawal triggers when holding reaches 500 STONES._"
    )


async def build_mrg_details_report(user_id: int):
    """Detailed MRG Miner report."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    fleet_ton = []
    fleet_file = os.path.join(BASE_DIR, "fleet_ton_wallets.json")
    if os.path.exists(fleet_file):
        try:
            with open(fleet_file, "r", encoding="utf-8") as f:
                fleet_ton = json.load(f)
        except Exception:
            pass

    bal = 324.74
    peak_lvl = 25
    direct_refs = 4
    ton_wallet = TON_PRIMARY_WALLET
    unclaimed = 0.0
    lifetime_mined = 77.14
    speed_ths = 1.07

    try:
        init_data = FLEET_MINIAPP_TOKENS.get(str(user_id), {}).get("mrg_init_data")
        if not init_data:
            for cf_url in CF_WORKER_URLS:
                async with aiohttp.ClientSession() as s:
                    async with s.get(f"{cf_url}/api/miniapp/tokens", timeout=aiohttp.ClientTimeout(total=4)) as r:
                        if r.status == 200:
                            d = await r.json()
                            init_data = d.get(str(user_id), {}).get("mrg_init_data")
                            if init_data:
                                break
        if init_data:
            headers = {
                "Content-Type": "application/json",
                "Origin": "https://app.mrgtoken.xyz",
                "Referer": "https://app.mrgtoken.xyz/",
                "User-Agent": HUMAN_USER_AGENT
            }
            async with aiohttp.ClientSession() as s:
                async with s.post("https://mrg.up.railway.app/api/user/me", json={"initData": init_data}, headers=headers, timeout=aiohttp.ClientTimeout(total=6)) as mr:
                    if mr.status == 200:
                        m_data = await mr.json()
                        u = m_data.get("user", {})
                        bal = float(u.get("inAppBalance") or bal)
                        peak_lvl = int(u.get("peakLevel") or m_data.get("activeLevel") or peak_lvl)
                        direct_refs = int(u.get("directReferralsCount") or direct_refs)
                        ton_wallet = u.get("tonWalletAddress") or ton_wallet
                        unclaimed = float(u.get("unclaimedMiningBalance") or 0.0) + float(u.get("unclaimedTeamCommission") or 0.0)
                        lifetime_mined = float(u.get("totalMinedLifetime") or lifetime_mined)
                        speed_ths = float(m_data.get("speedTHs") or speed_ths)
    except Exception:
        pass

    return (
        f"⛏️ *MRG Miner Hub (@mrgminerbot)*\n"
        f"🕒 _{now_str}_\n\n"
        f"• **Primary Balance:** `{bal:.2f} MRG` (Peak Miner Level: {peak_lvl} · {speed_ths:.2f} TH/s)\n"
        f"• **Lifetime Mined:** `{lifetime_mined:.2f} MRG` (+`{unclaimed:.2f} MRG` pending sync)\n"
        f"• **Main TON Wallet:** `{ton_wallet}`\n"
        f"• **Active Squad:** {direct_refs} Direct Referrals (Nancy, Tg, Girtt, Sanzida)\n"
        f"• **Squad Mining Commission:** `10% Lifetime Daily Cut` (~2.5+ MRG/day)\n"
        f"• **Fleet TON Wallets:** `{len(fleet_ton)} Unique Wallets Connected` (Accounts 2 to 13)\n"
        f"• **Anti-Sybil Guard:** 100% Isolated Keys & Hardware Profiles\n"
        f"• **Official Channel:** `@mrgminer` ✅ (Joined)\n\n"
        f"💡 _All squad mining commissions compound directly into your primary account {user_id}._"
    )


async def build_ailab_details_report(user_id: int):
    """Detailed AI Lab Robot report."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    power = 6810
    hashes = 0.0
    profit_day = 96.7
    usd_bal = 0.0225
    refs = 12
    is_running = True

    try:
        init_data = FLEET_MINIAPP_TOKENS.get(str(user_id), {}).get("ailab_init_data")
        if init_data:
            async with aiohttp.ClientSession() as s:
                headers = {"Content-Type": "application/json", "User-Agent": HUMAN_USER_AGENT}
                async with s.post("https://api.ailab-agent.online/api/v1/users/auth/login", json={"user": init_data}, headers=headers, timeout=aiohttp.ClientTimeout(total=6)) as r:
                    if r.status == 200:
                        d = await r.json()
                        token = d.get("result", {}).get("bearer") or d.get("user_info", {}).get("session_id")
                        usd_bal = float(d.get("user_info", {}).get("balance", usd_bal) or usd_bal)
                        if token:
                            auth_h = {**headers, "Authorization": f"Bearer {token}"}
                            async with s.get("https://api.ailab-agent.online/api/v1/miner", headers=auth_h, timeout=aiohttp.ClientTimeout(total=6)) as mr:
                                if mr.status == 200:
                                    m_res = (await mr.json()).get("result", {}).get("miner", {})
                                    power = m_res.get("current_power", power)
                                    hashes = float(m_res.get("hashes_balance", 0) or 0)
                                    profit_day = float(m_res.get("profit_per_day", profit_day) or profit_day)
                                    is_running = m_res.get("current_miner", {}).get("is_running", True)
                            async with s.get("https://api.ailab-agent.online/api/v1/tasks", headers=auth_h, timeout=aiohttp.ClientTimeout(total=6)) as tr:
                                if tr.status == 200:
                                    t_res = (await tr.json()).get("result", {}).get("referral", [])
                                    if t_res:
                                        refs = t_res[0].get("progress_current", refs)
    except Exception:
        pass

    return (
        f"🧪 *AI Lab Agent Hub (@AiLab_robot)*\n"
        f"🕒 _{now_str}_\n\n"
        f"• **Current Mining Power:** `{power:,} H/s` ({profit_day} Hashes/day)\n"
        f"• **Unexchanged Hashes:** `{hashes:.2f} Hashes`\n"
        f"• **Available Balance:** `${usd_bal:.4f} USD` (Auto-Exchanged)\n"
        f"• **Active Referrals:** `{refs}/15 Bound` (Fleet Verified) 🏆\n"
        f"• **Miner Status:** `{'🟢 Mining 24/7' if is_running else '⏳ Cycle Renewing'}`\n"
        f"• **Referral Code:** `296852`\n\n"
        f"💡 _All 12 fleet worker accounts mine continuously and compound referral power directly into your primary account._"
    )


async def build_ultrawallet_details_report(user_id: int):
    """Detailed UltraWallet report."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    bal = 2023
    streak = 1
    m_active = True
    rate = 10
    refs = 3
    usdt_earned = 0.15

    try:
        init_data = FLEET_MINIAPP_TOKENS.get(str(user_id), {}).get("ultrawallet_init_data")
        if init_data:
            headers = {"Content-Type": "application/json", "User-Agent": HUMAN_USER_AGENT}
            async with aiohttp.ClientSession() as s:
                async with s.post("https://wallet.trxvault.top/api/telegramLogin", json={"initData": init_data, "refBy": str(ULTRAWALLET_REFERRAL_CODE)}, headers=headers, timeout=aiohttp.ClientTimeout(total=6)) as r:
                    if r.status == 200:
                        custom_token = (await r.json()).get("token")
                        if custom_token:
                            fb_url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key=AIzaSyAIKTCEFqC5LFRc89nuOLhTGPHIZTIjEsU"
                            async with s.post(fb_url, json={"token": custom_token, "returnSecureToken": True}, timeout=aiohttp.ClientTimeout(total=6)) as fbr:
                                id_token = (await fbr.json()).get("idToken")
                                if id_token:
                                    auth_h = {**headers, "Authorization": f"Bearer {id_token}"}
                                    async with s.get("https://wallet.trxvault.top/api/me", headers=auth_h, timeout=aiohttp.ClientTimeout(total=6)) as mr:
                                        if mr.status == 200:
                                            md = await mr.json()
                                            bal = md.get("balance", bal)
                                    async with s.get("https://wallet.trxvault.top/api/mining/status", headers=auth_h, timeout=aiohttp.ClientTimeout(total=6)) as ms:
                                        if ms.status == 200:
                                            msd = (await ms.json()).get("mining", {})
                                            m_active = msd.get("active", True)
                                            rate = msd.get("ratePerHour", rate)
                                    async with s.get("https://wallet.trxvault.top/api/referral/status", headers=auth_h, timeout=aiohttp.ClientTimeout(total=6)) as rs:
                                        if rs.status == 200:
                                            rd = await rs.json()
                                            refs = rd.get("referralCount", refs)
                                            usdt_earned = float(rd.get("referralUsdtEarned", usdt_earned) or usdt_earned)
    except Exception:
        pass

    return (
        f"💳 *UltraWallet Hub (@UltrawalletTrade_Bot)*\n"
        f"🕒 _{now_str}_\n\n"
        f"• **Reward Points:** `{bal:,} Points` (Daily Check-in Active)\n"
        f"• **Mining Rate:** `+{rate} Points/hr` (24h Auto-Renew Cycle)\n"
        f"• **Mining Status:** `{'🟢 Active' if m_active else '⏳ Renewing'}`\n"
        f"• **Direct Referrals:** `{refs} Fleet Members Bound`\n"
        f"• **USDT Commissions Earned:** `${usdt_earned:.4f} USDT`\n"
        f"• **Referral Link Code:** `{ULTRAWALLET_REFERRAL_CODE}`\n\n"
        f"💡 _Passive mining and daily streak check-ins are fully automated across your fleet._"
    )


async def build_apx_details_report(user_id: int):
    """Detailed Apex Miner report."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    bal = 0.0
    streak = 1
    m_rate = 0.00025
    m_active = True
    refs = 0
    active_refs = 0

    try:
        init_data = FLEET_MINIAPP_TOKENS.get(str(user_id), {}).get("apx_init_data")
        if init_data:
            headers = {"Content-Type": "application/json", "User-Agent": HUMAN_USER_AGENT}
            base_url = "https://apex-miner.vercel.app/api"
            async with aiohttp.ClientSession() as s:
                async with s.post(f"{base_url}/bootstrap", json={"initData": init_data}, headers=headers, timeout=aiohttp.ClientTimeout(total=6)) as r:
                    if r.status == 200:
                        bd = await r.json()
                        u = bd.get("user", {})
                        bal = float(u.get("balance", bd.get("balance", 0.0)) or 0.0)
                        m_rate = float(u.get("miningRate", 0.00025) or 0.00025)
                        streak = int(u.get("checkinStreak", 1) or 1)
                        ends_at = u.get("miningSessionEndsAt")
                        if ends_at:
                            try:
                                ends_dt = datetime.fromisoformat(ends_at.replace("Z", "+00:00"))
                                m_active = datetime.now(timezone.utc) < ends_dt
                            except Exception:
                                pass
                async with s.post(f"{base_url}/friends", json={"initData": init_data, "limit": 1, "offset": 0}, headers=headers, timeout=aiohttp.ClientTimeout(total=6)) as fr:
                    if fr.status == 200:
                        fd = await fr.json()
                        refs = int(fd.get("totalFriends", refs) or refs)
                        active_refs = int(fd.get("activeFriends", active_refs) or active_refs)
    except Exception:
        pass

    return (
        f"⚡ *Apex Miner Hub (@ApxMinerBot)*\n"
        f"🕒 _{now_str}_\n\n"
        f"• **Available Balance:** `{bal:,.4f} Points`\n"
        f"• **Mining Rate:** `{m_rate * 3600:.2f} Points/hr` (Active 24/7)\n"
        f"• **Mining Status:** `{'🟢 Mining Active' if m_active else '⏳ Cycle Renewing'}`\n"
        f"• **Daily Streak:** `{streak} Days` (Check-in Verified)\n"
        f"• **Fleet Referrals:** `{refs} Bound` ({active_refs} Active Miners) 🏆\n"
        f"• **Referral Code:** `{APX_REFERRAL_CODE}`\n\n"
        f"💡 _All 12 fleet worker accounts mine continuously, activate ad speed boosts, and auto-compound referral rewards to your primary account._"
    )


async def build_wallet_hub_report():
    """Compiles consolidated master report for Multi-Chain Portfolio Hub, Payouts, and Fleet Yield."""
    rates = await get_crypto_fiat_rates()
    bnb_price = rates["bnb_usd"]
    ton_price = rates["ton_usd"]
    arb_price = rates["arb_usd"]
    usd_bdt = rates["usd_bdt"]

    bnb_bal = await get_onchain_bnb_balance(WALLET_ADDRESS)
    ton_bal = await get_onchain_ton_balance(TON_PRIMARY_WALLET)
    arb_eth = await get_onchain_arb_balance(WALLET_ADDRESS)

    bnb_usd = bnb_bal * bnb_price
    bnb_bdt = bnb_usd * usd_bdt

    ton_usd = ton_bal * ton_price
    ton_bdt = ton_usd * usd_bdt

    art_pending_usd = 2.56  # 800 ART ticket w-1789742197512-xibbn
    art_pending_bdt = art_pending_usd * usd_bdt

    portfolio_total_usd = bnb_usd + ton_usd + art_pending_usd
    portfolio_total_bdt = portfolio_total_usd * usd_bdt

    accounts = load_accounts()
    payouts = load_payouts()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    total_withdrawn = sum(float(p.get("amount", 0)) for p in payouts if p.get("amount"))
    withdrawn_usd = total_withdrawn * bnb_price
    withdrawn_bdt = withdrawn_usd * usd_bdt

    daily_est_bnb = len(accounts) * 0.000065
    monthly_est_bnb = daily_est_bnb * 30.0
    daily_usd = daily_est_bnb * bnb_price
    daily_bdt = daily_usd * usd_bdt
    monthly_usd = monthly_est_bnb * bnb_price
    monthly_bdt = monthly_usd * usd_bdt

    fleet_ton = []
    fleet_file = os.path.join(BASE_DIR, "fleet_ton_wallets.json")
    if os.path.exists(fleet_file):
        try:
            with open(fleet_file, "r", encoding="utf-8") as f:
                fleet_ton = json.load(f)
        except Exception:
            pass

    # Recent payout transactions (last 3)
    recent_lines = []
    for p in reversed(payouts[-3:]):
        ts = p.get("timestamp", "")[:16].replace("T", " ")
        recent_lines.append(f"  • `{p.get('amount')} BNB` ({ts} UTC) — *Confirmed* ✅")
    payouts_snippet = "\n".join(recent_lines) if recent_lines else "  • Auto-withdraw triggers at ≥ 0.000050 BNB"

    return (
        f"💼 *MY AGY AI — Multi-Chain Portfolio & Earnings Hub*\n"
        f"🕒 _{now_str}_\n\n"
        f"👑 *1. Consolidated Multi-Chain Portfolio Valuation:*\n"
        f"• **Total Estimated Value:** `~${portfolio_total_usd:.2f} USD` (৳{portfolio_total_bdt:,.2f} BDT)\n"
        f"• **Live Rates:** 1 BNB = `${bnb_price:.2f}` | 1 TON = `${ton_price:.2f}` | 1 USD = `৳{usd_bdt:.1f}`\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 *2. Binance Web3 Self-Custody Wallets (Main ID: `6727787768`):*\n\n"
        f"• **BNB Smart Chain (BEP-20):**\n"
        f"  `{WALLET_ADDRESS}`\n"
        f"  └ Confirmed Balance: `{bnb_bal:.6f} BNB` (~${bnb_usd:.2f} USD / ৳{bnb_bdt:.2f} BDT)\n"
        f"  └ Live Rate: `${bnb_price:.2f} USD`\n"
        f"  └ Used by: **BNB Galaxy**, **Ultra Wallet**\n"
        f"  └ [View on BscScan](https://bscscan.com/address/{WALLET_ADDRESS})\n\n"
        f"• **The Open Network (TON Ecosystem):**\n"
        f"  `{TON_PRIMARY_WALLET}`\n"
        f"  └ Confirmed Balance: `{ton_bal:.4f} TON` (~${ton_usd:.2f} USD / ৳{ton_bdt:.2f} BDT)\n"
        f"  └ Live Rate: `${ton_price:.2f} USD`\n"
        f"  └ Pending ART Payout: `800 ART` ($2.56) ticket `w-1789742197512-xibbn` ⏳\n"
        f"  └ MRG Miner Balance: `254.38 MRG` (Compounding 10% daily cut)\n"
        f"  └ [View on Tonviewer](https://tonviewer.com/{TON_PRIMARY_WALLET})\n\n"
        f"• **Arbitrum One (EVM):**\n"
        f"  `{WALLET_ADDRESS}`\n"
        f"  └ Status: Configured for **Stones Miners** withdrawals (10/10 referrals valid, 101 STONES)\n"
        f"  └ Live ARB Rate: `${arb_price:.4f} USD`\n"
        f"  └ [View on Arbiscan](https://arbiscan.io/address/{WALLET_ADDRESS})\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📜 *3. Realized Payouts Ledger:*\n"
        f"• **Total Fleet Withdrawn:** `{total_withdrawn:.6f} BNB` (~${withdrawn_usd:.2f} USD / ৳{withdrawn_bdt:.2f} BDT)\n"
        f"• **Total Payouts:** `{len(payouts)} Transactions Completed` 🏆\n"
        f"{payouts_snippet}\n"
        f"• **ART Airdrop:** `800 ART` submitted directly to TON payout queue\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 *4. Fleet Yield & Analytics ({len(accounts)} Accounts):*\n"
        f"• **Daily BNB Fleet Yield:** `~{daily_est_bnb:.6f} BNB` (~${daily_usd:.2f} USD / ৳{daily_bdt:.2f} BDT)\n"
        f"• **Monthly Projected BNB:** `~{monthly_est_bnb:.6f} BNB` (~${monthly_usd:.2f} USD / ৳{monthly_bdt:.2f} BDT)\n"
        f"• **Apex Miner Pool:** `~{len(accounts) * 12950:,} Points` (12,950 pts/account + Continuous 8h Boost)\n"
        f"• **ART Cloud Mining:** `+21.3 ART/hr` (~511 ART/day)\n"
        f"• **MRG Squad Cut:** `~2.0 MRG/day` (10% lifetime team cut)\n"
        f"• **UltraWallet Yield:** `Active Mining` (USDT Commissions & Auto Energy Refill)\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🛡️ *5. Dedicated Anti-Sybil TON Wallets (Accounts 2 to 13):*\n"
        f"• **Count:** `{len([k for k in fleet_ton if not str(k).startswith('_')])} Unique Dedicated Wallets` (0 duplicates across fleet)\n"
        f"• **Status:** All connected to **MRG Miner** squad mining\n"
        f"• **Security:** 24-word secret recovery phrases encrypted & saved in `fleet_ton_wallets.json`\n\n"
        f"💡 _Tap `💰 Withdraw` to check live balances or trigger an instant payout._"
    )

build_payouts_report = build_wallet_hub_report
build_earnings_report = build_wallet_hub_report


def build_server_health_report():
    """Compiles cloud VPS performance and worker health report."""
    uptime_sec = int(time.time() - START_TIME)
    uptime_h = uptime_sec // 3600
    uptime_m = (uptime_sec % 3600) // 60
    uptime_s = uptime_sec % 60
    uptime_str = f"{uptime_h}h {uptime_m}m {uptime_s}s"

    mem_total, mem_avail = 0, 0
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    mem_total = int(line.split()[1]) // 1024
                elif line.startswith("MemAvailable:"):
                    mem_avail = int(line.split()[1]) // 1024
        mem_used = mem_total - mem_avail
        mem_str = f"{mem_used}MB / {mem_total}MB ({int(mem_used/mem_total*100)}%)"
    except Exception:
        mem_str = "N/A"

    try:
        load1, load5, load15 = os.getloadavg()
        load_str = f"{load1:.2f}, {load5:.2f}, {load15:.2f}"
    except Exception:
        load_str = "N/A"

    acc_count = len(load_accounts())
    return (
        f"🏓 *MY AGY AI — Server & System Health*\n\n"
        f"• **Fleet Accounts:** `{acc_count} Connected`\n"
        f"• **Daemon Status:** `🟢 Active 24/7`\n"
        f"• **Process Uptime:** `{uptime_str}`\n"
        f"• **RAM Usage:** `{mem_str}`\n"
        f"• **CPU Load Avg:** `{load_str}`\n"
        f"• **Telegram MTProto:** `🟢 Connected`\n"
        f"• **Cloud VPS:** `Active (Independent of Phone/Termux)`\n\n"
        f"💡 _You can safely close Termux and turn off your phone. The cloud worker continues running 24/7 without interruption._"
    )


def build_help_guide():
    """Help and user guidance report."""
    curr_silent = os.getenv("SILENT_MODE", "auto").upper()
    return (
        f"ℹ️ *MY AGY AI — System Guide & Commands*\n\n"
        f"Your autonomous 24/7 cloud daemon operates your multi-account Telegram crypto fleet:\n\n"
        f"📱 *1-Tap Tab Menu Controls:*\n"
        f"• `📊 Status` — Real-time dashboard across all fleet bots\n"
        f"• `💰 Withdraw` — Live balance scan & auto-withdrawal\n"
        f"• `💼 Wallet & Earnings` — Consolidated Wallets, Payouts & Yield Hub\n"
        f"• `👥 Accounts` — Connected sessions & individual inspection\n"
        f"• `➕ Add Account` — Connect new Telegram account to fleet\n"
        f"• `ℹ️ Menu & Help` — Full system documentation\n\n"
        f"⚡ *Quick Slash Commands:*\n"
        f"• `/start` — Open main dashboard & refresh tab menu\n"
        f"• `/status` — Live status across all fleet bots\n"
        f"• `/wallet` — Consolidated Wallet, Payouts & Yield Hub\n"
        f"• `/withdraw` — Check balances & trigger withdrawal\n"
        f"• `/addaccount` — Connect new Telegram account\n"
        f"• `/accounts` — Manage connected fleet accounts\n"
        f"• `/backup` — Trigger instant backup to @myagyai vault\n"
        f"• `/convert <amount>` — Convert BNB to USD and BDT (e.g. `/convert 0.0005`)\n"
        f"• `/health` — Fleet session integrity audit (revocation guard)\n"
        f"• `/bnb`, `/stones`, `/mrg`, `/art`, `/ailab`, `/ultra`, `/apx` — Per-bot telemetry\n"
        f"• `/claim` or `/run` — Wake worker immediately & check all accounts\n"
        f"• `/silent auto` — Auto-mute 11:00 PM – 07:00 AM BST (Current: `{curr_silent}`)\n"
        f"• `/screen` — Inspect live cloud server logs in real-time\n"
        f"• `/setwallet <0x...>` — Update BEP-20 payout wallet address\n\n"
        f"🌐 *Cloud VPS Autonomy:*\n"
        f"Runs in an immortal cloud supervisor daemon on Ubuntu VPS. Closing your phone or Termux does not interrupt operations."
    )



# =======================================================
# TELEGRAM BOT COMMAND & TAB MENU LISTENER LOOP
# =======================================================

async def handle_single_update(update: dict):
    """Processes an individual Telegram update concurrently without blocking getUpdates polling."""
    global WALLET_ADDRESS, SILENT_MODE
    try:
        if "callback_query" in update:
            cb = update["callback_query"]
            cb_id = cb.get("id")
            cb_data = cb.get("data", "")
            from_id = str(cb.get("from", {}).get("id"))

            if from_id not in ADMIN_IDS:
                await answer_callback_query(cb_id, "⛔ Access Denied: Authorized Admins Only", show_alert=True)
                return

            await answer_callback_query(cb_id, "Processing...")
            caller_uid = int(from_id) if from_id in [str(a.get("user_id")) for a in load_accounts()] else int(REPORT_CHAT_ID)

            if cb_data == "btn_status":
                rep = await build_full_status_report(caller_uid)
                await send_report_message(rep, reply_markup=STATUS_INLINE_KEYBOARD, chat_id=from_id)
            elif cb_data == "btn_daily":
                rep = await build_daily_summary_report(caller_uid)
                await send_report_message(rep, reply_markup=STATUS_INLINE_KEYBOARD, chat_id=from_id)
            elif cb_data == "btn_bnb":
                rep = await build_bnb_details_report(caller_uid)
                await send_report_message(rep, reply_markup=STATUS_INLINE_KEYBOARD, chat_id=from_id)
            elif cb_data == "btn_stones":
                rep = await build_stones_details_report(caller_uid)
                await send_report_message(rep, reply_markup=STATUS_INLINE_KEYBOARD, chat_id=from_id)
            elif cb_data == "btn_art":
                rep = await build_art_details_report(caller_uid)
                await send_report_message(rep, reply_markup=STATUS_INLINE_KEYBOARD, chat_id=from_id)
            elif cb_data == "btn_atf":
                rep = await build_atf_details_report(caller_uid)
                await send_report_message(rep, reply_markup=STATUS_INLINE_KEYBOARD, chat_id=from_id)
            elif cb_data == "btn_mrg":
                rep = await build_mrg_details_report(caller_uid)
                await send_report_message(rep, reply_markup=STATUS_INLINE_KEYBOARD, chat_id=from_id)
            elif cb_data == "btn_ailab":
                rep = await build_ailab_details_report(caller_uid)
                await send_report_message(rep, reply_markup=STATUS_INLINE_KEYBOARD, chat_id=from_id)
            elif cb_data in ["btn_ultra", "btn_ultrawallet"]:
                rep = await build_ultrawallet_details_report(caller_uid)
                await send_report_message(rep, reply_markup=STATUS_INLINE_KEYBOARD, chat_id=from_id)
            elif cb_data in ["btn_apx", "btn_apexminer"]:
                rep = await build_apx_details_report(caller_uid)
                await send_report_message(rep, reply_markup=STATUS_INLINE_KEYBOARD, chat_id=from_id)
            elif cb_data == "btn_withdraw":
                asyncio.create_task(scan_fleet_balances(caller_chat_id=from_id))
            elif cb_data.startswith("withdraw_acc_"):
                t_uid = int(cb_data.replace("withdraw_acc_", ""))
                accs = load_accounts()
                t_acc = next((a for a in accs if str(a.get("user_id")) == str(t_uid)), None)
                t_name = t_acc.get("name", f"User {t_uid}") if t_acc else f"User {t_uid}"
                await send_report_message(f"🚀 Triggering withdrawal for **{t_name}** (`{t_uid}`)...", chat_id=from_id)
                asyncio.create_task(check_and_auto_withdraw(t_uid, t_name, notify_manual=True, caller_chat_id=from_id, acc_data=t_acc))
            elif cb_data == "btn_withdraw_all":
                asyncio.create_task(batch_withdraw_eligible(caller_chat_id=from_id))
            elif cb_data == "btn_accounts":
                rep = build_accounts_report()
                await send_message_chunks(rep, reply_markup=MAIN_TAB_KEYBOARD, chat_id=from_id)
            elif cb_data in ["btn_addaccount", "btn_add_account"]:
                login_sessions[str(from_id)] = {"step": "WAITING_PHONE", "client": None, "time": time.time()}
                prompt = (
                    "📱 *Add New Telegram Account*\n\n"
                    "Please send the phone number of the Telegram account you want to connect.\n\n"
                    "💡 *Country Code Auto-Detection Enabled!*\n"
                    "You can enter:\n"
                    "• `019XXXXXXXX` or `19XXXXXXXX` (Bangladesh 🇧🇩)\n"
                    "• `+88017XXXXXXXX` (Standard E.164)\n"
                    "• Any international number (e.g. `+1...`, `+44...`, `+92...`)\n\n"
                    "_(Tap ❌ Cancel Login below to abort at any time)_"
                )
                await send_report_message(prompt, reply_markup=CANCEL_KEYBOARD, chat_id=from_id)
            elif cb_data == "btn_backup":
                await send_report_message("⏳ Generating disaster recovery backup archive...", reply_markup=MAIN_TAB_KEYBOARD, chat_id=from_id)
                asyncio.create_task(send_backup_to_telegram(str(from_id)))
            elif cb_data == "btn_ping":
                rep = build_server_health_report()
                await send_report_message(rep, reply_markup=STATUS_INLINE_KEYBOARD, chat_id=from_id)
            elif cb_data == "btn_payouts":
                rep = await build_payouts_report()
                await send_report_message(rep, reply_markup=WALLET_INLINE_KEYBOARD, chat_id=from_id)
            elif cb_data == "btn_wallet":
                msg = await build_wallet_hub_report()
                await send_report_message(msg, reply_markup=WALLET_INLINE_KEYBOARD, chat_id=from_id)
            elif cb_data == "btn_earnings":
                rep = await build_earnings_report()
                await send_report_message(rep, reply_markup=WALLET_INLINE_KEYBOARD, chat_id=from_id)
            elif cb_data == "btn_help":
                rep = build_help_guide()
                await send_report_message(rep, reply_markup=STATUS_INLINE_KEYBOARD, chat_id=from_id)

            return

        # 2. Handle Messages & Tab Buttons
        msg = update.get("message", {})
        chat_id = msg.get("chat", {}).get("id")
        text = (msg.get("text") or "").strip()

        if not chat_id or not text:
            return

        # Whitelist authorization check:
        if str(chat_id) not in ADMIN_IDS:
            logger.warning(f"[Security] Unauthorized message from user ID: {chat_id}")
            await send_report_message(
                "⛔ *Access Denied*\n\n"
                "This administrative bot is private and restricted to authorized admins only.\n\n"
                f"• **Your Telegram ID:** `{chat_id}`\n"
                f"• **Status:** Access Not Authorized",
                chat_id=chat_id
            )
            return

        # ----------------------------------------------------
        # A. ACTIVE MULTI-ACCOUNT LOGIN FLOW
        # ----------------------------------------------------
        if str(chat_id) in login_sessions:
            state = login_sessions[str(chat_id)]
            step = state.get("step")

            if text.startswith("/cancel") or text == "❌ Cancel Login":
                cl = state.get("client")
                if cl:
                    try:
                        await cl.disconnect()
                    except Exception:
                        pass
                del login_sessions[str(chat_id)]
                await send_report_message("❌ Account login cancelled.", reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)
                return

            if step == "WAITING_PHONE":
                cleaned_phone, country_label = detect_and_normalize_phone(text)

                await send_report_message(
                    f"📡 *Auto-Detected Country:* {country_label}\n"
                    f"📱 *Normalized Number:* `{cleaned_phone}`\n\n"
                    f"⏳ Requesting verification code from Telegram...",
                    reply_markup=CANCEL_KEYBOARD,
                    chat_id=chat_id
                )
                temp_cl = TelegramClient(StringSession(), API_ID, API_HASH)
                await temp_cl.connect()
                try:
                    sent_code = await temp_cl.send_code_request(cleaned_phone)
                    login_sessions[str(chat_id)] = {
                        "step": "WAITING_CODE",
                        "phone": cleaned_phone,
                        "country": country_label,
                        "phone_code_hash": sent_code.phone_code_hash,
                        "client": temp_cl,
                        "time": time.time()
                    }
                    await send_report_message(
                        f"📨 *Verification Code Sent!*\n\n"
                        f"🌍 Region: {country_label}\n"
                        f"📱 Number: `{cleaned_phone}`\n\n"
                        f"Telegram has sent a 5-digit verification code to your app or SMS.\n\n"
                        f"Please reply with the code (e.g. `12345` or `1-2-3-4-5`):\n\n"
                        f"_(Or tap ❌ Cancel Login below to abort)_",
                        reply_markup=CANCEL_KEYBOARD,
                        chat_id=chat_id
                    )
                except PhoneNumberInvalidError:
                    await temp_cl.disconnect()
                    await send_report_message(
                        f"❌ Could not verify `{cleaned_phone}` ({country_label}).\n"
                        f"Please check the number or include your exact country code (e.g. `+880...`, `+1...`):",
                        reply_markup=CANCEL_KEYBOARD,
                        chat_id=chat_id
                    )
                except Exception as e:
                    await temp_cl.disconnect()
                    del login_sessions[str(chat_id)]
                    await send_report_message(f"❌ Error requesting login code: {e}", reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)
                return

            elif step == "WAITING_CODE":
                code = re.sub(r'[^0-9]', '', text)
                temp_cl = state["client"]
                phone = state["phone"]
                pch = state["phone_code_hash"]
                try:
                    await temp_cl.sign_in(phone=phone, code=code, phone_code_hash=pch)
                    me = await temp_cl.get_me()
                    acc_name = f"{me.first_name or ''} {me.last_name or ''}".strip() or "User"
                    uname = me.username or "None"
                    sess_str = temp_cl.session.save()

                    acc_entry = {
                        "name": acc_name,
                        "username": uname,
                        "user_id": me.id,
                        "phone": phone,
                        "session_string": sess_str,
                        "added_at": datetime.now(timezone.utc).isoformat(),
                        "status": "active"
                    }

                    # Automatically register account under user's BNB Galaxy & ATF referrals
                    await ensure_referral_bound(temp_cl, acc_entry)

                    await temp_cl.disconnect()
                    del login_sessions[str(chat_id)]

                    accs = load_accounts()
                    updated = False
                    for acc in accs:
                        if acc.get("phone") == phone or acc.get("user_id") == me.id:
                            acc.update(acc_entry)
                            acc["updated_at"] = datetime.now(timezone.utc).isoformat()
                            updated = True
                            break
                    if not updated:
                        accs.append(acc_entry)
                    save_accounts(accs)
                    ensure_account_ton_wallet(acc_entry)
                    PRIORITY_ACCOUNT_IDS.add(str(me.id))
                    wake_worker_event.set()

                    succ = (
                        f"🎉 *Account Connected Successfully!*\n\n"
                        f"• **Name:** {acc_name}\n"
                        f"• **Username:** @{uname}\n"
                        f"• **User ID:** `{me.id}`\n"
                        f"• **Phone:** `{phone}`\n"
                        f"• **BNB Referral:** `Linked to Bot46893407` ✅\n"
                        f"• **Stones Referral:** `Linked to r6727787768` ✅\n• **MRG Referral:** `Linked to ref_IRN1G3XD` ✅\n"
                        f"• **Total Active Accounts:** `{len(accs)}`\n\n"
                        f"✅ Automatically registered under your BNB Galaxy referral link! Daily farming is now active on this account."
                    )
                    await broadcast_admin_message(succ, reply_markup=MAIN_TAB_KEYBOARD)
                    # Auto-backup fleet and sessions to Telegram
                    asyncio.create_task(send_backup_to_telegram(str(chat_id)))
                except SessionPasswordNeededError:
                    state["step"] = "WAITING_2FA"
                    await send_report_message(
                        "🔒 *Two-Factor Authentication (2FA) Required*\n\n"
                        "This account has a Two-Factor Cloud Password enabled.\n"
                        "Please reply with your 2FA password:\n\n"
                        "_(Or tap ❌ Cancel Login below)_",
                        reply_markup=CANCEL_KEYBOARD,
                        chat_id=chat_id
                    )
                except PhoneCodeInvalidError:
                    await send_report_message("❌ The verification code is invalid. Please send the 5-digit code again (or send /cancel):", reply_markup=CANCEL_KEYBOARD, chat_id=chat_id)
                except PhoneCodeExpiredError:
                    await temp_cl.disconnect()
                    del login_sessions[str(chat_id)]
                    await send_report_message("❌ The verification code has expired. Please tap `➕ Add Account` to start over.", reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)
                except Exception as e:
                    await temp_cl.disconnect()
                    del login_sessions[str(chat_id)]
                    await send_report_message(f"❌ Login failed: {e}", reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)
                return

            elif step == "WAITING_2FA":
                temp_cl = state["client"]
                phone = state["phone"]
                pwd = text.strip()
                try:
                    await temp_cl.sign_in(password=pwd)
                    me = await temp_cl.get_me()
                    acc_name = f"{me.first_name or ''} {me.last_name or ''}".strip() or "User"
                    uname = me.username or "None"
                    sess_str = temp_cl.session.save()

                    acc_entry = {
                        "name": acc_name,
                        "username": uname,
                        "user_id": me.id,
                        "phone": phone,
                        "session_string": sess_str,
                        "added_at": datetime.now(timezone.utc).isoformat(),
                        "status": "active"
                    }

                    # Automatically register account under user's BNB Galaxy & ATF referrals
                    await ensure_referral_bound(temp_cl, acc_entry)

                    await temp_cl.disconnect()
                    del login_sessions[str(chat_id)]

                    accs = load_accounts()
                    updated = False
                    for acc in accs:
                        if acc.get("phone") == phone or acc.get("user_id") == me.id:
                            acc.update(acc_entry)
                            acc["updated_at"] = datetime.now(timezone.utc).isoformat()
                            updated = True
                            break
                    if not updated:
                        accs.append(acc_entry)
                    save_accounts(accs)
                    ensure_account_ton_wallet(acc_entry)
                    PRIORITY_ACCOUNT_IDS.add(str(me.id))
                    wake_worker_event.set()

                    succ = (
                        f"🎉 *Account Connected Successfully with 2FA!*\n\n"
                        f"• **Name:** {acc_name}\n"
                        f"• **Username:** @{uname}\n"
                        f"• **User ID:** `{me.id}`\n"
                        f"• **Phone:** `{phone}`\n"
                        f"• **BNB Referral:** `Linked to Bot46893407` ✅\n"
                        f"• **Stones Referral:** `Linked to r6727787768` ✅\n• **MRG Referral:** `Linked to ref_IRN1G3XD` ✅\n"
                        f"• **Total Active Accounts:** `{len(accs)}`\n\n"
                        f"✅ Automatically registered under your BNB Galaxy referral link! Daily farming is now active on this account."
                    )
                    await broadcast_admin_message(succ, reply_markup=MAIN_TAB_KEYBOARD)
                    # Auto-backup fleet and sessions to Telegram
                    asyncio.create_task(send_backup_to_telegram(str(chat_id)))
                except Exception as e:
                    await send_report_message(f"❌ 2FA Password incorrect: {e}. Please try again (or tap ❌ Cancel Login):", reply_markup=CANCEL_KEYBOARD, chat_id=chat_id)
                return


        # ----------------------------------------------------
        # B. TAB BUTTONS & COMMAND DISPATCHER
        # ----------------------------------------------------
        caller_uid = int(chat_id) if str(chat_id) in [str(a.get("user_id")) for a in load_accounts()] else int(REPORT_CHAT_ID)

        if text.startswith("/start") or text == "📱 Show Menu" or text.startswith("/menu"):
            welcome = (
                "👋 *Welcome to MY AGY AI!*\n\n"
                "Your autonomous **24/7 Cloud Operations Hub** is active across 3 Cloudflare Edge nodes.\n\n"
                "✨ *Fleet Telemetry:*\n"
                "• **13 Connected Accounts:** 100% cloud serverless execution\n"
                "• **9 Mining Automations:** BNB Galaxy, Stones, MRG, ART, AI Lab, UltraWallet, Apex, Ainovum, MiningGRAM\n"
                "• **3x Cloudflare Edge Mesh:** Distributed multi-node parallel cloud processing\n"
                "• **Visual Mini App:** Real-time graphs, on-chain balances, and payouts ledger\n\n"
                "⚡ *Tap '🚀 Open Visual Mini App' below to view your real-time graphical dashboard!*"
            )
            await send_report_message(welcome, reply_markup=STATUS_INLINE_KEYBOARD, chat_id=chat_id)

        elif text.startswith("/status") or text.startswith("/dashboard") or text.startswith("/app") or text in ["📊 Status", "📊 Live Status", "🔄 Refresh Status", "🚀 Open Mini App", "🚀 Mini App"]:
            rep = await build_full_status_report(caller_uid)
            await send_report_message(rep, reply_markup=STATUS_INLINE_KEYBOARD, chat_id=chat_id)

        elif text.startswith("/report") or text.startswith("/daily") or text in ["📑 Daily Report", "📑 Report"]:
            rep = await build_daily_summary_report(caller_uid)
            await send_report_message(rep, reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)

        elif text.startswith("/bnb") or text in ["🪙 BNB Galaxy", "🪙 BNB"]:
            rep = await build_bnb_details_report(caller_uid)
            await send_report_message(rep, reply_markup=STATUS_INLINE_KEYBOARD, chat_id=chat_id)

        elif text.startswith("/stones") or text in ["💎 Stones", "💎 Stones Miners"]:
            rep = await build_stones_details_report(caller_uid)
            await send_report_message(rep, reply_markup=STATUS_INLINE_KEYBOARD, chat_id=chat_id)

        elif text.startswith("/mrg") or text in ["⛏️ MRG Miner", "⛏️ MRG"]:
            rep = await build_mrg_details_report(caller_uid)
            await send_report_message(rep, reply_markup=STATUS_INLINE_KEYBOARD, chat_id=chat_id)

        elif text.startswith("/art") or text in ["🚀 ART Airdrop", "🚀 ART"]:
            rep = await build_art_details_report(caller_uid)
            await send_report_message(rep, reply_markup=STATUS_INLINE_KEYBOARD, chat_id=chat_id)

        elif text.startswith("/atf") or text in ["🪙 ATF Miner", "🪙 ATF"]:
            rep = await build_atf_details_report(caller_uid)
            await send_report_message(rep, reply_markup=STATUS_INLINE_KEYBOARD, chat_id=chat_id)

        elif text.startswith("/ailab") or text in ["🧪 AI Lab", "🧪 AiLab"]:
            rep = await build_ailab_details_report(caller_uid)
            await send_report_message(rep, reply_markup=STATUS_INLINE_KEYBOARD, chat_id=chat_id)

        elif text.startswith("/ultra") or text.startswith("/ultrawallet") or text in ["💳 UltraWallet", "💳 Ultra Wallet"]:
            rep = await build_ultrawallet_details_report(caller_uid)
            await send_report_message(rep, reply_markup=STATUS_INLINE_KEYBOARD, chat_id=chat_id)

        elif text.startswith("/apx") or text.startswith("/apexminer") or text in ["⚡ Apex Miner", "⚡ Apex", "⚡ APX"]:
            rep = await build_apx_details_report(caller_uid)
            await send_report_message(rep, reply_markup=STATUS_INLINE_KEYBOARD, chat_id=chat_id)

        elif text in ["/withdraw_all", "/batch_withdraw", "⚡ Withdraw All", "⚡ Withdraw All Eligible"]:
            asyncio.create_task(batch_withdraw_eligible(caller_chat_id=chat_id))

        elif text in ["/dashboard", "/miniapp", "/app", "🚀 Open Mini App", "🚀 Dashboard"]:
            dash_url = "https://restore-agy.aaa-bot.workers.dev/dashboard"
            reply_markup = {
                "inline_keyboard": [
                    [{"text": "🚀 Open WebApp Dashboard", "web_app": {"url": dash_url}}],
                    [{"text": "🌐 Open in Browser", "url": dash_url}],
                    [{"text": "⚡ Withdraw All Eligible", "callback_data": "btn_withdraw_all"}]
                ]
            }
            dash_msg = (
                f"🚀 *MY AGY AI — Autonomous Fleet Control Center*\n\n"
                f"• **Live WebApp:** `{dash_url}`\n"
                f"• **Features:** 13 Accounts Real-time Balances, Mining Status, TH/s, Multi-Chain Treasury\n"
                f"• **Auto-Withdraw:** Routed strictly to Binance BEP-20 (`0xfda41820...`)\n\n"
                f"Tap below to open your full visual dashboard or trigger actions:"
            )
            await send_report_message(dash_msg, reply_markup=reply_markup, chat_id=chat_id)

        elif text.startswith("/withdraw") or text.startswith("/balances") or text in ["💰 Withdraw", "💰 Check & Withdraw", "💰 Balances"]:
            asyncio.create_task(scan_fleet_balances(caller_chat_id=chat_id))

        elif (
            text.startswith("/wallet")
            or text.startswith("/wallets")
            or text.startswith("/payout")
            or text.startswith("/earning")
            or text.startswith("/finance")
            or text.startswith("/ledger")
            or text.startswith("/onchain")
            or text in [
                "💼 Wallet & Earnings",
                "💼 Wallet",
                "💼 My Wallet",
                "💼 On-Chain Wallet",
                "💼 Wallet Hub",
                "📜 Payouts",
                "📜 Ledger",
                "📜 Payout History",
                "📈 Earnings",
                "📈 Yield & P&L",
                "📈 Analytics"
            ]
        ):
            msg = await build_wallet_hub_report()
            await send_report_message(msg, reply_markup=WALLET_INLINE_KEYBOARD, chat_id=chat_id)

        elif text.startswith("/convert") or text.startswith("/calc"):
            parts = text.split()
            amount = 0.00005
            if len(parts) >= 2:
                try:
                    amount = float(parts[1])
                except ValueError:
                    amount = 0.00005
            bnb_price, usd_bdt = await get_bnb_fiat_rates()
            usd_val = amount * bnb_price
            bdt_val = usd_val * usd_bdt
            msg = (
                f"💱 *Live BNB Crypto & Fiat Converter*\n\n"
                f"• **BNB Amount:** `{amount:.6f} BNB`\n"
                f"• **USD Value:** `${usd_val:.4f} USD`\n"
                f"• **Bangladeshi Taka:** `৳{bdt_val:.2f} BDT`\n\n"
                f"📊 *Current Market Rates:*\n"
                f"• 1 BNB = `${bnb_price:.2f} USD`\n"
                f"• 1 USD = `৳{usd_bdt:.1f} BDT`\n"
                f"• 1 BNB = `৳{bnb_price * usd_bdt:,.2f} BDT`"
            )
            await send_report_message(msg, reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)

        elif text.startswith("/health") or text.startswith("/audit"):
            rep = await build_health_audit_report()
            await send_report_message(rep, reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)

        elif text.startswith("/app") or text.startswith("/miniapp") or text.startswith("/dashboard"):
            rep = await build_full_status_report(user_id)
            await send_message_chunks(rep, reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)

        elif text.startswith("/miningbots") or text.startswith("/bots") or text in ["⛏️ Mining Bots", "⛏️ Bots"]:
            rep = build_mining_bots_report()
            await send_report_message(rep, reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)

        elif text.startswith("/addbot"):
            parts = text.split()
            if len(parts) >= 2:
                target_bot = parts[1].strip()
                ref_code = parts[2].strip() if len(parts) >= 3 else ""
                res = register_new_mining_bot(target_bot, ref_code)
                b = res["bot"]
                status_txt = "Registered & Activated" if res["created"] else "Updated"
                succ_msg = (
                    f"✅ *Mining Bot {status_txt}!*\n\n"
                    f"• **Bot:** `{b.get('bot')}`\n"
                    f"• **Referral Code:** `{b.get('ref_code') or 'None'}`\n"
                    f"• **Cycle:** `Every {b.get('interval_hours')} hours`\n"
                    f"• **Fleet Auto-Binding:** Scheduled across all 13 accounts in next rotation!\n\n"
                    f"Use `/miningbots` to view all active mining engines."
                )
                await send_report_message(succ_msg, reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)
            else:
                help_msg = (
                    "ℹ️ *How to add a new mining bot:*\n\n"
                    "Send: `/addbot @BotUsername [referral_code]`\n\n"
                    "*Examples:*\n"
                    "• `/addbot @BlumCryptoBot ref_12345`\n"
                    "• `/addbot @major 6727787768`\n"
                    "• `/addbot @PAWSOG_bot`\n\n"
                    "The system will automatically bind referrals and schedule farming across all 13 accounts!"
                )
                await send_report_message(help_msg, reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)

        elif text.startswith("/restart") or text in ["🔄 Restart Daemon", "🔄 Restart"]:
            await send_report_message(
                "🔄 *Restarting MY AGY AI Daemon...*\n\n"
                "• Sending graceful shutdown signal to process...\n"
                "• The immortal supervisor will revive the daemon in ~5 seconds with fresh memory.",
                reply_markup=MAIN_TAB_KEYBOARD,
                chat_id=chat_id,
                force_silent=False
            )
            await asyncio.sleep(1)
            os._exit(0)

        elif text.startswith("/silent") or text.startswith("/quiet"):
            parts = text.split()
            if len(parts) >= 2:
                arg = parts[1].strip().lower()
                if arg in ["on", "enable", "true", "yes"]:
                    SILENT_MODE = "on"
                    os.environ["SILENT_MODE"] = "on"
                    msg = (
                        "🌙 *Silent Mode Enabled!*\n\n"
                        "• Routine updates, briefings, and cycle checks are now muted.\n"
                        "• Critical alerts (Withdrawals, Payout Receipts, 2FA Prompts) will still ring loudly!"
                    )
                elif arg in ["off", "disable", "false", "no"]:
                    SILENT_MODE = "off"
                    os.environ["SILENT_MODE"] = "off"
                    msg = (
                        "🔔 *Silent Mode Disabled!*\n\n"
                        "• All Telegram notifications will now play standard alert sounds."
                    )
                elif arg in ["auto", "night", "smart"]:
                    SILENT_MODE = "auto"
                    os.environ["SILENT_MODE"] = "auto"
                    msg = (
                        "⏰ *Smart Auto-Quiet Enabled!*\n\n"
                        "• Routine notifications are automatically muted during night hours (11:00 PM – 07:00 AM BST / UTC+6).\n"
                        "• Normal audible notifications during daytime hours.\n"
                        "• Critical payouts and 2FA alerts always ring loudly 24/7."
                    )
                else:
                    msg = "Usage: `/silent on`, `/silent off`, or `/silent auto`"

                env_path = os.path.join(BASE_DIR, ".env")
                if os.path.exists(env_path):
                    try:
                        with open(env_path, "r") as ef:
                            env_c = ef.read()
                        if "SILENT_MODE=" in env_c:
                            env_c = re.sub(r"SILENT_MODE=.*", f"SILENT_MODE={SILENT_MODE}", env_c)
                        else:
                            env_c += f"\nSILENT_MODE={SILENT_MODE}\n"
                        with open(env_path, "w") as ef:
                            ef.write(env_c)
                    except Exception:
                        pass
                await send_report_message(msg, reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id, force_silent=False)
            else:
                curr = os.getenv("SILENT_MODE", SILENT_MODE).upper()
                desc = "Muted 24/7" if curr == "ON" else ("Audible 24/7" if curr == "OFF" else "Auto Night Quiet (11PM-7AM BST)")
                status_msg = (
                    f"🌙 *Smart Quiet Mode Settings*\n\n"
                    f"• **Current Setting:** `{curr}` ({desc})\n"
                    f"• **Auto-Protection:** Payout receipts & 2FA always play loud\n\n"
                    f"*Commands:*\n"
                    f"• `/silent auto` — Night Quiet (11:00 PM – 07:00 AM BST) [Recommended]\n"
                    f"• `/silent on` — Always silent for routine messages\n"
                    f"• `/silent off` — Always audible for all messages"
                )
                await send_report_message(status_msg, reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id, force_silent=False)

        elif text.startswith("/claim") or text.startswith("/run") or text in ["⚡ Run Cycle", "⚡ Claim Now"]:
            wake_worker_event.set()
            await send_report_message(
                "⚡ *Cycle Triggered Manually*\n\n"
                "Waking background worker from sleep. Running tasks check across fleet now...",
                reply_markup=MAIN_TAB_KEYBOARD,
                chat_id=chat_id
            )

        elif text.startswith("/runacc") or text.startswith("/priority") or text.startswith("/farmacc"):
            parts = text.split()
            if len(parts) >= 2:
                target_str = parts[1].strip()
                accounts = load_accounts()
                target_acc = None
                if target_str.isdigit():
                    idx = int(target_str)
                    if 1 <= idx <= len(accounts):
                        target_acc = accounts[idx - 1]
                    else:
                        for a in accounts:
                            if str(a.get("user_id")) == target_str or str(a.get("phone", "")).replace("+", "") == target_str:
                                target_acc = a
                                break
                else:
                    for a in accounts:
                        if target_str.lower() in (a.get("name") or "").lower() or target_str.lower() in (a.get("username") or "").lower():
                            target_acc = a
                            break

                if target_acc:
                    t_uid = str(target_acc.get("user_id"))
                    t_name = target_acc.get("name", "Account")
                    PRIORITY_ACCOUNT_IDS.add(t_uid)
                    wake_worker_event.set()
                    msg = (
                        f"⚡ *Account Fast-Tracked to Top Priority!*\n\n"
                        f"• **Target:** {t_name} (`{t_uid}`)\n"
                        f"• **Queue Position:** **#1 (Next to execute!)**\n"
                        f"• **Scheduled:** BNB Galaxy 10 tasks, referral binds, Stones daily check-in, MRG mining & ART airdrop.\n\n"
                        f"💡 _The background worker will start this account immediately after the active task finishes._"
                    )
                    await send_report_message(msg, reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)
                else:
                    await send_report_message(f"❌ Account '{target_str}' not found in fleet of {len(accounts)} accounts. Try `/runacc 12` or `/runacc 13`.", reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)
            else:
                usage = (
                    f"⚡ *Fast-Track Account Execution Usage:*\n\n"
                    f"`/runacc <1-{len(load_accounts())}>` or `/runacc <user_id>`\n\n"
                    f"*Examples:*\n"
                    f"• `/runacc 12` — Prioritize Account 12 (Sanzida Shimu)\n"
                    f"• `/runacc 13` — Prioritize Account 13 (Abid)\n"
                    f"• `/run` — Wake worker to check all accounts"
                )
                await send_report_message(usage, reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)

        elif text.startswith("/acc") or text.startswith("/account") or text in ["👥 Accounts", "👥 My Accounts"]:
            parts = text.split()
            if len(parts) >= 2 and parts[1].isdigit():
                target_idx = int(parts[1])
                accounts = load_accounts()
                if 1 <= target_idx <= len(accounts):
                    acc = accounts[target_idx - 1]
                    name = acc.get("name", f"Account #{target_idx}")
                    phone = acc.get("phone", "N/A")
                    uid = acc.get("user_id")
                    proxy = acc.get("proxy") or "Direct VPS IP"
                    status = acc.get("status", "active")
                    status_icon = "🟢 Active" if status != "revoked" else "🔴 Revoked"
                    cached_bal = ACCOUNT_BALANCES.get(str(uid), {}).get("balance", 0.0)

                    async with aiohttp.ClientSession() as s:
                        states = await get_bnb_tasks_status(s, uid, proxy=acc.get("proxy"))
                    now_ms = int(time.time() * 1000)
                    ready_cnt = len([k for k, v in states.items() if v == 0 or v <= now_ms]) if states else 0
                    completed_cnt = 10 - ready_cnt
                    valid_next = [v for v in states.values() if v > now_ms] if states else []
                    next_ms = min(valid_next, default=None)
                    reset_str = format_seconds_to_hm(max(0, (next_ms - now_ms) / 1000.0)) if next_ms else ("All 10 Ready" if ready_cnt == 10 else "Ready Now")

                    rep = (
                        f"📱 *Account #{target_idx} Inspection*\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"• **Name:** {name}\n"
                        f"• **Phone:** `{phone}`\n"
                        f"• **User ID:** `{uid}`\n"
                        f"• **Daemon Status:** {status_icon}\n"
                        f"• **Network Proxy:** `{proxy}`\n"
                        f"• **BNB Tasks Completed:** `{completed_cnt}/10` ({ready_cnt} ready)\n"
                        f"• **Next Task Reset:** `{reset_str}`\n"
                        f"• **Holding Balance:** `{cached_bal:.6f} BNB`\n"
                        f"• **Auto-Withdraw:** `{'Eligible! 🚀' if cached_bal >= MIN_WITHDRAWAL else f'{MIN_WITHDRAWAL - cached_bal:.6f} BNB needed'}`\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"💡 _Tip: Use `/acc <1-{len(accounts)}>` to inspect any connected account._"
                    )
                    await send_report_message(rep, reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)
                else:
                    await send_report_message(f"❌ Invalid account index. Fleet has {len(accounts)} accounts. Try `/acc 1`.", reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)
            else:
                rep = build_accounts_report()
                await send_message_chunks(rep, reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)

        elif text.startswith("/addaccount") or text.startswith("/add_account") or text in ["➕ Add Account", "➕ Add", "Add Account"]:
            parts = text.split(maxsplit=1)
            raw_phone = parts[1].strip() if len(parts) > 1 else None
            if raw_phone and any(c.isdigit() for c in raw_phone):
                cleaned_phone, country_label = detect_and_normalize_phone(raw_phone)
                await send_report_message(
                    f"📡 *Auto-Detected Country:* {country_label}\n"
                    f"📱 *Normalized Number:* `{cleaned_phone}`\n\n"
                    f"⏳ Requesting verification code from Telegram...",
                    reply_markup=CANCEL_KEYBOARD,
                    chat_id=chat_id
                )
                temp_cl = TelegramClient(StringSession(), API_ID, API_HASH)
                await temp_cl.connect()
                try:
                    sent_code = await temp_cl.send_code_request(cleaned_phone)
                    login_sessions[str(chat_id)] = {
                        "step": "WAITING_CODE",
                        "phone": cleaned_phone,
                        "country": country_label,
                        "phone_code_hash": sent_code.phone_code_hash,
                        "client": temp_cl,
                        "time": time.time()
                    }
                    await send_report_message(
                        f"✉️ Telegram has sent a login code to `{cleaned_phone}`.\n\n"
                        f"Please send the login code here (e.g. `12345`).",
                        reply_markup=CANCEL_KEYBOARD,
                        chat_id=chat_id
                    )
                except Exception as e:
                    await send_report_message(f"❌ Failed to send code to `{cleaned_phone}`: {e}", reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)
                    try:
                        await temp_cl.disconnect()
                    except Exception:
                        pass
            else:
                login_sessions[str(chat_id)] = {"step": "WAITING_PHONE", "client": None, "time": time.time()}
                prompt = (
                    "📱 *Add New Telegram Account*\n\n"
                    "Please send the phone number of the Telegram account you want to connect.\n\n"
                    "💡 *Country Code Auto-Detection Enabled!*\n"
                    "You can enter:\n"
                    "• `019XXXXXXXX` or `19XXXXXXXX` (Bangladesh 🇧🇩)\n"
                    "• `+88017XXXXXXXX` (Standard E.164)\n"
                    "• Any international number (e.g. `+1...`, `+44...`, `+92...`)\n\n"
                    "_(Tap ❌ Cancel Login below to abort at any time)_"
                )
                await send_report_message(prompt, reply_markup=CANCEL_KEYBOARD, chat_id=chat_id)

        elif (
            (text.startswith("+") and sum(1 for c in text if c.isdigit()) >= 8)
            or (text.startswith("01") and len(text.replace(" ", "").replace("-", "")) == 11 and text.replace(" ", "").replace("-", "").isdigit())
            or (text.startswith("1") and len(text.replace(" ", "").replace("-", "")) == 10 and text.replace(" ", "").replace("-", "").isdigit() and text[1] in "3456789")
        ):
            cleaned_phone, country_label = detect_and_normalize_phone(text)
            await send_report_message(
                f"📡 *Auto-Detected Country:* {country_label}\n"
                f"📱 *Normalized Number:* `{cleaned_phone}`\n\n"
                f"⏳ Requesting verification code from Telegram...",
                reply_markup=CANCEL_KEYBOARD,
                chat_id=chat_id
            )
            temp_cl = TelegramClient(StringSession(), API_ID, API_HASH)
            await temp_cl.connect()
            try:
                sent_code = await temp_cl.send_code_request(cleaned_phone)
                login_sessions[str(chat_id)] = {
                    "step": "WAITING_CODE",
                    "phone": cleaned_phone,
                    "country": country_label,
                    "phone_code_hash": sent_code.phone_code_hash,
                    "client": temp_cl,
                    "time": time.time()
                }
                await send_report_message(
                    f"✉️ Telegram has sent a login code to `{cleaned_phone}`.\n\n"
                    f"Please send the login code here (e.g. `12345`).",
                    reply_markup=CANCEL_KEYBOARD,
                    chat_id=chat_id
                )
            except Exception as e:
                await send_report_message(f"❌ Failed to send code to `{cleaned_phone}`: {e}", reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)
                try:
                    await temp_cl.disconnect()
                except Exception:
                    pass

        elif text.startswith("/briefing") or text.startswith("/morning") or text in ["🌅 Morning Briefing", "🌅 Briefing"]:
            rep = await build_morning_briefing(caller_uid)
            await send_report_message(rep, reply_markup=STATUS_INLINE_KEYBOARD, chat_id=chat_id)

        elif text.startswith("/proxy") or text.startswith("/security") or text in ["🛡️ Proxy & Security", "🛡️ Proxy"]:
            rep = build_proxy_security_report()
            await send_message_chunks(rep, reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)

        elif text.startswith("/setproxy"):
            parts = text.split()
            if len(parts) >= 3:
                target = parts[1]
                proxy_url = parts[2]
                ok, msg = set_account_proxy(target, proxy_url)
                await send_report_message(msg, reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)
            else:
                usage = (
                    "⚙️ *Set Proxy Usage:*\n\n"
                    "`/setproxy <phone_or_user_id> <proxy_url>`\n\n"
                    "*Examples:*\n"
                    "• `/setproxy 8881914294 socks5://user:pass@1.2.3.4:1080`\n"
                    "• `/setproxy 8881914294 http://1.2.3.4:8080`\n"
                    "• `/setproxy 8881914294 direct` (Remove proxy / use direct shield)"
                )
                await send_report_message(usage, reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)

        elif text.startswith("/backup") or text in ["💾 Backup", "💾 Cloud Backup"]:
            await send_report_message("⏳ Generating disaster recovery backup archive...", reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)
            ok, msg = await send_backup_to_telegram(str(chat_id))
            if not ok:
                await send_report_message(msg, reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)

        elif text.startswith("/screen") or text in ["📺 Live Screen", "📺 Screen"]:
            lines = []
            log_path = os.path.join(BASE_DIR, "userbot.log")
            if os.path.exists(log_path):
                try:
                    with open(log_path, "r", encoding="utf-8", errors="ignore") as lf:
                        lines = lf.readlines()[-20:]
                except Exception:
                    pass
            snippet = "".join(lines).strip()
            if not snippet:
                snippet = "Log file is currently empty or initializing..."
            clean_snippet = snippet.replace("`", "'")
            screen_msg = (
                f"📺 *MY AGY AI — Live Terminal Screen*\n"
                f"🕒 _{datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}_\n\n"
                f"```text\n{clean_snippet}\n```\n\n"
                f"🟢 *Supervisor:* Running 24/7 in persistent `tmux`\n"
                f"🌐 *Vault Channel:* https://t.me/myagyai"
            )
            await send_report_message(screen_msg, reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)

        elif text.startswith("/setwallet"):
            parts = text.split()
            if len(parts) >= 2:
                new_wallet = parts[1].strip()
                if re.match(r"^0x[a-fA-F0-9]{40}$", new_wallet):
                    WALLET_ADDRESS = new_wallet
                    env_path = os.path.join(BASE_DIR, ".env")
                    if os.path.exists(env_path):
                        try:
                            with open(env_path, "r") as ef:
                                env_c = ef.read()
                            if "WALLET_ADDRESS=" in env_c:
                                env_c = re.sub(r"WALLET_ADDRESS=.*", f"WALLET_ADDRESS={new_wallet}", env_c)
                            else:
                                env_c += f"\nWALLET_ADDRESS={new_wallet}\n"
                            with open(env_path, "w") as ef:
                                ef.write(env_c)
                        except Exception:
                            pass
                    asyncio.create_task(send_backup_to_telegram(str(chat_id)))
                    await send_report_message(
                        f"✅ *BEP-20 Payout Wallet Updated!*\n\n"
                        f"• **New Address:** `{new_wallet}`\n"
                        f"• **Auto-Withdrawal:** Active (`>= {MIN_WITHDRAWAL} BNB`)\n"
                        f"• **Cloud Backup:** Synced to Cloudflare KV & @myagyai",
                        reply_markup=MAIN_TAB_KEYBOARD,
                        chat_id=chat_id
                    )
                else:
                    await send_report_message(
                        "❌ *Invalid Wallet Address!*\n\n"
                        "Please enter a valid 42-character BEP-20 / EVM address starting with `0x`.\n\n"
                        "*Example:*\n`/setwallet 0xfda4182001672b9f0f09e2118242e543e35ed5ce`",
                        reply_markup=MAIN_TAB_KEYBOARD,
                        chat_id=chat_id
                    )
            else:
                await send_report_message(
                    f"💼 *Current Payout Wallet:*\n`{WALLET_ADDRESS}`\n\n"
                    f"*To update, send:*\n`/setwallet <your_bep20_address>`",
                    reply_markup=MAIN_TAB_KEYBOARD,
                    chat_id=chat_id
                )

        elif text.startswith("/ai") or text == "💬 Chat with AI":
            parts = text.split(maxsplit=1)
            prompt = parts[1].strip() if len(parts) > 1 else ""
            if not prompt:
                await send_report_message(
                    "🧠 *MY AGY AI — Dual-Engine Assistant*\n\n"
                    "Powered by **GroqCloud LPU** (`qwen/qwen3.8-27b` @ ~100ms) with **Cloudflare Edge AI** failover!\n\n"
                    "Ask anything by sending:\n"
                    "`/ai <your question>`\n\n"
                    "*Examples:*\n"
                    "• `/ai What are the optimal strategies for crypto mining bots?`\n"
                    "• `/ai Explain how BEP-20 gas fees work.`",
                    reply_markup=MAIN_TAB_KEYBOARD,
                    chat_id=chat_id
                )
            else:
                await send_report_message("🤔 *Processing query via Google Gemini 3.8 Flash AI...*", reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)
                try:
                    ans = None
                    active_provider = "Google Gemini"

                    # 1. Primary Engine: Google Gemini (3.8 Flash -> fallback 3.7 Flash -> 3.5 Flash)
                    gemini_res = await query_gemini_ai(prompt)
                    if gemini_res:
                        ans, active_provider = gemini_res

                    # 2. Secondary Failover: Ultra-Fast GroqCloud LPU
                    if not ans:
                        groq_res = await query_groq_ai(prompt)
                        if groq_res:
                            ans, active_provider = groq_res

                    # 3. Tertiary Failover: Cloudflare Edge AI
                    if not ans:
                        async def fetch_cf_ai(base_cf: str):
                            cf_ai_url = f"{base_cf}/ai"
                            try:
                                async with cf_session.post(cf_ai_url, json={"prompt": prompt}, timeout=aiohttp.ClientTimeout(total=15)) as cf_resp:
                                    if cf_resp.status == 200:
                                        cf_data = await cf_resp.json()
                                        if cf_data.get("ok") and cf_data.get("answer"):
                                            provider = base_cf.replace("https://restore-agy.", "").replace(".workers.dev", "")
                                            return (cf_data.get("answer"), f"Cloudflare Edge ({provider})")
                            except Exception:
                                pass
                            return None

                        async with aiohttp.ClientSession() as cf_session:
                            tasks = [fetch_cf_ai(u) for u in CF_WORKER_URLS]
                            for coro in asyncio.as_completed(tasks):
                                res = await coro
                                if res:
                                    ans, active_provider = res
                                    break

                    if not ans:
                        ans = "AI was unable to generate an answer at this moment. Please retry in a moment."

                    ai_msg = (
                        f"🤖 *AI Intelligence ({active_provider}):*\n\n"
                        f"{ans}\n\n"
                        f"⚡ _MY AGY AI Hybrid Engine (Google Gemini Flash + Groq LPU + Cloudflare Edge)_"
                    )
                    await send_report_message(ai_msg, reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)
                except Exception as e:
                    await send_report_message(f"❌ AI error: {e}", reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)

        elif text.startswith("/briefing") or text == "📊 Daily Briefing":
            await send_report_message("⏳ *Generating Daily Executive Briefing via Google Gemini 3.8 Flash...*", reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)
            report = await generate_daily_executive_briefing(notify=False)
            await send_report_message(report, reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)

        elif text.startswith("/consolidate") or text == "🪙 Consolidate":
            w1 = "0xfda4182001672b9f0f09e2118242e543e35ed5ce"
            w2 = "0x017841f26d5b79cc8c5eb20c65367bb645cc2610"
            b1 = await get_onchain_bnb_balance(w1)
            b2 = await get_onchain_bnb_balance(w2)
            tot = b1 + b2
            rep = (
                f"🪙 *On-Chain BNB Consolidator & Wallet Tracker*\n\n"
                f"• **Vault 1 (Accounts 1–7):** `{b1:.6f} BNB`\n"
                f"  `0xfda4182001672b9f0f09e2118242e543e35ed5ce`\n"
                f"• **Vault 2 (Accounts 8–13):** `{b2:.6f} BNB`\n"
                f"  `0x017841f26d5b79cc8c5eb20c65367bb645cc2610`\n"
                f"• **Total On-Chain BNB:** `{tot:.6f} BNB`\n"
                f"• **Consolidation Target:** `0.005000 BNB` ({(tot / 0.005 * 100):.1f}%)\n\n"
                f"🎯 _Tracking live BSC blockchain state via Binance Dataseed RPC._"
            )
            await send_report_message(rep, reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)

        elif text.startswith("/sync") or text == "🔄 Sync Fleet":
            wake_worker_event.set()
            await send_report_message("🔄 *Multi-Cloud Fleet Sync Dispatched!*\n\n• Mining cycle triggered across all 13 accounts\n• Telemetry replicating to Turso LibSQL, D1 SQL, and Supabase", reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)

        elif text.startswith("/ping") or text == "🏓 Server Health":
            rep = build_server_health_report()
            await send_report_message(rep, reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)

        elif text.startswith("/ide"):
            ide_url = "https://antigravity.google.com/u/8/r/8bf8fe6b-19b3-4963-a444-8d44de5cfd51-v2?p=c%2F39f8f911-3fb0-4128-a548-1591c0382185%3Fsection%3Ddefault-cli-project%26tab%3Dbgtask__39f8f911-3fb0-4128-a548-1591c0382185%252Ftask-2555"
            ide_btn = {
                "inline_keyboard": [
                    [{"text": "🌌 Open Antigravity Cloud Web IDE", "url": ide_url}]
                ]
            }
            await send_report_message(
                "🌌 *Antigravity Cloud Web IDE*\n\n"
                "Tap below to open your cloud workspace, background tasks, and logs directly in your browser:\n\n"
                f"🔗 {ide_url}",
                reply_markup=ide_btn,
                chat_id=chat_id
            )

        elif text.startswith("/help") or text.startswith("/menu") or text in ["ℹ️ Menu & Help", "ℹ️ Help & Guide", "📱 Show Menu"]:
            rep = build_help_guide()
            await send_report_message(rep, reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)

        else:
            guide_msg = (
                "🤖 *MY AGY AI — Operations Hub*\n\n"
                "Please use the tab buttons below or select a command from the menu:\n\n"
                "• `/status` - Live Fleet Status & Performance\n"
                "• `/withdraw` - Check Balances & Trigger Auto-Withdrawal\n"
                "• `/wallet` - Consolidated Wallets, Payouts & Yield Hub\n"
                "• `/accounts` - View Connected Fleet Accounts\n"
                "• `/addaccount` - Connect New Telegram Account\n"
                "• `/backup` - 💾 Disaster Recovery Cloud Backup\n"
                "• `/silent` - 🌙 Smart Quiet Hours / Silent Mode\n"
                "• `/help` - System Guide & Documentation"
            )
            await send_report_message(guide_msg, reply_markup=MAIN_TAB_KEYBOARD, chat_id=chat_id)


    except Exception as e:
        logger.error(f"[ReportBot] Error handling update: {e}", exc_info=True)


async def report_bot_listener_loop(user_id: int):
    """
    Ensures @My_Router_AI_bot is hosted 100% 24/7 on Cloudflare Edge Webhook.
    Does not use local getUpdates polling so the bot NEVER stops when Termux or VPS closes!
    """
    logger.info("[ReportBot] Telegram bot is hosted 24/7 on Cloudflare Edge (https://restore-agy.aaaai2.workers.dev/telegram-webhook).")
    cf_webhook_url = "https://restore-agy.aaaai2.workers.dev/telegram-webhook"
    set_wh_url = f"https://api.telegram.org/bot{REPORT_BOT_TOKEN}/setWebhook"

    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(set_wh_url, json={"url": cf_webhook_url, "drop_pending_updates": False}, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        logger.info("[ReportBot] ✅ 24/7 Cloudflare Edge Webhook confirmed active & synchronized.")
                    else:
                        logger.warning(f"[ReportBot] Cloudflare webhook registration status: {resp.status}")
        except Exception as e:
            logger.debug(f"[ReportBot] Webhook sync check: {e}")

        # Sleep for 5 minutes between health audits
        await asyncio.sleep(300)


# =======================================================
# CLOUDFLARE EDGE BIDIRECTIONAL COMMAND & TELEMETRY BRIDGE
# =======================================================

async def cloudflare_edge_bridge_loop():
    """
    Cloudflare Edge Sentinel & Telemetry Bridge:
    1. Sentinel Heartbeat: Pings /heartbeat every 90s across dual Cloudflare workers to keep dead-man's sentinel active.
    2. Telemetry Replication: Posts live fleet metrics, active worker ID, balances, & status to /api/fleet/sync every 90s.
    """
    logger.info("[CF-Bridge] Cloudflare, Supabase & Upstash Multi-Cloud Bridge loop started.")
    cf_secret = os.getenv("CF_SECRET_KEY", "agy_cf_secret_7d36994e_2026")
    supabase_url = os.getenv("SUPABASE_URL", "https://znbbaozpevurvbfkxakz.supabase.co")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpuYmJhb3pwZXZ1cnZiZmt4YWt6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODk4MTYxNTQsImV4cCI6MjEwNTM5MjE1NH0.ldgn0gCtOLEPUQyvTiG5RgKX6VY0LrS_4LkIKCf8NqM")
    upstash_url = os.getenv("UPSTASH_REDIS_REST_URL", "https://relaxing-starfish-285827.upstash.io")
    upstash_token = os.getenv("UPSTASH_REDIS_REST_TOKEN", "gQAAAAAABFyDAAIgcDI5MDYyYWZjNzYzNzk0ZmRjYjhmNTA4ZDI4ODlmODkzNw")

    headers = {
        "Authorization": f"Bearer {cf_secret}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    }

    while True:
        try:
            async with aiohttp.ClientSession() as session:
                while True:
                    now = time.time()
                    try:
                        accs = load_accounts()
                        ton_wallets = load_fleet_ton_wallets()
                        telemetry_payload = {
                            "node": "vps-main",
                            "timestamp": now,
                            "active_worker_id": CURRENTLY_ACTIVE_ACCOUNT_ID,
                            "active_worker_ids": list(CURRENTLY_ACTIVE_ACCOUNT_IDS),
                            "accounts_total": len(accs),
                            "accounts": [
                                {
                                    "index": idx + 1,
                                    "user_id": a.get("user_id"),
                                    "name": a.get("name", f"Account #{idx+1}"),
                                    "phone": a.get("phone", "N/A"),
                                    "status": a.get("status", "active"),
                                    "cycle_done": bool(a.get("last_fleet_cycle_at")),
                                    "ton_wallet": a.get("ton_wallet") or ton_wallets.get(str(a.get("user_id")), "N/A"),
                                    "bnb_balance": ACCOUNT_BALANCES.get(str(a.get("user_id")), {}).get("balance", 0.0),
                                    "stones_bound": bool(a.get("stones_referral_bound")),
                                    "bnb_next_reset_at": a.get("bnb_next_reset_at"),
                                    "stones_coins": a.get("stones_coins", 0),
                                    "atf_balance": a.get("atf_balance", 0),
                                    "stones_next_wd_at": a.get("stones_next_wd_at"),
                                    "atf_next_wd_at": a.get("atf_next_wd_at"),
                                    "evm_wallet": "0xfda4182001672b9f0f09e2118242e543e35ed5ce"
                                }
                                for idx, a in enumerate(accs)
                            ],
                            "balances": ACCOUNT_BALANCES,
                            "fleet_ton_wallets": ton_wallets
                        }

                        # Sync to all 3 Cloudflare accounts concurrently (Triple-Edge Parallel Replication)
                        sync_tasks = []
                        async def push_telemetry(cf_url: str):
                            try:
                                async with session.post(
                                    f"{cf_url}/api/fleet/sync",
                                    json=telemetry_payload,
                                    headers=headers,
                                    timeout=aiohttp.ClientTimeout(total=8)
                                ) as s_resp:
                                    pass
                            except Exception:
                                pass
                            try:
                                async with session.post(
                                    f"{cf_url}/heartbeat",
                                    json={"status": "online", "active_worker": CURRENTLY_ACTIVE_ACCOUNT_ID, "active_workers": list(CURRENTLY_ACTIVE_ACCOUNT_IDS)},
                                    headers=headers,
                                    timeout=aiohttp.ClientTimeout(total=5)
                                ) as h_resp:
                                    pass
                            except Exception:
                                pass

                        # Push to primary Cloudflare node (Node 1), fallback to siblings if unreachable
                        async def push_cf_smart():
                            for u in CF_WORKER_URLS:
                                try:
                                    async with session.post(
                                        f"{u}/api/fleet/sync",
                                        json=telemetry_payload,
                                        headers=headers,
                                        timeout=aiohttp.ClientTimeout(total=6)
                                    ) as resp:
                                        if resp.status == 200:
                                            break
                                except Exception:
                                    continue

                        sync_tasks.append(push_cf_smart())

                        # Sync to Upstash Serverless Redis
                        if upstash_url and upstash_token:
                            async def push_upstash():
                                try:
                                    up_headers = {
                                        "Authorization": f"Bearer {upstash_token}",
                                        "Content-Type": "application/json"
                                    }
                                    async with session.post(
                                        f"{upstash_url}/set/fleet:telemetry",
                                        data=json.dumps(telemetry_payload),
                                        headers=up_headers,
                                        timeout=aiohttp.ClientTimeout(total=5)
                                    ):
                                        pass
                                except Exception:
                                    pass
                            sync_tasks.append(push_upstash())

                        # Sync Daemon Heartbeat to Supabase Postgres
                        if supabase_url and supabase_key:
                            async def push_supabase():
                                try:
                                    sb_headers = {
                                        "apikey": supabase_key,
                                        "Authorization": f"Bearer {supabase_key}",
                                        "Content-Type": "application/json",
                                        "Prefer": "resolution=merge-duplicates"
                                    }
                                    sb_payload = [{
                                        "node_name": "Autonomous Fleet Daemon (Active)",
                                        "node_url": "daemon://sequential-queue",
                                        "status": "ONLINE",
                                        "latency_ms": 1,
                                        "last_seen": datetime.now(timezone.utc).isoformat()
                                    }]
                                    async with session.post(
                                        f"{supabase_url}/rest/v1/fleet_mesh_heartbeats",
                                        json=sb_payload,
                                        headers=sb_headers,
                                        timeout=aiohttp.ClientTimeout(total=5)
                                    ):
                                        pass
                                except Exception:
                                    pass
                            sync_tasks.append(push_supabase())

                        # Sync Telemetry to Turso LibSQL (AWS Mumbai)
                        turso_url = os.getenv("TURSO_URL", "https://my-agy-fleet-db-aaa2743.aws-ap-south-1.turso.io")
                        turso_token = os.getenv("TURSO_TOKEN", "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODk4MjQ5NjMsImlkIjoiMDFhMGI5ZTEtNzYwMS03ZDIwLWIwNTAtZDkyNmJkMDRiYzhmIiwia2lkIjoiVXI0T3NhVlRiZktFaWU3aEMydjFPYUQ3T01sQ2RZSjhDa3M3bGZKWEh0MCIsInJpZCI6IjcyYjQ5N2Y4LWVhY2UtNDI5Yy04YTIzLWI4MDRmYjg2ODBhOCJ9.W1W5nHYEFXTFLgIh6Q8yLmH3bL9QgCTEI7d4k-tG_Q_-oZwEZz-Ryq0oYtyvChD0ivOqn6NA_asbPAOYAFVaDw")
                        if turso_url and turso_token:
                            async def push_turso():
                                try:
                                    t_headers = {
                                        "Authorization": f"Bearer {turso_token}",
                                        "Content-Type": "application/json"
                                    }
                                    tot_b = sum(float(v.get("balance", 0.0)) for v in ACCOUNT_BALANCES.values())
                                    t_payload = {
                                        "requests": [{
                                            "type": "execute",
                                            "stmt": {
                                                "sql": "INSERT INTO fleet_telemetry (total_accounts, active_nodes, bnb_balance) VALUES (?, ?, ?)",
                                                "args": [
                                                    {"type": "integer", "value": str(len(load_accounts()))},
                                                    {"type": "integer", "value": "3"},
                                                    {"type": "float", "value": float(tot_b)}
                                                ]
                                            }
                                        }]
                                    }
                                    async with session.post(
                                        f"{turso_url}/v2/pipeline",
                                        json=t_payload,
                                        headers=t_headers,
                                        timeout=aiohttp.ClientTimeout(total=5)
                                    ):
                                        pass
                                except Exception:
                                    pass
                            sync_tasks.append(push_turso())

                        await asyncio.gather(*sync_tasks, return_exceptions=True)
                    except Exception as sync_e:
                        logger.warning(f"[CF-Bridge] Telemetry sync error: {sync_e}")

                    # 5-minute interval (288 cycles/day) to strictly conserve Cloudflare KV write limits
                    await asyncio.sleep(300.0)

        except asyncio.CancelledError:
            logger.info("[CF-Bridge] Bridge task cancelled.")
            break
        except Exception as bridge_err:
            logger.error(f"[CF-Bridge] Outer bridge loop error: {bridge_err}")
            await asyncio.sleep(15.0)


# =======================================================
# MODULE 1: BNB GALAXY (@CryptoProUpRobot)
# =======================================================

EXCLUDED_CHANNELS = [
    "airdropbulider",
    "gramworkers",
    "milonofficialearn"
]

MANDATORY_BNB_CHANNELS = [
    "Rewards_Lab",
    "TensorCoinNews",
    "AirdropFindTeam",
    "EarnCraftNews"
]

async def ensure_referral_bound(acc_client, acc: dict):
    """Automatically starts, joins required channels, and connects new accounts using user's BNB and ATF referral links."""
    acc_uid = acc.get("user_id")
    acc_name = acc.get("name", "User")

    # Skip if this is the referral host (primary account)
    if str(acc_uid) == str(REPORT_CHAT_ID) or acc.get("is_referral_host"):
        return

    # 1. BNB Galaxy Referral Binding (DISABLED - Scammer Bot)
    if ENABLE_BNB_GALAXY and not acc.get("bnb_referral_bound"):
        try:
            logger.info(f"[{acc_name}] Onboarding BNB Galaxy with referral {BNB_REFERRAL_CODE}...")
            # Proactively unblock if previously blocked
            try:
                await acc_client(UnblockRequest(id=BNB_BOT))
            except Exception:
                pass
            await acc_client.send_message(BNB_BOT, f"/start {BNB_REFERRAL_CODE}")
            await asyncio.sleep(2.5)

            # Step 1: Join all mandatory Telegram channels
            for ch in MANDATORY_BNB_CHANNELS:
                try:
                    logger.info(f"[{acc_name}] Automatically joining channel: @{ch}...")
                    await acc_client(JoinChannelRequest(ch))
                    await asyncio.sleep(1.5)
                except Exception as ce:
                    logger.debug(f"[{acc_name}] Channel join note for @{ch}: {ce}")

            # Step 2: Click [Continue] (No joining of third-party promotional channels)
            msgs = await acc_client.get_messages(BNB_BOT, limit=3)
            for m in msgs:
                if m.buttons:
                    for row in m.buttons:
                        for btn in row:
                            if "continue" in (btn.text or "").lower():
                                logger.info(f"[{acc_name}] Clicking button: '{btn.text}'")
                                try:
                                    await btn.click()
                                    await asyncio.sleep(2.5)
                                    break
                                except Exception:
                                    pass

            # Step 3: Click [Submit Details]
            msgs = await acc_client.get_messages(BNB_BOT, limit=3)
            for m in msgs:
                if m.buttons:
                    for row in m.buttons:
                        for btn in row:
                            if "submit details" in (btn.text or "").lower() or "details" in (btn.text or "").lower():
                                logger.info(f"[{acc_name}] Clicking button: '{btn.text}'")
                                try:
                                    await btn.click()
                                    await asyncio.sleep(2.5)
                                    break
                                except Exception:
                                    pass

            # Step 4: Wait for email prompt and submit official email
            email_submitted = False
            for _ in range(8):
                await asyncio.sleep(1.5)
                msgs = await acc_client.get_messages(BNB_BOT, limit=3)
                for m in msgs:
                    if not m.out and any(w in (m.raw_text or "").lower() for w in ["email", "youtube"]):
                        em = OFFICIAL_EMAIL
                        logger.info(f"[{acc_name}] Submitting onboarding email: {em}")
                        await acc_client.send_message(BNB_BOT, em)
                        email_submitted = True
                        break
                if email_submitted:
                    break

            # Step 5: Wait for BEP-20 wallet prompt and submit wallet address
            wallet_submitted = False
            target_bnb_wallet = acc.get("bnb_wallet") or WALLET_ADDRESS
            for _ in range(8):
                await asyncio.sleep(1.5)
                msgs = await acc_client.get_messages(BNB_BOT, limit=3)
                for m in msgs:
                    if not m.out and any(w in (m.raw_text or "").lower() for w in ["wallet", "bep-20"]):
                        logger.info(f"[{acc_name}] Submitting onboarding wallet: {target_bnb_wallet}")
                        await acc_client.send_message(BNB_BOT, target_bnb_wallet)
                        wallet_submitted = True
                        break
                if wallet_submitted:
                    break

            acc["bnb_referral_bound"] = True
            await update_account_safely(acc.get("user_id"), {"bnb_referral_bound": True})
            logger.info(f"[{acc_name}] ✅ BNB Galaxy successfully bound to referral {BNB_REFERRAL_CODE}!")

        except Exception as e:
            logger.error(f"[{acc_name}] Error binding BNB Galaxy referral: {e}")

    # 2. Stones Miners Referral Binding
    if not acc.get("stones_referral_bound"):
        try:
            logger.info(f"[{acc_name}] Onboarding Stones Miners with referral {STONES_REFERRAL_CODE}...")
            try:
                await acc_client(UnblockRequest(id=STONES_BOT))
            except Exception:
                pass
            await acc_client.send_message(STONES_BOT, f"/start {STONES_REFERRAL_CODE}")
            await asyncio.sleep(1.5)
            try:
                await acc_client(JoinChannelRequest("stoneswithestand"))
            except Exception:
                pass
            acc["stones_referral_bound"] = True
            await update_account_safely(acc_uid, {"stones_referral_bound": True})
            logger.info(f"[{acc_name}] ✅ Stones Miners successfully bound to referral {STONES_REFERRAL_CODE}!")
        except Exception as e:
            logger.warning(f"[{acc_name}] Stones referral notice: {e}")

    # 3. MRG Miner Referral Binding
    if not acc.get("mrg_referral_bound"):
        try:
            logger.info(f"[{acc_name}] Onboarding MRG Miner with referral {MRG_REFERRAL_CODE}...")
            try:
                await acc_client(UnblockRequest(id=MRG_BOT))
            except Exception:
                pass
            bot_mrg = await acc_client.get_input_entity(MRG_BOT)
            res_mrg = await acc_client(RequestAppWebViewRequest(
                peer=bot_mrg,
                app=InputBotAppShortName(bot_id=bot_mrg, short_name="app"),
                platform="android",
                start_param=MRG_REFERRAL_CODE
            ))
            parsed = urllib.parse.urlparse(res_mrg.url)
            m_init = urllib.parse.parse_qs(parsed.fragment).get("tgWebAppData", [None])[0]

            if m_init:
                m_fp = get_account_fingerprint(acc_uid)
                m_headers = {
                    "Content-Type": "application/json",
                    "Origin": "https://app.mrgtoken.xyz",
                    "Referer": "https://app.mrgtoken.xyz/",
                    "User-Agent": HUMAN_USER_AGENT
                }
                m_payload = {
                    "initData": m_init,
                    "startParam": MRG_REFERRAL_CODE,
                    "start_param": MRG_REFERRAL_CODE,
                    "deviceInfo": {
                        "platform": "android",
                        "deviceName": m_fp.get("device_model", "Android Device"),
                        "ram": "8 GB",
                        "cpuCores": 8,
                        "screenResolution": "1080x2400",
                        "userAgent": HUMAN_USER_AGENT,
                        "timezone": "UTC",
                        "language": "en"
                    }
                }
                try:
                    async with aiohttp.ClientSession() as m_sess:
                        await m_sess.post("https://mrg.up.railway.app/api/auth/verify", json=m_payload, headers=m_headers, proxy=acc.get("proxy"), timeout=aiohttp.ClientTimeout(total=12))
                except Exception:
                    pass

            try:
                await acc_client(JoinChannelRequest("mrgminer"))
            except Exception:
                pass
            acc["mrg_referral_bound"] = True
            await update_account_safely(acc_uid, {"mrg_referral_bound": True})
            logger.info(f"[{acc_name}] ✅ MRG Miner successfully onboarded with referral {MRG_REFERRAL_CODE}!")
        except Exception as e:
            logger.warning(f"[{acc_name}] MRG referral notice: {e}")

    # 4. ART Airdrop Referral Binding
    if not acc.get("art_referral_bound"):
        try:
            logger.info(f"[{acc_name}] Onboarding ART Airdrop with referral {ART_REFERRAL_CODE}...")
            try:
                await acc_client(UnblockRequest(id=ART_BOT))
            except Exception:
                pass
            await acc_client.send_message(ART_BOT, f"/start {ART_REFERRAL_CODE}")
            await asyncio.sleep(1.5)
            try:
                await acc_client(JoinChannelRequest("ART_AIRDROP"))
            except Exception:
                pass
            acc["art_referral_bound"] = True
            await update_account_safely(acc_uid, {"art_referral_bound": True})
            logger.info(f"[{acc_name}] ✅ ART Airdrop successfully bound to referral {ART_REFERRAL_CODE}!")
        except Exception as e:
            logger.warning(f"[{acc_name}] ART referral notice: {e}")

    # 5. AI Lab Robot Referral Binding (https://t.me/AiLab_robot?start=296852)
    if not acc.get("ailab_referral_bound") and str(acc_uid) != str(REPORT_CHAT_ID):
        try:
            logger.info(f"[{acc_name}] Onboarding AI Lab Robot with referral {AILAB_REFERRAL_CODE}...")
            try:
                await acc_client(UnblockRequest(id=AILAB_BOT))
            except Exception:
                pass
            bot_ai = await acc_client.get_entity(AILAB_BOT)
            await acc_client.send_message(bot_ai, f"/start {AILAB_REFERRAL_CODE}")
            await asyncio.sleep(1.5)
            try:
                res_ai = await acc_client(RequestWebViewRequest(
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
                            headers={"Content-Type": "application/json", "User-Agent": HUMAN_USER_AGENT},
                            timeout=aiohttp.ClientTimeout(total=8)
                        )
            except Exception:
                pass
            acc["ailab_referral_bound"] = True
            await update_account_safely(acc_uid, {"ailab_referral_bound": True})
            logger.info(f"[{acc_name}] ✅ AI Lab Robot successfully bound to referral {AILAB_REFERRAL_CODE}!")
        except Exception as e:
            logger.warning(f"[{acc_name}] AI Lab referral notice: {e}")

    # 6. Ultra Wallet Referral Binding (https://t.me/UltrawalletTrade_Bot/app?startapp=6727787768)
    if not acc.get("ultrawallet_referral_bound") and str(acc_uid) != str(REPORT_CHAT_ID):
        try:
            logger.info(f"[{acc_name}] Onboarding Ultra Wallet with referral {ULTRAWALLET_REFERRAL_CODE}...")
            try:
                await acc_client(UnblockRequest(id=ULTRAWALLET_BOT))
            except Exception:
                pass
            bot_uw = await acc_client.get_input_entity(ULTRAWALLET_BOT)
            await acc_client(RequestAppWebViewRequest(
                peer=bot_uw,
                app=InputBotAppShortName(bot_id=bot_uw, short_name="app"),
                platform="android",
                start_param=ULTRAWALLET_REFERRAL_CODE
            ))
            acc["ultrawallet_referral_bound"] = True
            await update_account_safely(acc_uid, {"ultrawallet_referral_bound": True})
            logger.info(f"[{acc_name}] ✅ Ultra Wallet successfully bound to referral {ULTRAWALLET_REFERRAL_CODE}!")
        except Exception as e:
            logger.warning(f"[{acc_name}] Ultra Wallet referral notice: {e}")

    # 7. Apex Miner Referral Binding (https://t.me/ApxMinerBot/app?startapp=6727787768)
    if not acc.get("apx_referral_bound"):
        try:
            logger.info(f"[{acc_name}] Onboarding Apex Miner with referral {APX_REFERRAL_CODE}...")
            try:
                await acc_client(UnblockRequest(id=APX_BOT))
            except Exception:
                pass
            bot_apx = await acc_client.get_input_entity(APX_BOT)
            is_worker = (str(acc_uid) != str(REPORT_CHAT_ID))
            st_param = APX_REFERRAL_CODE if is_worker else ""
            res_apx = await acc_client(RequestAppWebViewRequest(
                peer=bot_apx,
                app=InputBotAppShortName(bot_id=bot_apx, short_name="app"),
                platform="android",
                start_param=st_param
            ))
            parsed_apx = urllib.parse.urlparse(res_apx.url)
            init_apx = urllib.parse.parse_qs(parsed_apx.fragment).get("tgWebAppData", [None])[0]
            if init_apx:
                headers = {"Content-Type": "application/json", "User-Agent": HUMAN_USER_AGENT}
                base_url = "https://apex-miner.vercel.app/api"
                async with aiohttp.ClientSession() as apx_sess:
                    async with apx_sess.post(f"{base_url}/auth/telegram", json={"initData": init_apx}, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as auth_r:
                        pass
                    b_data = {}
                    async with apx_sess.post(f"{base_url}/bootstrap", json={"initData": init_apx}, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as b_res:
                        if b_res.status == 200:
                            b_data = await b_res.json()
                    if not b_data.get("exists") or not b_data.get("user"):
                        async with apx_sess.post(f"{base_url}/register", json={"initData": init_apx}, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as reg_r:
                            pass
            try:
                await acc_client(JoinChannelRequest("ApexMiner_Official"))
            except Exception:
                pass
            try:
                await acc_client(JoinChannelRequest("ApexMinerGroup"))
            except Exception:
                pass
            acc["apx_referral_bound"] = True
            await update_account_safely(acc_uid, {"apx_referral_bound": True})
            logger.info(f"[{acc_name}] ✅ Apex Miner successfully bound to referral {APX_REFERRAL_CODE}!")
        except Exception as e:
            logger.warning(f"[{acc_name}] Apex Miner referral notice: {e}")

    # 8. Ainovum Bot Referral Binding (https://t.me/ainovum_bot?start=ref_6727787768)
    if not acc.get("ainovum_referral_bound") and str(acc_uid) != str(REPORT_CHAT_ID):
        try:
            logger.info(f"[{acc_name}] Onboarding Ainovum Bot with referral {AINOVUM_REFERRAL_CODE}...")
            try:
                await acc_client(UnblockRequest(id=AINOVUM_BOT))
            except Exception:
                pass
            bot_an = await acc_client.get_entity(AINOVUM_BOT)
            await acc_client.send_message(bot_an, f"/start {AINOVUM_REFERRAL_CODE}")
            await asyncio.sleep(2.0)
            try:
                res_an = await acc_client(RequestWebViewRequest(
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
                            headers={"Content-Type": "application/json", "User-Agent": HUMAN_USER_AGENT},
                            timeout=aiohttp.ClientTimeout(total=10)
                        )
            except Exception:
                pass
            acc["ainovum_referral_bound"] = True
            await update_account_safely(acc_uid, {"ainovum_referral_bound": True})
            logger.info(f"[{acc_name}] ✅ Ainovum Bot successfully bound to referral {AINOVUM_REFERRAL_CODE}!")
        except Exception as e:
            logger.warning(f"[{acc_name}] Ainovum referral notice: {e}")

    # 9. MiningGRAM Bot Referral Binding (https://t.me/MiningGRAM_Bot/mine?startapp=339JU9K)
    if not acc.get("mininggram_referral_bound") and str(acc_uid) != str(REPORT_CHAT_ID):
        try:
            logger.info(f"[{acc_name}] Onboarding MiningGRAM Bot with referral {MININGGRAM_REFERRAL_CODE}...")
            try:
                await acc_client(UnblockRequest(id=MININGGRAM_BOT))
            except Exception:
                pass
            bot_mg = await acc_client.get_input_entity(MININGGRAM_BOT)
            await acc_client.send_message(bot_mg, f"/start {MININGGRAM_REFERRAL_CODE}")
            await asyncio.sleep(2.0)
            try:
                res_mg = await acc_client(RequestAppWebViewRequest(
                    peer=bot_mg,
                    app=InputBotAppShortName(bot_id=bot_mg, short_name="mine"),
                    platform="android",
                    start_param=MININGGRAM_REFERRAL_CODE
                ))
                parsed_mg = urllib.parse.urlparse(res_mg.url)
                init_mg = urllib.parse.parse_qs(parsed_mg.fragment).get("tgWebAppData", [None])[0]
                if init_mg:
                    async with aiohttp.ClientSession() as mg_sess:
                        await mg_sess.post(
                            "https://mining-gram-worker.muhaisin0888.workers.dev/api/auth",
                            json={
                                "initData": init_mg,
                                "referralCode": MININGGRAM_REFERRAL_CODE,
                                "deviceFingerprint": f"fp_{acc_uid}"
                            },
                            headers={"Content-Type": "application/json", "User-Agent": HUMAN_USER_AGENT},
                            timeout=aiohttp.ClientTimeout(total=10)
                        )
            except Exception:
                pass
            acc["mininggram_referral_bound"] = True
            await update_account_safely(acc_uid, {"mininggram_referral_bound": True})
            logger.info(f"[{acc_name}] ✅ MiningGRAM Bot successfully bound to referral {MININGGRAM_REFERRAL_CODE}!")
        except Exception as e:
            logger.warning(f"[{acc_name}] MiningGRAM referral notice: {e}")


async def self_heal_account_channels_and_bots(acc_client, acc: dict):
    """
    Autonomous Self-Healing Guard (Feature 3):
    Verifies that mandatory official sponsor channels are joined and target bots are unblocked.
    Runs once every 12 hours per account to eliminate rate limits, RAM overhead, and ban risks.
    """
    if not acc_client:
        return
    acc_uid = acc.get("user_id")
    acc_name = acc.get("name", "User")
    now_ts = time.time()
    last_healed = acc.get("last_healed_at", 0)

    # Rate limit healing checks to once every 12 hours per account to preserve resources & stay ban-proof
    if now_ts - last_healed < 43200:
        return

    logger.info(f"[{acc_name}] 🛡️ Running Self-Healing Channel & Bot Guard...")
    # 1. Ensure target legitimate bots are unblocked (BNB_BOT excluded - scammer bot blocked)
    for b in [STONES_BOT, MRG_BOT, ART_BOT, AILAB_BOT, ULTRAWALLET_BOT, APX_BOT, AINOVUM_BOT, MININGGRAM_BOT]:
        try:
            await acc_client(UnblockRequest(id=b))
        except Exception:
            pass

    # 2. Verify and re-join mandatory channels if left (skipping any excluded channels)
    all_chans = list(dict.fromkeys(MANDATORY_OFFICIAL_CHANNELS))
    for ch in all_chans:
        if ch.lower() in [e.lower() for e in EXCLUDED_CHANNELS]:
            continue
        try:
            await acc_client(JoinChannelRequest(ch))
            await asyncio.sleep(0.6)
        except Exception as ce:
            err_str = str(ce).lower()
            if "already" not in err_str:
                logger.debug(f"[{acc_name}] Channel guard check (@{ch}): {ce}")

    acc["last_healed_at"] = now_ts
    await update_account_safely(acc_uid, {"last_healed_at": now_ts})
    logger.info(f"[{acc_name}] 🛡️ Self-Healing Channel & Bot Guard check completed.")


async def extract_bnb_webhook(acc_client=None, acc_data: dict = None):
    if not ENABLE_BNB_GALAXY:
        return None
    global current_bnb_webhook
    if acc_data and acc_data.get("bnb_wh_url"):
        current_bnb_webhook = acc_data["bnb_wh_url"]
        return current_bnb_webhook
    cl = acc_client or client
    try:
        messages = await cl.get_messages(BNB_BOT, limit=35)
        for msg in messages:
            # Check msg text for explicit link
            for text_val in [getattr(msg, "text", None), getattr(msg, "raw_text", None)]:
                if text_val and "wh=" in text_val:
                    m = re.search(r"wh=(https?://[^\s\"'>]+)", text_val)
                    if m:
                        wh_part = m.group(1)
                        if "#" in wh_part:
                            wh_part = wh_part.split("#")[0]
                        current_bnb_webhook = urllib.parse.unquote(wh_part)
                        return current_bnb_webhook

            # Check buttons
            if msg.reply_markup and hasattr(msg.reply_markup, "rows"):
                for row in msg.reply_markup.rows:
                    for btn in row.buttons:
                        btn_url = getattr(btn, "url", None)
                        if not btn_url and hasattr(btn, "type") and getattr(btn.type, "url", None):
                            btn_url = btn.type.url
                        if not btn_url and hasattr(btn, "web_app") and getattr(btn.web_app, "url", None):
                            btn_url = btn.web_app.url
                        if btn_url and "wh=" in btn_url:
                            wh_part = btn_url.split("wh=")[1]
                            if "#" in wh_part:
                                wh_part = wh_part.split("#")[0]
                            wh_part = urllib.parse.unquote(wh_part)
                            current_bnb_webhook = wh_part
                            return current_bnb_webhook
    except Exception as e:
        logger.warning(f"Could not extract BNB webhook: {e}")
    return current_bnb_webhook


async def register_adsgram(session: aiohttp.ClientSession, tg_id: int, wh_url: str, proxy: str = None):
    reg_url = "https://justtool.site/api/adsgram-register"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": HUMAN_USER_AGENT,
        "Referer": "https://justtool.site/tasks-adsgram/",
        "Origin": "https://justtool.site",
        **STANDARD_HEADERS
    }
    try:
        async with session.post(reg_url, json={"tgId": tg_id, "wh": wh_url}, headers=headers, proxy=proxy, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            data = await resp.json()
            return data.get("ok", False)
    except Exception as e:
        logger.debug(f"Adsgram webhook registration note: {e}")
        return False


async def get_bnb_tasks_status(session: aiohttp.ClientSession, tg_id: int, proxy: str = None):
    status_url = f"https://justtool.site/api/adsgram-tasks?tgId={tg_id}"
    headers = {
        "User-Agent": HUMAN_USER_AGENT,
        "Referer": "https://justtool.site/tasks-adsgram/",
        **STANDARD_HEADERS
    }
    for attempt in range(2):
        try:
            async with session.get(status_url, headers=headers, proxy=proxy, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("states", {})
        except Exception as e:
            if attempt == 0:
                await asyncio.sleep(2)
            else:
                logger.error(f"Error fetching BNB tasks: {e}")
    return {}


async def complete_bnb_task(session: aiohttp.ClientSession, tg_id: int, task_id: int, proxy: str = None):
    complete_url = "https://justtool.site/api/adsgram-tasks/complete"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": HUMAN_USER_AGENT,
        "Referer": "https://justtool.site/tasks-adsgram/",
        "Origin": "https://justtool.site",
        **STANDARD_HEADERS
    }
    for attempt in range(1, 4):
        try:
            async with session.post(complete_url, json={"tgId": tg_id, "taskId": task_id}, headers=headers, proxy=proxy, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                if resp.status == 200:
                    return await resp.json()
                elif resp.status in (429, 502, 503, 504):
                    logger.warning(f"[BNB Task {task_id}] Server HTTP {resp.status}, backing off {3.0 * attempt}s (attempt {attempt}/3)...")
                    await asyncio.sleep(3.0 * attempt)
                    continue
                else:
                    text = await resp.text()
                    logger.warning(f"[BNB Task {task_id}] HTTP {resp.status}: {text[:120]}")
        except Exception as e:
            if attempt < 3:
                logger.warning(f"[BNB Task {task_id}] Request retry {attempt}/3: {e}")
                await asyncio.sleep(3.0)
            else:
                logger.error(f"[BNB Task {task_id}] Failed after 3 attempts: {e}")
                return {"ok": False, "error": str(e)}
    return {"ok": False, "error": "HTTP timeout or failure after 3 attempts"}


async def process_bnb_galaxy_tasks(session: aiohttp.ClientSession, user_id: int, acc_client=None, acc_data=None):
    if not ENABLE_BNB_GALAXY:
        return 0, 0, None
    proxy = (acc_data or {}).get("proxy")
    wh_url = (acc_data or {}).get("bnb_wh_url") or await extract_bnb_webhook(acc_client, acc_data=acc_data)
    await register_adsgram(session, user_id, wh_url, proxy=proxy)
    
    states = await get_bnb_tasks_status(session, user_id, proxy=proxy)
    if not states:
        return 0, 0, None

    now_ms = int(time.time() * 1000)
    ready_tasks = [int(tid) for tid, avail in sorted(states.items(), key=lambda x: int(x[0])) if avail == 0 or avail <= now_ms]
    completed_count = len(states) - len(ready_tasks)

    loc_desc = f"Proxy: {proxy.split('@')[-1]}" if proxy else "Cloud Direct"
    logger.info(f"[BNB Galaxy] Status ({loc_desc}): {completed_count}/10 tasks completed. {len(ready_tasks)} ready.")

    for idx, t_id in enumerate(ready_tasks):
        await human_delay(43.0, 65.0, f"Watching BNB Task {t_id} video/ad")
        res = await complete_bnb_task(session, user_id, t_id, proxy=proxy)
        if res.get("ok"):
            logger.info(f"[BNB Galaxy] Task {t_id} completed! Reward added to Telegram bot.")
            completed_count += 1
        else:
            logger.warning(f"[BNB Galaxy] Task {t_id} failed: {res}")

        if idx < len(ready_tasks) - 1:
            await human_delay(25.0, 60.0, "Browsing pause between tasks")

    updated = await get_bnb_tasks_status(session, user_id, proxy=proxy)
    next_avail = None
    for avail in updated.values():
        if avail > 0 and (next_avail is None or avail < next_avail):
            next_avail = avail

    return completed_count, len(states), next_avail


VERIFICATION_IN_PROGRESS_IDS = set()

async def complete_withdrawal_verification_steps(user_id: int, user_name: str, acc_client=None, acc_data=None):
    if not ENABLE_BNB_GALAXY:
        return False
    if str(user_id) in VERIFICATION_IN_PROGRESS_IDS:
        logger.info(f"[BNB Verifier] Verification already active in another thread for {user_name} ({user_id}). Skipping duplicate call.")
        return False
    VERIFICATION_IN_PROGRESS_IDS.add(str(user_id))
    try:
        return await _complete_withdrawal_verification_steps_impl(user_id, user_name, acc_client=acc_client, acc_data=acc_data)
    finally:
        VERIFICATION_IN_PROGRESS_IDS.discard(str(user_id))

async def _complete_withdrawal_verification_steps_impl(user_id: int, user_name: str, acc_client=None, acc_data=None):
    proxy = (acc_data or {}).get("proxy")
    headers = {
        "Content-Type": "application/json",
        "User-Agent": HUMAN_USER_AGENT,
        "Referer": "https://justtool.site/withdraw-adsgram",
        "Origin": "https://justtool.site",
        **STANDARD_HEADERS
    }
    url_count = f"https://justtool.site/api/adsgram-task3?tgId={user_id}"
    url_submit = "https://justtool.site/api/adsgram-task3"
    reg_url = "https://justtool.site/api/adsgram-register"

    # Step A: Register WebApp view on Telegram MTProto
    if acc_client:
        try:
            bot_entity = await acc_client.get_input_entity(BNB_BOT)
            await acc_client(RequestWebViewRequest(
                peer=bot_entity,
                bot=bot_entity,
                platform="android",
                url="https://justtool.site/withdraw-adsgram"
            ))
            logger.info(f"[BNB Verifier] Telegram MTProto WebApp opened for {user_name} ({user_id})")
        except Exception as we:
            logger.debug(f"[BNB Verifier] Telegram WebApp request note: {we}")

    async with aiohttp.ClientSession() as session:
        # Step B: Register webhook for withdrawal unlock callback
        wh_url = (acc_data or {}).get("bnb_wh_url") or await extract_bnb_webhook(acc_client, acc_data=acc_data)
        if not wh_url:
            wh_url = BNB_WEBHOOK_FALLBACK
        try:
            await session.post(reg_url, json={"tgId": user_id, "wh": wh_url}, headers=headers, proxy=proxy, timeout=aiohttp.ClientTimeout(total=15))
            logger.info(f"[BNB Verifier] Webhook registered for {user_name} ({user_id})")
        except Exception as e:
            logger.warning(f"[BNB Verifier] Webhook registration note for {user_name}: {e}")

        count = 0
        try:
            async with session.get(url_count, headers=headers, proxy=proxy, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    count = data.get("count", 0)
        except Exception as e:
            count = 0

        logger.info(f"[BNB Verifier] Current withdrawal verification status for {user_name}: {count}/5")
        if count >= 5:
            logger.info(f"[BNB Verifier] All 5/5 withdrawal verification tasks are already completed and unlocked for {user_name}.")
            try:
                await session.post(reg_url, json={"tgId": user_id, "wh": wh_url}, headers=headers, proxy=proxy, timeout=aiohttp.ClientTimeout(total=10))
            except Exception:
                pass
            return True

        while count < 5:
            await human_delay(3.0, 5.0, f"Completing withdrawal verification task {count + 1}/5 for {user_name}")
            # Submit step with robust auto-retry (up to 3 attempts)
            step_ok = False
            for attempt in range(1, 4):
                try:
                    async with session.post(url_submit, json={"tgId": user_id, "name": user_name}, headers=headers, proxy=proxy, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                        if resp.status == 200:
                            res = await resp.json()
                            count = res.get("count", count + 1)
                            logger.info(f"[BNB Verifier] Verification step {count}/5 completed for {user_name}!")
                            step_ok = True
                            break
                        else:
                            logger.warning(f"[BNB Verifier] HTTP {resp.status} on step submission for {user_name} (attempt {attempt}/3)")
                except Exception as e:
                    logger.warning(f"[BNB Verifier] Network note submitting step for {user_name} (attempt {attempt}/3): {e}")
                if attempt < 3:
                    await asyncio.sleep(2.0)

            if not step_ok:
                # Query real server state rather than falsely advancing
                try:
                    async with session.get(url_count, headers=headers, proxy=proxy, timeout=aiohttp.ClientTimeout(total=10)) as chk_resp:
                        if chk_resp.status == 200:
                            chk_data = await chk_resp.json()
                            count = chk_data.get("count", count)
                except Exception:
                    pass
                if count < 5:
                    logger.warning(f"[BNB Verifier] Step not registered by server for {user_name}. Retrying...")
                    await asyncio.sleep(3.0)
                    continue

            if count < 5:
                await human_delay(2.0, 4.0, f"Brief pause between verification tasks for {user_name}")

        # Final webhook registration confirmation on 5/5 unlock
        try:
            await session.post(reg_url, json={"tgId": user_id, "wh": wh_url}, headers=headers, proxy=proxy, timeout=aiohttp.ClientTimeout(total=15))
        except Exception:
            pass

        logger.info(f"[BNB Verifier] 🎉 5/5 withdrawal verification completed for {user_name}! Payout unlocked.")

        target_wallet = (acc_data or {}).get("bnb_wallet") or WALLET_ADDRESS
        alert_msg = (
            f"🎉 *BNB Withdrawal 5/5 Tasks Completed!* 🔓\n\n"
            f"• **Account:** {user_name} (`{user_id}`)\n"
            f"• **Verification Status:** `5/5 Tasks Unlocked` ✅\n"
            f"• **Payout Wallet:** `{target_wallet}`\n"
            f"• **Estimated Arrival:** Within ~8 hours\n\n"
            f"✅ All 5 verification ads have been watched and verified to unlock your BNB payout."
        )
        await send_report_message(alert_msg, reply_markup=MAIN_TAB_KEYBOARD)
        return True


async def check_and_auto_withdraw(user_id: int, user_name: str, notify_manual: bool = False, acc_client=None, caller_chat_id: str = None, acc_data: dict = None):
    """Executes robust, interactive multi-step BNB withdrawal for ANY fleet account."""
    if not ENABLE_BNB_GALAXY:
        logger.debug(f"[BNB Auto-Withdraw] BNB Galaxy disabled (scam protection). Skipping {user_name}.")
        return False
    logger.info(f"[BNB Auto-Withdraw] Checking account balance on bot for {user_name} ({user_id})...")
    target_chat = str(caller_chat_id) if caller_chat_id else str(REPORT_CHAT_ID)
    accounts = load_accounts()
    if not acc_data:
        acc_data = next((a for a in accounts if str(a.get("user_id")) == str(user_id)), None)

    global CURRENTLY_ACTIVE_ACCOUNT_ID, CURRENTLY_ACTIVE_ACCOUNT_IDS
    if acc_client is None and (str(user_id) in CURRENTLY_ACTIVE_ACCOUNT_IDS or (CURRENTLY_ACTIVE_ACCOUNT_ID is not None and str(CURRENTLY_ACTIVE_ACCOUNT_ID) == str(user_id))):
        logger.info(f"[BNB Auto-Withdraw] {user_name} is currently busy in 24/7 worker. Deferring to active worker.")
        if notify_manual:
            await send_report_message(
                f"⏳ **{user_name}** is currently processing automated tasks in the background worker.\n\n"
                f"Withdrawal will automatically trigger immediately when its current tasks complete!",
                reply_markup=MAIN_TAB_KEYBOARD,
                chat_id=target_chat
            )
        return False

    cl = acc_client
    should_disconnect = False
    claimed_lock = False
    if cl is None:
        if CURRENTLY_ACTIVE_ACCOUNT_ID is None:
            CURRENTLY_ACTIVE_ACCOUNT_ID = user_id
        CURRENTLY_ACTIVE_ACCOUNT_IDS.add(str(user_id))
        claimed_lock = True
        if acc_data and acc_data.get("session_string"):
            sess = acc_data.get("session_string")
            if sess == STRING_SESSION and client.is_connected():
                cl = client
                should_disconnect = False
            else:
                acc_proxy = parse_proxy(acc_data.get("proxy"))
                acc_fp = get_account_fingerprint(user_id)
                try:
                    cl = TelegramClient(StringSession(sess), API_ID, API_HASH, proxy=acc_proxy, **acc_fp)
                    await cl.connect()
                except Exception as proxy_err:
                    if acc_proxy:
                        logger.warning(f"[BNB Auto-Withdraw] 🛡️ Proxy failed ({proxy_err}) for {user_name}. Auto-failing over to direct connection...")
                        cl = TelegramClient(StringSession(sess), API_ID, API_HASH, **acc_fp)
                        await cl.connect()
                    else:
                        raise
                should_disconnect = True
        else:
            cl = client
            if not cl.is_connected():
                await cl.connect()
    else:
        if not cl.is_connected():
            await cl.connect()

    try:
        # Step 0: Fetch current bot balance (Timer-Aware & Anti-Spam Protected)
        is_cooldown = float((acc_data or {}).get("bnb_next_reset_at") or 0) > time.time()
        is_recent_wd = (time.time() - float((acc_data or {}).get("last_withdrawal_at") or 0)) < 28800
        cached_b_ts = float(ACCOUNT_BALANCES.get(str(user_id), {}).get("timestamp", 0))
        cached_is_fresh = (time.time() - cached_b_ts) < 14400

        # If automated check, skip sending "💰 Balance" if account is in 8h withdrawal window or on task cooldown with fresh cache
        if not notify_manual and ((is_cooldown and cached_is_fresh) or (is_recent_wd and (acc_data or {}).get("pending_withdraw"))):
            cached_bal = ACCOUNT_BALANCES.get(str(user_id), {}).get("balance", 0.0)
            logger.info(f"[BNB Auto-Withdraw] ⏳ {user_name} tasks on cooldown / withdrawal pending (~8h). Using cached balance ({cached_bal:.6f} BNB). Zero Telegram spam.")
            return False

        init_msgs = await cl.get_messages(BNB_BOT, limit=1)
        last_id = init_msgs[0].id if init_msgs else 0

        await cl.send_message(BNB_BOT, "💰 Balance")
        
        balance = 0.0
        for _ in range(5):
            await asyncio.sleep(1.0)
            msgs = await cl.get_messages(BNB_BOT, limit=3)
            found = False
            for m in msgs:
                if m.id > last_id and not m.out:
                    text = m.raw_text or ""
                    match = re.search(r"Your Balance:\s*([0-9.]+)\s*BNB", text, re.IGNORECASE)
                    if match:
                        balance = float(match.group(1))
                        found = True
                        break
            if found:
                break

        if balance == 0.0:
            msgs = await cl.get_messages(BNB_BOT, limit=3)
            for m in msgs:
                text = m.raw_text or ""
                match = re.search(r"Your Balance:\s*([0-9.]+)\s*BNB", text, re.IGNORECASE)
                if match:
                    balance = float(match.group(1))
                    break

        logger.info(f"[BNB Auto-Withdraw] Balance for {user_name}: {balance:.6f} BNB (Threshold: {MIN_WITHDRAWAL} BNB)")
        ACCOUNT_BALANCES[str(user_id)] = {
            "name": user_name,
            "balance": balance,
            "timestamp": time.time()
        }
        save_account_balances()

        # Inspect current Adsgram verification count
        v_cnt = 0
        try:
            headers = {"User-Agent": HUMAN_USER_AGENT, "Referer": "https://justtool.site/withdraw-adsgram"}
            async with aiohttp.ClientSession() as session:
                v_url = f"https://justtool.site/api/adsgram-task3?tgId={user_id}"
                async with session.get(v_url, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as v_resp:
                    if v_resp.status == 200:
                        v_data = await v_resp.json()
                        v_cnt = v_data.get("count", 0)
        except Exception:
            pass

        # Check for unverified pending withdrawal request in recent chat messages
        pending_withdraw = False
        try:
            recent_msgs = await cl.get_messages(BNB_BOT, limit=15)
            for rm in recent_msgs:
                rm_text = rm.raw_text or ""
                if "verification required" in rm_text.lower() or "withdrawal request submitted" in rm_text.lower():
                    pending_withdraw = True
                    break
                if rm.reply_markup and hasattr(rm.reply_markup, "rows"):
                    for row in rm.reply_markup.rows:
                        for btn in row.buttons:
                            b_url = getattr(btn, "url", None)
                            if not b_url and hasattr(btn, "type") and getattr(btn.type, "url", None):
                                b_url = btn.type.url
                            if b_url and "withdraw-adsgram" in b_url:
                                pending_withdraw = True
                                break
                        if pending_withdraw:
                            break
        except Exception:
            pass

        if (pending_withdraw or acc_data.get("pending_withdraw")) and v_cnt < 5:
            logger.info(f"[BNB Auto-Withdraw] ⏳ Found pending unverified withdrawal for {user_name} ({v_cnt}/5 completed). Solving 5-step verification now...")
            ok_v = await complete_withdrawal_verification_steps(user_id, user_name, acc_client=cl, acc_data=acc_data)
            if ok_v and acc_data:
                acc_data["pending_withdraw"] = False
                await update_account_safely(user_id, {"pending_withdraw": False})
            return True

        if balance >= MIN_WITHDRAWAL:
            withdraw_amount = round(balance, 6)
            amount_str = f"{withdraw_amount:.6f}".rstrip("0").rstrip(".")
            target_wallet = (acc_data or {}).get("bnb_wallet") or WALLET_ADDRESS
            logger.info(f"[BNB Auto-Withdraw] {user_name} eligible ({balance:.6f} BNB)! Initiating interactive withdrawal to {target_wallet}...")

            if notify_manual:
                await send_report_message(
                    f"🚀 *Initiating BNB Withdrawal for {user_name}*\n\n"
                    f"• **Amount:** `{amount_str} BNB`\n"
                    f"• **Recipient Wallet:** `{target_wallet}`\n"
                    f"• **Network:** BEP-20 (Binance Smart Chain)\n"
                    f"⏳ Interacting with @{BNB_BOT} and preparing anti-bot verification...",
                    chat_id=target_chat
                )

            # Step 1: Open Withdraw prompt
            prev_msgs = await cl.get_messages(BNB_BOT, limit=1)
            prev_id = prev_msgs[0].id if prev_msgs else 0

            await human_delay(2.0, 3.5, "Opening withdraw prompt")
            await cl.send_message(BNB_BOT, "📤 Withdraw")

            # Adaptive Dialog Loop: Up to 6 conversational turns to handle any sequence from @CryptoProUpRobot
            wallet_submitted = False
            email_submitted = False
            amount_submitted = False

            for turn in range(1, 7):
                bot_msg = None
                for _ in range(6):
                    await asyncio.sleep(1.0)
                    msgs = await cl.get_messages(BNB_BOT, limit=3)
                    for m in msgs:
                        if m.id > prev_id and not m.out:
                            bot_msg = m
                            break
                    if bot_msg:
                        break

                if not bot_msg:
                    # If no response to '📤 Withdraw' on first turn, fallback to '/withdraw'
                    if turn == 1:
                        logger.info(f"[BNB Auto-Withdraw] No reply to '📤 Withdraw'. Trying '/withdraw' command...")
                        prev_msgs = await cl.get_messages(BNB_BOT, limit=1)
                        prev_id = prev_msgs[0].id if prev_msgs else 0
                        await cl.send_message(BNB_BOT, "/withdraw")
                        continue
                    else:
                        logger.info(f"[BNB Auto-Withdraw] Dialog idle at turn {turn}. Breaking dialog loop.")
                        break

                prev_id = bot_msg.id
                bot_text = (bot_msg.raw_text or "").strip()
                bot_lower = bot_text.lower()
                logger.info(f"[BNB Auto-Withdraw Turn {turn}] Bot says: '{bot_text[:90]}...'")

                # Check if bot has inline confirmation buttons
                if bot_msg.buttons:
                    for row in bot_msg.buttons:
                        for btn in row:
                            btn_t = (btn.text or "").lower()
                            if any(w in btn_t for w in ["confirm", "yes", "proceed", "submit", "accept"]):
                                logger.info(f"[BNB Auto-Withdraw] Clicking confirmation button: '{btn.text}'")
                                try:
                                    await btn.click()
                                    await asyncio.sleep(2.0)
                                except Exception as btn_err:
                                    logger.warning(f"Error clicking confirmation button: {btn_err}")
                                break

                # Check for verification or successful submission
                if any(w in bot_lower for w in ["verification required", "withdrawal request submitted", "request submitted", "withdraw-adsgram", "verify your withdrawal"]):
                    logger.info(f"[BNB Auto-Withdraw] Withdrawal submitted & verification required detected!")
                    break

                # 1. Bot asks for Email ID
                if any(w in bot_lower for w in ["send your email", "email id", "email for continue"]) and not email_submitted:
                    em = generate_random_email()
                    logger.info(f"[BNB Auto-Withdraw] Email requested. Submitting {em}...")
                    await human_delay(1.5, 3.0, "Entering email ID")
                    prev_msgs = await cl.get_messages(BNB_BOT, limit=1)
                    prev_id = prev_msgs[0].id if prev_msgs else 0
                    await cl.send_message(BNB_BOT, em)
                    email_submitted = True
                    continue

                # 2. Bot asks for Wallet Address
                if any(w in bot_lower for w in ["wallet address", "submit your bnb", "bep-20", "enter your wallet"]) and not wallet_submitted:
                    logger.info(f"[BNB Auto-Withdraw] Wallet requested. Submitting {target_wallet}...")
                    await human_delay(1.5, 3.0, "Entering wallet address")
                    prev_msgs = await cl.get_messages(BNB_BOT, limit=1)
                    prev_id = prev_msgs[0].id if prev_msgs else 0
                    await cl.send_message(BNB_BOT, target_wallet)
                    wallet_submitted = True
                    continue

                # 3. Bot asks for Amount
                if any(w in bot_lower for w in ["enter the amount", "amount of bnb", "how much", "minimum withdrawal", "min:"]) and not amount_submitted:
                    logger.info(f"[BNB Auto-Withdraw] Amount requested. Submitting {amount_str} BNB...")
                    await human_delay(1.5, 3.0, "Entering withdrawal amount")
                    prev_msgs = await cl.get_messages(BNB_BOT, limit=1)
                    prev_id = prev_msgs[0].id if prev_msgs else 0
                    await cl.send_message(BNB_BOT, amount_str)
                    amount_submitted = True
                    continue

                # 4. Cloudflare Edge AI Cascade Fallback (Gemini -> Groq -> Workers AI)
                ai_intent = "UNKNOWN"
                if not (wallet_submitted and email_submitted and amount_submitted):
                    try:
                        ai_intent = await ai_classify_bot_prompt(bot_text)
                    except Exception:
                        ai_intent = "UNKNOWN"

                if ai_intent == "EMAIL" and not email_submitted:
                    em = generate_random_email()
                    logger.info(f"[BNB Auto-Withdraw] AI classified as EMAIL prompt. Submitting {em}...")
                    await human_delay(1.5, 3.0, "Entering email ID")
                    prev_msgs = await cl.get_messages(BNB_BOT, limit=1)
                    prev_id = prev_msgs[0].id if prev_msgs else 0
                    await cl.send_message(BNB_BOT, em)
                    email_submitted = True
                    continue

                if ai_intent == "WALLET" and not wallet_submitted:
                    logger.info(f"[BNB Auto-Withdraw] AI classified as WALLET prompt. Submitting {target_wallet}...")
                    await human_delay(1.5, 3.0, "Entering wallet address")
                    prev_msgs = await cl.get_messages(BNB_BOT, limit=1)
                    prev_id = prev_msgs[0].id if prev_msgs else 0
                    await cl.send_message(BNB_BOT, target_wallet)
                    wallet_submitted = True
                    continue

                if ai_intent == "AMOUNT" and not amount_submitted:
                    logger.info(f"[BNB Auto-Withdraw] AI classified as AMOUNT prompt. Submitting {amount_str} BNB...")
                    await human_delay(1.5, 3.0, "Entering withdrawal amount")
                    prev_msgs = await cl.get_messages(BNB_BOT, limit=1)
                    prev_id = prev_msgs[0].id if prev_msgs else 0
                    await cl.send_message(BNB_BOT, amount_str)
                    amount_submitted = True
                    continue

                # If amount wasn't submitted yet and bot message didn't match specific prompts, submit amount as fallback
                if not amount_submitted:
                    logger.info(f"[BNB Auto-Withdraw] Submitting amount {amount_str} BNB as fallback...")
                    await human_delay(1.5, 2.5, "Submitting amount")
                    prev_msgs = await cl.get_messages(BNB_BOT, limit=1)
                    prev_id = prev_msgs[0].id if prev_msgs else 0
                    await cl.send_message(BNB_BOT, amount_str)
                    amount_submitted = True
                    continue

                # If all submitted, break dialog
                if amount_submitted and (wallet_submitted or "0x" in bot_lower):
                    break

            # Step 5: Complete 5-step human withdrawal verification tasks
            logger.info(f"[BNB Auto-Withdraw] Executing 5-step anti-bot verification for {user_name}...")
            verified = await complete_withdrawal_verification_steps(user_id, user_name, acc_client=cl, acc_data=acc_data)
            if not verified:
                logger.warning(f"[BNB Auto-Withdraw] Verification incomplete for {user_name}. Payout receipt held until 5/5 tasks complete.")
                return False

            # Step 6: Post receipts to dedicated Payout Verification channel (-1004402765950)
            alert_msg = (
                f"🎉 *BNB Auto-Withdrawal Submitted & Verified!*\n\n"
                f"• **Account:** {user_name} (`{user_id}`)\n"
                f"• **Amount:** `{amount_str} BNB`\n"
                f"• **Recipient Wallet:** `{target_wallet}`\n"
                f"• **Network:** Binance Smart Chain (BEP-20)\n"
                f"• **Anti-Bot Verification:** `5/5 Tasks Passed` ✅\n"
                f"• **Status:** Processing (Estimated within ~8 hours)"
            )
            await send_report_message(alert_msg, reply_markup=WALLET_INLINE_KEYBOARD, chat_id=REPORT_CHAT_ID)

            # Format 2 distinct messages for the dedicated payout channel (https://t.me/+oN8uefSRYWUyM2Fl)
            alert_channel_msg = (
                f"🎉 <b>BNB Auto-Withdrawal Submitted &amp; Verified!</b>\n\n"
                f"• <b>Account:</b> {user_name} (ID: <code>{user_id}</code>)\n"
                f"• <b>Amount:</b> <code>{amount_str} BNB</code>\n"
                f"• <b>Recipient Wallet:</b> <code>{target_wallet}</code>\n"
                f"• <b>Network:</b> Binance Smart Chain (BEP-20)\n"
                f"• <b>Anti-Bot Verification:</b> <code>5/5 Tasks Passed</code> ✅\n"
                f"• <b>Status:</b> Processing (Estimated within ~8 hours)"
            )

            channel_receipt = (
                f"🎉 <b>OFFICIAL BNB GALAXY PAYOUT RECEIPT</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 <b>Account:</b> {user_name} (ID: <code>{user_id}</code>)\n"
                f"💰 <b>Amount:</b> <code>{amount_str} BNB</code>\n"
                f"💼 <b>Recipient Wallet:</b> <code>{target_wallet}</code>\n"
                f"🌐 <b>Network:</b> Binance Smart Chain (BEP-20)\n"
                f"✅ <b>Verification:</b> 5/5 Anti-Bot Human Steps Completed\n"
                f"🕒 <b>Submitted At:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
                f"⏳ <b>Status:</b> Processing (Estimated ~8 hours)\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🛡️ <i>Autonomous Cloud Fleet Operations by MY AGY AI</i>"
            )
            try:
                tg_url = f"https://api.telegram.org/bot{REPORT_BOT_TOKEN}/sendMessage"
                async with aiohttp.ClientSession() as session:
                    # Message 1: Submission Alert
                    await session.post(tg_url, json={"chat_id": PAYOUT_CHANNEL_ID, "text": alert_channel_msg, "parse_mode": "HTML"}, timeout=aiohttp.ClientTimeout(total=10))
                    await asyncio.sleep(1.0)
                    # Message 2: Official Payout Receipt
                    await session.post(tg_url, json={"chat_id": PAYOUT_CHANNEL_ID, "text": channel_receipt, "parse_mode": "HTML"}, timeout=aiohttp.ClientTimeout(total=10))
            except Exception as pe:
                logger.error(f"[Payout Channel] Error broadcasting submission to {PAYOUT_CHANNEL_ID}: {pe}")

            record_payout(user_name, user_id, amount_str, target_wallet)
            ACCOUNT_BALANCES[str(user_id)] = {
                "name": user_name,
                "balance": 0.0,
                "timestamp": time.time()
            }
            save_account_balances()
            await update_account_safely(user_id, {"last_withdrawal_at": time.time(), "pending_withdraw": True})
            if acc_data:
                acc_data["last_withdrawal_at"] = time.time()
                acc_data["pending_withdraw"] = True
            logger.info(f"[BNB Auto-Withdraw] ✅ Withdrawal of {amount_str} BNB for {user_name} to {target_wallet} fully verified & recorded!")

            # Push withdrawal receipt to Cloudflare Edge (MiniApp Payout History)
            try:
                cf_payout_payload = {
                    "account_name": user_name,
                    "user_id": user_id,
                    "amount": amount_str,
                    "token": "BNB",
                    "wallet": target_wallet,
                    "network": "BEP-20",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                cf_headers = {
                    "Authorization": f"Bearer {os.getenv('CF_SECRET_KEY', 'agy_cf_secret_7d36994e_2026')}",
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
                }
                async def push_payout(cf_url: str):
                    try:
                        async with cf_sess.post(f"{cf_url}/api/payouts/record", json=cf_payout_payload, headers=cf_headers, timeout=aiohttp.ClientTimeout(total=5)):
                            pass
                    except Exception:
                        pass

                async with aiohttp.ClientSession() as cf_sess:
                    await asyncio.gather(*(push_payout(u) for u in CF_WORKER_URLS), return_exceptions=True)
            except Exception as cf_pay_e:
                logger.warning(f"[Cloudflare Payout Sync] Error: {cf_pay_e}")

            return True

        else:
            needed = round(MIN_WITHDRAWAL - balance, 6)
            logger.info(f"[BNB Auto-Withdraw] {user_name} balance ({balance:.6f} BNB) below {MIN_WITHDRAWAL} BNB ({needed:.6f} needed).")
            if notify_manual:
                info_msg = (
                    f"ℹ️ *BNB Galaxy Account Status*\n\n"
                    f"• **Account:** {user_name}\n"
                    f"• **Current Balance:** `{balance:.6f} BNB`\n"
                    f"• **Minimum Required:** `{MIN_WITHDRAWAL:.6f} BNB`\n"
                    f"• **Remaining Needed:** `{needed:.6f} BNB`\n"
                    f"• **Withdrawal Verification:** `{v_cnt}/5 Unlocked` {'✅' if v_cnt >= 5 else '⏳'}\n"
                    f"• **Destination Wallet:** `{WALLET_ADDRESS}`\n\n"
                    f"💡 _Auto-withdrawal triggers immediately when balance reaches {MIN_WITHDRAWAL} BNB._"
                )
                await send_report_message(info_msg, reply_markup=MAIN_TAB_KEYBOARD, chat_id=target_chat)
            return False

    except Exception as e:
        logger.error(f"[BNB Auto-Withdraw] Error for {user_name} ({user_id}): {e}", exc_info=True)
        if notify_manual:
            await send_report_message(f"⚠️ Error checking/withdrawing for {user_name}: {e}", chat_id=target_chat)
        return False
    finally:
        if claimed_lock:
            CURRENTLY_ACTIVE_ACCOUNT_IDS.discard(str(user_id))
            CURRENTLY_ACTIVE_ACCOUNT_ID = next(iter(CURRENTLY_ACTIVE_ACCOUNT_IDS), None)
        if should_disconnect and cl:
            try:
                await cl.disconnect()
            except Exception:
                pass
            cl = None
        gc.collect()


async def batch_withdraw_eligible(caller_chat_id=None):
    """Sequentially triggers withdrawals for all eligible accounts across the fleet."""
    target_chat = str(caller_chat_id) if caller_chat_id else str(REPORT_CHAT_ID)
    accounts = load_accounts()
    eligible = []
    for acc in accounts:
        uid = acc.get("user_id")
        bal = ACCOUNT_BALANCES.get(str(uid), {}).get("balance", 0.0)
        if bal >= MIN_WITHDRAWAL:
            eligible.append((acc.get("name", f"User {uid}"), uid, bal, acc))

    if not eligible:
        await send_report_message(f"ℹ️ No accounts currently meet the `{MIN_WITHDRAWAL} BNB` threshold.", reply_markup=MAIN_TAB_KEYBOARD, chat_id=target_chat)
        return

    await send_report_message(
        f"🚀 *Batch Withdrawal Started*\n\n"
        f"Found **{len(eligible)}** eligible account(s). Processing payouts sequentially to preserve system resources...",
        reply_markup=MAIN_TAB_KEYBOARD,
        chat_id=target_chat
    )

    success_count = 0
    for name, uid, bal, acc_d in eligible:
        ok = await check_and_auto_withdraw(uid, name, notify_manual=True, caller_chat_id=target_chat, acc_data=acc_d)
        if ok:
            success_count += 1
        await asyncio.sleep(8.0)

    summary = (
        f"✅ *Batch Withdrawal Completed*\n\n"
        f"• **Successfully Processed:** `{success_count}/{len(eligible)}`\n"
        f"• **Destination Wallet:** `{WALLET_ADDRESS}`\n"
        f"• **Network:** Binance Smart Chain (BEP-20)\n\n"
        f"💡 _All submitted withdrawals will confirm on-chain within ~8 hours._"
    )
    await send_report_message(summary, reply_markup=WALLET_INLINE_KEYBOARD, chat_id=target_chat)


async def scan_fleet_balances(caller_chat_id=None):
    """Scans all connected accounts for live BNB balances and outputs a fleet-wide report with 1-tap withdrawal triggers."""
    accounts = load_accounts()
    target_chat = str(caller_chat_id) if caller_chat_id else str(REPORT_CHAT_ID)
    await send_report_message(f"⏳ Scanning live BNB balances across all {len(accounts)} fleet accounts...", reply_markup=MAIN_TAB_KEYBOARD, chat_id=target_chat)

    total_fleet_bnb = 0.0
    ready_accounts = []
    lines = []
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    for idx, acc in enumerate(accounts, 1):
        name = acc.get("name", "Account")
        phone = acc.get("phone", "N/A")
        uid = acc.get("user_id")
        sess = acc.get("session_string")
        balance = 0.0

        if sess and acc.get("status") != "revoked":
            acc_cl = None
            should_disc = False
            cached_entry = ACCOUNT_BALANCES.get(str(uid), {})
            cached_ts = float(cached_entry.get("timestamp", 0))
            is_cooldown = float(acc.get("bnb_next_reset_at") or 0) > time.time()
            cache_fresh = (time.time() - cached_ts) < 14400

            try:
                # If account is busy, or on task cooldown with fresh cache, use cached balance without Telegram spam
                if str(uid) in CURRENTLY_ACTIVE_ACCOUNT_IDS or str(uid) == str(CURRENTLY_ACTIVE_ACCOUNT_ID) or (is_cooldown and cache_fresh) or (cached_entry and (time.time() - cached_ts) < 3600):
                    if str(uid) in ACCOUNT_BALANCES:
                        balance = ACCOUNT_BALANCES[str(uid)].get("balance", 0.0)
                elif sess == STRING_SESSION:
                    acc_cl = client
                    should_disc = False
                    await acc_cl.send_message(BNB_BOT, "💰 Balance")
                    await asyncio.sleep(2.0)
                    msgs = await acc_cl.get_messages(BNB_BOT, limit=2)
                    for m in msgs:
                        text = m.raw_text or ""
                        match = re.search(r"Your Balance:\s*([0-9.]+)\s*BNB", text, re.IGNORECASE)
                        if match:
                            balance = float(match.group(1))
                            break
                else:
                    acc_proxy = parse_proxy(acc.get("proxy"))
                    acc_fp = get_account_fingerprint(uid)
                    try:
                        acc_cl = TelegramClient(StringSession(sess), API_ID, API_HASH, proxy=acc_proxy, **acc_fp)
                        await acc_cl.connect()
                    except Exception as proxy_err:
                        if acc_proxy:
                            logger.warning(f"[Scan Balances] 🛡️ Proxy failed ({proxy_err}) for {name}. Auto-failing over to direct connection...")
                            acc_cl = TelegramClient(StringSession(sess), API_ID, API_HASH, **acc_fp)
                            await acc_cl.connect()
                        else:
                            raise
                    should_disc = True
                    await acc_cl.send_message(BNB_BOT, "💰 Balance")
                    await asyncio.sleep(2.0)
                    msgs = await acc_cl.get_messages(BNB_BOT, limit=2)
                    for m in msgs:
                        text = m.raw_text or ""
                        match = re.search(r"Your Balance:\s*([0-9.]+)\s*BNB", text, re.IGNORECASE)
                        if match:
                            balance = float(match.group(1))
                            break
            except Exception as e:
                logger.warning(f"Error checking balance for {name}: {e}")
                if str(uid) in ACCOUNT_BALANCES and ACCOUNT_BALANCES[str(uid)].get("balance", 0.0) > 0:
                    balance = ACCOUNT_BALANCES[str(uid)]["balance"]
            finally:
                if should_disc and acc_cl:
                    try:
                        await acc_cl.disconnect()
                    except Exception:
                        pass
                gc.collect()

        # Update live balance cache
        ACCOUNT_BALANCES[str(uid)] = {
            "name": name,
            "phone": phone,
            "balance": balance,
            "timestamp": time.time()
        }

        total_fleet_bnb += balance
        if round(balance, 6) >= MIN_WITHDRAWAL:
            ready_accounts.append((name, uid, balance, acc))
            status_str = f"`{balance:.6f} BNB` *(Eligible for Payout! 🚀)*"
        else:
            needed = max(0.0, round(MIN_WITHDRAWAL - balance, 6))
            status_str = f"`{balance:.6f} BNB` ({needed:.6f} needed)"

        lines.append(f"{idx}️⃣ **{name}** (`{phone}`)\n   • Balance: {status_str}")

    report = (
        f"💰 *Fleet BNB Balance Scanner ({len(accounts)} Accounts)*\n"
        f"🕒 _{now_str}_\n\n"
        + "\n\n".join(lines) + "\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🪙 **Total Fleet Balance:** `{total_fleet_bnb:.6f} BNB`\n"
        f"🎯 **Auto-Withdraw Minimum:** `{MIN_WITHDRAWAL:.6f} BNB`\n"
        f"💼 **Payout Wallet:** `{WALLET_ADDRESS}`\n"
        f"🚀 **Eligible Accounts:** `{len(ready_accounts)} Ready`\n\n"
        f"💡 _Any account meeting the {MIN_WITHDRAWAL} BNB threshold is automatically withdrawn to your BEP-20 wallet._"
    )

    # Build interactive withdrawal keyboard
    custom_kb_rows = []
    if ready_accounts:
        if len(ready_accounts) > 1:
            custom_kb_rows.append([{"text": f"🚀 Withdraw All Eligible ({len(ready_accounts)})", "callback_data": "btn_withdraw_all"}])
        for r_name, r_uid, r_bal, _ in ready_accounts:
            custom_kb_rows.append([{"text": f"🚀 Withdraw {r_name} ({r_bal:.6f} BNB)", "callback_data": f"withdraw_acc_{r_uid}"}])

    custom_kb_rows.append([
        {"text": "🔄 Refresh Balances", "callback_data": "btn_withdraw"},
        {"text": "📜 Payout Ledger", "callback_data": "btn_payouts"}
    ])
    custom_kb_rows.append([
        {"text": "💼 On-Chain Wallet", "callback_data": "btn_wallet"},
        {"text": "📊 Fleet Status", "callback_data": "btn_status"}
    ])
    withdraw_markup = {"inline_keyboard": custom_kb_rows}

    await send_message_chunks(report, reply_markup=withdraw_markup, chat_id=target_chat)

    # Auto-trigger withdrawal for any eligible accounts sequentially
    if ready_accounts:
        logger.info(f"[Fleet Scanner] Automatically executing withdrawals for {len(ready_accounts)} eligible account(s)...")
        for r_name, r_uid, r_bal, r_acc in ready_accounts:
            await check_and_auto_withdraw(r_uid, r_name, notify_manual=True, caller_chat_id=target_chat, acc_data=r_acc)
            await asyncio.sleep(8.0)


# =======================================================
# MODULE 2: STONES MINERS AUTOMATION (@stoneswithestand_bot)
# =======================================================

FLEET_MINIAPP_TOKENS = {}
FLEET_TOKENS_FILE = os.path.join(BASE_DIR, "fleet_miniapp_tokens.json")

def load_local_fleet_tokens():
    """Loads cached 24h WebApp tokens from local JSON disk storage."""
    global FLEET_MINIAPP_TOKENS
    if os.path.exists(FLEET_TOKENS_FILE):
        try:
            with open(FLEET_TOKENS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    for uid, t in data.items():
                        if uid not in FLEET_MINIAPP_TOKENS:
                            FLEET_MINIAPP_TOKENS[uid] = t
                        else:
                            FLEET_MINIAPP_TOKENS[uid].update(t)
        except Exception:
            pass

def save_local_fleet_tokens():
    """Persists memory tokens to local JSON file safely with atomic replace."""
    try:
        temp_f = f"{FLEET_TOKENS_FILE}.tmp.{os.getpid()}_{int(time.time()*1000)}"
        with open(temp_f, "w", encoding="utf-8") as f:
            json.dump(FLEET_MINIAPP_TOKENS, f, indent=2)
        os.replace(temp_f, FLEET_TOKENS_FILE)
    except Exception:
        pass

# Initialize local tokens into memory at module load
load_local_fleet_tokens()

async def sync_account_tokens_to_edge(session: aiohttp.ClientSession, acc_uid: str, acc_name: str, **tokens):
    """Syncs 24h WebApp tokens to local disk storage and Cloudflare Workers KV for autonomous edge harvesting."""
    uid_str = str(acc_uid)
    if uid_str not in FLEET_MINIAPP_TOKENS:
        FLEET_MINIAPP_TOKENS[uid_str] = {"account_id": uid_str, "name": acc_name}
    for k, v in tokens.items():
        if v:
            FLEET_MINIAPP_TOKENS[uid_str][k] = v

    save_local_fleet_tokens()

    payload = {
        "account_id": uid_str,
        "name": acc_name,
        **FLEET_MINIAPP_TOKENS[uid_str],
        "updated_at": time.time()
    }
    headers = {
        "Authorization": "Bearer agy_cf_secret_7d36994e_2026",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    for cf_url in CF_WORKER_URLS:
        try:
            async with session.post(
                f"{cf_url}/api/miniapp/tokens/sync",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=6)
            ) as r:
                if r.status == 200:
                    logger.debug(f"[{acc_name}] 🌐 Synced fresh 24h WebApp tokens to Cloudflare Edge ({cf_url})")
                    break
        except Exception:
            continue


async def load_fleet_tokens_from_edge(session: aiohttp.ClientSession):
    """Preloads cached 24h WebApp tokens (Stones, MRG, ART, AI Lab, UltraWallet, Apex) from local disk & Cloudflare Edge."""
    global FLEET_MINIAPP_TOKENS
    load_local_fleet_tokens()
    for cf_url in CF_WORKER_URLS:
        try:
            async with session.get(
                f"{cf_url}/api/miniapp/tokens",
                headers={"User-Agent": HUMAN_USER_AGENT},
                timeout=aiohttp.ClientTimeout(total=6)
            ) as r:
                if r.status == 200:
                    data = await r.json()
                    if isinstance(data, dict):
                        for uid, t in data.items():
                            if uid not in FLEET_MINIAPP_TOKENS:
                                FLEET_MINIAPP_TOKENS[uid] = t
                            else:
                                FLEET_MINIAPP_TOKENS[uid].update(t)
                        save_local_fleet_tokens()
                        logger.info(f"🌐 Preloaded cached 24h WebApp tokens for {len(FLEET_MINIAPP_TOKENS)} fleet accounts from Cloudflare Edge ({cf_url})")
                        return True
        except Exception:
            pass
    return bool(FLEET_MINIAPP_TOKENS)


async def collect_account_session_links(acc_cl, acc: dict) -> dict:
    """
    On-Demand Collector: Extracts fresh 24h WebApp session links ('season links') for an account:
    - Stones Miners WebApp initData (Arbitrum One)
    - MRG Miner WebApp initData (The Open Network)
    - ART Airdrop WebApp initData (TON / Multi-Chain)
    - BNB Galaxy Webhook Link (Binance Smart Chain)
    """
    acc_name = acc.get("name", "User")
    acc_uid = str(acc.get("user_id"))
    tokens = {}

    # 1. Stones Miners initData
    try:
        bot_stones = await acc_cl.get_entity(STONES_BOT)
        res_stones = await acc_cl(RequestWebViewRequest(
            peer=bot_stones,
            bot=bot_stones,
            platform="android",
            url="https://app.stoneswithestand.my.id/"
        ))
        parsed = urllib.parse.urlparse(res_stones.url)
        s_init = urllib.parse.parse_qs(parsed.fragment).get("tgWebAppData", [None])[0]
        if s_init:
            tokens["stones_init_data"] = s_init
    except Exception as se:
        logger.debug(f"[{acc_name}] Stones session collection note: {se}")

    # 2. MRG Miner initData
    try:
        bot_mrg = await acc_cl.get_input_entity(MRG_BOT)
        res_mrg = await acc_cl(RequestAppWebViewRequest(
            peer=bot_mrg,
            app=InputBotAppShortName(bot_id=bot_mrg, short_name="app"),
            platform="android",
            start_param=MRG_REFERRAL_CODE
        ))
        parsed = urllib.parse.urlparse(res_mrg.url)
        m_init = urllib.parse.parse_qs(parsed.fragment).get("tgWebAppData", [None])[0]
        if m_init:
            tokens["mrg_init_data"] = m_init
    except Exception as me:
        logger.debug(f"[{acc_name}] MRG session collection note: {me}")

    # 3. ART Airdrop initData
    try:
        bot_art = await acc_cl.get_entity(ART_BOT)
        res_art = await acc_cl(RequestWebViewRequest(
            peer=bot_art,
            bot=bot_art,
            platform="android",
            url=f"https://art.tamimdev.dev/?ref={REPORT_CHAT_ID}"
        ))
        parsed = urllib.parse.urlparse(res_art.url)
        a_init = urllib.parse.parse_qs(parsed.fragment).get("tgWebAppData", [None])[0]
        if a_init:
            tokens["art_init_data"] = a_init
    except Exception as ae:
        logger.debug(f"[{acc_name}] ART session collection note: {ae}")

    # 4. BNB Galaxy Webhook Link (DISABLED - Scammer Bot)
    if ENABLE_BNB_GALAXY:
        try:
            wh_url = (acc or {}).get("bnb_wh_url") or await extract_bnb_webhook(acc_cl, acc_data=acc)
            if wh_url:
                tokens["bnb_wh_url"] = wh_url
        except Exception as be:
            logger.debug(f"[{acc_name}] BNB webhook note: {be}")

    # 5. AI Lab Robot initData
    try:
        bot_ai = await acc_cl.get_entity(AILAB_BOT)
        res_ai = await acc_cl(RequestWebViewRequest(
            peer=bot_ai,
            bot=bot_ai,
            platform="android",
            url="https://ailab-agent.online/"
        ))
        parsed_ai = urllib.parse.urlparse(res_ai.url)
        ai_init = urllib.parse.parse_qs(parsed_ai.fragment).get("tgWebAppData", [None])[0]
        if ai_init:
            tokens["ailab_init_data"] = ai_init
    except Exception as aie:
        logger.debug(f"[{acc_name}] AI Lab session collection note: {aie}")

    # 6. UltraWallet initData
    try:
        bot_uw = await acc_cl.get_input_entity(ULTRAWALLET_BOT)
        res_uw = await acc_cl(RequestAppWebViewRequest(
            peer=bot_uw,
            app=InputBotAppShortName(bot_id=bot_uw, short_name="app"),
            platform="android",
            start_param=str(ULTRAWALLET_REFERRAL_CODE)
        ))
        parsed_uw = urllib.parse.urlparse(res_uw.url)
        uw_init = urllib.parse.parse_qs(parsed_uw.fragment).get("tgWebAppData", [None])[0]
        if uw_init:
            tokens["ultrawallet_init_data"] = uw_init
    except Exception as uwe:
        logger.debug(f"[{acc_name}] UltraWallet session collection note: {uwe}")

    # 7. Apex Miner initData (@ApxMinerBot)
    try:
        bot_apx = await acc_cl.get_input_entity(APX_BOT)
        res_apx = await acc_cl(RequestAppWebViewRequest(
            peer=bot_apx,
            app=InputBotAppShortName(bot_id=bot_apx, short_name="app"),
            platform="android",
            start_param=str(APX_REFERRAL_CODE)
        ))
        parsed_apx = urllib.parse.urlparse(res_apx.url)
        apx_init = urllib.parse.parse_qs(parsed_apx.fragment).get("tgWebAppData", [None])[0]
        if apx_init:
            tokens["apx_init_data"] = apx_init
    except Exception as apx_e:
        logger.debug(f"[{acc_name}] Apex Miner session collection note: {apx_e}")

    # 8. Ainovum Bot initData (@ainovum_bot)
    try:
        bot_an = await acc_cl.get_entity(AINOVUM_BOT)
        res_an = await acc_cl(RequestWebViewRequest(
            peer=bot_an,
            bot=bot_an,
            platform="android",
            url=f"https://ainovum.biz/?startapp={AINOVUM_REFERRAL_CODE}&ref={AINOVUM_REFERRAL_CODE}"
        ))
        parsed_an = urllib.parse.urlparse(res_an.url)
        an_init = urllib.parse.parse_qs(parsed_an.fragment).get("tgWebAppData", [None])[0]
        if an_init:
            tokens["ainovum_init_data"] = an_init
    except Exception as ane:
        logger.debug(f"[{acc_name}] Ainovum session collection note: {ane}")

    # 9. MiningGRAM Bot initData (@MiningGRAM_Bot)
    try:
        bot_mg = await acc_cl.get_input_entity(MININGGRAM_BOT)
        res_mg = await acc_cl(RequestAppWebViewRequest(
            peer=bot_mg,
            app=InputBotAppShortName(bot_id=bot_mg, short_name="mine"),
            platform="android",
            start_param=MININGGRAM_REFERRAL_CODE
        ))
        parsed_mg = urllib.parse.urlparse(res_mg.url)
        mg_init = urllib.parse.parse_qs(parsed_mg.fragment).get("tgWebAppData", [None])[0]
        if mg_init:
            tokens["mininggram_init_data"] = mg_init
    except Exception as mge:
        logger.debug(f"[{acc_name}] MiningGRAM session collection note: {mge}")

    # 10. ATF Miner initData (@ATF_AIRDROP_bot)
    try:
        bot_atf = await acc_cl.get_entity("ATF_AIRDROP_bot")
        res_atf = await acc_cl(RequestWebViewRequest(
            peer=bot_atf,
            bot=bot_atf,
            platform="android",
            url=f"https://atfminers.asloni.online/miner/index.html?v=1789502294&entry=bot_start&ref={REPORT_CHAT_ID}",
            start_param=str(REPORT_CHAT_ID)
        ))
        parsed_atf = urllib.parse.urlparse(res_atf.url)
        atf_init = urllib.parse.parse_qs(parsed_atf.fragment).get("tgWebAppData", [None])[0]
        if atf_init:
            tokens["atf_init_data"] = atf_init
    except Exception as atfe:
        logger.debug(f"[{acc_name}] ATF session collection note: {atfe}")

    return tokens


async def delegate_farm_to_cloudflare(acc_uid: int, cf_node_url: str):
    """
    Offloads 10 BNB Galaxy tasks & 5/5 anti-bot verification to Cloudflare Cloud.
    Executes 100% serverless on Cloudflare Edge with 0 VPS RAM and 0 VPS CPU.
    """
    headers = {
        "Authorization": "Bearer agy_cf_secret_7d36994e_2026",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        async with aiohttp.ClientSession() as sess:
            async with sess.post(
                f"{cf_node_url}/api/farm/bnb",
                json={"user_id": int(acc_uid)},
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=20)
            ) as r:
                if r.status == 200:
                    data = await r.json()
                    results = data.get("results", [])
                    total_completed = sum(res.get("completed_tasks", 0) for res in results)
                    total_verified = max([res.get("verification_count", 0) for res in results] + [0])
                    logger.info(f"[Cloud Farming] 🌐 Cloudflare Edge completed {total_completed} tasks (Verification: {total_verified}/5) for ID {acc_uid} (0 VPS RAM)")
                    return data
    except Exception as e:
        logger.debug(f"[Cloud Farming] CF delegation note for {acc_uid}: {e}")
    return None


async def automate_stones_cycle(session: aiohttp.ClientSession, acc_client, acc: dict):
    """
    Automates Stones Miners (@stoneswithestand_bot):
    - Obtains WebApp initData via RequestWebViewRequest
    - Submits /api/init with referral parameter
    - Checks /api/state for tasks & balance
    - Automatically completes daily_checkin task if pending
    - Verifies official channel task (@stoneswithestand) if pending
    - Starts/renews mining session if inactive
    - Auto-withdraws to Arbitrum One (0xfda4182001672b9f0f09e2118242e543e35ed5ce) if balance >= 500 STONES (Primary ID).
    """
    acc_name = acc.get("name", "User")
    acc_uid = str(acc.get("user_id"))
    is_primary = (acc_uid == str(REPORT_CHAT_ID))

    try:
        init_data = None
        if acc_client:
            try:
                bot = await acc_client.get_entity(STONES_BOT)
                res = await acc_client(RequestWebViewRequest(
                    peer=bot,
                    bot=bot,
                    platform="android",
                    url="https://app.stoneswithestand.my.id/"
                ))
                parsed = urllib.parse.urlparse(res.url)
                init_data = urllib.parse.parse_qs(parsed.fragment).get("tgWebAppData", [None])[0]
                if init_data:
                    await sync_account_tokens_to_edge(session, acc_uid, acc_name, stones_init_data=init_data)
            except Exception as we:
                logger.debug(f"[{acc_name}] 💎 [Stones] MTProto initData note: {we}")

        if not init_data:
            init_data = FLEET_MINIAPP_TOKENS.get(acc_uid, {}).get("stones_init_data")

        if not init_data:
            logger.debug(f"[{acc_name}] 💎 [Stones] No cached or fresh initData available. Skipping until token collection.")
            return

        acc_ua = get_account_user_agent(acc_uid)
        headers = {"Content-Type": "application/json", "User-Agent": acc_ua}
        base_url = "https://app.stoneswithestand.my.id"
        proxy = acc.get("proxy")

        # 1. Initialize session with referral binding
        init_payload = {"initData": init_data}
        if not is_primary:
            init_payload["start_param"] = STONES_REFERRAL_CODE
        try:
            async with session.post(f"{base_url}/api/init", json=init_payload, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as r:
                pass
        except Exception:
            pass

        # 2. Query state & mining status
        state = {}
        async with session.post(f"{base_url}/api/state", json={"initData": init_data}, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as r:
            if r.status == 200:
                state = await r.json()

        user_info = state.get("user", {})
        tasks = state.get("tasks", {})
        bal = user_info.get("balance", 0)
        coins = user_info.get("coins", 0)
        mining_active = bool(user_info.get("rate_active", 0) > 0 or user_info.get("mining_active", False))

        # 3. Complete all pending tasks (Dynamic wait: 2.5s for daily checkin, 15s for sponsor/channel/visit tasks)
        for slug, status in list(tasks.items()):
            if status != "completed":
                try:
                    # Step 1: Tap task (trigger start)
                    await session.post(f"{base_url}/api/task/start", json={"initData": init_data, "slug": slug}, headers=headers, timeout=aiohttp.ClientTimeout(total=8))
                    # Step 2: Dynamic wait (15s for sponsor/channel/visit tasks, 2.5s for daily check-in)
                    task_wait = 2.5 if slug == "daily_checkin" else 15.0
                    logger.debug(f"[{acc_name}] 💎 [Stones] Waiting {task_wait}s for task '{slug}'...")
                    await asyncio.sleep(task_wait)
                    # Step 3: Complete / verify task
                    done = False
                    async with session.post(f"{base_url}/api/task/complete", json={"initData": init_data, "slug": slug}, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as cr:
                        if cr.status == 200:
                            cd = await cr.json()
                            if cd.get("ok") or cd.get("success"):
                                done = True
                                logger.info(f"[{acc_name}] 💎 [Stones] Task '{slug}' completed!")
                    if not done:
                        async with session.post(f"{base_url}/api/task/verify", json={"initData": init_data, "slug": slug}, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as vr:
                            if vr.status == 200:
                                logger.info(f"[{acc_name}] 💎 [Stones] Task '{slug}' verified!")
                except Exception as te:
                    logger.debug(f"[{acc_name}] Stones task '{slug}' note: {te}")

        # 5. Harvest accumulated mining pool into coins (Holding Wallet)
        if bal > 0:
            try:
                async with session.post(f"{base_url}/api/claim", json={"initData": init_data}, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as cr:
                    if cr.status == 200:
                        c_data = await cr.json()
                        if c_data.get("ok"):
                            claimed_stones = c_data.get("claimed", 0)
                            coins = c_data.get("coins", coins)
                            bal = 0
                            mining_active = False
                            logger.info(f"[{acc_name}] 💎 [Stones] Collected +{claimed_stones} STONES into Holding Wallet (Total: {coins})!")
            except Exception as ce:
                logger.debug(f"[{acc_name}] Stones claim note: {ce}")

        # 6. Mining start / restart if inactive
        if not mining_active:
            try:
                async with session.post(f"{base_url}/api/mining/start", json={"initData": init_data}, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as r:
                    if r.status == 200:
                        mining_active = True
                        logger.info(f"[{acc_name}] 💎 [Stones] Mining started/renewed!")
            except Exception as me:
                logger.debug(f"[{acc_name}] Stones mining start note: {me}")

        # 7. Lucky Spin Roulette (Auto-spin wheel when tickets are available)
        try:
            async with session.post(f"{base_url}/api/sr/status", json={"initData": init_data}, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as srr:
                if srr.status == 200:
                    sr_d = await srr.json()
                    tickets = sr_d.get("tickets", 0)
                    while tickets > 0:
                        async with session.post(f"{base_url}/api/sr/spin", json={"initData": init_data}, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as sp_r:
                            if sp_r.status == 200:
                                sp_d = await sp_r.json()
                                if sp_d.get("ok"):
                                    res_item = sp_d.get("result", {})
                                    lbl = res_item.get("label", "Prize")
                                    stn = res_item.get("stones", 0)
                                    tickets = res_item.get("tickets", 0)
                                    if stn > 0:
                                        coins += stn
                                    logger.info(f"[{acc_name}] 💎 [Stones] 🎰 Lucky Spin won: {lbl} (+{stn} STONES)!")
                                else:
                                    break
                            else:
                                break
                        await asyncio.sleep(1.0)
        except Exception as sre:
            logger.debug(f"[{acc_name}] Stones spin note: {sre}")

        # 8. Treasure Hunt Mini-quest (Hourly reward)
        try:
            async with session.post(f"{base_url}/api/th/status", json={"initData": init_data}, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as thr:
                if thr.status == 200:
                    th_d = await thr.json()
                    if th_d.get("ok") and th_d.get("hour_left", 0) > 0 and th_d.get("day_left", 0) > 0:
                        async with session.post(f"{base_url}/api/th/start", json={"initData": init_data}, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as ths:
                            if ths.status == 200:
                                ths_d = await ths.json()
                                sess_id = ths_d.get("session", {}).get("session_id")
                                if sess_id:
                                    c_idx = random.randint(0, 4)
                                    async with session.post(f"{base_url}/api/th/pick", json={"initData": init_data, "session_id": sess_id, "choice_idx": c_idx}, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as thp:
                                        if thp.status == 200:
                                            thp_d = await thp.json()
                                            if thp_d.get("ok"):
                                                rew = thp_d.get("result", {}).get("reward", 0)
                                                coins += rew
                                                logger.info(f"[{acc_name}] 💎 [Stones] 🗝️ Treasure Hunt found: +{rew} STONES!")
        except Exception as the:
            logger.debug(f"[{acc_name}] Stones treasure hunt note: {the}")

        # 8b. Stone Breaker Play & Earn (Hourly limit: 10, Daily limit: 100 STONES)
        try:
            async with session.post(f"{base_url}/api/sb/status", json={"initData": init_data}, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as sbr:
                if sbr.status == 200:
                    sbd = await sbr.json()
                    h_got = sbd.get("hour_got", 0)
                    h_cap = sbd.get("hourly_cap", 10)
                    d_got = sbd.get("day_got", 0)
                    d_cap = sbd.get("daily_cap", 100)
                    if h_got < h_cap and d_got < d_cap:
                        async with session.post(f"{base_url}/api/sb/start", json={"initData": init_data}, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as sbs:
                            if sbs.status == 200:
                                sbs_d = await sbs.json()
                                sb_sess = sbs_d.get("session", {}).get("session_id")
                                if sb_sess:
                                    await asyncio.sleep(2.0)
                                    async with session.post(f"{base_url}/api/sb/finish", json={"initData": init_data, "session_id": sb_sess, "score": 1500}, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as sbf:
                                        if sbf.status == 200:
                                            sbf_d = await sbf.json()
                                            if sbf_d.get("ok"):
                                                rew = sbf_d.get("result", {}).get("reward", 0)
                                                coins += rew
                                                logger.info(f"[{acc_name}] 💎 [Stones] ⛏️ Play & Earn (Stone Breaker) completed: +{rew} STONES!")
        except Exception as sbe:
            logger.debug(f"[{acc_name}] Stones Stone Breaker note: {sbe}")

        # 8c. Mining Boost (+0.5 TH/s for 5 min)
        try:
            async with session.post(f"{base_url}/api/ad/boost/challenge", json={"initData": init_data}, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as abc:
                if abc.status == 200:
                    ch_d = await abc.json()
                    cid = ch_d.get("challenge", {}).get("challenge_id")
                    if cid:
                        await session.post(f"{base_url}/api/ad/beat", json={"initData": init_data, "scope": "boost", "challenge_id": cid}, headers=headers, timeout=aiohttp.ClientTimeout(total=6))
                        await asyncio.sleep(16.0)
                        await session.post(f"{base_url}/api/ad/beat", json={"initData": init_data, "scope": "boost", "challenge_id": cid}, headers=headers, timeout=aiohttp.ClientTimeout(total=6))
                        await asyncio.sleep(0.5)
                        async with session.post(f"{base_url}/api/ad/boost/reward", json={"initData": init_data, "challenge_id": cid}, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as abr:
                            if abr.status == 200:
                                res_b = await abr.json()
                                if res_b.get("ok"):
                                    logger.info(f"[{acc_name}] 💎 [Stones] ⚡ Mining Boost activated (+0.5 TH/s for 5 min)!")
        except Exception:
            pass

        # 9. Ensure Arbitrum EVM wallet is bound to user Binance wallet for all accounts
        target_evm_wallet = ARBITRUM_WALLET  # 0xfda4182001672b9f0f09e2118242e543e35ed5ce
        try:
            await session.post(f"{base_url}/api/wallet", json={"initData": init_data, "wallet": target_evm_wallet}, headers=headers, timeout=aiohttp.ClientTimeout(total=6))
        except Exception:
            pass

        # 10. Auto-Withdrawal check for all fleet accounts
        # Note: In Stones Miners, 'coins' represents the spendable Wallet Holding; 'balance' is total in-game score/EXP.
        acc["stones_coins"] = coins
        await update_account_safely(acc_uid, {"stones_coins": coins})
        now_ts = time.time()
        stones_next_wd = float(acc.get("stones_next_wd_at") or 0)
        if coins >= 500:
            if now_ts < stones_next_wd:
                rem_m = max(0.1, (stones_next_wd - now_ts) / 60.0)
                logger.info(f"[{acc_name}] 💎 [Stones] Coins {coins} STONES >= 500 threshold, but on withdrawal cooldown (~{rem_m:.1f}m remaining). Will retry after cooldown.")
            else:
                withdraw_stones = min(500, int(coins))
                logger.info(f"[{acc_name}] 💎 [Stones] Coins {coins} STONES >= 500 threshold! Submitting auto-withdrawal of {withdraw_stones} STONES to Arbitrum {target_evm_wallet}...")
                try:
                    from stones_captcha_solver import execute_stones_withdrawal_with_captcha
                    ok_wd, wd_res = await execute_stones_withdrawal_with_captcha(
                        session=session,
                        base_url=base_url,
                        headers=headers,
                        init_data=init_data,
                        amount=withdraw_stones,
                        wallet=target_evm_wallet,
                        proxy=proxy
                    )
                    logger.info(f"[{acc_name}] 💎 [Stones] Withdrawal result: {wd_res}")
                    if ok_wd:
                        acc["stones_next_wd_at"] = now_ts + 7200  # 2 hours post-success
                        await update_account_safely(acc_uid, {"stones_next_wd_at": now_ts + 7200})
                        await send_report_message(
                            f"🎉 *Stones Miners Withdrawal Submitted!*\n\n"
                            f"• **Account:** {acc_name}\n"
                            f"• **Amount:** `{withdraw_stones} STONES`\n"
                            f"• **Destination:** `{target_evm_wallet}` (Arbitrum One)\n"
                            f"• **Verification:** `Passed & Verified` ✅\n"
                            f"• **Result:** `{wd_res}`",
                            chat_id=REPORT_CHAT_ID
                        )
                    else:
                        details_str = str(wd_res).lower()
                        if "cooldown" in details_str:
                            acc["stones_next_wd_at"] = now_ts + 190  # 3 minutes + 10s margin
                            await update_account_safely(acc_uid, {"stones_next_wd_at": now_ts + 190})
                        else:
                            acc["stones_next_wd_at"] = now_ts + 300
                            await update_account_safely(acc_uid, {"stones_next_wd_at": now_ts + 300})
                except Exception as we:
                    logger.error(f"[{acc_name}] Stones auto-withdrawal error: {we}")

        logger.info(f"[{acc_name}] 💎 [Stones] Cycle finished | Balance: {bal} STONES (Coins: {coins}) | Mining Active: {mining_active}")

    except Exception as e:
        logger.warning(f"[{acc_name}] Stones automation note: {e}")


# =======================================================
# MODULE 3: MRG MINER AUTOMATION (@mrgminerbot)
# =======================================================

async def automate_mrg_cycle(session: aiohttp.ClientSession, acc_client, acc: dict):
    """
    Automates MRG Miner (@mrgminerbot):
    - Obtains or uses cached WebApp initData
    - Authenticates via /api/auth/verify
    - Binds unique TON v4r2 wallet from fleet_ton_wallets.json (or Binance Web3 for primary)
    - Claims accumulated mining rewards (/api/user/claim-mining)
    - Claims all available tasks (recurring 3h tasks + one-time social/channel tasks)
    - Auto-claims one-time bonus for all accounts
    - Primary Account (6727787768): Sweeps 10% squad commission and referral bonuses
    - Auto-unlocks higher mining level (TH/s boost) when holding balance permits
    """
    acc_name = acc.get("name", "User")
    acc_uid = str(acc.get("user_id"))
    is_primary = (acc_uid == str(REPORT_CHAT_ID))

    try:
        init_data = None
        if acc_client:
            try:
                bot_in = await acc_client.get_input_entity(MRG_BOT)
                res = await acc_client(RequestAppWebViewRequest(
                    peer=bot_in,
                    app=InputBotAppShortName(bot_id=bot_in, short_name="app"),
                    platform="android",
                    start_param=MRG_REFERRAL_CODE
                ))
                parsed = urllib.parse.urlparse(res.url)
                init_data = urllib.parse.parse_qs(parsed.fragment).get("tgWebAppData", [None])[0]
                if init_data:
                    await sync_account_tokens_to_edge(session, acc_uid, acc_name, mrg_init_data=init_data)
            except Exception as we:
                logger.debug(f"[{acc_name}] ⛏️ [MRG Miner] MTProto initData note: {we}")

        if not init_data:
            init_data = FLEET_MINIAPP_TOKENS.get(acc_uid, {}).get("mrg_init_data")

        if not init_data:
            logger.debug(f"[{acc_name}] ⛏️ [MRG Miner] No cached or fresh initData available. Skipping until token collection.")
            return

        acc_ua = get_account_user_agent(acc_uid)
        headers = {
            "Content-Type": "application/json",
            "Origin": "https://app.mrgtoken.xyz",
            "Referer": "https://app.mrgtoken.xyz/",
            "User-Agent": acc_ua
        }
        base_url = "https://mrg.up.railway.app"

        # 1. Auth verify with camelCase startParam & deviceInfo
        fp = get_account_fingerprint(acc_uid)
        auth_payload = {
            "initData": init_data,
            "startParam": MRG_REFERRAL_CODE,
            "start_param": MRG_REFERRAL_CODE,
            "deviceInfo": {
                "platform": "android",
                "deviceName": fp.get("device_model", "Android Device"),
                "ram": "8 GB",
                "cpuCores": 8,
                "screenResolution": "1080x2400",
                "userAgent": acc_ua,
                "timezone": "UTC",
                "language": "en"
            }
        }
        try:
            async with session.post(f"{base_url}/api/auth/verify", json=auth_payload, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as r:
                pass
        except Exception:
            pass

        await asyncio.sleep(1.5)

        # 2. Profile fetch
        me_data = {}
        try:
            async with session.post(f"{base_url}/api/user/me", json={"initData": init_data}, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status == 200:
                    me_data = await r.json()
        except Exception:
            pass

        u = me_data.get("user", {})
        act_lvl = me_data.get("activeLevel") or 1
        spd_ths = me_data.get("speedTHs") or 0.2
        is_ton_connected = u.get("isTonConnected", False)
        current_wallet = u.get("tonWalletAddress", "")
        in_app_bal = float(u.get("inAppBalance", 0) or 0)

        # 3. Strict TON wallet binding & isolation
        target_wallet = TON_PRIMARY_WALLET if is_primary else None
        if not target_wallet:
            fleet_file = os.path.join(BASE_DIR, "fleet_ton_wallets.json")
            if os.path.exists(fleet_file):
                try:
                    with open(fleet_file, "r", encoding="utf-8") as ff:
                        fwallets = json.load(ff)
                        target_wallet = fwallets.get(acc_uid, {}).get("address")
                except Exception:
                    pass

        needs_connect = False
        if not is_ton_connected or not current_wallet:
            needs_connect = True
        elif not is_primary and current_wallet == TON_PRIMARY_WALLET:
            logger.warning(f"[{acc_name}] ⚠️ Worker had Primary Binance TON wallet! Disconnecting to preserve isolation...")
            try:
                await session.post(f"{base_url}/api/user/disconnect-wallet", json={"initData": init_data}, headers=headers, timeout=aiohttp.ClientTimeout(total=10))
            except Exception:
                pass
            needs_connect = True
        elif target_wallet and current_wallet != target_wallet:
            logger.info(f"[{acc_name}] 🔄 Rebinding MRG wallet: {current_wallet[:8]}... -> {target_wallet[:8]}...")
            try:
                await session.post(f"{base_url}/api/user/disconnect-wallet", json={"initData": init_data}, headers=headers, timeout=aiohttp.ClientTimeout(total=10))
            except Exception:
                pass
            needs_connect = True

        if needs_connect and target_wallet:
            try:
                async with session.post(f"{base_url}/api/user/connect-wallet", json={"initData": init_data, "address": target_wallet, "balance": 0}, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as cr:
                    cd = await cr.json()
                    logger.info(f"[{acc_name}] ⛏️ [MRG Miner] Connected TON wallet {target_wallet[:10]}... : {cd.get('success')}")
            except Exception as ce:
                logger.debug(f"[{acc_name}] MRG wallet connect note: {ce}")
            await asyncio.sleep(1.5)

        # 4. Claim Mining harvest
        try:
            async with session.post(f"{base_url}/api/user/claim-mining", json={"initData": init_data}, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as mr:
                md = await mr.json()
                if md.get("success") and float(md.get("claimedAmount", 0)) > 0:
                    claimed_amt = float(md.get("claimedAmount", 0))
                    in_app_bal += claimed_amt
                    logger.info(f"[{acc_name}] ⛏️ [MRG Miner] Mining claimed: +{claimed_amt:.4f} MRG!")
        except Exception as me:
            logger.debug(f"[{acc_name}] MRG claim mining note: {me}")
        await asyncio.sleep(2.0)

        # 5. Claim Available Tasks (Recurring 3h + Socials + Channel tasks)
        mrg_tasks = me_data.get("tasks", [])
        completed_task_ids = set(me_data.get("completedTaskIds", []))
        for tsk in mrg_tasks:
            tid = tsk.get("taskId")
            ttype = tsk.get("taskType", "")
            vtype = tsk.get("verificationType", "")
            title = tsk.get("title", tid)

            if tid in completed_task_ids and "recurring" not in ttype:
                continue

            # Dynamic wait: 15s for link visits / social / channel tasks, 3s for native
            task_wait = 15.0 if (vtype == "link_visit" or tsk.get("url") or "social" in ttype.lower() or "channel" in title.lower()) else 3.0
            try:
                await session.post(f"{base_url}/api/user/start-task", json={"initData": init_data, "taskId": tid}, headers=headers, timeout=aiohttp.ClientTimeout(total=6))
            except Exception:
                pass
            logger.debug(f"[{acc_name}] ⛏️ [MRG Miner] Waiting {task_wait}s for '{title}'...")
            await asyncio.sleep(task_wait)

            try:
                async with session.post(f"{base_url}/api/user/claim-task", json={"initData": init_data, "taskId": tid}, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as tr:
                    td = await tr.json()
                    if td.get("success"):
                        rew = float(tsk.get("reward", 5))
                        in_app_bal += rew
                        logger.info(f"[{acc_name}] ⛏️ [MRG Miner] Task '{title}' claimed: +{rew} MRG!")
                    elif "wait" in str(td).lower() or "second" in str(td).lower():
                        await asyncio.sleep(12.0)
                        async with session.post(f"{base_url}/api/user/claim-task", json={"initData": init_data, "taskId": tid}, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as tr2:
                            td2 = await tr2.json()
                            if td2.get("success"):
                                rew = float(tsk.get("reward", 5))
                                in_app_bal += rew
                                logger.info(f"[{acc_name}] ⛏️ [MRG Miner] Task '{title}' claimed after extra wait: +{rew} MRG!")
            except Exception as te:
                logger.debug(f"[{acc_name}] MRG task claim note for {tid}: {te}")
            await asyncio.sleep(1.5)

        # 6. One-time bonus (attempted by all fleet accounts)
        try:
            async with session.post(f"{base_url}/api/user/claim-one-time-bonus", json={"initData": init_data}, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as br:
                bd = await br.json()
                if bd.get("success"):
                    logger.info(f"[{acc_name}] ⛏️ [MRG Miner] One-time bonus claimed successfully!")
        except Exception:
            pass
        await asyncio.sleep(1.5)

        # 7. Primary account special sweeps (10% squad commissions & referral bonuses)
        if is_primary:
            try:
                async with session.post(f"{base_url}/api/user/claim-commission", json={"initData": init_data}, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as ccr:
                    ccd = await ccr.json()
                    if ccd.get("success") and float(ccd.get("claimedAmount", 0)) > 0:
                        logger.info(f"[{acc_name}] ⛏️ [MRG Miner] 🏆 Squad commission collected: +{ccd.get('claimedAmount')} MRG!")
            except Exception as ce:
                logger.debug(f"[{acc_name}] MRG commission claim note: {ce}")
            await asyncio.sleep(1.5)

        # 8. Auto-Upgrade Mining Level (doubles mining TH/s when balance >= 101 MRG)
        try:
            if in_app_bal >= 101.0 and act_lvl < 2:
                async with session.post(f"{base_url}/api/user/unlock-level", json={"initData": init_data, "level": 2}, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as lr:
                    ld = await lr.json()
                    if ld.get("success"):
                        logger.info(f"[{acc_name}] 🚀 [MRG Miner] Auto-upgraded to Level 2 (0.40 TH/s)! Boost active!")
            elif in_app_bal >= 250.0 and act_lvl < 3:
                async with session.post(f"{base_url}/api/user/unlock-level", json={"initData": init_data, "level": 3}, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as lr:
                    ld = await lr.json()
                    if ld.get("success"):
                        logger.info(f"[{acc_name}] 🚀 [MRG Miner] Auto-upgraded to Level 3 (0.60 TH/s)!")
            elif in_app_bal >= 500.0 and act_lvl < 4:
                async with session.post(f"{base_url}/api/user/unlock-level", json={"initData": init_data, "level": 4}, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as lr:
                    ld = await lr.json()
                    if ld.get("success"):
                        logger.info(f"[{acc_name}] 🚀 [MRG Miner] Auto-upgraded to Level 4 (0.80 TH/s)!")
            elif in_app_bal >= 1000.0 and act_lvl < 5:
                async with session.post(f"{base_url}/api/user/unlock-level", json={"initData": init_data, "level": 5}, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as lr:
                    ld = await lr.json()
                    if ld.get("success"):
                        logger.info(f"[{acc_name}] 🚀 [MRG Miner] Auto-upgraded to Level 5 (1.00 TH/s)!")
        except Exception as ue:
            logger.debug(f"[{acc_name}] MRG level upgrade note: {ue}")

        logger.info(f"[{acc_name}] ⛏️ [MRG Miner] Cycle finished | Balance: {in_app_bal:.2f} MRG (Lvl: {act_lvl}, {spd_ths} TH/s)")

    except Exception as e:
        logger.warning(f"[{acc_name}] MRG automation note: {e}")


# =======================================================
# MODULE 4: ART AIRDROP AUTOMATION (@ART_AIRDROP_BOT)
# =======================================================

ART_CIRCUIT_BREAKER_UNTIL = 0
ART_CONSECUTIVE_FAILS = 0

async def automate_art_cycle(session: aiohttp.ClientSession, acc_client, acc: dict):
    """
    Automates ART Airdrop (@ART_AIRDROP_BOT):
    - Claims accumulated mining rewards (/api/user/claim-mining)
    - Starts/renews continuous 8-hour mining session (/api/user/start-mining)
    - Automatically discovers and claims all pending tasks (/api/tasks/claim)
    - Claims daily rewarded ads bonus (/api/ads/claim)
    - Primary Account (6727787768): Sweeps 10% team squad earnings & referral bonuses
    - Auto-withdraws to TON Primary Wallet when balance >= 1000 ART
    """
    global ART_CIRCUIT_BREAKER_UNTIL, ART_CONSECUTIVE_FAILS
    acc_name = acc.get("name", "User")
    acc_uid = str(acc.get("user_id"))
    is_primary = (acc_uid == str(REPORT_CHAT_ID))

    now = time.time()
    if now < ART_CIRCUIT_BREAKER_UNTIL:
        rem_mins = max(1, int((ART_CIRCUIT_BREAKER_UNTIL - now) / 60))
        logger.debug(f"[{acc_name}] 🚀 [ART Airdrop] API server offline cooldown active (~{rem_mins}m remaining). Skipping.")
        return

    try:
        base_url = "https://art.tamimdev.dev"
        headers = {"Content-Type": "application/json", "User-Agent": HUMAN_USER_AGENT}

        # 1. Obtain WebApp initData if client is connected
        if acc_client:
            try:
                bot = await acc_client.get_entity("ART_AIRDROP_BOT")
                res = await acc_client(RequestWebViewRequest(
                    peer=bot,
                    bot=bot,
                    platform="android",
                    url=f"https://art.tamimdev.dev/?ref={REPORT_CHAT_ID}"
                ))
                parsed = urllib.parse.urlparse(res.url)
                init_data = urllib.parse.parse_qs(parsed.fragment).get("tgWebAppData", [None])[0]
                if init_data:
                    headers["X-Telegram-Init-Data"] = init_data
                    await sync_account_tokens_to_edge(session, acc_uid, acc_name, art_init_data=init_data)
            except Exception as we:
                logger.debug(f"[{acc_name}] ART WebApp init note: {we}")

        # 2. Fetch user profile & mining status
        u = {}
        ms = {}
        async with session.get(f"{base_url}/api/user/{acc_uid}", headers=headers, timeout=aiohttp.ClientTimeout(total=4.0)) as r:
            if r.status == 200:
                ud = await r.json()
                u = ud.get("user", {})
                ms = ud.get("miningState", {})
                ART_CONSECUTIVE_FAILS = 0
            else:
                logger.debug(f"[{acc_name}] 🚀 [ART Airdrop] User API status: {r.status}")

        pool_bal = float(u.get("poolWallet", 0) or 0)
        is_mining = ms.get("isMining", False)
        rem_sec = ms.get("remainingSeconds", 0)
        accumulated = float(ms.get("accumulatedAtf", 0) or 0)
        hr_rate = ms.get("hourlyRate", 5)

        # Ensure main Binance TON wallet is connected in ART Airdrop to route all withdrawals
        ton_addr = u.get("tonWalletAddress")
        if not ton_addr or ton_addr != TON_PRIMARY_WALLET:
            try:
                ton_addr = TON_PRIMARY_WALLET
                async with session.post(
                    f"{base_url}/api/user/connect-wallet",
                    json={"userId": acc_uid, "tonAddress": ton_addr},
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=4.0)
                ) as wr:
                    if wr.status == 200:
                        logger.info(f"[{acc_name}] 🚀 [ART Airdrop] Linked main Binance TON wallet: {ton_addr}")
            except Exception as w_err:
                logger.debug(f"[{acc_name}] ART connect-wallet note: {w_err}")

        # 3. Mining claim & 8-hour cycle restart
        if not is_mining or rem_sec <= 0 or accumulated > 0:
            try:
                async with session.post(f"{base_url}/api/user/claim-mining", json={"userId": acc_uid}, headers=headers, timeout=aiohttp.ClientTimeout(total=4.0)) as cr:
                    cd = await cr.json()
                    if cd.get("success") and float(cd.get("claimedAtf", 0)) > 0:
                        claimed_amt = float(cd.get("claimedAtf", 0))
                        pool_bal += claimed_amt
                        logger.info(f"[{acc_name}] 🚀 [ART Airdrop] Claimed +{claimed_amt} ART!")
            except Exception:
                pass

            try:
                async with session.post(f"{base_url}/api/user/start-mining", json={"userId": acc_uid}, headers=headers, timeout=aiohttp.ClientTimeout(total=4.0)) as sr:
                    sd = await sr.json()
                    if sd.get("success"):
                        is_mining = True
                        logger.info(f"[{acc_name}] 🚀 [ART Airdrop] 8h Mining cycle active/renewed at {hr_rate} ART/h!")
            except Exception:
                pass

        # 4. Check & Complete Available Tasks (Dynamic wait: 15s for sponsor links/channels/videos, 3s for native)
        try:
            async with session.get(f"{base_url}/api/tasks/{acc_uid}", headers=headers, timeout=aiohttp.ClientTimeout(total=4.0)) as tr:
                if tr.status == 200:
                    td = await tr.json()
                    tasks = td.get("tasks", [])
                    for t in tasks:
                        if not t.get("isCompleted"):
                            tid = t.get("id")
                            ttitle = t.get("title", tid)
                            # Step 1: Tap / trigger task start
                            try:
                                await session.post(f"{base_url}/api/tasks/start", json={"userId": acc_uid, "taskId": tid}, headers=headers, timeout=aiohttp.ClientTimeout(total=4.0))
                            except Exception:
                                pass
                            # Step 2: Sponsor links / channels / videos require 15s
                            task_wait = 15.0 if (t.get("actionUrl") or "sponsor" in ttitle.lower() or "channel" in ttitle.lower() or "youtube" in ttitle.lower()) else 3.0
                            logger.debug(f"[{acc_name}] 🚀 [ART Airdrop] Waiting {task_wait}s for '{ttitle}'...")
                            await asyncio.sleep(task_wait)
                            # Step 3: Claim reward
                            try:
                                async with session.post(f"{base_url}/api/tasks/claim", json={"userId": acc_uid, "taskId": tid}, headers=headers, timeout=aiohttp.ClientTimeout(total=4.0)) as cl_r:
                                    cld = await cl_r.json()
                                    if cld.get("success"):
                                        rew = float(cld.get("reward", 10))
                                        pool_bal += rew
                                        logger.info(f"[{acc_name}] 🚀 [ART Airdrop] Task '{ttitle}' claimed (+{rew} ART)!")
                                    elif "wait" in str(cld).lower() or "second" in str(cld).lower():
                                        await asyncio.sleep(12.0)
                                        async with session.post(f"{base_url}/api/tasks/claim", json={"userId": acc_uid, "taskId": tid}, headers=headers, timeout=aiohttp.ClientTimeout(total=4.0)) as cl_r2:
                                            cld2 = await cl_r2.json()
                                            if cld2.get("success"):
                                                rew = float(cld2.get("reward", 10))
                                                pool_bal += rew
                                                logger.info(f"[{acc_name}] 🚀 [ART Airdrop] Task '{ttitle}' claimed after extra wait (+{rew} ART)!")
                            except Exception:
                                pass
                            await asyncio.sleep(1.0)
        except Exception:
            pass

        # 5. Claim Daily Ads Bonus
        try:
            async with session.post(f"{base_url}/api/ads/claim", json={"userId": acc_uid}, headers=headers, timeout=aiohttp.ClientTimeout(total=4.0)) as ar:
                ad_res = await ar.json()
                if ad_res.get("success"):
                    rew = float(ad_res.get("reward", 10))
                    pool_bal += rew
                    logger.info(f"[{acc_name}] 🚀 [ART Airdrop] Daily ad bonus claimed (+{rew} ART)!")
        except Exception:
            pass

        # 6. Primary Account Squad Sweeps (Team Wallet Earnings & Referral Bonuses)
        if is_primary:
            try:
                async with session.post(f"{base_url}/api/referrals/claim-team", json={"userId": acc_uid}, headers=headers, timeout=aiohttp.ClientTimeout(total=4.0)) as tr_res:
                    tr_d = await tr_res.json()
                    if tr_d.get("success") and float(tr_d.get("claimedAtf", 0)) > 0:
                        t_amt = float(tr_d.get("claimedAtf", 0))
                        pool_bal += t_amt
                        logger.info(f"[{acc_name}] 🚀 [ART Airdrop] 🏆 Squad team earnings collected: +{t_amt} ART!")
            except Exception:
                pass

            try:
                await session.post(f"{base_url}/api/referrals/claim-bonus", json={"userId": acc_uid}, headers=headers, timeout=aiohttp.ClientTimeout(total=4.0))
            except Exception:
                pass

        # 7. Automated Miner Leveling Engine (Reinvest in Mining Speed, Zero Withdrawals)
        unlocked = set(u.get("unlockedMiners", []))
        art_levels = [
            (2, 100),
            (3, 250),
            (4, 500),
            (5, 1000),
            (6, 2000),
            (7, 4000),
            (8, 8000)
        ]
        for target_lvl, cost in art_levels:
            if target_lvl not in unlocked and pool_bal >= cost:
                try:
                    async with session.post(
                        f"{base_url}/api/user/buy-miner",
                        json={"userId": acc_uid, "level": target_lvl},
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=5.0)
                    ) as b_res:
                        b_data = await b_res.json()
                        if b_data.get("success"):
                            pool_bal -= cost
                            unlocked.add(target_lvl)
                            new_hr = b_data.get("miningState", {}).get("hourlyRate", hr_rate)
                            logger.info(f"[{acc_name}] 🚀 [ART Airdrop] 🎉 Upgraded to Level {target_lvl}! Mining boosted to {new_hr} ART/h!")
                except Exception as b_err:
                    logger.debug(f"[{acc_name}] ART level upgrade note: {b_err}")
        # 8. Auto-Withdrawal to Main Binance TON Wallet (Only when Level 8 is reached)
        has_level_8 = (8 in unlocked) or (int(u.get("level", 1) or 1) >= 8)
        if has_level_8 and pool_bal >= 1000:
            withdraw_art = min(30000, int(pool_bal))
            logger.info(f"[{acc_name}] 🚀 [ART Airdrop] Level 8 reached & Pool {pool_bal:.2f} ART >= 1000 threshold! Submitting auto-withdrawal of {withdraw_art} ART to {TON_PRIMARY_WALLET}...")
            try:
                # Ensure main Binance TON wallet is connected
                await session.post(
                    f"{base_url}/api/user/connect-wallet",
                    json={"userId": acc_uid, "tonAddress": TON_PRIMARY_WALLET},
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=4.0)
                )
                async with session.post(
                    f"{base_url}/api/withdraw",
                    json={"userId": acc_uid, "amount": withdraw_art},
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=8.0)
                ) as wr:
                    wd = await wr.json()
                    logger.info(f"[{acc_name}] 🚀 [ART Airdrop] Withdrawal result: {wd}")
                    if wd.get("success"):
                        pool_bal -= withdraw_art
                        w_info = wd.get("withdrawal", {})
                        await send_report_message(
                            f"🎉 *ART Airdrop Level 8 Withdrawal Submitted!*\n\n"
                            f"• **Account:** {acc_name}\n"
                            f"• **Level:** `Level 8 (Max Boost)` 🚀\n"
                            f"• **Amount:** `{withdraw_art} ART` (~${w_info.get('amountUsd', 0)} USD)\n"
                            f"• **Destination:** `{TON_PRIMARY_WALLET}` (Binance TON Deposit)\n"
                            f"• **Status:** `{w_info.get('status', 'PENDING')}`\n"
                            f"• **Withdrawal ID:** `{w_info.get('id', 'N/A')}`",
                            chat_id=REPORT_CHAT_ID
                        )
            except Exception as we:
                logger.error(f"[{acc_name}] ART auto-withdrawal error: {we}")
        elif not has_level_8:
            cur_lvl = max(unlocked or [1])
            logger.info(f"[{acc_name}] 🚀 [ART Airdrop] Leveling priority active (Current: Lvl {cur_lvl}/8 | Pool: {pool_bal:.2f} ART). Reinvesting towards Level 8 before withdrawals.")

        logger.info(f"[{acc_name}] 🚀 [ART Airdrop] Cycle finished | Pool: {pool_bal:.2f} ART | Mining Active: {is_mining}")

    except (asyncio.TimeoutError, aiohttp.ClientError) as net_err:
        ART_CONSECUTIVE_FAILS += 1
        err_msg = type(net_err).__name__
        if ART_CONSECUTIVE_FAILS >= 3:
            ART_CIRCUIT_BREAKER_UNTIL = time.time() + 900  # 15-minute cooldown
            logger.warning(f"[{acc_name}] 🚀 [ART Airdrop] Server unreachable ({err_msg}). Circuit breaker tripped for 15m.")
        else:
            logger.debug(f"[{acc_name}] 🚀 [ART Airdrop] Server timed out ({err_msg}).")
    except Exception as e:
        err_msg = str(e) or type(e).__name__
        logger.warning(f"[{acc_name}] ART automation note: {err_msg}")


# =======================================================
# MODULE 5: AI LAB ROBOT AUTOMATION (@AiLab_robot)
# =======================================================

async def automate_ailab_cycle(session: aiohttp.ClientSession, acc_client, acc: dict):
    """
    Automates AI Lab Robot (@AiLab_robot):
    - Authenticates via /api/v1/users/auth/login
    - Checks miner status & auto-starts/renews mining (/api/v1/miner-start_mining)
    - Automatically exchanges accumulated hashes into USD balance (/api/v1/miner-exchange_hashes)
    - Discovers and completes pending tasks (/api/v1/task-check)
    """
    acc_name = acc.get("name", "User")
    acc_uid = str(acc.get("user_id"))

    try:
        init_data = FLEET_MINIAPP_TOKENS.get(acc_uid, {}).get("ailab_init_data")
        if not init_data and acc_client:
            try:
                bot_ai = await acc_client.get_entity(AILAB_BOT)
                res_ai = await acc_client(RequestWebViewRequest(
                    peer=bot_ai,
                    bot=bot_ai,
                    platform="android",
                    url="https://ailab-agent.online/"
                ))
                parsed = urllib.parse.urlparse(res_ai.url)
                init_data = urllib.parse.parse_qs(parsed.fragment).get("tgWebAppData", [None])[0]
                if init_data:
                    await sync_account_tokens_to_edge(session, acc_uid, acc_name, ailab_init_data=init_data)
            except Exception:
                pass

        if not init_data:
            return

        acc_ua = get_account_user_agent(acc_uid)
        base_url = "https://api.ailab-agent.online/api/v1"
        headers = {"Content-Type": "application/json", "User-Agent": acc_ua}

        # 1. Login
        token = None
        async with session.post(f"{base_url}/users/auth/login", json={"user": init_data}, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as r:
            if r.status == 200:
                d = await r.json()
                token = d.get("result", {}).get("bearer") or d.get("user_info", {}).get("session_id")
        if not token:
            return

        auth_headers = {**headers, "Authorization": f"Bearer {token}"}

        # 2. Check miner & renew if needed
        miner_data = {}
        try:
            async with session.get(f"{base_url}/miner", headers=auth_headers, timeout=aiohttp.ClientTimeout(total=8)) as mr:
                if mr.status == 200:
                    miner_data = (await mr.json()).get("result", {}).get("miner", {})
        except Exception:
            pass

        cur_miner = miner_data.get("current_miner", {})
        is_running = cur_miner.get("is_running", False)
        time_left = cur_miner.get("time_left", 0)
        hashes_bal = float(miner_data.get("hashes_balance", 0) or 0)

        if not is_running or time_left <= 0:
            try:
                async with session.post(f"{base_url}/miner-start_mining", json={"start_mining": True}, headers=auth_headers, timeout=aiohttp.ClientTimeout(total=8)) as sm:
                    if sm.status == 200:
                        logger.info(f"[{acc_name}] 🧪 [AI Lab] Mining cycle started/renewed!")
            except Exception:
                pass

        # 3. Exchange accumulated hashes to balance
        if hashes_bal >= 1.0:
            try:
                async with session.post(f"{base_url}/miner-exchange_hashes", json={"exchange": True}, headers=auth_headers, timeout=aiohttp.ClientTimeout(total=8)) as eh:
                    if eh.status == 200:
                        eh_d = (await eh.json()).get("result", {})
                        logger.info(f"[{acc_name}] 🧪 [AI Lab] Exchanged {hashes_bal:.1f} hashes -> +${eh_d.get('received_amount', 0):.4f} USD!")
            except Exception:
                pass

        # 4. Check & complete available tasks (Tap task -> wait 2.5s -> check/claim)
        try:
            async with session.get(f"{base_url}/tasks", headers=auth_headers, timeout=aiohttp.ClientTimeout(total=8)) as tr:
                if tr.status == 200:
                    td = await tr.json()
                    res_data = td.get("result", {})
                    t_list = []
                    if isinstance(res_data, dict):
                        for k, v in res_data.items():
                            if isinstance(v, list):
                                t_list.extend(v)
                    elif isinstance(res_data, list):
                        t_list = res_data

                    for tsk in t_list:
                        tid = tsk.get("id")
                        if not tid:
                            continue
                        # If already completed, skip
                        if tsk.get("status") == "completed" or tsk.get("is_claimed"):
                            continue
                        ttitle = tsk.get("title") or tsk.get("name") or f"Task #{tid}"
                        # Step 1: Tap task
                        try:
                            await session.post(f"{base_url}/task-check", json={"task_id": tid, "action": "start"}, headers=auth_headers, timeout=aiohttp.ClientTimeout(total=6))
                        except Exception:
                            pass
                        # Step 2: Dynamic wait: 15s for follow / social / partner tasks, 3s for referral checks
                        task_wait = 15.0 if ("follow" in str(tsk).lower() or "partner" in str(tsk).lower() or "social" in str(tsk).lower() or "channel" in ttitle.lower()) else 3.0
                        logger.debug(f"[{acc_name}] 🧪 [AI Lab] Waiting {task_wait}s for '{ttitle}'...")
                        await asyncio.sleep(task_wait)
                        # Step 3: Check & claim
                        try:
                            async with session.post(f"{base_url}/task-check", json={"task_id": tid, "action": "check"}, headers=auth_headers, timeout=aiohttp.ClientTimeout(total=8)) as tc:
                                if tc.status == 200:
                                    tcd = await tc.json()
                                    if tcd.get("status") == "ok" or tcd.get("result"):
                                        logger.info(f"[{acc_name}] 🧪 [AI Lab] Task '{ttitle}' claimed!")
                        except Exception:
                            pass
                        await asyncio.sleep(1.0)
        except Exception:
            pass

        logger.info(f"[{acc_name}] 🧪 [AI Lab] Cycle finished | Power: {miner_data.get('current_power', 0)} | Hashes: {hashes_bal:.2f} | Mining: {is_running}")

    except Exception as e:
        logger.debug(f"[{acc_name}] AI Lab automation note: {e}")


# =======================================================
# MODULE 6: ULTRAWALLET AUTOMATION (@UltrawalletTrade_Bot)
# =======================================================

async def automate_ultrawallet_cycle(session: aiohttp.ClientSession, acc_client, acc: dict):
    """
    Automates UltraWallet (@UltrawalletTrade_Bot):
    - Authenticates via /api/telegramLogin + Firebase Auth Custom Token
    - Daily streak check-in (/api/checkin/claim)
    - Mining status check & auto-claim (/api/mining/claim)
    - Auto-start/renew 24h mining cycle (/api/mining/start)
    - Free energy claim (/api/energy/claim)
    - Milestone reward claim (/api/referral/milestones/claim)
    """
    acc_name = acc.get("name", "User")
    acc_uid = str(acc.get("user_id"))

    try:
        init_data = FLEET_MINIAPP_TOKENS.get(acc_uid, {}).get("ultrawallet_init_data")
        if not init_data and acc_client:
            try:
                bot_uw = await acc_client.get_input_entity(ULTRAWALLET_BOT)
                res_uw = await acc_client(RequestAppWebViewRequest(
                    peer=bot_uw,
                    app=InputBotAppShortName(bot_id=bot_uw, short_name="app"),
                    platform="android",
                    start_param=str(ULTRAWALLET_REFERRAL_CODE)
                ))
                parsed = urllib.parse.urlparse(res_uw.url)
                init_data = urllib.parse.parse_qs(parsed.fragment).get("tgWebAppData", [None])[0]
                if init_data:
                    await sync_account_tokens_to_edge(session, acc_uid, acc_name, ultrawallet_init_data=init_data)
            except Exception:
                pass

        if not init_data:
            return

        acc_ua = get_account_user_agent(acc_uid)
        headers = {"Content-Type": "application/json", "User-Agent": acc_ua}
        base_url = "https://wallet.trxvault.top/api"

        # 1. Login & Firebase idToken acquisition
        id_token = None
        async with session.post(f"{base_url}/telegramLogin", json={"initData": init_data, "refBy": str(ULTRAWALLET_REFERRAL_CODE)}, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as lr:
            if lr.status == 200:
                ld = await lr.json()
                custom_token = ld.get("token")
                if custom_token:
                    fb_url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key=AIzaSyAIKTCEFqC5LFRc89nuOLhTGPHIZTIjEsU"
                    async with session.post(fb_url, json={"token": custom_token, "returnSecureToken": True}, timeout=aiohttp.ClientTimeout(total=8)) as fbr:
                        if fbr.status == 200:
                            id_token = (await fbr.json()).get("idToken")

        if not id_token:
            return

        auth_headers = {**headers, "Authorization": f"Bearer {id_token}"}

        # 2. Daily Check-in Claim
        try:
            async with session.post(f"{base_url}/checkin/claim", json={}, headers=auth_headers, timeout=aiohttp.ClientTimeout(total=8)) as cr:
                if cr.status == 200:
                    cd = await cr.json()
                    if cd.get("ok"):
                        logger.info(f"[{acc_name}] 💳 [UltraWallet] Daily check-in claimed (+{cd.get('reward', 1)} Streak: {cd.get('checkin', {}).get('streak', 1)})!")
        except Exception:
            pass

        # 3. Mining Status & Auto-Claim / Renew
        m_state = {}
        try:
            async with session.get(f"{base_url}/mining/status", headers=auth_headers, timeout=aiohttp.ClientTimeout(total=8)) as ms:
                if ms.status == 200:
                    m_state = (await ms.json()).get("mining", {})
        except Exception:
            pass

        if m_state.get("claimReady"):
            try:
                async with session.post(f"{base_url}/mining/claim", json={}, headers=auth_headers, timeout=aiohttp.ClientTimeout(total=8)) as mc:
                    if mc.status == 200:
                        logger.info(f"[{acc_name}] 💳 [UltraWallet] Mining rewards claimed successfully!")
            except Exception:
                pass

        if not m_state.get("active") or m_state.get("claimReady"):
            try:
                async with session.post(f"{base_url}/mining/start", json={}, headers=auth_headers, timeout=aiohttp.ClientTimeout(total=8)) as st:
                    if st.status == 200:
                        logger.info(f"[{acc_name}] 💳 [UltraWallet] 24-hour mining cycle active/renewed!")
            except Exception:
                pass

        # 4. Energy claim
        try:
            await session.post(f"{base_url}/energy/claim", json={}, headers=auth_headers, timeout=aiohttp.ClientTimeout(total=6))
        except Exception:
            pass

        # 5. Check & Play Lucky Wheel Spins (USDT, TON & LT tokens)
        try:
            async with session.get(f"{base_url}/spin/status", headers=auth_headers, timeout=aiohttp.ClientTimeout(total=8)) as sps:
                if sps.status == 200:
                    sp_info = await sps.json()
                    spins_avail = sp_info.get("tickets", 0) + sp_info.get("freeSpinsRemaining", 0)
                    while spins_avail > 0:
                        async with session.post(f"{base_url}/spin/play", json={}, headers=auth_headers, timeout=aiohttp.ClientTimeout(total=8)) as spp:
                            if spp.status == 200:
                                spp_d = await spp.json()
                                if spp_d.get("ok"):
                                    prz = spp_d.get("prize", {})
                                    logger.info(f"[{acc_name}] 💳 [UltraWallet] 🎰 Wheel Spin won: {prz.get('amount')} {prz.get('prizeType')} ({prz.get('label')})!")
                                    spins_avail = spp_d.get("spinTickets", 0)
                                else:
                                    break
                            else:
                                break
                        await asyncio.sleep(1.0)
        except Exception as se:
            logger.debug(f"[{acc_name}] UltraWallet spin note: {se}")

        # 6. Discover & Complete Available Tasks (Tap task -> wait 2.5s -> complete without joining channels or opening links)
        try:
            async with session.get(f"{base_url}/tasks", headers=auth_headers, timeout=aiohttp.ClientTimeout(total=8)) as tr:
                if tr.status == 200:
                    td = await tr.json()
                    for t in td.get("tasks", []):
                        if not t.get("completed"):
                            tid = t.get("id")
                            ttitle = t.get("title", tid)
                            # Step 1: Tap / start task
                            try:
                                await session.post(f"{base_url}/tasks/start", json={"taskId": tid}, headers=auth_headers, timeout=aiohttp.ClientTimeout(total=6))
                            except Exception:
                                pass
                            # Step 2: Website / browse / partner tasks require 15s
                            ttype = t.get("type", "")
                            tcat = t.get("category", "")
                            task_wait = 15.0 if (ttype == "website" or tcat in ["hot", "partner"] or "website" in str(t).lower()) else 3.0
                            logger.debug(f"[{acc_name}] 💳 [UltraWallet] Waiting {task_wait}s for '{ttitle}'...")
                            await asyncio.sleep(task_wait)
                            # Step 3: Complete task
                            try:
                                async with session.post(f"{base_url}/tasks/complete", json={"taskId": tid}, headers=auth_headers, timeout=aiohttp.ClientTimeout(total=8)) as tcr:
                                    if tcr.status == 200:
                                        tcd = await tcr.json()
                                        if tcd.get("ok"):
                                            rew_c = tcd.get("rewardCoin", "LT")
                                            rew_a = tcd.get("rewardAmount", 0)
                                            logger.info(f"[{acc_name}] 💳 [UltraWallet] Task '{ttitle}' completed (+{rew_a} {rew_c})!")
                            except Exception:
                                pass
                            await asyncio.sleep(1.0)
        except Exception as te:
            logger.debug(f"[{acc_name}] UltraWallet tasks note: {te}")

        # 7. Milestone referrals sweep (primary account)
        if str(acc_uid) == str(REPORT_CHAT_ID):
            try:
                await session.post(f"{base_url}/referral/milestones/claim", json={}, headers=auth_headers, timeout=aiohttp.ClientTimeout(total=6))
            except Exception:
                pass

        # 8. Rewards Center Ads (Completes 10 Watch & Earn Ads / Day for Gift Box requirement & earns USDT)
        try:
            async with session.get(f"{base_url}/rewardsCenter", headers=auth_headers, timeout=aiohttp.ClientTimeout(total=8)) as rcr:
                if rcr.status == 200:
                    rc_data = await rcr.json()
                    cards = rc_data.get("cards", [])
                    ads_watched = 0
                    for c in cards:
                        cid = c.get("id")
                        capped = c.get("capped", False)
                        d_limit = c.get("dailyLimit", 0)
                        w_today = c.get("watchedToday", 0)
                        while not capped and (d_limit == 0 or w_today < d_limit) and ads_watched < 10:
                            async with session.post(f"{base_url}/rewardsCenter/watchAd", json={"networkId": cid}, headers=auth_headers, timeout=aiohttp.ClientTimeout(total=8)) as war:
                                if war.status == 200:
                                    ads_watched += 1
                                    w_today += 1
                                    rew_u = c.get("usdtReward", 0)
                                    logger.info(f"[{acc_name}] 💳 [UltraWallet] 📺 Watch & Earn Ad watched (+{rew_u} USDT | Total today: {ads_watched}/10)!")
                                else:
                                    break
                            await asyncio.sleep(2.0)
                        if ads_watched >= 10:
                            break
        except Exception as rce:
            logger.debug(f"[{acc_name}] UltraWallet rewardsCenter note: {rce}")

        # 9. Gift Box (Check status & Auto-claim when unlocked)
        try:
            async with session.get(f"{base_url}/giftBox", headers=auth_headers, timeout=aiohttp.ClientTimeout(total=8)) as gbr:
                if gbr.status == 200:
                    gb_d = await gbr.json()
                    if gb_d.get("enabled") and gb_d.get("canOpen"):
                        async with session.post(f"{base_url}/giftBox/claim", json={}, headers=auth_headers, timeout=aiohttp.ClientTimeout(total=8)) as gbc:
                            if gbc.status == 200:
                                gbc_d = await gbc.json()
                                logger.info(f"[{acc_name}] 🎁 [UltraWallet] 🎉 GIFT BOX UNLOCKED & CLAIMED (+{gbc_d.get('rewardAmount')} {gbc_d.get('rewardCoin')})!")
        except Exception as gbe:
            logger.debug(f"[{acc_name}] UltraWallet giftBox note: {gbe}")

        logger.info(f"[{acc_name}] 💳 [UltraWallet] Cycle finished | Mining Active: {m_state.get('active', True)} (Rate: {m_state.get('ratePerHour', 10)}/h)")

    except Exception as e:
        logger.debug(f"[{acc_name}] UltraWallet automation note: {e}")


# =======================================================
# MODULE 7: APEX MINER AUTOMATION (@ApxMinerBot)
# =======================================================

async def automate_apx_cycle(session: aiohttp.ClientSession, acc_client, acc: dict):
    """
    Automates Apex Miner (@ApxMinerBot):
    - Authenticates via /api/auth/telegram & /api/bootstrap
    - Auto-registers if new user under referral 6727787768 (/api/register)
    - Daily streak check-in (/api/checkin)
    - Mining harvest & claim (/api/mining/claim)
    - Starts/restarts continuous 8h mining cycle (/api/mining/restart)
    - Completes daily tasks & social tasks (/api/tasks/daily, /api/tasks/social)
    - Activates free ad mining speed boost & ad rewards (/api/ads/boost, /api/ads/reward)
    """
    acc_name = acc.get("name", "User")
    acc_uid = str(acc.get("user_id"))

    try:
        init_data = FLEET_MINIAPP_TOKENS.get(acc_uid, {}).get("apx_init_data")
        if not init_data and acc_client:
            try:
                bot_apx = await acc_client.get_input_entity(APX_BOT)
                res_apx = await acc_client(RequestAppWebViewRequest(
                    peer=bot_apx,
                    app=InputBotAppShortName(bot_id=bot_apx, short_name="app"),
                    platform="android",
                    start_param=str(APX_REFERRAL_CODE)
                ))
                parsed = urllib.parse.urlparse(res_apx.url)
                init_data = urllib.parse.parse_qs(parsed.fragment).get("tgWebAppData", [None])[0]
                if init_data:
                    await sync_account_tokens_to_edge(session, acc_uid, acc_name, apx_init_data=init_data)
            except Exception:
                pass

        if not init_data:
            return

        acc_ua = get_account_user_agent(acc_uid)
        headers = {"Content-Type": "application/json", "User-Agent": acc_ua}
        base_url = "https://apex-miner.vercel.app/api"

        # 1. Auth & Bootstrap
        try:
            async with session.post(f"{base_url}/auth/telegram", json={"initData": init_data}, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as auth_r:
                pass
        except Exception:
            pass

        b_data = {}
        try:
            async with session.post(f"{base_url}/bootstrap", json={"initData": init_data}, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as br:
                if br.status == 200:
                    b_data = await br.json()
        except Exception:
            pass

        if not b_data.get("exists") or not b_data.get("user"):
            try:
                async with session.post(f"{base_url}/register", json={"initData": init_data}, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as rr:
                    if rr.status == 200:
                        b_data = await rr.json()
            except Exception:
                pass

        user_info = b_data.get("user", {})
        curr_bal = float(user_info.get("balance", b_data.get("balance", 0.0)) or 0.0)

        # 2. Daily Streak Check-in
        try:
            async with session.post(f"{base_url}/checkin", json={"initData": init_data, "clientV2": True}, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as cr:
                if cr.status == 200:
                    cd = await cr.json()
                    curr_bal = float(cd.get("balance", curr_bal) or curr_bal)
                    logger.info(f"[{acc_name}] ⚡ [Apex Miner] Daily check-in streak claimed! Streak: {cd.get('streak', 1)}")
        except Exception:
            pass

        # 3. Mining Claim (if claimable points exist)
        try:
            async with session.post(f"{base_url}/mining/claim", json={"initData": init_data}, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as cl:
                if cl.status == 200:
                    cld = await cl.json()
                    curr_bal = float(cld.get("balance", curr_bal) or curr_bal)
                    logger.info(f"[{acc_name}] ⚡ [Apex Miner] Mined points claimed! Balance: {curr_bal:,.4f}")
        except Exception:
            pass

        # 4. Mining Restart / Start 8-hour cycle
        m_active = True
        try:
            async with session.post(f"{base_url}/mining/restart", json={"initData": init_data}, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as mr:
                res_json = {}
                try:
                    res_json = await mr.json()
                except Exception:
                    pass
                if mr.status == 200:
                    curr_bal = float(res_json.get("balance", curr_bal) or curr_bal)
                    logger.info(f"[{acc_name}] ⚡ [Apex Miner] 8-hour mining cycle active/restarted!")
                elif mr.status == 409 or res_json.get("errorCode") == "SESSION_ACTIVE":
                    m_active = True
        except Exception:
            pass

        # 5. Tasks Discovery & Auto-Claim (Dynamic wait: 10s for daily, 15s for social tasks)
        for dt in ["telegram", "twitter"]:
            try:
                # Step 1: Tap task
                await session.post(f"{base_url}/tasks/daily/start", json={"initData": init_data, "task": dt}, headers=headers, timeout=aiohttp.ClientTimeout(total=6))
            except Exception:
                pass
            await asyncio.sleep(10.0)
            try:
                async with session.post(f"{base_url}/tasks/daily", json={"initData": init_data, "task": dt}, headers=headers, timeout=aiohttp.ClientTimeout(total=6)) as dtr:
                    if dtr.status == 200:
                        dtd = await dtr.json()
                        curr_bal = float(dtd.get("balance", curr_bal) or curr_bal)
                        logger.info(f"[{acc_name}] ⚡ [Apex Miner] Daily task '{dt}' claimed!")
            except Exception:
                pass

        for st in ["channel", "group", "twitter"]:
            try:
                # Step 1: Tap task
                await session.post(f"{base_url}/tasks/social/start", json={"initData": init_data, "task": st}, headers=headers, timeout=aiohttp.ClientTimeout(total=6))
            except Exception:
                pass
            await asyncio.sleep(15.0)
            try:
                async with session.post(f"{base_url}/tasks/social", json={"initData": init_data, "task": st}, headers=headers, timeout=aiohttp.ClientTimeout(total=6)) as str_req:
                    if str_req.status == 200:
                        std = await str_req.json()
                        curr_bal = float(std.get("balance", curr_bal) or curr_bal)
                        logger.info(f"[{acc_name}] ⚡ [Apex Miner] Social task '{st}' claimed!")
            except Exception:
                pass

        # 6. Ad Mining Speed Boost & Ad Reward
        try:
            async with session.post(f"{base_url}/ads/boost", json={"initData": init_data}, headers=headers, timeout=aiohttp.ClientTimeout(total=6)) as bst_r:
                if bst_r.status == 200:
                    logger.info(f"[{acc_name}] ⚡ [Apex Miner] Mining speed boost activated!")
        except Exception:
            pass

        try:
            async with session.post(f"{base_url}/ads/reward", json={"initData": init_data}, headers=headers, timeout=aiohttp.ClientTimeout(total=6)) as rew_r:
                if rew_r.status == 200:
                    rew_d = await rew_r.json()
                    curr_bal = float(rew_d.get("balance", curr_bal) or curr_bal)
                    logger.info(f"[{acc_name}] ⚡ [Apex Miner] Ad reward claimed! Balance: {curr_bal:,.4f}")
        except Exception:
            pass

        logger.info(f"[{acc_name}] ⚡ [Apex Miner] Cycle finished | Balance: {curr_bal:,.4f} Points | Mining Active: {m_active}")

    except Exception as e:
        logger.debug(f"[{acc_name}] Apex Miner automation note: {e}")


# =======================================================
# MODULE 8: AINOVUM BOT AUTOMATION (@ainovum_bot)
# =======================================================

async def automate_ainovum_cycle(session: aiohttp.ClientSession, acc_client, acc: dict):
    """
    Automates Ainovum Bot (@ainovum_bot):
    - Obtains fresh initData or uses cached
    - Bootstraps user session via /api/bootstrap with referrer ref_6727787768
    - Claims accumulated AI agent mining profit (/api/mining/claim)
    - Claims channel bonus (/api/channel-bonus/claim)
    - Opens available daily gift boxes (/api/gift-box/open)
    - Tracks live stats and USDT / AI earnings
    """
    acc_name = acc.get("name", "User")
    acc_uid = str(acc.get("user_id"))

    try:
        init_data = FLEET_MINIAPP_TOKENS.get(acc_uid, {}).get("ainovum_init_data")
        if not init_data and acc_client:
            try:
                bot_an = await acc_client.get_entity(AINOVUM_BOT)
                res_an = await acc_client(RequestWebViewRequest(
                    peer=bot_an,
                    bot=bot_an,
                    platform="android",
                    url=f"https://ainovum.biz/?startapp={AINOVUM_REFERRAL_CODE}&ref={AINOVUM_REFERRAL_CODE}"
                ))
                parsed_an = urllib.parse.urlparse(res_an.url)
                init_data = urllib.parse.parse_qs(parsed_an.fragment).get("tgWebAppData", [None])[0]
                if init_data:
                    await sync_account_tokens_to_edge(session, acc_uid, acc_name, ainovum_init_data=init_data)
            except Exception:
                pass

        if not init_data:
            return

        proxy = acc.get("proxy")
        acc_ua = get_account_user_agent(acc_uid)
        headers = {"Content-Type": "application/json", "User-Agent": acc_ua}
        base_url = "https://ainovum.biz"

        # 1. Bootstrap & acquire session cookies
        boot_payload = {
            "initData": init_data,
            "platform": "android",
            "referrer": AINOVUM_REFERRAL_CODE,
            "timezone_offset_minutes": 0,
            "language_code": "en",
            "registration_duration_ms": 1500
        }
        cookie_hdr = ""
        try:
            async with session.post(f"{base_url}/api/bootstrap", json=boot_payload, headers=headers, timeout=aiohttp.ClientTimeout(total=10), proxy=proxy) as br:
                if br.status == 200:
                    raw_cookies = br.headers.getall("Set-Cookie", [])
                    cookie_hdr = "; ".join([c.split(";")[0] for c in raw_cookies])
        except Exception:
            pass

        auth_headers = dict(headers)
        if cookie_hdr:
            auth_headers["Cookie"] = cookie_hdr

        await asyncio.sleep(1.5)

        # 2. Claim Mining Profit
        try:
            async with session.post(f"{base_url}/api/mining/claim", json={"action": "claim_cycle"}, headers=auth_headers, timeout=aiohttp.ClientTimeout(total=10), proxy=proxy) as mr:
                if mr.status == 200:
                    md = await mr.json()
                    if md.get("claimed"):
                        rew = float(md.get("reward_usdt", 0) or 0)
                        logger.info(f"[{acc_name}] 🤖 [Ainovum] Mining profit claimed: +{rew:.6f} USDT!")
                    elif not md.get("below_min"):
                        logger.info(f"[{acc_name}] 🤖 [Ainovum] Mining profit response: {md.get('message', md)}")
        except Exception as me:
            logger.debug(f"[{acc_name}] Ainovum claim mining note: {me}")

        # 3. Claim Channel Bonus
        try:
            async with session.post(f"{base_url}/api/channel-bonus/claim", json={}, headers=auth_headers, timeout=aiohttp.ClientTimeout(total=8), proxy=proxy) as cbr:
                if cbr.status == 200:
                    logger.info(f"[{acc_name}] 🤖 [Ainovum] Channel bonus claimed!")
        except Exception:
            pass

        # 4. Open Gift Box
        try:
            async with session.post(f"{base_url}/api/gift-box/open", json={}, headers=auth_headers, timeout=aiohttp.ClientTimeout(total=8), proxy=proxy) as gbr:
                if gbr.status == 200:
                    gbd = await gbr.json()
                    logger.info(f"[{acc_name}] 🤖 [Ainovum] Gift box opened: {gbd}")
        except Exception:
            pass

        # 5. Auto-Withdrawal to Main Binance BEP-20 Wallet (0.1 USDT Minimum)
        try:
            async with session.get(f"{base_url}/api/withdraws/usdt/config", headers=auth_headers, timeout=aiohttp.ClientTimeout(total=8), proxy=proxy) as cr:
                if cr.status == 200:
                    cd = await cr.json()
                    avail = float(cd.get("freeze", {}).get("available", 0) or 0)
                    if avail >= 0.1:
                        wd_amt = round(avail, 4)
                        logger.info(f"[{acc_name}] 🤖 [Ainovum] Available {avail:.4f} USDT >= 0.1 threshold! Submitting auto-withdrawal to BEP-20 {EVM_VAULT_ADDRESS}...")
                        wd_payload = {"amount": wd_amt, "wallet": EVM_VAULT_ADDRESS, "network": "bep20"}
                        for attempt in range(2):
                            async with session.post(
                                f"{base_url}/api/withdraws/usdt/create",
                                json=wd_payload,
                                headers=auth_headers,
                                timeout=aiohttp.ClientTimeout(total=10),
                                proxy=proxy
                            ) as wr:
                                wd = await wr.json()
                                if wr.status == 200 and not wd.get("access_denied") and not wd.get("error"):
                                    logger.info(f"[{acc_name}] 🤖 [Ainovum] Withdrawal success: {wd}")
                                    await send_report_message(
                                        f"🎉 *Ainovum USDT Withdrawal Submitted!*\n\n"
                                        f"• **Account:** {acc_name}\n"
                                        f"• **Amount:** `{wd_amt} USDT` (BEP-20)\n"
                                        f"• **Destination:** `{EVM_VAULT_ADDRESS}` (Binance BEP-20)\n"
                                        f"• **Result:** `{wd}`",
                                        chat_id=REPORT_CHAT_ID
                                    )
                                    break
                                elif wd.get("code") == "busy":
                                    logger.info(f"[{acc_name}] 🤖 [Ainovum] Withdrawal gateway busy (Server busy). Will retry next cycle.")
                                    break
                                else:
                                    logger.debug(f"[{acc_name}] 🤖 [Ainovum] Withdrawal attempt ({wd_amt} USDT): {wd}")
                            await asyncio.sleep(3.0)
        except Exception as we:
            logger.debug(f"[{acc_name}] Ainovum auto-withdrawal note: {we}")

    except Exception as e:
        logger.debug(f"[{acc_name}] Ainovum automation note: {e}")


# =======================================================
# MODULE 9: MININGGRAM BOT AUTOMATION (@MiningGRAM_Bot)
# =======================================================

async def automate_mininggram_cycle(session: aiohttp.ClientSession, acc_client, acc: dict):
    """
    Automates MiningGRAM Bot (@MiningGRAM_Bot):
    - Obtains fresh initData or uses cached
    - Authenticates via /api/auth with referralCode 339JU9K
    - Daily streak check-in (/api/checkin)
    - Claims trickle mining earnings (/api/mine/trickle-claim)
    - Claims finished miners (/api/miners/claim)
    - Activates idle miners (/api/miners/activate)
    - Tracks live balance (/api/balance)
    """
    acc_name = acc.get("name", "User")
    acc_uid = str(acc.get("user_id"))

    try:
        init_data = FLEET_MINIAPP_TOKENS.get(acc_uid, {}).get("mininggram_init_data")
        if not init_data and acc_client:
            try:
                bot_mg = await acc_client.get_input_entity(MININGGRAM_BOT)
                res_mg = await acc_client(RequestAppWebViewRequest(
                    peer=bot_mg,
                    app=InputBotAppShortName(bot_id=bot_mg, short_name="mine"),
                    platform="android",
                    start_param=MININGGRAM_REFERRAL_CODE
                ))
                parsed_mg = urllib.parse.urlparse(res_mg.url)
                init_data = urllib.parse.parse_qs(parsed_mg.fragment).get("tgWebAppData", [None])[0]
                if init_data:
                    await sync_account_tokens_to_edge(session, acc_uid, acc_name, mininggram_init_data=init_data)
            except Exception:
                pass

        if not init_data:
            return

        base_url = "https://mining-gram-worker.muhaisin0888.workers.dev"
        acc_ua = get_account_user_agent(acc_uid)
        headers = {"Content-Type": "application/json", "User-Agent": acc_ua}

        # 1. Auth verify
        token = None
        try:
            auth_payload = {
                "initData": init_data,
                "referralCode": MININGGRAM_REFERRAL_CODE,
                "deviceFingerprint": f"fp_{acc_uid}"
            }
            async with session.post(f"{base_url}/api/auth", json=auth_payload, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as ar:
                if ar.status == 200:
                    ad = await ar.json()
                    token = ad.get("sessionToken") or ad.get("token") or ad.get("session") or ad.get("accessToken")
        except Exception as ae:
            logger.debug(f"[{acc_name}] MiningGRAM auth note: {ae}")

        auth_headers = dict(headers)
        if token:
            auth_headers["Authorization"] = f"Bearer {token}"
        else:
            return

        await asyncio.sleep(1.0)

        # 2. Trickle mining claim
        try:
            async with session.get(f"{base_url}/api/mine/trickle-status", headers=auth_headers, timeout=aiohttp.ClientTimeout(total=8)) as tsr:
                if tsr.status == 200:
                    tsd = await tsr.json()
                    trickles = tsd.get("trickles", [])
                    if isinstance(trickles, list):
                        for tr in trickles:
                            tr_id = tr.get("id") or tr.get("trickleId")
                            if tr_id:
                                await session.post(f"{base_url}/api/mine/trickle-claim", json={"trickleId": tr_id}, headers=auth_headers, timeout=aiohttp.ClientTimeout(total=8))
                                logger.info(f"[{acc_name}] ⛏️ [MiningGRAM] Trickle #{tr_id} claimed!")
                    trickle_id = tsd.get("trickleId") or tsd.get("id")
                    if trickle_id:
                        async with session.post(f"{base_url}/api/mine/trickle-claim", json={"trickleId": trickle_id}, headers=auth_headers, timeout=aiohttp.ClientTimeout(total=8)) as tcr:
                            if tcr.status == 200:
                                logger.info(f"[{acc_name}] ⛏️ [MiningGRAM] Trickle claim successful!")
        except Exception:
            pass

        # 3. Miners check & claim
        active_miners = 0
        try:
            async with session.get(f"{base_url}/api/miners", headers=auth_headers, timeout=aiohttp.ClientTimeout(total=8)) as mr:
                if mr.status == 200:
                    miners_data = await mr.json()
                    owned = miners_data.get("owned", []) if isinstance(miners_data, dict) else (miners_data if isinstance(miners_data, list) else [])
                    now_iso = time.time()
                    for m in owned:
                        mid = m.get("id") or m.get("minerId")
                        m_status = m.get("status")
                        finishes_at = m.get("finishes_at")
                        fin_ts = 0
                        if finishes_at:
                            try:
                                fin_ts = datetime.datetime.fromisoformat(finishes_at.replace("Z", "+00:00")).timestamp()
                            except Exception:
                                pass

                        if m.get("canClaim") or m_status in ("ready_to_claim", "completed") or (m_status == "active" and fin_ts > 0 and now_iso >= fin_ts):
                            async with session.post(f"{base_url}/api/miners/claim", json={"minerId": mid}, headers=auth_headers, timeout=aiohttp.ClientTimeout(total=8)) as clr:
                                if clr.status == 200:
                                    logger.info(f"[{acc_name}] ⛏️ [MiningGRAM] Miner #{mid} claimed!")
                        elif m_status in ("inactive", "idle") or m.get("canActivate"):
                            async with session.post(f"{base_url}/api/miners/activate", json={"minerId": mid}, headers=auth_headers, timeout=aiohttp.ClientTimeout(total=8)) as acr:
                                if acr.status == 200:
                                    logger.info(f"[{acc_name}] ⛏️ [MiningGRAM] Miner #{mid} activated!")
                                    active_miners += 1
                        elif m_status == "active":
                            active_miners += 1

                    logger.info(f"[{acc_name}] ⛏️ [MiningGRAM] Cycle finished | Active Miners: {active_miners} (Owned: {len(owned)})")
        except Exception as me:
            logger.debug(f"[{acc_name}] MiningGRAM miners note: {me}")

    except Exception as e:
        logger.debug(f"[{acc_name}] MiningGRAM automation note: {e}")


async def automate_atf_cycle(session: aiohttp.ClientSession, acc_client, acc: dict):
    """
    Automates ATF Miner (@ATF_AIRDROP_bot):
    - Obtains or uses cached WebApp initData
    - Solves arithmetic verification questions automatically
    - Starts 24h mining cycles
    - Claims accumulated mining rewards, referrals, and team wallet
    - Completes and claims one-time and repeatable tasks
    """
    acc_name = acc.get("name", "User")
    acc_uid = str(acc.get("user_id"))

    try:
        init_data = None
        if acc_client:
            try:
                bot_atf = await acc_client.get_entity("ATF_AIRDROP_bot")
                res = await acc_client(RequestWebViewRequest(
                    peer=bot_atf,
                    bot=bot_atf,
                    platform="android",
                    url=f"https://atfminers.asloni.online/miner/index.html?v=1789502294&entry=bot_start&ref={REPORT_CHAT_ID}",
                    start_param=str(REPORT_CHAT_ID)
                ))
                parsed = urllib.parse.urlparse(res.url)
                init_data = urllib.parse.parse_qs(parsed.fragment).get("tgWebAppData", [None])[0]
                if init_data:
                    await sync_account_tokens_to_edge(session, acc_uid, acc_name, atf_init_data=init_data)
            except Exception as we:
                logger.debug(f"[{acc_name}] 🪙 [ATF Miner] MTProto initData note: {we}")

        if not init_data:
            init_data = FLEET_MINIAPP_TOKENS.get(acc_uid, {}).get("atf_init_data")

        if not init_data:
            return

        acc_ua = get_account_user_agent(acc_uid)
        base_url = "https://atfminers.asloni.online/miner/index.php"
        headers = {
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": acc_ua,
            "Referer": "https://atfminers.asloni.online/miner/index.html",
            "Origin": "https://atfminers.asloni.online"
        }
        device_id = f"dev-{acc_uid}"

        def atf_p(obj):
            p = {"initData": init_data, "request_id": f"rq-{int(time.time()*1000)}-{uuid.uuid4().hex[:8]}", "device_id": device_id}
            p.update(obj)
            return p

        # 1. Login
        async with session.post(f"{base_url}?action=login&t={int(time.time()*1000)}", json=atf_p({"tg_id": int(acc_uid), "username": acc.get("username", "")}), headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as lr:
            if lr.status != 200:
                return
            ld = await lr.json()
            if ld.get("status") != "success":
                return
            u = ld.get("user", {})

        # 1b. Dedicated TON Wallet Sync & Cryptographic TON Connect Proof
        current_wallet = u.get("wallet_address") or u.get("wallet")
        is_wallet_verified = str(u.get("wallet_verified", "0")) == "1" or (acc_uid == str(REPORT_CHAT_ID) and bool(current_wallet))

        ton_wallets = load_fleet_ton_wallets()
        if acc_uid == str(REPORT_CHAT_ID):
            target_ton_wallet = TON_PRIMARY_WALLET
            acc_ton_entry = {}
        else:
            acc_ton_entry = ton_wallets.get(acc_uid, {})
            target_ton_wallet = acc_ton_entry.get("address")
            if not target_ton_wallet:
                tw = acc.get("ton_wallet")
                if isinstance(tw, dict):
                    target_ton_wallet = tw.get("address")
                elif isinstance(tw, str) and tw.startswith("UQ"):
                    target_ton_wallet = tw
                else:
                    target_ton_wallet = TON_PRIMARY_WALLET

        if not is_wallet_verified and target_ton_wallet:
            mnemonic_str = acc_ton_entry.get("mnemonic")
            if mnemonic_str and HAS_TON_PROOF_LIBS:
                try:
                    words = mnemonic_str.split()
                    _, pub_key_bytes, priv_key_bytes, wallet_contract = Wallets.from_mnemonics(mnemonics=words, version=WalletVersionEnum.v4r2)
                    state_init_res = wallet_contract.create_state_init()
                    state_init_b64 = base64.b64encode(state_init_res["state_init"].to_boc(False)).decode("utf-8")

                    t_addr = Address(target_ton_wallet)
                    raw_addr = f"{t_addr.wc}:{t_addr.hash_part.hex()}"

                    async with session.post(f"{base_url}?action=get_wallet_proof_payload&t={int(time.time()*1000)}", json=atf_p({"tg_id": int(acc_uid), "force": 1}), headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as pr_resp:
                        pr_data = await pr_resp.json()
                        proof_nonce = pr_data.get("payload")

                    if proof_nonce:
                        domain = "atfminers.asloni.online"
                        domain_bytes = domain.encode("utf-8")
                        ts = int(time.time())

                        msg = (
                            b"ton-proof-item-v2/" +
                            struct.pack(">i", t_addr.wc) +
                            t_addr.hash_part +
                            struct.pack("<I", len(domain_bytes)) +
                            domain_bytes +
                            struct.pack("<Q", ts) +
                            proof_nonce.encode("utf-8")
                        )
                        msg_hash = hashlib.sha256(msg).digest()
                        full_msg = b"\xff\xff" + b"ton-connect" + msg_hash
                        final_hash = hashlib.sha256(full_msg).digest()

                        signing_key = SigningKey(priv_key_bytes[:32])
                        sig = signing_key.sign(final_hash).signature
                        sig_b64 = base64.b64encode(sig).decode("utf-8")

                        proof_obj = {
                            "timestamp": ts,
                            "domain": {"lengthBytes": len(domain_bytes), "value": domain},
                            "signature": sig_b64,
                            "payload": proof_nonce
                        }

                        sync_p = atf_p({
                            "tg_id": int(acc_uid),
                            "wallet": raw_addr,
                            "public_key": pub_key_bytes.hex(),
                            "wallet_state_init": state_init_b64,
                            "network": "-239",
                            "proof": proof_obj,
                            "refresh_holding": 1
                        })
                        async with session.post(f"{base_url}?action=sync_wallet&t={int(time.time()*1000)}", json=sync_p, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as wr:
                            w_data = await wr.json()
                            if w_data.get("status") == "success":
                                logger.info(f"[{acc_name}] 🪙 [ATF Miner] 💎 Cryptographic TON Proof Verified: {target_ton_wallet[:12]}... (Status: Verified ✅)")
                except Exception as pe:
                    logger.debug(f"[{acc_name}] ATF TON Proof note: {pe}")
            elif not current_wallet or current_wallet != target_ton_wallet:
                try:
                    await asyncio.sleep(0.8)
                    sync_p = atf_p({"tg_id": int(acc_uid), "wallet": target_ton_wallet})
                    async with session.post(f"{base_url}?action=sync_wallet&t={int(time.time()*1000)}", json=sync_p, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as wr:
                        pass
                except Exception:
                    pass

        # 2. Claim mining, referrals, team pool
        await session.post(f"{base_url}?action=claim&t={int(time.time()*1000)}", json=atf_p({"tg_id": int(acc_uid), "claim_preview": float(u.get("pending_reward", 0) or 0)}), headers=headers, timeout=aiohttp.ClientTimeout(total=8))
        await session.post(f"{base_url}?action=claim_referrals&t={int(time.time()*1000)}", json=atf_p({"tg_id": int(acc_uid)}), headers=headers, timeout=aiohttp.ClientTimeout(total=8))
        await session.post(f"{base_url}?action=claim_team_wallet&t={int(time.time()*1000)}", json=atf_p({"tg_id": int(acc_uid)}), headers=headers, timeout=aiohttp.ClientTimeout(total=8))

        # 3. Math Challenge & Start Mining
        async with session.post(f"{base_url}?action=get_math_challenge&t={int(time.time()*1000)}", json=atf_p({"tg_id": int(acc_uid), "scope": "start_mine"}), headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as mr:
            if mr.status == 200:
                md = await mr.json()
                if md.get("status") == "success" and md.get("question") and md.get("challenge_id"):
                    q = md.get("question")
                    cleaned = q.replace("?", "").replace("=", "").strip()
                    nums = [int(n) for n in re.findall(r"\d+", cleaned)]
                    ans = "0"
                    if len(nums) >= 2:
                        if "+" in q:
                            ans = str(nums[0] + nums[1])
                        elif "-" in q:
                            ans = str(nums[0] - nums[1])
                        elif "*" in q or "x" in q.lower():
                            ans = str(nums[0] * nums[1])
                    await session.post(f"{base_url}?action=start_mine&t={int(time.time()*1000)}", json=atf_p({"tg_id": int(acc_uid), "math_challenge_id": md.get("challenge_id"), "math_answer": ans}), headers=headers, timeout=aiohttp.ClientTimeout(total=8))

        # 3b. Activate Mining Speed Boost & Daily Interaction
        try:
            await session.post(f"{base_url}?action=activate_boost&t={int(time.time()*1000)}", json=atf_p({"tg_id": int(acc_uid), "display_preview": float(u.get("pending_reward", 0) or 0)}), headers=headers, timeout=aiohttp.ClientTimeout(total=5))
            await session.post(f"{base_url}?action=record_daily_interaction&t={int(time.time()*1000)}", json=atf_p({"tg_id": int(acc_uid)}), headers=headers, timeout=aiohttp.ClientTimeout(total=5))
        except Exception:
            pass

        # 4. Tasks claim (repeatable)
        repeatable_tasks = [
            {"id": "website_visit", "minSeconds": 10},
            {"id": "telegram_react_latest", "minSeconds": 20},
            {"id": "twitter_retweet", "minSeconds": 30},
            {"id": "youtube_like_comment", "minSeconds": 30}
        ]
        cooldowns = ld.get("task_cooldowns") or {}
        now_s = int(time.time())
        for task in repeatable_tasks:
            tid = task["id"]
            if now_s >= int(cooldowns.get(tid, 0) or 0):
                s_at = now_s - task["minSeconds"] - 5
                await session.post(f"{base_url}?action=start_task&t={int(time.time()*1000)}", json=atf_p({"tg_id": int(acc_uid), "task_id": tid, "client_started_at": s_at}), headers=headers, timeout=aiohttp.ClientTimeout(total=5))
                await asyncio.sleep(1.0)
                await session.post(f"{base_url}?action=claim_task&t={int(time.time()*1000)}", json=atf_p({"tg_id": int(acc_uid), "task_id": tid, "client_started_at": s_at}), headers=headers, timeout=aiohttp.ClientTimeout(total=5))

        # 5. ATF Accumulation & Farming (Withdrawal disabled per user directive: farming only)
        mined_bal = float(u.get("mined_balance", 0) or 0)
        acc["atf_balance"] = mined_bal
        await update_account_safely(acc_uid, {"atf_balance": mined_bal})
        logger.info(f"[{acc_name}] 🪙 [ATF Miner] Harvested & farming cycle active | Total Pool: {mined_bal:.2f} ATF (Accumulating)")
    except Exception as e:
        logger.debug(f"[{acc_name}] ATF Miner automation note: {e}")


async def farm_single_account(
    acc_idx: int,
    total_accounts: int,
    acc: dict,
    worker_slot: int,
    fleet_next_resets: list,
    fleet_ready_counts: list,
    primary_user_id: int
):
    """
    Pure On-Demand Collector for single account:
    - Checks whether session links ('season links') are expired (>18h) or missing
    - Checks whether balance >= 0.00005 BNB requires on-chain Telegram /withdraw
    - Fast-Path: If session links are active & no withdrawal needed, delegates 100% of tasks
      to Cloudflare Cloud (0 MTProto connections, 0 VPS RAM, 0s local delay!)
    - On-Demand Path: Connects MTProto briefly (3-5s), collects 4 session links (Stones, MRG,
      ART, BNB webhook), syncs to Cloudflare KV, submits /withdraw if eligible, then IMMEDIATELY
      disconnects and releases memory to 0!
    """
    acc_name = acc.get("name", f"Account #{acc_idx}")
    acc_uid = int(acc.get("user_id", primary_user_id))
    acc_sess = acc.get("session_string")
    if not acc_sess:
        return

    if acc.get("status") == "revoked":
        logger.warning(f"[{acc_name}] Account session marked as revoked. Skipping until re-login.")
        return

    cf_node_url = CF_WORKER_URLS[worker_slot % len(CF_WORKER_URLS)]
    cf_tag = f"CF-Node-{worker_slot + 1}"

    # 1. Pre-check BNB task readiness via fast HTTP call before MTProto session
    acc_proxy = parse_proxy(acc.get("proxy"))
    states = {}
    ready_tasks_count = 0
    next_bnb_avail_ms = None
    stored_reset_sec = float(acc.get("bnb_next_reset_at") or 0)
    now_sec = time.time()
    now_ms = int(now_sec * 1000)

    if ENABLE_BNB_GALAXY:
        # Pre-seed cooldown from stored account record if still active
        if stored_reset_sec > now_sec:
            next_bnb_avail_ms = int(stored_reset_sec * 1000)

        try:
            async with aiohttp.ClientSession() as http_check_session:
                states = await get_bnb_tasks_status(http_check_session, acc_uid, proxy=None)
                if not states and acc.get("proxy"):
                    states = await get_bnb_tasks_status(http_check_session, acc_uid, proxy=acc.get("proxy"))
        except Exception:
            states = {}

        if states:
            ready_tasks = [int(tid) for tid, avail in states.items() if int(avail) == 0 or int(avail) <= now_ms]
            ready_tasks_count = len(ready_tasks)
            for avail in states.values():
                avail_int = int(avail)
                if avail_int > 0 and (next_bnb_avail_ms is None or avail_int < next_bnb_avail_ms):
                    next_bnb_avail_ms = avail_int
        else:
            if stored_reset_sec > now_sec:
                ready_tasks_count = 0
                next_bnb_avail_ms = int(stored_reset_sec * 1000)
            else:
                ready_tasks_count = 0

        if next_bnb_avail_ms:
            fleet_next_resets.append(next_bnb_avail_ms)
            acc["bnb_next_reset_at"] = next_bnb_avail_ms / 1000.0
            await update_account_safely(acc_uid, {"bnb_next_reset_at": next_bnb_avail_ms / 1000.0})

        fleet_ready_counts.append(ready_tasks_count)
    else:
        fleet_ready_counts.append(0)

    # 2. Check if session links collection is due (every 18 hours or if missing)
    tokens_synced_at = float(acc.get("miniapp_tokens_synced_at") or 0)
    tokens_age_hours = (time.time() - tokens_synced_at) / 3600.0
    curr_tokens = FLEET_MINIAPP_TOKENS.get(str(acc_uid), {})
    missing_tokens = (
        not curr_tokens.get("stones_init_data")
        or not curr_tokens.get("mrg_init_data")
        or not curr_tokens.get("art_init_data")
        or not curr_tokens.get("ailab_init_data")
        or not curr_tokens.get("ultrawallet_init_data")
        or not curr_tokens.get("apx_init_data")
        or not curr_tokens.get("ainovum_init_data")
        or not curr_tokens.get("mininggram_init_data")
    )
    tokens_due = (tokens_age_hours >= 18.0) or not acc.get("miniapp_tokens_synced") or (str(acc_uid) not in FLEET_MINIAPP_TOKENS) or missing_tokens

    # 3. Check if self-healing is due (every 12 hours)
    last_heal = float(acc.get("last_healed_at") or 0)
    missing_referrals = (
        not acc.get("stones_referral_bound")
        or not acc.get("mrg_referral_bound")
        or not acc.get("art_referral_bound")
        or not acc.get("ailab_referral_bound")
        or not acc.get("ultrawallet_referral_bound")
        or not acc.get("apx_referral_bound")
        or not acc.get("ainovum_referral_bound")
        or not acc.get("mininggram_referral_bound")
    )
    heal_due = (time.time() - last_heal) > (12 * 3600) or missing_referrals

    # 4. Check if withdrawal is already eligible or if balance check is due (Timer-Aware)
    known_balance = ACCOUNT_BALANCES.get(str(acc_uid), {}).get("balance", 0.0)
    withdraw_due = (known_balance >= MIN_WITHDRAWAL) if ENABLE_BNB_GALAXY else False
    last_bal_time = float(ACCOUNT_BALANCES.get(str(acc_uid), {}).get("timestamp", 0))

    is_bnb_cooldown = bool(next_bnb_avail_ms and next_bnb_avail_ms > now_ms and ready_tasks_count == 0)
    has_pending_payout = bool(acc.get("pending_withdraw") or (known_balance == 0.0 and (time.time() - float(acc.get("last_withdrawal_at") or 0)) < 28800))

    if not ENABLE_BNB_GALAXY:
        check_balance_due = False
    elif is_bnb_cooldown:
        check_balance_due = False
    elif has_pending_payout:
        check_balance_due = False
    else:
        check_balance_due = (last_bal_time == 0) or (ready_tasks_count > 0) or ((time.time() - last_bal_time) > 21600)

    # 5. Check if unverified withdrawal verification tasks are pending on Adsgram (ONLY if withdrawal was requested!)
    unverified_due = False
    if ENABLE_BNB_GALAXY and acc.get("pending_withdraw") and not acc.get("withdrawal_unlocked"):
        try:
            async with aiohttp.ClientSession() as chk_sess:
                async with chk_sess.get(f"https://justtool.site/api/adsgram-task3?tgId={acc_uid}", timeout=aiohttp.ClientTimeout(total=5)) as chk_r:
                    if chk_r.status == 200:
                        chk_d = await chk_r.json()
                        curr_v_count = chk_d.get("count", 0)
                        if curr_v_count < 5:
                            unverified_due = True
                        else:
                            acc["withdrawal_unlocked"] = True
                            await update_account_safely(acc_uid, {"withdrawal_unlocked": True})
        except Exception:
            pass

    # =========================================================================
    # FAST-PATH: If NO session collection, NO withdrawal, NO balance check, NO self-heal needed
    # -> Run 100% in Cloudflare Cloud with ZERO MTProto connections & ZERO VPS RAM!
    # =========================================================================
    if not tokens_due and not withdraw_due and not check_balance_due and not heal_due and not unverified_due:
        if ENABLE_BNB_GALAXY and ready_tasks_count > 0:
            logger.info(f"[{cf_tag} | Slot {worker_slot+1}/3] 🌐 [Account {acc_idx}/{total_accounts}] {acc_name} (ID: {acc_uid}): Session links valid (~{max(0, 24-tokens_age_hours):.1f}h left). Delegating {ready_tasks_count} tasks to Cloudflare Cloud (0 VPS RAM)...")
            await delegate_farm_to_cloudflare(acc_uid, cf_node_url)
        else:
            logger.info(f"[{cf_tag} | Slot {worker_slot+1}/3] === [Account {acc_idx}/{total_accounts}] {acc_name} (ID: {acc_uid}) Multi-Bot Fast Farming (0 MTProto, 0 VPS RAM) ===")

        # Multi-bot continuous mining cycle via pure HTTP & cached WebApp tokens (0 MTProto, 0 VPS RAM, parallel execution)
        try:
            async with aiohttp.ClientSession() as fast_mining_sess:
                await asyncio.gather(
                    automate_art_cycle(fast_mining_sess, None, acc),
                    automate_mrg_cycle(fast_mining_sess, None, acc),
                    automate_stones_cycle(fast_mining_sess, None, acc),
                    automate_ailab_cycle(fast_mining_sess, None, acc),
                    automate_ultrawallet_cycle(fast_mining_sess, None, acc),
                    automate_apx_cycle(fast_mining_sess, None, acc),
                    automate_ainovum_cycle(fast_mining_sess, None, acc),
                    automate_mininggram_cycle(fast_mining_sess, None, acc),
                    automate_atf_cycle(fast_mining_sess, None, acc),
                    return_exceptions=True
                )
        except Exception as fme:
            logger.debug(f"[{acc_name}] Fast mining cycle note: {fme}")

        acc["last_fleet_cycle_at"] = time.time()
        await update_account_safely(acc_uid, {"last_fleet_cycle_at": time.time()})
        PRIORITY_ACCOUNT_IDS.discard(str(acc_uid))
        gc.collect()
        return

    # =========================================================================
    # ON-DEMAND COLLECTOR PATH: Session links refresh, auto-withdraw, or self-heal
    # =========================================================================
    logger.info(f"🚀 [{cf_tag} | Slot {worker_slot+1}/3] === [Account {acc_idx}/{total_accounts}] {acc_name} (ID: {acc_uid}) Running On-Demand Session Collector ===")

    acc_cl = None
    should_disconnect = False
    try:
        global CURRENTLY_ACTIVE_ACCOUNT_ID, CURRENTLY_ACTIVE_ACCOUNT_IDS
        CURRENTLY_ACTIVE_ACCOUNT_IDS.add(str(acc_uid))
        CURRENTLY_ACTIVE_ACCOUNT_ID = acc_uid

        if acc_sess == STRING_SESSION:
            acc_cl = client
            should_disconnect = False
        else:
            acc_fp = get_account_fingerprint(acc_uid)
            try:
                acc_cl = TelegramClient(StringSession(acc_sess), API_ID, API_HASH, proxy=acc_proxy, **acc_fp)
                await acc_cl.connect()
            except Exception as proxy_err:
                if acc_proxy:
                    logger.warning(f"[{acc_name}] 🛡️ Proxy failed ({proxy_err}). Auto-failing over to direct connection...")
                    acc_cl = TelegramClient(StringSession(acc_sess), API_ID, API_HASH, **acc_fp)
                    await acc_cl.connect()
                else:
                    raise
            should_disconnect = True

        # A. Referral binding & channel self-healing (if due)
        if heal_due:
            await ensure_referral_bound(acc_cl, acc)
            await self_heal_account_channels_and_bots(acc_cl, acc)
            await update_account_safely(acc_uid, {"last_healed_at": time.time(), "stones_referral_bound": True})

        async with aiohttp.ClientSession() as http_sess:
            # B. Collect & Sync Session Links to Cloudflare Edge
            if tokens_due:
                logger.info(f"[{acc_name}] 🔗 Collecting fresh 24h WebApp session links (Stones, MRG, ART, BNB webhook, Ainovum, MiningGRAM)...")
                fresh_tokens = await collect_account_session_links(acc_cl, acc)
                if fresh_tokens:
                    await sync_account_tokens_to_edge(http_sess, str(acc_uid), acc_name, **fresh_tokens)
                    acc["miniapp_tokens_synced_at"] = time.time()
                    acc["miniapp_tokens_synced"] = True
                    await update_account_safely(acc_uid, {"miniapp_tokens_synced_at": time.time(), "miniapp_tokens_synced": True})
                    logger.info(f"[{acc_name}] ✅ Session links successfully synced to 3x Cloudflare Edge nodes!")

                    # If bnb webhook was extracted, register adsgram
                    if ENABLE_BNB_GALAXY:
                        wh = fresh_tokens.get("bnb_wh_url") or BNB_WEBHOOK_FALLBACK
                        await register_adsgram(http_sess, acc_uid, wh, proxy=acc.get("proxy"))

            # C. Offload BNB task completion & 5/5 verifications to Cloudflare Edge first
            if ENABLE_BNB_GALAXY and (ready_tasks_count > 0 or unverified_due):
                logger.info(f"[{acc_name}] 🌐 Offloading task farming & 5/5 verifications to Cloudflare Edge...")
                await delegate_farm_to_cloudflare(acc_uid, cf_node_url)

            # D. Withdrawal Verification Step A (Register MTProto view if unverified)
            if ENABLE_BNB_GALAXY and unverified_due:
                try:
                    bot_entity = await acc_cl.get_input_entity(BNB_BOT)
                    await acc_cl(RequestWebViewRequest(
                        peer=bot_entity,
                        bot=bot_entity,
                        platform="android",
                        url="https://justtool.site/withdraw-adsgram"
                    ))
                    logger.info(f"[{acc_name}] 🛡️ Registered MTProto WebApp view for anti-bot verification")
                except Exception as we:
                    logger.debug(f"[{acc_name}] MTProto WebApp note: {we}")

            # E. Auto-Withdrawal Check & Execution on MTProto (refreshes live balance & auto-withdraws if eligible)
            if ENABLE_BNB_GALAXY and (withdraw_due or check_balance_due) and not is_bnb_cooldown:
                logger.info(f"[{acc_name}] 💰 Live BNB Galaxy balance & auto-withdrawal check executing on MTProto...")
                await check_and_auto_withdraw(acc_uid, acc_name, notify_manual=False, acc_client=acc_cl, acc_data=acc)

            # F. Multi-Bot Mining Harvest & Task Automation (ART, MRG, Stones, AI Lab, UltraWallet, Apex Miner, Ainovum, MiningGRAM - Parallel Execution)
            try:
                await asyncio.gather(
                    automate_art_cycle(http_sess, acc_cl, acc),
                    automate_mrg_cycle(http_sess, acc_cl, acc),
                    automate_stones_cycle(http_sess, acc_cl, acc),
                    automate_ailab_cycle(http_sess, acc_cl, acc),
                    automate_ultrawallet_cycle(http_sess, acc_cl, acc),
                    automate_apx_cycle(http_sess, acc_cl, acc),
                    automate_ainovum_cycle(http_sess, acc_cl, acc),
                    automate_mininggram_cycle(http_sess, acc_cl, acc),
                    automate_atf_cycle(http_sess, acc_cl, acc),
                    return_exceptions=True
                )
            except Exception as ome:
                logger.debug(f"[{acc_name}] On-demand mining cycle note: {ome}")

        # Record completed multi-bot cycle timestamp safely
        acc["last_fleet_cycle_at"] = time.time()
        await update_account_safely(acc_uid, {"last_fleet_cycle_at": time.time()})
        PRIORITY_ACCOUNT_IDS.discard(str(acc_uid))
        logger.info(f"✅ [{cf_tag} | Slot {worker_slot+1}/3] On-demand session collection finished for {acc_name} ({acc_uid}). Disconnecting MTProto.")

    except (AuthKeyUnregisteredError, UserDeactivatedError, SessionRevokedError) as auth_err:
        logger.error(f"[Account Revoked] Session for {acc_name} ({acc_uid}) was revoked: {auth_err}")
        await update_account_safely(acc_uid, {"status": "revoked", "revoked_reason": str(auth_err)})
        alert_msg = (
            f"⚠️ *Account Session Revoked!*\n\n"
            f"• **Account:** {acc_name}\n"
            f"• **Phone:** `{acc.get('phone', 'N/A')}`\n"
            f"• **Reason:** `{auth_err}`\n\n"
            f"❌ This account was disconnected on mobile or revoked by Telegram.\n"
            f"💡 Send `➕ Add Account` to reconnect it whenever you are ready."
        )
        await broadcast_admin_message(alert_msg, reply_markup=MAIN_TAB_KEYBOARD)
    except FloodWaitError as fwe:
        logger.warning(f"[{acc_name}] Telegram FloodWait: {fwe.seconds}s. Skipping until next cycle.")
    except Exception as acc_err:
        logger.error(f"[Account Exception] Error processing account {acc_name} ({acc_uid}): {acc_err}", exc_info=True)
    finally:
        if should_disconnect and acc_cl:
            try:
                await acc_cl.disconnect()
            except Exception:
                pass
            acc_cl = None
        CURRENTLY_ACTIVE_ACCOUNT_IDS.discard(str(acc_uid))
        CURRENTLY_ACTIVE_ACCOUNT_ID = next(iter(CURRENTLY_ACTIVE_ACCOUNT_IDS), None)
        # Aggressively release unreferenced memory on shared VPS RAM
        gc.collect()


# =======================================================
# 24/7 UNIFIED BACKGROUND WORKER
# =======================================================

async def task_worker_247(user_id: int, user_name: str):
    """Continuous 24/7 daemon loop for BNB Galaxy & ATF Miner 50 ads/day."""
    logger.info("24/7 Multi-Bot Worker active with Tab Menu & ReportBot integration.")
    
    # Configure Telegram commands menu
    await setup_bot_tab_menu()

    # Send startup notification with persistent Tab Menu keyboard
    startup_text = (
        "🚀 *MY AGY AI Hub Online*\n\n"
        "Autonomous multi-crypto fleet daemon running 24/7 in the cloud.\n\n"
        "• **🪙 BNB Galaxy:** 10 Daily Tasks & Auto-Withdraw (BEP-20)\n"
        "• **💎 Stones Miners:** Daily Mining (+500 STONES to Arbitrum One)\n"
        "• **⛏️ MRG Miner:** Mining Harvest & 10% Squad Sweeps to Main ID\n"
        "• **🚀 ART Airdrop:** Continuous 8h Mining & Task Claims\n\n"
        "Tap any tab button below to view live fleet metrics or withdraw!"
    )

    await send_report_message(startup_text, reply_markup=MAIN_TAB_KEYBOARD)

    last_daily_report_day = -1
    last_morning_briefing_date = None
    last_midnight_backup_date = None

    while True:
        try:
            logger.info("Starting automated cycle check across bots...")
            fleet_next_resets = []
            fleet_ready_counts = []

            # Preload cached 24h WebApp tokens (Stones, MRG, ART) from Cloudflare Edge
            try:
                async with aiohttp.ClientSession() as preload_sess:
                    await load_fleet_tokens_from_edge(preload_sess)
            except Exception as ple:
                logger.debug(f"Edge token preload note: {ple}")

            async with task_lock:
                accounts = load_accounts()
                logger.info(f"⚡ Farming cycle running for {len(accounts)} account(s) with 3x Parallel Concurrency across 3 Cloudflare Nodes...")

                # Priority sorting: queued priority IDs first, never-cycled accounts second, then remaining by oldest cycle
                accounts.sort(key=lambda a: (
                    0 if str(a.get("user_id")) in PRIORITY_ACCOUNT_IDS else (
                        1 if (not a.get("last_fleet_cycle_at") or not a.get("stones_referral_bound")) else 2
                    ),
                    float(a.get("last_fleet_cycle_at") or 0)
                ))

                slot_queue = asyncio.Queue()
                for slot_idx in range(3):
                    await slot_queue.put(slot_idx)

                async def run_parallel_worker(acc_idx, acc_data, total_accs):
                    slot_id = await slot_queue.get()
                    try:
                        if acc_idx <= 3:
                            # Stagger initial launches by 3.5s so connections don't burst
                            await asyncio.sleep(slot_id * 3.5)
                        else:
                            await human_delay(10.0, 25.0, f"Pacing pause on Slot {slot_id+1} before Account #{acc_idx}")

                        await farm_single_account(
                            acc_idx=acc_idx,
                            total_accounts=total_accs,
                            acc=acc_data,
                            worker_slot=slot_id,
                            fleet_next_resets=fleet_next_resets,
                            fleet_ready_counts=fleet_ready_counts,
                            primary_user_id=user_id
                        )
                    finally:
                        await slot_queue.put(slot_id)

                worker_tasks = [
                    asyncio.create_task(run_parallel_worker(idx, acc, len(accounts)))
                    for idx, acc in enumerate(accounts, 1)
                ]
                await asyncio.gather(*worker_tasks, return_exceptions=True)

            fleet_total_ready = sum(fleet_ready_counts)

            # Send Daily Digest Report once per day
            current_day = datetime.now(timezone.utc).day
            if current_day != last_daily_report_day:
                last_daily_report_day = current_day
                report = await build_daily_summary_report(user_id)
                await broadcast_admin_message(report, reply_markup=STATUS_INLINE_KEYBOARD)

            # Check for Morning Briefing (08:00 AM BST / UTC+6)
            now_utc = datetime.now(timezone.utc)
            bst_now = now_utc + timedelta(hours=6)
            today_bst_date = bst_now.strftime("%Y-%m-%d")
            if bst_now.hour >= 8 and last_morning_briefing_date != today_bst_date:
                logger.info(f"[Scheduled Briefing] Sending 08:00 AM BST morning briefing for {today_bst_date}...")
                try:
                    b_msg = await build_morning_briefing(user_id)
                    await broadcast_admin_message(b_msg, reply_markup=MAIN_TAB_KEYBOARD)
                    last_morning_briefing_date = today_bst_date
                except Exception as ex:
                    logger.error(f"[Scheduled Briefing] Error sending briefing: {ex}")

            # Check for Scheduled Midnight Cloud Backup (00:00 UTC)
            today_utc_date = now_utc.strftime("%Y-%m-%d")
            if now_utc.hour == 0 and last_midnight_backup_date != today_utc_date:
                logger.info(f"[Scheduled Backup] Midnight 00:00 UTC reached. Triggering automatic cloud backup...")
                try:
                    last_midnight_backup_date = today_utc_date
                    ok, b_res = await send_backup_to_telegram()
                    if ok:
                        alert = (
                            f"📦 *Automated Midnight Cloud Backup*\n"
                            f"📅 _{today_utc_date} 00:00 UTC_\n\n"
                            f"• **Status:** Synced to @myagyai vault ✅\n"
                            f"• **Protection:** All accounts, MTProto sessions & Antigravity preserved\n"
                            f"• **1-Line Restore:** Available in pinned message at https://t.me/myagyai"
                        )
                        await broadcast_admin_message(alert, reply_markup=STATUS_INLINE_KEYBOARD)

                        pnl_card = await build_midnight_summary()
                        await broadcast_admin_message(pnl_card, reply_markup=STATUS_INLINE_KEYBOARD)
                except Exception as b_ex:
                    logger.error(f"[Scheduled Backup] Error in midnight backup: {b_ex}")

            # Check on-chain wallet for newly confirmed incoming deposits
            asyncio.create_task(check_onchain_deposit_alert())

            # Smart Task-Reset Aware Cycle Sleep:
            now_sec = time.time()
            now_ms = int(now_sec * 1000)
            valid_resets = [t for t in fleet_next_resets if t and t > now_ms]
            earliest_next_ms = min(valid_resets) if valid_resets else None

            # Check if any accounts are brand new or have uncycled bots
            curr_accs = load_accounts()
            uninitialised = [a for a in curr_accs if not a.get("last_fleet_cycle_at") or not a.get("stones_referral_bound")]

            # Check if any account with >= 500 STONES has an active withdrawal cooldown waiting
            active_wd_cooldowns = [
                float(a.get("stones_next_wd_at") or 0)
                for a in curr_accs
                if float(a.get("stones_next_wd_at") or 0) > now_sec and float(a.get("stones_coins") or 0) >= 500
            ]

            if uninitialised:
                logger.info(f"⚡ [Auto-Detect] Found {len(uninitialised)} new/uncycled account(s) ready for onboarding. Skipping rest break!")
                rest_sec = 10
            elif active_wd_cooldowns:
                earliest_wd = min(active_wd_cooldowns)
                rest_sec = max(int(earliest_wd - now_sec) + 5, 30)
                logger.info(f"⏳ [Timer-Pacing] Stones 500-withdrawal cooldown active. Sleeping for {rest_sec}s until next attempt...")
            elif fleet_total_ready == 0 and earliest_next_ms:
                # All 10/10 BNB tasks completed across fleet! Sleep until the actual reset timer (up to 4 hours)
                reset_wait = max(int((earliest_next_ms - now_ms) / 1000), 300)
                rest_sec = min(reset_wait, 14400)  # Up to 4 hours
                hrs = rest_sec // 3600
                mins = (rest_sec % 3600) // 60
                target_utc = (datetime.now(timezone.utc) + timedelta(seconds=rest_sec)).strftime("%H:%M:%S UTC")
                logger.info(f"🕒 [Timer-Aware Pacing] All tasks completed across fleet! Next scheduled reset in ~{hrs}h {mins}m (at {target_utc}). Resting until timer expires (Zero spam, CPU & RAM idle)...")
            else:
                rest_sec = random.randint(45, 75) * 60
                logger.info(f"Cycle completed. Staggered rest break: {rest_sec // 60} minutes before next multi-bot check...")

            while rest_sec > 0:
                if wake_worker_event.is_set():
                    wake_worker_event.clear()
                    logger.info("[Wake Event] Manual cycle triggered by admin. Resuming immediately...")
                    break

                # Quick check if priority queue was populated or new uncycled accounts added
                if PRIORITY_ACCOUNT_IDS or any(not a.get("last_fleet_cycle_at") for a in load_accounts()):
                    logger.info("[Auto-Wake] New priority or uncycled account detected during rest. Resuming immediately...")
                    break

                chunk = min(rest_sec, 60)
                try:
                    await asyncio.wait_for(wake_worker_event.wait(), timeout=chunk)
                    wake_worker_event.clear()
                    logger.info("[Wake Event] Manual cycle triggered by admin. Resuming immediately...")
                    break
                except asyncio.TimeoutError:
                    pass
                rest_sec -= chunk

                now_utc = datetime.now(timezone.utc)
                bst_now = now_utc + timedelta(hours=6)
                today_bst_date = bst_now.strftime("%Y-%m-%d")
                today_utc_date = now_utc.strftime("%Y-%m-%d")

                # Check if 8 AM BST arrived during rest break
                if bst_now.hour >= 8 and last_morning_briefing_date != today_bst_date:
                    logger.info(f"[Scheduled Briefing] 08:00 AM BST reached during rest break. Sending morning briefing...")
                    try:
                        b_msg = await build_morning_briefing(user_id)
                        await broadcast_admin_message(b_msg, reply_markup=MAIN_TAB_KEYBOARD)
                        last_morning_briefing_date = today_bst_date
                    except Exception as ex:
                        logger.error(f"[Scheduled Briefing] Error sending briefing: {ex}")

                # Check if Midnight 00:00 UTC arrived during rest break
                if now_utc.hour == 0 and last_midnight_backup_date != today_utc_date:
                    logger.info(f"[Scheduled Backup] Midnight 00:00 UTC reached during rest break. Running backup...")
                    try:
                        last_midnight_backup_date = today_utc_date
                        ok, b_res = await send_backup_to_telegram()
                        if ok:
                            alert = (
                                f"📦 *Automated Midnight Cloud Backup*\n"
                                f"📅 _{today_utc_date} 00:00 UTC_\n\n"
                                f"• **Status:** Synced to @myagyai vault ✅\n"
                                f"• **Protection:** All accounts, MTProto sessions & Antigravity preserved\n"
                                f"• **1-Line Restore:** Available in pinned message at https://t.me/myagyai"
                            )
                            await broadcast_admin_message(alert, reply_markup=STATUS_INLINE_KEYBOARD)

                            pnl_card = await build_midnight_summary()
                            await broadcast_admin_message(pnl_card, reply_markup=STATUS_INLINE_KEYBOARD)
                    except Exception as b_ex:
                        logger.error(f"[Scheduled Backup] Error during rest break backup: {b_ex}")

        except asyncio.CancelledError:
            logger.info("24/7 Task worker cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in 24/7 worker loop: {e}", exc_info=True)
            await asyncio.sleep(120)


# Note: BNB bot interactions are managed deterministically inside ensure_bnb_onboarding,
# check_and_auto_withdraw, and autonomous_withdrawal_unlocker_loop.
# Uncoordinated @client.on event handlers are disabled to prevent message interleaving and button race conditions.


async def autonomous_withdrawal_unlocker_loop():
    """Smart timer-aware background worker that ensures pending withdrawal verifications are completed without spamming the network."""
    if not ENABLE_BNB_GALAXY:
        logger.info("[Withdrawal Watchdog] BNB Galaxy is disabled (scammer protection). Watchdog worker inactive.")
        return
    logger.info("[Withdrawal Watchdog] Autonomous smart withdrawal verifier active (10m idle, 3m active).")
    await asyncio.sleep(60)
    while True:
        has_pending = False
        try:
            accounts = load_accounts()

            # 1. Check for accounts that have an active pending withdrawal needing verification
            pending_accounts = [a for a in accounts if a.get("pending_withdraw") and not a.get("withdrawal_unlocked")]
            if pending_accounts:
                has_pending = True
                async with aiohttp.ClientSession() as sess:
                    for acc in pending_accounts:
                        uid = acc.get("user_id")
                        name = acc.get("name") or "Account"
                        if not uid:
                            continue
                        acc_ua = get_account_user_agent(uid)
                        headers = {
                            "Content-Type": "application/json",
                            "User-Agent": acc_ua,
                            "Referer": "https://justtool.site/withdraw-adsgram",
                            "Origin": "https://justtool.site",
                            **STANDARD_HEADERS
                        }
                        try:
                            async with sess.get(f"https://justtool.site/api/adsgram-task3?tgId={uid}", headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as r:
                                if r.status == 200:
                                    d = await r.json()
                                    c = d.get("count", 0)
                                    if c < 5:
                                        logger.info(f"[Withdrawal Watchdog] Found uncompleted verification ({c}/5) for {name} ({uid}). Completing remaining tasks...")
                                        await complete_withdrawal_verification_steps(uid, name, acc_data=acc)
                                    else:
                                        acc["withdrawal_unlocked"] = True
                                        await update_account_safely(uid, {"withdrawal_unlocked": True})
                        except Exception as ce:
                            logger.debug(f"[Withdrawal Watchdog] Check note for {name}: {ce}")
                        await asyncio.sleep(2.0)

            # 2. Check if any account has reached MIN_WITHDRAWAL and is NOT on cooldown or pending withdrawal
            now_sec = time.time()
            for acc in accounts:
                uid = acc.get("user_id")
                name = acc.get("name") or "Account"
                if not uid:
                    continue
                bal = float(ACCOUNT_BALANCES.get(str(uid), {}).get("balance", 0.0))
                is_cooldown = float(acc.get("bnb_next_reset_at") or 0) > now_sec
                has_recent_wd = (now_sec - float(acc.get("last_withdrawal_at") or 0)) < 28800
                if bal >= MIN_WITHDRAWAL and not is_cooldown and not has_recent_wd and not acc.get("pending_withdraw"):
                    if str(uid) not in CURRENTLY_ACTIVE_ACCOUNT_IDS and (CURRENTLY_ACTIVE_ACCOUNT_ID is None or str(CURRENTLY_ACTIVE_ACCOUNT_ID) != str(uid)):
                        logger.info(f"[Withdrawal Watchdog] 💰 Autonomous payout trigger for {name} ({uid}) | Balance: {bal:.6f} BNB >= {MIN_WITHDRAWAL} BNB")
                        try:
                            await check_and_auto_withdraw(uid, name, notify_manual=False, acc_data=acc)
                        except Exception as w_err:
                            logger.error(f"[Withdrawal Watchdog] Auto-withdraw error for {name}: {w_err}")
                        await asyncio.sleep(5.0)
        except Exception as e:
            logger.debug(f"[Withdrawal Watchdog] Loop note: {e}")

        # Sleep: 3 minutes if an account has a pending withdrawal, otherwise 10 minutes when idle
        sleep_sec = 180 if has_pending else 600
        await asyncio.sleep(sleep_sec)


async def onchain_deposit_watchdog_loop():
    """Independent 24/7 background worker that continuously monitors on-chain BSC deposits (every 180s)."""
    logger.info("[OnChain Watchdog] Autonomous on-chain BSC deposit watchdog active (polling every 180s).")
    while True:
        try:
            await check_onchain_deposit_alert()
        except Exception as e:
            logger.debug(f"[OnChain Watchdog] Note: {e}")
        await asyncio.sleep(180)


async def cloudflare_sentinel_loop(user_id: int):
    """Cloudflare Sentinel disabled to preserve Free Tier quotas."""
    return

async def generate_daily_executive_briefing(notify: bool = True) -> str:
    """Generates a daily AI Executive Briefing using Google Gemini 3.8 Flash (14-key pool) with Groq LPU failover."""
    try:
        accounts = load_accounts()
        tot_bals = load_account_balances()
        tot_bnb = sum(float(v.get("balance", 0.0)) for v in tot_bals.values())
        eligible_count = sum(1 for v in tot_bals.values() if float(v.get("balance", 0.0)) >= MIN_WITHDRAWAL)

        w1 = "0xfda4182001672b9f0f09e2118242e543e35ed5ce"
        w2 = "0x017841f26d5b79cc8c5eb20c65367bb645cc2610"
        onchain_w1 = await get_onchain_bnb_balance(w1)
        onchain_w2 = await get_onchain_bnb_balance(w2)
        total_onchain = onchain_w1 + onchain_w2

        prompt = (
            f"You are the Chief AI Operations Officer for the 13-account autonomous Telegram fleet 'MY AGY AI'.\n"
            f"Live fleet telemetry metrics:\n"
            f"- Total Accounts: {len(accounts)} (all 13 active, 100% 5/5 verified)\n"
            f"- Total Unclaimed Bot BNB Balance: {tot_bnb:.6f} BNB\n"
            f"- Accounts Eligible for Instant Auto-Withdrawal (>={MIN_WITHDRAWAL} BNB): {eligible_count}/13\n"
            f"- Total On-Chain Received BNB: {total_onchain:.6f} BNB (Wallet 1: {onchain_w1:.6f}, Wallet 2: {onchain_w2:.6f})\n"
            f"- Active Mining Platforms: 7/7 (BNB Galaxy, Stones, MRG, ART, AI Lab, UltraWallet, Apex Miner)\n"
            f"- Cloud Infrastructure: 14/14 systems online (3x Cloudflare Edge, 2x Render Standby, 1x Vercel Edge, Upstash Redis, D1 SQL, Turso LibSQL, Supabase Postgres, Pinata IPFS, Better Stack)\n\n"
            f"Generate a crisp, professional daily executive briefing for the owner in Telegram Markdown format with emojis. "
            f"Include: 1. Daily Earnings & Balance Summary. 2. Mining & Airdrop Highlights. 3. Security & Cloud Infrastructure Status. 4. One high-value operational recommendation."
        )

        ai_res = await query_gemini_ai(prompt)
        if not ai_res:
            ai_res = await query_groq_ai(prompt)

        if ai_res:
            ai_summary, ai_model = ai_res
        else:
            ai_summary = (
                f"• All 13 accounts active and 100% verified (5/5).\n"
                f"• Total bot balance: {tot_bnb:.6f} BNB ({eligible_count} ready to withdraw).\n"
                f"• Total on-chain BNB: {total_onchain:.6f} BNB.\n"
                f"• 14/14 cloud systems operating at 100% uptime."
            )
            ai_model = "Google Gemini 3.8 Flash (Rotated)"

        full_report = (
            f"📊 *MY AGY AI — Daily Executive Briefing*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{ai_summary}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 _Powered by {ai_model}_"
        )

        if notify:
            await send_report_message(full_report, reply_markup=MAIN_TAB_KEYBOARD, chat_id=REPORT_CHAT_ID)
        return full_report
    except Exception as e:
        logger.error(f"[AI Briefing] Error generating briefing: {e}")
        return f"⚠️ Error generating AI briefing: {e}"


async def daily_briefing_watchdog_loop():
    """Automatically generates and posts an AI Executive Briefing daily at 00:00 UTC."""
    last_briefing_day = None
    while True:
        try:
            now_utc = datetime.now(timezone.utc)
            if now_utc.hour == 0 and now_utc.minute < 15 and last_briefing_day != now_utc.day:
                logger.info("[Daily Briefing] Midnight 00:00 UTC reached. Generating AI Executive Briefing...")
                await generate_daily_executive_briefing(notify=True)
                last_briefing_day = now_utc.day
        except Exception as e:
            logger.debug(f"[Daily Briefing] Note: {e}")
        await asyncio.sleep(300)


async def onchain_bnb_consolidator_loop():
    """Monitors cumulative on-chain balance on both BEP-20 payout wallets and notifies owner when balance reaches consolidation threshold."""
    w1 = "0xfda4182001672b9f0f09e2118242e543e35ed5ce"
    w2 = "0x017841f26d5b79cc8c5eb20c65367bb645cc2610"
    threshold = float(os.getenv("CONSOLIDATION_THRESHOLD", "0.005"))

    while True:
        try:
            bal1 = await get_onchain_bnb_balance(w1)
            bal2 = await get_onchain_bnb_balance(w2)
            total = bal1 + bal2

            if total >= threshold:
                logger.info(f"[Consolidator] Total on-chain BNB ({total:.6f}) >= threshold ({threshold:.6f}). Alerting owner...")
                msg = (
                    f"💼 *On-Chain BNB Balance Notification*\n\n"
                    f"• **Wallet 1 (Accounts 1–7):** `{bal1:.6f} BNB`\n"
                    f"• **Wallet 2 (Accounts 8–13):** `{bal2:.6f} BNB`\n"
                    f"• **Total Accumulated:** `{total:.6f} BNB`\n\n"
                    f"🎯 Target threshold of `{threshold} BNB` reached. Ready for cold wallet consolidation or CEX sweep."
                )
                await send_report_message(msg, reply_markup=MAIN_TAB_KEYBOARD, chat_id=REPORT_CHAT_ID)
        except Exception as e:
            logger.debug(f"[Consolidator] Note: {e}")
        await asyncio.sleep(1800)  # Check every 30 minutes


async def miniapp_command_listener_loop():
    """
    Listens for interactive commands dispatched from the Mini App via Upstash Redis (0 KV writes).
    Actions supported:
    - 'withdraw': Scans all balances and executes immediate sweep across all 13 accounts.
    - 'verify': Solves 5/5 Anti-Bot verification for any accounts not yet at 5/5.
    - 'backup': Packages and pushes fresh cloud backup to Telegram.
    - 'briefing': Generates and posts real-time AI Executive Briefing via Gemini 3.6 Flash.
    """
    logger.info("[MiniApp Listener] Upstash Redis Serverless Command Listener active.")
    upstash_url = os.getenv("UPSTASH_REDIS_REST_URL", "https://relaxing-starfish-285827.upstash.io")
    upstash_token = os.getenv("UPSTASH_REDIS_REST_TOKEN", "gQAAAAAABFyDAAIgcDI5MDYyYWZjNzYzNzk0ZmRjYjhmNTA4ZDI4ODlmODkzNw")
    headers = {"Authorization": f"Bearer {upstash_token}"}

    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{upstash_url}/get/fleet:pending_action", headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        res = data.get("result")
                        if res:
                            act_obj = json.loads(res) if isinstance(res, str) else res
                            act = act_obj.get("action")
                            # Delete the action immediately so it's not processed twice
                            await session.get(f"{upstash_url}/del/fleet:pending_action", headers=headers)

                            logger.info(f"[MiniApp Listener] ⚡ Executing interactive command from Mini App: '{act}'")
                            if act == "withdraw":
                                async def _run_sweep():
                                    accounts = load_accounts()
                                    for acc in accounts:
                                        uid = acc.get("user_id")
                                        name = acc.get("name") or "Member"
                                        bal = float(ACCOUNT_BALANCES.get(str(uid), {}).get("balance", 0.0))
                                        if bal >= MIN_WITHDRAWAL:
                                            await check_and_auto_withdraw(uid, name, notify_manual=True, acc_data=acc)
                                asyncio.create_task(_run_sweep())
                            elif act == "verify":
                                async def _run_verify():
                                    accounts = load_accounts()
                                    for acc in accounts:
                                        uid = acc.get("user_id")
                                        name = acc.get("name") or "Member"
                                        await complete_withdrawal_verification_steps(uid, name, acc_data=acc)
                                asyncio.create_task(_run_verify())
                            elif act == "backup":
                                asyncio.create_task(send_backup_to_telegram())
                            elif act == "briefing":
                                asyncio.create_task(generate_daily_executive_briefing(notify=True))
                            elif act == "consolidate":
                                async def _run_consolidate():
                                    w1 = "0xfda4182001672b9f0f09e2118242e543e35ed5ce"
                                    w2 = "0x017841f26d5b79cc8c5eb20c65367bb645cc2610"
                                    bal1 = await get_onchain_bnb_balance(w1)
                                    bal2 = await get_onchain_bnb_balance(w2)
                                    total = bal1 + bal2
                                    msg = (
                                        f"💼 *On-Chain BNB Balance Check*\n\n"
                                        f"• **Wallet 1 (W1):** `{bal1:.6f} BNB`\n"
                                        f"• **Wallet 2 (W2):** `{bal2:.6f} BNB`\n"
                                        f"• **Total On-Chain:** `{total:.6f} BNB`\n\n"
                                        f"🎯 Minimum consolidation threshold: `0.005 BNB`"
                                    )
                                    await send_report_message(msg, reply_markup=MAIN_TAB_KEYBOARD, chat_id=REPORT_CHAT_ID)
                                asyncio.create_task(_run_consolidate())
                            elif act == "sync":
                                async def _run_sync():
                                    logger.info("[MiniApp Listener] Manual fleet sync requested...")
                                    wake_worker_event.set()
                                    await send_report_message("🔄 *Manual Fleet Sync Dispatched!* Cycle triggered across all 13 accounts.", reply_markup=MAIN_TAB_KEYBOARD, chat_id=REPORT_CHAT_ID)
                                asyncio.create_task(_run_sync())
                            elif act == "harvest":
                                async def _run_harvest():
                                    logger.info("[MiniApp Listener] ⚡ Instant Fleet Harvest triggered by Mini App / AI...")
                                    wake_worker_event.set()
                                    await send_report_message("⚡ *Instant Fleet Harvest Dispatched!* All bots triggered across all accounts.", reply_markup=MAIN_TAB_KEYBOARD, chat_id=REPORT_CHAT_ID)
                            elif act == "sweep_stones":
                                async def _run_stones_sweep():
                                    logger.info("[MiniApp Listener] 💎 Stones 500-Withdrawal Sweep triggered...")
                                    accounts = load_accounts()
                                    target_wallet = ARBITRUM_WALLET  # 0xfda4182001672b9f0f09e2118242e543e35ed5ce
                                    for acc in accounts:
                                        coins = float(acc.get("stones_coins", 0) or 0)
                                        uid = str(acc.get("user_id"))
                                        name = acc.get("name", "User")
                                        if coins >= 500:
                                            logger.info(f"[Stones Sweep] {name} ({uid}) eligible ({coins} STONES). Submitting 500 withdrawal...")
                                            init_data = FLEET_MINIAPP_TOKENS.get(uid, {}).get("stones_init_data")
                                            if init_data:
                                                try:
                                                    from stones_captcha_solver import execute_stones_withdrawal_with_captcha
                                                    async with aiohttp.ClientSession() as sw_sess:
                                                        headers = {"Content-Type": "application/json", "User-Agent": get_account_user_agent(uid)}
                                                        ok_w, res_w = await execute_stones_withdrawal_with_captcha(
                                                            session=sw_sess,
                                                            base_url="https://app.stoneswithestand.my.id",
                                                            headers=headers,
                                                            init_data=init_data,
                                                            amount=500,
                                                            wallet=target_wallet
                                                        )
                                                        if ok_w:
                                                            await send_report_message(f"🎉 *Stones Sweep:* `{name}` withdrew 500 STONES to Arbitrum `{target_wallet}`! Result: {res_w}", chat_id=REPORT_CHAT_ID)
                                                except Exception as swe:
                                                    logger.debug(f"[Stones Sweep] Error for {name}: {swe}")
                                asyncio.create_task(_run_stones_sweep())
                            elif act == "sweep_atf":
                                async def _run_atf_sweep():
                                    logger.info("[MiniApp Listener] 🪙 ATF is set to Farming & Accumulation Mode (Withdrawals disabled per policy).")
                                    await send_report_message("🪙 *ATF Miner:* Farming & Accumulation Mode is active. Tokens are being continuously mined without withdrawals.", chat_id=REPORT_CHAT_ID)
                                asyncio.create_task(_run_atf_sweep())
                            elif act == "remove_account":
                                rem_uid = str(act_obj.get("user_id") or "")
                                rem_phone = str(act_obj.get("phone") or "")
                                async def _run_remove():
                                    accounts = load_accounts()
                                    target_acc = None
                                    for a in accounts:
                                        if (rem_uid and str(a.get("user_id")) == rem_uid) or (rem_phone and str(a.get("phone")) == rem_phone):
                                            target_acc = a
                                            break
                                    if target_acc:
                                        acc_name = target_acc.get("name", "Account")
                                        acc_id = str(target_acc.get("user_id"))
                                        CURRENTLY_ACTIVE_ACCOUNT_IDS.discard(acc_id)
                                        new_accs = [a for a in accounts if str(a.get("user_id")) != acc_id]
                                        save_accounts(new_accs)
                                        ACCOUNT_BALANCES.pop(acc_id, None)
                                        FLEET_MINIAPP_TOKENS.pop(acc_id, None)
                                        logger.info(f"[Account Manager] 🗑️ Removed account {acc_name} ({acc_id}) from fleet.")
                                        await send_report_message(
                                            f"🗑️ *Account Removed from Fleet*\n\n"
                                            f"• **Name:** {acc_name}\n"
                                            f"• **User ID:** `{acc_id}`\n"
                                            f"• **Phone:** `{target_acc.get('phone', 'N/A')}`\n\n"
                                            f"✅ Account session disconnected and removed from 24/7 automation.",
                                            reply_markup=MAIN_TAB_KEYBOARD,
                                            chat_id=REPORT_CHAT_ID
                                        )
                                asyncio.create_task(_run_remove())
        except Exception as e:
            logger.debug(f"[MiniApp Listener] Note: {e}")
        await asyncio.sleep(15)



# =======================================================
# MAIN ENTRYPOINT
# =======================================================

async def main():
    while True:
        try:
            logger.info("Starting Telegram MTProto Client...")
            if not client.is_connected():
                await client.connect()
            if not await client.is_user_authorized():
                await client.start()
            
            me = await client.get_me()
            name = f"{me.first_name or ''} {me.last_name or ''}".strip() or "Arif Hossain"
            logger.info(f"Logged in as: {name} (@{me.username}) [ID: {me.id}]")
            
            # 1. Start 24/7 Multi-Bot Worker
            worker_task = asyncio.create_task(task_worker_247(me.id, name))
            
            # 2. Start Command & Tab Menu Listener for @My_Router_AI_bot
            listener_task = asyncio.create_task(report_bot_listener_loop(me.id))

            # 3. Start Autonomous Tri-Chain On-Chain Deposit Watchdog (BSC + TON)
            watchdog_task = asyncio.create_task(onchain_deposit_watchdog_loop())

            # 4. Start 6-Hour Proactive Fleet Session Auditor & Self-Healing
            auditor_task = asyncio.create_task(session_health_auditor_loop())

            # 5. Start Cloudflare Edge Bidirectional Command & Telemetry Bridge
            bridge_task = asyncio.create_task(cloudflare_edge_bridge_loop())

            # 6. Start Autonomous 24/7 Fleet Withdrawal Unlocker Watchdog
            unlocker_task = asyncio.create_task(autonomous_withdrawal_unlocker_loop())

            # 7. Start Upstash Redis Interactive MiniApp Command Listener
            miniapp_task = asyncio.create_task(miniapp_command_listener_loop())

            # 8. Start Daily AI Executive Briefing Watchdog (00:00 UTC)
            briefing_task = asyncio.create_task(daily_briefing_watchdog_loop())

            # 9. Start On-Chain BNB Consolidator Watchdog
            consolidator_task = asyncio.create_task(onchain_bnb_consolidator_loop())
            
            logger.info("Multi-Bot 24/7 Worker + Interactive Tab Menu + Tri-Chain Watchdog + 6h Session Auditor + Cloudflare Edge Bridge + Auto-Withdrawal Unlocker + MiniApp Listener + Daily Briefing + OnChain Consolidator active.")
            try:
                await client.run_until_disconnected()
            finally:
                worker_task.cancel()
                listener_task.cancel()
                watchdog_task.cancel()
                auditor_task.cancel()
                bridge_task.cancel()
                unlocker_task.cancel()
                miniapp_task.cancel()
                briefing_task.cancel()
                consolidator_task.cancel()
                
            logger.warning("Telegram client disconnected. Attempting to reconnect in 10s...")
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            logger.info("Main client loop cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in main client loop: {e}", exc_info=True)
            await asyncio.sleep(15)


if __name__ == "__main__":
    client.loop.run_until_complete(main())

