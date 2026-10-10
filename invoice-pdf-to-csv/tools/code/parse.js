// PARSE INVOICES  (Code node, "Run once for all items")
// One regex profile per supplier layout. To support a new layout, add a profile below;
// nothing else in the workflow changes.
//   classic : "TAX INVOICE" header, "Invoice No:" labels, ISO dates, 1,234.56 numbers
//   modern  : "INVOICE" + "Invoice #", "04 Aug 2026" dates, "desc | qty x unit | amount" rows
//   compact : one-line header "Inv. No.: .. Date: .. Due: .. Cur: ..", dd.mm.yyyy, 1.234,56 numbers
const MON = { jan: 1, feb: 2, mar: 3, apr: 4, may: 5, jun: 6, jul: 7, aug: 8, sep: 9, oct: 10, nov: 11, dec: 12 };
const pad = n => String(n).padStart(2, '0');

const dateParsers = {
  iso: s => (/^(\d{4})-(\d{2})-(\d{2})$/.exec(s) || []).slice(1).join('-') || null,
  dmy_mon: s => { const m = /^(\d{1,2}) ([A-Za-z]{3}) (\d{4})$/.exec(s); return m && MON[m[2].toLowerCase()] ? `${m[3]}-${pad(MON[m[2].toLowerCase()])}-${pad(m[1])}` : null; },
  dmy_dot: s => { const m = /^(\d{1,2})\.(\d{1,2})\.(\d{4})$/.exec(s); return m ? `${m[3]}-${pad(m[2])}-${pad(m[1])}` : null; },
};
const numParsers = {
  us: s => Number(s.replace(/,/g, '')),                       // 1,234.56
  eu: s => Number(s.replace(/\./g, '').replace(',', '.')),   // 1.234,56
};
const AMT = { us: '-?[\\d,]+\\.\\d{2}', eu: '-?[\\d.]+,\\d{2}' };

const PROFILES = {
  classic: {
    detect: /^TAX INVOICE\b|\bTAX INVOICE$/m,
    supplier: /^(.+)\n/,                                       // first line
    invoice_no: /^Invoice No:[ \t]*(.*)$/m,
    invoice_date: /^Invoice Date:[ \t]*(.*)$/m,
    due_date: /^Due Date:[ \t]*(.*)$/m,
    currency: /^Currency:[ \t]*([A-Z]{3})/m,
    dateFmt: 'iso', numFmt: 'us',
    linesStart: /^Description\s+Qty/m, linesEnd: /^Subtotal:/m,
    line: new RegExp(`^(.+?)\\s+(\\d+)\\s+(${AMT.us})\\s+(${AMT.us})$`),
    subtotal: new RegExp(`^Subtotal:[ \\t]*(${AMT.us})`, 'm'),
    tax: new RegExp(`^Tax \\([\\d.]+%\\):[ \\t]*(${AMT.us})`, 'm'),
    total: new RegExp(`^TOTAL DUE:[ \\t]*(${AMT.us})`, 'm'),
  },
  modern: {
    detect: /^INVOICE$/m,
    supplier: /^(.+)\n/,
    invoice_no: /^Invoice #[ \t]*(.*)$/m,                     // line is absent on some PDFs -> null
    invoice_date: /^Issued[ \t]+(.*)$/m,
    due_date: /^Payment due[ \t]+(.*)$/m,
    currency: /^All amounts in[ \t]+([A-Z]{3})/m,
    dateFmt: 'dmy_mon', numFmt: 'us',
    linesStart: /^ITEM$/m, linesEnd: /^Net amount/m,
    line: new RegExp(`^(.+?) \\| (\\d+) x (${AMT.us}) \\| (${AMT.us})$`),
    subtotal: new RegExp(`^Net amount[ \\t]+(${AMT.us})`, 'm'),
    tax: new RegExp(`^VAT [\\d.]+%[ \\t]+(${AMT.us})`, 'm'),
    total: new RegExp(`^Amount payable[ \\t]+(${AMT.us})`, 'm'),
  },
  compact: {
    detect: /^Inv\. No\.:/m,
    supplier: /^(.+)\n/,
    invoice_no: /^Inv\. No\.:[ \t]*(.*?)[ \t]*Date:/m,
    invoice_date: /Date:[ \t]*(\S+)[ \t]+Due:/m,
    due_date: /Due:[ \t]*(\S+)[ \t]+Cur:/m,
    currency: /Cur:[ \t]*([A-Z]{3})/m,
    dateFmt: 'dmy_dot', numFmt: 'eu',
    linesStart: /^Pos\. Description/m, linesEnd: /^Net total:/m,
    line: new RegExp(`^\\d+\\.\\s+(.+?) -- (\\d+) -- (${AMT.eu}) -- (${AMT.eu})$`),
    subtotal: new RegExp(`^Net total:[ \\t]*(${AMT.eu})`, 'm'),
    tax: new RegExp(`^VAT [\\d.]+%:[ \\t]*(${AMT.eu})`, 'm'),
    total: new RegExp(`^Gross total:[ \\t]*(${AMT.eu})`, 'm'),
  },
};

const grab = (re, text) => { const m = re.exec(text); return m ? (m[1] ?? '').trim() || null : null; };
const r2 = x => Math.round(x * 100) / 100;

// File names come from the Read node (Extract from File drops binaries but keeps item pairing).
const names = $('Read PDFs').all().map(i => i.binary?.data?.fileName ?? 'unknown.pdf');
const results = [];

$input.all().forEach((item, idx) => {
  const file = names[item.pairedItem?.item ?? idx];
  const base = { file, layout: null, supplier: null, invoice_no: null, invoice_date: null, due_date: null,
                 currency: null, lines: [], subtotal: null, tax: null, total: null, parse_error: null, text_chars: 0 };
  if (item.json.error) { results.push({ json: { ...base, parse_error: 'PDF_READ_ERROR' } }); return; }
  const text = String(item.json.text ?? '').replace(/\r/g, '').trim();
  base.text_chars = text.length;
  if (text.length < 20) { results.push({ json: { ...base, parse_error: 'NO_TEXT_LAYER' } }); return; }  // scanned / image-only
  const layout = Object.keys(PROFILES).find(k => PROFILES[k].detect.test(text));
  if (!layout) { results.push({ json: { ...base, parse_error: 'UNKNOWN_LAYOUT' } }); return; }
  const P = PROFILES[layout];
  const num = s => (s == null ? null : r2(numParsers[P.numFmt](s)));
  const date = s => (s == null ? null : dateParsers[P.dateFmt](s));

  // line items = every row between the table header and the totals block
  const from = text.search(P.linesStart), to = text.search(P.linesEnd);
  const lines = text.slice(from, to < 0 ? undefined : to).split('\n').map(l => l.trim()).flatMap((l, n) => {
    const m = P.line.exec(l);
    return m ? [{ line_no: 0, description: m[1].trim(), qty: Number(m[2]), unit_price: num(m[3]), amount: num(m[4]) }] : [];
  }).map((l, n) => ({ ...l, line_no: n + 1 }));

  let supplier = grab(P.supplier, text + '\n');
  if (supplier && supplier === supplier.toUpperCase()) supplier = supplier.replace(/\w\S*/g, w => w[0] + w.slice(1).toLowerCase());
  results.push({ json: {
    ...base, layout, supplier,
    invoice_no: grab(P.invoice_no, text), invoice_date: date(grab(P.invoice_date, text)), due_date: date(grab(P.due_date, text)),
    currency: grab(P.currency, text), lines,
    subtotal: num(grab(P.subtotal, text)), tax: num(grab(P.tax, text)), total: num(grab(P.total, text)),
  } });
});

results.sort((a, b) => (a.json.file < b.json.file ? -1 : a.json.file > b.json.file ? 1 : 0));
return results;
