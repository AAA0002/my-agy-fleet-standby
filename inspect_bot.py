import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
STRING_SESSION = os.getenv("TELEGRAM_STRING_SESSION")

client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

async def main():
    await client.connect()
    entity = await client.get_entity("CryptoProUpRobot")
    messages = await client.get_messages(entity, limit=5)
    
    print("=" * 60)
    print("FULL MESSAGES WITH @CryptoProUpRobot")
    print("=" * 60)
    for msg in reversed(messages):
        sender = "You" if msg.out else f"@{entity.username}"
        print(f"Message ID: {msg.id} | Date: {msg.date} | Sender: {sender}")
        print("Content:")
        print(msg.text or "[No text]")
        if msg.buttons:
            print("Buttons:")
            for row in msg.buttons:
                row_str = " | ".join([f"[{b.text}]" for b in row])
                print(f"  {row_str}")
        print("-" * 60)

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())
