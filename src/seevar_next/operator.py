"""Operator menu and one-shot runner."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from seevar_next.config import SeeVarConfig, load_config

DEFAULT_CONFIG = Path("config/seevar-next.json")


def run(cmd: list[str]) -> int:
    """Run one command and stream output."""
    print("$ " + " ".join(cmd), flush=True)
    return subprocess.call(cmd)


def preflight(config: SeeVarConfig) -> int:
    """Build nightly plan and seestarpy export."""
    rc = run(
        [
            "seevar-next-preflight",
            "--catalog",
            config.catalog,
            "--lat",
            str(config.latitude_deg),
            "--lon",
            str(config.longitude_deg),
            "--limit",
            str(config.limit),
            "--hours",
            str(config.hours),
            "--sun-alt",
            str(config.sun_alt_limit_deg),
            "--min-alt",
            str(config.min_alt_deg),
            "--output",
            "data/tonights_plan.json",
        ]
    )
    if rc:
        return rc
    return run(
        [
            "seevar-next-seestarpy-plan",
            "--input",
            "data/tonights_plan.json",
            "--output",
            config.seestarpy_plan_path,
            "--timezone",
            config.timezone,
        ]
    )


def dryrun() -> int:
    """Run a three-target proof dry-run."""
    return run(
        [
            "seevar-next-dryrun",
            "--plan",
            "data/tonights_plan.json",
            "--proof",
            "data/flight_runs/dryrun.jsonl",
            "--status",
            "data/status.json",
            "--limit",
            "3",
        ]
    )


def status() -> int:
    """Print current status."""
    return run(
        [
            "seevar-next-status",
            "--proof",
            "data/flight_runs/dryrun.jsonl",
            "--plan",
            "data/tonights_plan.json",
            "--output",
            "data/status.json",
        ]
    )


def readiness(config_path: Path) -> int:
    """Check weather and scope readiness."""
    return run(["seevar-next-readiness", "--config", str(config_path)])


def refresh_aavso() -> int:
    """Refresh AAVSO campaign catalog."""
    return run(["seevar-next-fetch-aavso", "--output", "catalogs/campaign_targets.json"])


def flight_submit(config: SeeVarConfig) -> int:
    """Submit the seestarpy plan."""
    return run(["seevar-next-flight", "submit", "--plan", config.seestarpy_plan_path])


def guarded_flight_submit(config: SeeVarConfig, config_path: Path) -> int:
    """Gate flight submit on weather and telescope readiness."""
    rc = readiness(config_path)
    if rc:
        return rc
    return flight_submit(config)


def flight_status() -> int:
    """Show seestarpy running-plan status."""
    return run(["seevar-next-flight", "status", "--human"])


def flight_policy() -> int:
    """Show flight policy."""
    return run(["seevar-next-flight", "policy"])


def flight_monitor() -> int:
    """Monitor seestarpy flight status."""
    return run(["seevar-next-flight", "monitor", "--human", "--samples", "0", "--interval-sec", "30"])


def dashboard(config_path: Path) -> int:
    """Serve the local dashboard."""
    return run(["seevar-next-dashboard", "--config", str(config_path)])


def menu(config_path: Path) -> int:
    """Show a small text menu."""
    config = load_config(config_path)
    actions = {
        "1": ("Build tonight plan", lambda: preflight(config)),
        "2": ("Dry-run 3 targets", dryrun),
        "3": ("Show status", status),
        "4": ("Check readiness", lambda: readiness(config_path)),
        "5": ("Refresh AAVSO catalog", refresh_aavso),
        "6": ("Submit seestarpy plan", lambda: guarded_flight_submit(config, config_path)),
        "7": ("Seestarpy plan status", flight_status),
        "8": ("Show flight policy", flight_policy),
        "9": ("Monitor flight", flight_monitor),
        "10": ("Start dashboard", lambda: dashboard(config_path)),
        "q": ("Quit", lambda: 0),
    }
    while True:
        print("\nSeeVar Next")
        for key, (label, _) in actions.items():
            print(f"  {key}. {label}")
        choice = input("> ").strip().lower()
        if choice in actions:
            return actions[choice][1]()
        print("Unknown choice")


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="SeeVar Next operator command.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "command",
        nargs="?",
        choices=[
            "menu",
            "preflight",
            "dryrun",
            "status",
            "readiness",
            "refresh-aavso",
            "flight-submit",
            "flight-status",
            "flight-policy",
            "flight-monitor",
            "dashboard",
        ],
        default="menu",
    )
    args = parser.parse_args()
    config = load_config(args.config)
    if args.command == "menu":
        return menu(args.config)
    if args.command == "preflight":
        return preflight(config)
    if args.command == "dryrun":
        return dryrun()
    if args.command == "status":
        return status()
    if args.command == "readiness":
        return readiness(args.config)
    if args.command == "refresh-aavso":
        return refresh_aavso()
    if args.command == "flight-submit":
        return guarded_flight_submit(config, args.config)
    if args.command == "flight-status":
        return flight_status()
    if args.command == "flight-policy":
        return flight_policy()
    if args.command == "flight-monitor":
        return flight_monitor()
    if args.command == "dashboard":
        return dashboard(args.config)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
