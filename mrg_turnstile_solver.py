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


async def solve_turnstile_for_account(browser, acc_info: dict) -> bool:
    """
    Opens app.mrgtoken.xyz with account's actual Telegram initData in stealth browser.
    Allows the app to mount the Turnstile component, solve it, and invoke verify-human.
    """
    uid = acc_info["uid"]
    m_init = acc_info["init_data"]

    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
        viewport={"width": 412, "height": 915},
        locale="en-US",
        timezone_id="UTC"
    )

    page = await context.new_page()

    # Pass the real initData via Telegram WebApp mock and URL hash
    encoded_init = urllib.parse.quote(m_init)
    target_url = f"{APP_ORIGIN}/#tgWebAppData={encoded_init}"

    await page.add_init_script(f"""
        Object.defineProperty(navigator, 'webdriver', {{ get: () => undefined }});
        window.Telegram = {{
            WebApp: {{
                initData: '{m_init}',
                initDataUnsafe: {{}},
                ready: () => {{}},
                expand: () => {{}},
                close: () => {{}},
                colorScheme: 'dark',
                themeParams: {{}}
            }}
        }};
    """)

    verified_event = asyncio.Event()
    acquired_token = {"token": None}

    # Intercept network requests and responses
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

    logger.info(f"⏳ Navigating to {APP_ORIGIN} for UID {uid}...")
    try:
        await page.goto(target_url, wait_until="load", timeout=25000)
    except Exception as e:
        logger.warning(f"UID {uid} navigation note: {e}")

    # Allow React hydration
    await asyncio.sleep(2.5)

    # 1. Click the 'Claim' button in the MRG UI to trigger the claim & security verification modal
    try:
        clicked = await page.evaluate("""
            () => {
                const btns = Array.from(document.querySelectorAll('button'));
                const claimBtn = btns.find(b => b.innerText && b.innerText.toLowerCase().includes('claim'));
                if (claimBtn) {
                    claimBtn.click();
                    return true;
                }
                return false;
            }
        """)
        if clicked:
            logger.info(f"🖱️ Clicked Claim button for UID {uid}.")
    except Exception as e:
        logger.warning(f"UID {uid} click note: {e}")

    # 2. Check for Turnstile iframe and click checkbox if present
    for _ in range(8):
        if verified_event.is_set():
            break
        try:
            ts_frame = page.frame_locator("iframe[src*='challenges.cloudflare.com']")
            checkbox = ts_frame.locator("input[type='checkbox'], #challenge-stage, .ctp-checkbox-label, body")
            if await checkbox.count() > 0:
                logger.info(f"🖱️ Found Turnstile iframe checkbox for UID {uid}! Clicking...")
                await checkbox.first.click(timeout=3000)
                break
        except Exception:
            pass
        await asyncio.sleep(1.0)

    # Wait for the app's native verify-human call
    try:
        await asyncio.wait_for(verified_event.wait(), timeout=12.0)
        logger.info(f"✅ UID {uid}: Turnstile successfully solved natively by MiniApp!")
        await context.close()
        return True
    except asyncio.TimeoutError:
        logger.info(f"ℹ️ UID {uid}: Native verify-human did not fire in 12s. Attempting programmatic render...")

    # Fallback: manually invoke Turnstile render on page
    solve_js = f"""
        async () => {{
            return new Promise((resolve) => {{
                let checkInt = setInterval(() => {{
                    if (window.turnstile && typeof window.turnstile.render === 'function') {{
                        clearInterval(checkInt);
                        try {{
                            let container = document.getElementById('cf-manual-slot');
                            if (!container) {{
                                container = document.createElement('div');
                                container.id = 'cf-manual-slot';
                                document.body.appendChild(container);
                            }}
                            window.turnstile.render(container, {{
                                sitekey: '{SITE_KEY}',
                                callback: function(tok) {{
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
                }}, 250);

                setTimeout(() => {{
                    clearInterval(checkInt);
                    resolve({{ success: false, error: 'timeout_15s' }});
                }}, 15000);
            }});
        }}
    """
    try:
        render_task = asyncio.create_task(page.evaluate(solve_js))
        # Look for iframe during programmatic render and click checkbox if needed
        for _ in range(6):
            if render_task.done():
                break
            try:
                ts_frame = page.frame_locator("iframe[src*='challenges.cloudflare.com']")
                checkbox = ts_frame.locator("input[type='checkbox'], #challenge-stage, .ctp-checkbox-label, body")
                if await checkbox.count() > 0:
                    logger.info(f"🖱️ Clicking programmatic Turnstile checkbox for UID {uid}...")
                    await checkbox.first.click(timeout=3000)
                    break
            except Exception:
                pass
            await asyncio.sleep(1.0)

        render_res = await render_task
        if render_res.get("success") and render_res.get("token"):
            tok = render_res["token"]
            logger.info(f"✅ UID {uid}: Programmatic Turnstile token acquired: {tok[:16]}...")
            ver_res = verify_human_token(m_init, tok)
            if ver_res.get("success"):
                logger.info(f"🎉 UID {uid}: Programmatic verify-human succeeded!")
                await context.close()
                return True
            else:
                logger.error(f"❌ UID {uid}: Programmatic verify-human rejected: {ver_res}")
    except Exception as e:
        logger.warning(f"UID {uid} evaluate note: {e}")

    await context.close()
    return False


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
    """Solves Turnstile for Victor's Company, logs in, binds referral, and saves humanPass."""
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
        viewport={"width": 412, "height": 915},
        locale="en-US",
        timezone_id="UTC"
    )
    page = await context.new_page()
    encoded_init = urllib.parse.quote(v_init)
    target_url = f"{VICTORS_ORIGIN}/#tgWebAppData={encoded_init}"

    await page.add_init_script(f"""
        Object.defineProperty(navigator, 'webdriver', {{ get: () => undefined }});
        window.Telegram = {{
            WebApp: {{
                initData: '{v_init}',
                initDataUnsafe: {{}},
                ready: () => {{}},
                expand: () => {{}},
                close: () => {{}}
            }}
        }};
    """)

    acquired_token = {"token": None}

    async def handle_request(request):
        try:
            if "auth/login" in request.url:
                post_data = request.post_data_json
                if post_data and post_data.get("turnstileToken"):
                    acquired_token["token"] = post_data["turnstileToken"]
        except Exception:
            pass

    page.on("request", handle_request)

    try:
        await page.goto(target_url, wait_until="load", timeout=25000)
    except Exception as e:
        logger.warning(f"[Victor's] UID {uid} navigation note: {e}")

    await asyncio.sleep(2.5)

    for _ in range(6):
        if acquired_token["token"]:
            break
        try:
            ts_frame = page.frame_locator("iframe[src*='challenges.cloudflare.com']")
            checkbox = ts_frame.locator("input[type='checkbox'], #challenge-stage, .ctp-checkbox-label, body")
            if await checkbox.count() > 0:
                logger.info(f"🖱️ [Victor's] Found Turnstile iframe for UID {uid}! Clicking...")
                await checkbox.first.click(timeout=3000)
                break
        except Exception:
            pass
        await asyncio.sleep(1.0)

    if not acquired_token["token"]:
        solve_js = f"""
            async () => {{
                return new Promise((resolve) => {{
                    let checkInt = setInterval(() => {{
                        if (window.turnstile && typeof window.turnstile.render === 'function') {{
                            clearInterval(checkInt);
                            try {{
                                let container = document.getElementById('cf-vic-slot');
                                if (!container) {{
                                    container = document.createElement('div');
                                    container.id = 'cf-vic-slot';
                                    document.body.appendChild(container);
                                }}
                                window.turnstile.render(container, {{
                                    sitekey: '{VICTORS_SITEKEY}',
                                    callback: function(tok) {{
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
                    }}, 250);
                    setTimeout(() => {{
                        clearInterval(checkInt);
                        resolve({{ success: false, error: 'Turnstile timeout' }});
                    }}, 12000);
                }});
            }}
        """
        try:
            res = await page.evaluate(solve_js)
            if res and res.get("success") and res.get("token"):
                acquired_token["token"] = res["token"]
        except Exception as e:
            logger.warning(f"[Victor's] UID {uid} manual solve error: {e}")

    await context.close()

    if acquired_token["token"]:
        logger.info(f"✅ [Victor's] UID {uid}: Turnstile solved! Logging in...")
        login_p = {
            "turnstileToken": acquired_token["token"]
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
                save_victors_pass_to_upstash(uid, str(hp))
                logger.info(f"🎉 [Victor's] UID {uid}: Successfully obtained humanPass: {str(hp)[:12]}... (Saved to Redis)")
                return True
    return False


async def run_mrg_auto_solver():
    """Main workflow: audits all 18 accounts, solves needed challenges, and auto-claims."""
    logger.info("====================================================================")
    logger.info("🚀 Starting 100% Cloud MRG Auto-Farming & Turnstile Solver Cycle")
    logger.info("====================================================================")

    accounts_data = []
    accounts_needing_solver = []
    victors_accounts = []

    # 1. Fetch tokens and inspect account states
    for idx, uid in enumerate(FLEET_UIDS, 1):
        tok_dict = get_token_from_upstash(uid)
        mrg_init = tok_dict.get("mrg_init_data")
        vic_init = tok_dict.get("victors_init_data")
        if vic_init:
            victors_accounts.append({
                "uid": uid,
                "init_data": vic_init
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
    logger.info(f"📊 Audit Summary: {len(accounts_data)} accounts connected. {needed_count} accounts require MRG Turnstile. {len(victors_accounts)} accounts found with Victor's Company.")

    # 2. Launch stealth browser and process accounts needing verification
    solved_count = 0
    total_claimed_mrg = 0.0
    victors_solved = 0

    if needed_count > 0 or len(victors_accounts) > 0:
        # Import patchright (or fallback to playwright)
        try:
            from patchright.async_api import async_playwright
            logger.info("🛡️ Using Patchright stealth browser engine.")
        except ImportError:
            from playwright.async_api import async_playwright
            logger.info("🌐 Using Playwright browser engine.")

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

            # A. Solve MRG passes
            for acc in accounts_needing_solver:
                uid = acc["uid"]
                m_init = acc["init_data"]
                success = await solve_turnstile_for_account(browser, acc)
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

                await asyncio.sleep(1.5)

            # B. Solve Victor's Company passes
            for v_acc in victors_accounts:
                v_uid = v_acc["uid"]
                v_init = v_acc["init_data"]
                try:
                    v_res = await solve_victors_turnstile(browser, v_uid, v_init, is_master=(v_uid == 6727787768))
                    if v_res:
                        victors_solved += 1
                except Exception as ve:
                    logger.warning(f"Victor's solve exception for UID {v_uid}: {ve}")
                await asyncio.sleep(1.5)

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
        f"🚀 <b>MRG & Victor's Cloud Turnstile Engine Report</b>\n\n"
        f"• <b>Total Fleet Accounts:</b> 18\n"
        f"• <b>MRG Pass Solved:</b> {solved_count}/{needed_count}\n"
        f"• <b>Victor's Pass Solved:</b> {victors_solved}/{len(victors_accounts)}\n"
        f"• <b>Total MRG Harvested:</b> {total_claimed_mrg:.2f} MRG\n"
        f"• <b>Execution Time:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
        f"⚡ <i>100% Cloud Execution. Zero phone load.</i>"
    )
    logger.info(f"📢 Telemetry: MRG Solved {solved_count}/{needed_count}, Victor's Solved {victors_solved}, Claimed {total_claimed_mrg:.2f} MRG.")
    send_tg_alert(report_msg)


if __name__ == "__main__":
    asyncio.run(run_mrg_auto_solver())
