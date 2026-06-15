"""Operator menu and one-shot runner."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

DEFAULT_CONFIG = Path("config/seevar-next.json")


def load_config(path: Path) -> dict[str, Any]:
    """Load operator configuration."""
    if not path.exists():
        return {
            "latitude_deg": 52.39,
            "longitude_deg": 4.61,
            "catalog": "campaign_targets",
            "limit": 20,
            "timezone": "Europe/Amsterdam",
        }
    return json.loads(path.read_text(encoding="utf-8"))


def run(cmd: list[str]) -> int:
    """Run one command and stream output."""
    print("$ " + " ".join(cmd))
    return subprocess.call(cmd)


def preflight(config: dict[str, Any]) -> int:
    """Build nightly plan and seestarpy export."""
    rc = run(
        [
            "seevar-next-preflight",
            "--catalog",
            str(config.get("catalog", "campaign_targets")),
            "--lat",
            str(config["latitude_deg"]),
            "--lon",
            str(config["longitude_deg"]),
            "--limit",
            str(config.get("limit", 20)),
            "--hours",
            str(config.get("hours", 24.0)),
            "--sun-alt",
            str(config.get("sun_alt_limit_deg", -12.0)),
            "--min-alt",
            str(config.get("min_alt_deg", 25.0)),
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
            "data/seestarpy_plan.json",
            "--timezone",
            str(config.get("timezone", "Europe/Amsterdam")),
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


def refresh_aavso() -> int:
    """Refresh AAVSO campaign catalog."""
    return run(["seevar-next-fetch-aavso", "--output", "catalogs/campaign_targets.json"])


def menu(config_path: Path) -> int:
    """Show a small text menu."""
    config = load_config(config_path)
    actions = {
        "1": ("Build tonight plan", lambda: preflight(config)),
        "2": ("Dry-run 3 targets", dryrun),
        "3": ("Show status", status),
        "4": ("Refresh AAVSO catalog", refresh_aavso),
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
    parser.add_argument("command", nargs="?", choices=["menu", "preflight", "dryrun", "status", "refresh-aavso"], default="menu")
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
    if args.command == "refresh-aavso":
        return refresh_aavso()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
