#!/usr/bin/env python3
"""Builds build/workflow.src.json (importable n8n workflow) from the Code-node sources in tools/code/."""
import json
from pathlib import Path

HERE = Path(__file__).parent
CODE = lambda n: (HERE / "code" / n).read_text()
BASE = "/home/node/.n8n-files/invoice-pdf-to-csv"
nodes, conns = [], {}


def node(name, type_, ver, pos, params, **extra):
    nodes.append({"parameters": params, "id": f"n-{len(nodes) + 1:02d}", "name": name, "type": type_,
                  "typeVersion": ver, "position": pos, **extra})


def sticky(name, pos, w, h, text, color=7):
    node(name, "n8n-nodes-base.stickyNote", 1, pos, {"content": text, "height": h, "width": w, "color": color})


def link(a, b, out=0, inp=0):
    conns.setdefault(a, {"main": []})
    m = conns[a]["main"]
    while len(m) <= out:
        m.append([])
    m[out].append({"node": b, "type": "main", "index": inp})


def csv_branch(tag, y, code_file, filename, label):
    node(f"Rows: {label}", "n8n-nodes-base.code", 2, [820, y], {"jsCode": CODE(code_file)})
    node(f"To CSV: {label}", "n8n-nodes-base.convertToFile", 1.1, [980, y],
         {"operation": "csv", "options": {"fileName": filename, "headerRow": True}})
    node(f"Write {filename}", "n8n-nodes-base.readWriteFile", 1, [1140, y],
         {"operation": "write", "fileName": f"={BASE}/out/{filename}", "dataPropertyName": "data", "options": {}})
    link("Validate", f"Rows: {label}")
    link(f"Rows: {label}", f"To CSV: {label}")
    link(f"To CSV: {label}", f"Write {filename}")


Y = 300
node("Manual Trigger", "n8n-nodes-base.manualTrigger", 1, [0, Y], {})
node("Schedule (disabled)", "n8n-nodes-base.scheduleTrigger", 1.2, [0, Y + 170],
     {"rule": {"interval": [{"field": "cronExpression", "expression": "0 7 * * 1-5"}]}}, disabled=True)
node("Read PDFs", "n8n-nodes-base.readWriteFile", 1, [180, Y],
     {"operation": "read", "fileSelector": f"{BASE}/in/*.pdf", "options": {}})
node("Extract PDF text", "n8n-nodes-base.extractFromFile", 1, [340, Y],
     {"operation": "pdf", "options": {}}, onError="continueRegularOutput")
node("Parse invoices", "n8n-nodes-base.code", 2, [500, Y], {"jsCode": CODE("parse.js")})
node("Validate", "n8n-nodes-base.code", 2, [660, Y], {"jsCode": CODE("validate.js")})
csv_branch("inv", Y - 160, "rows_invoices.js", "invoices.csv", "invoices")
csv_branch("lin", Y, "rows_lines.js", "line_items.csv", "line items")
csv_branch("exc", Y + 160, "rows_exceptions.js", "exceptions.csv", "exceptions")
node("Wait for all CSVs", "n8n-nodes-base.merge", 3, [1300, Y], {"numberInputs": 3})
node("Summary", "n8n-nodes-base.code", 2, [1460, Y], {"jsCode": CODE("summary.js"), "mode": "runOnceForAllItems"})
node("To text: summary", "n8n-nodes-base.convertToFile", 1.1, [1620, Y],
     {"operation": "toText", "sourceProperty": "markdown", "options": {"fileName": "summary.md"}})
node("Write summary.md", "n8n-nodes-base.readWriteFile", 1, [1780, Y],
     {"operation": "write", "fileName": f"={BASE}/out/summary.md", "dataPropertyName": "data", "options": {}})

for a, b in [("Manual Trigger", "Read PDFs"), ("Schedule (disabled)", "Read PDFs"), ("Read PDFs", "Extract PDF text"),
             ("Extract PDF text", "Parse invoices"), ("Parse invoices", "Validate")]:
    link(a, b)
link("Write invoices.csv", "Wait for all CSVs", 0, 0)
link("Write line_items.csv", "Wait for all CSVs", 0, 1)
link("Write exceptions.csv", "Wait for all CSVs", 0, 2)
link("Wait for all CSVs", "Summary")
link("Summary", "To text: summary")
link("To text: summary", "Write summary.md")

sticky("Note: title", [-60, Y - 400], 1000, 150,
       "## Supplier invoice PDFs -> CSV, with exception flagging\nReads every PDF in a folder, extracts the text layer, parses it with one regex profile per supplier layout, "
       "validates the arithmetic, dates and duplicates, and writes `invoices.csv`, `line_items.csv`, `exceptions.csv` and a summary. Deterministic: no LLM, no external calls.", 4)
sticky("Note: 1 trigger + read", [-60, Y - 200], 480, 520,
       "### 1. Trigger and read\nManual run, or the (disabled) weekday 07:00 schedule.\nRead every `*.pdf` in the input folder (glob), then pull the text layer out of each.\n"
       "A PDF with no text (scanned image) comes through with empty text and is flagged later.", 6)
sticky("Note: 2 parse", [440, Y - 200], 160, 520,
       "### 2. Parse\nRegex profile per layout: classic, modern, compact. Handles ISO / `04 Aug 2026` / `dd.mm.yyyy` dates and `1,234.56` / `1.234,56` numbers.", 5)
sticky("Note: 3 validate", [610, Y - 200], 160, 520,
       "### 3. Validate\nLines vs subtotal, subtotal + tax vs total (tolerance 0.02), required fields, due vs invoice date, duplicate numbers.", 3)
sticky("Note: 4 outputs", [780, Y - 250], 520, 650,
       "### 4. Three CSV outputs\nOne row per invoice, one per line item, one per exception (file, invoice_no, reason, detail).", 4)
sticky("Note: 5 summary", [1310, Y - 200], 560, 520,
       "### 5. Summary\nWaits for all three files, then counts invoices and exceptions by reason and writes `summary.md`.", 7)

wf = {"id": "invPdfToCsv01", "name": "Invoice PDFs to CSV with exception flagging", "nodes": nodes, "connections": conns,
      "settings": {"executionOrder": "v1"}, "pinData": {}, "active": False}
(HERE.parent / "build").mkdir(exist_ok=True)
(HERE.parent / "build" / "workflow.src.json").write_text(json.dumps(wf, indent=2))
print(len(nodes), "nodes")
