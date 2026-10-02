"""Demo simulator (DEMO_MODE=true only): small realistic changes every 5 minutes so the pilot looks alive."""
import os
import random

import db
import logic


def run():
    if os.environ.get("DEMO_MODE", "true").lower() != "true":
        return {"skipped": True}
    snap = db.snapshot(force=True)
    now = logic.now()
    n = 0
    by = "simulated update"
    for f in snap["facilities"].values():
        pk = f"FACILITY#{f['id']}"
        for d, b in f["beds"].items():
            r = random.random()
            if r < 0.35:
                occ = max(0, min(b["total"], b["occupied"] + random.choice([-2, -1, -1, 1, 1, 2])))
                db.update_fields(pk, f"RES#bed#{d}", {"occupied": occ, "updatedAt": now, "updatedBy": by})
                n += 1
            elif r < 0.6:
                db.update_fields(pk, f"RES#bed#{d}", {"updatedAt": now, "updatedBy": "confirmed by ward staff"})
        for k, doc in f["doctors"].items():
            if random.random() < 0.08:
                db.update_fields(pk, f"RES#doctor#{k}", {"onDuty": not doc.get("onDuty"), "updatedAt": now,
                                                         "updatedBy": "duty roster"})
                n += 1
            elif random.random() < 0.3:
                db.update_fields(pk, f"RES#doctor#{k}", {"updatedAt": now})
        for e, eq in f["equipment"].items():
            r = random.random()
            if r < 0.05 and e != "Oxygen":
                st = random.choice([s for s in ("working", "down", "busy") if s != eq["status"]])
                db.update_fields(pk, f"RES#equipment#{e}", {"status": st, "queue": random.randint(0, 10),
                                                            "updatedAt": now, "updatedBy": by})
                n += 1
            elif r < 0.3:
                db.update_fields(pk, f"RES#equipment#{e}", {"queue": max(0, eq.get("queue", 0) + random.choice([-2, -1, 1, 2])),
                                                            "updatedAt": now, "updatedBy": "confirmed by staff"})
        meds = list(f["medicine"].items())
        for k, m in random.sample(meds, min(len(meds), 4)):
            q = max(0, m.get("qty", 0) + random.choice([-5, -3, -2, 6, 10, 20]))
            db.update_fields(pk, f"RES#medicine#{k}", {"qty": q, "inStock": q > 0, "updatedAt": now, "updatedBy": by})
            n += 1
        for g, bl in f["blood"].items():
            if random.random() < 0.3:
                u = max(0, bl.get("units", 0) + random.choice([-1, -1, 1, 2]))
                db.update_fields(pk, f"RES#blood#{g}", {"units": u, "updatedAt": now, "updatedBy": by})
                n += 1
            else:
                db.update_fields(pk, f"RES#blood#{g}", {"updatedAt": now})
    for a in snap["ambulances"].values():
        if a["status"] in ("enroute", "busy") and a.get("requestId"):
            req = db.get(f"REQUEST#{a['requestId']}")
            if not req or now - req["createdAt"] > req["toPatientSec"] + req["toHospitalSec"] + 240:
                fields = {"status": "available", "requestId": "", "updatedAt": now}
                if req:
                    fields.update(lat=req["destLat"], lon=req["destLon"])
                db.update_fields(f"AMBULANCE#{a['id']}", "META", fields)
                n += 1
        elif a["status"] == "busy" and random.random() < 0.3:
            db.update_fields(f"AMBULANCE#{a['id']}", "META", {"status": "available", "updatedAt": now})
        elif a["status"] == "available":
            lat = min(31.62, max(31.40, a["lat"] + random.uniform(-0.004, 0.004)))
            lon = min(74.42, max(74.22, a["lon"] + random.uniform(-0.004, 0.004)))
            db.update_fields(f"AMBULANCE#{a['id']}", "META", {"lat": lat, "lon": lon, "updatedAt": now})
    db.invalidate()
    print("simulator changes:", n)
    return {"changes": n}
