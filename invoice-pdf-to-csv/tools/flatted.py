"""Minimal decoder for the `flatted` JSON format n8n uses to store execution data."""
import json


def parse(s):
    arr = json.loads(s)
    seen = {}

    def res(i):
        if i in seen:
            return seen[i]
        v = arr[i]
        if isinstance(v, list):
            out = []
            seen[i] = out
            out.extend(res(int(x)) if isinstance(x, str) else x for x in v)
            return out
        if isinstance(v, dict):
            out = {}
            seen[i] = out
            for k, x in v.items():
                out[k] = res(int(x)) if isinstance(x, str) else x
            return out
        seen[i] = v
        return v

    return res(0)
