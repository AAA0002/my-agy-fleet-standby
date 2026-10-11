with open('public_admin/login.html', 'r') as f:
    html = f.read()

# Replace header logo emoji ⚡ with SVG lightning
html = html.replace(
    '<div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center text-white text-lg font-black shadow-glow-blue border border-cyan-400/40">\n            ⚡\n          </div>',
    '<div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center text-white shadow-glow-blue border border-cyan-400/40">\n            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" fill="currentColor"/></svg>\n          </div>'
)

# Replace tab emojis
html = html.replace('<span>💼</span>\n          <span>Admin Console</span>', '<svg class="w-3.5 h-3.5 text-cyan-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="20" height="14" x="2" y="7" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>\n          <span>Admin Console</span>')
html = html.replace('<span>🤖</span>\n          <span>Telegram Bot</span>', '<svg class="w-3.5 h-3.5 text-blue-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 8V4H8m8 0h-4M4 8h16a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2zm5 5h.01m6 0h.01"/></svg>\n          <span>Telegram Bot</span>')

html = html.replace('<span>📱</span>\n        <span>1-Tap QR Login</span>', '<svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="5" height="5" x="3" y="3" rx="1"/><rect width="5" height="5" x="16" y="3" rx="1"/><rect width="5" height="5" x="3" y="16" rx="1"/><path d="M21 16h-3a2 2 0 0 0-2 2v3"/><path d="M12 7v3a2 2 0 0 1-2 2H7"/></svg>\n        <span>1-Tap QR Login</span>')
html = html.replace('<span>📨</span>\n        <span>Direct Code Verification</span>', '<svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m15.5 7.5 2.3 2.3a1 1 0 0 0 1.4 0l2.1-2.1a1 1 0 0 0 0-1.4L19 4M21 2l-9.6 9.6a5 5 0 1 0 2.2 2.2L21 6.4V2z"/></svg>\n        <span>Direct Code Verification</span>')
html = html.replace('<span>📊</span>\n        <span>Fleet Matrix (18)</span>', '<svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="20" height="8" x="2" y="2" rx="2" ry="2"/><rect width="20" height="8" x="2" y="14" rx="2" ry="2"/><line x1="6" x2="6.01" y1="6" y2="6"/><line x1="6" x2="6.01" y1="18" y2="18"/></svg>\n        <span>Fleet Matrix (18)</span>')

# Replace form header emojis
html = html.replace('<span>📱</span> Direct QR Telegram Session Link', '<svg class="w-4 h-4 text-cyan-400 inline-block mr-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="5" height="5" x="3" y="3" rx="1"/><rect width="5" height="5" x="16" y="3" rx="1"/><rect width="5" height="5" x="3" y="16" rx="1"/></svg> Direct QR Telegram Session Link')
html = html.replace('<span>📨</span> Direct SMS / Telegram OTP Verification', '<svg class="w-4 h-4 text-cyan-400 inline-block mr-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m15.5 7.5 2.3 2.3a1 1 0 0 0 1.4 0l2.1-2.1a1 1 0 0 0 0-1.4L19 4M21 2l-9.6 9.6a5 5 0 1 0 2.2 2.2L21 6.4V2z"/></svg> Direct SMS / Telegram OTP Verification')
html = html.replace('<span>📊</span> 18-Node Fleet Session Telemetry Matrix', '<svg class="w-4 h-4 text-cyan-400 inline-block mr-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="20" height="8" x="2" y="2" rx="2" ry="2"/><rect width="20" height="8" x="2" y="14" rx="2" ry="2"/></svg> 18-Node Fleet Session Telemetry Matrix')

# Replace options 👑
html = html.replace('Node #01 — Arif Hossain 👑', 'Node #01 — Arif Hossain [Master Host]')
html = html.replace('Node #01 — Arif Hossain (+8801317342850) 👑', 'Node #01 — Arif Hossain (+8801317342850) [Master Host]')
html = html.replace('${a.index === 1 ? \'<span class="text-[8px] bg-amber-500/20 text-amber-300 px-1 py-0.2 rounded font-bold">👑 Master</span>\' : \'\'}', '${a.index === 1 ? \'<span class="text-[8px] bg-amber-500/20 text-amber-300 px-1 py-0.2 rounded font-bold">MASTER</span>\' : \'\'}')

# Replace link button emojis
html = html.replace('<span>🔗</span>\n            <span>Link Device on This Phone (1-Tap) ↗️</span>', '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6m4-3h6v6m-11 5L21 3"/></svg>\n            <span>Link Device on This Phone (1-Tap)</span>')

# Replace tip emoji
html = html.replace('<span>💡</span>', '<svg class="w-4 h-4 text-cyan-400 inline-block mr-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>')
html = html.replace('Settings ➔ Devices ➔ Link Desktop Device', 'Settings -> Devices -> Link Desktop Device')

# Replace success emojis
html = html.replace('<span class="text-2xl">🎉</span>', '<svg class="w-8 h-8 text-emerald-400 mx-auto" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>')
html = html.replace('🎉 Node #${nodeIdx} Linked & Authenticated!', 'Node #${nodeIdx} Linked & Authenticated Successfully!')
html = html.replace('🎉 Node #${nodeIdx}', 'Node #${nodeIdx}')
html = html.replace('🟢 Session Active & Farming in Cloud', 'ONLINE | Cloud 24/7 Farming Active')
html = html.replace('🟢 Online', 'ONLINE')
html = html.replace('⚡ Relink', 'Relink')
html = html.replace('🔄 Refresh Matrix', 'Refresh Matrix')
html = html.replace('📨 Request Code', 'Request Code')
html = html.replace('⚡ Verify Code & Link Node', 'Verify Code & Link Node')

with open('public_admin/login.html', 'w') as f:
    f.write(html)

with open('public_admin/login/index.html', 'w') as f:
    f.write(html)

print("Updated login.html and login/index.html with professional SVG icons!")
