// tgcloud/lib/fleetApi.js — Cloud Mesh Interop Client
import { fetch } from 'sdk';
import { CF_WORKER_URLS, RENDER_NODES, UPSTASH_URL, UPSTASH_TOKEN, SECRET_KEY, BROWSER_HEADERS } from './config.js';

export async function fetchFleetStatus() {
  for (const cfUrl of CF_WORKER_URLS) {
    try {
      const resp = await fetch(`${cfUrl}/api/farm/status`, {
        method: 'GET',
        headers: {
          ...BROWSER_HEADERS,
          'Authorization': `Bearer ${SECRET_KEY}`
        }
      });
      if (resp.ok) {
        return await resp.json();
      }
    } catch (_) {}
  }

  for (const rNode of RENDER_NODES) {
    try {
      const resp = await fetch(`${rNode}/api/farm/status`, {
        method: 'GET',
        headers: {
          ...BROWSER_HEADERS,
          'Authorization': `Bearer ${SECRET_KEY}`
        }
      });
      if (resp.ok) {
        return await resp.json();
      }
    } catch (_) {}
  }

  return { ok: false, error: 'All mesh nodes unreachable' };
}

export async function triggerFarmSweep(bot = 'all') {
  const dispatched = [];
  for (const cfUrl of CF_WORKER_URLS) {
    try {
      const resp = await fetch(`${cfUrl}/api/farm/all`, {
        method: 'POST',
        headers: {
          ...BROWSER_HEADERS,
          'Authorization': `Bearer ${SECRET_KEY}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ all: true, bot })
      });
      if (resp.ok) {
        dispatched.push(cfUrl);
      }
    } catch (_) {}
  }

  for (const rNode of RENDER_NODES) {
    try {
      const resp = await fetch(`${rNode}/api/farm/cloud-all`, {
        method: 'POST',
        headers: {
          ...BROWSER_HEADERS,
          'Authorization': `Bearer ${SECRET_KEY}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ all: true, bot })
      });
      if (resp.ok) {
        dispatched.push(rNode);
      }
    } catch (_) {}
  }

  return { ok: dispatched.length > 0, nodes_triggered: dispatched.length };
}

export async function fetchWallets() {
  try {
    const resp = await fetch(`${UPSTASH_URL}/get/fleet:wallets:ton`, {
      headers: {
        'Authorization': `Bearer ${UPSTASH_TOKEN}`
      }
    });
    if (resp.ok) {
      const data = await resp.json();
      const res = data.result;
      if (res) {
        return typeof res === 'string' ? JSON.parse(res) : res;
      }
    }
  } catch (_) {}
  return {};
}
