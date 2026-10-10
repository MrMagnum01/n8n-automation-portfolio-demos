# Run evidence

Instance: n8n 2.42.6 (Docker, self-hosted). Workflow id `invPdfToCsv01`, imported from `tools/build_workflow.py` output,
exported afterwards to `workflow.json`.

## Execution

| Field | Value |
|---|---|
| Execution id | 6 |
| Mode | manual (started through the REST API, the same call the UI makes) |
| Status | success |
| Started | 2026-10-10T11:15:16.913Z |
| Stopped | 2026-10-10T11:15:17.507Z (594 ms) |
| Input | 12 PDFs in `in/` (`sample-data/`) |

Per-node results (from the stored execution data):

| Node | Status | Time | Items out |
|---|---|---|---|
| Manual Trigger | success | 0 ms | 1 |
| Read PDFs | success | 43 ms | 12 |
| Extract PDF text | success | 153 ms | 12 |
| Parse invoices | success | 49 ms | 12 |
| Validate | success | 28 ms | 12 |
| Rows: invoices | success | 16 ms | 12 |
| To CSV: invoices | success | 7 ms | 1 |
| Write invoices.csv | success | 13 ms | 1 |
| Rows: line items | success | 11 ms | 40 |
| To CSV: line items | success | 3 ms | 1 |
| Write line_items.csv | success | 5 ms | 1 |
| Rows: exceptions | success | 12 ms | 6 |
| To CSV: exceptions | success | 2 ms | 1 |
| Write exceptions.csv | success | 7 ms | 1 |
| Wait for all CSVs | success | 38 ms | 3 |
| Summary | success | 16 ms | 1 |
| To text: summary | success | 2 ms | 1 |
| Write summary.md | success | 5 ms | 1 |

(Earlier execution ids 1 to 5 on this instance are unrelated: id 1 was a throw-away extraction test of mine, deleted
afterwards; 2 to 5 belong to the other demo.)

## Output files (`output/`)

```
12 output/invoices.csv
40 output/line_items.csv
6 output/exceptions.csv
30 output/summary.md
88 total
```

(`wc -l` counts newlines, and the files have no trailing newline, so each figure equals the data rows excluding the header: 12 invoices, 40 line items, 6 exceptions. A CSV parse gives 13 / 41 / 7 records including the header row.)

### exceptions.csv

```
file,invoice_no,reason,detail
alder-AS-10421_resend.pdf,AS-10421,DUPLICATE_INVOICE_NO,AS-10421 from Alder Street Print Shop already seen in alder-AS-10421.pdf
birchwood-BF-0091.pdf,BF-2026-0091,TOTAL_MISMATCH,"subtotal 1,187.30 + tax 237.46 = 1,424.76, printed total 1,509.76 (diff 85.00)"
birchwood-no-number.pdf,,MISSING_INVOICE_NO,no invoice number found on the document
cobalt-0322.pdf,CA/2026/0322,DUE_BEFORE_INVOICE,due 2026-08-06 is before invoice date 2026-08-15
meridian-MC-7730.pdf,MC-7730,LINES_SUBTOTAL_MISMATCH,"lines add up to 3,885.50, printed subtotal 3,765.50 (diff -120.00)"
scan-0412.pdf,,NO_TEXT_LAYER,"no extractable text (0 chars) - likely a scanned image, needs OCR or manual entry"
```

### summary.md

```
# Invoice batch summary

- PDFs read: 12
- Parsed to structured data: 11
- Clean (passed every check): 6
- Flagged for review: 6

## Exceptions by reason

- DUE_BEFORE_INVOICE: 1
- DUPLICATE_INVOICE_NO: 1
- LINES_SUBTOTAL_MISMATCH: 1
- MISSING_INVOICE_NO: 1
- NO_TEXT_LAYER: 1
- TOTAL_MISMATCH: 1

## Total of clean invoices, by currency

- EUR: 34,857.96
- GBP: 4,421.76
- USD: 3,255.14

## Flagged files

- alder-AS-10421_resend.pdf: DUPLICATE_INVOICE_NO
- birchwood-BF-0091.pdf: TOTAL_MISMATCH
- birchwood-no-number.pdf: MISSING_INVOICE_NO
- cobalt-0322.pdf: DUE_BEFORE_INVOICE
- meridian-MC-7730.pdf: LINES_SUBTOTAL_MISMATCH
- scan-0412.pdf: NO_TEXT_LAYER
```

## Check against ground truth (`python3 tools/verify.py`)

```
PASS alder-AS-10421.pdf expected clean got clean
PASS alder-AS-10433.pdf expected clean got clean
PASS alder-AS-10421_resend.pdf expected ['DUPLICATE_INVOICE_NO'] got ['DUPLICATE_INVOICE_NO']
PASS birchwood-BF-0087.pdf expected clean got clean
PASS birchwood-BF-0091.pdf expected ['TOTAL_MISMATCH'] got ['TOTAL_MISMATCH']
PASS birchwood-no-number.pdf expected ['MISSING_INVOICE_NO'] got ['MISSING_INVOICE_NO']
PASS cobalt-0315.pdf expected clean got clean
PASS cobalt-0322.pdf expected ['DUE_BEFORE_INVOICE'] got ['DUE_BEFORE_INVOICE']
PASS cobalt-0340.pdf expected clean got clean
PASS meridian-MC-7730.pdf expected ['LINES_SUBTOTAL_MISMATCH'] got ['LINES_SUBTOTAL_MISMATCH']
PASS northwind-NW-2201.pdf expected clean got clean
PASS scan-0412.pdf expected ['NO_TEXT_LAYER'] got ['NO_TEXT_LAYER']
12/12 files match ground truth
```

## Self-check for sensitive strings

Command: `grep -RInE "password|token|apikey|api_key|secret|@(?!example)|dedi|tailnet|ts\.net|/home/"` (PCRE) over this folder.
See the final section of this file for the result.

Result: every hit is benign. The only matches are (a) the container path `/home/node/.n8n-files/...` (the n8n file
sandbox inside Docker, not a host path), (b) the names of the two environment variables the helper scripts read
(`N8N_OWNER_*`; values are injected by a secret wrapper at run time and are never printed, stored, or visible in any
screenshot), and (c) this command text itself. No real emails, hostnames, tokens, or host paths are present.
