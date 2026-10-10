#!/usr/bin/env python3
"""Builds workflow.json (importable n8n workflow) from the JS snippets in tools/js/.
Usage: python3 build_workflow.py out.json
"""
import json, sys, uuid
from pathlib import Path

JS = Path(__file__).parent / "js"
code = lambda n: (JS / n).read_text()
BASE = "/home/node/.n8n-files/csv-daily-report-alert"   # inside the n8n container
nodes, conns = [], {}

def node(name, type_, ver, pos, params=None, **extra):
    n = {"parameters": params or {}, "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, name)), "name": name,
         "type": type_, "typeVersion": ver, "position": pos}
    n.update(extra); nodes.append(n); return name

def sticky(content, x, y, w, h, color):
    nodes.append({"parameters": {"content": content, "height": h, "width": w, "color": color},
                  "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "sticky" + content[:30])),
                  "name": "Sticky " + content.split("\n")[0].strip("# "),
                  "type": "n8n-nodes-base.stickyNote", "typeVersion": 1, "position": [x, y]})

def link(a, b, out=0):
    conns.setdefault(a, {"main": []})
    while len(conns[a]["main"]) <= out: conns[a]["main"].append([])
    conns[a]["main"][out].append({"node": b, "type": "main", "index": 0})

S = "$('Settings').first().json"
C = "$('Compose report + alerts').first().json"
def assign(name, value): return {"id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "a" + name)), "name": name, "value": value, "type": "string"}

# ---- lane geometry ----
X0, YT, YB = 0, 200, 610      # YT = row-export lane (runs first), YB = report + alert lane
sched = node("Every day 07:00 UTC", "n8n-nodes-base.scheduleTrigger", 1.2, [X0, YT + 140 - 120],
             {"rule": {"interval": [{"field": "cronExpression", "expression": "0 7 * * *"}]}})
manual = node("Manual run (demo)", "n8n-nodes-base.manualTrigger", 1, [X0, YT + 140 + 60])
settings = node("Settings", "n8n-nodes-base.set", 3.4, [X0 + 240, YT + 140], {"assignments": {"assignments": [
    assign("company", "Ridgeline Trail Supply"),
    assign("input_file", f"{BASE}/input/orders_latest.csv"),
    assign("report_dir", f"{BASE}/reports"),
    assign("slack_webhook_url", "http://127.0.0.1:5690/slack/webhook"),
    assign("email_api_url", "http://127.0.0.1:5690/email/send"),
    assign("alert_email_from", "reports@example.com"),
    assign("alert_email_to", "ops-team@example.org"),
    assign("run_date", "={{ $now.toFormat('yyyy-MM-dd') }}"),
]}, "options": {}})
read = node("Read orders CSV", "n8n-nodes-base.readWriteFile", 1, [X0 + 540, YT + 140],
            {"operation": "read", "fileSelector": f"={{{{ {S}.input_file }}}}", "options": {}})
parse = node("Parse CSV", "n8n-nodes-base.extractFromFile", 1.1, [X0 + 760, YT + 140],
             {"operation": "csv", "options": {"headerRow": True}})
validate = node("Validate rows", "n8n-nodes-base.code", 2, [X0 + 1040, YT + 140],
                {"mode": "runOnceForAllItems", "language": "javaScript", "jsCode": code("validate.js")})

# lane 1: split + export rows
split = node("Valid or invalid?", "n8n-nodes-base.if", 2.2, [X0 + 1340, YT + 140], {"conditions": {
    "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict", "version": 2},
    "conditions": [{"id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "c1")), "leftValue": "={{ $json.reason }}", "rightValue": "",
                    "operator": {"type": "string", "operation": "empty", "singleValue": True}}],
    "combinator": "and"}, "options": {}})
vcsv = node("Valid rows to CSV", "n8n-nodes-base.convertToFile", 1.1, [X0 + 1620, YT + 40],
            {"operation": "csv", "options": {"fileName": "valid_rows.csv"}})
vsave = node("Save valid_rows.csv", "n8n-nodes-base.readWriteFile", 1, [X0 + 1840, YT + 40],
             {"operation": "write", "fileName": f"={{{{ {S}.report_dir }}}}/valid_rows_{{{{ {S}.run_date }}}}.csv", "options": {}})
bcsv = node("Bad rows to CSV", "n8n-nodes-base.convertToFile", 1.1, [X0 + 1620, YT + 240],
            {"operation": "csv", "options": {"fileName": "bad_rows.csv"}})
bsave = node("Save bad_rows.csv", "n8n-nodes-base.readWriteFile", 1, [X0 + 1840, YT + 240],
             {"operation": "write", "fileName": f"={{{{ {S}.report_dir }}}}/bad_rows_{{{{ {S}.run_date }}}}.csv", "options": {}})

# lane 2: summary -> report -> alert
summ = node("Build summary", "n8n-nodes-base.code", 2, [X0 + 1340, YB + 40],
            {"mode": "runOnceForAllItems", "language": "javaScript", "jsCode": code("summary.js")})
comp = node("Compose report + alerts", "n8n-nodes-base.code", 2, [X0 + 1620, YB + 40],
            {"mode": "runOnceForAllItems", "language": "javaScript", "jsCode": code("compose.js")})
rhtml = node("Report to HTML file", "n8n-nodes-base.convertToFile", 1.1, [X0 + 1840, YB + 40],
             {"operation": "toText", "sourceProperty": "html", "binaryPropertyName": "data",
              "options": {"fileName": "report.html"}})
rsave = node("Save report.html", "n8n-nodes-base.readWriteFile", 1, [X0 + 2060, YB + 40],
             {"operation": "write", "fileName": f"={{{{ {C}.files.reportFile }}}}", "options": {}})
anyb = node("Any bad rows?", "n8n-nodes-base.if", 2.2, [X0 + 2400, YB + 40], {"conditions": {
    "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict", "version": 2},
    "conditions": [{"id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "c2")), "leftValue": f"={{{{ {C}.invalid }}}}", "rightValue": 0,
                    "operator": {"type": "number", "operation": "gt"}}],
    "combinator": "and"}, "options": {}})
def post(name, y, urlkey, body):
    return node(name, "n8n-nodes-base.httpRequest", 4.2, [X0 + 2700, y],
                {"method": "POST", "url": f"={{{{ {S}.{urlkey} }}}}", "sendBody": True, "specifyBody": "json",
                 "jsonBody": f"={{{{ JSON.stringify({C}.{body}) }}}}", "options": {"timeout": 10000}},
                retryOnFail=True, maxTries=3, waitBetweenTries=2000)
slack = post("Post Slack alert (mock)", YB - 60, "slack_webhook_url", "slack")
mail = post("Send email alert (mock)", YB + 140, "email_api_url", "email")

for a, b in [(sched, settings), (manual, settings), (settings, read), (read, parse), (parse, validate),
             (validate, split), (vcsv, vsave), (bcsv, bsave), (validate, summ), (summ, comp), (comp, rhtml),
             (rhtml, rsave), (rsave, anyb)]:
    link(a, b)
link(split, vcsv, 0); link(split, bcsv, 1); link(anyb, slack, 0); link(anyb, mail, 0)

# ---- sticky notes (section labels) ----
sticky("# Daily orders CSV: validate, report, alert\n"
       "Reads the morning orders export, checks every row against **11 readable rules** (one reason per bad row), "
       "writes an HTML report plus `valid_rows` / `bad_rows` CSVs, and, if anything is wrong, posts a Slack-format "
       "alert and an email payload.\n\n"
       "**Mock endpoints:** Slack and email go to a local sink on `127.0.0.1`. Swap the two URLs in *Settings* for a real Slack webhook / email API.",
       -40, -190, 1180, 200, 7)
sticky("## 1. Triggers & settings\nDaily at **07:00 UTC**. The manual trigger is for demo / test runs. "
       "*Settings* holds paths, endpoints and recipients in one place.", -40, 20, 480, 520, 4)
sticky("## 2. Ingest\nRead the CSV from disk and parse it to one item per row. "
       "Swap for *Google Sheets* or *HTTP / SFTP* to read a different source.", 500, 20, 440, 520, 3)
sticky("## 3. Validate\nOne Code node, rules in plain JS. First failing rule wins, so each bad row has exactly one `reason`.", 960, 20, 260, 520, 6)
sticky("## 4. Split & export rows\nValid and invalid rows are written to separate CSVs in the report folder.", 1260, 20, 800, 550, 5)
sticky("## 5. Summarise & report\nTotals, revenue by region, top SKUs, invalid-by-reason, then render the HTML report.", 1260, 585, 1060, 270, 2)
sticky("## 6. Alert if bad rows\nIF invalid > 0: POST Slack Block Kit JSON and an email payload (retry x3).", 2340, 480, 740, 400, 1)

wf = {"name": "Daily orders CSV: validate, report, alert", "nodes": nodes, "connections": conns, "active": False,
      "settings": {"executionOrder": "v1", "timezone": "UTC"}, "pinData": {}, "tags": [],
      "id": "csvDailyReport01"}
Path(sys.argv[1]).write_text(json.dumps(wf, indent=2))
print("wrote", sys.argv[1], len(nodes), "nodes")
