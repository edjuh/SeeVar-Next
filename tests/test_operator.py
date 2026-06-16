#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filename: tests/test_operator.py
Version: 0.1.0
Objective: Test operator behavior.
"""
import json

from seevar_next.config import load_config


def test_load_operator_config(tmp_path):
    path = tmp_path / "seevar-next.json"
    path.write_text(json.dumps({"latitude_deg": 1.0, "longitude_deg": 2.0}), encoding="utf-8")

    cfg = load_config(path)

    assert cfg.latitude_deg == 1.0
    assert cfg.longitude_deg == 2.0
