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
import math
import json
import base64
import asyncio
import logging
from typing import Tuple, List, Dict, Optional
from collections import Counter
from PIL import Image, ImageEnhance
import aiohttp
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

logger = logging.getLogger("StonesCaptchaSolver")

GEMINI_API_KEYS = [k.strip() for k in os.getenv("GEMINI_API_KEYS", "").split(",") if k.strip()]
TEMPLATES_FILE = os.path.join(BASE_DIR, "stones_captcha_templates.json")
_TEMPLATES_CACHE: Optional[Dict[str, List[List[float]]]] = None


def load_templates() -> Dict[str, List[List[float]]]:
    global _TEMPLATES_CACHE
    if _TEMPLATES_CACHE is not None:
        return _TEMPLATES_CACHE
    if os.path.exists(TEMPLATES_FILE):
        try:
            with open(TEMPLATES_FILE, "r", encoding="utf-8") as f:
                _TEMPLATES_CACHE = json.load(f)
                return _TEMPLATES_CACHE
        except Exception as e:
            logger.error(f"Error loading captcha templates: {e}")
    _TEMPLATES_CACHE = {}
    return _TEMPLATES_CACHE


def dot(v1: List[float], v2: List[float]) -> float:
    return sum(a * b for a, b in zip(v1, v2))


def norm(v: List[float]) -> float:
    return math.sqrt(sum(a * a for a in v)) + 1e-6


def cosine_sim(v1: List[float], v2: List[float]) -> float:
    return dot(v1, v2) / (norm(v1) * norm(v2))


def extract_character_vectors(img: Image.Image) -> List[Tuple[List[float], Image.Image]]:
    """
    Extracts the 5 characters by unique solid color,
    normalizes them to 20x25, and returns (vector, cropped_canvas) tuples.
    """
    w, h = img.size
    colors = Counter([img.getpixel((x, y)) for x in range(w) for y in range(h)])
    # Character colors: dark and frequent (> 120 pixels, average brightness < 110)
    char_colors = [c for c, cnt in colors.most_common(15) if cnt > 120 and (c[0] + c[1] + c[2]) / 3 < 110]

    chars = []
    for col in char_colors:
        xs = [x for x in range(w) for y in range(h) if img.getpixel((x, y)) == col]
        ys = [y for x in range(w) for y in range(h) if img.getpixel((x, y)) == col]
        if not xs or not ys:
            continue
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        chars.append((min_x, max_x, min_y, max_y, col))

    # Sort left to right
    chars.sort(key=lambda t: t[0])

    char_data = []
    for min_x, max_x, min_y, max_y, col in chars[:5]:
        cw = max_x - min_x + 1
        ch = max_y - min_y + 1
        c_img = Image.new("L", (cw, ch), 0)
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                if img.getpixel((x, y)) == col:
                    c_img.putpixel((x - min_x, y - min_y), 255)

        norm_img = c_img.resize((20, 25), Image.Resampling.BILINEAR)
        vec = [round(norm_img.getpixel((px, py)) / 255.0, 3) for px in range(20) for py in range(25)]
        char_data.append((vec, c_img))

    return char_data


def solve_stones_captcha_templates(raw_b64: str) -> Tuple[str, float]:
    """Offline template matching solver for Stones Miner captcha."""
    try:
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",")[-1]
        img_bytes = base64.b64decode(raw_b64)
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        char_data = extract_character_vectors(img)
        if len(char_data) != 5:
            return "", 0.0

        templates = load_templates()
        if not templates:
            return "", 0.0

        predicted_chars = []
        confidences = []

        for vec, _ in char_data:
            best_char = "?"
            best_score = -1.0
            for ch, t_list in templates.items():
                for t_arr in t_list:
                    sim = cosine_sim(vec, t_arr)
                    if sim > best_score:
                        best_score = sim
                        best_char = ch

            predicted_chars.append(best_char)
            confidences.append(max(0.0, best_score))

        pred_str = "".join(predicted_chars)
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
        if "?" in pred_str or len(pred_str) != 5:
            return "", avg_conf
        return pred_str, avg_conf
    except Exception as e:
        logger.debug(f"[Stones Captcha] Template matching error: {e}")
        return "", 0.0


def learn_new_captcha(raw_b64: str, verified_code: str):
    """Adds newly verified character vectors to the template library."""
    if len(verified_code) != 5:
        return
    try:
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",")[-1]
        img_bytes = base64.b64decode(raw_b64)
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        char_data = extract_character_vectors(img)
        if len(char_data) == 5:
            templates = load_templates()
            updated = False
            for ch, (vec, _) in zip(verified_code, char_data):
                t_list = templates.setdefault(ch, [])
                if len(t_list) < 15:
                    t_list.append(vec)
                    updated = True
                else:
                    min_sim = min(cosine_sim(vec, existing) for existing in t_list)
                    if min_sim < 0.92:
                        t_list.append(vec)
                        updated = True
            if updated:
                with open(TEMPLATES_FILE, "w", encoding="utf-8") as f:
                    json.dump(templates, f)
                logger.info(f"[Stones Captcha] Dynamically learned new character templates for: {verified_code}")
    except Exception as e:
        logger.debug(f"[Stones Captcha] Error learning captcha: {e}")


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

    # Rotate through active Gemini Vision models
    models = ["gemini-flash-latest", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-flash-lite-latest"]
    keys = list(GEMINI_API_KEYS)

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as ai_session:
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
                                    if clean and len(clean) == length:
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
                                if not cf_d.get("ok"):
                                    logger.warning(f"[Stones Withdrawal] Ad confirm note: {cf_d.get('info')}")
                                    break
                            else:
                                break
                        # Poll proof status
                        async with session.post(
                            f"{base_url}/api/wd/ad/proof",
                            json={"initData": init_data, "challenge_id": cid},
                            headers=req_headers,
                            proxy=proxy,
                            timeout=aiohttp.ClientTimeout(total=8)
                        ) as pfr:
                            if pfr.status == 200:
                                pfd = await pfr.json()
                                if pfd.get("state") == "ok":
                                    cur_boarded = pfd.get("boarded", cur_boarded + 1)
                                else:
                                    cur_boarded = pfd.get("boarded", cur_boarded)
                                    break
                            else:
                                break
                        await asyncio.sleep(1.0)
                    if cur_boarded < req_ads:
                        return False, f"🎬 Watch all {req_ads} ads fully to submit this withdrawal (confirmed: {cur_boarded}/{req_ads})"
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

                # Step 2: Solve with AI Vision, fallback to offline template matching
                proc_b64 = preprocess_captcha_image(img_raw)
                ans = await solve_captcha_with_ai(proc_b64, length=length)
                if not ans:
                    logger.info(f"[Stones Captcha] AI Vision busy/rate-limited. Falling back to offline template matching...")
                    ans, conf = solve_stones_captcha_templates(img_raw)
                    if ans:
                        logger.info(f"[Stones Captcha] Offline template solver matched: '{ans}' (confidence: {conf:.2f})")

                if not ans:
                    logger.warning(f"[Stones Captcha] All solvers failed to resolve image on attempt {attempt}")
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
                            try:
                                learn_new_captcha(img_raw, ans)
                            except Exception:
                                pass
                            break
                        else:
                            logger.warning(f"[Stones Captcha] Verification rejected: {vres.get('info', 'Unknown')}")
                            await asyncio.sleep(1.5)
        except Exception as e:
            err_desc = f"{type(e).__name__}: {e}" if str(e) else type(e).__name__
            logger.error(f"[Stones Captcha] Exception during captcha cycle: {err_desc}")
            if isinstance(e, (asyncio.TimeoutError, aiohttp.ClientConnectorError, aiohttp.ServerTimeoutError)):
                logger.warning(f"[Stones Captcha] Network/Origin timeout detected. Aborting captcha attempts.")
                break
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
        err_desc = f"{type(e).__name__}: {e}" if str(e) else type(e).__name__
        return False, err_desc
