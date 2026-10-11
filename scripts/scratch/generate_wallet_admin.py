import json
import re
import subprocess

# 1. Load fleet wallets data
with open('public_admin/fleet_wallets_data.json', 'r') as f:
    fleet_wallets = json.load(f)

fleet_wallets_json = json.dumps(fleet_wallets, indent=2)

# 2. Read existing admin.html
with open('public_admin/admin.html', 'r') as f:
    orig = f.read()

# Let's verify markers
assert "const DEFAULT_FLEET = [" in orig, "DEFAULT_FLEET marker missing"
assert "// TAB 2: TREASURY & DESTINATION WALLETS" in orig, "TAB 2 marker missing"
assert "// TAB 3: ARI AI MULTI-MODEL STUDIO" in orig, "TAB 3 marker missing"
assert "isAddModalOpen && React.createElement(\"div\"," in orig, "isAddModalOpen marker missing"

print("All markers verified successfully!")
