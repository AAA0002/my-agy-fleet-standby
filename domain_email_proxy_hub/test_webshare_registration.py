#!/usr/bin/env python3
"""
Webshare Registration Real Test
Tests registering a fresh account on Webshare using custom domain alias *@agy.dpdns.org.
Monitors DOM, network calls, reCAPTCHA behavior, and incoming confirmation email via IMAP.
"""

import os
import sys
import time
import asyncio
import secrets
import string
import imaplib
import email
from patchright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

GMAIL_USER = os.getenv("GMAIL_ADDRESS", "aaa.support.a@gmail.com")
GMAIL_PASS = os.getenv("GMAIL_APP_PASSWORD")
DOMAIN = "agy.dpdns.org"

def generate_alias(prefix="ws_alpha"):
    suffix = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(5))
    return f"{prefix}_{suffix}@{DOMAIN}"

def generate_password():
    chars = string.ascii_letters + string.digits + "!@#$%"
    return "".join(secrets.choice(chars) for _ in range(16)) + "A1!"

def check_gmail_for_webshare(target_alias=None, max_wait=30):
    print(f"Checking Gmail ({GMAIL_USER}) for incoming Webshare confirmation email...")
    start = time.time()
    while time.time() - start < max_wait:
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(GMAIL_USER, GMAIL_PASS)
            mail.select("inbox")
            status, messages = mail.search(None, '(FROM "webshare")')
            msg_ids = messages[0].split()
            if msg_ids:
                # Check recent messages
                for mid in reversed(msg_ids[-5:]):
                    _, data = mail.fetch(mid, "(RFC822)")
                    msg = email.message_from_bytes(data[0][1])
                    subj = msg.get("Subject", "")
                    to_addr = msg.get("To", "")
                    print(f"  Found Webshare email! Subject: {subj}, To: {to_addr}")
                    if not target_alias or target_alias in to_addr or target_alias in str(msg):
                        body = ""
                        for part in msg.walk():
                            if part.get_content_type() in ["text/plain", "text/html"]:
                                p = part.get_payload(decode=True)
                                if p:
                                    body += p.decode("utf-8", errors="ignore")
                        mail.logout()
                        return {"subject": subj, "body": body, "to": to_addr}
            mail.logout()
        except Exception as e:
            print(f"  IMAP error: {e}")
        time.sleep(5)
    return None

async def run_registration():
    alias = generate_alias()
    password = generate_password()
    print(f"==================================================")
    print(f"Webshare Real Registration Test")
    print(f"Target Alias:    {alias}")
    print(f"Target Password: {'*' * len(password)}")
    print(f"Forwarding to:   {GMAIL_USER}")
    print(f"==================================================")

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

        api_logs = []
        async def on_response(response):
            if any(term in response.url for term in ["api", "register", "auth", "token", "user", "sakotis"]):
                try:
                    text = await response.text()
                    api_logs.append({
                        "status": response.status,
                        "url": response.url,
                        "body": text[:500]
                    })
                    print(f"  [HTTP {response.status}] {response.url[:70]}")
                except Exception:
                    pass

        page.on("response", on_response)

        print("\n1. Navigating to https://dashboard.webshare.io/register/ ...")
        await page.goto("https://dashboard.webshare.io/register/", wait_until="domcontentloaded", timeout=20000)
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

        print("4. Monitoring submission for 15 seconds...")
        for i in range(15):
            await asyncio.sleep(1)
            # Check for error banners
            alerts = await page.query_selector_all('[role="alert"], .MuiAlert-message, .error-message, .Mui-error')
            for a in alerts:
                t = (await a.inner_text()).strip()
                if t:
                    print(f"  [UI ALERT]: {t}")

        print(f"Final Page URL: {page.url}")
        title = await page.title()
        print(f"Final Page Title: {title}")

        # Check if reCAPTCHA challenge bframe is visible
        for f in page.frames:
            if "recaptcha" in f.url and "bframe" in f.url:
                print("  [CAPTCHA]: reCAPTCHA interactive challenge bframe detected!")

        await browser.close()

    print("\n5. Checking API interaction logs:")
    for log in api_logs:
        print(f"  - Status {log['status']}: {log['url']}")
        if log['status'] >= 400 or "error" in log['body'].lower() or "token" in log['body'].lower():
            print(f"    Body snippet: {log['body']}")

    print("\n6. Checking Gmail IMAP for confirmation email...")
    incoming = check_gmail_for_webshare(target_alias=alias, max_wait=20)
    if incoming:
        print(f"\n🎉 SUCCESS! Incoming confirmation email received:")
        print(f"  Subject: {incoming['subject']}")
        print(f"  Snippet: {incoming['body'][:300]}")
    else:
        print("\n⏳ No incoming confirmation email found within wait window.")

if __name__ == "__main__":
    asyncio.run(run_registration())
