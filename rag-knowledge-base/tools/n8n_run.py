#!/usr/bin/env python3
"""Run a saved n8n workflow through the editor REST API (manual execution) and wait for it.

Credentials come from the environment (N8N_OWNER_EMAIL / N8N_OWNER_PASSWORD), never from args.
Usage: secret run N8N_OWNER_EMAIL N8N_OWNER_PASSWORD -- python3 n8n_run.py <workflow-id> [trigger-node-name]
       ... n8n_run.py --activate <workflow-id> | --deactivate <workflow-id>
"""
import json, os, sys, time, urllib.request, http.cookiejar

BASE = "http://127.0.0.1:5678"
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))


def call(method, path, body=None):
    req = urllib.request.Request(BASE + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json"})
    try:
        with op.open(req, timeout=600) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, e.read()[:800].decode(), file=sys.stderr)
        raise


call("POST", "/rest/login", {"emailOrLdapLoginId": os.environ["N8N_OWNER_EMAIL"],
                             "password": os.environ["N8N_OWNER_PASSWORD"]})
args = sys.argv[1:]
if args[0] in ("--activate", "--deactivate"):
    wf = call("GET", f"/rest/workflows/{args[1]}")["data"]
    if args[0] == "--activate":
        r = call("POST", f"/rest/workflows/{args[1]}/activate", {"versionId": wf["versionId"]})
    else:
        r = call("POST", f"/rest/workflows/{args[1]}/deactivate", {})
    print(json.dumps({"active": r.get("data", {}).get("active")}))
    sys.exit(0)

wid = args[0]
trigger = args[1] if len(args) > 1 else "Manual Trigger"
wf = call("GET", f"/rest/workflows/{wid}")["data"]
t0 = time.time()
res = call("POST", f"/rest/workflows/{wid}/run", {"workflowData": wf, "triggerToStartFrom": {"name": trigger}})
eid = res["data"]["executionId"]
print("executionId", eid)
while True:
    ex = call("GET", f"/rest/executions/{eid}")["data"]
    if ex.get("finished") or ex.get("status") in ("error", "success", "crashed", "canceled"):
        break
    time.sleep(2)
print("status", ex.get("status"), "seconds", round(time.time() - t0, 1))
