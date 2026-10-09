// tgcloud/handlers/callback_query.js — Handles inline keyboard button clicks
import { api } from 'sdk';
import { fetchFleetStatus, triggerFarmSweep, fetchWallets } from '../lib/fleetApi.js';

export default async function (query, ctx) {
  const data = query.data;
  const chatId = query.message?.chat?.id;

  try {
    await api.answerCallbackQuery({
      callback_query_id: query.id,
      text: 'Processing request...'
    });
  } catch (_) {}

  if (!chatId) return;

  if (data === 'cmd_farm') {
    await api.sendMessage({
      chat_id: chatId,
      text: '🚀 *Dispatched farm sweep across all 18 accounts & 9 bots!*',
      parse_mode: 'Markdown'
    });
    await triggerFarmSweep('all');
    return;
  }

  if (data === 'cmd_status') {
    const statusData = await fetchFleetStatus();
    const run = statusData.last_farm_run || {};
    const results = run.results || [];
    let text = `📊 *Fleet Status Summary*\n• Accounts Farmed: ${run.farmed_count || results.length}/18\n• Status: ${run.status || 'Active'}\n\n`;
    for (const r of results.slice(0, 5)) {
      text += `👤 *${r.name || r.uid}*: ${Object.keys(r.bots || {}).length} bots active\n`;
    }
    await api.sendMessage({
      chat_id: chatId,
      text: text,
      parse_mode: 'Markdown'
    });
    return;
  }

  if (data === 'cmd_wallets') {
    const wallets = await fetchWallets();
    const count = Object.keys(wallets).length;
    await api.sendMessage({
      chat_id: chatId,
      text: `💼 *Fleet Wallets*: ${count}/18 TON wallets bound to fleet accounts.`,
      parse_mode: 'Markdown'
    });
    return;
  }

  if (data === 'cmd_cleanup') {
    await api.sendMessage({
      chat_id: chatId,
      text: '🧹 *Autonomous Multi-Tier Clean-Up System Active*\n\n' +
        '• *Tier 1: Disk Hygiene* — Pruning __pycache__, rotating logs, capping local backup zips\n' +
        '• *Tier 2: Phone Guardrail* — Enforcing 0 background bots on phone (Rule 4)\n' +
        '• *Tier 3: Upstash Hygiene* — Trimming lists (fleet:payouts capped to 100) and purging expired security passes\n' +
        '• *Tier 4: CI/CD Hygiene* — Pruning stale GitHub Actions workflow runs older than 7 days\n\n' +
        '⚡ Clean-up runs automatically every 12 hours via Sentinel and on-demand via `python clean_up_system.py`.',
      parse_mode: 'Markdown'
    });
    return;
  }
}
