"""Build compact status from proof ledgers."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from seevar_next.proof.ledger import ProofLedger


def _load_plan_targets(plan_path: Path | None) -> list[str]:
    """Load target names from a plan."""
    if not plan_path or not plan_path.exists():
        return []
    payload = json.loads(plan_path.read_text(encoding="utf-8"))
    return [str(row.get("name")) for row in payload.get("targets", []) if row.get("name")]


def build_status(proof_path: Path, plan_path: Path | None = None) -> dict[str, Any]:
    """Summarize current proof state."""
    rows = ProofLedger(proof_path).read_all()
    by_target: dict[str, list] = defaultdict(list)
    for row in rows:
        if row.target != "*":
            by_target[row.target].append(row)
    target_status = {}
    for target, target_rows in by_target.items():
        latest = target_rows[-1]
        target_status[target] = {
            "phase": latest.phase,
            "step": latest.step,
            "status": latest.status,
            "reason": latest.reason,
            "passed": sum(1 for row in target_rows if row.status == "pass"),
            "failed": sum(1 for row in target_rows if row.status == "fail"),
        }
    counts = Counter(str(row.status) for row in rows)
    return {
        "planned_targets": _load_plan_targets(plan_path),
        "proof_rows": len(rows),
        "status_counts": dict(counts),
        "targets": target_status,
    }


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Build SeeVar Next monitor status JSON.")
    parser.add_argument("--proof", type=Path, default=Path("data/flight_runs/dryrun.jsonl"))
    parser.add_argument("--plan", type=Path, default=Path("data/tonights_plan.json"))
    parser.add_argument("--output", type=Path, default=Path("data/status.json"))
    args = parser.parse_args()
    status = build_status(args.proof, args.plan)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(status, indent=2), encoding="utf-8")
    print(json.dumps(status, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
