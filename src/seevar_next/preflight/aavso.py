"""AAVSO Target Tool fetcher."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import httpx

from seevar_next.preflight.catalogs import coerce_float

TARGET_TOOL_URL = "https://targettool.aavso.org/TargetTool/api/v1/targets"


def _extract_targets(payload: Any) -> list[dict[str, Any]]:
    """Extract target rows from AAVSO responses."""
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("targets", "data", "results"):
            if isinstance(payload.get(key), list):
                return [item for item in payload[key] if isinstance(item, dict)]
    raise ValueError("unexpected AAVSO Target Tool payload")


def fetch_targets(api_key: str, section: str = "ac", limit: int = 0) -> list[dict[str, Any]]:
    """Fetch raw AAVSO Target Tool targets."""
    response = httpx.get(
        TARGET_TOOL_URL,
        auth=(api_key, "api_token"),
        params={"obs_section": section},
        timeout=30.0,
    )
    response.raise_for_status()
    targets = _extract_targets(response.json())
    return targets[:limit] if limit else targets


def normalize_targets(rows: list[dict[str, Any]], mag_limit: float = 15.0, min_dec: float = -8.0) -> list[dict[str, Any]]:
    """Normalize AAVSO rows into SeeVar campaign target shape."""
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        name = row.get("star_name") or row.get("name") or row.get("primaryName")
        coords_value = row.get("coordinates")
        coords: dict[str, Any] = coords_value if isinstance(coords_value, dict) else {}
        ra = coerce_float(row.get("ra") or row.get("raDeg") or coords.get("ra") or coords.get("raDeg"))
        dec = coerce_float(row.get("dec") or row.get("decDeg") or coords.get("dec") or coords.get("decDeg"))
        mag = coerce_float(row.get("max_mag") or row.get("maxMag") or row.get("magnitude") or row.get("mag"))
        if not name or ra is None or dec is None or mag is None or mag > mag_limit or dec < min_dec:
            continue
        out[str(name)] = {
            "name": str(name),
            "ra": ra,
            "dec": dec,
            "type": row.get("var_type") or row.get("targetType"),
            "max_mag": mag,
            "min_mag": coerce_float(row.get("min_mag") or row.get("minMag")),
            "recommended_cadence_days": coerce_float(row.get("recommended_cadence_days") or row.get("cadence")) or 3.0,
            "priority": 1 if row.get("priority") is True else 2,
            "duration": 600,
            "source": "AAVSO Target Tool",
            "target_class": "AAVSO_CAMPAIGN",
        }
    return list(out.values())


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Fetch AAVSO campaign targets.")
    parser.add_argument("--api-key", default=os.environ.get("AAVSO_TARGET_TOOL_API_KEY"))
    parser.add_argument("--section", default="ac")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--output", type=Path, default=Path("catalogs/campaign_targets.json"))
    parser.add_argument("--raw-output", type=Path, default=Path("catalogs/aavso_targettool_raw.json"))
    args = parser.parse_args()
    if not args.api_key:
        raise SystemExit("missing AAVSO_TARGET_TOOL_API_KEY")
    raw = fetch_targets(args.api_key, args.section, args.limit)
    normalized = normalize_targets(raw)
    args.raw_output.parent.mkdir(parents=True, exist_ok=True)
    args.raw_output.write_text(json.dumps({"targets": raw}, indent=2), encoding="utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"metadata": {"source": "AAVSO Target Tool"}, "targets": normalized}, indent=2), encoding="utf-8")
    print(json.dumps({"raw": len(raw), "normalized": len(normalized), "output": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
