#!/usr/bin/env python3
"""
chickenland_promo_sniper.py
=============================================================================
CHICKEN LAND DUAL-ENGINE SUB-SECOND FLEET PROMO CODE SNIPER & AUTO-COMPOUNDER
=============================================================================
Combines:
1. Real-Time MTProto Telegram Push Socket Listener (0ms push latency via Telethon)
2. High-Frequency Non-Blocking Async HTTP Poller (2.5s fallback with cache-busting)
3. Sub-Second Concurrent aiohttp Parallel Burst Engine across all 24 fleet accounts (~300-450ms)
4. Non-Blocking In-Memory State & Background Upstash Redis Persistence
5. Autonomous Flock Reinvestment: buys basic hens automatically when coins >= 1000
6. Cloud-Native: Zero Phone Load (designed to run 24/7 on Render Node 3)
=============================================================================
"""

import os
import sys
import json
import time
import re
import asyncio
import aiohttp
import urllib.parse
import urllib.request
import base64
from typing import Dict, Any, List, Set, Optional

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    pass

# Constants & Configuration
CHANNEL_USERNAME = "ChickenLandCodes"
CHANNEL_ID = -1004433995185
RAW_CHANNEL_ID = 4433995185
CHANNEL_URL = "https://t.me/s/ChickenLandCodes"
RPC_URL = "https://app8968434282.tgcloud.ai/api/rpc"

UPSTASH_URL = os.getenv("UPSTASH_URL") or os.getenv("UPSTASH_REDIS_REST_URL") or "https://internal-dodo-83852.upstash.io"
UPSTASH_TOKEN = os.getenv("UPSTASH_TOKEN") or os.getenv("UPSTASH_REDIS_REST_TOKEN") or ""
TURSO_URL = os.getenv("TURSO_DATABASE_URL") or os.getenv("TURSO_URL") or "https://my-agy-fleet-db-aaa2743.aws-ap-south-1.turso.io"
TURSO_TOKEN = os.getenv("TURSO_DB_TOKEN") or os.getenv("TURSO_AUTH_TOKEN") or ""

REPORT_BOT_TOKEN = os.getenv("REPORT_BOT_TOKEN") or os.getenv("ADMIN_BOT_TOKEN") or ""
REPORT_CHAT_ID = os.getenv("REPORT_CHAT_ID") or "6727787768"
ADMIN_NOTIF_CHANNEL = os.getenv("ADMIN_NOTIFICATION_CHANNEL_ID", "-1004358687850")

API_ID = int(os.getenv("API_ID") or os.getenv("TELEGRAM_API_ID") or 2040)
API_HASH = os.getenv("API_HASH") or os.getenv("TELEGRAM_API_HASH") or "5cd9e5bbfb572a4429a0c54774153b47"

USER_AGENT = "Mozilla/5.0 (Linux; Android 14; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36"
SCRAPER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

CODE_REGEX = re.compile(r'\b(CL[A-Z0-9]{6,12})\b|<code>([A-Z0-9]{6,16})</code>|👉\s*([A-Z0-9]{6,16})\s*👈')

# Global In-Memory Fast State (Zero latency lookups during burst)
SEEN_CODES: Set[str] = set()
CLAIMED_CODES: Set[str] = set()
EXHAUSTED_CODES: Set[str] = set()
ACCOUNT_CLAIMED_CODES: Dict[str, Set[str]] = {}
CACHED_FLEET_TOKENS: Dict[str, Dict[str, Any]] = {}
BURST_LOCK = asyncio.Lock()

def turso_execute(sql: str, args: list = None) -> Optional[List[List[Any]]]:
    """Synchronous Turso LibSQL pipeline execution."""
    if not TURSO_TOKEN:
        return None
    endpoint = TURSO_URL.rstrip("/").replace("libsql://", "https://") + "/v2/pipeline"
    headers = {"Authorization": f"Bearer {TURSO_TOKEN}", "Content-Type": "application/json"}
    formatted_args = []
    if args:
        for a in args:
            if isinstance(a, int):
                formatted_args.append({"type": "integer", "value": str(a)})
            else:
                formatted_args.append({"type": "text", "value": str(a)})
    req_body = {
        "requests": [
            {"type": "execute", "stmt": {"sql": sql, "args": formatted_args}}
        ]
    }
    try:
        req = urllib.request.Request(endpoint, data=json.dumps(req_body).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("results", [])
            if results and results[0].get("response", {}).get("result", {}).get("rows"):
                rows = results[0]["response"]["result"]["rows"]
                return [[c.get("value") for c in r] for r in rows]
    except Exception:
        pass
    return None

async def async_turso_execute(session: aiohttp.ClientSession, sql: str, args: list = None) -> Optional[List[List[Any]]]:
    """Non-blocking async Turso LibSQL pipeline execution."""
    if not TURSO_TOKEN:
        return None
    endpoint = TURSO_URL.rstrip("/").replace("libsql://", "https://") + "/v2/pipeline"
    headers = {"Authorization": f"Bearer {TURSO_TOKEN}", "Content-Type": "application/json"}
    formatted_args = []
    if args:
        for a in args:
            if isinstance(a, int):
                formatted_args.append({"type": "integer", "value": str(a)})
            else:
                formatted_args.append({"type": "text", "value": str(a)})
    req_body = {
        "requests": [
            {"type": "execute", "stmt": {"sql": sql, "args": formatted_args}}
        ]
    }
    try:
        async with session.post(endpoint, json=req_body, headers=headers, timeout=aiohttp.ClientTimeout(total=3)) as resp:
            if resp.status == 200:
                data = await resp.json()
                results = data.get("results", [])
                if results and results[0].get("response", {}).get("result", {}).get("rows"):
                    rows = results[0]["response"]["result"]["rows"]
                    return [[c.get("value") for c in r] for r in rows]
    except Exception:
        pass
    return None

def turso_get(key: str) -> Optional[str]:
    rows = turso_execute("SELECT val FROM kv_mesh WHERE key = ? LIMIT 1", [key])
    if rows and len(rows) > 0 and len(rows[0]) > 0:
        return rows[0][0]
    return None

def turso_set(key: str, val: Any) -> bool:
    val_str = json.dumps(val) if not isinstance(val, str) else val
    now_ts = int(time.time())
    res = turso_execute("INSERT OR REPLACE INTO kv_mesh (key, val, updated_at) VALUES (?, ?, ?)", [key, val_str, now_ts])
    return res is not None

async def async_turso_get(session: aiohttp.ClientSession, key: str) -> Optional[str]:
    rows = await async_turso_execute(session, "SELECT val FROM kv_mesh WHERE key = ? LIMIT 1", [key])
    if rows and len(rows) > 0 and len(rows[0]) > 0:
        return rows[0][0]
    return None

async def async_turso_set(session: aiohttp.ClientSession, key: str, val: Any) -> bool:
    val_str = json.dumps(val) if not isinstance(val, str) else val
    now_ts = int(time.time())
    res = await async_turso_execute(session, "INSERT OR REPLACE INTO kv_mesh (key, val, updated_at) VALUES (?, ?, ?)", [key, val_str, now_ts])
    return res is not None

def redis_command(cmd: str, *args) -> Any:
    """Synchronous Redis helper for initial startup loading."""
    if not UPSTASH_URL or not UPSTASH_TOKEN:
        return None
    headers = {"Authorization": f"Bearer {UPSTASH_TOKEN}", "Content-Type": "application/json"}
    try:
        req = urllib.request.Request(UPSTASH_URL, data=json.dumps([cmd, *args]).encode('utf-8'), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data.get("result")
    except Exception:
        try:
            url = f"{UPSTASH_URL.rstrip('/')}/{cmd}/" + "/".join(urllib.parse.quote(str(a), safe='') for a in args)
            req_get = urllib.request.Request(url, headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"})
            with urllib.request.urlopen(req_get, timeout=4) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                return data.get("result")
        except Exception:
            return None

async def async_redis_command(session: aiohttp.ClientSession, cmd: str, *args) -> Any:
    """Non-blocking async Redis helper for post-burst persistence."""
    if not UPSTASH_URL or not UPSTASH_TOKEN:
        return None
    headers = {"Authorization": f"Bearer {UPSTASH_TOKEN}", "Content-Type": "application/json"}
    try:
        async with session.post(UPSTASH_URL, json=[cmd, *args], headers=headers, timeout=aiohttp.ClientTimeout(total=3)) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("result")
    except Exception:
        try:
            url = f"{UPSTASH_URL.rstrip('/')}/{cmd}/" + "/".join(urllib.parse.quote(str(a), safe='') for a in args)
            async with session.get(url, headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}, timeout=aiohttp.ClientTimeout(total=3)) as resp2:
                if resp2.status == 200:
                    data2 = await resp2.json()
                    return data2.get("result")
        except Exception:
            pass
    return None

def is_code_seen(code: str) -> bool:
    code = code.strip().upper()
    if code in SEEN_CODES:
        return True
    # Dual-check: Redis and Turso LibSQL
    try:
        if redis_command("SISMEMBER", "chickenland:seen_codes", code) == 1:
            return True
    except Exception:
        pass
    try:
        t_seen = turso_get("chickenland:seen_codes")
        if t_seen:
            parsed = json.loads(t_seen) if isinstance(t_seen, str) else t_seen
            if isinstance(parsed, list) and code in parsed:
                return True
    except Exception:
        pass
    return False

def is_code_claimed(code: str) -> bool:
    code = code.strip().upper()
    if code in CLAIMED_CODES:
        return True
    # Dual-check: Redis and Turso LibSQL
    try:
        if redis_command("SISMEMBER", "chickenland:claimed_codes", code) == 1:
            return True
    except Exception:
        pass
    try:
        t_claimed = turso_get("chickenland:claimed_codes")
        if t_claimed:
            parsed = json.loads(t_claimed) if isinstance(t_claimed, str) else t_claimed
            if isinstance(parsed, list) and code in parsed:
                return True
    except Exception:
        pass
    return False

def mark_code_seen(code: str):
    code = code.strip().upper()
    SEEN_CODES.add(code)
    try:
        redis_command("SADD", "chickenland:seen_codes", code)
    except Exception:
        pass
    try:
        seen_list = list(SEEN_CODES)[-200:]
        turso_set("chickenland:seen_codes", seen_list)
    except Exception:
        pass

def mark_code_claimed(code: str):
    code = code.strip().upper()
    CLAIMED_CODES.add(code)
    try:
        redis_command("SADD", "chickenland:claimed_codes", code)
    except Exception:
        pass
    try:
        claimed_list = list(CLAIMED_CODES)[-200:]
        turso_set("chickenland:claimed_codes", claimed_list)
    except Exception:
        pass

def send_telegram_alert(text: str):
    """Sends clean notification card to Admin channels."""
    if not REPORT_BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{REPORT_BOT_TOKEN}/sendMessage"
    targets = [REPORT_CHAT_ID]
    if ADMIN_NOTIF_CHANNEL and ADMIN_NOTIF_CHANNEL not in targets:
        targets.append(ADMIN_NOTIF_CHANNEL)
    for tid in targets:
        payload = {
            "chat_id": tid,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=4)
        except Exception as e:
            print(f"[Telegram Alert Error]: {e}", file=sys.stderr)

def get_b64_token(init_data: str) -> str:
    """Standardizes WebApp initData to TMA base64 authorization token."""
    if not init_data:
        return ""
    if init_data.startswith("TMA "):
        return init_data[4:].strip()
    if "%3D" in init_data or "query_id=" in init_data or "user=" in init_data:
        decoded = urllib.parse.unquote(init_data) if "%3D" in init_data else init_data
        return base64.b64encode(decoded.encode("utf-8")).decode("utf-8")
    return init_data.strip()

def load_fleet_tokens(force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
    """
    Loads all active Chicken Land WebApp authorization tokens across all 24 accounts.
    Prioritizes Upstash Redis `miniapp_tokens`, then `fleet:tokens:{uid}`, then `accounts.json`, then `fleet_miniapp_tokens.json`.
    """
    global CACHED_FLEET_TOKENS
    if CACHED_FLEET_TOKENS and not force_refresh and len(CACHED_FLEET_TOKENS) >= 20:
        return CACHED_FLEET_TOKENS

    base_dir = os.path.dirname(os.path.abspath(__file__))
    tokens_path = os.path.join(base_dir, "fleet_miniapp_tokens.json")
    accs_path = os.path.join(base_dir, "accounts.json")

    fleet = {}
    names = {}
    accounts_list = []
    if os.path.exists(accs_path):
        try:
            with open(accs_path, "r", encoding="utf-8") as f:
                accounts_list = json.load(f)
                for acc in accounts_list:
                    uid = str(acc.get("user_id", ""))
                    if uid:
                        names[uid] = acc.get("name", f"Account {uid}")
        except Exception:
            pass

    # 0. Prioritize Turso LibSQL Mesh SSOT (Zero rate limits, 25M ops/mo)
    for turso_k in ("fleet:tokens_state", "miniapp_tokens"):
        try:
            res_turso = turso_get(turso_k)
            if res_turso:
                tok_map = json.loads(res_turso) if isinstance(res_turso, str) else res_turso
                while isinstance(tok_map, str):
                    try:
                        tok_map = json.loads(tok_map)
                    except Exception:
                        break
                if isinstance(tok_map, dict):
                    for uid, toks in tok_map.items():
                        if str(uid) == "8881914294" or "nancy" in str(names.get(str(uid), "")).lower():
                            continue
                        tok = (toks.get("chickenland_init_data") or toks.get("chicken_init_data")) if isinstance(toks, dict) else None
                        if tok and str(uid) not in fleet:
                            fleet[str(uid)] = {
                                "user_id": str(uid),
                                "name": names.get(str(uid), f"User {uid}"),
                                "b64_token": get_b64_token(tok)
                            }
            if len(fleet) >= 20:
                break
        except Exception:
            pass

    # 1. Prioritize Upstash Redis for ground-truth monolithic miniapp_tokens
    if UPSTASH_URL and UPSTASH_TOKEN and len(fleet) < 20:
        try:
            res = redis_command("GET", "miniapp_tokens")
            if res:
                tok_map = json.loads(res) if isinstance(res, str) else res
                while isinstance(tok_map, str):
                    try:
                        tok_map = json.loads(tok_map)
                    except Exception:
                        break
                if isinstance(tok_map, dict):
                    for uid, toks in tok_map.items():
                        if str(uid) == "8881914294" or "nancy" in str(names.get(str(uid), "")).lower():
                            continue
                        tok = (toks.get("chickenland_init_data") or toks.get("chicken_init_data")) if isinstance(toks, dict) else None
                        if tok and str(uid) not in fleet:
                            fleet[str(uid)] = {
                                "user_id": str(uid),
                                "name": names.get(str(uid), f"User {uid}"),
                                "b64_token": get_b64_token(tok)
                            }
        except Exception as e:
            pass

    # 2. Check individual keys `fleet:tokens:{uid}` for any missing accounts
    for acc in accounts_list:
        uid = str(acc.get("user_id", ""))
        if str(uid) == "8881914294" or "nancy" in str(acc.get("name", "")).lower():
            continue
        if uid and uid not in fleet and UPSTASH_URL and UPSTASH_TOKEN:
            try:
                res = redis_command("GET", f"fleet:tokens:{uid}")
                if res:
                    u_toks = json.loads(res) if isinstance(res, str) else res
                    while isinstance(u_toks, str):
                        try:
                            u_toks = json.loads(u_toks)
                        except Exception:
                            break
                    if isinstance(u_toks, dict):
                        tok = u_toks.get("chickenland_init_data") or u_toks.get("chicken_init_data")
                        if tok:
                            fleet[str(uid)] = {
                                "user_id": str(uid),
                                "name": names.get(str(uid), f"User {uid}"),
                                "b64_token": get_b64_token(tok)
                            }
            except Exception:
                pass

    # 3. Fallback to accounts.json
    for acc in accounts_list:
        uid = str(acc.get("user_id", ""))
        if str(uid) == "8881914294" or "nancy" in str(acc.get("name", "")).lower():
            continue
        if uid and uid not in fleet:
            tok = acc.get("chickenland_init_data") or acc.get("chicken_init_data")
            if tok and isinstance(tok, str):
                fleet[str(uid)] = {
                    "user_id": str(uid),
                    "name": names.get(str(uid), f"User {uid}"),
                    "b64_token": get_b64_token(tok)
                }

    # 4. Fallback to fleet_miniapp_tokens.json
    if os.path.exists(tokens_path) and len(fleet) < 20:
        try:
            with open(tokens_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                while isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except Exception:
                        break
                if isinstance(data, dict):
                    for uid, toks in data.items():
                        if str(uid) == "8881914294" or "nancy" in str(names.get(str(uid), "")).lower():
                            continue
                        tok = (toks.get("chickenland_init_data") or toks.get("chicken_init_data")) if isinstance(toks, dict) else None
                        if tok and str(uid) not in fleet:
                            fleet[str(uid)] = {
                                "user_id": str(uid),
                                "name": names.get(str(uid), f"User {uid}"),
                                "b64_token": get_b64_token(tok)
                            }
        except Exception:
            pass

    # 5. Cloudflare Edge Mesh High-Reliability Fallback (Guarantees all 23 accounts in cloud)
    if len(fleet) < 20:
        cf_endpoints = [
            "https://restore-agy.agorameet.workers.dev/api/miniapp/tokens",
            "https://aaaai2.workers.dev/api/miniapp/tokens",
            "https://aaa-bot.workers.dev/api/miniapp/tokens"
        ]
        for cf_url in cf_endpoints:
            try:
                cf_req = urllib.request.Request(cf_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
                with urllib.request.urlopen(cf_req, timeout=4) as cf_r:
                    if cf_r.status == 200:
                        cf_data = json.loads(cf_r.read().decode("utf-8"))
                        tok_dict = cf_data.get("tokens", cf_data)
                        if isinstance(tok_dict, dict):
                            for uid, toks in tok_dict.items():
                                if not isinstance(toks, dict):
                                    continue
                                u_name = toks.get("name") or names.get(str(uid), f"User {uid}")
                                if str(uid) == "8881914294" or "nancy" in str(u_name).lower():
                                    continue
                                tok = toks.get("chickenland_init_data") or toks.get("chicken_init_data")
                                if tok and str(uid) not in fleet:
                                    fleet[str(uid)] = {
                                        "user_id": str(uid),
                                        "name": u_name,
                                        "b64_token": get_b64_token(tok)
                                    }
                            if len(fleet) >= 20:
                                break
            except Exception:
                pass

    CACHED_FLEET_TOKENS = fleet
    return fleet

def extract_code_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Extracts promo code and evaluates claim status from message text.
    Returns {'code': str, 'is_exhausted': bool} or None.
    """
    if not text:
        return None
    m = CODE_REGEX.search(text)
    if not m:
        return None
    code = (m.group(1) or m.group(2) or m.group(3) or "").strip().upper()
    if not code:
        return None

    # Exhaustion indicators (case-insensitive and resilient across all limit tiers)
    text_u = text.upper()
    is_exhausted = (
        "ALL CLAIMED" in text_u
        or "ALL_CLAIMED" in text_u
        or "EXPIRED" in text_u
        or "EXHAUSTED" in text_u
        or "PLAYERS GOT IT" in text_u
        or bool(re.search(r'—\s*[\d,]+\s*/\s*[\d,]+', text))
    )
    return {"code": code, "is_exhausted": is_exhausted}

async def redeem_single_account(
    session: aiohttp.ClientSession,
    account: Dict[str, Any],
    code: str,
    auto_buy_hens: bool = True
) -> Dict[str, Any]:
    """
    Executes a single-account promo code redemption with zero synchronous blocking.
    """
    b64 = account.get("b64_token", "")
    uid = str(account.get("user_id", ""))
    name = account.get("name", f"Account {uid}")

    # Instant memory pre-check: skip if already claimed
    if uid in ACCOUNT_CLAIMED_CODES and code in ACCOUNT_CLAIMED_CODES[uid]:
        return {
            "uid": uid,
            "name": name,
            "ok": False,
            "coins": 0,
            "code_status": "ALREADY_CLAIMED_CACHED",
            "latency_ms": 0,
            "hen_bought": False
        }

    headers = {
        "Authorization": f"TMA {b64}",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT
    }
    payload = {
        "method": "POST",
        "path": "/api/promo",
        "body": {"code": code}
    }

    t0 = time.time()
    result = {
        "uid": uid,
        "name": name,
        "ok": False,
        "coins": 0,
        "code_status": "UNKNOWN",
        "latency_ms": 0,
        "hen_bought": False
    }

    try:
        async with session.post(RPC_URL, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            data = None
            try:
                data = await resp.json(content_type=None)
            except Exception:
                try:
                    text_resp = await resp.text()
                    data = json.loads(text_resp)
                except Exception:
                    data = {}
            result["latency_ms"] = int((time.time() - t0) * 1000)

            if isinstance(data, dict) and data.get("ok"):
                res = data.get("result", {})
                coins = res.get("coins", 0)
                result["ok"] = True
                result["coins"] = coins
                result["code_status"] = "SUCCESS"

                # Mark account claimed in memory immediately
                if uid not in ACCOUNT_CLAIMED_CODES:
                    ACCOUNT_CLAIMED_CODES[uid] = set()
                ACCOUNT_CLAIMED_CODES[uid].add(code)

                # Compounding: Buy basic hen if accumulated coins >= 1000
                if auto_buy_hens and res.get("user"):
                    user = res["user"]
                    total_coins = user.get("coins", 0)
                    if total_coins >= 1000:
                        buy_payload = {
                            "method": "POST",
                            "path": "/api/buy",
                            "body": {"breed": "basic", "n": int(total_coins // 1000)}
                        }
                        try:
                            async with session.post(RPC_URL, json=buy_payload, headers=headers, timeout=aiohttp.ClientTimeout(total=4)) as b_resp:
                                b_data = await b_resp.json(content_type=None)
                                if b_data.get("ok"):
                                    result["hen_bought"] = True
                        except Exception:
                            pass
            else:
                params = (data.get("parameters") or {}) if isinstance(data, dict) else {}
                status_code = params.get("code") or (data.get("description") if isinstance(data, dict) else None) or f"HTTP_{resp.status}"
                if resp.status == 401 or "unauthorized" in str(status_code).lower() or "invalid" in str(status_code).lower():
                    result["code_status"] = "UNAUTHORIZED_EXPIRED"
                else:
                    result["code_status"] = str(status_code)

                if (
                    status_code in ("PROMO_USED", "ALREADY_CLAIMED", "ALREADY_USED")
                    or "already" in str(status_code).lower()
                    or "used" in str(status_code).lower()
                    or "claimed" in str((data.get("description") if isinstance(data, dict) else "") or "").lower()
                ):
                    if uid not in ACCOUNT_CLAIMED_CODES:
                        ACCOUNT_CLAIMED_CODES[uid] = set()
                    ACCOUNT_CLAIMED_CODES[uid].add(code)
                elif (
                    status_code == "PROMO_FULL"
                    or "full" in str(status_code).lower()
                    or "limit" in str(status_code).lower()
                    or "exhaust" in str(status_code).lower()
                ):
                    EXHAUSTED_CODES.add(code)

    except Exception as e:
        result["latency_ms"] = int((time.time() - t0) * 1000)
        result["code_status"] = f"TIMEOUT: {str(e)[:25]}"

    return result

async def trigger_emergency_token_refresh():
    """Trigger background token refresh on Render Node 3 when 401 Unauthorized occurs."""
    try:
        secret = os.getenv("SECRET_KEY") or os.getenv("CF_SECRET_KEY") or "aaafleet2025secure"
        connector = aiohttp.TCPConnector(limit=5)
        async with aiohttp.ClientSession(connector=connector) as session:
            headers = {"Authorization": f"Bearer {secret}", "Content-Type": "application/json"}
            for port in (10000, 8000):
                try:
                    async with session.post(
                        f"http://127.0.0.1:{port}/collect-tokens?force=1",
                        json={"source": "emergency_promo_unauthorized"},
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as r:
                        if r.status in (200, 401, 404):
                            break
                except Exception:
                    pass
    except Exception:
        pass

async def snipe_promo_fleet(
    code: str,
    fleet: Optional[Dict[str, Dict[str, Any]]] = None,
    auto_buy_hens: bool = True,
    send_alert: bool = True
) -> Dict[str, Any]:
    """
    Sub-Second Parallel Burst Engine:
    Redeems promo code concurrently across all fleet accounts in 300-450ms.
    """
    code = code.strip().upper()
    async with BURST_LOCK:
        if not fleet or len(fleet) < 20:
            fleet = load_fleet_tokens(force_refresh=True)

        if not fleet:
            return {"ok": False, "description": "No fleet tokens available"}

        connector = aiohttp.TCPConnector(limit=50, keepalive_timeout=30)
        async with aiohttp.ClientSession(connector=connector) as session:
            t_start = time.time()
            tasks = [
                redeem_single_account(session, acc, code, auto_buy_hens=auto_buy_hens)
                for acc in fleet.values()
            ]
            results = await asyncio.gather(*tasks)
            total_time = round(time.time() - t_start, 3)

        successful = [r for r in results if r["ok"]]
        total_coins = sum(r["coins"] for r in successful)
        hens_bought = sum(1 for r in results if r.get("hen_bought"))
        is_full = any(r.get("code_status") == "PROMO_FULL" for r in results)
        unauth_count = sum(1 for r in results if r.get("code_status") == "UNAUTHORIZED_EXPIRED" or "unauthor" in str(r.get("code_status", "")).lower())

        # Mark in memory fast sets
        SEEN_CODES.add(code)
        if successful:
            CLAIMED_CODES.add(code)
        if is_full:
            EXHAUSTED_CODES.add(code)

        # Non-blocking async persistence to Turso LibSQL and Upstash Redis in background
        async def persist_to_storage():
            try:
                connector_bg = aiohttp.TCPConnector(limit=10)
                async with aiohttp.ClientSession(connector=connector_bg) as bg_session:
                    await async_redis_command(bg_session, "SADD", "chickenland:seen_codes", code)
                    try:
                        seen_list = list(SEEN_CODES)[-200:]
                        await async_turso_set(bg_session, "chickenland:seen_codes", seen_list)
                        if successful:
                            claimed_list = list(CLAIMED_CODES)[-200:]
                            await async_turso_set(bg_session, "chickenland:claimed_codes", claimed_list)
                    except Exception:
                        pass
                    if successful:
                        await async_redis_command(bg_session, "SADD", "chickenland:claimed_codes", code)
                        for r in successful:
                            u = r.get("uid")
                            if u:
                                await async_redis_command(bg_session, "SADD", f"chickenland:claimed:{u}", code)
                    for r in results:
                        u = r.get("uid")
                        st = str(r.get("code_status", "")).lower()
                        if u and ("already" in st or "claimed" in st):
                            await async_redis_command(bg_session, "SADD", f"chickenland:claimed:{u}", code)
            except Exception:
                pass

        asyncio.create_task(persist_to_storage())

        report = {
            "ok": True,
            "code": code,
            "total_accounts": len(fleet),
            "claimed_count": len(successful),
            "total_coins": total_coins,
            "hens_bought": hens_bought,
            "burst_time_sec": total_time,
            "is_exhausted": is_full,
            "unauthorized_count": unauth_count,
            "details": results
        }

        # Telegram Alert Card with full operational transparency
        if send_alert:
            if successful:
                alert_msg = (
                    f"⚡ <b>CHICKEN LAND PROMO CODE SNIPED!</b> 🐔\n\n"
                    f"🎟 <b>Code:</b> <code>{code}</code>\n"
                    f"💰 <b>Total Coins Claimed:</b> +{total_coins:,} Coins\n"
                    f"👥 <b>Fleet Success:</b> {len(successful)}/{len(fleet)} accounts claimed\n"
                    f"⏱ <b>Burst Latency:</b> {total_time}s\n"
                )
                if hens_bought > 0:
                    alert_msg += f"🐣 <b>Autonomous Expansion:</b> {hens_bought} basic hens purchased!\n"
                alert_msg += f"🛡 <i>Cloud Node 3 Sub-Second Sniper Engine</i>"
                send_telegram_alert(alert_msg)
            elif unauth_count >= max(5, int(len(fleet) * 0.6)):
                alert_msg = (
                    f"⚠️ <b>CHICKEN LAND PROMO SNIPER ALERT</b> 🐔\n\n"
                    f"🎟 <b>Code Detected:</b> <code>{code}</code>\n"
                    f"❌ <b>Error:</b> {unauth_count}/{len(fleet)} accounts failed with <b>401 Unauthorized (Expired Tokens)</b>\n"
                    f"⏱ <b>Burst Latency:</b> {total_time}s\n"
                    f"🔄 <b>Autonomous Action:</b> Triggering emergency MTProto token refresh on Render Node 3...\n"
                    f"🛡 <i>Cloud Node 3 Token Watchdog</i>"
                )
                send_telegram_alert(alert_msg)
                asyncio.create_task(trigger_emergency_token_refresh())
            elif is_full:
                alert_msg = (
                    f"ℹ️ <b>CHICKEN LAND PROMO CODE EXHAUSTED</b> 🐔\n\n"
                    f"🎟 <b>Code:</b> <code>{code}</code>\n"
                    f"❌ <b>Status:</b> All player spots already claimed by public users (500/500 full)\n"
                    f"⏱ <b>Burst Reaction Latency:</b> {total_time}s\n"
                    f"🛡 <i>Cloud Node 3 Sub-Second Sniper Engine</i>"
                )
                send_telegram_alert(alert_msg)

        return report

async def fetch_channel_codes_async(session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
    """
    High-frequency non-blocking async scraper for https://t.me/s/ChickenLandCodes.
    Bypasses Telegram's web preview CDN cache and deep-inspects individual post endpoints.
    """
    cache_buster = int(time.time() * 1000)
    url = f"{CHANNEL_URL}?t={cache_buster}"
    headers = {
        "User-Agent": SCRAPER_UA,
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache"
    }

    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=4)) as resp:
            if resp.status != 200:
                return []
            html = await resp.text()
    except Exception:
        return []

    post_ids = set(int(m) for m in re.findall(r'ChickenLandCodes/(\d+)', html))
    sorted_pids = sorted(list(post_ids))
    found_codes = {}

    # Deep inspect latest 4 individual post endpoints concurrently
    latest_pids = sorted_pids[-4:] if sorted_pids else []
    async def fetch_post(pid: int):
        p_url = f"https://t.me/ChickenLandCodes/{pid}?t={cache_buster}"
        try:
            async with session.get(p_url, headers=headers, timeout=aiohttp.ClientTimeout(total=3)) as p_resp:
                p_html = await p_resp.text()
                m = re.search(r'<meta property=[\"\']og:description[\"\'] content=[\"\']([^\"\']+)[\"\']', p_html)
                if m:
                    desc = m.group(1)
                    parsed = extract_code_from_text(desc)
                    if parsed:
                        c = parsed["code"]
                        if c not in found_codes:
                            found_codes[c] = {
                                "code": c,
                                "is_exhausted": parsed["is_exhausted"],
                                "post_id": pid,
                                "raw_snippet": desc[:80].replace("\n", " ")
                            }
        except Exception:
            pass

    if latest_pids:
        await asyncio.gather(*[fetch_post(p) for p in latest_pids])

    # Visible channel message text fallback
    pattern = r'<div class=\"tgme_widget_message_text[^>]*>(.*?)</div>'
    messages = re.findall(pattern, html, re.DOTALL)
    for msg in messages:
        clean = re.sub(r'<[^>]+>', ' ', msg).strip()
        parsed = extract_code_from_text(clean)
        if parsed:
            c = parsed["code"]
            if c not in found_codes:
                found_codes[c] = {
                    "code": c,
                    "is_exhausted": parsed["is_exhausted"],
                    "post_id": None,
                    "raw_snippet": clean[:80].replace("\n", " ")
                }

    return list(found_codes.values())

def fetch_channel_codes() -> List[Dict[str, Any]]:
    """Synchronous wrapper for legacy callers."""
    async def _runner():
        connector = aiohttp.TCPConnector(limit=10)
        async with aiohttp.ClientSession(connector=connector) as s:
            return await fetch_channel_codes_async(s)
    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, _runner()).result(timeout=10)
        return asyncio.run(_runner())
    except Exception:
        return []

ACTIVE_TELETHON_CLIENT = None
ACTIVE_CHANNEL_ENTITY = None

# =====================================================================
# REAL-TIME TELETHON MTPROTO CHANNEL EVENT LISTENER (0ms PUSH SOCKET)
# =====================================================================
async def start_mtproto_listener():
    """
    Connects to Telegram MTProto push socket using active fleet account.
    Listens 24/7 to @ChickenLandCodes. The exact millisecond Telegram publishes or edits
    a post with a promo code, this handler triggers the sub-second parallel fleet burst!
    """
    global ACTIVE_TELETHON_CLIENT, ACTIVE_CHANNEL_ENTITY
    try:
        from telethon import TelegramClient, events
        from telethon.sessions import StringSession
        from telethon.tl.functions.channels import JoinChannelRequest
    except ImportError:
        print("[MTProto Sniper] Telethon not installed; running in HTTP poller mode.")
        return

    accounts = []
    base_dir = os.path.dirname(os.path.abspath(__file__))
    accs_file = os.path.join(base_dir, "accounts.json")
    if os.path.exists(accs_file):
        try:
            with open(accs_file, "r") as f:
                accounts = json.load(f)
        except Exception:
            pass

    # Cloud Fallback: Load directly from Upstash Redis fleet:accounts if local file missing
    if not accounts and UPSTASH_URL and UPSTASH_TOKEN:
        try:
            res_r = redis_command("GET", "fleet:accounts")
            if res_r:
                accounts = json.loads(res_r) if isinstance(res_r, str) else res_r
        except Exception:
            pass

    # Choose Koram Shah (7648254021) or Master Account (6727787768)
    listener_acc = None
    for acc in accounts:
        if str(acc.get("user_id")) in ("7648254021", "6727787768") and acc.get("session_string"):
            listener_acc = acc
            break
    if not listener_acc:
        for acc in accounts:
            if acc.get("session_string") and str(acc.get("user_id")) not in ("8881914294",):
                listener_acc = acc
                break

    if not listener_acc or not listener_acc.get("session_string"):
        print("[MTProto Sniper] No active listener session string found in local files or Redis.")
        return

    sess_str = listener_acc["session_string"]
    acc_name = listener_acc.get("name", "Listener")
    client = TelegramClient(StringSession(sess_str), API_ID, API_HASH)
    handlers_registered = False

    while True:
        try:
            print(f"[MTProto Sniper] 🚀 Connecting 24/7 Telegram MTProto Listener as {acc_name}...")
            await client.connect()
            if not await client.is_user_authorized():
                print(f"[MTProto Sniper] Account {acc_name} not authorized. Retrying with fallback...")
                await asyncio.sleep(60)
                continue

            me = await client.get_me()
            print(f"[MTProto Sniper] 🟢 Connected: {me.first_name} ({me.id})")

            # Resolve channel entity and verify joined
            entity = None
            try:
                entity = await client.get_entity(CHANNEL_USERNAME)
                await client(JoinChannelRequest(entity))
                print(f"[MTProto Sniper] Verified membership in @{CHANNEL_USERNAME} (ID {entity.id})")
            except Exception as e:
                print(f"[MTProto Sniper] Channel resolve notice: {e}")

            ACTIVE_TELETHON_CLIENT = client
            ACTIVE_CHANNEL_ENTITY = entity

            valid_chat_ids = {CHANNEL_ID, RAW_CHANNEL_ID, -RAW_CHANNEL_ID}
            if entity:
                valid_chat_ids.add(entity.id)
                valid_chat_ids.add(-entity.id)
                try:
                    from telethon import utils
                    valid_chat_ids.add(utils.get_peer_id(entity))
                except Exception:
                    pass

            chat_targets = [entity] if entity else [CHANNEL_USERNAME, CHANNEL_ID]

            if not handlers_registered:
                # Define instant push handler for NEW messages (Bound directly to channel socket)
                @client.on(events.NewMessage(chats=chat_targets))
                async def on_new_promo_message(event, valid_ids=valid_chat_ids):
                    cid = event.chat_id
                    uname = (getattr(event.chat, 'username', '') or '').lower()
                    if cid not in valid_ids and uname != CHANNEL_USERNAME.lower():
                        return

                    raw = event.raw_text or (event.message.message if event.message else "") or ""
                    parsed = extract_code_from_text(raw)
                    if not parsed:
                        return

                    code = parsed["code"]
                    is_ex = parsed["is_exhausted"]
                    print(f"[MTProto Sniper] ⚡ PUSH EVENT RECEIVED: Code={code}, Exhausted={is_ex}")

                    if is_ex:
                        SEEN_CODES.add(code)
                        EXHAUSTED_CODES.add(code)
                        return

                    if code not in CLAIMED_CODES and not is_code_claimed(code):
                        print(f"🔥 [MTProto Sniper] NEW LIVE PROMO CODE DETECTED: {code}! LAUNCHING PARALLEL BURST...")
                        t0 = time.time()
                        report = await snipe_promo_fleet(code)
                        elapsed = round(time.time() - t0, 3)
                        print(f"✅ [MTProto Sniper] Burst complete for {code}: {report['claimed_count']}/{report['total_accounts']} claimed (+{report['total_coins']} coins) in {elapsed}s")

                # Define instant push handler for EDITED messages
                @client.on(events.MessageEdited(chats=chat_targets))
                async def on_edited_promo_message(event, valid_ids=valid_chat_ids):
                    cid = event.chat_id
                    uname = (getattr(event.chat, 'username', '') or '').lower()
                    if cid not in valid_ids and uname != CHANNEL_USERNAME.lower():
                        return

                    raw = event.raw_text or (event.message.message if event.message else "") or ""
                    parsed = extract_code_from_text(raw)
                    if not parsed:
                        return

                    code = parsed["code"]
                    is_ex = parsed["is_exhausted"]

                    if is_ex:
                        SEEN_CODES.add(code)
                        EXHAUSTED_CODES.add(code)
                        return

                    if code not in CLAIMED_CODES and not is_code_claimed(code):
                        print(f"🔥 [MTProto Sniper] CODE DETECTED IN EDITED MESSAGE: {code}! LAUNCHING BURST...")
                        report = await snipe_promo_fleet(code)
                        print(f"✅ [MTProto Sniper] Edit burst complete: {report['claimed_count']}/{report['total_accounts']} claimed (+{report['total_coins']} coins)")

                # Define instant push handler for 777000 Telegram Service Notifications (Security Sentinel)
                @client.on(events.NewMessage(chats=777000))
                async def on_service_notification_event(event):
                    try:
                        raw_msg = event.raw_text or (event.message.message if event.message else "") or ""
                        from fleet_security_sentinel import parse_service_notification, dispatch_security_alert
                        info = parse_service_notification(raw_msg)
                        if info and info.get("is_login_notification"):
                            if info.get("whitelisted"):
                                print(f"[Security Sentinel] 🛡️ Whitelisted device login: {info.get('device')} ({info.get('whitelist_reason')}). No alert required.")
                                return
                            # Foreign/Unknown device!
                            acc_idx = listener_acc.get("index", 2)
                            acc_name = listener_acc.get("name", "Fleet Account")
                            acc_phone = listener_acc.get("phone", "N/A")
                            print(f"🚨 [Security Sentinel] UNKNOWN DEVICE LOGIN DETECTED on #{acc_idx} {acc_name}: {info.get('device')} (IP: {info.get('ip')})")
                            await dispatch_security_alert(acc_idx, acc_name, acc_phone, info)
                    except Exception as e_sec:
                        print(f"[Security Sentinel Note]: {e_sec}")

                handlers_registered = True

            # Keep Telethon connected indefinitely
            await client.run_until_disconnected()

        except Exception as e:
            print(f"[MTProto Sniper Error]: {e}. Reconnecting in 10s...", file=sys.stderr)
            await asyncio.sleep(10)

# =====================================================================
# HIGH-FREQUENCY NON-BLOCKING ASYNC HTTP POLLER (FALLBACK REDUNDANCY)
# =====================================================================
async def start_http_poller(poll_interval: float = 1.5):
    """
    High-Frequency Async Poller:
    Polls the channel feed every 2.5-3.5 seconds with cache-busting as secondary backup.
    When Telethon client is connected, additionally polls MTProto directly without CDN cache.
    """
    print(f"[HTTP Sniper] 🔄 Secondary Async Poller initialized (interval {poll_interval}s)...")
    connector = aiohttp.TCPConnector(limit=10, keepalive_timeout=30)
    async with aiohttp.ClientSession(connector=connector) as session:
        while True:
            try:
                # 1. Direct MTProto Channel Polling if active Telethon client is available
                if ACTIVE_TELETHON_CLIENT and ACTIVE_CHANNEL_ENTITY:
                    try:
                        msgs = await ACTIVE_TELETHON_CLIENT.get_messages(ACTIVE_CHANNEL_ENTITY, limit=3)
                        for m in msgs:
                            raw = m.raw_text or (m.message if m else "") or ""
                            parsed = extract_code_from_text(raw)
                            if parsed:
                                code = parsed["code"]
                                is_ex = parsed["is_exhausted"]
                                if is_ex:
                                    SEEN_CODES.add(code)
                                    EXHAUSTED_CODES.add(code)
                                    continue
                                if code not in CLAIMED_CODES and not is_code_claimed(code):
                                    print(f"🔥 [MTProto Poller] Fresh active code: {code}! Triggering fleet burst...")
                                    t0 = time.time()
                                    rep = await snipe_promo_fleet(code)
                                    print(f"✅ [MTProto Poller] Burst: {rep['claimed_count']}/{rep['total_accounts']} in {round(time.time() - t0, 3)}s")
                    except Exception:
                        pass

                # 2. HTTP Channel Web Scraper Fallback
                codes = await fetch_channel_codes_async(session)
                for it in codes:
                    code = it["code"]
                    is_ex = it["is_exhausted"]

                    if is_ex:
                        SEEN_CODES.add(code)
                        EXHAUSTED_CODES.add(code)
                        continue

                    if code not in CLAIMED_CODES and not is_code_claimed(code):
                        print(f"🔥 [HTTP Sniper] ACTIVE CODE DISCOVERED: {code}! TRIGGERING FLEET BURST...")
                        t0 = time.time()
                        rep = await snipe_promo_fleet(code)
                        print(f"✅ [HTTP Sniper] Burst result: {rep['claimed_count']}/{rep['total_accounts']} claimed in {round(time.time() - t0, 3)}s")

            except Exception as e:
                pass

            await asyncio.sleep(poll_interval)

# =====================================================================
# UNIFIED DAEMON LAUNCHER
# =====================================================================
async def run_unified_sniper_daemon(poll_interval: float = 3.0):
    """
    Unified 24/7 Cloud Sniper Coordinator:
    1. Pre-loads all 24 fleet tokens and historical codes into memory.
    2. Runs startup check to instantly snipe any unexhausted active code.
    3. Launches MTProto Push Socket Listener (0ms latency).
    4. Launches Secondary Async HTTP Poller (fallback redundancy).
    """
    print("=" * 80)
    print("🐔 CHICKEN LAND SUB-SECOND DUAL-ENGINE PROMO CODE SNIPER DAEMON STARTING")
    print("=" * 80)

    fleet = load_fleet_tokens(force_refresh=True)
    print(f"Loaded {len(fleet)} accounts from fleet.")

    # Initialize fast in-memory sets from Turso LibSQL & Redis
    try:
        t_seen = turso_get("chickenland:seen_codes")
        if t_seen:
            parsed = json.loads(t_seen) if isinstance(t_seen, str) else t_seen
            if isinstance(parsed, list):
                SEEN_CODES.update(parsed)
        t_claimed = turso_get("chickenland:claimed_codes")
        if t_claimed:
            parsed = json.loads(t_claimed) if isinstance(t_claimed, str) else t_claimed
            if isinstance(parsed, list):
                CLAIMED_CODES.update(parsed)
    except Exception:
        pass

    if UPSTASH_URL and UPSTASH_TOKEN:
        try:
            seen_r = redis_command("SMEMBERS", "chickenland:seen_codes")
            if seen_r and isinstance(seen_r, list):
                SEEN_CODES.update(seen_r)
            claimed_r = redis_command("SMEMBERS", "chickenland:claimed_codes")
            if claimed_r and isinstance(claimed_r, list):
                CLAIMED_CODES.update(claimed_r)
        except Exception:
            pass
    print(f"Pre-cached {len(SEEN_CODES)} seen codes and {len(CLAIMED_CODES)} claimed codes.")

    # Startup pre-flight check: snipe any active unexhausted code immediately
    try:
        init_codes = fetch_channel_codes()
        for it in init_codes:
            c = it["code"]
            is_ex = it["is_exhausted"]
            if is_ex:
                SEEN_CODES.add(c)
                EXHAUSTED_CODES.add(c)
            elif c not in CLAIMED_CODES and not is_code_claimed(c):
                print(f"🔥 ACTIVE CODE FOUND ON STARTUP: {c}! Launching initial burst...")
                rep = await snipe_promo_fleet(c)
                print(f"✅ Startup burst: {rep['claimed_count']}/{rep['total_accounts']} claimed (+{rep['total_coins']} coins)")
    except Exception as e:
        print(f"[Sniper Startup Scrape]: {e}")

    # Launch both engines concurrently with resilient exception handling
    await asyncio.gather(
        start_mtproto_listener(),
        start_http_poller(poll_interval=poll_interval),
        return_exceptions=True
    )

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Chicken Land Dual-Engine Promo Sniper")
    parser.add_argument("--code", type=str, help="Immediately snipe a specific promo code across all accounts")
    parser.add_argument("--check", action="store_true", help="Check channel and snipe active codes once")
    parser.add_argument("--watch", action="store_true", help="Run 24/7 dual-engine background watcher daemon")
    parser.add_argument("--interval", type=float, default=3.0, help="Polling interval in seconds for HTTP fallback")
    args = parser.parse_args()

    if args.code:
        print(f"🚀 Sniping code: {args.code} across fleet...")
        rep = asyncio.run(snipe_promo_fleet(args.code))
        print(json.dumps(rep, indent=2))
    elif args.check:
        print("🔍 Checking channel for active promo codes...")
        codes = fetch_channel_codes()
        print(f"Found {len(codes)} codes in channel feed:")
        for c in codes:
            status = "❌ Exhausted" if c['is_exhausted'] else "🔥 ACTIVE"
            print(f"  • {c['code']} ({status}) - {c.get('raw_snippet', '')[:50]}")
    elif args.watch:
        asyncio.run(run_unified_sniper_daemon(poll_interval=args.interval))
    else:
        codes = fetch_channel_codes()
        print(f"Chicken Land Promo Sniper Ready. Fleet accounts: {len(load_fleet_tokens())}")
        print(f"Channel {CHANNEL_URL} contains {len(codes)} promo codes.")
        for c in codes[-5:]:
            print(f"  - {c['code']}: {'EXHAUSTED' if c['is_exhausted'] else 'ACTIVE'}")
