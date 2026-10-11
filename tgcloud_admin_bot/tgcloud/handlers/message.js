import { api, db } from 'sdk';
import { eq } from 'sdk/db';
import { loginSessions } from '../schema.js';
import { CONFIG } from '../lib/config.js';
import { sendLoginCode, verifyLoginCode, cancelLogin, fetchFleetLive, requestBackend } from '../lib/backend.js';
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
    await cancelLogin(chatId).catch(() => {});
    await db.delete(loginSessions).where(eq(loginSessions.chatId, chatId)).run().catch(() => {});

    // Wipe persistent ReplyKeyboardMarkup button from the user's Telegram client
    await api.sendMessage({
      chat_id: chatId,
      text: "❌ *Login Session Cancelled.*",
      parse_mode: "Markdown",
      reply_markup: { remove_keyboard: true }
    });

    const live = await fetchFleetLive();
    await api.sendMessage({
      chat_id: chatId,
      text: buildDashboardBanner(live),
      parse_mode: "Markdown",
      reply_markup: getMainMenuKeyboard()
    });
    return;
  }

  // 3. Preemptive Command Router (Any command starting with '/' cancels active login state)
  const isCommand = rawText.startsWith('/');
  if (isCommand) {
    await cancelLogin(chatId).catch(() => {});
    await db.delete(loginSessions).where(eq(loginSessions.chatId, chatId)).run().catch(() => {});

    const cmd = rawText.split(' ')[0].toLowerCase();

    if (cmd === '/start' || cmd === '/menu') {
      // First wipe any stuck ReplyKeyboardMarkup
      await api.sendMessage({
        chat_id: chatId,
        text: "⚡ *AAA AUTO Sentinel Ready*",
        parse_mode: "Markdown",
        reply_markup: { remove_keyboard: true }
      });

      const live = await fetchFleetLive();
      await api.sendMessage({
        chat_id: chatId,
        text: buildDashboardBanner(live),
        parse_mode: "Markdown",
        reply_markup: getMainMenuKeyboard()
      });
      return;
    }

    if (cmd === '/otp' || cmd === '/code') {
      const live = await fetchFleetLive();
      await api.sendMessage({
        chat_id: chatId,
        text: "🔑 *1-Tap OTP Verification Code Fetcher*\n\nSelect an account to instantly read the latest Telegram verification code from cloud MTProto:",
        parse_mode: "Markdown",
        reply_markup: buildOtpKeyboard(live.accounts)
      });
      return;
    }

    if (cmd === '/relink') {
      const live = await fetchFleetLive();
      const revokedCount = live.revoked_count || 13;
      await api.sendMessage({
        chat_id: chatId,
        text: `🔄 *Re-link Fleet Accounts*\n\nFound *${revokedCount}* accounts requiring session renewal.\nSelect an account below to trigger instant SMS/Telegram login code:`,
        parse_mode: "Markdown",
        reply_markup: buildRelinkKeyboard(live.accounts)
      });
      return;
    }

    if (cmd === '/accounts' || cmd === '/fleet') {
      const live = await fetchFleetLive();
      await api.sendMessage({
        chat_id: chatId,
        text: `📱 *Fleet Accounts Overview (${live.healthy_count || 5}/${live.total_accounts || 18} Active)*\n\n🟢 = Active MTProto Session\n🔴 = Session Revoked / Needs Re-link\n👑 = Master Host Account\n\nSelect an account to view details:`,
        parse_mode: "Markdown",
        reply_markup: buildAccountsKeyboard(live.accounts)
      });
      return;
    }

    if (cmd === '/status' || cmd === '/mesh') {
      const live = await fetchFleetLive();
      await api.sendMessage({
        chat_id: chatId,
        text: buildMeshStatusBanner(live),
        parse_mode: "Markdown",
        reply_markup: getMainMenuKeyboard()
      });
      return;
    }

    if (cmd === '/wallets') {
      await api.sendMessage({
        chat_id: chatId,
        text: buildWalletsBanner(),
        parse_mode: "Markdown",
        reply_markup: getMainMenuKeyboard()
      });
      return;
    }

    if (cmd === '/farm') {
      await api.sendMessage({
        chat_id: chatId,
        text: "⚡ *Triggering Farming Cycle Across All 8 Legitimate Bots...*\n\n• Dispatched to Render Standby cluster...",
        parse_mode: "Markdown"
      });
      await requestBackend('/api/farm/cloud-all', 'POST', {}).catch(() => {});
      await api.sendMessage({
        chat_id: chatId,
        text: "⚡ *Mining Cycle Dispatched to Cloud Cluster!* 🟢\n\nActive bots farmed: Stones, MRG, AI Lab, UltraWallet, ATF, FINVORA, Victor's, VyroDrop.",
        parse_mode: "Markdown",
        reply_markup: getMainMenuKeyboard()
      });
      return;
    }

    // Default unknown command
    await api.sendMessage({
      chat_id: chatId,
      text: `🤖 *AAA AUTO Sentinel*\n\nCommand \`${cmd}\` not recognized.\nTap /menu or /start to open the fleet dashboard.`,
      parse_mode: "Markdown",
      reply_markup: getMainMenuKeyboard()
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
          text: `🔒 *Two-Factor Authentication (2FA) Required*\n\nThis account has a Two-Factor Cloud Password enabled.\nPlease reply directly with your 2FA password:`,
          parse_mode: "Markdown",
          reply_markup: getCancelLoginKeyboard()
        });
        return;
      }

      if (res && res.ok) {
        await db.delete(loginSessions).where(eq(loginSessions.chatId, chatId)).run();
        const accName = res.name || res.account?.name || activeSession.phone || 'User';
        const uid = res.user_id || res.account?.user_id || 'Active';
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
        password: rawText,
        phone: activeSession.phone,
        nodeUrl: activeSession.nodeUrl,
        index: activeSession.accountIndex
      });

      if (res && res.ok) {
        await db.delete(loginSessions).where(eq(loginSessions.chatId, chatId)).run();
        const accName = res.name || res.account?.name || activeSession.phone || 'User';
        const uid = res.user_id || res.account?.user_id || 'Active';
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
        text: `🔒 *Two-Factor Authentication (2FA) Required*\n\nThis account has a Two-Factor Cloud Password enabled.\nPlease reply directly with your 2FA password:`,
        parse_mode: "Markdown",
        reply_markup: getCancelLoginKeyboard()
      });
      return;
    }

    if (res && res.ok) {
      const accName = res.name || res.account?.name || 'Verified User';
      const uid = res.user_id || res.account?.user_id || 'Active';
      await api.sendMessage({
        chat_id: chatId,
        text: `🎉 *Account Successfully Linked!* 🟢\n\n• Name: *${accName}*\n• Telegram ID: \`${uid}\`\n• Status: Active Cloud Session`,
        parse_mode: "Markdown",
        reply_markup: getMainMenuKeyboard()
      });
      return;
    }
  }

  // 6. Auto-detect phone number sent directly
  const directPhone = normalizePhone(rawText);
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

  // 7. Default Fallback
  await api.sendMessage({
    chat_id: chatId,
    text: `🤖 *AAA AUTO Sentinel Command Bot*\n\nTap /menu or /start to open the fleet dashboard.`,
    parse_mode: "Markdown",
    reply_markup: getMainMenuKeyboard()
  });
}
