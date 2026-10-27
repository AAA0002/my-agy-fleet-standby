#!/usr/bin/env python3
"""
chickenland_miner.py
=============================================================================
CHICKEN LAND AUTONOMOUS MINING & FARMING ENGINE FOR AAA AUTO FLEET
=============================================================================
Manages autonomous farming for Chicken Land (@ChickenLandBot / tgcloud.ai app 8968434282):
- TMA Authorization (Base64 encoded initData)
- Automated programmatic CAPTCHA bypass (turnstile fallback + target icon picking)
- Daily checkin claiming & streak progression
- Task sweeping (channel, payments, news, promo, partner reactions)
- Egg collection & selling (/api/sell)
- Autonomous hen purchasing (flock expansion)
- Basket storage upgrades
- Referral commission claiming (/api/ref/claim)
=============================================================================
"""

import os
import sys
import json
import time
import base64
import urllib.parse
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List

class ChickenLandMiner:
    API_RPC = "https://app8968434282.tgcloud.ai/api/rpc"
    
    def __init__(self, init_data: str, user_id: Optional[str] = None):
        """
        Initializes miner with Telegram WebApp initData string or TMA base64 token.
        """
        self.user_id = str(user_id) if user_id else ""
        if init_data.startswith("TMA "):
            self.b64_token = init_data[4:].strip()
            self.raw_init_data = ""
        elif "%3D" in init_data or "query_id=" in init_data or "user=" in init_data:
            # Check if URL decoded or needs decoding
            if "%3D" in init_data:
                decoded = urllib.parse.unquote(init_data)
            else:
                decoded = init_data
            self.raw_init_data = decoded
            self.b64_token = base64.b64encode(decoded.encode("latin1")).decode("latin1")
        else:
            # Assume already base64 encoded
            self.b64_token = init_data.strip()
            self.raw_init_data = ""
            
    def rpc(self, path: str, body: Optional[Dict[str, Any]] = None, timeout: int = 15) -> Dict[str, Any]:
        """Executes a JSON-RPC request to the Chicken Land serverless cloud."""
        payload = {
            "method": "POST" if body is not None else "GET",
            "path": path,
            "body": body if body is not None else {}
        }
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.API_RPC,
            data=data_bytes,
            headers={
                "Authorization": f"TMA {self.b64_token}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Linux; Android 14; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36"
            },
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                return res
        except urllib.error.HTTPError as e:
            try:
                err_body = json.loads(e.read().decode("utf-8"))
                return err_body
            except Exception:
                return {"ok": False, "error_code": e.code, "description": str(e)}
        except Exception as e:
            return {"ok": False, "error_code": 0, "description": str(e)}

    def get_config(self) -> Dict[str, Any]:
        """Fetches game configuration, prices, and limits."""
        return self.rpc("/api/config")

    def get_profile(self, ref: str = "12668") -> Dict[str, Any]:
        """Fetches user profile, inventory, and stats."""
        return self.rpc("/api/me", {"ref": ref, "lang": "en"})

    def ensure_human(self) -> bool:
        """
        Validates human status / solves captcha automatically.
        Uses the serverless fallback to 'pick' mode, locates target, and submits correct pick.
        """
        for _ in range(4):
            cap = self.rpc("/api/captcha", {})
            if not cap.get("ok"):
                time.sleep(1)
                continue
            res = cap.get("result", {})
            if res.get("done"):
                return True
            kind = res.get("kind")
            if kind == "turnstile":
                self.rpc("/api/human", {"fallback": True, "why": "unsupported"})
                time.sleep(1.5)
                continue
            if kind == "pick":
                items = res.get("items", [])
                target = res.get("target", "")
                if target in items:
                    idx = items.index(target)
                    pick_res = self.rpc("/api/human", {"pick": idx})
                    if pick_res.get("ok"):
                        return True
            time.sleep(1)
        return False

    def claim_welcome(self) -> Dict[str, Any]:
        """Claims initial 1,000 welcome coins if uncollected."""
        return self.rpc("/api/welcome", {})

    def collect_and_sell(self) -> Dict[str, Any]:
        """Collects produced eggs and sells them for coins/egg balance."""
        return self.rpc("/api/sell", {})

    def claim_daily(self) -> Dict[str, Any]:
        """Claims daily checkin coins."""
        return self.rpc("/api/task", {"id": "daily"})

    def claim_referrals(self) -> Dict[str, Any]:
        """Claims pending referral commission coins."""
        return self.rpc("/api/ref/claim", {})

    def check_promo(self, code: str) -> Dict[str, Any]:
        """Checks if a promo code is valid and available."""
        return self.rpc("/api/promo/check", {"code": code.strip()})

    def redeem_promo(self, code: str) -> Dict[str, Any]:
        """Redeems promo code for coins."""
        return self.rpc("/api/promo", {"code": code.strip()})

    def buy_hens(self, breed: str = "basic", max_count: int = 10) -> int:
        """Buys hens of specified breed if coins are available."""
        prof = self.get_profile()
        user = prof.get("result", {}).get("user", {})
        coins = user.get("coins", 0)
        hen_cost = 1000 # Basic hen cost
        if coins < hen_cost:
            return 0
        
        can_buy = min(int(coins // hen_cost), max_count)
        if can_buy <= 0:
            return 0
            
        res = self.rpc("/api/buy", {"breed": breed, "n": can_buy})
        if res.get("ok"):
            return can_buy
        return 0

    def upgrade_basket(self) -> bool:
        """Upgrades basket capacity if affordable."""
        prof = self.get_profile()
        user = prof.get("result", {}).get("user", {})
        coins = user.get("coins", 0)
        lvl = user.get("basketLevel", 0)
        cfg = self.get_config().get("result", {})
        basket_cfg = cfg.get("basket", [])
        if lvl + 1 < len(basket_cfg):
            next_cost = basket_cfg[lvl + 1].get("cost", 999999)
            if coins >= next_cost:
                res = self.rpc("/api/upgrade", {})
                return bool(res.get("ok"))
        return False

    def claim_tasks(self) -> Dict[str, Any]:
        """Sweeps and claims available social & daily tasks."""
        tasks_resp = self.rpc("/api/tasks")
        if not tasks_resp.get("ok"):
            return {"claimed": []}
            
        res = tasks_resp.get("result", {})
        prof = self.get_profile()
        user = prof.get("result", {}).get("user", {})
        completed_tasks = set(user.get("tasks", []))
        completed_day = set(user.get("dayTasks", []))
        
        claimed = []
        
        # 1. Main tasks
        main_tasks = ["channel", "payments", "chat", "x"]
        for tid in main_tasks:
            if tid not in completed_tasks:
                self.rpc("/api/task/open", {"id": tid})
                time.sleep(1)
                r = self.rpc("/api/task", {"id": tid})
                if r.get("ok"):
                    claimed.append(tid)
                    
        # 2. Daily tasks
        day_tasks = ["dnews", "dpay", "dpromo"]
        for tid in day_tasks:
            if tid not in completed_day:
                self.rpc("/api/task/open", {"id": tid})
                time.sleep(1)
                r = self.rpc("/api/task", {"id": tid})
                if r.get("ok"):
                    claimed.append(tid)
                    
        # 3. Custom/partner tasks
        custom = res.get("custom", [])
        for c in custom:
            cid = c.get("id")
            if cid and cid not in completed_tasks:
                self.rpc("/api/task/open", {"id": cid})
                time.sleep(1)
                r = self.rpc("/api/task", {"id": cid})
                if r.get("ok"):
                    claimed.append(cid)
                    
        return {"claimed": claimed}

    def run_farming_cycle(self, ref: str = "12668") -> Dict[str, Any]:
        """
        Executes a complete autonomous farming cycle for this account:
        1. Auth & Profile
        2. Ensure Human / Captcha
        3. Claim Welcome if needed
        4. Claim Daily Checkin
        5. Collect and Sell Eggs
        6. Sweep Tasks
        7. Claim Referral Rewards
        8. Buy Hens if affordable
        9. Upgrade Basket if affordable
        """
        cycle_report = {
            "user_id": self.user_id,
            "status": "success",
            "eggs_collected": 0,
            "coins_earned": 0,
            "hens_bought": 0,
            "tasks_claimed": [],
            "daily_claimed": False,
            "ref_claimed": False,
            "basket_upgraded": False
        }
        
        # Step 1: Initial profile & ref bind
        prof = self.get_profile(ref=ref)
        if not prof.get("ok"):
            cycle_report["status"] = "failed"
            cycle_report["error"] = prof.get("description", "Auth failed")
            return cycle_report
            
        user = prof.get("result", {}).get("user", {})
        cycle_report["name"] = user.get("name")
        cycle_report["num"] = user.get("num")
        
        # Step 2: Ensure human
        if not user.get("human"):
            if self.ensure_human():
                time.sleep(1)
            
        # Step 3: Welcome bonus
        if not user.get("welcome"):
            w_res = self.claim_welcome()
            if not w_res.get("ok"):
                # If captcha needed, retry human then welcome
                self.ensure_human()
                time.sleep(1)
                self.claim_welcome()
            
        # Step 4: Daily checkin
        daily_res = self.claim_daily()
        if daily_res.get("ok"):
            cycle_report["daily_claimed"] = True
            
        # Step 5: Collect and sell eggs
        sell_res = self.collect_and_sell()
        if sell_res.get("ok"):
            cycle_report["eggs_collected"] = sell_res.get("result", {}).get("eggs", 0)
            cycle_report["coins_earned"] = sell_res.get("result", {}).get("coins", 0)
            
        # Step 6: Sweep tasks
        tasks_res = self.claim_tasks()
        cycle_report["tasks_claimed"] = tasks_res.get("claimed", [])
        
        # Step 7: Claim referrals
        ref_res = self.claim_referrals()
        if ref_res.get("ok") and ref_res.get("result", {}).get("coins", 0) > 0:
            cycle_report["ref_claimed"] = True
            cycle_report["ref_coins"] = ref_res.get("result", {}).get("coins", 0)
            
        # Step 8: Buy hens
        hens = self.buy_hens()
        cycle_report["hens_bought"] = hens
        
        # Step 9: Upgrade basket
        upgraded = self.upgrade_basket()
        cycle_report["basket_upgraded"] = upgraded
        
        # Final status
        final_prof = self.get_profile()
        final_user = final_prof.get("result", {}).get("user", {})
        cycle_report["final_coins"] = final_user.get("coins", 0)
        cycle_report["final_hens"] = final_user.get("hens", 0)
        cycle_report["final_rate"] = final_user.get("rate", 0)
        cycle_report["final_egg_bal"] = final_user.get("eggBal", 0)
        cycle_report["withdrawn_usd"] = final_user.get("withdrawnUsd", 0)
        
        return cycle_report

if __name__ == "__main__":
    tokens_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fleet_miniapp_tokens.json")
    if os.path.exists(tokens_file):
        tokens_data = json.load(open(tokens_file))
        # Test on first account with chickenland token
        for uid, toks in tokens_data.items():
            tok = toks.get("chickenland_init_data")
            if tok:
                print(f"Running test cycle on account {uid}...")
                miner = ChickenLandMiner(tok, user_id=uid)
                report = miner.run_farming_cycle()
                print(json.dumps(report, indent=2))
                break
    else:
        print("No tokens file found to test.")
