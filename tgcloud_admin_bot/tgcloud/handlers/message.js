import { api, db } from 'sdk';
import { eq } from 'sdk/db';
import { loginSessions } from '../schema.js';
import { CONFIG } from '../lib/config.js';
import { sendLoginCode, verifyLoginCode, cancelLogin, fetchFleetLive, markAccountActive, requestBackend } from '../lib/backend.js';
import {
  getMainMenuKeyboard,
  getCancelLoginKeyboard,
  buildOtpKeyboard,
  buildRelinkKeyboard,
  buildAccountsKeyboard,
  buildDashboardBanner,
  buildMeshStatusBanner,
  buildWalletsBanner
} from '../lib/ui.js';

function normalizePhone(raw) {
  let cleaned = String(raw || '').replace(/[^0-9+]/g, '');
  if (cleaned.startsWith('01') && cleaned.length === 11) {
    cleaned = '+88' + cleaned;
  } else if (!cleaned.startsWith('+') && cleaned.length >= 8) {
    cleaned = '+' + cleaned;
  }
  return cleaned;
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

  // 2. Preemptive Cancel Check (Supports /cancel, cancel, ❌ Cancel Login, ❌, etc.)
  const isCancel = /cancel/i.test(rawText) || rawText.includes('❌');
  if (isCancel) {
    cancelLogin(chatId);
    await db.delete(loginSessions).where(eq(loginSessions.chatId, chatId)).run().catch(() => {});

    // Wipe persistent ReplyKeyboardMarkup button from the user's Telegram client
    await api.sendMessage({
      chat_id: chatId,
      text: "🧹 *Authentication flow cancelled & keyboard cleared.*",
      parse_mode: "Markdown",
      reply_markup: { remove_keyboard: true }
    });

    const live = await fetchFleetLive();
    await api.sendMessage({
      chat_id: chatId,
      text: buildDashboardBanner(live),
      parse_mode: "Markdown",
      reply_markup: getMainMenuKeyboard(live.revoked_count || 13)
    });
    return;
  }

  // 3. Preemptive Command Router (Any command starting with '/' cancels active login state)
  const isCommand = rawText.startsWith('/');
  if (isCommand) {
    cancelLogin(chatId);
    await db.delete(loginSessions).where(eq(loginSessions.chatId, chatId)).run().catch(() => {});

    const cmd = rawText.split(' ')[0].toLowerCase();

    if (cmd === '/start' || cmd === '/menu') {
      // First wipe any stuck ReplyKeyboardMarkup
      await api.sendMessage({
        chat_id: chatId,
        text: "⚡ *AAA AUTO Command Sentinel Ready*",
        parse_mode: "Markdown",
        reply_markup: { remove_keyboard: true }
      });

      const live = await fetchFleetLive();
      await api.sendMessage({
        chat_id: chatId,
        text: buildDashboardBanner(live),
        parse_mode: "Markdown",
        reply_markup: getMainMenuKeyboard(live.revoked_count || 13)
      });
      return;
    }

    if (cmd === '/otp' || cmd === '/code') {
      const live = await fetchFleetLive();
      const text = `┌──────────────────────────────────────┐
│  🔑 *1-TAP TELEGRAM OTP VAULT*       │
│  _Instant MTProto Authorization_     │
└──────────────────────────────────────┘

Select an active account node below to instantly inspect the latest Telegram verification code:`;
      await api.sendMessage({
        chat_id: chatId,
        text,
        parse_mode: "Markdown",
        reply_markup: buildOtpKeyboard(live.accounts)
      });
      return;
    }

    if (cmd === '/relink') {
      const live = await fetchFleetLive();
      const revokedCount = live.revoked_count || 13;
      const text = `┌──────────────────────────────────────┐
│  🔄 *FLEET SESSION RECOVERY CENTER*  │
│  _Automated 1-Tap Re-Authentication_ │
└──────────────────────────────────────┘

⚠️ *Offline Fleet Sessions:* \`${revokedCount} Nodes Require Renewal\`

Tap any account node below to dispatch an official verification code:`;
      await api.sendMessage({
        chat_id: chatId,
        text,
        parse_mode: "Markdown",
        reply_markup: buildRelinkKeyboard(live.accounts)
      });
      return;
    }

    if (cmd === '/accounts' || cmd === '/fleet') {
      const live = await fetchFleetLive();
      const text = `📱 *FLEET ACCOUNTS MATRIX (${live.healthy_count || 5}/${live.total_accounts || 18} ACTIVE)*\n\n🟢 = Active MTProto Session\n🔴 = Session Revoked / Needs Re-link\n👑 = Master Host Account\n\nSelect an account node below to inspect dossier:`;
      await api.sendMessage({
        chat_id: chatId,
        text,
        parse_mode: "Markdown",
        reply_markup: buildAccountsKeyboard(live.accounts, 'all')
      });
      return;
    }

    if (cmd === '/status' || cmd === '/mesh') {
      const live = await fetchFleetLive();
      await api.sendMessage({
        chat_id: chatId,
        text: buildMeshStatusBanner(live),
        parse_mode: "Markdown",
        reply_markup: getMainMenuKeyboard(live.revoked_count || 13)
      });
      return;
    }

    if (cmd === '/wallets') {
      await api.sendMessage({
        chat_id: chatId,
        text: buildWalletsBanner(),
        parse_mode: "Markdown",
        reply_markup: getMainMenuKeyboard(13)
      });
      return;
    }

    if (cmd === '/farm') {
      await api.sendMessage({
        chat_id: chatId,
        text: "⚡ *Triggering Mining Cycle Across All 8 Legitimate Bots...*\n\n• Dispatched to Render Standby primary coordinator...",
        parse_mode: "Markdown"
      });
      requestBackend('/api/farm/cloud-all', 'POST', {}).catch(() => {});
      
      const banner = 
`┌──────────────────────────────────────┐
│  ⚡ *AUTONOMOUS 8-BOT MINING CYCLE*  │
└──────────────────────────────────────┘

🚀 Dispatched multi-farming cycle across all 18 nodes:

◈ 💎 *Stones Miner*      → Harvesting & Compounding
◈ 🪙 *MRG Miner*         → Turnstile Pass Verification & Harvest
◈ 🔬 *AI Lab*            → Research Task Claims
◈ 💼 *UltraWallet*       → Point Staking & Yield
◈ ⚡ *ATF Miner*         → Cloud Captcha & Mining Cycle
◈ 📈 *FINVORA*           → Yield Harvesting
◈ 👑 *Victor's Company*  → Proof-of-Pass & Level Compounding
◈ 💧 *VyroDrop*          → Wallet Sync & Airdrop Farming

📡 *Cluster Execution:* \`Render Standby Node 2 (Frankfurt)\`
⚡ *Phone Impact:* \`0% CPU • 0% RAM • 100% Cloud Execution\``;

      await api.sendMessage({
        chat_id: chatId,
        text: banner,
        parse_mode: "Markdown",
        reply_markup: getMainMenuKeyboard(13)
      });
      return;
    }

    // Default unknown command
    await api.sendMessage({
      chat_id: chatId,
      text: `🤖 *AAA AUTO Sentinel*\n\nCommand \`${cmd}\` not recognized.\nTap /menu or /start to open the fleet dashboard.`,
      parse_mode: "Markdown",
      reply_markup: getMainMenuKeyboard(13)
    });
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

Telegram dispatched an official 5-digit verification code to \`${cleanPhone}\`.

Please reply directly with the code (e.g. \`12345\`):`,
          parse_mode: "Markdown",
          reply_markup: getCancelLoginKeyboard()
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

      await api.sendMessage({
        chat_id: chatId,
        text: `🔄 *Verifying Telegram Code \`${cleanCode}\` on cloud cluster...*`,
        parse_mode: "Markdown"
      });

      const res = await verifyLoginCode({
        chatId,
        code: cleanCode,
        phone: activeSession.phone,
        nodeUrl: activeSession.nodeUrl,
        index: activeSession.accountIndex
      });

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
• *Autonomous Mining:* \`Bound to 8 Legitimate Bots\`${dupNotice}

Node updated in active cloud cluster.`,
          parse_mode: "Markdown",
          reply_markup: getMainMenuKeyboard(live.revoked_count || 12)
        });
        return;
      }

      await api.sendMessage({
        chat_id: chatId,
        text: `❌ *Verification Failed*\n\n*Error:* ${res?.error || 'Invalid code'}\n\nPlease check the code and reply again:`,
        parse_mode: "Markdown",
        reply_markup: getCancelLoginKeyboard()
      });
      return;
    }

    // Step 3: Waiting for 2FA password
    if (activeSession.step === 'WAITING_2FA') {
      await api.sendMessage({
        chat_id: chatId,
        text: `🔐 *Authenticating Two-Factor Password on cloud cluster...*`,
        parse_mode: "Markdown"
      });

      const res = await verifyLoginCode({
        chatId,
        password: rawText,
        phone: activeSession.phone,
        nodeUrl: activeSession.nodeUrl,
        index: activeSession.accountIndex
      });

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
• *Autonomous Mining:* \`Bound to 8 Legitimate Bots\`${dupNotice}

Node updated in active cloud cluster.`,
          parse_mode: "Markdown",
          reply_markup: getMainMenuKeyboard(live.revoked_count || 12)
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
      await db.delete(loginSessions).where(eq(loginSessions.chatId, chatId)).run();
      await db.insert(loginSessions).values({
        chatId,
        step: 'WAITING_2FA'
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
        reply_markup: getMainMenuKeyboard(live.revoked_count || 12)
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
      await db.delete(loginSessions).where(eq(loginSessions.chatId, chatId)).run();
      await db.insert(loginSessions).values({
        chatId,
        step: 'WAITING_CODE',
        phone: directPhone,
        phoneCodeHash: res.phone_code_hash || '',
        accountIndex,
        nodeUrl: res.nodeUrl || ''
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
    text: `🤖 *AAA AUTO Sentinel Command Bot*\n\nTap /menu or /start to open the fleet dashboard.`,
    parse_mode: "Markdown",
    reply_markup: getMainMenuKeyboard(13)
  });
}
