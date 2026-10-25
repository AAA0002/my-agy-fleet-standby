import os
import json
import time
import urllib.request
import urllib.parse
from dotenv import load_dotenv

load_dotenv()
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import RequestWebViewRequest, RequestAppWebViewRequest
from telethon.tl.functions.contacts import UnblockRequest
from telethon.tl.types import InputBotAppShortName

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")

AILAB_REF = "296852"
ULTRA_REF = "6727787768"
PRIMARY_ID = "6727787768"

def main():
    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        accounts = json.load(f)

    print(f"🚀 Starting Fleet Onboarding for AI Lab Robot & UltraWallet ({len(accounts)-1} worker accounts)...")
    success_ailab = 0
    success_ultra = 0

    for idx, acc in enumerate(accounts):
        uid = str(acc.get("user_id"))
        name = acc.get("name", f"Account #{idx+1}")
        sess = acc.get("session_string")

        # Skip Primary account
        if uid == PRIMARY_ID or not sess:
            continue

        print(f"\n==========================================")
        print(f"[{idx+1}/{len(accounts)}] Processing {name} (ID: {uid})...")
        print(f"==========================================")

        client = TelegramClient(StringSession(sess), API_ID, API_HASH)
        try:
            client.connect()
            if not client.is_connected():
                print(f"  ❌ Could not connect MTProto for {name}")
                continue

            # ----------------------------------------------------
            # 1. AI LAB ROBOT (https://t.me/AiLab_robot?start=296852)
            # ----------------------------------------------------
            try:
                try:
                    client(UnblockRequest(id="AiLab_robot"))
                except Exception:
                    pass
                bot_ai = client.get_entity("AiLab_robot")
                client.send_message(bot_ai, f"/start {AILAB_REF}")
                time.sleep(1.5)

                res_ai = client(RequestWebViewRequest(
                    peer=bot_ai,
                    bot=bot_ai,
                    platform="android",
                    url="https://ailab-agent.online/"
                ))
                parsed_ai = urllib.parse.urlparse(res_ai.url)
                init_ai = urllib.parse.parse_qs(parsed_ai.fragment).get("tgWebAppData", [None])[0]

                if init_ai:
                    headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-S918B)"}
                    req_ai = urllib.request.Request(
                        "https://api.ailab-agent.online/api/v1/users/auth/login",
                        data=json.dumps({"user": init_ai}).encode(),
                        headers=headers
                    )
                    with urllib.request.urlopen(req_ai, timeout=10) as r_ai:
                        d_ai = json.loads(r_ai.read())
                        print(f"  ✅ [AI Lab] Bound to referral {AILAB_REF}! User ID: {d_ai.get('result', {}).get('user_id')}")
                        acc["ailab_referral_bound"] = True
                        success_ailab += 1
                else:
                    print(f"  ⚠️ [AI Lab] WebApp initData not returned")
            except Exception as e:
                print(f"  ❌ [AI Lab] Error: {e}")

            time.sleep(2)

            # ----------------------------------------------------
            # 2. ULTRA WALLET (https://t.me/UltrawalletTrade_Bot/app?startapp=6727787768)
            # ----------------------------------------------------
            try:
                try:
                    client(UnblockRequest(id="UltrawalletTrade_Bot"))
                except Exception:
                    pass
                bot_uw = client.get_input_entity("UltrawalletTrade_Bot")
                try:
                    client.send_message("UltrawalletTrade_Bot", f"/start {ULTRA_REF}")
                except Exception:
                    pass
                time.sleep(1.5)

                res_uw = client(RequestAppWebViewRequest(
                    peer=bot_uw,
                    app=InputBotAppShortName(bot_id=bot_uw, short_name="app"),
                    platform="android",
                    start_param=ULTRA_REF
                ))
                parsed_uw = urllib.parse.urlparse(res_uw.url)
                init_uw = urllib.parse.parse_qs(parsed_uw.fragment).get("tgWebAppData", [None])[0]

                if init_uw:
                    headers_uw = {
                        "Content-Type": "application/json",
                        "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36",
                        "Referer": f"https://wallet.trxvault.top/?tgWebAppStartParam={ULTRA_REF}"
                    }
                    req_uw = urllib.request.Request(
                        "https://wallet.trxvault.top/api/telegramLogin",
                        data=json.dumps({"initData": init_uw, "refBy": ULTRA_REF}).encode(),
                        headers=headers_uw
                    )
                    with urllib.request.urlopen(req_uw, timeout=10) as r_uw:
                        d_uw = json.loads(r_uw.read())
                        has_token = bool(d_uw.get("token"))
                        print(f"  ✅ [Ultra Wallet] Bound to referral {ULTRA_REF}! Login Token: {has_token}")
                        acc["ultrawallet_referral_bound"] = True
                        success_ultra += 1
                else:
                    print(f"  ⚠️ [Ultra Wallet] WebApp initData not returned")
            except Exception as e:
                print(f"  ❌ [Ultra Wallet] Error: {e}")

        except Exception as conn_err:
            print(f"  ⚠️ General error on {name}: {conn_err}")
        finally:
            try:
                client.disconnect()
            except Exception:
                pass

        time.sleep(2.5)

    # Save accounts.json safely
    temp_file = f"{ACCOUNTS_FILE}.tmp.{os.getpid()}_{int(time.time()*1000)}"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(accounts, f, indent=2, ensure_ascii=False)
    os.replace(temp_file, ACCOUNTS_FILE)

    print("\n==========================================")
    print(f"🎉 FLEET ONBOARDING COMPLETE!")
    print(f"• AI Lab Robot Bound: {success_ailab}/{len(accounts)-1}")
    print(f"• Ultra Wallet Bound: {success_ultra}/{len(accounts)-1}")
    print("==========================================")

if __name__ == "__main__":
    main()
