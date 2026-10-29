#!/usr/bin/env python3
"""
run_onboard_runner.py
Orchestrates targeted multi-step cloud onboarding across remaining worker accounts.
Honors Zero Phone Load directive: All MTProto channel joins, invite acceptance,
and verification clicks execute 100% in the cloud on Render Singapore.
"""

import os
import json
import time
import urllib.request
import urllib.error

RENDER_URL = os.getenv("RENDER_URL", "https://my-agy-fleet-standby-node3.onrender.com/api/onboard-new-bots")
SECRET_KEY = os.getenv("SECRET_KEY") or os.getenv("CF_SECRET_KEY", "")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
ACCOUNTS_FILE = os.getenv("ACCOUNTS_FILE") or os.path.join(PROJECT_ROOT, "accounts.json")
if not os.path.exists(ACCOUNTS_FILE):
    ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")

PENDING_UIDS = [
    8450010161,  # Nadim (@Asssssggj)
    8782429452,  # Kaitlyn (@Asssssklg)
    7734849205,  # Abid Hasan (@Abidhasan222)
    8025472383,  # Abid Hasan 2 (Abid)
    8851426148,  # Node 9 (@Akkffrr)
    8203342513,  # Node 10 (@AAlllAA2)
    8190649727,  # MD. ARIF HOSSAIN (@aaamah222)
    7487048946,  # Sanzida Shimu (@Sanzidashimu)
    8741547543,  # Abid 3 (@Abid_300)
    8727040932   # Raj Thakur (@Rajjjjjjjjjk)
]

def main():
    with open(ACCOUNTS_FILE, "r") as f:
        accounts = json.load(f)

    # Filter to pending accounts
    target_accounts = [a for a in accounts if a.get("user_id") in PENDING_UIDS]
    print(f"🚀 Processing Targeted Multi-Step Onboarding for {len(target_accounts)} Remaining Accounts...")

    headers = {
        "Authorization": f"Bearer {SECRET_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "Antigravity-Onboard-Runner"
    }

    verified_count = 0
    for i, acc in enumerate(target_accounts, 1):
        uid = acc.get("user_id")
        name = acc.get("name")
        print(f"\n[{i}/{len(target_accounts)}] Onboarding: {name} (ID: {uid}) on Render Cloud...")

        payload = json.dumps({"accounts": [acc]}).encode("utf-8")
        req = urllib.request.Request(RENDER_URL, data=payload, headers=headers, method="POST")

        try:
            # 240s generous timeout so all 7 bots complete their 6-turn dialogues
            with urllib.request.urlopen(req, timeout=240) as resp:
                data = json.loads(resp.read().decode())
                res_list = data.get("results", [])
                if res_list:
                    res = res_list[0]
                    bots = res.get("bots", {})
                    print(f"  ✅ Result for {name}:")
                    for b_name, b_stat in bots.items():
                        print(f"     • {b_name}: {b_stat}")
                    verified_count += 1
                else:
                    print(f"  ⚠️ No results returned: {data}")
        except urllib.error.HTTPError as e:
            print(f"  ❌ Render HTTP Error {e.code}: {e.read().decode()[:200]}")
        except Exception as e:
            print(f"  ❌ Error contacting Render: {e}")

        # Politeness delay between accounts
        time.sleep(2)

    print("\n" + "="*50)
    print(f"🎉 Completed Targeted Multi-Step Onboarding for {verified_count}/{len(target_accounts)} Accounts!")
    print("="*50)

if __name__ == "__main__":
    main()
