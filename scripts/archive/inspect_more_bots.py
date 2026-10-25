import asyncio
import os
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv()
client = TelegramClient(StringSession(os.getenv("TELEGRAM_STRING_SESSION")), int(os.getenv("TELEGRAM_API_ID")), os.getenv("TELEGRAM_API_HASH"))

async def inspect():
    await client.connect()
    for u in ["selim_token_bot", "monsterland_bot", "mrgminerbot", "ART_AIRDROP_BOT"]:
        try:
            bot = await client.get_entity(u)
            msgs = await client.get_messages(bot, limit=3)
            print(f"=== {u} ({bot.first_name}) ===")
            for m in reversed(msgs):
                print(f"[{m.date}] {m.raw_text}")
                if m.reply_markup and hasattr(m.reply_markup, "rows"):
                    for row in m.reply_markup.rows:
                        row_items = []
                        for b in row.buttons:
                            row_items.append(f"[{b.text}]")
                        print("  " + " | ".join(row_items))
                print("-" * 30)
        except Exception as e:
            print(f"Error on {u}: {e}")

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(inspect())
