#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filename: src/seevar_next/preflight/catalogs.py
Version: 0.1.0
Objective: Load mixed SeeVar-style catalog JSON safely and normalize it into strict `TargetPlan` rows for preflight.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from seevar_next.models import TargetPlan


def load_json(path: Path) -> Any:
    """Load one JSON file from disk.

    Why: catalog handling starts from user or fetched JSON files, so preflight
    needs one small trusted read step before any normalization happens.
    """
    return json.loads(path.read_text(encoding="utf-8"))


def catalog_items(payload: Any) -> list[dict[str, Any]]:
    """Extract raw target rows from supported catalog shapes.

    Why: older SeeVar data is not fully uniform, so preflight needs one place
    that accepts the known `list`, `targets`, or `data` layouts.
    """
    if isinstance(payload, list):
        return [dict(item) for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        rows = payload.get("targets", payload.get("data", []))
        if isinstance(rows, list):
            return [dict(item) for item in rows if isinstance(item, dict)]
    raise ValueError("catalog does not contain a target list")


def coerce_float(value: Any) -> float | None:
    """Convert loose numeric input to `float` or `None`.

    Why: catalog fields often arrive as strings, empty values, or mixed types,
    and normalization should reject bad numbers without crashing the run.
    """
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_target(row: dict[str, Any], source: str) -> TargetPlan | None:
    """Normalize one raw catalog row into a strict `TargetPlan`.

    Why: the rest of preflight should only deal with one internal target shape,
    not many external catalog formats and field-name variants.
    """
    name = str(row.get("name") or row.get("target_name") or "").strip()
    ra = coerce_float(row.get("ra_deg", row.get("ra")))
    dec = coerce_float(row.get("dec_deg", row.get("dec")))
    if not name or ra is None or dec is None:
        return None
    cadence = coerce_float(row.get("recommended_cadence_days", row.get("cadence_days")))
    return TargetPlan(
        name=name,
        ra_deg=ra,
        dec_deg=dec,
        priority=int(row.get("priority", 100) or 100),
        target_type=row.get("type"),
        max_mag=coerce_float(row.get("max_mag", row.get("mag_max"))),
        min_mag=coerce_float(row.get("min_mag", row.get("mag_min"))),
        cadence_days=cadence,
        duration_sec=int(row.get("duration", row.get("duration_sec", 600)) or 600),
        source=source,
        notes={
            "catalog": row.get("catalog"),
            "target_class": row.get("target_class"),
            "science_mode": row.get("science_mode", "variable"),
        },
    )


def load_catalog_paths(paths: list[Path]) -> list[TargetPlan]:
    """Load several catalog files and merge them into one target list.

    Why: nightly planning can draw from multiple local sources, and this step
    keeps the best row per target name by priority before planning starts.
    """
    targets: dict[str, TargetPlan] = {}
    for path in paths:
        source = path.stem
        for row in catalog_items(load_json(path)):
            target = normalize_target(row, source)
            if target is None:
                continue
            current = targets.get(target.name)
            if current is None or target.priority < current.priority:
                targets[target.name] = target
    return list(targets.values())


def load_catalog_dir(catalog_dir: Path, names: list[str] | None = None) -> list[TargetPlan]:
    """Load named or all catalogs from one directory.

    Why: operators need a simple entry point for preflight that can either load
    a chosen subset or sweep the whole catalog directory in one call.
    """
    if names:
        paths = [catalog_dir / f"{name}.json" for name in names]
    else:
        paths = sorted(catalog_dir.glob("*.json"))
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError("missing catalog(s): " + ", ".join(missing))
    return load_catalog_paths(paths)
