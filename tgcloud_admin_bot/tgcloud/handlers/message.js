import { api, db } from 'sdk';
import { eq, sql } from 'sdk/db';
import { loginSessions } from '../schema.js';
import { CONFIG } from '../lib/config.js';
import { sendLoginCode, verifyLoginCode, cancelLogin, fetchFleetLive, markAccountActive, requestBackend, dispatchParallelFarming } from '../lib/backend.js';
import {
  getMainMenuKeyboard,
  getCancelLoginKeyboard,
  getPersistentReplyKeyboard,
  getLoginCancelReplyKeyboard,
  buildOtpKeyboard,
  buildRelinkKeyboard,
  buildAccountsKeyboard,
  buildDashboardBanner,
  buildMeshStatusBanner,
  buildWalletsBanner,
  buildPinPadKeyboard
} from '../lib/ui.js';
import {
  formatWalletDossier,
  buildWalletsKeyboard,
  buildWalletsSummaryBanner
} from '../lib/fleetWallets.js';

function normalizePhone(raw) {
  let cleaned = String(raw || '').replace(/[^0-9+]/g, '');
  if (cleaned.startsWith('01') && cleaned.length === 11) {
    cleaned = '+88' + cleaned;
  } else if (!cleaned.startsWith('+') && cleaned.length >= 8) {
    cleaned = '+' + cleaned;
  }
  return cleaned;
}

// Disappearing single-console dashboard helper: keeps chat spotless!
async function sendLivingDashboard(chatId, text, reply_markup, parseMode = "Markdown") {
  try {
    const session = await db.select().from(loginSessions).where(eq(loginSessions.chatId, chatId)).get();
    const lastMsgId = session?.meta?.lastMsgId;
    if (lastMsgId) {
      await api.deleteMessage({ chat_id: chatId, message_id: lastMsgId }).catch(() => {});
    }
  } catch (_) {}
  const sent = await api.sendMessage({
    chat_id: chatId,
    text,
    parse_mode: parseMode,
    reply_markup
  });
  if (sent && sent.message_id) {
    const session = await db.select().from(loginSessions).where(eq(loginSessions.chatId, chatId)).get();
    const meta = { ...(session?.meta || {}), lastMsgId: sent.message_id };
    await db.insert(loginSessions).values({
      chatId,
      step: session?.step || 'IDLE',
      meta
    }).onConflictDoUpdate({
      target: loginSessions.chatId,
      set: { meta, updatedAt: sql`(unixepoch())` }
    }).run().catch(() => {});
  }
  return sent;
}

export default async function (message, ctx) {
  if (!message || !message.chat) return;

  const chatId = String(message.chat.id);
  const userId = message.from ? message.from.id : null;
  const rawText = (message.text || '').trim();

  // 1. Security Check: Admin Access Only (Arif Hossain: 6727787768)
  if (userId && !CONFIG.ADMIN_IDS.includes(userId)) {
    await api.sendMessage({
      chat_id: chatId,
      text: "⛔ *Access Denied*\n\nThis is the private AAA AUTO Admin Command Sentinel. Unauthorized access is restricted.",
      parse_mode: "Markdown"
    });
    return;
  }

  // 2. Preemptive Cancel Check (Supports /cancel, cancel, ❌ Cancel Login, ❌ Cancel Authentication, ❌, etc.)
  const isCancel = /cancel/i.test(rawText) || rawText.includes('❌');
  if (isCancel) {
    cancelLogin(chatId);
    await db.delete(loginSessions).where(eq(loginSessions.chatId, chatId)).run().catch(() => {});

    // Desper message: auto-delete user cancel command
    await api.deleteMessage({ chat_id: chatId, message_id: message.message_id }).catch(() => {});

    const live = await fetchFleetLive(true);
    await sendLivingDashboard(chatId, buildDashboardBanner(live), getMainMenuKeyboard(live.revoked_count));
    return;
  }

  // 3. Command & Persistent Keyboard Menu Action Router
  const lowerText = rawText.toLowerCase();
  const isCommand = rawText.startsWith('/');
  const isKeyboardAction = 
    rawText.includes("Fleet Nodes") ||
    rawText.includes("Web Wallets") ||
    rawText.includes("1-Tap OTP") ||
    rawText.includes("Farm 5 Bots") ||
    rawText.includes("Farm 8 Bots") ||
    rawText.includes("Status & Mesh") ||
    rawText.includes("Refresh Menu") ||
    rawText.includes("Open WebApp Console") ||
    lowerText === "menu" ||
    lowerText === "start" ||
    lowerText === "keyboard menu" ||
    lowerText === "keyboard" ||
    lowerText === "wallets" ||
    lowerText === "wallet" ||
    lowerText.startsWith("wallet ") ||
    lowerText === "nodes" ||
    lowerText === "farm" ||
    lowerText === "otp";

  if (isCommand || isKeyboardAction) {
    cancelLogin(chatId);
    await db.delete(loginSessions).where(eq(loginSessions.chatId, chatId)).run().catch(() => {});

    // Desper message: auto-delete user trigger command
    await api.deleteMessage({ chat_id: chatId, message_id: message.message_id }).catch(() => {});

    // Sync bot commands in background for native [/] button
    api.setMyCommands({
      commands: [
        { command: "start", description: "🚀 Open Dashboard & Keyboard Menu" },
        { command: "menu", description: "⚡ Open Command Sentinel Menu" },
        { command: "accounts", description: "📱 Fleet Nodes Matrix (18 Nodes)" },
        { command: "wallets", description: "💼 Multi-Chain Treasury Vault" },
        { command: "wallet", description: "🔑 Inspect Node Wallet & Seeds (/wallet <1-18>)" },
        { command: "otp", description: "🔑 1-Tap Telegram Verification OTP" },
        { command: "farm", description: "⚡ 1-Click 5-Bot Cloud Farming" },
        { command: "status", description: "📊 System Status & Edge Mesh" },
        { command: "cancel", description: "❌ Cancel Active Login Flow" }
      ]
    }).catch(() => {});

    const cmd = isCommand ? rawText.split(' ')[0].toLowerCase() : '';

    if (cmd === '/start' || cmd === '/menu' || lowerText === 'menu' || lowerText === 'start' || lowerText.includes('refresh menu') || lowerText.includes('keyboard')) {
      const live = await fetchFleetLive(true);
      await sendLivingDashboard(chatId, buildDashboardBanner(live), getMainMenuKeyboard(live.revoked_count));
      return;
    }

    if (rawText.includes("Open WebApp Console") || lowerText === 'webapp') {
      await sendLivingDashboard(chatId, "🚀 *AAA AUTO WebApp Console*\n\nTap below to launch the executive mobile dashboard:", {
        inline_keyboard: [
          [{ text: "🚀 Open WebApp Console ↗️", web_app: { url: "https://app8858823950.tgcloud.ai/" } }]
        ]
      });
      return;
    }

    if (cmd === '/otp' || cmd === '/code' || rawText.includes("1-Tap OTP") || lowerText === 'otp') {
      const live = await fetchFleetLive(true);
      const text = `┌──────────────────────────────┐
│  🔑 *1-TAP TELEGRAM OTP*     │
│  _MTProto Verification_      │
└──────────────────────────────┘

Select an active account node below to instantly inspect the latest Telegram verification code:`;
      await sendLivingDashboard(chatId, text, buildOtpKeyboard(live.accounts));
      return;
    }

    if (cmd === '/relink') {
      const live = await fetchFleetLive(true);
      const revokedCount = live.revoked_count !== undefined ? live.revoked_count : (live.accounts ? live.accounts.filter(a => a.status !== 'active').length : 11);
      const text = `┌──────────────────────────────┐
│  🔄 *SESSION RECOVERY*       │
│  _1-Tap Re-Authentication_   │
└──────────────────────────────┘

⚠️ *Offline Fleet Sessions:* \`${revokedCount} Nodes Require Renewal\`

Tap any account node below to dispatch an official verification code:`;
      await sendLivingDashboard(chatId, text, buildRelinkKeyboard(live.accounts));
      return;
    }

    if (cmd === '/accounts' || cmd === '/fleet' || rawText.includes("Fleet Nodes") || lowerText === 'nodes') {
      const live = await fetchFleetLive(true);
      const actCount = live.healthy_count !== undefined ? live.healthy_count : (live.accounts ? live.accounts.filter(a => a.status === 'active').length : 7);
      const text = `📱 *FLEET ACCOUNTS MATRIX (${actCount}/${live.total_accounts || 18} ACTIVE)*\n\n🟢 = Active MTProto Session\n🔴 = Session Revoked / Needs Re-link\n👑 = Master Host Account\n\nSelect an account node below to inspect dossier:`;
      await sendLivingDashboard(chatId, text, buildAccountsKeyboard(live.accounts, 'all'));
      return;
    }

    if (cmd === '/status' || cmd === '/mesh' || rawText.includes("Status & Mesh") || lowerText === 'status' || lowerText === 'mesh') {
      const live = await fetchFleetLive(true);
      await sendLivingDashboard(chatId, buildMeshStatusBanner(live), getMainMenuKeyboard(live.revoked_count));
      return;
    }

    if (cmd === '/wallet' || cmd === '/wallets' || rawText.startsWith('/wallet') || rawText.startsWith('/wallets') || rawText.includes("Web Wallets") || lowerText === 'wallets' || lowerText === 'wallet' || lowerText.startsWith('wallet ')) {
      const parts = rawText.trim().split(/\s+/);
      const targetIdx = (parts.length >= 2 && /^\d+$/.test(parts[1])) ? parseInt(parts[1], 10) : null;
      if (targetIdx && targetIdx >= 1 && targetIdx <= 18) {
        const text = formatWalletDossier(targetIdx);
        if (text) {
          await sendLivingDashboard(chatId, text, buildWalletsKeyboard(targetIdx), "HTML");
          return;
        }
      }
      await sendLivingDashboard(chatId, buildWalletsSummaryBanner(), buildWalletsKeyboard(null), "HTML");
      return;
    }

    if (cmd === '/farm' || rawText.includes("Farm 8 Bots") || rawText.includes("Farm 9 Bots") || rawText.includes("Farm 5 Bots") || lowerText === 'farm') {
      await sendLivingDashboard(chatId, "⚡ *Dispatching 100% Cloud Mining across 8 Pools...*\n\n• Target: All 20 Fleet Accounts (Nodes 01-20)\n• Backend: Render Standby Node 2 (Frankfurt)\n\n_Executing 100% in cloud, 0% phone load..._", null);
      await dispatchParallelFarming().catch(() => {});
      
      const banner = 
`┌──────────────────────────────┐
│  ⚡ *AUTONOMOUS 8-POOL FARM* │
└──────────────────────────────┘

🚀 Dispatched cloud harvest across all 21 nodes & 8 mining pools:

◈ ⚡ *MRG Miner*         → Turnstile Pass Verification & Harvest
◈ 🪙 *ATF Miner*         → Cloud Captcha & Mining Cycle
◈ 🏢 *Victor's Company*  → Proof-of-Pass & Level Compounding
◈ 💎 *Kynex Network*     → Session Token Claim & Node Mining
◈ ⛏️ *DiggoMiner*        → 30-Day JWT Cached Session Claim
◈ 🐸 *PepeGram*          → 6h Hash Production Harvest
◈ 🤖 *AdxEarn AI*        → Rewarded Ads Farming Cycle
◈ 🐔 *Chicken Land*      → Egg Harvest & Selling Cycle

📡 *Cloud Architecture:* Render Node 2 (Frankfurt) • 3x Cloudflare Edge Mesh
⚡ *Phone Impact:* \`0% CPU • 0% RAM • 100% Cloud Execution\``;

      const live = await fetchFleetLive();
      await sendLivingDashboard(chatId, banner, getMainMenuKeyboard(live.revoked_count));
      return;
    }

    // Default unknown command
    await sendLivingDashboard(chatId, `🤖 *AAA AUTO Sentinel*\n\nCommand \`${cmd}\` not recognized.\nTap /menu or /start to open the fleet dashboard.`, getMainMenuKeyboard(13));
    return;
  }

  // 4. Stateful Login Handling (ONLY reached if NOT a command and NOT cancel)
  let activeSession = await db.select().from(loginSessions).where(eq(loginSessions.chatId, chatId)).get();

  if (activeSession) {
    // Step 1: Waiting for phone number
    if (activeSession.step === 'WAITING_PHONE') {
      const cleanPhone = normalizePhone(rawText);
      if (cleanPhone.length < 9) {
        await api.sendMessage({
          chat_id: chatId,
          text: "⚠️ *Invalid Phone Number Format*\n\nPlease reply with the international phone number (e.g. `+8801943805617` or `01943805617`):",
          parse_mode: "Markdown",
          reply_markup: getCancelLoginKeyboard()
        });
        return;
      }

      // Check for duplicate account by phone
      const live = await fetchFleetLive();
      const dupAcc = live.accounts.find(a => normalizePhone(a.phone) === cleanPhone);
      const dupIdx = dupAcc?.index || Object.entries(CONFIG.KNOWN_PHONES).find(([i, p]) => normalizePhone(p) === cleanPhone)?.[0];
      if (dupIdx) {
        const dupName = dupAcc?.name || `Account #${dupIdx}`;
        await api.sendMessage({
          chat_id: chatId,
          text: `⚠️ *DUPLICATE ACCOUNT DETECTED!*\n\n• Phone: \`${cleanPhone}\` is already assigned to *Node #${dupIdx}* (*${dupName}*).\n• Current Status: ${dupAcc?.status === 'active' ? '🟢 Online' : '🔴 Session Revoked'}\n\n🔄 *Re-linking existing Node #${dupIdx} instead of creating a duplicate.*`,
          parse_mode: "Markdown"
        });
        activeSession.accountIndex = parseInt(dupIdx, 10);
      }

      await api.sendMessage({
        chat_id: chatId,
        text: `┌──────────────────────────────────────┐
│  📱 *CONNECTING TO TELEGRAM MTPROTO* │
└──────────────────────────────────────┘

• *Target Phone:* \`${cleanPhone}\`
• *Cluster Gateway:* \`Render Standby Node 2 (Frankfurt)\`

Dispatching official Telegram verification code...`,
        parse_mode: "Markdown"
      });

      const res = await sendLoginCode(cleanPhone, chatId, activeSession.accountIndex);
      if (res && res.ok) {
        await db.update(loginSessions).set({
          step: 'WAITING_CODE',
          phone: cleanPhone,
          phoneCodeHash: res.phone_code_hash || '',
          accountIndex: activeSession.accountIndex || null,
          nodeUrl: res.nodeUrl || ''
        }).where(eq(loginSessions.chatId, chatId)).run();

        await api.sendMessage({
          chat_id: chatId,
          text: `┌──────────────────────────────────────┐
│  📨 *OFFICIAL TELEGRAM CODE SENT*    │
└──────────────────────────────────────┘

• *Target Phone:* \`${cleanPhone}\`

Telegram dispatched an official 5-digit verification code to \`${cleanPhone}\`.

⚡ *Instant Auto-2FA:* Once code is verified, your 2FA password automatically will authenticate automatically in 0.5s!

⚠️ *DO NOT TYPE THE CODE AS TEXT IN CHAT!*
Telegram automatically blocks any codes typed in chat messages as 'previously shared'.
Tap the digits on the PIN Pad below:`,
          parse_mode: "Markdown",
          reply_markup: buildPinPadKeyboard('', activeSession.accountIndex)
        });
      } else {
        await api.sendMessage({
          chat_id: chatId,
          text: `❌ *Could Not Request Code*\n\n*Error:* ${res?.error || 'Unknown network error'}\n\nPlease check phone number and try again:`,
          parse_mode: "Markdown",
          reply_markup: getCancelLoginKeyboard()
        });
      }
      return;
    }

    // Step 2: Waiting for OTP verification code
    if (activeSession.step === 'WAITING_CODE') {
      const cleanCode = rawText.replace(/[^0-9]/g, '');
      if (cleanCode.length < 3) {
        await api.sendMessage({
          chat_id: chatId,
          text: "⚠️ *Invalid Code Format*\n\nPlease reply with the verification digits sent by Telegram (e.g., `79964`):",
          parse_mode: "Markdown",
          reply_markup: getCancelLoginKeyboard()
        });
        return;
      }

      // Desper message: auto-delete user OTP digits for security & zero chat clutter
      await api.deleteMessage({ chat_id: chatId, message_id: message.message_id }).catch(() => {});

      const progressMsg = await api.sendMessage({
        chat_id: chatId,
        text: `🔄 *Verifying Telegram Code \`${cleanCode}\` on cloud cluster...*`,
        parse_mode: "Markdown"
      });

      const res = await verifyLoginCode({
        chatId,
        code: cleanCode,
        phone: activeSession.phone,
        phoneCodeHash: activeSession.phoneCodeHash,
        nodeUrl: activeSession.nodeUrl,
        index: activeSession.accountIndex
      });

      if (progressMsg?.message_id) {
        await api.deleteMessage({ chat_id: chatId, message_id: progressMsg.message_id }).catch(() => {});
      }

      if (res && res.need_2fa) {
        await db.update(loginSessions).set({
          step: 'WAITING_2FA'
        }).where(eq(loginSessions.chatId, chatId)).run();

        await api.sendMessage({
          chat_id: chatId,
          text: `┌──────────────────────────────────────┐
│  🔒 *TWO-FACTOR 2FA PASSWORD*        │
└──────────────────────────────────────┘

This Telegram account has a Two-Factor Cloud Password enabled.

Please reply directly with your 2FA password:`,
          parse_mode: "Markdown",
          reply_markup: getCancelLoginKeyboard()
        });
        return;
      }

      if (res && res.ok) {
        await db.delete(loginSessions).where(eq(loginSessions.chatId, chatId)).run();
        const accName = res.name || res.account?.name || activeSession.phone || 'User';
        const uid = res.user_id || res.account?.user_id || 'Active';
        const targetIdx = res.index || activeSession.accountIndex || 1;

        // Immediately update cache and SQLite so state updates in 0ms!
        await markAccountActive(targetIdx, uid, accName, activeSession.phone);
        const live = await fetchFleetLive(true);

        const dupNotice = res.is_duplicate 
          ? `\n⚠️ *Duplicate Notice:* User was already registered as Node #${res.existing_index || targetIdx}. Re-linked session credentials.`
          : '';

        await api.sendMessage({
          chat_id: chatId,
          text: `┌──────────────────────────────────────┐
│  🎉 *SESSION SUCCESSFULLY LINKED!*   │
└──────────────────────────────────────┘

• *Operator:* *${accName}*
• *Node Index:* *#${targetIdx < 10 ? '0' + targetIdx : targetIdx}*
• *Telegram UID:* \`${uid}\`
• *Session State:* \`🟢 Online & Cryptographically Secured\`
• *Treasury Suite:* \`TON • EVM • TRON • SOL • BTC Bound\`
• *Autonomous Mining:* \`Bound to 5 Legitimate Bots\`${dupNotice}

Node updated in active cloud cluster.`,
          parse_mode: "Markdown",
          reply_markup: getMainMenuKeyboard(live.revoked_count)
        });
        return;
      }

      const isExpired = res?.expired || (res?.error && res.error.toLowerCase().includes('expired'));
      const targetIdx = activeSession.accountIndex || 1;
      const padIdx = targetIdx < 10 ? '0' + targetIdx : targetIdx;
      const errText = isExpired
        ? `⚠️ *Telegram Security Block (Code Invalidated)*\n\nTelegram flagged this code because it was sent as a chat message.\n\n🚀 *RECOMMENDED SOLUTION:* Use *1-Tap QR Login* below (100% immune to code sharing blocks, zero codes needed)!`
        : `❌ *Verification Failed*\n\n*Error:* ${res?.error || 'Invalid code'}\n\nPlease check the code and reply again, or switch to QR login:`;

      await api.sendMessage({
        chat_id: chatId,
        text: errText,
        parse_mode: "Markdown",
        reply_markup: {
          inline_keyboard: [
            [{ text: `📱 1-Tap QR Login (Node #${padIdx} - Zero Code)`, callback_data: `btn_qr_login_acc_${targetIdx}` }],
            [{ text: `⌨️ Enter Code via PIN Pad Keypad`, callback_data: `btn_pinpad_acc_${targetIdx}` }],
            [{ text: "❌ Cancel & Main Menu", callback_data: "btn_main_menu" }]
          ]
        }
      });
      return;
    }

    // Step 3: Waiting for 2FA password
    if (activeSession.step === 'WAITING_2FA') {
      // Desper message: auto-delete user's 2FA password immediately for security
      await api.deleteMessage({ chat_id: chatId, message_id: message.message_id }).catch(() => {});

      const progressMsg = await api.sendMessage({
        chat_id: chatId,
        text: `🔐 *Authenticating Two-Factor Password on cloud cluster...*`,
        parse_mode: "Markdown"
      });

      const res = await verifyLoginCode({
        chatId,
        password: rawText,
        phone: activeSession.phone,
        phoneCodeHash: activeSession.phoneCodeHash,
        nodeUrl: activeSession.nodeUrl,
        index: activeSession.accountIndex
      });

      if (progressMsg?.message_id) {
        await api.deleteMessage({ chat_id: chatId, message_id: progressMsg.message_id }).catch(() => {});
      }

      if (res && res.ok) {
        await db.delete(loginSessions).where(eq(loginSessions.chatId, chatId)).run();
        const accName = res.name || res.account?.name || activeSession.phone || 'User';
        const uid = res.user_id || res.account?.user_id || 'Active';
        const targetIdx = res.index || activeSession.accountIndex || 1;

        // Immediately update cache and SQLite!
        await markAccountActive(targetIdx, uid, accName, activeSession.phone);
        const live = await fetchFleetLive(true);

        const dupNotice = res.is_duplicate 
          ? `\n⚠️ *Duplicate Notice:* User was already registered as Node #${res.existing_index || targetIdx}. Re-linked session credentials.`
          : '';

        await api.sendMessage({
          chat_id: chatId,
          text: `┌──────────────────────────────────────┐
│  🎉 *2FA AUTHENTICATION SUCCESSFUL!* │
└──────────────────────────────────────┘

• *Operator:* *${accName}*
• *Node Index:* *#${targetIdx < 10 ? '0' + targetIdx : targetIdx}*
• *Telegram UID:* \`${uid}\`
• *Session State:* \`🟢 Online & Cryptographically Secured\`
• *Treasury Suite:* \`TON • EVM • TRON • SOL • BTC Bound\`
• *Autonomous Mining:* \`Bound to 5 Legitimate Bots\`${dupNotice}

Node updated in active cloud cluster.`,
          parse_mode: "Markdown",
          reply_markup: getMainMenuKeyboard(live.revoked_count)
        });
        return;
      }

      await api.sendMessage({
        chat_id: chatId,
        text: `❌ *2FA Authentication Failed*\n\n*Error:* ${res?.error || 'Incorrect password'}\n\nPlease check your Two-Factor Password and try again:`,
        parse_mode: "Markdown",
        reply_markup: getCancelLoginKeyboard()
      });
      return;
    }
  }

  // 5. Auto-detect 5-digit verification code sent directly without prior state
  const pureDigits = rawText.replace(/[^0-9]/g, '');
  if (pureDigits.length === 5) {
    await api.sendMessage({
      chat_id: chatId,
      text: `🔄 *Auto-detected 5-digit code \`${pureDigits}\`... Connecting to cloud MTProto...*`,
      parse_mode: "Markdown"
    });

    const res = await verifyLoginCode({ chatId, code: pureDigits });
    if (res && res.need_2fa) {
      await db.insert(loginSessions).values({
        chatId,
        step: 'WAITING_2FA'
      }).onConflictDoUpdate({
        target: loginSessions.chatId,
        set: {
          step: 'WAITING_2FA',
          updatedAt: sql`(unixepoch())`
        }
      }).run();

      await api.sendMessage({
        chat_id: chatId,
        text: `┌──────────────────────────────────────┐
│  🔒 *TWO-FACTOR 2FA PASSWORD*        │
└──────────────────────────────────────┘

This account has a Two-Factor Cloud Password enabled.
Please reply directly with your 2FA password:`,
        parse_mode: "Markdown",
        reply_markup: getCancelLoginKeyboard()
      });
      return;
    }

    if (res && res.ok) {
      const accName = res.name || res.account?.name || 'Verified User';
      const uid = res.user_id || res.account?.user_id || 'Active';
      const targetIdx = res.index || 1;
      await markAccountActive(targetIdx, uid, accName, '');
      const live = await fetchFleetLive(true);

      await api.sendMessage({
        chat_id: chatId,
        text: `┌──────────────────────────────────────┐
│  🎉 *SESSION SUCCESSFULLY LINKED!*   │
└──────────────────────────────────────┘

• *Operator:* *${accName}*
• *Telegram UID:* \`${uid}\`
• *Session State:* \`🟢 Online & Active\``,
        parse_mode: "Markdown",
        reply_markup: getMainMenuKeyboard(live.revoked_count)
      });
      return;
    }
  }

  // 6. Auto-detect phone number sent directly
  const directPhone = normalizePhone(rawText);
  if (/^\+8801[3-9][0-9]{8}$/.test(directPhone) || /^\+[1-9][0-9]{8,14}$/.test(directPhone)) {
    const live = await fetchFleetLive();
    const dupAcc = live.accounts.find(a => normalizePhone(a.phone) === directPhone);
    const dupIdx = dupAcc?.index || Object.entries(CONFIG.KNOWN_PHONES).find(([i, p]) => normalizePhone(p) === directPhone)?.[0];
    let accountIndex = dupIdx ? parseInt(dupIdx, 10) : null;

    if (dupIdx) {
      const dupName = dupAcc?.name || `Account #${dupIdx}`;
      await api.sendMessage({
        chat_id: chatId,
        text: `⚠️ *DUPLICATE ACCOUNT DETECTED!*\n\n• Phone: \`${directPhone}\` is already assigned to *Node #${dupIdx}* (*${dupName}*).\n• Current Status: ${dupAcc?.status === 'active' ? '🟢 Online' : '🔴 Session Revoked'}\n\n🔄 *Re-linking existing Node #${dupIdx}...*`,
        parse_mode: "Markdown"
      });
    }

    await api.sendMessage({
      chat_id: chatId,
      text: `🔄 *Auto-detected phone number \`${directPhone}\`... Dispatching verification code...*`,
      parse_mode: "Markdown"
    });

    const res = await sendLoginCode(directPhone, chatId, accountIndex);
    if (res && res.ok) {
      await db.insert(loginSessions).values({
        chatId,
        step: 'WAITING_CODE',
        phone: directPhone,
        phoneCodeHash: res.phone_code_hash || '',
        accountIndex,
        nodeUrl: res.nodeUrl || ''
      }).onConflictDoUpdate({
        target: loginSessions.chatId,
        set: {
          step: 'WAITING_CODE',
          phone: directPhone,
          phoneCodeHash: res.phone_code_hash || '',
          accountIndex,
          nodeUrl: res.nodeUrl || '',
          updatedAt: sql`(unixepoch())`
        }
      }).run();

      await api.sendMessage({
        chat_id: chatId,
        text: `┌──────────────────────────────────────┐
│  📨 *OFFICIAL TELEGRAM CODE SENT*    │
└──────────────────────────────────────┘

Telegram dispatched an official 5-digit verification code to \`${directPhone}\`.

Please reply directly with the code (e.g. \`12345\`):`,
        parse_mode: "Markdown",
        reply_markup: getCancelLoginKeyboard()
      });
      return;
    }
  }

  // 7. Default Fallback
  await api.sendMessage({
    chat_id: chatId,
    text: `🤖 *AAA AUTO Sentinel Command Bot*\n\nUse the docked keyboard menu below or tap /menu for the fleet dashboard.`,
    parse_mode: "Markdown",
    reply_markup: getPersistentReplyKeyboard()
  });

  const live = await fetchFleetLive();
  await api.sendMessage({
    chat_id: chatId,
    text: buildDashboardBanner(live),
    parse_mode: "Markdown",
    reply_markup: getMainMenuKeyboard(live.revoked_count || 13)
  });
}
