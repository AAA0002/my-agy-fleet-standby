#!/usr/bin/env python3
"""
victors_fleet_wallet_connector.py
Connects dedicated TON wallets with TonConnect 2.0 cryptographic proof,
completes tutorials, checks in, claims free tasks, and activates mining
for all Victor's Company (@VictorsCompanybot) fleet accounts.
"""

import os
import sys
import json
import time
import struct
import hashlib
import base64
import urllib.request
import urllib.error
import logging

from nacl.signing import SigningKey
from tonsdk.contract.wallet import Wallets, WalletVersionEnum
from tonsdk.utils import Address

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("victors_wallet_connector")

UPSTASH_URL = os.getenv("UPSTASH_URL") or "https://rich-emu-106119.upstash.io"
UPSTASH_TOKEN = os.getenv("UPSTASH_TOKEN") or ""
VICTORS_API = "https://server.victors.company/api"
VICTORS_ORIGIN = "https://app.victors.company"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")
FLEET_WALLETS_FILE = os.path.join(BASE_DIR, "fleet_ton_wallets.json")

def load_fleet_uids() -> list:
    """Loads all fleet user IDs from accounts.json, preserving order."""
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                accs = json.load(f)
                uids = [int(a["user_id"]) for a in accs if a.get("user_id")]
                if uids:
                    return uids
        except Exception as e:
            logger.warning(f"Error loading accounts.json: {e}")
    return [
        6727787768, 8881914294, 7648254021, 8826375659, 8450010161,
        8782429452, 7734849205, 8025472383, 8851426148, 8203342513,
        8190649727, 7487048946, 8741547543, 8727040932, 7749125802,
        7954290138, 8841038141, 8975442879, 8937908003, 8609131528
    ]

FLEET_UIDS = load_fleet_uids()


def get_upstash(key: str):
    req = urllib.request.Request(
        f"{UPSTASH_URL}/get/{key}",
        headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}
    )
    with urllib.request.urlopen(req, timeout=12) as resp:
        res = json.loads(resp.read().decode())["result"]
        return json.loads(res) if isinstance(res, str) else res


def safe_post(url: str, data: dict, headers: dict) -> tuple:
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body.startswith("{") or body.startswith("[") else body
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8") if e.fp else ""
        try:
            return e.code, json.loads(err)
        except Exception:
            return e.code, err
    except Exception as e:
        return 0, str(e)


def safe_get(url: str, headers: dict) -> tuple:
    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=12) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body.startswith("{") or body.startswith("[") else body
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8") if e.fp else ""
        try:
            return e.code, json.loads(err)
        except Exception:
            return e.code, err
    except Exception as e:
        return 0, str(e)


def create_victors_ton_proof(wallet_entry: dict, nonce: str) -> tuple:
    """Signs TonConnect 2.0 proof-of-ownership for Victor's Company."""
    words = wallet_entry["mnemonic"].split() if isinstance(wallet_entry["mnemonic"], str) else wallet_entry["mnemonic"]
    _, pub_key_bytes, priv_key_bytes, wallet_contract = Wallets.from_mnemonics(
        mnemonics=words, version=WalletVersionEnum.v4r2
    )
    state_init_res = wallet_contract.create_state_init()
    state_init_b64 = base64.b64encode(state_init_res["state_init"].to_boc(False)).decode("utf-8")

    t_addr = wallet_contract.address
    wc = t_addr.wc
    addr_hash = t_addr.hash_part
    friendly_addr = t_addr.to_string(is_user_friendly=True, is_bounceable=False, is_url_safe=True)
    domain = "app.victors.company"
    timestamp = int(time.time())

    prefix = b"ton-proof-item-v2/"
    wc_bytes = struct.pack(">i", wc)
    domain_bytes = domain.encode("utf-8")
    domain_len = struct.pack("<I", len(domain_bytes))
    ts_bytes = struct.pack("<Q", timestamp)
    payload_bytes = nonce.encode("utf-8")

    msg = prefix + wc_bytes + addr_hash + domain_len + domain_bytes + ts_bytes + payload_bytes
    msg_hash = hashlib.sha256(msg).digest()
    full_msg = b"\xff\xff" + b"ton-connect" + msg_hash
    digest = hashlib.sha256(full_msg).digest()

    signing_key = SigningKey(priv_key_bytes[:32])
    sig = signing_key.sign(digest).signature
    sig_b64 = base64.b64encode(sig).decode("utf-8")

    proof_item = {
        "timestamp": timestamp,
        "domain": {
            "lengthBytes": len(domain_bytes),
            "value": domain
        },
        "signature": sig_b64,
        "payload": nonce
    }
    return proof_item, state_init_b64, pub_key_bytes.hex(), friendly_addr


def process_fleet_accounts():
    logger.info("📡 Loading miniapp_tokens and TON wallets from Upstash and local vault...")
    miniapp = get_upstash("miniapp_tokens") or {}
    wallets = get_upstash("fleet:wallets:ton") or {}
    
    # Merge local fallback wallets
    if os.path.exists(FLEET_WALLETS_FILE):
        try:
            with open(FLEET_WALLETS_FILE, "r", encoding="utf-8") as f:
                local_w = json.load(f)
                for k, v in local_w.items():
                    if k not in wallets or not wallets[k].get("mnemonic"):
                        wallets[k] = v
        except Exception as fe:
            logger.warning(f"Error reading local wallets: {fe}")

    success_count = 0
    total = len(FLEET_UIDS)

    for uid in FLEET_UIDS:
        p_data = get_upstash(f"victors:pass:{uid}")
        hp = p_data.get("humanPass") if (p_data and isinstance(p_data, dict)) else None

        v_init = None
        if str(uid) in miniapp and miniapp[str(uid)].get("victors_init_data"):
            v_init = miniapp[str(uid)]["victors_init_data"]
        if not v_init:
            t_data = get_upstash(f"fleet:tokens:{uid}")
            if t_data and t_data.get("victors_init_data"):
                v_init = t_data["victors_init_data"]

        if not v_init:
            logger.warning(f"UID {uid}: No victors_init_data found. Skipping.")
            continue

        w_entry = wallets.get(str(uid)) or wallets.get(int(uid))
        if not w_entry:
            logger.warning(f"UID {uid}: No TON wallet configured. Skipping.")
            continue

        headers = {
            "Authorization": f"tma {v_init}",
            "Content-Type": "application/json",
            "Origin": VICTORS_ORIGIN,
            "Referer": f"{VICTORS_ORIGIN}/",
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 Mobile"
        }
        if hp:
            headers["x-human-pass"] = str(hp)

        logger.info(f"--------------------------------------------------")
        logger.info(f"🚀 Processing UID {uid}...")

        # 1. Probe /me
        me_code, me_res = safe_get(f"{VICTORS_API}/me", headers)
        if me_code != 200 or not isinstance(me_res, dict) or not me_res.get("success"):
            logger.warning(f"UID {uid}: /me request failed: {me_code} {me_res}")
            if me_code == 401 and "HUMAN_REQUIRED" in str(me_res):
                logger.warning(f"UID {uid}: Needs fresh Cloudflare Turnstile humanPass. Solve via cloud runner.")
            continue

        user = me_res.get("user", {})
        fname = user.get("firstName", "Unknown")
        bal = user.get("inAppBalance", 0)
        is_conn = user.get("isWalletConnected", False)
        is_owned = user.get("walletOwned", False)
        logger.info(f"👤 {fname} (UID {uid}) | Balance: {bal} VIC | WalletConnected: {is_conn} | WalletOwned: {is_owned}")

        # 2. Tutorial & Daily Check-in
        safe_post(f"{VICTORS_API}/me/tutorial", {}, headers)
        safe_post(f"{VICTORS_API}/checkin", {}, headers)

        try:
            # 3. Connect TON Wallet via TonConnect 2.0 Proof
            if not (is_conn and is_owned):
                np_code, np_res = safe_get(f"{VICTORS_API}/wallet/proof-payload", headers)
                if np_code == 200 and isinstance(np_res, dict) and np_res.get("payload"):
                    nonce = np_res["payload"]
                    proof_item, state_init_b64, pub_key_hex, friendly_addr = create_victors_ton_proof(w_entry, nonce)
                    conn_body = {
                        "address": friendly_addr,
                        "proof": proof_item,
                        "stateInit": state_init_b64,
                        "publicKey": pub_key_hex
                    }
                    c_code, c_res = safe_post(f"{VICTORS_API}/wallet/connect", conn_body, headers)
                    if c_code in (200, 201) and isinstance(c_res, dict) and c_res.get("success"):
                        logger.info(f"💎 UID {uid}: Successfully connected TON wallet {friendly_addr[:12]}... (walletOwned=True)!")
                        success_count += 1
                        safe_post(f"{VICTORS_API}/tasks/claim", {"taskId": "connect-wallet"}, headers)
                    else:
                        logger.warning(f"UID {uid}: Connect wallet error: {c_code} {c_res}")
                else:
                    logger.warning(f"UID {uid}: Failed to obtain proof-payload nonce: {np_code} {np_res}")
            else:
                logger.info(f"💎 UID {uid}: TON wallet already connected and verified owned.")
                success_count += 1

            # 4. Unlock Level 1 Miner to start farming & remove home.noJob
            u_code, u_res = safe_post(f"{VICTORS_API}/levels/unlock", {"level": 1}, headers)
            logger.info(f"⛏️ UID {uid}: Level 1 Miner unlock status: {u_code}")

            # 5. Claim Tasks
            for tid in ["connect-wallet", "follow-victors-company-on-x", "like-retweet-comment-on-x", "subscribe-vic-on-youtube"]:
                t_code, t_res = safe_post(f"{VICTORS_API}/tasks/claim", {"taskId": tid}, headers)
                if t_code in (200, 201) and isinstance(t_res, dict) and t_res.get("success"):
                    logger.info(f"🎁 UID {uid}: Claimed '{tid}' (+{t_res.get('reward')} VIC)!")

            # 6. Mining Claim
            m_code, m_res = safe_post(f"{VICTORS_API}/mining/claim", {}, headers)
            logger.info(f"⛏️ UID {uid}: Mining accrual claim result: {m_code}")
        except Exception as e:
            logger.error(f"UID {uid} unexpected error during wallet processing: {e}")

    logger.info(f"==================================================")
    logger.info(f"🎉 Completed fleet wallet connection: {success_count}/{total} accounts connected & verified!")


if __name__ == "__main__":
    process_fleet_accounts()
