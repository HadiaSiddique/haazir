"""Offline test with a fake DynamoDB: real facilities only, availability only from staff reports."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import fakes  # noqa: F401,E402  (installs fake boto3)
import handler  # noqa: E402

FAIL = []


def call(method, path, body=None, q=None, expect=200, demo="0"):
    q = dict(q or {})
    q.setdefault("demo", demo)
    ev = {"requestContext": {"http": {"method": method}}, "rawPath": path, "queryStringParameters": q,
          "body": json.dumps(body) if body is not None else None}
    r = handler.api(ev)
    data = json.loads(r["body"])
    ok = r["statusCode"] == expect
    print(f"{'OK ' if ok else 'BAD'} {method} {path} -> {r['statusCode']}")
    if not ok:
        FAIL.append(path)
        print("   ", data)
    return data


def check(cond, msg):
    print(("   ok  " if cond else "   BAD ") + msg)
    if not cond:
        FAIL.append(msg)


# old simulated rows must be wiped by the reset
fakes.STORE[("FACILITY#hosp-mayo", "RES#bed#ICU")] = {"pk": "FACILITY#hosp-mayo", "sk": "RES#bed#ICU", "kind": "bed", "key": "ICU", "total": 16, "occupied": 16}
fakes.STORE[("AMBULANCE#amb-01", "META")] = {"pk": "AMBULANCE#amb-01", "sk": "META", "id": "amb-01"}
print(handler.api({"action": "seed"}))
check(("AMBULANCE#amb-01", "META") not in fakes.STORE, "simulated ambulance removed")
check(fakes.STORE.get(("FACILITY#hosp-mayo", "RES#bed#ICU"), {}).get("demo"), "old row replaced by flagged demo row")

L = {"lat": 31.5204, "lon": 74.3487}
st = call("GET", "/stats")
check(st["hospitals"] == 19 and st["privateHospitals"] == 9, f"19 hospitals, 9 private ({st['hospitals']}, {st['privateHospitals']})")
check(st["pharmacies"] >= 50, f"real pharmacies loaded ({st['pharmacies']})")
check(st["hospitalsReporting"] == 0 and st["reportedFreeBeds"] == 0, "nothing reported before staff report")

r = call("POST", "/ask", {"text": "abbu ko seenay mein dard", **L})
check(r["entities"]["redFlag"] and r["entities"]["department"] == "Cardiology", "chest pain -> red flag, Cardiology")
check(all(h["freeBeds"] is None for h in r["hospitals"]), "no invented bed numbers")
check(all(not h["equipment"] and not h["doctorsOnDuty"] for h in r["hospitals"]), "no invented machines or doctors")
print("    top:", r["hospitals"][0]["name"], "|", r["hospitals"][0]["why"])
for t in ["O negative blood chahiye 2 bottle", "Augmentin kahan milegi Johar Town", "CT scan kahan ho raha hai abhi",
          "lady doctor gynae", "ambulance chahiye", "bachay ko tez bukhar hai", "emergency"]:
    a = call("POST", "/ask", {"text": t, **L})
    print(f"    '{t}' -> {a['intent']} {a['entities'].get('bloodGroup') or ''} {a['entities'].get('department') or ''}")

b = call("GET", "/blood/search", q={"group": "O-", "units": "2", **L})
check(all(x["exactUnits"] is None for x in b["banks"]), "blood units not invented")
m = call("GET", "/medicine/search", q={"q": "augmentin", **L})
check(not m["pharmacies"] and m["nearbyPharmacies"], "no invented stock, nearest real pharmacies listed")
e = call("GET", "/equipment", q={"type": "CT", **L})
check(all(x["status"] == "unknown" for x in e["results"]), "machine status unknown until reported")

# staff report flow (hospital)
sp = call("POST", "/staff/parse", {"facilityId": "hosp-mayo", "pin": "1234",
                                   "text": "Medicine ward mein 2 bed khali, CT kharab hai, Dr Sana 8 baje tak duty pe"})
print("    parsed:", [c["label"] for c in sp["changes"]])
check(len(sp["changes"]) == 3, "hospital message -> 3 changes")
call("POST", "/staff/update", {"facilityId": "hosp-mayo", "pin": "1234", "changes": sp["changes"]})
call("POST", "/staff/update", {"facilityId": "hosp-mayo", "pin": "1234", "changes": [{"kind": "bed", "key": "Emergency", "free": 0}]})
call("POST", "/staff/update", {"facilityId": "hosp-mayo", "pin": "1234", "changes": [{"kind": "bed", "key": "Emergency", "delta": 2}]})
call("POST", "/staff/update", {"facilityId": "hosp-pic", "pin": "1234", "changes": [{"kind": "bed", "key": "Cardiology", "free": 4},
     {"kind": "doctor", "name": "Dr Ayesha Malik", "dept": "Cardiology", "gender": "F", "onDuty": True, "shiftEnds": "22:00"}]})
f = call("GET", "/facility/hosp-mayo", q=L)
check(f["beds"]["Medicine"]["free"] == 2 and f["beds"]["Emergency"]["free"] == 2, "reported beds stored (Medicine 2, Emergency 0+2)")
check(f["equipment"]["CT"]["status"] == "down" and any(d["name"] == "Dr Sana" for d in f["doctors"]), "CT down + Dr Sana reported")
r = call("POST", "/ask", {"text": "abbu ko seenay mein dard", **L})
print("    top after reports:", r["hospitals"][0]["name"], "|", r["hospitals"][0]["why"])
check(r["hospitals"][0]["id"] == "hosp-pic", "PIC (reported 4 cardiology beds + cardiologist) ranks first")
fl = call("GET", "/hospitals", q={"dept": "Cardiology", "female": "1", **L})
check(any(h["femaleDoctor"] for h in fl["hospitals"]), "female doctor filter finds reported female doctor")
call("POST", "/staff/update", {"facilityId": "hosp-mayo", "pin": "0000", "changes": []}, expect=403)
call("POST", "/staff/parse", {"facilityId": "ph-01", "pin": "1234", "text": "x"})
# pharmacy + blood bank
ph = call("POST", "/staff/parse", {"facilityId": "ph-04", "pin": "1234", "text": "Panadol khatam, Augmentin 20 packs aa gaye"})
print("    pharmacy parsed:", [c["label"] for c in ph["changes"]])
check(len(ph["changes"]) == 2, "pharmacy message -> 2 changes")
call("POST", "/staff/update", {"facilityId": "ph-04", "pin": "1234", "changes": ph["changes"]})
m = call("GET", "/medicine/search", q={"q": "augmentin", **L})
check(m["pharmacies"] and m["pharmacies"][0]["id"] == "ph-04", "reported stock found")
p = call("POST", "/medicine/plan", {"items": ["Augmentin 625"], **L})
check(p["onePharmacy"], "plan finds the pharmacy that reported")
bb = call("POST", "/staff/parse", {"facilityId": "bb-sundas", "pin": "1234", "text": "O- 2 unit, B+ 10 unit"})
print("    blood parsed:", [c["label"] for c in bb["changes"]])
call("POST", "/staff/update", {"facilityId": "bb-sundas", "pin": "1234", "changes": bb["changes"]})
b = call("GET", "/blood/search", q={"group": "O-", "units": "2", **L})
check(b["banks"][0]["id"] == "bb-sundas" and b["banks"][0]["exactUnits"] == 2, "reported blood found first")
call("POST", "/notify", {"facilityId": "hosp-pic", "department": "Cardiology", "note": "chest pain", "eta": 12, "byAmbulance": True})
al = call("POST", "/staff/alerts", {"facilityId": "hosp-pic", "pin": "1234"})
check(len(al["alerts"]) == 1, "hospital alert received")
call("POST", "/staff/alerts/ack", {"facilityId": "hosp-pic", "pin": "1234", "sk": al["alerts"][0]["sk"]})
call("POST", "/blood/request", {"group": "O-", "units": 2, "hospital": "Mayo Hospital"})
st = call("GET", "/stats")
check(st["hospitalsReporting"] == 2, f"2 hospitals reporting ({st['hospitalsReporting']})")
call("GET", "/map")
call("GET", "/facilities")
call("GET", "/helplines")
call("POST", "/ask", {"text": ""}, expect=400)
call("GET", "/nope", expect=404)
dm = call("POST", "/ask", {"text": "abbu ko seenay mein dard", **L}, demo="1")
check(any(h["demo"] and h["freeBeds"] is not None for h in dm["hospitals"]), "demo mode: sample numbers shown and tagged demo")
check(any("sample data" in h["why"] for h in dm["hospitals"]), "demo rows say demo in the why line")
mm = call("GET", "/medicine/search", q={"q": "panadol", **L})
check(mm["matched"][0]["use"] == "Pain relief and fever" and mm["matched"][0]["rx"] == "otc", "medicine use + prescription status")
ma = call("GET", "/medicine/search", q={"q": "augmentin", **L})
check(ma["matched"][0]["rx"] == "rx", "antibiotic marked prescription needed")
sd = call("GET", "/stats", demo="1")
check(len(sd["recentReports"]) > 0, "activity feed has entries")
print("\nFAILURES:", FAIL if FAIL else "none")
