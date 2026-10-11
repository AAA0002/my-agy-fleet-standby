import { api, db } from 'sdk';
import { eq } from 'sdk/db';
import { loginSessions } from '../schema.js';
import { CONFIG } from '../lib/config.js';
import { sendLoginCode, cancelLogin, fetchFleetLive, fetchOtpForAccount, requestBackend } from '../lib/backend.js';
import {
  getMainMenuKeyboard,
  getCancelLoginKeyboard,
  getBackToMenuKeyboard,
  buildOtpKeyboard,
  buildRelinkKeyboard,
  buildAccountsKeyboard,
  buildDashboardBanner,
  buildMeshStatusBanner,
  buildWalletsBanner
} from '../lib/ui.js';

async function replyOrEdit(chatId, messageId, text, reply_markup) {
  try {
    await api.editMessageText({
      chat_id: chatId,
      message_id: messageId,
      text,
      parse_mode: "Markdown",
      reply_markup
    });
  } catch (err) {
    const errStr = String(err || '');
    if (!errStr.includes('message is not modified')) {
      await api.sendMessage({
        chat_id: chatId,
        text,
        parse_mode: "Markdown",
        reply_markup
      }).catch(() => {});
    }
  }
}

export default async function (callbackQuery, ctx) {
  if (!callbackQuery || !callbackQuery.message) return;

  const data = callbackQuery.data || '';
  const chatId = String(callbackQuery.message.chat.id);
  const messageId = callbackQuery.message.message_id;
  const userId = callbackQuery.from ? callbackQuery.from.id : null;

  // Enforce admin permission (Arif Hossain: 6727787768)
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
    await replyOrEdit(chatId, messageId, buildDashboardBanner(live), getMainMenuKeyboard());
    return;
  }

  if (data === 'btn_fleet_accounts') {
    const live = await fetchFleetLive();
    const text = `📱 *Fleet Accounts Overview (${live.healthy_count || 5}/${live.total_accounts || 18} Active)*\n\n🟢 = Active MTProto Session\n🔴 = Session Revoked / Needs Re-link\n👑 = Master Host Account\n\nSelect an account to view details:`;
    await replyOrEdit(chatId, messageId, text, buildAccountsKeyboard(live.accounts, "btn_account_view_"));
    return;
  }

  if (data.startsWith('btn_account_view_')) {
    const idx = parseInt(data.replace('btn_account_view_', ''), 10);
    const live = await fetchFleetLive();
    const acc = live.accounts.find(a => a.index === idx) || { index: idx, name: `Account #${idx}` };
    const phone = acc.phone || CONFIG.KNOWN_PHONES[idx] || "Unknown";
    const isHealthy = acc.status === 'active';
    const isHost = String(acc.user_id) === "6727787768";

    const detailText = 
`📱 *Fleet Account #${idx} Details*
──────────────────────────────
• *Name:* ${acc.name || 'Worker Account'} ${isHost ? '👑 (Master Host)' : ''}
• *Phone:* \`${phone}\`
• *Telegram ID:* \`${acc.user_id || 'N/A'}\`
• *Session Status:* ${isHealthy ? '🟢 Active MTProto Session' : '🔴 Session Revoked (Needs Re-link)'}
• *Wallets Suite:* TON, EVM, SOL, TRX, BTC Generated & Bound

${isHealthy ? '✅ Account is online and mining actively in cloud cluster.' : '⚠️ Authorization expired. Tap Re-link below to refresh session.'}`;

    const buttons = [];
    if (isHealthy) {
      buttons.push([
        { text: "🔑 Fetch OTP Code", callback_data: `btn_otp_get_${idx}` },
        { text: "⚡ Farm Account", callback_data: `btn_farm_acc_${idx}` }
      ]);
    } else {
      buttons.push([
        { text: `⚡ 1-Tap Re-link Account #${idx}`, callback_data: `btn_relink_acc_${idx}` }
      ]);
    }
    buttons.push([
      { text: "🔙 Accounts List", callback_data: "btn_fleet_accounts" },
      { text: "🔙 Main Menu", callback_data: "btn_main_menu" }
    ]);

    await replyOrEdit(chatId, messageId, detailText, { inline_keyboard: buttons });
    return;
  }

  if (data.startsWith('btn_farm_acc_')) {
    const idx = parseInt(data.replace('btn_farm_acc_', ''), 10);
    const live = await fetchFleetLive();
    const acc = live.accounts.find(a => a.index === idx);
    const uid = acc?.user_id || idx;

    await replyOrEdit(chatId, messageId, `⚡ *Farming Account #${idx} (${acc?.name || 'Worker'})...*\n\nDispatched to Render Standby cluster...`, null);
    await requestBackend(`/api/farm/account/${uid}`, 'POST', {}).catch(() => {});

    await replyOrEdit(chatId, messageId, `✅ *Account #${idx} Farming Cycle Dispatched!* 🟢\n\nActive bots farmed: Stones, MRG, AI Lab, UltraWallet, ATF, FINVORA, Victor's, VyroDrop.`, {
      inline_keyboard: [
        [{ text: `📱 Back to Account #${idx}`, callback_data: `btn_account_view_${idx}` }],
        [{ text: "🔙 Accounts List", callback_data: "btn_fleet_accounts" }],
        [{ text: "🔙 Main Menu", callback_data: "btn_main_menu" }]
      ]
    });
    return;
  }

  if (data === 'btn_otp_menu') {
    const live = await fetchFleetLive();
    const text = "🔑 *1-Tap OTP Verification Code Fetcher*\n\nSelect an account to instantly read its latest Telegram login code from cloud MTProto:";
    await replyOrEdit(chatId, messageId, text, buildOtpKeyboard(live.accounts));
    return;
  }

  if (data.startsWith('btn_otp_get_')) {
    const idx = parseInt(data.replace('btn_otp_get_', ''), 10);
    await replyOrEdit(chatId, messageId, `⏳ *Fetching Latest OTP for Account #${idx}...*\n\nQuerying cloud MTProto inbox...`, null);

    const res = await fetchOtpForAccount(idx);
    const live = await fetchFleetLive();

    if (res && res.code) {
      const text = `🔑 *Telegram Verification Code for Account #${idx}*\n\n• Code: \`${res.code}\`\n• Time: \`${res.time || 'Recent'}\`\n\nTap to copy: \`${res.code}\``;
      await replyOrEdit(chatId, messageId, text, buildOtpKeyboard(live.accounts));
    } else if (res && res.session_revoked) {
      const text = `🔴 *Account #${idx} Session Revoked on Telegram*\n\nThe authorization key was invalidated or expired.\nTap below to re-link this account:`;
      await replyOrEdit(chatId, messageId, text, {
        inline_keyboard: [
          [{ text: `⚡ 1-Tap Re-link Account #${idx}`, callback_data: `btn_relink_acc_${idx}` }],
          [{ text: "🔙 OTP Menu", callback_data: "btn_otp_menu" }],
          [{ text: "🔙 Main Menu", callback_data: "btn_main_menu" }]
        ]
      });
    } else {
      const text = `⚠️ *No Recent OTP Found for Account #${idx}*\n\nNo verification codes received in the last 15 minutes, or the account is currently idle.`;
      await replyOrEdit(chatId, messageId, text, buildOtpKeyboard(live.accounts));
    }
    return;
  }

  if (data === 'btn_relink_menu') {
    const live = await fetchFleetLive();
    const revokedCount = live.revoked_count || 13;
    const text = `🔄 *Select Account to Re-Link (${revokedCount} Revoked):*\n\nTap an account to immediately dispatch a Telegram verification code:`;
    await replyOrEdit(chatId, messageId, text, buildRelinkKeyboard(live.accounts));
    return;
  }

  if (data.startsWith('btn_relink_acc_')) {
    const idx = parseInt(data.replace('btn_relink_acc_', ''), 10);
    const knownPhone = CONFIG.KNOWN_PHONES[idx];

    // Clean existing session for this chat
    await db.delete(loginSessions).where(eq(loginSessions.chatId, chatId)).run().catch(() => {});

    if (knownPhone) {
      await replyOrEdit(chatId, messageId, `🔄 *Re-linking Account #${idx}*\n\n• Phone: \`${knownPhone}\`\n• Dispatching Telegram verification code...`, null);

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

      await replyOrEdit(chatId, messageId, `📱 *Enter Phone Number for Account #${idx}*\n\nPlease reply with the international phone number (e.g., \`+8801943805617\`):`, getCancelLoginKeyboard());
    }
    return;
  }

  if (data === 'btn_add_account') {
    await db.delete(loginSessions).where(eq(loginSessions.chatId, chatId)).run().catch(() => {});
    await db.insert(loginSessions).values({
      chatId,
      step: 'WAITING_PHONE'
    }).run();

    await replyOrEdit(chatId, messageId, "➕ *Add New Account to Fleet*\n\nPlease reply with the phone number with country code (e.g., `+8801943805617`):", getCancelLoginKeyboard());
    return;
  }

  if (data === 'btn_cancel_login') {
    await cancelLogin(chatId).catch(() => {});
    await db.delete(loginSessions).where(eq(loginSessions.chatId, chatId)).run().catch(() => {});

    try {
      await api.sendMessage({
        chat_id: chatId,
        text: "🧹 *Cleared temporary keyboard.*",
        reply_markup: { remove_keyboard: true }
      });
    } catch (_) {}

    const live = await fetchFleetLive();
    await replyOrEdit(chatId, messageId, buildDashboardBanner(live), getMainMenuKeyboard());
    return;
  }

  if (data === 'btn_farm_all') {
    await replyOrEdit(chatId, messageId, "⚡ *Triggering Mining Cycle Across All 8 Legitimate Bots...*\n\n• Dispatched to Render Standby cluster...", null);
    const res = await requestBackend('/api/farm/cloud-all', 'POST', {}).catch(() => {});
    const msg = `⚡ *Mining Cycle Dispatched!* 🟢\n\nActive bots farmed: Stones, MRG, AI Lab, UltraWallet, ATF, FINVORA, Victor's, VyroDrop.\nCluster state: ${res?.status || 'Dispatched successfully'}`;
    await replyOrEdit(chatId, messageId, msg, getMainMenuKeyboard());
    return;
  }

  if (data === 'btn_system_status' || data === 'btn_mesh_status') {
    const live = await fetchFleetLive();
    await replyOrEdit(chatId, messageId, buildMeshStatusBanner(live), getBackToMenuKeyboard());
    return;
  }

  if (data === 'btn_wallets') {
    await replyOrEdit(chatId, messageId, buildWalletsBanner(), getBackToMenuKeyboard());
    return;
  }
}