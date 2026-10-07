import os
import sys
import json
import time
import asyncio
import aiohttp
import re
import urllib.parse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, "fleet_miniapp_tokens.json"), "r") as f:
    TOKENS_DB = json.load(f)

with open(os.path.join(BASE_DIR, "accounts.json"), "r") as f:
    ACCOUNTS = json.load(f)

MASTER_UID = "6727787768"

async def test_bot_farming_and_sidetasks(uid, name, tokens, acc_info):
    is_owner = (str(uid) == MASTER_UID)
    report = {
        "account": f"{name} (UID: {uid})",
        "is_master": is_owner,
        "bots": {}
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        # 1. Stones Miners
        stones_init = tokens.get("stones_init_data")
        if stones_init:
            s_h = {**headers, "Origin": "https://app.stoneswithestand.my.id", "Referer": "https://app.stoneswithestand.my.id/"}
            b_rep = {"core": {}, "side_tasks": []}
            try:
                # Core: claim & start
                async with session.post("https://app.stoneswithestand.my.id/api/claim", json={"initData": stones_init}, headers=s_h, timeout=aiohttp.ClientTimeout(total=8)) as r:
                    cl_data = await r.json() if r.status == 200 else {}
                    b_rep["core"]["claim"] = f"HTTP {r.status} - {cl_data.get('message', 'ok')}"
                async with session.post("https://app.stoneswithestand.my.id/api/mining/start", json={"initData": stones_init}, headers=s_h, timeout=aiohttp.ClientTimeout(total=8)) as r:
                    st_data = await r.json() if r.status == 200 else {}
                    b_rep["core"]["start_mining"] = f"HTTP {r.status} - {st_data.get('message', 'started')}"

                # Side Task: Daily checkin
                async with session.post("https://app.stoneswithestand.my.id/api/task/complete", json={"initData": stones_init, "slug": "daily_checkin"}, headers=s_h, timeout=aiohttp.ClientTimeout(total=8)) as r:
                    chk_d = await r.json() if r.status == 200 else {}
                    b_rep["side_tasks"].append(f"Daily Check-in: HTTP {r.status} ({chk_d.get('message', 'done')})")

                # Side Task: Stone Breaker mini-game status
                async with session.post("https://app.stoneswithestand.my.id/api/sb/status", json={"initData": stones_init}, headers=s_h, timeout=aiohttp.ClientTimeout(total=8)) as r:
                    if r.status == 200:
                        sbd = await r.json()
                        h_got, h_cap = sbd.get("hour_got", 0), sbd.get("hourly_cap", 10)
                        d_got, d_cap = sbd.get("day_got", 0), sbd.get("daily_cap", 100)
                        b_rep["side_tasks"].append(f"Stone Breaker Minigame: Hour {h_got}/{h_cap} STONES, Day {d_got}/{d_cap} STONES")

                # Side Task: Mining Boost (+0.5 TH/s)
                async with session.post("https://app.stoneswithestand.my.id/api/ad/boost/challenge", json={"initData": stones_init}, headers=s_h, timeout=aiohttp.ClientTimeout(total=8)) as r:
                    if r.status == 200:
                        abcd = await r.json()
                        cid = abcd.get("challenge", {}).get("challenge_id")
                        b_rep["side_tasks"].append(f"Hashrate Boost (+0.5 TH/s): Challenge ID {cid or 'Active'}")

                # State & balance
                async with session.post("https://app.stoneswithestand.my.id/api/state", json={"initData": stones_init}, headers=s_h, timeout=aiohttp.ClientTimeout(total=8)) as r:
                    if r.status == 200:
                        std = await r.json()
                        bal = std.get("user", {}).get("balance", 0)
                        hr = std.get("user", {}).get("hashrate", 0)
                        b_rep["core"]["balance"] = f"{bal:.2f} STONES (Hashrate: {hr} TH/s)"
            except Exception as e:
                b_rep["error"] = str(e)
            report["bots"]["1. Stones Miners"] = b_rep

        # 2. MRG Miner
        mrg_init = tokens.get("mrg_init_data")
        if mrg_init:
            m_h = {**headers, "Origin": "https://app.mrgtoken.xyz", "Referer": "https://app.mrgtoken.xyz/"}
            b_rep = {"core": {}, "side_tasks": []}
            try:
                # Core: claim mining
                async with session.post("https://mrg.up.railway.app/api/user/claim-mining", json={"initData": mrg_init}, headers=m_h, timeout=aiohttp.ClientTimeout(total=8)) as r:
                    cld = await r.json() if r.status == 200 else {}
                    b_rep["core"]["claim"] = f"HTTP {r.status} - {cld.get('message', 'ok')}"

                # State & Side Tasks
                async with session.post("https://mrg.up.railway.app/api/user/me", json={"initData": mrg_init}, headers=m_h, timeout=aiohttp.ClientTimeout(total=8)) as r:
                    if r.status == 200:
                        med = await r.json()
                        u_obj = med.get("user", {})
                        in_bal = u_obj.get("inAppBalance", 0)
                        cur_lvl = u_obj.get("peakLevel") or u_obj.get("manualUnlockedLevel") or 1
                        b_rep["core"]["balance"] = f"{in_bal} MRG (Miner Level: {cur_lvl}/203)"
                        
                        tasks = med.get("tasks", [])
                        comp_ids = set(med.get("completedTaskIds", []))
                        pending_cnt = len([t for t in tasks if t.get("taskId") not in comp_ids])
                        b_rep["side_tasks"].append(f"Task System: {len(comp_ids)} Completed, {pending_cnt} Pending Tasks")
                        
                        ton_conn = u_obj.get("isTonConnected")
                        ton_addr = u_obj.get("tonWalletAddress", "None")
                        b_rep["side_tasks"].append(f"TON Wallet: {'Connected: ' + ton_addr[:8] + '...' if ton_conn else 'Unbound'}")
                        
                        # Master Referral Commission
                        if is_owner:
                            async with session.post("https://mrg.up.railway.app/api/user/claim-commission", json={"initData": mrg_init}, headers=m_h, timeout=aiohttp.ClientTimeout(total=8)) as cr:
                                b_rep["side_tasks"].append(f"Master Referral Commission Claim: HTTP {cr.status}")
            except Exception as e:
                b_rep["error"] = str(e)
            report["bots"]["2. MRG Miner"] = b_rep

        # 3. ART Airdrop
        art_init = tokens.get("art_init_data")
        if art_init:
            art_h = {**headers, "Origin": "https://art.tamimdev.dev", "Referer": "https://art.tamimdev.dev/", "X-Telegram-Init-Data": art_init}
            b_rep = {"core": {}, "side_tasks": []}
            try:
                # Core: claim & start
                async with session.post("https://art.tamimdev.dev/api/user/claim-mining", json={"userId": int(uid)}, headers=art_h, timeout=aiohttp.ClientTimeout(total=8)) as r:
                    b_rep["core"]["claim"] = f"HTTP {r.status}"
                async with session.post("https://art.tamimdev.dev/api/user/start-mining", json={"userId": int(uid)}, headers=art_h, timeout=aiohttp.ClientTimeout(total=8)) as r:
                    b_rep["core"]["start_mining"] = f"HTTP {r.status}"

                # Side Task: Daily Ad Claim
                async with session.post("https://art.tamimdev.dev/api/ads/claim", json={"userId": int(uid)}, headers=art_h, timeout=aiohttp.ClientTimeout(total=8)) as r:
                    ad_res = await r.json() if r.status == 200 else {}
                    b_rep["side_tasks"].append(f"Daily High-Yield Ad: HTTP {r.status} ({ad_res.get('message', 'claimed')})")

                # User details, miner tier & balance
                async with session.get(f"https://art.tamimdev.dev/api/user/{uid}", headers=art_h, timeout=aiohttp.ClientTimeout(total=8)) as r:
                    if r.status == 200:
                        ud = await r.json()
                        u_info = ud.get("user", {})
                        pool = u_info.get("poolWallet", 0)
                        hold = u_info.get("holdingWallet", 0)
                        miners = u_info.get("unlockedMiners", [])
                        b_rep["core"]["balance"] = f"Pool: {pool:.2f} ART, Hold: {hold:.2f} ART"
                        b_rep["side_tasks"].append(f"Miner Hardware Levels: {miners} (Top Level: {max(miners) if miners else 1}/8)")
                        ton_w = u_info.get("tonAddress")
                        b_rep["side_tasks"].append(f"TON Wallet: {ton_w[:10] + '...' if ton_w else 'Not bound'}")
            except Exception as e:
                b_rep["error"] = str(e)
            report["bots"]["3. ART Airdrop"] = b_rep

        # 4. TRX Power Mining
        trx_init = tokens.get("trxpower_init_data")
        if trx_init:
            trx_base = "https://eb0frexrmrfl9pgywxd8ebxo.187.53.139.6.sslip.io/api"
            trx_h = {**headers, "Origin": "https://eb0frexrmrfl9pgywxd8ebxo.187.53.139.6.sslip.io", "Referer": "https://eb0frexrmrfl9pgywxd8ebxo.187.53.139.6.sslip.io/"}
            b_rep = {"core": {}, "side_tasks": []}
            try:
                # Login
                async with session.post(f"{trx_base}/auth/telegram", json={"initData": trx_init}, headers=trx_h, timeout=aiohttp.ClientTimeout(total=8)) as r:
                    auth_d = await r.json() if r.status == 200 else {}
                    jwt_tok = auth_d.get("token") or auth_d.get("data", {}).get("token")
                
                if jwt_tok:
                    authed_h = {**trx_h, "Authorization": f"Bearer {jwt_tok}", "x-telegram-init-data": trx_init}
                    # Core: claim
                    async with session.post(f"{trx_base}/mining/claim", json={}, headers=authed_h, timeout=aiohttp.ClientTimeout(total=8)) as r:
                        cl_d = await r.json() if r.status == 200 else {}
                        b_rep["core"]["claim"] = f"HTTP {r.status} (+{cl_d.get('claimedAmount', 0)} TRX)"

                    # Side Task: Channel Verification
                    async with session.post(f"{trx_base}/user/verify-channels", json={}, headers=authed_h, timeout=aiohttp.ClientTimeout(total=8)) as r:
                        b_rep["side_tasks"].append(f"Channel Verification: HTTP {r.status}")

                    # Side Task: Channel Task Claim
                    async with session.post(f"{trx_base}/tasks/channel/claim", json={}, headers=authed_h, timeout=aiohttp.ClientTimeout(total=8)) as r:
                        b_rep["side_tasks"].append(f"Channel Task Claim: HTTP {r.status}")

                    # Side Task: TRON Wallet Binding
                    tron_w = (acc_info.get("tron_wallet") or {}).get("address")
                    if tron_w:
                        async with session.post(f"{trx_base}/user/wallet", json={"address": tron_w}, headers=authed_h, timeout=aiohttp.ClientTimeout(total=8)) as r:
                            b_rep["side_tasks"].append(f"TRON Wallet Binding ({tron_w[:8]}...): HTTP {r.status}")

                    # Balance & Stats
                    async with session.get(f"{trx_base}/user/stats", headers=authed_h, timeout=aiohttp.ClientTimeout(total=8)) as r:
                        if r.status == 200:
                            sd = await r.json()
                            u_sd = sd.get("user") or sd.get("data", {}).get("user") or sd
                            b_rep["core"]["balance"] = f"{u_sd.get('balance', 0):.4f} TRX"
            except Exception as e:
                b_rep["error"] = str(e)
            report["bots"]["9. TRX Power"] = b_rep

        # 5. FINVORA Web3
        fin_init = tokens.get("finvora_init_data")
        if fin_init:
            fin_h = {**headers, "X-Telegram-Init-Data": fin_init}
            b_rep = {"core": {}, "side_tasks": []}
            try:
                # Core: Mining Claim
                async with session.post("https://finvora-production.up.railway.app/api/mining/claim", json={}, headers=fin_h, timeout=aiohttp.ClientTimeout(total=8)) as r:
                    fcd = await r.json() if r.status == 200 else {}
                    b_rep["core"]["claim"] = f"HTTP {r.status} (Claimed: {fcd.get('claimed', 0):.4f} GRAM)"

                # Side Task: Instant Bonus
                async with session.post("https://finvora-production.up.railway.app/api/bonus/instant", json={}, headers=fin_h, timeout=aiohttp.ClientTimeout(total=8)) as r:
                    ibd = await r.json() if r.status == 200 else {}
                    b_rep["side_tasks"].append(f"Instant Bonus: HTTP {r.status} ({ibd.get('message', 'ok')})")

                # Side Task: TON Wallet Binding
                target_ton = (acc_info.get("ton_wallet") or {}).get("address")
                if target_ton:
                    async with session.post("https://finvora-production.up.railway.app/api/wallet/connect", json={"address": target_ton, "walletType": "manual"}, headers=fin_h, timeout=aiohttp.ClientTimeout(total=8)) as r:
                        b_rep["side_tasks"].append(f"TON Wallet Connect ({target_ton[:8]}...): HTTP {r.status}")
            except Exception as e:
                b_rep["error"] = str(e)
            report["bots"]["13. FINVORA Web3"] = b_rep

        # 14. TurboGram V1
        tb_init = tokens.get("turbogram_init_data")
        if tb_init:
            tb_h = {**headers, "Authorization": f"tma {tb_init}"}
            b_rep = {"core": {}, "side_tasks": []}
            try:
                # Core: Balance & User State
                async with session.get("https://turbo.tamimdev.dev/api/me", headers=tb_h, timeout=aiohttp.ClientTimeout(total=8)) as r:
                    if r.status == 200:
                        med = await r.json()
                        b_rep["core"]["balance"] = f"{med.get('balance', 0):.2f} GRAM"

                # Side Task: Task Discovery & Completion
                async with session.get("https://turbo.tamimdev.dev/api/tasks", headers=tb_h, timeout=aiohttp.ClientTimeout(total=8)) as r:
                    if r.status == 200:
                        tasks = await r.json()
                        completed = len([t for t in tasks if t.get("isCompleted")])
                        b_rep["side_tasks"].append(f"Partner Tasks: {completed}/{len(tasks)} Completed (Referral Tier Active)")

                # Side Task: TON Wallet Binding
                target_ton = (acc_info.get("ton_wallet") or {}).get("address")
                if target_ton:
                    async with session.post("https://turbo.tamimdev.dev/api/me/wallet", json={"address": target_ton}, headers=tb_h, timeout=aiohttp.ClientTimeout(total=8)) as r:
                        b_rep["side_tasks"].append(f"TON Wallet Connect: HTTP {r.status}")
            except Exception as e:
                b_rep["error"] = str(e)
            report["bots"]["14. TurboGram V1"] = b_rep

    return report

async def main():
    print("="*80)
    print("🚀 FLEET-WIDE BOT FARMING & SIDE TASKS COMPREHENSIVE LIVE AUDIT")
    print("="*80)
    
    # Audit Master Account 6727787768
    master_tokens = TOKENS_DB.get(MASTER_UID, {})
    master_acc = next((a for a in ACCOUNTS if str(a.get("user_id")) == MASTER_UID), {})
    master_name = f"{master_acc.get('first_name', '')} {master_acc.get('last_name', '')}".strip() or "Master"
    
    print(f"\n[1/2] Auditing Master Account: {master_name} (UID: {MASTER_UID})...")
    res_master = await test_bot_farming_and_sidetasks(MASTER_UID, master_name, master_tokens, master_acc)
    
    # Audit Worker Account 8881914294
    worker_uid = "8881914294"
    worker_tokens = TOKENS_DB.get(worker_uid, {})
    worker_acc = next((a for a in ACCOUNTS if str(a.get("user_id")) == worker_uid), {})
    worker_name = f"{worker_acc.get('first_name', '')} {worker_acc.get('last_name', '')}".strip() or "Worker 1"

    print(f"\n[2/2] Auditing Worker Account: {worker_name} (UID: {worker_uid})...")
    res_worker = await test_bot_farming_and_sidetasks(worker_uid, worker_name, worker_tokens, worker_acc)

    with open(os.path.join(BASE_DIR, "live_farming_and_sidetasks_report.json"), "w") as rf:
        json.dump({"master": res_master, "worker": res_worker}, rf, indent=2)

    print("\n✅ Audit Complete! Results saved to live_farming_and_sidetasks_report.json")

if __name__ == "__main__":
    asyncio.run(main())
