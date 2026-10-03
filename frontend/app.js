/* Haazir frontend: hash-routed single page, no build step.
   Facilities are real. Availability is shown ONLY when staff have reported it; otherwise "not reported yet". */
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
  const HELPLINES = [["1122", "Rescue 1122", "ریسکیو 1122"], ["115", "Edhi Ambulance", "ایدھی ایمبولینس"]];

  function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } }
  const state = { lang: store("lang") || "en", loc: null, staff: null, demo: true }; // sample data always shown (tagged "sample"); real staff reports replace it
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
    if (m < 2880) return L_(`${Math.round(m / 60)} h ago`, `${Math.round(m / 60)} گھنٹے پہلے`);
    return L_(`${Math.round(m / 1440)} days ago`, `${Math.round(m / 1440)} دن پہلے`);
  }
  const staleNote = (ts) => (ts && nowS() - ts > 7200 ? ` <span class="stale-note">${L_("may be outdated", "پرانی معلومات ہو سکتی ہے")}</span>` : "");
  const dirUrl = (lat, lon) => `https://www.google.com/maps/dir/?api=1&destination=${lat},${lon}`;
  const locQ = () => `lat=${state.loc.lat}&lon=${state.loc.lon}`;
  const NR = () => L_("not reported yet", "ابھی رپورٹ نہیں");
  const nrPill = (what) => `<span class="pill x">${esc(what)}: ${NR()}</span>`;

  async function api(path, opts) {
    const ctl = new AbortController();
    const timer = setTimeout(() => ctl.abort(), 28000);
    try {
      if (!state.demo) path += (path.includes("?") ? "&" : "?") + "demo=0";
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
    setTimeout(() => { try { m.invalidateSize(); } catch (e) {} }, 150); // re-measure after layout
    return m;
  }
  function youMarker(m) { if (m) window.L.circleMarker([state.loc.lat, state.loc.lon], { radius: 8, color: "#fff", weight: 3, fillColor: "#1e66f5", fillOpacity: 1 }).addTo(m).bindPopup(L_("You", "آپ")); }

  const skeleton = (n) => Array.from({ length: n || 3 }, () => '<div class="skel"></div>').join("");
  const errBox = (e) => `<div class="err">${esc(e.message || e)}</div>`;

  // ------------------------------------------------------------ chrome
  function chrome() {
    document.documentElement.lang = state.lang === "ur" ? "ur" : "en";
    document.documentElement.dir = state.lang === "ur" ? "rtl" : "ltr";
    document.getElementById("pilot").style.display = state.demo ? "none" : "";
    document.getElementById("pilot").textContent = state.demo
      ? L_("🧪 Demo mode: hospitals, pharmacies and blood banks are real places in Lahore; the availability numbers are SAMPLE data for this demo. Switch 'Demo data' off to see real staff reports only.", "🧪 ڈیمو: ہسپتال، فارمیسیاں اور بلڈ بینک اصل ہیں؛ دستیابی کے نمبر نمونہ (فرضی) ہیں۔ صرف اصل رپورٹس دیکھنے کے لیے ڈیمو بند کریں۔")
      : L_("Real reports only: availability shown here was reported by staff. Anything not reported says 'not reported yet'.", "صرف اصل رپورٹس: دستیابی اسٹاف نے رپورٹ کی ہے۔");
    const r = location.hash.split("?")[0];
    const link = (h, en, ur, cls) => `<a href="${h}" class="${cls || ""} ${r === h ? "on" : ""}">${L_(en, ur)}</a>`;
    document.getElementById("nav").innerHTML =
      link("#/hospitals", "Hospitals", "ہسپتال", "hide-m") + link("#/medicine", "Medicine", "دوا", "hide-m") +
      link("#/blood", "Blood", "خون", "hide-m") + link("#/dashboard", "Dashboard", "ڈیش بورڈ", "hide-m") +
      link("#/staff", "Staff", "اسٹاف") +
      `<button class="lang" id="langBtn">${state.lang === "ur" ? "English" : "اردو"}</button>`;
    document.getElementById("langBtn").onclick = () => { state.lang = state.lang === "ur" ? "en" : "ur"; store("lang", state.lang); route(); };
    const yr = new Date().getFullYear();
    document.getElementById("foot").innerHTML = `
      <div class="fgrid">
        <div class="fcol about"><a class="logo" href="#/"><span class="logo-mark">✚</span>Haazir <small>حاضر</small></a>
          <p>${L_("Know before you go. Haazir helps families in Lahore find a free bed, a doctor on duty, a working machine, medicine and blood, and helps hospital staff share it in one message.", "جانے سے پہلے جانیں۔ حاضر لاہور کے خاندانوں کو بستر، ڈاکٹر، مشین، دوا اور خون تلاش کرنے میں مدد دیتا ہے۔")}</p>
          <a class="btn p sm" href="#/contact">✉️ ${L_("Contact us", "رابطہ کریں")}</a></div>
        <div class="fcol"><h4>${L_("Find care", "علاج تلاش کریں")}</h4>
          <a href="#/hospitals">${L_("Hospital beds", "ہسپتال بستر")}</a><a href="#/ambulance">${L_("Ambulance", "ایمبولینس")}</a><a href="#/medicine">${L_("Medicine", "دوا")}</a>
          <a href="#/blood">${L_("Blood", "خون")}</a><a href="#/equipment">CT / MRI / ${L_("Dialysis", "ڈائیلاسز")}</a><a href="#/dashboard">${L_("City dashboard", "شہر ڈیش بورڈ")}</a></div>
        <div class="fcol"><h4>${L_("For hospitals", "ہسپتالوں کے لیے")}</h4>
          <a href="#/staff">${L_("Staff portal", "اسٹاف پورٹل")}</a><a href="#/contact?role=hospital">${L_("Join the pilot", "پائلٹ میں شامل ہوں")}</a>
          <a href="#/contact?role=pharmacy">${L_("Pharmacies", "فارمیسیاں")}</a><a href="#/contact?role=bloodbank">${L_("Blood banks", "بلڈ بینک")}</a></div>
        <div class="fcol"><h4>${L_("Emergency numbers", "ایمرجنسی نمبر")}</h4>
          <a href="tel:1122" class="em">🚑 Rescue 1122</a><a href="tel:115" class="em">🚑 Edhi ${L_("Ambulance", "ایمبولینس")} 115</a>
          <a href="tel:15">🚓 ${L_("Police", "پولیس")} 15</a><a href="tel:16">🚒 ${L_("Fire brigade", "فائر بریگیڈ")} 16</a></div>
        <div class="fcol"><h4>${L_("Contact", "رابطہ")}</h4>
          <span>📍 Lahore, Punjab, Pakistan</span><a href="#/contact">✉️ ${L_("Send us a message", "پیغام بھیجیں")}</a>
          <a href="#/contact?role=health_department">🏛️ ${L_("Health department partners", "محکمہ صحت")}</a></div>
      </div>
      <div class="fbottom">
        <span>© ${yr} Haazir · ${L_("Pilot for Lahore", "لاہور پائلٹ")}</span>
        <span>${L_("Availability numbers are sample data in this pilot; doctor names are fictional.", "اس پائلٹ میں دستیابی کے نمبر نمونہ ہیں؛ ڈاکٹروں کے نام فرضی ہیں۔")}</span>
        <span>${L_("Not medical advice. Haazir does not diagnose. In an emergency call", "طبی مشورہ نہیں۔ ایمرجنسی میں کال کریں")} <a href="tel:1122">1122</a>.</span>
        <span>${L_("Map data", "نقشہ")} © OpenStreetMap contributors</span>
      </div>`;
  }

  // ------------------------------------------------------------ shared blocks
  function locationRow(light) {
    const opts = Object.keys(AREAS).map((a) => `<option ${state.loc.label === a ? "selected" : ""}>${a}</option>`).join("");
    return `<div class="locrow ${light ? "light" : ""}">📍 <span id="locLabel">${esc(state.loc.label || L_("My location", "میری لوکیشن"))}</span>
      <button type="button" id="gpsBtn">${L_("Use my location", "میری لوکیشن")}</button>
      <select id="areaSel"><option value="">${L_("or pick area", "یا علاقہ چنیں")}</option>${opts}</select></div>`;
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

  const helplineBtns = (white) => HELPLINES.map(([n, en, ur], i) => `<a class="btn ${i === 0 ? (white ? "w" : "d") : ""}" ${i && white ? 'style="background:transparent;color:#fff;border-color:#fff"' : ""} href="tel:${n}">📞 ${L_(en, ur)}: ${n}</a>`).join("");

  function redBanner(reason, best) {
    return `<div class="alert-red">
      <h2>🚨 ${L_("Emergency: call an ambulance now", "ایمرجنسی: ابھی ایمبولینس بلائیں")}</h2>
      <div>${esc(reason ? L_("Warning sign: ", "خطرے کی علامت: ") + reason : "")}</div>
      <div class="btns">${helplineBtns(true)}</div>
      ${best ? `<div class="btns"><button class="btn" style="background:transparent;color:#fff;border-color:#fff" data-notify="${best.id}" data-dept="${esc(best.department || "Emergency")}" data-name="${esc(best.name)}" data-eta="${best.etaMin}" data-amb="1">🔔 ${L_("Tell", "اطلاع دیں:")} ${esc(best.name)} ${L_("you're coming", "کہ آپ آ رہے ہیں")}</button></div>` : ""}
      <div class="small" style="margin-top:8px;opacity:.9">${L_("Haazir is not a diagnosis. Call the ambulance first, then use the list below to choose and alert a hospital.", "یہ تشخیص نہیں۔ پہلے ایمبولینس بلائیں، پھر نیچے سے ہسپتال چنیں۔")}</div>
    </div>`;
  }

  const bedClass = (free) => (free == null ? "x" : free === 0 ? "r" : free <= 3 ? "a" : "g");
  const eqPill = (k, e) => {
    if (!e || e.status === "unknown") return nrPill(k);
    const c = e.status === "working" ? "g" : e.status === "busy" ? "a" : "r";
    const lbl = e.status === "working" ? L_("working", "چالو") : e.status === "busy" ? L_("busy", "مصروف") : L_("down", "خراب");
    return `<span class="pill ${c} ${e.stale ? "stale" : ""}">${k}: ${lbl}</span>`;
  };
  const ownPill = (o) => (o === "private" ? `<span class="pill a">💳 ${L_("Private · fees apply", "پرائیویٹ · فیس")}</span>` : `<span class="pill o">🏛️ ${L_("Government · free", "سرکاری · مفت")}</span>`);
  const loadPill = (l) => (l === "Unknown" ? "" : `<span class="pill ${l === "Low" ? "g" : l === "Busy" ? "a" : "r"}">ER ${l === "Low" ? L_("has space", "جگہ ہے") : l === "Busy" ? L_("busy", "مصروف") : L_("reported full", "بھرا ہوا")}</span>`);
  const demoPill = () => `<span class="pill sample" title="${L_("Sample data for this pilot", "پائلٹ کے لیے نمونہ ڈیٹا")}">${L_("sample", "نمونہ")}</span>`;
  const reportLine = (ts, by, demo) => (demo ? `${demoPill()}<span class="pill x">${ago(ts)}</span>` : ts ? `<span class="pill g">✓ ${L_("reported", "رپورٹ")} ${ago(ts)}${by ? " · " + esc(by) : ""}</span>${staleNote(ts)}` : `<span class="pill x">${L_("No live report yet", "ابھی کوئی رپورٹ نہیں")}</span>`);

  function hospitalCard(h, i) {
    const d = h.department;
    const reportedBeds = Object.values(h.beds);
    const free = d ? h.freeBeds : (reportedBeds.length ? reportedBeds.reduce((s, b) => s + b.free, 0) : null);
    const stale = d && h.beds[d] && h.beds[d].stale;
    const eqKeys = Object.keys(h.equipment);
    const docs = (h.doctorsOnDuty || []).slice(0, 2).map((x) => `${esc(x.name)}${x.gender === "F" ? " ♀" : ""}${x.dept ? " (" + esc(dept(x.dept)) + (x.shiftEnds ? ", " + L_("until", "تک") + " " + x.shiftEnds : "") + ")" : ""}`).join(" · ");
    return `<div class="card ${i === 0 ? "top1" : ""}">
      ${i === 0 ? `<div class="pill o" style="margin-bottom:8px">★ ${h.hasReports ? L_("Best match from current reports", "موجودہ رپورٹس کے مطابق بہترین") : L_("Nearest suitable hospital", "قریب ترین موزوں ہسپتال")}</div>` : ""}
      <div class="row">
        <div class="big ${bedClass(free)} ${stale ? "stale" : ""}">${free == null ? "?" : free}<small>${free == null ? L_("beds not<br>reported", "بستر رپورٹ<br>نہیں") : L_("free beds", "خالی بستر") + (d ? "<br>" + esc(dept(d)) : "")}</small></div>
        <div class="grow">
          <h3>${esc(state.lang === "ur" && h.nameUr ? h.nameUr : h.name)}</h3>
          <div class="muted small">${h.distanceKm} km · ~${h.etaMin} ${L_("min by road", "منٹ")}</div>
          <div class="pills">${ownPill(h.ownership)}${reportLine(h.updatedAt, null, h.demo)}${loadPill(h.erLoad)}${h.femaleDoctor ? `<span class="pill o">♀ ${L_("Female doctor reported on duty", "لیڈی ڈاکٹر ڈیوٹی پر")}</span>` : ""}${eqKeys.map((k) => eqPill(k, h.equipment[k])).join("")}</div>
          <div class="small">🩺 ${docs || `<span class="muted">${L_("Doctors on duty: not reported yet", "ڈیوٹی ڈاکٹر: ابھی رپورٹ نہیں")}</span>`}</div>
          ${h.why ? `<div class="why">${L_("Why:", "وجہ:")} ${esc(h.why)}</div>` : ""}
        </div>
      </div>
      <div class="btns">
        <a class="btn p" target="_blank" rel="noopener" href="${dirUrl(h.lat, h.lon)}">🧭 ${L_("Directions", "راستہ")}</a>
        <button class="btn" data-notify="${h.id}" data-dept="${esc(d || "Emergency")}" data-name="${esc(h.name)}" data-eta="${h.etaMin}">🔔 ${L_("Tell hospital you're coming", "ہسپتال کو اطلاع دیں")}</button>
        <a class="btn" href="#/facility/${h.id}">${L_("Details", "تفصیل")} →</a>
      </div>
    </div>`;
  }

  function bindActions(root) {
    root.querySelectorAll("[data-notify]").forEach((b) => b.onclick = () => notifyModal(b.dataset));
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
      <p class="small muted">${L_("Sends an alert to this hospital's Haazir staff portal so the team can prepare. Pilot: hospitals see it only if their staff use the portal, so please also call or go directly.", "ہسپتال کے اسٹاف پورٹل پر اطلاع جائے گی۔ پائلٹ: صرف اسی صورت میں نظر آئے گی جب اسٹاف پورٹل استعمال کرے۔")}</p>
      <div class="field"><select id="nDept">${DEPTS.map((d) => `<option ${d === ds.dept ? "selected" : ""} value="${d}">${dept(d)}</option>`).join("")}</select></div>
      <div class="field"><input id="nNote" maxlength="200" placeholder="${L_("What happened? e.g. chest pain, 60 year old man", "کیا ہوا؟ مثلاً سینے میں درد")}"></div>
      <div class="field"><input id="nEta" type="number" min="0" max="600" value="${esc(ds.eta || 20)}"> <span class="muted" style="align-self:center">${L_("minutes away", "منٹ دور")}</span></div>
      <label class="small"><input type="checkbox" id="nAmb" ${ds.amb ? "checked" : ""}> ${L_("Coming by ambulance (1122 / Edhi)", "ایمبولینس سے آ رہے ہیں")}</label>
      <div class="btns"><button class="btn p" id="nSend">${L_("Send alert", "اطلاع بھیجیں")}</button><button class="btn" id="nCancel">${L_("Cancel", "منسوخ")}</button></div><div id="nOut"></div>`);
    m.querySelector("#nCancel").onclick = () => m.remove();
    m.querySelector("#nSend").onclick = async (ev) => {
      ev.target.disabled = true;
      try {
        const r = await post("/notify", { facilityId: ds.notify, department: m.querySelector("#nDept").value, note: m.querySelector("#nNote").value, eta: +m.querySelector("#nEta").value, byAmbulance: m.querySelector("#nAmb").checked });
        m.querySelector("#nOut").innerHTML = `<div class="note">✅ ${L_("Alert sent to the staff portal. Reference:", "اطلاع بھیج دی گئی۔ ریفرنس:")} <b style="font-size:20px">${esc(r.referenceCode)}</b></div>`;
      } catch (e) { m.querySelector("#nOut").innerHTML = errBox(e); ev.target.disabled = false; }
    };
  }

  function speak(text) {
    try { if (!window.speechSynthesis) return; const u = new SpeechSynthesisUtterance(text); u.lang = state.lang === "ur" ? "ur-PK" : "en-US"; speechSynthesis.cancel(); speechSynthesis.speak(u); } catch (e) {}
  }

  // ------------------------------------------------------------ pages
  async function home() {
    const ex = ["abbu ko seenay mein dard", "O negative blood chahiye 2 bottle", "Augmentin kahan milegi Johar Town", "CT scan kahan ho raha hai abhi", "lady doctor gynae", "bachay ko tez bukhar hai"];
    const tiles = [
      ["#/hospitals", "🛏️", "c2", L_("Hospital bed", "ہسپتال بستر"), L_("Free beds by department", "شعبہ وار خالی بستر")],
      ["#/ambulance", "🚑", "c1", L_("Ambulance", "ایمبولینس"), L_("1122 · Edhi · alert hospital", "1122 · ایدھی · اطلاع")],
      ["#/medicine", "💊", "c3", L_("Medicine", "دوا"), L_("Stock, uses, prescription scan", "اسٹاک، استعمال، نسخہ")],
      ["#/blood", "🩸", "c6", L_("Blood", "خون"), L_("Units + WhatsApp donor call", "یونٹس + واٹس ایپ")],
      ["#/equipment", "🩻", "c5", L_("CT / MRI / Dialysis", "سی ٹی / ایم آر آئی"), L_("Which machine is working", "کون سی مشین چالو ہے")],
      ["#/hospitals?female=1&dept=Gynae/Obstetrics", "👩‍⚕️", "c4", L_("Lady doctor", "لیڈی ڈاکٹر"), L_("Female doctor on duty", "ڈیوٹی پر لیڈی ڈاکٹر")],
      ["#/dashboard", "🗺️", "c7", L_("City dashboard", "شہر ڈیش بورڈ"), L_("Live capacity map", "لائیو نقشہ")],
      ["#/staff", "🧑‍⚕️", "c8", L_("I'm hospital staff", "میں اسٹاف ہوں"), L_("Report in one message", "ایک پیغام میں رپورٹ")],
    ];
    $app.innerHTML = `
    <div class="hero2">
      <section class="hero">
        <div class="badge"><span class="pulse"></span> ${L_("Live in Lahore", "لاہور میں لائیو")}</div>
        <h1 class="big1">${L_("Know <em>before</em> you go.", "جانے <em>سے پہلے</em> جانیں۔")}</h1>
        <p>${L_("Free bed? Doctor on duty? CT working? Your medicine? O-negative blood? One question in Urdu or English, answered across Lahore's hospitals, pharmacies and blood banks.", "خالی بستر؟ ڈیوٹی ڈاکٹر؟ سی ٹی چالو؟ دوا؟ او نیگیٹو خون؟ اردو یا انگریزی میں ایک سوال، پورے لاہور سے جواب۔")}</p>
        <form class="ask" id="askForm"><input id="q" autocomplete="off" maxlength="300" placeholder="${L_("What do you need? e.g. abbu ko seenay mein dard", "آپ کو کیا چاہیے؟")}" aria-label="What do you need"><button type="button" class="mic" id="mic" title="Speak" aria-label="Speak">🎤</button><button class="go">${L_("Find", "تلاش")}</button></form>
        <div class="examples">${ex.map((e) => `<button type="button" data-ex="${esc(e)}">${esc(e)}</button>`).join("")}</div>
        ${locationRow(false)}
      </section>
      <aside class="live">
        <h3><span class="pulse"></span> ${L_("Latest reports across Lahore", "لاہور بھر سے تازہ رپورٹس")} ${state.demo ? demoPill() : ""}</h3>
        <ul class="feed" id="feed">${'<li><div class="skel" style="height:34px;width:100%;margin:0"></div></li>'.repeat(5)}</ul>
        <a class="btn sm" href="#/dashboard" style="margin-top:10px">🗺️ ${L_("Open city dashboard", "شہر ڈیش بورڈ کھولیں")} →</a>
      </aside>
    </div>
    <div class="scene">${(window.HAAZIR_ART || {}).scene || ""}</div>
    <div class="emstrip"><div class="grow">🚨 ${L_("Emergency? Don't wait. Call now.", "ایمرجنسی؟ انتظار نہ کریں، ابھی کال کریں۔")}</div>
      <a href="tel:1122">📞 Rescue 1122</a><a href="tel:115" class="ghost">📞 Edhi 115</a><a href="#/ask?q=${encodeURIComponent("emergency")}" class="ghost">${L_("Nearest emergency →", "قریب ترین ایمرجنسی →")}</a></div>
    <div class="tiles2">${tiles.map(([h, i, c, t, s]) => `<a class="tile2" href="${h}"><span class="ic ${c}">${i}</span><b>${t}</b><span class="s">${s}</span></a>`).join("")}</div>
    <div class="bigstats" id="bigStats">${'<div class="stat skel" style="height:96px"></div>'.repeat(5)}</div>
    <div class="sec"><h2>${L_("Everything you need, in one place", "سب کچھ ایک جگہ")}</h2><p class="lead">${L_("Real hospitals, pharmacies and blood banks across Lahore, plus the ambulance helplines.", "لاہور کے اصل ہسپتال، فارمیسیاں، بلڈ بینک اور ایمبولینس ہیلپ لائنز۔")}</p>
      <div class="showcase">${[["#/hospitals", "hospital", L_("19 hospitals", "19 ہسپتال"), L_("10 government (free) · 9 private", "10 سرکاری · 9 پرائیویٹ")], ["#/medicine", "pharmacy", L_("71 pharmacies", "71 فارمیسیاں"), L_("Stock, uses, prescription info", "اسٹاک، استعمال، نسخہ")], ["#/blood", "bloodbank", L_("6 blood banks", "6 بلڈ بینک"), L_("Units by blood group", "بلڈ گروپ کے مطابق")], ["#/ambulance", "ambulance", L_("Ambulance", "ایمبولینس"), "Rescue 1122 · Edhi 115"]].map(([h, a, t, s]) => `<a class="showcard" href="${h}"><div class="art">${(window.HAAZIR_ART || {})[a] || ""}</div><b>${t}</b><span>${s}</span></a>`).join("")}</div></div>
    <div class="sec"><h2>${L_("Every facility on one map", "ہر ادارہ ایک نقشے پر")}</h2><p class="lead">${L_("Real hospitals, pharmacies and blood banks, coloured by reported capacity.", "اصل ہسپتال، فارمیسیاں اور بلڈ بینک، رپورٹ شدہ گنجائش کے رنگ میں۔")}</p>
      <div class="legend"><span><span class="dot" style="background:#138a4a"></span> ${L_("beds free", "بستر خالی")}</span><span><span class="dot" style="background:#b26a00"></span> ${L_("few beds", "کم بستر")}</span><span><span class="dot" style="background:#c62828"></span> ${L_("full", "بھرا")}</span><span><span class="dot" style="background:#8a96a0"></span> ${L_("not reported", "رپورٹ نہیں")}</span><span><span class="dot" style="background:#7b5cd6"></span> ${L_("blood bank", "بلڈ بینک")}</span><span><span class="dot" style="background:#1e66f5"></span> ${L_("pharmacy", "فارمیسی")}</span></div>
      <div class="map" id="homeMap"></div></div>
    <div class="sec"><h2>${L_("How Haazir works", "حاضر کیسے کام کرتا ہے")}</h2><p class="lead">${L_("The information already exists in the heads of ward staff, pharmacists and blood bank clerks. Haazir connects it to families.", "معلومات اسٹاف کے پاس موجود ہے؛ حاضر اسے خاندانوں تک پہنچاتا ہے۔")}</p>
      <div class="flow">
        <div class="card"><span class="num">1</span><div class="art sm">${(window.HAAZIR_ART || {}).phone || ""}</div><h3>${L_("Staff send one line", "اسٹاف ایک لائن بھیجے")}</h3><div class="small muted">${L_("In Roman Urdu, the way they'd text on WhatsApp. AI on Amazon Bedrock turns it into updates they confirm.", "رومن اردو میں، جیسے واٹس ایپ پر۔ AI اسے اپ ڈیٹس میں بدلتا ہے۔")}</div><div class="eg">Medicine ward mein 2 bed khali, CT kharab hai</div></div>
        <div class="card"><span class="num">2</span><div class="art sm">${(window.HAAZIR_ART || {}).search || ""}</div><h3>${L_("Families ask", "خاندان پوچھیں")}</h3><div class="small muted">${L_("Typed or spoken, Urdu or English. Danger signs show 1122 and Edhi first.", "لکھ کر یا بول کر۔ خطرے کی علامت پر پہلے 1122۔")}</div><div class="eg">abbu ko seenay mein dard</div></div>
        <div class="card"><span class="num">3</span><div class="art sm">${(window.HAAZIR_ART || {}).pin || ""}</div><h3>${L_("Go to the right place", "صحیح جگہ جائیں")}</h3><div class="small muted">${L_("Ranked hospitals with a 'why', directions, and an alert so the ER knows you're coming.", "درجہ بندی، راستہ، اور ہسپتال کو پیشگی اطلاع۔")}</div><div class="eg">★ PIC · 4 Cardiology beds · 7 min</div></div>
      </div></div>
    <div class="sec"><h2>${L_("Why you can trust it", "اس پر بھروسہ کیوں")}</h2>
    <div class="card small">
      📍 ${L_("Real places: 19 Lahore hospitals (10 government, 9 private), pharmacies from OpenStreetMap, and known blood banks.", "اصل مقامات: 19 ہسپتال، اوپن اسٹریٹ میپ کی فارمیسیاں، معروف بلڈ بینک۔")}<br>
      🧪 ${L_("This pilot shows sample availability numbers (tagged 'sample') until hospitals start reporting. Real staff reports replace them instantly.", "یہ پائلٹ نمونہ نمبر دکھاتا ہے (نمونہ لیبل)، اسٹاف کی اصل رپورٹ فوراً ان کی جگہ لیتی ہے۔")}<br>
      🕒 ${L_("Every report shows when it was made; older than 2 hours is greyed out.", "ہر رپورٹ کا وقت درج ہے۔")}<br>
      🧮 ${L_("AI only understands language. A simple, explainable formula ranks hospitals.", "AI صرف زبان سمجھتا ہے؛ درجہ بندی سادہ فارمولا کرتا ہے۔")}<br>
      🚨 ${L_("Danger signs always show Rescue 1122 and Edhi 115 first. Haazir never diagnoses.", "خطرے کی علامات پر ہمیشہ پہلے 1122 اور 115۔")}
    </div></div>`;
    const form = document.getElementById("askForm"), q = document.getElementById("q");
    const submit = () => (form.requestSubmit ? form.requestSubmit() : form.onsubmit(new Event("submit")));
    form.onsubmit = (e) => { e.preventDefault(); if (q.value.trim()) location.hash = "#/ask?q=" + encodeURIComponent(q.value.trim()); };
    $app.querySelectorAll("[data-ex]").forEach((b) => b.onclick = () => { q.value = b.dataset.ex; submit(); });
    bindMic(document.getElementById("mic"), q, submit);
    bindLocation();

    const countUp = (el, to) => {
      const n = Number(to); if (!isFinite(n)) { el.textContent = to; return; }
      const t0 = performance.now(), dur = 900;
      const step = (t) => { const k = Math.min(1, (t - t0) / dur); el.textContent = Math.round(n * (1 - Math.pow(1 - k, 3))); if (k < 1) requestAnimationFrame(step); };
      requestAnimationFrame(step);
    };
    const icon = { bed: "🛏️", equipment: "🩻", blood: "🩸" };
    const m = makeMap(document.getElementById("homeMap"), [31.50, 74.31], 11);
    let first = true;
    async function load() {
      try {
        const [s, mp] = await Promise.all([api("/stats"), first ? api("/map") : Promise.resolve(null)]);
        const feed = document.getElementById("feed");
        if (!feed) return;
        feed.innerHTML = (s.recentReports || []).slice(0, 6).map((r) => `<li><span class="fi">${icon[r.kind] || "📋"}</span><div><b>${esc(r.facility)}</b><div class="t">${esc(r.text)} · ${ago(r.at)}</div></div></li>`).join("")
          || `<li class="muted small">${L_("No reports yet. Staff can report from the Staff portal.", "ابھی کوئی رپورٹ نہیں۔")}</li>`;
        if (first) {
          const st = document.getElementById("bigStats");
          const items = [[s.hospitals, L_("real hospitals", "اصل ہسپتال")], [s.pharmacies, L_("pharmacies mapped", "فارمیسیاں")], [s.bloodBanks, L_("blood banks", "بلڈ بینک")], [s.reportedFreeBeds, L_("free beds reported", "رپورٹ شدہ خالی بستر")], [s.hospitalsReporting, L_("hospitals reporting", "رپورٹ کرنے والے ہسپتال")]];
          st.innerHTML = items.map(([b, t]) => `<div class="stat"><b data-n="${esc(b)}">0</b><span>${t}</span></div>`).join("");
          st.querySelectorAll("[data-n]").forEach((el) => countUp(el, el.dataset.n));
          if (m && mp) {
            mp.facilities.forEach((f) => {
              if (f.type === "hospital") {
                const col = !f.reported ? "#8a96a0" : f.reportedFreeBeds === 0 ? "#c62828" : f.reportedFreeBeds <= 3 ? "#b26a00" : "#138a4a";
                window.L.circleMarker([f.lat, f.lon], { radius: 9, weight: 2, color: "#fff", fillColor: col, fillOpacity: .95 }).addTo(m).bindPopup(`<b>${esc(f.name)}</b><br><a href="#/facility/${f.id}">${L_("Details", "تفصیل")}</a>`);
              } else window.L.circleMarker([f.lat, f.lon], { radius: f.type === "bloodbank" ? 6 : 3, color: f.type === "bloodbank" ? "#7b5cd6" : "#1e66f5", fillOpacity: .8 }).addTo(m).bindPopup(esc(f.name));
            });
          }
          first = false;
        }
      } catch (e) { const feed = document.getElementById("feed"); if (feed) feed.innerHTML = `<li>${errBox(e)}</li>`; }
    }
    await load();
    every(load, 15000);
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
      const best = d.hospitals && d.hospitals[0];
      let html = "";
      if (e.redFlag || d.intent === "ambulance") html += redBanner(e.redFlagReason, best);
      html += `<div class="note">🧠 ${esc(reason || "")} <span class="pill o">${d.understoodBy === "ai" ? L_("understood by AI", "AI نے سمجھا") : L_("keyword match", "الفاظ سے")}</span>
        ${e.department ? `<span class="pill x">${esc(dept(e.department))}</span>` : ""}${e.urgency && e.urgency !== "routine" ? `<span class="pill r">${esc(e.urgency)}</span>` : ""}
        <button class="btn sm" id="say" style="margin-inline-start:6px">🔊</button></div>`;
      if (d.minutesSaved) html += `<div class="note">⏱️ ${L_("The nearest hospital's staff report no free beds, so a better option is shown first. That can save a wasted trip.", "قریبی ہسپتال نے بستر نہ ہونے کی رپورٹ دی ہے، اس لیے بہتر آپشن پہلے دکھایا۔")}</div>`;
      if (d.hospitals && d.hospitals.length) {
        if (!d.hospitals.some((h) => h.hasReports)) html += `<div class="note warn small">ℹ️ ${L_("None of these hospitals have reported live availability yet, so they are sorted by distance and department. Call ahead or go to the nearest emergency.", "ان ہسپتالوں نے ابھی دستیابی رپورٹ نہیں کی، اس لیے فاصلے کے مطابق ترتیب دی گئی ہے۔")}</div>`;
        html += `<div class="chips"><a class="chip" href="#/hospitals?dept=${encodeURIComponent(e.department || "Emergency")}&type=government">🏛️ ${L_("Government only", "صرف سرکاری")}</a><a class="chip" href="#/hospitals?dept=${encodeURIComponent(e.department || "Emergency")}&type=private">💳 ${L_("Private only", "صرف پرائیویٹ")}</a><a class="chip" href="#/hospitals?dept=${encodeURIComponent(e.department || "Emergency")}&female=1">♀ ${L_("Female doctor", "لیڈی ڈاکٹر")}</a></div>`;
        html += d.hospitals.map((h, i) => hospitalCard(h, i)).join("");
      } else if (d.hospitals) html += `<div class="empty">${L_("No matching hospital found.", "کوئی ہسپتال نہیں ملا۔")}</div>`;
      res.innerHTML = html + (d.medicine ? '<div id="medRes"></div>' : "") + (d.blood ? '<div id="bloodRes"></div>' : "") + (d.equipment ? '<div id="eqRes"></div>' : "");
      if (d.medicine) renderMedicine(document.getElementById("medRes"), d.medicine);
      if (d.blood) renderBlood(document.getElementById("bloodRes"), d.blood);
      if (d.equipment) renderEquipment(document.getElementById("eqRes"), d.equipment);
      const say = document.getElementById("say"); if (say) say.onclick = () => speak(reason || "");
      bindActions(res);
    } catch (err) { res.innerHTML = errBox(err); }
  }

  async function hospitalsPage(params) {
    const sel = { dept: params.get("dept") || "Emergency", female: params.get("female") === "1", type: params.get("type") || "" };
    $app.innerHTML = `<h1>🛏️ ${L_("Hospitals near you", "آپ کے قریب ہسپتال")}</h1>${locationRow(true)}
      <div class="chips">${DEPTS.map((d) => `<button class="chip ${d === sel.dept ? "on" : ""}" data-d="${d}">${esc(dept(d))}</button>`).join("")}</div>
      <div class="chips">${[["", L_("All hospitals", "تمام")], ["government", "🏛️ " + L_("Government (free)", "سرکاری (مفت)")], ["private", "💳 " + L_("Private (fees)", "پرائیویٹ (فیس)")]].map(([v, l]) => `<button class="chip ${sel.type === v ? "on" : ""}" data-own="${v}">${l}</button>`).join("")}
        <button class="chip ${sel.female ? "on" : ""}" id="fFem">♀ ${L_("Female doctor reported", "لیڈی ڈاکٹر")}</button></div>
      <div id="res">${skeleton(3)}</div>`;
    const go = () => { location.hash = `#/hospitals?dept=${encodeURIComponent(sel.dept)}${sel.female ? "&female=1" : ""}${sel.type ? "&type=" + sel.type : ""}`; };
    $app.querySelectorAll("[data-d]").forEach((b) => b.onclick = () => { sel.dept = b.dataset.d; go(); });
    $app.querySelectorAll("[data-own]").forEach((b) => b.onclick = () => { sel.type = b.dataset.own; go(); });
    document.getElementById("fFem").onclick = () => { sel.female = !sel.female; go(); };
    bindLocation(() => hospitalsPage(params));
    const res = document.getElementById("res");
    try {
      const d = await api(`/hospitals?${locQ()}&dept=${encodeURIComponent(sel.dept)}${sel.female ? "&female=1" : ""}${sel.type ? "&type=" + sel.type : ""}`);
      let list = d.hospitals;
      if (sel.female) list = list.filter((h) => h.femaleDoctor);
      res.innerHTML = list.length ? list.map((h, i) => hospitalCard(h, i)).join("")
        : `<div class="empty">${sel.female ? L_("No hospital has reported a female doctor on duty in this department yet.", "ابھی کسی ہسپتال نے لیڈی ڈاکٹر کی رپورٹ نہیں دی۔") : L_("No hospital matches these filters.", "کوئی ہسپتال نہیں ملا۔")}</div>`;
      bindActions(res);
    } catch (e) { res.innerHTML = errBox(e); }
  }

  async function facilityPage(id) {
    $app.innerHTML = skeleton(4);
    try {
      const f = await api(`/facility/${encodeURIComponent(id)}?${locQ()}`);
      const approx = f.locationPrecision === "area" ? ` <span class="pill a">${L_("approximate location", "اندازاً مقام")}</span>` : "";
      let html = `<a href="javascript:history.back()" class="small">← ${L_("Back", "واپس")}</a><h1>${esc(state.lang === "ur" && f.nameUr ? f.nameUr : f.name)}</h1>
        <div class="pills">${f.type === "hospital" ? ownPill(f.ownership) : ""}${loadPill(f.erLoad || "Unknown")}${approx}${f.demo ? demoPill() : ""}<span class="pill x">${f.distanceKm} km${f.etaMin ? " · ~" + f.etaMin + " min" : ""}</span></div>
        <div class="small muted">${L_("Name and location source:", "نام اور مقام کا ذریعہ:")} ${esc(f.source || "")}</div>
        <div class="btns"><a class="btn p" target="_blank" rel="noopener" href="${dirUrl(f.lat, f.lon)}">🧭 ${L_("Directions", "راستہ")}</a>${f.type === "hospital" ? `<button class="btn" data-notify="${f.id}" data-dept="Emergency" data-name="${esc(f.name)}" data-eta="${f.etaMin}">🔔 ${L_("Tell hospital you're coming", "اطلاع دیں")}</button>` : ""}</div>`;
      if (f.type === "hospital") {
        html += `<h2>${L_("Beds by department", "شعبہ وار بستر")}</h2><div class="card"><table class="t"><tr><th>${L_("Department", "شعبہ")}</th><th>${L_("Free beds", "خالی بستر")}</th><th>${L_("Reported", "رپورٹ")}</th></tr>` +
          (f.departments || []).map((k) => { const b = f.beds[k]; return `<tr class="${b && b.stale ? "stale" : ""}"><td>${esc(dept(k))}</td><td>${b ? `<span class="pill ${bedClass(b.free)}">${b.free}</span>` : `<span class="pill x">${NR()}</span>`}</td><td class="small muted">${b ? ago(b.updatedAt) + staleNote(b.updatedAt) : ""}</td></tr>`; }).join("") + "</table></div>";
        html += `<h2>${L_("Doctors reported on duty", "ڈیوٹی پر ڈاکٹر (رپورٹ)")}</h2><div class="card">` + (f.doctors.length ? `<table class="t">` + f.doctors.map((d) => `<tr><td>${esc(d.name)} ${d.gender === "F" ? "♀" : ""}</td><td>${esc(dept(d.dept || ""))}</td><td>${d.onDuty ? `<span class="pill g">${L_("on duty", "ڈیوٹی پر")}${d.shiftEnds ? " → " + d.shiftEnds : ""}</span>` : `<span class="pill x">${L_("off", "آف")}</span>`}</td><td class="small muted">${ago(d.updatedAt)}</td></tr>`).join("") + "</table>" : `<div class="muted small">${NR()}</div>`) + "</div>";
        html += `<h2>${L_("Machines", "مشینیں")}</h2><div class="card pills">` + EQUIP.map((k) => eqPill(k, f.equipment[k])).join(" ") + "</div>";
      }
      if (f.type === "pharmacy") {
        html += `<h2>${L_("Medicine stock reported", "رپورٹ شدہ دوائیں")}</h2><div class="card">` + (f.medicine.length ? `<table class="t">` + f.medicine.map((m) => `<tr class="${nowS() - m.updatedAt > 7200 ? "stale" : ""}"><td>${esc(m.name)}</td><td>${m.qty > 0 ? `<span class="pill g">${m.qty}</span>` : `<span class="pill r">${L_("out", "ختم")}</span>`}</td><td>${m.priceRs ? "Rs " + m.priceRs : ""}</td><td class="small muted">${ago(m.updatedAt)}</td></tr>`).join("") + "</table>" : `<div class="muted small">${L_("This pharmacy hasn't reported stock yet.", "اس فارمیسی نے ابھی اسٹاک رپورٹ نہیں کیا۔")}</div>`) + "</div>";
      }
      if (f.type === "bloodbank") {
        html += `<h2>${L_("Blood units reported", "رپورٹ شدہ خون")}</h2><div class="card pills">` + GROUPS.map((g) => { const b = f.blood[g]; return b ? `<span class="pill ${b.units === 0 ? "r" : b.units < 3 ? "a" : "g"}">${g}: ${b.units}</span>` : `<span class="pill x">${g}: ${NR()}</span>`; }).join("") + "</div>";
      }
      if (f.recentUpdates && f.recentUpdates.length) html += `<h2>${L_("Recent reports", "حالیہ رپورٹس")}</h2><div class="card small">` + f.recentUpdates.map((u) => `<div>${esc(u.what)} · <span class="muted">${esc(u.by || "")}, ${ago(u.at)}</span></div>`).join("") + "</div>";
      $app.innerHTML = html;
      bindActions($app);
    } catch (e) { $app.innerHTML = errBox(e); }
  }

  // ---- ambulance: real helplines + alert the hospital
  async function ambulancePage() {
    $app.innerHTML = `<h1>🚑 ${L_("Ambulance", "ایمبولینس")}</h1>
      <div class="alert-red"><h2>📞 ${L_("Call an ambulance service", "ایمبولینس سروس کو کال کریں")}</h2>
        <div class="btns">${helplineBtns(true)}</div>
        <div class="small" style="margin-top:8px;opacity:.9">${L_("Haazir does not dispatch ambulances. These are the real public helplines.", "حاضر ایمبولینس نہیں بھیجتا۔ یہ اصل ہیلپ لائنز ہیں۔")}</div></div>
      <div class="card"><h3>🔔 ${L_("Then tell the hospital you're coming", "پھر ہسپتال کو بتائیں کہ آپ آ رہے ہیں")}</h3>
        <p class="small muted">${L_("Nearest hospitals with an emergency department. Tap 'Tell hospital' so the emergency team sees you coming in its staff portal.", "قریب ترین ایمرجنسی والے ہسپتال۔")}</p>${locationRow(true)}</div>
      <div id="res">${skeleton(2)}</div>`;
    bindLocation(() => ambulancePage());
    const res = document.getElementById("res");
    try {
      const d = await api(`/hospitals?${locQ()}&dept=Emergency`);
      res.innerHTML = d.hospitals.slice(0, 5).map((h, i) => hospitalCard(h, i)).join("");
      res.querySelectorAll("[data-notify]").forEach((b) => { b.dataset.amb = "1"; });
      bindActions(res);
    } catch (e) { res.innerHTML = errBox(e); }
  }

  // ---- medicine
  function medicinePage(params) {
    $app.innerHTML = `<h1>💊 ${L_("Find a medicine", "دوا تلاش کریں")}</h1>${locationRow(true)}
      <form class="field" id="mf"><input id="mq" maxlength="80" placeholder="${L_("Medicine name, e.g. Augmentin 625", "دوا کا نام")}" value="${esc(params.get("q") || "")}"><button class="btn p">${L_("Search", "تلاش")}</button></form>
      <div class="card"><h3>📷 ${L_("Scan a prescription", "نسخہ اسکین کریں")}</h3><p class="small muted">${L_("Take a photo. AI reads the medicine names, you confirm them, and Haazir looks for one pharmacy that has reported having everything.", "تصویر لیں؛ AI نام پڑھے گا، آپ تصدیق کریں۔")}</p>
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
    out.innerHTML = (keepMsg ? out.innerHTML : "") + `<div class="note">✏️ ${L_("Check the list. Edit anything that's wrong.", "فہرست چیک کریں اور غلطی درست کریں۔")}</div><div id="rxRows">${meds.map(rowH).join("")}</div>
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
    if (p.onePharmacy) html += `<div class="note">✅ <b>${L_("One pharmacy has reported having everything:", "ایک فارمیسی میں سب کچھ:")}</b> ${esc(p.stops[0].name)} (${p.stops[0].distanceKm} km)</div>`;
    else if (p.stops.length) html += `<div class="note warn">${L_(`No single pharmacy has reported everything. Fewest stops: ${p.stops.length}`, `کسی ایک فارمیسی میں سب کچھ نہیں؛ ${p.stops.length} جگہیں`)}</div>`;
    else html += `<div class="note warn">${L_("No pharmacy has reported stock of these medicines yet. Try the nearest pharmacies or ask your hospital dispensary.", "ابھی کسی فارمیسی نے یہ دوائیں رپورٹ نہیں کیں۔")}</div>`;
    html += p.stops.map((s) => `<div class="card"><h3>🏪 ${esc(s.name)}</h3><div class="small muted">${s.distanceKm} km · ~${s.etaMin} min</div><table class="t">${Object.values(s.have).map((h) => `<tr><td>${esc(h.name)} ${h.substitute ? `<span class="pill a">${L_("same-salt substitute", "متبادل")}</span>` : ""}</td><td>${h.priceRs ? "Rs " + h.priceRs : ""}</td></tr>`).join("")}</table><div class="btns"><a class="btn p sm" target="_blank" rel="noopener" href="${dirUrl(s.lat, s.lon)}">🧭 ${L_("Directions", "راستہ")}</a></div></div>`).join("");
    if (p.missing.length && p.stops.length) html += `<div class="note warn">${L_("Not found:", "نہیں ملی:")} ${p.missing.map((m) => esc(m.asked)).join(", ")}</div>`;
    if (p.totalRs) html += `<div class="card"><b>${L_("Total (reported prices)", "کل (رپورٹ شدہ قیمت)")}: Rs ${p.totalRs}</b></div>`;
    html += `<div class="note warn small">⚠️ ${L_("Confirm with your doctor or pharmacist before switching.", "تبدیل کرنے سے پہلے ڈاکٹر یا فارماسسٹ سے تصدیق کریں۔")}</div>`;
    el.innerHTML = html;
  }

  function renderMedicine(el, d) {
    if (!d.matched || !d.matched.length) { el.innerHTML = `<div class="empty">${L_("We couldn't match that medicine name. Try the brand name printed on the box.", "دوا کا نام نہیں ملا۔ ڈبے پر لکھا نام آزمائیں۔")}</div>`; return; }
    const m = d.matched[0];
    const RX = { rx: ["rx", "📝 " + L_("Prescription needed: ask your doctor", "ڈاکٹر کا نسخہ ضروری ہے")], otc: ["otc", "✅ " + L_("Usually sold without a prescription", "عام طور پر نسخے کے بغیر ملتی ہے")], ask: ["ask", "💬 " + L_("Ask your pharmacist or doctor", "فارماسسٹ یا ڈاکٹر سے پوچھیں")] }[m.rx || "ask"];
    let html = `<div class="card"><h3>💊 ${esc(m.name)}</h3><div class="small muted">${L_("Active ingredient", "جزو")}: ${esc(m.salt)} ${esc(m.strength)}</div>
      <div class="medinfo">${m.use ? `<div class="use"><b>${L_("Used for", "استعمال")}:</b> ${esc(state.lang === "ur" && m.useUr ? m.useUr : m.use)}</div>` : ""}
      <div><span class="rxb ${RX[0]}">${RX[1]}</span></div>
      <div class="small muted">${L_("General information, not medical advice. Always take medicines as your doctor prescribed.", "یہ عمومی معلومات ہیں، طبی مشورہ نہیں۔ دوا ہمیشہ ڈاکٹر کے نسخے کے مطابق لیں۔")}</div></div>`;
    if (d.alternatives.length) html += `<div class="small" style="margin-top:8px"><b>${L_("Same active ingredient and strength", "اسی جزو اور طاقت کی دوائیں")}:</b> ${d.alternatives.map((a) => esc(a.name)).join(" · ")}</div><div class="small muted">${L_("Generic versions are usually cheaper.", "جنرک عموماً سستی ہوتی ہے۔")}</div><div class="small" style="color:var(--warn)">⚠️ ${L_("Confirm with your doctor or pharmacist before switching.", "تبدیل کرنے سے پہلے ڈاکٹر یا فارماسسٹ سے تصدیق کریں۔")}</div>`;
    html += `</div><div class="map" id="medMap"></div>`;
    if (d.pharmacies.length) html += `<h2>🏪 ${L_("Pharmacies that reported stock", "جن فارمیسیوں نے اسٹاک رپورٹ کیا")}</h2>` + d.pharmacies.map(stockCard).join("");
    else html += `<div class="note warn">ℹ️ ${L_(`No pharmacy has reported stock of this medicine yet (${d.reportingPharmacies} pharmacies reporting so far). Nearest real pharmacies:`, "ابھی کسی فارمیسی نے یہ دوا رپورٹ نہیں کی۔ قریب ترین فارمیسیاں:")}</div>` +
      (d.nearbyPharmacies || []).map((p) => `<div class="card"><div class="row"><div class="grow"><h3>${esc(p.name)}</h3><div class="small muted">${p.distanceKm} km · ${L_("stock not reported", "اسٹاک رپورٹ نہیں")}</div></div><a class="btn p sm" target="_blank" rel="noopener" href="${dirUrl(p.lat, p.lon)}">🧭 ${L_("Directions", "راستہ")}</a></div></div>`).join("");
    el.innerHTML = html;
    const mp = makeMap(document.getElementById("medMap"), [state.loc.lat, state.loc.lon], 13);
    if (mp) {
      youMarker(mp);
      (d.pharmacies.length ? d.pharmacies : d.nearbyPharmacies || []).forEach((p) => window.L.circleMarker([p.lat, p.lon], { radius: 8, color: p.hasExact ? "#138a4a" : p.stock ? "#b26a00" : "#8a96a0", fillOpacity: .8 }).addTo(mp).bindPopup(esc(p.name)));
    }
  }
  function stockCard(p) {
    return `<div class="card"><div class="row"><div class="grow"><h3>${esc(p.name)}</h3><div class="small muted">${p.distanceKm} km · ~${p.etaMin} min</div>
      <div class="pills">${p.stock.map((s) => `<span class="pill ${s.exact ? "g" : "a"} ${s.stale ? "stale" : ""}">${esc(s.name)} · ${s.qty} ${L_("in stock", "موجود")}${s.priceRs ? " · Rs " + s.priceRs : ""}</span>`).join("")}${p.stock.some((s) => s.demo) ? demoPill() : ""}</div>
      <div class="small muted">${L_("reported", "رپورٹ")} ${ago(Math.max(...p.stock.map((s) => s.updatedAt || 0)))}</div></div></div>
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
  function renderBlood(el, d) {
    let html = `<div class="note small">ℹ️ ${L_(`A patient needing ${d.group} can usually receive: ${d.compatibleGroups.join(", ")}.`, `${d.group} کے مریض کو عام طور پر یہ گروپ لگ سکتے ہیں: ${d.compatibleGroups.join("، ")}`)} ${esc(d.compatNote)}</div>`;
    if (!d.banks.some((b) => b.reported)) html += `<div class="note warn small">ℹ️ ${L_("These are real blood banks, but none has reported units yet. Please call them, or share a donor request below.", "یہ اصل بلڈ بینک ہیں مگر ابھی کسی نے یونٹس رپورٹ نہیں کیے۔")}</div>`;
    html += d.banks.map((b, i) => `<div class="card ${i === 0 && b.enough ? "top1" : ""} ${b.stale ? "stale" : ""}"><div class="row"><div class="big ${b.exactUnits == null ? "x" : b.exactUnits >= d.units ? "g" : b.exactUnits > 0 ? "a" : "r"}">${b.exactUnits == null ? "?" : b.exactUnits}<small>${b.exactUnits == null ? L_("not<br>reported", "رپورٹ<br>نہیں") : esc(d.group) + " " + L_("units", "بوتلیں")}</small></div>
      <div class="grow"><h3>${esc(b.name)}</h3><div class="small muted">${b.distanceKm} km · ~${b.etaMin} min${b.updatedAt ? " · " + L_("reported", "رپورٹ") + " " + ago(b.updatedAt) + staleNote(b.updatedAt) : ""}</div>
      <div class="pills">${b.demo ? demoPill() : ""}${b.locationPrecision === "area" ? `<span class="pill a">${L_("approximate location", "اندازاً مقام")}</span>` : ""}${Object.entries(b.compatibleUnits).map(([g, u]) => `<span class="pill o">${L_("compatible", "موزوں")} ${g}: ${u}</span>`).join("")}</div></div></div>
      <div class="btns"><a class="btn p sm" target="_blank" rel="noopener" href="${dirUrl(b.lat, b.lon)}">🧭 ${L_("Directions", "راستہ")}</a></div></div>`).join("");
    html += `<div class="card"><h3>📣 ${L_("Ask donors on WhatsApp", "واٹس ایپ پر ڈونرز سے رابطہ")}</h3><p class="small muted">${L_("Creates a clear, ready-to-forward request in English and Urdu.", "انگریزی اور اردو میں واضح پیغام۔")}</p>
      <div class="field"><input id="bHosp" maxlength="80" placeholder="${L_("Hospital name, e.g. Mayo Hospital", "ہسپتال کا نام")}"><input id="bContact" maxlength="30" placeholder="${L_("Contact number (optional)", "رابطہ نمبر (اختیاری)")}"></div>
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
    $app.innerHTML = `<h1>🩻 ${L_("Where is it working?", "کہاں چالو ہے؟")}</h1>${locationRow(true)}
      <div class="chips">${EQUIP.map((x) => `<button class="chip ${x === t ? "on" : ""}" data-t="${x}">${x}</button>`).join("")}</div><div id="res">${skeleton(3)}</div>`;
    bindLocation(() => equipmentPage(params));
    $app.querySelectorAll("[data-t]").forEach((b) => b.onclick = () => { location.hash = "#/equipment?type=" + b.dataset.t; });
    const res = document.getElementById("res");
    api(`/equipment?type=${t}&${locQ()}`).then((d) => renderEquipment(res, d)).catch((e) => res.innerHTML = errBox(e));
  }
  function renderEquipment(el, d) {
    const anyReported = d.results.some((r) => r.status !== "unknown");
    el.innerHTML = `<h2>${esc(d.type)}</h2>` + (anyReported ? "" : `<div class="note warn small">ℹ️ ${L_(`No hospital has reported ${d.type} status yet. Nearest hospitals are listed; please call ahead.`, "ابھی کسی ہسپتال نے رپورٹ نہیں کیا؛ قریب ترین ہسپتال درج ہیں۔")}</div>`) +
      d.results.slice(0, 12).map((r, i) => `<div class="card ${i === 0 && r.status === "working" ? "top1" : ""} ${r.stale ? "stale" : ""}"><div class="row"><div class="grow"><h3>${esc(r.name)}</h3>
      <div class="pills">${ownPill(r.ownership)}${eqPill(d.type, r)}${r.demo ? demoPill() : ""}</div>
      <div class="small muted">${r.distanceKm} km · ~${r.etaMin} min${r.updatedAt ? " · " + L_("reported", "رپورٹ") + " " + ago(r.updatedAt) + staleNote(r.updatedAt) : ""}</div></div></div>
      <div class="btns"><a class="btn p sm" target="_blank" rel="noopener" href="${dirUrl(r.lat, r.lon)}">🧭 ${L_("Directions", "راستہ")}</a><a class="btn sm" href="#/facility/${r.id}">${L_("Details", "تفصیل")}</a></div></div>`).join("");
  }

  // ---- staff portal
  async function staffPage() {
    if (!state.staff) {
      $app.innerHTML = `<h1>🧑‍⚕️ ${L_("Staff portal", "اسٹاف پورٹل")}</h1><div class="card"><p class="small muted">${L_("Ward staff, pharmacists and blood bank clerks keep Haazir accurate. Everything families see comes from these reports.", "خاندان جو کچھ دیکھتے ہیں وہ انہی رپورٹس سے آتا ہے۔")}</p>
        <div class="field"><select id="sFac"><option>${L_("Loading…", "لوڈ ہو رہا ہے…")}</option></select></div>
        <div class="field"><input id="sPin" type="password" inputmode="numeric" maxlength="8" placeholder="PIN"></div>
        <div class="note small">${L_("Pilot PIN:", "پائلٹ PIN:")} <b>1234</b>. ${L_("In a real rollout each staff member gets a verified account.", "اصل نظام میں ہر اسٹاف کا تصدیق شدہ اکاؤنٹ ہوگا۔")}</div>
        <div class="btns"><button class="btn p" id="sGo">${L_("Open portal", "پورٹل کھولیں")}</button></div><div id="sOut"></div></div>`;
      try {
        const d = await api("/facilities");
        const groups = { hospital: L_("Hospitals", "ہسپتال"), pharmacy: L_("Pharmacies", "فارمیسیاں"), bloodbank: L_("Blood banks", "بلڈ بینک") };
        document.getElementById("sFac").innerHTML = Object.entries(groups).map(([t, lbl]) => `<optgroup label="${lbl}">${d.facilities.filter((f) => f.type === t).map((f) => `<option value="${f.id}" ${f.id === "hosp-mayo" ? "selected" : ""}>${esc(f.name)}</option>`).join("")}</optgroup>`).join("");
      } catch (e) { document.getElementById("sOut").innerHTML = errBox(e); }
      document.getElementById("sGo").onclick = async () => {
        const facilityId = document.getElementById("sFac").value, pin = document.getElementById("sPin").value;
        try { const r = await post("/staff/login", { facilityId, pin }); state.staff = { facilityId, pin, name: r.facility.name, type: r.facility.type, tab: "quick" }; staffPage(); }
        catch (e) { document.getElementById("sOut").innerHTML = errBox(e); }
      };
      return;
    }
    const s = state.staff;
    const tabs = s.type === "hospital" ? [["quick", "⚡ " + L_("Quick update", "فوری اپ ڈیٹ")], ["alerts", "🔔 " + L_("Alerts", "الرٹس")], ["beds", L_("Beds", "بستر")], ["doctors", L_("Doctors", "ڈاکٹر")], ["equipment", L_("Machines", "مشینیں")]]
      : s.type === "pharmacy" ? [["quick", "⚡ " + L_("Quick update", "فوری اپ ڈیٹ")], ["stock", L_("Stock", "اسٹاک")]] : [["quick", "⚡ " + L_("Quick update", "فوری اپ ڈیٹ")], ["blood", L_("Blood", "خون")]];
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
        body.innerHTML = `<div class="card">${(f.departments || []).map((k) => { const b = f.beds[k]; return `<div class="ctl"><div class="grow"><b>${esc(dept(k))}</b><div class="small muted">${b ? L_("reported", "رپورٹ") + " " + ago(b.updatedAt) : NR()}</div></div>
          ${b ? `<button data-bed="${esc(k)}" data-d="-1">−</button><span class="n">${b.free}</span><button data-bed="${esc(k)}" data-d="1">+</button>` : `<input type="number" min="0" max="500" class="btn sm" style="width:80px" data-bedset="${esc(k)}" placeholder="#"><button style="width:auto;padding:0 12px;font-size:14px" data-bedgo="${esc(k)}">${L_("Report", "رپورٹ")}</button>`}</div>`; }).join("")}
          <div class="small muted">${L_("Free beds right now. Tap + when a bed frees up and − when a patient is admitted.", "اس وقت خالی بستر۔")}</div></div>`;
        body.querySelectorAll("[data-bed]").forEach((b) => b.onclick = () => send([{ kind: "bed", key: b.dataset.bed, delta: +b.dataset.d }]));
        body.querySelectorAll("[data-bedgo]").forEach((b) => b.onclick = () => { const v = body.querySelector(`[data-bedset="${b.dataset.bedgo}"]`).value; if (v !== "") send([{ kind: "bed", key: b.dataset.bedgo, free: +v }]); });
      } else if (s.tab === "doctors") {
        body.innerHTML = `<div class="card"><h3>${L_("Add doctor on duty", "ڈیوٹی ڈاکٹر شامل کریں")}</h3>
          <div class="field"><input id="dName" maxlength="40" placeholder="${L_("Name, e.g. Dr Sana Khan", "نام")}"><select id="dDept">${(f.departments || []).map((d) => `<option value="${d}">${dept(d)}</option>`).join("")}</select></div>
          <div class="field"><select id="dGender"><option value="">${L_("Gender (optional)", "جنس")}</option><option value="F">${L_("Female", "خاتون")}</option><option value="M">${L_("Male", "مرد")}</option></select><input id="dUntil" type="time" value="20:00"><button class="btn p" id="dAdd">${L_("Report on duty", "رپورٹ کریں")}</button></div></div>
          <div class="card">${f.doctors.length ? f.doctors.map((d) => `<div class="ctl"><div class="grow"><b>${esc(d.name)}</b> ${d.gender === "F" ? "♀" : ""}<div class="small muted">${esc(dept(d.dept || ""))} · ${d.shiftEnds ? L_("until", "تک") + " " + esc(d.shiftEnds) : ""} · ${ago(d.updatedAt)}</div></div><button style="width:auto;padding:0 12px;font-size:14px" data-doc="${esc(d.key)}" data-name="${esc(d.name)}" data-on="${d.onDuty ? 0 : 1}">${d.onDuty ? "✅ " + L_("On duty", "ڈیوٹی پر") : "⏸ " + L_("Off", "آف")}</button></div>`).join("") : `<div class="muted small">${L_("No doctors reported yet.", "ابھی کوئی ڈاکٹر رپورٹ نہیں۔")}</div>`}</div>`;
        document.getElementById("dAdd").onclick = () => { const n = document.getElementById("dName").value.trim(); if (n) send([{ kind: "doctor", name: n, dept: document.getElementById("dDept").value, gender: document.getElementById("dGender").value || null, onDuty: true, shiftEnds: document.getElementById("dUntil").value || null }]); };
        body.querySelectorAll("[data-doc]").forEach((b) => b.onclick = () => send([{ kind: "doctor", key: b.dataset.doc, name: b.dataset.name, onDuty: b.dataset.on === "1" }]));
      } else if (s.tab === "equipment") {
        body.innerHTML = `<div class="card">${EQUIP.map((k) => { const e = f.equipment[k]; return `<div class="ctl"><div class="grow"><b>${k}</b><div class="small muted">${e ? L_("reported", "رپورٹ") + " " + ago(e.updatedAt) : NR()}</div></div><select data-eq="${k}" class="btn sm">${e ? "" : `<option selected disabled>${L_("choose…", "منتخب کریں…")}</option>`}${["working", "busy", "down"].map((st) => `<option ${e && st === e.status ? "selected" : ""} value="${st}">${st}</option>`).join("")}</select></div>`; }).join("")}</div>`;
        body.querySelectorAll("[data-eq]").forEach((sel) => sel.onchange = () => send([{ kind: "equipment", key: sel.dataset.eq, status: sel.value }]));
      } else if (s.tab === "stock") {
        body.innerHTML = `<div class="card"><h3>${L_("Report stock", "اسٹاک رپورٹ کریں")}</h3><p class="small muted">${L_("Fastest: use Quick update, e.g. 'Panadol khatam, Augmentin 20 packs aa gaye'.", "سب سے تیز: فوری اپ ڈیٹ استعمال کریں۔")}</p></div>
          <div class="card">${f.medicine.length ? f.medicine.map((m) => `<div class="ctl"><div class="grow"><b>${esc(m.name)}</b><div class="small muted">${m.priceRs ? "Rs " + m.priceRs + " · " : ""}${ago(m.updatedAt)}</div></div><button data-med="${esc(m.key)}" data-d="-5">−</button><span class="n">${m.qty}</span><button data-med="${esc(m.key)}" data-d="5">+</button><button data-med0="${esc(m.key)}" style="width:auto;padding:0 10px;font-size:13px">${L_("Out", "ختم")}</button></div>`).join("") : `<div class="muted small">${L_("No stock reported yet.", "ابھی کوئی اسٹاک رپورٹ نہیں۔")}</div>`}</div>`;
        body.querySelectorAll("[data-med]").forEach((b) => b.onclick = () => send([{ kind: "medicine", key: b.dataset.med, delta: +b.dataset.d }]));
        body.querySelectorAll("[data-med0]").forEach((b) => b.onclick = () => send([{ kind: "medicine", key: b.dataset.med0, qty: 0 }]));
      } else if (s.tab === "blood") {
        body.innerHTML = `<div class="card">${GROUPS.map((g) => { const b = f.blood[g]; return `<div class="ctl"><div class="grow"><b>${g}</b><div class="small muted">${b ? L_("reported", "رپورٹ") + " " + ago(b.updatedAt) : NR()}</div></div>${b ? `<button data-bl="${g}" data-d="-1">−</button><span class="n">${b.units}</span><button data-bl="${g}" data-d="1">+</button>` : `<input type="number" min="0" max="500" class="btn sm" style="width:80px" data-blset="${g}" placeholder="#"><button style="width:auto;padding:0 12px;font-size:14px" data-blgo="${g}">${L_("Report", "رپورٹ")}</button>`}</div>`; }).join("")}</div>`;
        body.querySelectorAll("[data-bl]").forEach((b) => b.onclick = () => send([{ kind: "blood", key: b.dataset.bl, delta: +b.dataset.d }]));
        body.querySelectorAll("[data-blgo]").forEach((b) => b.onclick = () => { const v = body.querySelector(`[data-blset="${b.dataset.blgo}"]`).value; if (v !== "") send([{ kind: "blood", key: b.dataset.blgo, units: +v }]); });
      }
    }
    async function renderQuick() {
      // Chat-style flow: type (or tap suggestions) -> Send update -> check what was understood -> Publish -> done
      let f = null;
      try { f = await api(`/facility/${s.facilityId}`); } catch (e) {}
      const depts = (f && f.departments) || ["Medicine"];
      const d0 = (depts.find((d) => d !== "Emergency") || "Emergency").split("/")[0];
      const chips = s.type === "pharmacy"
        ? ["Panadol khatam", "Augmentin 20 packs aa gaye", "Risek 10 packs aa gaye", "Brufen khatam"]
        : s.type === "bloodbank"
          ? ["O- 2 unit", "O+ 12 unit", "B+ 10 unit", "AB- 1 unit"]
          : [`${d0} ward mein 2 bed khali`, "Emergency mein 3 bed khali", `${d0} ward full`, "CT kharab hai", "CT theek ho gaya", "Dr Sana 8 baje tak duty pe"];
      body.innerHTML = `<div class="card">
        <h3>⚡ ${L_("What's the situation right now?", "اس وقت کیا صورتحال ہے؟")}</h3>
        <p class="small muted">${L_("Type one message the way you'd send it on WhatsApp, or tap the suggestions to build it. Only report what is true right now.", "واٹس ایپ کی طرح ایک پیغام لکھیں یا نیچے سے منتخب کریں۔ صرف وہی لکھیں جو اس وقت درست ہو۔")}</p>
        <div class="small" style="margin:6px 0 4px"><b>${L_("Tap to add:", "شامل کرنے کے لیے دبائیں:")}</b></div>
        <div class="chips" id="qChips">${chips.map((c) => `<button type="button" class="chip" data-chip="${esc(c)}">+ ${esc(c)}</button>`).join("")}</div>
        <textarea id="qText" maxlength="500" placeholder="${esc(chips.slice(0, 3).join(", "))}"></textarea>
        <div class="btns"><button class="btn p" id="qSend" style="min-width:180px">➤ ${L_("Send update", "اپ ڈیٹ بھیجیں")}</button><button class="btn" id="qClear">${L_("Clear", "صاف کریں")}</button></div>
        <div id="qOut"></div></div>
        <div class="card"><h3>🕒 ${L_("Your recent updates", "آپ کی حالیہ اپ ڈیٹس")}</h3><div id="qHist" class="small muted">…</div></div>`;
      const ta = document.getElementById("qText"), out = document.getElementById("qOut");
      body.querySelectorAll("[data-chip]").forEach((b) => b.onclick = () => { ta.value = (ta.value.trim() ? ta.value.trim().replace(/[,.]$/, "") + ", " : "") + b.dataset.chip; ta.focus(); });
      document.getElementById("qClear").onclick = () => { ta.value = ""; out.innerHTML = ""; };
      async function history() {
        const h = document.getElementById("qHist");
        try {
          const ff = await api(`/facility/${s.facilityId}`);
          const mine = (ff.recentUpdates || []).filter((u) => !u.demo);
          h.innerHTML = mine.length ? mine.map((u) => `<div>✅ ${esc(u.what)} · <span class="muted">${ago(u.at)}</span></div>`).join("") : L_("No updates from staff yet. Your first update will appear here.", "ابھی کوئی اپ ڈیٹ نہیں۔");
        } catch (e) { h.innerHTML = errBox(e); }
      }
      document.getElementById("qSend").onclick = async (ev) => {
        const text = ta.value.trim();
        if (!text) { out.innerHTML = `<div class="note warn">${L_("Type a message or tap a suggestion first.", "پہلے پیغام لکھیں یا کوئی تجویز دبائیں۔")}</div>`; return; }
        ev.target.disabled = true; out.innerHTML = `<div class="note">🧠 ${L_("Reading your message…", "پیغام پڑھا جا رہا ہے…")}</div>`;
        try {
          const r = await post("/staff/parse", { facilityId: s.facilityId, pin: s.pin, text });
          if (!r.changes.length) {
            out.innerHTML = `<div class="note warn">${L_("Couldn't understand that. Mention the ward (e.g. Medicine ward), the machine (CT, MRI, XRay…), the doctor (Dr Name) or the medicine, or tap a suggestion above.", "سمجھ نہیں آیا۔ وارڈ، مشین، ڈاکٹر یا دوا کا نام لکھیں۔")}</div>`;
          } else {
            out.innerHTML = `<div class="note" style="margin-top:12px"><b>${L_("Haazir understood:", "حاضر نے یہ سمجھا:")}</b> <span class="small muted">${L_("untick anything that's wrong", "غلط کو ہٹا دیں")}</span></div>` +
              r.changes.map((c, i) => `<label class="ctl"><span class="grow">${esc(c.label)}</span><input type="checkbox" checked data-i="${i}" style="width:24px;height:24px"></label>`).join("") +
              `<div class="btns"><button class="btn p" id="qPub" style="min-width:180px">✅ ${L_("Publish now", "ابھی شائع کریں")}</button><button class="btn" id="qEdit">✏️ ${L_("Edit message", "پیغام بدلیں")}</button></div>`;
            document.getElementById("qEdit").onclick = () => { out.innerHTML = ""; ta.focus(); };
            document.getElementById("qPub").onclick = async (e2) => {
              const chosen = r.changes.filter((c, i) => out.querySelector(`[data-i="${i}"]`).checked);
              if (!chosen.length) return;
              e2.target.disabled = true;
              try {
                const u = await post("/staff/update", { facilityId: s.facilityId, pin: s.pin, changes: chosen });
                out.innerHTML = `<div class="note" style="margin-top:12px">🎉 <b>${u.applied.length} ${L_("updates published.", "اپ ڈیٹس شائع ہو گئیں۔")}</b> ${L_("Families searching Haazir see them now.", "خاندان انہیں ابھی دیکھ سکتے ہیں۔")}</div>
                  <div class="btns"><button class="btn p" id="qAgain">➕ ${L_("Send another update", "ایک اور اپ ڈیٹ")}</button><a class="btn" href="#/facility/${s.facilityId}">👀 ${L_("See what families see", "خاندان کیا دیکھتے ہیں")}</a></div>`;
                document.getElementById("qAgain").onclick = () => { ta.value = ""; out.innerHTML = ""; ta.focus(); };
                history();
              } catch (e) { out.innerHTML = errBox(e); }
            };
          }
        } catch (e) { out.innerHTML = errBox(e); }
        ev.target.disabled = false;
      };
      history();
    }
    async function renderAlerts() {
      async function load() {
        try {
          const d = await post("/staff/alerts", { facilityId: s.facilityId, pin: s.pin });
          if (s.tab !== "alerts") return;
          body.innerHTML = d.alerts.length ? d.alerts.map((a) => `<div class="card ${a.ack ? "stale" : "top1"}"><div class="row"><div class="grow"><b>${a.source && a.source.startsWith("ambulance") ? "🚑" : "👪"} ${esc(dept(a.department))}</b> · <span class="small muted">${ago(a.createdAt)}${a.etaSec ? " · ETA ~" + Math.round(a.etaSec / 60) + " min" : ""} · ${L_("ref", "ریف")} ${esc(a.id)}</span><div>${esc(a.note)}</div></div>
            ${a.ack ? `<span class="pill g">${L_("acknowledged", "موصول")}</span>` : `<button class="btn p sm" data-ack="${esc(a.sk)}">${L_("Acknowledge", "موصول")}</button>`}</div></div>`).join("") : `<div class="empty">${L_("No incoming alerts. Families who tap 'Tell hospital you're coming' will show up here.", "کوئی الرٹ نہیں۔")}</div>`;
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
    $app.innerHTML = `<h1>🗺️ ${L_("Lahore health capacity", "لاہور صحت کی گنجائش")}</h1><p class="muted small">${L_("For the health department and emergency control rooms. Shows only what facilities have reported. Refreshes every 15 seconds.", "صرف رپورٹ شدہ معلومات۔ ہر 15 سیکنڈ میں تازہ۔")}</p>
      <div class="stats" id="dStats">${'<div class="stat skel" style="height:72px"></div>'.repeat(8)}</div>
      <div class="legend" style="margin-top:12px"><span><span class="dot" style="background:#138a4a"></span> ${L_("reported beds free", "بستر خالی")}</span><span><span class="dot" style="background:#b26a00"></span> ${L_("few beds", "کم بستر")}</span><span><span class="dot" style="background:#c62828"></span> ${L_("reported full", "بھرا")}</span><span><span class="dot" style="background:#8a96a0"></span> ${L_("not reported yet", "رپورٹ نہیں")}</span><span><span class="dot" style="background:#7b5cd6"></span> ${L_("blood bank", "بلڈ بینک")}</span><span><span class="dot" style="background:#1e66f5"></span> ${L_("pharmacy", "فارمیسی")}</span></div>
      <div class="map tall" id="dMap"></div><div class="grid2" id="dLists"></div>`;
    const m = makeMap(document.getElementById("dMap"), [31.50, 74.31], 11);
    const layers = m ? { hosp: window.L.layerGroup().addTo(m), bb: window.L.layerGroup().addTo(m), ph: window.L.layerGroup() } : null;
    if (m) window.L.control.layers(null, { [L_("Hospitals", "ہسپتال")]: layers.hosp, [L_("Blood banks", "بلڈ بینک")]: layers.bb, [L_("Pharmacies", "فارمیسیاں")]: layers.ph }).addTo(m);
    async function load() {
      try {
        const [s, mp] = await Promise.all([api("/stats"), api("/map")]);
        const c = s.counters || {};
        const ds = document.getElementById("dStats");
        if (!ds) return;
        ds.innerHTML = [[`${s.hospitalsReporting}/${s.hospitals}`, L_("hospitals reporting", "ہسپتال رپورٹ کر رہے ہیں")], [`${s.pharmaciesReporting}/${s.pharmacies}`, L_("pharmacies reporting", "فارمیسیاں رپورٹ کر رہی ہیں")], [`${s.bloodBanksReporting}/${s.bloodBanks}`, L_("blood banks reporting", "بلڈ بینک رپورٹ کر رہے ہیں")], [s.reportedFreeBeds, L_("reported free beds", "رپورٹ شدہ خالی بستر")],
          [s.hospitalsReportedFull.length, L_("ERs reported full", "ایمرجنسی بھری (رپورٹ)")], [s.machinesReportedDown.length, L_("machines reported down", "خراب مشینیں (رپورٹ)")], [c.searches || 0, L_("family searches", "تلاشیں")], [c.staffUpdates || 0, L_("staff reports", "اسٹاف رپورٹس")]]
          .map(([b, t]) => `<div class="stat"><b>${esc(b)}</b><span>${t}</span></div>`).join("");
        if (layers) {
          Object.values(layers).forEach((l) => l.clearLayers());
          mp.facilities.forEach((f) => {
            if (f.type === "hospital") {
              const col = !f.reported ? "#8a96a0" : f.reportedFreeBeds === 0 ? "#c62828" : f.reportedFreeBeds <= 3 ? "#b26a00" : "#138a4a";
              window.L.circleMarker([f.lat, f.lon], { radius: 10, weight: 2, color: "#fff", fillColor: col, fillOpacity: .95 }).addTo(layers.hosp)
                .bindPopup(`<b>${esc(f.name)}</b><br>${f.ownership === "private" ? L_("Private · fees", "پرائیویٹ") : L_("Government · free", "سرکاری")}<br>${f.reported ? f.reportedFreeBeds + " " + L_("reported free beds", "خالی بستر") : NR()}<br><a href="#/facility/${f.id}">${L_("Details", "تفصیل")}</a>`);
            } else if (f.type === "bloodbank") window.L.circleMarker([f.lat, f.lon], { radius: 7, color: "#7b5cd6", fillOpacity: .9 }).addTo(layers.bb).bindPopup(esc(f.name));
            else window.L.circleMarker([f.lat, f.lon], { radius: 4, color: "#1e66f5", fillOpacity: .8 }).addTo(layers.ph).bindPopup(esc(f.name));
          });
        }
        const dl = document.getElementById("dLists");
        const deptRows = Object.entries(s.reportedFreeBedsByDept);
        if (dl) dl.innerHTML = `<div class="card"><h3>${L_("Reported free beds by department", "شعبہ وار رپورٹ شدہ بستر")}</h3>${deptRows.length ? `<table class="t">${deptRows.map(([k, v]) => `<tr><td>${esc(dept(k))}</td><td><span class="pill ${v === 0 ? "r" : v < 4 ? "a" : "g"}">${v}</span></td></tr>`).join("")}</table>` : `<div class="muted small">${L_("No bed reports yet.", "ابھی کوئی رپورٹ نہیں۔")}</div>`}</div>
          <div class="card"><h3>${L_("Needs attention (reported)", "توجہ طلب (رپورٹ)")}</h3><div class="small"><b>${L_("ERs reported full", "بھری ایمرجنسی")}:</b> ${s.hospitalsReportedFull.map(esc).join(", ") || "-"}</div>
          <div class="small" style="margin-top:6px"><b>${L_("Machines reported down", "خراب مشینیں")}:</b> ${s.machinesReportedDown.map((x) => `${esc(x.equipment)} (${esc(x.hospital)})`).join(", ") || "-"}</div>
          <div class="small" style="margin-top:6px"><b>${L_("Blood units reported", "رپورٹ شدہ خون")}:</b> ${Object.entries(s.reportedBloodUnits).map(([g, u]) => `<span class="pill ${u < 5 ? "r" : "g"}">${g} ${u}</span>`).join(" ") || "-"}</div></div>`;
      } catch (e) { const ds = document.getElementById("dStats"); if (ds) ds.innerHTML = errBox(e); }
    }
    await load();
    every(load, 15000);
  }

  // ---- contact / join the pilot
  function contactPage(params) {
    const roles = [["family", L_("Patient or family", "مریض یا خاندان")], ["hospital", L_("Hospital staff", "ہسپتال اسٹاف")], ["pharmacy", L_("Pharmacy", "فارمیسی")], ["bloodbank", L_("Blood bank", "بلڈ بینک")], ["health_department", L_("Health department", "محکمہ صحت")], ["other", L_("Other", "دیگر")]];
    const pre = params.get("role") || "family";
    $app.innerHTML = `<div class="grid2" style="align-items:start">
      <div><h1>✉️ ${L_("Contact us", "رابطہ کریں")}</h1>
        <p class="muted">${L_("Questions, feedback, or want your hospital, pharmacy or blood bank to join the Haazir pilot? Send us a message and we'll get back to you.", "سوال، رائے، یا اپنا ہسپتال، فارمیسی یا بلڈ بینک شامل کرنا چاہتے ہیں؟ پیغام بھیجیں۔")}</p>
        <div class="card"><div class="field"><input id="cName" maxlength="80" placeholder="${L_("Your name", "آپ کا نام")}"></div>
          <div class="field"><select id="cRole">${roles.map(([v, l]) => `<option value="${v}" ${v === pre ? "selected" : ""}>${l}</option>`).join("")}</select><input id="cOrg" maxlength="120" placeholder="${L_("Organisation (optional)", "ادارہ (اختیاری)")}"></div>
          <div class="field"><input id="cReach" maxlength="120" placeholder="${L_("Phone or email", "فون یا ای میل")}"></div>
          <textarea id="cMsg" maxlength="1000" placeholder="${L_("Your message", "آپ کا پیغام")}"></textarea>
          <p class="small muted">🔒 ${L_("We only use your details to reply to you. Never share medical details here; in an emergency call 1122.", "آپ کی معلومات صرف جواب دینے کے لیے استعمال ہوں گی۔ ایمرجنسی میں 1122 کال کریں۔")}</p>
          <div class="btns"><button class="btn p" id="cSend">➤ ${L_("Send message", "پیغام بھیجیں")}</button></div><div id="cOut"></div></div></div>
      <div><div class="card art">${(window.HAAZIR_ART || {}).hospital || ""}</div>
        <div class="card small"><h3>${L_("Emergency numbers", "ایمرجنسی نمبر")}</h3>
          <div class="btns">${helplineBtns(false)}</div><p class="muted">${L_("Haazir is not an emergency service. For any emergency call Rescue 1122 or Edhi 115 first.", "حاضر ایمرجنسی سروس نہیں۔ پہلے 1122 یا 115 کال کریں۔")}</p></div>
        <div class="card small"><h3>🏥 ${L_("For hospitals, pharmacies and blood banks", "ہسپتالوں، فارمیسیوں اور بلڈ بینکوں کے لیے")}</h3>
          <p class="muted">${L_("Joining is free. Your staff report availability in one Roman-Urdu message from any phone, and families see it instantly.", "شمولیت مفت ہے۔ اسٹاف کسی بھی فون سے ایک پیغام میں رپورٹ کرتا ہے۔")}</p><a class="btn sm" href="#/staff">${L_("Try the staff portal", "اسٹاف پورٹل آزمائیں")} →</a></div></div></div>`;
    document.getElementById("cSend").onclick = async (ev) => {
      const out = document.getElementById("cOut");
      ev.target.disabled = true;
      try {
        const r = await post("/contact", { name: document.getElementById("cName").value, role: document.getElementById("cRole").value, organisation: document.getElementById("cOrg").value, contact: document.getElementById("cReach").value, message: document.getElementById("cMsg").value });
        out.innerHTML = `<div class="note">✅ ${L_("Thank you! Your message has been received. Reference:", "شکریہ! آپ کا پیغام موصول ہو گیا۔ ریفرنس:")} <b>${esc(r.referenceCode)}</b></div>`;
        ["cName", "cOrg", "cReach", "cMsg"].forEach((id) => { document.getElementById(id).value = ""; });
      } catch (e) { out.innerHTML = errBox(e); }
      ev.target.disabled = false;
    };
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
      case "ambulance": return ambulancePage();
      case "medicine": return medicinePage(params);
      case "blood": return bloodPage(params);
      case "equipment": return equipmentPage(params);
      case "staff": return staffPage();
      case "dashboard": return dashboardPage();
      case "contact": return contactPage(params);
      default: return home();
    }
  }
  window.addEventListener("hashchange", route);
  route();
})();
