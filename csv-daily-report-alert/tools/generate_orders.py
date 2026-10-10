#!/usr/bin/env python3
"""Generate a synthetic daily orders export with deliberately seeded bad rows.

Fixed seed -> identical file every run.  Fictional company: "Ridgeline Trail Supply".
Usage: python3 generate_orders.py [out.csv]
"""
import csv, random, sys
from datetime import date, timedelta

SEED = 20261009
REPORT_DAY = date(2026, 10, 9)          # export covers the last 3 days up to this date
N_ROWS = 220

REGIONS = ["EMEA", "NA", "APAC", "LATAM"]
SKUS = {  # sku -> (unit price)
    "TRL-BOOT-01": 129.00, "TRL-PACK-30": 89.50, "TNT-2P-ALP": 249.00,
    "SLP-BAG-15": 139.90, "STV-GAS-MINI": 34.95, "HDL-LED-400": 44.00,
    "JKT-SHELL-M": 179.00, "SOK-WOOL-3PK": 24.50, "BTL-STL-1L": 19.99,
    "POL-CARB-PR": 69.00,
}
CURRENCY = {"EMEA": "EUR", "NA": "USD", "APAC": "USD", "LATAM": "USD"}
STATUSES = ["paid", "paid", "paid", "shipped", "shipped", "pending", "refunded"]
FIELDS = ["order_id", "order_date", "customer_email", "region", "sku", "qty",
          "unit_price", "currency", "status"]

def main(out):
    rnd = random.Random(SEED)
    rows = []
    for i in range(N_ROWS):
        sku = rnd.choice(list(SKUS))
        region = rnd.choices(REGIONS, weights=[30, 40, 18, 12])[0]
        rows.append({
            "order_id": f"RT-{100200 + i}",
            "order_date": (REPORT_DAY - timedelta(days=rnd.randint(0, 2))).isoformat(),
            "customer_email": f"customer{rnd.randint(1, 140):03d}@example.com",
            "region": region,
            "sku": sku,
            "qty": rnd.choices([1, 2, 3, 4, 5, 10], weights=[45, 25, 12, 8, 6, 4])[0],
            "unit_price": f"{SKUS[sku]:.2f}",
            "currency": CURRENCY[region] if rnd.random() > 0.15 else "USD",
            "status": rnd.choice(STATUSES),
        })
    # Seed 14 bad rows (~6.4%) of varied kinds; each row gets exactly one defect.
    kinds = ["missing_email"] * 3 + ["negative_qty"] * 3 + ["bad_price"] * 3 + \
            ["unknown_currency"] * 2 + ["duplicate_id"] * 2 + ["future_date"]
    idx = rnd.sample(range(5, N_ROWS), len(kinds))
    for kind, i in zip(kinds, idx):
        r = rows[i]
        if kind == "missing_email":
            r["customer_email"] = ""
        elif kind == "negative_qty":
            r["qty"] = -rnd.randint(1, 3)
        elif kind == "bad_price":
            r["unit_price"] = rnd.choice(["N/A", "12,5O", "TBD"])
        elif kind == "unknown_currency":
            r["currency"] = rnd.choice(["XXX", "BTC", "ZZZ"])
        elif kind == "duplicate_id":
            r["order_id"] = rows[rnd.randint(0, 4)]["order_id"]   # clashes with an early good row
        elif kind == "future_date":
            r["order_date"] = (REPORT_DAY + timedelta(days=rnd.randint(200, 400))).isoformat()
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader(); w.writerows(rows)
    print(f"wrote {len(rows)} rows ({len(kinds)} seeded defects) -> {out}")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "../sample-data/orders_latest.csv")
