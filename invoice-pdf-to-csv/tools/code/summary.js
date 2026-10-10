// SUMMARY  (Code node, runs once after the three CSVs are written)
const inv = $('Validate').all().map(i => i.json);
const byReason = {};
inv.forEach(i => i.issues.forEach(x => { byReason[x.code] = (byReason[x.code] || 0) + 1; }));
const ok = inv.filter(i => i.status === 'ok');
const flagged = inv.filter(i => i.status !== 'ok');
const parsed = inv.filter(i => i.status !== 'unreadable');
const sums = {};
ok.forEach(i => { sums[i.currency] = Math.round(((sums[i.currency] || 0) + i.total) * 100) / 100; });
const fmt = x => x.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const md = [
  '# Invoice batch summary', '',
  `- PDFs read: ${inv.length}`,
  `- Parsed to structured data: ${parsed.length}`,
  `- Clean (passed every check): ${ok.length}`,
  `- Flagged for review: ${flagged.length}`, '',
  '## Exceptions by reason', '',
  ...Object.entries(byReason).sort().map(([k, v]) => `- ${k}: ${v}`), '',
  '## Total of clean invoices, by currency', '',
  ...Object.entries(sums).sort().map(([k, v]) => `- ${k}: ${fmt(v)}`), '',
  '## Flagged files', '',
  ...flagged.map(i => `- ${i.file}: ${i.issues.map(x => x.code).join(', ')}`), '',
].join('\n');
return [{ json: {
  pdfs_read: inv.length, parsed: parsed.length, clean: ok.length, flagged: flagged.length,
  exceptions_by_reason: byReason, clean_totals_by_currency: sums, markdown: md,
} }];
