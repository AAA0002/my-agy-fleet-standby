    // ==========================================================
    // TAB 2: REAL NON-CUSTODIAL WEB3 MULTI-CHAIN WALLET
    // ==========================================================
    activeTab === "wallets" && (() => {
      const activeNodeIdx = walletSelectedNode || 1;
      const activeNodeAcc = fleet.find(a => a.index === activeNodeIdx) || DEFAULT_FLEET[activeNodeIdx - 1] || DEFAULT_FLEET[0];
      const activeNodeName = cleanName(activeNodeAcc, activeNodeIdx - 1);
      const activeNodePhone = activeNodeAcc?.phone || KNOWN_PHONES_BY_INDEX[activeNodeIdx] || "Cloud Node";
      
      const allTokens = getTokensForNode(activeNodeIdx);
      const filteredTokens = walletChainFilter === "all" ? allTokens : allTokens.filter(t => t.chain === walletChainFilter);
      const totalNetWorthUsd = allTokens.reduce((s, t) => s + (t.usdVal || 0), 0);
      const totalNetWorthLocal = totalNetWorthUsd * currencyRate;
      
      const primaryTonAddr = getNodeAddress(activeNodeIdx, "ton");
      const shortTonAddr = primaryTonAddr ? (primaryTonAddr.slice(0, 6) + "..." + primaryTonAddr.slice(-4)) : "Not Configured";
      const keys = getNodeKeys(activeNodeIdx);
      const mnemonicWords = keys.ton_mnemonic ? keys.ton_mnemonic.trim().split(/\s+/) : [];

      return React.createElement("div", { className: "animate-entrance space-y-3 pb-6 font-sans" },
        // 1. Executive Master Net Worth Card (Real On-Chain Status)
        React.createElement("div", { className: `rounded-3xl p-5 border shadow-xl relative overflow-hidden ${cardBg}` },
          // Top row: Header & Real Connection Status
          React.createElement("div", { className: "flex items-center justify-between mb-3" },
            React.createElement("div", { className: "flex items-center gap-2" },
              React.createElement(CryptoLogo, { chain: "ton", symbol: "TON", className: "w-8 h-8 shadow-glow-blue" }),
              React.createElement("div", null,
                React.createElement("div", { className: "text-[10px] font-mono uppercase tracking-wider text-cyan-400 font-bold" },
                  `Node #${activeNodeIdx} Non-Custodial Signer`
                ),
                React.createElement("h2", { className: `text-sm font-black truncate max-w-[190px] ${isDark ? 'text-white' : 'text-slate-900'}` }, activeNodeName)
              )
            ),
            React.createElement("button", {
              onClick: () => { fetchLiveOnChainBalances(activeNodeIdx); haptic("light"); },
              className: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 hover:border-emerald-500/60 text-[10px] font-bold px-2.5 py-1 rounded-full flex items-center gap-1.5 font-mono cursor-pointer transition"
            },
              React.createElement("span", { className: `w-1.5 h-1.5 rounded-full bg-emerald-400 ${liveBalances.syncing ? 'animate-spin' : 'animate-pulse'}` }),
              liveBalances.syncing ? "SYNCING RPC..." : "LIVE ON-CHAIN RPC"
            )
          ),

          // Total Portfolio Valuation
          React.createElement("div", { className: "my-2" },
            React.createElement("div", { className: "text-[10px] text-slate-400 uppercase font-mono font-bold tracking-wider flex items-center justify-between" },
              React.createElement("span", null, "Total Portfolio Valuation"),
              liveBalances.lastSynced && React.createElement("span", { className: "text-[9px] text-slate-500 font-mono" }, `Synced: ${liveBalances.lastSynced}`)
            ),
            React.createElement("div", { className: `text-3xl font-black font-mono tracking-tight my-1 ${isDark ? 'text-white' : 'text-slate-900'}` },
              `${currencySymbol}${totalNetWorthLocal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
            ),
            React.createElement("div", { className: "flex items-center gap-2 text-xs font-mono" },
              React.createElement("span", { className: "text-slate-400" }, `≈ $${totalNetWorthUsd.toFixed(2)} USD`),
              React.createElement("span", { className: "text-slate-500" }, "|"),
              React.createElement("span", { className: "text-cyan-400 font-bold" }, `BDT ${(totalNetWorthUsd * 122.5).toLocaleString(undefined, { maximumFractionDigits: 0 })}`),
              React.createElement("span", { className: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] px-1.5 py-0.2 rounded font-bold ml-auto" }, "Real On-Chain")
            )
          ),

          // Primary TON address preview with quick explorer & copy
          React.createElement("div", { className: `mt-3 p-2 rounded-xl border flex items-center justify-between text-xs font-mono ${subCardBg}` },
            React.createElement("div", { className: "flex items-center gap-1.5 truncate" },
              React.createElement("span", { className: "text-cyan-400 text-[10px] font-bold" }, "TON Address:"),
              React.createElement("span", { className: "truncate text-slate-300 text-[11px]" }, shortTonAddr)
            ),
            React.createElement("div", { className: "flex items-center gap-1 shrink-0" },
              React.createElement("button", {
                onClick: () => copyToClipboard(primaryTonAddr, "Copied TON Address!"),
                className: "p-1 text-slate-400 hover:text-cyan-400 transition cursor-pointer"
              }, React.createElement(Icon, { name: "copy", className: "w-3.5 h-3.5" })),
              React.createElement("a", {
                href: EXPLORER_URLS.ton(primaryTonAddr),
                target: "_blank",
                rel: "noopener noreferrer",
                className: "p-1 text-slate-400 hover:text-cyan-400 transition"
              }, React.createElement(Icon, { name: "externalLink", className: "w-3.5 h-3.5" }))
            )
          ),

          // Action Dock: Send, Receive, Secret Phrase, Export
          React.createElement("div", { className: "grid grid-cols-4 gap-2 mt-4 pt-3 border-t border-white/10" },
            React.createElement("button", {
              onClick: () => {
                setSendForm({ chain: "ton", token: "TON", recipient: "", amount: "", memo: "", loading: false, result: null });
                setIsSendModalOpen(true);
                haptic("light");
              },
              className: "flex flex-col items-center justify-center gap-1 p-2.5 rounded-2xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-glow-blue transition active:scale-95 cursor-pointer"
            },
              React.createElement(Icon, { name: "arrowUpRight", className: "w-4 h-4" }),
              React.createElement("span", { className: "text-[10px]" }, "Send")
            ),
            React.createElement("button", {
              onClick: () => {
                setReceiveChain("ton");
                setIsReceiveModalOpen(true);
                haptic("light");
              },
              className: "flex flex-col items-center justify-center gap-1 p-2.5 rounded-2xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-glow-emerald transition active:scale-95 cursor-pointer"
            },
              React.createElement(Icon, { name: "arrowDownLeft", className: "w-4 h-4" }),
              React.createElement("span", { className: "text-[10px]" }, "Receive")
            ),
            React.createElement("button", {
              onClick: () => {
                setIsKeysModalOpen(true);
                haptic("medium");
              },
              className: `flex flex-col items-center justify-center gap-1 p-2.5 rounded-2xl border ${subCardBg} hover:border-cyan-500/50 text-slate-200 font-bold text-xs transition active:scale-95 cursor-pointer`
            },
              React.createElement(Icon, { name: "key", className: "w-4 h-4 text-amber-400" }),
              React.createElement("span", { className: "text-[10px]" }, "Secret Phrase")
            ),
            React.createElement("button", {
              onClick: exportFleetMatrixCsv,
              className: `flex flex-col items-center justify-center gap-1 p-2.5 rounded-2xl border ${subCardBg} hover:border-cyan-500/50 text-slate-200 font-bold text-xs transition active:scale-95 cursor-pointer`
            },
              React.createElement(Icon, { name: "receipt", className: "w-4 h-4 text-cyan-400" }),
              React.createElement("span", { className: "text-[10px]" }, "Export CSV")
            )
          )
        ),

        // 2. Real Non-Custodial Secret Phrase Connection Card
        React.createElement("div", { className: `rounded-2xl p-4 border ${subCardBg}` },
          React.createElement("div", { className: "flex items-center justify-between mb-2" },
            React.createElement("div", { className: "flex items-center gap-2" },
              React.createElement("span", { className: "p-1.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400" },
                React.createElement(Icon, { name: "key", className: "w-4 h-4" })
              ),
              React.createElement("div", null,
                React.createElement("div", { className: "font-black text-xs text-white" }, "Non-Custodial Account Connection"),
                React.createElement("div", { className: "text-[10px] text-slate-400 font-mono" },
                  keys.ton_mnemonic ? "24-Word Mnemonic Loaded (BIP39 Derivation)" : "Binance Custody Account Bound"
                )
              )
            ),
            React.createElement("button", {
              onClick: () => { setKeysRevealed(prev => !prev); haptic("medium"); },
              className: `px-2.5 py-1 rounded-xl text-[10px] font-mono font-bold transition flex items-center gap-1 cursor-pointer border ${
                keysRevealed ? "bg-rose-500/20 text-rose-300 border-rose-500/40" : "bg-cyan-500/20 text-cyan-300 border-cyan-500/40"
              }`
            },
              React.createElement(Icon, { name: keysRevealed ? "eyeOff" : "eye", className: "w-3 h-3" }),
              keysRevealed ? "Hide Secret Phrase" : "Show Secret Phrase"
            )
          ),

          // If revealed, display real 24 words
          keysRevealed && React.createElement("div", { className: "mt-3 pt-3 border-t border-white/10 space-y-2.5 animate-slide-up" },
            mnemonicWords.length > 0 ? React.createElement("div", null,
              React.createElement("div", { className: "flex items-center justify-between text-[10px] font-mono text-slate-400 mb-1.5" },
                React.createElement("span", null, `Node #${activeIdx} Secret Recovery Phrase (24 Words):`),
                React.createElement("button", {
                  onClick: () => copyToClipboard(keys.ton_mnemonic, "Copied 24-Word Recovery Phrase!"),
                  className: "text-cyan-400 hover:text-white font-bold flex items-center gap-1 cursor-pointer"
                },
                  React.createElement(Icon, { name: "copy", className: "w-3 h-3" }),
                  "Copy All 24 Words"
                )
              ),
              React.createElement("div", { className: "grid grid-cols-3 gap-1.5 font-mono text-[10px]" },
                mnemonicWords.map((word, wIdx) => React.createElement("div", {
                  key: wIdx,
                  className: "p-1.5 rounded-lg bg-black/40 border border-white/10 text-slate-200 truncate flex items-center gap-1"
                },
                  React.createElement("span", { className: "text-slate-500 text-[9px] w-4" }, `${wIdx + 1}.`),
                  React.createElement("span", { className: "font-bold" }, word)
                ))
              ),
              React.createElement("div", { className: "mt-2 p-2 rounded-xl bg-blue-500/10 border border-blue-500/20 text-[10px] font-mono text-cyan-300 flex items-center justify-between" },
                React.createElement("span", null, "Derivation Path: m/44'/607'/0' (TON Standard)"),
                React.createElement("a", {
                  href: `https://app.tonkeeper.com/transfer/${primaryTonAddr}`,
                  target: "_blank",
                  rel: "noopener noreferrer",
                  className: "underline font-bold text-cyan-400 hover:text-white"
                }, "Connect Tonkeeper ->")
              )
            ) : React.createElement("div", { className: "text-xs font-mono text-slate-400 p-2" },
              keys.evm_key || "Direct Centralized Custody: Mapped to Binance Main Deposit Address."
            )
          )
        ),

        // 3. Account Node Switcher (Horizontal Pill Scroll for all 18 Nodes)
        React.createElement("div", { className: "space-y-1.5" },
          React.createElement("div", { className: "flex items-center justify-between px-1" },
            React.createElement("span", { className: "text-[10px] font-bold text-slate-400 uppercase tracking-wider font-mono" }, "Switch Fleet Account Node:"),
            React.createElement("span", { className: "text-[10px] text-cyan-400 font-mono font-bold" }, `Active Node #${activeNodeIdx} (of 18)`)
          ),
          React.createElement("div", { className: "flex items-center gap-1.5 overflow-x-auto pb-1" },
            fleet.map((acc, idx) => {
              const accNum = acc.index || (idx + 1);
              const isSelected = walletSelectedNode === accNum;
              const isHost = accNum === 1;
              return React.createElement("button", {
                key: accNum,
                onClick: () => { setWalletSelectedNode(accNum); haptic("light"); },
                className: `px-3 py-1.5 rounded-xl text-xs font-mono font-bold shrink-0 transition cursor-pointer flex items-center gap-1 border ${
                  isSelected
                    ? "bg-cyan-500/20 text-cyan-300 border-cyan-400 shadow-glow-cyan"
                    : `${subCardBg} text-slate-400 border-white/5 hover:border-white/20`
                }`
              },
                isHost ? React.createElement(Icon, { name: "crown", className: "w-3 h-3 text-amber-400" }) : `#${accNum}`,
                React.createElement("span", { className: "max-w-[70px] truncate" }, cleanName(acc, idx))
              );
            })
          )
        ),

        // 4. Sub-Tab Switcher: [ Token Assets | 18-Node Matrix | On-Chain Explorers ]
        React.createElement("div", { className: `p-1 rounded-2xl border flex items-center gap-1 text-xs font-mono ${subCardBg}` },
          [
            { id: "assets", label: "Token Assets", icon: "wallet", count: allTokens.length },
            { id: "matrix", label: "18-Node Matrix", icon: "server", count: 18 },
            { id: "activity", label: "Live Explorers", icon: "activity", count: 5 }
          ].map(tab => React.createElement("button", {
            key: tab.id,
            onClick: () => { setWalletSubTab(tab.id); haptic("light"); },
            className: `flex-1 py-1.5 rounded-xl font-bold transition text-center cursor-pointer flex items-center justify-center gap-1.5 ${
              walletSubTab === tab.id
                ? (isDark ? "bg-white/10 text-cyan-400 shadow-sm" : "bg-white text-blue-600 shadow-sm")
                : "text-slate-400 hover:text-slate-200"
            }`
          },
            React.createElement(Icon, { name: tab.icon, className: "w-3.5 h-3.5" }),
            `${tab.label} (${tab.count})`
          ))
        ),

        // 5. SUB-TAB 1: ASSETS
        walletSubTab === "assets" && React.createElement("div", { className: "space-y-3" },
          // Chain Filter Bar
          React.createElement("div", { className: "flex items-center gap-1.5 overflow-x-auto pb-1" },
            [
              { id: "all", label: "All Chains", icon: "server" },
              { id: "ton", label: "TON", chain: "ton" },
              { id: "bsc", label: "BSC", chain: "bsc" },
              { id: "tron", label: "TRON", chain: "tron" },
              { id: "sol", label: "Solana", chain: "sol" },
              { id: "btc", label: "Bitcoin", chain: "btc" }
            ].map(chain => React.createElement("button", {
              key: chain.id,
              onClick: () => { setWalletChainFilter(chain.id); haptic("light"); },
              className: `px-2.5 py-1 rounded-lg text-[11px] font-mono font-bold shrink-0 transition cursor-pointer flex items-center gap-1 border ${
                walletChainFilter === chain.id
                  ? "bg-cyan-500/20 text-cyan-300 border-cyan-400/50"
                  : `${subCardBg} text-slate-400 border-transparent hover:border-white/10`
              }`
            },
              chain.chain ? React.createElement(CryptoLogo, { chain: chain.chain, symbol: chain.label, className: "w-3.5 h-3.5" }) : React.createElement(Icon, { name: chain.icon, className: "w-3 h-3" }),
              chain.label
            ))
          ),

          // Token Assets Cards List
          React.createElement("div", { className: "space-y-2" },
            filteredTokens.map((tok, tIdx) => {
              const tokValLocal = (tok.usdVal || 0) * currencyRate;
              return React.createElement("div", {
                key: `${tok.chain}-${tok.symbol}-${tIdx}`,
                className: `p-3 rounded-2xl border transition hover:border-cyan-500/40 ${cardBg}`
              },
                React.createElement("div", { className: "flex items-center justify-between" },
                  // Left: Icon & Name
                  React.createElement("div", { className: "flex items-center gap-2.5" },
                    React.createElement(CryptoLogo, { symbol: tok.symbol, chain: tok.chain, className: "w-9 h-9" }),
                    React.createElement("div", null,
                      React.createElement("div", { className: "flex items-center gap-1.5" },
                        React.createElement("span", { className: `font-black text-xs ${isDark ? 'text-white' : 'text-slate-900'}` }, tok.symbol),
                        React.createElement("span", { className: "text-[9px] font-mono px-1.5 py-0.2 rounded bg-white/5 text-slate-400 border border-white/10" }, tok.chain.toUpperCase()),
                        tok.isLiveRpc && React.createElement("span", { className: "text-[8px] font-mono px-1 py-0.2 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30" }, "LIVE RPC")
                      ),
                      React.createElement("div", { className: "text-[10px] text-slate-400 font-mono truncate max-w-[120px]" }, tok.name)
                    )
                  ),
                  // Right: Balance & Value
                  React.createElement("div", { className: "text-right font-mono" },
                    React.createElement("div", { className: `font-black text-xs ${isDark ? 'text-white' : 'text-slate-900'}` },
                      `${tok.balance.toLocaleString(undefined, { maximumFractionDigits: tok.symbol === 'BTC' ? 6 : 4 })} ${tok.symbol}`
                    ),
                    React.createElement("div", { className: "text-[10px] text-cyan-400 font-bold" },
                      `${currencySymbol}${tokValLocal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                    )
                  )
                ),
                // Sub-row: Price, 24h change & Quick Send/Receive buttons
                React.createElement("div", { className: "flex items-center justify-between mt-2 pt-2 border-t border-white/5 text-[10px] font-mono" },
                  React.createElement("div", { className: "flex items-center gap-1.5" },
                    React.createElement("span", { className: "text-slate-400" }, `$${tok.price < 0.01 ? tok.price.toFixed(5) : tok.price.toFixed(2)}`),
                    React.createElement("span", { className: `font-bold ${tok.isPositive ? 'text-emerald-400' : 'text-rose-400'}` }, tok.change24h)
                  ),
                  React.createElement("div", { className: "flex items-center gap-1.5" },
                    React.createElement("button", {
                      onClick: () => {
                        setSendForm({ chain: tok.chain, token: tok.symbol, recipient: "", amount: "", memo: "", loading: false, result: null });
                        setIsSendModalOpen(true);
                        haptic("light");
                      },
                      className: "px-2.5 py-1 rounded-lg bg-blue-500/10 hover:bg-blue-500/20 text-cyan-400 font-bold border border-blue-500/20 transition cursor-pointer"
                    }, "Send"),
                    React.createElement("button", {
                      onClick: () => {
                        setReceiveChain(tok.chain);
                        setIsReceiveModalOpen(true);
                        haptic("light");
                      },
                      className: "px-2.5 py-1 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 font-bold border border-emerald-500/20 transition cursor-pointer"
                    }, "Receive")
                  )
                )
              );
            })
          )
        ),

        // 6. SUB-TAB 2: 18-NODE MATRIX
        walletSubTab === "matrix" && React.createElement("div", { className: "space-y-3 font-mono text-xs" },
          React.createElement("div", { className: "flex items-center justify-between" },
            React.createElement("div", null,
              React.createElement("h4", { className: `font-black text-xs ${isDark ? 'text-white' : 'text-slate-900'}` }, "18-Node Treasury Matrix"),
              React.createElement("p", { className: "text-[10px] text-slate-400" }, "Multi-Chain on-chain mapping across 5 chains")
            ),
            React.createElement("div", { className: "flex items-center gap-1.5" },
              React.createElement("button", {
                onClick: exportFleetMatrixCsv,
                className: "px-2.5 py-1 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-[10px] transition cursor-pointer"
              }, "CSV"),
              React.createElement("button", {
                onClick: exportFleetVaultJson,
                className: "px-2.5 py-1 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-bold text-[10px] transition cursor-pointer"
              }, "JSON")
            )
          ),
          React.createElement("div", { className: "space-y-2 max-h-[550px] overflow-y-auto pr-1" },
            fleetWallets.map(w => {
              const isSelected = walletSelectedNode === w.index;
              return React.createElement("div", {
                key: `matrix-${w.index}`,
                onClick: () => { setWalletSelectedNode(w.index); haptic("light"); },
                className: `p-3 rounded-2xl border transition cursor-pointer ${isSelected ? "border-cyan-400/80 bg-cyan-500/10" : cardBg}`
              },
                React.createElement("div", { className: "flex items-center justify-between pb-1.5 mb-1.5 border-b border-white/5" },
                  React.createElement("div", { className: "flex items-center gap-2" },
                    React.createElement("span", { className: "w-6 h-6 rounded-lg bg-blue-500/20 text-cyan-400 font-bold flex items-center justify-center text-[10px]" }, `#${w.index}`),
                    React.createElement("span", { className: `font-black text-xs ${isDark ? 'text-white' : 'text-slate-900'}` }, w.name)
                  ),
                  React.createElement("span", { className: "text-[10px] text-cyan-400 font-mono" }, w.phone)
                ),
                React.createElement("div", { className: "space-y-1 text-[10px]" },
                  React.createElement("div", { className: "flex items-center justify-between" },
                    React.createElement("div", { className: "flex items-center gap-1 text-slate-400" },
                      React.createElement(CryptoLogo, { chain: "ton", symbol: "TON", className: "w-3 h-3" }),
                      React.createElement("span", null, "TON:")
                    ),
                    React.createElement("div", { className: "flex items-center gap-1" },
                      React.createElement("span", { className: "text-slate-300 font-mono" }, w.ton ? (w.ton.slice(0, 8) + "..." + w.ton.slice(-4)) : "None"),
                      React.createElement("button", { onClick: (e) => { e.stopPropagation(); copyToClipboard(w.ton, "Copied TON!"); } }, React.createElement(Icon, { name: "copy", className: "w-2.5 h-2.5 text-slate-400 hover:text-white" }))
                    )
                  ),
                  React.createElement("div", { className: "flex items-center justify-between" },
                    React.createElement("div", { className: "flex items-center gap-1 text-slate-400" },
                      React.createElement(CryptoLogo, { chain: "bsc", symbol: "BNB", className: "w-3 h-3" }),
                      React.createElement("span", null, "BSC:")
                    ),
                    React.createElement("div", { className: "flex items-center gap-1" },
                      React.createElement("span", { className: "text-slate-300 font-mono" }, w.evm ? (w.evm.slice(0, 8) + "..." + w.evm.slice(-4)) : "None"),
                      React.createElement("button", { onClick: (e) => { e.stopPropagation(); copyToClipboard(w.evm, "Copied BSC!"); } }, React.createElement(Icon, { name: "copy", className: "w-2.5 h-2.5 text-slate-400 hover:text-white" }))
                    )
                  ),
                  React.createElement("div", { className: "flex items-center justify-between" },
                    React.createElement("div", { className: "flex items-center gap-1 text-slate-400" },
                      React.createElement(CryptoLogo, { chain: "tron", symbol: "TRX", className: "w-3 h-3" }),
                      React.createElement("span", null, "TRON:")
                    ),
                    React.createElement("div", { className: "flex items-center gap-1" },
                      React.createElement("span", { className: "text-slate-300 font-mono" }, w.tron ? (w.tron.slice(0, 8) + "..." + w.tron.slice(-4)) : "None"),
                      React.createElement("button", { onClick: (e) => { e.stopPropagation(); copyToClipboard(w.tron, "Copied TRON!"); } }, React.createElement(Icon, { name: "copy", className: "w-2.5 h-2.5 text-slate-400 hover:text-white" }))
                    )
                  ),
                  React.createElement("div", { className: "flex items-center justify-between" },
                    React.createElement("div", { className: "flex items-center gap-1 text-slate-400" },
                      React.createElement(CryptoLogo, { chain: "sol", symbol: "SOL", className: "w-3 h-3" }),
                      React.createElement("span", null, "SOL:")
                    ),
                    React.createElement("div", { className: "flex items-center gap-1" },
                      React.createElement("span", { className: "text-slate-300 font-mono" }, w.sol ? (w.sol.slice(0, 8) + "..." + w.sol.slice(-4)) : "None"),
                      React.createElement("button", { onClick: (e) => { e.stopPropagation(); copyToClipboard(w.sol, "Copied SOL!"); } }, React.createElement(Icon, { name: "copy", className: "w-2.5 h-2.5 text-slate-400 hover:text-white" }))
                    )
                  ),
                  React.createElement("div", { className: "flex items-center justify-between" },
                    React.createElement("div", { className: "flex items-center gap-1 text-slate-400" },
                      React.createElement(CryptoLogo, { chain: "btc", symbol: "BTC", className: "w-3 h-3" }),
                      React.createElement("span", null, "BTC:")
                    ),
                    React.createElement("div", { className: "flex items-center gap-1" },
                      React.createElement("span", { className: "text-slate-300 font-mono" }, w.btc ? (w.btc.slice(0, 8) + "..." + w.btc.slice(-4)) : "None"),
                      React.createElement("button", { onClick: (e) => { e.stopPropagation(); copyToClipboard(w.btc, "Copied BTC!"); } }, React.createElement(Icon, { name: "copy", className: "w-2.5 h-2.5 text-slate-400 hover:text-white" }))
                    )
                  )
                )
              );
            })
          )
        ),

        // 7. SUB-TAB 3: LIVE BLOCK EXPLORERS
        walletSubTab === "activity" && React.createElement("div", { className: "space-y-2 font-mono text-xs" },
          [
            { name: "TON Blockchain", explorer: "Tonviewer", url: EXPLORER_URLS.ton(primaryTonAddr), address: primaryTonAddr, chain: "ton" },
            { name: "BNB Smart Chain", explorer: "BscScan", url: EXPLORER_URLS.bsc(getNodeAddress(activeNodeIdx, "bsc")), address: getNodeAddress(activeNodeIdx, "bsc"), chain: "bsc" },
            { name: "TRON Network", explorer: "TronScan", url: EXPLORER_URLS.tron(getNodeAddress(activeNodeIdx, "tron")), address: getNodeAddress(activeNodeIdx, "tron"), chain: "tron" },
            { name: "Solana Network", explorer: "Solscan", url: EXPLORER_URLS.sol(getNodeAddress(activeNodeIdx, "sol")), address: getNodeAddress(activeNodeIdx, "sol"), chain: "sol" },
            { name: "Bitcoin Taproot", explorer: "Mempool Space", url: EXPLORER_URLS.btc(getNodeAddress(activeNodeIdx, "btc")), address: getNodeAddress(activeNodeIdx, "btc"), chain: "btc" }
          ].map((exp, eIdx) => React.createElement("div", {
            key: eIdx,
            className: `p-3 rounded-2xl border flex items-center justify-between ${cardBg}`
          },
            React.createElement("div", { className: "flex items-center gap-2.5 truncate" },
              React.createElement(CryptoLogo, { chain: exp.chain, symbol: exp.chain.toUpperCase(), className: "w-8 h-8" }),
              React.createElement("div", { className: "truncate" },
                React.createElement("div", { className: `font-black text-xs ${isDark ? 'text-white' : 'text-slate-900'}` }, exp.name),
                React.createElement("div", { className: "text-[10px] text-slate-400 truncate max-w-[180px]" }, exp.address)
              )
            ),
            React.createElement("a", {
              href: exp.url,
              target: "_blank",
              rel: "noopener noreferrer",
              className: "px-2.5 py-1.5 rounded-xl bg-blue-600/10 hover:bg-blue-600/20 text-cyan-400 font-bold border border-blue-500/20 text-[10px] flex items-center gap-1 transition"
            },
              React.createElement("span", null, exp.explorer),
              React.createElement(Icon, { name: "externalLink", className: "w-3 h-3" })
            )
          ))
        )
      );
    })(),
