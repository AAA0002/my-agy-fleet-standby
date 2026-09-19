#!/usr/bin/env python3
"""
render_failover_manager.py
Automated Render Cloud High-Availability Fallback Controller
Strict Rules & Protections:
1. 100% Free Plan Only (plan: "free", $0 cost).
2. Completely isolated: Dedicated service name "my-agy-fleet-standby".
3. STRICT GUARDRAIL: Protected existing services (like atf-mtproto-relayer-backup)
   are BLACKLISTED and will NEVER be modified, triggered, or deleted.
"""

import os
import sys
import json
import asyncio
import aiohttp

RENDER_API_KEY = os.getenv("RENDER_API_KEY", "rnd_LRrxGD2Rg7szFvTwKZDE4aNIOmnG")
OWNER_ID = "tea-dakgi2ad0e5s73dtbfu0"
DEDICATED_SERVICE_NAME = "my-agy-fleet-standby"
BASE_URL = "https://api.render.com/v1"

# Hardcoded blacklisted services that must NEVER be touched under any circumstances
PROTECTED_EXISTING_SERVICES = [
    "srv-dakh1r942hec73aifqi0",
    "atf-mtproto-relayer-backup"
]

def assert_safe_service(service_id: str, service_name: str = ""):
    if service_id in PROTECTED_EXISTING_SERVICES or service_name in PROTECTED_EXISTING_SERVICES:
        raise PermissionError(f"CRITICAL SAFETY ABORT: Service {service_id} ({service_name}) is a protected user project and cannot be touched!")

async def list_our_services(session: aiohttp.ClientSession) -> list:
    """Lists services, filtering out protected existing user projects."""
    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json"
    }
    url = f"{BASE_URL}/services?limit=20"
    async with session.get(url, headers=headers) as resp:
        if resp.status == 200:
            services = await resp.json()
            fleet_services = []
            for s in services:
                svc = s.get("service", {})
                sid = svc.get("id")
                sname = svc.get("name")
                if sid not in PROTECTED_EXISTING_SERVICES and sname not in PROTECTED_EXISTING_SERVICES:
                    fleet_services.append(svc)
            return fleet_services
        return []

async def create_free_standby_service(session: aiohttp.ClientSession) -> dict:
    """Creates a 100% FREE Tier Web Service on Render for standby failover."""
    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # Check if already exists
    existing = await list_our_services(session)
    for svc in existing:
        if svc.get("name") == DEDICATED_SERVICE_NAME:
            return {"ok": True, "already_exists": True, "service": svc}
            
    payload = {
        "type": "web_service",
        "name": DEDICATED_SERVICE_NAME,
        "ownerId": OWNER_ID,
        "repo": "https://github.com/AAA2743/my-agy-ai-fleet",
        "branch": "main",
        "autoDeploy": "no",  # Manual/API deploy only to save free hours
        "serviceDetails": {
            "plan": "free",  # STRICTLY FREE TIER ($0.00)
            "runtime": "python",
            "buildCommand": "pip install -r requirements.txt",
            "startCommand": "python3 bep20_onchain_watcher.py"
        }
    }
    
    url = f"{BASE_URL}/services"
    async with session.post(url, headers=headers, json=payload) as resp:
        if resp.status in [200, 201]:
            data = await resp.json()
            return {"ok": True, "service": data}
        return {"ok": False, "status": resp.status, "error": await resp.text()}

async def main():
    async with aiohttp.ClientSession() as session:
        print("[Render Fallback Manager] Safe environment audit...")
        services = await list_our_services(session)
        print(f"[Render Fallback Manager] Dedicated fleet services found: {len(services)}")
        print("[Render Fallback Manager] Protected services guardrail active ✅ (atf-mtproto-relayer-backup protected).")

if __name__ == "__main__":
    asyncio.run(main())
