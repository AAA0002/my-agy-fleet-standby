import os
import json
import time
import urllib.request
import urllib.parse
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import RequestAppWebViewRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import InputBotAppShortName
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

    # Process accounts 4 to 11 (indices 3 to 10)
    for idx in range(3, len(accounts)):
        acc = accounts[idx]
        name = acc.get("name", f"Account #{idx+1}")
        uid = acc.get("user_id")
        sess = acc.get("session_string")

        if not sess or str(uid) == REFERRAL_ID:
            continue

        print(f"\n==========================================")
        print(f"[{idx+1}/{len(accounts)}] Onboarding: {name} (ID: {uid})")
        print(f"==========================================")

        client = TelegramClient(StringSession(sess), API_ID, API_HASH)
        try:
            client.connect()

            # 1. Ultra Wallet
            try:
                bot1 = client.get_input_entity("UltrawalletTrade_Bot")
                res1 = client(RequestAppWebViewRequest(
                    peer=bot1,
                    app=InputBotAppShortName(bot_id=bot1, short_name="app"),
                    platform="android",
                    start_param=REFERRAL_ID
                ))
                parsed = urllib.parse.urlparse(res1.url)
                fragment = urllib.parse.parse_qs(parsed.fragment)
                init_data1 = fragment.get("tgWebAppData", [None])[0]
                if init_data1:
                    headers1 = {
                        "Content-Type": "application/json",
                        "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36",
                        "Referer": f"https://wallet.trxvault.top/?tgWebAppStartParam={REFERRAL_ID}"
                    }
                    req1 = urllib.request.Request(
                        "https://wallet.trxvault.top/api/telegramLogin",
                        data=json.dumps({"initData": init_data1, "refBy": REFERRAL_ID}).encode(),
                        headers=headers1
                    )
                    with urllib.request.urlopen(req1, timeout=10) as resp1:
                        d1 = json.loads(resp1.read())
                        print(f"  ✅ [Ultra Wallet] Bound! Token: {bool(d1.get('token'))}")
            except Exception as e:
                print(f"  ❌ [Ultra Wallet] Note: {e}")

            time.sleep(2)

            # 2. Gram Workers
            try:
                bot2 = client.get_entity("gramworkersbot")
                client.send_message(bot2, f"/start {REFERRAL_ID}")
                time.sleep(2)
                msgs = client.get_messages(bot2, limit=1)
                if msgs and msgs[0].buttons:
                    msgs[0].buttons[0][0].click()
                print(f"  ✅ [Gram Workers] Bound to referral {REFERRAL_ID}!")
            except Exception as e:
                print(f"  ❌ [Gram Workers] Note: {e}")

            time.sleep(2)

            # 3. Stones White Stand
            try:
                bot3 = client.get_entity("stoneswithestand_bot")
                client.send_message(bot3, f"/start r{REFERRAL_ID}")
                time.sleep(1.5)
                try:
                    client(JoinChannelRequest("stoneswithestand"))
                except Exception:
                    pass
                print(f"  ✅ [Stones White Stand] Bound to referral r{REFERRAL_ID}!")
            except Exception as e:
                print(f"  ❌ [Stones White Stand] Note: {e}")

            time.sleep(2)

            # 4. Zyntrix Mining
            try:
                bot4 = client.get_input_entity("ZyntrixMiningBot")
                res4 = client(RequestAppWebViewRequest(
                    peer=bot4,
                    app=InputBotAppShortName(bot_id=bot4, short_name="app"),
                    platform="android",
                    start_param=REFERRAL_ID
                ))
                print(f"  ✅ [Zyntrix Mining] Bound! WebApp URL registered.")
            except Exception as e:
                print(f"  ❌ [Zyntrix Mining] Note: {e}")

            time.sleep(2)

            # 5. TRX Power Mining
            try:
                bot5 = client.get_entity("trxpowermining_bot")
                client.send_message(bot5, f"/start ref_TRX{REFERRAL_ID}")
                time.sleep(1.5)
                print(f"  ✅ [TRX Power Mining] Bound to referral ref_TRX{REFERRAL_ID}!")
            except Exception as e:
                print(f"  ❌ [TRX Power Mining] Note: {e}")

            time.sleep(2)

            # 6. Bitcoin Cloud Miners
            try:
                bot6 = client.get_entity("BitcoinCloudMinersBot")
                client.send_message(bot6, f"/start {REFERRAL_ID}")
                time.sleep(1.5)
                print(f"  ✅ [Bitcoin Cloud Miners] Bound to referral {REFERRAL_ID}!")
            except Exception as e:
                print(f"  ❌ [Bitcoin Cloud Miners] Note: {e}")

            time.sleep(2)

            # 7. Tensor Mining Robot
            try:
                bot7 = client.get_input_entity("TensorMiningRobot")
                res7 = client(RequestAppWebViewRequest(
                    peer=bot7,
                    app=InputBotAppShortName(bot_id=bot7, short_name="myapp"),
                    platform="android",
                    start_param=REFERRAL_ID
                ))
                print(f"  ✅ [Tensor Mining Robot] Bound! WebApp URL registered.")
            except Exception as e:
                print(f"  ❌ [Tensor Mining Robot] Note: {e}")

            time.sleep(2)

            # 8. Ton Trader AI
            try:
                bot8 = client.get_input_entity("TonTraderAIBot")
                res8 = client(RequestAppWebViewRequest(
                    peer=bot8,
                    app=InputBotAppShortName(bot_id=bot8, short_name="app"),
                    platform="android",
                    start_param=f"REF_{REFERRAL_ID}"
                ))
                print(f"  ✅ [Ton Trader AI] Bound! WebApp URL registered.")
            except Exception as e:
                print(f"  ❌ [Ton Trader AI] Note: {e}")

            time.sleep(2)

            # 9. FINVORA Web3
            try:
                bot9 = client.get_entity("FINVORAWeb3bot")
                client.send_message(bot9, f"/start ref_TRX{REFERRAL_ID}")
                time.sleep(1.5)
                print(f"  ✅ [FINVORA Web3] Bound to referral ref_TRX{REFERRAL_ID}!")
            except Exception as e:
                print(f"  ❌ [FINVORA Web3] Note: {e}")

            time.sleep(2)

            # 10. TurboGram V1
            try:
                bot10 = client.get_entity("TurboGramV1_bot")
                client.send_message(bot10, "/start r_3520c92b")
                time.sleep(1.5)
                print(f"  ✅ [TurboGram V1] Bound to referral r_3520c92b!")
            except Exception as e:
                print(f"  ❌ [TurboGram V1] Note: {e}")

            time.sleep(2)

            # 11. Ominix AI Trade
            try:
                bot11 = client.get_input_entity("OminixAiBot")
                res11 = client(RequestAppWebViewRequest(
                    peer=bot11,
                    app=InputBotAppShortName(bot_id=bot11, short_name="Trade"),
                    platform="android",
                    start_param=REFERRAL_ID
                ))
                print(f"  ✅ [Ominix AI Trade] Bound! WebApp URL registered.")
            except Exception as e:
                print(f"  ❌ [Ominix AI Trade] Note: {e}")

            acc["custom_referrals_bound"] = True

        except Exception as err:
            print(f"  ⚠️ Error connecting {name}: {err}")
        finally:
            try:
                client.disconnect()
            except Exception:
                pass

        time.sleep(3)

    # Save updated status
    temp_file = f"{ACCOUNTS_FILE}.tmp.{os.getpid()}_{int(time.time()*1000)}"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(accounts, f, indent=2, ensure_ascii=False)
    os.replace(temp_file, ACCOUNTS_FILE)
    print("\n🎉 ALL FLEET ACCOUNTS SUCCESSFULLY BOUND TO YOUR REFERRAL LINKS!")

if __name__ == "__main__":
    main()
