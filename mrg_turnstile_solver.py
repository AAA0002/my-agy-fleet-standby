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
import random
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

UPSTASH_URL = os.getenv("UPSTASH_URL") or "https://pleasant-locust-220893.upstash.io"
UPSTASH_TOKEN = os.getenv("UPSTASH_TOKEN") or "gQAAAAAAA17dAAIgcDFhZmU2OTdiZjRmYmY0OTI2OTgyZTYyYjkwYWQ5ODYzZg"
ALERT_BOT_TOKEN = os.getenv("ALERT_BOT_TOKEN") or "8858823950:AAEdX47g7as1xLYEudfRUHaVGUdNIaU_ku8"
OWNER_ID = os.getenv("OWNER_ID") or "6727787768"
CAPSOLVER_KEY = os.getenv("CAPSOLVER_KEY") or ""
TWOCAPTCHA_KEY = os.getenv("TWOCAPTCHA_KEY") or ""

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

ATF_SITEKEY = "0x4AAAAAAEbiOQ5xhVRMXGgt"
ATF_ORIGIN = "https://atfminers.asloni.online"
ATF_API = "https://atfminers.asloni.online/miner/index.php"

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


def get_webshare_proxy() -> dict | None:
    """
    Fetches an active high-speed proxy from Webshare to bypass Cloudflare WAF
    datacenter blocks in GitHub Actions and cloud runner environments.
    """
    webshare_keys = [
        os.getenv("WEBSHARE_KEY") or "1r347t4h8dwfkpoa4ifmmyajvmu3oxyn2guzs5k0",
        "e9lkjm26eqqah0s5zg26lk8tuiuxr9deznbp0aql"
    ]
    for key in webshare_keys:
        if not key:
            continue
        try:
            req = urllib.request.Request(
                "https://proxy.webshare.io/api/v2/proxy/list/?mode=direct&page=1&page_size=25",
                headers={"Authorization": f"Token {key}"}
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())
                results = [p for p in data.get("results", []) if p.get("valid", True)]
                if results:
                    p = random.choice(results)
                    return {
                        "server": f"http://{p['proxy_address']}:{p['port']}",
                        "username": p.get("username", "Arif2743"),
                        "password": p.get("password", "Arif2743")
                    }
        except Exception as e:
            logger.warning(f"Webshare proxy fetch warning: {e}")
    return None


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


def load_all_miniapp_tokens() -> dict:
    """Fetch miniapp_tokens master dictionary from Upstash Redis."""
    try:
        req = urllib.request.Request(
            f"{UPSTASH_URL}/get/miniapp_tokens",
            headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode())
            res = data.get("result")
            if res:
                parsed = json.loads(res) if isinstance(res, str) else res
                while isinstance(parsed, str):
                    parsed = json.loads(parsed)
                return parsed if isinstance(parsed, dict) else {}
    except Exception as e:
        logger.warning(f"Error fetching miniapp_tokens: {e}")
    return {}


def get_token_from_upstash(uid: int, miniapp_cache: dict = None) -> dict:
    """Fetch tokens from Upstash Redis REST, falling back to miniapp_tokens."""
    res_dict = {}
    try:
        req = urllib.request.Request(
            f"{UPSTASH_URL}/get/fleet:tokens:{uid}",
            headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
            res = data.get("result")
            if res:
                parsed = json.loads(res) if isinstance(res, str) else res
                while isinstance(parsed, str):
                    parsed = json.loads(parsed)
                if isinstance(parsed, dict):
                    res_dict = parsed
    except Exception:
        pass

    if isinstance(miniapp_cache, dict) and str(uid) in miniapp_cache:
        m_entry = miniapp_cache[str(uid)]
        if isinstance(m_entry, dict):
            for k, v in m_entry.items():
                if k not in res_dict or not res_dict[k]:
                    res_dict[k] = v
    return res_dict


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
            "tonWalletBalance": float(user.get("tonWalletBalance") or 0),
            "unclaimed": float(user.get("unclaimedMiningBalance") or 0),
            "humanVerifiedUntil": user.get("humanVerifiedUntil"),
            "manualUnlockedLevel": int(user.get("manualUnlockedLevel") or 1),
            "peakLevel": int(user.get("peakLevel") or 1),
            "isVerified": user.get("isVerified", False),
            "isTonConnected": user.get("isTonConnected", False),
            "tonWalletAddress": user.get("tonWalletAddress", ""),
            "referrerId": user.get("referrerId"),
            "isQualified": user.get("isQualified", False)
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
        bypass_csp=True,
        user_agent="Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
        viewport={"width": 412, "height": 915},
        is_mobile=True,
        has_touch=True,
        locale="en-US",
        timezone_id="UTC"
    )

    page = await context.new_page()

    # Always strictly URL-encode initData inside tgWebAppData hash to prevent & delimiter truncation
    target_url = f"{APP_ORIGIN}/#tgWebAppData={urllib.parse.quote(m_init, safe='')}"

    json_m_init = json.dumps(m_init)

    await page.add_init_script(f"""
        Object.defineProperty(navigator, 'webdriver', {{ get: () => undefined }});

        // 0. Pre-fill sessionStorage so telegram-web-app.js SDK initializes full initData
        try {{
            sessionStorage.setItem('__telegram__initParams', JSON.stringify({{
                tgWebAppData: {json_m_init},
                tgWebAppPlatform: 'android',
                tgWebAppVersion: '8.0'
            }}));
            sessionStorage.setItem('initParams', JSON.stringify({{
                tgWebAppData: {json_m_init},
                tgWebAppPlatform: 'android',
                tgWebAppVersion: '8.0'
            }}));
        }} catch(e) {{}}

        // 1. Hook Telegram WebApp object and permanently protect initData
        const mockWebApp = {{
            initData: {json_m_init},
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
        try {{
            Object.defineProperty(mockWebApp, 'initData', {{
                configurable: true,
                enumerable: true,
                get: () => {json_m_init},
                set: () => {{}}
            }});
        }} catch(e) {{}}

        let _tg = {{ WebApp: mockWebApp }};
        try {{
            Object.defineProperty(window, 'Telegram', {{
                configurable: true,
                enumerable: true,
                get: () => _tg,
                set: (v) => {{
                    _tg = v || {{}};
                    if (!_tg.WebApp) {{
                        _tg.WebApp = mockWebApp;
                    }} else {{
                        try {{
                            Object.defineProperty(_tg.WebApp, 'initData', {{
                                configurable: true,
                                enumerable: true,
                                get: () => {json_m_init},
                                set: () => {{}}
                            }});
                        }} catch(e) {{
                            _tg.WebApp.initData = {json_m_init};
                        }}
                    }}
                }}
            }});
        }} catch(e) {{}}

        window.__mrgTurnstileToken = null;

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
            if response.status == 401:
                logger.warning(f"⚠️ [MRG 401] UID {uid} resource: {response.url}")
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
    try:
        has_ts = await page.evaluate("() => typeof window.turnstile?.render === 'function'")
        if not has_ts:
            logger.info(f"Adding Turnstile script tag via Playwright for MRG UID {uid}...")
            await page.add_script_tag(url="https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit")
            try:
                await page.wait_for_function("() => typeof window.turnstile?.render === 'function'", timeout=12000)
            except Exception:
                pass
    except Exception as tse:
        logger.warning(f"MRG Turnstile script tag note: {tse}")

    solve_js = f"""
        async () => {{
            return new Promise((resolve) => {{
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
                }} else {{
                    container.innerHTML = '';
                }}

                function renderWidget() {{
                    try {{
                        window.turnstile.render(container, {{
                            sitekey: '{SITE_KEY}',
                            theme: 'dark',
                            appearance: 'always',
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
                }}

                if (window.turnstile && typeof window.turnstile.render === 'function') {{
                    renderWidget();
                }} else {{
                    let attempts = 0;
                    const iv = setInterval(() => {{
                        attempts++;
                        if (window.turnstile && typeof window.turnstile.render === 'function') {{
                            clearInterval(iv);
                            renderWidget();
                        }} else if (attempts > 200) {{
                            clearInterval(iv);
                            resolve({{ success: false, error: 'turnstile_load_timeout' }});
                        }}
                    }}, 100);
                }}

                setTimeout(() => {{
                    resolve({{ success: false, error: 'timeout_25s' }});
                }}, 25000);
            }});
        }}
    """
    try:
        solve_task = asyncio.create_task(page.evaluate(solve_js))
        for _ in range(16):
            ts_iframe = page.locator("#cf-manual-slot iframe, iframe[src*='challenges.cloudflare.com']").first
            if await ts_iframe.count() > 0:
                box = await ts_iframe.bounding_box()
                if box and box["width"] > 0 and box["height"] > 0:
                    click_x = box["x"] + min(32.0, box["width"] / 3)
                    click_y = box["y"] + box["height"] / 2
                    logger.info(f"🖱️ Clicking MRG programmatic Turnstile iframe at ({click_x:.1f}, {click_y:.1f})...")
                    await page.mouse.move(click_x, click_y, steps=8)
                    await asyncio.sleep(0.15)
                    await page.mouse.down()
                    await asyncio.sleep(0.1)
                    await page.mouse.up()
                    break
            await asyncio.sleep(0.6)

        render_res = await asyncio.wait_for(solve_task, timeout=28.0)
        if render_res and render_res.get("success") and render_res.get("token"):
            tok = render_res["token"]
            logger.info(f"✅ UID {uid}: Programmatic MRG token acquired: {tok[:16]}...")
            ver_res = verify_human_token(m_init, tok)
            if ver_res.get("success"):
                logger.info(f"🎉 UID {uid}: Programmatic verify-human succeeded!")
                save_mrg_pass_to_upstash(uid, tok)
                await context.close()
                return True
        else:
            logger.warning(f"UID {uid} MRG programmatic note: {render_res}")
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


def solve_turnstile_via_api(sitekey: str, page_url: str, action: str = "login", cdata: str = None) -> str | None:
    """
    Solves Cloudflare Turnstile using CapSolver or 2Captcha REST APIs if credentials are provided.
    Returns the Turnstile token string or None if unconfigured / failed.
    """
    if CAPSOLVER_KEY:
        try:
            logger.info(f"🧩 Solving Turnstile via CapSolver API for {page_url}...")
            task_dict = {
                "type": "AntiTurnstileTaskProxyLess",
                "websiteURL": page_url,
                "websiteKey": sitekey,
                "action": action
            }
            if cdata:
                task_dict["cdata"] = cdata
            create_payload = {
                "clientKey": CAPSOLVER_KEY,
                "task": task_dict
            }
            req = urllib.request.Request(
                "https://api.capsolver.com/createTask",
                data=json.dumps(create_payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
            task_id = data.get("taskId")
            if task_id:
                for _ in range(25):
                    time.sleep(2)
                    res_req = urllib.request.Request(
                        "https://api.capsolver.com/getTaskResult",
                        data=json.dumps({"clientKey": CAPSOLVER_KEY, "taskId": task_id}).encode("utf-8"),
                        headers={"Content-Type": "application/json"}
                    )
                    with urllib.request.urlopen(res_req, timeout=15) as resp:
                        res_data = json.loads(resp.read().decode())
                    if res_data.get("status") == "ready":
                        tok = res_data.get("solution", {}).get("token")
                        if tok:
                            logger.info(f"🎉 [CapSolver] Turnstile token acquired: {tok[:16]}...")
                            return tok
                    elif res_data.get("status") == "failed":
                        logger.warning(f"[CapSolver] Task failed: {res_data}")
                        break
        except Exception as e:
            logger.warning(f"[CapSolver] API error: {e}")

    if TWOCAPTCHA_KEY:
        try:
            logger.info(f"🧩 Solving Turnstile via 2Captcha API for {page_url}...")
            in_url = f"https://2captcha.com/in.php?key={TWOCAPTCHA_KEY}&method=turnstile&sitekey={sitekey}&pageurl={urllib.parse.quote(page_url)}&action={action}&json=1"
            req = urllib.request.Request(in_url)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
            if data.get("status") == 1:
                req_id = data.get("request")
                for _ in range(25):
                    time.sleep(3)
                    res_url = f"https://2captcha.com/res.php?key={TWOCAPTCHA_KEY}&action=get&id={req_id}&json=1"
                    with urllib.request.urlopen(res_url, timeout=15) as resp:
                        res_data = json.loads(resp.read().decode())
                    if res_data.get("status") == 1:
                        tok = res_data.get("request")
                        if tok:
                            logger.info(f"🎉 [2Captcha] Turnstile token acquired: {tok[:16]}...")
                            return tok
                    elif res_data.get("request") != "CAPCHA_NOT_READY":
                        logger.warning(f"[2Captcha] Error: {res_data}")
                        break
        except Exception as e:
            logger.warning(f"[2Captcha] API error: {e}")

    return None


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


def save_vyro_pass_to_upstash(uid: int, turnstile_token: str):
    """Saves valid VyroDrop Turnstile pass to Upstash Redis for edge nodes and Render."""
    try:
        req = urllib.request.Request(
            f"{UPSTASH_URL}/set/vyro:pass:{uid}",
            data=json.dumps({"turnstileToken": turnstile_token, "updated_at": time.time()}).encode(),
            headers={"Authorization": f"Bearer {UPSTASH_TOKEN}", "Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            pass
    except Exception as e:
        logger.warning(f"Error saving Vyro pass to Redis for UID {uid}: {e}")


async def solve_victors_turnstile(browser, uid: int, v_init: str, is_master: bool) -> bool:
    """
    Solves Turnstile for Victor's Company, logs in, binds referral, and saves humanPass.
    Supports instant API solving (CapSolver / 2Captcha) and headless Patchright Chromium stealth.
    Clicks Cloudflare Turnstile iframe with precise coordinates, and executes full recruitment pipeline.
    """
    # 0. Check API solver first (instant, proxy-less)
    acquired_token = solve_turnstile_via_api(VICTORS_SITEKEY, VICTORS_ORIGIN, action="login")
    acquired_pass = None

    if not acquired_token:
        context = await browser.new_context(
            bypass_csp=True,
            user_agent="Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
            viewport={"width": 412, "height": 915},
            is_mobile=True,
            has_touch=True,
            locale="en-US",
            timezone_id="UTC"
        )
        page = await context.new_page()

        encoded_init = urllib.parse.quote(v_init)
        target_url = (
            f"{VICTORS_ORIGIN}/#tgWebAppData={encoded_init}"
            f"&tgWebAppPlatform=android"
            f"&tgWebAppVersion=8.0"
            f"&tgWebAppThemeParams=%7B%22bg_color%22%3A%22%231a1147%22%2C%22text_color%22%3A%22%23ffffff%22%7D"
        )

        ref_to_bind = "" if is_master else VICTORS_REF
        json_v_init = json.dumps(v_init)
        json_ref_to_bind = json.dumps(ref_to_bind)
    
        await page.add_init_script(f"""
            Object.defineProperty(navigator, 'webdriver', {{ get: () => undefined }});
    
            // 0. Pre-fill sessionStorage so telegram-web-app.js parses valid initData
            try {{
                sessionStorage.setItem('__telegram__initParams', JSON.stringify({{
                    tgWebAppData: {json_v_init},
                    tgWebAppPlatform: 'android',
                    tgWebAppVersion: '8.0'
                }}));
                sessionStorage.setItem('initParams', JSON.stringify({{
                    tgWebAppData: {json_v_init},
                    tgWebAppPlatform: 'android',
                    tgWebAppVersion: '8.0'
                }}));
            }} catch(e) {{}}

            // 1. Hook Telegram WebApp object
            const mockWebApp = {{
                initData: {json_v_init},
                initDataUnsafe: {{
                    start_param: {json_ref_to_bind},
                    user: {{ id: {uid} }}
                }},
                version: '8.0',
                platform: 'android',
                colorScheme: 'dark',
                themeParams: {{
                    bg_color: '#1a1147',
                    text_color: '#ffffff',
                    hint_color: '#8b8b8b',
                    link_color: '#ffd700',
                    button_color: '#ffd700',
                    button_text_color: '#000000'
                }},
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
            try {{
                Object.defineProperty(window, 'Telegram', {{
                    configurable: true,
                    enumerable: true,
                    get: () => _tg,
                    set: (v) => {{
                        _tg = v || {{}};
                        if (!_tg.WebApp) {{
                            _tg.WebApp = mockWebApp;
                        }} else {{
                            _tg.WebApp.initData = {json_v_init};
                            _tg.WebApp.initDataUnsafe = {{
                                start_param: {json_ref_to_bind},
                                user: {{ id: {uid} }}
                            }};
                        }}
                    }}
                }});
            }} catch(e) {{}}
    
            // 2. State containers
            window.__victorsTurnstileToken = null;
            window.__victorsHumanPass = null;
    
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
    
        acquired_token_dict = {"token": None}
        acquired_pass_dict = {"pass": None}
    
        async def handle_victors_response(response):
            try:
                if "/auth/login" in response.url:
                    data = await response.json()
                    hp = data.get("humanPass") or (data.get("data", {}).get("humanPass") if isinstance(data.get("data"), dict) else None)
                    if hp:
                        logger.info(f"🎉 [Victor's] Captured humanPass from /auth/login: {str(hp)[:16]}...")
                        acquired_pass_dict["pass"] = str(hp)
            except Exception:
                pass
    
        async def handle_victors_request(request):
            try:
                if "/auth/login" in request.url:
                    post_data = request.post_data_json
                    if post_data and post_data.get("turnstileToken"):
                        acquired_token_dict["token"] = post_data["turnstileToken"]
            except Exception:
                pass
    
        page.on("response", handle_victors_response)
        page.on("request", handle_victors_request)
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
            acquired_token = tok or acquired_token_dict.get("token")
            if acquired_token and len(acquired_token) > 20:
                break
            hp = await page.evaluate("() => window.__victorsHumanPass || null")
            acquired_pass = hp or acquired_pass_dict.get("pass")
            if acquired_pass:
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
                        await page.mouse.move(click_x, click_y, steps=8)
                        await asyncio.sleep(0.15)
                        await page.mouse.down()
                        await asyncio.sleep(0.1)
                        await page.mouse.up()
                        # Also dispatch targeted synthetic click on iframe element
                        try:
                            await ts_iframe.click(position={"x": min(32.0, box["width"] / 3), "y": box["height"] / 2}, timeout=2500)
                        except Exception:
                            pass
                    
                    # Direct click inside frame locator
                    try:
                        ts_frame = page.frame_locator("iframe[src*='challenges.cloudflare.com']")
                        click_target = ts_frame.locator("#challenge-stage, .ctp-checkbox-label, .mark, body").first
                        if await click_target.count() > 0:
                            await click_target.click(timeout=3000)
                    except Exception:
                        pass
            except Exception as ce:
                logger.warning(f"[Victor's] UID {uid} iframe click note: {ce}")
    
            # Wait up to 15s after click for token or humanPass
            for _ in range(15):
                tok = await page.evaluate("() => window.__victorsTurnstileToken || (window.turnstile && typeof window.turnstile.getResponse === 'function' ? window.turnstile.getResponse() : null) || null")
                acquired_token = tok or acquired_token_dict.get("token")
                if acquired_token and len(acquired_token) > 20:
                    break
                hp = await page.evaluate("() => window.__victorsHumanPass || null")
                acquired_pass = hp or acquired_pass_dict.get("pass")
                if acquired_pass:
                    break
                await asyncio.sleep(1.0)
    
        # Step 3: Programmatic fallback render with exact Turnstile parameters
        if not acquired_token and not acquired_pass:
            logger.info(f"⚡ [Victor's] UID {uid}: Attempting programmatic Turnstile render with action='login'...")
            try:
                has_ts = await page.evaluate("() => typeof window.turnstile?.render === 'function'")
                if not has_ts:
                    logger.info(f"Adding Turnstile script tag via Playwright for Victor's UID {uid}...")
                    await page.add_script_tag(url="https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit")
                    try:
                        await page.wait_for_function("() => typeof window.turnstile?.render === 'function'", timeout=12000)
                    except Exception:
                        pass
            except Exception as tse:
                logger.warning(f"Victor's Turnstile script tag note: {tse}")

            solve_js = f"""
                async () => {{
                    return new Promise((resolve) => {{
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
                        }} else {{
                            container.innerHTML = '';
                        }}

                        function renderWidget() {{
                            try {{
                                window.turnstile.render(container, {{
                                    sitekey: '{VICTORS_SITEKEY}',
                                    action: 'login',
                                    theme: 'dark',
                                    appearance: 'always',
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
                        }}

                        if (window.turnstile && typeof window.turnstile.render === 'function') {{
                            renderWidget();
                        }} else {{
                            let attempts = 0;
                            const iv = setInterval(() => {{
                                attempts++;
                                if (window.turnstile && typeof window.turnstile.render === 'function') {{
                                    clearInterval(iv);
                                    renderWidget();
                                }} else if (attempts > 200) {{
                                    clearInterval(iv);
                                    resolve({{ success: false, error: 'turnstile_load_timeout' }});
                                }}
                            }}, 100);
                        }}

                        setTimeout(() => {{
                            resolve({{ success: false, error: 'timeout_25s' }});
                        }}, 25000);
                    }});
                }}
            """
            try:
                solve_task = asyncio.create_task(page.evaluate(solve_js))
                for _ in range(16):
                    ts_iframe = page.locator("#cf-vic-slot iframe, iframe[src*='challenges.cloudflare.com']").first
                    if await ts_iframe.count() > 0:
                        box = await ts_iframe.bounding_box()
                        if box and box["width"] > 0 and box["height"] > 0:
                            click_x = box["x"] + min(32.0, box["width"] / 3)
                            click_y = box["y"] + box["height"] / 2
                            logger.info(f"🖱️ [Victor's] Clicking programmatic Turnstile iframe at ({click_x:.1f}, {click_y:.1f})...")
                            await page.mouse.move(click_x, click_y, steps=8)
                            await asyncio.sleep(0.15)
                            await page.mouse.down()
                            await asyncio.sleep(0.1)
                            await page.mouse.up()
                            try:
                                await ts_iframe.click(position={"x": min(32.0, box["width"] / 3), "y": box["height"] / 2}, timeout=2000)
                            except Exception:
                                pass
                            try:
                                ts_f = page.frame_locator("#cf-vic-slot iframe, iframe[src*='challenges.cloudflare.com']")
                                tgt = ts_f.locator("#challenge-stage, .ctp-checkbox-label, .mark, body").first
                                if await tgt.count() > 0:
                                    await tgt.click(timeout=2500)
                            except Exception:
                                pass
                            break
                    await asyncio.sleep(0.6)
    
                render_res = await asyncio.wait_for(solve_task, timeout=28.0)
                if render_res and render_res.get("success") and render_res.get("token"):
                    acquired_token = render_res["token"]
            except Exception as re:
                logger.warning(f"[Victor's] UID {uid} programmatic render note: {re}")
    
        await context.close()
    
        acquired_pass = acquired_pass or acquired_pass_dict.get("pass")
        acquired_token = acquired_token or acquired_token_dict.get("token")
    
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

        # 2. Connect TON wallet to qualify recruit & unlock Level 1 Miner via TonConnect 2.0 proof
        fleet_ton_wallets = load_fleet_ton_wallets()
        w_entry = fleet_ton_wallets.get(str(uid)) or fleet_ton_wallets.get(uid)
        if w_entry and w_entry.get("mnemonic"):
            np_code, np_res = safe_get(f"{VICTORS_API}/wallet/proof-payload", extra_headers=v_authed_headers)
            if np_code == 200 and isinstance(np_res, dict) and np_res.get("payload"):
                nonce = np_res["payload"]
                proof_data = create_ton_proof(w_entry, nonce, domain="app.victors.company")
                words = w_entry["mnemonic"].split() if isinstance(w_entry["mnemonic"], str) else w_entry["mnemonic"]
                from tonsdk.contract.wallet import Wallets, WalletVersionEnum
                _, _, _, wallet_contract = Wallets.from_mnemonics(mnemonics=words, version=WalletVersionEnum.v4r2)
                friendly_addr = wallet_contract.address.to_string(is_user_friendly=True, is_bounceable=False, is_url_safe=True)
                conn_body = {
                    "address": friendly_addr,
                    "proof": proof_data["proof"],
                    "stateInit": proof_data["walletStateInit"],
                    "publicKey": proof_data["publicKey"]
                }
                c_code, c_res = safe_post(f"{VICTORS_API}/wallet/connect", conn_body, extra_headers=v_authed_headers)
                logger.info(f"💼 [Victor's] UID {uid}: Connected TON wallet {friendly_addr[:12]}... (code: {c_code}, walletOwned=True)")

        # Claim free social tasks
        for tid in ["follow-victors-company-on-x", "like-retweet-comment-on-x", "subscribe-vic-on-youtube"]:
            safe_post(f"{VICTORS_API}/tasks/claim", {"taskId": tid}, extra_headers=v_authed_headers)

        # 3. Claim daily passive mining
        m_code, m_res = safe_post(f"{VICTORS_API}/mining/claim", {}, extra_headers=v_authed_headers)
        logger.info(f"⛏️ [Victor's] UID {uid}: Mining claim: {m_code} {m_res}")

        # 4. Check profile and unlock levels if available
        p_code, p_res = safe_get(f"{VICTORS_API}/me", extra_headers=v_authed_headers)
        if p_code == 200 and isinstance(p_res, dict):
            u_info = p_res.get("user") or p_res
            cur_lvl = u_info.get("level", 1)
            manual_lvl = u_info.get("manualUnlockedLevel", 0)
            if manual_lvl < 1 or cur_lvl < 1:
                safe_post(f"{VICTORS_API}/levels/unlock", {"level": 1}, extra_headers=v_authed_headers)
                logger.info(f"⬆️ [Victor's] UID {uid}: Hired Level 1 Miner to start auto mining!")
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


def create_ton_proof(wallet_entry: dict, payload_nonce: str, domain: str = "vyro.run.place") -> dict:
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

    t_addr = wallet_contract.address
    wc = t_addr.wc
    addr_hash = t_addr.hash_part

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

    # 3. Request challenge first to determine if human verification is required
    ch_code, ch_body = safe_post(f"{VYRO_API}/wallet/challenge", {}, extra_headers=v_headers)
    nonce = None

    if ch_code in (200, 201) and isinstance(ch_body, dict) and ch_body.get("payload"):
        nonce = ch_body["payload"]
        logger.info(f"🔑 [VyroDrop] UID {uid}: Challenge nonce received directly: {nonce[:12]}...")
    elif ch_code == 403 and isinstance(ch_body, dict):
        ts_info = ch_body.get("error", {}).get("turnstile", {})
        ts_sitekey = ts_info.get("siteKey") or VYRO_SITEKEY
        ts_action = ts_info.get("action") or "wallet_onboarding"
        ts_cdata = ts_info.get("cdata") or ""
        logger.info(f"🛡️ [VyroDrop] UID {uid}: Turnstile challenge requested (siteKey={ts_sitekey}, action={ts_action}, cdata={ts_cdata[:12]}...). Solving...")

        # 0. Check API solver first (instant, proxy-less)
        api_token = solve_turnstile_via_api(ts_sitekey, VYRO_ORIGIN, action=ts_action, cdata=ts_cdata)
        if api_token:
            logger.info(f"✅ [VyroDrop] UID {uid}: Turnstile solved via API: {api_token[:16]}...")
            save_vyro_pass_to_upstash(uid, api_token)
            ch_code2, ch_body2 = safe_post(f"{VYRO_API}/wallet/challenge", {"turnstileToken": api_token}, extra_headers=v_headers)
            if ch_code2 in (200, 201) and isinstance(ch_body2, dict) and ch_body2.get("payload"):
                nonce = ch_body2["payload"]
                logger.info(f"🔑 [VyroDrop] UID {uid}: Nonce received via API solved challenge: {nonce[:12]}...")

        if not nonce:
            context = await browser.new_context(
                bypass_csp=True,
                user_agent="Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
                viewport={"width": 412, "height": 915},
                is_mobile=True,
                has_touch=True,
                locale="en-US",
                timezone_id="UTC"
            )
            page = await context.new_page()
            
            json_vyro_init = json.dumps(vyro_init)
            target_url = f"{VYRO_ORIGIN}/profile/wallet#tgWebAppData={urllib.parse.quote(vyro_init, safe='')}"

            await page.add_init_script(f"""
                Object.defineProperty(navigator, 'webdriver', {{ get: () => undefined }});

                // 0. Pre-fill sessionStorage for telegram-web-app.js SDK
                try {{
                    sessionStorage.setItem('__telegram__initParams', JSON.stringify({{
                        tgWebAppData: {json_vyro_init},
                        tgWebAppPlatform: 'android',
                        tgWebAppVersion: '8.0'
                    }}));
                    sessionStorage.setItem('initParams', JSON.stringify({{
                        tgWebAppData: {json_vyro_init},
                        tgWebAppPlatform: 'android',
                        tgWebAppVersion: '8.0'
                    }}));
                }} catch(e) {{}}

                const mockWebApp = {{
                    initData: {json_vyro_init},
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
                try {{
                    Object.defineProperty(mockWebApp, 'initData', {{
                        configurable: true,
                        enumerable: true,
                        get: () => {json_vyro_init},
                        set: () => {{}}
                    }});
                }} catch(e) {{}}

                let _tg = {{ WebApp: mockWebApp }};
                try {{
                    Object.defineProperty(window, 'Telegram', {{
                        configurable: true,
                        enumerable: true,
                        get: () => _tg,
                        set: (v) => {{
                            _tg = v || {{}};
                            if (!_tg.WebApp) {{
                                _tg.WebApp = mockWebApp;
                            }} else {{
                                try {{
                                    Object.defineProperty(_tg.WebApp, 'initData', {{
                                        configurable: true,
                                        enumerable: true,
                                        get: () => {json_vyro_init},
                                        set: () => {{}}
                                    }});
                                }} catch(e) {{
                                    _tg.WebApp.initData = {json_vyro_init};
                                }}
                            }}
                        }}
                    }});
                }} catch(e) {{}}
                window.__vyroTurnstileToken = null;
            """)

            try:
                await page.goto(target_url, wait_until="domcontentloaded", timeout=18000)
            except Exception as e:
                logger.warning(f"[VyroDrop] UID {uid} navigation note: {e}")

            await asyncio.sleep(2.0)

            # Ensure Turnstile script tag is loaded
            try:
                has_ts = await page.evaluate("() => typeof window.turnstile?.render === 'function'")
                if not has_ts:
                    logger.info(f"Adding Turnstile script tag via Playwright for VyroDrop UID {uid}...")
                    await page.add_script_tag(url="https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit")
                    try:
                        await page.wait_for_function("() => typeof window.turnstile?.render === 'function'", timeout=12000)
                    except Exception:
                        pass
            except Exception as tse:
                logger.warning(f"VyroDrop Turnstile script tag note: {tse}")

            solve_js = f"""
                async () => {{
                    return new Promise((resolve) => {{
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
                        }} else {{
                            container.innerHTML = '';
                        }}

                        function renderWidget() {{
                            try {{
                                window.turnstile.render(container, {{
                                    sitekey: '{ts_sitekey}',
                                    action: '{ts_action}',
                                    cdata: '{ts_cdata}',
                                    theme: 'dark',
                                    appearance: 'always',
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
                        }}

                        if (window.turnstile && typeof window.turnstile.render === 'function') {{
                            renderWidget();
                        }} else {{
                            let attempts = 0;
                            const iv = setInterval(() => {{
                                attempts++;
                                if (window.turnstile && typeof window.turnstile.render === 'function') {{
                                    clearInterval(iv);
                                    renderWidget();
                                }} else if (attempts > 200) {{
                                    clearInterval(iv);
                                    resolve({{ success: false, error: 'turnstile_load_timeout' }});
                                }}
                            }}, 100);
                        }}

                        setTimeout(() => {{
                            resolve({{ success: false, error: 'timeout_25s' }});
                        }}, 25000);
                    }});
                }}
            """

            try:
                solve_task = asyncio.create_task(page.evaluate(solve_js))
                for _ in range(16):
                    try:
                        ts_iframe = page.locator("#cf-vyro-slot iframe, iframe[src*='challenges.cloudflare.com']").first
                        if await ts_iframe.count() > 0:
                            box = await ts_iframe.bounding_box()
                            if box and box["width"] > 0 and box["height"] > 0:
                                click_x = box["x"] + min(32.0, box["width"] / 3)
                                click_y = box["y"] + box["height"] / 2
                                logger.info(f"🖱️ [VyroDrop] Click Turnstile iframe for UID {uid} at ({click_x:.1f}, {click_y:.1f})...")
                                await page.mouse.move(click_x, click_y, steps=8)
                                await asyncio.sleep(0.15)
                                await page.mouse.down()
                                await asyncio.sleep(0.1)
                                await page.mouse.up()
                                try:
                                    await ts_iframe.click(position={"x": min(32.0, box["width"] / 3), "y": box["height"] / 2}, timeout=2000)
                                except Exception:
                                    pass
                                try:
                                    ts_f = page.frame_locator("#cf-vyro-slot iframe, iframe[src*='challenges.cloudflare.com']")
                                    tgt = ts_f.locator("#challenge-stage, .ctp-checkbox-label, .mark, body").first
                                    if await tgt.count() > 0:
                                        await tgt.click(timeout=2500)
                                except Exception:
                                    pass
                                break
                    except Exception:
                        pass
                    await asyncio.sleep(0.6)

                render_res = await asyncio.wait_for(solve_task, timeout=28.0)
                if render_res and render_res.get("success") and render_res.get("token"):
                    tok = render_res["token"]
                    logger.info(f"✅ [VyroDrop] UID {uid}: Turnstile solved: {tok[:16]}...")
                    save_vyro_pass_to_upstash(uid, tok)
                    ch_code2, ch_body2 = safe_post(f"{VYRO_API}/wallet/challenge", {"turnstileToken": tok}, extra_headers=v_headers)
                    if ch_code2 in (200, 201) and isinstance(ch_body2, dict) and ch_body2.get("payload"):
                        nonce = ch_body2["payload"]
                        logger.info(f"🔑 [VyroDrop] UID {uid}: Nonce received via solved challenge: {nonce[:12]}...")
                    else:
                        logger.error(f"❌ [VyroDrop] UID {uid}: Challenge submit failed: {ch_code2} {ch_body2}")
                else:
                    logger.warning(f"[VyroDrop] UID {uid} solve note: {render_res}")
            except Exception as se:
                logger.warning(f"[VyroDrop] UID {uid} solve note: {se}")
            finally:
                if 'context' in locals():
                    await context.close()
    else:
        logger.error(f"❌ [VyroDrop] UID {uid}: Unexpected challenge response: {ch_code} {ch_body}")
        return False

    if not nonce:
        logger.error(f"❌ [VyroDrop] UID {uid}: Could not acquire challenge nonce.")
        return False

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


async def solve_atf_turnstile(browser, uid: int, atf_init: str) -> bool:
    """
    Solves Cloudflare Turnstile entry captcha for ATF Miner (5-day cycle or new accounts).
    Submits verified captcha_token to index.php?action=verify_entry_captcha, and saves pass to Upstash.
    """
    acquired_token = solve_turnstile_via_api(ATF_SITEKEY, ATF_ORIGIN, action="verify_entry_captcha")
    if not acquired_token and browser:
        try:
            context = await browser.new_context(
                bypass_csp=True,
                user_agent="Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
                viewport={"width": 412, "height": 915},
                is_mobile=True,
                has_touch=True
            )
            page = await context.new_page()
            target_url = f"{ATF_ORIGIN}/miner/index.html?entry=bot_start#tgWebAppData={urllib.parse.quote(atf_init, safe='')}"
            json_atf_init = json.dumps(atf_init)
            await page.add_init_script(f"""
                Object.defineProperty(navigator, 'webdriver', {{ get: () => undefined }});
                try {{
                    sessionStorage.setItem('__telegram__initParams', JSON.stringify({{ tgWebAppData: {json_atf_init} }}));
                    sessionStorage.setItem('initParams', JSON.stringify({{ tgWebAppData: {json_atf_init} }}));
                }} catch(e) {{}}
                const mockWebApp = {{
                    initData: {json_atf_init},
                    initDataUnsafe: {{ user: {{ id: {uid} }} }},
                    version: '8.0', platform: 'android',
                    ready: () => {{}}, expand: () => {{}}, close: () => {{}},
                    onEvent: () => {{}}, offEvent: () => {{}}, sendData: () => {{}}
                }};
                window.Telegram = {{ WebApp: mockWebApp }};
                window.__atfSolvedToken = null;

                let _atfCb = null;
                Object.defineProperty(window, '__atfEntryCaptchaCallback', {{
                    configurable: true,
                    enumerable: true,
                    get: () => _atfCb,
                    set: (fn) => {{
                        _atfCb = async (tok) => {{
                            window.__atfSolvedToken = tok;
                            if (typeof fn === 'function') {{
                                try {{ return await fn(tok); }} catch(e) {{}}
                            }}
                        }};
                    }}
                }});

                const origFetch = window.fetch;
                window.fetch = async function(...args) {{
                    const url = String(args[0] || '');
                    if (url.includes('verify_entry_captcha')) {{
                        try {{
                            const b = JSON.parse(args[1]?.body || '{{}}');
                            if (b.captcha_token) window.__atfSolvedToken = b.captcha_token;
                        }} catch(e) {{}}
                    }}
                    return await origFetch.apply(this, args);
                }};
            """)

            try:
                await page.goto(target_url, wait_until="domcontentloaded", timeout=18000)
            except Exception:
                pass

            await asyncio.sleep(2.0)

            # Trigger gate if frontend did not auto-open
            await page.evaluate(f"""
                () => {{
                    try {{
                        if (typeof showEntryCaptchaGate === 'function') showEntryCaptchaGate(true);
                        if (typeof ensureEntryCaptchaBeforeLogin === 'function') ensureEntryCaptchaBeforeLogin({{ id: {uid} }}, true);
                    }} catch(e) {{}}
                }}
            """)

            # Fast check: wait for token or click iframe
            for _ in range(15):
                tok = await page.evaluate("() => window.__atfSolvedToken || null")
                if tok and len(tok) > 20:
                    acquired_token = tok
                    break
                try:
                    ts_iframe = page.locator("#entryCaptchaBox iframe, iframe[src*='challenges.cloudflare.com']").first
                    if await ts_iframe.count() > 0:
                        box = await ts_iframe.bounding_box()
                        if box and box["width"] > 0 and box["height"] > 0:
                            click_x = box["x"] + min(32.0, box["width"] / 3)
                            click_y = box["y"] + box["height"] / 2
                            await page.mouse.move(click_x, click_y, steps=6)
                            await asyncio.sleep(0.12)
                            await page.mouse.down()
                            await asyncio.sleep(0.08)
                            await page.mouse.up()
                        else:
                            ts_frame = page.frame_locator("#entryCaptchaBox iframe, iframe[src*='challenges.cloudflare.com']")
                            click_target = ts_frame.locator("#challenge-stage, .ctp-checkbox-label, .mark").first
                            if await click_target.count() > 0:
                                await click_target.click(timeout=2500)
                except Exception:
                    pass
                await asyncio.sleep(1.2)

            # Programmatic fallback render
            if not acquired_token:
                logger.info(f"⚡ [ATF] UID {uid}: Attempting programmatic Turnstile render into #entryCaptchaBox...")
                try:
                    has_ts = await page.evaluate("() => typeof window.turnstile?.render === 'function'")
                    if not has_ts:
                        logger.info(f"Adding Turnstile script tag via Playwright for ATF UID {uid}...")
                        await page.add_script_tag(url="https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit")
                        try:
                            await page.wait_for_function("() => typeof window.turnstile?.render === 'function'", timeout=12000)
                        except Exception:
                            pass
                except Exception as tse:
                    logger.warning(f"ATF Turnstile script tag note: {tse}")

                solve_js = f"""
                    async () => {{
                        return new Promise((resolve) => {{
                            let box = document.getElementById('entryCaptchaBox') || document.body;

                            function renderWidget() {{
                                try {{
                                    window.turnstile.render(box, {{
                                        sitekey: '{ATF_SITEKEY}',
                                        size: 'normal',
                                        theme: 'dark',
                                        appearance: 'always',
                                        callback: function(tok) {{
                                            window.__atfSolvedToken = tok;
                                            resolve({{ success: true, token: tok }});
                                        }},
                                        'error-callback': function(err) {{
                                            resolve({{ success: false, error: String(err) }});
                                        }}
                                    }});
                                }} catch(e) {{
                                    resolve({{ success: false, error: String(e) }});
                                }}
                            }}

                            if (window.turnstile && typeof window.turnstile.render === 'function') {{
                                renderWidget();
                            }} else {{
                                let attempts = 0;
                                const iv = setInterval(() => {{
                                    attempts++;
                                    if (window.turnstile && typeof window.turnstile.render === 'function') {{
                                        clearInterval(iv);
                                        renderWidget();
                                    }} else if (attempts > 200) {{
                                        clearInterval(iv);
                                        resolve({{ success: false, error: 'turnstile_load_timeout' }});
                                    }}
                                }}, 100);
                            }}

                            setTimeout(() => {{
                                resolve({{ success: false, error: 'timeout_20s' }});
                            }}, 20000);
                        }});
                    }}
                """
                try:
                    solve_task = asyncio.create_task(page.evaluate(solve_js))
                    for _ in range(6):
                        try:
                            ts_iframe = page.locator("#entryCaptchaBox iframe, iframe[src*='challenges.cloudflare.com']").first
                            if await ts_iframe.count() > 0:
                                box = await ts_iframe.bounding_box()
                                if box and box["width"] > 0 and box["height"] > 0:
                                    click_x = box["x"] + min(32.0, box["width"] / 3)
                                    click_y = box["y"] + box["height"] / 2
                                    await page.mouse.move(click_x, click_y, steps=6)
                                    await asyncio.sleep(0.12)
                                    await page.mouse.down()
                                    await asyncio.sleep(0.08)
                                    await page.mouse.up()
                                    break
                        except Exception:
                            pass
                        await asyncio.sleep(0.8)
                    render_res = await asyncio.wait_for(solve_task, timeout=12.0)
                    if render_res and render_res.get("success") and render_res.get("token"):
                        acquired_token = render_res["token"]
                except Exception as pe:
                    logger.warning(f"[ATF] UID {uid} programmatic render note: {pe}")

            await context.close()
        except Exception as e:
            logger.warning(f"[ATF Turnstile] Browser solve error for UID {uid}: {e}")

    if acquired_token:
        logger.info(f"🎉 [ATF] Turnstile token acquired for UID {uid}: {acquired_token[:16]}...")
        p = {
            "initData": atf_init,
            "tg_id": uid,
            "username": "",
            "captcha_token": acquired_token
        }
        atf_h = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/json",
            "Referer": f"{ATF_ORIGIN}/miner/index.html",
            "Origin": ATF_ORIGIN
        }
        v_code, v_data = safe_post(f"{ATF_API}?action=verify_entry_captcha&t={int(time.time()*1000)}", p, extra_headers=atf_h)
        if (v_code in (200, 201)) or (isinstance(v_data, dict) and v_data.get("status") == "success"):
            logger.info(f"✅ [ATF] Verified entry captcha for UID {uid} on ATF server!")
            try:
                req_up = urllib.request.Request(
                    f"{UPSTASH_URL}/set/atf:pass:{uid}",
                    data=json.dumps({"captcha_token": acquired_token, "updated_at": time.time()}).encode(),
                    headers={"Authorization": f"Bearer {UPSTASH_TOKEN}", "Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req_up, timeout=8):
                    pass
            except Exception:
                pass
            return True
    return False


async def run_mrg_auto_solver():
    """Main workflow: audits all 18 accounts, solves needed challenges, connects wallets, and auto-claims."""
    logger.info("====================================================================")
    logger.info("🚀 Starting 100% Cloud Fleet Auto-Farming & Turnstile Solver Cycle")
    logger.info("====================================================================")

    fleet_ton_wallets = load_fleet_ton_wallets()
    miniapp_cache = load_all_miniapp_tokens()
    accounts_data = []
    accounts_needing_solver = []
    victors_accounts = []
    vyro_accounts = []
    atf_accounts = []
    kynex_accounts = []

    # 1. Fetch tokens and inspect account states
    for idx, uid in enumerate(FLEET_UIDS, 1):
        tok_dict = get_token_from_upstash(uid, miniapp_cache=miniapp_cache)
        mrg_init = tok_dict.get("mrg_init_data")
        atf_init = tok_dict.get("atf_init_data")
        vic_init = tok_dict.get("victors_init_data")
        vyro_init = tok_dict.get("vyro_init_data")
        kynex_init = tok_dict.get("kynex_init_data")

        if atf_init:
            atf_accounts.append({
                "uid": uid,
                "init_data": atf_init
            })

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

        if kynex_init:
            kynex_accounts.append({
                "uid": uid,
                "init_data": kynex_init
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
        f"{len(vyro_accounts)} accounts found with VyroDrop. "
        f"{len(atf_accounts)} accounts found with ATF Miner. "
        f"{len(kynex_accounts)} accounts found with Kynex Network."
    )

    # 2. Launch stealth browser and process accounts needing verification
    solved_count = 0
    total_claimed_mrg = 0.0
    victors_solved = 0
    vyro_wallets_connected = 0
    atf_solved = 0

    if needed_count > 0 or len(victors_accounts) > 0 or len(vyro_accounts) > 0 or len(atf_accounts) > 0:
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
        atf_accounts.sort(key=lambda a: 0 if a["uid"] == 6727787768 else 1)

        is_xvfb = bool(os.getenv("DISPLAY") or os.getenv("CI"))
        headless_flag = False if is_xvfb else True
        logger.info(f"🖥️ Launching Chromium (headless={headless_flag}, DISPLAY={os.getenv('DISPLAY')}, CI={os.getenv('CI')})...")

        ws_proxy = get_webshare_proxy()
        launch_kwargs = {
            "headless": headless_flag,
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--window-size=1280,800"
            ]
        }
        if ws_proxy:
            logger.info(f"🌐 Routing browser through Webshare proxy: {ws_proxy['server']}")
            launch_kwargs["proxy"] = ws_proxy

        async with async_playwright() as p:
            browser = await p.chromium.launch(**launch_kwargs)

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

                    # Auto-upgrade level if balance allows (including dedicated TON wallet balance)
                    new_bal = acc["stat"]["inAppBalance"] + claimed_amt + acc["stat"].get("tonWalletBalance", 0.0)
                    auto_unlock_mrg_level(m_init, acc["stat"]["manualUnlockedLevel"], new_bal)

                await asyncio.sleep(1.0)

            # B. Solve Victor's Company passes & qualify recruits
            for v_acc in victors_accounts:
                v_uid = v_acc["uid"]
                v_init = v_acc["init_data"]

                # Fast pre-check: If account already has a working humanPass in Upstash Redis, test it and skip heavy browser launch!
                cached_pass = None
                try:
                    c_resp = safe_get(f"{UPSTASH_URL}/get/victors:pass:{v_uid}", extra_headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"})
                    if c_resp and isinstance(c_resp[1], dict) and c_resp[1].get("result"):
                        raw_r = c_resp[1]["result"]
                        parsed_r = json.loads(raw_r) if isinstance(raw_r, str) else raw_r
                        cached_pass = parsed_r.get("humanPass")
                except Exception:
                    pass

                if cached_pass:
                    test_h = {
                        "Authorization": f"tma {v_init}",
                        "Origin": VICTORS_ORIGIN,
                        "Referer": f"{VICTORS_ORIGIN}/",
                        "x-human-pass": str(cached_pass)
                    }
                    t_code, t_d = safe_get(f"{VICTORS_API}/me", extra_headers=test_h)
                    if t_code == 200 and isinstance(t_d, dict) and (t_d.get("success") is True or "state" in t_d or "user" in t_d):
                        logger.info(f"✅ [Victor's] UID {v_uid}: Human pass already active and valid in Upstash Redis! Skipping browser solve.")
                        safe_post(f"{VICTORS_API}/mining/claim", {}, extra_headers=test_h)
                        safe_post(f"{VICTORS_API}/checkin", {}, extra_headers=test_h)
                        safe_post(f"{VICTORS_API}/me/tutorial", {}, extra_headers=test_h)
                        u_res = t_d.get("user") or t_d
                        if isinstance(u_res, dict) and u_res.get("manualUnlockedLevel", 0) < 1:
                            safe_post(f"{VICTORS_API}/levels/unlock", {"level": 1}, extra_headers=test_h)
                        safe_post(f"{VICTORS_API}/referral/claim-bonus", {}, extra_headers=test_h)
                        safe_post(f"{VICTORS_API}/referral/claim-commission", {}, extra_headers=test_h)
                        # Fetch and claim pending tasks
                        _, tk_data = safe_get(f"{VICTORS_API}/tasks", extra_headers=test_h)
                        if isinstance(tk_data, dict):
                            raw_tasks = tk_data.get("tasks") or (tk_data.get("data", {}).get("tasks") if isinstance(tk_data.get("data"), dict) else [])
                            if isinstance(raw_tasks, list):
                                for task_item in raw_tasks:
                                    if isinstance(task_item, dict) and task_item.get("status") in ("READY_TO_CLAIM", "PENDING", "COMPLETED") and not task_item.get("claimed"):
                                        tid = task_item.get("id") or task_item.get("taskId")
                                        if tid:
                                            safe_post(f"{VICTORS_API}/tasks/claim", {"taskId": tid}, extra_headers=test_h)
                        victors_solved += 1
                        continue
                    else:
                        logger.info(f"⚠️ [Victor's] UID {v_uid}: Cached pass expired (HTTP {t_code}). Launching browser solver...")

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

            # D. Solve ATF Miner entry captcha passes (5-day security check & new accounts)
            for atf_acc in atf_accounts:
                a_uid = atf_acc["uid"]
                a_init = atf_acc["init_data"]
                # Fast pre-check: Check if login requires captcha
                p_chk = {
                    "initData": a_init,
                    "tg_id": a_uid,
                    "username": "",
                    "request_id": f"rq-chk-{a_uid}",
                    "device_id": f"dev-chk-{a_uid}"
                }
                atf_h = {
                    "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36",
                    "X-Requested-With": "XMLHttpRequest",
                    "Content-Type": "application/json",
                    "Referer": f"{ATF_ORIGIN}/miner/index.html",
                    "Origin": ATF_ORIGIN
                }
                chk_code, chk_d = safe_post(f"{ATF_API}?action=login&t={int(time.time()*1000)}", p_chk, extra_headers=atf_h)
                needs_atf_captcha = (chk_code == 403) or (isinstance(chk_d, dict) and chk_d.get("reason") in ("entry_captcha_required", "captcha_required"))
                if needs_atf_captcha:
                    logger.info(f"⚠️ [ATF] UID {a_uid} requires entry captcha. Solving Turnstile (0x4AAAAAAEbiOQ5xhVRMXGgt)...")
                    try:
                        atf_res = await asyncio.wait_for(
                            solve_atf_turnstile(browser, a_uid, a_init),
                            timeout=55.0
                        )
                        if atf_res:
                            atf_solved += 1
                            # Immediately login & start mining post-solve
                            safe_post(f"{ATF_API}?action=login&t={int(time.time()*1000)}", p_chk, extra_headers=atf_h)
                            safe_post(f"{ATF_API}?action=claim&t={int(time.time()*1000)}", p_chk, extra_headers=atf_h)
                    except asyncio.TimeoutError:
                        logger.warning(f"ATF solve timed out (55s) for UID {a_uid}")
                    except Exception as ae:
                        logger.warning(f"ATF solve exception for UID {a_uid}: {ae}")
                    await asyncio.sleep(1.0)
                else:
                    logger.info(f"✅ [ATF] UID {a_uid}: Login valid without captcha. Skipping.")

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
                    # Auto-upgrade level if balance allows (including dedicated TON wallet balance)
                    new_bal = acc["stat"]["inAppBalance"] + claimed_amt + acc["stat"].get("tonWalletBalance", 0.0)
                    auto_unlock_mrg_level(m_init, acc["stat"]["manualUnlockedLevel"], new_bal)

    # 4. Master Account Referral Sweep
    master_acc = next((a for a in accounts_data if a["uid"] == 6727787768), None)
    if master_acc:
        m_init = master_acc["init_data"]
        safe_post(f"{API_BASE}/api/user/claim-commission", {"initData": m_init})
        safe_post(f"{API_BASE}/api/user/claim-one-time-bonus", {"initData": m_init})
        logger.info("👑 Master Account referral commission and team bonus claimed.")

    # 5. Kynex Network Multi-Account Cloud Auto-Farming
    kynex_farmed = 0
    total_claimed_knx = 0.0
    if kynex_accounts:
        logger.info(f"⚡ Starting Kynex Network Auto-Farming for {len(kynex_accounts)} accounts...")
        try:
            import aiohttp
            from kynex_miner import farm_kynex_account

            async with aiohttp.ClientSession() as kyn_session:
                for k_acc in kynex_accounts:
                    kuid = k_acc["uid"]
                    kinit = k_acc["init_data"]
                    try:
                        k_res = await farm_kynex_account(
                            kyn_session,
                            kinit,
                            {"user_id": kuid, "account_id": kuid},
                            is_master=(kuid == 6727787768)
                        )
                        kynex_farmed += 1
                        c_knx = k_res.get("claimed_knx") or 0.0
                        total_claimed_knx += float(c_knx)
                        logger.info(f"✅ [Kynex] UID {kuid}: {k_res.get('status')}")
                    except Exception as ke:
                        logger.warning(f"⚠️ [Kynex] UID {kuid} farm error: {ke}")
        except Exception as kerr:
            logger.warning(f"⚠️ Kynex fleet farm exception: {kerr}")

    # 6. Telegram Telemetry Notification
    report_msg = (
        f"🚀 <b>5-Bot Fleet Cloud Turnstile & Multi-Farming Engine Report</b>\n\n"
        f"• <b>Total Fleet Accounts:</b> 18\n"
        f"• <b>MRG Pass Solved:</b> {solved_count}/{needed_count}\n"
        f"• <b>ATF Captcha Solved:</b> {atf_solved}/{len(atf_accounts)}\n"
        f"• <b>Victor's Pass Solved:</b> {victors_solved}/{len(victors_accounts)}\n"
        f"• <b>VyroDrop Wallets & Mining:</b> {vyro_wallets_connected}/{len(vyro_accounts)}\n"
        f"• <b>Kynex Network Farmed:</b> {kynex_farmed}/{len(kynex_accounts)} (+{total_claimed_knx:.2f} KNX)\n"
        f"• <b>Total MRG Harvested:</b> {total_claimed_mrg:.2f} MRG\n"
        f"• <b>Execution Time:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
        f"⚡ <i>100% Cloud Execution. Zero phone load.</i>"
    )
    logger.info(
        f"📢 Telemetry: MRG Solved {solved_count}/{needed_count}, "
        f"ATF Solved {atf_solved}/{len(atf_accounts)}, "
        f"Victor's Solved {victors_solved}/{len(victors_accounts)}, "
        f"Vyro Connected {vyro_wallets_connected}/{len(vyro_accounts)}, "
        f"Kynex Farmed {kynex_farmed}/{len(kynex_accounts)}, "
        f"Claimed {total_claimed_mrg:.2f} MRG, {total_claimed_knx:.2f} KNX."
    )
    send_tg_alert(report_msg)


if __name__ == "__main__":
    asyncio.run(run_mrg_auto_solver())
