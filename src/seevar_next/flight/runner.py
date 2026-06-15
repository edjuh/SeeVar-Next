"""Flight CLI."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from seevar_next.flight.seestarpy_adapter import SeestarpyAdapter
from seevar_next.flight.status import (
    build_flight_snapshot,
    build_submitted_snapshot,
    render_flight_status,
    write_flight_status,
)


def _print_status(snapshot: dict, human: bool) -> None:
    """Print flight status."""
    if human:
        print(render_flight_status(snapshot), end="")
        return
    print(json.dumps(snapshot, indent=2))


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Submit or monitor a seestarpy plan.")
    parser.add_argument("command", choices=["validate", "submit", "status", "monitor", "stop"])
    parser.add_argument("--plan", type=Path, default=Path("data/seestarpy_plan.json"))
    parser.add_argument("--proof", type=Path, default=Path("data/flight_runs/flight.jsonl"))
    parser.add_argument("--json-output", type=Path, default=Path("data/flight_status.json"))
    parser.add_argument("--text-output", type=Path, default=Path("data/flight_status.txt"))
    parser.add_argument("--run-id", default="manual")
    parser.add_argument("--timeout-sec", type=float, default=12.0)
    parser.add_argument("--human", action="store_true")
    parser.add_argument("--interval-sec", type=float, default=30.0)
    parser.add_argument("--samples", type=int, default=1, help="Monitor samples; 0 means forever.")
    args = parser.parse_args()
    adapter = SeestarpyAdapter(args.proof, args.run_id, timeout_sec=args.timeout_sec)
    if args.command == "validate":
        payload = adapter.validate_file(args.plan)
        print(json.dumps({"valid": payload["plan_name"], "targets": len(payload["list"])}, indent=2))
        return 0
    if args.command == "submit":
        try:
            payload = adapter.submit_file(args.plan)
            snapshot = build_submitted_snapshot(payload)
            write_flight_status(snapshot, args.json_output, args.text_output)
            print(json.dumps({"submitted": payload["plan_name"], "targets": len(payload["list"])}, indent=2))
            return 0
        except Exception as exc:
            snapshot = build_flight_snapshot(None, str(exc))
            write_flight_status(snapshot, args.json_output, args.text_output)
            print(json.dumps({"submitted": False, "error": str(exc)}, indent=2))
            return 1
    if args.command in {"status", "monitor"}:
        sample = 0
        last_rc = 0
        while True:
            sample += 1
            try:
                snapshot = build_flight_snapshot(adapter.status())
                write_flight_status(snapshot, args.json_output, args.text_output)
                _print_status(snapshot, args.human)
                last_rc = 0
            except Exception as exc:
                snapshot = build_flight_snapshot(None, str(exc))
                write_flight_status(snapshot, args.json_output, args.text_output)
                _print_status(snapshot, args.human)
                last_rc = 1
            if args.command == "status" or (args.samples and sample >= args.samples):
                return last_rc
            time.sleep(args.interval_sec)
    try:
        adapter.stop()
        snapshot = {"running": False, "state": "stopped", "targets": []}
        write_flight_status(snapshot, args.json_output, args.text_output)
        print(json.dumps({"stopped": True}, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"stopped": False, "error": str(exc)}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
