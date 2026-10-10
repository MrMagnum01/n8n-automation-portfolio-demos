// One flat row per PDF -> invoices.csv (column order = CSV column order)
const f2 = x => (x == null ? '' : x.toFixed(2));
return $input.all().map(({ json: i }) => ({ json: {
  file: i.file, invoice_no: i.invoice_no ?? '', supplier: i.supplier ?? '', layout: i.layout ?? '',
  invoice_date: i.invoice_date ?? '', due_date: i.due_date ?? '', currency: i.currency ?? '',
  line_count: i.lines.length, subtotal: f2(i.subtotal), tax: f2(i.tax), total: f2(i.total),
  status: i.status, issue_codes: i.issues.map(x => x.code).join(';'),
} }));
