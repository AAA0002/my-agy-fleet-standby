#!/usr/bin/env python3
"""
trigger_circleci_failover.py
Automated & Manual Failover Dispatcher to CircleCI for MY AGY AI Fleet.
Triggers CircleCI turnstile solver pipeline when GitHub Actions is unavailable or fails.
"""

import os
import sys
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

REPO_OWNER = os.getenv("GITHUB_REPOSITORY_OWNER", "AAA0002")
REPO_NAME = "ATL"
CIRCLECI_TOKEN = os.getenv("CIRCLECI_TOKEN", "")

def trigger_failover():
    if not CIRCLECI_TOKEN:
        print("⚠️ CIRCLECI_TOKEN not found in environment.")
        print("To enable CircleCI failover dispatch:")
        print("1. Generate a Personal API Token on https://app.circleci.com/settings/user/tokens")
        print("2. Add CIRCLECI_TOKEN to your .env file or GitHub / Cloudflare Secrets.")
        return False

    url = f"https://circleci.com/api/v2/project/gh/{REPO_OWNER}/{REPO_NAME}/pipeline"
    payload = json.dumps({
        "parameters": {
            "is_failover": True
        }
    }).encode("utf-8")

    headers = {
        "Circle-Token": CIRCLECI_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            pipeline_id = data.get("id")
            pipeline_state = data.get("state")
            print(f"🚀 [CircleCI Failover] Successfully dispatched pipeline: {pipeline_id} (State: {pipeline_state})")
            return True
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        print(f"❌ [CircleCI Failover] HTTP {e.code} error: {err_msg}")
        return False
    except Exception as e:
        print(f"❌ [CircleCI Failover] Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("⚡ Triggering CircleCI Failover Turnstile Pipeline...")
    success = trigger_failover()
    sys.exit(0 if success else 1)
