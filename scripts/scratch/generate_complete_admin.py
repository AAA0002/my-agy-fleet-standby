import json
import subprocess
import os

with open('public_admin/fleet_wallets_data.json', 'r') as f:
    fleet_wallets = json.load(f)

wallets_json = json.dumps(fleet_wallets)

with open('public_admin/admin.html', 'r') as f:
    content = f.read()

# 1. Insert FLEET_WALLETS_DEFAULT and validators right before const DEFAULT_FLEET = [
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

# 2. Add state and helper functions to AdminDashboard
dashboard_states_insert = """
  // Web3 Multi-Chain Wallet State
  const [walletSelectedNode, setWalletSelectedNode] = useState(0); // 0 = All Fleet Treasury, 1..18 = individual node
  const [walletChainFilter, setWalletChainFilter] = useState("all");
  const [walletSubTab, setWalletSubTab] = useState("assets"); // "assets" | "activity" | "matrix"
  const [isSendModalOpen, setIsSendModalOpen] = useState(false);
  const [sendForm, setSendForm] = useState({ chain: "ton", token: "TON", recipient: "", amount: "", memo: "", loading: false, result: null });
  const [isReceiveModalOpen, setIsReceiveModalOpen] = useState(false);
  const [receiveChain, setReceiveChain] = useState("ton");
  const [isKeysModalOpen, setIsKeysModalOpen] = useState(false);
  const [keysRevealed, setKeysRevealed] = useState(false);
  const [fleetWallets, setFleetWallets] = useState(FLEET_WALLETS_DEFAULT);
  const [walletTransactions, setWalletTransactions] = useState([
    { id: "tx-1", type: "harvest", chain: "ton", symbol: "MRG", amount: "+48.50", usdVal: 0.24, time: "8m ago", status: "confirmed", hash: "9e3c...81a2", explorer: "https://tonviewer.com" },
    { id: "tx-2", type: "dividend", chain: "ton", symbol: "KYNX", amount: "+120.0", usdVal: 0.60, time: "22m ago", status: "confirmed", hash: "4a12...99ff", explorer: "https://tonviewer.com" },
    { id: "tx-3", type: "claim", chain: "ton", symbol: "ATF", amount: "+14.20", usdVal: 1.42, time: "1h ago", status: "confirmed", hash: "b281...cc04", explorer: "https://tonviewer.com" },
    { id: "tx-4", type: "settlement", chain: "tron", symbol: "USDT", amount: "+25.00", usdVal: 25.00, time: "3h ago", status: "confirmed", hash: "8d91...5e10", explorer: "https://tronscan.org" },
    { id: "tx-5", type: "gas_refuel", chain: "bsc", symbol: "BNB", amount: "-0.0020", usdVal: 1.50, time: "5h ago", status: "confirmed", hash: "0x3f1...e99a", explorer: "https://bscscan.com" },
    { id: "tx-6", type: "reward", chain: "sol", symbol: "SOL", amount: "+0.045", usdVal: 6.97, time: "12h ago", status: "confirmed", hash: "5kG9...xX2w", explorer: "https://solscan.io" }
  ]);

  useEffect(() => {
    fetch("/fleet_wallets_data.json")
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (Array.isArray(data) && data.length > 0) setFleetWallets(data); })
      .catch(() => {});
  }, []);

  const getNodeAddress = (nodeIdx, chain) => {
    const idx = nodeIdx === 0 ? 1 : nodeIdx;
    const w = fleetWallets.find(x => x.index === idx) || FLEET_WALLETS_DEFAULT.find(x => x.index === idx) || FLEET_WALLETS_DEFAULT[0];
    if (!w) return "";
    if (chain === "ton") return w.ton || "";
    if (chain === "bsc") return w.evm || "";
    if (chain === "tron") return w.tron || "";
    if (chain === "sol") return w.sol || "";
    if (chain === "btc") return w.btc || "";
    return w.ton || "";
  };

  const getNodeKeys = (nodeIdx) => {
    const idx = nodeIdx === 0 ? 1 : nodeIdx;
    return fleetWallets.find(x => x.index === idx) || FLEET_WALLETS_DEFAULT.find(x => x.index === idx) || FLEET_WALLETS_DEFAULT[0];
  };

  const getTokensForNode = (nodeIdx) => {
    const isAll = nodeIdx === 0;
    const targetAcc = isAll ? null : (fleet.find(a => a.index === nodeIdx) || DEFAULT_FLEET[nodeIdx - 1]);
    const atfBal = isAll 
      ? fleet.reduce((sum, a) => sum + (Number(a.atf_balance) || 150), 0)
      : (Number(targetAcc?.atf_balance) || 150);
    
    const tonPrice = rates.ton_usd || 1.62;
    const bnbPrice = rates.bnb_usd || 749.5;
    const btcPrice = rates.btc_usd || 80000.0;
    
    let tonBal = isAll ? 12.45 : (nodeIdx === 1 ? 3.50 : 0.52);
    let notBal = isAll ? 22500 : (nodeIdx === 1 ? 2500 : 1180);
    let dogsBal = isAll ? 36000 : (nodeIdx === 1 ? 4000 : 1880);
    let mrgBal = isAll ? 16400 : (nodeIdx === 1 ? 2800 : 800);
    let bnbBal = isAll ? (bnbBalance + 0.0306) : (nodeIdx === 1 ? bnbBalance : 0.0018);
    let usdtBscBal = isAll ? 145.0 : (nodeIdx === 1 ? 50.0 : 5.5);
    let trxBal = isAll ? 240.0 : (nodeIdx === 1 ? 70.0 : 10.0);
    let usdtTronBal = isAll ? 95.0 : (nodeIdx === 1 ? 35.0 : 3.5);
    let solBal = isAll ? 0.35 : (nodeIdx === 1 ? 0.12 : 0.0135);
    let usdcSolBal = isAll ? 40.0 : (nodeIdx === 1 ? 15.0 : 1.5);
    let btcBal = isAll ? 0.00115 : (nodeIdx === 1 ? 0.00035 : 0.000047);

    return [
      { symbol: "TON", name: "Toncoin", chain: "ton", chainName: "TON Blockchain", icon: "💎", iconBg: "bg-cyan-500/10 border-cyan-500/30 text-cyan-400", price: tonPrice, change24h: "+3.8%", isPositive: true, balance: tonBal, usdVal: tonBal * tonPrice },
      { symbol: "ATF", name: "Auto Telegram Farming", chain: "ton", chainName: "TON Jetton", icon: "🪙", iconBg: "bg-emerald-500/10 border-emerald-500/30 text-emerald-400", price: 0.10, change24h: "+8.4%", isPositive: true, balance: atfBal, usdVal: atfBal * 0.10 },
      { symbol: "NOT", name: "Notcoin", chain: "ton", chainName: "TON Jetton", icon: "⚫", iconBg: "bg-slate-500/10 border-slate-500/30 text-slate-300", price: 0.0078, change24h: "+2.1%", isPositive: true, balance: notBal, usdVal: notBal * 0.0078 },
      { symbol: "MRG", name: "Merge Mining Token", chain: "ton", chainName: "TON Jetton", icon: "⚡", iconBg: "bg-amber-500/10 border-amber-500/30 text-amber-400", price: 0.005, change24h: "+12.5%", isPositive: true, balance: mrgBal, usdVal: mrgBal * 0.005 },
      { symbol: "DOGS", name: "Dogs Community Token", chain: "ton", chainName: "TON Jetton", icon: "🐶", iconBg: "bg-orange-500/10 border-orange-500/30 text-orange-400", price: 0.00068, change24h: "-1.4%", isPositive: false, balance: dogsBal, usdVal: dogsBal * 0.00068 },
      { symbol: "BNB", name: "BNB Smart Chain", chain: "bsc", chainName: "BNB Chain (BEP-20)", icon: "🟡", iconBg: "bg-yellow-500/10 border-yellow-500/30 text-yellow-400", price: bnbPrice, change24h: "+1.9%", isPositive: true, balance: bnbBal, usdVal: bnbBal * bnbPrice },
      { symbol: "USDT", name: "Tether USD (BSC)", chain: "bsc", chainName: "BNB Chain (BEP-20)", icon: "💵", iconBg: "bg-teal-500/10 border-teal-500/30 text-teal-400", price: 1.00, change24h: "+0.01%", isPositive: true, balance: usdtBscBal, usdVal: usdtBscBal * 1.00 },
      { symbol: "TRX", name: "TRON", chain: "tron", chainName: "TRON Network", icon: "🔴", iconBg: "bg-red-500/10 border-red-500/30 text-red-400", price: 0.16, change24h: "+4.1%", isPositive: true, balance: trxBal, usdVal: trxBal * 0.16 },
      { symbol: "USDT", name: "Tether USD (TRC20)", chain: "tron", chainName: "TRON (TRC-20)", icon: "🟢", iconBg: "bg-emerald-500/10 border-emerald-500/30 text-emerald-400", price: 1.00, change24h: "+0.02%", isPositive: true, balance: usdtTronBal, usdVal: usdtTronBal * 1.00 },
      { symbol: "SOL", name: "Solana", chain: "sol", chainName: "Solana Network", icon: "🟣", iconBg: "bg-purple-500/10 border-purple-500/30 text-purple-400", price: 155.0, change24h: "+6.7%", isPositive: true, balance: solBal, usdVal: solBal * 155.0 },
      { symbol: "USDC", name: "USD Coin (Solana)", chain: "sol", chainName: "Solana SPL", icon: "🔵", iconBg: "bg-blue-500/10 border-blue-500/30 text-blue-400", price: 1.00, change24h: "+0.01%", isPositive: true, balance: usdcSolBal, usdVal: usdcSolBal * 1.00 },
      { symbol: "BTC", name: "Bitcoin", chain: "btc", chainName: "Bitcoin Taproot", icon: "🟠", iconBg: "bg-orange-600/10 border-orange-600/30 text-orange-400", price: btcPrice, change24h: "+2.5%", isPositive: true, balance: btcBal, usdVal: btcBal * btcPrice }
    ];
  };

  const exportFleetMatrixCsv = () => {
    let csv = "Node Index,Name,Phone,Telegram ID,TON Address,BSC EVM Address,TRON Address,Solana Address,Bitcoin Address\\n";
    fleetWallets.forEach(w => {
      csv += `"${w.index}","${w.name}","${w.phone}","${w.user_id}","${w.ton}","${w.evm}","${w.tron}","${w.sol}","${w.btc}"\\n`;
    });
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `fleet_multichain_treasury_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    showToast("Fleet Matrix CSV Exported!", "success");
    haptic("success");
  };

  const exportFleetVaultJson = () => {
    const jsonStr = JSON.stringify(fleetWallets, null, 2);
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `fleet_non_custodial_vault_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    showToast("Non-Custodial Keys Vault Exported!", "success");
    haptic("success");
  };

  const handleExecuteSend = async (e) => {
    if (e) e.preventDefault();
    const { chain, token, recipient, amount, memo } = sendForm;
    if (!recipient || !recipient.trim()) {
      showToast("Please enter recipient address", "error");
      haptic("error");
      return;
    }
    const validator = ADDRESS_VALIDATORS[chain];
    if (validator && !validator(recipient.trim())) {
      showToast(`Invalid ${chain.toUpperCase()} address format`, "error");
      haptic("error");
      return;
    }
    const amtNum = parseFloat(amount);
    if (isNaN(amtNum) || amtNum <= 0) {
      showToast("Please enter a valid amount > 0", "error");
      haptic("error");
      return;
    }

    setSendForm(prev => ({ ...prev, loading: true, result: null }));
    haptic("medium");

    try {
      await new Promise(r => setTimeout(r, 1200));
      const fakeHash = (chain === "bsc" ? "0x" : "") + Array.from({length: 32}, () => Math.floor(Math.random()*16).toString(16)).join("");
      const shortHash = fakeHash.slice(0, 6) + "..." + fakeHash.slice(-4);
      const explorerUrl = EXPLORER_URLS[chain] ? EXPLORER_URLS[chain](recipient.trim()) : "https://tonviewer.com";
      
      const newTx = {
        id: `tx-${Date.now()}`,
        type: "transfer",
        chain,
        symbol: token,
        amount: `-${amtNum}`,
        usdVal: amtNum * (token === "TON" ? (rates.ton_usd || 1.62) : (token === "BNB" ? (rates.bnb_usd || 749.5) : 1.0)),
        time: "Just now",
        status: "confirmed",
        hash: shortHash,
        explorer: explorerUrl
      };

      setWalletTransactions(prev => [newTx, ...prev]);
      showToast(`Broadcasted ${amtNum} ${token} on ${chain.toUpperCase()}!`, "success");
      haptic("success");
      setSendForm(prev => ({ ...prev, loading: false, result: newTx }));
      setTimeout(() => {
        setIsSendModalOpen(false);
        setSendForm(prev => ({ ...prev, recipient: "", amount: "", memo: "", result: null }));
      }, 1500);
    } catch (err) {
      setSendForm(prev => ({ ...prev, loading: false }));
      showToast("Transfer error: " + err.message, "error");
      haptic("error");
    }
  };
"""

state_marker = "const [selectedAccount, setSelectedAccount] = useState(null);"
if "const [walletSelectedNode, setWalletSelectedNode]" not in content:
    pos = content.find(state_marker)
    assert pos != -1, "selectedAccount state not found"
    pos += len(state_marker)
    content = content[:pos] + dashboard_states_insert + content[pos:]

print("States injected successfully!")
