#!/usr/bin/env python3
"""
victors_cloud_phone_launcher.py
Interactive Cloud Virtual Phone Runner for Victor's Company (@VictorsCompanybot).
Runs in GitHub Actions alongside Xvfb, noVNC, and Cloudflare Tunnel.
Streams interactive mobile browser to the user's phone via Cloudflare Tunnel.
As the user taps Turnstile on the virtual screen, it captures tokens and automatically
executes the full recruitment qualification pipeline across all 16 fleet accounts.
"""

import os
import sys
import json
import time
import urllib.parse
import urllib.request
import logging
import subprocess

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("victors_cloud_phone")

UPSTASH_URL = os.getenv("UPSTASH_URL") or "https://relaxing-starfish-285827.upstash.io"
UPSTASH_TOKEN = os.getenv("UPSTASH_TOKEN") or "gQAAAAAABFyDAAIgcDI5MDYyYWZjNzYzNzk0ZmRjYjhmNTA4ZDI4ODlmODkzNw"
ALERT_BOT_TOKEN = os.getenv("ALERT_BOT_TOKEN") or "8858823950:AAEdX47g7as1xLYEudfRUHaVGUdNIaU_ku8"
OWNER_ID = os.getenv("OWNER_ID") or "6727787768"

VICTORS_SITEKEY = "0x4AAAAAAFD0KRgPRFVwDvgn"
VICTORS_ORIGIN = "https://app.victors.company"
VICTORS_API = "https://server.victors.company/api"
VICTORS_REF = "ref_A20AA96F18"

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
        logger.warning(f"Failed to send Telegram alert: {e}")


def load_fleet_ton_wallets() -> dict:
    """Fetch fleet TON wallets from Upstash Redis."""
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
        logger.warning(f"Error fetching TON wallets from Upstash: {e}")
    return {}


def get_token_from_upstash(uid: int) -> dict:
    """Fetch tokens from Upstash Redis."""
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


def save_victors_pass_to_upstash(uid: int, human_pass: str):
    """Saves valid Victor's Company humanPass to Upstash Redis."""
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
        logger.warning(f"Error saving Victor's pass to Redis: {e}")


def safe_post(url: str, json_data: dict, extra_headers: dict = None) -> tuple:
    """Synchronous POST request wrapper."""
    headers = {
        "Content-Type": "application/json",
        "Origin": VICTORS_ORIGIN,
        "Referer": f"{VICTORS_ORIGIN}/",
        "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 Mobile"
    }
    if extra_headers:
        headers.update(extra_headers)
    try:
        data_bytes = json.dumps(json_data).encode("utf-8")
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body.startswith("{") or body.startswith("[") else body
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8") if e.fp else ""
        try:
            return e.code, json.loads(err_body)
        except Exception:
            return e.code, err_body
    except Exception as e:
        return 0, str(e)


def qualify_recruit(uid: int, v_init: str, human_pass: str, is_master: bool, ton_wallets: dict):
    """Qualifies sub-account: links TON wallet, claims task, sweeps master bonus."""
    v_headers = {
        "Content-Type": "application/json",
        "Authorization": f"tma {v_init}",
        "x-human-pass": str(human_pass),
        "Origin": VICTORS_ORIGIN,
        "Referer": f"{VICTORS_ORIGIN}/",
        "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 Mobile"
    }

    # 1. Tutorial & checkin
    safe_post(f"{VICTORS_API}/me/tutorial", {}, extra_headers=v_headers)
    safe_post(f"{VICTORS_API}/checkin", {}, extra_headers=v_headers)

    # 2. Connect TON wallet & claim task
    w_entry = ton_wallets.get(str(uid)) or ton_wallets.get(uid)
    if w_entry and isinstance(w_entry, dict) and w_entry.get("address"):
        ton_addr = w_entry["address"]
        safe_post(f"{VICTORS_API}/wallet/connect", {"address": ton_addr}, extra_headers=v_headers)
        t_code, t_res = safe_post(f"{VICTORS_API}/tasks/claim", {"taskId": "connect-wallet"}, extra_headers=v_headers)
        logger.info(f"🎯 UID {uid}: Claimed connect-wallet task -> QUALIFIED: {t_code} {t_res}")

    # 3. Mining claim
    safe_post(f"{VICTORS_API}/mining/claim", {}, extra_headers=v_headers)

    # 4. Master sweeps referral hiring bonus (+100 V per recruit)
    if is_master:
        b_code, b_res = safe_post(f"{VICTORS_API}/referral/claim-bonus", {}, extra_headers=v_headers)
        c_code, c_res = safe_post(f"{VICTORS_API}/referral/claim-commission", {}, extra_headers=v_headers)
        logger.info(f"👑 Master recruitment bonus swept: {b_code} {b_res}, commissions: {c_code} {c_res}")


def main():
    logger.info("====================================================================")
    logger.info("📱 Starting Victor's Company Cloud Virtual Phone Assistant Engine")
    logger.info("====================================================================")

    ton_wallets = load_fleet_ton_wallets()
    accounts_to_process = []

    for uid in FLEET_UIDS:
        tok_dict = get_token_from_upstash(uid)
        vic_init = tok_dict.get("victors_init_data")
        if vic_init:
            accounts_to_process.append({
                "uid": uid,
                "init_data": vic_init,
                "is_master": (uid == 6727787768 or str(uid) == str(OWNER_ID))
            })

    logger.info(f"Loaded {len(accounts_to_process)} fleet accounts for Victor's Company.")
    if not accounts_to_process:
        logger.error("No accounts found with victors_init_data.")
        return

    # Use SeleniumBase or Playwright in headful mode attached to DISPLAY=:99
    try:
        from patchright.sync_api import sync_playwright
    except ImportError:
        from playwright.sync_api import sync_playwright

    qualified_count = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--window-size=450,950",
                "--window-position=0,0"
            ]
        )
        context = browser.new_context(
            viewport={"width": 430, "height": 932},
            is_mobile=True,
            has_touch=True,
            user_agent="Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36"
        )
        page = context.new_page()

        for idx, acc in enumerate(accounts_to_process, 1):
            uid = acc["uid"]
            v_init = acc["init_data"]
            is_master = acc["is_master"]
            ref_to_bind = "" if is_master else VICTORS_REF

            logger.info(f"[{idx}/{len(accounts_to_process)}] 📲 Loading UID {uid} onto Virtual Phone screen...")
            target_url = f"{VICTORS_ORIGIN}/#tgWebAppData={v_init}"

            # Mock Telegram WebApp object
            page.add_init_script(f"""
                window.__capturedTurnstileToken = null;
                const mockWebApp = {{
                    initData: {json.dumps(v_init)},
                    initDataUnsafe: {{
                        start_param: {json.dumps(ref_to_bind)},
                        user: {{ id: {uid} }}
                    }},
                    version: '8.0',
                    platform: 'android',
                    ready: () => {{}},
                    expand: () => {{}},
                    close: () => {{}}
                }};
                window.Telegram = {{ WebApp: mockWebApp }};

                // Intercept Turnstile callback
                const origFetch = window.fetch;
                window.fetch = async function(...args) {{
                    const url = String(args[0] || '');
                    if (url.includes('/auth/login')) {{
                        try {{
                            const b = JSON.parse(args[1]?.body || '{{}}');
                            if (b.turnstileToken) {{
                                window.__capturedTurnstileToken = b.turnstileToken;
                            }}
                        }} catch(e) {{}}
                    }}
                    return origFetch.apply(this, args);
                }};
            """)

            page.goto(target_url, timeout=30000)
            logger.info(f"⏳ Waiting for Turnstile interaction for UID {uid} (up to 45 seconds)...")

            token = None
            for _ in range(45):
                time.sleep(1.0)
                try:
                    tok = page.evaluate("""() => {
                        return window.__capturedTurnstileToken ||
                               (window.turnstile && typeof window.turnstile.getResponse === 'function' ? window.turnstile.getResponse() : null) ||
                               null;
                    }""")
                    if tok and len(tok) > 20:
                        token = tok
                        break
                except Exception:
                    pass

            if token:
                logger.info(f"🎉 UID {uid}: Turnstile solved ({token[:16]}...)! Logging in...")
                login_p = {"turnstileToken": token}
                if not is_master:
                    login_p["startParam"] = VICTORS_REF

                st_code, body = safe_post(
                    f"{VICTORS_API}/auth/login",
                    login_p,
                    extra_headers={"Authorization": f"tma {v_init}"}
                )
                if st_code in (200, 201) and isinstance(body, dict):
                    hp = body.get("humanPass") or (body.get("data", {}).get("humanPass") if isinstance(body.get("data"), dict) else None)
                    if hp:
                        save_victors_pass_to_upstash(uid, str(hp))
                        logger.info(f"✅ UID {uid}: humanPass saved. Qualifying recruit...")
                        qualify_recruit(uid, v_init, str(hp), is_master, ton_wallets)
                        qualified_count += 1
                        send_tg_alert(f"✅ <b>Victor's Recruit Qualified ({qualified_count}/{len(accounts_to_process)})</b>\nUID: <code>{uid}</code> bound to <code>{VICTORS_REF}</code>!")
            else:
                logger.warning(f"⚠️ UID {uid}: No token captured within timeout. Proceeding...")

        browser.close()

    final_msg = (
        f"👑 <b>Victor's Company Virtual Phone Session Finished</b>\n\n"
        f"• <b>Total Qualified Recruits:</b> {qualified_count}/{len(accounts_to_process)}\n"
        f"• <b>Master Referral:</b> <code>{VICTORS_REF}</code>\n"
        f"• <b>Time:</b> {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n\n"
        f"⚡ <i>100% Cloud Execution via Cloudflare Tunnel.</i>"
    )
    logger.info(final_msg)
    send_tg_alert(final_msg)


if __name__ == "__main__":
    main()
