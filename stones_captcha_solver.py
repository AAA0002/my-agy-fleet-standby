#!/usr/bin/env python3
"""
stones_captcha_solver.py
Autonomous Captcha Solver & Auto-Withdrawal Engine for Stones Miners.

Handles the 2026-09-21 Stones Miners update:
1. Replaces the old 4-ad gate with the human verification code (captcha) gate.
2. Isolates the 5 distinct character colors from the 210x68 PNG image.
3. Classifies each character using normalized cosine template matching + Tesseract fallback.
4. Dynamically learns new character templates whenever a verification succeeds.
5. Obtains the one-time 'captcha_ticket' and submits the withdrawal to Arbitrum One.
"""

import os
import io
import math
import json
import base64
import asyncio
import logging
from typing import Optional, Tuple, Dict, List
from collections import Counter
from PIL import Image, ImageFilter
import aiohttp

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

logger = logging.getLogger("StonesCaptchaSolver")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_FILE = os.path.join(BASE_DIR, "stones_captcha_templates.json")

# In-memory template cache
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


def save_templates(templates: Dict[str, List[List[float]]]):
    global _TEMPLATES_CACHE
    _TEMPLATES_CACHE = templates
    try:
        with open(TEMPLATES_FILE, "w", encoding="utf-8") as f:
            json.dump(templates, f)
    except Exception as e:
        logger.error(f"Error saving captcha templates: {e}")


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


def solve_stones_captcha(img_bytes: bytes) -> Tuple[str, float]:
    """
    Solves Stones Miners captcha from raw image bytes.
    Returns (predicted_5_char_string, average_confidence).
    """
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    char_data = extract_character_vectors(img)
    if len(char_data) != 5:
        # Fallback: attempt full-image OCR if character segmentation was irregular
        return _fallback_full_ocr(img), 0.5

    templates = load_templates()
    predicted_chars = []
    confidences = []

    for vec, c_img in char_data:
        best_char = "?"
        best_score = -1.0

        for ch, t_list in templates.items():
            for t_arr in t_list:
                sim = cosine_sim(vec, t_arr)
                if sim > best_score:
                    best_score = sim
                    best_char = ch

        # If similarity is lower than 0.82 and Tesseract is available, try character OCR
        if best_score < 0.82 and HAS_TESSERACT:
            tess_char = _ocr_single_char(c_img)
            if tess_char and tess_char.isalnum():
                best_char = tess_char.upper()
                best_score = 0.85

        predicted_chars.append(best_char)
        confidences.append(max(0.0, best_score))

    pred_str = "".join(predicted_chars)
    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
    return pred_str, avg_conf


def _ocr_single_char(c_img: Image.Image) -> str:
    """Runs single-character Tesseract OCR on a cropped character canvas."""
    if not HAS_TESSERACT:
        return ""
    cw, ch = c_img.size
    canvas = Image.new("L", (cw + 30, ch + 30), 255)
    inv_c = Image.eval(c_img, lambda p: 0 if p > 100 else 255)
    canvas.paste(inv_c, (15, 15))
    for psm in [10, 8]:
        for scale in [2, 3]:
            try:
                s_img = canvas.resize((canvas.width * scale, canvas.height * scale), Image.Resampling.LANCZOS)
                txt = pytesseract.image_to_string(
                    s_img,
                    config=f"--psm {psm} -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
                ).strip()
                cleaned = "".join(c for c in txt.upper() if c.isalnum())
                if cleaned:
                    return cleaned[:1]
            except Exception:
                pass
    return ""


def _fallback_full_ocr(img: Image.Image) -> str:
    """Full-image OCR fallback."""
    if not HAS_TESSERACT:
        return ""
    try:
        w, h = img.size
        gray = img.convert("L")
        scaled = gray.resize((w * 3, h * 3), Image.Resampling.NEAREST)
        txt = pytesseract.image_to_string(
            scaled,
            config="--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        ).strip()
        cleaned = "".join(c for c in txt.upper() if c.isalnum())
        return cleaned[:5]
    except Exception:
        return ""


def learn_new_captcha(img_bytes: bytes, verified_code: str):
    """Adds newly verified character vectors to the template library."""
    if len(verified_code) != 5:
        return
    try:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        char_data = extract_character_vectors(img)
        if len(char_data) == 5:
            templates = load_templates()
            updated = False
            for ch, (vec, _) in zip(verified_code, char_data):
                # Keep up to 3 diverse templates per character
                t_list = templates.setdefault(ch, [])
                if len(t_list) < 3:
                    t_list.append(vec)
                    updated = True
                else:
                    # Check if this vector is significantly different from existing ones
                    min_sim = min(cosine_sim(vec, existing) for existing in t_list)
                    if min_sim < 0.92:
                        t_list.append(vec)
                        updated = True
            if updated:
                save_templates(templates)
                logger.info(f"Learned new character templates for: {verified_code}")
    except Exception as e:
        logger.debug(f"Error learning captcha: {e}")


async def execute_stones_withdrawal_with_captcha(
    session: aiohttp.ClientSession,
    base_url: str,
    headers: dict,
    init_data: str,
    amount: int,
    wallet: str,
    proxy: Optional[str] = None
) -> Tuple[bool, dict]:
    """
    Executes complete Stones Miners withdrawal with automated captcha verification:
    1. Precheck
    2. Captcha Issue -> Solve -> Verify -> Get Ticket
    3. Submit /api/withdraw with captcha_ticket
    """
    req_headers = dict(headers)
    req_headers["Content-Type"] = "application/json"

    # Step 1: Precheck
    try:
        async with session.post(
            f"{base_url}/api/wd/ad/precheck",
            json={"initData": init_data, "amount": amount, "wallet": wallet, "currency": "stones"},
            headers=req_headers,
            timeout=aiohttp.ClientTimeout(total=10, connect=5),
            proxy=proxy
        ) as pr:
            pd = await pr.json()
            if not pd.get("ok") and not pd.get("success"):
                return False, {"error": "precheck_failed", "details": pd}
    except Exception as pe:
        return False, {"error": f"precheck_exception: {pe}"}

    # Step 1b: 4 Video Ads Gate (if required by server)
    if pd.get("need_ad"):
        boarded_ads = pd.get("boarded", 0)
        req_ads = pd.get("required", 4)
        ad_attempts = 0
        while boarded_ads < req_ads and ad_attempts < 6:
            ad_attempts += 1
            logger.info(f"[Stones Withdrawal] 📺 Completing video ad verification ({boarded_ads}/{req_ads} boarded, attempt {ad_attempts})...")
            try:
                async with session.post(
                    f"{base_url}/api/wd/ad/challenge",
                    json={"initData": init_data},
                    headers=req_headers,
                    timeout=aiohttp.ClientTimeout(total=10, connect=5),
                    proxy=proxy
                ) as ch_res:
                    if ch_res.status == 200:
                        ch_data = await ch_res.json()
                        cid = ch_data.get("challenge", {}).get("challenge_id")
                        if cid:
                            await session.post(f"{base_url}/api/ad/beat", json={"initData": init_data, "scope": "wd", "challenge_id": cid}, headers=req_headers, timeout=aiohttp.ClientTimeout(total=8, connect=5), proxy=proxy)
                            await asyncio.sleep(16.0)
                            await session.post(f"{base_url}/api/ad/beat", json={"initData": init_data, "scope": "wd", "challenge_id": cid}, headers=req_headers, timeout=aiohttp.ClientTimeout(total=8, connect=5), proxy=proxy)
                            await asyncio.sleep(0.5)
                            async with session.post(
                                f"{base_url}/api/wd/ad/confirm",
                                json={"initData": init_data, "challenge_id": cid},
                                headers=req_headers,
                                timeout=aiohttp.ClientTimeout(total=10, connect=5),
                                proxy=proxy
                            ) as cf_res:
                                cf_data = await cf_res.json()
                                boarded_ads = cf_data.get("verified", boarded_ads + 1)
                                logger.info(f"[Stones Withdrawal] 📺 Ad verified: {cf_data} ({boarded_ads}/{req_ads})")
            except Exception as ade:
                logger.debug(f"[Stones Withdrawal] Ad challenge error: {ade}")
                break
            await asyncio.sleep(2.0)

    # Step 2: Captcha Verification Loop (up to 12 attempts)
    captcha_ticket = None
    for attempt in range(1, 13):
        try:
            async with session.post(
                f"{base_url}/api/wd/captcha/issue",
                json={"initData": init_data},
                headers=req_headers,
                timeout=aiohttp.ClientTimeout(total=10, connect=5),
                proxy=proxy
            ) as ir:
                issue_data = await ir.json()

            if issue_data.get("enabled") is False:
                # Captcha is turned off on server -> proceed directly
                break

            if not issue_data.get("ok") or not issue_data.get("image"):
                await asyncio.sleep(1.5)
                continue

            cid = issue_data.get("captcha_id")
            raw_img = issue_data.get("image", "")
            img_b64 = raw_img.split(",", 1)[1] if "," in raw_img else raw_img
            img_bytes = base64.b64decode(img_b64)

            pred_code, confidence = solve_stones_captcha(img_bytes)
            logger.info(f"[Stones Captcha] Attempt {attempt}: Solved #{cid} -> '{pred_code}' (conf: {confidence:.2f})")

            if len(pred_code) == 5 and "?" not in pred_code:
                async with session.post(
                    f"{base_url}/api/wd/captcha/verify",
                    json={"initData": init_data, "captcha_id": cid, "answer": pred_code},
                    headers=req_headers,
                    timeout=aiohttp.ClientTimeout(total=10, connect=5),
                    proxy=proxy
                ) as vr:
                    vd = await vr.json()
                    if vd.get("ok") and vd.get("ticket"):
                        captcha_ticket = vd["ticket"]
                        logger.info(f"[Stones Captcha] ✅ Ticket Acquired: {captcha_ticket[:16]}...")
                        learn_new_captcha(img_bytes, pred_code)
                        break
                    else:
                        logger.debug(f"[Stones Captcha] Attempt {attempt} rejected: {vd.get('info', vd)}")

            await asyncio.sleep(1.5)
        except Exception as ce:
            logger.debug(f"[Stones Captcha] Attempt {attempt} error: {ce}")
            await asyncio.sleep(1.5)

    # Step 3: Submit Withdrawal
    wd_payload = {
        "initData": init_data,
        "amount": amount,
        "wallet": wallet,
        "currency": "stones"
    }
    if captcha_ticket:
        wd_payload["captcha_ticket"] = captcha_ticket

    try:
        async with session.post(
            f"{base_url}/api/withdraw",
            json=wd_payload,
            headers=req_headers,
            timeout=aiohttp.ClientTimeout(total=12, connect=5),
            proxy=proxy
        ) as wr:
            wd_res = await wr.json()
            ok = wd_res.get("ok") or wd_res.get("success") or False
            return ok, wd_res
    except Exception as we:
        return False, {"error": f"withdraw_exception: {we}"}
