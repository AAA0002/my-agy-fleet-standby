#!/usr/bin/env python3
"""
run_onboard_runner.py
Calls /api/onboard-new-bots on Render Cloud Standby for each worker account.
Honors the Zero Phone Load directive: All MTProto interaction, channel joins,
and button clicks execute in the cloud on Render Singapore.
"""

import json
import time
import urllib.request
import urllib.error

RENDER_URL = "https://my-agy-fleet-standby.onrender.com/api/onboard-new-bots"
SECRET_KEY = "agy_cf_secret_7d36994e_2026"
ACCOUNTS_FILE = "/root/projects/AAA_AUTO/accounts.json"

def main():
    with open(ACCOUNTS_FILE, "r") as f:
        accounts = json.load(f)

    # Master is index 0 (6727787768). Worker accounts are index 1 to 13.
    worker_accounts = [a for a in accounts if str(a.get("user_id")) != "6727787768"]

    print(f"🚀 Starting Cloud Onboarding for {len(worker_accounts)} Worker Accounts via Render...")
    headers = {
        "Authorization": f"Bearer {SECRET_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "Antigravity-Onboard-Runner"
    }

    all_results = []
    for i, acc in enumerate(worker_accounts, 1):
        uid = acc.get("user_id")
        name = acc.get("name")
        print(f"\n[{i}/{len(worker_accounts)}] Onboarding Account: {name} (ID: {uid}) on Render Cloud...")
        
        payload = json.dumps({"accounts": [acc]}).encode("utf-8")
        req = urllib.request.Request(RENDER_URL, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode())
                res_list = data.get("results", [])
                if res_list:
                    res = res_list[0]
                    bots = res.get("bots", {})
                    print(f"  ✅ Result for {name}:")
                    for b_name, b_stat in bots.items():
                        print(f"     • {b_name}: {b_stat}")
                    all_results.append(res)
                else:
                    print(f"  ⚠️ No results array returned: {data}")
        except urllib.error.HTTPError as e:
            print(f"  ❌ Render HTTP Error {e.code}: {e.read().decode()[:200]}")
        except Exception as e:
            print(f"  ❌ Error contacting Render: {e}")

        # Sleep briefly between accounts to be polite
        time.sleep(2)

    print("\n" + "="*50)
    print(f"🎉 Onboarding Completed across {len(all_results)} Accounts!")
    print("="*50)

if __name__ == "__main__":
    main()
