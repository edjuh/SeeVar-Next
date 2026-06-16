#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filename: src/seevar_next/readiness.py
Version: 0.1.0
Objective: Human-readable readiness checks.
"""
from __future__ import annotations

import argparse
import json
import socket
from pathlib import Path
from typing import Any

from seevar_next.config import ScopeConfig, SeeVarConfig, load_config
from seevar_next.models import ProofStep, StepStatus
from seevar_next.proof.ledger import ProofLedger
from seevar_next.weather import evaluate_weather, fetch_weather


def probe_scope(scope: ScopeConfig, timeout_sec: float = 2.0) -> dict[str, Any]:
    """Probe one telescope host."""
    if not scope.enabled:
        return {"name": scope.name, "host": scope.host, "enabled": False, "ok": True, "summary": "disabled"}
    failures = []
    for port in scope.status_ports:
        try:
            with socket.create_connection((scope.host, port), timeout=timeout_sec):
                return {
                    "name": scope.name,
                    "host": scope.host,
                    "enabled": True,
                    "ok": True,
                    "summary": f"reachable tcp/{port}",
                    "port": port,
                }
        except OSError as exc:
            failures.append(f"tcp/{port}: {exc.__class__.__name__}")
    return {
        "name": scope.name,
        "host": scope.host,
        "enabled": True,
        "ok": False,
        "summary": "not reachable",
        "reasons": failures,
    }


def build_readiness(config: SeeVarConfig, *, scope_timeout_sec: float = 2.0) -> dict[str, Any]:
    """Build one readiness result."""
    try:
        weather = evaluate_weather(config, fetch_weather(config))
    except Exception as exc:
        weather = {"ok": False, "summary": "weather unavailable", "reasons": [str(exc)]}
    scopes = [probe_scope(scope, scope_timeout_sec) for scope in config.scopes]
    blockers: list[str] = []
    if not weather["ok"]:
        blockers.extend(f"weather: {reason}" for reason in weather.get("reasons", []))
    for scope in scopes:
        if scope.get("enabled") and not scope["ok"]:
            blockers.append(f"{scope['name']}: {scope['summary']}")
    return {"ok": not blockers, "weather": weather, "scopes": scopes, "blockers": blockers}


def render_readiness(result: dict[str, Any]) -> str:
    """Render readiness for humans."""
    lines = [f"SeeVar Next readiness: {'GO' if result['ok'] else 'NO-GO'}"]
    lines.append(f"Weather: {'GO' if result['weather']['ok'] else 'NO-GO'} - {result['weather']['summary']}")
    lines.append("Scopes:")
    for scope in result["scopes"]:
        state = "GO" if scope["ok"] else "NO-GO"
        if not scope.get("enabled"):
            state = "SKIP"
        lines.append(f"- {scope['name']} {scope['host']}: {state} - {scope['summary']}")
    if result["blockers"]:
        lines.append("Blockers:")
        lines.extend(f"- {item}" for item in result["blockers"])
    return "\n".join(lines) + "\n"


def write_proof(result: dict[str, Any], proof_path: Path, run_id: str) -> None:
    """Write readiness proof rows."""
    ledger = ProofLedger(proof_path)
    ledger.append(
        ProofStep(
            run_id=run_id,
            target="*",
            phase="readiness",
            step="weather",
            status=StepStatus.PASS if result["weather"]["ok"] else StepStatus.FAIL,
            reason="; ".join(result["weather"].get("reasons", [])) or None,
            meta=result["weather"],
        )
    )
    for scope in result["scopes"]:
        ledger.append(
            ProofStep(
                run_id=run_id,
                target=scope["name"],
                phase="readiness",
                step="connect",
                status=StepStatus.SKIP if not scope.get("enabled") else StepStatus.PASS if scope["ok"] else StepStatus.FAIL,
                reason="; ".join(scope.get("reasons", [])) or None,
                meta=scope,
            )
        )
    ledger.append(
        ProofStep(
            run_id=run_id,
            target="*",
            phase="readiness",
            step="run_gate",
            status=StepStatus.PASS if result["ok"] else StepStatus.FAIL,
            reason="; ".join(result["blockers"]) or None,
            meta={"blockers": result["blockers"]},
        )
    )


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Check weather and telescope readiness.")
    parser.add_argument("--config", type=Path, default=Path("config/seevar-next.json"))
    parser.add_argument("--json-output", type=Path, default=Path("data/readiness.json"))
    parser.add_argument("--text-output", type=Path, default=Path("data/readiness.txt"))
    parser.add_argument("--proof", type=Path, default=Path("data/flight_runs/readiness.jsonl"))
    parser.add_argument("--run-id", default="manual")
    parser.add_argument("--scope-timeout-sec", type=float, default=2.0)
    args = parser.parse_args()

    result = build_readiness(load_config(args.config), scope_timeout_sec=args.scope_timeout_sec)
    text = render_readiness(result)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    args.text_output.parent.mkdir(parents=True, exist_ok=True)
    args.text_output.write_text(text, encoding="utf-8")
    write_proof(result, args.proof, args.run_id)
    print(text, end="")
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
