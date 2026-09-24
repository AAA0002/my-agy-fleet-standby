#!/usr/bin/env python3
"""
stones_captcha_solver.py
Autonomous AI Captcha Solver & Withdrawal Submitter for Stones Miner (@stoneswithestand_bot).
Resolves dynamic image captchas via PIL contrast enhancement + Google Gemini Vision,
obtains verification ticket, and submits verified withdrawal to Arbitrum One.
"""

import os
import io
import re
import json
import base64
import asyncio
import logging
from typing import Tuple
from PIL import Image, ImageEnhance
import aiohttp
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

logger = logging.getLogger("StonesCaptchaSolver")

GEMINI_API_KEYS = [k.strip() for k in os.getenv("GEMINI_API_KEYS", "").split(",") if k.strip()]


def preprocess_captcha_image(raw_base64: str) -> str:
    """Preprocesses captcha image for maximum OCR / LLM vision accuracy."""
    if "," in raw_base64:
        raw_base64 = raw_base64.split(",")[-1]
    img = Image.open(io.BytesIO(base64.b64decode(raw_base64))).convert("L")
    img = img.resize((img.width * 2, img.height * 2), Image.Resampling.LANCZOS)
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


async def solve_captcha_with_ai(proc_b64: str, length: int = 5) -> str:
    """Queries Gemini Vision to read captcha characters."""
    prompt = (
        f"Look at this captcha image carefully. It contains exactly {length} alphanumeric characters "
        "(letters and numbers). Distinguish carefully between 0 and O, 1 and I, 5 and S, 8 and B. "
        f"Return ONLY the {length} characters in uppercase, strictly no spaces, no punctuation, no explanations."
    )
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/png", "data": proc_b64}}
            ]
        }]
    }

    # Rotate through keys
    models = ["gemini-3.5-flash-lite", "gemini-flash-latest", "gemini-2.5-flash-lite"]
    keys = list(GEMINI_API_KEYS)

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as ai_session:
        for model in models:
            for k in keys[:8]:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
                headers = {"Content-Type": "application/json", "X-goog-api-key": k}
                try:
                    async with ai_session.post(url, json=payload, headers=headers) as gr:
                        if gr.status == 200:
                            gdata = await gr.json()
                            candidates = gdata.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                if parts:
                                    raw_text = parts[0].get("text", "")
                                    clean = re.sub(r"[^a-zA-Z0-9]", "", raw_text).upper().strip()
                                    if clean:
                                        return clean
                except Exception:
                    continue
    return ""


async def execute_stones_withdrawal_with_captcha(
    session: aiohttp.ClientSession,
    base_url: str,
    headers: dict,
    init_data: str,
    amount: int,
    wallet: str,
    proxy: str = None
) -> Tuple[bool, str]:
    """
    Executes a complete Stones Miner auto-withdrawal:
    1. Checks captcha gate (/api/wd/captcha/issue).
    2. If required, solves dynamic image challenge and obtains verification ticket.
    3. Submits withdrawal to /api/withdraw with ticket.
    """
    req_headers = dict(headers)
    req_headers["Content-Type"] = "application/json"

    # Step 0: Pre-check withdrawal ad boarding requirements
    try:
        async with session.post(
            f"{base_url}/api/wd/ad/precheck",
            json={"initData": init_data, "amount": amount, "wallet": wallet, "currency": "stones"},
            headers=req_headers,
            proxy=proxy,
            timeout=aiohttp.ClientTimeout(total=10)
        ) as pcr:
            if pcr.status == 200:
                pcd = await pcr.json()
                if pcd.get("need_ad"):
                    req_ads = pcd.get("required", 3)
                    cur_boarded = pcd.get("boarded", 0)
                    while cur_boarded < req_ads:
                        logger.info(f"[Stones Withdrawal] Onboarding withdrawal ad ({cur_boarded + 1}/{req_ads})...")
                        async with session.post(
                            f"{base_url}/api/wd/ad/challenge",
                            json={"initData": init_data},
                            headers=req_headers,
                            proxy=proxy,
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as chr:
                            if chr.status != 200:
                                break
                            ch_data = await chr.json()
                            cid = ch_data.get("challenge", {}).get("challenge_id")
                        if not cid:
                            break
                        # Heartbeat 1
                        await session.post(
                            f"{base_url}/api/ad/beat",
                            json={"initData": init_data, "scope": "wd", "challenge_id": cid},
                            headers=req_headers,
                            proxy=proxy,
                            timeout=aiohttp.ClientTimeout(total=8)
                        )
                        # Simulate rewarded video duration
                        await asyncio.sleep(16.0)
                        # Heartbeat 2
                        await session.post(
                            f"{base_url}/api/ad/beat",
                            json={"initData": init_data, "scope": "wd", "challenge_id": cid},
                            headers=req_headers,
                            proxy=proxy,
                            timeout=aiohttp.ClientTimeout(total=8)
                        )
                        await asyncio.sleep(0.5)
                        # Confirm ad view
                        async with session.post(
                            f"{base_url}/api/wd/ad/confirm",
                            json={"initData": init_data, "challenge_id": cid},
                            headers=req_headers,
                            proxy=proxy,
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as cfr:
                            if cfr.status == 200:
                                cf_d = await cfr.json()
                                if cf_d.get("ok"):
                                    cur_boarded += 1
                                else:
                                    logger.warning(f"[Stones Withdrawal] Ad confirm note: {cf_d.get('info')}")
                                    break
                            else:
                                break
                        await asyncio.sleep(1.0)
    except Exception as ade:
        logger.debug(f"[Stones Withdrawal] Precheck/ad onboarding exception: {ade}")

    # Step 1: Issue captcha or check if enabled
    ticket = None
    max_attempts = 3

    for attempt in range(1, max_attempts + 1):
        try:
            async with session.post(
                f"{base_url}/api/wd/captcha/issue",
                json={"initData": init_data},
                headers=req_headers,
                proxy=proxy,
                timeout=aiohttp.ClientTimeout(total=12)
            ) as ir:
                if ir.status != 200:
                    logger.warning(f"[Stones Captcha] Issue returned status {ir.status}")
                    break

                ires = await ir.json()
                if not ires.get("ok"):
                    logger.warning(f"[Stones Captcha] Issue failed: {ires}")
                    break

                # If captcha is disabled server-side, proceed immediately
                if ires.get("enabled") is False:
                    ticket = None
                    break

                cid = ires.get("captcha_id")
                img_raw = ires.get("image", "")
                length = ires.get("length", 5)

                if not img_raw or not cid:
                    logger.warning(f"[Stones Captcha] Incomplete captcha payload: {ires}")
                    break

                # Step 2: Solve with AI Vision
                proc_b64 = preprocess_captcha_image(img_raw)
                ans = await solve_captcha_with_ai(proc_b64, length=length)
                if not ans:
                    logger.warning(f"[Stones Captcha] AI failed to solve image on attempt {attempt}")
                    await asyncio.sleep(1.0)
                    continue

                logger.info(f"[Stones Captcha] Solved code: '{ans}' (attempt {attempt}/{max_attempts})")

                # Step 3: Verify answer
                async with session.post(
                    f"{base_url}/api/wd/captcha/verify",
                    json={"initData": init_data, "captcha_id": cid, "answer": ans},
                    headers=req_headers,
                    proxy=proxy,
                    timeout=aiohttp.ClientTimeout(total=12)
                ) as vr:
                    if vr.status == 200:
                        vres = await vr.json()
                        if vres.get("ok") and vres.get("ticket"):
                            ticket = vres.get("ticket")
                            logger.info(f"[Stones Captcha] Verification passed! Ticket: {ticket[:8]}...")
                            break
                        else:
                            logger.warning(f"[Stones Captcha] Verification rejected: {vres.get('info', 'Unknown')}")
                            await asyncio.sleep(1.5)
        except Exception as e:
            logger.error(f"[Stones Captcha] Exception during captcha cycle: {e}")
            await asyncio.sleep(1.5)

    # Step 4: Submit the actual withdrawal
    withdraw_payload = {
        "initData": init_data,
        "amount": amount,
        "wallet": wallet,
        "currency": "stones"
    }
    if ticket:
        withdraw_payload["ticket"] = ticket
        withdraw_payload["captcha_ticket"] = ticket

    try:
        async with session.post(
            f"{base_url}/api/withdraw",
            json=withdraw_payload,
            headers=req_headers,
            proxy=proxy,
            timeout=aiohttp.ClientTimeout(total=15)
        ) as wr:
            try:
                wres = await wr.json()
            except Exception:
                wres = {"info": await wr.text()}
            if wr.status == 200 and wres.get("ok"):
                msg = wres.get("info") or f"Successfully withdrawn {amount} STONES"
                return True, msg
            else:
                err_msg = wres.get("info") or wres.get("error") or f"HTTP {wr.status}: {wres}"
                return False, err_msg
    except Exception as e:
        return False, str(e)
