#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filename: src/seevar_next/flight/status.py
Version: 0.1.0
Objective: Human flight status rendering.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_flight_snapshot(current: dict[str, Any] | None, error: str | None = None) -> dict[str, Any]:
    """Build a compact flight snapshot."""
    if error:
        return {"running": False, "state": "error", "error": error, "targets": [], "scopes": []}
    if not current:
        return {"running": False, "state": "idle", "targets": [], "scopes": []}
    plan = current.get("plan") or {}
    targets = []
    for item in plan.get("list", []):
        targets.append(
            {
                "name": item.get("target_name") or item.get("name") or "-",
                "state": item.get("state", "pending"),
                "skip": bool(item.get("skip", False)),
                "start_min": item.get("start_min"),
                "duration_min": item.get("duration_min"),
            }
        )
    return {
        "running": True,
        "state": current.get("state", "running"),
        "plan_name": plan.get("plan_name"),
        "targets": targets,
        "scopes": [],
    }


def build_submitted_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    """Build a snapshot immediately after submit."""
    return {
        "running": True,
        "state": "submitted",
        "plan_name": payload.get("plan_name"),
        "scopes": [],
        "targets": [
            {
                "name": item.get("target_name") or "-",
                "state": "submitted",
                "skip": bool(item.get("skip", False)),
                "start_min": item.get("start_min"),
                "duration_min": item.get("duration_min"),
            }
            for item in payload.get("list", [])
        ],
    }


def with_scope_status(snapshot: dict[str, Any], scopes: list[dict[str, Any]]) -> dict[str, Any]:
    """Attach scope status to a flight snapshot."""
    clone = dict(snapshot)
    clone["scopes"] = scopes
    return clone


def render_flight_status(snapshot: dict[str, Any]) -> str:
    """Render flight status for humans."""
    state = str(snapshot.get("state", "unknown")).upper()
    lines = [f"SeeVar Next flight: {state}"]
    if snapshot.get("plan_name"):
        lines.append(f"Plan: {snapshot['plan_name']}")
    if snapshot.get("error"):
        lines.append(f"Error: {snapshot['error']}")
    scopes = snapshot.get("scopes") or []
    if scopes:
        lines.append("Scopes:")
        for scope in scopes:
            state = "online" if scope.get("ok") else "offline"
            detail = scope.get("summary") or "; ".join(scope.get("errors", [])) or "-"
            lines.append(f"- {scope.get('name', scope.get('host'))} {scope.get('host')}: {state} - {detail}")
    targets = snapshot.get("targets") or []
    if targets:
        lines.append("Targets:")
        for idx, target in enumerate(targets, start=1):
            skip = " skip" if target.get("skip") else ""
            duration = target.get("duration_min")
            duration_text = f", {duration} min" if duration is not None else ""
            lines.append(f"- {idx}. {target['name']}: {target.get('state', 'pending')}{skip}{duration_text}")
    else:
        lines.append("Targets: none")
    return "\n".join(lines) + "\n"


def write_flight_status(snapshot: dict[str, Any], json_path: Path, text_path: Path) -> None:
    """Write JSON and text flight status files."""
    json_path.parent.mkdir(parents=True, exist_ok=True)
    text_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    text_path.write_text(render_flight_status(snapshot), encoding="utf-8")
