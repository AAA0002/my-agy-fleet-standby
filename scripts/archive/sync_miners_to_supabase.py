#!/usr/bin/env python3
"""
Syncs community miners from Upstash Redis to Supabase Postgres (table community_miners)
"""
import os
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

UPSTASH_URL = os.getenv("UPSTASH_REDIS_REST_URL", "https://internal-dodo-83852.upstash.io")
UPSTASH_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://znbbaozpevurvbfkxakz.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

def sync_miners():
    upstash_headers = {'Authorization': f'Bearer {UPSTASH_TOKEN}'}
    supabase_headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates'
    }

    # 1. Fetch all user keys
    req_keys = urllib.request.Request(f'{UPSTASH_URL}/keys/ub_user:*', headers=upstash_headers)
    with urllib.request.urlopen(req_keys) as resp:
        keys_data = json.loads(resp.read().decode('utf-8'))
        keys = keys_data.get('result', [])

    print(f"Found {len(keys)} community miner profiles in Upstash.")
    records = []

    for k in keys:
        req_val = urllib.request.Request(f'{UPSTASH_URL}/get/{k}', headers=upstash_headers)
        with urllib.request.urlopen(req_val) as resp:
            val_data = json.loads(resp.read().decode('utf-8'))
            raw = val_data.get('result')
            if not raw:
                continue
            prof = json.loads(raw) if isinstance(raw, str) else raw

            uid = k.replace("ub_user:", "").strip()
            records.append({
                "id": str(uid),
                "username": prof.get("username", ""),
                "first_name": prof.get("first_name", ""),
                "points": int(prof.get("points", 0)),
                "slots": int(prof.get("slots", 1)),
                "temp_slots": int(prof.get("temp_slots", 0)),
                "farming_active": bool(prof.get("farming_active", True)),
                "daily_streak": int(prof.get("daily_streak", 0)),
                "ad_count": int(prof.get("ad_count", 0)),
                "accounts": prof.get("accounts", []),
                "profile_data": prof
            })

    if not records:
        print("No records to sync.")
        return

    # Upsert to Supabase
    req_upsert = urllib.request.Request(
        f'{SUPABASE_URL}/rest/v1/community_miners',
        data=json.dumps(records).encode('utf-8'),
        headers=supabase_headers,
        method='POST'
    )
    try:
        with urllib.request.urlopen(req_upsert) as resp:
            print(f"✅ Successfully synced {len(records)} community miners to Supabase Postgres (HTTP {resp.status})!")
    except urllib.error.HTTPError as e:
        print(f"❌ Supabase upsert error: {e.code} - {e.read().decode('utf-8')}")

if __name__ == "__main__":
    sync_miners()
