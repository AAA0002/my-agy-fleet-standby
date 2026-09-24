
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;

    // 1. Health check
    if (path === "/health") {
      return new Response(JSON.stringify({ ok: true, service: "MY AGY AI Edge Gateway", version: "3.0" }), {
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

      // Wait up to 5 seconds for response in KV
      let result = null;
      for (let i = 0; i < 25; i++) {
        await new Promise(r => setTimeout(r, 200));
        const resStr = await env.BACKUP_KV.get("vps_cmd_result_" + cmdId);
        if (resStr) {
          result = JSON.parse(resStr);
          await env.BACKUP_KV.delete("vps_cmd_result_" + cmdId);
          break;
        }
      }

      if (result) {
        return new Response(JSON.stringify({ ok: true, output: result.output, exit_code: result.exit_code }), {
          headers: { "Content-Type": "application/json" }
        });
      } else {
        return new Response(JSON.stringify({
          ok: true,
          output: `[Command queued to VPS] ID: ${cmdId}\nExecuting in background... If VPS is connected, output will appear in Live Logs.`,
          queued: true
        }), {
          headers: { "Content-Type": "application/json" }
        });
      }
    }

    // 7. MiniApp & Terminal: Poll Pending Command (Used by VPS)
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

    // 8. MiniApp & Terminal: Submit Command Result (Used by VPS)
    if (path === "/api/miniapp/submit_result" && request.method === "POST") {
      const auth = request.headers.get("Authorization");
      if (auth !== `Bearer ${env.SECRET_KEY}`) {
        return new Response(JSON.stringify({ ok: false, error: "Unauthorized" }), { status: 401 });
      }

      const resBody = await request.json().catch(() => ({}));
      const cmdId = resBody.id;
      if (cmdId) {
        await env.BACKUP_KV.put("vps_cmd_result_" + cmdId, JSON.stringify(resBody), { expirationTtl: 120 });
      }
      return new Response(JSON.stringify({ ok: true }), { headers: { "Content-Type": "application/json" } });
    }

    // 9. MiniApp & Terminal: Push Logs & Get Logs
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

    // 10. Workers AI endpoint
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
        const aiRes = await env.AI.run("@cf/meta/llama-3.2-3b-instruct", { prompt: prompt, max_tokens: 300 });
        const ansText = aiRes.response || (aiRes.choices && aiRes.choices[0] ? aiRes.choices[0].text : JSON.stringify(aiRes));
        return new Response(JSON.stringify({ ok: true, answer: ansText.trim() }), {
          headers: { "Content-Type": "application/json" }
        });
      } catch (err) {
        return new Response(JSON.stringify({ ok: false, error: err.message }), { status: 500 });
      }
    }

    // 11. TELEGRAM BOT MINI APP & INTERACTIVE WEB TERMINAL
    if (path === "/app" || path === "/miniapp" || path === "/terminal" || path === "/status" || path === "/dashboard") {
      const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>MY AGY AI — Cloud Terminal & Operations Console</title>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <style>
    :root {
      --bg: #090d16;
      --card-bg: #111827;
      --card-border: #1f2937;
      --primary: #00ff9d;
      --accent: #38bdf8;
      --text: #f3f4f6;
      --muted: #9ca3af;
      --danger: #ef4444;
      --term-bg: #030712;
      --term-text: #4ade80;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body { background: var(--bg); color: var(--text); padding-bottom: 70px; min-height: 100vh; }
    
    /* Header */
    .header {
      background: rgba(17, 24, 39, 0.95);
      backdrop-filter: blur(10px);
      padding: 12px 16px;
      border-bottom: 1px solid var(--card-border);
      display: flex;
      justify-content: space-between;
      align-items: center;
      position: sticky;
      top: 0;
      z-index: 100;
    }
    .header-title { font-size: 1rem; font-weight: 700; color: var(--accent); display: flex; align-items: center; gap: 8px; }
    .status-pill {
      font-size: 0.75rem;
      padding: 3px 10px;
      border-radius: 999px;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .status-pill.online { background: rgba(0, 255, 157, 0.15); color: var(--primary); border: 1px solid rgba(0, 255, 157, 0.3); }
    .status-pill.offline { background: rgba(239, 68, 68, 0.15); color: var(--danger); border: 1px solid rgba(239, 68, 68, 0.3); }
    .dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }

    /* Content & Tabs */
    .container { padding: 14px; max-width: 800px; margin: 0 auto; }
    .tab-content { display: none; }
    .tab-content.active { display: block; }

    /* Terminal View */
    .term-window {
      background: var(--term-bg);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      height: 480px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
    }
    .term-header {
      background: #111827;
      padding: 8px 12px;
      display: flex;
      align-items: center;
      gap: 6px;
      border-bottom: 1px solid #1f2937;
    }
    .term-circle { width: 10px; height: 10px; border-radius: 50%; }
    .term-title { font-size: 0.75rem; color: var(--muted); margin-left: 8px; font-family: monospace; }
    .term-body {
      flex: 1;
      padding: 12px;
      overflow-y: auto;
      font-family: "Courier New", Courier, monospace;
      font-size: 0.8rem;
      color: var(--term-text);
      line-height: 1.4;
      white-space: pre-wrap;
      word-break: break-all;
    }
    .term-input-bar {
      display: flex;
      padding: 8px;
      background: #0f172a;
      border-top: 1px solid var(--card-border);
      gap: 8px;
    }
    .term-prompt { color: var(--accent); font-family: monospace; font-size: 0.85rem; align-self: center; padding-left: 4px; }
    .term-input {
      flex: 1;
      background: transparent;
      border: none;
      outline: none;
      color: #fff;
      font-family: monospace;
      font-size: 0.85rem;
    }
    .term-btn {
      background: var(--primary);
      color: #000;
      border: none;
      border-radius: 6px;
      padding: 6px 14px;
      font-size: 0.8rem;
      font-weight: 700;
      cursor: pointer;
    }

    /* Quick Action Chips */
    .chips-container { display: flex; gap: 8px; overflow-x: auto; padding: 10px 0 14px 0; -webkit-overflow-scrolling: touch; }
    .chip {
      background: #1f2937;
      color: var(--text);
      border: 1px solid #374151;
      border-radius: 20px;
      padding: 6px 12px;
      font-size: 0.75rem;
      font-family: monospace;
      white-space: nowrap;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 4px;
    }
    .chip:hover { border-color: var(--accent); color: var(--accent); }

    /* Fleet Cards */
    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 16px;
      margin-bottom: 12px;
    }
    .card h2 { font-size: 0.95rem; color: var(--accent); margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }
    .stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .stat-item { background: #0f172a; padding: 10px; border-radius: 8px; border: 1px solid #1e293b; }
    .stat-label { font-size: 0.7rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; }
    .stat-val { font-size: 1.05rem; font-weight: 700; color: #fff; margin-top: 4px; }

    /* Action Buttons */
    .btn-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 14px; }
    .action-btn {
      background: #1e293b;
      border: 1px solid #334155;
      color: #fff;
      padding: 12px;
      border-radius: 8px;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
    }
    .action-btn.primary { background: linear-gradient(135deg, #0284c7, #0369a1); border: none; }
    .action-btn.success { background: linear-gradient(135deg, #059669, #047857); border: none; }

    /* Bottom Navigation */
    .nav-bar {
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      height: 60px;
      background: rgba(17, 24, 39, 0.98);
      backdrop-filter: blur(12px);
      border-top: 1px solid var(--card-border);
      display: flex;
      justify-content: space-around;
      align-items: center;
      z-index: 100;
    }
    .nav-btn {
      background: transparent;
      border: none;
      color: var(--muted);
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;
      font-size: 0.7rem;
      font-weight: 600;
      cursor: pointer;
      width: 25%;
    }
    .nav-btn.active { color: var(--primary); }
    .nav-icon { font-size: 1.15rem; }
  </style>
</head>
<body>

  <div class="header">
    <div class="header-title">⚡ MY AGY AI Console</div>
    <div class="status-pill online" id="topStatus">
      <div class="dot"></div>
      <span id="topStatusText">Connecting...</span>
    </div>
  </div>

  <div class="container">
    <!-- TAB 1: TERMINAL CONSOLE -->
    <div class="tab-content active" id="tab-terminal">
      <div class="chips-container">
        <div class="chip" onclick="runPreset('status')">📊 status</div>
        <div class="chip" onclick="runPreset('ps aux | grep python')">⚙️ ps aux</div>
        <div class="chip" onclick="runPreset('tail -n 25 userbot.log')">📜 tail log</div>
        <div class="chip" onclick="runPreset('uptime')">⏱️ uptime</div>
        <div class="chip" onclick="runPreset('free -h')">💾 free mem</div>
        <div class="chip" onclick="runPreset('curl -s https://restore-agy.aaa-bot.workers.dev/status')">🌐 edge check</div>
      </div>

      <div class="term-window">
        <div class="term-header">
          <div class="term-circle" style="background:#ef4444"></div>
          <div class="term-circle" style="background:#eab308"></div>
          <div class="term-circle" style="background:#22c55e"></div>
          <div class="term-title">arif2743@192.46.208.170 — bash</div>
        </div>
        <div class="term-body" id="termOutput">⚡ MY AGY AI Interactive Cloud Terminal Initialized.
Connected to VPS Host (192.46.208.170) via Cloudflare Edge.
Type any Linux command below or tap a quick chip above.
</div>
        <div class="term-input-bar">
          <span class="term-prompt">$</span>
          <input type="text" class="term-input" id="cmdInput" placeholder="Type command (e.g. ps, uptime, tail log)..." autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false">
          <button class="term-btn" onclick="executeCmd()">Run</button>
        </div>
      </div>
    </div>

    <!-- TAB 2: FLEET OPERATIONS -->
    <div class="tab-content" id="tab-fleet">
      <div class="card">
        <h2>🖥️ VPS Fleet Sentinel</h2>
        <div class="stat-grid">
          <div class="stat-item">
            <div class="stat-label">VPS Status</div>
            <div class="stat-val" id="statVps" style="color:var(--primary)">Online</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">Active Accounts</div>
            <div class="stat-val" id="statAccs">3 Accounts</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">ATF Holding</div>
            <div class="stat-val" id="statAtf">2,223.23 ATF</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">Ads Watched Today</div>
            <div class="stat-val" id="statAds">146 Ads</div>
          </div>
        </div>

        <div class="btn-grid">
          <button class="action-btn success" onclick="runPreset('check bnb')">💰 Auto-Withdraw BNB</button>
          <button class="action-btn primary" onclick="runPreset('backup')">💾 Push Cloud Backup</button>
          <button class="action-btn" onclick="runPreset('tail -n 25 userbot.log')">📜 Inspect Logs</button>
          <button class="action-btn" onclick="runPreset('./cloudflared_tunnel.sh status')">🛡️ Tunnel Status</button>
        </div>
      </div>

      <div class="card">
        <h2>⚡ 1-Click Disaster Recovery</h2>
        <p style="font-size:0.8rem; color:var(--muted); line-height:1.4; margin-bottom:10px;">
          Run this single command on Android Termux or any new Linux VPS to restore full fleet in 40s:
        </p>
        <code style="background:#020617; padding:8px 12px; border-radius:6px; display:block; font-size:0.75rem; color:var(--accent); word-break:break-all;">
          curl -sSL https://restore-agy.aaa-bot.workers.dev | bash
        </code>
      </div>
    </div>

    <!-- TAB 3: LIVE LOGS STREAM -->
    <div class="tab-content" id="tab-logs">
      <div class="card" style="height:520px; display:flex; flex-direction:column;">
        <h2>📜 userbot.log — Live Tail</h2>
        <div style="flex:1; background:#020617; border-radius:8px; padding:10px; overflow-y:auto; font-family:monospace; font-size:0.75rem; color:#cbd5e1; white-space:pre-wrap;" id="logBox">
Loading live logs from Cloudflare Edge...
        </div>
        <button class="action-btn" style="margin-top:10px;" onclick="fetchLogs()">🔄 Refresh Logs</button>
      </div>
    </div>

    <!-- TAB 4: EDGE AI CHAT -->
    <div class="tab-content" id="tab-ai">
      <div class="card" style="height:520px; display:flex; flex-direction:column;">
        <h2>🤖 Cloudflare Workers AI (Llama 3.2)</h2>
        <div style="flex:1; background:#020617; border-radius:8px; padding:12px; overflow-y:auto; font-size:0.85rem; line-height:1.4;" id="aiChatBox">
          <div style="color:var(--muted); margin-bottom:8px;">💡 Ask anything about your bot fleet, Python scripts, or crypto mining optimization:</div>
        </div>
        <div style="display:flex; gap:8px; margin-top:10px;">
          <input type="text" id="aiInput" class="term-input" style="background:#1e293b; border:1px solid #334155; border-radius:6px; padding:8px;" placeholder="Ask AI anything...">
          <button class="term-btn" onclick="askAi()">Ask</button>
        </div>
      </div>
    </div>
  </div>

  <!-- BOTTOM NAVIGATION -->
  <div class="nav-bar">
    <button class="nav-btn active" onclick="switchTab('terminal')">
      <span class="nav-icon">💻</span>
      <span>Terminal</span>
    </button>
    <button class="nav-btn" onclick="switchTab('fleet')">
      <span class="nav-icon">📊</span>
      <span>Fleet</span>
    </button>
    <button class="nav-btn" onclick="switchTab('logs')">
      <span class="nav-icon">📜</span>
      <span>Logs</span>
    </button>
    <button class="nav-btn" onclick="switchTab('ai')">
      <span class="nav-icon">🤖</span>
      <span>AI Chat</span>
    </button>
  </div>

  <script>
    const tg = window.Telegram?.WebApp;
    if (tg) {
      tg.ready();
      tg.expand();
      try {
        tg.setHeaderColor('#090d16');
        tg.setBackgroundColor('#090d16');
      } catch(_) {}
    }

    function haptic() {
      if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('light');
    }

    function switchTab(tabId) {
      haptic();
      document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));
      document.getElementById('tab-' + tabId).classList.add('active');
      const idx = ['terminal', 'fleet', 'logs', 'ai'].indexOf(tabId);
      if (idx !== -1) document.querySelectorAll('.nav-btn')[idx].classList.add('active');
      if (tabId === 'logs') fetchLogs();
    }

    document.getElementById('cmdInput').addEventListener('keydown', function(e) {
      if (e.key === 'Enter') executeCmd();
    });
    document.getElementById('aiInput').addEventListener('keydown', function(e) {
      if (e.key === 'Enter') askAi();
    });

    async function executeCmd() {
      const input = document.getElementById('cmdInput');
      const cmd = input.value.trim();
      if (!cmd) return;
      input.value = '';
      haptic();

      const term = document.getElementById('termOutput');
      term.textContent += `\n$ ${cmd}\n⏳ Executing on VPS...`;
      term.scrollTop = term.scrollHeight;

      try {
        const resp = await fetch('/api/miniapp/exec', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ command: cmd })
        });
        const data = await resp.json();
        term.textContent += `\n${data.output || 'No output'}\n`;
      } catch (err) {
        term.textContent += `\n❌ Error: ${err.message}\n`;
      }
      term.scrollTop = term.scrollHeight;
    }

    function runPreset(cmd) {
      document.getElementById('cmdInput').value = cmd;
      switchTab('terminal');
      executeCmd();
    }

    async function fetchStatus() {
      try {
        const resp = await fetch('/api/miniapp/status');
        const data = await resp.json();
        const hb = data.heartbeat;
        if (hb) {
          const diffSec = Math.round((Date.now() - hb.last_seen) / 1000);
          if (diffSec < 360) {
            document.getElementById('topStatus').className = 'status-pill online';
            document.getElementById('topStatusText').textContent = 'VPS Online (' + diffSec + 's)';
            document.getElementById('statVps').textContent = 'Online (' + diffSec + 's)';
          } else {
            document.getElementById('topStatus').className = 'status-pill offline';
            document.getElementById('topStatusText').textContent = 'VPS Offline';
            document.getElementById('statVps').textContent = 'Offline';
          }
          if (hb.data) {
            if (hb.data.fleet_accounts) document.getElementById('statAccs').textContent = hb.data.fleet_accounts + ' Accounts';
            if (hb.data.atf_holding) document.getElementById('statAtf').textContent = hb.data.atf_holding + ' ATF';
            if (hb.data.atf_ads_today !== undefined) document.getElementById('statAds').textContent = hb.data.atf_ads_today + ' Ads';
          }
        }
      } catch (_) {}
    }

    async function fetchLogs() {
      try {
        const resp = await fetch('/api/miniapp/logs');
        const data = await resp.json();
        document.getElementById('logBox').textContent = data.logs || 'No logs found.';
      } catch (e) {
        document.getElementById('logBox').textContent = 'Error loading logs: ' + e.message;
      }
    }

    async function askAi() {
      const input = document.getElementById('aiInput');
      const q = input.value.trim();
      if (!q) return;
      input.value = '';
      haptic();

      const box = document.getElementById('aiChatBox');
      box.innerHTML += `<div style="margin-top:8px; color:var(--accent);"><b>You:</b> ${escapeHtml(q)}</div>`;
      box.innerHTML += `<div id="aiTemp" style="margin-top:4px; color:var(--muted);">Thinking via Cloudflare Llama 3.2...</div>`;
      box.scrollTop = box.scrollHeight;

      try {
        const resp = await fetch('/ai', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt: q })
        });
        const data = await resp.json();
        const temp = document.getElementById('aiTemp');
        if (temp) temp.remove();
        box.innerHTML += `<div style="margin-top:4px; color:var(--primary);"><b>AI:</b> ${escapeHtml(data.answer || 'No response')}</div>`;
      } catch (err) {
        const temp = document.getElementById('aiTemp');
        if (temp) temp.remove();
        box.innerHTML += `<div style="margin-top:4px; color:var(--danger);">Error: ${err.message}</div>`;
      }
      box.scrollTop = box.scrollHeight;
    }

    function escapeHtml(str) {
      return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    fetchStatus();
    setInterval(fetchStatus, 5000);
  </script>
</body>
</html>`;

      return new Response(html, {
        headers: { "Content-Type": "text/html; charset=utf-8" }
      });
    }

    return new Response("Not Found", { status: 404 });
  }
};
