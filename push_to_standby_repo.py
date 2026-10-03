#!/usr/bin/env python3
"""
push_to_standby_repo.py
Synchronizes render_standby_app.py as app.py to GitHub repo AAA0002/my-agy-fleet-standby,
triggering automatic deployment on Render Node 1 (Singapore) and Node 2 (Frankfurt).
"""

import os
import json
import base64
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STANDBY_SRC = os.path.join(BASE_DIR, "render_standby_app.py")

# Read credentials from .env
env = {}
with open(os.path.join(BASE_DIR, ".env")) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")

PAT = env.get("GITHUB_USERBOT_PAT") or env.get("GITHUB_FINE_GRAINED_PAT")
REPO = "AAA0002/my-agy-fleet-standby"
FILE_PATH = "app.py"

def push_app():
    if not os.path.exists(STANDBY_SRC):
        print(f"❌ Source file {STANDBY_SRC} not found.")
        return

    with open(STANDBY_SRC, "rb") as f:
        content_bytes = f.read()

    b64_content = base64.b64encode(content_bytes).decode("utf-8")

    # 1. Get current SHA
    get_url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"Bearer {PAT}",
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/vnd.github.v3+json"
    }

    req = urllib.request.Request(get_url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            current_sha = data.get("sha")
    except Exception as e:
        print(f"⚠️ Could not get SHA (might be new file): {e}")
        current_sha = None

    # 2. Update file on GitHub
    put_data = {
        "message": "feat: dynamic isolated wallet routing across AI Lab, Ainovum, BNB bot, and MRG TON wallet binding",
        "content": b64_content
    }
    if current_sha:
        put_data["sha"] = current_sha

    req_put = urllib.request.Request(
        get_url,
        data=json.dumps(put_data).encode("utf-8"),
        headers=headers,
        method="PUT"
    )

    try:
        with urllib.request.urlopen(req_put) as put_resp:
            res = json.loads(put_resp.read().decode())
            new_commit = res.get("commit", {}).get("sha", "")[:8]
            print(f"✅ Successfully pushed updated app.py to {REPO} (Commit: {new_commit})!")
            print("🚀 Render Node 1 (Singapore) and Node 2 (Frankfurt) will auto-deploy.")
    except Exception as pe:
        print(f"❌ Error pushing to GitHub: {pe}")

if __name__ == "__main__":
    push_app()
