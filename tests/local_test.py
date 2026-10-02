import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import fakes  # noqa: F401  (installs fake boto3)
import handler  # noqa: E402


def call(method, path, body=None, q=None):
    ev = {"requestContext": {"http": {"method": method}}, "rawPath": path, "queryStringParameters": q,
          "body": json.dumps(body) if body is not None else None}
    r = handler.api(ev)
    data = json.loads(r["body"])
    print(f"{method} {path} -> {r['statusCode']}")
    if r["statusCode"] >= 400:
        print("   ", data)
    return data


print(handler.api({"action": "seed"}))
L = {"lat": 31.52, "lon": 74.35}
r = call("POST", "/ask", {"text": "abbu ko seenay mein dard", **L})
print("   intent", r["intent"], "redFlag", r["entities"]["redFlag"], "dept", r["entities"]["department"])
print("   top:", r["hospitals"][0]["name"], "|", r["hospitals"][0]["why"])
for t in ["O negative blood chahiye 2 bottle", "Augmentin kahan milegi Johar Town", "CT scan kahan ho raha hai abhi",
          "lady doctor gynae", "ambulance chahiye", "bachay ko tez bukhar hai"]:
    r = call("POST", "/ask", {"text": t, **L})
    ex = r.get("hospitals", [{}])[0].get("name") if r.get("hospitals") else (
        (r.get("medicine") or {}).get("pharmacies", [{}])[0].get("name") if r.get("medicine") else
        (r.get("blood") or {}).get("banks", [{}])[0].get("name") if r.get("blood") else
        (r.get("equipment") or {}).get("results", [{}])[0].get("name"))
    print(f"   '{t}' -> {r['intent']} {r['entities'].get('bloodGroup') or ''} {r['entities'].get('department') or ''} :: {ex}")
call("GET", "/hospitals", q={"dept": "ICU", **L})
f = call("GET", "/facility/hosp-mayo", q=L)
print("   beds", list(f["beds"].items())[:2])
a = call("POST", "/ambulance/request", {"condition": "chest pain, unconscious", **L})
print("   ", a)
s = call("GET", f"/ambulance/request/{a['requestId']}")
print("   status", s["status"], s["etaSec"])
call("POST", "/notify", {"facilityId": "hosp-mayo", "department": "Medicine", "note": "fever", "eta": 20})
m = call("GET", "/medicine/search", q={"q": "augmentin", **L})
print("   alts", [x["name"] for x in m["alternatives"]], "pharmacies", len(m["pharmacies"]))
p = call("POST", "/medicine/plan", {"items": ["Augmentin 625", "Panadol", "Risek 20mg", "Glucophage"], **L})
print("   onePharmacy", p["onePharmacy"], [s["name"] for s in p["stops"]], p["totalRs"])
b = call("GET", "/blood/search", q={"group": "O-", "units": "2", **L})
print("   blood top", b["banks"][0]["name"], b["banks"][0]["exactUnits"])
br = call("POST", "/blood/request", {"group": "O-", "units": 2, "hospital": "Mayo Hospital"})
print("   ", br["message"])
e = call("GET", "/equipment", q={"type": "MRI", **L})
print("   MRI", [(x["name"], x["status"]) for x in e["results"]][:3])
sp = call("POST", "/staff/parse", {"facilityId": "hosp-mayo", "pin": "1234",
                                   "text": "Medicine ward 3 mein 2 bed khali, CT kharab hai, Dr Sana 8 baje tak duty pe"})
print("   parsed", [c["label"] for c in sp["changes"]])
up = call("POST", "/staff/update", {"facilityId": "hosp-mayo", "pin": "1234", "changes": sp["changes"]})
print("   applied", len(up["applied"]))
ph = call("POST", "/staff/parse", {"facilityId": "ph-gulberg", "pin": "1234", "text": "Panadol khatam, Augmentin 20 packs aa gaye"})
print("   pharmacy parsed", [c["label"] for c in ph["changes"]])
call("POST", "/staff/update", {"facilityId": "hosp-mayo", "pin": "1234", "changes": [{"kind": "bed", "key": "ICU", "delta": 1}]})
call("POST", "/staff/update", {"facilityId": "hosp-mayo", "pin": "0000", "changes": []})
al = call("POST", "/staff/alerts", {"facilityId": "hosp-mayo", "pin": "1234"})
print("   alerts", len(al["alerts"]))
call("POST", "/staff/alerts/ack", {"facilityId": "hosp-mayo", "pin": "1234", "sk": al["alerts"][0]["sk"]})
st = call("GET", "/stats")
print("   stats", st["freeBedsTotal"], st["ambulancesAvailable"], st["bloodShortages"], st["counters"])
call("GET", "/map")
call("GET", "/facilities")
print(handler.api({"action": "simulate"}))
call("POST", "/ask", {"text": ""})
call("GET", "/nope")
