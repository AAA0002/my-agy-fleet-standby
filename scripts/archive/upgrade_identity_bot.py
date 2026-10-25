#!/usr/bin/env python3
"""
Deploy upgraded aaa-telegram-identity-bot with AI, Phone OSINT, and Fleet Monitor to Cloudflare Workers.
"""

import json
import asyncio
import aiohttp

import os

CF_EMAIL = os.getenv("CF_EMAIL_NODE_2", "Koramshah2@gmail.com")
CF_API_KEY = os.getenv("CF_API_KEY_NODE_2", "")
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID_NODE_2", "cf47efdd654cdb07ffe03d1361583f12")
WORKER_NAME = "aaa-telegram-identity-bot"
KV_NAMESPACE_ID = "44d6b1accc8c4fc18ee6d500eb9f0b14"
BOT_TOKEN = os.getenv("IDENTITY_BOT_TOKEN", "")
OWNER_ID = os.getenv("OWNER_ID", "6727787768")

async def main():
    print("🚀 Deploying upgraded 'aaa-telegram-identity-bot' with Workers AI & OSINT...")

    with open("/home/arif2743/cf_identity_bot.js", "r", encoding="utf-8") as f:
        code = f.read()

    headers = {
        "X-Auth-Email": CF_EMAIL,
        "X-Auth-Key": CF_API_KEY,
    }

    metadata = {
        "main_module": "index.js",
        "bindings": [
            {
                "name": "BOT_KV",
                "type": "kv_namespace",
                "namespace_id": KV_NAMESPACE_ID
            },
            {
                "name": "BOT_TOKEN",
                "type": "plain_text",
                "text": BOT_TOKEN
            },
            {
                "name": "OWNER_ID",
                "type": "plain_text",
                "text": OWNER_ID
            },
            {
                "name": "AI",
                "type": "ai"
            }
        ],
        "compatibility_date": "2024-09-01"
    }

    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/workers/scripts/{WORKER_NAME}"

    form = aiohttp.FormData()
    form.add_field("metadata", json.dumps(metadata), content_type="application/json", filename="metadata.json")
    form.add_field("index.js", code, content_type="application/javascript+module", filename="index.js")

    async with aiohttp.ClientSession() as session:
        async with session.put(url, headers=headers, data=form) as resp:
            res = await resp.json()
            if res.get("success"):
                print("✅ aaa-telegram-identity-bot upgraded & deployed successfully on Cloudflare Edge!")
            else:
                print(f"❌ Deployment failed: {res.get('errors')}")

if __name__ == "__main__":
    asyncio.run(main())
