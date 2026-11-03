#!/usr/bin/env python3
"""
refresh_fleet_tokens.py
Automated Multi-Account Telegram MiniApp Token Refresher (Delegates to refresh_cloud_tokens.py)
Connects to Fleet Accounts via Telethon (MTProto) and extracts fresh 24h WebApp initData
for all 9 active legitimate fleet MiniApps:
  1. ATF Miner (@atfminers_bot)
  2. Kynex Network (@Kynex_miningbot)
  3. DiggoMiner (@Diggominer_bot)
  4. PepeGram (@Pepe_gram_bot)
  5. AdxEarn AI (@AdxEarnAibot)
  6. Chicken Land (@ChickenLandBot)
  7. Grouche Mine (@GRC_AirdrooBot)
  8. LUM Miner (@lumeonminer_bot)
  9. EarnVault (@EarnVaultApp_bot)
"""

import asyncio
import refresh_cloud_tokens

if __name__ == "__main__":
    asyncio.run(refresh_cloud_tokens.main())
