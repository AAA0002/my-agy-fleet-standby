// tgcloud/endpoints/getOtp.js — Mini App API for 1-tap OTP retrieval
import { fetchOtpForAccount } from '../lib/backend.js';

export default async function (input, ctx) {
  const accountIndex = parseInt(input?.accountIndex || input?.idx || 1, 10);
  const otpData = await fetchOtpForAccount(accountIndex);

  if (otpData && otpData.code) {
    return {
      ok: true,
      found: true,
      account_index: accountIndex,
      code: String(otpData.code).trim(),
      raw: otpData,
      timestamp: Date.now()
    };
  }

  return {
    ok: true,
    found: false,
    account_index: accountIndex,
    message: otpData?.message || 'No active Telegram verification code found in the last 15 minutes. Ensure an SMS/login code was requested for this node.',
    raw: otpData,
    timestamp: Date.now()
  };
}
