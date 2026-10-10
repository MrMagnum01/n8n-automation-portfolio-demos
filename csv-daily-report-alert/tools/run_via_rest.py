# Triggers the workflow over the n8n REST API. Run as: secret run N8N_OWNER_EMAIL N8N_OWNER_PASSWORD -- python3 run_via_rest.py
# (credentials come from the environment only; nothing is stored in this folder)
import os, json, urllib.request, http.cookiejar, sys
base="http://127.0.0.1:5678"
cj=http.cookiejar.CookieJar(); op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
def req(path, data=None, method=None):
    r=urllib.request.Request(base+path, data=json.dumps(data).encode() if data is not None else None, method=method, headers={"Content-Type":"application/json"})
    try: return json.load(op.open(r))
    except urllib.error.HTTPError as e: print(e.code, e.read()[:500]); raise
req("/rest/login", {"emailOrLdapLoginId":os.environ["N8N_OWNER_EMAIL"],"email":os.environ["N8N_OWNER_EMAIL"],"password":os.environ["N8N_OWNER_PASSWORD"]})
wf=req("/rest/workflows/csvDailyReport01")["data"]
res=req("/rest/workflows/csvDailyReport01/run", {"workflowData":wf, "triggerToStartFrom":{"name":"Manual run (demo)"}})
print(json.dumps(res)[:500])
