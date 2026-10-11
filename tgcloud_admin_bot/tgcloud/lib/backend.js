import { fetch } from 'sdk';
import { CONFIG } from './config.js';

export async function requestBackend(path, method = 'GET', body = null) {
  const urls = [...CONFIG.BACKEND_NODES, ...CONFIG.EDGE_MESH];
  for (const base of urls) {
    try {
      const url = `${base}${path.startsWith('/') ? '' : '/'}${path}`;
      const opts = {
        method,
        headers: {
          'Authorization': `Bearer ${CONFIG.SECRET_KEY}`,
          'Content-Type': 'application/json'
        }
      };
      if (body && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
        opts.body = JSON.stringify(body);
      }
      const res = await fetch(url, opts);
      if (res.ok) {
        return await res.json();
      }
    } catch (_) {
      // try next backend node
    }
  }
  return null;
}

export async function sendLoginCode(phone, chatId, accountIndex) {
  for (const base of CONFIG.BACKEND_NODES) {
    try {
      const res = await fetch(`${base}/api/account/login/send-code`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${CONFIG.SECRET_KEY}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          phone: String(phone).trim(),
          chat_id: String(chatId),
          secret: CONFIG.SECRET_KEY,
          index: accountIndex || null
        })
      });
      if (res.ok) {
        const data = await res.json();
        return { ...data, nodeUrl: base };
      }
    } catch (_) {}
  }
  return { ok: false, error: 'Could not connect to Render MTProto nodes. Please retry in a moment.' };
}

export async function verifyLoginCode({ chatId, code, password, phone, nodeUrl, index }) {
  const nodes = nodeUrl ? [nodeUrl, ...CONFIG.BACKEND_NODES.filter(u => u !== nodeUrl)] : CONFIG.BACKEND_NODES;
  for (const base of nodes) {
    try {
      const res = await fetch(`${base}/api/account/login/verify-code`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${CONFIG.SECRET_KEY}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          phone: phone || '',
          code: code || '',
          password: password || '',
          chat_id: String(chatId),
          secret: CONFIG.SECRET_KEY,
          index: index || null
        })
      });
      if (res.ok) {
        const data = await res.json();
        if (data.ok || data.need_2fa) {
          return data;
        }
        if (data.error && !data.error.includes('No active login session found')) {
          return data;
        }
      }
    } catch (_) {}
  }
  return { ok: false, error: 'Login verification failed on cloud cluster. Please try again.' };
}

export async function cancelLogin(chatId) {
  for (const base of CONFIG.BACKEND_NODES) {
    try {
      await fetch(`${base}/api/account/login/cancel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chat_id: String(chatId) })
      });
    } catch (_) {}
  }
}

export async function fetchFleetLive() {
  const res = await requestBackend('/api/fleet/live');
  return res || { accounts: [], healthy_count: 0, total_accounts: 0 };
}

export async function fetchOtpForAccount(accountIndex) {
  for (const base of CONFIG.BACKEND_NODES) {
    try {
      const res = await fetch(`${base}/api/account/otp?index=${accountIndex}`, {
        headers: { 'Authorization': `Bearer ${CONFIG.SECRET_KEY}` }
      });
      if (res.ok) {
        const d = await res.json();
        if (d.ok && d.code) return d;
      }
    } catch (_) {}
  }
  return null;
}
