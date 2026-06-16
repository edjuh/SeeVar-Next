#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filename: tests/test_contracts.py
Version: 0.1.0
Objective: Test contracts behavior.
"""
from pathlib import Path

import pytest

from seevar_next.models import TargetPlan
from seevar_next.postflight.pipeline import require_frames
from seevar_next.preflight.planner import build_plan


def test_preflight_orders_by_priority():
    plan = build_plan(
        [
            TargetPlan(name="B", ra_deg=2, dec_deg=2, priority=20),
            TargetPlan(name="A", ra_deg=1, dec_deg=1, priority=10),
        ]
    )
    assert [item.name for item in plan] == ["A", "B"]


def test_postflight_requires_frames(tmp_path: Path):
    with pytest.raises(ValueError, match="need 1 FITS"):
        require_frames(tmp_path)
