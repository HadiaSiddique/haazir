"""Deterministic, explainable logic. AI understands language; this code decides.

Availability (beds, doctors on duty, machines, stock, blood) comes ONLY from staff reports. When nothing has been
reported, the value is unknown and is shown as "not reported", never as zero or "down"."""
import math
import re
import time

import ai
from seed_data import BLOOD_GROUPS, MED_INFO, MEDICINES

LAHORE = (31.5204, 74.3587)
TRAFFIC_KMH = 20
STALE_SECONDS = 2 * 3600
DEPARTMENTS = ["Emergency", "Medicine", "Surgery", "Cardiology", "Paediatrics", "Gynae/Obstetrics",
               "Orthopaedics", "ICU", "Burns"]
EQUIP_TYPES = ["CT", "MRI", "XRay", "Dialysis", "Ventilator", "Oxygen"]
INTENTS = ["hospital_care", "ambulance", "medicine", "blood", "test_equipment", "doctor"]

# recipient -> donor groups it can safely receive red cells from (standard ABO/Rh table)
BLOOD_COMPAT = {
    "O-": ["O-"], "O+": ["O+", "O-"], "A-": ["A-", "O-"], "A+": ["A+", "A-", "O+", "O-"],
    "B-": ["B-", "O-"], "B+": ["B+", "B-", "O+", "O-"], "AB-": ["AB-", "A-", "B-", "O-"],
    "AB+": BLOOD_GROUPS,
}

RED_FLAGS = [
    (r"seen[ae]y? (mein|me|main) dard|seene|chest pain|heart attack|dil (ka|ki|mein)|dil ka daura|chhati", "Chest pain", "Cardiology"),
    (r"saa?ns|breath|dam ghut|saans nahi|breathing", "Breathing difficulty", "Emergency"),
    (r"behosh|unconscious|hosh nahi|faint|not responding", "Unconscious / unresponsive", "Emergency"),
    (r"khoon (beh|nikal|ruk)|heavy bleeding|bleeding|khoon bohat", "Heavy bleeding", "Emergency"),
    (r"fali?j|laqwa|stroke|munh tehra|face droop|slurred|zuban larkhara", "Stroke signs", "Emergency"),
    (r"dora|mirgi|seizure|\bfits?\b|jhatke", "Seizure", "Emergency"),
    (r"accident|haadsa|hadsa|injur|zakhm|zakhmi|gir gay|fracture|haddi toot", "Severe injury", "Orthopaedics"),
    (r"dard-?e-?zeh|labou?r|delivery|zachgi|pani ki thaili|pregnan.*(bleed|khoon|dard)", "Labour complications", "Gynae/Obstetrics"),
    (r"jal gay|burn|jhulas", "Burns", "Burns"),
    (r"\bemergency\b|imergency|ایمرجنسی", "Reported emergency", "Emergency"),
]

DEPT_WORDS = [
    (r"bacha|bachay|bachi|child|baby|paediatric|pediatric|infant|navjaat", "Paediatrics"),
    (r"gyn|gynae|pregnan|haamla|delivery|zachgi|lady doctor|ladies", "Gynae/Obstetrics"),
    (r"dil|heart|cardi|seen[ae]y? (mein|me) dard|bp|blood pressure", "Cardiology"),
    (r"haddi|bone|fracture|ortho|joint|kamar", "Orthopaedics"),
    (r"operation|surgery|surgeon|appendix|pathri", "Surgery"),
    (r"icu|ventilator|critical", "ICU"),
    (r"burn|jal gay", "Burns"),
    (r"bukhar|fever|sugar|diabet|dengue|typhoid|ulti|dast|infection|kamzori", "Medicine"),
]


def haversine(a_lat, a_lon, b_lat, b_lon):
    r = 6371.0
    p1, p2 = math.radians(a_lat), math.radians(b_lat)
    dp, dl = p2 - p1, math.radians(b_lon - a_lon)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def eta_min(km, kmh=TRAFFIC_KMH):
    return max(2, round(km / kmh * 60))


def loc(lat, lon):
    try:
        lat, lon = float(lat), float(lon)
        if 30.5 < lat < 32.5 and 73.5 < lon < 75.5:
            return lat, lon
    except (TypeError, ValueError):
        pass
    return LAHORE


def now():
    return int(time.time())


def fresh(res):
    return now() - int(res.get("updatedAt", 0)) < STALE_SECONDS


# ---------------------------------------------------------------- understanding

def keyword_understand(text):
    t = (text or "").lower()
    ent = {"department": None, "urgency": "routine", "redFlag": False, "redFlagReason": None,
           "medicines": [], "bloodGroup": None, "units": None, "testType": None,
           "femaleDoctor": False, "sehatCard": False}
    for pat, reason, dept in RED_FLAGS:
        if re.search(pat, t):
            ent.update(redFlag=True, redFlagReason=reason, urgency="emergency", department=dept)
            break
    if not ent["department"]:
        for pat, dept in DEPT_WORDS:
            if re.search(pat, t):
                ent["department"] = dept
                break
    m = re.search(r"\b(ab|a|b|o)\s*(\+|-|pos(?:itive)?|neg(?:ative)?|plus|minus)", t)
    if m:
        g = m.group(1).upper()
        sign = "+" if m.group(2) in ("+", "pos", "positive", "plus") else "-"
        ent["bloodGroup"] = g + sign
    u = re.search(r"(\d+)\s*(bottle|botal|bag|unit|pint)", t)
    if u:
        ent["units"] = int(u.group(1))
    for key, name, salt, strength in MEDICINES:
        brand = name.split()[0].lower()
        if len(brand) > 3 and brand in t and name not in ent["medicines"]:
            ent["medicines"].append(name.split(" (")[0])
    for e, pat in [("CT", r"\bct\b|ct scan|cat scan"), ("MRI", r"\bmri\b"), ("XRay", r"x-?ray|xray"),
                   ("Dialysis", r"dialys"), ("Ventilator", r"ventilator"), ("Oxygen", r"oxygen|oxijan")]:
        if re.search(pat, t):
            ent["testType"] = e
            break
    ent["femaleDoctor"] = bool(re.search(r"lady|female|khatoon|aurat doctor|women doctor|lady doctor", t))
    ent["sehatCard"] = bool(re.search(r"sehat|sehat card|health card", t))
    ent["area"] = next((a for a in AREAS if a in t), None)
    if re.search(r"jaldi|urgent|foran|abhi", t) and ent["urgency"] == "routine":
        ent["urgency"] = "urgent"

    if re.search(r"ambulance|ambulence|1122|rescue", t):
        intent = "ambulance"
    elif ent["bloodGroup"] or re.search(r"\bblood\b|khoon chahiye|donor", t):
        intent = "blood"
    elif ent["medicines"] or re.search(r"dawa|dawai|medicine|tablet|goli|pharmacy|kahan milegi", t):
        intent = "medicine"
    elif ent["testType"] and not ent["redFlag"]:
        intent = "test_equipment"
    elif ent["femaleDoctor"] or re.search(r"\bdoctor\b|dr\b|specialist", t):
        intent = "doctor"
    else:
        intent = "hospital_care"
    return intent, ent


UNDERSTAND_PROMPT = """You route people in Lahore, Pakistan to healthcare. Input may be Urdu, Roman Urdu or English.
You do NOT diagnose. Classify the request and extract entities. Reply with ONLY a JSON object:
{"intent": one of ["hospital_care","ambulance","medicine","blood","test_equipment","doctor"],
 "department": one of ["Emergency","Medicine","Surgery","Cardiology","Paediatrics","Gynae/Obstetrics","Orthopaedics","ICU","Burns"] or null,
 "urgency": "emergency"|"urgent"|"routine",
 "redFlag": true if ANY of: chest pain, breathing difficulty, unconscious, heavy bleeding, stroke signs, seizure, severe injury, labour complications, severe burns,
 "redFlagReason": short English phrase or null,
 "medicines": [medicine names mentioned, e.g. "Augmentin 625mg"],
 "bloodGroup": "O-"|"O+"|"A+"|... or null, "units": integer or null,
 "testType": one of ["CT","MRI","XRay","Dialysis","Ventilator","Oxygen"] or null,
 "femaleDoctor": boolean, "sehatCard": boolean,
 "area": Lahore area name mentioned or null,
 "reasonEn": one short sentence explaining what you understood (no diagnosis),
 "reasonUr": the same sentence in simple Urdu script}
Examples: "abbu ko seenay mein dard" -> hospital_care, Cardiology, emergency, redFlag true.
"O negative blood chahiye 2 bottle" -> blood, bloodGroup "O-", units 2.
"Augmentin kahan milegi Johar Town" -> medicine, medicines ["Augmentin"], area "Johar Town".
"CT scan kahan ho raha hai abhi" -> test_equipment, testType "CT".
"lady doctor gynae" -> doctor, department "Gynae/Obstetrics", femaleDoctor true."""

AREAS = {"johar town": (31.4697, 74.2728), "gulberg": (31.5204, 74.3487), "dha": (31.4720, 74.4060),
         "model town": (31.4834, 74.3256), "iqbal town": (31.5050, 74.2900), "garden town": (31.5000, 74.3220),
         "shadman": (31.5390, 74.3300), "anarkali": (31.5690, 74.3100), "township": (31.4500, 74.3100),
         "wapda town": (31.4350, 74.2650), "faisal town": (31.4790, 74.3040), "samanabad": (31.5340, 74.2980),
         "cantt": (31.5100, 74.3900), "shahdara": (31.6280, 74.2950), "ichhra": (31.5300, 74.3150),
         "bahria town": (31.3690, 74.1830), "valencia": (31.4040, 74.2560)}


def understand(text):
    k_intent, k_ent = keyword_understand(text)
    data = ai.converse_json(UNDERSTAND_PROMPT, f"Request: {text[:500]}")
    source = "ai"
    if not isinstance(data, dict) or data.get("intent") not in INTENTS:
        data, source = {"intent": k_intent, **k_ent}, "keywords"
    ent = {**k_ent, **{k: v for k, v in data.items() if k not in ("intent",) and v not in (None, "", [])}}
    if ent.get("department") not in DEPARTMENTS:
        ent["department"] = k_ent["department"]
    if ent.get("testType") not in EQUIP_TYPES:
        ent["testType"] = k_ent["testType"]
    if ent.get("bloodGroup") not in BLOOD_GROUPS:
        ent["bloodGroup"] = k_ent["bloodGroup"]
    # safety: a keyword red flag is never overridden by the model
    if k_ent["redFlag"]:
        ent["redFlag"] = True
        ent["redFlagReason"] = ent.get("redFlagReason") or k_ent["redFlagReason"]
        ent["urgency"] = "emergency"
    ent["redFlag"] = bool(ent.get("redFlag"))
    intent = data["intent"]
    if ent["redFlag"] and intent in ("doctor", "test_equipment"):
        intent = "hospital_care"
    return intent, ent, source


# ---------------------------------------------------------------- hospitals (reported data only)

def reported_free(f, dept):
    """Free beds as last reported by staff, or None if never reported."""
    b = f["beds"].get(dept)
    return None if not b else int(b.get("free", 0))


def er_load(f):
    free = reported_free(f, "Emergency")
    if free is None:
        return "Unknown"
    return "Full" if free == 0 else ("Busy" if free <= 3 else "Low")


def hospital_card(f, lat, lon, dept=None):
    km = haversine(lat, lon, f["lat"], f["lon"])
    on_duty = [d for d in f["doctors"].values() if d.get("onDuty")]
    dept_docs = [d for d in on_duty if not dept or d.get("dept") == dept]
    beds = {k: {"free": int(v.get("free", 0)), "updatedAt": v.get("updatedAt"), "updatedBy": v.get("updatedBy"),
                "stale": not fresh(v)} for k, v in f["beds"].items()}
    reports = [r.get("updatedAt", 0) for g in ("beds", "doctors", "equipment") for r in f[g].values()]
    return {
        "id": f["id"], "name": f["name"], "nameUr": f.get("nameUr"), "lat": f["lat"], "lon": f["lon"],
        "ownership": f.get("ownership", "government"), "departments": f.get("departments", []),
        "distanceKm": round(km, 1), "etaMin": eta_min(km), "erLoad": er_load(f),
        "department": dept, "freeBeds": reported_free(f, dept) if dept else None,
        "beds": beds,
        "doctorsOnDuty": [{"name": d["name"], "dept": d.get("dept"), "gender": d.get("gender"), "shiftEnds": d.get("shiftEnds")}
                          for d in (dept_docs or on_duty)][:4],
        "femaleDoctor": any(d.get("gender") == "F" for d in (dept_docs if dept else on_duty)),
        "equipment": {k: {"status": v["status"], "stale": not fresh(v), "updatedAt": v.get("updatedAt")}
                      for k, v in f["equipment"].items()},
        "hasReports": bool(reports), "updatedAt": max(reports) if reports else None,
        "demo": any(r.get("demo") for g in ("beds", "doctors", "equipment") for r in f[g].values()),
    }


def rank_hospitals(snap, lat, lon, dept=None, equipment=None, female=False, sehat=False, red_flag=False, ownership=None):
    """Rank by what is KNOWN. Unknown availability is neutral (no bonus, no penalty); distance always counts."""
    dept = dept or ("Emergency" if red_flag else None)
    results = []
    for f in snap["facilities"].values():
        if f["type"] != "hospital":
            continue
        if dept and dept not in f.get("departments", []):
            continue
        if ownership and f.get("ownership", "government") != ownership:
            continue
        card = hospital_card(f, lat, lon, dept)
        score, why = 0.0, []
        if dept:
            why.append(f"has {dept}")
            fb = card["freeBeds"]
            src = "demo sample:" if f["beds"].get(dept, {}).get("demo") else "staff report"
            if fb is None:
                why.append("beds not reported yet")
            elif fb == 0:
                score -= 100
                why.append(f"{src} no free {dept} beds")
            else:
                score += 30 + min(fb, 5) * 3
                why.append(f"{src} {fb} free {dept} beds")
            # real reports first, then demo sample rows
            specialists = sorted((d for d in f["doctors"].values() if d.get("onDuty") and d.get("dept") == dept),
                                 key=lambda d: bool(d.get("demo")))
            if specialists:
                score += 25
                why.append(f"{specialists[0]['name']} {'(demo) ' if specialists[0].get('demo') else ''}on duty")
        if female:
            fem = [d for d in f["doctors"].values() if d.get("onDuty") and d.get("gender") == "F"
                   and (not dept or d.get("dept") == dept)]
            if fem:
                score += 20
                why.append(f"female doctor {fem[0]['name']} reported on duty")
        if equipment:
            e = f["equipment"].get(equipment)
            if not e:
                why.append(f"{equipment} status not reported")
            elif e["status"] == "working":
                score += 20
                why.append(f"{equipment} reported working")
            elif e["status"] == "busy":
                score += 5
                why.append(f"{equipment} reported busy")
            else:
                score -= 60
                why.append(f"{equipment} reported down")
        if card["erLoad"] == "Full":
            score -= 35 if red_flag else 15
        score -= card["etaMin"] * (2.5 if red_flag else 1.2)  # in emergencies every minute counts more
        card["score"] = round(score, 1)
        card["why"] = ", ".join(why[:3]) + f" · {card['etaMin']} min away"
        results.append(card)
    results.sort(key=lambda c: -c["score"])
    return results


def minutes_saved(results):
    """Count ~25 min when the nearest relevant hospital has REPORTED it cannot help and we routed elsewhere."""
    if len(results) < 2:
        return 0
    nearest = min(results, key=lambda c: c["distanceKm"])
    reported_full = nearest["freeBeds"] == 0
    return 25 if (reported_full and results[0]["id"] != nearest["id"]) else 0


# ---------------------------------------------------------------- medicine

CATALOG = {k: {"key": k, "name": n, "salt": s, "strength": st,
               "use": MED_INFO.get(s, (None, None, "ask"))[0], "useUr": MED_INFO.get(s, (None, None, "ask"))[1],
               "rx": MED_INFO.get(s, (None, None, "ask"))[2]} for k, n, s, st in MEDICINES}


def match_medicine(q):
    """Fuzzy match a free-text medicine name to catalogue keys (best first)."""
    q = (q or "").lower().strip()
    if not q:
        return []
    words = [w for w in re.split(r"[^a-z0-9.]+", q) if w]
    scored = []
    for k, m in CATALOG.items():
        name, salt = m["name"].lower(), m["salt"].lower()
        s = 0
        if q in name:
            s += 10
        for w in words:
            if len(w) >= 3 and (name.startswith(w) or f" {w}" in name):
                s += 5
            if len(w) >= 4 and w in salt:
                s += 3
            if w.rstrip("mg") and w.rstrip("mg") in m["strength"]:
                s += 1
        if s:
            scored.append((s, k))
    scored.sort(key=lambda x: -x[0])
    if not scored:
        return []
    top = scored[0][0]
    return [k for s, k in scored if s >= max(5, top - 4)][:6]


def same_salt(key):
    m = CATALOG[key]
    return [k for k, x in CATALOG.items() if x["salt"] == m["salt"] and x["strength"] == m["strength"]]


def medicine_search(snap, q, lat, lon):
    keys = match_medicine(q)
    if not keys:
        return {"query": q, "matched": [], "pharmacies": [], "alternatives": [], "reportingPharmacies": 0}
    primary = keys[0]
    alt_keys = [k for k in same_salt(primary) if k != primary]
    pharmacies, reporting = [], 0
    for f in snap["facilities"].values():
        if f["type"] != "pharmacy":
            continue
        if f["medicine"]:
            reporting += 1
        stock = []
        for k in [primary] + alt_keys:
            r = f["medicine"].get(k)
            if r and r.get("qty", 0) > 0:
                stock.append({"key": k, "name": CATALOG[k]["name"], "qty": r["qty"], "priceRs": r.get("priceRs"),
                              "exact": k == primary, "stale": not fresh(r), "updatedAt": r.get("updatedAt"),
                              "demo": bool(r.get("demo"))})
        if not stock:
            continue
        km = haversine(lat, lon, f["lat"], f["lon"])
        pharmacies.append({"id": f["id"], "name": f["name"], "lat": f["lat"], "lon": f["lon"],
                           "distanceKm": round(km, 1), "etaMin": eta_min(km),
                           "hasExact": any(s["exact"] for s in stock), "stock": stock})
    pharmacies.sort(key=lambda p: (not p["hasExact"], p["distanceKm"]))
    nearby = sorted(({"id": f["id"], "name": f["name"], "lat": f["lat"], "lon": f["lon"],
                      "distanceKm": round(haversine(lat, lon, f["lat"], f["lon"]), 1)}
                     for f in snap["facilities"].values() if f["type"] == "pharmacy"), key=lambda p: p["distanceKm"])[:8]
    return {"query": q, "matched": [CATALOG[primary]], "alternatives": [CATALOG[k] for k in alt_keys],
            "pharmacies": pharmacies[:12], "nearbyPharmacies": nearby, "reportingPharmacies": reporting,
            "note": "Same active ingredient and strength only. Confirm with your doctor or pharmacist before switching."}


def medicine_plan(snap, names, lat, lon):
    """Using REPORTED stock only: one pharmacy with everything, else fewest stops (greedy set cover)."""
    wanted = []
    for n in names[:10]:
        ks = match_medicine(n)
        wanted.append({"asked": n, "key": ks[0] if ks else None, "name": CATALOG[ks[0]]["name"] if ks else None})
    keys = [w["key"] for w in wanted if w["key"]]
    shops = []
    for f in snap["facilities"].values():
        if f["type"] != "pharmacy":
            continue
        have = {}
        for k in keys:
            for alt in [k] + [a for a in same_salt(k) if a != k]:
                r = f["medicine"].get(alt)
                if r and r.get("qty", 0) > 0:
                    have[k] = {"key": alt, "name": CATALOG[alt]["name"], "priceRs": r.get("priceRs"), "substitute": alt != k}
                    break
        if have:
            km = haversine(lat, lon, f["lat"], f["lon"])
            shops.append({"id": f["id"], "name": f["name"], "lat": f["lat"], "lon": f["lon"],
                          "distanceKm": round(km, 1), "etaMin": eta_min(km), "have": have})
    full = [s for s in shops if len(s["have"]) == len(set(keys))]
    full_exact = [s for s in full if not any(v["substitute"] for v in s["have"].values())]
    pick = sorted(full_exact or full, key=lambda s: s["distanceKm"])
    if keys and pick:
        stops = [pick[0]]
    else:
        stops, remaining = [], set(keys)
        while remaining and shops:
            best = max(shops, key=lambda s: (len(remaining & set(s["have"])), -s["distanceKm"]))
            got = remaining & set(best["have"])
            if not got:
                break
            stops.append({**best, "have": {k: best["have"][k] for k in got}})
            remaining -= got
    prices = [v["priceRs"] for s in stops for v in s["have"].values()]
    covered = {k for s in stops for k in s["have"]}
    return {"items": wanted, "stops": stops, "onePharmacy": len(stops) == 1 and len(covered) == len(set(keys)) > 0,
            "missing": [w for w in wanted if not w["key"] or w["key"] not in covered],
            "totalRs": sum(prices) if prices and all(p is not None for p in prices) else None,
            "note": "Based only on stock reported by pharmacists. Substitutes have the same active ingredient and "
                    "strength. Confirm with your doctor or pharmacist before switching."}


RX_PROMPT = """You read photos of prescriptions or medicine packs from Pakistan. List ONLY the medicines you can read.
Reply ONLY JSON: {"medicines":[{"name":"brand or generic name","strength":"e.g. 625mg or null","confidence":"high"|"medium"|"low"}]}.
Do not guess doses or add medicines that are not visible. If nothing is readable return {"medicines":[]}."""


# ---------------------------------------------------------------- blood

def blood_search(snap, group, units, lat, lon):
    group = group if group in BLOOD_GROUPS else "O+"
    units = max(1, min(int(units or 1), 20))
    compat = BLOOD_COMPAT[group]
    banks = []
    for f in snap["facilities"].values():
        if f["type"] != "bloodbank":
            continue
        km = haversine(lat, lon, f["lat"], f["lon"])
        reported = bool(f["blood"])
        exact = f["blood"][group]["units"] if group in f["blood"] else None
        comp = {g: f["blood"][g]["units"] for g in compat if g != group and g in f["blood"] and f["blood"][g]["units"] > 0}
        updated = max([r.get("updatedAt", 0) for r in f["blood"].values()] or [0]) or None
        banks.append({"id": f["id"], "name": f["name"], "lat": f["lat"], "lon": f["lon"],
                      "locationPrecision": f.get("locationPrecision", "exact"),
                      "distanceKm": round(km, 1), "etaMin": eta_min(km), "reported": reported,
                      "exactUnits": exact, "compatibleUnits": comp, "enough": exact is not None and exact >= units,
                      "demo": any(r.get("demo") for r in f["blood"].values()),
                      "updatedAt": updated, "stale": bool(updated) and now() - updated > STALE_SECONDS})
    banks.sort(key=lambda b: (not b["enough"], not b["reported"], b["distanceKm"]))
    return {"group": group, "units": units, "compatibleGroups": compat, "banks": banks,
            "compatNote": "Standard ABO/Rh red-cell compatibility. The blood bank will cross-match before transfusion."}


# ---------------------------------------------------------------- equipment

def equipment_search(snap, etype, lat, lon):
    etype = etype if etype in EQUIP_TYPES else "CT"
    rows = []
    for f in snap["facilities"].values():
        if f["type"] != "hospital":
            continue
        e = f["equipment"].get(etype)
        km = haversine(lat, lon, f["lat"], f["lon"])
        rows.append({"id": f["id"], "name": f["name"], "lat": f["lat"], "lon": f["lon"],
                     "ownership": f.get("ownership", "government"), "distanceKm": round(km, 1), "etaMin": eta_min(km),
                     "status": e["status"] if e else "unknown", "updatedAt": e.get("updatedAt") if e else None,
                     "stale": bool(e) and not fresh(e), "demo": bool(e and e.get("demo"))})
    order = {"working": 0, "busy": 1, "unknown": 2, "down": 3}
    rows.sort(key=lambda r: (order[r["status"]], r["etaMin"]))
    return {"type": etype, "results": rows}


# ---------------------------------------------------------------- staff updates

STAFF_PROMPT = """You convert short hospital/pharmacy/blood-bank staff messages (Urdu, Roman Urdu or English) into structured updates.
Facility: {facility}
Allowed keys:
{resources}
Reply ONLY JSON: {{"changes":[...], "summaryEn":"...", "summaryUr":"..."}} where each change is one of:
{{"kind":"bed","key":"<department>","free":<int free beds>}}
{{"kind":"doctor","name":"Dr <name as written>","dept":"<department or null>","gender":"F"|"M"|null,"onDuty":true|false,"shiftEnds":"HH:MM" or null}}
{{"kind":"equipment","key":"<CT|MRI|XRay|Dialysis|Ventilator|Oxygen>","status":"working"|"down"|"busy"}}
{{"kind":"medicine","key":"<medicine key>","qty":<int>,"priceRs":<int or null>}}  (khatam / out of stock = 0; "20 packs aa gaye" = 20)
{{"kind":"blood","key":"<group>","units":<int>}}
Times like "8 baje" mean 20:00 if it is about evening duty, else 08:00. ONLY include changes the message states. Never invent."""


def facility_resources_text(f):
    lines = []
    if f["type"] == "hospital":
        lines.append("departments: " + ", ".join(f.get("departments", [])))
        lines.append("equipment: " + ", ".join(EQUIP_TYPES))
        if f["doctors"]:
            lines.append("doctors already listed: " + ", ".join(f"{v['name']} ({v.get('dept')})" for v in f["doctors"].values()))
    if f["type"] == "pharmacy":
        lines.append("medicine keys: " + ", ".join(f"{k} = {v['name']}" for k, v in CATALOG.items()))
    if f["type"] == "bloodbank":
        lines.append("blood groups: " + ", ".join(BLOOD_GROUPS))
    return "\n".join(lines)


def _doctor_key(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower().replace("dr ", "").replace("dr.", "")).strip("-")[:40] or "doctor"


def keyword_parse_staff(f, text):
    t = text.lower()
    changes = []
    if f["type"] == "hospital":
        for d in f.get("departments", []):
            dl = d.lower().split("/")[0]
            m = re.search(rf"{re.escape(dl[:5])}\w*[^.,]*?(\d+)\s*(bed|beds|bistar)[^.,]*?(khali|free|available)", t)
            if m:
                changes.append({"kind": "bed", "key": d, "free": int(m.group(1))})
            elif re.search(rf"{re.escape(dl[:5])}\w*[^.,]*?(full|bhar|koi bed nahi|no bed)", t):
                changes.append({"kind": "bed", "key": d, "free": 0})
        for e in EQUIP_TYPES:
            pat = r"x-?ray" if e == "XRay" else rf"\b{e.lower()}\b"
            if re.search(rf"{pat}[^.,]*?(kharab|down|band|out of order|not working)", t):
                changes.append({"kind": "equipment", "key": e, "status": "down"})
            elif re.search(rf"{pat}[^.,]*?(busy|rush|line)", t):
                changes.append({"kind": "equipment", "key": e, "status": "busy"})
            elif re.search(rf"{pat}[^.,]*?(theek|working|chal raha|fixed|chalu)", t):
                changes.append({"kind": "equipment", "key": e, "status": "working"})
        for m in re.finditer(r"\bdr\.?\s+([a-z]+(?:\s+[a-z]+)?)([^.,]*)", t):
            name_words = [w for w in m.group(1).split() if w not in ("ki", "ka", "ke", "ko", "aaj", "abhi")]
            rest = m.group(2)
            if not name_words:
                continue
            name = "Dr " + " ".join(w.capitalize() for w in name_words[:2] if not re.match(r"^\d", w))
            # department named next to the doctor, else the ward named elsewhere in the same message
            dept = next((d for d in f.get("departments", []) if d.lower().split("/")[0][:5] in rest), None) or \
                next((d for d in f.get("departments", []) if d != "Emergency" and d.lower().split("/")[0][:5] in t), None)
            if re.search(r"off|chali gay|chale gay|leave|chutti|nahi", rest):
                changes.append({"kind": "doctor", "name": name, "dept": dept, "onDuty": False})
            elif re.search(r"duty|on\b|aa gay|available|maujood", rest):
                hm = re.search(r"(\d{1,2})\s*baje", rest)
                shift = None
                if hm:
                    h = int(hm.group(1))
                    shift = f"{h + 12 if 5 <= h < 12 else h:02d}:00"
                changes.append({"kind": "doctor", "name": name, "dept": dept, "onDuty": True, "shiftEnds": shift})
    if f["type"] == "pharmacy":
        for k, m in CATALOG.items():
            brand = m["name"].split()[0].lower()
            if re.search(rf"\b{re.escape(brand)}\b[^.,]*?(khatam|out of stock|nahi hai|finished)", t):
                changes.append({"kind": "medicine", "key": k, "qty": 0})
            else:
                q = re.search(rf"\b{re.escape(brand)}\b[^.,]*?(\d+)\s*(pack|packs|box|dabba|strip)", t)
                if q:
                    changes.append({"kind": "medicine", "key": k, "qty": int(q.group(1))})
    if f["type"] == "bloodbank":
        for g in BLOOD_GROUPS:
            q = re.search(rf"(?<![a-z]){re.escape(g.lower())}\s*[^.,]*?(\d+)\s*(unit|bag|bottle)", t)
            if q:
                changes.append({"kind": "blood", "key": g, "units": int(q.group(1))})
    # keep first change per (kind, key/name)
    seen, out = set(), []
    for c in changes:
        k = (c["kind"], c.get("key") or c.get("name"))
        if k not in seen:
            seen.add(k)
            out.append(c)
    return out


def validate_changes(f, changes):
    """Keep only changes that fit this facility, with sane values. Returns normalized changes with labels."""
    ok = []
    depts = f.get("departments", [])
    for c in changes if isinstance(changes, list) else []:
        if not isinstance(c, dict):
            continue
        kind, key = c.get("kind"), c.get("key")
        try:
            if kind == "bed" and f["type"] == "hospital" and key in depts:
                free = max(0, min(int(c["free"]), 500))
                was = f["beds"].get(key, {}).get("free")
                ok.append({"kind": "bed", "key": key, "free": free,
                           "label": f"{key}: {free} free beds" + (f" (was {was})" if was is not None else " (first report)")})
            elif kind == "doctor" and f["type"] == "hospital":
                name = str(c.get("name") or "").strip()
                existing = f["doctors"].get(key) if key else None
                if existing and not name:
                    name = existing["name"]
                if not re.match(r"^(Dr\.?\s+)?[A-Za-z][A-Za-z .'-]{1,40}$", name):
                    continue
                if not name.lower().startswith("dr"):
                    name = "Dr " + name
                dkey = key if existing else _doctor_key(name)
                prev = f["doctors"].get(dkey, {})
                dept = c.get("dept") if c.get("dept") in depts else prev.get("dept")
                gender = c.get("gender") if c.get("gender") in ("F", "M") else prev.get("gender")
                on = bool(c.get("onDuty"))
                sh = c.get("shiftEnds") if isinstance(c.get("shiftEnds"), str) and re.match(r"^\d{2}:\d{2}$", c.get("shiftEnds") or "") else None
                ok.append({"kind": "doctor", "key": dkey, "name": name, "dept": dept, "gender": gender, "onDuty": on,
                           "shiftEnds": sh, "label": f"{name}{' (' + dept + ')' if dept else ''}: "
                                                     f"{'on duty' if on else 'off duty'}" + (f" until {sh}" if sh and on else "")})
            elif kind == "equipment" and f["type"] == "hospital" and key in EQUIP_TYPES and c.get("status") in ("working", "down", "busy"):
                was = f["equipment"].get(key, {}).get("status")
                ok.append({"kind": "equipment", "key": key, "status": c["status"],
                           "label": f"{key}: {c['status']}" + (f" (was {was})" if was else " (first report)")})
            elif kind == "medicine" and f["type"] == "pharmacy" and key in CATALOG:
                q = max(0, min(int(c["qty"]), 10000))
                price = c.get("priceRs")
                price = int(price) if isinstance(price, (int, float)) and 0 < price < 100000 else f["medicine"].get(key, {}).get("priceRs")
                ok.append({"kind": "medicine", "key": key, "qty": q, "priceRs": price,
                           "label": f"{CATALOG[key]['name']}: {q if q else 'out of stock'}" + (f" · Rs {price}" if price else "")})
            elif kind == "blood" and f["type"] == "bloodbank" and key in BLOOD_GROUPS:
                u = max(0, min(int(c["units"]), 500))
                ok.append({"kind": "blood", "key": key, "units": u, "label": f"Blood {key}: {u} units"})
        except (TypeError, ValueError, KeyError):
            continue
    return ok
