#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filename: tests/test_seestar_rpc.py
Version: 0.1.0
Objective: Test seestar rpc behavior.
"""
from seevar_next.flight.seestar_rpc import probe_status


def test_probe_status_reports_offline(monkeypatch):
    def fake_connect(*_args, **_kwargs):
        raise OSError("offline")

    monkeypatch.setattr("socket.create_connection", fake_connect)

    status = probe_status("192.0.2.1", timeout_sec=0.01)

    assert not status["ok"]
    assert status["errors"]
