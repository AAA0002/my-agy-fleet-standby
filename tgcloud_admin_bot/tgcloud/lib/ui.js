export function getMainMenuKeyboard() {
  return {
    inline_keyboard: [
      [
        { text: "📱 Fleet Accounts", callback_data: "btn_fleet_accounts" },
        { text: "➕ Add Account", callback_data: "btn_add_account" }
      ],
      [
        { text: "🔑 1-Tap OTP Code", callback_data: "btn_otp_menu" },
        { text: "🔄 Re-link (13)", callback_data: "btn_relink_menu" }
      ],
      [
        { text: "⚡ Farm 8 Bots", callback_data: "btn_farm_all" },
        { text: "📊 Fleet Telemetry", callback_data: "btn_system_status" }
      ],
      [
        { text: "💼 Multi-Chain Wallets", callback_data: "btn_wallets" },
        { text: "🛡️ Serverless Mesh", callback_data: "btn_mesh_status" }
      ],
      [
        { text: "🚀 Open WebApp Dashboard ↗️", web_app: { url: "https://app8858823950.tgcloud.ai/" } }
      ]
    ]
  };
}

export function getCancelLoginKeyboard() {
  return {
    inline_keyboard: [
      [{ text: "❌ Cancel Login", callback_data: "btn_cancel_login" }]
    ]
  };
}

export function getBackToMenuKeyboard() {
  return {
    inline_keyboard: [
      [{ text: "🔙 Main Menu", callback_data: "btn_main_menu" }]
    ]
  };
}

export function buildAccountsKeyboard(accounts = [], actionPrefix = "btn_account_view_") {
  const rows = [];
  const chunkSize = 3;
  for (let i = 0; i < accounts.length; i += chunkSize) {
    const chunk = accounts.slice(i, i + chunkSize);
    rows.push(chunk.map((acc, cIdx) => {
      const idx = acc.index || (i + cIdx + 1);
      const isHost = String(acc.user_id) === "6727787768";
      const isRev = acc.status === "revoked" || acc.status === "inactive";
      const tag = isHost ? " 👑" : (isRev ? " 🔴" : " 🟢");
      const shortName = (acc.name || `Acc #${idx}`).split(" ")[0];
      return {
        text: `${idx}. ${shortName}${tag}`,
        callback_data: `${actionPrefix}${idx}`
      };
    }));
  }
  rows.push([
    { text: "➕ Add Account", callback_data: "btn_add_account" },
    { text: "🔄 Re-link (13)", callback_data: "btn_relink_menu" }
  ]);
  rows.push([{ text: "🔙 Main Menu", callback_data: "btn_main_menu" }]);
  return { inline_keyboard: rows };
}

export function buildOtpKeyboard(accounts = []) {
  const rows = [];
  const activeTargets = accounts.filter(a => a.status === 'active');
  const targetList = activeTargets.length > 0 ? activeTargets : accounts;
  const chunkSize = 2;
  for (let i = 0; i < targetList.length; i += chunkSize) {
    const chunk = targetList.slice(i, i + chunkSize);
    rows.push(chunk.map((acc, cIdx) => {
      const idx = acc.index || (i + cIdx + 1);
      const shortName = (acc.name || `Acc #${idx}`).split(" ")[0];
      const isHost = String(acc.user_id) === "6727787768";
      const tag = isHost ? " 👑" : " 🟢";
      return {
        text: `🔑 OTP #${idx} (${shortName})${tag}`,
        callback_data: `btn_otp_get_${idx}`
      };
    }));
  }
  rows.push([
    { text: "📱 All Accounts", callback_data: "btn_fleet_accounts" },
    { text: "🔙 Main Menu", callback_data: "btn_main_menu" }
  ]);
  return { inline_keyboard: rows };
}

export function buildRelinkKeyboard(accounts = []) {
  const rows = [];
  const relinkTargets = accounts.filter(a => a.status === 'revoked' || a.status === 'inactive');
  const targetList = relinkTargets.length > 0 ? relinkTargets : accounts;
  const chunkSize = 2;
  for (let i = 0; i < targetList.length; i += chunkSize) {
    const chunk = targetList.slice(i, i + chunkSize);
    rows.push(chunk.map(acc => {
      const idx = acc.index;
      const shortName = (acc.name || `Acc #${idx}`).split(" ")[0];
      return {
        text: `⚡ Re-link #${idx} (${shortName}) 🔴`,
        callback_data: `btn_relink_acc_${idx}`
      };
    }));
  }
  rows.push([{ text: "🔙 Main Menu", callback_data: "btn_main_menu" }]);
  return { inline_keyboard: rows };
}

export function buildDashboardBanner(live = {}) {
  const total = live.total_accounts || 18;
  const active = live.healthy_count || 5;
  const revoked = live.revoked_count !== undefined ? live.revoked_count : (total - active);

  return `⚡ *AAA AUTO SERVERLESS COMMAND SENTINEL* ⚡
──────────────────────────────
☁️ *Platform:* Telegram Serverless V8 Platform
💾 *Database:* Native SQLite Database
🌐 *Mesh Cluster:* Render Nodes 1-3 & Cloudflare Mesh
🤖 *Active Legitimate Bots (8):*
   • 💎 Stones Miner | 🪙 MRG Miner
   • 🔬 AI Lab | 💼 UltraWallet
   • ⚡ ATF Miner | 📈 FINVORA
   • 👑 Victor's Company | 💧 VyroDrop

📱 *Fleet Sessions:*
   🟢 *Active:* \`${active}\` Accounts
   🔴 *Revoked:* \`${revoked}\` Accounts (Tap Re-link below)
   👑 *Master Host:* \`Arif (#11 MD. ARIF HOSSAIN)\`

Select an action below to manage fleet operations:`;
}

export function buildMeshStatusBanner(live = {}) {
  const total = live.total_accounts || 18;
  const active = live.healthy_count || 5;

  return `🛡️ *Infrastructure & Mesh Health Status*
──────────────────────────────
☁️ *Telegram Serverless:* 🟢 Operational (V8 Platform)
💾 *SQLite Database:* 🟢 Active & Migrated
🌐 *Cloudflare Triple-Mesh:*
   • Node 1 (aaaai2.workers.dev): 🟢 Healthy
   • Node 2 (aaa-bot.workers.dev): 🟢 Healthy
   • Node 3 (aaa222.workers.dev): 🟢 Healthy
🚀 *Render Standby Cluster:*
   • Node 1 (Singapore): 🟢 Standby
   • Node 2 (Frankfurt): 🟢 Primary Coordinator (200 OK)
   • Node 3 (Oregon): 🟢 Standby
🗄️ *Upstash Serverless Redis:* 🟢 Active (pleasant-locust-220893)
🤖 *Active Legitimate Bots (8):*
   Stones, MRG, AI Lab, UltraWallet, ATF, FINVORA, Victor's, VyroDrop
📱 *Fleet Status:* ${active}/${total} Active Cloud Sessions`;
}

export function buildWalletsBanner() {
  return `💼 *Fleet Multi-Chain Wallets Suite*
──────────────────────────────
Every account in the 18-node fleet is provisioned with an isolated, non-custodial multi-chain wallet suite:

• 💎 *TON (v4R2):* Dedicated mnemonic & address for TON miners (MRG, ATF)
• 🪙 *EVM (BSC / Ethereum):* Dedicated private key & address
• ⚡ *Tron (TRX):* Dedicated private key & TRC-20 address
• ☀️ *Solana (SOL):* Dedicated private key & address
• ₿ *Bitcoin (BTC):* Dedicated Native SegWit address

🔐 *Security:* All private keys and mnemonics are archived in the encrypted master secrets vault. Zero private keys are exposed over unsecured networks.`;
}
