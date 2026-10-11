import json
import subprocess
import os

with open('public_admin/fleet_wallets_data.json', 'r') as f:
    fleet_wallets = json.load(f)

wallets_json = json.dumps(fleet_wallets)

with open('wallet_states_code.js', 'r') as f:
    states_code = f.read()

with open('wallet_tab_code.js', 'r') as f:
    tab_code = f.read()

with open('wallet_modals_code.js', 'r') as f:
    modals_code = f.read()

with open('public_admin/admin.html', 'r') as f:
    content = f.read()

# 1. Top data structures
top_insert = f"""const FLEET_WALLETS_DEFAULT = {wallets_json};

const ADDRESS_VALIDATORS = {{
  ton: (addr) => Boolean(addr && (/^(EQ|UQ)[a-zA-Z0-9_-]{{46}}$/.test(addr) || /\\.ton$/i.test(addr))),
  bsc: (addr) => Boolean(addr && /^0x[a-fA-F0-9]{{40}}$/.test(addr)),
  tron: (addr) => Boolean(addr && /^T[a-km-zA-HJ-NP-Z1-9]{{33}}$/.test(addr)),
  sol: (addr) => Boolean(addr && /^[1-9A-HJ-NP-Za-km-z]{{32,44}}$/.test(addr)),
  btc: (addr) => Boolean(addr && /^(1|3|bc1)[a-zA-HJ-NP-Z0-9]{{25,62}}$/.test(addr))
}};

const EXPLORER_URLS = {{
  ton: (addr) => `https://tonviewer.com/${{addr}}`,
  bsc: (addr) => `https://bscscan.com/address/${{addr}}`,
  tron: (addr) => `https://tronscan.org/#/address/${{addr}}`,
  sol: (addr) => `https://solscan.io/account/${{addr}}`,
  btc: (addr) => `https://mempool.space/address/${{addr}}`
}};

"""

if "const FLEET_WALLETS_DEFAULT =" not in content:
    target_pos = content.find("const DEFAULT_FLEET = [")
    assert target_pos != -1, "DEFAULT_FLEET not found"
    content = content[:target_pos] + top_insert + content[target_pos:]
    print("Inserted FLEET_WALLETS_DEFAULT")

# 2. Add state and helper functions to AdminDashboard
state_marker = "const [selectedAccount, setSelectedAccount] = useState(null);"
if "const [walletSelectedNode, setWalletSelectedNode]" not in content:
    pos = content.find(state_marker)
    assert pos != -1, "selectedAccount state not found"
    pos += len(state_marker)
    content = content[:pos] + "\n" + states_code + "\n" + content[pos:]
    print("Inserted wallet states and helper functions")

# 3. Replace TAB 2 section
tab2_start = content.find("// TAB 2: TREASURY & DESTINATION WALLETS")
assert tab2_start != -1, "Tab 2 start marker not found"
tab3_start = content.find("// ==========================================================\n    // TAB 3: ARI AI MULTI-MODEL STUDIO")
if tab3_start == -1:
    tab3_start = content.find("// TAB 3: ARI AI MULTI-MODEL STUDIO")
assert tab3_start != -1, "Tab 3 marker not found"

content = content[:tab2_start] + tab_code + ",\n\n    " + content[tab3_start:]
print("Replaced Tab 2 with Web3 Wallet App")

# 4. Inject Modals right after isAddModalOpen
closing_needle = "addStep === \"success\" && React.createElement(\"div\", { className: \"py-4 text-center space-y-2\" },"
pos = content.find(closing_needle)
assert pos != -1, "closing_needle not found"

closing_bracket = "        )\n      )\n    )"
closing_pos = content.find(closing_bracket, pos)
assert closing_pos != -1, "closing_bracket not found"
closing_pos += len(closing_bracket)

content = content[:closing_pos] + ",\n\n" + modals_code.strip() + content[closing_pos:]
print("Injected Send, Receive, and Keys Vault modals")

# 5. Save updated admin.html
with open('public_admin/admin.html', 'w') as f:
    f.write(content)
print("Updated public_admin/admin.html successfully!")

# 6. Synchronize public_admin/admin/index.html
with open('public_admin/admin/index.html', 'w') as f:
    f.write(content)
print("Synchronized public_admin/admin/index.html successfully!")
