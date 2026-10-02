"""Runs the exact demo story from SUBMISSION.md against the offline fake table."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import fakes  # noqa: F401,E402
import handler  # noqa: E402


def call(method, path, body=None, q=None):
    r = handler.api({"requestContext": {"http": {"method": method}}, "rawPath": path, "queryStringParameters": q,
                     "body": json.dumps(body) if body is not None else None})
    return r["statusCode"], json.loads(r["body"])


handler.api({"action": "seed"})
L = {"lat": 31.5204, "lon": 74.3487}
_, a = call("POST", "/ask", {"text": "abbu ko seenay mein dard", **L})
print("1 before:", a["hospitals"][0]["name"], "|", a["hospitals"][0]["why"])
_, p = call("POST", "/staff/parse", {"facilityId": "hosp-pic", "pin": "1234",
                                     "text": "Cardiology ward mein 4 bed khali, Dr Ayesha 10 baje tak duty pe"})
print("2 preview:", [c["label"] for c in p["changes"]])
call("POST", "/staff/update", {"facilityId": "hosp-pic", "pin": "1234", "changes": p["changes"]})
_, a = call("POST", "/ask", {"text": "abbu ko seenay mein dard", **L})
print("3 after:", a["hospitals"][0]["name"], "|", a["hospitals"][0]["why"])
_, n = call("POST", "/notify", {"facilityId": "hosp-pic", "department": "Cardiology", "note": "chest pain", "eta": 7})
_, al = call("POST", "/staff/alerts", {"facilityId": "hosp-pic", "pin": "1234"})
print("4 alert:", n["referenceCode"], "->", al["alerts"][0]["note"])
_, p = call("POST", "/staff/parse", {"facilityId": "ph-04", "pin": "1234", "text": "Panadol khatam, Augmentin 20 packs aa gaye"})
call("POST", "/staff/update", {"facilityId": "ph-04", "pin": "1234", "changes": p["changes"]})
_, m = call("GET", "/medicine/search", q={"q": "Augmentin", **L})
print("5 medicine:", [(x["name"], x["stock"][0]["qty"]) for x in m["pharmacies"]])
_, b = call("POST", "/blood/request", {"group": "O-", "units": 2, "hospital": "Mayo Hospital"})
print("6 whatsapp:", b["message"][:70])
