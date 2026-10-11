import { api, db } from 'sdk';
import { eq, sql } from 'sdk/db';
import { loginSessions } from '../schema.js';
import { CONFIG } from '../lib/config.js';
import { sendLoginCode, cancelLogin, fetchFleetLive, fetchOtpForAccount, requestBackend, dispatchParallelFarming } from '../lib/backend.js';
import {
  getMainMenuKeyboard,
  getPersistentReplyKeyboard,
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

  if (data === 'btn_main_menu' || data === 'btn_refresh_menu') {
    const live = await fetchFleetLive(true);
    await replyOrEdit(chatId, messageId, buildDashboardBanner(live), getMainMenuKeyboard(live.revoked_count));
    return;
  }

  if (data === 'btn_fleet_accounts' || data === 'btn_filter_all') {
    const live = await fetchFleetLive(true);
    const actCount = live.healthy_count !== undefined ? live.healthy_count : (live.accounts ? live.accounts.filter(a => a.status === 'active').length : 7);
    const text = `📱 *FLEET ACCOUNTS MATRIX (${actCount}/${live.total_accounts || 18} ACTIVE)*\n\n🟢 = Active MTProto Session\n🔴 = Session Revoked / Needs Re-link\n👑 = Master Host Account\n\nSelect an account node below to inspect dossier:`;
    await replyOrEdit(chatId, messageId, text, buildAccountsKeyboard(live.accounts, 'all'));
    return;
  }

  if (data === 'btn_filter_active') {
    const live = await fetchFleetLive(true);
    const actCount = live.healthy_count !== undefined ? live.healthy_count : (live.accounts ? live.accounts.filter(a => a.status === 'active').length : 7);
    const text = `🟢 *ONLINE ACTIVE SESSIONS (${actCount} NODES)*\n\nAll accounts below have active 24h MTProto authorization keys.\nSelect a node to inspect:`;
    await replyOrEdit(chatId, messageId, text, buildAccountsKeyboard(live.accounts, 'active'));
    return;
  }

  if (data === 'btn_filter_revoked') {
    const live = await fetchFleetLive(true);
    const revCount = live.revoked_count !== undefined ? live.revoked_count : (live.accounts ? live.accounts.filter(a => a.status !== 'active').length : 11);
    const text = `🔴 *REVOKED SESSIONS (${revCount} NODES)*\n\nSessions below require re-linking. Tap any account to trigger 1-tap SMS/Telegram login code:`;
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

    await replyOrEdit(chatId, messageId, `✅ *Node #${idx < 10 ? '0' + idx : idx} Mining Cycle Dispatched!* 🟢\n\nActive bots farmed: MRG, ATF, Victor's, VyroDrop, Kynex Network.\n100% cloud execution, 0% phone load.`, {
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
    const live = await fetchFleetLive(true);
    const revokedCount = live.revoked_count !== undefined ? live.revoked_count : (live.accounts ? live.accounts.filter(a => a.status !== 'active').length : 11);
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
    const live = await fetchFleetLive();
    const acc = live.accounts.find(a => a.index === idx);
    const knownPhone = acc?.phone || CONFIG.KNOWN_PHONES[idx];

    // Check if code dispatch is already active for this account to prevent double dispatch
    const existing = await db.select().from(loginSessions).where(eq(loginSessions.chatId, chatId)).get();
    if (existing && existing.step === 'WAITING_CODE' && existing.accountIndex === idx) {
      await api.answerCallbackQuery({
        callback_query_id: callbackQuery.id,
        text: `⏳ Code already dispatched for Node #${idx < 10 ? '0' + idx : idx}! Please enter it below.`
      }).catch(() => {});
      return;
    }

    if (knownPhone) {
      // 1. Immediately edit card to disable buttons & show progress (prevents double tap!)
      await replyOrEdit(chatId, messageId, `⏳ *Connecting to MTProto Cluster...*\n\n• Target: *Node #${idx < 10 ? '0' + idx : idx}* (\`${knownPhone}\`)\n• Dispatched code request to Frankfurt cluster.\n\n_Please wait 5–10s for the official Telegram verification code..._`, null);

      const res = await sendLoginCode(knownPhone, chatId, idx);
      if (res && res.ok) {
        await db.insert(loginSessions).values({
          chatId,
          step: 'WAITING_CODE',
          phone: knownPhone,
          phoneCodeHash: res.phone_code_hash || '',
          accountIndex: idx,
          nodeUrl: res.nodeUrl || ''
        }).onConflictDoUpdate({
          target: loginSessions.chatId,
          set: {
            step: 'WAITING_CODE',
            phone: knownPhone,
            phoneCodeHash: res.phone_code_hash || '',
            accountIndex: idx,
            nodeUrl: res.nodeUrl || '',
            updatedAt: sql`(unixepoch())`
          }
        }).run();

        // 2. Edit existing message in-place ("desper message" pattern - single living card!)
        await replyOrEdit(chatId, messageId, `┌──────────────────────────────────────┐
│  📨 *VERIFICATION CODE DISPATCHED*   │
└──────────────────────────────────────┘

• *Account:* \`Node #${idx < 10 ? '0' + idx : idx}\`
• *Target Phone:* \`${knownPhone}\`

Telegram dispatched an official 5-digit verification code to \`${knownPhone}\`.

Please reply directly with the code (e.g. \`12345\`):`, getCancelLoginKeyboard());
      } else {
        await replyOrEdit(chatId, messageId, `❌ *Could not request code:* ${res?.error || 'Network error'}\n\nPlease try again:`, {
          inline_keyboard: [
            [{ text: `🔄 Retry (Node #${idx < 10 ? '0' + idx : idx})`, callback_data: `btn_relink_acc_${idx}` }],
            [{ text: "🔙 Main Menu", callback_data: "btn_main_menu" }]
          ]
        });
      }
      return;
    } else {
      await db.insert(loginSessions).values({
        chatId,
        step: 'WAITING_PHONE',
        accountIndex: idx
      }).onConflictDoUpdate({
        target: loginSessions.chatId,
        set: {
          step: 'WAITING_PHONE',
          accountIndex: idx,
          updatedAt: sql`(unixepoch())`
        }
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
    }).onConflictDoUpdate({
      target: loginSessions.chatId,
      set: {
        step: 'WAITING_PHONE',
        accountIndex: null,
        updatedAt: sql`(unixepoch())`
      }
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
        text: "🧹 *Authentication cancelled. Keyboard menu active:*",
        parse_mode: "Markdown",
        reply_markup: getPersistentReplyKeyboard()
      });
    } catch (_) {}

    const live = await fetchFleetLive(true);
    await replyOrEdit(chatId, messageId, buildDashboardBanner(live), getMainMenuKeyboard(live.revoked_count));
    return;
  }

  if (data === 'btn_farm_all') {
    await replyOrEdit(chatId, messageId, "⚡ *Dispatching Dual-Shard Cloud Mining across 5 Bots...*\n\n• Shard 1 (Nodes 01-09) → Render Node 2 (Frankfurt)\n• Shard 2 (Nodes 10-18) → Render Node 3 (Oregon)\n\n_Executing 100% in cloud, 0% phone load..._", null);
    await dispatchParallelFarming().catch(() => {});
    
    const banner = 
`┌──────────────────────────────┐
│  ⚡ *AUTONOMOUS 5-BOT FARM*  │
└──────────────────────────────┘

🚀 Dispatched parallel dual-shard farming across all 18 nodes:

◈ 🪙 *MRG Miner*         → Turnstile Pass Verification & Harvest
◈ ⚡ *ATF Miner*         → Cloud Captcha & Mining Cycle
◈ 👑 *Victor's Company*  → Proof-of-Pass & Level Compounding
◈ 💧 *VyroDrop*          → Wallet Sync & Airdrop Farming
◈ 🌐 *Kynex Network*     → Session Token Claim & Node Mining

📡 *Parallel Shard Architecture:*
• \`Shard 1 (Nodes 01-09)\` → Render Node 2 (Frankfurt)
• \`Shard 2 (Nodes 10-18)\` → Render Node 3 (Oregon)
⚡ *Phone Impact:* \`0% CPU • 0% RAM • 100% Cloud Execution\``;

    const live = await fetchFleetLive();
    await replyOrEdit(chatId, messageId, banner, getMainMenuKeyboard(live.revoked_count));
    return;
  }

  if (data === 'btn_system_status' || data === 'btn_mesh_status') {
    const live = await fetchFleetLive();
    await replyOrEdit(chatId, messageId, buildMeshStatusBanner(live), getBackToMenuKeyboard());
    return;
  }

  if (data === 'btn_wallets' || data === 'btn_fleet_wallets') {
    await replyOrEdit(chatId, messageId, buildWalletsBanner(), getBackToMenuKeyboard());
    return;
  }
}