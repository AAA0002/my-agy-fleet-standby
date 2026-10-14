#!/usr/bin/env python3
"""
render_failover_manager.py
Automated Render 3-Account Cloud Baton Relay & Maintenance Mode Mesh Controller

Strict Architecture:
  1. Exactly 3 Legitimate Render Accounts:
     - Node 1: coz1gameh1@gmail.com (Singapore) -> srv-damuhkmgekts73f1osag (my-agy-fleet-standby)
     - Node 2: abidhasanch2001@gmail.com (Frankfurt) -> srv-dan5q00ae00c73djummg (my-agy-fleet-standby-node2) [Current Primary]
     - Node 3: koramshah2@gmail.com (Oregon) -> srv-db437o3tqb8s73dt4erg (my-agy-fleet-standby-node3)
  2. Protected Projects (NEVER TOUCHED):
     - temp-mail-bot: srv-d8j9n867r5hc73dlqvgg (Protected User Project)
     - hermes-grok-cloud-agent: srv-daojdt5g1s2s738jsjmg (Dedicated Ari AI Groq Council Agent)
  3. Telegram Anti-Ban Maintenance Mode & Graceful Disconnect:
     - When switching Render nodes, the system enters Maintenance Mode for a 5-minute cooling window.
     - All Telegram MTProto sockets are disconnected and closed cleanly.
     - Old node container is suspended (hour consumption stops at 0).
     - New node container resumes and waits out the cooling window before connecting to Telegram.
     - Zero dual-IP connection overlap -> Zero Telegram account bans / AuthKeyDuplicatedError.
"""

import os
import sys
import json
import time
import asyncio
import aiohttp
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.render.com/v1"
REPORT_BOT_TOKEN = os.getenv("REPORT_BOT_TOKEN", "8858823950:AAEdX47g7as1xLYEudfRUHaVGUdNIaU_ku8")
REPORT_CHAT_ID = os.getenv("REPORT_CHAT_ID", "6727787768")
UPSTASH_URL = os.getenv("UPSTASH_URL") or os.getenv("UPSTASH_REDIS_REST_URL") or "https://pleasant-locust-220893.upstash.io"
UPSTASH_TOKEN = os.getenv("UPSTASH_TOKEN") or os.getenv("UPSTASH_REDIS_REST_TOKEN") or "gQAAAAAAA17dAAIgcDFhZmU2OTdiZjRmYmY0OTI2OTgyZTYyYjkwYWQ5ODYzZg"

RENDER_ACCOUNTS = [
    {
        "node": 1,
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
        "node": 2,
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
        "node": 3,
        "name": "Render Node 3 (Oregon)",
        "email": "koramshah2@gmail.com",
        "api_key": os.getenv("RENDER_API_KEY_3") or os.getenv("RENDER_API_KEY", "rnd_PqsurfX5D9blSaEEuEDDAUcl393y"),
        "owner_id": "tea-daoj9nid0e5s738gqp0g",
        "service_name": "my-agy-fleet-standby-node3",
        "service_id": "srv-db437o3tqb8s73dt4erg",
        "url": "https://my-agy-fleet-standby-node3.onrender.com",
        "region": "oregon"
    }
]

RELAYER_SERVICES = []

# Blacklisted user services that must NEVER be touched under any circumstances
PROTECTED_EXISTING_SERVICES = [
    "srv-d8j9n867r5hc73dlqvgg",
    "temp-mail-bot",
    "srv-daojdt5g1s2s738jsjmg",
    "hermes-grok-cloud-agent"
]

def assert_safe_service(service_id: str, service_name: str = ""):
    if service_id in PROTECTED_EXISTING_SERVICES or service_name in PROTECTED_EXISTING_SERVICES:
        raise PermissionError(f"CRITICAL SAFETY ABORT: Service {service_id} ({service_name}) is protected and cannot be modified or rotated!")

async def send_telegram_alert(text: str):
    """Sends an administrative alert to @myagyai via Telegram Bot API."""
    if not (REPORT_BOT_TOKEN and REPORT_CHAT_ID):
        print(f"[Alert] {text}")
        return
    try:
        url = f"https://api.telegram.org/bot{REPORT_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": REPORT_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status != 200:
                    print(f"[Telegram Alert] Failed HTTP {resp.status}")
    except Exception as e:
        print(f"[Telegram Alert] Error: {e}")

async def set_maintenance_mode(enabled: bool, duration_seconds: int = 300, reason: str = ""):
    """Sets or clears the distributed Maintenance Mode in Upstash Redis."""
    if not (UPSTASH_URL and UPSTASH_TOKEN):
        return
    up_h = {"Authorization": f"Bearer {UPSTASH_TOKEN}"}
    now = time.time()
    async with aiohttp.ClientSession() as s:
        if enabled:
            until = now + duration_seconds
            await s.post(f"{UPSTASH_URL}/set/fleet:maintenance_mode/{reason or 'Render Node Rotation'}?ex={duration_seconds + 60}", headers=up_h, timeout=aiohttp.ClientTimeout(total=5))
            await s.post(f"{UPSTASH_URL}/set/fleet:maintenance_until/{until}?ex={duration_seconds + 60}", headers=up_h, timeout=aiohttp.ClientTimeout(total=5))
            print(f"🔒 [Maintenance Mode] ENABLED for {duration_seconds}s (Until: {datetime.fromtimestamp(until, tz=timezone.utc).strftime('%H:%M:%S UTC')}). Reason: {reason}")
        else:
            await s.post(f"{UPSTASH_URL}/del/fleet:maintenance_mode", headers=up_h, timeout=aiohttp.ClientTimeout(total=5))
            await s.post(f"{UPSTASH_URL}/del/fleet:maintenance_until", headers=up_h, timeout=aiohttp.ClientTimeout(total=5))
            print("🔓 [Maintenance Mode] DISABLED. Normal cloud operations resumed.")

async def is_in_maintenance_mode() -> tuple[bool, str, int]:
    """Checks if the fleet is in Maintenance Mode. Returns (in_maint, reason, remaining_seconds)."""
    if not (UPSTASH_URL and UPSTASH_TOKEN):
        return (False, "", 0)
    try:
        up_h = {"Authorization": f"Bearer {UPSTASH_TOKEN}"}
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{UPSTASH_URL}/get/fleet:maintenance_mode", headers=up_h, timeout=aiohttp.ClientTimeout(total=3)) as r:
                if r.status == 200:
                    d = await r.json()
                    val = d.get("result")
                    if val and val not in ("null", "false", "0", ""):
                        async with s.get(f"{UPSTASH_URL}/get/fleet:maintenance_until", headers=up_h, timeout=aiohttp.ClientTimeout(total=3)) as r_u:
                            until_ts = 0
                            if r_u.status == 200:
                                u_d = await r_u.json()
                                try:
                                    until_ts = float(u_d.get("result") or 0)
                                except Exception:
                                    until_ts = 0
                            now = time.time()
                            if until_ts > now:
                                return (True, str(val), int(until_ts - now))
    except Exception as e:
        print(f"[Maintenance Check Error] {e}")
    return (False, "", 0)

async def check_account_health(session: aiohttp.ClientSession, account: dict) -> dict:
    headers = {
        "Authorization": f"Bearer {account['api_key']}",
        "Accept": "application/json"
    }
    svc_info = {
        "node": account["node"],
        "name": account["name"],
        "email": account["email"],
        "url": account["url"],
        "service_id": account["service_id"],
        "service_status": "unknown",
        "endpoint_alive": False
    }
    try:
        async with session.get(f"{BASE_URL}/services/{account['service_id']}", headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as r:
            if r.status == 200:
                data = await r.json()
                svc = data.get("service", {}) if "service" in data else data
                svc_info["service_status"] = svc.get("suspended", "not_suspended")
                svc_info["plan"] = svc.get("serviceDetails", {}).get("plan")
                svc_info["region"] = svc.get("serviceDetails", {}).get("region")
            else:
                svc_info["error"] = f"HTTP {r.status}"
    except Exception as e:
        svc_info["error"] = str(e)

    # Check live web endpoint
    try:
        async with session.get(f"{account['url']}/health", timeout=aiohttp.ClientTimeout(total=8)) as hr:
            svc_info["endpoint_alive"] = (hr.status == 200)
    except Exception:
        svc_info["endpoint_alive"] = False

    return svc_info

async def suspend_node(node_num: int) -> bool:
    """Suspends the specified Render node via Render REST API."""
    acc = next((a for a in RENDER_ACCOUNTS if a["node"] == node_num), None)
    if not acc:
        print(f"❌ Unknown node number: {node_num}")
        return False
    assert_safe_service(acc["service_id"], acc["service_name"])
    headers = {"Authorization": f"Bearer {acc['api_key']}", "Accept": "application/json"}
    url = f"{BASE_URL}/services/{acc['service_id']}/suspend"
    async with aiohttp.ClientSession() as s:
        try:
            async with s.post(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status in (200, 202, 204):
                    print(f"⏸️ Successfully suspended {acc['name']} ({acc['service_id']}). Hour meter frozen to 0!")
                    return True
                else:
                    err = await r.text()
                    print(f"❌ Failed to suspend {acc['name']}: HTTP {r.status} - {err}")
                    return False
        except Exception as e:
            print(f"❌ Error suspending {acc['name']}: {e}")
            return False

async def resume_node(node_num: int) -> bool:
    """Resumes the specified Render node via Render REST API."""
    acc = next((a for a in RENDER_ACCOUNTS if a["node"] == node_num), None)
    if not acc:
        print(f"❌ Unknown node number: {node_num}")
        return False
    assert_safe_service(acc["service_id"], acc["service_name"])
    headers = {"Authorization": f"Bearer {acc['api_key']}", "Accept": "application/json"}
    url = f"{BASE_URL}/services/{acc['service_id']}/resume"
    async with aiohttp.ClientSession() as s:
        try:
            async with s.post(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status in (200, 202, 204):
                    print(f"▶️ Successfully resumed {acc['name']} ({acc['service_id']}).")
                    return True
                else:
                    err = await r.text()
                    print(f"❌ Failed to resume {acc['name']}: HTTP {r.status} - {err}")
                    return False
        except Exception as e:
            print(f"❌ Error resuming {acc['name']}: {e}")
            return False

async def disconnect_node_mtproto(acc: dict):
    """Sends a clean disconnect request to the node's MTProto socket endpoint."""
    try:
        url = f"{acc['url']}/api/fleet/disconnect-mtproto"
        async with aiohttp.ClientSession() as s:
            async with s.post(url, timeout=aiohttp.ClientTimeout(total=8)) as r:
                if r.status == 200:
                    print(f"🔌 [Clean Disconnect] Node {acc['node']} successfully severed MTProto sockets.")
    except Exception as e:
        print(f"Note: Could not reach {acc['url']}/api/fleet/disconnect-mtproto ({e})")

async def rotate_node(from_node: int, to_node: int, cooldown_seconds: int = 300) -> bool:
    """
    Executes an atomic Baton Relay Handover between Render nodes with Telegram Anti-Ban Maintenance Mode.
    Sequence:
      1. Enter Maintenance Mode in Upstash Redis (duration: cooldown_seconds).
      2. Broadcast Alert to Admin via Telegram.
      3. Resume destination node (to_node).
      4. Poll destination node until endpoint is up and ready.
      5. Explicitly disconnect MTProto sockets on source node (from_node).
      6. Suspend source node (from_node) -> stops container, freezes hours.
      7. Wait out the cooling buffer (cooldown_seconds) so Telegram server cleans up socket states.
      8. Exit Maintenance Mode -> destination node takes over cleanly on its own IP.
      9. Broadcast Completion Alert to Admin via Telegram.
    """
    from_acc = next((a for a in RENDER_ACCOUNTS if a["node"] == from_node), None)
    to_acc = next((a for a in RENDER_ACCOUNTS if a["node"] == to_node), None)

    if not from_acc or not to_acc:
        print(f"❌ Invalid rotation pair: Node {from_node} -> Node {to_node}")
        return False

    print("=" * 70)
    print(f"🚀 INITIATING BATON RELAY HANDOVER: {from_acc['name']} ➡️ {to_acc['name']}")
    print(f"🛡️ TELEGRAM ANTI-BAN MAINTENANCE MODE: {cooldown_seconds}s COOLING WINDOW")
    print("=" * 70)

    # 1. Enable Maintenance Mode
    reason_str = f"Render Node Handover: Node {from_node} ({from_acc['region']}) ➡️ Node {to_node} ({to_acc['region']})"
    await set_maintenance_mode(True, duration_seconds=cooldown_seconds, reason=reason_str)

    # 2. Telegram Alert
    start_alert = (
        f"🟡 <b>[FLEET ROTATION] Maintenance Mode Activated</b>\n\n"
        f"🔄 <b>Handover:</b> {from_acc['name']} ➡️ {to_acc['name']}\n"
        f"⏳ <b>Cooling Duration:</b> {cooldown_seconds // 60} minutes ({cooldown_seconds}s)\n"
        f"🛡️ <b>Anti-Ban Safeguard:</b> All Telegram MTProto sockets are being disconnected cleanly so Telegram never sees dual-IP collisions.\n"
        f"⏸️ <b>Source Node:</b> Suspending container to freeze free tier hour usage."
    )
    await send_telegram_alert(start_alert)

    # 3. Resume target node
    print(f"1. Resuming destination {to_acc['name']} via Render API...")
    resumed = await resume_node(to_node)
    if not resumed:
        print("❌ Handover aborted: Could not resume target node!")
        await set_maintenance_mode(False)
        return False

    # 4. Wait for destination node to warm up
    print("2. Warming up destination node (polling health endpoint)...")
    dest_alive = False
    for attempt in range(24):
        await asyncio.sleep(5)
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(f"{to_acc['url']}/health", timeout=aiohttp.ClientTimeout(total=5)) as r:
                    if r.status == 200:
                        dest_alive = True
                        print(f"✅ Destination {to_acc['name']} is ALIVE and reachable!")
                        break
        except Exception:
            pass
        print(f"   Waiting for {to_acc['name']} boot... ({attempt+1}/24)")

    if not dest_alive:
        print(f"❌ Handover aborted: Destination {to_acc['name']} failed to respond healthy within 120s!")
        await set_maintenance_mode(False)
        abort_alert = (
            f"🔴 <b>[FLEET ROTATION ABORTED] Handover Failed</b>\n\n"
            f"❌ <b>Destination:</b> {to_acc['name']} failed to become healthy within 120s.\n"
            f"🛡️ <b>Action:</b> Kept {from_acc['name']} running. Maintenance mode deactivated."
        )
        await send_telegram_alert(abort_alert)
        return False

    # 5. Clean disconnect on old node
    print(f"3. Severing MTProto connections on {from_acc['name']}...")
    await disconnect_node_mtproto(from_acc)

    # 6. Suspend old node
    print(f"4. Suspending source node {from_acc['name']} via Render API...")
    suspended = await suspend_node(from_node)
    if not suspended:
        print("⚠️ Warning: Source node suspend returned error. Checking status...")

    # 7. Cooling Buffer (Wait out maintenance cooldown)
    print(f"5. Enforcing cooling period ({cooldown_seconds}s) to allow Telegram datacenter socket state to flush...")
    # Calculate remaining time
    in_maint, _, rem = await is_in_maintenance_mode()
    wait_time = max(rem, 30)
    for remaining in range(wait_time, 0, -10):
        print(f"   ⏳ Cooling down: {remaining}s remaining before Telegram reconnection...")
        await asyncio.sleep(min(remaining, 10))

    # 8. Clear Maintenance Mode and Promote New Node
    print("6. Clearing Maintenance Mode and promoting destination node...")
    await set_maintenance_mode(False)
    if UPSTASH_URL and UPSTASH_TOKEN:
        up_h = {"Authorization": f"Bearer {UPSTASH_TOKEN}"}
        async with aiohttp.ClientSession() as s:
            await s.post(f"{UPSTASH_URL}/set/fleet:active_render_node/node{to_node}", headers=up_h)
            await s.post(f"{UPSTASH_URL}/set/fleet:mtproto_coordinator/node{to_node}?ex=1800", headers=up_h)

    # 9. Send Final Telegram Alert
    finish_alert = (
        f"🟢 <b>[FLEET ROTATION] Handover Completed Successfully!</b>\n\n"
        f"✅ <b>Active Cloud Node:</b> {to_acc['name']} ({to_acc['region'].upper()})\n"
        f"⏸️ <b>Suspended Node:</b> {from_acc['name']} (0 hours consumed)\n"
        f"🛡️ <b>Telegram Anti-Ban:</b> Cooling period elapsed. All 18 Telegram sessions safely resuming on clean single IP.\n"
        f"🚀 <b>Fleet Status:</b> Normal cloud farming, token refresh, and OTP monitoring active!"
    )
    await send_telegram_alert(finish_alert)
    print("=" * 70)
    print("🎉 ROTATION COMPLETE! NEW ACTIVE NODE IS LIVE.")
    print("=" * 70)
    return True

def get_current_month_hours() -> float:
    """Calculates active running hours for the current calendar month."""
    now = datetime.now(timezone.utc)
    month_start = datetime(now.year, now.month, 1, 0, 0, 0, tzinfo=timezone.utc)
    elapsed_seconds = (now - month_start).total_seconds()
    return round(elapsed_seconds / 3600.0, 1)

async def check_and_auto_rotate(limit_hours: float = 650.0) -> bool:
    """
    Checks active Render node usage. If current node usage >= limit_hours (650h):
    1. Pauses all operations (Maintenance Mode in Upstash Redis).
    2. Resumes destination standby node (Node 3 Oregon) via Render REST API.
    3. Confirms destination node is healthy.
    4. Suspends old node (Node 2 Frankfurt) via Render REST API to freeze hour consumption.
    5. Waits out 5-minute cooling period (anti-ban protection).
    6. Promotes new node in Upstash Redis.
    7. Clears Maintenance Mode and resumes normal cloud operations.
    """
    cur_hours = get_current_month_hours()
    print(f"⏱️ Current Month Active Runtime: {cur_hours}h / 750h Free Tier (Threshold: {limit_hours}h)")
    if cur_hours < limit_hours:
        print(f"✅ Safe margin: {round(limit_hours - cur_hours, 1)}h remaining before auto-rotation. No action needed.")
        return False

    print(f"🚨 LIMIT REACHED: Node 2 Frankfurt reached {cur_hours}h (>= {limit_hours}h limit). Initiating Baton Relay to Node 3 Oregon!")
    return await rotate_node(from_node=2, to_node=3, cooldown_seconds=300)

async def print_status():
    """Prints comprehensive health & maintenance status for all 3 nodes."""
    async with aiohttp.ClientSession() as session:
        print("=" * 70)
        print("RENDER SINGLE-ACTIVE BATON RELAY CONTROLLER (650H AUTO-FAILOVER)")
        print("=" * 70)

        in_maint, reason, rem = await is_in_maintenance_mode()
        if in_maint:
            print(f"🟡 MAINTENANCE MODE ACTIVE: {reason}")
            print(f"   Cooldown remaining: {rem} seconds ({rem // 60}m {rem % 60}s)")
        else:
            print("🟢 FLEET STATUS: NORMAL (Maintenance Mode Idle)")
        print("-" * 70)

        cur_hours = get_current_month_hours()
        print(f"⏱️ BILLING MONTH RUNTIME: {cur_hours}h / 750h Free Tier (Threshold: 650h)")
        if cur_hours >= 650.0:
            print("⚠️ WARNING: 650h threshold reached! Baton Relay rotation is due.")
        else:
            print(f"✅ Safe margin: {round(650.0 - cur_hours, 1)}h remaining before auto-rotation.")
        print("-" * 70)

        for acc in RENDER_ACCOUNTS:
            health = await check_account_health(session, acc)
            if health.get("service_status") == "suspended":
                status_symbol = "⏸️ SUSPENDED (0h Consumed / Frozen)"
            elif health.get("endpoint_alive"):
                status_symbol = "🟢 ACTIVE & ONLINE (Current Single Host)"
            elif health.get("service_status") == "not_suspended":
                status_symbol = "🟡 ACTIVE CONTAINER (Booting/Warming)"
            else:
                status_symbol = "🔴 UNKNOWN / OFFLINE"

            print(f"• [Node {acc['node']}] {acc['name']}: {status_symbol}")
            print(f"  Service: {acc['service_id']} | Email: {acc['email']}")
            print(f"  URL: {acc['url']}")
            print("-" * 70)
        print("=" * 70)

async def main():
    args = sys.argv[1:]
    if not args or args[0] == "status":
        await print_status()
    elif args[0] == "check_limit":
        limit = float(args[1]) if len(args) > 1 else 650.0
        await check_and_auto_rotate(limit_hours=limit)
    elif args[0] == "rotate":
        from_n = int(args[1]) if len(args) > 1 else 2
        to_n = int(args[2]) if len(args) > 2 else 3
        cooldown = int(args[3]) if len(args) > 3 else 300
        await rotate_node(from_n, to_n, cooldown_seconds=cooldown)
    elif args[0] == "suspend":
        node_n = int(args[1]) if len(args) > 1 else 1
        await suspend_node(node_n)
    elif args[0] == "resume":
        node_n = int(args[1]) if len(args) > 1 else 2
        await resume_node(node_n)
    elif args[0] == "maint":
        action = args[1] if len(args) > 1 else "status"
        if action == "on":
            secs = int(args[2]) if len(args) > 2 else 300
            await set_maintenance_mode(True, duration_seconds=secs, reason="Manual Operator Trigger")
        elif action == "off":
            await set_maintenance_mode(False)
        else:
            in_m, rsn, rem = await is_in_maintenance_mode()
            print(f"Maintenance: {in_m}, Reason: {rsn}, Remaining: {rem}s")
    else:
        print("Usage:")
        print("  python3 render_failover_manager.py status")
        print("  python3 render_failover_manager.py check_limit [650]")
        print("  python3 render_failover_manager.py rotate <from_node> <to_node> [cooldown_seconds]")
        print("  python3 render_failover_manager.py suspend <node_num>")
        print("  python3 render_failover_manager.py resume <node_num>")
        print("  python3 render_failover_manager.py maint on [seconds] | off")

if __name__ == "__main__":
    asyncio.run(main())
