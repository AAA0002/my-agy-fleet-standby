#!/usr/bin/env python3
"""
deploy_all_pages.py
Deploys Cloudflare Pages across all 5 accounts:
- Node 1 (korimhaji210): public_admin -> aaa-admin-portal (Admin Dashboard)
- Node 5 (aaaai-engine): public_admin -> aaa-ai-engine (Admin Dashboard Mirror)
- Node 4 (aaafreeai): public_ads -> atf-miner-app (Primary Watch Ads)
- Node 2 (Koramshah2): public_ads -> aaa-watch-ads (Watch Ads Mirror 2)
- Node 3 (coz1gameh3): public_ads -> aaa-community-ads (Watch Ads Mirror 3)
"""

import os
import subprocess
import sys

PAGES_CONFIGS = [
    {
        "name": "Node 1 - aaa-admin-portal (Admin Dashboard)",
        "account_id": "c9f92ab4a8b26b15f958ac25c22300bc",
        "email": "korimhaji210@gmail.com",
        "api_key": "cfk_1NzkotzLPy3htYaju8Ha6KolPDuNCMGiECzsyx6Gb7e6ad9f",
        "project": "aaa-admin-portal",
        "folder": "public_admin",
        "type": "admin"
    },
    {
        "name": "Node 5 - aaa-ai-engine (Admin Dashboard Mirror)",
        "account_id": "da98cfb7cca333391bb349333f294d0f",
        "api_token": "cfat_o447c1qlRZp5Lr0rHR4JjyMoLNKMkksaqnaZBDYF06cb8be4",
        "project": "aaa-ai-engine",
        "folder": "public_admin",
        "type": "admin"
    },
    {
        "name": "Node 4 - atf-miner-app (Primary Watch Ads)",
        "account_id": "abbe3cc008ebb9dd029ded333fef6e9f",
        "email": "aaafreeai@gmail.com",
        "api_key": "cfk_a3KGc7NbioJlm6oy2vE7F2qzPiluqdx6T64rGVaX3f8eb8d5",
        "project": "atf-miner-app",
        "folder": "public_ads",
        "type": "ads"
    },
    {
        "name": "Node 2 - aaa-watch-ads (Watch Ads Mirror 2)",
        "account_id": "cf47efdd654cdb07ffe03d1361583f12",
        "email": "Koramshah2@gmail.com",
        "api_key": "cfk_6goOEQC3vW220yQbYMwD1P9xsLUdFHjvo4wOYn5A7d36994e",
        "project": "aaa-watch-ads",
        "folder": "public_ads",
        "type": "ads"
    },
    {
        "name": "Node 3 - aaa-community-ads (Watch Ads Mirror 3)",
        "account_id": "e1bfe1206dd7195f89591a9200105f1c",
        "email": "coz1gameh3@gmail.com",
        "api_key": "cfk_g2He8oRyc1GQbnGziVHxsv7Opopk7ucJZCEh2KfD715c0e54",
        "project": "aaa-community-ads",
        "folder": "public_ads",
        "type": "ads"
    }
]

def deploy_pages_account(cfg):
    print(f"\n==================================================")
    print(f"  Deploying {cfg['name']} ({cfg['folder']} -> {cfg['project']})")
    print(f"==================================================")

    env = os.environ.copy()
    env["CLOUDFLARE_ACCOUNT_ID"] = cfg["account_id"]
    if "api_token" in cfg:
        env["CLOUDFLARE_API_TOKEN"] = cfg["api_token"]
        env.pop("CLOUDFLARE_API_KEY", None)
        env.pop("CLOUDFLARE_EMAIL", None)
    else:
        env["CLOUDFLARE_EMAIL"] = cfg["email"]
        env["CLOUDFLARE_API_KEY"] = cfg["api_key"]
        env.pop("CLOUDFLARE_API_TOKEN", None)

    cmd = [
        "npx", "wrangler", "pages", "deploy", cfg["folder"],
        f"--project-name={cfg['project']}",
        "--commit-dirty=true"
    ]

    try:
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
        print(f"✅ [{cfg['project']}] Deployed successfully!")
        for line in proc.stdout.splitlines():
            if "Deployment complete" in line or "https://" in line:
                print(f"   {line.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ [{cfg['project']}] Deployment failed: {e.stderr or e.stdout}")
        return False

def main():
    print("=" * 60)
    print("  MY AGY AI — Multi-Account Cloudflare Pages Deployer")
    print("  Separation: Admin Dashboards (Nodes 1,5) | Watch Ads (Nodes 4,2,3)")
    print("=" * 60)

    success = 0
    for cfg in PAGES_CONFIGS:
        ok = deploy_pages_account(cfg)
        if ok:
            success += 1

    print(f"\n==================================================")
    print(f"  Result: {success}/{len(PAGES_CONFIGS)} Cloudflare Pages Deployed!")
    print(f"==================================================")

if __name__ == "__main__":
    main()
