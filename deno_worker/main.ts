// MY AGY AI - Autonomous Edge Sentinel & Mesh Synchronizer
// Deployed on Deno Deploy (V8 Edge Runtime)

const BOT_TOKEN = Deno.env.get("REPORT_BOT_TOKEN") || "8858823950:AAFFkuls8hBf23taCZE1y5gVzP4AFCuqI5o";
const CHAT_ID = Deno.env.get("REPORT_CHAT_ID") || "6727787768";

const NODES = [
  { name: "Render Singapore (Node 1)", url: "https://my-agy-fleet-standby.onrender.com/health", type: "render" },
  { name: "Render Frankfurt (Node 2)", url: "https://my-agy-fleet-standby-node2.onrender.com/health", type: "render" },
  { name: "Cloudflare Shard 0 (aaaai2)", url: "https://restore-agy.aaaai2.workers.dev/health", type: "cloudflare" },
  { name: "Cloudflare Shard 1 (aaa-bot)", url: "https://restore-agy.aaa-bot.workers.dev/health", type: "cloudflare" },
  { name: "Cloudflare Shard 2 (aaa222)", url: "https://restore-agy.aaa222.workers.dev/health", type: "cloudflare" }
];

// Open Deno KV for zero-latency edge state
let kv: Deno.Kv | null = null;
try {
  kv = await Deno.openKv();
} catch (e) {
  console.warn("Deno KV initialization note:", e);
}

async function probeNode(node: { name: string; url: string; type: string }) {
  const start = Date.now();
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 8000);
    const resp = await fetch(node.url, {
      method: "GET",
      headers: { "User-Agent": "AGY-Deno-Sentinel/1.0" },
      signal: controller.signal
    });
    clearTimeout(timeoutId);
    const latencyMs = Date.now() - start;
    return {
      name: node.name,
      url: node.url,
      type: node.type,
      status: resp.status === 200 ? "ONLINE" : `HTTP_${resp.status}`,
      statusCode: resp.status,
      latencyMs,
      ok: resp.ok
    };
  } catch (err: any) {
    return {
      name: node.name,
      url: node.url,
      type: node.type,
      status: err.name === "AbortError" ? "TIMEOUT" : "ERROR",
      error: err.message || "Connection failed",
      latencyMs: Date.now() - start,
      ok: false
    };
  }
}

async function runMeshProbe() {
  const results = await Promise.all(NODES.map(probeNode));
  const onlineCount = results.filter(r => r.ok).length;
  const healthScore = Math.round((onlineCount / NODES.length) * 100);

  if (kv) {
    try {
      await kv.set(["fleet", "last_probe"], {
        timestamp: new Date().toISOString(),
        onlineCount,
        totalNodes: NODES.length,
        healthScore,
        results
      });
    } catch (_) {}
  }

  return {
    timestamp: new Date().toISOString(),
    region: Deno.env.get("DENO_REGION") || "edge",
    healthScore: `${healthScore}%`,
    nodesOnline: `${onlineCount}/${NODES.length}`,
    nodes: results
  };
}

async function sendTelegramAlert(text: string) {
  try {
    const resp = await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        chat_id: CHAT_ID,
        text,
        parse_mode: "HTML"
      })
    });
    return await resp.json();
  } catch (e: any) {
    return { ok: false, error: e.message };
  }
}

// Built-in Autonomous Deno Cron: Runs every 10 minutes directly on Deno edge
try {
  Deno.cron("Fleet Mesh Heartbeat & Keepalive", "*/10 * * * *", async () => {
    console.log("[Deno.cron] Executing autonomous fleet keepalive & probe...");
    const probe = await runMeshProbe();
    console.log(`[Deno.cron] Probe complete: ${probe.nodesOnline} nodes online (${probe.healthScore})`);
  });
} catch (e) {
  console.warn("Deno.cron setup note:", e);
}

// HTTP Server
Deno.serve(async (req: Request) => {
  const url = new URL(req.url);
  const path = url.pathname;

  // 1. Health check
  if (path === "/health") {
    return new Response(JSON.stringify({
      status: "ONLINE",
      service: "MY AGY AI Deno Edge Sentinel",
      region: Deno.env.get("DENO_REGION") || "global",
      timestamp: new Date().toISOString()
    }), {
      headers: { "content-type": "application/json", "access-control-allow-origin": "*" }
    });
  }

  // 2. Full Live Mesh Status (Parallel probe to Render & Cloudflare)
  if (path === "/mesh-status") {
    const probe = await runMeshProbe();
    return new Response(JSON.stringify(probe, null, 2), {
      headers: { "content-type": "application/json", "access-control-allow-origin": "*" }
    });
  }

  // 3. Historical metrics from Deno KV
  if (path === "/stats") {
    let lastProbe = null;
    if (kv) {
      const entry = await kv.get(["fleet", "last_probe"]);
      lastProbe = entry.value;
    }
    return new Response(JSON.stringify({
      edge: "Deno Deploy",
      hasKv: !!kv,
      lastProbe
    }, null, 2), {
      headers: { "content-type": "application/json", "access-control-allow-origin": "*" }
    });
  }

  // 4. Dispatch Telegram Notification
  if (path === "/notify" && req.method === "POST") {
    try {
      const body = await req.json();
      const message = body.text || "⚠️ [MY AGY AI] Edge Alert Ping";
      const res = await sendTelegramAlert(message);
      return new Response(JSON.stringify(res), {
        headers: { "content-type": "application/json" }
      });
    } catch (e: any) {
      return new Response(JSON.stringify({ error: e.message }), { status: 400 });
    }
  }

  // Root endpoint: System Overview
  return new Response(JSON.stringify({
    service: "MY AGY AI Cloud Sentinel",
    runtime: "Deno Deploy v2 Edge",
    endpoints: {
      health: "/health",
      mesh_status: "/mesh-status",
      stats: "/stats",
      notify: "POST /notify"
    },
    fleet: {
      render_nodes: 2,
      cloudflare_shards: 3,
      deno_edge_nodes: 2
    },
    status: "ALL_SYSTEMS_ACTIVE"
  }, null, 2), {
    headers: { "content-type": "application/json", "access-control-allow-origin": "*" }
  });
});
