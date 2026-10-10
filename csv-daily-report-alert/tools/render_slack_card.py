#!/usr/bin/env python3
"""Render the captured (mock) Slack Block Kit payload as a Slack-like HTML card, and split the sink log
into slack-alert-payload.json / email-alert-payload.json.
Usage: python3 render_slack_card.py <mock-sink-received.jsonl> <outdir>
"""
import html, json, re, sys
src, out = sys.argv[1], sys.argv[2]
recs = [json.loads(l) for l in open(src)]
slack = next(r for r in recs if r["path"].startswith("/slack"))
mail = next(r for r in recs if r["path"].startswith("/email"))
json.dump(slack["body"], open(f"{out}/slack-alert-payload.json", "w"), indent=2)
json.dump(mail["body"], open(f"{out}/email-alert-payload.json", "w"), indent=2)

def md(t):
    t = html.escape(t)
    stash = []
    def keep(m, tag):
        stash.append(f"<{tag}>{m.group(1)}</{tag}>"); return f"\x00{len(stash)-1}\x00"
    t = re.sub(r"```(.*?)```", lambda m: keep(m, "pre"), t, flags=re.S)
    t = re.sub(r"`([^`]+)`", lambda m: keep(m, "code"), t)
    t = re.sub(r"\*([^*\n]+)\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<!\w)_([^_\n]+)_(?!\w)", r"<i>\1</i>", t)
    t = t.replace(":warning:", "&#9888;&#65039;").replace("\n", "<br>")
    t = re.sub(r"\x00(\d+)\x00", lambda m: stash[int(m.group(1))], t)
    return t.replace("<pre><br>", "<pre>").replace("<br><pre>", "<pre>")

parts = []
for b in slack["body"]["blocks"]:
    if b["type"] == "header":
        parts.append(f'<h2>{md(b["text"]["text"])}</h2>')
    elif b["type"] == "section" and "fields" in b:
        parts.append('<div class="fields">' + "".join(f"<div>{md(f['text'])}</div>" for f in b["fields"]) + "</div>")
    elif b["type"] == "section":
        parts.append(f'<div class="sec">{md(b["text"]["text"])}</div>')
    elif b["type"] == "divider":
        parts.append("<hr>")
    elif b["type"] == "context":
        parts.append('<div class="ctx">' + " ".join(md(e["text"]) for e in b["elements"]) + "</div>")
page = f"""<!doctype html><html><head><meta charset="utf-8"><style>
body{{margin:0;background:#fff;font:15px/1.46668 Lato,"Segoe UI",Helvetica,Arial,sans-serif;color:#1d1c1d;padding:28px}}
.chan{{color:#616061;font-size:13px;margin-bottom:10px}}
.msg{{display:flex;gap:10px}} .av{{width:36px;height:36px;border-radius:6px;background:#2a7d6b;color:#fff;font-weight:700;display:flex;align-items:center;justify-content:center;flex:none}}
.body{{max-width:640px}} .name{{font-weight:900}} .app{{background:#e8e8e8;border-radius:3px;font-size:10px;padding:0 4px;margin-left:4px;vertical-align:1px}} .time{{color:#616061;font-size:12px;margin-left:6px}}
.card{{border-left:4px solid #e01e5a;padding:2px 0 2px 12px;margin-top:6px}}
h2{{font-size:18px;margin:6px 0 8px}} .sec{{margin:6px 0}} .fields{{display:grid;grid-template-columns:1fr 1fr;gap:8px 20px;margin:8px 0}}
hr{{border:0;border-top:1px solid #ddd;margin:10px 0}} pre{{background:#f8f8f8;border:1px solid #ddd;border-radius:4px;padding:8px;font:12px/1.4 Monaco,Menlo,Consolas,monospace;margin:4px 0}}
code{{background:#f8f8f8;border:1px solid #ddd;border-radius:3px;color:#c01343;padding:0 3px;font:12px Monaco,Menlo,Consolas,monospace}} .ctx{{color:#616061;font-size:12px;margin-top:8px}}
.mock{{margin-top:16px;color:#98a2b3;font-size:11px}}
</style></head><body><div class="chan"># ops-alerts</div>
<div class="msg"><div class="av">N8</div><div class="body"><div><span class="name">Orders Report Bot</span><span class="app">APP</span><span class="time">07:00</span></div>
<div class="card">{''.join(parts)}</div></div></div>
<div class="mock">Rendering of the captured Block Kit payload (mock webhook, no real Slack used).</div></body></html>"""
open(f"{out}/slack-alert-card.html", "w").write(page)
print("ok")
