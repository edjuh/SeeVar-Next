"""Flight policy reporting."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from seevar_next.config import SeeVarConfig, load_config
from seevar_next.models import ProofStep, StepStatus
from seevar_next.proof.ledger import ProofLedger


def build_policy(config: SeeVarConfig) -> dict[str, Any]:
    """Build the configured flight policy."""
    return {
        "primary_adapter": config.flight.primary_adapter,
        "fallback_adapter": config.flight.fallback_adapter,
        "submit_mode": config.flight.submit_mode,
        "retry_failed_targets": config.flight.retry_failed_targets,
        "max_attempts_per_target": config.flight.max_attempts_per_target,
        "allow_pretty_targets": config.flight.allow_pretty_targets,
        "pretty_after_science": config.flight.pretty_after_science,
        "failure_rules": {
            "missing_solve": config.flight.fail_on_missing_solve,
            "tracking_off": config.flight.fail_on_tracking_off,
            "too_few_frames": config.flight.fail_on_too_few_frames,
        },
    }


def render_policy(policy: dict[str, Any]) -> str:
    """Render flight policy for humans."""
    rules = policy["failure_rules"]
    lines = [
        "SeeVar Next flight policy",
        f"Primary: {policy['primary_adapter']}",
        f"Fallback: {policy['fallback_adapter']}",
        f"Submit: {policy['submit_mode']}",
        f"Retry failed science targets: {'yes' if policy['retry_failed_targets'] else 'no'}",
        f"Max attempts per target: {policy['max_attempts_per_target']}",
        f"Pretty targets after science: {'yes' if policy['allow_pretty_targets'] and policy['pretty_after_science'] else 'no'}",
        "Target fails on:",
    ]
    for label, enabled in rules.items():
        if enabled:
            lines.append(f"- {label.replace('_', ' ')}")
    return "\n".join(lines) + "\n"


def write_policy(config_path: Path, json_output: Path, text_output: Path, proof_path: Path, run_id: str) -> dict[str, Any]:
    """Write policy files and proof."""
    policy = build_policy(load_config(config_path))
    json_output.parent.mkdir(parents=True, exist_ok=True)
    text_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(policy, indent=2), encoding="utf-8")
    text_output.write_text(render_policy(policy), encoding="utf-8")
    ProofLedger(proof_path).append(
        ProofStep(
            run_id=run_id,
            target="*",
            phase="flight",
            step="policy",
            status=StepStatus.PASS,
            evidence_path=str(json_output),
            meta=policy,
        )
    )
    return policy
