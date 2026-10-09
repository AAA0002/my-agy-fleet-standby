#!/usr/bin/env python3
"""
run_fleet_arcade_expeditions.py
Executes autonomous Deep Mine arcade expeditions across all ready fleet accounts.
"""

import os
import sys
import json
import asyncio
import aiohttp
import logging
import urllib.request
from victors_arcade_solver import solve_deep_mine_expeditions

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("fleet_arcade")

UPSTASH_URL = os.getenv("UPSTASH_URL") or "https://relaxing-starfish-285827.upstash.io"
UPSTASH_TOKEN = os.getenv("UPSTASH_TOKEN") or "gQAAAAAABFyDAAIgcDI5MDYyYWZjNzYzNzk0ZmRjYjhmNTA4ZDI4ODlmODkzNw"
VICTORS_API = "https://server.victors.company/api"
VICTORS_ORIGIN = "https://app.victors.company"

UID_NAMES = {
    8881914294: "Nancy",
    8826375659: "Arif",
    8450010161: "Nadim",
    8782429452: "Kaitlyn",
    7734849205: "Abid Hasan",
    8851426148: "Node 9",
    8203342513: "Girtt (Node 10)",
    8190649727: "MD. Arif",
    8741547543: "Abid (3)",
    7954290138: "Roger",
    8975442879: "Mary"
}


def get_upstash(key: str):
    try:
        req = urllib.request.Request(
            f"{UPSTASH_URL}/get/{key}",
            headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            res = json.loads(resp.read().decode())["result"]
            return json.loads(res) if isinstance(res, str) else res
    except Exception as e:
        logger.error(f"Upstash error {key}: {e}")
        return None


async def main():
    tokens = get_upstash("miniapp_tokens") or {}
    logger.info("=" * 65)
    logger.info("VICTOR'S COMPANY — FLEET DEEP MINE EXPEDITIONS RUNNER")
    logger.info("=" * 65)

    results = []

    async with aiohttp.ClientSession() as session:
        for uid, name in UID_NAMES.items():
            tma = tokens.get(str(uid), {}).get("victors_init_data")
            hp_obj = get_upstash(f"victors:pass:{uid}")
            hp = hp_obj.get("humanPass") if isinstance(hp_obj, dict) else hp_obj

            if not tma or not hp:
                logger.warning(f"[{name} ({uid})] Missing tma or humanPass. Skipping.")
                continue

            v_headers = {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15",
                "Content-Type": "application/json",
                "Authorization": f"tma {tma}",
                "x-human-pass": str(hp),
                "Origin": VICTORS_ORIGIN,
                "Referer": f"{VICTORS_ORIGIN}/"
            }

            logger.info(f"\n--- Starting Deep Mine for {name} ({uid}) ---")
            stats = await solve_deep_mine_expeditions(session, v_headers, f"{name} ({uid})", max_runs=2)
            results.append({"uid": uid, "name": name, **stats})
            await asyncio.sleep(1.0)

    logger.info("\n" + "=" * 65)
    logger.info("FLEET EXPEDITIONS COMPLETED SUMMARY:")
    logger.info("=" * 65)
    total_runs = sum(r["runs_played"] for r in results)
    total_paid = sum(r["total_paid"] for r in results)
    total_net = sum(r["net_vic"] for r in results)

    for r in results:
        bal_str = f"{r['final_balance']:.2f} VIC" if r["final_balance"] is not None else "N/A"
        logger.info(f"  • {r['name']}: {r['runs_played']} runs | Total Paid: {r['total_paid']:.1f} VIC | Net: {r['net_vic']:+.1f} VIC | Balance: {bal_str}")

    logger.info("-" * 65)
    logger.info(f"Total Runs Played: {total_runs} | Total Payout: {total_paid:.1f} VIC | Net Result: {total_net:+.1f} VIC")
    logger.info("=" * 65)


if __name__ == "__main__":
    asyncio.run(main())
