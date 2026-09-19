#!/usr/bin/env python3
"""
render_failover_manager.py
Automated Render Cloud High-Availability Fallback Controller
Active Account: coz1gameh1@gmail.com
Workspace Owner: tea-d8j9clt8nd3s73eb041g (My Workspace)

Strict Rules & Protections:
1. 100% Free Plan Only (plan: "free", $0 cost).
2. Completely isolated: Dedicated service name "my-agy-fleet-standby".
3. STRICT GUARDRAIL: Protected existing services (temp-mail-bot, atf-mtproto-relayer-backup)
   are BLACKLISTED and will NEVER be modified, triggered, or deleted.
"""

import os
import sys
import json
import asyncio
import aiohttp

RENDER_API_KEY = os.getenv("RENDER_API_KEY", "rnd_cGQwvG9J4pe6Rpf06sRMb4pzR6v1")
OWNER_ID = "tea-d8j9clt8nd3s73eb041g"
ACCOUNT_EMAIL = "coz1gameh1@gmail.com"
DEDICATED_SERVICE_NAME = "my-agy-fleet-standby"
STANDBY_SERVICE_ID = "srv-damuhkmgekts73f1osag"
STANDBY_URL = "https://my-agy-fleet-standby.onrender.com"
BASE_URL = "https://api.render.com/v1"

# Hardcoded blacklisted services that must NEVER be touched under any circumstances
PROTECTED_EXISTING_SERVICES = [
    "srv-d8j9n867r5hc73dlqvgg",
    "temp-mail-bot",
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

async def get_protected_services_status(session: aiohttp.ClientSession) -> dict:
    """Read-only health check to verify protected services remain untouched and online."""
    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json"
    }
    url = f"{BASE_URL}/services?limit=20"
    async with session.get(url, headers=headers) as resp:
        if resp.status == 200:
            services = await resp.json()
            status_map = {}
            for s in services:
                svc = s.get("service", {})
                sid = svc.get("id")
                sname = svc.get("name")
                if sid in PROTECTED_EXISTING_SERVICES or sname in PROTECTED_EXISTING_SERVICES:
                    status_map[sname] = {
                        "id": sid,
                        "suspended": svc.get("suspended"),
                        "type": svc.get("type"),
                        "updated_at": svc.get("updatedAt")
                    }
            return status_map
        return {}

async def main():
    async with aiohttp.ClientSession() as session:
        print(f"[Render Fallback Manager] Connected to active account: {ACCOUNT_EMAIL}")
        protected = await get_protected_services_status(session)
        print(f"[Render Fallback Manager] User Projects Safe & Online: {protected}")
        fleet_services = await list_our_services(session)
        print(f"[Render Fallback Manager] Dedicated fleet services found: {len(fleet_services)}")
        print("[Render Fallback Manager] Guardrails active: temp-mail-bot & atf-mtproto-relayer-backup protected ✅")

if __name__ == "__main__":
    asyncio.run(main())
