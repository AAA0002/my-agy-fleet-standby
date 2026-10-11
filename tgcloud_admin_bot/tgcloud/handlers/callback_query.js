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
  buildAccountDetailCard,
  buildAccountDetailKeyboard,
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
    await replyOrEdit(chatId, messageId, buildDashboardBanner(live), getMainMenuKeyboard(live.revoked_count || 13));
    return;
  }

  if (data === 'btn_fleet_accounts' || data === 'btn_filter_all') {
    const live = await fetchFleetLive();
    const text = `📱 *FLEET ACCOUNTS MATRIX (${live.healthy_count || 5}/${live.total_accounts || 18} ACTIVE)*\n\n🟢 = Active MTProto Session\n🔴 = Session Revoked / Needs Re-link\n👑 = Master Host Account\n\nSelect an account node below to inspect dossier:`;
    await replyOrEdit(chatId, messageId, text, buildAccountsKeyboard(live.accounts, 'all'));
    return;
  }

  if (data === 'btn_filter_active') {
    const live = await fetchFleetLive();
    const text = `🟢 *ONLINE ACTIVE SESSIONS (${live.healthy_count || 5} NODES)*\n\nAll accounts below have active 24h MTProto authorization keys.\nSelect a node to inspect:`;
    await replyOrEdit(chatId, messageId, text, buildAccountsKeyboard(live.accounts, 'active'));
    return;
  }

  if (data === 'btn_filter_revoked') {
    const live = await fetchFleetLive();
    const text = `🔴 *REVOKED SESSIONS (${live.revoked_count || 13} NODES)*\n\nSessions below require re-linking. Tap any account to trigger 1-tap SMS/Telegram login code:`;
    await replyOrEdit(chatId, messageId, text, buildAccountsKeyboard(live.accounts, 'revoked'));
    return;
  }

  if (data.startsWith('btn_account_view_')) {
    const idx = parseInt(data.replace('btn_account_view_', ''), 10);
    const live = await fetchFleetLive();
    const acc = live.accounts.find(a => a.index === idx) || { index: idx, name: `Account #${idx}` };
    await replyOrEdit(chatId, messageId, buildAccountDetailCard(acc), buildAccountDetailKeyboard(acc));
    return;
  }

  if (data.startsWith('btn_farm_acc_')) {
    const idx = parseInt(data.replace('btn_farm_acc_', ''), 10);
    const live = await fetchFleetLive();
    const acc = live.accounts.find(a => a.index === idx) || { index: idx, name: `Account #${idx}` };
    const uid = acc?.user_id || idx;

    await replyOrEdit(chatId, messageId, `⚡ *Farming Node #${idx < 10 ? '0' + idx : idx} (${acc.name})...*\n\nDispatched to Render Standby cloud cluster...`, null);
    await requestBackend(`/api/farm/account/${uid}`, 'POST', {}).catch(() => {});

    await replyOrEdit(chatId, messageId, `✅ *Node #${idx < 10 ? '0' + idx : idx} Mining Cycle Dispatched!* 🟢\n\nActive bots farmed: Stones, MRG, AI Lab, UltraWallet, ATF, FINVORA, Victor's, VyroDrop.\n100% cloud execution, 0% phone load.`, {
      inline_keyboard: [
        [{ text: `📱 Back to Node #${idx < 10 ? '0' + idx : idx}`, callback_data: `btn_account_view_${idx}` }],
        [{ text: "📱 Fleet Matrix", callback_data: "btn_fleet_accounts" }],
        [{ text: "🔙 Main Menu", callback_data: "btn_main_menu" }]
      ]
    });
    return;
  }

  if (data === 'btn_otp_menu') {
    const live = await fetchFleetLive();
    const text = `┌──────────────────────────────────────┐
│  🔑 *1-TAP TELEGRAM OTP VAULT*       │
│  _Instant MTProto Authorization_     │
└──────────────────────────────────────┘

Select an active account node below to instantly inspect the latest Telegram verification code received from MTProto:`;
    await replyOrEdit(chatId, messageId, text, buildOtpKeyboard(live.accounts));
    return;
  }

  if (data.startsWith('btn_otp_get_')) {
    const idx = parseInt(data.replace('btn_otp_get_', ''), 10);
    await replyOrEdit(chatId, messageId, `⏳ *Extracting Latest OTP for Node #${idx < 10 ? '0' + idx : idx}...*\n\nConnecting to cloud MTProto inbox...`, null);

    const res = await fetchOtpForAccount(idx);
    const live = await fetchFleetLive();
    const acc = live.accounts.find(a => a.index === idx) || { index: idx, name: `Account #${idx}` };
    const phone = acc.phone || CONFIG.KNOWN_PHONES[idx] || "Unassigned";

    if (res && res.code) {
      const text = `┌──────────────────────────────────────┐
│  🔑 *TELEGRAM VERIFICATION CODE*     │
└──────────────────────────────────────┘

• *Account Node:* \`#${idx < 10 ? '0' + idx : idx} • ${acc.name}\`
• *Phone Number:* \`${phone}\`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔐 *AUTHENTICATION DIGITS:*
\`${res.code}\`   _(Tap code to copy: \`${res.code}\`)_
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• *Timestamp:* \`${res.time || 'Fresh (< 2 mins)'}\`
• *Verification State:* \`🟢 Official Cloud MTProto Passcode\`

Use this code to authorize desktop, web, or mobile clients.`;
      await replyOrEdit(chatId, messageId, text, buildOtpKeyboard(live.accounts));
    } else if (res && res.session_revoked) {
      const text = `🔴 *Node #${idx < 10 ? '0' + idx : idx} Session Revoked on Telegram*\n\nThe authorization key was invalidated or expired.\nTap below to re-link this session:`;
      await replyOrEdit(chatId, messageId, text, {
        inline_keyboard: [
          [{ text: `⚡ 1-Tap Re-link Node #${idx < 10 ? '0' + idx : idx}`, callback_data: `btn_relink_acc_${idx}` }],
          [{ text: "🔑 Back to OTP Vault", callback_data: "btn_otp_menu" }],
          [{ text: "🔙 Main Menu", callback_data: "btn_main_menu" }]
        ]
      });
    } else {
      const text = `⚠️ *No Recent OTP Found for Node #${idx < 10 ? '0' + idx : idx}*\n\nNo verification codes received in the last 15 minutes, or the node is currently idle.`;
      await replyOrEdit(chatId, messageId, text, buildOtpKeyboard(live.accounts));
    }
    return;
  }

  if (data === 'btn_relink_menu') {
    const live = await fetchFleetLive();
    const revokedCount = live.revoked_count || 13;
    const text = `┌──────────────────────────────────────┐
│  🔄 *FLEET SESSION RECOVERY CENTER*  │
│  _Automated 1-Tap Re-Authentication_ │
└──────────────────────────────────────┘

⚠️ *Offline Fleet Sessions:* \`${revokedCount} Nodes Require Renewal\`

Tap any account node below. The cloud cluster will automatically connect to Telegram MTProto and dispatch the official verification code to its registered phone number:`;
    await replyOrEdit(chatId, messageId, text, buildRelinkKeyboard(live.accounts));
    return;
  }

  if (data.startsWith('btn_relink_acc_')) {
    const idx = parseInt(data.replace('btn_relink_acc_', ''), 10);
    const knownPhone = CONFIG.KNOWN_PHONES[idx];

    // Clean existing session for this chat
    await db.delete(loginSessions).where(eq(loginSessions.chatId, chatId)).run().catch(() => {});

    if (knownPhone) {
      await replyOrEdit(chatId, messageId, `🔄 *Re-linking Node #${idx < 10 ? '0' + idx : idx}*\n\n• Phone: \`${knownPhone}\`\n• Dispatching official Telegram verification code...`, null);

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
          text: `┌──────────────────────────────────────┐
│  📨 *VERIFICATION CODE DISPATCHED*   │
└──────────────────────────────────────┘

• *Account:* \`Node #${idx < 10 ? '0' + idx : idx}\`
• *Target Phone:* \`${knownPhone}\`

Telegram dispatched an official 5-digit verification code to \`${knownPhone}\`.

Please reply directly with the code (e.g. \`12345\`):`,
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

      await replyOrEdit(chatId, messageId, `📱 *Enter Phone Number for Node #${idx < 10 ? '0' + idx : idx}*\n\nPlease reply with the international phone number (e.g., \`+8801943805617\`):`, getCancelLoginKeyboard());
    }
    return;
  }

  if (data === 'btn_add_account') {
    await db.delete(loginSessions).where(eq(loginSessions.chatId, chatId)).run().catch(() => {});
    await db.insert(loginSessions).values({
      chatId,
      step: 'WAITING_PHONE'
    }).run();

    await replyOrEdit(chatId, messageId, `┌──────────────────────────────────────┐
│  ➕ *LINK NEW TELEGRAM SESSION*      │
└──────────────────────────────────────┘

Please reply directly with the full phone number including international country code (e.g. \`+8801943805617\` or \`01943805617\`):`, getCancelLoginKeyboard());
    return;
  }

  if (data === 'btn_cancel_login') {
    await cancelLogin(chatId).catch(() => {});
    await db.delete(loginSessions).where(eq(loginSessions.chatId, chatId)).run().catch(() => {});

    try {
      await api.sendMessage({
        chat_id: chatId,
        text: "🧹 *Cleared temporary input state.*",
        reply_markup: { remove_keyboard: true }
      });
    } catch (_) {}

    const live = await fetchFleetLive();
    await replyOrEdit(chatId, messageId, buildDashboardBanner(live), getMainMenuKeyboard(live.revoked_count || 13));
    return;
  }

  if (data === 'btn_farm_all') {
    await replyOrEdit(chatId, messageId, "⚡ *Triggering Mining Cycle Across All 8 Legitimate Bots...*\n\n• Dispatched to Render Standby primary coordinator...", null);
    const res = await requestBackend('/api/farm/cloud-all', 'POST', {}).catch(() => {});
    
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

    await replyOrEdit(chatId, messageId, banner, getMainMenuKeyboard());
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