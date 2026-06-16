#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filename: src/seevar_next/preflight/planner.py
Version: 0.1.0
Objective: Proof-driven preflight planner.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

import astropy.units as u
from astropy.coordinates import AltAz, EarthLocation, SkyCoord, get_sun
from astropy.time import Time

from seevar_next.models import NightlyPlan, ProofStep, StepStatus, TargetPlan
from seevar_next.preflight.catalogs import load_catalog_dir
from seevar_next.proof.ledger import ProofLedger


def build_plan(targets: list[TargetPlan], limit: int | None = None) -> list[TargetPlan]:
    """Return a priority-sorted observing plan."""
    planned = sorted(targets, key=lambda item: (item.priority, item.name))
    return planned[:limit] if limit else planned


def _utc(value: str | None) -> datetime:
    """Parse an ISO time or return now."""
    if not value:
        return datetime.now(timezone.utc)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _time_grid(start_utc: datetime, hours: float, step_minutes: int) -> list[datetime]:
    """Build UTC sample times."""
    count = max(1, int(hours * 60 / step_minutes) + 1)
    return [start_utc + timedelta(minutes=step_minutes * idx) for idx in range(count)]


def _dark_mask(times: Iterable[datetime], location: EarthLocation, sun_alt_limit_deg: float) -> list[bool]:
    """Return true where the Sun is below the configured limit."""
    t = Time(list(times))
    sun_alt = get_sun(t).transform_to(AltAz(obstime=t, location=location)).alt.deg
    return [float(alt) <= sun_alt_limit_deg for alt in sun_alt]


def _target_window(
    target: TargetPlan,
    times: list[datetime],
    dark: list[bool],
    location: EarthLocation,
    min_alt_deg: float,
) -> TargetPlan | None:
    """Return target with best window metadata or None."""
    coord = SkyCoord(ra=target.ra_deg * u.deg, dec=target.dec_deg * u.deg, frame="icrs")
    altaz = coord.transform_to(AltAz(obstime=Time(times), location=location))
    usable = [(idx, float(alt)) for idx, alt in enumerate(altaz.alt.deg) if dark[idx] and float(alt) >= min_alt_deg]
    if not usable:
        return None
    best_idx, best_alt = max(usable, key=lambda item: item[1])
    first_idx = usable[0][0]
    last_idx = usable[-1][0]
    clone = target.model_copy()
    clone.best_start_utc = times[first_idx]
    clone.best_end_utc = times[last_idx]
    clone.max_alt_deg = best_alt
    clone.notes = dict(clone.notes)
    clone.notes["best_sample_utc"] = times[best_idx].isoformat()
    return clone


def build_nightly_plan(
    targets: list[TargetPlan],
    *,
    latitude_deg: float,
    longitude_deg: float,
    start_utc: datetime,
    hours: float = 12.0,
    step_minutes: int = 10,
    sun_alt_limit_deg: float = -18.0,
    min_alt_deg: float = 25.0,
    limit: int | None = None,
    run_id: str = "manual",
) -> NightlyPlan:
    """Build one observable target list."""
    location = EarthLocation(lat=latitude_deg * u.deg, lon=longitude_deg * u.deg)
    times = _time_grid(start_utc, hours, step_minutes)
    dark = _dark_mask(times, location, sun_alt_limit_deg)
    warnings = []
    if not any(dark):
        warnings.append("no astronomical-dark samples in planning window")
    visible = [
        planned
        for target in targets
        if (planned := _target_window(target, times, dark, location, min_alt_deg)) is not None
    ]
    return NightlyPlan(
        run_id=run_id,
        site_latitude_deg=latitude_deg,
        site_longitude_deg=longitude_deg,
        targets=build_plan(visible, limit),
        warnings=warnings,
    )


def write_plan(plan: NightlyPlan, output_path: Path) -> None:
    """Write the nightly plan JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(plan.model_dump_json(indent=2), encoding="utf-8")


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Build a SeeVar Next nightly plan.")
    parser.add_argument("--catalog-dir", type=Path, default=Path("catalogs"))
    parser.add_argument("--catalog", action="append", help="Catalog name without .json; may be repeated.")
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("--start-utc")
    parser.add_argument("--hours", type=float, default=12.0)
    parser.add_argument("--sun-alt", type=float, default=-18.0)
    parser.add_argument("--min-alt", type=float, default=25.0)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--run-id", default="manual")
    parser.add_argument("--output", type=Path, default=Path("data/tonights_plan.json"))
    parser.add_argument("--proof", type=Path, default=Path("data/flight_runs/preflight.jsonl"))
    args = parser.parse_args()

    ledger = ProofLedger(args.proof)
    targets = load_catalog_dir(args.catalog_dir, args.catalog)
    ledger.append(ProofStep(run_id=args.run_id, target="*", phase="preflight", step="catalog", status=StepStatus.PASS, meta={"targets": len(targets)}))
    plan = build_nightly_plan(
        targets,
        latitude_deg=args.lat,
        longitude_deg=args.lon,
        start_utc=_utc(args.start_utc),
        hours=args.hours,
        sun_alt_limit_deg=args.sun_alt,
        min_alt_deg=args.min_alt,
        limit=args.limit,
        run_id=args.run_id,
    )
    write_plan(plan, args.output)
    status = StepStatus.PASS if plan.targets else StepStatus.FAIL
    ledger.append(ProofStep(run_id=args.run_id, target="*", phase="preflight", step="plan", status=status, evidence_path=str(args.output), meta={"planned": len(plan.targets), "warnings": plan.warnings}))
    for order, target in enumerate(plan.targets, start=1):
        ledger.append(
            ProofStep(
                run_id=args.run_id,
                target=target.name,
                phase="preflight",
                step="observable",
                status=StepStatus.PASS,
                evidence_path=str(args.output),
                meta={
                    "order": order,
                    "best_start_utc": target.best_start_utc.isoformat() if target.best_start_utc else None,
                    "best_end_utc": target.best_end_utc.isoformat() if target.best_end_utc else None,
                    "max_alt_deg": target.max_alt_deg,
                },
            )
        )
    print(json.dumps({"planned": len(plan.targets), "output": str(args.output), "warnings": plan.warnings}, indent=2))
    return 0 if plan.targets else 2


if __name__ == "__main__":
    raise SystemExit(main())
