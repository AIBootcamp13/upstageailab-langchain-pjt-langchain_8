#!/usr/bin/env python3
"""
Best-effort smoke-test for the Chainlit UI endpoints used by the inline-edit flow.

What it does (best-effort):
- Ping the app base URL (default: http://localhost:8000)
- POST a quick chat to /api/chat to try to create a draft/update action
- If any message id is returned in the response JSON, attempt to call /_action open_inline_editor
- Call /_action start_manual_edit and then POST an "edited" message to /api/chat to exercise manual-edit consumption

The script is intentionally tolerant: Chainlit versions and deployments expose slightly different
endpoints and payload shapes, so the script reports what worked and what didn't rather than failing.

Usage:
  python3 scripts/smoke_chainlit_ui.py --base http://localhost:8000

"""

import argparse
import json
import os
import sys
import time

try:
    import requests
except Exception:
    requests = None
    import urllib.request
    import urllib.parse


DEFAULT_BASE = os.environ.get("CHAINLIT_BASE_URL", "http://localhost:8000")


def http_post(url, payload, headers=None, timeout=8):
    headers = headers or {"Content-Type": "application/json"}
    body = json.dumps(payload).encode("utf-8")
    if requests:
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=timeout)
            return r.status_code, r.text, _try_json(r)
        except Exception as e:
            return None, str(e), None
    else:
        req = urllib.request.Request(url, data=body, headers=headers or {})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                txt = resp.read().decode("utf-8")
                code = resp.getcode()
                try:
                    js = json.loads(txt)
                except Exception:
                    js = None
                return code, txt, js
        except Exception as e:
            return None, str(e), None


def _try_json(resp):
    try:
        return resp.json()
    except Exception:
        return None


def ping(base):
    url = base.rstrip("/") + "/"
    try:
        if requests:
            r = requests.get(url, timeout=4)
            return r.status_code in (200, 401, 403)
        else:
            with urllib.request.urlopen(url, timeout=4) as resp:
                return resp.getcode() == 200
    except Exception:
        return False


def try_chat(base, message_text="Hello smoke test"):
    url = base.rstrip("/") + "/api/chat"
    payloads = [
        {"message": message_text},
        {"content": message_text},
        {"input": message_text},
    ]
    for p in payloads:
        code, txt, js = http_post(url, p)
        print(f"POST {url} -> {code}")
        if code and 200 <= code < 300:
            return code, txt, js
    return None, None, None


def try_action(base, name, payload=None):
    url = base.rstrip("/") + "/_action"
    body = {"name": name, "payload": payload or {}}
    code, txt, js = http_post(url, body)
    print(f"POST {url} (action={name}) -> {code}")
    return code, txt, js


def find_message_id(js):
    if not js:
        return None
    # Common places to look for ids
    for key in ["id", "message_id", "parent_id", "data", "result"]:
        if key in js:
            val = js[key]
            if isinstance(val, str):
                return val
            if isinstance(val, dict):
                # dive one level
                for kk in ["id", "message_id"]:
                    if kk in val and isinstance(val[kk], str):
                        return val[kk]
    # Also search recursively for any string-looking id
    def recurse(o):
        if isinstance(o, dict):
            for v in o.values():
                r = recurse(v)
                if r:
                    return r
        elif isinstance(o, list):
            for v in o:
                r = recurse(v)
                if r:
                    return r
        elif isinstance(o, str):
            if len(o) >= 6 and ("-" in o or o.isalnum()):
                return o
        return None

    return recurse(js)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=DEFAULT_BASE, help="Base URL for Chainlit app")
    ap.add_argument("--wait", type=int, default=1, help="seconds to wait between steps")
    args = ap.parse_args()

    base = args.base
    print("Chainlit smoke-test using base:", base)

    ok = ping(base)
    print("Ping base ->", ok)
    if not ok:
        print("Base URL not reachable. Make sure Chainlit is running at the provided URL.")

    print("--- Trying chat POST (create/trigger draft) ---")
    code, txt, js = try_chat(base, "Please create an initial draft for testing.")
    if not code:
        print("Couldn't POST to /api/chat; skipping action steps.")
        return 2

    mid = find_message_id(js) or None
    print("Discovered message id:", mid)

    time.sleep(args.wait)

    if mid:
        print("--- Trying open_inline_editor action ---")
        try_action(base, "open_inline_editor", {"message_id": mid})
    else:
        print("No message id found; attempt open_inline_editor with no id")
        try_action(base, "open_inline_editor", {})

    time.sleep(args.wait)

    print("--- Trying start_manual_edit action ---")
    try_action(base, "start_manual_edit", {})

    time.sleep(args.wait)

    print("--- Posting edited draft as chat message (manual edit flow) ---")
    edited = "[SMOKE EDIT] This is an edited draft used by the smoke test. Remove if you see it."
    code2, txt2, js2 = try_chat(base, edited)
    print("Edited post result:", code2)

    print("--- Done. Review the server logs (/tmp/chainlit_run.log) for detailed behaviour. ---")
    return 0


if __name__ == "__main__":
    sys.exit(main())
