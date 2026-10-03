"""One-off: make local_test.py demo-aware (honesty checks run with demo=0; extra demo/medicine checks)."""
import os

p = os.path.join(os.path.dirname(__file__), "local_test.py")
s = open(p, encoding="utf-8").read()
pairs = [
    ('def call(method, path, body=None, q=None, expect=200):\n    ev = {',
     'def call(method, path, body=None, q=None, expect=200, demo="0"):\n    q = dict(q or {})\n    q.setdefault("demo", demo)\n    ev = {'),
    ('check(("FACILITY#hosp-mayo", "RES#bed#ICU") not in fakes.STORE, "simulated bed row removed")',
     'check(fakes.STORE.get(("FACILITY#hosp-mayo", "RES#bed#ICU"), {}).get("demo"), "old row replaced by flagged demo row")'),
    ('print("\\nFAILURES:", FAIL if FAIL else "none")',
     'dm = call("POST", "/ask", {"text": "abbu ko seenay mein dard", **L}, demo="1")\n'
     'check(any(h["demo"] and h["freeBeds"] is not None for h in dm["hospitals"]), "demo mode: sample numbers shown and tagged demo")\n'
     'check(any("demo sample" in h["why"] for h in dm["hospitals"]), "demo rows say demo in the why line")\n'
     'mm = call("GET", "/medicine/search", q={"q": "panadol", **L})\n'
     'check(mm["matched"][0]["use"] == "Pain relief and fever" and mm["matched"][0]["rx"] == "otc", "medicine use + prescription status")\n'
     'ma = call("GET", "/medicine/search", q={"q": "augmentin", **L})\n'
     'check(ma["matched"][0]["rx"] == "rx", "antibiotic marked prescription needed")\n'
     'sd = call("GET", "/stats", demo="1")\n'
     'check(len(sd["recentReports"]) > 0, "activity feed has entries")\n'
     'print("\\nFAILURES:", FAIL if FAIL else "none")'),
]
for old, new in pairs:
    assert old in s, old[:60]
    s = s.replace(old, new)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("tests patched")
