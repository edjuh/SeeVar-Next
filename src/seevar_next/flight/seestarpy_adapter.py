"""Thin seestarpy adapter boundary."""

from __future__ import annotations

from seevar_next.models import TargetPlan


class SeestarpyAdapter:
    """Adapter interface for seestarpy execution."""

    def validate_plan(self, plan: list[TargetPlan]) -> bool:
        """Return true when the plan has at least one target."""
        return bool(plan)

    def submit_plan(self, plan: list[TargetPlan]) -> str:
        """Submit a plan and return an execution id."""
        if not self.validate_plan(plan):
            raise ValueError("empty plan")
        return "dry-run"
