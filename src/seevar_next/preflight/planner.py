"""Preflight planner skeleton."""

from __future__ import annotations

from seevar_next.models import TargetPlan


def build_plan(targets: list[TargetPlan], limit: int | None = None) -> list[TargetPlan]:
    """Return a priority-sorted observing plan."""
    planned = sorted(targets, key=lambda item: item.priority)
    return planned[:limit] if limit else planned
