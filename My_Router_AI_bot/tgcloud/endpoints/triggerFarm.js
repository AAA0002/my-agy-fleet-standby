// tgcloud/endpoints/triggerFarm.js — Mini App API for 1-click cloud harvest sweeps
import { triggerFarmSweep } from '../lib/fleetApi.js';

export default async function (input, ctx) {
  const botTarget = input?.bot || 'all';
  const res = await triggerFarmSweep(botTarget);

  return {
    ok: res.ok,
    nodes_triggered: res.nodes_triggered,
    target: botTarget,
    timestamp: Date.now()
  };
}
