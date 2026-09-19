
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;

    // 1. Health check
    if (path === "/health") {
      return new Response(JSON.stringify({ ok: true, service: "MY AGY AI Edge Gateway", version: "3.5" }), {
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
curl -fsSL "${url.origin}/backup.zip" -o backup.zip

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

    // 6. MiniApp & Terminal: Execute Command (Pushed to KV Queue)
    if (path === "/api/miniapp/exec" && request.method === "POST") {
      const reqData = await request.json().catch(() => ({}));
      const cmd = reqData.command || reqData.cmd;
      if (!cmd) {
        return new Response(JSON.stringify({ ok: false, error: "No command provided" }), {
          status: 400,
          headers: { "Content-Type": "application/json" }
        });
      }

      const cmdId = "cmd_" + Date.now() + "_" + Math.random().toString(36).substring(2, 7);
      const cmdItem = { id: cmdId, cmd: cmd.trim(), timestamp: Date.now() };

      await env.BACKUP_KV.put("vps_cmd_queue", JSON.stringify(cmdItem));

      // Wait up to 5.5 seconds for response in KV
      let result = null;
      for (let i = 0; i < 28; i++) {
        await new Promise(r => setTimeout(r, 200));
        const resStr = await env.BACKUP_KV.get("vps_cmd_result_" + cmdId);
        if (resStr) {
          result = JSON.parse(resStr);
          await env.BACKUP_KV.delete("vps_cmd_result_" + cmdId);
          break;
        }
      }

      if (result) {
        return new Response(JSON.stringify({ ok: true, done: true, output: result.output, exit_code: result.exit_code }), {
          headers: { "Content-Type": "application/json" }
        });
      } else {
        return new Response(JSON.stringify({
          ok: true,
          done: false,
          id: cmdId,
          queued: true
        }), {
          headers: { "Content-Type": "application/json" }
        });
      }
    }

    // 7. MiniApp & Terminal: Check Asynchronous Command Result
    if (path === "/api/miniapp/check_result") {
      const cmdId = url.searchParams.get("id");
      if (!cmdId) {
        return new Response(JSON.stringify({ ok: false, error: "Missing cmd id" }), { status: 400 });
      }
      const resStr = await env.BACKUP_KV.get("vps_cmd_result_" + cmdId);
      if (resStr) {
        const res = JSON.parse(resStr);
        await env.BACKUP_KV.delete("vps_cmd_result_" + cmdId);
        return new Response(JSON.stringify({ ok: true, done: true, output: res.output, exit_code: res.exit_code }), {
          headers: { "Content-Type": "application/json" }
        });
      }
      return new Response(JSON.stringify({ ok: true, done: false }), {
        headers: { "Content-Type": "application/json" }
      });
    }

    // 8. MiniApp & Terminal: Poll Pending Command (Used by VPS)
    if (path === "/api/miniapp/poll_cmd") {
      const auth = request.headers.get("Authorization");
      if (auth !== `Bearer ${env.SECRET_KEY}`) {
        return new Response(JSON.stringify({ ok: false, error: "Unauthorized" }), { status: 401 });
      }

      const rawQ = await env.BACKUP_KV.get("vps_cmd_queue");
      if (rawQ) {
        const item = JSON.parse(rawQ);
        await env.BACKUP_KV.delete("vps_cmd_queue");
        return new Response(JSON.stringify({ ok: true, has_command: true, ...item }), {
          headers: { "Content-Type": "application/json" }
        });
      }
      return new Response(JSON.stringify({ ok: true, has_command: false }), {
        headers: { "Content-Type": "application/json" }
      });
    }

    // 9. MiniApp & Terminal: Submit Command Result (Used by VPS)
    if (path === "/api/miniapp/submit_result" && request.method === "POST") {
      const auth = request.headers.get("Authorization");
      if (auth !== `Bearer ${env.SECRET_KEY}`) {
        return new Response(JSON.stringify({ ok: false, error: "Unauthorized" }), { status: 401 });
      }

      const resBody = await request.json().catch(() => ({}));
      const cmdId = resBody.id;
      if (cmdId) {
        await env.BACKUP_KV.put("vps_cmd_result_" + cmdId, JSON.stringify(resBody), { expirationTtl: 180 });
      }
      return new Response(JSON.stringify({ ok: true }), { headers: { "Content-Type": "application/json" } });
    }

    // 10. MiniApp & Terminal: Push Logs & Get Logs
    if (path === "/api/miniapp/push_logs" && request.method === "POST") {
      const auth = request.headers.get("Authorization");
      if (auth !== `Bearer ${env.SECRET_KEY}`) {
        return new Response(JSON.stringify({ ok: false, error: "Unauthorized" }), { status: 401 });
      }
      const rawText = await request.text();
      await env.BACKUP_KV.put("vps_logs", rawText, { expirationTtl: 3600 });
      return new Response(JSON.stringify({ ok: true }), { headers: { "Content-Type": "application/json" } });
    }

    if (path === "/api/miniapp/logs") {
      const logs = (await env.BACKUP_KV.get("vps_logs")) || "No live logs pushed yet. Connecting to VPS...";
      return new Response(JSON.stringify({ ok: true, logs }), { headers: { "Content-Type": "application/json" } });
    }

    if (path === "/api/miniapp/status") {
      const rawMeta = await env.BACKUP_KV.get("latest_backup_meta");
      const meta = rawMeta ? JSON.parse(rawMeta) : { updated_at: "Never", size_kb: 0 };
      const rawHb = await env.BACKUP_KV.get("vps_heartbeat");
      const hb = rawHb ? JSON.parse(rawHb) : null;
      return new Response(JSON.stringify({ ok: true, meta, heartbeat: hb }), {
        headers: { "Content-Type": "application/json" }
      });
    }

    // 11. Workers AI endpoint
    if (path === "/ai") {
      let prompt = url.searchParams.get("q") || url.searchParams.get("prompt");
      if (request.method === "POST") {
        const body = await request.json().catch(() => ({}));
        prompt = body.prompt || body.q || prompt;
      }
      if (!prompt) {
        return new Response(JSON.stringify({ ok: false, error: "Missing prompt" }), { status: 400 });
      }
      try {
        const aiRes = await env.AI.run("@cf/meta/llama-3.2-3b-instruct", { prompt: prompt, max_tokens: 350 });
        const ansText = aiRes.response || (aiRes.choices && aiRes.choices[0] ? aiRes.choices[0].text : JSON.stringify(aiRes));
        return new Response(JSON.stringify({ ok: true, answer: ansText.trim() }), {
          headers: { "Content-Type": "application/json" }
        });
      } catch (err) {
        return new Response(JSON.stringify({ ok: false, error: err.message }), { status: 500 });
      }
    }

    // 12. TELEGRAM BOT MINI APP & INTERACTIVE WEB TERMINAL
    if (path === "/app" || path === "/miniapp" || path === "/terminal" || path === "/status" || path === "/dashboard") {
      return new Response(MINIAPP_HTML, {
        headers: { "Content-Type": "text/html; charset=utf-8" }
      });
    }

    return new Response("Not Found", { status: 404 });
  }
};

const MINIAPP_HTML = "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n  <meta charset=\"UTF-8\">\n  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover\">\n  <title>MY AGY AI \u2014 Cloud Terminal & Operations Console</title>\n  <script src=\"https://telegram.org/js/telegram-web-app.js\"></script>\n  <style>\n    :root {\n      --bg: #070a12;\n      --card-bg: #0f172a;\n      --card-border: #1e293b;\n      --primary: #00ff9d;\n      --accent: #38bdf8;\n      --text: #f8fafc;\n      --muted: #94a3b8;\n      --danger: #f43f5e;\n      --warning: #f59e0b;\n      --term-bg: #020617;\n      --term-text: #4ade80;\n      --safe-bottom: env(safe-area-inset-bottom, 0px);\n    }\n    * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }\n    html, body {\n      height: 100%;\n      height: -webkit-fill-available;\n      height: 100dvh;\n      width: 100%;\n      overflow: hidden;\n      position: fixed;\n      background: var(--bg);\n      color: var(--text);\n      font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, Helvetica, Arial, sans-serif;\n      display: flex;\n      flex-direction: column;\n    }\n    \n    /* Header */\n    .header {\n      flex-shrink: 0;\n      background: rgba(15, 23, 42, 0.98);\n      backdrop-filter: blur(16px);\n      border-bottom: 1px solid var(--card-border);\n      padding: 8px 12px;\n      display: flex;\n      justify-content: space-between;\n      align-items: center;\n      z-index: 50;\n    }\n    .header-left {\n      display: flex;\n      align-items: center;\n      gap: 6px;\n    }\n    .header-brand {\n      font-weight: 800;\n      font-size: 0.9rem;\n      color: #fff;\n      display: flex;\n      align-items: center;\n      gap: 4px;\n    }\n    .header-badge {\n      background: linear-gradient(135deg, #0284c7, #06b6d4);\n      color: #fff;\n      font-size: 0.6rem;\n      padding: 1px 5px;\n      border-radius: 4px;\n      font-weight: 800;\n      letter-spacing: 0.5px;\n    }\n    .header-actions {\n      display: flex;\n      align-items: center;\n      gap: 6px;\n    }\n    .ide-header-btn {\n      background: linear-gradient(135deg, #3b82f6, #1d4ed8);\n      color: #fff;\n      border: none;\n      font-size: 0.68rem;\n      font-weight: 700;\n      padding: 4px 8px;\n      border-radius: 6px;\n      display: flex;\n      align-items: center;\n      gap: 4px;\n      cursor: pointer;\n      box-shadow: 0 2px 6px rgba(59, 130, 246, 0.3);\n    }\n    .ide-header-btn:active { opacity: 0.8; }\n    .status-pill {\n      font-size: 0.68rem;\n      font-weight: 600;\n      padding: 3px 8px;\n      border-radius: 999px;\n      display: flex;\n      align-items: center;\n      gap: 5px;\n      background: rgba(16, 185, 129, 0.12);\n      color: #10b981;\n      border: 1px solid rgba(16, 185, 129, 0.3);\n    }\n    .status-pill.offline {\n      background: rgba(244, 63, 94, 0.12);\n      color: var(--danger);\n      border-color: rgba(244, 63, 94, 0.3);\n    }\n    .dot {\n      width: 6px;\n      height: 6px;\n      border-radius: 50%;\n      background: currentColor;\n      box-shadow: 0 0 6px currentColor;\n    }\n\n    /* Main Viewport Container */\n    .viewport-container {\n      flex: 1;\n      min-height: 0;\n      display: flex;\n      flex-direction: column;\n      position: relative;\n      overflow: hidden;\n    }\n    .tab-pane {\n      display: none;\n      flex: 1;\n      min-height: 0;\n      flex-direction: column;\n      padding: 8px 10px;\n    }\n    .tab-pane.active {\n      display: flex;\n    }\n\n    /* Scrollable Tab Pane for Fleet */\n    .tab-pane.scrollable {\n      overflow-y: auto;\n      -webkit-overflow-scrolling: touch;\n      padding-bottom: 24px;\n    }\n\n    /* Terminal Tab */\n    #pane-terminal {\n      overflow: hidden;\n    }\n    .chip-bar {\n      flex-shrink: 0;\n      display: flex;\n      gap: 6px;\n      overflow-x: auto;\n      padding-bottom: 6px;\n      scrollbar-width: none;\n    }\n    .chip-bar::-webkit-scrollbar { display: none; }\n    .chip {\n      flex-shrink: 0;\n      background: #1e293b;\n      border: 1px solid #334155;\n      color: #cbd5e1;\n      border-radius: 14px;\n      padding: 4px 9px;\n      font-size: 0.7rem;\n      font-family: monospace;\n      cursor: pointer;\n      display: flex;\n      align-items: center;\n      gap: 4px;\n    }\n    .chip:active {\n      background: #0284c7;\n      color: #fff;\n      border-color: #38bdf8;\n    }\n    .chip.highlight {\n      background: linear-gradient(135deg, #1e3a8a, #1e40af);\n      border-color: #60a5fa;\n      color: #93c5fd;\n      font-weight: 700;\n    }\n\n    .terminal-card {\n      flex: 1;\n      min-height: 0;\n      background: var(--term-bg);\n      border: 1px solid var(--card-border);\n      border-radius: 8px;\n      display: flex;\n      flex-direction: column;\n      overflow: hidden;\n      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);\n    }\n    .term-title-bar {\n      flex-shrink: 0;\n      background: #0f172a;\n      border-bottom: 1px solid #1e293b;\n      padding: 5px 8px;\n      display: flex;\n      justify-content: space-between;\n      align-items: center;\n    }\n    .term-dots {\n      display: flex;\n      gap: 4px;\n    }\n    .t-dot { width: 8px; height: 8px; border-radius: 50%; }\n    .t-red { background: #ef4444; }\n    .t-yel { background: #eab308; }\n    .t-grn { background: #22c55e; }\n    .term-hostname {\n      font-family: monospace;\n      font-size: 0.68rem;\n      color: var(--muted);\n    }\n    .term-actions {\n      display: flex;\n      gap: 4px;\n    }\n    .t-btn {\n      background: #1e293b;\n      border: 1px solid #334155;\n      color: #94a3b8;\n      font-size: 0.65rem;\n      padding: 2px 6px;\n      border-radius: 4px;\n      cursor: pointer;\n    }\n    .t-btn:active { color: #fff; border-color: var(--accent); }\n\n    .term-screen {\n      flex: 1;\n      min-height: 0;\n      padding: 8px 10px;\n      overflow-y: auto;\n      font-family: \"SFMono-Regular\", Consolas, \"Liberation Mono\", Menlo, Courier, monospace;\n      font-size: 0.74rem;\n      line-height: 1.4;\n      color: var(--term-text);\n      white-space: pre-wrap;\n      word-break: break-all;\n      -webkit-overflow-scrolling: touch;\n    }\n    .term-prompt-line { color: var(--accent); font-weight: bold; margin-top: 6px; }\n    .term-loading-line { color: var(--warning); font-style: italic; margin: 3px 0; }\n    .term-error-line { color: var(--danger); }\n    .term-info-line { color: #94a3b8; }\n\n    .term-input-row {\n      flex-shrink: 0;\n      background: #0f172a;\n      border-top: 1px solid #1e293b;\n      padding: 6px 8px;\n      display: flex;\n      align-items: center;\n      gap: 6px;\n    }\n    .term-prompt-symbol {\n      color: var(--primary);\n      font-family: monospace;\n      font-weight: 700;\n      font-size: 0.85rem;\n    }\n    .term-text-input {\n      flex: 1;\n      background: transparent;\n      border: none;\n      outline: none;\n      color: #fff;\n      font-family: monospace;\n      font-size: 0.8rem;\n    }\n    .term-run-btn {\n      background: linear-gradient(135deg, #0284c7, #026ca3);\n      color: #fff;\n      border: none;\n      border-radius: 6px;\n      padding: 5px 12px;\n      font-size: 0.72rem;\n      font-weight: 700;\n      cursor: pointer;\n    }\n    .term-run-btn:active { opacity: 0.8; }\n\n    /* Fleet Tab */\n    .featured-ide-card {\n      background: linear-gradient(135deg, rgba(30, 58, 138, 0.35), rgba(15, 23, 42, 0.95));\n      border: 1px solid #3b82f6;\n      border-radius: 10px;\n      padding: 12px;\n      margin-bottom: 10px;\n      display: flex;\n      justify-content: space-between;\n      align-items: center;\n      box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);\n    }\n    .featured-ide-title { font-size: 0.82rem; font-weight: 800; color: #60a5fa; display: flex; align-items: center; gap: 6px; }\n    .featured-ide-sub { font-size: 0.68rem; color: #cbd5e1; margin-top: 2px; }\n    .featured-ide-btn {\n      background: linear-gradient(135deg, #2563eb, #1d4ed8);\n      color: #fff;\n      border: none;\n      padding: 7px 12px;\n      border-radius: 6px;\n      font-size: 0.72rem;\n      font-weight: 700;\n      cursor: pointer;\n      display: flex;\n      align-items: center;\n      gap: 4px;\n      box-shadow: 0 2px 8px rgba(37, 99, 235, 0.4);\n    }\n    .featured-ide-btn:active { opacity: 0.85; }\n\n    .fleet-grid {\n      display: grid;\n      grid-template-columns: 1fr 1fr;\n      gap: 8px;\n      margin-bottom: 10px;\n    }\n    .stat-card {\n      background: var(--card-bg);\n      border: 1px solid var(--card-border);\n      border-radius: 8px;\n      padding: 8px 10px;\n    }\n    .stat-card-title {\n      font-size: 0.62rem;\n      color: var(--muted);\n      text-transform: uppercase;\n      letter-spacing: 0.5px;\n    }\n    .stat-card-val {\n      font-size: 1rem;\n      font-weight: 800;\n      color: #fff;\n      margin-top: 2px;\n    }\n    .stat-card-sub {\n      font-size: 0.65rem;\n      color: var(--primary);\n      margin-top: 1px;\n    }\n\n    .section-title {\n      font-size: 0.78rem;\n      font-weight: 700;\n      color: var(--accent);\n      margin: 8px 0 5px 0;\n      display: flex;\n      align-items: center;\n      gap: 6px;\n    }\n    .account-roster {\n      display: flex;\n      flex-direction: column;\n      gap: 6px;\n      margin-bottom: 10px;\n    }\n    .account-row {\n      background: var(--card-bg);\n      border: 1px solid var(--card-border);\n      border-radius: 8px;\n      padding: 7px 10px;\n      display: flex;\n      justify-content: space-between;\n      align-items: center;\n    }\n    .account-info {\n      display: flex;\n      flex-direction: column;\n      gap: 1px;\n    }\n    .acc-name { font-size: 0.78rem; font-weight: 700; color: #fff; }\n    .acc-meta { font-size: 0.66rem; color: var(--muted); }\n    .acc-badge {\n      font-size: 0.62rem;\n      font-weight: 700;\n      padding: 2px 6px;\n      border-radius: 999px;\n      background: rgba(0, 255, 157, 0.15);\n      color: var(--primary);\n      border: 1px solid rgba(0, 255, 157, 0.3);\n    }\n\n    .action-grid {\n      display: grid;\n      grid-template-columns: 1fr 1fr;\n      gap: 8px;\n      margin-top: 4px;\n      margin-bottom: 10px;\n    }\n    .fleet-btn {\n      background: #1e293b;\n      border: 1px solid #334155;\n      color: #fff;\n      padding: 9px;\n      border-radius: 8px;\n      font-size: 0.72rem;\n      font-weight: 600;\n      cursor: pointer;\n      display: flex;\n      align-items: center;\n      justify-content: center;\n      gap: 5px;\n    }\n    .fleet-btn:active { background: #334155; }\n    .fleet-btn.primary { background: linear-gradient(135deg, #0284c7, #0369a1); border: none; }\n    .fleet-btn.success { background: linear-gradient(135deg, #059669, #047857); border: none; }\n\n    /* Logs Tab */\n    #pane-logs {\n      overflow: hidden;\n    }\n    .logs-card {\n      flex: 1;\n      min-height: 0;\n      background: var(--card-bg);\n      border: 1px solid var(--card-border);\n      border-radius: 8px;\n      display: flex;\n      flex-direction: column;\n      overflow: hidden;\n    }\n    .logs-header {\n      flex-shrink: 0;\n      background: #0f172a;\n      border-bottom: 1px solid #1e293b;\n      padding: 5px 8px;\n      display: flex;\n      justify-content: space-between;\n      align-items: center;\n    }\n    .logs-screen {\n      flex: 1;\n      min-height: 0;\n      padding: 8px 10px;\n      overflow-y: auto;\n      font-family: monospace;\n      font-size: 0.7rem;\n      line-height: 1.38;\n      color: #cbd5e1;\n      white-space: pre-wrap;\n      word-break: break-all;\n      -webkit-overflow-scrolling: touch;\n    }\n    .filter-bar {\n      flex-shrink: 0;\n      display: flex;\n      gap: 5px;\n      padding: 5px 8px;\n      background: #0a0f1d;\n      border-bottom: 1px solid #1e293b;\n      overflow-x: auto;\n    }\n    .filter-btn {\n      flex-shrink: 0;\n      background: #1e293b;\n      border: 1px solid #334155;\n      color: var(--muted);\n      font-size: 0.65rem;\n      padding: 3px 7px;\n      border-radius: 4px;\n      cursor: pointer;\n    }\n    .filter-btn.active {\n      background: var(--accent);\n      color: #000;\n      font-weight: 700;\n      border-color: var(--accent);\n    }\n\n    /* AI Tab */\n    #pane-ai {\n      overflow: hidden;\n    }\n    .ai-card {\n      flex: 1;\n      min-height: 0;\n      background: var(--card-bg);\n      border: 1px solid var(--card-border);\n      border-radius: 8px;\n      display: flex;\n      flex-direction: column;\n      overflow: hidden;\n    }\n    .ai-messages {\n      flex: 1;\n      min-height: 0;\n      padding: 8px 10px;\n      overflow-y: auto;\n      display: flex;\n      flex-direction: column;\n      gap: 8px;\n      -webkit-overflow-scrolling: touch;\n    }\n    .ai-bubble {\n      max-width: 88%;\n      padding: 7px 10px;\n      border-radius: 10px;\n      font-size: 0.78rem;\n      line-height: 1.4;\n    }\n    .ai-bubble.user {\n      align-self: flex-end;\n      background: #0284c7;\n      color: #fff;\n      border-bottom-right-radius: 2px;\n    }\n    .ai-bubble.bot {\n      align-self: flex-start;\n      background: #1e293b;\n      color: #e2e8f0;\n      border: 1px solid #334155;\n      border-bottom-left-radius: 2px;\n    }\n    .ai-bubble.bot pre {\n      background: #020617;\n      padding: 5px;\n      border-radius: 4px;\n      margin: 5px 0;\n      overflow-x: auto;\n      font-family: monospace;\n      color: var(--primary);\n    }\n    .ai-bubble.bot code {\n      background: #0f172a;\n      padding: 1px 3px;\n      border-radius: 3px;\n      font-family: monospace;\n      color: var(--accent);\n    }\n\n    /* Bottom Nav */\n    .nav-bar {\n      flex-shrink: 0;\n      height: calc(52px + var(--safe-bottom));\n      padding-bottom: var(--safe-bottom);\n      background: rgba(12, 18, 30, 0.98);\n      backdrop-filter: blur(16px);\n      border-top: 1px solid var(--card-border);\n      display: flex;\n      justify-content: space-around;\n      align-items: center;\n      z-index: 50;\n    }\n    .nav-tab {\n      background: transparent;\n      border: none;\n      color: var(--muted);\n      display: flex;\n      flex-direction: column;\n      align-items: center;\n      gap: 2px;\n      font-size: 0.66rem;\n      font-weight: 600;\n      cursor: pointer;\n      width: 25%;\n      padding: 4px 0;\n    }\n    .nav-tab.active {\n      color: var(--primary);\n    }\n    .nav-tab-icon { font-size: 1.15rem; }\n  </style>\n</head>\n<body>\n\n  <!-- TOP HEADER -->\n  <div class=\"header\">\n    <div class=\"header-left\">\n      <div class=\"header-brand\">\n        <span>\u26a1 MY AGY AI</span>\n        <span class=\"header-badge\">PRO</span>\n      </div>\n    </div>\n    <div class=\"header-actions\">\n      <button class=\"ide-header-btn\" onclick=\"openAgyIde()\">\ud83c\udf0c IDE \u2197</button>\n      <div class=\"status-pill\" id=\"headerStatus\">\n        <div class=\"dot\"></div>\n        <span id=\"headerStatusText\">Connecting...</span>\n      </div>\n    </div>\n  </div>\n\n  <!-- VIEWPORT TABS -->\n  <div class=\"viewport-container\">\n\n    <!-- TAB 1: TERMINAL -->\n    <div class=\"tab-pane active\" id=\"pane-terminal\">\n      <div class=\"chip-bar\">\n        <div class=\"chip highlight\" onclick=\"openAgyIde()\">\ud83c\udf0c Cloud IDE \u2197</div>\n        <div class=\"chip\" onclick=\"runPreset('status')\">\ud83d\udcca status</div>\n        <div class=\"chip\" onclick=\"runPreset('ps aux | grep python')\">\u2699\ufe0f ps aux</div>\n        <div class=\"chip\" onclick=\"runPreset('tail -n 25 userbot.log')\">\ud83d\udcdc tail log</div>\n        <div class=\"chip\" onclick=\"runPreset('uptime')\">\u23f1\ufe0f uptime</div>\n        <div class=\"chip\" onclick=\"runPreset('free -h')\">\ud83d\udcbe free mem</div>\n        <div class=\"chip\" onclick=\"runPreset('check bnb')\">\ud83e\ude99 check bnb</div>\n        <div class=\"chip\" onclick=\"runPreset('backup')\">\ud83d\udcbe backup</div>\n      </div>\n\n      <div class=\"terminal-card\">\n        <div class=\"term-title-bar\">\n          <div class=\"term-dots\">\n            <div class=\"t-dot t-red\"></div>\n            <div class=\"t-dot t-yel\"></div>\n            <div class=\"t-dot t-grn\"></div>\n          </div>\n          <div class=\"term-hostname\">arif2743@192.46.208.170:~$</div>\n          <div class=\"term-actions\">\n            <button class=\"t-btn\" onclick=\"copyTerminal()\">\ud83d\udccb Copy</button>\n            <button class=\"t-btn\" onclick=\"clearTerminal()\">\ud83e\uddf9 Clear</button>\n          </div>\n        </div>\n\n        <div class=\"term-screen\" id=\"termScreen\">\n          <div class=\"term-info-line\">\u26a1 MY AGY AI Interactive Cloud Terminal</div>\n          <div class=\"term-info-line\">Connected to VPS Host (192.46.208.170) via Cloudflare Edge.</div>\n          <div class=\"term-info-line\">Tap any shortcut above or enter any Linux command below:</div>\n        </div>\n\n        <div class=\"term-input-row\">\n          <span class=\"term-prompt-symbol\">$</span>\n          <input type=\"text\" class=\"term-text-input\" id=\"cmdInput\" placeholder=\"Command (e.g. ps, uptime, tail log)...\" autocomplete=\"off\" autocorrect=\"off\" autocapitalize=\"off\" spellcheck=\"false\">\n          <button class=\"term-run-btn\" onclick=\"submitCmd()\">Run</button>\n        </div>\n      </div>\n    </div>\n\n    <!-- TAB 2: FLEET -->\n    <div class=\"tab-pane scrollable\" id=\"pane-fleet\">\n      <!-- FEATURED ANTIGRAVITY IDE CARD -->\n      <div class=\"featured-ide-card\">\n        <div>\n          <div class=\"featured-ide-title\">\ud83c\udf0c Antigravity Cloud Web IDE</div>\n          <div class=\"featured-ide-sub\">Live developer console, workspace & background tasks</div>\n        </div>\n        <button class=\"featured-ide-btn\" onclick=\"openAgyIde()\">Open IDE \u2197</button>\n      </div>\n\n      <div class=\"fleet-grid\">\n        <div class=\"stat-card\">\n          <div class=\"stat-card-title\">VPS Server Status</div>\n          <div class=\"stat-card-val\" id=\"cardVpsStatus\" style=\"color:var(--primary)\">Online</div>\n          <div class=\"stat-card-sub\" id=\"cardVpsPing\">Heartbeat synced</div>\n        </div>\n        <div class=\"stat-card\">\n          <div class=\"stat-card-title\">Connected Accounts</div>\n          <div class=\"stat-card-val\" id=\"cardAccsCount\">3 Accounts</div>\n          <div class=\"stat-card-sub\">Multi-Worker Active</div>\n        </div>\n        <div class=\"stat-card\">\n          <div class=\"stat-card-title\">ATF Holding</div>\n          <div class=\"stat-card-val\" id=\"cardAtfHolding\">2,237.25 ATF</div>\n          <div class=\"stat-card-sub\">Daily Auto-Compounding</div>\n        </div>\n        <div class=\"stat-card\">\n          <div class=\"stat-card-title\">Ads Watched Today</div>\n          <div class=\"stat-card-val\" id=\"cardAdsToday\">146 Ads</div>\n          <div class=\"stat-card-sub\">Tier-1 US Emulation</div>\n        </div>\n      </div>\n\n      <div class=\"section-title\">\ud83d\udc65 Active Account Roster</div>\n      <div class=\"account-roster\" id=\"rosterList\">\n        <div class=\"account-row\">\n          <div class=\"account-info\">\n            <span class=\"acc-name\">Arif Hossain</span>\n            <span class=\"acc-meta\">@Arif2743aaa \u2022 ID: 6727787768</span>\n          </div>\n          <span class=\"acc-badge\">\ud83d\udc51 Master (Online)</span>\n        </div>\n        <div class=\"account-row\">\n          <div class=\"account-info\">\n            <span class=\"acc-name\">Nancy</span>\n            <span class=\"acc-meta\">Worker \u2022 ID: 8881914294</span>\n          </div>\n          <span class=\"acc-badge\">\u26a1 Worker (Active)</span>\n        </div>\n        <div class=\"account-row\">\n          <div class=\"account-info\">\n            <span class=\"acc-name\">Koram Shah</span>\n            <span class=\"acc-meta\">@Ksaaaks \u2022 ID: 7648254021</span>\n          </div>\n          <span class=\"acc-badge\">\u26a1 Worker (Active)</span>\n        </div>\n      </div>\n\n      <div class=\"section-title\">\u26a1 Instant Operations</div>\n      <div class=\"action-grid\">\n        <button class=\"fleet-btn success\" id=\"btnBnbWithdraw\" onclick=\"triggerAction('check bnb', this, 'Checking BNB...')\">\ud83d\udcb0 Auto-Withdraw BNB</button>\n        <button class=\"fleet-btn primary\" id=\"btnCloudBackup\" onclick=\"triggerAction('backup', this, 'Backing up...')\">\ud83d\udcbe Push Cloud Backup</button>\n        <button class=\"fleet-btn\" onclick=\"runPreset('tail -n 30 userbot.log')\">\ud83d\udcdc Tail userbot.log</button>\n        <button class=\"fleet-btn\" onclick=\"runPreset('./cloudflared_tunnel.sh status')\">\ud83d\udee1\ufe0f Tunnel Status</button>\n      </div>\n\n      <div class=\"section-title\">\ud83c\udf10 1-Line Disaster Recovery</div>\n      <div style=\"background:var(--card-bg); border:1px solid var(--card-border); border-radius:8px; padding:10px; font-size:0.75rem;\">\n        <div style=\"color:var(--muted); margin-bottom:6px;\">Run this command on Termux or any VPS to restore all bots in 40 seconds:</div>\n        <div style=\"display:flex; gap:6px; align-items:center;\">\n          <code style=\"flex:1; background:#020617; padding:6px 8px; border-radius:4px; color:var(--accent); font-family:monospace; word-break:break-all;\">curl -sSL https://restore-agy.aaa-bot.workers.dev | bash</code>\n          <button class=\"t-btn\" style=\"padding:6px 10px;\" onclick=\"copyRestoreCmd()\">Copy</button>\n        </div>\n      </div>\n    </div>\n\n    <!-- TAB 3: LOGS -->\n    <div class=\"tab-pane\" id=\"pane-logs\">\n      <div class=\"logs-card\">\n        <div class=\"logs-header\">\n          <span style=\"font-size:0.75rem; font-weight:700; color:var(--accent)\">\ud83d\udcdc userbot.log</span>\n          <div style=\"display:flex; gap:6px;\">\n            <button class=\"t-btn\" id=\"streamToggleBtn\" onclick=\"toggleLogStream()\">\ud83d\udfe2 Live (3s)</button>\n            <button class=\"t-btn\" onclick=\"copyLogs()\">\ud83d\udccb Copy</button>\n            <button class=\"t-btn\" onclick=\"fetchLogsNow()\">\ud83d\udd04</button>\n          </div>\n        </div>\n\n        <div class=\"filter-bar\">\n          <button class=\"filter-btn active\" onclick=\"setLogFilter('all', this)\">All</button>\n          <button class=\"filter-btn\" onclick=\"setLogFilter('BNB', this)\">BNB Galaxy</button>\n          <button class=\"filter-btn\" onclick=\"setLogFilter('ATF', this)\">ATF Miner</button>\n          <button class=\"filter-btn\" onclick=\"setLogFilter('Verifier', this)\">Verifier</button>\n          <button class=\"filter-btn\" onclick=\"setLogFilter('ERROR', this)\">Errors</button>\n        </div>\n\n        <div class=\"logs-screen\" id=\"logsScreen\">Loading real-time logs from VPS...</div>\n      </div>\n    </div>\n\n    <!-- TAB 4: AI CHAT -->\n    <div class=\"tab-pane\" id=\"pane-ai\">\n      <div class=\"ai-card\">\n        <div class=\"logs-header\">\n          <span style=\"font-size:0.75rem; font-weight:700; color:var(--primary)\">\ud83e\udd16 Cloudflare Edge AI (Llama 3.2)</span>\n          <button class=\"t-btn\" onclick=\"clearAiChat()\">\ud83e\uddf9 Clear</button>\n        </div>\n\n        <div class=\"ai-messages\" id=\"aiMessages\">\n          <div class=\"ai-bubble bot\">\n            \ud83d\udc4b <b>Hi Arif!</b> I am your serverless Cloudflare Edge Assistant. Ask me anything about your bot fleet, BNB auto-withdrawals, ATF ad tasks, or Linux VPS commands!\n          </div>\n        </div>\n\n        <div class=\"term-input-row\" style=\"background:#0f172a;\">\n          <input type=\"text\" class=\"term-text-input\" id=\"aiInput\" placeholder=\"Ask AI about your bots...\" autocomplete=\"off\">\n          <button class=\"term-run-btn\" onclick=\"sendAiMsg()\">Send</button>\n        </div>\n      </div>\n    </div>\n\n  </div>\n\n  <!-- BOTTOM NAVIGATION -->\n  <div class=\"nav-bar\">\n    <button class=\"nav-tab active\" id=\"navTab-terminal\" onclick=\"switchTab('terminal')\">\n      <span class=\"nav-tab-icon\">\ud83d\udcbb</span>\n      <span>Terminal</span>\n    </button>\n    <button class=\"nav-tab\" id=\"navTab-fleet\" onclick=\"switchTab('fleet')\">\n      <span class=\"nav-tab-icon\">\ud83d\udcca</span>\n      <span>Fleet</span>\n    </button>\n    <button class=\"nav-tab\" id=\"navTab-logs\" onclick=\"switchTab('logs')\">\n      <span class=\"nav-tab-icon\">\ud83d\udcdc</span>\n      <span>Logs</span>\n    </button>\n    <button class=\"nav-tab\" id=\"navTab-ai\" onclick=\"switchTab('ai')\">\n      <span class=\"nav-tab-icon\">\ud83e\udd16</span>\n      <span>AI Chat</span>\n    </button>\n  </div>\n\n  <!-- JAVASCRIPT LOGIC -->\n  <script>\n    const tg = window.Telegram?.WebApp;\n    const AGY_IDE_URL = \"https://antigravity.google.com/u/8/r/8bf8fe6b-19b3-4963-a444-8d44de5cfd51-v2?p=c%2F39f8f911-3fb0-4128-a548-1591c0382185%3Fsection%3Ddefault-cli-project%26tab%3Dbgtask__39f8f911-3fb0-4128-a548-1591c0382185%252Ftask-2555\";\n\n    if (tg) {\n      tg.ready();\n      tg.expand();\n      try {\n        if (tg.enableClosingConfirmation) tg.enableClosingConfirmation();\n        if (tg.setHeaderColor) tg.setHeaderColor('#070a12');\n        if (tg.setBackgroundColor) tg.setBackgroundColor('#070a12');\n      } catch(_) {}\n    }\n\n    // Handle viewport resize (mobile soft keyboards)\n    if (window.visualViewport) {\n      window.visualViewport.addEventListener('resize', () => {\n        document.body.style.height = window.visualViewport.height + 'px';\n        const screen = document.getElementById('termScreen');\n        if (screen && currentTab === 'terminal') screen.scrollTop = screen.scrollHeight;\n      });\n    }\n\n    function openAgyIde() {\n      haptic('success');\n      if (tg?.openLink) {\n        tg.openLink(AGY_IDE_URL);\n      } else {\n        window.open(AGY_IDE_URL, '_blank');\n      }\n    }\n\n    function haptic(type) {\n      try {\n        if (tg?.HapticFeedback) {\n          if (type === 'success') tg.HapticFeedback.notificationOccurred('success');\n          else tg.HapticFeedback.impactOccurred('light');\n        }\n      } catch(_) {}\n    }\n\n    let currentTab = 'terminal';\n    function switchTab(tabId) {\n      if (currentTab === tabId) return;\n      haptic();\n      currentTab = tabId;\n\n      document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));\n      document.querySelectorAll('.nav-tab').forEach(el => el.classList.remove('active'));\n\n      const pane = document.getElementById('pane-' + tabId);\n      const tabBtn = document.getElementById('navTab-' + tabId);\n      if (pane) pane.classList.add('active');\n      if (tabBtn) tabBtn.classList.add('active');\n\n      if (tg?.BackButton) {\n        if (tabId !== 'terminal') {\n          tg.BackButton.show();\n          tg.BackButton.onClick(() => switchTab('terminal'));\n        } else {\n          tg.BackButton.hide();\n        }\n      }\n\n      if (tabId === 'logs') {\n        fetchLogsNow();\n      }\n    }\n\n    // Enter Key Listeners\n    document.getElementById('cmdInput').addEventListener('keydown', function(e) {\n      if (e.key === 'Enter') submitCmd();\n    });\n    document.getElementById('aiInput').addEventListener('keydown', function(e) {\n      if (e.key === 'Enter') sendAiMsg();\n    });\n\n    // 1. FAST TERMINAL ENGINE WITH ASYNC POLLING\n    let activeCmdPollTimer = null;\n    async function submitCmd() {\n      const input = document.getElementById('cmdInput');\n      const cmd = input.value.trim();\n      if (!cmd) return;\n      input.value = '';\n      haptic();\n\n      const screen = document.getElementById('termScreen');\n      const pLine = document.createElement('div');\n      pLine.className = 'term-prompt-line';\n      pLine.textContent = '$ ' + cmd;\n      screen.appendChild(pLine);\n\n      const loadLine = document.createElement('div');\n      loadLine.className = 'term-loading-line';\n      loadLine.id = 'activeCmdLoading';\n      loadLine.textContent = '\u23f3 Executing on VPS... (0s)';\n      screen.appendChild(loadLine);\n      screen.scrollTop = screen.scrollHeight;\n\n      const startTime = Date.now();\n      let pollCount = 0;\n\n      try {\n        const resp = await fetch('/api/miniapp/exec', {\n          method: 'POST',\n          headers: { 'Content-Type': 'application/json' },\n          body: JSON.stringify({ command: cmd })\n        });\n        const data = await resp.json();\n\n        if (data.done) {\n          const l = document.getElementById('activeCmdLoading');\n          if (l) l.remove();\n          renderTermOutput(screen, data.output, data.exit_code);\n          return;\n        }\n\n        // If queued, poll /api/miniapp/check_result?id=... every 600ms\n        const cmdId = data.id;\n        if (!cmdId) {\n          const l = document.getElementById('activeCmdLoading');\n          if (l) l.remove();\n          renderTermOutput(screen, data.output || 'Command queued.');\n          return;\n        }\n\n        if (activeCmdPollTimer) clearInterval(activeCmdPollTimer);\n        activeCmdPollTimer = setInterval(async () => {\n          pollCount++;\n          const sec = Math.round((Date.now() - startTime) / 1000);\n          const l = document.getElementById('activeCmdLoading');\n          if (l) l.textContent = '\u23f3 Executing on VPS... (' + sec + 's)';\n\n          try {\n            const cResp = await fetch('/api/miniapp/check_result?id=' + encodeURIComponent(cmdId));\n            const cData = await cResp.json();\n            if (cData.done) {\n              clearInterval(activeCmdPollTimer);\n              activeCmdPollTimer = null;\n              const curL = document.getElementById('activeCmdLoading');\n              if (curL) curL.remove();\n              renderTermOutput(screen, cData.output, cData.exit_code);\n            } else if (pollCount > 35) {\n              clearInterval(activeCmdPollTimer);\n              activeCmdPollTimer = null;\n              const curL = document.getElementById('activeCmdLoading');\n              if (curL) {\n                curL.textContent = '\u26a0\ufe0f Command still executing on VPS in background. Check Live Logs tab.';\n                curL.className = 'term-info-line';\n              }\n            }\n          } catch (_) {}\n        }, 600);\n\n      } catch (err) {\n        const l = document.getElementById('activeCmdLoading');\n        if (l) l.remove();\n        const errLine = document.createElement('div');\n        errLine.className = 'term-error-line';\n        errLine.textContent = '\u274c Network Error: ' + err.message;\n        screen.appendChild(errLine);\n        screen.scrollTop = screen.scrollHeight;\n      }\n    }\n\n    function renderTermOutput(screen, text, exitCode) {\n      const outDiv = document.createElement('div');\n      outDiv.style.margin = '4px 0 10px 0';\n      outDiv.style.color = (exitCode && exitCode !== 0) ? '#fca5a5' : '#4ade80';\n      outDiv.textContent = text || '(No output)';\n      screen.appendChild(outDiv);\n      screen.scrollTop = screen.scrollHeight;\n    }\n\n    function runPreset(cmd) {\n      document.getElementById('cmdInput').value = cmd;\n      switchTab('terminal');\n      submitCmd();\n    }\n\n    function clearTerminal() {\n      haptic();\n      const screen = document.getElementById('termScreen');\n      screen.innerHTML = '<div class=\"term-info-line\">Terminal cleared. Ready for commands.</div>';\n    }\n\n    function copyTerminal() {\n      haptic('success');\n      const text = document.getElementById('termScreen').innerText;\n      navigator.clipboard.writeText(text);\n      if (tg?.showAlert) tg.showAlert('Terminal output copied to clipboard!');\n      else alert('Terminal output copied!');\n    }\n\n    // 2. FLEET & SENTINEL ENGINE\n    async function fetchFleetStatus() {\n      try {\n        const resp = await fetch('/api/miniapp/status');\n        const data = await resp.json();\n        const hb = data.heartbeat;\n        if (hb) {\n          const diffSec = Math.round((Date.now() - hb.last_seen) / 1000);\n          const hStatus = document.getElementById('headerStatus');\n          const hText = document.getElementById('headerStatusText');\n          const vpsCard = document.getElementById('cardVpsStatus');\n          const vpsPing = document.getElementById('cardVpsPing');\n\n          if (diffSec < 300) {\n            hStatus.className = 'status-pill';\n            hText.textContent = 'Online (' + diffSec + 's)';\n            vpsCard.textContent = 'Online';\n            vpsCard.style.color = 'var(--primary)';\n            vpsPing.textContent = 'Pinged ' + diffSec + 's ago';\n          } else {\n            hStatus.className = 'status-pill offline';\n            hText.textContent = 'Offline (' + Math.round(diffSec / 60) + 'm)';\n            vpsCard.textContent = 'Offline';\n            vpsCard.style.color = 'var(--danger)';\n            vpsPing.textContent = 'Last seen ' + Math.round(diffSec / 60) + 'm ago';\n          }\n\n          if (hb.data) {\n            const d = hb.data;\n            if (d.fleet_accounts !== undefined) {\n              document.getElementById('cardAccsCount').textContent = d.fleet_accounts + ' Accounts';\n            }\n            if (d.atf_holding !== undefined) {\n              document.getElementById('cardAtfHolding').textContent = d.atf_holding + ' ATF';\n            }\n            if (d.atf_ads_today !== undefined) {\n              document.getElementById('cardAdsToday').textContent = d.atf_ads_today + ' Ads';\n            }\n            if (d.accounts && Array.isArray(d.accounts) && d.accounts.length > 0) {\n              renderAccountRoster(d.accounts);\n            }\n          }\n        }\n      } catch (_) {}\n    }\n\n    function renderAccountRoster(accs) {\n      const list = document.getElementById('rosterList');\n      list.innerHTML = '';\n      accs.forEach(acc => {\n        const row = document.createElement('div');\n        row.className = 'account-row';\n        const isMaster = acc.role && acc.role.includes('Master');\n        row.innerHTML = '<div class=\"account-info\">' +\n          '<span class=\"acc-name\">' + escapeHtml(acc.name) + '</span>' +\n          '<span class=\"acc-meta\">' + escapeHtml(acc.username) + ' \u2022 ID: ' + escapeHtml(String(acc.user_id)) + '</span>' +\n          '</div>' +\n          '<span class=\"acc-badge\" style=\"' + (isMaster ? 'border-color:#38bdf8; color:#38bdf8;' : '') + '\">' +\n          escapeHtml(acc.role) + ' (Active)</span>';\n        list.appendChild(row);\n      });\n    }\n\n    async function triggerAction(cmd, btn, loadingMsg) {\n      haptic();\n      const origText = btn.textContent;\n      btn.textContent = '\u23f3 ' + loadingMsg;\n      btn.disabled = true;\n      try {\n        await fetch('/api/miniapp/exec', {\n          method: 'POST',\n          headers: { 'Content-Type': 'application/json' },\n          body: JSON.stringify({ command: cmd })\n        });\n        haptic('success');\n        btn.textContent = '\u2705 Done!';\n        setTimeout(() => {\n          btn.textContent = origText;\n          btn.disabled = false;\n        }, 2000);\n      } catch (e) {\n        btn.textContent = '\u274c Failed';\n        setTimeout(() => {\n          btn.textContent = origText;\n          btn.disabled = false;\n        }, 2000);\n      }\n    }\n\n    function copyRestoreCmd() {\n      haptic('success');\n      const cmd = 'curl -sSL https://restore-agy.aaa-bot.workers.dev | bash';\n      navigator.clipboard.writeText(cmd);\n      if (tg?.showAlert) tg.showAlert('1-Line Restore command copied to clipboard!');\n      else alert('Restore command copied!');\n    }\n\n    // 3. LOGS ENGINE\n    let rawLogContent = '';\n    let currentLogFilter = 'all';\n    let isLogStreaming = true;\n    let logStreamInterval = null;\n\n    async function fetchLogsNow() {\n      try {\n        const resp = await fetch('/api/miniapp/logs');\n        const data = await resp.json();\n        rawLogContent = data.logs || 'No logs found.';\n        applyLogFilter();\n      } catch (e) {\n        document.getElementById('logsScreen').textContent = 'Error loading logs: ' + e.message;\n      }\n    }\n\n    function setLogFilter(filter, btn) {\n      haptic();\n      currentLogFilter = filter;\n      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));\n      btn.classList.add('active');\n      applyLogFilter();\n    }\n\n    function applyLogFilter() {\n      const screen = document.getElementById('logsScreen');\n      if (!rawLogContent) {\n        screen.textContent = 'No logs available.';\n        return;\n      }\n      let lines = rawLogContent.split('\\n');\n      if (currentLogFilter !== 'all') {\n        const term = currentLogFilter.toUpperCase();\n        lines = lines.filter(l => l.toUpperCase().includes(term));\n      }\n      screen.textContent = lines.join('\\n') || '(No log lines matching filter \"' + currentLogFilter + '\")';\n      screen.scrollTop = screen.scrollHeight;\n    }\n\n    function toggleLogStream() {\n      haptic();\n      isLogStreaming = !isLogStreaming;\n      const btn = document.getElementById('streamToggleBtn');\n      if (isLogStreaming) {\n        btn.textContent = '\ud83d\udfe2 Live (3s)';\n        btn.style.color = 'var(--primary)';\n        startLogStreaming();\n      } else {\n        btn.textContent = '\u23f8\ufe0f Paused';\n        btn.style.color = 'var(--muted)';\n        if (logStreamInterval) clearInterval(logStreamInterval);\n      }\n    }\n\n    function startLogStreaming() {\n      if (logStreamInterval) clearInterval(logStreamInterval);\n      logStreamInterval = setInterval(() => {\n        if (currentTab === 'logs' && isLogStreaming) {\n          fetchLogsNow();\n        }\n      }, 3000);\n    }\n\n    function copyLogs() {\n      haptic('success');\n      navigator.clipboard.writeText(document.getElementById('logsScreen').innerText);\n      if (tg?.showAlert) tg.showAlert('Logs copied to clipboard!');\n      else alert('Logs copied!');\n    }\n\n    // 4. AI CHAT ENGINE\n    async function sendAiMsg() {\n      const input = document.getElementById('aiInput');\n      const q = input.value.trim();\n      if (!q) return;\n      input.value = '';\n      haptic();\n\n      const box = document.getElementById('aiMessages');\n      const uBubble = document.createElement('div');\n      uBubble.className = 'ai-bubble user';\n      uBubble.textContent = q;\n      box.appendChild(uBubble);\n\n      const bBubble = document.createElement('div');\n      bBubble.className = 'ai-bubble bot';\n      bBubble.id = 'aiThinkingBubble';\n      bBubble.innerHTML = '<i>Thinking via Cloudflare Llama 3.2...</i>';\n      box.appendChild(bBubble);\n      box.scrollTop = box.scrollHeight;\n\n      try {\n        const resp = await fetch('/ai', {\n          method: 'POST',\n          headers: { 'Content-Type': 'application/json' },\n          body: JSON.stringify({ prompt: q })\n        });\n        const data = await resp.json();\n        const curB = document.getElementById('aiThinkingBubble');\n        if (curB) {\n          curB.removeAttribute('id');\n          curB.innerHTML = formatMarkdown(data.answer || 'No answer generated.');\n        }\n      } catch (e) {\n        const curB = document.getElementById('aiThinkingBubble');\n        if (curB) {\n          curB.removeAttribute('id');\n          curB.innerHTML = '<span style=\"color:var(--danger)\">Error: ' + escapeHtml(e.message) + '</span>';\n        }\n      }\n      box.scrollTop = box.scrollHeight;\n    }\n\n    function clearAiChat() {\n      haptic();\n      const box = document.getElementById('aiMessages');\n      box.innerHTML = '<div class=\"ai-bubble bot\">Chat history cleared. How can I help you?</div>';\n    }\n\n    function formatMarkdown(str) {\n      let out = escapeHtml(str);\n      out = out.replace(/```([\\s\\S]*?)```/g, '<pre><code>$1</code></pre>');\n      out = out.replace(/`([^`]+)`/g, '<code>$1</code>');\n      out = out.replace(/\\*\\*([^*]+)\\*\\*/g, '<b>$1</b>');\n      out = out.replace(/\\n/g, '<br>');\n      return out;\n    }\n\n    function escapeHtml(str) {\n      return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\"/g, '&quot;');\n    }\n\n    // Startup Initializations\n    fetchFleetStatus();\n    setInterval(fetchFleetStatus, 4000);\n    startLogStreaming();\n  </script>\n</body>\n</html>";
