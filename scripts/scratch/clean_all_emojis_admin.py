with open('public_admin/admin.html', 'r') as f:
    text = f.read()

# Replace bot names emojis
text = text.replace('["⚡ MRG", "🪙 ATF", "🏢 Victor", "💎 Kynex"]', '["MRG Pool", "ATF Farm", "Victor Corp", "Kynex Net"]')

# Replace add modal emoji
text = text.replace('React.createElement("span", { className: "w-8 h-8 rounded-xl bg-blue-500/20 text-cyan-400 flex items-center justify-center text-sm font-black border border-blue-500/30" }, "➕")', 'React.createElement("span", { className: "w-8 h-8 rounded-xl bg-blue-500/20 text-cyan-400 flex items-center justify-center border border-blue-500/30" }, React.createElement(Icon, { name: "plus", className: "w-4 h-4" }))')

# Replace success emoji in add modal
text = text.replace('React.createElement("div", { className: "text-3xl" }, "🎉")', 'React.createElement(Icon, { name: "shieldCheck", className: "w-10 h-10 text-emerald-400 mx-auto mb-2" })')

# Replace Master Host emoji
text = text.replace('"Master Host 👑"', '"Master Host [Primary]"')

with open('public_admin/admin.html', 'w') as f:
    f.write(text)

with open('public_admin/admin/index.html', 'w') as f:
    f.write(text)

print("Cleaned remaining emojis from admin.html and admin/index.html")
