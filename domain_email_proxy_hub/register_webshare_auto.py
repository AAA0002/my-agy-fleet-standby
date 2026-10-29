#!/usr/bin/env python3
"""
Webshare Autonomous Account Creator & Proxy Harvester
1. Generates catch-all alias *@agy.dpdns.org.
2. Automates browser registration with audio reCAPTCHA v2 solver.
3. Polls Gmail IMAP for Webshare verification email.
4. Completes activation and extracts the fresh API token.
"""

import os
import re
import time
import asyncio
import secrets
import string
import imaplib
import email
import requests
from dotenv import load_dotenv
from patchright.async_api import async_playwright
from audio_recaptcha_solver import solve_recaptcha_audio

local_env = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(local_env):
    load_dotenv(local_env)

DOMAIN = "agy.dpdns.org"
GMAIL_USER = os.getenv("GMAIL_ADDRESS", "aaa.support.a@gmail.com")
GMAIL_PASS = os.getenv("GMAIL_APP_PASSWORD")

def generate_alias(prefix="ws_fleet"):
    suffix = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(6))
    return f"{prefix}_{suffix}@{DOMAIN}"

def generate_password():
    chars = string.ascii_letters + string.digits + "!@#$%^"
    return "".join(secrets.choice(chars) for _ in range(16)) + "A1!"

def check_gmail_for_verification(target_alias, max_wait=45):
    print(f"Waiting for Webshare activation email forwarded to {GMAIL_USER}...")
    start = time.time()
    while time.time() - start < max_wait:
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(GMAIL_USER, GMAIL_PASS)
            mail.select("inbox")
            status, messages = mail.search(None, '(FROM "webshare")')
            msg_ids = messages[0].split()
            if msg_ids:
                for mid in reversed(msg_ids[-5:]):
                    _, data = mail.fetch(mid, "(RFC822)")
                    msg = email.message_from_bytes(data[0][1])
                    subj = str(msg.get("Subject", ""))
                    to_addr = str(msg.get("To", ""))
                    raw_body = ""
                    for part in msg.walk():
                        if part.get_content_type() in ["text/plain", "text/html"]:
                            p = part.get_payload(decode=True)
                            if p:
                                raw_body += p.decode("utf-8", errors="ignore")
                    
                    if target_alias in to_addr or target_alias in raw_body or "verify" in raw_body:
                        # Extract activation URL
                        urls = re.findall(r'https://[^\s\"\'<>]+verify[^\s\"\'<>]+', raw_body)
                        if not urls:
                            urls = re.findall(r'https://[^\s\"\'<>]+activation[^\s\"\'<>]+', raw_body)
                        mail.logout()
                        return {
                            "subject": subj,
                            "url": urls[0].replace("&amp;", "&") if urls else None,
                            "body": raw_body
                        }
            mail.logout()
        except Exception as e:
            print(f"  IMAP error: {e}")
        time.sleep(5)
    return None

async def run():
    alias = generate_alias()
    password = generate_password()
    print("==================================================")
    print("Autonomous Webshare Account Registration")
    print(f"Target Alias:    {alias}")
    print(f"Forwarding to:   {GMAIL_USER}")
    print("==================================================")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage"
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()

        print("\n1. Navigating to https://dashboard.webshare.io/register/ ...")
        await page.goto("https://dashboard.webshare.io/register/", wait_until="domcontentloaded", timeout=25000)
        await asyncio.sleep(4)

        print("2. Filling registration form...")
        email_inp = await page.wait_for_selector('input[data-testid="email-input"]', timeout=10000)
        await email_inp.fill(alias)

        pass_inp = await page.wait_for_selector('input[data-testid="password-input"]', timeout=10000)
        await pass_inp.fill(password)

        chk_inp = await page.wait_for_selector('input[type="checkbox"]', timeout=10000)
        await chk_inp.click()

        print("3. Clicking 'Sign Up With Email'...")
        signup_btn = await page.wait_for_selector('button:has-text("Sign Up With Email")', timeout=10000)
        await signup_btn.click()

        print("4. Checking for reCAPTCHA challenge...")
        await asyncio.sleep(4)
        
        has_challenge = False
        for f in page.frames:
            if "recaptcha" in f.url and "bframe" in f.url:
                has_challenge = True
                break

        if has_challenge:
            print("  Detected reCAPTCHA challenge! Engaging audio solver...")
            solved = await solve_recaptcha_audio(page)
            print(f"  Solver result: {solved}")
            await asyncio.sleep(5)
        else:
            print("  No bframe challenge popped up directly. Monitoring submission...")

        print(f"5. Final Page URL: {page.url}")
        title = await page.title()
        print(f"   Final Title: {title}")

        await browser.close()

    print("\n6. Checking Gmail IMAP for activation link...")
    activation = check_gmail_for_verification(alias, max_wait=30)
    if activation and activation.get("url"):
        act_url = activation["url"]
        print(f"🎉 SUCCESS! Received activation link:\n  {act_url}")
        print("7. Activating account via GET request...")
        r = requests.get(act_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        print(f"   Activation response: HTTP {r.status_code}")
    elif activation:
        print(f"Received email: {activation['subject']}")
    else:
        print("⏳ No activation email received within window.")

if __name__ == "__main__":
    asyncio.run(run())
