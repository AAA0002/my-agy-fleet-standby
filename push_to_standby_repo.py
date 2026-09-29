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

REPO = "AAA2743/my-agy-fleet-standby"
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

    print(f"[*] Fetching current {FILE_PATH} from {REPO}...")
    get_url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    req = urllib.request.Request(get_url, headers=headers)
    
    sha = None
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            sha = data.get("sha")
            print(f"[+] Current remote SHA: {sha}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print("[*] File does not exist yet remotely, will create new.")
        else:
            raise RuntimeError(f"Error fetching remote file: {e.code} {e.reason}")

    commit_payload = {
        "message": "feat: deploy 15-bot farming, interactive verification and onboarding endpoint to Render",
        "content": b64_content,
        "branch": "main"
    }
    if sha:
        commit_payload["sha"] = sha

    payload_json = json.dumps(commit_payload).encode("utf-8")
    put_req = urllib.request.Request(get_url, data=payload_json, headers=headers, method="PUT")

    print(f"[*] Pushing updated {FILE_PATH} ({len(content_bytes)} bytes) to {REPO}...")
    try:
        with urllib.request.urlopen(put_req) as resp:
            res_data = json.loads(resp.read().decode())
            new_sha = res_data.get("commit", {}).get("sha", "unknown")
            print(f"[+] SUCCESS! Committed new version to {REPO}. New commit: {new_sha}")
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode()
        print(f"[-] HTTP Error {e.code}: {err_msg}")
        sys.exit(1)

if __name__ == "__main__":
    main()
