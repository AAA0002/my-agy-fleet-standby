import json
import re

with open('public_admin/fleet_wallets_data.json', 'r') as f:
    fleet_wallets = json.load(f)

wallets_json_str = json.dumps(fleet_wallets, indent=2)

print("Loaded wallets count:", len(fleet_wallets))
