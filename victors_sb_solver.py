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
        logger.warning(f"Error saving Victor's pass to Redis for UID {uid}: {e}")


def safe_post(url: str, json_data: dict, extra_headers: dict = None) -> tuple:
    """Synchronous POST request wrapper."""
    headers = {
        "Content-Type": "application/json",
        "Origin": VICTORS_ORIGIN,
        "Referer": f"{VICTORS_ORIGIN}/",
        "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36"
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
        "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36"
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


def run_pipeline_for_account(uid: int, v_init: str, human_pass: str, is_master: bool, ton_wallets: dict) -> bool:
    """Executes full recruit qualification, wallet binding, and mining claiming pipeline."""
    v_headers = {
        "Content-Type": "application/json",
        "Authorization": f"tma {v_init}",
        "x-human-pass": str(human_pass),
        "Origin": VICTORS_ORIGIN,
        "Referer": f"{VICTORS_ORIGIN}/",
        "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 Mobile"
    }

    # 1. Tutorial & Daily Check-in
    safe_post(f"{VICTORS_API}/me/tutorial", {}, extra_headers=v_headers)
    safe_post(f"{VICTORS_API}/checkin", {}, extra_headers=v_headers)

    # 2. Connect TON wallet to qualify recruit & unlock Level 1 Miner
    w_entry = ton_wallets.get(str(uid)) or ton_wallets.get(uid)
    if w_entry and isinstance(w_entry, dict) and w_entry.get("address"):
        ton_addr = w_entry["address"]
        c_code, c_res = safe_post(f"{VICTORS_API}/wallet/connect", {"address": ton_addr}, extra_headers=v_headers)
        logger.info(f"💼 [Victor's] UID {uid}: Connected TON wallet {ton_addr[:12]}... (HTTP {c_code})")

        # Claim connect-wallet task -> this sets qualified: true in backend!
        t_code, t_res = safe_post(f"{VICTORS_API}/tasks/claim", {"taskId": "connect-wallet"}, extra_headers=v_headers)
        logger.info(f"🎯 [Victor's] UID {uid}: Claimed connect-wallet task: {t_code} {t_res}")

    # 3. Claim passive mining
    m_code, m_res = safe_post(f"{VICTORS_API}/mining/claim", {}, extra_headers=v_headers)
    logger.info(f"⛏️ [Victor's] UID {uid}: Mining claim: {m_code} {m_res}")

    # 4. Check profile & unlock higher levels
    p_code, p_res = safe_get(f"{VICTORS_API}/me", extra_headers=v_headers)
    if p_code == 200 and isinstance(p_res, dict):
        u_info = p_res.get("user") or p_res
        cur_lvl = u_info.get("level", 1)
        unlocked = u_info.get("unlockedLevel", cur_lvl)
        if unlocked > cur_lvl:
            safe_post(f"{VICTORS_API}/levels/unlock", {"level": unlocked}, extra_headers=v_headers)
            logger.info(f"⬆️ [Victor's] UID {uid}: Upgraded to level {unlocked}!")

    # 5. Play arcade mining run
    try:
        _, arc_d = safe_get(f"{VICTORS_API}/arcade", extra_headers=v_headers)
        if arc_d and isinstance(arc_d, dict) and arc_d.get("runsLeft", 0) > 0:
            st_c, _ = safe_post(f"{VICTORS_API}/arcade/mine/start", {"tool": "pickaxe", "items": []}, extra_headers=v_headers)
            if st_c in (200, 201):
                for d in range(4):
                    time.sleep(0.5)
                    _, d_res = safe_post(f"{VICTORS_API}/arcade/mine/dig", {"x": 4, "y": d}, extra_headers=v_headers)
                    if not d_res or (isinstance(d_res, dict) and d_res.get("result") == "bust"):
                        break
                safe_post(f"{VICTORS_API}/arcade/mine/end", {}, extra_headers=v_headers)
                logger.info(f"🎮 [Victor's] UID {uid}: Completed arcade mining run.")
    except Exception:
        pass

    # 6. Master Account sweeps recruitment hiring bonuses (+100 V per recruit)
    if is_master:
        b_code, b_res = safe_post(f"{VICTORS_API}/referral/claim-bonus", {}, extra_headers=v_headers)
        c_code, c_res = safe_post(f"{VICTORS_API}/referral/claim-commission", {}, extra_headers=v_headers)
        logger.info(f"👑 [Victor's] Master recruitment bonus: {b_code} {b_res}, commissions: {c_code} {c_res}")

    return True


def solve_victors_with_seleniumbase():
    """Main execution using SeleniumBase UC mode to solve Turnstile for Victor's accounts."""
    try:
        from seleniumbase import SB
    except ImportError:
        logger.error("SeleniumBase not installed. Please install with: pip install seleniumbase")
        return

    ton_wallets = load_fleet_ton_wallets()
    accounts_to_process = []

    # 1. Collect accounts with victors_init_data
    for uid in FLEET_UIDS:
        tok_dict = get_token_from_upstash(uid)
        vic_init = tok_dict.get("victors_init_data")
        if vic_init:
            accounts_to_process.append({
                "uid": uid,
                "init_data": vic_init,
                "is_master": (uid == 6727787768 or str(uid) == str(OWNER_ID))
            })

    logger.info(f"🏢 Found {len(accounts_to_process)} accounts with Victor's Company initData.")
    if not accounts_to_process:
        return

    solved_count = 0

    # 2. Run SeleniumBase UC mode session
    with SB(uc=True, test=True, xvfb=True, locale="en") as sb:
        for acc in accounts_to_process:
            uid = acc["uid"]
            v_init = acc["init_data"]
            is_master = acc["is_master"]
            ref_to_bind = "" if is_master else VICTORS_REF

            logger.info(f"🚀 Processing UID {uid} (is_master={is_master})...")
            target_url = f"{VICTORS_ORIGIN}/#tgWebAppData={v_init}"

            try:
                sb.activate_cdp_mode()
                sb.uc_open_with_reconnect(target_url, reconnect_time=4)

                # Inject Telegram mock object
                sb.execute_script(f"""
                    window.__victorsTurnstileToken = null;
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
                """)

                # Attempt automatic Turnstile bypass
                sb.sleep(2.5)
                sb.solve_captcha()

                # Poll for Turnstile token
                token = None
                for _ in range(12):
                    token = sb.execute_script("""
                        return (window.turnstile && typeof window.turnstile.getResponse === 'function' ? window.turnstile.getResponse() : null) || window.__victorsTurnstileToken || null;
                    """)
                    if token and len(token) > 20:
                        break
                    sb.sleep(1.0)

                if not token:
                    # Programmatic render attempt
                    token = sb.execute_script(f"""
                        return new Promise((resolve) => {{
                            if (!window.turnstile) return resolve(null);
                            let div = document.getElementById('sb-cf-slot');
                            if (!div) {{
                                div = document.createElement('div');
                                div.id = 'sb-cf-slot';
                                document.body.appendChild(div);
                            }}
                            window.turnstile.render(div, {{
                                sitekey: '{VICTORS_SITEKEY}',
                                action: 'login',
                                appearance: 'interaction-only',
                                callback: (tok) => resolve(tok),
                                'error-callback': () => resolve(null)
                            }});
                            setTimeout(() => resolve(null), 10000);
                        }});
                    """)

                if token and len(token) > 20:
                    logger.info(f"✅ UID {uid}: Cloudflare Turnstile SOLVED ({token[:16]}...)!")

                    # Call /api/auth/login
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
                    else:
                        logger.warning(f"UID {uid} /auth/login error: {st_code} {body}")
                else:
                    logger.warning(f"UID {uid}: Turnstile could not be solved in this cycle.")

            except Exception as e:
                logger.warning(f"UID {uid} processing note: {e}")

            sb.sleep(1.0)

    report_msg = (
        f"🏢 <b>Victor's Company Cloud Turnstile Solver Report</b>\n\n"
        f"• <b>Accounts Processed:</b> {len(accounts_to_process)}\n"
        f"• <b>Turnstile Solved & Qualified:</b> {solved_count}/{len(accounts_to_process)}\n"
        f"• <b>Master Referral Bound:</b> <code>{VICTORS_REF}</code>\n"
        f"• <b>Execution Time:</b> {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n\n"
        f"⚡ <i>100% Cloud Execution (SeleniumBase UC Stealth). Zero phone load.</i>"
    )
    logger.info(f"📢 Final: {solved_count}/{len(accounts_to_process)} accounts solved & qualified.")
    send_tg_alert(report_msg)


if __name__ == "__main__":
    solve_victors_with_seleniumbase()
