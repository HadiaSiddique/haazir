"""One-off: turn an Overpass export (list of {kind,name,lat,lon}) into backend/osm_pharmacies.py."""
import json
import os
import re
import sys

rows = json.load(open(sys.argv[1], encoding="utf-8-sig"))
seen, out = set(), []
for r in rows:
    if r["kind"] != "pharmacy":
        continue
    n = re.sub(r"\s+", " ", r["name"]).strip()
    if len(n) < 5 or n.lower() in ("pharmacy", "medical store", "chemist"):
        continue
    k = (n.lower(), round(r["lat"], 3), round(r["lon"], 3))
    if k in seen:
        continue
    seen.add(k)
    out.append((n, r["lat"], r["lon"]))

dst = os.path.join(os.path.dirname(__file__), "..", "backend", "osm_pharmacies.py")
with open(dst, "w", encoding="utf-8", newline="\n") as f:
    f.write('"""Real pharmacies in Lahore from OpenStreetMap (amenity=pharmacy). (c) OpenStreetMap contributors, ODbL.\n'
            'Only name and location are used. Stock is never invented: it appears only when a pharmacist reports it."""\n')
    f.write("PHARMACIES = [\n")
    for i, (n, la, lo) in enumerate(out):
        f.write("    (%r, %r, %.4f, %.4f),\n" % ("ph-%02d" % (i + 1), n, la, lo))
    f.write("]\n")
print(len(out), "pharmacies written")
