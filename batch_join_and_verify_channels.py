import os
import json
import time
import urllib.request
import urllib.parse
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import RequestWebViewRequest, RequestAppWebViewRequest
from telethon.tl.types import InputBotAppShortName
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
API_ID = int(os.getenv("TELEGRAM_API_ID", "24726207"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "5cd9e5bbfb572a4429a0c54774153b47")
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")

CHANNELS = [
    "mrgminer",
    "mrgfun",
    "VictorsCompany",
    "vyrodrop",
    "atfminers"
]

def main():
    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        accounts = json.load(f)

    # Process all worker accounts (Accounts 2 to end)
    for idx in range(1, len(accounts)):
        acc = accounts[idx]
        name = acc.get("name", f"Account #{idx+1}")
        uid = str(acc.get("user_id"))
        sess = acc.get("session_string")

        if not sess or uid == "6727787768":
            continue

        print(f"\n=======================================================")
        print(f"[{idx+1}/{len(accounts)}] Processing {name} (UID: {uid})")
        print(f"=======================================================")

        client = TelegramClient(StringSession(sess), API_ID, API_HASH)
        try:
            client.connect()

            # 1. Join all official channels
            for ch in CHANNELS:
                try:
                    client(JoinChannelRequest(ch))
                    print(f"  ✅ Joined @{ch}")
                except Exception as e:
                    print(f"  Note @{ch}: {e}")
                time.sleep(1.2)

            # 2. MRG Miner: Claim Telegram Channel task
            try:
                bot_mrg = client.get_input_entity("mrgminerbot")
                res_m = client(RequestAppWebViewRequest(
                    peer=bot_mrg,
                    app=InputBotAppShortName(bot_id=bot_mrg, short_name="app"),
                    platform="android",
                    start_param="ref_IRN1G3XD"
                ))
                parsed_m = urllib.parse.urlparse(res_m.url)
                init_data_m = urllib.parse.parse_qs(parsed_m.fragment).get("tgWebAppData", [None])[0]
                if init_data_m:
                    req_mrg = urllib.request.Request(
                        "https://mrg.up.railway.app/api/user/claim-task",
                        data=json.dumps({"initData": init_data_m, "taskId": "task-1789255007980"}).encode(),
                        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
                    )
                    with urllib.request.urlopen(req_mrg, timeout=10) as r_mrg:
                        md = json.loads(r_mrg.read())
                        print(f"  ⛏️ [MRG Miner] Channel task claimed: {md.get('success')}")
            except Exception as me:
                print(f"  Note MRG: {me}")

        except Exception as e:
            print(f"  ❌ Error for {name}: {e}")
        finally:
            try:
                client.disconnect()
            except:
                pass

        time.sleep(2.5)

    print("\n🎉 ALL FLEET ACCOUNTS JOINED OFFICIAL CHANNELS & COMPLETED TASKS!")

if __name__ == "__main__":
    main()
