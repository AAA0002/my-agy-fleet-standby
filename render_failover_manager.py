#!/usr/bin/env python3
"""
render_failover_manager.py
Automated Render Multi-Account Cloud Failover Mesh Controller
Dual Account High Availability:
  Node 1: coz1gameh1@gmail.com (Singapore) -> https://my-agy-fleet-standby.onrender.com
  Node 2: abidhasanch2001@gmail.com (Frankfurt) -> https://my-agy-fleet-standby-node2.onrender.com

Strict Rules & Protections:
1. 100% Free Plan Only (plan: "free", $0 cost forever).
2. Completely isolated: Dedicated services only.
3. STRICT GUARDRAIL: Protected existing user services (temp-mail-bot, atf-mtproto-relayer-backup)
   are BLACKLISTED and will NEVER be modified, triggered, or deleted.
"""

import os
import sys
import json
import asyncio
import aiohttp

RENDER_ACCOUNTS = [
    {
        "name": "Render Node 1 (Singapore)",
        "email": "coz1gameh1@gmail.com",
        "api_key": os.getenv("RENDER_API_KEY_1", "rnd_cGQwvG9J4pe6Rpf06sRMb4pzR6v1"),
        "owner_id": "tea-d8j9clt8nd3s73eb041g",
        "service_name": "my-agy-fleet-standby",
        "service_id": "srv-damuhkmgekts73f1osag",
        "url": "https://my-agy-fleet-standby.onrender.com",
        "region": "singapore"
    },
    {
        "name": "Render Node 2 (Frankfurt)",
        "email": "abidhasanch2001@gmail.com",
        "api_key": os.getenv("RENDER_API_KEY_2", "rnd_KnVaiOw93SKa4fSTrEURwZrP0UaB"),
        "owner_id": "tea-dan5pgbm8hqs73a5cvig",
        "service_name": "my-agy-fleet-standby-node2",
        "service_id": "srv-dan5q00ae00c73djummg",
        "url": "https://my-agy-fleet-standby-node2.onrender.com",
        "region": "frankfurt"
    },
    {
        "name": "Render Node 3 (Hermes-Grok AI Council)",
        "email": "koramshah2@gmail.com",
        "api_key": os.getenv("RENDER_API_KEY", "rnd_PqsurfX5D9blSaEEuEDDAUcl393y"),
        "owner_id": "tea-daoj9nid0e5s738gqp0g",
        "service_name": "hermes-grok-cloud-agent",
        "service_id": "srv-daojdt5g1s2s738jsjmg",
        "url": "https://hermes-grok-cloud-agent.onrender.com",
        "region": "singapore"
    }
]

BASE_URL = "https://api.render.com/v1"

# Blacklisted user services that must NEVER be touched under any circumstances
PROTECTED_EXISTING_SERVICES = [
    "srv-d8j9n867r5hc73dlqvgg",
    "temp-mail-bot",
    "srv-dakh1r942hec73aifqi0",
    "atf-mtproto-relayer-backup"
]

def assert_safe_service(service_id: str, service_name: str = ""):
    if service_id in PROTECTED_EXISTING_SERVICES or service_name in PROTECTED_EXISTING_SERVICES:
        raise PermissionError(f"CRITICAL SAFETY ABORT: Service {service_id} ({service_name}) is a protected user project and cannot be touched!")

async def check_account_health(session: aiohttp.ClientSession, account: dict) -> dict:
    headers = {
        "Authorization": f"Bearer {account['api_key']}",
        "Accept": "application/json"
    }
    # 1. Check service status
    svc_info = {"name": account["name"], "email": account["email"], "url": account["url"], "status": "unknown"}
    try:
        async with session.get(f"{BASE_URL}/services/{account['service_id']}", headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as r:
            if r.status == 200:
                data = await r.json()
                svc = data.get("service", {})
                svc_info["service_status"] = svc.get("suspended", "active")
                svc_info["plan"] = svc.get("serviceDetails", {}).get("plan")
                svc_info["region"] = svc.get("serviceDetails", {}).get("region")
            else:
                svc_info["error"] = f"HTTP {r.status}"
    except Exception as e:
        svc_info["error"] = str(e)

    # 2. Check live web endpoint
    try:
        async with session.get(f"{account['url']}/health", timeout=aiohttp.ClientTimeout(total=10)) as hr:
            svc_info["endpoint_alive"] = (hr.status == 200)
    except Exception:
        svc_info["endpoint_alive"] = False

    return svc_info

async def trigger_batch_collection(session: aiohttp.ClientSession, secret_key: str = "agy_cf_secret_7d36994e_2026") -> dict:
    """Tries Node 1 first. If Node 1 fails or times out, immediately triggers Node 2."""
    for acc in RENDER_ACCOUNTS:
        url = f"{acc['url']}/collect-tokens"
        try:
            async with session.post(
                url,
                headers={"Authorization": f"Bearer {secret_key}", "Content-Type": "application/json"},
                json={},
                timeout=aiohttp.ClientTimeout(total=45)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {"success": True, "active_node": acc["name"], "result": data}
        except Exception as e:
            print(f"[{acc['name']}] Attempt failed: {e}. Falling back to next Render node...")
            continue

    return {"success": False, "error": "All Render standby nodes failed or sleeping."}

async def main():
    async with aiohttp.ClientSession() as session:
        print("=" * 65)
        print("RENDER DUAL-ACCOUNT CLOUD FAILOVER MESH STATUS")
        print("=" * 65)
        for acc in RENDER_ACCOUNTS:
            health = await check_account_health(session, acc)
            status_symbol = "🟢 ONLINE" if health.get("endpoint_alive") else "🟡 DEPLOYING / SLEEPING"
            print(f"• {acc['name']} ({acc['region'].upper()}): {status_symbol}")
            print(f"  Email: {acc['email']}")
            print(f"  URL: {acc['url']}")
            print(f"  Plan: {health.get('plan', 'free')} ($0/mo)")
            print("-" * 65)

if __name__ == "__main__":
    asyncio.run(main())
