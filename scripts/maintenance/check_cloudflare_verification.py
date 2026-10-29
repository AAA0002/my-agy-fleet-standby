#!/usr/bin/env python3
"""
Cloudflare Email Routing Verification Helper
Checks the inbox of GMAIL_ADDRESS for Cloudflare verification emails,
extracts the confirmation link, and can automatically complete the verification.
"""

import os
import re
import imaplib
import email
from email.header import decode_header
import requests
from dotenv import load_dotenv

load_dotenv(".env")

GMAIL_USER = os.getenv("GMAIL_ADDRESS")
GMAIL_PASS = os.getenv("GMAIL_APP_PASSWORD")

def check_verification_email():
    if not GMAIL_USER or not GMAIL_PASS:
        print("Missing GMAIL_ADDRESS or GMAIL_APP_PASSWORD in .env")
        return None

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_PASS)
        mail.select("inbox")

        # Search recent messages from Cloudflare
        status, messages = mail.search(None, '(FROM "cloudflare")')
        if not messages[0]:
            # Fallback to search all unread
            status, messages = mail.search(None, 'UNSEEN')

        msg_ids = messages[0].split()
        if not msg_ids:
            print("No recent Cloudflare or unread emails found.")
            mail.logout()
            return None

        # Check latest 5 emails in reverse order
        for msg_id in reversed(msg_ids[-5:]):
            _, data = mail.fetch(msg_id, "(RFC822)")
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)

            subject, encoding = decode_header(msg.get("Subject", ""))[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8", errors="ignore")

            sender = msg.get("From", "")
            print(f"Checking email: '{subject}' from {sender}")

            if "cloudflare" in sender.lower() or "verify" in subject.lower() or "routing" in subject.lower():
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() in ["text/plain", "text/html"]:
                            payload = part.get_payload(decode=True)
                            if payload:
                                body += payload.decode("utf-8", errors="ignore")
                else:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        body = payload.decode("utf-8", errors="ignore")

                # Search for Cloudflare verification URL
                urls = re.findall(r'https://[^\s"<>]+email-routing[^\s"<>]+', body)
                if not urls:
                    urls = re.findall(r'https://dash\.cloudflare\.com/[^\s"<>]+verify[^\s"<>]+', body)

                if urls:
                    print(f"Found Cloudflare verification URL: {urls[0]}")
                    mail.logout()
                    return urls[0]

        mail.logout()
        print("No verification link found in recent emails.")
        return None
    except Exception as e:
        print(f"Error checking email: {e}")
        return None

if __name__ == "__main__":
    url = check_verification_email()
    if url:
        print(f"\nVerification Link:\n{url}")
