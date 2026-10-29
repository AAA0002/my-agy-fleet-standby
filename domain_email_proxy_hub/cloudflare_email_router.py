#!/usr/bin/env python3
"""
Cloudflare Email Router
Manages Cloudflare Email Routing for agy.dpdns.org.
Pre-configures rules, destination mailboxes, and automated verification.
"""

import os
import re
import imaplib
import email
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

CF_TOKEN = os.getenv("CF_ZONE_EMAIL_TOKEN") or os.getenv("CF_API_TOKEN_USERBOT")
ZONE_ID = "f668c3573777bb05a95eba5dc01ada32"  # agy.dpdns.org
ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID_USERBOT")
DESTINATION_EMAIL = os.getenv("GMAIL_ADDRESS", "aaa.support.a@gmail.com")
GMAIL_PASS = os.getenv("GMAIL_APP_PASSWORD")

def get_cf_headers():
    if not CF_TOKEN:
        raise ValueError("Missing CF_ZONE_EMAIL_TOKEN in .env")
    return {
        "Authorization": f"Bearer {CF_TOKEN}",
        "Content-Type": "application/json"
    }

def check_destination_address_status():
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/email/routing/addresses"
    r = requests.get(url, headers=get_cf_headers())
    if r.status_code != 200:
        print(f"Error fetching destination addresses: {r.status_code} {r.text}")
        return None
    addresses = r.json().get("result", [])
    for addr in addresses:
        if addr.get("email") == DESTINATION_EMAIL:
            return addr
    return None

def check_gmail_for_verification():
    """Checks Gmail inbox via IMAP for Cloudflare's verification email and extracts token."""
    if not DESTINATION_EMAIL or not GMAIL_PASS:
        print("Missing GMAIL_ADDRESS or GMAIL_APP_PASSWORD in .env")
        return None
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(DESTINATION_EMAIL, GMAIL_PASS)
        mail.select("inbox")
        status, messages = mail.search(None, '(FROM "cloudflare")')
        msg_ids = messages[0].split()
        if not msg_ids:
            mail.logout()
            return None
        
        # Check latest Cloudflare message
        _, data = mail.fetch(msg_ids[-1], "(RFC822)")
        msg = email.message_from_bytes(data[0][1])
        body = ""
        for part in msg.walk():
            if part.get_content_type() in ["text/plain", "text/html"]:
                p = part.get_payload(decode=True)
                if p:
                    body += p.decode("utf-8", errors="ignore")
        mail.logout()
        
        urls = re.findall(r'https://dash\.cloudflare\.com/email_fwdr/verify[^\s\"\'<>]+', body)
        return urls[0].replace("&amp;", "&") if urls else None
    except Exception as e:
        print(f"IMAP Error: {e}")
        return None

def get_routing_rules():
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/email/routing/rules"
    r = requests.get(url, headers=get_cf_headers())
    if r.status_code != 200:
        return []
    return r.json().get("result", [])

def enable_catch_all_rule():
    rules = get_routing_rules()
    catch_all = None
    for rule in rules:
        for m in rule.get("matchers", []):
            if m.get("type") == "all":
                catch_all = rule
                break
    if not catch_all:
        print("No catch-all rule found.")
        return False
        
    rule_id = catch_all.get("id")
    payload = {
        "name": "Catch-all forward to Gmail",
        "matchers": [{"type": "all"}],
        "actions": [{"type": "forward", "value": [DESTINATION_EMAIL]}],
        "enabled": True,
        "priority": 0
    }
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/email/routing/rules/{rule_id}"
    r = requests.put(url, headers=get_cf_headers(), json=payload)
    print(f"Update Catch-all Rule status: {r.status_code}")
    if r.status_code == 200:
        print("  🎉 Catch-all rule is now ACTIVE and forwarding to", DESTINATION_EMAIL)
        return True
    else:
        print(f"  Note: {r.text}")
        return False

if __name__ == "__main__":
    print(f"=== Cloudflare Email Router Status for agy.dpdns.org ===")
    addr = check_destination_address_status()
    if addr:
        print(f"Destination Email: {addr.get('email')} -> Status: {addr.get('status')}")
    else:
        print(f"Destination Email {DESTINATION_EMAIL} not yet registered.")
        
    v_url = check_gmail_for_verification()
    if v_url:
        print(f"\nLatest Verification URL from Gmail:\n{v_url}")
        
    enable_catch_all_rule()
