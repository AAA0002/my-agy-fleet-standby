/**
 * AAA ATF Miner Waterfall & Downside Ad Controller
 * Multi-Provider Banner Ecosystem & Dynamic Real-Time Refresh Engine
 * Supports: A-Ads (Adaptive & 300x250), RichAds TMA Native, HilltopAds MultiTag A/B, VAST 3.0, OnClickA, Adsterra (7 isolated formats)
 */
(function(global) {
  'use strict';

  let isRefreshing = false;
  let lastRefreshTime = 0;

  function updateVisualIndicator(status) {
    const dot = document.getElementById('downside-refresh-dot');
    const label = document.getElementById('downside-refresh-label');
    if (!dot || !label) return;

    if (status === 'refreshing') {
      dot.style.background = '#f59e0b'; // Amber
      dot.style.boxShadow = '0 0 8px #f59e0b';
      label.textContent = 'Refreshing Banners...';
      label.style.color = '#fcd34d';
    } else if (status === 'done') {
      dot.style.background = '#10b981'; // Emerald
      dot.style.boxShadow = '0 0 8px #10b981';
      const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      label.textContent = `Ads Updated (${timeStr})`;
      label.style.color = '#a7f3d0';
      setTimeout(() => {
        if (label) {
          label.textContent = 'Sponsor Banners Live';
          label.style.color = '#e2e8f0';
          dot.style.boxShadow = 'none';
        }
      }, 4000);
    }
  }

  function refreshDownsideAds(force = false) {
    const now = Date.now();
    // Debounce rapid repeated calls within 1.5s unless forced
    if (!force && now - lastRefreshTime < 1500) {
      return;
    }
    lastRefreshTime = now;

    console.log('[Waterfall] Refreshing all downside ads and sponsor units with fresh creatives...');
    updateVisualIndicator('refreshing');

    // 1. Refresh A-Ads Adaptive Unit (ID 2455341)
    try {
      const aadsBox = document.getElementById('aads-box');
      const oldAads = document.getElementById('a-ads-frame');
      if (aadsBox && oldAads) {
        const newFrame = document.createElement('iframe');
        newFrame.id = 'a-ads-frame';
        newFrame.setAttribute('data-aa', '2455341');
        newFrame.style.cssText = 'border:0; padding:0; width:100%; max-width:320px; height:60px; overflow:hidden; background-color:transparent;';
        newFrame.setAttribute('loading', 'eager');
        newFrame.src = `https://acceptable.a-ads.com/2455341/?size=Adaptive&_t=${now}`;
        aadsBox.replaceChild(newFrame, oldAads);
        console.log('[Waterfall] A-Ads Adaptive banner refreshed');
      }
    } catch (e) {
      console.warn('[Waterfall] A-Ads Adaptive refresh notice:', e);
    }

    // 1b. Refresh Crypto Sponsor 300x250 Unit (ID 2455341)
    try {
      const cryptoBox = document.getElementById('crypto-sponsor-box');
      const oldCrypto = document.getElementById('crypto-sponsor-frame');
      if (cryptoBox && oldCrypto) {
        const newFrame = document.createElement('iframe');
        newFrame.id = 'crypto-sponsor-frame';
        newFrame.setAttribute('data-aa', '2455341');
        newFrame.style.cssText = 'border:0; padding:0; width:300px; height:250px; overflow:hidden; background-color:transparent;';
        newFrame.setAttribute('loading', 'eager');
        newFrame.src = `https://acceptable.a-ads.com/2455341/?size=300x250&_t=${now}`;
        cryptoBox.replaceChild(newFrame, oldCrypto);
        console.log('[Waterfall] Crypto Sponsor 300x250 banner refreshed');
      }
    } catch (e) {
      console.warn('[Waterfall] Crypto Sponsor refresh notice:', e);
    }

    // 2. Refresh RichAds TMA Native Controller
    try {
      const richTarget = document.getElementById('richads-target');
      if (richTarget) {
        richTarget.innerHTML = '';
      }
      if (typeof TelegramAdsController !== 'undefined') {
        try {
          const richController = new TelegramAdsController();
          richController.initialize({
            pubId: "1021343",
            appId: "8896"
          });
          window.TelegramAdsController = richController;
          console.log('[Waterfall] RichAds TMA controller re-initialized');
        } catch (e) {
          console.warn('[Waterfall] RichAds TMA init notice:', e);
        }
      }
    } catch (e) {
      console.warn('[Waterfall] RichAds refresh notice:', e);
    }

    // 3. Refresh HilltopAds Silent VAST 3.0 & Google IMA Video Feed
    try {
      if (typeof window.initSilentVastPlayer === 'function') {
        window.initSilentVastPlayer(true);
      }
    } catch (e) {
      console.warn('[Waterfall] VAST video rotation notice:', e);
    }

    // 4. Refresh HilltopAds MultiTag Zone A (Zone 7428545)
    try {
      const zoneA = document.getElementById('hilltop-zone-a');
      if (zoneA) {
        zoneA.innerHTML = '';
        const scriptA = document.createElement('script');
        scriptA.src = `https://candid-revenue.com/b.XcVfsXdJGqlU0GYxWAcS/IekmO9YuEZHULlCkFPqT/cC0LM/jtgH1fNbDbUYt/NQzjQWy/O/DTUI0ZO-Qn?_t=${now}`;
        scriptA.async = true;
        scriptA.referrerPolicy = 'no-referrer-when-downgrade';
        zoneA.appendChild(scriptA);
        console.log('[Waterfall] HilltopAds Zone A re-injected');
      }
    } catch (e) {
      console.warn('[Waterfall] HilltopAds Zone A notice:', e);
    }

    // 5. Refresh HilltopAds MultiTag Zone B (Zone 7428533)
    try {
      const zoneB = document.getElementById('hilltop-zone-b');
      if (zoneB) {
        zoneB.innerHTML = '';
        const scriptB = document.createElement('script');
        scriptB.src = `https://candid-revenue.com/b/X/VTsnd.Gxlv0nYAW/co/WeXmV9_u_ZQUulqktPHT/cY0hM/jmg/1vMlztMptqN/z/QXyfOCD/UCzKNmwW?_t=${now}`;
        scriptB.async = true;
        scriptB.referrerPolicy = 'no-referrer-when-downgrade';
        zoneB.appendChild(scriptB);
        console.log('[Waterfall] HilltopAds Zone B re-injected');
      }
    } catch (e) {
      console.warn('[Waterfall] HilltopAds Zone B notice:', e);
    }

    // 6. Refresh OnClickA Display Banner (Spot 464181)
    try {
      const onclickaBox = document.getElementById('onclicka-ad');
      if (onclickaBox) {
        onclickaBox.innerHTML = '';
        const onclickaScript = document.createElement('script');
        onclickaScript.async = true;
        onclickaScript.src = `https://js.wpadmngr.com/static/adManager.js?_t=${now}`;
        onclickaScript.setAttribute('data-admpid', '464181');
        onclickaBox.appendChild(onclickaScript);
        console.log('[Waterfall] OnClickA script re-injected');
      }
    } catch (e) {
      console.warn('[Waterfall] OnClickA refresh notice:', e);
    }

    // 7. Refresh Adsterra Multi-Unit Ecosystem (7 Formats Engine)
    try {
      const adsterraContainer = document.getElementById('adsterra-ecosystem-container');
      if (adsterraContainer) {
        // Refresh all isolated Adsterra iframes by reloading their srcdoc/src
        const iframes = adsterraContainer.querySelectorAll('iframe');
        iframes.forEach((ifr) => {
          try {
            if (ifr.srcdoc) {
              const doc = ifr.srcdoc;
              ifr.srcdoc = '';
              setTimeout(() => { ifr.srcdoc = doc; }, 60);
            } else if (ifr.src && ifr.src !== 'about:blank') {
              const base = ifr.src.split('&_t=')[0].split('?_t=')[0];
              ifr.src = base + (base.includes('?') ? '&' : '?') + '_t=' + now;
            }
          } catch (ifrErr) {}
        });

        // Format 3: Native Responsive Banner Container
        const nativeContainer = document.getElementById('container-cddb980692194d13198a2a8e374c5fbc');
        if (nativeContainer) {
          nativeContainer.innerHTML = '';
          const nativeScript = document.createElement('script');
          nativeScript.async = true;
          nativeScript.setAttribute('data-cfasync', 'false');
          nativeScript.src = `https://pl31346908.profitableratecpmnetwork.com/cddb980692194d13198a2a8e374c5fbc/invoke.js?_t=${now}`;
          nativeContainer.appendChild(nativeScript);
        }
        console.log('[Waterfall] Adsterra ecosystem iframes and native banner reloaded');
      }
    } catch (e) {
      console.warn('[Waterfall] Adsterra refresh notice:', e);
    }

    // Finish visual indicator after small buffer
    setTimeout(() => {
      updateVisualIndicator('done');
    }, 800);

    // 8. Broadcast event for any custom ad listeners
    try {
      window.dispatchEvent(new CustomEvent('ads:refreshed', { detail: { timestamp: now } }));
    } catch(e) {}
  }

  const refreshAllDownsideBanners = refreshDownsideAds;

  global.refreshDownsideAds = refreshDownsideAds;
  global.refreshAllDownsideBanners = refreshAllDownsideBanners;

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { refreshDownsideAds, refreshAllDownsideBanners };
  }
})(typeof window !== 'undefined' ? window : this);
