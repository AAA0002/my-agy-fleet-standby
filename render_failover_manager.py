#!/usr/bin/env python3
"""
render_failover_manager.py
Automated Render Cloud High-Availability Fallback Controller
Uses Render API (Coz1gameh2@gmail.com / aaafreeai@gmail.com)
Connects to service: atf-mtproto-relayer-backup (srv-dakh1r942hec73aifqi0)
Can trigger emergency cloud redeployment or spin up fallback workers if VPS fails.
"""

import os
import sys
import json
import asyncio
import aiohttp

RENDER_API_KEY = os.getenv("RENDER_API_KEY", "rnd_LRrxGD2Rg7szFvTwKZDE4aNIOmnG")
SERVICE_ID = "srv-dakh1r942hec73aifqi0"
BASE_URL = "https://api.render.com/v1"

async def check_service_status(session: aiohttp.ClientSession) -> dict:
    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json"
    }
    url = f"{BASE_URL}/services/{SERVICE_ID}"
    async with session.get(url, headers=headers) as resp:
        if resp.status == 200:
            data = await resp.json()
            return {
                "ok": True,
                "id": data.get("id"),
                "name": data.get("name"),
                "url": data.get("serviceDetails", {}).get("url"),
                "suspended": data.get("suspended"),
                "updated_at": data.get("updatedAt")
            }
        return {"ok": False, "status": resp.status, "error": await resp.text()}

async def trigger_emergency_deploy(session: aiohttp.ClientSession) -> dict:
    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    url = f"{BASE_URL}/services/{SERVICE_ID}/deploys"
    async with session.post(url, headers=headers, json={"clearCache": "do_not_clear"}) as resp:
        if resp.status in [200, 201]:
            data = await resp.json()
            return {"ok": True, "deploy_id": data.get("id"), "status": data.get("status")}
        return {"ok": False, "status": resp.status, "error": await resp.text()}

async def main():
    async with aiohttp.ClientSession() as session:
        print("[Render Fallback Manager] Checking service health...")
        status = await check_service_status(session)
        print(f"[Render Fallback Manager] Status: {status}")

if __name__ == "__main__":
    asyncio.run(main())
