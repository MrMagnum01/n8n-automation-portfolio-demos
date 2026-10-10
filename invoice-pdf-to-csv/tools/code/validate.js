// VALIDATE  (Code node, "Run once for all items")
// Checks, each producing a machine-readable reason code:
//   NO_TEXT_LAYER / UNKNOWN_LAYOUT / PDF_READ_ERROR   parser could not read the file (from Parse step)
//   MISSING_INVOICE_NO, MISSING_FIELD                 required fields
//   LINE_AMOUNT_MISMATCH                              qty x unit price != printed line amount
//   LINES_SUBTOTAL_MISMATCH                           sum of lines != printed subtotal
//   TOTAL_MISMATCH                                    subtotal + tax != printed total
//   DUE_BEFORE_INVOICE                                due date earlier than invoice date
//   DUPLICATE_INVOICE_NO                              same supplier + invoice number already seen (in file-name order)
const TOLERANCE = 0.02;                       // currency units; absorbs per-line rounding
const REQUIRED = ['supplier', 'invoice_date', 'due_date', 'currency', 'subtotal', 'tax', 'total'];
const money = x => x.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const diff = (a, b) => Math.round((a - b) * 100) / 100;

const firstSeen = new Map();
return $input.all().map(({ json: inv }) => {
  const issues = [];
  const add = (code, detail) => issues.push({ code, detail });

  if (inv.parse_error) {
    add(inv.parse_error, inv.parse_error === 'NO_TEXT_LAYER'
      ? `no extractable text (${inv.text_chars} chars) - likely a scanned image, needs OCR or manual entry`
      : inv.parse_error === 'UNKNOWN_LAYOUT' ? 'text found but no layout profile matches' : 'PDF could not be read');
    return { json: { ...inv, status: 'unreadable', issues } };
  }

  if (!inv.invoice_no) add('MISSING_INVOICE_NO', 'no invoice number found on the document');
  for (const f of REQUIRED) if (inv[f] == null) add('MISSING_FIELD', `${f} not found`);
  if (!inv.lines.length) add('MISSING_FIELD', 'no line items found');

  for (const l of inv.lines) {
    const d = diff(l.qty * l.unit_price, l.amount);
    if (Math.abs(d) > TOLERANCE) add('LINE_AMOUNT_MISMATCH', `line ${l.line_no} "${l.description}": ${l.qty} x ${money(l.unit_price)} = ${money(l.qty * l.unit_price)}, printed ${money(l.amount)}`);
  }
  if (inv.lines.length && inv.subtotal != null) {
    const sum = diff(inv.lines.reduce((s, l) => s + l.amount, 0), 0);
    const d = diff(inv.subtotal, sum);
    if (Math.abs(d) > TOLERANCE) add('LINES_SUBTOTAL_MISMATCH', `lines add up to ${money(sum)}, printed subtotal ${money(inv.subtotal)} (diff ${money(d)})`);
  }
  if (inv.subtotal != null && inv.tax != null && inv.total != null) {
    const expect = diff(inv.subtotal + inv.tax, 0);
    const d = diff(inv.total, expect);
    if (Math.abs(d) > TOLERANCE) add('TOTAL_MISMATCH', `subtotal ${money(inv.subtotal)} + tax ${money(inv.tax)} = ${money(expect)}, printed total ${money(inv.total)} (diff ${money(d)})`);
  }
  if (inv.invoice_date && inv.due_date && inv.due_date < inv.invoice_date)   // ISO strings sort chronologically
    add('DUE_BEFORE_INVOICE', `due ${inv.due_date} is before invoice date ${inv.invoice_date}`);

  if (inv.invoice_no) {
    const key = `${(inv.supplier || '').toLowerCase()}|${inv.invoice_no.toUpperCase()}`;
    if (firstSeen.has(key)) add('DUPLICATE_INVOICE_NO', `${inv.invoice_no} from ${inv.supplier} already seen in ${firstSeen.get(key)}`);
    else firstSeen.set(key, inv.file);
  }
  return { json: { ...inv, status: issues.length ? 'exception' : 'ok', issues } };
});
