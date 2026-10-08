#!/usr/bin/env python3
"""
MY AGY AI — 100% Cloud MRG Auto-Farming & Turnstile Solver Engine
Runs 100% in Cloud (GitHub Actions / Cloud VMs) — Zero Phone Load.

Solves Cloudflare Turnstile invisibly using Playwright Chromium,
refreshes `humanVerifiedUntil` pass across all 18 accounts,
claims accumulated mining rewards, and compounds miner levels.
"""

import os
import sys
import json
import time
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


async def acquire_turnstile_tokens_batch(needed_count: int) -> list:
    """
    Launches headless Chromium using Playwright in the cloud,
    navigates to app.mrgtoken.xyz, and generates fresh Turnstile tokens.
    """
    if needed_count <= 0:
        return []

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.error("Playwright is not installed. Run: pip install playwright && playwright install chromium")
        return []

    logger.info(f"🌐 Launching Cloud Headless Chromium for {needed_count} Turnstile challenge(s)...")
    tokens = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--window-size=1280,800"
            ]
        )

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
            viewport={"width": 412, "height": 915},
            locale="en-US",
            timezone_id="UTC"
        )

        page = await context.new_page()

        # Stealth script injections
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.Telegram = {
                WebApp: {
                    initData: '',
                    initDataUnsafe: {},
                    ready: () => {},
                    expand: () => {},
                    close: () => {},
                    colorScheme: 'dark',
                    themeParams: {}
                }
            };
        """)

        logger.info(f"⏳ Navigating to {APP_ORIGIN}...")
        try:
            await page.goto(APP_ORIGIN, wait_until="networkidle", timeout=30000)
        except Exception as e:
            logger.warning(f"Navigation note: {e}")

        # Solve sequentially for the required number of tokens
        for i in range(needed_count):
            logger.info(f"🔄 Solving Cloudflare Turnstile token [{i+1}/{needed_count}]...")
            solve_js = f"""
                async () => {{
                    return new Promise((resolve) => {{
                        let interval = setInterval(() => {{
                            if (window.turnstile && typeof window.turnstile.render === 'function') {{
                                clearInterval(interval);
                                try {{
                                    let container = document.getElementById('cf-turnstile-slot-{i}');
                                    if (!container) {{
                                        container = document.createElement('div');
                                        container.id = 'cf-turnstile-slot-{i}';
                                        document.body.appendChild(container);
                                    }}
                                    window.turnstile.render(container, {{
                                        sitekey: '{SITE_KEY}',
                                        callback: function(tok) {{
                                            resolve({{ success: true, token: tok }});
                                        }},
                                        'error-callback': function(err) {{
                                            resolve({{ success: false, error: String(err) }});
                                        }},
                                        'expired-callback': function() {{
                                            resolve({{ success: false, error: 'expired' }});
                                        }}
                                    }});
                                }} catch (e) {{
                                    resolve({{ success: false, error: String(e) }});
                                }}
                            }}
                        }}, 250);

                        setTimeout(() => {{
                            clearInterval(interval);
                            resolve({{ success: false, error: 'timeout_25s' }});
                        }}, 25000);
                    }});
                }}
            """
            result = await page.evaluate(solve_js)
            if result.get("success") and result.get("token"):
                tok = result["token"]
                tokens.append(tok)
                logger.info(f"✅ Acquired Turnstile Token #{i+1}: {tok[:18]}... (len: {len(tok)})")
            else:
                logger.error(f"❌ Failed to acquire Turnstile Token #{i+1}: {result.get('error')}")

            await asyncio.sleep(1.5)

        await browser.close()

    return tokens


async def run_mrg_auto_solver():
    """Main workflow: audits all 18 accounts, solves needed challenges, and auto-claims."""
    logger.info("====================================================================")
    logger.info("🚀 Starting 100% Cloud MRG Auto-Farming & Turnstile Solver Cycle")
    logger.info("====================================================================")

    accounts_data = []
    accounts_needing_solver = []

    # 1. Fetch tokens and inspect account states
    for idx, uid in enumerate(FLEET_UIDS, 1):
        tok_dict = get_token_from_upstash(uid)
        mrg_init = tok_dict.get("mrg_init_data")

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
    logger.info(f"📊 Audit Summary: {len(accounts_data)} accounts connected. {needed_count} accounts require Turnstile solving.")

    # 2. Acquire fresh Turnstile tokens in headless browser if needed
    fresh_tokens = []
    if needed_count > 0:
        fresh_tokens = await acquire_turnstile_tokens_batch(needed_count)

    # 3. Process accounts needing verification
    solved_count = 0
    total_claimed_mrg = 0.0

    for i, acc in enumerate(accounts_needing_solver):
        uid = acc["uid"]
        m_init = acc["init_data"]

        if i < len(fresh_tokens):
            turnstile_token = fresh_tokens[i]
            # Call /api/user/verify-human
            ver_res = verify_human_token(m_init, turnstile_token)
            if ver_res.get("success"):
                logger.info(f"🎉 UID {uid}: verify-human succeeded! Human pass unlocked for 8 hours.")
                solved_count += 1

                # Claim accumulated mining rewards
                claim_res = claim_mining_reward(m_init, turnstile_token)
                claimed_amt = float(claim_res.get("claimedAmount") or acc["stat"]["unclaimed"])
                total_claimed_mrg += claimed_amt
                logger.info(f"⛏️ UID {uid}: Successfully claimed {claimed_amt:.2f} MRG! Miner restarted.")

                # Auto-upgrade level if balance allows
                new_bal = acc["stat"]["inAppBalance"] + claimed_amt
                auto_unlock_mrg_level(m_init, acc["stat"]["manualUnlockedLevel"], new_bal)
            else:
                logger.error(f"❌ UID {uid}: verify-human rejected: {ver_res}")
        else:
            logger.warning(f"⚠️ UID {uid}: No fresh token available to solve challenge.")

    # 4. Also claim rewards for accounts that already had an active pass
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

    # 5. Master Account Referral Sweep
    master_acc = next((a for a in accounts_data if a["uid"] == 6727787768), None)
    if master_acc:
        m_init = master_acc["init_data"]
        safe_post(f"{API_BASE}/api/user/claim-commission", {"initData": m_init})
        safe_post(f"{API_BASE}/api/user/claim-one-time-bonus", {"initData": m_init})
        logger.info("👑 Master Account referral commission and team bonus claimed.")

    # 6. Telegram Telemetry Notification
    report_msg = (
        f"🚀 <b>MRG 100% Cloud Auto-Farming Report</b>\n\n"
        f"• <b>Total Fleet Accounts:</b> 18\n"
        f"• <b>Active Accounts Checked:</b> {len(accounts_data)}\n"
        f"• <b>Turnstile Passes Solved:</b> {solved_count}/{needed_count}\n"
        f"• <b>Total MRG Harvested:</b> {total_claimed_mrg:.2f} MRG\n"
        f"• <b>Execution Time:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
        f"⚡ <i>Cloud Mining is ACTIVE across all nodes. Zero stops.</i>"
    )
    logger.info(f"📢 Telemetry: Solved {solved_count}/{needed_count}, Claimed {total_claimed_mrg:.2f} MRG.")
    send_tg_alert(report_msg)


if __name__ == "__main__":
    asyncio.run(run_mrg_auto_solver())
