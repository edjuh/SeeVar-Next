"""Proof-backed seestarpy plan adapter."""

from __future__ import annotations

import importlib
import json
import signal
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from seevar_next.models import ProofStep, StepStatus
from seevar_next.proof.ledger import ProofLedger


def load_plan_payload(path: Path) -> dict[str, Any]:
    """Load a seestarpy plan JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def validate_plan_payload(payload: dict[str, Any]) -> None:
    """Validate the required seestarpy plan shape."""
    if not isinstance(payload.get("plan_name"), str):
        raise ValueError("missing plan_name")
    if not isinstance(payload.get("update_time_seestar"), str):
        raise ValueError("missing update_time_seestar")
    targets = payload.get("list")
    if not isinstance(targets, list) or not targets:
        raise ValueError("plan list is empty")
    for idx, target in enumerate(targets, start=1):
        for key in ("target_id", "target_name", "target_ra_dec", "start_min", "duration_min"):
            if key not in target:
                raise ValueError(f"target {idx} missing {key}")


def _seestarpy_plan_module():
    """Import seestarpy.plan."""
    try:
        return importlib.import_module("seestarpy.plan")
    except ImportError:
        package = importlib.import_module("seestarpy")
        return package.plan


@contextmanager
def time_limit(seconds: float):
    """Raise TimeoutError when seestarpy blocks too long."""
    if seconds <= 0 or not hasattr(signal, "SIGALRM"):
        yield
        return

    def _handler(_signum, _frame):
        raise TimeoutError(f"seestarpy call exceeded {seconds:.1f}s")

    old_handler = signal.signal(signal.SIGALRM, _handler)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)


class SeestarpyAdapter:
    """Submit and monitor plans through seestarpy."""

    def __init__(self, proof_path: Path, run_id: str = "manual", timeout_sec: float = 12.0) -> None:
        self.ledger = ProofLedger(proof_path)
        self.run_id = run_id
        self.timeout_sec = timeout_sec

    def _proof(self, step: str, status: StepStatus, reason: str | None = None, meta: dict | None = None) -> None:
        """Append one flight proof row."""
        self.ledger.append(
            ProofStep(
                run_id=self.run_id,
                target="*",
                phase="flight",
                step=step,
                status=status,
                reason=reason,
                meta=meta or {},
            )
        )

    def submit_file(self, path: Path) -> dict[str, Any]:
        """Validate and submit one seestarpy plan file."""
        payload = load_plan_payload(path)
        validate_plan_payload(payload)
        self._proof("validate_plan", StepStatus.PASS, meta={"targets": len(payload["list"]), "plan": str(path)})
        try:
            with time_limit(self.timeout_sec):
                plan = _seestarpy_plan_module()
                plan.set_view_plan(payload)
        except Exception as exc:
            self._proof("submit_plan", StepStatus.FAIL, reason=str(exc))
            raise
        self._proof("submit_plan", StepStatus.PASS, meta={"plan_name": payload["plan_name"]})
        return payload

    def validate_file(self, path: Path) -> dict[str, Any]:
        """Validate one plan without submitting it."""
        payload = load_plan_payload(path)
        validate_plan_payload(payload)
        self._proof("validate_plan", StepStatus.PASS, meta={"targets": len(payload["list"]), "plan": str(path)})
        return payload

    def status(self) -> dict[str, Any] | None:
        """Read and proof current running plan status."""
        try:
            with time_limit(self.timeout_sec):
                plan = _seestarpy_plan_module()
                current = plan.get_running_plan()
        except Exception as exc:
            self._proof("running_plan", StepStatus.FAIL, reason=str(exc))
            raise
        meta: dict[str, Any] = {"running": current is not None}
        if current:
            meta["state"] = current.get("state")
            meta["plan_name"] = (current.get("plan") or {}).get("plan_name")
            meta["targets"] = [
                {
                    "target_name": item.get("target_name"),
                    "state": item.get("state", "pending"),
                    "skip": item.get("skip", False),
                }
                for item in (current.get("plan") or {}).get("list", [])
            ]
        self._proof("running_plan", StepStatus.PASS, meta=meta)
        return current

    def stop(self) -> None:
        """Stop the running plan."""
        try:
            with time_limit(self.timeout_sec):
                plan = _seestarpy_plan_module()
                plan.stop_view_plan()
        except Exception as exc:
            self._proof("stop_plan", StepStatus.FAIL, reason=str(exc))
            raise
        self._proof("stop_plan", StepStatus.PASS)
