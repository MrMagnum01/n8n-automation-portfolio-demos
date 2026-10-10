#!/usr/bin/env python3
"""Render the three result CSVs as one simple static HTML page (for the results screenshot)."""
import csv, html, sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
out = Path(sys.argv[1]) if len(sys.argv) > 1 else root / "output" / "results.html"


def table(name, cols=None, status_col=None, limit=None):
    rows = list(csv.DictReader(open(root / "output" / name, encoding="utf-8-sig")))
    total = len(rows)
    rows = rows[:limit] if limit else rows
    cols = cols or list(rows[0].keys())
    h = [f"<h2>{html.escape(name)} <small>{total} rows{f" (first {len(rows)} shown)" if len(rows) < total else ""}</small></h2><table><tr>"]
    h += [f"<th>{html.escape(c)}</th>" for c in cols] + ["</tr>"]
    for r in rows:
        cls = ""
        if status_col:
            cls = ' class="' + r[status_col] + '"'
        h.append(f"<tr{cls}>" + "".join(
            f'<td class="{ "num" if c in ("subtotal","tax","total","amount","unit_price","qty","line_count","line_no") else ""}">{html.escape(r[c])}</td>'
            for c in cols) + "</tr>")
    h.append("</table>")
    return "".join(h)


page = """<!doctype html><meta charset="utf-8"><title>Invoice batch results</title>
<style>
body{font:13px/1.35 system-ui,sans-serif;margin:22px 28px;color:#1d2330;background:#fff}
h1{font-size:19px;margin:0 0 4px} p{margin:0 0 10px;color:#586274}
h2{font-size:15px;margin:18px 0 6px} h2 small{color:#7a8496;font-weight:400}
table{border-collapse:collapse;width:100%} th,td{border:1px solid #d9dee7;padding:3px 8px;text-align:left;white-space:nowrap}
th{background:#eef1f6} td.num{text-align:right;font-variant-numeric:tabular-nums}
tr.exception td{background:#fff4d6} tr.unreadable td{background:#fde2e2}
</style>
<h1>Invoice batch results</h1>
<p>Rendered from the CSVs the workflow wrote. Yellow = flagged by a check, red = PDF could not be read.</p>
""" + table("invoices.csv", ["file", "invoice_no", "supplier", "invoice_date", "due_date", "currency", "line_count", "subtotal", "tax", "total", "status", "issue_codes"], "status") \
    + table("exceptions.csv") + table("line_items.csv", limit=5).replace("<table>", "<table style='font-size:12px'>", 1)
out.write_text(page)
print("wrote", out)
