"""One-off source patch: route all read endpoints through the demo-aware snapshot view."""
import os
import re

root = os.path.join(os.path.dirname(__file__), "..", "backend")


def patch(fn, pairs):
    p = os.path.join(root, fn)
    s = open(p, encoding="utf-8").read()
    for old, new in pairs:
        if old not in s:
            raise SystemExit(f"MISSING in {fn}: {old[:70]}")
        s = s.replace(old, new)
    open(p, "w", encoding="utf-8", newline="\n").write(s)


patch("handler.py", [
    ("from seed_data import HELPLINES, build_items\n",
     "from seed_data import HELPLINES, build_demo_items, build_items\n"),
    ("# ------------------------------------------------------------------ routes\n",
     "def snap_for(event, data=None):\n"
     "    \"\"\"Snapshot as the user sees it: demo sample data ON by default; demo=0 shows real staff reports only.\"\"\"\n"
     "    v = (data or {}).get(\"demo\", qs(event).get(\"demo\", \"1\"))\n"
     "    return db.view(db.snapshot(), str(v).lower() not in (\"0\", \"false\"))\n\n\n"
     "# ------------------------------------------------------------------ routes\n"),
    ("    if area in logic.AREAS:\n        lat, lon = logic.AREAS[area]\n    snap = db.snapshot()\n",
     "    if area in logic.AREAS:\n        lat, lon = logic.AREAS[area]\n    snap = snap_for(event, data)\n"),
    ("    return {\"hospitals\": logic.rank_hospitals(db.snapshot(), lat, lon,",
     "    return {\"hospitals\": logic.rank_hospitals(snap_for(event), lat, lon,"),
    ("    lat, lon = logic.loc(q.get(\"lat\"), q.get(\"lon\"))\n    snap = db.snapshot()\n    f = snap[\"facilities\"].get(fid)\n    if not f:\n        return resp(404",
     "    lat, lon = logic.loc(q.get(\"lat\"), q.get(\"lon\"))\n    snap = snap_for(event)\n    f = snap[\"facilities\"].get(fid)\n    if not f:\n        return resp(404"),
    ("    return logic.medicine_search(db.snapshot(), name, lat, lon)",
     "    return logic.medicine_search(snap_for(event), name, lat, lon)"),
    ("    return logic.medicine_plan(db.snapshot(), names, lat, lon)",
     "    return logic.medicine_plan(snap_for(event, data), names, lat, lon)"),
    ("    return logic.blood_search(db.snapshot(), g, units, lat, lon)",
     "    return logic.blood_search(snap_for(event), g, units, lat, lon)"),
    ("    return logic.equipment_search(db.snapshot(), q.get(\"type\"), lat, lon)",
     "    return logic.equipment_search(snap_for(event), q.get(\"type\"), lat, lon)"),
    ("def r_stats(event):\n    snap = db.snapshot()\n",
     "def r_stats(event):\n    snap = snap_for(event)\n"),
    ("def r_map(event):\n    snap = db.snapshot()\n",
     "def r_map(event):\n    snap = snap_for(event)\n"),
    ("    card[\"recentUpdates\"] = sorted(updates, key=lambda u: -(u[\"at\"] or 0))[:8]\n",
     "    card[\"recentUpdates\"] = sorted(updates, key=lambda u: -(u[\"at\"] or 0))[:8]\n"
     "    card[\"demo\"] = any(r.get(\"demo\") for g in (\"beds\", \"doctors\", \"equipment\", \"medicine\", \"blood\") for r in f[g].values())\n"),
    ("def reset_to_real_data():\n    \"\"\"Remove every non-reference row (old simulated availability, ambulances, requests, alerts) and reseed.\"\"\"\n    items = build_items()\n",
     "def reset_to_real_data():\n    \"\"\"Remove every non-reference row (reports, requests, alerts) and reseed real facilities + flagged demo rows.\"\"\"\n    items = build_items() + build_demo_items()\n"),
    ("            updates.append({\"what\": f\"{r.get('kind')}: {label}\", \"by\": r.get(\"updatedBy\"), \"at\": r.get(\"updatedAt\")})",
     "            updates.append({\"what\": f\"{r.get('kind')}: {label}\", \"by\": r.get(\"updatedBy\"), \"at\": r.get(\"updatedAt\"),\n"
     "                            \"demo\": bool(r.get(\"demo\"))})"),
    ("        \"counters\": snap.get(\"stats\", {}), \"updatedAt\": logic.now(),\n",
     "        \"counters\": snap.get(\"stats\", {}), \"updatedAt\": logic.now(),\n"
     "        \"recentReports\": recent_reports(snap),\n"),
    ("def r_map(event):",
     "def recent_reports(snap, n=8):\n"
     "    \"\"\"Latest bed/equipment/blood/stock reports across the city, for the live activity feed.\"\"\"\n"
     "    rows = []\n"
     "    for f in snap[\"facilities\"].values():\n"
     "        for b, r in f[\"beds\"].items():\n"
     "            rows.append((r.get(\"updatedAt\", 0), f[\"name\"], f\"{b}: {r.get('free')} free beds\", \"bed\", r.get(\"demo\"), f[\"id\"]))\n"
     "        for e, r in f[\"equipment\"].items():\n"
     "            rows.append((r.get(\"updatedAt\", 0), f[\"name\"], f\"{e}: {r.get('status')}\", \"equipment\", r.get(\"demo\"), f[\"id\"]))\n"
     "        for g, r in f[\"blood\"].items():\n"
     "            rows.append((r.get(\"updatedAt\", 0), f[\"name\"], f\"{g}: {r.get('units')} units\", \"blood\", r.get(\"demo\"), f[\"id\"]))\n"
     "    rows.sort(key=lambda x: -x[0])\n"
     "    return [{\"at\": a, \"facility\": fn, \"text\": t, \"kind\": k, \"demo\": bool(d), \"id\": i} for a, fn, t, k, d, i in rows[:n]]\n\n\n"
     "def r_map(event):"),
])

patch("logic.py", [
    ("from seed_data import MEDICINES, BLOOD_GROUPS\n", "from seed_data import BLOOD_GROUPS, MED_INFO, MEDICINES\n"),
    ("CATALOG = {k: {\"key\": k, \"name\": n, \"salt\": s, \"strength\": st} for k, n, s, st in MEDICINES}",
     "CATALOG = {k: {\"key\": k, \"name\": n, \"salt\": s, \"strength\": st,\n"
     "               \"use\": MED_INFO.get(s, (None, None, \"ask\"))[0], \"useUr\": MED_INFO.get(s, (None, None, \"ask\"))[1],\n"
     "               \"rx\": MED_INFO.get(s, (None, None, \"ask\"))[2]} for k, n, s, st in MEDICINES}"),
    ("        \"hasReports\": bool(reports), \"updatedAt\": max(reports) if reports else None,\n",
     "        \"hasReports\": bool(reports), \"updatedAt\": max(reports) if reports else None,\n"
     "        \"demo\": any(r.get(\"demo\") for g in (\"beds\", \"doctors\", \"equipment\") for r in f[g].values()),\n"),
    ("                              \"exact\": k == primary, \"stale\": not fresh(r), \"updatedAt\": r.get(\"updatedAt\")})",
     "                              \"exact\": k == primary, \"stale\": not fresh(r), \"updatedAt\": r.get(\"updatedAt\"),\n"
     "                              \"demo\": bool(r.get(\"demo\"))})"),
    ("                      \"exactUnits\": exact, \"compatibleUnits\": comp, \"enough\": exact is not None and exact >= units,",
     "                      \"exactUnits\": exact, \"compatibleUnits\": comp, \"enough\": exact is not None and exact >= units,\n"
     "                      \"demo\": any(r.get(\"demo\") for r in f[\"blood\"].values()),"),
    ("                     \"stale\": bool(e) and not fresh(e)})",
     "                     \"stale\": bool(e) and not fresh(e), \"demo\": bool(e and e.get(\"demo\"))})"),
])
print("patched")
