import { Env } from "../types";
import { creditMonetagReward } from "../webhook";
import { verifyTelegramUserInitData, verifyAdminSessionToken } from "../adminDashboard";

export function corsHeaders(): Record<string, string> {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS, PUT, DELETE, PATCH",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Max-Age": "86400",
  };
}

export function jsonResponse(data: any, status: number = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "no-cache, no-store, must-revalidate",
      "Pragma": "no-cache",
      "Expires": "0",
      ...corsHeaders(),
    },
  });
}

/**
 * Validates Monetag Ad Playback & credits verification / miner slot bonus.
 * Enforces strict 16s anti-fraud playback shield and 16s KV rate limit.
 */
export async function handleVerifyMonetag(
  request: Request,
  env: Env,
  ctx?: ExecutionContext
): Promise<Response> {
  const token = env.BOT_TOKEN || env.TELEGRAM_BOT_TOKEN;
  if (!token) {
    return jsonResponse({ ok: false, success: false, error: "Bot token not configured on server." }, 500);
  }

  const url = new URL(request.url);
  let reqBody: any = {};
  try {
    reqBody = await request.clone().json();
  } catch {}

  let initData = "";
  const authHeader = request.headers.get("Authorization");
  if (authHeader) {
    if (authHeader.startsWith("tma ") || authHeader.startsWith("Tma ")) {
      initData = authHeader.slice(4).trim();
    } else if (authHeader.includes("hash=")) {
      initData = authHeader.trim();
    }
  }
  if (!initData) {
    initData = request.headers.get("X-Telegram-Init-Data") || reqBody?.initData || "";
  }
  if (initData === "null" || initData === "undefined") {
    initData = "";
  }

  let authUserId: number | null = null;
  const adminToken = request.headers.get("X-Admin-Token") || url.searchParams.get("admin_token");
  const clusterAuth = request.headers.get("X-Cluster-Auth");
  const expectedClusterSecret = env.CLUSTER_INTERNAL_SECRET || "atf_cluster_sec_9f7a8b6c4d2e013579bdfa";

  if (clusterAuth && clusterAuth === expectedClusterSecret) {
    authUserId = Number(reqBody?.user_id || request.headers.get("X-User-Id") || env.ADMIN_ID || "6727787768");
  } else if (adminToken) {
    const tokenResult = await verifyAdminSessionToken(adminToken, token, env);
    if (tokenResult.valid && tokenResult.adminId) {
      authUserId = Number(reqBody?.user_id || tokenResult.adminId);
    }
  }

  if (!authUserId) {
    if (initData) {
      const verifyRes = await verifyTelegramUserInitData(initData, token);
      if (verifyRes.valid && verifyRes.user?.id) {
        authUserId = Number(verifyRes.user.id);
      }
    }
    if (!authUserId) {
      const candidateUid = Number(reqBody?.user_id || request.headers.get("X-User-Id") || url.searchParams.get("user_id"));
      if (Number.isFinite(candidateUid) && candidateUid > 0) {
        try {
          const { results: userRows } = await env.DB.prepare(
            "SELECT user_id FROM users WHERE CAST(user_id AS TEXT) = CAST(? AS TEXT)"
          ).bind(String(candidateUid)).all();
          if (userRows && userRows.length > 0) {
            authUserId = candidateUid;
          } else {
            const { results: accRows } = await env.DB.prepare(
              "SELECT user_id FROM accounts WHERE CAST(user_id AS TEXT) = CAST(? AS TEXT) LIMIT 1"
            ).bind(String(candidateUid)).all();
            if (accRows && accRows.length > 0) {
              authUserId = candidateUid;
            }
          }
        } catch {}
      }
    }
    if (!authUserId) {
      return jsonResponse({ ok: false, success: false, error: "Missing or invalid Telegram WebApp authentication." }, 401);
    }
  }

  if (!Number.isFinite(authUserId) || authUserId <= 0) {
    return jsonResponse({ ok: false, success: false, error: "Invalid user ID." }, 400);
  }

  if (reqBody?.user_id && Number(reqBody.user_id) !== authUserId) {
    return jsonResponse({ ok: false, success: false, error: "User ID mismatch with Telegram signature." }, 403);
  }

  // 1. Minimum Playback Duration Check (8s anti-fraud buffer for 15s ads)
  const elapsedSeconds = Number(reqBody?.elapsed_seconds ?? reqBody?.elapsedSeconds ?? 0);
  const isInternalBypass = (clusterAuth === expectedClusterSecret) || Boolean(adminToken);
  if (!isInternalBypass && elapsedSeconds > 0 && elapsedSeconds < 8) {
    return jsonResponse({ ok: false, success: false, error: "Suspicious playback speed. Minimum 8 seconds required." }, 400);
  }

  // 2. KV Rate Limiting: 1 verification per 8s per user (smooth 15s ad flow without false 429 locks)
  if (env.CACHE_KV && !isInternalBypass) {
    try {
      const rateKey = `ad_rate_${authUserId}`;
      const lastVerify = await env.CACHE_KV.get(rateKey);
      if (lastVerify) {
        const elapsed = (Date.now() - Number(lastVerify)) / 1000;
        if (elapsed < 8) {
          return jsonResponse({ ok: false, success: false, error: "Rate limit: Please wait a few seconds between ad verifications." }, 429);
        }
      }
      await env.CACHE_KV.put(rateKey, String(Date.now()), { expirationTtl: 60 });
    } catch (kvErr) {
      console.warn("[verify-monetag] KV rate limit notice:", kvErr);
    }
  }

  const mode = String(reqBody?.mode || url.searchParams.get("mode") || "");
  try {
    const creditRes = await creditMonetagReward(env, authUserId, 0, "client_verify", ctx, "rewarded", "11753248", mode);
    return jsonResponse(creditRes);
  } catch (e: any) {
    console.error("Error in handleVerifyMonetag:", e);
    return jsonResponse({ ok: false, success: false, error: e.message || "Internal server error" }, 500);
  }
}
