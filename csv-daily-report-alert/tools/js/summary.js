// Aggregate the validated rows into one summary object.
const rows = $input.all().map(i => i.json);
const bad = rows.filter(r => r.reason);
const good = rows.filter(r => !r.reason);
const settings = $('Settings').first().json;

const LABELS = {
  missing_order_id: 'Missing order id', duplicate_order_id: 'Duplicate order id',
  invalid_date: 'Unparseable date', future_date: 'Order date in the future',
  missing_email: 'Missing customer email', invalid_email: 'Malformed customer email',
  unknown_region: 'Unknown region', missing_sku: 'Missing SKU',
  bad_quantity: 'Quantity not a positive whole number',
  non_numeric_price: 'Unit price not numeric', unknown_currency: 'Unknown currency',
};
const round2 = n => Math.round(n * 100) / 100;

// Revenue = qty x unit_price of VALID rows, refunded orders excluded. Kept per currency (no FX guessing).
const byRegion = {}, totals = {}, skus = {};
let refunded = 0;
for (const r of good) {
  if (r.status === 'refunded') { refunded++; continue; }
  const amount = Number(r.qty) * Number(r.unit_price);
  const k = r.region + '|' + r.currency;
  byRegion[k] ??= { region: r.region, currency: r.currency, orders: 0, units: 0, revenue: 0 };
  byRegion[k].orders++; byRegion[k].units += Number(r.qty); byRegion[k].revenue += amount;
  totals[r.currency] = (totals[r.currency] || 0) + amount;
  skus[r.sku] ??= { sku: r.sku, orders: 0, units: 0 };
  skus[r.sku].orders++; skus[r.sku].units += Number(r.qty);
}
const reasons = {};
for (const r of bad) reasons[r.reason] = (reasons[r.reason] || 0) + 1;
const dates = good.map(r => r.order_date).sort();

return [{ json: {
  run_date: settings.run_date,
  run_at: $now.toISO(),
  source_file: settings.input_file.split('/').pop(),
  company: settings.company,
  rows: rows.length, valid: good.length, invalid: bad.length,
  invalid_pct: rows.length ? round2(100 * bad.length / rows.length) : 0,
  refunded_excluded: refunded,
  order_date_from: dates[0] || null, order_date_to: dates[dates.length - 1] || null,
  revenue_by_region: Object.values(byRegion)
    .map(x => ({ ...x, revenue: round2(x.revenue) }))
    .sort((a, b) => a.region.localeCompare(b.region) || a.currency.localeCompare(b.currency)),
  revenue_totals: Object.entries(totals).map(([currency, v]) => ({ currency, revenue: round2(v) })),
  top_skus: Object.values(skus).sort((a, b) => b.units - a.units || a.sku.localeCompare(b.sku)).slice(0, 5),
  invalid_by_reason: Object.entries(reasons)
    .map(([reason, count]) => ({ reason, label: LABELS[reason] || reason, count }))
    .sort((a, b) => b.count - a.count || a.reason.localeCompare(b.reason)),
  bad_rows: bad.map(r => ({ csv_line: r.csv_line, order_id: r.order_id, reason: r.reason })),
} }];
