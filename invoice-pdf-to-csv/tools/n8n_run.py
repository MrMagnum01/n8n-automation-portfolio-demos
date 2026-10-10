#!/usr/bin/env python3
"""Run an n8n workflow through the REST API (as the UI does) and wait for it.

Credentials come from the environment (N8N_OWNER_EMAIL / N8N_OWNER_PASSWORD),
injected by the secret store wrapper; they are never printed or written.

    secret run N8N_OWNER_EMAIL N8N_OWNER_PASSWORD -- python3 n8n_run.py <workflow-id> [--dump exec.json]
"""
import http.cookiejar
import json
import os
import sys
import time
import urllib.request

BASE = "http://127.0.0.1:5678"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"Content-Type": "application/json", "browser-id": "demo-runner"})
    try:
        with op.open(req, timeout=120) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} on {method} {path}: {e.read().decode()[:600]}")


def main():
    wf_id = sys.argv[1]
    call("POST", "/rest/login", {"emailOrLdapLoginId": os.environ["N8N_OWNER_EMAIL"],
                                 "password": os.environ["N8N_OWNER_PASSWORD"]})
    wf = call("GET", f"/rest/workflows/{wf_id}")["data"]
    trig = next(n for n in wf["nodes"] if n["type"] == "n8n-nodes-base.manualTrigger")
    res = call("POST", f"/rest/workflows/{wf_id}/run",
               {"workflowData": wf, "triggerToStartFrom": {"name": trig["name"]}})
    ex_id = res["data"]["executionId"]
    print("executionId", ex_id)
    for _ in range(120):
        ex = call("GET", f"/rest/executions/{ex_id}")["data"]
        if ex.get("finished") or ex.get("status") in ("success", "error", "crashed", "canceled"):
            break
        time.sleep(1)
    print("status", ex.get("status"), "startedAt", ex.get("startedAt"), "stoppedAt", ex.get("stoppedAt"))
    if "--dump" in sys.argv:
        with open(sys.argv[sys.argv.index("--dump") + 1], "w") as f:
            json.dump(ex, f)


main()
