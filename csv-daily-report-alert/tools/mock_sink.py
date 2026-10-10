#!/usr/bin/env python3
"""MOCK Slack-webhook / email endpoint. No real Slack or SMTP is contacted anywhere.

Listens on 127.0.0.1:<port> (default 5690) and appends every POST it receives to a JSONL file:
  POST /slack/webhook  -> pretend Slack incoming webhook (replies "ok" like Slack does)
  POST /email/send     -> pretend transactional-email API (replies {"status":"queued"})
Usage: python3 mock_sink.py [port] [out.jsonl]
"""
import json, sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5690
OUT = sys.argv[2] if len(sys.argv) > 2 else "mock-sink-received.jsonl"

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        try:
            body = json.loads(raw)
        except ValueError:
            body = {"_raw": raw.decode("utf-8", "replace")}
        rec = {"received_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "path": self.path, "content_type": self.headers.get("Content-Type"), "body": body}
        with open(OUT, "a") as f:
            f.write(json.dumps(rec) + "\n")
        if self.path.startswith("/slack"):
            payload, ctype = b"ok", "text/plain"
        else:
            payload, ctype = b'{"status":"queued"}', "application/json"
        self.send_response(200); self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(payload))); self.end_headers()
        self.wfile.write(payload)
    def log_message(self, fmt, *a):
        sys.stderr.write("[mock-sink] " + fmt % a + "\n")

if __name__ == "__main__":
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
