#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filename: tests/test_readiness.py
Version: 0.1.0
Objective: Test readiness behavior.
"""
from seevar_next.config import ScopeConfig, SeeVarConfig
from seevar_next.readiness import build_readiness, probe_scope, render_readiness
from seevar_next.weather import evaluate_weather


class DummySocket:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_weather_gate_blocks_clouds():
    cfg = SeeVarConfig(latitude_deg=52.0, longitude_deg=4.0)
    payload = {"hourly": {"cloud_cover": [95], "precipitation": [0], "wind_speed_10m": [8]}}

    result = evaluate_weather(cfg, payload)

    assert not result["ok"]
    assert "cloud" in result["reasons"][0]


def test_probe_scope_accepts_any_open_port(monkeypatch):
    def fake_connect(address, timeout):
        if address[1] == 22:
            return DummySocket()
        raise OSError("closed")

    monkeypatch.setattr("socket.create_connection", fake_connect)

    result = probe_scope(ScopeConfig(name="Wilhelmina", host="192.168.178.251", status_ports=[4700, 22]))

    assert result["ok"]
    assert result["port"] == 22


def test_readiness_renders_human_no_go(monkeypatch):
    cfg = SeeVarConfig(latitude_deg=52.0, longitude_deg=4.0, scopes=[ScopeConfig(name="W", host="bad", status_ports=[22])])

    monkeypatch.setattr("seevar_next.readiness.fetch_weather", lambda config: {"hourly": {"cloud_cover": [10]}})
    monkeypatch.setattr("socket.create_connection", lambda address, timeout: (_ for _ in ()).throw(OSError("closed")))

    result = build_readiness(cfg)
    text = render_readiness(result)

    assert not result["ok"]
    assert "SeeVar Next readiness: NO-GO" in text
    assert "W bad: NO-GO" in text
