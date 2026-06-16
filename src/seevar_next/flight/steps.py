#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filename: src/seevar_next/flight/steps.py
Version: 0.1.0
Objective: Proofed flight-step dry run.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from seevar_next.flight.dryrun import load_plan
from seevar_next.models import ProofStep, StepStatus
from seevar_next.proof.ledger import ProofLedger


@dataclass(frozen=True)
class StepSpec:
    """One expected flight step."""

    code: str
    phase: str
    step: str
    label: str
    target_scoped: bool = True


PREFLIGHT_STEPS = [
    StepSpec("P1", "preflight", "config_catalog", "config and target catalogs loaded", target_scoped=False),
    StepSpec("P2", "preflight", "weather_readiness", "weather and safety readiness", target_scoped=False),
    StepSpec("P3", "preflight", "cadence", "ledger cadence and due-target filter", target_scoped=False),
    StepSpec("P4", "preflight", "dark_window", "dark window, horizon, moon, and altitude gates", target_scoped=False),
    StepSpec("P5", "preflight", "scope_inventory", "enabled telescope inventory and connection probe", target_scoped=False),
    StepSpec("P6", "preflight", "three_point_alignment", "3-point star alignment / pointing model", target_scoped=False),
    StepSpec("P7", "preflight", "plan_export", "science and optional pretty plans exported", target_scoped=False),
    StepSpec("P8", "preflight", "run_gate", "final GO / NO-GO operator gate", target_scoped=False),
]

TARGET_STEPS = [
    StepSpec("A1", "flight", "target_lock", "target locked"),
    StepSpec("A2", "flight", "safety_gate", "zero-state and safety gate"),
    StepSpec("A3", "flight", "session_init", "session telemetry valid"),
    StepSpec("A4", "flight", "slew", "slew command"),
    StepSpec("A5", "flight", "slew_complete", "slew completion proof"),
    StepSpec("A6", "flight", "settle", "settle after slew"),
    StepSpec("A7", "flight", "solve", "fresh pointing solve"),
    StepSpec("A8", "flight", "corrective_retry", "nudge/retry if solve is off"),
    StepSpec("A9", "flight", "exposure_plan", "exposure plan"),
    StepSpec("A10", "flight", "expose_download", "expose and download frame"),
    StepSpec("A11", "flight", "frame_accept", "frame QC and FITS accept"),
    StepSpec("A12", "flight", "commit", "commit success/failure"),
]

POSTFLIGHT_STEPS = [
    StepSpec("F1", "postflight", "darks", "dark closure", target_scoped=False),
    StepSpec("F2", "postflight", "stack", "one accepted stack per target", target_scoped=False),
    StepSpec("F3", "postflight", "solve_stack", "stack WCS solve", target_scoped=False),
    StepSpec("F4", "postflight", "photometry", "photometry", target_scoped=False),
    StepSpec("F5", "postflight", "report", "AAVSO report staging", target_scoped=False),
    StepSpec("F6", "postflight", "retry_plan", "retry failed science targets", target_scoped=False),
    StepSpec("F7", "postflight", "pretty_plan", "pretty targets if science time remains", target_scoped=False),
    StepSpec("F8", "postflight", "park", "park or shutdown policy", target_scoped=False),
]


def _status_for(spec: StepSpec, fail_code: str | None) -> StepStatus:
    """Return step status for a simulated failure code."""
    return StepStatus.FAIL if fail_code and spec.code == fail_code else StepStatus.PASS


def _row(run_id: str, target: str, spec: StepSpec, status: StepStatus, plan_path: Path) -> ProofStep:
    """Build one proof row."""
    return ProofStep(
        run_id=run_id,
        target=target,
        phase=spec.phase,
        step=spec.step,
        status=status,
        evidence_path=str(plan_path),
        reason=f"simulated failure at {spec.code}" if status == StepStatus.FAIL else None,
        meta={"code": spec.code, "label": spec.label},
    )


def run_step_dryrun(
    plan_path: Path,
    proof_path: Path,
    json_output: Path,
    text_output: Path,
    *,
    limit: int = 3,
    fail_code: str | None = None,
) -> dict[str, Any]:
    """Write proof rows for the expected flight chain."""
    plan = load_plan(plan_path)
    ledger = ProofLedger(proof_path)
    preflight_failed = False
    for spec in PREFLIGHT_STEPS:
        if preflight_failed:
            row = _row(plan.run_id, "*", spec, StepStatus.SKIP, plan_path)
            row.reason = "previous required step failed"
        else:
            row = _row(plan.run_id, "*", spec, _status_for(spec, fail_code), plan_path)
            if row.status == StepStatus.FAIL:
                preflight_failed = True
        ledger.append(row)

    target_summaries = []
    for target in plan.targets[:limit]:
        stop_remaining = preflight_failed
        target_ok = True
        for spec in TARGET_STEPS:
            if stop_remaining:
                status = StepStatus.SKIP
                reason = "preflight failed" if preflight_failed else "previous required step failed"
            else:
                status = _status_for(spec, fail_code)
                reason = None
            row = _row(plan.run_id, target.name, spec, status, plan_path)
            if reason:
                row.reason = reason
            ledger.append(row)
            if status == StepStatus.FAIL:
                target_ok = False
                stop_remaining = True
            if status == StepStatus.SKIP:
                target_ok = False
        target_summaries.append({"target": target.name, "ok": target_ok})

    postflight_failed = preflight_failed
    for spec in POSTFLIGHT_STEPS:
        if postflight_failed:
            row = _row(plan.run_id, "*", spec, StepStatus.SKIP, plan_path)
            row.reason = "preflight failed" if preflight_failed else "previous required step failed"
        else:
            row = _row(plan.run_id, "*", spec, _status_for(spec, fail_code), plan_path)
            if row.status == StepStatus.FAIL:
                postflight_failed = True
        ledger.append(row)

    rows = ledger.read_all()
    result = {
        "targets": target_summaries,
        "preflight_ok": not preflight_failed,
        "postflight_ok": not postflight_failed,
        "proof_rows": len(rows),
        "failed": sum(1 for row in rows if row.status == StepStatus.FAIL),
        "skipped": sum(1 for row in rows if row.status == StepStatus.SKIP),
        "chain": [spec.__dict__ for spec in [*PREFLIGHT_STEPS, *TARGET_STEPS, *POSTFLIGHT_STEPS]],
    }
    json_output.parent.mkdir(parents=True, exist_ok=True)
    text_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    text_output.write_text(render_step_summary(result), encoding="utf-8")
    return result


def render_step_summary(result: dict[str, Any]) -> str:
    """Render step dry run for humans."""
    lines = [
        "SeeVar Next flight-step dry run",
        f"Preflight: {'pass' if result['preflight_ok'] else 'fail'}",
        f"Postflight: {'pass' if result['postflight_ok'] else 'fail'}",
        f"Proof rows: {result['proof_rows']}",
        f"Failed: {result['failed']}",
        f"Skipped: {result['skipped']}",
        "Targets:",
    ]
    lines.extend(f"- {item['target']}: {'pass' if item['ok'] else 'fail'}" for item in result["targets"])
    lines.append("Chain:")
    lines.extend(f"- {item['code']} {item['phase']}.{item['step']}: {item['label']}" for item in result["chain"])
    return "\n".join(lines) + "\n"
