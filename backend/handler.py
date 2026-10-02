"""Haazir API: one Lambda behind an HTTP API, routed by method + path.

Facilities are real (hospitals, pharmacies, blood banks). Availability exists only when staff report it."""
import base64
import json
import os
import re
import urllib.parse
import uuid

import ai
import db
import logic
from seed_data import HELPLINES, build_items

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
           "reasonEn": ent.get("reasonEn"), "reasonUr": ent.get("reasonUr"), "helplines": HELPLINES}
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
                                   female=ent.get("femaleDoctor"), red_flag=ent.get("redFlag") or intent == "ambulance")
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
        return f"Possible emergency ({ent.get('redFlagReason')}). Showing the nearest hospitals with {ent.get('department') or 'Emergency'}."
    return {
        "medicine": "Looking for this medicine at pharmacies that have reported stock.",
        "blood": f"Looking for {ent.get('bloodGroup') or 'blood'} at blood banks.",
        "test_equipment": f"Looking for a working {ent.get('testType') or 'machine'}.",
        "ambulance": "Call an ambulance helpline. Below are the nearest hospitals with an emergency department.",
        "doctor": "Looking for doctors reported on duty.",
    }.get(intent, f"Looking for hospitals with {ent.get('department') or 'the right'} department.")


def r_hospitals(event):
    q = qs(event)
    lat, lon = logic.loc(q.get("lat"), q.get("lon"))
    dept = q.get("dept") if q.get("dept") in logic.DEPARTMENTS else None
    eq = q.get("equipment") if q.get("equipment") in logic.EQUIP_TYPES else None
    own = q.get("type") if q.get("type") in ("government", "private") else None
    return {"hospitals": logic.rank_hospitals(db.snapshot(), lat, lon, dept=dept, equipment=eq,
                                              female=q.get("female") == "1", ownership=own)}


def r_facility(event, fid):
    q = qs(event)
    lat, lon = logic.loc(q.get("lat"), q.get("lon"))
    snap = db.snapshot()
    f = snap["facilities"].get(fid)
    if not f:
        return resp(404, {"error": "Facility not found"})
    if f["type"] == "hospital":
        card = logic.hospital_card(f, lat, lon)
    else:
        km = logic.haversine(lat, lon, f["lat"], f["lon"])
        card = {"id": f["id"], "name": f["name"], "lat": f["lat"], "lon": f["lon"],
                "distanceKm": round(km, 1), "etaMin": logic.eta_min(km)}
    card["type"] = f["type"]
    card["locationPrecision"] = f.get("locationPrecision", "exact")
    card["source"] = f.get("source")
    card["doctors"] = sorted(f["doctors"].values(), key=lambda d: (not d.get("onDuty"), d.get("dept") or ""))
    card["medicine"] = sorted(({**m, "name": logic.CATALOG.get(m["key"], {}).get("name", m["key"])}
                               for m in f["medicine"].values()), key=lambda m: m["name"])
    card["blood"] = f["blood"]
    updates = []
    for g in ("beds", "doctors", "equipment", "medicine", "blood"):
        for r in f[g].values():
            label = r.get("name") or logic.CATALOG.get(r.get("key"), {}).get("name") or r.get("key")
            updates.append({"what": f"{r.get('kind')}: {label}", "by": r.get("updatedBy"), "at": r.get("updatedAt")})
    card["recentUpdates"] = sorted(updates, key=lambda u: -(u["at"] or 0))[:8]
    return card


def r_facilities(event):
    snap = db.snapshot()
    t = qs(event).get("type")
    return {"facilities": [{"id": f["id"], "name": f["name"], "type": f["type"]} for f in
                           sorted(snap["facilities"].values(), key=lambda f: (f["type"], f["name"]))
                           if not t or f["type"] == t]}


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
    f = snap["facilities"].get(fid)
    if not f or f["type"] != "hospital":
        raise BadRequest("Unknown hospital")
    dept = data.get("department") if data.get("department") in logic.DEPARTMENTS else "Emergency"
    note = text_arg(data.get("note"), 300) or "Patient on the way"
    try:
        eta = max(0, min(int(data.get("eta") or 0), 600)) * 60
    except (TypeError, ValueError):
        eta = None
    by = "ambulance (1122/Edhi)" if data.get("byAmbulance") else "family"
    aid = create_alert(fid, dept, f"{'Patient coming by ambulance' if data.get('byAmbulance') else 'Family on the way'}: {note}",
                       eta=eta, source=by)
    db.bump(notifications=1)
    return {"referenceCode": aid, "facility": f["name"], "department": dept}


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


def apply_changes(f, changes, who="staff portal (pilot)"):
    """Write reported values. Every report carries updatedAt + updatedBy."""
    now = logic.now()
    pk = f"FACILITY#{f['id']}"
    items = []
    for c in changes:
        k = c["kind"]
        base = {"pk": pk, "kind": k, "updatedAt": now, "updatedBy": who}
        if k == "bed":
            items.append({**base, "sk": f"RES#bed#{c['key']}", "key": c["key"], "free": c["free"]})
        elif k == "doctor":
            items.append({**base, "sk": f"RES#doctor#{c['key']}", "key": c["key"], "name": c["name"],
                          "dept": c.get("dept"), "gender": c.get("gender"), "onDuty": c["onDuty"],
                          "shiftEnds": c.get("shiftEnds")})
        elif k == "equipment":
            items.append({**base, "sk": f"RES#equipment#{c['key']}", "key": c["key"], "status": c["status"]})
        elif k == "medicine":
            items.append({**base, "sk": f"RES#medicine#{c['key']}", "key": c["key"], "qty": c["qty"],
                          "priceRs": c.get("priceRs")})
        elif k == "blood":
            items.append({**base, "sk": f"RES#blood#{c['key']}", "key": c["key"], "units": c["units"]})
    db.batch_write([{k: v for k, v in it.items() if v is not None} for it in items])
    db.bump(staffUpdates=len(items))


def r_staff_parse(event):
    data = body_of(event)
    snap = db.snapshot(force=True)
    f = require_staff(data, snap)
    text = text_arg(data.get("text"), 500)
    if not text:
        raise BadRequest("Type an update")
    prompt = logic.STAFF_PROMPT.format(facility=f"{f['name']} ({f['type']})", resources=logic.facility_resources_text(f))
    parsed = ai.converse_json(prompt, text)
    source = "ai"
    raw = parsed.get("changes") if isinstance(parsed, dict) else None
    changes = logic.validate_changes(f, raw) if raw is not None else []
    if not changes:
        changes = logic.validate_changes(f, logic.keyword_parse_staff(f, text))
        source = "keywords"
    return {"changes": changes, "understoodBy": source,
            "summaryEn": parsed.get("summaryEn") if isinstance(parsed, dict) else None,
            "summaryUr": parsed.get("summaryUr") if isinstance(parsed, dict) else None}


def r_staff_update(event):
    data = body_of(event)
    snap = db.snapshot(force=True)
    f = require_staff(data, snap)
    changes = data.get("changes") or []
    normalized = []
    for c in changes if isinstance(changes, list) else []:
        if not isinstance(c, dict):
            continue
        try:
            if c.get("kind") == "bed" and "delta" in c:
                normalized.append({"kind": "bed", "key": c.get("key"),
                                   "free": (f["beds"].get(c.get("key"), {}).get("free") or 0) + int(c["delta"])})
            elif c.get("kind") == "medicine" and "delta" in c:
                normalized.append({"kind": "medicine", "key": c.get("key"),
                                   "qty": (f["medicine"].get(c.get("key"), {}).get("qty") or 0) + int(c["delta"])})
            elif c.get("kind") == "blood" and "delta" in c:
                normalized.append({"kind": "blood", "key": c.get("key"),
                                   "units": (f["blood"].get(c.get("key"), {}).get("units") or 0) + int(c["delta"])})
            else:
                normalized.append(c)
        except (TypeError, ValueError):
            continue
    valid = logic.validate_changes(f, normalized)
    if not valid:
        raise BadRequest("Nothing to update")
    apply_changes(f, valid)
    return {"applied": valid}


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
    facs = list(snap["facilities"].values())
    hosp = [f for f in facs if f["type"] == "hospital"]
    reporting = [f for f in hosp if f["beds"] or f["doctors"] or f["equipment"]]
    free_by_dept, full, down = {}, [], []
    for f in hosp:
        for d, b in f["beds"].items():
            free_by_dept[d] = free_by_dept.get(d, 0) + int(b.get("free", 0))
        if logic.er_load(f) == "Full":
            full.append(f["name"])
        for e, v in f["equipment"].items():
            if v["status"] == "down":
                down.append({"hospital": f["name"], "equipment": e})
    blood = {}
    for f in facs:
        if f["type"] == "bloodbank":
            for g, v in f["blood"].items():
                blood[g] = blood.get(g, 0) + v["units"]
    return {
        "hospitals": len(hosp), "privateHospitals": sum(1 for f in hosp if f.get("ownership") == "private"),
        "pharmacies": sum(1 for f in facs if f["type"] == "pharmacy"),
        "bloodBanks": sum(1 for f in facs if f["type"] == "bloodbank"),
        "hospitalsReporting": len(reporting),
        "pharmaciesReporting": sum(1 for f in facs if f["type"] == "pharmacy" and f["medicine"]),
        "bloodBanksReporting": sum(1 for f in facs if f["type"] == "bloodbank" and f["blood"]),
        "reportedFreeBeds": sum(free_by_dept.values()), "reportedFreeBedsByDept": free_by_dept,
        "hospitalsReportedFull": full, "machinesReportedDown": down, "reportedBloodUnits": blood,
        "counters": snap.get("stats", {}), "updatedAt": logic.now(),
    }


def r_map(event):
    snap = db.snapshot()
    pts = []
    for f in snap["facilities"].values():
        p = {"id": f["id"], "name": f["name"], "type": f["type"], "lat": f["lat"], "lon": f["lon"]}
        if f["type"] == "hospital":
            p["ownership"] = f.get("ownership", "government")
            p["reported"] = bool(f["beds"])
            p["reportedFreeBeds"] = sum(int(b.get("free", 0)) for b in f["beds"].values()) if f["beds"] else None
            p["erLoad"] = logic.er_load(f)
        pts.append(p)
    return {"facilities": pts}


ROUTES = [
    ("POST", r"^/ask$", r_ask),
    ("GET", r"^/hospitals$", r_hospitals),
    ("GET", r"^/facilities$", r_facilities),
    ("GET", r"^/facility/([\w-]+)$", r_facility),
    ("GET", r"^/helplines$", lambda e: {"helplines": HELPLINES}),
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
# reachable even without CloudFront. Files are copied into backend/static by deploy.ps1.
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
STATIC = {"/": ("index.html", "text/html; charset=utf-8"), "/index.html": ("index.html", "text/html; charset=utf-8"),
          "/app.js": ("app.js", "application/javascript; charset=utf-8"),
          "/styles.css": ("styles.css", "text/css; charset=utf-8"),
          "/config.js": (None, "application/javascript")}


def static_file(path):
    name, ctype = STATIC[path]
    headers = {"content-type": ctype, "cache-control": "no-cache"}
    if name is None:
        return {"statusCode": 200, "headers": headers, "body": "window.HAAZIR_API = '';"}
    fp = os.path.join(STATIC_DIR, name)
    if not os.path.exists(fp):
        return resp(404, {"error": "Not found"})
    with open(fp, "rb") as fh:
        return {"statusCode": 200, "headers": headers, "body": fh.read().decode("utf-8")}


def reset_to_real_data():
    """Remove every non-reference row (old simulated availability, ambulances, requests, alerts) and reseed."""
    items = build_items()
    keep = {(i["pk"], i["sk"]) for i in items}
    stale = [(i["pk"], i["sk"]) for i in db._scan_all() if (i["pk"], i["sk"]) not in keep]
    db.batch_delete(stale)
    db.batch_write(items + [{"pk": "STATS", "sk": "GLOBAL", "searches": 0, "medicineSearches": 0, "bloodRequests": 0,
                             "estMinutesSaved": 0, "notifications": 0, "staffUpdates": 0}])
    return {"seeded": len(items), "removed": len(stale)}


def api(event, context=None):
    if event.get("action") == "seed":  # direct invocation by deploy script only
        return reset_to_real_data()
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
