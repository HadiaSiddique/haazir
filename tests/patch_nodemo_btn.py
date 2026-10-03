"""One-off: remove the Demo button + top banner; sample data always on; subtle 'sample' tags."""
import os

base = os.path.join(os.path.dirname(__file__), "..", "frontend")


def patch(fn, pairs):
    p = os.path.join(base, fn)
    s = open(p, encoding="utf-8").read()
    for old, new in pairs:
        if old not in s:
            raise SystemExit(f"MISSING in {fn}: {old[:80]}")
        s = s.replace(old, new)
    open(p, "w", encoding="utf-8", newline="\n").write(s)


patch("app.js", [
    # sample data always on; ?demo=0 in the page URL still shows real reports only (for the video)
    ('demo: store("demo") !== "0" };', 'demo: !/[?&]demo=0\\b/.test(location.search) };'),
    ('    document.getElementById("pilot").textContent = state.demo\n',
     '    document.getElementById("pilot").style.display = state.demo ? "none" : "";\n'
     '    document.getElementById("pilot").textContent = state.demo\n'),
    ('      `<button class="demoSwitch ${state.demo ? "on" : ""}" id="demoBtn" title="Sample data for the demo">🧪 ${L_("Demo data", "ڈیمو")} <span class="k"></span></button>` +\n', ''),
    ('    document.getElementById("demoBtn").onclick = () => { state.demo = !state.demo; store("demo", state.demo ? "1" : "0"); route(); };\n', ''),
    ('const demoPill = () => `<span class="pill demo">🧪 ${L_("demo sample", "ڈیمو نمونہ")}</span>`;',
     'const demoPill = () => `<span class="pill sample" title="${L_("Sample data for this pilot", "پائلٹ کے لیے نمونہ ڈیٹا")}">${L_("sample", "نمونہ")}</span>`;'),
    ('${state.demo ? `<span class="pill demo">🧪 ${L_("demo sample", "ڈیمو")}</span>` : ""}</h3>', '${state.demo ? demoPill() : ""}</h3>'),
    ('🧪 ${L_("Demo mode shows sample availability, clearly tagged \'demo sample\'. Switch it off in the header to see real staff reports only.", "ڈیمو موڈ میں نمونہ ڈیٹا \'ڈیمو\' لیبل کے ساتھ ہے؛ اوپر سے بند کریں۔")}',
     '🧪 ${L_("This pilot shows sample availability numbers (tagged \'sample\') until hospitals start reporting. Real staff reports replace them instantly.", "یہ پائلٹ نمونہ نمبر دکھاتا ہے (نمونہ لیبل)، اسٹاف کی اصل رپورٹ فوراً ان کی جگہ لیتی ہے۔")}'),
    ('" + (state.demo ? "Demo mode is on: availability numbers are sample data." : "Availability is shown only when staff report it.") + "',
     '" + (state.demo ? "Pilot: availability numbers (beds, doctors, machines, stock, blood) are sample data; doctor names are fictional." : "Showing real staff reports only.") + "'),
])
patch("styles.css", [
    ('.pill.demo {', '.pill.sample { background: transparent; color: var(--grey); border: 1px dashed var(--line); font-weight: 600; }\n.pill.demo {'),
])
patch("index.html", [
    ('<div class="pilot" id="pilot">', '<div class="pilot" id="pilot" style="display:none">'),
])
print("patched")
