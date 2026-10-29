#!/usr/bin/env python3
"""
Webshare Proxy Harvester & Account Expander
Leverages unlimited custom catch-all email aliases from @agy.dpdns.org
to automate Webshare free proxy registrations and expand the fleet proxy pool.
"""

import os
import re
import imaplib
import email
import secrets
import string
import requests
from dotenv import load_dotenv

local_env = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
parent_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(local_env):
    load_dotenv(local_env)
if os.path.exists(parent_env):
    load_dotenv(parent_env)

DOMAIN = "agy.dpdns.org"
GMAIL_USER = os.getenv("GMAIL_ADDRESS", "aaa.support.a@gmail.com")
GMAIL_PASS = os.getenv("GMAIL_APP_PASSWORD")

def generate_random_alias(prefix="fleet"):
    rand_str = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(6))
    return f"{prefix}_{rand_str}@{DOMAIN}"

def generate_strong_password():
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(chars) for _ in range(16))

def fetch_latest_webshare_verification_email():
    """Checks Gmail inbox via IMAP for incoming Webshare verification link."""
    if not GMAIL_USER or not GMAIL_PASS:
        return None
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_PASS)
        mail.select("inbox")
        status, messages = mail.search(None, '(FROM "webshare")')
        msg_ids = messages[0].split()
        if not msg_ids:
            mail.logout()
            return None
        
        _, data = mail.fetch(msg_ids[-1], "(RFC822)")
        msg = email.message_from_bytes(data[0][1])
        body = ""
        for part in msg.walk():
            if part.get_content_type() in ["text/plain", "text/html"]:
                p = part.get_payload(decode=True)
                if p:
                    body += p.decode("utf-8", errors="ignore")
        mail.logout()
        
        urls = re.findall(r'https://proxy\.webshare\.io/[^\s\"\'<>]+verify[^\s\"\'<>]+', body)
        return urls[0].replace("&amp;", "&") if urls else None
    except Exception as e:
        print(f"Error checking Webshare email: {e}")
        return None

def check_existing_webshare_keys():
    print("Checking active Webshare keys in .env:")
    for k in ["WEBSHARE_KEY_3", "WEBSHARE_KEY_2", "WEBSHARE_KEY_1", "WEBSHARE_KEY"]:
        val = os.getenv(k)
        if not val:
            continue
        try:
            r = requests.get(
                "https://proxy.webshare.io/api/v2/proxy/list/?mode=direct&page=1&page_size=10",
                headers={"Authorization": f"Token {val}"},
                timeout=5
            )
            if r.status_code == 200:
                count = len(r.json().get("results", []))
                print(f"  • {k} -> Active (Returns {count} proxies)")
            else:
                print(f"  • {k} -> HTTP {r.status_code}")
        except Exception as e:
            print(f"  • {k} -> {e}")

if __name__ == "__main__":
    print(f"=== Webshare Proxy Expansion Engine (@{DOMAIN}) ===")
    check_existing_webshare_keys()
    
    sample_alias = generate_random_alias("proxy")
    print(f"\nGenerated Catch-All Alias for New Registration:")
    print(f"  Email: {sample_alias}")
    print(f"  (All incoming emails forward automatically to {GMAIL_USER})")
