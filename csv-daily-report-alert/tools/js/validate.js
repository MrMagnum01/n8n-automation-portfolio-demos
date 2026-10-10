// VALIDATION RULES - checked in this order, first failure wins,
// so every bad row carries exactly ONE reason.
const VALID_CURRENCIES = ['USD', 'EUR', 'GBP'];
const VALID_REGIONS = ['EMEA', 'NA', 'APAC', 'LATAM'];
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const PRICE_RE = /^\d+(\.\d{1,2})?$/;         // plain decimal, no thousands separators
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const today = $now.toFormat('yyyy-MM-dd');     // workflow timezone = UTC
const seen = new Set();

return $input.all().map((item, i) => {
  const r = {};
  for (const [k, v] of Object.entries(item.json)) r[k] = String(v ?? '').trim();

  const qty = Number(r.qty);
  let reason = '';
  if (!r.order_id)                                        reason = 'missing_order_id';
  else if (seen.has(r.order_id))                          reason = 'duplicate_order_id';
  else if (!DATE_RE.test(r.order_date) || isNaN(Date.parse(r.order_date))) reason = 'invalid_date';
  else if (r.order_date > today)                          reason = 'future_date';
  else if (!r.customer_email)                             reason = 'missing_email';
  else if (!EMAIL_RE.test(r.customer_email))              reason = 'invalid_email';
  else if (!VALID_REGIONS.includes(r.region))             reason = 'unknown_region';
  else if (!r.sku)                                        reason = 'missing_sku';
  else if (!Number.isInteger(qty) || qty <= 0)            reason = 'bad_quantity';
  else if (!PRICE_RE.test(r.unit_price))                  reason = 'non_numeric_price';
  else if (!VALID_CURRENCIES.includes(r.currency))        reason = 'unknown_currency';

  if (r.order_id) seen.add(r.order_id);
  return { json: { ...r, csv_line: i + 2, reason } };   // csv_line = line number in the source file
});
