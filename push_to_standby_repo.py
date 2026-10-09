#!/usr/bin/env python3
"""
push_to_standby_repo.py
Synchronizes render_standby_app.py as app.py to GitHub repo AAA0002/my-agy-fleet-standby,
triggering automatic deployment on Render Node 1 (Singapore) and Node 2 (Frankfurt).
"""

import os
import json
import base64
import hashlib
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
KORAM_PAT = "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"
REPOS = [
    ("AAA0002/my-agy-fleet-standby", PAT),
    ("koramshah2/my-agy-fleet-standby", KORAM_PAT)
]
FILE_PATH = "app.py"

def push_file(local_path: str, repo_path: str, commit_msg: str):
    if not os.path.exists(local_path):
        print(f"❌ Source file {local_path} not found.")
        return

    with open(local_path, "rb") as f:
        content_bytes = f.read()

    b64_content = base64.b64encode(content_bytes).decode("utf-8")

    for repo, pat in REPOS:
        if not pat:
            continue
        get_url = f"https://api.github.com/repos/{repo}/contents/{repo_path}"
        headers = {
            "Authorization": f"Bearer {pat}",
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/vnd.github.v3+json"
        }

        current_sha = None
        # 1. Fetch sha via git tree for efficiency and reliability on large files
        try:
            tree_req = urllib.request.Request(f"https://api.github.com/repos/{repo}/git/trees/main", headers=headers)
            with urllib.request.urlopen(tree_req, timeout=15) as resp:
                tree_data = json.loads(resp.read().decode())
                for item in tree_data.get("tree", []):
                    if item.get("path") == repo_path:
                        current_sha = item.get("sha")
                        break
        except Exception:
            pass

        # 2. Fallback to contents API if tree lookup did not find it
        if not current_sha:
            try:
                req = urllib.request.Request(get_url, headers=headers)
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode())
                    current_sha = data.get("sha")
            except Exception:
                pass

        local_blob_sha = hashlib.sha1(b"blob " + str(len(content_bytes)).encode() + b"\0" + content_bytes).hexdigest()
        if current_sha and current_sha == local_blob_sha:
            print(f"⏩ {repo_path} in {repo} is already up to date ({current_sha[:8]}).")
            continue

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
            with urllib.request.urlopen(req_put, timeout=30) as put_resp:
                res = json.loads(put_resp.read().decode())
                new_commit = res.get("commit", {}).get("sha", "")[:8]
                print(f"✅ Pushed {repo_path} to {repo} (Commit: {new_commit})!")
        except urllib.error.HTTPError as pe:
            err_body = pe.read().decode() if hasattr(pe, "read") else ""
            print(f"❌ Error pushing {repo_path} to {repo}: {pe} - {err_body}")
        except Exception as pe:
            print(f"❌ Error pushing {repo_path} to {repo}: {pe}")

def push_app():
    push_file(STANDBY_SRC, "app.py", "feat: 8-bot fleet auto-farming, multi-node Render standby mesh")
    req_file = os.path.join(BASE_DIR, "requirements.txt")
    if os.path.exists(req_file):
        push_file(req_file, "requirements.txt", "deps: update dependencies")
    
    # Trigger Render Node 1 deploy (Singapore - Coz1)
    node1_key = env.get("RENDER_API_KEY_1", "rnd_cGQwvG9J4pe6Rpf06sRMb4pzR6v1")
    srv_node1 = "srv-damuhkmgekts73f1osag"
    try:
        req_dep1 = urllib.request.Request(
            f"https://api.render.com/v1/services/{srv_node1}/deploys",
            data=json.dumps({"clearCache": "do_not_clear"}).encode(),
            headers={"Authorization": f"Bearer {node1_key}", "Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req_dep1, timeout=15) as d_resp:
            d_data = json.loads(d_resp.read().decode())
            print(f"🚀 Render Node 1 (Singapore) deployment triggered: {d_data.get('id')}")
    except Exception as de:
        print(f"Note triggering Render Node 1 deploy: {de}")

    # Trigger Render Node 2 deploy (Frankfurt - Abid)
    node2_key = env.get("RENDER_API_KEY_2", "rnd_KnVaiOw93SKa4fSTrEURwZrP0UaB")
    srv_node2 = "srv-dan5q00ae00c73djummg"
    try:
        req_dep2 = urllib.request.Request(
            f"https://api.render.com/v1/services/{srv_node2}/deploys",
            data=json.dumps({"clearCache": "do_not_clear"}).encode(),
            headers={"Authorization": f"Bearer {node2_key}", "Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req_dep2, timeout=15) as d_resp:
            d_data = json.loads(d_resp.read().decode())
            print(f"🚀 Render Node 2 (Frankfurt) deployment triggered: {d_data.get('id')}")
    except Exception as de:
        print(f"Note triggering Render Node 2 deploy: {de}")

    # Trigger Render Node 3 deploy (Oregon - Koram)
    node3_key = env.get("RENDER_API_KEY", "rnd_PqsurfX5D9blSaEEuEDDAUcl393y")
    srv_node3 = "srv-db437o3tqb8s73dt4erg"
    try:
        req_dep3 = urllib.request.Request(
            f"https://api.render.com/v1/services/{srv_node3}/deploys",
            data=json.dumps({"clearCache": "do_not_clear"}).encode(),
            headers={"Authorization": f"Bearer {node3_key}", "Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req_dep3, timeout=15) as d_resp:
            d_data = json.loads(d_resp.read().decode())
            print(f"🚀 Render Node 3 (Oregon) deployment triggered: {d_data.get('id')}")
    except Exception as de:
        print(f"Note triggering Render Node 3 deploy: {de}")

if __name__ == "__main__":
    push_app()
