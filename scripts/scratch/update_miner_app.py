#!/usr/bin/env python3
"""Updates public_ads/miner/index.html with QR login, phone login, and non-custodial wallet management."""
import os
import re

def update_miner():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "public_ads", "miner", "index.html")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Replace 1-Tap Instant Connect Button with Dual Authentic QR & Phone Connect Buttons
    old_btn = """        <!-- 1-Tap Instant Connect Button -->
        <button type="button" onclick="quickConnectCurrentAccount()" id="btn-quick-connect" class="w-full min-h-[44px] py-2.5 px-4 rounded-xl bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs active:scale-[0.98] transition flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/20 mb-3">
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"></path></svg>
          <span>⚡ 1-Tap Link My Telegram Account</span>
        </button>"""

    new_btn = """        <!-- Authentic Telegram Device QR & Phone Login Buttons -->
        <div class="grid grid-cols-2 gap-2 mb-3">
          <button type="button" onclick="startQrConnectModal()" id="btn-quick-qr" class="min-h-[44px] py-2.5 px-3 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-xs active:scale-[0.98] transition flex items-center justify-center gap-1.5 shadow-lg shadow-blue-500/20">
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>
            <span>📱 1-Tap QR Login</span>
          </button>
          <button type="button" onclick="openPhoneLoginModal()" id="btn-phone-login" class="min-h-[44px] py-2.5 px-3 rounded-xl bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs active:scale-[0.98] transition flex items-center justify-center gap-1.5 shadow-lg shadow-emerald-500/20">
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>
            <span>📱 Phone Login</span>
          </button>
        </div>"""

    if old_btn in content:
        content = content.replace(old_btn, new_btn)
        print("Updated connect buttons.")

    # 2. Add Wallets Section to Tab 4 (tab-accounts)
    wallets_section = """
      <!-- Non-Custodial Multi-Chain Wallets Card -->
      <div id="wallets-card-container" class="mt-4 card-glass p-4 rounded-2xl space-y-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <div class="w-7 h-7 rounded-lg bg-blue-500/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
              <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 12V8H6a2 2 0 0 1-2-2c0-1.1.9-2 2-2h12v4"></path><path d="M4 6v12a2 2 0 0 0 2 2h14v-4"></path><path d="M18 12a2 2 0 0 0 0 4h4v-4z"></path></svg>
            </div>
            <div>
              <h3 class="font-bold text-xs sm:text-sm text-white">💎 Non-Custodial Wallets</h3>
              <p class="text-[10px] text-slate-400 font-mono">Full ownership of keys & mining rewards</p>
            </div>
          </div>
          <button onclick="revealWalletSecrets()" class="px-2.5 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 text-cyan-300 border border-cyan-500/30 text-[10px] font-bold active:scale-95 transition flex items-center gap-1">
            <svg class="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="7.5" cy="15.5" r="5.5"></circle><path d="m21 2-9.6 9.6"></path><path d="m15.5 7.5 3 3L22 7l-3-3"></path></svg>
            <span>Show Keys</span>
          </button>
        </div>

        <div id="user-wallets-display" class="space-y-1.5 text-xs font-mono">
          <div class="p-2.5 rounded-xl bg-black/40 border border-white/5 flex items-center justify-between">
            <span class="text-slate-400 uppercase font-bold text-[9px]">TON:</span>
            <span id="wallet-addr-ton" class="text-sky-300 truncate max-w-[200px]">Generating...</span>
            <button onclick="copyWalletText('ton')" class="text-slate-400 hover:text-white p-1">📋</button>
          </div>
          <div class="p-2.5 rounded-xl bg-black/40 border border-white/5 flex items-center justify-between">
            <span class="text-slate-400 uppercase font-bold text-[9px]">EVM:</span>
            <span id="wallet-addr-evm" class="text-amber-300 truncate max-w-[200px]">Generating...</span>
            <button onclick="copyWalletText('evm')" class="text-slate-400 hover:text-white p-1">📋</button>
          </div>
        </div>

        <!-- Custom Payout Wallet Input -->
        <div class="pt-2 border-t border-white/5">
          <label class="block text-[10px] uppercase font-bold text-slate-400 mb-1">🔌 Bind Personal Wallet (Tonkeeper / MetaMask)</label>
          <div class="flex gap-1.5">
            <input type="text" id="input-custom-wallet" class="flex-1 p-2 rounded-xl bg-black/40 border border-white/10 text-xs font-mono text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500" placeholder="Enter TON (UQ...) or EVM (0x...) address" />
            <button onclick="submitCustomWallet()" class="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold shrink-0 transition active:scale-95 cursor-pointer">Save</button>
          </div>
          <div id="custom-wallet-status" class="text-[9px] text-slate-400 mt-1 font-mono">Mining payouts will route directly to this address.</div>
        </div>
      </div>
"""

    if '<div id="accounts-list-container" class="space-y-2">' in content and 'wallets-card-container' not in content:
        content = content.replace('</div>\n    </div>\n\n    <!-- ---------------------------------------------------- -->\n    <!-- TAB 5: ABOUT & NETWORK', '</div>' + wallets_section + '    </div>\n\n    <!-- ---------------------------------------------------- -->\n    <!-- TAB 5: ABOUT & NETWORK')
        print("Added Wallets section to Tab Accounts.")

    # 3. Add Modals before </main>
    modals_html = """
    <!-- Modal: QR Code Device Link -->
    <div id="qr-connect-modal" class="hidden fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4">
      <div class="card-glass w-full max-w-sm rounded-3xl p-5 border border-white/10 space-y-3 text-center animate-slide-up">
        <div class="flex items-center justify-between pb-2 border-b border-white/10">
          <div class="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
            <span class="text-blue-400">📱</span> 1-Tap Telegram QR Login
          </div>
          <button onclick="closeQrConnectModal()" class="w-7 h-7 rounded-full bg-white/10 text-slate-400 hover:text-white flex items-center justify-center text-xs">✕</button>
        </div>
        <p class="text-[11px] text-slate-300 leading-snug">
          Zero SMS codes needed! Connect official Telegram session for 24/7 cloud auto-farming across 9 pools.
        </p>
        <div class="p-3 bg-white rounded-2xl mx-auto w-52 h-52 flex items-center justify-center shadow-lg">
          <img id="qr-code-image" src="" alt="Scan QR Code" class="w-full h-full object-contain" />
        </div>
        <div id="qr-modal-status" class="text-[10px] text-slate-400 font-mono">Connecting to Render Cloud...</div>
        <button id="btn-qr-direct-link" class="w-full py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold text-xs active:scale-95 transition">
          ⚡ Link Device in Telegram Now
        </button>
        <button onclick="closeQrConnectModal()" class="w-full py-2 rounded-xl bg-white/5 hover:bg-white/10 text-slate-400 text-xs">
          Cancel
        </button>
      </div>
    </div>

    <!-- Modal: Phone Number Cloud Login -->
    <div id="phone-login-modal" class="hidden fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4">
      <div class="card-glass w-full max-w-sm rounded-3xl p-5 border border-white/10 space-y-3 animate-slide-up text-left">
        <div class="flex items-center justify-between pb-2 border-b border-white/10">
          <div class="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
            <span class="text-emerald-400">📱</span> Phone Cloud Login
          </div>
          <button onclick="closePhoneLoginModal()" class="w-7 h-7 rounded-full bg-white/10 text-slate-400 hover:text-white flex items-center justify-center text-xs">✕</button>
        </div>

        <div id="phone-step-1" class="space-y-3">
          <p class="text-[11px] text-slate-300">Enter your phone number with country code. Telegram will send an official 5-digit verification code.</p>
          <input type="text" id="input-phone-number" placeholder="+8801... or +1..." class="w-full p-2.5 rounded-xl bg-black/50 border border-white/10 text-xs text-white font-mono placeholder-slate-600 focus:outline-none focus:border-cyan-500" />
          <button id="btn-send-phone-code" onclick="requestPhoneCode()" class="w-full py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 text-white font-bold text-xs active:scale-95 transition">Send Verification Code</button>
        </div>

        <div id="phone-step-2" class="hidden space-y-3">
          <p class="text-[11px] text-slate-300">Enter the 5-digit verification code sent to <span id="phone-code-sent-to" class="text-cyan-300 font-mono"></span> in Telegram:</p>
          <input type="text" id="input-phone-code" placeholder="12345" maxlength="6" class="w-full p-2.5 rounded-xl bg-black/50 border border-white/10 text-base text-center text-white font-mono tracking-widest focus:outline-none focus:border-cyan-500" />
          <button id="btn-verify-phone-code" onclick="verifyPhoneCode()" class="w-full py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 text-white font-bold text-xs active:scale-95 transition">Verify & Connect</button>
        </div>
      </div>
    </div>

    <!-- Modal: Wallet Secrets -->
    <div id="wallet-secrets-modal" class="hidden fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-4">
      <div class="card-glass w-full max-w-sm rounded-3xl p-5 border border-white/10 space-y-3 animate-slide-up text-left">
        <div class="flex items-center justify-between pb-2 border-b border-white/10">
          <div class="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
            <span class="text-amber-400">🔐</span> Non-Custodial Secrets
          </div>
          <button onclick="document.getElementById('wallet-secrets-modal').classList.add('hidden')" class="w-7 h-7 rounded-full bg-white/10 text-slate-400 hover:text-white flex items-center justify-center text-xs">✕</button>
        </div>
        <p class="text-[10px] text-amber-300 bg-amber-500/10 p-2 rounded-xl border border-amber-500/20 leading-relaxed">
          ⚠️ <strong>CAUTION:</strong> Never share these secrets with anyone! You hold 100% full ownership of this wallet suite.
        </p>
        <div>
          <label class="block text-[9px] uppercase font-bold text-slate-400 mb-1">24-Word Recovery Mnemonic:</label>
          <div id="secrets-mnemonic" class="p-2.5 rounded-xl bg-black/60 border border-white/10 font-mono text-[11px] text-emerald-300 break-words select-all">Loading...</div>
        </div>
        <button onclick="document.getElementById('wallet-secrets-modal').classList.add('hidden')" class="w-full py-2 rounded-xl bg-white/10 hover:bg-white/20 text-white font-bold text-xs">Close</button>
      </div>
    </div>
"""

    if '<!-- Modal: QR Code Device Link -->' not in content:
        content = content.replace('  </main>', modals_html + '  </main>')
        print("Added modals before </main>.")

    # 4. Add JavaScript Controller Handlers
    js_code = """
    // -------------------------------------------------------------
    // QR Code, Phone Login & Non-Custodial Wallet Controller Logic
    // -------------------------------------------------------------
    let qrPollInterval = null;
    let phoneLoginNodeUrl = "";
    let phoneLoginTarget = "";

    async function startQrConnectModal() {
      const modal = document.getElementById('qr-connect-modal');
      const img = document.getElementById('qr-code-image');
      const linkBtn = document.getElementById('btn-qr-direct-link');
      const statusText = document.getElementById('qr-modal-status');
      if (modal) modal.classList.remove('hidden');
      if (statusText) statusText.textContent = "Connecting to Render Cloud & generating QR link...";
      if (img) img.src = "";

      try {
        const res = await apiRequest('/api/account/login/qr-start', {
          method: "POST",
          body: JSON.stringify({ chat_id: "ub_" + currentUserId, is_user_bot: true })
        });
        if (res && res.ok && res.url) {
          if (img && res.qr_image_url) img.src = res.qr_image_url;
          if (linkBtn) {
            linkBtn.onclick = () => {
              if (window.Telegram?.WebApp?.openTelegramLink) {
                window.Telegram.WebApp.openTelegramLink(res.url);
              } else {
                window.open(res.url, "_blank");
              }
            };
          }
          if (statusText) statusText.textContent = "Scan QR or tap button to authorize in Telegram.";

          if (qrPollInterval) clearInterval(qrPollInterval);
          qrPollInterval = setInterval(async () => {
            try {
              const sRes = await apiRequest(`/api/account/login/qr-status?chat_id=ub_${currentUserId}`);
              if (sRes && sRes.status === "success") {
                clearInterval(qrPollInterval);
                qrPollInterval = null;
                closeQrConnectModal();
                showToast("Account connected successfully via QR!");
                await loadUserProfile();
                switchTab('accounts');
              }
            } catch (_) {}
          }, 2000);
        } else {
          if (statusText) statusText.textContent = "Could not start QR: " + (res?.error || "Timeout");
        }
      } catch (err) {
        if (statusText) statusText.textContent = "Connection error: " + err.message;
      }
    }

    function closeQrConnectModal() {
      if (qrPollInterval) {
        clearInterval(qrPollInterval);
        qrPollInterval = null;
      }
      const modal = document.getElementById('qr-connect-modal');
      if (modal) modal.classList.add('hidden');
    }

    function openPhoneLoginModal() {
      const modal = document.getElementById('phone-login-modal');
      if (modal) modal.classList.remove('hidden');
      document.getElementById('phone-step-1').classList.remove('hidden');
      document.getElementById('phone-step-2').classList.add('hidden');
      document.getElementById('input-phone-number').value = "";
      document.getElementById('input-phone-code').value = "";
    }

    function closePhoneLoginModal() {
      const modal = document.getElementById('phone-login-modal');
      if (modal) modal.classList.add('hidden');
    }

    async function requestPhoneCode() {
      let ph = document.getElementById('input-phone-number').value.trim();
      if (!ph) { showToast("Please enter phone number"); return; }
      const btn = document.getElementById('btn-send-phone-code');
      btn.disabled = true;
      btn.textContent = "Requesting code...";
      try {
        const res = await apiRequest('/api/account/login/send-code', {
          method: "POST",
          body: JSON.stringify({ phone: ph, chat_id: "ub_" + currentUserId })
        });
        if (res && res.ok) {
          phoneLoginNodeUrl = res.node_url || "";
          phoneLoginTarget = res.phone || ph;
          document.getElementById('phone-step-1').classList.add('hidden');
          document.getElementById('phone-step-2').classList.remove('hidden');
          document.getElementById('phone-code-sent-to').textContent = phoneLoginTarget;
          showToast("Code sent to " + phoneLoginTarget);
        } else {
          showToast(res?.error || "Failed to send code");
        }
      } catch (e) {
        showToast("Error: " + e.message);
      } finally {
        btn.disabled = false;
        btn.textContent = "Send Verification Code";
      }
    }

    async function verifyPhoneCode() {
      const code = document.getElementById('input-phone-code').value.trim();
      if (!code) { showToast("Please enter verification code"); return; }
      const btn = document.getElementById('btn-verify-phone-code');
      btn.disabled = true;
      btn.textContent = "Verifying...";
      try {
        const res = await apiRequest('/api/account/login/verify-code', {
          method: "POST",
          body: JSON.stringify({
            chat_id: "ub_" + currentUserId,
            code: code,
            phone: phoneLoginTarget,
            node_url: phoneLoginNodeUrl,
            is_user_bot: true
          })
        });
        if (res && res.ok) {
          closePhoneLoginModal();
          showToast("Account connected successfully!");
          await loadUserProfile();
          switchTab('accounts');
        } else if (res && res.need_2fa) {
          showToast("2FA Password required. Please login via QR or bot.");
        } else {
          showToast(res?.error || "Invalid code");
        }
      } catch (e) {
        showToast("Verification error: " + e.message);
      } finally {
        btn.disabled = false;
        btn.textContent = "Verify & Connect";
      }
    }

    async function submitCustomWallet() {
      const addr = document.getElementById('input-custom-wallet').value.trim();
      if (!addr) { showToast("Please enter wallet address"); return; }
      const isTon = /^(EQ|UQ)[a-zA-Z0-9_-]{46,48}$/.test(addr);
      const isEvm = /^0x[a-fA-F0-9]{40}$/.test(addr);
      if (!isTon && !isEvm) {
        showToast("Invalid format. Must start with UQ/EQ or 0x");
        return;
      }
      const chain = isTon ? "ton" : "evm";
      try {
        const res = await apiRequest('/api/user/wallet/custom', {
          method: "POST",
          body: JSON.stringify({ user_id: currentUserId, address: addr, chain: chain })
        });
        if (res && res.ok) {
          showToast(`Custom ${chain.toUpperCase()} wallet bound successfully!`);
          document.getElementById('custom-wallet-status').textContent = `🟢 Payouts route to personal ${chain.toUpperCase()} wallet: ${addr.slice(0, 8)}...`;
          await loadUserProfile();
        } else {
          showToast(res?.error || "Failed to save wallet");
        }
      } catch (e) {
        showToast("Error: " + e.message);
      }
    }

    async function revealWalletSecrets() {
      const modal = document.getElementById('wallet-secrets-modal');
      const box = document.getElementById('secrets-mnemonic');
      if (modal) modal.classList.remove('hidden');
      if (box) box.textContent = "Fetching secrets from Turso LibSQL...";

      try {
        const res = await apiRequest(`/api/user/wallet/generate`, {
          method: "POST",
          body: JSON.stringify({ user_id: currentUserId, name: "User" })
        });
        if (res && res.ok && res.wallets) {
          const mn = res.wallets.ton?.mnemonic || res.wallets.evm?.mnemonic || "Deterministic seed linked to your account";
          if (box) box.textContent = mn;
        } else {
          if (box) box.textContent = "Send /wallets in @AAAPREMIUMAPPSbot to view your secrets securely in private chat.";
        }
      } catch (e) {
        if (box) box.textContent = "Send /wallets in @AAAPREMIUMAPPSbot to view secrets.";
      }
    }

    function copyWalletText(chain) {
      const el = document.getElementById(`wallet-addr-${chain}`);
      if (el && el.textContent) {
        navigator.clipboard.writeText(el.textContent).then(() => showToast(`Copied ${chain.toUpperCase()} address!`));
      }
    }
"""

    if 'async function startQrConnectModal' not in content:
        content = content.replace('    // Submit Connect Account', js_code + '\n    // Submit Connect Account')
        print("Added JS handlers.")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("public_ads/miner/index.html updated successfully!")

if __name__ == "__main__":
    update_miner()
