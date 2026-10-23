(() => {
  "use strict";
  const ua = navigator.userAgent || "";
  const ios = /iPhone|iPad|iPod/i.test(ua) ||
    (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  // One browser audio owner for every Web export, including desktop Web.
  // Never instantiate a competing Godot MP3 stream on Web.
  if (window.VorGunAudio?.isWebAudioOwner) return;

  const asset = filename => new URL("./media/" + filename, document.baseURI).href;
  const music = new Audio(asset("music.mp3"));
  music.preload = "auto";
  music.loop = true;
  music.playsInline = true;
  let unlocked = false;
  let musicEnabled = true, sfxEnabled = true;
  let musicVolume = 0.8, sfxVolume = 0.75;
  let context = null, output = null, musicGain = null, mediaSource = null;
  let lastError = "", plays = 0, musicStarts = 0, musicPlayPending = false;
  const sampleFiles = {
    hop: "cooper_chponk.wav",
    open: "door_open_office.wav",
    flush: "tube_water_flush.wav",
    birds: "bird_takeoff_soft_purr.wav",
    close: "door_close_soft.wav",
    select: "select_woosh.wav",
    menu: "menu_flip.wav"
  };
  const encoded = {}, decoded = {};
  music.volume = musicVolume;

  // Load asset bytes early. Decode with an AudioContext only after the first user gesture.
  for (const [kind, name] of Object.entries(sampleFiles)) {
    encoded[kind] = fetch(asset(name), { cache: "force-cache" })
      .then(response => { if (!response.ok) throw Error(name + " HTTP " + response.status); return response.arrayBuffer(); })
      .catch(error => { console.warn("VorGun SFX loading", kind, error); return null; });
  }

  function recordFailure(e) {
    lastError = e?.name || String(e);
    console.warn("VorGun iPhone audio", e);
  }
  function ensureMusic() {
    if (!unlocked || !musicEnabled || !music.paused || musicPlayPending) return;
    musicPlayPending = true;
    try {
      const pending = music.play();
      if (pending?.then) {
        pending.then(() => {
          musicPlayPending = false;
          musicStarts++;
          // A user can switch Music OFF while playback permission resolves.
          if (!musicEnabled) music.pause();
        }).catch(e => {
          musicPlayPending = false;
          recordFailure(e);
        });
      } else {
        musicPlayPending = false;
        musicStarts++;
      }
    } catch (e) {
      musicPlayPending = false;
      recordFailure(e);
    }
  }
  function resumeContext() {
    // iOS suspends AudioContext when the browser/player goes to the background.
    // Reuse the existing context; never build another music element or gain chain.
    if (context && context.state !== "running") {
      try {
        const resumed = context.resume();
        if (resumed?.catch) resumed.catch(recordFailure);
      } catch (e) { recordFailure(e); }
    }
  }
  function unlock() {
    if (unlocked) {
      // A previous play() can fail with NotAllowedError or iOS can interrupt
      // audio after lock-screen/app switching. Retry on the next real tap.
      resumeContext();
      ensureMusic();
      return;
    }
    unlocked = true;
    const Ctx = window.AudioContext || window.webkitAudioContext;
    if (Ctx) {
      try {
        context = new Ctx();
        output = context.createGain();
        output.gain.value = sfxEnabled ? sfxVolume : 0;
        output.connect(context.destination);
        // Safari iOS often ignores HTMLAudioElement.volume: use WebAudio GainNode.
        if (typeof context.createMediaElementSource === "function") {
          mediaSource = context.createMediaElementSource(music);
          musicGain = context.createGain();
          musicGain.gain.value = musicVolume;
          mediaSource.connect(musicGain);
          musicGain.connect(context.destination);
          music.volume = 1;
        }
        const resumed = context.resume();
        if (resumed?.catch) resumed.catch(recordFailure);
        for (const [kind, bytes] of Object.entries(encoded)) {
          bytes.then(ab => {
            if (!ab || !context) return;
            return context.decodeAudioData(ab.slice(0))
              .then(buffer => { decoded[kind] = buffer; })
              .catch(error => { console.warn("VorGun SFX decode", kind, error); });
          }).catch(recordFailure);
        }
      } catch (e) { recordFailure(e); }
    }
    ensureMusic();
  }
  function onGesture(event) {
    if (event.isTrusted) unlock();
  }
  document.addEventListener("touchend", onGesture, { capture: true, passive: true });
  document.addEventListener("click", onGesture, { capture: true });
  function setVolume(v) {
    musicVolume = Math.max(0, Math.min(1, Number(v) || 0));
    if (musicGain) {
      musicGain.gain.value = musicVolume;
      music.volume = 1;
    } else music.volume = musicVolume;
  }
  function setMusicEnabled(v) {
    musicEnabled = Boolean(v);
    if (!musicEnabled) music.pause();
    else ensureMusic();
  }
  function setSfxVolume(v) {
    sfxVolume = Math.max(0, Math.min(1, Number(v) || 0));
    if (output) output.gain.value = sfxEnabled ? sfxVolume : 0;
  }
  function setSfxEnabled(v) {
    sfxEnabled = Boolean(v);
    if (output) output.gain.value = sfxEnabled ? sfxVolume : 0;
  }
  function quickSynth(kind) {
    // Very first landing can precede WAV decoding; use a transient instead of silence.
    if (!context || !output || context.state !== "running") return;
    const osc = context.createOscillator(), gain = context.createGain();
    const now = context.currentTime;
    osc.type = kind === "open" || kind === "close" ? "triangle" : "sine";
    const startHz = {hop:380,open:220,close:150,select:720,menu:620}[kind] || 460;
    osc.frequency.setValueAtTime(startHz, now);
    osc.frequency.exponentialRampToValueAtTime(Math.max(75, startHz * 0.57), now + 0.14);
    gain.gain.setValueAtTime(0.001, now);
    gain.gain.exponentialRampToValueAtTime(0.24, now + 0.009);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.16);
    osc.connect(gain); gain.connect(output);
    osc.start(now); osc.stop(now + 0.17);
  }
  function playFlush() {
    // Deliberately comic suction / plumbing whoosh; no speech generated.
    // Three overlapping pitch falls, mixed ONLY through the SFX gain node.
    if (!unlocked || !sfxEnabled || sfxVolume <= 0 || !context || !output) return;
    if (context.state !== "running") {
      context.resume().catch(recordFailure);
      return;
    }
    const now = context.currentTime;
    for (let i = 0; i < 3; i++) {
      const source = context.createOscillator();
      const volume = context.createGain();
      const t = now + i * 0.15;
      source.type = i === 1 ? "triangle" : "sine";
      source.frequency.setValueAtTime(660 - 135 * i, t);
      source.frequency.exponentialRampToValueAtTime(90 - 13 * i, t + 1.08);
      volume.gain.setValueAtTime(0.001, t);
      volume.gain.exponentialRampToValueAtTime(0.20 - i * 0.035, t + 0.055);
      volume.gain.exponentialRampToValueAtTime(0.001, t + 1.12);
      source.connect(volume);
      volume.connect(output);
      source.start(t);
      source.stop(t + 1.13);
    }
    plays++;
  }
  function playBoat() {
    // Low, watery paddle hum — only on the SFX bus, never the looping MP3.
    if (!unlocked || !sfxEnabled || sfxVolume <= 0 || !context || !output) return;
    if (context.state !== "running") { context.resume().catch(recordFailure); return; }
    const source = context.createOscillator();
    const env = context.createGain();
    const now = context.currentTime;
    source.type = "triangle";
    source.frequency.setValueAtTime(175, now);
    source.frequency.exponentialRampToValueAtTime(108, now + 1.4);
    env.gain.setValueAtTime(0.001, now);
    env.gain.exponentialRampToValueAtTime(0.10, now + 0.12);
    env.gain.exponentialRampToValueAtTime(0.001, now + 1.45);
    source.connect(env);
    env.connect(output);
    source.start(now);
    source.stop(now + 1.45);
    plays++;
  }
  function play(kind) {
    if (!unlocked || !sfxEnabled || sfxVolume <= 0) return;
    if (!context || !output) return;
    if (context.state !== "running") {
      context.resume().catch(recordFailure);
      return;
    }
    // The pneumatic tube needs an audible pressure drop on mobile even when
    // the decoded WAV is exceptionally quiet. Layer the existing short swoosh
    // over its source sample, still on the single SFX bus.
    if (kind === "flush") playFlush();
    const data = decoded[kind];
    if (!data) { if (kind === "birds" || kind === "flush") return; quickSynth(kind); return; }
    const src = context.createBufferSource();
    src.buffer = data;
    if (kind === "birds") {
      const gentle = context.createGain();
      gentle.gain.value = 0.38;
      src.connect(gentle);
      gentle.connect(output);
    } else src.connect(output);
    src.start();
    plays++;
  }
  // Idempotent singleton. Scene changes are not playback events.
  window.VorGunAudio = {
    isIOS: ios,
    isWebAudioOwner: true,
    enableFromTap: unlock,
    startMusic: ensureMusic,
    setMusicEnabled, setVolume, setSfxEnabled, setSfxVolume,
    playHop: () => play("hop"),
    playDoor: opening => play(opening ? "open" : "close"),
    playAction: kind => kind === "birds" ? play("birds") : kind === "flush" ? play("flush") : kind === "boat" ? playBoat() : play(kind === "menu" ? "menu" : "select"),
    diagnostic: () => ({
      unlocked, musicEnabled, sfxEnabled, musicVolume, sfxVolume,
      musicPaused: music.paused, musicTime: music.currentTime,
      musicStarts, musicPlayPending, plays, contextState: context?.state || "none",
      decoded: Object.keys(decoded), lastError
    })
  };
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden && unlocked && musicEnabled) {
      // Recover the suspended WebAudio graph on return from iPhone browser UI;
      // a subsequent trusted touch retries music if autoplay is blocked.
      resumeContext();
      ensureMusic();
    }
  });
})();