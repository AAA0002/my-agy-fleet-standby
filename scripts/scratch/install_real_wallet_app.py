import re
import json
import subprocess

with open('wallet_states_code.js', 'r', encoding='utf-8') as f:
    wallet_states = f.read().strip()

with open('wallet_tab_code.js', 'r', encoding='utf-8') as f:
    wallet_tab = f.read().strip()

with open('wallet_modals_code.js', 'r', encoding='utf-8') as f:
    wallet_modals = f.read().strip()

with open('public_admin/admin.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 1. Locate wallet states block
# Starts with line containing "Web3 Multi-Chain" or "walletSelectedNode"
start_state_idx = None
end_state_idx = None

for i, l in enumerate(lines):
    if '// Web3 Multi-Chain' in l or 'const [walletSelectedNode' in l:
        if start_state_idx is None:
            start_state_idx = i
    if '// Add Account Modal State' in l or 'const [isAddModalOpen' in l:
        if end_state_idx is None and start_state_idx is not None:
            end_state_idx = i
            break

print(f"State block found: lines {start_state_idx + 1} to {end_state_idx + 1}")

# 2. Locate Tab 2 block
start_tab2_idx = None
end_tab2_idx = None

for i, l in enumerate(lines):
    if 'activeTab === "wallets"' in l:
        # Walk backwards to find comment if any
        j = i - 1
        while j >= 0 and ('//' in lines[j] or lines[j].strip() == ''):
            j -= 1
        start_tab2_idx = j + 1
    if 'activeTab === "ai"' in l and start_tab2_idx is not None:
        # Walk backwards to find comment
        j = i - 1
        while j >= 0 and ('//' in lines[j] or lines[j].strip() == ''):
            j -= 1
        end_tab2_idx = j + 1
        break

print(f"Tab 2 block found: lines {start_tab2_idx + 1} to {end_tab2_idx + 1}")

# 3. Locate Modals block
start_modals_idx = None
end_modals_idx = None

for i, l in enumerate(lines):
    if 'isSendModalOpen && React.createElement' in l:
        j = i - 1
        while j >= 0 and ('//' in lines[j] or lines[j].strip() == ''):
            j -= 1
        start_modals_idx = j + 1
    if 'ReactDOM.render(' in l and start_modals_idx is not None:
        # Walk backwards past closing brackets
        j = i - 1
        while j >= 0 and lines[j].strip() not in [')', ');', '}', '})()', '})()']:
            j -= 1
        # The closing of the dashboard component is ');'
        # The modals end right before ');\n}'
        # Let's find 'isKeysModalOpen' end
        end_modals_idx = None
        for k in range(start_modals_idx, i):
            if 'Download Encrypted JSON Vault Backup' in lines[k]:
                # Next few lines close the modal
                m = k + 1
                while m < i and lines[m].strip() != '})()':
                    m += 1
                end_modals_idx = m + 1
                break
        break

print(f"Modals block found: lines {start_modals_idx + 1} to {end_modals_idx + 1}")

assert start_state_idx is not None and end_state_idx is not None
assert start_tab2_idx is not None and end_tab2_idx is not None
assert start_modals_idx is not None and end_modals_idx is not None

# Now reconstruct lines
# Part 1: before state block
new_lines = lines[:start_state_idx]
# Insert state block
new_lines.append("  " + wallet_states + "\n\n")
# Part 2: between state and Tab 2
new_lines.extend(lines[end_state_idx:start_tab2_idx])
# Insert Tab 2 block
new_lines.append("    " + wallet_tab + ",\n\n")
# Part 3: between Tab 2 and Modals
new_lines.extend(lines[end_tab2_idx:start_modals_idx])
# Insert Modals block
new_lines.append("    " + wallet_modals + "\n\n")
# Part 4: after Modals
new_lines.extend(lines[end_modals_idx:])

full_content = "".join(new_lines)

# Write to admin.html
with open('public_admin/admin.html', 'w', encoding='utf-8') as f:
    f.write(full_content)

# Synchronize to admin/index.html
with open('public_admin/admin/index.html', 'w', encoding='utf-8') as f:
    f.write(full_content)

print("Merged real wallet app successfully into public_admin/admin.html and admin/index.html!")

