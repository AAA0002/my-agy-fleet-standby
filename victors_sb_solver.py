#!/usr/bin/env python3
"""
victors_sb_solver.py
Dedicated 100% Cloud Turnstile Solver & Referral Qualification Engine for Victor's Company (@VictorsCompanybot).
Runs in GitHub Actions / Cloud VMs using SeleniumBase UC Mode + CDP Stealth (Zero Phone Load).
Bypasses Cloudflare Turnstile natively without requiring paid third-party APIs.
Qualifies all fleet recruits under Master referral ref_A20AA96F18.
"""

import os
import sys
import json
import time
import urllib.parse
import urllib.request
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("victors_sb_solver")

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
    """Sends notification to Owner Telegram."""
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
        logger.warning(f"Error fetching TON wallets from Upstash Redis: {e}")
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
        logger.warning(f"Upstash token fetch warning for UID {uid}: {e}")
    return {}


def get_victors_pass_from_upstash(uid: int) -> str:
    """Fetch saved humanPass from Upstash Redis."""
    try:
        req = urllib.request.Request(
            f"{UPSTASH_URL}/get/victors:pass:{uid}",
            headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            res = data.get("result")
            if res:
                d = json.loads(res) if isinstance(res, str) else res
                return d.get("humanPass")
    except Exception:
        pass
    return None


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


def safe_get(url: str, extra_headers: dict = None) -> tuple:
    """Synchronous GET request wrapper."""
    headers = {
        "Origin": VICTORS_ORIGIN,
        "Referer": f"{VICTORS_ORIGIN}/",
        "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 Mobile"
    }
    if extra_headers:
        headers.update(extra_headers)
    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
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


def probe_account(uid: int, v_init: str) -> tuple:
    """Rapid health probe to check session validity."""
    existing_hp = get_victors_pass_from_upstash(uid)
    if existing_hp:
        code, body = safe_get(
            f"{VICTORS_API}/me",
            extra_headers={"Authorization": f"tma {v_init}", "x-human-pass": existing_hp}
        )
        if code == 200 and isinstance(body, dict) and body.get("success") is True:
            return "ALREADY_AUTH", existing_hp

    code, body = safe_post(
        f"{VICTORS_API}/auth/login",
        {"startParam": VICTORS_REF},
        extra_headers={"Authorization": f"tma {v_init}"}
    )
    if code == 403 and isinstance(body, dict) and body.get("code") == "HUMAN_REQUIRED":
        return "HUMAN_REQUIRED", None
    elif code in (200, 201) and isinstance(body, dict):
        hp = body.get("humanPass") or (body.get("data", {}).get("humanPass") if isinstance(body.get("data"), dict) else None)
        if hp:
            return "ALREADY_AUTH", hp
    elif code == 401:
        return "EXPIRED", body

    return "UNKNOWN", body


def run_pipeline_for_account(uid: int, v_init: str, human_pass: str, is_master: bool, ton_wallets: dict):
    """Executes the full recruitment qualification pipeline."""
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
        w_code, _ = safe_post(f"{VICTORS_API}/wallet/connect", {"address": ton_addr}, extra_headers=v_headers)
        t_code, t_res = safe_post(f"{VICTORS_API}/tasks/claim", {"taskId": "connect-wallet"}, extra_headers=v_headers)
        logger.info(f"🎯 UID {uid}: TON wallet {ton_addr[:10]}... connected ({w_code}), task claimed -> QUALIFIED: {t_code} {t_res}")

    # 3. Mining claim
    safe_post(f"{VICTORS_API}/mining/claim", {}, extra_headers=v_headers)


def sweep_master_bonuses(master_uid: int):
    """Sweeps recruitment hiring bonus (+100 V per qualified recruit) for Master Account."""
    headers = {
        "Content-Type": "application/json",
        "Origin": VICTORS_ORIGIN,
        "Referer": f"{VICTORS_ORIGIN}/",
        "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 Mobile"
    }
    b_code, b_res = safe_post(f"{VICTORS_API}/referral/claim-bonus", {}, extra_headers=headers)
    c_code, c_res = safe_post(f"{VICTORS_API}/referral/claim-commission", {}, extra_headers=headers)
    logger.info(f"👑 Master recruitment bonus swept: {b_code} {b_res}, commissions: {c_code} {c_res}")


def solve_victors_with_seleniumbase():
    """Main execution using SeleniumBase UC mode to solve Turnstile for Victor's accounts."""
    try:
        from seleniumbase import SB
    except ImportError:
        logger.error("SeleniumBase not installed. Please install with: pip install seleniumbase")
        return

    ton_wallets = load_fleet_ton_wallets()
    raw_accounts = []

    for uid in FLEET_UIDS:
        tok_dict = get_token_from_upstash(uid)
        vic_init = tok_dict.get("victors_init_data")
        name = tok_dict.get("name", f"UID {uid}")
        if vic_init:
            raw_accounts.append({
                "uid": uid,
                "name": name,
                "init_data": vic_init,
                "is_master": (uid == 6727787768 or str(uid) == str(OWNER_ID))
            })

    logger.info(f"🏢 Found {len(raw_accounts)} accounts with Victor's Company initData. Running pre-flight probe...")

    active_accounts = []
    solved_count = 0

    for acc in raw_accounts:
        uid = acc["uid"]
        status, data = probe_account(uid, acc["init_data"])
        if status == "HUMAN_REQUIRED":
            logger.info(f"  👉 UID {uid} ({acc['name']}): Session valid -> READY for Turnstile.")
            active_accounts.append(acc)
        elif status == "ALREADY_AUTH":
            logger.info(f"  ✅ UID {uid} ({acc['name']}): Already authenticated! Running qualification...")
            save_victors_pass_to_upstash(uid, data)
            run_pipeline_for_account(uid, acc["init_data"], data, acc["is_master"], ton_wallets)
            solved_count += 1
        elif status == "EXPIRED":
            logger.warning(f"  ⚠️ UID {uid} ({acc['name']}): Session expired. Skipping.")
        else:
            active_accounts.append(acc)

    if not active_accounts:
        logger.info("No accounts currently requiring Turnstile. Checking Master bonuses...")
        sweep_master_bonuses(6727787768)
        return

    with SB(uc=True, test=True, xvfb=True, locale="en") as sb:
        for acc in active_accounts:
            uid = acc["uid"]
            name = acc["name"]
            v_init = acc["init_data"]
            is_master = acc["is_master"]
            ref_to_bind = "" if is_master else VICTORS_REF

            logger.info(f"🚀 Processing UID {uid} ({name}, is_master={is_master})...")
            encoded_init = urllib.parse.quote(v_init)
            target_url = (
                f"{VICTORS_ORIGIN}/#tgWebAppData={encoded_init}"
                f"&tgWebAppPlatform=android"
                f"&tgWebAppVersion=8.0"
                f"&tgWebAppThemeParams=%7B%22bg_color%22%3A%22%231a1147%22%2C%22text_color%22%3A%22%23ffffff%22%7D"
            )

            try:
                sb.uc_open(target_url)

                # Inject Telegram mock object & sessionStorage
                sb.execute_script(f"""
                    try {{
                        sessionStorage.setItem('__telegram__initParams', JSON.stringify({{
                            tgWebAppData: {json.dumps(v_init)},
                            tgWebAppPlatform: 'android',
                            tgWebAppVersion: '8.0'
                        }}));
                        sessionStorage.setItem('initParams', JSON.stringify({{
                            tgWebAppData: {json.dumps(v_init)},
                            tgWebAppPlatform: 'android',
                            tgWebAppVersion: '8.0'
                        }}));
                    }} catch(e) {{}}

                    window.__victorsTurnstileToken = null;
                    window.Telegram = window.Telegram || {{}};
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
                    Object.defineProperty(window.Telegram, 'WebApp', {{
                        get: () => mockWebApp,
                        set: (v) => {{ Object.assign(mockWebApp, v); mockWebApp.initData = {json.dumps(v_init)}; }},
                        configurable: true
                    }});
                """)

                # Attempt Turnstile solve
                sb.sleep(2.0)
                try:
                    sb.solve_captcha()
                except Exception:
                    pass

                # Poll for Turnstile token
                token = None
                for _ in range(15):
                    token = sb.execute_script("""
                        return (window.turnstile && typeof window.turnstile.getResponse === 'function' ? window.turnstile.getResponse() : null) || window.__victorsTurnstileToken || null;
                    """)
                    if token and len(token) > 20:
                        break
                    sb.sleep(1.0)

                if token and len(token) > 20:
                    logger.info(f"✅ UID {uid}: Cloudflare Turnstile SOLVED ({token[:16]}...)!")
                    login_p = {"turnstileToken": token}
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
                            save_victors_pass_to_upstash(uid, str(hp))
                            logger.info(f"🎉 UID {uid}: Acquired humanPass! Executing qualification pipeline...")
                            run_pipeline_for_account(uid, v_init, str(hp), is_master, ton_wallets)
                            solved_count += 1
                            send_tg_alert(f"✅ <b>Victor's Recruit Qualified ({solved_count}/{len(raw_accounts)})</b>\nUID: <code>{uid}</code> bound to <code>{VICTORS_REF}</code>!")
                    else:
                        logger.warning(f"UID {uid} /auth/login error: {st_code} {body}")
                else:
                    logger.warning(f"UID {uid}: Turnstile could not be solved in this cycle.")

            except Exception as e:
                logger.warning(f"UID {uid} processing note: {e}")

            sb.sleep(1.0)

    sweep_master_bonuses(6727787768)

    report_msg = (
        f"🏢 <b>Victor's Company Cloud Turnstile Solver Report</b>\n\n"
        f"• <b>Accounts Processed:</b> {len(raw_accounts)}\n"
        f"• <b>Turnstile Solved & Qualified:</b> {solved_count}/{len(raw_accounts)}\n"
        f"• <b>Master Referral Bound:</b> <code>{VICTORS_REF}</code>\n"
        f"• <b>Execution Time:</b> {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n\n"
        f"⚡ <i>100% Cloud Execution (SeleniumBase UC Stealth). Zero phone load.</i>"
    )
    logger.info(f"📢 Final: {solved_count}/{len(raw_accounts)} accounts solved & qualified.")
    send_tg_alert(report_msg)


if __name__ == "__main__":
    solve_victors_with_seleniumbase()
