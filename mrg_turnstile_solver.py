#!/usr/bin/env python3
"""
MY AGY AI — 100% Cloud MRG Auto-Farming & Turnstile Solver Engine
Runs 100% in Cloud (GitHub Actions / Cloud VMs) — Zero Phone Load.

Solves Cloudflare Turnstile invisibly using Patchright Chromium stealth,
refreshes `humanVerifiedUntil` pass across all 18 accounts,
claims accumulated mining rewards, and compounds miner levels.
"""

import os
import sys
import json
import time
import struct
import hashlib
import base64
import asyncio
import logging
import urllib.parse
import urllib.request
from datetime import datetime, timezone

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("mrg_turnstile_solver")

UPSTASH_URL = os.getenv("UPSTASH_URL") or "https://relaxing-starfish-285827.upstash.io"
UPSTASH_TOKEN = os.getenv("UPSTASH_TOKEN") or "gQAAAAAABFyDAAIgcDI5MDYyYWZjNzYzNzk0ZmRjYjhmNTA4ZDI4ODlmODkzNw"
ALERT_BOT_TOKEN = os.getenv("ALERT_BOT_TOKEN") or "8858823950:AAEdX47g7as1xLYEudfRUHaVGUdNIaU_ku8"
OWNER_ID = os.getenv("OWNER_ID") or "6727787768"

SITE_KEY = "0x4AAAAAAFI-XXL7bFNbLU_J"
APP_ORIGIN = "https://app.mrgtoken.xyz"
API_BASE = "https://mrg.up.railway.app"

VICTORS_SITEKEY = "0x4AAAAAAFD0KRgPRFVwDvgn"
VICTORS_ORIGIN = "https://app.victors.company"
VICTORS_API = "https://server.victors.company/api"
VICTORS_REF = "ref_A20AA96F18"

VYRO_SITEKEY = "0x4AAAAAAFMSnxZaI2W86NOg"
VYRO_ORIGIN = "https://vyro.run.place"
VYRO_API = "https://vyro.run.place/api"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FLEET_TON_WALLETS_FILE = os.path.join(BASE_DIR, "fleet_ton_wallets.json")

def load_fleet_ton_wallets() -> dict:
    if os.path.exists(FLEET_TON_WALLETS_FILE):
        try:
            with open(FLEET_TON_WALLETS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data:
                    return data
        except Exception:
            pass
    # Fallback to Upstash Redis for 100% cloud environments (GitHub Actions, VMs)
    try:
        req = urllib.request.Request(
            f"{UPSTASH_URL}/get/fleet:wallets:ton",
            headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode())
            res = data.get("result")
            if res:
                return json.loads(res) if isinstance(res, str) else res
    except Exception as e:
        logger.warning(f"Error fetching ton wallets from Upstash Redis: {e}")
    return {}

FLEET_UIDS = [
    6727787768,  # Master (Arif Hossain)
    8881914294,  # Nancy
    7648254021,  # Koram
    8826375659,  # Arif
    8450010161,  # Nadim
    8782429452,  # Kaitlyn
    7734849205,  # Node 7
    8025472383,  # Node 8
    8851426148,  # Node 9
    8203342513,  # Node 10
    8190649727,  # MD. Arif
    7487048946,  # Sanzida
    8741547543,  # Abid (3)
    8727040932,  # Node 14
    7749125802,  # Node 15
    7954290138,  # Node 16
    8975442879,  # Node 17
    8841038141   # Node 18
]


def send_tg_alert(text: str):
    """Sends notification to Owner / Backup channel."""
    if not ALERT_BOT_TOKEN or not OWNER_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{ALERT_BOT_TOKEN}/sendMessage"
        payload = json.dumps({
            "chat_id": OWNER_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        logger.warning(f"Telegram notification warning: {e}")


def get_token_from_upstash(uid: int) -> dict:
    """Fetch tokens from Upstash Redis REST."""
    try:
        req = urllib.request.Request(
            f"{UPSTASH_URL}/get/fleet:tokens:{uid}",
            headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            res = data.get("result")
            if res:
                return json.loads(res) if isinstance(res, str) else res
    except Exception as e:
        logger.warning(f"Upstash fetch warning for UID {uid}: {e}")
    return {}


def safe_post(url: str, json_data: dict, extra_headers: dict = None) -> tuple:
    """Synchronous POST request wrapper."""
    headers = {
        "Content-Type": "application/json",
        "Origin": APP_ORIGIN,
        "Referer": f"{APP_ORIGIN}/",
        "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36"
    }
    if extra_headers:
        headers.update(extra_headers)

    data_bytes = json.dumps(json_data).encode("utf-8")
    req = urllib.request.Request(url, data=data_bytes, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as he:
        try:
            body = json.loads(he.read().decode())
            return he.code, body
        except Exception:
            return he.code, {"error": str(he)}
    except Exception as e:
        return 0, {"error": str(e)}


def safe_get(url: str, extra_headers: dict = None) -> tuple:
    """Synchronous GET request wrapper."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36"
    }
    if extra_headers:
        headers.update(extra_headers)

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as he:
        try:
            body = json.loads(he.read().decode())
            return he.code, body
        except Exception:
            return he.code, {"error": str(he)}
    except Exception as e:
        return 0, {"error": str(e)}


def check_account_status(init_data: str) -> dict:
    """Queries /api/user/me to inspect human pass and balances."""
    status_code, body = safe_post(f"{API_BASE}/api/user/me", {"initData": init_data})
    if status_code == 200 and isinstance(body, dict):
        user = body.get("user", {})
        return {
            "success": True,
            "inAppBalance": float(user.get("inAppBalance") or 0),
            "unclaimed": float(user.get("unclaimedMiningBalance") or 0),
            "humanVerifiedUntil": user.get("humanVerifiedUntil"),
            "manualUnlockedLevel": int(user.get("manualUnlockedLevel") or 1),
            "isVerified": user.get("isVerified", False),
            "isTonConnected": user.get("isTonConnected", False),
            "tonWalletAddress": user.get("tonWalletAddress", "")
        }
    return {"success": False, "error": body.get("error", "Unknown error")}


def is_human_pass_active(human_verified_until: str) -> bool:
    """Returns True if human pass is active with at least 45 minutes remaining."""
    if not human_verified_until:
        return False
    try:
        dt = datetime.fromisoformat(human_verified_until.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff_seconds = (dt - now).total_seconds()
        return diff_seconds > 2700  # More than 45 minutes remaining
    except Exception:
        return False


def claim_mining_reward(init_data: str, turnstile_token: str = None) -> dict:
    """Calls /api/user/claim-mining."""
    payload = {
        "initData": init_data,
        "deviceInfo": {
            "model": "SM-S928B",
            "ram": 12,
            "cores": 8,
            "screen": "1440x3120",
            "language": "en-US"
        }
    }
    if turnstile_token:
        payload["turnstileToken"] = turnstile_token

    status_code, body = safe_post(f"{API_BASE}/api/user/claim-mining", payload)
    return body


def verify_human_token(init_data: str, turnstile_token: str) -> dict:
    """Calls /api/user/verify-human."""
    payload = {
        "initData": init_data,
        "turnstileToken": turnstile_token
    }
    status_code, body = safe_post(f"{API_BASE}/api/user/verify-human", payload)
    return body


def auto_unlock_mrg_level(init_data: str, current_level: int, balance: float):
    """Auto-unlocks MRG levels up to 203 if balance allows."""
    if balance < 100:
        return current_level

    def wp_calc(e):
        if e <= 0: return 0
        if e == 1: return 100
        if e <= 203: return round(100 + 9900 * (((e - 1) / 202.0) ** 1.8))
        return 10000

    lo, hi, target_lvl = 1, 203, current_level
    while lo <= hi:
        mid = (lo + hi) // 2
        if balance >= wp_calc(mid):
            target_lvl = mid
            lo = mid + 1
        else:
            hi = mid - 1

    if target_lvl > current_level:
        logger.info(f"⬆️ Upgrading miner level from {current_level} to {target_lvl}...")
        safe_post(f"{API_BASE}/api/user/unlock-level", {"initData": init_data, "level": target_lvl})
        return target_lvl
    return current_level


async def solve_turnstile_for_account(browser, acc_info: dict) -> bool:
    """
    Opens app.mrgtoken.xyz with account's actual Telegram initData in stealth browser.
    Allows the app to mount the Turnstile component, solve it, and invoke verify-human.
    """
    uid = acc_info["uid"]
    m_init = acc_info["init_data"]

    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
        viewport={"width": 412, "height": 915},
        is_mobile=True,
        has_touch=True,
        locale="en-US",
        timezone_id="UTC"
    )

    page = await context.new_page()

    encoded_init = urllib.parse.quote(m_init)
    target_url = f"{APP_ORIGIN}/#tgWebAppData={encoded_init}"

    await page.add_init_script(f"""
        Object.defineProperty(navigator, 'webdriver', {{ get: () => undefined }});

        const mockWebApp = {{
            initData: '{m_init}',
            initDataUnsafe: {{ user: {{ id: {uid} }} }},
            version: '8.0',
            platform: 'android',
            colorScheme: 'dark',
            themeParams: {{}},
            isExpanded: true,
            viewportHeight: 915,
            viewportStableHeight: 915,
            ready: () => {{}},
            expand: () => {{}},
            close: () => {{}},
            onEvent: () => {{}},
            offEvent: () => {{}},
            sendData: () => {{}}
        }};
        let _tg = {{ WebApp: mockWebApp }};
        Object.defineProperty(window, 'Telegram', {{
            configurable: true,
            get: () => _tg,
            set: (v) => {{
                if (v && v.WebApp) {{
                    Object.assign(v.WebApp, mockWebApp);
                    v.WebApp.initData = mockWebApp.initData;
                }}
                _tg = v;
            }}
        }});

        window.__mrgTurnstileToken = null;
        let _ts = undefined;
        Object.defineProperty(window, 'turnstile', {{
            configurable: true,
            get: () => _ts,
            set: (val) => {{
                _ts = val;
                if (val && typeof val.render === 'function' && !val.__hooked) {{
                    val.__hooked = true;
                    const origRender = val.render.bind(val);
                    val.render = function(container, params) {{
                        console.log('[MRG-HOOK] turnstile.render called! action=' + (params.action || 'none'));
                        const origCb = params.callback;
                        params.callback = function(tok) {{
                            console.log('[MRG-HOOK] Turnstile token acquired: ' + tok.substring(0, 16) + '...');
                            window.__mrgTurnstileToken = tok;
                            if (typeof origCb === 'function') origCb(tok);
                        }};
                        return origRender(container, params);
                    }};
                }}
            }}
        }});

        const origFetch = window.fetch;
        window.fetch = async function(...args) {{
            const url = String(args[0] || '');
            if (url.includes('verify-human') || url.includes('claim-mining')) {{
                try {{
                    const body = JSON.parse(args[1]?.body || '{{}}');
                    if (body.turnstileToken) {{
                        window.__mrgTurnstileToken = body.turnstileToken;
                    }}
                }} catch(e) {{}}
            }}
            return await origFetch.apply(this, args);
        }};
    """)

    verified_event = asyncio.Event()
    acquired_token = {"token": None}

    async def handle_response(response):
        try:
            if "verify-human" in response.url:
                res_json = await response.json()
                if res_json.get("success"):
                    logger.info(f"🎉 UID {uid}: Real app received 200 OK from verify-human!")
                    verified_event.set()
        except Exception:
            pass

    async def handle_request(request):
        try:
            if "verify-human" in request.url:
                post_data = request.post_data_json
                if post_data and post_data.get("turnstileToken"):
                    acquired_token["token"] = post_data["turnstileToken"]
        except Exception:
            pass

    page.on("response", handle_response)
    page.on("request", handle_request)
    page.on("console", lambda msg: logger.info(f"[MRG Console UID {uid}] {msg.text}"))

    logger.info(f"⏳ Navigating to {APP_ORIGIN} for UID {uid}...")
    try:
        await page.goto(target_url, wait_until="domcontentloaded", timeout=18000)
    except Exception as e:
        logger.warning(f"UID {uid} navigation note: {e}")

    await asyncio.sleep(2.5)

    # 1. Click Claim or Mine button to mount verification if needed
    try:
        await page.evaluate("""
            () => {
                const btns = Array.from(document.querySelectorAll('button, a, div[role="button"]'));
                const claimBtn = btns.find(b => b.innerText && (b.innerText.toLowerCase().includes('claim') || b.innerText.toLowerCase().includes('verify') || b.innerText.toLowerCase().includes('mine')));
                if (claimBtn) {
                    claimBtn.click();
                    return true;
                }
                return false;
            }
        """)
    except Exception as e:
        logger.warning(f"UID {uid} click note: {e}")

    # 2. Check for passive token or Turnstile iframe
    for _ in range(8):
        if verified_event.is_set():
            break
        tok = await page.evaluate("() => window.__mrgTurnstileToken || (window.turnstile && typeof window.turnstile.getResponse === 'function' ? window.turnstile.getResponse() : null) || null")
        if tok and len(tok) > 20:
            acquired_token["token"] = tok
            break
        try:
            ts_iframe = page.locator("iframe[src*='challenges.cloudflare.com']").first
            if await ts_iframe.count() > 0:
                box = await ts_iframe.bounding_box()
                if box and box["width"] > 0 and box["height"] > 0:
                    click_x = box["x"] + min(32.0, box["width"] / 3)
                    click_y = box["y"] + box["height"] / 2
                    logger.info(f"🖱️ Found Turnstile iframe for MRG UID {uid}! Click at ({click_x:.1f}, {click_y:.1f})...")
                    await page.mouse.move(click_x, click_y, steps=8)
                    await asyncio.sleep(0.15)
                    await page.mouse.down()
                    await asyncio.sleep(0.1)
                    await page.mouse.up()
                else:
                    ts_frame = page.frame_locator("iframe[src*='challenges.cloudflare.com']")
                    stage = ts_frame.locator("#challenge-stage, .ctp-checkbox-label, .mark").first
                    if await stage.count() > 0:
                        await stage.click(timeout=3000)

                for _ in range(15):
                    if verified_event.is_set():
                        break
                    tok = await page.evaluate("() => window.__mrgTurnstileToken || (window.turnstile && typeof window.turnstile.getResponse === 'function' ? window.turnstile.getResponse() : null) || null")
                    if tok and len(tok) > 20:
                        acquired_token["token"] = tok
                        break
                    await asyncio.sleep(1.0)
                break
        except Exception:
            pass
        await asyncio.sleep(1.0)

    if acquired_token["token"]:
        ver_res = verify_human_token(m_init, acquired_token["token"])
        if ver_res.get("success"):
            logger.info(f"🎉 UID {uid}: Turnstile verify-human succeeded via DOM token!")
            save_mrg_pass_to_upstash(uid, acquired_token["token"])
            await context.close()
            return True

    if verified_event.is_set():
        logger.info(f"✅ UID {uid}: Turnstile successfully solved natively by MiniApp!")
        if acquired_token["token"]:
            save_mrg_pass_to_upstash(uid, acquired_token["token"])
        await context.close()
        return True

    # Fallback: programmatic Turnstile render
    solve_js = f"""
        async () => {{
            return new Promise((resolve) => {{
                if (!window.turnstile || typeof window.turnstile.render !== 'function') {{
                    return resolve({{ success: false, error: 'no_turnstile' }});
                }}
                try {{
                    let container = document.getElementById('cf-manual-slot');
                    if (!container) {{
                        container = document.createElement('div');
                        container.id = 'cf-manual-slot';
                        container.style.position = 'fixed';
                        container.style.top = '50%';
                        container.style.left = '50%';
                        container.style.transform = 'translate(-50%, -50%)';
                        container.style.width = '300px';
                        container.style.height = '65px';
                        container.style.zIndex = '9999999';
                        container.style.background = '#18181b';
                        document.body.appendChild(container);
                    }}
                    window.turnstile.render(container, {{
                        sitekey: '{SITE_KEY}',
                        theme: 'light',
                        appearance: 'interaction-only',
                        callback: function(tok) {{
                            window.__mrgTurnstileToken = tok;
                            resolve({{ success: true, token: tok }});
                        }},
                        'error-callback': function(err) {{
                            resolve({{ success: false, error: String(err) }});
                        }}
                    }});
                }} catch (e) {{
                    resolve({{ success: false, error: String(e) }});
                }}
                setTimeout(() => resolve({{ success: false, error: 'timeout_12s' }}), 12000);
            }});
        }}
    """
    try:
        render_res = await page.evaluate(solve_js)
        if render_res and render_res.get("success") and render_res.get("token"):
            tok = render_res["token"]
            logger.info(f"✅ UID {uid}: Programmatic MRG token acquired: {tok[:16]}...")
            ver_res = verify_human_token(m_init, tok)
            if ver_res.get("success"):
                logger.info(f"🎉 UID {uid}: Programmatic verify-human succeeded!")
                save_mrg_pass_to_upstash(uid, tok)
                await context.close()
                return True
    except Exception as e:
        logger.warning(f"UID {uid} evaluate note: {e}")

    await context.close()
    return False


def save_mrg_pass_to_upstash(uid: int, turnstile_token: str):
    """Saves valid MRG turnstile token to Upstash Redis for edge nodes."""
    try:
        req = urllib.request.Request(
            f"{UPSTASH_URL}/set/mrg:pass:{uid}",
            data=json.dumps({"turnstileToken": turnstile_token, "updated_at": time.time()}).encode(),
            headers={"Authorization": f"Bearer {UPSTASH_TOKEN}", "Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            pass
    except Exception as e:
        logger.warning(f"Error saving MRG pass to Redis for UID {uid}: {e}")


def save_victors_pass_to_upstash(uid: int, human_pass: str):
    """Saves valid Victor's Company humanPass to Upstash Redis for edge nodes."""
    try:
        req = urllib.request.Request(
            f"{UPSTASH_URL}/set/victors:pass:{uid}",
            data=json.dumps({"humanPass": human_pass, "updated_at": time.time()}).encode(),
            headers={"Authorization": f"Bearer {UPSTASH_TOKEN}", "Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            pass
    except Exception as e:
        logger.warning(f"Error saving Victor's pass to Redis for UID {uid}: {e}")


async def solve_victors_turnstile(browser, uid: int, v_init: str, is_master: bool) -> bool:
    """
    Solves Turnstile for Victor's Company, logs in, binds referral, and saves humanPass.
    Uses mobile browser stealth context, hooks window.turnstile and window.fetch,
    clicks Cloudflare Turnstile iframe with precise coordinates, and executes full recruitment pipeline.
    """
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
        viewport={"width": 412, "height": 915},
        is_mobile=True,
        has_touch=True,
        locale="en-US",
        timezone_id="UTC"
    )
    page = await context.new_page()
    encoded_init = urllib.parse.quote(v_init)
    target_url = f"{VICTORS_ORIGIN}/#tgWebAppData={encoded_init}"

    ref_to_bind = "" if is_master else VICTORS_REF

    await page.add_init_script(f"""
        Object.defineProperty(navigator, 'webdriver', {{ get: () => undefined }});

        // 1. Hook Telegram WebApp object
        const mockWebApp = {{
            initData: '{v_init}',
            initDataUnsafe: {{
                start_param: '{ref_to_bind}',
                user: {{ id: {uid} }}
            }},
            version: '8.0',
            platform: 'android',
            colorScheme: 'dark',
            themeParams: {{}},
            isExpanded: true,
            viewportHeight: 915,
            viewportStableHeight: 915,
            ready: () => {{}},
            expand: () => {{}},
            close: () => {{}},
            onEvent: () => {{}},
            offEvent: () => {{}},
            sendData: () => {{}}
        }};
        let _tg = {{ WebApp: mockWebApp }};
        Object.defineProperty(window, 'Telegram', {{
            configurable: true,
            get: () => _tg,
            set: (v) => {{
                if (v && v.WebApp) {{
                    Object.assign(v.WebApp, mockWebApp);
                    v.WebApp.initData = mockWebApp.initData;
                    v.WebApp.initDataUnsafe = mockWebApp.initDataUnsafe;
                }}
                _tg = v;
            }}
        }});

        // 2. Hook window.turnstile globally to intercept render callback
        window.__victorsTurnstileToken = null;
        window.__victorsHumanPass = null;
        window.__victorsTurnstileError = null;
        let _ts = undefined;
        Object.defineProperty(window, 'turnstile', {{
            configurable: true,
            get: () => _ts,
            set: (val) => {{
                _ts = val;
                if (val && typeof val.render === 'function' && !val.__hooked) {{
                    val.__hooked = true;
                    const origRender = val.render.bind(val);
                    val.render = function(container, params) {{
                        console.log('[CF-HOOK] turnstile.render called! action=' + (params.action || 'none'));
                        const origCb = params.callback;
                        params.callback = function(tok) {{
                            console.log('[CF-HOOK] Turnstile token acquired: ' + tok.substring(0, 16) + '...');
                            window.__victorsTurnstileToken = tok;
                            if (typeof origCb === 'function') origCb(tok);
                        }};
                        const origErr = params['error-callback'];
                        params['error-callback'] = function(err) {{
                            console.error('[CF-HOOK] Turnstile error: ' + err);
                            window.__victorsTurnstileError = String(err);
                            if (typeof origErr === 'function') origErr(err);
                        }};
                        return origRender(container, params);
                    }};
                }}
            }}
        }});

        // 3. Hook fetch to intercept /auth/login payload & response directly
        const origFetch = window.fetch;
        window.fetch = async function(...args) {{
            const url = String(args[0] || '');
            if (url.includes('/auth/login')) {{
                try {{
                    const body = JSON.parse(args[1]?.body || '{{}}');
                    if (body.turnstileToken) {{
                        window.__victorsTurnstileToken = body.turnstileToken;
                    }}
                }} catch(e) {{}}
            }}
            const res = await origFetch.apply(this, args);
            if (url.includes('/auth/login')) {{
                try {{
                    const clone = res.clone();
                    const data = await clone.json();
                    if (data && data.humanPass) {{
                        window.__victorsHumanPass = data.humanPass;
                        console.log('[CF-HOOK] Captured humanPass from /auth/login: ' + data.humanPass.substring(0, 16) + '...');
                    }}
                }} catch(e) {{}}
            }}
            return res;
        }};
    """)

    page.on("console", lambda msg: logger.info(f"[Victor's Console UID {uid}] {msg.text}"))

    try:
        await page.goto(target_url, wait_until="domcontentloaded", timeout=18000)
    except Exception as e:
        logger.warning(f"[Victor's] UID {uid} navigation note: {e}")

    await asyncio.sleep(2.5)

    acquired_token = None
    acquired_pass = None

    # Step 1: Check if Turnstile solved passively / automatically
    for _ in range(8):
        tok = await page.evaluate("() => window.__victorsTurnstileToken || (window.turnstile && typeof window.turnstile.getResponse === 'function' ? window.turnstile.getResponse() : null) || null")
        if tok and len(tok) > 20:
            acquired_token = tok
            break
        hp = await page.evaluate("() => window.__victorsHumanPass || null")
        if hp:
            acquired_pass = hp
            break
        await asyncio.sleep(1.0)

    # Step 2: If not solved, locate Turnstile iframe and simulate human click
    if not acquired_token and not acquired_pass:
        try:
            ts_iframe = page.locator("iframe[src*='challenges.cloudflare.com']").first
            if await ts_iframe.count() > 0:
                box = await ts_iframe.bounding_box()
                if box and box["width"] > 0 and box["height"] > 0:
                    click_x = box["x"] + min(32.0, box["width"] / 3)
                    click_y = box["y"] + box["height"] / 2
                    logger.info(f"🖱️ [Victor's] Found Turnstile iframe for UID {uid}! Humanized click at ({click_x:.1f}, {click_y:.1f})...")
                    await page.mouse.move(click_x, click_y, steps=10)
                    await asyncio.sleep(0.2)
                    await page.mouse.down()
                    await asyncio.sleep(0.12)
                    await page.mouse.up()
                else:
                    ts_frame = page.frame_locator("iframe[src*='challenges.cloudflare.com']")
                    click_target = ts_frame.locator("#challenge-stage, .ctp-checkbox-label, .mark").first
                    if await click_target.count() > 0:
                        await click_target.click(timeout=3000)
        except Exception as ce:
            logger.warning(f"[Victor's] UID {uid} iframe click note: {ce}")

        # Wait up to 15s after click for token or humanPass
        for _ in range(15):
            tok = await page.evaluate("() => window.__victorsTurnstileToken || (window.turnstile && typeof window.turnstile.getResponse === 'function' ? window.turnstile.getResponse() : null) || null")
            if tok and len(tok) > 20:
                acquired_token = tok
                break
            hp = await page.evaluate("() => window.__victorsHumanPass || null")
            if hp:
                acquired_pass = hp
                break
            await asyncio.sleep(1.0)

    # Step 3: Programmatic fallback render with exact Turnstile parameters
    if not acquired_token and not acquired_pass:
        logger.info(f"⚡ [Victor's] UID {uid}: Attempting programmatic Turnstile render with action='login'...")
        solve_js = f"""
            async () => {{
                return new Promise((resolve) => {{
                    if (!window.turnstile || typeof window.turnstile.render !== 'function') {{
                        return resolve({{ success: false, error: 'no_turnstile' }});
                    }}
                    try {{
                        let container = document.getElementById('cf-vic-slot');
                        if (!container) {{
                            container = document.createElement('div');
                            container.id = 'cf-vic-slot';
                            container.style.position = 'fixed';
                            container.style.top = '50%';
                            container.style.left = '50%';
                            container.style.transform = 'translate(-50%, -50%)';
                            container.style.width = '300px';
                            container.style.height = '65px';
                            container.style.zIndex = '9999999';
                            container.style.background = '#1a1147';
                            document.body.appendChild(container);
                        }}
                        window.turnstile.render(container, {{
                            sitekey: '{VICTORS_SITEKEY}',
                            action: 'login',
                            theme: 'light',
                            appearance: 'interaction-only',
                            callback: function(tok) {{
                                window.__victorsTurnstileToken = tok;
                                resolve({{ success: true, token: tok }});
                            }},
                            'error-callback': function(err) {{
                                resolve({{ success: false, error: String(err) }});
                            }}
                        }});
                    }} catch (e) {{
                        resolve({{ success: false, error: String(e) }});
                    }}
                    setTimeout(() => resolve({{ success: false, error: 'timeout_12s' }}), 12000);
                }});
            }}
        """
        try:
            render_res = await page.evaluate(solve_js)
            if render_res and render_res.get("success") and render_res.get("token"):
                acquired_token = render_res["token"]
        except Exception as re:
            logger.warning(f"[Victor's] UID {uid} programmatic render note: {re}")

    await context.close()

    # Step 4: Exchange acquired Turnstile token for humanPass via POST /api/auth/login
    if not acquired_pass and acquired_token:
        logger.info(f"✅ [Victor's] UID {uid}: Turnstile solved ({acquired_token[:16]}...)! Calling /auth/login...")
        login_p = {
            "turnstileToken": acquired_token
        }
        if not is_master:
            login_p["startParam"] = VICTORS_REF

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"tma {v_init}",
            "Origin": VICTORS_ORIGIN,
            "Referer": f"{VICTORS_ORIGIN}/",
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 Mobile"
        }
        st_code, body = safe_post(f"{VICTORS_API}/auth/login", login_p, extra_headers=headers)
        if st_code in (200, 201) and isinstance(body, dict):
            hp = body.get("humanPass") or (body.get("data", {}).get("humanPass") if isinstance(body.get("data"), dict) else None)
            if hp:
                acquired_pass = str(hp)
        else:
            logger.warning(f"[Victor's] UID {uid} /auth/login response: {st_code} {body}")

    # Step 5: Save humanPass to Upstash Redis and execute recruitment & farming pipeline
    if acquired_pass:
        save_victors_pass_to_upstash(uid, str(acquired_pass))
        logger.info(f"🎉 [Victor's] UID {uid}: Successfully obtained humanPass: {str(acquired_pass)[:16]}... (Saved to Redis)")

        v_authed_headers = {
            "Content-Type": "application/json",
            "Authorization": f"tma {v_init}",
            "x-human-pass": str(acquired_pass),
            "Origin": VICTORS_ORIGIN,
            "Referer": f"{VICTORS_ORIGIN}/",
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 Mobile"
        }

        # 1. Complete tutorial & daily check-in
        safe_post(f"{VICTORS_API}/me/tutorial", {}, extra_headers=v_authed_headers)
        safe_post(f"{VICTORS_API}/checkin", {}, extra_headers=v_authed_headers)

        # 2. Connect TON wallet to qualify recruit & unlock Level 1 Miner
        fleet_ton_wallets = load_fleet_ton_wallets()
        w_entry = fleet_ton_wallets.get(str(uid)) or fleet_ton_wallets.get(uid)
        if w_entry and w_entry.get("address"):
            ton_addr = w_entry["address"]
            c_code, c_res = safe_post(f"{VICTORS_API}/wallet/connect", {"address": ton_addr}, extra_headers=v_authed_headers)
            logger.info(f"💼 [Victor's] UID {uid}: Connected TON wallet {ton_addr[:12]}...: {c_code}")

            # Claim connect-wallet task to qualify recruit and trigger referral rewards
            t_code, t_res = safe_post(f"{VICTORS_API}/tasks/claim", {"taskId": "connect-wallet"}, extra_headers=v_authed_headers)
            logger.info(f"🎯 [Victor's] UID {uid}: Claimed connect-wallet task: {t_code} {t_res}")

        # 3. Claim daily passive mining
        m_code, m_res = safe_post(f"{VICTORS_API}/mining/claim", {}, extra_headers=v_authed_headers)
        logger.info(f"⛏️ [Victor's] UID {uid}: Mining claim: {m_code} {m_res}")

        # 4. Check profile and unlock levels if available
        p_code, p_res = safe_get(f"{VICTORS_API}/me", extra_headers=v_authed_headers)
        if p_code == 200 and isinstance(p_res, dict):
            u_info = p_res.get("user") or p_res
            cur_lvl = u_info.get("level", 1)
            unlocked = u_info.get("unlockedLevel", cur_lvl)
            if unlocked > cur_lvl:
                safe_post(f"{VICTORS_API}/levels/unlock", {"level": unlocked}, extra_headers=v_authed_headers)
                logger.info(f"⬆️ [Victor's] UID {uid}: Miner level upgraded to {unlocked}!")

        # 5. Play arcade minigame
        try:
            _, arc_d = safe_get(f"{VICTORS_API}/arcade", extra_headers=v_authed_headers)
            if arc_d and isinstance(arc_d, dict) and arc_d.get("runsLeft", 0) > 0:
                st_c, _ = safe_post(f"{VICTORS_API}/arcade/mine/start", {"tool": "pickaxe", "items": []}, extra_headers=v_authed_headers)
                if st_c in (200, 201):
                    for d in range(4):
                        _, d_res = safe_post(f"{VICTORS_API}/arcade/mine/dig", {"x": 4, "y": d}, extra_headers=v_authed_headers)
                        if not d_res or (isinstance(d_res, dict) and d_res.get("result") == "bust"):
                            break
                    safe_post(f"{VICTORS_API}/arcade/mine/end", {}, extra_headers=v_authed_headers)
                    logger.info(f"🎮 [Victor's] UID {uid}: Arcade run completed.")
        except Exception:
            pass

        # 6. If Master Account: sweep referral hiring bonuses & commissions
        if is_master:
            b_code, b_res = safe_post(f"{VICTORS_API}/referral/claim-bonus", {}, extra_headers=v_authed_headers)
            c_code, c_res = safe_post(f"{VICTORS_API}/referral/claim-commission", {}, extra_headers=v_authed_headers)
            logger.info(f"👑 [Victor's] Master recruitment bonus: {b_code} {b_res}, commissions: {c_code} {c_res}")

        return True

    return False


def create_ton_proof(wallet_entry: dict, payload_nonce: str) -> dict:
    """Creates a TonConnect 2.0 proof-of-ownership payload signed with the account's TON key."""
    from nacl.signing import SigningKey
    from tonsdk.contract.wallet import Wallets, WalletVersionEnum
    from tonsdk.utils import Address

    mnemonic = wallet_entry.get("mnemonic")
    if not mnemonic:
        raise ValueError("Missing mnemonic in wallet entry")
    words = mnemonic.split() if isinstance(mnemonic, str) else mnemonic
    _, pub_key_bytes, priv_key_bytes, wallet_contract = Wallets.from_mnemonics(
        mnemonics=words, version=WalletVersionEnum.v4r2
    )
    state_init_res = wallet_contract.create_state_init()
    state_init_b64 = base64.b64encode(state_init_res["state_init"].to_boc(False)).decode("utf-8")

    t_addr = Address(wallet_entry["address"])
    wc = t_addr.wc
    addr_hash = t_addr.hash_part

    domain = "vyro.run.place"
    timestamp = int(time.time())

    # Standard TonConnect 2.0 ton-proof-item-v2 structure
    prefix = b"ton-proof-item-v2/"
    wc_bytes = struct.pack(">i", wc)
    domain_bytes = domain.encode("utf-8")
    domain_len = struct.pack("<I", len(domain_bytes))
    ts_bytes = struct.pack("<Q", timestamp)
    payload_bytes = payload_nonce.encode("utf-8")

    msg = prefix + wc_bytes + addr_hash + domain_len + domain_bytes + ts_bytes + payload_bytes
    msg_hash = hashlib.sha256(msg).digest()
    full_msg = b"\xff\xff" + b"ton-connect" + msg_hash
    digest = hashlib.sha256(full_msg).digest()

    signing_key = SigningKey(priv_key_bytes[:32])
    sig = signing_key.sign(digest).signature
    sig_b64 = base64.b64encode(sig).decode("utf-8")

    raw_addr = f"{wc}:{addr_hash.hex()}"

    return {
        "address": raw_addr,
        "chain": "-239",
        "publicKey": pub_key_bytes.hex(),
        "walletStateInit": state_init_b64,
        "proof": {
            "timestamp": timestamp,
            "domain": {
                "lengthBytes": len(domain_bytes),
                "value": domain
            },
            "signature": sig_b64,
            "payload": payload_nonce
        }
    }


async def solve_vyro_wallet_onboarding(browser, uid: int, vyro_init: str, wallet_entry: dict) -> bool:
    """
    Checks Vyro wallet status. If unconnected, solves Turnstile challenge,
    signs TonConnect 2.0 proof with account's dedicated TON key, connects wallet,
    and starts mining. If already connected, verifies and triggers mining start.
    """
    v_headers = {
        "Authorization": f"tma {vyro_init}",
        "Content-Type": "application/json",
        "Origin": VYRO_ORIGIN,
        "Referer": f"{VYRO_ORIGIN}/",
        "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 Mobile"
    }

    # 1. Check bootstrap status first
    boot_status, boot_data = safe_get(f"{VYRO_API}/bootstrap", extra_headers=v_headers)
    if not isinstance(boot_data, dict):
        boot_data = {}

    is_wallet_connected = boot_data.get("wallet", {}).get("connected", False)
    mining_status = boot_data.get("mining", {}).get("status", "IDLE")

    if is_wallet_connected:
        logger.info(f"⚡ [VyroDrop] UID {uid}: Wallet already connected ({boot_data.get('wallet', {}).get('friendlyAddress')}).")
        # If mining is IDLE, start mining
        if mining_status == "IDLE":
            st_code, m_res = safe_post(f"{VYRO_API}/mining/start", {}, extra_headers=v_headers)
            if st_code in (200, 201):
                logger.info(f"⛏️ [VyroDrop] UID {uid}: Mining successfully started: {m_res.get('mining', {}).get('status', 'ACTIVE')}")
            else:
                logger.warning(f"[VyroDrop] UID {uid} mining/start response: {st_code} {m_res}")

        # Claim mining if active or ready
        mining_obj = boot_data.get("mining", {})
        session_id = mining_obj.get("sessionId")
        if session_id and (mining_status in ("READY", "ACTIVE") or float(mining_obj.get("claimablePreviewRaw") or 0) > 0):
            cl_code, cl_res = safe_post(f"{VYRO_API}/mining/claim", {"sessionId": session_id}, extra_headers=v_headers)
            logger.info(f"⛏️ [VyroDrop] UID {uid}: Mining claimed: {cl_code} {cl_res}")

        # If Master Account: sweep referral commission
        if uid == 6727787768 or str(uid) == str(OWNER_ID):
            ref_code, ref_res = safe_post(f"{VYRO_API}/referrals/claim", {}, extra_headers=v_headers)
            logger.info(f"👑 [VyroDrop] Master referral sweep: {ref_code} {ref_res}")
        return True

    # 2. Wallet needs connection. Check if we have dedicated TON wallet
    if not wallet_entry or not wallet_entry.get("mnemonic"):
        logger.error(f"❌ [VyroDrop] UID {uid}: No dedicated TON wallet / mnemonic found in fleet_ton_wallets.json!")
        return False

    user_id = boot_data.get("user", {}).get("id") or ""
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
        viewport={"width": 412, "height": 915},
        is_mobile=True,
        has_touch=True,
        locale="en-US",
        timezone_id="UTC"
    )
    page = await context.new_page()
    encoded_init = urllib.parse.quote(vyro_init)
    target_url = f"{VYRO_ORIGIN}/#tgWebAppData={encoded_init}"

    await page.add_init_script(f"""
        Object.defineProperty(navigator, 'webdriver', {{ get: () => undefined }});

        const mockWebApp = {{
            initData: '{vyro_init}',
            initDataUnsafe: {{ user: {{ id: {uid} }} }},
            version: '8.0',
            platform: 'android',
            colorScheme: 'dark',
            themeParams: {{}},
            isExpanded: true,
            viewportHeight: 915,
            viewportStableHeight: 915,
            ready: () => {{}},
            expand: () => {{}},
            close: () => {{}},
            onEvent: () => {{}},
            offEvent: () => {{}},
            sendData: () => {{}}
        }};
        let _tg = {{ WebApp: mockWebApp }};
        Object.defineProperty(window, 'Telegram', {{
            configurable: true,
            get: () => _tg,
            set: (v) => {{
                if (v && v.WebApp) {{
                    Object.assign(v.WebApp, mockWebApp);
                    v.WebApp.initData = mockWebApp.initData;
                }}
                _tg = v;
            }}
        }});

        window.__vyroTurnstileToken = null;
        let _ts = undefined;
        Object.defineProperty(window, 'turnstile', {{
            configurable: true,
            get: () => _ts,
            set: (val) => {{
                _ts = val;
                if (val && typeof val.render === 'function' && !val.__hooked) {{
                    val.__hooked = true;
                    const origRender = val.render.bind(val);
                    val.render = function(container, params) {{
                        console.log('[VYRO-HOOK] turnstile.render called! action=' + (params.action || 'none'));
                        const origCb = params.callback;
                        params.callback = function(tok) {{
                            console.log('[VYRO-HOOK] Turnstile token acquired: ' + tok.substring(0, 16) + '...');
                            window.__vyroTurnstileToken = tok;
                            if (typeof origCb === 'function') origCb(tok);
                        }};
                        return origRender(container, params);
                    }};
                }}
            }}
        }});

        const origFetch = window.fetch;
        window.fetch = async function(...args) {{
            const url = String(args[0] || '');
            if (url.includes('wallet/challenge')) {{
                try {{
                    const body = JSON.parse(args[1]?.body || '{{}}');
                    if (body.turnstileToken) {{
                        window.__vyroTurnstileToken = body.turnstileToken;
                    }}
                }} catch(e) {{}}
            }}
            return await origFetch.apply(this, args);
        }};
    """)

    acquired_token = {"token": None}

    async def handle_request(request):
        try:
            if "wallet/challenge" in request.url:
                post_data = request.post_data_json
                if post_data and post_data.get("turnstileToken"):
                    acquired_token["token"] = post_data["turnstileToken"]
        except Exception:
            pass

    page.on("request", handle_request)
    page.on("console", lambda msg: logger.info(f"[Vyro Console UID {uid}] {msg.text}"))

    try:
        await page.goto(target_url, wait_until="domcontentloaded", timeout=18000)
    except Exception as e:
        logger.warning(f"[VyroDrop] UID {uid} navigation note: {e}")

    await asyncio.sleep(2.5)

    # 1. Passive / auto-solve check
    for _ in range(8):
        tok = await page.evaluate("() => window.__vyroTurnstileToken || (window.turnstile && typeof window.turnstile.getResponse === 'function' ? window.turnstile.getResponse() : null) || null")
        if tok and len(tok) > 20:
            acquired_token["token"] = tok
            break
        await asyncio.sleep(1.0)

    # 2. Check for native Turnstile iframe and simulate click
    if not acquired_token["token"]:
        try:
            ts_iframe = page.locator("iframe[src*='challenges.cloudflare.com']").first
            if await ts_iframe.count() > 0:
                box = await ts_iframe.bounding_box()
                if box and box["width"] > 0 and box["height"] > 0:
                    click_x = box["x"] + min(32.0, box["width"] / 3)
                    click_y = box["y"] + box["height"] / 2
                    logger.info(f"🖱️ [VyroDrop] Found Turnstile iframe for UID {uid}! Humanized click at ({click_x:.1f}, {click_y:.1f})...")
                    await page.mouse.move(click_x, click_y, steps=10)
                    await asyncio.sleep(0.2)
                    await page.mouse.down()
                    await asyncio.sleep(0.12)
                    await page.mouse.up()
                else:
                    ts_frame = page.frame_locator("iframe[src*='challenges.cloudflare.com']")
                    click_target = ts_frame.locator("#challenge-stage, .ctp-checkbox-label, .mark").first
                    if await click_target.count() > 0:
                        await click_target.click(timeout=3000)
        except Exception as ce:
            logger.warning(f"[VyroDrop] UID {uid} iframe click note: {ce}")

        for _ in range(15):
            tok = await page.evaluate("() => window.__vyroTurnstileToken || (window.turnstile && typeof window.turnstile.getResponse === 'function' ? window.turnstile.getResponse() : null) || null")
            if tok and len(tok) > 20:
                acquired_token["token"] = tok
                break
            await asyncio.sleep(1.0)

    # 3. Fallback: programmatic render of Turnstile for Vyro
    if not acquired_token["token"]:
        solve_js = f"""
            async () => {{
                return new Promise((resolve) => {{
                    if (!window.turnstile || typeof window.turnstile.render !== 'function') {{
                        return resolve({{ success: false, error: 'no_turnstile' }});
                    }}
                    try {{
                        let container = document.getElementById('cf-vyro-slot');
                        if (!container) {{
                            container = document.createElement('div');
                            container.id = 'cf-vyro-slot';
                            container.style.position = 'fixed';
                            container.style.top = '50%';
                            container.style.left = '50%';
                            container.style.transform = 'translate(-50%, -50%)';
                            container.style.width = '300px';
                            container.style.height = '65px';
                            container.style.zIndex = '9999999';
                            container.style.background = '#18181b';
                            document.body.appendChild(container);
                        }}
                        window.turnstile.render(container, {{
                            sitekey: '{VYRO_SITEKEY}',
                            action: 'wallet_onboarding',
                            cdata: '{user_id}',
                            theme: 'light',
                            appearance: 'interaction-only',
                            callback: function(tok) {{
                                window.__vyroTurnstileToken = tok;
                                resolve({{ success: true, token: tok }});
                            }},
                            'error-callback': function(err) {{
                                resolve({{ success: false, error: String(err) }});
                            }}
                        }});
                    }} catch (e) {{
                        resolve({{ success: false, error: String(e) }});
                    }}
                    setTimeout(() => resolve({{ success: false, error: 'Turnstile timeout' }}), 12000);
                }});
            }}
        """
        try:
            res = await page.evaluate(solve_js)
            if res and res.get("success") and res.get("token"):
                acquired_token["token"] = res["token"]
        except Exception as e:
            logger.warning(f"[VyroDrop] UID {uid} manual solve error: {e}")

    await context.close()

    # 3. Submit challenge to get nonce payload
    challenge_payload = {}
    if acquired_token["token"]:
        challenge_payload["turnstileToken"] = acquired_token["token"]

    ch_code, ch_body = safe_post(f"{VYRO_API}/wallet/challenge", challenge_payload, extra_headers=v_headers)
    if ch_code not in (200, 201) or not isinstance(ch_body, dict) or not ch_body.get("payload"):
        logger.error(f"❌ [VyroDrop] UID {uid}: Challenge rejected: {ch_code} {ch_body}")
        return False

    nonce = ch_body["payload"]
    logger.info(f"🔑 [VyroDrop] UID {uid}: Challenge nonce received: {nonce[:12]}...")

    # 4. Sign TonConnect 2.0 proof
    try:
        connect_payload = create_ton_proof(wallet_entry, nonce)
    except Exception as pe:
        logger.error(f"❌ [VyroDrop] UID {uid}: TonConnect proof generation failed: {pe}")
        return False

    # 5. Connect wallet
    conn_code, conn_body = safe_post(f"{VYRO_API}/wallet/connect", connect_payload, extra_headers=v_headers)
    if conn_code not in (200, 201):
        logger.error(f"❌ [VyroDrop] UID {uid}: Wallet connect failed: {conn_code} {conn_body}")
        return False

    logger.info(f"🎉 [VyroDrop] UID {uid}: Wallet successfully connected! Bound address: {wallet_entry.get('address')[:12]}...")

    # 6. Start mining
    st_code, m_res = safe_post(f"{VYRO_API}/mining/start", {}, extra_headers=v_headers)
    if st_code in (200, 201):
        logger.info(f"⛏️ [VyroDrop] UID {uid}: Mining started successfully!")

    # 7. If Master Account: sweep referral commission
    if uid == 6727787768 or str(uid) == str(OWNER_ID):
        ref_code, ref_res = safe_post(f"{VYRO_API}/referrals/claim", {}, extra_headers=v_headers)
        logger.info(f"👑 [VyroDrop] Master referral sweep post-connect: {ref_code} {ref_res}")

    return True


async def run_mrg_auto_solver():
    """Main workflow: audits all 18 accounts, solves needed challenges, connects wallets, and auto-claims."""
    logger.info("====================================================================")
    logger.info("🚀 Starting 100% Cloud Fleet Auto-Farming & Turnstile Solver Cycle")
    logger.info("====================================================================")

    fleet_ton_wallets = load_fleet_ton_wallets()
    accounts_data = []
    accounts_needing_solver = []
    victors_accounts = []
    vyro_accounts = []

    # 1. Fetch tokens and inspect account states
    for idx, uid in enumerate(FLEET_UIDS, 1):
        tok_dict = get_token_from_upstash(uid)
        mrg_init = tok_dict.get("mrg_init_data")
        vic_init = tok_dict.get("victors_init_data")
        vyro_init = tok_dict.get("vyro_init_data")

        if vic_init:
            victors_accounts.append({
                "uid": uid,
                "init_data": vic_init
            })

        if vyro_init:
            vyro_accounts.append({
                "uid": uid,
                "init_data": vyro_init
            })

        if not mrg_init:
            logger.warning(f"[{idx:02d}/18] UID {uid}: No mrg_init_data found in Upstash. Skipping.")
            continue

        if mrg_init.startswith("user%3D") or "%257B" in mrg_init or "%2522" in mrg_init:
            mrg_init = urllib.parse.unquote(mrg_init)

        stat = check_account_status(mrg_init)
        if not stat.get("success"):
            logger.warning(f"[{idx:02d}/18] UID {uid}: Could not fetch account status ({stat.get('error')}).")
            continue

        has_active_pass = is_human_pass_active(stat.get("humanVerifiedUntil"))
        acc_info = {
            "uid": uid,
            "idx": idx,
            "init_data": mrg_init,
            "stat": stat,
            "has_active_pass": has_active_pass
        }
        accounts_data.append(acc_info)

        if not has_active_pass:
            accounts_needing_solver.append(acc_info)
            logger.info(
                f"[{idx:02d}/18] UID {uid}: ⚠️ Human pass needed. "
                f"Bal: {stat['inAppBalance']:.1f} MRG, Unclaimed: {stat['unclaimed']:.2f} MRG (Lvl {stat['manualUnlockedLevel']})"
            )
        else:
            logger.info(
                f"[{idx:02d}/18] UID {uid}: ✅ Human pass already active until {stat['humanVerifiedUntil']}. "
                f"Bal: {stat['inAppBalance']:.1f} MRG, Unclaimed: {stat['unclaimed']:.2f} MRG"
            )

    needed_count = len(accounts_needing_solver)
    logger.info(
        f"📊 Audit Summary: {len(accounts_data)} accounts connected. "
        f"{needed_count} accounts require MRG Turnstile. "
        f"{len(victors_accounts)} accounts found with Victor's Company. "
        f"{len(vyro_accounts)} accounts found with VyroDrop."
    )

    # 2. Launch stealth browser and process accounts needing verification
    solved_count = 0
    total_claimed_mrg = 0.0
    victors_solved = 0
    vyro_wallets_connected = 0

    if needed_count > 0 or len(victors_accounts) > 0 or len(vyro_accounts) > 0:
        # Import patchright (or fallback to playwright)
        try:
            from patchright.async_api import async_playwright
            logger.info("🛡️ Using Patchright stealth browser engine.")
        except ImportError:
            from playwright.async_api import async_playwright
            logger.info("🌐 Using Playwright browser engine.")

        # Prioritize Master Account (6727787768) first in every queue
        accounts_needing_solver.sort(key=lambda a: 0 if a["uid"] == 6727787768 else 1)
        victors_accounts.sort(key=lambda a: 0 if a["uid"] == 6727787768 else 1)
        vyro_accounts.sort(key=lambda a: 0 if a["uid"] == 6727787768 else 1)

        is_xvfb = bool(os.getenv("DISPLAY") or os.getenv("CI"))
        headless_flag = False if is_xvfb else True
        logger.info(f"🖥️ Launching Chromium (headless={headless_flag}, DISPLAY={os.getenv('DISPLAY')}, CI={os.getenv('CI')})...")

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=headless_flag,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                    "--window-size=1280,800"
                ]
            )

            # A. Solve MRG passes
            for acc in accounts_needing_solver:
                uid = acc["uid"]
                m_init = acc["init_data"]
                try:
                    success = await asyncio.wait_for(solve_turnstile_for_account(browser, acc), timeout=55.0)
                except asyncio.TimeoutError:
                    logger.warning(f"MRG Turnstile timed out (55s) for UID {uid}")
                    success = False
                except Exception as me:
                    logger.warning(f"MRG Turnstile exception for UID {uid}: {me}")
                    success = False

                if success:
                    solved_count += 1
                    # Claim accumulated mining rewards
                    claim_res = claim_mining_reward(m_init)
                    claimed_amt = float(claim_res.get("claimedAmount") or acc["stat"]["unclaimed"])
                    total_claimed_mrg += claimed_amt
                    logger.info(f"⛏️ UID {uid}: Successfully claimed {claimed_amt:.2f} MRG! Miner restarted.")

                    # Auto-upgrade level if balance allows
                    new_bal = acc["stat"]["inAppBalance"] + claimed_amt
                    auto_unlock_mrg_level(m_init, acc["stat"]["manualUnlockedLevel"], new_bal)

                await asyncio.sleep(1.0)

            # B. Solve Victor's Company passes & qualify recruits
            for v_acc in victors_accounts:
                v_uid = v_acc["uid"]
                v_init = v_acc["init_data"]
                try:
                    v_res = await asyncio.wait_for(
                        solve_victors_turnstile(browser, v_uid, v_init, is_master=(v_uid == 6727787768)),
                        timeout=55.0
                    )
                    if v_res:
                        victors_solved += 1
                except asyncio.TimeoutError:
                    logger.warning(f"Victor's solve timed out (55s) for UID {v_uid}")
                except Exception as ve:
                    logger.warning(f"Victor's solve exception for UID {v_uid}: {ve}")
                await asyncio.sleep(1.0)

            # C. Solve VyroDrop wallet onboarding & start mining
            for vy_acc in vyro_accounts:
                vy_uid = vy_acc["uid"]
                vy_init = vy_acc["init_data"]
                w_entry = fleet_ton_wallets.get(str(vy_uid)) or fleet_ton_wallets.get(vy_uid)
                try:
                    vy_res = await asyncio.wait_for(
                        solve_vyro_wallet_onboarding(browser, vy_uid, vy_init, w_entry),
                        timeout=55.0
                    )
                    if vy_res:
                        vyro_wallets_connected += 1
                except asyncio.TimeoutError:
                    logger.warning(f"VyroDrop solve timed out (55s) for UID {vy_uid}")
                except Exception as vye:
                    logger.warning(f"VyroDrop onboarding exception for UID {vy_uid}: {vye}")
                await asyncio.sleep(1.0)

            await browser.close()

    # 3. Also claim rewards for accounts that already had an active pass
    for acc in accounts_data:
        if acc["has_active_pass"]:
            uid = acc["uid"]
            m_init = acc["init_data"]
            if acc["stat"]["unclaimed"] > 0.05:
                claim_res = claim_mining_reward(m_init)
                if claim_res.get("success"):
                    claimed_amt = float(claim_res.get("claimedAmount") or acc["stat"]["unclaimed"])
                    total_claimed_mrg += claimed_amt
                    logger.info(f"⛏️ UID {uid}: Auto-claimed active pass reward: {claimed_amt:.2f} MRG.")
                    new_bal = acc["stat"]["inAppBalance"] + claimed_amt
                    auto_unlock_mrg_level(m_init, acc["stat"]["manualUnlockedLevel"], new_bal)

    # 4. Master Account Referral Sweep
    master_acc = next((a for a in accounts_data if a["uid"] == 6727787768), None)
    if master_acc:
        m_init = master_acc["init_data"]
        safe_post(f"{API_BASE}/api/user/claim-commission", {"initData": m_init})
        safe_post(f"{API_BASE}/api/user/claim-one-time-bonus", {"initData": m_init})
        logger.info("👑 Master Account referral commission and team bonus claimed.")

    # 5. Telegram Telemetry Notification
    report_msg = (
        f"🚀 <b>MRG, Victor's & Vyro Cloud Turnstile Engine Report</b>\n\n"
        f"• <b>Total Fleet Accounts:</b> 18\n"
        f"• <b>MRG Pass Solved:</b> {solved_count}/{needed_count}\n"
        f"• <b>Victor's Pass Solved:</b> {victors_solved}/{len(victors_accounts)}\n"
        f"• <b>VyroDrop Wallets & Mining:</b> {vyro_wallets_connected}/{len(vyro_accounts)}\n"
        f"• <b>Total MRG Harvested:</b> {total_claimed_mrg:.2f} MRG\n"
        f"• <b>Execution Time:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
        f"⚡ <i>100% Cloud Execution. Zero phone load.</i>"
    )
    logger.info(
        f"📢 Telemetry: MRG Solved {solved_count}/{needed_count}, "
        f"Victor's Solved {victors_solved}/{len(victors_accounts)}, "
        f"Vyro Connected {vyro_wallets_connected}/{len(vyro_accounts)}, "
        f"Claimed {total_claimed_mrg:.2f} MRG."
    )
    send_tg_alert(report_msg)


if __name__ == "__main__":
    asyncio.run(run_mrg_auto_solver())
