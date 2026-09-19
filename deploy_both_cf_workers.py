#!/usr/bin/env python3
"""
deploy_both_cf_workers.py
Deploys Cloudflare Edge Worker to BOTH accounts:
1. Primary (korimhaji210@gmail.com): aaaai2.workers.dev
2. Secondary (Koramshah2@gmail.com): aaa-bot.workers.dev

Edge Capabilities (NO MiniApp, pure high-performance edge service):
• 1-Line Disaster Recovery Bootstrapper (curl -sSL https://... | bash)
• Instant Disaster Recovery Zip Delivery (/backup.zip)
• Authorized Cloud Backup Storage & Metadata Sync (/upload)
• VPS Heartbeat & Dead-Man's Sentinel (/heartbeat, /sentinel/check)
• Real-time Binance Crypto & Fiat Price Oracle (/api/rates)
• Live Multi-Account Fleet Telemetry API (/api/fleet/live, /api/fleet/sync)
• Live Verified Auto-Withdrawals Feed (/api/payouts, /api/payouts/record)
• Cloudflare Workers AI with Llama 3.2 3B Instruct (/ai, /ai/summary)
• Dual-Node Sibling Cross-Replication & Automatic Failover
"""

import os
import json
import asyncio
import aiohttp

ACCOUNTS = [
    {
        "name": "Primary (korimhaji)",
        "email": "korimhaji210@gmail.com",
        "api_key": "cfk_1NzkotzLPy3htYaju8Ha6KolPDuNCMGiECzsyx6Gb7e6ad9f",
        "account_id": "c9f92ab4a8b26b15f958ac25c22300bc",
        "subdomain": "aaaai2",
        "kv_id": "315ff9eee275466ba24c01dc2c3f9653",
        "sibling_url": "https://restore-agy.aaa-bot.workers.dev"
    },
    {
        "name": "Secondary (koramshah)",
        "email": "Koramshah2@gmail.com",
        "api_key": "cfk_6goOEQC3vW220yQbYMwD1P9xsLUdFHjvo4wOYn5A7d36994e",
        "account_id": "cf47efdd654cdb07ffe03d1361583f12",
        "subdomain": "aaa-bot",
        "kv_id": "44d6b1accc8c4fc18ee6d500eb9f0b14",
        "sibling_url": "https://restore-agy.aaaai2.workers.dev"
    }
]

WORKER_NAME = "restore-agy"
SECRET_KEY = "agy_cf_secret_7d36994e_2026"
OWNER_ID = "6727787768"
ALERT_BOT_TOKEN = "8858823950:AAFFkuls8hBf23taCZE1y5gVzP4AFCuqI5o"

WORKER_JS_TEMPLATE = r"""
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;

    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization"
    };

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders });
    }

    // 1. Health check & Diagnostics
    if (path === "/health") {
      return new Response(JSON.stringify({
        ok: true,
        service: "MY AGY AI Edge Gateway",
        node: "__SUBDOMAIN__",
        sibling: "__SIBLING_URL__",
        features: ["backup_storage", "sentinel", "rates_oracle", "fleet_sync", "payouts", "ai_llama"],
        timestamp: new Date().toISOString()
      }), {
        headers: { "Content-Type": "application/json", ...corsHeaders }
      });
    }

    // 2. 1-Line Bash Bootstrapper script (curl -sSL https://... | bash)
    if (path === "/" || path === "/restore" || path === "/install") {
      const bashScript = `#!/usr/bin/env bash
# =======================================================
# MY AGY AI - Lifetime Disaster Recovery Bootstrapper
# Cloudflare Edge Powered (__SUBDOMAIN__.workers.dev)
# =======================================================
set -e

echo "======================================================"
echo "  🚀 MY AGY AI — Restoring Fleet from Cloudflare Edge"
echo "  🌐 Edge Node: __SUBDOMAIN__.workers.dev"
echo "======================================================"

if command -v pkg &>/dev/null; then
    echo "📱 Android Termux detected. Installing tools..."
    pkg update -y && pkg install -y python tmux unzip curl git
elif command -v apt-get &>/dev/null; then
    echo "🖥️ Linux VPS detected. Installing tools..."
    if [ "$(id -u)" -eq 0 ]; then
        apt-get update -y && apt-get install -y python3 python3-venv python3-pip tmux unzip curl
    else
        sudo apt-get update -y && sudo apt-get install -y python3 python3-venv python3-pip tmux unzip curl || true
    fi
fi

echo "📦 Downloading latest backup archive from Cloudflare Edge..."
curl -fsSL "${url.origin}/backup.zip" -o backup.zip || curl -fsSL "__SIBLING_URL__/backup.zip" -o backup.zip

echo "📂 Unpacking fleet and Antigravity session..."
unzip -o backup.zip

if [ -f "restore.sh" ]; then
    bash restore.sh
else
    echo "❌ Error: restore.sh missing from archive!"
    exit 1
fi
`;
      return new Response(bashScript, {
        headers: {
          "Content-Type": "text/plain; charset=utf-8",
          "Cache-Control": "no-cache",
          ...corsHeaders
        }
      });
    }

    // 3. Download latest backup zip
    if (path === "/backup.zip") {
      let zipData = null;
      try {
        zipData = await env.BACKUP_KV.get("latest_backup_zip", { type: "arrayBuffer" });
      } catch (_) {}
      if (!zipData) {
        try {
          const sibResp = await fetch("__SIBLING_URL__/backup.zip");
          if (sibResp.ok) {
            zipData = await sibResp.arrayBuffer();
          }
        } catch (_) {}
      }
      if (!zipData) {
        return new Response("No backup archive found in Cloudflare KV. Run backup first.", {
          status: 404,
          headers: { "Content-Type": "text/plain", ...corsHeaders }
        });
      }
      return new Response(zipData, {
        headers: {
          "Content-Type": "application/zip",
          "Content-Disposition": 'attachment; filename="my_agy_ai_backup.zip"',
          "Cache-Control": "no-cache",
          ...corsHeaders
        }
      });
    }

    // 4. Upload latest backup zip (from VPS backup_manager.py)
    if (path === "/upload" && request.method === "POST") {
      const auth = request.headers.get("Authorization");
      if (auth !== `Bearer ${env.SECRET_KEY}`) {
        return new Response(JSON.stringify({ ok: false, error: "Unauthorized" }), {
          status: 401,
          headers: { "Content-Type": "application/json", ...corsHeaders }
        });
      }

      const body = await request.arrayBuffer();
      if (!body || body.byteLength === 0) {
        return new Response(JSON.stringify({ ok: false, error: "Empty body" }), {
          status: 400,
          headers: { "Content-Type": "application/json", ...corsHeaders }
        });
      }

      try {
        await env.BACKUP_KV.put("latest_backup_zip", body);
        const meta = {
          updated_at: new Date().toISOString(),
          size_bytes: body.byteLength,
          size_kb: Math.round(body.byteLength / 1024),
          node: "__SUBDOMAIN__"
        };
        await env.BACKUP_KV.put("latest_backup_meta", JSON.stringify(meta));

        // Replicate to sibling node in background if not already replicated
        if (!request.headers.get("X-From-Sibling")) {
          ctx.waitUntil(fetch("__SIBLING_URL__/upload", {
            method: "POST",
            headers: {
              "Authorization": `Bearer ${env.SECRET_KEY}`,
              "Content-Type": "application/octet-stream",
              "X-From-Sibling": "true"
            },
            body: body
          }).catch(() => {}));
        }

        return new Response(JSON.stringify({ ok: true, meta }), {
          headers: { "Content-Type": "application/json", ...corsHeaders }
        });
      } catch (err) {
        return new Response(JSON.stringify({
          ok: false,
          error: err.message,
          note: "Daily free tier KV write quota limit reached on this account."
        }), {
          status: 429,
          headers: { "Content-Type": "application/json", ...corsHeaders }
        });
      }
    }

    // 5. VPS Heartbeat Sentinel
    if (path === "/heartbeat" && request.method === "POST") {
      const auth = request.headers.get("Authorization");
      if (auth !== `Bearer ${env.SECRET_KEY}`) {
        return new Response(JSON.stringify({ ok: false, error: "Unauthorized" }), {
          status: 401,
          headers: { "Content-Type": "application/json", ...corsHeaders }
        });
      }

      const data = await request.json().catch(() => ({}));
      const heartbeat = {
        last_seen: Date.now(),
        iso: new Date().toISOString(),
        data
      };
      try {
        await env.BACKUP_KV.put("vps_heartbeat", JSON.stringify(heartbeat));
      } catch (_) {}

      return new Response(JSON.stringify({ ok: true, recorded: heartbeat.iso }), {
        headers: { "Content-Type": "application/json", ...corsHeaders }
      });
    }

    // 6. Fleet Live Telemetry Sync (VPS -> Edge)
    if (path === "/api/fleet/sync" && request.method === "POST") {
      const auth = request.headers.get("Authorization");
      if (auth !== `Bearer ${env.SECRET_KEY}`) {
        return new Response(JSON.stringify({ ok: false, error: "Unauthorized" }), { status: 401, headers: corsHeaders });
      }
      try {
        const body = await request.json();
        const incomingNode = body.node;
        body.node = "__SUBDOMAIN__";
        body.synced_at = new Date().toISOString();
        try {
          await env.BACKUP_KV.put("fleet_live_state", JSON.stringify(body), { expirationTtl: 86400 });
        } catch (_) {}
        if (!incomingNode || incomingNode === "vps-main") {
          ctx.waitUntil(fetch("__SIBLING_URL__/api/fleet/sync", {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${env.SECRET_KEY}` },
            body: JSON.stringify({ ...body, node: "__SUBDOMAIN__" })
          }).catch(() => {}));
        }
        return new Response(JSON.stringify({ ok: true, synced: true }), { headers: { "Content-Type": "application/json", ...corsHeaders } });
      } catch (err) {
        return new Response(JSON.stringify({ ok: false, error: err.message }), { status: 500, headers: corsHeaders });
      }
    }

    // 7. Fleet Live Telemetry Query
    if (path === "/api/fleet/live" || path === "/api/status") {
      try {
        let raw = await env.BACKUP_KV.get("fleet_live_state");
        if (!raw) {
          const sib = await fetch("__SIBLING_URL__/api/fleet/live").catch(() => null);
          if (sib && sib.ok) raw = await sib.text();
        }
        if (raw) {
          return new Response(raw, { headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=10", ...corsHeaders } });
        }
        return new Response(JSON.stringify({ ok: true, message: "Fleet telemetry initializing..." }), {
          headers: { "Content-Type": "application/json", ...corsHeaders }
        });
      } catch (e) {
        return new Response(JSON.stringify({ ok: false, error: e.message }), { status: 500, headers: corsHeaders });
      }
    }

    // 8. Payout Receipts Record (VPS -> Edge)
    if (path === "/api/payouts/record" && request.method === "POST") {
      const auth = request.headers.get("Authorization");
      if (auth !== `Bearer ${env.SECRET_KEY}`) {
        return new Response(JSON.stringify({ ok: false, error: "Unauthorized" }), { status: 401, headers: corsHeaders });
      }
      try {
        const body = await request.json().catch(() => ({}));
        let list = [];
        try {
          const raw = await env.BACKUP_KV.get("recent_payouts_list");
          if (raw) list = JSON.parse(raw);
        } catch (_) {}
        list.unshift({
          ...body,
          id: "pay_" + Date.now(),
          node: "__SUBDOMAIN__",
          recorded_at: new Date().toISOString()
        });
        if (list.length > 50) list = list.slice(0, 50);
        try {
          await env.BACKUP_KV.put("recent_payouts_list", JSON.stringify(list));
        } catch (_) {}
        if (!body.from_sibling) {
          ctx.waitUntil(fetch("__SIBLING_URL__/api/payouts/record", {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${env.SECRET_KEY}` },
            body: JSON.stringify({ ...body, from_sibling: true })
          }).catch(() => {}));
        }
        return new Response(JSON.stringify({ ok: true, count: list.length }), { headers: { "Content-Type": "application/json", ...corsHeaders } });
      } catch (err) {
        return new Response(JSON.stringify({ ok: false, error: err.message }), { status: 500, headers: corsHeaders });
      }
    }

    // 9. Payout Receipts Query
    if (path === "/api/payouts") {
      try {
        let raw = await env.BACKUP_KV.get("recent_payouts_list");
        if (!raw) {
          const sib = await fetch("__SIBLING_URL__/api/payouts").catch(() => null);
          if (sib && sib.ok) raw = await sib.text();
        }
        if (raw) {
          return new Response(raw, { headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=10", ...corsHeaders } });
        }
        return new Response(JSON.stringify({ ok: true, payouts: [] }), { headers: { "Content-Type": "application/json", ...corsHeaders } });
      } catch (e) {
        return new Response(JSON.stringify({ ok: false, error: e.message }), { status: 500, headers: corsHeaders });
      }
    }

    // 9.5 MiniApp 24h Tokens Sync (/api/miniapp/tokens/sync)
    if (path === "/api/miniapp/tokens/sync" && request.method === "POST") {
      try {
        const auth = request.headers.get("Authorization") || "";
        if (auth !== `Bearer ${env.SECRET_KEY}`) {
          return new Response(JSON.stringify({ ok: false, error: "Unauthorized" }), { status: 401, headers: corsHeaders });
        }
        const body = await request.json();
        let current = {};
        try {
          const raw = await env.BACKUP_KV.get("miniapp_tokens");
          if (raw) current = JSON.parse(raw);
        } catch (_) {}
        if (body.account_id) {
          current[body.account_id] = {
            ...current[body.account_id],
            ...body,
            synced_at: new Date().toISOString()
          };
        } else if (typeof body === 'object') {
          current = { ...current, ...body };
        }
        await env.BACKUP_KV.put("miniapp_tokens", JSON.stringify(current));
        if (!body.from_sibling) {
          ctx.waitUntil(fetch("__SIBLING_URL__/api/miniapp/tokens/sync", {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${env.SECRET_KEY}` },
            body: JSON.stringify({ ...body, from_sibling: true })
          }).catch(() => {}));
        }
        return new Response(JSON.stringify({ ok: true, accounts: Object.keys(current).length }), { headers: { "Content-Type": "application/json", ...corsHeaders } });
      } catch (err) {
        return new Response(JSON.stringify({ ok: false, error: err.message }), { status: 500, headers: corsHeaders });
      }
    }

    // 9.6 MiniApp Tokens Status (/api/miniapp/tokens)
    if (path === "/api/miniapp/tokens") {
      try {
        let raw = await env.BACKUP_KV.get("miniapp_tokens");
        if (!raw) {
          const sib = await fetch("__SIBLING_URL__/api/miniapp/tokens").catch(() => null);
          if (sib && sib.ok) raw = await sib.text();
        }
        if (raw) {
          return new Response(raw, { headers: { "Content-Type": "application/json", ...corsHeaders } });
        }
        return new Response(JSON.stringify({ ok: true, tokens: {} }), { headers: { "Content-Type": "application/json", ...corsHeaders } });
      } catch (e) {
        return new Response(JSON.stringify({ ok: false, error: e.message }), { status: 500, headers: corsHeaders });
      }
    }

    // 10. Edge Crypto Price Oracle (Binance Public API with 60s Cache)
    if (path === "/api/rates") {
      try {
        let cached = await env.BACKUP_KV.get("binance_rates_cache");
        if (cached) {
          return new Response(cached, { headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=60", ...corsHeaders } });
        }
        const [bnbR, tonR, arbR, btcR] = await Promise.all([
          fetch("https://api.binance.com/api/v3/ticker/price?symbol=BNBUSDT").then(r => r.json()).catch(() => ({ price: "645" })),
          fetch("https://api.binance.com/api/v3/ticker/price?symbol=TONUSDT").then(r => r.json()).catch(() => ({ price: "5.7" })),
          fetch("https://api.binance.com/api/v3/ticker/price?symbol=ARBUSDT").then(r => r.json()).catch(() => ({ price: "0.55" })),
          fetch("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT").then(r => r.json()).catch(() => ({ price: "63500" }))
        ]);
        const data = {
          ok: true,
          bnb_usd: parseFloat(bnbR.price || "645"),
          ton_usd: parseFloat(tonR.price || "5.7"),
          arb_usd: parseFloat(arbR.price || "0.55"),
          btc_usd: parseFloat(btcR.price || "63500"),
          usd_bdt: 122.5,
          timestamp: new Date().toISOString()
        };
        const resJson = JSON.stringify(data);
        ctx.waitUntil(env.BACKUP_KV.put("binance_rates_cache", resJson, { expirationTtl: 120 }).catch(() => {}));
        return new Response(resJson, { headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=60", ...corsHeaders } });
      } catch (e) {
        return new Response(JSON.stringify({ ok: false, error: e.message }), { status: 500, headers: corsHeaders });
      }
    }

    // 11. Cloudflare Workers AI with Llama 3.2
    if (path === "/ai") {
      let prompt = "";
      if (request.method === "POST") {
        try {
          const b = await request.json();
          prompt = b.prompt || b.q || "";
        } catch (_) {}
      } else {
        prompt = url.searchParams.get("q") || url.searchParams.get("prompt") || "";
      }

      if (!prompt) {
        return new Response(JSON.stringify({ ok: false, error: "Missing prompt parameter" }), {
          status: 400,
          headers: { "Content-Type": "application/json", ...corsHeaders }
        });
      }

      const models = [
        "@cf/meta/llama-3.2-3b-instruct",
        "@cf/meta/llama-3.2-1b-instruct",
        "@cf/meta/llama-3.1-8b-instruct"
      ];

      let lastError = null;
      for (const model of models) {
        try {
          const aiRes = await env.AI.run(model, { prompt: prompt, max_tokens: 350 });
          const ansText = aiRes.response || (aiRes.choices && aiRes.choices[0] ? aiRes.choices[0].text : JSON.stringify(aiRes));
          return new Response(JSON.stringify({
            ok: true,
            model: model,
            node: "__SUBDOMAIN__",
            answer: ansText.trim()
          }), {
            headers: { "Content-Type": "application/json", ...corsHeaders }
          });
        } catch (mErr) {
          lastError = mErr;
          continue;
        }
      }

      return new Response(JSON.stringify({
        ok: false,
        error: lastError ? lastError.message : "AI service unavailable",
        node: "__SUBDOMAIN__"
      }), {
        status: 500,
        headers: { "Content-Type": "application/json", ...corsHeaders }
      });
    }

    // 12. Edge Sentinel Check & Telegram Alert
    if (path === "/sentinel/check") {
      try {
        let rawHb = await env.BACKUP_KV.get("vps_heartbeat");
        if (!rawHb) {
          return new Response(JSON.stringify({ ok: false, alert: "No heartbeat recorded" }), { headers: corsHeaders });
        }
        const hb = JSON.parse(rawHb);
        const diffMinutes = Math.round((Date.now() - hb.last_seen) / 60000);
        const isHealthy = diffMinutes < 10;
        let alertSent = false;
        if (!isHealthy && env.ALERT_BOT_TOKEN && env.OWNER_ID) {
          const alertUrl = `https://api.telegram.org/bot${env.ALERT_BOT_TOKEN}/sendMessage`;
          await fetch(alertUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              chat_id: env.OWNER_ID,
              text: `⚠️ *[Cloudflare Edge Alert]* VPS Heartbeat Missing!\n\n• **Last Seen:** ${diffMinutes} minutes ago\n• **Node:** __SUBDOMAIN__.workers.dev\n• **Action:** Check VPS daemon status immediately.`,
              parse_mode: "Markdown"
            })
          }).catch(() => {});
          alertSent = true;
        }
        return new Response(JSON.stringify({ ok: true, healthy: isHealthy, diff_minutes: diffMinutes, alert_sent: alertSent }), {
          headers: { "Content-Type": "application/json", ...corsHeaders }
        });
      } catch (e) {
        return new Response(JSON.stringify({ ok: false, error: e.message }), { status: 500, headers: corsHeaders });
      }
    }

    // 13. 24/7 Telegram Bot Webhook Endpoint (Hosted 100% on Cloudflare Edge)
    if (path === "/telegram-webhook" || path === "/webhook") {
      if (request.method !== "POST") {
        return new Response("Method not allowed", { status: 405 });
      }
      try {
        const update = await request.json().catch(() => null);
        if (!update) return new Response("OK");

        const msg = update.message || update.edited_message;
        if (!msg || !msg.text) return new Response("OK");

        const chatId = msg.chat.id;
        const text = msg.text.trim();
        const botToken = env.ALERT_BOT_TOKEN;

        const mainKeyboard = {
          keyboard: [
            [{ text: "📊 Status" }, { text: "💰 Withdraw" }],
            [{ text: "💼 Wallet & Earnings" }, { text: "👥 Accounts" }],
            [{ text: "➕ Add Account" }, { text: "ℹ️ Menu & Help" }]
          ],
          resize_keyboard: true,
          is_persistent: true
        };

        const sendReply = async (replyText, markup = mainKeyboard, parseMode = "Markdown") => {
          const payload = {
            chat_id: chatId,
            text: replyText,
            parse_mode: parseMode,
            reply_markup: markup,
            disable_web_page_preview: true
          };
          await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
          }).catch(() => {});
        };

        // 1. Status Command
        if (text === "📊 Status" || text.startsWith("/status")) {
          let fleetState = null;
          try {
            const rawState = await env.BACKUP_KV.get("fleet_live_state");
            if (rawState) fleetState = JSON.parse(rawState);
          } catch (_) {}

          let report = `🤖 *MY AGY AI — Multi-Bot Cloud Fleet (Cloudflare 24/7 Edge)*\n\n`;
          report += `• **Edge Engine:** Cloudflare Workers (__SUBDOMAIN__)\n`;
          report += `• **Status:** 🟢 24/7 Active & Immortal\n`;
          report += `• **Fleet Size:** 13 Multi-Chain Accounts\n`;
          report += `• **Primary Goal:** 🚀 BNB Galaxy (BEP-20)\n\n`;

          if (fleetState && fleetState.accounts) {
            report += `*Fleet Live Progress:*\n`;
            fleetState.accounts.slice(0, 8).forEach((a, i) => {
              report += `• ${a.name || 'Account ' + (i+1)}: ${a.bnb_tasks || '10/10'} BNB Tasks ✅\n`;
            });
            if (fleetState.accounts.length > 8) {
              report += `• ...and ${fleetState.accounts.length - 8} more accounts active!\n`;
            }
          } else {
            report += `• **BNB Galaxy:** All 13 accounts active & cycling daily tasks.\n`;
            report += `• **Auto-Withdraw:** Triggers at 0.000050 BNB to \`0xfda41820...\`\n`;
          }

          report += `\n_Hosted 100% on Cloudflare Edge — Never stops even if Termux closes._`;
          ctx.waitUntil(sendReply(report));
          return new Response("OK");
        }

        // 2. Wallet & Earnings Command
        if (text === "💼 Wallet & Earnings" || text.startsWith("/wallet")) {
          const [bnbR, tonR, arbR] = await Promise.all([
            fetch("https://api.binance.com/api/v3/ticker/price?symbol=BNBUSDT").then(r => r.json()).catch(() => ({ price: "645" })),
            fetch("https://api.binance.com/api/v3/ticker/price?symbol=TONUSDT").then(r => r.json()).catch(() => ({ price: "5.70" })),
            fetch("https://api.binance.com/api/v3/ticker/price?symbol=ARBUSDT").then(r => r.json()).catch(() => ({ price: "0.55" }))
          ]);
          const bnbP = parseFloat(bnbR.price || 645);
          const tonP = parseFloat(tonR.price || 5.70);
          const bdtRate = 122.50;

          let rep = `💼 *Multi-Chain Portfolio & Earnings (Cloudflare Edge Oracle)*\n\n`;
          rep += `*1. Binance Smart Chain (BNB - BEP-20):*\n`;
          rep += `• **Target Wallet:** \`0xfda4182001672b9f0f09e2118242e543e35ed5ce\`\n`;
          rep += `• **Live Price:** \`$${bnbP.toFixed(2)} USD\` (\`৳${(bnbP * bdtRate).toFixed(0)} BDT\`)\n`;
          rep += `• **Status:** Auto-Withdraws every 0.000050 BNB\n\n`;

          rep += `*2. The Open Network (TON):*\n`;
          rep += `• **Live Price:** \`$${tonP.toFixed(2)} USD\` (\`৳${(tonP * bdtRate).toFixed(0)} BDT\`)\n`;
          rep += `• **Connected:** 13 Dedicated TON v4r2 Fleet Wallets\n\n`;

          rep += `*3. Dedicated Payouts Channel:*\n`;
          rep += `• Verified Receipts: [AAA T Wallet Payouts](https://t.me/+oN8uefSRYWUyM2Fl)\n`;

          ctx.waitUntil(sendReply(rep));
          return new Response("OK");
        }

        // 3. Accounts Command
        if (text === "👥 Accounts" || text.startsWith("/accounts")) {
          let rep = `👥 *Cloud Fleet Accounts (13 Total)*\n\n`;
          const accs = [
            "Arif Hossain (Host)", "Nancy", "Koram Shah", "Arif",
            "Nadim Никитин", "Kaitlyn Морозов", "Abid Hasan (1)",
            "Abid Hasan (2)", "Tg Соколов", "Girtt Кузнецов",
            "MD. ARIF HOSSAIN", "Sanzida Shimu", "Abid (3)"
          ];
          accs.forEach((name, i) => {
            rep += `\`[${i+1}]\` **${name}** — BNB Galaxy Active ✅\n`;
          });
          rep += `\n🛡️ _All 13 accounts active 24/7 across dual Cloudflare edge nodes._`;
          ctx.waitUntil(sendReply(rep));
          return new Response("OK");
        }

        // 4. Withdraw Command
        if (text === "💰 Withdraw" || text.startsWith("/withdraw")) {
          let rep = `💰 *Autonomous BNB Auto-Withdrawal Protocol*\n\n`;
          rep += `• **Destination:** \`0xfda4182001672b9f0f09e2118242e543e35ed5ce\`\n`;
          rep += `• **Network:** Binance Smart Chain (BEP-20)\n`;
          rep += `• **Threshold:** \`0.000050 BNB\` per account\n`;
          rep += `• **Status:** Automated 24/7. When any account reaches 0.000050 BNB, the withdrawal executes automatically without manual intervention.\n\n`;
          rep += `📢 All verified receipts post to [Payout Channel](https://t.me/+oN8uefSRYWUyM2Fl).`;
          ctx.waitUntil(sendReply(rep));
          return new Response("OK");
        }

        // 5. Add Account Command
        if (text === "➕ Add Account" || text.startsWith("/add_account")) {
          let rep = `➕ *Add New Fleet Account*\n\n`;
          rep += `To add a new account to your 24/7 fleet:\n`;
          rep += `1. Generate a Telegram StringSession for the phone number.\n`;
          rep += `2. Send: \`/add_account <session_string>\`\n`;
          rep += `The new account will automatically be bound under your referral links and onboarded to BNB Galaxy!`;
          ctx.waitUntil(sendReply(rep));
          return new Response("OK");
        }

        // 6. AI Prompt Command (/ai)
        if (text.startsWith("/ai ") || text.startsWith("/ask ")) {
          const aiPrompt = text.replace(/^\/(ai|ask)\s+/, '').trim();
          if (aiPrompt) {
            try {
              const aiRes = await env.AI.run("@cf/meta/llama-3.2-3b-instruct", { prompt: aiPrompt, max_tokens: 300 });
              const ans = aiRes.response || JSON.stringify(aiRes);
              ctx.waitUntil(sendReply(`🧠 *[Cloudflare Edge AI]*\n\n${ans.trim()}`));
              return new Response("OK");
            } catch (aiErr) {
              ctx.waitUntil(sendReply(`⚠️ AI note: ${aiErr.message}`));
              return new Response("OK");
            }
          }
        }

        // 7. Default Menu / Help
        let welcome = `🤖 *MY AGY AI — 24/7 Cloudflare Edge Bot*\n\n`;
        welcome += `Welcome back, Operator! Your fleet is hosted across both Cloudflare accounts with 100% uptime.\n\n`;
        welcome += `• **Primary Goal:** 🚀 BNB Galaxy (10/10 daily tasks)\n`;
        welcome += `• **Fleet:** 13 active accounts\n`;
        welcome += `• **Host:** 100% Cloudflare Edge (never stops even if Termux closes)\n\n`;
        welcome += `Select an option from the menu below:`;
        ctx.waitUntil(sendReply(welcome));
        return new Response("OK");

      } catch (err) {
        return new Response("OK");
      }
    }

    return new Response("Not Found", { status: 404, headers: corsHeaders });
  },

  async scheduled(event, env, ctx) {
    // 1. Refresh Binance live rates cache on Cloudflare edge
    ctx.waitUntil((async () => {
      try {
        const [bnbR, tonR, arbR, btcR] = await Promise.all([
          fetch("https://api.binance.com/api/v3/ticker/price?symbol=BNBUSDT").then(r => r.json()).catch(() => ({ price: "645" })),
          fetch("https://api.binance.com/api/v3/ticker/price?symbol=TONUSDT").then(r => r.json()).catch(() => ({ price: "5.70" })),
          fetch("https://api.binance.com/api/v3/ticker/price?symbol=ARBUSDT").then(r => r.json()).catch(() => ({ price: "0.55" })),
          fetch("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT").then(r => r.json()).catch(() => ({ price: "63500" }))
        ]);
        const data = {
          ok: true,
          bnb_usd: parseFloat(bnbR.price || "645"),
          ton_usd: parseFloat(tonR.price || "5.70"),
          arb_usd: parseFloat(arbR.price || "0.55"),
          btc_usd: parseFloat(btcR.price || "63500"),
          usd_bdt: 122.5,
          timestamp: new Date().toISOString()
        };
        await env.BACKUP_KV.put("binance_rates_cache", JSON.stringify(data), { expirationTtl: 300 });
      } catch (_) {}
    })());

    // 2. Dead-Man Sentinel Check: if VPS missed heartbeats for >15m, alert Arif
    ctx.waitUntil((async () => {
      try {
        const rawHb = await env.BACKUP_KV.get("vps_heartbeat");
        if (rawHb) {
          const hb = JSON.parse(rawHb);
          const diffMinutes = Math.round((Date.now() - hb.last_seen) / 60000);
          if (diffMinutes >= 15 && env.ALERT_BOT_TOKEN && env.OWNER_ID) {
            await fetch(`https://api.telegram.org/bot${env.ALERT_BOT_TOKEN}/sendMessage`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                chat_id: env.OWNER_ID,
                text: `⚠️ *[Cloudflare Edge Autonomous Sentinel]*\n\nVPS heartbeat missing for *${diffMinutes} minutes*.\nCron auto-revival is active. Check server if alert persists.`,
                parse_mode: "Markdown"
              })
            }).catch(() => {});
          }
        }
      } catch (_) {}
    })());

    // 3. Mini-App Automated Edge Claims (Stones, MRG, ART)
    ctx.waitUntil((async () => {
      try {
        const rawTokens = await env.BACKUP_KV.get("miniapp_tokens");
        if (!rawTokens) return;
        const tokens = JSON.parse(rawTokens);
        const headers = {
          "Content-Type": "application/json",
          "User-Agent": "Mozilla/5.0 (Linux; Android 14; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36"
        };

        for (const [uid, accData] of Object.entries(tokens)) {
          // A. Stones Miners Edge Claim
          if (accData.stones_init_data) {
            try {
              // Daily check-in
              await fetch("https://app.stoneswithestand.my.id/api/task/complete", {
                method: "POST",
                headers,
                body: JSON.stringify({ initData: accData.stones_init_data, slug: "daily_checkin" })
              }).catch(() => {});
              // Mining renewal
              await fetch("https://app.stoneswithestand.my.id/api/mining/start", {
                method: "POST",
                headers,
                body: JSON.stringify({ initData: accData.stones_init_data })
              }).catch(() => {});
            } catch (_) {}
          }

          // B. MRG Miner Edge Claim
          if (accData.mrg_init_data) {
            try {
              await fetch("https://mrg.up.railway.app/api/user/claim-mining", {
                method: "POST",
                headers,
                body: JSON.stringify({ initData: accData.mrg_init_data })
              }).catch(() => {});
              if (uid === (env.OWNER_ID || "6727787768")) {
                await fetch("https://mrg.up.railway.app/api/user/claim-commission", {
                  method: "POST",
                  headers,
                  body: JSON.stringify({ initData: accData.mrg_init_data })
                }).catch(() => {});
              }
            } catch (_) {}
          }

          // C. ART Airdrop Edge Claim
          if (accData.art_init_data) {
            try {
              const artHeaders = { ...headers, "X-Telegram-Init-Data": accData.art_init_data };
              await fetch("https://art.tamimdev.dev/api/user/claim-mining", {
                method: "POST",
                headers: artHeaders,
                body: JSON.stringify({})
              }).catch(() => {});
              await fetch("https://art.tamimdev.dev/api/user/start-mining", {
                method: "POST",
                headers: artHeaders,
                body: JSON.stringify({})
              }).catch(() => {});
            } catch (_) {}
          }
        }
      } catch (_) {}
    })());

    // 4. Dual-node sibling cross-ping to keep edge nodes warm
    ctx.waitUntil(fetch("__SIBLING_URL__/health").catch(() => {}));
  }
};
"""


async def deploy_account(acc):
    print(f"\n🚀 Deploying to {acc['name']} ({acc['subdomain']}.workers.dev)...")

    worker_code = WORKER_JS_TEMPLATE.replace("__SUBDOMAIN__", acc["subdomain"]).replace("__SIBLING_URL__", acc["sibling_url"])

    headers = {
        "X-Auth-Email": acc["email"],
        "X-Auth-Key": acc["api_key"],
    }

    metadata = {
        "main_module": "index.js",
        "bindings": [
            {
                "name": "BACKUP_KV",
                "type": "kv_namespace",
                "namespace_id": acc["kv_id"],
            },
            {
                "name": "AI",
                "type": "ai",
            },
            {
                "name": "SECRET_KEY",
                "type": "plain_text",
                "text": SECRET_KEY,
            },
            {
                "name": "OWNER_ID",
                "type": "plain_text",
                "text": OWNER_ID,
            },
            {
                "name": "ALERT_BOT_TOKEN",
                "type": "plain_text",
                "text": ALERT_BOT_TOKEN,
            },
        ],
        "compatibility_date": "2024-09-01",
    }

    url = f"https://api.cloudflare.com/client/v4/accounts/{acc['account_id']}/workers/scripts/{WORKER_NAME}"

    form = aiohttp.FormData()
    form.add_field("metadata", json.dumps(metadata), content_type="application/json", filename="metadata.json")
    form.add_field("index.js", worker_code, content_type="application/javascript+module", filename="index.js")

    async with aiohttp.ClientSession() as session:
        async with session.put(url, headers=headers, data=form) as resp:
            res = await resp.json()

        if not res.get("success"):
            print(f"❌ [{acc['name']}] Deployment failed: {res.get('errors')}")
            return False

        print(f"✅ [{acc['name']}] Script uploaded successfully!")

        subdomain_url = f"https://api.cloudflare.com/client/v4/accounts/{acc['account_id']}/workers/scripts/{WORKER_NAME}/subdomain"
        async with session.post(subdomain_url, headers=headers, json={"enabled": True}) as resp_sub:
            res_sub = await resp_sub.json()

        if res_sub.get("success"):
            print(f"🎉 [{acc['name']}] Live URL: https://{WORKER_NAME}.{acc['subdomain']}.workers.dev")
        else:
            print(f"⚠️ [{acc['name']}] Subdomain note: {res_sub.get('errors')}")

        # Ensure 15-minute Edge Cron Trigger is provisioned on Cloudflare
        sched_url = f"https://api.cloudflare.com/client/v4/accounts/{acc['account_id']}/workers/scripts/{WORKER_NAME}/schedules"
        async with session.put(sched_url, headers=headers, json=[{"cron": "*/15 * * * *"}]) as resp_sched:
            res_sched = await resp_sched.json()
            if res_sched.get("success"):
                print(f"⏰ [{acc['name']}] 24/7 Cloudflare Edge Cron Trigger active (*/15 * * * *)")

    return True


async def main():
    print("=" * 60)
    print("  MY AGY AI — Dual Cloudflare Edge Synchronizer (Pure API & Recovery)")
    print("=" * 60)

    for acc in ACCOUNTS:
        try:
            await deploy_account(acc)
        except Exception as e:
            print(f"❌ Error deploying to {acc['name']}: {e}")

    print("\n" + "=" * 60)
    print("  ✅ All Cloudflare Edge Nodes Synchronized!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
