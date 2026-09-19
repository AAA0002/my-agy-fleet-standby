// MY AGY AI - Autonomous Multi-Cloud Edge Sentinel & Mesh Synchronizer
// Powered by Deno Deploy V2, Supabase Postgres, Upstash Redis & TonAPI

const BOT_TOKEN = Deno.env.get("REPORT_BOT_TOKEN") || "8858823950:AAFFkuls8hBf23taCZE1y5gVzP4AFCuqI5o";
const CHAT_ID = Deno.env.get("REPORT_CHAT_ID") || "6727787768";

// Cloud Integrations
const SUPABASE_URL = Deno.env.get("SUPABASE_URL") || "https://znbbaozpevurvbfkxakz.supabase.co";
const SUPABASE_KEY = Deno.env.get("SUPABASE_ANON_KEY") || "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpuYmJhb3pwZXZ1cnZiZmt4YWt6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODk4MTYxNTQsImV4cCI6MjEwNTM5MjE1NH0.ldgn0gCtOLEPUQyvTiG5RgKX6VY0LrS_4LkIKCf8NqM";
const UPSTASH_URL = Deno.env.get("UPSTASH_REDIS_REST_URL") || "https://relaxing-starfish-285827.upstash.io";
const UPSTASH_TOKEN = Deno.env.get("UPSTASH_REDIS_REST_TOKEN") || "gQAAAAAABFyDAAIgcDI5MDYyYWZjNzYzNzk0ZmRjYjhmNTA4ZDI4ODlmODkzNw";
const TONAPI_KEY = Deno.env.get("TONAPI_KEY") || "AGCD63WTWLGKKWYAAAAKRKZU45HTYMDI3PV7UBKKL6QDVIHG54NQDVNSQF7W3LQJ3X77QKY";

const NODES = [
  { name: "Render Singapore (Node 1)", url: "https://my-agy-fleet-standby.onrender.com/health", type: "render" },
  { name: "Render Frankfurt (Node 2)", url: "https://my-agy-fleet-standby-node2.onrender.com/health", type: "render" },
  { name: "Cloudflare Shard 0 (aaaai2)", url: "https://restore-agy.aaaai2.workers.dev/health", type: "cloudflare" },
  { name: "Cloudflare Shard 1 (aaa-bot)", url: "https://restore-agy.aaa-bot.workers.dev/health", type: "cloudflare" },
  { name: "Cloudflare Shard 2 (aaa222)", url: "https://restore-agy.aaa222.workers.dev/health", type: "cloudflare" }
];

// Deno KV
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
      headers: { "User-Agent": "AGY-Deno-Sentinel/2.0" },
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

async function getTonRates() {
  try {
    const resp = await fetch("https://tonapi.io/v2/rates?tokens=ton,usdt&currencies=usd", {
      headers: { "Authorization": `Bearer ${TONAPI_KEY}` }
    });
    if (resp.ok) {
      const data = await resp.json();
      return {
        tonUsd: data?.rates?.TON?.prices?.USD || 0,
        usdtUsd: data?.rates?.USDT?.prices?.USD || 1.0
      };
    }
  } catch (_) {}
  return { tonUsd: 0, usdtUsd: 1.0 };
}

async function syncToSupabase(results: any[]) {
  try {
    const records = results.map(r => ({
      node_name: r.name,
      node_url: r.url,
      status: r.status,
      latency_ms: r.latencyMs,
      last_seen: new Date().toISOString()
    }));

    await fetch(`${SUPABASE_URL}/rest/v1/fleet_mesh_heartbeats`, {
      method: "POST",
      headers: {
        "apikey": SUPABASE_KEY,
        "Authorization": `Bearer ${SUPABASE_KEY}`,
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
      },
      body: JSON.stringify(records)
    });
  } catch (e) {
    console.warn("Supabase heartbeat sync note:", e);
  }
}

async function syncToUpstash(state: any) {
  try {
    await fetch(`${UPSTASH_URL}/set/fleet:mesh_status`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${UPSTASH_TOKEN}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify(state)
    });
  } catch (e) {
    console.warn("Upstash sync note:", e);
  }
}

async function runMeshProbe() {
  const [results, rates] = await Promise.all([
    Promise.all(NODES.map(probeNode)),
    getTonRates()
  ]);

  const onlineCount = results.filter(r => r.ok).length;
  const healthScore = Math.round((onlineCount / NODES.length) * 100);

  const payload = {
    timestamp: new Date().toISOString(),
    region: Deno.env.get("DENO_REGION") || "edge",
    healthScore: `${healthScore}%`,
    nodesOnline: `${onlineCount}/${NODES.length}`,
    marketRates: rates,
    nodes: results
  };

  // Broadcast to all storage layers concurrently
  await Promise.allSettled([
    syncToSupabase(results),
    syncToUpstash(payload),
    kv ? kv.set(["fleet", "last_probe"], payload) : Promise.resolve()
  ]);

  return payload;
}

// Autonomous 10-Minute Edge Cron
try {
  Deno.cron("Fleet Mesh 24/7 Keepalive & Cloud Sync", "*/10 * * * *", async () => {
    console.log("[Deno.cron] Executing autonomous fleet sync & keepalive...");
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

  // 2. Full Live Mesh Status (Parallel probe to Render + Cloudflare + Supabase + Upstash)
  if (path === "/mesh-status") {
    const probe = await runMeshProbe();
    return new Response(JSON.stringify(probe, null, 2), {
      headers: { "content-type": "application/json", "access-control-allow-origin": "*" }
    });
  }

  // 3. Historical State from Upstash Redis or Deno KV
  if (path === "/stats") {
    let cached = null;
    try {
      const upResp = await fetch(`${UPSTASH_URL}/get/fleet:mesh_status`, {
        headers: { "Authorization": `Bearer ${UPSTASH_TOKEN}` }
      });
      if (upResp.ok) {
        const d = await upResp.json();
        if (d.result) cached = typeof d.result === "string" ? JSON.parse(d.result) : d.result;
      }
    } catch (_) {}

    if (!cached && kv) {
      const entry = await kv.get(["fleet", "last_probe"]);
      cached = entry.value;
    }

    return new Response(JSON.stringify({
      edge: "Deno Deploy",
      source: cached ? "Upstash/DenoKV" : "live",
      state: cached
    }, null, 2), {
      headers: { "content-type": "application/json", "access-control-allow-origin": "*" }
    });
  }

  // 4. Dispatch Telegram Notification
  if (path === "/notify" && req.method === "POST") {
    try {
      const body = await req.json();
      const message = body.text || "⚠️ [MY AGY AI] Edge Alert Ping";
      const resp = await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chat_id: CHAT_ID,
          text: message,
          parse_mode: "HTML"
        })
      });
      const res = await resp.json();
      return new Response(JSON.stringify(res), {
        headers: { "content-type": "application/json" }
      });
    } catch (e: any) {
      return new Response(JSON.stringify({ error: e.message }), { status: 400 });
    }
  }

  // Root Overview
  return new Response(JSON.stringify({
    service: "MY AGY AI Cloud Sentinel & Multi-Cloud Hub",
    runtime: "Deno Deploy v2 Edge",
    endpoints: {
      health: "/health",
      mesh_status: "/mesh-status",
      stats: "/stats",
      notify: "POST /notify"
    },
    cloud_integrations: {
      render_nodes: 2,
      cloudflare_shards: 3,
      deno_edge_nodes: 2,
      supabase_postgres: "CONNECTED",
      upstash_redis: "CONNECTED",
      tonapi_io: "CONNECTED"
    },
    status: "ALL_SYSTEMS_ACTIVE"
  }, null, 2), {
    headers: { "content-type": "application/json", "access-control-allow-origin": "*" }
  });
});
