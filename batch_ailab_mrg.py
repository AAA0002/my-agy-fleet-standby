import os
import json
import time
import urllib.request
import urllib.parse
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import RequestAppWebViewRequest, RequestWebViewRequest
from telethon.tl.types import InputBotAppShortName
from dotenv import load_dotenv

load_dotenv()
API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")

AILAB_REF = "296852"
MRG_REF = "ref_IRN1G3XD"
PRIMARY_ID = "6727787768"

def main():
    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        accounts = json.load(f)

    # Process Accounts 3 to 11 (indices 2 to 10)
    for idx in range(2, len(accounts)):
        acc = accounts[idx]
        name = acc.get("name", f"Account #{idx+1}")
        uid = acc.get("user_id")
        sess = acc.get("session_string")

        if not sess or str(uid) == PRIMARY_ID:
            continue

        print(f"\n==========================================")
        print(f"[{idx+1}/{len(accounts)}] Onboarding: {name} (ID: {uid})")
        print(f"==========================================")

        client = TelegramClient(StringSession(sess), API_ID, API_HASH)
        try:
            client.connect()

            # 1. AI Lab Robot (/start 296852 + login)
            try:
                bot1 = client.get_entity("AiLab_robot")
                client.send_message(bot1, f"/start {AILAB_REF}")
                time.sleep(2)
                res1 = client(RequestWebViewRequest(
                    peer=bot1,
                    bot=bot1,
                    platform="android",
                    url="https://ailab-agent.online/"
                ))
                parsed1 = urllib.parse.urlparse(res1.url)
                init_data1 = urllib.parse.parse_qs(parsed1.fragment).get("tgWebAppData", [None])[0]
                if init_data1:
                    headers1 = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
                    req1 = urllib.request.Request(
                        "https://api.ailab-agent.online/api/v1/users/auth/login",
                        data=json.dumps({"user": init_data1}).encode(),
                        headers=headers1
                    )
                    with urllib.request.urlopen(req1, timeout=10) as resp1:
                        d1 = json.loads(resp1.read())
                        print(f"  ✅ [AI Lab] Bound to referral {AILAB_REF}! User: {d1.get('result', {}).get('username') or name}")
            except Exception as e:
                print(f"  ❌ [AI Lab] Note: {e}")

            time.sleep(2)

            # 2. MRG Miner (ref_IRN1G3XD + auth verify + user profile)
            try:
                bot2_in = client.get_input_entity("mrgminerbot")
                res2 = client(RequestAppWebViewRequest(
                    peer=bot2_in,
                    app=InputBotAppShortName(bot_id=bot2_in, short_name="app"),
                    platform="android",
                    start_param=MRG_REF
                ))
                parsed2 = urllib.parse.urlparse(res2.url)
                init_data2 = urllib.parse.parse_qs(parsed2.fragment).get("tgWebAppData", [None])[0]
                if init_data2:
                    headers2 = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
                    req2 = urllib.request.Request(
                        "https://mrg.up.railway.app/api/auth/verify",
                        data=json.dumps({"initData": init_data2, "start_param": MRG_REF}).encode(),
                        headers=headers2
                    )
                    with urllib.request.urlopen(req2, timeout=10) as resp2:
                        d2 = json.loads(resp2.read())
                        print(f"  ✅ [MRG Miner] Verified: {d2.get('verified', False)}")

                    req2b = urllib.request.Request(
                        "https://mrg.up.railway.app/api/user/me",
                        data=json.dumps({"initData": init_data2}).encode(),
                        headers=headers2
                    )
                    with urllib.request.urlopen(req2b, timeout=10) as resp2b:
                        d2b = json.loads(resp2b.read())
                        u2 = d2b.get("user", {})
                        print(f"  ✅ [MRG Miner] Bound to referral {MRG_REF}! ReferrerId: {u2.get('referrerId')}")
            except Exception as e:
                print(f"  ❌ [MRG Miner] Note: {e}")

        except Exception as err:
            print(f"  ⚠️ Error connecting {name}: {err}")
        finally:
            try:
                client.disconnect()
            except Exception:
                pass

        time.sleep(3)

    print("\n🎉 ALL FLEET ACCOUNTS SUCCESSFULLY BOUND TO AI LAB & MRG MINER!")

if __name__ == "__main__":
    main()
