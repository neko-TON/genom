"""CA-хранилище (Vercel Edge Config): чистые функции + сетевые обёртки.

Импортируется serverless-функциями api/ca.py и api/admin.py тем же
способом, что server.py в api/state.py. На импорте сети нет.
"""
import hmac
import json
import os
import re
import urllib.error
import urllib.request
from urllib.parse import parse_qs, urlparse

_PRINTABLE = re.compile(r"^[\x20-\x7e]*$")


def parse_edge_config(url):
    """'https://edge-config.vercel.com/<id>?token=<t>' -> (id, token) | None."""
    if not url or not isinstance(url, str):
        return None
    try:
        p = urlparse(url)
    except ValueError:
        return None
    if p.scheme != "https" or not p.netloc:
        return None
    cfg_id = p.path.strip("/")
    token = (parse_qs(p.query).get("token") or [""])[0]
    if not cfg_id or not token:
        return None
    return cfg_id, token


def validate_ca(raw):
    """Строка 0–80 печатаемых ASCII после strip; иначе None. '' легальна."""
    if not isinstance(raw, str):
        return None
    s = raw.strip()
    if len(s) > 80 or not _PRINTABLE.match(s):
        return None
    return s


def check_secret(supplied, expected):
    """Постоянное по времени сравнение; пустой expected — всегда False."""
    if not expected or not isinstance(supplied, str):
        return False
    return hmac.compare_digest(supplied.encode(), expected.encode())


def read_ca():
    """Текущий CA из Edge Config; любая проблема -> None."""
    parsed = parse_edge_config(os.environ.get("EDGE_CONFIG", ""))
    if not parsed:
        return None
    cfg_id, token = parsed
    url = "https://edge-config.vercel.com/%s/item/ca?token=%s" % (cfg_id, token)
    try:
        with urllib.request.urlopen(url, timeout=4) as r:
            value = json.loads(r.read().decode())
    except Exception:
        return None
    if isinstance(value, str) and value.strip():
        return value
    return None


def write_ca(value):
    """Upsert item 'ca' через Vercel API. -> (ok, err_text)."""
    parsed = parse_edge_config(os.environ.get("EDGE_CONFIG", ""))
    api_token = os.environ.get("VERCEL_API_TOKEN", "")
    if not parsed or not api_token:
        return False, "storage is not configured"
    cfg_id, _ = parsed
    url = "https://api.vercel.com/v1/edge-config/%s/items" % cfg_id
    team = os.environ.get("VERCEL_TEAM_ID", "")
    if team:
        url += "?teamId=" + team
    body = json.dumps({"items": [
        {"operation": "upsert", "key": "ca", "value": value}]}).encode()
    req = urllib.request.Request(
        url, data=body, method="PATCH",
        headers={"Authorization": "Bearer " + api_token,
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            r.read()
        return True, ""
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode()[:200]
        except Exception:
            pass
        return False, "vercel api: %d %s" % (e.code, detail)
    except Exception as exc:
        return False, "vercel api: %r" % (exc,)
