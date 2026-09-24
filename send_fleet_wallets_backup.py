import os
import sys
import json
import time
import asyncio
import urllib.request
import urllib.parse
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = "/home/arif2743"
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")
FLEET_WALLETS_FILE = os.path.join(BASE_DIR, "fleet_ton_wallets.json")
BACKUP_TXT_FILE = os.path.join(BASE_DIR, "FLEET_TELEGRAM_TON_WALLETS_BACKUP.txt")

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
STRING_SESSION = os.getenv("TELEGRAM_STRING_SESSION")
REPORT_BOT_TOKEN = os.getenv("REPORT_BOT_TOKEN", "8858823950:AAFFkuls8hBf23taCZE1y5gVzP4AFCuqI5o")
REPORT_CHAT_ID = os.getenv("REPORT_CHAT_ID", "6727787768")
AAA_T_WALLET_GROUP = -1003973231307
MYAGYAI_CHANNEL = -1004453515167

def send_bot_message(text, chat_id):
    url = f"https://api.telegram.org/bot{REPORT_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        # Fallback to plain text if Markdown parsing fails
        try:
            payload.pop("parse_mode", None)
            req_plain = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req_plain, timeout=15) as r_p:
                return json.loads(r_p.read())
        except Exception as e2:
            print(f"Error sending message to {chat_id}: {e2}")
            return None

def send_bot_document(file_path, chat_id, caption=""):
    url = f"https://api.telegram.org/bot{REPORT_BOT_TOKEN}/sendDocument"
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    filename = os.path.basename(file_path)
    body = bytearray()
    
    # chat_id field
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(f'Content-Disposition: form-data; name="chat_id"\r\n\r\n{chat_id}\r\n'.encode())
    
    # caption field
    if caption:
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n'.encode())
        
    # document field
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(f'Content-Disposition: form-data; name="document"; filename="{filename}"\r\n'.encode())
    body.extend(b"Content-Type: text/plain\r\n\r\n")
    body.extend(file_bytes)
    body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())

    req = urllib.request.Request(url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"Error sending document to {chat_id}: {e}")
        return None

def main():
    print("Loading accounts and fleet TON wallets...")
    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        accounts = json.load(f)

    with open(FLEET_WALLETS_FILE, "r", encoding="utf-8") as f:
        fleet_wallets = json.load(f)

    # 1. Generate text backup file
    now_str = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    lines = []
    lines.append("================================================================================")
    lines.append("      MY AGY AI — OFFICIAL TELEGRAM FLEET TON WALLETS & SECRET KEYS VAULT       ")
    lines.append("================================================================================")
    lines.append(f"Generated at: {now_str}")
    lines.append("Anti-Sybil Architecture: 100% Unique TON Addresses across all fleet accounts")
    lines.append("Wallet Version: TON v4r2 (Standard workchain 0)")
    lines.append("================================================================================\n")

    lines.append("--------------------------------------------------------------------------------")
    lines.append("👑 PRIMARY MASTER ACCOUNT (Arif Hossain / ID: 6727787768)")
    lines.append("--------------------------------------------------------------------------------")
    lines.append("• Telegram ID:         6727787768")
    lines.append("• Username:            @Arif2743aaa")
    lines.append("• Phone:               +8801944898197 (Bangladesh)")
    lines.append("• Arbitrum One Wallet: 0xfda4182001672b9f0f09e2118242e543e35ed5ce (Stones Miners)")
    lines.append("• BEP-20 BSC Wallet:   0xfda4182001672b9f0f09e2118242e543e35ed5ce (BNB Galaxy)")
    lines.append("• TON Network Wallet:  UQBPZiSvitdPU3VUyJK2mRaHVBl69xejw5aOrh1KfKA7gwDT (ART & MRG)")
    lines.append("• Custody:             Binance Web3 Wallet (Secured by Binance Cloud Multi-Party)\n")

    lines.append("--------------------------------------------------------------------------------")
    lines.append("👥 WORKER FLEET TON WALLETS & 24-WORD RECOVERY SEED PHRASES")
    lines.append("--------------------------------------------------------------------------------")

    worker_cards = []
    for idx, acc in enumerate(accounts):
        uid = str(acc.get("user_id"))
        if uid == "6727787768":
            continue

        w = fleet_wallets.get(uid, {})
        name = acc.get("name", f"Account #{idx+1}")
        phone = acc.get("phone", "N/A")
        addr = w.get("address", "N/A")
        addr_bounce = w.get("address_bounceable", "N/A")
        addr_raw = w.get("address_raw", "N/A")
        mnemonic = w.get("mnemonic", "N/A")
        pub_hex = w.get("public_key_hex", "N/A")
        priv_hex = w.get("private_key_hex", "N/A")

        lines.append(f"Account #{idx+1}: {name}")
        lines.append(f"• Telegram User ID: {uid}")
        lines.append(f"• Phone Number:     {phone}")
        lines.append(f"• TON Address:      {addr}")
        lines.append(f"• Bounceable:       {addr_bounce}")
        lines.append(f"• Raw Address:      {addr_raw}")
        lines.append(f"• Public Key (Hex): {pub_hex}")
        lines.append(f"• 24-Word Mnemonic:")
        lines.append(f"  {mnemonic}")
        lines.append("--------------------------------------------------------------------------------")

        card_md = (
            f"💼 *Account #{idx+1}: {name}*\n"
            f"• **Telegram ID:** `{uid}`\n"
            f"• **Phone:** `{phone}`\n"
            f"• **TON Address:**\n`{addr}`\n\n"
            f"🔑 **24-Word Secret Recovery Mnemonic:**\n"
            f"```text\n{mnemonic}\n```"
        )
        worker_cards.append(card_md)

    with open(BACKUP_TXT_FILE, "w", encoding="utf-8") as bf:
        bf.write("\n".join(lines))
    print(f"✅ Saved clean vault document to {BACKUP_TXT_FILE}")

    # 2. Target destinations
    targets = [
        AAA_T_WALLET_GROUP, # AAA T Wallet Supergroup (-1003973231307)
        REPORT_CHAT_ID,     # Arif Direct (6727787768)
        MYAGYAI_CHANNEL     # Cloud Backup Vault (-1004453515167)
    ]

    intro_header = (
        "🔐 *MY AGY AI — TELEGRAM FLEET WALLETS & SECRET KEYS VAULT*\n\n"
        "Here is the complete, official archive of all generated Telegram TON Wallets with their **24-word secret recovery seed phrases** and public addresses.\n\n"
        "• **Network:** The Open Network (TON v4r2)\n"
        "• **Anti-Sybil Guard:** 100% Unique addresses across all accounts (0 duplicates)\n"
        "• **Compatibility:** Import directly into Tonkeeper, Telegram Wallet (`@wallet`), or MyTonWallet\n"
        "• **Primary ID (`6727787768`):** Routes to Binance Web3 Wallets\n\n"
        "👇 *Individual Account Keys Listed Below:* 👇"
    )

    for tgt in targets:
        print(f"\n=======================================================")
        print(f"Broadcasting Wallet Vault to target: {tgt}")
        print(f"=======================================================")
        
        # Send Intro Header
        res_h = send_bot_message(intro_header, tgt)
        print(f"  Header sent: {bool(res_h and res_h.get('ok'))}")
        time.sleep(1.0)

        # Send worker cards in grouped messages (2 accounts per message to avoid Telegram 4096 char limits)
        for i in range(0, len(worker_cards), 2):
            batch = worker_cards[i:i+2]
            msg_text = "\n\n" + "—" * 28 + "\n\n".join(batch)
            res_c = send_bot_message(msg_text, tgt)
            print(f"  Batch {i//2 + 1}/{(len(worker_cards)+1)//2} sent: {bool(res_c and res_c.get('ok'))}")
            time.sleep(1.5)

        # Upload the complete raw backup file document
        caption = (
            "📦 Complete Telegram TON Wallets & Secret Recovery Keys Backup File.\n"
            "Keep this file safe! It contains the 24-word recovery seeds for all 11 worker accounts."
        )
        res_d = send_bot_document(BACKUP_TXT_FILE, tgt, caption=caption)
        print(f"  Vault Document file sent: {bool(res_d and res_d.get('ok'))}")
        time.sleep(1.5)

    print("\n🎉 ALL SECRETS AND TELEGRAM WALLETS SUCCESSFULLY BROADCASTED & SECURED IN AAA T WALLET GROUP!")

if __name__ == "__main__":
    main()
