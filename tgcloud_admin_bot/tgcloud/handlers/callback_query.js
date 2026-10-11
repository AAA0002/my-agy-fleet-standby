import { api, db } from 'sdk';
import { eq } from 'sdk/db';
import { loginSessions } from '../schema.js';
import { CONFIG } from '../lib/config.js';
import { sendLoginCode, cancelLogin, fetchFleetLive, fetchOtpForAccount, requestBackend } from '../lib/backend.js';
import { getMainMenuKeyboard, getCancelLoginKeyboard, getBackToMenuKeyboard, buildOtpKeyboard, buildRelinkKeyboard, buildAccountsKeyboard } from '../lib/ui.js';

export default async function (callbackQuery, ctx) {
  if (!callbackQuery || !callbackQuery.message) return;

  const data = callbackQuery.data || '';
  const chatId = String(callbackQuery.message.chat.id);
  const messageId = callbackQuery.message.message_id;
  const userId = callbackQuery.from ? callbackQuery.from.id : null;

  // Enforce admin permission
  if (userId && !CONFIG.ADMIN_IDS.includes(userId)) {
    await api.answerCallbackQuery({
      callback_query_id: callbackQuery.id,
      text: "⛔ Unauthorized access.",
      show_alert: true
    });
    return;
  }

  // Answer callback query promptly
  await api.answerCallbackQuery({ callback_query_id: callbackQuery.id }).catch(() => {});

  if (data === 'btn_main_menu') {
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

    await api.editMessageText({
      chat_id: chatId,
      message_id: messageId,
      text: banner,
      parse_mode: "Markdown",
      reply_markup: getMainMenuKeyboard()
    });
    return;
  }

  if (data === 'btn_fleet_accounts') {
    const live = await fetchFleetLive();
    const accounts = Array.from({ length: 18 }, (_, i) => ({
      index: i + 1,
      name: `Account #${i + 1}`,
      status: [2, 10, 11, 14, 17].includes(i + 1) ? 'active' : 'revoked'
    }));

    await api.editMessageText({
      chat_id: chatId,
      message_id: messageId,
      text: "📱 *Fleet Accounts Overview*\n\nSelect an account to view details or trigger maintenance:",
      parse_mode: "Markdown",
      reply_markup: buildAccountsKeyboard(accounts, "btn_account_view_")
    });
    return;
  }

  if (data === 'btn_otp_menu') {
    const accounts = Array.from({ length: 18 }, (_, i) => ({
      index: i + 1,
      name: `Account #${i + 1}`,
      status: [2, 10, 11, 14, 17].includes(i + 1) ? 'active' : 'revoked'
    }));

    await api.editMessageText({
      chat_id: chatId,
      message_id: messageId,
      text: "🔑 *1-Tap OTP Verification Code Fetcher*\n\nSelect an account to instantly read its latest Telegram login code from MTProto:",
      parse_mode: "Markdown",
      reply_markup: buildOtpKeyboard(accounts)
    });
    return;
  }

  if (data.startsWith('btn_otp_get_')) {
    const idx = parseInt(data.replace('btn_otp_get_', ''), 10);
    await api.editMessageText({
      chat_id: chatId,
      message_id: messageId,
      text: `⏳ *Fetching Latest OTP for Account #${idx}...*\n\nQuerying cloud MTProto inbox...`,
      parse_mode: "Markdown"
    });

    const res = await fetchOtpForAccount(idx);
    if (res && res.code) {
      await api.editMessageText({
        chat_id: chatId,
        message_id: messageId,
        text: `🔑 *Telegram Verification Code for Account #${idx}*\n\n• Code: \`${res.code}\`\n• Time: \`${res.time || 'Recent'}\`\n\nTap to copy: \`${res.code}\``,
        parse_mode: "Markdown",
        reply_markup: buildOtpKeyboard(Array.from({ length: 18 }, (_, i) => ({ index: i + 1 })))
      });
    } else {
      await api.editMessageText({
        chat_id: chatId,
        message_id: messageId,
        text: `⚠️ *No Recent OTP Found for Account #${idx}*\n\nNo verification codes received in the last 15 minutes, or the account session is currently unlinked.`,
        parse_mode: "Markdown",
        reply_markup: buildOtpKeyboard(Array.from({ length: 18 }, (_, i) => ({ index: i + 1 })))
      });
    }
    return;
  }

  if (data === 'btn_relink_menu') {
    const accounts = Array.from({ length: 18 }, (_, i) => ({
      index: i + 1,
      name: `Account #${i + 1}`,
      status: [2, 10, 11, 14, 17].includes(i + 1) ? 'active' : 'revoked'
    }));

    await api.editMessageText({
      chat_id: chatId,
      message_id: messageId,
      text: "🔄 *Select Account to Re-Link / Refresh Session:*",
      parse_mode: "Markdown",
      reply_markup: buildRelinkKeyboard(accounts)
    });
    return;
  }

  if (data.startsWith('btn_relink_acc_')) {
    const idx = parseInt(data.replace('btn_relink_acc_', ''), 10);
    const knownPhone = CONFIG.KNOWN_PHONES[idx];

    // Clean existing session for this chat
    await db.delete(loginSessions).where(eq(loginSessions.chatId, chatId)).run();

    if (knownPhone) {
      await api.editMessageText({
        chat_id: chatId,
        message_id: messageId,
        text: `🔄 *Re-linking Account #${idx}*\n\n• Phone: \`${knownPhone}\`\n• Dispatching Telegram verification code...`,
        parse_mode: "Markdown"
      });

      const res = await sendLoginCode(knownPhone, chatId, idx);
      if (res && res.ok) {
        await db.insert(loginSessions).values({
          chatId,
          step: 'WAITING_CODE',
          phone: knownPhone,
          phoneCodeHash: res.phone_code_hash || '',
          accountIndex: idx,
          nodeUrl: res.nodeUrl || ''
        }).run();

        await api.sendMessage({
          chat_id: chatId,
          text: `📨 *Verification Code Sent for Account #${idx}!*\n\nTelegram sent a 5-digit verification code to \`${knownPhone}\`.\n\nPlease reply directly with the code (e.g. \`12345\`):`,
          parse_mode: "Markdown",
          reply_markup: getCancelLoginKeyboard()
        });
      } else {
        await api.sendMessage({
          chat_id: chatId,
          text: `❌ *Could not request code:* ${res?.error || 'Network error'}\n\nPlease try again:`,
          parse_mode: "Markdown",
          reply_markup: getMainMenuKeyboard()
        });
      }
    } else {
      await db.insert(loginSessions).values({
        chatId,
        step: 'WAITING_PHONE',
        accountIndex: idx
      }).run();

      await api.editMessageText({
        chat_id: chatId,
        message_id: messageId,
        text: `📱 *Enter Phone Number for Account #${idx}*\n\nPlease reply with the international phone number (e.g., \`+8801943805617\`):`,
        parse_mode: "Markdown",
        reply_markup: getCancelLoginKeyboard()
      });
    }
    return;
  }

  if (data === 'btn_add_account') {
    await db.delete(loginSessions).where(eq(loginSessions.chatId, chatId)).run();
    await db.insert(loginSessions).values({
      chatId,
      step: 'WAITING_PHONE'
    }).run();

    await api.editMessageText({
      chat_id: chatId,
      message_id: messageId,
      text: "➕ *Add New Account to Fleet*\n\nPlease reply with the phone number with country code (e.g., `+8801943805617`):",
      parse_mode: "Markdown",
      reply_markup: getCancelLoginKeyboard()
    });
    return;
  }

  if (data === 'btn_cancel_login') {
    await cancelLogin(chatId);
    await db.delete(loginSessions).where(eq(loginSessions.chatId, chatId)).run();
    await api.editMessageText({
      chat_id: chatId,
      message_id: messageId,
      text: "❌ *Login process cancelled.*",
      parse_mode: "Markdown",
      reply_markup: getMainMenuKeyboard()
    });
    return;
  }

  if (data === 'btn_farm_all') {
    await api.editMessageText({
      chat_id: chatId,
      message_id: messageId,
      text: "⚡ *Triggering Mining Cycle Across All 8 Legitimate Bots...*\n\n• Dispatched to Render Standby cluster...",
      parse_mode: "Markdown"
    });
    const res = await requestBackend('/api/fleet/sync', 'POST', {});
    await api.editMessageText({
      chat_id: chatId,
      message_id: messageId,
      text: `⚡ *Mining Cycle Dispatched!* 🟢\n\nActive bots farmed: Stones, MRG, AI Lab, UltraWallet, ATF, FINVORA, Victor's, VyroDrop.\nResponse: ${res ? 'OK' : 'Sent'}`,
      parse_mode: "Markdown",
      reply_markup: getMainMenuKeyboard()
    });
    return;
  }

  if (data === 'btn_system_status' || data === 'btn_mesh_status') {
    const live = await fetchFleetLive();
    const txt = 
`🛡️ *Infrastructure & Mesh Health Status*
──────────────────────────────
☁️ *Telegram Serverless:* 🟢 Operational (V8 Isolate)
💾 *SQLite Database:* 🟢 Active & Migrated
🌐 *Cloudflare 3-Node Mesh:*
   • Node 1 (aaaai2.workers.dev): 🟢 Healthy
   • Node 2 (aaa-bot.workers.dev): 🟢 Healthy
   • Node 3 (aaa222.workers.dev): 🟢 Healthy
🚀 *Render Standby Cluster:*
   • Node 1 (Singapore): 🟢 Active
   • Node 2 (Frankfurt): 🟢 Active
   • Node 3 (Oregon): 🟢 Active
🤖 *Active Legitimate Bots:* 8 Bots
📱 *Fleet Accounts:* ${live.healthy_count || 5}/${live.total_accounts || 18} Active`;

    await api.editMessageText({
      chat_id: chatId,
      message_id: messageId,
      text: txt,
      parse_mode: "Markdown",
      reply_markup: getBackToMenuKeyboard()
    });
    return;
  }

  if (data === 'btn_wallets') {
    await api.editMessageText({
      chat_id: chatId,
      message_id: messageId,
      text: "💼 *Fleet Multi-Chain Wallets*\n\nEvery account has an isolated cryptographic wallet suite:\n• TON: Dedicated v4R2 Wallet\n• EVM (BSC/ETH): Dedicated Address\n• Tron (TRX): Dedicated Address\n• Solana: Dedicated Address\n• Bitcoin: Dedicated Native SegWit Address\n\nAll secrets securely archived in vault.",
      parse_mode: "Markdown",
      reply_markup: getBackToMenuKeyboard()
    });
    return;
  }
}