"""One-off source patch for frontend/app.js: demo switch + tags, medicine info, redesigned home."""
import os

p = os.path.join(os.path.dirname(__file__), "..", "frontend", "app.js")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("MISSING: " + old[:90])
    s = s.replace(old, new)


# 1. state + api(): demo flag travels as ?demo=0 when switched off
rep('const state = { lang: store("lang") || "en", loc: null, staff: null };',
    'const state = { lang: store("lang") || "en", loc: null, staff: null, demo: store("demo") !== "0" };')
rep('const r = await fetch(API + path, Object.assign(',
    'if (!state.demo) path += (path.includes("?") ? "&" : "?") + "demo=0";\n      const r = await fetch(API + path, Object.assign(')

# 2. banner + demo switch in the header
rep('document.getElementById("pilot").textContent = L_("Pilot: real Lahore hospitals, pharmacies and blood banks. Beds, doctors, machines, stock and blood appear only when staff report them.", "پائلٹ: لاہور کے اصل ہسپتال، فارمیسیاں اور بلڈ بینک۔ بستر، ڈاکٹر، مشینیں، دوا اور خون صرف اسٹاف کی رپورٹ کے بعد دکھائے جاتے ہیں۔");',
    'document.getElementById("pilot").textContent = state.demo\n'
    '      ? L_("🧪 Demo mode: hospitals, pharmacies and blood banks are real places in Lahore; the availability numbers are SAMPLE data for this demo. Switch \'Demo data\' off to see real staff reports only.", "🧪 ڈیمو: ہسپتال، فارمیسیاں اور بلڈ بینک اصل ہیں؛ دستیابی کے نمبر نمونہ (فرضی) ہیں۔ صرف اصل رپورٹس دیکھنے کے لیے ڈیمو بند کریں۔")\n'
    '      : L_("Real reports only: availability shown here was reported by staff. Anything not reported says \'not reported yet\'.", "صرف اصل رپورٹس: دستیابی اسٹاف نے رپورٹ کی ہے۔");')
rep('      `<button class="lang" id="langBtn">${state.lang === "ur" ? "English" : "اردو"}</button>`;',
    '      `<button class="demoSwitch ${state.demo ? "on" : ""}" id="demoBtn" title="Sample data for the demo">🧪 ${L_("Demo data", "ڈیمو")} <span class="k"></span></button>` +\n'
    '      `<button class="lang" id="langBtn">${state.lang === "ur" ? "English" : "اردو"}</button>`;')
rep('    document.getElementById("langBtn").onclick =',
    '    document.getElementById("demoBtn").onclick = () => { state.demo = !state.demo; store("demo", state.demo ? "1" : "0"); route(); };\n'
    '    document.getElementById("langBtn").onclick =')

# 3. demo tags
rep('const reportLine = (ts, by) => (ts ?',
    'const demoPill = () => `<span class="pill demo">🧪 ${L_("demo sample", "ڈیمو نمونہ")}</span>`;\n'
    '  const reportLine = (ts, by, demo) => (demo ? `${demoPill()}<span class="pill x">${ago(ts)}</span>` : ts ?')
rep('${reportLine(h.updatedAt)}', '${reportLine(h.updatedAt, null, h.demo)}')
rep('<span class="pill ${s.exact ? "g" : "a"} ${s.stale ? "stale" : ""}">${esc(s.name)} · ${s.qty} ${L_("in stock", "موجود")}${s.priceRs ? " · Rs " + s.priceRs : ""}</span>`).join("")}</div>',
    '<span class="pill ${s.exact ? "g" : "a"} ${s.stale ? "stale" : ""}">${esc(s.name)} · ${s.qty} ${L_("in stock", "موجود")}${s.priceRs ? " · Rs " + s.priceRs : ""}</span>`).join("")}${p.stock.some((s) => s.demo) ? demoPill() : ""}</div>')
rep('<div class="pills">${b.locationPrecision === "area"',
    '<div class="pills">${b.demo ? demoPill() : ""}${b.locationPrecision === "area"')
rep('<div class="pills">${ownPill(r.ownership)}${eqPill(d.type, r)}</div>',
    '<div class="pills">${ownPill(r.ownership)}${eqPill(d.type, r)}${r.demo ? demoPill() : ""}</div>')
rep('${approx}<span class="pill x">${f.distanceKm} km',
    '${approx}${f.demo ? demoPill() : ""}<span class="pill x">${f.distanceKm} km')

# 4. medicine: what it's for + prescription status
rep('let html = `<div class="card"><h3>💊 ${esc(m.name)}</h3><div class="small muted">${L_("Active ingredient", "جزو")}: ${esc(m.salt)} ${esc(m.strength)}</div>`;',
    'const RX = { rx: ["rx", "📝 " + L_("Prescription needed: ask your doctor", "ڈاکٹر کا نسخہ ضروری ہے")], otc: ["otc", "✅ " + L_("Usually sold without a prescription", "عام طور پر نسخے کے بغیر ملتی ہے")], ask: ["ask", "💬 " + L_("Ask your pharmacist or doctor", "فارماسسٹ یا ڈاکٹر سے پوچھیں")] }[m.rx || "ask"];\n'
    '    let html = `<div class="card"><h3>💊 ${esc(m.name)}</h3><div class="small muted">${L_("Active ingredient", "جزو")}: ${esc(m.salt)} ${esc(m.strength)}</div>\n'
    '      <div class="medinfo">${m.use ? `<div class="use"><b>${L_("Used for", "استعمال")}:</b> ${esc(state.lang === "ur" && m.useUr ? m.useUr : m.use)}</div>` : ""}\n'
    '      <div><span class="rxb ${RX[0]}">${RX[1]}</span></div>\n'
    '      <div class="small muted">${L_("General information, not medical advice. Always take medicines as your doctor prescribed.", "یہ عمومی معلومات ہیں، طبی مشورہ نہیں۔ دوا ہمیشہ ڈاکٹر کے نسخے کے مطابق لیں۔")}</div></div>`;')

open(p, "w", encoding="utf-8", newline="\n").write(s)
print("frontend patched")
