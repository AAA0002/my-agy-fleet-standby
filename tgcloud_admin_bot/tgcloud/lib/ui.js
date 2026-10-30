import { CONFIG } from './config.js';

export function getMainMenuKeyboard(revokedCount) {
  const revText = revokedCount !== undefined ? ` [${revokedCount}]` : '';
  return {
    inline_keyboard: [
      [
        { text: "🚀 Open WebApp Console ↗️", web_app: { url: "https://app8858823950.tgcloud.ai/" } }
      ],
      [
        { text: "📱 Fleet Accounts [18]", callback_data: "btn_fleet_accounts" },
        { text: "➕ Link Session", callback_data: "btn_add_account" }
      ],
      [
        { text: "🔑 1-Tap OTP Vault", callback_data: "btn_otp_menu" },
        { text: `🔄 Session Recovery${revText}`, callback_data: "btn_relink_menu" }
      ],
      [
        { text: "⚡ Farm 8-Bot Fleet", callback_data: "btn_farm_all" },
        { text: "📊 Telemetry Live", callback_data: "btn_system_status" }
      ],
      [
        { text: "💼 Treasury Wallets", callback_data: "btn_wallets" },
        { text: "🌐 Global Edge Mesh", callback_data: "btn_mesh_status" }
      ],
      [
        { text: "🔄 Refresh Dashboard", callback_data: "btn_refresh_menu" }
      ]
    ]
  };
}

export function getPersistentReplyKeyboard() {
  return {
    keyboard: [
      [
        { text: "🚀 Open WebApp Console ↗️", web_app: { url: "https://app8858823950.tgcloud.ai/" } }
      ],
      [
        { text: "📱 Fleet Nodes" },
        { text: "💼 Web Wallets" }
      ],
      [
        { text: "🔑 1-Tap OTP" },
        { text: "⚡ Farm 5 Bots" }
      ],
      [
        { text: "📊 Status & Mesh" },
        { text: "🔄 Refresh Menu" }
      ]
    ],
    resize_keyboard: true,
    is_persistent: true
  };
}

export function getLoginCancelReplyKeyboard() {
  return {
    keyboard: [
      [{ text: "❌ Cancel Authentication" }]
    ],
    resize_keyboard: true,
    is_persistent: true
  };
}

export function getCancelLoginKeyboard() {
  return {
    inline_keyboard: [
      [{ text: "❌ Abort Authentication", callback_data: "btn_cancel_login" }]
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

export function buildAccountsKeyboard(accounts = [], filter = 'all', actionPrefix = 'btn_account_view_') {
  const filtered = accounts.filter(acc => {
    if (filter === 'active') return acc.status === 'active';
    if (filter === 'revoked') return acc.status === 'revoked' || acc.status === 'inactive';
    return true;
  });

  const activeCount = accounts.filter(a => a.status === 'active').length;
  const revokedCount = accounts.filter(a => a.status === 'revoked' || a.status === 'inactive').length;

  const rows = [];
  
  // Interactive Filter Tabs
  rows.push([
    { text: filter === 'all' ? `• All [${accounts.length || 18}] •` : `All [${accounts.length || 18}]`, callback_data: "btn_filter_all" },
    { text: filter === 'active' ? `• 🟢 Online [${activeCount}] •` : `🟢 Online [${activeCount}]`, callback_data: "btn_filter_active" },
    { text: filter === 'revoked' ? `• 🔴 Revoked [${revokedCount}] •` : `🔴 Revoked [${revokedCount}]`, callback_data: "btn_filter_revoked" }
  ]);

  // Account Nodes Grid (3 Columns)
  const chunkSize = 3;
  for (let i = 0; i < filtered.length; i += chunkSize) {
    const chunk = filtered.slice(i, i + chunkSize);
    rows.push(chunk.map((acc, cIdx) => {
      const idx = acc.index || (i + cIdx + 1);
      const isHost = String(acc.user_id) === "6727787768";
      const isRev = acc.status === "revoked" || acc.status === "inactive";
      const tag = isHost ? " 👑" : (isRev ? " 🔴" : " 🟢");
      const shortName = (acc.name || `Acc #${idx}`).split(" ")[0];
      const paddedIdx = idx < 10 ? `0${idx}` : `${idx}`;
      return {
        text: `#${paddedIdx} ${shortName}${tag}`,
        callback_data: `${actionPrefix}${idx}`
      };
    }));
  }

  // Quick Action Utilities
  rows.push([
    { text: "➕ Link New Session", callback_data: "btn_add_account" },
    { text: `🔄 Re-link Offline [${revokedCount}]`, callback_data: "btn_relink_menu" }
  ]);
  rows.push([{ text: "🔙 Return to Dashboard", callback_data: "btn_main_menu" }]);
  return { inline_keyboard: rows };
}

export function buildAccountDetailCard(acc = {}) {
  const idx = acc.index || 1;
  const name = acc.name || `Account #${idx}`;
  const uname = acc.username ? `@${acc.username}` : '@None';
  const phone = acc.phone || CONFIG.KNOWN_PHONES[idx] || "Unassigned";
  const uid = acc.user_id || 'N/A';
  const isHealthy = acc.status === 'active';
  const isHost = String(acc.user_id) === "6727787768";

  const tonAddr = acc.ton_wallet?.address || 'Provisioned in Vault';
  const evmAddr = acc.evm_wallet?.address || 'Provisioned in Vault';
  const tronAddr = acc.tron_wallet?.address || 'Provisioned in Vault';
  const solAddr = acc.solana_wallet?.address || 'Provisioned in Vault';
  const btcAddr = acc.btc_wallet?.address || 'Provisioned in Vault';

  return `┌──────────────────────────────┐
│  📱 *NODE #${idx < 10 ? '0' + idx : idx} DOSSIER*           │
└──────────────────────────────┘

• *Operator:* *${name}* ${isHost ? '👑 `HOST`' : ''}
• *Phone:* \`${phone}\`
• *UID:* \`${uid}\`
• *Session:* ${isHealthy ? '🟢 `ACTIVE & CONNECTED`' : '🔴 `REVOKED (RE-LINK NEEDED)`'}
• *Cluster:* \`Render Node 2 (Frankfurt)\`
• *Mining:* \`5 Bots (100% Cloud-First)\`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💼 *MULTI-CHAIN VAULT ADDRESSES:*
• 💎 *TON:* \`${tonAddr}\`
• 🪙 *EVM:* \`${evmAddr}\`
• ⚡ *TRX:* \`${tronAddr}\`
• ☀️ *SOL:* \`${solAddr}\`
• ₿ *BTC:* \`${btcAddr}\`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
${isHealthy 
  ? '✅ *Status:* Session nominal. Farming yield 24/7 in cloud.' 
  : '⚠️ *Status:* Session expired on Telegram DC. Tap 1-Tap Re-link below.'}`;
}

export function buildAccountDetailKeyboard(acc = {}) {
  const idx = acc.index || 1;
  const isHealthy = acc.status === 'active';
  const buttons = [];

  buttons.push([
    { text: "🚀 Open WebApp Wallet ↗️", web_app: { url: "https://app8858823950.tgcloud.ai/" } }
  ]);

  if (isHealthy) {
    buttons.push([
      { text: "🔑 Extract OTP Code", callback_data: `btn_otp_get_${idx}` },
      { text: "⚡ Farm Account", callback_data: `btn_farm_acc_${idx}` }
    ]);
  } else {
    buttons.push([
      { text: `⚡ 1-Tap Re-link Session #${idx} 🔴`, callback_data: `btn_relink_acc_${idx}` }
    ]);
  }

  buttons.push([
    { text: "💼 View Multi-Chain Wallet & Seeds", callback_data: `wallet_view_${idx}` }
  ]);

  buttons.push([
    { text: "📱 Back to Fleet", callback_data: "btn_fleet_accounts" },
    { text: "🔙 Main Menu", callback_data: "btn_main_menu" }
  ]);

  return { inline_keyboard: buttons };
}

export function buildOtpKeyboard(accounts = []) {
  const activeTargets = accounts.filter(a => a.status === 'active');
  const targetList = activeTargets.length > 0 ? activeTargets : accounts;
  const rows = [];
  const chunkSize = 2;

  for (let i = 0; i < targetList.length; i += chunkSize) {
    const chunk = targetList.slice(i, i + chunkSize);
    rows.push(chunk.map(acc => {
      const idx = acc.index;
      const shortName = (acc.name || `Acc #${idx}`).split(" ")[0];
      const isHost = String(acc.user_id) === "6727787768";
      const tag = isHost ? " 👑" : " 🟢";
      return {
        text: `🔑 OTP #${idx < 10 ? '0' + idx : idx} (${shortName})${tag}`,
        callback_data: `btn_otp_get_${idx}`
      };
    }));
  }

  rows.push([
    { text: "📱 All Fleet Accounts", callback_data: "btn_fleet_accounts" },
    { text: "🔙 Main Menu", callback_data: "btn_main_menu" }
  ]);
  return { inline_keyboard: rows };
}

export function buildRelinkKeyboard(accounts = []) {
  const relinkTargets = accounts.filter(a => a.status === 'revoked' || a.status === 'inactive');
  const targetList = relinkTargets.length > 0 ? relinkTargets : accounts;
  const rows = [];
  const chunkSize = 2;

  for (let i = 0; i < targetList.length; i += chunkSize) {
    const chunk = targetList.slice(i, i + chunkSize);
    rows.push(chunk.map(acc => {
      const idx = acc.index;
      const shortName = (acc.name || `Acc #${idx}`).split(" ")[0];
      return {
        text: `⚡ Re-link #${idx < 10 ? '0' + idx : idx} (${shortName}) 🔴`,
        callback_data: `btn_relink_acc_${idx}`
      };
    }));
  }

  rows.push([{ text: "🔙 Return to Dashboard", callback_data: "btn_main_menu" }]);
  return { inline_keyboard: rows };
}

export function buildDashboardBanner(live = {}) {
  const total = live.total_accounts || 18;
  const active = live.healthy_count !== undefined ? live.healthy_count : (live.accounts ? live.accounts.filter(a => a.status === 'active').length : 7);
  const revoked = live.revoked_count !== undefined ? live.revoked_count : (total - active);

  // Mobile-optimized 10-segment visual health bar (never wraps on narrow phones)
  const totalSegments = 10;
  const greenSegments = Math.round((active / total) * totalSegments);
  const redSegments = totalSegments - greenSegments;
  const healthBar = "🟩".repeat(greenSegments) + "🟥".repeat(redSegments);
  const pct = Math.round((active / total) * 100);

  return `┌──────────────────────────────┐
│  ⚡ *AAA AUTO SENTINEL V8*   │
│  _Enterprise Fleet Console_  │
└──────────────────────────────┘

📡 *STATUS:* \`🟢 ONLINE • NOMINAL\`
☁️ *PLATFORM:* \`Telegram Serverless Edge\`
💾 *DB:* \`Native SQLite WAL + Upstash\`
🌐 *CLUSTER:* \`Render Frankfurt (Coordinator)\`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 *FLEET HEALTH: ${active}/${total} (${pct}%)*
${healthBar}
• 🟢 *Active Sessions:* \`${active} Online\`
• 🔴 *Revoked Sessions:* \`${revoked} Offline\`
• 👑 *Master Host:* \`#11 MD. ARIF HOSSAIN\`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 *8-BOT AUTONOMOUS MINING SUITE*
◈ ⚡ MRG Miner      ◈ 🪙 ATF Miner
◈ 🏢 Victor's Co.   ◈ 🌐 Kynex Net
◈ ⛏️ DiggoMiner     ◈ 🐸 PepeGram
◈ 🤖 AdxEarn AI     ◈ 🐔 Chicken Land

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💼 *TREASURY:* \`TON • EVM • TRX • SOL • BTC\`
🔒 *SECURITY:* \`0 Phone Load • Non-Custodial\`

Select an operational directive below:`;
}

export function buildMeshStatusBanner(live = {}) {
  const total = live.total_accounts || 18;
  const active = live.healthy_count !== undefined ? live.healthy_count : (live.accounts ? live.accounts.filter(a => a.status === 'active').length : 7);

  return `┌──────────────────────────────────────┐
│  🌐 *GLOBAL INFRASTRUCTURE MESH*     │
│  _Triple-Tier Redundant Cloud_       │
└──────────────────────────────────────┘

☁️ *TIER 1: TELEGRAM SERVERLESS PLATFORM*
• Runtime: \`V8 Isolated Global Edge\`
• App ID: \`app8858823950 (@myagyai)\`
• Webhook: \`https://cloud.telegram.org/app8858823950/webhook\` (🟢 In Sync)
• Storage: \`Native SQLite WAL Database\`

🌐 *TIER 2: CLOUDFLARE 5-NODE EDGE MESH*
• Node 1 (aaaai2.workers.dev): \`🟢 Primary Cron Farming\`
• Node 2 (aaa-bot.workers.dev): \`🟢 Passive Hot Standby\`
• Node 3 (aaa222.workers.dev): \`🟢 Passive Hot Standby\`
• Node 4 (agorameet.workers.dev): \`🟢 Passive Hot Standby\`
• Node 5 (aaaai.workers.dev): \`🟢 Passive Hot Standby\`

🚀 *TIER 3: RENDER CLUSTER & UPSTASH REDIS*
• Primary Host: \`Node 2 Frankfurt\` (🟢 200 OK Coordinator)
• Standby Failover: \`Node 3 Oregon\` & \`Node 1 Singapore\`
• Distributed DB: \`internal-dodo-83852.upstash.io\` (🟢 10k Quota)

📱 *LOCAL HOST (SAMSUNG GALAXY A30):*
• Mode: \`100% Dedicated Pair Programming CLI\`
• Daemon Load: \`0 Local Bots (Rule 4 Zero Phone Load)\`
• Active Nodes: \`${active}/${total} Managed Remotely\``;
}

export function buildWalletsBanner() {
  return `┌──────────────────────────────────────┐
│  💼 *FLEET TREASURY & MULTI-CHAIN*   │
│  _Cryptographic Non-Custodial Vault_ │
└──────────────────────────────────────┘

Every node in the 18-account fleet is provisioned with an isolated cryptographic wallet suite across 5 major blockchains:

• 💎 *TON Ecosystem (v4R2):*
  Dedicated non-custodial 24-word seed mnemonics bound directly to MRG and ATF Telegram WebApps.

• 🪙 *EVM / BSC (BEP-20):*
  Dedicated private keys for BNB Chain and Ethereum yield extraction.

• ⚡ *TRON Network (TRC-20):*
  Dedicated addresses for USDT and TRC-20 farming contracts.

• ☀️ *Solana Network:*
  Dedicated Ed25519 keypairs for Solana ecosystem airdrops.

• ₿ *Bitcoin (Native SegWit):*
  P2WPKH bech32 addresses for satoshi accumulation.

🔐 *Non-Custodial Architecture:*
All private keys and recovery seeds are permanently encrypted in the Master Secrets Vault. Zero automatic withdrawals enabled (100% Accumulation Mode).`;
}

export function buildPinPadKeyboard(currentDigits = '', accountIndex = 1) {
  const digitsStr = String(currentDigits || '');
  const slots = [0, 1, 2, 3, 4].map(i => digitsStr[i] ? digitsStr[i] : '•').join('  ');
  const padIdx = accountIndex < 10 ? '0' + accountIndex : accountIndex;

  return {
    inline_keyboard: [
      [
        { text: `🔑 Code: [ ${slots} ]`, callback_data: "pin_ignore" }
      ],
      [
        { text: "1", callback_data: "pin_digit_1" },
        { text: "2", callback_data: "pin_digit_2" },
        { text: "3", callback_data: "pin_digit_3" }
      ],
      [
        { text: "4", callback_data: "pin_digit_4" },
        { text: "5", callback_data: "pin_digit_5" },
        { text: "6", callback_data: "pin_digit_6" }
      ],
      [
        { text: "7", callback_data: "pin_digit_7" },
        { text: "8", callback_data: "pin_digit_8" },
        { text: "9", callback_data: "pin_digit_9" }
      ],
      [
        { text: "⌫ Del", callback_data: "pin_backspace" },
        { text: "0", callback_data: "pin_digit_0" },
        { text: "✅ Verify", callback_data: "pin_submit" }
      ],
      [
        { text: `📱 Switch to 1-Tap QR Login (Node #${padIdx})`, callback_data: `btn_qr_login_acc_${accountIndex}` }
      ],
      [
        { text: "🔐 Enter via Secure WebApp ↗️", web_app: { url: "https://app8858823950.tgcloud.ai/" } }
      ],
      [
        { text: "❌ Cancel", callback_data: "btn_cancel_login" }
      ]
    ]
  };
}

export function buildQrLoginKeyboard(accountIndex = 1, qrUrl = '') {
  const padIdx = accountIndex < 10 ? '0' + accountIndex : accountIndex;
  const rows = [];
  if (qrUrl) {
    rows.push([
      { text: "🔗 Link Device on This Phone ↗️", url: qrUrl }
    ]);
  }
  rows.push([
    { text: "⌨️ Enter SMS Code via PIN Pad", callback_data: `btn_pinpad_acc_${accountIndex}` },
    { text: "🔄 Refresh QR", callback_data: `btn_qr_login_acc_${accountIndex}` }
  ]);
  rows.push([
    { text: "🔐 Open Secure WebApp ↗️", web_app: { url: "https://app8858823950.tgcloud.ai/" } }
  ]);
  rows.push([
    { text: "❌ Cancel & Main Menu", callback_data: "btn_main_menu" }
  ]);
  return { inline_keyboard: rows };
}
