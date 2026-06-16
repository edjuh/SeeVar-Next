#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filename: tests/test_flight_status.py
Version: 0.1.0
Objective: Test flight status behavior.
"""
from seevar_next.flight.status import build_flight_snapshot, build_submitted_snapshot, render_flight_status


def test_render_flight_status_from_running_plan():
    snapshot = build_flight_snapshot(
        {
            "state": "running",
            "plan": {
                "plan_name": "SeeVar",
                "list": [{"target_name": "ST Boo", "state": "exposing", "duration_min": 10}],
            },
        }
    )

    text = render_flight_status(snapshot)

    assert "SeeVar Next flight: RUNNING" in text
    assert "ST Boo: exposing" in text


def test_submitted_snapshot_lists_targets():
    snapshot = build_submitted_snapshot(
        {"plan_name": "SeeVar", "list": [{"target_name": "ST Boo", "duration_min": 10}]}
    )

    assert snapshot["state"] == "submitted"
    assert snapshot["targets"][0]["name"] == "ST Boo"
