import json

with open('public_admin/fleet_wallets_data.json') as f:
    wallets = json.load(f)

print("Test OK, wallets loaded:", len(wallets))
