/* NOSTRO front — digit-stream background + live node data */
(function () {
  "use strict";

  var $ = function (id) { return document.getElementById(id); };
  var REDUCED = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var TAU = Math.PI * 2;

  /* ============ digit stream (vanilla port of DigitStream) ============ */
  (function digitStream() {
    var canvas = $("wave");
    if (!canvas || !canvas.getContext) return;
    var ctx = canvas.getContext("2d");

    var CFG = {
      particleCount: window.innerWidth < 760 ? 320 : 700,
      speed: 0.4,
      flowStrength: 0.5,
      disperseStrength: 1,
      idleDim: 0.65,
      snakeAmplitude: 0.5,
      color: [171, 224, 255],
      colorfulSparks: true,
    };
    var WAVES = 2.4, WAVES2 = 5.5, PHASE = -0.35, PHASE2 = 0.2, WAVESY = 3, AMPY = 0.02;
    var IDLE_MS = 160;

    function pathPoint(t, amp) {
      var amp2 = amp * 0.37;
      return {
        x: 0.5 + amp * Math.sin((t * WAVES + PHASE) * TAU) + amp2 * Math.sin((t * WAVES2 + PHASE2) * TAU),
        y: -0.06 + t * 1.12 + AMPY * Math.sin(t * WAVESY * TAU),
      };
    }
    function pathTangent(t, amp) {
      var e = 0.001;
      var a = pathPoint(Math.max(0, t - e), amp);
      var b = pathPoint(Math.min(1, t + e), amp);
      var dx = b.x - a.x, dy = b.y - a.y;
      var len = Math.hypot(dx, dy) || 1;
      return { x: dx / len, y: dy / len };
    }
    function rand(a, b) { return a + Math.random() * (b - a); }
    function randDigit() {
      return Math.random() < 0.5 ? (Math.random() < 0.5 ? "7" : "0")
        : String(Math.floor(Math.random() * 10));
    }
    function spawn() {
      var wide = Math.random() < 0.28;
      var t = Math.random();
      return {
        t: t,
        off: wide ? rand(-0.16, 0.16) : rand(-0.03, 0.03),
        speed: rand(0.0001, 0.0004),
        size: Math.round(rand(7, 13)),
        hue: rand(190, 320),
        colorful: Math.random() < 0.3 && t < 0.55,
        life: rand(0.5, 1),
        wAmp: rand(0.02, 0.1),
        wFreq: rand(1.5, 5),
        wPhase: rand(0, TAU),
        ch: randDigit(),
        dAx: rand(0.06, 0.24) * (Math.random() < 0.5 ? -1 : 1),
        dAy: rand(0.02, 0.09) * (Math.random() < 0.5 ? -1 : 1),
        dFx: rand(0.3, 1.1), dFy: rand(0.3, 1.1),
        dPx: rand(0, TAU), dPy: rand(0, TAU),
      };
    }

    var W = 0, H = 0;
    var dpr = Math.min(window.devicePixelRatio || 1, 1.75);
    var particles = [];
    var bright = 1, disperse = 0, drift = 0, flow = 0;
    var lastActivity = 0;
    var running = false, rafId = null;

    function resize() {
      W = Math.max(1, window.innerWidth);
      H = Math.max(1, window.innerHeight);
      canvas.width = Math.round(W * dpr);
      canvas.height = Math.round(H * dpr);
      canvas.style.width = W + "px";
      canvas.style.height = H + "px";
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    resize();
    window.addEventListener("resize", resize);

    for (var i = 0; i < CFG.particleCount; i++) particles.push(spawn());

    var lastScrollY = window.scrollY;
    function bump(delta) {
      flow += delta * 0.0007 * CFG.flowStrength;
      lastActivity = performance.now();
    }
    window.addEventListener("scroll", function () {
      bump(window.scrollY - lastScrollY);
      lastScrollY = window.scrollY;
    }, { passive: true });
    window.addEventListener("wheel", function (e) { bump(e.deltaY); }, { passive: true });

    function draw(staticPass) {
      var amp = CFG.snakeAmplitude * 0.3;
      var speedK = CFG.speed / 0.4;
      var idle = performance.now() - lastActivity > IDLE_MS;
      bright += ((idle ? CFG.idleDim : 1) - bright) * (idle ? 0.03 : 0.12);
      disperse += ((idle ? 1 : 0) - disperse) * (idle ? 0.01 : 0.06);
      drift += 0.02;
      var disp = disperse * CFG.disperseStrength;
      var c = CFG.color;

      ctx.globalCompositeOperation = "destination-out";
      ctx.fillStyle = "rgba(0,0,0,0.14)";
      ctx.fillRect(0, 0, W, H);

      ctx.globalCompositeOperation = "lighter";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      for (var i = 0; i < particles.length; i++) {
        var pt = particles[i];
        pt.t += pt.speed * speedK * (staticPass ? 40 : 1);
        if (pt.t >= 1) pt.t -= 1;
        if (Math.random() < 0.003) pt.ch = randDigit();
        var et = pt.t + flow;
        et -= Math.floor(et);
        var p = pathPoint(et, amp);
        var tan = pathTangent(et, amp);
        var wander = pt.wAmp * Math.sin(et * pt.wFreq * TAU + pt.wPhase);
        var totalOff = pt.off + wander;
        var wx = disp * pt.dAx * Math.sin(drift * pt.dFx + pt.dPx);
        var wy = disp * pt.dAy * Math.sin(drift * pt.dFy + pt.dPy);
        var x = (p.x + -tan.y * totalOff + wx) * W;
        var y = (p.y + tan.x * totalOff + wy) * H;
        var coreFade = 1 - Math.min(1, Math.abs(totalOff) / 0.22);
        var alpha = (0.28 * coreFade * pt.life + 0.02) * bright;
        ctx.font = pt.size + 'px "JetBrains Mono", ui-monospace, Menlo, monospace';
        ctx.fillStyle = CFG.colorfulSparks && pt.colorful
          ? "hsla(" + pt.hue + ", 60%, 66%, " + alpha + ")"
          : "rgba(" + c[0] + "," + c[1] + "," + c[2] + "," + alpha + ")";
        ctx.fillText(pt.ch, x, y);
      }
    }

    function frame() {
      if (!running) return;
      rafId = requestAnimationFrame(frame);
      draw(false);
    }
    if (REDUCED) {
      for (var s = 0; s < 26; s++) draw(true);
      return;
    }
    function start() { if (!running) { running = true; frame(); } }
    function stop() { running = false; if (rafId) cancelAnimationFrame(rafId); rafId = null; }
    document.addEventListener("visibilitychange", function () {
      if (document.hidden) stop(); else start();
    });
    start();
  })();

  /* ============ reveal ============ */
  var rvEls = document.querySelectorAll(".rv");
  if ("IntersectionObserver" in window && !REDUCED) {
    var ro = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add("in"); ro.unobserve(en.target); }
      });
    }, { threshold: 0.1, rootMargin: "0px 0px -30px 0px" });
    rvEls.forEach(function (el) { ro.observe(el); });
  } else {
    rvEls.forEach(function (el) { el.classList.add("in"); });
  }

  /* ============ live data ============ */
  var HEX = "0123456789abcdef";
  var lastHashEpoch = null;
  var TAPE_BUILT = false;

  function fmt(n, d) {
    return Number(n).toLocaleString("en-US", { maximumFractionDigits: d || 0 });
  }

  function scrambleHash(el, target) {
    if (REDUCED) { el.textContent = target; return; }
    var t0 = performance.now(), dur = 1400, len = target.length;
    function step(now) {
      var p = Math.min(1, (now - t0) / dur);
      var locked = Math.floor(p * len);
      var out = target.slice(0, locked);
      for (var i = locked; i < len; i++) {
        out += i < 2 ? target[i] : HEX[(Math.random() * 16) | 0];
      }
      el.textContent = out;
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  function buildTape(s) {
    var tape = $("tape");
    if (!tape) return;
    var items = Object.keys(s.prices).map(function (a) {
      var w = s.weights[a];
      return '<span class="tape-item">' + a + " <b>" + fmt(s.prices[a], 2) + "</b>" +
        (w ? ' <span class="w">' + (w / 100).toFixed(1) + "%</span>" : "") +
        "</span>";
    }).join("");
    tape.innerHTML = items + items + items + items;
    TAPE_BUILT = true;
  }

  function renderMini(s) {
    var el = $("miniBasket");
    if (!el) return;
    var entries = Object.entries(s.weights).sort(function (a, b) {
      if (a[0] === "USDG") return 1;
      if (b[0] === "USDG") return -1;
      return b[1] - a[1];
    }).slice(0, 5);
    var maxW = Math.max.apply(null, entries.map(function (e) { return e[1]; }).concat([1]));
    el.innerHTML = entries.map(function (e) {
      return '<div class="mb-row"><span class="mb-t">' + e[0] + "</span>" +
        '<div class="mb-bar"><div class="mb-fill' + (e[0] === "USDG" ? " cash" : "") +
        '" style="width:' + (e[1] / maxW * 100).toFixed(1) + '%"></div></div>' +
        '<span class="mb-w">' + (e[1] / 100).toFixed(1) + "%</span></div>";
    }).join("");
  }

  function renderCommit(s) {
    var rec = null;
    for (var i = s.track.length - 1; i >= 0; i--) {
      if (s.track[i].hash) { rec = s.track[i]; break; }
    }
    if (!rec) return;
    $("cEpoch").textContent = rec.epoch;
    var st = $("cStatus");
    if (!rec.revealed) {
      st.innerHTML = 'the thesis stays sealed until the epoch ends<span class="cursor">▌</span>';
      st.className = "dim";
    } else if (rec.verified) {
      st.textContent = "opened / keccak256 checked out / part of the public record";
      st.className = "term-ok";
    } else {
      st.textContent = "opened / hashes disagree / epoch stamped failed";
      st.className = "term-bad";
    }
    if (rec.epoch !== lastHashEpoch) {
      lastHashEpoch = rec.epoch;
      scrambleHash($("cHash"), rec.hash);
    }
  }

  function renderPhases(s) {
    document.querySelectorAll(".ph li[data-ph]").forEach(function (li) {
      var p = parseInt(li.getAttribute("data-ph"), 10);
      li.classList.toggle("active", p === s.phase);
      li.classList.toggle("past", p < s.phase);
    });
  }

  function shortAddr(a) {
    return a && a.length > 12 ? a.slice(0, 8) + "…" + a.slice(-6) : (a || "—");
  }

  function setState(ok, s) {
    var el = $("stState");
    if (!el) return;
    if (!ok) {
      el.className = "strip-state err";
      el.textContent = "NODE DOWN — START IT: python3 server.py";
      return;
    }
    if (s && s.mode === "live") {
      el.className = "strip-state";
      el.textContent = "ON-CHAIN · LIVE";
    } else if (s && s.public) {
      el.className = "strip-state sim";
      el.textContent = "ON STANDBY / GOING LIVE ON PONS V2";
    } else {
      el.className = "strip-state sim";
      el.textContent = "SIMULATED DATA / LOCAL NODE / CONCEPT V0.1";
    }
  }

  function setMode(s) {
    var live = s.mode === "live";
    var noSim = live || s.public;
    document.querySelectorAll(".sim-only").forEach(function (el) { el.hidden = noSim; });
    var lv = $("stLive");
    var tapeEl = document.querySelector(".tape");
    if (tapeEl) tapeEl.style.display = noSim ? "none" : "";
    var mb = $("miniBasket");
    if (mb) mb.style.display = noSim ? "none" : "";
    if (!lv) return;
    lv.hidden = !noSim;
    if (!live && s.public) {
      lv.textContent = "NO TOKEN ADDRESS HAS BEEN ATTACHED YET";
      return;
    }
    if (live && s.live && s.live.ok) {
      var L = s.live;
      var tail;
      if (L.kind === "token") {
        var P = L.pons || {};
        tail = (P.graduated ? "<b>GRADUATED · UNISWAP V4</b> · "
            : (P.progress_pct != null ? "CURVE <b>" + P.progress_pct + "%</b> · " : "")) +
          "TOKEN <b>" + shortAddr(L.vault) + "</b>";
      } else {
        tail = "EPOCH <b>" + (L.current_epoch != null ? L.current_epoch : "—") +
          "</b> · VAULT <b>" + shortAddr(L.vault) + "</b>";
      }
      lv.innerHTML =
        "CHAIN <b>" + L.chain_id + "</b> · BLOCK <b>" + fmt(L.block) + "</b> · " +
        (L.symbol || "?") + " SUPPLY <b>" + (L.total_supply != null ? fmt(L.total_supply) : "—") +
        "</b> · " + tail;
    } else if (live) {
      lv.textContent = "pulling chain state…";
    }
  }

  function tick() {
    fetch("/api/state").then(function (r) { return r.json(); }).then(function (s) {
      $("stEpoch").textContent = s.epoch;
      $("stNav").textContent = fmt(s.nav);
      $("stUnit").textContent = s.unit_value.toFixed(4);
      $("stRun").textContent = fmt(s.treasury.runway_days, 0);
      $("stPhase").textContent = s.phase;
      var noSim = s.mode === "live" || s.public;
      if (!TAPE_BUILT && !noSim) buildTape(s);
      setMode(s);
      if (!noSim) {
        renderMini(s);
        renderCommit(s);
      } else {
        var st = $("cStatus");
        if (st) {
          st.className = "dim";
          st.innerHTML = 'once the vault is live, commits land on the public record<span class="cursor">▌</span>';
        }
      }
      renderPhases(s);
      setState(true, s);
    }).catch(function () { setState(false); });
  }
  tick();
  setInterval(tick, 2000);
})();
