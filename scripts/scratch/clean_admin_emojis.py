import re

with open('public_admin/admin.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Add lock, alertTriangle, clock, cpu to iconPaths if missing
if 'lock:' not in text:
    target = '  usdt: \'<path d="M13 13.5V19H11V13.5C8 13.3 5.5 12.5 5.5 11.5C5.5 10.5 8 9.7 11 9.5V7H13V9.5C16 9.7 18.5 10.5 18.5 11.5C18.5 12.5 16 13.3 13 13.5ZM13 11V10C15 10.1 16.5 10.6 16.5 11.2C16.5 11.8 15 12.3 13 12.4V11ZM11 11V12.4C9 12.3 7.5 11.8 7.5 11.2C7.5 10.6 9 10.1 11 10V11Z"/>\''
    replacement = target + ''',
  lock: '<rect width="18" height="11" x="3" y="11" rx="2" ry="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" />',
  alertTriangle: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" /><line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" />',
  clock: '<circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />',
  cpu: '<rect x="4" y="4" width="16" height="16" rx="2" /><rect x="9" y="9" width="6" height="6" /><line x1="9" y1="1" x2="9" y2="4" /><line x1="15" y1="1" x2="15" y2="4" /><line x1="9" y1="20" x2="9" y2="23" /><line x1="15" y1="20" x2="15" y2="23" /><line x1="20" y1="9" x2="23" y2="9" /><line x1="20" y1="14" x2="23" y2="14" /><line x1="1" y1="9" x2="4" y2="9" /><line x1="1" y1="14" x2="4" y2="14" />'
'''
    assert target in text, 'usdt not found in iconPaths'
    text = text.replace(target, replacement)

# 1. SUPPORTED_TOKENS emojis
text = text.replace('icon: "💎", iconBg:', 'icon: "ton", iconBg:')
text = text.replace('icon: "🪙", iconBg:', 'icon: "ton", iconBg:')
text = text.replace('icon: "⚫", iconBg:', 'icon: "ton", iconBg:')
text = text.replace('icon: "⚡", iconBg:', 'icon: "ton", iconBg:')
text = text.replace('icon: "🐶", iconBg:', 'icon: "ton", iconBg:')
text = text.replace('icon: "🟡", iconBg:', 'icon: "bsc", iconBg:')
text = text.replace('icon: "💵", iconBg:', 'icon: "bsc", iconBg:')
text = text.replace('icon: "🔴", iconBg:', 'icon: "tron", iconBg:')
text = text.replace('icon: "🟢", iconBg:', 'icon: "tron", iconBg:')
text = text.replace('icon: "🟣", iconBg:', 'icon: "sol", iconBg:')
text = text.replace('icon: "🔵", iconBg:', 'icon: "sol", iconBg:')
text = text.replace('icon: "🟠", iconBg:', 'icon: "btc", iconBg:')

# 2. SDXL prompt
text = text.replace('🎨 Stable Diffusion XL rendering for prompt:', 'SDXL neural image synthesized for prompt:')

# 3. Lock icon
text = text.replace(
    'React.createElement("div", { className: "w-14 h-14 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-500 flex items-center justify-center text-2xl mb-4 shadow-sm" }, "🔒"),',
    'React.createElement("div", { className: "w-14 h-14 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-500 flex items-center justify-center mb-4 shadow-sm" }, React.createElement(Icon, { name: "lock", className: "w-7 h-7 text-red-400" })),'
)

# 4. Header logo ⚡
text = text.replace(
    '        React.createElement("div", { className: "w-9 h-9 rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-cyan-400 text-white flex items-center justify-center font-black text-sm shadow-glow-blue" },\n          "⚡"\n        ),',
    '        React.createElement("div", { className: "w-9 h-9 rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-cyan-400 text-white flex items-center justify-center shadow-glow-blue" },\n          React.createElement(Icon, { name: "zap", className: "w-5 h-5 text-cyan-300" })\n        ),'
)

# 5. Mining Bots card
text = text.replace('{ name: "MRG Miner", chain: "TON", icon: "⚡" }', '{ name: "MRG Miner", chain: "TON", logo: "MRG" }')
text = text.replace('{ name: "ATF Miner", chain: "TON", icon: "🪙" }', '{ name: "ATF Miner", chain: "TON", logo: "ATF" }')
text = text.replace('{ name: "Victor\'s Co", chain: "TON", icon: "🏢" }', '{ name: "Victor\'s Co", chain: "TON", logo: "TON" }')
text = text.replace('{ name: "VyroDrop", chain: "TON", icon: "💧" }', '{ name: "VyroDrop", chain: "TON", logo: "TON" }')
text = text.replace('{ name: "Kynex Net", chain: "KNX", icon: "💎" }', '{ name: "Kynex Net", chain: "KNX", logo: "TON" }')
text = text.replace(
    'React.createElement("span", { className: "text-sm" }, b.icon),',
    'React.createElement(CryptoLogo, { symbol: b.logo, className: "w-4 h-4" }),'
)

# 6. Master icon
text = text.replace('isMaster ? "👑" : `#${accNum}`', 'isMaster ? "HOST" : `#${accNum}`')

# 7. Mining status
text = text.replace('"🟢 Mining"', '"Mining Active"')

# 8. AI models
text = text.replace('{ id: "deepseek", label: "🔮 DeepSeek R1", tag: "32B Reasoning" },', '{ id: "deepseek", label: "DeepSeek R1", tag: "32B Reasoning" },')
text = text.replace('{ id: "groq", label: "⚡ Groq LPU", tag: "700 t/s LPU" },', '{ id: "groq", label: "Groq LPU", tag: "700 t/s LPU" },')
text = text.replace('{ id: "llama", label: "🦙 Meta Llama 3.2", tag: "Fast Edge" },', '{ id: "llama", label: "Meta Llama 3.2", tag: "Fast Edge" },')
text = text.replace('{ id: "gemini", label: "⚡ Gemini Flash", tag: "Google Cloud" },', '{ id: "gemini", label: "Gemini Flash", tag: "Google Cloud" },')
text = text.replace('{ id: "image", label: "🎨 SDXL Image", tag: "Visual Art" }', '{ id: "image", label: "SDXL Image", tag: "Visual Art" }')

# 9. AI message model tag
text = text.replace(
    'm.model && React.createElement("div", { className: "text-[9px] font-mono text-cyan-400 font-bold mb-1 opacity-80" }, `🤖 ${m.model}`),',
    'm.model && React.createElement("div", { className: "text-[9px] font-mono text-cyan-400 font-bold mb-1 opacity-80 flex items-center gap-1" }, React.createElement(Icon, { name: "cpu", className: "w-3 h-3 text-cyan-400" }), m.model),'
)

# 10. AI prompts
text = text.replace('{ label: "📊 Fleet Telemetry", cmd: "Summarize the 18-account fleet status and token accumulation." },', '{ label: "Fleet Telemetry", cmd: "Summarize the 18-account fleet status and token accumulation." },')
text = text.replace('{ label: "👛 Vault Balances", cmd: "Check BNB vault and multi-chain wallet settlements." },', '{ label: "Vault Balances", cmd: "Check BNB vault and multi-chain wallet settlements." },')
text = text.replace('{ label: "🌾 Optimize Mining", cmd: "What is the optimal harvest schedule for MRG and ATF?" }', '{ label: "Optimize Mining", cmd: "What is the optimal harvest schedule for MRG and ATF?" }')

# 11. OTP Auto
text = text.replace('otpAutoPoll ? "⚡ Auto: ON" : "Auto: OFF"', 'otpAutoPoll ? "Auto: ON" : "Auto: OFF"')

# 12. OTP Success & Copy
text = text.replace('React.createElement("div", { className: "text-[10px] text-emerald-400 font-bold uppercase tracking-wider" }, "🎉 Active Telegram Code Detected"),', 'React.createElement("div", { className: "text-[10px] text-emerald-400 font-bold uppercase tracking-wider" }, "Active Telegram Code Detected"),')
text = text.replace('}, `📋 1-Tap Copy (${otpResult.code})`),', '}, `1-Tap Copy (${otpResult.code})`),')

# 13. OTP warnings & timers
text = text.replace('React.createElement("div", { className: "text-base mb-1" }, "⚠️"),', 'React.createElement(Icon, { name: "alertTriangle", className: "w-5 h-5 text-amber-400 mx-auto mb-1" }),')
text = text.replace('React.createElement("div", { className: "text-base mb-1" }, "⏳"),', 'React.createElement(Icon, { name: "clock", className: "w-5 h-5 text-cyan-400 mx-auto mb-1 animate-spin" }),')

# 14. Ping
text = text.replace('testingMesh ? "Pinging..." : "⚡ Ping All"', 'testingMesh ? "Pinging..." : "Ping All"')

# 15. Host / Node
text = text.replace('isHost ? "Master Host [Primary]" : "Worker Node 🟢"', 'isHost ? "Master Host [Primary]" : "Worker Node [Online]"')

with open('public_admin/admin.html', 'w', encoding='utf-8') as f:
    f.write(text)

with open('public_admin/admin/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('Updated public_admin/admin.html and public_admin/admin/index.html!')
