#!/usr/bin/env python3
import asyncio
import json
import logging
import os
import sys
import time
import urllib.parse
import urllib.request
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import dotenv_values
from patchright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("victors_master_claim")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

config = dotenv_values(os.path.join(PROJECT_ROOT, ".env"))
api_id = int(config.get("TELEGRAM_API_ID", 28005322))
api_hash = config.get("TELEGRAM_API_HASH", "5cd9b2512f7f2b1d7d0a51c4db223b47")
UPSTASH_URL = config.get("UPSTASH_URL") or "https://rich-emu-106119.upstash.io"
UPSTASH_TOKEN = config.get("UPSTASH_TOKEN") or ""

VICTORS_SITEKEY = "0x4AAAAAAFD0KRgPRFVwDvgn"
VICTORS_ORIGIN = "https://app.victors.company"
VICTORS_API = "https://server.victors.company/api"

accs_file = os.path.join(PROJECT_ROOT, "accounts.json")
with open(accs_file) as f:
    accs = json.load(f)

masters = [a for a in accs if str(a.get("user_id")) == "6727787768"]
if not masters:
    logger.error("Master account 6727787768 not found in accounts.json")
    sys.exit(1)
master = masters[0]
uid = 6727787768

def safe_api(method, endpoint, payload=None, headers=None):
    url = f"{VICTORS_API}{endpoint}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8")
            try:
                return resp.status, json.loads(body)
            except Exception:
                return resp.status, body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, body
    except Exception as e:
        return 0, str(e)

async def main():
    logger.info("=== 1. Extracting fresh Telegram WebApp Token for Master (6727787768) ===")
    client = TelegramClient(StringSession(master["session_string"]), api_id, api_hash)
    await client.connect()
    from refresh_cloud_tokens import extract_bot_webapp_token, VICTORS_BOT
    v_init = await extract_bot_webapp_token(client, VICTORS_BOT, default_url="https://app.victors.company/", candidate_short_names=["app", "play"])
    await client.disconnect()

    if not v_init:
        logger.error("Failed to extract init_data from Telegram!")
        return

    logger.info(f"Fresh init_data acquired (length: {len(v_init)})")

    # Update miniapp_tokens in Upstash with this fresh token
    try:
        req_up = urllib.request.Request(f"{UPSTASH_URL}/get/miniapp_tokens", headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"})
        with urllib.request.urlopen(req_up, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            raw_res = data.get("result")
            if raw_res:
                res = json.loads(raw_res) if isinstance(raw_res, str) else raw_res
                if isinstance(res, str): res = json.loads(res)
            else:
                res = {}
            if str(uid) in res:
                res[str(uid)]["victors_init_data"] = v_init
                res[str(uid)]["synced_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                put_req = urllib.request.Request(
                    f"{UPSTASH_URL}/set/miniapp_tokens",
                    data=json.dumps(res).encode(),
                    headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"},
                    method="POST"
                )
                with urllib.request.urlopen(put_req, timeout=10) as pr:
                    logger.info("Updated miniapp_tokens in Upstash Redis!")
    except Exception as ue:
        logger.warning(f"Note updating Upstash miniapp_tokens: {ue}")

    logger.info("=== 2. Solving Cloudflare Turnstile in Headless Chromium ===")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage"
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
            viewport={"width": 412, "height": 915},
            is_mobile=True,
            has_touch=True
        )
        page = await context.new_page()

        acquired_token_dict = {"token": None}
        acquired_pass_dict = {"pass": None}

        async def handle_response(response):
            if "/auth/login" in response.url:
                try:
                    data = await response.json()
                    hp = data.get("humanPass") or (data.get("data", {}).get("humanPass") if isinstance(data.get("data"), dict) else None)
                    if hp:
                        logger.info(f"🎉 Captured humanPass from /auth/login: {str(hp)[:20]}...")
                        acquired_pass_dict["pass"] = str(hp)
                except Exception:
                    pass

        async def handle_request(request):
            if "/auth/login" in request.url:
                try:
                    p_data = request.post_data_json
                    if p_data and p_data.get("turnstileToken"):
                        acquired_token_dict["token"] = p_data["turnstileToken"]
                        logger.info(f"Captured turnstileToken from request: {p_data['turnstileToken'][:20]}...")
                except Exception:
                    pass

        page.on("response", handle_response)
        page.on("request", handle_request)

        encoded_init = urllib.parse.quote(v_init, safe="")
        target_url = f"{VICTORS_ORIGIN}/#tgWebAppData={encoded_init}&tgWebAppPlatform=android&tgWebAppVersion=8.0"

        json_v_init = json.dumps(v_init)
        await page.add_init_script(f"""
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

            const mockWebApp = {{
                initData: {json_v_init},
                initDataUnsafe: {{
                    start_param: '',
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
            window.Telegram = {{ WebApp: mockWebApp }};
            window.__victorsTurnstileToken = null;
            window.__victorsHumanPass = null;
        """)

        logger.info("Navigating to Victor's Company web app...")
        try:
            await page.goto(target_url, wait_until="domcontentloaded", timeout=20000)
        except Exception as e:
            logger.warning(f"Navigation warning: {e}")

        await asyncio.sleep(3.0)

        # Check for Turnstile
        for attempt in range(12):
            if acquired_pass_dict["pass"] or acquired_token_dict["token"]:
                break
            tok = await page.evaluate("() => window.__victorsTurnstileToken || (document.querySelector('[name=\"cf-turnstile-response\"]')?.value) || (window.turnstile && typeof window.turnstile.getResponse === 'function' ? window.turnstile.getResponse() : null) || null")
            if tok and len(tok) > 20:
                acquired_token_dict["token"] = tok
                break
            
            # Try clicking visible iframe checkbox if found
            ts_iframe = page.locator("iframe[src*='challenges.cloudflare.com']").first
            if await ts_iframe.count() > 0:
                try:
                    box = await ts_iframe.bounding_box()
                    if box and box["width"] >= 200 and box["height"] >= 45:
                        click_x = box["x"] + 32.0
                        click_y = box["y"] + (box["height"] / 2.0)
                        logger.info(f"Dispatched click on Turnstile checkbox at ({click_x:.1f}, {click_y:.1f})")
                        await page.mouse.move(click_x, click_y, steps=5)
                        await page.mouse.down()
                        await asyncio.sleep(0.1)
                        await page.mouse.up()
                except Exception:
                    pass
            await asyncio.sleep(2.0)

        token = acquired_token_dict["token"]
        human_pass = acquired_pass_dict["pass"]

        if token and not human_pass:
            logger.info(f"Using captured turnstileToken to log in to /api/auth/login...")
            headers = {
                "Authorization": f"tma {v_init}",
                "Content-Type": "application/json",
                "Origin": VICTORS_ORIGIN,
                "Referer": f"{VICTORS_ORIGIN}/",
                "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 Mobile"
            }
            body = {
                "turnstileToken": token,
                "device": {
                    "platform": "android",
                    "tgVersion": "8.0",
                    "screen": "430x932@3",
                    "ram": 8,
                    "cpu": 8
                }
            }
            st, res = safe_api("POST", "/auth/login", payload=body, headers=headers)
            logger.info(f"/auth/login response ({st}): {res}")
            if st in (200, 201) and isinstance(res, dict):
                human_pass = res.get("humanPass")

        await browser.close()

    if not human_pass:
        logger.error("Could not acquire humanPass! Turnstile challenge was not solved.")
        return

    logger.info(f"🎉 SUCCESS! Acquired humanPass: {human_pass}")

    # Save to Upstash Redis
    try:
        pass_req = urllib.request.Request(
            f"{UPSTASH_URL}/set/victors:pass:{uid}",
            data=json.dumps({"humanPass": human_pass, "updated_at": time.time()}).encode(),
            headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"},
            method="POST"
        )
        with urllib.request.urlopen(pass_req, timeout=10) as pr:
            logger.info(f"Saved victors:pass:{uid} to Upstash Redis!")
    except Exception as pe:
        logger.warning(f"Error saving pass to Upstash: {pe}")

    auth_h = {
        "Authorization": f"tma {v_init}",
        "x-human-pass": str(human_pass),
        "Content-Type": "application/json",
        "Origin": VICTORS_ORIGIN,
        "Referer": f"{VICTORS_ORIGIN}/",
        "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 Mobile"
    }

    logger.info("=== 3. Executing Claims & Mining on Live Account ===")
    
    # A. Check Profile
    st, me = safe_api("GET", "/me", headers=auth_h)
    logger.info(f"Profile status ({st}): {json.dumps(me)[:300]}")

    # B. Daily Check-in (Clock in)
    st, ck = safe_api("POST", "/checkin", payload={}, headers=auth_h)
    logger.info(f"Daily Check-in status ({st}): {ck}")

    # C. Claim Mined Shift Yield (54+ VIC Cart)
    st, mc = safe_api("POST", "/mining/claim", payload={}, headers=auth_h)
    logger.info(f"Mining Claim status ({st}): {mc}")

    # D. Unlock Level 57
    st, lu = safe_api("POST", "/levels/unlock", payload={"level": 57}, headers=auth_h)
    logger.info(f"Level 57 Unlock status ({st}): {lu}")

    # E. Fetch Tasks & Claim
    st, td = safe_api("GET", "/tasks", headers=auth_h)
    if st == 200 and isinstance(td, dict):
        tasks = td.get("tasks", [])
        logger.info(f"Total tasks available: {len(tasks)}")
        for t in tasks:
            tid = t.get("id") or t.get("taskId")
            title = t.get("title") or t.get("name") or tid
            claimed = t.get("claimed", False)
            status = t.get("status")
            if not claimed:
                logger.info(f"Attempting to claim task '{title}' ({tid}, status: {status})...")
                # simulate dwell
                await asyncio.sleep(4.2)
                st_c, res_c = safe_api("POST", "/tasks/claim", payload={"taskId": tid}, headers=auth_h)
                logger.info(f"  Claim result ({st_c}): {res_c}")

    # F. Refresh profile to show final balances
    st, final_me = safe_api("GET", "/me", headers=auth_h)
    if st == 200 and isinstance(final_me, dict):
        u = final_me.get("user") or final_me
        logger.info(f"🏆 Final Account State: Level {u.get('manualUnlockedLevel')}, VIC Balance: {u.get('inAppBalance')}")

asyncio.run(main())
