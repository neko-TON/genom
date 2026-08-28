/* NOSTRO CONSOLE — клиент локального узла */
(function () {
  "use strict";

  var $ = function (id) { return document.getElementById(id); };
  var state = null;

  function fmt(n, d) {
    return Number(n).toLocaleString("en-US", {
      maximumFractionDigits: d == null ? 0 : d,
      minimumFractionDigits: d == null ? 0 : d,
    });
  }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function simDay(t) {
    var d = Math.floor(t / 86400), rest = t % 86400;
    var h = Math.floor(rest / 3600), m = Math.floor((rest % 3600) / 60);
    return "D" + d + " " + String(h).padStart(2, "0") + ":" + String(m).padStart(2, "0");
  }
  function post(path, body) {
    return fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    }).then(function (r) { return r.json(); })
      .then(function (r) { refresh(); return r; })
      .catch(function () {});
  }

  /* ---------- render ---------- */
  var SIM_CARDS = ["cardBasket", "cardChart", "cardTrack", "cardGuard",
                   "cardHolders", "cardWallet", "cardTreasury", "cardGov", "cardLog"];

  function show(id, on) {
    var el = $(id);
    if (el) el.hidden = !on;
  }

  function render(s) {
    state = s;
    var live = s.mode === "live";
    // мок-симуляция видна только на локальном (непубличном) узле
    var showSim = !live && !s.public;
    var R = s.real;
    var hasReal = live && R && R.epochs && R.epochs.length;

    // sim-карточки: либо симуляция, либо живые данные агента
    show("cardBasket", showSim || (live && s.live && s.live.basket));
    show("cardChart", showSim || (hasReal && R.uv && R.uv.length > 1));
    show("cardHolders", showSim || (hasReal && R.holders.length));
    show("cardGuard", showSim || (hasReal && R.last && R.last.checks.length));
    show("cardTrack", showSim);
    show("cardWallet", showSim);
    show("cardTreasury", showSim);
    show("cardGov", showSim);
    show("cardLog", showSim);

    var ctl = document.querySelector(".top-ctl");
    if (ctl) ctl.style.display = showSim ? "" : "none";

    renderTop(s); renderLaunch(s); renderAlerts(s);
    renderWalletUI(); refreshOnWallet();

    if (showSim) {
      renderBasket(s); renderChart(s);
      renderTrack(s); renderGuard(s); renderHolders(s); renderWallet(s);
      renderTreasury(s); renderGov(s); renderLog(s);
      return;
    }
    if (live) {
      if (s.live && s.live.basket) renderBasketLive(s.live.basket, R);
      if (hasReal) {
        if (R.uv && R.uv.length > 1) renderChartLive(R);
        if (R.holders.length) renderHoldersLive(R);
        if (R.last && R.last.checks.length) renderGuardLive(R);
      }
    }
  }

  /* ---------- живые рендеры (реальные ончейн-данные) ---------- */

  function priceOf(sym, R) {
    if (sym === "USDG") return 1;
    if (sym === "ETH") return 0;   // ETH держим как рабочий остаток, не позиция
    return (R && R.prices && R.prices[sym]) || 0;
  }

  function renderBasketLive(B, R) {
    var head = document.querySelector("#cardBasket h2");
    if (head) head.innerHTML = '<span class="cn mono">NostroBasket</span> Basket — real holdings on Uniswap v4';
    var rows = (B.positions || []).map(function (p) {
      return { sym: p.symbol, amount: p.amount, value: p.amount * priceOf(p.symbol, R) };
    });
    var nav = rows.reduce(function (a, r) { return a + r.value; }, 0);
    var maxV = Math.max.apply(null, rows.map(function (r) { return r.value; }).concat([1e-9]));
    $("basket").innerHTML = rows.sort(function (a, b) { return b.value - a.value; })
      .map(function (r) {
        var pct = nav > 0 ? (r.value / nav * 100) : 0;
        return '<div class="b-row"><span class="b-tkr">' + esc(r.sym) + "</span>" +
          '<div class="b-bar"><div class="b-fill' + (r.sym === "USDG" ? " cash" : "") +
          '" style="width:' + (r.value / maxV * 100).toFixed(1) + '%"></div></div>' +
          '<span class="b-w">' + (r.value > 0 ? pct.toFixed(1) + "% · " : "") +
          fmt(r.amount, r.sym === "ETH" ? 6 : 4) + "</span>" +
          '<span class="b-p">' + (priceOf(r.sym, R) ? "$" + fmt(priceOf(r.sym, R), 2) : "—") +
          "</span></div>";
      }).join("");
    var tgt = R && R.weights ? Object.keys(R.weights).map(function (k) {
      return k + " " + (R.weights[k] / 100).toFixed(0) + "%";
    }).join(" · ") : "";
    $("basketFoot").textContent =
      "NAV ≈ " + fmt(nav, 4) + " USDG · agent target: " + (tgt || "—");
  }

  function renderChartLive(R) {
    var head = document.querySelector("#cardChart h2");
    if (head) head.innerHTML = '<span class="cn mono">NAV</span> Unit value — real prices, real epochs';
    drawChart(R.uv, null);
    var lg = document.querySelector("#cardChart .legend");
    if (lg) lg.innerHTML = '<span><i class="sw sw-fact"></i>unit value since epoch 1 (' +
      R.uv.length + " epochs)</span>";
  }

  function renderHoldersLive(R) {
    var head = document.querySelector("#cardHolders h2");
    if (head) head.innerHTML = '<span class="cn mono">weight × time</span> Holders — indexed from Transfer logs';
    var L = state.live || {};
    var known = {};
    if (L.pons && L.pons.curve) known[L.pons.curve.toLowerCase()] = "bonding curve · unsold supply";
    if (L.fee_vault) known[L.fee_vault.address.toLowerCase()] = "nostro fee vault";
    if (L.basket) known[L.basket.address.toLowerCase()] = "nostro basket";
    var maxShare = Math.max.apply(null, R.holders.map(function (h) { return h.share; }).concat([0.0001]));
    $("holders").innerHTML = '<table class="h"><tr>' +
      "<th>wallet</th><th class='r'>$NSTRO</th><th>epoch share</th><th class='r'>accrued ETH</th></tr>" +
      R.holders.map(function (h) {
        var barW = Math.max(2, h.share / maxShare * 90);
        var tag = known[h.id.toLowerCase()];
        if (tag) {
          return "<tr style='opacity:.55'><td>" + esc(h.name) +
            '<span class="tag tag-bot">' + esc(tag) + "</span></td>" +
            "<td class='r'>" + fmt(h.balance) + "</td>" +
            "<td><span class='mono' style='font-size:11px'>—</span></td>" +
            "<td class='r'>—</td></tr>";
        }
        return "<tr><td>" + esc(h.name) + "</td>" +
          "<td class='r'>" + fmt(h.balance) + "</td>" +
          "<td><span class='share-bar' style='width:" + barW + "px'></span> " +
          "<span class='mono' style='font-size:11px'>" + (h.share * 100).toFixed(2) + "%</span></td>" +
          "<td class='r'>" + fmt(h.claimable, 8) + "</td></tr>";
      }).join("") + "</table>" +
      '<p class="foot">Shares accrue as balance × holding time, indexed straight from on-chain Transfer events.</p>';
  }

  function renderGuardLive(R) {
    var head = document.querySelector("#cardGuard h2");
    if (head) head.innerHTML = '<span class="cn mono">MandateGuard</span> Latest vector check — epoch ' + (R.last.n + 1);
    var e = R.last;
    $("guard").innerHTML = e.checks.map(function (c) {
      return '<div class="g-row ' + (c.ok ? "g-ok" : "g-bad") + '">' +
        '<span class="g-dot"></span><span class="g-name">' + esc(c.name) + "</span>" +
        '<span class="g-detail">' + esc(c.detail) + "</span></div>";
    }).join("") +
      (e.cancelled
        ? '<p class="g-cancel">epoch cancelled: ' + esc(e.cancelled) + "</p>"
        : '<p class="foot">vector accepted' +
          (e.executed ? " and executed on-chain via Uniswap v4" : " · sealed, no trade needed") +
          "</p>");
  }

  /* ---------- live chain (configured via ./nstro CLI) ---------- */
  function shortAddr(a) {
    return a && a.length > 12 ? a.slice(0, 8) + "…" + a.slice(-6) : (a || "—");
  }

  function commitsTrack(CM) {
    if (!CM || !CM.records || !CM.records.length) return "";
    var rows = CM.records.slice(0, 6).map(function (r) {
      var badge = r.failed
        ? '<span class="t-badge t-fail">mismatch — failed</span>'
        : r.revealed
          ? '<span class="t-badge t-ok">keccak verified</span>'
          : '<span class="t-badge t-sealed">thesis sealed</span>';
      var link = "https://robinhoodchain.blockscout.com/address/" + CM.address;
      return '<div class="t-item"><div class="t-head">' +
        '<span class="t-ep">E-' + r.epoch + "</span>" +
        '<a class="t-hash" target="_blank" rel="noopener" href="' + link + '">' +
        r.hash.slice(0, 22) + "…" + r.hash.slice(-8) + "</a>" + badge + "</div>" +
        '<div class="t-meta">commit ' + simDay(r.committed_at) +
        (r.revealed_at ? " → reveal " + simDay(r.revealed_at) : " · on-chain, awaiting reveal") +
        "</div></div>";
    }).join("");
    return '<div style="margin-top:16px"><p class="foot mono" style="margin-bottom:8px">' +
      'ON-CHAIN TRACK RECORD · every hash is a real transaction in NostroCommits</p>' +
      rows + "</div>";
  }

  function renderLaunch(s) {
    var card = $("cardLive"), box = $("liveInfo"), st = $("cfgStatus");
    if (!card || !box) return;
    card.hidden = !(s.mode === "live" || s.public);
    if (s.mode !== "live") {
      if (s.public) {
        st.className = "mono lf-status";
        st.textContent = "standby — the token address has not been connected yet";
        box.innerHTML = "";
      } else {
        box.innerHTML = "";
      }
      return;
    }
    var L = s.live;
    if (!L) { st.className = "mono lf-status"; st.textContent = "connecting…"; return; }
    if (!L.ok) {
      st.className = "mono lf-status err";
      st.textContent = L.error || "chain unreachable";
      box.innerHTML = "";
      return;
    }
    st.className = "mono lf-status ok";
    st.textContent = (L.kind === "token" ? "watching the launch token" : "reading the vault") + " every 4s";
    function cell(k, v) {
      return '<div class="live-cell"><span>' + k + "</span><b>" + v + "</b></div>";
    }
    var supply = L.total_supply != null ? fmt(L.total_supply) : "—";
    var cells =
      cell("chain id", L.chain_id) +
      cell("block", fmt(L.block)) +
      cell("contract", (L.name || "?") + " · " + (L.symbol || "?") + " · " + fmt(L.code_size) + " bytes") +
      cell("total supply", supply);
    if (L.kind === "token") {
      var P = L.pons || {};
      if (P.registered != null) cells += cell("pons factory", P.registered ? "registered" : "not found");
      if (P.graduated) {
        cells += cell("status", '<span style="color:var(--good)">GRADUATED — UNISWAP V4</span>');
        cells += cell("curve", "100% — pool is live, LP locked");
      } else if (P.phase_label) {
        cells += cell("status", P.phase_label);
      }
      if (!P.graduated && P.progress_pct != null) cells += cell("curve progress", P.progress_pct + "%" +
        (P.graduation_threshold ? " of " + fmt(P.graduation_threshold, 2) : ""));
      if (!P.graduated && P.ready != null) cells += cell("ready to graduate", P.ready ? "YES" : "no");
      if (P.pair) cells += cell("pair", P.pair === "ETH" ? "ETH" : shortAddr(P.pair));
      if (P.fees_accrued != null) cells += cell("creator fees accrued",
        fmt(P.fees_accrued, 5) + " " + (P.fees_asset === "ETH" ? "ETH" : "(pair)"));
      if (P.fee_bps != null) cells += cell("pool fee", (P.fee_bps / 100) + "%");
      if (P.creator_tax_bps != null) cells += cell("creator tax", (P.creator_tax_bps / 100) + "%");
      if (P.buyback != null) cells += cell("buyback", P.buyback ? "on" : "off");
      cells += cell("token", shortAddr(L.vault));
      if (L.fee_vault) {
        var FV = L.fee_vault;
        cells += cell("nostro vault · received", fmt(FV.total, 6) + " ETH") +
          cell("basket 80%", fmt(FV.basket, 6)) +
          cell("agent ops 13%", fmt(FV.agent, 6)) +
          cell("protocol 7%", fmt(FV.protocol, 6)) +
          (FV.weth_pending ? cell("weth pending", fmt(FV.weth_pending, 6) + " → processWETH()") : "") +
          cell("vault address", shortAddr(FV.address));
      }
      if (L.commits) {
        var CM = L.commits;
        cells += cell("commitstore · epoch", CM.epoch) +
          cell("sealed decisions", CM.committed) +
          cell("revealed", CM.revealed) +
          cell("failed reveals", CM.failed);
      }
      if (L.basket) cells += cell("basket address", shortAddr(L.basket.address));
      box.innerHTML = '<div class="live-grid">' + cells + "</div>" +
        '<div class="gov-btns" style="margin-top:14px">' +
        '<a class="act act-ice" target="_blank" rel="noopener" href="https://ponsfamily.com/' + L.vault + '">trade on pons ↗</a>' +
        '<a class="act" target="_blank" rel="noopener" href="https://robinhoodchain.blockscout.com/token/' + L.vault + '">explorer ↗</a>' +
        "</div>" + commitsTrack(L.commits);
      return;
    }
    {
      cells +=
        cell("epoch (on-chain)", L.current_epoch != null ? L.current_epoch : "—") +
        cell("nav", L.nav != null ? fmt(L.nav, 2) + " USDG" : "—") +
        cell("units outstanding", L.units != null ? fmt(L.units, 2) : "—") +
        cell("guard", shortAddr(L.linked && L.linked.guard)) +
        cell("executor", shortAddr(L.linked && L.linked.executor)) +
        cell("oracle", shortAddr(L.linked && L.linked.oracle)) +
        cell("governance", shortAddr(L.linked && L.linked.governance)) +
        cell("vault", shortAddr(L.vault));
    }
    box.innerHTML = '<div class="live-grid">' + cells + "</div>";
  }

  function renderTop(s) {
    if (s.mode === "live" || s.public) {
      $("topStats").innerHTML =
        '<span class="mode-tag ' + (s.mode === "live" ? "live" : "sim") + '">' +
        (s.mode === "live" ? "LIVE ON-CHAIN" : "STANDBY") + "</span>" +
        (s.mode === "live" && s.live && s.live.ok
          ? "<span>chain <b>" + s.live.chain_id + "</b></span>" +
            "<span>block <b>" + fmt(s.live.block) + "</b></span>" +
            "<span><b>" + (s.live.symbol || "—") + "</b></span>"
          : "<span>waiting for the token address</span>");
      $("epochProgress").style.width = "0%";
      return;
    }
    var duv = "";
    if (s.unit_values.length > 1) {
      var prev = s.unit_values[s.unit_values.length - 2];
      var pct = (s.unit_value / prev - 1) * 100;
      duv = ' <span class="' + (pct >= 0 ? "" : "") + '" style="color:' +
        (pct >= 0 ? "var(--good)" : "var(--bad)") + '">' +
        (pct >= 0 ? "+" : "") + pct.toFixed(2) + "%</span>";
    }
    $("topStats").innerHTML =
      '<span class="mode-tag sim">SIM</span>' +
      "<span>epoch <b>" + s.epoch + "</b> · " + simDay(s.t) + "</span>" +
      '<span class="phase">phase <b>' + s.phase + "</b>" +
      (s.phase === 1 ? " · shadow" : s.phase === 0 ? " · passive" : "") + "</span>" +
      "<span>NAV <b>" + fmt(s.nav) + "</b> USDG</span>" +
      "<span>unit <b>" + s.unit_value.toFixed(4) + "</b>" + duv + "</span>" +
      "<span>runway <b>" + s.treasury.runway_days + "</b> days</span>";
    $("epochProgress").style.width = (s.epoch_progress * 100).toFixed(1) + "%";
    $("btnPause").textContent = s.paused ? "▶" : "⏸";
    var sel = $("selSpeed");
    if (sel && s.speed) {
      var sec = String(Math.round(86400 / s.speed));
      if (sel.value !== sec && document.activeElement !== sel) sel.value = sec;
    }
  }

  function renderAlerts(s) {
    if (s.mode === "live" || s.public) { $("alerts").innerHTML = ""; return; }
    var html = "";
    if (s.guard.frozen) {
      html += '<div class="alert alert-bad">BREAKER: drawdown exceeded −25% over 7 epochs — agent frozen since epoch ' +
        s.guard.freeze_epoch + ", basket moved to USDG. Unlock requires a vote." +
        ' <button onclick="NC.gov(\'unfreeze\')">vote to unfreeze</button></div>';
    }
    if (s.treasury.hold_mode) {
      html += '<div class="alert alert-warn">Runway under 14 days: hold mode — one rebalance every three days.</div>';
    }
    $("alerts").innerHTML = html;
  }

  function renderBasket(s) {
    var entries = Object.entries(s.weights).sort(function (a, b) {
      if (a[0] === "USDG") return 1;
      if (b[0] === "USDG") return -1;
      return b[1] - a[1];
    });
    var maxW = Math.max.apply(null, entries.map(function (e) { return e[1]; }).concat([1]));
    $("basket").innerHTML = entries.map(function (e) {
      var a = e[0], w = e[1];
      var val = s.nav * w / 10000;
      return '<div class="b-row"><span class="b-tkr">' + a + "</span>" +
        '<div class="b-bar"><div class="b-fill' + (a === "USDG" ? " cash" : "") +
        '" style="width:' + (w / maxW * 100).toFixed(1) + '%"></div></div>' +
        '<span class="b-w">' + (w / 100).toFixed(1) + "% · " + fmt(val) + "</span>" +
        '<span class="b-p">' + fmt(s.prices[a], 2) + "</span></div>";
    }).join("");
    $("basketFoot").textContent =
      "tax queued for the batch buy: " + fmt(s.pending_quote, 2) +
      " USDG · epoch volume: " + fmt(s.volume_epoch) + " USDG";
  }

  function renderChart(s) {
    drawChart(s.unit_values, s.shadow_uv);
  }

  function drawChart(seriesA, seriesB) {
    var cv = $("chart");
    var dpr = Math.min(2, window.devicePixelRatio || 1);
    var W = cv.clientWidth || 400, H = 220;
    cv.width = W * dpr; cv.height = H * dpr;
    var ctx = cv.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, W, H);

    var a = seriesA || [], b = seriesB || [];
    var n = Math.max(a.length, b.length);
    if (n < 2) return;
    var all = a.concat(b);
    var lo = Math.min.apply(null, all), hi = Math.max.apply(null, all);
    if (hi - lo < 1e-9) { hi = lo + 1e-9; }
    var pad = (hi - lo) * 0.1;
    lo -= pad; hi += pad;

    var x = function (i, len) { return 6 + (W - 12) * i / (len - 1); };
    var y = function (v) { return H - 8 - (H - 16) * (v - lo) / (hi - lo); };

    ctx.strokeStyle = "rgba(171,224,255,.08)";
    ctx.lineWidth = 1;
    for (var gy = 0; gy <= 4; gy++) {
      ctx.beginPath();
      ctx.moveTo(0, 8 + (H - 16) * gy / 4);
      ctx.lineTo(W, 8 + (H - 16) * gy / 4);
      ctx.stroke();
    }
    // базовая линия 1.0
    if (lo < 1 && 1 < hi) {
      ctx.strokeStyle = "rgba(171,224,255,.2)";
      ctx.setLineDash([4, 5]);
      ctx.beginPath(); ctx.moveTo(0, y(1)); ctx.lineTo(W, y(1)); ctx.stroke();
      ctx.setLineDash([]);
    }
    function line(arr, color, width, dash) {
      if (arr.length < 2) return;
      ctx.strokeStyle = color; ctx.lineWidth = width;
      ctx.setLineDash(dash || []);
      ctx.beginPath();
      for (var i = 0; i < arr.length; i++) {
        var px = x(i, arr.length), py = y(arr[i]);
        if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
      }
      ctx.stroke(); ctx.setLineDash([]);
    }
    line(b, "rgba(77,163,255,.55)", 1.6, [5, 4]);
    line(a, "#abe0ff", 2.2);
  }

  var openEpochs = {};

  function trackDetails(r, submitted) {
    var out = '<div class="t-details">';
    if (submitted && submitted.checks && submitted.checks.length) {
      out += "<h4>MandateGuard · vector check at submission</h4>";
      out += submitted.checks.map(function (c) {
        return '<div class="g-row ' + (c.ok ? "g-ok" : "g-bad") + '">' +
          '<span class="g-dot"></span><span class="g-name">' + esc(c.name) + "</span>" +
          '<span class="g-detail">' + esc(c.detail) + "</span></div>";
      }).join("");
      out += '<div class="t-meta">turnover ' + (submitted.turnover_bps / 100).toFixed(1) + "% NAV</div>";
    }
    if (submitted && submitted.exec && submitted.exec.trades && submitted.exec.trades.length) {
      out += "<h4>Executor · batch (" + submitted.exec.max_impact_bps + " bps max impact, cost " +
        fmt(submitted.exec.cost, 2) + " USDG)</h4>";
      out += submitted.exec.trades.map(function (t) {
        return '<div class="t-trade"><span>' + t.asset + "</span><b>" +
          (t.value >= 0 ? "+" : "") + fmt(t.value, 0) + " USDG · " + t.impact_bps + " bps</b></div>";
      }).join("");
    } else if (submitted && !submitted.cancelled && submitted.phase < 2) {
      out += '<div class="t-meta">shadow phase — no execution</div>';
    }
    return out + "</div>";
  }

  function renderTrack(s) {
    var dnav = {};
    s.epochs.forEach(function (e) { dnav[e.n] = e; });
    var items = s.track.slice().reverse().slice(0, 8);
    $("track").innerHTML = items.map(function (r) {
      var badge = !r.revealed
        ? '<span class="t-badge t-sealed">thesis sealed</span>'
        : r.verified
          ? '<span class="t-badge t-ok">keccak verified</span>'
          : '<span class="t-badge t-fail">mismatch — failed</span>';
      var e = dnav[r.epoch];
      var d = e ? '<span class="t-dnav" style="color:' +
        (e.dnav_pct >= 0 ? "var(--good)" : "var(--bad)") + '">' +
        (e.dnav_pct >= 0 ? "+" : "") + e.dnav_pct.toFixed(2) + "%</span>" : "";
      // the vector for epoch N is submitted at the close of N−1 — cancellation lives there
      var submitted = dnav[r.epoch - 1];
      var cancelled = submitted && submitted.cancelled
        ? '<div class="t-meta" style="color:var(--warn)">epoch cancelled: ' + esc(submitted.cancelled) + "</div>" : "";
      var open = !!openEpochs[r.epoch];
      return '<div class="t-item" data-ep="' + r.epoch + '"><div class="t-head">' +
        '<span class="t-ep">E-' + r.epoch + "</span>" +
        '<span class="t-hash">' + r.hash.slice(0, 22) + "…" + r.hash.slice(-8) + "</span>" +
        '<span class="t-open-hint mono">' + (open ? "▾" : "▸") + "</span>" +
        badge + d + "</div>" +
        (r.thesis ? '<div class="t-thesis">' + esc(r.thesis) + "</div>" : "") +
        '<div class="t-meta">commit ' + simDay(r.committed_at) +
        (r.revealed_at ? " → reveal " + simDay(r.revealed_at) : " · trade → reveal next epoch") +
        "</div>" + cancelled +
        (open ? trackDetails(r, submitted) : "") +
        "</div>";
    }).join("") || '<p class="foot">the agent has not submitted a vector yet (phase 0)</p>';
  }

  document.getElementById("track").addEventListener("click", function (e) {
    var item = e.target.closest(".t-item");
    if (!item) return;
    var ep = item.getAttribute("data-ep");
    openEpochs[ep] = !openEpochs[ep];
    if (state) renderTrack(state);
  });

  function renderGuard(s) {
    var last = null;
    for (var i = s.epochs.length - 1; i >= 0; i--) {
      if (s.epochs[i].checks && s.epochs[i].checks.length) { last = s.epochs[i]; break; }
    }
    var lim = s.guard.limits;
    var head = '<p class="g-lim">phase ' + s.phase + " limits: weight ≤ " +
      lim.max_weight_bps / 100 + "% · turnover ≤ " + lim.turnover_bps / 100 + "% NAV</p>";
    if (!last) { $("guard").innerHTML = head + '<p class="foot">no checks yet</p>'; return; }
    $("guard").innerHTML = head + last.checks.map(function (c) {
      return '<div class="g-row ' + (c.ok ? "g-ok" : "g-bad") + '">' +
        '<span class="g-dot"></span><span class="g-name">' + esc(c.name) + "</span>" +
        '<span class="g-detail">' + esc(c.detail) + "</span></div>";
    }).join("") +
      (last.cancelled ? '<p class="g-cancel">Epoch ' + (last.n + 1) + " cancelled: " + esc(last.cancelled) + "</p>"
        : '<p class="foot">vector for epoch ' + (last.n + 1) + " accepted" +
          (last.executed ? " and executed in one batch" : s.phase < 2 ? " (shadow, no execution)" : "") + "</p>");
  }

  function renderHolders(s) {
    var rows = s.holders.slice().sort(function (a, b) { return b.balance - a.balance; });
    var maxShare = Math.max.apply(null, rows.map(function (h) { return h.last_share; }).concat([0.0001]));
    $("holders").innerHTML = '<table class="h"><tr>' +
      "<th>wallet</th><th class='r'>$NSTRO</th><th>epoch share</th><th class='r'>accrued</th><th class='r'>claimed</th></tr>" +
      rows.map(function (h) {
        var tag = h.kind === "user" ? '<span class="tag tag-you">you</span>'
          : h.kind === "sniper" ? '<span class="tag tag-bot">bot</span>' : "";
        var barW = Math.max(2, h.last_share / maxShare * 90);
        return "<tr class='" + (h.kind === "user" ? "you" : h.kind === "sniper" ? "sniper" : "") + "'>" +
          "<td>" + esc(h.name) + tag + "</td>" +
          "<td class='r'>" + fmt(h.balance) + "</td>" +
          "<td><span class='share-bar' style='width:" + barW + "px'></span> " +
          "<span class='mono' style='font-size:11px'>" + (h.last_share * 100).toFixed(2) + "%</span></td>" +
          "<td class='r'>" + fmt(h.claimable_value, 2) + "</td>" +
          "<td class='r'>" + fmt(h.claimed_value, 2) + "</td></tr>";
      }).join("") + "</table>" +
      '<p class="foot">The sniper bot buys 800k $NSTRO twelve seconds before every close — its share tends to zero: weight is balance × time.</p>';
  }

  function renderWallet(s) {
    var you = s.holders.find(function (h) { return h.id === "you"; });
    if (!you) return;
    $("wallet").innerHTML = '<div class="w-stats">' +
      "<div><b>" + fmt(you.balance) + "</b><span>$NSTRO</span></div>" +
      "<div><b>" + fmt(you.claimable_value, 2) + "</b><span>accrued · USDG</span></div>" +
      "<div><b>" + fmt(you.claimed_value, 2) + "</b><span>claimed · USDG</span></div></div>";
    var claimBtn = $("btnClaim");
    if (claimBtn) claimBtn.disabled = !(you.claimable_value > 0);
  }

  function renderTreasury(s) {
    var t = s.treasury;
    $("treasury").innerHTML =
      '<div class="tr-run"><b>' + fmt(t.runway_days, 1) + "</b><span>days of runway" +
      (t.hold_mode ? ' <span class="badge-hold">hold mode</span>' : "") + "</span></div>" +
      '<div class="kv"><span>USDG balance</span><b>' + fmt(t.usdg, 2) + "</b></div>" +
      '<div class="kv"><span>Cost per epoch (inference + gas)</span><b>' + fmt(t.epoch_cost, 0) + "</b></div>" +
      '<div class="kv"><span>Inflow: 13% of the tax</span><b>' + fmt(t.inflow_tax, 2) + "</b></div>" +
      '<div class="kv"><span>Inflow: 1% creator fees</span><b>' + fmt(t.inflow_creator, 2) + "</b></div>" +
      '<div class="kv"><span>Protocol fund (7%)</span><b>' + fmt(t.protocol_fund, 2) + "</b></div>";
  }

  function renderGov(s) {
    var steps = [0, 1, 2, 3].map(function (p) {
      var cls = p === s.phase ? "on" : p < s.phase ? "done" : "";
      var names = ["passive", "shadow", "reduced", "full"];
      return '<span class="ph ' + cls + '">P' + p + " · " + names[p] + "</span>";
    }).join("");
    var queue = s.gov_queue.length
      ? s.gov_queue.map(function (g) {
          return '<div class="gq">' + esc(g.label) + " — <b>timelock until epoch " + g.eta + "</b></div>";
        }).join("")
      : '<div class="gq">queue is empty</div>';
    var btns = "";
    if (s.phase === 2 && !s.gov_queue.some(function (g) { return g.action === "phase3"; })) {
      btns += '<button class="act" onclick="NC.gov(\'phase3\')">vote: phase 3</button>';
    }
    if (s.guard.frozen && !s.gov_queue.some(function (g) { return g.action === "unfreeze"; })) {
      btns += '<button class="act" onclick="NC.gov(\'unfreeze\')">vote: unfreeze</button>';
    }
    $("gov").innerHTML = '<div class="ph-steps">' + steps + "</div>" + queue +
      (btns ? '<div class="gov-btns">' + btns + "</div>" : "") +
      '<p class="foot">Every change is a holder vote plus a 3-day timelock (3 epochs). Three days for dissenters to exit.</p>';
  }

  function renderLog(s) {
    $("log").innerHTML = s.log.slice().reverse().map(function (l) {
      return "<div><b>" + simDay(l.t) + "</b> " + esc(l.msg) + "</div>";
    }).join("");
  }

  /* ---------- controls ---------- */
  $("btnPause").addEventListener("click", function () {
    post("/api/control", { action: state && state.paused ? "resume" : "pause" });
  });
  $("btnAdvance").addEventListener("click", function () {
    post("/api/control", { action: "advance" });
  });
  $("selSpeed").addEventListener("change", function () {
    post("/api/control", { action: "speed", value: parseFloat(this.value) });
  });
  document.querySelectorAll("[data-trade]").forEach(function (b) {
    b.addEventListener("click", function () {
      var amtEl = $("tradeAmt");
      var amount = amtEl ? parseFloat(amtEl.value) : 100000;
      if (!isFinite(amount) || amount <= 0) return;
      post("/api/trade", { side: b.getAttribute("data-trade"), amount: amount });
    });
  });
  $("btnClaim").addEventListener("click", function () { post("/api/claim"); });

  window.NC = { gov: function (a) { post("/api/gov", { action: a }); } };

  /* ---------- real wallet (EIP-1193, Robinhood Chain 4663) ---------- */
  var CHAIN_HEX = "0x1237"; // 4663
  var SEL = { balanceOf: "0x70a08231", previewUnits: "0x0d85a3ad", claim: "0x4e71d92d",
              buy: "0x59a87bc1", sell: "0xd04c6983", approve: "0x095ea7b3",
              allowance: "0xdd62ed3e", processWeth: "0x4e193f50", burnToken: "0x950dad19" };
  var FEE_VAULT = "0xB2FC6481A65BACc91277a3488dcc7f6b1C210813";
  var EXPLORER = "https://robinhoodchain.blockscout.com/tx/";
  var W3 = { account: null, busy: false };

  function toWeiHex(v) {
    // строку в 18-decimals wei без float-погрешности
    var s = String(v).trim();
    var neg = s[0] === "-";
    if (neg) return "0x0";
    var parts = s.split(".");
    var whole = parts[0] || "0";
    var frac = (parts[1] || "").slice(0, 18);
    while (frac.length < 18) frac += "0";
    var big = BigInt(whole) * 1000000000000000000n + BigInt(frac || "0");
    return "0x" + big.toString(16);
  }
  function num32(hex) { return hex.replace(/^0x/, "").padStart(64, "0"); }

  function ethReq(method, params) {
    return window.ethereum.request({ method: method, params: params || [] });
  }
  function padAddr(a) { return a.slice(2).toLowerCase().padStart(64, "0"); }

  function ensureChain() {
    return ethReq("wallet_switchEthereumChain", [{ chainId: CHAIN_HEX }])
      .catch(function (e) {
        if (e && (e.code === 4902 || (e.data && e.data.originalError && e.data.originalError.code === 4902))) {
          return ethReq("wallet_addEthereumChain", [{
            chainId: CHAIN_HEX,
            chainName: "Robinhood Chain",
            nativeCurrency: { name: "Ether", symbol: "ETH", decimals: 18 },
            rpcUrls: [state && state.config && state.config.rpc_url ? state.config.rpc_url : ""],
          }]);
        }
        throw e;
      });
  }

  function connectWallet() {
    if (!window.ethereum) {
      alert("No wallet extension found. Install MetaMask / Rabby and reload.");
      return;
    }
    // wallet_requestPermissions форсит пикер аккаунтов при каждом клике;
    // не все кошельки его умеют — тогда обычный requestAccounts
    ethReq("wallet_requestPermissions", [{ eth_accounts: {} }])
      .catch(function () { return null; })
      .then(function () { return ethReq("eth_requestAccounts"); })
      .then(function (accs) {
        W3.account = accs && accs[0];
        if (state && state.mode === "live") return ensureChain();
      })
      .then(function () { renderWalletUI(); refreshOnWallet(); })
      .catch(function () { renderWalletUI(); });
  }

  function renderWalletUI() {
    var b = $("btnWallet");
    if (!b) return;
    var noSim = state && (state.mode === "live" || state.public);
    b.hidden = !noSim;
    b.textContent = W3.account
      ? W3.account.slice(0, 6) + "…" + W3.account.slice(-4)
      : "CONNECT WALLET";
    var ac = $("cardActions");
    if (ac) ac.hidden = !(state && state.mode === "live" && W3.account);
  }

  function actStatus(cls, html) {
    var el = $("actStatus");
    if (el) { el.className = "mono act-status " + (cls || ""); el.innerHTML = html; }
  }
  function txLink(hash) {
    return '<a target="_blank" rel="noopener" href="' + EXPLORER + hash + '">' +
      hash.slice(0, 14) + "… ↗</a>";
  }

  function sendTx(tx, label) {
    if (!W3.account) { actStatus("err", "connect a wallet first"); return; }
    actStatus("", label + " — confirm in your wallet…");
    ensureChain()
      .then(function () {
        tx.from = W3.account;
        return ethReq("eth_sendTransaction", [tx]);
      })
      .then(function (hash) {
        actStatus("ok", label + " sent: " + txLink(hash));
        setTimeout(refreshOnWallet, 4000);
      })
      .catch(function (e) {
        actStatus("err", label + " failed: " + ((e && e.message) || "rejected"));
      });
  }

  function curveAddr() {
    return state && state.live && state.live.pons && state.live.pons.curve;
  }

  function doBuy() {
    var curve = curveAddr();
    if (!curve) { actStatus("err", "no curve — token may have graduated"); return; }
    var eth = $("buyEth").value;
    var wei = toWeiHex(eth);
    // buy(quoteIn, minTokensOut=0, recipient=you)
    var data = SEL.buy + num32(wei) + num32("0x0") + num32(W3.account);
    sendTx({ to: curve, value: wei, data: data }, "buy " + eth + " ETH");
  }
  function doSell() {
    var curve = curveAddr();
    if (!curve) { actStatus("err", "no curve — token may have graduated"); return; }
    var token = state.live.vault;
    var amt = toWeiHex($("sellTok").value);
    // сначала approve кривой, потом sell
    actStatus("", "approve curve → sell (two signatures)…");
    ensureChain().then(function () {
      return ethReq("eth_sendTransaction", [{
        from: W3.account, to: token,
        data: SEL.approve + num32(curve) + num32(amt) }]);
    }).then(function () {
      var data = SEL.sell + num32(amt) + num32("0x0") + num32(W3.account);
      return ethReq("eth_sendTransaction", [{ from: W3.account, to: curve, data: data }]);
    }).then(function (hash) {
      actStatus("ok", "sell sent: " + txLink(hash));
      setTimeout(refreshOnWallet, 4000);
    }).catch(function (e) {
      actStatus("err", "sell failed: " + ((e && e.message) || "rejected"));
    });
  }
  function doFeed() {
    var eth = $("feedEth").value;
    sendTx({ to: FEE_VAULT, value: toWeiHex(eth) }, "feed " + eth + " ETH to vault");
  }
  function doProcessWeth() {
    sendTx({ to: FEE_VAULT, data: SEL.processWeth }, "processWETH");
  }
  function doBurn() {
    var t = prompt("Token address to burn from the vault (0x…):");
    if (!t || !/^0x[0-9a-fA-F]{40}$/.test(t)) { actStatus("err", "bad address"); return; }
    sendTx({ to: FEE_VAULT, data: SEL.burnToken + num32(t) }, "burn token");
  }

  function refreshClaims() {
    if (!W3.account) return;
    fetch("/api/claims?address=" + W3.account.toLowerCase())
      .then(function (r) { return r.json(); })
      .then(function (c) { W3.claims = c; renderClaimBox(); })
      .catch(function () {});
  }

  function renderClaimBox() {
    var el = $("claimBox");
    if (!el) return;
    var c = W3.claims;
    if (!c || !c.rounds || !c.rounds.length) {
      el.innerHTML = '<p class="foot">Nothing distributed to this wallet yet. ' +
        'Rewards accrue as balance × time and are published on-chain each epoch.</p>';
      return;
    }
    var open = c.rounds.filter(function (r) { return !r.claimed; });
    var wei = open.reduce(function (a, r) { return a + BigInt(r.amount); }, 0n);
    var eth = Number(wei) / 1e18;
    el.innerHTML =
      '<div class="w-stats"><div><b>' + fmt(eth, 8) + "</b><span>claimable ETH</span></div>" +
      "<div><b>" + open.length + "</b><span>open epochs</span></div>" +
      "<div><b>" + (c.rounds.length - open.length) + "</b><span>already claimed</span></div></div>" +
      '<div class="wallet-btns"><button class="act act-ice" id="btnClaimReal"' +
      (open.length ? "" : " disabled") + ">claim " + fmt(eth, 6) + " ETH</button></div>" +
      '<p class="foot">Each epoch\'s payout is fixed on-chain by a Merkle root — ' +
      "the amount is proven, not trusted.</p>";
    var b = $("btnClaimReal");
    if (b) b.addEventListener("click", claimReal);
  }

  function claimReal() {
    var c = W3.claims;
    if (!c || !c.distributor) return;
    var open = (c.rounds || []).filter(function (r) { return !r.claimed; });
    if (!open.length) return;
    var data;
    if (open.length === 1) {
      var r = open[0];
      // claim(uint256,uint256,bytes32[])
      data = "0x" + "ae0b51df" + num32(BigInt(r.epoch).toString(16)) +
        num32(BigInt(r.amount).toString(16)) + num32((96).toString(16)) +
        num32(r.proof.length.toString(16)) +
        r.proof.map(function (p) { return num32(p); }).join("");
      // офсет массива = 3 слова (epoch, amount, offset) → 0x60
    } else {
      actStatus("", "claiming " + open.length + " epochs, one signature per epoch…");
    }
    if (open.length > 1) {
      // последовательные claim'ы — проще и дешевле в отладке, чем claimMany
      var i = 0;
      var next = function () {
        if (i >= open.length) { refreshClaims(); return; }
        var rr = open[i++];
        var d = "0x" + "ae0b51df" + num32(BigInt(rr.epoch).toString(16)) +
          num32(BigInt(rr.amount).toString(16)) + num32((96).toString(16)) +
          num32(rr.proof.length.toString(16)) +
          rr.proof.map(function (p) { return num32(p); }).join("");
        ethReq("eth_sendTransaction", [{ from: W3.account, to: c.distributor, data: d }])
          .then(function (h) {
            actStatus("ok", "claim epoch " + rr.epoch + ": " + txLink(h));
            setTimeout(next, 2500);
          })
          .catch(function (e) {
            actStatus("err", "claim failed: " + ((e && e.message) || "rejected"));
          });
      };
      ensureChain().then(next);
      return;
    }
    sendTx({ to: c.distributor, data: data }, "claim epoch " + open[0].epoch);
    setTimeout(refreshClaims, 6000);
  }

  function refreshOnWallet() {
    var card = $("cardOnWallet"), box = $("onWallet");
    if (!card || !box) return;
    var live = state && state.mode === "live" && state.live && state.live.ok;
    card.hidden = !(live && W3.account);
    if (card.hidden || W3.busy || !window.ethereum) return;
    W3.busy = true;
    refreshClaims();
    var L = state.live, token = L.vault, acc = W3.account;
    var dec = L.decimals || 18;
    var out = {};
    ethReq("eth_getBalance", [acc, "latest"]).then(function (weiHex) {
      out.eth = parseInt(weiHex, 16) / 1e18;
      return ethReq("eth_call", [{ to: token, data: SEL.balanceOf + padAddr(acc) }, "latest"])
        .catch(function () { return null; });
    }).then(function (bal) {
      out.tokens = bal && bal !== "0x" ? parseInt(bal, 16) / Math.pow(10, dec) : null;
      if (L.kind === "vault") {
        return ethReq("eth_call", [{ to: token, data: SEL.previewUnits + padAddr(acc) }, "latest"])
          .catch(function () { return null; });
      }
      return null;
    }).then(function (units) {
      out.units = units && units !== "0x" ? parseInt(units, 16) / 1e18 : null;
      var html =
        '<div class="w-stats">' +
        "<div><b>" + fmt(out.eth, 4) + "</b><span>ETH</span></div>" +
        (out.tokens != null
          ? "<div><b>" + fmt(out.tokens) + "</b><span>" + esc(L.symbol || "tokens") + "</span></div>" : "") +
        (out.units != null
          ? "<div><b>" + fmt(out.units, 4) + "</b><span>accrued units</span></div>" : "") +
        "</div>";
      html += '<div id="claimBox"></div>';
      box.innerHTML = html;
      renderClaimBox();
      W3.busy = false;
    }).catch(function () { W3.busy = false; });
  }

  function claimReal() {
    if (!W3.account || !state || !state.live) return;
    ensureChain().then(function () {
      return ethReq("eth_sendTransaction",
        [{ from: W3.account, to: state.live.vault, data: SEL.claim }]);
    }).then(function () { setTimeout(refreshOnWallet, 4000); })
      .catch(function () {});
  }

  (function initWallet() {
    var b = $("btnWallet");
    if (b) b.addEventListener("click", connectWallet);
    var wire = { btnBuy: doBuy, btnSell: doSell, btnFeed: doFeed,
                 btnProcessWeth: doProcessWeth, btnBurn: doBurn };
    Object.keys(wire).forEach(function (id) {
      var el = $(id);
      if (el) el.addEventListener("click", wire[id]);
    });
    if (window.ethereum && window.ethereum.on) {
      window.ethereum.on("accountsChanged", function (a) {
        W3.account = a && a[0] ? a[0] : null;
        renderWalletUI(); refreshOnWallet();
      });
      window.ethereum.on("chainChanged", function () { refreshOnWallet(); });
    }
    setInterval(function () {
      if (W3.account && state && state.mode === "live") refreshOnWallet();
    }, 8000);
  })();

  /* ---------- poll ---------- */
  var reqSeq = 0;
  function refresh() {
    var id = ++reqSeq;
    fetch("/api/state").then(function (r) { return r.json(); })
      .then(function (s) { if (id === reqSeq) render(s); })
      .catch(function () {});
  }
  refresh();
  setInterval(refresh, 1200);
  window.addEventListener("resize", function () { if (state) render(state); });
})();
