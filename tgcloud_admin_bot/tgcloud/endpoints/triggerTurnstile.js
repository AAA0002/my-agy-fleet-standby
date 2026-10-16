// tgcloud/endpoints/triggerTurnstile.js — Triggers cloud Turnstile solver in GitHub Actions
import { fetch } from 'sdk';

const GH_TOKEN = (typeof process !== 'undefined' && process.env && process.env.GH_TOKEN) || "";
const REPO = "AAA0002/ATL";

export default async function (input, ctx) {
  try {
    const resp = await fetch(`https://api.github.com/repos/${REPO}/actions/workflows/mrg_turnstile_solver.yml/dispatches`, {
      method: 'POST',
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Authorization': `Bearer ${GH_TOKEN}`,
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ ref: 'main' })
    });

    return {
      ok: resp.status === 204,
      status: resp.status,
      timestamp: Date.now()
    };
  } catch (err) {
    return {
      ok: false,
      error: String(err),
      timestamp: Date.now()
    };
  }
}
