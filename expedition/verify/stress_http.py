"""Reproducible HTTP boundary and replay-load gate for Site Expedition.

Run this while the protected local server is listening on loopback::

    python3 -m expedition.verify.stress_http

The deployment token is read from ``expedition/var/access-token`` and is never
printed.  The gate spends no Mireye credits: every Expedition uses replay.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import http.client
import json
from pathlib import Path
import socket
import statistics
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TOKEN_FILE = ROOT / "var" / "access-token"
DEFAULT_OUTPUT_FILE = ROOT / "var" / "stress-http.json"


def _nearest_rank(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    index = max(
        0,
        min(len(values) - 1, int(len(values) * fraction + 0.999999) - 1),
    )
    return values[index]


def _slow_header_gate(
    host: str,
    port: int,
    count: int,
    timeout: float,
) -> tuple[int, float]:
    clients: list[socket.socket] = []
    started = time.perf_counter()
    try:
        for _ in range(count):
            client = socket.create_connection((host, port), timeout=2)
            client.settimeout(timeout + 2)
            client.sendall(b"GET /api/credits HTTP/1.1\r\nHost: local")
            clients.append(client)
        closed = 0
        for client in clients:
            try:
                if client.recv(1) == b"":
                    closed += 1
            except ConnectionResetError:
                closed += 1
            except socket.timeout:
                pass
        return closed, time.perf_counter() - started
    finally:
        for client in clients:
            client.close()


def _request(
    host: str,
    port: int,
    method: str,
    path: str,
    token: str,
    *,
    body: str | None = None,
    timeout: float = 30,
) -> tuple[int, float, str | None]:
    headers = {"Authorization": "Bearer " + token}
    if body is not None:
        headers["Content-Type"] = "application/json"
    started = time.perf_counter()
    connection = http.client.HTTPConnection(host, port, timeout=timeout)
    try:
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        response.read()
        return response.status, (time.perf_counter() - started) * 1000, None
    except Exception as exc:  # Network failures are part of this gate's report.
        return 0, (time.perf_counter() - started) * 1000, type(exc).__name__
    finally:
        connection.close()


def run(args: argparse.Namespace) -> dict[str, Any]:
    token = args.token_file.read_text().strip()
    if not token:
        raise RuntimeError("deployment token file is empty")

    closed, slow_elapsed = _slow_header_gate(
        args.host,
        args.port,
        args.slow_clients,
        args.socket_timeout,
    )
    recovery_status, recovery_ms, recovery_error = _request(
        args.host,
        args.port,
        "GET",
        "/api/credits",
        token,
        timeout=10,
    )

    body = json.dumps(
        {"mission": "warehouse", "live": False, "controls": {}},
        separators=(",", ":"),
    )

    def request_once(_index: int) -> tuple[int, float, str | None]:
        return _request(
            args.host,
            args.port,
            "POST",
            "/api/expedition",
            token,
            body=body,
        )

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(request_once, range(args.requests)))

    latencies = sorted(ms for status, ms, _error in results if status == 200)
    errors: dict[str, int] = {}
    for status, _latency, error in results:
        if status == 200:
            continue
        key = str(status) if status else error or "unknown"
        errors[key] = errors.get(key, 0) + 1

    ok = (
        closed == args.slow_clients
        and recovery_status == 200
        and recovery_error is None
        and len(latencies) == args.requests
    )
    p95 = _nearest_rank(latencies, 0.95)
    return {
        "ok": ok,
        "slow_headers": {
            "closed": closed,
            "total": args.slow_clients,
            "release_s": round(slow_elapsed, 2),
        },
        "recovery": {
            "status": recovery_status,
            "ms": round(recovery_ms, 1),
            "error": recovery_error,
        },
        "load": {
            "requests": args.requests,
            "max_in_flight": args.workers,
            "http_200": len(latencies),
            "errors": errors,
            "p50_ms": round(statistics.median(latencies), 1) if latencies else None,
            "p95_ms": round(p95, 1) if p95 is not None else None,
            "max_ms": round(max(latencies), 1) if latencies else None,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8030)
    parser.add_argument("--token-file", type=Path, default=DEFAULT_TOKEN_FILE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_FILE)
    parser.add_argument("--slow-clients", type=int, default=16)
    parser.add_argument("--socket-timeout", type=float, default=5.0)
    parser.add_argument("--requests", type=int, default=80)
    parser.add_argument("--workers", type=int, default=16)
    args = parser.parse_args()
    if min(args.slow_clients, args.requests, args.workers) <= 0:
        parser.error("slow-clients, requests, and workers must be positive")
    return args


def main() -> None:
    args = parse_args()
    report = run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
