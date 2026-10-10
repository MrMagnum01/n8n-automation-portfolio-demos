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
