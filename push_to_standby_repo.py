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

def push_file(local_path: str, repo_path: str, commit_msg: str):
    if not os.path.exists(local_path):
        print(f"❌ Source file {local_path} not found.")
        return

    with open(local_path, "rb") as f:
        content_bytes = f.read()

    b64_content = base64.b64encode(content_bytes).decode("utf-8")

    get_url = f"https://api.github.com/repos/{REPO}/contents/{repo_path}"
    headers = {
        "Authorization": f"Bearer {PAT}",
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/vnd.github.v3+json"
    }

    req = urllib.request.Request(get_url, headers=headers)
    current_sha = None
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            current_sha = data.get("sha")
    except Exception as e:
        pass

    put_data = {
        "message": commit_msg,
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
            print(f"✅ Pushed {repo_path} to {REPO} (Commit: {new_commit})!")
    except Exception as pe:
        print(f"❌ Error pushing {repo_path} to GitHub: {pe}")

def push_app():
    push_file(STANDBY_SRC, "app.py", "feat: auto wallet generation, bot binding, and farming for new accounts")
    req_file = os.path.join(BASE_DIR, "requirements.txt")
    if os.path.exists(req_file):
        push_file(req_file, "requirements.txt", "deps: add ecdsa and base58")
    print("🚀 Render Node 1 (Singapore) and Node 2 (Frankfurt) will auto-deploy.")

if __name__ == "__main__":
    push_app()
