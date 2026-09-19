import os
import sys
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
STRING_SESSION = os.getenv("TELEGRAM_STRING_SESSION")

if not API_ID or not API_HASH:
    print("Error: TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env")
    sys.exit(1)

try:
    API_ID = int(API_ID)
except ValueError:
    print("Error: TELEGRAM_API_ID must be an integer")
    sys.exit(1)

client = TelegramClient(StringSession(STRING_SESSION or ""), API_ID, API_HASH)

async def main():
    print("Connecting to Telegram...")
    await client.connect()
    if not await client.is_user_authorized():
        print("Failed: Session is not authorized or string session is invalid.")
        return
    me = await client.get_me()
    name = f"{me.first_name or ''} {me.last_name or ''}".strip()
    username = f"@{me.username}" if me.username else "None"
    phone = me.phone if hasattr(me, "phone") and me.phone else "Hidden"
    print("=" * 45)
    print(" Telegram Account Connected Successfully!")
    print("=" * 45)
    print(f"Name:     {name}")
    print(f"Username: {username}")
    print(f"User ID:  {me.id}")
    print(f"Phone:    {phone}")
    print("=" * 45)

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())
