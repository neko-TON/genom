"""Vercel serverless: смена CA из админки (секрет + запись в Edge Config)."""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ca_lib import check_secret, validate_ca, write_ca  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def _json(self, obj, code):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
            data = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(data, dict):
                raise ValueError
        except (ValueError, json.JSONDecodeError):
            return self._json({"ok": False, "error": "bad json"}, 400)
        if not check_secret(data.get("secret"),
                            os.environ.get("ADMIN_SECRET", "")):
            return self._json({"ok": False, "error": "unauthorized"}, 401)
        ca = validate_ca(data.get("ca"))
        if ca is None:
            return self._json({"ok": False, "error": "bad ca"}, 400)
        ok, err = write_ca(ca)
        if not ok:
            return self._json({"ok": False, "error": err}, 502)
        return self._json({"ok": True, "ca": ca}, 200)
