/* Haazir frontend: hash-routed single page, no build step. */
(function () {
  "use strict";
  const API = (window.HAAZIR_API || "").replace(/\/$/, "");
  const $app = document.getElementById("app");
  const AREAS = {
    "Gulberg": [31.5204, 74.3487], "Johar Town": [31.4697, 74.2728], "DHA": [31.4720, 74.4060],
    "Model Town": [31.4834, 74.3256], "Iqbal Town": [31.5050, 74.2900], "Garden Town": [31.5000, 74.3220],
    "Shadman": [31.5390, 74.3300], "Anarkali": [31.5690, 74.3100], "Township": [31.4500, 74.3100],
    "Wapda Town": [31.4350, 74.2650], "Faisal Town": [31.4790, 74.3040], "Samanabad": [31.5340, 74.2980],
    "Cantt": [31.5100, 74.3900], "Shahdara": [31.6280, 74.2950], "Bahria Town": [31.3690, 74.1830]
  };
  const DEPTS = ["Emergency", "Medicine", "Surgery", "Cardiology", "Paediatrics", "Gynae/Obstetrics", "Orthopaedics", "ICU", "Burns"];
  const DEPT_UR = { "Emergency": "ایمرجنسی", "Medicine": "میڈیسن", "Surgery": "سرجری", "Cardiology": "دل (کارڈیالوجی)", "Paediatrics": "بچے", "Gynae/Obstetrics": "زچگی / گائنی", "Orthopaedics": "ہڈی (آرتھو)", "ICU": "آئی سی یو", "Burns": "جلنا (برنز)" };
  const EQUIP = ["CT", "MRI", "XRay", "Dialysis", "Ventilator", "Oxygen"];
  const GROUPS = ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"];

  function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } }
  const state = { lang: store("lang") || "en", loc: null, staff: null };
  try { const l = JSON.parse(store("loc") || "null"); if (l && l.lat) state.loc = l; } catch (e) {}
  if (!state.loc) state.loc = { lat: 31.5204, lon: 74.3487, label: "Gulberg" };

  const L_ = (en, ur) => (state.lang === "ur" && ur ? ur : en);
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const dept = (d) => (state.lang === "ur" ? (DEPT_UR[d] || d) : d);
  const nowS = () => Math.floor(Date.now() / 1000);
  function ago(ts) {
    if (!ts) return "";
    const m = Math.max(0, Math.round((nowS() - ts) / 60));
    if (m < 1) return L_("just now", "ابھی");
    if (m < 60) return L_(`${m} min ago`, `${m} منٹ پہلے`);
    return L_(`${Math.round(m / 60)} h ago`, `${Math.round(m / 60)} گھنٹے پہلے`);
  }
  const staleNote = (ts) => (ts && nowS() - ts > 7200 ? ` <span class="stale-note">${L_("may be outdated", "پرانی معلومات ہو سکتی ہے")}</span>` : "");
  const dirUrl = (lat, lon) => `https://www.google.com/maps/dir/?api=1&destination=${lat},${lon}`;
  const locQ = () => `lat=${state.loc.lat}&lon=${state.loc.lon}`;

  async function api(path, opts) {
    const ctl = new AbortController();
    const timer = setTimeout(() => ctl.abort(), 28000);
    try {
      const r = await fetch(API + path, Object.assign({ signal: ctl.signal, headers: { "content-type": "application/json" } }, opts || {}));
      const data = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(data.error || `Request failed (${r.status})`);
      return data;
    } catch (e) {
      if (e.name === "AbortError") throw new Error(L_("The server took too long. Please try again.", "سرور نے دیر کر دی، دوبارہ کوشش کریں۔"));
      if (e instanceof TypeError) throw new Error(L_("Can't reach Haazir. Check your internet connection.", "انٹرنیٹ کنکشن چیک کریں۔"));
      throw e;
    } finally { clearTimeout(timer); }
  }
  const post = (p, body) => api(p, { method: "POST", body: JSON.stringify(body) });

  // ------------------------------------------------------------ lifecycle (maps, timers)
  let maps = [], timers = [];
  function cleanup() { maps.forEach((m) => { try { m.remove(); } catch (e) {} }); maps = []; timers.forEach(clearInterval); timers = []; }
  function every(fn, ms) { timers.push(setInterval(fn, ms)); }
  function makeMap(el, center, zoom) {
    if (!window.L) { el.innerHTML = `<div class="empty">${L_("Map unavailable", "نقشہ دستیاب نہیں")}</div>`; return null; }
    const m = window.L.map(el, { scrollWheelZoom: false }).setView(center, zoom || 12);
    window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 18, attribution: "© OpenStreetMap" }).addTo(m);
    maps.push(m);
    return m;
  }
  const dotIcon = (emoji) => window.L.divIcon({ className: "", html: `<div style="font-size:24px;line-height:24px">${emoji}</div>`, iconSize: [24, 24], iconAnchor: [12, 12] });
  function youMarker(m) { if (m) window.L.circleMarker([state.loc.lat, state.loc.lon], { radius: 8, color: "#fff", weight: 3, fillColor: "#1e66f5", fillOpacity: 1 }).addTo(m).bindPopup(L_("You", "آپ")); }

  const skeleton = (n) => Array.from({ length: n || 3 }, () => '<div class="skel"></div>').join("");
  const errBox = (e) => `<div class="err">${esc(e.message || e)}</div>`;

  // ------------------------------------------------------------ chrome
  function chrome() {
    document.documentElement.lang = state.lang === "ur" ? "ur" : "en";
    document.documentElement.dir = state.lang === "ur" ? "rtl" : "ltr";
    document.getElementById("pilot").textContent = L_("⚠️ Pilot demo: availability data is simulated, not live.", "⚠️ پائلٹ ڈیمو: دستیابی کا ڈیٹا فرضی ہے، اصل نہیں۔");
    const r = location.hash.split("?")[0];
    const link = (h, en, ur, cls) => `<a href="${h}" class="${cls || ""} ${r === h ? "on" : ""}">${L_(en, ur)}</a>`;
    document.getElementById("nav").innerHTML =
      link("#/hospitals", "Hospitals", "ہسپتال", "hide-m") + link("#/medicine", "Medicine", "دوا", "hide-m") +
      link("#/blood", "Blood", "خون", "hide-m") + link("#/dashboard", "Dashboard", "ڈیش بورڈ", "hide-m") +
      link("#/staff", "Staff", "اسٹاف") +
      `<button class="lang" id="langBtn">${state.lang === "ur" ? "English" : "اردو"}</button>`;
    document.getElementById("langBtn").onclick = () => { state.lang = state.lang === "ur" ? "en" : "ur"; store("lang", state.lang); route(); };
    document.getElementById("foot").innerHTML = `<b>Haazir حاضر</b> · ${L_("Pilot demo for Lahore. All availability data is simulated and is not connected to any real hospital, pharmacy, blood bank or Rescue 1122. In an emergency call", "لاہور کے لیے پائلٹ ڈیمو۔ تمام ڈیٹا فرضی ہے۔ ایمرجنسی میں کال کریں")} <a href="tel:1122">1122</a>. ${L_("Haazir routes you to care. It does not diagnose.", "حاضر تشخیص نہیں کرتا، صرف راستہ دکھاتا ہے۔")} · Built on AWS.`;
  }

  // ------------------------------------------------------------ shared blocks
  function locationRow(light) {
    const opts = Object.keys(AREAS).map((a) => `<option ${state.loc.label === a ? "selected" : ""}>${a}</option>`).join("");
    return `<div class="locrow" ${light ? 'style="color:var(--muted)"' : ""}>📍 <span id="locLabel">${esc(state.loc.label || L_("My location", "میری لوکیشن"))}</span>
      <button type="button" id="gpsBtn" ${light ? 'class="btn sm"' : ""}>${L_("Use my location", "میری لوکیشن")}</button>
      <select id="areaSel" ${light ? 'class="btn sm"' : ""}><option value="">${L_("or pick area", "یا علاقہ چنیں")}</option>${opts}</select></div>`;
  }
  function bindLocation(onChange) {
    const gps = document.getElementById("gpsBtn"), sel = document.getElementById("areaSel");
    if (gps) gps.onclick = () => {
      if (!navigator.geolocation) return alert(L_("Location not available on this device", "لوکیشن دستیاب نہیں"));
      gps.textContent = "…";
      navigator.geolocation.getCurrentPosition((p) => {
        let { latitude: lat, longitude: lon } = p.coords;
        let label = L_("My location", "میری لوکیشن");
        if (!(lat > 31.2 && lat < 31.8 && lon > 74.0 && lon < 74.6)) { lat = 31.5204; lon = 74.3487; label = "Gulberg (outside Lahore pilot area)"; }
        setLoc({ lat, lon, label }); onChange && onChange();
      }, () => { gps.textContent = L_("Location blocked, pick area", "علاقہ چنیں"); }, { timeout: 8000 });
    };
    if (sel) sel.onchange = () => { const a = AREAS[sel.value]; if (a) { setLoc({ lat: a[0], lon: a[1], label: sel.value }); onChange && onChange(); } };
  }
  function setLoc(l) { state.loc = l; store("loc", JSON.stringify(l)); const el = document.getElementById("locLabel"); if (el) el.textContent = l.label; }

  function redBanner(condition, reason) {
    return `<div class="alert-red">
      <h2>🚨 ${L_("Emergency: call Rescue 1122 now", "ایمرجنسی: ابھی ریسکیو 1122 کو کال کریں")}</h2>
      <div>${esc(reason ? L_("Warning sign: ", "خطرے کی علامت: ") + reason : "")}</div>
      <div class="btns">
        <a class="btn w" href="tel:1122">📞 ${L_("Call Rescue 1122", "ریسکیو 1122 کال کریں")}</a>
        <button class="btn" style="background:transparent;color:#fff" data-amb="${esc(condition || "")}">🚑 ${L_("Request ambulance (demo)", "ایمبولینس منگوائیں (ڈیمو)")}</button>
      </div>
      <div class="small" style="margin-top:8px;opacity:.9">${L_("Haazir is not a diagnosis. The demo ambulance network is simulated, so always call 1122 first.", "یہ تشخیص نہیں۔ ڈیمو ایمبولینس فرضی ہے، پہلے 1122 کال کریں۔")}</div>
    </div>`;
  }

  function bedClass(free, total) { if (free == null) return "x"; if (free === 0) return "r"; if (free <= Math.max(2, total * 0.1)) return "a"; return "g"; }
  const eqPill = (k, e) => { const c = e.status === "working" ? "g" : e.status === "busy" ? "a" : "r"; const lbl = e.status === "working" ? L_("working", "چالو") : e.status === "busy" ? L_("busy", "مصروف") : L_("down", "خراب"); return `<span class="pill ${c} ${e.stale ? "stale" : ""}">${k}: ${lbl}</span>`; };
  const loadPill = (l) => `<span class="pill ${l === "Low" ? "g" : l === "Busy" ? "a" : "r"}">ER ${l === "Low" ? L_("calm", "کم رش") : l === "Busy" ? L_("busy", "مصروف") : L_("full", "بھرا ہوا")}</span>`;

  function hospitalCard(h, i, opts) {
    opts = opts || {};
    const d = h.department;
    const free = d ? h.freeBeds : Object.values(h.beds).reduce((s, b) => s + b.free, 0);
    const total = d ? (h.beds[d] || {}).total : Object.values(h.beds).reduce((s, b) => s + b.total, 0);
    const stale = d && h.beds[d] && h.beds[d].stale;
    const keyEq = ["CT", "MRI", "XRay", "Dialysis", "Ventilator"].filter((k) => h.equipment[k]).slice(0, 4);
    const docs = (h.doctorsOnDuty || []).slice(0, 2).map((x) => `${esc(x.name)}${x.gender === "F" ? " ♀" : ""} (${esc(dept(x.dept))}${x.shiftEnds ? ", " + L_("until", "تک") + " " + x.shiftEnds : ""})`).join(" · ");
    return `<div class="card ${i === 0 ? "top1" : ""}">
      ${i === 0 ? `<div class="pill o" style="margin-bottom:8px">★ ${L_("Best match right now", "اس وقت بہترین")}</div>` : ""}
      <div class="row">
        <div class="big ${bedClass(free, total)} ${stale ? "stale" : ""}">${free == null ? "?" : free}<small>${d ? L_("free beds", "خالی بستر") + "<br>" + esc(dept(d)) : L_("free beds", "خالی بستر")}</small></div>
        <div class="grow">
          <h3>${esc(state.lang === "ur" && h.nameUr ? h.nameUr : h.name)}</h3>
          <div class="muted small">${h.distanceKm} km · ~${h.etaMin} ${L_("min by road", "منٹ")} · ${L_("updated", "اپ ڈیٹ")} ${ago(h.updatedAt)}${stale ? staleNote(0) : ""}</div>
          <div class="pills">${loadPill(h.erLoad)}${h.sehatCard ? `<span class="pill o">Sehat Card</span>` : ""}${h.femaleDoctor ? `<span class="pill o">♀ ${L_("Female doctor", "لیڈی ڈاکٹر")}</span>` : ""}${keyEq.map((k) => eqPill(k, h.equipment[k])).join("")}</div>
          <div class="small">🩺 ${docs || L_("No doctor on duty listed", "کوئی ڈاکٹر ڈیوٹی پر نہیں")}</div>
          ${h.why ? `<div class="why">${L_("Why:", "وجہ:")} ${esc(h.why)}</div>` : ""}
        </div>
      </div>
      <div class="btns">
        <a class="btn p" target="_blank" rel="noopener" href="${dirUrl(h.lat, h.lon)}">🧭 ${L_("Directions", "راستہ")}</a>
        <a class="btn" href="tel:${esc(h.phone || "")}">📞 ${L_("Call", "کال")}</a>
        <button class="btn" data-notify="${h.id}" data-dept="${esc(d || "Emergency")}" data-name="${esc(h.name)}" data-eta="${h.etaMin}">🔔 ${L_("Notify hospital", "ہسپتال کو اطلاع دیں")}</button>
        ${opts.redFlag ? `<button class="btn d" data-amb="${esc(opts.condition || "")}" data-dest="${h.id}">🚑 ${L_("Ambulance to here (demo)", "یہاں ایمبولینس (ڈیمو)")}</button>` : ""}
        <a class="btn" href="#/facility/${h.id}">${L_("Details", "تفصیل")} →</a>
      </div>
    </div>`;
  }

  function bindActions(root) {
    root.querySelectorAll("[data-amb]").forEach((b) => b.onclick = () => requestAmbulance(b.dataset.amb, b.dataset.dest, b));
    root.querySelectorAll("[data-notify]").forEach((b) => b.onclick = () => notifyModal(b.dataset));
    root.querySelectorAll("[data-ask]").forEach((b) => b.onclick = () => { location.hash = "#/ask?q=" + encodeURIComponent(b.dataset.ask); });
  }

  async function requestAmbulance(condition, destId, btn) {
    if (btn) { btn.disabled = true; btn.textContent = L_("Requesting…", "درخواست بھیجی جا رہی ہے…"); }
    try {
      const r = await post("/ambulance/request", { lat: state.loc.lat, lon: state.loc.lon, condition: condition || "Emergency", destinationHospitalId: destId || undefined });
      location.hash = "#/ambulance/" + r.requestId;
    } catch (e) { alert(e.message); if (btn) { btn.disabled = false; btn.textContent = "🚑 " + L_("Try again", "دوبارہ"); } }
  }

  function modal(html) {
    const bg = document.createElement("div");
    bg.className = "modal-bg";
    bg.innerHTML = `<div class="modal">${html}</div>`;
    bg.onclick = (e) => { if (e.target === bg) bg.remove(); };
    document.body.appendChild(bg);
    return bg;
  }
  function notifyModal(ds) {
    const m = modal(`<h3>🔔 ${L_("Tell", "اطلاع دیں:")} ${esc(ds.name)}</h3>
      <p class="small muted">${L_("The hospital's staff portal gets an alert so they can prepare. (Pilot demo: alerts go to the demo staff portal only.)", "ہسپتال اسٹاف کو اطلاع ملے گی (ڈیمو)۔")}</p>
      <div class="field"><select id="nDept">${DEPTS.map((d) => `<option ${d === ds.dept ? "selected" : ""} value="${d}">${dept(d)}</option>`).join("")}</select></div>
      <div class="field"><input id="nNote" maxlength="200" placeholder="${L_("What happened? e.g. high fever, 6 year old", "کیا ہوا؟ مثلاً تیز بخار")}"></div>
      <div class="field"><input id="nEta" type="number" min="0" max="600" value="${esc(ds.eta || 20)}"> <span class="muted" style="align-self:center">${L_("minutes away", "منٹ دور")}</span></div>
      <div class="btns"><button class="btn p" id="nSend">${L_("Send alert", "اطلاع بھیجیں")}</button><button class="btn" id="nCancel">${L_("Cancel", "منسوخ")}</button></div><div id="nOut"></div>`);
    m.querySelector("#nCancel").onclick = () => m.remove();
    m.querySelector("#nSend").onclick = async (ev) => {
      ev.target.disabled = true;
      try {
        const r = await post("/notify", { facilityId: ds.notify, department: m.querySelector("#nDept").value, note: m.querySelector("#nNote").value, eta: +m.querySelector("#nEta").value });
        m.querySelector("#nOut").innerHTML = `<div class="note">✅ ${L_("Alert sent. Show this reference at the desk:", "اطلاع بھیج دی گئی۔ ریفرنس کوڈ:")} <b style="font-size:20px">${esc(r.referenceCode)}</b></div>`;
      } catch (e) { m.querySelector("#nOut").innerHTML = errBox(e); ev.target.disabled = false; }
    };
  }

  function speak(text) {
    try { if (!window.speechSynthesis) return; const u = new SpeechSynthesisUtterance(text); u.lang = state.lang === "ur" ? "ur-PK" : "en-US"; speechSynthesis.cancel(); speechSynthesis.speak(u); } catch (e) {}
  }

  // ------------------------------------------------------------ pages
  async function home() {
    const ex = ["abbu ko seenay mein dard", "O negative blood chahiye 2 bottle", "Augmentin kahan milegi Johar Town", "CT scan kahan ho raha hai abhi", "lady doctor gynae", "bachay ko tez bukhar hai"];
    $app.innerHTML = `
    <section class="hero">
      <h1>${L_("Know before you go.", "جانے سے پہلے جانیں۔")}</h1>
      <p>${L_("Which Lahore hospital has a free bed, a doctor on duty, a working CT scanner, your medicine or O-negative blood, right now? Ask in Urdu or English.", "لاہور کے کس ہسپتال میں ابھی بستر، ڈاکٹر، سی ٹی اسکین، دوا یا خون دستیاب ہے؟ اردو یا انگریزی میں پوچھیں۔")}</p>
      <form class="ask" id="askForm"><input id="q" autocomplete="off" maxlength="300" placeholder="${L_("What do you need? e.g. abbu ko seenay mein dard", "آپ کو کیا چاہیے؟")}" aria-label="What do you need"><button type="button" class="mic" id="mic" title="Speak" aria-label="Speak">🎤</button><button class="go">${L_("Find", "تلاش")}</button></form>
      <div class="examples">${ex.map((e) => `<button type="button" data-ex="${esc(e)}">${esc(e)}</button>`).join("")}</div>
      ${locationRow(false)}
    </section>
    <div class="tiles">
      <a class="tile em" href="#/ask?q=${encodeURIComponent("emergency")}"><span class="ic">🚨</span>${L_("Emergency", "ایمرجنسی")}</a>
      <a class="tile" href="#/hospitals"><span class="ic">🛏️</span>${L_("Hospital bed", "ہسپتال بستر")}</a>
      <a class="tile" href="#/ambulance"><span class="ic">🚑</span>${L_("Ambulance", "ایمبولینس")}</a>
      <a class="tile" href="#/medicine"><span class="ic">💊</span>${L_("Medicine", "دوا")}</a>
      <a class="tile" href="#/blood"><span class="ic">🩸</span>${L_("Blood", "خون")}</a>
      <a class="tile" href="#/equipment"><span class="ic">🩻</span>CT / MRI / ${L_("Dialysis", "ڈائیلاسز")}</a>
      <a class="tile" href="#/hospitals?female=1&dept=Gynae/Obstetrics"><span class="ic">👩‍⚕️</span>${L_("Lady doctor", "لیڈی ڈاکٹر")}</a>
      <a class="tile" href="#/dashboard"><span class="ic">🗺️</span>${L_("City dashboard", "شہر ڈیش بورڈ")}</a>
    </div>
    <h2>${L_("Across Lahore right now", "اس وقت لاہور میں")} <span class="pill x">${L_("simulated", "فرضی")}</span></h2>
    <div class="stats" id="liveStats">${'<div class="stat skel" style="height:72px"></div>'.repeat(4)}</div>
    <h2>${L_("How it works", "یہ کیسے کام کرتا ہے")}</h2>
    <div class="steps">
      <div class="card"><h3>1 · ${L_("Ask in your words", "اپنے الفاظ میں پوچھیں")}</h3><div class="small muted">${L_("Type or speak in Urdu, Roman Urdu or English. AI on Amazon Bedrock understands what you need: bed, ambulance, medicine, blood, test or doctor.", "اردو، رومن اردو یا انگریزی میں لکھیں یا بولیں۔")}</div></div>
      <div class="card"><h3>2 · ${L_("See what's available", "دیکھیں کیا دستیاب ہے")}</h3><div class="small muted">${L_("A transparent ranking (free beds, doctor on duty, working machines, ER load, travel time) explains why each option is suggested.", "واضح درجہ بندی بتاتی ہے کہ کیوں۔")}</div></div>
      <div class="card"><h3>3 · ${L_("Go, or get help coming", "جائیں یا مدد منگوائیں")}</h3><div class="small muted">${L_("Directions, call, alert the hospital before you arrive, request an ambulance (demo) or share a blood request on WhatsApp.", "راستہ، کال، ہسپتال کو پیشگی اطلاع، ایمبولینس یا واٹس ایپ پر خون کی درخواست۔")}</div></div>
    </div>
    <h2>${L_("Why you can trust the data", "ڈیٹا پر بھروسہ کیوں")}</h2>
    <div class="card small">
      ✅ ${L_("Updated by the people who know: ward staff, pharmacists and blood bank clerks, in one Roman-Urdu message from the staff portal.", "وارڈ اسٹاف، فارماسسٹ اور بلڈ بینک خود ایک پیغام میں اپ ڈیٹ کرتے ہیں۔")}<br>
      🕒 ${L_("Every number shows when it was last updated. Anything older than 2 hours is greyed out and marked 'may be outdated'.", "ہر معلومات کے ساتھ وقت درج ہے؛ 2 گھنٹے سے پرانی معلومات مدھم دکھائی جاتی ہے۔")}<br>
      🧮 ${L_("AI only understands language. A simple, explainable formula decides the ranking.", "AI صرف زبان سمجھتا ہے؛ فیصلہ ایک سادہ فارمولا کرتا ہے۔")}<br>
      🚨 ${L_("Danger signs always show Rescue 1122 first. Haazir never diagnoses.", "خطرے کی علامات پر ہمیشہ پہلے 1122۔ حاضر تشخیص نہیں کرتا۔")}<br>
      ⚠️ <b>${L_("This pilot uses simulated data for 10 Lahore public hospitals, 18 pharmacies, 6 blood banks and 12 ambulances.", "یہ پائلٹ فرضی ڈیٹا استعمال کرتا ہے۔")}</b>
    </div>`;
    const form = document.getElementById("askForm"), q = document.getElementById("q");
    form.onsubmit = (e) => { e.preventDefault(); if (q.value.trim()) location.hash = "#/ask?q=" + encodeURIComponent(q.value.trim()); };
    $app.querySelectorAll("[data-ex]").forEach((b) => b.onclick = () => { q.value = b.dataset.ex; form.requestSubmit ? form.requestSubmit() : form.onsubmit(new Event("submit")); });
    bindMic(document.getElementById("mic"), q, () => form.requestSubmit ? form.requestSubmit() : form.onsubmit(new Event("submit")));
    bindLocation();
    try {
      const s = await api("/stats");
      const c = s.counters || {};
      const el = document.getElementById("liveStats");
      if (el) el.innerHTML = [
        [s.freeBedsTotal, L_("free beds in 10 hospitals", "خالی بستر")],
        [`${s.ambulancesAvailable}/${s.ambulancesTotal}`, L_("demo ambulances available", "ایمبولینس دستیاب")],
        [s.machinesDown.length, L_("machines down right now", "مشینیں خراب")],
        [c.estMinutesSaved || 0, L_("est. minutes saved for families", "منٹ بچائے گئے")],
      ].map(([b, t]) => `<div class="stat"><b>${esc(b)}</b><span>${t}</span></div>`).join("");
    } catch (e) { const el = document.getElementById("liveStats"); if (el) el.innerHTML = errBox(e); }
  }

  function bindMic(btn, input, done) {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR || !btn) { if (btn) btn.style.display = "none"; return; }
    btn.onclick = () => {
      const r = new SR();
      r.lang = state.lang === "ur" ? "ur-PK" : "en-IN";
      r.interimResults = false;
      btn.classList.add("rec");
      r.onresult = (e) => { input.value = e.results[0][0].transcript; done && done(); };
      r.onend = () => btn.classList.remove("rec");
      r.onerror = () => btn.classList.remove("rec");
      r.start();
    };
  }

  async function askPage(params) {
    const q = params.get("q") || "";
    $app.innerHTML = `<form class="ask card" id="askForm" style="padding:6px;border:1px solid var(--line)"><input id="q" maxlength="300" value="${esc(q)}"><button type="button" class="mic" id="mic">🎤</button><button class="go">${L_("Find", "تلاش")}</button></form>
      ${locationRow(true)}<div id="res">${skeleton(3)}</div>`;
    const form = document.getElementById("askForm"), qi = document.getElementById("q");
    form.onsubmit = (e) => { e.preventDefault(); location.hash = "#/ask?q=" + encodeURIComponent(qi.value.trim()); };
    bindMic(document.getElementById("mic"), qi, () => form.onsubmit(new Event("submit")));
    bindLocation(() => askPage(params));
    const res = document.getElementById("res");
    try {
      const d = await post("/ask", { text: q, lat: state.loc.lat, lon: state.loc.lon, lang: state.lang });
      const e = d.entities || {};
      const reason = (state.lang === "ur" && d.reasonUr) ? d.reasonUr : d.reasonEn;
      let html = "";
      if (e.redFlag) html += redBanner(q, e.redFlagReason);
      html += `<div class="note">🧠 ${esc(reason || "")} <span class="pill o">${d.understoodBy === "ai" ? L_("understood by AI", "AI نے سمجھا") : L_("keyword match", "الفاظ سے")}</span>
        ${e.department ? `<span class="pill x">${esc(dept(e.department))}</span>` : ""}${e.urgency && e.urgency !== "routine" ? `<span class="pill r">${esc(e.urgency)}</span>` : ""}
        <button class="btn sm" id="say" style="margin-inline-start:6px">🔊</button></div>`;
      if (d.minutesSaved) html += `<div class="note">⏱️ ${L_("The nearest hospital can't help right now, so we sent you to the best option instead. That saves a wasted trip (about 25 minutes).", "قریبی ہسپتال ابھی مدد نہیں کر سکتا، اس لیے بہتر آپشن دکھایا۔")}</div>`;
      if (d.intent === "ambulance") {
        html += `<div class="card"><h3>🚑 ${L_("Ambulance", "ایمبولینس")}</h3><p class="small muted">${L_("For any emergency call Rescue 1122. You can also request the nearest vehicle from the demo ambulance network.", "کسی بھی ایمرجنسی میں 1122 کال کریں۔")}</p>
          <div class="btns"><a class="btn d" href="tel:1122">📞 ${L_("Call Rescue 1122", "ریسکیو 1122")}</a><button class="btn p" data-amb="${esc(q)}">🚑 ${L_("Request ambulance (demo)", "ایمبولینس منگوائیں (ڈیمو)")}</button></div></div>`;
      }
      if (d.hospitals) html += d.hospitals.length ? d.hospitals.map((h, i) => hospitalCard(h, i, { redFlag: e.redFlag, condition: q })).join("") : `<div class="empty">${L_("No matching hospital found.", "کوئی ہسپتال نہیں ملا۔")}</div>`;
      res.innerHTML = html + (d.medicine ? '<div id="medRes"></div>' : "") + (d.blood ? '<div id="bloodRes"></div>' : "") + (d.equipment ? '<div id="eqRes"></div>' : "");
      if (d.medicine) renderMedicine(document.getElementById("medRes"), d.medicine);
      if (d.blood) renderBlood(document.getElementById("bloodRes"), d.blood);
      if (d.equipment) renderEquipment(document.getElementById("eqRes"), d.equipment);
      const say = document.getElementById("say"); if (say) say.onclick = () => speak(reason || "");
      bindActions(res);
    } catch (err) { res.innerHTML = errBox(err); }
  }

  async function hospitalsPage(params) {
    const sel = { dept: params.get("dept") || "Emergency", female: params.get("female") === "1", sehat: params.get("sehat") === "1" };
    $app.innerHTML = `<h1>🛏️ ${L_("Hospital beds right now", "اس وقت ہسپتال بستر")}</h1>${locationRow(true)}
      <div class="chips" id="deptChips">${DEPTS.map((d) => `<button class="chip ${d === sel.dept ? "on" : ""}" data-d="${d}">${esc(dept(d))}</button>`).join("")}</div>
      <div class="chips"><button class="chip ${sel.sehat ? "on" : ""}" id="fSehat">Sehat Card</button><button class="chip ${sel.female ? "on" : ""}" id="fFem">♀ ${L_("Female doctor", "لیڈی ڈاکٹر")}</button></div>
      <div id="res">${skeleton(3)}</div>`;
    const go = () => { location.hash = `#/hospitals?dept=${encodeURIComponent(sel.dept)}${sel.female ? "&female=1" : ""}${sel.sehat ? "&sehat=1" : ""}`; };
    $app.querySelectorAll("[data-d]").forEach((b) => b.onclick = () => { sel.dept = b.dataset.d; go(); });
    document.getElementById("fSehat").onclick = () => { sel.sehat = !sel.sehat; go(); };
    document.getElementById("fFem").onclick = () => { sel.female = !sel.female; go(); };
    bindLocation(() => hospitalsPage(params));
    const res = document.getElementById("res");
    try {
      const d = await api(`/hospitals?${locQ()}&dept=${encodeURIComponent(sel.dept)}${sel.female ? "&female=1" : ""}${sel.sehat ? "&sehat=1" : ""}`);
      res.innerHTML = d.hospitals.length ? d.hospitals.map((h, i) => hospitalCard(h, i)).join("") : `<div class="empty">${L_("No hospital matches these filters.", "ان فلٹرز کے ساتھ کوئی ہسپتال نہیں۔")}</div>`;
      bindActions(res);
    } catch (e) { res.innerHTML = errBox(e); }
  }

  async function facilityPage(id) {
    $app.innerHTML = skeleton(4);
    try {
      const f = await api(`/facility/${encodeURIComponent(id)}?${locQ()}`);
      let html = `<a href="javascript:history.back()" class="small">← ${L_("Back", "واپس")}</a><h1>${esc(state.lang === "ur" && f.nameUr ? f.nameUr : f.name)}</h1>
        <div class="muted">${f.distanceKm} km ${f.etaMin ? "· ~" + f.etaMin + " min" : ""} ${f.erLoad ? "· " + loadPill(f.erLoad) : ""}</div>
        <div class="btns"><a class="btn p" target="_blank" rel="noopener" href="${dirUrl(f.lat, f.lon)}">🧭 ${L_("Directions", "راستہ")}</a>${f.type === "hospital" ? `<button class="btn" data-notify="${f.id}" data-dept="Emergency" data-name="${esc(f.name)}" data-eta="${f.etaMin}">🔔 ${L_("Notify hospital", "اطلاع دیں")}</button>` : ""}</div>`;
      if (f.beds && Object.keys(f.beds).length) {
        html += `<h2>${L_("Beds by department", "شعبہ وار بستر")}</h2><div class="card"><table class="t"><tr><th>${L_("Department", "شعبہ")}</th><th>${L_("Free", "خالی")}</th><th>${L_("Total", "کل")}</th><th>${L_("Updated", "اپ ڈیٹ")}</th></tr>` +
          Object.entries(f.beds).map(([k, b]) => `<tr class="${b.stale ? "stale" : ""}"><td>${esc(dept(k))}</td><td><span class="pill ${bedClass(b.free, b.total)}">${b.free}</span></td><td>${b.total}</td><td class="small muted">${ago(b.updatedAt)}${staleNote(b.updatedAt)}</td></tr>`).join("") + "</table></div>";
      }
      if (f.doctors && f.doctors.length) {
        html += `<h2>${L_("Doctors", "ڈاکٹر")}</h2><div class="card"><table class="t">` + f.doctors.map((d) => `<tr><td>${esc(d.name)} ${d.gender === "F" ? "♀" : ""}</td><td>${esc(dept(d.dept))}</td><td>${d.onDuty ? `<span class="pill g">${L_("on duty", "ڈیوٹی پر")}${d.shiftEnds ? " → " + d.shiftEnds : ""}</span>` : `<span class="pill x">${L_("off", "چھٹی")}</span>`}</td></tr>`).join("") + "</table></div>";
      }
      if (f.equipment && Object.keys(f.equipment).length) {
        html += `<h2>${L_("Machines", "مشینیں")}</h2><div class="card pills">` + Object.entries(f.equipment).map(([k, e]) => eqPill(k, e) + (e.queue ? `<span class="small muted">(${L_("queue", "قطار")} ${e.queue})</span>` : "")).join(" ") + "</div>";
      }
      if (f.medicine && f.medicine.length) {
        html += `<h2>${f.type === "hospital" ? L_("Free dispensary stock", "مفت ڈسپنسری") : L_("Medicine stock", "دوا اسٹاک")}</h2><div class="card"><table class="t">` + f.medicine.map((m) => `<tr class="${nowS() - m.updatedAt > 7200 ? "stale" : ""}"><td>${esc(m.name)}<div class="small muted">${esc(m.salt)} ${esc(m.strength)}</div></td><td>${m.inStock ? `<span class="pill g">${m.qty}</span>` : `<span class="pill r">${L_("out", "ختم")}</span>`}</td><td>${m.priceRs ? "Rs " + m.priceRs : L_("free", "مفت")}</td></tr>`).join("") + "</table></div>";
      }
      if (f.blood && Object.keys(f.blood).length) {
        html += `<h2>${L_("Blood units", "خون کی بوتلیں")}</h2><div class="card pills">` + Object.entries(f.blood).map(([g, b]) => `<span class="pill ${b.units === 0 ? "r" : b.units < 3 ? "a" : "g"}">${g}: ${b.units}</span>`).join("") + "</div>";
      }
      html += `<h2>${L_("Recent updates", "حالیہ اپ ڈیٹس")}</h2><div class="card small">` + (f.recentUpdates || []).map((u) => `<div>${esc(u.what)} · <span class="muted">${esc(u.by || "")}, ${ago(u.at)}</span></div>`).join("") + "</div>";
      $app.innerHTML = html;
      bindActions($app);
    } catch (e) { $app.innerHTML = errBox(e); }
  }

  // ---- ambulance
  function ambulancePage() {
    $app.innerHTML = `<h1>🚑 ${L_("Ambulance", "ایمبولینس")}</h1>
      <div class="alert-red"><h2>📞 ${L_("Real emergency? Call Rescue 1122.", "اصل ایمرجنسی؟ 1122 کال کریں۔")}</h2><div class="btns"><a class="btn w" href="tel:1122">${L_("Call Rescue 1122", "ریسکیو 1122 کال کریں")}</a></div></div>
      <div class="card"><h3>${L_("Demo ambulance network", "ڈیمو ایمبولینس نیٹ ورک")} <span class="pill x">${L_("simulated", "فرضی")}</span></h3>
      <p class="small muted">${L_("Picks the nearest free vehicle (advanced life support for danger signs), chooses the best hospital and alerts it before you arrive.", "قریبی ایمبولینس، بہترین ہسپتال، اور پیشگی اطلاع۔")}</p>
      <textarea id="cond" maxlength="300" placeholder="${L_("What happened? e.g. abbu behosh ho gaye, saans nahi aa rahi", "کیا ہوا؟")}"></textarea>
      ${locationRow(true)}
      <div class="btns"><button class="btn p" id="reqBtn">🚑 ${L_("Request ambulance (demo)", "ایمبولینس منگوائیں (ڈیمو)")}</button></div></div>`;
    bindLocation();
    const b = document.getElementById("reqBtn");
    b.onclick = () => requestAmbulance(document.getElementById("cond").value.trim() || "Emergency", null, b);
  }

  async function ambulanceTrack(rid) {
    $app.innerHTML = `<h1>🚑 ${L_("Ambulance on the way", "ایمبولینس راستے میں")} <span class="pill x">${L_("demo", "ڈیمو")}</span></h1>
      <div class="row" style="flex-wrap:wrap"><div class="grow"><div class="muted small">${L_("Arriving in", "پہنچنے میں")}</div><div class="countdown" id="cd">…</div><div id="ambInfo" class="small"></div></div>
      <a class="btn d" href="tel:1122">📞 ${L_("Call Rescue 1122", "ریسکیو 1122")}</a></div>
      <div class="map tall" id="ambMap"></div><div class="grid2"><div class="card"><h3>${L_("Status", "صورتحال")}</h3><ul class="timeline" id="tl"></ul></div><div class="card" id="hospBox"></div></div>`;
    let m = null, ambM = null, first = true;
    const labels = { assigned: L_("Ambulance assigned", "ایمبولینس مقرر"), en_route: L_("On the way to you", "آپ کی طرف روانہ"), arrived: L_("Arrived at patient", "مریض تک پہنچ گئی"), to_hospital: L_("Heading to hospital", "ہسپتال کی طرف"), at_hospital: L_("Reached hospital", "ہسپتال پہنچ گئی") };
    async function tick() {
      try {
        const s = await api(`/ambulance/request/${rid}`);
        if (first) {
          first = false;
          m = makeMap(document.getElementById("ambMap"), [s.patient.lat, s.patient.lon], 13);
          if (m) {
            window.L.marker([s.patient.lat, s.patient.lon], { icon: dotIcon("📍") }).addTo(m).bindPopup(L_("Patient", "مریض"));
            window.L.marker([s.destination.lat, s.destination.lon], { icon: dotIcon("🏥") }).addTo(m).bindPopup(esc(s.destination.name));
            ambM = window.L.marker([s.lat, s.lon], { icon: dotIcon("🚑") }).addTo(m);
            m.fitBounds([[s.patient.lat, s.patient.lon], [s.destination.lat, s.destination.lon], [s.lat, s.lon]], { padding: [40, 40] });
          }
          document.getElementById("ambInfo").innerHTML = `${esc(s.ambulance.id)} · ${s.ambulance.type === "ALS" ? L_("Advanced life support", "ایڈوانس لائف سپورٹ") : L_("Basic ambulance", "بیسک ایمبولینس")} · ${L_("real-world estimate", "اصل اندازہ")} ~${s.realEtaMin} min`;
          document.getElementById("hospBox").innerHTML = `<h3>🏥 ${esc(s.destination.name)}</h3><div class="note">✅ ${L_("Hospital has been alerted before arrival.", "ہسپتال کو پیشگی اطلاع دے دی گئی ہے۔")}</div><div class="small muted">${L_("Message sent to the emergency desk:", "ایمرجنسی ڈیسک کو پیغام:")}</div><div class="small">“${esc(s.summary)}”</div><div class="btns"><a class="btn sm" href="#/facility/${s.destination.id}">${L_("Hospital details", "ہسپتال کی تفصیل")}</a></div>`;
        }
        if (ambM) ambM.setLatLng([s.lat, s.lon]);
        const cd = document.getElementById("cd");
        if (cd) cd.textContent = s.status === "at_hospital" ? L_("At hospital", "ہسپتال میں") : s.status === "arrived" ? L_("Arrived", "پہنچ گئی") : `${Math.floor(s.etaSec / 60)}:${String(s.etaSec % 60).padStart(2, "0")}`;
        const done = new Set(s.timeline.map((x) => x.status));
        const tl = document.getElementById("tl");
        if (tl) tl.innerHTML = Object.keys(labels).map((k) => `<li class="${done.has(k) ? "done" : ""}">${labels[k]}</li>`).join("");
      } catch (e) { const cd = document.getElementById("cd"); if (cd) cd.textContent = "!"; }
    }
    await tick();
    every(tick, 2000);
  }

  // ---- medicine
  function medicinePage(params) {
    $app.innerHTML = `<h1>💊 ${L_("Find a medicine", "دوا تلاش کریں")}</h1>${locationRow(true)}
      <form class="field" id="mf"><input id="mq" maxlength="80" placeholder="${L_("Medicine name, e.g. Augmentin 625", "دوا کا نام")}" value="${esc(params.get("q") || "")}"><button class="btn p">${L_("Search", "تلاش")}</button></form>
      <div class="card"><h3>📷 ${L_("Scan a prescription", "نسخہ اسکین کریں")}</h3><p class="small muted">${L_("Take a photo. AI reads the medicine names, you confirm them, and we find one pharmacy that has everything.", "تصویر لیں؛ AI نام پڑھے گا، آپ تصدیق کریں، ہم ایک فارمیسی ڈھونڈیں گے جہاں سب کچھ ہو۔")}</p>
      <input type="file" id="rx" accept="image/*" capture="environment"> <button class="btn sm" id="rxManual">${L_("or type the list", "یا فہرست لکھیں")}</button><div id="rxOut"></div></div>
      <div id="res"></div>`;
    bindLocation();
    const mq = document.getElementById("mq");
    document.getElementById("mf").onsubmit = async (e) => {
      e.preventDefault();
      if (!mq.value.trim()) return;
      const res = document.getElementById("res");
      res.innerHTML = skeleton(3);
      try { renderMedicine(res, await api(`/medicine/search?q=${encodeURIComponent(mq.value.trim())}&${locQ()}`)); } catch (err) { res.innerHTML = errBox(err); }
    };
    if (params.get("q")) document.getElementById("mf").onsubmit(new Event("submit"));
    document.getElementById("rx").onchange = (e) => scanRx(e.target.files[0]);
    document.getElementById("rxManual").onclick = () => rxConfirm([{ name: "" }]);
  }

  function shrink(file) {
    return new Promise((ok, bad) => {
      const img = new Image();
      img.onload = () => {
        const s = Math.min(1, 1400 / Math.max(img.width, img.height));
        const c = document.createElement("canvas");
        c.width = Math.round(img.width * s); c.height = Math.round(img.height * s);
        c.getContext("2d").drawImage(img, 0, 0, c.width, c.height);
        ok(c.toDataURL("image/jpeg", 0.82));
      };
      img.onerror = () => bad(new Error(L_("Could not open this image", "تصویر نہیں کھل سکی")));
      img.src = URL.createObjectURL(file);
    });
  }

  async function scanRx(file) {
    if (!file) return;
    const out = document.getElementById("rxOut");
    out.innerHTML = `<div class="note">🔎 ${L_("Reading prescription with AI…", "AI نسخہ پڑھ رہا ہے…")}</div>`;
    try {
      const img = await shrink(file);
      const r = await post("/medicine/prescription", { imageBase64: img, lat: state.loc.lat, lon: state.loc.lon });
      if (!r.medicines.length) out.innerHTML = `<div class="note warn">${esc(r.message || L_("No medicine names could be read. Please type them.", "نام نہیں پڑھے جا سکے، براہ کرم لکھیں۔"))}</div>`;
      rxConfirm(r.medicines.length ? r.medicines : [{ name: "" }], !r.medicines.length);
    } catch (e) { out.innerHTML = errBox(e); }
  }

  function rxConfirm(meds, keepMsg) {
    const out = document.getElementById("rxOut");
    const rowH = (m) => `<div class="field rxrow"><input value="${esc(m.name || "")}" placeholder="${L_("Medicine name", "دوا کا نام")}">${m.confidence ? `<span class="pill ${m.confidence === "high" ? "g" : m.confidence === "low" ? "r" : "a"}" style="align-self:center">${esc(m.confidence)}</span>` : ""}</div>`;
    out.innerHTML = (keepMsg ? out.innerHTML : "") + `<div class="note">✏️ ${L_("Check the list. Edit anything the AI got wrong.", "فہرست چیک کریں اور غلطی درست کریں۔")}</div><div id="rxRows">${meds.map(rowH).join("")}</div>
      <div class="btns"><button class="btn sm" id="rxAdd">+ ${L_("Add medicine", "دوا شامل کریں")}</button><button class="btn p" id="rxGo">${L_("Find a pharmacy with everything", "سب کچھ ایک جگہ تلاش کریں")}</button></div><div id="planOut"></div>`;
    document.getElementById("rxAdd").onclick = () => document.getElementById("rxRows").insertAdjacentHTML("beforeend", rowH({ name: "" }));
    document.getElementById("rxGo").onclick = async () => {
      const items = [...document.querySelectorAll(".rxrow input")].map((i) => i.value.trim()).filter(Boolean);
      const po = document.getElementById("planOut");
      if (!items.length) { po.innerHTML = errBox(L_("Add at least one medicine", "کم از کم ایک دوا لکھیں")); return; }
      po.innerHTML = skeleton(1);
      try { renderPlan(po, await post("/medicine/plan", { items, lat: state.loc.lat, lon: state.loc.lon })); } catch (e) { po.innerHTML = errBox(e); }
    };
  }

  function renderPlan(el, p) {
    let html = "";
    if (p.onePharmacy) html += `<div class="note">✅ <b>${L_("One pharmacy has everything:", "ایک فارمیسی میں سب کچھ:")}</b> ${esc(p.stops[0].name)} (${p.stops[0].distanceKm} km)</div>`;
    else if (p.stops.length) html += `<div class="note warn">${L_(`No single pharmacy has everything. Fewest stops: ${p.stops.length}`, `کسی ایک فارمیسی میں سب کچھ نہیں؛ ${p.stops.length} جگہیں`)}</div>`;
    else html += `<div class="note warn">${L_("None of these medicines were found in stock nearby.", "یہ دوائیں قریب دستیاب نہیں۔")}</div>`;
    html += p.stops.map((s) => `<div class="card"><h3>🏪 ${esc(s.name)}</h3><div class="small muted">${s.distanceKm} km · ~${s.etaMin} min</div><table class="t">${Object.values(s.have).map((h) => `<tr><td>${esc(h.name)} ${h.substitute ? `<span class="pill a">${L_("same-salt substitute", "متبادل")}</span>` : ""}</td><td>Rs ${h.priceRs}</td></tr>`).join("")}</table><div class="btns"><a class="btn p sm" target="_blank" rel="noopener" href="${dirUrl(s.lat, s.lon)}">🧭 ${L_("Directions", "راستہ")}</a></div></div>`).join("");
    if (p.missing.length) html += `<div class="note warn">${L_("Not found:", "نہیں ملی:")} ${p.missing.map((m) => esc(m.asked)).join(", ")}</div>`;
    if (p.stops.length) html += `<div class="card"><b>${L_("Estimated total", "کل اندازاً")}: Rs ${p.totalRs}</b> <span class="small muted">(${L_("simulated prices", "فرضی قیمتیں")})</span></div>`;
    html += `<div class="note warn small">⚠️ ${L_("Confirm with your doctor or pharmacist before switching.", "تبدیل کرنے سے پہلے ڈاکٹر یا فارماسسٹ سے تصدیق کریں۔")}</div>`;
    el.innerHTML = html;
  }

  function renderMedicine(el, d) {
    if (!d.matched || !d.matched.length) { el.innerHTML = `<div class="empty">${L_("We couldn't match that medicine name. Try the brand name printed on the box.", "دوا کا نام نہیں ملا۔ ڈبے پر لکھا نام آزمائیں۔")}</div>`; return; }
    const m = d.matched[0];
    let html = `<div class="card"><h3>💊 ${esc(m.name)}</h3><div class="small muted">${L_("Active ingredient", "جزو")}: ${esc(m.salt)} ${esc(m.strength)}</div>`;
    if (d.alternatives.length) html += `<div class="small" style="margin-top:8px"><b>${L_("Cheaper same-salt alternatives", "اسی جزو کی سستی متبادل")}:</b> ${d.alternatives.map((a) => `${esc(a.name)} (~Rs ${a.priceRs})`).join(" · ")}</div><div class="small" style="color:var(--warn)">⚠️ ${L_("Confirm with your doctor or pharmacist before switching.", "تبدیل کرنے سے پہلے ڈاکٹر یا فارماسسٹ سے تصدیق کریں۔")}</div>`;
    html += `</div><div class="map" id="medMap"></div>`;
    if (d.dispensaries.length) html += `<h2>🏥 ${L_("Free at hospital dispensaries", "ہسپتال ڈسپنسری میں مفت")}</h2>` + d.dispensaries.map(stockCard).join("");
    html += `<h2>🏪 ${L_("Pharmacies with stock", "فارمیسیاں جہاں دستیاب ہے")}</h2>` + (d.pharmacies.length ? d.pharmacies.map(stockCard).join("") : `<div class="empty">${L_("Out of stock everywhere nearby.", "قریب کہیں دستیاب نہیں۔")}</div>`);
    el.innerHTML = html;
    const mp = makeMap(document.getElementById("medMap"), [state.loc.lat, state.loc.lon], 12);
    if (mp) { youMarker(mp); [...d.pharmacies, ...d.dispensaries].forEach((p) => window.L.circleMarker([p.lat, p.lon], { radius: 8, color: p.hasExact ? "#138a4a" : "#b26a00", fillOpacity: .8 }).addTo(mp).bindPopup(esc(p.name))); }
  }
  function stockCard(p) {
    return `<div class="card"><div class="row"><div class="grow"><h3>${esc(p.name)}</h3><div class="small muted">${p.distanceKm} km · ~${p.etaMin} min ${p.open24h ? "· 24h" : ""}</div>
      <div class="pills">${p.stock.map((s) => `<span class="pill ${s.exact ? "g" : "a"} ${s.stale ? "stale" : ""}">${esc(s.name)} · ${s.qty} ${L_("left", "باقی")} · ${s.priceRs ? "Rs " + s.priceRs : L_("free", "مفت")}</span>`).join("")}</div>
      <div class="small muted">${L_("updated", "اپ ڈیٹ")} ${ago(Math.max(...p.stock.map((s) => s.updatedAt)))}</div></div></div>
      <div class="btns"><a class="btn p sm" target="_blank" rel="noopener" href="${dirUrl(p.lat, p.lon)}">🧭 ${L_("Directions", "راستہ")}</a><a class="btn sm" href="#/facility/${p.id}">${L_("Stock list", "اسٹاک")}</a></div></div>`;
  }

  // ---- blood
  function bloodPage(params) {
    const g = params.get("group") || "O-";
    $app.innerHTML = `<h1>🩸 ${L_("Find blood", "خون تلاش کریں")}</h1>${locationRow(true)}
      <div class="chips">${GROUPS.map((x) => `<button class="chip ${x === g ? "on" : ""}" data-g="${x}">${x}</button>`).join("")}</div>
      <div class="field"><select id="units">${[1, 2, 3, 4, 5, 6].map((u) => `<option ${String(u) === (params.get("units") || "2") ? "selected" : ""}>${u}</option>`).join("")}</select><span class="muted" style="align-self:center">${L_("units / bottles needed", "بوتلیں درکار")}</span></div>
      <div id="res">${skeleton(2)}</div>`;
    bindLocation(() => bloodPage(params));
    $app.querySelectorAll("[data-g]").forEach((b) => b.onclick = () => { location.hash = `#/blood?group=${encodeURIComponent(b.dataset.g)}&units=${document.getElementById("units").value}`; });
    document.getElementById("units").onchange = (e) => { location.hash = `#/blood?group=${encodeURIComponent(g)}&units=${e.target.value}`; };
    const res = document.getElementById("res");
    api(`/blood/search?group=${encodeURIComponent(g)}&units=${params.get("units") || 2}&${locQ()}`).then((d) => renderBlood(res, d)).catch((e) => res.innerHTML = errBox(e));
  }
  async function renderBlood(el, d) {
    let html = `<div class="note small">ℹ️ ${L_(`A patient needing ${d.group} can usually receive: ${d.compatibleGroups.join(", ")}.`, `${d.group} کے مریض کو عام طور پر یہ گروپ لگ سکتے ہیں: ${d.compatibleGroups.join("، ")}`)} ${esc(d.compatNote)}</div>`;
    html += d.banks.map((b, i) => `<div class="card ${i === 0 && b.enough ? "top1" : ""} ${b.stale ? "stale" : ""}"><div class="row"><div class="big ${b.exactUnits >= d.units ? "g" : b.exactUnits > 0 ? "a" : "r"}">${b.exactUnits}<small>${esc(d.group)} ${L_("units", "بوتلیں")}</small></div>
      <div class="grow"><h3>${esc(b.name)}</h3><div class="small muted">${b.distanceKm} km · ~${b.etaMin} min · ${L_("updated", "اپ ڈیٹ")} ${ago(b.updatedAt)}${staleNote(b.updatedAt)}</div>
      ${Object.keys(b.compatibleUnits).length ? `<div class="pills">${Object.entries(b.compatibleUnits).map(([g, u]) => `<span class="pill o">${L_("compatible", "موزوں")} ${g}: ${u}</span>`).join("")}</div>` : ""}</div></div>
      <div class="btns"><a class="btn p sm" target="_blank" rel="noopener" href="${dirUrl(b.lat, b.lon)}">🧭 ${L_("Directions", "راستہ")}</a></div></div>`).join("");
    html += `<div class="card"><h3>📣 ${L_("Ask donors on WhatsApp", "واٹس ایپ پر ڈونرز سے رابطہ")}</h3><p class="small muted">${L_("Creates a clear, ready-to-forward request in English and Urdu.", "انگریزی اور اردو میں واضح پیغام۔")}</p>
      <div class="field"><select id="bHosp"><option>Mayo Hospital</option><option>Services Hospital</option><option>Jinnah Hospital</option><option>Sir Ganga Ram Hospital</option><option>Lahore General Hospital</option><option>Children's Hospital Lahore</option><option>Punjab Institute of Cardiology</option><option>Shaikh Zayed Hospital</option></select><input id="bContact" maxlength="30" placeholder="${L_("Contact number (optional)", "رابطہ نمبر (اختیاری)")}"></div>
      <div class="btns"><button class="btn p" id="bReq">📲 ${L_("Create request & share", "درخواست بنائیں اور شیئر کریں")}</button></div><div id="bOut"></div></div>`;
    el.innerHTML = html;
    document.getElementById("bReq").onclick = async (ev) => {
      ev.target.disabled = true;
      try {
        const r = await post("/blood/request", { group: d.group, units: d.units, hospital: document.getElementById("bHosp").value, contact: document.getElementById("bContact").value });
        document.getElementById("bOut").innerHTML = `<div class="note small">${esc(r.message)}<br><span class="ur">${esc(r.messageUr)}</span></div><div class="btns"><a class="btn p" target="_blank" rel="noopener" href="${r.whatsappUrl}">${L_("Open WhatsApp", "واٹس ایپ کھولیں")}</a></div>`;
      } catch (e) { document.getElementById("bOut").innerHTML = errBox(e); }
      ev.target.disabled = false;
    };
  }

  // ---- equipment
  function equipmentPage(params) {
    const t = params.get("type") || "CT";
    $app.innerHTML = `<h1>🩻 ${L_("Where is it working right now?", "اس وقت کہاں چالو ہے؟")}</h1>${locationRow(true)}
      <div class="chips">${EQUIP.map((x) => `<button class="chip ${x === t ? "on" : ""}" data-t="${x}">${x}</button>`).join("")}</div><div id="res">${skeleton(3)}</div>`;
    bindLocation(() => equipmentPage(params));
    $app.querySelectorAll("[data-t]").forEach((b) => b.onclick = () => { location.hash = "#/equipment?type=" + b.dataset.t; });
    const res = document.getElementById("res");
    api(`/equipment?type=${t}&${locQ()}`).then((d) => renderEquipment(res, d)).catch((e) => res.innerHTML = errBox(e));
  }
  function renderEquipment(el, d) {
    el.innerHTML = `<h2>${esc(d.type)}</h2>` + (d.results.length ? d.results.map((r, i) => `<div class="card ${i === 0 && r.status === "working" ? "top1" : ""} ${r.stale ? "stale" : ""}"><div class="row"><div class="grow"><h3>${esc(r.name)}</h3>
      <div class="pills">${eqPill(d.type, r)}${r.waitMin != null ? `<span class="pill x">${L_("queue", "قطار")} ${r.queue} · ~${r.waitMin} min ${L_("wait", "انتظار")}</span>` : ""}</div>
      <div class="small muted">${r.distanceKm} km · ~${r.etaMin} min · ${L_("updated", "اپ ڈیٹ")} ${ago(r.updatedAt)}${staleNote(r.updatedAt)}</div></div></div>
      <div class="btns"><a class="btn p sm" target="_blank" rel="noopener" href="${dirUrl(r.lat, r.lon)}">🧭 ${L_("Directions", "راستہ")}</a><a class="btn sm" href="#/facility/${r.id}">${L_("Details", "تفصیل")}</a></div></div>`).join("") : `<div class="empty">${L_("No hospital lists this machine.", "کسی ہسپتال میں یہ مشین درج نہیں۔")}</div>`);
  }

  // ---- staff portal
  async function staffPage() {
    if (!state.staff) {
      $app.innerHTML = `<h1>🧑‍⚕️ ${L_("Staff portal", "اسٹاف پورٹل")}</h1><div class="card"><p class="small muted">${L_("Ward staff, pharmacists and blood bank clerks keep Haazir accurate. Pick your facility.", "اپنا ادارہ منتخب کریں۔")}</p>
        <div class="field"><select id="sFac"><option>${L_("Loading…", "لوڈ ہو رہا ہے…")}</option></select></div>
        <div class="field"><input id="sPin" type="password" inputmode="numeric" maxlength="8" placeholder="PIN"></div>
        <div class="note small">${L_("Demo PIN:", "ڈیمو PIN:")} <b>1234</b></div>
        <div class="btns"><button class="btn p" id="sGo">${L_("Open portal", "پورٹل کھولیں")}</button></div><div id="sOut"></div></div>`;
      try {
        const d = await api("/facilities");
        const groups = { hospital: L_("Hospitals", "ہسپتال"), pharmacy: L_("Pharmacies", "فارمیسیاں"), bloodbank: L_("Blood banks", "بلڈ بینک") };
        document.getElementById("sFac").innerHTML = Object.entries(groups).map(([t, lbl]) => `<optgroup label="${lbl}">${d.facilities.filter((f) => f.type === t).map((f) => `<option value="${f.id}">${esc(f.name)}</option>`).join("")}</optgroup>`).join("");
      } catch (e) { document.getElementById("sOut").innerHTML = errBox(e); }
      document.getElementById("sGo").onclick = async () => {
        const facilityId = document.getElementById("sFac").value, pin = document.getElementById("sPin").value;
        try { const r = await post("/staff/login", { facilityId, pin }); state.staff = { facilityId, pin, name: r.facility.name, type: r.facility.type, tab: r.facility.type === "hospital" ? "alerts" : r.facility.type === "pharmacy" ? "stock" : "blood" }; staffPage(); }
        catch (e) { document.getElementById("sOut").innerHTML = errBox(e); }
      };
      return;
    }
    const s = state.staff;
    const tabs = s.type === "hospital" ? [["alerts", "🔔 " + L_("Alerts", "الرٹس")], ["quick", "⚡ " + L_("Quick update", "فوری اپ ڈیٹ")], ["beds", L_("Beds", "بستر")], ["doctors", L_("Doctors", "ڈاکٹر")], ["equipment", L_("Equipment", "مشینیں")], ["stock", L_("Dispensary", "ڈسپنسری")]]
      : s.type === "pharmacy" ? [["stock", L_("Stock", "اسٹاک")], ["quick", "⚡ " + L_("Quick update", "فوری اپ ڈیٹ")]] : [["blood", L_("Blood", "خون")], ["quick", "⚡ " + L_("Quick update", "فوری اپ ڈیٹ")]];
    $app.innerHTML = `<div class="row"><div class="grow"><h1>🧑‍⚕️ ${esc(s.name)}</h1></div><button class="btn sm" id="sOutBtn">${L_("Switch facility", "ادارہ تبدیل")}</button></div>
      <div class="tabs">${tabs.map(([k, l]) => `<button data-tab="${k}" class="${s.tab === k ? "on" : ""}">${l}</button>`).join("")}</div><div id="sBody">${skeleton(2)}</div>`;
    document.getElementById("sOutBtn").onclick = () => { state.staff = null; staffPage(); };
    $app.querySelectorAll("[data-tab]").forEach((b) => b.onclick = () => { s.tab = b.dataset.tab; cleanup(); staffPage(); });
    const body = document.getElementById("sBody");
    const send = async (changes) => { try { await post("/staff/update", { facilityId: s.facilityId, pin: s.pin, changes }); renderTab(); } catch (e) { alert(e.message); } };
    async function renderTab() {
      if (s.tab === "alerts") return renderAlerts();
      if (s.tab === "quick") return renderQuick();
      let f;
      try { f = await api(`/facility/${s.facilityId}`); } catch (e) { body.innerHTML = errBox(e); return; }
      if (s.tab === "beds") {
        body.innerHTML = `<div class="card">${Object.entries(f.beds).map(([k, b]) => `<div class="ctl"><div class="grow"><b>${esc(dept(k))}</b><div class="small muted">${L_("of", "میں سے")} ${b.total} · ${ago(b.updatedAt)}</div></div><button data-bed="${esc(k)}" data-d="-1">−</button><span class="n">${b.free}</span><button data-bed="${esc(k)}" data-d="1">+</button></div>`).join("")}<div class="small muted">${L_("Free beds. Tap + when a bed frees up and − when a patient is admitted.", "خالی بستر")}</div></div>`;
        body.querySelectorAll("[data-bed]").forEach((b) => b.onclick = () => send([{ kind: "bed", key: b.dataset.bed, delta: +b.dataset.d }]));
      } else if (s.tab === "doctors") {
        body.innerHTML = `<div class="card">${f.doctors.map((d) => `<div class="ctl"><div class="grow"><b>${esc(d.name)}</b> ${d.gender === "F" ? "♀" : ""}<div class="small muted">${esc(dept(d.dept))} · ${L_("shift ends", "شفٹ ختم")} ${esc(d.shiftEnds || "-")}</div></div><button style="width:auto;padding:0 12px;font-size:14px" class="${d.onDuty ? "" : ""}" data-doc="${esc(d.key)}" data-on="${d.onDuty ? 0 : 1}">${d.onDuty ? "✅ " + L_("On duty", "ڈیوٹی پر") : "⏸ " + L_("Off", "آف")}</button></div>`).join("")}</div>`;
        body.querySelectorAll("[data-doc]").forEach((b) => b.onclick = () => send([{ kind: "doctor", key: b.dataset.doc, onDuty: b.dataset.on === "1" }]));
      } else if (s.tab === "equipment") {
        body.innerHTML = `<div class="card">${Object.entries(f.equipment).map(([k, e]) => `<div class="ctl"><div class="grow"><b>${k}</b><div class="small muted">${ago(e.updatedAt)}</div></div><select data-eq="${k}" class="btn sm">${["working", "busy", "down"].map((st) => `<option ${st === e.status ? "selected" : ""}>${st}</option>`).join("")}</select></div>`).join("")}</div>`;
        body.querySelectorAll("[data-eq]").forEach((sel) => sel.onchange = () => send([{ kind: "equipment", key: sel.dataset.eq, status: sel.value }]));
      } else if (s.tab === "stock") {
        body.innerHTML = f.medicine.length ? `<div class="card">${f.medicine.map((m) => `<div class="ctl"><div class="grow"><b>${esc(m.name)}</b><div class="small muted">${ago(m.updatedAt)}</div></div><button data-med="${esc(m.key)}" data-d="-5">−</button><span class="n">${m.qty}</span><button data-med="${esc(m.key)}" data-d="5">+</button><button data-med0="${esc(m.key)}" style="width:auto;padding:0 10px;font-size:13px">${L_("Out", "ختم")}</button></div>`).join("")}</div>` : `<div class="empty">${L_("No stock listed", "کوئی اسٹاک نہیں")}</div>`;
        body.querySelectorAll("[data-med]").forEach((b) => b.onclick = () => send([{ kind: "medicine", key: b.dataset.med, delta: +b.dataset.d }]));
        body.querySelectorAll("[data-med0]").forEach((b) => b.onclick = () => send([{ kind: "medicine", key: b.dataset.med0, qty: 0 }]));
      } else if (s.tab === "blood") {
        body.innerHTML = `<div class="card">${Object.entries(f.blood).map(([g, b]) => `<div class="ctl"><div class="grow"><b>${g}</b><div class="small muted">${ago(b.updatedAt)}</div></div><button data-bl="${g}" data-d="-1">−</button><span class="n">${b.units}</span><button data-bl="${g}" data-d="1">+</button></div>`).join("")}</div>`;
        body.querySelectorAll("[data-bl]").forEach((b) => b.onclick = () => send([{ kind: "blood", key: b.dataset.bl, delta: +b.dataset.d }]));
      }
    }
    function renderQuick() {
      const ex = s.type === "hospital" ? "Medicine ward 3 mein 2 bed khali, CT kharab hai, Dr Sana 8 baje tak duty pe" : s.type === "pharmacy" ? "Panadol khatam, Augmentin 20 packs aa gaye" : "O- 2 unit aa gaye, B+ 10 unit";
      body.innerHTML = `<div class="card"><h3>⚡ ${L_("Type one message, the way you'd send it on WhatsApp", "ایک پیغام لکھیں، جیسے واٹس ایپ پر")}</h3>
        <textarea id="qText" maxlength="500" placeholder="${esc(ex)}"></textarea><div class="btns"><button class="btn sm" id="qEx">${L_("Use example", "مثال")}</button><button class="btn p" id="qParse">${L_("Preview changes", "تبدیلیاں دیکھیں")}</button></div><div id="qOut"></div></div>`;
      document.getElementById("qEx").onclick = () => { document.getElementById("qText").value = ex; };
      document.getElementById("qParse").onclick = async (ev) => {
        const text = document.getElementById("qText").value.trim();
        const out = document.getElementById("qOut");
        if (!text) return;
        ev.target.disabled = true; out.innerHTML = `<div class="note">🧠 ${L_("Understanding…", "سمجھ رہا ہے…")}</div>`;
        try {
          const r = await post("/staff/parse", { facilityId: s.facilityId, pin: s.pin, text });
          if (!r.changes.length) { out.innerHTML = `<div class="note warn">${L_("No changes understood. Try naming the ward, machine, doctor or medicine.", "کوئی تبدیلی سمجھ نہیں آئی۔")}</div>`; }
          else {
            out.innerHTML = `<div class="note">${L_("Understood", "سمجھا گیا")} <span class="pill o">${r.understoodBy === "ai" ? "AI" : L_("keywords", "الفاظ")}</span></div>` +
              r.changes.map((c, i) => `<label class="ctl"><span class="grow">${esc(c.label)}</span><input type="checkbox" checked data-i="${i}" style="width:24px;height:24px"></label>`).join("") +
              `<div class="btns"><button class="btn p" id="qApply">✅ ${L_("Confirm & publish", "تصدیق کریں")}</button></div>`;
            document.getElementById("qApply").onclick = async () => {
              const chosen = r.changes.filter((c, i) => out.querySelector(`[data-i="${i}"]`).checked);
              try { const u = await post("/staff/update", { facilityId: s.facilityId, pin: s.pin, changes: chosen }); out.innerHTML = `<div class="note">✅ ${u.applied.length} ${L_("updates published. Patients see them now.", "اپ ڈیٹس شائع ہو گئیں۔")}</div>`; }
              catch (e) { out.innerHTML = errBox(e); }
            };
          }
        } catch (e) { out.innerHTML = errBox(e); }
        ev.target.disabled = false;
      };
    }
    async function renderAlerts() {
      async function load() {
        try {
          const d = await post("/staff/alerts", { facilityId: s.facilityId, pin: s.pin });
          if (s.tab !== "alerts") return;
          body.innerHTML = d.alerts.length ? d.alerts.map((a) => `<div class="card ${a.ack ? "stale" : "top1"}"><div class="row"><div class="grow"><b>${a.source === "ambulance" ? "🚑" : "👪"} ${esc(dept(a.department))}</b> · <span class="small muted">${ago(a.createdAt)}${a.etaSec ? " · ETA ~" + Math.round(a.etaSec / 60) + " min" : ""} · ${L_("ref", "ریف")} ${esc(a.id)}</span><div>${esc(a.note)}</div></div>
            ${a.ack ? `<span class="pill g">${L_("acknowledged", "موصول")}</span>` : `<button class="btn p sm" data-ack="${esc(a.sk)}">${L_("Acknowledge", "موصول")}</button>`}</div></div>`).join("") : `<div class="empty">${L_("No incoming alerts. Families and ambulances that notify you will show up here.", "کوئی الرٹ نہیں۔")}</div>`;
          body.querySelectorAll("[data-ack]").forEach((b) => b.onclick = async () => { b.disabled = true; try { await post("/staff/alerts/ack", { facilityId: s.facilityId, pin: s.pin, sk: b.dataset.ack }); load(); } catch (e) { alert(e.message); } });
        } catch (e) { body.innerHTML = errBox(e); }
      }
      await load();
      every(load, 10000);
    }
    renderTab();
  }

  // ---- city dashboard
  async function dashboardPage() {
    $app.innerHTML = `<h1>🗺️ ${L_("Lahore health capacity: live", "لاہور صحت کی گنجائش")}</h1><p class="muted small">${L_("For the health department and Rescue 1122 control rooms. Refreshes every 15 seconds. Pilot data is simulated.", "محکمہ صحت اور 1122 کے لیے۔ ہر 15 سیکنڈ میں تازہ۔ فرضی ڈیٹا۔")}</p>
      <div class="stats" id="dStats">${'<div class="stat skel" style="height:72px"></div>'.repeat(8)}</div>
      <div class="legend" style="margin-top:12px"><span><span class="dot" style="background:#138a4a"></span> ${L_("hospital has room", "گنجائش")}</span><span><span class="dot" style="background:#b26a00"></span> ${L_("nearly full", "تقریباً بھرا")}</span><span><span class="dot" style="background:#c62828"></span> ${L_("full", "بھرا")}</span><span>🚑 ${L_("free", "فارغ")} / 🚨 ${L_("on a call", "مصروف")}</span><span><span class="dot" style="background:#7b5cd6"></span> ${L_("blood bank", "بلڈ بینک")}</span><span><span class="dot" style="background:#8a96a0"></span> ${L_("pharmacy", "فارمیسی")}</span></div>
      <div class="map tall" id="dMap"></div><div class="grid2" id="dLists"></div>`;
    const m = makeMap(document.getElementById("dMap"), [31.51, 74.32], 12);
    const layers = m ? { hosp: window.L.layerGroup().addTo(m), amb: window.L.layerGroup().addTo(m), bb: window.L.layerGroup().addTo(m), ph: window.L.layerGroup() } : null;
    if (m) window.L.control.layers(null, { [L_("Hospitals", "ہسپتال")]: layers.hosp, [L_("Ambulances", "ایمبولینس")]: layers.amb, [L_("Blood banks", "بلڈ بینک")]: layers.bb, [L_("Pharmacies", "فارمیسیاں")]: layers.ph }).addTo(m);
    async function load() {
      try {
        const [s, mp] = await Promise.all([api("/stats"), api("/map")]);
        const c = s.counters || {};
        const ds = document.getElementById("dStats");
        if (!ds) return;
        ds.innerHTML = [[s.freeBedsTotal, L_("free beds", "خالی بستر")], [s.hospitalsFull.length, L_("ERs full", "ایمرجنسی بھری")], [`${s.ambulancesAvailable}/${s.ambulancesTotal}`, L_("ambulances free", "ایمبولینس فارغ")], [s.machinesDown.length, L_("machines down", "مشینیں خراب")],
          [s.bloodShortages.join(" ") || "-", L_("blood shortages (<5 units)", "خون کی کمی")], [c.searches || 0, L_("searches", "تلاش")], [c.ambulanceRequests || 0, L_("ambulance requests", "ایمبولینس درخواستیں")], [c.estMinutesSaved || 0, L_("est. minutes saved", "منٹ بچائے")]]
          .map(([b, t]) => `<div class="stat"><b>${esc(b)}</b><span>${t}</span></div>`).join("");
        if (layers) {
          Object.values(layers).forEach((l) => l.clearLayers());
          mp.facilities.forEach((f) => {
            if (f.type === "hospital") window.L.circleMarker([f.lat, f.lon], { radius: 11, weight: 2, color: "#fff", fillColor: f.capacity < 0.8 ? "#138a4a" : f.capacity < 0.95 ? "#b26a00" : "#c62828", fillOpacity: .95 }).addTo(layers.hosp).bindPopup(`<b>${esc(f.name)}</b><br>${f.freeBeds} ${L_("free beds", "خالی بستر")} · ER ${esc(f.erLoad)}<br><a href="#/facility/${f.id}">${L_("Details", "تفصیل")}</a>`);
            else if (f.type === "bloodbank") window.L.circleMarker([f.lat, f.lon], { radius: 7, color: "#7b5cd6", fillOpacity: .9 }).addTo(layers.bb).bindPopup(esc(f.name));
            else window.L.circleMarker([f.lat, f.lon], { radius: 5, color: "#8a96a0", fillOpacity: .8 }).addTo(layers.ph).bindPopup(esc(f.name));
          });
          mp.ambulances.forEach((a) => window.L.marker([a.lat, a.lon], { icon: dotIcon(a.status === "available" ? "🚑" : "🚨") }).addTo(layers.amb).bindPopup(`${esc(a.id)} · ${esc(a.type)} · ${esc(a.status)}`));
        }
        const dl = document.getElementById("dLists");
        if (dl) dl.innerHTML = `<div class="card"><h3>${L_("Free beds by department", "شعبہ وار خالی بستر")}</h3><table class="t">${Object.entries(s.freeBedsByDept).map(([k, v]) => `<tr><td>${esc(dept(k))}</td><td><span class="pill ${v === 0 ? "r" : v < 10 ? "a" : "g"}">${v}</span></td></tr>`).join("")}</table></div>
          <div class="card"><h3>${L_("Needs attention", "توجہ طلب")}</h3><div class="small"><b>${L_("ERs at capacity", "بھری ایمرجنسی")}:</b> ${s.hospitalsFull.map(esc).join(", ") || "-"}</div>
          <div class="small" style="margin-top:6px"><b>${L_("Machines down", "خراب مشینیں")}:</b> ${s.machinesDown.map((x) => `${esc(x.equipment)} (${esc(x.hospital)})`).join(", ") || "-"}</div>
          <div class="small" style="margin-top:6px"><b>${L_("Blood units city-wide", "شہر بھر میں خون")}:</b> ${Object.entries(s.bloodUnits).map(([g, u]) => `<span class="pill ${u < 5 ? "r" : "g"}">${g} ${u}</span>`).join(" ")}</div></div>`;
      } catch (e) { const ds = document.getElementById("dStats"); if (ds) ds.innerHTML = errBox(e); }
    }
    await load();
    every(load, 15000);
  }

  // ------------------------------------------------------------ router
  function route() {
    cleanup();
    chrome();
    document.querySelectorAll(".modal-bg").forEach((x) => x.remove());
    const h = location.hash.replace(/^#/, "") || "/";
    const [path, qs] = h.split("?");
    const params = new URLSearchParams(qs || "");
    const parts = path.split("/").filter(Boolean);
    window.scrollTo(0, 0);
    if (window.HAAZIR_API === undefined) { $app.innerHTML = errBox("API not configured"); return; }
    if (!parts.length) return home();
    switch (parts[0]) {
      case "ask": return askPage(params);
      case "hospitals": return hospitalsPage(params);
      case "facility": return facilityPage(parts[1]);
      case "ambulance": return parts[1] ? ambulanceTrack(parts[1]) : ambulancePage();
      case "medicine": return medicinePage(params);
      case "blood": return bloodPage(params);
      case "equipment": return equipmentPage(params);
      case "staff": return staffPage();
      case "dashboard": return dashboardPage();
      default: return home();
    }
  }
  window.addEventListener("hashchange", route);
  route();
})();
