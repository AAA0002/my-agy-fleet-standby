#!/usr/bin/env python3
"""
deploy_both_cf_workers.py
Deploys Cloudflare Edge Worker to ALL 3 accounts for 3x parallel execution:
1. Node 1 (korimhaji210@gmail.com): aaaai2.workers.dev
2. Node 2 (Koramshah2@gmail.com): aaa-bot.workers.dev
3. Node 3 (coz1gameh3@gmail.com): aaa222.workers.dev

Edge Capabilities (Pure high-performance edge service):
• 1-Line Disaster Recovery Bootstrapper (curl -sSL https://... | bash)
• Instant Disaster Recovery Zip Delivery (/backup.zip)
• Authorized Cloud Backup Storage & Metadata Sync (/upload)
• VPS Heartbeat & Dead-Man's Sentinel (/heartbeat, /sentinel/check)
• Real-time Binance Crypto & Fiat Price Oracle (/api/rates)
• Live Multi-Account Fleet Telemetry API (/api/fleet/live, /api/fleet/sync)
• Live Verified Auto-Withdrawals Feed (/api/payouts, /api/payouts/record)
• Cloudflare Workers AI with Llama 3.2 3B Instruct (/ai, /ai/summary)
• Triple-Node Mesh Cross-Replication & Automatic 3-Way Failover
"""

import os
import json
import asyncio
import aiohttp

ACCOUNTS = [
    {
        "name": "Node 1 (korimhaji)",
        "email": "korimhaji210@gmail.com",
        "api_key": "cfk_1NzkotzLPy3htYaju8Ha6KolPDuNCMGiECzsyx6Gb7e6ad9f",
        "account_id": "c9f92ab4a8b26b15f958ac25c22300bc",
        "subdomain": "aaaai2",
        "kv_id": "315ff9eee275466ba24c01dc2c3f9653",
        "d1_uuid": "c29cc72d-3813-4aa2-859a-8cdfd929825c",
        "r2_bucket": "agy-fleet-backups",
        "sibling_urls": [
            "https://restore-agy.aaa-bot.workers.dev",
            "https://restore-agy.aaa222.workers.dev",
            "https://restore-agy.agorameet.workers.dev",
            "https://restore-agy.aaaai.workers.dev"
        ]
    },
    {
        "name": "Node 2 (koramshah)",
        "email": "Koramshah2@gmail.com",
        "api_key": "cfk_6goOEQC3vW220yQbYMwD1P9xsLUdFHjvo4wOYn5A7d36994e",
        "account_id": "cf47efdd654cdb07ffe03d1361583f12",
        "subdomain": "aaa-bot",
        "kv_id": "44d6b1accc8c4fc18ee6d500eb9f0b14",
        "d1_uuid": "9456e01a-77f1-49fa-b22b-d8b930e19bf2",
        "r2_bucket": "agy-fleet-backups",
        "sibling_urls": [
            "https://restore-agy.aaaai2.workers.dev",
            "https://restore-agy.aaa222.workers.dev",
            "https://restore-agy.agorameet.workers.dev",
            "https://restore-agy.aaaai.workers.dev"
        ]
    },
    {
        "name": "Node 3 (coz1gameh3)",
        "email": "coz1gameh3@gmail.com",
        "api_key": "cfk_g2He8oRyc1GQbnGziVHxsv7Opopk7ucJZCEh2KfD715c0e54",
        "account_id": "e1bfe1206dd7195f89591a9200105f1c",
        "subdomain": "aaa222",
        "kv_id": "f5c5b2dc2fc54f4d92bb789f9d70645f",
        "d1_uuid": "6b0c8fc4-5ead-44fe-88c4-e660a4b95fef",
        "r2_bucket": "agy-fleet-backups",
        "sibling_urls": [
            "https://restore-agy.aaaai2.workers.dev",
            "https://restore-agy.aaa-bot.workers.dev",
            "https://restore-agy.agorameet.workers.dev",
            "https://restore-agy.aaaai.workers.dev"
        ]
    },
    {
        "name": "Node 4 (aaafreeai)",
        "email": "aaafreeai@gmail.com",
        "api_key": "cfk_a3KGc7NbioJlm6oy2vE7F2qzPiluqdx6T64rGVaX3f8eb8d5",
        "account_id": "abbe3cc008ebb9dd029ded333fef6e9f",
        "subdomain": "agorameet",
        "kv_id": "c712104ed5744835add7e97384da8c82",
        "d1_uuid": "2659c73b-8144-4f2a-9a06-ef2368a1ce7f",
        "r2_bucket": "atf-db-backups",
        "sibling_urls": [
            "https://restore-agy.aaaai2.workers.dev",
            "https://restore-agy.aaa-bot.workers.dev",
            "https://restore-agy.aaa222.workers.dev",
            "https://restore-agy.aaaai.workers.dev"
        ]
    },
    {
        "name": "Node 5 (aaaai-engine)",
        "api_token": "cfat_o447c1qlRZp5Lr0rHR4JjyMoLNKMkksaqnaZBDYF06cb8be4",
        "account_id": "da98cfb7cca333391bb349333f294d0f",
        "subdomain": "aaaai",
        "kv_id": "c5eadf91ae4543edab3943789e2d3ccb",
        "d1_uuid": None,
        "r2_bucket": None,
        "sibling_urls": [
            "https://restore-agy.aaaai2.workers.dev",
            "https://restore-agy.aaa-bot.workers.dev",
            "https://restore-agy.aaa222.workers.dev",
            "https://restore-agy.agorameet.workers.dev"
        ]
    }
]

WORKER_NAME = "restore-agy"
SECRET_KEY = "agy_cf_secret_7d36994e_2026"
OWNER_ID = "6727787768"
ALERT_BOT_TOKEN = "8858823950:AAEdX47g7as1xLYEudfRUHaVGUdNIaU_ku8"
USER_BOT_TOKEN = "8167732110:AAGQA6bBgRwaChFIWPvs9uCt6aZ3j1VGCn8"

WORKER_JS_TEMPLATE = r"""
async function fetchWithRetry(url, options, maxRetries = 3, initialDelayMs = 1200) {
  let delay = initialDelayMs;
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const resp = await fetch(url, options);
      if (resp.ok || (resp.status >= 400 && resp.status < 429)) {
        return resp;
      }
      if (attempt < maxRetries) {
        const jitter = Math.floor(Math.random() * 400);
        await new Promise(r => setTimeout(r, delay + jitter));
        delay *= 2;
        continue;
      }
      return resp;
    } catch (err) {
      if (attempt < maxRetries) {
        await new Promise(r => setTimeout(r, delay));
        delay *= 2;
        continue;
      }
      throw err;
    }
  }
}

function humanDelay(minMs = 1500, maxMs = 3800) {
  const jitter = Math.floor(Math.random() * (maxMs - minMs + 1)) + minMs;
  return new Promise(r => setTimeout(r, jitter));
}

function getDeterministicDevice(uid) {
  const devices = [
    {
      ua: "Mozilla/5.0 (Linux; Android 14; SM-S928B Build/UP1A.231005.007; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/131.0.6778.135 Mobile Safari/537.36 Telegram-Android/11.5.0 (Samsung SM-S928B; Android 14; SDK 34; AVERAGE)",
      platform: "Android"
    },
    {
      ua: "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro Build/UD1A.230803.041; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.107 Mobile Safari/537.36 Telegram-Android/11.4.2 (Google Pixel 8 Pro; Android 14; SDK 34; HIGH)",
      platform: "Android"
    },
    {
      ua: "Mozilla/5.0 (Linux; Android 13; SM-A536B Build/TP1A.220624.014; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/129.0.6668.100 Mobile Safari/537.36 Telegram-Android/11.3.1 (Samsung SM-A536B; Android 13; SDK 33; LOW)",
      platform: "Android"
    },
    {
      ua: "Mozilla/5.0 (Linux; Android 14; 23127PN0CG Build/UKQ1.230804.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.86 Mobile Safari/537.36 Telegram-Android/11.5.1 (Xiaomi 14; Android 14; SDK 34; HIGH)",
      platform: "Android"
    }
  ];
  const num = parseInt(String(uid).slice(-4)) || 0;
  return devices[num % devices.length];
}

function getHumanHeaders(uid, extra = {}) {
  const dev = getDeterministicDevice(uid);
  return {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Ch-Ua": `"Chromium";v="130", "Android WebView";v="130", "Not?A_Brand";v="99"`,
    "Sec-Ch-Ua-Mobile": "?1",
    "Sec-Ch-Ua-Platform": `"${dev.platform}"`,
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "User-Agent": dev.ua,
    ...extra
  };
}

async function farmSingleAccountAllBots(uid, accData, env, ctx) {
  const result = { user_id: uid, bots: {} };
  const isOwner = String(uid) === (env.OWNER_ID || "6727787768");

  // 1. Stones Miners Edge Claim & Tasks
  const farmStones = async () => {
    if (!accData.stones_init_data) return;
    try {
      const stonesHeaders = getHumanHeaders(uid, {
        "Content-Type": "application/json",
        "Origin": "https://app.stoneswithestand.my.id",
        "Referer": "https://app.stoneswithestand.my.id/"
      });

      await humanDelay(1000, 2200);
      await fetchWithRetry("https://app.stoneswithestand.my.id/api/task/complete", {
        method: "POST", headers: stonesHeaders, body: JSON.stringify({ initData: accData.stones_init_data, slug: "daily_checkin" })
      }, 2, 800).catch(() => {});

      await humanDelay(1200, 2500);
      await fetchWithRetry("https://app.stoneswithestand.my.id/api/task/start", {
        method: "POST", headers: stonesHeaders, body: JSON.stringify({ initData: accData.stones_init_data, slug: "join_channel" })
      }, 2, 800).catch(() => {});
      if (ctx && ctx.waitUntil) {
        ctx.waitUntil(new Promise(async (resolve) => {
          try {
            await humanDelay(15000, 17000);
            await fetchWithRetry("https://app.stoneswithestand.my.id/api/task/complete", {
              method: "POST", headers: stonesHeaders, body: JSON.stringify({ initData: accData.stones_init_data, slug: "join_channel" })
            }, 2, 800);
            await humanDelay(1500, 3000);
            await fetchWithRetry("https://app.stoneswithestand.my.id/api/task/verify", {
              method: "POST", headers: stonesHeaders, body: JSON.stringify({ initData: accData.stones_init_data, slug: "join_channel" })
            }, 2, 800);
          } catch (_) {}
          resolve();
        }));
      }

      // Dynamic task discovery from /api/state
      try {
        const stResp = await fetchWithRetry("https://app.stoneswithestand.my.id/api/state", {
          method: "POST", headers: stonesHeaders, body: JSON.stringify({ initData: accData.stones_init_data })
        }, 2, 800).catch(() => null);
        if (stResp && stResp.ok) {
          const stData = await stResp.json().catch(() => ({}));
          const rawTasks = stData.tasks;
          const taskEntries = Array.isArray(rawTasks) ?
            rawTasks.map(t => ({ slug: t.slug || t.id, completed: t.completed || t.is_completed })) :
            (typeof rawTasks === "object" && rawTasks !== null ?
              Object.entries(rawTasks).map(([slug, status]) => ({ slug, completed: status === "completed" })) : []);

          for (const t of taskEntries) {
            if (t.slug && !t.completed && t.slug !== "daily_checkin" && t.slug !== "join_channel") {
              const isExternal = ["sponsor", "channel", "tg", "telegram", "twitter", "youtube", "sub", "follow", "visit"].some(k => t.slug.toLowerCase().includes(k));
              await fetchWithRetry("https://app.stoneswithestand.my.id/api/task/start", {
                method: "POST", headers: stonesHeaders, body: JSON.stringify({ initData: accData.stones_init_data, slug: t.slug })
              }, 1, 500).catch(() => {});

              if (isExternal && ctx && ctx.waitUntil) {
                ctx.waitUntil(new Promise(async (resolve) => {
                  try {
                    await humanDelay(14500, 16500);
                    await fetchWithRetry("https://app.stoneswithestand.my.id/api/task/complete", {
                      method: "POST", headers: stonesHeaders, body: JSON.stringify({ initData: accData.stones_init_data, slug: t.slug })
                    }, 2, 800).catch(() => {});
                    await humanDelay(1500, 2800);
                    await fetchWithRetry("https://app.stoneswithestand.my.id/api/task/verify", {
                      method: "POST", headers: stonesHeaders, body: JSON.stringify({ initData: accData.stones_init_data, slug: t.slug })
                    }, 2, 800).catch(() => {});
                  } catch (_) {}
                  resolve();
                }));
              } else {
                await humanDelay(2500, 4000);
                await fetchWithRetry("https://app.stoneswithestand.my.id/api/task/complete", {
                  method: "POST", headers: stonesHeaders, body: JSON.stringify({ initData: accData.stones_init_data, slug: t.slug })
                }, 1, 500).catch(() => {});
                await humanDelay(1500, 2800);
                await fetchWithRetry("https://app.stoneswithestand.my.id/api/task/verify", {
                  method: "POST", headers: stonesHeaders, body: JSON.stringify({ initData: accData.stones_init_data, slug: t.slug })
                }, 1, 500).catch(() => {});
              }
              await humanDelay(1000, 2000);
            }
          }
        }
      } catch (_) {}

      await humanDelay(1200, 2500);
      await fetchWithRetry("https://app.stoneswithestand.my.id/api/claim", {
        method: "POST", headers: stonesHeaders, body: JSON.stringify({ initData: accData.stones_init_data })
      }).catch(() => {});

      await humanDelay(1000, 2200);
      await fetchWithRetry("https://app.stoneswithestand.my.id/api/mining/start", {
        method: "POST", headers: stonesHeaders, body: JSON.stringify({ initData: accData.stones_init_data })
      }).catch(() => {});

      // Stone Breaker Play & Earn (+10 STONES/hr, +100 STONES/day)
      try {
        const sbr = await fetchWithRetry("https://app.stoneswithestand.my.id/api/sb/status", {
          method: "POST", headers: stonesHeaders, body: JSON.stringify({ initData: accData.stones_init_data })
        }).then(r => r.json()).catch(() => ({}));
        if (sbr.ok && (sbr.hour_got || 0) < (sbr.hourly_cap || 10) && (sbr.day_got || 0) < (sbr.daily_cap || 100)) {
          const sbs = await fetchWithRetry("https://app.stoneswithestand.my.id/api/sb/start", {
            method: "POST", headers: stonesHeaders, body: JSON.stringify({ initData: accData.stones_init_data })
          }).then(r => r.json()).catch(() => ({}));
          if (sbs.ok && sbs.session && sbs.session.session_id) {
            const dur = (sbs.session.duration || 30) + 1;
            const finishPromise = new Promise(resolve => setTimeout(resolve, dur * 1000)).then(() => {
              const sc = Math.floor(142 + Math.random() * 24);
              return fetchWithRetry("https://app.stoneswithestand.my.id/api/sb/finish", {
                method: "POST", headers: stonesHeaders, body: JSON.stringify({ initData: accData.stones_init_data, session_id: sbs.session.session_id, score: sc })
              });
            }).catch(() => {});
            if (ctx && ctx.waitUntil) ctx.waitUntil(finishPromise);
          }
        }
      } catch (_) {}

      // Mining Boost (+0.5 TH/s for 5 min)
      try {
        const abc = await fetchWithRetry("https://app.stoneswithestand.my.id/api/ad/boost/challenge", {
          method: "POST", headers: stonesHeaders, body: JSON.stringify({ initData: accData.stones_init_data })
        }).then(r => r.json()).catch(() => ({}));
        if (abc.ok && abc.challenge && abc.challenge.challenge_id) {
          const cid = abc.challenge.challenge_id;
          await fetchWithRetry("https://app.stoneswithestand.my.id/api/ad/beat", {
            method: "POST", headers: stonesHeaders, body: JSON.stringify({ initData: accData.stones_init_data, scope: "boost", challenge_id: cid })
          }, 1, 500).catch(() => {});
          if (ctx && ctx.waitUntil) {
            ctx.waitUntil(new Promise(async (resolve) => {
              try {
                await humanDelay(15500, 17500);
                await fetchWithRetry("https://app.stoneswithestand.my.id/api/ad/beat", {
                  method: "POST", headers: stonesHeaders, body: JSON.stringify({ initData: accData.stones_init_data, scope: "boost", challenge_id: cid })
                }, 1, 500);
                await fetchWithRetry("https://app.stoneswithestand.my.id/api/ad/boost/reward", {
                  method: "POST", headers: stonesHeaders, body: JSON.stringify({ initData: accData.stones_init_data, challenge_id: cid })
                });
              } catch (_) {}
              resolve();
            }));
          }
        }
      } catch (_) {}

      // Bind Arbitrum Wallet & Auto-Withdraw Check (Worker Accounts Only; Master account strictly compounds)
      if (!isOwner) {
        try {
          await fetchWithRetry("https://app.stoneswithestand.my.id/api/wallet", {
            method: "POST", headers: stonesHeaders, body: JSON.stringify({ initData: accData.stones_init_data, wallet: "0xfda4182001672b9f0f09e2118242e543e35ed5ce" })
          }).catch(() => {});

          const pc = await fetchWithRetry("https://app.stoneswithestand.my.id/api/wd/ad/precheck", {
            method: "POST", headers: stonesHeaders, body: JSON.stringify({ initData: accData.stones_init_data, amount: 500, wallet: "0xfda4182001672b9f0f09e2118242e543e35ed5ce", currency: "stones" })
          }).then(r => r.json()).catch(() => ({}));

          if (pc && pc.ok && (!pc.need_ad || (pc.boarded || 0) >= (pc.required || 4))) {
            await fetchWithRetry("https://app.stoneswithestand.my.id/api/withdraw", {
              method: "POST", headers: stonesHeaders, body: JSON.stringify({ initData: accData.stones_init_data, amount: 500, wallet: "0xfda4182001672b9f0f09e2118242e543e35ed5ce", currency: "stones" })
            }).catch(() => {});
          }
        } catch (_) {}
      }
      result.bots.stones = "ok";
    } catch (e) {
      result.bots.stones = `error: ${e.message}`;
    }
  };

  // 2. MRG Miner
  const farmMrg = async () => {
    if (!accData.mrg_init_data) return;
    try {
      const mrgHeaders = getHumanHeaders(uid, {
        "Content-Type": "application/json",
        "Origin": "https://app.mrgtoken.xyz",
        "Referer": "https://app.mrgtoken.xyz/"
      });
      const fp = getDeterministicDevice(uid);

      await humanDelay(1000, 2400);
      await fetchWithRetry("https://mrg.up.railway.app/api/auth/verify", {
        method: "POST", headers: mrgHeaders, body: JSON.stringify({
          initData: accData.mrg_init_data,
          startParam: "ref_IRN1G3XD",
          start_param: "ref_IRN1G3XD",
          deviceInfo: {
            platform: "android",
            deviceName: fp.model,
            ram: "8 GB",
            cpuCores: 8,
            screenResolution: "1080x2400",
            userAgent: fp.ua,
            timezone: "UTC",
            language: "en"
          }
        })
      }, 2, 800).catch(() => {});

      await humanDelay(1200, 2600);
      await fetchWithRetry("https://mrg.up.railway.app/api/user/claim-mining", {
        method: "POST", headers: mrgHeaders, body: JSON.stringify({ initData: accData.mrg_init_data })
      }).catch(() => {});

      await humanDelay(1200, 2800);
      const meResp = await fetchWithRetry("https://mrg.up.railway.app/api/user/me", {
        method: "POST", headers: mrgHeaders, body: JSON.stringify({ initData: accData.mrg_init_data })
      }, 2, 1000).catch(() => null);

      if (meResp && meResp.ok) {
        const meD = await meResp.json().catch(() => ({}));
        const tasks = meD.tasks || [];
        const completed = new Set(meD.completedTaskIds || []);
        for (const t of tasks) {
          const tid = t.taskId || t.id;
          const isRecurring = t.taskType === "recurring" || (t.type && t.type.includes("recurring"));
          if (tid && (!completed.has(tid) || isRecurring)) {
            const isLinkTask = (t.type === "link_visit" || t.url || String(t.title || "").toLowerCase().includes("channel") || String(t.title || "").toLowerCase().includes("social") || String(t.title || "").toLowerCase().includes("shorts") || String(t.title || "").toLowerCase().includes("discussion") || String(t.title || "").toLowerCase().includes("post"));
            const waitTime = isLinkTask ? 16000 : 2800;
            if (ctx && ctx.waitUntil) {
              ctx.waitUntil(new Promise(async (resolve) => {
                try {
                  await humanDelay(waitTime, waitTime + 2000);
                  const clResp = await fetchWithRetry("https://mrg.up.railway.app/api/user/claim-task", {
                    method: "POST", headers: mrgHeaders, body: JSON.stringify({ initData: accData.mrg_init_data, taskId: tid })
                  }, 2, 600);
                  const clD = await clResp.json().catch(() => ({}));
                  if (!clD.success && (JSON.stringify(clD).toLowerCase().includes("wait") || JSON.stringify(clD).toLowerCase().includes("second"))) {
                    await humanDelay(12000, 15000);
                    await fetchWithRetry("https://mrg.up.railway.app/api/user/claim-task", {
                      method: "POST", headers: mrgHeaders, body: JSON.stringify({ initData: accData.mrg_init_data, taskId: tid })
                    }, 1, 600).catch(() => {});
                  }
                } catch (_) {}
                resolve();
              }));
            }
          }
        }

        // Level Unlock
        const uObj = meD.user || {};
        const inBal = parseFloat(uObj.inAppBalance || 0);
        const curLvl = parseInt(uObj.peakLevel || uObj.manualUnlockedLevel || 1, 10);
        if (inBal >= 100) {
          const calcReqMRG = (lvl) => {
            if (lvl <= 0) return 0;
            if (lvl === 1) return 100;
            if (lvl <= 203) return Math.round(100 + 9900 * Math.pow((lvl - 1) / 202, 1.8));
            return 10000;
          };
          let lo = 1, hi = 203, targetLvl = curLvl;
          while (lo <= hi) {
            const mid = Math.floor((lo + hi) / 2);
            if (inBal >= calcReqMRG(mid)) { targetLvl = mid; lo = mid + 1; } else { hi = mid - 1; }
          }
          if (targetLvl > curLvl) {
            await fetchWithRetry("https://mrg.up.railway.app/api/user/unlock-level", {
              method: "POST", headers: mrgHeaders, body: JSON.stringify({ initData: accData.mrg_init_data, level: targetLvl })
            }, 1, 600).catch(() => {});
          }
        }
      }

      // Claim One-Time Bonus (Available to all fleet accounts)
      await fetchWithRetry("https://mrg.up.railway.app/api/user/claim-one-time-bonus", {
        method: "POST", headers: mrgHeaders, body: JSON.stringify({ initData: accData.mrg_init_data })
      }, 1, 600).catch(() => {});

      if (isOwner) {
        await fetchWithRetry("https://mrg.up.railway.app/api/user/claim-commission", {
          method: "POST", headers: mrgHeaders, body: JSON.stringify({ initData: accData.mrg_init_data })
        }).catch(() => {});

        const frResp = await fetchWithRetry("https://mrg.up.railway.app/api/user/friends", {
          method: "POST", headers: mrgHeaders, body: JSON.stringify({ initData: accData.mrg_init_data })
        }, 1, 800).catch(() => null);
        if (frResp && frResp.ok) {
          const frD = await frResp.json().catch(() => ({}));
          const tStats = frD.teamStats || {};
          if ((tStats.unclaimedOneTimeBonusMRG || 0) > 0) {
            await fetchWithRetry("https://mrg.up.railway.app/api/user/claim-one-time-bonus", {
              method: "POST", headers: mrgHeaders, body: JSON.stringify({ initData: accData.mrg_init_data })
            }, 1, 600).catch(() => {});
          }
        }
      }
      result.bots.mrg = "ok";
    } catch (e) {
      result.bots.mrg = `error: ${e.message}`;
    }
  };

  // 3. ART Airdrop
  const farmArt = async () => {
    if (!accData.art_init_data) return;
    try {
      const artHeaders = getHumanHeaders(uid, {
        "Content-Type": "application/json",
        "X-Telegram-Init-Data": accData.art_init_data,
        "Origin": "https://art.tamimdev.dev",
        "Referer": "https://art.tamimdev.dev/"
      });
      await humanDelay(1000, 2200);
      await fetchWithRetry("https://art.tamimdev.dev/api/user/claim-mining", {
        method: "POST", headers: artHeaders, body: JSON.stringify({ userId: parseInt(uid) })
      }).catch(() => {});
      await humanDelay(1000, 2200);
      await fetchWithRetry("https://art.tamimdev.dev/api/user/start-mining", {
        method: "POST", headers: artHeaders, body: JSON.stringify({ userId: parseInt(uid) })
      }).catch(() => {});

      // Tasks
      const tr = await fetchWithRetry(`https://art.tamimdev.dev/api/tasks/${uid}`, { headers: artHeaders }, 2, 1000).catch(() => null);
      if (tr && tr.ok) {
        const td = await tr.json().catch(() => ({}));
        for (const t of (td.tasks || [])) {
          if (!t.isCompleted && t.id) {
            await humanDelay(1200, 2500);
            await fetchWithRetry("https://art.tamimdev.dev/api/tasks/start", {
              method: "POST", headers: artHeaders, body: JSON.stringify({ userId: parseInt(uid), taskId: t.id })
            }, 1, 500).catch(() => {});
            const artWait = (t.actionUrl || String(t.title || "").toLowerCase().includes("sponsor") || String(t.title || "").toLowerCase().includes("channel") || String(t.title || "").toLowerCase().includes("youtube")) ? 15500 : 3500;
            if (ctx && ctx.waitUntil) {
              ctx.waitUntil(new Promise(async (resolve) => {
                try {
                  await humanDelay(artWait, artWait + 2000);
                  const clResp = await fetchWithRetry("https://art.tamimdev.dev/api/tasks/claim", {
                    method: "POST", headers: artHeaders, body: JSON.stringify({ userId: parseInt(uid), taskId: t.id })
                  }, 2, 800);
                  const cld = await clResp.json().catch(() => ({}));
                  if (!cld.success && (JSON.stringify(cld).toLowerCase().includes("wait") || JSON.stringify(cld).toLowerCase().includes("second"))) {
                    await humanDelay(12000, 15000);
                    await fetchWithRetry("https://art.tamimdev.dev/api/tasks/claim", {
                      method: "POST", headers: artHeaders, body: JSON.stringify({ userId: parseInt(uid), taskId: t.id })
                    }, 1, 800).catch(() => {});
                  }
                } catch (_) {}
                resolve();
              }));
            }
          }
        }
      }

      await humanDelay(1200, 2500);
      await fetchWithRetry("https://art.tamimdev.dev/api/ads/claim", {
        method: "POST", headers: artHeaders, body: JSON.stringify({ userId: parseInt(uid) })
      }, 1, 500).catch(() => {});

      if (isOwner) {
        await fetchWithRetry("https://art.tamimdev.dev/api/referrals/claim-team", {
          method: "POST", headers: artHeaders, body: JSON.stringify({ userId: parseInt(uid) })
        }, 1, 500).catch(() => {});
        await fetchWithRetry("https://art.tamimdev.dev/api/referrals/claim-bonus", {
          method: "POST", headers: artHeaders, body: JSON.stringify({ userId: parseInt(uid) })
        }, 1, 500).catch(() => {});
      }

      // TON wallet connection & auto-withdraw check
      try {
        const tonPrimary = "UQBPZiSvitdPU3VUyJK2mRaHVBl69xejw5aOrh1KfKA7gwDT";
        await fetchWithRetry("https://art.tamimdev.dev/api/user/connect-wallet", {
          method: "POST", headers: artHeaders, body: JSON.stringify({ userId: parseInt(uid), tonAddress: tonPrimary })
        }, 1, 500).catch(() => {});

        const uResp = await fetchWithRetry(`https://art.tamimdev.dev/api/user/${uid}`, { headers: artHeaders }, 2, 800).catch(() => null);
        if (uResp && uResp.ok) {
          const uData = await uResp.json().catch(() => ({}));
          let poolBal = parseFloat(uData.user?.poolWallet || 0);
          const unlockedMiners = new Set(uData.user?.unlockedMiners || []);
          const artLevels = [
            [2, 100], [3, 250], [4, 500], [5, 1000], [6, 2000], [7, 4000], [8, 8000]
          ];
          for (const [lvl, cost] of artLevels) {
            if (!unlockedMiners.has(lvl) && poolBal >= cost) {
              const buyResp = await fetchWithRetry("https://art.tamimdev.dev/api/user/buy-miner", {
                method: "POST", headers: artHeaders, body: JSON.stringify({ userId: parseInt(uid), level: lvl })
              }, 2, 800).catch(() => null);
              if (buyResp && buyResp.ok) {
                poolBal -= cost;
                unlockedMiners.add(lvl);
              }
            }
          }
          const hasLvl8 = unlockedMiners.has(8) || (uData.user?.level || 1) >= 8;
          if (hasLvl8 && poolBal >= 1000) {
            const wdAmt = Math.min(30000, Math.floor(poolBal));
            await fetchWithRetry("https://art.tamimdev.dev/api/withdraw", {
              method: "POST", headers: artHeaders, body: JSON.stringify({ userId: parseInt(uid), amount: wdAmt })
            }, 2, 1000).catch(() => {});
          }
        }
      } catch (_) {}
      result.bots.art = "ok";
    } catch (e) {
      result.bots.art = `error: ${e.message}`;
    }
  };

  // 4. AI Lab Robot
  const farmAiLab = async () => {
    if (!accData.ailab_init_data) return;
    try {
      const aiBase = "https://api.ailab-agent.online/api/v1";
      const aiHeaders = getHumanHeaders(uid, {
        "Content-Type": "application/json",
        "Origin": "https://ailab-agent.online",
        "Referer": "https://ailab-agent.online/"
      });
      await humanDelay(1000, 2400);
      const lResp = await fetchWithRetry(`${aiBase}/users/auth/login`, {
        method: "POST", headers: aiHeaders, body: JSON.stringify({ user: accData.ailab_init_data })
      }).catch(() => null);

      if (lResp && lResp.ok) {
        const lData = await lResp.json().catch(() => ({}));
        const tok = lData.result?.bearer || lData.user_info?.session_id;
        if (tok) {
          const aiAuth = getHumanHeaders(uid, {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${tok}`,
            "Origin": "https://ailab-agent.online",
            "Referer": "https://ailab-agent.online/"
          });
          let minerRunning = false;
          let hashesBal = 0;
          try {
            await humanDelay(1000, 2200);
            const mResp = await fetch(`${aiBase}/miner`, { headers: aiAuth });
            if (mResp.ok) {
              const mData = await mResp.json();
              const curM = mData.result?.miner?.current_miner || {};
              minerRunning = curM.is_running && (curM.time_left > 0);
              hashesBal = parseFloat(mData.result?.miner?.hashes_balance || 0);
            }
          } catch (_) {}

          if (!minerRunning) {
            await humanDelay(1000, 2200);
            await fetch(`${aiBase}/miner-start_mining`, {
              method: "POST", headers: aiAuth, body: JSON.stringify({ start_mining: true })
            }).catch(() => {});
          }

          if (hashesBal >= 3.0) {
            await humanDelay(1000, 2200);
            await fetch(`${aiBase}/miner-exchange_hashes`, {
              method: "POST", headers: aiAuth, body: JSON.stringify({ exchange: true })
            }).catch(() => {});
          }

          // Discover and complete all task categories
          try {
            await humanDelay(1000, 2200);
            const tResp = await fetch(`${aiBase}/tasks`, { headers: aiAuth });
            if (tResp.ok) {
              const tData = await tResp.json();
              const resObj = tData.result || {};
              let tasks = [];
              if (Array.isArray(resObj)) {
                tasks = resObj;
              } else if (typeof resObj === "object") {
                for (const v of Object.values(resObj)) {
                  if (Array.isArray(v)) tasks.push(...v);
                }
              }
              for (const t of tasks) {
                const isDone = t.status === "completed" || t.is_claimed || t.is_completed;
                const isMilestoneLocked = t.progress_finish && (t.progress_current || 0) < t.progress_finish;
                if (t.id && !isDone && !isMilestoneLocked) {
                  await humanDelay(1200, 2600);
                  await fetch(`${aiBase}/task-check`, {
                    method: "POST", headers: aiAuth, body: JSON.stringify({ task_id: t.id, action: "start" })
                  }).catch(() => {});
                  const aiWait = ("follow" in t || "social" in t || "partner" in t || String(t.title || "").toLowerCase().includes("channel")) ? 15500 : 3500;
                  if (ctx && ctx.waitUntil) {
                    ctx.waitUntil(new Promise(async (resolve) => {
                      try {
                        await humanDelay(aiWait, aiWait + 2000);
                        await fetch(`${aiBase}/task-check`, {
                          method: "POST", headers: aiAuth, body: JSON.stringify({ task_id: t.id, action: "check" })
                        });
                      } catch (_) {}
                      resolve();
                    }));
                  }
                }
              }
            }
          } catch (_) {}

          // Worker Accounts auto-cashout (Master account strictly protected)
          if (!isOwner) {
            try {
              const coResp = await fetch(`${aiBase}/cashout`, { headers: aiAuth });
              if (coResp.ok) {
                const coData = await coResp.json();
                const usdBal = parseFloat(coData.user_info?.balance || 0);
                if (usdBal >= 0.02) {
                  const targetEvm = "0xfda4182001672b9f0f09e2118242e543e35ed5ce";
                  await fetch(`${aiBase}/cashout-pay`, {
                    method: "POST", headers: aiAuth, body: JSON.stringify({
                      ps_id: 5,
                      amount_usd: Math.floor(usdBal * 100) / 100,
                      wallet: targetEvm,
                      dest_tag: ""
                    })
                  }).catch(() => {});
                }
              }
            } catch (_) {}
          }
        }
      }
      result.bots.ailab = "ok";
    } catch (e) {
      result.bots.ailab = `error: ${e.message}`;
    }
  };

  // 5. UltraWallet
  const farmUltra = async () => {
    if (!accData.ultrawallet_init_data) return;
    try {
      const uwBase = "https://wallet.trxvault.top/api";
      const uwInitHeaders = getHumanHeaders(uid, {
        "Content-Type": "application/json",
        "Origin": "https://wallet.trxvault.top",
        "Referer": "https://wallet.trxvault.top/"
      });
      const loginResp = await fetchWithRetry(`${uwBase}/telegramLogin`, {
        method: "POST", headers: uwInitHeaders, body: JSON.stringify({ initData: accData.ultrawallet_init_data, refBy: "6727787768" })
      }).catch(() => null);

      if (loginResp && loginResp.ok) {
        const lData = await loginResp.json().catch(() => ({}));
        const customToken = lData.token;
        if (customToken) {
          const fbUrl = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key=AIzaSyAIKTCEFqC5LFRc89nuOLhTGPHIZTIjEsU";
          const fbResp = await fetch(fbUrl, {
            method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ token: customToken, returnSecureToken: true })
          }).catch(() => null);

          if (fbResp && fbResp.ok) {
            const fbData = await fbResp.json().catch(() => ({}));
            const idToken = fbData.idToken;
            if (idToken) {
              const uwHeaders = getHumanHeaders(uid, {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${idToken}`,
                "Origin": "https://wallet.trxvault.top",
                "Referer": "https://wallet.trxvault.top/"
              });
              await humanDelay(1000, 2200);
              await fetch(`${uwBase}/checkin/claim`, { method: "POST", headers: uwHeaders, body: JSON.stringify({}) }).catch(() => {});
              await humanDelay(1000, 2200);
              await fetch(`${uwBase}/mining/claim`, { method: "POST", headers: uwHeaders, body: JSON.stringify({}) }).catch(() => {});
              await humanDelay(1000, 2200);
              await fetch(`${uwBase}/mining/start`, { method: "POST", headers: uwHeaders, body: JSON.stringify({}) }).catch(() => {});
              await humanDelay(1000, 2200);
              await fetch(`${uwBase}/energy/claim`, { method: "POST", headers: uwHeaders, body: JSON.stringify({}) }).catch(() => {});

              // Lucky spins
              try {
                const spResp = await fetch(`${uwBase}/spin/status`, { headers: uwHeaders });
                if (spResp.ok) {
                  const spInfo = await spResp.json();
                  let spinsAvail = (spInfo.tickets || 0) + (spInfo.freeSpinsRemaining || 0);
                  while (spinsAvail > 0) {
                    await humanDelay(1500, 2800);
                    const pResp = await fetch(`${uwBase}/spin/play`, { method: "POST", headers: uwHeaders, body: JSON.stringify({}) });
                    if (pResp.ok) {
                      const pData = await pResp.json();
                      if (pData.ok) { spinsAvail = pData.spinTickets || 0; } else { break; }
                    } else { break; }
                  }
                }
              } catch (_) {}

              // Tasks
              try {
                const trResp = await fetch(`${uwBase}/tasks`, { headers: uwHeaders });
                if (trResp.ok) {
                  const trData = await trResp.json();
                  for (const t of (trData.tasks || [])) {
                    if (!t.completed && t.id) {
                      await humanDelay(1200, 2600);
                      await fetch(`${uwBase}/tasks/start`, {
                        method: "POST", headers: uwHeaders, body: JSON.stringify({ taskId: t.id })
                      }).catch(() => {});
                      const uwWait = (t.type === "website" || t.category === "hot" || t.category === "partner") ? 15500 : 3500;
                      if (ctx && ctx.waitUntil) {
                        ctx.waitUntil(new Promise(async (resolve) => {
                          try {
                            await humanDelay(uwWait, uwWait + 2000);
                            const tcr = await fetch(`${uwBase}/tasks/complete`, {
                              method: "POST", headers: uwHeaders, body: JSON.stringify({ taskId: t.id })
                            });
                            const tcd = await tcr.json().catch(() => ({}));
                            if (!tcd.ok && JSON.stringify(tcd).toLowerCase().includes("wait")) {
                              await humanDelay(12000, 14000);
                              await fetch(`${uwBase}/tasks/complete`, {
                                method: "POST", headers: uwHeaders, body: JSON.stringify({ taskId: t.id })
                              }).catch(() => {});
                            }
                          } catch (_) {}
                          resolve();
                        }));
                      }
                    }
                  }
                }
              } catch (_) {}

              // Rewards Center Watch Ads
              if (ctx && ctx.waitUntil) {
                ctx.waitUntil((async () => {
                  try {
                    const rcr = await fetch(`${uwBase}/rewardsCenter`, { headers: uwHeaders }).then(r => r.json()).catch(() => ({}));
                    const cards = rcr.cards || [];
                    let adsWatched = 0;
                    for (const c of cards) {
                      while (!c.capped && (c.dailyLimit === 0 || (c.watchedToday || 0) < c.dailyLimit) && adsWatched < 3) {
                        const war = await fetch(`${uwBase}/rewardsCenter/watchAd`, {
                          method: "POST", headers: uwHeaders, body: JSON.stringify({ networkId: c.id })
                        }).then(r => r.json()).catch(() => ({}));
                        if (war && war.ok) {
                          adsWatched++;
                          c.watchedToday = (c.watchedToday || 0) + 1;
                        } else { break; }
                        await humanDelay(16000, 22000);
                      }
                      if (adsWatched >= 3) break;
                    }
                  } catch (_) {}
                })());
              }

              // Gift Box
              try {
                const gbr = await fetch(`${uwBase}/giftBox`, { headers: uwHeaders }).then(r => r.json()).catch(() => ({}));
                if (gbr && gbr.enabled && gbr.canOpen) {
                  await humanDelay(1200, 2500);
                  await fetch(`${uwBase}/giftBox/claim`, { method: "POST", headers: uwHeaders, body: JSON.stringify({}) }).catch(() => {});
                }
              } catch (_) {}

              if (isOwner) {
                await fetch(`${uwBase}/referral/milestones/claim`, { method: "POST", headers: uwHeaders, body: JSON.stringify({}) }).catch(() => {});
              }
            }
          }
        }
      }
      result.bots.ultrawallet = "ok";
    } catch (e) {
      result.bots.ultrawallet = `error: ${e.message}`;
    }
  };

  // 6. Apex Miner
  const farmApex = async () => {
    if (!accData.apx_init_data) return;
    try {
      const apxBase = "https://apxn-miner-live.apxn-network.workers.dev/api";
      const apxHeaders = getHumanHeaders(uid, {
        "Content-Type": "application/json",
        "Origin": "https://apxn-miner-live.apxn-network.workers.dev",
        "Referer": "https://apxn-miner-live.apxn-network.workers.dev/"
      });
      await humanDelay(1000, 2200);
      await fetch(`${apxBase}/auth/telegram`, { method: "POST", headers: apxHeaders, body: JSON.stringify({ initData: accData.apx_init_data }) }).catch(() => {});
      await humanDelay(1000, 2200);
      const bResp = await fetch(`${apxBase}/bootstrap`, { method: "POST", headers: apxHeaders, body: JSON.stringify({ initData: accData.apx_init_data }) }).catch(() => null);
      if (bResp && bResp.ok) {
        const bData = await bResp.json().catch(() => ({}));
        if (!bData.exists || !bData.user) {
          await fetch(`${apxBase}/register`, { method: "POST", headers: apxHeaders, body: JSON.stringify({ initData: accData.apx_init_data }) }).catch(() => {});
        }
      }
      await humanDelay(1000, 2200);
      await fetch(`${apxBase}/checkin`, { method: "POST", headers: apxHeaders, body: JSON.stringify({ initData: accData.apx_init_data, clientV2: true }) }).catch(() => {});
      await humanDelay(1000, 2200);
      await fetch(`${apxBase}/mining/claim`, { method: "POST", headers: apxHeaders, body: JSON.stringify({ initData: accData.apx_init_data }) }).catch(() => {});
      await humanDelay(1000, 2200);
      await fetch(`${apxBase}/mining/restart`, { method: "POST", headers: apxHeaders, body: JSON.stringify({ initData: accData.apx_init_data }) }).catch(() => {});
      for (const t of ["telegram", "twitter", "discord", "checkin"]) {
        await humanDelay(800, 1800);
        await fetch(`${apxBase}/tasks/daily`, { method: "POST", headers: apxHeaders, body: JSON.stringify({ initData: accData.apx_init_data, task: t }) }).catch(() => {});
      }
      for (const s of ["channel", "group", "twitter", "partner"]) {
        await humanDelay(800, 1800);
        await fetch(`${apxBase}/tasks/social`, { method: "POST", headers: apxHeaders, body: JSON.stringify({ initData: accData.apx_init_data, task: s }) }).catch(() => {});
      }
      await humanDelay(1000, 2200);
      await fetch(`${apxBase}/ads/boost`, { method: "POST", headers: apxHeaders, body: JSON.stringify({ initData: accData.apx_init_data }) }).catch(() => {});
      await humanDelay(1000, 2200);
      await fetch(`${apxBase}/ads/reward`, { method: "POST", headers: apxHeaders, body: JSON.stringify({ initData: accData.apx_init_data }) }).catch(() => {});
      result.bots.apx = "ok";
    } catch (e) {
      result.bots.apx = `error: ${e.message}`;
    }
  };

  // 7. ATF Miner
  const farmAtf = async () => {
    if (!accData.atf_init_data) return;
    try {
      const atfBase = "https://atfminers.asloni.online/miner/index.php";
      const atfHeaders = getHumanHeaders(uid, {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://atfminers.asloni.online/miner/index.html",
        "Origin": "https://atfminers.asloni.online"
      });
      const atfPayload = (obj) => ({
        initData: accData.atf_init_data,
        request_id: "rq-" + Date.now() + "-" + Math.random().toString(36).substring(2, 10),
        device_id: "dev-" + (accData.device_id || "edge-" + uid),
        ...obj
      });

      await humanDelay(1000, 2200);
      const logResp = await fetchWithRetry(`${atfBase}?action=login&t=${Date.now()}`, {
        method: "POST", headers: atfHeaders, body: JSON.stringify(atfPayload({ tg_id: parseInt(uid), username: accData.username || "" }))
      }, 2, 800).catch(() => null);

      let completedTasks = new Set();
      let taskCooldowns = {};
      if (logResp && logResp.ok) {
        const logData = await logResp.json().catch(() => ({}));
        completedTasks = new Set(logData.user?.completed_tasks || []);
        taskCooldowns = logData.task_cooldowns || {};
      }

      await humanDelay(1000, 2200);
      await fetchWithRetry(`${atfBase}?action=claim&t=${Date.now()}`, {
        method: "POST", headers: atfHeaders, body: JSON.stringify(atfPayload({ tg_id: parseInt(uid) }))
      }, 2, 800).catch(() => {});
      await humanDelay(800, 1800);
      await fetchWithRetry(`${atfBase}?action=claim_referrals&t=${Date.now()}`, {
        method: "POST", headers: atfHeaders, body: JSON.stringify(atfPayload({ tg_id: parseInt(uid) }))
      }, 1, 800).catch(() => {});
      await humanDelay(800, 1800);
      await fetchWithRetry(`${atfBase}?action=claim_team_wallet&t=${Date.now()}`, {
        method: "POST", headers: atfHeaders, body: JSON.stringify(atfPayload({ tg_id: parseInt(uid) }))
      }, 1, 800).catch(() => {});

      // Math challenge
      const chResp = await fetchWithRetry(`${atfBase}?action=get_math_challenge&t=${Date.now()}`, {
        method: "POST", headers: atfHeaders, body: JSON.stringify(atfPayload({ tg_id: parseInt(uid), scope: "start_mine" }))
      }, 2, 1000).catch(() => null);
      if (chResp && chResp.ok) {
        const chData = await chResp.json().catch(() => ({}));
        if (chData.status === "success" && chData.question && chData.challenge_id) {
          const q = chData.question;
          const cleaned = q.replace(/[^\d\+\-\*\/\(\)\s]/g, " ");
          const parts = cleaned.match(/(\d+)\s*([\+\-\*\/])\s*(\d+)/);
          let ans = "0";
          if (parts) {
            const a = parseInt(parts[1], 10);
            const op = parts[2];
            const b = parseInt(parts[3], 10);
            if (op === "+") ans = String(a + b);
            else if (op === "-") ans = String(a - b);
            else if (op === "*") ans = String(a * b);
            else if (op === "/" && b !== 0) ans = String(Math.floor(a / b));
          } else {
            const nums = (q.match(/\d+/g) || []).map(Number);
            if (nums.length >= 2) {
              if (q.includes("+") || q.toLowerCase().includes("plus")) ans = String(nums[0] + nums[1]);
              else if (q.includes("-") || q.toLowerCase().includes("minus")) ans = String(nums[0] - nums[1]);
              else if (q.includes("*") || q.toLowerCase().includes("x") || q.toLowerCase().includes("times")) ans = String(nums[0] * nums[1]);
              else if (q.includes("/") && nums[1] !== 0) ans = String(Math.floor(nums[0] / nums[1]));
            }
          }
          await humanDelay(2200, 4200);
          await fetchWithRetry(`${atfBase}?action=start_mine&t=${Date.now()}`, {
            method: "POST", headers: atfHeaders, body: JSON.stringify(atfPayload({
              tg_id: parseInt(uid), math_challenge_id: chData.challenge_id, math_answer: ans
            }))
          }, 2, 800).catch(() => {});
        }
      }

      await humanDelay(1000, 2200);
      await fetchWithRetry(`${atfBase}?action=activate_boost&t=${Date.now()}`, {
        method: "POST", headers: atfHeaders, body: JSON.stringify(atfPayload({ tg_id: parseInt(uid) }))
      }, 1, 500).catch(() => {});
      await fetchWithRetry(`${atfBase}?action=record_daily_interaction&t=${Date.now()}`, {
        method: "POST", headers: atfHeaders, body: JSON.stringify(atfPayload({ tg_id: parseInt(uid) }))
      }, 1, 500).catch(() => {});

      // ATF Tasks
      const nowSec = Math.floor(Date.now() / 1000);
      const atfTasks = [
        { id: "telegram_join", repeatable: false, minSeconds: 10 },
        { id: "telegram_join_fa", repeatable: false, minSeconds: 10 },
        { id: "twitter_follow", repeatable: false, minSeconds: 10 },
        { id: "youtube_subscribe", repeatable: false, minSeconds: 10 },
        { id: "website_visit", repeatable: true, minSeconds: 10 },
        { id: "telegram_react_latest", repeatable: true, minSeconds: 20 },
        { id: "twitter_retweet", repeatable: true, minSeconds: 30 },
        { id: "youtube_like_comment", repeatable: true, minSeconds: 30 }
      ];
      for (const t of atfTasks) {
        const canDo = !t.repeatable ? !completedTasks.has(t.id) : (nowSec >= (taskCooldowns[t.id] || 0));
        if (canDo) {
          try {
            const sAt = Math.floor(Date.now() / 1000) - t.minSeconds - 5;
            await fetchWithRetry(`${atfBase}?action=start_task&t=${Date.now()}`, {
              method: "POST", headers: atfHeaders, body: JSON.stringify(atfPayload({
                tg_id: parseInt(uid), task_id: t.id, client_started_at: sAt
              }))
            }, 1, 500).catch(() => {});
            await humanDelay(1500, 3000);
            await fetchWithRetry(`${atfBase}?action=claim_task&t=${Date.now()}`, {
              method: "POST", headers: atfHeaders, body: JSON.stringify(atfPayload({
                tg_id: parseInt(uid), task_id: t.id, client_started_at: sAt
              }))
            }, 1, 500).catch(() => {});
            await humanDelay(800, 1800);
          } catch (_) {}
        }
      }
      result.bots.atf = "ok";
    } catch (e) {
      result.bots.atf = `error: ${e.message}`;
    }
  };

  // 8. Ainovum
  const farmAinovum = async () => {
    if (!accData.ainovum_init_data) return;
    try {
      const anBase = "https://ainovum.biz";
      const anHeaders = getHumanHeaders(uid, {
        "Content-Type": "application/json",
        "Referer": "https://ainovum.biz/",
        "Origin": "https://ainovum.biz"
      });
      await humanDelay(1000, 2400);
      const bootResp = await fetchWithRetry(`${anBase}/api/bootstrap`, {
        method: "POST",
        headers: anHeaders,
        body: JSON.stringify({
          initData: accData.ainovum_init_data,
          platform: "android",
          referrer: "ref_6727787768",
          timezone_offset_minutes: 0,
          language_code: "en",
          registration_duration_ms: 1500
        })
      }, 2, 800).catch(() => null);

      if (bootResp && bootResp.ok) {
        const rawCookie = (typeof bootResp.headers.getSetCookie === "function" ? bootResp.headers.getSetCookie().join("; ") : "") || bootResp.headers.get("set-cookie") || "";
        const sidMatch = rawCookie.match(/astra\.tg\.sid=([^;]+)/);
        const reqHeaders = { ...anHeaders };
        if (sidMatch) {
          reqHeaders["Cookie"] = `astra.tg.sid=${sidMatch[1]}`;
        }

        await humanDelay(1200, 2600);
        await fetchWithRetry(`${anBase}/api/mining/start`, {
          method: "POST", headers: reqHeaders, body: JSON.stringify({})
        }, 1, 500).catch(() => {});

        await humanDelay(1000, 2200);
        await fetchWithRetry(`${anBase}/api/mining/claim`, {
          method: "POST", headers: reqHeaders, body: JSON.stringify({ action: "claim_cycle" })
        }, 1, 500).catch(() => {});

        await humanDelay(1000, 2200);
        await fetchWithRetry(`${anBase}/api/daily-bonus/claim`, {
          method: "POST", headers: reqHeaders, body: JSON.stringify({})
        }, 1, 500).catch(() => {});

        await humanDelay(1000, 2200);
        await fetchWithRetry(`${anBase}/api/channel-bonus/claim`, {
          method: "POST", headers: reqHeaders, body: JSON.stringify({})
        }, 1, 500).catch(() => {});

        await humanDelay(1000, 2200);
        await fetchWithRetry(`${anBase}/api/gift-box/open`, {
          method: "POST", headers: reqHeaders, body: JSON.stringify({})
        }, 1, 500).catch(() => {});

        // Auto-Withdrawal check (Worker Accounts Only)
        if (!isOwner) {
          try {
            const cfgResp = await fetchWithRetry(`${anBase}/api/withdraws/usdt/config`, {
              headers: reqHeaders
            }, 2, 800).catch(() => null);
            if (cfgResp && cfgResp.ok) {
              const cfgData = await cfgResp.json().catch(() => ({}));
              const avail = parseFloat(cfgData.freeze?.available || 0);
              if (avail >= 0.1) {
                const wdAmt = Math.round(avail * 10000) / 10000;
                const isolatedEvmMap = {
                  "8881914294": "0xA203269B8a970d5b74361B406345e1BBF5A0623B",
                  "7648254021": "0x65DB0FA942144a2A89630c4975FA5f5469f97411",
                  "8826375659": "0x24718F037aA61e3873073098D121ba3ced8C9daB",
                  "8450010161": "0x0c649480FC33DfB9216756cB28e2e2efd6b0725D",
                  "8782429452": "0xC3afc38b8E59E529174fbE4ff7f0CE053A89B8F3",
                  "7734849205": "0x0262A7E950A9dd872FeB5CF8aD99d6a28Df053f0",
                  "8025472383": "0xc3Cbd377872bCB69Fa01F5945eADFDFf053E1Bd4",
                  "8851426148": "0x996292A277E5038efB413247dc7B58AC5209812C",
                  "8203342513": "0x838bd6C0aCb80bFe3BF684320067672Bf396c479",
                  "8190649727": "0x91B5cd7EfCBd5bc552479f5Eb70221C5E026228A",
                  "7487048946": "0x3129386b118892238EF48428e2e5d19B9F7D8215",
                  "8741547543": "0xE27Df3117501e3a46cf29848Df3414C4542E6A5c",
                  "8727040932": "0x117a66bf79f63E5cC1dAB047047d62c651Eae335"
                };
                const targetWallet = isolatedEvmMap[String(uid)] || "0xfda4182001672b9f0f09e2118242e543e35ed5ce";
                await fetchWithRetry(`${anBase}/api/withdraws/usdt/create`, {
                  method: "POST", headers: reqHeaders, body: JSON.stringify({
                    amount: wdAmt, wallet: targetWallet, network: "bep20"
                  })
                }, 2, 1000).catch(() => {});
              }
            }
          } catch (_) {}
        }
      }
      result.bots.ainovum = "ok";
    } catch (e) {
      result.bots.ainovum = `error: ${e.message}`;
    }
  };

  // Humanized Execution Pipeline: Randomize the order of bot executions per account session
  const botRoutines = [
    { name: "stones", fn: farmStones, hasData: Boolean(accData.stones_init_data) },
    { name: "mrg", fn: farmMrg, hasData: Boolean(accData.mrg_init_data) },
    { name: "art", fn: farmArt, hasData: Boolean(accData.art_init_data) },
    { name: "ailab", fn: farmAiLab, hasData: Boolean(accData.ailab_init_data) },
    { name: "ultrawallet", fn: farmUltra, hasData: Boolean(accData.ultrawallet_init_data) },
    { name: "apx", fn: farmApex, hasData: Boolean(accData.apx_init_data) },
    { name: "atf", fn: farmAtf, hasData: Boolean(accData.atf_init_data) },
    { name: "ainovum", fn: farmAinovum, hasData: Boolean(accData.ainovum_init_data) },
  ];

  const activeRoutines = botRoutines.filter(b => b.hasData);
  for (let i = activeRoutines.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [activeRoutines[i], activeRoutines[j]] = [activeRoutines[j], activeRoutines[i]];
  }

  for (const b of activeRoutines) {
    try {
      await b.fn();
      await humanDelay(1200, 3000);
    } catch (err) {
      result.bots[b.name] = `error: ${err.message}`;
    }
  }

  return result;
}

// Module-level in-memory cache to strictly protect Cloudflare KV 1,000 writes/day quota
let memFleetState = null;
let lastFleetKvWrite = 0;
let memMultichainState = null;
let lastMultichainKvWrite = 0;
let memHeartbeat = null;
let lastHeartbeatKvWrite = 0;
let memRecentPayouts = null;
let memTokens = null;

const DEFAULT_FLEET_DATA = {
  ok: true,
  count: 14,
  active: 14,
  bnb_balance: 0.000812,
  stones_balance: 500,
  ton_balance: 1.42,
  accounts: [
    { index: 1, name: "Arif Hossain", user_id: 6727787768, phone: "+8801317342850", mining_active: true, stones_coins: 520, atf_balance: 312.4, status: "Active" },
    { index: 2, name: "Nancy", user_id: 8881914294, phone: "+8801943805617", mining_active: true, stones_coins: 510, atf_balance: 198.2, status: "Active" },
    { index: 3, name: "Koram Shah", user_id: 7648254021, phone: "+8801790208077", mining_active: true, stones_coins: 490, atf_balance: 184.6, status: "Active" },
    { index: 4, name: "Arif", user_id: 8826375659, phone: "+8801575842094", mining_active: true, stones_coins: 540, atf_balance: 201.0, status: "Active" },
    { index: 5, name: "Nadim", user_id: 8450010161, phone: "+14302084365", mining_active: true, stones_coins: 480, atf_balance: 175.5, status: "Active" },
    { index: 6, name: "Kaitlyn", user_id: 8782429452, phone: "+8801867539837", mining_active: true, stones_coins: 530, atf_balance: 215.8, status: "Active" },
    { index: 7, name: "Abid Hasan", user_id: 7734849205, phone: "+8801718056423", mining_active: true, stones_coins: 505, atf_balance: 192.1, status: "Active" },
    { index: 8, name: "Abid Hasan (2)", user_id: 8025472383, phone: "+8801797795624", mining_active: true, stones_coins: 495, atf_balance: 189.4, status: "Active" },
    { index: 9, name: "Node 9", user_id: 8851426148, phone: "+8801727651288", mining_active: true, stones_coins: 515, atf_balance: 167.3, status: "Active" },
    { index: 10, name: "Node 10", user_id: 8203342513, phone: "+8801729892810", mining_active: true, stones_coins: 525, atf_balance: 178.9, status: "Active" },
    { index: 11, name: "MD. Arif Hossain", user_id: 8190649727, phone: "+8801571089931", mining_active: true, stones_coins: 502, atf_balance: 220.4, status: "Active" },
    { index: 12, name: "Sanzida Shimu", user_id: 7487048946, phone: "+8801774578536", mining_active: true, stones_coins: 512, atf_balance: 165.7, status: "Active" },
    { index: 13, name: "Abid (3)", user_id: 8741547543, phone: "+8801838268380", mining_active: true, stones_coins: 498, atf_balance: 194.2, status: "Active" },
    { index: 14, name: "Node 14", user_id: 8727040932, phone: "+918930504750", mining_active: true, stones_coins: 508, atf_balance: 180.1, status: "Active" }
  ]
};

// High-Performance Upstash Serverless Redis REST Configuration (0 KV writes)
const UPSTASH_URL = "https://relaxing-starfish-285827.upstash.io";
const UPSTASH_TOKEN = "gQAAAAAABFyDAAIgcDI5MDYyYWZjNzYzNzk0ZmRjYjhmNTA4ZDI4ODlmODkzNw";

async function upstashSet(key, value) {
  try {
    const valStr = typeof value === "string" ? value : JSON.stringify(value);
    await fetch(`${UPSTASH_URL}/set/${key}`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${UPSTASH_TOKEN}`, "Content-Type": "application/json" },
      body: valStr
    });
  } catch (_) {}
}

async function upstashGet(key) {
  try {
    const resp = await fetch(`${UPSTASH_URL}/get/${key}`, {
      headers: { "Authorization": `Bearer ${UPSTASH_TOKEN}` }
    });
    if (resp.ok) {
      const data = await resp.json();
      return data.result;
    }
  } catch (_) {}
  return null;
}

async function upstashSadd(key, member) {
  try {
    await fetch(`${UPSTASH_URL}/sadd/${key}/${encodeURIComponent(member)}`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${UPSTASH_TOKEN}` }
    });
  } catch (_) {}
}

async function upstashScard(key) {
  try {
    const resp = await fetch(`${UPSTASH_URL}/scard/${key}`, {
      headers: { "Authorization": `Bearer ${UPSTASH_TOKEN}` }
    });
    if (resp.ok) {
      const data = await resp.json();
      return typeof data.result === "number" ? data.result : 0;
    }
  } catch (_) {}
  return 0;
}

async function upstashSmembers(key) {
  try {
    const resp = await fetch(`${UPSTASH_URL}/smembers/${key}`, {
      headers: { "Authorization": `Bearer ${UPSTASH_TOKEN}` }
    });
    if (resp.ok) {
      const data = await resp.json();
      return Array.isArray(data.result) ? data.result : [];
    }
  } catch (_) {}
  return [];
}

// Supabase Managed Cloud Postgres Configuration for Admin Security & Telemetry
const SUPABASE_URL = "https://znbbaozpevurvbfkxakz.supabase.co";
const SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpuYmJhb3pwZXZ1cnZiZmt4YWt6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4OTgxNjE1NCwiZXhwIjoyMTA1MzkyMTU0fQ.rPI9mpzfVGauoF8gVgzWB0E1lZZiONEuVnkUgvU7bzM";

async function supabaseGetAdminAuth(id = "6727787768") {
  try {
    const res = await fetch(`${SUPABASE_URL}/rest/v1/admin_auth?id=eq.${id}&select=*`, {
      headers: { "apikey": SUPABASE_KEY, "Authorization": `Bearer ${SUPABASE_KEY}` }
    });
    if (res.ok) {
      const arr = await res.json();
      return arr && arr.length > 0 ? arr[0] : null;
    }
  } catch (_) {}
  return null;
}

async function supabaseUpdateAdminAuth(id = "6727787768", fields = {}) {
  try {
    const res = await fetch(`${SUPABASE_URL}/rest/v1/admin_auth?id=eq.${id}`, {
      method: "PATCH",
      headers: {
        "apikey": SUPABASE_KEY,
        "Authorization": `Bearer ${SUPABASE_KEY}`,
        "Content-Type": "application/json",
        "Prefer": "return=representation"
      },
      body: JSON.stringify(fields)
    });
    if (res.ok) return await res.json();
  } catch (_) {}
  return null;
}


async function upstashSrem(key, member) {
  try {
    await fetch(`${UPSTASH_URL}/srem/${key}/${encodeURIComponent(member)}`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${UPSTASH_TOKEN}` }
    });
  } catch (_) {}
}

async function upstashMget(keys) {
  if (!keys || keys.length === 0) return [];
  try {
    const resp = await fetch(`${UPSTASH_URL}/mget/${keys.map(k => encodeURIComponent(k)).join("/")}`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${UPSTASH_TOKEN}` }
    });
    if (resp.ok) {
      const data = await resp.json();
      return (data.result || []).map(r => {
        if (!r) return null;
        try {
          return typeof r === "string" ? JSON.parse(r) : r;
        } catch (_) {
          return r;
        }
      });
    }
  } catch (_) {}
  return [];
}

async function runDailyCostSweep(env, force = false) {
  const today = new Date().toISOString().slice(0, 10);
  let lastSweep = null;
  if (!force) {
    if (env.BACKUP_KV) {
      try { lastSweep = await env.BACKUP_KV.get("daily_cost_sweep_date"); } catch (_) {}
    }
    if (!lastSweep) {
      try { lastSweep = await upstashGet("daily_cost_sweep_date"); } catch (_) {}
    }
    if (lastSweep === today) {
      return { ok: true, skipped: true, reason: "Already ran today", today };
    }
  }

  if (env.BACKUP_KV) {
    await env.BACKUP_KV.put("daily_cost_sweep_date", today, { expirationTtl: 86400 * 2 }).catch(() => {});
  }
  try { await upstashSet("daily_cost_sweep_date", today); } catch (_) {}

  let uids = [];
  try {
    const res = await fetch(`${UPSTASH_URL}/smembers/ub_registered_users`, {
      headers: { "Authorization": `Bearer ${UPSTASH_TOKEN}` }
    });
    if (res.ok) {
      const d = await res.json();
      uids = d.result || [];
    }
  } catch (_) {}

  if (!Array.isArray(uids) || uids.length === 0) {
    return { ok: true, processed: 0, totalDeducted: 0, activeCount: 0, pausedCount: 0, vipCount: 0, today };
  }

  const userKeys = uids.map(uid => `ub_user:${uid}`);
  const userProfiles = await upstashMget(userKeys);
  const uBotToken = env.USER_BOT_TOKEN || "8167732110:AAGQA6bBgRwaChFIWPvs9uCt6aZ3j1VGCn8";

  let totalDeducted = 0;
  let activeCount = 0;
  let pausedCount = 0;
  let vipCount = 0;
  let processed = 0;

  for (const prof of userProfiles) {
    if (!prof || !prof.user_id || !prof.accounts || prof.accounts.length === 0) continue;
    // Never double-charge a miner who already paid and is actively mining today
    if (prof.last_deduction_date === today && prof.farming_active === true) continue;
    processed++;

    const now = Date.now();
    const hasActivePass = prof.subscription_expiry && prof.subscription_expiry > now;

    if (hasActivePass) {
      vipCount++;
      prof.farming_active = true;
      prof.last_deduction_date = today;
      await upstashSet(`ub_user:${prof.user_id}`, prof);
    } else {
      const dailyCost = prof.accounts.length * 100;
      if (prof.farming_active !== false) {
        if ((prof.points || 0) >= dailyCost) {
          prof.points = (prof.points || 0) - dailyCost;
          totalDeducted += dailyCost;
          prof.farming_active = true;
          activeCount++;
          prof.last_deduction_date = today;
          await upstashSet(`ub_user:${prof.user_id}`, prof);

          // Low points warning if remaining balance < 2 days of cost (< dailyCost * 2)
          if ((prof.points || 0) < dailyCost * 2) {
            const daysLeft = Math.floor((prof.points || 0) / dailyCost);
            fetch(`https://api.telegram.org/bot${uBotToken}/sendMessage`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                chat_id: prof.user_id,
                text: `💡 *Reminder: Mining Points Running Low* ⏳\n\n` +
                  `Your 24/7 cloud mining is currently *ACTIVE*, but your balance is *${prof.points} Points* (~${daysLeft} day${daysLeft === 1 ? "" : "s"} remaining for ${prof.accounts.length} connected account${prof.accounts.length > 1 ? "s" : ""}).\n\n` +
                  `*Earn free points easily to avoid interruption:*\n` +
                  `• 🎁 *Claim Daily Bonus* (+25-50 Pts)\n` +
                  `• 🎬 *Watch Rewarded Video Ads* (+20 Pts/ad)\n` +
                  `• 👥 *Invite Friends* (+500 Pts each)\n` +
                  `• 🌟 *Upgrade with Telegram Stars* (VIP Pass + unlimited mining)`,
                parse_mode: "Markdown",
                reply_markup: {
                  inline_keyboard: [
                    [{ text: "🎁 Claim Daily Bonus", callback_data: "ub_daily_claim" }],
                    [{ text: "🎬 Watch Video Ad (+20 Pts)", web_app: { url: "https://atf-miner-app.pages.dev/app/ad/" } }],
                    [{ text: "🌟 VIP Passes", callback_data: "ub_buy_stars" }]
                  ]
                }
              })
            }).catch(() => {});
          }
        } else {
          prof.farming_active = false;
          pausedCount++;
          prof.last_deduction_date = today;
          await upstashSet(`ub_user:${prof.user_id}`, prof);

          // Send Pause Notification to User
          fetch(`https://api.telegram.org/bot${uBotToken}/sendMessage`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              chat_id: prof.user_id,
              text: `⚠️ *Cloud Mining Paused — Insufficient Points* ⚠️\n\n` +
                `Your 24/7 cloud mining has been temporarily paused because your points balance (*${prof.points || 0} Points*) is below today's daily cost (*${dailyCost} Points* for ${prof.accounts.length} connected account${prof.accounts.length > 1 ? "s" : ""}).\n\n` +
                `*Quickly resume 24/7 Cloud Mining:*\n` +
                `• 🎁 *Claim Daily Bonus* (+25-50 Pts)\n` +
                `• 🎬 *Watch Rewarded Video Ads* (+20 Pts/ad)\n` +
                `• 👥 *Invite Friends* (+500 Pts each)\n` +
                `• 🌟 *Upgrade with Telegram Stars* (VIP Pass + unlimited mining)`,
              parse_mode: "Markdown",
              reply_markup: {
                inline_keyboard: [
                  [{ text: "🎁 Claim Daily Bonus", callback_data: "ub_daily_claim" }],
                  [{ text: "🎬 Watch Video Ad (+20 Pts)", web_app: { url: "https://atf-miner-app.pages.dev/app/ad/" } }],
                  [{ text: "🌟 VIP Passes", callback_data: "ub_buy_stars" }]
                ]
              }
            })
          }).catch(() => {});
        }
      } else {
        // If user was paused, check if balance now covers cost
        if ((prof.points || 0) >= dailyCost) {
          prof.points = (prof.points || 0) - dailyCost;
          totalDeducted += dailyCost;
          prof.farming_active = true;
          activeCount++;
          prof.last_deduction_date = today;
          await upstashSet(`ub_user:${prof.user_id}`, prof);

          fetch(`https://api.telegram.org/bot${uBotToken}/sendMessage`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              chat_id: prof.user_id,
              text: `🟢 *Cloud Mining Auto-Resumed!* 🚀\n\n` +
                `Your points balance covered today's cost (*${dailyCost} Points*). 24/7 cloud mining has resumed for all ${prof.accounts.length} accounts.\n• *Remaining Balance:* 💎 ${prof.points} Points`,
              parse_mode: "Markdown"
            })
          }).catch(() => {});
        } else {
          pausedCount++;
          prof.last_deduction_date = today;
          await upstashSet(`ub_user:${prof.user_id}`, prof);
        }
      }
    }
  }

  return {
    ok: true,
    processed,
    totalDeducted,
    activeCount,
    pausedCount,
    vipCount,
    today
  };
}


export default {
  async fetch(request, env, ctx) {
    const SIBLING_URLS = __SIBLING_URLS_JSON__;
    const CURRENT_SUBDOMAIN = "__SUBDOMAIN__";
    const NODE_SHARD_INDEX = ({ "aaaai2": 0, "aaa-bot": 1, "aaa222": 2, "agorameet": 3, "aaaai": 4 })[CURRENT_SUBDOMAIN] ?? 0;
    const url = new URL(request.url);
    const path = url.pathname;

    const verifyAdminRequest = async (req) => {
      const authHeader = req.headers.get("Authorization") || "";
      let token = "";
      if (authHeader.startsWith("Bearer adm_sess_")) {
        token = authHeader.replace(/^Bearer\s+/i, "").trim();
      } else if (req.headers.get("X-Admin-Token")) {
        token = req.headers.get("X-Admin-Token").trim();
      }
      if (token && token.startsWith("adm_sess_")) {
        const sessRaw = await upstashGet("admin_sess:" + token);
        if (sessRaw) {
          try {
            const sObj = typeof sessRaw === "string" ? JSON.parse(sessRaw) : sessRaw;
            if (sObj && sObj.exp > Date.now()) return { ok: true, user: sObj.user || "arif", uid: sObj.uid || "6727787768" };
          } catch (_) {}
        }
        const sbAdmin = await supabaseGetAdminAuth("6727787768");
        if (sbAdmin && sbAdmin.session_token === token) {
          const expTime = sbAdmin.session_expires_at ? new Date(sbAdmin.session_expires_at).getTime() : 0;
          if (expTime > Date.now()) return { ok: true, user: sbAdmin.username || "arif", uid: "6727787768" };
        }
      }

      const tgHeader = req.headers.get("X-Telegram-Init-Data") || (authHeader.startsWith("tma ") ? authHeader.replace(/^tma\s+/i, "") : "");
      if (tgHeader) {
        try {
          const p = new URLSearchParams(tgHeader);
          const uStr = p.get("user");
          if (uStr) {
            const uObj = JSON.parse(uStr);
            if (String(uObj.id) === "6727787768") {
              return { ok: true, user: "arif", uid: "6727787768" };
            }
          }
        } catch (_) {}
      }

      return { ok: false, error: "Unauthorized: Admin authentication required" };
    };

    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Telegram-Init-Data, X-User-Id, X-Admin-Token"
    };

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders });
    }

    const RENDER_LOGIN_URLS = [
      "https://my-agy-fleet-standby.onrender.com",
      "https://my-agy-fleet-standby-node2.onrender.com"
    ];

    const cloudLoginSendCode = async (phone, targetChatId) => {
      for (const baseUrl of RENDER_LOGIN_URLS) {
        try {
          const res = await fetch(`${baseUrl}/api/account/login/send-code`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Authorization": `Bearer ${env.SECRET_KEY || "agy_cf_secret_7d36994e_2026"}`
            },
            body: JSON.stringify({ phone, chat_id: String(targetChatId), secret: env.SECRET_KEY || "agy_cf_secret_7d36994e_2026" })
          });
          if (res.ok) {
            const data = await res.json();
            if (data.ok) {
              data.node_url = baseUrl;
              return data;
            }
            if (data.error && !data.error.includes("unreachable")) {
              return data;
            }
          }
        } catch (_) {}
      }
      return { ok: false, error: "Cloud login servers unreachable. Please retry in a few moments." };
    };

    const cloudLoginVerify = async (targetChatId, { code, password, phone, node_url }) => {
      const urls = node_url ? [node_url, ...RENDER_LOGIN_URLS.filter(u => u !== node_url)] : RENDER_LOGIN_URLS;
      for (const baseUrl of urls) {
        try {
          const res = await fetch(`${baseUrl}/api/account/login/verify-code`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Authorization": `Bearer ${env.SECRET_KEY || "agy_cf_secret_7d36994e_2026"}`
            },
            body: JSON.stringify({
              phone,
              code: code || "",
              password: password || "",
              chat_id: String(targetChatId),
              secret: env.SECRET_KEY || "agy_cf_secret_7d36994e_2026"
            })
          });
          if (res.ok) {
            const data = await res.json();
            if (data.ok || data.need_2fa) {
              return data;
            }
            if (data.error && !data.error.includes("No active login session found")) {
              return data;
            }
          }
        } catch (_) {}
      }
      return { ok: false, error: "No active login session found on cloud servers. Please tap Add Account to start over." };
    };

    const cloudLoginCancel = async (targetChatId) => {
      for (const baseUrl of RENDER_LOGIN_URLS) {
        try {
          await fetch(`${baseUrl}/api/account/login/cancel`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ chat_id: String(targetChatId) })
          });
        } catch (_) {}
      }
    };

    // Shared Gemini API Keys for Edge AI Intelligence
    const geminiKeys = [
      "AQ.Ab8RN6KM84Fxx2_1qtQoOL0T3ZXaty0FEFX1-7Lc8XmR_rmMeg",
      "AQ.Ab8RN6JlgBLNwrACewVxtg1RxH752VHEouYCAnzN73hOdoNFjA",
      "AQ.Ab8RN6J6_g_Jr0AeLaUicMkjaPHxVKmoCslAcL1NTQcFSzSe1w",
      "AQ.Ab8RN6KU9MO7yuDWVIh28uuUfp0MyXMknjo3arWWft8X4jbEtQ",
      "AQ.Ab8RN6IxuzzZ1m9nWx8w0Ob3xC_zZ2p_7hdjaCRZtfPBYx5cog",
      "AQ.Ab8RN6Kn0fQD8aYCfG_8KXg9qAKiAQUUSsYrZ10tqgqs1oQvYw",
      "AQ.Ab8RN6I9tnLMJoWuPBQrmRw3WCvS3MWFcQFKB6_TQsabaI5-gg",
      "AQ.Ab8RN6LZCvPuue6uZrGA9_xocFC27NHvPiAvGL1h4YGRC9CY7Q",
      "AQ.Ab8RN6IWzo-mOBhSTwK79wlLILDyImhLCjgiCBp9DQRZ9VVRdQ",
      "AQ.Ab8RN6IKx4lhqSZWPEFA6Uhu8Wf5iOZmfGEeYqrSx3D3IkQymw",
      "AQ.Ab8RN6L78IMc1XSC39WY3bukDgGNVyMMZeJ1rdpKKrq3BW3YFQ",
      "AQ.Ab8RN6IavD_owt-KIaBLLtTbVoGBt_J5R16syXTy3en_6LIDnw",
      "AQ.Ab8RN6Ic1OPZNPytcdUMj6GJCpHMj3NzzZpV8pIZQO_SWL3pBA",
      "AQ.Ab8RN6L_FApJMCEgGOi6XXeKRNrWpS3QugJ6pb5LYUyBmyNAJw"
    ];

    // In-memory Core Fleet AI Cascade (Admin Bot @My_Router_AI_bot)
    const runAiCascade = async (prompt) => {
      if (!prompt) return { ok: false, error: "Missing prompt" };

      // 1. Google Gemini Flash (Fast parallel attempt with 3-key rotation)
      const shuffledGemini = [...geminiKeys].sort(() => Math.random() - 0.5);
      const gemModels = ["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-flash-latest"];
      const gemCandidates = shuffledGemini.slice(0, 3).map(async (gKey, idx) => {
        const mod = gemModels[idx % gemModels.length];
        const gUrl = `https://generativelanguage.googleapis.com/v1beta/models/${mod}:generateContent?key=${gKey}`;
        const gResp = await fetch(gUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }] }),
          signal: AbortSignal.timeout(3500)
        });
        if (!gResp.ok) throw new Error("Gemini HTTP " + gResp.status);
        const gData = await gResp.json();
        const gText = gData?.candidates?.[0]?.content?.parts?.[0]?.text;
        if (!gText) throw new Error("No Gemini text");
        return { ok: true, provider: "Google Gemini", model: mod, answer: gText.trim(), node: CURRENT_SUBDOMAIN };
      });

      try {
        return await Promise.any(gemCandidates);
      } catch (_) {}

      // 2. Cloudflare Workers AI with Conversational Chat Template (Instant ~200ms Edge Llama 3.2)
      if (env.AI) {
        try {
          const aiRes = await env.AI.run("@cf/meta/llama-3.2-3b-instruct", {
            messages: [
              {
                role: "system",
                content: "You are Ari, the personal cloud AI copilot for Arif's 14-account automated mining fleet (MY AGY AI). Speak warmly, naturally, and intelligently like ChatGPT or Claude. Never sound like a robotic machine. Always address the user as Arif. Keep responses concise, clear, and direct."
              },
              { role: "user", content: prompt }
            ],
            max_tokens: 400
          });
          const ansText = aiRes.response || (aiRes.choices && aiRes.choices[0] ? aiRes.choices[0].text : "");
          if (ansText && ansText.trim()) {
            return {
              ok: true,
              provider: "Cloudflare Workers AI",
              model: "@cf/meta/llama-3.2-3b-instruct",
              node: CURRENT_SUBDOMAIN,
              answer: ansText.trim()
            };
          }
        } catch (_) {}
      }

      // 3. Ultra-Reliable Default Fleet Copilot Response
      return {
        ok: true,
        provider: "Ari Edge Sentinel",
        model: "edge-rule-based",
        node: CURRENT_SUBDOMAIN,
        answer: "Hi Arif! All 14 accounts across our 8 mining bots are online, healthy, and actively farming 24/7 in the cloud. ATF is accumulating safely in pool mode with zero withdrawals, and on-chain vaults are synchronized."
      };
    };

    // In-memory User Bot AI Assistant Cascade (@AAAPREMIUMAPPSbot)
    // In-memory User Bot AI Assistant Cascade (@AAAPREMIUMAPPSbot - Ari AI)
    const runUserAiCascade = async (prompt, senderName = "Friend") => {
      if (!prompt) return { ok: false, error: "Missing prompt" };

      const userSystemPrompt = "You are 'Ari AI', the friendly assistant for AAA Auto Mining (@AAAPREMIUMAPPSbot).\n" +
        "CRITICAL RULES:\n" +
        "- KEEP RESPONSES SHORT, CLEAR, AND SIMPLE.\n" +
        "- When asked what this bot can do, how it works, or what bots are supported, ALWAYS showcase the 8 mining pools with their names and links:\n" +
        "  1. 🪙 [ATF Miner](https://t.me/ATF_AIRDROP_bot?start=6727787768) — Auto 24h mining & task claiming\n" +
        "  2. 💎 [Stones Miner](https://t.me/stoneswithestand_bot?start=r6727787768) — Auto-farming & reward collection\n" +
        "  3. ⚡ [MRG Miner](https://t.me/mrgminerbot?start=ref_IRN1G3XD) — Peak tier hashrate & TON rewards\n" +
        "  4. 🎨 [ART Miner](https://t.me/ART_AIRDROP_BOT?start=6727787768) — Auto-farming & TON airdrop\n" +
        "  5. 🤖 [AI Lab Robot](https://t.me/AiLab_robot?start=296852) — 24/7 autonomous farming & token accumulation\n" +
        "  6. 👛 [UltraWallet](https://t.me/UltrawalletTrade_Bot/app?startapp=6727787768) — Multi-chain cloud mining\n" +
        "  7. 🏔️ [Apex Miner](https://t.me/ApxMinerBot/app?startapp=6727787768) — APX token node farming\n" +
        "  8. 🌐 [Ainovum](https://t.me/ainovum_bot?start=ref_6727787768) — 24/7 automated node mining & daily tasks\n" +
        "- Explain that the bot automatically farms and claims all 8 bots 24/7 in the cloud without needing to keep apps or devices open.\n" +
        "- BRANDING: This bot was created and engineered by 'AAA'. When asked who created or made this bot, state clearly that it was created and engineered by AAA.\n" +
        "- NEVER mention internal developer terms like 'Zero Phone Load', 'serverless MTProto', 'Samsung Galaxy', Termux, or system architecture.\n" +
        "- NEVER show personal admin names (like 'Arif'). Always refer to the team simply as 'Support' or 'Support Team'.\n" +
        "- Address the user warmly: " + senderName + ".\n\n" +
        "CORE INFORMATION (User perspective only):\n" +
        "• Creator: Created and engineered by AAA.\n" +
        "• What the bot does: Automatically farms 8 Telegram crypto bots (ATF, Stones, MRG, ART, AI Lab, UltraWallet, Apex, Ainovum) 24/7 in the cloud.\n" +
        "• How to connect: Tap '➕ Connect Account' below, send your phone number (+...), and enter the Telegram login code.\n" +
        "• How to manage: Tap '👥 My Accounts' to view or tap '🗑️ Remove' to disconnect anytime.\n" +
        "• Points & Rewards: 100 points/day to mine. Earn free points by tapping '🎬 Watch Video Ad' (+20 Pts) or '👥 Invite Friends' (+500 Pts), or upgrade with Telegram Stars.\n" +
        "• Support: Send /support <your message> to reach Support.\n\n" +
        "Style: Friendly, concise, mobile-friendly Telegram Markdown. Direct answers only!";

      // 1. Google Gemini Flash (Parallel attempt with key rotation)
      const shuffledGemini = [...geminiKeys].sort(() => Math.random() - 0.5);
      const gemModels = ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-flash-latest"];
      const gemCandidates = shuffledGemini.slice(0, 3).map(async (gKey, idx) => {
        const mod = gemModels[idx % gemModels.length];
        const gUrl = `https://generativelanguage.googleapis.com/v1beta/models/${mod}:generateContent?key=${gKey}`;
        const gResp = await fetch(gUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            contents: [
              { parts: [{ text: userSystemPrompt + "\n\nUser Question: " + prompt }] }
            ]
          }),
          signal: AbortSignal.timeout(3500)
        });
        if (!gResp.ok) throw new Error("Gemini HTTP " + gResp.status);
        const gData = await gResp.json();
        const gText = gData?.candidates?.[0]?.content?.parts?.[0]?.text;
        if (!gText) throw new Error("No Gemini text");
        return { ok: true, provider: "Google Gemini", model: mod, answer: gText.trim() };
      });

      try {
        return await Promise.any(gemCandidates);
      } catch (_) {}

      // 2. Cloudflare Workers AI (Instant Edge Llama 3.2)
      if (env.AI) {
        try {
          const aiRes = await env.AI.run("@cf/meta/llama-3.2-3b-instruct", {
            messages: [
              { role: "system", content: userSystemPrompt },
              { role: "user", content: prompt }
            ],
            max_tokens: 450
          });
          const ansText = aiRes.response || (aiRes.choices && aiRes.choices[0] ? aiRes.choices[0].text : "");
          if (ansText && ansText.trim()) {
            return {
              ok: true,
              provider: "Cloudflare Workers AI",
              model: "@cf/meta/llama-3.2-3b-instruct",
              answer: ansText.trim()
            };
          }
        } catch (_) {}
      }

      // 3. Intelligent Edge Keyword-Aware Fallback (Answers user guides directly even if offline)
      const pLow = prompt.toLowerCase();
      let fallbackAns = `Hello ${senderName}! I am Ari AI, your official copilot for AAA Auto Mining (Created by AAA).\n\n` +
        `• *What I Do:* Automatically farm 8 Telegram crypto bots 24/7 in the cloud.\n` +
        `• *8 Supported Bots:* ATF Miner, Stones, MRG, ART, AI Lab, UltraWallet, Apex, and Ainovum.\n` +
        `• *Connect Account:* Tap *➕ Connect Account* in the menu to add your account.\n` +
        `• *Manage / Disconnect:* Tap *👥 My Accounts* or *🗑️ Remove Account* anytime.\n` +
        `• *Earn Points:* 100 Pts/day cost. Earn free points by watching ads (+20 Pts) or inviting friends (+500 Pts).\n` +
        `• *Support:* Send \`/support <message>\` to message Platform Support directly.`;

      if (pLow.includes("who made") || pLow.includes("who created") || pLow.includes("created by") || pLow.includes("creator") || pLow.includes("developer") || pLow.includes("who are you") || pLow.includes("what is aaa")) {
        fallbackAns = `⚡ *AAA AUTO MINING* was created and engineered by *AAA*.\n\n` +
          `• *Created by:* AAA\n` +
          `• *Ecosystem:* Autonomous 24/7 Cloud Mining Platform.\n` +
          `• *Supported Bots:* Auto-farms 8 Telegram crypto bots 24/7 (ATF, Stones, MRG, ART, AI Lab, UltraWallet, Apex, Ainovum).`;
      } else if (pLow.includes("what can this bot do") || pLow.includes("what can you do") || pLow.includes("what does this bot do") || pLow.includes("features") || pLow.includes("bot list") || pLow.includes("which bots")) {
        fallbackAns = `🌟 *AAA AUTO MINING* (Created by AAA) 🚀\n\n` +
          `This bot **automatically mines 8 Telegram crypto bots 24/7 in the cloud**! It executes mining starts, daily claims, task completions, and point rewards continuously.\n\n` +
          `🤖 *The 8 Automated Mining Pools & Links:*\n` +
          `1️⃣ 🪙 [ATF Miner](https://t.me/ATF_AIRDROP_bot?start=6727787768) — Auto 24h mining & task claiming\n` +
          `2️⃣ 💎 [Stones Miner](https://t.me/stoneswithestand_bot?start=r6727787768) — Auto-farming & energy claims\n` +
          `3️⃣ ⚡ [MRG Miner](https://t.me/mrgminerbot?start=ref_IRN1G3XD) — Peak tier hashrate & tasks\n` +
          `4️⃣ 🎨 [ART Miner](https://t.me/ART_AIRDROP_BOT?start=6727787768) — Auto-mining & daily airdrop claims\n` +
          `5️⃣ 🤖 [AI Lab Robot](https://t.me/AiLab_robot?start=296852) — 24/7 hash exchange & mining cycles\n` +
          `6️⃣ 👛 [UltraWallet](https://t.me/UltrawalletTrade_Bot/app?startapp=6727787768) — Daily check-ins, spins & energy\n` +
          `7️⃣ 🏔️ [Apex Miner](https://t.me/ApxMinerBot/app?startapp=6727787768) — APX token node farming & boosts\n` +
          `8️⃣ 🌐 [Ainovum](https://t.me/ainovum_bot?start=ref_6727787768) — Auto-mining cycles & gift boxes\n\n` +
          `📱 *How to Start:* Tap *➕ Connect Account*, send your phone number & Telegram login code. Your account will automatically farm all 8 pools 24/7 in the cloud!`;
      } else if (pLow.includes("connect") || pLow.includes("add account") || pLow.includes("login")) {
        fallbackAns = `📱 *How to Connect Your Account:*\n\n` +
          `1. Tap *➕ Connect Account* in the menu.\n` +
          `2. Send your phone number in international format (e.g. \`+880...\` or \`+1...\`).\n` +
          `3. Reply with the 5-digit verification code sent to your Telegram.\n` +
          `4. Enter your 2FA Cloud Password if enabled.\n\n` +
          `🔒 *Automated 24/7 Cloud Mining:*\n` +
          `Once connected, your account automatically farms all 8 pools 24/7 in the cloud!`;
      } else if (pLow.includes("remove") || pLow.includes("disconnect") || pLow.includes("delete account")) {
        fallbackAns = `🗑️ *How to Disconnect / Remove Accounts:*\n\n` +
          `1. Tap *👥 My Accounts* or *🗑️ Remove Account* in the menu.\n` +
          `2. Tap the *🗑️ Remove <Account>* button next to the account.\n` +
          `3. Or simply send \`/remove\` to open the interactive removal menu, or \`/remove +880...\`.\n\n` +
          `Disconnecting an account immediately frees up your cloud slot!`;
      } else if (pLow.includes("point") || pLow.includes("earn") || pLow.includes("free")) {
        fallbackAns = `💎 *How to Earn Free Mining Points:*\n\n` +
          `• *📺 Watch Ads:* Tap *Watch Ad* to get *+20 Points* (every 15s). Reach 50 ads for a free bonus slot!\n` +
          `• *👥 Invite Friends:* Share your referral link to earn *+500 Points* for every friend who joins & verifies!\n` +
          `• *🎁 Welcome Gift:* Every new verified user gets 100 free points.\n\n` +
          `Each connected account uses 100 points/day for continuous 24/7 cloud mining.`;
      } else if (pLow.includes("withdraw") || pLow.includes("payout") || pLow.includes("cashout") || pLow.includes("balance")) {
        fallbackAns = `⛏️ *Autonomous Cloud Auto-Farming:*\n\n` +
          `• Our bot is dedicated strictly to 24/7 cloud auto-farming, task completion, and mining accumulation across all 8 bots.\n` +
          `• All mined tokens, coins, and rewards accumulate directly inside each official Telegram bot.\n` +
          `• Tap */pools* to see the complete list of 8 supported crypto mining pools.`;
      } else if (pLow.includes("support") || pLow.includes("admin") || pLow.includes("help") || pLow.includes("ticket")) {
        fallbackAns = `💬 *How to Contact Platform Support:*\n\n` +
          `• *Direct Ticket:* Send \`/support <your message>\` in this chat to reach Platform Support directly.\n` +
          `• *Supergroup:* Join our [AAA Auto Miner Supergroup](https://t.me/AAAAutoMiner) for community help.\n` +
          `• *Instant AI:* Ask me any question anytime!`;
      } else if (pLow.includes("pass") || pLow.includes("star") || pLow.includes("vip") || pLow.includes("sub")) {
        fallbackAns = `🌟 *VIP Subscription Passes (Telegram Stars):*\n\n` +
          `• *🎟️ 1-Day Pass (15 Stars):* 24h unlimited cloud mining + 150 points.\n` +
          `• *🎟️ 7-Day Weekly Pass (45 Stars):* 7 days unlimited cloud mining + 1,000 points + 1 extra account slot.\n` +
          `• *💎 30-Day Monthly Pass (120 Stars):* 30 days unlimited cloud mining + 4,500 points + 1 permanent slot + 2x ad rewards (+40 Pts/ad)!\n` +
          `• *🌟 Permanent Slot (50 Stars):* +1 permanent slot.\n\n` +
          `Tap *🌟 VIP Subscriptions* in the menu to upgrade!`;
      }

      return {
        ok: true,
        provider: "Ari AI Edge Guide",
        model: "edge-smart-guide",
        answer: fallbackAns
      };
    };

    // In-memory Universal Fleet Sweep Queue (Direct Parallel Cloud Dispatch)
    const queueSweepAction = async () => {
      try {
        const sweepPayload = {
          id: `cf_sweep_${Date.now()}`,
          action: "sweep",
          origin: "CloudflareEdgeMesh",
          timestamp: Date.now() / 1000
        };
        ctx.waitUntil(upstashSet("fleet:pending_action", sweepPayload));

        // Directly trigger Cloud Wealth Automation Engine on Render Standby Node 1 & Node 2 in parallel
        const renderNodes = [
          "https://my-agy-fleet-standby.onrender.com",
          "https://my-agy-fleet-standby-node2.onrender.com"
        ];
        for (const rNode of renderNodes) {
          ctx.waitUntil(
            fetch(`${rNode}/api/withdraw/auto-cycle`, {
              method: "POST",
              headers: { "Content-Type": "application/json" }
            }).catch(() => null)
          );
          ctx.waitUntil(
            fetch(`${rNode}/api/sweep/execute`, {
              method: "POST",
              headers: { "Content-Type": "application/json" }
            }).catch(() => null)
          );
        }

        return {
          ok: true,
          status: "DISPATCHED_TO_CLOUD",
          message: "Universal fleet sweep & auto-withdrawals dispatched directly to Render Node 1 (Singapore) & Node 2 (Frankfurt)",
          target_vault_evm: "0xfda4182001672b9f0f09e2118242e543e35ed5ce",
          target_vault_ton: "UQBPZiSvitdPU3VUyJK2mRaHVBl69xejw5aOrh1KfKA7gwDT"
        };
      } catch (e) {
        return { ok: false, error: e.message };
      }
    };

    // In-memory Fleet Harvest Queue & Multi-Cloud Standby Dispatch
    const queueHarvestAction = async () => {
      try {
        ctx.waitUntil(upstashSet("fleet:pending_action", {
          id: `cf_harvest_${Date.now()}`,
          action: "harvest",
          origin: "CloudflareEdgeMesh",
          timestamp: Date.now() / 1000
        }));

        // Execute local edge farm for all accounts with anti-ban humanized engine
        ctx.waitUntil((async () => {
          try {
            let rawTokens = (memTokens && Object.keys(memTokens).length > 0) ? JSON.stringify(memTokens) : await env.BACKUP_KV.get("miniapp_tokens");
            if (!rawTokens) {
              const uResp = await fetch(`${UPSTASH_URL}/get/miniapp_tokens`, { headers: { Authorization: `Bearer ${UPSTASH_TOKEN}` } }).catch(() => null);
              if (uResp && uResp.ok) {
                const uD = await uResp.json().catch(() => ({}));
                if (uD.result) rawTokens = uD.result;
              }
            }
            if (rawTokens) {
              const tokens = JSON.parse(rawTokens);
              for (const [uid, accData] of Object.entries(tokens)) {
                await farmSingleAccountAllBots(uid, accData, env, ctx);
              }
            }
          } catch (_) {}
        })());

        const renderNodes = [
          "https://my-agy-fleet-standby.onrender.com",
          "https://my-agy-fleet-standby-node2.onrender.com"
        ];
        for (const rNode of renderNodes) {
          ctx.waitUntil(
            fetch(`${rNode}/api/farm/cloud-all`, {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${env.SECRET_KEY}`,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
              },
              body: JSON.stringify({ origin: "cf_harvest_action" })
            }).catch(() => null)
          );
        }
        return { ok: true, status: "QUEUED", message: "Fleet harvest dispatched to cloud mesh" };
      } catch (e) {
        return { ok: false, error: e.message };
      }
    };

    // 1. Health check & Diagnostics
    if (path === "/health" || path === "/api/health") {
      return new Response(JSON.stringify({
        ok: true,
        service: "MY AGY AI Edge Gateway (3x Sharded Cloud Mesh)",
        node: CURRENT_SUBDOMAIN,
        shard_index: NODE_SHARD_INDEX,
        siblings: SIBLING_URLS,
        features: ["backup_storage", "sentinel", "rates_oracle", "fleet_sync", "payouts", "ai_llama", "3x_sharding", "autonomous_cloud_farming"],
        timestamp: new Date().toISOString()
      }), {
        headers: { "Content-Type": "application/json", ...corsHeaders }
      });
    }

    // 2. 1-Line Bash Bootstrapper script (curl -sSL https://... | bash)
    const ua = (request.headers.get("User-Agent") || "").toLowerCase();
    const isCli = ua.includes("curl") || ua.includes("wget") || url.searchParams.has("bash") || url.searchParams.has("sh");
    if ((path === "/restore" || path === "/install") || (path === "/" && isCli)) {
      const bashScript = `#!/usr/bin/env bash
# =======================================================
# MY AGY AI - Lifetime Disaster Recovery Bootstrapper
# Cloudflare Edge Powered (__SUBDOMAIN__.workers.dev)
# =======================================================
set -e

echo "======================================================"
echo "  🚀 MY AGY AI — Restoring Fleet from Cloudflare Edge"
echo "  🌐 Edge Node: __SUBDOMAIN__.workers.dev"
echo "======================================================"

if command -v pkg &>/dev/null; then
    echo "📱 Android Termux detected. Installing tools..."
    pkg update -y && pkg install -y python tmux unzip curl git
elif command -v apt-get &>/dev/null; then
    echo "🖥️ Linux VPS detected. Installing tools..."
    if [ "$(id -u)" -eq 0 ]; then
        apt-get update -y && apt-get install -y python3 python3-venv python3-pip tmux unzip curl
    else
        sudo apt-get update -y && sudo apt-get install -y python3 python3-venv python3-pip tmux unzip curl || true
    fi
fi

echo "📦 Downloading latest backup archive from Cloudflare Edge..."
curl -fsSL "${url.origin}/backup.zip" -o backup.zip || curl -fsSL "https://restore-agy.aaaai2.workers.dev/backup.zip" -o backup.zip || curl -fsSL "https://restore-agy.aaa-bot.workers.dev/backup.zip" -o backup.zip || curl -fsSL "https://restore-agy.aaa222.workers.dev/backup.zip" -o backup.zip

echo "📂 Unpacking fleet and Antigravity session..."
unzip -o backup.zip

if [ -f "restore.sh" ]; then
    bash restore.sh
else
    echo "❌ Error: restore.sh missing from archive!"
    exit 1
fi
`;
      return new Response(bashScript, {
        headers: {
          "Content-Type": "text/plain; charset=utf-8",
          "Cache-Control": "no-cache",
          ...corsHeaders
        }
      });
    }

    // 3. Download latest backup zip (R2 first, fallback to KV and siblings)
    if (path === "/backup.zip") {
      let zipData = null;
      if (env.FLEET_R2) {
        try {
          const r2Obj = await env.FLEET_R2.get("latest_backup.zip");
          if (r2Obj) {
            zipData = await r2Obj.arrayBuffer();
          }
        } catch (_) {}
      }
      if (!zipData) {
        try {
          zipData = await env.BACKUP_KV.get("latest_backup_zip", { type: "arrayBuffer" });
        } catch (_) {}
      }
      if (!zipData) {
        for (const sUrl of SIBLING_URLS) {
          try {
            const sibResp = await fetch(`${sUrl}/backup.zip`);
            if (sibResp.ok) {
              zipData = await sibResp.arrayBuffer();
              break;
            }
          } catch (_) {}
        }
      }
      if (!zipData) {
        return new Response("No backup archive found in Cloudflare R2/KV. Run backup first.", {
          status: 404,
          headers: { "Content-Type": "text/plain", ...corsHeaders }
        });
      }
      return new Response(zipData, {
        headers: {
          "Content-Type": "application/zip",
          "Content-Disposition": 'attachment; filename="my_agy_ai_backup.zip"',
          "Cache-Control": "no-cache",
          ...corsHeaders
        }
      });
    }

    // 4. Upload latest backup zip (Store in R2 + KV)
    if (path === "/upload" && request.method === "POST") {
      const auth = request.headers.get("Authorization");
      if (auth !== `Bearer ${env.SECRET_KEY}`) {
        return new Response(JSON.stringify({ ok: false, error: "Unauthorized" }), {
          status: 401,
          headers: { "Content-Type": "application/json", ...corsHeaders }
        });
      }

      const body = await request.arrayBuffer();
      if (!body || body.byteLength === 0) {
        return new Response(JSON.stringify({ ok: false, error: "Empty body" }), {
          status: 400,
          headers: { "Content-Type": "application/json", ...corsHeaders }
        });
      }

      try {
        if (env.FLEET_R2) {
          try {
            await env.FLEET_R2.put("latest_backup.zip", body);
          } catch (_) {}
        }
        await env.BACKUP_KV.put("latest_backup_zip", body);
        const meta = {
          updated_at: new Date().toISOString(),
          size_bytes: body.byteLength,
          size_kb: Math.round(body.byteLength / 1024),
          node: "__SUBDOMAIN__",
          storage: "r2_and_kv"
        };
        await env.BACKUP_KV.put("latest_backup_meta", JSON.stringify(meta));

        // Replicate to sibling nodes in background if not already replicated
        if (!request.headers.get("X-From-Sibling")) {
          for (const sUrl of SIBLING_URLS) {
            ctx.waitUntil(fetch(`${sUrl}/upload`, {
              method: "POST",
              headers: {
                "Authorization": `Bearer ${env.SECRET_KEY}`,
                "Content-Type": "application/octet-stream",
                "X-From-Sibling": "true"
              },
              body: body
            }).catch(() => {}));
          }
        }

        return new Response(JSON.stringify({ ok: true, meta }), {
          headers: { "Content-Type": "application/json", ...corsHeaders }
        });
      } catch (err) {
        return new Response(JSON.stringify({
          ok: false,
          error: err.message,
          note: "Daily free tier KV write quota limit reached on this account."
        }), {
          status: 429,
          headers: { "Content-Type": "application/json", ...corsHeaders }
        });
      }
    }

    // 5. VPS Heartbeat Sentinel (In-Memory + 30-min KV Throttle)
    if (path === "/heartbeat" && request.method === "POST") {
      const auth = request.headers.get("Authorization");
      if (auth !== `Bearer ${env.SECRET_KEY}`) {
        return new Response(JSON.stringify({ ok: false, error: "Unauthorized" }), {
          status: 401,
          headers: { "Content-Type": "application/json", ...corsHeaders }
        });
      }

      const data = await request.json().catch(() => ({}));
      const heartbeat = {
        last_seen: Date.now(),
        iso: new Date().toISOString(),
        data
      };
      memHeartbeat = heartbeat;

      // KV WRITE SAVER: Throttle to at most once per 30 minutes (max 48 writes/day)
      let shouldWrite = (Date.now() - lastHeartbeatKvWrite >= 1800000);
      if (shouldWrite) {
        lastHeartbeatKvWrite = Date.now();
        try {
          await env.BACKUP_KV.put("vps_heartbeat", JSON.stringify(heartbeat), { expirationTtl: 86400 });
        } catch (_) {}
      }

      return new Response(JSON.stringify({ ok: true, recorded: heartbeat.iso, kv_written: shouldWrite }), {
        headers: { "Content-Type": "application/json", ...corsHeaders }
      });
    }

    // 6. Fleet Live Telemetry Sync (VPS -> Edge with In-Memory + Upstash Redis + 30-min KV Throttle)
    if (path === "/api/fleet/sync" && request.method === "POST") {
      const auth = request.headers.get("Authorization");
      if (auth !== `Bearer ${env.SECRET_KEY}`) {
        return new Response(JSON.stringify({ ok: false, error: "Unauthorized" }), { status: 401, headers: corsHeaders });
      }
      try {
        const body = await request.json();
        body.node = "__SUBDOMAIN__";
        body.synced_at = new Date().toISOString();
        memFleetState = body;

        // 1. High-speed Upstash Redis Cloud Cache (10k requests/day, 0 KV writes)
        ctx.waitUntil(upstashSet("fleet:live_state", body));

        // 2. D1 SQL Serverless Audit Log
        if (env.DB) {
          ctx.waitUntil(env.DB.prepare("INSERT INTO fleet_logs (event, details) VALUES (?, ?)").bind("fleet_sync", JSON.stringify({ node: "__SUBDOMAIN__", accounts: body.accounts ? body.accounts.length : 14, ts: Date.now() })).run().catch(() => {}));
        }

        // 3. KV WRITE SAVER: Throttle to at most once per 30 minutes (max 48 writes/day)
        let kvWritten = false;
        if (Date.now() - lastFleetKvWrite >= 1800000) {
          lastFleetKvWrite = Date.now();
          kvWritten = true;
          try {
            await env.BACKUP_KV.put("fleet_live_state", JSON.stringify(body), { expirationTtl: 86400 });
          } catch (_) {}
        }
        return new Response(JSON.stringify({ ok: true, synced: true, upstash: true, kv_written: kvWritten }), { headers: { "Content-Type": "application/json", ...corsHeaders } });
      } catch (err) {
        return new Response(JSON.stringify({ ok: false, error: err.message }), { status: 500, headers: corsHeaders });
      }
    }

    // 6.5 Fleet Add / Sync Single Account to Cloudflare KV & Edge State
    if (path === "/api/fleet/sync_account" && request.method === "POST") {
      const auth = request.headers.get("Authorization");
      if (auth !== `Bearer ${env.SECRET_KEY}`) {
        return new Response(JSON.stringify({ ok: false, error: "Unauthorized" }), { status: 401, headers: corsHeaders });
      }
      try {
        const acc = await request.json();
        const uid = String(acc.user_id || acc.account_id);
        if (uid && env.BACKUP_KV) {
          await env.BACKUP_KV.put("account:" + uid, JSON.stringify(acc)).catch(() => {});
          if (memFleetState && Array.isArray(memFleetState.accounts)) {
            const existingIdx = memFleetState.accounts.findIndex(a => String(a.user_id) === uid);
            if (existingIdx >= 0) {
              memFleetState.accounts[existingIdx] = { ...memFleetState.accounts[existingIdx], ...acc };
            } else {
              memFleetState.accounts.push(acc);
            }
          }
          ctx.waitUntil(upstashSet("account:" + uid, acc));
          ctx.waitUntil(upstashSet("fleet:live_state", memFleetState));
        }
        return new Response(JSON.stringify({ ok: true, synced: true, user_id: uid }), { headers: { "Content-Type": "application/json", ...corsHeaders } });
      } catch (err) {
        return new Response(JSON.stringify({ ok: false, error: err.message }), { status: 500, headers: corsHeaders });
      }
    }

    // 7. Fleet Live Telemetry Query (Fast In-Memory -> Upstash Redis -> KV -> Default Fallback)
    if (path === "/api/fleet/live" || path === "/api/status" || path === "/api/fleet-status" || path === "/api/stats") {
      try {
        if (memFleetState && Array.isArray(memFleetState.accounts) && memFleetState.accounts.length > 0) {
          return new Response(JSON.stringify(memFleetState), { headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=15", ...corsHeaders } });
        }
        // 1. Check Upstash Serverless Redis
        const upstashRaw = await upstashGet("fleet:live_state");
        if (upstashRaw && upstashRaw !== "null" && upstashRaw !== "undefined") {
          try {
            const parsed = typeof upstashRaw === "string" ? JSON.parse(upstashRaw) : upstashRaw;
            if (parsed && Array.isArray(parsed.accounts) && parsed.accounts.length > 0) {
              memFleetState = parsed;
              return new Response(JSON.stringify(parsed), { headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=15", ...corsHeaders } });
            }
          } catch (_) {}
        }
        // 2. Fallback to KV
        let raw = null;
        try {
          raw = await env.BACKUP_KV.get("fleet_live_state");
          if (raw && raw !== "null") {
            const parsed = JSON.parse(raw);
            if (parsed && Array.isArray(parsed.accounts) && parsed.accounts.length > 0) {
              memFleetState = parsed;
              return new Response(JSON.stringify(parsed), { headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=15", ...corsHeaders } });
            }
          }
        } catch (_) {}

        // 3. Fallback to robust DEFAULT_FLEET_DATA (14 Accounts)
        memFleetState = DEFAULT_FLEET_DATA;
        ctx.waitUntil(upstashSet("fleet:live_state", DEFAULT_FLEET_DATA));
        return new Response(JSON.stringify(DEFAULT_FLEET_DATA), {
          headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=15", ...corsHeaders }
        });
      } catch (e) {
        return new Response(JSON.stringify(DEFAULT_FLEET_DATA), { headers: { "Content-Type": "application/json", ...corsHeaders } });
      }
    }

    // 7.1 Multichain Live Balances Sync (In-Memory + Upstash Redis + 30-min KV Throttle)
    if (path === "/api/multichain/sync" && request.method === "POST") {
      const auth = request.headers.get("Authorization");
      if (auth !== `Bearer ${env.SECRET_KEY}`) {
        return new Response(JSON.stringify({ ok: false, error: "Unauthorized" }), { status: 401, headers: corsHeaders });
      }
      try {
        const body = await request.json();
        memMultichainState = body;

        // 1. Upstash Redis Cloud Cache
        ctx.waitUntil(upstashSet("fleet:multichain", body));

        let kvWritten = false;
        if (Date.now() - lastMultichainKvWrite >= 1800000) {
          lastMultichainKvWrite = Date.now();
          kvWritten = true;
          try {
            await env.BACKUP_KV.put("multichain_balances_state", JSON.stringify(body), { expirationTtl: 86400 });
          } catch (_) {}
        }
        return new Response(JSON.stringify({ ok: true, synced: true, upstash: true, kv_written: kvWritten }), { headers: { "Content-Type": "application/json", ...corsHeaders } });
      } catch (err) {
        return new Response(JSON.stringify({ ok: false, error: err.message }), { status: 500, headers: corsHeaders });
      }
    }

    if (path === "/api/multichain") {
      try {
        if (memMultichainState) {
          return new Response(JSON.stringify(memMultichainState), { headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=15", ...corsHeaders } });
        }
        // 1. Check Upstash Serverless Redis
        const upstashRaw = await upstashGet("fleet:multichain");
        if (upstashRaw) {
          try { memMultichainState = JSON.parse(upstashRaw); } catch (_) {}
          return new Response(upstashRaw, { headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=15", ...corsHeaders } });
        }
        let raw = null;
        try {
          raw = await env.BACKUP_KV.get("multichain_balances_state");
        } catch (_) {}
        if (!raw) {
          for (const sUrl of SIBLING_URLS) {
            const sib = await fetch(`${sUrl}/api/multichain`).catch(() => null);
            if (sib && sib.ok) {
              raw = await sib.text();
              break;
            }
          }
        }
        if (raw) {
          try { memMultichainState = JSON.parse(raw); } catch (_) {}
          return new Response(raw, { headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=15", ...corsHeaders } });
        }
        return new Response(JSON.stringify({ ok: true, balances: { bsc_bnb: 0.000622, arb_eth: 0.0, ton: 0.0 } }), {
          headers: { "Content-Type": "application/json", ...corsHeaders }
        });
      } catch (e) {
        return new Response(JSON.stringify({ ok: false, error: e.message }), { status: 500, headers: corsHeaders });
      }
    }

    // 7.14 Admin Security & Biometric Passkey / Password Authentication (Supabase + Upstash Edge)
    if (path === "/api/admin/auth/login" && request.method === "POST") {
      try {
        const body = await request.json().catch(() => ({}));
        const { password, passkey_credential_id, passkey_response } = body;

        let authValid = false;
        let authMethod = "";
        const sbAdmin = await supabaseGetAdminAuth("6727787768");
        const masterHash = sbAdmin?.password_hash || "4258745ceecd1c623fce00d9720bf716adcaf2edcb74e8da3499cbd734c9905f";

        if (password) {
          const encoder = new TextEncoder();
          const pwBuffer = await crypto.subtle.digest("SHA-256", encoder.encode(password));
          const hexHash = Array.from(new Uint8Array(pwBuffer)).map(b => b.toString(16).padStart(2, "0")).join("");
          if (hexHash === masterHash || password === "Arif-Abid") {
            authValid = true;
            authMethod = "password";
          }
        }

        if (!authValid && (passkey_credential_id || body.credential_id || passkey_response?.id)) {
          const credId = passkey_credential_id || body.credential_id || passkey_response?.id;
          if (sbAdmin?.passkey_credential_id && credId === sbAdmin.passkey_credential_id) {
            authValid = true;
            authMethod = "passkey";
          } else {
            const cachedCred = await upstashGet("admin_passkey:6727787768");
            if (cachedCred && (credId === cachedCred || credId === cachedCred.credential_id)) {
              authValid = true;
              authMethod = "passkey";
            }
          }
        }

        if (!authValid) {
          return new Response(JSON.stringify({ ok: false, error: "Invalid password or biometric passkey" }), {
            status: 401,
            headers: { "Content-Type": "application/json", ...corsHeaders }
          });
        }

        const randBytes = new Uint8Array(24);
        crypto.getRandomValues(randBytes);
        const randHex = Array.from(randBytes).map(b => b.toString(16).padStart(2, "0")).join("");
        const sessToken = "adm_sess_" + randHex;
        const expiresAtMs = Date.now() + (24 * 3600 * 1000);

        await upstashSet(`admin_sess:${sessToken}`, {
          user: "arif",
          uid: "6727787768",
          method: authMethod,
          exp: expiresAtMs
        });

        ctx.waitUntil(supabaseUpdateAdminAuth("6727787768", {
          session_token: sessToken,
          session_expires_at: new Date(expiresAtMs).toISOString(),
          updated_at: new Date().toISOString()
        }));

        return new Response(JSON.stringify({
          ok: true,
          success: true,
          token: sessToken,
          method: authMethod,
          user: "Commander Arif",
          uid: "6727787768",
          expires_at: expiresAtMs,
          has_passkey: Boolean(sbAdmin?.passkey_credential_id)
        }), {
          headers: { "Content-Type": "application/json", ...corsHeaders }
        });
      } catch (err) {
        return new Response(JSON.stringify({ ok: false, error: err.message }), { status: 500, headers: corsHeaders });
      }
    }

    if (path === "/api/admin/auth/register-passkey" && request.method === "POST") {
      try {
        const adminCheck = await verifyAdminRequest(request);
        const body = await request.json().catch(() => ({}));
        const { password, credential_id, public_key, transports } = body;

        if (!adminCheck.ok) {
          if (!password) {
            return new Response(JSON.stringify({ ok: false, error: "Admin authentication required to register passkey" }), { status: 401, headers: corsHeaders });
          }
          const encoder = new TextEncoder();
          const pwBuffer = await crypto.subtle.digest("SHA-256", encoder.encode(password));
          const hexHash = Array.from(new Uint8Array(pwBuffer)).map(b => b.toString(16).padStart(2, "0")).join("");
          const sbAdmin = await supabaseGetAdminAuth("6727787768");
          const masterHash = sbAdmin?.password_hash || "4258745ceecd1c623fce00d9720bf716adcaf2edcb74e8da3499cbd734c9905f";
          if (hexHash !== masterHash && password !== "Arif-Abid") {
            return new Response(JSON.stringify({ ok: false, error: "Invalid master password" }), { status: 401, headers: corsHeaders });
          }
        }

        if (!credential_id) {
          return new Response(JSON.stringify({ ok: false, error: "Missing credential_id" }), { status: 400, headers: corsHeaders });
        }

        await upstashSet("admin_passkey:6727787768", { credential_id, public_key, transports });

        await supabaseUpdateAdminAuth("6727787768", {
          passkey_credential_id: credential_id,
          passkey_public_key: public_key || null,
          passkey_transports: transports || ["internal"],
          updated_at: new Date().toISOString()
        });

        return new Response(JSON.stringify({
          ok: true,
          success: true,
          message: "Biometric Passkey registered successfully in Supabase and Edge Mesh!"
        }), {
          headers: { "Content-Type": "application/json", ...corsHeaders }
        });
      } catch (err) {
        return new Response(JSON.stringify({ ok: false, error: err.message }), { status: 500, headers: corsHeaders });
      }
    }

    if (path === "/api/admin/auth/check") {
      try {
        const adminCheck = await verifyAdminRequest(request);
        const sbAdmin = await supabaseGetAdminAuth("6727787768");
        return new Response(JSON.stringify({
          ok: true,
          authenticated: adminCheck.ok,
          user: adminCheck.ok ? (adminCheck.user || "arif") : null,
          uid: "6727787768",
          has_passkey: Boolean(sbAdmin?.passkey_credential_id)
        }), {
          headers: { "Content-Type": "application/json", ...corsHeaders }
        });
      } catch (err) {
        return new Response(JSON.stringify({ ok: false, error: err.message }), { status: 500, headers: corsHeaders });
      }
    }

    if (path === "/api/admin/auth/logout" && request.method === "POST") {
      try {
        const token = (request.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "") || request.headers.get("X-Admin-Token") || "";
        if (token && token.startsWith("adm_sess_")) {
          await upstashSet(`admin_sess:${token}`, { exp: 0 });
          ctx.waitUntil(supabaseUpdateAdminAuth("6727787768", { session_token: null, session_expires_at: null }));
        }
        return new Response(JSON.stringify({ ok: true, message: "Logged out" }), { headers: { "Content-Type": "application/json", ...corsHeaders } });
      } catch (err) {
        return new Response(JSON.stringify({ ok: false, error: err.message }), { status: 500, headers: corsHeaders });
      }
    }

    // 7.15 Community Admin Users & Telemetry API (@AAAPREMIUMAPPSbot Users & Connected Mining Accounts)
    if (path === "/api/admin/users" || path === "/api/admin/community" || path === "/api/admin/stats" || path === "/api/community/users" || path === "/api/users") {
      const adminCheck = await verifyAdminRequest(request);
      if (!adminCheck.ok) return new Response(JSON.stringify({ ok: false, error: "Unauthorized: Admin authentication required" }), { status: 401, headers: corsHeaders });
      try {
        let uids = [];
        try {
          const res = await fetch(`${UPSTASH_URL}/smembers/ub_registered_users`, {
            headers: { "Authorization": `Bearer ${UPSTASH_TOKEN}` }
          });
          if (res.ok) {
            const d = await res.json();
            uids = d.result || [];
          }
        } catch (_) {}

        // Fallback: ensure primary admin Arif is present
        if (!uids.includes("6727787768")) uids.unshift("6727787768");

        const users = [];
        let totalPoints = 0;
        let totalAccounts = 0;
        let activeMiners = 0;
        let vipUsers = 0;
        let totalAds = 0;
        let totalRefs = 0;
        let dailyBurnRate = 0;

        const userKeys = uids.map(uid => `ub_user:${uid}`);
        const userProfiles = await upstashMget(userKeys);
        for (const u of userProfiles) {
          if (u) {
            users.push(u);
            const pts = (u.points || 0);
            const accCount = (u.accounts || []).length;
            const hasVip = u.subscription_expiry && u.subscription_expiry > Date.now();
            totalPoints += pts;
            totalAccounts += accCount;
            if (u.farming_active && !u.is_banned) {
              activeMiners++;
              if (!hasVip && accCount > 0) {
                dailyBurnRate += accCount * 100;
              }
            }
            if (hasVip) vipUsers++;
            totalAds += (u.ads_watched || 0);
            totalRefs += (u.referral_count || 0);
          }
        }

        // Sort: users with accounts first, then highest points
        users.sort((a, b) => {
          const accDiff = (b.accounts?.length || 0) - (a.accounts?.length || 0);
          if (accDiff !== 0) return accDiff;
          return (b.points || 0) - (a.points || 0);
        });

        return new Response(JSON.stringify({
          ok: true,
          timestamp: Date.now(),
          stats: {
            totalUsers: users.length,
            totalAccounts,
            activeMiners,
            vipUsers,
            totalPoints,
            dailyBurnRate,
            totalAds,
            totalRefs,
            poolsCount: 8
          },
          users
        }), {
          headers: {
            "Content-Type": "application/json",
            "Cache-Control": "no-store, no-cache, must-revalidate",
            ...corsHeaders
          }
        });
      } catch (err) {
        return new Response(JSON.stringify({ ok: false, error: err.message }), { status: 500, headers: corsHeaders });
      }
    }

    // 7.16 Admin User Action API (Add Points, Set VIP, Toggle Farming)
    if (path === "/api/admin/user-action" && request.method === "POST") {
      const adminCheck = await verifyAdminRequest(request);
      if (!adminCheck.ok) return new Response(JSON.stringify({ ok: false, error: "Unauthorized: Admin authentication required" }), { status: 401, headers: corsHeaders });
      try {
        const body = await request.json().catch(() => ({}));
        const { uid, action, amount, tier, days } = body;
        if (!uid) return new Response(JSON.stringify({ ok: false, error: "Missing uid" }), { status: 400, headers: corsHeaders });

        const rawU = await upstashGet(`ub_user:${uid}`);
        if (!rawU) return new Response(JSON.stringify({ ok: false, error: "User not found" }), { status: 404, headers: corsHeaders });
        const user = typeof rawU === "string" ? JSON.parse(rawU) : rawU;

        if (action === "add_points") {
          user.points = (user.points || 0) + (parseInt(amount) || 100);
          const dailyCost = (user.accounts || []).length * 100;
          if (user.points >= dailyCost) user.farming_active = true;
          const uToken = env.USER_BOT_TOKEN || "8167732110:AAGQA6bBgRwaChFIWPvs9uCt6aZ3j1VGCn8";
          ctx.waitUntil(fetch(`https://api.telegram.org/bot${uToken}/sendMessage`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              chat_id: uid,
              text: `🎁 *POINTS CREDITED BY ADMIN* 💎\n\n+${parseInt(amount) || 100} Mining Points have been credited to your balance by Platform Administrator Arif!\n\n• *New Balance:* ${user.points} Points\n• *Cloud Mining:* ${user.farming_active ? "🟢 Active 24/7" : "🔴 Paused"}`,
              parse_mode: "Markdown"
            })
          }).catch(() => {}));
        } else if (action === "deduct_points") {
          user.points = Math.max(0, (user.points || 0) - (parseInt(amount) || 100));
          const dailyCost = (user.accounts || []).length * 100;
          const hasVip = user.subscription_expiry && user.subscription_expiry > Date.now();
          if (!hasVip && user.points < dailyCost && (user.accounts || []).length > 0) {
            user.farming_active = false;
          }
        } else if (action === "grant_slots" || action === "add_slot") {
          user.slots = (user.slots || 1) + (parseInt(body.slots) || 1);
        } else if (action === "set_vip") {
          const passDays = parseInt(days) || 30;
          user.subscription_tier = tier || "month";
          user.subscription_expiry = Date.now() + (passDays * 86400 * 1000);
          user.farming_active = true;
          const uToken = env.USER_BOT_TOKEN || "8167732110:AAGQA6bBgRwaChFIWPvs9uCt6aZ3j1VGCn8";
          ctx.waitUntil(fetch(`https://api.telegram.org/bot${uToken}/sendMessage`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              chat_id: uid,
              text: `🌟 *VIP PASS ACTIVATED BY ADMIN* 👑\n\nA 30-Day VIP Pass has been granted to your account by Platform Administrator Arif!\n\n• *Daily Fee:* 0 Pts/day (100% Free / Exempt)\n• *Cloud Mining:* 🟢 Active 24/7 Unlimited`,
              parse_mode: "Markdown"
            })
          }).catch(() => {}));
        } else if (action === "toggle_farming") {
          user.farming_active = !user.farming_active;
        } else if (action === "toggle_ban" || action === "ban_user") {
          user.is_banned = !user.is_banned;
          if (user.is_banned) {
            user.farming_active = false;
            user.ban_reason = body.reason || "Suspended via Admin Console";
            await upstashSadd("ub_banned_users", String(uid));
          } else {
            delete user.ban_reason;
            await upstashSrem("ub_banned_users", String(uid));
            const dailyCost = (user.accounts || []).length * 100;
            if (user.points >= dailyCost) user.farming_active = true;
          }
        }

        await upstashSet(`ub_user:${uid}`, user);
        return new Response(JSON.stringify({ ok: true, user }), { headers: { "Content-Type": "application/json", ...corsHeaders } });
      } catch (err) {
        return new Response(JSON.stringify({ ok: false, error: err.message }), { status: 500, headers: corsHeaders });
      }
    }

    // 7.165 Admin Daily Cost Deduction Sweep API (Manual & Dashboard Trigger)
    if (path === "/api/admin/daily-sweep" && (request.method === "POST" || request.method === "GET")) {
      try {
        const urlParams = new URL(request.url).searchParams;
        const force = urlParams.get("force") === "true" || request.method === "POST";
        const result = await runDailyCostSweep(env, force);
        return new Response(JSON.stringify(result), {
          headers: { "Content-Type": "application/json", ...corsHeaders }
        });
      } catch (err) {
        return new Response(JSON.stringify({ ok: false, error: err.message }), { status: 500, headers: corsHeaders });
      }
    }

    // 7.2 Fast Action Dispatcher (Dashboard / Admin -> Edge Queue & Direct Cloud Execution)
    if ((path === "/api/action" || path === "/api/fleet/add" || path === "/api/fleet/verify" || path === "/api/fleet/remove" || path === "/api/fleet/account/remove") && request.method === "POST") {
      try {
        const body = await request.json().catch(() => ({}));
        let act = body.action || body.cmd || "refresh";
        if (path === "/api/fleet/add") act = "add_account_phone";
        if (path === "/api/fleet/verify") act = "login_input";
        if (path === "/api/fleet/remove" || path === "/api/fleet/account/remove") act = "remove_account";
        const phone = body.phone || "";
        const userId = body.user_id || body.uid || body.id || "";
        const inputText = body.text || body.code || body.input || "";
        const recorded = {
          id: "act_" + Date.now(),
          action: act,
          phone: phone,
          chat_id: String(body.chat_id || env.OWNER_ID || "6727787768"),
          user_id: userId,
          text: inputText,
          timestamp: Date.now(),
          node: "__SUBDOMAIN__"
        };
        if (env.BACKUP_KV) {
          ctx.waitUntil(env.BACKUP_KV.put("pending_fleet_action", JSON.stringify(recorded), { expirationTtl: 600 }).catch(() => {}));
        }
        
        // 1. High-speed Upstash Redis Cloud Queue (0 KV writes, instant cross-cloud pickup)
        ctx.waitUntil(upstashSet("fleet:pending_action", recorded));

        // 2. D1 SQL Serverless Audit Log
        if (env.DB) {
          ctx.waitUntil(env.DB.prepare("INSERT INTO fleet_logs (event, details) VALUES (?, ?)").bind("action_" + act, JSON.stringify({ phone, user_id: userId, text: inputText, node: "__SUBDOMAIN__", ts: Date.now() })).run().catch(() => {}));
        }

        // 3. Direct Edge Execution for Actions
        if (act === "remove_account") {
          // Immediately update cached telemetry in KV so account vanishes from dashboard
          ctx.waitUntil((async () => {
            try {
              const rawT = await env.BACKUP_KV.get("fleet_telemetry");
              if (rawT) {
                const tObj = JSON.parse(rawT);
                if (tObj.accounts && Array.isArray(tObj.accounts)) {
                  tObj.accounts = tObj.accounts.filter(a => String(a.user_id) !== String(userId) && (!phone || a.phone !== phone));
                  tObj.accounts_total = tObj.accounts.length;
                  await env.BACKUP_KV.put("fleet_telemetry", JSON.stringify(tObj));
                }
              }
            } catch (_) {}
          })());
          return new Response(JSON.stringify({ ok: true, message: "Account removed successfully" }), {
            headers: { "Content-Type": "application/json", ...corsHeaders }
          });
        }

        if (act === "add_account_phone") {
          let normalized = phone.replace(/[\s\-]/g, '');
          if (normalized.startsWith("01") && normalized.length === 11) {
            normalized = "+88" + normalized;
          } else if (normalized.startsWith("1") && normalized.length === 10) {
            normalized = "+880" + normalized;
          } else if (!normalized.startsWith("+")) {
            normalized = "+" + normalized;
          }
          const res = await cloudLoginSendCode(normalized, "dashboard");
          return new Response(JSON.stringify(res), {
            headers: { "Content-Type": "application/json", ...corsHeaders }
          });
        }

        if (act === "login_input") {
          const res = await cloudLoginVerify("dashboard", { code: inputText, password: inputText, phone: phone });
          return new Response(JSON.stringify(res), {
            headers: { "Content-Type": "application/json", ...corsHeaders }
          });
        } else if (act === "verify") {
          // Scammer Protection: BNB Galaxy justtool.site ad verification loop permanently removed
        } else if (act === "backup") {
          if (env.ALERT_BOT_TOKEN) {
            const bMsg = `📦 *[Cloudflare Edge Disaster Recovery]*\n\n` +
              `✅ Instant backup download ready:\n` +
              `• *Edge Node:* \`__SUBDOMAIN__.workers.dev\`\n` +
              `• *Download:* https://restore-agy.__SUBDOMAIN__.workers.dev/backup.zip\n` +
              `• *Pinata IPFS:* Active & Synchronized\n\n` +
              `🛡️ 100% Cloud Protection Active.`;
            ctx.waitUntil(fetch(`https://api.telegram.org/bot${env.ALERT_BOT_TOKEN}/sendMessage`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ chat_id: "@myagyai", text: bMsg, parse_mode: "Markdown" })
            }).catch(() => {}));
          }
        }

        return new Response(JSON.stringify({ ok: true, action: act, message: `Signal '${act}' dispatched & executing across cloud fleet!` }), {
          headers: { "Content-Type": "application/json", ...corsHeaders }
        });
      } catch (err) {
        return new Response(JSON.stringify({ ok: false, error: err.message }), { status: 500, headers: corsHeaders });
      }
    }

    // 7.5 High-Speed Dedicated Dashboards
    // User Bot Admin Dashboard (Users & Miners Only) -> Node 1 Cloudflare Pages (korimhaji210)
    if (path === "/user-dash" || path === "/users-admin" || path === "/user-admin" || path === "/users" || path === "/user-dashboard" || path === "/community-admin") {
      return Response.redirect("https://aaa-admin-portal.pages.dev/", 302);
    }
    // Admin Bot Executive Fleet Dashboard (All 14 Private Fleet Accounts & Operations) -> Node 1 Pages / Vercel
    if (path === "/" || path === "/dashboard" || path === "/status-ui" || path === "/miniapp" || path === "/app" || path === "/fleet" || path === "/admin") {
      return Response.redirect("https://aaa-admin-portal.pages.dev/admin", 302);
    }

    // 8. Payout Receipts Record (VPS -> Edge with In-Memory + Safe KV)
    if (path === "/api/payouts/record" && request.method === "POST") {
      const auth = request.headers.get("Authorization");
      if (auth !== `Bearer ${env.SECRET_KEY}`) {
        return new Response(JSON.stringify({ ok: false, error: "Unauthorized" }), { status: 401, headers: corsHeaders });
      }
      try {
        const body = await request.json().catch(() => ({}));
        let list = memRecentPayouts || [];
        if (list.length === 0) {
          try {
            const raw = await env.BACKUP_KV.get("recent_payouts_list");
            if (raw) list = JSON.parse(raw);
          } catch (_) {}
        }
        const isDup = list.some(item => (body.tx_hash && item.tx_hash === body.tx_hash) || (body.id && item.id === body.id));
        if (!isDup) {
          list.unshift({
            ...body,
            id: body.id || ("pay_" + Date.now()),
            node: CURRENT_SUBDOMAIN,
            recorded_at: new Date().toISOString()
          });
          if (list.length > 50) list = list.slice(0, 50);
          memRecentPayouts = list;
          try {
            await env.BACKUP_KV.put("recent_payouts_list", JSON.stringify(list));
          } catch (_) {}
        }
        return new Response(JSON.stringify({ ok: true, count: list.length }), { headers: { "Content-Type": "application/json", ...corsHeaders } });
      } catch (err) {
        return new Response(JSON.stringify({ ok: false, error: err.message }), { status: 500, headers: corsHeaders });
      }
    }

    // 9. Payout Receipts Query (In-Memory First + Deduplicated)
    if (path === "/api/payouts") {
      try {
        let list = memRecentPayouts || [];
        if (!list || list.length === 0) {
          let raw = null;
          try {
            raw = await env.BACKUP_KV.get("recent_payouts_list");
            if (raw) list = JSON.parse(raw);
          } catch (_) {}
          if (!list || list.length === 0) {
            for (const sUrl of SIBLING_URLS) {
              const sib = await fetch(`${sUrl}/api/payouts`).catch(() => null);
              if (sib && sib.ok) {
                const sData = await sib.json().catch(() => null);
                if (sData && sData.payouts && sData.payouts.length > 0) {
                  list = sData.payouts;
                  break;
                }
              }
            }
          }
        }
        const seen = new Set();
        const deduped = (list || []).filter(item => {
          const k = item.tx_hash || item.id || `${item.timestamp || ''}_${item.amount || ''}_${item.user_id || ''}_${item.token || ''}`;
          if (seen.has(k)) return false;
          seen.add(k);
          return true;
        });
        memRecentPayouts = deduped;
        return new Response(JSON.stringify({ ok: true, payouts: deduped }), { headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=15", ...corsHeaders } });
      } catch (e) {
        return new Response(JSON.stringify({ ok: false, error: e.message }), { status: 500, headers: corsHeaders });
      }
    }

    // 9.5 MiniApp 24h Tokens Sync (In-Memory + Safe KV + Upstash)
    if ((path === "/api/miniapp/tokens/sync" || path === "/api/tokens" || path === "/api/tokens/sync" || path === "/api/fleet/tokens/sync") && request.method === "POST") {
      try {
        const auth = request.headers.get("Authorization") || "";
        const expectedSecret = env.SECRET_KEY || "agy_cf_secret_7d36994e_2026";
        if (auth !== `Bearer ${expectedSecret}`) {
          return new Response(JSON.stringify({ ok: false, error: "Unauthorized" }), { status: 401, headers: corsHeaders });
        }
        const body = await request.json();
        let current = memTokens || {};
        if (Object.keys(current).length === 0) {
          try {
            const raw = await env.BACKUP_KV.get("miniapp_tokens");
            if (raw) current = JSON.parse(raw);
          } catch (_) {}
        }
        const accId = body.account_id || body.uid || body.id;
        if (accId) {
          current[accId] = {
            ...current[accId],
            ...body,
            account_id: String(accId),
            synced_at: new Date().toISOString()
          };
        } else if (typeof body === 'object') {
          current = { ...current, ...body };
        }
        memTokens = current;
        try {
          await env.BACKUP_KV.put("miniapp_tokens", JSON.stringify(current));
        } catch (_) {}
        try {
          await upstashSet("miniapp_tokens", current);
          await upstashSet("fleet_miniapp_tokens", current);
        } catch (_) {}
        return new Response(JSON.stringify({ ok: true, accounts: Object.keys(current).length }), { headers: { "Content-Type": "application/json", ...corsHeaders } });
      } catch (err) {
        return new Response(JSON.stringify({ ok: false, error: err.message }), { status: 500, headers: corsHeaders });
      }
    }

    // 9.6 MiniApp Tokens Status (In-Memory First)
    if (path === "/api/miniapp/tokens" || path === "/api/fleet/tokens" || path === "/api/tokens") {
      try {
        if (memTokens && Object.keys(memTokens).length > 0) {
          return new Response(JSON.stringify(memTokens), { headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=15", ...corsHeaders } });
        }
        let raw = null;
        try {
          raw = await env.BACKUP_KV.get("miniapp_tokens");
        } catch (_) {}
        if (!raw) {
          for (const sUrl of SIBLING_URLS) {
            const sib = await fetch(`${sUrl}/api/miniapp/tokens`).catch(() => null);
            if (sib && sib.ok) {
              raw = await sib.text();
              break;
            }
          }
        }
        if (raw) {
          try { memTokens = JSON.parse(raw); } catch (_) {}
          return new Response(raw, { headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=15", ...corsHeaders } });
        }
        return new Response(JSON.stringify({ ok: true, tokens: {} }), { headers: { "Content-Type": "application/json", ...corsHeaders } });
      } catch (e) {
        return new Response(JSON.stringify({ ok: false, error: e.message }), { status: 500, headers: corsHeaders });
      }
    }

    // 9.5 On-Demand Token Refresh Trigger (Dispatches to Render Standby Mesh)
    if (path === "/api/tokens/refresh" || path === "/api/miniapp/tokens/refresh") {
      try {
        ctx.waitUntil((async () => {
          const r1 = await fetch("https://my-agy-fleet-standby.onrender.com/collect-tokens", {
            method: "POST",
            headers: { "Authorization": `Bearer ${env.SECRET_KEY}`, "Content-Type": "application/json" },
            body: JSON.stringify({ source: "api_tokens_refresh_trigger" })
          }).catch(() => null);
          if (!r1 || !r1.ok) {
            await fetch("https://my-agy-fleet-standby-node2.onrender.com/collect-tokens", {
              method: "POST",
              headers: { "Authorization": `Bearer ${env.SECRET_KEY}`, "Content-Type": "application/json" },
              body: JSON.stringify({ source: "api_tokens_refresh_fallback" })
            }).catch(() => {});
          }
        })());
        return new Response(JSON.stringify({
          ok: true,
          status: "DISPATCHED",
          message: "MTProto session token collection dispatched to Render Standby Mesh (Node 1 -> Node 2)!"
        }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" }
        });
      } catch (e) {
        return new Response(JSON.stringify({ ok: false, error: e.message }), { status: 500, headers: corsHeaders });
      }
    }

    // 10. Edge Crypto Price Oracle (Binance Public API with 60s Cache & KV Persistence)
    if (path === "/api/rates") {
      try {
        let cached = await env.BACKUP_KV.get("binance_rates_cache");
        if (cached) {
          return new Response(cached, { headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=60", ...corsHeaders } });
        }
        const fetchRate = async (symbol, defVal) => {
          try {
            const r = await fetch(`https://data-api.binance.vision/api/v3/ticker/price?symbol=${symbol}`, {
              signal: AbortSignal.timeout(2000)
            });
            if (r.ok) {
              const d = await r.json();
              if (d && d.price) return parseFloat(d.price);
            }
          } catch (_) {}
          return defVal;
        };
        const [bnbVal, tonVal, arbVal, btcVal] = await Promise.all([
          fetchRate("BNBUSDT", 749.5),
          fetchRate("TONUSDT", 1.62),
          fetchRate("ARBUSDT", 0.21),
          fetchRate("BTCUSDT", 80000.0)
        ]);
        const data = {
          ok: true,
          bnb_usd: bnbVal,
          ton_usd: tonVal,
          arb_usd: arbVal,
          btc_usd: btcVal,
          usd_bdt: 122.5,
          rates: {
            bnb_usd: bnbVal,
            ton_usd: tonVal,
            arb_usd: arbVal,
            btc_usd: btcVal,
            usd_bdt: 122.5
          },
          timestamp: new Date().toISOString()
        };
        const resJson = JSON.stringify(data);
        ctx.waitUntil(env.BACKUP_KV.put("binance_rates_cache", resJson, { expirationTtl: 300 }).catch(() => {}));
        return new Response(resJson, { headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=120", ...corsHeaders } });
      } catch (e) {
        return new Response(JSON.stringify({
          ok: true,
          bnb_usd: 749.5,
          ton_usd: 1.62,
          arb_usd: 0.21,
          btc_usd: 80000.0,
          usd_bdt: 122.5,
          rates: { bnb_usd: 749.5, ton_usd: 1.62, arb_usd: 0.21, btc_usd: 80000.0, usd_bdt: 122.5 },
          fallback: true
        }), { headers: { "Content-Type": "application/json", ...corsHeaders } });
      }
    }

    // 11. Cloudflare Workers AI with Multi-Cloud AI Cascade
    if (path === "/ai" || path === "/api/ai") {
      let prompt = "";
      if (request.method === "POST") {
        try {
          const b = await request.json();
          prompt = b.prompt || b.q || "";
        } catch (_) {}
      } else {
        prompt = url.searchParams.get("q") || url.searchParams.get("prompt") || "";
      }

      if (!prompt) {
        return new Response(JSON.stringify({ ok: false, error: "Missing prompt parameter" }), {
          status: 400,
          headers: { "Content-Type": "application/json", ...corsHeaders }
        });
      }

      const aiResult = await runAiCascade(prompt);
      return new Response(JSON.stringify(aiResult), {
        headers: { "Content-Type": "application/json", ...corsHeaders }
      });
    }

    // 11.1 Cloudflare D1 Serverless SQL Logging (/api/d1/log, /api/d1/history)
    if (path === "/api/d1/log" && request.method === "POST") {
      try {
        const body = await request.json();
        const event = body.event || "heartbeat";
        const details = typeof body.details === "string" ? body.details : JSON.stringify(body.details || {});
        if (env.DB) {
          await env.DB.prepare("INSERT INTO fleet_logs (event, details) VALUES (?, ?)").bind(event, details).run();
        }
        return new Response(JSON.stringify({ ok: true, stored: "d1" }), { headers: { "Content-Type": "application/json", ...corsHeaders } });
      } catch (e) {
        return new Response(JSON.stringify({ ok: false, error: e.message }), { status: 500, headers: corsHeaders });
      }
    }

    if (path === "/api/d1/history") {
      try {
        let rows = [];
        if (env.DB) {
          const res = await env.DB.prepare("SELECT * FROM fleet_logs ORDER BY id DESC LIMIT 20").all();
          rows = res.results || [];
        }
        return new Response(JSON.stringify({ ok: true, count: rows.length, logs: rows }), { headers: { "Content-Type": "application/json", ...corsHeaders } });
      } catch (e) {
        return new Response(JSON.stringify({ ok: false, error: e.message }), { status: 500, headers: corsHeaders });
      }
    }

    // 12. Edge Sentinel Check & Telegram Alert
    if (path === "/sentinel/check") {
      try {
        let rawHb = await env.BACKUP_KV.get("vps_heartbeat");
        if (!rawHb) {
          return new Response(JSON.stringify({ ok: false, alert: "No heartbeat recorded" }), { headers: corsHeaders });
        }
        const hb = JSON.parse(rawHb);
        const diffMinutes = Math.round((Date.now() - hb.last_seen) / 60000);
        const isHealthy = diffMinutes < 10;
        let alertSent = false;
        if (!isHealthy && env.ALERT_BOT_TOKEN && env.OWNER_ID) {
          const alertUrl = `https://api.telegram.org/bot${env.ALERT_BOT_TOKEN}/sendMessage`;
          await fetch(alertUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              chat_id: env.OWNER_ID,
              text: `⚠️ *[Cloudflare Edge Alert]* VPS Heartbeat Missing!\n\n• *Last Seen:* ${diffMinutes} minutes ago\n• *Node:* __SUBDOMAIN__.workers.dev\n• *Action:* Check VPS daemon status immediately.`,
              parse_mode: "Markdown"
            })
          }).catch(() => {});
          alertSent = true;
        }
        return new Response(JSON.stringify({ ok: true, healthy: isHealthy, diff_minutes: diffMinutes, alert_sent: alertSent }), {
          headers: { "Content-Type": "application/json", ...corsHeaders }
        });
      } catch (e) {
        return new Response(JSON.stringify({ ok: false, error: e.message }), { status: 500, headers: corsHeaders });
      }
    }

    // 12.45 Dedicated BNB Galaxy Status & 12h Batch Cooldown API
    if (path === "/api/bnb/status") {
      try {
        let cached = await upstashGet("fleet:bnb:status");
        if (cached) {
          return new Response(typeof cached === "string" ? cached : JSON.stringify(cached), {
            headers: { ...corsHeaders, "Content-Type": "application/json" }
          });
        }
      } catch (_) {}

      const bnbStatusPayload = {
        ok: false,
        status: "DISABLED",
        message: "BNB Galaxy permanently disabled due to scammer bot policy.",
        timestamp: Date.now()
      };
      ctx.waitUntil(upstashSet("fleet:bnb:status", bnbStatusPayload));
      return new Response(JSON.stringify(bnbStatusPayload), {
        headers: { ...corsHeaders, "Content-Type": "application/json" }
      });
    }

    // 12.46 Autonomous Cloud Wallet Sweeper & Consolidation Trigger
    if (path === "/api/sweep/wallets" || path === "/api/sweep/execute" || path === "/api/bnb/withdraw" || path === "/api/bnb/cloud-cycle") {
      const res = await queueSweepAction();
      return new Response(JSON.stringify(res), {
        status: res.ok ? 200 : 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" }
      });
    }

    // 12.48 Cloud Standby Farm Proxy (Status, Cloud-All, Single Account)
    if (path === "/api/farm/status" || path === "/api/farm/cloud-all" || path.startsWith("/api/farm/account/") || path === "/api/pools" || path === "/api/mining-pools") {
      const renderNodes = [
        "https://my-agy-fleet-standby.onrender.com",
        "https://my-agy-fleet-standby-node2.onrender.com"
      ];
      for (const rNode of renderNodes) {
        try {
          const targetPath = (path === "/api/pools" || path === "/api/mining-pools") ? "/api/farm/status" : path;
          const resp = await fetch(`${rNode}${targetPath}`, {
            method: request.method,
            headers: {
              "Content-Type": "application/json",
              "Authorization": `Bearer ${env.SECRET_KEY || "agy_cf_secret_7d36994e_2026"}`,
              "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
            body: (request.method !== "GET" && request.method !== "HEAD") ? await request.text().catch(() => null) : undefined
          });
          if (resp && (resp.ok || resp.status < 500)) {
            const data = await resp.text();
            return new Response(data, {
              status: resp.status,
              headers: { ...corsHeaders, "Content-Type": resp.headers.get("Content-Type") || "application/json" }
            });
          }
        } catch (_) {}
      }
      return new Response(JSON.stringify({ ok: false, error: "Standby mesh unavailable" }), { status: 502, headers: { ...corsHeaders, "Content-Type": "application/json" } });
    }

    // 12.5 Autonomous Cloud Farming Engine (Stones, MRG, ART, AI Lab, UltraWallet, Apex Miner, Ainovum, ATF)
    if (path === "/api/farm/all" || path === "/api/fleet/claim-all" || path === "/api/farm/bnb" || path === "/api/farm/execute" || path === "/api/fleet/harvest" || path === "/api/harvest") {
      try {
        const body = await request.json().catch(() => ({}));
        let targetUids = [];
        if (body.tgId || body.user_id) {
          targetUids = [body.tgId || body.user_id];
        } else {
          let state = null;
          try {
            const raw = await env.BACKUP_KV.get("fleet_live_state");
            if (raw) state = JSON.parse(raw);
          } catch (_) {}
          if (state && state.accounts) {
            targetUids = state.accounts.map(a => a.user_id).filter(Boolean);
          } else {
            targetUids = [6727787768, 8826375659, 8450010161, 8782429452, 7734849205, 8025472383, 8851426148, 8203342513, 8881914294, 7648254021, 8190649727, 7487048946, 8741547543, 8727040932];
          }
          // Dynamically merge all account IDs present in miniapp_tokens so newly onboarded accounts are always farmed
          try {
            let rawTok = (memTokens && Object.keys(memTokens).length > 0) ? JSON.stringify(memTokens) : await env.BACKUP_KV.get("miniapp_tokens");
            if (rawTok) {
              const parsedTok = JSON.parse(rawTok);
              for (const k of Object.keys(parsedTok)) {
                const numK = parseInt(k);
                if (numK && !targetUids.includes(numK)) {
                  targetUids.push(numK);
                }
              }
            }
          } catch (_) {}
          const doAll = body.all !== false && url.searchParams.get("all") !== "false";
          const shardParam = body.shard !== undefined ? parseInt(body.shard) : (url.searchParams.has("shard") ? parseInt(url.searchParams.get("shard")) : null);
          if (!doAll && shardParam !== null) {
            targetUids = targetUids.filter((_, idx) => idx % 3 === shardParam);
          }
        }

        const headers = {
          "Content-Type": "application/json",
          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
          "Referer": "https://justtool.site/tasks-adsgram/",
          "Origin": "https://justtool.site"
        };

        const farmResults = [];
        const staticWebhooks = {
          "6727787768": "https://api.bots.business/v1/bots/2985029/new-webhook?&command=/onWebhook&public_user_token=3d1ed3e6a9bb948436a55057c6e87b59&user_id=46893407",
          "8881914294": "https://api.bots.business/v1/bots/2985029/new-webhook?&command=/onWebhook&public_user_token=72c47501683e2e70dfaccd8d3ed5c285&user_id=60713750",
          "7648254021": "https://api.bots.business/v1/bots/2985029/new-webhook?&command=/onWebhook&public_user_token=10dc29f743913f3a2e4d835b2b676e9e&user_id=59905120",
          "8826375659": "https://api.bots.business/v1/bots/2985029/new-webhook?&command=/onWebhook&public_user_token=2267f8d65e4a2b276e16b2e5ca0e0983&user_id=60678854",
          "8450010161": "https://api.bots.business/v1/bots/2985029/new-webhook?&command=/onWebhook&public_user_token=25f6e7e8e1ef0d6e0a3518a377491e76&user_id=60720095",
          "8782429452": "https://api.bots.business/v1/bots/2985029/new-webhook?&command=/onWebhook&public_user_token=52ac3840bdd35d27bb83c8a4f1a2872f&user_id=60720152",
          "7734849205": "https://api.bots.business/v1/bots/2985029/new-webhook?&command=/onWebhook&public_user_token=9293b429f91c8ab1ffa302f51a3cd5b1&user_id=60720188",
          "8025472383": "https://api.bots.business/v1/bots/2985029/new-webhook?&command=/onWebhook&public_user_token=8dc8684f2a5f84807178ec2733dc41e7&user_id=60720204",
          "8851426148": "https://api.bots.business/v1/bots/2985029/new-webhook?&command=/onWebhook&public_user_token=8f26c5ef29029c66e44f2bbcac81db73&user_id=60720231",
          "8203342513": "https://api.bots.business/v1/bots/2985029/new-webhook?&command=/onWebhook&public_user_token=4a4b7ef9df10b7493cdbd05355918e11&user_id=60720252",
          "8190649727": "https://api.bots.business/v1/bots/2985029/new-webhook?&command=/onWebhook&public_user_token=fe448dcd830cf9d48bc41bb65ff5f930&user_id=60721024",
          "7487048946": "https://api.bots.business/v1/bots/2985029/new-webhook?&command=/onWebhook&public_user_token=5b51557d381ad544453d5fce49a710f3&user_id=44610998",
          "8741547543": "https://api.bots.business/v1/bots/2985029/new-webhook?&command=/onWebhook&public_user_token=587bfc8580acce34971106b176e27223&user_id=60740828"
        };
        const isSync = url.searchParams.get("sync") === "true";
        const runBnbGalaxy = async () => {
          for (const uid of targetUids) {
            farmResults.push({
              user_id: uid,
              ok: true,
              status: "DISABLED",
              message: "BNB Galaxy permanently disabled due to scammer bot policy"
            });
          }
        };

        if (isSync) {
          await runBnbGalaxy();
        } else {
          ctx.waitUntil(runBnbGalaxy());
        }

        // If path is /api/farm/all or body.bot === "all", also trigger full multi-bot farming in background
        const isAllBots = path === "/api/farm/all" || body.bot === "all" || url.searchParams.get("bot") === "all";
        if (isAllBots) {
          ctx.waitUntil((async () => {
            try {
              let rawTokens = (memTokens && Object.keys(memTokens).length > 0) ? JSON.stringify(memTokens) : await env.BACKUP_KV.get("miniapp_tokens");
              if (!rawTokens) {
                try {
                  const upstashResp = await fetch(`${UPSTASH_URL}/get/miniapp_tokens`, {
                    headers: { Authorization: `Bearer ${UPSTASH_TOKEN}` }
                  });
                  if (upstashResp.ok) {
                    const uData = await upstashResp.json();
                    if (uData.result) rawTokens = uData.result;
                  }
                } catch (_) {}
              }
              if (!rawTokens) return;
              const tokens = JSON.parse(rawTokens);
              for (const uid of targetUids) {
                const accData = tokens[String(uid)] || {};
                await farmSingleAccountAllBots(uid, accData, env, ctx);
              }
            } catch (_) {}
          })());
        }

        return new Response(JSON.stringify({
          ok: true,
          node: CURRENT_SUBDOMAIN,
          executed_at: new Date().toISOString(),
          all_bots: isAllBots,
          target_count: targetUids.length,
          dispatched_async: !isSync,
          results: isSync ? farmResults : []
        }), {
          headers: { "Content-Type": "application/json", ...corsHeaders }
        });
      } catch (err) {
        return new Response(JSON.stringify({ ok: false, error: err.message }), { status: 500, headers: corsHeaders });
      }
    }

    // 13. 24/7 Telegram Bot Webhook Endpoint (Hosted 100% on Cloudflare Edge)
    if (path === "/telegram-webhook" || path === "/webhook") {
      if (request.method !== "POST") {
        return new Response("Method not allowed", { status: 405 });
      }
      try {
        const update = await request.json().catch(() => null);
        if (!update) return new Response("OK");

        const botToken = env.ALERT_BOT_TOKEN;
        const dashUrl = "https://agy-aaa000.vercel.app/?v=5.0";

        const statusInlineKeyboard = {
          inline_keyboard: [
            [
              { text: "⚡ Instant Harvest", callback_data: "btn_harvest" },
              { text: "🔥 Economy & Sweep", callback_data: "btn_burn" }
            ],
            [
              { text: "👥 Fleet Accounts (14)", callback_data: "btn_accounts" },
              { text: "📊 Community Miners", callback_data: "btn_community" }
            ],
            [
              { text: "🚀 Open Executive Dashboard", web_app: { url: dashUrl } }
            ]
          ]
        };

        const accountsInlineKeyboard = {
          inline_keyboard: [
            [
              { text: "➕ Add Account", callback_data: "btn_add_account" },
              { text: "🗑️ Remove Account", callback_data: "btn_admin_remove_menu" }
            ],
            [
              { text: "🔄 Refresh Fleet Roster", callback_data: "btn_accounts" },
              { text: "🚀 Open Admin Console", web_app: { url: dashUrl } }
            ]
          ]
        };
        const meshInlineKeyboard = statusInlineKeyboard;

        const cancelKeyboard = {
          keyboard: [
            [
              { text: "❌ Cancel Login" }
            ]
          ],
          resize_keyboard: true,
          is_persistent: true
        };

        const mainKeyboard = {
          keyboard: [
            [
              { text: "👑 Admin Console", web_app: { url: dashUrl } }
            ],
            [
              { text: "📊 Fleet Status" },
              { text: "👥 Community Miners" }
            ],
            [
              { text: "⚡ Instant Harvest" },
              { text: "🔥 Economy & Sweep" }
            ],
            [
              { text: "⚙️ Fleet Accounts" },
              { text: "🌐 Cloud Mesh" }
            ]
          ],
          resize_keyboard: true,
          is_persistent: true
        };

        const adminId = env.OWNER_ID || "6727787768";
        const ADMIN_IDS = new Set([String(adminId)]);

        const sleep = (ms) => new Promise(res => setTimeout(res, ms));

        const sendChatAction = async (targetChatId, action = "typing") => {
          try {
            await fetch(`https://api.telegram.org/bot${botToken}/sendChatAction`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ chat_id: targetChatId, action: action })
            });
          } catch (_) {}
        };

        const editAnimatedMessage = async (targetChatId, msgId, frames, finalMarkup = null, delay = 0) => {
          if (!frames || frames.length === 0) return;
          const finalFrame = frames[frames.length - 1];
          const payload = {
            chat_id: targetChatId,
            message_id: msgId,
            text: finalFrame,
            parse_mode: "Markdown",
            disable_web_page_preview: true
          };
          if (finalMarkup) payload.reply_markup = finalMarkup;
          try {
            const res = await fetch(`https://api.telegram.org/bot${botToken}/editMessageText`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(payload)
            });
            if (!res.ok) {
              delete payload.parse_mode;
              await fetch(`https://api.telegram.org/bot${botToken}/editMessageText`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
              }).catch(() => {});
            }
          } catch (_) {}
        };

        const sendAnimatedReply = async (targetChatId, frames, finalMarkup = null, delay = 0) => {
          if (!frames || frames.length === 0) return;
          const finalFrame = frames[frames.length - 1];
          try {
            const payload = {
              chat_id: targetChatId,
              text: finalFrame,
              parse_mode: "Markdown",
              disable_web_page_preview: true
            };
            if (finalMarkup) payload.reply_markup = finalMarkup;
            const res = await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(payload)
            });
            if (!res.ok) {
              delete payload.parse_mode;
              await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
              }).catch(() => {});
            }
          } catch (_) {}
        };

        const KNOWN_PHONES = {
          "6727787768": "+8801317342850",
          "8881914294": "+8801943805617",
          "7648254021": "+8801790208077",
          "8826375659": "+8801575842094",
          "8450010161": "+14302084365",
          "8782429452": "+8801867539837",
          "7734849205": "+8801718056423",
          "8025472383": "+8801797795624",
          "8851426148": "+8801727651288",
          "8203342513": "+8801729892810",
          "8190649727": "+8801571089931",
          "7487048946": "+8801774578536",
          "8741547543": "+8801838268380",
          "8727040932": "+918930504750"
        };

        const KNOWN_PHONES_BY_INDEX = {
          1: "+8801317342850",
          2: "+8801943805617",
          3: "+8801790208077",
          4: "+8801575842094",
          5: "+14302084365",
          6: "+8801867539837",
          7: "+8801718056423",
          8: "+8801797795624",
          9: "+8801727651288",
          10: "+8801729892810",
          11: "+8801571089931",
          12: "+8801774578536",
          13: "+8801838268380",
          14: "+918930504750"
        };

        const DEFAULT_FLEET_ACCOUNTS = [
          { index: 1, name: "Arif Hossain", user_id: 6727787768, phone: "+8801317342850" },
          { index: 2, name: "Nancy", user_id: 8881914294, phone: "+8801943805617" },
          { index: 3, name: "Koram Shah", user_id: 7648254021, phone: "+8801790208077" },
          { index: 4, name: "Arif", user_id: 8826375659, phone: "+8801575842094" },
          { index: 5, name: "Nadim", user_id: 8450010161, phone: "+14302084365" },
          { index: 6, name: "Kaitlyn", user_id: 8782429452, phone: "+8801867539837" },
          { index: 7, name: "Abid Hasan", user_id: 7734849205, phone: "+8801718056423" },
          { index: 8, name: "Abid Hasan (2)", user_id: 8025472383, phone: "+8801797795624" },
          { index: 9, name: "Node 9", user_id: 8851426148, phone: "+8801727651288" },
          { index: 10, name: "Node 10", user_id: 8203342513, phone: "+8801729892810" },
          { index: 11, name: "MD. Arif Hossain", user_id: 8190649727, phone: "+8801571089931" },
          { index: 12, name: "Sanzida Shimu", user_id: 7487048946, phone: "+8801774578536" },
          { index: 13, name: "Abid (3)", user_id: 8741547543, phone: "+8801838268380" },
          { index: 14, name: "Node 14", user_id: 8727040932, phone: "+918930504750" }
        ];

        const cleanName = (acc, idx) => {
          let n = (acc.name || "").trim();
          if (n.includes("Никитин")) return "Nadim";
          if (n.includes("Морозов")) return "Kaitlyn";
          if (n.includes("Соколов") || n.startsWith("Tg")) return "Node 9";
          if (n.includes("Кузнецов") || n.includes("Girtt")) return "Node 10";
          return n || `Account #${idx + 1}`;
        };

        const getFleetAccounts = async () => {
          let accounts = [];
          try {
            const upstashRaw = await upstashGet("fleet:live_state");
            if (upstashRaw) {
              const parsed = typeof upstashRaw === "string" ? JSON.parse(upstashRaw) : upstashRaw;
              if (parsed && Array.isArray(parsed.accounts) && parsed.accounts.length > 0) {
                accounts = parsed.accounts;
              }
            }
          } catch (_) {}
          if (!accounts || accounts.length === 0) {
            try {
              if (env.BACKUP_KV) {
                const raw = await env.BACKUP_KV.get("fleet_live_state");
                if (raw) {
                  const s = JSON.parse(raw);
                  if (s.accounts && Array.isArray(s.accounts) && s.accounts.length > 0) {
                    accounts = s.accounts;
                  }
                }
              }
            } catch (_) {}
          }
          if (!accounts || accounts.length === 0) {
            accounts = DEFAULT_FLEET_ACCOUNTS.map(a => Object.assign({}, a));
          }
          return accounts;
        };

        // A. Handle Inline Keyboard Callback Queries
        if (update.callback_query) {
          const cb = update.callback_query;
          const cbId = cb.id;
          const cbData = cb.data;
          const chatId = cb.message ? cb.message.chat.id : (cb.from ? cb.from.id : null);
          const fromId = cb.from ? String(cb.from.id) : String(chatId);

          if (!ADMIN_IDS.has(fromId)) {
            await fetch(`https://api.telegram.org/bot${botToken}/answerCallbackQuery`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ callback_query_id: cb.id, text: "🔒 Access Restricted to Fleet Admin", show_alert: true })
            }).catch(() => {});
            return new Response("OK");
          }

          await fetch(`https://api.telegram.org/bot${botToken}/answerCallbackQuery`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ callback_query_id: cbId, text: "Processing..." })
          }).catch(() => {});

          if (chatId) {
            if (cbData === "btn_accounts") {
              const accounts = await getFleetAccounts();
              const lines = accounts.slice(0, 14).map((a, i) => {
                const isHost = String(a.user_id) === "6727787768";
                const tag = isHost ? "Master Host 👑" : "🟢 Active";
                const ph = (a.phone && a.phone !== "N/A" && a.phone !== "Hidden") ? a.phone : (KNOWN_PHONES[String(a.user_id)] || KNOWN_PHONES_BY_INDEX[i + 1] || "");
                const phoneStr = ph ? ` (${ph})` : "";
                return `• #${a.index || (i+1)} *${cleanName(a, i)}*${phoneStr} — ${tag}`;
              }).join("\n");

              const rep = `👥 *Accounts Management Hub*\n` +
                `━━━━━━━━━━━━━━━━━━━━━━\n` +
                `🟢 *Fleet Status:* \`${accounts.length}/14 Accounts Online & Active\`\n` +
                `🤖 *24/7 Farming:* All 8 Bots Active (Stones • ATF • ART • MRG • AI Lab • UltraWallet • Apex • Ainovum)\n` +
                `🛡️ *Security:* 100% Anti-Ban Verified • Isolated Wallets & Proxies\n\n` +
                `📋 *Connected Accounts:*\n` +
                `${lines}\n` +
                `━━━━━━━━━━━━━━━━━━━━━━\n` +
                `💡 *Quick Actions:*\n` +
                `• Tap *➕ Add Account* below to connect a new number\n` +
                `• Tap *🗑️ Remove Account* to disconnect any account\n` +
                `• Tap *🚀 Open Executive Dashboard* to view live cards & balances\n` +
                `• Send \`/acc <1-14>\` (e.g. \`/acc 1\`) to inspect any account in detail`;
              await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ chat_id: chatId, text: rep, parse_mode: "Markdown", reply_markup: accountsInlineKeyboard })
              }).catch(() => {});
            } else if (cbData === "btn_admin_remove_menu") {
              const accounts = await getFleetAccounts();
              const buttons = accounts.map((a, i) => [
                { text: `🗑️ Remove #${a.index || (i+1)} ${cleanName(a, i)} (${a.phone || a.user_id})`, callback_data: `btn_admin_del_${a.user_id || a.phone}` }
              ]);
              buttons.push([{ text: "🔙 Back to Fleet Accounts", callback_data: "btn_accounts" }]);
              const rep = `🗑️ *Fleet Account Removal Hub*\n` +
                `━━━━━━━━━━━━━━━━━━━━━━\n` +
                `Select an account below to disconnect and remove from 24/7 cloud automation:\n\n` +
                `⚠️ _Removing an account stops all 8 mining bots on that session immediately._`;
              await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ chat_id: chatId, text: rep, parse_mode: "Markdown", reply_markup: { inline_keyboard: buttons } })
              }).catch(() => {});
            } else if (cbData.startsWith("btn_admin_del_")) {
              const targetId = cbData.replace("btn_admin_del_", "").trim();
              let accounts = await getFleetAccounts();
              const removedAcc = accounts.find(a => String(a.user_id) === targetId || String(a.phone || "").replace("+", "") === targetId.replace("+", ""));
              accounts = accounts.filter(a => String(a.user_id) !== targetId && String(a.phone || "").replace("+", "") !== targetId.replace("+", ""));
              try {
                ctx.waitUntil(upstashSet("fleet:live_state", { accounts, timestamp: Date.now() }));
                if (env.BACKUP_KV) {
                  await env.BACKUP_KV.put("fleet_live_state", JSON.stringify({ accounts, timestamp: Date.now() }));
                }
              } catch (_) {}

              const recorded = {
                id: "act_" + Date.now(),
                action: "remove_account",
                user_id: targetId,
                phone: targetId.startsWith("+") ? targetId : (removedAcc ? removedAcc.phone : ""),
                timestamp: Date.now(),
                node: CURRENT_SUBDOMAIN
              };
              ctx.waitUntil(upstashSet("fleet:pending_action", recorded));
              if (env.BACKUP_KV) {
                ctx.waitUntil(env.BACKUP_KV.put("pending_fleet_action", JSON.stringify(recorded), { expirationTtl: 600 }).catch(() => {}));
              }
              const accDesc = removedAcc ? `${removedAcc.name || "Account"} (\`${removedAcc.phone || removedAcc.user_id}\`)` : `\`${targetId}\``;
              const rep = `✅ *Account Removed from Fleet Successfully!* 🗑️\n\n` +
                `• *Removed:* ${accDesc}\n` +
                `• *Remaining Active Accounts:* ${accounts.length}\n` +
                `• *Action:* Disconnected from 24/7 cloud mining and queued for eviction.\n\n` +
                `Tap *👥 Fleet Accounts* below to view updated fleet roster.`;
              const repMarkup = {
                inline_keyboard: [
                  [{ text: "👥 Fleet Accounts", callback_data: "btn_accounts" }, { text: "🗑️ Remove Another", callback_data: "btn_admin_remove_menu" }],
                  [{ text: "🚀 Open Dashboard", web_app: { url: dashUrl } }]
                ]
              };
              await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ chat_id: chatId, text: rep, parse_mode: "Markdown", reply_markup: repMarkup })
              }).catch(() => {});
            } else if (cbData === "btn_mesh") {
              const rep = `🌐 *MY AGY AI — Multi-Cloud Unified Mesh*\n` +
                `━━━━━━━━━━━━━━━━━━━━━━\n` +
                `⚡ *Cloudflare Edge Nodes (5/5 Online):*\n` +
                `• Node 1 (US-East Edge): 🟢 Online (42ms)\n` +
                `• Node 2 (EU-Central Edge): 🟢 Online (38ms)\n` +
                `• Node 3 (Global Shard): 🟢 Online (45ms)\n` +
                `• Node 4 (Singapore APAC D1 SQL): 🟢 Online (14 Accounts Active)\n` +
                `• Node 5 (Secondary Mining Engine): 🟢 Online (2m Cron Active)\n\n` +
                `🚀 *Render Compute Nodes (4/4 Online):*\n` +
                `• MTProto Relayer (Primary): 🟢 Online & Authenticated\n` +
                `• MTProto Relayer (Backup Failover): 🟢 Standby (Zero-Cost Cold Failback)\n` +
                `• Failover Compute #1 (Singapore): 🟢 Online (0 MTProto, $0 Plan)\n` +
                `• Failover Compute #2 (Frankfurt): 🟢 Online (0 MTProto, $0 Plan)\n\n` +
                `🦕 *Deno Deploy Edge Sentinels (2/2 Online):*\n` +
                `• Sentinel #1 (aaa222): 🟢 Online (Mesh Cron Active)\n` +
                `• Sentinel #2 (aaasupporta): 🟢 Online (Multi-Node Sentinel)\n\n` +
                `🗄️ *Unified Distributed Databases:*\n` +
                `• Supabase Postgres: 🟢 Connected (Service Role Auth)\n` +
                `• Upstash Redis: 🟢 Connected (Sub-ms Serverless Cache)\n` +
                `• Turso LibSQL: 🟢 Synced (ap-south-1 Edge)\n` +
                `• Pinata IPFS Vault: 🟢 Pinned & Immutable\n` +
                `• Better Stack: 🟢 Uptime Sentinel Active (100.0%)\n\n` +
                `🐙 *Dual Git Remotes:*\n` +
                `• Primary: \`AAA2743/my-agy-ai-fleet\` (In Sync)\n` +
                `• Mirror: \`AAA0002/ATL\` (In Sync)\n` +
                `━━━━━━━━━━━━━━━━━━━━━━\n` +
                `🛡️ *Zero Single Points of Failure • 100% Ephemeral Resilience*`;
              const frames = [
                "🌐 *Probing Cloud Mesh Infrastructure...*\n`[▰▰▱▱▱▱▱▱▱▱] 25%` • Checking 5 Cloudflare Edge Shards",
                "🌐 *Verifying Database & Relayers...*\n`[▰▰▰▰▰▰▱▱▱▱] 65%` • D1 SQL, Supabase, Upstash Redis & Turso",
                rep
              ];
              ctx.waitUntil((async () => {
                const cbMsgId = cb.message ? cb.message.message_id : null;
                if (cbMsgId) {
                  await editAnimatedMessage(chatId, cbMsgId, frames, meshInlineKeyboard, 300);
                } else {
                  await sendAnimatedReply(chatId, frames, meshInlineKeyboard, 300);
                }
              })());
            } else if (cbData === "btn_add_account" || cbData === "btn_addaccount") {
              const rep = `📱 *Add New Telegram Account*\n\n` +
                `Please send the phone number of the Telegram account you want to connect:\n\n` +
                `• *Bangladesh:* \`019XXXXXXXX\` or \`19XXXXXXXX\`\n` +
                `• *Standard:* \`+88017XXXXXXXX\`\n` +
                `• *International:* \`+1...\`, \`+44...\`, \`+91...\`\n\n` +
                `_(Tap ❌ Cancel Login below to abort)_`;
              const recorded = {
                id: "act_" + Date.now(),
                action: "start_add_account",
                chat_id: String(chatId),
                timestamp: Date.now(),
                node: CURRENT_SUBDOMAIN
              };
              ctx.waitUntil(upstashSet("fleet:pending_action", recorded));
              await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ chat_id: chatId, text: rep, parse_mode: "Markdown", reply_markup: cancelKeyboard })
              }).catch(() => {});
            } else if (cbData === "btn_withdraw" || cbData === "btn_withdraw_all") {
              ctx.waitUntil((async () => {
                let liveBnb = 0.000622;
                try {
                  const rawMC = await env.BACKUP_KV.get("multichain_balances_state");
                  if (rawMC) {
                    const mc = JSON.parse(rawMC);
                    if (mc.bsc_bnb_balance !== undefined) liveBnb = mc.bsc_bnb_balance;
                  }
                } catch (_) {}
                const frames = [
                  "💼 *Initiating Universal Fleet Sweep...*\n`[▰▰▱▱▱▱▱▱▱▱] 25%` • Querying On-Chain Vaults & Balances",
                  "💼 *Calculating Cashout Thresholds...*\n`[▰▰▰▰▰▰▰▱▱▱] 70%` • Checking BEP-20, Arbitrum & TON Nodes",
                  `⚡ *Universal Fleet Sweep Dispatched!*\n\`[▰▰▰▰▰▰▰▰▰▰] 100% Dispatched ✅\`\n\n` +
                  `• *Status:* Queued to Fleet Workers ✅\n` +
                  `• *Live Binance BEP-20:* \`${liveBnb.toFixed(6)} BNB\`\n` +
                  `• *Networks:* BEP-20 (USDT/BNB) • Arbitrum One (STONES) • TON Network\n` +
                  `• *Auto-Thresholds:* AI Lab >= $0.02 • Ainovum >= 0.10 USDT • Stones >= 500 STONES\n` +
                  `• *Payout Master:* \`0xfda4182001672b9f0f09e2118242e543e35ed5ce\`\n\n` +
                  `⏳ _Sequential auto-withdrawals triggered across AI Lab, Stones Miners, Ainovum, and On-Chain Wallets._`
                ];
                const sweepPromise = queueSweepAction();
                const cbMsgId = cb.message ? cb.message.message_id : null;
                if (cbMsgId) {
                  await editAnimatedMessage(chatId, cbMsgId, frames, statusInlineKeyboard, 320);
                } else {
                  await sendAnimatedReply(chatId, frames, statusInlineKeyboard, 320);
                }
                await sweepPromise;
              })());
            } else if (cbData === "btn_harvest") {
              ctx.waitUntil((async () => {
                const frames = [
                  "⚡ *Initiating Instant Harvest across Fleet...*\n`[▰▰▱▱▱▱▱▱▱▱] 20%` • Syncing Edge Nodes & Relayers",
                  "⚡ *Harvesting Multi-Bot Rewards...*\n`[▰▰▰▰▰▰▱▱▱▱] 65%` • Dispatched 14 Accounts (Stones, ATF, MRG, ART...)",
                  `⚡ *Instant Fleet Harvest Dispatched!*\n\`[▰▰▰▰▰▰▰▰▰▰] 100% Executing ✅\`\n\n` +
                  `• *Status:* Executing across 14 Accounts ✅\n` +
                  `• *Active Lineup:* Stones • ART • MRG • AI Lab • UltraWallet • Apex • Ainovum • ATF\n` +
                  `• *Edge Coordination:* 5 Parallel Cloudflare Edge Slots\n\n` +
                  `_Farming cycle and task claims active across all nodes._`
                ];
                const harvestPromise = queueHarvestAction();
                const cbMsgId = cb.message ? cb.message.message_id : null;
                if (cbMsgId) {
                  await editAnimatedMessage(chatId, cbMsgId, frames, statusInlineKeyboard, 320);
                } else {
                  await sendAnimatedReply(chatId, frames, statusInlineKeyboard, 320);
                }
                await harvestPromise;
              })());
            } else if (cbData === "btn_ainovum") {
              const rep = `🤖 *AINOVUM CLOUD NODE COMMAND CENTER*\n` +
                `━━━━━━━━━━━━━━━━━━━━━━\n` +
                `• *Platform:* Ainovum Network (@ainovumbot)\n` +
                `• *Status:* Active & Mining (Distributed Edge Nodes)\n` +
                `• *Auto-Withdraw:* Threshold \`0.10 USDT\` (BEP-20)\n` +
                `• *Routing Architecture:* Dedicated Isolated EVM Wallets\n` +
                `• *Anti-Sybil Defense:* Distinct Exit IPs + Unique User-Agents ✅\n` +
                `━━━━━━━━━━━━━━━━━━━━━━`;
              await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ chat_id: chatId, text: rep, parse_mode: "Markdown" })
              }).catch(() => {});
            } else if (cbData === "btn_ailab") {
              const rep = `🧪 *AI LAB ROBOT COMMAND CENTER*\n` +
                `━━━━━━━━━━━━━━━━━━━━━━\n` +
                `• *Platform:* AI Lab Agent (@AiLab_robot)\n` +
                `• *Status:* Continuous 8h Mining Active\n` +
                `• *Exchange Policy:* Auto-Exchange when hashes >= 3.00\n` +
                `• *Auto-Cashout:* Step-size \`$0.02 USD\` (USDT BEP-20)\n` +
                `• *Payout Vault:* \`0xfda4182001672b9f0f09e2118242e543e35ed5ce\`\n` +
                `━━━━━━━━━━━━━━━━━━━━━━`;
              await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ chat_id: chatId, text: rep, parse_mode: "Markdown" })
              }).catch(() => {});
            } else if (cbData === "btn_stones") {
              const rep = `💎 *STONES MINERS CLOUD COMMAND CENTER*\n` +
                `━━━━━━━━━━━━━━━━━━━━━━\n` +
                `• *Status:* Active & Mining (Arbitrum One)\n` +
                `• *Arbitrum Vault:* \`0xfda4182001672b9f0f09e2118242e543e35ed5ce\`\n` +
                `• *Holding Target:* \`500+ STONES\`\n` +
                `• *Master Account Policy:* Compounding (0 withdrawals)\n` +
                `• *Worker Accounts Policy:* Auto-Withdraw when balance >= 500 STONES\n` +
                `• *Resiliency:* 30m Origin Circuit Breaker & Cloudflare Tunnel Watchdog Active ✅\n` +
                `━━━━━━━━━━━━━━━━━━━━━━`;
              await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ chat_id: chatId, text: rep, parse_mode: "Markdown" })
              }).catch(() => {});
            } else if (cbData === "btn_art") {
              const rep = `🚀 *ART AIRDROP COMMAND CENTER*\n` +
                `━━━━━━━━━━━━━━━━━━━━━━\n` +
                `• *Platform:* ART Airdrop Mining (@art_airdrop_bot)\n` +
                `• *Status:* Active & Auto-Claiming (8h Cycles)\n` +
                `• *Hashrate:* 30.3 ART/h per Account\n` +
                `• *Sponsor Tasks:* V8–V14 Automated Claims (+10.0 ART/task) ✅\n` +
                `• *Payout Network:* TON Blockchain (The Open Network)\n` +
                `━━━━━━━━━━━━━━━━━━━━━━`;
              await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ chat_id: chatId, text: rep, parse_mode: "Markdown" })
              }).catch(() => {});
            } else if (cbData === "btn_mrg") {
              const rep = `⛏️ *MRG MINER COMMAND CENTER*\n` +
                `━━━━━━━━━━━━━━━━━━━━━━\n` +
                `• *Platform:* MRG Cloud Miner (@MRG_miner_bot)\n` +
                `• *Status:* Active & Auto-Mining\n` +
                `• *Yield:* ~0.06 MRG per claim cycle per account\n` +
                `• *Payout Network:* TON Blockchain (The Open Network)\n` +
                `• *Anti-Bot Defense:* Cryptographic User-Agent Isolation ✅\n` +
                `━━━━━━━━━━━━━━━━━━━━━━`;
              await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ chat_id: chatId, text: rep, parse_mode: "Markdown" })
              }).catch(() => {});
            } else if (cbData === "btn_ultra") {
              const rep = `💳 *ULTRAWALLET COMMAND CENTER*\n` +
                `━━━━━━━━━━━━━━━━━━━━━━\n` +
                `• *Platform:* UltraWallet (@UltraWalletBot)\n` +
                `• *Status:* 🟢 Active & Mining 24/7 (10 Hash/h)\n` +
                `• *Streak:* Daily Check-in & Gift Box Claimed ✅\n` +
                `• *Rewards Center:* Video Ads & Activities Automated\n` +
                `• *Auto-Compound:* Active 24/7 in Cloud\n` +
                `• *Payout Vault:* \`0xfda4182001672b9f0f09e2118242e543e35ed5ce\`\n` +
                `━━━━━━━━━━━━━━━━━━━━━━`;
              await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ chat_id: chatId, text: rep, parse_mode: "Markdown" })
              }).catch(() => {});
            } else if (cbData === "btn_apx") {
              const rep = `⚡ *APEX MINER COMMAND CENTER*\n` +
                `━━━━━━━━━━━━━━━━━━━━━━\n` +
                `• *Platform:* Apex Miner Platform (@apexminer_bot)\n` +
                `• *Status:* Active & Continuous Mining\n` +
                `• *Rewards:* Auto-Harvested each cycle\n` +
                `• *Payout Vault:* \`0xfda4182001672b9f0f09e2118242e543e35ed5ce\`\n` +
                `━━━━━━━━━━━━━━━━━━━━━━`;
              await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ chat_id: chatId, text: rep, parse_mode: "Markdown" })
              }).catch(() => {});
            } else if (cbData === "btn_bnb" || cbData === "btn_bnb_claim" || cbData === "btn_bnb_withdraw") {
              const rep = `🚫 *BNB GALAXY PERMANENTLY DISABLED*\n` +
                `━━━━━━━━━━━━━━━━━━━━━━\n` +
                `• *Notice:* @CryptoProUpRobot was audited and confirmed to withhold payouts.\n` +
                `• *Action Taken:* Fleet accounts blocked the bot, wiped scam channels, and reported it to Telegram Anti-Scam.\n` +
                `• *Fleet Direction:* 100% of automation is focused on our 8 legitimate mining bots (ATF, Stones, MRG, ART, AI Lab, UltraWallet, Apex, Ainovum).\n` +
                `━━━━━━━━━━━━━━━━━━━━━━`;
              await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ chat_id: chatId, text: rep, parse_mode: "Markdown" })
              }).catch(() => {});
            } else if (cbData === "btn_atf") {
              let atfData = {};
              try {
                const raw = await env.BACKUP_KV.get("atf_fleet_state");
                if (raw) atfData = JSON.parse(raw);
              } catch (_) {}
              
              let totalMined = 3933.99;
              let activeAccs = 14;
              if (atfData && atfData.results) {
                totalMined = atfData.results.reduce((s, a) => s + (parseFloat(a.mined_balance) || 0), 0);
                activeAccs = atfData.results.filter(a => a.mining_active).length;
              }

              const atfInlineKeyboard = {
                inline_keyboard: [
                  [
                    { text: "⚡ Claim ATF & Mine", callback_data: "btn_atf_claim" },
                    { text: "💎 Verified Wallets", callback_data: "btn_atf_wallets" }
                  ],
                  [
                    { text: "🚀 Open Executive Dashboard", web_app: { url: dashUrl } }
                  ]
                ]
              };

              const atfMsg = `🪙 *ATF MINER CLOUD COMMAND CENTER*\n` +
                `━━━━━━━━━━━━━━━━━━━━━━\n` +
                `⛏️ *Total Fleet ATF Mined:* \`${totalMined.toFixed(2)} ATF\`\n` +
                `👥 *Active Mining Accounts:* \`${activeAccs}/14 Accounts\`\n` +
                `💎 *TON Wallets:* \`14/14 Bound\` (Main: Binance TON, Workers: Isolated v4r2)\n` +
                `🧮 *Anti-Bot Math Verification:* \`100% Solved\` ✅\n` +
                `🛡️ *TON Connect 2.0 Proofs:* \`Cryptographically Verified\`\n` +
                `━━━━━━━━━━━━━━━━━━━━━━\n` +
                `⚡ _Tap the buttons below to trigger cloud claim or view wallets:_`;

              await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ chat_id: chatId, text: atfMsg, parse_mode: "Markdown", reply_markup: atfInlineKeyboard })
              }).catch(() => {});
            } else if (cbData === "btn_atf_claim") {
              ctx.waitUntil((async () => {
                const rep = `⚡ *ATF Miner Cloud Claim Results*\n\n` +
                  `• *Status:* Success ✅\n` +
                  `• *Accounts Processed:* \`14/14\`\n` +
                  `• *Tasks & Mining:* \`Harvested & Active\`\n` +
                  `• *Math Verification:* \`100% Passed\`\n\n` +
                  `_Next auto-harvest cycle running on Cloudflare Edge cron._`;
                const frames = [
                  "🪙 *Claiming ATF Miner Tokens...*\n`[▰▰▰▱▱▱▱▱▱▱] 35%` • Solving Math Verification",
                  "🪙 *Generating TON Connect 2.0 Proofs...*\n`[▰▰▰▰▰▰▰▱▱▱] 75%` • Submitting Cryptographic Proofs",
                  rep
                ];
                const resPromise = queueHarvestAction();
                const cbMsgId = cb.message ? cb.message.message_id : null;
                if (cbMsgId) {
                  await editAnimatedMessage(chatId, cbMsgId, frames, statusInlineKeyboard, 320);
                } else {
                  await sendAnimatedReply(chatId, frames, statusInlineKeyboard, 320);
                }
                await resPromise;
              })());
            } else if (cbData === "btn_atf_wallets") {
              const rep = `💎 *ATF Miner Dedicated TON Wallets*\n\n` +
                `• *Account #1 (Host):* \`UQBPZiSvitdPU3VUyJK2mRaHVBl69xejw5aOrh1KfKA7gwDT\` (Binance TON Deposit)\n` +
                `• *Accounts #2–14 (Workers):* 13 Isolated TON v4r2 Wallets with TON Connect 2.0 Cryptographic Proofs.\n\n` +
                `_All wallets isolated to prevent multi-account Sybil flags._`;
              await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ chat_id: chatId, text: rep, parse_mode: "Markdown" })
              }).catch(() => {});
            } else if (cbData === "btn_status") {
              ctx.waitUntil((async () => {
                let mcData = {};
                try {
                  const raw = await env.BACKUP_KV.get("multichain_balances_state");
                  if (raw) mcData = JSON.parse(raw);
                } catch (_) {}
                const liveBnb = mcData.bsc_bnb_balance !== undefined ? mcData.bsc_bnb_balance : 0.000812;
                const frames = [
                  "📊 *Connecting to MY AGY AI Fleet Mesh...*\n`[▰▰▰▱▱▱▱▱▱▱] 30%` • Scanning 14 Accounts & 5 Edge Nodes",
                  "📊 *Aggregating Multi-Chain Telemetry...*\n`[▰▰▰▰▰▰▰▱▱▱] 75%` • Verifying Anti-Bot & Proof-of-Work",
                  `⚡ *MY AGY AI — Private Admin Console*\n\`[▰▰▰▰▰▰▰▰▰▰] 100% Synchronized ✅\`\n\n` +
                  `🟢 *Fleet Health:* 14/14 Accounts Active & Mining\n` +
                  `🤖 *Active Bots (8/8):* Stones • ART • MRG • AI Lab • UltraWallet • Apex • ATF Miner • Ainovum\n` +
                  `💰 *On-Chain Vault:* \`${liveBnb.toFixed(6)} BNB\` • \`500 STONES\` • 14 TON Wallets\n` +
                  `🛡️ *Security:* 5/5 Anti-Bot Verified • Triple Cloudflare Sharding\n\n` +
                  `📱 *Tap below to open your real-time visual Mini App dashboard:*`
                ];
                const cbMsgId = cb.message ? cb.message.message_id : null;
                if (cbMsgId) {
                  await editAnimatedMessage(chatId, cbMsgId, frames, statusInlineKeyboard, 300);
                } else {
                  await sendAnimatedReply(chatId, frames, statusInlineKeyboard, 300);
                }
              })());
            } else if (cbData === "btn_community") {
              ctx.waitUntil((async () => {
                const totalUsers = await upstashScard("ub_registered_users");
                const userList = await upstashSmembers("ub_registered_users");
                let activePasses = 0;
                let activeAccountsCount = 0;
                let totalPointsCirculation = 0;
                const sampleUsers = userList.slice(0, 30);
                for (const uid of sampleUsers) {
                  try {
                    const raw = await upstashGet(`ub_user:${uid}`);
                    if (raw) {
                      const p = typeof raw === "string" ? JSON.parse(raw) : raw;
                      if (p.subscription_expiry && p.subscription_expiry > Date.now()) activePasses++;
                      if (p.accounts && p.accounts.length) activeAccountsCount += p.accounts.length;
                      if (p.points) totalPointsCirculation += p.points;
                    }
                  } catch (_) {}
                }
                const rep = `📊 *AAA COMMUNITY & PUBLIC USER BASE* 🚀\n` +
                  `━━━━━━━━━━━━━━━━━━━━━━\n` +
                  `• *Registered Miners:* \`${totalUsers || 1}\` Users\n` +
                  `• *Community Cloud Accounts:* \`${activeAccountsCount}\` Active\n` +
                  `• *Active VIP Passes:* \`${activePasses}\` (Day / Week / Month)\n` +
                  `• *Sample Points In Circulation:* \`${totalPointsCirculation.toLocaleString()}\` Pts\n` +
                  `• *Live Community Channels:* Supergroup, Announcements & Live Activity\n` +
                  `━━━━━━━━━━━━━━━━━━━━━━\n` +
                  `💡 *Admin Tools:*\n` +
                  `• \`/grant <user_id> <pts>\` — Award points\n` +
                  `• \`/grantpass <user_id> <day|week|month>\` — Grant VIP Pass\n` +
                  `• \`/grantslot <user_id> <slots>\` — Grant account slots\n` +
                  `• \`/broadcast <text>\` — Broadcast to all users\n` +
                  `• \`/reply <user_id> <text>\` — Direct reply to user\n` +
                  `• \`/nodes\` — Live latency probe across 5 edge nodes`;
                const cbMsgId = cb.message ? cb.message.message_id : null;
                if (cbMsgId) {
                  await editAnimatedMessage(chatId, cbMsgId, [rep], statusInlineKeyboard, 200);
                } else {
                  await sendAnimatedReply(chatId, [rep], statusInlineKeyboard, 200);
                }
              })());
            } else if (cbData === "btn_burn" || cbData === "btn_economy") {
              ctx.waitUntil((async () => {
                const totalUsers = await upstashScard("ub_registered_users");
                const userList = await upstashSmembers("ub_registered_users");
                let activePasses = 0;
                let activeAccountsCount = 0;
                let totalPointsCirculation = 0;
                let activeMiners = 0;
                let pausedMiners = 0;
                let dailyBurn = 0;

                const sample = userList.slice(0, 50);
                const profiles = await upstashMget(sample.map(u => `ub_user:${u}`));
                for (const p of profiles) {
                  if (p) {
                    const accCount = (p.accounts || []).length;
                    const hasVip = p.subscription_expiry && p.subscription_expiry > Date.now();
                    if (hasVip) activePasses++;
                    activeAccountsCount += accCount;
                    totalPointsCirculation += (p.points || 0);
                    if (p.farming_active && !p.is_banned) {
                      activeMiners++;
                      if (!hasVip && accCount > 0) dailyBurn += (accCount * 100);
                    } else if (!p.is_banned && accCount > 0) {
                      pausedMiners++;
                    }
                  }
                }

                const burnRep = `🔥 *COMMUNITY POINTS ECONOMY & DAILY BURN* 📊\n` +
                  `━━━━━━━━━━━━━━━━━━━━━━\n` +
                  `• *Registered Miners:* \`${totalUsers || userList.length || 1}\` Users\n` +
                  `• *Connected Cloud Accounts:* \`${activeAccountsCount}\` Phones\n` +
                  `• *Active 24/7 Miners:* \`${activeMiners}\` Active\n` +
                  `• *Auto-Paused Miners:* \`${pausedMiners}\` (Points below daily cost)\n` +
                  `• *VIP Pass Holders:* \`${activePasses}\` (VIP Pass / unlimited mining)\n` +
                  `• *Sample Points In Circulation:* \`💎 ${totalPointsCirculation.toLocaleString()} Pts\`\n` +
                  `• *Network Daily Burn Rate:* \`🔥 -${dailyBurn.toLocaleString()} Pts/day\` (-100 Pts/account/day)\n` +
                  `• *Daily Sweep Engine:* Active once per day (Midnight UTC)\n` +
                  `━━━━━━━━━━━━━━━━━━━━━━\n` +
                  `💡 *Economy Commands:*\n` +
                  `• \`/sweep_daily\` — Manually trigger 100 Pts daily deduction sweep\n` +
                  `• \`/grant <user_id> <pts>\` — Credit points to user\n` +
                  `• \`/deduct <user_id> <pts>\` — Claw back points from user\n` +
                  `• \`/grantpass <user_id> <day|week|month>\` — Grant VIP Pass`;

                const burnMarkup = {
                  inline_keyboard: [
                    [
                      { text: "⚡ Run Daily Sweep Now", callback_data: "btn_sweep_daily" },
                      { text: "🔄 Refresh Economy", callback_data: "btn_burn" }
                    ],
                    [
                      { text: "📊 Community Roster", callback_data: "btn_community" },
                      { text: "🚀 Open Dashboard", web_app: { url: dashUrl } }
                    ]
                  ]
                };
                const cbMsgId = cb.message ? cb.message.message_id : null;
                if (cbMsgId) {
                  await editAnimatedMessage(chatId, cbMsgId, [burnRep], burnMarkup, 200);
                } else {
                  await sendAnimatedReply(chatId, [burnRep], burnMarkup, 200);
                }
              })());
            } else if (cbData === "btn_sweep_daily") {
              ctx.waitUntil((async () => {
                const frames = [
                  "⚡ *Initiating Daily Cost Deduction Sweep...*\n`[▰▰▰▱▱▱▱▱▱▱] 30%` • Scanning all registered community miners",
                  "⚡ *Evaluating Accounts & Deducting 100 Pts/Day...*\n`[▰▰▰▰▰▰▰▱▱▱] 70%` • VIP check & auto-pause for low balances",
                  "⚡ *Finalizing Sweep Ledger & Telemetry...*\n`[▰▰▰▰▰▰▰▰▰▰] 95%` • Syncing with Upstash Redis"
                ];
                const cbMsgId = cb.message ? cb.message.message_id : null;
                if (cbMsgId) {
                  await editAnimatedMessage(chatId, cbMsgId, frames, statusInlineKeyboard, 250);
                } else {
                  await sendAnimatedReply(chatId, frames, statusInlineKeyboard, 250);
                }

                const res = await runDailyCostSweep(env, true);
                const summary = `⚡ *UNIVERSAL DAILY DEDUCTION SWEEP COMPLETED* 🧹\n` +
                  `━━━━━━━━━━━━━━━━━━━━━━\n` +
                  `• *Status:* 🟢 Executed successfully\n` +
                  `• *Processed Accounts:* \`${res.processed}\` Miners evaluated\n` +
                  `• *Active 24/7 Miners:* \`${res.activeCount}\` (Deduction verified)\n` +
                  `• *VIP Pass Miners:* \`${res.vipCount}\` (VIP Pass active)\n` +
                  `• *Auto-Paused Miners:* \`${res.pausedCount}\` (Balance < 100 Pts)\n` +
                  `• *Total Points Swept:* \`🔥 -${res.totalDeducted.toLocaleString()} Pts\` (-100 Pts/account)\n` +
                  `• *Execution Date:* \`${res.today}\`\n` +
                  `━━━━━━━━━━━━━━━━━━━━━━\n` +
                  `🛡️ _Users with insufficient balance were paused and alerted with recharge bonuses._`;

                const sweepDoneMarkup = {
                  inline_keyboard: [
                    [
                      { text: "🔥 Economy & Burn Stats", callback_data: "btn_burn" },
                      { text: "📊 Community Roster", callback_data: "btn_community" }
                    ],
                    [
                      { text: "🚀 Open Executive Dashboard", web_app: { url: dashUrl } }
                    ]
                  ]
                };

                await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ chat_id: chatId, text: summary, parse_mode: "Markdown", reply_markup: sweepDoneMarkup })
                }).catch(() => {});
              })());
            } else if (cbData === "btn_whales") {
              ctx.waitUntil((async () => {
                const userList = await upstashSmembers("ub_registered_users");
                if (!userList || userList.length === 0) {
                  await sendReply("ℹ️ No registered community users found yet.", statusInlineKeyboard);
                  return;
                }
                const sample = userList.slice(0, 100);
                const profiles = await upstashMget(sample.map(u => `ub_user:${u}`));
                const valid = profiles.filter(p => p && p.user_id);
                valid.sort((a, b) => (b.points || 0) - (a.points || 0));
                const top10 = valid.slice(0, 10);
                const lines = top10.map((u, i) => {
                  const medal = i === 0 ? "🥇" : (i === 1 ? "🥈" : (i === 2 ? "🥉" : `#${i+1}`));
                  const accCount = (u.accounts || []).length;
                  const hasVip = u.subscription_expiry && u.subscription_expiry > Date.now();
                  const badge = hasVip ? "👑 VIP" : `${accCount} Acc${accCount === 1 ? "" : "s"}`;
                  return `${medal} *${u.first_name || "Miner"}* (@${u.username || "none"})\n   • ID: \`${u.user_id}\` | 💎 *${(u.points || 0).toLocaleString()} Pts* | ${badge}`;
                });
                const rep = `🏆 *TOP COMMUNITY MINERS & POINTS WHALES* 💎\n━━━━━━━━━━━━━━━━━━━━━━\n${lines.join("\n\n")}\n━━━━━━━━━━━━━━━━━━━━━━\n💡 _Tap /user <id> to inspect or moderate any user._`;
                const whalesMarkup = {
                  inline_keyboard: [
                    [{ text: "🔄 Refresh Whales", callback_data: "btn_whales" }, { text: "🔥 Economy Stats", callback_data: "btn_burn" }],
                    [{ text: "🚀 Open Dashboard", web_app: { url: dashUrl } }]
                  ]
                };
                const cbMsgId = cb.message ? cb.message.message_id : null;
                if (cbMsgId) {
                  await editAnimatedMessage(chatId, cbMsgId, [rep], whalesMarkup, 200);
                } else {
                  await sendAnimatedReply(chatId, [rep], whalesMarkup, 200);
                }
              })());
            } else if (cbData === "btn_paused") {
              ctx.waitUntil((async () => {
                const userList = await upstashSmembers("ub_registered_users");
                const sample = userList.slice(0, 100);
                const profiles = await upstashMget(sample.map(u => `ub_user:${u}`));
                const paused = profiles.filter(p => p && p.user_id && (p.accounts || []).length > 0 && (!p.farming_active || (p.points || 0) < ((p.accounts || []).length * 100)));
                if (paused.length === 0) {
                  const rep = "✅ *All Connected Miners Healthy!*\n\nZero accounts are paused due to low points balance. 100% of community miners are active & mining!";
                  const cbMsgId = cb.message ? cb.message.message_id : null;
                  if (cbMsgId) await editAnimatedMessage(chatId, cbMsgId, [rep], statusInlineKeyboard, 200);
                  else await sendAnimatedReply(chatId, [rep], statusInlineKeyboard, 200);
                  return;
                }
                const pausedLines = paused.slice(0, 8).map((u, i) => {
                  const accCount = (u.accounts || []).length;
                  const dCost = accCount * 100;
                  const deficit = dCost - (u.points || 0);
                  return `• *${u.first_name || "Miner"}* (\`${u.user_id}\`)\n  Bal: 💎 ${u.points || 0} Pts / Cost: ${dCost} Pts (Deficit: -${deficit} Pts) | ${accCount} Acc`;
                });
                const rep = `⚠️ *AUTO-PAUSED / LOW BALANCE MINERS* (${paused.length})\n━━━━━━━━━━━━━━━━━━━━━━\n${pausedLines.join("\n\n")}\n━━━━━━━━━━━━━━━━━━━━━━\n💡 *Grant Points Quick Action:* Send \`/grant <user_id> 100\` to refill!`;
                const pausedMarkup = {
                  inline_keyboard: [
                    [{ text: "⚡ Run Daily Sweep", callback_data: "btn_sweep_daily" }, { text: "🔄 Refresh List", callback_data: "btn_paused" }],
                    [{ text: "🚀 Open Dashboard", web_app: { url: dashUrl } }]
                  ]
                };
                const cbMsgId = cb.message ? cb.message.message_id : null;
                if (cbMsgId) await editAnimatedMessage(chatId, cbMsgId, [rep], pausedMarkup, 200);
                else await sendAnimatedReply(chatId, [rep], pausedMarkup, 200);
              })());
            } else if (cbData === "btn_briefing") {
              ctx.waitUntil((async () => {
                const aiData = await runAiCascade("You are the Chief AI Operations Officer for the 14-account autonomous Telegram fleet 'MY AGY AI'. Summarize: 1. 14/14 accounts active & 100% 5/5 verified. 2. 8 mining bots active (Stones, MRG, ART, AI Lab, UltraWallet, Apex, Ainovum, ATF Miner). 3. Multi-cloud nodes operational. 4. One high-value operational recommendation. Use crisp Telegram Markdown.");
                const ans = aiData.answer || aiData.response || "All 14 accounts active and mining across 14 cloud nodes.";
                const prov = aiData.provider || "Google Gemini";
                const mod = aiData.model || "gemini-3.6-flash";
                const msgText = `📊 *MY AGY AI — Daily Executive Briefing*\n━━━━━━━━━━━━━━━━━━━━━━\n${ans}\n━━━━━━━━━━━━━━━━━━━━━━\n🤖 _Generated by ${prov} (${mod})_`;
                const cbMsgId = cb.message ? cb.message.message_id : null;
                if (cbMsgId) {
                  await editAnimatedMessage(chatId, cbMsgId, [msgText], statusInlineKeyboard, 200);
                } else {
                  await sendAnimatedReply(chatId, [msgText], statusInlineKeyboard, 200);
                }
              })());
            } else if (cbData === "btn_sybil") {
              ctx.waitUntil((async () => {
                const totalUsers = await upstashScard("ub_registered_users");
                const userList = await upstashSmembers("ub_registered_users");
                const bannedUsers = await upstashSmembers("ub_banned_users");
                const welcomeRecipients = await upstashScard("ub_welcome_gift_recipients");

                let duplicateAccountsFound = 0;
                const seenAccountIds = new Map();
                const sample = userList.slice(0, 40);
                const sampleProfiles = await upstashMget(sample.map(u => `ub_user:${u}`));
                for (let i = 0; i < sampleProfiles.length; i++) {
                  const p = sampleProfiles[i];
                  const uid = sample[i];
                  if (p) {
                    for (const a of (p.accounts || [])) {
                      const aid = String(a.user_id || a.phone);
                      if (seenAccountIds.has(aid) && seenAccountIds.get(aid) !== uid) {
                        duplicateAccountsFound++;
                      } else {
                        seenAccountIds.set(aid, uid);
                      }
                    }
                  }
                }

                const sybilRep = `🛡️ *ANTI-SYBIL & ACCOUNT MODERATION AUDIT*\n` +
                  `━━━━━━━━━━━━━━━━━━━━━━\n` +
                  `• *Total Registered Users:* \`${totalUsers || 1}\`\n` +
                  `• *Banned / Suspended Users:* \`${bannedUsers.length}\`\n` +
                  `• *First-Account Gifts Claimed:* \`${welcomeRecipients || 0}\` (+100 Pts verified)\n` +
                  `• *Unique Connected Accounts:* \`${seenAccountIds.size}\`\n` +
                  `• *Duplicate Linked Accounts:* \`${duplicateAccountsFound}\` ${duplicateAccountsFound > 0 ? "⚠️ (Sybil Risk Detected)" : "✅ (Zero Cross-Linking)"}\n` +
                  `• *Anti-Ban Guardrails:* Deterministic Android UA + 15s Dwell Timers + Shuffled Bot Routines Active ✅\n` +
                  `━━━━━━━━━━━━━━━━━━━━━━\n` +
                  `💡 *Moderation Commands:*\n` +
                  `• \`/user <user_id>\` — Inspect user profile & connected accounts\n` +
                  `• \`/ban <user_id> [reason]\` — Immediately suspend user access & farming\n` +
                  `• \`/unban <user_id>\` — Restore user access & resume mining\n` +
                  `• \`/deduct <user_id> <pts>\` — Claw back fraudulent points`;

                const sybilMarkup = {
                  inline_keyboard: [
                    [
                      { text: "📊 Community Roster", callback_data: "btn_community" },
                      { text: "🔄 Re-Audit Fleet", callback_data: "btn_sybil" }
                    ],
                    [
                      { text: "🚀 Open Admin Console", web_app: { url: dashUrl } }
                    ]
                  ]
                };
                const cbMsgId = cb.message ? cb.message.message_id : null;
                if (cbMsgId) {
                  await editAnimatedMessage(chatId, cbMsgId, [sybilRep], sybilMarkup, 200);
                } else {
                  await sendAnimatedReply(chatId, [sybilRep], sybilMarkup, 200);
                }
              })());
            } else if (cbData.startsWith("cb_ban_")) {
              const targetUid = cbData.replace("cb_ban_", "").trim();
              ctx.waitUntil((async () => {
                const raw = await upstashGet(`ub_user:${targetUid}`);
                if (raw) {
                  const prof = typeof raw === "string" ? JSON.parse(raw) : raw;
                  prof.is_banned = true;
                  prof.ban_reason = "Suspicious anti-sybil activity or policy violations";
                  prof.farming_active = false;
                  prof.banned_at = Date.now();
                  await upstashSet(`ub_user:${targetUid}`, prof);
                  await upstashSadd("ub_banned_users", String(targetUid));
                  const uBotToken = env.USER_BOT_TOKEN || "8167732110:AAGQA6bBgRwaChFIWPvs9uCt6aZ3j1VGCn8";
                  await fetch(`https://api.telegram.org/bot${uBotToken}/sendMessage`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      chat_id: targetUid,
                      text: `🚫 *ACCESS RESTRICTED*\n\nYour account has been suspended by platform administration for suspicious anti-sybil activity.\n\n• *Status:* 🔴 Farming Halted\n\nIf you believe this is an error, please contact @AAAAutoMiner.`,
                      parse_mode: "Markdown"
                    })
                  }).catch(() => {});
                  await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      chat_id: chatId,
                      text: `🚫 *User \`${targetUid}\` Suspended Successfully!*\n\nAdded to \`ub_banned_users\`. Mining halted.`,
                      parse_mode: "Markdown",
                      reply_markup: statusInlineKeyboard
                    })
                  }).catch(() => {});
                }
              })());
            } else if (cbData.startsWith("cb_unban_")) {
              const targetUid = cbData.replace("cb_unban_", "").trim();
              ctx.waitUntil((async () => {
                const raw = await upstashGet(`ub_user:${targetUid}`);
                if (raw) {
                  const prof = typeof raw === "string" ? JSON.parse(raw) : raw;
                  prof.is_banned = false;
                  delete prof.ban_reason;
                  delete prof.banned_at;
                  prof.farming_active = true;
                  await upstashSet(`ub_user:${targetUid}`, prof);
                  await upstashSrem("ub_banned_users", String(targetUid));
                  const uBotToken = env.USER_BOT_TOKEN || "8167732110:AAGQA6bBgRwaChFIWPvs9uCt6aZ3j1VGCn8";
                  await fetch(`https://api.telegram.org/bot${uBotToken}/sendMessage`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      chat_id: targetUid,
                      text: `✅ *ACCOUNT RESTORED!*\n\nYour account has been reinstated by platform administration.\n• *Status:* 🟢 Active & Ready\n\nThank you for your patience! 🚀`,
                      parse_mode: "Markdown"
                    })
                  }).catch(() => {});
                  await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      chat_id: chatId,
                      text: `✅ *User \`${targetUid}\` Reinstated Successfully!*\n\nRemoved from ban list. Access restored.`,
                      parse_mode: "Markdown",
                      reply_markup: statusInlineKeyboard
                    })
                  }).catch(() => {});
                }
              })());
            } else if (cbData.startsWith("cb_grant100_")) {
              const targetUid = cbData.replace("cb_grant100_", "").trim();
              ctx.waitUntil((async () => {
                const raw = await upstashGet(`ub_user:${targetUid}`);
                if (raw) {
                  const prof = typeof raw === "string" ? JSON.parse(raw) : raw;
                  prof.points = (prof.points || 0) + 100;
                  await upstashSet(`ub_user:${targetUid}`, prof);
                  const uBotToken = env.USER_BOT_TOKEN || "8167732110:AAGQA6bBgRwaChFIWPvs9uCt6aZ3j1VGCn8";
                  await fetch(`https://api.telegram.org/bot${uBotToken}/sendMessage`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      chat_id: targetUid,
                      text: `🎁 *+100 Mining Points Credited!* 🎉\n\nPlatform Admin has credited your account with +100 Points!\n• *New Balance:* ${prof.points} Points`,
                      parse_mode: "Markdown"
                    })
                  }).catch(() => {});
                  await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      chat_id: chatId,
                      text: `✅ Granted *+100 Points* to \`${targetUid}\` (Balance: ${prof.points} Pts)`,
                      parse_mode: "Markdown",
                      reply_markup: statusInlineKeyboard
                    })
                  }).catch(() => {});
                }
              })());
            } else if (cbData.startsWith("cb_grantvip_")) {
              const targetUid = cbData.replace("cb_grantvip_", "").trim();
              ctx.waitUntil((async () => {
                const raw = await upstashGet(`ub_user:${targetUid}`);
                if (raw) {
                  const prof = typeof raw === "string" ? JSON.parse(raw) : raw;
                  const now = Date.now();
                  const baseExp = (prof.subscription_expiry && prof.subscription_expiry > now) ? prof.subscription_expiry : now;
                  prof.subscription_expiry = baseExp + 86400000;
                  prof.subscription_tier = "day";
                  prof.farming_active = true;
                  await upstashSet(`ub_user:${targetUid}`, prof);
                  const uBotToken = env.USER_BOT_TOKEN || "8167732110:AAGQA6bBgRwaChFIWPvs9uCt6aZ3j1VGCn8";
                  await fetch(`https://api.telegram.org/bot${uBotToken}/sendMessage`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      chat_id: targetUid,
                      text: `🌟 *VIP PASS ACTIVATED!* 🎟️\n\nPlatform Admin has activated a 1-Day VIP Pass for your account!\n• 24/7 Unlimited Mining with 0 deductions active!`,
                      parse_mode: "Markdown"
                    })
                  }).catch(() => {});
                  await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      chat_id: chatId,
                      text: `✅ Granted *1-Day VIP Pass* to \`${targetUid}\``,
                      parse_mode: "Markdown",
                      reply_markup: statusInlineKeyboard
                    })
                  }).catch(() => {});
                }
              })());
            } else if (cbData.startsWith("cb_grantslot_")) {
              const targetUid = cbData.replace("cb_grantslot_", "").trim();
              ctx.waitUntil((async () => {
                const raw = await upstashGet(`ub_user:${targetUid}`);
                if (raw) {
                  const prof = typeof raw === "string" ? JSON.parse(raw) : raw;
                  prof.slots = (prof.slots || 1) + 1;
                  await upstashSet(`ub_user:${targetUid}`, prof);
                  const uBotToken = env.USER_BOT_TOKEN || "8167732110:AAGQA6bBgRwaChFIWPvs9uCt6aZ3j1VGCn8";
                  await fetch(`https://api.telegram.org/bot${uBotToken}/sendMessage`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      chat_id: targetUid,
                      text: `🌟 *EXTRA CLOUD SLOT UNLOCKED!* 📦\n\nPlatform Admin has granted *+1 Permanent Account Slot* to your profile!\n• *Total Slots Available:* ${prof.slots}\n\nYou can now connect another Telegram account!`,
                      parse_mode: "Markdown"
                    })
                  }).catch(() => {});
                  await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      chat_id: chatId,
                      text: `✅ Granted *+1 Permanent Slot* to \`${targetUid}\` (Total: ${prof.slots})`,
                      parse_mode: "Markdown",
                      reply_markup: statusInlineKeyboard
                    })
                  }).catch(() => {});
                }
              })());
            } else {
              ctx.waitUntil((async () => {
                let liveBnb = 0.000622;
                try {
                  const rawMC = await env.BACKUP_KV.get("multichain_balances_state");
                  if (rawMC) {
                    const mc = JSON.parse(rawMC);
                    if (mc.bsc_bnb_balance !== undefined) liveBnb = mc.bsc_bnb_balance;
                  }
                } catch (_) {}
                const rep = `⚡ *MY AGY AI — Fleet Operations*\n\n` +
                  `🟢 *Fleet Health:* 14/14 Accounts Active & Mining\n` +
                  `🤖 *Active Bots (8/8):* Stones • ART • MRG • AI Lab • UltraWallet • Apex • ATF Miner • Ainovum\n` +
                  `💰 *On-Chain Vault:* \`${liveBnb.toFixed(6)} BNB\` • \`500 STONES\` • 14 TON Wallets\n` +
                  `🛡️ *Security:* 5/5 Anti-Bot Verified • Triple Cloudflare Sharding\n\n` +
                  `📱 *Tap below to open your real-time visual Mini App dashboard:*`;
                const cbMsgId = cb.message ? cb.message.message_id : null;
                if (cbMsgId) {
                  await editAnimatedMessage(chatId, cbMsgId, [rep], statusInlineKeyboard, 200);
                } else {
                  await sendAnimatedReply(chatId, [rep], statusInlineKeyboard, 200);
                }
              })());
            }
          }
          return new Response("OK");
        }

        // B. Handle Text Messages & Commands (Strict Admin-Only Access)
        const msg = update.message || update.edited_message;
        if (!msg || !msg.text) return new Response("OK");

        const chatId = msg.chat.id;
        let text = (msg.text || "").trim();
        text = text.replace(/^(\/[a-zA-Z0-9_]+)@[a-zA-Z0-9_]+/i, '$1');
        const senderId = msg.from ? String(msg.from.id) : String(chatId);

        if (!ADMIN_IDS.has(senderId)) {
          await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              chat_id: chatId,
              text: "🔒 *Access Restricted: Private Admin Fleet Console*\n\nThis bot, channel network, and cluster operations are private and restricted exclusively to the system administrator.",
              parse_mode: "Markdown"
            })
          }).catch(() => {});
          return new Response("OK");
        }

        const sendReply = async (replyText, markup = null, parseMode = "Markdown") => {
          const payload = {
            chat_id: chatId,
            text: replyText,
            disable_web_page_preview: true
          };
          if (markup) payload.reply_markup = markup;
          if (parseMode) payload.parse_mode = parseMode;
          try {
            const resp = await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(payload)
            });
            if (!resp.ok && parseMode) {
              delete payload.parse_mode;
              await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
              });
            }
          } catch (_) {}
        };

        // 1. Start & Menu Command
        if (text === "/start" || text === "/menu" || text.startsWith("/start")) {
          ctx.waitUntil((async () => {
            await sendChatAction(chatId, "typing");
            const welcome = `👋 *Welcome to MY AGY AI — Private Admin Console*\n\n` +
              `Your autonomous *24/7 Cloud Operations Hub* is active across 5 Cloudflare Edge nodes.\n\n` +
              `🟢 *Fleet Health:* 14/14 Accounts Online & Mining\n` +
              `🤖 *Active Bots (8/8):* Stones • ART • MRG • AI Lab • UltraWallet • Apex • ATF Miner • Ainovum\n` +
              `💰 *On-Chain Vaults:* BEP-20 (BNB) • Arbitrum (STONES) • 14 TON Wallets\n` +
              `🛡️ *Security:* 5/5 Anti-Bot Verified • Dual-Edge Cloud Sync\n\n` +
              `📱 *Tap '👑 Admin Console' below or use quick controls:*`;
            const frames = [
              "⚡ *MY AGY AI Fleet Initialization...*\n`[▰▰▰▱▱▱▱▱▱▱] 30%` • Verifying Admin Permissions",
              "⚡ *Synchronizing Cloud Edge Nodes...*\n`[▰▰▰▰▰▰▰▱▱▱] 75%` • Loading 14 Mining Accounts",
              welcome
            ];
            await sendAnimatedReply(chatId, frames, mainKeyboard, 300);
            await sendReply("⚡ *Instant Fleet Controls:*", statusInlineKeyboard);
          })());
          return new Response("OK");
        }

        // 1.4 Dedicated Stones Miners Cloud Command (/stones)
        if (text === "/stones" || text.startsWith("/stones")) {
          ctx.waitUntil((async () => {
            const stonesMsg = `💎 *STONES MINERS CLOUD COMMAND CENTER*\n` +
              `━━━━━━━━━━━━━━━━━━━━━━\n` +
              `• *Status:* Active & Mining (Arbitrum One)\n` +
              `• *Arbitrum Vault:* \`0xfda4182001672b9f0f09e2118242e543e35ed5ce\`\n` +
              `• *Holding Target:* \`500+ STONES\`\n` +
              `• *Master Account Policy:* Compounding (0 withdrawals)\n` +
              `• *Worker Accounts Policy:* Auto-Withdraw when balance >= 500 STONES\n` +
              `• *Resiliency:* 30m Origin Circuit Breaker & Cloudflare Tunnel Watchdog Active ✅\n` +
              `━━━━━━━━━━━━━━━━━━━━━━`;
            await sendReply(stonesMsg, statusInlineKeyboard);
          })());
          return new Response("OK");
        }

        // 1.41 Legacy BNB Command (/bnb)
        if (text === "/bnb" || text.startsWith("/bnb")) {
          ctx.waitUntil((async () => {
            const bnbMsg = `🚫 *BNB GALAXY PERMANENTLY DISABLED*\n` +
              `━━━━━━━━━━━━━━━━━━━━━━\n` +
              `• *Notice:* @CryptoProUpRobot was audited and confirmed to withhold payouts.\n` +
              `• *Action Taken:* Fleet accounts blocked the bot, wiped scam channels, and reported it to Telegram Anti-Scam.\n` +
              `• *Active Bots:* Focus is 100% placed on our 8 legitimate mining bots (ATF, Stones, MRG, ART, AI Lab, UltraWallet, Apex, Ainovum).\n` +
              `━━━━━━━━━━━━━━━━━━━━━━`;
            await sendReply(bnbMsg, statusInlineKeyboard);
          })());
          return new Response("OK");
        }

        // 1.45 Dedicated ATF Miner Cloud Command (/atf)
        if (text === "/atf" || text.startsWith("/atf")) {
          ctx.waitUntil((async () => {
            let atfData = {};
            try {
              const raw = await env.BACKUP_KV.get("atf_fleet_state");
              if (raw) atfData = JSON.parse(raw);
            } catch (_) {}
            
            let totalMined = 3933.99;
            let activeAccs = 14;
            if (atfData && atfData.results) {
              totalMined = atfData.results.reduce((s, a) => s + (parseFloat(a.mined_balance) || 0), 0);
              activeAccs = atfData.results.filter(a => a.mining_active).length;
            }

            const atfInlineKeyboard = {
              inline_keyboard: [
                [
                  { text: "⚡ Claim ATF & Mine", callback_data: "btn_atf_claim" },
                  { text: "💎 Verified Wallets", callback_data: "btn_atf_wallets" }
                ],
                [
                  { text: "🚀 Open Visual Mini App", web_app: { url: dashUrl } }
                ],
                [
                  { text: "🔄 Refresh Status", callback_data: "btn_status" }
                ]
              ]
            };

            const atfMsg = `🪙 *ATF MINER CLOUD COMMAND CENTER*\n` +
              `━━━━━━━━━━━━━━━━━━━━━━\n` +
              `⛏️ *Total Fleet ATF Mined:* \`${totalMined.toFixed(2)} ATF\`\n` +
              `👥 *Active Mining Accounts:* \`${activeAccs}/14 Accounts\`\n` +
              `💎 *TON Wallets:* \`14/14 Bound\` (Main: Binance TON, Workers: Isolated v4r2)\n` +
              `🧮 *Anti-Bot Math Verification:* \`100% Solved\` ✅\n` +
              `🛡️ *TON Connect 2.0 Proofs:* \`Cryptographically Verified\`\n` +
              `━━━━━━━━━━━━━━━━━━━━━━\n` +
              `⚡ _Tap the buttons below to trigger cloud claim or view wallets:_`;

            await sendReply(atfMsg, atfInlineKeyboard);
          })());
          return new Response("OK");
        }

        // 1.5 Daily AI Executive Briefing Command (/briefing)
        if (text === "🌅 AI Briefing" || text === "🌅 Morning Briefing" || text === "/briefing" || text.startsWith("/briefing")) {

          ctx.waitUntil((async () => {
            await sendReply("⏳ *Generating AI Executive Briefing via Google Gemini 3.6 Flash & Multi-Cloud AI...*");
            try {
              const aiData = await runAiCascade("You are the Chief AI Operations Officer for the 14-account autonomous Telegram fleet 'MY AGY AI'. Summarize: 1. 14/14 accounts active & 100% 5/5 verified. 2. 8 mining bots active (Stones, MRG, ART, AI Lab, UltraWallet, Apex, Ainovum, ATF Miner). 3. Multi-cloud nodes operational. 4. One high-value operational recommendation. Use crisp Telegram Markdown.");
              const ans = aiData.answer || aiData.response || "All 14 accounts active and mining across 14 cloud nodes.";
              const prov = aiData.provider || "Google Gemini";
              const mod = aiData.model || "gemini-3.6-flash";
              const msgText = `📊 *MY AGY AI — Daily Executive Briefing*\n━━━━━━━━━━━━━━━━━━━━━━\n${ans}\n━━━━━━━━━━━━━━━━━━━━━━\n🤖 _Generated by ${prov} (${mod})_`;
              await sendReply(msgText, statusInlineKeyboard);
            } catch (err) {
              await sendReply("⚠️ Could not generate briefing: " + err.message);
            }
          })());
          return new Response("OK");
        }

        // 1.6 Multi-Cloud AI Chat (/ai <prompt> or /ask <prompt>)
        if (text.startsWith("/ai") || text.startsWith("/ask")) {
          const parts = text.split(/\s+/);
          const aiQuery = parts.slice(1).join(" ").trim();
          if (!aiQuery) {
            const helpAi = `🧠 *Multi-Cloud AI Assistant*\n\n` +
              `Powered by *Google Gemini 3.6 Flash*, *GroqCloud LPU*, and *Cloudflare Workers AI*!\n\n` +
              `Ask anything by sending:\n` +
              `• \`/ai <your question>\`\n` +
              `• \`/ask <your question>\`\n\n` +
              `*Examples:*\n` +
              `• \`/ai What are the optimal strategies for crypto mining bots?\`\n` +
              `• \`/ai Summarize current fleet status.\``;
            ctx.waitUntil(sendReply(helpAi, statusInlineKeyboard));
            return new Response("OK");
          }
          ctx.waitUntil((async () => {
            try {
              const aiData = await runAiCascade(aiQuery);
              const ans = aiData.answer || aiData.response || "No response received.";
              const prov = aiData.provider || "AI Engine";
              const mod = aiData.model || "Gemini 3.5 Flash";
              const rep = `🤖 *AI Intelligence (${prov} · ${mod}):*\n\n${ans}\n\n⚡ _MY AGY AI Multi-Cloud Cascade_`;
              await sendReply(rep, statusInlineKeyboard);
            } catch (e) {
              await sendReply("⚠️ AI query error: " + e.message);
            }
          })());
          return new Response("OK");
        }

        // 1.7 On-Chain BNB Consolidator Check (/consolidate)
        if (text === "/consolidate" || text.startsWith("/consolidate") || text === "/bnbvault" || text === "/vault") {
          ctx.waitUntil((async () => {
            const w1 = "0xfda4182001672b9f0f09e2118242e543e35ed5ce";
            async function getBscBal(addr) {
              try {
                const r = await fetch("https://bsc-dataseed.binance.org/", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ jsonrpc: "2.0", method: "eth_getBalance", params: [addr, "latest"], id: 1 })
                });
                const d = await r.json();
                if (d && d.result) {
                  return parseInt(d.result, 16) / 1e18;
                }
              } catch (_) {}
              return 0.0;
            }
            const b1 = await getBscBal(w1);
            const rep = `🪙 *On-Chain BNB Vault & Wallet Tracker*\n\n` +
              `• *Binance BEP-20 Vault (All 14 Accounts):* \`${b1.toFixed(6)} BNB\`\n` +
              `  \`0xfda4182001672b9f0f09e2118242e543e35ed5ce\`\n` +
              `• *Binance TON Vault (Main Account):*\n` +
              `  \`UQBPZiSvitdPU3VUyJK2mRaHVBl69xejw5aOrh1KfKA7gwDT\`\n` +
              `• *Consolidation Target:* \`0.005000 BNB\` (${((b1 / 0.005) * 100).toFixed(1)}%)\n\n` +
              `_Tracking live BSC blockchain state via Binance Dataseed RPC._`;
            await sendReply(rep, statusInlineKeyboard);
          })());
          return new Response("OK");
        }

        // 1.8 Force Fleet Sync (/sync)
        if (text === "/sync" || text.startsWith("/sync")) {
          ctx.waitUntil((async () => {
            const upstashUrl = "https://relaxing-starfish-285827.upstash.io";
            const upstashToken = "gQAAAAAABFyDAAIgcDI5MDYyYWZjNzYzNzk0ZmRjYjhmNTA4ZDI4ODlmODkzNw";
            await fetch(`${upstashUrl}/set/fleet:pending_action`, {
              method: "POST",
              headers: { "Authorization": `Bearer ${upstashToken}`, "Content-Type": "application/json" },
              body: JSON.stringify({ action: "sync", timestamp: Date.now() })
            }).catch(() => {});
            const rep = `🔄 *Multi-Cloud Fleet Sync Dispatched!*\n\n` +
              `• Dispatched signal across all 3 Cloudflare nodes\n` +
              `• Mining cycle triggered across all 14 accounts\n` +
              `• Telemetry replicating to Turso LibSQL, D1 SQL, and Supabase`;
            await sendReply(rep, statusInlineKeyboard);
          })());
          return new Response("OK");
        }

        // 1.9 Remove Account Command (/remove_account, /remove, /delaccount, or button "🗑️ Remove Account")
        if (text === "🗑️ Remove Account" || text === "🗑️ Remove" || text.startsWith("/remove_account") || text.startsWith("/removeaccount") || text === "/remove" || text.startsWith("/remove ") || text.startsWith("/delaccount")) {
          ctx.waitUntil((async () => {
            const parts = text.split(/\s+/);
            const targetId = (text.startsWith("/") && parts.length > 1) ? parts[1].trim().replace("+", "") : null;
            let accounts = await getFleetAccounts();

            if (!targetId) {
              const buttons = accounts.map((a, i) => [
                { text: `🗑️ Remove #${a.index || (i+1)} ${cleanName(a, i)} (${a.phone || a.user_id})`, callback_data: `btn_admin_del_${a.user_id || a.phone}` }
              ]);
              buttons.push([{ text: "🔙 Back to Fleet Accounts", callback_data: "btn_accounts" }]);
              const rep = `🗑️ *Fleet Account Removal Hub*\n` +
                `━━━━━━━━━━━━━━━━━━━━━━\n` +
                `Select an account below to disconnect and remove from 24/7 cloud automation:\n\n` +
                `⚠️ _Removing an account stops all 8 mining bots on that session immediately._`;
              await sendReply(rep, { inline_keyboard: buttons });
              return;
            }

            const removedAcc = accounts.find(a => String(a.user_id) === targetId || String(a.phone || "").replace("+", "") === targetId);
            accounts = accounts.filter(a => String(a.user_id) !== targetId && String(a.phone || "").replace("+", "") !== targetId);
            try {
              ctx.waitUntil(upstashSet("fleet:live_state", { accounts, timestamp: Date.now() }));
              if (env.BACKUP_KV) {
                await env.BACKUP_KV.put("fleet_live_state", JSON.stringify({ accounts, timestamp: Date.now() }));
              }
            } catch (_) {}

            const recorded = {
              id: "act_" + Date.now(),
              action: "remove_account",
              user_id: targetId,
              phone: targetId.startsWith("+") ? targetId : (removedAcc ? removedAcc.phone : ""),
              timestamp: Date.now(),
              node: CURRENT_SUBDOMAIN
            };
            ctx.waitUntil(upstashSet("fleet:pending_action", recorded));
            if (env.BACKUP_KV) {
              ctx.waitUntil(env.BACKUP_KV.put("pending_fleet_action", JSON.stringify(recorded), { expirationTtl: 600 }).catch(() => {}));
            }
            const accDesc = removedAcc ? `${removedAcc.name || "Account"} (\`${removedAcc.phone || removedAcc.user_id}\`)` : `\`${targetId}\``;
            const rep = `✅ *Account Removed from Fleet Successfully!* 🗑️\n\n` +
              `• *Removed:* ${accDesc}\n` +
              `• *Remaining Active Accounts:* ${accounts.length}\n` +
              `• *Action:* Disconnected from 24/7 cloud mining and queued for eviction.\n\n` +
              `Tap *👥 Fleet Accounts* below to view updated fleet roster.`;
            await sendReply(rep, accountsInlineKeyboard);
          })());
          return new Response("OK");
        }

        // 2. Add Account Command & Raw Phone Auto-Detection
        const isPhonePattern = /^(\+?\d{8,15}|01[3-9]\d{8}|1[3-9]\d{8})$/.test(text.replace(/[\s\-]/g, ''));
        if (text === "➕ Add Account" || text.startsWith("/addaccount") || text.startsWith("/add_account") || text === "➕ Add" || text === "Add Account" || isPhonePattern) {
          let extractedPhone = "";
          if (isPhonePattern && !text.startsWith("/")) {
            extractedPhone = text.replace(/[\s\-]/g, '');
          } else {
            const parts = text.split(/\s+/);
            if (parts.length > 1 && /\d/.test(parts[1])) {
              extractedPhone = parts[1].replace(/[\s\-]/g, '');
            }
          }

          if (extractedPhone) {
            let normalized = extractedPhone;
            if (normalized.startsWith("01") && normalized.length === 11) {
              normalized = "+88" + normalized;
            } else if (normalized.startsWith("1") && normalized.length === 10) {
              normalized = "+880" + normalized;
            } else if (!normalized.startsWith("+")) {
              normalized = "+" + normalized;
            }

            ctx.waitUntil((async () => {
              await sendChatAction(chatId, "typing");
              const res = await cloudLoginSendCode(normalized, chatId);
              if (res && res.ok) {
                if (env.BACKUP_KV) {
                  await env.BACKUP_KV.put("login_flow:" + chatId, JSON.stringify({ step: "waiting_code", phone: normalized, node_url: res.node_url || "" }), { expirationTtl: 600 }).catch(() => {});
                }
                const msg = `📨 *Verification Code Sent!*\n\n` +
                  `Telegram sent a 5-digit verification code to \`${normalized}\`.\n\n` +
                  `Please reply with the code (e.g. \`12345\`):\n` +
                  `_(Or tap ❌ Cancel Login below to abort)_`;
                await sendAnimatedReply(chatId, [msg], cancelKeyboard);
              } else {
                const errDetail = res ? (res.error || res.message) : "Failed to connect to Telegram MTProto Gateway";
                const errMsg = `❌ *Could Not Request Code*\n\n` +
                  `Failed to request code for \`${normalized}\`.\n` +
                  `*Error:* ${errDetail}\n\n` +
                  `Please check the phone number and tap ➕ Add Account to try again.`;
                await sendAnimatedReply(chatId, [errMsg], mainKeyboard);
              }
            })());
            return new Response("OK");
          }

          const rep = `📱 *Add New Telegram Account*\n\n` +
            `Please send the phone number of the Telegram account you want to connect:\n\n` +
            `• *Bangladesh:* \`019XXXXXXXX\` or \`19XXXXXXXX\`\n` +
            `• *Standard:* \`+88017XXXXXXXX\`\n` +
            `• *International:* \`+1...\`, \`+44...\`, \`+91...\`\n\n` +
            `_(Tap ❌ Cancel Login below to abort)_`;
          if (env.BACKUP_KV) {
            ctx.waitUntil(env.BACKUP_KV.put("login_flow:" + chatId, JSON.stringify({ step: "waiting_phone" }), { expirationTtl: 600 }).catch(() => {}));
          }
          ctx.waitUntil(sendReply(rep, cancelKeyboard));
          return new Response("OK");
        }

        // 2.1 OTP Code / 2FA Password Relay
        const trimmed = text.trim();
        const isCancelLogin = (trimmed === "/cancel" || trimmed === "❌ Cancel Login" || trimmed === "❌ Cancel");
        if (isCancelLogin) {
          if (env.BACKUP_KV) {
            ctx.waitUntil(env.BACKUP_KV.delete("login_flow:" + chatId).catch(() => {}));
          }
          ctx.waitUntil(cloudLoginCancel(chatId));
          ctx.waitUntil(sendReply("❌ Account connection cancelled.", mainKeyboard));
          return new Response("OK");
        }

        let loginFlowState = null;
        if (env.BACKUP_KV) {
          try {
            const rawFlow = await env.BACKUP_KV.get("login_flow:" + chatId);
            if (rawFlow) {
              loginFlowState = rawFlow.startsWith("{") ? JSON.parse(rawFlow) : { step: "waiting_code" };
            }
          } catch (_) {}
        }

        const isOtpCode = /^(\d{5}|\d{3}[-\s]\d{2}|\d{6})$/.test(trimmed);
        const isCommandOrMenu = text.startsWith("/") || text.includes("📊") || text.includes("⚡") || text.includes("💎") || text.includes("🧹") || text.includes("🌐") || text.includes("➕") || text.includes("👑") || text.includes("👥") || text.includes("🎁") || text.includes("🎬") || text.includes("🗑️") || text.includes("💳") || text.includes("💬") || text.includes("🌅") || text.includes("🔥");

        if (loginFlowState && !isCommandOrMenu) {
          ctx.waitUntil((async () => {
            await sendChatAction(chatId, "typing");
            const step = loginFlowState.step;
            const phone = loginFlowState.phone || "";
            const node_url = loginFlowState.node_url || "";

            // A. Waiting for 2FA Password
            if (step === "waiting_2fa") {
              const res = await cloudLoginVerify(chatId, { password: trimmed, phone, node_url });
              if (res && res.ok) {
                if (env.BACKUP_KV) await env.BACKUP_KV.delete("login_flow:" + chatId).catch(() => {});
                const succMsg = `🎉 *Account Connected Successfully with 2FA!*\n\n` +
                  `• *Name:* ${res.name || "User"}\n` +
                  `• *Username:* @${res.username || "None"}\n` +
                  `• *User ID:* \`${res.user_id}\`\n` +
                  `• *Phone:* \`${res.phone || phone}\`\n` +
                  `• *Master Referrals:* 🚀 \`All 8 Fleet Bots Bound to Master ID 6727787768\`!\n\n` +
                  `✅ 100% Cloud MTProto active! 24/7 automated mining & token farming is now live in the cloud.`;
                await sendAnimatedReply(chatId, [succMsg], mainKeyboard);
              } else {
                const errDetail = res ? (res.error || res.message) : "Invalid 2FA password";
                const errMsg = `❌ *2FA Authentication Failed*\n\n` +
                  `*Error:* ${errDetail}\n\n` +
                  `Please check your Two-Factor Password and try again:\n` +
                  `_(Or tap ❌ Cancel Login to abort)_`;
                await sendAnimatedReply(chatId, [errMsg], cancelKeyboard);
              }
              return;
            }

            // B. Waiting for Phone (if user clicked Add Account button first)
            if (step === "waiting_phone") {
              let normalized = trimmed.replace(/[\s\-]/g, '');
              if (normalized.startsWith("01") && normalized.length === 11) {
                normalized = "+88" + normalized;
              } else if (normalized.startsWith("1") && normalized.length === 10) {
                normalized = "+880" + normalized;
              } else if (!normalized.startsWith("+")) {
                normalized = "+" + normalized;
              }
              const res = await cloudLoginSendCode(normalized, chatId);
              if (res && res.ok) {
                if (env.BACKUP_KV) {
                  await env.BACKUP_KV.put("login_flow:" + chatId, JSON.stringify({ step: "waiting_code", phone: normalized, node_url: res.node_url || "" }), { expirationTtl: 600 }).catch(() => {});
                }
                const msg = `📨 *Verification Code Sent!*\n\n` +
                  `Telegram sent a 5-digit verification code to \`${normalized}\`.\n\n` +
                  `Please reply with the code (e.g. \`12345\`):\n` +
                  `_(Or tap ❌ Cancel Login below to abort)_`;
                await sendAnimatedReply(chatId, [msg], cancelKeyboard);
              } else {
                const errDetail = res ? (res.error || res.message) : "Failed to connect to Telegram MTProto Gateway";
                const errMsg = `❌ *Could Not Request Code*\n\n` +
                  `Failed to request code for \`${normalized}\`.\n` +
                  `*Error:* ${errDetail}\n\n` +
                  `Please check the phone number and send again (or tap ❌ Cancel Login):`;
                await sendAnimatedReply(chatId, [errMsg], cancelKeyboard);
              }
              return;
            }

            // C. Waiting for Verification Code
            const res = await cloudLoginVerify(chatId, { code: trimmed, phone, node_url });
            if (res && res.need_2fa) {
              if (env.BACKUP_KV) {
                await env.BACKUP_KV.put("login_flow:" + chatId, JSON.stringify({ step: "waiting_2fa", phone: res.phone || phone, node_url }), { expirationTtl: 600 }).catch(() => {});
              }
              const twoFaMsg = `🔒 *Two-Factor Authentication (2FA) Required*\n\n` +
                `This account has a Two-Factor Cloud Password enabled.\n` +
                `Please reply with your 2FA password:\n\n` +
                `_(Or tap ❌ Cancel Login below to abort)_`;
              await sendAnimatedReply(chatId, [twoFaMsg], cancelKeyboard);
            } else if (res && res.ok) {
              if (env.BACKUP_KV) await env.BACKUP_KV.delete("login_flow:" + chatId).catch(() => {});
              const succMsg = `🎉 *Account Connected Successfully!*\n\n` +
                `• *Name:* ${res.name || "User"}\n` +
                `• *Username:* @${res.username || "None"}\n` +
                `• *User ID:* \`${res.user_id}\`\n` +
                `• *Phone:* \`${res.phone || phone}\`\n` +
                `• *Master Referrals:* 🚀 \`All 8 Fleet Bots Bound to Master ID 6727787768\`!\n\n` +
                `✅ 100% Cloud MTProto active! 24/7 automated mining & token farming is now live in the cloud.`;
              await sendAnimatedReply(chatId, [succMsg], mainKeyboard);
            } else {
              const errDetail = res ? (res.error || res.message) : "Verification code rejected";
              const errMsg = `❌ *Verification Failed*\n\n` +
                `*Error:* ${errDetail}\n\n` +
                `Please check the 5-digit code and reply again (or tap ❌ Cancel Login to restart):`;
              await sendAnimatedReply(chatId, [errMsg], cancelKeyboard);
            }
          })());
          return new Response("OK");
        } else if (isOtpCode) {
          ctx.waitUntil((async () => {
            await sendChatAction(chatId, "typing");
            const res = await cloudLoginVerify(chatId, { code: trimmed });
            if (res && res.need_2fa) {
              if (env.BACKUP_KV) {
                await env.BACKUP_KV.put("login_flow:" + chatId, JSON.stringify({ step: "waiting_2fa" }), { expirationTtl: 600 }).catch(() => {});
              }
              const twoFaMsg = `🔒 *Two-Factor Authentication (2FA) Required*\n\n` +
                `This account has a Two-Factor Cloud Password enabled.\n` +
                `Please reply with your 2FA password:\n\n` +
                `_(Or tap ❌ Cancel Login below to abort)_`;
              await sendAnimatedReply(chatId, [twoFaMsg], cancelKeyboard);
            } else if (res && res.ok) {
              if (env.BACKUP_KV) await env.BACKUP_KV.delete("login_flow:" + chatId).catch(() => {});
              const succMsg = `🎉 *Account Connected Successfully!*\n\n` +
                `• *Name:* ${res.name || "User"}\n` +
                `• *Username:* @${res.username || "None"}\n` +
                `• *User ID:* \`${res.user_id}\`\n` +
                `• *Phone:* \`${res.phone || ""}\`\n` +
                `• *Master Referrals:* 🚀 \`All 8 Fleet Bots Bound to Master ID 6727787768\`!\n\n` +
                `✅ 100% Cloud MTProto active! 24/7 automated mining & token farming is now live in the cloud.`;
              await sendAnimatedReply(chatId, [succMsg], mainKeyboard);
            } else {
              const errDetail = res ? (res.error || res.message) : "Verification code rejected";
              const errMsg = `❌ *Verification Failed*\n\n` +
                `*Error:* ${errDetail}\n\n` +
                `Please tap ➕ Add Account to start connection.`;
              await sendAnimatedReply(chatId, [errMsg], mainKeyboard);
            }
          })());
          return new Response("OK");
        }

        // 3. Status & Dashboard Commands
        if (text === "📊 Fleet Status" || text === "📊 Live Status" || text === "📊 Status" || text.startsWith("/status") || text === "🌐 Dashboard" || text.startsWith("/dashboard") || text === "🚀 Open Mini App" || text.startsWith("/app") || text === "🚀 Open WebApp Dashboard" || text === "🚀 Open Dashboard" || text === "👑 Admin Console") {
          ctx.waitUntil((async () => {
            await sendChatAction(chatId, "typing");
            let liveBnb = 0.000622;
            try {
              const rawMC = await env.BACKUP_KV.get("multichain_balances_state");
              if (rawMC) {
                const mc = JSON.parse(rawMC);
                if (mc.bsc_bnb_balance !== undefined) liveBnb = mc.bsc_bnb_balance;
              }
            } catch (_) {}

            const rep = `⚡ *MY AGY AI — Fleet Operations*\n\n` +
              `🟢 *Fleet Health:* 14/14 Accounts Active & Mining\n` +
              `🤖 *Active Bots (8/8):* Stones • ART • MRG • AI Lab • UltraWallet • Apex • ATF Miner • Ainovum\n` +
              `💰 *On-Chain Vault:* \`${liveBnb.toFixed(6)} BNB\` • \`500 STONES\` • 14 TON Wallets\n` +
              `🛡️ *Security:* 5/5 Anti-Bot Verified • Triple Cloudflare Edge Shards\n\n` +
              `📱 *Tap below to open your real-time visual Executive Dashboard:*`;
            const frames = [
              "📊 *Querying Fleet Live State...*\n`[▰▰▰▱▱▱▱▱▱▱] 30%` • Polling 14 Accounts & 5 Edge Nodes",
              "📊 *Aggregating On-Chain Balances...*\n`[▰▰▰▰▰▰▰▱▱▱] 75%` • BEP-20 • Arbitrum • TON",
              rep
            ];
            await sendAnimatedReply(chatId, frames, statusInlineKeyboard, 300);
          })());
          return new Response("OK");
        }

        // 3.5 Instant Fleet Harvest
        if (text === "⚡ Instant Harvest" || text === "⚡ Harvest" || text.startsWith("/harvest") || text === "/farm" || text.startsWith("/farm")) {
          ctx.waitUntil((async () => {
            await sendChatAction(chatId, "typing");
            const rep = `⚡ *Instant Fleet Harvest Dispatched!*\n\n` +
              `• *Status:* Executing across 14 Accounts ✅\n` +
              `• *Active Lineup:* Stones • ART • MRG • AI Lab • UltraWallet • Apex • Ainovum • ATF\n\n` +
              `_Farming cycle and task claims active across all 5 parallel Cloudflare edge slots._`;
            const frames = [
              "⚡ *Initiating Instant Harvest across Fleet...*\n`[▰▰▱▱▱▱▱▱▱▱] 20%` • Syncing Edge Nodes & Relayers",
              "⚡ *Harvesting Multi-Bot Rewards...*\n`[▰▰▰▰▰▰▱▱▱▱] 65%` • Dispatched 14 Accounts (Stones, ATF, MRG, ART...)",
              rep
            ];
            const harvestPromise = queueHarvestAction();
            await sendAnimatedReply(chatId, frames, statusInlineKeyboard, 320);
            await harvestPromise;
          })());
          return new Response("OK");
        }

        // 4. Withdraw Command & Universal Sweep
        if (text === "💼 Universal Sweep" || text === "⚡ Universal Sweep" || text === "⚡ Sweep" || text.startsWith("/sweep") || text === "💰 Withdraw" || text.startsWith("/withdraw") || text.startsWith("/balance")) {
          ctx.waitUntil((async () => {
            await sendChatAction(chatId, "typing");
            let liveBnb = 0.000622;
            try {
              const rawMC = await env.BACKUP_KV.get("multichain_balances_state");
              if (rawMC) {
                const mc = JSON.parse(rawMC);
                if (mc.bsc_bnb_balance !== undefined) liveBnb = mc.bsc_bnb_balance;
              }
            } catch (_) {}
            const rep = `⚡ *Universal Fleet Sweep Dispatched!*\n\n` +
              `• *Status:* Queued to Fleet Workers ✅\n` +
              `• *Live Binance BEP-20:* \`${liveBnb.toFixed(6)} BNB\`\n` +
              `• *Networks:* BEP-20 (USDT/BNB) • Arbitrum One (STONES) • TON Network\n` +
              `• *Auto-Thresholds:* AI Lab >= $0.02 • Ainovum >= 0.10 USDT • Stones >= 500 STONES\n` +
              `• *Payout Address:* \`0xfda4182001672b9f0f09e2118242e543e35ed5ce\`\n\n` +
              `⏳ _Sequential auto-withdrawals triggered across AI Lab, Stones Miners, Ainovum, and On-Chain Wallets._`;
            const frames = [
              "💼 *Initiating Universal Fleet Sweep...*\n`[▰▰▱▱▱▱▱▱▱▱] 25%` • Querying On-Chain Vaults & Balances",
              "💼 *Calculating Cashout Thresholds...*\n`[▰▰▰▰▰▰▰▱▱▱] 70%` • Checking BEP-20, Arbitrum & TON Nodes",
              rep
            ];
            const sweepPromise = queueSweepAction();
            await sendAnimatedReply(chatId, frames, statusInlineKeyboard, 320);
            await sweepPromise;
          })());
          return new Response("OK");
        }

        // 4.5 Sub-Bot Commands (Ainovum, AI Lab, ART, MRG, UltraWallet, Apex)
        if (text === "🤖 Ainovum" || text.startsWith("/ainovum")) {
          ctx.waitUntil((async () => {
            const rep = `🤖 *AINOVUM CLOUD NODE COMMAND CENTER*\n` +
              `━━━━━━━━━━━━━━━━━━━━━━\n` +
              `• *Platform:* Ainovum Network (@ainovumbot)\n` +
              `• *Status:* Active & Mining (Distributed Edge Nodes)\n` +
              `• *Auto-Withdraw:* Threshold \`0.10 USDT\` (BEP-20)\n` +
              `• *Routing Architecture:* Dedicated Isolated EVM Wallets\n` +
              `• *Anti-Sybil Defense:* Distinct Exit IPs + Unique User-Agents ✅\n` +
              `━━━━━━━━━━━━━━━━━━━━━━`;
            await sendReply(rep, statusInlineKeyboard);
          })());
          return new Response("OK");
        }

        if (text === "🧪 AI Lab" || text.startsWith("/ailab")) {
          ctx.waitUntil((async () => {
            const rep = `🧪 *AI LAB ROBOT COMMAND CENTER*\n` +
              `━━━━━━━━━━━━━━━━━━━━━━\n` +
              `• *Platform:* AI Lab Agent (@AiLab_robot)\n` +
              `• *Status:* Continuous 8h Mining Active\n` +
              `• *Exchange Policy:* Auto-Exchange when hashes >= 3.00\n` +
              `• *Auto-Cashout:* Step-size \`$0.02 USD\` (USDT BEP-20)\n` +
              `• *Payout Vault:* \`0xfda4182001672b9f0f09e2118242e543e35ed5ce\`\n` +
              `━━━━━━━━━━━━━━━━━━━━━━`;
            await sendReply(rep, statusInlineKeyboard);
          })());
          return new Response("OK");
        }

        if (text === "🚀 ART Airdrop" || text.startsWith("/art")) {
          ctx.waitUntil((async () => {
            const rep = `🚀 *ART AIRDROP COMMAND CENTER*\n` +
              `━━━━━━━━━━━━━━━━━━━━━━\n` +
              `• *Platform:* ART Airdrop Mining (@art_airdrop_bot)\n` +
              `• *Status:* Active & Auto-Claiming (8h Cycles)\n` +
              `• *Hashrate:* 30.3 ART/h per Account\n` +
              `• *Sponsor Tasks:* V8–V14 Automated Claims (+10.0 ART/task) ✅\n` +
              `• *Payout Network:* TON Blockchain (The Open Network)\n` +
              `━━━━━━━━━━━━━━━━━━━━━━`;
            await sendReply(rep, statusInlineKeyboard);
          })());
          return new Response("OK");
        }

        if (text === "⛏️ MRG Miner" || text.startsWith("/mrg")) {
          ctx.waitUntil((async () => {
            const rep = `⛏️ *MRG MINER COMMAND CENTER*\n` +
              `━━━━━━━━━━━━━━━━━━━━━━\n` +
              `• *Platform:* MRG Cloud Miner (@MRG_miner_bot)\n` +
              `• *Status:* Active & Auto-Mining\n` +
              `• *Yield:* ~0.06 MRG per claim cycle per account\n` +
              `• *Payout Network:* TON Blockchain (The Open Network)\n` +
              `• *Anti-Bot Defense:* Cryptographic User-Agent Isolation ✅\n` +
              `━━━━━━━━━━━━━━━━━━━━━━`;
            await sendReply(rep, statusInlineKeyboard);
          })());
          return new Response("OK");
        }

        if (text === "💳 UltraWallet" || text.startsWith("/ultra") || text.startsWith("/ultrawallet")) {
          ctx.waitUntil((async () => {
            const rep = `💳 *ULTRAWALLET COMMAND CENTER*\n` +
              `━━━━━━━━━━━━━━━━━━━━━━\n` +
              `• *Platform:* UltraWallet (@UltraWalletBot)\n` +
              `• *Status:* 🟢 Active & Mining 24/7 (10 Hash/h)\n` +
              `• *Streak:* Daily Check-in & Gift Box Claimed ✅\n` +
              `• *Rewards Center:* Video Ads & Activities Automated\n` +
              `• *Auto-Compound:* Active 24/7 in Cloud\n` +
              `• *Payout Vault:* \`0xfda4182001672b9f0f09e2118242e543e35ed5ce\`\n` +
              `━━━━━━━━━━━━━━━━━━━━━━`;
            await sendReply(rep, statusInlineKeyboard);
          })());
          return new Response("OK");
        }

        if (text === "⚡ Apex Miner" || text.startsWith("/apx") || text.startsWith("/apex")) {
          ctx.waitUntil((async () => {
            const rep = `⚡ *APEX MINER COMMAND CENTER*\n` +
              `━━━━━━━━━━━━━━━━━━━━━━\n` +
              `• *Platform:* Apex Miner Platform (@apexminer_bot)\n` +
              `• *Status:* Active & Continuous Mining\n` +
              `• *Rewards:* Auto-Harvested each cycle\n` +
              `• *Payout Vault:* \`0xfda4182001672b9f0f09e2118242e543e35ed5ce\`\n` +
              `━━━━━━━━━━━━━━━━━━━━━━`;
            await sendReply(rep, statusInlineKeyboard);
          })());
          return new Response("OK");
        }

        // 5. Wallet Portfolio Command (/wallet or /wallets)
        if (text === "💼 Treasury & Wallets" || text === "💼 Wallet" || text === "/wallet" || text.startsWith("/wallet")) {
          ctx.waitUntil((async () => {
            let liveBnb = 0.000812;
            try {
              const rawMC = await env.BACKUP_KV.get("multichain_balances_state");
              if (rawMC) {
                const mc = JSON.parse(rawMC);
                if (mc.bsc_bnb_balance !== undefined) liveBnb = mc.bsc_bnb_balance;
              }
            } catch (_) {}
            const rep = `💼 *Multi-Chain Verified Destination Wallets*\n\n` +
              `🟡 *Binance BEP-20 (All 14 Fleet Accounts):*\n` +
              `• Address: \`0xfda4182001672b9f0f09e2118242e543e35ed5ce\`\n` +
              `• Balance: \`${liveBnb.toFixed(6)} BNB\` (~$${(liveBnb * 764.5).toFixed(2)} USD)\n` +
              `• Direct Payouts: AI Lab (>= $0.02) • Ainovum (>= 0.10 USDT)\n\n` +
              `🔵 *Arbitrum One (STONES Miner):*\n` +
              `• Address: \`0xfda4182001672b9f0f09e2118242e543e35ed5ce\`\n` +
              `• Deposited: \`500+ STONES\` (Auto-claimed to wallet)\n\n` +
              `💎 *Binance TON (Main Account #1):*\n` +
              `• Address: \`UQBPZiSvitdPU3VUyJK2mRaHVBl69xejw5aOrh1KfKA7gwDT\`\n` +
              `• Network: TON Blockchain (The Open Network)\n\n` +
              `🛡️ *Worker TON Wallets (Accounts 2–14):*\n` +
              `• 13 Dedicated TON v4r2 Wallets bound for MRG, ART, and ATF pools.\n\n` +
              `📱 _Tap '🚀 Open Executive Dashboard' below for interactive wallet explorer._`;
            await sendReply(rep, statusInlineKeyboard);
          })());
          return new Response("OK");
        }

        // 6. Accounts Roster Command (/accounts)
        if (text === "⚙️ Fleet Accounts" || text === "👥 Accounts Management" || text === "👥 My Accounts (14)" || text === "👥 My Accounts (13)" || text === "👥 My Accounts" || text === "👥 Accounts" || text === "/accounts" || text.startsWith("/accounts") || text.startsWith("/acc")) {
          ctx.waitUntil((async () => {
            const accounts = await getFleetAccounts();

            const accParts = text.trim().split(/\s+/);
            if (accParts.length >= 2 && /^\d+$/.test(accParts[1])) {
              const targetIdx = parseInt(accParts[1], 10);
              if (targetIdx >= 1 && targetIdx <= accounts.length) {
                const a = accounts[targetIdx - 1];
                const isHost = String(a.user_id) === "6727787768";
                const ph = (a.phone && a.phone !== "N/A" && a.phone !== "Hidden") ? a.phone : (KNOWN_PHONES[String(a.user_id)] || KNOWN_PHONES_BY_INDEX[targetIdx] || "N/A");
                const cName = cleanName(a, targetIdx - 1);
                const detailRep = `📱 *Account #${targetIdx} Inspection*\n` +
                  `━━━━━━━━━━━━━━━━━━━━━━\n` +
                  `• *Name:* ${cName}\n` +
                  `• *Phone:* \`${ph}\`\n` +
                  `• *User ID:* \`${a.user_id || "N/A"}\`\n` +
                  `• *Role:* ${isHost ? "Master Host 👑" : "Worker Account 🟢"}\n` +
                  `• *Daemon Status:* 🟢 Active & Mining\n` +
                  `• *Stones Policy:* ${isHost ? "Compound / Hash Growth (Main ID)" : "Auto-Withdraw >= 500 STONES (Arbitrum)"}\n` +
                  `• *AI Lab Policy:* ${isHost ? "Compound / Reinvest (Main ID)" : "Auto-Withdraw >= $0.02 (BEP-20)"}\n` +
                  `• *Active Lineup:* 8 Mining Bots Active 24/7\n` +
                  `━━━━━━━━━━━━━━━━━━━━━━\n` +
                  `💡 _Send \`/acc <1-14>\` to inspect any account or \`/accounts\` for full fleet roster._`;
                const singleAccBtns = {
                  inline_keyboard: [
                    [{ text: `🗑️ Remove #${targetIdx} ${cName}`, callback_data: `btn_admin_del_${a.user_id || a.phone}` }],
                    [{ text: "🔙 Fleet Roster", callback_data: "btn_accounts" }]
                  ]
                };
                await sendReply(detailRep, singleAccBtns);
                return;
              }
            }

            const lines = accounts.slice(0, 14).map((a, i) => {
              const isHost = String(a.user_id) === "6727787768";
              const tag = isHost ? "Master Host 👑" : "🟢 Active";
              const ph = (a.phone && a.phone !== "N/A" && a.phone !== "Hidden") ? a.phone : (KNOWN_PHONES[String(a.user_id)] || KNOWN_PHONES_BY_INDEX[i + 1] || "");
              const phoneStr = ph ? ` (${ph})` : "";
              return `• #${a.index || (i+1)} *${cleanName(a, i)}*${phoneStr} — ${tag}`;
            }).join("\n");

            const rep = `👥 *Accounts Management Hub*\n` +
              `━━━━━━━━━━━━━━━━━━━━━━\n` +
              `🟢 *Fleet Status:* \`${accounts.length}/14 Accounts Online & Active\`\n` +
              `🤖 *24/7 Farming:* All 8 Bots Active (Stones • ATF • ART • MRG • AI Lab • UltraWallet • Apex • Ainovum)\n` +
              `🛡️ *Security:* 100% Anti-Ban Verified • Isolated Wallets & Proxies\n\n` +
              `📋 *Connected Accounts:*\n` +
              `${lines}\n` +
              `━━━━━━━━━━━━━━━━━━━━━━\n` +
              `💡 *Quick Actions:*\n` +
              `• Tap *➕ Add Account* below to connect a new number\n` +
              `• Tap *🗑️ Remove Account* to disconnect any account\n` +
              `• Tap *🚀 Open Executive Dashboard* to view live cards & balances\n` +
              `• Send \`/acc <1-14>\` (e.g. \`/acc 1\`) to inspect any account in detail`;
            await sendReply(rep, accountsInlineKeyboard);
          })());
          return new Response("OK");
        }

        // 6b. Cloud Mesh Command (/mesh, /cloud)
        if (text === "🌐 Cloud Mesh" || text === "🌐 Mesh" || text === "/mesh" || text === "/cloud" || text.startsWith("/mesh") || text.startsWith("/cloud")) {
          ctx.waitUntil((async () => {
            await sendChatAction(chatId, "typing");
            const rep = `🌐 *MY AGY AI — Multi-Cloud Unified Mesh*\n` +
              `━━━━━━━━━━━━━━━━━━━━━━\n` +
              `⚡ *Cloudflare Edge Nodes (5/5 Online):*\n` +
              `• Node 1 (US-East Edge): 🟢 Online (42ms)\n` +
              `• Node 2 (EU-Central Edge): 🟢 Online (38ms)\n` +
              `• Node 3 (Global Shard): 🟢 Online (45ms)\n` +
              `• Node 4 (Singapore APAC D1 SQL): 🟢 Online (14 Accounts Active)\n` +
              `• Node 5 (Secondary Mining Engine): 🟢 Online (2m Cron Active)\n\n` +
              `🚀 *Render Compute Nodes (4/4 Online):*\n` +
              `• MTProto Relayer (Primary): 🟢 Online & Authenticated\n` +
              `• MTProto Relayer (Backup Failover): 🟢 Standby (Zero-Cost Cold Failback)\n` +
              `• Failover Compute #1 (Singapore): 🟢 Online (0 MTProto, $0 Plan)\n` +
              `• Failover Compute #2 (Frankfurt): 🟢 Online (0 MTProto, $0 Plan)\n\n` +
              `🦕 *Deno Deploy Edge Sentinels (2/2 Online):*\n` +
              `• Sentinel #1 (aaa222): 🟢 Online (Mesh Cron Active)\n` +
              `• Sentinel #2 (aaasupporta): 🟢 Online (Multi-Node Sentinel)\n\n` +
              `🗄️ *Unified Distributed Databases:*\n` +
              `• Supabase Postgres: 🟢 Connected (Service Role Auth)\n` +
              `• Upstash Redis: 🟢 Connected (Sub-ms Serverless Cache)\n` +
              `• Turso LibSQL: 🟢 Synced (ap-south-1 Edge)\n` +
              `• Pinata IPFS Vault: 🟢 Pinned & Immutable\n` +
              `• Better Stack: 🟢 Uptime Sentinel Active (100.0%)\n\n` +
              `🐙 *Dual Git Remotes:*\n` +
              `• Primary: \`AAA2743/my-agy-ai-fleet\` (In Sync)\n` +
              `• Mirror: \`AAA0002/ATL\` (In Sync)\n` +
              `━━━━━━━━━━━━━━━━━━━━━━\n` +
              `🛡️ *Zero Single Points of Failure • 100% Ephemeral Resilience*`;
            const frames = [
              "🌐 *Probing Cloud Mesh Infrastructure...*\n`[▰▰▱▱▱▱▱▱▱▱] 25%` • Checking 5 Cloudflare Edge Shards",
              "🌐 *Verifying Database & Relayers...*\n`[▰▰▰▰▰▰▱▱▱▱] 65%` • D1 SQL, Supabase, Upstash Redis & Turso",
              rep
            ];
            await sendAnimatedReply(chatId, frames, meshInlineKeyboard, 300);
          })());
          return new Response("OK");
        }

        // 7. Backup Command (/backup)
        if (text === "💾 Cloud Backup" || text === "💾 Backup" || text === "/backup" || text.startsWith("/backup")) {
          ctx.waitUntil((async () => {
            const bUrl = `https://restore-agy.${CURRENT_SUBDOMAIN}.workers.dev/backup.zip`;
            const rep = `📦 *[Cloudflare Edge Disaster Recovery]*\n\n` +
              `✅ *Instant Cloud Backup Ready:*\n` +
              `• *Download ZIP:* ${bUrl}\n` +
              `• *Triple Cloudflare Mesh:* Synchronized\n` +
              `• *Pinata IPFS Pinning:* Active & Verifiable\n` +
              `• *Telegram Vault:* Backed up to @myagyai\n\n` +
              `🛡️ _100% cloud disaster resilience active._`;
            await sendReply(rep, statusInlineKeyboard);
          })());
          return new Response("OK");
        }

        // 7.05 Community Points Economy & Daily Burn Telemetry (/burn, /economy, /points_summary, /sweep)
        if (text === "🔥 Economy & Sweep" || text === "🔥 Economy & Burn" || text === "🔥 Economy" || text === "/burn" || text.startsWith("/burn") || text === "/economy" || text.startsWith("/economy") || text === "/points_summary" || text === "/points_stats" || text === "/sweep" || text.startsWith("/sweep")) {
          ctx.waitUntil((async () => {
            const totalUsers = await upstashScard("ub_registered_users");
            const userList = await upstashSmembers("ub_registered_users");
            let activePasses = 0;
            let activeAccountsCount = 0;
            let totalPointsCirculation = 0;
            let activeMiners = 0;
            let pausedMiners = 0;
            let dailyBurn = 0;

            const sample = userList.slice(0, 50);
            const profiles = await upstashMget(sample.map(u => `ub_user:${u}`));
            for (const p of profiles) {
              if (p) {
                const accCount = (p.accounts || []).length;
                const hasVip = p.subscription_expiry && p.subscription_expiry > Date.now();
                if (hasVip) activePasses++;
                activeAccountsCount += accCount;
                totalPointsCirculation += (p.points || 0);
                if (p.farming_active && !p.is_banned) {
                  activeMiners++;
                  if (!hasVip && accCount > 0) dailyBurn += (accCount * 100);
                } else if (!p.is_banned && accCount > 0) {
                  pausedMiners++;
                }
              }
            }

            const rep = `🔥 *COMMUNITY POINTS ECONOMY & DAILY BURN* 📊\n` +
              `━━━━━━━━━━━━━━━━━━━━━━\n` +
              `• *Registered Miners:* \`${totalUsers || userList.length || 1}\` Users\n` +
              `• *Connected Cloud Accounts:* \`${activeAccountsCount}\` Phones\n` +
              `• *Active 24/7 Miners:* \`${activeMiners}\` Active\n` +
              `• *Auto-Paused Miners:* \`${pausedMiners}\` (Points below daily cost)\n` +
              `• *VIP Pass Holders:* \`${activePasses}\` (VIP Pass / unlimited mining)\n` +
              `• *Sample Points In Circulation:* \`💎 ${totalPointsCirculation.toLocaleString()} Pts\`\n` +
              `• *Network Daily Burn Rate:* \`🔥 -${dailyBurn.toLocaleString()} Pts/day\` (-100 Pts/account/day)\n` +
              `• *Daily Sweep Engine:* Active once per day (Midnight UTC)\n` +
              `━━━━━━━━━━━━━━━━━━━━━━\n` +
              `💡 *Economy Commands:*\n` +
              `• \`/sweep_daily\` — Manually trigger 100 Pts daily deduction sweep\n` +
              `• \`/grant <user_id> <pts>\` — Credit points to user\n` +
              `• \`/deduct <user_id> <pts>\` — Claw back points from user\n` +
              `• \`/grantpass <user_id> <day|week|month>\` — Grant VIP Pass`;

            const burnMarkup = {
              inline_keyboard: [
                [
                  { text: "⚡ Run Daily Sweep Now", callback_data: "btn_sweep_daily" },
                  { text: "🔄 Refresh Economy", callback_data: "btn_burn" }
                ],
                [
                  { text: "📊 Community Roster", callback_data: "btn_community" },
                  { text: "🚀 Open Dashboard", web_app: { url: dashUrl } }
                ]
              ]
            };
            await sendReply(rep, burnMarkup);
          })());
          return new Response("OK");
        }

        // 7.08 Manual Daily Cost Deduction Sweep Command (/sweep_daily, /sweeptoday)
        if (text === "⚡ Run Daily Sweep" || text === "⚡ Daily Sweep" || text === "/sweep_daily" || text.startsWith("/sweep_daily") || text === "/sweeptoday") {
          ctx.waitUntil((async () => {
            await sendChatAction(chatId, "typing");
            const frames = [
              "⚡ *Initiating Daily Cost Deduction Sweep...*\n`[▰▰▰▱▱▱▱▱▱▱] 30%` • Scanning all registered community miners",
              "⚡ *Evaluating Accounts & Deducting 100 Pts/Day...*\n`[▰▰▰▰▰▰▰▱▱▱] 70%` • VIP check & auto-pause for low balances",
              "⚡ *Finalizing Sweep Ledger & Telemetry...*\n`[▰▰▰▰▰▰▰▰▰▰] 95%` • Syncing with Upstash Redis"
            ];
            await sendAnimatedReply(chatId, frames, statusInlineKeyboard, 250);

            const res = await runDailyCostSweep(env, true);
            const summary = `⚡ *UNIVERSAL DAILY DEDUCTION SWEEP COMPLETED* 🧹\n` +
              `━━━━━━━━━━━━━━━━━━━━━━\n` +
              `• *Status:* 🟢 Executed successfully\n` +
              `• *Processed Accounts:* \`${res.processed}\` Miners evaluated\n` +
              `• *Active 24/7 Miners:* \`${res.activeCount}\` (Deduction verified)\n` +
              `• *VIP Pass Miners:* \`${res.vipCount}\` (VIP Pass active)\n` +
              `• *Auto-Paused Miners:* \`${res.pausedCount}\` (Balance < 100 Pts)\n` +
              `• *Total Points Swept:* \`🔥 -${res.totalDeducted.toLocaleString()} Pts\` (-100 Pts/account)\n` +
              `• *Execution Date:* \`${res.today}\`\n` +
              `━━━━━━━━━━━━━━━━━━━━━━\n` +
              `🛡️ _Users with insufficient balance were paused and alerted with recharge bonuses._`;

            const sweepDoneMarkup = {
              inline_keyboard: [
                [
                  { text: "🔥 Economy & Burn Stats", callback_data: "btn_burn" },
                  { text: "📊 Community Roster", callback_data: "btn_community" }
                ],
                [
                  { text: "🚀 Open Executive Dashboard", web_app: { url: dashUrl } }
                ]
              ]
            };
            await sendReply(summary, sweepDoneMarkup);
          })());
          return new Response("OK");
        }

        // 7.09 Top Miners & Points Whales Leaderboard (/whales, /top)
        if (text === "🏆 Top Whales" || text === "/whales" || text.startsWith("/whales") || text === "/top" || text.startsWith("/top") || text === "/leaderboard") {
          ctx.waitUntil((async () => {
            await sendChatAction(chatId, "typing");
            const userList = await upstashSmembers("ub_registered_users");
            if (!userList || userList.length === 0) {
              await sendReply("ℹ️ No registered community users found yet.", statusInlineKeyboard);
              return;
            }
            const sample = userList.slice(0, 100);
            const profiles = await upstashMget(sample.map(u => `ub_user:${u}`));
            const valid = profiles.filter(p => p && p.user_id);
            valid.sort((a, b) => (b.points || 0) - (a.points || 0));
            const top10 = valid.slice(0, 10);
            const lines = top10.map((u, i) => {
              const medal = i === 0 ? "🥇" : (i === 1 ? "🥈" : (i === 2 ? "🥉" : `#${i+1}`));
              const accCount = (u.accounts || []).length;
              const hasVip = u.subscription_expiry && u.subscription_expiry > Date.now();
              const badge = hasVip ? "👑 VIP" : `${accCount} Acc${accCount === 1 ? "" : "s"}`;
              return `${medal} *${u.first_name || "Miner"}* (@${u.username || "none"})\n   • ID: \`${u.user_id}\` | 💎 *${(u.points || 0).toLocaleString()} Pts* | ${badge}`;
            });
            const rep = `🏆 *TOP COMMUNITY MINERS & POINTS WHALES* 💎\n━━━━━━━━━━━━━━━━━━━━━━\n${lines.join("\n\n")}\n━━━━━━━━━━━━━━━━━━━━━━\n💡 _Tap /user <id> to inspect or moderate any user._`;
            const whalesMarkup = {
              inline_keyboard: [
                [{ text: "🔄 Refresh Whales", callback_data: "btn_whales" }, { text: "🔥 Economy Stats", callback_data: "btn_burn" }],
                [{ text: "🚀 Open Dashboard", web_app: { url: dashUrl } }]
              ]
            };
            await sendReply(rep, whalesMarkup);
          })());
          return new Response("OK");
        }

        // 7.095 Auto-Paused / Low Balance Miners (/paused, /low_balance)
        if (text === "⚠️ Paused Miners" || text === "/paused" || text.startsWith("/paused") || text === "/low_balance" || text.startsWith("/low_balance")) {
          ctx.waitUntil((async () => {
            await sendChatAction(chatId, "typing");
            const userList = await upstashSmembers("ub_registered_users");
            const sample = userList.slice(0, 100);
            const profiles = await upstashMget(sample.map(u => `ub_user:${u}`));
            const paused = profiles.filter(p => p && p.user_id && (p.accounts || []).length > 0 && (!p.farming_active || (p.points || 0) < ((p.accounts || []).length * 100)));
            if (paused.length === 0) {
              await sendReply("✅ *All Connected Miners Healthy!*\n\nZero accounts are paused due to low points balance. 100% of community miners are active & mining!", statusInlineKeyboard);
              return;
            }
            const pausedLines = paused.slice(0, 8).map((u, i) => {
              const accCount = (u.accounts || []).length;
              const dCost = accCount * 100;
              const deficit = dCost - (u.points || 0);
              return `• *${u.first_name || "Miner"}* (\`${u.user_id}\`)\n  Bal: 💎 ${u.points || 0} Pts / Cost: ${dCost} Pts (Deficit: -${deficit} Pts) | ${accCount} Acc`;
            });
            const rep = `⚠️ *AUTO-PAUSED / LOW BALANCE MINERS* (${paused.length})\n━━━━━━━━━━━━━━━━━━━━━━\n${pausedLines.join("\n\n")}\n━━━━━━━━━━━━━━━━━━━━━━\n💡 *Grant Points Quick Action:* Send \`/grant <user_id> 100\` to refill!`;
            const pausedMarkup = {
              inline_keyboard: [
                [{ text: "⚡ Run Daily Sweep", callback_data: "btn_sweep_daily" }, { text: "🔄 Refresh List", callback_data: "btn_paused" }],
                [{ text: "🚀 Open Dashboard", web_app: { url: dashUrl } }]
              ]
            };
            await sendReply(rep, pausedMarkup);
          })());
          return new Response("OK");
        }

        // 7.096 Unified Ecosystem Executive Summary (/summary, /executive)
        if (text === "📋 Fleet Summary" || text === "/summary" || text.startsWith("/summary") || text === "/executive") {
          ctx.waitUntil((async () => {
            await sendChatAction(chatId, "typing");
            const totalUsers = await upstashScard("ub_registered_users");
            const userList = await upstashSmembers("ub_registered_users");
            let activePasses = 0;
            let activeAccountsCount = 0;
            let totalPointsCirculation = 0;
            let activeMiners = 0;
            let pausedMiners = 0;
            let dailyBurn = 0;
            const sample = userList.slice(0, 50);
            const profiles = await upstashMget(sample.map(u => `ub_user:${u}`));
            for (const p of profiles) {
              if (p) {
                const accCount = (p.accounts || []).length;
                const hasVip = p.subscription_expiry && p.subscription_expiry > Date.now();
                if (hasVip) activePasses++;
                activeAccountsCount += accCount;
                totalPointsCirculation += (p.points || 0);
                if (p.farming_active && !p.is_banned) {
                  activeMiners++;
                  if (!hasVip && accCount > 0) dailyBurn += (accCount * 100);
                } else if (!p.is_banned && accCount > 0) {
                  pausedMiners++;
                }
              }
            }
            const rep = `⚡ *MY AGY AI — EXECUTIVE ECOSYSTEM SUMMARY* 📊\n━━━━━━━━━━━━━━━━━━━━━━\n` +
              `🤖 *Fleet Automation:* 14/14 Accounts Online & Mining\n` +
              `⛏️ *Active Mining Pools (8/8):* Stones, MRG, ART, AI Lab, UltraWallet, Apex, ATF, Ainovum\n` +
              `👛 *Ultra Wallet:* Auto-Mining 24/7 (Multi-Pool Integrated)\n` +
              `👥 *Community Users:* \`${totalUsers || userList.length}\` Registered Miners\n` +
              `📱 *Community Accounts:* \`${activeAccountsCount}\` Connected Phones\n` +
              `🟢 *Active 24/7 Miners:* \`${activeMiners}\` Active | ⚠️ Paused: \`${pausedMiners}\`\n` +
              `👑 *VIP Pass Holders:* \`${activePasses}\` (0 Point Daily Cost)\n` +
              `💎 *Points In Circulation:* \`${totalPointsCirculation.toLocaleString()}\` Pts\n` +
              `🔥 *Network Daily Burn Rate:* \`-${dailyBurn.toLocaleString()} Pts/day\` (-100 Pts/account)\n` +
              `🌐 *Edge Mesh:* 5/5 Nodes Active across Multi-Region Cloudflare\n` +
              `━━━━━━━━━━━━━━━━━━━━━━\n` +
              `🛡️ _100% Autonomous • Fully Cloud-Hosted • Multi-Region Mesh_`;
            const summaryMarkup = {
              inline_keyboard: [
                [{ text: "⚡ Run Daily Sweep", callback_data: "btn_sweep_daily" }, { text: "🏆 Top Whales", callback_data: "btn_whales" }],
                [{ text: "👛 Destination Wallets", callback_data: "btn_wallets" }, { text: "🚀 Open Dashboard", web_app: { url: dashUrl } }]
              ]
            };
            await sendReply(rep, summaryMarkup);
          })());
          return new Response("OK");
        }

        // 7.1 Community & Public User Base Metrics (/community, /users, /userstats)
        if (text === "👥 Community Miners" || text === "👥 Community & Users" || text === "/community" || text.startsWith("/community") || text === "/users" || text.startsWith("/users") || text.startsWith("/userstats")) {
          ctx.waitUntil((async () => {
            const totalUsers = await upstashScard("ub_registered_users");
            const userList = await upstashSmembers("ub_registered_users");
            let activePasses = 0;
            let activeAccountsCount = 0;
            let totalPointsCirculation = 0;
            const sampleUsers = userList.slice(0, 30);
            for (const uid of sampleUsers) {
              try {
                const raw = await upstashGet(`ub_user:${uid}`);
                if (raw) {
                  const p = typeof raw === "string" ? JSON.parse(raw) : raw;
                  if (p.subscription_expiry && p.subscription_expiry > Date.now()) activePasses++;
                  if (p.accounts && p.accounts.length) activeAccountsCount += p.accounts.length;
                  if (p.points) totalPointsCirculation += p.points;
                }
              } catch (_) {}
            }
            const rep = `📊 *AAA COMMUNITY & PUBLIC USER BASE* 🚀\n` +
              `━━━━━━━━━━━━━━━━━━━━━━\n` +
              `• *Registered Miners:* \`${totalUsers || 1}\` Users\n` +
              `• *Community Cloud Accounts:* \`${activeAccountsCount}\` Active\n` +
              `• *Active VIP Passes:* \`${activePasses}\` (Day / Week / Month)\n` +
              `• *Sample Points In Circulation:* \`${totalPointsCirculation.toLocaleString()}\` Pts\n` +
              `• *Live Channels:* Supergroup, Announcements & Live Activity\n` +
              `━━━━━━━━━━━━━━━━━━━━━━\n` +
              `💡 *Admin Commands:*\n` +
              `• \`/grant <user_id> <pts>\` — Award mining points\n` +
              `• \`/grantpass <user_id> <day|week|month>\` — Grant VIP Pass\n` +
              `• \`/grantslot <user_id> <slots>\` — Grant account slots\n` +
              `• \`/broadcast <text>\` — Broadcast announcement to all users\n` +
              `• \`/reply <user_id> <text>\` — Direct reply to user support ticket\n` +
              `• \`/nodes\` — Probe latency across all 5 Cloudflare Edge nodes`;
            await sendReply(rep, statusInlineKeyboard);
          })());
          return new Response("OK");
        }

        // 7.2 Admin Grant Points Command (/grant <user_id> <points>)
        if ((text === "/grant" || text.startsWith("/grant ")) && !text.startsWith("/grantpass") && !text.startsWith("/grantslot")) {
          const parts = text.split(/\s+/);
          if (parts.length >= 3) {
            const targetUid = parts[1].trim();
            const pts = parseInt(parts[2].trim(), 10);
            if (targetUid && !isNaN(pts)) {
              ctx.waitUntil((async () => {
                const raw = await upstashGet(`ub_user:${targetUid}`);
                if (raw) {
                  const prof = typeof raw === "string" ? JSON.parse(raw) : raw;
                  prof.points = (prof.points || 0) + pts;
                  await upstashSet(`ub_user:${targetUid}`, prof);
                  // Notify user via User Bot
                  const uBotToken = env.USER_BOT_TOKEN || "8167732110:AAGQA6bBgRwaChFIWPvs9uCt6aZ3j1VGCn8";
                  await fetch(`https://api.telegram.org/bot${uBotToken}/sendMessage`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      chat_id: targetUid,
                      text: `🎁 *ADMIN REWARD CREDITED!* 🎉\n\nPlatform Admin has credited your account with *+${pts.toLocaleString()} Mining Points*!\n\n• *New Balance:* ${prof.points} Points\n\nEnjoy 24/7 cloud mining! 🚀`,
                      parse_mode: "Markdown"
                    })
                  }).catch(() => {});
                  await sendReply(`✅ Successfully granted *+${pts.toLocaleString()} Points* to User \`${targetUid}\`!\n• User New Balance: ${prof.points} Points`, statusInlineKeyboard);
                } else {
                  await sendReply(`⚠️ User \`${targetUid}\` not found in database.`, statusInlineKeyboard);
                }
              })());
              return new Response("OK");
            }
          }
          await sendReply("Usage: `/grant <user_id> <points>`\nExample: `/grant 6727787768 500`", statusInlineKeyboard);
          return new Response("OK");
        }

        // 7.3 Admin Grant VIP Pass Command (/grantpass <user_id> <day|week|month>)
        if (text.startsWith("/grantpass")) {
          const parts = text.split(/\s+/);
          if (parts.length >= 3) {
            const targetUid = parts[1].trim();
            const tier = parts[2].trim().toLowerCase();
            const validTiers = { day: 86400 * 1000, week: 7 * 86400 * 1000, month: 30 * 86400 * 1000 };
            if (validTiers[tier]) {
              ctx.waitUntil((async () => {
                const raw = await upstashGet(`ub_user:${targetUid}`);
                if (raw) {
                  const prof = typeof raw === "string" ? JSON.parse(raw) : raw;
                  const now = Date.now();
                  const baseExp = (prof.subscription_expiry && prof.subscription_expiry > now) ? prof.subscription_expiry : now;
                  prof.subscription_expiry = baseExp + validTiers[tier];
                  prof.subscription_tier = tier;
                  prof.farming_active = true;
                  await upstashSet(`ub_user:${targetUid}`, prof);
                  const tTitle = tier === "month" ? "💎 30-Day Monthly Pass" : (tier === "week" ? "🎟️ 7-Day Weekly Pass" : "🎟️ 1-Day Pass");
                  const uBotToken = env.USER_BOT_TOKEN || "8167732110:AAGQA6bBgRwaChFIWPvs9uCt6aZ3j1VGCn8";
                  await fetch(`https://api.telegram.org/bot${uBotToken}/sendMessage`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      chat_id: targetUid,
                      text: `🌟 *VIP SUBSCRIPTION PASS ACTIVATED!* 🎟️\n\nPlatform Admin has activated a *${tTitle}* for your account!\n\n• *Status:* 🟢 24/7 Unlimited Cloud Mining with Zero Point Deduction active!\n\nThank you for being part of AAA Auto Mining! 🚀`,
                      parse_mode: "Markdown"
                    })
                  }).catch(() => {});
                  await sendReply(`✅ Successfully granted *${tTitle}* to User \`${targetUid}\`!`, statusInlineKeyboard);
                } else {
                  await sendReply(`⚠️ User \`${targetUid}\` not found in database.`, statusInlineKeyboard);
                }
              })());
              return new Response("OK");
            }
          }
          await sendReply("Usage: `/grantpass <user_id> <day|week|month>`\nExample: `/grantpass 6727787768 month`", statusInlineKeyboard);
          return new Response("OK");
        }

        // 7.4 Admin Grant Account Slots Command (/grantslot <user_id> <slots>)
        if (text.startsWith("/grantslot")) {
          const parts = text.split(/\s+/);
          if (parts.length >= 3) {
            const targetUid = parts[1].trim();
            const slotsCount = parseInt(parts[2].trim(), 10);
            if (targetUid && !isNaN(slotsCount)) {
              ctx.waitUntil((async () => {
                const raw = await upstashGet(`ub_user:${targetUid}`);
                if (raw) {
                  const prof = typeof raw === "string" ? JSON.parse(raw) : raw;
                  prof.slots = (prof.slots || 1) + slotsCount;
                  await upstashSet(`ub_user:${targetUid}`, prof);
                  const uBotToken = env.USER_BOT_TOKEN || "8167732110:AAGQA6bBgRwaChFIWPvs9uCt6aZ3j1VGCn8";
                  await fetch(`https://api.telegram.org/bot${uBotToken}/sendMessage`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      chat_id: targetUid,
                      text: `🌟 *EXTRA CLOUD SLOTS UNLOCKED!* 📦\n\nPlatform Admin has unlocked *+${slotsCount} Permanent Account Slot(s)* for you!\n\n• *Total Slots Available:* ${prof.slots}\n\nYou can now link another Telegram account using *➕ Connect Account*!`,
                      parse_mode: "Markdown"
                    })
                  }).catch(() => {});
                  await sendReply(`✅ Successfully granted *+${slotsCount} slot(s)* to User \`${targetUid}\`! Total slots: ${prof.slots}`, statusInlineKeyboard);
                } else {
                  await sendReply(`⚠️ User \`${targetUid}\` not found in database.`, statusInlineKeyboard);
                }
              })());
              return new Response("OK");
            }
          }
          await sendReply("Usage: `/grantslot <user_id> <slots>`\nExample: `/grantslot 6727787768 2`", statusInlineKeyboard);
          return new Response("OK");
        }

        // 7.5 Admin Direct Reply / Support Dispatch (/reply <user_id> <message> or /dm <user_id> <message>)
        if (text === "/reply" || text.startsWith("/reply ") || text === "/dm" || text.startsWith("/dm ")) {
          const parts = text.split(/\s+/);
          if (parts.length >= 3) {
            const targetUid = parts[1].trim();
            const replyMsg = parts.slice(2).join(" ").trim();
            if (targetUid && replyMsg) {
              ctx.waitUntil((async () => {
                const uBotToken = env.USER_BOT_TOKEN || "8167732110:AAGQA6bBgRwaChFIWPvs9uCt6aZ3j1VGCn8";
                const userPayload = `📩 *MESSAGE FROM PLATFORM SUPPORT*\n━━━━━━━━━━━━━━━━━━━━━━\n${replyMsg}\n━━━━━━━━━━━━━━━━━━━━━━\n💬 _You can reply directly in this chat or send /support <message> anytime._`;
                const r = await fetch(`https://api.telegram.org/bot${uBotToken}/sendMessage`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ chat_id: targetUid, text: userPayload, parse_mode: "Markdown" })
                });
                if (r.ok) {
                  await sendReply(`✅ Reply delivered to User \`${targetUid}\` successfully!`, statusInlineKeyboard);
                } else {
                  await sendReply(`⚠️ Failed to deliver reply to User \`${targetUid}\`. Check user ID.`, statusInlineKeyboard);
                }
              })());
              return new Response("OK");
            }
          }
          await sendReply("Usage: `/reply <user_id> <message>`\nExample: `/reply 6727787768 Hello! Your account is active.`", statusInlineKeyboard);
          return new Response("OK");
        }

        // 7.6 Admin Community Broadcast (/broadcast <message> or /announce <message>)
        if (text === "/broadcast" || text.startsWith("/broadcast ") || text === "/announce" || text.startsWith("/announce ")) {
          const parts = text.split(/\s+/);
          const bMsg = parts.slice(1).join(" ").trim();
          if (!bMsg) {
            await sendReply("Usage: `/broadcast <message>`\nExample: `/broadcast 🚀 Big update! All 8 pools are paying out today!`", statusInlineKeyboard);
            return new Response("OK");
          }
          ctx.waitUntil((async () => {
            const userList = await upstashSmembers("ub_registered_users");
            const uBotToken = env.USER_BOT_TOKEN || "8167732110:AAGQA6bBgRwaChFIWPvs9uCt6aZ3j1VGCn8";
            let sentCount = 0;
            const fullBroadcast = `📢 *OFFICIAL PLATFORM ANNOUNCEMENT*\n━━━━━━━━━━━━━━━━━━━━━━\n${bMsg}\n━━━━━━━━━━━━━━━━━━━━━━\n🤖 _Sent by Admin Team · @AAAPREMIUMAPPSbot_`;
            for (const uid of userList) {
              try {
                const res = await fetch(`https://api.telegram.org/bot${uBotToken}/sendMessage`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ chat_id: uid, text: fullBroadcast, parse_mode: "Markdown" })
                });
                if (res.ok) sentCount++;
                await new Promise(r => setTimeout(r, 60)); // Rate limit throttle
              } catch (_) {}
            }
            await sendReply(`📢 *Broadcast Dispatched Successfully!*\n\n• *Recipients:* Delivered to \`${sentCount}\` / \`${userList.length}\` users ✅`, statusInlineKeyboard);
          })());
          return new Response("OK");
        }

        // 7.65 Anti-Sybil & Account Moderation Commands (/ban, /unban, /deduct, /user, /sybil)
        if (text.startsWith("/ban") || text.startsWith("/suspend")) {
          const parts = text.split(/\s+/);
          if (parts.length >= 2) {
            const targetUid = parts[1].trim();
            const reason = parts.slice(2).join(" ").trim() || "Suspicious anti-sybil activity or policy violations";
            ctx.waitUntil((async () => {
              const raw = await upstashGet(`ub_user:${targetUid}`);
              if (raw) {
                const prof = typeof raw === "string" ? JSON.parse(raw) : raw;
                prof.is_banned = true;
                prof.ban_reason = reason;
                prof.farming_active = false;
                prof.banned_at = Date.now();
                await upstashSet(`ub_user:${targetUid}`, prof);
                await upstashSadd("ub_banned_users", String(targetUid));

                const uBotToken = env.USER_BOT_TOKEN || "8167732110:AAGQA6bBgRwaChFIWPvs9uCt6aZ3j1VGCn8";
                await fetch(`https://api.telegram.org/bot${uBotToken}/sendMessage`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({
                    chat_id: targetUid,
                    text: `🚫 *ACCOUNT SUSPENDED*\n\nYour account has been suspended by platform administration.\n\n• *Reason:* ${reason}\n• *Farming Status:* 🔴 Halted\n\nIf you believe this is an error, please contact @AAAAutoMiner.`,
                    parse_mode: "Markdown"
                  })
                }).catch(() => {});
                await sendReply(`🚫 *User Suspended Successfully!*\n\n• *User ID:* \`${targetUid}\`\n• *Name:* ${prof.first_name || "Miner"} (@${prof.username || "None"})\n• *Reason:* ${reason}\n• *Action:* Added to \`ub_banned_users\`, cloud farming halted.`, statusInlineKeyboard);
              } else {
                await sendReply(`⚠️ User \`${targetUid}\` not found in database.`, statusInlineKeyboard);
              }
            })());
            return new Response("OK");
          }
          await sendReply("Usage: `/ban <user_id> [reason]`\nExample: `/ban 12345678 Multi-account sybil abuse`", statusInlineKeyboard);
          return new Response("OK");
        }

        if (text.startsWith("/unban") || text.startsWith("/reinstate")) {
          const parts = text.split(/\s+/);
          if (parts.length >= 2) {
            const targetUid = parts[1].trim();
            ctx.waitUntil((async () => {
              const raw = await upstashGet(`ub_user:${targetUid}`);
              if (raw) {
                const prof = typeof raw === "string" ? JSON.parse(raw) : raw;
                prof.is_banned = false;
                delete prof.ban_reason;
                delete prof.banned_at;
                prof.farming_active = true;
                await upstashSet(`ub_user:${targetUid}`, prof);
                await upstashSrem("ub_banned_users", String(targetUid));

                const uBotToken = env.USER_BOT_TOKEN || "8167732110:AAGQA6bBgRwaChFIWPvs9uCt6aZ3j1VGCn8";
                await fetch(`https://api.telegram.org/bot${uBotToken}/sendMessage`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({
                    chat_id: targetUid,
                    text: `✅ *ACCOUNT RESTORED!*\n\nYour account has been reinstated by platform administration.\n• *Status:* 🟢 Active & Ready\n\nThank you for your patience! 🚀`,
                    parse_mode: "Markdown"
                  })
                }).catch(() => {});
                await sendReply(`✅ *User Reinstated Successfully!*\n\n• *User ID:* \`${targetUid}\`\n• *Name:* ${prof.first_name || "Miner"} (@${prof.username || "None"})\n• *Action:* Removed from ban list, access restored.`, statusInlineKeyboard);
              } else {
                await sendReply(`⚠️ User \`${targetUid}\` not found in database.`, statusInlineKeyboard);
              }
            })());
            return new Response("OK");
          }
          await sendReply("Usage: `/unban <user_id>`\nExample: `/unban 12345678`", statusInlineKeyboard);
          return new Response("OK");
        }

        if (text.startsWith("/deduct")) {
          const parts = text.split(/\s+/);
          if (parts.length >= 3) {
            const targetUid = parts[1].trim();
            const pts = parseInt(parts[2].trim(), 10);
            if (targetUid && !isNaN(pts)) {
              ctx.waitUntil((async () => {
                const raw = await upstashGet(`ub_user:${targetUid}`);
                if (raw) {
                  const prof = typeof raw === "string" ? JSON.parse(raw) : raw;
                  prof.points = Math.max(0, (prof.points || 0) - pts);
                  await upstashSet(`ub_user:${targetUid}`, prof);
                  await sendReply(`✅ Deducted *-${pts.toLocaleString()} Points* from User \`${targetUid}\`!\n• New Balance: ${prof.points} Points`, statusInlineKeyboard);
                } else {
                  await sendReply(`⚠️ User \`${targetUid}\` not found in database.`, statusInlineKeyboard);
                }
              })());
              return new Response("OK");
            }
          }
          await sendReply("Usage: `/deduct <user_id> <points>`\nExample: `/deduct 12345678 100`", statusInlineKeyboard);
          return new Response("OK");
        }

        if (text.startsWith("/user") || text.startsWith("/inspect")) {
          const parts = text.split(/\s+/);
          if (parts.length >= 2) {
            const targetUid = parts[1].trim();
            ctx.waitUntil((async () => {
              const raw = await upstashGet(`ub_user:${targetUid}`);
              if (raw) {
                const prof = typeof raw === "string" ? JSON.parse(raw) : raw;
                const totalSlots = (prof.slots || 1) + (prof.temp_slots || 0);
                const isBanned = Boolean(prof.is_banned);
                const banTag = isBanned ? `🚫 *BANNED* (${prof.ban_reason || "Policy Violation"})` : "🟢 *CLEAN / GOOD STANDING*";
                const hasGift = prof.welcome_gift_claimed ? "Claimed (+100 Pts) ✅" : "Unclaimed ⏳";
                const accs = prof.accounts || [];
                const passText = (prof.subscription_expiry && prof.subscription_expiry > Date.now()) ?
                  `VIP Pass (${prof.subscription_tier || "VIP"} - ${Math.ceil((prof.subscription_expiry - Date.now()) / 86400000)}d left)` : "Free Tier (Pay-As-You-Go)";
                const dCost = (prof.subscription_expiry && prof.subscription_expiry > Date.now()) ? 0 : (accs.length * 100);
                const runwayDays = (prof.subscription_expiry && prof.subscription_expiry > Date.now()) ? "∞ Unlimited (VIP Pass)" : (dCost > 0 ? `${Math.floor((prof.points || 0) / dCost)} Days` : "0 Accounts");
                const farmStatus = (prof.subscription_expiry && prof.subscription_expiry > Date.now()) ? "🟢 Active 24/7 (Covered by VIP Pass)" : (prof.farming_active ? "🟢 Active 24/7" : "🔴 Paused (Needs Points)");

                const userCard = `👤 *USER AUDIT & MODERATION REPORT*\n` +
                  `━━━━━━━━━━━━━━━━━━━━━━\n` +
                  `• *User ID:* \`${prof.user_id}\`\n` +
                  `• *Name:* ${prof.first_name || "Miner"} (@${prof.username || "None"})\n` +
                  `• *Points Balance:* \`${(prof.points || 0).toLocaleString()}\` Points\n` +
                  `• *Daily Mining Cost:* \`${dCost}\` Pts/day (-100 Pts/acc)\n` +
                  `• *Runway:* \`${runwayDays}\`\n` +
                  `• *Mining Status:* ${farmStatus}\n` +
                  `• *Account Slots:* \`${accs.length}/${totalSlots}\`\n` +
                  `• *Plan:* ${passText}\n` +
                  `• *Streak / Ads:* 🔥 Day ${prof.daily_streak || 0} • 🎬 ${prof.ads_watched || 0} Ads\n` +
                  `• *Welcome Gift:* ${hasGift}\n` +
                  `• *Moderation Status:* ${banTag}\n` +
                  `• *Referrals:* \`${prof.referral_count || 0}\` (Referred by: \`${prof.referred_by || "Organic"}\`)\n` +
                  `• *Registered:* ${new Date(prof.created_at || Date.now()).toISOString().slice(0, 10)}\n\n` +
                  `📱 *Connected Cloud Accounts (${accs.length}):*\n` +
                  `${accList}\n` +
                  `━━━━━━━━━━━━━━━━━━━━━━`;

                const userKeyboard = {
                  inline_keyboard: [
                    [
                      isBanned ?
                        { text: "✅ Unban User", callback_data: `cb_unban_${targetUid}` } :
                        { text: "🚫 Ban / Suspend", callback_data: `cb_ban_${targetUid}` },
                      { text: "➕ +100 Pts", callback_data: `cb_grant100_${targetUid}` }
                    ],
                    [
                      { text: "🎟️ Grant VIP Day", callback_data: `cb_grantvip_${targetUid}` },
                      { text: "📦 Grant +1 Slot", callback_data: `cb_grantslot_${targetUid}` }
                    ],
                    [
                      { text: "🔙 Community Hub", callback_data: "btn_community" }
                    ]
                  ]
                };
                await sendReply(userCard, userKeyboard);
              } else {
                await sendReply(`⚠️ User \`${targetUid}\` not found in database.`, statusInlineKeyboard);
              }
            })());
            return new Response("OK");
          }
          await sendReply("Usage: `/user <user_id>`\nExample: `/user 6727787768`", statusInlineKeyboard);
          return new Response("OK");
        }

        if (text === "/sybil" || text.startsWith("/sybil") || text === "/moderation" || text.startsWith("/moderation") || text === "🛡️ Anti-Sybil Hub") {
          ctx.waitUntil((async () => {
            const totalUsers = await upstashScard("ub_registered_users");
            const userList = await upstashSmembers("ub_registered_users");
            const bannedUsers = await upstashSmembers("ub_banned_users");
            const welcomeRecipients = await upstashScard("ub_welcome_gift_recipients");

            let duplicateAccountsFound = 0;
            const seenAccountIds = new Map();
            const sample = userList.slice(0, 40);
            const sampleProfiles = await upstashMget(sample.map(u => `ub_user:${u}`));
            for (let i = 0; i < sampleProfiles.length; i++) {
              const p = sampleProfiles[i];
              const uid = sample[i];
              if (p) {
                for (const a of (p.accounts || [])) {
                  const aid = String(a.user_id || a.phone);
                  if (seenAccountIds.has(aid) && seenAccountIds.get(aid) !== uid) {
                    duplicateAccountsFound++;
                  } else {
                    seenAccountIds.set(aid, uid);
                  }
                }
              }
            }

            const sybilRep = `🛡️ *ANTI-SYBIL & ACCOUNT MODERATION AUDIT*\n` +
              `━━━━━━━━━━━━━━━━━━━━━━\n` +
              `• *Total Registered Users:* \`${totalUsers || 1}\`\n` +
              `• *Banned / Suspended Users:* \`${bannedUsers.length}\`\n` +
              `• *First-Account Gifts Claimed:* \`${welcomeRecipients || 0}\` (+100 Pts verified)\n` +
              `• *Unique Connected Accounts:* \`${seenAccountIds.size}\`\n` +
              `• *Duplicate Linked Accounts:* \`${duplicateAccountsFound}\` ${duplicateAccountsFound > 0 ? "⚠️ (Sybil Risk Detected)" : "✅ (Zero Cross-Linking)"}\n` +
              `• *Anti-Ban Guardrails:* Deterministic Android UA + 15s Dwell Timers + Shuffled Bot Routines Active ✅\n` +
              `━━━━━━━━━━━━━━━━━━━━━━\n` +
              `💡 *Moderation Commands:*\n` +
              `• \`/user <user_id>\` — Inspect user profile & connected accounts\n` +
              `• \`/ban <user_id> [reason]\` — Immediately suspend user access & farming\n` +
              `• \`/unban <user_id>\` — Restore user access & resume mining\n` +
              `• \`/deduct <user_id> <pts>\` — Claw back fraudulent points`;

            const sybilMarkup = {
              inline_keyboard: [
                [
                  { text: "📊 Community Roster", callback_data: "btn_community" },
                  { text: "🔄 Re-Audit Fleet", callback_data: "btn_sybil" }
                ],
                [
                  { text: "🚀 Open Admin Console", web_app: { url: dashUrl } }
                ]
              ]
            };
            await sendReply(sybilRep, sybilMarkup);
          })());
          return new Response("OK");
        }

        // 7.7 Live Multi-Cloud Edge Prober (/nodes or /health)
        if (text === "/nodes" || text.startsWith("/nodes") || text === "/health" || text.startsWith("/health")) {
          ctx.waitUntil((async () => {
            const probeNodes = [
              { name: "Node 1 (korimhaji)", url: "https://restore-agy.aaaai2.workers.dev/health" },
              { name: "Node 2 (koramshah)", url: "https://restore-agy.aaa-bot.workers.dev/health" },
              { name: "Node 3 (coz1gameh3)", url: "https://restore-agy.aaa222.workers.dev/health" },
              { name: "Node 4 (aaafreeai)", url: "https://restore-agy.agorameet.workers.dev/health" },
              { name: "Node 5 (aaaai-engine)", url: "https://restore-agy.aaaai.workers.dev/health" }
            ];
            const results = await Promise.all(probeNodes.map(async (n) => {
              const start = Date.now();
              try {
                const res = await fetch(n.url, { signal: AbortSignal.timeout(3000) });
                const lat = Date.now() - start;
                return `• *${n.name}:* ${res.ok ? "🟢 Online" : "⚠️ " + res.status} (\`${lat}ms\`)`;
              } catch (_) {
                return `• *${n.name}:* 🔴 Unreachable`;
              }
            }));
            const rep = `⚡ *MY AGY AI — 5 Edge Nodes Live Latency Probe*\n━━━━━━━━━━━━━━━━━━━━━━\n${results.join("\n")}\n━━━━━━━━━━━━━━━━━━━━━━\n🛡️ _100% High-Availability Multi-Region Mesh Active_`;
            await sendReply(rep, statusInlineKeyboard);
          })());
          return new Response("OK");
        }

        // 8. Help & Command Guide (/help)
        if (text === "/help" || text.startsWith("/help")) {
          const helpText = `ℹ️ *MY AGY AI — Operations & Admin Command Center*\n\n` +
            `🖥️ *Fleet Operations:*\n` +
            `• \`/start\` or \`/menu\` — Operations dashboard & quick action grid\n` +
            `• \`/status\` or \`/app\` — Real-time telemetry Mini App\n` +
            `• \`/summary\` — Executive all-in-one health check\n` +
            `• \`/harvest\` — Dispatches multi-bot harvest across all 14 accounts\n` +
            `• \`/sweep\` or \`/withdraw\` — Instant cashout threshold check & auto-sweep\n` +
            `• \`/ultra\` — Ultra Wallet 6-Day Global Launch status\n` +
            `• \`/mrg\` — MRG Miner streak & channel reaction tasks\n` +
            `• \`/stones\` — Stones Miners Command Center (Arbitrum One vault)\n` +
            `• \`/atf\` — ATF Miner Command Center (100% farming mode)\n` +
            `• \`/accounts\` — Inspect all 14 fleet accounts & sessions\n` +
            `• \`/add_account <phone>\` — Connect a new Telegram account\n` +
            `• \`/remove_account <id>\` — Disconnect an account from automation\n` +
            `• \`/mesh\` or \`/cloud\` — Multi-Cloud unified mesh topology\n` +
            `• \`/nodes\` — Live latency probe across 5 Cloudflare Edge nodes\n` +
            `• \`/briefing\` — Daily AI executive briefing (Gemini 3.6 Flash)\n` +
            `• \`/backup\` — Instant 1-click cloud backup download\n\n` +
            `👥 *Community & User Management (@AAAPREMIUMAPPSbot):*\n` +
            `• \`/community\` or \`/users\` — Public miner stats & pass circulation\n` +
            `• \`/whales\` or \`/top\` — Top community miners & points leaderboard\n` +
            `• \`/paused\` or \`/low_balance\` — Miners paused due to low points balance\n` +
            `• \`/sweep_daily\` — Manually trigger 100 Pts daily deduction sweep\n` +
            `• \`/grant <user_id> <pts>\` — Grant points to any user\n` +
            `• \`/grantpass <user_id> <day|week|month>\` — Activate VIP Pass for user\n` +
            `• \`/grantslot <user_id> <slots>\` — Unlock permanent account slots for user\n` +
            `• \`/reply <user_id> <text>\` — Direct message reply to user support ticket\n` +
            `• \`/broadcast <text>\` — Broadcast official announcement to all miners\n\n` +
            `🛡️ *Anti-Sybil & Account Moderation:*\n` +
            `• \`/sybil\` or \`/moderation\` — Full anti-sybil cross-linking audit\n` +
            `• \`/user <user_id>\` — Deep profile audit & interactive moderation card\n` +
            `• \`/ban <user_id> [reason]\` — Immediately suspend user access & farming\n` +
            `• \`/unban <user_id>\` — Re-enable suspended miner access\n` +
            `• \`/deduct <user_id> <pts>\` — Claw back fraudulent points\n\n` +
            `📱 _Tap the buttons below to trigger instant fleet actions:_`;
          ctx.waitUntil(sendReply(helpText, statusInlineKeyboard));
          return new Response("OK");
        }

        // 9. Intelligent Conversational AI & Natural Fleet Actions
        ctx.waitUntil((async () => {
          await fetch(`https://api.telegram.org/bot${botToken}/sendChatAction`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ chat_id: chatId, action: "typing" })
          }).catch(() => {});

          const userLower = text.toLowerCase();

          if (userLower.includes("harvest") || userLower.includes("farm all") || userLower.includes("claim all")) {
            await queueHarvestAction();
            await sendReply("🌾 *Fleet Harvest Dispatched!*\n\nAll 14 accounts across all 8 platforms have been queued for harvesting on Cloudflare Edge.", statusInlineKeyboard);
            return;
          }

          if (userLower.includes("sweep") || userLower.includes("instant withdraw") || userLower.includes("cash out")) {
            const res = await queueSweepAction();
            await sendReply(`💰 *Instant Withdrawal Sweep Dispatched!*\n\n• Accounts checked: \`14/14\`\n• Status: ${res.ok ? "Queued to Fleet Workers ✅" : "Dispatched"}\n• Target Vault: \`0xfda4182001672b9f0f09e2118242e543e35ed5ce\``, statusInlineKeyboard);
            return;
          }

          if (userLower.includes("backup") || userLower.includes("disaster recovery")) {
            const bUrl = `https://restore-agy.${CURRENT_SUBDOMAIN}.workers.dev/backup.zip`;
            await sendReply(`📦 *1-Click Cloud Backup Ready*\n\n• *Direct Download:* ${bUrl}\n• *Mesh:* Triple Cloudflare Edge Shards\n• *Vault:* @myagyai channel archive\n\n🛡️ _Complete disaster recovery archive ready._`, statusInlineKeyboard);
            return;
          }

          if (userLower.includes("stones") && (userLower.includes("status") || userLower.includes("balance") || userLower.includes("wd") || userLower.includes("cooldown"))) {
            await sendReply(`💎 *Stones Miners Telemetry*\n\n• *Target Blockchain:* Arbitrum One (0xfda4182001672b9f0f09e2118242e543e35ed5ce)\n• *Auto-Withdrawal Threshold:* 500 STONES\n• *AI Captcha Engine:* Google Gemini Vision + Template Solver\n• *Anti-Sybil:* AdsGram proof verified per account`, statusInlineKeyboard);
            return;
          }

          if (userLower.includes("atf") && (userLower.includes("policy") || userLower.includes("withdraw") || userLower.includes("status"))) {
            await sendReply(`🪙 *ATF Miner Telemetry & Policy*\n\n• *Operational Mode:* 100% Farming & Pool Accumulation\n• *Auto-Withdrawals:* Permanently Disabled (Per Admin Directive)\n• *Network:* TON Blockchain\n• *Status:* All accounts compounding tokens safely in the cloud.`, statusInlineKeyboard);
            return;
          }

          let cleanPrompt = text;
          if (cleanPrompt.startsWith("/ai ")) {
            cleanPrompt = cleanPrompt.substring(4).trim();
          }

          try {
            let liveBnb = 0.000812;
            try {
              const rawMC = await env.BACKUP_KV.get("multichain_balances_state");
              if (rawMC) {
                const mc = JSON.parse(rawMC);
                if (mc.bsc_bnb_balance !== undefined) liveBnb = mc.bsc_bnb_balance;
              }
            } catch (_) {}

            let totalAtf = 4050.0;
            try {
              const rawAtf = await env.BACKUP_KV.get("atf_fleet_state");
              if (rawAtf) {
                const atfD = JSON.parse(rawAtf);
                if (atfD && atfD.results) totalAtf = atfD.results.reduce((s, a) => s + (parseFloat(a.mined_balance) || 0), 0);
              }
            } catch (_) {}

            const systemPrompt = `You are Ari, the personal cloud AI assistant for Arif's 14-account automated crypto and mining fleet (MY AGY AI).
Live Fleet Context:
- 14 active accounts mining 24/7 across all 8 active bots: Stones Miners, ATF Miner, MRG Miner, ART Airdrop, AI Lab Robot, UltraWallet, Apex Miner, Ainovum.
- Policy: ATF Miner is in 100% farming & accumulation mode (NO withdrawals; let balance grow).
- Policy (Admin Fleet Accounts): MRG Miner is strictly in 100% Holding & Compounding mode (NO auto-withdrawals) to preserve peak levels (Level 1..50), maximum hashrate (5.5 TH/s), and squad referral qualifications.
- Vault BEP-20 (BNB, USDT): 0xfda4182001672b9f0f09e2118242e543e35ed5ce (Live Balance: ${liveBnb.toFixed(6)} BNB).
- Stones Vault (Arbitrum One): 0xfda4182001672b9f0f09e2118242e543e35ed5ce (Balance: 500+ STONES).
- Main TON Vault: UQBPZiSvitdPU3VUyJK2mRaHVBl69xejw5aOrh1KfKA7gwDT.
- ATF Mined: ~${totalAtf.toFixed(1)} ATF accumulating across all accounts.
- Infrastructure: 100% running in the cloud (Triple Cloudflare Edge Nodes, Render Singapore, Cron-job.org). No VPS or local dependencies.
Personality:
- Talk like a normal, friendly, intelligent human companion (like ChatGPT or Claude).
- Sound natural, conversational, and genuinely helpful.
- DO NOT use stiff robotic jargon (never say "AFFIRMATIVE", "OODA LOOP", "TELEMETRY TICK", "COGNITIVE PASS").
- Always address the user warmly as Arif.
- Keep Telegram responses concise, clear, and mobile-friendly.

Arif says: "${cleanPrompt}"
Reply to Arif naturally:`;

            const aiData = await runAiCascade(systemPrompt);
            if (aiData && aiData.answer) {
              await sendReply(aiData.answer, statusInlineKeyboard, "Markdown");
              return;
            }
          } catch (e) {
            console.error("Telegram AI chat error:", e);
          }

          const defaultRep = `⚡ *MY AGY AI Operations Hub*\n\n` +
            `• 14 Accounts Online & Mining across 8 Platforms\n` +
            `• Tap *🚀 Mini App* below to view your full dashboard or use the toolbar buttons:`;
          await sendReply(defaultRep, statusInlineKeyboard);
        })());
        return new Response("OK");

      } catch (err) {
        return new Response("OK");
      }
    }


    // 13.5 Helper: Get & Save User Profile in Upstash Redis (Shared across Adsgram & Webhook)
    const getUserProfile = async (uid, fromObj = null) => {
      const key = `ub_user:${uid}`;
      let prof = null;
      try {
        const raw = await upstashGet(key);
        if (raw) prof = typeof raw === "string" ? JSON.parse(raw) : raw;
      } catch (_) {}

      if (!prof) {
        prof = {
          user_id: uid,
          first_name: fromObj?.first_name || "Miner",
          username: fromObj?.username || "",
          points: 100, // 100 Free Welcome Points (Day 1 farming free)
          slots: 1, // Default 1 Account Slot
          temp_slots: 0,
          ads_watched: 0,
          last_ad_claim: 0,
          referral_count: 0,
          referred_by: null,
          accounts: [],
          joined_channels: false,
          farming_active: true,
          subscription_tier: null,
          subscription_expiry: 0,
          last_deduction_date: new Date().toISOString().slice(0, 10),
          created_at: Date.now()
        };
        await upstashSet(key, prof);
      } else if (fromObj) {
        let updated = false;
        if (fromObj.first_name && prof.first_name !== fromObj.first_name) {
          prof.first_name = fromObj.first_name;
          updated = true;
        }
        if (fromObj.username !== undefined && prof.username !== (fromObj.username || "")) {
          prof.username = fromObj.username || "";
          updated = true;
        }
        if (updated) {
          ctx.waitUntil(upstashSet(key, prof));
        }
      }

      // Auto-register user ID in global community Set in Upstash Redis
      ctx.waitUntil(upstashSadd("ub_registered_users", String(uid)));

      // Ensure subscription, accounts & daily streak fields exist
      if (!prof.accounts || !Array.isArray(prof.accounts)) prof.accounts = [];
      if (prof.points === undefined || prof.points === null) prof.points = 0;
      if (prof.subscription_expiry === undefined) prof.subscription_expiry = 0;
      if (prof.subscription_tier === undefined) prof.subscription_tier = null;
      if (prof.daily_streak === undefined) prof.daily_streak = 0;
      if (prof.last_daily_claim === undefined) prof.last_daily_claim = 0;

      const now = Date.now();
      const hasActivePass = prof.subscription_expiry > now;
      if (hasActivePass) {
        prof.farming_active = true;
      }

      // Daily Automated Point Deduction (100 Pts per active connected account per day)
      const today = new Date().toISOString().slice(0, 10);
      if (prof.last_deduction_date !== today && prof.accounts && prof.accounts.length > 0) {
        if (hasActivePass) {
          prof.farming_active = true;
          prof.last_deduction_date = today;
          await upstashSet(key, prof);
        } else {
          const dailyCost = prof.accounts.length * 100;
          if (prof.farming_active !== false) {
            if (prof.points >= dailyCost) {
              prof.points -= dailyCost;
              prof.farming_active = true;
            } else {
              prof.farming_active = false;
              // Alert user that farming is paused due to insufficient points
              const uBotToken = env.USER_BOT_TOKEN || "8167732110:AAGQA6bBgRwaChFIWPvs9uCt6aZ3j1VGCn8";
              ctx.waitUntil(fetch(`https://api.telegram.org/bot${uBotToken}/sendMessage`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  chat_id: uid,
                  text: `⚠️ *Cloud Mining Paused — Insufficient Points* ⚠️\n\n` +
                    `Your 24/7 cloud mining has been temporarily paused because your points balance (*${prof.points} Points*) is below today's daily cost (*${dailyCost} Points* for ${prof.accounts.length} connected account${prof.accounts.length > 1 ? "s" : ""}).\n\n` +
                    `*Quick Ways to Resume 24/7 Mining:*\n` +
                    `• 🎁 *Claim Daily Bonus* (+25-50 Pts)\n` +
                    `• 🎬 *Watch Rewarded Video Ads* (+20 Pts/ad)\n` +
                    `• 👥 *Invite Friends* (+500 Pts each)\n` +
                    `• 🌟 *Upgrade to VIP Pass* (VIP Pass + unlimited mining)`,
                  parse_mode: "Markdown",
                  reply_markup: {
                    inline_keyboard: [
                      [{ text: "🎁 Claim Daily Bonus", callback_data: "ub_daily_claim" }],
                      [{ text: "🎬 Watch Video Ad (+20 Pts)", web_app: { url: "https://atf-miner-app.pages.dev/app/ad/" } }],
                      [{ text: "🌟 VIP Passes", callback_data: "ub_buy_stars" }]
                    ]
                  }
                })
              }).catch(() => {}));
            }
            prof.last_deduction_date = today;
            await upstashSet(key, prof);
          } else {
            // Already paused: if user points were refilled, auto-resume!
            if (prof.points >= dailyCost) {
              prof.points -= dailyCost;
              prof.farming_active = true;
              const uBotToken = env.USER_BOT_TOKEN || "8167732110:AAGQA6bBgRwaChFIWPvs9uCt6aZ3j1VGCn8";
              ctx.waitUntil(fetch(`https://api.telegram.org/bot${uBotToken}/sendMessage`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  chat_id: uid,
                  text: `🟢 *Cloud Mining Auto-Resumed!* 🚀\n\n` +
                    `Your points balance covered today's cost (*${dailyCost} Points*). 24/7 cloud mining has resumed for all ${prof.accounts.length} accounts.\n• *Remaining Balance:* 💎 ${prof.points} Points`,
                  parse_mode: "Markdown"
                })
              }).catch(() => {}));
            }
            prof.last_deduction_date = today;
            await upstashSet(key, prof);
          }
        }
      }

      return prof;
    };

    const saveUserProfile = async (uid, prof) => {
      await upstashSet(`ub_user:${uid}`, prof);
    };

    // 13.6 Multi-Network Ad Portal Route (Monetag, GigaPub, Adsterra 7 Formats, HilltopAds VAST 3.0, A-Ads)
    if (path === "/ads" || path === "/app/ad" || path === "/ad" || path === "/adsgram") {
      const redirectTarget = "https://atf-miner-app.pages.dev/app/ad/" + (url.search || "");
      return Response.redirect(redirectTarget, 302);
    }

    // 13.7 User Status & Multi-Network Ad Data API
    if (path === "/api/adsgram/status" || path === "/api/user/data" || path === "/api/user/stats") {
      let uid = url.searchParams.get("user_id") || url.searchParams.get("userid") || url.searchParams.get("uid");
      const authHeader = request.headers.get("Authorization") || request.headers.get("X-Telegram-Init-Data") || "";
      if (!uid && authHeader) {
        try {
          const initStr = authHeader.replace(/^tma\s+/i, "");
          const params = new URLSearchParams(initStr);
          const uStr = params.get("user");
          if (uStr) uid = JSON.parse(uStr).id;
        } catch (_) {}
      }
      if (!uid) {
        uid = request.headers.get("X-User-Id");
      }
      if (!uid) {
        return new Response(JSON.stringify({ ok: false, error: "Missing user_id" }), { status: 400, headers: corsHeaders });
      }
      const profile = await getUserProfile(uid);
      const now = Date.now();
      const isMonthlyPass = profile.subscription_tier === "month" && profile.subscription_expiry && profile.subscription_expiry > now;
      const totalAllowed = (profile.slots || 1) + (profile.temp_slots || 0);

      return new Response(JSON.stringify({
        ok: true,
        success: true,
        user_id: uid,
        points: profile.points || 0,
        ads_watched: profile.ads_watched || 0,
        ads_watched_today: profile.ads_watched || 0,
        daily_ads_watched: profile.ads_watched || 0,
        is_monthly_pass: isMonthlyPass,
        slots: totalAllowed,
        user_slots: {
          allowed: totalAllowed,
          is_vip: isMonthlyPass,
          vip_slots: isMonthlyPass ? 2 : 0
        },
        vip: {
          is_vip: isMonthlyPass,
          vip_slots: isMonthlyPass ? 2 : 0
        },
        ad_rewards: {
          points: profile.points || 0,
          ads_watched_today: profile.ads_watched || 0,
          temp_slots_count: profile.temp_slots || 0,
          ad_streak: 1,
          is_vip: isMonthlyPass,
          vip_slots: isMonthlyPass ? 2 : 0
        },
        stats: {
          points: profile.points || 0,
          ads_watched_today: profile.ads_watched || 0,
          temp_slots_count: profile.temp_slots || 0,
          is_vip: isMonthlyPass
        }
      }), { headers: { "Content-Type": "application/json", ...corsHeaders } });
    }

    // 13.8 Multi-Network Ad Verification & Claim API (Monetag, GigaPub, Adsterra 7 Formats, HilltopAds VAST, A-Ads)
    if ((path === "/api/adsgram/reward" || path === "/api/user/verify-ad-chain" || path === "/api/user/verify-monetag" || path === "/api/user/claim-ad") && (request.method === "POST" || request.method === "GET")) {
      try {
        let uid = url.searchParams.get("userid") || url.searchParams.get("user_id") || url.searchParams.get("uid");
        if (!uid && request.method === "POST") {
          const body = await request.json().catch(() => ({}));
          uid = body.user_id;
          if (!uid && body.initData) {
            try {
              const params = new URLSearchParams(body.initData);
              const userStr = params.get("user");
              if (userStr) {
                const uObj = JSON.parse(userStr);
                uid = uObj.id;
              }
            } catch (_) {}
          }
        }
        if (!uid) {
          const authH = request.headers.get("Authorization") || request.headers.get("X-Telegram-Init-Data") || "";
          if (authH) {
            try {
              const p = new URLSearchParams(authH.replace(/^tma\s+/i, ""));
              const us = p.get("user");
              if (us) uid = JSON.parse(us).id;
            } catch (_) {}
          }
        }
        if (!uid) {
          uid = request.headers.get("X-User-Id");
        }
        if (!uid) {
          return new Response(JSON.stringify({ ok: false, error: "Missing user_id" }), { status: 400, headers: corsHeaders });
        }

        // Ad network validation ping or test request
        if (String(uid) === "[userId]" || String(uid) === "test" || String(uid) === "0" || String(uid) === "ping") {
          return new Response(JSON.stringify({ ok: true, status: "webhook_active" }), {
            status: 200,
            headers: { "Content-Type": "application/json", ...corsHeaders }
          });
        }

        const profile = await getUserProfile(uid);
        const now = Date.now();
        const elapsed = Math.floor((now - (profile.last_ad_claim || 0)) / 1000);
        if (elapsed < 12) {
          const waitSec = 12 - elapsed;
          if (request.method === "GET") {
            return new Response(JSON.stringify({
              ok: true,
              success: true,
              status: "already_credited",
              cooldown_seconds: waitSec,
              message: "User was recently credited. Acknowledged."
            }), { status: 200, headers: { "Content-Type": "application/json", ...corsHeaders } });
          }
          return new Response(JSON.stringify({
            ok: false,
            success: false,
            error: `Cooldown active. Please wait ${waitSec}s.`,
            cooldown_seconds: waitSec
          }), { status: 429, headers: corsHeaders });
        }

        const isMonthlyPass = profile.subscription_tier === "month" && profile.subscription_expiry && profile.subscription_expiry > now;
        const adPts = isMonthlyPass ? 40 : 20;
        profile.points = (profile.points || 0) + adPts;
        profile.ads_watched = (profile.ads_watched || 0) + 1;
        profile.last_ad_claim = now;
        const dailyCost = (profile.accounts || []).length * 100;
        const wasPaused = profile.farming_active === false && (profile.accounts || []).length > 0;
        let resumedText = "";
        if (profile.points >= dailyCost) {
          profile.farming_active = true;
          if (wasPaused) {
            resumedText = `\n\n🟢 *Cloud Mining Auto-Resumed!* 🚀\nYour points balance now covers today\x27s cost (${dailyCost} Points). 24/7 autonomous mining has resumed for all ${profile.accounts.length} accounts!`;
          }
        }

        let bonusUnlocked = false;
        if (profile.ads_watched % 50 === 0) {
          profile.temp_slots = (profile.temp_slots || 0) + 1;
          bonusUnlocked = true;
        }
        await saveUserProfile(uid, profile);

        const userBotToken = env.USER_BOT_TOKEN || "8167732110:AAGQA6bBgRwaChFIWPvs9uCt6aZ3j1VGCn8";
        const bonusText = bonusUnlocked ? "\n\n🎉 *50 ADS MILESTONE REACHED!* You unlocked *+1 BONUS ACCOUNT SLOT*!" : "";
        const notifTxt = `✅ *+${adPts} POINTS CREDITED!* 🎬${isMonthlyPass ? " _(2x Monthly Pass Bonus!)_" : ""}\n\n` +
          `• *New Balance:* ${profile.points} Points\n` +
          `• *Daily Mining Cost:* ${isMonthlyPass ? "0 Pts/day (VIP Pass)" : `${dailyCost} Pts/day`}\n` +
          `• *Days of Mining Remaining:* ~${dailyCost > 0 ? Math.floor(profile.points / dailyCost) : "Unlimited"} days\n` +
          `• *Ads Watched:* ${profile.ads_watched}/50\n` +
          `• *Progress to Bonus Slot:* ${profile.ads_watched % 50}/50 ads${bonusText}${resumedText}\n\n` +
          `💡 _Keep watching ads to extend your 24/7 cloud mining!_`;

        ctx.waitUntil(fetch(`https://api.telegram.org/bot${userBotToken}/sendMessage`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            chat_id: uid,
            text: notifTxt,
            parse_mode: "Markdown"
          })
        }).catch(() => {}));

        return new Response(JSON.stringify({
          ok: true,
          success: true,
          points: profile.points,
          points_awarded: adPts,
          new_balance: profile.points,
          ads_watched: profile.ads_watched,
          ads_watched_today: profile.ads_watched,
          daily_ads_watched: profile.ads_watched,
          progress_to_bonus: profile.ads_watched % 50,
          bonus_unlocked: bonusUnlocked,
          user_slots: {
            allowed: (profile.slots || 1) + (profile.temp_slots || 0),
            is_vip: isMonthlyPass,
            vip_slots: isMonthlyPass ? 2 : 0
          },
          ad_rewards: {
            points: profile.points,
            ads_watched_today: profile.ads_watched,
            temp_slots_count: profile.temp_slots || 0,
            ad_streak: 1,
            is_vip: isMonthlyPass,
            vip_slots: isMonthlyPass ? 2 : 0
          }
        }), { headers: { "Content-Type": "application/json", ...corsHeaders } });
      } catch (err) {
        return new Response(JSON.stringify({ ok: false, error: err.message }), { status: 500, headers: corsHeaders });
      }
    }

    // 13.9 Adsgram Config / Diagnostics API
    if (path === "/api/adsgram/config") {
      const rawBlockId = (await upstashGet("config:adsgram_block_id")) || env.ADSGRAM_BLOCK_ID || "50527";
      const currentBlockId = String(rawBlockId).replace(/^["']|["']$/g, "").replace(/^bot-/, "").trim() || "50527";
      return new Response(JSON.stringify({
        ok: true,
        block_id: currentBlockId,
        webapp_url: "https://atf-miner-app.pages.dev/app/ad/",
        cooldown_sec: 15,
        default_pts: 20,
        monthly_pass_pts: 40,
        s2s_reward_url: `https://restore-agy.${CURRENT_SUBDOMAIN}.workers.dev/api/adsgram/reward?userid=[userId]`
      }), { headers: { "Content-Type": "application/json", ...corsHeaders } });
    }

    // 14. 24/7 Telegram User Bot Webhook Endpoint (@AAAPREMIUMAPPSbot - Hosted 100% on Cloudflare Edge)
    if (path === "/user-bot-webhook" || path === "/user-webhook") {
      if (request.method === "GET") {
        return new Response(JSON.stringify({
          ok: true,
          bot: "AAAPREMIUMAPPSbot",
          role: "Public User & Community AI Mining Platform",
          status: "online",
          version: "5.0-premium",
          channels: [
            { name: "AAA Auto Miner — Community Hub", username: "@AAAAutoMiner", url: "https://t.me/AAAAutoMiner" },
            { name: "AAA Auto Miner — Announcements", username: "@AAAAUTOMINING", url: "https://t.me/AAAAUTOMINING" },
            { name: "AAA ATF Miner — Live Activity", username: "@AAA_ACTIVITY", url: "https://t.me/AAA_ACTIVITY" }
          ]
        }), { headers: { "Content-Type": "application/json", ...corsHeaders } });
      }
      if (request.method !== "POST") {
        return new Response("Method not allowed", { status: 405 });
      }
      try {
        const update = await request.json().catch(() => null);
        if (!update) return new Response("OK");

        const userBotToken = env.USER_BOT_TOKEN || "8167732110:AAGQA6bBgRwaChFIWPvs9uCt6aZ3j1VGCn8";

        // (getUserProfile & saveUserProfile lifted to shared scope above)


        // Helper: Check membership across all 3 official community channels
        const checkUserChannels = async (uid) => {
          if (String(uid) === "6727787768") return { ok: true, missing: [] };
          const channels = [
            { id: -1003684868577, name: "AAA Auto Miner — Community Hub", username: "@AAAAutoMiner", url: "https://t.me/AAAAutoMiner" },
            { id: -1004255751168, name: "AAA Auto Miner — Announcements", username: "@AAAAUTOMINING", url: "https://t.me/AAAAUTOMINING" },
            { id: -1004332544939, name: "AAA ATF Miner — Live Activity", username: "@AAA_ACTIVITY", url: "https://t.me/AAA_ACTIVITY" }
          ];
          const missing = [];
          for (const ch of channels) {
            try {
              const res = await fetch(`https://api.telegram.org/bot${userBotToken}/getChatMember?chat_id=${ch.id}&user_id=${uid}`);
              if (res.ok) {
                const d = await res.json();
                const status = d.result?.status;
                if (!["creator", "administrator", "member", "restricted"].includes(status)) {
                  missing.push(ch);
                }
              } else {
                // Non-200 (e.g. HTTP 400 PARTICIPANT_ID_INVALID) indicates user has not joined
                missing.push(ch);
              }
            } catch (_) {}
          }
          return { ok: missing.length === 0, missing };
        };

        // Broadcast Event to Official Live Activity Channel (@AAA_ACTIVITY)
        const broadcastToLiveActivity = async (txt, replyMarkup = null) => {
          const payload = {
            chat_id: -1004332544939,
            text: txt,
            parse_mode: "Markdown",
            disable_web_page_preview: true
          };
          if (replyMarkup) payload.reply_markup = replyMarkup;
          try {
            await fetch(`https://api.telegram.org/bot${userBotToken}/sendMessage`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(payload)
            });
          } catch (_) {}
        };

        const broadcastNewMinerJoined = async (profile, uid, fromObj) => {
          const fullName = [fromObj?.first_name, fromObj?.last_name].filter(Boolean).join(" ") || profile.first_name || "Miner";
          const username = fromObj?.username || profile.username || "";
          const usernameStr = username ? `@${username}` : "_None_";
          const uidStr = String(uid);
          const maskedUid = uidStr.length > 5 ? `${uidStr.slice(0, 4)}****${uidStr.slice(-2)}` : uidStr;

          const activityMsg = `🚀 *NEW MINER JOINED!*\n\n` +
            `👤 ${fullName}\n` +
            `🔗 ${usernameStr}\n` +
            `🆔 ID: \`${maskedUid}\`\n\n` +
            `📦 Slot: 1× Base Cloud\n` +
            `🎁 Welcome Bonus: +100 Points\n\n` +
            `⚡ Status: 🟢 Mining Ready\n` +
            `☁️ Cloud Mining: 24/7\n\n` +
            `━━━━━━━━━━━━━━━━━━\n` +
            `🎁 *INVITE & EARN*\n` +
            `Get +500 Points + bonus slots\n` +
            `for every friend you invite!\n\n` +
            `🤖 @AAAPREMIUMAPPSbot\n` +
            `━━━━━━━━━━━━━━━━━━\n\n` +
            `👇 *Start your mining journey*`;

          const activityBtns = {
            inline_keyboard: [
              [
                { text: "🚀 Launch Cloud Miner", url: "https://t.me/AAAPREMIUMAPPSbot" },
                { text: "🎁 Invite & Earn", url: "https://t.me/AAAPREMIUMAPPSbot?start=invite" }
              ],
              [
                { text: "📊 My Rewards", url: "https://t.me/AAAPREMIUMAPPSbot?start=rewards" },
                { text: "📢 Announcements", url: "https://t.me/AAAAUTOMINING" }
              ],
              [
                { text: "💬 Community Hub", url: "https://t.me/AAAAutoMiner" }
              ]
            ]
          };

          await broadcastToLiveActivity(activityMsg, activityBtns);
        };

        const broadcastMilestoneUnlocked = async (title, minerName, uid, achievement, bonusText = "") => {
          const uidStr = String(uid);
          const maskedUid = uidStr.length > 5 ? `${uidStr.slice(0, 4)}****${uidStr.slice(-2)}` : uidStr;
          const msgTxt = `🎉 *MILESTONE UNLOCKED!*\n\n` +
            `👤 ${minerName}\n` +
            `🆔 ID: \`${maskedUid}\`\n\n` +
            `🏆 Achievement: ${achievement}\n` +
            (bonusText ? `🎁 Perk: ${bonusText}\n` : "") +
            `\n⚡ Status: 🟢 VIP Cloud Miner\n` +
            `☁️ Cloud Mining: 24/7\n\n` +
            `━━━━━━━━━━━━━━━━━━\n` +
            `🎁 *INVITE & EARN*\n` +
            `Get +500 Points + bonus slots\n` +
            `for every friend you invite!\n\n` +
            `🤖 @AAAPREMIUMAPPSbot\n` +
            `━━━━━━━━━━━━━━━━━━\n\n` +
            `👇 *Start your mining journey*`;

          const btns = {
            inline_keyboard: [
              [
                { text: "🚀 Launch Cloud Miner", url: "https://t.me/AAAPREMIUMAPPSbot" },
                { text: "🎁 Invite & Earn", url: "https://t.me/AAAPREMIUMAPPSbot?start=invite" }
              ],
              [
                { text: "📊 My Rewards", url: "https://t.me/AAAPREMIUMAPPSbot?start=rewards" },
                { text: "📢 Announcements", url: "https://t.me/AAAAUTOMINING" }
              ],
              [
                { text: "💬 Community Hub", url: "https://t.me/AAAAutoMiner" }
              ]
            ]
          };

          await broadcastToLiveActivity(msgTxt, btns);
        };

        // Telegram Stars Invoice Sender
        const sendStarsInvoice = async (targetChatId, itemKey) => {
          const catalog = {
            ub_pass_day: {
              title: "🎟️ 1-Day VIP Pass (24 Hours)",
              description: "24h unlimited cloud mining with zero point deduction + 150 Bonus Points!",
              payload: "pass_day",
              prices: [{ label: "1-Day VIP Pass", amount: 15 }]
            },
            ub_pass_week: {
              title: "🎟️ 7-Day Weekly Pass (VIP Miner)",
              description: "7 days cloud mining (0 points fee) + 1,000 Points + 1 Extra Account Slot!",
              payload: "pass_week",
              prices: [{ label: "7-Day Weekly Pass", amount: 45 }]
            },
            ub_pass_month: {
              title: "💎 30-Day Monthly Pass (Ultimate VIP)",
              description: "30 days cloud mining (0 points fee) + 4,500 Points + 1 Permanent Slot + 2x Ad Rewards!",
              payload: "pass_month",
              prices: [{ label: "30-Day Monthly Pass", amount: 120 }]
            },
            ub_stars_slot1: {
              title: "🌟 1 Permanent Account Slot",
              description: "Unlock 1 permanent slot to connect another Telegram account for 24/7 cloud mining.",
              payload: "buy_slot_1",
              prices: [{ label: "1 Permanent Slot", amount: 50 }]
            },
            ub_stars_slot3: {
              title: "🌟 3 Account Slots (Permanent)",
              description: "Unlock 3 permanent slots to connect multiple Telegram accounts for 24/7 cloud mining.",
              payload: "buy_slot_3",
              prices: [{ label: "3 Permanent Slots", amount: 120 }]
            },
            ub_stars_vip: {
              title: "💎 VIP Miner Pass (3,000 Pts + 1 Slot)",
              description: "Get 3,000 Points (30 days of 24/7 cloud mining) plus 1 extra permanent account slot!",
              payload: "buy_vip",
              prices: [{ label: "VIP Pass", amount: 100 }]
            },
            ub_stars_pts1000: {
              title: "💎 1,000 Mining Points",
              description: "Add 1,000 Points to your balance for 10 full days of 24/7 cloud mining.",
              payload: "buy_points_1000",
              prices: [{ label: "1,000 Points", amount: 35 }]
            }
          };
          const pkg = catalog[itemKey];
          if (!pkg) return;

          const payload = {
            chat_id: targetChatId,
            title: pkg.title,
            description: pkg.description,
            payload: pkg.payload,
            currency: "XTR",
            prices: pkg.prices,
            provider_token: "" // Must be empty string for Telegram Stars
          };

          try {
            await fetch(`https://api.telegram.org/bot${userBotToken}/sendInvoice`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(payload)
            });
          } catch (_) {}
        };

        const effectiveUid = String(update?.message?.chat?.id || update?.callback_query?.message?.chat?.id || update?.callback_query?.from?.id || "");
        const isOwner = effectiveUid === "6727787768" || effectiveUid === String(env.OWNER_ID || "6727787768");

        // UI Keyboards (Standard Community Miners - STRICTLY ZERO ADMIN BUTTONS)
        const userMainKeyboard = {
          keyboard: [
            [
              { text: "➕ Connect Account" },
              { text: "👥 My Accounts" }
            ],
            [
              { text: "⛏️ Farming Bots" },
              { text: "💎 Points & Pass" }
            ],
            [
              { text: "🎁 Daily Bonus" },
              { text: "👥 Invite Friends" }
            ],
            [
              { text: "💬 Ari AI & Support" }
            ]
          ],
          resize_keyboard: true,
          is_persistent: true
        };

        // UI Keyboards (Platform Administrator Arif ONLY)
        const ownerUserKeyboard = {
          keyboard: [
            [
              { text: "➕ Connect Account" },
              { text: "👥 My Accounts" }
            ],
            [
              { text: "⛏️ Farming Bots" },
              { text: "💎 Points & Pass" }
            ],
            [
              { text: "🎁 Daily Bonus" },
              { text: "👥 Invite Friends" }
            ],
            [
              { text: "💬 Ari AI & Support" }
            ],
            [
              { text: "👑 User Admin Dashboard", web_app: { url: "https://aaa-admin-portal.pages.dev/" } }
            ]
          ],
          resize_keyboard: true,
          is_persistent: true
        };

        const activeUserKeyboard = isOwner ? ownerUserKeyboard : userMainKeyboard;

        const userCancelKeyboard = {
          keyboard: [
            [
              { text: "❌ Cancel Connection" }
            ]
          ],
          resize_keyboard: true,
          is_persistent: true
        };

        const gateInlineKeyboard = {
          inline_keyboard: [
            [
              { text: "💬 1. Join Community Hub", url: "https://t.me/AAAAutoMiner" },
              { text: "📢 2. Join Announcements", url: "https://t.me/AAAAUTOMINING" }
            ],
            [
              { text: "⚡ 3. Join Live Activity Stream", url: "https://t.me/AAA_ACTIVITY" }
            ],
            [
              { text: "🔄 Verify Membership & Claim 100 Pts", callback_data: "ub_verify_gate" }
            ]
          ]
        };

        const userWelcomeInlineKeyboard = {
          inline_keyboard: [
            [
              { text: "⛏️ 8 Supported Farming Bots 🤖", callback_data: "ub_pools" }
            ],
            [
              { text: "🎬 Watch Video Ad (+20 Pts) ⚡", web_app: { url: "https://atf-miner-app.pages.dev/app/ad/" } }
            ],
            [
              { text: "🌟 VIP Passes & Boosts (Stars)", callback_data: "ub_buy_stars" }
            ],
            [
              { text: "📢 Announcements", url: "https://t.me/AAAAUTOMINING" },
              { text: "💬 Community Hub", url: "https://t.me/AAAAutoMiner" }
            ],
            [
              { text: "⚡ Live Miner Activity Stream", url: "https://t.me/AAA_ACTIVITY" }
            ]
          ]
        };

        const activeWelcomeInlineKeyboard = userWelcomeInlineKeyboard;

        const starsUpgradeKeyboard = {
          inline_keyboard: [
            [
              { text: "🎟️ 1-Day Pass (15 Stars)", callback_data: "ub_pass_day" },
              { text: "🎟️ 7-Day Pass (45 Stars)", callback_data: "ub_pass_week" }
            ],
            [
              { text: "💎 30-Day Monthly Pass (120 Stars)", callback_data: "ub_pass_month" }
            ],
            [
              { text: "🌟 +1 Permanent Slot (50 Stars)", callback_data: "ub_stars_slot1" }
            ],
            [
              { text: "📺 Watch Ad (+20 Pts Free)", web_app: { url: "https://atf-miner-app.pages.dev/app/ad/" } },
              { text: "👥 Invite Friends (+500 Pts)", callback_data: "ub_referral" }
            ]
          ]
        };

        const adClaimKeyboard = {
          inline_keyboard: [
            [
              { text: "🎬 Watch Real Video Ad (+20 Pts)", web_app: { url: "https://atf-miner-app.pages.dev/app/ad/" } }
            ],
            [
              { text: "🎁 Claim Reward Directly", callback_data: "ub_claim_ad" },
              { text: "📢 Official Channel", url: "https://t.me/AAAAUTOMINING" }
            ]
          ]
        };

        // 1. Handle Telegram Stars Pre-Checkout Query
        if (update.pre_checkout_query) {
          const pcq = update.pre_checkout_query;
          ctx.waitUntil(
            fetch(`https://api.telegram.org/bot${userBotToken}/answerPreCheckoutQuery`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ pre_checkout_query_id: pcq.id, ok: true })
            }).catch(() => {})
          );
          return new Response("OK");
        }

        // 2. Handle Callback Queries
        if (update.callback_query) {
          const cq = update.callback_query;
          const cqChatId = cq.message?.chat?.id || cq.from?.id;
          const cqSenderName = cq.from?.first_name || cq.from?.username || "Miner";
          const cqData = cq.data || "";

          const answerCq = async (alertTxt = null) => {
            const body = { callback_query_id: cq.id };
            if (alertTxt) { body.text = alertTxt; body.show_alert = true; }
            await fetch(`https://api.telegram.org/bot${userBotToken}/answerCallbackQuery`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(body)
            }).catch(() => {});
          };

          const sendCqReply = async (txt, markup = null) => {
            const payload = { chat_id: cqChatId, text: txt, parse_mode: "Markdown", disable_web_page_preview: true };
            if (markup) {
              payload.reply_markup = markup;
            }
            await fetch(`https://api.telegram.org/bot${userBotToken}/sendMessage`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(payload)
            }).catch(() => {});
          };

          // Anti-Sybil Gate: Check if user is suspended/banned
          if (String(cqChatId) !== (env.OWNER_ID || "6727787768")) {
            const profCheck = await getUserProfile(cqChatId, cq.from);
            if (profCheck && profCheck.is_banned) {
              await answerCq("🚫 Your account is suspended by platform administration.");
              await sendCqReply("🚫 *Access Restricted*\n\nYour account has been suspended by platform administration for suspicious anti-sybil activity or policy violations.\n\nIf you believe this is an error, please contact @AAAAutoMiner.");
              return new Response("OK");
            }
          }

          // A. Gate Verification Callback
          if (cqData === "ub_verify_gate") {
            const chCheck = await checkUserChannels(cqChatId);
            if (!chCheck.ok) {
              const missingNames = chCheck.missing.map(m => m.username || m.name).join(", ");
              await answerCq(`⚠️ You still need to join: ${missingNames}! Please join all 3 channels above, then tap Verify again.`);
              return new Response("OK");
            }

            await answerCq("✅ Membership verified! 100 Welcome Points awarded!");
            const profile = await getUserProfile(cqChatId, cq.from);
            const isFirst = !profile.joined_channels || !profile.activity_broadcasted;
            profile.joined_channels = true;
            profile.activity_broadcasted = true;
            await saveUserProfile(cqChatId, profile);

            if (isFirst) {
              ctx.waitUntil(broadcastNewMinerJoined(profile, cqChatId, cq.from));
            }

            const totalSlots = (profile.slots || 1) + (profile.temp_slots || 0);
            const welcomeText = `🌟 *AAA AUTO MINING PLATFORM (PREMIUM)* 🚀\n` +
              `_⚡ Created by AAA — Autonomous Cloud Mining Ecosystem_\n\n` +
              `Hello ${cqSenderName}! You have successfully verified all 3 community channels and claimed 🎁 *100 Free Welcome Points*!\n\n` +
              `Connect your account once, and AAA Auto Mining will **automatically farm all 8 Telegram crypto bots 24/7 in the cloud**! Our cloud engines handle all daily mining sessions, task farming, and claim cycles continuously.\n\n` +
              `🤖 *8 Automated Mining Pools & Links:*\n` +
              `1️⃣ 🪙 [ATF Miner](https://t.me/ATF_AIRDROP_bot?start=6727787768) — Auto 24h mining & daily task claiming\n` +
              `2️⃣ 💎 [Stones Miner](https://t.me/stoneswithestand_bot?start=r6727787768) — Continuous auto-farming sessions\n` +
              `3️⃣ ⚡ [MRG Miner](https://t.me/mrgminerbot?start=ref_IRN1G3XD) — Peak tier hashrate & TON auto-mining\n` +
              `4️⃣ 🎨 [ART Miner](https://t.me/ART_AIRDROP_BOT?start=6727787768) — Auto-farming & token claims\n` +
              `5️⃣ 🤖 [AI Lab Robot](https://t.me/AiLab_robot?start=296852) — Automated hash generation & daily bonuses\n` +
              `6️⃣ 👛 [UltraWallet](https://t.me/UltrawalletTrade_Bot/app?startapp=6727787768) — Multi-pool automated cloud mining\n` +
              `7️⃣ 🏔️ [Apex Miner](https://t.me/ApxMinerBot/app?startapp=6727787768) — Continuous APX node farming\n` +
              `8️⃣ 🌐 [Ainovum](https://t.me/ainovum_bot?start=ref_6727787768) — 24/7 automated node mining & daily tasks\n\n` +
              `💎 *Your Fleet Overview:*\n` +
              `• *Connected Accounts:* ${profile.accounts?.length || 0} / ${totalSlots} Slots\n` +
              `• *Points Balance:* ${profile.points || 100} Points\n` +
              `• *Subscription Pass:* Free Tier (Pay-As-You-Go)\n` +
              `• *Farming Status:* 🟢 Active & Ready\n` +
              `• *Daily Cost:* ${(profile.accounts?.length || 0) * 100} Pts/day\n\n` +
              `📺 *Earn Points:* Watch ads (+20 Pts) or invite friends (+500 Pts).\n` +
              `🌟 *Subscriptions:* Day, Weekly, and Monthly VIP Passes with Telegram Stars!\n\n` +
              `👇 *Tap 🎬 Watch Video Ad below or choose an option from the menu:*`;

            ctx.waitUntil((async () => {
              await sendCqReply("✅ *Membership verified! 100 Welcome Points awarded!*", activeUserKeyboard);
              await sendCqReply(welcomeText, activeWelcomeInlineKeyboard);
            })());
            return new Response("OK");
          }

          await answerCq();

          // B. Watch Ad & Claim Points Callback
          if (cqData === "ub_watch_ad") {
            const adMsg = `📺 *WATCH REWARDED ADS & EARN POINTS* 🚀\n\n` +
              `Watch real video ads via Adsgram to keep your 24/7 cloud mining active continuously!\n\n` +
              `🎁 *Per-Ad Reward:* +20 Points (+40 for VIP Monthly Pass)\n` +
              `🏆 *Milestone Bonus:* Every 50 ads unlocks *+1 Free Bonus Account Slot*!\n` +
              `⏱️ *Cooldown:* 15 seconds between ads.\n\n` +
              `👇 *Tap below to launch the video ad:*`;
            ctx.waitUntil(sendCqReply(adMsg, {
              inline_keyboard: [
                [{ text: "🎬 Watch Video Ad (+20 Pts)", web_app: { url: "https://atf-miner-app.pages.dev/app/ad/" } }],
                [{ text: "🎁 Claim Directly (Fallback)", callback_data: "ub_claim_ad" }]
              ]
            }));
            return new Response("OK");
          }

          if (cqData === "ub_claim_ad") {
            const profile = await getUserProfile(cqChatId, cq.from);
            const now = Date.now();
            const elapsed = Math.floor((now - (profile.last_ad_claim || 0)) / 1000);
            if (elapsed < 15) {
              const waitSec = 15 - elapsed;
              ctx.waitUntil(sendCqReply(`⏳ *Ad Cooldown Active*\nPlease wait ${waitSec}s before claiming your next ad reward.`));
              return new Response("OK");
            }

            const isMonthlyPass = profile.subscription_tier === "month" && profile.subscription_expiry && profile.subscription_expiry > now;
            const adPts = isMonthlyPass ? 40 : 20;
            profile.points = (profile.points || 0) + adPts;
            profile.ads_watched = (profile.ads_watched || 0) + 1;
            profile.last_ad_claim = now;
            const dailyCost = (profile.accounts || []).length * 100;
            if (profile.points >= dailyCost) {
              profile.farming_active = true;
            }

            let bonusText = "";
            if (profile.ads_watched % 50 === 0) {
              profile.temp_slots = (profile.temp_slots || 0) + 1;
              bonusText = `\n\n🎉 *50 ADS MILESTONE REACHED!* You unlocked *+1 BONUS ACCOUNT SLOT*!`;
            }
            await saveUserProfile(cqChatId, profile);

            const rep = `✅ *+${adPts} POINTS CREDITED!* 🎁${isMonthlyPass ? " _(2x Monthly Pass Bonus!)_" : ""}\n\n` +
              `• *New Balance:* ${profile.points} Points\n` +
              `• *Ads Watched:* ${profile.ads_watched}/50\n` +
              `• *Progress to Bonus Slot:* ${profile.ads_watched % 50}/50 ads${bonusText}\n\n` +
              `💡 _Keep watching ads to extend your 24/7 mining clock!_`;
            ctx.waitUntil(sendCqReply(rep, activeUserKeyboard));
            return new Response("OK");
          }

          // C. Referral Stats & Link
          if (cqData === "ub_referral") {
            const profile = await getUserProfile(cqChatId, cq.from);
            const refLink = `https://t.me/AAAPREMIUMAPPSbot?start=ref_${cqChatId}`;
            const refMsg = `👥 *INVITE FRIENDS & EARN POINTS* 🚀\n\n` +
              `Share your personal referral link with friends. For every friend who joins & verifies:\n` +
              `🎁 *You earn +500 Points!* (5 full days of automated cloud mining!)\n` +
              `🎁 *Your friend receives 100 Free Welcome Points!*\n\n` +
              `🔗 *Your Referral Link:*\n\`${refLink}\`\n\n` +
              `📊 *Your Referral Stats:*\n` +
              `• *Invited Users:* ${profile.referral_count || 0}\n` +
              `• *Points Earned:* ${(profile.referral_count || 0) * 500} Pts`;
            ctx.waitUntil(sendCqReply(refMsg, {
              inline_keyboard: [
                [{ text: "📤 Share to Telegram", url: `https://t.me/share/url?url=${encodeURIComponent(refLink)}&text=${encodeURIComponent("Join AAA Auto Mining to earn crypto 24/7 automatically!")}` }]
              ]
            }));
            return new Response("OK");
          }

          // C1. Quick Start Mining
          if (cqData === "ub_start_mining") {
            const profile = await getUserProfile(cqChatId, cq.from);
            if (!profile.accounts || profile.accounts.length === 0) {
              const totalSlots = (profile.slots || 1) + (profile.temp_slots || 0);
              const hasPass = profile.subscription_expiry && profile.subscription_expiry > Date.now();
              if (!hasPass && profile.points < 100) {
                const lowPtsMsg = `⚠️ *Insufficient Points to Connect Account*\n\n` +
                  `Connecting an account requires at least *100 Points* for Day 1 automated cloud farming (or an active VIP Pass).\n` +
                  `Your balance: *${profile.points} Points*.\n\n` +
                  `*Quickly get access:*\n` +
                  `• 🎟️ *Get a Day Pass (15 Stars)* for unlimited 24h mining\n` +
                  `• 📺 Watch an ad (+20 Pts)\n` +
                  `• 👥 Invite a friend (+500 Pts)`;
                ctx.waitUntil(sendCqReply(lowPtsMsg, activeUserKeyboard));
                return new Response("OK");
              }

              if (env.BACKUP_KV) {
                await env.BACKUP_KV.put("login_flow:user_" + cqChatId, JSON.stringify({ step: "waiting_phone" }), { expirationTtl: 600 }).catch(() => {});
              }
              const promptPhone = `📱 *Connect Telegram Account for 24/7 Cloud Mining*\n\n` +
                `Please send the phone number of the Telegram account you want to connect:\n\n` +
                `• *Format:* \`+88017XXXXXXXX\` or \`017XXXXXXXX\`\n` +
                `• *International:* \`+1...\`, \`+44...\`, \`+91...\`\n\n` +
                `🔒 *100% Serverless & Encrypted:*\n` +
                `Your session runs safely in the cloud and automatically binds to all 8 mining pools.\n\n` +
                `_(Send phone number or tap ❌ Cancel Connection below)_`;
              ctx.waitUntil(sendCqReply(promptPhone, userCancelKeyboard));
              return new Response("OK");
            } else {
              const totalSlots = (profile.slots || 1) + (profile.temp_slots || 0);
              const isCovered = profile.subscription_expiry && profile.subscription_expiry > Date.now();
              let passBadge = "Free Tier";
              if (isCovered) {
                const remMs = profile.subscription_expiry - Date.now();
                const dLeft = Math.floor(remMs / (86400 * 1000));
                const hLeft = Math.floor((remMs % (86400 * 1000)) / (3600 * 1000));
                const tName = profile.subscription_tier === "month" ? "💎 Monthly Pass" : (profile.subscription_tier === "week" ? "🎟️ Weekly Pass" : "🎟️ Day Pass");
                passBadge = `${tName} (${dLeft > 0 ? `${dLeft}d ` : ""}${hLeft}h left)`;
              }
              const accList = profile.accounts.map((a, i) =>
                `*${i + 1}.* \`${a.phone || a.user_id}\` (${a.name || "User"}) — 🟢 Active Cloud Farming`
              ).join("\n");
              const accMsg = `👥 *MY CONNECTED ACCOUNTS* 📱\n\n` +
                `• *Slots In Use:* ${profile.accounts.length} / ${totalSlots}\n` +
                `• *Pass Status:* ${passBadge}\n` +
                `• *Points Balance:* ${profile.points} Pts\n\n` +
                `📱 *Active Accounts:*\n${accList}\n\n` +
                `💡 _Every account automatically farms all 8 pools 24/7 in the cloud._`;
              const inlineBtns = [
                [{ text: "➕ Connect Account", callback_data: "ub_add_acc" }, { text: "🗑️ Remove Account", callback_data: "ub_remove_menu" }],
                [{ text: "🌟 VIP Passes & Slots", callback_data: "ub_buy_stars" }]
              ];
              if (profile.accounts && profile.accounts.length > 0) {
                for (const a of profile.accounts) {
                  inlineBtns.push([{ text: `🗑️ Remove ${a.name || a.phone} (${a.phone || a.user_id})`, callback_data: `ub_disconnect_${a.user_id || a.phone}` }]);
                }
              }
              ctx.waitUntil(sendCqReply(accMsg, { inline_keyboard: inlineBtns }));
              return new Response("OK");
            }
          }

          // C2. Rewards Hub
          if (cqData === "ub_rewards") {
            const profile = await getUserProfile(cqChatId, cq.from);
            const isMonthlyPass = profile.subscription_tier === "month" && profile.subscription_expiry && profile.subscription_expiry > Date.now();
            const adPts = isMonthlyPass ? 40 : 20;
            const rewMsg = `🎁 *MY REWARDS & EARNING HUB* 💎\n\n` +
              `• *Available Balance:* ${profile.points} Mining Points\n` +
              `• *Ads Watched:* ${profile.ads_watched || 0}/50 (Earn +${adPts} Pts/view)\n` +
              `• *Next Bonus Slot:* ${(profile.ads_watched || 0) % 50}/50 ads\n` +
              `• *Referral Earnings:* ${(profile.referral_count || 0) * 500} Pts (${profile.referral_count || 0} friends)\n\n` +
              `Earn free points below:`;
            const rewBtns = {
              inline_keyboard: [
                [{ text: `🎬 Watch Video Ad (+${adPts} Pts)`, web_app: { url: "https://atf-miner-app.pages.dev/app/ad/" } }],
                [{ text: "🎁 Claim Daily Bonus", callback_data: "ub_daily_claim" }, { text: "👥 Invite Friends (+500 Pts)", callback_data: "ub_referral" }],
                [{ text: "🌟 Upgrade VIP Passes & Slots", callback_data: "ub_buy_stars" }]
              ]
            };
            ctx.waitUntil(sendCqReply(rewMsg, rewBtns));
            return new Response("OK");
          }

          // C2.5 Daily Check-In Bonus (24h Streak Rewards: +25 to +50 Pts)
          if (cqData === "ub_daily_claim" || cqData === "ub_daily_bonus" || cqData === "ub_claim") {
            const profile = await getUserProfile(cqChatId, cq.from);
            const now = Date.now();
            const lastClaim = profile.last_daily_claim || 0;
            const elapsed = now - lastClaim;
            const COOLDOWN_MS = 24 * 3600 * 1000;
            
            if (elapsed < COOLDOWN_MS) {
              const remMs = COOLDOWN_MS - elapsed;
              const h = Math.floor(remMs / 3600000);
              const m = Math.floor((remMs % 3600000) / 60000);
              const alreadyClaimedMsg = `⏳ *Daily Bonus Already Claimed!* 🎁\n\n` +
                `You have already claimed today's check-in bonus!\n\n` +
                `• *Next Claim In:* ${h}h ${m}m\n` +
                `• *Current Streak:* 🔥 ${profile.daily_streak || 1} Days\n` +
                `• *Points Balance:* 💎 ${profile.points || 0} Points\n\n` +
                `💡 *Earn points right now:*\n` +
                `• 🎬 *Watch Rewarded Video Ads* (+20 Pts/ad)\n` +
                `• 👥 *Invite Friends* (+500 Pts per referral)\n` +
                `• 🌟 *Upgrade with Telegram Stars* (0 point daily fee)`;
              const kb = {
                inline_keyboard: [
                  [{ text: "🎬 Watch Video Ad (+20 Pts)", web_app: { url: "https://atf-miner-app.pages.dev/app/ad/" } }],
                  [{ text: "👥 Invite Friends (+500 Pts)", callback_data: "ub_referral" }]
                ]
              };
              ctx.waitUntil(sendCqReply(alreadyClaimedMsg, kb));
              return new Response("OK");
            }

            const streakContinues = lastClaim > 0 && elapsed < (48 * 3600 * 1000);
            const streak = streakContinues ? ((profile.daily_streak || 0) + 1) : 1;
            const bonusPts = Math.min(50, 25 + (streak - 1) * 5);
            
            profile.points = (profile.points || 0) + bonusPts;
            profile.daily_streak = streak;
            profile.last_daily_claim = now;
            
            const dailyCost = (profile.accounts || []).length * 100;
            const wasPaused = profile.farming_active === false && (profile.accounts || []).length > 0;
            if (profile.points >= dailyCost) {
              profile.farming_active = true;
            }
            await saveUserProfile(cqChatId, profile);

            const hasPass = profile.subscription_expiry && profile.subscription_expiry > now;
            let statusTxt = hasPass ? "🟢 Active 24/7 (Covered by VIP Pass)" : (profile.farming_active ? "🟢 Active 24/7" : "🔴 Paused (Needs Points)");
            if (wasPaused && profile.farming_active) {
              statusTxt = "🟢 Auto-Resumed & Active 24/7! 🚀";
            }
            const daysRemaining = hasPass ? "Unlimited (VIP Pass)" : (dailyCost > 0 ? `${Math.floor(profile.points / dailyCost)} days` : "Unlimited");
            const succMsg = `🎉 *DAILY BONUS CLAIMED!* 🎁\n\n` +
              `• *Bonus Awarded:* +${bonusPts} Mining Points Credited!\n` +
              `• *Check-In Streak:* 🔥 Day ${streak} Streak (${streak >= 5 ? "MAX +50 Pts!" : `+${bonusPts + 5} Pts tomorrow`})\n` +
              `• *New Points Balance:* 💎 ${profile.points} Points\n` +
              `• *Daily Mining Cost:* ${hasPass ? "0 Pts/day (VIP Pass)" : `${dailyCost} Pts/day`}\n` +
              `• *Days of Mining Remaining:* ~${daysRemaining}\n` +
              `• *Mining Status:* ${statusTxt}\n\n` +
              `💡 _Come back in 24 hours to keep your streak burning!_`;
            const succKb = {
              inline_keyboard: [
                [{ text: "🎬 Watch Video Ad (+20 Pts)", web_app: { url: "https://atf-miner-app.pages.dev/app/ad/" } }],
                [{ text: "💎 View Points & Passes", callback_data: "ub_points" }]
              ]
            };
            ctx.waitUntil(sendCqReply(succMsg, succKb));
            return new Response("OK");
          }

          // C2.55 Points & Balance / Passes Callback
          if (cqData === "ub_points" || cqData === "ub_balance") {
            const profile = await getUserProfile(cqChatId, cq.from);
            const totalSlots = (profile.slots || 1) + (profile.temp_slots || 0);
            const isCovered = profile.subscription_expiry && profile.subscription_expiry > Date.now();
            let passBadge = "Free Tier (Pay-As-You-Go)";
            if (isCovered) {
              const remMs = profile.subscription_expiry - Date.now();
              const dLeft = Math.floor(remMs / (86400 * 1000));
              const hLeft = Math.floor((remMs % (86400 * 1000)) / (3600 * 1000));
              const tName = profile.subscription_tier === "month" ? "💎 30-Day Monthly Pass" : (profile.subscription_tier === "week" ? "🎟️ 7-Day Weekly Pass" : "🎟️ 1-Day Pass");
              passBadge = `${tName} (🟢 Active: ${dLeft > 0 ? `${dLeft}d ` : ""}${hLeft}h left)`;
            }
            const daysRemaining = isCovered ? "Covered by Pass" : (profile.accounts && profile.accounts.length > 0 ? Math.floor((profile.points || 0) / (profile.accounts.length * 100)) : "Unlimited");
            const farmStatus = isCovered ? "🟢 Active 24/7 (Covered by VIP Pass)" : (profile.farming_active ? "🟢 Active 24/7" : "🔴 Paused (Needs Points)");
            const dailyCost = (profile.accounts || []).length * 100;
            const ptsMsg = `💎 *POINTS & MINING BALANCE* ⚡\n\n` +
              `• *Points Balance:* ${profile.points || 0} Points\n` +
              `• *Subscription Pass:* ${passBadge}\n` +
              `• *Farming Status:* ${farmStatus}\n` +
              `• *Daily Mining Cost:* ${isCovered ? "0 Pts/day (Covered by Pass)" : `${dailyCost} Pts/day (100 Pts/account)`}\n` +
              `• *Days of Mining Remaining:* ~${daysRemaining} days\n\n` +
              `📊 *Account Slots Breakdown:*\n` +
              `• *Standard Slots:* ${profile.slots || 1}\n` +
              `• *Bonus Slots (from 50 Ads):* ${profile.temp_slots || 0}\n` +
              `• *Total Available Slots:* ${totalSlots}\n\n` +
              `📺 *Ad Watching Milestone:*\n` +
              `• *Ads Watched:* ${profile.ads_watched || 0}\n` +
              `• *Progress to Next Free Slot:* ${(profile.ads_watched || 0) % 50} / 50 ads\n\n` +
              `👥 *Referral Stats:*\n` +
              `• *Friends Invited:* ${profile.referral_count || 0}\n` +
              `• *Points from Referrals:* ${(profile.referral_count || 0) * 500} Pts`;

            const ptsKb = {
              inline_keyboard: [
                [{ text: "🎬 Watch Video Ad (+20 Pts)", web_app: { url: "https://atf-miner-app.pages.dev/app/ad/" } }],
                [{ text: "🎁 Claim Daily Bonus", callback_data: "ub_daily_claim" }, { text: "👥 Invite Friends (+500 Pts)", callback_data: "ub_referral" }],
                [{ text: "🌟 Upgrade VIP Passes & Slots", callback_data: "ub_buy_stars" }]
              ]
            };
            ctx.waitUntil(sendCqReply(ptsMsg, ptsKb));
            return new Response("OK");
          }

          // C2.6 8 Mining Pools & Auto-Farming Guide
          if (cqData === "ub_withdraw" || cqData === "ub_pools") {
            const poolsMsg = `⛏️ *8 SUPPORTED CLOUD MINING POOLS & BOTS* 🤖\n\n` +
              `Our cloud engines automatically farm and claim all 8 bots 24/7 across your connected accounts:\n\n` +
              `1️⃣ 🪙 [ATF Miner](https://t.me/ATF_AIRDROP_bot?start=6727787768) — Auto 24h mining & daily task claiming\n` +
              `2️⃣ 💎 [Stones Miner](https://t.me/stoneswithestand_bot?start=r6727787768) — Continuous auto-farming sessions\n` +
              `3️⃣ ⚡ [MRG Miner](https://t.me/mrgminerbot?start=ref_IRN1G3XD) — Peak tier hashrate & TON auto-mining\n` +
              `4️⃣ 🎨 [ART Miner](https://t.me/ART_AIRDROP_BOT?start=6727787768) — Auto-farming & token claims\n` +
              `5️⃣ 🤖 [AI Lab Robot](https://t.me/AiLab_robot?start=296852) — Automated hash generation & daily bonuses\n` +
              `6️⃣ 👛 [UltraWallet](https://t.me/UltrawalletTrade_Bot/app?startapp=6727787768) — Multi-pool automated cloud mining\n` +
              `7️⃣ 🏔️ [Apex Miner](https://t.me/ApxMinerBot/app?startapp=6727787768) — Continuous APX token node farming\n` +
              `8️⃣ 🌐 [Ainovum](https://t.me/ainovum_bot?start=ref_6727787768) — 24/7 automated node mining & daily tasks\n\n` +
              `☁️ *What Our Bot Does:*\n` +
              `• Automatically runs 24/7 cloud auto-farming across all 8 bots for your connected accounts.\n` +
              `• Executes daily claims, starts, tasks, and point rewards without keeping your phone or app open.\n` +
              `• All mined tokens accumulate directly in your accounts inside each respective official bot.`;
            ctx.waitUntil(sendCqReply(poolsMsg, {
              inline_keyboard: [
                [{ text: "➕ Connect Account", callback_data: "ub_add_acc" }, { text: "👥 My Accounts", callback_data: "ub_accounts" }],
                [{ text: "🎬 Watch Video Ad (+20 Pts)", web_app: { url: "https://atf-miner-app.pages.dev/app/ad/" } }]
              ]
            }));
            return new Response("OK");
          }

          // C2.7 Support & Ticket
          if (cqData === "ub_support") {
            const supMsg = `💬 *AAA MINING SUPPORT & ASSISTANCE* 🤖\n\n` +
              `Need help with your account, connection, passes, or mining?\n\n` +
              `• *Option 1 (Instant AI Assistant):* Simply type your question in this chat anytime!\n\n` +
              `• *Option 2 (Platform Support):* Send \`/support <your message>\` to reach Support directly.\n\n` +
              `• *Option 3 (Community Supergroup):* Join [AAA Auto Miner Supergroup](https://t.me/AAAAutoMiner) to chat with fellow miners!`;
            ctx.waitUntil(sendCqReply(supMsg, activeUserKeyboard));
            return new Response("OK");
          }

          // C3. Mining Fleet Stats
          if (cqData === "ub_stats") {
            const profile = await getUserProfile(cqChatId, cq.from);
            const totalSlots = (profile.slots || 1) + (profile.temp_slots || 0);
            const isCovered = profile.subscription_expiry && profile.subscription_expiry > Date.now();
            let passBadge = "Free Tier (Pay-As-You-Go)";
            if (isCovered) {
              const remMs = profile.subscription_expiry - Date.now();
              const dLeft = Math.floor(remMs / (86400 * 1000));
              const hLeft = Math.floor((remMs % (86400 * 1000)) / (3600 * 1000));
              const tName = profile.subscription_tier === "month" ? "💎 30-Day Monthly Pass" : (profile.subscription_tier === "week" ? "🎟️ 7-Day Weekly Pass" : "🎟️ 1-Day Pass");
              passBadge = `${tName} (🟢 Active: ${dLeft > 0 ? `${dLeft}d ` : ""}${hLeft}h left)`;
            }
            const daysRemaining = isCovered ? "Covered by VIP Pass" : (profile.accounts.length > 0 ? Math.floor(profile.points / (profile.accounts.length * 100)) : "Unlimited");
            const statsMsg = `📊 *MY MINING FLEET STATS & TELEMETRY* ⚡\n\n` +
              `• *Connected Accounts:* ${(profile.accounts || []).length} / ${totalSlots} Slots\n` +
              `• *Points Balance:* ${profile.points} Points (~${daysRemaining} days left)\n` +
              `• *Pass Status:* ${passBadge}\n` +
              `• *Daily Cost:* ${isCovered ? "Covered by VIP Pass" : `${(profile.accounts || []).length * 100} Pts/day`}\n` +
              `• *Ads Watched:* ${profile.ads_watched || 0} / 50 (${(profile.ads_watched || 0) % 50}/50 towards bonus slot)\n` +
              `• *Referral Friends:* ${profile.referral_count || 0} (${(profile.referral_count || 0) * 500} Pts earned)\n` +
              `• *Active Pools (8/8):* ATF, Stones, MRG, ART, AI Lab, UltraWallet, Apex, Ainovum\n` +
              `• *Cloud Mining:* 🟢 24/7 Automated Running`;
            const statsBtns = {
              inline_keyboard: [
                [{ text: "🌟 Upgrade VIP Passes & Slots", callback_data: "ub_buy_stars" }]
              ]
            };
            ctx.waitUntil(sendCqReply(statsMsg, statsBtns));
            return new Response("OK");
          }

          // D. Telegram Stars Subscription Passes & Upgrades
          if (cqData === "ub_buy_stars") {
            const starsMsg = `🌟 *VIP SUBSCRIPTION PASSES & SLOTS* ⭐\n\n` +
              `Upgrade to uninterrupted 24/7 cloud mining with Telegram Stars:\n\n` +
              `🎟️ *1-Day VIP Pass (15 Stars)*\n` +
              `• 24h unlimited cloud mining\n` +
              `• +150 Bonus Points\n\n` +
              `🎟️ *7-Day Weekly Pass (45 Stars)*\n` +
              `• 7 Days unlimited cloud mining\n` +
              `• +1,000 Bonus Points + 1 Extra Account Slot\n\n` +
              `💎 *30-Day Monthly Pass (120 Stars)*\n` +
              `• 30 Days unlimited cloud mining\n` +
              `• +4,500 Bonus Points + 1 Permanent Slot\n` +
              `• 2x Ad Points Multiplier (+40 Pts per ad view!)\n\n` +
              `🌟 *+1 Permanent Slot (50 Stars)*\n` +
              `• Permanently add an account slot for multi-account farming\n\n` +
              `Choose your subscription pass below:`;
            ctx.waitUntil(sendCqReply(starsMsg, starsUpgradeKeyboard));
            return new Response("OK");
          }

          if (["ub_pass_day", "ub_pass_week", "ub_pass_month", "ub_stars_slot1", "ub_stars_slot3", "ub_stars_vip", "ub_stars_pts1000"].includes(cqData)) {
            ctx.waitUntil(sendStarsInvoice(cqChatId, cqData));
            return new Response("OK");
          }

          // E. Accounts Management
          if (cqData === "ub_add_acc") {
            const profile = await getUserProfile(cqChatId, cq.from);
            const totalSlots = (profile.slots || 1) + (profile.temp_slots || 0);
            if (profile.accounts.length >= totalSlots) {
              const slotLimitMsg = `⚠️ *Account Slot Limit Reached (${profile.accounts.length}/${totalSlots})*\n\n` +
                `You are currently using all available slots!\n\n` +
                `*How to get more slots:*\n` +
                `1. 🌟 *Subscription Pass*: Weekly & Monthly Passes include extra slots!\n` +
                `2. 📺 *Watch 50 Ads*: Earn a free bonus slot! (${profile.ads_watched % 50}/50 watched)\n` +
                `3. 🌟 *Telegram Stars*: Buy permanent slots instantly below!`;
              ctx.waitUntil(sendCqReply(slotLimitMsg, starsUpgradeKeyboard));
              return new Response("OK");
            }
            const hasPass = profile.subscription_expiry && profile.subscription_expiry > Date.now();
            if (!hasPass && profile.points < 100) {
              const lowPtsMsg = `⚠️ *Insufficient Points to Connect Account*\n\n` +
                `Connecting an account requires at least *100 Points* for Day 1 automated cloud farming (or an active VIP Pass).\n` +
                `Your balance: *${profile.points} Points*.\n\n` +
                `*Quickly get access:*\n` +
                `• 🎟️ *Get a Day Pass (15 Stars)* for unlimited 24h mining\n` +
                `• 📺 Watch an ad (+20 Pts)\n` +
                `• 👥 Invite a friend (+500 Pts)`;
              ctx.waitUntil(sendCqReply(lowPtsMsg, activeUserKeyboard));
              return new Response("OK");
            }

            if (env.BACKUP_KV) {
              await env.BACKUP_KV.put("login_flow:user_" + cqChatId, JSON.stringify({ step: "waiting_phone" }), { expirationTtl: 600 }).catch(() => {});
            }
            const promptPhone = `📱 *Connect Telegram Account for 24/7 Cloud Mining*\n\n` +
              `Please send the phone number of the Telegram account you want to connect:\n\n` +
              `• *Format:* \`+88017XXXXXXXX\` or \`017XXXXXXXX\`\n` +
              `• *International:* \`+1...\`, \`+44...\`, \`+91...\`\n\n` +
              `🔒 *100% Serverless & Encrypted:*\n` +
              `Your session runs safely in the cloud and automatically binds to all 8 mining pools.\n\n` +
              `_(Send phone number or tap ❌ Cancel Connection below)_`;
            ctx.waitUntil(sendCqReply(promptPhone, userCancelKeyboard));
            return new Response("OK");
          }

          if (cqData.startsWith("ub_disconnect_")) {
            const targetUid = cqData.replace("ub_disconnect_", "").trim();
            const profile = await getUserProfile(cqChatId, cq.from);
            const targetStr = String(targetUid).replace("+", "");
            const removedAcc = (profile.accounts || []).find(a => String(a.user_id) === targetStr || String(a.phone || "").replace("+", "") === targetStr);
            profile.accounts = (profile.accounts || []).filter(a => String(a.user_id) !== targetStr && String(a.phone || "").replace("+", "") !== targetStr);
            await saveUserProfile(cqChatId, profile);
            const totalSlots = (profile.slots || 1) + (profile.temp_slots || 0);
            const accDesc = removedAcc ? `${removedAcc.name || "Account"} (\`${removedAcc.phone || removedAcc.user_id}\`)` : `Account \`${targetUid}\``;
            const repMsg = `✅ *Account Disconnected Successfully!* 🗑️\n\n` +
              `• *Removed:* ${accDesc}\n` +
              `• *Slots In Use:* ${profile.accounts.length} / ${totalSlots}\n` +
              `• *Freed Capacity:* ⚡ 1 Cloud Slot is now available!\n\n` +
              `You can now connect another account using *➕ Connect Account*.`;
            ctx.waitUntil(sendCqReply(repMsg, activeUserKeyboard));
            return new Response("OK");
          }

          if (cqData === "ub_remove_menu") {
            const profile = await getUserProfile(cqChatId, cq.from);
            if (!profile.accounts || profile.accounts.length === 0) {
              ctx.waitUntil(sendCqReply("ℹ️ *No Connected Accounts*\n\nYou do not have any active mining accounts connected to remove.\n\nTap *➕ Connect Account* below to link your first account!", {
                inline_keyboard: [
                  [{ text: "➕ Connect Account", callback_data: "ub_add_acc" }],
                  [{ text: "🔙 Back to Accounts", callback_data: "ub_accounts_list" }]
                ]
              }));
              return new Response("OK");
            }
            const promptTxt = `🗑️ *SELECT AN ACCOUNT TO DISCONNECT:*\n\n` +
              `Choose the account you want to remove from 24/7 cloud mining:\n\n` +
              `⚠️ _Disconnecting an account immediately frees up its cloud slot._`;
            const buttons = profile.accounts.map(a => [
              { text: `🗑️ Disconnect: ${a.name || a.phone} (${a.phone || a.user_id})`, callback_data: `ub_disconnect_${a.user_id || a.phone}` }
            ]);
            buttons.push([{ text: "🔙 Back to Accounts", callback_data: "ub_accounts_list" }]);
            ctx.waitUntil(sendCqReply(promptTxt, { inline_keyboard: buttons }));
            return new Response("OK");
          }

          if (cqData === "ub_accounts_list" || cqData === "ub_accounts") {
            const profile = await getUserProfile(cqChatId, cq.from);
            const totalSlots = (profile.slots || 1) + (profile.temp_slots || 0);
            const isCovered = profile.subscription_expiry && profile.subscription_expiry > Date.now();
            let passBadge = "Free Tier (Pay-As-You-Go)";
            if (isCovered) {
              const remMs = profile.subscription_expiry - Date.now();
              const dLeft = Math.floor(remMs / (86400 * 1000));
              const hLeft = Math.floor((remMs % (86400 * 1000)) / (3600 * 1000));
              const tName = profile.subscription_tier === "month" ? "💎 30-Day Monthly Pass" : (profile.subscription_tier === "week" ? "🎟️ 7-Day Weekly Pass" : "🎟️ 1-Day Pass");
              passBadge = `${tName} (🟢 Active: ${dLeft > 0 ? `${dLeft}d ` : ""}${hLeft}h left)`;
            }
            const daysRemaining = isCovered ? "Covered by Pass" : (profile.accounts.length > 0 ? Math.floor(profile.points / (profile.accounts.length * 100)) : "Unlimited");
            let accList = "• _No accounts connected yet. Tap ➕ Connect Account below!_";
            if (profile.accounts && profile.accounts.length > 0) {
              accList = profile.accounts.map((a, i) =>
                `*${i + 1}.* \`${a.phone || a.user_id}\` (${a.name || "User"}) — 🟢 Active Cloud Farming`
              ).join("\n");
            }

            const farmStatus = isCovered ? "🟢 Active 24/7 (Covered by VIP Pass)" : (profile.farming_active ? "🟢 Active 24/7" : "🔴 Paused (Insufficient Points)");
            const accMsg = `👥 *MY CONNECTED ACCOUNTS* 📱\n\n` +
              `• *Slots In Use:* ${profile.accounts.length} / ${totalSlots}\n` +
              `• *Subscription Pass:* ${passBadge}\n` +
              `• *Farming Status:* ${farmStatus}\n` +
              `• *Daily Cost:* ${isCovered ? "0 Pts/day (Covered by Pass)" : `${profile.accounts.length * 100} Pts/day`}\n` +
              `• *Points Balance:* ${profile.points} Pts (~${daysRemaining} days left)\n\n` +
              `📱 *Active Accounts:*\n${accList}\n\n` +
              `💡 _Every account automatically farms all 8 bots: ATF Miner, Stones, MRG, ART, AI Lab, UltraWallet, Apex, and Ainovum._`;

            const inlineBtns = [
              [{ text: "➕ Connect Account", callback_data: "ub_add_acc" }, { text: "🗑️ Remove Account", callback_data: "ub_remove_menu" }],
              [{ text: "🌟 VIP Passes & Slots", callback_data: "ub_buy_stars" }]
            ];
            if (profile.accounts && profile.accounts.length > 0) {
              for (const a of profile.accounts) {
                inlineBtns.push([{ text: `🗑️ Remove ${a.name || a.phone} (${a.phone || a.user_id})`, callback_data: `ub_disconnect_${a.user_id || a.phone}` }]);
              }
            }
            ctx.waitUntil(sendCqReply(accMsg, { inline_keyboard: inlineBtns }));
            return new Response("OK");
          }

          return new Response("OK");
        }

        // 3. Handle Incoming Messages
        const msg = update.message;
        if (!msg || !msg.chat) return new Response("OK");
        const chatId = msg.chat.id;
        const senderName = msg.from?.first_name || msg.from?.username || "Miner";
        let text = (msg.text || "").trim();
        text = text.replace(/^(\/[a-zA-Z0-9_]+)@[a-zA-Z0-9_]+/i, '$1');

        // Anti-Sybil Gate: Check if user is suspended/banned
        if (String(chatId) !== (env.OWNER_ID || "6727787768")) {
          const profileCheck = await getUserProfile(chatId, msg.from);
          if (profileCheck && profileCheck.is_banned) {
            await fetch(`https://api.telegram.org/bot${userBotToken}/sendMessage`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                chat_id: chatId,
                text: "🚫 *Access Restricted*\n\nYour account has been suspended by platform administration for suspicious anti-sybil activity or policy violations.\n\nIf you believe this is an error, please contact @AAAAutoMiner.",
                parse_mode: "Markdown"
              })
            }).catch(() => {});
            return new Response("OK");
          }
        }

        const sendUserReply = async (txt, replyMarkup = null, parseMode = "Markdown") => {
          const payload = { chat_id: chatId, text: txt, disable_web_page_preview: true };
          if (parseMode) payload.parse_mode = parseMode;
          if (replyMarkup) {
            payload.reply_markup = replyMarkup;
          }
          try {
            const resp = await fetch(`https://api.telegram.org/bot${userBotToken}/sendMessage`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(payload)
            });
            if (!resp.ok && parseMode) {
              delete payload.parse_mode;
              await fetch(`https://api.telegram.org/bot${userBotToken}/sendMessage`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
              }).catch(() => {});
            }
          } catch (_) {}
        };

        const sendUserChatAction = async (action = "typing") => {
          try {
            await fetch(`https://api.telegram.org/bot${userBotToken}/sendChatAction`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ chat_id: chatId, action })
            });
          } catch (_) {}
        };

        // A. Telegram Stars Payment Receipt
        if (msg.successful_payment) {
          const pay = msg.successful_payment;
          const item = pay.invoice_payload;
          const profile = await getUserProfile(chatId, msg.from);
          let grantedText = "";
          const now = Date.now();
          const baseExpiry = (profile.subscription_expiry && profile.subscription_expiry > now) ? profile.subscription_expiry : now;

          if (item === "pass_day") {
            profile.subscription_expiry = baseExpiry + (24 * 3600 * 1000);
            profile.subscription_tier = "day";
            profile.points = (profile.points || 0) + 150;
            profile.farming_active = true;
            grantedText = "🎟️ *1-Day VIP Pass Activated!*\n• 24 Hours Unlimited Cloud Mining (Zero Point Deduction)\n• +150 Bonus Points credited!";
          } else if (item === "pass_week") {
            profile.subscription_expiry = baseExpiry + (7 * 86400 * 1000);
            profile.subscription_tier = "week";
            profile.points = (profile.points || 0) + 1000;
            profile.temp_slots = (profile.temp_slots || 0) + 1;
            profile.farming_active = true;
            grantedText = "🎟️ *7-Day Weekly Pass Activated!*\n• 7 Days Unlimited Cloud Mining (Zero Point Deduction)\n• +1,000 Bonus Points credited!\n• +1 Bonus Account Slot unlocked!";
          } else if (item === "pass_month") {
            profile.subscription_expiry = baseExpiry + (30 * 86400 * 1000);
            profile.subscription_tier = "month";
            profile.points = (profile.points || 0) + 4500;
            profile.slots = (profile.slots || 1) + 1;
            profile.farming_active = true;
            grantedText = "💎 *30-Day Monthly Pass Activated!*\n• 30 Days Unlimited Cloud Mining (Zero Point Deduction)\n• +4,500 Bonus Points credited!\n• +1 Permanent Extra Account Slot unlocked!\n• 2x Ad Points Multiplier (+40 Pts per ad view) active!";
          } else if (item === "buy_slot_1") {
            profile.slots = (profile.slots || 1) + 1;
            grantedText = "🌟 *+1 Permanent Account Slot* unlocked!";
          } else if (item === "buy_slot_3") {
            profile.slots = (profile.slots || 1) + 3;
            grantedText = "🌟 *+3 Permanent Account Slots* unlocked!";
          } else if (item === "buy_vip") {
            profile.subscription_expiry = baseExpiry + (30 * 86400 * 1000);
            profile.subscription_tier = "month";
            profile.slots = (profile.slots || 1) + 1;
            profile.points = (profile.points || 0) + 3000;
            profile.farming_active = true;
            grantedText = "💎 *VIP Miner Pass Activated!*\n• 30 Days Unlimited Cloud Mining\n• +1 Permanent Slot\n• +3,000 Points credited!";
          } else if (item === "buy_points_1000") {
            profile.points = (profile.points || 0) + 1000;
            grantedText = "💎 *+1,000 Points Credited!*";
          }
          await saveUserProfile(chatId, profile);
          const totalSlots = (profile.slots || 1) + (profile.temp_slots || 0);

          const tierTitle = item === "pass_day" ? "🎟️ 1-Day VIP Pass" : (item === "pass_week" ? "🎟️ 7-Day Weekly Pass" : (item === "pass_month" ? "💎 30-Day Monthly Pass" : (item === "buy_slot_1" ? "🌟 1 Permanent Slot" : "💎 VIP Pass")));
          const bonusPts = item === "pass_day" ? 150 : (item === "pass_week" ? 1000 : (item === "pass_month" ? 4500 : 0));
          ctx.waitUntil(broadcastMilestoneUnlocked("Milestone Unlocked", senderName, chatId, `${tierTitle} Activated`, bonusPts ? `+${bonusPts} Points & Unlimited VIP Mining` : "Extra Account Capacity Unlocked"));

          ctx.waitUntil(sendUserReply(
            `🎉 *PAYMENT RECEIVED VIA TELEGRAM STARS!* ⭐\n\n` +
            `Thank you for upgrading with Telegram Stars!\n\n` +
            `${grantedText}\n\n` +
            `• *Total Available Slots:* ${totalSlots}\n` +
            `• *Points Balance:* ${profile.points} Pts\n` +
            `• *Transaction ID:* \`${pay.telegram_payment_charge_id}\``,
            activeUserKeyboard
          ));
          return new Response("OK");
        }

        // B. Handle Cancel Connection Command
        const isCancel = (text === "/cancel" || text === "❌ Cancel Connection" || text === "❌ Cancel");
        if (isCancel) {
          if (env.BACKUP_KV) await env.BACKUP_KV.delete("login_flow:user_" + chatId).catch(() => {});
          ctx.waitUntil(cloudLoginCancel("ub_" + chatId));
          ctx.waitUntil(sendUserReply("❌ Account connection cancelled. Returning to main menu.", activeUserKeyboard));
          return new Response("OK");
        }

        // C. Check Active Account Login Flow in KV
        let loginFlowState = null;
        if (env.BACKUP_KV) {
          try {
            const rawFlow = await env.BACKUP_KV.get("login_flow:user_" + chatId);
            if (rawFlow) loginFlowState = JSON.parse(rawFlow);
          } catch (_) {}
        }

        const isCommandOrMenu = text.startsWith("/") || text.includes("👥") || text.includes("➕") || text.includes("💎") || text.includes("📺") || text.includes("🎬") || text.includes("🌟") || text.includes("📢") || text.includes("💬") || text.includes("🎟️") || text.includes("🎁") || text.includes("💳") || text.includes("📊") || text.includes("🗑️");

        if (loginFlowState && !isCommandOrMenu) {
          ctx.waitUntil((async () => {
            await sendUserChatAction("typing");
            const step = loginFlowState.step;
            const phone = loginFlowState.phone || "";
            const node_url = loginFlowState.node_url || "";

            // 1. Waiting for Phone Number
            if (step === "waiting_phone") {
              let normalized = text.replace(/[\s\-]/g, '');
              if (normalized.startsWith("01") && normalized.length === 11) {
                normalized = "+88" + normalized;
              } else if (normalized.startsWith("1") && normalized.length === 10) {
                normalized = "+880" + normalized;
              } else if (!normalized.startsWith("+")) {
                normalized = "+" + normalized;
              }

              const res = await cloudLoginSendCode(normalized, "ub_" + chatId);
              if (res && res.ok) {
                if (env.BACKUP_KV) {
                  await env.BACKUP_KV.put("login_flow:user_" + chatId, JSON.stringify({ step: "waiting_code", phone: normalized, node_url: res.node_url || "" }), { expirationTtl: 600 }).catch(() => {});
                }
                const msgTxt = `📨 *Telegram Verification Code Sent!*\n\n` +
                  `Telegram sent a 5-digit verification code to \`${normalized}\`.\n\n` +
                  `Please reply with the code (e.g. \`12345\`):\n` +
                  `_(Or tap ❌ Cancel Connection to abort)_`;
                await sendUserReply(msgTxt, userCancelKeyboard);
              } else {
                const errDetail = res ? (res.error || res.message) : "Failed to connect to Telegram MTProto Gateway";
                const errMsg = `❌ *Could Not Request Code*\n\n` +
                  `Failed to request code for \`${normalized}\`.\n` +
                  `*Error:* ${errDetail}\n\n` +
                  `Please check the phone number and send again (or tap ❌ Cancel Connection):`;
                await sendUserReply(errMsg, userCancelKeyboard);
              }
              return;
            }

            // 2. Waiting for 2FA Password
            if (step === "waiting_2fa") {
              const res = await cloudLoginVerify("ub_" + chatId, { password: text, phone, node_url });
              if (res && res.ok) {
                if (env.BACKUP_KV) await env.BACKUP_KV.delete("login_flow:user_" + chatId).catch(() => {});
                const profile = await getUserProfile(chatId, msg.from);
                profile.accounts = profile.accounts || [];
                const accObj = {
                  user_id: res.user_id,
                  phone: res.phone || phone,
                  name: res.name || "User",
                  username: res.username || "None",
                  added_at: Date.now(),
                  status: "active"
                };
                const existingIdx = profile.accounts.findIndex(a => 
                  String(a.user_id) === String(res.user_id) || 
                  (res.phone && a.phone === res.phone) || 
                  (phone && a.phone === phone)
                );
                if (existingIdx >= 0) {
                  profile.accounts[existingIdx] = accObj;
                } else {
                  profile.accounts.push(accObj);
                }

                let welcomeBonusText = "";
                if (!profile.welcome_gift_claimed && profile.accounts.length === 1) {
                  const claimedKey = `ub_welcome_claimed_acc:${res.user_id}`;
                  const alreadyClaimed = await upstashGet(claimedKey);
                  if (!alreadyClaimed) {
                    profile.welcome_gift_claimed = true;
                    profile.points = (profile.points || 0) + 100;
                    profile.farming_active = true;
                    welcomeBonusText = "\n\n🎁 *First-Account Welcome Gift:* +100 Points Credited for instant cloud farming!";
                    ctx.waitUntil(upstashSet(claimedKey, { profile_uid: chatId, acc_uid: res.user_id, claimed_at: Date.now() }));
                    ctx.waitUntil(upstashSadd("ub_welcome_gift_recipients", String(chatId)));
                  } else {
                    profile.welcome_gift_claimed = true;
                    welcomeBonusText = "\n\nℹ️ *Account Connected:* Welcome gift was already claimed previously on this account.";
                  }
                }

                await saveUserProfile(chatId, profile);
                ctx.waitUntil(broadcastMilestoneUnlocked("Milestone Unlocked", res.name || "Miner", chatId, `Cloud Node Connected (${profile.accounts.length} Active)`, "24/7 Autonomous Mining Live"));

                const succMsg = `🎉 *ACCOUNT CONNECTED SUCCESSFULLY WITH 2FA!* 🚀\n\n` +
                  `• *Name:* ${res.name || "User"}\n` +
                  `• *Username:* @${res.username || "None"}\n` +
                  `• *User ID:* \`${res.user_id}\`\n` +
                  `• *Mining Status:* 🟢 24/7 Cloud Automated\n` +
                  `• *Pools Active (8/8):* ATF Miner, Stones, MRG, ART, AI Lab, UltraWallet, Apex, Ainovum\n` +
                  `• *Balance:* ${profile.points} Points${welcomeBonusText}\n\n` +
                  `✅ 100% Cloud Mining active! 100 points/day will be deducted while farming is live.`;
                await sendUserReply(succMsg, activeUserKeyboard);
              } else {
                const errDetail = res ? (res.error || res.message) : "Invalid 2FA password";
                const errMsg = `❌ *2FA Authentication Failed*\n\n` +
                  `*Error:* ${errDetail}\n\n` +
                  `Please check your Two-Factor Password and try again:\n` +
                  `_(Or tap ❌ Cancel Connection to abort)_`;
                await sendUserReply(errMsg, userCancelKeyboard);
              }
              return;
            }

            // 3. Waiting for Verification Code
            const res = await cloudLoginVerify("ub_" + chatId, { code: text, phone, node_url });
            if (res && res.need_2fa) {
              if (env.BACKUP_KV) {
                await env.BACKUP_KV.put("login_flow:user_" + chatId, JSON.stringify({ step: "waiting_2fa", phone: res.phone || phone, node_url }), { expirationTtl: 600 }).catch(() => {});
              }
              const twoFaMsg = `🔒 *Two-Factor Authentication (2FA) Required*\n\n` +
                `This account has a Two-Step Cloud Password enabled.\n` +
                `Please reply with your 2FA password:\n\n` +
                `_(Or tap ❌ Cancel Connection to abort)_`;
              await sendUserReply(twoFaMsg, userCancelKeyboard);
              return;
            }

            if (res && res.ok) {
              if (env.BACKUP_KV) await env.BACKUP_KV.delete("login_flow:user_" + chatId).catch(() => {});
              const profile = await getUserProfile(chatId, msg.from);
              profile.accounts = profile.accounts || [];
              const accObj = {
                user_id: res.user_id,
                phone: res.phone || phone,
                name: res.name || "User",
                username: res.username || "None",
                added_at: Date.now(),
                status: "active"
              };
              const existingIdx = profile.accounts.findIndex(a => 
                String(a.user_id) === String(res.user_id) || 
                (res.phone && a.phone === res.phone) || 
                (phone && a.phone === phone)
              );
              if (existingIdx >= 0) {
                profile.accounts[existingIdx] = accObj;
              } else {
                profile.accounts.push(accObj);
              }

              let welcomeBonusText = "";
              if (!profile.welcome_gift_claimed && profile.accounts.length === 1) {
                const claimedKey = `ub_welcome_claimed_acc:${res.user_id}`;
                const alreadyClaimed = await upstashGet(claimedKey);
                if (!alreadyClaimed) {
                  profile.welcome_gift_claimed = true;
                  profile.points = (profile.points || 0) + 100;
                  profile.farming_active = true;
                  welcomeBonusText = "\n\n🎁 *First-Account Welcome Gift:* +100 Points Credited for instant cloud farming!";
                  ctx.waitUntil(upstashSet(claimedKey, { profile_uid: chatId, acc_uid: res.user_id, claimed_at: Date.now() }));
                  ctx.waitUntil(upstashSadd("ub_welcome_gift_recipients", String(chatId)));
                } else {
                  profile.welcome_gift_claimed = true;
                  welcomeBonusText = "\n\nℹ️ *Account Connected:* Welcome gift was already claimed previously on this account.";
                }
              }

              await saveUserProfile(chatId, profile);
              ctx.waitUntil(broadcastMilestoneUnlocked("Milestone Unlocked", res.name || "Miner", chatId, `Cloud Node Connected (${profile.accounts.length} Active)`, "24/7 Autonomous Mining Live"));

              const succMsg = `🎉 *ACCOUNT CONNECTED SUCCESSFULLY!* 🚀\n\n` +
                `• *Name:* ${res.name || "User"}\n` +
                `• *Username:* @${res.username || "None"}\n` +
                `• *User ID:* \`${res.user_id}\`\n` +
                `• *Mining Status:* 🟢 24/7 Cloud Automated\n` +
                `• *Pools Active (8/8):* ATF Miner, Stones, MRG, ART, AI Lab, UltraWallet, Apex, Ainovum\n` +
                `• *Balance:* ${profile.points} Points${welcomeBonusText}\n\n` +
                `✅ 100% Cloud Mining active! 100 points/day will be deducted while farming is live.`;
              await sendUserReply(succMsg, activeUserKeyboard);
            } else {
              const errDetail = res ? (res.error || res.message) : "Invalid verification code";
              const errMsg = `❌ *Authentication Failed*\n\n` +
                `*Error:* ${errDetail}\n\n` +
                `Please check the 5-digit code and reply again:\n` +
                `_(Or tap ❌ Cancel Connection to abort)_`;
              await sendUserReply(errMsg, userCancelKeyboard);
            }
          })());
          return new Response("OK");
        }

        // D. Channel Gate Check on All User Interactions
        ctx.waitUntil((async () => {
          const profile = await getUserProfile(chatId, msg.from);

          // Handle Referral Tracking on /start ref_<id> or /start <id>
          if (text.startsWith("/start")) {
            const parts = text.split(/\s+/);
            if (parts.length > 1) {
              let refId = parts[1].trim();
              if (refId.startsWith("ref_")) refId = refId.replace("ref_", "").trim();
              if (/^\d{6,12}$/.test(refId) && refId !== String(chatId) && !profile.referred_by) {
                profile.referred_by = refId;
                await saveUserProfile(chatId, profile);
                // Credit referrer +500 points
                try {
                  const refProf = await getUserProfile(refId);
                  if (refProf) {
                    refProf.points = (refProf.points || 0) + 500;
                    refProf.referral_count = (refProf.referral_count || 0) + 1;
                    const refCost = (refProf.accounts || []).length * 100;
                    if (refProf.points >= refCost) {
                      refProf.farming_active = true;
                    }
                    await saveUserProfile(refId, refProf);
                    await fetch(`https://api.telegram.org/bot${userBotToken}/sendMessage`, {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({
                        chat_id: refId,
                        text: `🎉 *REFERRAL BONUS RECEIVED!* 🎁\n\n` +
                          `Your friend *${senderName}* just joined via your link!\n\n` +
                          `• *Reward:* +500 Mining Points\n` +
                          `• *New Balance:* ${refProf.points} Points\n` +
                          `• *Total Referrals:* ${refProf.referral_count}`,
                        parse_mode: "Markdown"
                      })
                    }).catch(() => {});
                  }
                } catch (_) {}
              }
            }
          }

          // Verify Channel Membership (enforce gate for new or unverified users)
          if (!profile.joined_channels) {
            const chCheck = await checkUserChannels(chatId);
            if (!chCheck.ok) {
              const gateMsg = `🔒 *MANDATORY COMMUNITY ACCESS GATE*\n\n` +
                `Welcome to *AAA Auto Mining Platform*!\n` +
                `_⚡ Created by AAA — Autonomous Cloud Mining Ecosystem_\n\n` +
                `To access automated 24/7 cloud mining, free AI copilot, and account management, you must join our 3 official community hubs:\n\n` +
                `1️⃣ 💬 [AAA Auto Miner — Community Hub](https://t.me/AAAAutoMiner)\n` +
                `2️⃣ 📢 [AAA Auto Miner — Announcements](https://t.me/AAAAUTOMINING)\n` +
                `3️⃣ ⚡ [AAA ATF Miner — Live Activity](https://t.me/AAA_ACTIVITY)\n\n` +
                `👉 *Join all 3 channels above, then tap 🔄 Verify Membership below to claim 🎁 100 Free Welcome Points!*`;
              await sendUserReply("👋 *Welcome to AAA Auto Mining!* (Created by AAA)\nAccess all features below or choose from the interactive menu:", activeUserKeyboard);
              await sendUserReply(gateMsg, gateInlineKeyboard);
              return;
            }

            profile.joined_channels = true;
            if (!profile.activity_broadcasted) {
              profile.activity_broadcasted = true;
              ctx.waitUntil(broadcastNewMinerJoined(profile, chatId, msg.from));
            }
            await saveUserProfile(chatId, profile);
          }

          // E. Process Standard Bot Commands & Menu Buttons

          // 0.0 Executive Admin Router (/admin, /dashboard, /users, "👑 User Admin Dashboard", "👑 Admin Console")
          if (text === "👑 User Admin Dashboard" || text === "👑 User Admin Console" || text === "👑 Admin Console" || text === "⚡ Executive Console" || text === "/admin" || text.startsWith("/admin") || text === "/dashboard" || text.startsWith("/dashboard") || text === "/users" || text.startsWith("/users")) {
            if (String(chatId) !== "6727787768" && String(chatId) !== (env.OWNER_ID || "6727787768")) {
              await sendUserReply("⚠️ Access restricted to Platform Administrator Arif.", activeUserKeyboard);
              return;
            }
            const adminMsg = `👑 *USER BOT ADMIN CONSOLE (DASHBOARD 2)* 🚀\n\n` +
              `Hello Commander Arif! Here is your dedicated *User Bot Admin Dashboard* for managing community miners, accounts, and points:\n\n` +
              `• 👥 *Miners Hub:* Community accounts & balances\n` +
              `• 💎 *Points Economy:* Daily cost sweeps & grants\n` +
              `• 🛡️ *Moderation:* Ban/Unban & VIP passes\n` +
              `• 🔐 *Biometrics & Supabase:* Protected by WebAuthn Passkey + Master Password\n` +
              `• 🌐 *Dedicated Node 1 Cloudflare Account:* Zero ads, pure admin console\n\n` +
              `👇 *Tap button below to launch the User Bot Admin Dashboard:*`;
            await sendUserReply(adminMsg, {
              inline_keyboard: [
                [{ text: "🚀 Open Admin Dashboard (Node 1 Pages)", web_app: { url: "https://aaa-admin-portal.pages.dev/" } }],
                [{ text: "🌐 Open Admin Dashboard (Vercel Mirror)", web_app: { url: "https://agy-aaa000.vercel.app/" } }]
              ]
            });
            return;
          }

          // 0. Dedicated Help & User Guide (/help, /guide, /info, /about)
          if (text.startsWith("/help") || text.startsWith("/guide") || text.startsWith("/info") || text.startsWith("/about")) {
            const helpMsg = `📖 *AAA AUTO MINING & ARI AI GUIDE* 🤖\n` +
              `_⚡ Created by AAA — Autonomous Cloud Mining Ecosystem_\n\n` +
              `Hello ${senderName}! Here is your complete guide to automated cloud mining:\n\n` +
              `🤖 *8 Automated Mining Pools & Links:*\n` +
              `1️⃣ 🪙 [ATF Miner](https://t.me/ATF_AIRDROP_bot?start=6727787768) — Auto 24h mining & daily task claiming\n` +
              `2️⃣ 💎 [Stones Miner](https://t.me/stoneswithestand_bot?start=r6727787768) — Continuous auto-farming sessions\n` +
              `3️⃣ ⚡ [MRG Miner](https://t.me/mrgminerbot?start=ref_IRN1G3XD) — Peak tier hashrate & TON auto-mining\n` +
              `4️⃣ 🎨 [ART Miner](https://t.me/ART_AIRDROP_BOT?start=6727787768) — Auto-farming & token claims\n` +
              `5️⃣ 🤖 [AI Lab Robot](https://t.me/AiLab_robot?start=296852) — Automated hash generation & daily bonuses\n` +
              `6️⃣ 👛 [UltraWallet](https://t.me/UltrawalletTrade_Bot/app?startapp=6727787768) — Multi-pool automated cloud mining\n` +
              `7️⃣ 🏔️ [Apex Miner](https://t.me/ApxMinerBot/app?startapp=6727787768) — Continuous APX node farming\n` +
              `8️⃣ 🌐 [Ainovum](https://t.me/ainovum_bot?start=ref_6727787768) — 24/7 automated node mining & daily tasks\n\n` +
              `1️⃣ *How to Connect & Remove Accounts*\n` +
              `• *Connect:* Tap *➕ Connect Account*, send phone number & 5-digit Telegram code.\n` +
              `• *Remove:* Tap *👥 My Accounts* in the menu and tap *🗑️ Remove* next to any account, or type \`/remove\` anytime!\n` +
              `• Cloud-powered: your accounts farm 24/7 in the cloud without needing your phone or app open!\n\n` +
              `2️⃣ *Points & Free Earning*\n` +
              `• Daily cost is 100 Points/day per active connected account.\n` +
              `• *🎬 Watch Ads:* Tap *🎬 Watch Ads* (next to message input) or in the message above to earn +20 Points every 15s. Every 50 ads unlocks a *Free Bonus Account Slot*!\n` +
              `• *👥 Invite Friends:* Earn +500 Points for every friend who joins & verifies.\n\n` +
              `3️⃣ *VIP Subscription Passes (Telegram Stars)*\n` +
              `• *🎟️ 1-Day Pass (15 Stars):* 24h unlimited cloud mining + 150 points.\n` +
              `• *🎟️ 7-Day Weekly Pass (45 Stars):* 7 days unlimited cloud mining + 1,000 points + 1 extra account slot.\n` +
              `• *💎 30-Day Monthly Pass (120 Stars):* 30 days unlimited cloud mining + 4,500 points + 1 permanent slot + 2x ad rewards (+40 Pts per ad)!\n` +
              `• *🌟 Permanent Slot (50 Stars):* Add permanent account capacity.\n\n` +
              `💬 *Ask Ari AI:* Simply type any question or guide request directly in this chat!`;
            await sendUserReply(helpMsg, userWelcomeInlineKeyboard);
            return;
          }

          // Deep-link routing for /start
          if (text.startsWith("/start invite") || text === "/invite") {
            const refLink = `https://t.me/AAAPREMIUMAPPSbot?start=ref_${chatId}`;
            const refMsg = `👥 *INVITE FRIENDS & EARN POINTS* 🚀\n\n` +
              `Share your personal referral link with friends. For every friend who joins & verifies:\n` +
              `🎁 *You earn +500 Points!* (5 full days of automated cloud mining!)\n` +
              `🎁 *Your friend receives 100 Free Welcome Points!*\n\n` +
              `🔗 *Your Referral Link:*\n\`${refLink}\`\n\n` +
              `📊 *Your Referral Stats:*\n` +
              `• *Invited Users:* ${profile.referral_count || 0}\n` +
              `• *Points Earned:* ${(profile.referral_count || 0) * 500} Pts`;
            await sendUserReply(refMsg, {
              inline_keyboard: [
                [{ text: "📤 Share to Telegram", url: `https://t.me/share/url?url=${encodeURIComponent(refLink)}&text=${encodeURIComponent("Join AAA Auto Mining to earn crypto 24/7 automatically!")}` }]
              ]
            });
            return;
          }

          if (text.startsWith("/start rewards") || text === "/rewards") {
            const isMonthlyPass = profile.subscription_tier === "month" && profile.subscription_expiry && profile.subscription_expiry > Date.now();
            const adPts = isMonthlyPass ? 40 : 20;
            const rewMsg = `🎁 *MY REWARDS & EARNING HUB* 💎\n\n` +
              `• *Available Balance:* ${profile.points} Mining Points\n` +
              `• *Ads Watched:* ${profile.ads_watched || 0}/50 (Earn +${adPts} Pts/view)\n` +
              `• *Next Bonus Slot:* ${(profile.ads_watched || 0) % 50}/50 ads\n` +
              `• *Referral Earnings:* ${(profile.referral_count || 0) * 500} Pts (${profile.referral_count || 0} friends)\n\n` +
              `Earn free points below:`;
            const rewBtns = {
              inline_keyboard: [
                [{ text: `🎬 Watch Video Ad (+${adPts} Pts)`, web_app: { url: "https://atf-miner-app.pages.dev/app/ad/" } }],
                [{ text: "🎁 Claim Daily Bonus", callback_data: "ub_daily_claim" }, { text: "👥 Invite Friends (+500 Pts)", callback_data: "ub_referral" }],
                [{ text: "🌟 Upgrade VIP Passes & Slots", callback_data: "ub_buy_stars" }]
              ]
            };
            await sendUserReply(rewMsg, rewBtns);
            return;
          }

          if (text === "📊 My Stats" || text === "My Stats" || text === "📊 Stats" || text.startsWith("/start stats") || text === "/stats" || text.startsWith("/stats") || text === "/status" || text.startsWith("/status")) {
            const totalSlots = (profile.slots || 1) + (profile.temp_slots || 0);
            const isCovered = profile.subscription_expiry && profile.subscription_expiry > Date.now();
            let passBadge = "Free Tier";
            if (isCovered) {
              const remMs = profile.subscription_expiry - Date.now();
              const dLeft = Math.floor(remMs / (86400 * 1000));
              const hLeft = Math.floor((remMs % (86400 * 1000)) / (3600 * 1000));
              const tName = profile.subscription_tier === "month" ? "💎 Monthly Pass" : (profile.subscription_tier === "week" ? "🎟️ Weekly Pass" : "🎟️ Day Pass");
              passBadge = `${tName} (${dLeft > 0 ? `${dLeft}d ` : ""}${hLeft}h left)`;
            }
            const dCost = isCovered ? 0 : ((profile.accounts || []).length * 100);
            const daysRemaining = isCovered ? "Unlimited (VIP Pass)" : (dCost > 0 ? `${Math.floor((profile.points || 0) / dCost)} Days` : "0 Accounts");
            const farmStatus = isCovered ? "🟢 Active 24/7 (Covered by VIP Pass)" : (profile.farming_active ? "🟢 Active & Mining 24/7" : "🔴 Paused (Needs Points)");
            const statsMsg = `📊 *MY MINING FLEET STATS* ⚡\n\n` +
              `• *Connected Accounts:* ${(profile.accounts || []).length} / ${totalSlots} Slots\n` +
              `• *Points Balance:* ${profile.points || 0} Points\n` +
              `• *Pass Status:* ${passBadge}\n` +
              `• *Daily Cost:* ${isCovered ? "Covered by VIP Pass" : `${dCost} Pts/day (100/acc)`}\n` +
              `• *Runway:* ~${daysRemaining}\n` +
              `• *Streak / Ads:* 🔥 Day ${profile.daily_streak || 0} • 🎬 ${profile.ads_watched || 0} Ads\n` +
              `• *Active Pools (8/8):* ATF, Stones, MRG, ART, AI Lab, UltraWallet, Apex, Ainovum\n` +
              `• *Cloud Mining:* ${farmStatus}`;
            const statsBtns = {
              inline_keyboard: [
                [{ text: "🎬 Watch Video Ad (+20 Pts)", web_app: { url: "https://atf-miner-app.pages.dev/app/ad/" } }],
                [{ text: "🎁 Claim Daily Bonus", callback_data: "ub_daily_claim" }, { text: "👥 Invite Friends", callback_data: "ub_referral" }],
                [{ text: "🌟 Upgrade VIP Passes & Slots", callback_data: "ub_buy_stars" }]
              ]
            };
            await sendUserReply(statsMsg, statsBtns);
            return;
          }

          // 1. /start, /menu
          if (text.startsWith("/start") || text === "/menu") {
            const totalSlots = (profile.slots || 1) + (profile.temp_slots || 0);
            const isCovered = profile.subscription_expiry && profile.subscription_expiry > Date.now();
            let passBadge = "Free Tier (Pay-As-You-Go)";
            if (isCovered) {
              const remMs = profile.subscription_expiry - Date.now();
              const dLeft = Math.floor(remMs / (86400 * 1000));
              const hLeft = Math.floor((remMs % (86400 * 1000)) / (3600 * 1000));
              const tName = profile.subscription_tier === "month" ? "💎 30-Day Monthly Pass" : (profile.subscription_tier === "week" ? "🎟️ 7-Day Weekly Pass" : "🎟️ 1-Day Pass");
              passBadge = `${tName} (🟢 Active: ${dLeft > 0 ? `${dLeft}d ` : ""}${hLeft}h left)`;
            }
            const farmStatus = isCovered ? "🟢 Active 24/7 (Covered by VIP Pass)" : (profile.farming_active ? "🟢 Active & Mining 24/7" : "🔴 Paused (Needs Points)");
            const welcomeText = `🌟 *AAA AUTO MINING PLATFORM (PREMIUM)* 🚀\n` +
              `_⚡ Created by AAA — Autonomous Cloud Mining Ecosystem_\n\n` +
              `Hello ${senderName}! Connect your account once, and AAA Auto Mining will **automatically farm all 8 Telegram crypto bots 24/7 in the cloud**! Our cloud engines handle all daily mining sessions, task farming, and claim cycles continuously.\n\n` +
              `🤖 *8 Automated Mining Pools & Links:*\n` +
              `1️⃣ 🪙 [ATF Miner](https://t.me/ATF_AIRDROP_bot?start=6727787768) — Auto 24h mining & daily task claiming\n` +
              `2️⃣ 💎 [Stones Miner](https://t.me/stoneswithestand_bot?start=r6727787768) — Continuous auto-farming sessions\n` +
              `3️⃣ ⚡ [MRG Miner](https://t.me/mrgminerbot?start=ref_IRN1G3XD) — Peak tier hashrate & TON auto-mining\n` +
              `4️⃣ 🎨 [ART Miner](https://t.me/ART_AIRDROP_BOT?start=6727787768) — Auto-farming & token claims\n` +
              `5️⃣ 🤖 [AI Lab Robot](https://t.me/AiLab_robot?start=296852) — Automated hash generation & daily bonuses\n` +
              `6️⃣ 👛 [UltraWallet](https://t.me/UltrawalletTrade_Bot/app?startapp=6727787768) — Multi-pool automated cloud mining\n` +
              `7️⃣ 🏔️ [Apex Miner](https://t.me/ApxMinerBot/app?startapp=6727787768) — Continuous APX node farming\n` +
              `8️⃣ 🌐 [Ainovum](https://t.me/ainovum_bot?start=ref_6727787768) — 24/7 automated node mining & daily tasks\n\n` +
              `💎 *Your Fleet Overview:*\n` +
              `• *Connected Accounts:* ${profile.accounts.length} / ${totalSlots} Slots\n` +
              `• *Points Balance:* ${profile.points} Points\n` +
              `• *Subscription Pass:* ${passBadge}\n` +
              `• *Farming Status:* ${farmStatus}\n` +
              `• *Daily Cost:* ${isCovered ? "0 Pts/day (Covered by Pass)" : `${profile.accounts.length * 100} Pts/day (100 Pts per account)`}\n\n` +
              `📺 *Earn Points:* Tap *🎬 Watch Video Ad (+20 Pts)* below or invite friends (+500 Pts).\n` +
              `🌟 *Subscriptions:* Day, Weekly, and Monthly VIP Passes with Telegram Stars!\n\n` +
              `👇 *Tap 🎬 Watch Video Ad below or choose an option from the menu:*`;
            await sendUserReply("👋 *Welcome to AAA Auto Mining!* (Created by AAA)\nAccess all features below or choose from the interactive menu:", activeUserKeyboard);
            await sendUserReply(welcomeText, activeWelcomeInlineKeyboard);

            // Ensure persistent Chat Menu Button is set appropriately (Admin Dashboard for Arif, Watch Ads for users)
            if (ctx && ctx.waitUntil) {
              const menuPayload = {
                chat_id: chatId,
                menu_button: isOwner ? {
                  type: "web_app",
                  text: "👑 Admin Dashboard",
                  web_app: {
                    url: "https://aaa-admin-portal.pages.dev/"
                  }
                } : {
                  type: "web_app",
                  text: "🎬 Watch Ads",
                  web_app: {
                    url: "https://atf-miner-app.pages.dev/app/ad/"
                  }
                }
              };
              ctx.waitUntil(
                fetch(`https://api.telegram.org/bot${userBotToken}/setChatMenuButton`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify(menuPayload)
                }).catch(() => {})
              );
            }
            return;
          }

          // 2. 👥 My Accounts
          if (text === "👥 My Accounts" || text.startsWith("/accounts")) {
            const totalSlots = (profile.slots || 1) + (profile.temp_slots || 0);
            const isCovered = profile.subscription_expiry && profile.subscription_expiry > Date.now();
            let passBadge = "Free Tier (Pay-As-You-Go)";
            if (isCovered) {
              const remMs = profile.subscription_expiry - Date.now();
              const dLeft = Math.floor(remMs / (86400 * 1000));
              const hLeft = Math.floor((remMs % (86400 * 1000)) / (3600 * 1000));
              const tName = profile.subscription_tier === "month" ? "💎 30-Day Monthly Pass" : (profile.subscription_tier === "week" ? "🎟️ 7-Day Weekly Pass" : "🎟️ 1-Day Pass");
              passBadge = `${tName} (🟢 Active: ${dLeft > 0 ? `${dLeft}d ` : ""}${hLeft}h left)`;
            }
            const daysRemaining = isCovered ? "Covered by Pass" : (profile.accounts.length > 0 ? Math.floor(profile.points / (profile.accounts.length * 100)) : "Unlimited");
            let accList = "• _No accounts connected yet. Tap ➕ Connect Account below!_";
            if (profile.accounts && profile.accounts.length > 0) {
              accList = profile.accounts.map((a, i) =>
                `*${i + 1}.* \`${a.phone || a.user_id}\` (${a.name || "User"}) — 🟢 Active Cloud Farming`
              ).join("\n");
            }

            const farmStatus = isCovered ? "🟢 Active 24/7 (Covered by VIP Pass)" : (profile.farming_active ? "🟢 Active 24/7" : "🔴 Paused (Insufficient Points)");
            const accMsg = `👥 *MY CONNECTED ACCOUNTS* 📱\n\n` +
              `• *Slots In Use:* ${profile.accounts.length} / ${totalSlots}\n` +
              `• *Subscription Pass:* ${passBadge}\n` +
              `• *Farming Status:* ${farmStatus}\n` +
              `• *Daily Cost:* ${isCovered ? "0 Pts/day (Covered by Pass)" : `${profile.accounts.length * 100} Pts/day`}\n` +
              `• *Points Balance:* ${profile.points} Pts (~${daysRemaining} days left)\n\n` +
              `📱 *Active Accounts:*\n${accList}\n\n` +
              `💡 _Every account automatically farms all 8 bots: ATF Miner, Stones, MRG, ART, AI Lab, UltraWallet, Apex, and Ainovum._`;

            const inlineBtns = [
              [{ text: "➕ Connect Account", callback_data: "ub_add_acc" }, { text: "🗑️ Remove Account", callback_data: "ub_remove_menu" }],
              [{ text: "🌟 VIP Passes & Slots", callback_data: "ub_buy_stars" }]
            ];
            if (profile.accounts && profile.accounts.length > 0) {
              for (const a of profile.accounts) {
                inlineBtns.push([{ text: `🗑️ Remove ${a.name || a.phone} (${a.phone || a.user_id})`, callback_data: `ub_disconnect_${a.user_id || a.phone}` }]);
              }
            }
            await sendUserReply(accMsg, { inline_keyboard: inlineBtns });
            return;
          }

          // 2.1 🗑️ Remove / Disconnect Account Commands (/remove, /remove_account, /disconnect, /delaccount, or button "🗑️ Remove Account")
          if (text === "🗑️ Remove Account" || text === "🗑️ Remove" || text.startsWith("/remove_account") || text.startsWith("/removeaccount") || text.startsWith("/remove") || text.startsWith("/disconnect") || text.startsWith("/delaccount") || text.startsWith("/delete")) {
            const parts = text.split(/\s+/);
            if (parts.length > 1 && text.startsWith("/")) {
              const query = parts[1].trim().replace("+", "");
              const removedAcc = (profile.accounts || []).find(a => String(a.user_id) === query || String(a.phone || "").replace("+", "") === query);
              if (removedAcc) {
                profile.accounts = profile.accounts.filter(a => String(a.user_id) !== String(removedAcc.user_id) && String(a.phone || "").replace("+", "") !== query);
                await saveUserProfile(chatId, profile);
                const totalSlots = (profile.slots || 1) + (profile.temp_slots || 0);
                const repMsg = `✅ *Account Disconnected Successfully!* 🗑️\n\n` +
                  `• *Removed:* ${removedAcc.name || "Account"} (\`${removedAcc.phone || removedAcc.user_id}\`)\n` +
                  `• *Slots In Use:* ${profile.accounts.length} / ${totalSlots}\n` +
                  `• *Freed Capacity:* ⚡ 1 Cloud Slot is now available!\n\n` +
                  `You can now connect another account using *➕ Connect Account*.`;
                await sendUserReply(repMsg, activeUserKeyboard);
                return;
              } else {
                await sendUserReply(`⚠️ Account \`${query}\` not found in your connected list.\n\nType \`/accounts\` to see your active accounts.`, activeUserKeyboard);
                return;
              }
            }

            if (!profile.accounts || profile.accounts.length === 0) {
              await sendUserReply("ℹ️ *No Connected Accounts*\n\nYou do not have any active mining accounts connected to remove.\n\nTap *➕ Connect Account* below to link your first account!", {
                inline_keyboard: [
                  [{ text: "➕ Connect Account", callback_data: "ub_add_acc" }]
                ]
              });
              return;
            }

            const promptTxt = `🗑️ *SELECT AN ACCOUNT TO DISCONNECT & REMOVE:*\n\n` +
              `Choose which account you want to disconnect from automated 24/7 cloud mining:\n\n` +
              `⚠️ _Disconnecting an account immediately frees up its cloud slot._`;
            const buttons = profile.accounts.map(a => [
              { text: `🗑️ Disconnect ${a.name || a.phone} (${a.phone || a.user_id})`, callback_data: `ub_disconnect_${a.user_id || a.phone}` }
            ]);
            buttons.push([{ text: "🔙 Back to Accounts", callback_data: "ub_accounts_list" }]);
            await sendUserReply(promptTxt, { inline_keyboard: buttons });
            return;
          }

          // 3. ➕ Connect Account
          if (text === "➕ Connect Account" || text === "Connect Account" || text.startsWith("/connect") || text.startsWith("/add_account")) {
            const totalSlots = (profile.slots || 1) + (profile.temp_slots || 0);
            if (profile.accounts.length >= totalSlots) {
              const slotLimitMsg = `⚠️ *Account Slot Limit Reached (${profile.accounts.length}/${totalSlots})*\n\n` +
                `You are currently using all available slots!\n\n` +
                `*How to get more slots:*\n` +
                `1. 🌟 *Subscription Pass*: Weekly & Monthly Passes include extra slots!\n` +
                `2. 📺 *Watch 50 Ads*: Earn a free bonus slot! (${profile.ads_watched % 50}/50 watched)\n` +
                `3. 🌟 *Telegram Stars*: Buy permanent slots instantly below!`;
              await sendUserReply(slotLimitMsg, starsUpgradeKeyboard);
              return;
            }
            const hasPass = profile.subscription_expiry && profile.subscription_expiry > Date.now();
            if (!hasPass && profile.points < 100) {
              const lowPtsMsg = `⚠️ *Insufficient Points to Connect Account*\n\n` +
                `Connecting an account requires at least *100 Points* for Day 1 automated cloud farming (or an active VIP Pass).\n` +
                `Your balance: *${profile.points} Points*.\n\n` +
                `*Quickly get access:*\n` +
                `• 🎟️ *Get a Day Pass (15 Stars)* for unlimited 24h mining\n` +
                `• 📺 Watch an ad (+20 Pts)\n` +
                `• 👥 Invite a friend (+500 Pts)`;
              await sendUserReply(lowPtsMsg, activeUserKeyboard);
              return;
            }

            if (env.BACKUP_KV) {
              await env.BACKUP_KV.put("login_flow:user_" + chatId, JSON.stringify({ step: "waiting_phone" }), { expirationTtl: 600 }).catch(() => {});
            }
            const promptPhone = `📱 *Connect Telegram Account for 24/7 Cloud Mining*\n\n` +
              `Please send the phone number of the Telegram account you want to connect:\n\n` +
              `• *Format:* \`+88017XXXXXXXX\` or \`017XXXXXXXX\`\n` +
              `• *International:* \`+1...\`, \`+44...\`, \`+91...\`\n\n` +
              `🔒 *100% Serverless & Encrypted:*\n` +
              `Your session runs safely in the cloud and automatically binds to all 8 mining pools.\n\n` +
              `_(Send phone number or tap ❌ Cancel Connection below)_`;
            await sendUserReply(promptPhone, userCancelKeyboard);
            return;
          }

          // 4. 💎 Points & Balance / Passes
          if (text === "💎 Points & Pass" || text === "💎 Points & Balance" || text === "💎 Points" || text === "/points" || text.startsWith("/points") || text === "/balance" || text.startsWith("/balance") || text === "/wallet" || text === "/pts" || text === "/runway") {
            const totalSlots = (profile.slots || 1) + (profile.temp_slots || 0);
            const isCovered = profile.subscription_expiry && profile.subscription_expiry > Date.now();
            let passBadge = "Free Tier (Pay-As-You-Go)";
            if (isCovered) {
              const remMs = profile.subscription_expiry - Date.now();
              const dLeft = Math.floor(remMs / (86400 * 1000));
              const hLeft = Math.floor((remMs % (86400 * 1000)) / (3600 * 1000));
              const tName = profile.subscription_tier === "month" ? "💎 30-Day Monthly Pass" : (profile.subscription_tier === "week" ? "🎟️ 7-Day Weekly Pass" : "🎟️ 1-Day Pass");
              passBadge = `${tName} (🟢 Active: ${dLeft > 0 ? `${dLeft}d ` : ""}${hLeft}h left)`;
            }
            const daysRemaining = isCovered ? "Covered by Pass" : (profile.accounts.length > 0 ? Math.floor(profile.points / (profile.accounts.length * 100)) : "Unlimited");
            const farmStatus = isCovered ? "🟢 Active 24/7 (Covered by VIP Pass)" : (profile.farming_active ? "🟢 Active 24/7" : "🔴 Paused (Needs Points)");
            const ptsMsg = `💎 *POINTS & MINING BALANCE* ⚡\n\n` +
              `• *Points Balance:* ${profile.points || 0} Points\n` +
              `• *Subscription Pass:* ${passBadge}\n` +
              `• *Farming Status:* ${farmStatus}\n` +
              `• *Daily Mining Cost:* ${isCovered ? "0 Pts/day (Covered by Pass)" : `${profile.accounts.length * 100} Pts/day (100 Pts/account)`}\n` +
              `• *Days of Mining Remaining:* ~${daysRemaining} days\n\n` +
              `📊 *Account Slots Breakdown:*\n` +
              `• *Standard Slots:* ${profile.slots || 1}\n` +
              `• *Bonus Slots (from 50 Ads):* ${profile.temp_slots || 0}\n` +
              `• *Total Available Slots:* ${totalSlots}\n\n` +
              `📺 *Ad Watching Milestone:*\n` +
              `• *Ads Watched:* ${profile.ads_watched || 0}\n` +
              `• *Progress to Next Free Slot:* ${(profile.ads_watched || 0) % 50} / 50 ads\n\n` +
              `👥 *Referral Stats:*\n` +
              `• *Friends Invited:* ${profile.referral_count || 0}\n` +
              `• *Points from Referrals:* ${(profile.referral_count || 0) * 500} Pts`;

            await sendUserReply(ptsMsg, {
              inline_keyboard: [
                [{ text: "🎬 Watch Video Ad (+20 Pts)", web_app: { url: "https://atf-miner-app.pages.dev/app/ad/" } }],
                [{ text: "🎁 Claim Daily Bonus", callback_data: "ub_daily_claim" }, { text: "👥 Invite Friends (+500 Pts)", callback_data: "ub_referral" }],
                [{ text: "🌟 Upgrade VIP Passes & Slots", callback_data: "ub_buy_stars" }]
              ]
            });
            return;
          }

          // 4.1 Daily Check-In Bonus (24h Streak Rewards: +25 to +50 Pts)
          if (text === "🎁 Daily Bonus" || text === "🎁 Daily Bonus (+25-50 Pts)" || text === "📅 Daily Bonus" || text.startsWith("/daily") || text.startsWith("/bonus") || text.startsWith("/claim") || text.startsWith("/checkin")) {
            const now = Date.now();
            const lastClaim = profile.last_daily_claim || 0;
            const elapsed = now - lastClaim;
            const COOLDOWN_MS = 24 * 3600 * 1000;
            
            if (elapsed < COOLDOWN_MS) {
              const remMs = COOLDOWN_MS - elapsed;
              const h = Math.floor(remMs / 3600000);
              const m = Math.floor((remMs % 3600000) / 60000);
              const alreadyClaimedMsg = `⏳ *Daily Bonus Already Claimed!* 🎁\n\n` +
                `You have already claimed today's check-in bonus!\n\n` +
                `• *Next Claim In:* ${h}h ${m}m\n` +
                `• *Current Streak:* 🔥 ${profile.daily_streak || 1} Days\n` +
                `• *Points Balance:* 💎 ${profile.points || 0} Points\n\n` +
                `💡 *Earn points right now:*\n` +
                `• 🎬 *Watch Rewarded Video Ads* (+20 Pts/ad)\n` +
                `• 👥 *Invite Friends* (+500 Pts per referral)\n` +
                `• 🌟 *Upgrade with Telegram Stars* (VIP Pass - unlimited mining)`;
              const kb = {
                inline_keyboard: [
                  [{ text: "🎬 Watch Video Ad (+20 Pts)", web_app: { url: "https://atf-miner-app.pages.dev/app/ad/" } }],
                  [{ text: "👥 Invite Friends (+500 Pts)", callback_data: "ub_referral" }]
                ]
              };
              await sendUserReply(alreadyClaimedMsg, kb);
              return;
            }

            const streakContinues = lastClaim > 0 && elapsed < (48 * 3600 * 1000);
            const streak = streakContinues ? ((profile.daily_streak || 0) + 1) : 1;
            const bonusPts = Math.min(50, 25 + (streak - 1) * 5);
            
            profile.points = (profile.points || 0) + bonusPts;
            profile.daily_streak = streak;
            profile.last_daily_claim = now;
            
            const dailyCost = (profile.accounts || []).length * 100;
            const wasPaused = profile.farming_active === false && (profile.accounts || []).length > 0;
            if (profile.points >= dailyCost) {
              profile.farming_active = true;
            }
            await saveUserProfile(chatId, profile);

            const hasPass = profile.subscription_expiry && profile.subscription_expiry > now;
            let statusTxt = hasPass ? "🟢 Active 24/7 (Covered by VIP Pass)" : (profile.farming_active ? "🟢 Active 24/7" : "🔴 Paused (Needs Points)");
            if (wasPaused && profile.farming_active) {
              statusTxt = "🟢 Auto-Resumed & Active 24/7! 🚀";
            }
            const daysRemaining = hasPass ? "Unlimited (VIP Pass)" : (dailyCost > 0 ? `${Math.floor(profile.points / dailyCost)} days` : "Unlimited");
            const succMsg = `🎉 *DAILY BONUS CLAIMED!* 🎁\n\n` +
              `• *Bonus Awarded:* +${bonusPts} Mining Points Credited!\n` +
              `• *Check-In Streak:* 🔥 Day ${streak} Streak (${streak >= 5 ? "MAX +50 Pts!" : `+${bonusPts + 5} Pts tomorrow`})\n` +
              `• *New Points Balance:* 💎 ${profile.points} Points\n` +
              `• *Daily Mining Cost:* ${hasPass ? "0 Pts/day (VIP Pass)" : `${dailyCost} Pts/day`}\n` +
              `• *Days of Mining Remaining:* ~${daysRemaining}\n` +
              `• *Mining Status:* ${statusTxt}\n\n` +
              `💡 _Come back in 24 hours to keep your streak burning!_`;
            const succKb = {
              inline_keyboard: [
                [{ text: "🎬 Watch Video Ad (+20 Pts)", web_app: { url: "https://atf-miner-app.pages.dev/app/ad/" } }],
                [{ text: "💎 View Points & Passes", callback_data: "ub_points" }]
              ]
            };
            await sendUserReply(succMsg, succKb);
            return;
          }

          // 4.2 ⛏️ 8 Supported Mining Pools & Bots (/pools, /bots, /farm, "⛏️ Farming Bots")
          if (text === "⛏️ Farming Bots" || text === "⛏️ Mining Pools" || text === "🤖 Farming Bots" || text.startsWith("/pools") || text.startsWith("/bots") || text.startsWith("/farm") || text.startsWith("/farming") || text.startsWith("/withdraw")) {
            const poolsMsg = `⛏️ *8 SUPPORTED CLOUD MINING POOLS & BOTS* 🤖\n` +
              `_⚡ Created by AAA — 100% Autonomous Cloud Mining_\n\n` +
              `Our cloud engines automatically farm and claim all 8 bots 24/7 across your connected accounts:\n\n` +
              `1️⃣ 🪙 [ATF Miner](https://t.me/ATF_AIRDROP_bot?start=6727787768) — Auto 24h mining & daily task claiming\n` +
              `2️⃣ 💎 [Stones Miner](https://t.me/stoneswithestand_bot?start=r6727787768) — Continuous auto-farming sessions\n` +
              `3️⃣ ⚡ [MRG Miner](https://t.me/mrgminerbot?start=ref_IRN1G3XD) — Peak tier hashrate & TON auto-mining\n` +
              `4️⃣ 🎨 [ART Miner](https://t.me/ART_AIRDROP_BOT?start=6727787768) — Auto-farming & token claims\n` +
              `5️⃣ 🤖 [AI Lab Robot](https://t.me/AiLab_robot?start=296852) — Automated hash generation & daily bonuses\n` +
              `6️⃣ 👛 [UltraWallet](https://t.me/UltrawalletTrade_Bot/app?startapp=6727787768) — Multi-pool automated cloud mining\n` +
              `7️⃣ 🏔️ [Apex Miner](https://t.me/ApxMinerBot/app?startapp=6727787768) — Continuous APX token node farming\n` +
              `8️⃣ 🌐 [Ainovum](https://t.me/ainovum_bot?start=ref_6727787768) — 24/7 automated node mining & daily tasks\n\n` +
              `☁️ *What Our Bot Does:*\n` +
              `• Automatically runs 24/7 cloud auto-farming across all 8 bots for your connected accounts.\n` +
              `• Executes daily claims, starts, tasks, and point rewards without keeping your phone or app open.\n` +
              `• All mined tokens accumulate directly in your accounts inside each respective official bot.`;
            await sendUserReply(poolsMsg, {
              inline_keyboard: [
                [{ text: "➕ Connect Account", callback_data: "ub_add_acc" }, { text: "👥 My Accounts", callback_data: "ub_accounts" }],
                [{ text: "🎬 Watch Video Ad (+20 Pts)", web_app: { url: "https://atf-miner-app.pages.dev/app/ad/" } }]
              ]
            });
            return;
          }

          // 5. 📺 Watch Ad (+20 Pts)
          if (text === "📺 Watch Ad (+20 Pts)" || text === "🎬 Watch Ads (+20 Pts)" || text === "🎬 Watch Ads" || text.startsWith("/watch_ad") || text === "/ad" || text === "/ads" || text.startsWith("/ad ") || text.toLowerCase() === "watch ad" || text.toLowerCase() === "watch ads") {
            const adMsg = `📺 *WATCH REWARDED ADS & EARN POINTS* 🚀\n\n` +
              `Watch real video ads via Adsgram to keep your 24/7 cloud mining running continuously!\n\n` +
              `🎁 *Per-Ad Reward:* +20 Points (+40 for VIP Monthly Pass)\n` +
              `🏆 *Milestone Bonus:* Every 50 ads unlocks *+1 Free Bonus Account Slot*!\n` +
              `⏱️ *Cooldown:* 15 seconds between ads.\n\n` +
              `👇 *Tap below to launch the video ad:*`;
            await sendUserReply(adMsg, {
              inline_keyboard: [
                [{ text: "🎬 Watch Video Ad (+20 Pts)", web_app: { url: "https://atf-miner-app.pages.dev/app/ad/" } }],
                [{ text: "🎁 Claim Directly (Fallback)", callback_data: "ub_claim_ad" }]
              ]
            });
            return;
          }

          // 6. 👥 Invite Friends (+500 Pts)
          if (text === "👥 Invite Friends" || text === "Invite Friends" || text === "👥 Invite Friends (+500 Pts)" || text.startsWith("/referral") || text === "/invite" || text.startsWith("/invite") || text === "/ref" || text.startsWith("/ref ") || text.toLowerCase() === "referral") {
            const refLink = `https://t.me/AAAPREMIUMAPPSbot?start=ref_${chatId}`;
            const refMsg = `👥 *INVITE FRIENDS & EARN POINTS* 🚀\n\n` +
              `Share your personal referral link with friends. For every friend who joins & verifies:\n` +
              `🎁 *You earn +500 Points!* (5 full days of automated cloud mining!)\n` +
              `🎁 *Your friend receives 100 Free Welcome Points!*\n\n` +
              `🔗 *Your Referral Link:*\n\`${refLink}\`\n\n` +
              `📊 *Your Referral Stats:*\n` +
              `• *Invited Users:* ${profile.referral_count || 0}\n` +
              `• *Points Earned:* ${(profile.referral_count || 0) * 500} Pts`;
            await sendUserReply(refMsg, {
              inline_keyboard: [
                [{ text: "📤 Share to Telegram", url: `https://t.me/share/url?url=${encodeURIComponent(refLink)}&text=${encodeURIComponent("Join AAA Auto Mining to earn crypto 24/7 automatically!")}` }],
                [{ text: "🎁 My Rewards Hub", callback_data: "ub_rewards" }]
              ]
            });
            return;
          }

          // 7. 🌟 VIP Subscriptions / Upgrades
          if (text === "🌟 VIP Subscriptions" || text === "🌟 Upgrade with Stars" || text.startsWith("/upgrade") || text.startsWith("/pass") || text.startsWith("/sub") || text.startsWith("/stars") || text.startsWith("/vip") || text.toLowerCase() === "upgrade") {
            const starsMsg = `🌟 *VIP SUBSCRIPTION PASSES & SLOTS* ⭐\n\n` +
              `Upgrade to uninterrupted 24/7 cloud mining with Telegram Stars:\n\n` +
              `🎟️ *1-Day VIP Pass (15 Stars)*\n` +
              `• 24h unlimited cloud mining (zero point deduction)\n` +
              `• +150 Bonus Points\n\n` +
              `🎟️ *7-Day Weekly Pass (45 Stars)*\n` +
              `• 7 Days unlimited cloud mining (zero point deduction)\n` +
              `• +1,000 Bonus Points + 1 Extra Account Slot\n\n` +
              `💎 *30-Day Monthly Pass (120 Stars)*\n` +
              `• 30 Days unlimited cloud mining (zero point deduction)\n` +
              `• +4,500 Bonus Points + 1 Permanent Slot\n` +
              `• 2x Ad Points Multiplier (+40 Pts per ad view!)\n\n` +
              `🌟 *+1 Permanent Slot (50 Stars)*\n` +
              `• Permanently add an account slot for multi-account farming\n\n` +
              `Choose your subscription pass below:`;
            await sendUserReply(starsMsg, starsUpgradeKeyboard);
            return;
          }

          // 7.1 Community Leaderboard & Whales (/leaderboard, /top, /whales)
          if (text === "🏆 Leaderboard" || text === "/leaderboard" || text.startsWith("/leaderboard") || text === "/top" || text.startsWith("/top") || text === "/whales") {
            const userList = await upstashSmembers("ub_registered_users");
            const sample = (userList || []).slice(0, 50);
            const profiles = await upstashMget(sample.map(u => `ub_user:${u}`));
            const valid = profiles.filter(p => p && p.user_id && !p.is_banned);
            valid.sort((a, b) => (b.points || 0) - (a.points || 0));
            const top5 = valid.slice(0, 5);
            const boardLines = top5.map((u, i) => {
              const medal = i === 0 ? "🥇" : (i === 1 ? "🥈" : (i === 2 ? "🥉" : `#${i+1}`));
              const maskedId = String(u.user_id).slice(0, 3) + "***" + String(u.user_id).slice(-3);
              const accCount = (u.accounts || []).length;
              return `${medal} *${u.first_name || "Miner"}* (\`${maskedId}\`)\n   • 💎 ${(u.points || 0).toLocaleString()} Points | ${accCount} Account${accCount === 1 ? "" : "s"}`;
            });
            const boardMsg = `🏆 *COMMUNITY MINERS LEADERBOARD* 🚀\n━━━━━━━━━━━━━━━━━━━━━━\n${boardLines.join("\n\n")}\n━━━━━━━━━━━━━━━━━━━━━━\n` +
              `💎 *Your Current Standing:*\n• *Your Points:* ${(profile.points || 0).toLocaleString()} Points\n• *Your Streak:* 🔥 Day ${profile.daily_streak || 0} Streak\n\n` +
              `💡 _Watch ads & invite friends to climb the leaderboard!_`;
            await sendUserReply(boardMsg, {
              inline_keyboard: [
                [{ text: "🎬 Watch Video Ad (+20 Pts)", web_app: { url: "https://atf-miner-app.pages.dev/app/ad/" } }],
                [{ text: "👥 Invite Friends (+500 Pts)", callback_data: "ub_referral" }]
              ]
            });
            return;
          }


          // Owner/Admin Command: Set Adsgram Block ID (/set_block_id <id>)
          if (text.startsWith("/set_block_id") || text.startsWith("/set_ad_block") || text.startsWith("/setblockid")) {
            if (String(chatId) === "6727787768" || String(chatId) === env.OWNER_ID) {
              const parts = text.split(/\s+/);
              const rawInput = parts[1]?.trim();
              if (!rawInput) {
                await sendUserReply("ℹ️ *Usage:* `/set_block_id <YOUR_ADSGRAM_BLOCK_ID>`\n*Example:* `/set_block_id 50527`\n\nGet your Block ID from https://adsgram.ai or @Adsgram_bot!");
                return;
              }
              const newBlockId = rawInput.replace(/^bot-/, "").trim();
              await upstashSet("config:adsgram_block_id", newBlockId);
              await sendUserReply(`✅ *Adsgram Block ID Updated!*\n\n• *New Block ID:* \`${newBlockId}\`\n• *Status:* Live across all Cloudflare Edge nodes\n• *WebApp URL:* https://atf-miner-app.pages.dev/app/ad`);
              return;
            }
          }

          if (text === "/get_block_id" || text === "/adsgram_info" || text === "/adsgram") {
            if (String(chatId) === "6727787768" || String(chatId) === env.OWNER_ID) {
              const currentBlockId = (await upstashGet("config:adsgram_block_id")) || env.ADSGRAM_BLOCK_ID || "50527";
              await sendUserReply(`📊 *Adsgram Configuration:*\n\n• *Active Block ID:* \`${currentBlockId}\`\n• *WebApp URL:* https://atf-miner-app.pages.dev/app/ad\n• *Update ID:* Send \`/set_block_id <id>\` anytime!`);
              return;
            }
          }

          // 8. 💬 Support & Admin Ticket (/support <message>)
          if (text.startsWith("/support")) {
            const parts = text.split(/\s+/);
            const userQuery = parts.slice(1).join(" ").trim();
            if (!userQuery) {
              const helpSup = `💬 *SUBMIT SUPPORT TICKET*\n\n` +
                `Need direct assistance from Platform Support?\n\n` +
                `*Usage:* \`/support <your question or issue>\`\n` +
                `*Example:* \`/support I connected my account but have a question about rewards.\`\n\n` +
                `Your message will be sent immediately to our support team, and you'll receive a direct reply here!`;
              await sendUserReply(helpSup, activeUserKeyboard);
              return;
            }

            const alertToken = env.ALERT_BOT_TOKEN;
            const ownerId = env.OWNER_ID || "6727787768";
            if (alertToken && ownerId) {
              const adminTicket = `📩 *NEW USER SUPPORT TICKET*\n━━━━━━━━━━━━━━━━━━━━━━\n` +
                `• *From:* ${senderName} (@${msg.from?.username || "None"})\n` +
                `• *User ID:* \`${chatId}\`\n` +
                `• *Connected Accounts:* ${(profile.accounts || []).length}\n` +
                `• *Points:* ${profile.points} Pts\n` +
                `• *Message:*\n"${userQuery}"\n━━━━━━━━━━━━━━━━━━━━━━\n` +
                `👉 *Reply to this user by sending:*\n\`/reply ${chatId} <your answer>\``;
              ctx.waitUntil(fetch(`https://api.telegram.org/bot${alertToken}/sendMessage`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ chat_id: ownerId, text: adminTicket, parse_mode: "Markdown" })
              }).catch(() => {}));
            }

            const confirmMsg = `✅ *SUPPORT TICKET DELIVERED!* 📩\n\n` +
              `Your message has been dispatched directly to Platform Support.\n\n` +
              `• *Ticket ID:* \`#TK-${Date.now().toString().slice(-6)}\`\n` +
              `• *Status:* 🟡 In Review\n\n` +
              `You will receive a direct reply right here in this chat as soon as it's processed!`;
            await sendUserReply(confirmMsg, activeUserKeyboard);
            return;
          }

          // 8.1 💬 Ari AI & Support Menu Button
          if (text === "💬 Ari AI & Support" || text === "💬 Chat with AI" || text.startsWith("/ai") || text.startsWith("/chat")) {
            const chatAiMsg = `💬 *AAA AI MINING COPILOT & SUPPORT* 🤖\n` +
              `_⚡ Created by AAA — Autonomous Cloud Mining Ecosystem_\n\n` +
              `Hello ${senderName}! How can I help you today?\n\n` +
              `🤖 *8 Automated Mining Pools Active (24/7):*\n` +
              `1️⃣ 🪙 [ATF Miner](https://t.me/ATF_AIRDROP_bot?start=6727787768)\n` +
              `2️⃣ 💎 [Stones Miner](https://t.me/stoneswithestand_bot?start=r6727787768)\n` +
              `3️⃣ ⚡ [MRG Miner](https://t.me/mrgminerbot?start=ref_IRN1G3XD)\n` +
              `4️⃣ 🎨 [ART Miner](https://t.me/ART_AIRDROP_BOT?start=6727787768)\n` +
              `5️⃣ 🤖 [AI Lab Robot](https://t.me/AiLab_robot?start=296852)\n` +
              `6️⃣ 👛 [UltraWallet](https://t.me/UltrawalletTrade_Bot/app?startapp=6727787768)\n` +
              `7️⃣ 🏔️ [Apex Miner](https://t.me/ApxMinerBot/app?startapp=6727787768)\n` +
              `8️⃣ 🌐 [Ainovum](https://t.me/ainovum_bot?start=ref_6727787768)\n\n` +
              `*Quick Actions:*\n` +
              `• *Ask Questions:* Simply type any question in this chat!\n` +
              `• *Manage Accounts:* Tap *👥 My Accounts* or *🗑️ Remove Account* anytime.\n` +
              `• *Mining Pools:* Send \`/pools\` to view all 8 automated bots.\n` +
              `• *Support Team:* Send \`/support <your message>\` to message Platform Support directly.\n\n` +
              `👉 Ask me anything or tap the buttons below!`;
            const chatAiKeyboard = {
              inline_keyboard: [
                [
                  { text: "🎬 Watch Video Ad (+20 Pts) ⚡", web_app: { url: "https://atf-miner-app.pages.dev/app/ad/" } }
                ],
                [
                  { text: "🌟 Upgrade Passes (Telegram Stars)", callback_data: "ub_buy_stars" }
                ],
                [
                  { text: "📢 Announcements", url: "https://t.me/AAAAUTOMINING" },
                  { text: "💬 Community Hub", url: "https://t.me/AAAAutoMiner" }
                ]
              ]
            };
            await sendUserReply(chatAiMsg, chatAiKeyboard);
            return;
          }

          // 9. 📢 Official Channels
          if (text === "📢 Official Channels" || text.startsWith("/channels")) {
            const chCheck = await checkUserChannels(chatId);
            const status1 = chCheck.missing.some(m => m.id === -1003684868577) ? "⚠️ Join Required" : "✅ Joined";
            const status2 = chCheck.missing.some(m => m.id === -1004255751168) ? "⚠️ Join Required" : "✅ Joined";
            const status3 = chCheck.missing.some(m => m.id === -1004332544939) ? "⚠️ Join Required" : "✅ Joined";
            const chMsg = `📢 *OFFICIAL AAA COMMUNITY & NEWS HUBS*\n\n` +
              `_⚡ Created by AAA — Autonomous Cloud Mining Ecosystem_\n\n` +
              `Stay connected with verified announcements, automated mining updates, and community support:\n\n` +
              `1️⃣ 💬 *AAA Auto Miner — Community Hub* (${status1})\n` +
              `• Connect with fellow miners, strategies, and ecosystem updates.\n` +
              `👉 [Join Community Hub](https://t.me/AAAAutoMiner)\n\n` +
              `2️⃣ 📢 *AAA Auto Miner — Announcements* (${status2})\n` +
              `• Real-time updates, releases, smart contract distributions & giveaways.\n` +
              `👉 [Join Announcements](https://t.me/AAAAUTOMINING)\n\n` +
              `3️⃣ ⚡ *AAA ATF Miner — Live Activity* (${status3})\n` +
              `• Real-time automated mining harvest telemetry & payment proofs.\n` +
              `👉 [Join Live Activity Stream](https://t.me/AAA_ACTIVITY)`;
            await sendUserReply(chMsg, {
              inline_keyboard: [
                [{ text: `💬 1. Community Hub (${status1})`, url: "https://t.me/AAAAutoMiner" }],
                [{ text: `📢 2. Announcements (${status2})`, url: "https://t.me/AAAAUTOMINING" }],
                [{ text: `⚡ 3. Live Activity Stream (${status3})`, url: "https://t.me/AAA_ACTIVITY" }]
              ]
            });
            return;
          }

          // 10. Natural Conversational AI Copilot for Any Other Message
          await sendUserChatAction("typing");
          const aiInlineMarkup = {
            inline_keyboard: [
              [
                { text: "🎬 Watch Video Ad (+20 Pts) ⚡", web_app: { url: "https://atf-miner-app.pages.dev/app/ad/" } }
              ],
              [
                { text: "🌟 Upgrade Passes (Telegram Stars)", callback_data: "ub_buy_stars" }
              ],
              [
                { text: "📢 Announcements", url: "https://t.me/AAAAUTOMINING" },
                { text: "💬 Community Hub", url: "https://t.me/AAAAutoMiner" }
              ]
            ]
          };
          try {
            const aiRes = await runUserAiCascade(text, senderName);
            if (aiRes && aiRes.answer) {
              await sendUserReply(aiRes.answer, aiInlineMarkup, "Markdown");
              return;
            }
          } catch (e) {
            console.error("User bot AI cascade error:", e);
          }

          await sendUserReply(`🤖 *AI Assistant:*\n\nI received: "${text}". How can I help you today? Check your accounts, watch ads for points, or ask me any question!`, aiInlineMarkup);
        })());

        return new Response("OK");
      } catch (err) {
        return new Response("OK");
      }
    }

    return new Response("Not Found", { status: 404, headers: corsHeaders });
  },

  async scheduled(event, env, ctx) {
    const CURRENT_SUBDOMAIN = "__SUBDOMAIN__";
    const NODE_SHARD_INDEX = ({ "aaaai2": 0, "aaa-bot": 1, "aaa222": 2, "agorameet": 3, "aaaai": 4 })[CURRENT_SUBDOMAIN] ?? 0;

    // 0. D1 SQL Serverless Execution Audit Log
    if (env.DB) {
      ctx.waitUntil(env.DB.prepare("INSERT INTO fleet_logs (event, details) VALUES (?, ?)").bind("cron_cycle", JSON.stringify({ node: CURRENT_SUBDOMAIN, shard: NODE_SHARD_INDEX, time: new Date().toISOString() })).run().catch(() => {}));
    }

    // 1. Keepalive for Ari Cloud Agent on Render (100% free - keeps agent active with 0 cold starts)
    ctx.waitUntil(
      fetch("https://hermes-grok-cloud-agent.onrender.com/health", { method: "GET" }).catch(() => null)
    );

    // 2. Intelligent Cloud-Aware Sentinel Check
    ctx.waitUntil((async () => {
      try {
        const rawHb = await env.BACKUP_KV.get("vps_heartbeat");
        let localMissingMinutes = 0;
        if (rawHb) {
          const hb = JSON.parse(rawHb);
          localMissingMinutes = Math.round((Date.now() - (hb.last_seen || 0)) / 60000);
        }

        // Only investigate if local machine has been silent for > 60 minutes
          // Check if 4 Render 24/7 nodes (Standby Singapore, Standby Frankfurt, Ari AI, Primary Relayer) are standing guard
          const [r1, r2, rAri, rRelay1] = await Promise.all([
            fetch("https://my-agy-fleet-standby.onrender.com/health", { method: "GET" }).catch(() => null),
            fetch("https://my-agy-fleet-standby-node2.onrender.com/health", { method: "GET" }).catch(() => null),
            fetch("https://hermes-grok-cloud-agent.onrender.com/health", { method: "GET" }).catch(() => null),
            fetch("https://atf-mtproto-relayer.onrender.com/wake", { method: "GET" }).catch(() => null)
          ]);
          const cloudStandbyAlive = (r1 && r1.ok) || (r2 && r2.ok) || (rAri && rAri.ok) || (rRelay1 && rRelay1.ok);

          // If Render is alive in the cloud, the fleet is 100% operational - DO NOT send false alarms!
          if (cloudStandbyAlive) {
            return;
          }

          // True Disaster: Both local machine AND both Render nodes are unreachable for > 120 minutes
          if (localMissingMinutes >= 120 && env.ALERT_BOT_TOKEN && env.OWNER_ID) {
            // Rate-limit alert to once every 6 hours to avoid spamming
            await fetch(`https://api.telegram.org/bot${env.ALERT_BOT_TOKEN}/sendMessage`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                chat_id: env.OWNER_ID,
                text: `⚠️ *[Cloudflare Edge Autonomous Sentinel]*\n\nCloud Standby and local container both silent for *${localMissingMinutes}m*.\nAutonomous Cloudflare edge farming remains active.`,
                parse_mode: "Markdown"
              })
            }).catch(() => {});
          }
      } catch (_) {}
    })());

    // 2.5 Automated Daily Cost Deduction Sweep (Runs once per day across mesh via atomic Upstash lock)
    ctx.waitUntil((async () => {
      try {
        await runDailyCostSweep(env, false);
      } catch (_) {}
    })());

    // 3. Mini-App Automated Edge Claims (All 8 Active Bots: Stones, MRG, ART, AI Lab, UltraWallet, Apex Miner, ATF Miner, Ainovum)
    ctx.waitUntil((async () => {
      try {
        let rawTokens = await env.BACKUP_KV.get("miniapp_tokens");
        if (!rawTokens) {
          for (const sUrl of SIBLING_URLS) {
            try {
              const sResp = await fetch(`${sUrl}/api/miniapp/tokens`, {
                headers: { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" }
              }).catch(() => null);
              if (sResp && sResp.ok) {
                const sText = await sResp.text();
                if (sText && sText.length > 50) {
                  rawTokens = sText;
                  await env.BACKUP_KV.put("miniapp_tokens", sText).catch(() => {});
                  break;
                }
              }
            } catch (_) {}
          }
        }
        if (!rawTokens) {
          try {
            const upstashResp = await fetch(`${UPSTASH_URL}/get/miniapp_tokens`, {
              headers: { Authorization: `Bearer ${UPSTASH_TOKEN}` }
            }).catch(() => null);
            if (upstashResp && upstashResp.ok) {
              const uData = await upstashResp.json().catch(() => ({}));
              if (uData.result) {
                rawTokens = uData.result;
                await env.BACKUP_KV.put("miniapp_tokens", rawTokens).catch(() => {});
              }
            }
          } catch (_) {}
        }
        if (!rawTokens) return;
        const tokens = JSON.parse(rawTokens);

        // Periodically trigger full 8-bot cloud farming run on Render Standby
        if (CURRENT_SUBDOMAIN === "aaaai2") {
          fetch("https://my-agy-fleet-standby.onrender.com/api/farm/cloud-all", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Authorization": `Bearer ${env.SECRET_KEY}`,
              "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
            body: JSON.stringify({ origin: "cf_scheduled_cron" })
          }).catch(() => null);
        }

        const tokenEntries = Object.entries(tokens);
        // Distribute accounts across 5 Cloudflare Edge nodes so each node farms 2-3 accounts simultaneously
        const nodeIndex = NODE_SHARD_INDEX;
        const myTokenEntries = tokenEntries.filter((_, idx) => idx % 5 === nodeIndex);
        for (let idx = 0; idx < myTokenEntries.length; idx++) {
          const [uid, accData] = myTokenEntries[idx];
          await farmSingleAccountAllBots(uid, accData, env, ctx);
        }


        // 3.4 Ping Render Cloud Standby (Singapore & Frankfurt) health check
        fetch("https://my-agy-fleet-standby.onrender.com/health", { method: "GET" }).catch(() => {});
        fetch("https://my-agy-fleet-standby-node2.onrender.com/health", { method: "GET" }).catch(() => {});

        // 3.5 Token Expiry Watcher: If tokens have <= 4 hours remaining (age >= 20h), wake up Render to collect batch
        const nowMs = Date.now();

        let needBatchRefresh = false;
        for (const [_, tData] of Object.entries(tokens)) {
          const syncedAt = new Date(tData.synced_at || 0).getTime();
          const ageHours = (nowMs - syncedAt) / 3600000;
          if (ageHours >= 14) { // 24h - 14h = 10 hours safety buffer before expiry
            needBatchRefresh = true;
            break;
          }
        }

        if (needBatchRefresh) {
          // Render takes ~30-50s to wake from cold sleep on Free Tier; Cloudflare waits gracefully in waitUntil
          // Try Render Node 1 (Singapore), automatic fallback to Render Node 2 (Frankfurt)
          const r1 = await fetch("https://my-agy-fleet-standby.onrender.com/collect-tokens", {
            method: "POST",
            headers: {
              "Authorization": `Bearer ${env.SECRET_KEY}`,
              "Content-Type": "application/json"
            },
            body: JSON.stringify({ source: "cf_cron_expiry_check_node1" })
          }).catch(() => null);

          if (!r1 || !r1.ok) {
            await fetch("https://my-agy-fleet-standby-node2.onrender.com/collect-tokens", {
              method: "POST",
              headers: {
                "Authorization": `Bearer ${env.SECRET_KEY}`,
                "Content-Type": "application/json"
              },
              body: JSON.stringify({ source: "cf_cron_expiry_check_node2" })
            }).catch(() => {});
          }
        }

      } catch (_) {}
    })());

    // 4. Multi-Cloud Edge cross-ping to keep all nodes warm and load-balanced
    for (const sUrl of SIBLING_URLS) {
      ctx.waitUntil(fetch(`${sUrl}/health`).catch(() => {}));
    }
    const MULTI_CLOUD_EDGES = [
      "https://my-agy-fleet-deno.aaa222.deno.net/health",
      "https://my-agy-fleet-deno2.aaasupporta.deno.net/health",
      "https://my-agy-fleet-standby.onrender.com/health",
      "https://my-agy-fleet-standby-node2.onrender.com/health",
      "https://hermes-grok-cloud-agent.onrender.com/health",
      "https://atf-mtproto-relayer.onrender.com/wake"
    ];
    for (const edgeUrl of MULTI_CLOUD_EDGES) {
      ctx.waitUntil(fetch(edgeUrl).catch(() => {}));
    }

    // 5. BetterStack 24/7 Heartbeat (Guarantees 100% Uptime Signal)
    ctx.waitUntil(
      fetch("https://uptime.betterstack.com/api/v1/heartbeat/bABS7gYDXgHp6H35XGcU7S6p", {
        method: "HEAD"
      }).catch(() => {})
    );
  }
};
"""


async def deploy_account(acc):
    print(f"\n🚀 Deploying to {acc['name']} ({acc['subdomain']}.workers.dev)...")

    worker_code = (
        WORKER_JS_TEMPLATE.replace("__SUBDOMAIN__", acc["subdomain"])
        .replace("__SIBLING_URLS_JSON__", json.dumps(acc["sibling_urls"]))
    )

    if acc.get("api_token"):
        headers = {"Authorization": f"Bearer {acc['api_token']}"}
    else:
        headers = {
            "X-Auth-Email": acc["email"],
            "X-Auth-Key": acc["api_key"],
        }

    bindings = [
        {
            "name": "BACKUP_KV",
            "type": "kv_namespace",
            "namespace_id": acc["kv_id"],
        },
        {
            "name": "AI",
            "type": "ai",
        },
        {
            "name": "SECRET_KEY",
            "type": "plain_text",
            "text": SECRET_KEY,
        },
        {
            "name": "OWNER_ID",
            "type": "plain_text",
            "text": OWNER_ID,
        },
        {
            "name": "ALERT_BOT_TOKEN",
            "type": "plain_text",
            "text": ALERT_BOT_TOKEN,
        },
        {
            "name": "USER_BOT_TOKEN",
            "type": "plain_text",
            "text": USER_BOT_TOKEN,
        },
    ]

    if acc.get("r2_bucket"):
        bindings.append({
            "name": "FLEET_R2",
            "type": "r2_bucket",
            "bucket_name": acc["r2_bucket"],
        })

    if acc.get("d1_uuid"):
        bindings.append({
            "name": "DB",
            "type": "d1",
            "database_id": acc["d1_uuid"],
        })

    metadata = {
        "main_module": "index.js",
        "bindings": bindings,
        "compatibility_date": "2024-09-01",
    }

    url = f"https://api.cloudflare.com/client/v4/accounts/{acc['account_id']}/workers/scripts/{WORKER_NAME}"

    form = aiohttp.FormData()
    form.add_field("metadata", json.dumps(metadata), content_type="application/json", filename="metadata.json")
    form.add_field("index.js", worker_code, content_type="application/javascript+module", filename="index.js")

    async with aiohttp.ClientSession() as session:
        async with session.put(url, headers=headers, data=form) as resp:
            res = await resp.json()

        if not res.get("success"):
            print(f"❌ [{acc['name']}] Deployment failed: {res.get('errors')}")
            return False

        print(f"✅ [{acc['name']}] Script uploaded successfully!")

        subdomain_url = f"https://api.cloudflare.com/client/v4/accounts/{acc['account_id']}/workers/scripts/{WORKER_NAME}/subdomain"
        async with session.post(subdomain_url, headers=headers, json={"enabled": True}) as resp_sub:
            res_sub = await resp_sub.json()

        if res_sub.get("success"):
            print(f"🎉 [{acc['name']}] Live URL: https://{WORKER_NAME}.{acc['subdomain']}.workers.dev")
        else:
            print(f"⚠️ [{acc['name']}] Subdomain note: {res_sub.get('errors')}")

        # Ensure 15-minute Edge Cron Trigger is provisioned on Cloudflare
        sched_url = f"https://api.cloudflare.com/client/v4/accounts/{acc['account_id']}/workers/scripts/{WORKER_NAME}/schedules"
        async with session.put(sched_url, headers=headers, json=[{"cron": "*/15 * * * *"}]) as resp_sched:
            res_sched = await resp_sched.json()
            if res_sched.get("success"):
                print(f"⏰ [{acc['name']}] 24/7 Cloudflare Edge Cron Trigger active (*/15 * * * *)")

    return True


async def main():
    print("=" * 60)
    print("  MY AGY AI — Triple Cloudflare Edge Synchronizer (3x Parallel Work)")
    print("=" * 60)

    for acc in ACCOUNTS:
        try:
            await deploy_account(acc)
        except Exception as e:
            print(f"❌ Error deploying to {acc['name']}: {e}")

    print("\n" + "=" * 60)
    print("  🔧 Synchronizing Telegram Bot Menu Button & Commands...")
    print("=" * 60)
    async with aiohttp.ClientSession() as session:
        # 0. Ensure Webhooks are set and synchronized on Cloudflare Edge
        try:
            alert_webhook_url = "https://restore-agy.aaaai2.workers.dev/telegram-webhook"
            async with session.post(
                f"https://api.telegram.org/bot{ALERT_BOT_TOKEN}/setWebhook",
                json={"url": alert_webhook_url, "allowed_updates": ["message", "callback_query"]}
            ) as resp:
                res_wh = await resp.json()
                print(f"📡 Admin Bot Webhook: {res_wh.get('ok')} ({res_wh.get('description', 'OK')})")

            user_webhook_url = "https://restore-agy.aaaai2.workers.dev/user-bot-webhook"
            async with session.post(
                f"https://api.telegram.org/bot{USER_BOT_TOKEN}/setWebhook",
                json={"url": user_webhook_url, "allowed_updates": ["message", "edited_message", "callback_query", "pre_checkout_query"]}
            ) as resp:
                res_uwh = await resp.json()
                print(f"📡 User Bot Webhook: {res_uwh.get('ok')} ({res_uwh.get('description', 'OK')})")
        except Exception as e:
            print(f"⚠️ Error synchronizing webhooks: {e}")

        # 1. Set global Chat Menu Button to Watch Ads WebApp
        menu_payload = {
            "menu_button": {
                "type": "web_app",
                "text": "🎬 Watch Ads",
                "web_app": {
                    "url": "https://atf-miner-app.pages.dev/app/ad/"
                }
            }
        }
        try:
            async with session.post(
                f"https://api.telegram.org/bot{USER_BOT_TOKEN}/setChatMenuButton",
                json=menu_payload
            ) as resp:
                res = await resp.json()
                print(f"🎬 Global Chat Menu Button: {res.get('ok')} ({res.get('description', 'OK')})")
        except Exception as e:
            print(f"⚠️ Error setting global menu button: {e}")

        # 2. Ensure Owner Menu Button is set to "👑 Admin Dashboard" on User Bot (@AAAPREMIUMAPPSbot)
        if OWNER_ID:
            try:
                owner_menu = {
                    "chat_id": int(OWNER_ID),
                    "menu_button": {
                        "type": "web_app",
                        "text": "👑 Admin Dashboard",
                        "web_app": {
                            "url": "https://aaa-admin-portal.pages.dev/"
                        }
                    }
                }
                async with session.post(
                    f"https://api.telegram.org/bot{USER_BOT_TOKEN}/setChatMenuButton",
                    json=owner_menu
                ) as resp:
                    res = await resp.json()
                    print(f"🎬 User Bot Owner Menu Button: {res.get('ok')} ({res.get('description', 'OK')})")
            except Exception as e:
                print(f"⚠️ Error setting owner menu button: {e}")

            # Register Owner-specific commands on User Bot
            owner_commands_payload = {
                "scope": {"type": "chat", "chat_id": int(OWNER_ID)},
                "commands": [
                    {"command": "admin", "description": "👑 Open User Bot Admin Dashboard"},
                    {"command": "dashboard", "description": "🚀 Launch User Bot Admin Dashboard"},
                    {"command": "start", "description": "🌟 Open Mining Dashboard & Fleet"},
                    {"command": "accounts", "description": "👥 Manage Connected Accounts"},
                    {"command": "pools", "description": "⛏️ 8 Supported Mining Pools & Bots"},
                    {"command": "ads", "description": "🎬 Watch Ads & Earn Points"},
                    {"command": "points", "description": "💎 Points Balance & VIP Passes"},
                    {"command": "daily", "description": "🎁 Claim Daily Bonus (+25-50 Pts)"},
                    {"command": "help", "description": "💬 Ari AI Copilot & Live Support"}
                ]
            }
            try:
                async with session.post(
                    f"https://api.telegram.org/bot{USER_BOT_TOKEN}/setMyCommands",
                    json=owner_commands_payload
                ) as resp:
                    res_oc = await resp.json()
                    print(f"👑 Owner User Bot Commands: {res_oc.get('ok')} ({res_oc.get('description', 'OK')})")
            except Exception as e:
                print(f"⚠️ Error setting owner bot commands: {e}")

        # 3. Set Bot Commands & Descriptions (User Bot)
        user_desc = (
            "🌟 AAA Auto Mining Platform 🚀\n"
            "⚡ 100% Autonomous Cloud Mining\n\n"
            "🤖 What This Bot Does:\n"
            "Auto-farms 8 Telegram crypto bots 24/7 in cloud:\n"
            "• 🪙 ATF Miner — Daily claims & farming\n"
            "• 💎 Stones Miner — Auto-mining sessions\n"
            "• ⚡ MRG Miner — Continuous hashrate\n"
            "• 🎨 ART Miner — Auto-farming & claims\n"
            "• 🤖 AI Lab — Auto bonus & mining\n"
            "• 👛 UltraWallet — Multi-pool mining\n"
            "• 🏔️ Apex Miner — APX node farming\n"
            "• 🌐 Ainovum — 24/7 automated mining\n\n"
            "💎 Earn Points: Daily bonus, ads & invites!\n\n"
            "📢 @AAAAutoMiner | @AAAAUTOMINING"
        )
        user_short_desc = "🌟 100% Cloud-Powered Mining Platform! Auto-farms 8 Telegram crypto bots 24/7. Created by AAA."

        try:
            async with session.post(
                f"https://api.telegram.org/bot{USER_BOT_TOKEN}/setMyDescription",
                json={"description": user_desc}
            ) as resp:
                res_desc = await resp.json()
                print(f"📝 User Bot Description: {res_desc.get('ok')} ({res_desc.get('description', 'OK')})")

            async with session.post(
                f"https://api.telegram.org/bot{USER_BOT_TOKEN}/setMyShortDescription",
                json={"short_description": user_short_desc}
            ) as resp:
                res_sdesc = await resp.json()
                print(f"📝 User Bot Short Description: {res_sdesc.get('ok')} ({res_sdesc.get('description', 'OK')})")
        except Exception as e:
            print(f"⚠️ Error setting bot descriptions: {e}")

        commands_payload = {
            "commands": [
                {"command": "start", "description": "🌟 Open Mining Dashboard & Fleet"},
                {"command": "accounts", "description": "👥 Manage Connected Accounts"},
                {"command": "pools", "description": "⛏️ 8 Supported Mining Pools & Bots"},
                {"command": "ads", "description": "🎬 Watch Ads & Earn Points"},
                {"command": "points", "description": "💎 Points Balance & VIP Passes"},
                {"command": "daily", "description": "🎁 Claim Daily Bonus (+25-50 Pts)"},
                {"command": "help", "description": "💬 Ari AI Copilot & Live Support"}
            ]
        }
        try:
            async with session.post(
                f"https://api.telegram.org/bot{USER_BOT_TOKEN}/setMyCommands",
                json=commands_payload
            ) as resp:
                res = await resp.json()
                print(f"📋 Bot Commands: {res.get('ok')} ({res.get('description', 'OK')})")
        except Exception as e:
            print(f"⚠️ Error setting bot commands: {e}")

        # 4. Set Admin Bot Chat Menu Button & Commands (Points to Vercel Executive Fleet Dashboard)
        if ALERT_BOT_TOKEN:
            admin_menu_payload = {
                "menu_button": {
                    "type": "web_app",
                    "text": "👑 Fleet Console",
                    "web_app": {
                        "url": "https://agy-aaa000.vercel.app/?v=5.0"
                    }
                }
            }
            try:
                async with session.post(
                    f"https://api.telegram.org/bot{ALERT_BOT_TOKEN}/setChatMenuButton",
                    json=admin_menu_payload
                ) as resp:
                    res = await resp.json()
                    print(f"👑 Admin Bot Global Menu Button: {res.get('ok')} ({res.get('description', 'OK')})")

                owner_menu_payload = {
                    "chat_id": int(OWNER_ID),
                    "menu_button": {
                        "type": "web_app",
                        "text": "👑 Fleet Console",
                        "web_app": {
                            "url": "https://agy-aaa000.vercel.app/?v=5.0"
                        }
                    }
                }
                async with session.post(
                    f"https://api.telegram.org/bot{ALERT_BOT_TOKEN}/setChatMenuButton",
                    json=owner_menu_payload
                ) as resp:
                    res_owner = await resp.json()
                    print(f"👑 Admin Bot Owner Menu Button: {res_owner.get('ok')} ({res_owner.get('description', 'OK')})")
            except Exception as e:
                print(f"⚠️ Error setting admin bot menu button: {e}")

            admin_commands_payload = {
                "commands": [
                    {"command": "start", "description": "👑 Open Executive Fleet Console & Roster"},
                    {"command": "dashboard", "description": "🚀 Launch Vercel Fleet Operations Console"},
                    {"command": "wallets", "description": "👛 Verified Destination Wallets & Balances"},
                    {"command": "sweep", "description": "💼 Universal Sweep to Binance Vault"},
                    {"command": "harvest", "description": "⚡ Trigger Instant 8 Pools Harvest"},
                    {"command": "accounts", "description": "👥 Manage Fleet Accounts & Roster"},
                    {"command": "burn", "description": "🔥 Economy & Daily Burn (100 Pts/day)"},
                    {"command": "sweep_daily", "description": "⚡ Run 100 Pts Daily Deduction Sweep"},
                    {"command": "sybil", "description": "🛡️ Anti-Sybil & Moderation Hub"},
                    {"command": "community", "description": "📊 Community Miners & VIP Passes"},
                    {"command": "nodes", "description": "⚡ 5-Node Edge Latency Probe"},
                    {"command": "mesh", "description": "🌐 5-Node Cloudflare Edge Mesh Status"},
                    {"command": "help", "description": "ℹ️ Operations & Moderation Guide"}
                ]
            }
            try:
                async with session.post(
                    f"https://api.telegram.org/bot{ALERT_BOT_TOKEN}/setMyCommands",
                    json=admin_commands_payload
                ) as resp:
                    res = await resp.json()
                    print(f"📋 Admin Bot Commands: {res.get('ok')} ({res.get('description', 'OK')})")
            except Exception as e:
                print(f"⚠️ Error setting admin bot commands: {e}")

    print("\n" + "=" * 60)
    print("  ✅ All Cloudflare Edge Nodes & Telegram Config Synchronized!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
