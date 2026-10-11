// tgcloud/endpoints/getFleetStatus.js — Comprehensive Mini App API for live fleet telemetry
import { fetchFleetStatus, fetchWallets } from '../lib/fleetApi.js';
import { fetchFleetLive } from '../lib/backend.js';

export default async function (input, ctx) {
  const [statusData, wallets, liveData] = await Promise.allSettled([
    fetchFleetStatus(),
    fetchWallets(),
    fetchFleetLive()
  ]);

  return {
    ok: true,
    caller: ctx.initData?.user?.id || 'anonymous',
    fleet_status: statusData.status === 'fulfilled' ? statusData.value : null,
    wallets: wallets.status === 'fulfilled' ? wallets.value : {},
    fleet_live: liveData.status === 'fulfilled' ? liveData.value : null,
    timestamp: Date.now()
  };
}
