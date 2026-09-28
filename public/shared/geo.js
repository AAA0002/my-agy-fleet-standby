/**
 * ATF Miner Edge Geo & Timezone Utility
 * High-resilience Edge Geo & Local Time with auto-detection
 */
(function() {
  function countryCodeToEmoji(countryCode) {
    if (!countryCode || countryCode === 'UN' || countryCode.length !== 2) {
      return '🌐';
    }
    const code = countryCode.toUpperCase();
    return String.fromCodePoint(...[...code].map(c => 127397 + c.charCodeAt(0)));
  }

  function detectClientCountry(tz) {
    if (typeof navigator !== 'undefined' && navigator.language) {
      const parts = navigator.language.split('-');
      if (parts[1] && parts[1].length === 2) return parts[1].toUpperCase();
    }
    if (!tz) return 'US';
    const lower = tz.toLowerCase();
    if (lower.includes('dhaka')) return 'BD';
    if (lower.includes('kolkata') || lower.includes('calcutta') || lower.includes('mumbai') || lower.includes('delhi')) return 'IN';
    if (lower.includes('karachi') || lower.includes('lahore') || lower.includes('islamabad')) return 'PK';
    if (lower.includes('tashkent') || lower.includes('samarkand')) return 'UZ';
    if (lower.includes('moscow') || lower.includes('samara') || lower.includes('yekaterinburg') || lower.includes('novosibirsk') || lower.includes('vladivostok')) return 'RU';
    if (lower.includes('london')) return 'GB';
    if (lower.includes('berlin') || lower.includes('frankfurt')) return 'DE';
    if (lower.includes('paris')) return 'FR';
    if (lower.includes('rome')) return 'IT';
    if (lower.includes('madrid')) return 'ES';
    if (lower.includes('dubai')) return 'AE';
    if (lower.includes('riyadh')) return 'SA';
    if (lower.includes('cairo')) return 'EG';
    if (lower.includes('lagos') || lower.includes('abuja')) return 'NG';
    if (lower.includes('nairobi')) return 'KE';
    if (lower.includes('johannesburg')) return 'ZA';
    if (lower.includes('jakarta') || lower.includes('makassar')) return 'ID';
    if (lower.includes('ho_chi_minh') || lower.includes('hanoi')) return 'VN';
    if (lower.includes('bangkok')) return 'TH';
    if (lower.includes('kuala_lumpur')) return 'MY';
    if (lower.includes('singapore')) return 'SG';
    if (lower.includes('manila')) return 'PH';
    if (lower.includes('almaty') || lower.includes('astana') || lower.includes('qyzylorda')) return 'KZ';
    if (lower.includes('baku')) return 'AZ';
    if (lower.includes('tbilisi')) return 'GE';
    if (lower.includes('yerevan')) return 'AM';
    if (lower.includes('kyiv') || lower.includes('kiev')) return 'UA';
    if (lower.includes('minsk')) return 'BY';
    if (lower.includes('warsaw')) return 'PL';
    if (lower.includes('istanbul')) return 'TR';
    if (lower.includes('sao_paulo') || lower.includes('rio')) return 'BR';
    if (lower.includes('buenos_aires')) return 'AR';
    if (lower.includes('mexico')) return 'MX';
    if (lower.includes('toronto') || lower.includes('vancouver') || lower.includes('montreal')) return 'CA';
    if (lower.includes('sydney') || lower.includes('melbourne')) return 'AU';
    if (lower.includes('tokyo')) return 'JP';
    if (lower.includes('seoul')) return 'KR';
    if (lower.includes('new_york') || lower.includes('chicago') || lower.includes('los_angeles') || lower.includes('denver') || lower.includes('phoenix')) return 'US';
    return 'US';
  }

  function getLocalTime(timezone) {
    try {
      return new Date().toLocaleTimeString([], {
        timeZone: timezone || undefined,
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (e) {
      return new Date().toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit'
      });
    }
  }

  let activeInterval = null;
  let currentGeo = null;

  function initGeoClock(geoData) {
    if (geoData) currentGeo = geoData;
    
    let tz = currentGeo?.timezone;
    if (!tz && typeof Intl !== 'undefined' && Intl.DateTimeFormat) {
      try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone; } catch (e) {}
    }
    if (!tz) tz = 'UTC';

    let country = currentGeo?.country;
    if (!country || country === 'UN') {
      country = detectClientCountry(tz);
    }
    country = country.toUpperCase();
    const flag = countryCodeToEmoji(country);

    const pillEl = document.getElementById('geoClockPill') || document.getElementById('geo-pill');
    if (pillEl) {
      pillEl.classList.remove('hidden');
      pillEl.innerHTML = `<span id="geo-flag">${flag}</span> <span id="geo-clock">${getLocalTime(tz)}</span>`;
    }

    function update() {
      const clockEl = document.getElementById('geo-clock');
      if (clockEl) {
        clockEl.textContent = getLocalTime(tz);
      } else {
        const p = document.getElementById('geoClockPill') || document.getElementById('geo-pill');
        if (p) p.innerHTML = `<span id="geo-flag">${flag}</span> <span id="geo-clock">${getLocalTime(tz)}</span>`;
      }
    }
    update();
    if (activeInterval) clearInterval(activeInterval);
    activeInterval = setInterval(update, 5000);
  }

  window.ATFGeo = {
    countryCodeToEmoji,
    detectClientCountry,
    getLocalTime,
    initGeoClock
  };

  // Immediate auto-boot so clock is never stuck on --:--
  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', function() { initGeoClock(); });
    } else {
      setTimeout(function() { initGeoClock(); }, 0);
    }
  }
})();
