#!/usr/bin/env python3
"""
Syncs fleet accounts and payouts to Supabase Managed Cloud Postgres.
"""
import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://znbbaozpevurvbfkxakz.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in locals() else os.getcwd()

def sync_accounts():
    accounts_file = os.path.join(BASE_DIR, "accounts.json")
    if not os.path.exists(accounts_file):
        print("No accounts.json found.")
        return
    with open(accounts_file, "r", encoding="utf-8") as f:
        accounts = json.load(f)

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }

    records = []
    for acc in accounts:
        user_id = str(acc.get("user_id", acc.get("phone", "")))
        if not user_id:
            continue
        records.append({
            "id": user_id,
            "phone": acc.get("phone", ""),
            "status": "active" if acc.get("session_string") else "pending",
            "data": {
                "name": acc.get("name", ""),
                "username": acc.get("username", ""),
                "stones_wallet": acc.get("stones_wallet", ""),
                "mrg_wallet": acc.get("mrg_wallet", ""),
                "art_wallet": acc.get("art_wallet", "")
            }
        })

    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/fleet_accounts",
        data=json.dumps(records).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"✅ Supabase synced {len(records)} accounts successfully (HTTP {resp.status})")
    except Exception as e:
        print(f"⚠️ Supabase sync error: {e}")

if __name__ == "__main__":
    sync_accounts()
