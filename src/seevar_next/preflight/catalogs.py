"""Catalog loading and normalization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from seevar_next.models import TargetPlan


def load_json(path: Path) -> Any:
    """Load JSON from disk."""
    return json.loads(path.read_text(encoding="utf-8"))


def catalog_items(payload: Any) -> list[dict[str, Any]]:
    """Extract target rows from known SeeVar catalog shapes."""
    if isinstance(payload, list):
        return [dict(item) for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        rows = payload.get("targets", payload.get("data", []))
        if isinstance(rows, list):
            return [dict(item) for item in rows if isinstance(item, dict)]
    raise ValueError("catalog does not contain a target list")


def coerce_float(value: Any) -> float | None:
    """Return a float or None."""
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_target(row: dict[str, Any], source: str) -> TargetPlan | None:
    """Convert one SeeVar catalog row to a TargetPlan."""
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
    """Load and normalize multiple catalog files."""
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
    """Load selected catalogs from a directory."""
    if names:
        paths = [catalog_dir / f"{name}.json" for name in names]
    else:
        paths = sorted(catalog_dir.glob("*.json"))
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError("missing catalog(s): " + ", ".join(missing))
    return load_catalog_paths(paths)
