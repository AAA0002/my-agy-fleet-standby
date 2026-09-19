import os
import json
import time
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.channels import LeaveChannelRequest
from dotenv import load_dotenv

load_dotenv()
API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")

CHANNELS_TO_LEAVE = [
    "AirdropBulider",
    "gramworkers",
    "milonOFFICIALEARN"
]

def main():
    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        accounts = json.load(f)

    print(f"Processing {len(accounts)} accounts to LEAVE: {CHANNELS_TO_LEAVE}")

    for idx, acc in enumerate(accounts):
        name = acc.get("name", f"Account #{idx+1}")
        uid = str(acc.get("user_id"))
        sess = acc.get("session_string")

        if not sess:
            continue

        print(f"\n[{idx+1}/{len(accounts)}] Processing {name} (ID: {uid})...")
        client = TelegramClient(StringSession(sess), API_ID, API_HASH)
        try:
            client.connect()
            for ch in CHANNELS_TO_LEAVE:
                try:
                    entity = client.get_entity(ch)
                    client(LeaveChannelRequest(entity))
                    print(f"  👋 Left channel @{ch}")
                except Exception as e:
                    err_msg = str(e).lower()
                    if "not a member" in err_msg or "user_not_participant" in err_msg:
                        print(f"  ℹ️ Not in @{ch} (already left)")
                    else:
                        print(f"  Note @{ch}: {e}")
                time.sleep(1.0)
        except Exception as e:
            print(f"  ❌ Error for {name}: {e}")
        finally:
            try:
                client.disconnect()
            except Exception:
                pass

        time.sleep(1.5)

    print("\n🎉 ALL ACCOUNTS HAVE SUCCESSFULLY LEFT THE REQUESTED CHANNELS!")

if __name__ == "__main__":
    main()
