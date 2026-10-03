"""One-off: illustrations on home, remove 'Built on AWS' section, full footer, contact page."""
import os

root = os.path.join(os.path.dirname(__file__), "..")


def patch(fn, pairs):
    p = os.path.join(root, fn)
    s = open(p, encoding="utf-8").read()
    for old, new in pairs:
        if old not in s:
            raise SystemExit(f"MISSING in {fn}: {old[:90]}")
        s = s.replace(old, new)
    open(p, "w", encoding="utf-8", newline="\n").write(s)


FOOTER = r'''    const yr = new Date().getFullYear();
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
'''

CONTACT_PAGE = r'''  // ---- contact / join the pilot
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
'''

patch("frontend/app.js", [
    # footer
    ('    document.getElementById("foot").innerHTML = `<b>Haazir حاضر</b>', FOOTER + '    void `<b>Haazir حاضر</b>'),
    # home: badge, scene, showcase, illustrated steps, remove AWS section
    ('${L_("Live in Lahore · built on AWS", "لاہور میں لائیو · AWS پر")}', '${L_("Live in Lahore", "لاہور میں لائیو")}'),
    ('    <div class="emstrip"><div class="grow">',
     '    <div class="scene">${(window.HAAZIR_ART || {}).scene || ""}</div>\n    <div class="emstrip"><div class="grow">'),
    ('    <div class="sec"><h2>${L_("Every facility on one map"',
     '    <div class="sec"><h2>${L_("Everything you need, in one place", "سب کچھ ایک جگہ")}</h2><p class="lead">${L_("Real hospitals, pharmacies and blood banks across Lahore, plus the ambulance helplines.", "لاہور کے اصل ہسپتال، فارمیسیاں، بلڈ بینک اور ایمبولینس ہیلپ لائنز۔")}</p>\n'
     '      <div class="showcase">${[["#/hospitals", "hospital", L_("19 hospitals", "19 ہسپتال"), L_("10 government (free) · 9 private", "10 سرکاری · 9 پرائیویٹ")], ["#/medicine", "pharmacy", L_("71 pharmacies", "71 فارمیسیاں"), L_("Stock, uses, prescription info", "اسٹاک، استعمال، نسخہ")], ["#/blood", "bloodbank", L_("6 blood banks", "6 بلڈ بینک"), L_("Units by blood group", "بلڈ گروپ کے مطابق")], ["#/ambulance", "ambulance", L_("Ambulance", "ایمبولینس"), "Rescue 1122 · Edhi 115"]].map(([h, a, t, s]) => `<a class="showcard" href="${h}"><div class="art">${(window.HAAZIR_ART || {})[a] || ""}</div><b>${t}</b><span>${s}</span></a>`).join("")}</div></div>\n'
     '    <div class="sec"><h2>${L_("Every facility on one map"'),
    ('<div class="card"><span class="num">1</span><h3>', '<div class="card"><span class="num">1</span><div class="art sm">${(window.HAAZIR_ART || {}).phone || ""}</div><h3>'),
    ('<div class="card"><span class="num">2</span><h3>', '<div class="card"><span class="num">2</span><div class="art sm">${(window.HAAZIR_ART || {}).search || ""}</div><h3>'),
    ('<div class="card"><span class="num">3</span><h3>', '<div class="card"><span class="num">3</span><div class="art sm">${(window.HAAZIR_ART || {}).pin || ""}</div><h3>'),
    ('    <div class="sec"><h2>${L_("Built on AWS", "AWS پر بنا")}</h2><p class="lead">${L_("Serverless, pay-per-use, ready to scale from one hospital to all of Punjab.", "سرور لیس، ایک ہسپتال سے پورے پنجاب تک۔")}</p>\n'
     '      <div class="awsrow"><span>Amazon Bedrock</span><span>AWS Lambda</span><span>Amazon DynamoDB</span><span>Amazon API Gateway</span><span>Amazon CloudFront</span><span>Amazon S3</span><span>AWS CloudFormation</span></div></div>\n', ''),
    # contact route
    ('  // ------------------------------------------------------------ router\n', CONTACT_PAGE),
    ('      case "dashboard": return dashboardPage();\n', '      case "dashboard": return dashboardPage();\n      case "contact": return contactPage(params);\n'),
])

patch("frontend/index.html", [
    ('<script src="config.js"></script>', '<script src="config.js"></script>\n<script src="art.js"></script>'),
])
patch("backend/handler.py", [
    ('          "/styles.css": ("styles.css", "text/css; charset=utf-8"),',
     '          "/styles.css": ("styles.css", "text/css; charset=utf-8"),\n          "/art.js": ("art.js", "application/javascript; charset=utf-8"),'),
])
patch("deploy.ps1", [
    ('Copy-Item frontend\\index.html, frontend\\app.js, frontend\\styles.css backend\\static\\',
     'Copy-Item frontend\\index.html, frontend\\app.js, frontend\\art.js, frontend\\styles.css backend\\static\\'),
])
print("patched")
