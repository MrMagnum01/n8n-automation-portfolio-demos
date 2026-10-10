#!/usr/bin/env python3
"""Synthetic supplier-invoice PDF generator (Python standard library only).

Writes 12 text-based PDFs in 3 layouts plus one image-only "scanned" PDF, and
expected.json (ground truth for the deliberate exceptions).
Fixed seed + no timestamps => byte-for-byte reproducible output.

    python3 generate_invoices.py ../sample-data
"""
import json
import random
import sys
import zlib
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, timedelta
from pathlib import Path

SEED = 140
CENT = Decimal("0.01")


def money(x):
    return Decimal(x).quantize(CENT, rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------- tiny PDF writer
def esc(s):
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_pdf(ops, fonts, image=None):
    """ops: content stream string. fonts: {resource_name: BaseFont}."""
    objs = []  # list of bytes (object bodies)

    def add(b):
        objs.append(b if isinstance(b, bytes) else b.encode("latin-1"))
        return len(objs)

    add("<< /Type /Catalog /Pages 2 0 R >>")          # 1
    add("<< /Type /Pages /Kids [3 0 R] /Count 1 >>")  # 2
    page_obj = len(objs) + 1                          # 3 (filled below)
    add(b"")
    font_ids = {}
    for name, base in fonts.items():
        font_ids[name] = add(f"<< /Type /Font /Subtype /Type1 /BaseFont /{base} /Encoding /WinAnsiEncoding >>")
    content = zlib.compress(ops.encode("latin-1"), 9)
    cid = add(b"<< /Filter /FlateDecode /Length %d >>\nstream\n" % len(content) + content + b"\nendstream")
    res = "/Font << " + " ".join(f"/{n} {i} 0 R" for n, i in font_ids.items()) + " >>"
    if image:
        w, h, raw = image
        data = zlib.compress(raw, 9)
        iid = add(b"<< /Type /XObject /Subtype /Image /Width %d /Height %d /ColorSpace /DeviceGray "
                  b"/BitsPerComponent 8 /Filter /FlateDecode /Length %d >>\nstream\n" % (w, h, len(data))
                  + data + b"\nendstream")
        res += f" /XObject << /Im0 {iid} 0 R >>"
    objs[page_obj - 1] = (f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                          f"/Contents {cid} 0 R /Resources << {res} >> >>").encode("latin-1")
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for o in offsets:
        out += b"%010d 00000 n \n" % o
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    return bytes(out)


class Page:
    def __init__(self):
        self.ops = []

    def text(self, x, y, s, font="F1", size=10):
        self.ops.append(f"BT /{font} {size} Tf {x} {y} Td ({esc(s)}) Tj ET")

    def rule(self, x1, y, x2, w=0.6):
        self.ops.append(f"{w} w {x1} {y} m {x2} {y} l S")

    def box(self, x, y, w, h, gray=0.92):
        self.ops.append(f"{gray} g {x} {y} {w} {h} re f 0 g")


# ---------------------------------------------------------------- formatting per layout
def fmt_us(d):          # 1,234.56
    return f"{d:,.2f}"


def fmt_eu(d):          # 1.234,56
    return f"{d:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def pct(rate):
    return f"{(rate * 100).normalize():f}"


def totals(inv):
    sub = sum((money(q * u) for _, q, u in inv["lines"]), Decimal(0))
    tax = money(sub * inv["tax_rate"])
    return sub, tax, sub + tax


def printed_totals(inv):
    sub, tax, tot = totals(inv)
    if "subtotal_delta" in inv:       # printed subtotal differs from the lines; total follows printed subtotal
        sub = sub + Decimal(inv["subtotal_delta"])
        tax = money(sub * inv["tax_rate"])
        tot = sub + tax
    if "total_override" in inv:
        tot = Decimal(inv["total_override"])
    return sub, tax, tot


# ---------------------------------------------------------------- layout A: "classic" (Courier)
def layout_classic(inv):
    p = Page()
    sub, tax, tot = printed_totals(inv)
    p.box(40, 770, 515, 40)
    p.text(50, 785, inv["supplier"].upper(), "F2", 16)
    p.text(50, 750, inv["address"], "F1", 9)
    p.text(400, 750, "TAX INVOICE", "F2", 14)
    y = 715
    p.text(50, y, f"Invoice No: {inv['number']}", "F1", 10); y -= 14
    p.text(50, y, f"Invoice Date: {inv['date'].isoformat()}", "F1", 10); y -= 14
    p.text(50, y, f"Due Date: {inv['due'].isoformat()}", "F1", 10); y -= 14
    p.text(50, y, f"Currency: {inv['currency']}", "F1", 10); y -= 14
    p.text(50, y, f"Bill To: {inv['customer']}", "F1", 10); y -= 30
    p.text(50, y, f"{'Description':<34}{'Qty':>5}{'Unit Price':>14}{'Amount':>14}", "F2", 10); y -= 6
    p.rule(50, y, 545); y -= 14
    for d, q, u in inv["lines"]:
        p.text(50, y, f"{d:<34}{q:>5}{fmt_us(u):>14}{fmt_us(money(q * u)):>14}", "F1", 10); y -= 14
    p.rule(50, y + 6, 545); y -= 10
    p.text(50, y, f"{'Subtotal:':>53}{fmt_us(sub):>14}", "F1", 10); y -= 14
    p.text(50, y, f"{'Tax (' + pct(inv['tax_rate']) + '%):':>53}{fmt_us(tax):>14}", "F1", 10); y -= 14
    p.text(50, y, f"{'TOTAL DUE:':>53}{fmt_us(tot):>14}", "F2", 10); y -= 40
    p.text(50, y, "Payment terms: net 30 days. Thank you for your business.", "F1", 8)
    return p, {"F1": "Courier", "F2": "Courier-Bold"}


# ---------------------------------------------------------------- layout B: "modern" (Helvetica)
def layout_modern(inv):
    p = Page()
    sub, tax, tot = printed_totals(inv)
    d, due = inv["date"], inv["due"]
    p.text(50, 780, inv["supplier"], "F2", 20)
    p.text(50, 764, inv["address"], "F1", 8)
    p.text(430, 780, "INVOICE", "F2", 20)
    y = 725
    if inv["number"]:
        p.text(50, y, f"Invoice #   {inv['number']}", "F1", 10)
    y -= 15
    p.text(50, y, f"Issued   {d.day:02d} {MON[d.month - 1]} {d.year}", "F1", 10); y -= 15
    p.text(50, y, f"Payment due   {due.day:02d} {MON[due.month - 1]} {due.year}", "F1", 10); y -= 15
    p.text(50, y, f"All amounts in {inv['currency']}", "F1", 10); y -= 15
    p.text(50, y, f"Billed to   {inv['customer']}", "F1", 10); y -= 35
    p.box(45, y - 5, 505, 18)
    p.text(50, y, "ITEM", "F2", 9); y -= 22
    for desc, q, u in inv["lines"]:
        p.text(50, y, f"{desc}   |   {q} x {fmt_us(u)}   |   {fmt_us(money(q * u))}", "F1", 10); y -= 16
    y -= 8
    p.rule(50, y + 10, 545)
    p.text(50, y, f"Net amount   {fmt_us(sub)}", "F1", 10); y -= 15
    p.text(50, y, f"VAT {pct(inv['tax_rate'])}%   {fmt_us(tax)}", "F1", 10); y -= 15
    p.text(50, y, f"Amount payable   {fmt_us(tot)}", "F2", 12)
    return p, {"F1": "Helvetica", "F2": "Helvetica-Bold"}


# ---------------------------------------------------------------- layout C: "compact" (Times, EU numbers)
def layout_compact(inv):
    p = Page()
    sub, tax, tot = printed_totals(inv)
    d, due = inv["date"], inv["due"]
    p.text(50, 790, inv["supplier"], "F2", 15)
    p.text(50, 777, inv["address"], "F1", 8)
    p.text(50, 750, f"Inv. No.: {inv['number']}     Date: {d.day:02d}.{d.month:02d}.{d.year}     "
                    f"Due: {due.day:02d}.{due.month:02d}.{due.year}     Cur: {inv['currency']}", "F1", 10)
    p.text(50, 735, f"Customer: {inv['customer']}", "F1", 10)
    y = 710
    p.rule(50, y + 12, 545)
    p.text(50, y, "Pos.  Description  --  Qty  --  Unit price  --  Total", "F2", 10); y -= 6
    p.rule(50, y, 545); y -= 14
    for i, (desc, q, u) in enumerate(inv["lines"], 1):
        p.text(50, y, f"{i}.  {desc}  --  {q}  --  {fmt_eu(u)}  --  {fmt_eu(money(q * u))}", "F1", 10); y -= 14
    p.rule(50, y + 6, 545); y -= 12
    p.text(50, y, f"Net total: {fmt_eu(sub)}", "F1", 10); y -= 14
    p.text(50, y, f"VAT {pct(inv['tax_rate'])}%: {fmt_eu(tax)}", "F1", 10); y -= 14
    p.text(50, y, f"Gross total: {fmt_eu(tot)}", "F2", 11)
    return p, {"F1": "Times-Roman", "F2": "Times-Bold"}


LAYOUTS = {"classic": layout_classic, "modern": layout_modern, "compact": layout_compact}


# ---------------------------------------------------------------- image-only "scan"
def scanned_pdf(rng):
    w, h = 400, 560
    px = bytearray(b"\xf2" * (w * h))
    for y in range(h):                       # paper grain
        for x in range(0, w, 3):
            px[y * w + x] = 232 + rng.randrange(0, 20)
    for row in range(28):                    # grey "text" bars
        y0 = 40 + row * 17
        x = 30
        while x < w - 40:
            seg = rng.randrange(12, 60)
            if rng.random() > 0.15:
                for yy in range(y0, y0 + 7):
                    for xx in range(x, min(x + seg, w - 30)):
                        px[yy * w + xx] = 40 + rng.randrange(0, 50)
            x += seg + 8
    ops = "q 520 0 0 740 37 50 cm /Im0 Do Q"
    return build_pdf(ops, {"F1": "Helvetica"}, image=(w, h, bytes(px)))


# ---------------------------------------------------------------- the data set
SUPPLIERS = {
    "alder": ("Alder Street Print Shop", "12 Example Road, Sampletown 00001"),
    "birch": ("Birchwood Freight Ltd", "4 Placeholder Lane, Mocktown MT1 0AA"),
    "cobalt": ("Cobalt Analytics GmbH", "Musterstrasse 7, 00000 Beispielstadt"),
    "meridian": ("Meridian Cloud Services", "88 Sample Avenue, Demoville 00002"),
    "north": ("Northwind Office Partners", "1 Fictional Plaza, Testburg 00003"),
}
CUSTOMER = "Fictional Customer Ltd"
CATALOG = {
    "alder": [("Business cards (500)", 45), ("Flyers A5 (1000)", 120), ("Roll-up banner", 85), ("Poster A1", 32), ("Letterhead pad", 18)],
    "birch": [("Pallet freight - zone 2", 140), ("Pallet freight - zone 4", 210), ("Tail-lift surcharge", 35), ("Customs handling", 60), ("Storage per week", 25)],
    "cobalt": [("Dashboard build (day)", 640), ("Data cleaning (day)", 520), ("Training session", 900), ("Report template", 310), ("Support retainer", 450)],
    "meridian": [("Cloud storage 1TB monthly", 48), ("Compute node monthly", 220), ("Backup add-on", 30), ("Priority support", 150), ("Static IP", 8)],
    "north": [("Ergonomic keyboard", 79), ("Laptop stand", 54), ("Printer toner", 96), ("Desk lamp", 41), ("Monitor arm", 112)],
}

# (file, supplier key, layout, number, offset_days, tax, currency, extras, expected_issue)
PLAN = [
    ("alder-AS-10421.pdf", "alder", "classic", "AS-10421", 0, "0.08", "USD", {}, None),
    ("alder-AS-10433.pdf", "alder", "classic", "AS-10433", 14, "0.08", "USD", {}, None),
    ("alder-AS-10421_resend.pdf", "alder", "classic", "AS-10421", 20, "0.08", "USD", {}, "DUPLICATE_INVOICE_NO"),
    ("birchwood-BF-0087.pdf", "birch", "modern", "BF-2026-0087", 3, "0.20", "GBP", {}, None),
    ("birchwood-BF-0091.pdf", "birch", "modern", "BF-2026-0091", 17, "0.20", "GBP", {"total_override": "+85.00"}, "TOTAL_MISMATCH"),
    ("birchwood-no-number.pdf", "birch", "modern", None, 25, "0.20", "GBP", {}, "MISSING_INVOICE_NO"),
    ("cobalt-0315.pdf", "cobalt", "compact", "CA/2026/0315", 6, "0.19", "EUR", {}, None),
    ("cobalt-0322.pdf", "cobalt", "compact", "CA/2026/0322", 12, "0.19", "EUR", {"due_offset": -9}, "DUE_BEFORE_INVOICE"),
    ("cobalt-0340.pdf", "cobalt", "compact", "CA/2026/0340", 31, "0.19", "EUR", {}, None),
    ("meridian-MC-7730.pdf", "meridian", "classic", "MC-7730", 9, "0.10", "USD", {"subtotal_delta": "-120.00"}, "LINES_SUBTOTAL_MISMATCH"),
    ("northwind-NW-2201.pdf", "north", "modern", "NW-2201", 22, "0", "USD", {}, None),
    ("scan-0412.pdf", None, None, None, 0, None, None, {}, "NO_TEXT_LAYER"),
]


def main(outdir):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    base = date(2026, 8, 3)
    truth = []
    for fname, key, layout, number, off, tax, cur, extra, issue in PLAN:
        if key is None:
            (out / fname).write_bytes(scanned_pdf(rng))
            truth.append({"file": fname, "expected_issue": issue})
            continue
        n = rng.randint(2, 5)
        picks = rng.sample(CATALOG[key], n)
        lines = [(d, rng.randint(1, 12), Decimal(u) + Decimal(rng.choice([0, 0, 50, 90])) / 100) for d, u in picks]
        inv_date = base + timedelta(days=off)
        inv = {
            "supplier": SUPPLIERS[key][0], "address": SUPPLIERS[key][1], "customer": CUSTOMER,
            "number": number, "date": inv_date, "due": inv_date + timedelta(days=extra.get("due_offset", 30)),
            "currency": cur, "tax_rate": Decimal(tax), "lines": lines,
        }
        if "total_override" in extra:   # "+85.00" => printed total is 85.00 too high
            inv["total_override"] = totals(inv)[2] + Decimal(extra["total_override"])
        if "subtotal_delta" in extra:
            inv["subtotal_delta"] = extra["subtotal_delta"]
        page, fonts = LAYOUTS[layout](inv)
        (out / fname).write_bytes(build_pdf("\n".join(page.ops), fonts))
        sub, tax_a, tot = printed_totals(inv)
        truth.append({
            "file": fname, "layout": layout, "supplier": inv["supplier"], "invoice_no": number,
            "invoice_date": inv["date"].isoformat(), "due_date": inv["due"].isoformat(), "currency": cur,
            "lines": len(lines), "subtotal": str(sub), "tax": str(tax_a), "total": str(tot), "expected_issue": issue,
        })
    (out / "expected.json").write_text(json.dumps(truth, indent=2) + "\n")
    print(f"wrote {len(PLAN)} PDFs + expected.json to {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "../sample-data")
