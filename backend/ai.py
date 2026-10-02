"""Amazon Bedrock (Converse API). Every call: 8s timeout, returns None on any failure so callers fall back."""
import base64
import json
import os
import re

import boto3
from botocore.config import Config

MODEL_ID = os.environ.get("MODEL_ID", "us.amazon.nova-lite-v1:0")
_client = boto3.client("bedrock-runtime", config=Config(read_timeout=8, connect_timeout=3,
                                                        retries={"max_attempts": 1}))


def _extract_json(text):
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if m:
        text = m.group(1)
    start = min([i for i in (text.find("{"), text.find("[")) if i >= 0], default=-1)
    if start < 0:
        return None
    end = max(text.rfind("}"), text.rfind("]"))
    try:
        return json.loads(text[start:end + 1])
    except Exception:
        return None


def converse_json(system, user_text, image_b64=None, image_format="jpeg", max_tokens=700):
    content = []
    if image_b64:
        content.append({"image": {"format": image_format, "source": {"bytes": base64.b64decode(image_b64)}}})
    content.append({"text": user_text})
    try:
        resp = _client.converse(
            modelId=MODEL_ID,
            system=[{"text": system}],
            messages=[{"role": "user", "content": content}],
            inferenceConfig={"maxTokens": max_tokens, "temperature": 0},
        )
        text = "".join(b.get("text", "") for b in resp["output"]["message"]["content"])
        return _extract_json(text)
    except Exception as e:
        print("bedrock error:", type(e).__name__, str(e)[:300])
        return None


def converse_text(system, user_text, max_tokens=200):
    try:
        resp = _client.converse(
            modelId=MODEL_ID, system=[{"text": system}],
            messages=[{"role": "user", "content": [{"text": user_text}]}],
            inferenceConfig={"maxTokens": max_tokens, "temperature": 0.2},
        )
        return "".join(b.get("text", "") for b in resp["output"]["message"]["content"]).strip()
    except Exception as e:
        print("bedrock error:", type(e).__name__, str(e)[:300])
        return None
