#!/usr/bin/env python3
"""Render output/answers.json as a small standalone HTML page (used for the answers screenshot)."""
import html, json, sys
src, dst = sys.argv[1], sys.argv[2]
d = json.load(open(src))
s = d["summary"]
rows = []
for a in d["answers"]:
    ok = a["correct"]
    cites = "".join(f'<span class="cite">[{html.escape(c)}]</span>' for c in a["citations"])
    ans = html.escape(a["answer"])
    rows.append(f'''<div class="card {'ok' if ok else 'bad'}">
<div class="q"><b>{html.escape(a["id"])}</b> {html.escape(a["question"])}</div>
<div class="a"><span class="tag {a["status"].lower()}">{a["status"]}</span> {ans} {cites}</div>
<div class="m">expected: {a["expected_action"]}{(" / " + ", ".join(a["expected_docs"])) if a["expected_docs"] else ""} &middot; rule check: {"PASS" if ok else "FAIL"} &middot; {a["latency_s"]}s</div></div>''')
page = f'''<!doctype html><meta charset="utf-8"><title>RAG answers</title><style>
body{{font:15px/1.45 system-ui,sans-serif;background:#f6f7f9;color:#1d2330;margin:0;padding:28px;max-width:1000px}}
h1{{font-size:20px;margin:0 0 6px}} .sum{{margin:0 0 18px;color:#46506a}}
.card{{background:#fff;border:1px solid #dde1ea;border-left:5px solid #2f8f5b;border-radius:6px;padding:12px 16px;margin:0 0 12px}}
.card.bad{{border-left-color:#c0392b}} .q{{margin-bottom:6px}} .m{{margin-top:6px;font-size:12.5px;color:#6a7285}}
.tag{{font-size:11.5px;font-weight:700;padding:2px 7px;border-radius:4px;margin-right:6px}}
.tag.answer{{background:#e1f3ea;color:#1c6b43}} .tag.abstain{{background:#fdf0d5;color:#8a5a00}}
.cite{{display:inline-block;font:12.5px ui-monospace,monospace;background:#e8edf8;color:#27408b;border-radius:4px;padding:1px 6px;margin-left:4px}}
</style><h1>Company knowledge base Q&amp;A - real run (local models, $0 metered)</h1>
<p class="sum">{s["answered_with_correct_doc_citation"]}/{s["answerable"]} answerable questions answered with the expected document cited &middot;
{s["abstained_correctly"]}/{s["should_abstain"]} unanswerable questions correctly abstained &middot; median {s["latency_s_per_question"]["median"]}s per question
(rule-based scoring, no LLM judge)</p>
{"".join(rows)}'''
open(dst, "w").write(page)
