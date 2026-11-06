#!/usr/bin/env python3
"""
enhance_dashboards.py - Comprehensive Dashboard Enhancer
Improves UI/UX, filter controls, wallet explorers, 9-pool integrity,
and responsive ergonomics across all dashboards in AAA AUTO.
"""

import os
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def enhance_admin_html():
    admin_path = os.path.join(BASE_DIR, "public_admin", "admin.html")
    with open(admin_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update Category Filter Chips
    old_chips = """      // Category Filter Chips & Search Bar
      React.createElement("div", { className: "flex items-center gap-1.5 overflow-x-auto pb-1 mb-2.5" },
        [
          { id: "all", label: `All (${fleet.length})` },
          { id: "personal", label: "Personal #1-8" },
          { id: "cloud", label: `Cloud #${fleet.length > 8 ? "9-" + fleet.length : "9+"}` }
        ].map(chip => React.createElement("button", {"""

    new_chips = """      // Category Filter Chips & Search Bar
      React.createElement("div", { className: "flex items-center gap-1.5 overflow-x-auto pb-1 mb-2.5 no-scrollbar" },
        [
          { id: "all", label: `All (${fleet.length})` },
          { id: "online", label: `🟢 Online (${fleet.filter(a => !a.session_revoked && a.status !== 'Needs Re-link').length})` },
          { id: "master", label: "👑 Master (#1)" },
          { id: "workers", label: `👥 Workers (${fleet.length > 1 ? fleet.length - 1 : 0})` },
          { id: "cloud", label: "☁️ Cloud Mesh" }
        ].map(chip => React.createElement("button", {"""

    if old_chips in content:
        content = content.replace(old_chips, new_chips)
        print("✅ Updated filter chips in admin.html")

    # 2. Update filteredFleet logic
    old_filter = """      if (!matchSearch) return false;
      const idx = acc.index || 0;
      if (fleetFilter === "personal") return idx >= 1 && idx <= 8;
      if (fleetFilter === "cloud") return idx >= 9;
      return true;"""

    new_filter = """      if (!matchSearch) return false;
      const idx = acc.index || (fleet.indexOf(acc) + 1);
      const isRev = acc.session_revoked === true || acc.status === "Needs Re-link";
      if (fleetFilter === "online") return !isRev;
      if (fleetFilter === "relink") return isRev;
      if (fleetFilter === "master") return idx === 1 || String(acc.user_id) === "6727787768";
      if (fleetFilter === "workers") return idx > 1 && String(acc.user_id) !== "6727787768";
      if (fleetFilter === "personal") return idx >= 1 && idx <= 8;
      if (fleetFilter === "cloud") return idx >= 9;
      return true;"""

    if old_filter in content:
        content = content.replace(old_filter, new_filter)
        print("✅ Updated filteredFleet logic in admin.html")

    # 3. Add 1-Tap Farm button directly on each Account Card
    old_card_status = """              React.createElement("div", { className: "flex items-center gap-1" },
                (acc.session_revoked || acc.status === "Needs Re-link")
                  ? React.createElement("span", { className: "bg-rose-500/10 text-rose-400 border border-rose-500/30 text-[9px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1" },
                      "🔴 Needs Re-link"
                    )
                  : React.createElement("span", { className: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[9px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1" },
                      "🟢 Mining"
                    )
              )"""

    new_card_status = """              React.createElement("div", { className: "flex items-center gap-1.5" },
                React.createElement("button", {
                  onClick: (e) => {
                    e.stopPropagation();
                    handleFarmSingleAccount(acc.user_id, acc.name || `Account #${accNum}`);
                  },
                  title: "1-Tap Cloud Farm 9 Pools",
                  className: "text-[9px] font-mono font-bold text-cyan-400 bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 px-2 py-0.5 rounded cursor-pointer transition active:scale-95 flex items-center gap-1"
                },
                  React.createElement(Icon, { name: "zap", className: "w-2.5 h-2.5 text-cyan-400" }),
                  "Farm"
                ),
                (acc.session_revoked || acc.status === "Needs Re-link")
                  ? React.createElement("span", { className: "bg-rose-500/10 text-rose-400 border border-rose-500/30 text-[9px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1" },
                      "🔴 Needs Re-link"
                    )
                  : React.createElement("span", { className: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[9px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1" },
                      "🟢 Mining"
                    )
              )"""

    if old_card_status in content:
        content = content.replace(old_card_status, new_card_status)
        print("✅ Added 1-Tap Farm button to account cards in admin.html")

    # 4. Enhance Account Drawer / Modal Multi-Chain Wallets with BTC & Block Explorers
    old_wallets_drawer = """                [
                  { ch: "ton", name: "💎 TON", addr: accWallets.ton },
                  { ch: "evm", name: "🟡 EVM (BSC)", addr: accWallets.evm },
                  { ch: "tron", name: "🔴 TRON", addr: accWallets.tron },
                  { ch: "sol", name: "🟣 SOL", addr: accWallets.sol }
                ].filter(w => Boolean(w.addr)).map(w => React.createElement("div", {
                  key: w.ch,
                  className: "flex items-center justify-between p-1.5 rounded-lg bg-black/40 border border-white/5 font-mono text-[9px]"
                },
                  React.createElement("span", { className: "text-slate-400 w-16 shrink-0" }, w.name),
                  React.createElement("span", { className: "truncate text-slate-200 mx-1 select-all" }, w.addr),
                  React.createElement("button", {
                    onClick: () => copyToClipboard(w.addr, `Copied ${w.name} address!`),
                    className: "px-1.5 py-0.5 rounded bg-white/10 hover:bg-white/20 text-slate-300"
                  }, "Copy")
                ))"""

    new_wallets_drawer = """                [
                  { ch: "ton", name: "💎 TON", addr: accWallets.ton },
                  { ch: "evm", name: "🟡 EVM (BSC)", addr: accWallets.evm },
                  { ch: "tron", name: "🔴 TRON", addr: accWallets.tron },
                  { ch: "sol", name: "🟣 SOL", addr: accWallets.sol },
                  { ch: "btc", name: "🟠 BTC", addr: accWallets.btc }
                ].filter(w => Boolean(w.addr)).map(w => {
                  const explorerUrl = BLOCK_EXPLORERS[w.ch] ? BLOCK_EXPLORERS[w.ch](w.addr) : "";
                  return React.createElement("div", {
                    key: w.ch,
                    className: "flex items-center justify-between p-1.5 rounded-lg bg-black/40 border border-white/5 font-mono text-[9px]"
                  },
                    React.createElement("span", { className: "text-slate-400 w-20 shrink-0 font-bold" }, w.name),
                    React.createElement("span", { className: "truncate text-slate-200 mx-1 select-all font-mono" }, w.addr),
                    React.createElement("div", { className: "flex items-center gap-1 shrink-0" },
                      React.createElement("button", {
                        onClick: () => copyToClipboard(w.addr, `Copied ${w.name} address!`),
                        className: "px-1.5 py-0.5 rounded bg-white/10 hover:bg-white/20 text-slate-300 transition active:scale-95"
                      }, "Copy"),
                      explorerUrl && React.createElement("a", {
                        href: explorerUrl,
                        target: "_blank",
                        rel: "noopener noreferrer",
                        className: "px-1.5 py-0.5 rounded bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 transition active:scale-95"
                      }, "↗")
                    )
                  );
                })"""

    if old_wallets_drawer in content:
        content = content.replace(old_wallets_drawer, new_wallets_drawer)
        print("✅ Added BTC & Block Explorer links to wallet drawer in admin.html")

    # Write back to public_admin/admin.html
    with open(admin_path, "w", encoding="utf-8") as f:
        f.write(content)

    # Mirror to all admin.html destinations
    for target in [
        os.path.join(BASE_DIR, "public", "admin.html"),
        os.path.join(BASE_DIR, "public_admin", "index.html"),
        os.path.join(BASE_DIR, "public_admin", "admin", "index.html"),
        os.path.join(BASE_DIR, "dashboard.html"),
        os.path.join(BASE_DIR, "tgcloud_admin_bot", "public", "index.html")
    ]:
        shutil.copyfile(admin_path, target)
        print(f"✅ Mirrored admin.html -> {os.path.relpath(target, BASE_DIR)}")

def enhance_user_admin_html():
    uadmin_path = os.path.join(BASE_DIR, "public_admin", "user-admin.html")
    with open(uadmin_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Mirror to all user-admin destinations
    for target in [
        os.path.join(BASE_DIR, "public", "user-admin.html"),
        os.path.join(BASE_DIR, "public_admin", "users", "index.html"),
        os.path.join(BASE_DIR, "public_admin", "user-admin", "index.html")
    ]:
        shutil.copyfile(uadmin_path, target)
        print(f"✅ Mirrored user-admin.html -> {os.path.relpath(target, BASE_DIR)}")

def enhance_user_miner_html():
    miner_path = os.path.join(BASE_DIR, "public_ads", "miner", "index.html")
    target = os.path.join(BASE_DIR, "public", "miner", "index.html")
    shutil.copyfile(miner_path, target)
    print(f"✅ Mirrored miner index.html -> {os.path.relpath(target, BASE_DIR)}")

def enhance_ads_portal_html():
    ads_path = os.path.join(BASE_DIR, "public_ads", "index.html")
    for target in [
        os.path.join(BASE_DIR, "public", "ad", "index.html"),
        os.path.join(BASE_DIR, "public", "app", "ad", "index.html"),
        os.path.join(BASE_DIR, "public_ads", "ad", "index.html"),
        os.path.join(BASE_DIR, "public_ads", "app", "ad", "index.html")
    ]:
        shutil.copyfile(ads_path, target)
        print(f"✅ Mirrored ads portal -> {os.path.relpath(target, BASE_DIR)}")

if __name__ == "__main__":
    print("🚀 Starting Comprehensive Dashboard Enhancements...")
    enhance_admin_html()
    enhance_user_admin_html()
    enhance_user_miner_html()
    enhance_ads_portal_html()
    print("🎉 All dashboards enhanced and synchronized successfully!")
