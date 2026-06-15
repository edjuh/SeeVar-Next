"""Dry-run proof chain for planned targets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from seevar_next.models import NightlyPlan, ProofStep, StepStatus
from seevar_next.monitor.status import build_status
from seevar_next.proof.ledger import ProofLedger

DRYRUN_STEPS = ["connect", "slew", "solve", "track", "expose", "accept", "stack", "photometry", "report"]


def load_plan(path: Path) -> NightlyPlan:
    """Load a nightly plan."""
    return NightlyPlan.model_validate(json.loads(path.read_text(encoding="utf-8")))


def run_dryrun(plan_path: Path, proof_path: Path, status_path: Path, limit: int = 3) -> dict:
    """Write pass proofs for the first planned targets."""
    plan = load_plan(plan_path)
    ledger = ProofLedger(proof_path)
    for target in plan.targets[:limit]:
        for step in DRYRUN_STEPS:
            ledger.append(
                ProofStep(
                    run_id=plan.run_id,
                    target=target.name,
                    phase="dryrun",
                    step=step,
                    status=StepStatus.PASS,
                    evidence_path=str(plan_path),
                    meta={"ra_deg": target.ra_deg, "dec_deg": target.dec_deg},
                )
            )
    status = build_status(proof_path, plan_path)
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
    return status


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Dry-run planned targets through the proof chain.")
    parser.add_argument("--plan", type=Path, default=Path("data/tonights_plan.json"))
    parser.add_argument("--proof", type=Path, default=Path("data/flight_runs/dryrun.jsonl"))
    parser.add_argument("--status", type=Path, default=Path("data/status.json"))
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()
    print(json.dumps(run_dryrun(args.plan, args.proof, args.status, args.limit), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
