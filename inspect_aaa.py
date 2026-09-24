import asyncio
import os
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv()
client = TelegramClient(StringSession(os.getenv("TELEGRAM_STRING_SESSION")), int(os.getenv("TELEGRAM_API_ID")), os.getenv("TELEGRAM_API_HASH"))

async def inspect():
    await client.connect()
    bot = await client.get_entity("AAAPREMIUMAPPSbot")
    print(f"Bot Name: {bot.first_name}")
    print(f"Bot Username: @{bot.username}")
    print(f"Bot ID: {bot.id}")
    
    print("\n--- Recent Messages ---")
    msgs = await client.get_messages(bot, limit=10)
    for m in reversed(msgs):
        sender = "You" if m.out else f"@{bot.username}"
        print(f"ID {m.id} | [{m.date}] {sender}:")
        print(m.raw_text or "[No text]")
        if m.reply_markup and hasattr(m.reply_markup, "rows"):
            print("Buttons:")
            for row in m.reply_markup.rows:
                items = []
                for b in row.buttons:
                    items.append(f"[{b.text} (url={getattr(b, 'url', None)}, data={getattr(b, 'data', None)})]")
                print("  " + " | ".join(items))
        print("-" * 50)

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(inspect())
