#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filename: tests/test_flight_policy.py
Version: 0.1.0
Objective: Test flight policy behavior.
"""
from seevar_next.config import SeeVarConfig
from seevar_next.flight.policy import build_policy, render_policy


def test_default_policy_matches_operator_decisions():
    policy = build_policy(SeeVarConfig(latitude_deg=52.0, longitude_deg=4.0))

    assert policy["primary_adapter"] == "seestarpy"
    assert policy["fallback_adapter"] == "seestar_alp"
    assert policy["submit_mode"] == "plan"
    assert policy["retry_failed_targets"]
    assert policy["allow_pretty_targets"]
    assert all(policy["failure_rules"].values())


def test_render_policy_is_human_readable():
    text = render_policy(build_policy(SeeVarConfig(latitude_deg=52.0, longitude_deg=4.0)))

    assert "Primary: seestarpy" in text
    assert "Fallback: seestar_alp" in text
    assert "missing solve" in text
