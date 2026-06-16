#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filename: src/seevar_next/preflight/seestarpy_plan.py
Version: 0.1.0
Objective: Export SeeVar plans to seestarpy named-plan JSON.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


def _load_json(path: Path) -> Any:
    """Load JSON from disk."""
    return json.loads(path.read_text(encoding="utf-8"))


def _target_id(name: str, ra_hours: float, dec_deg: float) -> int:
    """Build a stable seestarpy target id."""
    raw = f"{name}|{ra_hours:.7f}|{dec_deg:.7f}".encode("utf-8")
    return 100_000_000 + (int(hashlib.sha1(raw).hexdigest()[:8], 16) % 900_000_000)


def _parse_iso(value: str | None) -> datetime | None:
    """Parse an ISO timestamp."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _clock_min(value: str) -> int:
    """Parse HH:MM to minutes."""
    hour, minute = value.split(":", 1)
    return int(hour) * 60 + int(minute)


def _targets(payload: Any) -> list[dict[str, Any]]:
    """Extract plan targets."""
    if isinstance(payload, dict):
        rows = payload.get("targets", payload.get("data", []))
    else:
        rows = payload
    if not isinstance(rows, list):
        raise ValueError("input does not contain targets")
    return [dict(row) for row in rows]


def build_seestarpy_plan(
    input_path: Path,
    timezone_name: str,
    plan_name: str,
    plan_date: str | None = None,
    default_start: str = "21:00",
) -> dict[str, Any]:
    """Convert a SeeVar plan to seestarpy named-plan format."""
    rows = _targets(_load_json(input_path))
    tz = ZoneInfo(timezone_name)
    local_date = date.fromisoformat(plan_date) if plan_date else datetime.now(tz).date()
    fallback_start = _clock_min(default_start)
    output_targets = []
    for row in rows:
        name = str(row.get("name", "SeeVar Target"))
        if row.get("ra_hours") is not None:
            ra_hours = float(row["ra_hours"]) % 24.0
        else:
            ra_hours = float(row["ra_deg"]) / 15.0 % 24.0
        dec_deg = float(row["dec_deg"])
        duration = max(1, math.ceil(float(row.get("duration_sec", 600)) / 60.0))
        start_dt = _parse_iso(row.get("best_start_utc"))
        if start_dt:
            local = start_dt.astimezone(tz)
            start_min = (local.date() - local_date).days * 1440 + local.hour * 60 + local.minute
        else:
            start_min = fallback_start
        fallback_start = start_min + duration
        output_targets.append(
            {
                "target_id": _target_id(name, ra_hours, dec_deg),
                "target_name": name,
                "alias_name": name,
                "target_ra_dec": [round(ra_hours, 6), round(dec_deg, 6)],
                "lp_filter": False,
                "start_min": start_min,
                "duration_min": duration,
            }
        )
    return {"plan_name": plan_name, "update_time_seestar": local_date.strftime("%Y.%m.%d"), "list": output_targets}


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Export a SeeVar plan to seestarpy.")
    parser.add_argument("--input", type=Path, default=Path("data/tonights_plan.json"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timezone", default="Europe/Amsterdam")
    parser.add_argument("--name", default="SeeVar")
    parser.add_argument("--plan-date")
    parser.add_argument("--default-start", default="21:00")
    args = parser.parse_args()
    payload = build_seestarpy_plan(args.input, args.timezone, args.name, args.plan_date, args.default_start)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"targets": len(payload["list"]), "output": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
