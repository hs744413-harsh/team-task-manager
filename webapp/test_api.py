"""End-to-end API smoke check against a running dev server.

Usage:
    python manage.py runserver       # in one terminal
    python test_api.py               # in another

It hits the JWT register/login endpoints, then the Project/Task/Comment/Stats
endpoints, printing status codes for each step.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
import uuid

BASE_URL = "http://127.0.0.1:8000"


def _request(method: str, path: str, *, body=None, token: str | None = None):
    url = BASE_URL + path
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = resp.read().decode("utf-8") or "{}"
            return resp.status, json.loads(payload) if payload.startswith(("{", "[")) else payload
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(body)
        except json.JSONDecodeError:
            return e.code, body


def main() -> int:
    print("Smoke testing TaskFlow API")
    print("=" * 50)

    suffix = uuid.uuid4().hex[:6]
    payload = {
        "username": f"apitest_{suffix}",
        "first_name": "API",
        "last_name": "Tester",
        "email": f"apitest_{suffix}@example.com",
        "password": "ZxcVbn!Pa55",
        "password2": "ZxcVbn!Pa55",
    }

    print("\n1. Register user")
    status, body = _request("POST", "/accounts/api/register/", body=payload)
    print(f"   {status} -> {body}")
    if status >= 400:
        print("registration failed; aborting")
        return 1

    print("\n2. Obtain JWT")
    status, body = _request("POST", "/accounts/api/token/",
                            body={"username": payload["username"],
                                  "password": payload["password"]})
    print(f"   {status} -> keys: {list(body)}")
    if status != 200:
        return 1
    access = body["access"]

    print("\n3. /api/projects/ (read)")
    status, body = _request("GET", "/api/projects/", token=access)
    print(f"   {status} -> {body.get('count', 'no count')} projects")

    print("\n4. /api/tasks/ (read)")
    status, body = _request("GET", "/api/tasks/", token=access)
    print(f"   {status} -> {body.get('count', 'no count')} tasks")

    print("\n5. /api/dashboard/stats/")
    status, body = _request("GET", "/api/dashboard/stats/", token=access)
    print(f"   {status} -> {body if isinstance(body, dict) else body[:120]}")

    print("\n6. /accounts/api/me/")
    status, body = _request("GET", "/accounts/api/me/", token=access)
    print(f"   {status} -> {body}")

    print("\n" + "=" * 50)
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
