#!/usr/bin/env python3
"""
push_to_standby_repo.py
Synchronizes canonical app.py to GitHub repo AAA0002/my-agy-fleet-standby,
triggering automatic deployment on Render Node 1 (Singapore) and Node 2 (Frankfurt).
"""

import os
import json
import base64
import hashlib
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STANDBY_SRC = os.path.join(BASE_DIR, "app.py")

# Read credentials from .env
env = {}
with open(os.path.join(BASE_DIR, ".env")) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")

def get_valid_github_pat() -> str:
    cred_path = os.path.expanduser("~/.git-credentials")
    if os.path.exists(cred_path):
        try:
            with open(cred_path, "r", encoding="utf-8") as f:
                for line in f:
                    if "@github.com" in line:
                        auth_part = line.strip().split("@github.com")[0].replace("https://", "")
                        return auth_part.split(":")[1] if ":" in auth_part else auth_part
        except Exception:
            pass
    return env.get("GITHUB_USERBOT_PAT") or env.get("GITHUB_FINE_GRAINED_PAT") or ""

PAT = get_valid_github_pat()
REPOS = [
    ("AAA0002/my-agy-fleet-standby", PAT)
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
            with urllib.request.urlopen(req_put, timeout=60) as put_resp:
                res = json.loads(put_resp.read().decode())
                new_commit = res.get("commit", {}).get("sha", "")[:8]
                print(f"✅ Pushed {repo_path} to {repo} (Commit: {new_commit})!")
        except urllib.error.HTTPError as pe:
            err_body = pe.read().decode() if hasattr(pe, "read") else ""
            print(f"❌ Error pushing {repo_path} to {repo}: {pe} - {err_body}")
        except Exception as pe:
            print(f"❌ Error pushing {repo_path} to {repo}: {pe}")

def push_app():
    push_file(STANDBY_SRC, "app.py", "feat: 8-bot fleet auto-farming (MRG, ATF, Victors, Kynex, Diggo, Pepe, Adx, Chicken)")
    kynex_file = os.path.join(BASE_DIR, "kynex_miner.py")
    if os.path.exists(kynex_file):
        push_file(kynex_file, "kynex_miner.py", "feat: Kynex Network cloud mining engine")
    reg_file = os.path.join(BASE_DIR, "bot_registry.py")
    if os.path.exists(reg_file):
        push_file(reg_file, "bot_registry.py", "feat: 8-bot fleet registry single source of truth")
    arc_file = os.path.join(BASE_DIR, "victors_arcade_solver.py")
    if os.path.exists(arc_file):
        push_file(arc_file, "victors_arcade_solver.py", "feat: Victor's Company Deep Mine arcade solver engine")
    sidetasks_file = os.path.join(BASE_DIR, "finish_all_fleet_sidetasks.py")
    if os.path.exists(sidetasks_file):
        push_file(sidetasks_file, "finish_all_fleet_sidetasks.py", "feat: 8-bot fleet side tasks auto-sweep engine")
    mrg_solver = os.path.join(BASE_DIR, "mrg_turnstile_solver.py")
    if os.path.exists(mrg_solver):
        push_file(mrg_solver, "mrg_turnstile_solver.py", "feat: MRG total holding level qualification and solver")
    login_acc = os.path.join(BASE_DIR, "login_account.py")
    if os.path.exists(login_acc):
        push_file(login_acc, "login_account.py", "feat: Dual-layer Telegram /start and WebApp start_param referral binding")
    vic_sb = os.path.join(BASE_DIR, "victors_sb_solver.py")
    if os.path.exists(vic_sb):
        push_file(vic_sb, "victors_sb_solver.py", "feat: Victor's Company CDP stealth Turnstile solver and Level 1 unlock")
    vic_cpl = os.path.join(BASE_DIR, "victors_cloud_phone_launcher.py")
    if os.path.exists(vic_cpl):
        push_file(vic_cpl, "victors_cloud_phone_launcher.py", "feat: Victor's Company cloud phone launcher")
    req_file = os.path.join(BASE_DIR, "requirements.txt")
    if os.path.exists(req_file):
        push_file(req_file, "requirements.txt", "deps: update dependencies")
    clean_file = os.path.join(BASE_DIR, "clean_up_system.py")
    if os.path.exists(clean_file):
        push_file(clean_file, "clean_up_system.py", "feat: autonomous multi-tier clean up engine")
    rct_f = os.path.join(BASE_DIR, "refresh_cloud_tokens.py")
    if os.path.exists(rct_f):
        push_file(rct_f, "refresh_cloud_tokens.py", "feat: 10-bot cloud token refresher")
    emt_f = os.path.join(BASE_DIR, "extract_all_missing_fleet_tokens.py")
    if os.path.exists(emt_f):
        push_file(emt_f, "extract_all_missing_fleet_tokens.py", "feat: 10-bot missing tokens batch extractor")
    
    # Strictly Pin Deployment EXCLUSIVELY to Render Node 2 (Frankfurt - Abid)
    # Node 1 (Singapore) and Node 3 (Oregon) are suspended to guarantee ZERO IP collisions
    node2_key = env.get("RENDER_API_KEY_2", "")
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

if __name__ == "__main__":
    push_app()
