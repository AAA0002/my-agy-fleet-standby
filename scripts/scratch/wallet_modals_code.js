    // ==========================================================
    // SEND MODAL (REAL WEB3 SIGNING & CLOUD RELAY)
    // ==========================================================
    isSendModalOpen && React.createElement("div", {
      className: "fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 font-sans",
      onClick: () => setIsSendModalOpen(false)
    },
      React.createElement("div", {
        className: `w-full max-w-sm rounded-3xl p-5 shadow-2xl border animate-slide-up ${isDark ? 'bg-dark-900 border-dark-700 text-white' : 'bg-white border-slate-200 text-slate-900'}`,
        onClick: (e) => e.stopPropagation()
      },
        React.createElement("div", { className: "flex items-center justify-between pb-3 mb-3 border-b border-white/10" },
          React.createElement("div", { className: "flex items-center gap-2" },
            React.createElement("span", { className: "w-8 h-8 rounded-xl bg-blue-500/20 text-cyan-400 flex items-center justify-center text-sm font-black border border-blue-500/30" },
              React.createElement(Icon, { name: "arrowUpRight", className: "w-4 h-4" })
            ),
            React.createElement("div", null,
              React.createElement("h3", { className: "font-black text-sm" }, "Send Crypto Assets"),
              React.createElement("span", { className: "text-[10px] text-slate-400 font-mono" }, `From Node #${walletSelectedNode || 1} Non-Custodial Vault`)
            )
          ),
          React.createElement("button", {
            onClick: () => setIsSendModalOpen(false),
            className: "w-7 h-7 rounded-full bg-white/10 text-slate-400 hover:text-white flex items-center justify-center cursor-pointer"
          }, React.createElement(Icon, { name: "x", className: "w-4 h-4" }))
        ),

        React.createElement("form", { onSubmit: handleExecuteSend, className: "space-y-3 font-mono text-xs" },
          // Chain Selector
          React.createElement("div", null,
            React.createElement("label", { className: "text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1" }, "Network"),
            React.createElement("div", { className: "grid grid-cols-5 gap-1 text-[10px] text-center" },
              [
                { id: "ton", label: "TON", token: "TON", chain: "ton" },
                { id: "bsc", label: "BSC", token: "BNB", chain: "bsc" },
                { id: "tron", label: "TRX", token: "TRX", chain: "tron" },
                { id: "sol", label: "SOL", token: "SOL", chain: "sol" },
                { id: "btc", label: "BTC", token: "BTC", chain: "btc" }
              ].map(c => React.createElement("button", {
                key: c.id,
                type: "button",
                onClick: () => setSendForm(prev => ({ ...prev, chain: c.id, token: c.token })),
                className: `py-1.5 rounded-lg font-bold border transition cursor-pointer flex items-center justify-center gap-1 ${
                  sendForm.chain === c.id ? "bg-cyan-500/20 border-cyan-400 text-cyan-300" : `${subCardBg} border-white/5 text-slate-400 hover:border-white/20`
                }`
              },
                React.createElement(CryptoLogo, { chain: c.chain, symbol: c.token, className: "w-3 h-3" }),
                c.label
              ))
            )
          ),

          // Recipient Address Input
          React.createElement("div", null,
            React.createElement("div", { className: "flex items-center justify-between mb-1" },
              React.createElement("label", { className: "text-[10px] font-bold text-slate-400 uppercase tracking-wider" }, "Recipient Address"),
              ADDRESS_VALIDATORS[sendForm.chain](sendForm.recipient.trim()) && React.createElement("span", { className: "text-[10px] text-emerald-400 font-bold flex items-center gap-0.5" },
                React.createElement(Icon, { name: "check", className: "w-3 h-3" }),
                "Valid Format"
              )
            ),
            React.createElement("input", {
              type: "text",
              value: sendForm.recipient,
              onChange: (e) => setSendForm(prev => ({ ...prev, recipient: e.target.value })),
              placeholder: `Enter ${sendForm.chain.toUpperCase()} address...`,
              className: `w-full px-3 py-2 border rounded-xl text-xs font-mono outline-none ${
                sendForm.recipient && !ADDRESS_VALIDATORS[sendForm.chain](sendForm.recipient.trim())
                  ? "border-rose-500 bg-rose-500/10 text-rose-300"
                  : (isDark ? 'bg-dark-850 border-dark-700 text-white' : 'bg-slate-50 border-slate-200 text-slate-900')
              }`
            })
          ),

          // Amount Input
          React.createElement("div", null,
            React.createElement("div", { className: "flex items-center justify-between mb-1" },
              React.createElement("label", { className: "text-[10px] font-bold text-slate-400 uppercase tracking-wider" }, `Amount (${sendForm.token})`),
              React.createElement("button", {
                type: "button",
                onClick: () => {
                  const tok = getTokensForNode(walletSelectedNode).find(t => t.chain === sendForm.chain && t.symbol === sendForm.token);
                  if (tok) setSendForm(prev => ({ ...prev, amount: String(tok.balance) }));
                },
                className: "text-[10px] text-cyan-400 font-bold hover:underline cursor-pointer"
              }, "MAX")
            ),
            React.createElement("input", {
              type: "number",
              step: "any",
              value: sendForm.amount,
              onChange: (e) => setSendForm(prev => ({ ...prev, amount: e.target.value })),
              placeholder: "0.00",
              className: `w-full px-3 py-2 border rounded-xl text-xs font-mono font-bold outline-none ${isDark ? 'bg-dark-850 border-dark-700 text-white' : 'bg-slate-50 border-slate-200 text-slate-900'}`
            })
          ),

          // Memo / Destination Tag
          React.createElement("div", null,
            React.createElement("label", { className: "text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1" }, "Memo / Tag (Optional)"),
            React.createElement("input", {
              type: "text",
              value: sendForm.memo,
              onChange: (e) => setSendForm(prev => ({ ...prev, memo: e.target.value })),
              placeholder: "Required for Central Exchanges (e.g. Binance)...",
              className: `w-full px-3 py-2 border rounded-xl text-xs font-mono outline-none ${isDark ? 'bg-dark-850 border-dark-700 text-white' : 'bg-slate-50 border-slate-200 text-slate-900'}`
            })
          ),

          // Fee Estimate Box
          React.createElement("div", { className: `p-2 rounded-xl border flex items-center justify-between text-[11px] ${subCardBg}` },
            React.createElement("span", { className: "text-slate-400" }, "Est. Network Gas Fee:"),
            React.createElement("span", { className: "text-emerald-400 font-bold" },
              sendForm.chain === "ton" ? "~0.005 TON (~$0.01)" : (sendForm.chain === "bsc" ? "~0.0003 BNB (~$0.22)" : "~$0.05")
            )
          ),

          // 1-Tap Tonkeeper Signing Link (if TON)
          sendForm.chain === "ton" && sendForm.recipient && parseFloat(sendForm.amount) > 0 && React.createElement("a", {
            href: `https://app.tonkeeper.com/transfer/${sendForm.recipient}?amount=${Math.round(parseFloat(sendForm.amount) * 1e9)}${sendForm.memo ? `&text=${encodeURIComponent(sendForm.memo)}` : ''}`,
            target: "_blank",
            rel: "noopener noreferrer",
            className: "w-full py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs flex items-center justify-center gap-2 cursor-pointer shadow-glow-blue transition active:scale-95"
          },
            React.createElement(CryptoLogo, { chain: "ton", symbol: "TON", className: "w-4 h-4" }),
            "Open & Sign in Tonkeeper (Phone)"
          ),

          // Submit Cloud Relay Button
          React.createElement("button", {
            type: "submit",
            disabled: sendForm.loading,
            className: "w-full py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-bold rounded-xl text-xs shadow-glow-blue transition cursor-pointer flex items-center justify-center gap-2"
          },
            sendForm.loading ? "Broadcasting to Cloud..." : "Broadcast via Cloud Cluster Relay"
          )
        )
      )
    ),

    // ==========================================================
    // RECEIVE MODAL
    // ==========================================================
    isReceiveModalOpen && (() => {
      const activeAddress = getNodeAddress(walletSelectedNode, receiveChain);
      const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=${encodeURIComponent(activeAddress)}&bgcolor=ffffff&color=000000&margin=2`;
      return React.createElement("div", {
        className: "fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 font-sans",
        onClick: () => setIsReceiveModalOpen(false)
      },
        React.createElement("div", {
          className: `w-full max-w-sm rounded-3xl p-5 shadow-2xl border animate-slide-up ${isDark ? 'bg-dark-900 border-dark-700 text-white' : 'bg-white border-slate-200 text-slate-900'}`,
          onClick: (e) => e.stopPropagation()
        },
          React.createElement("div", { className: "flex items-center justify-between pb-3 mb-3 border-b border-white/10" },
            React.createElement("div", { className: "flex items-center gap-2" },
              React.createElement("span", { className: "w-8 h-8 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-sm font-black border border-emerald-500/30" },
                React.createElement(Icon, { name: "arrowDownLeft", className: "w-4 h-4" })
              ),
              React.createElement("div", null,
                React.createElement("h3", { className: "font-black text-sm" }, "Deposit & Receive"),
                React.createElement("span", { className: "text-[10px] text-slate-400 font-mono" }, `Node #${walletSelectedNode || 1} Vault`)
              )
            ),
            React.createElement("button", {
              onClick: () => setIsReceiveModalOpen(false),
              className: "w-7 h-7 rounded-full bg-white/10 text-slate-400 hover:text-white flex items-center justify-center cursor-pointer"
            }, React.createElement(Icon, { name: "x", className: "w-4 h-4" }))
          ),

          // Chain Selector Pills
          React.createElement("div", { className: "grid grid-cols-5 gap-1 mb-3 text-[10px] text-center font-mono" },
            [
              { id: "ton", label: "TON", chain: "ton" },
              { id: "bsc", label: "BSC", chain: "bsc" },
              { id: "tron", label: "TRON", chain: "tron" },
              { id: "sol", label: "SOL", chain: "sol" },
              { id: "btc", label: "BTC", chain: "btc" }
            ].map(c => React.createElement("button", {
              key: c.id,
              onClick: () => { setReceiveChain(c.id); haptic("light"); },
              className: `py-1.5 rounded-lg font-bold border transition cursor-pointer flex items-center justify-center gap-1 ${
                receiveChain === c.id ? "bg-emerald-500/20 border-emerald-400 text-emerald-300" : `${subCardBg} border-white/5 text-slate-400 hover:border-white/20`
              }`
            },
              React.createElement(CryptoLogo, { chain: c.chain, symbol: c.label, className: "w-3 h-3" }),
              c.label
            ))
          ),

          // QR Code Card
          React.createElement("div", { className: "p-3 rounded-2xl bg-white flex items-center justify-center shadow-inner my-2" },
            React.createElement("img", {
              src: qrUrl,
              alt: "Deposit Address QR Code",
              className: "w-44 h-44 rounded-xl"
            })
          ),

          // Address Display & Copy
          React.createElement("div", { className: `p-2.5 rounded-xl border my-3 space-y-1 ${subCardBg}` },
            React.createElement("div", { className: "flex items-center justify-between text-[10px] font-mono text-slate-400" },
              React.createElement("span", null, `${receiveChain.toUpperCase()} Deposit Address:`),
              React.createElement("span", { className: "text-emerald-400 font-bold" }, "Direct Custody")
            ),
            React.createElement("div", { className: "flex items-center justify-between font-mono text-xs" },
              React.createElement("span", { className: "truncate text-slate-200 select-all pr-2" }, activeAddress),
              React.createElement("button", {
                onClick: () => copyToClipboard(activeAddress, `Copied ${receiveChain.toUpperCase()} address!`),
                className: "p-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white shrink-0 cursor-pointer transition active:scale-95"
              }, React.createElement(Icon, { name: "copy", className: "w-3.5 h-3.5" }))
            )
          ),

          // Warning & Explorer Link
          React.createElement("div", { className: "space-y-2 font-mono text-xs" },
            React.createElement("div", { className: "p-2 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-[10px] flex items-center gap-1.5" },
              React.createElement(Icon, { name: "shieldCheck", className: "w-3 h-3 text-amber-400 shrink-0" }),
              React.createElement("span", null, `Deposit only ${receiveChain.toUpperCase()} assets to this address. Cross-chain loss is irreversible.`)
            ),
            React.createElement("a", {
              href: EXPLORER_URLS[receiveChain](activeAddress),
              target: "_blank",
              rel: "noopener noreferrer",
              className: "w-full py-2 bg-white/10 hover:bg-white/20 text-slate-300 font-bold rounded-xl text-xs transition flex items-center justify-center gap-1.5 cursor-pointer"
            },
              React.createElement("span", null, `View on ${receiveChain.toUpperCase()} Explorer`),
              React.createElement(Icon, { name: "externalLink", className: "w-3 h-3" })
            )
          )
        )
      );
    })(),

    // ==========================================================
    // KEYS VAULT MODAL (SECRET PHRASE & ALL CHAINS)
    // ==========================================================
    isKeysModalOpen && (() => {
      const activeIdx = walletSelectedNode || 1;
      const keys = getNodeKeys(activeIdx);
      const mnemonicWords = keys.ton_mnemonic ? keys.ton_mnemonic.trim().split(/\s+/) : [];

      return React.createElement("div", {
        className: "fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-md p-4 font-sans",
        onClick: () => setIsKeysModalOpen(false)
      },
        React.createElement("div", {
          className: `w-full max-w-sm rounded-3xl p-5 shadow-2xl border max-h-[90vh] overflow-y-auto animate-slide-up ${isDark ? 'bg-dark-900 border-dark-700 text-white' : 'bg-white border-slate-200 text-slate-900'}`,
          onClick: (e) => e.stopPropagation()
        },
          React.createElement("div", { className: "flex items-center justify-between pb-3 mb-3 border-b border-white/10" },
            React.createElement("div", { className: "flex items-center gap-2" },
              React.createElement("span", { className: "w-8 h-8 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center text-sm font-black border border-amber-500/30" },
                React.createElement(Icon, { name: "key", className: "w-4 h-4" })
              ),
              React.createElement("div", null,
                React.createElement("h3", { className: "font-black text-sm" }, "Non-Custodial Cryptographic Keys"),
                React.createElement("span", { className: "text-[10px] text-slate-400 font-mono" }, `Node #${activeIdx} · ${cleanName(DEFAULT_FLEET[activeIdx - 1], activeIdx - 1)}`)
              )
            ),
            React.createElement("button", {
              onClick: () => setIsKeysModalOpen(false),
              className: "w-7 h-7 rounded-full bg-white/10 text-slate-400 hover:text-white flex items-center justify-center cursor-pointer"
            }, React.createElement(Icon, { name: "x", className: "w-4 h-4" }))
          ),

          // Security Alert Banner
          React.createElement("div", { className: "p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-[10px] font-mono leading-relaxed mb-3 flex items-start gap-1.5" },
            React.createElement(Icon, { name: "shieldCheck", className: "w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" }),
            React.createElement("span", null, "NEVER share private keys or seed phrases with anyone. Antigravity stores keys in non-custodial local state.")
          ),

          // Reveal Toggle Button
          React.createElement("button", {
            onClick: () => { setKeysRevealed(prev => !prev); haptic("medium"); },
            className: `w-full py-2.5 rounded-xl font-bold font-mono text-xs flex items-center justify-center gap-2 transition cursor-pointer mb-3 border ${
              keysRevealed ? "bg-rose-600/20 text-rose-300 border-rose-500/50" : "bg-cyan-600/20 text-cyan-300 border-cyan-500/50"
            }`
          },
            React.createElement(Icon, { name: keysRevealed ? "eyeOff" : "eye", className: "w-4 h-4" }),
            keysRevealed ? "Hide Confidential Credentials" : "Reveal 24-Word Seed & Private Keys"
          ),

          !keysRevealed ? React.createElement("div", { className: `p-6 rounded-2xl border text-center font-mono text-xs text-slate-400 ${subCardBg}` },
            React.createElement(Icon, { name: "shieldCheck", className: "w-8 h-8 text-cyan-400 mx-auto mb-2" }),
            "Credentials Encrypted & Hidden",
            React.createElement("div", { className: "text-[10px] text-slate-500 mt-1" }, "Tap Reveal above to unlock the non-custodial cryptographic vault.")
          ) : React.createElement("div", { className: "space-y-3 font-mono text-xs" },
            // 24-Word TON Seed Phrase
            React.createElement("div", { className: `p-3 rounded-2xl border ${subCardBg}` },
              React.createElement("div", { className: "flex items-center justify-between mb-2" },
                React.createElement("div", { className: "flex items-center gap-1 font-bold text-cyan-400 text-[11px]" },
                  React.createElement(CryptoLogo, { chain: "ton", symbol: "TON", className: "w-3.5 h-3.5" }),
                  React.createElement("span", null, "24-Word TON Seed Mnemonic:")
                ),
                keys.ton_mnemonic && React.createElement("button", {
                  onClick: () => copyToClipboard(keys.ton_mnemonic, "Copied 24-word TON seed!"),
                  className: "text-[10px] text-slate-400 hover:text-white flex items-center gap-1 cursor-pointer"
                },
                  React.createElement(Icon, { name: "copy", className: "w-3 h-3" }),
                  "Copy All"
                )
              ),
              mnemonicWords.length > 0 ? React.createElement("div", { className: "grid grid-cols-3 gap-1 text-[10px]" },
                mnemonicWords.map((wrd, wIdx) => React.createElement("div", {
                  key: wIdx,
                  className: "p-1 rounded bg-black/30 border border-white/5 truncate text-slate-300"
                }, `${wIdx + 1}. ${wrd}`))
              ) : React.createElement("div", { className: "text-[10px] text-slate-400 italic" }, "Master Central / Binance Web3 Vault (Direct Custody)")
            ),

            // EVM / BSC Private Key
            React.createElement("div", { className: `p-2.5 rounded-xl border ${subCardBg}` },
              React.createElement("div", { className: "flex items-center justify-between text-[10px] text-slate-400 mb-1" },
                React.createElement("div", { className: "flex items-center gap-1" },
                  React.createElement(CryptoLogo, { chain: "bsc", symbol: "BNB", className: "w-3 h-3" }),
                  React.createElement("span", null, "BSC / EVM Private Key:")
                ),
                React.createElement("button", { onClick: () => copyToClipboard(keys.evm_key || keys.evm, "Copied BSC Key!") }, React.createElement(Icon, { name: "copy", className: "w-3 h-3 hover:text-white" }))
              ),
              React.createElement("div", { className: "text-[10px] text-slate-300 font-mono truncate" }, keys.evm_key || "Direct Centralized Custody")
            ),

            // TRON Private Key
            React.createElement("div", { className: `p-2.5 rounded-xl border ${subCardBg}` },
              React.createElement("div", { className: "flex items-center justify-between text-[10px] text-slate-400 mb-1" },
                React.createElement("div", { className: "flex items-center gap-1" },
                  React.createElement(CryptoLogo, { chain: "tron", symbol: "TRX", className: "w-3 h-3" }),
                  React.createElement("span", null, "TRON Private Key:")
                ),
                React.createElement("button", { onClick: () => copyToClipboard(keys.tron_key || keys.tron, "Copied TRON Key!") }, React.createElement(Icon, { name: "copy", className: "w-3 h-3 hover:text-white" }))
              ),
              React.createElement("div", { className: "text-[10px] text-slate-300 font-mono truncate" }, keys.tron_key || "Direct Centralized Custody")
            ),

            // Solana Secret Key
            React.createElement("div", { className: `p-2.5 rounded-xl border ${subCardBg}` },
              React.createElement("div", { className: "flex items-center justify-between text-[10px] text-slate-400 mb-1" },
                React.createElement("div", { className: "flex items-center gap-1" },
                  React.createElement(CryptoLogo, { chain: "sol", symbol: "SOL", className: "w-3 h-3" }),
                  React.createElement("span", null, "Solana Secret Key:")
                ),
                React.createElement("button", { onClick: () => copyToClipboard(keys.sol_key || keys.sol, "Copied Solana Key!") }, React.createElement(Icon, { name: "copy", className: "w-3 h-3 hover:text-white" }))
              ),
              React.createElement("div", { className: "text-[10px] text-slate-300 font-mono truncate" }, keys.sol_key || "Direct Centralized Custody")
            ),

            // Bitcoin Key
            React.createElement("div", { className: `p-2.5 rounded-xl border ${subCardBg}` },
              React.createElement("div", { className: "flex items-center justify-between text-[10px] text-slate-400 mb-1" },
                React.createElement("div", { className: "flex items-center gap-1" },
                  React.createElement(CryptoLogo, { chain: "btc", symbol: "BTC", className: "w-3 h-3" }),
                  React.createElement("span", null, "Bitcoin Taproot Key:")
                ),
                React.createElement("button", { onClick: () => copyToClipboard(keys.btc_key || keys.btc, "Copied Bitcoin Key!") }, React.createElement(Icon, { name: "copy", className: "w-3 h-3 hover:text-white" }))
              ),
              React.createElement("div", { className: "text-[10px] text-slate-300 font-mono truncate" }, keys.btc_key || "Direct Centralized Custody")
            )
          ),

          // Download JSON Vault
          React.createElement("button", {
            onClick: exportFleetVaultJson,
            className: "w-full py-2 bg-white/10 hover:bg-white/20 text-slate-300 font-bold rounded-xl text-xs transition flex items-center justify-center gap-1.5 cursor-pointer mt-3 font-mono"
          },
            React.createElement(Icon, { name: "receipt", className: "w-3.5 h-3.5 text-cyan-400" }),
            "Download Encrypted JSON Vault Backup"
          )
        )
      );
    })()
