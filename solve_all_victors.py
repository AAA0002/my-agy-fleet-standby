#!/usr/bin/env python3
"""
solve_all_victors.py
Dedicated 100% Cloud Turnstile Solver for Victor's Company (@VictorsCompanybot).
Runs in the cloud with Patchright Chromium stealth.
Bypasses Cloudflare Turnstile with hardware CDP mouse click on the native challenge frame.
Captures humanPass and syncs to Upstash Redis for 24 hours of autonomous cloud mining.
"""

import os
import sys
import json
import time
import shutil
import asyncio
import urllib.request
import urllib.parse
import logging
from patchright.async_api import async_playwright

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("victors_solver")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_file = os.path.join(BASE_DIR, ".env")
env = {}
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")

UPSTASH_URL = env.get("UPSTASH_REDIS_REST_URL") or "https://rich-emu-106119.upstash.io"
UPSTASH_TOKEN = env.get("UPSTASH_REDIS_REST_TOKEN") or ""

async def solve_single_account(browser, uid: str, name: str, v_init: str) -> bool:
    logger.info(f"🚀 [Victor's] Processing UID {uid} ({name})...")
    login_data = {}
    
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
        viewport={"width": 412, "height": 915},
        is_mobile=True,
        has_touch=True
    )
    page = await context.new_page()
    
    async def on_resp(r):
        if "/api/auth/login" in r.url:
            try:
                data = await r.json()
                login_data.update(data)
                logger.info(f"  [UID {uid}] Auth response: success={data.get('success')} pass={bool(data.get('humanPass'))}")
            except Exception:
                pass
                
    page.on("response", on_resp)
    encoded = urllib.parse.quote(v_init)
    target_url = f"https://app.victors.company/#tgWebAppData={encoded}&tgWebAppPlatform=android&tgWebAppVersion=8.0"
    
    try:
        await page.goto(target_url, timeout=30000, wait_until="domcontentloaded")
        await asyncio.sleep(4.0)
        
        iframe_el = page.locator('iframe[src*="challenges.cloudflare.com"]').first
        if await iframe_el.count() > 0:
            box = await iframe_el.bounding_box()
            if box:
                click_x = box["x"] + 32.0
                click_y = box["y"] + (box["height"] / 2.0)
                await page.mouse.move(click_x, click_y, steps=6)
                await asyncio.sleep(0.12)
                await page.mouse.down()
                await asyncio.sleep(0.12)
                await page.mouse.up()
                logger.info(f"  [UID {uid}] Clicked Turnstile at ({click_x:.1f}, {click_y:.1f}), waiting for solve...")
                for _ in range(12):
                    if login_data.get("humanPass"):
                        break
                    await asyncio.sleep(1.0)
    except Exception as e:
        logger.warning(f"  [UID {uid}] Navigation/click error: {e}")
    finally:
        await context.close()
        
    hpass = login_data.get("humanPass")
    if hpass:
        logger.info(f"  🎉 [UID {uid}] Solved Turnstile! humanPass: {hpass[:20]}...")
        save_req = urllib.request.Request(
            f"{UPSTASH_URL}/set/victors:pass:{uid}?ex=86400",
            data=hpass.encode(),
            headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}
        )
        try:
            with urllib.request.urlopen(save_req, timeout=5) as s_resp:
                pass
        except Exception as se:
            logger.warning(f"  [UID {uid}] Redis save note: {se}")
            
        # Execute immediate claims
        h = {
            "Content-Type": "application/json",
            "Authorization": f"tma {v_init}",
            "x-human-pass": str(hpass),
            "Origin": "https://app.victors.company",
            "Referer": "https://app.victors.company/"
        }
        for ep in ["/api/checkin", "/api/me/tutorial", "/api/referral/claim-bonus", "/api/mining/claim"]:
            try:
                r_claim = urllib.request.Request(f"https://server.victors.company{ep}", data=b"{}", headers=h)
                with urllib.request.urlopen(r_claim, timeout=6) as cr:
                    logger.info(f"  [UID {uid}] {ep} -> HTTP {cr.status}")
            except urllib.error.HTTPError as he:
                logger.info(f"  [UID {uid}] {ep} -> HTTP {he.code}")
            except Exception:
                pass
        return True
    else:
        logger.warning(f"  ⚠️ [UID {uid}] Turnstile did not yield humanPass.")
        return False

async def main():
    logger.info("🔍 Loading fleet tokens from Upstash Redis...")
    req = urllib.request.Request(
        f"{UPSTASH_URL}/get/fleet_miniapp_tokens",
        headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        tokens = json.loads(json.loads(resp.read().decode())["result"])
        
    # Check existing active passes to avoid redundant browser runs
    pipe_keys = [f"victors:pass:{uid}" for uid in tokens.keys()]
    pass_req = urllib.request.Request(
        f"{UPSTASH_URL}/mget/{'/'.join(pipe_keys)}",
        headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}
    )
    existing_passes = {}
    try:
        with urllib.request.urlopen(pass_req, timeout=10) as presp:
            raw_res = json.loads(presp.read().decode()).get("result") or []
            for uid, pval in zip(tokens.keys(), raw_res):
                if pval and pval not in ("null", "nil", "None", ""):
                    existing_passes[uid] = pval
    except Exception:
        pass
        
    logger.info(f"Found {len(existing_passes)} accounts already with active 24h passes.")
    
    # Filter candidates
    candidates = []
    for uid, acc in tokens.items():
        v_init = acc.get("victors_init_data")
        if not v_init:
            continue
        if uid in existing_passes:
            continue
        candidates.append((uid, acc.get("name") or "User", v_init))
        
    logger.info(f"Targeting {len(candidates)} accounts requiring Victor's Turnstile...")
    if not candidates:
        logger.info("✅ All accounts already solved and active!")
        return

    chrome_path = shutil.which("chromium") or "/usr/bin/chromium"
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=chrome_path,
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled"
            ]
        )
        
        solved_count = 0
        for uid, name, v_init in candidates:
            success = await solve_single_account(browser, uid, name, v_init)
            if success:
                solved_count += 1
            await asyncio.sleep(2.0)
            
        await browser.close()
        logger.info(f"🏁 Finished Victor's solver cycle: {solved_count}/{len(candidates)} successfully solved & claimed!")

if __name__ == "__main__":
    asyncio.run(main())
