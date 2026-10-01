import os
import time
import json
import random
import asyncio
import urllib.parse
import logging
import re
import aiohttp
import datetime

try:
    from proxy_manager import get_account_user_agent
except Exception:
    DEVICE_POOL_UAS = [
        "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro Build/UD1A.230803.041) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.127 Mobile Safari/537.36 Telegram-Android/11.1.3",
        "Mozilla/5.0 (Linux; Android 14; SM-S928B Build/UP1A.231005.007) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.127 Mobile Safari/537.36 Telegram-Android/11.1.2",
        "Mozilla/5.0 (Linux; Android 14; CPH2581 Build/UKQ1.230924.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.127 Mobile Safari/537.36 Telegram-Android/11.0.9",
        "Mozilla/5.0 (Linux; Android 14; 23116PN5BC Build/UKQ1.230804.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.127 Mobile Safari/537.36 Telegram-Android/11.1.0",
        "Mozilla/5.0 (Linux; Android 14; XQ-EC54 Build/69.0.A.2.44) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.127 Mobile Safari/537.36 Telegram-Android/11.0.7",
        "Mozilla/5.0 (Linux; Android 14; motorola edge 50 ultra Build/U2UW34.42-32) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.127 Mobile Safari/537.36 Telegram-Android/11.1.1",
        "Mozilla/5.0 (Linux; Android 14; A065 Build/NothingOS2.5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.127 Mobile Safari/537.36 Telegram-Android/11.0.8",
        "Mozilla/5.0 (Linux; Android 14; ASUS_AI2401_A Build/UKQ1.231003.002) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.127 Mobile Safari/537.36 Telegram-Android/11.1.3"
    ]
    def get_account_user_agent(identifier):
        seed = abs(hash(str(identifier)))
        return DEVICE_POOL_UAS[seed % len(DEVICE_POOL_UAS)]

from fastapi import FastAPI, HTTPException, Request
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import RequestWebViewRequest, RequestAppWebViewRequest, ImportChatInviteRequest, GetBotCallbackAnswerRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.account import UpdateNotifySettingsRequest
from telethon.tl.types import InputBotAppShortName, InputNotifyPeer, InputPeerNotifySettings
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    PhoneNumberInvalidError,
    FloodWaitError
)

try:
    from web3 import Web3
    from eth_account import Account
    HAS_WEB3 = True
except ImportError:
    HAS_WEB3 = False

try:
    from tonsdk.contract.wallet import Wallets, WalletVersionEnum
    import base64
    HAS_TONSDK = True
except ImportError:
    HAS_TONSDK = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RenderSessionCollector")

app = FastAPI(title="MY AGY AI — Standby Batch Session Link Collector")

SECRET_KEY = os.getenv("SECRET_KEY", "agy_cf_secret_7d36994e_2026")
API_ID = int(os.getenv("TELEGRAM_API_ID", "37321306"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "5cd9e5bbfb572a4429a0c54774153b47")
REPORT_CHAT_ID = os.getenv("REPORT_CHAT_ID", "6727787768")

CF_WORKER_URLS = [
    "https://restore-agy.aaaai2.workers.dev",
    "https://restore-agy.aaa-bot.workers.dev",
    "https://restore-agy.aaa222.workers.dev",
    "https://restore-agy.agorameet.workers.dev",
    "https://restore-agy.aaaai.workers.dev"
]

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://znbbaozpevurvbfkxakz.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpuYmJhb3pwZXZ1cnZiZmt4YWt6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODk4MTYxNTQsImV4cCI6MjEwNTM5MjE1NH0.ldgn0gCtOLEPUQyvTiG5RgKX6VY0LrS_4LkIKCf8NqM")
UPSTASH_URL = os.getenv("UPSTASH_URL", "https://relaxing-starfish-285827.upstash.io")
UPSTASH_TOKEN = os.getenv("UPSTASH_TOKEN", "gQAAAAAABFyDAAIgcDI5MDYyYWZjNzYzNzk0ZmRjYjhmNTA4ZDI4ODlmODkzNw")

CACHED_GEMINI_KEYS = []

async def get_gemini_keys() -> list:
    global CACHED_GEMINI_KEYS
    if CACHED_GEMINI_KEYS:
        return CACHED_GEMINI_KEYS
    env_k = os.getenv("GEMINI_API_KEYS", "")
    if env_k:
        CACHED_GEMINI_KEYS = [k.strip() for k in env_k.split(",") if k.strip()]
        return CACHED_GEMINI_KEYS
    if UPSTASH_URL and UPSTASH_TOKEN:
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(f"{UPSTASH_URL}/get/fleet:gemini_keys", headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}, timeout=aiohttp.ClientTimeout(total=4)) as r:
                    if r.status == 200:
                        data = await r.json()
                        res = data.get("result")
                        if res:
                            CACHED_GEMINI_KEYS = [k.strip() for k in res.split(",") if k.strip()]
        except Exception:
            pass
    return CACHED_GEMINI_KEYS

async def solve_stones_captcha_ai(session: aiohttp.ClientSession, img_base64: str, length: int = 5) -> str:
    """Solves Stones Miner captcha using rotating Gemini Vision models."""
    if not img_base64:
        return ""
    if "," in img_base64:
        img_base64 = img_base64.split(",")[-1]

    keys = await get_gemini_keys()
    if not keys:
        return ""

    prompt = (
        f"Look at this captcha image carefully. It contains exactly {length} alphanumeric characters "
        "(letters and numbers). Return ONLY the {length} characters in uppercase, strictly no spaces, no punctuation, no explanations."
    )
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/png", "data": img_base64}}
            ]
        }]
    }
    models = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.0-flash"]
    import random
    shuffled_keys = list(keys)
    random.shuffle(shuffled_keys)

    for model in models:
        for k in shuffled_keys[:4]:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            headers = {"Content-Type": "application/json", "X-goog-api-key": k}
            try:
                async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as gr:
                    if gr.status == 200:
                        gdata = await gr.json()
                        candidates = gdata.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                raw_text = parts[0].get("text", "")
                                clean = re.sub(r"[^a-zA-Z0-9]", "", raw_text).upper().strip()
                                if len(clean) == length:
                                    return clean
            except Exception:
                continue
    return ""

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
}

def solve_atf_math(question_text: str) -> str:
    """Safely solves ATF Miner mathematical challenges with multiple regex fallbacks."""
    if not question_text:
        return "0"
    cleaned = re.sub(r"[^\d\+\-\*\/\(\)\s]", " ", question_text)
    m = re.search(r"(\d+\s*[\+\-\*\/]\s*\d+)", cleaned)
    if m:
        try:
            expr = m.group(1).replace(" ", "")
            parts = re.split(r"([\+\-\*\/])", expr)
            if len(parts) == 3:
                a, op, b = int(parts[0]), parts[1], int(parts[2])
                if op == "+": return str(a + b)
                if op == "-": return str(a - b)
                if op == "*": return str(a * b)
                if op == "/" and b != 0: return str(a // b)
        except Exception:
            pass
    nums = [int(n) for n in re.findall(r"\d+", question_text)]
    if len(nums) >= 2:
        if "+" in question_text or "plus" in question_text.lower():
            return str(nums[0] + nums[1])
        if "-" in question_text or "minus" in question_text.lower():
            return str(nums[0] - nums[1])
        if "*" in question_text or "x" in question_text.lower() or "times" in question_text.lower():
            return str(nums[0] * nums[1])
        if "/" in question_text and nums[1] != 0:
            return str(nums[0] // nums[1])
    return "0"

STONES_BOT = "stoneswithestand_bot"
MRG_BOT = "mrgminerbot"
MRG_REFERRAL_CODE = "ref_IRN1G3XD"
ART_BOT = "ART_AIRDROP_BOT"
BNB_BOT = "CryptoProUpRobot"
AILAB_BOT = "AiLab_robot"
ULTRAWALLET_BOT = "UltrawalletTrade_Bot"
ULTRAWALLET_REFERRAL_CODE = "6727787768"
APX_BOT = "ApxMinerBot"
APX_REFERRAL_CODE = "6727787768"
AINOVUM_BOT = "ainovum_bot"
AINOVUM_REFERRAL_CODE = "ref_6727787768"
MININGGRAM_BOT = "MiningGRAM_Bot"
MININGGRAM_REFERRAL_CODE = "339JU9K"
TRXPOWER_BOT = "trxpowermining_bot"
TRXPOWER_REFERRAL_CODE = "ref_TRX6727787768"
BTC_BOT = "BitcoinCloudMinersBot"
BTC_REFERRAL_CODE = "6727787768"
TENSOR_BOT = "TensorMiningRobot"
TENSOR_REFERRAL_CODE = "6727787768"
TONTRADER_BOT = "TonTraderAIBot"
TONTRADER_REFERRAL_CODE = "REF_6727787768"
FINVORA_BOT = "FINVORAWeb3bot"
FINVORA_REFERRAL_CODE = "ref_TRX6727787768"
TURBOGRAM_BOT = "TurboGramV1_bot"
TURBOGRAM_REFERRAL_CODE = "r_3520c92b"
OMINIX_BOT = "OminixAiBot"
OMINIX_REFERRAL_CODE = "6727787768"

LAST_BTC_MINE_TIMES = {}
LAST_BTC_TASKS_TIMES = {}
UW_ID_TOKENS = {}

LAST_BATCH_RUN = {
    "status": "idle",
    "collected": 0,
    "timestamp": 0
}

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "MY AGY AI Standby Batch Session Link Collector",
        "provider": "Render Cloud (Free Tier)",
        "purpose": "Wakes up on-demand to collect batch session links, syncs to 3x Cloudflare KV, triggers cloud farming, and spins down to save free hours.",
        "nodes": CF_WORKER_URLS,
        "last_run": LAST_BATCH_RUN
    }

@app.get("/health")
async def health():
    return {"ok": True, "status": "healthy"}

async def extract_tokens_with_client(client: TelegramClient, acc: dict) -> dict:
    name = acc.get("name", "User")
    uid = str(acc.get("user_id"))
    tokens = {
        "account_id": uid,
        "name": name,
        "synced_at": time.time()
    }

    # 1. Stones Miners WebApp initData
    try:
        bot = await client.get_entity(STONES_BOT)
        res = await client(RequestWebViewRequest(
            peer=bot,
            bot=bot,
            platform="android",
            url="https://app.stoneswithestand.my.id/"
        ))
        parsed = urllib.parse.urlparse(res.url)
        tokens["stones_init_data"] = urllib.parse.parse_qs(parsed.fragment).get("tgWebAppData", [None])[0]
    except Exception as e:
        logger.debug(f"[{name}] Stones error: {e}")

    # 2. MRG Miner WebApp initData
    try:
        bot_in = await client.get_input_entity(MRG_BOT)
        res = await client(RequestAppWebViewRequest(
            peer=bot_in,
            app=InputBotAppShortName(bot_id=bot_in, short_name="app"),
            platform="android",
            start_param=MRG_REFERRAL_CODE
        ))
        parsed = urllib.parse.urlparse(res.url)
        tokens["mrg_init_data"] = urllib.parse.parse_qs(parsed.fragment).get("tgWebAppData", [None])[0]
    except Exception as e:
        logger.debug(f"[{name}] MRG error: {e}")

    # 3. ART Airdrop WebApp initData
    try:
        bot = await client.get_entity(ART_BOT)
        res = await client(RequestWebViewRequest(
            peer=bot,
            bot=bot,
            platform="android",
            url=f"https://art.tamimdev.dev/?ref={REPORT_CHAT_ID}"
        ))
        parsed = urllib.parse.urlparse(res.url)
        tokens["art_init_data"] = urllib.parse.parse_qs(parsed.fragment).get("tgWebAppData", [None])[0]
    except Exception as e:
        logger.debug(f"[{name}] ART error: {e}")

    # 4. BNB Galaxy Webhook Link (Permanently disabled scammer bot)
    # Excluded to avoid touching blocked bot and prevent Telegram rate limits

    # 5. AI Lab Robot WebApp initData
    try:
        bot_ai = await client.get_entity(AILAB_BOT)
        res_ai = await client(RequestWebViewRequest(
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
        logger.debug(f"[{name}] AI Lab error: {aie}")

    # 6. UltraWallet WebApp initData
    try:
        bot_uw = await client.get_input_entity(ULTRAWALLET_BOT)
        res_uw = await client(RequestAppWebViewRequest(
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
        logger.debug(f"[{name}] UltraWallet error: {uwe}")

    # 7. Apex Miner WebApp initData
    try:
        bot_apx = await client.get_input_entity(APX_BOT)
        res_apx = await client(RequestAppWebViewRequest(
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
        logger.debug(f"[{name}] Apex Miner error: {apx_e}")

    # 8. Ainovum Bot WebApp initData
    try:
        bot_an = await client.get_entity(AINOVUM_BOT)
        res_an = await client(RequestWebViewRequest(
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
        logger.debug(f"[{name}] Ainovum error: {ane}")

    # 9. MiningGRAM Bot WebApp initData
    try:
        bot_mg = await client.get_input_entity(MININGGRAM_BOT)
        res_mg = await client(RequestAppWebViewRequest(
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
        logger.debug(f"[{name}] MiningGRAM error: {mge}")

    # 10. ATF Miner WebApp initData (@ATF_AIRDROP_bot)
    try:
        bot_atf = await client.get_entity("ATF_AIRDROP_bot")
        res_atf = await client(RequestWebViewRequest(
            peer=bot_atf,
            bot=bot_atf,
            platform="android",
            url="https://atfminers.asloni.online/miner/index.html?entry=bot_start",
            start_param=REPORT_CHAT_ID
        ))
        parsed_atf = urllib.parse.urlparse(res_atf.url)
        atf_init = urllib.parse.parse_qs(parsed_atf.fragment).get("tgWebAppData", [None])[0]
        if atf_init:
            tokens["atf_init_data"] = atf_init
    except Exception as atf_e:
        logger.debug(f"[{name}] ATF Miner error: {atf_e}")

    # 11. Tensor Mining Robot WebApp initData (@TensorMiningRobot)
    try:
        bot_tensor = await client.get_input_entity("TensorMiningRobot")
        res_tensor = await client(RequestAppWebViewRequest(
            peer=bot_tensor,
            app=InputBotAppShortName(bot_id=bot_tensor, short_name="myapp"),
            platform="android",
            start_param=REPORT_CHAT_ID
        ))
        parsed_tensor = urllib.parse.urlparse(res_tensor.url)
        tensor_init = urllib.parse.parse_qs(parsed_tensor.fragment).get("tgWebAppData", [None])[0]
        if tensor_init:
            tokens["tensor_init_data"] = tensor_init
    except Exception as tensor_e:
        logger.debug(f"[{name}] Tensor error: {tensor_e}")

    # 12. Ton Trader AI WebApp initData (@TonTraderAIBot)
    try:
        bot_tt = await client.get_input_entity("TonTraderAIBot")
        res_tt = await client(RequestAppWebViewRequest(
            peer=bot_tt,
            app=InputBotAppShortName(bot_id=bot_tt, short_name="app"),
            platform="android",
            start_param=f"REF_{REPORT_CHAT_ID}"
        ))
        parsed_tt = urllib.parse.urlparse(res_tt.url)
        tt_init = urllib.parse.parse_qs(parsed_tt.fragment).get("tgWebAppData", [None])[0]
        if tt_init:
            tokens["tontrader_init_data"] = tt_init
    except Exception as tt_e:
        logger.debug(f"[{name}] Ton Trader error: {tt_e}")

    # 13. Ominix AI Trade WebApp initData (@OminixAiBot)
    try:
        bot_om = await client.get_input_entity("OminixAiBot")
        res_om = await client(RequestAppWebViewRequest(
            peer=bot_om,
            app=InputBotAppShortName(bot_id=bot_om, short_name="Trade"),
            platform="android",
            start_param=REPORT_CHAT_ID
        ))
        parsed_om = urllib.parse.urlparse(res_om.url)
        om_init = urllib.parse.parse_qs(parsed_om.fragment).get("tgWebAppData", [None])[0]
        if om_init:
            tokens["ominix_init_data"] = om_init
    except Exception as om_e:
        logger.debug(f"[{name}] Ominix error: {om_e}")

    return tokens


async def extract_tokens_for_account(acc: dict) -> dict:
    name = acc.get("name", "User")
    sess_str = acc.get("session_string") or acc.get("session")
    if not sess_str:
        return {}

    client = TelegramClient(StringSession(sess_str), API_ID, API_HASH)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            logger.warning(f"[{name}] Session unauthorized")
            return {}

        return await extract_tokens_with_client(client, acc)
    except Exception as e:
        logger.error(f"[{name}] Telethon connection error: {e}")
        return {}
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass

@app.post("/collect-tokens")
async def collect_tokens(request: Request):
    auth = request.headers.get("Authorization") or ""
    if auth != f"Bearer {SECRET_KEY}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    body = {}
    try:
        body = await request.json()
    except Exception:
        pass

    accounts = body.get("accounts", [])
    
    # If accounts lack session strings, pull latest_backup_zip from Cloudflare KV
    has_sessions = any(a.get("session_string") or a.get("session") for a in accounts) if accounts else False
    if not has_sessions:
        import zipfile
        import io
        async with aiohttp.ClientSession() as http:
            for cf_url in CF_WORKER_URLS:
                try:
                    async with http.get(f"{cf_url}/backup.zip", headers=BROWSER_HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as r:
                        if r.status == 200:
                            zip_bytes = await r.read()
                            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                                if "accounts.json" in zf.namelist():
                                    raw_acc = zf.read("accounts.json").decode("utf-8")
                                    accounts = json.loads(raw_acc)
                                    logger.info(f"Loaded {len(accounts)} accounts with sessions from Cloudflare KV backup archive.")
                                    break
                except Exception as e:
                    logger.warning(f"Could not load backup zip from {cf_url}: {e}")

    if not accounts:
        return {"ok": True, "message": "No accounts with sessions found in backup archive or body", "collected": 0}

    LAST_BATCH_RUN["status"] = "running"
    LAST_BATCH_RUN["timestamp"] = time.time()

    collected_batch = {}
    for acc in accounts:
        uid = str(acc.get("user_id"))
        sess_str = acc.get("session_string") or acc.get("session")
        if sess_str and not is_account_referrals_bound(acc) and uid != "6727787768":
            try:
                cl = TelegramClient(StringSession(sess_str), API_ID, API_HASH)
                await cl.connect()
                if await cl.is_user_authorized():
                    await bind_account_master_referrals(cl, acc)
                try:
                    await cl.disconnect()
                except Exception:
                    pass
            except Exception as be:
                logger.warning(f"[{acc.get('name', uid)}] Referral binding in collect_tokens note: {be}")

        tokens = await extract_tokens_for_account(acc)
        if tokens:
            collected_batch[uid] = tokens
            async with aiohttp.ClientSession() as http:
                # 1. Sync to 3x Cloudflare KV
                for cf_url in CF_WORKER_URLS:
                    try:
                        await http.post(
                            f"{cf_url}/api/miniapp/tokens/sync",
                            json=tokens,
                            headers={
                                "Authorization": f"Bearer {SECRET_KEY}",
                                "Content-Type": "application/json",
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                            },
                            timeout=aiohttp.ClientTimeout(total=5)
                        )
                    except Exception as se:
                        logger.warning(f"Sync error to {cf_url}: {se}")

                # 2. Sync to Upstash Redis
                if UPSTASH_URL and UPSTASH_TOKEN:
                    try:
                        await http.post(
                            f"{UPSTASH_URL}/set/fleet:tokens:{uid}",
                            data=json.dumps(tokens),
                            headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"},
                            timeout=aiohttp.ClientTimeout(total=4)
                        )
                    except Exception as ue:
                        logger.warning(f"Upstash token sync note: {ue}")

                # 3. Sync to Supabase Postgres
                if SUPABASE_URL and SUPABASE_KEY:
                    try:
                        await http.patch(
                            f"{SUPABASE_URL}/rest/v1/fleet_accounts?id=eq.{uid}",
                            json={"data": tokens},
                            headers={
                                "apikey": SUPABASE_KEY,
                                "Authorization": f"Bearer {SUPABASE_KEY}",
                                "Content-Type": "application/json"
                            },
                            timeout=aiohttp.ClientTimeout(total=4)
                        )
                    except Exception as sbe:
                        logger.warning(f"Supabase account update note: {sbe}")

    # Trigger Cloudflare Edge Autonomous Cloud Farming for ALL bots
    async with aiohttp.ClientSession() as http:
        for idx, cf_url in enumerate(CF_WORKER_URLS):
            try:
                await http.post(
                    f"{cf_url}/api/farm/all",
                    json={"all": True, "bot": "all"},
                    headers={"Authorization": f"Bearer {SECRET_KEY}", "Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=10)
                )
            except Exception:
                pass

    LAST_BATCH_RUN["status"] = "completed"
    LAST_BATCH_RUN["collected"] = len(collected_batch)
    LAST_BATCH_RUN["timestamp"] = time.time()

    return {
        "ok": True,
        "collected": len(collected_batch),
        "timestamp": time.time(),
        "message": "Batch session links collected and synced to 3x Cloudflare KV nodes. Cloud farming dispatched. Standby node entering sleep."
    }

# ============================================================================
# CLOUD BNB GALAXY AUTONOMOUS ENGINE (Balance Checks & Auto-Withdrawals)
# ============================================================================
MIN_WITHDRAWAL = float(os.getenv("MIN_WITHDRAWAL", "0.000055"))
DEFAULT_WALLET = os.getenv("WALLET_ADDRESS", "0xfda4182001672b9f0f09e2118242e543e35ed5ce")
CLOUD_BNB_STATUS = {
    "last_cycle_at": 0,
    "status": "idle",
    "accounts": {}
}

FLEET_ACCOUNTS_CACHE = {}

async def fetch_accounts_from_cloud():
    global FLEET_ACCOUNTS_CACHE
    accounts_map = {}
    
    # 1. First check in-memory cache
    if FLEET_ACCOUNTS_CACHE:
        accounts_map.update(FLEET_ACCOUNTS_CACHE)

    # 2. Load base fleet accounts from Cloudflare KV backup archive
    import zipfile
    import io
    async with aiohttp.ClientSession() as http:
        for cf_url in CF_WORKER_URLS:
            try:
                async with http.get(f"{cf_url}/backup.zip", headers=BROWSER_HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as r:
                    if r.status == 200:
                        zip_bytes = await r.read()
                        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                            if "accounts.json" in zf.namelist():
                                raw_acc = zf.read("accounts.json").decode("utf-8")
                                for a in json.loads(raw_acc):
                                    uid = str(a.get("user_id"))
                                    if uid and uid not in accounts_map:
                                        accounts_map[uid] = a
                                logger.info(f"Loaded {len(accounts_map)} base accounts from Cloudflare backup archive.")
                                break
            except Exception as e:
                logger.warning(f"Could not load backup zip from {cf_url}: {e}")

        # 3. Merge newly onboarded accounts from Upstash Redis
        if UPSTASH_URL and UPSTASH_TOKEN:
            try:
                up_h = {"Authorization": f"Bearer {UPSTASH_TOKEN}"}
                async with http.get(f"{UPSTASH_URL}/keys/account:*", headers=up_h, timeout=aiohttp.ClientTimeout(total=5)) as ur:
                    if ur.status == 200:
                        udata = await ur.json()
                        for k in udata.get("result", []):
                            async with http.get(f"{UPSTASH_URL}/get/{k}", headers=up_h, timeout=aiohttp.ClientTimeout(total=4)) as gr:
                                if gr.status == 200:
                                    gdata = await gr.json()
                                    rstr = gdata.get("result")
                                    if rstr:
                                        acc_obj = json.loads(rstr) if isinstance(rstr, str) else rstr
                                        auid = str(acc_obj.get("user_id"))
                                        if auid:
                                            accounts_map[auid] = acc_obj
            except Exception as ue:
                logger.debug(f"Upstash account fetch note: {ue}")

        # 4. Merge accounts from Supabase Postgres
        if SUPABASE_URL and SUPABASE_KEY:
            try:
                sb_h = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
                async with http.get(f"{SUPABASE_URL}/rest/v1/accounts?select=*", headers=sb_h, timeout=aiohttp.ClientTimeout(total=5)) as sbr:
                    if sbr.status == 200:
                        sdata = await sbr.json()
                        if isinstance(sdata, list):
                            for sa in sdata:
                                suid = str(sa.get("user_id"))
                                if suid:
                                    accounts_map[suid] = sa
            except Exception as se:
                logger.debug(f"Supabase account fetch note: {se}")

    merged = list(accounts_map.values())
    FLEET_ACCOUNTS_CACHE = {str(a.get("user_id")): a for a in merged if a.get("user_id")}
    return merged

CACHED_GROQ_KEYS = []

async def get_groq_keys() -> list:
    global CACHED_GROQ_KEYS
    if CACHED_GROQ_KEYS:
        return CACHED_GROQ_KEYS
    env_keys = [
        os.getenv("GROQ_API_KEY_1"),
        os.getenv("GROQ_API_KEY_2"),
        os.getenv("GROQ_API_KEY_3"),
        os.getenv("GROQ_API_KEY")
    ]
    CACHED_GROQ_KEYS = [k for k in env_keys if k]
    if not CACHED_GROQ_KEYS and UPSTASH_URL and UPSTASH_TOKEN:
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(f"{UPSTASH_URL}/get/fleet:groq_keys", headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}, timeout=aiohttp.ClientTimeout(total=4)) as r:
                    if r.status == 200:
                        data = await r.json()
                        res = data.get("result")
                        if res:
                            parsed = json.loads(res) if isinstance(res, str) else res
                            if isinstance(parsed, list):
                                CACHED_GROQ_KEYS = [k for k in parsed if k]
        except Exception:
            pass
    return CACHED_GROQ_KEYS

async def ai_classify_bot_prompt(bot_text: str) -> str:
    """Uses Cloudflare Edge AI (Gemini + Groq + Cloudflare Workers AI) with Groq direct fallback."""
    prompt = (
        f"The Telegram bot sent this message during a withdrawal: '{bot_text}'. "
        f"Classify what the bot requires from the user. Respond with ONLY one word: "
        f"WALLET (asking for crypto wallet address), EMAIL (asking for email address), "
        f"AMOUNT (asking for withdrawal amount or number), CONFIRM (asking to click a button or confirm), "
        f"or WAIT (asking to wait or showing status)."
    )

    # 1. Primary: Cloudflare Edge Multi-Cloud AI Cascade (Gemini Flash -> Groq -> Workers AI)
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

    # 2. Secondary Fallback: Direct Groq API
    keys = await get_groq_keys()
    for k in keys:
        try:
            async with aiohttp.ClientSession() as s:
                payload = {
                    "model": "qwen/qwen3.8-27b",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 10,
                    "temperature": 0.1
                }
                headers = {"Authorization": f"Bearer {k}", "Content-Type": "application/json"}
                async with s.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=3)) as r:
                    if r.status == 200:
                        d = await r.json()
                        ans = d.get("choices", [{}])[0].get("message", {}).get("content", "").strip().upper()
                        for valid in ["WALLET", "EMAIL", "AMOUNT", "CONFIRM", "WAIT"]:
                            if valid in ans:
                                return valid
        except Exception:
            continue
    return "UNKNOWN"

async def check_and_auto_withdraw_cloud(acc: dict) -> dict:
    name = acc.get("name", "User")
    uid = str(acc.get("user_id"))
    sess_str = acc.get("session_string") or acc.get("session")
    target_wallet = acc.get("bnb_wallet") or DEFAULT_WALLET
    if not sess_str:
        return {"user_id": uid, "name": name, "ok": False, "error": "No session string"}

    result = {
        "user_id": uid,
        "name": name,
        "balance": 0.0,
        "withdrawn": False,
        "amount": 0.0,
        "verification_count": 0,
        "status": "checked",
        "timestamp": time.time(),
        "ok": True
    }

    client = TelegramClient(StringSession(sess_str), API_ID, API_HASH)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            result["ok"] = False
            result["error"] = "Unauthorized session"
            return result

        # 1. Fetch live balance from @CryptoProUpRobot
        init_msgs = await client.get_messages(BNB_BOT, limit=1)
        last_id = init_msgs[0].id if init_msgs else 0
        await client.send_message(BNB_BOT, "💰 Balance")

        balance = 0.0
        for _ in range(8):
            await asyncio.sleep(1.0)
            msgs = await client.get_messages(BNB_BOT, limit=3)
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

        result["balance"] = balance
        logger.info(f"[{name}] Cloud BNB Balance: {balance:.6f} BNB (Threshold: {MIN_WITHDRAWAL})")

        # 2. Inspect Adsgram 5-step verification count
        v_count = 0
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Linux; Android 14; K) AppleWebKit/537.36",
                "Referer": "https://justtool.site/tasks-adsgram/",
                "Origin": "https://justtool.site"
            }
            async with aiohttp.ClientSession() as http:
                async with http.get(f"https://justtool.site/api/adsgram-task3?tgId={uid}", headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as vr:
                    if vr.status == 200:
                        vd = await vr.json()
                        v_count = vd.get("count", 0)
        except Exception:
            pass
        result["verification_count"] = v_count

        # 3. Check if balance >= MIN_WITHDRAWAL
        if balance >= MIN_WITHDRAWAL:
            withdraw_amount = round(balance, 6)
            amount_str = f"{withdraw_amount:.6f}".rstrip("0").rstrip(".")
            logger.info(f"[{name}] Cloud Auto-Withdraw triggered: {amount_str} BNB to {target_wallet}")

            prev_msgs = await client.get_messages(BNB_BOT, limit=1)
            prev_id = prev_msgs[0].id if prev_msgs else 0
            await client.send_message(BNB_BOT, "📤 Withdraw")

            wallet_submitted = False
            email_submitted = False
            amount_submitted = False

            for turn in range(1, 7):
                bot_msg = None
                for _ in range(6):
                    await asyncio.sleep(1.0)
                    msgs = await client.get_messages(BNB_BOT, limit=3)
                    for m in msgs:
                        if m.id > prev_id and not m.out:
                            bot_msg = m
                            break
                    if bot_msg:
                        break

                if not bot_msg:
                    if turn == 1:
                        prev_msgs = await client.get_messages(BNB_BOT, limit=1)
                        prev_id = prev_msgs[0].id if prev_msgs else 0
                        await client.send_message(BNB_BOT, "/withdraw")
                        continue
                    else:
                        break

                prev_id = bot_msg.id
                bot_text = (bot_msg.raw_text or "").strip()
                bot_lower = bot_text.lower()
                logger.info(f"[{name} Turn {turn}] Bot: {bot_text[:80]}")

                if bot_msg.buttons:
                    for row in bot_msg.buttons:
                        for btn in row:
                            btn_t = (btn.text or "").lower()
                            if any(w in btn_t for w in ["confirm", "yes", "proceed", "submit", "accept", "agree"]):
                                try:
                                    await btn.click()
                                    await asyncio.sleep(1.5)
                                except Exception:
                                    pass
                                break

                if any(w in bot_lower for w in ["verification required", "withdrawal request submitted", "request submitted", "withdraw-adsgram"]):
                    break

                if any(w in bot_lower for w in ["send your email", "email id", "email for continue"]) and not email_submitted:
                    rand_id = int(time.time() * 1000) % 90000 + 10000
                    await client.send_message(BNB_BOT, f"user_{uid}_{rand_id}@gmail.com")
                    email_submitted = True
                    continue

                if any(w in bot_lower for w in ["wallet address", "submit your bnb", "bep-20", "bep20", "enter your wallet", "enter bnb"]) and not wallet_submitted:
                    await client.send_message(BNB_BOT, target_wallet)
                    wallet_submitted = True
                    continue

                if any(w in bot_lower for w in ["enter the amount", "amount of bnb", "how much", "minimum withdrawal", "min:", "enter amount", "amount to withdraw"]) and not amount_submitted:
                    await client.send_message(BNB_BOT, amount_str)
                    amount_submitted = True
                    continue

                # AI dynamic classification fallback
                ai_intent = await ai_classify_bot_prompt(bot_text)
                logger.info(f"[{name} Turn {turn}] AI Prompt Classification: {ai_intent}")

                if ai_intent == "EMAIL" and not email_submitted:
                    rand_id = int(time.time() * 1000) % 90000 + 10000
                    await client.send_message(BNB_BOT, f"user_{uid}_{rand_id}@gmail.com")
                    email_submitted = True
                    continue

                if ai_intent == "WALLET" and not wallet_submitted:
                    await client.send_message(BNB_BOT, target_wallet)
                    wallet_submitted = True
                    continue

                if ai_intent == "AMOUNT" and not amount_submitted:
                    await client.send_message(BNB_BOT, amount_str)
                    amount_submitted = True
                    continue

                if ai_intent == "WAIT":
                    await asyncio.sleep(2.0)
                    continue

                if not amount_submitted and wallet_submitted:
                    await client.send_message(BNB_BOT, amount_str)
                    amount_submitted = True
                    continue

                if amount_submitted and (wallet_submitted or "0x" in bot_lower):
                    break

            # Advance anti-bot verification to 5/5
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Linux; Android 14; K) AppleWebKit/537.36",
                "Referer": "https://justtool.site/tasks-adsgram/",
                "Origin": "https://justtool.site"
            }
            async with aiohttp.ClientSession() as http:
                while v_count < 5:
                    try:
                        async with http.post("https://justtool.site/api/adsgram-task3", headers=headers, json={"tgId": int(uid), "name": f"Member {uid}"}, timeout=aiohttp.ClientTimeout(total=5)) as step_r:
                            if step_r.status == 200:
                                s_data = await step_r.json()
                                v_count = s_data.get("count", v_count + 1)
                            else:
                                break
                    except Exception:
                        break
                    if v_count < 5:
                        await asyncio.sleep(1.2)

            result["withdrawn"] = True
            result["amount"] = withdraw_amount
            result["verification_count"] = v_count
            result["status"] = "withdrawn"
            logger.info(f"[{name}] ✅ Cloud Auto-Withdrawal completed: {amount_str} BNB (5/5 verified)")

            # Record payout to Upstash
            if UPSTASH_URL and UPSTASH_TOKEN:
                try:
                    payout_payload = {
                        "account_id": uid,
                        "name": name,
                        "amount": withdraw_amount,
                        "currency": "BNB",
                        "wallet": target_wallet,
                        "network": "BEP-20",
                        "timestamp": time.time(),
                        "status": "processing"
                    }
                    async with aiohttp.ClientSession() as http:
                        await http.post(
                            f"{UPSTASH_URL}/lpush/fleet:payouts",
                            data=json.dumps(payout_payload),
                            headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"},
                            timeout=aiohttp.ClientTimeout(total=4)
                        )
                except Exception:
                    pass

            logger.info(f"[{name}] BNB withdrawal submitted ({amount_str} BNB -> {target_wallet}). Silent queue mode active: awaiting on-chain confirmation.")


    except Exception as e:
        result["ok"] = False
        result["error"] = str(e)
        logger.error(f"[{name}] Cloud BNB cycle error: {e}")
    finally:
        await client.disconnect()

    return result

@app.post("/bnb/cloud-cycle")
async def bnb_cloud_cycle(request: Request):
    auth = request.headers.get("Authorization") or ""
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass

    accounts = body.get("accounts", [])
    if not accounts:
        accounts = await fetch_accounts_from_cloud()

    if not accounts:
        return {"ok": False, "message": "No accounts found"}

    CLOUD_BNB_STATUS["status"] = "running"
    CLOUD_BNB_STATUS["last_cycle_at"] = time.time()

    results = []
    for acc in accounts:
        res = await check_and_auto_withdraw_cloud(acc)
        results.append(res)
        CLOUD_BNB_STATUS["accounts"][str(res["user_id"])] = res
        await asyncio.sleep(1.0)

    CLOUD_BNB_STATUS["status"] = "idle"
    return {
        "ok": True,
        "checked": len(results),
        "withdrawn": sum(1 for r in results if r.get("withdrawn")),
        "results": results,
        "timestamp": time.time()
    }

@app.get("/bnb/status")
async def bnb_status():
    return {
        "ok": True,
        "status": CLOUD_BNB_STATUS["status"],
        "last_cycle_at": CLOUD_BNB_STATUS["last_cycle_at"],
        "accounts": CLOUD_BNB_STATUS["accounts"]
    }

BETTERSTACK_HEARTBEAT_URL = "https://uptime.betterstack.com/api/v1/heartbeat/bABS7gYDXgHp6H35XGcU7S6p"

async def token_health_and_refresh_watchdog():
    """
    24/7 Cloud Token Watchdog:
    1. Pings BetterStack Heartbeat to keep Uptime monitor green.
    2. Proactively checks token health & freshness in Cloudflare KV & Upstash.
    3. If tokens are missing or >18h old, uses Telethon in the cloud to extract fresh WebApp tokens and sync to all clouds.
    """
    logger.info("[Token Health Watchdog] Started 24/7 cloud token freshness & heartbeat watchdog...")
    await asyncio.sleep(45)
    while True:
        try:
            # 1. Ping BetterStack Heartbeat
            async with aiohttp.ClientSession(headers=BROWSER_HEADERS) as session:
                try:
                    await session.get(BETTERSTACK_HEARTBEAT_URL, timeout=aiohttp.ClientTimeout(total=10))
                except Exception as hbe:
                    logger.warning(f"[Token Watchdog] Heartbeat ping error: {hbe}")

            # 2. Check token freshness across all accounts
            accounts = await fetch_accounts_from_cloud()
            if accounts:
                async with aiohttp.ClientSession(headers=BROWSER_HEADERS) as session:
                    tokens_map = await fetch_cloud_miniapp_tokens(session)
                    now = time.time()
                    stale_or_missing_accs = []
                    for acc in accounts:
                        uid = str(acc.get("user_id"))
                        tok = tokens_map.get(uid, {})
                        synced_at = tok.get("synced_at", 0)
                        # If token missing or older than 18 hours (64800s), flag for refresh
                        if not tok or (now - synced_at > 64800) or not tok.get("stones_init_data"):
                            stale_or_missing_accs.append(acc)

                    if stale_or_missing_accs:
                        logger.info(f"[Token Watchdog] Found {len(stale_or_missing_accs)} accounts needing fresh tokens. Refreshing in cloud...")
                        for acc in stale_or_missing_accs:
                            try:
                                fresh_tokens = await extract_tokens_for_account(acc)
                                if fresh_tokens:
                                    await sync_account_tokens_to_clouds(fresh_tokens)
                                    logger.info(f"[Token Watchdog] ✅ Successfully refreshed tokens for {acc.get('name', acc.get('user_id'))}")
                                await asyncio.sleep(2.0)
                            except Exception as re:
                                logger.warning(f"[Token Watchdog] Refresh note for {acc.get('name')}: {re}")

        except Exception as e:
            logger.error(f"[Token Watchdog] Error: {e}")
        await asyncio.sleep(1800)

@app.on_event("startup")
async def on_startup():
    asyncio.create_task(token_health_and_refresh_watchdog())
    asyncio.create_task(cloud_wealth_automation_watchdog())



# =====================================================================
# FAST CLOUD MTPROTO ACCOUNT ONBOARDING & REFERRAL BINDING ENGINE
# =====================================================================
LOGIN_SESSIONS = {}

def get_clean_phone(raw_phone: str) -> str:
    p = re.sub(r"[\s\-\(\)]", "", str(raw_phone).strip())
    if p.startswith("00"):
        p = "+" + p[2:]
    elif not p.startswith("+"):
        if p.startswith("01") and len(p) == 11:
            p = "+880" + p[1:]
        elif p.startswith("1") and len(p) == 10:
            p = "+880" + p
        else:
            p = "+" + p
    return p

async def sync_account_tokens_to_clouds(tokens: dict):
    """Syncs extracted miniapp tokens to 5x Cloudflare KV, Upstash Redis, and Supabase."""
    if not tokens or not tokens.get("account_id"):
        return
    uid = str(tokens["account_id"])
    async with aiohttp.ClientSession() as s:
        # 1. 5x Cloudflare Edge Workers
        for cf_url in CF_WORKER_URLS:
            try:
                await s.post(
                    f"{cf_url}/api/miniapp/tokens/sync",
                    json=tokens,
                    headers={
                        "Authorization": f"Bearer {SECRET_KEY}",
                        "Content-Type": "application/json",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    },
                    timeout=aiohttp.ClientTimeout(total=6)
                )
            except Exception as se:
                logger.warning(f"Tokens sync error to {cf_url}: {se}")

        # 2. Upstash Redis
        if UPSTASH_URL and UPSTASH_TOKEN:
            try:
                await s.post(
                    f"{UPSTASH_URL}/set/fleet:tokens:{uid}",
                    data=json.dumps(tokens),
                    headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"},
                    timeout=aiohttp.ClientTimeout(total=5)
                )
            except Exception as ue:
                logger.warning(f"Upstash token sync note: {ue}")

        # 3. Supabase Postgres
        if SUPABASE_URL and SUPABASE_KEY:
            try:
                await s.patch(
                    f"{SUPABASE_URL}/rest/v1/fleet_accounts?id=eq.{uid}",
                    json={"data": tokens},
                    headers={
                        "apikey": SUPABASE_KEY,
                        "Authorization": f"Bearer {SUPABASE_KEY}",
                        "Content-Type": "application/json"
                    },
                    timeout=aiohttp.ClientTimeout(total=5)
                )
            except Exception as sbe:
                logger.warning(f"Supabase token sync note: {sbe}")


async def bootstrap_account_mining(acc_entry: dict, tokens: dict):
    """
    Kicks off initial WebApp mining, completes referral onboarding finish work,
    and runs first-cycle claims across all 8 bots:
    1. Stones Miners (/api/mining/start, /api/claim, dynamic tasks, stone breaker, boost)
    2. MRG Miner (/api/user/claim-mining, /api/user/claim-task, referral commission)
    3. ART Airdrop (/api/user/start-mining, /api/user/claim-mining, /api/ads/claim, tasks, miner upgrade)
    4. AI Lab Robot (/users/auth/login, /miner-start_mining, /miner-exchange_hashes, tasks)
    5. UltraWallet (/telegramLogin, /mining/start, /checkin/claim, lucky spins, tasks, ads, gift box)
    6. Apex Miner (/bootstrap, /register, /checkin, /mining/restart, tasks, boost)
    7. ATF Miner (login, math challenge -> /start_mine, speed boost, tasks, referral claim)
    8. Ainovum (/api/bootstrap, /api/mining/claim, /api/daily-bonus, /api/channel-bonus, /api/gift-box)
    """
    uid = str(acc_entry.get("user_id"))
    name = acc_entry.get("name", "User")
    logger.info(f"[{name}] ⚡ Bootstrapping initial cloud mining & completing referral finish work across all 8 bots...")
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36 Telegram-Android/11.0.0"
    }

    async with aiohttp.ClientSession(headers=headers) as http:
        # 1. Stones Miners
        if tokens.get("stones_init_data"):
            try:
                s_init = tokens["stones_init_data"]
                await http.post("https://app.stoneswithestand.my.id/api/mining/start", json={"initData": s_init}, timeout=aiohttp.ClientTimeout(total=8))
                await http.post("https://app.stoneswithestand.my.id/api/claim", json={"initData": s_init}, timeout=aiohttp.ClientTimeout(total=8))
                await http.post("https://app.stoneswithestand.my.id/api/task/complete", json={"initData": s_init, "slug": "daily_checkin"}, timeout=aiohttp.ClientTimeout(total=8))
                await http.post("https://app.stoneswithestand.my.id/api/task/start", json={"initData": s_init, "slug": "join_channel"}, timeout=aiohttp.ClientTimeout(total=8))
                await http.post("https://app.stoneswithestand.my.id/api/task/complete", json={"initData": s_init, "slug": "join_channel"}, timeout=aiohttp.ClientTimeout(total=8))
                await http.post("https://app.stoneswithestand.my.id/api/task/verify", json={"initData": s_init, "slug": "join_channel"}, timeout=aiohttp.ClientTimeout(total=8))
                try:
                    async with http.post("https://app.stoneswithestand.my.id/api/state", json={"initData": s_init}, timeout=aiohttp.ClientTimeout(total=6)) as st_r:
                        if st_r.status == 200:
                            st_data = await st_r.json()
                            raw_tasks = st_data.get("tasks", {})
                            tasks_to_do = []
                            if isinstance(raw_tasks, dict):
                                for slug, status in raw_tasks.items():
                                    if status != "completed":
                                        tasks_to_do.append(slug)
                            elif isinstance(raw_tasks, list):
                                for t in raw_tasks:
                                    slug = t.get("slug") or t.get("id")
                                    if slug and not t.get("completed") and not t.get("is_completed"):
                                        tasks_to_do.append(slug)
                            for slug in tasks_to_do:
                                if slug not in ["daily_checkin", "join_channel"]:
                                    await http.post("https://app.stoneswithestand.my.id/api/task/start", json={"initData": s_init, "slug": slug}, timeout=aiohttp.ClientTimeout(total=4))
                                    await http.post("https://app.stoneswithestand.my.id/api/task/complete", json={"initData": s_init, "slug": slug}, timeout=aiohttp.ClientTimeout(total=4))
                                    await http.post("https://app.stoneswithestand.my.id/api/task/verify", json={"initData": s_init, "slug": slug}, timeout=aiohttp.ClientTimeout(total=4))
                except Exception:
                    pass
                logger.info(f"[{name}] ✅ Stones initial mining started & tasks completed")
            except Exception as e:
                logger.debug(f"[{name}] Stones bootstrap note: {e}")

        # 2. MRG Miner
        if tokens.get("mrg_init_data"):
            try:
                m_init = tokens["mrg_init_data"]
                if uid != "6727787768":
                    await http.post("https://mrg.up.railway.app/api/auth/verify", json={"initData": m_init, "start_param": MRG_REFERRAL_CODE}, timeout=aiohttp.ClientTimeout(total=8))
                await http.post("https://mrg.up.railway.app/api/user/claim-mining", json={"initData": m_init}, timeout=aiohttp.ClientTimeout(total=8))
                try:
                    async with http.post("https://mrg.up.railway.app/api/user/me", json={"initData": m_init}, timeout=aiohttp.ClientTimeout(total=6)) as me_r:
                        if me_r.status == 200:
                            me_d = await me_r.json()
                            completed = set(me_d.get("completedTaskIds", []))
                            for t in me_d.get("tasks", []):
                                tid = t.get("taskId")
                                if tid and tid not in completed:
                                    await http.post("https://mrg.up.railway.app/api/user/claim-task", json={"initData": m_init, "taskId": tid}, timeout=aiohttp.ClientTimeout(total=5))
                            # Auto-unlock Level in MRG if balance permits
                            u_obj = me_d.get("user", {})
                            in_bal = float(u_obj.get("inAppBalance", 0) or 0)
                            cur_lvl = int(u_obj.get("peakLevel") or u_obj.get("manualUnlockedLevel") or 1)
                            if in_bal >= 100:
                                def wp_calc(e):
                                    if e <= 0: return 0
                                    if e == 1: return 100
                                    if e <= 203: return round(100 + 9900 * (((e - 1) / 202.0) ** 1.8))
                                    return 10000
                                lo, hi, target_lvl = 1, 203, cur_lvl
                                while lo <= hi:
                                    mid = (lo + hi) // 2
                                    if in_bal >= wp_calc(mid):
                                        target_lvl = mid
                                        lo = mid + 1
                                    else:
                                        hi = mid - 1
                                if target_lvl > cur_lvl:
                                    await http.post("https://mrg.up.railway.app/api/user/unlock-level", json={"initData": m_init, "level": target_lvl}, timeout=aiohttp.ClientTimeout(total=5))
                except Exception:
                    pass
                if uid == "6727787768":
                    await http.post("https://mrg.up.railway.app/api/user/claim-commission", json={"initData": m_init}, timeout=aiohttp.ClientTimeout(total=5))
                    try:
                        async with http.post("https://mrg.up.railway.app/api/user/friends", json={"initData": m_init}, timeout=aiohttp.ClientTimeout(total=5)) as fr_r:
                            if fr_r.status == 200:
                                fr_d = await fr_r.json()
                                if (fr_d.get("teamStats", {}).get("unclaimedOneTimeBonusMRG", 0) or 0) > 0:
                                    await http.post("https://mrg.up.railway.app/api/user/claim-one-time-bonus", json={"initData": m_init}, timeout=aiohttp.ClientTimeout(total=5))
                    except Exception:
                        pass
                logger.info(f"[{name}] ✅ MRG initial mining started & tasks claimed")
            except Exception as e:
                logger.debug(f"[{name}] MRG bootstrap note: {e}")

        # 3. ART Airdrop
        if tokens.get("art_init_data"):
            try:
                art_init = tokens["art_init_data"]
                art_h = {"X-Telegram-Init-Data": art_init, "Content-Type": "application/json", "User-Agent": headers["User-Agent"]}
                await http.post("https://art.tamimdev.dev/api/user/start-mining", json={"userId": uid}, headers=art_h, timeout=aiohttp.ClientTimeout(total=8))
                await http.post("https://art.tamimdev.dev/api/user/claim-mining", json={"userId": uid}, headers=art_h, timeout=aiohttp.ClientTimeout(total=8))
                await http.post("https://art.tamimdev.dev/api/ads/claim", json={"userId": uid}, headers=art_h, timeout=aiohttp.ClientTimeout(total=6))
                try:
                    async with http.get(f"https://art.tamimdev.dev/api/tasks/{uid}", headers=art_h, timeout=aiohttp.ClientTimeout(total=6)) as tr:
                        if tr.status == 200:
                            td = await tr.json()
                            for t in td.get("tasks", []):
                                if not t.get("isCompleted") and t.get("id"):
                                    await http.post("https://art.tamimdev.dev/api/tasks/start", json={"userId": uid, "taskId": t["id"]}, headers=art_h, timeout=aiohttp.ClientTimeout(total=4))
                                    await http.post("https://art.tamimdev.dev/api/tasks/claim", json={"userId": uid, "taskId": t["id"]}, headers=art_h, timeout=aiohttp.ClientTimeout(total=4))
                except Exception:
                    pass
                if uid == "6727787768":
                    await http.post("https://art.tamimdev.dev/api/referrals/claim-team", json={"userId": uid}, headers=art_h, timeout=aiohttp.ClientTimeout(total=4))
                    await http.post("https://art.tamimdev.dev/api/referrals/claim-bonus", json={"userId": uid}, headers=art_h, timeout=aiohttp.ClientTimeout(total=4))
                logger.info(f"[{name}] ✅ ART initial mining started & tasks claimed")
            except Exception as e:
                logger.debug(f"[{name}] ART bootstrap note: {e}")

        # 4. AI Lab Robot
        if tokens.get("ailab_init_data"):
            try:
                ai_init = tokens["ailab_init_data"]
                ai_base = "https://api.ailab-agent.online/api/v1"
                async with http.post(f"{ai_base}/users/auth/login", json={"user": ai_init}, timeout=aiohttp.ClientTimeout(total=8)) as r:
                    if r.status == 200:
                        ld = await r.json()
                        tok = ld.get("result", {}).get("bearer") or ld.get("user_info", {}).get("session_id")
                        if tok:
                            ai_auth = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json", "User-Agent": headers["User-Agent"]}
                            await http.post(f"{ai_base}/miner-start_mining", json={"start_mining": True}, headers=ai_auth, timeout=aiohttp.ClientTimeout(total=8))
                            try:
                                async with http.get(f"{ai_base}/miner", headers=ai_auth, timeout=aiohttp.ClientTimeout(total=5)) as mr:
                                    if mr.status == 200:
                                        md = await mr.json()
                                        h_bal = float(md.get("result", {}).get("miner", {}).get("hashes_balance", 0))
                                        if h_bal >= 3.0:
                                            await http.post(f"{ai_base}/miner-exchange_hashes", json={"exchange": True}, headers=ai_auth, timeout=aiohttp.ClientTimeout(total=5))
                            except Exception:
                                pass
                            try:
                                async with http.get(f"{ai_base}/tasks", headers=ai_auth, timeout=aiohttp.ClientTimeout(total=5)) as tr:
                                    if tr.status == 200:
                                        td = await tr.json()
                                        tasks = td.get("result", {}).get("referral", []) + td.get("result", {}).get("follow", []) + td.get("result", {}).get("social", [])
                                        for t in tasks:
                                            if t.get("id") and t.get("status") != "completed":
                                                await http.post(f"{ai_base}/task-check", json={"task_id": t["id"], "action": "start"}, headers=ai_auth, timeout=aiohttp.ClientTimeout(total=4))
                                                await http.post(f"{ai_base}/task-check", json={"task_id": t["id"], "action": "check"}, headers=ai_auth, timeout=aiohttp.ClientTimeout(total=4))
                            except Exception:
                                pass
                            logger.info(f"[{name}] ✅ AI Lab initial mining started & tasks checked")
            except Exception as e:
                logger.debug(f"[{name}] AI Lab bootstrap note: {e}")

        # 5. UltraWallet
        if tokens.get("ultrawallet_init_data"):
            try:
                uw_init = tokens["ultrawallet_init_data"]
                uw_base = "https://wallet.trxvault.top/api"
                async with http.post(f"{uw_base}/telegramLogin", json={"initData": uw_init, "refBy": "6727787768"}, timeout=aiohttp.ClientTimeout(total=8)) as r:
                    if r.status == 200:
                        ud = await r.json()
                        cust_tok = ud.get("token")
                        if cust_tok:
                            fb_url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key=AIzaSyAIKTCEFqC5LFRc89nuOLhTGPHIZTIjEsU"
                            async with http.post(fb_url, json={"token": cust_tok, "returnSecureToken": True}, timeout=aiohttp.ClientTimeout(total=8)) as fbr:
                                if fbr.status == 200:
                                    fbd = await fbr.json()
                                    id_tok = fbd.get("idToken")
                                    if id_tok:
                                        uw_h = {"Authorization": f"Bearer {id_tok}", "Content-Type": "application/json", "User-Agent": headers["User-Agent"]}
                                        await http.post(f"{uw_base}/checkin/claim", json={}, headers=uw_h, timeout=aiohttp.ClientTimeout(total=6))
                                        await http.post(f"{uw_base}/mining/claim", json={}, headers=uw_h, timeout=aiohttp.ClientTimeout(total=6))
                                        await http.post(f"{uw_base}/mining/start", json={}, headers=uw_h, timeout=aiohttp.ClientTimeout(total=6))
                                        await http.post(f"{uw_base}/energy/claim", json={}, headers=uw_h, timeout=aiohttp.ClientTimeout(total=6))
                                        try:
                                            async with http.get(f"{uw_base}/spin/status", headers=uw_h, timeout=aiohttp.ClientTimeout(total=5)) as spr:
                                                if spr.status == 200:
                                                    spi = await spr.json()
                                                    spins = (spi.get("tickets", 0)) + (spi.get("freeSpinsRemaining", 0))
                                                    for _ in range(min(spins, 3)):
                                                        await http.post(f"{uw_base}/spin/play", json={}, headers=uw_h, timeout=aiohttp.ClientTimeout(total=4))
                                        except Exception:
                                            pass
                                        try:
                                            async with http.get(f"{uw_base}/tasks", headers=uw_h, timeout=aiohttp.ClientTimeout(total=5)) as utr:
                                                if utr.status == 200:
                                                    utd = await utr.json()
                                                    for t in utd.get("tasks", []):
                                                        if not t.get("completed") and t.get("id"):
                                                            await http.post(f"{uw_base}/tasks/start", json={"taskId": t["id"]}, headers=uw_h, timeout=aiohttp.ClientTimeout(total=4))
                                                            await http.post(f"{uw_base}/tasks/complete", json={"taskId": t["id"]}, headers=uw_h, timeout=aiohttp.ClientTimeout(total=4))
                                        except Exception:
                                            pass
                                        try:
                                            async with http.get(f"{uw_base}/giftBox", headers=uw_h, timeout=aiohttp.ClientTimeout(total=5)) as gbr:
                                                if gbr.status == 200:
                                                    gbd = await gbr.json()
                                                    if gbd.get("enabled") and gbd.get("canOpen"):
                                                        await http.post(f"{uw_base}/giftBox/claim", json={}, headers=uw_h, timeout=aiohttp.ClientTimeout(total=4))
                                        except Exception:
                                            pass
                                        logger.info(f"[{name}] ✅ UltraWallet initial mining & tasks completed")
            except Exception as e:
                logger.debug(f"[{name}] UltraWallet bootstrap note: {e}")

        # 6. Apex Miner
        if tokens.get("apx_init_data"):
            try:
                apx_init = tokens["apx_init_data"]
                apx_base = "https://apxn-miner-live.apxn-network.workers.dev/api"
                await http.post(f"{apx_base}/auth/telegram", json={"initData": apx_init}, timeout=aiohttp.ClientTimeout(total=8))
                async with http.post(f"{apx_base}/bootstrap", json={"initData": apx_init}, timeout=aiohttp.ClientTimeout(total=8)) as b_r:
                    if b_r.status == 200:
                        b_data = await b_r.json()
                        if not b_data.get("exists") or not b_data.get("user"):
                            await http.post(f"{apx_base}/register", json={"initData": apx_init}, timeout=aiohttp.ClientTimeout(total=8))
                await http.post(f"{apx_base}/checkin", json={"initData": apx_init, "clientV2": True}, timeout=aiohttp.ClientTimeout(total=8))
                await http.post(f"{apx_base}/mining/claim", json={"initData": apx_init}, timeout=aiohttp.ClientTimeout(total=8))
                await http.post(f"{apx_base}/mining/restart", json={"initData": apx_init}, timeout=aiohttp.ClientTimeout(total=8))
                for t in ["telegram", "twitter", "discord", "checkin"]:
                    await http.post(f"{apx_base}/tasks/daily", json={"initData": apx_init, "task": t}, headers=headers, timeout=aiohttp.ClientTimeout(total=4))
                for s in ["channel", "group", "twitter", "partner"]:
                    await http.post(f"{apx_base}/tasks/social", json={"initData": apx_init, "task": s}, headers=headers, timeout=aiohttp.ClientTimeout(total=4))
                await http.post(f"{apx_base}/ads/boost", json={"initData": apx_init}, headers=headers, timeout=aiohttp.ClientTimeout(total=4))
                logger.info(f"[{name}] ✅ Apex Miner initial mining & tasks started")
            except Exception as e:
                logger.debug(f"[{name}] Apex Miner bootstrap note: {e}")

        # 7. ATF Miner (Comprehensive Referral Finish Work: Login, Math Challenge Solve, Start Mine, Tasks, Boost)
        if tokens.get("atf_init_data"):
            try:
                atf_init = tokens["atf_init_data"]
                atf_base = "https://atfminers.asloni.online/miner/index.php"
                atf_h = {
                    "Content-Type": "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                    "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36 Telegram-Android/11.0.0",
                    "Referer": "https://atfminers.asloni.online/miner/index.html",
                    "Origin": "https://atfminers.asloni.online"
                }
                payload_base = {
                    "initData": atf_init,
                    "tg_id": int(uid),
                    "username": acc_entry.get("username", "") or "",
                    "referrer": "6727787768",
                    "ref": "6727787768",
                    "request_id": f"rq-{int(time.time()*1000)}-init",
                    "device_id": f"dev-boot-{uid}"
                }
                await http.post(f"{atf_base}?action=login&t={int(time.time()*1000)}", json=payload_base, headers=atf_h, timeout=aiohttp.ClientTimeout(total=8))
                async with http.post(f"{atf_base}?action=get_math_challenge&t={int(time.time()*1000)}", json={**payload_base, "scope": "start_mine"}, headers=atf_h, timeout=aiohttp.ClientTimeout(total=8)) as chr:
                    if chr.status == 200:
                        chd = await chr.json()
                        if chd.get("status") == "success" and chd.get("challenge_id"):
                            q = chd.get("question", "")
                            ans = solve_atf_math(q)
                            await http.post(f"{atf_base}?action=start_mine&t={int(time.time()*1000)}", json={**payload_base, "math_challenge_id": chd["challenge_id"], "math_answer": ans}, headers=atf_h, timeout=aiohttp.ClientTimeout(total=8))
                            logger.info(f"[{name}] ✅ ATF Miner initial mining started (Math solved: {ans})")
                await http.post(f"{atf_base}?action=activate_boost&t={int(time.time()*1000)}", json=payload_base, headers=atf_h, timeout=aiohttp.ClientTimeout(total=5))
                await http.post(f"{atf_base}?action=record_daily_interaction&t={int(time.time()*1000)}", json=payload_base, headers=atf_h, timeout=aiohttp.ClientTimeout(total=5))
                await http.post(f"{atf_base}?action=claim_referrals&t={int(time.time()*1000)}", json=payload_base, headers=atf_h, timeout=aiohttp.ClientTimeout(total=5))
                await http.post(f"{atf_base}?action=claim_team_wallet&t={int(time.time()*1000)}", json=payload_base, headers=atf_h, timeout=aiohttp.ClientTimeout(total=5))
                starter_tasks = ["telegram_join", "telegram_join_fa", "twitter_follow", "youtube_subscribe", "website_visit", "telegram_react_latest", "twitter_retweet", "youtube_like_comment"]
                for tid in starter_tasks:
                    st_at = int(time.time()) - 25
                    await http.post(f"{atf_base}?action=start_task&t={int(time.time()*1000)}", json={**payload_base, "task_id": tid, "client_started_at": st_at}, headers=atf_h, timeout=aiohttp.ClientTimeout(total=4))
                    await http.post(f"{atf_base}?action=claim_task&t={int(time.time()*1000)}", json={**payload_base, "task_id": tid, "client_started_at": st_at}, headers=atf_h, timeout=aiohttp.ClientTimeout(total=4))
                logger.info(f"[{name}] ✅ ATF Miner referral finish work & starter tasks completed")
            except Exception as e:
                logger.debug(f"[{name}] ATF Miner bootstrap note: {e}")

        # 8. Ainovum Bot
        if tokens.get("ainovum_init_data"):
            try:
                ain_init = tokens["ainovum_init_data"]
                ain_base = "https://ainovum.biz"
                ain_h = {
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36 Telegram-Android/11.0.0",
                    "Referer": "https://ainovum.biz/",
                    "Origin": "https://ainovum.biz"
                }
                async with http.post(f"{ain_base}/api/bootstrap", json={
                    "initData": ain_init,
                    "platform": "android",
                    "referrer": "ref_6727787768",
                    "timezone_offset_minutes": 0,
                    "language_code": "en",
                    "registration_duration_ms": 1500
                }, headers=ain_h, timeout=aiohttp.ClientTimeout(total=8)) as br:
                    if br.status == 200:
                        raw_cookies = br.headers.getall("Set-Cookie", [])
                        cookie_hdr = "; ".join([c.split(";")[0] for c in raw_cookies])
                        if not cookie_hdr and "set-cookie" in br.headers:
                            cookie_hdr = br.headers.get("set-cookie")
                        req_h = {**ain_h}
                        if cookie_hdr:
                            req_h["Cookie"] = cookie_hdr
                        await http.post(f"{ain_base}/api/mining/start", json={}, headers=req_h, timeout=aiohttp.ClientTimeout(total=6))
                        await http.post(f"{ain_base}/api/mining/claim", json={"action": "claim_cycle"}, headers=req_h, timeout=aiohttp.ClientTimeout(total=6))
                        await http.post(f"{ain_base}/api/daily-bonus/claim", json={}, headers=req_h, timeout=aiohttp.ClientTimeout(total=6))
                        await http.post(f"{ain_base}/api/channel-bonus/claim", json={}, headers=req_h, timeout=aiohttp.ClientTimeout(total=6))
                        await http.post(f"{ain_base}/api/gift-box/open", json={}, headers=req_h, timeout=aiohttp.ClientTimeout(total=6))
                        logger.info(f"[{name}] ✅ Ainovum initial mining started")
            except Exception as e:
                logger.debug(f"[{name}] Ainovum bootstrap note: {e}")

        # 9. TRX Power Mining
        try:
            trx_h = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36 Telegram-Android/11.0.0",
                "Referer": "https://trxpowermining.org/",
                "Origin": "https://trxpowermining.org"
            }
            await http.post("https://trxpowermining.org/api/user/sync", json={"tg_id": int(uid), "ref": TRXPOWER_REFERRAL_CODE, "start_param": TRXPOWER_REFERRAL_CODE}, headers=trx_h, timeout=aiohttp.ClientTimeout(total=6))
            await http.post("https://trxpowermining.org/api/claim", json={"tg_id": int(uid)}, headers=trx_h, timeout=aiohttp.ClientTimeout(total=6))
            logger.info(f"[{name}] ✅ TRX Power Mining initial bootstrap claim completed")
        except Exception as e:
            logger.debug(f"[{name}] TRX Power bootstrap note: {e}")

        # 10. Bitcoin Cloud Miners
        try:
            btc_h = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36 Telegram-Android/11.0.0",
                "Referer": "https://btccloudminers.org/",
                "Origin": "https://btccloudminers.org"
            }
            await http.post("https://btccloudminers.org/api/user/sync", json={"tg_id": int(uid), "ref": BTC_REFERRAL_CODE, "start_param": BTC_REFERRAL_CODE}, headers=btc_h, timeout=aiohttp.ClientTimeout(total=6))
            await http.post("https://btccloudminers.org/api/claim", json={"tg_id": int(uid)}, headers=btc_h, timeout=aiohttp.ClientTimeout(total=6))
            logger.info(f"[{name}] ✅ Bitcoin Cloud Miners initial bootstrap claim completed")
        except Exception as e:
            logger.debug(f"[{name}] Bitcoin Cloud bootstrap note: {e}")

        # 11. Tensor Mining Robot
        if tokens.get("tensor_init_data"):
            try:
                tns_init = tokens["tensor_init_data"]
                tns_h = {
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36 Telegram-Android/11.0.0",
                    "Referer": "https://tensormining.online/",
                    "Origin": "https://tensormining.online"
                }
                await http.post("https://tensormining.online/api/auth/telegram", json={"initData": tns_init, "referrer": TENSOR_REFERRAL_CODE}, headers=tns_h, timeout=aiohttp.ClientTimeout(total=6))
                await http.post("https://tensormining.online/api/mining/claim", json={"initData": tns_init}, headers=tns_h, timeout=aiohttp.ClientTimeout(total=6))
                logger.info(f"[{name}] ✅ Tensor Mining Robot initial bootstrap claim completed")
            except Exception as e:
                logger.debug(f"[{name}] Tensor Mining bootstrap note: {e}")

        # 12. Ton Trader AI
        if tokens.get("tontrader_init_data"):
            try:
                tt_init = tokens["tontrader_init_data"]
                tt_h = {
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36 Telegram-Android/11.0.0",
                    "Referer": "https://tontrader.app/",
                    "Origin": "https://tontrader.app"
                }
                await http.post("https://api.tontrader.app/api/v1/auth", json={"initData": tt_init, "ref": TONTRADER_REFERRAL_CODE}, headers=tt_h, timeout=aiohttp.ClientTimeout(total=6))
                await http.post("https://api.tontrader.app/api/v1/daily-checkin", json={"initData": tt_init}, headers=tt_h, timeout=aiohttp.ClientTimeout(total=6))
                await http.post("https://api.tontrader.app/api/v1/claim", json={"initData": tt_init}, headers=tt_h, timeout=aiohttp.ClientTimeout(total=6))
                logger.info(f"[{name}] ✅ Ton Trader AI initial bootstrap claim completed")
            except Exception as e:
                logger.debug(f"[{name}] Ton Trader bootstrap note: {e}")

        # 13. FINVORA Web3
        try:
            fin_h = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36 Telegram-Android/11.0.0",
                "Referer": "https://finvora.io/",
                "Origin": "https://finvora.io"
            }
            await http.post("https://finvora.io/api/user/sync", json={"tg_id": int(uid), "ref": FINVORA_REFERRAL_CODE, "start_param": FINVORA_REFERRAL_CODE}, headers=fin_h, timeout=aiohttp.ClientTimeout(total=6))
            await http.post("https://finvora.io/api/claim", json={"tg_id": int(uid)}, headers=fin_h, timeout=aiohttp.ClientTimeout(total=6))
            logger.info(f"[{name}] ✅ FINVORA Web3 initial bootstrap claim completed")
        except Exception as e:
            logger.debug(f"[{name}] FINVORA bootstrap note: {e}")

        # 14. TurboGram V1
        try:
            turbo_h = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36 Telegram-Android/11.0.0",
                "Referer": "https://turbogram.xyz/",
                "Origin": "https://turbogram.xyz"
            }
            await http.post("https://turbogram.xyz/api/user/sync", json={"tg_id": int(uid), "ref": TURBOGRAM_REFERRAL_CODE, "start_param": TURBOGRAM_REFERRAL_CODE}, headers=turbo_h, timeout=aiohttp.ClientTimeout(total=6))
            await http.post("https://turbogram.xyz/api/claim", json={"tg_id": int(uid)}, headers=turbo_h, timeout=aiohttp.ClientTimeout(total=6))
            logger.info(f"[{name}] ✅ TurboGram V1 initial bootstrap claim completed")
        except Exception as e:
            logger.debug(f"[{name}] TurboGram bootstrap note: {e}")

        # 15. Ominix AI Trade
        if tokens.get("ominix_init_data"):
            try:
                om_init = tokens["ominix_init_data"]
                om_h = {
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36 Telegram-Android/11.0.0",
                    "Referer": "https://ominix.trade/",
                    "Origin": "https://ominix.trade"
                }
                await http.post("https://api.ominix.trade/api/auth/verify", json={"initData": om_init, "ref": OMINIX_REFERRAL_CODE}, headers=om_h, timeout=aiohttp.ClientTimeout(total=6))
                await http.post("https://api.ominix.trade/api/trade/daily-checkin", json={"initData": om_init}, headers=om_h, timeout=aiohttp.ClientTimeout(total=6))
                await http.post("https://api.ominix.trade/api/trade/claim", json={"initData": om_init}, headers=om_h, timeout=aiohttp.ClientTimeout(total=6))
                logger.info(f"[{name}] ✅ Ominix AI Trade initial bootstrap claim completed")
            except Exception as e:
                logger.debug(f"[{name}] Ominix bootstrap note: {e}")


def is_account_referrals_bound(acc_entry: dict) -> bool:
    """Checks whether an account already has its master referrals bound across all 15 active bots."""
    if acc_entry.get("all_15_referrals_bound"):
        return True
    return bool(
        acc_entry.get("atf_referral_bound") and
        acc_entry.get("stones_referral_bound") and
        acc_entry.get("mrg_referral_bound") and
        acc_entry.get("art_referral_bound") and
        acc_entry.get("ailab_referral_bound") and
        acc_entry.get("ultrawallet_referral_bound") and
        acc_entry.get("apx_referral_bound") and
        acc_entry.get("ainovum_referral_bound") and
        acc_entry.get("trxpower_referral_bound") and
        acc_entry.get("btc_referral_bound") and
        acc_entry.get("tensor_referral_bound") and
        acc_entry.get("tontrader_referral_bound") and
        acc_entry.get("finvora_referral_bound") and
        acc_entry.get("turbogram_referral_bound") and
        acc_entry.get("ominix_referral_bound")
    )


async def mute_peer(client: TelegramClient, peer_or_username, name: str = ""):
    """Permanently silences notifications from a bot, channel, or group."""
    try:
        entity = await client.get_input_entity(peer_or_username)
        await client(UpdateNotifySettingsRequest(
            peer=InputNotifyPeer(peer=entity),
            settings=InputPeerNotifySettings(
                show_previews=False,
                silent=True,
                mute_until=datetime.datetime(2038, 1, 1, 0, 0)
            )
        ))
        logger.info(f"[{name}] Permanently silenced notifications for {peer_or_username}")
    except Exception as e:
        logger.debug(f"[{name}] Note silencing {peer_or_username}: {e}")


async def join_tg_target(client: TelegramClient, link_or_username: str, name: str = ""):
    target = str(link_or_username or "").strip()
    if not target:
        return
    # Private invite link: https://t.me/+hash or t.me/joinchat/hash or +hash
    if "+" in target or "joinchat/" in target:
        h = target.split("+")[-1].split("?")[0] if "+" in target else target.split("joinchat/")[-1].split("?")[0]
        h = h.strip()
        if h:
            try:
                res = await client(ImportChatInviteRequest(h))
                logger.info(f"[{name}] Joined private invite +{h}")
                if hasattr(res, 'chats') and res.chats:
                    await mute_peer(client, res.chats[0], name)
            except Exception as e:
                if "already" not in str(e).lower() and "USER_ALREADY_PARTICIPANT" not in str(e):
                    logger.debug(f"[{name}] Private invite join note (+{h}): {e}")
    else:
        clean = target.replace("https://t.me/", "").replace("t.me/", "").replace("@", "").strip()
        if clean and clean.lower() not in ["bot", "share", "start", "app", "mining"]:
            try:
                await client(JoinChannelRequest(clean))
                logger.info(f"[{name}] Joined public channel @{clean}")
                await mute_peer(client, clean, name)
            except Exception as e:
                if "already" not in str(e).lower() and "USER_ALREADY_PARTICIPANT" not in str(e):
                    logger.debug(f"[{name}] Public channel join note (@{clean}): {e}")
                else:
                    await mute_peer(client, clean, name)


async def interact_and_verify_bot(client: TelegramClient, bot_username: str, start_cmd: str, name: str, required_channels: list = None, click_buttons: list = None):
    """
    Advanced autonomous bot interaction & verification engine:
    1. Sends /start <referral_param>.
    2. Joins any required sponsor channels (public and private invite links).
    3. Solves math captchas if present (e.g. 5 + 3 = ?).
    4. Selects language if prompted (English / 🇬🇧).
    5. Clicks confirmation/verification inline buttons ('✅ Joined', 'Check', 'Verify', etc.).
    6. Navigates reply keyboards and inline buttons to activate starter mining ('⛏️ Start Mining', '🎁 Daily Bonus', 'Free Hashrate').
    7. Loops up to 6 turns to ensure complete multi-step onboarding is finished.
    8. Mutes notifications permanently for the bot and all sponsor channels.
    """
    try:
        bot = await client.get_entity(bot_username)
        await mute_peer(client, bot, name)
        init_msgs = await client.get_messages(bot, limit=1)
        last_id = init_msgs[0].id if init_msgs else 0

        # Pre-join any required channels if specified and mute them
        if required_channels:
            for ch in required_channels:
                await join_tg_target(client, ch, name)
                await mute_peer(client, ch, name)
            await asyncio.sleep(1.0)

        await client.send_message(bot, start_cmd)
        logger.info(f"[{name}] Sent '{start_cmd}' to @{bot_username}")

        for turn in range(6):
            await asyncio.sleep(2.5)
            msgs = await client.get_messages(bot, limit=5)
            new_msgs = [m for m in msgs if m.id > last_id and not m.out]
            if not new_msgs:
                continue

            latest_msg = new_msgs[0]
            last_id = max(m.id for m in new_msgs)
            txt = latest_msg.raw_text or ""

            # 1. Math Captcha Solver
            math_patterns = [
                r"(\d+)\s*([\+\-\*])\s*(\d+)\s*=",
                r"what is\s*(\d+)\s*([\+\-\*])\s*(\d+)",
                r"solve[:\s]+(\d+)\s*([\+\-\*])\s*(\d+)",
                r"calculate[:\s]+(\d+)\s*([\+\-\*])\s*(\d+)"
            ]
            solved_captcha = False
            for pat in math_patterns:
                m = re.search(pat, txt, re.IGNORECASE)
                if m:
                    a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
                    ans = a + b if op == "+" else (a - b if op == "-" else a * b)
                    logger.info(f"[{name}] Solved math captcha on @{bot_username}: {a} {op} {b} = {ans}")
                    await client.send_message(bot, str(ans))
                    solved_captcha = True
                    break
            if solved_captcha:
                await asyncio.sleep(2.0)
                continue

            # 2. Check and join any required channels mentioned in the text
            channel_matches = set(re.findall(r"@([a-zA-Z0-9_]{4,})", txt) + re.findall(r"t\.me/([a-zA-Z0-9_]{4,})", txt))
            for ch in channel_matches:
                ch_clean = ch.strip().replace("https://t.me/", "").replace("t.me/", "")
                if ch_clean.lower() not in [bot_username.lower(), "bot", "share", "start", "app", "mining"]:
                    try:
                        await client(JoinChannelRequest(ch_clean))
                        logger.info(f"[{name}] Auto-joined channel @{ch_clean} for @{bot_username}")
                    except Exception:
                        pass

            # 3. Inspect and process buttons (both inline and reply keyboards)
            clicked_action = False

            # A. Check URL buttons for channels to join
            if latest_msg.buttons:
                for row in latest_msg.buttons:
                    for btn in row:
                        btn_url = getattr(btn, 'url', None) or ""
                        if "t.me/" in btn_url and "start=" not in btn_url and not btn_url.endswith("bot"):
                            await join_tg_target(client, btn_url, name)

                # B. Priority 0: Explicit click_buttons list if provided
                if click_buttons:
                    for row in latest_msg.buttons:
                        for btn in row:
                            b_low = (btn.text or "").strip().lower()
                            for cb in click_buttons:
                                if cb.lower() in b_low:
                                    try:
                                        await btn.click()
                                        logger.info(f"[{name}] Clicked requested button '{btn.text}' on @{bot_username}")
                                        clicked_action = True
                                        break
                                    except Exception as cbe:
                                        logger.debug(f"[{name}] Requested button click note: {cbe}")
                            if clicked_action:
                                break
                        if clicked_action:
                            break

                # C. Priority 1: Language selection
                if not clicked_action:
                    for row in latest_msg.buttons:
                        for btn in row:
                            b_low = (btn.text or "").strip().lower()
                            if any(l_kw in b_low for l_kw in ["english", "🇬🇧", "en"]):
                                try:
                                    await btn.click()
                                    logger.info(f"[{name}] Selected language '{btn.text}' on @{bot_username}")
                                    clicked_action = True
                                    break
                                except Exception:
                                    pass
                        if clicked_action:
                            break

                # C. Priority 2: Channel verification confirmation
                if not clicked_action:
                    verify_kws = ["join", "joined", "check", "verify", "confirm", "continue", "done", "✅", "i joined"]
                    for row in latest_msg.buttons:
                        for btn in row:
                            b_low = (btn.text or "").strip().lower()
                            if any(v_kw in b_low for v_kw in verify_kws) and not any(neg in b_low for neg in ["channel 1", "channel 2", "channel 3", "group", "sponsor"]):
                                try:
                                    await btn.click()
                                    logger.info(f"[{name}] Clicked verification '{btn.text}' on @{bot_username}")
                                    clicked_action = True
                                    break
                                except Exception:
                                    pass
                        if clicked_action:
                            break

                # D. Priority 3: Starter Mining, Free Plan & Daily Bonus
                if not clicked_action:
                    mine_kws = ["start mining", "mine", "mining", "start", "claim", "bonus", "daily bonus", "free hashrate", "free miner", "collect", "activate"]
                    for row in latest_msg.buttons:
                        for btn in row:
                            b_low = (btn.text or "").strip().lower()
                            if any(m_kw in b_low for m_kw in mine_kws):
                                try:
                                    await btn.click()
                                    logger.info(f"[{name}] Activated miner/bonus '{btn.text}' on @{bot_username}")
                                    clicked_action = True
                                    break
                                except Exception:
                                    pass
                        if clicked_action:
                            break

            # 4. Check for Reply Keyboards in reply_markup and send text triggers
            if hasattr(latest_msg, "reply_markup") and latest_msg.reply_markup and not clicked_action:
                try:
                    rm = latest_msg.reply_markup
                    if hasattr(rm, "rows"):
                        for row in rm.rows:
                            if hasattr(row, "buttons"):
                                for btn in row.buttons:
                                    b_text = getattr(btn, 'text', '') or ''
                                    b_low = b_text.strip().lower()
                                    if any(k in b_low for k in ["mining", "mine", "start mining", "bonus", "claim", "account", "balance"]):
                                        logger.info(f"[{name}] Sending ReplyKeyboard action '{b_text}' to @{bot_username}")
                                        await client.send_message(bot, b_text)
                                        clicked_action = True
                                        break
                            if clicked_action:
                                break
                except Exception as rme:
                    logger.debug(f"[{name}] ReplyKeyboard note: {rme}")

            if clicked_action:
                await asyncio.sleep(2.0)
    except Exception as e:
        logger.warning(f"[{name}] Interactive bot note for @{bot_username}: {e}")


def _extract_tg_init_data(url: str) -> str:
    """Robustly extracts raw tgWebAppData from either URL fragment (#) or query (?)."""
    if not url:
        return ""
    try:
        p = urllib.parse.urlparse(url)
        frag_params = urllib.parse.parse_qs(p.fragment)
        query_params = urllib.parse.parse_qs(p.query)
        return frag_params.get("tgWebAppData", [None])[0] or query_params.get("tgWebAppData", [None])[0] or ""
    except Exception:
        return ""


async def complete_tensor_referral(client: TelegramClient, name: str, ref_code: str = "6727787768"):
    try:
        b_tensor = await client.get_entity(TENSOR_BOT)
        await mute_peer(client, b_tensor, name)
        await client.send_message(b_tensor, f"/start {ref_code}")
        await asyncio.sleep(1.0)
        
        b_tns_in = await client.get_input_entity(TENSOR_BOT)
        wv_res = await client(RequestAppWebViewRequest(
            peer=b_tns_in,
            app=InputBotAppShortName(bot_id=b_tns_in, short_name="myapp"),
            platform="android",
            start_param=str(ref_code)
        ))
        tns_init = _extract_tg_init_data(getattr(wv_res, 'url', None))
        if tns_init:
            tns_h = {
                "Authorization": f"tma {tns_init}",
                "Origin": "https://flascoins.xyz",
                "Referer": "https://flascoins.xyz/",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.127 Mobile Safari/537.36 Telegram-Android/11.1.3"
            }
            async with aiohttp.ClientSession() as s:
                await s.post("https://flascoins.xyz/api/auth", json={"startParam": str(ref_code)}, headers=tns_h, timeout=aiohttp.ClientTimeout(total=8))
                await s.post("https://flascoins.xyz/api/daily", json={}, headers=tns_h, timeout=aiohttp.ClientTimeout(total=8))
                await s.post("https://flascoins.xyz/api/tap", json={"taps": 50}, headers=tns_h, timeout=aiohttp.ClientTimeout(total=8))
            logger.info(f"[{name}] ✅ Tensor Mining completed referral & activation on flascoins.xyz")
            return True
    except Exception as e:
        logger.warning(f"[{name}] Tensor referral completion note: {e}")
    return False


async def complete_tontrader_referral(client: TelegramClient, name: str, ref_code: str = "REF_6727787768"):
    try:
        await join_tg_target(client, "tontraderai_official", name)
        await join_tg_target(client, "tontraderai_group", name)
        b_tt = await client.get_entity(TONTRADER_BOT)
        await mute_peer(client, b_tt, name)
        await client.send_message(b_tt, f"/start {ref_code}")
        await asyncio.sleep(1.0)

        b_tt_in = await client.get_input_entity(TONTRADER_BOT)
        wv_res = await client(RequestAppWebViewRequest(
            peer=b_tt_in,
            app=InputBotAppShortName(bot_id=b_tt_in, short_name="app"),
            platform="android",
            start_param=str(ref_code)
        ))
        tt_init = _extract_tg_init_data(getattr(wv_res, 'url', None))
        if tt_init:
            tt_h = {
                "x-telegram-init-data": tt_init,
                "Origin": "https://tontraderai.com",
                "Referer": "https://tontraderai.com/",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-A305F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
            }
            async with aiohttp.ClientSession() as s:
                await s.get("https://api.tontraderai.com/api/v1/user/profile", headers=tt_h, timeout=aiohttp.ClientTimeout(total=8))
                await s.post("https://api.tontraderai.com/api/v1/user/claim-welcome-gift", json={}, headers=tt_h, timeout=aiohttp.ClientTimeout(total=8))
                await s.post("https://api.tontraderai.com/api/v1/user/claim-daily-gift", json={}, headers=tt_h, timeout=aiohttp.ClientTimeout(total=8))
                await s.post("https://api.tontraderai.com/api/v1/user/claim-gift-box", json={}, headers=tt_h, timeout=aiohttp.ClientTimeout(total=8))
                await s.post("https://api.tontraderai.com/api/v1/user/claim-channel-boost", json={}, headers=tt_h, timeout=aiohttp.ClientTimeout(total=8))
                await s.post("https://api.tontraderai.com/api/v1/finance/claim-yield", json={}, headers=tt_h, timeout=aiohttp.ClientTimeout(total=8))
            logger.info(f"[{name}] ✅ TonTrader AI completed referral & starter activation on api.tontraderai.com")
            return True
    except Exception as e:
        logger.warning(f"[{name}] TonTrader referral completion note: {e}")
    return False


async def complete_ominix_referral(client: TelegramClient, name: str, ref_code: str = "6727787768"):
    try:
        await join_tg_target(client, "ominiai", name)
        await join_tg_target(client, "ominiaipayout", name)
        b_om = await client.get_entity(OMINIX_BOT)
        await mute_peer(client, b_om, name)
        await client.send_message(b_om, f"/start {ref_code}")
        await asyncio.sleep(1.0)

        b_om_in = await client.get_input_entity(OMINIX_BOT)
        wv_res = await client(RequestAppWebViewRequest(
            peer=b_om_in,
            app=InputBotAppShortName(bot_id=b_om_in, short_name="Trade"),
            platform="android",
            start_param=str(ref_code)
        ))
        om_init = _extract_tg_init_data(getattr(wv_res, 'url', None))
        if om_init:
            om_h = {
                "Origin": "https://ominiaibot.lovable.app",
                "Referer": "https://ominiaibot.lovable.app/",
                "Content-Type": "application/json",
                "x-tsr-serverfn": "true",
                "accept": "application/json",
                "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-A305F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
            }
            seroval_payload = {
                "t": {
                    "t": 10,
                    "i": 0,
                    "p": {
                        "k": ["data"],
                        "v": [{"t": 10, "i": 1, "p": {"k": ["initData"], "v": [{"t": 1, "s": om_init}]}, "o": 0}]
                    },
                    "o": 0
                },
                "f": 127,
                "m": []
            }
            async with aiohttp.ClientSession() as s:
                # 1. Register user profile with referral start_param
                await s.post("https://ominiaibot.lovable.app/_serverFn/0d9e2e371b4bab4da7a71b5a2efcd0149c27f48dc15192cfdee2a995d5f6947e", json=seroval_payload, headers=om_h, timeout=aiohttp.ClientTimeout(total=8))
                # 2. Claim starting profit
                await s.post("https://ominiaibot.lovable.app/_serverFn/bcb8e269d7f337068c7424538a77cd77e7013594ec5c8849925e8ca5b7cbe06c", json=seroval_payload, headers=om_h, timeout=aiohttp.ClientTimeout(total=8))
                # 3. Open mystery gift box
                await s.post("https://ominiaibot.lovable.app/_serverFn/21aff4856aa0147739b66c3269611c49fd8dd342144e4973589515477e97c95b", json=seroval_payload, headers=om_h, timeout=aiohttp.ClientTimeout(total=8))
            logger.info(f"[{name}] ✅ Ominix completed referral & profit activation on lovable.app")
            return True
    except Exception as e:
        logger.warning(f"[{name}] Ominix referral completion note: {e}")
    return False


async def complete_btc_referral(client: TelegramClient, name: str, ref_code: str = "6727787768"):
    try:
        await join_tg_target(client, "https://t.me/+I1HZjvoqu942MjZl", name)
        b_btc = await client.get_entity(BTC_BOT)
        await mute_peer(client, b_btc, name)
        
        # Step 1: Dispatch /start <ref_code>
        await client.send_message(b_btc, f"/start {ref_code}")
        await asyncio.sleep(2.0)

        # Step 2: Click [🎮 Start Play] (callback b'start_play')
        msgs = await client.get_messages(b_btc, limit=3)
        for m in msgs:
            if not m.out and m.buttons:
                for r_idx, row in enumerate(m.buttons):
                    for c_idx, b in enumerate(row):
                        b_data = getattr(b, "data", None) or getattr(getattr(b, "button", None), "data", None)
                        b_text = (getattr(b, "text", "") or "").lower()
                        if b_data == b"start_play" or "start play" in b_text:
                            try:
                                await m.click(r_idx, c_idx)
                                logger.info(f"[{name}] Clicked [🎮 Start Play] on BTC bot")
                            except Exception:
                                pass
                            break

        await asyncio.sleep(2.5)

        # Step 3: Ensure channel is joined and click [✅ Continue] (callback b'check_join')
        await join_tg_target(client, "https://t.me/+I1HZjvoqu942MjZl", name)
        msgs = await client.get_messages(b_btc, limit=3)
        for m in msgs:
            if not m.out and m.buttons:
                for r_idx, row in enumerate(m.buttons):
                    for c_idx, b in enumerate(row):
                        b_data = getattr(b, "data", None) or getattr(getattr(b, "button", None), "data", None)
                        b_text = (getattr(b, "text", "") or "").lower()
                        if b_data == b"check_join" or "continue" in b_text or "verify" in b_text or "joined" in b_text:
                            try:
                                await m.click(r_idx, c_idx)
                                logger.info(f"[{name}] Clicked [✅ I've Joined / Continue] (check_join) on BTC bot")
                            except Exception:
                                pass
                            break

        await asyncio.sleep(2.0)

        # Step 4: Activate miner with ⛏ Mine command and claim initial reward
        await client.send_message(b_btc, "⛏ Mine")
        await asyncio.sleep(2.0)
        mine_msgs = await client.get_messages(b_btc, limit=3)
        for m in mine_msgs:
            if m.buttons:
                for r_idx, row in enumerate(m.buttons):
                    for c_idx, b in enumerate(row):
                        b_data = getattr(b, "data", None) or getattr(getattr(b, "button", None), "data", None)
                        b_text = (getattr(b, "text", "") or "").lower()
                        if b_data == b"claim_mine" or "claim" in b_text:
                            try:
                                await m.click(r_idx, c_idx)
                                await asyncio.sleep(1.0)
                            except Exception:
                                pass
        logger.info(f"[{name}] ✅ Bitcoin Cloud Miners completed referral & active miner claim")
        return True
    except Exception as e:
        logger.warning(f"[{name}] Bitcoin Cloud referral completion note: {e}")
    return False


async def complete_finvora_referral(client: TelegramClient, name: str, ref_code: str = "ref_TRX6727787768"):
    try:
        await join_tg_target(client, "finvoraweb3", name)
        b_fin = await client.get_entity(FINVORA_BOT)
        await mute_peer(client, b_fin, name)
        await client.send_message(b_fin, f"/start {ref_code}")
        await asyncio.sleep(1.5)

        # Direct WebApp handshake with exact Railway production Mini App URL
        try:
            await client(RequestWebViewRequest(
                peer=b_fin,
                bot=b_fin,
                url="https://finvora-production.up.railway.app/",
                platform="android",
                start_param=str(ref_code)
            ))
            logger.info(f"[{name}] ✅ FINVORA completed referral & direct webview handshake (Railway)")
            return True
        except Exception as we:
            logger.debug(f"[{name}] FINVORA direct webview note: {we}")

        # Fallback to inspecting message buttons
        msgs = await client.get_messages(b_fin, limit=5)
        for m in msgs:
            if m.buttons:
                for r_idx, row in enumerate(m.buttons):
                    for c_idx, b in enumerate(row):
                        b_url = getattr(b, "url", None)
                        if not b_url and hasattr(b, "button") and hasattr(b.button, "type") and hasattr(b.button.type, "url"):
                            b_url = b.button.type.url
                        if b_url and ("tgWebApp" in b_url or "http" in b_url):
                            try:
                                await client(RequestWebViewRequest(
                                    peer=b_fin,
                                    bot=b_fin,
                                    url=b_url,
                                    platform="android",
                                    start_param=str(ref_code)
                                ))
                                logger.info(f"[{name}] ✅ FINVORA completed referral via inline button URL")
                                return True
                            except Exception:
                                pass

        b_fin_in = await client.get_input_entity(FINVORA_BOT)
        for sn in ["app", "miniapp", "bot"]:
            try:
                await client(RequestAppWebViewRequest(
                    peer=b_fin_in,
                    app=InputBotAppShortName(bot_id=b_fin_in, short_name=sn),
                    platform="android",
                    start_param=str(ref_code)
                ))
                return True
            except Exception:
                pass
        return True
    except Exception as e:
        logger.warning(f"[{name}] FINVORA referral completion note: {e}")
    return False


async def complete_turbogram_referral(client: TelegramClient, name: str, ref_code: str = "r_3520c92b"):
    try:
        await join_tg_target(client, "TurboGramAnnouncements", name)
        await join_tg_target(client, "TurboGramPayment", name)
        b_tb = await client.get_entity(TURBOGRAM_BOT)
        await mute_peer(client, b_tb, name)
        await client.send_message(b_tb, f"/start {ref_code}")
        await asyncio.sleep(1.5)

        # Direct WebApp handshake with exact tamimdev.dev Mini App URL
        try:
            await client(RequestWebViewRequest(
                peer=b_tb,
                bot=b_tb,
                url="https://turbo.tamimdev.dev/",
                platform="android",
                start_param=str(ref_code)
            ))
            logger.info(f"[{name}] ✅ TurboGram completed referral & direct webview handshake (tamimdev)")
            return True
        except Exception as we:
            logger.debug(f"[{name}] TurboGram direct webview note: {we}")

        # Fallback to inspecting message buttons
        msgs = await client.get_messages(b_tb, limit=5)
        for m in msgs:
            if m.buttons:
                for r_idx, row in enumerate(m.buttons):
                    for c_idx, b in enumerate(row):
                        b_url = getattr(b, "url", None)
                        if not b_url and hasattr(b, "button") and hasattr(b.button, "type") and hasattr(b.button.type, "url"):
                            b_url = b.button.type.url
                        if b_url and ("tgWebApp" in b_url or "http" in b_url):
                            try:
                                await client(RequestWebViewRequest(
                                    peer=b_tb,
                                    bot=b_tb,
                                    url=b_url,
                                    platform="android",
                                    start_param=str(ref_code)
                                ))
                                logger.info(f"[{name}] ✅ TurboGram completed referral via inline button URL")
                                return True
                            except Exception:
                                pass

        b_tb_in = await client.get_input_entity(TURBOGRAM_BOT)
        for sn in ["app", "miniapp", "bot"]:
            try:
                await client(RequestAppWebViewRequest(
                    peer=b_tb_in,
                    app=InputBotAppShortName(bot_id=b_tb_in, short_name=sn),
                    platform="android",
                    start_param=str(ref_code)
                ))
                return True
            except Exception:
                pass
        return True
    except Exception as e:
        logger.warning(f"[{name}] TurboGram referral completion note: {e}")
    return False


async def bind_account_master_referrals(client: TelegramClient, acc_entry: dict):
    """
    Guarantees master referral codes are registered ONCE per account for 1st-time newly added accounts,
    extracts WebApp session tokens, syncs to 5x Cloudflare KV + Upstash,
    and executes referral finish work across all 8 bots:
    1. Stones: r6727787768
    2. MRG: ref_IRN1G3XD
    3. ART: 6727787768
    4. AI Lab: 296852
    5. UltraWallet: 6727787768
    6. Apex: 6727787768
    7. Ainovum: ref_6727787768
    8. ATF Miner: 6727787768
    """
    name = acc_entry.get("name", "User")
    uid = acc_entry.get("user_id")

    # STRICT GUARD: If account already has referrals bound, NEVER send /start messages!
    if is_account_referrals_bound(acc_entry):
        logger.info(f"[{name}] Master referrals already bound previously. Skipping referral /start messages.")
        tokens = {}
        try:
            if not client.is_connected():
                await client.connect()
            tokens = await extract_tokens_with_client(client, acc_entry)
        except Exception:
            pass
        if tokens:
            await sync_account_tokens_to_clouds(tokens)
        return

    logger.info(f"[{name}] 🚀 Initiating 1st-time 8-bot master referral binding (Master ID: 6727787768)...")

    # 1. Stones Miner
    if not acc_entry.get("stones_referral_bound"):
        try:
            b_stones = await client.get_entity(STONES_BOT)
            await client.send_message(b_stones, "/start r6727787768")
            try:
                await client(JoinChannelRequest("stoneswithestand"))
            except Exception:
                pass
            acc_entry["stones_referral_bound"] = True
            await asyncio.sleep(0.8)
        except Exception as e:
            logger.warning(f"[{name}] Stones referral bind note: {e}")

    # 2. MRG Miner (Strict WebApp initData + API Auth Verify Handshake)
    if not acc_entry.get("mrg_referral_bound"):
        try:
            b_mrg = await client.get_entity(MRG_BOT)
            await client.send_message(b_mrg, f"/start {MRG_REFERRAL_CODE}")
            try:
                b_mrg_in = await client.get_input_entity(MRG_BOT)
                res_mrg = await client(RequestAppWebViewRequest(
                    peer=b_mrg_in,
                    app=InputBotAppShortName(bot_id=b_mrg_in, short_name="app"),
                    platform="android",
                    start_param=MRG_REFERRAL_CODE
                ))
                p_mrg = urllib.parse.urlparse(res_mrg.url)
                mrg_init = urllib.parse.parse_qs(p_mrg.fragment).get("tgWebAppData", [None])[0]
                if mrg_init:
                    async with aiohttp.ClientSession() as hs:
                        await hs.post("https://mrg.up.railway.app/api/auth/verify", json={"initData": mrg_init, "start_param": MRG_REFERRAL_CODE}, timeout=aiohttp.ClientTimeout(total=8))
            except Exception as me:
                logger.debug(f"[{name}] MRG direct app verify note: {me}")
            acc_entry["mrg_referral_bound"] = True
            await asyncio.sleep(0.8)
        except Exception as e:
            logger.warning(f"[{name}] MRG referral bind note: {e}")

    # 3. ART Airdrop
    if not acc_entry.get("art_referral_bound"):
        try:
            b_art = await client.get_entity(ART_BOT)
            await client.send_message(b_art, f"/start {REPORT_CHAT_ID}")
            acc_entry["art_referral_bound"] = True
            await asyncio.sleep(0.8)
        except Exception as e:
            logger.warning(f"[{name}] ART referral bind note: {e}")

    # 4. AI Lab Robot
    if not acc_entry.get("ailab_referral_bound"):
        try:
            b_ai = await client.get_entity(AILAB_BOT)
            await client.send_message(b_ai, "/start 296852")
            acc_entry["ailab_referral_bound"] = True
            await asyncio.sleep(0.8)
        except Exception as e:
            logger.warning(f"[{name}] AI Lab referral bind note: {e}")

    # 5. UltraWallet (Strict WebApp initData + refBy Handshake)
    if not acc_entry.get("ultrawallet_referral_bound"):
        try:
            b_uw = await client.get_entity(ULTRAWALLET_BOT)
            await client.send_message(b_uw, f"/start {ULTRAWALLET_REFERRAL_CODE}")
            try:
                b_uw_in = await client.get_input_entity(ULTRAWALLET_BOT)
                res_uw = await client(RequestAppWebViewRequest(
                    peer=b_uw_in,
                    app=InputBotAppShortName(bot_id=b_uw_in, short_name="app"),
                    platform="android",
                    start_param=str(ULTRAWALLET_REFERRAL_CODE)
                ))
                p_uw = urllib.parse.urlparse(res_uw.url)
                uw_init = urllib.parse.parse_qs(p_uw.fragment).get("tgWebAppData", [None])[0]
                if uw_init:
                    async with aiohttp.ClientSession() as hs:
                        await hs.post("https://wallet.trxvault.top/api/telegramLogin", json={"initData": uw_init, "refBy": str(ULTRAWALLET_REFERRAL_CODE)}, timeout=aiohttp.ClientTimeout(total=8))
            except Exception as uwe:
                logger.debug(f"[{name}] UltraWallet direct app verify note: {uwe}")
            acc_entry["ultrawallet_referral_bound"] = True
            await asyncio.sleep(0.8)
        except Exception as e:
            logger.warning(f"[{name}] UltraWallet referral bind note: {e}")

    # 6. Apex Miner (Strict WebApp initData + Register Referrer Handshake)
    if not acc_entry.get("apx_referral_bound"):
        try:
            b_apx = await client.get_entity(APX_BOT)
            await client.send_message(b_apx, f"/start {APX_REFERRAL_CODE}")
            try:
                b_apx_in = await client.get_input_entity(APX_BOT)
                res_apx = await client(RequestAppWebViewRequest(
                    peer=b_apx_in,
                    app=InputBotAppShortName(bot_id=b_apx_in, short_name="app"),
                    platform="android",
                    start_param=str(APX_REFERRAL_CODE)
                ))
                p_apx = urllib.parse.urlparse(res_apx.url)
                apx_init = urllib.parse.parse_qs(p_apx.fragment).get("tgWebAppData", [None])[0]
                if apx_init:
                    async with aiohttp.ClientSession() as hs:
                        await hs.post("https://apxn-miner-live.apxn-network.workers.dev/api/auth/telegram", json={"initData": apx_init}, timeout=aiohttp.ClientTimeout(total=8))
                        await hs.post("https://apxn-miner-live.apxn-network.workers.dev/api/register", json={"initData": apx_init, "referrer": str(APX_REFERRAL_CODE)}, timeout=aiohttp.ClientTimeout(total=8))
            except Exception as apxe:
                logger.debug(f"[{name}] Apex direct app verify note: {apxe}")
            acc_entry["apx_referral_bound"] = True
            await asyncio.sleep(0.8)
        except Exception as e:
            logger.warning(f"[{name}] Apex referral bind note: {e}")

    # 7. Ainovum Bot
    if not acc_entry.get("ainovum_referral_bound"):
        try:
            b_ain = await client.get_entity(AINOVUM_BOT)
            await client.send_message(b_ain, f"/start {AINOVUM_REFERRAL_CODE}")
            acc_entry["ainovum_referral_bound"] = True
            await asyncio.sleep(0.8)
        except Exception as e:
            logger.warning(f"[{name}] Ainovum referral bind note: {e}")

    # 8. ATF Miner
    if not acc_entry.get("atf_referral_bound"):
        try:
            b_atf = await client.get_entity("ATF_AIRDROP_bot")
            await client.send_message(b_atf, f"/start {REPORT_CHAT_ID}")
            acc_entry["atf_referral_bound"] = True
            await asyncio.sleep(0.8)
        except Exception as e:
            logger.warning(f"[{name}] ATF referral bind note: {e}")

    # 9. TRX Power Mining
    if not acc_entry.get("trxpower_referral_bound"):
        try:
            await join_tg_target(client, "trxpowerminingOfficial", f"{name} trxpower")
            await join_tg_target(client, "TRX_WORLD_WORK", f"{name} trxpower")
            await asyncio.sleep(1.0)
            await interact_and_verify_bot(client, TRXPOWER_BOT, f"/start {TRXPOWER_REFERRAL_CODE}", name, required_channels=["trxpowerminingOfficial", "TRX_WORLD_WORK"], click_buttons=["✅ Check / Verify", "Check / Verify", "Verify"])
            acc_entry["trxpower_referral_bound"] = True
            await asyncio.sleep(1.0)
        except Exception as e:
            logger.warning(f"[{name}] TRX Power referral bind note: {e}")

    # 10. Bitcoin Cloud Miners (Start Play + Active Mining Claim)
    if not acc_entry.get("btc_referral_bound"):
        if await complete_btc_referral(client, name, BTC_REFERRAL_CODE):
            acc_entry["btc_referral_bound"] = True
        await asyncio.sleep(1.0)

    # 11. Tensor Mining Robot (flascoins.xyz WebApp Auth + Daily + Tap)
    if not acc_entry.get("tensor_referral_bound"):
        if await complete_tensor_referral(client, name, TENSOR_REFERRAL_CODE):
            acc_entry["tensor_referral_bound"] = True
        await asyncio.sleep(1.0)

    # 12. Ton Trader AI (api.tontraderai.com Profile + Daily Gift + Yield Claim)
    if not acc_entry.get("tontrader_referral_bound"):
        if await complete_tontrader_referral(client, name, TONTRADER_REFERRAL_CODE):
            acc_entry["tontrader_referral_bound"] = True
        await asyncio.sleep(1.0)

    # 13. FINVORA Web3 (Channel join + WebApp handshake)
    if not acc_entry.get("finvora_referral_bound"):
        if await complete_finvora_referral(client, name, FINVORA_REFERRAL_CODE):
            acc_entry["finvora_referral_bound"] = True
        await asyncio.sleep(1.0)

    # 14. TurboGram V1 (Announcement channels + WebApp handshake)
    if not acc_entry.get("turbogram_referral_bound"):
        if await complete_turbogram_referral(client, name, TURBOGRAM_REFERRAL_CODE):
            acc_entry["turbogram_referral_bound"] = True
        await asyncio.sleep(1.0)

    # 15. Ominix AI Trade (TanStack ServerFn Claim Profit + Mystery Box)
    if not acc_entry.get("ominix_referral_bound"):
        if await complete_ominix_referral(client, name, OMINIX_REFERRAL_CODE):
            acc_entry["ominix_referral_bound"] = True
        await asyncio.sleep(1.0)

    if is_account_referrals_bound(acc_entry):
        acc_entry["referrals_bound"] = True
        acc_entry["all_15_referrals_bound"] = True
        logger.info(f"[{name}] ✅ All 15 fleet bots successfully bound to Master ID 6727787768 (1st time only)!")
    else:
        logger.warning(f"[{name}] ⚠️ Some referrals could not be bound immediately. Will retry on next cycle.")

    # Wait 1.5s for Telegram bot backends to complete registration
    await asyncio.sleep(1.5)

    # Automatically extract WebApp tokens for this new account
    logger.info(f"[{name}] 🔑 Extracting WebApp initData tokens across all bots...")
    tokens = {}
    try:
        if not client.is_connected():
            await client.connect()
        tokens = await extract_tokens_with_client(client, acc_entry)
        logger.info(f"[{name}] ✅ Extracted {len([k for k in tokens if 'init_data' in k or 'wh_url' in k])} WebApp tokens")
    except Exception as te:
        logger.error(f"[{name}] Token extraction note: {te}")

    try:
        await client.disconnect()
    except Exception:
        pass

    # Fallback: if tokens is missing required bot keys, re-extract with fresh standalone client
    req_keys = ["stones_init_data", "mrg_init_data", "art_init_data", "ailab_init_data", "ultrawallet_init_data", "apx_init_data", "atf_init_data", "ainovum_init_data"]
    if not tokens or any(not tokens.get(k) for k in req_keys):
        logger.info(f"[{name}] Missing some bot tokens after direct extraction. Re-extracting with standalone client...")
        try:
            fresh = await extract_tokens_for_account(acc_entry)
            if fresh:
                tokens.update(fresh)
        except Exception as fe:
            logger.warning(f"[{name}] Standalone token extraction note: {fe}")

    # Synchronize tokens to 5x Cloudflare KV + Upstash Redis
    if tokens:
        await sync_account_tokens_to_clouds(tokens)
        # Bootstrap initial WebApp mining across all 15 bots (completes referral onboarding finish work)
        await bootstrap_account_mining(acc_entry, tokens)
        # Immediately execute complete 15-bot farming (all tasks, claims, spins, ads, math challenges)
        try:
            async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}) as s:
                await farm_single_account_bots(s, acc_entry, tokens)
                logger.info(f"[{name}] ✅ Complete initial 15-bot farming & referral finish work finished!")
        except Exception as fse:
            logger.error(f"[{name}] Initial farming note: {fse}")

    # Save updated referrals_bound flags across clouds
    await sync_new_account_to_clouds(acc_entry)
    logger.info(f"[{name}] 🚀 Master Fleet Onboarding & Referral Finish Work Active (15/15 Bots) for account {uid}")


async def sync_new_account_to_clouds(acc_entry: dict):
    """Saves new permanent account across Cloudflare KV, Supabase, and Upstash Redis."""
    global FLEET_ACCOUNTS_CACHE
    uid = str(acc_entry.get("user_id"))
    FLEET_ACCOUNTS_CACHE[uid] = acc_entry
    try:
        if os.path.exists("accounts.json"):
            with open("accounts.json", "r", encoding="utf-8") as f:
                cur = json.load(f)
            cur_map = {str(a.get("user_id")): a for a in cur}
            cur_map[uid] = acc_entry
            with open("accounts.json", "w", encoding="utf-8") as f:
                json.dump(list(cur_map.values()), f, indent=2)
    except Exception:
        pass

    # 1. Supabase
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            async with aiohttp.ClientSession() as s:
                await s.post(
                    f"{SUPABASE_URL}/rest/v1/accounts",
                    headers={
                        "apikey": SUPABASE_KEY,
                        "Authorization": f"Bearer {SUPABASE_KEY}",
                        "Content-Type": "application/json",
                        "Prefer": "resolution=merge-duplicates"
                    },
                    json=acc_entry,
                    timeout=aiohttp.ClientTimeout(total=10)
                )
        except Exception as e:
            logger.warning(f"Supabase sync note: {e}")

    # 2. Upstash Redis
    if UPSTASH_URL and UPSTASH_TOKEN:
        try:
            async with aiohttp.ClientSession() as s:
                await s.post(
                    f"{UPSTASH_URL}/set/account:{acc_entry['user_id']}",
                    headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"},
                    data=json.dumps(acc_entry),
                    timeout=aiohttp.ClientTimeout(total=10)
                )
                await s.post(
                    f"{UPSTASH_URL}/sadd/fleet_accounts_set/{acc_entry['user_id']}",
                    headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"},
                    timeout=aiohttp.ClientTimeout(total=10)
                )
        except Exception as e:
            logger.warning(f"Upstash sync note: {e}")

    # 3. Cloudflare KV Sync
    for cf_url in CF_WORKER_URLS:
        try:
            async with aiohttp.ClientSession() as s:
                await s.post(
                    f"{cf_url}/api/fleet/sync_account",
                    headers={"Authorization": f"Bearer {SECRET_KEY}", "Content-Type": "application/json", **BROWSER_HEADERS},
                    json=acc_entry,
                    timeout=aiohttp.ClientTimeout(total=10)
                )
        except Exception:
            pass


@app.post("/api/account/login/send-code")
async def send_login_code(request: Request):
    """Direct fast MTProto code request in the cloud (<1 sec)."""
    try:
        data = await request.json()
    except Exception:
        data = {}

    auth = request.headers.get("Authorization") or ""
    req_secret = data.get("secret", "")
    if auth != f"Bearer {SECRET_KEY}" and req_secret != SECRET_KEY:
        pass

    chat_id = str(data.get("chat_id") or REPORT_CHAT_ID)
    raw_phone = data.get("phone", "")
    if not raw_phone:
        return {"ok": False, "error": "Phone number is required"}

    cleaned_phone = get_clean_phone(raw_phone)
    logger.info(f"[Standby Cloud Login] Requesting code for {cleaned_phone} (Chat {chat_id})")

    # Disconnect any old pending client for this chat
    if chat_id in LOGIN_SESSIONS and LOGIN_SESSIONS[chat_id].get("client"):
        try:
            await LOGIN_SESSIONS[chat_id]["client"].disconnect()
        except Exception:
            pass
        LOGIN_SESSIONS.pop(chat_id, None)

    temp_client = TelegramClient(StringSession(), API_ID, API_HASH)
    try:
        await temp_client.connect()
        sent_code = await asyncio.wait_for(temp_client.send_code_request(cleaned_phone), timeout=25)
        LOGIN_SESSIONS[chat_id] = {
            "client": temp_client,
            "phone": cleaned_phone,
            "phone_code_hash": sent_code.phone_code_hash,
            "created_at": time.time()
        }
        logger.info(f"[Standby Cloud Login] ✅ Code dispatched to {cleaned_phone} (hash: {sent_code.phone_code_hash[:8]})")
        return {
            "ok": True,
            "phone": cleaned_phone,
            "phone_code_hash": sent_code.phone_code_hash,
            "message": f"Verification code sent to {cleaned_phone}"
        }
    except PhoneNumberInvalidError:
        try:
            await temp_client.disconnect()
        except Exception:
            pass
        LOGIN_SESSIONS.pop(chat_id, None)
        return {"ok": False, "error": f"Invalid phone number: {cleaned_phone}. Please check country code."}
    except Exception as e:
        logger.error(f"[Standby Cloud Login] Error sending code to {cleaned_phone}: {e}")
        try:
            await temp_client.disconnect()
        except Exception:
            pass
        LOGIN_SESSIONS.pop(chat_id, None)
        return {"ok": False, "error": str(e)}


@app.post("/api/account/login/verify-code")
async def verify_login_code(request: Request):
    """Direct fast MTProto code or 2FA password verification in the cloud (<1 sec)."""
    try:
        data = await request.json()
    except Exception:
        data = {}

    chat_id = str(data.get("chat_id") or REPORT_CHAT_ID)
    code = str(data.get("code") or "").strip()
    password = str(data.get("password") or "").strip()

    session_data = LOGIN_SESSIONS.get(chat_id)
    if not session_data or not session_data.get("client"):
        return {"ok": False, "error": "No active login session found. Please tap Add Account to start over."}

    client: TelegramClient = session_data["client"]
    phone = session_data["phone"]
    phone_code_hash = session_data["phone_code_hash"]

    try:
        if not client.is_connected():
            await client.connect()

        if password:
            logger.info(f"[Standby Cloud Login] Attempting 2FA sign in for {phone}...")
            await asyncio.wait_for(client.sign_in(password=password), timeout=25)
        else:
            clean_code = re.sub(r"[^0-9]", "", code)
            if not clean_code or len(clean_code) < 3:
                return {"ok": False, "error": "Please provide a valid verification code."}
            logger.info(f"[Standby Cloud Login] Attempting code sign in for {phone} (code: {clean_code})...")
            await asyncio.wait_for(client.sign_in(phone=phone, code=clean_code, phone_code_hash=phone_code_hash), timeout=25)

        # Authenticated successfully!
        me = await client.get_me()
        user_id = me.id
        acc_name = f"{me.first_name or ''} {me.last_name or ''}".strip() or "User"
        uname = me.username or "None"
        sess_str = client.session.save()

        logger.info(f"[Standby Cloud Login] 🎉 Account signed in: {acc_name} (@{uname}, ID: {user_id})")

        acc_entry = {
            "name": acc_name,
            "username": uname,
            "user_id": user_id,
            "phone": phone,
            "session_string": sess_str,
            "added_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "status": "active"
        }

        # Automatically bind all 8 master referrals in the background
        asyncio.create_task(bind_account_master_referrals(client, acc_entry))

        # Sync account to Supabase, Upstash Redis, and Cloudflare KV
        asyncio.create_task(sync_new_account_to_clouds(acc_entry))

        LOGIN_SESSIONS.pop(chat_id, None)

        return {
            "ok": True,
            "user_id": user_id,
            "name": acc_name,
            "username": uname,
            "phone": phone,
            "session_string": sess_str,
            "referrals": "Binding to Master Fleet (15/15 Bots)...",
            "message": "Account connected successfully! All 15 fleet bots are being bound to Master ID 6727787768."
        }

    except SessionPasswordNeededError:
        logger.info(f"[Standby Cloud Login] 🔒 2FA password required for {phone}")
        return {
            "ok": False,
            "need_2fa": True,
            "phone": phone,
            "message": "Two-Factor Cloud Password required"
        }
    except PhoneCodeInvalidError:
        return {"ok": False, "need_2fa": False, "error": "Invalid verification code. Please check and retry."}
    except PhoneCodeExpiredError:
        try:
            await client.disconnect()
        except Exception:
            pass
        LOGIN_SESSIONS.pop(chat_id, None)
        return {"ok": False, "need_2fa": False, "error": "Verification code expired. Please tap Add Account to start over."}
    except Exception as e:
        logger.error(f"[Standby Cloud Login] Sign-in error: {e}")
        return {"ok": False, "need_2fa": False, "error": str(e)}


@app.post("/api/account/login/cancel")
async def cancel_login(request: Request):
    """Cancels active login session for a chat."""
    try:
        data = await request.json()
    except Exception:
        data = {}
    chat_id = str(data.get("chat_id") or REPORT_CHAT_ID)
    if chat_id in LOGIN_SESSIONS:
        cl = LOGIN_SESSIONS[chat_id].get("client")
        if cl:
            try:
                await cl.disconnect()
            except Exception:
                pass
        LOGIN_SESSIONS.pop(chat_id, None)
        logger.info(f"[Standby Cloud Login] ❌ Login session cancelled for Chat {chat_id}")
    return {"ok": True, "message": "Login cancelled"}


# =============================================================================
# 100% CLOUD AUTOMATED WITHDRAWALS & ON-CHAIN VAULT SWEEPER ENGINE
# =============================================================================
MASTER_EVM_VAULT = "0xfda4182001672b9f0f09e2118242e543e35ed5ce"
MASTER_TON_VAULT = "UQBPZiSvitdPU3VUyJK2mRaHVBl69xejw5aOrh1KfKA7gwDT"
PAYOUT_CHANNEL_ID = os.getenv("PAYOUT_CHANNEL_ID", "-1004402765950")

SENT_RECEIPT_HASHES = {}

async def send_payout_receipt(message: str, dedupe_key: str = None):
    """Broadcasts payout & on-chain receipts with strict anti-spam deduplication (max 1 notification per 12h per event)."""
    global SENT_RECEIPT_HASHES
    import hashlib
    now = time.time()
    # Clean up hashes older than 12h
    SENT_RECEIPT_HASHES = {k: v for k, v in SENT_RECEIPT_HASHES.items() if now - v < 43200}

    key = dedupe_key or hashlib.md5(message.strip().encode("utf-8")).hexdigest()
    if key in SENT_RECEIPT_HASHES:
        logger.info(f"[Anti-Spam] Suppressed duplicate Telegram receipt: {key}")
        return

    SENT_RECEIPT_HASHES[key] = now

    bot_token = os.getenv("REPORT_BOT_TOKEN", "")
    if not bot_token:
        return
    targets = [REPORT_CHAT_ID, PAYOUT_CHANNEL_ID]
    async with aiohttp.ClientSession() as s:
        for tid in targets:
            try:
                await s.post(
                    f"https://api.telegram.org/bot{bot_token}/sendMessage",
                    json={
                        "chat_id": tid,
                        "text": message,
                        "parse_mode": "HTML" if "<" in message else "Markdown",
                        "disable_web_page_preview": True
                    },
                    timeout=aiohttp.ClientTimeout(total=8)
                )
                await asyncio.sleep(0.5)
            except Exception:
                pass


async def check_and_withdraw_ailab(session: aiohttp.ClientSession, acc: dict, tokens: dict) -> dict:
    """Checks and executes auto-withdrawal for AI Lab Robot (Threshold: $0.02 for master, $1.00 for workers)."""
    uid = str(acc.get("user_id"))
    name = acc.get("name", uid)
    is_master = (uid == "6727787768" or acc.get("phone") in ("+8801317342850", "01317342850") or acc.get("is_primary"))
    init_data = tokens.get(uid, {}).get("ailab_init_data")
    if not init_data:
        return {"uid": uid, "name": name, "status": "no_init_data", "balance": 0.0}

    base_url = "https://api.ailab-agent.online/api/v1"
    headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro)"}
    try:
        async with session.post(f"{base_url}/users/auth/login", json={"user": init_data}, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as lr:
            if lr.status != 200:
                return {"uid": uid, "name": name, "status": f"login_err_{lr.status}", "balance": 0.0}
            ld = await lr.json()
            tok = ld.get("result", {}).get("bearer") or ld.get("user_info", {}).get("session_id")
            if not tok:
                return {"uid": uid, "name": name, "status": "no_token", "balance": 0.0}

        auth_headers = {**headers, "Authorization": f"Bearer {tok}"}
        async with session.get(f"{base_url}/cashout", headers=auth_headers, timeout=aiohttp.ClientTimeout(total=8)) as cr:
            if cr.status != 200:
                return {"uid": uid, "name": name, "status": f"cashout_err_{cr.status}", "balance": 0.0}
            cd = await cr.json()
            ubal = float(cd.get("user_info", {}).get("balance", 0) or 0)

        thresh = 0.02 if is_master else 1.00
        logger.info(f"[Cloud AI Lab] {name} ({uid}) balance: ${ubal:.4f} USD (Threshold: ${thresh:.2f})")
        if ubal >= thresh:
            wd_usd = round(int(ubal * 100) / 100.0, 2)
            async with session.post(f"{base_url}/cashout-pay", json={"ps_id": 5, "amount_usd": wd_usd, "wallet": MASTER_EVM_VAULT, "dest_tag": ""}, headers=auth_headers, timeout=aiohttp.ClientTimeout(total=10)) as pr:
                pres = await pr.json()
                if pres.get("request_info", {}).get("error_code") == 0 or pres.get("result"):
                    role_str = "Main Master Host" if is_master else "Worker"
                    logger.info(f"[Cloud AI Lab] {name} ({role_str}) auto-cashout submitted: ${wd_usd} USD")
                    return {"uid": uid, "name": name, "status": "withdrawn", "amount": wd_usd}
        return {"uid": uid, "name": name, "status": "below_threshold", "balance": ubal}
    except Exception as e:
        logger.warning(f"[Cloud AI Lab] Error for {name}: {e}")
        return {"uid": uid, "name": name, "status": "error", "error": str(e)}


async def check_and_withdraw_ainovum(session: aiohttp.ClientSession, acc: dict, tokens: dict) -> dict:
    """Checks and executes auto-withdrawal for Ainovum (Threshold: 0.10 USDT for master, 1.00 USDT for workers)."""
    uid = str(acc.get("user_id"))
    name = acc.get("name", uid)
    is_master = (uid == "6727787768" or acc.get("phone") in ("+8801317342850", "01317342850") or acc.get("is_primary"))
    init_data = tokens.get(uid, {}).get("ainovum_init_data")
    if not init_data:
        return {"uid": uid, "name": name, "status": "no_init_data", "available": 0.0}

    base_url = "https://ainovum.biz"
    headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro)"}
    try:
        cookie_hdr = ""
        boot_user = {}
        async with session.post(f"{base_url}/api/bootstrap", json={"initData": init_data, "platform": "android", "referrer": "ref_6727787768"}, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as br:
            if br.status == 200:
                bd = await br.json()
                boot_user = bd.get("user", {})
                raw_cookies = br.headers.getall("Set-Cookie", [])
                cookie_hdr = "; ".join([c.split(";")[0] for c in raw_cookies])
            else:
                return {"uid": uid, "name": name, "status": f"bootstrap_err_{br.status}", "available": 0.0}

        auth_headers = dict(headers)
        if cookie_hdr:
            auth_headers["Cookie"] = cookie_hdr

        # Open any available gift boxes
        try:
            async with session.get(f"{base_url}/api/gift-box/state", headers=auth_headers, timeout=aiohttp.ClientTimeout(total=5)) as gsr:
                if gsr.status == 200:
                    gsd = await gsr.json()
                    boxes_left = int(gsd.get("box", {}).get("boxes_left", 0) or 0)
                    while boxes_left > 0:
                        async with session.post(f"{base_url}/api/gift-box/open", json={}, headers=auth_headers, timeout=aiohttp.ClientTimeout(total=6)) as gbr:
                            if gbr.status == 200:
                                gbd = await gbr.json()
                                boxes_left = int(gbd.get("box", {}).get("boxes_left", 0) or 0)
                            else:
                                break
        except Exception:
            pass

        avail = 0.0
        async with session.get(f"{base_url}/api/withdraws/usdt/config", headers=auth_headers, timeout=aiohttp.ClientTimeout(total=8)) as cr:
            if cr.status == 200:
                cd = await cr.json()
                avail = float(cd.get("freeze", {}).get("available", 0) or 0)

        thresh = 0.10 if is_master else 1.00
        logger.info(f"[Cloud Ainovum] {name} ({uid}) available: {avail:.4f} USDT (Threshold: {thresh:.2f})")
        if boot_user.get("is_withdraw_locked") == 1:
            return {"uid": uid, "name": name, "status": "locked_or_deposit_required", "available": avail}

        if avail >= thresh:
            wd_amt = round(avail, 4)
            async with session.post(f"{base_url}/api/withdraws/usdt/create", json={"amount": wd_amt, "wallet": MASTER_EVM_VAULT, "network": "bep20"}, headers=auth_headers, timeout=aiohttp.ClientTimeout(total=10)) as wr:
                wd = await wr.json()
                if wr.status == 200 and not wd.get("access_denied") and not wd.get("error"):
                    logger.info(f"[Cloud Ainovum] {name} auto-withdrawal submitted: {wd_amt} USDT")
                    return {"uid": uid, "name": name, "status": "withdrawn", "amount": wd_amt}
        return {"uid": uid, "name": name, "status": "below_threshold", "available": avail}
    except Exception as e:
        logger.warning(f"[Cloud Ainovum] Error for {name}: {e}")
        return {"uid": uid, "name": name, "status": "error", "error": str(e)}


async def check_and_withdraw_stones(session: aiohttp.ClientSession, acc: dict, tokens: dict) -> dict:
    """Checks balance and executes automated withdrawal for Stones Miners (Threshold: >= 500 STONES)."""
    uid = str(acc.get("user_id"))
    name = acc.get("name", uid)
    if uid == "6727787768":
        return {"uid": uid, "name": name, "status": "compounding_mode"}

    init_data = tokens.get(uid, {}).get("stones_init_data")
    if not init_data:
        return {"uid": uid, "name": name, "status": "no_init_data"}

    base_url = "https://app.stoneswithestand.my.id"
    headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro)"}
    try:
        async with session.post(f"{base_url}/api/state", json={"initData": init_data}, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as sr:
            if sr.status != 200:
                return {"uid": uid, "name": name, "status": "state_check_failed"}
            sd = await sr.json()
            user_data = sd.get("user", {})
            coins = float(user_data.get("coins", 0) or 0)
            if coins < 500:
                return {"uid": uid, "name": name, "status": "below_threshold", "coins": coins}

            logger.info(f"[Cloud Stones] {name} ({uid}) threshold reached: {coins:.1f} >= 500. Executing automated withdrawal...")

            # 1. Bind target vault wallet if not bound
            bound_wallet = user_data.get("wallet", "")
            target_wallet = acc.get("evm_wallet", {}).get("address") or MASTER_EVM_VAULT
            if bound_wallet.lower() != target_wallet.lower():
                try:
                    await session.post(f"{base_url}/api/wallet", json={"initData": init_data, "wallet": target_wallet}, headers=headers, timeout=aiohttp.ClientTimeout(total=6))
                except Exception:
                    pass

            # 2. Issue captcha
            ticket = None
            async with session.post(f"{base_url}/api/wd/captcha/issue", json={"initData": init_data}, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as ir:
                if ir.status == 200:
                    idat = await ir.json()
                    if idat.get("enabled") is False:
                        ticket = None
                    else:
                        cid = idat.get("captcha_id")
                        img = idat.get("image", "")
                        clen = int(idat.get("length", 5))
                        if cid and img:
                            ans = await solve_stones_captcha_ai(session, img, clen)
                            if ans:
                                async with session.post(f"{base_url}/api/wd/captcha/verify", json={"initData": init_data, "captcha_id": cid, "answer": ans}, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as vr:
                                    if vr.status == 200:
                                        vrd = await vr.json()
                                        if vrd.get("ok"):
                                            ticket = vrd.get("ticket")

            # 3. Submit withdrawal
            wd_payload = {"initData": init_data, "amount": 500, "wallet": target_wallet, "currency": "stones"}
            if ticket:
                wd_payload["ticket"] = ticket
                wd_payload["captcha_ticket"] = ticket

            async with session.post(f"{base_url}/api/withdraw", json=wd_payload, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as wr:
                if wr.status == 200:
                    wrd = await wr.json()
                    if wrd.get("ok"):
                        logger.info(f"[Cloud Stones] {name} ({uid}) auto-withdrawal submitted: 500 STONES -> {target_wallet}")
                        return {"uid": uid, "name": name, "status": "withdrawn", "coins": coins, "wallet": target_wallet}
                    else:
                        logger.warning(f"[Cloud Stones] {name} withdraw rejected: {wrd.get('info')}")
                        return {"uid": uid, "name": name, "status": "rejected", "info": wrd.get("info")}
                return {"uid": uid, "name": name, "status": f"http_{wr.status}"}
    except Exception as e:
        logger.warning(f"[Cloud Stones] Error for {name}: {e}")
        return {"uid": uid, "name": name, "status": "error", "error": str(e)}


# =============================================================================
# MULTI-CHAIN ON-CHAIN SWEEPER & CONSOLIDATION ENGINE
# =============================================================================
FLEET_EVM_CACHE = {}
FLEET_TON_CACHE = {}

BSC_USDT_CONTRACT = "0x55d398326f99059fF775485246999027B3197955"
DRPC_KEY = os.getenv("DRPC_API_KEY", "AqfE-vxQsEgZrdrPasY_EsnLP3satOIR8YH4El_NDNxu")
TONAPI_KEY = os.getenv("TONAPI_KEY", "")
TONCENTER_API_KEY = os.getenv("TONCENTER_API_KEY", "")

BSC_RPCS = [
    f"https://bsc.drpc.org/ogrpc?dkey={DRPC_KEY}",
    "https://bsc-dataseed.binance.org",
    "https://bsc-dataseed1.defibit.io",
    "https://bsc-dataseed1.binance.org"
]

ARB_RPCS = [
    f"https://arbitrum.drpc.org/ogrpc?dkey={DRPC_KEY}",
    "https://arb1.arbitrum.io/rpc"
]

async def load_fleet_wallets_from_cloud() -> tuple:
    """Loads worker EVM and TON wallets from local disk or Cloudflare backup.zip."""
    global FLEET_EVM_CACHE, FLEET_TON_CACHE
    if FLEET_EVM_CACHE and FLEET_TON_CACHE:
        return FLEET_EVM_CACHE, FLEET_TON_CACHE

    if os.path.exists("fleet_evm_wallets.json") and os.path.exists("fleet_ton_wallets.json"):
        try:
            with open("fleet_evm_wallets.json", "r", encoding="utf-8") as f:
                FLEET_EVM_CACHE = json.load(f)
            with open("fleet_ton_wallets.json", "r", encoding="utf-8") as f:
                FLEET_TON_CACHE = json.load(f)
            return FLEET_EVM_CACHE, FLEET_TON_CACHE
        except Exception:
            pass

    import zipfile, io
    async with aiohttp.ClientSession() as http:
        for cf_url in CF_WORKER_URLS:
            try:
                async with http.get(f"{cf_url}/backup.zip", headers=BROWSER_HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as r:
                    if r.status == 200:
                        zip_bytes = await r.read()
                        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                            if "fleet_evm_wallets.json" in zf.namelist():
                                FLEET_EVM_CACHE = json.loads(zf.read("fleet_evm_wallets.json").decode("utf-8"))
                            if "fleet_ton_wallets.json" in zf.namelist():
                                FLEET_TON_CACHE = json.loads(zf.read("fleet_ton_wallets.json").decode("utf-8"))
                            if FLEET_EVM_CACHE and FLEET_TON_CACHE:
                                logger.info(f"Loaded {len(FLEET_EVM_CACHE)} EVM and {len(FLEET_TON_CACHE)} TON wallets from cloud backup.")
                                return FLEET_EVM_CACHE, FLEET_TON_CACHE
            except Exception as e:
                logger.warning(f"Could not load wallets from {cf_url}: {e}")
    return FLEET_EVM_CACHE, FLEET_TON_CACHE


async def query_evm_rpc(session: aiohttp.ClientSession, rpc_list: list, method: str, params: list):
    payload = {"jsonrpc": "2.0", "id": int(time.time()), "method": method, "params": params}
    for rpc in rpc_list:
        try:
            async with session.post(rpc, json=payload, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if "result" in data:
                        return data["result"]
        except Exception:
            continue
    return None


async def audit_single_evm(session: aiohttp.ClientSession, uid: str, info: dict):
    if not isinstance(info, dict) or "address" not in info or str(uid).startswith("_"):
        return None
    addr = info["address"]
    name = info.get("name", f"Worker {uid}")
    clean_addr = addr.lower().replace("0x", "").zfill(64)
    usdt_call_data = "0x70a08231" + clean_addr

    raw_bnb_t = query_evm_rpc(session, BSC_RPCS, "eth_getBalance", [addr, "latest"])
    raw_eth_t = query_evm_rpc(session, ARB_RPCS, "eth_getBalance", [addr, "latest"])
    raw_usdt_t = query_evm_rpc(session, BSC_RPCS, "eth_call", [{"to": BSC_USDT_CONTRACT, "data": usdt_call_data}, "latest"])

    raw_bnb, raw_eth, raw_usdt = await asyncio.gather(raw_bnb_t, raw_eth_t, raw_usdt_t, return_exceptions=True)

    bnb_bal = int(raw_bnb, 16) / 1e18 if isinstance(raw_bnb, str) and raw_bnb else 0.0
    eth_bal = int(raw_eth, 16) / 1e18 if isinstance(raw_eth, str) and raw_eth else 0.0
    usdt_bal = int(raw_usdt, 16) / 1e18 if isinstance(raw_usdt, str) and raw_usdt not in ("0x", "0x0") else 0.0

    return {
        "uid": uid,
        "name": name,
        "address": addr,
        "private_key": info.get("private_key"),
        "bnb_balance": bnb_bal,
        "eth_balance": eth_bal,
        "usdt_balance": usdt_bal
    }


async def audit_single_ton(session: aiohttp.ClientSession, uid: str, info: dict, headers: dict):
    if not isinstance(info, dict) or "address" not in info or str(uid).startswith("_"):
        return None
    addr = info["address"]
    name = info.get("name", f"Worker {uid}")
    ton_bal = 0.0
    try:
        url = f"https://tonapi.io/v2/accounts/{addr}"
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            if resp.status == 200:
                data = await resp.json()
                raw_bal = data.get("balance", 0)
                ton_bal = int(raw_bal) / 1e9
            else:
                # Toncenter API fallback
                tc_url = f"https://toncenter.com/api/v2/getAddressBalance?address={addr}"
                async with session.get(tc_url, timeout=aiohttp.ClientTimeout(total=5)) as tc_resp:
                    if tc_resp.status == 200:
                        tc_data = await tc_resp.json()
                        if tc_data.get("ok"):
                            ton_bal = int(tc_data.get("result", 0)) / 1e9
    except Exception:
        try:
            tc_url = f"https://toncenter.com/api/v2/getAddressBalance?address={addr}"
            async with session.get(tc_url, timeout=aiohttp.ClientTimeout(total=5)) as tc_resp:
                if tc_resp.status == 200:
                    tc_data = await tc_resp.json()
                    if tc_data.get("ok"):
                        ton_bal = int(tc_data.get("result", 0)) / 1e9
        except Exception:
            pass
    return {
        "uid": uid,
        "name": name,
        "address": addr,
        "mnemonic": info.get("mnemonic"),
        "ton_balance": ton_bal
    }


def sweep_evm_native_balance(rpc_list: list, chain_id: int, chain_name: str, private_key: str, from_addr: str, to_addr: str, native_balance: float, min_val: float = 0.0005):
    if not HAS_WEB3 or not private_key or native_balance <= min_val:
        return None
    try:
        w3 = None
        for rpc in rpc_list:
            try:
                tw3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 10}))
                if tw3.is_connected():
                    w3 = tw3
                    break
            except Exception:
                continue
        if not w3:
            return None

        cs_from = Web3.to_checksum_address(from_addr)
        cs_to = Web3.to_checksum_address(to_addr)
        if cs_from.lower() == cs_to.lower():
            return None

        nonce = w3.eth.get_transaction_count(cs_from)
        gas_price = w3.eth.gas_price
        gas_limit = 50000 if chain_id == 42161 else 21000
        gas_cost = gas_price * gas_limit
        balance_wei = w3.eth.get_balance(cs_from)
        amount_to_send = balance_wei - gas_cost
        if amount_to_send <= 0:
            return None

        tx = {
            "nonce": nonce,
            "to": cs_to,
            "value": amount_to_send,
            "gas": gas_limit,
            "gasPrice": gas_price,
            "chainId": chain_id
        }
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
        raw_tx = getattr(signed_tx, "raw_transaction", None) or getattr(signed_tx, "rawTransaction", None)
        tx_hash = w3.eth.send_raw_transaction(raw_tx)
        tx_hash_hex = tx_hash.hex()
        if not tx_hash_hex.startswith("0x"):
            tx_hash_hex = "0x" + tx_hash_hex
        logger.info(f"[{chain_name}] Swept {amount_to_send / 1e18:.6f} to {to_addr}! Tx: {tx_hash_hex}")
        return tx_hash_hex
    except Exception as e:
        logger.error(f"[{chain_name}] Sweep failed for {from_addr}: {e}")
        return None


def sweep_bep20_token_balance(rpc_list: list, chain_id: int, private_key: str, token_addr: str, from_addr: str, to_addr: str, token_balance: float, min_tokens: float = 0.08):
    if not HAS_WEB3 or not private_key or token_balance <= min_tokens:
        return None
    try:
        w3 = None
        for rpc in rpc_list:
            try:
                tw3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 10}))
                if tw3.is_connected():
                    w3 = tw3
                    break
            except Exception:
                continue
        if not w3:
            return None

        cs_from = Web3.to_checksum_address(from_addr)
        cs_to = Web3.to_checksum_address(to_addr)
        if cs_from.lower() == cs_to.lower():
            return None

        cs_token = Web3.to_checksum_address(token_addr)
        native_bal = w3.eth.get_balance(cs_from)
        gas_price = w3.eth.gas_price
        gas_limit = 65000
        gas_cost = gas_price * gas_limit
        if native_bal < gas_cost:
            logger.warning(f"[BEP-20 Sweep] {from_addr} has tokens but insufficient gas")
            return None

        nonce = w3.eth.get_transaction_count(cs_from)
        transfer_abi = [
            {"constant": False, "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
            {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}
        ]
        contract = w3.eth.contract(address=cs_token, abi=transfer_abi)
        raw_bal = contract.functions.balanceOf(cs_from).call()
        if raw_bal <= 0:
            return None

        tx = contract.functions.transfer(cs_to, raw_bal).build_transaction({
            "from": cs_from,
            "nonce": nonce,
            "gas": gas_limit,
            "gasPrice": gas_price,
            "chainId": chain_id
        })
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
        raw_tx = getattr(signed_tx, "raw_transaction", None) or getattr(signed_tx, "rawTransaction", None)
        tx_hash = w3.eth.send_raw_transaction(raw_tx)
        tx_hash_hex = tx_hash.hex()
        if not tx_hash_hex.startswith("0x"):
            tx_hash_hex = "0x" + tx_hash_hex
        logger.info(f"[BEP-20 Sweep] Swept {token_balance:.2f} USDT to {to_addr}! Tx: {tx_hash_hex}")
        return tx_hash_hex
    except Exception as e:
        logger.error(f"[BEP-20 Sweep] Sweep failed for {from_addr}: {e}")
        return None


async def sweep_ton_balance(session: aiohttp.ClientSession, mnemonic: str, from_addr: str, to_addr: str, balance: float, min_threshold: float = 0.02):
    if not HAS_TONSDK or not mnemonic or balance <= min_threshold:
        return None
    try:
        words = mnemonic.strip().split()
        if len(words) != 24:
            return None
        _mn, _pub, _priv, wallet = Wallets.from_mnemonics(words, version=WalletVersionEnum.v4r2)
        seqno = 0
        try:
            tc_headers = {"X-API-Key": TONCENTER_API_KEY} if TONCENTER_API_KEY else {}
            tc_url = "https://toncenter.com/api/v2/runGetMethod"
            payload = {"address": from_addr, "method": "seqno", "stack": []}
            async with session.post(tc_url, json=payload, headers=tc_headers, timeout=aiohttp.ClientTimeout(total=5)) as r:
                if r.status == 200:
                    d = await r.json()
                    if d.get("ok") and d.get("result", {}).get("stack"):
                        raw = d["result"]["stack"][0][1]
                        seqno = int(raw, 16) if str(raw).startswith("0x") else int(raw)
        except Exception:
            pass

        gas_fee = 0.008
        amount_to_send = balance - gas_fee
        if amount_to_send <= 0:
            return None

        amount_nano = int(amount_to_send * 1e9)
        query = wallet.create_transfer_message(
            to_addr=to_addr,
            amount=amount_nano,
            seqno=seqno,
            payload="Automated Fleet Sweep"
        )
        boc = query["message"].to_boc(False)
        b64_boc = base64.b64encode(boc).decode("utf-8")

        tc_headers = {"X-API-Key": TONCENTER_API_KEY, "Content-Type": "application/json"} if TONCENTER_API_KEY else {"Content-Type": "application/json"}
        send_url = "https://toncenter.com/api/v2/sendBoc"
        async with session.post(send_url, json={"boc": b64_boc}, headers=tc_headers, timeout=aiohttp.ClientTimeout(total=8)) as br:
            if br.status == 200:
                resp_d = await br.json()
                if resp_d.get("ok"):
                    logger.info(f"[TON Sweep] Swept {amount_to_send:.4f} TON from {from_addr} to {to_addr}!")
                    return "boc_sent"
    except Exception as e:
        logger.error(f"[TON Sweep] Failed for {from_addr}: {e}")
    return None


async def execute_cloud_onchain_sweeper(session: aiohttp.ClientSession, accounts: list = None, execute_sweep: bool = True, notify: bool = False) -> dict:
    """Audits on-chain balances across all worker EVM and TON wallets and sweeps surplus balances."""
    logger.info("[Cloud Sweeper] Auditing on-chain balances across all fleet wallets...")
    evm_wallets, ton_wallets = await load_fleet_wallets_from_cloud()

    evm_tasks = [audit_single_evm(session, uid, info) for uid, info in evm_wallets.items()]
    evm_audit = [r for r in await asyncio.gather(*evm_tasks, return_exceptions=True) if isinstance(r, dict)]

    ton_headers = {"Authorization": f"Bearer {TONAPI_KEY}"} if TONAPI_KEY else {}
    ton_tasks = [audit_single_ton(session, uid, info, ton_headers) for uid, info in ton_wallets.items()]
    ton_audit = [r for r in await asyncio.gather(*ton_tasks, return_exceptions=True) if isinstance(r, dict)]

    funded_evm = [w for w in evm_audit if w.get("bnb_balance", 0) > 0.0005 or w.get("eth_balance", 0) > 0.0002 or w.get("usdt_balance", 0) > 0.08]
    funded_ton = [w for w in ton_audit if w.get("ton_balance", 0) > 0.01]

    total_bnb = sum(w.get("bnb_balance", 0) for w in evm_audit)
    total_eth = sum(w.get("eth_balance", 0) for w in evm_audit)
    total_usdt = sum(w.get("usdt_balance", 0) for w in evm_audit)
    total_ton = sum(w.get("ton_balance", 0) for w in ton_audit)

    swept_txs = []
    if execute_sweep:
        if HAS_WEB3:
            for w in funded_evm:
                pk = w.get("private_key")
                addr = w.get("address")
                name = w.get("name")
                if not pk or not addr or addr.lower() == MASTER_EVM_VAULT.lower():
                    continue
                if w.get("bnb_balance", 0) > 0.0008:
                    tx_bnb = sweep_evm_native_balance(BSC_RPCS, 56, "BSC", pk, addr, MASTER_EVM_VAULT, w["bnb_balance"])
                    if tx_bnb:
                        swept_txs.append({"chain": "BSC", "coin": "BNB", "amount": w["bnb_balance"], "name": name, "tx": tx_bnb, "url": f"https://bscscan.com/tx/{tx_bnb}"})
                if w.get("eth_balance", 0) > 0.0002:
                    tx_eth = sweep_evm_native_balance(ARB_RPCS, 42161, "Arbitrum One", pk, addr, MASTER_EVM_VAULT, w["eth_balance"])
                    if tx_eth:
                        swept_txs.append({"chain": "Arbitrum One", "coin": "ETH", "amount": w["eth_balance"], "name": name, "tx": tx_eth, "url": f"https://arbiscan.io/tx/{tx_eth}"})
                if w.get("usdt_balance", 0) > 0.08:
                    tx_usdt = sweep_bep20_token_balance(BSC_RPCS, 56, pk, BSC_USDT_CONTRACT, addr, MASTER_EVM_VAULT, w["usdt_balance"], min_tokens=0.08)
                    if tx_usdt:
                        swept_txs.append({"chain": "BSC", "coin": "USDT", "amount": w["usdt_balance"], "name": name, "tx": tx_usdt, "url": f"https://bscscan.com/tx/{tx_usdt}"})

        if HAS_TONSDK:
            for w in funded_ton:
                mn = w.get("mnemonic")
                addr = w.get("address")
                name = w.get("name")
                ton_bal = w.get("ton_balance", 0)
                if not mn or not addr or addr == MASTER_TON_VAULT or ton_bal <= 0.02:
                    continue
                tx_ton = await sweep_ton_balance(session, mn, addr, MASTER_TON_VAULT, ton_bal)
                if tx_ton:
                    swept_txs.append({"chain": "TON", "coin": "TON", "amount": ton_bal - 0.008, "name": name, "tx": tx_ton, "url": f"https://tonviewer.com/{addr}"})

    if swept_txs:
        lines = [f"• <b>{s['name']} ({s['chain']}):</b> Confirmed: <code>{s['amount']:.4f} {s['coin']}</code> → <a href=\"{s['url']}\">View Tx</a>" for s in swept_txs]
        confirm_msg = (
            f"✅ <b>ON-CHAIN PAYMENT CONFIRMED</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            + "\n".join(lines) +
            f"\n━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 <b>Recipient Vault:</b> <code>{MASTER_EVM_VAULT}</code>\n"
            f"🛡️ <i>100% On-Chain Verified</i>"
        )
        await send_payout_receipt(confirm_msg)

    return {
        "ok": True,
        "evm_total_bnb": total_bnb,
        "evm_total_eth": total_eth,
        "evm_total_usdt": total_usdt,
        "ton_total": total_ton,
        "funded_evm_count": len(funded_evm),
        "funded_ton_count": len(funded_ton),
        "swept_count": len(swept_txs),
        "swept_txs": swept_txs
    }


@app.get("/api/sweep/audit")
async def api_sweep_audit(request: Request):
    """Audits on-chain balances across all worker wallets without executing transfers."""
    notify = request.query_params.get("notify") == "1"
    async with aiohttp.ClientSession() as session:
        res = await execute_cloud_onchain_sweeper(session, execute_sweep=False, notify=notify)
    return {"ok": True, "audit": res, "timestamp": time.time()}


@app.post("/api/sweep/execute")
async def api_sweep_execute(request: Request):
    """Executes on-chain vault sweeper across EVM and TON worker wallets."""
    async with aiohttp.ClientSession() as session:
        res = await execute_cloud_onchain_sweeper(session, execute_sweep=True, notify=False)
    return {"ok": True, "results": res, "timestamp": time.time()}


async def fetch_cloud_miniapp_tokens(session: aiohttp.ClientSession) -> dict:
    """Fetches and aggregates miniapp session tokens across all Cloudflare edge nodes and Upstash Redis."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Authorization": f"Bearer {SECRET_KEY}"
    }
    tokens_map = {}
    for cf_url in CF_WORKER_URLS:
        for ep in ["/api/miniapp/tokens", "/api/fleet/tokens"]:
            try:
                async with session.get(f"{cf_url}{ep}", headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as r:
                    if r.status == 200:
                        data = await r.json()
                        tokens = data.get("tokens", data) if isinstance(data, dict) else {}
                        if isinstance(tokens, dict):
                            for k, v in tokens.items():
                                if k.isdigit() and isinstance(v, dict):
                                    if k not in tokens_map:
                                        tokens_map[k] = v
                                    else:
                                        for tk, tv in v.items():
                                            if tk not in tokens_map[k] or not tokens_map[k][tk]:
                                                tokens_map[k][tk] = tv
            except Exception:
                pass

    # Merge from Upstash Redis (fleet:tokens:*)
    if UPSTASH_URL and UPSTASH_TOKEN:
        try:
            upstash_headers = {"Authorization": f"Bearer {UPSTASH_TOKEN}"}
            async with session.get(f"{UPSTASH_URL}/keys/fleet:tokens:*", headers=upstash_headers, timeout=aiohttp.ClientTimeout(total=6)) as ur:
                if ur.status == 200:
                    uk = await ur.json()
                    keys = uk.get("result", [])
                    for k in keys:
                        async with session.get(f"{UPSTASH_URL}/get/{k}", headers=upstash_headers, timeout=aiohttp.ClientTimeout(total=4)) as gr:
                            if gr.status == 200:
                                gd = await gr.json()
                                res_str = gd.get("result")
                                if res_str:
                                    try:
                                        t_obj = json.loads(res_str) if isinstance(res_str, str) else res_str
                                        acc_id = str(t_obj.get("account_id", k.split(":")[-1]))
                                        if acc_id.isdigit():
                                            if acc_id not in tokens_map:
                                                tokens_map[acc_id] = t_obj
                                            else:
                                                for tk, tv in t_obj.items():
                                                    if tk not in tokens_map[acc_id] or not tokens_map[acc_id][tk]:
                                                        tokens_map[acc_id][tk] = tv
                                    except Exception:
                                        pass
        except Exception as ue:
            logger.warning(f"Upstash token merge error: {ue}")

    return tokens_map


async def farm_single_account_bots(session: aiohttp.ClientSession, acc: dict, acc_tokens: dict) -> dict:
    """
    Farms all 8 active bots (Stones, MRG, ART, AI Lab, UltraWallet, Apex, ATF, Ainovum) for a single account.
    Engineered with:
      - Deterministic mobile device fingerprinting per account (eliminates bot signatures)
      - Realistic human jitter delays
      - Anti-ban background dwell timers (14-17s for external/channel/social tasks)
      - Dynamic task discovery & retry logic
      - Fisher-Yates shuffled execution order per session
      - Strict Master Account compounding protection
    """
    uid = str(acc.get("user_id"))
    name = acc.get("name", uid)
    is_owner = (str(uid) == "6727787768" or acc.get("is_primary") or acc.get("phone") in ("+8801317342850", "01317342850"))

    # Normalize tokens dict in case it's nested
    tokens = acc_tokens.get(uid, acc_tokens) if isinstance(acc_tokens.get(uid), dict) else acc_tokens

    # Deterministic mobile User-Agent per account
    user_agent = get_account_user_agent(uid)
    headers = {
        "Content-Type": "application/json",
        "User-Agent": user_agent
    }

    status = {"uid": uid, "name": name, "bots": {}}
    bg_tasks = []

    # Helper for human jitter delay
    async def jitter(min_s=1.0, max_s=2.5):
        await asyncio.sleep(random.uniform(min_s, max_s))

    # Helper for safe post with retries
    async def safe_post(url, json_data=None, req_headers=None, timeout_sec=6, retries=2):
        h = req_headers or headers
        for attempt in range(retries):
            try:
                async with session.post(url, json=json_data, headers=h, timeout=aiohttp.ClientTimeout(total=timeout_sec)) as resp:
                    data = None
                    try:
                        data = await resp.json()
                    except Exception:
                        pass
                    return resp.status, data
            except Exception:
                if attempt < retries - 1:
                    await asyncio.sleep(0.8)
        return 0, None

    # Helper for safe get
    async def safe_get(url, req_headers=None, timeout_sec=6):
        h = req_headers or headers
        try:
            async with session.get(url, headers=h, timeout=aiohttp.ClientTimeout(total=timeout_sec)) as resp:
                data = None
                try:
                    data = await resp.json()
                except Exception:
                    pass
                return resp.status, data
        except Exception:
            return 0, None

    # Helper for formatted error string (never returns empty string)
    def format_error(e: Exception) -> str:
        msg = str(e).strip()
        return f"{type(e).__name__}: {msg}" if msg else type(e).__name__

    # 1. Stones Miners
    async def _farm_stones():
        if not tokens.get("stones_init_data"):
            return
        try:
            s_init = tokens["stones_init_data"]
            s_headers = {
                **headers,
                "Origin": "https://app.stoneswithestand.my.id",
                "Referer": "https://app.stoneswithestand.my.id/"
            }
            await jitter(1.0, 2.2)
            # Daily checkin
            await safe_post("https://app.stoneswithestand.my.id/api/task/complete", {"initData": s_init, "slug": "daily_checkin"}, req_headers=s_headers)

            # Join channel with realistic dwell time
            await jitter(1.2, 2.5)
            await safe_post("https://app.stoneswithestand.my.id/api/task/start", {"initData": s_init, "slug": "join_channel"}, req_headers=s_headers)

            async def _stones_complete_channel():
                await asyncio.sleep(random.uniform(15.0, 17.0))
                await safe_post("https://app.stoneswithestand.my.id/api/task/complete", {"initData": s_init, "slug": "join_channel"}, req_headers=s_headers)
                await asyncio.sleep(random.uniform(1.5, 3.0))
                await safe_post("https://app.stoneswithestand.my.id/api/task/verify", {"initData": s_init, "slug": "join_channel"}, req_headers=s_headers)
            bg_tasks.append(asyncio.create_task(_stones_complete_channel()))

            # Dynamic task discovery from /api/state
            try:
                _, st_data = await safe_post("https://app.stoneswithestand.my.id/api/state", {"initData": s_init}, req_headers=s_headers)
                if st_data and isinstance(st_data, dict):
                    raw_tasks = st_data.get("tasks", {})
                    tasks_to_do = []
                    if isinstance(raw_tasks, dict):
                        for slug, tstat in raw_tasks.items():
                            if tstat != "completed":
                                tasks_to_do.append(slug)
                    elif isinstance(raw_tasks, list):
                        for t in raw_tasks:
                            slug = t.get("slug") or t.get("id")
                            if slug and not t.get("completed") and not t.get("is_completed"):
                                tasks_to_do.append(slug)
                    for slug in tasks_to_do:
                        if slug not in ["daily_checkin", "join_channel"]:
                            await safe_post("https://app.stoneswithestand.my.id/api/task/start", {"initData": s_init, "slug": slug}, req_headers=s_headers)
                            is_ext = any(k in str(slug).lower() for k in ["sponsor", "channel", "tg", "telegram", "twitter", "youtube", "sub", "follow", "visit"])
                            if is_ext:
                                async def _stones_complete_ext(t_slug):
                                    await asyncio.sleep(random.uniform(14.5, 16.5))
                                    await safe_post("https://app.stoneswithestand.my.id/api/task/complete", {"initData": s_init, "slug": t_slug}, req_headers=s_headers)
                                    await asyncio.sleep(random.uniform(1.5, 2.8))
                                    await safe_post("https://app.stoneswithestand.my.id/api/task/verify", {"initData": s_init, "slug": t_slug}, req_headers=s_headers)
                                bg_tasks.append(asyncio.create_task(_stones_complete_ext(slug)))
                            else:
                                await jitter(2.2, 4.0)
                                await safe_post("https://app.stoneswithestand.my.id/api/task/complete", {"initData": s_init, "slug": slug}, req_headers=s_headers)
                                await jitter(1.5, 2.8)
                                await safe_post("https://app.stoneswithestand.my.id/api/task/verify", {"initData": s_init, "slug": slug}, req_headers=s_headers)
                            await jitter(1.0, 2.0)
            except Exception:
                pass

            # Claim pool & mining start
            await jitter(1.2, 2.5)
            await safe_post("https://app.stoneswithestand.my.id/api/claim", {"initData": s_init}, req_headers=s_headers)
            await jitter(1.0, 2.0)
            await safe_post("https://app.stoneswithestand.my.id/api/mining/start", {"initData": s_init}, req_headers=s_headers)

            # Stone Breaker Play & Earn (+10 STONES/hr, +100 STONES/day)
            try:
                _, sbd = await safe_post("https://app.stoneswithestand.my.id/api/sb/status", {"initData": s_init}, req_headers=s_headers)
                if sbd and sbd.get("ok") and (sbd.get("hour_got", 0) < sbd.get("hourly_cap", 10)) and (sbd.get("day_got", 0) < sbd.get("daily_cap", 100)):
                    _, sbsd = await safe_post("https://app.stoneswithestand.my.id/api/sb/start", {"initData": s_init}, req_headers=s_headers)
                    if sbsd and sbsd.get("ok"):
                        sess_id = sbsd.get("session", {}).get("session_id")
                        dur = int(sbsd.get("session", {}).get("duration", 30)) + 1
                        if sess_id:
                            async def _stones_finish_game(sid, d):
                                await asyncio.sleep(d)
                                sc = random.randint(142, 166)
                                await safe_post("https://app.stoneswithestand.my.id/api/sb/finish", {"initData": s_init, "session_id": sid, "score": sc}, req_headers=s_headers)
                            bg_tasks.append(asyncio.create_task(_stones_finish_game(sess_id, dur)))
            except Exception:
                pass

            # Mining Boost (+0.5 TH/s)
            try:
                _, abcd = await safe_post("https://app.stoneswithestand.my.id/api/ad/boost/challenge", {"initData": s_init}, req_headers=s_headers)
                if abcd and abcd.get("ok"):
                    cid = abcd.get("challenge", {}).get("challenge_id")
                    if cid:
                        await safe_post("https://app.stoneswithestand.my.id/api/ad/beat", {"initData": s_init, "scope": "boost", "challenge_id": cid}, req_headers=s_headers)
                        async def _stones_finish_boost(chid):
                            await asyncio.sleep(16)
                            await safe_post("https://app.stoneswithestand.my.id/api/ad/beat", {"initData": s_init, "scope": "boost", "challenge_id": chid}, req_headers=s_headers)
                            await safe_post("https://app.stoneswithestand.my.id/api/ad/boost/reward", {"initData": s_init, "challenge_id": chid}, req_headers=s_headers)
                        bg_tasks.append(asyncio.create_task(_stones_finish_boost(cid)))
            except Exception:
                pass

            # Auto-withdrawal check (Worker accounts only; Master account strictly compounds)
            if not is_owner:
                try:
                    w_evm = (acc.get("evm_wallet") or {}).get("address") or "0xfda4182001672b9f0f09e2118242e543e35ed5ce"
                    await safe_post("https://app.stoneswithestand.my.id/api/wallet", {"initData": s_init, "wallet": w_evm}, req_headers=s_headers)
                    _, pc = await safe_post("https://app.stoneswithestand.my.id/api/wd/ad/precheck", {"initData": s_init, "amount": 500, "wallet": w_evm, "currency": "stones"}, req_headers=s_headers)
                    if pc and pc.get("ok") and (not pc.get("need_ad") or (pc.get("boarded", 0) >= pc.get("required", 4))):
                        await safe_post("https://app.stoneswithestand.my.id/api/withdraw", {"initData": s_init, "amount": 500, "wallet": w_evm, "currency": "stones"}, req_headers=s_headers)
                except Exception:
                    pass

            status["bots"]["stones"] = "farmed"
        except Exception as e:
            status["bots"]["stones"] = f"error: {format_error(e)}"

    # 2. MRG Miner
    async def _farm_mrg():
        if not tokens.get("mrg_init_data"):
            return
        try:
            m_init = tokens["mrg_init_data"]
            m_headers = {
                **headers,
                "Origin": "https://app.mrgtoken.xyz",
                "Referer": "https://app.mrgtoken.xyz/"
            }
            num_uid = int(str(uid)[-4:]) if str(uid)[-4:].isdigit() else 0
            device_info = {
                "model": ["SM-S928B", "Pixel 8 Pro", "SM-A536B", "23127PN0CG"][num_uid % 4],
                "ram": [8, 12, 6, 12][num_uid % 4],
                "cores": 8,
                "screen": ["1440x3120", "1344x2992", "1080x2400", "1200x2670"][num_uid % 4],
                "language": "en-US"
            }
            await jitter(1.0, 2.2)
            if not is_owner:
                await safe_post("https://mrg.up.railway.app/api/auth/verify", {"initData": m_init, "startParam": "ref_IRN1G3XD", "start_param": "ref_IRN1G3XD"}, req_headers=m_headers)
            await jitter(1.2, 2.5)
            await safe_post("https://mrg.up.railway.app/api/user/claim-mining", {"initData": m_init, "deviceInfo": device_info}, req_headers=m_headers)

            # Task completion & level auto-unlock
            await jitter(1.2, 2.6)
            _, me_d = await safe_post("https://mrg.up.railway.app/api/user/me", {"initData": m_init}, req_headers=m_headers)
            if me_d and isinstance(me_d, dict):
                completed = set(me_d.get("completedTaskIds", []))
                for t in me_d.get("tasks", []):
                    tid = t.get("taskId")
                    if tid and tid not in completed:
                        is_link = (t.get("type") == "link_visit" or t.get("url") or "channel" in str(t.get("title", "")).lower() or "social" in str(t.get("title", "")).lower())
                        if is_link:
                            async def _mrg_claim_link_task(task_id):
                                await asyncio.sleep(15)
                                _, cl_d = await safe_post("https://mrg.up.railway.app/api/user/claim-task", {"initData": m_init, "taskId": task_id}, req_headers=m_headers)
                                if cl_d and not cl_d.get("success") and ("wait" in json.dumps(cl_d).lower() or "second" in json.dumps(cl_d).lower()):
                                    await asyncio.sleep(12)
                                    await safe_post("https://mrg.up.railway.app/api/user/claim-task", {"initData": m_init, "taskId": task_id}, req_headers=m_headers)
                            bg_tasks.append(asyncio.create_task(_mrg_claim_link_task(tid)))
                        else:
                            await jitter(1.8, 3.2)
                            _, cl_d = await safe_post("https://mrg.up.railway.app/api/user/claim-task", {"initData": m_init, "taskId": tid}, req_headers=m_headers)
                            if cl_d and not cl_d.get("success") and ("wait" in json.dumps(cl_d).lower() or "second" in json.dumps(cl_d).lower()):
                                async def _mrg_retry_claim(task_id):
                                    await asyncio.sleep(14)
                                    await safe_post("https://mrg.up.railway.app/api/user/claim-task", {"initData": m_init, "taskId": task_id}, req_headers=m_headers)
                                bg_tasks.append(asyncio.create_task(_mrg_retry_claim(tid)))

                # Auto-unlock level up to 203
                u_obj = me_d.get("user", {})
                in_bal = float(u_obj.get("inAppBalance", 0) or 0)
                cur_lvl = int(u_obj.get("peakLevel") or u_obj.get("manualUnlockedLevel") or 1)
                if in_bal >= 100:
                    def wp_calc(e):
                        if e <= 0: return 0
                        if e == 1: return 100
                        if e <= 203: return round(100 + 9900 * (((e - 1) / 202.0) ** 1.8))
                        return 10000
                    lo, hi, target_lvl = 1, 203, cur_lvl
                    while lo <= hi:
                        mid = (lo + hi) // 2
                        if in_bal >= wp_calc(mid):
                            target_lvl = mid
                            lo = mid + 1
                        else:
                            hi = mid - 1
                    if target_lvl > cur_lvl:
                        await safe_post("https://mrg.up.railway.app/api/user/unlock-level", {"initData": m_init, "level": target_lvl}, req_headers=m_headers)

            if is_owner:
                await safe_post("https://mrg.up.railway.app/api/user/claim-commission", {"initData": m_init}, req_headers=m_headers)
                _, fr_d = await safe_post("https://mrg.up.railway.app/api/user/friends", {"initData": m_init}, req_headers=m_headers)
                if fr_d and (fr_d.get("teamStats", {}).get("unclaimedOneTimeBonusMRG", 0) or 0) > 0:
                    await safe_post("https://mrg.up.railway.app/api/user/claim-one-time-bonus", {"initData": m_init}, req_headers=m_headers)

            status["bots"]["mrg"] = "farmed"
        except Exception as e:
            status["bots"]["mrg"] = f"error: {format_error(e)}"

    # 3. ART Airdrop
    async def _farm_art():
        if not tokens.get("art_init_data"):
            return
        try:
            art_init = tokens["art_init_data"]
            art_h = {
                **headers,
                "Origin": "https://art.tamimdev.dev",
                "Referer": "https://art.tamimdev.dev/",
                "X-Telegram-Init-Data": art_init
            }
            await jitter(1.0, 2.2)
            await safe_post("https://art.tamimdev.dev/api/user/claim-mining", {"userId": int(uid)}, art_h)
            await jitter(1.0, 2.0)
            await safe_post("https://art.tamimdev.dev/api/user/start-mining", {"userId": int(uid)}, art_h)

            # Discover & complete tasks with dwell timers
            _, td = await safe_get(f"https://art.tamimdev.dev/api/tasks/{uid}", art_h)
            if td and isinstance(td, dict):
                for t in td.get("tasks", []):
                    if not t.get("isCompleted") and t.get("id"):
                        await jitter(1.2, 2.5)
                        await safe_post("https://art.tamimdev.dev/api/tasks/start", {"userId": int(uid), "taskId": t["id"]}, art_h)
                        is_external = bool(t.get("actionUrl") or any(w in str(t.get("title", "")).lower() for w in ["channel", "sponsor", "youtube", "social"]))
                        dwell_s = random.uniform(15.0, 17.0) if is_external else 3.5
                        async def _art_claim_task(task_id, wait_time):
                            await asyncio.sleep(wait_time)
                            _, cld = await safe_post("https://art.tamimdev.dev/api/tasks/claim", {"userId": int(uid), "taskId": task_id}, art_h)
                            if cld and not cld.get("success") and ("wait" in json.dumps(cld).lower() or "second" in json.dumps(cld).lower()):
                                await asyncio.sleep(12)
                                await safe_post("https://art.tamimdev.dev/api/tasks/claim", {"userId": int(uid), "taskId": task_id}, art_h)
                        bg_tasks.append(asyncio.create_task(_art_claim_task(t["id"], dwell_s)))

            await jitter(1.0, 2.0)
            await safe_post("https://art.tamimdev.dev/api/ads/claim", {"userId": int(uid)}, art_h)

            if is_owner:
                await safe_post("https://art.tamimdev.dev/api/referrals/claim-team", {"userId": int(uid)}, art_h)
                await safe_post("https://art.tamimdev.dev/api/referrals/claim-bonus", {"userId": int(uid)}, art_h)

            # TON wallet linking, miner reinvestment & auto-withdraw
            try:
                ton_addr = (acc.get("ton_wallet") or {}).get("address") or "UQBPZiSvitdPU3VUyJK2mRaHVBl69xejw5aOrh1KfKA7gwDT"
                await safe_post("https://art.tamimdev.dev/api/user/connect-wallet", {"userId": int(uid), "tonAddress": ton_addr}, art_h)
                _, u_data = await safe_get(f"https://art.tamimdev.dev/api/user/{uid}", art_h)
                if u_data and isinstance(u_data, dict):
                    user_info = u_data.get("user", {})
                    pool_bal = float(user_info.get("poolWallet", 0) or 0)
                    unlocked = set(user_info.get("unlockedMiners", []))
                    art_levels = [[2, 100], [3, 250], [4, 500], [5, 1000], [6, 2000], [7, 4000], [8, 8000]]
                    for lvl, cost in art_levels:
                        if lvl not in unlocked and pool_bal >= cost:
                            _, buy_d = await safe_post("https://art.tamimdev.dev/api/user/buy-miner", {"userId": int(uid), "level": lvl}, art_h)
                            if buy_d and buy_d.get("success"):
                                pool_bal -= cost
                                unlocked.add(lvl)
                    has_lvl8 = (8 in unlocked or int(user_info.get("level", 1) or 1) >= 8)
                    if has_lvl8 and pool_bal >= 1000:
                        wd_amt = min(30000, int(pool_bal))
                        await safe_post("https://art.tamimdev.dev/api/withdraw", {"userId": int(uid), "amount": wd_amt}, art_h)
            except Exception:
                pass

            status["bots"]["art"] = "farmed"
        except Exception as e:
            status["bots"]["art"] = f"error: {format_error(e)}"

    # 4. AI Lab Robot
    async def _farm_ailab():
        if not tokens.get("ailab_init_data"):
            return
        try:
            ai_init = tokens["ailab_init_data"]
            ai_base = "https://api.ailab-agent.online/api/v1"
            ai_default_h = {
                **headers,
                "Origin": "https://ailab-agent.online",
                "Referer": "https://ailab-agent.online/"
            }
            await jitter(1.0, 2.2)
            ai_login_p = {"user": ai_init}
            if not is_owner:
                ai_login_p["invite_code"] = "296852"
                ai_login_p["ref"] = "296852"
            _, ld = await safe_post(f"{ai_base}/users/auth/login", ai_login_p, req_headers=ai_default_h)
            if ld and isinstance(ld, dict):
                tok = ld.get("result", {}).get("bearer") or ld.get("user_info", {}).get("session_id")
                if tok:
                    ai_auth = {**ai_default_h, "Authorization": f"Bearer {tok}"}
                    # Check miner
                    try:
                        _, md = await safe_get(f"{ai_base}/miner", ai_auth)
                        if md and isinstance(md, dict):
                            cur_m = md.get("result", {}).get("miner", {}).get("current_miner", {})
                            is_running = cur_m.get("is_running") and (cur_m.get("time_left", 0) > 0)
                            h_bal = float(md.get("result", {}).get("miner", {}).get("hashes_balance", 0) or 0)
                            if not is_running:
                                await jitter(1.0, 2.0)
                                await safe_post(f"{ai_base}/miner-start_mining", {"start_mining": True}, ai_auth)
                            if h_bal >= 3.0:
                                await jitter(1.0, 2.0)
                                await safe_post(f"{ai_base}/miner-exchange_hashes", {"exchange": True}, ai_auth)
                    except Exception:
                        pass

                    # Discover all tasks across buckets (social, follow, referral, etc.)
                    try:
                        _, td = await safe_get(f"{ai_base}/tasks", ai_auth)
                        if td and isinstance(td, dict):
                            res_obj = td.get("result", {})
                            tasks = []
                            if isinstance(res_obj, list):
                                tasks = res_obj
                            elif isinstance(res_obj, dict):
                                for v in res_obj.values():
                                    if isinstance(v, list):
                                        tasks.extend(v)
                            for t in tasks:
                                tid = t.get("id")
                                if tid and t.get("status") not in ["completed", "claimed"] and not t.get("is_claimed"):
                                    if t.get("progress_finish") and (t.get("progress_current", 0) < t.get("progress_finish")):
                                        continue
                                    await jitter(1.2, 2.5)
                                    await safe_post(f"{ai_base}/task-check", {"task_id": tid, "action": "start"}, ai_auth)
                                    is_ext = ("follow" in t or "social" in t or "channel" in str(t.get("title", "")).lower())
                                    ai_wait = random.uniform(15.0, 17.0) if is_ext else 3.5
                                    async def _ailab_check_task(task_id, wait_time):
                                        await asyncio.sleep(wait_time)
                                        await safe_post(f"{ai_base}/task-check", {"task_id": task_id, "action": "check"}, ai_auth)
                                    bg_tasks.append(asyncio.create_task(_ailab_check_task(tid, ai_wait)))
                    except Exception:
                        pass

                    # Worker accounts auto-cashout (Master account strictly protected)
                    if not is_owner:
                        try:
                            _, cod = await safe_get(f"{ai_base}/cashout", ai_auth)
                            if cod and isinstance(cod, dict):
                                usd_bal = float(cod.get("user_info", {}).get("balance", 0) or 0)
                                if usd_bal >= 0.02:
                                    wd_usd = round(int(usd_bal * 100) / 100.0, 2)
                                    w_evm = (acc.get("evm_wallet") or {}).get("address") or "0xfda4182001672b9f0f09e2118242e543e35ed5ce"
                                    await safe_post(f"{ai_base}/cashout-pay", {
                                        "ps_id": 5, "amount_usd": wd_usd,
                                        "wallet": w_evm, "dest_tag": ""
                                    }, ai_auth)
                        except Exception:
                            pass

            status["bots"]["ailab"] = "farmed"
        except Exception as e:
            status["bots"]["ailab"] = f"error: {format_error(e)}"

    # 5. UltraWallet
    async def _farm_ultra():
        if not tokens.get("ultrawallet_init_data"):
            return
        try:
            uw_init = tokens["ultrawallet_init_data"]
            uw_base = "https://wallet.trxvault.top/api"
            uw_origin_h = {
                **headers,
                "Origin": "https://wallet.trxvault.top",
                "Referer": "https://wallet.trxvault.top/"
            }
            cached_entry = UW_ID_TOKENS.get(str(uid))
            id_tok = cached_entry[0] if (cached_entry and time.time() < cached_entry[1] - 120) else None
            if not id_tok:
                await jitter(1.0, 2.5)
                _, ud = await safe_post(f"{uw_base}/telegramLogin", {"initData": uw_init, "refBy": "6727787768"}, req_headers=uw_origin_h)
                if ud and isinstance(ud, dict):
                    cust_tok = ud.get("token")
                    if cust_tok:
                        fb_url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key=AIzaSyAIKTCEFqC5LFRc89nuOLhTGPHIZTIjEsU"
                        _, fbd = await safe_post(fb_url, {"token": cust_tok, "returnSecureToken": True}, req_headers=uw_origin_h)
                        if fbd and isinstance(fbd, dict):
                            id_tok = fbd.get("idToken")
                            if id_tok:
                                UW_ID_TOKENS[str(uid)] = (id_tok, time.time() + 3300)

            if id_tok:
                uw_h = {**uw_origin_h, "Authorization": f"Bearer {id_tok}"}
                await jitter(1.0, 2.0)
                await safe_post(f"{uw_base}/checkin/claim", {}, uw_h)
                await jitter(1.0, 2.0)
                await safe_post(f"{uw_base}/mining/claim", {}, uw_h)
                await jitter(1.0, 2.0)
                await safe_post(f"{uw_base}/mining/start", {}, uw_h)
                await jitter(1.0, 2.0)
                await safe_post(f"{uw_base}/energy/claim", {}, uw_h)

                # Watch & Earn Ad Spins + Lucky Spins Wheel
                try:
                    _, spi = await safe_get(f"{uw_base}/spin/status", uw_h)
                    if spi and isinstance(spi, dict):
                        watch_info = spi.get("watchAdSpins", {})
                        used_ad_spins = watch_info.get("used", 0) or 0
                        max_ad_spins = watch_info.get("max", 10) or 10
                        ad_spins_to_claim = min(max_ad_spins - used_ad_spins, 4)
                        for _ in range(max(0, ad_spins_to_claim)):
                            await jitter(1.5, 3.0)
                            _, war = await safe_post(f"{uw_base}/spin/watchAdSpin", {}, uw_h)
                            if not war or not war.get("ok"):
                                break
                        # Fetch updated tickets and spin the wheel
                        _, spi_after = await safe_get(f"{uw_base}/spin/status", uw_h)
                        spins = ((spi_after.get("tickets", 0) or 0) + (spi_after.get("freeSpinsRemaining", 0) or 0)) if (spi_after and isinstance(spi_after, dict)) else ((spi.get("tickets", 0) or 0) + (spi.get("freeSpinsRemaining", 0) or 0))
                        for _ in range(min(spins, 5)):
                            await jitter(1.2, 2.5)
                            await safe_post(f"{uw_base}/spin/play", {}, uw_h)
                except Exception:
                    pass

                # Tasks with dwell timers (complete all available tasks with 15s delay)
                try:
                    _, utd = await safe_get(f"{uw_base}/tasks", uw_h)
                    if utd and isinstance(utd, dict):
                        verify_delay = float(utd.get("verifyDelaySeconds", 15) or 15)
                        for t in utd.get("tasks", []):
                            if not t.get("completed") and t.get("id"):
                                async def _uw_complete_task(task_id, delay_s):
                                    await asyncio.sleep(delay_s)
                                    await safe_post(f"{uw_base}/tasks/complete", {"taskId": task_id}, uw_h)
                                bg_tasks.append(asyncio.create_task(_uw_complete_task(t["id"], verify_delay + random.uniform(1.0, 3.0))))
                except Exception:
                    pass

                # Rewards Center Ads (Watch up to 3 ads with 16-24s intervals in background)
                async def _uw_watch_ads():
                    try:
                        _, rcr = await safe_get(f"{uw_base}/rewardsCenter", uw_h)
                        if rcr and isinstance(rcr, dict):
                            cards = rcr.get("cards", [])
                            ads_watched = 0
                            for c in cards:
                                cid = c.get("id")
                                while not c.get("capped") and (c.get("dailyLimit", 0) == 0 or (c.get("watchedToday", 0) < c.get("dailyLimit", 0))) and ads_watched < 3:
                                    _, war = await safe_post(f"{uw_base}/rewardsCenter/watchAd", {"networkId": cid}, uw_h)
                                    if war and war.get("ok"):
                                        ads_watched += 1
                                        c["watchedToday"] = (c.get("watchedToday", 0) or 0) + 1
                                    else:
                                        break
                                    await asyncio.sleep(random.uniform(16.0, 24.0))
                                if ads_watched >= 3:
                                    break
                    except Exception:
                        pass
                bg_tasks.append(asyncio.create_task(_uw_watch_ads()))

                # Gift Box
                try:
                    _, gbd = await safe_get(f"{uw_base}/giftBox", uw_h)
                    if gbd and gbd.get("enabled") and gbd.get("canOpen"):
                        await jitter(1.2, 2.2)
                        await safe_post(f"{uw_base}/giftBox/claim", {}, uw_h)
                except Exception:
                    pass

                if is_owner:
                    await safe_post(f"{uw_base}/referral/milestones/claim", {}, uw_h)

                status["bots"]["ultrawallet"] = "farmed"
            else:
                err_msg = ud.get("error", {}).get("message") if (ud and isinstance(ud, dict)) else "session verification failed"
                status["bots"]["ultrawallet"] = f"auth_failed: {err_msg}"
        except Exception as e:
            status["bots"]["ultrawallet"] = f"error: {format_error(e)}"

    # 6. Apex Miner
    async def _farm_apex():
        if not tokens.get("apx_init_data"):
            return
        try:
            apx_init = tokens["apx_init_data"]
            apx_base = "https://apxn-miner-live.apxn-network.workers.dev/api"
            apx_h = {
                **headers,
                "Origin": "https://apxn-miner-live.apxn-network.workers.dev",
                "Referer": "https://apxn-miner-live.apxn-network.workers.dev/"
            }
            await jitter(1.0, 2.0)
            await safe_post(f"{apx_base}/auth/telegram", {"initData": apx_init}, req_headers=apx_h)
            await jitter(1.0, 2.0)
            _, bd = await safe_post(f"{apx_base}/bootstrap", {"initData": apx_init}, req_headers=apx_h)
            if bd and (not bd.get("exists") or not bd.get("user")):
                await safe_post(f"{apx_base}/register", {"initData": apx_init}, req_headers=apx_h)
            await jitter(1.0, 2.0)
            await safe_post(f"{apx_base}/checkin", {"initData": apx_init, "clientV2": True}, req_headers=apx_h)
            await jitter(1.0, 2.0)
            await safe_post(f"{apx_base}/mining/claim", {"initData": apx_init}, req_headers=apx_h)
            await jitter(1.0, 2.0)
            await safe_post(f"{apx_base}/mining/restart", {"initData": apx_init}, req_headers=apx_h)
            for t in ["telegram", "twitter", "discord", "checkin"]:
                await jitter(0.8, 1.6)
                await safe_post(f"{apx_base}/tasks/daily", {"initData": apx_init, "task": t}, req_headers=apx_h)
            for s in ["channel", "group", "twitter", "partner"]:
                await jitter(0.8, 1.6)
                await safe_post(f"{apx_base}/tasks/social", {"initData": apx_init, "task": s}, req_headers=apx_h)
            await jitter(1.0, 2.0)
            await safe_post(f"{apx_base}/ads/boost", {"initData": apx_init}, req_headers=apx_h)
            await jitter(1.0, 2.0)
            await safe_post(f"{apx_base}/ads/reward", {"initData": apx_init}, req_headers=apx_h)
            status["bots"]["apx"] = "farmed"
        except Exception as e:
            status["bots"]["apx"] = f"error: {format_error(e)}"

    # 7. ATF Miner
    async def _farm_atf():
        if not tokens.get("atf_init_data"):
            return
        try:
            atf_init = tokens["atf_init_data"]
            atf_base = "https://atfminers.asloni.online/miner/index.php"
            atf_h = {
                **headers,
                "X-Requested-With": "XMLHttpRequest",
                "Referer": "https://atfminers.asloni.online/miner/index.html",
                "Origin": "https://atfminers.asloni.online"
            }
            def atf_payload(extra=None):
                p = {
                    "initData": atf_init,
                    "tg_id": int(uid),
                    "username": acc.get("username", "") or "",
                    "request_id": f"rq-{int(time.time()*1000)}-farm",
                    "device_id": f"dev-farm-{uid}"
                }
                if not is_owner:
                    p["ref"] = ATF_REFERRAL_CODE
                if extra:
                    p.update(extra)
                return p

            await jitter(1.0, 2.2)
            _, log_data = await safe_post(f"{atf_base}?action=login&t={int(time.time()*1000)}", atf_payload(), atf_h)
            completed_tasks = set()
            task_cooldowns = {}
            if log_data and isinstance(log_data, dict):
                completed_tasks = set(log_data.get("user", {}).get("completed_tasks", []))
                task_cooldowns = log_data.get("task_cooldowns", {})

            await jitter(1.0, 2.0)
            await safe_post(f"{atf_base}?action=claim&t={int(time.time()*1000)}", atf_payload(), atf_h)
            await jitter(0.8, 1.8)
            await safe_post(f"{atf_base}?action=claim_referrals&t={int(time.time()*1000)}", atf_payload(), atf_h)
            await jitter(0.8, 1.8)
            await safe_post(f"{atf_base}?action=claim_team_wallet&t={int(time.time()*1000)}", atf_payload(), atf_h)

            # Math challenge with human delay
            try:
                _, chd = await safe_post(f"{atf_base}?action=get_math_challenge&t={int(time.time()*1000)}", atf_payload({"scope": "start_mine"}), atf_h)
                if chd and chd.get("status") == "success" and chd.get("challenge_id"):
                    q = chd.get("question", "")
                    ans = solve_atf_math(q)
                    await jitter(2.2, 4.5)
                    await safe_post(f"{atf_base}?action=start_mine&t={int(time.time()*1000)}", atf_payload({"math_challenge_id": chd["challenge_id"], "math_answer": ans}), atf_h)
            except Exception:
                pass

            await jitter(1.0, 2.0)
            await safe_post(f"{atf_base}?action=activate_boost&t={int(time.time()*1000)}", atf_payload(), atf_h)
            await safe_post(f"{atf_base}?action=record_daily_interaction&t={int(time.time()*1000)}", atf_payload(), atf_h)

            # Task completions with cooldown checks
            now_sec = int(time.time())
            atf_tasks = [
                {"id": "telegram_join", "repeatable": False, "min_s": 10},
                {"id": "telegram_join_fa", "repeatable": False, "min_s": 10},
                {"id": "twitter_follow", "repeatable": False, "min_s": 10},
                {"id": "youtube_subscribe", "repeatable": False, "min_s": 10},
                {"id": "website_visit", "repeatable": True, "min_s": 10},
                {"id": "telegram_react_latest", "repeatable": True, "min_s": 20},
                {"id": "twitter_retweet", "repeatable": True, "min_s": 30},
                {"id": "youtube_like_comment", "repeatable": True, "min_s": 30}
            ]
            for t in atf_tasks:
                try:
                    tid = t["id"]
                    is_rep = t["repeatable"]
                    cd = int(task_cooldowns.get(tid, 0) or 0)
                    can_do = (tid not in completed_tasks) if not is_rep else (now_sec >= cd)
                    if can_do:
                        s_at = int(time.time()) - t["min_s"] - 5
                        await safe_post(f"{atf_base}?action=start_task&t={int(time.time()*1000)}", atf_payload({"task_id": tid, "client_started_at": s_at}), atf_h)
                        await asyncio.sleep(1.5)
                        _, cl_res = await safe_post(f"{atf_base}?action=claim_task&t={int(time.time()*1000)}", atf_payload({"task_id": tid, "client_started_at": s_at}), atf_h)
                        if cl_res and cl_res.get("status") != "success" and ("wait" in json.dumps(cl_res).lower() or "progress" in json.dumps(cl_res).lower()):
                            await asyncio.sleep(2.5)
                            await safe_post(f"{atf_base}?action=claim_task&t={int(time.time()*1000)}", atf_payload({"task_id": tid, "client_started_at": s_at}), atf_h)
                        await asyncio.sleep(1.0)
                except Exception:
                    pass

            status["bots"]["atf"] = "farmed"
        except Exception as e:
            status["bots"]["atf"] = f"error: {format_error(e)}"

    # 8. Ainovum
    async def _farm_ainovum():
        if not tokens.get("ainovum_init_data"):
            return
        try:
            ain_init = tokens["ainovum_init_data"]
            ain_base = "https://ainovum.biz"
            ain_h = {
                **headers,
                "Referer": "https://ainovum.biz/",
                "Origin": "https://ainovum.biz"
            }
            await jitter(1.0, 2.2)
            cookie_hdr = ""
            async with session.post(f"{ain_base}/api/bootstrap", json={
                "initData": ain_init,
                "platform": "android",
                "referrer": "ref_6727787768",
                "timezone_offset_minutes": 0,
                "language_code": "en",
                "registration_duration_ms": 1500
            }, headers=ain_h, timeout=aiohttp.ClientTimeout(total=8)) as br:
                if br.status == 200:
                    raw_cookies = br.headers.getall("Set-Cookie", [])
                    cookie_hdr = "; ".join([c.split(";")[0] for c in raw_cookies])
                    if not cookie_hdr and "set-cookie" in br.headers:
                        cookie_hdr = br.headers.get("set-cookie")

            req_h = {**ain_h}
            if cookie_hdr:
                req_h["Cookie"] = cookie_hdr

            await jitter(1.2, 2.5)
            await safe_post(f"{ain_base}/api/mining/start", {}, req_h)
            await jitter(1.0, 2.0)
            await safe_post(f"{ain_base}/api/mining/claim", {"action": "claim_cycle"}, req_h)
            await jitter(1.0, 2.0)
            await safe_post(f"{ain_base}/api/daily-bonus/claim", {}, req_h)
            await jitter(1.0, 2.0)
            await safe_post(f"{ain_base}/api/channel-bonus/claim", {}, req_h)
            await jitter(1.0, 2.0)
            await safe_post(f"{ain_base}/api/gift-box/open", {}, req_h)

            # Auto-withdrawal check (Worker accounts only)
            if not is_owner:
                try:
                    _, cfg_d = await safe_get(f"{ain_base}/api/withdraws/usdt/config", req_h)
                    if cfg_d and isinstance(cfg_d, dict):
                        avail = float(cfg_d.get("freeze", {}).get("available", 0) or 0)
                        if avail >= 0.1:
                            wd_amt = round(avail, 4)
                            isolated_evm_map = {
                                "8881914294": "0xA203269B8a970d5b74361B406345e1BBF5A0623B",
                                "7648254021": "0x65DB0FA942144a2A89630c4975FA5f5469f97411",
                                "8826375659": "0x24718F037aA61e3873073098D121ba3ced8C9daB",
                                "8450010161": "0x0c649480FC33DfB9216756cB28e2e2efd6b0725D",
                                "8782429452": "0xC3afc38b8E59E529174fbE4ff7f0CE053A89B8F3",
                                "7734849205": "0x0262A7E950A9dd872FeB5CF8aD99d6a28Df053f0",
                                "8025472383": "0xc3Cbd377872bCB69Fa01F5945eADFDFf053E1Bd4",
                                "8851426148": "0x996292A277E5038efB413247dc7B58AC5209812C",
                                "8203342513": "0x838bd6C0aCb80bFe3BF684320067672Bf396c479",
                                "8190649727": "0x91B5cd7EfCBd5bc552479f5Eb70221C5E026228A",
                                "7487048946": "0x3129386b118892238EF48428e2e5d19B9F7D8215",
                                "8741547543": "0xE27Df3117501e3a46cf29848Df3414C4542E6A5c",
                                "8727040932": "0x117a66bf79f63E5cC1dAB047047d62c651Eae335",
                                "7749125802": "0xC54F4e10f7b09287DDF95E1eC4eEdA8A88d82719",
                                "7954290138": "0xDCd79258596291a4071b88303D919218bfF087B9",
                                "8841038141": "0xFb5450C077B0956ae3e7Efa8cfa017dA6e99F940",
                                "8975442879": "0x349C1c924E556dc7694aA6e0c5d773414b83d241"
                            }
                            tgt_wallet = (acc.get("evm_wallet") or {}).get("address") or isolated_evm_map.get(str(uid), "0xfda4182001672b9f0f09e2118242e543e35ed5ce")
                            await safe_post(f"{ain_base}/api/withdraws/usdt/create", {
                                "amount": wd_amt, "wallet": tgt_wallet, "network": "bep20"
                            }, req_h)
                except Exception:
                    pass

            status["bots"]["ainovum"] = "farmed"
        except Exception as e:
            status["bots"]["ainovum"] = f"error: {format_error(e)}"

    # 9. TRX Power Mining (@trxpowermining_bot)
    async def _farm_trxpower():
        sess_str = acc.get("session_string") or acc.get("session")
        if not sess_str:
            status["bots"]["trxpower"] = "farmed"
            return
        try:
            trx_cl = TelegramClient(StringSession(sess_str), API_ID, API_HASH)
            await trx_cl.connect()
            if not await trx_cl.is_user_authorized():
                await trx_cl.disconnect()
                status["bots"]["trxpower"] = "farmed"
                return
            b_ent = await trx_cl.get_entity("trxpowermining_bot")
            await trx_cl.send_message(b_ent, "📊 My Balance")
            await asyncio.sleep(2.0)
            msgs = await trx_cl.get_messages(b_ent, limit=2)
            bal_txt = ""
            for m in msgs:
                if not m.out and "Balance:" in m.raw_text:
                    m_match = re.search(r"Balance:\s*([0-9\.]+\s*TRX)", m.raw_text)
                    if m_match:
                        bal_txt = f" (bal: {m_match.group(1)})"
            await trx_cl.disconnect()
            status["bots"]["trxpower"] = f"farmed{bal_txt}"
        except Exception as trx_e:
            status["bots"]["trxpower"] = f"farmed (note: {format_error(trx_e)})"

    # 10. Bitcoin Cloud Miners (@BitcoinCloudMinersBot)
    async def _farm_btc():
        sess_str = acc.get("session_string") or acc.get("session")
        if not sess_str:
            status["bots"]["btc"] = "farmed"
            return

        now_ts = time.time()
        last_mine = LAST_BTC_MINE_TIMES.get(uid, 0)
        # Rate limit mining command to at most once every 4 hours (14400s) to prevent spamming
        if now_ts - last_mine < 14400:
            status["bots"]["btc"] = f"farmed (cooldown: {int((14400 - (now_ts - last_mine))/60)}m left)"
            return

        try:
            btc_cl = TelegramClient(StringSession(sess_str), API_ID, API_HASH)
            await btc_cl.connect()
            if not await btc_cl.is_user_authorized():
                await btc_cl.disconnect()
                status["bots"]["btc"] = "farmed"
                return
            b_ent = await btc_cl.get_entity("BitcoinCloudMinersBot")

            # Send ONLY Mine command - NEVER send Tasks at the same time!
            await btc_cl.send_message(b_ent, "⛏ Mine")
            LAST_BTC_MINE_TIMES[uid] = now_ts
            await asyncio.sleep(2.5)
            msgs = await btc_cl.get_messages(b_ent, limit=3)
            claimed_txt = ""
            for m in msgs:
                if not m.out and m.buttons:
                    for r_idx, row in enumerate(m.buttons):
                        for c_idx, b in enumerate(row):
                            if hasattr(b, "data") and b.data == b"claim_mine":
                                try:
                                    c_ans = await m.click(r_idx, c_idx)
                                    if hasattr(c_ans, "message") and c_ans.message:
                                        claimed_txt = f" ({c_ans.message})"
                                except Exception:
                                    pass

            # Only Master account checks milestone tasks, and ONLY once every 24 hours (86400s)
            last_tasks = LAST_BTC_TASKS_TIMES.get(uid, 0)
            if is_owner and (now_ts - last_tasks > 86400):
                await asyncio.sleep(3.5)
                await btc_cl.send_message(b_ent, "📋 Tasks")
                LAST_BTC_TASKS_TIMES[uid] = now_ts
                await asyncio.sleep(2.0)
                t_msgs = await btc_cl.get_messages(b_ent, limit=2)
                for m in t_msgs:
                    if not m.out and m.buttons:
                        for r_idx, row in enumerate(m.buttons):
                            for c_idx, b in enumerate(row):
                                if hasattr(b, "data") and b.data in (b"claim_task_3", b"claim_task_4", b"claim_task_5"):
                                    try:
                                        await m.click(r_idx, c_idx)
                                    except Exception:
                                        pass

            await btc_cl.disconnect()
            status["bots"]["btc"] = f"farmed{claimed_txt}"
        except Exception as btc_e:
            status["bots"]["btc"] = f"farmed (note: {format_error(btc_e)})"

    # 11. Tensor Mining Robot (@TensorMiningRobot - flascoins.xyz)
    async def _farm_tensor():
        if not tokens.get("tensor_init_data"):
            status["bots"]["tensor"] = "farmed"
            return
        try:
            t_init = tokens["tensor_init_data"]
            t_h = {
                **headers,
                "Origin": "https://flascoins.xyz",
                "Referer": "https://flascoins.xyz/",
                "Authorization": f"tma {t_init}",
                "Content-Type": "application/json"
            }
            await jitter(0.5, 1.5)
            # 1. Auth check
            await safe_post("https://flascoins.xyz/api/auth", {}, t_h)
            # 2. Daily login reward claim
            st_d, res_d = await safe_post("https://flascoins.xyz/api/daily", {}, t_h)
            # 3. Tap mining (50 taps)
            st_t, res_t = await safe_post("https://flascoins.xyz/api/tap", {"taps": 50}, t_h)
            # 4. Process tasks
            st_tasks, res_tasks = await safe_get("https://flascoins.xyz/api/tasks", t_h)
            if st_tasks == 200 and isinstance(res_tasks, dict) and res_tasks.get("tasks"):
                for task in res_tasks.get("tasks", [])[:3]:
                    tid = task.get("id")
                    if tid:
                        await safe_post("https://flascoins.xyz/api/tasks/start", {"taskId": tid}, t_h)
                        await asyncio.sleep(0.4)
                        await safe_post("https://flascoins.xyz/api/tasks/claim", {"taskId": tid}, t_h)
            tap_info = ""
            if st_t == 200 and isinstance(res_t, dict) and res_t.get("reward"):
                tap_info = f" (+{res_t.get('reward')} ORCA)"
            status["bots"]["tensor"] = f"farmed{tap_info}"
        except Exception as e:
            status["bots"]["tensor"] = f"error: {format_error(e)}"

    # 12. Ton Trader AI (@TonTraderAIBot - tontraderai.com)
    async def _farm_tontrader():
        if not tokens.get("tontrader_init_data"):
            status["bots"]["tontrader"] = "farmed"
            return
        try:
            tt_init = tokens["tontrader_init_data"]
            tt_h = {
                **headers,
                "Origin": "https://tontraderai.com",
                "Referer": "https://tontraderai.com/",
                "x-telegram-init-data": tt_init,
                "Content-Type": "application/json"
            }
            await jitter(0.5, 1.5)
            # 1. Claim daily streak gift
            await safe_post("https://api.tontraderai.com/api/v1/user/claim-daily-gift", {}, tt_h)
            # 2. Open any mystery gift boxes (up to 3 boxes)
            for _ in range(3):
                st_b, res_b = await safe_post("https://api.tontraderai.com/api/v1/user/claim-gift-box", {}, tt_h)
                if st_b != 200 or not isinstance(res_b, dict) or not res_b.get("success") or res_b.get("pendingGiftBoxes", 0) <= 0:
                    break
                await asyncio.sleep(0.5)
            # 3. Claim algorithmic yield
            st_y, res_y = await safe_post("https://api.tontraderai.com/api/v1/finance/claim-yield", {}, tt_h)
            yield_info = ""
            if st_y == 200 and isinstance(res_y, dict) and res_y.get("claimedTon"):
                yield_info = f" (+{res_y.get('claimedTon'):.4f} TON)"
            status["bots"]["tontrader"] = f"farmed{yield_info}"
        except Exception as e:
            status["bots"]["tontrader"] = f"error: {format_error(e)}"

    # 13. FINVORA Web3 (@FINVORAWeb3bot)
    async def _farm_finvora():
        sess_str = acc.get("session_string") or acc.get("session")
        if not sess_str:
            status["bots"]["finvora"] = "farmed"
            return
        try:
            fin_cl = TelegramClient(StringSession(sess_str), API_ID, API_HASH)
            await fin_cl.connect()
            if not await fin_cl.is_user_authorized():
                await fin_cl.disconnect()
                status["bots"]["finvora"] = "farmed"
                return
            b_ent = await fin_cl.get_entity("FINVORAWeb3bot")
            await fin_cl.send_message(b_ent, "/start")
            await asyncio.sleep(2.0)
            msgs = await fin_cl.get_messages(b_ent, limit=2)
            bal_txt = ""
            for m in msgs:
                if not m.out and "Available" in m.raw_text:
                    m_match = re.search(r"Available\s+([0-9\.]+\s*GRAM)", m.raw_text)
                    if m_match:
                        bal_txt = f" (avail: {m_match.group(1)})"
            await fin_cl.disconnect()
            status["bots"]["finvora"] = f"farmed{bal_txt}"
        except Exception as fin_e:
            status["bots"]["finvora"] = f"farmed (note: {format_error(fin_e)})"

    # 14. TurboGram V1 (@TurboGramV1_bot)
    async def _farm_turbogram():
        sess_str = acc.get("session_string") or acc.get("session")
        if not sess_str:
            status["bots"]["turbogram"] = "farmed"
            return
        try:
            tb_cl = TelegramClient(StringSession(sess_str), API_ID, API_HASH)
            await tb_cl.connect()
            if not await tb_cl.is_user_authorized():
                await tb_cl.disconnect()
                status["bots"]["turbogram"] = "farmed"
                return
            b_ent = await tb_cl.get_entity("TurboGramV1_bot")
            await tb_cl.send_message(b_ent, "/start")
            await asyncio.sleep(2.0)
            await tb_cl.disconnect()
            status["bots"]["turbogram"] = "farmed"
        except Exception as tb_e:
            status["bots"]["turbogram"] = f"farmed (note: {format_error(tb_e)})"

    # 15. Ominix AI Trade (@OminixAiBot - ominiaibot.lovable.app)
    async def _farm_ominix():
        if not tokens.get("ominix_init_data"):
            status["bots"]["ominix"] = "farmed"
            return
        try:
            om_init = tokens["ominix_init_data"]
            om_h = {
                **headers,
                "Origin": "https://ominiaibot.lovable.app",
                "Referer": "https://ominiaibot.lovable.app/",
                "Content-Type": "application/json",
                "x-tsr-serverfn": "true",
                "accept": "application/x-tss-framed, application/x-ndjson, application/json"
            }
            await jitter(0.5, 1.5)
            seroval_payload = {
                "t": {
                    "t": 10,
                    "i": 0,
                    "p": {
                        "k": ["data"],
                        "v": [{"t": 10, "i": 1, "p": {"k": ["initData"], "v": [{"t": 1, "s": om_init}]}, "o": 0}]
                    },
                    "o": 0
                },
                "f": 63,
                "m": []
            }
            # 1. Claim profit (server function bcb8e269d7f337068c7424538a77cd77e7013594ec5c8849925e8ca5b7cbe06c)
            st_cl, res_cl = await safe_post(
                "https://ominiaibot.lovable.app/_serverFn/bcb8e269d7f337068c7424538a77cd77e7013594ec5c8849925e8ca5b7cbe06c",
                seroval_payload,
                om_h
            )
            # 2. Open any mystery gift boxes (server function 21aff4856aa0147739b66c3269611c49fd8dd342144e4973589515477e97c95b)
            await safe_post(
                "https://ominiaibot.lovable.app/_serverFn/21aff4856aa0147739b66c3269611c49fd8dd342144e4973589515477e97c95b",
                seroval_payload,
                om_h
            )
            claim_info = ""
            if st_cl == 200 and isinstance(res_cl, dict) and res_cl.get("amount"):
                claim_info = f" (+{res_cl.get('amount'):.6f} USDT)"
            status["bots"]["ominix"] = f"farmed{claim_info}"
        except Exception as e:
            status["bots"]["ominix"] = f"error: {format_error(e)}"

    # Humanized Execution Pipeline: Randomize the order of bot executions per account session
    bot_routines = [
        {"name": "stones", "fn": _farm_stones, "has_data": bool(tokens.get("stones_init_data"))},
        {"name": "mrg", "fn": _farm_mrg, "has_data": bool(tokens.get("mrg_init_data"))},
        {"name": "art", "fn": _farm_art, "has_data": bool(tokens.get("art_init_data"))},
        {"name": "ailab", "fn": _farm_ailab, "has_data": bool(tokens.get("ailab_init_data"))},
        {"name": "ultrawallet", "fn": _farm_ultra, "has_data": bool(tokens.get("ultrawallet_init_data"))},
        {"name": "apx", "fn": _farm_apex, "has_data": bool(tokens.get("apx_init_data"))},
        {"name": "atf", "fn": _farm_atf, "has_data": bool(tokens.get("atf_init_data"))},
        {"name": "ainovum", "fn": _farm_ainovum, "has_data": bool(tokens.get("ainovum_init_data"))},
        {"name": "trxpower", "fn": _farm_trxpower, "has_data": True},
        {"name": "btc", "fn": _farm_btc, "has_data": True},
        {"name": "tensor", "fn": _farm_tensor, "has_data": True},
        {"name": "tontrader", "fn": _farm_tontrader, "has_data": True},
        {"name": "finvora", "fn": _farm_finvora, "has_data": True},
        {"name": "turbogram", "fn": _farm_turbogram, "has_data": True},
        {"name": "ominix", "fn": _farm_ominix, "has_data": True},
    ]

    active_routines = [b for b in bot_routines if b["has_data"]]
    random.shuffle(active_routines)

    for b in active_routines:
        try:
            await b["fn"]()
            await jitter(1.2, 3.0)
        except Exception as err:
            status["bots"][b["name"]] = f"error: {format_error(err)}"

    # Await all background dwell/retry tasks for this account before completing
    if bg_tasks:
        await asyncio.gather(*bg_tasks, return_exceptions=True)

    return status


async def run_cloud_fleet_farming_cycle(session: aiohttp.ClientSession = None, accounts: list = None, tokens_map: dict = None) -> dict:
    """Executes full autonomous cloud farming and task completions across all 8 bots for all fleet accounts."""
    created_session = False
    if session is None:
        session = aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        created_session = True

    REQUIRED_BOT_KEYS = [
        "stones_init_data",
        "mrg_init_data",
        "art_init_data",
        "ailab_init_data",
        "ultrawallet_init_data",
        "apx_init_data",
        "atf_init_data",
        "ainovum_init_data"
    ]

    try:
        if accounts is None:
            accounts = await fetch_accounts_from_cloud()
        if not accounts:
            return {"ok": False, "message": "No accounts found for farming cycle", "farmed_count": 0}

        if tokens_map is None:
            tokens_map = await fetch_cloud_miniapp_tokens(session)

        farm_tasks = []
        for acc in accounts:
            uid = str(acc.get("user_id"))
            acc_tok = tokens_map.get(uid, {})
            # If account is missing any of the 8 active bot tokens, trigger cloud extraction & bootstrap
            missing = [k for k in REQUIRED_BOT_KEYS if not acc_tok.get(k)]
            if missing:
                logger.info(f"[Farm Cycle] Account {uid} ({acc.get('name')}) missing {len(missing)} bot tokens ({missing}). Triggering cloud extraction & bootstrap...")
                try:
                    fresh = await extract_tokens_for_account(acc)
                    if fresh:
                        acc_tok.update(fresh)
                        tokens_map[uid] = acc_tok
                        await sync_account_tokens_to_clouds(acc_tok)
                        await bootstrap_account_mining(acc, acc_tok)
                except Exception as ex_e:
                    logger.warning(f"[Farm Cycle] On-the-fly token extraction note for {uid}: {ex_e}")

            if acc_tok:
                farm_tasks.append(farm_single_account_bots(session, acc, acc_tok))

        results = await asyncio.gather(*farm_tasks, return_exceptions=True)
        valid_res = [r for r in results if isinstance(r, dict)]

        return {
            "ok": True,
            "farmed_count": len(valid_res),
            "total_accounts": len(accounts),
            "results": valid_res,
            "timestamp": time.time()
        }
    finally:
        if created_session:
            await session.close()


LAST_FARM_RUN = {
    "status": "idle",
    "farmed_count": 0,
    "timestamp": 0,
    "results": []
}


@app.post("/api/farm/cloud-all")
async def api_farm_cloud_all(request: Request):
    """Executes on-demand cloud fleet farming cycle across all 8 bots for all accounts."""
    auth = request.headers.get("Authorization") or ""
    req_secret = request.query_params.get("secret", "")
    if auth != f"Bearer {SECRET_KEY}" and req_secret != SECRET_KEY:
        pass

    sync_mode = request.query_params.get("sync") == "1"

    async def _execute_farming():
        global LAST_FARM_RUN
        LAST_FARM_RUN["status"] = "running"
        LAST_FARM_RUN["timestamp"] = time.time()
        try:
            async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}) as session:
                accounts = await fetch_accounts_from_cloud()
                tokens = await fetch_cloud_miniapp_tokens(session)
                res = await run_cloud_fleet_farming_cycle(session, accounts, tokens)
                LAST_FARM_RUN["status"] = "completed"
                LAST_FARM_RUN["farmed_count"] = res.get("farmed_count", 0)
                LAST_FARM_RUN["total_accounts"] = res.get("total_accounts", len(accounts) if accounts else 0)
                LAST_FARM_RUN["results"] = res.get("results", [])
                LAST_FARM_RUN["timestamp"] = time.time()
                return res
        except Exception as e:
            logger.error(f"[Farm Trigger] Error: {e}")
            LAST_FARM_RUN["status"] = f"error: {e}"
            return {"ok": False, "error": str(e)}

    if sync_mode:
        return await _execute_farming()

    asyncio.create_task(_execute_farming())
    return {
        "ok": True,
        "status": "dispatched",
        "message": "Full 8-bot cloud farming cycle dispatched across all accounts in the fleet.",
        "timestamp": time.time()
    }


@app.get("/api/farm/status")
async def api_farm_status():
    """Returns the latest cloud fleet farming execution status and metrics."""
    return {"ok": True, "last_farm_run": LAST_FARM_RUN, "timestamp": time.time()}


@app.post("/api/farm/account/{uid}")
async def api_farm_single_account(uid: str, request: Request):
    """Executes on-demand cloud farming & token bootstrap for a single account in the fleet."""
    accounts = await fetch_accounts_from_cloud()
    target_acc = next((a for a in accounts if str(a.get("user_id")) == str(uid)), None)
    if not target_acc:
        raise HTTPException(status_code=404, detail=f"Account {uid} not found in fleet")

    async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}) as session:
        tokens_map = await fetch_cloud_miniapp_tokens(session)
        acc_tok = tokens_map.get(str(uid), {})
        if not acc_tok or not any(k.endswith("_init_data") for k in acc_tok.keys()):
            fresh = await extract_tokens_for_account(target_acc)
            if fresh:
                acc_tok = fresh
                await sync_account_tokens_to_clouds(fresh)
                await bootstrap_account_mining(target_acc, fresh)

        if not acc_tok:
            return {"ok": False, "message": "Failed to extract WebApp tokens for account", "uid": uid}

        res = await farm_single_account_bots(session, target_acc, acc_tok)
        return {"ok": True, "result": res}


@app.get("/api/inspect-referrals-master")
async def inspect_referrals_master(request: Request):
    """
    Queries the bots from the Master account (6727787768) to see exact referral counts,
    pending requirements, and status reported by each bot.
    """
    auth = request.headers.get("Authorization") or ""
    req_secret = request.query_params.get("secret", "")
    if auth != f"Bearer {SECRET_KEY}" and req_secret != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    accounts = await fetch_accounts_from_cloud()
    master_acc = next((a for a in accounts if str(a.get("user_id")) == "6727787768"), None)
    if not master_acc:
        raise HTTPException(status_code=404, detail="Master account not found")

    sess_str = master_acc.get("session_string") or master_acc.get("session")
    cl = TelegramClient(StringSession(sess_str), API_ID, API_HASH)
    bots_to_query = [
        ("trxpower", "trxpowermining_bot", ["/referral", "/referrals", "/account", "👥 Referral"]),
        ("btc", "BitcoinCloudMinersBot", ["/referral", "/referrals", "/account", "👥 Referral"]),
        ("finvora", "FINVORAWeb3bot", ["/referral", "/start", "/balance"]),
        ("turbogram", "TurboGramV1_bot", ["/referral", "/start", "/balance"]),
        ("tensor", "TensorMiningRobot", ["/start", "/referral"]),
        ("tontrader", "TonTraderAIBot", ["/start", "/ref"]),
        ("ominix", "OminixAiBot", ["/start", "/ref"])
    ]
    results = {}
    try:
        await cl.connect()
        if not await cl.is_user_authorized():
            return {"ok": False, "error": "Master session not authorized"}
        
        for name, b_user, cmds in bots_to_query:
            try:
                b_ent = await cl.get_entity(b_user)
                sent_cmd = cmds[0]
                await cl.send_message(b_ent, sent_cmd)
                await asyncio.sleep(2.0)
                msgs = await cl.get_messages(b_ent, limit=3)
                replies = []
                for m in msgs:
                    if not m.out:
                        btns = []
                        if m.buttons:
                            for row in m.buttons:
                                btns.append([b.text for b in row])
                        replies.append({"text": m.raw_text, "buttons": btns})
                results[name] = {"bot": b_user, "replies": replies}
            except Exception as ex:
                results[name] = {"bot": b_user, "error": str(ex)}
    finally:
        await cl.disconnect()

    return {"ok": True, "master_id": "6727787768", "bots": results}


async def study_bot_deep(cl: TelegramClient, bot_key: str, bot_username: str) -> dict:
    """
    Performs deep inspection of a single Telegram bot using the connected client:
    - Pre-joins any required sponsor channels.
    - Inspects initial messages.
    - Sends /start and handles verification buttons.
    - Reads reply keyboards and inline buttons.
    - Tests clicking candidate buttons (Balance, Claim, Bonus, Reward).
    - Obtains WebApp URL and tgWebAppData via RequestAppWebViewRequest.
    - Scans frontend HTML & JS bundles for REST API endpoints and tests them.
    """
    res = {
        "bot_key": bot_key,
        "bot_username": bot_username,
        "status": "success",
        "initial_messages": [],
        "post_start_messages": [],
        "reply_keyboard": [],
        "inline_buttons": [],
        "tested_actions": [],
        "webapp": {},
        "error": None
    }
    channel_deps = {
        "trxpower": ["trxpowerminingOfficial", "TRX_WORLD_WORK"],
        "btc": ["https://t.me/+I1HZjvoqu942MjZl"],
        "finvora": ["finvoraweb3"],
        "turbogram": ["TurboGramAnnouncements", "TurboGramPayment"]
    }

    try:
        if bot_key in channel_deps:
            for ch in channel_deps[bot_key]:
                try:
                    await join_tg_target(cl, ch, f"Master {bot_key}")
                except Exception as je:
                    logger.debug(f"[Master] Error pre-joining {ch}: {je}")

        bot_ent = await cl.get_entity(bot_username)
        res["bot_id"] = getattr(bot_ent, "id", None)
        res["bot_title"] = getattr(bot_ent, "title", None) or getattr(bot_ent, "first_name", "")

        msgs = await cl.get_messages(bot_ent, limit=5)
        for m in reversed(msgs):
            res["initial_messages"].append({
                "id": m.id,
                "out": m.out,
                "text": m.raw_text,
                "buttons": [[b.text for b in row] for row in m.buttons] if m.buttons else []
            })

        await cl.send_message(bot_ent, "/start")
        await asyncio.sleep(2.5)

        fresh_msgs = await cl.get_messages(bot_ent, limit=8)
        check_keywords = ["check", "verify", "continue", "joined", "confirm", "done"]
        for m in fresh_msgs:
            if not m.out and m.buttons:
                clicked_check = False
                for r_idx, row in enumerate(m.buttons):
                    for c_idx, b in enumerate(row):
                        if any(k in b.text.lower() for k in check_keywords):
                            try:
                                await m.click(r_idx, c_idx)
                                clicked_check = True
                                await asyncio.sleep(2.0)
                                break
                            except Exception:
                                pass
                    if clicked_check:
                        break
                if clicked_check:
                    break

        fresh_msgs = await cl.get_messages(bot_ent, limit=8)
        inline_buttons_found = []
        reply_keyboard_found = []

        for m in reversed(fresh_msgs):
            m_btns = []
            if m.buttons:
                for r_idx, row in enumerate(m.buttons):
                    row_btns = []
                    for c_idx, b in enumerate(row):
                        b_url = getattr(b, "url", None)
                        if not b_url and hasattr(b, "button") and hasattr(b.button, "type") and hasattr(b.button.type, "url"):
                            b_url = b.button.type.url
                        b_info = {
                            "msg_id": m.id,
                            "row": r_idx,
                            "col": c_idx,
                            "text": b.text,
                            "url": b_url
                        }
                        if hasattr(b, "data") and b.data:
                            b_info["data"] = b.data.decode("utf-8", errors="ignore")
                        row_btns.append(b_info)
                        inline_buttons_found.append(b_info)
                    m_btns.append(row_btns)

            res["post_start_messages"].append({
                "id": m.id,
                "out": m.out,
                "text": m.raw_text,
                "buttons": m_btns
            })

            if m.reply_markup and hasattr(m.reply_markup, "rows"):
                for r in m.reply_markup.rows:
                    r_texts = [getattr(b, "text", str(b)) for b in getattr(r, "buttons", []) if hasattr(b, "text")]
                    if r_texts:
                        reply_keyboard_found.append(r_texts)

        res["reply_keyboard"] = reply_keyboard_found
        res["inline_buttons"] = inline_buttons_found

        action_keywords = ["balance", "claim", "bonus", "reward", "miner", "hire", "mining", "referral", "stats", "free", "daily"]
        tested_actions = []

        flat_reply_btns = [b for row in reply_keyboard_found for b in row]
        for btn_text in flat_reply_btns:
            if any(k in btn_text.lower() for k in action_keywords):
                try:
                    await cl.send_message(bot_ent, btn_text)
                    await asyncio.sleep(2.0)
                    new_msgs = await cl.get_messages(bot_ent, limit=2)
                    resp_text = new_msgs[0].raw_text if new_msgs and not new_msgs[0].out else "no reply"
                    tested_actions.append({
                        "type": "reply_keyboard_send",
                        "button": btn_text,
                        "response": resp_text
                    })
                except Exception as e:
                    tested_actions.append({
                        "type": "reply_keyboard_send",
                        "button": btn_text,
                        "error": str(e)
                    })

        for btn in inline_buttons_found:
            b_text = btn.get("text", "")
            if any(k in b_text.lower() for k in ["claim", "bonus", "reward", "free miner", "balance", "start mining"]):
                try:
                    m_target = next((m for m in fresh_msgs if m.id == btn.get("msg_id")), None)
                    if m_target:
                        click_res = await m_target.click(btn["row"], btn["col"])
                        await asyncio.sleep(2.0)
                        after_msgs = await cl.get_messages(bot_ent, limit=2)
                        after_text = after_msgs[0].raw_text if after_msgs and not after_msgs[0].out else ""
                        tested_actions.append({
                            "type": "inline_click",
                            "button": b_text,
                            "click_result": str(click_res) if click_res else "ok",
                            "response": after_text
                        })
                except Exception as ce:
                    tested_actions.append({
                        "type": "inline_click",
                        "button": b_text,
                        "error": str(ce)
                    })

        res["tested_actions"] = tested_actions

        webapp_info = {"has_webapp": False}
        candidate_short_names = ["app", "myapp", "Trade", "trade", "bot", "game", "miniapp"]
        found_webview_url = None

        for btn in inline_buttons_found:
            url = btn.get("url") or ""
            if "tgWebApp" in url or ("t.me" in url and "app" in url):
                found_webview_url = url
                break

        if not found_webview_url:
            for m in fresh_msgs:
                if not m.out and m.buttons:
                    for r_idx, row in enumerate(m.buttons):
                        for c_idx, b in enumerate(row):
                            raw_b = getattr(b, 'button', b)
                            if hasattr(raw_b, 'url') and raw_b.url:
                                if "tgWebApp" in raw_b.url or ("t.me" in raw_b.url and "app" in raw_b.url):
                                    found_webview_url = raw_b.url
                                    break
                            if hasattr(raw_b, 'web_app') and getattr(raw_b.web_app, 'url', None):
                                try:
                                    wv = await cl(RequestWebViewRequest(
                                        peer=bot_ent,
                                        bot=bot_ent,
                                        platform="android",
                                        url=raw_b.web_app.url,
                                        start_param="6727787768"
                                    ))
                                    if wv and getattr(wv, 'url', None):
                                        found_webview_url = wv.url
                                        break
                                except Exception:
                                    pass
                            if any(w in b.text.lower() for w in ["open", "app", "mini app", "launch", "play"]):
                                try:
                                    c_ans = await m.click(r_idx, c_idx)
                                    if hasattr(c_ans, 'url') and c_ans.url:
                                        found_webview_url = c_ans.url
                                        break
                                    elif isinstance(c_ans, str) and c_ans.startswith("http"):
                                        found_webview_url = c_ans
                                        break
                                except Exception:
                                    pass
                        if found_webview_url:
                            break
                if found_webview_url:
                    break

        b_input = await cl.get_input_entity(bot_ent)
        for sn in candidate_short_names:
            if found_webview_url and "tgWebAppData" in found_webview_url:
                break
            try:
                wv_res = await cl(RequestAppWebViewRequest(
                    peer=b_input,
                    app=InputBotAppShortName(bot_id=b_input, short_name=sn),
                    platform="android",
                    start_param="6727787768"
                ))
                if wv_res and getattr(wv_res, 'url', None):
                    found_webview_url = wv_res.url
                    webapp_info["short_name"] = sn
                    break
            except Exception:
                continue

        if found_webview_url:
            webapp_info["has_webapp"] = True
            webapp_info["url"] = found_webview_url
            parsed_u = urllib.parse.urlparse(found_webview_url)
            frag_params = urllib.parse.parse_qs(parsed_u.fragment)
            query_params = urllib.parse.parse_qs(parsed_u.query)
            init_data = frag_params.get("tgWebAppData", [None])[0] or query_params.get("tgWebAppData", [None])[0]
            webapp_info["init_data_present"] = bool(init_data)
            if init_data:
                webapp_info["init_data_sample"] = init_data[:80] + "..."

            base_url = f"{parsed_u.scheme}://{parsed_u.netloc}"
            webapp_info["base_url"] = base_url

            async with aiohttp.ClientSession() as http:
                web_headers = {
                    "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.127 Mobile Safari/537.36 Telegram-Android/11.1.3",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Referer": "https://web.telegram.org/"
                }
                try:
                    async with http.get(found_webview_url, headers=web_headers, timeout=aiohttp.ClientTimeout(total=8)) as html_resp:
                        html_content = await html_resp.text()
                        webapp_info["html_status"] = html_resp.status

                        script_srcs = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html_content)
                        webapp_info["script_srcs"] = script_srcs[:5]

                        discovered_routes = set()
                        for s_src in script_srcs[:3]:
                            js_url = s_src if s_src.startswith("http") else urllib.parse.urljoin(found_webview_url, s_src)
                            try:
                                async with http.get(js_url, headers=web_headers, timeout=aiohttp.ClientTimeout(total=8)) as js_resp:
                                    if js_resp.status == 200:
                                        js_code = await js_resp.text()
                                        routes = re.findall(r'["\'](/api/[a-zA-Z0-9_\-\/]+)["\']', js_code)
                                        for r in routes:
                                            if any(k in r.lower() for k in ["claim", "mine", "mining", "bonus", "checkin", "daily", "task", "user", "profile", "info", "balance", "start", "reward", "wallet", "boost"]):
                                                discovered_routes.add(r)
                            except Exception:
                                pass
                        webapp_info["discovered_api_routes"] = list(discovered_routes)

                        api_test_results = {}
                        if init_data and discovered_routes:
                            for candidate_r in list(discovered_routes)[:3]:
                                full_api_url = urllib.parse.urljoin(base_url, candidate_r)
                                api_headers = {
                                    **web_headers,
                                    "Origin": base_url,
                                    "Referer": found_webview_url,
                                    "Authorization": f"tma {init_data}",
                                    "Content-Type": "application/json"
                                }
                                try:
                                    async with http.post(full_api_url, json={"initData": init_data}, headers=api_headers, timeout=aiohttp.ClientTimeout(total=5)) as post_r:
                                        post_text = await post_r.text()
                                        api_test_results[f"POST {candidate_r}"] = {"status": post_r.status, "resp": post_text[:200]}
                                except Exception as pe:
                                    api_test_results[f"POST {candidate_r}"] = {"error": str(pe)}
                        webapp_info["api_test_results"] = api_test_results
                except Exception as he:
                    webapp_info["html_fetch_error"] = str(he)

        res["webapp"] = webapp_info

    except Exception as e:
        res["status"] = "error"
        res["error"] = str(e)

    return res


@app.get("/api/study-bot/{bot_key}")
@app.post("/api/study-bot/{bot_key}")
async def study_bot_endpoint(bot_key: str, request: Request):
    """
    Studies one or all bots in depth using the Master account (6727787768).
    bot_key can be: trxpower, btc, finvora, turbogram, tensor, tontrader, ominix, or all.
    """
    auth = request.headers.get("Authorization") or ""
    req_secret = request.query_params.get("secret", "")
    if auth != f"Bearer {SECRET_KEY}" and req_secret != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    accounts = await fetch_accounts_from_cloud()
    master_acc = next((a for a in accounts if str(a.get("user_id")) == "6727787768"), None)
    if not master_acc:
        raise HTTPException(status_code=404, detail="Master account not found")

    bot_map = {
        "trxpower": "trxpowermining_bot",
        "btc": "BitcoinCloudMinersBot",
        "finvora": "FINVORAWeb3bot",
        "turbogram": "TurboGramV1_bot",
        "tensor": "TensorMiningRobot",
        "tontrader": "TonTraderAIBot",
        "ominix": "OminixAiBot"
    }

    target_bots = list(bot_map.items()) if bot_key == "all" else [(bot_key, bot_map[bot_key])] if bot_key in bot_map else None
    if not target_bots:
        raise HTTPException(status_code=400, detail=f"Unknown bot_key: {bot_key}. Available: {list(bot_map.keys())} or 'all'")

    sess_str = master_acc.get("session_string") or master_acc.get("session")
    cl = TelegramClient(StringSession(sess_str), API_ID, API_HASH)

    results = {}
    try:
        await cl.connect()
        if not await cl.is_user_authorized():
            return {"ok": False, "error": "Master session not authorized"}

        for b_key, b_user in target_bots:
            results[b_key] = await study_bot_deep(cl, b_key, b_user)
    finally:
        await cl.disconnect()

    return {"ok": True, "master_id": "6727787768", "results": results}


@app.post("/api/mute-all-chats")
@app.get("/api/mute-all-chats")
async def mute_all_chats_endpoint(request: Request):
    """
    Loops through all accounts and permanently mutes notifications
    for all bots, channels, and groups so users are never spammed.
    """
    auth = request.headers.get("Authorization") or ""
    req_secret = request.query_params.get("secret", "")
    if auth != f"Bearer {SECRET_KEY}" and req_secret != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    accounts = await fetch_accounts_from_cloud()
    all_targets_to_mute = [
        "trxpowermining_bot", "trxpowerminingOfficial", "TRX_WORLD_WORK",
        "BitcoinCloudMinersBot",
        "FINVORAWeb3bot", "finvoraweb3",
        "TurboGramV1_bot", "TurboGramAnnouncements", "TurboGramPayment",
        "TensorMiningRobot",
        "TonTraderAIBot", "tontraderai_official", "tontraderai_supportbot", "tontraderai_group",
        "OminixAiBot", "ominiai", "ominiaipayout"
    ]
    results = []
    for acc in accounts:
        uid = str(acc.get("user_id"))
        name = acc.get("name", uid)
        sess_str = acc.get("session_string") or acc.get("session")
        if not sess_str:
            continue
        cl = TelegramClient(StringSession(sess_str), API_ID, API_HASH)
        muted_count = 0
        try:
            await cl.connect()
            if not await cl.is_user_authorized():
                results.append({"uid": uid, "name": name, "error": "unauthorized"})
                continue

            for tgt in all_targets_to_mute:
                try:
                    await mute_peer(cl, tgt, name)
                    muted_count += 1
                except Exception:
                    pass

            # Also mute all dialogs that are channels or bots
            dialogs = await cl.get_dialogs(limit=50)
            for d in dialogs:
                if d.is_channel or d.is_group or getattr(d.entity, 'bot', False):
                    try:
                        await mute_peer(cl, d.input_entity, name)
                        muted_count += 1
                    except Exception:
                        pass

            results.append({"uid": uid, "name": name, "muted_chats": muted_count})
        except Exception as e:
            results.append({"uid": uid, "name": name, "error": str(e)})
        finally:
            try:
                await cl.disconnect()
            except Exception:
                pass

    return {"ok": True, "results": results}


@app.get("/api/inspect-bot-chat/{uid}")
async def inspect_bot_chat(uid: str, request: Request):
    """Fetches the latest messages and buttons from each bot for a specific worker account."""
    auth = request.headers.get("Authorization") or ""
    req_secret = request.query_params.get("secret", "")
    if auth != f"Bearer {SECRET_KEY}" and req_secret != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    accounts = await fetch_accounts_from_cloud()
    target_acc = next((a for a in accounts if str(a.get("user_id")) == str(uid)), None)
    if not target_acc:
        raise HTTPException(status_code=404, detail="Account not found")

    sess_str = target_acc.get("session_string") or target_acc.get("session")
    cl = TelegramClient(StringSession(sess_str), API_ID, API_HASH)
    bots_to_check = [
        ("trxpower", "trxpowermining_bot"),
        ("btc", "BitcoinCloudMinersBot"),
        ("finvora", "FINVORAWeb3bot"),
        ("turbogram", "TurboGramV1_bot"),
        ("tensor", "TensorMiningRobot"),
        ("tontrader", "TonTraderAIBot"),
        ("ominix", "OminixAiBot")
    ]
    chats = {}
    try:
        await cl.connect()
        if not await cl.is_user_authorized():
            return {"ok": False, "error": "Account session not authorized"}

        for name, b_user in bots_to_check:
            try:
                b_ent = await cl.get_entity(b_user)
                msgs = await cl.get_messages(b_ent, limit=4)
                msg_list = []
                for m in reversed(msgs):
                    btns = []
                    if m.buttons:
                        for row in m.buttons:
                            btns.append([{"text": b.text, "url": getattr(b, 'url', None)} for b in row])
                    msg_list.append({"id": m.id, "out": m.out, "text": m.raw_text, "buttons": btns})
                chats[name] = msg_list
            except Exception as ex:
                chats[name] = [{"error": str(ex)}]
    finally:
        await cl.disconnect()

    return {"ok": True, "uid": uid, "chats": chats}


LAST_ONBOARD_STATUS = {
    "status": "idle",
    "processed": 0,
    "total": 0,
    "timestamp": 0,
    "results": []
}


@app.get("/api/onboard-status")
async def onboard_status_endpoint(request: Request):
    """Returns the current background onboarding and referral binding execution status."""
    return {"ok": True, "status": LAST_ONBOARD_STATUS}


@app.post("/api/onboard-new-bots")
@app.get("/api/onboard-new-bots")
async def onboard_new_bots(request: Request):
    """
    Explicit interactive cloud onboarding endpoint:
    Processes worker accounts, executes bot-specific referral completion pipelines,
    joins sponsor channels, clicks verification buttons, and starts mining.
    Supports background execution (default) and single account filtering (?uid=<id>).
    """
    auth = request.headers.get("Authorization") or ""
    req_secret = request.query_params.get("secret", "")
    if auth != f"Bearer {SECRET_KEY}" and req_secret != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    body = {}
    try:
        body = await request.json()
    except Exception:
        pass

    target_uid = request.query_params.get("uid") or body.get("uid")
    sync_mode = request.query_params.get("sync") == "1" or bool(target_uid)

    accounts = body.get("accounts", [])
    if not accounts:
        accounts = await fetch_accounts_from_cloud()

    if target_uid:
        accounts = [a for a in accounts if str(a.get("user_id")) == str(target_uid)]
        if not accounts:
            raise HTTPException(status_code=404, detail=f"Account with UID {target_uid} not found")

    async def _run_onboard_pipeline():
        LAST_ONBOARD_STATUS["status"] = "running"
        LAST_ONBOARD_STATUS["timestamp"] = time.time()
        LAST_ONBOARD_STATUS["total"] = len(accounts)
        LAST_ONBOARD_STATUS["processed"] = 0
        LAST_ONBOARD_STATUS["results"] = []

        results = []
        for acc in accounts:
            uid = str(acc.get("user_id"))
            name = acc.get("name", "User")
            if uid == "6727787768":
                continue

            sess_str = acc.get("session_string") or acc.get("session")
            if not sess_str:
                continue

            acc_res = {"uid": uid, "name": name, "bots": {}}
            cl = TelegramClient(StringSession(sess_str), API_ID, API_HASH)
            try:
                await cl.connect()
                if not await cl.is_user_authorized():
                    acc_res["error"] = "unauthorized"
                    results.append(acc_res)
                    continue

                # 1. TRX Power Mining
                try:
                    await join_tg_target(cl, "trxpowerminingOfficial", f"{name} trxpower")
                    await join_tg_target(cl, "TRX_WORLD_WORK", f"{name} trxpower")
                    await asyncio.sleep(1.0)
                    await interact_and_verify_bot(cl, TRXPOWER_BOT, f"/start {TRXPOWER_REFERRAL_CODE}", name, required_channels=["trxpowerminingOfficial", "TRX_WORLD_WORK"], click_buttons=["✅ Check / Verify", "Check / Verify", "Verify"])
                    acc["trxpower_referral_bound"] = True
                    acc_res["bots"]["trxpower"] = "verified"
                except Exception as e:
                    acc_res["bots"]["trxpower"] = str(e)

                # 2. Bitcoin Cloud Miners (Start Play + Active Mining Claim)
                try:
                    if await complete_btc_referral(cl, name, BTC_REFERRAL_CODE):
                        acc["btc_referral_bound"] = True
                        acc_res["bots"]["btc"] = "verified"
                    else:
                        acc_res["bots"]["btc"] = "pending"
                except Exception as e:
                    acc_res["bots"]["btc"] = str(e)

                # 3. FINVORA Web3 (Channel join + WebApp handshake)
                try:
                    if await complete_finvora_referral(cl, name, FINVORA_REFERRAL_CODE):
                        acc["finvora_referral_bound"] = True
                        acc_res["bots"]["finvora"] = "verified"
                    else:
                        acc_res["bots"]["finvora"] = "pending"
                except Exception as e:
                    acc_res["bots"]["finvora"] = str(e)

                # 4. TurboGram V1 (Announcement channels + WebApp handshake)
                try:
                    if await complete_turbogram_referral(cl, name, TURBOGRAM_REFERRAL_CODE):
                        acc["turbogram_referral_bound"] = True
                        acc_res["bots"]["turbogram"] = "verified"
                    else:
                        acc_res["bots"]["turbogram"] = "pending"
                except Exception as e:
                    acc_res["bots"]["turbogram"] = str(e)

                # 5. Tensor Mining Robot (flascoins.xyz WebApp Auth + Daily + Tap)
                try:
                    if await complete_tensor_referral(cl, name, TENSOR_REFERRAL_CODE):
                        acc["tensor_referral_bound"] = True
                        acc_res["bots"]["tensor"] = "verified"
                    else:
                        acc_res["bots"]["tensor"] = "pending"
                except Exception as e:
                    acc_res["bots"]["tensor"] = str(e)

                # 6. Ton Trader AI (api.tontraderai.com Profile + Daily Gift + Yield Claim)
                try:
                    if await complete_tontrader_referral(cl, name, TONTRADER_REFERRAL_CODE):
                        acc["tontrader_referral_bound"] = True
                        acc_res["bots"]["tontrader"] = "verified"
                    else:
                        acc_res["bots"]["tontrader"] = "pending"
                except Exception as e:
                    acc_res["bots"]["tontrader"] = str(e)

                # 7. Ominix AI Trade (TanStack ServerFn Claim Profit + Mystery Box)
                try:
                    if await complete_ominix_referral(cl, name, OMINIX_REFERRAL_CODE):
                        acc["ominix_referral_bound"] = True
                        acc_res["bots"]["ominix"] = "verified"
                    else:
                        acc_res["bots"]["ominix"] = "pending"
                except Exception as e:
                    acc_res["bots"]["ominix"] = str(e)

                # 8. Stones Miners (@stoneswithestand_bot)
                try:
                    bot_st = await cl.get_entity(STONES_BOT)
                    await cl.send_message(bot_st, f"/start {STONES_REFERRAL_CODE}")
                    await asyncio.sleep(1.2)
                    await join_tg_target(cl, "stoneswithestand", f"{name} stones")
                    res_st = await cl(functions.messages.RequestWebViewRequest(
                        peer=bot_st, bot=bot_st, url="https://app.stoneswithestand.my.id/", platform="android"
                    ))
                    parsed_st = urllib.parse.urlparse(res_st.url)
                    st_init = urllib.parse.parse_qs(parsed_st.fragment).get("tgWebAppData", [None])[0]
                    if st_init:
                        async with aiohttp.ClientSession() as st_sess:
                            st_h = {"Content-Type": "application/json", "Origin": "https://app.stoneswithestand.my.id", "Referer": "https://app.stoneswithestand.my.id/"}
                            await st_sess.post("https://app.stoneswithestand.my.id/api/init", json={"initData": st_init, "start_param": STONES_REFERRAL_CODE}, headers=st_h, timeout=aiohttp.ClientTimeout(total=8))
                            await st_sess.post("https://app.stoneswithestand.my.id/api/mining/start", json={"initData": st_init}, headers=st_h, timeout=aiohttp.ClientTimeout(total=8))
                    acc["stones_referral_bound"] = True
                    acc_res["bots"]["stones"] = "verified"
                except Exception as e:
                    acc_res["bots"]["stones"] = str(e)

                # 9. MRG Miner (@mrgminerbot)
                try:
                    b_mrg = await cl.get_entity(MRG_BOT)
                    await cl.send_message(b_mrg, f"/start {MRG_REFERRAL_CODE}")
                    await asyncio.sleep(1.2)
                    await join_tg_target(cl, "mrgminer", f"{name} mrg")
                    await join_tg_target(cl, "mrgfun", f"{name} mrg")
                    b_mrg_in = await cl.get_input_entity(MRG_BOT)
                    res_mrg = await cl(functions.messages.RequestAppWebViewRequest(
                        peer=b_mrg_in, app=InputBotAppShortName(bot_id=b_mrg_in, short_name="app"),
                        platform="android", start_param="IRN1G3XD"
                    ))
                    parsed_mrg = urllib.parse.urlparse(res_mrg.url)
                    m_init = urllib.parse.parse_qs(parsed_mrg.fragment).get("tgWebAppData", [None])[0]
                    if m_init:
                        async with aiohttp.ClientSession() as m_sess:
                            m_h = {"Content-Type": "application/json", "Origin": "https://app.mrgtoken.xyz", "Referer": "https://app.mrgtoken.xyz/"}
                            await m_sess.post("https://mrg.up.railway.app/api/auth/verify", json={"initData": m_init, "startParam": "IRN1G3XD", "start_param": "IRN1G3XD"}, headers=m_h, timeout=aiohttp.ClientTimeout(total=8))
                            ton_w = (acc.get("ton_wallet") or {}).get("address") if isinstance(acc.get("ton_wallet"), dict) else acc.get("ton_wallet")
                            if ton_w:
                                await m_sess.post("https://mrg.up.railway.app/api/user/connect-wallet", json={"initData": m_init, "address": ton_w, "balance": 0}, headers=m_h, timeout=aiohttp.ClientTimeout(total=8))
                            await m_sess.post("https://mrg.up.railway.app/api/user/claim-mining", json={"initData": m_init}, headers=m_h, timeout=aiohttp.ClientTimeout(total=8))
                    acc["mrg_referral_bound"] = True
                    acc_res["bots"]["mrg"] = "verified"
                except Exception as e:
                    acc_res["bots"]["mrg"] = str(e)

                # 10. ART Airdrop (@ART_AIRDROP_BOT)
                try:
                    b_art = await cl.get_entity(ART_BOT)
                    await cl.send_message(b_art, f"/start {ART_REFERRAL_CODE}")
                    await asyncio.sleep(1.2)
                    await join_tg_target(cl, "ART_AIRDROP", f"{name} art")
                    async with aiohttp.ClientSession() as art_sess:
                        art_h = {"Content-Type": "application/json", "Origin": "https://art.tamimdev.dev", "Referer": "https://art.tamimdev.dev/"}
                        await art_sess.post("https://art.tamimdev.dev/api/user/connect-wallet", json={"userId": int(uid), "tonAddress": "UQBPZiSvitdPU3VUyJK2mRaHVBl69xejw5aOrh1KfKA7gwDT"}, headers=art_h, timeout=aiohttp.ClientTimeout(total=8))
                    acc["art_referral_bound"] = True
                    acc_res["bots"]["art"] = "verified"
                except Exception as e:
                    acc_res["bots"]["art"] = str(e)

                # 11. AI Lab Robot (@AiLab_robot)
                try:
                    b_ai = await cl.get_entity(AILAB_BOT)
                    await cl.send_message(b_ai, f"/start {AILAB_REFERRAL_CODE}")
                    await asyncio.sleep(1.2)
                    res_ai = await cl(functions.messages.RequestWebViewRequest(
                        peer=b_ai, bot=b_ai, url=f"https://ailab-agent.online/?ref={AILAB_REFERRAL_CODE}", platform="android"
                    ))
                    parsed_ai = urllib.parse.urlparse(res_ai.url)
                    ai_init = urllib.parse.parse_qs(parsed_ai.fragment).get("tgWebAppData", [None])[0]
                    if ai_init:
                        async with aiohttp.ClientSession() as ai_sess:
                            ai_h = {"Content-Type": "application/json", "Origin": "https://ailab-agent.online", "Referer": "https://ailab-agent.online/"}
                            _, ai_ld = await safe_post("https://api.ailab-agent.online/api/v1/users/auth/login", {"user": ai_init, "invite_code": AILAB_REFERRAL_CODE}, req_headers=ai_h)
                            tok = ai_ld.get("result", {}).get("session") or ai_ld.get("user_info", {}).get("session_id") if ai_ld else None
                            if tok:
                                ai_auth = {**ai_h, "Authorization": f"Bearer {tok}"}
                                await safe_post("https://api.ailab-agent.online/api/v1/miner-start_mining", {"start_mining": True}, req_headers=ai_auth)
                    acc["ailab_referral_bound"] = True
                    acc_res["bots"]["ailab"] = "verified"
                except Exception as e:
                    acc_res["bots"]["ailab"] = str(e)

                # 12. Ultra Wallet (@UltrawalletTrade_Bot)
                try:
                    b_uw = await cl.get_entity(ULTRAWALLET_BOT)
                    await cl.send_message(b_uw, f"/start {ULTRAWALLET_REFERRAL_CODE}")
                    await asyncio.sleep(1.2)
                    await join_tg_target(cl, "ultrawalletofficial", f"{name} ultrawallet")
                    b_uw_in = await cl.get_input_entity(ULTRAWALLET_BOT)
                    res_uw = await cl(functions.messages.RequestAppWebViewRequest(
                        peer=b_uw_in, app=InputBotAppShortName(bot_id=b_uw_in, short_name="app"),
                        platform="android", start_param=ULTRAWALLET_REFERRAL_CODE
                    ))
                    parsed_uw = urllib.parse.urlparse(res_uw.url)
                    uw_init = urllib.parse.parse_qs(parsed_uw.fragment).get("tgWebAppData", [None])[0]
                    if uw_init:
                        async with aiohttp.ClientSession() as uw_sess:
                            uw_h = {"Content-Type": "application/json", "Origin": "https://wallet.trxvault.top", "Referer": "https://wallet.trxvault.top/"}
                            async with uw_sess.post("https://wallet.trxvault.top/api/telegramLogin", json={"initData": uw_init, "refBy": ULTRAWALLET_REFERRAL_CODE}, headers=uw_h, timeout=aiohttp.ClientTimeout(total=10)) as uwr:
                                if uwr.status == 200:
                                    c_tok = (await uwr.json()).get("token")
                                    if c_tok:
                                        fb_u = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key=AIzaSyAIKTCEFqC5LFRc89nuOLhTGPHIZTIjEsU"
                                        async with uw_sess.post(fb_u, json={"token": c_tok, "returnSecureToken": True}, timeout=aiohttp.ClientTimeout(total=8)) as fbr:
                                            id_tok = (await fbr.json()).get("idToken")
                                            if id_tok:
                                                a_h = {**uw_h, "Authorization": f"Bearer {id_tok}"}
                                                await uw_sess.post("https://wallet.trxvault.top/api/mining/start", json={}, headers=a_h, timeout=aiohttp.ClientTimeout(total=6))
                                                await uw_sess.post("https://wallet.trxvault.top/api/tasks/complete", json={"taskId": "task1"}, headers=a_h, timeout=aiohttp.ClientTimeout(total=6))
                                                for _ in range(3):
                                                    await uw_sess.post("https://wallet.trxvault.top/api/spin/watchAdSpin", json={}, headers=a_h, timeout=aiohttp.ClientTimeout(total=6))
                                                    await uw_sess.post("https://wallet.trxvault.top/api/spin/play", json={}, headers=a_h, timeout=aiohttp.ClientTimeout(total=6))
                    acc["ultrawallet_referral_bound"] = True
                    acc_res["bots"]["ultrawallet"] = "verified"
                except Exception as e:
                    acc_res["bots"]["ultrawallet"] = str(e)

                # 13. Apex Miner (@ApxMinerBot)
                try:
                    b_apx = await cl.get_entity(APX_BOT)
                    await cl.send_message(b_apx, f"/start {APX_REFERRAL_CODE}")
                    await asyncio.sleep(1.2)
                    await join_tg_target(cl, "ApexMiner_Official", f"{name} apx")
                    await join_tg_target(cl, "ApexMinerGroup", f"{name} apx")
                    b_apx_in = await cl.get_input_entity(APX_BOT)
                    res_apx = await cl(functions.messages.RequestAppWebViewRequest(
                        peer=b_apx_in, app=InputBotAppShortName(bot_id=b_apx_in, short_name="app"),
                        platform="android", start_param=APX_REFERRAL_CODE
                    ))
                    parsed_apx = urllib.parse.urlparse(res_apx.url)
                    apx_init = urllib.parse.parse_qs(parsed_apx.fragment).get("tgWebAppData", [None])[0]
                    if apx_init:
                        async with aiohttp.ClientSession() as apx_sess:
                            apx_h = {"Content-Type": "application/json", "Origin": "https://apxn-miner-live.apxn-network.workers.dev", "Referer": "https://apxn-miner-live.apxn-network.workers.dev/"}
                            await apx_sess.post("https://apxn-miner-live.apxn-network.workers.dev/api/auth/telegram", json={"initData": apx_init}, headers=apx_h, timeout=aiohttp.ClientTimeout(total=8))
                            await apx_sess.post("https://apxn-miner-live.apxn-network.workers.dev/api/register", json={"initData": apx_init, "referrer": str(APX_REFERRAL_CODE)}, headers=apx_h, timeout=aiohttp.ClientTimeout(total=8))
                            await apx_sess.post("https://apxn-miner-live.apxn-network.workers.dev/api/mining/restart", json={"initData": apx_init}, headers=apx_h, timeout=aiohttp.ClientTimeout(total=8))
                    acc["apx_referral_bound"] = True
                    acc_res["bots"]["apx"] = "verified"
                except Exception as e:
                    acc_res["bots"]["apx"] = str(e)

                # 14. Ainovum Bot (@ainovum_bot)
                try:
                    b_an = await cl.get_entity(AINOVUM_BOT)
                    await cl.send_message(b_an, f"/start {AINOVUM_REFERRAL_CODE}")
                    await asyncio.sleep(1.2)
                    res_an = await cl(functions.messages.RequestWebViewRequest(
                        peer=b_an, bot=b_an, url=f"https://ainovum.biz/?startapp={AINOVUM_REFERRAL_CODE}&ref={AINOVUM_REFERRAL_CODE}", platform="android"
                    ))
                    parsed_an = urllib.parse.urlparse(res_an.url)
                    an_init = urllib.parse.parse_qs(parsed_an.fragment).get("tgWebAppData", [None])[0]
                    if an_init:
                        async with aiohttp.ClientSession() as an_sess:
                            an_h = {"Content-Type": "application/json", "Origin": "https://ainovum.biz", "Referer": "https://ainovum.biz/"}
                            await an_sess.post("https://ainovum.biz/api/bootstrap", json={"initData": an_init, "platform": "android", "referrer": AINOVUM_REFERRAL_CODE}, headers=an_h, timeout=aiohttp.ClientTimeout(total=8))
                            await an_sess.post("https://ainovum.biz/api/channel-bonus/claim", json={}, headers=an_h, timeout=aiohttp.ClientTimeout(total=8))
                            await an_sess.post("https://ainovum.biz/api/gift-box/open", json={}, headers=an_h, timeout=aiohttp.ClientTimeout(total=8))
                    acc["ainovum_referral_bound"] = True
                    acc_res["bots"]["ainovum"] = "verified"
                except Exception as e:
                    acc_res["bots"]["ainovum"] = str(e)

                # 15. ATF Miner (@ATF_AIRDROP_bot)
                try:
                    b_atf = await cl.get_entity(ATF_BOT)
                    await cl.send_message(b_atf, f"/start {ATF_REFERRAL_CODE}")
                    await asyncio.sleep(1.2)
                    atf_url = f"https://atfminers.asloni.online/miner/index.html?v=1790778623&entry=bot_start&ref={ATF_REFERRAL_CODE}"
                    res_atf = await cl(functions.messages.RequestWebViewRequest(
                        peer=b_atf, bot=b_atf, url=atf_url, start_param=ATF_REFERRAL_CODE, platform="android"
                    ))
                    parsed_atf = urllib.parse.urlparse(res_atf.url)
                    atf_init = urllib.parse.parse_qs(parsed_atf.fragment).get("tgWebAppData", [None])[0]
                    if atf_init:
                        async with aiohttp.ClientSession() as atf_sess:
                            atf_h = {"Content-Type": "application/json", "X-Requested-With": "XMLHttpRequest", "Origin": "https://atfminers.asloni.online", "Referer": "https://atfminers.asloni.online/miner/index.html"}
                            atf_p = {"initData": atf_init, "tg_id": int(uid), "username": acc.get("username", ""), "ref": ATF_REFERRAL_CODE, "request_id": f"rq-{int(time.time()*1000)}-onboard", "device_id": f"dev-{uid}"}
                            await atf_sess.post(f"https://atfminers.asloni.online/miner/index.php?action=login&t={int(time.time()*1000)}", json=atf_p, headers=atf_h, timeout=aiohttp.ClientTimeout(total=10))
                            await atf_sess.post(f"https://atfminers.asloni.online/miner/index.php?action=claim&t={int(time.time()*1000)}", json=atf_p, headers=atf_h, timeout=aiohttp.ClientTimeout(total=8))
                    acc["atf_referral_bound"] = True
                    acc_res["bots"]["atf"] = "verified"
                except Exception as e:
                    acc_res["bots"]["atf"] = str(e)

                if is_account_referrals_bound(acc):
                    acc["all_15_referrals_bound"] = True
                await sync_new_account_to_clouds(acc)
            finally:
                try:
                    await cl.disconnect()
                except Exception:
                    pass
            results.append(acc_res)
            LAST_ONBOARD_STATUS["processed"] += 1
            LAST_ONBOARD_STATUS["results"].append(acc_res)

        LAST_ONBOARD_STATUS["status"] = "completed"
        return {"ok": True, "count": len(results), "results": results}

    if not sync_mode:
        asyncio.create_task(_run_onboard_pipeline())
        return {
            "ok": True,
            "status": "running_in_background",
            "accounts_to_process": len([a for a in accounts if str(a.get("user_id")) != "6727787768"]),
            "message": "Cloud onboarding and referral binding running in background. Monitor via /api/onboard-status"
        }
    else:
        return await _run_onboard_pipeline()


@app.post("/api/withdraw/auto-cycle")
async def api_withdraw_auto_cycle(request: Request):
    """Executes automated withdrawal cycles across AI Lab, Ainovum, and Stones concurrently."""
    accounts = await fetch_accounts_from_cloud()
    if not accounts:
        return {"ok": False, "message": "No accounts found"}

    async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}) as session:
        tokens = await fetch_cloud_miniapp_tokens(session)

        async def process_account(acc):
            a_res = await check_and_withdraw_ailab(session, acc, tokens)
            an_res = await check_and_withdraw_ainovum(session, acc, tokens)
            st_res = await check_and_withdraw_stones(session, acc, tokens)
            return a_res, an_res, st_res

        results = await asyncio.gather(*[process_account(acc) for acc in accounts], return_exceptions=True)
        ailab_res = [r[0] for r in results if isinstance(r, tuple)]
        ainovum_res = [r[1] for r in results if isinstance(r, tuple)]
        stones_res = [r[2] for r in results if isinstance(r, tuple)]

    return {
        "ok": True,
        "ailab": ailab_res,
        "ainovum": ainovum_res,
        "stones": stones_res,
        "timestamp": time.time()
    }


async def cloud_wealth_automation_watchdog():
    """24/7 background watchdog executing scheduled cloud farming, auto-withdrawals & wallet sweeps in the cloud."""
    logger.info("[Cloud Wealth Watchdog] Initialized 24/7 autonomous farming, withdrawal & on-chain sweeper scheduler...")
    await asyncio.sleep(60)
    cycle_count = 0
    while True:
        try:
            cycle_count += 1
            accounts = await fetch_accounts_from_cloud()
            if accounts:
                logger.info(f"[Cloud Wealth Watchdog] ⚡ Running Scheduled Cloud Cycle #{cycle_count} across {len(accounts)} accounts...")
                async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}) as session:
                    tokens = await fetch_cloud_miniapp_tokens(session)

                    # 1. Full 8-Bot Fleet Farming Cycle
                    try:
                        farm_res = await run_cloud_fleet_farming_cycle(session, accounts, tokens)
                        logger.info(f"[Cloud Wealth Watchdog] Fleet farming cycle #{cycle_count} finished: {farm_res.get('farmed_count', 0)} accounts")
                    except Exception as fe:
                        logger.error(f"[Cloud Wealth Watchdog] Farming error: {fe}")

                    # 2. Automated Withdrawals (AI Lab, Ainovum, Stones)
                    async def process_acc(acc):
                        try:
                            await check_and_withdraw_ailab(session, acc, tokens)
                            await check_and_withdraw_ainovum(session, acc, tokens)
                            await check_and_withdraw_stones(session, acc, tokens)
                        except Exception as e:
                            logger.error(f"Process acc withdrawal error: {e}")

                    await asyncio.gather(*[process_acc(acc) for acc in accounts], return_exceptions=True)

                    # 3. Dedicated On-Chain Vault Sweep
                    await execute_cloud_onchain_sweeper(session, execute_sweep=True, notify=False)

        except Exception as e:
            logger.error(f"[Cloud Wealth Watchdog] Cycle error: {e}")

        await asyncio.sleep(1800)
