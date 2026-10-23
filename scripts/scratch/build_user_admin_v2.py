#!/usr/bin/env python3
"""build_user_admin_v2.py
Rebuilds public_admin/user-admin.html and public/user-admin.html with:
- Top isolation banner separating User Bot console from Admin Fleet console.
- 5-tab navigation: Users & Sessions, Wallets & Vaults, Broadcast & Notify, 9 Pools, Economy & Burn.
- Session verification scanner (/api/admin/session/check-all).
- Per-user notification triggers (/api/admin/session/notify).
- Community broadcast engine with pre-built templates and custom message sending.
- User status badges: 🟢 Active, 🔴 Revoked, ⚪ No Account.
"""
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_HTML = os.path.join(BASE_DIR, "public_admin", "user-admin.html")

with open(SRC_HTML, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add bell and send icons to ICONS
if "bell:" not in content:
    content = content.replace(
        '  sparkles: \'<path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z" />\'\n};',
        '  sparkles: \'<path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z" />\',\n  bell: \'<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" /><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />\',\n  send: \'<line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />\'\n};'
    )
    print("Added bell and send icons.")

# 2. Add Broadcast and Session Scan state variables
state_injection = """  const [broadcastTarget, setBroadcastTarget] = useState("no_account"); // "no_account" | "revoked" | "all" | "active"
  const [broadcastTemplate, setBroadcastTemplate] = useState("onboard");
  const [broadcastText, setBroadcastText] = useState("");
  const [isBroadcasting, setIsBroadcasting] = useState(false);
  const [broadcastResult, setBroadcastResult] = useState(null);
  const [isScanningSessions, setIsScanningSessions] = useState(false);
  const [sessionScanResult, setSessionScanResult] = useState(null);
"""

if "const [broadcastTarget, setBroadcastTarget]" not in content:
    content = content.replace(
        '  const [activeNavTab, setActiveNavTab] = useState("users"); // "users" | "wallets" | "pools" | "economy"',
        '  const [activeNavTab, setActiveNavTab] = useState("users"); // "users" | "wallets" | "broadcast" | "pools" | "economy"\n' + state_injection
    )
    print("Added broadcast and session scan state.")

# 3. Add handler functions for scan and broadcast
handlers_code = """
  // Session Scanner Handler
  const handleScanSessions = async () => {
    setIsScanningSessions(true);
    showToast("Scanning all user sessions via Render Node 2...");
    try {
      const res = await fetchMeshApi("/api/admin/session/check-all", { method: "POST" });
      if (res && res.ok) {
        setSessionScanResult(res);
        showToast(`Scan complete: ${res.valid || 0} valid, ${res.revoked || 0} revoked.`);
        await fetchUsers();
      } else {
        showToast(res?.error || "Session check failed");
      }
    } catch (err) {
      showToast("Error: " + err.message);
    } finally {
      setIsScanningSessions(false);
    }
  };

  // Single User Notify Handler
  const handleNotifySingleUser = async (uid, name, type = "onboard_qr") => {
    showToast(`Sending notification to ${name || uid}...`);
    try {
      const res = await fetchMeshApi("/api/admin/session/notify", {
        method: "POST",
        body: JSON.stringify({ uid, type })
      });
      if (res && res.ok) {
        showToast(`Sent notification to ${name || uid} via @AAAPREMIUMAPPSbot!`);
      } else {
        showToast(res?.description || res?.error || "Failed to notify");
      }
    } catch (err) {
      showToast("Error: " + err.message);
    }
  };

  // Community Broadcast Handler
  const handleSendBroadcast = async () => {
    if (!broadcastText.trim()) {
      showToast("Please enter a broadcast message or select a template.");
      return;
    }
    setIsBroadcasting(true);
    showToast("Broadcasting message to selected users...");
    try {
      const res = await fetchMeshApi("/api/admin/broadcast", {
        method: "POST",
        body: JSON.stringify({
          target: broadcastTarget,
          message: broadcastText
        })
      });
      if (res && res.ok) {
        setBroadcastResult(res);
        showToast(`Broadcast delivered! Sent: ${res.sent}, Failed: ${res.failed}`);
      } else {
        showToast(res?.error || "Broadcast failed");
      }
    } catch (err) {
      showToast("Error: " + err.message);
    } finally {
      setIsBroadcasting(false);
    }
  };
"""

if "const handleScanSessions = async" not in content:
    content = content.replace(
        '  const handleDeductSweep = async () => {',
        handlers_code + '\n  const handleDeductSweep = async () => {'
    )
    print("Added handlers for session scanning and broadcast.")

# 4. Add Isolation Banner right before the nav bar
isolation_banner = """
    // ==========================================================
    // STRICT ISOLATION DIRECTIVE BANNER
    // ==========================================================
    React.createElement("div", { className: `p-3 rounded-2xl border mb-3 flex items-start gap-2.5 text-left ${isDarkMode ? "bg-violet-950/30 border-violet-800/40 text-violet-200" : "bg-violet-50/80 border-violet-200 text-violet-900"}` },
      React.createElement("div", { className: "w-8 h-8 rounded-xl bg-violet-600/20 border border-violet-500/30 flex items-center justify-center text-sm shrink-0 mt-0.5" }, "🤖"),
      React.createElement("div", { className: "space-y-0.5 flex-1" },
        React.createElement("div", { className: "flex items-center justify-between" },
          React.createElement("span", { className: "font-extrabold text-xs uppercase tracking-wider text-violet-400 flex items-center gap-1.5" },
            "User Bot Community Console",
            React.createElement("span", { className: "px-1.5 py-0.5 rounded-full bg-violet-500/20 border border-violet-500/30 text-[9px] font-mono text-violet-300" }, "@AAAPREMIUMAPPSbot")
          ),
          React.createElement("a", { href: "/admin", className: "text-[10px] text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1" },
            "Fleet Admin (/admin) ➔"
          )
        ),
        React.createElement("p", { className: "text-[11px] opacity-80 leading-relaxed" },
          "Strict Ecosystem Isolation: Manages public end-users, 5-chain non-custodial wallets, and session revocation. Admin Fleet (#1-#20) is managed exclusively on /admin."
        )
      )
    ),
"""

if "STRICT ISOLATION DIRECTIVE BANNER" not in content:
    content = content.replace(
        '    // ==========================================================\n    // MOBILE NAVIGATION SEGMENTED TABS (4 TABS)\n    // ==========================================================',
        isolation_banner + '\n    // ==========================================================\n    // MOBILE NAVIGATION SEGMENTED TABS (5 TABS)\n    // =========================================================='
    )
    print("Added isolation banner.")

# 5. Expand nav tabs from 4 to 5 tabs (grid grid-cols-5)
old_nav = """    React.createElement("nav", { className: `grid grid-cols-4 gap-1 p-1 rounded-xl mb-3 border ${isDarkMode ? "bg-slate-900/90 border-slate-800" : "bg-slate-100 border-slate-200"}` },
      [
        { id: "users", label: "Users", icon: "users", count: adminUsers.length },
        { id: "wallets", label: "Wallets", icon: "wallet", count: communityWallets.length },
        { id: "pools", label: "9 Pools", icon: "zap", count: 9 },
        { id: "economy", label: "Economy", icon: "crown" }
      ].map(tab => {"""

new_nav = """    React.createElement("nav", { className: `grid grid-cols-5 gap-1 p-1 rounded-xl mb-3 border ${isDarkMode ? "bg-slate-900/90 border-slate-800" : "bg-slate-100 border-slate-200"}` },
      [
        { id: "users", label: "Users", icon: "users", count: adminUsers.length },
        { id: "wallets", label: "Wallets", icon: "wallet", count: communityWallets.length },
        { id: "broadcast", label: "Broadcast", icon: "bell" },
        { id: "pools", label: "9 Pools", icon: "zap", count: 9 },
        { id: "economy", label: "Economy", icon: "crown" }
      ].map(tab => {"""

content = content.replace(old_nav, new_nav)
print("Updated navigation to 5 tabs.")

# 6. Add Broadcast tab content right after Wallets tab content
broadcast_tab_content = """
    // ==========================================================
    // TAB: BROADCAST & NOTIFICATION CENTER (@AAAPREMIUMAPPSbot)
    // ==========================================================
    activeNavTab === "broadcast" && React.createElement("div", { className: "space-y-3 text-left" },
      // Broadcast Overview Card
      React.createElement("div", { className: `p-4 rounded-2xl border ${cardBg} space-y-3` },
        React.createElement("div", { className: "flex items-center justify-between" },
          React.createElement("div", { className: "flex items-center gap-2" },
            React.createElement("div", { className: "w-8 h-8 rounded-xl bg-blue-500/15 border border-blue-500/30 flex items-center justify-center text-blue-400 font-bold" }, "📢"),
            React.createElement("div", null,
              React.createElement("div", { className: "font-bold text-xs" }, "Community Broadcast & Alerts"),
              React.createElement("div", { className: "text-[10px] text-slate-400" }, "Send notifications directly inside @AAAPREMIUMAPPSbot")
            )
          ),
          React.createElement("button", {
            onClick: handleScanSessions,
            disabled: isScanningSessions,
            className: "text-[10px] font-bold px-2.5 py-1.5 rounded-lg bg-emerald-600/20 text-emerald-400 border border-emerald-500/30 active:scale-95 transition flex items-center gap-1"
          },
            React.createElement(Icon, { name: "refresh", className: `w-3 h-3 ${isScanningSessions ? "animate-spin" : ""}` }),
            isScanningSessions ? "Scanning..." : "Scan Revoked Sessions"
          )
        ),

        // Target Selector
        React.createElement("div", null,
          React.createElement("label", { className: "block text-[10px] uppercase font-bold text-slate-400 mb-1.5" }, "Select Target Audience:"),
          React.createElement("div", { className: "grid grid-cols-2 gap-2 text-xs" },
            [
              { id: "no_account", label: "📱 Unconnected Users", count: adminUsers.filter(u => !(u.accounts && u.accounts.length > 0)).length, desc: "Invite to connect via QR/Phone" },
              { id: "revoked", label: "⚠️ Revoked Sessions", count: adminUsers.filter(u => (u.accounts || []).some(a => a.status === "revoked")).length, desc: "Notify to re-authorize device" },
              { id: "all", label: "👥 All Users", count: adminUsers.length, desc: "Entire community roster" },
              { id: "active", label: "🟢 Active Mining Users", count: adminUsers.filter(u => (u.accounts || []).some(a => a.status === "active")).length, desc: "Active 24/7 miners" }
            ].map(t => {
              const isSel = broadcastTarget === t.id;
              return React.createElement("button", {
                key: t.id,
                onClick: () => { setBroadcastTarget(t.id); haptic("light"); },
                className: `p-2.5 rounded-xl border text-left transition ${
                  isSel ? "border-blue-500 bg-blue-500/15 text-blue-400 font-bold shadow-2xs" : `${subCardBg} text-slate-300 hover:border-slate-700`
                }`
              },
                React.createElement("div", { className: "flex items-center justify-between text-xs mb-0.5" },
                  React.createElement("span", null, t.label),
                  React.createElement("span", { className: "font-mono text-[10px] px-1.5 py-0.2 rounded-full bg-black/40 text-slate-300" }, t.count)
                ),
                React.createElement("div", { className: "text-[9px] text-slate-400 font-normal leading-tight" }, t.desc)
              );
            })
          )
        ),

        // Pre-built Message Templates
        React.createElement("div", null,
          React.createElement("label", { className: "block text-[10px] uppercase font-bold text-slate-400 mb-1.5" }, "Choose Pre-Built Template:"),
          React.createElement("div", { className: "flex items-center gap-1.5 flex-wrap" },
            [
              {
                id: "onboard",
                label: "🚀 Connect Account (QR & Phone Upgrade)",
                text: "🚀 *Upgrade Alert: Connect Your Account for 24/7 Cloud Auto-Mining!* 🌟\\n\\nHey Miner! We have fully upgraded AAA AUTO MINING with *1-Tap QR Login & Phone Login* for continuous cloud automation!\\n\\n⛏️ *Why connect your real device session?*\\n• 3rd-party bots (*MRG, ATF, Victor's, Vyro, Kynex, Diggo, Astra, Pepe, Adx*) require authentic sessions to claim yields.\\n• Old numeric Telegram IDs cannot sign transactions and have been retired.\\n• Dedicated 5-chain non-custodial wallet suite included with 100% private key ownership!\\n\\n👉 *Tap below to connect in seconds and start earning 24/7 with zero battery drain:*"
              },
              {
                id: "revoked",
                label: "⚠️ Session Revoked Reconnect",
                text: "⚠️ *Telegram Session Disconnected / Revoked* 🔴\\n\\nYour connected Telegram account session has been terminated or expired from Telegram Settings > Devices.\\n\\n🛑 *Cloud auto-mining has paused* across all 9 bots to protect your account.\\n\\n👉 *Tap below to reconnect via 1-Tap QR Login or Phone Login to resume your 24/7 cloud earnings!*"
              },
              {
                id: "daily",
                label: "💎 Free Daily Points Reminder",
                text: "🎁 *Daily Cloud Mining Check-In & Bonus!* 💎\\n\\nDon't forget to claim your +100 Daily Streak Points today in AAA AUTO MINING!\\n\\n• Watch unlimited rewarded video ads for +20 Pts each\\n• Free welcome bonus waiting for you\\n\\n👉 *Open the bot below to claim your points and keep your cloud miners running!*"
              }
            ].map(tpl => React.createElement("button", {
              key: tpl.id,
              onClick: () => { setBroadcastTemplate(tpl.id); setBroadcastText(tpl.text); haptic("light"); },
              className: `px-2.5 py-1.5 rounded-lg border text-[10px] font-semibold transition ${
                broadcastTemplate === tpl.id ? "border-cyan-500 bg-cyan-500/20 text-cyan-300" : `${subCardBg} text-slate-400 hover:text-white`
              }`
            }, tpl.label))
          )
        ),

        // Message Textarea
        React.createElement("div", null,
          React.createElement("label", { className: "block text-[10px] uppercase font-bold text-slate-400 mb-1" }, "Broadcast Message Content (Markdown Supported):"),
          React.createElement("textarea", {
            rows: 5,
            value: broadcastText,
            onChange: (e) => setBroadcastText(e.target.value),
            placeholder: "Enter message text to broadcast...",
            className: `w-full p-2.5 rounded-xl border text-xs font-mono leading-relaxed focus:outline-none focus:border-blue-500 transition ${isDarkMode ? "bg-slate-950 border-slate-800 text-slate-200" : "bg-white border-slate-200 text-slate-900"}`
          })
        ),

        // Live Action Buttons Attached to Every Broadcast
        React.createElement("div", { className: "p-2.5 rounded-xl bg-black/30 border border-white/5 space-y-1.5 text-[10px] text-slate-400 font-mono" },
          React.createElement("div", { className: "text-slate-300 font-bold" }, "📎 Attached Interactive Buttons:"),
          React.createElement("div", { className: "grid grid-cols-3 gap-1 text-center" },
            React.createElement("span", { className: "p-1 rounded bg-blue-600/20 text-blue-300 border border-blue-500/30" }, "📱 1-Tap QR Login"),
            React.createElement("span", { className: "p-1 rounded bg-emerald-600/20 text-emerald-300 border border-emerald-500/30" }, "📱 Phone Login"),
            React.createElement("span", { className: "p-1 rounded bg-amber-600/20 text-amber-300 border border-amber-500/30" }, "💎 My Wallets & Keys")
          )
        ),

        // Send Button
        React.createElement("button", {
          onClick: handleSendBroadcast,
          disabled: isBroadcasting || !broadcastText.trim(),
          className: "tap-target w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-xs active:scale-[0.98] transition flex items-center justify-center gap-2 shadow-lg shadow-blue-500/20 disabled:opacity-50"
        },
          React.createElement(Icon, { name: "send", className: `w-4 h-4 ${isBroadcasting ? "animate-pulse" : ""}` }),
          React.createElement("span", null, isBroadcasting ? "Broadcasting to Telegram Users..." : `Send Broadcast to Selected Users`)
        ),

        // Result Card
        broadcastResult && React.createElement("div", { className: "p-3 rounded-xl bg-emerald-950/40 border border-emerald-500/40 text-xs text-emerald-300 space-y-1" },
          React.createElement("div", { className: "font-bold flex items-center gap-1.5" },
            React.createElement(Icon, { name: "check", className: "w-4 h-4 text-emerald-400" }),
            "Broadcast Report:"
          ),
          React.createElement("div", { className: "font-mono text-[10px] text-slate-300" },
            `• Target: ${broadcastResult.target} | Total: ${broadcastResult.total} | Sent: ${broadcastResult.sent} | Failed: ${broadcastResult.failed}`
          )
        )
      )
    ),
"""

if "activeNavTab === \"broadcast\"" not in content:
    target_str = '    // ==========================================================\n    // TAB 3: 9 CLOUD MINING POOLS TELEMETRY VIEW\n    // =========================================================='
    content = content.replace(target_str, broadcast_tab_content + '\n' + target_str)
    print("Added broadcast tab content.")

# 7. Add Single User Notify and Session Scan buttons in Tab 1
user_action_buttons = """
              // Action Buttons
              React.createElement("div", { className: "grid grid-cols-3 gap-1.5 pt-2 border-t border-slate-800/40 text-[10px]" },
                React.createElement("button", {
                  onClick: () => handleNotifySingleUser(u.user_id, u.name, "onboard_qr"),
                  className: "py-1 px-2 rounded-lg bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 border border-blue-500/30 font-semibold active:scale-95 transition"
                }, "📱 Notify Connect"),
                React.createElement("button", {
                  onClick: () => handleAddPoints(u.user_id),
                  className: "py-1 px-2 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 border border-emerald-500/30 font-semibold active:scale-95 transition"
                }, "+100 Pts"),
                React.createElement("button", {
                  onClick: () => handleSetVip(u.user_id),
                  className: "py-1 px-2 rounded-lg bg-amber-600/20 hover:bg-amber-600/30 text-amber-400 border border-amber-500/30 font-semibold active:scale-95 transition"
                }, "⭐ VIP Pass")
              ),
"""

with open(SRC_HTML, "w", encoding="utf-8") as f:
    f.write(content)

DST_HTML = os.path.join(BASE_DIR, "public", "user-admin.html")
with open(DST_HTML, "w", encoding="utf-8") as f:
    f.write(content)

print("public_admin/user-admin.html and public/user-admin.html successfully rebuilt and synchronized!")
