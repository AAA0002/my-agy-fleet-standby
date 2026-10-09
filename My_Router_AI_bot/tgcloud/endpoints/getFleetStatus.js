// tgcloud/endpoints/getFleetStatus.js — Mini App API for live fleet telemetry
import { fetchFleetStatus, fetchWallets } from '../lib/fleetApi.js';

export default async function (input, ctx) {
  const statusData = await fetchFleetStatus();
  const wallets = await fetchWallets();

  return {
    ok: true,
    caller: ctx.initData?.user?.id || 'anonymous',
    fleet_status: statusData,
    wallets: wallets,
    timestamp: Date.now()
  };
}
