import asyncio
import random
import time
import aiohttp

TG_ID = 6727787768
NAME = "Arif Hossain"
TARGET_COUNT = 5

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36 Telegram-Android/11.0.0",
    "Referer": "https://justtool.site/withdraw-adsgram",
    "Origin": "https://justtool.site"
}

async def get_current_count(session):
    url = f"https://justtool.site/api/adsgram-task3?tgId={TG_ID}"
    async with session.get(url, headers=HEADERS) as resp:
        data = await resp.json()
        return data.get("count", 0)

async def complete_step(session):
    url = "https://justtool.site/api/adsgram-task3"
    async with session.post(url, json={"tgId": TG_ID, "name": NAME}, headers=HEADERS) as resp:
        return await resp.json()

async def main():
    async with aiohttp.ClientSession() as session:
        count = await get_current_count(session)
        print(f"Current withdrawal verification progress: {count}/{TARGET_COUNT}")
        
        while count < TARGET_COUNT:
            # Human watch delay: 45 to 52 seconds
            watch_time = round(random.uniform(45.0, 52.0), 2)
            print(f"Simulating human watch for verification step {count + 1}/{TARGET_COUNT} ({watch_time}s)...")
            await asyncio.sleep(watch_time)
            
            res = await complete_step(session)
            count = res.get("count", count + 1)
            print(f"Step verified! Current progress: {count}/{TARGET_COUNT}")
            
            if count < TARGET_COUNT:
                pause = round(random.uniform(20.0, 35.0), 2)
                print(f"Natural pause between steps ({pause}s)...")
                await asyncio.sleep(pause)

        print("=" * 50)
        print("ALL 5/5 WITHDRAWAL VERIFICATION TASKS COMPLETED!")
        print("Withdrawal is now fully verified and unlocked!")
        print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
