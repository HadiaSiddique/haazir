"""DynamoDB access: single table, whole-city snapshot cached briefly in memory."""
import os
import time
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key

TABLE = boto3.resource("dynamodb").Table(os.environ.get("TABLE_NAME", "HaazirData"))
_cache = {"at": 0, "data": None}
CACHE_SECONDS = 10


def plain(v):
    """Convert DynamoDB Decimals to int/float recursively."""
    if isinstance(v, list):
        return [plain(x) for x in v]
    if isinstance(v, dict):
        return {k: plain(x) for k, x in v.items()}
    if isinstance(v, Decimal):
        return int(v) if v == v.to_integral_value() else float(v)
    return v


def dyn(v):
    """Convert floats to Decimal for writes."""
    if isinstance(v, list):
        return [dyn(x) for x in v]
    if isinstance(v, dict):
        return {k: dyn(x) for k, x in v.items()}
    if isinstance(v, float):
        return Decimal(str(round(v, 6)))
    return v


def _scan_all():
    items, kwargs = [], {}
    while True:
        resp = TABLE.scan(**kwargs)
        items.extend(resp.get("Items", []))
        if "LastEvaluatedKey" not in resp:
            return [plain(i) for i in items]
        kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]


def snapshot(force=False):
    """Return {'facilities': {id: meta+resources}, 'ambulances': {id: meta}, 'stats': {...}}."""
    if not force and _cache["data"] and time.time() - _cache["at"] < CACHE_SECONDS:
        return _cache["data"]
    facilities, ambulances, stats = {}, {}, {}
    for it in _scan_all():
        pk, sk = it["pk"], it["sk"]
        if pk.startswith("FACILITY#"):
            fid = pk.split("#", 1)[1]
            f = facilities.setdefault(fid, {"id": fid, "beds": {}, "doctors": {}, "equipment": {},
                                            "medicine": {}, "blood": {}})
            if sk == "META":
                f.update({k: v for k, v in it.items() if k not in ("pk", "sk")})
            else:
                if it.get("demo"):  # demo rows always look recent: age is relative to now
                    it["updatedAt"] = int(time.time()) - int(it.get("demoAgeMin", 10)) * 60
                kind = it.get("kind")
                bucket = {"bed": "beds", "doctor": "doctors", "equipment": "equipment",
                          "medicine": "medicine", "blood": "blood"}.get(kind)
                if bucket:
                    f[bucket][it["key"]] = {k: v for k, v in it.items() if k not in ("pk", "sk")}
        elif pk.startswith("AMBULANCE#"):
            ambulances[it["id"]] = {k: v for k, v in it.items() if k not in ("pk", "sk")}
        elif pk == "STATS":
            stats = {k: v for k, v in it.items() if k not in ("pk", "sk")}
    data = {"facilities": {k: v for k, v in facilities.items() if "type" in v},
            "ambulances": ambulances, "stats": stats}
    _cache.update(at=time.time(), data=data)
    return data


def view(snap, demo=True):
    """The snapshot as seen by a user: with demo rows (default) or real staff reports only."""
    if demo:
        return snap
    facs = {}
    for fid, f in snap["facilities"].items():
        g = dict(f)
        for b in ("beds", "doctors", "equipment", "medicine", "blood"):
            g[b] = {k: v for k, v in f[b].items() if not v.get("demo")}
        facs[fid] = g
    return {**snap, "facilities": facs}


def invalidate():
    _cache["at"] = 0


def put(item):
    TABLE.put_item(Item=dyn(item))
    invalidate()


def get(pk, sk="META"):
    r = TABLE.get_item(Key={"pk": pk, "sk": sk}).get("Item")
    return plain(r) if r else None


def update_fields(pk, sk, fields):
    names, values, sets = {}, {}, []
    for i, (k, v) in enumerate(fields.items()):
        names[f"#f{i}"] = k
        values[f":v{i}"] = dyn(v)
        sets.append(f"#f{i} = :v{i}")
    TABLE.update_item(Key={"pk": pk, "sk": sk}, UpdateExpression="SET " + ", ".join(sets),
                      ExpressionAttributeNames=names, ExpressionAttributeValues=values)
    invalidate()


def bump(**counters):
    """Atomically increment STATS/GLOBAL counters."""
    if not counters:
        return
    names, values, parts = {}, {}, []
    for i, (k, v) in enumerate(counters.items()):
        names[f"#c{i}"] = k
        values[f":c{i}"] = v
        parts.append(f"#c{i} :c{i}")
    try:
        TABLE.update_item(Key={"pk": "STATS", "sk": "GLOBAL"}, UpdateExpression="ADD " + ", ".join(parts),
                          ExpressionAttributeNames=names, ExpressionAttributeValues=values)
    except Exception as e:  # stats must never break a user request
        print("stats bump failed", e)


def query_pk(pk, limit=50):
    resp = TABLE.query(KeyConditionExpression=Key("pk").eq(pk), ScanIndexForward=False, Limit=limit)
    return [plain(i) for i in resp.get("Items", [])]


def batch_delete(keys):
    with TABLE.batch_writer() as bw:
        for pk, sk in keys:
            bw.delete_item(Key={"pk": pk, "sk": sk})
    invalidate()


def batch_write(items):
    with TABLE.batch_writer(overwrite_by_pkeys=["pk", "sk"]) as bw:
        for it in items:
            bw.put_item(Item=dyn(it))
    invalidate()
