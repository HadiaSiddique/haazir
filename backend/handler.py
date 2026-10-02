"""Haazir API: one Lambda behind an HTTP API, routed by method + path."""
import base64
import json
import os
import re
import urllib.parse
import uuid

import ai
import db
import logic
import sim
from seed_data import build_items

STAFF_PIN = os.environ.get("STAFF_PIN", "1234")
GROUP_RE = re.compile(r"^(A|B|AB|O)[+-]$")


class BadRequest(Exception):
    pass


def resp(code, body):
    return {"statusCode": code, "headers": {"content-type": "application/json", "cache-control": "no-store"},
            "body": json.dumps(body, default=str)}


def body_of(event):
    raw = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode("utf-8", "replace")
    if len(raw) > 6_000_000:
        raise BadRequest("Request too large")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise BadRequest("Invalid JSON")
    if not isinstance(data, dict):
        raise BadRequest("JSON object expected")
    return data


def qs(event):
    return event.get("queryStringParameters") or {}


def text_arg(v, n=500):
    return str(v or "").strip()[:n]


def require_staff(data, snap):
    fid = text_arg(data.get("facilityId"), 60)
    if str(data.get("pin", "")) != STAFF_PIN:
        raise PermissionError("Wrong PIN")
    f = snap["facilities"].get(fid)
    if not f:
        raise BadRequest("Unknown facility")
    return f


# ------------------------------------------------------------------ routes

def r_ask(event):
    data = body_of(event)
    text = text_arg(data.get("text"))
    if not text:
        raise BadRequest("Please type what you need")
    lat, lon = logic.loc(data.get("lat"), data.get("lon"))
    intent, ent, source = logic.understand(text)
    area = (ent.get("area") or "").lower().strip()
    if area in logic.AREAS:
        lat, lon = logic.AREAS[area]
    snap = db.snapshot()
    out = {"intent": intent, "entities": ent, "understoodBy": source, "lat": lat, "lon": lon,
           "reasonEn": ent.get("reasonEn"), "reasonUr": ent.get("reasonUr")}
    counters = {"searches": 1}
    if intent == "medicine":
        q = (ent.get("medicines") or [text])[0]
        out["medicine"] = logic.medicine_search(snap, q, lat, lon)
        counters["medicineSearches"] = 1
    elif intent == "blood":
        out["blood"] = logic.blood_search(snap, ent.get("bloodGroup") or "O+", ent.get("units") or 1, lat, lon)
    elif intent == "test_equipment":
        out["equipment"] = logic.equipment_search(snap, ent.get("testType"), lat, lon)
    else:
        res = logic.rank_hospitals(snap, lat, lon, dept=ent.get("department"), equipment=ent.get("testType"),
                                   female=ent.get("femaleDoctor"), sehat=False, red_flag=ent.get("redFlag"))
        if not res and ent.get("femaleDoctor"):
            res = logic.rank_hospitals(snap, lat, lon, dept=None, female=True)
        out["hospitals"] = res[:8]
        saved = logic.minutes_saved(res)
        if saved:
            counters["estMinutesSaved"] = saved
            out["minutesSaved"] = saved
    if not out.get("reasonEn"):
        out["reasonEn"] = fallback_reason(intent, ent)
    db.bump(**counters)
    return out


def fallback_reason(intent, ent):
    if ent.get("redFlag"):
        return f"Possible emergency ({ent.get('redFlagReason')}). Showing hospitals with free {ent.get('department') or 'Emergency'} beds."
    return {
        "medicine": "Looking for medicine stock at nearby pharmacies.",
        "blood": f"Looking for {ent.get('bloodGroup') or 'blood'} at blood banks.",
        "test_equipment": f"Looking for a working {ent.get('testType') or 'machine'} right now.",
        "ambulance": "Finding the nearest available ambulance.",
        "doctor": "Looking for doctors on duty now.",
    }.get(intent, f"Looking for hospitals with free {ent.get('department') or ''} beds.".replace("  ", " "))


def r_hospitals(event):
    q = qs(event)
    lat, lon = logic.loc(q.get("lat"), q.get("lon"))
    dept = q.get("dept") if q.get("dept") in logic.DEPARTMENTS else None
    eq = q.get("equipment") if q.get("equipment") in logic.EQUIP_TYPES else None
    return {"hospitals": logic.rank_hospitals(db.snapshot(), lat, lon, dept=dept, equipment=eq,
                                              female=q.get("female") == "1", sehat=q.get("sehat") == "1")}


def r_facility(event, fid):
    q = qs(event)
    lat, lon = logic.loc(q.get("lat"), q.get("lon"))
    snap = db.snapshot()
    f = snap["facilities"].get(fid)
    if not f:
        return resp(404, {"error": "Facility not found"})
    card = logic.hospital_card(f, lat, lon) if f["type"] == "hospital" else {
        "id": f["id"], "name": f["name"], "lat": f["lat"], "lon": f["lon"],
        "distanceKm": round(logic.haversine(lat, lon, f["lat"], f["lon"]), 1)}
    card["type"] = f["type"]
    card["doctors"] = sorted(f["doctors"].values(), key=lambda d: (not d.get("onDuty"), d["dept"]))
    card["medicine"] = sorted(f["medicine"].values(), key=lambda m: m["name"])
    card["blood"] = f["blood"]
    card["open24h"] = f.get("open24h")
    updates = []
    for g in ("beds", "doctors", "equipment", "medicine", "blood"):
        for r in f[g].values():
            updates.append({"what": f"{r.get('kind')}: {r.get('name') or r.get('key')}", "by": r.get("updatedBy"),
                            "at": r.get("updatedAt")})
    card["recentUpdates"] = sorted(updates, key=lambda u: -(u["at"] or 0))[:8]
    return card


def r_facilities(event):
    snap = db.snapshot()
    t = qs(event).get("type")
    return {"facilities": [{"id": f["id"], "name": f["name"], "type": f["type"]} for f in
                           sorted(snap["facilities"].values(), key=lambda f: (f["type"], f["name"]))
                           if not t or f["type"] == t]}


def r_ambulance_request(event):
    data = body_of(event)
    lat, lon = logic.loc(data.get("lat"), data.get("lon"))
    condition = text_arg(data.get("condition"), 300) or "Emergency"
    snap = db.snapshot(force=True)
    _, ent = logic.keyword_understand(condition)
    red = bool(data.get("redFlag")) or ent["redFlag"]
    amb = logic.pick_ambulance(snap, lat, lon, als=red)
    if not amb:
        return resp(409, {"error": "No demo ambulance free right now. Call Rescue 1122.", "call": "1122"})
    dest_id = text_arg(data.get("destinationHospitalId"), 60)
    dest = snap["facilities"].get(dest_id) if dest_id else None
    dept = data.get("department") if data.get("department") in logic.DEPARTMENTS else ent["department"]
    if not dest or dest["type"] != "hospital":
        ranked = logic.rank_hospitals(snap, lat, lon, dept=dept, red_flag=True)
        dest = snap["facilities"][ranked[0]["id"]]
    km_pt = logic.haversine(amb["lat"], amb["lon"], lat, lon)
    km_h = logic.haversine(lat, lon, dest["lat"], dest["lon"])
    # simulated travel times (compressed for the demo, capped so the map visibly moves)
    to_patient = int(max(45, min(180, logic.eta_min(km_pt, 35) * 60 / 4)))
    to_hosp = int(max(45, min(180, logic.eta_min(km_h, 35) * 60 / 4)))
    rid = "R" + uuid.uuid4().hex[:6].upper()
    summary = ai.converse_text(
        "Write ONE short line (max 25 words) for hospital emergency staff about an incoming patient. "
        "No diagnosis; describe the reported problem only.",
        f"Reported: {condition}. Red flag: {ent.get('redFlagReason') or 'none'}. Ambulance type: {amb['type']}.") \
        or f"Incoming {amb['type']} ambulance: reported '{condition[:80]}'" + (f" ({ent['redFlagReason']})" if red else "")
    now = logic.now()
    req = {"pk": f"REQUEST#{rid}", "sk": "META", "id": rid, "type": "ambulance", "createdAt": now,
           "condition": condition, "redFlag": red, "ambulanceId": amb["id"], "ambulanceType": amb["type"],
           "startLat": amb["lat"], "startLon": amb["lon"], "lat": lat, "lon": lon,
           "destId": dest["id"], "destName": dest["name"], "destLat": dest["lat"], "destLon": dest["lon"],
           "toPatientSec": to_patient, "toHospitalSec": to_hosp, "summary": summary,
           "realEtaMin": logic.eta_min(km_pt, 35)}
    db.put(req)
    db.update_fields(f"AMBULANCE#{amb['id']}", "META", {"status": "enroute", "requestId": rid, "updatedAt": now})
    create_alert(dest["id"], dept or "Emergency", f"Ambulance {amb['id']} ({amb['type']}) bringing patient. {summary}",
                 eta=to_patient + to_hosp, source="ambulance", ref=rid)
    db.bump(ambulanceRequests=1)
    return {"requestId": rid, "ambulance": {"id": amb["id"], "type": amb["type"]},
            "destination": {"id": dest["id"], "name": dest["name"]}, "summary": summary, "hospitalAlerted": True}


def r_ambulances(event):
    """Nearby demo ambulances with distance and simulated ETA (35 km/h with sirens in Lahore traffic)."""
    q = qs(event)
    lat, lon = logic.loc(q.get("lat"), q.get("lon"))
    rows = []
    for a in db.snapshot()["ambulances"].values():
        km = logic.haversine(lat, lon, a["lat"], a["lon"])
        rows.append({"id": a["id"], "type": a["type"], "status": a["status"], "lat": a["lat"], "lon": a["lon"],
                     "distanceKm": round(km, 1), "etaMin": logic.eta_min(km, 35), "updatedAt": a.get("updatedAt")})
    rows.sort(key=lambda r: (r["status"] != "available", r["distanceKm"]))
    avail = [r for r in rows if r["status"] == "available"]
    return {"ambulances": rows, "available": len(avail), "total": len(rows),
            "nearest": avail[0] if avail else None,
            "nearestALS": next((r for r in avail if r["type"] == "ALS"), None)}


def r_ambulance_status(event, rid):
    req = db.get(f"REQUEST#{rid}")
    if not req:
        return resp(404, {"error": "Request not found"})
    prog = logic.ambulance_progress(req)
    return {"requestId": rid, **prog, "ambulance": {"id": req["ambulanceId"], "type": req["ambulanceType"]},
            "patient": {"lat": req["lat"], "lon": req["lon"]},
            "destination": {"id": req["destId"], "name": req["destName"], "lat": req["destLat"], "lon": req["destLon"]},
            "summary": req.get("summary"), "condition": req.get("condition"), "realEtaMin": req.get("realEtaMin")}


def create_alert(fid, dept, note, eta=None, source="notify", ref=None):
    aid = "A" + uuid.uuid4().hex[:6].upper()
    now = logic.now()
    db.put({"pk": f"ALERT#{fid}", "sk": f"{now:012d}#{aid}", "id": aid, "facilityId": fid, "department": dept,
            "note": note[:400], "etaSec": eta, "source": source, "ref": ref, "createdAt": now, "ack": False})
    return aid


def r_notify(event):
    data = body_of(event)
    fid = text_arg(data.get("facilityId"), 60)
    snap = db.snapshot()
    if fid not in snap["facilities"]:
        raise BadRequest("Unknown facility")
    dept = data.get("department") if data.get("department") in logic.DEPARTMENTS else "Emergency"
    note = text_arg(data.get("note"), 300) or "Patient on the way"
    try:
        eta = max(0, min(int(data.get("eta") or 0), 600)) * 60
    except (TypeError, ValueError):
        eta = None
    aid = create_alert(fid, dept, f"Family on the way: {note}", eta=eta, source="family")
    db.bump(notifications=1)
    return {"referenceCode": aid, "facility": snap["facilities"][fid]["name"], "department": dept}


def r_medicine_search(event):
    q = qs(event)
    lat, lon = logic.loc(q.get("lat"), q.get("lon"))
    name = text_arg(q.get("q"), 100)
    if not name:
        raise BadRequest("Type a medicine name")
    db.bump(medicineSearches=1, searches=1)
    return logic.medicine_search(db.snapshot(), name, lat, lon)


def r_medicine_plan(event):
    data = body_of(event)
    lat, lon = logic.loc(data.get("lat"), data.get("lon"))
    names = [text_arg(n, 80) for n in (data.get("items") or []) if text_arg(n, 80)]
    if not names:
        raise BadRequest("Add at least one medicine")
    return logic.medicine_plan(db.snapshot(), names, lat, lon)


def r_prescription(event):
    data = body_of(event)
    img = data.get("imageBase64") or ""
    if "," in img[:100]:
        img = img.split(",", 1)[1]
    if not img or len(img) > 5_500_000:
        raise BadRequest("Please upload a photo under 4 MB")
    fmt = "png" if img.startswith("iVBOR") else ("webp" if img.startswith("UklGR") else "jpeg")
    parsed = ai.converse_json(logic.RX_PROMPT, "Read the medicines in this image.", image_b64=img, image_format=fmt)
    meds = (parsed or {}).get("medicines") if isinstance(parsed, dict) else None
    if meds is None:
        return {"medicines": [], "aiAvailable": False,
                "message": "Could not read the photo right now. Please type the medicine names."}
    clean = []
    for m in meds[:10]:
        if isinstance(m, dict) and m.get("name"):
            label = text_arg(m["name"], 60) + (f" {m['strength']}" if m.get("strength") and str(m["strength"]) not in m["name"] else "")
            keys = logic.match_medicine(label)
            clean.append({"name": label, "confidence": m.get("confidence", "medium"),
                          "matched": logic.CATALOG[keys[0]]["name"] if keys else None})
    db.bump(medicineSearches=1)
    return {"medicines": clean, "aiAvailable": True}


def r_blood_search(event):
    q = qs(event)
    lat, lon = logic.loc(q.get("lat"), q.get("lon"))
    g = (q.get("group") or "O+").upper().replace(" ", "+")
    if not GROUP_RE.match(g):
        raise BadRequest("Unknown blood group")
    try:
        units = int(q.get("units") or 1)
    except ValueError:
        units = 1
    return logic.blood_search(db.snapshot(), g, units, lat, lon)


def r_blood_request(event):
    data = body_of(event)
    g = text_arg(data.get("group"), 4).upper()
    if not GROUP_RE.match(g):
        raise BadRequest("Unknown blood group")
    try:
        units = max(1, min(int(data.get("units") or 1), 20))
    except (TypeError, ValueError):
        units = 1
    hospital = text_arg(data.get("hospital"), 80) or "[hospital]"
    contact = text_arg(data.get("contact"), 40) or "[contact number]"
    rid = "B" + uuid.uuid4().hex[:6].upper()
    db.put({"pk": f"REQUEST#{rid}", "sk": "META", "id": rid, "type": "blood", "group": g, "units": units,
            "hospital": hospital, "createdAt": logic.now()})
    db.bump(bloodRequests=1)
    msg = (f"URGENT: {units} unit(s) of {g} blood needed at {hospital}, Lahore. "
           f"Please contact {contact}. Ref {rid}. (via Haazir)")
    msg_ur = f"فوری ضرورت: {hospital}، لاہور میں {g} خون کی {units} بوتل درکار ہے۔ رابطہ: {contact}"
    return {"requestId": rid, "message": msg, "messageUr": msg_ur,
            "whatsappUrl": "https://wa.me/?text=" + urllib.parse.quote(msg + "\n" + msg_ur)}


def r_equipment(event):
    q = qs(event)
    lat, lon = logic.loc(q.get("lat"), q.get("lon"))
    return logic.equipment_search(db.snapshot(), q.get("type"), lat, lon)


def apply_changes(f, changes, who="staff portal"):
    now = logic.now()
    pk = f"FACILITY#{f['id']}"
    for c in changes:
        k = c["kind"]
        if k == "bed":
            total = f["beds"][c["key"]]["total"]
            db.update_fields(pk, f"RES#bed#{c['key']}", {"occupied": total - c["free"], "updatedAt": now, "updatedBy": who})
        elif k == "doctor":
            fields = {"onDuty": c["onDuty"], "updatedAt": now, "updatedBy": who}
            if c.get("shiftEnds"):
                fields["shiftEnds"] = c["shiftEnds"]
            db.update_fields(pk, f"RES#doctor#{c['key']}", fields)
        elif k == "equipment":
            db.update_fields(pk, f"RES#equipment#{c['key']}", {"status": c["status"], "updatedAt": now, "updatedBy": who})
        elif k == "medicine":
            db.update_fields(pk, f"RES#medicine#{c['key']}", {"qty": c["qty"], "inStock": c["qty"] > 0,
                                                              "updatedAt": now, "updatedBy": who})
        elif k == "blood":
            db.update_fields(pk, f"RES#blood#{c['key']}", {"units": c["units"], "updatedAt": now, "updatedBy": who})
    db.bump(staffUpdates=len(changes))
    db.invalidate()


def r_staff_parse(event):
    data = body_of(event)
    snap = db.snapshot(force=True)
    f = require_staff(data, snap)
    text = text_arg(data.get("text"), 500)
    if not text:
        raise BadRequest("Type an update")
    parsed = ai.converse_json(logic.STAFF_PROMPT.format(resources=logic.facility_resources_text(f)), text)
    source = "ai"
    raw = parsed.get("changes") if isinstance(parsed, dict) else None
    changes = logic.validate_changes(f, raw) if raw is not None else []
    if not changes:
        changes = logic.validate_changes(f, logic.keyword_parse_staff(f, text))
        source = "keywords"
    return {"changes": changes, "understoodBy": source,
            "summaryEn": (parsed or {}).get("summaryEn") if isinstance(parsed, dict) else None,
            "summaryUr": (parsed or {}).get("summaryUr") if isinstance(parsed, dict) else None}


def r_staff_update(event):
    data = body_of(event)
    snap = db.snapshot(force=True)
    f = require_staff(data, snap)
    changes = data.get("changes") or []
    # direct +/- controls send deltas for beds
    normalized = []
    for c in changes if isinstance(changes, list) else []:
        if isinstance(c, dict) and c.get("kind") == "bed" and "delta" in c and c.get("key") in f["beds"]:
            b = f["beds"][c["key"]]
            try:
                normalized.append({"kind": "bed", "key": c["key"],
                                   "free": b["total"] - b["occupied"] + int(c["delta"])})
            except (TypeError, ValueError):
                pass
        elif isinstance(c, dict) and c.get("kind") == "medicine" and "delta" in c and c.get("key") in f["medicine"]:
            try:
                normalized.append({"kind": "medicine", "key": c["key"],
                                   "qty": f["medicine"][c["key"]]["qty"] + int(c["delta"])})
            except (TypeError, ValueError):
                pass
        elif isinstance(c, dict) and c.get("kind") == "blood" and "delta" in c and c.get("key") in f["blood"]:
            try:
                normalized.append({"kind": "blood", "key": c["key"],
                                   "units": f["blood"][c["key"]]["units"] + int(c["delta"])})
            except (TypeError, ValueError):
                pass
        else:
            normalized.append(c)
    valid = logic.validate_changes(f, normalized)
    if not valid:
        raise BadRequest("Nothing to update")
    apply_changes(f, valid)
    return {"applied": valid, "facility": r_facility({"queryStringParameters": {}}, f["id"])}


def r_staff_alerts(event):
    snap = db.snapshot()
    f = require_staff(body_of(event), snap)
    alerts = db.query_pk(f"ALERT#{f['id']}", limit=30)
    return {"alerts": [{k: v for k, v in a.items() if k not in ("pk",)} for a in alerts]}


def r_staff_ack(event):
    data = body_of(event)
    snap = db.snapshot()
    f = require_staff(data, snap)
    sk = text_arg(data.get("sk"), 60)
    if not re.match(r"^\d{12}#A[0-9A-F]{6}$", sk):
        raise BadRequest("Bad alert id")
    db.update_fields(f"ALERT#{f['id']}", sk, {"ack": True, "ackAt": logic.now()})
    return {"ok": True}


def r_login(event):
    data = body_of(event)
    f = require_staff(data, db.snapshot())
    return {"ok": True, "facility": {"id": f["id"], "name": f["name"], "type": f["type"]}}


def r_stats(event):
    snap = db.snapshot()
    hosp = [f for f in snap["facilities"].values() if f["type"] == "hospital"]
    free_by_dept = {}
    full = []
    down = []
    for f in hosp:
        for d, b in f["beds"].items():
            free_by_dept[d] = free_by_dept.get(d, 0) + max(0, b["total"] - b["occupied"])
        if logic.er_load(f) == "Full":
            full.append(f["name"])
        for e, v in f["equipment"].items():
            if v["status"] == "down":
                down.append({"hospital": f["name"], "equipment": e})
    blood = {}
    for f in snap["facilities"].values():
        if f["type"] == "bloodbank":
            for g, v in f["blood"].items():
                blood[g] = blood.get(g, 0) + v["units"]
    amb = list(snap["ambulances"].values())
    return {
        "freeBedsTotal": sum(free_by_dept.values()), "freeBedsByDept": free_by_dept,
        "hospitalsFull": full, "machinesDown": down,
        "ambulancesAvailable": sum(1 for a in amb if a["status"] == "available"), "ambulancesTotal": len(amb),
        "bloodUnits": blood, "bloodShortages": [g for g, u in blood.items() if u < 5],
        "counters": snap.get("stats", {}),
        "facilities": len(snap["facilities"]), "updatedAt": logic.now(),
    }


def r_map(event):
    snap = db.snapshot()
    pts = []
    for f in snap["facilities"].values():
        p = {"id": f["id"], "name": f["name"], "type": f["type"], "lat": f["lat"], "lon": f["lon"]}
        if f["type"] == "hospital":
            tot = sum(b["total"] for b in f["beds"].values())
            occ = sum(b["occupied"] for b in f["beds"].values())
            p["capacity"] = round(occ / max(1, tot), 2)
            p["freeBeds"] = tot - occ
            p["erLoad"] = logic.er_load(f)
        pts.append(p)
    ambs = [{"id": a["id"], "type": a["type"], "status": a["status"], "lat": a["lat"], "lon": a["lon"]}
            for a in snap["ambulances"].values()]
    return {"facilities": pts, "ambulances": ambs}


ROUTES = [
    ("POST", r"^/ask$", r_ask),
    ("GET", r"^/hospitals$", r_hospitals),
    ("GET", r"^/facilities$", r_facilities),
    ("GET", r"^/facility/([\w-]+)$", r_facility),
    ("GET", r"^/ambulances$", r_ambulances),
    ("POST", r"^/ambulance/request$", r_ambulance_request),
    ("GET", r"^/ambulance/request/(R[0-9A-F]{6})$", r_ambulance_status),
    ("POST", r"^/notify$", r_notify),
    ("GET", r"^/medicine/search$", r_medicine_search),
    ("POST", r"^/medicine/plan$", r_medicine_plan),
    ("POST", r"^/medicine/prescription$", r_prescription),
    ("GET", r"^/blood/search$", r_blood_search),
    ("POST", r"^/blood/request$", r_blood_request),
    ("GET", r"^/equipment$", r_equipment),
    ("POST", r"^/staff/login$", r_login),
    ("POST", r"^/staff/parse$", r_staff_parse),
    ("POST", r"^/staff/update$", r_staff_update),
    ("POST", r"^/staff/alerts$", r_staff_alerts),
    ("POST", r"^/staff/alerts/ack$", r_staff_ack),
    ("GET", r"^/stats$", r_stats),
    ("GET", r"^/map$", r_map),
    ("GET", r"^/health$", lambda e: {"ok": True, "model": ai.MODEL_ID, "time": logic.now()}),
]


# The site can also be served straight from this Lambda (same origin as the API), so the app stays
# reachable even before/without CloudFront. Files are copied into backend/static by deploy.ps1.
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
STATIC = {"/": ("index.html", "text/html; charset=utf-8"), "/index.html": ("index.html", "text/html; charset=utf-8"),
          "/app.js": ("app.js", "application/javascript; charset=utf-8"),
          "/styles.css": ("styles.css", "text/css; charset=utf-8"),
          "/config.js": (None, "application/javascript"), "/og.png": ("og.png", "image/png")}


def static_file(path):
    name, ctype = STATIC[path]
    headers = {"content-type": ctype, "cache-control": "public, max-age=60"}
    if name is None:
        return {"statusCode": 200, "headers": headers, "body": "window.HAAZIR_API = '';"}
    fp = os.path.join(STATIC_DIR, name)
    if not os.path.exists(fp):
        return resp(404, {"error": "Not found"})
    with open(fp, "rb") as fh:
        data = fh.read()
    if ctype.startswith("image/"):
        return {"statusCode": 200, "headers": headers, "isBase64Encoded": True, "body": base64.b64encode(data).decode()}
    return {"statusCode": 200, "headers": headers, "body": data.decode("utf-8")}


def api(event, context=None):
    # direct invocations (deploy script)
    if event.get("action") == "seed":
        items = build_items()
        keep = {(i["pk"], i["sk"]) for i in items}
        stale = [(i["pk"], i["sk"]) for i in db._scan_all()
                 if i["pk"].startswith(("FACILITY#", "AMBULANCE#")) and (i["pk"], i["sk"]) not in keep]
        db.batch_delete(stale)
        db.batch_write(items)
        return {"seeded": len(items), "removedStale": len(stale)}
    if event.get("action") == "simulate" or event.get("source") == "aws.events":
        return sim.run()
    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")
    path = event.get("rawPath", "/")
    path = re.sub(r"^/api", "", path).rstrip("/") or "/"
    if method == "OPTIONS":
        return resp(204, {})
    if method == "GET" and path in STATIC:
        return static_file(path)
    for m, pat, fn in ROUTES:
        mt = re.match(pat, path)
        if m == method and mt:
            try:
                out = fn(event, *mt.groups())
                return out if isinstance(out, dict) and "statusCode" in out else resp(200, out)
            except BadRequest as e:
                return resp(400, {"error": str(e)})
            except PermissionError as e:
                return resp(403, {"error": str(e)})
            except Exception as e:
                print("ERROR", path, type(e).__name__, e)
                import traceback
                traceback.print_exc()
                return resp(500, {"error": "Something went wrong. Please try again."})
    return resp(404, {"error": "Not found"})
