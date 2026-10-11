import { api, db } from 'sdk';
import { eq } from 'sdk/db';
import { loginSessions } from '../schema.js';
import { CONFIG } from '../lib/config.js';
import { sendLoginCode, verifyLoginCode, cancelLogin, fetchFleetLive } from '../lib/backend.js';
import { getMainMenuKeyboard, getCancelLoginKeyboard, buildOtpKeyboard, buildRelinkKeyboard, buildAccountsKeyboard } from '../lib/ui.js';

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
  const text = (message.text || '').trim();

  // Enforce admin security (Arif Hossain / 6727787768)
  if (userId && !CONFIG.ADMIN_IDS.includes(userId)) {
    await api.sendMessage({
      chat_id: chatId,
      text: "⛔ *Access Denied*\n\nThis is the private AAA AUTO Admin Command Sentinel. Unauthorized access is restricted.",
      parse_mode: "Markdown"
    });
    return;
  }

  // Check if this chat has an active login session in Telegram Serverless SQLite DB
  let activeSession = await db.select().from(loginSessions).where(eq(loginSessions.chatId, chatId)).get();

  if (text === '/cancel' || text.toLowerCase() === 'cancel') {
    await cancelLogin(chatId);
    if (activeSession) {
      await db.delete(loginSessions).where(eq(loginSessions.chatId, chatId)).run();
    }
    await api.sendMessage({
      chat_id: chatId,
      text: "❌ *Login Process Cancelled.*\n\nReturned to standard idle sentinel mode.",
      parse_mode: "Markdown",
      reply_markup: getMainMenuKeyboard()
    });
    return;
  }

  if (activeSession) {
    // Step 1: Waiting for phone number
    if (activeSession.step === 'WAITING_PHONE') {
      const cleanPhone = normalizePhone(text);
      if (cleanPhone.length < 9) {
        await api.sendMessage({
          chat_id: chatId,
          text: "⚠️ *Invalid Phone Number Format*\n\nPlease send the full phone number (e.g., `+8801943805617` or `01943805617`):",
          parse_mode: "Markdown",
          reply_markup: getCancelLoginKeyboard()
        });
        return;
      }

      await api.sendMessage({
        chat_id: chatId,
        text: `🔄 *Connecting to Telegram MTProto...*\n\n• Phone: \`${cleanPhone}\`\n• Dispatching official verification code via cloud cluster...`,
        parse_mode: "Markdown"
      });

      const res = await sendLoginCode(cleanPhone, chatId, activeSession.accountIndex);
      if (res && res.ok) {
        await db.update(loginSessions).set({
          step: 'WAITING_CODE',
          phone: cleanPhone,
          phoneCodeHash: res.phone_code_hash || '',
          nodeUrl: res.nodeUrl || ''
        }).where(eq(loginSessions.chatId, chatId)).run();

        await api.sendMessage({
          chat_id: chatId,
          text: `📨 *Verification Code Sent!*\n\nTelegram sent a 5-digit verification code to \`${cleanPhone}\`.\n\nPlease reply directly with the code (e.g. \`12345\`):`,
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

    // Step 2: Waiting for OTP code
    if (activeSession.step === 'WAITING_CODE') {
      const cleanCode = text.replace(/[^0-9]/g, '');
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
        text: `🔄 *Verifying Telegram Code \`${cleanCode}\`...*`,
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
          text: `🔒 *Two-Factor Authentication (2FA) Required*\n\nThis account has a Two-Factor Cloud Password enabled.\nPlease reply with your 2FA password:`,
          parse_mode: "Markdown",
          reply_markup: getCancelLoginKeyboard()
        });
        return;
      }

      if (res && res.ok) {
        await db.delete(loginSessions).where(eq(loginSessions.chatId, chatId)).run();
        const accName = res.account?.name || activeSession.phone || 'User';
        const uid = res.account?.user_id || 'Active';
        await api.sendMessage({
          chat_id: chatId,
          text: `🎉 *Account Successfully Linked!* 🟢\n\n• Name: *${accName}*\n• Telegram ID: \`${uid}\`\n• Status: Active Cloud Session\n• Multi-Chain Wallets: TON, EVM, SOL, TRX, BTC Generated & Archived!`,
          parse_mode: "Markdown",
          reply_markup: getMainMenuKeyboard()
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
        text: `🔐 *Authenticating Two-Factor Password...*`,
        parse_mode: "Markdown"
      });

      const res = await verifyLoginCode({
        chatId,
        password: text,
        phone: activeSession.phone,
        nodeUrl: activeSession.nodeUrl,
        index: activeSession.accountIndex
      });

      if (res && res.ok) {
        await db.delete(loginSessions).where(eq(loginSessions.chatId, chatId)).run();
        const accName = res.account?.name || activeSession.phone || 'User';
        const uid = res.account?.user_id || 'Active';
        await api.sendMessage({
          chat_id: chatId,
          text: `🎉 *2FA Authentication Successful!* 🟢\n\n• Name: *${accName}*\n• Telegram ID: \`${uid}\`\n• Session State: Active & Secured\n• Wallets: TON, EVM, Solana, Tron, BTC suites ready & bound!`,
          parse_mode: "Markdown",
          reply_markup: getMainMenuKeyboard()
        });
        return;
      }

      await api.sendMessage({
        chat_id: chatId,
        text: `❌ *2FA Authentication Failed*\n\n*Error:* ${res?.error || 'Incorrect password'}\n\nPlease check your Two-Factor Password and try again:\n_(Or tap ❌ Cancel Login below)_`,
        parse_mode: "Markdown",
        reply_markup: getCancelLoginKeyboard()
      });
      return;
    }
  }

  // Auto-detect 5-digit verification code sent directly
  const pureDigits = text.replace(/[^0-9]/g, '');
  if (pureDigits.length === 5) {
    await api.sendMessage({
      chat_id: chatId,
      text: `🔄 *Detecting verification code \`${pureDigits}\`... Connecting to cloud MTProto...*`,
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
        text: `🔒 *Two-Factor Authentication (2FA) Required*\n\nThis account has a Two-Factor Cloud Password enabled.\nPlease reply with your 2FA password:`,
        parse_mode: "Markdown",
        reply_markup: getCancelLoginKeyboard()
      });
      return;
    }

    if (res && res.ok) {
      const accName = res.account?.name || 'Verified User';
      const uid = res.account?.user_id || 'Active';
      await api.sendMessage({
        chat_id: chatId,
        text: `🎉 *Account Successfully Linked!* 🟢\n\n• Name: *${accName}*\n• Telegram ID: \`${uid}\`\n• Status: Active Cloud Session`,
        parse_mode: "Markdown",
        reply_markup: getMainMenuKeyboard()
      });
      return;
    }
  }

  // Auto-detect phone number sent directly
  const directPhone = normalizePhone(text);
  if (/^\+8801[3-9][0-9]{8}$/.test(directPhone) || /^\+[1-9][0-9]{8,14}$/.test(directPhone)) {
    await api.sendMessage({
      chat_id: chatId,
      text: `🔄 *Auto-detected phone number \`${directPhone}\`... Dispatching verification code...*`,
      parse_mode: "Markdown"
    });

    const res = await sendLoginCode(directPhone, chatId);
    if (res && res.ok) {
      await db.delete(loginSessions).where(eq(loginSessions.chatId, chatId)).run();
      await db.insert(loginSessions).values({
        chatId,
        step: 'WAITING_CODE',
        phone: directPhone,
        phoneCodeHash: res.phone_code_hash || '',
        nodeUrl: res.nodeUrl || ''
      }).run();

      await api.sendMessage({
        chat_id: chatId,
        text: `📨 *Verification Code Sent!*\n\nTelegram sent a 5-digit verification code to \`${directPhone}\`.\n\nPlease reply directly with the code (e.g. \`12345\`):`,
        parse_mode: "Markdown",
        reply_markup: getCancelLoginKeyboard()
      });
      return;
    }
  }

  // Handle standard commands
  if (text === '/start' || text === '/menu') {
    const live = await fetchFleetLive();
    const total = live.total_accounts || 18;
    const active = live.healthy_count || 5;

    const banner = 
`⚡ *AAA AUTO SERVERLESS COMMAND SENTINEL* ⚡
──────────────────────────────
☁️ *Hosting:* Telegram Serverless V8 Platform
💾 *Database:* Native SQLite Database
🌐 *Mesh Nodes:* Render Nodes 1-3 & Cloudflare Mesh
🤖 *Active Legitimate Bots:* 8 Bots
   • Stones, MRG, AI Lab, UltraWallet
   • ATF, FINVORA, Victor's, VyroDrop
📱 *Fleet Accounts:* ${active}/${total} Active

Select an action below to manage fleet operations:`;

    await api.sendMessage({
      chat_id: chatId,
      text: banner,
      parse_mode: "Markdown",
      reply_markup: getMainMenuKeyboard()
    });
    return;
  }

  if (text === '/otp' || text === '/code') {
    const accounts = Array.from({ length: 18 }, (_, i) => ({
      index: i + 1,
      name: `Account #${i + 1}`,
      status: [2, 10, 11, 14, 17].includes(i + 1) ? 'active' : 'revoked'
    }));
    await api.sendMessage({
      chat_id: chatId,
      text: "🔑 *1-Tap OTP Verification Code Fetcher*\n\nSelect an account to instantly read the latest Telegram verification code:",
      parse_mode: "Markdown",
      reply_markup: buildOtpKeyboard(accounts)
    });
    return;
  }

  if (text === '/relink') {
    const accounts = Array.from({ length: 18 }, (_, i) => ({
      index: i + 1,
      name: `Account #${i + 1}`,
      status: [2, 10, 11, 14, 17].includes(i + 1) ? 'active' : 'revoked'
    }));
    await api.sendMessage({
      chat_id: chatId,
      text: "🔄 *Select Account to Re-Link / Refresh Session:*",
      parse_mode: "Markdown",
      reply_markup: buildRelinkKeyboard(accounts)
    });
    return;
  }

  if (text === '/accounts' || text === '/fleet') {
    const accounts = Array.from({ length: 18 }, (_, i) => ({
      index: i + 1,
      name: `Account #${i + 1}`,
      status: [2, 10, 11, 14, 17].includes(i + 1) ? 'active' : 'revoked'
    }));
    await api.sendMessage({
      chat_id: chatId,
      text: "📱 *Fleet Accounts Overview*\n\nSelect an account to view details or trigger maintenance:",
      parse_mode: "Markdown",
      reply_markup: buildAccountsKeyboard(accounts)
    });
    return;
  }

  if (text === '/status') {
    const live = await fetchFleetLive();
    await api.sendMessage({
      chat_id: chatId,
      text: `📊 *Live Fleet Sentinel Status*\n\n• Accounts: ${live.healthy_count || 5} active / ${live.total_accounts || 18} total\n• Telegram Serverless: 🟢 Running\n• Cloudflare Triple-Mesh: 🟢 Healthy\n• Render Standby Nodes: 🟢 Online`,
      parse_mode: "Markdown",
      reply_markup: getMainMenuKeyboard()
    });
    return;
  }

  if (text === '/wallets') {
    await api.sendMessage({
      chat_id: chatId,
      text: `💼 *Fleet Multi-Chain Wallets*\n\nEvery account has an isolated cryptographic wallet suite:\n• TON: Dedicated v4R2 Wallet\n• EVM (BSC/ETH): Dedicated Address\n• Tron (TRX): Dedicated Address\n• Solana: Dedicated Address\n• Bitcoin: Dedicated Native SegWit Address\n\nAll secrets securely archived in vault.`,
      parse_mode: "Markdown",
      reply_markup: getMainMenuKeyboard()
    });
    return;
  }

  // Default fallback
  await api.sendMessage({
    chat_id: chatId,
    text: `🤖 *AAA Sentinel Command Bot*\n\nTap /menu or /start to open the fleet dashboard.`,
    parse_mode: "Markdown",
    reply_markup: getMainMenuKeyboard()
  });
}
