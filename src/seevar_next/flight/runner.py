"""Flight CLI."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from seevar_next.config import load_config
from seevar_next.flight.policy import render_policy, write_policy
from seevar_next.flight.seestar_rpc import probe_status
from seevar_next.flight.seestarpy_adapter import SeestarpyAdapter
from seevar_next.flight.status import (
    build_flight_snapshot,
    build_submitted_snapshot,
    render_flight_status,
    with_scope_status,
    write_flight_status,
)


def _scope_status(config_path: Path, timeout_sec: float) -> list[dict]:
    """Probe configured scopes without seestarpy discovery."""
    config = load_config(config_path)
    rows = []
    for scope in config.scopes:
        if not scope.enabled:
            rows.append({"name": scope.name, "host": scope.host, "ok": True, "summary": "disabled"})
            continue
        status = probe_status(scope.host, timeout_sec=min(timeout_sec, 2.0))
        status["name"] = scope.name
        status["summary"] = "rpc ok" if status.get("ok") else "rpc unavailable"
        rows.append(status)
    return rows


def _print_status(snapshot: dict, human: bool) -> None:
    """Print flight status."""
    if human:
        print(render_flight_status(snapshot), end="")
        return
    print(json.dumps(snapshot, indent=2))


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Submit or monitor a seestarpy plan.")
    parser.add_argument("command", choices=["validate", "policy", "submit", "status", "monitor", "stop"])
    parser.add_argument("--plan", type=Path, default=Path("data/seestarpy_plan.json"))
    parser.add_argument("--proof", type=Path, default=Path("data/flight_runs/flight.jsonl"))
    parser.add_argument("--json-output", type=Path, default=Path("data/flight_status.json"))
    parser.add_argument("--text-output", type=Path, default=Path("data/flight_status.txt"))
    parser.add_argument("--policy-json-output", type=Path, default=Path("data/flight_policy.json"))
    parser.add_argument("--policy-text-output", type=Path, default=Path("data/flight_policy.txt"))
    parser.add_argument("--config", type=Path, default=Path("config/seevar-next.json"))
    parser.add_argument("--run-id", default="manual")
    parser.add_argument("--timeout-sec", type=float, default=12.0)
    parser.add_argument("--human", action="store_true")
    parser.add_argument("--interval-sec", type=float, default=30.0)
    parser.add_argument("--samples", type=int, default=1, help="Monitor samples; 0 means forever.")
    args = parser.parse_args()
    adapter = SeestarpyAdapter(args.proof, args.run_id, timeout_sec=args.timeout_sec)
    if args.command == "policy":
        policy = write_policy(args.config, args.policy_json_output, args.policy_text_output, args.proof, args.run_id)
        print(render_policy(policy), end="")
        return 0
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
                scopes = _scope_status(args.config, args.timeout_sec)
                enabled_online = any(scope.get("ok") and scope.get("summary") != "disabled" for scope in scopes)
                current = adapter.status() if enabled_online else None
                snapshot = with_scope_status(build_flight_snapshot(current), scopes)
                write_flight_status(snapshot, args.json_output, args.text_output)
                _print_status(snapshot, args.human)
                last_rc = 0
            except Exception as exc:
                try:
                    scopes = _scope_status(args.config, args.timeout_sec)
                except Exception:
                    scopes = []
                if scopes and not any(scope.get("ok") and scope.get("summary") != "disabled" for scope in scopes):
                    snapshot = with_scope_status(build_flight_snapshot(None), scopes)
                    last_rc = 0
                else:
                    snapshot = with_scope_status(build_flight_snapshot(None, str(exc)), scopes)
                    last_rc = 1
                write_flight_status(snapshot, args.json_output, args.text_output)
                _print_status(snapshot, args.human)
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
