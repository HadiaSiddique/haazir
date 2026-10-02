"""Offline smoke test: fake boto3 + in-memory table, exercises every route."""
import json
import os
import sys
import types
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

STORE = {}


class FakeTable:
    def scan(self, **kw):
        return {"Items": [dict(v) for v in STORE.values()]}

    def put_item(self, Item):
        STORE[(Item["pk"], Item["sk"])] = Item

    def get_item(self, Key):
        it = STORE.get((Key["pk"], Key["sk"]))
        return {"Item": dict(it)} if it else {}

    def update_item(self, Key, UpdateExpression, ExpressionAttributeNames, ExpressionAttributeValues):
        it = STORE.setdefault((Key["pk"], Key["sk"]), {"pk": Key["pk"], "sk": Key["sk"]})
        expr = UpdateExpression
        if expr.startswith("SET "):
            for part in expr[4:].split(", "):
                n, v = part.split(" = ")
                it[ExpressionAttributeNames[n]] = ExpressionAttributeValues[v]
        else:
            for part in expr[4:].split(", "):
                n, v = part.split(" ")
                k = ExpressionAttributeNames[n]
                it[k] = it.get(k, 0) + ExpressionAttributeValues[v]

    def query(self, KeyConditionExpression, **kw):
        pk = KeyConditionExpression._values[1]
        items = sorted([v for (p, s), v in STORE.items() if p == pk], key=lambda x: x["sk"], reverse=True)
        return {"Items": items}

    def batch_writer(self, **kw):
        t = self

        class BW:
            def __enter__(s): return s
            def __exit__(s, *a): pass
            def put_item(s, Item): t.put_item(Item)
        return BW()


boto3 = types.ModuleType("boto3")
boto3.resource = lambda *a, **k: types.SimpleNamespace(Table=lambda n: FakeTable())
boto3.client = lambda *a, **k: types.SimpleNamespace(converse=lambda **kw: (_ for _ in ()).throw(RuntimeError("no bedrock offline")))
cond = types.ModuleType("boto3.dynamodb.conditions")


class Key:
    def __init__(self, n): self.n = n
    def eq(self, v):
        o = types.SimpleNamespace(); o._values = (self.n, v); return o


cond.Key = Key
sys.modules.update({"boto3": boto3, "boto3.dynamodb": types.ModuleType("boto3.dynamodb"),
                    "boto3.dynamodb.conditions": cond})
botocore = types.ModuleType("botocore"); bc = types.ModuleType("botocore.config"); bc.Config = lambda **k: None
sys.modules.update({"botocore": botocore, "botocore.config": bc})

