#!/usr/bin/env python3
"""
MY AGY AI — Cloudflare Worker Deployment & KV Sync
Deploys `restore-agy` worker to Cloudflare Edge on `aaa-bot.workers.dev`.
"""

import os
import json
import asyncio
import aiohttp

CF_EMAIL = os.getenv("CF_EMAIL_NODE_1", "korimhaji210@gmail.com")
CF_API_KEY = os.getenv("CF_API_KEY_NODE_1", "")
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID_NODE_1", "c9f92ab4a8b26b15f958ac25c22300bc")
KV_NAMESPACE_ID = "315ff9eee275466ba24c01dc2c3f9653"
WORKER_NAME = "restore-agy"
SECRET_KEY = os.getenv("SECRET_KEY", "agy_cf_secret_7d36994e_2026")
OWNER_ID = os.getenv("OWNER_ID", "6727787768")
ALERT_BOT_TOKEN = os.getenv("ALERT_BOT_TOKEN", "")

WORKER_JS = """
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;

    // 1. Health check
    if (path === "/health") {
      return new Response(JSON.stringify({ ok: true, service: "MY AGY AI Edge Gateway", version: "2.0" }), {
        headers: { "Content-Type": "application/json" }
      });
    }

    // 2. 1-Line Bash Bootstrapper script (curl -sSL https://restore-agy.aaa-bot.workers.dev | bash)
    if (path === "/" || path === "/restore" || path === "/install") {
      const bashScript = `#!/usr/bin/env bash
# =======================================================
# MY AGY AI - Lifetime Disaster Recovery Bootstrapper
# Powered by Cloudflare Edge (restore-agy.aaa-bot.workers.dev)
# Compatible with Android Termux & Linux VPS (Ubuntu/Debian)
# =======================================================
set -e

echo "======================================================"
echo "  🚀 MY AGY AI — Restoring Fleet from Cloudflare Edge"
echo "======================================================"

# 1. Detect environment and install packages
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

# 2. Download latest backup archive directly from Cloudflare Edge
echo "📦 Downloading latest backup archive from Cloudflare..."
curl -fsSL "${url.origin}/backup.zip" -o backup.zip

# 3. Unpack archive
echo "📂 Unpacking bot fleet and Antigravity session..."
unzip -o backup.zip

# 4. Run restore.sh
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
          "Cache-Control": "no-cache"
        }
      });
    }

    // 3. Download latest backup zip
    if (path === "/backup.zip") {
      const zipData = await env.BACKUP_KV.get("latest_backup_zip", { type: "arrayBuffer" });
      if (!zipData) {
        return new Response("No backup archive found in Cloudflare KV yet. Run backup first.", {
          status: 404,
          headers: { "Content-Type": "text/plain" }
        });
      }
      return new Response(zipData, {
        headers: {
          "Content-Type": "application/zip",
          "Content-Disposition": 'attachment; filename="my_agy_ai_backup.zip"',
          "Cache-Control": "no-cache"
        }
      });
    }

    // 4. Upload latest backup zip (from VPS backup_manager.py)
    if (path === "/upload" && request.method === "POST") {
      const auth = request.headers.get("Authorization");
      if (auth !== `Bearer ${env.SECRET_KEY}`) {
        return new Response(JSON.stringify({ ok: false, error: "Unauthorized" }), {
          status: 401,
          headers: { "Content-Type": "application/json" }
        });
      }

      const body = await request.arrayBuffer();
      if (!body || body.byteLength === 0) {
        return new Response(JSON.stringify({ ok: false, error: "Empty body" }), {
          status: 400,
          headers: { "Content-Type": "application/json" }
        });
      }

      await env.BACKUP_KV.put("latest_backup_zip", body);
      const meta = {
        updated_at: new Date().toISOString(),
        size_bytes: body.byteLength,
        size_kb: Math.round(body.byteLength / 1024)
      };
      await env.BACKUP_KV.put("latest_backup_meta", JSON.stringify(meta));

      return new Response(JSON.stringify({ ok: true, meta }), {
        headers: { "Content-Type": "application/json" }
      });
    }

    // 5. VPS Heartbeat Sentinel
    if (path === "/heartbeat" && request.method === "POST") {
      const auth = request.headers.get("Authorization");
      if (auth !== `Bearer ${env.SECRET_KEY}`) {
        return new Response(JSON.stringify({ ok: false, error: "Unauthorized" }), {
          status: 401,
          headers: { "Content-Type": "application/json" }
        });
      }

      const data = await request.json().catch(() => ({}));
      const heartbeat = {
        last_seen: Date.now(),
        iso: new Date().toISOString(),
        data
      };
      await env.BACKUP_KV.put("vps_heartbeat", JSON.stringify(heartbeat));

      return new Response(JSON.stringify({ ok: true, recorded: heartbeat.iso }), {
        headers: { "Content-Type": "application/json" }
      });
    }

    // 6. Real-time Status Dashboard (HTML)
    if (path === "/status" || path === "/dashboard") {
      const rawMeta = await env.BACKUP_KV.get("latest_backup_meta");
      const meta = rawMeta ? JSON.parse(rawMeta) : { updated_at: "Never", size_kb: 0 };

      const rawHb = await env.BACKUP_KV.get("vps_heartbeat");
      const hb = rawHb ? JSON.parse(rawHb) : null;
      let vpsStatus = "⚪ Unknown";
      let lastSeenStr = "Never";
      if (hb) {
        const diffSec = Math.round((Date.now() - hb.last_seen) / 1000);
        if (diffSec < 400) {
          vpsStatus = "🟢 Online (Active)";
        } else {
          vpsStatus = `🔴 Offline (${Math.round(diffSec / 60)} min ago)`;
        }
        lastSeenStr = `${diffSec}s ago (${hb.iso})`;
      }

      const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MY AGY AI — Cloudflare Edge Dashboard</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; padding: 20px; max-width: 680px; margin: 0 auto; }
    .card { background: #1e293b; border-radius: 12px; padding: 20px; margin-bottom: 20px; border: 1px solid #334155; }
    h1 { font-size: 1.5rem; color: #38bdf8; margin-top: 0; }
    h2 { font-size: 1.1rem; color: #94a3b8; margin-top: 0; }
    .status-badge { display: inline-block; padding: 4px 10px; border-radius: 9999px; font-weight: 600; font-size: 0.85rem; }
    .online { background: #065f46; color: #34d399; }
    .offline { background: #7f1d1d; color: #f87171; }
    code { background: #020617; padding: 3px 6px; border-radius: 4px; font-family: monospace; color: #38bdf8; font-size: 0.9rem; }
    pre { background: #020617; padding: 12px; border-radius: 8px; overflow-x: auto; color: #a5f3fc; border: 1px solid #1e293b; font-size: 0.85rem; }
    .btn { display: inline-block; background: #0284c7; color: white; padding: 10px 18px; border-radius: 6px; text-decoration: none; font-weight: 600; margin-top: 10px; }
  </style>
</head>
<body>
  <h1>⚡ MY AGY AI — Cloud Edge Sentinel</h1>
  <div class="card">
    <h2>🖥️ VPS Fleet & MTProto Automation Status</h2>
    <p><b>Status:</b> ${vpsStatus}</p>
    <p><b>Last Heartbeat:</b> <code>${lastSeenStr}</code></p>
    ${hb && hb.data ? `<pre>${JSON.stringify(hb.data, null, 2)}</pre>` : ""}
  </div>

  <div class="card">
    <h2>💾 Cloudflare Edge Backup</h2>
    <p><b>Last Updated:</b> <code>${meta.updated_at}</code></p>
    <p><b>Size:</b> <code>${meta.size_kb} KB</code></p>
    <a class="btn" href="/backup.zip">📥 Download Backup Archive</a>
  </div>

  <div class="card">
    <h2>⚡ Lifetime 1-Click Restore Command</h2>
    <p>Copy and run on Android Termux or any new Linux VPS:</p>
    <pre>curl -sSL ${url.origin} | bash</pre>
  </div>
</body>
</html>`;

      return new Response(html, {
        headers: { "Content-Type": "text/html; charset=utf-8" }
      });
    }

    // 7. Workers AI endpoint (Free Cloudflare Edge LLM)
    if (path === "/ai") {
      let prompt = url.searchParams.get("q") || url.searchParams.get("prompt");
      if (request.method === "POST") {
        const body = await request.json().catch(() => ({}));
        prompt = body.prompt || body.q || prompt;
      }

      if (!prompt) {
        return new Response(JSON.stringify({ ok: false, error: "Missing 'q' or 'prompt' query parameter" }), {
          status: 400,
          headers: { "Content-Type": "application/json" }
        });
      }

      try {
        const aiRes = await env.AI.run("@cf/meta/llama-3.2-3b-instruct", {
          prompt: prompt,
          max_tokens: 300
        });
        const ansText = aiRes.response || (aiRes.choices && aiRes.choices[0] ? aiRes.choices[0].text : JSON.stringify(aiRes));
        return new Response(JSON.stringify({ ok: true, answer: ansText.trim() }), {
          headers: { "Content-Type": "application/json" }
        });
      } catch (err) {
        return new Response(JSON.stringify({ ok: false, error: err.message }), {
          status: 500,
          headers: { "Content-Type": "application/json" }
        });
      }
    }

    return new Response("Not Found", { status: 404 });
  }
};
"""


async def deploy():
    print("🚀 Deploying 'restore-agy' worker to Cloudflare Edge...")

    headers = {
        "X-Auth-Email": CF_EMAIL,
        "X-Auth-Key": CF_API_KEY,
    }

    metadata = {
        "main_module": "index.js",
        "bindings": [
            {
                "name": "BACKUP_KV",
                "type": "kv_namespace",
                "namespace_id": KV_NAMESPACE_ID,
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

    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/workers/scripts/{WORKER_NAME}"

    form = aiohttp.FormData()
    form.add_field("metadata", json.dumps(metadata), content_type="application/json", filename="metadata.json")
    form.add_field("index.js", WORKER_JS, content_type="application/javascript+module", filename="index.js")

    async with aiohttp.ClientSession() as session:
        async with session.put(url, headers=headers, data=form) as resp:
            res = await resp.json()

        if not res.get("success"):
            print(f"❌ Worker deployment failed: {res.get('errors')}")
            return False

        print("✅ Worker uploaded successfully!")

        # Enable worker on *.workers.dev subdomain
        subdomain_url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/workers/scripts/{WORKER_NAME}/subdomain"
        async with session.post(subdomain_url, headers=headers, json={"enabled": True}) as resp_sub:
            res_sub = await resp_sub.json()

        if res_sub.get("success"):
            print(f"🎉 Live Worker URL: https://{WORKER_NAME}.korimhaji.workers.dev")
        else:
            print(f"⚠️ Subdomain enable warning: {res_sub.get('errors')}")

    return True


if __name__ == "__main__":
    asyncio.run(deploy())

