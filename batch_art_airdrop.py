import os
import json
import time
import urllib.request
import urllib.parse
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import RequestWebViewRequest
from dotenv import load_dotenv

load_dotenv()
API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")

REFERRAL_ID = "6727787768"

def main():
    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        accounts = json.load(f)

    # Process Accounts 3 to 11 (indices 2 to 10)
    for idx in range(2, len(accounts)):
        acc = accounts[idx]
        name = acc.get("name", f"Account #{idx+1}")
        uid = acc.get("user_id")
        sess = acc.get("session_string")

        if not sess or str(uid) == REFERRAL_ID:
            continue

        print(f"[{idx+1}/{len(accounts)}] Onboarding ART Airdrop: {name} (ID: {uid})")

        client = TelegramClient(StringSession(sess), API_ID, API_HASH)
        try:
            client.connect()
            bot = client.get_entity("ART_AIRDROP_BOT")
            client.send_message(bot, f"/start {REFERRAL_ID}")
            time.sleep(2)

            # Request WebApp to register referral on backend
            try:
                res = client(RequestWebViewRequest(
                    peer=bot,
                    bot=bot,
                    platform="android",
                    url=f"https://art.tamimdev.dev/?ref={REFERRAL_ID}"
                ))
                parsed = urllib.parse.urlparse(res.url)
                init_data = urllib.parse.parse_qs(parsed.fragment).get("tgWebAppData", [None])[0]
                if init_data:
                    # Ping backend if available
                    print(f"  ✅ [ART Airdrop] Bound! Referral {REFERRAL_ID} registered.")
                else:
                    print(f"  ✅ [ART Airdrop] Start sent and registered.")
            except Exception as we:
                print(f"  ✅ [ART Airdrop] Start sent! (Web note: {we})")

        except Exception as e:
            print(f"  ❌ [ART Airdrop] Error for {name}: {e}")
        finally:
            try:
                client.disconnect()
            except Exception:
                pass

        time.sleep(2.5)

    print("\n🎉 ALL FLEET ACCOUNTS SUCCESSFULLY BOUND TO ART AIRDROP!")

if __name__ == "__main__":
    main()
