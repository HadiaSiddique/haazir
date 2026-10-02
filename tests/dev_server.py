"""Local preview: serves frontend/ and routes /api/* to the Lambda handler with an in-memory fake table."""
import http.server
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(__file__))
import fakes  # noqa: F401,E402
import handler  # noqa: E402

FRONT = os.path.join(os.path.dirname(__file__), "..", "frontend")
handler.api({"action": "seed"})


class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=FRONT, **k)

    def _api(self, method):
        u = urllib.parse.urlparse(self.path)
        n = int(self.headers.get("content-length") or 0)
        ev = {"requestContext": {"http": {"method": method}}, "rawPath": u.path,
              "queryStringParameters": dict(urllib.parse.parse_qsl(u.query)) or None,
              "body": self.rfile.read(n).decode() if n else None}
        r = handler.api(ev)
        body = r["body"].encode()
        self.send_response(r["statusCode"])
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/api/"):
            return self._api("GET")
        if self.path.startswith("/config.js"):
            b = b"window.HAAZIR_API = '/api';"
            self.send_response(200); self.send_header("content-type", "application/javascript")
            self.send_header("content-length", str(len(b))); self.end_headers(); self.wfile.write(b)
            return
        return super().do_GET()

    def do_POST(self):
        return self._api("POST")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    print("http://localhost:%d" % port)
    http.server.ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
