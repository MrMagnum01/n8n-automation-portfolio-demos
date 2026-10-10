#!/usr/bin/env python3
"""Compare output/exceptions.csv + invoices.csv against sample-data/expected.json (ground truth)."""
import csv, json, sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
truth = {t["file"]: t for t in json.load(open(root / "sample-data/expected.json"))}
rows = {r["file"]: r for r in csv.DictReader(open(root / "output/invoices.csv", encoding="utf-8-sig"))}
exc = {}
for r in csv.DictReader(open(root / "output/exceptions.csv", encoding="utf-8-sig")):
    exc.setdefault(r["file"], []).append(r["reason"])
bad = 0
for f, t in truth.items():
    got = exc.get(f, [])
    want = [t["expected_issue"]] if t["expected_issue"] else []
    r = rows[f]
    fields_ok = True
    if t["expected_issue"] != "NO_TEXT_LAYER":
        for k_t, k_r in [("invoice_no", "invoice_no"), ("invoice_date", "invoice_date"), ("due_date", "due_date"),
                         ("currency", "currency"), ("subtotal", "subtotal"), ("tax", "tax"), ("total", "total"), ("supplier", "supplier")]:
            if (t[k_t] or "") != r[k_r]:
                fields_ok = False
                print("  field mismatch", f, k_t, t[k_t], r[k_r])
        fields_ok &= int(r["line_count"]) == t["lines"]
    ok = got == want and fields_ok
    bad += not ok
    print(("PASS" if ok else "FAIL"), f, "expected", want or "clean", "got", got or "clean")
print(f"{len(truth) - bad}/{len(truth)} files match ground truth")
sys.exit(1 if bad else 0)
