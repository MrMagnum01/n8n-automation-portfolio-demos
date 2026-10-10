// One row per line item -> line_items.csv (unreadable PDFs have none)
const f2 = x => x.toFixed(2);
return $input.all().flatMap(({ json: i }) => i.lines.map(l => ({ json: {
  file: i.file, invoice_no: i.invoice_no ?? '', line_no: l.line_no, description: l.description,
  qty: l.qty, unit_price: f2(l.unit_price), amount: f2(l.amount),
} })));
