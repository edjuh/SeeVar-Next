#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filename: src/seevar_next/flight/seestar_rpc.py
Version: 0.1.0
Objective: Small direct Seestar JSON-RPC probes.
"""
from __future__ import annotations

import json
import socket
from typing import Any


def send_rpc(host: str, method: str, params: dict[str, Any] | None = None, *, port: int = 4700, timeout_sec: float = 2.0) -> dict[str, Any] | str:
    """Send one short JSON-RPC command to a Seestar."""
    cmd = {"id": 1, "verify": True, "method": method}
    if params is not None:
        cmd["params"] = params
    with socket.create_connection((host, port), timeout=timeout_sec) as sock:
        sock.settimeout(timeout_sec)
        sock.sendall((json.dumps(cmd) + "\r\n").encode())
        buf = ""
        last_line = ""
        while True:
            while "\r\n" not in buf:
                chunk = sock.recv(4096)
                if not chunk:
                    return json.loads(last_line) if last_line else {}
                buf += chunk.decode("utf-8", errors="replace")
            line, buf = buf.split("\r\n", 1)
            if not line:
                continue
            last_line = line
            try:
                frame = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(frame, dict) and frame.get("id") == 1:
                return frame


def probe_status(host: str, *, timeout_sec: float = 2.0) -> dict[str, Any]:
    """Probe basic scope status without seestarpy discovery."""
    result: dict[str, Any] = {"host": host, "ok": False}
    checks = {
        "connection": ("test_connection", None),
        "device": ("get_device_state", None),
        "view": ("get_view_state", None),
        "track": ("scope_get_track_state", None),
    }
    errors = []
    for key, (method, params) in checks.items():
        try:
            result[key] = send_rpc(host, method, params, timeout_sec=timeout_sec)
        except Exception as exc:
            errors.append(f"{method}: {exc.__class__.__name__}: {exc}")
    result["ok"] = bool(result.get("connection")) and not errors
    result["errors"] = errors
    return result
