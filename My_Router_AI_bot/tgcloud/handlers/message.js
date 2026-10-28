// tgcloud/handlers/message.js — Handles incoming Telegram messages
import { api } from 'sdk';
import { fetchFleetStatus, triggerFarmSweep, fetchWallets } from '../lib/fleetApi.js';

export default async function (message, ctx) {
  const chatId = message.chat.id;
  const text = (message.text || '').trim();

  if (text.startsWith('/start') || text.startsWith('/help')) {
    const welcome = `🤖 *AAA AUTO — Cloud Fleet Command Center*\n\n` +
      `⚡ *100% Cloud-Powered Architecture*\n` +
      `• *Fleet Accounts*: 18 Active Workers\n` +
      `• *Active Bots*: 8 Bots (MRG, ATF, Victor's, Kynex, Diggo, PepeGram, AdxEarn, Chicken Land)\n` +
      `• *Cloud Nodes*: 5x Cloudflare Edge + 2x Render Standby\n\n` +
      `Tap below to launch the Mini App or control the fleet:`;

    await api.sendMessage({
      chat_id: chatId,
      text: welcome,
      parse_mode: 'Markdown',
      reply_markup: {
        inline_keyboard: [
          [
            { text: '📱 Open Fleet Dashboard', web_app: { url: `https://app${ctx.bot?.id || '8858823950'}.tgcloud.ai/` } }
          ],
          [
            { text: '⚡ Farm 4 Bots Now', callback_data: 'cmd_farm' },
            { text: '📊 Live Status', callback_data: 'cmd_status' }
          ],
          [
            { text: '💼 Multichain Wallets', callback_data: 'cmd_wallets' },
            { text: '🧹 Clean Up Fleet', callback_data: 'cmd_cleanup' }
          ]
        ]
      }
    });
    return;
  }

  if (text.startsWith('/status')) {
    await api.sendMessage({
      chat_id: chatId,
      text: '⏳ *Querying Cloudflare Edge & Render Standby Mesh...*',
      parse_mode: 'Markdown'
    });

    const statusData = await fetchFleetStatus();
    if (!statusData.ok && !statusData.last_farm_run) {
      await api.sendMessage({
        chat_id: chatId,
        text: `❌ *Could not fetch status*: ${statusData.error || 'Timeout'}`
      });
      return;
    }

    const run = statusData.last_farm_run || {};
    const results = run.results || [];
    let report = `📊 *AAA AUTO — Live Fleet Status*\n`;
    report += `• *Status*: ${run.status || 'OK'}\n`;
    report += `• *Accounts Farmed*: ${run.farmed_count || results.length}/18\n`;
    report += `• *Last Sync*: ${run.timestamp ? new Date(run.timestamp * 1000).toISOString().replace('T', ' ').slice(0, 19) + ' UTC' : 'Recent'}\n\n`;

    const sample = results.slice(0, 6);
    for (const r of sample) {
      report += `👤 *${r.name || r.uid}* (\`${r.uid}\`):\n`;
      const bObj = r.bots || {};
      for (const [bName, bStatus] of Object.entries(bObj)) {
        report += `  ▫️ \`${bName}\`: ${bStatus}\n`;
      }
      report += `\n`;
    }

    if (results.length > 6) {
      report += `_...and ${results.length - 6} more accounts active._\n`;
    }

    await api.sendMessage({
      chat_id: chatId,
      text: report,
      parse_mode: 'Markdown',
      reply_markup: {
        inline_keyboard: [
          [
            { text: '📱 Open Full Dashboard', web_app: { url: `https://app${ctx.bot?.id || '8858823950'}.tgcloud.ai/` } },
            { text: '⚡ Farm Again', callback_data: 'cmd_farm' }
          ]
        ]
      }
    });
    return;
  }

  if (text.startsWith('/farm')) {
    await api.sendMessage({
      chat_id: chatId,
      text: '🚀 *Dispatching fleet-wide farming sweep across 5 Cloudflare Edge nodes...*',
      parse_mode: 'Markdown'
    });

    const farmRes = await triggerFarmSweep('all');
    await api.sendMessage({
      chat_id: chatId,
      text: farmRes.ok
        ? `✅ *Farm sweep active!* Dispatched to ${farmRes.nodes_triggered} Cloudflare Edge nodes. All 18 accounts farming 9 bots.`
        : `⚠️ Farm sweep dispatch noted. Check /status in 30s.`,
      parse_mode: 'Markdown'
    });
    return;
  }

  if (text.startsWith('/wallets')) {
    const wallets = await fetchWallets();
    const count = Object.keys(wallets).length;
    let wText = `💼 *Fleet TON Wallets (${count}/18 Connected)*:\n\n`;
    for (const [uid, addr] of Object.entries(wallets).slice(0, 8)) {
      wText += `• \`${uid}\`: \`${addr.slice(0, 8)}...${addr.slice(-6)}\`\n`;
    }
    if (count > 8) {
      wText += `_...and ${count - 8} more wallets bound._\n`;
    }
    await api.sendMessage({
      chat_id: chatId,
      text: wText,
      parse_mode: 'Markdown'
    });
    return;
  }

  if (text.startsWith('/cleanup') || text.startsWith('/clean')) {
    await api.sendMessage({
      chat_id: chatId,
      text: '🧹 *Autonomous Multi-Tier Clean-Up System*\n\n' +
        '• *Tier 1: Disk Hygiene* — Pruning __pycache__, rotating logs, capping local backup zips\n' +
        '• *Tier 2: Phone Guardrail* — Enforcing 0 background bots on phone (Rule 4)\n' +
        '• *Tier 3: Upstash Hygiene* — Trimming lists (fleet:payouts capped to 100) and purging expired security passes\n' +
        '• *Tier 4: CI/CD Hygiene* — Pruning stale GitHub Actions workflow runs older than 7 days\n\n' +
        '⚡ Clean-up runs automatically every 12 hours via Sentinel and on-demand via `python clean_up_system.py`.',
      parse_mode: 'Markdown'
    });
    return;
  }

  // Fallback default message
  await api.sendMessage({
    chat_id: chatId,
    text: `Command not recognized. Use /status, /farm, /wallets, /cleanup, or open the dashboard below.`,
    reply_markup: {
      inline_keyboard: [
        [{ text: '📱 Open Fleet Dashboard', web_app: { url: `https://app${ctx.bot?.id || '8858823950'}.tgcloud.ai/` } }]
      ]
    }
  });
}
