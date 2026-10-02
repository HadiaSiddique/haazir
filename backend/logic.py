"""Deterministic, explainable logic. AI understands language; this code decides."""
import math
import re
import time

import ai
from seed_data import MEDICINES, BLOOD_GROUPS

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
    for key, name, salt, strength, price in MEDICINES:
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


# ---------------------------------------------------------------- hospitals

def er_load(f):
    b = f["beds"].get("Emergency")
    if not b:
        return "Unknown"
    r = b["occupied"] / max(1, b["total"])
    return "Low" if r < 0.75 else ("Busy" if r < 0.95 else "Full")


def free_beds(f, dept):
    b = f["beds"].get(dept)
    return None if not b else max(0, b["total"] - b["occupied"])


def hospital_card(f, lat, lon, dept=None):
    km = haversine(lat, lon, f["lat"], f["lon"])
    on_duty = [d for d in f["doctors"].values() if d.get("onDuty")]
    dept_docs = [d for d in on_duty if not dept or d["dept"] == dept]
    beds = {k: {"free": max(0, v["total"] - v["occupied"]), "total": v["total"], "updatedAt": v["updatedAt"],
                "stale": not fresh(v)} for k, v in f["beds"].items()}
    last = max([r.get("updatedAt", 0) for g in ("beds", "doctors", "equipment") for r in f[g].values()] or [0])
    return {
        "id": f["id"], "name": f["name"], "nameUr": f.get("nameUr"), "lat": f["lat"], "lon": f["lon"],
        "phone": f.get("phone"), "sehatCard": f.get("sehatCard"), "ownership": f.get("ownership", "government"),
        "femaleDoctor": any(d["gender"] == "F" for d in (dept_docs if dept else on_duty)),
        "distanceKm": round(km, 1), "etaMin": eta_min(km), "erLoad": er_load(f),
        "department": dept, "freeBeds": free_beds(f, dept) if dept else None,
        "beds": beds,
        "doctorsOnDuty": [{"name": d["name"], "dept": d["dept"], "gender": d["gender"], "shiftEnds": d.get("shiftEnds")}
                          for d in (dept_docs or on_duty)][:4],
        "equipment": {k: {"status": v["status"], "queue": v.get("queue", 0), "stale": not fresh(v),
                          "updatedAt": v["updatedAt"]} for k, v in f["equipment"].items()},
        "updatedAt": last,
    }


def rank_hospitals(snap, lat, lon, dept=None, equipment=None, female=False, sehat=False, red_flag=False, ownership=None):
    dept = dept or ("Emergency" if red_flag else None)
    results = []
    for f in snap["facilities"].values():
        if f["type"] != "hospital":
            continue
        if dept and dept not in f["beds"]:
            continue
        if sehat and not f.get("sehatCard"):
            continue
        if ownership and f.get("ownership", "government") != ownership:
            continue
        card = hospital_card(f, lat, lon, dept)
        score, why = 0.0, []
        fb = card["freeBeds"]
        if dept:
            if fb == 0:
                score -= 100
                why.append(f"no free {dept} beds")
            else:
                score += min(fb, 5) * 4  # diminishing: 5+ free beds is "enough"
                why.append(f"{fb} free {dept} beds")
            specialists = [d for d in f["doctors"].values() if d.get("onDuty") and d["dept"] == dept]
            if specialists:
                score += 25
                why.append(f"{specialists[0]['name']} on duty")
            else:
                score -= 30
                why.append(f"no {dept} doctor on duty")
        if female:
            fem = [d for d in f["doctors"].values() if d.get("onDuty") and d["gender"] == "F"
                   and (not dept or d["dept"] == dept)]
            if fem:
                score += 15
                why.append(f"female doctor {fem[0]['name']} on duty")
            else:
                score -= 40
        if equipment:
            e = f["equipment"].get(equipment)
            if not e:
                score -= 60
            elif e["status"] == "working":
                score += 15
                why.append(f"{equipment} working")
            elif e["status"] == "busy":
                score += 3
                why.append(f"{equipment} busy (queue {e.get('queue', 0)})")
            else:
                score -= 40
                why.append(f"{equipment} down")
        load = card["erLoad"]
        score += {"Low": 10, "Busy": 0, "Full": -35 if red_flag else -15}.get(load, 0)
        if load == "Full":
            why.append("ER full")
        score -= card["etaMin"] * (2.5 if red_flag else 1.2)  # in emergencies every minute counts more
        card["score"] = round(score, 1)
        card["why"] = ", ".join(why[:3]) + f" · {card['etaMin']} min away"
        has_specialist = not dept or any(d.get("onDuty") and d["dept"] == dept for d in f["doctors"].values())
        card["canHelp"] = ((fb is None or fb > 0) and has_specialist
                           and not (equipment and f["equipment"].get(equipment, {}).get("status", "down") == "down"))
        results.append(card)
    results.sort(key=lambda c: -c["score"])
    return results


def minutes_saved(results):
    """+25 when the nearest relevant facility could not help and we routed elsewhere."""
    if len(results) < 2:
        return 0
    nearest = min(results, key=lambda c: c["distanceKm"])
    return 25 if (not nearest["canHelp"] and results[0]["id"] != nearest["id"]) else 0


# ---------------------------------------------------------------- medicine

CATALOG = {k: {"key": k, "name": n, "salt": s, "strength": st, "priceRs": p} for k, n, s, st, p in MEDICINES}


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
        return {"query": q, "matched": [], "pharmacies": [], "alternatives": [], "dispensaries": []}
    primary = keys[0]
    alt_keys = [k for k in same_salt(primary) if k != primary]
    pharmacies, dispensaries = [], []
    for f in snap["facilities"].values():
        if f["type"] not in ("pharmacy", "hospital"):
            continue
        km = haversine(lat, lon, f["lat"], f["lon"])
        stock = []
        for k in [primary] + alt_keys:
            r = f["medicine"].get(k)
            if r and r.get("inStock") and r.get("qty", 0) > 0:
                stock.append({"key": k, "name": r["name"], "qty": r["qty"], "priceRs": r["priceRs"],
                              "exact": k == primary, "stale": not fresh(r), "updatedAt": r["updatedAt"]})
        if not stock:
            continue
        row = {"id": f["id"], "name": f["name"], "type": f["type"], "lat": f["lat"], "lon": f["lon"],
               "distanceKm": round(km, 1), "etaMin": eta_min(km), "open24h": f.get("open24h"),
               "hasExact": any(s["exact"] for s in stock), "stock": stock}
        (dispensaries if f["type"] == "hospital" else pharmacies).append(row)
    pharmacies.sort(key=lambda p: (not p["hasExact"], p["distanceKm"]))
    dispensaries.sort(key=lambda p: p["distanceKm"])
    alts = sorted([CATALOG[k] for k in alt_keys], key=lambda m: m["priceRs"])
    return {"query": q, "matched": [CATALOG[primary]], "alternatives": alts,
            "pharmacies": pharmacies[:12], "dispensaries": dispensaries[:4],
            "note": "Same active ingredient and strength only. Confirm with your doctor or pharmacist before switching."}


def medicine_plan(snap, names, lat, lon):
    """Find one pharmacy with everything, else fewest stops (greedy set cover by distance)."""
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
                if r and r.get("inStock") and r.get("qty", 0) > 0:
                    have[k] = {"key": alt, "name": r["name"], "priceRs": r["priceRs"], "substitute": alt != k}
                    break
        if have:
            km = haversine(lat, lon, f["lat"], f["lon"])
            shops.append({"id": f["id"], "name": f["name"], "lat": f["lat"], "lon": f["lon"],
                          "distanceKm": round(km, 1), "etaMin": eta_min(km), "have": have})
    full = [s for s in shops if len(s["have"]) == len(set(keys))]
    full_exact = [s for s in full if not any(v["substitute"] for v in s["have"].values())]
    pick = sorted(full_exact or full, key=lambda s: s["distanceKm"])
    if keys and pick:
        s = pick[0]
        stops = [s]
    else:
        stops, remaining = [], set(keys)
        while remaining and shops:
            best = max(shops, key=lambda s: (len(remaining & set(s["have"])), -s["distanceKm"]))
            got = remaining & set(best["have"])
            if not got:
                break
            stops.append({**best, "have": {k: best["have"][k] for k in got}})
            remaining -= got
    total = sum(v["priceRs"] for s in stops for v in s["have"].values())
    covered = {k for s in stops for k in s["have"]}
    return {"items": wanted, "stops": stops, "onePharmacy": len(stops) == 1 and len(covered) == len(set(keys)) > 0,
            "missing": [w for w in wanted if not w["key"] or w["key"] not in covered],
            "totalRs": total,
            "note": "Substitutes have the same active ingredient and strength. Confirm with your doctor or pharmacist before switching."}


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
        exact = f["blood"].get(group, {}).get("units", 0)
        comp = {g: f["blood"].get(g, {}).get("units", 0) for g in compat if g != group}
        updated = max([r.get("updatedAt", 0) for r in f["blood"].values()] or [0])
        banks.append({"id": f["id"], "name": f["name"], "lat": f["lat"], "lon": f["lon"],
                      "distanceKm": round(km, 1), "etaMin": eta_min(km), "exactUnits": exact,
                      "compatibleUnits": {g: u for g, u in comp.items() if u > 0},
                      "enough": exact >= units, "updatedAt": updated, "stale": now() - updated > STALE_SECONDS})
    banks.sort(key=lambda b: (not b["enough"], b["exactUnits"] == 0, b["distanceKm"]))
    return {"group": group, "units": units, "compatibleGroups": compat, "banks": banks,
            "compatNote": "Standard ABO/Rh red-cell compatibility. The blood bank will cross-match before transfusion."}


# ---------------------------------------------------------------- equipment

def equipment_search(snap, etype, lat, lon):
    etype = etype if etype in EQUIP_TYPES else "CT"
    rows = []
    for f in snap["facilities"].values():
        e = f["equipment"].get(etype) if f["type"] == "hospital" else None
        if not e:
            continue
        km = haversine(lat, lon, f["lat"], f["lon"])
        q = e.get("queue", 0)
        rows.append({"id": f["id"], "name": f["name"], "lat": f["lat"], "lon": f["lon"],
                     "distanceKm": round(km, 1), "etaMin": eta_min(km), "status": e["status"], "queue": q,
                     "waitMin": q * 15 if e["status"] != "down" else None, "updatedAt": e["updatedAt"],
                     "stale": not fresh(e)})
    order = {"working": 0, "busy": 1, "down": 2}
    rows.sort(key=lambda r: (order[r["status"]], r["etaMin"] + (r["waitMin"] or 0)))
    return {"type": etype, "results": rows}


# ---------------------------------------------------------------- ambulance

def pick_ambulance(snap, lat, lon, als):
    avail = [a for a in snap["ambulances"].values() if a["status"] == "available"]
    pool = [a for a in avail if a["type"] == "ALS"] if als else []
    pool = pool or avail
    if not pool:
        return None
    return min(pool, key=lambda a: haversine(lat, lon, a["lat"], a["lon"]))


def ambulance_progress(req):
    """Simulated position: interpolate from start to patient, then patient to hospital."""
    t = now() - req["createdAt"]
    to_patient = req["toPatientSec"]
    to_hosp = req["toHospitalSec"]
    s, p, h = (req["startLat"], req["startLon"]), (req["lat"], req["lon"]), (req["destLat"], req["destLon"])
    timeline = [{"status": "assigned", "at": req["createdAt"]}]
    if t < 8:
        pos, status, eta = s, "assigned", to_patient
    elif t < to_patient:
        k = (t - 8) / max(1, to_patient - 8)
        pos, status, eta = (s[0] + (p[0] - s[0]) * k, s[1] + (p[1] - s[1]) * k), "en_route", to_patient - t
    elif t < to_patient + 30:
        pos, status, eta = p, "arrived", 0
    elif t < to_patient + 30 + to_hosp:
        k = (t - to_patient - 30) / max(1, to_hosp)
        pos, status, eta = (p[0] + (h[0] - p[0]) * k, p[1] + (h[1] - p[1]) * k), "to_hospital", to_patient + 30 + to_hosp - t
    else:
        pos, status, eta = h, "at_hospital", 0
    for st, at in [("en_route", 8), ("arrived", to_patient), ("to_hospital", to_patient + 30),
                   ("at_hospital", to_patient + 30 + to_hosp)]:
        if t >= at:
            timeline.append({"status": st, "at": req["createdAt"] + at})
    return {"status": status, "lat": pos[0], "lon": pos[1], "etaSec": max(0, int(eta)), "timeline": timeline}


# ---------------------------------------------------------------- staff updates

STAFF_PROMPT = """You convert short hospital/pharmacy/blood-bank staff messages (Urdu, Roman Urdu or English) into structured updates.
Facility resources (use ONLY these keys):
{resources}
Reply ONLY JSON: {{"changes":[...], "summaryEn":"...", "summaryUr":"..."}} where each change is one of:
{{"kind":"bed","key":"<department>","free":<int free beds>}}
{{"kind":"doctor","key":"<doctor key>","onDuty":true|false,"shiftEnds":"HH:MM" or null}}
{{"kind":"equipment","key":"<CT|MRI|XRay|Dialysis|Ventilator|Oxygen>","status":"working"|"down"|"busy"}}
{{"kind":"medicine","key":"<medicine key>","qty":<int>}}  (khatam / out of stock = 0; "20 packs aa gaye" = 20)
{{"kind":"blood","key":"<group>","units":<int>}}
Times like "8 baje" mean 20:00 if it is about evening duty, else 08:00. Do not invent changes that the message does not state."""


def facility_resources_text(f):
    lines = []
    if f["beds"]:
        lines.append("beds: " + ", ".join(f"{k} (total {v['total']})" for k, v in f["beds"].items()))
    if f["doctors"]:
        lines.append("doctors: " + ", ".join(f"{k} = {v['name']} ({v['dept']})" for k, v in f["doctors"].items()))
    if f["equipment"]:
        lines.append("equipment: " + ", ".join(f["equipment"].keys()))
    if f["medicine"]:
        lines.append("medicine keys: " + ", ".join(f"{k} = {v['name']}" for k, v in f["medicine"].items()))
    if f["blood"]:
        lines.append("blood groups: " + ", ".join(f["blood"].keys()))
    return "\n".join(lines)


def keyword_parse_staff(f, text):
    t = text.lower()
    changes = []
    for d in f["beds"]:
        dl = d.lower().split("/")[0]
        m = re.search(rf"{re.escape(dl[:5])}\w*[^.,]*?(\d+)\s*(bed|beds|bistar)[^.,]*?(khali|free|available)", t)
        if m:
            changes.append({"kind": "bed", "key": d, "free": int(m.group(1))})
        elif re.search(rf"{re.escape(dl[:5])}\w*[^.,]*?(full|bhar|koi bed nahi)", t):
            changes.append({"kind": "bed", "key": d, "free": 0})
    for e in f["equipment"]:
        if re.search(rf"\b{e.lower()}\b[^.,]*?(kharab|down|band|out of order|not working)", t):
            changes.append({"kind": "equipment", "key": e, "status": "down"})
        elif re.search(rf"\b{e.lower()}\b[^.,]*?(theek|working|chal raha|fixed|on)", t):
            changes.append({"kind": "equipment", "key": e, "status": "working"})
    for k, d in f["doctors"].items():
        first = d["name"].lower().replace("dr ", "").split()[0]
        if re.search(rf"\b{first}\b[^.,]*?(off duty|chali gay|chale gay|leave|chutti|\boff\b)", t):
            changes.append({"kind": "doctor", "key": k, "onDuty": False, "shiftEnds": None})
        elif re.search(rf"\b{first}\b[^.,]*?(duty|\bon\b|aa gay|available)", t):
            hm = re.search(rf"\b{first}\b[^.,]*?(\d{{1,2}})\s*baje", t)
            shift = None
            if hm:
                h = int(hm.group(1))
                shift = f"{h + 12 if h < 12 and h >= 5 else h:02d}:00"
            changes.append({"kind": "doctor", "key": k, "onDuty": True, "shiftEnds": shift})

    for k, m in f["medicine"].items():
        brand = m["name"].split()[0].lower()
        if re.search(rf"\b{brand}\b[^.,]*?(khatam|out of stock|nahi hai|finished)", t):
            changes.append({"kind": "medicine", "key": k, "qty": 0})
        else:
            q = re.search(rf"\b{brand}\b[^.,]*?(\d+)\s*(pack|packs|box|dabba|strip)", t)
            if q:
                changes.append({"kind": "medicine", "key": k, "qty": int(q.group(1))})
    for g in f["blood"]:
        q = re.search(rf"{re.escape(g.lower())}\s*[^.,]*?(\d+)\s*(unit|bag|bottle)", t)
        if q:
            changes.append({"kind": "blood", "key": g, "units": int(q.group(1))})
    return changes


def validate_changes(f, changes):
    """Keep only changes that refer to real resources of this facility, with sane values."""
    ok = []
    for c in changes if isinstance(changes, list) else []:
        if not isinstance(c, dict):
            continue
        kind, key = c.get("kind"), c.get("key")
        try:
            if kind == "bed" and key in f["beds"]:
                free = max(0, min(int(c["free"]), f["beds"][key]["total"]))
                ok.append({"kind": "bed", "key": key, "free": free,
                           "label": f"{key}: {free} free beds (was {f['beds'][key]['total'] - f['beds'][key]['occupied']})"})
            elif kind == "doctor" and key in f["doctors"]:
                on = bool(c.get("onDuty"))
                sh = c.get("shiftEnds") if isinstance(c.get("shiftEnds"), str) and re.match(r"^\d{2}:\d{2}$", c.get("shiftEnds") or "") else None
                ok.append({"kind": "doctor", "key": key, "onDuty": on, "shiftEnds": sh,
                           "label": f"{f['doctors'][key]['name']}: {'on duty' if on else 'off duty'}" + (f" until {sh}" if sh and on else "")})
            elif kind == "equipment" and key in f["equipment"] and c.get("status") in ("working", "down", "busy"):
                ok.append({"kind": "equipment", "key": key, "status": c["status"],
                           "label": f"{key}: {c['status']} (was {f['equipment'][key]['status']})"})
            elif kind == "medicine" and key in f["medicine"]:
                q = max(0, min(int(c["qty"]), 10000))
                ok.append({"kind": "medicine", "key": key, "qty": q,
                           "label": f"{f['medicine'][key]['name']}: {q if q else 'out of stock'}"})
            elif kind == "blood" and key in f["blood"]:
                u = max(0, min(int(c["units"]), 500))
                ok.append({"kind": "blood", "key": key, "units": u, "label": f"Blood {key}: {u} units"})
        except (TypeError, ValueError, KeyError):
            continue
    return ok
