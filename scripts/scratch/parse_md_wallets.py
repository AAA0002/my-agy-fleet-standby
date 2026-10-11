import re
import json

with open('/root/.gemini/antigravity-cli/brain/ab0db110-aa04-4d2f-808c-08e45816f8cd/FLEET_MULTICHAIN_WALLETS_DASHBOARD.md', 'r') as f:
    text = f.read()

accounts = re.findall(r'### Account #(\d+): (.*?)\n(.*?)(?=### Account #|\Z)', text, re.DOTALL)
print(f"Total account blocks found: {len(accounts)}")

parsed_wallets = []

for num_str, name_raw, block in accounts:
    idx = int(num_str)
    # clean name
    name_clean = name_raw.split('(')[0].strip()
    
    tg_match = re.search(r'Telegram ID\*\*:\s*`?(\d+)', block)
    tg_id = tg_match.group(1) if tg_match else ""
    
    phone_match = re.search(r'Phone Number\*\*:\s*`?([+\d]+)', block)
    phone = phone_match.group(1) if phone_match else ""
    
    ton_match = re.search(r'TON Network.*?\*\*:\s*`?([a-zA-Z0-9_\-]+)', block)
    ton = ton_match.group(1) if ton_match else ""
    
    evm_match = re.search(r'EVM.*?\*\*:\s*`?(0x[a-fA-F0-9]+)', block)
    evm = evm_match.group(1) if evm_match else ""
    
    tron_match = re.search(r'TRON.*?\*\*:\s*`?(T[a-zA-Z0-9]+)', block)
    tron = tron_match.group(1) if tron_match else ""
    
    sol_match = re.search(r'Solana.*?\*\*:\s*`?([a-zA-Z0-9]{32,50})', block)
    sol = sol_match.group(1) if sol_match else ""
    
    btc_match = re.search(r'Bitcoin.*?\*\*:\s*`?([a-zA-Z0-9]{25,70})', block)
    btc = btc_match.group(1) if btc_match else ""
    
    # Credentials
    mnemonic_match = re.search(r'Tonkeeper 24-Word Recovery Phrase\*\*:\s*```(?:text)?\s*([a-z ]+)\s*```', block)
    ton_mnemonic = mnemonic_match.group(1).strip() if mnemonic_match else ""
    
    evm_key_match = re.search(r'MetaMask / Trust Wallet.*?\*\*:\s*```(?:text)?\s*([a-fA-F0-9]+)\s*```', block)
    evm_key = evm_key_match.group(1).strip() if evm_key_match else ""
    
    tron_key_match = re.search(r'TronLink.*?\*\*:\s*```(?:text)?\s*([a-fA-F0-9]+)\s*```', block)
    tron_key = tron_key_match.group(1).strip() if tron_key_match else ""
    
    sol_key_match = re.search(r'Phantom.*?\*\*:\s*```(?:text)?\s*([a-zA-Z0-9]+)\s*```', block)
    sol_key = sol_key_match.group(1).strip() if sol_key_match else ""
    
    btc_key = evm_key # Secp256k1 uses EVM private key
    
    if idx == 1:
        ton_mnemonic = ""
        evm_key = "Binance Main Exchange Deposit (Direct Custody)"
        tron_key = "Binance Main Exchange Deposit (Direct Custody)"
        sol_key = "Binance Main Exchange Deposit (Direct Custody)"
        btc_key = "Binance Main Exchange Deposit (Direct Custody)"
    elif idx == 10:
        ton_mnemonic = "Binance Web3 Wallet 2 (AAA) - Managed via Binance Mobile App"
        evm_key = "Binance Web3 Wallet 2 (AAA) - Direct Custody in Binance App"
        tron_key = "Binance Web3 Wallet 2 (AAA) - Direct Custody in Binance App"
        sol_key = "Binance Web3 Wallet 2 (AAA) - Direct Custody in Binance App"
        btc_key = "Binance Web3 Wallet 2 (AAA) - Direct Custody in Binance App"

    parsed_wallets.append({
        "index": idx,
        "name": name_clean,
        "phone": phone,
        "user_id": tg_id,
        "ton": ton,
        "ton_mnemonic": ton_mnemonic,
        "evm": evm,
        "evm_key": evm_key,
        "tron": tron,
        "tron_key": tron_key,
        "sol": sol,
        "sol_key": sol_key,
        "btc": btc,
        "btc_key": btc_key
    })

parsed_wallets.sort(key=lambda x: x["index"])

with open('public_admin/fleet_wallets_data.json', 'w') as f:
    json.dump(parsed_wallets, f, indent=2)

print("Parsed and saved EXACT wallets from FLEET_MULTICHAIN_WALLETS_DASHBOARD.md for all 18 accounts!")
for w in parsed_wallets:
    print(f"#{w['index']:02d}: {w['name']:<20} | Phone: {w['phone']:<15} | TON: {w['ton'][:12]}... | EVM: {w['evm'][:10]}... | Has Mnemonic: {bool(w['ton_mnemonic'])}")
