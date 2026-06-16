#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filename: src/seevar_next/preflight/vsx.py
Version: 0.1.0
Objective: Small AAVSO VSX cache helper.
"""
from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from seevar_next.preflight.catalogs import load_catalog_paths


def _clean_float(value: Any) -> float | None:
    """Parse numeric VSX fields."""
    if value in (None, ""):
        return None
    text = re.sub(r"[^0-9.+-]", "", str(value))
    try:
        return float(text)
    except ValueError:
        return None


def query_vsx(name: str) -> dict[str, Any]:
    """Query one VSX object."""
    response = httpx.get(
        "https://aavso.org/vsx/index.php",
        params={"view": "api.object", "ident": name, "format": "json"},
        timeout=20.0,
    )
    response.raise_for_status()
    obj = response.json().get("VSXObject") or {}
    return {
        "name": name,
        "status": "ok" if obj else "no_match",
        "type": obj.get("VariabilityType") or obj.get("Type"),
        "max_mag": _clean_float(obj.get("MaxMag")),
        "min_mag": _clean_float(obj.get("MinMag")),
        "period_days": _clean_float(obj.get("Period")),
        "checked_utc": datetime.now(timezone.utc).isoformat(),
    }


def build_cache(catalog_paths: list[Path], output_path: Path, limit: int = 0, delay_sec: float = 1.0) -> dict[str, Any]:
    """Build or refresh a VSX cache from catalogs."""
    targets = load_catalog_paths(catalog_paths)
    if limit:
        targets = targets[:limit]
    stars = {}
    for idx, target in enumerate(targets):
        stars[target.name] = query_vsx(target.name)
        if idx + 1 < len(targets):
            time.sleep(delay_sec)
    payload = {"stars": stars}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Build an AAVSO VSX cache.")
    parser.add_argument("catalog", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, default=Path("data/vsx_catalog.json"))
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--delay-sec", type=float, default=1.0)
    args = parser.parse_args()
    payload = build_cache(args.catalog, args.output, args.limit, args.delay_sec)
    print(json.dumps({"stars": len(payload["stars"]), "output": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
