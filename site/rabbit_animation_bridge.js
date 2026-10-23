// The rabbit GIF is browser-decoded above the persistent Godot PNG portrait.
// No UI interaction is intercepted and no frame decoding runs in GDScript.
(function () {
  "use strict";
  const GIF_URL = "media/rabbit.gif";
  const FALLBACK_MATTE = "#120e0d";
  const GIF_SCALE = 1.045; // Slight zoom independent of the six PNG portraits.
  const SWAP_MS = 115; // Deliberate quick wipe, without overlapping two different poses.
  const PLAY_MS = 4100; // Trial timing, to be visually tuned to user's GIF.
  const IDLE_MS = 17000;
  let holder = null, bounds = null, enabled = false, generation = 0;
  let fadeTimer = null, idleTimer = null, releaseTimer = null, gifUnavailable = false;
  let gifMatte = "";

  function reducedMotion() {
    return typeof window.matchMedia === "function"
      && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }
  function ensureHolder() {
    if (holder) return holder;
    holder = document.createElement("div");
    holder.id = "vorgun-rabbit-animation";
    Object.assign(holder.style, {
      position: "fixed", pointerEvents: "none", overflow: "hidden",
      zIndex: "25", opacity: "1", display: "none",
      backgroundColor: FALLBACK_MATTE,
      clipPath: "inset(0 100% 0 0)", WebkitClipPath: "inset(0 100% 0 0)",
      transition: "clip-path " + SWAP_MS + "ms ease-out, -webkit-clip-path " + SWAP_MS + "ms ease-out"
    });
    document.body.appendChild(holder);
    return holder;
  }
  function position() {
    if (!holder || !bounds) return;
    const canvas = document.querySelector("canvas");
    if (!canvas || !canvas.getBoundingClientRect || bounds.vw <= 0 || bounds.vh <= 0) return;
    const cr = canvas.getBoundingClientRect();
    if (cr.width <= 0 || cr.height <= 0) return;
    const sx = cr.width / bounds.vw, sy = cr.height / bounds.vh;
    Object.assign(holder.style, {
      left: (cr.left + bounds.x * sx) + "px",
      top: (cr.top + bounds.y * sy) + "px",
      width: (bounds.w * sx) + "px",
      height: (bounds.h * sy) + "px"
    });
  }
  function sampleGifMatte(img) {
    // Sample an actual GIF corner after decode (same-origin Pages asset).
    // A 1px canvas avoids allocating/processing full animation frames on iOS.
    try {
      const sample = document.createElement("canvas");
      sample.width = 1;
      sample.height = 1;
      const ctx = sample.getContext("2d", { willReadFrequently: true });
      if (!ctx || img.naturalWidth < 2 || img.naturalHeight < 2) return;
      ctx.drawImage(img, 0, 0, 1, 1, 0, 0, 1, 1);
      const pixel = ctx.getImageData(0, 0, 1, 1).data;
      if (pixel[3] < 250) return;
      gifMatte = "#" + [pixel[0], pixel[1], pixel[2]]
        .map(v => v.toString(16).padStart(2, "0")).join("");
      if (holder) holder.style.backgroundColor = gifMatte;
    } catch (_) {
      // Unexpected GIF/CORS behavior: retain the local dark fallback.
    }
  }

  function setShutter(closed) {
    if (!holder) return;
    const mask = closed ? "inset(0 100% 0 0)" : "inset(0 0 0 0)";
    holder.style.clipPath = mask;
    holder.style.WebkitClipPath = mask; // iOS Safari.
  }
  function cancelTimers() {
    if (fadeTimer !== null) clearTimeout(fadeTimer);
    if (idleTimer !== null) clearTimeout(idleTimer);
    if (releaseTimer !== null) clearTimeout(releaseTimer);
    fadeTimer = null;
    idleTimer = null;
    releaseTimer = null;
  }
  function scheduleIdle() {
    if (!enabled || reducedMotion() || gifUnavailable) return;
    if (idleTimer !== null) clearTimeout(idleTimer);
    idleTimer = setTimeout(play, IDLE_MS);
  }
  function play() {
    if (!enabled || reducedMotion() || gifUnavailable) return;
    cancelTimers();
    const cycle = ++generation;
    ensureHolder();
    position();
    // A fresh <img> restarts animation while the URL stays HTTP-cacheable.
    const img = document.createElement("img");
    Object.assign(img.style, {
      display: "block", width: "100%", height: "100%",
      objectFit: "cover", objectPosition: "center center",
      transform: "scale(" + GIF_SCALE + ")",
      pointerEvents: "none"
    });
    img.alt = "";
    img.onload = function () {
      if (!enabled || cycle !== generation) return;
      if (!gifMatte) sampleGifMatte(img);
      setShutter(true);
      holder.style.display = "block";
      requestAnimationFrame(function () {
        if (!enabled || cycle !== generation) return;
        setShutter(false); // Fast reveal, no transparent face-on-face blend.
      });
      fadeTimer = setTimeout(function () {
        if (!enabled || cycle !== generation) return;
        setShutter(true); // Return to the relevant contextual PNG.
        releaseTimer = setTimeout(function () {
          if (!enabled || cycle !== generation) return;
          holder.replaceChildren();
          holder.style.display = "none";
        }, SWAP_MS + 20);
        scheduleIdle();
      }, PLAY_MS);
    };
    img.onerror = function () {
      if (cycle !== generation) return;
      gifUnavailable = true;
      setShutter(true);
      holder.style.display = "none";
    };
    holder.replaceChildren(img);
    setShutter(true);
    // Keep PNG until GIF is decoded; no transparent gap on slow iPhone loads.
    img.src = GIF_URL;
  }
  function setBounds(x, y, w, h, vw, vh) {
    bounds = { x: +x, y: +y, w: +w, h: +h, vw: +vw, vh: +vh };
    position();
  }
  function show(x, y, w, h, vw, vh) {
    setBounds(x, y, w, h, vw, vh);
    if (enabled) return;
    enabled = true;
    if (!reducedMotion()) play();
  }
  function sync(x, y, w, h, vw, vh) {
    setBounds(x, y, w, h, vw, vh);
  }
  function hide() {
    enabled = false;
    generation += 1;
    cancelTimers();
    if (holder) {
      setShutter(true);
      holder.style.display = "none";
      holder.replaceChildren();
    }
  }
  window.VorGunRabbit = {
    show: show, sync: sync, hide: hide,
    getBackgroundColor: function () { return gifMatte; }
  };
  window.addEventListener("resize", position);
  window.addEventListener("scroll", position, { passive: true });
})();