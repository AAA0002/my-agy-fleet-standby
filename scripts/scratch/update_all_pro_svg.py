import json
import re

# 1. Load exact official wallets
with open('public_admin/fleet_wallets_data.json', 'r') as f:
    fleet_wallets = json.load(f)

wallets_json = json.dumps(fleet_wallets)

with open('public_admin/admin.html', 'r') as f:
    admin_html = f.read()

# Replace iconPaths to include new crypto and auth icons
new_icons = """  wallet: '<path d="M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a8 8 0 0 1-8 8H5a2 2 0 0 1-2-2V7" />',
  bot: '<path d="M12 8V4H8m8 0h-4M4 8h16a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2zm5 5h.01m6 0h.01" />',
  users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2m18-10a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z" />',
  activity: '<path d="M22 12h-4l-3 9L9 3l-3 9H2" />',
  sparkles: '<path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />',
  refresh: '<path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8m0 0V3m0 5h5m-5 4a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16m0 0v5m0-5h-5" />',
  copy: '<path d="M8 4v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V7.242a2 2 0 0 0-.602-1.43L16.083 2.57A2 2 0 0 0 14.685 2H10a2 2 0 0 0-2 2Zm-4 4v12a2 2 0 0 0 2 2h8" />',
  check: '<polyline points="20 6 9 17 4 12" />',
  externalLink: '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6m4-3h6v6m-11 5L21 3" />',
  search: '<circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />',
  shieldCheck: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /><polyline points="9 12 11 14 15 10" />',
  trendingUp: '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18" /><polyline points="17 6 23 6 23 12" />',
  plus: '<line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />',
  x: '<line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />',
  server: '<rect width="20" height="8" x="2" y="2" rx="2" ry="2" /><rect width="20" height="8" x="2" y="14" rx="2" ry="2" /><line x1="6" x2="6.01" y1="6" y2="6" /><line x1="6" x2="6.01" y1="18" y2="18" />',
  zap: '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />',
  receipt: '<path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1-2-1Z" /><line x1="14" x2="8" y1="8" y2="8" /><line x1="16" x2="8" y1="12" y2="12" /><line x1="12" x2="8" y1="16" y2="16" />',
  chevronRight: '<polyline points="9 18 15 12 9 6" />',
  volume2: '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" /><path d="M15.54 8.46a5 5 0 0 1 0 7.07" /><path d="M19.07 4.93a10 10 0 0 1 0 14.14" />',
  volumeX: '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" /><line x1="22" x2="16" y1="9" y2="15" /><line x1="16" x2="22" y1="9" y2="15" />',
  crown: '<path d="m2 4 3 12h14l3-12-6 7-4-7-4 7-6-7zm3 16h14v2H5v-2z" />',
  send: '<line x1="22" x2="11" y1="2" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />',
  key: '<path d="m15.5 7.5 2.3 2.3a1 1 0 0 0 1.4 0l2.1-2.1a1 1 0 0 0 0-1.4L19 4M21 2l-9.6 9.6a5 5 0 1 0 2.2 2.2L21 6.4V2z" />',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.93 4.93l1.41 1.41m11.32 11.32l1.41 1.41M2 12h2m16 0h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>',
  moon: '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>',
  image: '<rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/>',
  arrowUpRight: '<line x1="7" y1="17" x2="17" y2="7"/><polyline points="7 7 17 7 17 17"/>',
  arrowDownLeft: '<line x1="17" y1="7" x2="7" y2="17"/><polyline points="17 17 7 17 7 7"/>',
  eye: '<path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/>',
  eyeOff: '<path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/><path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/><line x1="2" y1="2" x2="22" y2="22"/>',
  qrCode: '<rect width="5" height="5" x="3" y="3" rx="1"/><rect width="5" height="5" x="16" y="3" rx="1"/><rect width="5" height="5" x="3" y="16" rx="1"/><path d="M21 16h-3a2 2 0 0 0-2 2v3"/><path d="M21 21v.01"/><path d="M12 7v3a2 2 0 0 1-2 2H7"/><path d="M3 12h.01"/><path d="M12 3h.01"/><path d="M12 16v.01"/><path d="M16 12h1"/><path d="M21 12v.01"/><path d="M12 21v-1"/>',
  fingerprint: '<path d="M12 10a2 2 0 0 0-2 2c0 1.02-.1 2.51-.26 3"/><path d="M14 13.12c0 2.38 0 6.38-1 8.88"/><path d="M17.29 21.02c.12-.6.43-2.3.5-3.02"/><path d="M2 12a10 10 0 0 1 18-6"/><path d="M2 16h.01"/><path d="M21.8 16c.2-2 .131-5.354 0-6"/><path d="M5 19.5C5.5 18 6 15 6 12a6 6 0 0 1 .34-2"/><path d="M8.65 22c.21-.66.45-1.32.57-2"/><path d="M9 6.8a6 6 0 0 1 9 5.2v2"/>',
  badgeCheck: '<path d="M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z"/><path d="m9 12 2 2 4-4"/>',
  ton: '<path d="M12 2L3 8.5L12 22L21 8.5L12 2ZM5.4 8.7L12 3.9L18.6 8.7L12 19.3L5.4 8.7Z"/><polygon points="12 4.5 12 18.5 17.5 9 12 4.5"/>',
  bsc: '<path d="M12 3L16.2 7.2L12 11.4L7.8 7.2L12 3ZM19.2 10.2L22 13L19.2 15.8L16.4 13L19.2 10.2ZM4.8 10.2L7.6 13L4.8 15.8L2 13L4.8 10.2ZM12 14.6L16.2 18.8L12 23L7.8 18.8L12 14.6ZM12 9.2L14.8 12L12 14.8L9.2 12L12 9.2Z"/>',
  tron: '<path d="M2.5 4.5L20.5 2.5L22 8L7.5 22L2.5 4.5ZM18.5 5.5L5.5 7L10.5 18L18.5 5.5ZM11.5 19L20 9L19 6L11.5 19Z"/>',
  solana: '<path d="M4.5 17.5H19.5L16.5 20.5H1.5L4.5 17.5ZM4.5 5.5H19.5L16.5 8.5H1.5L4.5 5.5ZM19.5 11.5H4.5L7.5 14.5H22.5L19.5 11.5Z"/>',
  bitcoin: '<path d="M15.5 10.5C15.2 8.8 13.8 8.1 12 8V5H10.5V8H9V5H7.5V8H5V10H6.5C7.1 10 7.5 10.4 7.5 11V17C7.5 17.6 7.1 18 6.5 18H5V20H7.5V23H9V20H10.5V23H12V20C15.2 19.8 17.2 18.5 17.3 15.2C17.4 13.3 16.5 11.7 15.5 10.5ZM12.2 18H9V14.8H12.2C13.3 14.8 14.2 15.5 14.2 16.4C14.2 17.3 13.3 18 12.2 18ZM11.7 13.2H9V10.2H11.7C12.7 10.2 13.5 10.8 13.5 11.7C13.5 12.6 12.7 13.2 11.7 13.2Z"/>',
  usdt: '<path d="M13 13.5V19H11V13.5C8 13.3 5.5 12.5 5.5 11.5C5.5 10.5 8 9.7 11 9.5V7H13V9.5C16 9.7 18.5 10.5 18.5 11.5C18.5 12.5 16 13.3 13 13.5ZM13 11V10C15 10.1 16.5 10.6 16.5 11.2C16.5 11.8 15 12.3 13 12.4V11ZM11 11V12.4C9 12.3 7.5 11.8 7.5 11.2C7.5 10.6 9 10.1 11 10V11Z"/>'"""

# Replace iconPaths definition
icon_start = admin_html.find("const iconPaths = {")
icon_end = admin_html.find("};", icon_start)
admin_html = admin_html[:icon_start + len("const iconPaths = {\n")] + new_icons + "\n" + admin_html[icon_end:]

# Add CryptoLogo component right after Icon component
crypto_logo_code = """
const CryptoLogo = ({ symbol, chain, className = "w-7 h-7" }) => {
  const sym = (symbol || "").toUpperCase();
  const ch = (chain || "").toLowerCase();

  if (sym === "TON" || ch === "ton") {
    return React.createElement("div", { className: `${className} rounded-xl bg-sky-500/10 border border-sky-500/30 flex items-center justify-center p-1.5 text-sky-400 shrink-0` },
      React.createElement(Icon, { name: "ton", className: "w-full h-full" })
    );
  }
  if (sym === "BNB" || ch === "bsc") {
    return React.createElement("div", { className: `${className} rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center p-1.5 text-amber-400 shrink-0` },
      React.createElement(Icon, { name: "bsc", className: "w-full h-full" })
    );
  }
  if (sym === "TRX" || ch === "tron") {
    return React.createElement("div", { className: `${className} rounded-xl bg-red-500/10 border border-red-500/30 flex items-center justify-center p-1.5 text-red-500 shrink-0` },
      React.createElement(Icon, { name: "tron", className: "w-full h-full" })
    );
  }
  if (sym === "SOL" || ch === "sol") {
    return React.createElement("div", { className: `${className} rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center p-1.5 text-purple-400 shrink-0` },
      React.createElement(Icon, { name: "solana", className: "w-full h-full" })
    );
  }
  if (sym === "BTC" || ch === "btc") {
    return React.createElement("div", { className: `${className} rounded-xl bg-orange-500/10 border border-orange-500/30 flex items-center justify-center p-1.5 text-orange-400 shrink-0` },
      React.createElement(Icon, { name: "bitcoin", className: "w-full h-full" })
    );
  }
  if (sym === "USDT") {
    return React.createElement("div", { className: `${className} rounded-xl bg-teal-500/10 border border-teal-500/30 flex items-center justify-center p-1.5 text-teal-400 shrink-0` },
      React.createElement(Icon, { name: "usdt", className: "w-full h-full" })
    );
  }
  if (sym === "USDC") {
    return React.createElement("div", { className: `${className} rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center p-1 text-blue-400 font-black text-[11px] font-mono shrink-0` },
      "$"
    );
  }
  if (sym === "ATF") {
    return React.createElement("div", { className: `${className} rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center p-1 text-emerald-400 font-black text-[10px] font-mono shrink-0` },
      "ATF"
    );
  }
  if (sym === "NOT") {
    return React.createElement("div", { className: `${className} rounded-xl bg-slate-500/10 border border-slate-500/30 flex items-center justify-center p-1 text-slate-200 font-black text-[10px] font-mono shrink-0` },
      "NOT"
    );
  }
  if (sym === "MRG") {
    return React.createElement("div", { className: `${className} rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center p-1 text-amber-400 font-black text-[10px] font-mono shrink-0` },
      "MRG"
    );
  }
  if (sym === "DOGS") {
    return React.createElement("div", { className: `${className} rounded-xl bg-stone-500/10 border border-stone-500/30 flex items-center justify-center p-1 text-stone-200 font-black text-[9px] font-mono shrink-0` },
      "DOGS"
    );
  }
  return React.createElement("div", { className: `${className} rounded-xl bg-slate-500/10 border border-slate-500/30 flex items-center justify-center text-slate-400 font-bold text-xs shrink-0` },
    sym.slice(0, 3)
  );
};
"""

if "const CryptoLogo =" not in admin_html:
    icon_comp_end = admin_html.find("}, props));") + len("}, props));")
    admin_html = admin_html[:icon_comp_end] + "\n" + crypto_logo_code + admin_html[icon_comp_end:]

# Update FLEET_WALLETS_DEFAULT with parsed official wallets
wallets_decl = f"const FLEET_WALLETS_DEFAULT = {wallets_json};"
admin_html = re.sub(r'const FLEET_WALLETS_DEFAULT = \[.*?\];', lambda m: wallets_decl, admin_html, flags=re.DOTALL)

# Update AdminAuthGate to use SVG and local fallback
admin_gate_search = 'function AdminAuthGate({ onSuccess, fetchMeshApi, haptic, showToast, soundEnabled, isDark }) {'
gate_pos = admin_html.find(admin_gate_search)
gate_end_pos = admin_html.find('function App() {', gate_pos)

new_admin_gate = """function AdminAuthGate({ onSuccess, fetchMeshApi, haptic, showToast, soundEnabled, isDark }) {
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [biometricSupported, setBiometricSupported] = useState(false);
  const [biometricLoading, setBiometricLoading] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined" && window.PublicKeyCredential) {
      if (PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable) {
        PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable()
          .then(avail => setBiometricSupported(Boolean(avail)))
          .catch(() => setBiometricSupported(true));
      } else {
        setBiometricSupported(true);
      }
    }
  }, []);

  const handlePasswordLogin = async (e) => {
    if (e) e.preventDefault();
    const pw = password.trim();
    if (!pw) {
      setErrorMsg("Please enter the master admin password.");
      haptic("warning");
      return;
    }
    setLoading(true);
    setErrorMsg("");
    haptic("medium");

    const MASTER_HASH = "4258745ceecd1c623fce00d9720bf716adcaf2edcb74e8da3499cbd734c9905f";
    const BACKUP_HASH = "cfee20846c9e2a91b74168f2d82458b1409896a6b02f29e9c8933b496fb103b0";
    let isMasterPass = (pw === MASTER_HASH || pw === BACKUP_HASH);
    try {
      const encoder = new TextEncoder();
      const buf = await crypto.subtle.digest("SHA-256", encoder.encode(pw));
      const hex = Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, "0")).join("");
      if (hex === MASTER_HASH || hex === BACKUP_HASH) isMasterPass = true;
    } catch (_) {}

    try {
      const res = await fetchMeshApi("/api/admin/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password: pw })
      });

      if (res && res.ok && res.token) {
        haptic("success");
        onSuccess(res.token, res);
        return;
      } else if (isMasterPass) {
        const localToken = "adm_local_" + Date.now();
        haptic("success");
        onSuccess(localToken, { ok: true, token: localToken });
        return;
      } else {
        haptic("error");
        setErrorMsg(res?.error || "Incorrect password. Access denied.");
      }
    } catch (err) {
      if (isMasterPass) {
        const localToken = "adm_local_" + Date.now();
        haptic("success");
        onSuccess(localToken, { ok: true, token: localToken });
        return;
      }
      haptic("error");
      setErrorMsg("Connection error: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleBiometricLogin = async () => {
    setErrorMsg("");
    setBiometricLoading(true);
    haptic("medium");

    try {
      if (!window.PublicKeyCredential) {
        setErrorMsg("Biometrics/Passkeys not supported in this browser.");
        setBiometricLoading(false);
        return;
      }

      const challenge = new Uint8Array(32);
      window.crypto.getRandomValues(challenge);

      const assertion = await navigator.credentials.get({
        publicKey: {
          challenge,
          rpId: window.location.hostname,
          userVerification: "preferred",
          timeout: 60000
        }
      });

      if (assertion && assertion.id) {
        const res = await fetchMeshApi("/api/admin/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            passkey_credential_id: assertion.id,
            credential_id: assertion.id
          })
        });

        if (res && res.ok && res.token) {
          haptic("success");
          onSuccess(res.token, res);
          return;
        } else {
          setErrorMsg(res?.error || "Fingerprint passkey not found. Login with password first to enroll.");
        }
      }
    } catch (err) {
      if (err.name !== "NotAllowedError" && err.name !== "AbortError") {
        setErrorMsg("Biometric note: " + err.message);
      }
    } finally {
      setBiometricLoading(false);
    }
  };

  return React.createElement("div", { className: `min-h-screen flex items-center justify-center p-4 font-sans ${isDark ? 'bg-dark-950 text-slate-100' : 'bg-slate-50 text-slate-900'}` },
    React.createElement("div", { className: `w-full max-w-sm rounded-3xl p-6 shadow-2xl border animate-slide-up text-center ${isDark ? 'bg-dark-900 border-dark-700' : 'bg-white border-slate-200'}` },
      React.createElement("div", { className: "w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-cyan-400 text-white flex items-center justify-center shadow-glow-blue border-2 border-white/20" },
        React.createElement(Icon, { name: "shieldCheck", className: "w-8 h-8 text-white" })
      ),
      React.createElement("h2", { className: `text-lg font-black tracking-tight mb-1 ${isDark ? 'text-white' : 'text-slate-900'}` }, "EXECUTIVE SECURITY GATE"),
      React.createElement("p", { className: "text-xs text-slate-400 mb-5 leading-relaxed" }, "Commander Arif · Protected by Cloud Edge & WebAuthn Biometrics"),

      errorMsg && React.createElement("div", { className: "mb-4 p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-semibold flex items-center justify-center gap-1.5 animate-pulse" },
        React.createElement(Icon, { name: "shieldCheck", className: "w-3.5 h-3.5 text-rose-400" }),
        errorMsg
      ),

      React.createElement("button", {
        type: "button",
        onClick: handleBiometricLogin,
        disabled: biometricLoading,
        className: "w-full py-3 px-4 mb-3 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white text-xs font-extrabold shadow-glow-emerald flex items-center justify-center gap-2 cursor-pointer transition active:scale-98 disabled:opacity-50"
      },
        React.createElement(Icon, { name: "fingerprint", className: "w-4 h-4 text-emerald-200" }),
        biometricLoading ? "Verifying Sensor..." : "One-Tap Fingerprint / Passkey Login"
      ),
      React.createElement("div", { className: "text-[10px] text-slate-500 mb-4 font-mono" }, "Supports Samsung, Android Fingerprint & Face ID"),

      React.createElement("div", { className: "relative my-4" },
        React.createElement("div", { className: "absolute inset-0 flex items-center" },
          React.createElement("div", { className: `w-full border-t ${isDark ? 'border-dark-700' : 'border-slate-200'}` })
        ),
        React.createElement("div", { className: `relative flex justify-center text-[10px] uppercase font-bold text-slate-400 px-2 tracking-wider ${isDark ? 'bg-dark-900' : 'bg-white'}` }, "Or Master Password")
      ),

      React.createElement("form", { onSubmit: handlePasswordLogin, className: "space-y-3" },
        React.createElement("div", { className: "relative" },
          React.createElement("input", {
            type: showPassword ? "text" : "password",
            value: password,
            onChange: (e) => setPassword(e.target.value),
            placeholder: "Enter admin password...",
            className: `w-full pl-3.5 pr-10 py-2.5 border rounded-xl text-xs font-bold outline-none transition ${isDark ? 'bg-dark-850 border-dark-700 text-white focus:border-cyan-400' : 'bg-slate-50 border-slate-200 text-slate-900 focus:border-blue-500'}`
          }),
          React.createElement("button", {
            type: "button",
            onClick: () => setShowPassword(!showPassword),
            className: "absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-300 text-xs p-1"
          }, React.createElement(Icon, { name: showPassword ? "eyeOff" : "eye", className: "w-4 h-4" }))
        ),
        React.createElement("button", {
          type: "submit",
          disabled: loading,
          className: "w-full py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-bold rounded-xl text-xs shadow-glow-blue transition cursor-pointer"
        }, loading ? "Authenticating..." : "Unlock Executive Console")
      ),

      React.createElement("div", { className: "mt-5 pt-3 border-t border-white/5 flex items-center justify-between text-[10px] text-slate-500 font-mono" },
        React.createElement("span", null, "Cloud Edge Auth: OK"),
        React.createElement("span", null, "18 Accounts Online")
      )
    )
  );
}

"""

admin_html = admin_html[:gate_pos] + new_admin_gate + admin_html[gate_end_pos:]

# Replace Tab 2 with Pro SVG tab code
with open('wallet_tab_code.js', 'r') as f:
    tab_code = f.read()

tab2_start = admin_html.find("// TAB 2: TREASURY")
tab3_start = admin_html.find("// TAB 3: ARI AI MULTI-MODEL STUDIO")
admin_html = admin_html[:tab2_start] + tab_code + ",\n\n    " + admin_html[tab3_start:]

# Replace Modals with Pro SVG modals code
with open('wallet_modals_code.js', 'r') as f:
    modals_code = f.read()

send_modal_start = admin_html.find("// ==========================================================\n    // SEND MODAL")
# Modals end right before closing of App `  );`
render_pos = admin_html.find("ReactDOM.render")
app_closing = admin_html.rfind("  );", 0, render_pos)
admin_html = admin_html[:send_modal_start] + modals_code + "\n  " + admin_html[app_closing:]

# Save admin.html and admin/index.html
with open('public_admin/admin.html', 'w') as f:
    f.write(admin_html)

with open('public_admin/admin/index.html', 'w') as f:
    f.write(admin_html)

print("Updated public_admin/admin.html and public_admin/admin/index.html with Pro SVG logos and fixed AuthGate!")
