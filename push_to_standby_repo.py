#!/usr/bin/env python3
"""
push_to_standby_repo.py
Synchronizes render_standby_app.py to AAA2743/my-agy-fleet-standby as app.py
via the GitHub API using gh auth token.
Triggers Render Node 1 and Node 2 auto-deployments.
"""

import os
import sys
import json
import base64
import subprocess
import urllib.request
import urllib.error

REPO = "AAA0002/my-agy-fleet-standby"
FILE_PATH = "app.py"
LOCAL_FILE = "/root/projects/AAA_AUTO/render_standby_app.py"

def get_gh_token():
    res = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError("Failed to get gh token: " + res.stderr)
    return res.stdout.strip()

def main():
    token = get_gh_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "Antigravity-Agent"
    }

    print(f"[*] Reading local code from {LOCAL_FILE}...")
    with open(LOCAL_FILE, "rb") as f:
        content_bytes = f.read()

    b64_content = base64.b64encode(content_bytes).decode("ascii")

def push_file(headers, repo, remote_path, local_bytes, commit_msg):
    print(f"[*] Fetching current {remote_path} from {repo}...")
    get_url = f"https://api.github.com/repos/{repo}/contents/{remote_path}"
    req = urllib.request.Request(get_url, headers=headers)
    
    sha = None
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            sha = data.get("sha")
            print(f"[+] Current remote SHA for {remote_path}: {sha}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"[*] {remote_path} does not exist yet remotely, will create new.")
        else:
            raise RuntimeError(f"Error fetching remote file: {e.code} {e.reason}")

    b64_content = base64.b64encode(local_bytes).decode("ascii")
    commit_payload = {
        "message": commit_msg,
        "content": b64_content,
        "branch": "main"
    }
    if sha:
        commit_payload["sha"] = sha

    payload_json = json.dumps(commit_payload).encode("utf-8")
    put_req = urllib.request.Request(get_url, data=payload_json, headers=headers, method="PUT")

    print(f"[*] Pushing updated {remote_path} ({len(local_bytes)} bytes) to {repo}...")
    try:
        with urllib.request.urlopen(put_req) as resp:
            res_data = json.loads(resp.read().decode())
            new_sha = res_data.get("commit", {}).get("sha", "unknown")
            print(f"[+] SUCCESS! Committed {remote_path} to {repo}. New commit: {new_sha}")
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode()
        print(f"[-] HTTP Error {e.code}: {err_msg}")
        sys.exit(1)

def main():
    token = get_gh_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "Antigravity-Agent"
    }

    # 1. Push app.py
    with open(LOCAL_FILE, "rb") as f:
        app_bytes = f.read()
    push_file(headers, REPO, "app.py", app_bytes, "feat: deploy autonomous bot farming, interactive referral binding and mute engine")

    # 2. Push requirements.txt
    req_content = """fastapi==0.115.0
uvicorn==0.30.6
aiohttp==3.14.3
Telethon==1.45.0
python-dotenv==1.2.3
tonsdk>=1.0.15
web3>=6.0.0
pyaes==1.6.1
pyasn1==0.6.4
rsa==4.9.1
requests>=2.31.0
""".encode("utf-8")
    push_file(headers, REPO, "requirements.txt", req_content, "chore: requirements for standby node")

if __name__ == "__main__":
    main()
