export function getMainMenuKeyboard() {
  return {
    inline_keyboard: [
      [
        { text: "📱 Fleet Accounts", callback_data: "btn_fleet_accounts" },
        { text: "➕ Add Account", callback_data: "btn_add_account" }
      ],
      [
        { text: "🔑 Get OTP Code", callback_data: "btn_otp_menu" },
        { text: "🔄 Re-link Account", callback_data: "btn_relink_menu" }
      ],
      [
        { text: "⚡ Farm All Bots", callback_data: "btn_farm_all" },
        { text: "📊 Fleet Telemetry", callback_data: "btn_system_status" }
      ],
      [
        { text: "💼 Multi-Chain Wallets", callback_data: "btn_wallets" },
        { text: "🛡️ Serverless Mesh", callback_data: "btn_mesh_status" }
      ]
    ]
  };
}

export function getCancelLoginKeyboard() {
  return {
    inline_keyboard: [
      [{ text: "❌ Cancel Login", callback_data: "btn_cancel_login" }]
    ]
  };
}

export function getBackToMenuKeyboard() {
  return {
    inline_keyboard: [
      [{ text: "🔙 Main Menu", callback_data: "btn_main_menu" }]
    ]
  };
}

export function buildAccountsKeyboard(accounts = [], actionPrefix = "btn_account_view_") {
  const rows = [];
  const chunkSize = 3;
  for (let i = 0; i < accounts.length; i += chunkSize) {
    const chunk = accounts.slice(i, i + chunkSize);
    rows.push(chunk.map((acc, cIdx) => {
      const idx = acc.index || (i + cIdx + 1);
      const isHost = String(acc.user_id) === "6727787768";
      const isRev = acc.status === "revoked" || acc.status === "inactive";
      const tag = isHost ? " 👑" : (isRev ? " 🔴" : " 🟢");
      const shortName = (acc.name || `Acc #${idx}`).split(" ")[0];
      return {
        text: `${idx}. ${shortName}${tag}`,
        callback_data: `${actionPrefix}${idx}`
      };
    }));
  }
  rows.push([{ text: "🔙 Main Menu", callback_data: "btn_main_menu" }]);
  return { inline_keyboard: rows };
}

export function buildOtpKeyboard(accounts = []) {
  return buildAccountsKeyboard(accounts, "btn_otp_get_");
}

export function buildRelinkKeyboard(accounts = []) {
  return buildAccountsKeyboard(accounts, "btn_relink_acc_");
}
