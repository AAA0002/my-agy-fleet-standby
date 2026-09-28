/**
 * ATF Mining Ecosystem - Audio, Procedural Cyber Ambient Music & Dual-Layer Haptics Engine
 * 100% Zero-Asset Web Audio API implementation with rock-solid compatibility across iOS, Android & Desktop.
 * 
 * Sound Design Philosophy:
 * - SFX: Organic, tactile, warm acoustic UI sounds (soft wooden pops, liquid marimba drops, crystalline celesta cascades).
 *   NO harsh raw sawtooth buzzing or piercing high-frequency square waves.
 * - Ambient Music: "Ethereal Celestial Drift" - lush lo-fi meditative ambient synthesizer soundscape.
 *   Uses warm sine & detuned triangle choruses, gentle Butterworth lowpass filtering, and seamless cross-fading chords.
 * - Architecture: Studio-grade DynamicsCompressor limiter bus to prevent speaker clipping or distortion.
 */
(function(global) {
  'use strict';

  let audioCtx = null;
  let masterGain = null;
  let masterLimiter = null;
  let masterFilter = null;
  let sfxGain = null;
  let musicGain = null;
  let musicFilter = null;
  let isUnlocked = false;

  let sfxEnabled = true;
  let musicEnabled = false;
  let hapticsEnabled = true;
  let musicTimer = null;
  let activeMusicNodes = [];
  let currentChordIndex = 0;

  // Read persisted user preferences safely
  try {
    if (localStorage.getItem('atf_sound_enabled') === '0') sfxEnabled = false;
    if (localStorage.getItem('atf_cyber_music_enabled') === '1') musicEnabled = true;
    if (localStorage.getItem('atf_haptics_enabled') === '0') hapticsEnabled = false;
  } catch (e) {}

  /**
   * Initializes or returns the shared AudioContext with studio master bus chain:
   * [SFX/Music Bus] -> [Master Filter 7.5kHz] -> [Master Limiter/Compressor] -> [Master Gain] -> [Destination]
   */
  function getAudioContext() {
    if (!audioCtx) {
      const AudioContextClass = global.AudioContext || global.webkitAudioContext;
      if (AudioContextClass) {
        try {
          audioCtx = new AudioContextClass();

          // 1. Master Output Gain
          masterGain = audioCtx.createGain();
          masterGain.gain.value = 1.0;
          masterGain.connect(audioCtx.destination);

          // 2. Master Dynamics Compressor / Limiter (Prevents clipping & mobile speaker distortion)
          try {
            masterLimiter = audioCtx.createDynamicsCompressor();
            masterLimiter.threshold.setValueAtTime(-10.0, audioCtx.currentTime);
            masterLimiter.knee.setValueAtTime(24.0, audioCtx.currentTime);
            masterLimiter.ratio.setValueAtTime(8.0, audioCtx.currentTime);
            masterLimiter.attack.setValueAtTime(0.003, audioCtx.currentTime);
            masterLimiter.release.setValueAtTime(0.15, audioCtx.currentTime);
            masterLimiter.connect(masterGain);
          } catch (e) {
            masterLimiter = masterGain;
          }

          // 3. Master Soft Anti-Aliasing Lowpass Filter
          try {
            masterFilter = audioCtx.createBiquadFilter();
            masterFilter.type = 'lowpass';
            masterFilter.frequency.setValueAtTime(7500, audioCtx.currentTime);
            masterFilter.Q.setValueAtTime(0.707, audioCtx.currentTime);
            masterFilter.connect(masterLimiter);
          } catch (e) {
            masterFilter = masterLimiter;
          }

          // 4. SFX Bus (Warm, clear, balanced at 0.65)
          sfxGain = audioCtx.createGain();
          sfxGain.gain.value = sfxEnabled ? 0.65 : 0;
          sfxGain.connect(masterFilter);

          // 5. Music Bus with Dedicated Warmth Filter (Cutoff at 560Hz for lush lo-fi atmosphere)
          musicFilter = audioCtx.createBiquadFilter();
          musicFilter.type = 'lowpass';
          musicFilter.frequency.setValueAtTime(560, audioCtx.currentTime);
          musicFilter.Q.setValueAtTime(0.707, audioCtx.currentTime);
          musicFilter.connect(masterFilter);

          musicGain = audioCtx.createGain();
          musicGain.gain.value = musicEnabled ? 0.22 : 0;
          musicGain.connect(musicFilter);

        } catch (e) {
          console.warn('[AudioEngine] Context creation failed:', e);
        }
      }
    }
    return audioCtx;
  }

  /**
   * Safe Audio Unlocker for iOS Safari WebKit & Android Chrome WebViews.
   * Plays a 1-sample silent buffer directly to audio destination to awaken the audio hardware.
   */
  function unlockAudio(cb) {
    const ctx = getAudioContext();
    if (!ctx) {
      if (cb) cb();
      return;
    }

    const runUnlock = () => {
      try {
        const buffer = ctx.createBuffer(1, 1, 22050);
        const source = ctx.createBufferSource();
        source.buffer = buffer;
        source.connect(ctx.destination);
        source.start(0);
        isUnlocked = true;
      } catch (e) {}

      if (musicEnabled && !musicTimer) {
        startCyberMusic();
      }
      if (cb) cb();
    };

    if (ctx.state === 'suspended' || ctx.state === 'interrupted') {
      ctx.resume().then(runUnlock).catch(runUnlock);
    } else {
      runUnlock();
    }
  }

  // Register aggressive auto-unlock listeners on all common user touch / click events
  if (typeof document !== 'undefined') {
    const unlockEvents = ['touchstart', 'touchend', 'pointerdown', 'mousedown', 'click', 'keydown'];
    const handleUnlock = () => {
      unlockAudio();
      unlockEvents.forEach(evt => document.removeEventListener(evt, handleUnlock, true));
    };
    unlockEvents.forEach(evt => document.addEventListener(evt, handleUnlock, { capture: true, passive: true }));
  }

  /**
   * Helper to create a soft-enveloped sine oscillator with clean garbage collection.
   */
  function createSoftTone(ctx, dest, freq, startT, duration, peakGain, endGain = 0.0001, type = 'sine') {
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, startT);

    gain.gain.setValueAtTime(0.0001, startT);
    gain.gain.linearRampToValueAtTime(peakGain, startT + 0.006);
    gain.gain.exponentialRampToValueAtTime(endGain, startT + duration);

    osc.connect(gain);
    gain.connect(dest);

    osc.start(startT);
    osc.stop(startT + duration + 0.02);

    osc.onended = () => {
      try {
        osc.disconnect();
        gain.disconnect();
      } catch (e) {}
    };
    return { osc, gain };
  }

  /**
   * Procedural Sound Effects (SFX)
   * High-end acoustic sound design: tactile wooden pops, liquid marimba drops, crystalline celesta cascades.
   */
  function playFX(type) {
    if (!sfxEnabled) return;
    const ctx = getAudioContext();
    if (!ctx) return;

    const executeFx = () => {
      try {
        const now = ctx.currentTime;
        const out = sfxGain || masterGain || ctx.destination;

        switch (type) {
          // --- 1. Tactile UI Click / Tap: Organic wooden bubble micro-pop ---
          case 'click':
          case 'tick':
          case 'tap': {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            const filter = ctx.createBiquadFilter();

            filter.type = 'lowpass';
            filter.frequency.setValueAtTime(1400, now);
            filter.Q.setValueAtTime(1.0, now);

            osc.type = 'sine';
            // Subtle pitch envelope: quick pop from 380Hz to 135Hz in 30ms
            osc.frequency.setValueAtTime(380, now);
            osc.frequency.exponentialRampToValueAtTime(135, now + 0.030);

            gain.gain.setValueAtTime(0.0001, now);
            gain.gain.linearRampToValueAtTime(0.30, now + 0.003);
            gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.035);

            osc.connect(filter);
            filter.connect(gain);
            gain.connect(out);

            osc.start(now);
            osc.stop(now + 0.04);
            break;
          }

          // --- 2. Tab Switch: Soft liquid droplet / warm marimba pop ---
          case 'tab': {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            const filter = ctx.createBiquadFilter();

            filter.type = 'lowpass';
            filter.frequency.setValueAtTime(1800, now);

            osc.type = 'sine';
            // Liquid upward inflection with warm decay
            osc.frequency.setValueAtTime(460, now);
            osc.frequency.exponentialRampToValueAtTime(680, now + 0.018);
            osc.frequency.exponentialRampToValueAtTime(320, now + 0.065);

            gain.gain.setValueAtTime(0.0001, now);
            gain.gain.linearRampToValueAtTime(0.24, now + 0.005);
            gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.065);

            osc.connect(filter);
            filter.connect(gain);
            gain.connect(out);

            osc.start(now);
            osc.stop(now + 0.07);
            break;
          }

          // --- 3. Coin / Harvest / Claim: Crystalline Celesta Cascade ---
          case 'coin':
          case 'harvest':
          case 'claim': {
            // Golden pentatonic bell frequencies: E5, G#5, B5, E6
            const bellNotes = [
              { freq: 659.25, time: 0.000, dur: 0.38, vol: 0.28 }, // E5
              { freq: 830.61, time: 0.055, dur: 0.42, vol: 0.25 }, // G#5
              { freq: 987.77, time: 0.110, dur: 0.48, vol: 0.22 }, // B5
              { freq: 1318.51, time: 0.165, dur: 0.55, vol: 0.16 } // E6
            ];

            bellNotes.forEach(note => {
              const noteT = now + note.time;
              const osc = ctx.createOscillator();
              const gain = ctx.createGain();
              const filter = ctx.createBiquadFilter();

              filter.type = 'lowpass';
              filter.frequency.setValueAtTime(2600, noteT);
              filter.Q.setValueAtTime(1.2, noteT);

              osc.type = 'sine';
              osc.frequency.setValueAtTime(note.freq, noteT);

              // Smooth bell envelope: quick soft attack, long crystalline decay
              gain.gain.setValueAtTime(0.0001, noteT);
              gain.gain.linearRampToValueAtTime(note.vol, noteT + 0.008);
              gain.gain.exponentialRampToValueAtTime(0.0001, noteT + note.dur);

              osc.connect(filter);
              filter.connect(gain);
              gain.connect(out);

              osc.start(noteT);
              osc.stop(noteT + note.dur + 0.02);
            });
            break;
          }

          // --- 4. Success / Accomplishment: Cinematic Major 9th Celestial Bloom ---
          case 'success': {
            // Warm sub anchor + ascending shimmering chord: C4, E5, G5, B5, D6
            const chord = [
              { freq: 261.63, time: 0.000, dur: 0.50, vol: 0.20, type: 'sine' },     // C4 (sub warmth)
              { freq: 659.25, time: 0.045, dur: 0.45, vol: 0.22, type: 'sine' },     // E5
              { freq: 783.99, time: 0.095, dur: 0.50, vol: 0.20, type: 'sine' },     // G5
              { freq: 987.77, time: 0.150, dur: 0.55, vol: 0.18, type: 'triangle' }, // B5
              { freq: 1174.66, time: 0.210, dur: 0.65, vol: 0.16, type: 'sine' }     // D6
            ];

            chord.forEach(n => {
              const nT = now + n.time;
              createSoftTone(ctx, out, n.freq, nT, n.dur, n.vol, 0.0001, n.type);
            });
            break;
          }

          // --- 5. VIP / Level Up: Majestic Royal Fanfare ---
          case 'vip':
          case 'levelup': {
            // Two-stage royal shimmer: A Maj9 -> E Maj9 with shimmering overtones
            const fanfare = [
              { freq: 440.00, time: 0.00, dur: 0.45, vol: 0.22 }, // A4
              { freq: 554.37, time: 0.06, dur: 0.48, vol: 0.22 }, // C#5
              { freq: 659.25, time: 0.12, dur: 0.52, vol: 0.20 }, // E5
              { freq: 880.00, time: 0.18, dur: 0.58, vol: 0.18 }, // A5
              { freq: 1108.73, time: 0.26, dur: 0.65, vol: 0.16 }, // C#6
              { freq: 1318.51, time: 0.34, dur: 0.80, vol: 0.14 }  // E6
            ];

            fanfare.forEach(n => {
              const nT = now + n.time;
              createSoftTone(ctx, out, n.freq, nT, n.dur, n.vol, 0.0001, 'sine');
            });
            break;
          }

          // --- 6. Error / Denied: Polite Acoustic Double-Knock (NO harsh sawtooth) ---
          case 'error':
          case 'denied': {
            // Muted wooden double-tap: warm low sine pulses that inform without jarring
            const knocks = [
              { startFreq: 140, endFreq: 80, time: 0.000, dur: 0.040, vol: 0.25 },
              { startFreq: 112, endFreq: 64, time: 0.075, dur: 0.048, vol: 0.20 }
            ];

            knocks.forEach(k => {
              const kT = now + k.time;
              const osc = ctx.createOscillator();
              const gain = ctx.createGain();
              const filter = ctx.createBiquadFilter();

              filter.type = 'lowpass';
              filter.frequency.setValueAtTime(450, kT);

              osc.type = 'sine';
              osc.frequency.setValueAtTime(k.startFreq, kT);
              osc.frequency.exponentialRampToValueAtTime(k.endFreq, kT + k.dur);

              gain.gain.setValueAtTime(0.0001, kT);
              gain.gain.linearRampToValueAtTime(k.vol, kT + 0.004);
              gain.gain.exponentialRampToValueAtTime(0.0001, kT + k.dur);

              osc.connect(filter);
              filter.connect(gain);
              gain.connect(out);

              osc.start(kT);
              osc.stop(kT + k.dur + 0.01);
            });
            break;
          }

          // --- 7. Toggle: Crisp tactile micro-snap ---
          case 'toggle': {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(540, now);
            osc.frequency.exponentialRampToValueAtTime(360, now + 0.025);

            gain.gain.setValueAtTime(0.0001, now);
            gain.gain.linearRampToValueAtTime(0.22, now + 0.003);
            gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.025);

            osc.connect(gain);
            gain.connect(out);

            osc.start(now);
            osc.stop(now + 0.03);
            break;
          }

          // --- 8. Boost / Upgrade: Warm Euphoric Swell ---
          case 'boost':
          case 'upgrade': {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            const filter = ctx.createBiquadFilter();

            filter.type = 'lowpass';
            filter.frequency.setValueAtTime(350, now);
            filter.frequency.exponentialRampToValueAtTime(1600, now + 0.28);

            osc.type = 'triangle';
            osc.frequency.setValueAtTime(220, now);
            osc.frequency.exponentialRampToValueAtTime(587.33, now + 0.28); // D5

            gain.gain.setValueAtTime(0.0001, now);
            gain.gain.linearRampToValueAtTime(0.24, now + 0.08);
            gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.32);

            osc.connect(filter);
            filter.connect(gain);
            gain.connect(out);

            osc.start(now);
            osc.stop(now + 0.35);
            break;
          }

          default:
            break;
        }
      } catch (e) {
        console.warn('[AudioEngine] Error playing FX:', e);
      }
    };

    if (ctx.state === 'suspended' || ctx.state === 'interrupted') {
      ctx.resume().then(executeFx).catch(() => {});
    } else {
      executeFx();
    }
  }

  /**
   * Procedural Ambient Synth Music: "Ethereal Celestial Drift"
   * 
   * Harmonic Architecture:
   * Peaceful, expansive Neo-Tokyo Lydian / Add9 progression:
   * - Chord 1: Dmaj9  [D3 (146.83), A3 (220.00), C#4 (277.18), F#4 (369.99), E5 (659.25)]
   * - Chord 2: F#m7/11 [F#2 (92.50), C#3 (138.59), A3 (220.00), E4 (329.63), G#4 (415.30)]
   * - Chord 3: Bm9    [B2 (123.47), F#3 (185.00), A3 (220.00), C#4 (277.18), D4 (293.66)]
   * - Chord 4: Aadd9  [A2 (110.00), E3 (164.81), G#3 (207.65), B3 (246.94), E4 (329.63)]
   * 
   * Synthesis:
   * - Dual-oscillator detuned choruses (sine + soft triangle ±4.5 cents) passed through a warm 560Hz lowpass filter.
   * - 6.2-second chord duration with 1.8s attack, 2.6s release, and 1.2s cross-fade overlap.
   * - Soft ambient sub-bass pedal and faint celestial chimes (twinkling star pings).
   */
  const AMBIENT_CHORDS = [
    {
      rootFreq: 73.42, // D2
      notes: [146.83, 220.00, 277.18, 369.99], // D3, A3, C#4, F#4 (Dmaj9)
      sparkle: 659.25 // E5
    },
    {
      rootFreq: 92.50, // F#2
      notes: [138.59, 220.00, 329.63, 415.30], // C#3, A3, E4, G#4 (F#m7/11)
      sparkle: 554.37 // C#5
    },
    {
      rootFreq: 61.74, // B1
      notes: [185.00, 220.00, 277.18, 293.66], // F#3, A3, C#4, D4 (Bm9)
      sparkle: 739.99 // F#5
    },
    {
      rootFreq: 55.00, // A1
      notes: [164.81, 207.65, 246.94, 329.63], // E3, G#3, B3, E4 (Aadd9)
      sparkle: 987.77 // B5
    }
  ];

  function scheduleAmbientChord() {
    if (!musicEnabled) return;
    const ctx = getAudioContext();
    if (!ctx) return;

    try {
      const now = ctx.currentTime;
      const chordData = AMBIENT_CHORDS[currentChordIndex % AMBIENT_CHORDS.length];
      currentChordIndex++;

      const dest = musicGain || masterGain || ctx.destination;
      const chordDur = 6.2;
      const attackDur = 1.8;
      const releaseDur = 2.6;

      // 1. Soft Sub-Bass Pedal (Warm grounding sine wave, very gentle)
      const subOsc = ctx.createOscillator();
      const subGain = ctx.createGain();
      subOsc.type = 'sine';
      subOsc.frequency.setValueAtTime(chordData.rootFreq, now);

      subGain.gain.setValueAtTime(0.0001, now);
      subGain.gain.linearRampToValueAtTime(0.07, now + attackDur);
      subGain.gain.setValueAtTime(0.07, now + chordDur - releaseDur);
      subGain.gain.exponentialRampToValueAtTime(0.0001, now + chordDur);

      subOsc.connect(subGain);
      subGain.connect(dest);
      subOsc.start(now);
      subOsc.stop(now + chordDur + 0.05);

      subOsc.onended = () => {
        try {
          subOsc.disconnect();
          subGain.disconnect();
        } catch (e) {}
        const idx = activeMusicNodes.indexOf(subOsc);
        if (idx !== -1) activeMusicNodes.splice(idx, 1);
      };
      activeMusicNodes.push(subOsc);

      // 2. Pad Voices (Dual detuned sine & triangle for lush chorus warmth)
      chordData.notes.forEach((freq, idx) => {
        // Voice A: Warm fundamental sine
        const oscA = ctx.createOscillator();
        const gainA = ctx.createGain();
        oscA.type = 'sine';
        oscA.frequency.setValueAtTime(freq, now);

        const voiceGain = idx === 0 ? 0.12 : 0.08;
        gainA.gain.setValueAtTime(0.0001, now);
        gainA.gain.linearRampToValueAtTime(voiceGain, now + attackDur);
        gainA.gain.setValueAtTime(voiceGain, now + chordDur - releaseDur);
        gainA.gain.exponentialRampToValueAtTime(0.0001, now + chordDur);

        oscA.connect(gainA);
        gainA.connect(dest);
        oscA.start(now);
        oscA.stop(now + chordDur + 0.05);

        oscA.onended = () => {
          try {
            oscA.disconnect();
            gainA.disconnect();
          } catch (e) {}
          const aIdx = activeMusicNodes.indexOf(oscA);
          if (aIdx !== -1) activeMusicNodes.splice(aIdx, 1);
        };
        activeMusicNodes.push(oscA);

        // Voice B: Soft triangle with ±4.5 cents chorus detune
        const oscB = ctx.createOscillator();
        const gainB = ctx.createGain();
        oscB.type = 'triangle';
        oscB.frequency.setValueAtTime(freq, now);
        oscB.detune.setValueAtTime(idx % 2 === 0 ? 4.5 : -4.5, now);

        const chorusGain = voiceGain * 0.45;
        gainB.gain.setValueAtTime(0.0001, now);
        gainB.gain.linearRampToValueAtTime(chorusGain, now + attackDur + 0.2);
        gainB.gain.setValueAtTime(chorusGain, now + chordDur - releaseDur);
        gainB.gain.exponentialRampToValueAtTime(0.0001, now + chordDur);

        oscB.connect(gainB);
        gainB.connect(dest);
        oscB.start(now);
        oscB.stop(now + chordDur + 0.05);

        oscB.onended = () => {
          try {
            oscB.disconnect();
            gainB.disconnect();
          } catch (e) {}
          const bIdx = activeMusicNodes.indexOf(oscB);
          if (bIdx !== -1) activeMusicNodes.splice(bIdx, 1);
        };
        activeMusicNodes.push(oscB);
      });

      // 3. Ethereal Twinkling Celestial Chime (Subtle star ping at 1.4s into chord)
      if (chordData.sparkle) {
        const starTime = now + 1.4;
        const starOsc = ctx.createOscillator();
        const starGain = ctx.createGain();
        const starFilter = ctx.createBiquadFilter();

        starFilter.type = 'lowpass';
        starFilter.frequency.setValueAtTime(2200, starTime);

        starOsc.type = 'sine';
        starOsc.frequency.setValueAtTime(chordData.sparkle, starTime);

        starGain.gain.setValueAtTime(0.0001, starTime);
        starGain.gain.linearRampToValueAtTime(0.035, starTime + 0.012);
        starGain.gain.exponentialRampToValueAtTime(0.0001, starTime + 2.2);

        starOsc.connect(starFilter);
        starFilter.connect(starGain);
        starGain.connect(dest);

        starOsc.start(starTime);
        starOsc.stop(starTime + 2.3);

        starOsc.onended = () => {
          try {
            starOsc.disconnect();
            starGain.disconnect();
            starFilter.disconnect();
          } catch (e) {}
          const sIdx = activeMusicNodes.indexOf(starOsc);
          if (sIdx !== -1) activeMusicNodes.splice(sIdx, 1);
        };
        activeMusicNodes.push(starOsc);
      }

    } catch (e) {
      console.warn('[AudioEngine] Ambient chord scheduling error:', e);
    }
  }

  function startCyberMusic() {
    stopCyberMusic();
    const ctx = getAudioContext();
    if (!ctx) return;

    if (ctx.state === 'suspended' || ctx.state === 'interrupted') {
      ctx.resume().catch(() => {});
    }

    musicEnabled = true;
    try { localStorage.setItem('atf_cyber_music_enabled', '1'); } catch (e) {}

    // Smooth fade-in of music master gain
    if (musicGain) {
      const now = ctx.currentTime;
      musicGain.gain.cancelScheduledValues(now);
      musicGain.gain.setValueAtTime(musicGain.gain.value || 0.0001, now);
      musicGain.gain.linearRampToValueAtTime(0.22, now + 1.2);
    }

    // Play first chord immediately
    scheduleAmbientChord();

    // Overlapping cross-fade interval: Chords play every 5.0s (overlapping by 1.2s for seamless continuity)
    musicTimer = setInterval(() => {
      if (!musicEnabled) return;
      scheduleAmbientChord();
    }, 5000);
  }

  function stopCyberMusic() {
    musicEnabled = false;
    try { localStorage.setItem('atf_cyber_music_enabled', '0'); } catch (e) {}

    if (musicTimer) {
      clearInterval(musicTimer);
      musicTimer = null;
    }

    const ctx = getAudioContext();
    if (ctx && musicGain) {
      const now = ctx.currentTime;
      try {
        musicGain.gain.cancelScheduledValues(now);
        musicGain.gain.setValueAtTime(musicGain.gain.value, now);
        musicGain.gain.linearRampToValueAtTime(0.0001, now + 0.6);
      } catch (e) {}
    }

    // Fade out and stop active nodes
    setTimeout(() => {
      activeMusicNodes.forEach(node => {
        try { node.stop(); } catch (e) {}
        try { node.disconnect(); } catch (e) {}
      });
      activeMusicNodes = [];
      if (musicGain) musicGain.gain.value = 0;
    }, 650);
  }

  function toggleCyberMusic() {
    unlockAudio();
    if (musicEnabled) {
      stopCyberMusic();
      return false;
    } else {
      startCyberMusic();
      return true;
    }
  }

  // Handle mobile tab visibility & backgrounding lifecycle
  if (typeof document !== 'undefined') {
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        // Pause timer to avoid scheduler buildup when backgrounded
        if (musicTimer) {
          clearInterval(musicTimer);
          musicTimer = null;
        }
      } else {
        // Tab restored: resume AudioContext and loop if enabled
        if (musicEnabled) {
          const ctx = getAudioContext();
          if (ctx && (ctx.state === 'suspended' || ctx.state === 'interrupted')) {
            ctx.resume().then(() => {
              if (musicEnabled && !musicTimer) {
                scheduleAmbientChord();
                musicTimer = setInterval(() => {
                  if (!musicEnabled) return;
                  scheduleAmbientChord();
                }, 5000);
              }
            }).catch(() => {});
          } else if (!musicTimer) {
            scheduleAmbientChord();
            musicTimer = setInterval(() => {
              if (!musicEnabled) return;
              scheduleAmbientChord();
            }, 5000);
          }
        }
      }
    });
  }

  /**
   * Dual-Layer Haptics & Tactile Feedback Engine
   * Combines Telegram WebApp HapticFeedback with Hardware Navigator Vibrate.
   */
  function triggerHaptic(type = 'light') {
    if (!hapticsEnabled) return;

    // 1. Telegram WebApp HapticFeedback
    try {
      const tg = global.Telegram?.WebApp?.HapticFeedback;
      if (tg) {
        if (type === 'light' || type === 'medium' || type === 'heavy' || type === 'rigid' || type === 'soft') {
          tg.impactOccurred(type);
        } else if (type === 'success' || type === 'warning' || type === 'error') {
          tg.notificationOccurred(type);
        } else if (type === 'selection') {
          tg.selectionChanged();
        }
      }
    } catch (e) {}

    // 2. Hardware Navigator Vibrate Fallback
    if (typeof navigator !== 'undefined' && navigator.vibrate) {
      try {
        if (type === 'light' || type === 'selection') {
          navigator.vibrate(15);
        } else if (type === 'medium') {
          navigator.vibrate(32);
        } else if (type === 'heavy') {
          navigator.vibrate([40, 25, 40]);
        } else if (type === 'success') {
          navigator.vibrate([25, 35, 55]);
        } else if (type === 'warning' || type === 'error') {
          navigator.vibrate([50, 30, 50]);
        }
      } catch (e) {}
    }
  }

  // Export to global window object
  global.playFX = playFX;
  global.triggerHaptic = triggerHaptic;
  global.playHaptic = triggerHaptic;
  global.startCyberMusic = startCyberMusic;
  global.stopCyberMusic = stopCyberMusic;
  global.toggleCyberMusic = toggleCyberMusic;
  global.isCyberMusicPlaying = () => musicEnabled;
  global.unlockAudio = unlockAudio;

  global.setAudioSfxEnabled = (enabled) => {
    sfxEnabled = !!enabled;
    try { localStorage.setItem('atf_sound_enabled', sfxEnabled ? '1' : '0'); } catch (e) {}
    if (sfxGain) {
      sfxGain.gain.value = sfxEnabled ? 0.65 : 0;
    }
  };
  global.isAudioSfxEnabled = () => sfxEnabled;

  global.setHapticsEnabled = (enabled) => {
    hapticsEnabled = !!enabled;
    try { localStorage.setItem('atf_haptics_enabled', hapticsEnabled ? '1' : '0'); } catch (e) {}
  };
  global.isHapticsEnabled = () => hapticsEnabled;

})(typeof window !== 'undefined' ? window : this);
