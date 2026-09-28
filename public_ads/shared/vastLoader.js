/**
 * HilltopAds VAST 3.0 & Google Interactive Media Ads (IMA) SDK Video Controller
 * 
 * Supports:
 * 1. Google Interactive Media Ads (IMA) SDK via official Google loader with HilltopAds IMA tag
 * 2. Native VAST 3.0 XML parsing, progressive MP4/WebM video playback, real impression tracking,
 *    quartile event beacons (start, 25%, 50%, 75%, complete), and verified clickthrough delivery.
 * 
 * ZERO synthetic placeholders or fake stream animations: 100% genuine ad network delivery.
 */
(function(global) {
  'use strict';

  const VAST_CONFIG = {
    // Official HilltopAds VAST 3.0 Tag
    vastTagUrl: "https://zesty-career.com/dDm/F.zadKGcNEvqZ/GwUG/Jenmf9/uCZIU_lOkwPCTCc/0RMWjbga1ZM_jEUitWNwzmQsyNO/DMUIydOKQP",
    // Official HilltopAds VAST tag for Google Ad Manager / Google IMA SDK
    imaTagUrl: "https://zesty-career.com/dbmiFTzxd.GnNkvcZeGoUL/zeFmC9oudZ/UUljkcPATpch0lMhjngH1wMUjmU/tsNwzQQdyTOsD/UDy-OyS/ZPsBanW/1GpqdbDn0qxv",
    slotWidth: 300,
    slotHeight: 170
  };

  let adsManager = null;
  let adsLoader = null;
  let adDisplayContainer = null;
  let imaInitialized = false;

  let parsedAds = [];
  let currentAdIndex = 0;
  let currentClickThrough = null;
  let currentClickTracking = [];
  let firedTrackingEvents = new Set();
  let timeUpdateHandler = null;

  /**
   * Dispatches a real tracking beacon to the ad network (for impressions, clicks, quartile tracking)
   */
  function fireBeacon(url) {
    if (!url || typeof url !== 'string') return;
    const cleanUrl = url.trim();
    if (!cleanUrl) return;

    try {
      if (typeof navigator !== 'undefined' && typeof navigator.sendBeacon === 'function') {
        const sent = navigator.sendBeacon(cleanUrl);
        if (sent) return;
      }
    } catch (e) {}

    try {
      const img = new Image();
      img.referrerPolicy = 'no-referrer-when-downgrade';
      img.src = cleanUrl;
    } catch (e) {}

    try {
      fetch(cleanUrl, {
        method: 'GET',
        mode: 'no-cors',
        credentials: 'omit',
        cache: 'no-store'
      }).catch(() => {});
    } catch (e) {}
  }

  /**
   * Helper to clean CDATA and whitespace from XML node text
   */
  function getNodeText(node) {
    if (!node) return '';
    return (node.textContent || node.text || '').replace(/<!\[CDATA\[|\]\]>/g, '').trim();
  }

  /**
   * Parses standard VAST 3.0 XML response into structured Ad models
   */
  function parseVast3Xml(xmlDoc) {
    const results = [];
    const adNodes = xmlDoc.getElementsByTagName('Ad');
    if (!adNodes || adNodes.length === 0) return results;

    for (let i = 0; i < adNodes.length; i++) {
      const adNode = adNodes[i];
      const adId = adNode.getAttribute('id') || `vast-ad-${i}`;
      const inlineNode = adNode.getElementsByTagName('InLine')[0];
      if (!inlineNode) continue;

      const titleNode = inlineNode.getElementsByTagName('AdTitle')[0];
      const title = titleNode ? getNodeText(titleNode) : adId;

      // Impression tracking URLs
      const impNodes = inlineNode.getElementsByTagName('Impression');
      const impressions = [];
      for (let j = 0; j < impNodes.length; j++) {
        const u = getNodeText(impNodes[j]);
        if (u) impressions.push(u);
      }

      // Linear Creative & MediaFiles
      const linearNode = inlineNode.getElementsByTagName('Linear')[0];
      if (!linearNode) continue;

      // ClickThrough & ClickTracking
      let clickThrough = null;
      const clickThroughNode = linearNode.getElementsByTagName('ClickThrough')[0];
      if (clickThroughNode) {
        clickThrough = getNodeText(clickThroughNode);
      }

      const clickTrackingNodes = linearNode.getElementsByTagName('ClickTracking');
      const clickTracking = [];
      for (let j = 0; j < clickTrackingNodes.length; j++) {
        const u = getNodeText(clickTrackingNodes[j]);
        if (u) clickTracking.push(u);
      }

      // Tracking Events (start, firstQuartile, midpoint, thirdQuartile, complete, etc.)
      const trackingMap = {};
      const trackingNodes = linearNode.getElementsByTagName('Tracking');
      for (let j = 0; j < trackingNodes.length; j++) {
        const tNode = trackingNodes[j];
        const eventName = tNode.getAttribute('event');
        const eventUrl = getNodeText(tNode);
        if (eventName && eventUrl) {
          if (!trackingMap[eventName]) trackingMap[eventName] = [];
          trackingMap[eventName].push(eventUrl);
        }
      }

      // Media Files
      const mediaNodes = linearNode.getElementsByTagName('MediaFile');
      const mediaFiles = [];
      for (let j = 0; j < mediaNodes.length; j++) {
        const mNode = mediaNodes[j];
        const src = getNodeText(mNode);
        if (!src) continue;
        mediaFiles.push({
          src: src,
          type: mNode.getAttribute('type') || 'video/mp4',
          delivery: mNode.getAttribute('delivery') || 'progressive',
          bitrate: parseInt(mNode.getAttribute('bitrate') || '400', 10),
          width: parseInt(mNode.getAttribute('width') || '300', 10),
          height: parseInt(mNode.getAttribute('height') || '170', 10)
        });
      }

      if (mediaFiles.length > 0) {
        results.push({
          id: adId,
          title: title,
          impressions: impressions,
          clickThrough: clickThrough,
          clickTracking: clickTracking,
          trackingEvents: trackingMap,
          mediaFiles: mediaFiles
        });
      }
    }

    return results;
  }

  /**
   * Native VAST 3.0 Direct Player: Renders genuine MP4/WebM video and fires real ad network beacons
   */
  function playDirectVastAd(ad) {
    const player = document.getElementById('silent-vast-player');
    const wrapper = document.getElementById('vast-video-wrapper');
    const clickCta = document.getElementById('vast-click-cta');
    const labelBadge = document.getElementById('vast-ad-label');

    if (!player) return;

    // Pick progressive media file closest to 300x170 / mobile friendly
    let chosenMedia = null;
    const progressive = ad.mediaFiles.filter(m => m.delivery.toLowerCase() === 'progressive');
    const mp4s = progressive.filter(m => m.type.includes('mp4'));

    if (mp4s.length > 0) {
      // Sort by bitrate ascending, pick a smooth mobile resolution (~250-480kbps)
      mp4s.sort((a, b) => a.bitrate - b.bitrate);
      chosenMedia = mp4s[0];
    } else if (progressive.length > 0) {
      chosenMedia = progressive[0];
    } else {
      chosenMedia = ad.mediaFiles[0];
    }

    if (!chosenMedia) return;

    // Setup clickthrough
    currentClickThrough = ad.clickThrough || null;
    currentClickTracking = ad.clickTracking || [];

    if (clickCta) {
      clickCta.style.display = currentClickThrough ? 'flex' : 'none';
    }

    if (labelBadge) {
      labelBadge.textContent = 'VAST 3.0 AD';
    }

    // Reset tracking state for this creative
    firedTrackingEvents = new Set();

    // Fire Impressions immediately when ad creative loads
    if (ad.impressions && ad.impressions.length > 0) {
      ad.impressions.forEach(impUrl => {
        fireBeacon(impUrl);
        console.log('[VAST 3.0] Fired ad impression beacon to HilltopAds');
      });
    }

    // Set video source
    player.style.display = 'block';
    player.style.opacity = '1';
    player.muted = true;
    player.playsInline = true;
    player.autoplay = true;
    player.loop = false; // We advance to next creative or replay on ended

    if (player.src !== chosenMedia.src) {
      player.src = chosenMedia.src;
    }

    // Attach quartile tracking
    if (timeUpdateHandler) {
      player.removeEventListener('timeupdate', timeUpdateHandler);
    }

    timeUpdateHandler = function() {
      if (!player.duration || player.duration <= 0) return;
      const progress = player.currentTime / player.duration;

      function triggerEvent(name) {
        if (!firedTrackingEvents.has(name) && ad.trackingEvents[name]) {
          firedTrackingEvents.add(name);
          ad.trackingEvents[name].forEach(u => fireBeacon(u));
          console.log(`[VAST 3.0] Fired tracking event: ${name}`);
        }
      }

      if (progress > 0.01) triggerEvent('start');
      if (progress >= 0.25) triggerEvent('firstQuartile');
      if (progress >= 0.50) triggerEvent('midpoint');
      if (progress >= 0.75) triggerEvent('thirdQuartile');
      if (progress >= 0.98) triggerEvent('complete');
    };

    player.addEventListener('timeupdate', timeUpdateHandler);

    // Play next ad in rotation when video finishes
    player.onended = function() {
      if (ad.trackingEvents && ad.trackingEvents['complete']) {
        ad.trackingEvents['complete'].forEach(u => fireBeacon(u));
      }
      if (parsedAds.length > 1) {
        currentAdIndex = (currentAdIndex + 1) % parsedAds.length;
        playDirectVastAd(parsedAds[currentAdIndex]);
      } else {
        // Fetch fresh VAST rotation
        loadDirectVast3(true);
      }
    };

    try {
      player.load();
      const p = player.play();
      if (p && typeof p.catch === 'function') {
        p.catch(err => {
          console.log('[VAST 3.0] Silent autoplay pending interaction:', err);
        });
      }
    } catch (e) {
      console.warn('[VAST 3.0] Video load notice:', e);
    }
  }

  /**
   * Handle user click on VAST ad wrapper or CTA button
   */
  function handleAdClick(e) {
    if (e) e.stopPropagation();
    if (currentClickThrough) {
      // Fire click tracking beacons
      if (currentClickTracking && currentClickTracking.length > 0) {
        currentClickTracking.forEach(u => fireBeacon(u));
      }
      window.open(currentClickThrough, '_blank', 'noopener,noreferrer');
    }
  }

  /**
   * Fetches the direct VAST 3.0 XML and executes native playback with dual-tag fallback
   */
  async function loadDirectVast3(forceReload = false) {
    const urls = [VAST_CONFIG.vastTagUrl, VAST_CONFIG.imaTagUrl];
    console.log('[VAST 3.0] Requesting fresh VAST 3.0 XML feed...');

    for (const baseUrl of urls) {
      const url = baseUrl + (baseUrl.includes('?') ? '&' : '?') + '_t=' + Date.now();
      try {
        const res = await fetch(url, {
          cache: 'no-store',
          headers: {
            'Accept': 'application/xml, text/xml, */*'
          }
        });

        if (!res.ok) {
          console.warn(`[VAST 3.0] Feed ${baseUrl.slice(0, 35)}... returned HTTP ${res.status}`);
          continue;
        }

        const xmlText = await res.text();
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(xmlText, 'text/xml');

        const ads = parseVast3Xml(xmlDoc);
        if (ads.length > 0) {
          parsedAds = ads;
          currentAdIndex = 0;
          playDirectVastAd(parsedAds[0]);
          console.log(`[VAST 3.0] Loaded ${ads.length} genuine video creative(s) from HilltopAds`);
          return;
        }
      } catch (err) {
        console.warn('[VAST 3.0] Direct VAST fetch error:', err);
      }
    }
    console.warn('[VAST 3.0] No linear media creatives found across all tags');
  }

  /**
   * Initializes Google Interactive Media Ads (IMA) SDK
   */
  function initGoogleIma() {
    if (typeof global.google === 'undefined' || !global.google.ima) {
      console.log('[Google IMA] SDK not loaded, using direct VAST 3.0 player');
      loadDirectVast3();
      return;
    }

    const videoElement = document.getElementById('silent-vast-player');
    const adContainer = document.getElementById('ima-ad-container');
    const labelBadge = document.getElementById('vast-ad-label');

    if (!videoElement || !adContainer) {
      loadDirectVast3();
      return;
    }

    let imaStarted = false;
    let imaSafetyTimer = null;

    const engageNormalVastFallback = (reason) => {
      if (imaSafetyTimer) {
        clearTimeout(imaSafetyTimer);
        imaSafetyTimer = null;
      }
      if (adsManager) {
        try { adsManager.destroy(); } catch (e) {}
        adsManager = null;
      }
      console.warn(`[Google IMA] ${reason}. Seamlessly engaging normal VAST 3.0 player...`);
      loadDirectVast3();
    };

    try {
      if (!adDisplayContainer) {
        adDisplayContainer = new global.google.ima.AdDisplayContainer(adContainer, videoElement);
      }
      adDisplayContainer.initialize();

      if (!adsLoader) {
        adsLoader = new global.google.ima.AdsLoader(adDisplayContainer);
        adsLoader.getSettings().setAutoPlayAdBreaks(true);

        adsLoader.addEventListener(
          global.google.ima.AdsManagerLoadedEvent.Type.ADS_MANAGER_LOADED,
          function(adsManagerLoadedEvent) {
            console.log('[Google IMA] AdsManager loaded');
            const adsRenderingSettings = new global.google.ima.AdsRenderingSettings();
            adsRenderingSettings.restoreCustomPlaybackStateOnAdBreakComplete = true;

            adsManager = adsManagerLoadedEvent.getAdsManager(videoElement, adsRenderingSettings);

            adsManager.addEventListener(global.google.ima.AdErrorEvent.Type.AD_ERROR, function(adErrorEvent) {
              engageNormalVastFallback('AdManager playback error');
            });

            adsManager.addEventListener(global.google.ima.AdEvent.Type.STARTED, function() {
              imaStarted = true;
              if (imaSafetyTimer) {
                clearTimeout(imaSafetyTimer);
                imaSafetyTimer = null;
              }
              console.log('[Google IMA] Ad playback started successfully');
            });

            adsManager.addEventListener(global.google.ima.AdEvent.Type.CONTENT_PAUSE_REQUESTED, function() {
              videoElement.pause();
            });

            adsManager.addEventListener(global.google.ima.AdEvent.Type.CONTENT_RESUME_REQUESTED, function() {
              videoElement.play().catch(() => {});
            });

            adsManager.addEventListener(global.google.ima.AdEvent.Type.ALL_ADS_COMPLETED, function() {
              console.log('[Google IMA] All ads completed, requesting next rotation');
              engageNormalVastFallback('IMA ad cycle finished');
            });

            try {
              if (labelBadge) labelBadge.textContent = 'GOOGLE IMA AD';
              adsManager.init(VAST_CONFIG.slotWidth, VAST_CONFIG.slotHeight, global.google.ima.ViewMode.NORMAL);
              adsManager.setVolume(0); // Silent inline video
              adsManager.start();
            } catch (adErr) {
              engageNormalVastFallback('AdsManager.start exception');
            }
          },
          false
        );

        adsLoader.addEventListener(
          global.google.ima.AdErrorEvent.Type.AD_ERROR,
          function(adErrorEvent) {
            engageNormalVastFallback('AdsLoader request error');
          },
          false
        );
      }

      // Safety timeout: If Google IMA doesn't start playing within 2500ms, immediately fall back to normal VAST 3.0
      imaSafetyTimer = setTimeout(() => {
        if (!imaStarted) {
          engageNormalVastFallback('Creative start timeout (2.5s)');
        }
      }, 2500);

      // Request ads with user IMA tag
      const adsRequest = new global.google.ima.AdsRequest();
      adsRequest.adTagUrl = VAST_CONFIG.imaTagUrl + (VAST_CONFIG.imaTagUrl.includes('?') ? '&' : '?') + '_t=' + Date.now();
      adsRequest.linearAdSlotWidth = VAST_CONFIG.slotWidth;
      adsRequest.linearAdSlotHeight = VAST_CONFIG.slotHeight;
      adsRequest.nonLinearAdSlotWidth = VAST_CONFIG.slotWidth;
      adsRequest.nonLinearAdSlotHeight = VAST_CONFIG.slotHeight;

      adsLoader.requestAds(adsRequest);
      imaInitialized = true;
    } catch (e) {
      engageNormalVastFallback('Init exception: ' + e);
    }
  }

  /**
   * Master Entry: Initializes genuine VAST 3.0 & Google IMA video delivery
   */
  function initSilentVastPlayer(forceReload = false) {
    const wrapper = document.getElementById('vast-video-wrapper');
    const clickCta = document.getElementById('vast-click-cta');

    if (wrapper && !wrapper.dataset.clickBound) {
      wrapper.dataset.clickBound = 'true';
      wrapper.addEventListener('click', handleAdClick);
    }
    if (clickCta && !clickCta.dataset.clickBound) {
      clickCta.dataset.clickBound = 'true';
      clickCta.addEventListener('click', handleAdClick);
    }

    if (forceReload) {
      if (adsManager) {
        try { adsManager.destroy(); } catch (e) {}
        adsManager = null;
      }
    }

    // If Google IMA is available, try Google IMA first; otherwise use direct VAST 3.0
    if (typeof global.google !== 'undefined' && global.google.ima) {
      initGoogleIma();
    } else {
      loadDirectVast3(forceReload);
    }
  }

  // Bind to global window scope
  global.initSilentVastPlayer = initSilentVastPlayer;
  global.handleVastAdClick = handleAdClick;

  if (typeof document !== 'undefined') {
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
      initSilentVastPlayer();
    } else {
      document.addEventListener('DOMContentLoaded', () => initSilentVastPlayer());
    }
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { initSilentVastPlayer, parseVast3Xml };
  }
})(typeof window !== 'undefined' ? window : this);
