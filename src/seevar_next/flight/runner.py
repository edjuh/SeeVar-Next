"""Flight CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from seevar_next.flight.seestarpy_adapter import SeestarpyAdapter


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Submit or monitor a seestarpy plan.")
    parser.add_argument("command", choices=["validate", "submit", "status", "stop"])
    parser.add_argument("--plan", type=Path, default=Path("data/seestarpy_plan.json"))
    parser.add_argument("--proof", type=Path, default=Path("data/flight_runs/flight.jsonl"))
    parser.add_argument("--run-id", default="manual")
    args = parser.parse_args()
    adapter = SeestarpyAdapter(args.proof, args.run_id)
    if args.command == "validate":
        payload = adapter.validate_file(args.plan)
        print(json.dumps({"valid": payload["plan_name"], "targets": len(payload["list"])}, indent=2))
        return 0
    if args.command == "submit":
        payload = adapter.submit_file(args.plan)
        print(json.dumps({"submitted": payload["plan_name"], "targets": len(payload["list"])}, indent=2))
        return 0
    if args.command == "status":
        current = adapter.status()
        print(json.dumps(current or {"running": False}, indent=2))
        return 0
    adapter.stop()
    print(json.dumps({"stopped": True}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
