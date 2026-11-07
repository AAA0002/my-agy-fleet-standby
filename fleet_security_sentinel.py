#!/usr/bin/env python3
"""
fleet_security_sentinel.py
=============================================================================
AAA AUTO FLEET DEVICE SECURITY SENTINEL & INTRUSION DETECTION ENGINE
=============================================================================
Protects the 23-account Telegram fleet against unauthorized session takeovers:
1. Real-time interception of Telegram Service Notifications (peer=777000).
2. Hardware whitelist filtering:
   - Whitelist: User's Samsung Galaxy A30 ("Samsung Galaxy A30", "SM-A305F", etc.)
   - Whitelist: Our Cloud Mission Workers (Render Node 3, Linux PC 64bit, Telethon)
3. Instant security alerting for ANY unknown/unauthorized device (iPhone, Chrome, unknown PC, overseas IP).
4. Direct MTProto session inspection (GetAuthorizationsRequest) & 1-tap termination (ResetAuthorizationRequest).
"""

import os
import sys
import re
import json
import time
import logging
import asyncio
import aiohttp
import urllib.request
from typing import Dict, Any, Optional, Tuple, List

logger = logging.getLogger("security_sentinel")

# Load environment configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_file = os.path.join(BASE_DIR, ".env")
env_vars = {}
if os.path.exists(env_file):
    try:
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:
        pass

REPORT_BOT_TOKEN = os.getenv("REPORT_BOT_TOKEN") or env_vars.get("REPORT_BOT_TOKEN") or os.getenv("ADMIN_BOT_TOKEN") or env_vars.get("ADMIN_BOT_TOKEN") or ""
REPORT_CHAT_ID = os.getenv("REPORT_CHAT_ID") or env_vars.get("REPORT_CHAT_ID") or "-1004453515167"
ADMIN_NOTIF_CHANNEL = os.getenv("ADMIN_NOTIF_CHANNEL") or env_vars.get("ADMIN_NOTIF_CHANNEL") or "-1004358687850"

# Debounce cache to prevent duplicate alerts for the same foreign login (IP + Device, 6h TTL)
_ALERT_DEBOUNCE = {}

# =============================================================================
# 1. HARDWARE WHITELIST DEFINITIONS
# =============================================================================

# User's primary mobile device: Samsung Galaxy A30 (SM-A305F / SM-A305G)
USER_DEVICE_PATTERNS = [
    r"samsung[\s_-]*galaxy[\s_-]*a30",
    r"samsung[\s_-]*a30",
    r"galaxy[\s_-]*a30",
    r"sm[\s_-]*a305",
    r"sm[\s_-]*a30",
    r"a305f",
    r"a305g",
    r"a305fn",
    r"a3050"
]

# Our Cloud Mission Workers (Render Oregon Node 3, headless cloud runners, Telethon, Termux)
CLOUD_MISSION_PATTERNS = [
    r"pc[\s_-]*64bit",
    r"linux",
    r"render",
    r"telethon",
    r"cloud[\s_-]*coordinator",
    r"aaa[\s_-]*fleet",
    r"ubuntu",
    r"debian",
    r"aaaserver",
    r"aaatelegram",
    r"aarch64"
]

def is_device_whitelisted(device_str: str, platform: str = "", system_version: str = "", ip: str = "") -> Tuple[bool, str]:
    """
    Evaluates whether a device is authorized under the zero-trust fleet policy.
    Returns: (is_whitelisted: bool, reason: str)
    """
    if not device_str and not platform:
        return (False, "Empty device identifier")

    combined = f"{device_str} {platform} {system_version}".lower().strip()

    # 1. Check User's Personal Phone: Samsung Galaxy A30
    for pat in USER_DEVICE_PATTERNS:
        if re.search(pat, combined, re.IGNORECASE):
            return (True, f"Authorized User Phone (Samsung Galaxy A30: '{device_str}')")

    # 2. Check Our Cloud Mission Workers (Render / Linux / Telethon MTProto Engine / Termux)
    for pat in CLOUD_MISSION_PATTERNS:
        if re.search(pat, combined, re.IGNORECASE):
            return (True, f"Authorized Cloud Mission Node ('{device_str}')")

    return (False, f"Unrecognized Foreign Device ('{device_str}')")


# =============================================================================
# 2. TELEGRAM SERVICE NOTIFICATION (777000) PARSER
# =============================================================================

def parse_service_notification(text: str) -> Optional[Dict[str, Any]]:
    """
    Parses Telegram official security messages (from peer 777000) for new login alerts.
    Filters out OTP login codes and promotional announcements.
    """
    if not text:
        return None

    lower = text.lower()

    # CRITICAL BUG FIX: Ignore Telegram Login Code / OTP messages
    # E.g. "Login code: 82034. Do not give this code to anyone... If you didn't request this code by trying to log in on another device, simply ignore this message."
    if "login code:" in lower or ("code:" in lower and "log in to your telegram account" in lower):
        logger.info("[Security Sentinel] Ignored Telegram login OTP code message.")
        return None

    # Ignore promotional/bonus messages or official notices without actual login device events
    if "unblocked" in lower or "bonus is waiting" in lower or "channel request" in lower:
        return None

    # A real login notification from Telegram DC requires a Device: line or explicit login notification statement
    dev_m = re.search(r"Device:\s*([^\n\r]+)", text, re.IGNORECASE)
    is_explicit_login = (
        "login to your account from a new device" in lower
        or "new login from a new device" in lower
        or "logged in to your telegram account from" in lower
    )

    if not dev_m and not is_explicit_login:
        # Not a device login event
        return None

    # Check if message is a login alert
    if dev_m or ("login" in lower and ("device" in lower or "location" in lower or "ip" in lower)):
        loc_m = re.search(r"Location:\s*([^\n\r]+)", text, re.IGNORECASE)
        ip_m = re.search(r"IP(?:\s*Address)?:\s*([0-9a-fA-F\.:]+)", text, re.IGNORECASE)
        time_m = re.search(r"(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}[^\n\r]*)", text)

        device_raw = dev_m.group(1).strip() if dev_m else "Unknown Device"
        location_raw = loc_m.group(1).strip() if loc_m else "Unknown Location"
        # Clean up location string if it contains embedded (IP: ...)
        location_clean = re.sub(r"\(?ip:.*", "", location_raw, flags=re.IGNORECASE).strip(" ,()")
        if not location_clean:
            location_clean = location_raw

        ip_raw = ip_m.group(1).strip() if ip_m else "Unknown IP"
        time_raw = time_m.group(1).strip() if time_m else "Just now"

        whitelisted, reason = is_device_whitelisted(device_raw)

        return {
            "is_login_notification": True,
            "device": device_raw,
            "location": location_clean,
            "ip": ip_raw,
            "time": time_raw,
            "whitelisted": whitelisted,
            "whitelist_reason": reason,
            "raw_text": text
        }

    return None


# =============================================================================
# 3. HIGH-PRIORITY INTRUSION ALERT DISPATCHER
# =============================================================================

def resolve_canonical_account_meta(target_idx: Any, target_name: str = "", target_phone: str = "") -> Tuple[Any, str, str]:
    """
    Resolves canonical (index, name, phone) from accounts.json to eliminate any
    index shifts or mismatched names/phones across sentinels and webhooks.
    """
    try:
        accs_path = os.path.join(BASE_DIR, "accounts.json")
        if os.path.exists(accs_path):
            with open(accs_path, "r") as f:
                accs = json.load(f)
            
            # 1. Match by UID
            tgt_uid_str = str(target_idx).strip()
            for i, a in enumerate(accs, 1):
                uid_str = str(a.get("user_id") or a.get("id") or "")
                if uid_str and uid_str == tgt_uid_str:
                    return (i, a.get("name", target_name), a.get("phone", target_phone))

            # 2. Match by Phone
            if target_phone:
                clean_target_p = re.sub(r"[^\d+]", "", str(target_phone))
                for i, a in enumerate(accs, 1):
                    p = a.get("phone", "")
                    if p and re.sub(r"[^\d+]", "", p) == clean_target_p:
                        return (i, a.get("name", target_name), p)

            # 3. Match by numeric index 1..len(accs)
            if isinstance(target_idx, int) and 1 <= target_idx <= len(accs):
                a = accs[target_idx - 1]
                return (target_idx, a.get("name", target_name), a.get("phone", target_phone))
            if isinstance(target_idx, str) and target_idx.isdigit() and 1 <= int(target_idx) <= len(accs):
                idx = int(target_idx)
                a = accs[idx - 1]
                return (idx, a.get("name", target_name), a.get("phone", target_phone))
    except Exception:
        pass
    return (target_idx, target_name, target_phone)


async def dispatch_security_alert(
    account_idx: Any,
    account_name: str,
    account_phone: str,
    info: Dict[str, Any],
    session_hash: Optional[int] = None
) -> bool:
    """
    Dispatches an urgent alert card to Admin Notification Channel and Master Vault.
    Guarantees 6-hour deduplication per device/IP.
    """
    # Guarantee 100% canonical ground-truth account name and phone number
    account_idx, account_name, account_phone = resolve_canonical_account_meta(account_idx, account_name, account_phone)

    if not REPORT_BOT_TOKEN:
        logger.warning("[Security Sentinel] REPORT_BOT_TOKEN missing, alert skipped.")
        return False

    dev = info.get("device", "Unknown Device")
    ip = info.get("ip", "Unknown IP")
    loc = info.get("location", "Unknown Location")
    t_str = info.get("time", "Just now")
    dedup_key = f"{account_idx}:{dev}:{ip}"

    now = time.time()
    last_sent = _ALERT_DEBOUNCE.get(dedup_key, 0)
    if now - last_sent < 21600:  # 6 hours
        logger.info(f"[Security Sentinel] Duplicate alert suppressed for {dedup_key}.")
        return False

    _ALERT_DEBOUNCE[dedup_key] = now

    alert_msg = (
        f"🚨 <b>UNAUTHORIZED DEVICE LOGIN DETECTED!</b> 🔴\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• <b>Account:</b> #{account_idx} <b>{account_name}</b> (<code>{account_phone}</code>)\n"
        f"• <b>Device:</b> <code>{dev}</code> ⚠️\n"
        f"• <b>Location:</b> 📍 {loc}\n"
        f"• <b>IP Address:</b> 🌐 <code>{ip}</code>\n"
        f"• <b>Timestamp:</b> ⏱️ {t_str}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ <b>Security Notice:</b>\n"
        f"This device is <b>NOT your Samsung Galaxy A30</b> and <b>NOT our Cloud System</b>!\n"
        f"An unauthorized device has accessed this Telegram account!\n\n"
        f"👉 Go to <b>Settings &gt; Devices &gt; Active Sessions</b> on your Samsung A30 to terminate it immediately."
    )

    targets = [t for t in [ADMIN_NOTIF_CHANNEL, REPORT_CHAT_ID] if t]
    success = False

    async with aiohttp.ClientSession() as session:
        for chat_id in targets:
            try:
                payload = {
                    "chat_id": chat_id,
                    "text": alert_msg,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True
                }
                async with session.post(
                    f"https://api.telegram.org/bot{REPORT_BOT_TOKEN}/sendMessage",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=4)
                ) as resp:
                    if resp.status == 200:
                        success = True
            except Exception as e:
                logger.error(f"[Security Sentinel] Failed to deliver alert to {chat_id}: {e}")

    return success


# =============================================================================
# 4. ACTIVE SESSION AUDIT & TERMINATION (MTProto GetAuthorizationsRequest)
# =============================================================================

async def audit_account_sessions(
    client,
    account_idx: int,
    account_name: str,
    account_phone: str,
    auto_terminate_unknown: bool = False
) -> Dict[str, Any]:
    """
    Connects to Telegram via MTProto and inspects all active sessions on the account.
    Detects foreign devices and optionally terminates them.
    """
    from telethon.tl.functions.account import GetAuthorizationsRequest, ResetAuthorizationRequest

    result = {
        "account_idx": account_idx,
        "name": account_name,
        "phone": account_phone,
        "total_sessions": 0,
        "current_session": None,
        "whitelisted_sessions": [],
        "unknown_sessions": [],
        "terminated_count": 0
    }

    try:
        auths_resp = await client(GetAuthorizationsRequest())
        authorizations = getattr(auths_resp, "authorizations", []) or []
        result["total_sessions"] = len(authorizations)

        for auth in authorizations:
            dev_model = getattr(auth, "device_model", "Unknown")
            platform = getattr(auth, "platform", "")
            sys_ver = getattr(auth, "system_version", "")
            app_name = getattr(auth, "app_name", "")
            app_ver = getattr(auth, "app_version", "")
            ip = getattr(auth, "ip", "Unknown")
            country = getattr(auth, "country", "Unknown")
            is_current = getattr(auth, "current", False)
            auth_hash = getattr(auth, "hash", 0)

            session_info = {
                "hash": auth_hash,
                "device_model": dev_model,
                "platform": platform,
                "system_version": sys_ver,
                "app": f"{app_name} {app_ver}".strip(),
                "ip": ip,
                "country": country,
                "is_current": is_current
            }

            if is_current:
                result["current_session"] = session_info
                result["whitelisted_sessions"].append(session_info)
                continue

            # Check if this session matches user's Samsung Galaxy A30 or Cloud system
            is_white, reason = is_device_whitelisted(dev_model, platform, sys_ver, ip)
            if is_white:
                session_info["whitelist_reason"] = reason
                result["whitelisted_sessions"].append(session_info)
            else:
                session_info["alert_reason"] = reason
                result["unknown_sessions"].append(session_info)

                # Send intrusion alert
                await dispatch_security_alert(
                    account_idx=account_idx,
                    account_name=account_name,
                    account_phone=account_phone,
                    info={
                        "device": f"{dev_model} ({platform} {sys_ver})",
                        "location": country,
                        "ip": ip,
                        "time": "Active session detected on Telegram DC"
                    },
                    session_hash=auth_hash
                )

                # Auto-terminate if requested
                if auto_terminate_unknown and auth_hash:
                    try:
                        await client(ResetAuthorizationRequest(hash=auth_hash))
                        result["terminated_count"] += 1
                        logger.warning(f"[Security Sentinel] ❌ Terminated foreign session #{auth_hash} ({dev_model}) on Account #{account_idx}!")
                    except Exception as e_term:
                        logger.error(f"[Security Sentinel] Failed to terminate session {auth_hash}: {e_term}")

    except Exception as e:
        logger.error(f"[Security Sentinel] Session audit error for #{account_idx}: {e}")
        result["error"] = str(e)

    return result
