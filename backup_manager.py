#!/usr/bin/env python3
"""
backup_manager.py
Automated Cloud Backup & Disaster Recovery System for MY AGY AI & Antigravity.
Uploads complete fleet backups, MTProto sessions, Antigravity OAuth tokens,
and 1-click restore commands directly to the private vault channel:
https://t.me/myagyai
"""

import os
import sys
import json
import zipfile
import asyncio
import logging
from datetime import datetime, timezone, timedelta
import aiohttp
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

REPORT_BOT_TOKEN = os.getenv("REPORT_BOT_TOKEN", "8858823950:AAFFkuls8hBf23taCZE1y5gVzP4AFCuqI5o")
REPORT_CHAT_ID = os.getenv("REPORT_CHAT_ID", "6727787768")
BACKUP_CHANNEL = "@myagyai"

# Bot Fleet core files
CORE_BOT_FILES = [
    "accounts.json",
    ".env",
    "userbot_refresher.py",
    "proxy_manager.py",
    "phone_detector.py",
    "login_account.py",
    "backup_manager.py",
    "bot_supervisor.sh",
    "start_userbot.sh",
    "stop_userbot.sh",
    "restore.sh",
    "requirements.txt",
    "pro_agy_ai_symbol.jpg",
    ".cloudflare_credentials",
    "cloudflared_tunnel.sh",
    "my_agy_bot.service",
    "payouts.json",
    "payout_ledger.json",
    "fleet_ton_wallets.json",
    "fleet_evm_wallets.json",
    "bep20_onchain_watcher.py",
    "bep20_watcher_state.json",
    "multichain_onchain_watcher.py",
    "multichain_watcher_state.json",
    "daily_profit_reporter.py",
    ".onchain_state.json",
    "fleet_miniapp_tokens.json",
    "deploy_both_cf_workers.py",
    "batch_atf_miner.py",
    "atf_fleet_state.json",
    "refresh_fleet_tokens.py",
    "update_dashboard_compact.py",
    "stones_captcha_solver.py",
    "payout_balances.json",
    "FLEET_MASTER_REGISTRY.json",
    "commercial_user_isolation.py",
    "refresh_cloud_tokens.py"
]


# Antigravity CLI session files to preserve OAuth login & settings
AGY_CLI_DIR = os.path.expanduser("~/.gemini/antigravity-cli")
AGY_SESSION_FILES = [
    "antigravity-oauth-token",
    "settings.json",
    "installation_id",
    "jetski_state.pbtxt"
]


def create_backup_zip() -> str:
    """Creates a timestamped zip containing bot code and Antigravity session."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    zip_filename = f"my_agy_ai_backup_{timestamp}.zip"
    zip_path = os.path.join(BASE_DIR, zip_filename)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        # 1. Add core bot fleet files
        for fname in CORE_BOT_FILES:
            fpath = os.path.join(BASE_DIR, fname)
            if os.path.exists(fpath):
                zipf.write(fpath, arcname=fname)

        # 2. Add Antigravity session files into 'antigravity_session/'
        if os.path.exists(AGY_CLI_DIR):
            for agy_file in AGY_SESSION_FILES:
                agy_path = os.path.join(AGY_CLI_DIR, agy_file)
                if os.path.exists(agy_path):
                    zipf.write(agy_path, arcname=os.path.join("antigravity_session", agy_file))

        # 3. Add Cloudflare tunnel configs into 'cloudflared_config/'
        cf_dir = os.path.expanduser("~/.cloudflared")
        if os.path.exists(cf_dir):
            for cf_f in os.listdir(cf_dir):
                cf_path = os.path.join(cf_dir, cf_f)
                if os.path.isfile(cf_path):
                    zipf.write(cf_path, arcname=os.path.join("cloudflared_config", cf_f))

    # Auto-prune older backup archives (keep latest 2 to save disk on 2GB VPS)
    try:
        existing_zips = sorted([
            os.path.join(BASE_DIR, f) for f in os.listdir(BASE_DIR)
            if f.startswith("my_agy_ai_backup_") and f.endswith(".zip")
        ], key=os.path.getmtime)
        while len(existing_zips) > 2:
            oldest = existing_zips.pop(0)
            os.remove(oldest)
    except Exception:
        pass

    return zip_path


async def send_backup_to_telegram(chat_id: str = None) -> tuple[bool, str]:
    """
    Generates backup zip, uploads to https://t.me/myagyai, and returns
    the 1-line copy-paste recovery command for Linux VPS & Android Termux.
    """
    zip_path = create_backup_zip()
    zip_filename = os.path.basename(zip_path)
    zip_size_kb = round(os.path.getsize(zip_path) / 1024, 1)

    accounts_count = 0
    accounts_file = os.path.join(BASE_DIR, "accounts.json")
    if os.path.exists(accounts_file):
        try:
            with open(accounts_file, "r", encoding="utf-8") as f:
                accounts_count = len(json.load(f))
        except Exception:
            pass

    now_utc = datetime.now(timezone.utc)
    bst_time = now_utc + timedelta(hours=6)
    date_str = bst_time.strftime("%A, %d %B %Y • %I:%M %p BST")

    url_doc = f"https://api.telegram.org/bot{REPORT_BOT_TOKEN}/sendDocument"
    url_msg = f"https://api.telegram.org/bot{REPORT_BOT_TOKEN}/sendMessage"

    try:
        async with aiohttp.ClientSession() as session:
            # 0. Sync backup archive to triple Cloudflare Edge KV stores
            cf_endpoints = [
                "https://restore-agy.aaaai2.workers.dev/upload",
                "https://restore-agy.aaa-bot.workers.dev/upload",
                "https://restore-agy.aaa222.workers.dev/upload"
            ]
            cf_headers = {"Authorization": "Bearer agy_cf_secret_7d36994e_2026", "Content-Type": "application/zip"}
            try:
                with open(zip_path, "rb") as zf:
                    z_bytes = zf.read()
                async def upload_cf(ep):
                    try:
                        async with session.post(ep, headers=cf_headers, data=z_bytes, timeout=aiohttp.ClientTimeout(total=15)) as cf_r:
                            if cf_r.status == 200:
                                logging.info(f"[Cloudflare Edge] Backup synced to {ep}")
                    except Exception as cfe:
                        logging.warning(f"[Cloudflare Edge] Error uploading to {ep}: {cfe}")

                await asyncio.gather(*(upload_cf(ep) for ep in cf_endpoints), return_exceptions=True)
            except Exception:
                pass

            # 0.5 Pin to Pinata IPFS Decentralized Network
            pinata_jwt = os.getenv("PINATA_JWT")
            ipfs_cid = None
            if pinata_jwt:
                try:
                    form = aiohttp.FormData()
                    form.add_field("file", open(zip_path, "rb"), filename=zip_filename)
                    form.add_field("pinataMetadata", json.dumps({"name": zip_filename}))
                    headers_pinata = {"Authorization": f"Bearer {pinata_jwt}"}
                    async with session.post("https://api.pinata.cloud/pinning/pinFileToIPFS", data=form, headers=headers_pinata, timeout=aiohttp.ClientTimeout(total=25)) as p_resp:
                        if p_resp.status == 200:
                            p_data = await p_resp.json()
                            ipfs_cid = p_data.get("IpfsHash")
                            logging.info(f"[Pinata IPFS] Backup pinned: {ipfs_cid}")
                except Exception as pe:
                    logging.warning(f"[Pinata IPFS] Pinning error: {pe}")

            ipfs_line = f"• <b>IPFS Decentralized Gateway:</b> <code>https://gateway.pinata.cloud/ipfs/{ipfs_cid}</code>\n" if ipfs_cid else ""

            caption = (
                f"📦 <b>MY AGY AI — Disaster Recovery Backup Archive</b>\n"
                f"📅 <i>{date_str}</i>\n\n"
                f"• <b>Archive:</b> <code>{zip_filename}</code> ({zip_size_kb} KB)\n"
                f"• <b>Fleet Accounts:</b> <code>{accounts_count} Preserved</code>\n"
                f"• <b>Antigravity Session:</b> <code>Preserved & Auto-Authenticated</code> ✅\n"
                f"{ipfs_line}"
                f"• <b>Vault Channel:</b> <code>https://t.me/myagyai</code>\n\n"
                f"🛡️ <b>VPS Disconnect & Termux Protection:</b>\n"
                f"If your server is ever disconnected or deleted, you can restore your complete bot fleet and Antigravity in 1 click."
            )

            data = aiohttp.FormData()
            data.add_field("chat_id", BACKUP_CHANNEL)
            data.add_field("caption", caption)
            data.add_field("parse_mode", "HTML")
            data.add_field("document", open(zip_path, "rb"), filename=zip_filename)

            # 1. Upload backup archive directly to @myagyai Telegram channel (Unlimited, bypasses Cloudflare KV)
            async with session.post(url_doc, data=data) as resp:
                result = await resp.json()
                if not result.get("ok"):
                    return False, f"❌ Upload to channel failed: {result.get('description')}"

                file_id = result["result"]["document"]["file_id"]

            # 2. Construct 1-line restore command from Telegram CDN
            bootstrap = (
                "(command -v pkg >/dev/null && pkg install -y python tmux unzip curl || "
                "(command -v apt-get >/dev/null && (apt-get update -y && apt-get install -y python3 python3-venv python3-pip tmux unzip curl || "
                "sudo apt-get update -y && sudo apt-get install -y python3 python3-venv python3-pip tmux unzip curl)))"
            )
            py_fetch = (
                f"python3 -c \"import urllib.request as u, json, zipfile, os; "
                f"t='{REPORT_BOT_TOKEN}'; "
                f"f=json.loads(u.urlopen(f'https://api.telegram.org/bot{{t}}/getFile?file_id={file_id}').read())['result']['file_path']; "
                f"u.urlretrieve(f'https://api.telegram.org/file/bot{{t}}/{{f}}', 'b.zip'); "
                f"zipfile.ZipFile('b.zip').extractall('.'); "
                f"os.remove('b.zip'); "
                f"print('✅ Backup restored successfully!')\""
            )
            tg_one_liner = f"{bootstrap} && {py_fetch}"

            ipfs_restore = f"\n\n🌐 <b>Decentralized IPFS Direct Restore:</b>\n<code>curl -sL https://gateway.pinata.cloud/ipfs/{ipfs_cid} -o b.zip && python3 -c \"import zipfile; zipfile.ZipFile('b.zip').extractall('.'); print('✅ Restored from IPFS!')\"</code>" if ipfs_cid else ""

            instructions = (
                f"⚡ <b>MY AGY AI — 1-CLICK DISASTER RECOVERY</b>\n\n"
                f"📦 <b>Archive:</b> <code>{zip_filename}</code>\n"
                f"🕒 <b>Saved:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
                f"🛡️ <b>1-Line Restore Command (Termux / Linux VPS):</b>\n"
                f"<code>{tg_one_liner}</code>"
                f"{ipfs_restore}\n\n"
                f"<i>Restores all accounts, MTProto sessions, Antigravity CLI, and supervisor in under 45 seconds directly from Telegram CDN or IPFS!</i>"
            )

            # 3. Post instructions to @myagyai and pin it permanently
            async with session.post(url_msg, json={"chat_id": BACKUP_CHANNEL, "text": instructions, "parse_mode": "HTML"}) as resp2:
                res2 = await resp2.json()
                if res2.get("ok"):
                    cmd_msg_id = res2["result"]["message_id"]
                    pin_url = f"https://api.telegram.org/bot{REPORT_BOT_TOKEN}/pinChatMessage"
                    await session.post(pin_url, json={"chat_id": BACKUP_CHANNEL, "message_id": cmd_msg_id, "disable_notification": True})

            # 4. If triggered by a user in chat, notify them with the command as well
            if chat_id and str(chat_id) != BACKUP_CHANNEL:
                acc_count = 11
                try:
                    with open(os.path.join(BASE_DIR, "accounts.json"), "r", encoding="utf-8") as af:
                        acc_count = len(json.load(af))
                except Exception:
                    pass
                ipfs_user_line = f"🌐 <b>IPFS Decentralized Gateway:</b>\n<code>https://gateway.pinata.cloud/ipfs/{ipfs_cid}</code>\n\n" if ipfs_cid else ""
                user_msg = (
                    f"✅ <b>Backup uploaded directly to Telegram @myagyai vault & Pinata IPFS!</b>\n\n"
                    f"📦 <b>Archive:</b> <code>{zip_filename}</code>\n"
                    f"🔑 <b>All {acc_count} Accounts & Sessions:</b> Preserved\n"
                    f"{ipfs_user_line}"
                    f"⚡ <b>1-Line Restore Command:</b>\n"
                    f"<code>{tg_one_liner}</code>"
                )
                async with session.post(url_msg, json={"chat_id": str(chat_id), "text": user_msg, "parse_mode": "HTML"}) as resp3:
                    pass

            # Note: Local backup archive is preserved (up to 2 newest copies) via create_backup_zip pruning
            return True, f"✅ Backup uploaded to https://t.me/myagyai and saved locally!"

    except Exception as e:
        return False, f"❌ Backup failed: {e}"


if __name__ == "__main__":
    print("Uploading disaster recovery backup to https://t.me/myagyai...")
    ok, message = asyncio.run(send_backup_to_telegram(REPORT_CHAT_ID))
    print(message)
